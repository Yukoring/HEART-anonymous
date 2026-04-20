"""
Reasoning Prompts (Stage 3)

Agent-specific human prompt templates for reasoning execution.
Each agent type has its own prompt with tailored decision guidelines:
- What data this agent has access to
- When to return SUCCESS vs PARTIAL vs OUT_OF_SCOPE
- What information to provide even when the full answer is unknown

Template variables ({question}, {expert_data}, {memory_data}, etc.)
are filled by ReasoningAgent at invocation time.
"""

from typing import Dict, Any


def get_reasoning_prompt(agent_name: str) -> str:
    """
    Get agent-specific human prompt template for reasoning
    Returns template with {} variables to be filled by agent
    
    Args:
        agent_name: Name of the agent (e.g., "capability_reasoner")
        
    Returns:
        Agent-specific human prompt template
    """
    # New robot domain agents
    if agent_name == "capability_reasoner":
        return get_capability_prompt()
    elif agent_name == "environmental_reasoner":
        return get_environmental_prompt()
    elif agent_name == "path_reasoner":
        return get_path_prompt()
    elif agent_name == "feasibility_reasoner":
        return get_feasibility_prompt()
    elif agent_name == "constraint_reasoner":
        return get_constraint_prompt()
    elif agent_name == "homogeneous_reasoner":
        return get_homogeneous_prompt()
    else:
        return get_default_prompt()


def get_capability_prompt() -> str:
    return """
## Task:
Question: {question}
Current Focus: {question_type}
Original Goal: {original_task_type}
Context: From instruction "{original_instruction}"

## Your Data:
{expert_data}

## Previous Context:
{memory_data}
IMPORTANT: The question itself may contain critical information from previous attempts. Carefully read and use ALL information in the question, including any data provided by other agents.

## Response Requirements:
Current focus: {task_response_strategy}
Original goal: {original_task_response_strategy}
Note: Your answer should work toward achieving the original goal format.

## Decision Guidelines:
- Can you answer the ORIGINAL question with format "{original_task_response_strategy}"? → SUCCESS
- Can you CONTRIBUTE ANY information toward the answer? → PARTIAL
  * ALWAYS provide what you DO know (robot capabilities, actions possible)
  * Even if you can't complete the full answer, share your relevant data
  * Example: If asked about picking objects, share robot's gripper capabilities
- Is the question COMPLETELY outside your expertise with NO relevant data? → OUT_OF_SCOPE
- CRITICAL: Always share robot capabilities you know
- CRITICAL: Don't focus on what you lack - provide what you DO have
- IMPORTANT: You ONLY know robot capabilities, NOT object positions/properties:
  * "What can robot do?" → Can answer (navigate, pick, place, open, close, etc.)
  * "Can robot reach object X?" → PARTIAL (share max_reach, but need object position)
  * "Can robot open microwave?" → PARTIAL (robot CAN open things, but need microwave position)
  * For specific robot-object questions, provide robot capabilities and state what's needed

## Available Task Types for Follow-up:
{task_types}

## Response Format:
- **Status**: SUCCESS / PARTIAL / OUT_OF_SCOPE
- **Answer**: Answer based on verified data only, never guess or assume but provide all relevant information as you can.
  If you don't know the exact answer, give the all relevant data or information you have for next agent.
- **Follow-up Question**: (if not SUCCESS) What additional information is needed? Make the follow-up a question the agent can handle within tasktype (data)
- **Follow-up Task Type**: (if not SUCCESS) Select from available types above
- **Reasoning**: Agent's reasoning process and key considerations

{format_instructions}
"""

def get_environmental_prompt() -> str:
    return """
## Task:
Question: {question}
Current Focus: {question_type}
Original Goal: {original_task_type}
Context: From instruction "{original_instruction}"

## Your Data:
{expert_data}

## Previous Context:
{memory_data}
IMPORTANT: The question itself may contain critical information from previous attempts. Carefully read and use ALL information in the question, including any data provided by other agents.

## Response Requirements:
Current focus: {task_response_strategy}
Original goal: {original_task_response_strategy}
Note: Your answer should work toward achieving the original goal format.

## Decision Guidelines:
- Can you answer the ORIGINAL question with format "{original_task_response_strategy}"? → SUCCESS
- Can you CONTRIBUTE ANY information toward the answer? → PARTIAL
  * ALWAYS provide what you DO know (object locations, rooms, affordances)
  * Even if you can't complete the full answer, share your relevant data
  * Example: If asked about paths to dirty clothes, provide WHERE dirty clothes are located
- Is the question COMPLETELY outside your expertise with NO relevant data? → OUT_OF_SCOPE
- CRITICAL: Always share object locations and room information you have
- CRITICAL: Don't focus on what you lack - provide what you DO have
- Note: You cannot plan paths (no room connectivity) but you MUST share object locations

## Available Task Types for Follow-up:
{task_types}

## Response Format:
- **Status**: SUCCESS / PARTIAL / OUT_OF_SCOPE
- **Answer**: Answer based on verified data only, never guess or assume but provide all relevant information as you can.
  If you don't know the exact answer, give the all relevant data or information you have for next agent.
- **Follow-up Question**: (if not SUCCESS) What additional information is needed? Make the follow-up a question the agent can handle within tasktype (data)
- **Follow-up Task Type**: (if not SUCCESS) Select from available types above
- **Reasoning**: Agent's reasoning process and key considerations

{format_instructions}
"""

