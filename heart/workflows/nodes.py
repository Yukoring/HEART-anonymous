"""
HEART Workflow Nodes

LangGraph node functions implementing the 5-stage HEART pipeline:
  1. decompose_node: Instruction → atomic reasoning questions (Stage 1)
  2. allocate_node: Questions → agent assignments under token budget (Stage 2)
  3. execute_node (per agent): Run reasoning on assigned questions (Stage 3)
  4. synthesize_node: Cross-validate Q&A → planner constraints (Stage 4)
  5. plan_node: Generate executable plan via LLM-CoT or DELTA (Stage 5)
  6. metrics_collection_node: Aggregate per-stage token/time metrics

Each node reads from and writes to the shared LangGraph SystemState.
Agent instances are lazily initialized and cached across rounds.
"""

from typing import Dict, Any, List, Union
from collections import Counter
from heart.core.state import SystemState, StateReducer, StageType
from heart.core.schema import AgentType

# Import only when needed to avoid dependency issues during testing
try:
    from heart.orchestrator.task_decomposer import TaskDecomposer
    from heart.orchestrator.allocator_llm import LLMTaskAllocator
    from heart.orchestrator.allocator import TaskAllocator
    from heart.orchestrator.allocator_type import RuleBasedTaskAllocator
except ImportError as e:
    print(f"[WARNING] Import error: {e}")
    TaskDecomposer = None
    LLMTaskAllocator = None
    TaskAllocator = None


# ==================== Stage 1: Task Decomposition ====================

# Global instances for state persistence and component reuse
_decomposer_instance = None
_agent_instances = {}  # {agent_id: ReasoningAgent instance}

def decompose_node(state: SystemState) -> SystemState:
    """
    Stage 1: Task Decomposition Node

    Handles both initial decomposition and refinement.
    Dynamically creates ReasoningAgent instances based on agent list in state.
    Works for any number of agents (1, 3, 5, etc.).
    """
    global _decomposer_instance, _agent_instances
    from heart.core.schema import QuestionDecomposition, ReasoningQuestion
    from heart.agents.reasoning_agent import ReasoningAgent
    from heart.configs.models import REASONING_AGENTS

    decompose_data = StateReducer.for_decomposer(state)

    # Initialize decomposer only once
    if _decomposer_instance is None:
        _decomposer_instance = TaskDecomposer(env_data=decompose_data["env_data"])

    StateReducer.set_stage(state, StageType.DECOMPOSE)

    is_refinement = decompose_data["decompose_num"] > 0
    decompose_try = decompose_data["decompose_num"] + 1

    print(f"\n{'='*60}")
    print(f"[DECOMPOSE NODE] Attempt #{decompose_try}")
    print(f"Mode: {'Refinement' if is_refinement else 'Initial'}")
    print(f"Instruction: {state['instruction']}")

    if is_refinement:
        previous_questions = decompose_data["questions"]
        num_questions = len(previous_questions)
        if num_questions < 5:
            issue = f"Too few questions ({num_questions}) - need at least 5"
        elif num_questions > 20:
            issue = f"Too many questions ({num_questions}) - maximum 20"
        else:
            issue = "Quality issues detected"

        current_decomposition = QuestionDecomposition(
            instruction=state["instruction"],
            questions=[ReasoningQuestion(**q) for q in previous_questions.values()]
        )
        decompose = _decomposer_instance.refine(decompose=current_decomposition, issues=[issue])
    else:
        decompose = _decomposer_instance.decompose(instruction=decompose_data["instruction"])

    print(f"\n[DECOMPOSE RESULTS]")
    print(f"Questions generated: {len(decompose.questions)}")
    for i, q in enumerate(decompose.questions, 1):
        print(f"  {i}. [{q.question_type}] {q.prompt}")

    # Initialize agent instances dynamically from state's agent list
    agent_token_estimates = None

    if not _agent_instances and not is_refinement:
        env_data = state.get("env_data", {})
        # Get agent list from state (set by initialize_state)
        agent_ids = list(state.get("agent_capacities", {}).keys())

        # Get model/temperature from config
        from heart.configs.models import USE_AGENT_MEMORY
        _agent_instances = {}
        for agent_id in agent_ids:
            config = REASONING_AGENTS.get(agent_id, {"model": "gpt-4o", "temperature": 0.1})
            _agent_instances[agent_id] = ReasoningAgent(
                agent_id=agent_id,
                model_name=config["model"],
                temperature=config["temperature"],
                env_data=env_data,
                use_memory=USE_AGENT_MEMORY,
            )

        print(f"\n[AGENTS INITIALIZED] {list(_agent_instances.keys())}")

        # Get token estimates from each agent
        agent_token_estimates = {
            agent_id: agent.estimated_tokens
            for agent_id, agent in _agent_instances.items()
        }

    # Merge decomposition results into state
    state = StateReducer.merge_decomposition(state, decompose, decompose_try, agent_token_estimates)

    # Display decomposer metrics
    if _decomposer_instance and hasattr(_decomposer_instance, 'agent'):
        print(f"\n[DECOMPOSER METRICS]")
        print(f"Total tokens used: {_decomposer_instance.agent.total_tokens}")
        print(f"Total execution time: {_decomposer_instance.agent.total_time:.2f}s")
        print(f"Memory entries: {len(_decomposer_instance.agent.memory)}")

        state = _initialize_stage_metrics(state)
        state["evaluation_metrics"]["stage_1_decomposer"] = {
            "tokens": _decomposer_instance.agent.total_tokens,
            "time": _decomposer_instance.agent.total_time,
            "attempts": decompose_try
        }

    print(f"{'='*60}\n")
    return state


