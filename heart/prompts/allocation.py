"""
LLM Allocator Prompt

Human prompt template for the LLM-based allocator (baseline).
Given a question's content, type, and rationale, the LLM decides which
expert agent is most suitable. Used only when allocator_type="llm".
"""

def get_allocation_prompt() -> str:
    """
    Human prompt template for LLM-based single task allocation.
    Each task is processed individually to support parallel allocation.
    
    Returns:
        Allocation prompt template for single task
    """
    return """## Question to Allocate:
- Question: {question_prompt}
- Task Type: {task_type} - {task_type_description}
- Rationale: {question_rationale}

## Context:
Original Instruction: {original_instruction}

## Available Agents and Their Data:
{agent_profiles}

## Allocation Task:
Based on the task type and question content, select the ONE agent whose data can best answer this question.

Consider:
1. What data does this question require?
2. Which agent has access to that specific data?
3. Does the task type match the agent's expertise?

Provide:
- task_id: {question_id}
- assigned_agent: Must be EXACTLY one of: capability_reasoner, environmental_reasoner, path_reasoner, feasibility_reasoner, constraint_reasoner
- reasoning: Brief explanation of why this agent's data matches the question needs

{format_instructions}"""


