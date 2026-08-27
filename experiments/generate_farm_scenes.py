"""
Farm harvest scenes for the real-robot evaluation.

One instruction, five scene configurations. Holding the task fixed and varying
only the physical arrangement means any difference between conditions is
attributable to physical and logical reasoning rather than to task semantics,
and running every condition on the same scene makes the comparison paired.

Each tomato carries two independent labels:

  ripeness   ripe / unripe / rotten      -> what should be done with it
  reachable  ok / too_high / too_wide    -> whether it can be done at all

The discriminating cases are the ones where those disagree. A ripe tomato out
of reach must be left alone even though the instruction asks for ripe fruit,
and a rotten one out of reach cannot be discarded because it cannot be picked
up in the first place. A planner that reasons about only one of the two labels
fails on those.

The seeds are a designed sweep rather than a random draw: at this size a
random draw leaves cells of the matrix empty. Coverage is asserted at the end of the run.

Heights and widths are placed clear of the robot's limits — reachable at or
below 1.30 m against a 1.71 m ceiling, out of reach at or above 1.85 m — so
that no verdict depends on which reach model is used.

    python -m experiments.generate_farm_scenes

Writes scene graphs, numeric PDDL problems, and a placement sheet per seed.
"""

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from heart.evaluation.feasibility_oracle import get_capability, graspable

PROJECT_ROOT = Path(__file__).parent.parent
SCENE_OUT = PROJECT_ROOT / "data" / "farm" / "scenes"
PROBLEM_OUT = PROJECT_ROOT / "data" / "pddl" / "problem_num"
SHEET_OUT = PROJECT_ROOT / "data" / "farm" / "placement"

ROBOT = "summit_ur5e"
INSTRUCTION = ("Harvest all the ripe tomatoes and load them onto the robot, "
               "discard any rotten ones, then return to the dock.")

# Bands chosen to clear the robot's limits from both sides.
REACHABLE_Z = (0.45, 1.25)
OUT_OF_REACH_Z = (1.85, 2.05)
NORMAL_W = (0.055, 0.075)
OVERSIZE_W = (0.14, 0.17)
WEIGHT = (0.10, 0.25)          # kg — never near the 5 kg payload

# (ripeness, physical) per tomato. "ok" means the oracle can grasp it.
#
# Five scenes rather than ten, each densely loaded. Physically rebuilding a
# scene is the expensive step, so diversity is bought within a scene instead of
# across scenes: every one carries eight or nine tomatoes spanning the whole
# ripeness x reachability matrix. Five scenes still leaves the method
# comparison five independent units, where three would leave it three.
# Ordered by difficulty. The first scene is close to the simplest thing that
# still tests anything — two tomatoes to collect, one to throw away, one out of
# reach — and the last carries four traps at once. A gradient is worth more than
# five scenes of the same weight: if every condition fails the hard scenes and
# passes the easy ones, that is a result, whereas five uniformly hard scenes
# only say everything failed.
SEEDS: Dict[int, Tuple[int, List[Tuple[str, str]]]] = {
    1: (2, [("ripe","ok"),("ripe","ok"),("ripe","too_high"),("rotten","ok")]),
    2: (2, [("ripe","ok"),("ripe","ok"),("ripe","too_wide"),("rotten","ok"),
            ("unripe","ok")]),
    3: (2, [("ripe","ok"),("ripe","ok"),("ripe","ok"),("ripe","too_high"),
            ("rotten","ok"),("rotten","too_high")]),
    4: (2, [("ripe","ok"),("ripe","ok"),("ripe","ok"),("ripe","too_high"),
            ("ripe","too_wide"),("rotten","ok"),("unripe","too_high")]),
    5: (2, [("ripe","ok"),("ripe","ok"),("ripe","ok"),("ripe","too_high"),
            ("ripe","too_high"),("ripe","too_wide"),("rotten","ok"),("unripe","ok")]),
}

# Only one oversized tomato can be built, and the scenes are run one at a time,
# so no scene may call for more than one at once.
MAX_OVERSIZE_PER_SCENE = 1

# The oversized model is built to look ripe, so it cannot stand in for a rotten
# tomato. Rotten fruit that cannot be handled is therefore only represented by
# height, not by width.
OVERSIZE_RIPENESS = "ripe"

# The rig has two stems and holds at most four tomatoes on each.
MAX_STEMS = 2
MAX_PER_STEM = 4


@dataclass
class Tomato:
    name: str
    stem: str
    ripeness: str
    physical: str
    height: float
    width: float
    weight: float

    @property
    def expected(self) -> str:
        if self.physical != "ok":
            return "skip (out of reach)" if self.physical == "too_high" else "skip (too wide)"
        return {"ripe": "collect", "rotten": "discard", "unripe": "leave"}[self.ripeness]