# Use initialize_state(agents=["homogeneous_reasoner"]) for homogeneous experiments


# ==================== Stage 2: Task Allocation (Unified) ====================

_allocator_instance = None
_allocator_instance_llm = None

def allocate_node(state: SystemState) -> SystemState:
    """
    Unified allocation node — handles all allocator types.
    Allocator type is read from state["allocator_type"].
    Supports any number of agents (1, 3, 5, etc.).
    """
    global _allocator_instance, _allocator_instance_llm
    from heart.core.schema import ReasoningQuestion
    import time

    allocator_start_time = time.time()
    allocator_type = state.get("allocator_type", "heart")
    active_agents = list(state.get("agent_capacities", {}).keys())
    budget = state.get("token_budget", 20000)

    # Parse HEART allocator variant flags
    HEART_VARIANTS = {
        "heart":                {"use_capacity_planning": True,  "use_history_penalty": True},
        "heart_no_penalty":     {"use_capacity_planning": True,  "use_history_penalty": False},
        "heart_no_capacity":    {"use_capacity_planning": False, "use_history_penalty": True},
        "heart_semantic_only":  {"use_capacity_planning": False, "use_history_penalty": False},
    }

    # Initialize allocator based on type (only once)
    if allocator_type in HEART_VARIANTS:
        if _allocator_instance is None:
            flags = HEART_VARIANTS[allocator_type]
            _allocator_instance = TaskAllocator(
                max_token_sum=budget,
                use_capacity_planning=flags["use_capacity_planning"],
                use_history_penalty=flags["use_history_penalty"],
            )
        allocator = _allocator_instance
    elif allocator_type == "type_based":
        if _allocator_instance is None:
            _allocator_instance = RuleBasedTaskAllocator(max_token_sum=budget)
        allocator = _allocator_instance
    elif allocator_type == "llm":
        if _allocator_instance_llm is None:
            env_data = state.get("env_data", {})
            _allocator_instance_llm = LLMTaskAllocator(env_data=env_data, max_token_sum=budget)
        allocator = _allocator_instance_llm
    else:
        # Unknown type — default to full HEART
        if _allocator_instance is None:
            _allocator_instance = TaskAllocator(max_token_sum=budget)
        allocator = _allocator_instance

    # Update workflow stage
    StateReducer.set_stage(state, StageType.ALLOCATION)

    # state.setdefault("allocation_prompt_hash", {})
    # state.setdefault("last_agent_for_task", {})

    # Update agent_token_estimates with current values
    for agent_type, agent in _agent_instances.items():
        if hasattr(agent, 'estimated_tokens'):
            state['agent_token_estimates'][agent_type] = agent.estimated_tokens

    # Display node execution status
    print(f"\n{'='*60}")
    print(f"[ALLOCATE NODE - {allocator_type.upper()}]")
    print(f"Agents: {active_agents}")
    print(f"Token Estimates: {state['agent_token_estimates']}")
    
    # Stage 3 Metric Merge — read from agent instances (parallel-safe, no executor state mutation)
    state = _initialize_stage_metrics(state)
    if _agent_instances:
        # Agent cumulative totals (auto-accumulated via add_to_memory)
        total_agent_tokens = sum(getattr(a, 'total_tokens', 0) for a in _agent_instances.values())
        # cumulative_llm_time = sum of every agent's LLM call durations across all rounds.
        # This over-counts parallel work within a round (5 agents in parallel are summed).
        # Wall-clock for the agent stage is computed in metrics_collection_node from
        # round timestamps and stored in stage_3_agents["time"].
        cumulative_llm_time = sum(getattr(a, 'total_time', 0.0) for a in _agent_instances.values())
        state["evaluation_metrics"]["stage_3_agents"]["tokens"] = total_agent_tokens
        state["evaluation_metrics"]["stage_3_agents"]["cumulative_llm_time"] = cumulative_llm_time

        # Per-agent details
        if "agent_details" not in state["evaluation_metrics"]:
            state["evaluation_metrics"]["agent_details"] = {}
        for agent_id, agent in _agent_instances.items():
            state["evaluation_metrics"]["agent_details"][agent_id] = {
                "total_tokens": getattr(agent, 'total_tokens', 0),
                "total_time": getattr(agent, 'total_time', 0.0),
                "task_count": len(getattr(agent, 'memory', [])),
            }

        # Per-task details — rebuild from all memory entries each time
        # (agent.memory is cumulative, so we rebuild to avoid double-counting)
        task_details = {}
        for agent_id, agent in _agent_instances.items():
            for mem in getattr(agent, 'memory', []):
                task_id = mem.get('task_id', '')
                if not task_id:
                    continue
                response = mem.get('response')
                status = str(getattr(response, 'status', 'unknown')) if response else 'unknown'
                tokens = mem.get('tokens_used', 0)
                exec_time = mem.get('execution_time', 0.0)

                if task_id in task_details:
                    # Retry — accumulate tokens/time, update status/agent to latest
                    task_details[task_id]["tokens"] += tokens
                    task_details[task_id]["time"] += exec_time
                    task_details[task_id]["status"] = status
                    task_details[task_id]["agent"] = agent_id
                else:
                    task_details[task_id] = {
                        "tokens": tokens,
                        "time": exec_time,
                        "agent": agent_id,
                        "status": status,
                    }
        state["evaluation_metrics"]["task_details"] = task_details

    MAX_RETRIES = 5

    state = StateReducer.remove_completed_tasks(state)
    
    # Move tasks exceeding retry limit to failed
    state = StateReducer.move_tasks_to_failed(state, MAX_RETRIES)

    questions_to_allocate = []
    for q_id, agent in state.get("allocation_map", {}).items():
        if agent == "":  # Unallocated
            if q_id in state.get("questions", {}):
                questions_to_allocate.append(state["questions"][q_id])

    # Calculate allocation statistics
    allocation_map = state.get("allocation_map", {})
    completed_tasks = state.get("completed_tasks", {})
    failed_tasks = state.get("failed_tasks", {})
    
    unallocated = sum(1 for v in allocation_map.values() if v == "")
    allocated = sum(1 for v in allocation_map.values() if v != "")
    
    # Display allocation state
    print(f"State after cleanup:")
    print(f"  Completed: {len(completed_tasks)} tasks")
    print(f"  Failed: {len(failed_tasks)} tasks (exceeded {MAX_RETRIES} retries)")
    print(f"  Allocated: {allocated} tasks (in progress)")
    print(f"  Unallocated: {unallocated} tasks (need allocation)")
    
    if questions_to_allocate:
        print(f"\n[{allocator_type.upper()} ALLOCATION] Allocating {len(questions_to_allocate)} questions...")

        reasoning_questions = [ReasoningQuestion(**q) for q in questions_to_allocate]

        # Count inflight tasks per agent (only active agents)
        inflight_counts = Counter()
        active_set = set(active_agents)
        for agent_str in state.get("allocation_map", {}).values():
            if agent_str and agent_str in active_set:
                inflight_counts[agent_str] += 1

        token_estimates = state.get("agent_token_estimates", {})

        if allocator_type == "llm":
            # LLM allocator — routing by GPT-4o, budget applied internally
            original_instruction = state.get("instruction", "")
            allocation_result = allocator.allocate(
                reasoning_questions, original_instruction,
                agent_token_estimates=state.get("agent_token_estimates", {}),
                inflight_counts=dict(inflight_counts),
            )
        else:
            # HEART / TypeBased — with history penalty

            # Build history-aware penalty inputs
            history = state.get("allocation_history", {})
            last_agent_map = {}
            attempt_counts = {}

            if isinstance(history, dict):
                for qid, seq in history.items():
                    if not seq:
                        continue
                    seq_filt = [a for a in seq if isinstance(a, str) and a]
                    if not seq_filt:
                        continue
                    last_agent_map[qid] = seq_filt[-1]
                    attempt_counts[qid] = dict(Counter(seq_filt))

            allocation_result = allocator.allocate(
                reasoning_questions,
                agent_token_estimates=state.get("agent_token_estimates", {}),
                inflight_counts=inflight_counts,
                previous_assignments=last_agent_map,
                assignment_counts=attempt_counts,
                active_agents=active_agents,
            )

        if hasattr(allocator, "latest_capacities"):
            # Only update capacities for agents that were initialized (not all AgentType enum)
            original_agents = set(state.get("agent_capacities", {}).keys())
            state["agent_capacities"] = {
                k: v for k, v in allocator.latest_capacities.items()
                if k in original_agents
            }

        # DEBUG: Show per-question allocation decisions
        print(f"\n[ALLOCATION RESULTS]")
        for q_id, agent in sorted(allocation_result.items(), key=lambda x: int(x[0][1:]) if x[0][1:].isdigit() else 0):
            status = "ALLOCATED" if agent else "DEFERRED"
            print(f"  {q_id} → {agent if agent else '(deferred)'} [{status}]")

        agent_counts = {}
        allocated_tokens = 0
        for q_id, agent in allocation_result.items():
            if agent:
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
                allocated_tokens += max(1, int(token_estimates.get(agent, 1)))
        for agent, count in sorted(agent_counts.items()):
            cost = max(1, int(token_estimates.get(agent, 1)))
            print(f"  {agent}: {count} tasks (est. {cost * count} tokens)")
        print(f"  Estimated round usage: {allocated_tokens}/{budget} ({allocated_tokens/budget*100:.0f}%)")
        
        # Filter out allocations to non-active agents (e.g., LLM allocator may hallucinate agent names)
        filtered_result = {}
        for q_id, agent in allocation_result.items():
            if agent and agent not in active_set:
                print(f"  WARNING: {q_id} allocated to non-active agent '{agent}' → deferred")
                filtered_result[q_id] = ""
            else:
                filtered_result[q_id] = agent

        # Merge allocation results into state (only once)
        state = StateReducer.merge_allocation(state, filtered_result)

    state = StateReducer.distribute_pending_to_agents(state)
    
    # Calculate allocator time
    allocator_end_time = time.time()
    allocator_time = allocator_end_time - allocator_start_time

    # Initialize stage metrics
    state = _initialize_stage_metrics(state)

    # Get allocator tokens (LLM allocator uses tokens, others don't)
    # Use delta (current cumulative - previously recorded) to avoid double counting
    allocator_tokens = 0
    if allocator_type == "llm" and _allocator_instance_llm and hasattr(_allocator_instance_llm, 'agent'):
        current_total = _allocator_instance_llm.agent.total_tokens
        prev_total = state["evaluation_metrics"]["stage_2_allocator"].get("_prev_cumulative", 0)
        allocator_tokens = current_total - prev_total
        state["evaluation_metrics"]["stage_2_allocator"]["_prev_cumulative"] = current_total

    # Update stage 2 allocator metrics
    state["evaluation_metrics"]["stage_2_allocator"]["time"] += allocator_time
    state["evaluation_metrics"]["stage_2_allocator"]["tokens"] += allocator_tokens

    # Calculate round number
    if "rounds" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["rounds"] = []
    round_num = len(state["evaluation_metrics"]["rounds"]) + 1

    # Count task distribution if allocation happened
    agent_distribution = {}
    if 'allocation_result' in locals():
        for agent in allocation_result.values():
            if agent:
                agent_distribution[agent] = agent_distribution.get(agent, 0) + 1

    # Create simplified round metrics
    state["evaluation_metrics"]["rounds"].append({
        "round_num": round_num,
        "timestamp": allocator_end_time,
        "allocated_tasks": len([v for v in allocation_result.values() if v]) if 'allocation_result' in locals() else 0,
        "unallocated_tasks": len([v for v in allocation_result.values() if not v]) if 'allocation_result' in locals() else 0,
        "completed_count": len(state.get("completed_tasks", {})),
        "failed_count": len(state.get("failed_tasks", {})),
        "agent_distribution": agent_distribution,
        "allocator_time": allocator_time,
        "allocator_tokens": allocator_tokens
    })

    print(f"{'='*60}\n")

    return state



