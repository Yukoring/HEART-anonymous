"""
LLM-based Task Allocator (Baseline)

Uses GPT-4o to directly decide which agent should handle each question,
replacing the Sentence-BERT semantic matching used by the HEART allocator.
Serves as a baseline to compare LLM routing vs. embedding-based routing.

Includes the same token budget capacity planning as other allocators
for fair comparison under identical resource constraints.
"""

from typing import List, Dict, Any, Optional
from heart.core.schema import (
    AgentType,
    ReasoningQuestion,
    AgentTask,
    AgentType
)
from heart.agents.allocator_agent import AllocatorAgent
from heart.core.schema import TaskAllocation
from heart.prompts.allocation import get_allocation_prompt


class LLMTaskAllocator:
    """
    LLM-based Task Allocator

    Uses GPT-4o for routing decisions, with token budget capacity planning.
    """

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0,
                 env_data: Dict[str, Any] = None, max_token_sum: int = 20000):
        self.agent = AllocatorAgent(model_name=model_name, temperature=temperature, env_data=env_data)
        self.task_count = 0
        self.max_token_sum = max_token_sum
        self.latest_capacities: Dict[str, int] = {}

    def allocate(
        self,
        questions: List[ReasoningQuestion],
        original_instruction: str = "",
        agent_token_estimates: Optional[Dict[str, int]] = None,
        inflight_counts: Optional[Dict[str, int]] = None,
        **kwargs,
    ) -> Dict[str, str]:
        """
        Allocate questions using LLM, then apply token budget capacity planning.

        Args:
            questions: Decomposed reasoning questions
            original_instruction: Original instruction for context
            agent_token_estimates: {agent_id: estimated_tokens}
            inflight_counts: {agent_id: count} — currently processing tasks

        Returns:
            {question_id: agent_id} mapping (unallocated tasks have value "")
        """
        # Step 1: LLM decides routing (which agent for each task)
        tasks = []
        for question in questions:
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

        # Step 2: Parse LLM results into routing dict
        routing = {}
        for result in results:
            q_id = result.task_id.replace("task_", "") if result.task_id.startswith("task_") else result.task_id
            if result.success and result.result:
                allocation: TaskAllocation = result.result
                agent_name = allocation.assigned_agent.value if hasattr(allocation.assigned_agent, 'value') else allocation.assigned_agent
                routing[q_id] = agent_name
            else:
                routing[q_id] = AgentType.CONSTRAINT_REASONER.value  # fallback

        # Step 3: Simple sequential budget allocation (same as TypeBased)
        agent_token_estimates = agent_token_estimates or {}
        inflight_counts = inflight_counts or {}

        # Calculate used tokens from inflight
        used_tokens = 0
        for agent_id, count in inflight_counts.items():
            cost = max(1, int(agent_token_estimates.get(agent_id, 1)))
            used_tokens += count * cost

        remaining = max(0, self.max_token_sum - used_tokens)

        # Sequential allocation — fill in order until budget runs out
        final_alloc: Dict[str, str] = {}
        capacity_count: Dict[str, int] = {}
        budget_used = 0

        q_priority = {q.question_id: getattr(q, "priority", 99) for q in questions}
        sorted_q_ids = sorted(routing.keys(), key=lambda qid: q_priority.get(qid, 99))

        any_allocated = False
        for q_id in sorted_q_ids:
            agent_id = routing[q_id]
            cost = max(1, int(agent_token_estimates.get(agent_id, 1)))

            if budget_used + cost <= remaining:
                final_alloc[q_id] = agent_id
                budget_used += cost
                capacity_count[agent_id] = capacity_count.get(agent_id, 0) + 1
                any_allocated = True
            else:
                final_alloc[q_id] = ""  # Deferred to next round

        # Safety: if nothing was allocated AND all costs exceed max budget, force first task
        if not any_allocated and sorted_q_ids:
            min_cost = min(
                max(1, int(agent_token_estimates.get(routing[qid], 1)))
                for qid in sorted_q_ids
            )
            if min_cost > self.max_token_sum:
                q_id = sorted_q_ids[0]
                final_alloc[q_id] = routing[q_id]
                capacity_count[routing[q_id]] = capacity_count.get(routing[q_id], 0) + 1

        # Include all agents to prevent agent_capacities from shrinking
        self.latest_capacities = {a.value: capacity_count.get(a.value, 0) for a in AgentType}

        allocated = sum(1 for v in final_alloc.values() if v != "")
        deferred = sum(1 for v in final_alloc.values() if v == "")
        print(f"[LLM Allocator] Sequential budget: {budget_used}/{remaining} used, "
              f"Allocated: {allocated}, Deferred: {deferred}")

        return final_alloc
