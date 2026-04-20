"""
Unified Reasoning Agent

Single class for all reasoning agents in HEART. Behavior is entirely
determined by agent_id at initialization:
- System prompt: role description and reasoning rules (system_prompts.py)
- Data filtering: only role-relevant environment data (data_filter.py)
- Human prompt: agent-specific response guidelines (reasoning.py)

Supports all agent configurations:
- 5 heterogeneous agents: capability, environmental, path, feasibility, constraint
- 3-agent ablation: physical (cap+feas merged), spatial (env+path merged), constraint
- 1 homogeneous agent: receives full unfiltered data
"""

import time
import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from heart.agents.base import BaseAgent, ReasoningResult
from heart.core.schema import AgentTask, AgentResponse
from heart.prompts.reasoning import get_reasoning_prompt
from heart.prompts.descriptions import get_task_response_strategy, get_task_type_descriptions
from heart.prompts.system_prompts import get_system_prompt


class ReasoningAgent(BaseAgent):
    """
    Unified reasoning agent for HEART.

    All 5 heterogeneous agents + homogeneous agent use this same class.
    Behavior is determined entirely by agent_id:
      - system prompt: loaded from prompts/system_prompts.py via agent_id
      - data filtering: handled by base.py via agent_id → data_filter.py
      - human prompt: loaded from prompts/reasoning.py via agent_id
    """

    def __init__(self, agent_id: str, model_name: str = "gpt-4o",
                 temperature: float = 0.1, env_data: Dict[str, Any] = None,
                 use_memory: bool = True):
        """
        Args:
            agent_id: Agent identifier (e.g., "capability_reasoner", "homogeneous_reasoner")
            model_name: LLM model to use
            temperature: Generation temperature
            env_data: Environment data (filtered by base.py based on agent_id)
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="reasoning",
            model_name=model_name,
            env_data=env_data
        )

        self.use_memory = use_memory
        self.llm_client = ChatOpenAI(model=model_name, temperature=temperature)
        self.parser = PydanticOutputParser(pydantic_object=AgentResponse)
        self.parser_format = self.parser.get_format_instructions()
        self.system_prompt = get_system_prompt(agent_id)
        self.system_message = SystemMessagePromptTemplate.from_template(self.system_prompt)
        self.calculate_estimated_tokens()

    def reason(self, tasks: List[AgentTask]) -> List[ReasoningResult]:
        def process_task(task: AgentTask) -> ReasoningResult:
            start_time = time.time()
            try:
                human_prompt = task.metadata.get("human_prompt",
                                                  get_reasoning_prompt(self.agent_id))
                prompt_template = self._create_prompt_template(human_prompt)

                question = task.query
                memory_data = self.get_memory_summary() if (self.use_memory and self.memory) else "No previous conversations"
                expert_data_str = json.dumps(self.filtered_env_data, indent=2) if self.filtered_env_data else "{}"

                question_type = task.metadata.get("question_type", "")
                original_task_type = task.metadata.get("original_task_type", question_type)

                prompt_vars = {
                    "question": question,
                    "question_type": question_type,
                    "original_task_type": original_task_type,
                    "original_instruction": task.metadata.get("original_instruction", ""),
                    "task_response_strategy": get_task_response_strategy(question_type),
                    "original_task_response_strategy": get_task_response_strategy(original_task_type),
                    "task_types": get_task_type_descriptions(),
                    "expert_data": expert_data_str,
                    "memory_data": memory_data,
                    "format_instructions": self.parser_format
                }

                chain = prompt_template | self.llm_client.with_structured_output(AgentResponse)

                with get_usage_metadata_callback() as cb:
                    response = chain.invoke(prompt_vars)

                tokens_used = 0
                if hasattr(cb, 'usage_metadata'):
                    for _, stat in cb.usage_metadata.items():
                        tokens_used += stat.get("total_tokens", 0) if isinstance(stat, dict) else 0

                execution_time = time.time() - start_time

                self.add_to_memory(
                    task_id=task.task_id,
                    prompt={"system": self.system_prompt, "human": human_prompt,
                            "question": question, "expert_data": self.filtered_env_data},
                    response=response,
                    tokens_used=tokens_used,
                    execution_time=execution_time
                )

                return ReasoningResult(
                    task_id=task.task_id, success=True, result=response,
                    reasoning_trace=self._generate_trace(task.task_id, response),
                    tokens_used=tokens_used, execution_time=execution_time
                )

            except Exception as e:
                return ReasoningResult(
                    task_id=task.task_id, success=False, result={"error": str(e)},
                    reasoning_trace=f"{self.agent_id} reasoning failed: {str(e)}",
                    tokens_used=0, execution_time=time.time() - start_time
                )

        return RunnableLambda(process_task).map().with_config(
            {"run_name": f"{self.agent_id} Reasoning"}
        ).invoke(tasks)

    def _create_prompt_template(self, human_prompt: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            self.system_message,
            HumanMessagePromptTemplate.from_template(human_prompt)
        ])

    def _generate_trace(self, task_id: str, result: Any) -> str:
        if isinstance(result, AgentResponse):
            status = result.status.value if hasattr(result.status, 'value') else result.status
            return f"{self.agent_id} {status}: {result.reasoning if result.reasoning else 'Completed'}"
        return f"Completed {self.agent_id} for task: {task_id}"

    def calculate_estimated_tokens(self) -> None:
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4o")
        tokens = 0
        if self.system_prompt:
            tokens += len(encoding.encode(self.system_prompt))
        if self.filtered_env_data:
            tokens += len(encoding.encode(json.dumps(self.filtered_env_data, indent=2)))
        if self.parser_format:
            tokens += len(encoding.encode(self.parser_format))
        tokens += len(encoding.encode(get_reasoning_prompt(self.agent_id)))
        tokens += len(encoding.encode(get_task_type_descriptions()))
        self.base_estimated_tokens = tokens
        if self.memory:
            tokens += len(encoding.encode(self.get_memory_summary()))
        self.estimated_tokens = tokens
