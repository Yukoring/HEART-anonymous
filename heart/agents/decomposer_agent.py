"""
Decomposer Agent (Stage 1)

Breaks down a high-level task instruction into atomic reasoning questions
using a reasoning LLM (o4-mini). Each question is tagged with a TaskType
and includes a rationale explaining why it is needed for the task.

Automatically switches between single-robot and multi-robot decomposition
prompts based on the number of robots in the environment data.
"""

import time
import json
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import get_usage_metadata_callback

from heart.agents.base import BaseAgent, ReasoningResult
from heart.core.schema import QuestionDecomposition, ReasoningQuestion, TaskType, AgentTask
from heart.prompts.decomposition import get_decompose_human_prompt, get_decompose_multi_robot_prompt, get_refine_human_prompt
from heart.prompts.descriptions import get_agent_type_descriptions, get_task_type_descriptions
from heart.prompts.system_prompts import get_system_prompt


class DecomposerAgent(BaseAgent):
    """Task Decomposition Specialist — decomposes instructions into reasoning questions."""

    def __init__(self, model_name: str = "o4-mini", temperature: float = 0.7, env_data: Dict[str, Any] = None):
        super().__init__(agent_id="decomposer", agent_type="orchestrator", model_name=model_name, env_data=env_data)

        # o-series models don't support temperature parameter
        if model_name.startswith('o4') or model_name.startswith('o3') or model_name.startswith('o1'):
            self.llm_client = ChatOpenAI(model=model_name)
        else:
            self.llm_client = ChatOpenAI(model=model_name, temperature=temperature)

        self.parser = PydanticOutputParser(pydantic_object=QuestionDecomposition)
        self.parser_format = self.parser.get_format_instructions()
        self.system_prompt = get_system_prompt("decomposer")
        self.system_message = SystemMessagePromptTemplate.from_template(self.system_prompt)
        self.calculate_estimated_tokens()

    def reason(self, tasks: List[AgentTask]) -> List[ReasoningResult]:
        """Decomposer always processes exactly 1 task."""
        if len(tasks) != 1:
            raise ValueError(f"DecomposerAgent expects exactly 1 task, got {len(tasks)}")

        task = tasks[0]
        start_time = time.time()

        try:
            operation = task.metadata.get("operation", "decompose")

            # Select human prompt based on operation
            if operation == "decompose":
                num_robots = 0
                if self.filtered_env_data and isinstance(self.filtered_env_data, dict):
                    robot_data = self.filtered_env_data.get("robots", {})
                    if isinstance(robot_data, dict):
                        num_robots = len(robot_data)
                if num_robots >= 2:
                    human_prompt = get_decompose_multi_robot_prompt()
                else:
                    human_prompt = task.metadata.get("human_prompt") or get_decompose_human_prompt()
            elif operation == "refine":
                human_prompt = task.metadata.get("human_prompt") or get_refine_human_prompt()

            prompt_template = self._create_prompt_template(human_prompt)

            # Prepare prompt variables
            prompt_vars = {
                "instruction": task.query,
                "env_data": self.filtered_env_data,
                "format_instructions": self.parser_format,
                "agent_types": get_agent_type_descriptions(),
                "task_types": get_task_type_descriptions(),
            }

            # Refine-specific context
            if operation == "refine":
                prompt_vars["issues"] = task.metadata.get("issues", "No specific issues identified")
                memory_context = "No previous attempts"
                if self.memory:
                    recent = self.get_memory_context(limit=1)
                    if recent:
                        last_attempt = recent[0]
                        memory_context = f"Previous attempt (Task: {last_attempt['task_id']}):\n"
                        if 'response' in last_attempt and last_attempt['response']:
                            prev_result = last_attempt['response']
                            if hasattr(prev_result, 'questions'):
                                memory_context += f"- Generated {len(prev_result.questions)} questions\n"
                                for q in prev_result.questions:
                                    memory_context += f"  - {q.question_id} ({q.question_type}): {q.prompt}\n"
                                    if hasattr(q, 'rationale'):
                                        memory_context += f"    Rationale: {q.rationale}\n"
                prompt_vars["memory_context"] = memory_context

            chain = (prompt_template | self.llm_client.with_structured_output(QuestionDecomposition)).with_config({"run_name": "Decompose"})
            with get_usage_metadata_callback() as cb:
                result = chain.invoke(prompt_vars)

            tokens_used = 0
            for _, stat in cb.usage_metadata.items():
                tokens_used += stat.get("total_tokens", 0)
            execution_time = time.time() - start_time

            self.add_to_memory(
                task_id=task.task_id,
                prompt={"system_prompt": self.system_prompt, "human_prompt": human_prompt, "query": task.query, "env_data": self.filtered_env_data, "metadata": task.metadata},
                response=result, tokens_used=tokens_used, execution_time=execution_time
            )

            return [ReasoningResult(task_id=task.task_id, success=True, result=result, reasoning_trace=self._generate_trace(task.task_id, result, task), tokens_used=tokens_used, execution_time=execution_time)]

        except Exception as e:
            return [ReasoningResult(task_id=task.task_id, success=False, result=None, reasoning_trace=f"Task failed: {str(e)}", tokens_used=0, execution_time=time.time() - start_time)]

    def _create_prompt_template(self, human_prompt_template: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([self.system_message, HumanMessagePromptTemplate.from_template(human_prompt_template)])

    def _generate_trace(self, task_id: str, result: Any, task: AgentTask) -> str:
        if isinstance(result, QuestionDecomposition):
            return f"Successfully decomposed '{task.query}' into {len(result.questions)} reasoning questions"
        return f"Completed {task.metadata.get('operation', 'process')} for task: {task_id}"

    def calculate_estimated_tokens(self) -> None:
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4o")
        tokens = 0
        if self.system_prompt: tokens += len(encoding.encode(self.system_prompt))
        if self.filtered_env_data: tokens += len(encoding.encode(json.dumps(self.filtered_env_data, indent=2)))
        if self.parser_format: tokens += len(encoding.encode(self.parser_format))
        if self.memory: tokens += len(encoding.encode(self.get_memory_summary()))
        self.estimated_tokens = tokens
