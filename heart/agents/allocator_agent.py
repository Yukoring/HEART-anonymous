"""
LLM Allocator Agent

LLM-based task allocation agent that uses GPT-4o to assign each reasoning
question to the most suitable expert agent. Used only when allocator_type="llm"
as a baseline comparison against the HEART embedding-based allocator.
"""

import time
import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.runnables import RunnableLambda

from heart.agents.base import BaseAgent, ReasoningResult
from heart.core.schema import AgentTask, AgentType, TaskAllocation
from heart.prompts.allocation import get_allocation_prompt
from heart.prompts.descriptions import get_task_type_description, get_agent_type_descriptions
from heart.prompts.system_prompts import get_system_prompt


class AllocatorAgent(BaseAgent):
    """LLM-based Task Allocator — uses GPT-4o to assign tasks to agents."""

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0, env_data: Dict[str, Any] = None):
        super().__init__(agent_id="allocator", agent_type="orchestrator", model_name=model_name, env_data=env_data)
        self.llm_client = ChatOpenAI(model=model_name, temperature=temperature)
        self.parser = PydanticOutputParser(pydantic_object=TaskAllocation)
        self.parser_format = self.parser.get_format_instructions()
        self.system_prompt = get_system_prompt("allocator")
        self.system_message = SystemMessagePromptTemplate.from_template(self.system_prompt)
        self.calculate_estimated_tokens()

    def reason(self, tasks: List[AgentTask]) -> List[ReasoningResult]:
        def process_task(task: AgentTask) -> ReasoningResult:
            start_time = time.time()
            try:
                human_prompt = task.metadata.get("human_prompt", get_allocation_prompt())
                prompt_template = self._create_prompt_template(human_prompt)
                task_type = task.metadata.get("question_type", "")
                prompt_vars = {
                    "question_id": task.metadata.get("question_id", ""),
                    "original_instruction": task.metadata.get("original_instruction", ""),
                    "question_prompt": task.query,
                    "question_rationale": task.metadata.get("question_rationale", ""),
                    "task_type": task_type,
                    "task_type_description": get_task_type_description(task_type),
                    "agent_profiles": get_agent_type_descriptions(),
                    "format_instructions": self.parser_format
                }
                chain = prompt_template | self.llm_client.with_structured_output(TaskAllocation)
                with get_usage_metadata_callback() as cb:
                    allocation = chain.invoke(prompt_vars)
                tokens_used = 0
                for _, stat in cb.usage_metadata.items():
                    tokens_used += stat.get("total_tokens", 0)
                execution_time = time.time() - start_time
                self.add_to_memory(task_id=task.task_id, prompt={"system_prompt": self.system_prompt, "human_prompt": human_prompt, "query": task.query, "metadata": task.metadata}, response=allocation, tokens_used=tokens_used, execution_time=execution_time)
                return ReasoningResult(task_id=task.task_id, success=True, result=allocation, reasoning_trace=self._generate_trace(task.task_id, allocation, task), tokens_used=tokens_used, execution_time=execution_time)
            except Exception as e:
                return ReasoningResult(task_id=task.task_id, success=False, result=None, reasoning_trace=f"Allocation failed: {str(e)}", tokens_used=0, execution_time=time.time() - start_time)

        return RunnableLambda(process_task).map().with_config({"run_name": "Allocate"}).invoke(tasks)

    def _create_prompt_template(self, human_prompt_template: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([self.system_message, HumanMessagePromptTemplate.from_template(human_prompt_template)])

    def _generate_trace(self, task_id: str, result: Any, task: AgentTask) -> str:
        if isinstance(result, TaskAllocation):
            agent_name = result.assigned_agent.value if hasattr(result.assigned_agent, 'value') else result.assigned_agent
            return f"Allocated to {agent_name}: {result.reasoning}"
        return f"Completed allocation for task: {task_id}"

    def calculate_estimated_tokens(self) -> None:
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4o")
        tokens = 0
        if self.system_prompt: tokens += len(encoding.encode(self.system_prompt))
        if self.filtered_env_data: tokens += len(encoding.encode(json.dumps(self.filtered_env_data, indent=2)))
        if self.parser_format: tokens += len(encoding.encode(self.parser_format))
        if self.memory: tokens += len(encoding.encode(self.get_memory_summary()))
        tokens += len(encoding.encode(get_agent_type_descriptions()))
        self.estimated_tokens = tokens
