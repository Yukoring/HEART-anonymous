"""
Oracle calibration against the hand authored PDDL answer key.

The ground truth problem files encode physical infeasibility by omission: an
object the robot cannot handle is simply left out of `:objects`, sometimes with
a comment explaining why. This script recovers those implicit judgements and
checks them against heart.evaluation.feasibility_oracle.

An omitted item only counts as a deliberate exclusion when a sibling of the same
category is present — `bowl_55` absent while `bowl_63` is present is a choice,
whereas an item no task ever mentions is simply irrelevant.

Disagreements are the point of the script. Each one is either a threshold that
does not match the robot's specification, or a mistake in the answer key.

    python -m experiments.calibrate_oracle
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from heart.configs.tasks import (
    SCENE_TASKS,
    get_pddl_problem_path,
    get_scene_graph_path,
    get_scene_robots,
)
from heart.evaluation.feasibility_oracle import get_capability, graspable

PROJECT_ROOT = Path(__file__).parent.parent


def load_scene(scene_name: str) -> Dict:
    with open(PROJECT_ROOT / get_scene_graph_path(scene_name)) as f:
        return list(json.load(f).values())[0]


def scene_pickables(scene: Dict) -> Dict[str, Dict]:
    out = {}
    for room in scene["rooms"].values():
        for name, item in room.get("items", {}).items():
            if "pick" in item.get("affordance", []):
                out[name] = item
    return out


def problem_objects(path: Path) -> Tuple[set, List[str]]:
    """Object names declared in `:objects`, plus the file's leading comments."""
    text = path.read_text()
    comments = [line.strip().lstrip(";").strip()
                for line in text.splitlines()[:8] if line.strip().startswith(";")]

    match = re.search(r"\(:objects(.*?)\)\s*\(:init", text, re.S)
    if not match:
        return set(), comments

    names = set()
    for line in match.group(1).splitlines():
        line = line.split(";")[0]
        names.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", line.split("-")[0]))
    return names, comments


def category(name: str) -> str:
    """`bowl_55` -> `bowl`, so siblings of one kind can be grouped."""
    return re.sub(r"_\d+$", "", name)


def main() -> int:
    agree = disagree = 0
    rows: List[Tuple] = []

    for scene_name, tasks in SCENE_TASKS.items():
        scene = load_scene(scene_name)
        pickables = scene_pickables(scene)
        by_category = defaultdict(list)
        for name in pickables:
            by_category[category(name)].append(name)

        for task in tasks:
            problem_path = PROJECT_ROOT / get_pddl_problem_path(scene_name, task.id)
            if not problem_path.is_file():
                continue

            declared, comments = problem_objects(problem_path)

            robots = get_scene_robots(scene_name, task=task)
            # Manipulation is judged against the arm-equipped robot of the task.
            urdf_key = next(
                (cfg["urdf"] for cfg in robots.values()
                 if get_capability(cfg["urdf"]).has_gripper),
                None,
            )
            if urdf_key is None:
                continue

            for cat, siblings in by_category.items():
                present = [s for s in siblings if s in declared]
                absent = [s for s in siblings if s not in declared]
                # Only a category the task actually uses reveals a choice.
                if not present or not absent:
                    continue

                for name in absent:
                    ok, reasons = graspable(urdf_key, pickables[name])
                    # The answer key says infeasible; the oracle should agree.
                    if ok:
                        disagree += 1
                        rows.append(("MISS", task.id, urdf_key, name, "-", comments))
                    else:
                        agree += 1
                for name in present:
                    ok, reasons = graspable(urdf_key, pickables[name])
                    # The answer key says feasible; the oracle must not reject it.
                    if not ok:
                        disagree += 1
                        rows.append(("FALSE+", task.id, urdf_key, name,
                                     ",".join(reasons), comments))
                    else:
                        agree += 1

    print("Robot capabilities")
    for key in ("fetch_gripper", "jr2_kinova_gripper", "quadrotor"):
        print("  " + get_capability(key).describe())

    print(f"\nAnswer key agreement: {agree}/{agree + disagree}")
    if rows:
        print("\nDisagreements")
        print(f"  {'kind':7} {'task':7} {'robot':20} {'item':20} reason")
        for kind, task_id, urdf_key, name, reason, comments in rows:
            print(f"  {kind:7} {task_id:7} {urdf_key:20} {name:20} {reason}")
            for c in comments:
                print(f"          key: {c}")
    return 0 if not rows else 1


if __name__ == "__main__":
    sys.exit(main())
