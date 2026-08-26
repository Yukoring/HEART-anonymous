"""
Infeasibility detection rates from the re-scored plans.

Reports, per scene and planner, how often a produced plan attempts an action the
robot physically cannot perform. A trial is the unit, matching Table IV, and
DELTA's decomposed and undecomposed plans are folded together the way PlanSR
already folds them.

The denominator is trials that produced a plan. A trial where the planner
emitted nothing cannot attempt an infeasible action, so counting it as "no
violation" would credit the weakest baselines for failing earlier. The counts
are printed alongside so the coverage is visible.

VAL stops at the first unsatisfied precondition, so a plan failing earlier for
another reason may also contain an infeasible action further along. Every rate
here is therefore a lower bound. The last column makes the largest part of that
gap visible: a plan naming an action or object the domain does not define is
rejected before execution begins, so none of its preconditions are ever
evaluated and any physical violation inside it is invisible.

    python -m experiments.report_infeasibility
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from heart.configs.tasks import ABBR_TO_SCENE, SCENE_TASKS, get_scene_graph_path, get_scene_robots
from heart.evaluation.feasibility_oracle import get_capability, graspable

PROJECT_ROOT = Path(__file__).parent.parent
PICK = re.compile(r"\(pick\s+(\S+)\s+(\S+)")
PHYSICAL = re.compile(r"Satisfy \(item_(weight|width|height)\)?")
PARSE_LEVEL = re.compile(r"undefined_object\(|malformed_plan")
SCENES = {"bw": "Beechwood", "bn": "Benevolence", "mr": "Merom"}


def planner_family(planner: str) -> str:
    return "DELTA" if planner.startswith("delta") else "LLM-CoT"


def scene_items(abbr: str) -> dict:
    with open(PROJECT_ROOT / get_scene_graph_path(ABBR_TO_SCENE[abbr])) as f:
        scene = list(json.load(f).values())[0]
    return {name: item
            for room in scene["rooms"].values()
            for name, item in room.get("items", {}).items()}


def manipulator_for(abbr: str, task_id: str) -> str:
    """The arm-equipped robot of a task, whose limits the oracle applies."""
    scene_name = ABBR_TO_SCENE[abbr]
    task = next(t for t in SCENE_TASKS[scene_name] if t.id == task_id)
    robots = get_scene_robots(scene_name, task=task)
    return next(c["urdf"] for c in robots.values()
                if get_capability(c["urdf"]).has_gripper)


def attempts_infeasible_grasp(plan_path: Path, abbr: str, task_id: str,
                              items: dict) -> bool:
    """
    Whether the plan text picks up an object the oracle rules out.

    Read straight from the plan rather than from VAL, so it still counts for a
    plan VAL rejected before reaching the action — a malformed step earlier in
    the plan hides everything after it.
    """
    urdf_key = manipulator_for(abbr, task_id)
    for _, target in PICK.findall(plan_path.read_text()):
        item = items.get(target.rstrip(")"))
        if item is not None and not graspable(urdf_key, item)[0]:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-root", default="../exp")
    args = parser.parse_args()
    exp_root = Path(args.exp_root)

    trials = defaultdict(lambda: {"valid": False, "physical": False,
                                  "unevaluated": True, "attempts": False})
    constraint_counts = defaultdict(lambda: defaultdict(int))
    missing = []

    for abbr, scene in SCENES.items():
        path = PROJECT_ROOT / f"results/rescore_numeric_{abbr}.csv"
        if not path.is_file():
            missing.append(abbr)
            continue
        items = scene_items(abbr)
        for row in csv.DictReader(open(path)):
            # Only the planner comparison uses the baseline/HEART split.
            if row["source"] not in (f"task_{abbr}",):
                continue
            condition = "HEART" if row["condition"].startswith("heart") else "baseline"
            key = (scene, planner_family(row["planner"]), condition,
                   row["task_id"], row["iteration"])
            trial = trials[key]
            trial["valid"] |= row["valid_num"] == "True"
            reason = row["reason_num"]
            if not PARSE_LEVEL.match(reason):
                trial["unevaluated"] = False
            match = PHYSICAL.search(reason)
            if match:
                trial["physical"] = True
                constraint_counts[scene][match.group(1)] += 1
            plan_path = exp_root / row["file"]
            if plan_path.is_file():
                trial["attempts"] |= attempts_infeasible_grasp(
                    plan_path, abbr, row["task_id"], items)

    if missing:
        print(f"missing re-score output for: {', '.join(missing)}\n")
    if not trials:
        print("no re-scored plans found")
        return 1

    grouped = defaultdict(list)
    for (scene, planner, condition, _, _), trial in trials.items():
        grouped[(scene, planner, condition)].append(trial)

    print("Infeasible-action rate, trials that produced a plan")
    print(f"{'scene':12} {'planner':9} {'config':9} {'trials':>7} {'valid':>14} "
          f"{'VAL rejected':>15} {'plan text':>14} {'never evaluated':>17}")
    for scene in SCENES.values():
        for planner in ("LLM-CoT", "DELTA"):
            for condition in ("baseline", "HEART"):
                group = grouped.get((scene, planner, condition))
                if not group:
                    continue
                n = len(group)
                valid = sum(t["valid"] for t in group)
                physical = sum(t["physical"] for t in group)
                attempts = sum(t["attempts"] for t in group)
                blind = sum(t["unevaluated"] for t in group)
                print(f"{scene:12} {planner:9} {condition:9} {n:7} "
                      f"{valid:6} ({valid/n:5.1%}) {physical:5} ({physical/n:5.1%})"
                      f" {attempts:4} ({attempts/n:5.1%}) {blind:7} ({blind/n:5.1%})")
        print()

    print("Violated constraint, by scene")
    for scene, counts in constraint_counts.items():
        total = sum(counts.values())
        detail = "  ".join(f"{k} {v}" for k, v in sorted(counts.items()))
        print(f"  {scene:12} {total:4}   {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
