"""
Synthesis Prompts (Stage 4)

System and human prompt templates for the SynthesisAgent. The LLM receives
raw Q&A results from all reasoning agents and produces:
- Feasible/infeasible object classification with reasons
- Per-robot manipulation capacity summary
- Cleaned, deduplicated Q&A pairs with contradictions resolved

Separate prompt variants for single-robot and multi-robot tasks.
The output is injected into downstream planners as additional constraints.
"""


def get_synthesis_system_prompt() -> str:
    """Single-robot synthesis prompt."""
    return """You are a Constraint Synthesis Agent for robot task planning.

Your role: Cross-validate and consolidate raw Q&A results from multiple specialist agents
into clean, non-contradictory constraints that a task planner can directly use.

The raw Q&A comes from these specialist agents (each sees different data):
- Capability Reasoner: robot hardware specs (gripper, arm, sensors)
- Environmental Reasoner: object locations, affordances, accessibility
- Path Reasoner: room connectivity, navigation paths
- Feasibility Reasoner: physical feasibility (size vs gripper, reach, weight)
- Constraint Reasoner: logical constraints, action ordering, dependencies

CRITICAL — these agents may CONTRADICT each other because they see different data:
- Environmental agent may list an object as "pickable" (based on affordance)
- But Feasibility agent may say "too large for gripper" (based on size)
- In such cases: Feasibility OVERRIDES Environmental for physical checks

Your synthesis rules:
1. KEEP ALL ORIGINAL QUESTIONS exactly as they are — do not modify, merge, or remove questions
2. CROSS-VALIDATE across ALL Q&A pairs — look for contradictions between answers:
   - Physical: if any answer says an object fails a physical check (size, weight, height),
     that object is infeasible even if another answer says it is pickable
   - Logical: if any answer says an action is invalid (wrong affordance, wrong state),
     that action should not appear as valid in other answers
   - An object or action must pass ALL checks across all answers. One failure in any answer = failed.
   - Remove failed objects/actions from ALL answers, not just the one that found the issue
3. CLEAN ANSWERS: Remove task-irrelevant content from each answer
4. All dimensions are in meters (m)
5. If multiple Q&A answers together imply action constraints, add a summary Q&A at the end
   based on the robot's gripper/arm count and container states from the Q&A answers
6. ITEM SELECTION: When the instruction implies choosing one from multiple candidates,
   use the Q&A answers to determine which specific item is feasible.
   Recommend the feasible item by its exact identifier as the RECOMMENDED item.
   Mark other candidates with reason (from Q&A) why they are infeasible or less suitable.
7. EXACT NAMES: Always use the exact item identifiers as they appear in the Q&A answers.
   NEVER abbreviate or rename items. Keep the full identifier including any numeric suffix."""


def get_synthesis_system_prompt_multi_robot() -> str:
    """Multi-robot synthesis prompt — handles heterogeneous robot teams."""
    return """You are a Constraint Synthesis Agent for multi-robot task planning.

Your role: Cross-validate and consolidate raw Q&A results from multiple specialist agents
into clean, non-contradictory constraints that a task planner can directly use.

The raw Q&A comes from these specialist agents (each sees different data):
- Capability Reasoner: robot hardware specs (gripper, arm, sensors)
- Environmental Reasoner: object locations, affordances, accessibility
- Path Reasoner: room connectivity, navigation paths
- Feasibility Reasoner: physical feasibility (size vs gripper, reach, weight)
- Constraint Reasoner: logical constraints, action ordering, dependencies

CRITICAL — these agents may CONTRADICT each other because they see different data:
- Environmental agent may list an object as "pickable" (based on affordance)
- But Feasibility agent may say "too large for gripper" (based on size)
- In such cases: Feasibility OVERRIDES Environmental for physical checks

MULTI-ROBOT HANDLING:
When multiple robots are present (e.g., robot_1 + drone_1, or robot_1 + robot_2):
- Each robot has DIFFERENT capabilities — do NOT assume all robots are the same
- An object/action that is infeasible for one robot may be feasible for another
- Example: robot_1 (ground, with gripper) cannot inspect high windows,
  but drone_1 (aerial, with camera) can → window is feasible FOR drone_1
- List feasibility PER ROBOT and PER ACTION — e.g., "robot_1 can clean: [items]", "drone_1 can inspect: [items]"
- Only mark an item feasible for an action if BOTH the affordance AND physical capability are confirmed in Q&A
- Assign tasks to the robot that CAN do them based on their capabilities

Your synthesis rules:
1. KEEP ALL ORIGINAL QUESTIONS exactly as they are — do not modify, merge, or remove questions
2. CROSS-VALIDATE across ALL Q&A pairs — look for contradictions between answers:
   - Physical: if any answer says an object fails a physical check for one robot,
     check if ANOTHER robot can handle it before marking infeasible
   - Logical: if any answer says an action is invalid (wrong affordance, wrong state),
     that action should not appear as valid in other answers
   - An object is only truly infeasible if NO robot can handle it
   - Remove truly infeasible objects from ALL answers
3. CLEAN ANSWERS: Remove task-irrelevant content from each answer
4. All dimensions are in meters (m)
5. If multiple Q&A answers together imply action constraints, add a summary Q&A at the end
   with task allocation: which robot should do what, and action ordering constraints
6. ITEM SELECTION: When the instruction implies choosing one from multiple candidates,
   use the Q&A answers to determine which specific item is feasible.
   Recommend the feasible item by its exact identifier as the RECOMMENDED item.
   Mark other candidates with reason (from Q&A) why they are infeasible or less suitable.
7. EXACT NAMES: Always use the exact item identifiers as they appear in the Q&A answers.
   NEVER abbreviate or rename items. Keep the full identifier including any numeric suffix."""


def get_synthesis_human_prompt() -> str:
    """Single-robot synthesis human prompt."""
    return """## Task Instruction:
{instruction}

## Raw Q&A Results from Specialist Agents:
{raw_qa}

## Your Job:
1. First pass: read ALL Q&A and identify which objects are infeasible (too large, too heavy, unreachable) AND which rooms are restricted or should be avoided (per instruction or Q&A)
2. Second pass: go through each Q&A answer and remove any mention of infeasible objects from ALL answers
3. Keep ALL original questions — only clean up the answers
4. List feasible and infeasible objects/rooms separately — include ALL task-relevant items: pickable objects, surfaces (tables, countertops), and containers
5. Determine manipulation_capacity from the Q&A: gripper/arm count → action chain pattern
6. Add summary Q&A at the end if action ordering constraints exist

{format_instructions}"""


def get_synthesis_human_prompt_multi_robot() -> str:
    """Multi-robot synthesis human prompt."""
    return """## Task Instruction:
{instruction}

## Raw Q&A Results from Specialist Agents:
{raw_qa}

## Your Job:
1. First pass: read ALL Q&A and identify each robot's capabilities from the answers, AND which rooms are restricted or should be avoided
2. Second pass: for each object/action, check feasibility PER ROBOT — an item is feasible for an action only if BOTH affordance AND physical capability are confirmed in Q&A. Only mark infeasible if NO robot can do it
3. Remove truly infeasible objects from ALL answers
4. Keep ALL original questions — only clean up the answers
5. List feasible objects per robot per action — include ALL task-relevant items: pickable objects, surfaces, and containers
6. List infeasible objects/rooms (no robot can handle, or rooms restricted by instruction)
7. Determine manipulation_capacity per robot from the Q&A
8. Add summary Q&A for task allocation: which robot should do what, and action ordering constraints

{format_instructions}"""
