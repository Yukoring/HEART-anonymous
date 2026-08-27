"""
Plan generation on the farm scenes, before anything is set up physically.

Runs LLM-CoT alone, LLM-CoT with HEART, and Triple-S over the generated seeds
and records which tomato each plan reaches for. The point is to find out whether
the scenes discriminate: if no condition ever picks an out-of-reach or oversized
tomato, the arrangement is not testing what it was built to test and should be
rebuilt before a robot is involved.

Every pick in a plan is checked against the oracle, straight from the plan text.
No PDDL conversion is involved, so a plan that would fail validation for some
unrelated reason still reports the tomato it went for.

    python -m experiments.run_farm_planners --iterations 3

Writes plans and a per-pick record under results/farm_planners_<timestamp>/.
"""

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from experiments.generate_farm_scenes import INSTRUCTION, ROBOT, SEEDS
from heart.evaluation.feasibility_oracle import get_capability, graspable
from heart.utils.urdf_parser import parse_urdf_to_specs

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
SCENE_DIR = PROJECT_ROOT / "data" / "farm" / "scenes"
PICK = re.compile(r"\b(?:pick|pick_from|pick_up|grab|harvest)\s*\(\s*([^,)]+)\s*,\s*([^,)]+)")

CONDITIONS = ["baseline_llm_cot", "heart_llm_cot", "baseline_triple_s"]


@dataclass
class FarmTask:
    """Minimal stand-in for the household Task, enough for the planners."""
    id: str
    domain: str = "farm_harvest"
    goal: str = INSTRUCTION
    position: Optional[Dict[str, List[float]]] = None
    robots: Optional[Dict[str, str]] = None


def load_scene(seed: int) -> Dict:
    path = SCENE_DIR / f"farm_seed{seed:02d}_scene_graph.json"
    with open(path) as f:
        return json.load(f)


def env_data_for(seed: int) -> Dict[str, Any]:
    specs = parse_urdf_to_specs(str(PROJECT_ROOT / "data" / "robots" / "summit_ur5e.urdf"))
    return {
        "scene_graph": load_scene(seed),
        "robots": {"robot": {"urdf": specs, "position": [0.0, 0.0, 0.0],
                             "location": [], "state": [], "capability": []}},
    }


def tomatoes_of(seed: int) -> Dict[str, Dict]:
    scene = list(load_scene(seed).values())[0]
    return {name: item
            for room in scene["rooms"].values()
            for name, item in room.get("items", {}).items()
            if "pick" in item.get("affordance", [])}


def run_condition(condition: str, seed: int, iteration: int) -> Dict[str, Any]:
    env_data = env_data_for(seed)
    task = FarmTask(id=f"farm_seed{seed:02d}", robots={"robot": ROBOT})

    if condition == "baseline_llm_cot":
        from planners.llm_cot import LLMCoTPlanner
        return LLMCoTPlanner().plan(instruction=INSTRUCTION, env_data=env_data)

    if condition == "baseline_triple_s":
        from planners.triple_s import TripleSPlanner
        return TripleSPlanner().plan(instruction=INSTRUCTION, env_data=env_data)

    if condition == "heart_llm_cot":
        from experiments._common import reset_global_instances
        from experiments.configs import EXPERIMENTS
        from heart.core.state import initialize_state
        from heart.workflows.workflow import create_workflow

        reset_global_instances()
        config = EXPERIMENTS["heart_llm_cot"]
        state = initialize_state(
            instruction=INSTRUCTION, env_data=env_data,
            agents=config["agents"], allocator_type=config["allocator_type"],
            planner_type="llm_cot", token_budget=20000, planner_config={},
        )
        workflow = create_workflow(
            agents=config["agents"], allocator_type=config["allocator_type"],
            planner_type="llm_cot",
        )
        result = workflow.invoke(state, config={"recursion_limit": 100})
        return {"plan": result.get("plan_steps") or result.get("final_plan") or [],
                "tokens_used": result.get("workflow_total_tokens", 0),
                "execution_time": result.get("execution_time", 0.0)}

    raise ValueError(f"unknown condition: {condition}")


