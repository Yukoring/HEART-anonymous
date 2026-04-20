"""
HEART Allocator (Stage 2)

Assigns each decomposed reasoning question to the most suitable expert agent.
Three components work together:

1. SemanticTaskAssigner: Uses Sentence-BERT embeddings to compute cosine similarity
   between question prompts and agent role descriptions. Supports history-aware
   penalties to discourage re-assigning failed questions to the same agent.

2. TokenBudgetPlanner: Given a per-round token budget, computes how many agent
   instances can run in parallel based on each agent's estimated token cost.

3. TaskAllocator: Combines semantic assignment with budget-aware capacity planning.
   Supports ablation flags (use_capacity_planning, use_history_penalty) for
   isolating each component's contribution.

For single-agent mode (homogeneous), bypasses Sentence-BERT entirely.
"""

from __future__ import annotations

import time
import re
from typing import List, Dict, Optional
from enum import Enum
from sentence_transformers import SentenceTransformer, util
from collections import Counter
from collections import defaultdict

from heart.core.schema import AgentType, ReasoningQuestion


# ----------------------------- Task-Agent Matching -----------------------------

class SemanticTaskAssigner:
    """
    Assigns each reasoning task to the most semantically similar agent
    based on prompt-description cosine similarity using SentenceTransformer.
    """
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name, device='cpu')

        # Cache agent descriptions and their embeddings
        self.agent_types = list(AgentType)
        self.agent_texts = [a.description for a in self.agent_types]
        self.agent_embeddings = self.model.encode(self.agent_texts, convert_to_tensor=True)

    def assign(self,
               questions: List[ReasoningQuestion],
               previous_assignments: Optional[Dict[str, str]] = None,
               assignment_counts: Optional[Dict[str, Dict[str, int]]] = None,
               use_history_penalty: bool = True,
               active_agents: Optional[List[str]] = None,
               ) -> Dict[str, AgentType]:
        """
        Return mapping {question_id: best_matching_agent_type}.
        If use_history_penalty=True and previous_assignments[qid] exists,
        penalize that agent for this task.
        If active_agents is provided, only consider those agents as candidates.
        """
        prompts = [self.extract_prompt(q.prompt) for q in questions]
        task_types = [q.question_type for q in questions]
        task_embeddings = self.model.encode(prompts, convert_to_tensor=True)
        task_types_embeddings = self.model.encode(task_types, convert_to_tensor=True)

        sim_matrix1 = util.cos_sim(task_embeddings, self.agent_embeddings)
        sim_matrix2 = util.cos_sim(task_types_embeddings, self.agent_embeddings)
        sim_matrix = (sim_matrix1 + sim_matrix2)

        # Build mask for active agents only
        active_set = None
        if active_agents:
            active_set = set(active_agents)

        assignments: Dict[str, AgentType] = {}
        for i, q in enumerate(questions):
            scores = sim_matrix[i].clone()

            # Mask out inactive agents (set score to -inf)
            if active_set:
                for j, agent in enumerate(self.agent_types):
                    if agent.value not in active_set:
                        scores[j] = float('-inf')

            # ---- history-aware penalties (skipped when use_history_penalty=False) ----
            if use_history_penalty:
                per_try = 0.16  # penalty per previous try of that agent original = 0.08
                last_bonus = 0.12  # extra penalty for the very last tried agent
                cap = 0.60  # cap total penalty so we don't go crazy

                if assignment_counts and q.question_id in assignment_counts:
                    counts = assignment_counts[q.question_id]  # {agent_str: count}
                    for agent_str, cnt in counts.items():
                        try:
                            a = AgentType(agent_str)
                        except ValueError:
                            continue
                        idx = self.agent_types.index(a)
                        penalty = min(cap, per_try * max(0, int(cnt)))
                        if previous_assignments and previous_assignments.get(q.question_id) == agent_str:
                            penalty = min(cap, penalty + last_bonus - per_try)
                        scores[idx] -= penalty

            best_idx = int(scores.argmax())
            best_agent = self.agent_types[best_idx]
            assignments[q.question_id] = best_agent

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
        order = sorted([a for a in demand if demand[a] > 0], key=cost_of, reverse=True)

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