# ==================== Stage 3: Reasoning Execution ====================
# ==================== Stage 3: Reasoning Execution ====================

# Executor instances for each agent type
_executor_instances = {}

def get_executor_for_agent(agent_type: str, instruction: str, env_data: Dict[str, Any] = None):
    """
    Get or create executor instance for specific agent type.
    Reuses existing agent instances when available.
    
    Args:
        agent_type: Type of agent (e.g., "capability_reasoner")
        instruction: Original instruction for context
        env_data: Environment data (required if agent not yet initialized)
    """
    global _executor_instances, _agent_instances

    # Fallback: create agent if not already initialized (e.g., edge case)
    if agent_type not in _agent_instances:
        if not env_data:
            raise ValueError(f"env_data required to create agent {agent_type}")
        from heart.agents.reasoning_agent import ReasoningAgent
        from heart.configs.models import REASONING_AGENTS, USE_AGENT_MEMORY
        config = REASONING_AGENTS.get(agent_type, {"model": "gpt-4o", "temperature": 0.1})
        _agent_instances[agent_type] = ReasoningAgent(
            agent_id=agent_type,
            model_name=config["model"],
            temperature=config["temperature"],
            env_data=env_data,
            use_memory=USE_AGENT_MEMORY
        )

    # Create executor wrapper if not exists
    if agent_type not in _executor_instances:
        from heart.orchestrator.executor import ReasoningExecutor
        _executor_instances[agent_type] = ReasoningExecutor(
            agent_type=agent_type,
            instruction=instruction,
            agent_instance=_agent_instances[agent_type]
        )

    return _executor_instances[agent_type]


