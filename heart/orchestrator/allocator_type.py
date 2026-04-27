"""
TypeBased Task Allocator (Baseline)

Deterministically maps each question's TaskType to a predefined agent using
a fixed lookup table (TYPEBASED_MAPPING in configs/models.py).
No semantic matching or learning — purely rule-based routing.

Serves as a baseline to measure the value of semantic routing (HEART)
and LLM routing (LLM allocator). Uses the same sequential token budget
as the LLM allocator for fair comparison.
"""

from __future__ import annotations

import time
import re
from typing import List, Dict, Optional
from enum import Enum
from collections import Counter
from collections import defaultdict

from heart.core.schema import AgentType, ReasoningQuestion


# ----------------------------- Task-Agent Matching -----------------------------

class Rule_Based_TaskAssigner:
    """
    Assigns each reasoning task to the most semantically similar agent
    based on prompt-description cosine similarity using SentenceTransformer.
    """
    def __init__(self):
        self.agent_types = list(AgentType)
        # Rule-based mapping
        self.type_to_agent: Dict[str, AgentType] = {
            "ROBOT_CAPABILITY_ANALYSIS": AgentType.CAPABILITY_REASONER,
            "ACTION_FEASIBILITY": AgentType.CAPABILITY_REASONER,
            "OBJECT_DISCOVERY": AgentType.ENVIRONMENTAL_REASONER,
            "SCENE_UNDERSTANDING": AgentType.ENVIRONMENTAL_REASONER,
            "ROBOT_DISCOVERY": AgentType.PATH_REASONER,
            "PATH_PLANNING": AgentType.PATH_REASONER,
            "ROUTE_OPTIMIZATION": AgentType.PATH_REASONER,
            "PHYSICAL_FEASIBILITY": AgentType.FEASIBILITY_REASONER,
            "TASK_DEPENDENCY_ANALYSIS": AgentType.CONSTRAINT_REASONER,
            "ACTION_SEQUENCE_CONSTRAINTS": AgentType.CONSTRAINT_REASONER,
            "CONTEXTUAL_CONSTRAINTS": AgentType.CONSTRAINT_REASONER,
        }

    def assign(self,
               questions: List[ReasoningQuestion],
               previous_assignments: Optional[Dict[str, str]] = None,
               assignment_counts: Optional[Dict[str, Dict[str, int]]] = None,
               ) -> Dict[str, AgentType]:
        """
        Return mapping {question_id: agent_type} based on rule-based mapping.
        """
        assignments: Dict[str, AgentType] = {}

        for q in questions:
            task_type = q.question_type.upper()
            agent = self.type_to_agent.get(task_type, AgentType.CONSTRAINT_REASONER)
            # fallback: default to constraint_reasoner if unknown
            assignments[q.question_id] = agent

        return assignments
    
    def extract_prompt(self, text: str) -> str:
        matches = re.findall(r"Additional needed:\s*(.*)", text)
        if matches:
            # Return only the last "Additional needed" question
            return matches[-1].strip()
        else:
            # No match found — return full text as-is
            return text.strip()


# ----------------------------- Token Budget Planner -----------------------------

class AgentPool:
    def __init__(self, capacities: Dict[AgentType, int]):
        self.capacities = capacities
        self.busy = Counter()

    def available(self, agent: AgentType) -> int:
        return max(0, self.capacities.get(agent, 0) - self.busy.get(agent, 0))

    def acquire(self, agent: AgentType) -> bool:
        if self.available(agent) > 0:
            self.busy[agent] += 1
            return True
        return False

class TokenBudgetPlanner:
    """
    Computes how many agent instances can be launched under a token budget.
    Based on task-assigned agent demand and per-agent token cost.
    """
    def __init__(self, max_token_sum: int):
        self.max_token_sum = max(0, max_token_sum)

    def plan(self,
             task_assignments: Dict[str, AgentType],
             token_estimates: Dict[AgentType, int],
             inflight_counts: Optional[Dict[AgentType, int]] = None) -> AgentPool:

        inflight_counts = self._parse_agent_keys(inflight_counts or {})
        token_estimates = self._parse_agent_keys(token_estimates or {})

        demand = Counter(task_assignments.values())

        def cost_of(agent: AgentType) -> int:
            return max(1, int(token_estimates.get(agent, 1)))

        used_tokens = sum(inflight_counts.get(a, 0) * cost_of(a) for a in AgentType)
        remaining = max(0, self.max_token_sum - used_tokens)

        capacities: Dict[AgentType, int] = {a: 0 for a in AgentType}
        order = sorted([a for a in demand if demand[a] > 0], key=cost_of)

        for agent in order:
            if remaining <= 0:
                break

            # Special case: agent cost exceeds total budget → allow exactly one
            elif (remaining == self.max_token_sum and cost_of(agent) > remaining):
                capacities[agent] = 1
                remaining -= cost_of(agent)
                break

            c = cost_of(agent)
            max_new = remaining // c
            add = min(demand[agent], max_new)
            if add > 0:
                capacities[agent] = add
                remaining -= add * c

        return AgentPool(capacities)

    def _parse_agent_keys(self, d: Dict) -> Dict[AgentType, int]:
        """
        Accept both {str->int} and {AgentType->int}.
        """
        out: Dict[AgentType, int] = {}
        for a in AgentType:
            if a in d:
                out[a] = int(d[a])
            elif a.value in d:
                out[a] = int(d[a.value])
        return out


