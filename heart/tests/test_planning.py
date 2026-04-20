"""
Planning test — runs planner on a single task.

Usage:
    cd HEART/

    # HEART + LLM-CoT (default)
    python heart/tests/test_planning.py
    python heart/tests/test_planning.py --scene Beechwood_0 --task 0

    # HEART + DELTA
    python heart/tests/test_planning.py --planner delta
    python heart/tests/test_planning.py --planner delta --scene Beechwood_0 --task 0

    # Baselines (planner alone, no HEART)
    python heart/tests/test_planning.py --type baseline --planner llm_cot
    python heart/tests/test_planning.py --type baseline --planner delta

    # Options
    python heart/tests/test_planning.py --scene Merom_1 --task 0 --allocator heart --agents 5 --budget 20000
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_env_data(scene_name: str, task: "Task") -> Dict[str, Any]:
    """Load scene graph + parse URDF → env_data dict."""
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


AGENTS_5 = [
    "capability_reasoner", "environmental_reasoner", "path_reasoner",
    "feasibility_reasoner", "constraint_reasoner",
]


def run_heart_planning(scene_name: str, task_index: int, planner_type: str = "llm_cot",
                       budget: int = 20000, allocator_type: str = "heart", agents: list = None):
    """Run full HEART pipeline with configurable planner."""
    from heart.core.state import initialize_state
    from heart.workflows.workflow import create_workflow
    from heart.configs.tasks import get_tasks_for_scene
    import heart.workflows.nodes as nodes

    if agents is None:
        agents = AGENTS_5

    # Reset global instances
    nodes._decomposer_instance = None
    nodes._agent_instances = {}
    nodes._allocator_instance = None
    nodes._allocator_instance_llm = None
    nodes._executor_instances = {}

    tasks = get_tasks_for_scene(scene_name)
    task = tasks[task_index]

    print(f"\n{'='*60}")
    print(f"HEART + {planner_type.upper()} Planning")
    print(f"Scene: {scene_name} | Task: {task.id}")
    print(f"Instruction: {task.goal}")
    print(f"Allocator: {allocator_type} | Agents: {len(agents)} | Budget: {budget}")
    print(f"{'='*60}")

    env_data = load_env_data(scene_name, task)

    planner_config = {
        "domain": task.domain,
        "scene": scene_name.split("_")[0].lower(),
    }

    state = initialize_state(
        instruction=task.goal,
        env_data=env_data,
        agents=agents,
        allocator_type=allocator_type,
        planner_type=planner_type,
        planner_config=planner_config,
        token_budget=budget,
    )

    workflow = create_workflow(
        agents=agents,
        allocator_type=allocator_type,
        planner_type=planner_type,
    )

    start_time = time.time()
    result = workflow.invoke(state, config={"recursion_limit": 100})
    total_time = time.time() - start_time

    _print_results(result, total_time)
    return result


def run_baseline(scene_name: str, task_index: int, planner_type: str = "llm_cot"):
    """Run planner alone (no HEART)."""
    from heart.configs.tasks import get_tasks_for_scene

    tasks = get_tasks_for_scene(scene_name)
    task = tasks[task_index]

    print(f"\n{'='*60}")
    print(f"{planner_type.upper()} Baseline (no HEART)")
    print(f"Scene: {scene_name} | Task: {task.id}")
    print(f"Instruction: {task.goal}")
    print(f"{'='*60}")

    env_data = load_env_data(scene_name, task)

    planner_kwargs = {
        "instruction": task.goal,
        "env_data": env_data,
        "domain": task.domain,
        "scene": scene_name.split("_")[0].lower(),
    }

    if planner_type == "llm_cot":
        from planners.llm_cot import LLMCoTPlanner
        planner = LLMCoTPlanner()
    elif planner_type == "delta":
        from planners.delta.delta_planner import DeltaPlanner
        planner = DeltaPlanner()
    else:
        raise ValueError(f"Unknown planner: {planner_type}")

    result = planner.plan(**planner_kwargs)

    print(f"\nTokens: {result.get('tokens_used', 0)}")
    print(f"Time: {result.get('execution_time', 0):.1f}s")

    if result.get("plan"):
        print(f"\nPlan ({len(result['plan'])} steps):")
        for i, step in enumerate(result["plan"]):
            if isinstance(step, str) and step.startswith("#"):
                print(f"\n  {step}")
            else:
                print(f"  {i+1}. {step}")
    else:
        print("\nNo plan generated")

    return result


def _print_results(result, total_time):
    """Print HEART pipeline results."""
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Questions: {len(result.get('questions', {}))}")
    print(f"Completed: {len(result.get('completed_tasks', {}))}")
    print(f"Failed: {len(result.get('failed_tasks', {}))}")
    print(f"Constraints: {len(result.get('heart_constraints_text', ''))} chars")
    print(f"Total time: {total_time:.1f}s")

    plan_steps = result.get("plan_steps", [])
    if plan_steps:
        print(f"\nPlan ({len(plan_steps)} steps):")
        for i, step in enumerate(plan_steps):
            if isinstance(step, str) and step.startswith("#"):
                print(f"\n  {step}")
            else:
                print(f"  {i+1}. {step}")
    else:
        print("\nNo plan generated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HEART Planning Test")
    parser.add_argument("--scene", default="Benevolence_1")
    parser.add_argument("--task", type=int, default=1)
    parser.add_argument("--type", default="heart", choices=["heart", "baseline"])
    parser.add_argument("--planner", default="llm_cot", choices=["llm_cot", "delta"])
    parser.add_argument("--allocator", default="heart")
    parser.add_argument("--agents", default="5", choices=["5", "1"])
    parser.add_argument("--budget", type=int, default=20000)
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Check .env file.")
        exit(1)

    if args.type == "heart":
        agents = AGENTS_5 if args.agents == "5" else ["homogeneous_reasoner"]
        run_heart_planning(
            args.scene, args.task,
            planner_type=args.planner,
            budget=args.budget,
            allocator_type=args.allocator,
            agents=agents,
        )
    elif args.type == "baseline":
        run_baseline(args.scene, args.task, planner_type=args.planner)
