"""
Numeric PDDL generation.

Rewrites the hand authored domain and problem files into a validation-only pair
where physical infeasibility follows from preconditions instead of from an
object being missing.

The originals stay untouched. DELTA plans with them through Fast Downward,
which has no numeric fluent support, and the saved plan files were produced
against them. Only VAL ever sees the numeric variant.

Domain: `:fluents` is added to the requirements, six functions are declared, and
`pick` gains three comparisons. Action names and arities are left alone so the
7,371 already saved `.plan` files remain valid inputs.

Problem: every object a sibling-bearing category deliberately dropped is put
back into `:objects` and `:init`, and each item and agent gets its measured
values. An item whose scene graph entry carries no mass is emitted as 0.0, so
the weight constraint stays inactive where there is no measurement to apply.

    python -m experiments.generate_numeric_pddl bn

Outputs to data/pddl/domain_num/ and data/pddl/problem_num/.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from heart.configs.tasks import (
    ABBR_TO_SCENE,
    SCENE_TASKS,
    get_pddl_domain_path,
    get_pddl_problem_path,
    get_scene_graph_path,
    get_scene_robots,
)
from heart.evaluation.feasibility_oracle import get_capability, graspable, narrow_axis

PROJECT_ROOT = Path(__file__).parent.parent
DOMAIN_OUT = PROJECT_ROOT / "data" / "pddl" / "domain_num"
PROBLEM_OUT = PROJECT_ROOT / "data" / "pddl" / "problem_num"

FUNCTIONS_BLOCK = """
    (:functions
        (item_weight ?i - item)     ; kg
        (item_width ?i - item)      ; m, narrowest extent of the bounding box
        (item_height ?i - item)     ; m, above the floor
        (agent_payload ?a - agent)  ; kg, rated
        (agent_gripper ?a - agent)  ; m, maximum jaw separation
        (agent_reach ?a - agent)    ; m, highest graspable point
    )
