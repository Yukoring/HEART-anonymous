"""
Synthesis Agent (Stage 4)

Cross-validates and consolidates raw Q&A reasoning results into structured
constraints for downstream planners. Produces:
- Feasible objects: what each robot CAN manipulate
- Infeasible objects: what cannot be handled and why (size, weight, reach, access)
- Manipulation capacity: per-robot gripper/arm summary
- Cleaned Q&A: deduplicated, contradiction-resolved constraints

Automatically selects single-robot or multi-robot synthesis prompt
based on the number of robots in the task.
"""

import time
import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import get_usage_metadata_callback

from heart.core.schema import SynthesizedConstraints
from heart.prompts.synthesis import (
    get_synthesis_system_prompt, get_synthesis_human_prompt,
    get_synthesis_system_prompt_multi_robot, get_synthesis_human_prompt_multi_robot,
)


class SynthesisAgent:
    """
    Cross-validates and consolidates raw Q&A into clean constraints.

    Takes all completed Q&A from reasoning agents and produces:
    - feasible_objects: what the robot(s) CAN manipulate
    - infeasible_objects: what no robot can handle and why
    - constraints: clean Q&A pairs (deduplicated, contradiction-resolved)

    Automatically selects single-robot or multi-robot prompt based on num_robots.
    """

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0):
        self.model_name = model_name
        self.llm_client = ChatOpenAI(model=model_name, temperature=temperature)
        self.parser = PydanticOutputParser(pydantic_object=SynthesizedConstraints)
        self.parser_format = self.parser.get_format_instructions()

        # Metrics
        self.total_tokens = 0
        self.total_time = 0.0

    def synthesize(self, instruction: str, raw_qa: str, num_robots: int = 1) -> Dict[str, Any]:
        """
        Synthesize raw Q&A into clean constraints.

        Args:
            instruction: Original task instruction
            raw_qa: Raw Q&A text from format_constraints()

        Returns:
            {
                "constraints_text": str,  # Formatted for planner injection
                "feasible_objects": List[str],
                "infeasible_objects": List[str],
                "tokens_used": int,
                "execution_time": float,
            }
        """
        start_time = time.time()

        if not raw_qa or not raw_qa.strip():
            return {
                "constraints_text": "",
                "feasible_objects": [],
                "infeasible_objects": [],
                "tokens_used": 0,
                "execution_time": 0.0,
            }

        # Select prompt based on robot count
        if num_robots >= 2:
            system_prompt = get_synthesis_system_prompt_multi_robot()
            human_prompt = get_synthesis_human_prompt_multi_robot()
        else:
            system_prompt = get_synthesis_system_prompt()
            human_prompt = get_synthesis_human_prompt()
        system_message = SystemMessagePromptTemplate.from_template(system_prompt)
        human_template = HumanMessagePromptTemplate.from_template(human_prompt)
        prompt_template = ChatPromptTemplate.from_messages([
            system_message, human_template
        ])

        # Call LLM
        chain = (prompt_template | self.llm_client.with_structured_output(SynthesizedConstraints)).with_config(
            {"run_name": "Synthesis Agent"}
        )

        try:
            with get_usage_metadata_callback() as cb:
                response = chain.invoke({
                    "instruction": instruction,
                    "raw_qa": raw_qa,
                    "format_instructions": self.parser_format,
                })

            tokens_used = 0
            if hasattr(cb, "usage_metadata"):
                for _, stat in cb.usage_metadata.items():
                    tokens_used += stat.get("total_tokens", 0) if isinstance(stat, dict) else 0

            execution_time = time.time() - start_time
            self.total_tokens += tokens_used
            self.total_time += execution_time

            # Format output as clean Q&A text for planner
            constraints_text = self._format_output(response)

            return {
                "constraints_text": constraints_text,
                "feasible_objects": response.feasible_objects,
                "infeasible_objects": response.infeasible_objects,
                "tokens_used": tokens_used,
                "execution_time": execution_time,
            }

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[SynthesisAgent] Failed: {e}")
            # Fallback: return raw Q&A as-is
            return {
                "constraints_text": raw_qa,
                "feasible_objects": [],
                "infeasible_objects": [],
                "tokens_used": 0,
                "execution_time": execution_time,
            }

    def _format_output(self, result: SynthesizedConstraints) -> str:
        """Format SynthesizedConstraints into planner-ready text."""
        lines = []

        # Feasible objects
        if result.feasible_objects:
            lines.append("Feasible Objects (robot CAN manipulate):")
            for obj in result.feasible_objects:
                lines.append(f"  - {obj}")
            lines.append("")

        # Infeasible objects
        if result.infeasible_objects:
            lines.append("Infeasible Objects (DO NOT use these):")
            for obj in result.infeasible_objects:
                lines.append(f"  - {obj}")
            lines.append("")

        # Manipulation capacity and action chain
        if result.manipulation_capacity and result.manipulation_capacity != "N/A":
            lines.append("Manipulation Capacity:")
            lines.append(f"  {result.manipulation_capacity}")
            lines.append("")

        # Constraints as Q&A
        if result.constraints:
            lines.append("Additional Constraints:")
            for qa in result.constraints:
                lines.append(f"Q: {qa.question}")
                lines.append(f"A: {qa.answer}")
                lines.append("")

        return "\n".join(lines)

