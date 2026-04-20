"""
Budget × Plan SR Experiment

Same as allocator ablation but with planner included to measure Plan SR.
Uses fixed decomposition, runs HEART full across budgets with LLM-CoT planner.
Saves synthesis output (heart_constraints_text) for each run.

Usage:
    # All scenes, all tasks, default budgets
    python experiments/run_budget_plan.py

    # Specific scene/task
    python experiments/run_budget_plan.py --scenes Benevolence_1 --tasks 1 --iterations 5

    # Reuse saved decompositions from allocator ablation
    python experiments/run_budget_plan.py --decompose-dir results/allocator_ablation_xxx/

    # Custom budgets
    python experiments/run_budget_plan.py --budgets 20000 9999999
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
    extract_metrics, validate_plan_result, save_results, save_detail, append_metric, make_output_dir,
    get_scenes_and_tasks, parse_tasks_arg,
)
from experiments.configs import AGENTS_5, BUDGET_OPTIONS


# Only HEART full — budget is the variable
CONDITION = {
    "agents": AGENTS_5,
    "allocator_type": "heart",
    "planner_type": "llm_cot",
    "description": "HEART full + LLM-CoT",
}


def main():
    parser = argparse.ArgumentParser(description="Budget × Plan SR Experiment")
    parser.add_argument("--scenes", nargs="+", default=ALL_SCENES,
                        help="Scene names (default: all 3 scenes)")
    parser.add_argument("--tasks", nargs="+", default=["all"],
                        help="Task indices or 'all' (default: all)")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Iterations per budget (default: 3)")
    parser.add_argument("--budgets", type=int, nargs="+", default=BUDGET_OPTIONS,
                        help="Token budgets (default: 10000 20000 40000 9999999)")
    parser.add_argument("--decompose-dir", type=str, default=None,
                        help="Directory with saved decompositions (reuse from allocator ablation)")
    args = parser.parse_args()

    check_api_key()

    task_indices = parse_tasks_arg(args.tasks)
    scene_tasks = get_scenes_and_tasks(args.scenes, task_indices)

    total_runs = len(scene_tasks) * args.iterations * len(args.budgets)

    print(f"{'='*60}")
    print(f"BUDGET × PLAN SR EXPERIMENT (fixed decomposition)")
    print(f"Condition: {CONDITION['description']}")
    print(f"Scenes: {args.scenes}")
    print(f"Tasks: {len(scene_tasks)} scene-task pairs")
    print(f"Budgets: {args.budgets}")
    print(f"Iterations: {args.iterations}")
    print(f"Total runs: {total_runs}")
    print(f"{'='*60}")

    all_metrics = []
    all_states = []
    budget_str = "_".join(f"{b//1000}k" if b < 9999999 else "unlim" for b in args.budgets)
    output_dir = make_output_dir(f"budget_plan_{budget_str}", "_".join(args.scenes))

    for scene_name, task, task_idx in scene_tasks:
        print(f"\n{'='*60}")
        print(f"Scene: {scene_name}, Task {task_idx}: {task.goal[:60]}...")
        print(f"{'='*60}")

        env_data = load_env_data(scene_name, task)

        # Build planner_config (needed for DELTA scene/domain, LLM-CoT task_robots)
        from heart.configs.tasks import get_scene_robots
        scene_robots = get_scene_robots(scene_name, task=task)
        task_robots = {name: cfg["urdf"] for name, cfg in scene_robots.items()}
        planner_config = {
            "domain": task.domain,
            "scene": scene_name.split("_")[0].lower(),
            "task_robots": task_robots,
        }

        for iteration in range(1, args.iterations + 1):
            print(f"\n--- Iteration {iteration}/{args.iterations} ---")

            # Load saved decomposition or decompose fresh
            decomp = None
            if args.decompose_dir:
                decomp = load_decomposition(Path(args.decompose_dir), scene_name, task.id, iteration)
            if decomp is None:
                decomp = decompose_once(task.goal, env_data, AGENTS_5, extended=False)
                save_decomposition(decomp, output_dir, scene_name, task.id, iteration)

            questions_dict = decomp["questions_dict"]
            agent_token_estimates = decomp["agent_token_estimates"]
            dec_tokens = decomp["decomposer_tokens"]
            dec_time = decomp["decomposer_time"]
            num_questions = len(questions_dict)

            # Run same questions with each budget (WITH planner)
            for budget in args.budgets:
                budget_label = f"{budget//1000}k" if budget < 9999999 else "unlim"
                print(f"\n  [HEART + LLM-CoT] budget={budget_label} "
                      f"(same {num_questions} questions)")

                try:
                    result = run_with_fixed_decomposition(
                        instruction=task.goal,
                        env_data=env_data,
                        questions_dict=questions_dict,
                        agent_token_estimates=agent_token_estimates,
                        agents=CONDITION["agents"],
                        allocator_type=CONDITION["allocator_type"],
                        planner_type=CONDITION["planner_type"],
                        planner_config=planner_config,
                        budget=budget,
                    )

                    metrics = extract_metrics(result, CONDITION, scene_name, task, iteration)
                    metrics["experiment"] = f"HEART + LLM-CoT (budget={budget_label})"
                    metrics["condition"] = f"heart_{budget_label}"
                    metrics["allocator_type"] = CONDITION["allocator_type"]
                    metrics["budget"] = budget
                    metrics["budget_label"] = budget_label
                    metrics["decomposer_tokens"] = dec_tokens
                    metrics["decomposer_time"] = dec_time
                    metrics["constraints_chars"] = len(result.get("heart_constraints_text", ""))

                    # Validate plan
                    planner_type = CONDITION["planner_type"]
                    if metrics["plan_steps_count"] > 0:
                        val_result = validate_plan_result(
                            result, task, scene_name,
                            planner_type=planner_type,
                            output_dir=output_dir,
                            iteration=iteration,
                            condition=f"budget_{budget_label}",
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

                    plan_count = metrics.get("plan_steps_count", 0)
                    print(f"    Subtask SR: {metrics['success_rate']:.0%}, "
                          f"Plan steps: {plan_count}, "
                          f"Plan valid: {metrics.get('plan_valid', '?')}, "
                          f"Agent tokens: {metrics.get('agent_tokens', 0)}, "
                          f"Planner tokens: {metrics.get('planner_tokens', 0)}, "
                          f"Rounds: {metrics.get('active_rounds', '?')}, "
                          f"Time: {metrics.get('execution_time', 0):.1f}s")

                except Exception as e:
                    print(f"    ERROR: {e}")
                    traceback.print_exc()

    # Save all results (CSV + JSON details with heart_constraints_text)
    save_results(all_metrics, all_states, output_dir)

    # Summary per budget
    print(f"\n{'='*80}")
    print(f"BUDGET × PLAN SR SUMMARY")
    print(f"{'='*80}")

    header = (f"{'Budget':<8} {'N':>4} {'SubSR':>7} {'PlanSR':>8} "
              f"{'Steps':>6} {'AgentTok':>10} {'PlanTok':>9} "
              f"{'TotalTok':>10} {'Rounds':>7} {'Time(s)':>8}")
    print(header)
    print("-" * len(header))

    for budget in args.budgets:
        bl = f"{budget//1000}k" if budget < 9999999 else "unlim"
        runs = [m for m in all_metrics if m.get("budget") == budget]
        if not runs:
            continue
        n = len(runs)
        avg = lambda key: sum(r.get(key, 0) for r in runs) / n

        valid_runs = [r for r in runs if r.get("plan_valid") is not None]
        plan_sr = (sum(1 for r in valid_runs if r.get("plan_valid") or r.get("plan_valid_orig")) / len(valid_runs)
                   if valid_runs else 0)

        print(f"{bl:<8} {n:>4} {avg('success_rate'):>6.1%} {plan_sr:>7.1%} "
              f"{avg('plan_steps_count'):>6.1f} {avg('agent_tokens'):>10.0f} "
              f"{avg('planner_tokens'):>9.0f} {avg('workflow_total_tokens'):>10.0f} "
              f"{avg('active_rounds'):>7.1f} {avg('execution_time'):>8.1f}")

    print(f"{'='*80}")


if __name__ == "__main__":
    main()
