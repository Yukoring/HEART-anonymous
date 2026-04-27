"""
Common utilities for HEART experiments.

Shared functions: env data loading, single trial execution, metrics extraction, result saving.
"""

import os
import sys
import json
import csv
import copy
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


def check_api_key():
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)


def load_env_data(scene_name: str, task) -> Dict[str, Any]:
    """Load scene graph + parse URDF → env_data."""
    from heart.utils.urdf_parser import parse_urdf_to_specs
    from heart.configs.tasks import get_scene_graph_path, get_scene_robots, get_robot_urdf_path

    scene_path = PROJECT_ROOT / get_scene_graph_path(scene_name)
    with open(scene_path, "r") as f:
        scene_graph = json.load(f)

    scene_robots = get_scene_robots(scene_name, task=task)
    robots_dict = {}
    for robot_name, robot_config in scene_robots.items():
        urdf_path = PROJECT_ROOT / get_robot_urdf_path(robot_config["urdf"])
        position = task.position.get(robot_name, [0.0, 0.0, 0.0]) if task.position else [0.0, 0.0, 0.0]
        robots_dict[robot_name] = {
            "urdf": parse_urdf_to_specs(str(urdf_path)),
            "position": position,
            "location": [], "state": [], "capability": [],
        }

    return {"scene_graph": scene_graph, "robots": robots_dict}


def reset_global_instances():
    """Reset global node instances for clean state between runs."""
    import heart.workflows.nodes as nodes
    nodes._decomposer_instance = None
    nodes._agent_instances = {}
    nodes._allocator_instance = None
    if hasattr(nodes, '_allocator_instance_llm'):
        nodes._allocator_instance_llm = None
    nodes._executor_instances = {}
    nodes._synthesis_agent_instance = None


def run_heart_trial(
    config: Dict,
    scene_name: str,
    task,
    iteration: int,
    budget: int = 20000,
) -> Dict[str, Any]:
    """Run a single HEART experiment trial."""
    from heart.core.state import initialize_state
    from heart.workflows.workflow import create_workflow

    reset_global_instances()

    env_data = load_env_data(scene_name, task)

    # Auto-generate planner_config from scene/task info
    # For DELTA: pass task.robots so scene graph uses the correct robot configs
    from heart.configs.tasks import get_scene_robots
    scene_robots = get_scene_robots(scene_name, task=task)
    task_robots = {name: cfg["urdf"] for name, cfg in scene_robots.items()}
    # Map 3D start positions to nearest room if task.position is set (optional — DELTA uses room names)
    planner_config = {
        "domain": task.domain,                          # PDDL domain name (e.g., "serve_food")
        "scene": scene_name.split("_")[0].lower(),      # DELTA scene name (e.g., "benevolence")
        "task_robots": task_robots,                     # {robot_name: urdf_key}
    }

    state = initialize_state(
        instruction=task.goal,
        env_data=env_data,
        agents=config["agents"],
        allocator_type=config["allocator_type"],
        planner_type=config.get("planner_type"),
        planner_config=planner_config,
        token_budget=budget,
    )

    workflow = create_workflow(
        agents=config["agents"],
        allocator_type=config["allocator_type"],
        planner_type=config.get("planner_type"),
    )

    start_time = time.time()
    result = workflow.invoke(state, config={"recursion_limit": 100})
    total_time = time.time() - start_time

    result["_total_time"] = total_time
    result["_iteration"] = iteration
    return result


def run_baseline_trial(scene_name: str, task, iteration: int, planner_type: str = "llm_cot") -> Dict[str, Any]:
    """Run a single baseline (planner alone) trial."""
    from heart.configs.tasks import get_scene_robots
    env_data = load_env_data(scene_name, task)
    scene_robots = get_scene_robots(scene_name, task=task)
    task_robots = {name: cfg["urdf"] for name, cfg in scene_robots.items()}

    planner_kwargs = {
        "instruction": task.goal,
        "env_data": env_data,
        "domain": task.domain,
        "scene": scene_name.split("_")[0].lower(),
        "task_robots": task_robots,
    }

    if planner_type == "llm_cot":
        from planners.llm_cot import LLMCoTPlanner
        planner = LLMCoTPlanner()
    elif planner_type == "delta":
        from planners.delta.delta_planner import DeltaPlanner
        planner = DeltaPlanner()
    else:
        raise ValueError(f"Unknown planner type: {planner_type}")

    result = planner.plan(**planner_kwargs)
    result["_iteration"] = iteration
    return result


