"""
RobotSpec: legacy entries unchanged, per-arm figures where there are arms.

    python -m pytest heart/tests/test_robot_spec.py -q
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from heart.robot_spec import RobotSpec, robots_env
from heart.utils.data_filter import filter_data_for_agent
from heart.utils.urdf_parser import parse_urdf_to_specs

ROBOTS = ROOT / "data" / "robots"
DUAL = Path(__file__).parent / "fixtures" / "dual_arm.urdf"
SINGLE_ARMED = ["fetch_gripper.urdf", "jr2_kinova_gripper.urdf",
                "summit_ur5e.urdf", "quadrotor.urdf"]


def legacy_entry(path):
    """What every experiment in the paper built by hand."""
    return {"urdf": parse_urdf_to_specs(str(path)), "position": [],
            "location": [], "state": [], "capability": []}


# ---------------------------------------------------------------- reproduction

@pytest.mark.parametrize("urdf", SINGLE_ARMED)
def test_single_arm_entry_is_unchanged(urdf):
    assert RobotSpec.from_urdf(ROBOTS / urdf).to_env() == legacy_entry(ROBOTS / urdf)


@pytest.mark.parametrize("urdf", SINGLE_ARMED)
@pytest.mark.parametrize("agent", ["capability_reasoner", "feasibility_reasoner"])
def test_single_arm_agents_see_the_same_data(urdf, agent):
    new = {"robots": {"r": RobotSpec.from_urdf(ROBOTS / urdf).to_env()}}
    old = {"robots": {"r": legacy_entry(ROBOTS / urdf)}}
    assert filter_data_for_agent(agent, new) == filter_data_for_agent(agent, old)


# ------------------------------------------------------------------ two arms

def test_each_arm_gets_its_own_workspace():
    spec = RobotSpec.from_urdf(DUAL)
    assert set(spec.arms) == {"left", "right"}
    # The fixture's left arm is built 0.2 m longer than its right.
    assert spec.arms["left"].max_reach > spec.arms["right"].max_reach + 0.15


def test_robot_level_reach_is_the_better_arm():
    """The parser alone reports whichever arm it met first; that is too low."""
    urdf = RobotSpec.from_urdf(DUAL).to_env()["urdf"]
    assert urdf["arm"]["max_reach"] > parse_urdf_to_specs(str(DUAL))["arm"]["max_reach"]
    assert urdf["arm"]["num_arms"] == 2


def test_feasibility_agent_sees_limits_per_arm_in_cm():
    spec = RobotSpec.from_urdf(DUAL, arms={"left": {"gripper_opening": 0.09},
                                           "right": {"gripper_opening": 0.07}})
    seen = filter_data_for_agent("feasibility_reasoner",
                                 {"robots": {"h1": spec.to_env()}})["robots"]["h1"]
    assert seen["arms"]["left"]["gripper_max_opening_cm"] == 9.0
    assert seen["arms"]["right"]["gripper_max_opening_cm"] == 7.0
    assert seen["arms"]["left"]["max_reach_cm"] > seen["arms"]["right"]["max_reach_cm"]


# ----------------------------------------------------------------- overrides

def test_payload_fills_what_the_urdf_lacks():
    assert parse_urdf_to_specs(str(ROBOTS / "fetch_gripper.urdf"))["payload"]["max_weight"] is None
    spec = RobotSpec.from_urdf(ROBOTS / "fetch_gripper.urdf", payload_kg=6.0)
    assert spec.to_env()["urdf"]["payload"]["max_weight"] == 6.0


def test_overriding_one_arm_keeps_the_rest():
    base = RobotSpec.from_urdf(DUAL)
    spec = RobotSpec.from_urdf(DUAL, arms={"left": {"max_reach": 0.5}})
    assert spec.arms["left"].max_reach == 0.5
    assert spec.arms["left"].reach_height == base.arms["left"].reach_height
    assert spec.arms["right"] == base.arms["right"]


def test_misspelt_arm_field_is_an_error():
    with pytest.raises(ValueError, match="gripper_openning"):
        RobotSpec.from_urdf(DUAL, arms={"left": {"gripper_openning": 0.09}})


def test_naming_arms_on_a_one_armed_robot_reports_them():
    spec = RobotSpec.from_urdf(ROBOTS / "fetch_gripper.urdf",
                               arms={"arm": {"gripper_opening": 0.1}})
    assert "arms" in spec.to_env()["urdf"]["arm"]


# ---------------------------------------------------------------- teams, manual

def test_team_members_are_independent_copies():
    drone = RobotSpec.from_urdf(ROBOTS / "quadrotor.urdf")
    team = {f"d{i}": drone.at(position=[i, 0, 1]) for i in range(3)}
    env = robots_env(team)
    assert [env[f"d{i}"]["position"] for i in range(3)] == [[0, 0, 1], [1, 0, 1], [2, 0, 1]]
    assert drone.position == []
    team["d0"].arms.clear()
    assert team["d1"].arms == drone.arms


def test_robot_without_urdf():
    spec = RobotSpec.manual("go2", "quadruped", mobility="legged", payload_kg=5.0,
                            arms={"arm": {"max_reach": 0.6, "gripper_opening": 0.08}})
    seen = filter_data_for_agent("feasibility_reasoner",
                                 {"robots": {"go2": spec.to_env()}})["robots"]["go2"]
    assert seen["max_payload_weight"] == 5.0
    assert seen["arms"]["arm"]["max_reach_cm"] == 60.0