def executor_node(state: SystemState, agent_type: str) -> Dict[str, Any]:
    """
    Stage 3: Task Execution Node
    
    Processes tasks for a specific agent type.
    Returns partial state updates for parallel execution.
    
    Args:
        state: Current system state
        agent_type: Agent type to execute (e.g., "capability_reasoner")
        
    Returns:
        Partial state update containing only changed fields
    """
    # Extract executor data for this agent
    executor_data = StateReducer.for_executor(state, agent_type)
    
    if not executor_data["tasks"]:
        return {}  # No tasks to process
    
    # Display execution header
    agent_display_name = agent_type.upper().replace('_', ' ')
    print(f"\n[EXECUTOR: {agent_display_name}]")
    print(f"Processing {len(executor_data['tasks'])} tasks...")
    
    # Get or create executor for this agent type
    executor = get_executor_for_agent(
        agent_type, 
        instruction=executor_data["instruction"],
        env_data=executor_data["env_data"]  # Pass env_data for agent creation
    )
    
    # Execute agent reasoning tasks
    results = executor.execute_tasks_for_agent(
        agent_name=agent_type,
        tasks=executor_data["tasks"]
    )
    
    # Handle execution failures
    if not results:
        print(f"  ERROR: No results returned")
        # Mark all tasks for retry
        update = {
            "allocation_map": {},
            "agent_tasks": {agent_type: set()}  # Clear from agent_tasks
        }
        for task_id in executor_data["task_ids"]:
            update["allocation_map"][task_id] = ""  # Mark for reallocation
        return update
    
    # Display and summarize results (read-only — no state mutation for parallel safety)
    total_tokens = 0
    total_time = 0.0

    for result in results:
        task_id = result.get("task_id", "")
        status = result.get("status", "UNKNOWN")
        tokens = result.get("tokens_used", 0)
        exec_time = result.get("execution_time", 0.0)

        total_tokens += tokens
        total_time += exec_time

        print(f"  {task_id}: {status} ({tokens} tokens, {exec_time:.1f}s)")

    memory_count = 0
    cumulative_tokens = 0
    if agent_type in _agent_instances:
        agent = _agent_instances[agent_type]
        if hasattr(agent, 'memory') and agent.memory:
            memory_count = len(agent.memory)
        if hasattr(agent, 'total_tokens'):
            cumulative_tokens = agent.total_tokens

    print(f"Summary: Memory={memory_count} | Cumulative={cumulative_tokens} tokens | This run={total_tokens} tokens, {total_time:.1f}s")

    # Return ONLY partial state update (no state mutation — safe for parallel execution)
    return StateReducer.process_execution_results(
        results=results,
        agent_type=agent_type,
        current_questions=state.get("questions", {})
    )