# ----------------------------- Main Allocator -----------------------------

class RuleBasedTaskAllocator:
    """
    Rule-based allocator with random-shuffle budget allocation.
    Routing: fixed task type → agent mapping.
    Budget: random shuffle over questions until budget is exhausted
    (no capacity planning — baseline for isolating HEART's mechanisms).
    """
    def __init__(self,
                 max_token_sum: int = 20000,
                 verbose: bool = True):

        self.assigner = Rule_Based_TaskAssigner()
        self.token_planner = TokenBudgetPlanner(max_token_sum=max_token_sum)
        self.max_token_sum = max_token_sum
        self.verbose = verbose
        self.latest_capacities: Dict[str, int] = {}

    def allocate(self,
                 questions: List[ReasoningQuestion],
                 agent_token_estimates: Dict[str, int] = None,
                 inflight_counts: Optional[Dict[str, int]] = None,
                 previous_assignments: Optional[Dict[str, str]] = None,
                 assignment_counts: Optional[Dict[str, Dict[str, int]]] = None,
                 active_agents: Optional[List[str]] = None,
                 ) -> Dict[str, str]:

        import random

        agent_token_estimates = agent_token_estimates or {}
        inflight_counts = inflight_counts or {}

        # 1) Rule-based routing — fixed mapping
        task_assignments = self.assigner.assign(
            questions,
            previous_assignments=previous_assignments,
            assignment_counts=assignment_counts,
        )

        # 2) Random-shuffle budget allocation (no capacity planning)
        token_costs = self.token_planner._parse_agent_keys(agent_token_estimates)
        inflight = self.token_planner._parse_agent_keys(inflight_counts)

        used_tokens = 0
        for agent, count in inflight.items():
            cost = max(1, int(token_costs.get(agent, 1)))
            used_tokens += count * cost
        remaining = max(0, self.max_token_sum - used_tokens)

        final_alloc: Dict[str, str] = {}
        capacity_count: Dict[str, int] = {}
        budget_used = 0

        shuffled_qs = list(questions)
        random.shuffle(shuffled_qs)
        any_allocated = False
        for q in shuffled_qs:
            agent = task_assignments[q.question_id]
            agent_str = agent.value
            cost = max(1, int(token_costs.get(agent, 1)))

            if budget_used + cost <= remaining:
                final_alloc[q.question_id] = agent_str
                budget_used += cost
                capacity_count[agent_str] = capacity_count.get(agent_str, 0) + 1
                any_allocated = True
            else:
                # Budget exceeded — stop immediately, defer all remaining
                for remaining_q in shuffled_qs:
                    if remaining_q.question_id not in final_alloc:
                        final_alloc[remaining_q.question_id] = ""
                break

        # Safety: if nothing was allocated AND all agent costs exceed max budget,
        # force allocate first task to prevent infinite loop.
        if not any_allocated and shuffled_qs:
            min_cost = min(
                max(1, int(token_costs.get(task_assignments[q.question_id], 1)))
                for q in shuffled_qs
            )
            if min_cost > self.max_token_sum:
                q = shuffled_qs[0]
                agent = task_assignments[q.question_id]
                final_alloc[q.question_id] = agent.value
                capacity_count[agent.value] = capacity_count.get(agent.value, 0) + 1

        self.latest_capacities = {a.value: capacity_count.get(a.value, 0) for a in AgentType}

        if self.verbose:
            allocated = sum(1 for v in final_alloc.values() if v != "")
            total = len(questions)
            deferred = total - allocated
            print(f"[TypeBased Allocator] Random-shuffle budget: allocated={allocated}, deferred={deferred}")
            for k, v in final_alloc.items():
                if v:
                    print(f"  {k} → {v}")

        return final_alloc

    def _parse_agent_keys(self, d: Dict[str, int]) -> Dict[AgentType, int]:
        out: Dict[AgentType, int] = {}
        for a in AgentType:
            key = a.value
            if key in d:
                out[a] = int(d[key])
        return out