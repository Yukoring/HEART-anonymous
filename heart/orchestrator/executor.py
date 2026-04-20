"""
HEART Reasoning Executor (Stage 3)

Coordinates the execution of reasoning agents on allocated questions.
Each agent type has its own executor instance that manages:
- Converting question dicts to AgentTask objects with proper metadata
- Invoking the agent's reason() method
- Extracting structured results (status, answer, follow-up) from AgentResponse

The executor does not decide which agent handles which question — that is
done by the allocator (Stage 2). It only executes the assigned work.
"""

from typing import Dict, List, Any

from heart.core.schema import AgentTask

# Note: Agents are imported dynamically in nodes.py when needed


class ReasoningExecutor:
    """
    Reasoning Execution Orchestrator
    
    Each agent type has an independent instance.
    The same executor/agent is reused across nodes of the same agent type.
    """
    
    def __init__(self, agent_type: str = "", instruction: str = "", agent_instance=None):
        """
        Args:
            agent_type: Specific agent type to manage
            instruction: Original instruction for context
            agent_instance: Pre-initialized agent instance to reuse
        """
        self.agent_type = agent_type
        self.instruction = instruction
        
        # Use provided agent instance (already has filtered data)
        if agent_instance:
            self.agent = agent_instance
        else:
            raise ValueError("agent_instance must be provided (with pre-filtered env_data)")
    
            
    def execute_tasks_for_agent(
        self, 
        agent_name: str,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute tasks for a specific agent
        
        Args:
            agent_name: Agent name (e.g., "capability_reasoner")
            tasks: List of task dictionaries to process
            
        Returns:
            List of simplified result dicts with:
            - task_id: Question ID
            - success: API call success (True/False)
            - status: AgentResponse status ("SUCCESS"/"FAILED")
            - answer: Answer content
            - reasoning: Reasoning trace
            - follow_up_question: Optional follow-up (for FAILED)
            - tokens_used: Token count
            - execution_time: Time taken
        """
        # Verify this executor handles the requested agent
        if self.agent_type != agent_name:
            # Agent type mismatch
            return []
        
        agent = self.agent
        
        # Import agent-specific prompt
        from heart.prompts.reasoning import get_reasoning_prompt
        
        # Convert dict tasks to AgentTask objects
        agent_tasks = []
        for task_dict in tasks:
            question_id = task_dict.get("question_id", f"Q{len(agent_tasks)+1}")
            
            # Get human prompt template for this agent type
            human_prompt_template = get_reasoning_prompt(agent_name)
            
            # Get question type and original type for metadata
            question_type = task_dict.get("question_type", "")
            original_task_type = task_dict.get("original_task_type", question_type)  # Use current as default if no follow-up
            
            # Create unified AgentTask with minimal metadata
            agent_task = AgentTask(
                task_id=question_id,
                query=task_dict.get("prompt", ""),
                metadata={
                    "operation": "reasoning",
                    "question_type": question_type,  # Current question type
                    "original_task_type": original_task_type,  # Original question type (before follow-ups)
                    "original_instruction": self.instruction,  # Context
                    "human_prompt": human_prompt_template,
                }
            )
            agent_tasks.append(agent_task)
        
        # Execute tasks
        reasoning_results = agent.reason(agent_tasks)
        
        # Convert to simplified dict format
        simplified_results = []
        for result in reasoning_results:
            simplified = {
                "task_id": result.task_id,
                "success": result.success,  # API call success
                "tokens_used": result.tokens_used,
                "execution_time": result.execution_time
            }
            
            # Extract AgentResponse fields if API call was successful
            if result.success and result.result:
                agent_response = result.result
                simplified["status"] = agent_response.status if hasattr(agent_response, 'status') else "FAILED"
                simplified["answer"] = agent_response.answer_content if hasattr(agent_response, 'answer_content') else ""
                simplified["reasoning"] = agent_response.reasoning if hasattr(agent_response, 'reasoning') else result.reasoning_trace
                simplified["follow_up_question"] = agent_response.follow_up_question if hasattr(agent_response, 'follow_up_question') else None
                simplified["follow_up_task_type"] = agent_response.follow_up_task_type if hasattr(agent_response, 'follow_up_task_type') else None
            else:
                # API call failed
                simplified["status"] = "FAILED"
                simplified["answer"] = ""
                simplified["reasoning"] = result.reasoning_trace
                simplified["follow_up_question"] = None
                simplified["follow_up_task_type"] = None
                
            simplified_results.append(simplified)
        
        return simplified_results