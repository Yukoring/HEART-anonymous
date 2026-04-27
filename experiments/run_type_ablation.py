"""
Task Type Granularity Ablation (Response letter)

Shows that task types are auxiliary routing labels, not the system backbone.
Each condition decomposes INDEPENDENTLY with its own type set (5/8/11),
so the decomposer generates questions tailored to the available types.

What we want to show:
  - PlanSR is stable across type granularities (5 vs 8 vs 11)
  - This proves the allocator routes primarily by question text semantics
  - Therefore, the 11 types are a convenient taxonomy, not an architectural dependency

Conditions:
  - types_11: Original 11 task types
  - types_8:  8 merged types
  - types_5:  5 merged types

Usage:
    python experiments/run_type_ablation.py --scenes Benevolence_1 --iterations 5
"""

import argparse
import copy
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments._common import (
    ALL_SCENES,
    check_api_key, load_env_data, run_with_fixed_decomposition,
    extract_metrics, validate_plan_result, save_results, save_detail, append_metric,
    make_output_dir, get_scenes_and_tasks, parse_tasks_arg,
)
from experiments.configs import AGENTS_5

from heart.core.schema import TaskType, TaskType8, TaskType5


def get_type_descriptions(type_enum):
    """Generate task type descriptions string from any TaskType enum."""
    return "\n".join(f"- **{t.value}**: {t.description}" for t in type_enum)


def decompose_with_types(instruction, env_data, type_enum, question_range="10-15"):
    """
    Decompose instruction using a specific TaskType enum.
    Monkey-patches get_task_type_descriptions to inject custom types,
    then restores the original after decomposition.
    """
    import heart.prompts.descriptions as desc_module
    import heart.agents.decomposer_agent as dec_module

    # Save originals
    orig_fn = desc_module.get_task_type_descriptions

    # Patch with custom types
    custom_desc = get_type_descriptions(type_enum)
    desc_module.get_task_type_descriptions = lambda: custom_desc

    # Also patch in decomposer_agent if it cached the import
    if hasattr(dec_module, 'get_task_type_descriptions'):
        dec_module.get_task_type_descriptions = lambda: custom_desc

    try:
        from heart.orchestrator.task_decomposer import TaskDecomposer
        from heart.agents.reasoning_agent import ReasoningAgent
        from heart.configs.models import REASONING_AGENTS

        decomposer = TaskDecomposer(env_data=env_data)
        decomposition = decomposer.decompose(instruction=instruction)

        questions_dict = {}
        for q in decomposition.questions:
            q_dict = q.model_dump()
            q_id = q_dict.get("question_id", f"Q{len(questions_dict)+1}")
            q_dict["total_tokens"] = 0
            q_dict["total_time"] = 0.0
            questions_dict[q_id] = q_dict

        agent_token_estimates = {}
        for agent_id in AGENTS_5:
            config = REASONING_AGENTS.get(agent_id, {"model": "gpt-4o", "temperature": 0.1})
            agent = ReasoningAgent(
                agent_id=agent_id, model_name=config["model"],
                temperature=config["temperature"], env_data=env_data,
            )
            agent_token_estimates[agent_id] = agent.estimated_tokens

        dec_tokens = decomposer.agent.total_tokens
        dec_time = decomposer.agent.total_time

        type_names = [t.value for t in type_enum]
        print(f"  Decomposed into {len(questions_dict)} questions ({dec_tokens} tokens, {dec_time:.1f}s)")
        print(f"  Types used: {type_names}")
        for q_id, q in questions_dict.items():
            print(f"    {q_id}: [{q['question_type']}] {q['prompt'][:80]}...")

        return {
            "questions_dict": questions_dict,
            "agent_token_estimates": agent_token_estimates,
            "decomposer_tokens": dec_tokens,
            "decomposer_time": dec_time,
        }
    finally:
        # Restore originals
        desc_module.get_task_type_descriptions = orig_fn
        if hasattr(dec_module, 'get_task_type_descriptions'):
            dec_module.get_task_type_descriptions = orig_fn


# Condition definitions
TYPE_CONDITIONS = {
    "types_11": {
        "type_enum": TaskType,
        "num_types": 11,
        "description": "11 types (current HEART)",
    },
    "types_8": {
        "type_enum": TaskType8,
        "num_types": 8,
        "description": "8 types (similar merged)",
    },
    "types_5": {
        "type_enum": TaskType5,
        "num_types": 5,
        "description": "5 types (maximally merged)",
    },
}

BASE_CONFIG = {
    "agents": AGENTS_5,
    "allocator_type": "heart",
    "planner_type": "llm_cot",
    "description": "HEART 5 agents + LLM-CoT",
}


