"""
Triple-S planner (arXiv:2508.07421), ported to the HEART benchmark.

Triple-S generates policy code end to end rather than supplying context to a
downstream planner, so it enters this benchmark as a third planner beside
LLM-CoT and DELTA, not as a replacement for HEART's reasoning stage. Its output
uses the same action vocabulary LLM-CoT emits, which lets it run through the
existing validator untouched.

The four stages follow the paper:

  1. Simplification LLM  instruction -> ordered de-implicit minimal tasks
  2. Retrieval           top-k demonstrations by Sentence-BERT cosine similarity
  3. Solution LLM        one minimal task at a time -> actions, in a closed loop
                         with error feedback
  4. Summary LLM         encapsulate what worked, update the library

Two deliberate departures, both to keep the comparison fair rather than to
weaken the method:

Stage 3's loop is closed on a schema check — action names, arity, and object
identifiers — and not on VAL. The paper closes it on simulator execution, which
this benchmark has no equivalent of; closing it on VAL instead would hand
Triple-S the ground-truth PDDL that HEART never sees.

Stage 4 updates the library within a run but does not persist across tasks, so
no task benefits from having seen the evaluation set.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.callbacks import get_usage_metadata_callback

from heart.prompts.descriptions import get_robot_actions_from_affordances
from planners.triple_s.demonstrations import Demonstration, DemonstrationLibrary
from planners.triple_s import prompts

MAX_FEEDBACK_ROUNDS = 3
TOP_K = 2

# The action vocabulary LLM-CoT defines in its own prompt
# (planners/llm_cot/llm_as_planner_prompts.py). Triple-S is given the same set so
# the two planners are writing in the same language and the comparison is of
# reasoning, not of which verbs each was told about. Scene affordances add
# domain verbs on top of this; they never override it.
CANONICAL_ACTIONS = {
    "navigate": (3, "navigate(<robot>, <from_room>, <to_room>): move to a connected room"),
    "pick": (2, "pick(<robot>, <item>): pick up an item in the current room"),
    "pick_from": (3, "pick_from(<robot>, <item>, <container>): pick an item out of a container"),
    "place": (3, "place(<robot>, <item>, <target>): place the held item on or in a target"),
    "drop": (3, "drop(<robot>, <item>, <room>): release the held item, no target needed"),
    "open": (2, "open(<robot>, <container>): open a container"),
    "close": (2, "close(<robot>, <container>): close a container"),
    "turn_on": (2, "turn_on(<robot>, <device>): turn a device on"),
    "turn_off": (2, "turn_off(<robot>, <device>): turn a device off"),
    "check": (2, "check(<robot>, <item>): visually inspect an item in the current room"),
}


class TripleSPlanner:
    """Simplification-Solution-Summary planning over a scene graph."""

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0,
                 top_k: int = TOP_K, max_feedback_rounds: int = MAX_FEEDBACK_ROUNDS):
        self.model_name = model_name
        self.temperature = temperature
        self.top_k = top_k
        self.max_feedback_rounds = max_feedback_rounds
        self._llm: Optional[ChatOpenAI] = None

        self.total_tokens = 0
        self.total_time = 0.0

    @property
    def llm(self) -> ChatOpenAI:
        """Built on first use, so the schema checks are testable without a key."""
        if self._llm is None:
            self._llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
        return self._llm

    # ------------------------------------------------------------------ public

    def plan(self, instruction: str, env_data: Dict[str, Any],
             heart_constraints: str = "", **kwargs) -> Dict[str, Any]:
        """
        Generate an action plan.

        `heart_constraints` is accepted so this planner is interchangeable with
        the others; passing it runs Triple-S on top of HEART's reasoning, and
        leaving it empty runs Triple-S alone, which is the comparison the paper
        needs.
        """
        start = time.time()
        self._tokens_this_run = 0

        scene_graph = env_data.get("scene_graph", {})
        robots = env_data.get("robots", {})
        action_library = self._action_library(scene_graph)
        signatures = self._signatures(action_library)
        identifiers = self._identifiers(scene_graph, robots)
        environment = self._describe_environment(scene_graph, robots)

        library = DemonstrationLibrary()
        stage_log: List[Dict[str, Any]] = []

        try:
            minimal_tasks = self._simplify(instruction, environment)
            if not minimal_tasks:
                return self._result([], start, stage_log, "simplification produced no tasks")

            actions: List[str] = []
            for task in minimal_tasks:
                retrieved = library.retrieve(task, k=self.top_k)
                state = self._state_text(environment, actions, heart_constraints)
                step_actions, rounds, rejection = self._solve(
                    task, action_library, library.render(retrieved), state,
                    signatures, identifiers)

                stage_log.append({"minimal_task": task, "rounds": rounds,
                                  "accepted": bool(step_actions),
                                  "rejection": rejection})
                if not step_actions:
                    continue

                actions.extend(step_actions)
                demonstration = self._summarize(task, step_actions, action_library)
                if demonstration is not None:
                    stage_log[-1]["library"] = library.update(demonstration)

            return self._result(actions, start, stage_log)

        except Exception as exc:  # noqa: BLE001 — a failed run is a data point
            print(f"Triple-S planning failed: {exc}")
            return self._result([], start, stage_log, str(exc))

    # ------------------------------------------------------------------ stages

    def _simplify(self, instruction: str, environment: str) -> List[str]:
        """Stage 1: one instruction into an ordered list of minimal tasks."""
        text = self._ask(prompts.simplification_prompt(instruction, environment))
        tasks = []
        for line in text.splitlines():
            line = line.strip()
            match = re.match(r"^\d+[.)]\s*(.+)$", line)
            if match:
                tasks.append(match.group(1).strip())
        return tasks

    def _solve(self, minimal_task: str, action_library: str, demonstrations: str,
               state: str, signatures: Dict[str, int],
               identifiers: Set[str]) -> Tuple[List[str], int, str]:
        """
        Stage 3: actions for one minimal task, retried while the schema rejects.

        Returns the accepted actions, how many rounds it took, and the last
        rejection message (empty when accepted first try).
        """
        feedback = ""
        for round_index in range(1, self.max_feedback_rounds + 1):
            text = self._ask(prompts.solution_prompt(
                minimal_task, action_library, demonstrations, state, feedback))
            candidate = self._parse_actions(text)
            problems = self._check(candidate, signatures, identifiers)
            if not problems:
                return candidate, round_index, ""
            feedback = "\n".join(problems)
        return [], self.max_feedback_rounds, feedback

    def _summarize(self, minimal_task: str, actions: List[str],
                   action_library: str) -> Optional[Demonstration]:
        """Stage 4: fold a successful step into a reusable demonstration."""
        text = self._ask(prompts.summary_prompt(
            minimal_task, "\n".join(actions), action_library))

        description = thought = ""
        example: List[str] = []
        section = None
        for line in text.splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered.startswith("[task description]"):
                description = stripped.split("]", 1)[1].strip()
                section = "description"
            elif lowered.startswith("[thought]"):
                thought = stripped.split("]", 1)[1].strip()
                section = "thought"
            elif lowered.startswith("[examples]"):
                section = "examples"
            elif section == "examples" and "(" in stripped:
                example.append(stripped)

        if not description or not example:
            return None
        return Demonstration(description=description, thought=thought, actions=example)

    # ------------------------------------------------------------- schema check

    def _check(self, actions: List[str], signatures: Dict[str, int],
               identifiers: Set[str]) -> List[str]:
        """
        Reject an action sequence the domain cannot express.

        This stands in for the paper's compiler pass: an unknown action, a wrong
        argument count, or an identifier absent from the scene are exactly the
        errors it catches before anything reaches the controller.
        """
        problems = []
        if not actions:
            return ["No actions were produced."]

        for action in actions:
            match = re.match(r"^([a-z_]+)\((.*)\)$", action.strip())
            if match is None:
                problems.append(f"'{action}' is not of the form action(arg, ...).")
                continue

            name, arg_text = match.group(1), match.group(2)
            args = [a.strip() for a in arg_text.split(",") if a.strip()]

            if name not in signatures:
                problems.append(f"'{name}' is not in the action library.")
                continue
            if signatures[name] != len(args):
                problems.append(
                    f"'{name}' takes {signatures[name]} arguments, got {len(args)}.")
            unknown = [a for a in args if a not in identifiers]
            if unknown:
                problems.append(
                    f"'{name}' refers to {', '.join(unknown)}, which the scene "
                    f"does not contain.")
        return problems

    # ------------------------------------------------------------------ helpers

    def _ask(self, prompt: str) -> str:
        with get_usage_metadata_callback() as cb:
            response = self.llm.invoke(prompt)
        if hasattr(cb, "usage_metadata"):
            for _, stat in cb.usage_metadata.items():
                if isinstance(stat, dict):
                    self._tokens_this_run += stat.get("total_tokens", 0)
        return response.content if hasattr(response, "content") else str(response)

    @staticmethod
    def _parse_actions(text: str) -> List[str]:
        actions = []
        for line in text.splitlines():
            line = line.strip().strip("`").lstrip("- ").strip()
            line = re.sub(r"^\d+[.)]\s*", "", line)
            if re.match(r"^[a-z_]+\(.*\)$", line):
                actions.append(line)
        return actions

    @staticmethod
    def _action_library(scene_graph: Dict) -> str:
        """
        The canonical vocabulary, plus any domain verb the scene affords that it
        does not already cover (cleaning, pouring, and the like).
        """
        affordances: Set[str] = set()
        for scene in scene_graph.values():
            if not isinstance(scene, dict) or "rooms" not in scene:
                continue
            for room in scene["rooms"].values():
                for item in room.get("items", {}).values():
                    affordances.update(item.get("affordance", []))

        lines = ["Available Robot Actions:"]
        lines += [f"- {description}" for _, description in CANONICAL_ACTIONS.values()]
        for extra in get_robot_actions_from_affordances(affordances):
            match = re.search(r"([a-z_]+)\(", extra)
            if match and match.group(1) not in CANONICAL_ACTIONS:
                lines.append(extra if extra.startswith("- ") else f"- {extra}")
        return "\n".join(lines)

    @staticmethod
    def _signatures(action_library: str) -> Dict[str, int]:
        """Action name to argument count, read off the library descriptions."""
        signatures = {name: arity for name, (arity, _) in CANONICAL_ACTIONS.items()}
        for line in action_library.splitlines():
            match = re.search(r"([a-z_]+)\(([^)]*)\)", line)
            if match and match.group(1) not in signatures:
                args = [a for a in match.group(2).split(",") if a.strip()]
                signatures[match.group(1)] = len(args)
        return signatures

    @staticmethod
    def _identifiers(scene_graph: Dict, robots: Dict) -> Set[str]:
        names: Set[str] = set(robots.keys())
        for scene in scene_graph.values():
            if not isinstance(scene, dict) or "rooms" not in scene:
                continue
            for room_name, room in scene["rooms"].items():
                names.add(room_name)
                names.update(room.get("items", {}).keys())
        return names

    @staticmethod
    def _describe_environment(scene_graph: Dict, robots: Dict) -> str:
        lines = []
        for scene in scene_graph.values():
            if not isinstance(scene, dict) or "rooms" not in scene:
                continue
            for room_name, room in scene["rooms"].items():
                neighbours = ", ".join(room.get("neighbor", [])) or "none"
                lines.append(f"{room_name} (connects to: {neighbours})")
                for item_name, item in room.get("items", {}).items():
                    size = " x ".join(f"{v:.2f}" for v in item.get("size", []))
                    weight = item.get("weight")
                    detail = [f"size {size} m"]
                    if weight is not None:
                        detail.append(f"weight {weight} kg")
                    detail.append(f"height {item['location'][2]:.2f} m")
                    if item.get("affordance"):
                        detail.append("affords " + "/".join(item["affordance"]))
                    if item.get("state"):
                        detail.append("state " + "/".join(item["state"]))
                    lines.append(f"  - {item_name}: {'; '.join(detail)}")

        for name, config in robots.items():
            gripper = config.get("urdf", {}).get("gripper", {})
            arm = config.get("urdf", {}).get("arm", {})
            spec = []
            if gripper.get("max_opening"):
                spec.append(f"gripper opens to {gripper['max_opening']:.3f} m")
            if arm.get("reach_height"):
                spec.append(f"reaches {arm['reach_height']:.2f} m high")
            lines.append(f"{name}: {'; '.join(spec) if spec else 'no manipulator'}")

        return "\n".join(lines)

    @staticmethod
    def _state_text(environment: str, actions_so_far: List[str],
                    heart_constraints: str) -> str:
        parts = [environment]
        if actions_so_far:
            parts.append("Actions already executed:\n" + "\n".join(actions_so_far))
        if heart_constraints:
            parts.append("Additional constraints:\n" + heart_constraints)
        return "\n\n".join(parts)

    def _result(self, actions: List[str], start: float,
                stage_log: List[Dict[str, Any]], error: str = "") -> Dict[str, Any]:
        elapsed = time.time() - start
        self.total_tokens += self._tokens_this_run
        self.total_time += elapsed
        result = {
            "plan": actions,
            "tokens_used": self._tokens_this_run,
            "execution_time": elapsed,
            "stage_log": stage_log,
        }
        if error:
            result["error"] = error
        return result
