"""
Agent Role Ablation Experiment

Compares agent configurations with fixed decomposition and plan validation (VAL).
Decomposition is done once per (task, iteration) and reused across all conditions,
so the only variable is the agent configuration.

Conditions:
- 5_agents:     5 heterogeneous agents (capability, environmental, path, feasibility, constraint)
- 3_agents:     3 merged agents (physical, spatial, constraint)
- homogeneous:  1 homogeneous agent (all data, no specialization)

Usage:
    # All scenes, all tasks (default)
    python experiments/run_agent_role.py

    # Specific scenes, tasks, iterations
    python experiments/run_agent_role.py --scenes Benevolence_1 --tasks 0 1 --iterations 5

    # Specific conditions
    python experiments/run_agent_role.py --conditions 5_agents homogeneous

    # Reuse saved decompositions
    python experiments/run_agent_role.py --decompose-dir results/agent_role_xxx/
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
from experiments.configs import EXPERIMENTS

AGENT_CONDITIONS = [
    "5_agents",         # 5 heterogeneous agents
    "3_agents",         # 3 merged agents
    "homogeneous",      # 1 homogeneous agent
]


def get_agent_token_estimates(agents, env_data):
    """Compute per-agent token estimates for a given agent list."""
    from heart.agents.reasoning_agent import ReasoningAgent
    from heart.configs.models import REASONING_AGENTS

    estimates = {}
    for agent_id in agents:
        config = REASONING_AGENTS.get(agent_id, {"model": "gpt-4o", "temperature": 0.1})
        agent = ReasoningAgent(
            agent_id=agent_id, model_name=config["model"],
            temperature=config["temperature"], env_data=env_data,
        )
        estimates[agent_id] = agent.estimated_tokens
    return estimates


def main():
    parser = argparse.ArgumentParser(description="Agent Role Ablation Experiment")
    parser.add_argument("--scenes", nargs="+", default=ALL_SCENES,
                        help="Scene names (default: all 3 scenes)")
    parser.add_argument("--tasks", nargs="+", default=["all"],
                        help="Task indices or 'all' (default: all)")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--budget", type=int, default=20000)
    parser.add_argument("--conditions", nargs="+", default=AGENT_CONDITIONS)
    parser.add_argument("--decompose-dir", type=str, default=None,
                        help="Directory with saved decompositions to reuse")
    args = parser.parse_args()

    check_api_key()

    task_indices = parse_tasks_arg(args.tasks)
    scene_tasks = get_scenes_and_tasks(args.scenes, task_indices)

    print(f"{'='*60}")
    print(f"AGENT ROLE ABLATION EXPERIMENT (fixed decomposition)")
    print(f"Scenes: {args.scenes}")
    print(f"Tasks: {len(scene_tasks)} scene-task pairs")
    print(f"Conditions: {args.conditions}")
    print(f"Iterations: {args.iterations}")
    print(f"Validation: ON")
    print(f"{'='*60}")

    all_metrics = []
    all_states = []
    output_dir = make_output_dir("agent_role", "_".join(args.scenes))

    # Outer loop: task × iteration (decompose once), inner loop: conditions
    for scene_name, task, task_idx in scene_tasks:
        print(f"\n{'='*60}")
        print(f"Scene: {scene_name}, Task {task_idx}: {task.goal[:60]}...")
        print(f"{'='*60}")

        env_data = load_env_data(scene_name, task)

        for iteration in range(1, args.iterations + 1):
            print(f"\n  --- Iteration {iteration}/{args.iterations} ---")

            # Decompose once (or load saved)
            decomp = None
            if args.decompose_dir:
                decomp = load_decomposition(
                    Path(args.decompose_dir), scene_name, task.id, iteration)

            if decomp is None:
                # Use 5_agents for decomposition (superset)
                decomp = decompose_once(
                    instruction=task.goal, env_data=env_data,
                    agents=EXPERIMENTS["5_agents"]["agents"],
                )
                save_decomposition(decomp, output_dir, scene_name, task.id, iteration)

            questions_dict = decomp["questions_dict"]
            dec_tokens = decomp["decomposer_tokens"]
            dec_time = decomp["decomposer_time"]

            # Run each condition with the same decomposition
            for condition_name in args.conditions:
                config = EXPERIMENTS.get(condition_name)
                if not config:
                    print(f"  Unknown condition: {condition_name}, skipping")
                    continue

                agents = config["agents"]
                planner_type = config.get("planner_type", "llm_cot")
                print(f"\n    [{condition_name}] {len(agents)} agents, planner={planner_type}")

                try:
                    # Compute token estimates for this agent configuration
                    agent_token_estimates = get_agent_token_estimates(agents, env_data)

                    result = run_with_fixed_decomposition(
                        instruction=task.goal,
                        env_data=env_data,
                        questions_dict=questions_dict,
                        agent_token_estimates=agent_token_estimates,
                        agents=agents,
                        allocator_type=config.get("allocator_type", "heart"),
                        planner_type=planner_type,
                        budget=args.budget,
                    )

                    metrics = extract_metrics(result, config, scene_name, task, iteration)
                    metrics["condition"] = condition_name
                    metrics["num_agents"] = len(agents)
                    metrics["planner_type"] = planner_type
                    metrics["decomposer_tokens"] = dec_tokens
                    metrics["decomposer_time"] = dec_time

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
                        print(f"      Plan valid: {val_result['valid']}"
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

                    print(f"      Plan steps: {metrics['plan_steps_count']}, "
                          f"Tokens: {metrics['workflow_total_tokens']}, "
                          f"Time: {metrics['execution_time']:.1f}s")
                except Exception as e:
                    print(f"      ERROR: {e}")
                    traceback.print_exc()

    save_results(all_metrics, all_states, output_dir)

    # ── Summary Table (matches paper Table II format + extras) ──
    print(f"\n{'='*100}")
    print(f"AGENT ROLE SUMMARY  (paper Table II format)")
    print(f"{'='*100}")

    # Per-scene × per-condition breakdown
    scenes_seen = sorted(set(m["scene"] for m in all_metrics))
    header = (f"{'Scene':<16} {'Condition':<14} {'#Sub':>5} {'Rounds':>7} "
              f"{'Tok/sub':>8} {'Time/sub':>9} {'SubSR':>7} {'PlanSR':>7} "
              f"{'Retries':>8} {'Misroute':>9} {'Partial':>8} {'OOS':>5}  N")
    print(header)
    print("-" * len(header))

    for scene in scenes_seen:
        for condition_name in args.conditions:
            runs = [m for m in all_metrics
                    if m["scene"] == scene and m.get("condition") == condition_name]
            if not runs:
                continue
            n = len(runs)
            avg = lambda key, r=runs: sum(m.get(key, 0) for m in r) / len(r)
            valid_runs = [r for r in runs if r.get("plan_valid") is not None]
            plan_sr = (sum(1 for r in valid_runs if r["plan_valid"] or r.get("plan_valid_orig")) / len(valid_runs)
                       if valid_runs else float("nan"))

            scene_label = scene.split("_")[0]
            print(f"{scene_label:<16} {condition_name:<14} "
                  f"{avg('total_questions'):5.1f} {avg('active_rounds'):7.1f} "
                  f"{avg('token_per_question'):8.0f} {avg('time_per_question'):8.1f}s "
                  f"{avg('success_rate'):6.1%} {plan_sr:6.1%} "
                  f"{avg('total_retries'):8.1f} {avg('misroute_count'):9.1f} "
                  f"{avg('partial_count'):8.1f} {avg('out_of_scope_count'):5.1f} {n:3d}")
        print()

    # Aggregated per-condition (across all scenes)
    print(f"\n{'='*100}")
    print(f"AGGREGATED (all scenes)")
    print(f"{'='*100}")
    agg_header = (f"{'Condition':<14} {'#Sub':>5} {'Rounds':>7} "
                  f"{'Tok/sub':>8} {'Time/sub':>9} {'SubSR':>7} {'PlanSR':>7} "
                  f"{'TotalTok':>9} {'AgentTok':>9}  N")
    print(agg_header)
    print("-" * len(agg_header))

    for condition_name in args.conditions:
        runs = [m for m in all_metrics if m.get("condition") == condition_name]
        if not runs:
            continue
        n = len(runs)
        avg = lambda key, r=runs: sum(m.get(key, 0) for m in r) / len(r)
        valid_runs = [r for r in runs if r.get("plan_valid") is not None]
        plan_sr = (sum(1 for r in valid_runs if r["plan_valid"]) / len(valid_runs)
                   if valid_runs else float("nan"))

        print(f"{condition_name:<14} "
              f"{avg('total_questions'):5.1f} {avg('active_rounds'):7.1f} "
              f"{avg('token_per_question'):8.0f} {avg('time_per_question'):8.1f}s "
              f"{avg('success_rate'):6.1%} {plan_sr:6.1%} "
              f"{avg('workflow_total_tokens'):9.0f} {avg('agent_tokens'):9.0f} {n:3d}")

    print(f"{'='*100}")


if __name__ == "__main__":
    main()