class TaskAllocator:
    def __init__(self,
                 max_token_sum: int,
                 model_name: str = "all-mpnet-base-v2",
                 verbose: bool = True,
                 use_capacity_planning: bool = True,
                 use_history_penalty: bool = True):

        self._assigner = None  # Lazy loaded — only when multi-agent routing needed
        self._model_name = model_name
        self.token_planner = TokenBudgetPlanner(max_token_sum=max_token_sum)
        self.max_token_sum = max_token_sum
        self.verbose = verbose
        self.use_capacity_planning = use_capacity_planning
        self.use_history_penalty = use_history_penalty

        self.latest_capacities: Dict[str, int] = {}

    @property
    def assigner(self):
        """Lazy load SemanticTaskAssigner — avoids loading Sentence-BERT for single-agent mode."""
        if self._assigner is None:
            self._assigner = SemanticTaskAssigner(model_name=self._model_name)
        return self._assigner

    def allocate(self,
                 questions: List[ReasoningQuestion],
                 agent_token_estimates: Dict[str, int],
                 inflight_counts: Optional[Dict[str, int]] = None,
                 previous_assignments: Optional[Dict[str, str]] = None,
                 assignment_counts: Optional[Dict[str, Dict[str, int]]] = None,
                 active_agents: Optional[List[str]] = None,
                 ) -> Dict[str, str]:

        # Parse costs/inflight robustly (supports both str and AgentType keys)
        token_costs = self.token_planner._parse_agent_keys(agent_token_estimates or {})
        inflight = self.token_planner._parse_agent_keys(inflight_counts or {})

        # Single agent shortcut — skip Sentence-BERT routing and AgentType enum
        if active_agents and len(active_agents) == 1:
            agent_id = active_agents[0]

            # Get token cost — check both raw agent_token_estimates and parsed token_costs
            agent_token_cost = max(1, int(
                agent_token_estimates.get(agent_id, 0) or
                token_costs.get(agent_id, 1)
            ))

            # Calculate current inflight from raw inflight_counts (string keys)
            current_inflight = int(inflight_counts.get(agent_id, 0)) if inflight_counts else 0

            # Budget-aware capacity calculation
            used_tokens = current_inflight * agent_token_cost
            remaining = max(0, self.token_planner.max_token_sum - used_tokens)
            capacity = remaining // agent_token_cost if agent_token_cost > 0 else len(questions)
            capacity = max(1, min(5, capacity))  # Cap at 5 for stability (same as original)

            # Assign up to capacity by priority, rest stays unallocated ("")
            final_alloc: Dict[str, str] = {}
            sorted_qs = sorted(questions, key=lambda x: getattr(x, "priority", 99))
            for q in sorted_qs:
                if len(final_alloc) < capacity:
                    final_alloc[q.question_id] = agent_id
                else:
                    final_alloc[q.question_id] = ""  # Deferred to next round

            self.latest_capacities = {agent_id: capacity}

            if self.verbose:
                allocated = sum(1 for v in final_alloc.values() if v != "")
                deferred = sum(1 for v in final_alloc.values() if v == "")
                print(f"[Allocator] Single-agent mode:")
                print(f"  Agent: {agent_id} (cost: {agent_token_cost} tokens)")
                print(f"  Inflight: {current_inflight}, Used: {used_tokens}/{self.token_planner.max_token_sum}")
                print(f"  Capacity: {capacity} tasks this round")
                print(f"  Allocated: {allocated}, Deferred: {deferred}")

            return final_alloc

        # Multi-agent: Sentence-BERT semantic assignment
        # 1) Semantic assignment (with optional penalty on last tried agent)
        task_assignments = self.assigner.assign(
            questions,
            previous_assignments=previous_assignments,
            assignment_counts=assignment_counts,
            use_history_penalty=self.use_history_penalty,
            active_agents=active_agents,
        )



        if self.use_capacity_planning:
            # 2a) TokenBudgetPlanner: demand-based capacity per agent
            pool = self.token_planner.plan(task_assignments, token_costs, inflight)

            # 3a) Take as many as capacity allows by priority per agent
            grouped: Dict[AgentType, List[ReasoningQuestion]] = defaultdict(list)
            for q in questions:
                agent = task_assignments[q.question_id]
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
        else:
            # 2b) Random budget: randomly pick subtasks until budget exceeded
            import random

            used_tokens = 0
            for agent_id, count in (inflight or {}).items():
                cost = max(1, int(token_costs.get(agent_id, 1)))
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

            # Include all active agents in capacities (not just allocated ones)
            # to prevent agent_capacities from shrinking in nodes.py
            self.latest_capacities = {a.value: capacity_count.get(a.value, 0) for a in AgentType}

        if self.verbose:
            mode = "capacity planning" if self.use_capacity_planning else "sequential budget"
            penalty = "ON" if self.use_history_penalty else "OFF"
            print(f"[Allocator] Mode: {mode}, History penalty: {penalty}")
            print(f"[Allocator] Final assignment:")
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