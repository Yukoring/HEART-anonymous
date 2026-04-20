"""
Allocator Ablation Experiment

Compares allocator strategies across multiple budgets using fixed decomposition.
Uses extended decomposition (15-30 questions) to make capacity planning differences visible.
Decompositions are saved and can be reused with --decompose-dir.

Conditions:
- allocator_type_based:   Rule routing, sequential budget
- allocator_llm:          GPT-4o routing, sequential budget
- ablation_semantic_only: Embedding routing only (no capacity, no penalty)
- ablation_no_penalty:    Embedding + capacity planning (no penalty)
- ablation_no_capacity:   Embedding + history penalty (no capacity planning)
- allocator_heart:        Embedding + capacity + penalty (full HEART)

Usage:
    # All scenes, all tasks, default budgets (10k/20k/40k/unlimited)
    python experiments/run_allocator_ablation.py

    # Specific scenes, tasks, budgets
    python experiments/run_allocator_ablation.py --scenes Benevolence_1 --tasks 0 1 --budgets 20000 40000

    # Reuse saved decompositions (resume or run partial)
    python experiments/run_allocator_ablation.py --decompose-dir results/allocator_ablation_xxx/

    # Run specific conditions with saved decompositions
    python experiments/run_allocator_ablation.py --conditions allocator_heart --decompose-dir results/allocator_ablation_xxx/
"""

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments._common import (
    ALL_SCENES,
    check_api_key, load_env_data, decompose_once, run_with_fixed_decomposition,
    save_decomposition, load_decomposition,
    extract_metrics, validate_plan_result, save_results, save_detail, append_metric, make_output_dir, get_scenes_and_tasks, parse_tasks_arg,
)
from experiments.configs import EXPERIMENTS, AGENTS_5, BUDGET_OPTIONS

# All allocator conditions
ALLOCATOR_CONDITIONS = [
    "allocator_type_based",     # Rule routing, sequential budget
    "allocator_llm",            # LLM routing, sequential budget
    "ablation_semantic_only",   # Embedding routing only
    "ablation_no_penalty",      # Embedding + capacity planning only
    "ablation_no_capacity",     # Embedding + history penalty only
    "allocator_heart",          # Embedding + capacity + penalty (full HEART)
]