def get_path_prompt() -> str:
    return """
## Task:
Question: {question}
Current Focus: {question_type}
Original Goal: {original_task_type}
Context: From instruction "{original_instruction}"

## Your Data:
{expert_data}

## Previous Context:
{memory_data}
IMPORTANT: The question itself may contain critical information from previous attempts. Carefully read and use ALL information in the question, including any data provided by other agents.

## Response Requirements:
Current focus: {task_response_strategy}
Original goal: {original_task_response_strategy}
Note: Your answer should work toward achieving the original goal format.

## Decision Guidelines:
- Can you answer the ORIGINAL question with format "{original_task_response_strategy}"? → SUCCESS
- Can you CONTRIBUTE ANY information toward the answer? → PARTIAL
  * ALWAYS provide what you DO know (robot's current room, known room connections)
  * Even if you can't complete paths, share partial route information
  * Example: If destination unknown but you know robot location, share that first
- Is the question COMPLETELY outside your expertise with NO relevant data? → OUT_OF_SCOPE
- CRITICAL: If objects mentioned but rooms unknown, need object_discovery first
- CRITICAL: Always share robot's current location and any known room paths
- CRITICAL: Verify each room in path is neighbor of previous room

## Available Task Types for Follow-up:
{task_types}

## Response Format:
- **Status**: SUCCESS / PARTIAL / OUT_OF_SCOPE
- **Answer**: Answer based on verified data only, never guess or assume but provide all relevant information as you can.
  If you don't know the exact answer, give the all relevant data or information you have for next agent.
- **Follow-up Question**: (if not SUCCESS) What additional information is needed? Make the follow-up a question the agent can handle within tasktype (data)
- **Follow-up Task Type**: (if not SUCCESS) Select from available types above
- **Reasoning**: Agent's reasoning process and key considerations

{format_instructions}
"""


def get_feasibility_prompt() -> str:
    return """
## Task:
Question: {question}
Current Focus: {question_type}
Original Goal: {original_task_type}
Context: From instruction "{original_instruction}"

## Your Data:
{expert_data}

## Previous Context:
{memory_data}
IMPORTANT: The question itself may contain critical information from previous attempts. Carefully read and use ALL information in the question, including any data provided by other agents.

## Response Requirements:
Current focus: {task_response_strategy}
Original goal: {original_task_response_strategy}
Note: Your answer should work toward achieving the original goal format.

## Decision Guidelines:
- FIRST: Check if answer is already in the question from previous attempts → USE IT
- Can you answer the ORIGINAL question with format "{original_task_response_strategy}"? → SUCCESS
- CRITICAL: For physical_feasibility or action_feasibility questions:
  * If object position unknown → Return SUCCESS with "Cannot determine - position data missing"
  * NEVER return PARTIAL/OUT_OF_SCOPE for missing position data
- Is the question COMPLETELY outside your expertise? → OUT_OF_SCOPE (rare)
- IMPORTANT: Action feasibility rules (SIMPLIFIED due to limited data):
  * **pick/place**: Check z-height, size vs gripper, weight limit
  * **turn_on, turn_off, open, close, push, pull**: ONLY check z-height
    - If z within workspace_height_range → FEASIBLE
    - If z outside range → NOT FEASIBLE
    - Ignore x,y distance for these actions (assume robot can navigate)
  * Example: "Can robot turn_off lamp at z=1.5m?" → If z<2.2m → "YES, FEASIBLE"

## Available Task Types for Follow-up:
{task_types}

## Response Format:
- **Status**: SUCCESS / PARTIAL / OUT_OF_SCOPE
- **Answer**: Answer based on verified data only, never guess or assume but provide all relevant information as you can.
  If you don't know the exact answer, give the all relevant data or information you have for next agent.
- **Follow-up Question**: (if not SUCCESS) What additional information is needed? Make the follow-up a question the agent can handle within tasktype (data)
- **Follow-up Task Type**: (if not SUCCESS) Select from available types above
- **Reasoning**: Agent's reasoning process and key considerations

{format_instructions}
"""


