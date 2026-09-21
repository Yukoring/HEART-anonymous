"""
Robot descriptions for HEART, built from a URDF, by hand, or both.

The pipeline reads each robot as an entry of `env_data["robots"]`: the parsed
URDF specs plus its pose and state. Building that entry by hand means knowing
the parser's output layout and the fields the agents read. `RobotSpec` builds
it instead, and covers three cases the parser alone does not:

  * A figure the URDF does not carry. Rated payload is the usual one: URDFs
    give joint torques, not a mass the arm is rated to lift, so the parser
    reports None and the feasibility agent has nothing to compare a weight
    against. Pass it as `payload_kg`.

  * More than one arm. The parser measures the workspace of the single longest
    kinematic chain, which on a two-armed body is whichever arm happened to be
    found first. `from_urdf` measures each arm named left or right on its own,
    and `arms=` sets or corrects any figure per arm, so the agents can reason
    about which arm reaches an object rather than whether "the robot" does.

  * Several identical robots. `at()` copies a spec with a new pose, so a team
    of three is parsed once.

A single-armed robot built with no overrides produces exactly the entry the
experiments have always used, so results reproduce unchanged.

    from heart.robot_spec import RobotSpec

    fetch = RobotSpec.from_urdf("data/robots/fetch_gripper.urdf", payload_kg=6.0)
    h1 = RobotSpec.from_urdf("h1.urdf", payload_kg=3.0,
                             arms={"left": {"gripper_opening": 0.09},
                                   "right": {"gripper_opening": 0.09}})
    team = {f"drone_{i}": drone.at(position=p) for i, p in enumerate(starts)}
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from heart.utils.urdf_parser import arm_workspaces, parse_urdf_to_specs


@dataclass
class ArmSpec:
    """Limits of one arm, in metres and kilograms. None means unknown."""
    max_reach: Optional[float] = None       # radius the end effector reaches from the base
    reach_height: Optional[float] = None    # highest point it reaches, above the ground
    gripper_opening: Optional[float] = None # widest the gripper opens
    payload_kg: Optional[float] = None      # rated load for this arm
    degrees_of_freedom: Optional[int] = None

    def merged(self, overrides: Mapping[str, Any]) -> "ArmSpec":
        known = {f.name for f in fields(self)}
        unknown = set(overrides) - known
        if unknown:
            raise ValueError(f"unknown arm field(s) {sorted(unknown)}; "
                             f"expected some of {sorted(known)}")
        return ArmSpec(**{**self.__dict__, **overrides})


@dataclass
class RobotSpec:
    """One robot: what it is, what each arm can do, and where it stands."""
    name: str
    robot_type: str
    arms: Dict[str, ArmSpec] = field(default_factory=dict)
    payload_kg: Optional[float] = None
    position: List[float] = field(default_factory=list)
    location: List[str] = field(default_factory=list)
    state: List[str] = field(default_factory=list)
    capability: List[str] = field(default_factory=list)
    # Parser output kept whole, so fields not modelled above (base, sensors,
    # joint torques) still reach the agents.
    specs: Dict[str, Any] = field(default_factory=dict)
    # Whether per-arm figures should be shown to the agents. Off for a single
    # arm nobody overrode, which keeps the legacy entry byte-for-byte.
    per_arm: bool = False

    # ------------------------------------------------------------- builders

    @classmethod
    def from_urdf(cls, path: str | Path, *, payload_kg: Optional[float] = None,
                  arms: Optional[Mapping[str, Mapping[str, Any]]] = None,
                  robot_type: Optional[str] = None,
                  name: Optional[str] = None) -> "RobotSpec":
        """
        Read a URDF, then apply whatever the caller knows better.

        `arms` maps an arm name to the figures to set for it; names the URDF
        did not reveal are added. Giving `arms` at all switches on per-arm
        reporting, even for one arm.
        """
        specs = parse_urdf_to_specs(str(path))
        arm, grip = specs.get("arm") or {}, specs.get("gripper") or {}
        opening = grip.get("max_opening") if grip.get("has_gripper") else None

        found = arm_workspaces(str(path))
        if found:
            parsed = {side: ArmSpec(max_reach=w["max_reach"],
                                    reach_height=w["reach_height"],
                                    gripper_opening=opening,
                                    degrees_of_freedom=w["degrees_of_freedom"])
                      for side, w in found.items()}
        elif arm.get("has_arm"):
            parsed = {"arm": ArmSpec(max_reach=arm.get("max_reach"),
                                     reach_height=arm.get("reach_height"),
                                     gripper_opening=opening,
                                     degrees_of_freedom=arm.get("degrees_of_freedom"))}
        else:
            parsed = {}

        for arm_name, overrides in (arms or {}).items():
            parsed[arm_name] = parsed.get(arm_name, ArmSpec()).merged(overrides)

        return cls(name=name or specs.get("robot_name") or Path(path).stem,
                   robot_type=robot_type or specs.get("robot_type") or "unknown",
                   arms=parsed, payload_kg=payload_kg, specs=specs,
                   per_arm=bool(found) or bool(arms))

    @classmethod
    def manual(cls, name: str, robot_type: str, *,
               arms: Optional[Mapping[str, Mapping[str, Any]]] = None,
               payload_kg: Optional[float] = None,
               mobility: Optional[str] = None) -> "RobotSpec":
        """A robot with no URDF: every figure comes from the caller."""
        built = {n: ArmSpec().merged(v) for n, v in (arms or {}).items()}
        specs = {"robot_name": name, "robot_type": robot_type,
                 "base": {"mobility_type": mobility} if mobility else {}}
        return cls(name=name, robot_type=robot_type, arms=built,
                   payload_kg=payload_kg, specs=specs, per_arm=bool(built))

    def at(self, position: Optional[List[float]] = None,
           location: Optional[List[str]] = None,
           state: Optional[List[str]] = None) -> "RobotSpec":
        """A copy standing somewhere else. For teams of the same robot."""
        twin = copy.deepcopy(self)
        if position is not None:
            twin.position = list(position)
        if location is not None:
            twin.location = list(location)
        if state is not None:
            twin.state = list(state)
        return twin

    # ------------------------------------------------------------ pipeline

    def to_env(self) -> Dict[str, Any]:
        """The `env_data["robots"][id]` entry the pipeline reads."""
        urdf = copy.deepcopy(self.specs)

        if self.payload_kg is not None:
            urdf.setdefault("payload", {})["max_weight"] = self.payload_kg

        if self.per_arm and self.arms:
            arm = urdf.setdefault("arm", {})
            grip = urdf.setdefault("gripper", {})
            reaches = [a.max_reach for a in self.arms.values() if a.max_reach is not None]
            heights = [a.reach_height for a in self.arms.values() if a.reach_height is not None]
            openings = [a.gripper_opening for a in self.arms.values()
                        if a.gripper_opening is not None]
            # Robot-level figures stay the best any arm achieves, so a reader
            # of the old fields is never told the robot does less than it can.
            arm.update(has_arm=True, num_arms=len(self.arms),
                       max_reach=max(reaches) if reaches else arm.get("max_reach"),
                       reach_height=max(heights) if heights else arm.get("reach_height"))
            arm["arms"] = {n: {k: v for k, v in a.__dict__.items() if v is not None}
                           for n, a in self.arms.items()}
            if openings:
                grip.update(has_gripper=True, num_grippers=len(openings),
                            max_opening=max(openings))

        return {"urdf": urdf, "position": list(self.position),
                "location": list(self.location), "state": list(self.state),
                "capability": list(self.capability)}


def robots_env(robots: Mapping[str, RobotSpec]) -> Dict[str, Dict[str, Any]]:
    """`env_data["robots"]` for a team, keyed by the ids the planner will use."""
    return {rid: spec.to_env() for rid, spec in robots.items()}
