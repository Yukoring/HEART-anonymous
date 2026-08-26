"""
Planner Comparison Experiment

Compares planners with and without HEART reasoning, with plan validation (VAL).

Conditions:
- baseline_llm_cot: LLM-CoT alone (no HEART)
- baseline_delta:   DELTA alone (no HEART)
- heart_llm_cot:    HEART + LLM-CoT
- heart_delta:      HEART + DELTA
- baseline_triple_s: Triple-S alone (related-work baseline)

Triple-S is not in the default set. It answers a different question from the
others — how HEART compares against related work, rather than which planner
HEART is attached to — and it brings its own multi-LLM reasoning, so there is no
`heart_triple_s` counterpart to pair it with. Ask for it explicitly.

Usage:
    # All scenes, all tasks (default)
    python experiments/run_planner.py

    # Specific scenes, tasks, conditions
    python experiments/run_planner.py --scenes Benevolence_1 --tasks 0 1 --conditions baseline_llm_cot heart_llm_cot

    # LLM-CoT only comparison
    python experiments/run_planner.py --conditions baseline_llm_cot heart_llm_cot

    # DELTA only comparison
    python experiments/run_planner.py --conditions baseline_delta heart_delta

    # Related-work baseline
    python experiments/run_planner.py --conditions baseline_triple_s
"""

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments._common import (
    ALL_SCENES,
    check_api_key, run_heart_trial, run_baseline_trial, extract_metrics,
    validate_plan_result, save_results, save_detail, append_metric, make_output_dir, print_summary,
    get_scenes_and_tasks, parse_tasks_arg,
)
from experiments.configs import EXPERIMENTS

PLANNER_CONDITIONS = [
    "baseline_llm_cot",   # LLM-CoT alone
    "baseline_delta",     # DELTA alone
    "heart_llm_cot",      # HEART + LLM-CoT
    "heart_delta",        # HEART + DELTA
]

# Runs only when named on the command line, so the default set stays the
# planner-agnosticism comparison it has always been.
EXTRA_CONDITIONS = [
    "baseline_triple_s",  # Triple-S alone (related-work baseline)
]


