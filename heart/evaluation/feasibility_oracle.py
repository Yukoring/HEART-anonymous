"""
Feasibility Oracle

Deterministic ground truth for "can this robot physically manipulate this object".

Every threshold comes from the robot's URDF or its published datasheet — never
from a per-object judgement. This is what separates the oracle from the hand
written comments it replaces: previously an item was declared infeasible by
deleting it from a PDDL problem file, which made the answer key an assertion by
the same authors whose system was being scored.

A robot can grasp an item iff all three hold:

    min(dx, dy, dz) <= gripper_opening   the narrowest extent fits the jaws
    weight          <= payload           within the rated lifting capacity
    z               <= reach_height      within the arm's vertical workspace

The narrowest extent is what binds, because the approach direction is free: a
book 0.04 x 0.15 x 0.20 is grasped across its 0.04 spine, and a pair of
sunglasses 0.21 x 0.11 x 0.06 lying on a table is pinched across its 0.06
thickness from the side. Using only the horizontal footprint would reject both.

Robots without a gripper (e.g. the quadrotor) fail every grasp regardless.

Used in two places:
  1. Emitting numeric facts into PDDL problem files, so VAL derives infeasibility
     from preconditions instead of the object being absent from :objects.
  2. Producing ground truth labels to score how well HEART detects infeasibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from heart.utils.urdf_parser import parse_urdf_to_specs

PROJECT_ROOT = Path(__file__).parent.parent.parent  # HEART/

# Rated payload in kg. Not derivable from these URDFs: Fetch encodes only joint
# effort limits, and the JR2/Kinova finger joints carry inconsistent efforts
# (2 and 2000 Nm on the two fingers of the same gripper), so a torque based
# estimate would be meaningless. Published figures are used instead.
#
# Cross-check for Fetch, whose gripper is prismatic with effort=60 N per jaw:
#   m <= 2*mu*F/g = 2 * 0.5 * 60 / 9.81 = 6.1 kg, against 6.0 kg rated.
PUBLISHED_PAYLOAD_KG = {
    "fetch_gripper": 6.0,
    "jr2_kinova_gripper": 2.6,
    "quadrotor": None,
    "summit_ur5e": 5.0,   # UR5e rated payload
}

ROBOT_URDFS = {
    "fetch_gripper": "data/robots/fetch_gripper.urdf",
    "quadrotor": "data/robots/quadrotor.urdf",
    "jr2_kinova_gripper": "data/robots/jr2_kinova_gripper.urdf",
    "summit_ur5e": "data/robots/summit_ur5e.urdf",
}


@dataclass(frozen=True)
class RobotCapability:
    """Manipulation limits of one robot, as used by the oracle."""
    urdf_key: str
    has_gripper: bool
    gripper_opening: Optional[float]  # m, maximum jaw separation
    payload: Optional[float]          # kg, rated
    reach_height: Optional[float]     # m, highest graspable point above the base

    def describe(self) -> str:
        if not self.has_gripper:
            return f"{self.urdf_key}: no gripper"
        return (f"{self.urdf_key}: opening={self.gripper_opening:.3f} m, "
                f"payload={self.payload} kg, reach_height={self.reach_height:.3f} m")


_CAPABILITY_CACHE: Dict[str, RobotCapability] = {}


def get_capability(urdf_key: str) -> RobotCapability:
    """Robot limits, read once from the URDF and the published payload table."""
    if urdf_key in _CAPABILITY_CACHE:
        return _CAPABILITY_CACHE[urdf_key]

    urdf_path = ROBOT_URDFS.get(urdf_key)
    if urdf_path is None:
        raise KeyError(f"Unknown robot: {urdf_key}")

    specs = parse_urdf_to_specs(str(PROJECT_ROOT / urdf_path))
    cap = RobotCapability(
        urdf_key=urdf_key,
        has_gripper=bool(specs["gripper"]["has_gripper"]),
        gripper_opening=specs["gripper"]["max_opening"],
        payload=PUBLISHED_PAYLOAD_KG.get(urdf_key),
        reach_height=specs["arm"]["reach_height"],
    )
    _CAPABILITY_CACHE[urdf_key] = cap
    return cap


def narrow_axis(size: List[float]) -> float:
    """Smallest extent of the bounding box — the dimension the jaws must span."""
    return min(size)


def graspable(urdf_key: str, item: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Whether `item` (a scene graph entry) is graspable by `urdf_key`.

    Returns (feasible, reasons) where reasons names every violated constraint,
    empty when feasible. Constraints whose data is missing are not evaluated —
    an item with no weight is never rejected for being heavy.
    """
    cap = get_capability(urdf_key)
    if not cap.has_gripper:
        return False, ["no_gripper"]

    reasons: List[str] = []

    width = narrow_axis(item["size"])
    if cap.gripper_opening is not None and width > cap.gripper_opening:
        reasons.append(f"too_wide({width:.3f}>{cap.gripper_opening:.3f})")

    weight = item.get("weight")
    if weight is not None and cap.payload is not None and weight > cap.payload:
        reasons.append(f"too_heavy({weight}>{cap.payload})")

    height = item["location"][2]
    if cap.reach_height is not None and height > cap.reach_height:
        reasons.append(f"too_high({height:.2f}>{cap.reach_height:.2f})")

    return (not reasons), reasons


def infeasible_items(urdf_key: str, scene: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Every pickable item in `scene` that `urdf_key` cannot grasp, mapped to the
    constraints it violates. `scene` is the inner dict of a scene graph file.
    """
    out: Dict[str, List[str]] = {}
    for room in scene["rooms"].values():
        for name, item in room.get("items", {}).items():
            if "pick" not in item.get("affordance", []):
                continue
            ok, reasons = graspable(urdf_key, item)
            if not ok:
                out[name] = reasons
    return out
