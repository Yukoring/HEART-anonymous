"""
Decomposition Prompts (Stage 1)

Prompt templates for the task decomposer. Given a natural language instruction
and full environment data (scene graph + robot URDF), the decomposer generates
5-20 atomic reasoning questions covering capability, environment, path,
feasibility, and constraint dimensions. Each question is tagged with a TaskType.

Includes separate prompts for:
- Standard decomposition (get_decompose_human_prompt)
- Refinement when initial decomposition has issues (get_refine_human_prompt)
- Multi-robot decomposition (get_decompose_multi_robot_human_prompt)
"""


def get_decompose_human_prompt() -> str:
    """Get human prompt template for decomposition into reasoning questions"""
    return """
## Context Provided:

**Instruction**: {instruction}

**Environment Data**: 
{env_data}

## Available Task Types:
{task_types}

## Available Agents and Their Expertise:
{agent_types}

## Important Guidelines:

1. **Data-aware question generation**: Before forming any question, verify data availability:
   - Check which fields are populated in the provided env_data
   - Only ask questions answerable from non-empty fields
   - Adapt questions to use available proxy data when ideal data is missing

2. **Available data fields** (verify these exist before using):
   - **Robot**: URDF specs (gripper, arm reach), state, position, location
   - **Objects**: affordances (primary), size, material (if available), parent/relation, accessible, state
   - **Scene**: room connectivity (neighbors), room positions/sizes, item-room mappings
   - **Often missing**: weight, temperature, texture, color

3. **Think from task planning perspective**: Generate questions for robot execution:
   - What actions are executable? (check robot capabilities + object affordances)
   - How many objects can the robot manipulate simultaneously? (check num_grippers/arms)
   - What objects and locations are involved? (verify in scene graph)
   - What navigation paths are needed? (use room connectivity)
   - What constraints exist? (from object states and relationships)

4. **Handle ambiguous instructions**: When verbs are vague (e.g., 'prepare', 'organize'):
   - Interpret as minimal executable robot actions
   - Focus on what robot CAN do based on available data
   - Use simplest viable interpretation

5. **Focus on task-level feasibility**: Frame questions around execution possibility:
   - "Can robot reach/manipulate?" not exact measurements
   - "Is navigation possible?" not precise coordinates
   - Use affordances to infer object capabilities
   - When multiple candidate objects exist, check each individually

6. **Coverage areas** (based on available data):
   - Robot capabilities and location
   - Multi-object manipulation capacity (how many items simultaneously?)
   - Object discovery using affordances
   - Navigation via neighbor connections
   - Physical feasibility from size/reach data
   - Task ordering from states/dependencies
   - Efficiency optimization (parallel vs sequential actions)

7. **Include clear rationale**: Explain WHY each question is needed for task execution.

## Output Format:

For each reasoning question, provide:
1. **question_id**: Unique identifier (e.g., "Q1", "Q2", etc.)
2. **question_type**: The TaskType enum value from the list above
3. **prompt**: A clear, specific question to be answered
4. **rationale**: Why this question is necessary for the task
5. **priority**: Priority level (1=highest, 2=medium, 3=low)

Note: The allocator will decide which agent handles each question based on their expertise.

{format_instructions}
"""