def extract_metrics(result: Dict, config: Dict, scene_name: str, task, iteration: int) -> Dict:
    """Extract key metrics from experiment result."""
    is_baseline = config.get("_is_baseline", False) or config.get("agents") is None

    # Determine num_robots from task config
    from heart.configs.tasks import get_scene_robots
    scene_robots = get_scene_robots(scene_name, task=task)
    num_robots = len(scene_robots)

    if is_baseline:
        return {
            "experiment": config.get("description", "baseline"),
            "timestamp": datetime.now().isoformat(),
            "scene": scene_name,
            "task_id": task.id,
            "instruction": task.goal,
            "iteration": iteration,
            "num_robots": num_robots,
            "total_questions": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 1.0,
            "total_retries": 0,
            "total_rounds": 0,
            "active_rounds": 0,
            "partial_count": 0,
            "out_of_scope_count": 0,
            "misroute_count": 0,
            "avg_round_throughput": 0,
            "workflow_total_tokens": result.get("tokens_used", 0),
            "decomposer_tokens": 0,
            "decomposer_attempts": 0,
            "allocator_tokens": 0,
            "agent_tokens": 0,
            "synthesis_tokens": 0,
            "planner_tokens": result.get("tokens_used", 0),
            "token_per_question": 0,
            "time_per_question": 0,
            "execution_time": result.get("execution_time", 0),
            "decomposer_time": 0,
            "allocator_time": 0,
            "agent_time": 0,
            "synthesis_time": 0,
            "planner_time": result.get("execution_time", 0),
            "plan_steps_count": len(result.get("plan", [])),
            "plan_content": json.dumps(result.get("plan", [])),
            "agent_metrics": "{}",
            "task_metrics": "{}",
            "round_metrics": "[]",
            "error_occurred": False,
            "error_message": "",
        }

    # HEART experiment
    metrics = result.get("evaluation_metrics", {})
    plan_steps = result.get("plan_steps", [])
    questions = result.get("questions", {})
    completed = result.get("completed_tasks", {})
    failed = result.get("failed_tasks", {})
    rounds = metrics.get("rounds", [])
    allocation_history = result.get("allocation_history", {})
    task_details = metrics.get("task_details", {})

    active_rounds = sum(1 for r in rounds if r.get("allocated_tasks", 0) > 0)
    num_questions = len(questions) or 1
    total_agent_tokens = metrics.get("stage_3_agents", {}).get("tokens", 0)
    total_agent_time = metrics.get("stage_3_agents", {}).get("time", 0.0)

    # Retries: total agent changes across all questions
    total_retries = 0
    for q_id, history in allocation_history.items():
        if len(history) > 1:
            total_retries += len(history) - 1

    # Misroute count: questions where agent changed (different agent in history)
    misroute_count = 0
    for q_id, history in allocation_history.items():
        if len(set(history)) > 1:
            misroute_count += 1

    # PARTIAL / OUT_OF_SCOPE counts from task_details
    partial_count = 0
    out_of_scope_count = 0
    for q_id, td in task_details.items():
        status = str(td.get("status", ""))
        if "PARTIAL" in status:
            partial_count += 1
        elif "OUT_OF_SCOPE" in status:
            out_of_scope_count += 1

    # Average round throughput
    total_allocated = sum(r.get("allocated_tasks", 0) for r in rounds)
    avg_round_throughput = total_allocated / max(1, active_rounds)

    return {
        "experiment": config.get("description", ""),
        "timestamp": datetime.now().isoformat(),
        "scene": scene_name,
        "task_id": task.id,
        "instruction": task.goal,
        "iteration": iteration,
        "num_robots": num_robots,
        # Decomposition
        "total_questions": len(questions),
        # Execution
        "completed_tasks": len(completed),
        "failed_tasks": len(failed),
        "success_rate": len(completed) / max(1, len(questions)),
        "total_retries": total_retries,
        "total_rounds": len(rounds),
        "active_rounds": active_rounds,
        "partial_count": partial_count,
        "out_of_scope_count": out_of_scope_count,
        "misroute_count": misroute_count,
        "avg_round_throughput": round(avg_round_throughput, 2),
        # Tokens breakdown (5 stages)
        "workflow_total_tokens": (
            metrics.get("stage_1_decomposer", {}).get("tokens", 0) +
            metrics.get("stage_2_allocator", {}).get("tokens", 0) +
            total_agent_tokens +
            metrics.get("stage_4_synthesis", {}).get("tokens", 0) +
            metrics.get("stage_5_planner", {}).get("tokens", 0)
        ),
        "decomposer_tokens": metrics.get("stage_1_decomposer", {}).get("tokens", 0),
        "decomposer_attempts": metrics.get("stage_1_decomposer", {}).get("attempts", 0),
        "allocator_tokens": metrics.get("stage_2_allocator", {}).get("tokens", 0),
        "agent_tokens": total_agent_tokens,
        "synthesis_tokens": metrics.get("stage_4_synthesis", {}).get("tokens", 0),
        "planner_tokens": metrics.get("stage_5_planner", {}).get("tokens", 0),
        # Per-question averages
        "token_per_question": round(total_agent_tokens / num_questions, 2),
        "time_per_question": round(total_agent_time / num_questions, 2),
        # Time breakdown (5 stages)
        "execution_time": result.get("_total_time", 0),
        "decomposer_time": metrics.get("stage_1_decomposer", {}).get("time", 0.0),
        "allocator_time": metrics.get("stage_2_allocator", {}).get("time", 0.0),
        "agent_time": metrics.get("stage_3_agents", {}).get("time", 0.0),  # parallel-aware wall-clock
        "agent_cumulative_llm_time": metrics.get("stage_3_agents", {}).get("cumulative_llm_time", 0.0),  # over-counted, kept for diagnostics
        "synthesis_time": metrics.get("stage_4_synthesis", {}).get("time", 0.0),
        "planner_time": metrics.get("stage_5_planner", {}).get("time", 0.0),
        # Plan
        "plan_steps_count": len(plan_steps),
        "plan_content": json.dumps(plan_steps),
        # Detailed metrics (JSON strings for analysis)
        "agent_metrics": json.dumps(metrics.get("agent_details", {})),
        "task_metrics": json.dumps(task_details),
        "round_metrics": json.dumps(rounds),
        # Error tracking
        "error_occurred": False,
        "error_message": "",
    }