def main():
    parser = argparse.ArgumentParser(description="Planner Comparison Experiment")
    parser.add_argument("--scenes", nargs="+", default=ALL_SCENES,
                        help="Scene names (default: all 3 scenes)")
    parser.add_argument("--tasks", nargs="+", default=["all"],
                        help="Task indices or 'all' (default: all)")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--budget", type=int, default=20000)
    parser.add_argument("--conditions", nargs="+", default=PLANNER_CONDITIONS,
                        choices=PLANNER_CONDITIONS + EXTRA_CONDITIONS,
                        metavar="CONDITION")
    args = parser.parse_args()

    check_api_key()

    task_indices = parse_tasks_arg(args.tasks)
    scene_tasks = get_scenes_and_tasks(args.scenes, task_indices)

    print(f"{'='*60}")
    print(f"PLANNER COMPARISON EXPERIMENT")
    print(f"Scenes: {args.scenes}")
    print(f"Tasks: {len(scene_tasks)} scene-task pairs")
    print(f"Conditions: {args.conditions}")
    print(f"Iterations: {args.iterations}")
    print(f"Validation: ON")
    print(f"{'='*60}")

    all_metrics = []
    all_states = []
    output_dir = make_output_dir("planner", "_".join(args.scenes))

    for condition_name in args.conditions:
        config = EXPERIMENTS.get(condition_name)
        if not config:
            print(f"Unknown condition: {condition_name}, skipping")
            continue

        is_baseline = config.get("agents") is None
        planner_type = config.get("planner_type", "llm_cot")

        print(f"\n{'='*60}")
        print(f"CONDITION: {config['description']}")
        print(f"{'='*60}")

        for scene_name, task, task_idx in scene_tasks:
            print(f"\n--- Scene: {scene_name}, Task {task_idx}: {task.goal[:60]}... ---")

            for iteration in range(1, args.iterations + 1):
                print(f"  Iteration {iteration}/{args.iterations}")
                try:
                    # 1. Run planning pipeline
                    if is_baseline:
                        result = run_baseline_trial(scene_name, task, iteration, planner_type=planner_type)
                    else:
                        result = run_heart_trial(
                            config, scene_name, task, iteration, budget=args.budget
                        )

                    # 2. Extract metrics
                    metrics = extract_metrics(result, config, scene_name, task, iteration)
                    metrics["condition"] = condition_name
                    metrics["is_baseline"] = is_baseline
                    metrics["planner_type"] = planner_type

                    # 3. Validate plan (outside pipeline — tokens/time NOT counted)
                    if metrics["plan_steps_count"] > 0:
                        val_result = validate_plan_result(
                            result, task, scene_name, planner_type=planner_type,
                            output_dir=output_dir, iteration=iteration,
                            condition=condition_name,
                        )
                        metrics["plan_valid"] = val_result["valid"]
                        metrics["plan_valid_orig"] = val_result.get("valid_orig", None)
                        # If decomposed plan failed but orig plan is valid, update info
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

    # ── Summary Table (matches paper Table IV format + extras) ──
    print(f"\n{'='*100}")
    print(f"PLANNER COMPARISON SUMMARY  (paper Table IV format)")
    print(f"{'='*100}")

    # Per-scene × per-condition
    scenes_seen = sorted(set(m["scene"] for m in all_metrics))
    header = (f"{'Scene':<16} {'Condition':<20} {'PlanSR':>7} {'Steps':>6} "
              f"{'TotalTok(k)':>12} {'PlanTok(k)':>11} {'Time(s)':>8} "
              f"{'SubSR':>7}  N")
    print(header)
    print("-" * len(header))

    for scene in scenes_seen:
        for condition_name in args.conditions:
            runs = [m for m in all_metrics
                    if m["scene"] == scene and m.get("condition") == condition_name]
            if not runs:
                continue
            n = len(runs)
            avg = lambda key: sum(r.get(key, 0) for r in runs) / n
            valid_runs = [r for r in runs if r.get("plan_valid") is not None]
            plan_sr = (sum(1 for r in valid_runs if r["plan_valid"] or r.get("plan_valid_orig")) / len(valid_runs)
                       if valid_runs else float("nan"))

            scene_label = scene.split("_")[0]
            print(f"{scene_label:<16} {condition_name:<20} "
                  f"{plan_sr:6.1%} {avg('plan_steps_count'):6.1f} "
                  f"{avg('workflow_total_tokens')/1000:11.1f} {avg('planner_tokens')/1000:11.1f} "
                  f"{avg('execution_time'):7.1f} "
                  f"{avg('success_rate'):6.1%} {n:3d}")
        print()

    # Aggregated per-condition
    print(f"\n{'='*100}")
    print(f"AGGREGATED (all scenes)")
    print(f"{'='*100}")
    agg_header = (f"{'Condition':<20} {'PlanSR':>7} {'Steps':>6} "
                  f"{'TotalTok(k)':>12} {'PlanTok(k)':>11} {'Time(s)':>8}  N")
    print(agg_header)
    print("-" * len(agg_header))

    for condition_name in args.conditions:
        runs = [m for m in all_metrics if m.get("condition") == condition_name]
        if not runs:
            continue
        n = len(runs)
        avg = lambda key: sum(r.get(key, 0) for r in runs) / n
        valid_runs = [r for r in runs if r.get("plan_valid") is not None]
        plan_sr = (sum(1 for r in valid_runs if r["plan_valid"] or r.get("plan_valid_orig")) / len(valid_runs)
                   if valid_runs else float("nan"))

        print(f"{condition_name:<20} "
              f"{plan_sr:6.1%} {avg('plan_steps_count'):6.1f} "
              f"{avg('workflow_total_tokens')/1000:11.1f} {avg('planner_tokens')/1000:11.1f} "
              f"{avg('execution_time'):7.1f} {n:3d}")

    print(f"{'='*100}")


if __name__ == "__main__":
    main()
