"""
Task and robot configurations for experiments.
Defines scenes, tasks (instructions), and robot setups.

Naming convention:
  Scene abbreviations: bw (Beechwood_0), bn (Benevolence_1), mr (Merom_1)
  Task IDs: {scene_abbr}_{index} (e.g., bw_0, bn_1, mr_2)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Task:
    """Single task definition"""
    id: str
    domain: str  # PDDL domain name (used by DELTA and VAL)
    goal: str
    position: Dict[str, List[float]] = None  # Robot start positions per task
    robots: Dict[str, str] = None  # Robot config override per task: {name: urdf_key}. If None, use SCENE_ROBOTS.


# Scene abbreviation mapping
SCENE_ABBR = {
    "Beechwood_0": "bw",
    "Benevolence_1": "bn",
    "Merom_1": "mr",
}

ABBR_TO_SCENE = {v: k for k, v in SCENE_ABBR.items()}

# Robot URDF paths (relative to project root)
ROBOT_URDFS = {
    "fetch_gripper": "data/robots/fetch_gripper.urdf",
    "quadrotor": "data/robots/quadrotor.urdf",
    "jr2_kinova_gripper": "data/robots/jr2_kinova_gripper.urdf",
}

# Scene graph paths (relative to project root)
SCENE_GRAPHS = {
    "Beechwood_0": "data/scenes/Tiny_Beechwood_0_scene_graph.json",
    "Benevolence_1": "data/scenes/Tiny_Benevolence_1_scene_graph.json",
    "Merom_1": "data/scenes/Tiny_Merom_1_scene_graph.json",
}

# Robot configurations per scene — which robots and their URDF
SCENE_ROBOTS = {
    "Beechwood_0": {
        "robot": {"urdf": "fetch_gripper"},
    },
    "Benevolence_1": {
        "robot": {"urdf": "fetch_gripper"},
    },
    "Merom_1": {
        "robot_1": {"urdf": "fetch_gripper"},
        "drone_1": {"urdf": "quadrotor"},
    },
}

# Task definitions per scene
SCENE_TASKS = {
    "Beechwood_0": [
        Task(
            id="bw_0", domain="turn_off_lights",
            goal="Turn off all the turned-on floor lamps in the house",
            position={"robot": [-2.6, 3.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_1", domain="laundry",
            goal="Do laundry by putting dirty clothes into the washing machine and starting it",
            position={"robot": [-2.6, 3.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_2", domain="meal_prep",
            goal="Pick up the salad and the hamburger from the kitchen, place both on the dining table, and close the open fridge in the kitchen",
            position={"robot": [-2.6, 3.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_3", domain="pack_work",
            goal="Pack work items by putting notebook and pen in briefcase",
            position={"robot": [-6.9, 3.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_4", domain="kitchen_safety",
            goal="Ensure kitchen safety by checking if stove and oven are on, and turning them off if needed, also close the refrigerator if it opened then turn-on it.",
            position={"robot": [-6.9, 3.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_5", domain="room_survey",
            goal="Fly to every room in the house and check the state of all lamps",
            position={"drone_1": [-2.6, 0.5, 2.0]},
            robots={"drone_1": "quadrotor"},
        ),
        Task(
            id="bw_6", domain="appliance_inspection",
            goal="Fly through the kitchen and the utility room to verify the presence and location of the burner, microwave, fridge, washer, and dryer",
            position={"drone_1": [-2.6, 0.5, 2.0]},
            robots={"drone_1": "quadrotor"},
        ),
        Task(
            id="bw_7", domain="kitchen_restock",
            goal="Take the milk from the countertop and the cereal from the table, place both in the refrigerator, then close the refrigerator",
            position={"robot": [-2.6, 3.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_8", domain="fridge_then_oven",
            goal="Open the oven and place the hamburger, close the oven and turn it on, then take the milk and place it in the refrigerator",
            position={"robot": [-6.9, 3.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_9", domain="dishwasher_load",
            goal="Take the bowl from the dining table, open the dishwasher, place the bowl inside, and close and turn the dishwasher on",
            position={"robot": [-9.2, -1.1, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bw_10", domain="multi_container_store",
            goal="Put the milk in the refrigerator and the cereal in the chest in the kitchen, then close both",
            position={"robot": [-2.6, 3.1, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bw_11", domain="cross_house_delivery",
            goal="Put the notebook in the opened cabinet in the home office, the pen in the opened chest in the kitchen, and the salad in the sink in the utility room",
            position={"robot": [-6.9, 3.1, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bw_12", domain="milk_to_utility",
            goal="Pick up the milk from the kitchen and place it in the sink in the utility room without going through the dining room, staircase, or corridor",
            position={"robot": [-0.5, -3.7, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bw_13", domain="evening_living_room",
            goal="Turn off all turned-on floor lamps in the living room, turn on the TV, and clean the sofa",
            position={"robot": [-2.6, 3.1, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bw_14", domain="kitchen_office_organize",
            goal="Close the opened chest in the kitchen, then open the closed cabinet in the home office and place the pen inside the cabinet",
            position={"robot": [-9.2, -1.1, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
    ],

    "Benevolence_1": [
        Task(
            id="bn_0", domain="pack_essentials",
            goal="Pack work essentials by putting any one notebook and pen in briefcase",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_1", domain="serve_food",
            goal="Serve food to dining table by placing any one apple and hamburger on the dining table",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_2", domain="clean_kitchen",
            goal="Clean kitchen by putting one small bowl in dishwasher, if dishwasher is closed then open it first",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_3", domain="find_items",
            goal="Find personal items by placing sunglass next to hamburger and close open windows",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_4", domain="organize_kitchen",
            goal="Put the eatable food items on the kitchen countertop into the fridge from smallest to largest, then close the fridge",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_5", domain="microwave_apple",
            goal="Put an apple in the microwave and heat it",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_6", domain="bowl_to_oven",
            goal="Put a bowl in the oven and heat it",
            position={"robot": [0.1, -2.3, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_7", domain="sunglass_in_briefcase",
            goal="Put a sunglass in the briefcase",
            position={"robot": [0.1, -2.3, 0.0]},
            robots={"robot": "fetch_gripper"},
        ),
        Task(
            id="bn_8", domain="cheese_from_fridge",
            goal="Take a cheese out of the fridge and place it on the dining table",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bn_9", domain="clean_and_cup",
            goal="Clean all chairs in the dining room and bring a cup to the dining table",
            position={"robot": [-2.0, -3.5, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bn_10", domain="nearest_food",
            goal="Bring the nearest food item to the dining table",
            position={"robot": [-0.5, -6.0, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bn_11", domain="book_to_corridor",
            goal="Put any graspable book and the pen on the console table in the corridor",
            position={"robot": [0.1, -2.3, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bn_12", domain="living_room_setup",
            goal="Turn on the TV and the floor lamp, then put a sunglass on the sofa",
            position={"robot": [-2.0, -3.5, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bn_13", domain="close_largest_furniture",
            goal="Close the largest opened chest and clean the sofa",
            position={"robot": [-0.5, 0.4, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
        Task(
            id="bn_14", domain="visit_rooms",
            goal="Visit every room except the largest and the smallest",
            position={"robot": [-0.5, 0.4, 0.0]},
            robots={"robot": "jr2_kinova_gripper"},
        ),
    ],

    "Merom_1": [
        Task(
            id="mr_0", domain="home_security",
            goal="Inspect all opened windows in the house and turn off all lamps that are on",
            position={"robot_1": [2.7, 7.5, 0.0], "drone_1": [2.8, 7.9, 2.0]},
            robots={"robot_1": "fetch_gripper", "drone_1": "quadrotor"},
        ),
        Task(
            id="mr_1", domain="clean_and_inspect",
            goal="Clean all cleanable items in the bathroom, and check all pickable items located above 2.0 meters height in the house",
            position={"robot_1": [3.2, 0.0, 0.0], "drone_1": [2.8, 7.9, 2.0]},
            robots={"robot_1": "fetch_gripper", "drone_1": "quadrotor"},
        ),
        Task(
            id="mr_2", domain="paper_towel_organization",
            goal="Take the aerial view of all rooms in the house, and collect the paper towel closest to the robot's current position and place it in an opened cabinet in the kitchen then close the cabinet",
            position={"robot_1": [2.7, 7.5, 0.0], "drone_1": [2.8, 7.9, 2.0]},
            robots={"robot_1": "fetch_gripper", "drone_1": "quadrotor"},
        ),
        Task(
            id="mr_3", domain="evening_preparation",
            goal="Organize the house: if dishwasher is closed open it then take out the glass and place on dining table, close all the opened windows and turn off stove and all floor lamps that are on",
            position={"robot_1": [3.2, 1.0, 0.0], "robot_2": [3.0, 0.0, 0.0]},
            robots={"robot_1": "fetch_gripper", "robot_2": "fetch_gripper"},
        ),
        Task(
            id="mr_4", domain="party_preparation",
            goal="Prepare for party: take wine bottle and cheese from the kitchen to the dining table, turn on all lamps in the house and ensure all windows are closed",
            position={"robot_1": [3.2, 0.0, 0.0], "robot_2": [2.8, 7.9, 0.0]},
            robots={"robot_1": "fetch_gripper", "robot_2": "fetch_gripper"},
        ),
        Task(
            id="mr_5", domain="glass_delivery",
            goal="Open the fridge in the kitchen so the drone can inspect what is inside",
            position={"robot_1": [2.7, 7.5, 0.0], "drone_1": [2.8, 7.9, 2.0]},
            robots={"robot_1": "fetch_gripper", "drone_1": "quadrotor"},
        ),
        Task(
            id="mr_6", domain="cross_delivery",
            goal="Bring the atomizer to the coffee table in the living room and the notebook to the dining table, and have the drone check the opened windows",
            position={"robot_1": [-2.2, 2.0, 0.0], "drone_1": [-2.2, 2.0, 2.0]},
            robots={"robot_1": "fetch_gripper", "drone_1": "quadrotor"},
        ),
        Task(
            id="mr_7", domain="kitchen_survey",
            goal="Turn off the stove in the kitchen and close the opened window in the dining room, and have the drone survey the bedroom, child's room, and bathroom",
            position={"robot_1": [2.7, 7.5, 0.0], "drone_1": [2.8, 7.9, 2.0]},
            robots={"robot_1": "fetch_gripper", "drone_1": "quadrotor"},
        ),
        Task(
            id="mr_8", domain="zone_cleanup",
            goal="Turn off all the floor lamps that are on, turn off the stove, and close all opened windows. robot_1 cannot enter the kitchen, dining room, or child's room. robot_2 cannot enter the living room, bathroom, or bedroom.",
            position={"robot_1": [3.2, 0.1, 0.0], "robot_2": [-0.7, 0.2, 0.0]},
            robots={"robot_1": "fetch_gripper", "robot_2": "fetch_gripper"},
        ),
        Task(
            id="mr_9", domain="zone_delivery",
            goal="Put the notebook on the bottom cabinet in the bedroom and the wine bottle on the dining table. robot_1 cannot enter the kitchen, dining room, or child's room. robot_2 cannot enter the living room, bathroom, or bedroom.",
            position={"robot_1": [3.7, 4.0, 0.0], "robot_2": [-0.7, 0.2, 0.0]},
            robots={"robot_1": "fetch_gripper", "robot_2": "fetch_gripper"},
        ),
    ],
}


def get_tasks_for_scene(scene_name: str) -> List[Task]:
    """Get task list for a specific scene."""
    return SCENE_TASKS.get(scene_name, [])


def get_scene_graph_path(scene_name: str) -> str:
    """Get scene graph file path for a scene."""
    return SCENE_GRAPHS.get(scene_name, "")


def get_robot_urdf_path(robot_type: str) -> str:
    """Get URDF file path for a robot type."""
    return ROBOT_URDFS.get(robot_type, "")


def get_scene_robots(scene_name: str, task=None) -> Dict[str, Dict]:
    """Get robot configuration. Uses task.robots if available, else scene default."""
    if task and task.robots:
        return {name: {"urdf": urdf} for name, urdf in task.robots.items()}
    return SCENE_ROBOTS.get(scene_name, {})


def get_pddl_domain_path(task_id: str) -> str:
    """Get ground truth PDDL domain file path for a task.
    Uses task_id (e.g., 'bw_0') → scene abbr + domain name.
    """
    abbr = task_id.split("_")[0]  # bw, bn, mr
    domain = _get_domain_for_task(task_id)
    return f"data/pddl/domain/{abbr}_{domain}_domain.pddl"


def get_pddl_problem_path(scene_name: str, task_id: str) -> str:
    """Get ground truth PDDL problem file path for a scene+task.
    Uses scene abbreviation + domain name.
    """
    abbr = SCENE_ABBR.get(scene_name, task_id.split("_")[0])
    domain = _get_domain_for_task(task_id)
    return f"data/pddl/problem/{abbr}_{domain}_problem.pddl"


def get_scene_abbr(scene_name: str) -> str:
    """Get scene abbreviation (bw, bn, mr)."""
    return SCENE_ABBR.get(scene_name, scene_name.split("_")[0].lower())


def _get_domain_for_task(task_id: str) -> str:
    """Look up PDDL domain name from task_id."""
    for scene_tasks in SCENE_TASKS.values():
        for task in scene_tasks:
            if task.id == task_id:
                return task.domain
    return task_id  # fallback
