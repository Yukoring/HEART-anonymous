"""
Task Type Ablation Experiment (Response letter)

Shows that task types are auxiliary labels, not the system backbone.
Compares decomposition with different type granularities:
- typed_full:    11 types (current HEART)
- typed_reduced: ~7 types (merged similar types) — TODO
- untyped:       No type labels (routing by prompt content only) — TODO

Usage:
    # All scenes, all tasks (default)
    python experiments/run_type_ablation.py

    # Specific scenes, tasks, conditions
    python experiments/run_type_ablation.py --scenes Benevolence_1 --tasks 0 1 --iterations 3 --conditions typed_full
"""

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments._common import (
    ALL_SCENES,
    check_api_key, run_heart_trial, extract_metrics,
    validate_plan_result, save_results, save_detail, append_metric, make_output_dir,
    print_summary, get_scenes_and_tasks, parse_tasks_arg,
)
from experiments.configs import AGENTS_5

# Type ablation conditions — custom configs (not in EXPERIMENTS dict)
TYPE_CONDITIONS = {
    "typed_full": {
        "agents": AGENTS_5,
        "allocator_type": "heart",
        "planner_type": "llm_cot",
        "use_typed_decomposition": True,
        "description": "Full 11 types (current HEART)",
    },
}


def main():
    parser = argparse.ArgumentParser(description="Task Type Ablation")
    parser.add_argument("--scenes", nargs="+", default=ALL_SCENES,
                        help="Scene names (default: all 3 scenes)")
    parser.add_argument("--tasks", nargs="+", default=["all"],
                        help="Task indices or 'all' (default: all)")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--budget", type=int, default=20000)
    parser.add_argument("--conditions", nargs="+", default=None,
                        help="Condition names (default: all)")
    args = parser.parse_args()

    check_api_key()

    task_indices = parse_tasks_arg(args.tasks)
    scene_tasks = get_scenes_and_tasks(args.scenes, task_indices)

    conditions = {k: v for k, v in TYPE_CONDITIONS.items()
                  if args.conditions is None or k in args.conditions}

    print(f"{'='*60}")
    print(f"TYPE ABLATION EXPERIMENT")
    print(f"Scenes: {args.scenes}")
    print(f"Tasks: {len(scene_tasks)} scene-task pairs")
    print(f"Conditions: {list(conditions.keys())}")
    print(f"Iterations: {args.iterations}")
    print(f"Validation: ON")
    print(f"{'='*60}")

    all_metrics = []
    all_states = []
    output_dir = make_output_dir("type_ablation", "_".join(args.scenes))

    for condition_name, config in conditions.items():
        print(f"\n{'='*60}")
        print(f"CONDITION: {config['description']}")
        print(f"{'='*60}")

        planner_type = config.get("planner_type", "llm_cot")

        for scene_name, task, task_idx in scene_tasks:
            print(f"\n--- Scene: {scene_name}, Task {task_idx}: {task.goal[:60]}... ---")

            for iteration in range(1, args.iterations + 1):
                print(f"  Iteration {iteration}/{args.iterations}")
                try:
                    result = run_heart_trial(
                        config, scene_name, task, iteration, budget=args.budget
                    )
                    metrics = extract_metrics(result, config, scene_name, task, iteration)
                    metrics["condition"] = condition_name
                    metrics["type_mode"] = config.get("use_typed_decomposition", True)
                    metrics["planner_type"] = planner_type

                    # Validate plan
                    if metrics["plan_steps_count"] > 0:
                        val_result = validate_plan_result(
                            result, task, scene_name, planner_type=planner_type,
                            output_dir=output_dir, iteration=iteration,
                            condition=condition_name,
                        )
                        metrics["plan_valid"] = val_result["valid"]
                        metrics["plan_valid_orig"] = val_result.get("valid_orig", None)
                        if not val_result["valid"] and val_result.get("valid_orig"):
                            metrics["plan_valid_info"] = "Plan valid (undecomposed)"
                        else:
                            metrics["plan_valid_info"] = val_result["info"]
                        print(f"    Plan valid: {val_result['valid']}"
                              f"{' (orig: ' + str(val_result.get('valid_orig')) + ')' if planner_type == 'delta' else ''}"
                              f" — {metrics['plan_valid_info']}")
                    else:
                        metrics["plan_valid"] = False
                        metrics["plan_valid_orig"] = False
                        metrics["plan_valid_info"] = "no plan"

                    all_metrics.append(metrics)
                    all_states.append(result)
                    append_metric(metrics, output_dir)
                    save_detail(result, metrics, output_dir)

                    print(f"    Plan steps: {metrics['plan_steps_count']}, "
                          f"Tokens: {metrics['workflow_total_tokens']}, "
                          f"Time: {metrics['execution_time']:.1f}s")

                except Exception as e:
                    print(f"    ERROR: {e}")
                    traceback.print_exc()

    save_results(all_metrics, all_states, output_dir)
    print_summary(all_metrics)


if __name__ == "__main__":
    main()