def build(seed: int) -> Tuple[List[Tomato], List[str]]:
    stem_count, composition = SEEDS[seed]
    if stem_count > MAX_STEMS or len(composition) > stem_count * MAX_PER_STEM:
        raise ValueError(
            f"seed {seed}: {len(composition)} tomatoes on {stem_count} stems exceeds "
            f"the rig ({MAX_STEMS} stems, {MAX_PER_STEM} each)")
    oversize = [ripeness for ripeness, physical in composition if physical == "too_wide"]
    if len(oversize) > MAX_OVERSIZE_PER_SCENE:
        raise ValueError(
            f"seed {seed}: needs {len(oversize)} oversized tomatoes at once, only "
            f"{MAX_OVERSIZE_PER_SCENE} can be built")
    wrong = [r for r in oversize if r != OVERSIZE_RIPENESS]
    if wrong:
        raise ValueError(
            f"seed {seed}: oversized tomato marked {wrong[0]}, but the model "
            f"that exists looks {OVERSIZE_RIPENESS}")
    rng = random.Random(seed)
    stems = [f"stem_{i+1:02d}_0" for i in range(stem_count)]

    # Spread the composition over the stems so no stem is all one kind.
    order = list(composition)
    rng.shuffle(order)

    tomatoes = []
    for index, (ripeness, physical) in enumerate(order):
        stem = stems[index % stem_count]
        if physical == "too_high":
            height = round(rng.uniform(*OUT_OF_REACH_Z), 3)
        else:
            height = round(rng.uniform(*REACHABLE_Z), 3)
        width = round(rng.uniform(*(OVERSIZE_W if physical == "too_wide" else NORMAL_W)), 3)
        tomatoes.append(Tomato(
            name=f"tomato_{index+1:02d}", stem=stem, ripeness=ripeness,
            physical=physical, height=height, width=width,
            weight=round(rng.uniform(*WEIGHT), 3)))
    return tomatoes, stems


def scene_graph(seed: int, tomatoes: List[Tomato], stems: List[str]) -> Dict:
    rooms: Dict[str, Dict] = {
        "dock_0": {"location": [0.0, 0.0, 0.0], "size": [2.0, 2.0, 2.5],
                   "neighbor": ["door_0"] + stems,
                   "items": {"dock_station_01": {"location": [0.0, 0.0, 0.15],
                                                 "size": [0.6, 0.6, 0.3],
                                                 "affordance": ["place_on"]}}},
        "door_0": {"location": [0.0, 2.0, 0.0], "size": [1.0, 0.2, 2.2],
                   "neighbor": ["dock_0"] + stems,
                   "items": {"door_01": {"location": [0.0, 2.0, 1.0],
                                         "size": [0.05, 0.9, 2.0],
                                         "affordance": ["open", "close"]}}},
    }
    for i, stem in enumerate(stems):
        y = 3.0 + 1.5 * i
        rooms[stem] = {
            "location": [0.0, y, 0.0], "size": [1.5, 1.2, 2.5],
            "neighbor": ["dock_0", "door_0"] + [s for s in stems if s != stem],
            "items": {stem.replace("_0", "").replace("stem_", "stem_"):
                      {"location": [0.0, y, 1.05], "size": [0.05, 0.05, 2.10],
                       "affordance": []}},
        }
    for t in tomatoes:
        y = rooms[t.stem]["location"][1]
        rooms[t.stem]["items"][t.name] = {
            "location": [round(0.10 + 0.05 * len(rooms[t.stem]["items"]), 3), y, t.height],
            "size": [t.width, t.width, round(t.width * 0.95, 3)],
            "weight": t.weight,
            "affordance": ["pick"],
            "state": [t.ripeness],
        }
    return {f"Farm_Seed_{seed:02d}": {
        "metadata": {"function": "farm", "floors": 1, "floor_area": 12.0,
                     "gibson_split": None, "seed": seed},
        "rooms": rooms}}


def problem_pddl(seed: int, tomatoes: List[Tomato], stems: List[str],
                 goals: Dict[str, List[str]]) -> str:
    cap = get_capability(ROBOT)
    rooms = ["dock_0", "door_0"] + stems
    names = " ".join(t.name for t in tomatoes)

    init = [f"        (agent_at robot dock_0)", "", "        (room_is_dock dock_0)", ""]
    for a in rooms:
        for b in rooms:
            if a != b:
                init.append(f"        (neighbor {a} {b})")
    init.append("")
    for t in tomatoes:
        init.append(f"        (item_at {t.name} {t.stem}) (item_pickable {t.name})"
                    f" (item_{t.ripeness} {t.name})")
        init.append(f"        (= (item_height {t.name}) {t.height})"
                    f" (= (item_width {t.name}) {t.width})")
    init += ["", f"        ; {ROBOT} limits, from the URDF and the rated payload",
             f"        (= (agent_reach robot) {cap.reach_height:.3f})"
             f" (= (agent_gripper robot) {cap.gripper_opening:.4f})"]

    goal_lines = [f"        (item_collected {n})" for n in goals["collect"]]
    goal_lines += [f"        (item_discarded {n})" for n in goals["discard"]]
    goal_lines.append("        (agent_at robot dock_0)")

    return f"""(define (problem farm_harvest_seed{seed:02d})
    (:domain farm_harvest)

    ; Goal derived from the oracle, not hand-written: every ripe tomato the
    ; robot can actually grasp is collected, every rotten one it can grasp is
    ; discarded, and the rest are left where they are.
    (:objects
        robot - agent
        {' '.join(rooms)} - room
        {names} - item
    )

    (:init
{chr(10).join(init)}
    )

    (:goal (and
{chr(10).join(goal_lines)}
    ))
)
"""


