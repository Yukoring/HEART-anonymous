"""
HEART System State

LangGraph TypedDict state definition with custom merge functions for
concurrent node updates. Manages the full pipeline state:
- Questions: decomposed reasoning questions with status tracking
- Allocation: agent assignments, retry history, capacity tracking
- Results: completed/failed tasks, synthesis output, final plan
- Metrics: per-stage token usage and timing (5-stage breakdown)

StateReducer handles task lifecycle: allocation → execution → completion/retry → failure.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated, Set
from enum import Enum


def add_results(old: Dict, new: Dict) -> Dict:
    """Add new results to existing ones (for Dict merging)"""
    result = old.copy() if old else {}
    result.update(new)
    return result

def merge_agent_tasks(old: Dict[str, Set[str]], new: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """Merge agent_tasks from multiple executors
    
    Simply replaces with new value (typically empty set after processing)
    """
    result = old.copy() if old else {}
    for agent, tasks in (new or {}).items():
        result[agent] = tasks
    return result

def merge_allocation_map(old: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    """Merge allocation_map updates from multiple nodes
    
    Special handling:
    - Keys with special value "__DELETE__" will be removed
    - Otherwise, update with new value (including "")
    """
    result = old.copy() if old else {}
    for task_id, agent in (new or {}).items():
        if agent == "__DELETE__":
            # Special marker for deletion
            result.pop(task_id, None)
        else:
            # Update with new value (including "")
            result[task_id] = agent
    return result

def merge_questions(old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, Dict]:
    """Merge questions updates from multiple nodes

    If new contains a '_replace_all' key, completely replace old (used by decompose refinement).
    Otherwise, deep merge for question updates (e.g., updating prompt or question_type).
    """
    if not new:
        return old.copy() if old else {}

    # Full replacement mode: when decompose refinement generates a new question set
    if "_replace_all" in new:
        new = {k: v for k, v in new.items() if k != "_replace_all"}
        return new

    result = old.copy() if old else {}
    for q_id, q_data in new.items():
        if q_id in result:
            # Merge with existing question
            result[q_id] = {**result[q_id], **q_data}
        else:
            # New question
            result[q_id] = q_data
    return result


class StageType(str, Enum):
    """Workflow stages"""
    START = "start"
    DECOMPOSE = "decompose"
    REFINEMENT = "refinement"
    ALLOCATION = "allocation"
    EXECUTION = "execution"
    SYNTHESIS = "synthesis"
    PLAN = "plan"
    COMPLETED = "completed"


class SystemState(TypedDict):
    """
    Simplified Allocator-Centric System State
    
    Design Principles:
    1. Unified tracking based on question IDs
    2. Sets for deduplication and fast lookups
    3. Retry and failure tracking included
    4. Removed agent_availability for super-step structure
    """
    
    # ========== Core Input (immutable) ==========
    instruction: str  # Original robot task instruction
    env_data: Dict[str, Any]  # Environment information
    
    # ========== Stage 1: Decomposition Output ==========
    questions: Annotated[Dict[str, Any], merge_questions]  # {question_id: ReasoningQuestion dict} - All questions (original + follow-up)
    decompose_num: int  # Number of decomposition attempts
    
    # ========== Stage 2-3: Allocation & Execution ==========
    # Allocation tracking
    allocation_map: Annotated[Dict[str, str], merge_allocation_map]  # {question_id: agent_name} - Agent assigned to each question
    allocation_history: Dict[str, List[str]]  # Allocation history {question_id: [agent_names]}
    allocation_prompt_hash: Dict[str, str]  # Hash of prompts used for allocation
    # last_agent_for_task: Dict[str, str]  # Last agent assigned to each task

    # Task tracking (simplified with Sets/Dicts)
    agent_tasks: Annotated[Dict[str, Set[str]], merge_agent_tasks]  # {agent: {question_ids}} - Questions assigned to each agent
    pending_tasks: Dict[str, List[str]]  # {agent: [question_ids]} - Queued questions (order preserved)
    unallocated_tasks: List[str]  # [question_ids] - Tasks not allocated due to token limits (for tracking only)

    ## Execution Node - Annotated for parallel updates
    completed_tasks: Annotated[Dict[str, Dict[str, Any]], add_results]  # {question_id: {answer, reasoning, ...}}
    failed_tasks: Dict[str, Dict[str, Any]]  # {question_id: {reason, partial_answer, ...}} - Managed only by allocate_node
    
    # Agent Configuration
    token_budget: int  # Per-round token budget for allocation (default: 20000)
    agent_capacities: Dict[str, int]  # {agent_name: max_concurrent} - Max concurrent tasks per agent
    agent_token_estimates: Dict[str, int]  # {agent_name: estimated_tokens} - Estimated tokens per agent
    
    # ========== Stage 4: Synthesis Output ==========
    heart_constraints_text: str  # Formatted HEART Q&A constraints for planner

    # ========== Stage 5: Plan Output ==========
    planner_type: Optional[str]  # Planner type ("llm_cot", "delta", or None for reasoning only)
    planner_config: Dict[str, Any]  # Planner configuration (domain, scene, task_robots)
    final_plan: str  # Final robot execution plan
    plan_steps: List[Dict[str, Any]]  # Execution steps
    plan_orig: List[str]  # DELTA undecomposed plan (for validation)
    
    # ========== Control Flow ==========
    current_stage: StageType  # Current workflow stage
    workflow_id: str  # Workflow identifier
    error_logs: List[Dict[str, Any]]  # Error logs

    # ========== Evaluation Metrics (for experiments only) ==========
    evaluation_metrics: Dict[str, Any]  # Detailed metrics for evaluation
    allocator_type: Optional[str]  # Type of allocator used (heart/llm/type_based)


# ========== State Reducer for Allocator-Centric Management ==========

class StateReducer:
    """
    Extracts and merges minimal data required by each node.
    """
    
    @staticmethod
    def for_decomposer(state: SystemState) -> Dict[str, Any]:
        """Extract data needed by decomposer"""
        return {
            "instruction": state.get("instruction"),
            "env_data": state.get("env_data"),
            "decompose_num": state.get("decompose_num"),
            "questions": state.get("questions", {})  # Dictionary format
        }
    
    @staticmethod
    def merge_decomposition(state: SystemState, decomposition: Any, num: int, 
                          agent_token_estimates: Dict[str, int] = {}) -> SystemState:
        """Merge decomposition results into state (converts List to Dict)
        
        Args:
            state: System state
            decomposition: QuestionDecomposition object
            num: Decomposition attempt number
            agent_token_estimates: Optional token estimates from agents
        """
        # Convert QuestionDecomposition's List[ReasoningQuestion] to Dict
        questions_dict = {}
        for q in decomposition.questions:
            q_dict = q.dict()
            question_id = q_dict.get("question_id", f"Q{len(questions_dict)+1}")
            
            # Initialize token tracking fields for all questions
            q_dict["total_tokens"] = 0
            q_dict["total_time"] = 0.0
            
            questions_dict[question_id] = q_dict
        
        # Use _replace_all flag so LangGraph reducer replaces instead of merging
        # This ensures refinement drops questions from previous attempt
        questions_dict["_replace_all"] = True
        state["questions"] = questions_dict
        state["decompose_num"] = num
        state["current_stage"] = StageType.DECOMPOSE

        # Reset allocation_map to match new questions exactly
        # (drops leftover entries from previous decompose attempts)
        state["allocation_map"] = {q_id: "" for q_id in questions_dict if q_id != "_replace_all"}
        
        # Add agent token estimates if provided (only on first decomposition)
        if agent_token_estimates:
            state["agent_token_estimates"] = agent_token_estimates
        
        return state
    
    @staticmethod
    def merge_allocation(state: SystemState, allocation_result: Dict[str, str]) -> SystemState:
        """Merge allocation results into state and update unallocated_tasks
        
        Handles both formats:
        - LLM allocator: {"task_Q1": "agent_name", ...}
        - HEART allocator: {"Q1": "agent_name", ...}
        """
        
        # Track which questions were allocated
        allocated_ids = set()
        
        for task_key, assigned_agent in allocation_result.items():
            # Handle both formats: "task_Q1" (LLM) and "Q1" (HEART)
            if task_key.startswith("task_"):
                q_id = task_key.replace("task_", "")
            else:
                q_id = task_key
            
            allocated_ids.add(q_id)
            
            # Check if this question exists and is unallocated
            if q_id not in state.get("allocation_map", {}):
                continue
            if state["allocation_map"][q_id] != "":  # Already allocated
                continue
            
            # 1. Update allocation_map
            state["allocation_map"][q_id] = assigned_agent
            
            # 2. Add to pending_tasks (queue) - allocation_history updated later
            # Skip if assigned_agent is empty (unallocated)
            if assigned_agent and assigned_agent != "":
                if "pending_tasks" not in state:
                    state["pending_tasks"] = {}
                if assigned_agent not in state["pending_tasks"]:
                    state["pending_tasks"][assigned_agent] = []
                # Only append if not already in pending_tasks
                if q_id not in state["pending_tasks"][assigned_agent]:
                    state["pending_tasks"][assigned_agent].append(q_id)
        
        # 3. Update unallocated_tasks - questions that couldn't be allocated
        if "unallocated_tasks" not in state:
            state["unallocated_tasks"] = []
        
        # Find questions that were attempted but not allocated
        for q_id, agent in state.get("allocation_map", {}).items():
            if agent == "" and q_id not in allocated_ids:
                # This question remains unallocated
                if q_id not in state["unallocated_tasks"]:
                    state["unallocated_tasks"].append(q_id)
        
        # Remove questions that got allocated from unallocated list
        state["unallocated_tasks"] = [q_id for q_id in state["unallocated_tasks"] 
                                      if q_id not in allocated_ids]

        return state
    
    @staticmethod
    def distribute_pending_to_agents(state: SystemState) -> SystemState:
        """Move tasks from pending_tasks to agent_tasks based on capacity"""
        for agent_name in state.get("pending_tasks", {}).keys():
            capacity = state.get("agent_capacities", {}).get(agent_name, 1)
            pending = state["pending_tasks"][agent_name].copy()  # Copy to avoid modification during iteration
            # Initialize agent_tasks if needed
            if "agent_tasks" not in state:
                state["agent_tasks"] = {}
            if agent_name not in state["agent_tasks"]:
                state["agent_tasks"][agent_name] = set()
            
            # Current processing count
            current_processing = len(state["agent_tasks"][agent_name])
            
            # Calculate how many more tasks can be processed
            available_slots = capacity - current_processing
            
            if available_slots > 0:
                # Move tasks to agent_tasks
                tasks_to_add = []
                tasks_to_remove = []
                
                for task_id in pending[:available_slots]:
                    # Check if this agent has tried this task too many times consecutively
                    history = state.get("allocation_history", {}).get(task_id, [])
                    if len(history) >= 4:
                        # Check if last 4 attempts were by the same agent (5th consecutive = fail)
                        if history[-4:] == [agent_name] * 4:
                            # This would be the 5th consecutive attempt - move to failed
                            if "failed_tasks" not in state:
                                state["failed_tasks"] = {}
                            
                            # Get the original question from state questions
                            question = state.get("questions", {}).get(task_id, {})
                            
                            state["failed_tasks"][task_id] = {
                                "answer": "",
                                "reasoning": f"Failed: Same agent ({agent_name}) attempted 5 times consecutively",
                                "retry_count": len(history) + 1,
                                "original_prompt": question.get("prompt", "")
                            }
                            
                            # Remove from allocation_map if exists
                            if task_id in state.get("allocation_map", {}):
                                del state["allocation_map"][task_id]
                            
                            tasks_to_remove.append(task_id)
                            continue
                    
                    # Normal processing
                    tasks_to_add.append(task_id)
                    state["agent_tasks"][agent_name].add(task_id)
                    
                    # Update allocation_history when actually processing
                    if "allocation_history" not in state:
                        state["allocation_history"] = {}
                    if task_id not in state["allocation_history"]:
                        state["allocation_history"][task_id] = []
                    state["allocation_history"][task_id].append(agent_name)
                
                # Remove processed and failed tasks from pending
                remaining_pending = []
                for i, task_id in enumerate(pending):
                    if i >= available_slots:
                        remaining_pending.append(task_id)
                    elif task_id not in tasks_to_add and task_id not in tasks_to_remove:
                        remaining_pending.append(task_id)
                
                state["pending_tasks"][agent_name] = remaining_pending
                
        state["current_stage"] = StageType.EXECUTION
        
        return state
    
    
    @staticmethod
    def remove_completed_tasks(state: SystemState) -> SystemState:
        """Remove completed tasks from allocation_map
        
        Args:
            state: System state
            
        Returns:
            Updated state with completed tasks removed from allocation_map
        """
        for task_id in state.get("completed_tasks", {}).keys():
            if task_id in state.get("allocation_map", {}):
                state["allocation_map"].pop(task_id)
        
        return state
    
    @staticmethod
    def remove_failed_tasks(state: SystemState) -> SystemState:
        """Remove homogeneous failed tasks from allocation_map
        
        For homogeneous workflow, tasks in failed_tasks should be removed
        from allocation_map immediately (no retry mechanism).
        
        Args:
            state: System state
            
        Returns:
            Updated state with failed tasks removed from allocation_map
        """
        for task_id in state.get("failed_tasks", {}).keys():
            if task_id in state.get("allocation_map", {}):
                state["allocation_map"].pop(task_id)
        
        return state
    
    @staticmethod
    def move_tasks_to_failed(state: SystemState, max_retries: int = 4) -> SystemState:
        """Move tasks that exceeded max retries to failed_tasks
        
        Args:
            state: System state
            max_retries: Maximum retry attempts
            
        Returns:
            Updated state with failed tasks moved
        """
        allocation_map = state.get("allocation_map", {})
        allocation_history = state.get("allocation_history", {})
        questions = state.get("questions", {})
        
        tasks_to_fail = []
        
        for q_id, agent in allocation_map.items():
            if agent == "":  # Unallocated (needs retry)
                retry_count = len(allocation_history.get(q_id, []))
                
                if retry_count >= max_retries:
                    tasks_to_fail.append(q_id)
                    
                    # Get the question for partial answer
                    question = questions.get(q_id, {})
                    if "failed_tasks" not in state:
                        state["failed_tasks"] = {}
                    
                    state["failed_tasks"][q_id] = {
                        "answer": "",  # No final answer
                        "reasoning": f"Failed after {retry_count} attempts",
                        "retry_count": retry_count,
                        "original_prompt": question.get("prompt", "")
                    }
        
        # Remove failed tasks from allocation_map
        for task_id in tasks_to_fail:
            state["allocation_map"].pop(task_id, None)
        
        return state
    
    @staticmethod
    def set_stage(state: SystemState, stage: StageType) -> None:
        """Set the current workflow stage
        
        Args:
            state: System state
            stage: Stage to set
        """
        state["current_stage"] = stage
    
    @staticmethod
    def process_execution_results(
        results: List[Dict[str, Any]], 
        agent_type: str,
        current_questions: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Process execution results and create state update
        
        Args:
            results: List of execution results from agent
            agent_type: Type of agent that processed tasks
            current_questions: Current questions from state
            
        Returns:
            Partial state update dictionary
        """
        from heart.core.schema import AgentOutputStatus
        
        # Initialize update structure
        update = {
            "completed_tasks": {},
            "allocation_map": {},
            "questions": {},
            "agent_tasks": {agent_type: set()}  # Clear processed tasks
        }
        
        for result in results:
            task_id = result.get("task_id")
            if not task_id:
                continue
            
            # Get tokens and time from this execution
            tokens_used = result.get("tokens_used", 0)
            execution_time = result.get("execution_time", 0)
            
            # Update question's cumulative token tracking
            if task_id in current_questions:
                original_question = current_questions.get(task_id, {})
                updated_question = original_question.copy()
                updated_question["total_tokens"] = original_question.get("total_tokens", 0) + tokens_used
                updated_question["total_time"] = original_question.get("total_time", 0.0) + execution_time
                update["questions"][task_id] = updated_question
            
            # Check if API call was successful
            if not result.get("success", False):
                # API call failed - mark for retry
                update["allocation_map"][task_id] = ""  # Reset to unallocated
                continue
            
            status = result.get("status")
            
            # Handle SUCCESS (both heterogeneous and homogeneous)
            if status in [AgentOutputStatus.SUCCESS, "SUCCESS", "success"]:
                update["completed_tasks"][task_id] = {
                    "answer": result.get("answer", ""),
                    "reasoning": result.get("reasoning", "")
                    # Removed tokens_used and execution_time from here
                }
            
            # Handle PARTIAL or OUT_OF_SCOPE (heterogeneous only)
            elif status in [AgentOutputStatus.PARTIAL, AgentOutputStatus.OUT_OF_SCOPE, "PARTIAL", "OUT_OF_SCOPE"]:
                # Always handle PARTIAL/OUT_OF_SCOPE regardless of follow_up_question
                # Use the already updated question (with accumulated tokens)
                # or create new one if not already updated
                
                if task_id in update["questions"]:
                    updated_question = update["questions"][task_id]
                else:
                    original_question = current_questions.get(task_id, {})
                    updated_question = original_question.copy()
                
                # Build context
                status_context = f"{agent_type} ({status})"
                
                # Append previous attempt and follow-up
                follow_up_text = result.get('follow_up_question', 'No specific follow-up provided')
                updated_question["prompt"] = (
                    original_question.get("prompt", "") + 
                    f"\n\nPrevious attempt by {status_context}: {result.get('answer', '')}\n"
                    f"Additional needed: {follow_up_text}"
                )
                
                # Preserve original task type on first follow-up
                if "original_task_type" not in updated_question:
                    updated_question["original_task_type"] = original_question.get("question_type")
                
                # Update current question type if provided
                if result.get("follow_up_task_type"):
                    updated_question["question_type"] = result["follow_up_task_type"]
                
                # Track failed agents for OUT_OF_SCOPE
                if status in [AgentOutputStatus.OUT_OF_SCOPE, "OUT_OF_SCOPE"]:
                    if "failed_agents" not in updated_question:
                        updated_question["failed_agents"] = []
                    updated_question["failed_agents"].append(agent_type)
                
                update["questions"][task_id] = updated_question
                
                # Mark for reallocation
                update["allocation_map"][task_id] = ""

        return update
    
    @staticmethod
    def for_executor(state: SystemState, agent_type: str) -> Dict[str, Any]:
        """Extract data needed by executor - get tasks from agent_tasks
        
        Args:
            state: System state
            agent_type: Agent type (e.g., "capability_reasoner")
            
        Returns:
            Data needed for executor
        """
        # Get task IDs from agent_tasks
        task_ids = state.get("agent_tasks", {}).get(agent_type, set())
        
        # Get actual question objects for these IDs
        all_questions = state.get("questions", {})  # Dict format
        tasks_to_process = []
        for q_id in task_ids:
            if q_id in all_questions:
                tasks_to_process.append(all_questions[q_id])
        
        return {
            "instruction": state.get("instruction", ""),
            "tasks": tasks_to_process,
            "task_ids": list(task_ids),  # Pass IDs separately for convenience
            "env_data": state.get("env_data", {}),
            "agent_type": agent_type
        }