# ==================== Stage 4: Synthesis ====================

_synthesis_agent_instance = None

def synthesize_node(state: SystemState) -> SystemState:
    """
    Stage 4: Synthesis Node

    1. Formats raw Q&A results (Synthesizer.format_constraints)
    2. Cross-validates and consolidates via SynthesisAgent (LLM)
    3. Produces clean heart_constraints_text for planner

    Does NOT call a planner — that's plan_node (Stage 5).
    """
    global _synthesis_agent_instance
    from heart.orchestrator.synthesizer import Synthesizer
    from heart.agents.synthesis_agent import SynthesisAgent
    import time

    synthesis_start_time = time.time()

    print("\n" + "="*60)
    print("[SYNTHESIS STAGE] Cross-validating Q&A constraints")
    print("="*60)

    # Step 1: Format raw Q&A
    raw_qa = Synthesizer.format_constraints(state)

    if not raw_qa:
        print("No constraints generated (no completed tasks)")
        state = _initialize_stage_metrics(state)
        state["evaluation_metrics"]["stage_4_synthesis"] = {"tokens": 0, "time": 0.0}
        return {
            "heart_constraints_text": "",
            "current_stage": StageType.SYNTHESIS,
            "evaluation_metrics": state.get("evaluation_metrics", {}),
        }

    print(f"Raw Q&A: {len(raw_qa)} chars")

    # Step 2: Cross-validate via SynthesisAgent
    if _synthesis_agent_instance is None:
        from heart.configs.models import SYNTHESIS_CONFIG
        _synthesis_agent_instance = SynthesisAgent(
            model_name=SYNTHESIS_CONFIG["model"],
            temperature=SYNTHESIS_CONFIG["temperature"],
        )

    instruction = state.get("instruction", "")
    # Detect multi-robot from env_data
    env_data = state.get("env_data", {})
    num_robots = len(env_data.get("robots", {})) if env_data else 1

    result = _synthesis_agent_instance.synthesize(instruction=instruction, raw_qa=raw_qa, num_robots=num_robots)

    heart_constraints_text = result["constraints_text"]
    synthesis_tokens = result["tokens_used"]

    # Fallback: if synthesis produced empty output, use raw Q&A
    if not heart_constraints_text:
        print("[SYNTHESIS] Agent returned empty — using raw Q&A as fallback")
        heart_constraints_text = raw_qa

    state["heart_constraints_text"] = heart_constraints_text

    # Display results
    print(f"\nSynthesized: {len(heart_constraints_text)} chars (from {len(raw_qa)} raw)")
    if result["feasible_objects"]:
        print(f"Feasible objects: {result['feasible_objects']}")
    if result["infeasible_objects"]:
        print(f"Infeasible objects: {result['infeasible_objects']}")

    # Preview
    lines = heart_constraints_text.split('\n')[:8]
    for line in lines:
        print(f"  {line}")
    if len(heart_constraints_text.split('\n')) > 8:
        print(f"  ... ({len(heart_constraints_text.split(chr(10)))} lines total)")

    synthesis_time = time.time() - synthesis_start_time

    state = _initialize_stage_metrics(state)
    state["evaluation_metrics"]["stage_4_synthesis"] = {
        "tokens": synthesis_tokens,
        "time": synthesis_time,
    }

    print(f"\nSynthesis time: {synthesis_time:.2f}s, tokens: {synthesis_tokens}")
    print(f"{'='*60}\n")

    return {
        "heart_constraints_text": heart_constraints_text,
        "current_stage": StageType.SYNTHESIS,
        "evaluation_metrics": state.get("evaluation_metrics", {}),
    }