def main():
    parser = argparse.ArgumentParser(description="Task Type Granularity Ablation")
    parser.add_argument("--scenes", nargs="+", default=["Benevolence_1"],
                        help="Scene names (default: Benevolence_1)")
    parser.add_argument("--tasks", nargs="+", default=["all"],
                        help="Task indices or 'all'")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--budget", type=int, default=20000)
    parser.add_argument("--conditions", nargs="+", default=None)
    args = parser.parse_args()

    check_api_key()

    task_indices = parse_tasks_arg(args.tasks)
    scene_tasks = get_scenes_and_tasks(args.scenes, task_indices)

    conditions = {k: v for k, v in TYPE_CONDITIONS.items()
                  if args.conditions is None or k in args.conditions}

    total_runs = len(scene_tasks) * args.iterations * len(conditions)

    print(f"{'='*60}")
    print(f"TYPE GRANULARITY ABLATION")
    print(f"Scenes: {args.scenes}")
    print(f"Tasks: {len(scene_tasks)} scene-task pairs")
    print(f"Conditions: {list(conditions.keys())}")
    print(f"Iterations: {args.iterations}")
    print(f"Total runs: {total_runs}")
    print(f"{'='*60}")

    all_metrics = []
    all_states = []
    output_dir = make_output_dir("type_ablation", "_".join(args.scenes))

    from experiments._common import reset_global_instances

    for scene_name, task, task_idx in scene_tasks:
        print(f"\n{'='*60}")
        print(f"Scene: {scene_name}, Task {task_idx}: {task.goal[:60]}...")
        print(f"{'='*60}")

        env_data = load_env_data(scene_name, task)

        for iteration in range(1, args.iterations + 1):
            print(f"\n  --- Iteration {iteration}/{args.iterations} ---")

            for condition_name, cond_config in conditions.items():
                type_enum = cond_config["type_enum"]
                num_types = cond_config["num_types"]
                desc = cond_config["description"]

                print(f"\n    [{condition_name}] {desc}")

                try:
                    # Reset global instances for clean state
                    reset_global_instances()

                    # Decompose with this condition's type set
                    decomp = decompose_with_types(
                        instruction=task.goal,
                        env_data=env_data,
                        type_enum=type_enum,
                    )

                    questions_dict = decomp["questions_dict"]
                    agent_token_estimates = decomp["agent_token_estimates"]
                    dec_tokens = decomp["decomposer_tokens"]
                    dec_time = decomp["decomposer_time"]

                    # Run HEART pipeline with decomposed questions
                    result = run_with_fixed_decomposition(
                        instruction=task.goal,
                        env_data=env_data,
                        questions_dict=questions_dict,
                        agent_token_estimates=agent_token_estimates,
                        agents=AGENTS_5,
                        allocator_type="heart",
                        planner_type="llm_cot",
                        budget=args.budget,
                    )

                    metrics = extract_metrics(result, BASE_CONFIG, scene_name, task, iteration)
                    metrics["condition"] = condition_name
                    metrics["num_types"] = num_types
                    metrics["planner_type"] = "llm_cot"
                    metrics["decomposer_tokens"] = dec_tokens
                    metrics["decomposer_time"] = dec_time

                    # Validate plan
                    if metrics["plan_steps_count"] > 0:
                        val_result = validate_plan_result(
                            result, task, scene_name, planner_type="llm_cot",
                            output_dir=output_dir, iteration=iteration,
                            condition=condition_name,
                        )
                        metrics["plan_valid"] = val_result["valid"]
                        metrics["plan_valid_orig"] = val_result.get("valid_orig", None)
                        if not val_result["valid"] and val_result.get("valid_orig"):
                            metrics["plan_valid_info"] = "Plan valid (undecomposed)"
                        else:
                            metrics["plan_valid_info"] = val_result["info"]
                        print(f"      Plan valid: {val_result['valid']} — {metrics['plan_valid_info']}")
                    else:
                        metrics["plan_valid"] = False
                        metrics["plan_valid_orig"] = False
                        metrics["plan_valid_info"] = "no plan"

                    all_metrics.append(metrics)
                    all_states.append(result)
                    append_metric(metrics, output_dir)
                    save_detail(result, metrics, output_dir)

                    print(f"      Questions: {len(questions_dict)}, "
                          f"Plan steps: {metrics['plan_steps_count']}, "
                          f"Tokens: {metrics['workflow_total_tokens']}, "
                          f"Time: {metrics['execution_time']:.1f}s")

                except Exception as e:
                    print(f"      ERROR: {e}")
                    traceback.print_exc()

    save_results(all_metrics, all_states, output_dir)

    # ── Summary ──
    print(f"\n{'='*80}")
    print(f"TYPE GRANULARITY ABLATION SUMMARY")
    print(f"{'='*80}")

    header = (f"{'Condition':<14} {'#Types':>7} {'#Q':>5} {'PlanSR':>8} {'SubSR':>7} "
              f"{'Tok(k)':>8} {'Tok/Q':>8} {'Retries':>8} {'Misrt':>7}  N")
    print(header)
    print("-" * len(header))

    for condition_name in conditions:
        runs = [m for m in all_metrics if m.get("condition") == condition_name]
        if not runs:
            continue
        n = len(runs)
        avg = lambda key: sum(r.get(key, 0) for r in runs) / n

        valid_runs = [r for r in runs if r.get("plan_valid") is not None]
        plan_sr = (sum(1 for r in valid_runs if r.get("plan_valid") or r.get("plan_valid_orig"))
                   / len(valid_runs) if valid_runs else float("nan"))

        num_types = runs[0].get("num_types", "?")
        print(f"{condition_name:<14} {num_types:>7} {avg('total_questions'):>5.1f} {plan_sr:>7.1%} "
              f"{avg('success_rate'):>6.1%} {avg('workflow_total_tokens')/1000:>8.1f} "
              f"{avg('token_per_question'):>8.0f} "
              f"{avg('total_retries'):>8.1f} {avg('misroute_count'):>7.1f} {n:>3}")

    print(f"\n{'='*80}")
    print("If PlanSR is stable across 5/8/11 types → task types are auxiliary labels.")
    print("If #Q is similar → decomposer generates comparable questions regardless of type count.")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
