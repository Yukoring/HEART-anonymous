"""
DELTA Planner — HEART Integration Wrapper (Stage 5 option)

Adapts the DELTA LLM-to-PDDL planner for use within the HEART pipeline.
Matches the LLMCoTPlanner interface: plan(instruction, env_data, heart_constraints) -> dict.

DELTA pipeline stages (from delta.py):
  1. Domain generation: LLM generates PDDL domain from task example
  2. Scene pruning: LLM prunes scene graph to task-relevant items
  3. Problem generation: LLM generates PDDL problem from pruned scene
  4. Goal decomposition: Split into subgoals → solve each with Fast Downward
  5. Plan concatenation: Merge subgoal plans into final plan

HEART additions (this file, NEW — not in original DELTA):
  - delta_planner.py: Programmatic wrapper matching HEART's planner interface
  - prompt_heart.py: Modified pruning prompt that uses HEART constraints
  - TASK_START_ROOMS: Robot start room mapping for all 40 tasks
  - data/example.py: Task examples with GT costs for all 40 tasks
  - data/scene_graph.py: Scene graphs with robot configs for all 3 scenes
"""

import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# DELTA internal imports (relative to planners/delta/)
from planners.delta.data.scene_graph import load_scene_graph, prune_sg_with_item, extract_accessible_items_from_sg
from planners.delta.data import example
from planners.delta.llm import llm as delta_llm
from planners.delta.llm import llm_utils
from planners.delta import prompt as p
from planners.delta import planner as delta_planner_engine
from planners.delta.utils import utils


DELTA_ROOT = Path(__file__).parent
PROJECT_ROOT = DELTA_ROOT.parent.parent  # HEART/


def _src_domain_path(scene_abbr: str, domain: str) -> str:
    """Ground truth PDDL domain file (project-level data/pddl/)."""
    return str(PROJECT_ROOT / "data" / "pddl" / "domain" / f"{scene_abbr}_{domain}_domain.pddl")


def _src_problem_path(scene_abbr: str, domain: str) -> str:
    """Ground truth PDDL problem file (project-level data/pddl/)."""
    return str(PROJECT_ROOT / "data" / "pddl" / "problem" / f"{scene_abbr}_{domain}_problem.pddl")


# Robot start rooms per (scene, domain) — matches ground truth PDDL problem files
# Only needed when different from DELTA scene graph default
# Value can be a string (single robot) or dict (multi-robot: {robot_name: room})
TASK_START_ROOMS = {
    # bw_0~4: original tasks
    ("beechwood", "turn_off_lights"): "bathroom_1",
    ("beechwood", "laundry"): "bathroom_1",
    ("beechwood", "meal_prep"): "bathroom_1",
    ("beechwood", "pack_work"): "lobby_14",
    ("beechwood", "kitchen_safety"): "lobby_14",
    # bw_5, bw_6: drone-only inspection tasks
    ("beechwood", "room_survey"): {"drone_1": "corridor_8"},
    ("beechwood", "appliance_inspection"): {"drone_1": "corridor_8"},
    # bw_7~9: fetch tasks
    ("beechwood", "kitchen_restock"): "bathroom_1",
    ("beechwood", "fridge_then_oven"): "lobby_14",
    ("beechwood", "dishwasher_load"): "dining_room_10",
    # bn_0~4: original tasks
    ("benevolence", "pack_essentials"): "living_room_12",
    ("benevolence", "serve_food"): "living_room_12",
    ("benevolence", "clean_kitchen"): "living_room_12",
    ("benevolence", "find_items"): "living_room_12",
    ("benevolence", "organize_kitchen"): "living_room_12",
    # bn_5~7: fetch tasks
    ("benevolence", "microwave_apple"): "living_room_12",
    ("benevolence", "bowl_to_oven"): "dining_room_9",
    ("benevolence", "sunglass_in_briefcase"): "dining_room_9",
    # bn_8~11: jr2_kinova tasks
    ("benevolence", "cheese_from_fridge"): "living_room_12",
    ("benevolence", "clean_and_cup"): "corridor_7",
    ("benevolence", "nearest_food"): "living_room_12",
    ("benevolence", "book_to_corridor"): "dining_room_9",
    ("benevolence", "living_room_setup"): "corridor_7",
    ("benevolence", "close_largest_furniture"): "kitchen_11",
    ("benevolence", "visit_rooms"): "kitchen_11",
    # mr_0~4: Merom tasks
    ("merom", "home_security"): {"robot_1": "living_room_10", "drone_1": "living_room_10"},
    ("merom", "clean_and_inspect"): {"robot_1": "bedroom_3", "drone_1": "living_room_10"},
    ("merom", "paper_towel_organization"): {"robot_1": "living_room_10", "drone_1": "living_room_10"},
    ("merom", "evening_preparation"): {"robot_1": "bedroom_3", "robot_2": "bedroom_3"},
    ("merom", "party_preparation"): {"robot_1": "bedroom_3", "robot_2": "living_room_10"},
    ("merom", "glass_delivery"): {"robot_1": "living_room_10", "drone_1": "living_room_10"},
    ("merom", "cross_delivery"): {"robot_1": "childs_room_5", "drone_1": "childs_room_5"},
    ("merom", "kitchen_survey"): {"robot_1": "living_room_10", "drone_1": "living_room_10"},
    ("merom", "zone_cleanup"): {"robot_1": "bedroom_3", "robot_2": "childs_room_5"},
    ("merom", "zone_delivery"): {"robot_1": "bathroom_2", "robot_2": "childs_room_5"},
    # bw_10~14: jr2_kinova tasks
    ("beechwood", "multi_container_store"): "bathroom_1",
    ("beechwood", "cross_house_delivery"): "lobby_14",
    ("beechwood", "milk_to_utility"): "living_room_13",
    ("beechwood", "evening_living_room"): "bathroom_1",
    ("beechwood", "kitchen_office_organize"): "dining_room_10",
}


