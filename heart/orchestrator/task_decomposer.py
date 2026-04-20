"""
HEART Task Decomposer (Stage 1)

Decomposes a natural language task instruction into a set of atomic reasoning
questions, each tagged with a TaskType (e.g., path_planning, physical_feasibility).
Uses a reasoning LLM (o4-mini) with structured output to generate questions
that cover capability, environment, path, feasibility, and constraint dimensions.

Supports refinement: if the initial decomposition has issues (too few/many questions,
missing coverage), the refine() method re-invokes the LLM with feedback.
"""

import uuid
from typing import List, Dict, Any, Optional

from heart.core.schema import (
    QuestionDecomposition, ReasoningQuestion, TaskType, AgentTask
)
from heart.agents.decomposer_agent import DecomposerAgent
from heart.prompts.decomposition import (
    get_decompose_human_prompt,
    get_refine_human_prompt)


class TaskDecomposer:
    """
    Orchestrator responsible for Task Decomposition
    
    Performs decomposition and refinement using DecomposerAgent
    Controls agent behavior by passing human prompt as context
    """
    
    def __init__(self, model_name: str = "o4-mini", temperature: float = 0.7, env_data: Dict[str, Any] = None):
        # Change model to o3, o1, o4-mini or gpt-5 for better reasoning performance
        # Initialize the decomposer agent with env_data
        self.agent = DecomposerAgent(model_name=model_name, temperature=temperature, env_data=env_data)
        self.refine_count = 0
        
    def decompose(self, instruction: str) -> QuestionDecomposition:
        """
        Decompose instruction into reasoning questions
        
        Args:
            instruction: High-level robot instruction
            env_data: Environmental context
            
        Returns:
            QuestionDecomposition with reasoning questions
        """
        # Create AgentTask using unified structure
        task = AgentTask(
            task_id=f"Decompose",
            query=instruction,  # Main instruction to decompose
            metadata={
                "operation": "decompose",
                "human_prompt": get_decompose_human_prompt()  # Can override default
            }
        )
        
        # Use agent's reason method with the task (expects list)
        results = self.agent.reason([task])
        result = results[0]  # Decomposer always returns single result
        
        if result.success and result.result:
            decompose = result.result  # QuestionDecomposition object            
            return decompose
        else:
            # Handle failure case
            raise ValueError(f"Decompose failed: {result.reasoning_trace}")
    
    def refine(self, decompose: QuestionDecomposition, issues: List[str]) -> QuestionDecomposition:
        """
        Refine decomposition based on identified issues
        
        Args:
            decomposition: Current decomposition result
            issues: List of identified issues
            env_data: Environmental context
            
        Returns:
            Refined decomposition
        """
        if not issues:
            print("No issues to refine")
            return decompose
            
        print(f"Refining based on issues: {issues}")
        
        # Create AgentTask for refinement using unified structure
        task = AgentTask(
            task_id=f"Refine_{self.refine_count}",
            query=decompose.instruction,  # Main instruction to refine
            metadata={
                "operation": "refine",
                "human_prompt": get_refine_human_prompt(),
                "issues": "\n".join(issues)  # Issues in metadata for refinement
            }
        )

        self.refine_count += 1  # Increment task count

        # Use the same agent with refinement task (expects list)
        results = self.agent.reason([task])
        result = results[0]  # Decomposer always returns single result
        
        if result.success and result.result:
            return result.result
        else:
            # If refinement fails, return original
            print(f"Refine failed: {result.reasoning_trace}")
            return decompose
    