def validate_plan_result(
    result: Dict,
    task,
    scene_name: str,
    planner_type: Optional[str] = None,
    output_dir: Optional[Path] = None,
    iteration: int = 0,
    condition: str = "",
) -> Dict[str, Any]:
    """
    Validate plan from experiment result using VAL.

    Runs OUTSIDE the planning pipeline — validation cost is not counted in metrics.
    For DELTA: validates both decomposed and undecomposed plans (already PDDL).
    For LLM-CoT: convert to PDDL using LLM → validate.

    Saves plan files to output_dir/plans/ if output_dir is provided.

    Args:
        result: Experiment result dict (from run_heart_trial or run_baseline_trial)
        task: Task object with .id
        scene_name: Scene name (e.g., "Benevolence_1")
        planner_type: "llm_cot" or "delta" (auto-detected if not specified)
        output_dir: Directory to save plan files (optional)
        iteration: Iteration number for file naming
        condition: Condition name for file naming (e.g., "5_agents", "heart_llm_cot")

    Returns:
        {
            "valid": bool,
            "valid_orig": bool,
            "info": str,
            "pddl_plan": List[str],
            "conversion_time": float,
        }
    """
    from heart.evaluation.plan_validator import validate_plan

    # Auto-detect planner type
    if planner_type is None:
        planner_type = result.get("planner_type", "llm_cot")

    scene = scene_name.split("_")[0].lower()
    cond_part = f"_{condition}" if condition else ""
    plan_prefix = f"{task.id}_{scene}_iter{iteration}{cond_part}"

    # Get plan steps from result
    plan_steps = result.get("plan_steps", []) or result.get("plan", [])
    if not plan_steps:
        return {
            "valid": False, "valid_orig": False,
            "info": "No plan generated", "pddl_plan": [], "conversion_time": 0.0,
        }

    # Save plan files if output_dir provided
    if output_dir:
        plans_dir = Path(output_dir) / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        # Save original plan (LLM-CoT format or DELTA PDDL)
        orig_suffix = f"_{planner_type}.plan"
        with open(plans_dir / f"{plan_prefix}{orig_suffix}", "w") as f:
            f.write("\n".join(plan_steps) + "\n")

        # Save DELTA undecomposed plan if available
        if planner_type == "delta" and result.get("plan_orig"):
            with open(plans_dir / f"{plan_prefix}_delta_orig.plan", "w") as f:
                f.write("\n".join(result["plan_orig"]) + "\n")

    # Validate primary plan
    val_result = validate_plan(
        plan_steps=plan_steps,
        task_id=task.id,
        scene_name=scene_name,
        planner_type=planner_type,
    )

    # Save converted PDDL plan (LLM-CoT only — DELTA is already PDDL)
    if output_dir and planner_type != "delta" and val_result.get("pddl_plan"):
        plans_dir = Path(output_dir) / "plans"
        with open(plans_dir / f"{plan_prefix}_{planner_type}_pddl.plan", "w") as f:
            f.write("\n".join(val_result["pddl_plan"]) + "\n")

    # For DELTA: also validate undecomposed plan
    val_orig = False
    if planner_type == "delta" and result.get("plan_orig"):
        orig_result = validate_plan(
            plan_steps=result["plan_orig"],
            task_id=task.id,
            scene_name=scene_name,
            planner_type="delta",
        )
        val_orig = orig_result["valid"]

    val_result["valid_orig"] = val_orig
    return val_result