def placement_sheet(seed: int, tomatoes: List[Tomato], stems: List[str]) -> str:
    cap = get_capability(ROBOT)
    rows = "\n".join(
        f"| {t.name} | {t.stem} | {t.height:.2f} | {t.width:.3f} | {t.ripeness} | "
        f"{'—' if t.physical == 'ok' else t.physical} | {t.expected} |"
        for t in sorted(tomatoes, key=lambda x: (x.stem, x.name)))
    return f"""# Farm seed {seed:02d} — placement sheet

Instruction (identical for every seed and condition):

> {INSTRUCTION}

Robot: Summit XL + UR5e — reach {cap.reach_height:.2f} m, gripper opens to
{cap.gripper_opening:.4f} m, rated payload {cap.payload} kg.

Heights are measured from the ground to the fruit. Anything at or above 1.85 m
is beyond the arm; anything at or below 1.30 m is comfortably within it. Nothing
is placed in between, so the setup does not depend on where exactly the limit
falls.

| tomato | stem | height (m) | width (m) | ripeness | violates | expected |
|---|---|---|---|---|---|---|
{rows}

Stems: {', '.join(stems)}
"""


def main() -> int:
    for directory in (SCENE_OUT, PROBLEM_OUT, SHEET_OUT):
        directory.mkdir(parents=True, exist_ok=True)

    coverage = {"ripe/ok": 0, "ripe/blocked": 0, "rotten/ok": 0,
                "rotten/blocked": 0, "unripe/ok": 0, "unripe/blocked": 0,
                "too_high": 0, "too_wide": 0}
    print(f"{'seed':>4} {'stems':>6} {'tomatoes':>9} {'collect':>8} {'discard':>8} {'skip':>5}")

    for seed in sorted(SEEDS):
        tomatoes, stems = build(seed)
        scene = scene_graph(seed, tomatoes, stems)

        # Verify the intended labels against the oracle rather than trusting them.
        items = {n: i for r in scene[f"Farm_Seed_{seed:02d}"]["rooms"].values()
                 for n, i in r.get("items", {}).items()}
        goals = {"collect": [], "discard": []}
        for t in tomatoes:
            feasible = graspable(ROBOT, items[t.name])[0]
            if feasible != (t.physical == "ok"):
                raise AssertionError(
                    f"seed {seed}: {t.name} intended {t.physical} but oracle says "
                    f"{'graspable' if feasible else 'not graspable'}")
            if feasible and t.ripeness == "ripe":
                goals["collect"].append(t.name)
            elif feasible and t.ripeness == "rotten":
                goals["discard"].append(t.name)

            key = f"{t.ripeness}/{'ok' if t.physical == 'ok' else 'blocked'}"
            coverage[key] += 1
            if t.physical != "ok":
                coverage[t.physical] += 1

        (SCENE_OUT / f"farm_seed{seed:02d}_scene_graph.json").write_text(
            json.dumps(scene, indent=2) + "\n")
        (PROBLEM_OUT / f"farm_seed{seed:02d}_problem.pddl").write_text(
            problem_pddl(seed, tomatoes, stems, goals))
        (SHEET_OUT / f"farm_seed{seed:02d}.md").write_text(
            placement_sheet(seed, tomatoes, stems))

        skipped = len(tomatoes) - len(goals["collect"]) - len(goals["discard"])
        print(f"{seed:4} {len(stems):6} {len(tomatoes):9} "
              f"{len(goals['collect']):8} {len(goals['discard']):8} {skipped:5}")

    print("\nCoverage across the seeds")
    for key, count in coverage.items():
        print(f"  {key:16} {count}")
    missing = [k for k, v in coverage.items() if v == 0]
    if missing:
        print(f"\nUNCOVERED: {', '.join(missing)}")
        return 1
    print(f"\nscenes   -> {SCENE_OUT.relative_to(PROJECT_ROOT)}")
    print(f"problems -> {PROBLEM_OUT.relative_to(PROJECT_ROOT)}")
    print(f"sheets   -> {SHEET_OUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