"""

PICK_NUMERIC = """            (<= (item_weight ?i) (agent_payload ?a))
            (<= (item_width ?i) (agent_gripper ?a))
            (<= (item_height ?i) (agent_reach ?a))"""


def load_scene(scene_name: str) -> Dict:
    with open(PROJECT_ROOT / get_scene_graph_path(scene_name)) as f:
        return list(json.load(f).values())[0]


def item_index(scene: Dict) -> Dict[str, Tuple[str, Dict]]:
    """Every item in the scene, mapped to (room name, item entry)."""
    out = {}
    for room_name, room in scene["rooms"].items():
        for name, item in room.get("items", {}).items():
            out[name] = (room_name, item)
    return out


def category(name: str) -> str:
    return re.sub(r"_\d+$", "", name)


def mask_comments(text: str) -> str:
    """Blank out comment bodies, keeping every character offset intact."""
    out = []
    for line in text.split("\n"):
        idx = line.find(";")
        out.append(line if idx < 0 else line[:idx] + " " * (len(line) - idx))
    return "\n".join(out)


def parse_objects(text: str) -> Tuple[str, Set[str]]:
    """The `:objects` block verbatim, plus every name declared in it."""
    match = re.search(r"\(:objects(.*?)\n\s*\)", text, re.S)
    if not match:
        return "", set()
    body = match.group(1)
    names = set()
    for line in body.splitlines():
        line = line.split(";")[0]
        names.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", line.split("-")[0]))
    return match.group(0), names


def agents_in(text: str) -> List[str]:
    """Agent names declared in `:objects` (drones are excluded — they cannot grasp)."""
    out = []
    for line in text.splitlines():
        line = line.split(";")[0]
        if re.search(r"-\s*agent\b", line):
            out.extend(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", line.split("-")[0]))
    return out


def convert_domain(text: str) -> str:
    """Add numeric functions and the three grasp comparisons to `pick`."""
    if "(:functions" in text:
        raise ValueError("domain already numeric")

    # The domains carry either `:strips :typing` or `:strips :typing :adl`.
    text, n = re.subn(r"\(:requirements([^)]*)\)",
                      lambda m: f"(:requirements{m.group(1)} :fluents)", text, count=1)
    if n != 1:
        raise ValueError("no :requirements to extend")

    # Functions go after the predicate block, which ends the line before the
    # first action.
    text = re.sub(r"\n(\s*\(:action)", FUNCTIONS_BLOCK + r"\n\1", text, count=1)

    # Extend pick's precondition. The last paren before `:effect` closes the
    # `and`, so the comparisons go in front of it.
    def extend(match: re.Match) -> str:
        body = match.group(0)
        idx = body.rindex(")")
        return body[:idx] + "\n" + PICK_NUMERIC + ")" + body[idx + 1:]

    text, n = re.subn(r"(?<=:action pick\n)(.*?):effect", extend, text, count=1, flags=re.S)
    if n != 1:
        raise ValueError("could not extend pick precondition")
    return text


def convert_problem(text: str, task_id: str, robot_urdfs: Dict[str, str],
                    items: Dict[str, Tuple[str, Dict]]) -> Tuple[str, List[str]]:
    """Restore deliberately excluded siblings and append measured values."""
    objects_block, declared = parse_objects(text)
    agents = agents_in(objects_block)
    # Multi-robot scenes declare one agent per robot; each gets its own limits.
    # A drone is typed `- drone` and so never appears here.
    fallback = next(k for k in robot_urdfs.values() if get_capability(k).has_gripper)
    caps = {a: get_capability(robot_urdfs.get(a, fallback)) for a in agents}
    # The grasp thresholds in the problem must match the tightest robot that can
    # be bound to `pick`, which is per-agent, so no single `cap` is used below.

    by_category = defaultdict(list)
    for name in items:
        if "pick" in items[name][1].get("affordance", []):
            by_category[category(name)].append(name)

    # An absent sibling is only a deliberate exclusion when the robot genuinely
    # cannot handle it. Merom omits reachable items too — those are simply not
    # part of the task, and restoring them would assert an exclusion that the
    # answer key never made.
    # Only the arm-equipped robots decide this. A drone fails every grasp by
    # definition, so including it would mark every absent item as excluded.
    manipulators = {k for k in robot_urdfs.values() if get_capability(k).has_gripper}
    restored = []
    for siblings in by_category.values():
        present = [s for s in siblings if s in declared]
        if not present:
            continue
        for name in siblings:
            if name in declared:
                continue
            if any(not graspable(k, items[name][1])[0] for k in manipulators):
                restored.append(name)

    if restored:
        # Same line as the other items, so the file keeps its shape.
        item_line = re.search(r"\n(\s*)([^\n]*?)\s+-\s+item\n", objects_block)
        indent, existing = item_line.group(1), item_line.group(2)
        new_block = objects_block.replace(
            f"{indent}{existing} - item\n",
            f"{indent}{existing} {' '.join(restored)} - item\n")
        text = text.replace(objects_block, new_block)
        declared.update(restored)

    lines = ["", "        ; Restored objects — infeasibility is derived, not assumed"]
    for name in restored:
        room, _ = items[name]
        lines.append(f"        (item_at {name} {room}) (item_pickable {name}) (item_accessible {name})")

    lines.append("")
    lines.append("        ; Measured values (scene graph); weight 0.0 where unmeasured")
    for name in sorted(declared):
        if name not in items:
            continue
        _, item = items[name]
        weight = item.get("weight") or 0.0
        lines.append(f"        (= (item_weight {name}) {weight})"
                     f" (= (item_width {name}) {narrow_axis(item['size']):.3f})"
                     f" (= (item_height {name}) {item['location'][2]:.3f})")

    lines.append("")
    lines.append("        ; Robot limits (URDF and published payload)")
    for agent in agents:
        cap = caps[agent]
        lines.append(f"        (= (agent_payload {agent}) {cap.payload})"
                     f" (= (agent_gripper {agent}) {cap.gripper_opening:.3f})"
                     f" (= (agent_reach {agent}) {cap.reach_height:.3f})"
                     f"  ; {cap.urdf_key}")

    # Append to :init, whose closing paren is the last one before :goal. The
    # search runs over a comment-masked copy at identical offsets, because the
    # comments themselves contain parens ("put one notebook (either 64 or 54)").
    masked = mask_comments(text)
    goal_at = masked.index("(:goal")
    init_close = masked.rindex(")", 0, goal_at)
    lines.append("    ")
    text = text[:init_close] + "\n".join(lines) + text[init_close:]
    return text, restored


def main(abbr: str) -> int:
    scene_name = ABBR_TO_SCENE[abbr]
    scene = load_scene(scene_name)
    items = item_index(scene)

    DOMAIN_OUT.mkdir(parents=True, exist_ok=True)
    PROBLEM_OUT.mkdir(parents=True, exist_ok=True)

    converted = skipped = 0
    for task in SCENE_TASKS[scene_name]:
        domain_path = PROJECT_ROOT / get_pddl_domain_path(task.id)
        problem_path = PROJECT_ROOT / get_pddl_problem_path(scene_name, task.id)
        if not domain_path.is_file() or not problem_path.is_file():
            continue

        domain_text = domain_path.read_text()
        if ":action pick" not in domain_text:
            print(f"  {task.id:7} skipped — no pick action")
            skipped += 1
            continue

        robots = get_scene_robots(scene_name, task=task)
        robot_urdfs = {name: cfg["urdf"] for name, cfg in robots.items()}
        if not any(get_capability(k).has_gripper for k in robot_urdfs.values()):
            print(f"  {task.id:7} skipped — no robot with a gripper")
            skipped += 1
            continue

        problem_text, restored = convert_problem(
            problem_path.read_text(), task.id, robot_urdfs, items)
        urdf_key = "/".join(sorted({k for k in robot_urdfs.values()
                                    if get_capability(k).has_gripper}))

        (DOMAIN_OUT / domain_path.name).write_text(convert_domain(domain_text))
        (PROBLEM_OUT / problem_path.name).write_text(problem_text)

        note = f"restored {', '.join(restored)}" if restored else "no exclusions"
        print(f"  {task.id:7} {urdf_key:20} {note}")
        converted += 1

    print(f"\n{converted} converted, {skipped} skipped")
    print(f"  domains  -> {DOMAIN_OUT.relative_to(PROJECT_ROOT)}")
    print(f"  problems -> {PROBLEM_OUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "bn"))