def save_detail(result: Dict, metrics: Dict, output_dir: Path):
    """Save a single iteration's detail JSON immediately (crash-safe)."""
    detail_dir = Path(output_dir) / "details"
    detail_dir.mkdir(parents=True, exist_ok=True)

    name_parts = [
        metrics.get("condition", metrics.get("experiment", "")),
        metrics.get("scene", ""),
        metrics.get("task_id", ""),
        f"iter{metrics.get('iteration', 0)}",
        metrics.get("budget_label", ""),
    ]
    filename = "_".join(str(p) for p in name_parts if p) + ".json"

    detail = {
        "questions": result.get("questions", {}),
        "completed_tasks": result.get("completed_tasks", {}),
        "failed_tasks": result.get("failed_tasks", {}),
        "heart_constraints_text": result.get("heart_constraints_text", ""),
        "plan_steps": result.get("plan_steps", []),
        "plan_orig": result.get("plan_orig", []),
        "allocation_history": result.get("allocation_history", {}),
        "evaluation_metrics": result.get("evaluation_metrics", {}),
    }
    with open(detail_dir / filename, "w") as f:
        json.dump(detail, f, indent=2, default=str)


def save_results(all_metrics: List[Dict], all_states: List[Dict], output_dir: Path):
    """Save final experiment results — CSV rewrite + any remaining details."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if not all_metrics:
        return

    # CSV summary (full rewrite with union header)
    csv_path = output_dir / "metrics.csv"
    fieldnames = []
    seen = set()
    for m in all_metrics:
        for k in m.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_metrics)
    print(f"Results saved to {csv_path}")

    # Save any details not yet saved (backward compat)
    for i, state in enumerate(all_states):
        if i < len(all_metrics):
            save_detail(state, all_metrics[i], output_dir)

    detail_dir = output_dir / "details"
    n_files = len(list(detail_dir.glob("*.json"))) if detail_dir.exists() else 0
    print(f"Detail JSON files in {detail_dir}/ ({n_files} files)")


def append_metric(metric: Dict, output_dir: Path):
    """
    Append a single metric row to metrics.csv. Creates the file with header on first call.
    Used for incremental saves so crashes don't lose earlier results.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "metrics.csv"
    file_exists = csv_path.exists()

    if not file_exists:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(metric.keys()))
            writer.writeheader()
            writer.writerow(metric)
        return

    # Read existing header; if new keys appear, rewrite with union header
    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        try:
            existing_header = next(reader)
        except StopIteration:
            existing_header = []

    new_keys = [k for k in metric.keys() if k not in existing_header]
    if new_keys:
        # Rewrite file with union header
        with open(csv_path, "r", newline="") as f:
            rows = list(csv.DictReader(f))
        union_header = existing_header + new_keys
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=union_header)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            writer.writerow(metric)
    else:
        with open(csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=existing_header)
            writer.writerow({k: metric.get(k, "") for k in existing_header})