def get_constraint_prompt() -> str:
    return """
## Task:
Question: {question}
Current Focus: {question_type}
Original Goal: {original_task_type}
Context: From instruction "{original_instruction}"

## Your Data:
{expert_data}

## Previous Context:
{memory_data}
IMPORTANT: The question itself may contain critical information from previous attempts. Carefully read and use ALL information in the question, including any data provided by other agents.

## Response Requirements:
Current focus: {task_response_strategy}
Original goal: {original_task_response_strategy}
Note: Your answer should work toward achieving the original goal format.

## Decision Guidelines:
- Can you answer the ORIGINAL question with format "{original_task_response_strategy}"? → SUCCESS
- Can you CONTRIBUTE ANY information toward the answer? → PARTIAL
  * ALWAYS provide what you DO know (affordances, states, accessibility, dependencies)
  * Even if you can't complete the full answer, share your constraint analysis
  * Example: If asked about task ordering, provide what constraints you can identify
- Is the question COMPLETELY outside your expertise with NO relevant data? → OUT_OF_SCOPE
- CRITICAL: Always share constraints and dependencies you can identify
- CRITICAL: Provide affordance-based action possibilities even if incomplete

## Available Task Types for Follow-up:
{task_types}

## Response Format:
- **Status**: SUCCESS / PARTIAL / OUT_OF_SCOPE
- **Answer**: Answer based on verified data only, never guess or assume but provide all relevant information as you can.
  If you don't know the exact answer, give the all relevant data or information you have for next agent.
- **Follow-up Question**: (if not SUCCESS) What additional information is needed? Make the follow-up a question the agent can handle within tasktype (data)
- **Follow-up Task Type**: (if not SUCCESS) Select from available types above
- **Reasoning**: Agent's reasoning process and key considerations

{format_instructions}
"""

def get_default_prompt() -> str:
    """Default prompt template for unknown agent types"""
    return """
## Task:
Question: {question}
Type: {question_type}
Context: From instruction "{original_instruction}"

## Your Data:
{expert_data}

## Previous Context:
{memory_data}
IMPORTANT: The question itself may contain critical information from previous attempts. Carefully read and use ALL information in the question, including any data provided by other agents.

## Response Requirements:
Based on the task type: {task_response_strategy}

## Decision Guidelines:
- Can you answer with your available data? → SUCCESS
- Need information from other sources? → PARTIAL or OUT_OF_SCOPE
- When not SUCCESS, specify what data you need and suggest appropriate task type

## Available Task Types for Follow-up:
{task_types}

## Response Format:
- **Status**: SUCCESS / PARTIAL / OUT_OF_SCOPE
- **Answer**: Answer based on verified data only, never guess or assume but provide all relevant information as you can.
  If you don't know the exact answer, give the all relevant data or information you have for next agent.
- **Follow-up Question**: (if not SUCCESS) What additional information is needed? Make the follow-up a question the agent can handle within tasktype (data)
- **Follow-up Task Type**: (if not SUCCESS) Select from available types above
- **Reasoning**: Agent's reasoning process and key considerations

{format_instructions}
"""

def get_homogeneous_prompt() -> str:
    """Get human prompt template for homogeneous agent (no follow-up mechanism)"""
    return """
## Task:
Question: {question}
Current Focus: {question_type}
Original Goal: {original_task_type}
Context: From instruction "{original_instruction}"

## Your Complete Environment Data:
{expert_data}

## Previous Context:
{memory_data}
IMPORTANT: The question itself may contain critical information from previous attempts. Carefully read and use ALL information in the question, including any data provided by other agents.

## Response Requirements:
Current focus: {task_response_strategy}
Original goal: {original_task_response_strategy}
Note: Your answer should work toward achieving the original goal format.

## Decision Guidelines:
- Can you answer the ORIGINAL question with format "{original_task_response_strategy}"? → SUCCESS
- Can you CONTRIBUTE ANY information toward the answer? → PARTIAL
  * Provide what you DO know even if incomplete
  * Share relevant data you found
  * Better to give partial information than nothing
- Is the question COMPLETELY unanswerable with your data? → OUT_OF_SCOPE
- CRITICAL: You have access to ALL environment data (URDF, scene, affordances)
- CRITICAL: Use your complete data to provide the best possible answer
- IMPORTANT: Be flexible with format - focus on providing useful information

## Response Format:
- **Status**: SUCCESS / PARTIAL / OUT_OF_SCOPE  
- **Answer**: Answer based on verified data only, never guess or assume but provide all relevant information as you can.
  If you don't know the exact answer, give the all relevant data or information you have for next agent.
- **Reasoning**: Agent's reasoning process and key considerations

{format_instructions}"""