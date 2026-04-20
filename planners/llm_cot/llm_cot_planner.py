"""
LLM Chain-of-Thought Planner (Stage 5 option)

Generates executable robot action plans using GPT-4o with chain-of-thought
reasoning and few-shot examples. Supports three modes:
- Single robot: navigate, pick, place, open, close, turn_on/off, drop
- Drone only: navigate, check (aerial inspection)
- Multi-robot: heterogeneous teams with parallel task distribution

Works as both a standalone baseline (planner alone) and with HEART constraints
injected as additional context for improved plan quality.
"""

import time
import json
from typing import Dict, Any, List, Optional

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.output_parsers import PydanticOutputParser

from heart.core.schema import TaskPlan, MultiRobotTaskPlan
from heart.prompts.descriptions import get_robot_actions_from_affordances

SYSTEM_PROMPT = """You are an excellent planning agent.
Given some domain knowledge and a scene graph representation of an environment,
you can use it to generate a step-by-step task plan for solving a given goal instruction.

When information is provided, you MUST:
- Use ALL provided constraints and dependencies from the Q&A analysis
- Follow the identified rules and limitations strictly
- Respect the validated feasibility assessments, validated navigation paths, and validated action constraints
Your role is to integrate the analyzed information into a coherent executable plan."""


class LLMCoTPlanner:
    """
    LLM Chain-of-Thought Planner.

    Takes instruction + env_data + optional HEART constraints → generates action plan.
    Works independently (baseline) or with HEART constraints.
    """

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.system_message = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)

        self.parser = PydanticOutputParser(pydantic_object=TaskPlan)
        self.parser_format = self.parser.get_format_instructions()

        # Track metrics
        self.total_tokens = 0
        self.total_time = 0.0

    def plan(
        self,
        instruction: str,
        env_data: Dict[str, Any],
        heart_constraints: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate action plan.

        Args:
            instruction: Task instruction
            env_data: Full environment data (scene_graph + robots)
            heart_constraints: HEART Q&A constraints text (empty = baseline)

        Returns:
            {"plan": List[str], "tokens_used": int, "execution_time": float}
        """
        start_time = time.time()

        # 1. Convert data
        scene_data, robot_data, capability_actions = self._convert_data(env_data)

        # 2. Detect multi-robot / drone-only
        is_multi_robot = isinstance(robot_data, dict) and len(robot_data) >= 2
        is_drone_only = (
            not is_multi_robot
            and isinstance(robot_data, dict)
            and len(robot_data) == 1
            and not next(iter(robot_data.values())).get("urdf", {}).get("gripper", {}).get("has_gripper", True)
        )

        # 3. Select prompt and output schema
        if is_multi_robot:
            from planners.llm_cot.llm_as_planner_prompts import get_llm_as_planner_multi_robot_prompt
            human_prompt = get_llm_as_planner_multi_robot_prompt()
            output_schema = MultiRobotTaskPlan
            parser = PydanticOutputParser(pydantic_object=MultiRobotTaskPlan)
            format_instructions = parser.get_format_instructions()
        elif is_drone_only:
            from planners.llm_cot.llm_as_planner_prompts import get_llm_as_planner_drone_prompt
            human_prompt = get_llm_as_planner_drone_prompt()
            output_schema = TaskPlan
            format_instructions = self.parser_format
        else:
            from planners.llm_cot.llm_as_planner_prompts import get_llm_as_planner_prompt
            human_prompt = get_llm_as_planner_prompt()
            output_schema = TaskPlan
            format_instructions = self.parser_format

        # 4. Build prompt
        human_template = HumanMessagePromptTemplate.from_template(human_prompt)
        prompt_template = ChatPromptTemplate.from_messages([self.system_message, human_template])

        scene_str = json.dumps(scene_data, indent=2) if scene_data else "{}"
        robot_str = json.dumps(robot_data, indent=2) if robot_data else "{}"

        prompt_vars = {
            "query": instruction,
            "scene": scene_str,
            "robot": robot_str,
            "possible_actions": capability_actions,
            "additional_information": heart_constraints,
            "format_instructions": format_instructions,
        }

        # 5. Call LLM
        chain = (prompt_template | self.llm.with_structured_output(output_schema)).with_config(
            {"run_name": "LLM-CoT Planner"}
        )

        try:
            with get_usage_metadata_callback() as cb:
                response = chain.invoke(prompt_vars)

            tokens_used = 0
            if hasattr(cb, "usage_metadata"):
                for _, stat in cb.usage_metadata.items():
                    tokens_used += stat.get("total_tokens", 0) if isinstance(stat, dict) else 0

            execution_time = time.time() - start_time
            self.total_tokens += tokens_used
            self.total_time += execution_time

            # 6. Parse response
            actions = self._parse_response(response)

            return {
                "plan": actions,
                "tokens_used": tokens_used,
                "execution_time": execution_time,
            }

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"LLM-CoT planning failed: {e}")
            return {
                "plan": [],
                "tokens_used": 0,
                "execution_time": execution_time,
            }

    def _convert_data(self, env_data: Dict) -> tuple:
        """Convert env_data to planner format: (scene_data, robot_data, capability_actions)."""
        scene_graph = env_data.get("scene_graph", {})
        robot_data = env_data.get("robots", {})
        capability_actions = self._extract_capability_actions(scene_graph)
        return scene_graph, robot_data, capability_actions

    def _extract_capability_actions(self, scene_graph: Dict) -> str:
        """Extract available robot actions from scene affordances."""
        affordances = set()
        for scene_name, scene_data in scene_graph.items():
            if isinstance(scene_data, dict) and "rooms" in scene_data:
                for room_name, room_data in scene_data["rooms"].items():
                    for item_name, item_data in room_data.get("items", {}).items():
                        item_affordances = item_data.get("affordance", [])
                        if item_affordances:
                            affordances.update(item_affordances)

        actions = get_robot_actions_from_affordances(affordances)
        return "\n".join(actions)

    def _parse_response(self, response: Any) -> List[str]:
        """Parse LLM response into list of action strings."""
        if isinstance(response, TaskPlan):
            return response.plan if response.plan else []

        if hasattr(response, "robot_plans"):
            all_actions = []
            for robot_plan in response.robot_plans:
                all_actions.append(f"# {robot_plan.robot_id}'s tasks: {robot_plan.task_description}")
                all_actions.extend(robot_plan.actions)
            return all_actions

        return []