def make_output_dir(experiment_name: str, scene_name: str) -> Path:
    """Create timestamped output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return PROJECT_ROOT / "results" / f"{experiment_name}_{scene_name}_{timestamp}"


def print_summary(all_metrics: List[Dict]):
    """Print overall experiment summary."""
    if not all_metrics:
        return

    n = len(all_metrics)
    print(f"\n{'='*60}")
    print(f"SUMMARY: {n} runs completed")

    avg_questions = sum(m["total_questions"] for m in all_metrics) / n
    avg_completed = sum(m["completed_tasks"] for m in all_metrics) / n
    avg_sr = sum(m["success_rate"] for m in all_metrics) / n
    avg_rounds = sum(m.get("active_rounds", 0) for m in all_metrics) / n
    avg_retries = sum(m.get("total_retries", 0) for m in all_metrics) / n
    avg_tokens = sum(m.get("workflow_total_tokens", m.get("total_tokens", 0)) for m in all_metrics) / n
    avg_agent_tokens = sum(m.get("agent_tokens", 0) for m in all_metrics) / n
    avg_time = sum(m["execution_time"] for m in all_metrics) / n
    avg_steps = sum(m["plan_steps_count"] for m in all_metrics) / n

    print(f"Avg questions: {avg_questions:.1f}")
    print(f"Avg completed: {avg_completed:.1f} (SR: {avg_sr:.1%})")
    print(f"Avg rounds: {avg_rounds:.1f}, retries: {avg_retries:.1f}")
    print(f"Avg tokens: {avg_tokens:.0f} (agent: {avg_agent_tokens:.0f})")
    print(f"Avg time: {avg_time:.1f}s")
    print(f"Avg plan steps: {avg_steps:.1f}")
    print(f"{'='*60}")


ALL_SCENES = ["Benevolence_1", "Beechwood_0", "Merom_1"]


def get_scenes_and_tasks(scenes: List[str], task_indices: Optional[List[int]] = None):
    """
    Get scene-task pairs for experiment loop.

    Args:
        scenes: List of scene names
        task_indices: List of task indices, or None for all tasks
    """
    from heart.configs.tasks import get_tasks_for_scene

    scene_tasks = []
    for scene_name in scenes:
        tasks = get_tasks_for_scene(scene_name)
        indices = task_indices if task_indices is not None else list(range(len(tasks)))
        for i in indices:
            if i < len(tasks):
                scene_tasks.append((scene_name, tasks[i], i))
            else:
                print(f"Warning: task index {i} out of range for {scene_name} ({len(tasks)} tasks)")
    return scene_tasks


def parse_tasks_arg(tasks_str: List[str]) -> Optional[List[int]]:
    """
    Parse --tasks argument.
    Returns None for 'all', or list of ints.

    Examples:
        ["all"] → None
        ["0", "1", "3"] → [0, 1, 3]
    """
    if not tasks_str or tasks_str == ["all"]:
        return None
    return [int(t) for t in tasks_str]


# ==================== Fixed Decomposition Utilities ====================

def decompose_once(instruction: str, env_data: Dict[str, Any], agents: List[str],
                    extended: bool = False) -> Dict[str, Any]:
    """
    Decompose once and return reusable question set.

    Args:
        instruction: Task instruction
        env_data: Environment data
        agents: Agent IDs for token estimation
        extended: If True, use extended prompt (15-30 questions) for allocator ablation

    Returns dict with:
        questions_dict: {q_id: question_dict}
        agent_token_estimates: {agent_id: estimated_tokens}
        decomposer_tokens: int
        decomposer_time: float
    """
    from heart.orchestrator.task_decomposer import TaskDecomposer
    from heart.agents.reasoning_agent import ReasoningAgent
    from heart.configs.models import REASONING_AGENTS

    decomposer = TaskDecomposer(env_data=env_data)

    if extended:
        from heart.prompts.decomposition import get_decompose_extended_prompt
        from heart.core.schema import AgentTask
        task = AgentTask(
            task_id="Decompose",
            query=instruction,
            metadata={"operation": "decompose", "human_prompt": get_decompose_extended_prompt()}
        )
        results = decomposer.agent.reason([task])
        decomposition = results[0].result
    else:
        decomposition = decomposer.decompose(instruction=instruction)

    questions_dict = {}
    for q in decomposition.questions:
        q_dict = q.model_dump()
        q_id = q_dict.get("question_id", f"Q{len(questions_dict)+1}")
        q_dict["total_tokens"] = 0
        q_dict["total_time"] = 0.0
        questions_dict[q_id] = q_dict

    agent_token_estimates = {}
    for agent_id in agents:
        config = REASONING_AGENTS.get(agent_id, {"model": "gpt-4o", "temperature": 0.1})
        agent = ReasoningAgent(
            agent_id=agent_id, model_name=config["model"],
            temperature=config["temperature"], env_data=env_data,
        )
        agent_token_estimates[agent_id] = agent.estimated_tokens

    dec_tokens = decomposer.agent.total_tokens
    dec_time = decomposer.agent.total_time

    print(f"Decomposed into {len(questions_dict)} questions ({dec_tokens} tokens, {dec_time:.1f}s)")
    for q_id, q in questions_dict.items():
        print(f"  {q_id}: [{q['question_type']}] {q['prompt'][:80]}...")

    return {
        "questions_dict": questions_dict,
        "agent_token_estimates": agent_token_estimates,
        "decomposer_tokens": dec_tokens,
        "decomposer_time": dec_time,
    }


def save_decomposition(decomp: Dict[str, Any], output_dir: Path,
                       scene_name: str, task_id: str, iteration: int):
    """Save decomposition result to JSON for reuse."""
    decomp_dir = Path(output_dir) / "decompositions"
    decomp_dir.mkdir(parents=True, exist_ok=True)
    path = decomp_dir / f"{task_id}_{scene_name}_iter{iteration}.json"
    with open(path, "w") as f:
        json.dump(decomp, f, indent=2, default=str)
    print(f"Decomposition saved: {path}")
    return path


def load_decomposition(output_dir: Path, scene_name: str, task_id: str, iteration: int) -> Optional[Dict]:
    """Load previously saved decomposition. Returns None if not found."""
    path = Path(output_dir) / "decompositions" / f"{task_id}_{scene_name}_iter{iteration}.json"
    if path.exists():
        with open(path) as f:
            decomp = json.load(f)
        print(f"Decomposition loaded: {path} ({len(decomp['questions_dict'])} questions)")
        return decomp
    return None


def run_with_fixed_decomposition(
    instruction: str,
    env_data: Dict[str, Any],
    questions_dict: Dict[str, Dict],
    agent_token_estimates: Dict[str, int],
    agents: List[str],
    allocator_type: str = "heart",
    planner_type: Optional[str] = None,
    planner_config: Optional[Dict[str, Any]] = None,
    budget: int = 20000,
) -> Dict[str, Any]:
    """
    Run allocate+execute with pre-decomposed questions (skip_decompose workflow).
    Questions are deep-copied so the original set is not mutated.
    """
    from heart.core.state import initialize_state
    from heart.workflows.workflow import create_workflow

    reset_global_instances()

    state = initialize_state(
        instruction=instruction,
        env_data=env_data,
        agents=agents,
        allocator_type=allocator_type,
        planner_type=planner_type,
        planner_config=planner_config,
        token_budget=budget,
    )

    # Inject pre-decomposed questions
    state["questions"] = copy.deepcopy(questions_dict)
    state["decompose_num"] = 1
    state["allocation_map"] = {q_id: "" for q_id in questions_dict}
    state["agent_token_estimates"] = agent_token_estimates.copy()

    workflow = create_workflow(
        agents=agents,
        allocator_type=allocator_type,
        planner_type=planner_type,
        skip_decompose=True,
    )

    start_time = time.time()
    result = workflow.invoke(state, config={"recursion_limit": 100})
    total_time = time.time() - start_time

    result["_total_time"] = total_time
    return result