def validate(plan: List[str], seed: int, out_dir: Path, condition: str,
             iteration: int) -> tuple:
    """
    Validate against the numeric farm PDDL, the same way the household runs are
    validated: convert the plan to PDDL with an LLM, then hand it to VAL. The
    conversion cost is measurement overhead and is not counted against any
    planner.
    """
    from heart.evaluation.plan_validator import validate_plan

    if not plan:
        return False, "no plan"
    paths = {
        "domain": str(PROJECT_ROOT / "data/pddl/domain_num/farm_harvest_domain.pddl"),
        "problem": str(PROJECT_ROOT / f"data/pddl/problem_num/farm_seed{seed:02d}_problem.pddl"),
    }
    result = validate_plan(plan_steps=plan, task_id=f"farm_seed{seed:02d}",
                           scene_name="farm", planner_type="llm_cot",
                           pddl_paths=paths)
    if result.get("pddl_plan"):
        (out_dir / "plans" /
         f"farm_seed{seed:02d}_iter{iteration}_{condition}_pddl.plan"
         ).write_text("\n".join(result["pddl_plan"]) + "\n")
    return result["valid"], result["info"][:120]


def picks_in(plan: List[str]) -> List[str]:
    """Tomato names the plan tries to pick up, in order."""
    targets = []
    for step in plan:
        match = PICK.search(step)
        if match:
            targets.append(match.group(2).strip().strip(")'\""))
    return targets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--seeds", nargs="+", type=int, default=sorted(SEEDS))
    parser.add_argument("--conditions", nargs="+", default=CONDITIONS)
    args = parser.parse_args()

    out_dir = PROJECT_ROOT / "results" / f"farm_planners_{time.strftime('%Y%m%d_%H%M%S')}"
    (out_dir / "plans").mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []

    for condition in args.conditions:
        print(f"\n=== {condition} ===")
        for seed in args.seeds:
            tomatoes = tomatoes_of(seed)
            for iteration in range(1, args.iterations + 1):
                try:
                    result = run_condition(condition, seed, iteration)
                except Exception as exc:  # noqa: BLE001 — a failed run is data
                    print(f"  seed {seed} iter {iteration}: ERROR {exc}")
                    records.append({"condition": condition, "seed": seed,
                                    "iteration": iteration, "steps": 0,
                                    "picks": "", "infeasible": "", "error": str(exc)})
                    continue

                plan = result.get("plan", [])
                (out_dir / "plans" / f"farm_seed{seed:02d}_iter{iteration}_{condition}.plan"
                 ).write_text("\n".join(plan) + "\n")

                targets = picks_in(plan)
                bad = [t for t in targets
                       if t in tomatoes and not graspable(ROBOT, tomatoes[t])[0]]

                # Same protocol as the household runs: convert to PDDL, then VAL.
                valid, info = validate(plan, seed, out_dir, condition, iteration)

                records.append({
                    "condition": condition, "seed": seed, "iteration": iteration,
                    "steps": len(plan), "picks": "|".join(targets),
                    "infeasible": "|".join(bad), "valid": valid, "info": info,
                    "error": "",
                })
                flag = f"  <-- {', '.join(bad)}" if bad else ""
                print(f"  seed {seed} iter {iteration}: {len(plan):2} steps, "
                      f"{len(targets)} picks, {len(bad)} infeasible, "
                      f"valid={valid}{flag}")

    with open(out_dir / "picks.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"\n{'condition':22} {'runs':>5} {'picks':>7} {'infeasible picks':>17} "
          f"{'runs w/ any':>12}")
    for condition in args.conditions:
        rows = [r for r in records if r["condition"] == condition and not r["error"]]
        if not rows:
            continue
        picks = sum(len(r["picks"].split("|")) if r["picks"] else 0 for r in rows)
        bad = sum(len(r["infeasible"].split("|")) if r["infeasible"] else 0 for r in rows)
        runs_bad = sum(1 for r in rows if r["infeasible"])
        print(f"{condition:22} {len(rows):5} {picks:7} {bad:9} ({bad/max(picks,1):5.1%}) "
              f"{runs_bad:6} ({runs_bad/len(rows):5.1%})")

    reasons = Counter()
    for r in records:
        for name in filter(None, r["infeasible"].split("|")):
            reasons[(r["condition"], name)] += 1
    if reasons:
        print("\n무엇을 잘못 집었나")
        for (condition, name), count in reasons.most_common():
            print(f"  {condition:22} {name:12} x{count}")
    else:
        print("\n어떤 조건도 불가능한 토마토를 집지 않음 — 씬이 변별력이 없음")

    print(f"\n-> {out_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