def plan_node(state: SystemState) -> SystemState:
    """
    Stage 5: Plan Generation Node

    Calls the configured planner with HEART's reasoning results.
    Planner type is determined by state["planner_type"].
    Skipped if planner_type is None (reasoning-only mode).
    """
    import time

    planner_type = state.get("planner_type")
    if not planner_type:
        print("[PLAN NODE] No planner configured — reasoning only mode")
        state["current_stage"] = StageType.COMPLETED
        return state

    plan_start_time = time.time()

    print("\n" + "="*60)
    print(f"[PLAN NODE] Planner: {planner_type}")
    print("="*60)

    try:
        # Load planner based on type
        if planner_type == "llm_cot":
            from planners.llm_cot.llm_cot_planner import LLMCoTPlanner
            planner = LLMCoTPlanner()
        elif planner_type == "delta":
            from planners.delta.delta_planner import DeltaPlanner
            planner = DeltaPlanner()
        else:
            raise ValueError(f"Unknown planner type: {planner_type}")

        # Call planner with clean inputs + planner-specific config
        planner_config = state.get("planner_config", {})
        result = planner.plan(
            instruction=state["instruction"],
            env_data=state["env_data"],
            heart_constraints=state.get("heart_constraints_text", ""),
            **planner_config,
        )

        # Store results
        actions = result.get("plan", [])
        state["final_plan"] = actions
        state["plan_steps"] = actions
        if result.get("plan_orig"):
            state["plan_orig"] = result["plan_orig"]

        # Display plan
        is_multi_robot = any(a.startswith("#") for a in actions if isinstance(a, str))
        if is_multi_robot:
            actual_actions = [a for a in actions if not a.startswith("#")]
            print(f"Generated multi-robot plan with {len(actual_actions)} actions")
            for action in actions:
                if action.startswith("#"):
                    print(f"\n  {action.strip('#').strip()}")
                else:
                    print(f"    {action}")
        else:
            print(f"Generated {len(actions)} actions")
            for i, action in enumerate(actions):
                print(f"  {i+1}. {action}")

    except Exception as e:
        print(f"Plan generation failed: {str(e)}")
        import traceback
        traceback.print_exc()

    plan_time = time.time() - plan_start_time
    plan_tokens = result.get("tokens_used", 0) if 'result' in dir() else 0

    state = _initialize_stage_metrics(state)
    state["evaluation_metrics"]["stage_5_planner"] = {
        "tokens": plan_tokens,
        "time": plan_time
    }

    state["current_stage"] = StageType.COMPLETED
    print(f"Plan time: {plan_time:.2f}s")
    print(f"Plan tokens: {plan_tokens}")
    print(f"{'='*60}\n")

    return state