# ========== Utility Functions ==========

def initialize_state(
    instruction: str,
    env_data: Dict[str, Any],
    agents: List[str],
    allocator_type: str = "heart",
    planner_type: Optional[str] = None,
    planner_config: Optional[Dict[str, Any]] = None,
    token_budget: int = 20000,
) -> SystemState:
    """
    Create initial SystemState

    Args:
        instruction: Task instruction
        env_data: Environment data
        agents: List of agent IDs to use (e.g., ["capability_reasoner", ...])
        planner_type: Planner to use ("llm_cot", "delta", or None for reasoning only)
        planner_config: Planner-specific config (e.g., domain/scene for DELTA)

    Usage:
        # HEART + LLM-CoT
        state = initialize_state(
            instruction="Move the chair from R4 to R2",
            env_data={"robots": [...], "rooms": {...}},
            agents=["capability_reasoner", "environmental_reasoner", "path_reasoner",
                    "feasibility_reasoner", "constraint_reasoner"],
            planner_type="llm_cot",
        )

        # HEART reasoning only (no planner)
        state = initialize_state(
            instruction="...",
            env_data={...},
            agents=["capability_reasoner", ...],
            planner_type=None,
        )
    """
    import uuid

    agent_capacities = {agent: 1 for agent in agents}

    return SystemState(
        # Core Input
        instruction=instruction,
        env_data=env_data,

        # Stage 1: Decompose
        questions={},
        decompose_num=0,

        # Stage 2-3: Allocation & Execution
        allocation_map={},
        allocation_history={},
        allocation_prompt_hash={},

        # Task tracking
        agent_tasks={},
        pending_tasks={},
        unallocated_tasks=[],
        completed_tasks={},
        failed_tasks={},

        # Agent Configuration
        token_budget=token_budget,
        agent_capacities=agent_capacities,
        agent_token_estimates={},

        # Stage 4: Synthesis
        heart_constraints_text="",

        # Stage 5: Plan
        planner_type=planner_type,
        planner_config=planner_config or {},
        final_plan="",
        plan_steps=[],
        plan_orig=[],

        # Control Flow
        current_stage=StageType.START,
        workflow_id=str(uuid.uuid4()),
        error_logs=[],

        # Evaluation Metrics
        evaluation_metrics={},
        allocator_type=allocator_type
    )