def get_decompose_multi_robot_prompt() -> str:
    """Get human prompt template for multi-robot decomposition"""
    return """
## Context Provided:

**Instruction**: {instruction}

**Environment Data**:
{env_data}

## Available Task Types:
{task_types}

## Available Agents and Their Expertise:
{agent_types}

## Multi-Robot Specific Guidelines:

1. **Robot Capability Analysis**: With multiple robots available, first understand each robot's unique capabilities:
   - What can each robot type do that others cannot? (e.g., flying vs ground, manipulation vs observation)
   - Which robot is best suited for different parts of the task?
   - Can robots work in parallel on different subtasks?

2. **Task Distribution Questions**: Generate questions that help determine optimal robot assignment:
   - Which subtasks require physical manipulation? (typically ground robots)
   - Which subtasks require exploration or high viewpoints? (typically aerial robots)
   - Which subtasks can be done simultaneously by different robots?
   - Are there dependencies between subtasks that affect robot coordination?

3. **Robot-Specific Questions**: For EACH robot, ask:
   - What room is this robot currently in? (MUST ask for EVERY robot — not just one)
   - What actions can this specific robot perform based on its URDF?
   - What locations can this robot reach given its mobility type?
   - What sensing capabilities does this robot have for the task?

4. **Coordination and Efficiency**: Consider multi-robot advantages:
   - Can subtasks be parallelized across robots?
   - Which robot should handle which objects/locations for efficiency?
   - Are there spatial constraints that affect robot assignments?

5. **Data-aware question generation**: Before forming any question, verify data availability:
   - Check which fields are populated in the provided env_data
   - Only ask questions answerable from non-empty fields
   - Adapt questions to use available proxy data when ideal data is missing

6. **Available data fields** (verify these exist before using):
   - **Robots**: Multiple URDF specs, different capabilities per robot
   - **Objects**: affordances (primary), size, material (if available), parent/relation, accessible, state
   - **Scene**: room connectivity (neighbors), room positions/sizes, item-room mappings
   - **Often missing**: weight, temperature, texture, color

7. **Think from task planning perspective**: Generate questions for robot execution:
   - What actions are executable by EACH robot? (check individual robot capabilities)
   - How can robots divide the work efficiently?
   - What objects and locations are involved? (verify in scene graph)
   - What navigation paths are needed for each robot type?
   - What constraints exist? (from object states and relationships)

8. **Handle ambiguous instructions**: When verbs are vague (e.g., 'prepare', 'organize'):
   - Interpret as minimal executable robot actions
   - Focus on what each robot CAN do based on available data
   - Use simplest viable interpretation

9. **Focus on task-level feasibility**: Frame questions around execution possibility:
   - "Can this specific robot reach/manipulate?" not exact measurements
   - "Is navigation possible for ground/aerial robot?" not precise coordinates
   - Use affordances to infer object capabilities

10. **Coverage areas** (based on available data):
   - Individual robot capabilities and locations
   - Multi-robot task allocation strategy
   - Object discovery using affordances
   - Navigation via neighbor connections (ground) or direct paths (aerial)
   - Physical feasibility from size/reach data per robot
   - Task ordering from states/dependencies
   - Parallel execution opportunities

11. **Include clear rationale**: Explain WHY each question is needed for task execution and which robot it relates to.

## Output Format:

For each reasoning question, provide:
1. **question_id**: Unique identifier (e.g., "Q1", "Q2", etc.)
2. **question_type**: The TaskType enum value from the list above
3. **prompt**: A clear, specific question to be answered (may specify which robot when relevant)
4. **rationale**: Why this question is necessary for the task
5. **priority**: Priority level (1=highest, 2=medium, 3=low)

Note: The allocator will decide which agent handles each question based on their expertise.

{format_instructions}
"""


def get_refine_human_prompt() -> str:
    """Get human prompt template for refining reasoning questions"""
    return """
## Previous Attempt:
{memory_context}

## Issues to Fix:
{issues}

## Original Task:
**Instruction**: {instruction}
**Environment Data**: {env_data}

## Available Task Types:
{task_types}

## Available Agents:
{agent_types}

## Refinement Guidelines:

**IMPORTANT: You MUST generate between 5 and 20 questions (inclusive).**
- If you have fewer than 5, add more detailed questions
- If you have more than 20, consolidate or remove less critical ones

1. **Fix data-incompatible questions**: Replace questions requiring unavailable data
   - Check if question needs missing fields (e.g., weight, temperature)
   - Reformulate using available proxy data (e.g., size instead of weight)

2. **Ground questions in actual data**: Verify against provided env_data
   - Questions must use only populated fields
   - Adapt to use affordances when object types unclear
   - Use room-level info when exact positions missing

3. **Maintain task execution focus**: Support robot planning with available info
   - Focus on feasibility with existing data
   - Consider robot's actual capabilities from URDF

4. **Add missing coverage**: Include essential planning aspects
5. **Adjust priorities**: Based on execution dependencies
6. **Balance completeness with data constraints**: Cover what's answerable

Note: Focus on WHAT information is needed (task type), not WHO will answer it (agent assignment).

{format_instructions}
"""