def _initialize_stage_metrics(state: SystemState) -> SystemState:
    """Initialize stage metrics structure if not exists"""
    if "evaluation_metrics" not in state:
        state["evaluation_metrics"] = {}

    # Initialize 4-stage metrics at root level (not nested)
    if "stage_1_decomposer" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["stage_1_decomposer"] = {"tokens": 0, "time": 0.0, "attempts": 0}

    if "stage_2_allocator" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["stage_2_allocator"] = {"tokens": 0, "time": 0.0}

    if "stage_3_agents" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["stage_3_agents"] = {"temp_tokens": [], "temp_time": [], "tokens":0, "time":0.0}

    if "stage_4_synthesis" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["stage_4_synthesis"] = {"tokens": 0, "time": 0.0}

    if "stage_5_planner" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["stage_5_planner"] = {"tokens": 0, "time": 0.0}

    if "agent_details" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["agent_details"] = {}

    if "task_details" not in state["evaluation_metrics"]:
        state["evaluation_metrics"]["task_details"] = {}

    return state


# Function removed - using simplified rounds only


def metrics_collection_node(state: SystemState) -> SystemState:
    """
    Stage 4 Alternative: Metrics Collection Node (instead of synthesis)

    Collects and finalizes performance metrics for allocator comparison experiments.
    Used when synthesis is not needed (e.g., comparing allocator performance).

    Input: completed_tasks, failed_tasks, evaluation_metrics
    Output: final_summary in evaluation_metrics
    """
    import time
    from heart.core.state import StageType

    print("\n" + "="*60)
    print("METRICS COLLECTION STAGE")
    print("="*60)

    # Calculate final metrics
    completed = len(state.get("completed_tasks", {}))
    failed = len(state.get("failed_tasks", {}))
    total = len(state.get("questions", {}))
    unallocated = len(state.get("unallocated_tasks", []))

    # Initialize stage metrics if needed (in case we came here directly)
    state = _initialize_stage_metrics(state)

    # Preserve synthesis tokens/time if synthesis already ran before this node
    # (synthesize → metrics_collection flow: don't overwrite synthesis results)

    # --- Compute parallel-aware agent stage time from round timestamps ---
    # Each round's `timestamp` is the allocator-end time. Within a round, agents
    # run in parallel, so the round's agent-stage duration is max(agent times).
    # Between consecutive round timestamps, the prior round's agents run
    # (parallel) followed by the next round's allocator. The final entry in
    # rounds_list is the empty exit allocate call, so we iterate over N-1
    # segments to capture every active round's agent execution:
    #   agent_time_k = (timestamp_{k+1} - timestamp_k) - allocator_time_{k+1}
    rounds_list = state["evaluation_metrics"].get("rounds", [])
    agent_time_total = 0.0
    for k in range(len(rounds_list) - 1):
        ts_k = rounds_list[k].get("timestamp")
        ts_next = rounds_list[k + 1].get("timestamp")
        alloc_next = rounds_list[k + 1].get("allocator_time", 0.0)
        if ts_k is not None and ts_next is not None:
            seg = ts_next - ts_k - alloc_next
            if seg > 0:
                agent_time_total += seg
    state["evaluation_metrics"]["stage_3_agents"]["time"] = agent_time_total

    # Calculate total workflow time and tokens using new structure
    stage1 = state["evaluation_metrics"].get("stage_1_decomposer", {})
    stage2 = state["evaluation_metrics"].get("stage_2_allocator", {})
    stage3 = state["evaluation_metrics"].get("stage_3_agents", {})
    stage4 = state["evaluation_metrics"].get("stage_4_synthesis", {})

    # Total tokens across all stages (including synthesis if it ran)
    total_tokens = (
        stage1.get("tokens", 0) +  # Decomposer tokens
        stage2.get("tokens", 0) +  # Allocator tokens (all rounds)
        stage3.get("tokens", 0) +  # Agent tokens (total from all agents)
        stage4.get("tokens", 0)    # Synthesis tokens (if synthesis ran before metrics_collection)
    )

    # Calculate total time (considering parallel execution)
    # Total time = decomposer + sum(each round's time)
    total_time = stage1.get("time", 0.0)  # Decomposer time

    # Add up round times from simplified rounds
    for round_data in state["evaluation_metrics"].get("rounds", []):
        round_time = round_data.get("allocator_time", 0.0)
        total_time += round_time

    # Add final summary
    state["evaluation_metrics"]["final_summary"] = {
        "total_questions": total,
        "completed": completed,
        "failed": failed,
        "unallocated": unallocated,
        "success_rate": completed/total if total > 0 else 0,
        "failure_rate": failed/total if total > 0 else 0,
        "unallocated_rate": unallocated/total if total > 0 else 0,
        "allocation_rounds": len(state["evaluation_metrics"].get("rounds", [])),
        "allocator_type": state.get("allocator_type", "unknown"),
        "total_tokens": total_tokens,
        "total_time": total_time
    }

    # Display summary
    print(f"\nFINAL RESULTS:")
    print(f"  Allocator: {state.get('allocator_type', 'unknown')}")
    print(f"  Questions: {total}")
    print(f"  Completed: {completed} ({completed/total*100:.1f}%)" if total > 0 else f"  Completed: {completed}")
    print(f"  Failed: {failed} ({failed/total*100:.1f}%)" if total > 0 else f"  Failed: {failed}")
    print(f"  Unallocated: {unallocated} ({unallocated/total*100:.1f}%)" if total > 0 else f"  Unallocated: {unallocated}")
    print(f"  Allocation rounds: {len(state['evaluation_metrics'].get('rounds', []))}")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Total time: {total_time:.2f}s")

    # Display stage breakdown
    print(f"\nSTAGE BREAKDOWN:")
    print(f"  Stage 1 (Decomposer):")
    print(f"    Tokens: {stage1.get('tokens', 0):,}")
    print(f"    Time: {stage1.get('time', 0.0):.2f}s")
    print(f"    Attempts: {stage1.get('attempts', 0)}")

    print(f"  Stage 2 (Allocator):")
    print(f"    Tokens: {stage2.get('tokens', 0):,}")
    print(f"    Time: {stage2.get('time', 0.0):.2f}s")

    print(f"  Stage 3 (Agents):")
    print(f"    Tokens: {stage3.get('tokens', 0):,}")
    print(f"    Time: {stage3.get('time', 0.0):.2f}s")

    # Set stage to completed
    state["current_stage"] = StageType.COMPLETED

    print("="*60 + "\n")

    return state