def main():
    parser = argparse.ArgumentParser(description="Allocator Ablation Experiment")
    parser.add_argument("--scenes", nargs="+", default=ALL_SCENES,
                        help="Scene names (default: all 3 scenes)")
    parser.add_argument("--tasks", nargs="+", default=["all"],
                        help="Task indices or 'all' (default: all)")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Iterations per condition (default: 3)")
    parser.add_argument("--budgets", type=int, nargs="+", default=BUDGET_OPTIONS,
                        help="Token budgets (default: 10000 20000 40000)")
    parser.add_argument("--conditions", nargs="+", default=ALLOCATOR_CONDITIONS,
                        help="Condition names (default: all 6)")
    parser.add_argument("--decompose-dir", type=str, default=None,
                        help="Directory with saved decompositions. If provided, loads from there instead of decomposing fresh.")
    args = parser.parse_args()

    check_api_key()

    task_indices = parse_tasks_arg(args.tasks)
    scene_tasks = get_scenes_and_tasks(args.scenes, task_indices)

    total_runs = len(scene_tasks) * args.iterations * len(args.conditions) * len(args.budgets)

    print(f"{'='*60}")
    print(f"ALLOCATOR ABLATION EXPERIMENT (fixed decomposition)")
    print(f"Scenes: {args.scenes}")
    print(f"Tasks: {len(scene_tasks)} scene-task pairs")
    print(f"Conditions: {args.conditions}")
    print(f"Budgets: {args.budgets}")
    print(f"Iterations: {args.iterations}")
    print(f"Total runs: {total_runs}")
    print(f"{'='*60}")

    all_metrics = []
    all_states = []
    output_dir = make_output_dir("allocator_ablation", "_".join(args.scenes))

    for scene_name, task, task_idx in scene_tasks:
        print(f"\n{'='*60}")
        print(f"Scene: {scene_name}, Task {task_idx}: {task.goal[:60]}...")
        print(f"{'='*60}")

        env_data = load_env_data(scene_name, task)

        for iteration in range(1, args.iterations + 1):
            print(f"\n--- Iteration {iteration}/{args.iterations} ---")

            # Load saved decomposition or decompose fresh (always extended for allocator ablation)
            decomp = None
            if args.decompose_dir:
                decomp = load_decomposition(Path(args.decompose_dir), scene_name, task.id, iteration)
            if decomp is None:
                decomp = decompose_once(task.goal, env_data, AGENTS_5, extended=True)
                save_decomposition(decomp, output_dir, scene_name, task.id, iteration)

            questions_dict = decomp["questions_dict"]
            agent_token_estimates = decomp["agent_token_estimates"]
            dec_tokens = decomp["decomposer_tokens"]
            dec_time = decomp["decomposer_time"]
            num_questions = len(questions_dict)

            # Run all conditions × budgets with same questions
            for condition_name in args.conditions:
                config = EXPERIMENTS.get(condition_name)
                if not config:
                    print(f"  Unknown condition: {condition_name}, skipping")
                    continue

                agents = config["agents"]

                for budget in args.budgets:
                    budget_label = f"{budget//1000}k"
                    print(f"\n  [{config['description']}] budget={budget_label} "
                          f"(same {num_questions} questions)")

                    try:
                        result = run_with_fixed_decomposition(
                            instruction=task.goal,
                            env_data=env_data,
                            questions_dict=questions_dict,
                            agent_token_estimates=agent_token_estimates,
                            agents=agents,
                            allocator_type=config["allocator_type"],
                            planner_type=config.get("planner_type"),
                            budget=budget,
                        )

                        metrics = extract_metrics(result, config, scene_name, task, iteration)
                        metrics["condition"] = condition_name
                        metrics["allocator_type"] = config["allocator_type"]
                        metrics["budget"] = budget
                        metrics["budget_label"] = budget_label
                        metrics["decomposer_tokens"] = dec_tokens
                        metrics["decomposer_time"] = dec_time
                        planner_type = config.get("planner_type")
                        metrics["planner_type"] = planner_type

                        # Validate plan (if planner was used)
                        if metrics["plan_steps_count"] > 0:
                            val_result = validate_plan_result(
                                result, task, scene_name, planner_type=planner_type,
                                output_dir=output_dir, iteration=iteration,
                                condition=f"{condition_name}_{budget_label}",
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

                        print(f"    SR: {metrics['success_rate']:.0%}, "
                              f"Tokens: {metrics['workflow_total_tokens']}, "
                              f"Rounds: {metrics.get('active_rounds', '?')}, "
                              f"Retries: {metrics.get('total_retries', 0)}")

                    except Exception as e:
                        print(f"    ERROR: {e}")
                        traceback.print_exc()

    # Save raw data
    save_results(all_metrics, all_states, output_dir)

    # ── Summary Table (matches paper Table III format + extras) ──

    # Build summary data
    summary_rows = []
    for condition_name in args.conditions:
        config = EXPERIMENTS.get(condition_name, {})
        for budget in args.budgets:
            bl = f"{budget // 1000}k" if budget < 9999999 else "unlim"
            runs = [m for m in all_metrics
                    if m.get("condition") == condition_name and m.get("budget") == budget]
            if not runs:
                continue
            n = len(runs)
            avg = lambda key: sum(r.get(key, 0) for r in runs) / n
            summary_rows.append({
                "condition": condition_name,
                "description": config.get("description", condition_name),
                "budget": budget,
                "budget_label": bl,
                "n": n,
                "sr": avg("success_rate"),
                "rounds": avg("active_rounds"),
                "tokens": avg("workflow_total_tokens"),
                "agent_tokens": avg("agent_tokens"),
                "retries": avg("total_retries"),
                "misroute": avg("misroute_count"),
                "partial": avg("partial_count"),
                "oos": avg("out_of_scope_count"),
                "throughput": avg("avg_round_throughput"),
                "time": avg("execution_time"),
            })

    # Save summary CSV
    if summary_rows:
        import csv
        summary_path = output_dir / "summary.csv"
        with open(summary_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"Summary saved to {summary_path}")

    # Print: Table III style (condition × budget pivot — SR, Rounds, Tokens)
    print(f"\n{'='*100}")
    print(f"ALLOCATOR SUMMARY  (paper Table III format: SubSR / Rounds / Tokens)")
    print(f"{'='*100}")

    budget_labels = []
    for b in args.budgets:
        budget_labels.append(f"{b // 1000}k" if b < 9999999 else "unlim")

    header = f"{'Condition':<35}"
    for bl in budget_labels:
        header += f" | {bl:^22}"
    print(header)
    sub_header = f"{'':<35}"
    for bl in budget_labels:
        sub_header += f" |  {'SR':>5} {'Rnds':>5} {'Tok(k)':>7}"
    print(sub_header)
    print("-" * len(header))

    for condition_name in args.conditions:
        config = EXPERIMENTS.get(condition_name, {})
        line = f"{config.get('description', condition_name):<35}"
        for budget in args.budgets:
            rows = [r for r in summary_rows
                    if r["condition"] == condition_name and r["budget"] == budget]
            if rows:
                r = rows[0]
                line += f" | {r['sr']:5.1%} {r['rounds']:5.1f} {r['tokens']/1000:7.1f}"
            else:
                line += f" |     -     -       -"
        print(line)

    # Print: Extended detail table (retries, misroute, partial, OOS)
    print(f"\n{'='*100}")
    print(f"ALLOCATOR DETAIL  (component effect indicators)")
    print(f"{'='*100}")

    detail_header = (f"{'Condition':<35} {'Budget':>6} {'SubSR':>6} {'Retries':>8} "
                     f"{'Misroute':>9} {'Partial':>8} {'OOS':>5} {'Thruput':>8} {'Time(s)':>8}  N")
    print(detail_header)
    print("-" * len(detail_header))

    for condition_name in args.conditions:
        config = EXPERIMENTS.get(condition_name, {})
        for budget in args.budgets:
            rows = [r for r in summary_rows
                    if r["condition"] == condition_name and r["budget"] == budget]
            if not rows:
                continue
            r = rows[0]
            bl = r["budget_label"]
            desc = config.get("description", condition_name)
            print(f"{desc:<35} {bl:>6} {r['sr']:5.1%} {r['retries']:8.1f} "
                  f"{r['misroute']:9.1f} {r['partial']:8.1f} {r['oos']:5.1f} "
                  f"{r['throughput']:8.2f} {r['time']:7.1f} {r['n']:3d}")

    print(f"{'='*100}")


if __name__ == "__main__":
    main()
