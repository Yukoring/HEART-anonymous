"""
Base Agent Class

Abstract base class for all HEART LLM agents. Provides:
- Environment data filtering at initialization (via agent_id → data_filter.py)
- Conversation memory for multi-round reasoning (previous Q&A injected into prompts)
- Token estimation for budget planning (static prompt + dynamic memory)
- Cumulative performance metrics (total tokens, total time)

Subclasses: ReasoningAgent (5 expert + homogeneous + 3-agent ablation),
DecomposerAgent (Stage 1), AllocatorAgent (LLM allocator baseline).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time

from heart.core.schema import AgentTask


@dataclass
class ReasoningResult:
    """Result of an agent's reasoning execution"""
    task_id: str
    success: bool
    result: Any  # Parsed reasoning output (format depends on task type)
    reasoning_trace: str  # Description of reasoning process
    tokens_used: int
    execution_time: float


class BaseAgent(ABC):
    """
    Abstract base class for all LLM agents in HEART.

    Provides common functionality: environment data filtering, conversation memory,
    token estimation, and performance metrics tracking.
    Subclasses must implement reason() and calculate_estimated_tokens().
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,  # e.g., "reasoning", "decomposer", "allocator"
        model_name: str,  # e.g., "gpt-4o", "o4-mini"
        env_data: Dict[str, Any] = {}
    ):
        """
        Args:
            agent_id: Unique agent identifier
            agent_type: Agent category type
            model_name: LLM model name to use
            env_data: Environment data (filtered at initialization based on agent_id)
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.model_name = model_name

        # Filter and store environment data
        from heart.utils.data_filter import filter_data_for_agent
        self.filtered_env_data = filter_data_for_agent(agent_id, env_data or {})

        # Estimated tokens (calculated after subclass initialization)
        self.estimated_tokens = 0

        # LLM client (initialized by subclass)
        self.llm_client = None

        # Conversation memory (reasoning history for multi-round interactions)
        self.memory: List[Dict[str, Any]] = []

        # Performance metrics from actual API calls
        self.total_tokens: int = 0
        self.total_time: float = 0.0

    @abstractmethod
    def reason(self, tasks: List[AgentTask]) -> List[ReasoningResult]:
        """
        Execute reasoning on given tasks (core method).

        Args:
            tasks: List of AgentTask, each containing:
                   - query: main content to process
                   - metadata: additional context

        Returns:
            List of ReasoningResult

        Implementation patterns:
        - Single-task agents (decomposer): process tasks[0] only
        - Multi-task agents (reasoning agents): process all tasks
        """
        pass

    def update_metrics(self, tokens_used: int = 0, execution_time: float = 0.0) -> None:
        """Update cumulative performance metrics."""
        self.total_tokens += tokens_used
        self.total_time += execution_time

    def update_estimated_tokens(self) -> None:
        """
        Update estimated tokens including dynamic memory size.
        Called after memory changes to reflect current context size.
        """
        if not hasattr(self, 'base_estimated_tokens'):
            self.base_estimated_tokens = getattr(self, 'estimated_tokens', 0)

        memory_tokens = 0
        if self.memory:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-4o")
            memory_summary = self.get_memory_summary()
            memory_tokens = len(encoding.encode(memory_summary))

        # estimated_tokens = base (static: prompt + env_data) + memory (dynamic)
        self.estimated_tokens = self.base_estimated_tokens + memory_tokens

    def add_to_memory(
        self,
        task_id: str,
        prompt: Dict[str, Any],
        response: Any,
        tokens_used: int = 0,
        execution_time: float = 0.0
    ) -> None:
        """
        Add a reasoning exchange to memory and update metrics.

        Args:
            task_id: Task identifier
            prompt: Full prompt sent (system + human + context)
            response: LLM response object
            tokens_used: Tokens consumed by this call
            execution_time: Time taken for this call (seconds)
        """
        self.memory.append({
            "task_id": task_id,
            "timestamp": time.time(),
            "prompt": prompt,
            "response": response,
            "tokens_used": tokens_used,
            "execution_time": execution_time
        })

        self.update_metrics(tokens_used, execution_time)
        self.update_estimated_tokens()

    def get_memory_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent memory entries.

        Args:
            limit: Number of recent entries to return
        """
        return self.memory[-limit:] if self.memory else []

    def get_memory_summary(self) -> str:
        """
        Get full conversation history as formatted text.
        Used for injecting previous context into agent prompts.
        """
        if not self.memory:
            return "No previous conversations"

        summary_parts = []
        for conv in self.memory:
            question = conv['prompt'].get('question', 'Unknown question')

            response = conv.get('response')
            if response and hasattr(response, 'status') and hasattr(response, 'answer_content'):
                status = response.status
                answer = response.answer_content
                summary_parts.append(f"Q: {question}\nA ({status}): {answer}")
            else:
                summary_parts.append(f"Q: {question}\nA: [Response not available]")

        return "\n\n".join(summary_parts)

    def clear_memory(self) -> None:
        """Clear all conversation memory."""
        self.memory = []

    @abstractmethod
    def calculate_estimated_tokens(self) -> None:
        """
        Calculate estimated token usage for this agent.
        Each subclass implements this based on its prompt structure and filtered data size.
        Should update self.estimated_tokens with the calculated value.
        """
        pass
