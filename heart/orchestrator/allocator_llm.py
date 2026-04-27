"""
LLM-based Task Allocator (Baseline)

Uses GPT-4o to directly decide which agent should handle each question,
replacing the Sentence-BERT semantic matching used by the HEART allocator.
Serves as a baseline to compare LLM routing vs. embedding-based routing.

Token-efficient: only calls LLM for NEW questions or questions that need
re-routing (PARTIAL/OUT_OF_SCOPE). Previously assigned but deferred questions
retain their assignment without re-querying the LLM.

Includes the same token budget capacity planning as other allocators
for fair comparison under identical resource constraints.
"""

from typing import List, Dict, Any, Optional
from heart.core.schema import (
    AgentType,
    ReasoningQuestion,
    AgentTask,
)
from heart.agents.allocator_agent import AllocatorAgent
from heart.core.schema import TaskAllocation
from heart.prompts.allocation import get_allocation_prompt


class LLMTaskAllocator:
    """
    LLM-based Task Allocator

    Uses GPT-4o for routing decisions, with token budget capacity planning.
    Caches previous assignments to avoid redundant LLM calls for deferred questions.
    """

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0,
                 env_data: Dict[str, Any] = None, max_token_sum: int = 20000):
        from heart.orchestrator.allocator import TokenBudgetPlanner
        self.agent = AllocatorAgent(model_name=model_name, temperature=temperature, env_data=env_data)
        self.task_count = 0
        self.token_planner = TokenBudgetPlanner(max_token_sum=max_token_sum)
        self.max_token_sum = max_token_sum
        self.latest_capacities: Dict[str, int] = {}
        # Cache: {question_id: agent_id} — persists across rounds
        self._cached_assignments: Dict[str, str] = {}

    def allocate(
        self,
        questions: List[ReasoningQuestion],
        original_instruction: str = "",
        agent_token_estimates: Optional[Dict[str, int]] = None,
        inflight_counts: Optional[Dict[str, int]] = None,
        previous_assignments: Optional[Dict[str, str]] = None,
        assignment_counts: Optional[Dict[str, Dict[str, int]]] = None,
        **kwargs,
    ) -> Dict[str, str]:
        """
        Allocate questions using LLM, then apply token budget capacity planning.

        Only calls LLM for questions that:
        1. Have never been assigned before (new questions)
        2. Need re-routing due to PARTIAL/OUT_OF_SCOPE (detected via assignment_counts)

        Previously assigned but budget-deferred questions reuse cached assignment.
        """
        # Step 1: Determine which questions need LLM routing
        needs_llm = []
        routing = {}

        for question in questions:
            qid = question.question_id

            # Check if this question was previously assigned and failed (needs re-route)
            prev_count = 0
            if assignment_counts and qid in assignment_counts:
                prev_count = sum(assignment_counts[qid].values())

            if qid in self._cached_assignments and prev_count == 0:
                # Already assigned, never tried — just deferred by budget. Reuse.
                routing[qid] = self._cached_assignments[qid]
            elif qid in self._cached_assignments and previous_assignments and previous_assignments.get(qid) == self._cached_assignments[qid]:
                # Same agent failed — need re-route
                needs_llm.append(question)
            elif qid not in self._cached_assignments:
                # New question — needs LLM
                needs_llm.append(question)
            else:
                # Has cache and different agent tried — reuse cache
                routing[qid] = self._cached_assignments[qid]

        # Step 2: Call LLM only for questions that need routing
        if needs_llm:
            tasks = []
            for question in needs_llm:
                task_id = f"task_{question.question_id}"
                task = AgentTask(
                    task_id=task_id,
                    query=question.prompt,
                    metadata={
                        "operation": "allocation",
                        "human_prompt": get_allocation_prompt(),
                        "original_instruction": original_instruction,
                        "question_id": question.question_id,
                        "question_type": question.question_type,
                        "question_rationale": getattr(question, 'rationale', ''),
                        "priority": getattr(question, 'priority', 1)
                    }
                )
                tasks.append(task)

            results = self.agent.reason(tasks)

            for result in results:
                q_id = result.task_id.replace("task_", "") if result.task_id.startswith("task_") else result.task_id
                if result.success and result.result:
                    allocation: TaskAllocation = result.result
                    agent_name = allocation.assigned_agent.value if hasattr(allocation.assigned_agent, 'value') else allocation.assigned_agent
                    routing[q_id] = agent_name
                    self._cached_assignments[q_id] = agent_name
                else:
                    routing[q_id] = AgentType.CONSTRAINT_REASONER.value  # fallback
                    self._cached_assignments[q_id] = routing[q_id]

            print(f"[LLM Allocator] Called LLM for {len(needs_llm)} questions, reused cache for {len(questions) - len(needs_llm)}")
        else:
            print(f"[LLM Allocator] All {len(questions)} questions reused from cache")

        # Step 3: Capacity planning budget allocation (same as HEART/TypeBased)
        agent_token_estimates = agent_token_estimates or {}
        inflight_counts = inflight_counts or {}

        # Convert routing dict to AgentType for TokenBudgetPlanner
        task_assignments_typed = {}
        for q_id, agent_str in routing.items():
            try:
                task_assignments_typed[q_id] = AgentType(agent_str)
            except ValueError:
                task_assignments_typed[q_id] = AgentType.CONSTRAINT_REASONER

        token_costs = self.token_planner._parse_agent_keys(agent_token_estimates)
        inflight = self.token_planner._parse_agent_keys(inflight_counts)
        pool = self.token_planner.plan(task_assignments_typed, token_costs, inflight)

        # Take as many as capacity allows by priority per agent
        from collections import defaultdict
        grouped = defaultdict(list)
        for q in questions:
            if q.question_id in task_assignments_typed:
                agent = task_assignments_typed[q.question_id]
                grouped[agent].append(q)

        for agent, qlist in grouped.items():
            qlist.sort(key=lambda x: getattr(x, "priority", 99))

        final_alloc: Dict[str, str] = {}
        for agent in list(AgentType):
            if agent not in grouped:
                continue
            while pool.available(agent) > 0 and grouped[agent]:
                q = grouped[agent].pop(0)
                if pool.acquire(agent):
                    final_alloc[q.question_id] = agent.value

        self.latest_capacities = {a.value: pool.capacities.get(a, 0) for a in AgentType}

        allocated = sum(1 for v in final_alloc.values() if v != "")
        deferred = len(questions) - allocated
        print(f"[LLM Allocator] Capacity planning: allocated={allocated}, deferred={deferred}")

        return final_alloc