class DeltaPlanner:
    """
    DELTA planner wrapper for HEART workflow.

    Runs the full DELTA pipeline:
        Stage 1: PDDL domain generation (LLM)
        Stage 2: Scene graph pruning (LLM)
        Stage 3: PDDL problem generation (LLM)
        Stage 4: Task decomposition into subgoals (LLM)
        Planning: Fast Downward solver via PDDLGym
    """

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0):
        self.model = delta_llm.load_llm(model_name, temperature)
        self.domain_example = "clean"
        self.scene_example = example.get_scenes(self.domain_example)[0]
        self.total_tokens = 0
        self.total_time = 0.0

    def plan(
        self,
        instruction: str,
        env_data: Dict[str, Any],
        heart_constraints: str = "",
        domain: str = "",
        scene: str = "",
        task_robots: Dict[str, str] = None,
        task_positions: Dict[str, str] = None,
        max_time: float = 60,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run DELTA pipeline and return plan.

        Args:
            instruction: Task instruction (not directly used — DELTA uses domain/scene)
            env_data: Environment data (not directly used — DELTA loads its own scene graphs)
            heart_constraints: HEART Q&A constraints text (empty = baseline DELTA)
            domain: DELTA domain name (e.g., "turn_off_lights", "serve_food")
            scene: DELTA scene name (e.g., "beechwood", "benevolence", "merom")
            max_time: Fast Downward time limit in seconds

        Returns:
            {"plan": List[str], "tokens_used": int, "execution_time": float,
             "exit_code": int, "subgoals": int}
        """
        start_time = time.time()

        if not domain or not scene:
            print(f"[DeltaPlanner] WARNING: domain='{domain}', scene='{scene}' — both required")
            return {"plan": [], "tokens_used": 0, "execution_time": 0.0}

        # Scene abbreviation for PDDL file paths
        scene_abbr_map = {"beechwood": "bw", "benevolence": "bn", "merom": "mr"}
        scene_abbr = scene_abbr_map.get(scene, scene[:2])

        # Select prune/problem functions based on heart_constraints
        if heart_constraints:
            from planners.delta.prompt_heart import nl_prune_item_heart, sg_2_pddl_problem_heart
            prune_fn = nl_prune_item_heart
            problem_fn = sg_2_pddl_problem_heart
        else:
            prune_fn = p.nl_prune_item
            problem_fn = p.sg_2_pddl_problem

        # Load example data
        domain_exp_pddl, problem_exp_pddl = self._load_example_pddl()
        exp = example.get_example(self.domain_example)
        qry = example.get_example(domain)

        add_obj_exp = exp["add_obj"]
        add_act_exp = exp["add_act"]
        goal_exp = exp["goal"]
        subgoal_exp = exp["subgoal"]
        item_keep_exp = exp["item_keep"]
        add_obj_qry = qry["add_obj"]
        add_act_qry = qry["add_act"]
        goal_qry = qry["goal"]

        # Setup logging directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = str(DELTA_ROOT / "result" / f"{domain}_{scene}_{timestamp}")
        Path(log_path).mkdir(parents=True, exist_ok=True)

        # Reset model state
        self.model.reset()

        # Load scene graphs — task_robots and task_positions inject robots into scene graph
        scene_exp = load_scene_graph(self.scene_example)
        scene_qry = load_scene_graph(scene, task_robots=task_robots, task_positions=task_positions)

        # Backward compat: if task_positions not provided, fall back to TASK_START_ROOMS
        if not task_positions:
            start_rooms = TASK_START_ROOMS.get((scene, domain))
            if start_rooms and "robots" in scene_qry:
                if isinstance(start_rooms, str):
                    # Single robot — apply to first robot in scene
                    first_robot = next(iter(scene_qry["robots"]))
                    scene_qry["robots"][first_robot]["position"] = start_rooms
                elif isinstance(start_rooms, dict):
                    for robot_name, room in start_rooms.items():
                        if robot_name in scene_qry["robots"]:
                            scene_qry["robots"][robot_name]["position"] = room

        # File paths for generated PDDL
        d_tar_file = os.path.join(log_path, f"{domain}_domain.pddl")
        p_tar_file = os.path.join(log_path, f"{scene}_{domain}_problem.pddl")
        plan_file = os.path.join(log_path, f"{domain}_{scene}.plan")
        plan_decomp_file = os.path.join(log_path, f"{domain}_{scene}_decomp.plan")

        d_time, pr_time, p_time, dp_time = 0., 0., 0., 0.
        subgoal_pddl_list = []
        item_keep = []
        domain_tar, problem_tar = None, None

        # ==================== Stage 1: Domain generation ====================
        content_d, prompt_d = p.nl_2_pddl_domain(
            domain_exp_pddl, domain, add_obj_exp, add_obj_qry, add_act_exp, add_act_qry)
        self.model.log(content_d + prompt_d, os.path.join(log_path, f"{domain}_domain.prompt"))
        self.model.init_prompt_chain(content_d, prompt_d)
        d_start = time.time()
        domain_tar = self.model.query_msg_chain()
        d_time = time.time() - d_start
        self.model.log(domain_tar, os.path.join(log_path, f"{domain}_domain.response"))
        llm_utils.export_result(domain_tar, d_tar_file)
        self.model.update_prompt_chain_w_response(domain_tar)
        print(f"[DELTA] Stage 1 (domain): {d_time:.2f}s")

        # ==================== Stage 2: Scene pruning ====================
        items_exp = extract_accessible_items_from_sg(scene_exp)
        items_qry = extract_accessible_items_from_sg(scene_qry)

        if heart_constraints:
            content_pr, prompt_pr = prune_fn(
                items_exp, items_qry, goal_exp, goal_qry, item_keep_exp,
                domain_exp_pddl, domain_tar, heart_constraints=heart_constraints)
        else:
            content_pr, prompt_pr = prune_fn(
                items_exp, items_qry, goal_exp, goal_qry, item_keep_exp,
                domain_exp_pddl, domain_tar)

        self.model.log(content_pr + prompt_pr, os.path.join(log_path, f"{scene}_prune.prompt"))
        self.model.update_prompt_chain(content_pr, prompt_pr)
        pr_start = time.time()
        prune_tar = self.model.query_msg_chain()
        pr_time = time.time() - pr_start
        self.model.log(prune_tar, os.path.join(log_path, f"{scene}_{domain}_prune.response"))
        item_keep = llm_utils.export_obj_list(prune_tar)
        self.model.update_prompt_chain_w_response(prune_tar)
        scene_exp = prune_sg_with_item(scene_exp, item_keep_exp)
        scene_qry = prune_sg_with_item(scene_qry, item_keep)
        print(f"[DELTA] Stage 2 (prune): {pr_time:.2f}s, items kept: {len(item_keep)}")

        # ==================== Stage 3: Problem generation ====================
        if heart_constraints:
            content_p, prompt_p = problem_fn(
                self.domain_example, domain_exp_pddl, problem_exp_pddl,
                scene_exp, scene_qry, goal_exp, goal_qry, domain_tar, domain,
                heart_constraints=heart_constraints)
        else:
            content_p, prompt_p = problem_fn(
                self.domain_example, domain_exp_pddl, problem_exp_pddl,
                scene_exp, scene_qry, goal_exp, goal_qry, domain_tar, domain)

        self.model.log(content_p + prompt_p, os.path.join(log_path, f"{scene}_{domain}_prob.prompt"))
        self.model.update_prompt_chain(content_p, prompt_p)
        p_start = time.time()
        problem_tar = self.model.query_msg_chain()
        p_time = time.time() - p_start
        self.model.log(problem_tar, os.path.join(log_path, f"{scene}_{domain}_prob.response"))
        llm_utils.export_result(problem_tar, p_tar_file)
        self.model.update_prompt_chain_w_response(problem_tar)
        print(f"[DELTA] Stage 3 (problem): {p_time:.2f}s")

        # ==================== Stage 4: Decomposition ====================
        content_dp, prompt_dp = p.decompose_problem_chain(
            goal_exp, subgoal_exp, exp["subgoal_pddl"], item_keep_exp,
            goal_qry, problem_exp_pddl, item_keep, problem_tar, domain_tar,
            acc_goal=False)
        self.model.log(content_dp + prompt_dp, os.path.join(log_path, f"{scene}_{domain}_decomp.prompt"))
        self.model.update_prompt_chain(content_dp, prompt_dp)
        dp_start = time.time()
        decomp_tar = self.model.query_msg_chain()
        dp_time = time.time() - dp_start
        subgoal_pddl_list = llm_utils.export_subgoal_list(decomp_tar)
        self.model.log(decomp_tar, os.path.join(log_path, f"{scene}_{domain}_decomp.response"))
        self.model.update_prompt_chain_w_response(decomp_tar)
        print(f"[DELTA] Stage 4 (decompose): {dp_time:.2f}s, subgoals: {len(subgoal_pddl_list)}")

        total_llm_time = d_time + pr_time + p_time + dp_time

        # ==================== Planning: Fast Downward ====================
        # Plan generation only — validation is done externally by plan_validator
        plan_actions = []
        plan_actions_orig = []
        exit_code = 0
        exit_code_orig = 0

        try:
            # Setup PDDLGym
            if not os.path.isfile(d_tar_file):
                d_tar_file = _src_domain_path(scene_abbr, domain)
            if not os.path.isfile(p_tar_file):
                p_tar_file = _src_problem_path(scene, domain)

            delta_planner_engine.export_domain_to_pddlgym(domain, d_tar_file)
            delta_planner_engine.export_problem_to_pddlgym(
                domain, p_tar_file,
                p_idx="00" if len(str(len(subgoal_pddl_list))) > 1 else "0",
                clear_dir=True)
            delta_planner_engine.register_new_pddlgym_env(domain)

            # Undecomposed planning
            plan, plan_time, node, cost, exit_code_orig = \
                delta_planner_engine.query_pddlgym(domain, max_time=max_time)
            if exit_code_orig == 1:
                plan_actions_orig = plan
                with open(plan_file, "w") as pf:
                    pf.write("\n".join(plan))

            # Hierarchical planning with decomposed subgoals
            if len(subgoal_pddl_list) > 0:
                plans, times, nodes, costs, exit_code, completed_sp = \
                    delta_planner_engine.query_pddlgym_decompose(
                        domain, subgoal_pddl_list, save_path=log_path, max_time=max_time)
                if exit_code == 1:
                    for sp in plans:
                        plan_actions.extend(sp)
                    with open(plan_decomp_file, "w") as pdf:
                        for sp in plans:
                            pdf.writelines("\n".join(sp) + "\n\n")
            else:
                # No subgoals — use undecomposed plan
                print("[DELTA] No decomposed subgoals, using undecomposed plan")
                exit_code = exit_code_orig
                plan_actions = plan_actions_orig

        except Exception as e:
            print(f"[DELTA] Planning failed: {e}")
            import traceback
            traceback.print_exc()
            exit_code = 0

        execution_time = time.time() - start_time
        self.total_time += execution_time

        print(f"[DELTA] Total: {execution_time:.2f}s (LLM: {total_llm_time:.2f}s), "
              f"plan decomposed: {len(plan_actions)} actions, "
              f"plan orig: {len(plan_actions_orig)} actions")

        return {
            "plan": plan_actions,              # decomposed plan (primary)
            "plan_orig": plan_actions_orig,     # undecomposed plan
            "tokens_used": self.model.total_tokens,
            "execution_time": execution_time,
            "exit_code": exit_code,
            "exit_code_orig": exit_code_orig,
            "subgoals": len(subgoal_pddl_list),
            "llm_time": total_llm_time,
        }

    def _load_example_pddl(self):
        """Load example PDDL domain and problem files (few-shot, no scene prefix)."""
        domain_path = str(PROJECT_ROOT / "data" / "pddl" / "domain" / f"{self.domain_example}_domain.pddl")
        problem_path = str(PROJECT_ROOT / "data" / "pddl" / "problem" / f"{self.domain_example}_example_problem.pddl")

        with open(domain_path, "r") as f:
            domain_exp = f.read()
        with open(problem_path, "r") as f:
            problem_exp = f.read()

        return domain_exp, problem_exp
