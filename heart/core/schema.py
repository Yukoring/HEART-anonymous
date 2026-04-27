"""
HEART Schema Definitions

Pydantic models and enums for the HEART pipeline:
- AgentType: 5 expert agents + 3-agent/homogeneous ablation variants
- TaskType: 11 reasoning question categories with semantic descriptions
- AgentResponse: Structured output format with SUCCESS/PARTIAL/OUT_OF_SCOPE status
- SynthesizedConstraints: Cross-validated constraints for planner injection
- TaskPlan / MultiRobotTaskPlan: Planner output schemas
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class AgentType(str, Enum):
    """Available agent types for reasoning"""
    CAPABILITY_REASONER = "capability_reasoner"
    ENVIRONMENTAL_REASONER = "environmental_reasoner"
    PATH_REASONER = "path_reasoner"
    FEASIBILITY_REASONER = "feasibility_reasoner"
    CONSTRAINT_REASONER = "constraint_reasoner"
    # 3-agent ablation (combined-scope agents)
    PHYSICAL_REASONER = "physical_reasoner"
    SPATIAL_REASONER = "spatial_reasoner"

    @property
    def description(self) -> str:
        """Agent role and expertise description"""
        descriptions = {
            "capability_reasoner": (
                "Analyzes robot's action capabilities from state and hardware specifications. "
                "Expert in: Determining what actions the robot can perform, "
                "how many objects it can handle simultaneously (from gripper/arm count), "
                "what actions require free hands (open, close, turn_on, turn_off), "
                "and what hardware limitations affect action combinations. "
                "Data received: Robot state, capability list, parsed URDF specs."
            ),
            "environmental_reasoner": (
                "Understands environment's semantic and functional context through affordances and relationships. "
                "Expert in: Identifying objects by their functional capabilities (affordances), determining what actions "
                "can be performed with objects, understanding container-content relationships (parent/relation), "
                "verifying object accessibility for manipulation, discovering object existence and spatial hierarchy. "
                "Data received: Item affordances, accessibility flags, parent relationships, relation types (in/on)."
            ),
            "path_reasoner": (
                "Calculates room-to-room navigation paths using connectivity graph and identifies robot location. "
                "Expert in: Finding valid paths through room connections, generating multiple route options, "
                "determining shortest paths based on room topology, identifying robot's current room from position coordinates. "
                "Data received: Room connectivity graph (neighbors), room positions and sizes, robot position and location."
            ),
            "feasibility_reasoner": (
                "Determines physical feasibility using robot kinematics and object spatial properties. "
                "Expert in: Calculating if robot can physically reach object positions (x,y,z coordinates), "
                "evaluating gripper-object size compatibility from dimensions, assessing weight limits, "
                "checking height/distance constraints using parsed URDF metrics (max_reach, workspace_height). "
                "Data received: Robot parsed URDF metrics (max_reach, gripper_max_opening, workspace_height_range), "
                "object physical properties (positions, dimensions, weight, material)."
            ),
            "constraint_reasoner": (
                "Validates action ordering through logical rules, object states, robot limitations, and common sense. "
                "Expert in: Checking object affordances for permitted actions, "
                "evaluating object states (open/closed/on/off), "
                "determining action prerequisites (e.g., container must be open before placing items inside), "
                "combining robot hardware limitations with object states to derive required action sequences "
                "(e.g., if robot cannot manipulate while holding items, it must place first), "
                "and inferring implied actions from common sense when the instruction is underspecified "
                "Data received: Object affordances, states, accessibility, robot hardware constraints, original instruction."
            ),
            # 3-agent ablation
            "physical_reasoner": (
                "Analyzes robot hardware capabilities and determines physical feasibility of actions. "
                "Expert in: Determining what actions the robot can perform, "
                "how many objects it can handle simultaneously, what actions require free hands, "
                "calculating physical reachability, evaluating gripper-object size compatibility, "
                "assessing weight limits, and checking height constraints. "
                "Data received: Robot state, parsed URDF specs, "
                "object physical properties (positions, dimensions, weight)."
            ),
            "spatial_reasoner": (
                "Understands environment layout, object locations, and navigation paths. "
                "Expert in: Identifying objects and their locations, "
                "determining object affordances and accessibility, "
                "understanding container-content relationships, "
                "finding valid room-to-room navigation paths, "
                "and identifying robot's current room from position coordinates. "
                "Data received: Scene graph (rooms, items, affordances, neighbors), "
                "robot position."
            ),
        }
        return descriptions.get(self.value, "")
    
class TaskType(str, Enum):
    ROBOT_CAPABILITY_ANALYSIS = "robot_capability_analysis"
    ACTION_VALIDITY = "action_validity"
    OBJECT_DISCOVERY = "object_discovery"
    SCENE_UNDERSTANDING = "scene_understanding"
    ROBOT_DISCOVERY = "robot_discovery"
    PATH_PLANNING = "path_planning"
    ROUTE_OPTIMIZATION = "route_optimization"
    PHYSICAL_FEASIBILITY = "physical_feasibility"
    TASK_DEPENDENCY_ANALYSIS = "task_dependency_analysis"
    ACTION_SEQUENCE_CONSTRAINTS = "action_sequence_constraints"
    CONTEXTUAL_CONSTRAINTS = "contextual_constraints"

    @property
    def description(self) -> str:
        """Semantic description of the task type"""
        descriptions = {
            "robot_capability_analysis": "Identify robot's capabilities and multi-manipulation capacity (actions possible and how many objects simultaneously)",
            "action_validity": "Verify if specific robot-object-action combination is possible (capability AND affordance check)",
            "object_discovery": "Find specific objects, their exact locations, container relationships, and affordances",
            "scene_understanding": "Understand room-object relationships and general environment: what items are in which rooms, room purposes",
            "robot_discovery": "Determine robot's current room from its position coordinates",
            "path_planning": "Generate ALL valid room-to-room navigation paths using ONLY neighbor connections (must verify connectivity)",
            "route_optimization": "Select the BEST path from multiple valid paths (all must use neighbor connections) based on distance or efficiency",
            "physical_feasibility": "Calculate if manipulation is physically possible using exact positions and dimensions",
            "task_dependency_analysis": "Extract action rules (prerequisites) and action dependencies from instruction",
            "action_sequence_constraints": "Determine required action ordering from instruction and logic",
            "contextual_constraints": "Identify implicit rules from context and map relevant objects by their constraint-related (state) properties"
        }
        return descriptions.get(self.value, "")
    
    @property
    def response_strategy(self) -> str:
        """Response strategy and format for each TaskType"""
        strategies = {
            "robot_capability_analysis": 
                "Analyze robot capabilities with pattern matching:\n"
                "- Specific robot: 'robot_1 CAPABILITIES: [navigate, pick, place, push, pull] | HARDWARE: gripper=1, arms=1, mobile=yes | CAPACITY: 1 object at once (Need to place before pick, open, ....)'\n"
                "- Multiple robots: List each robot's distinct capabilities and limitations\n"
                "- Capability query: 'Robots with pick capability: [robot_1, robot_2] | Without: [robot_3-no_gripper]'",
            "action_validity": 
                "Check robot-object-action validity with pattern matching:\n"
                "- Specific (robot_1, object_5, pick): 'robot_1 CAN pick object_5 (has validity (position, size, weight, ...) + affordance match)'\n"
                "- Object wildcard (robot_1, *, pick): 'robot_1 CAN pick: [apple_2, bowl_3] | CANNOT pick: [table_1-no_affordance, ball_4-too high to reach]'\n"  
                "- Robot wildcard (*, object_5, pick): 'robot_1 CAN pick object_5 | robot_2 CANNOT pick object_5 (no gripper)'\n"
                "- Double wildcard (*, *, pick): List all valid robot-object pairs for action",
            "object_discovery": 
                "Find objects with flexible queries:\n"
                "- Specific object: 'apple_5: LOCATION: kitchen_9 (on table_3) | AFFORDANCES: [pick, place] | STATE: accessible'\n"
                "- Object type: 'All apples: {apple_5: kitchen_9, apple_7: dining_12}'\n"
                "- By property: 'Objects with open affordance: [cabinet_2, door_3] | Closed state: [cabinet_2, refrigerator_4]'",
            "scene_understanding": 
                "Map spatial relationships at different granularities:\n"
                "- Room inventory: 'kitchen_9: [sink_1, table_3, apple_5, bowl_2] | bedroom_4: [bed_1, lamp_2]'\n"  
                "- Object relations: 'ON: {apple_5: table_3, bowl_2: sink_1} | IN: {pen_4: drawer_2}'\n"
                "- Room purposes: 'cooking: kitchen_9 | sleeping: bedroom_4 | hygiene: bathroom_3'",
            "robot_discovery": 
                "Locate robots with flexible queries:\n"
                "- Specific robot: 'robot_1: ROOM: kitchen_9 | POSITION: [1.2, 3.4, 0] | STATUS: idle'\n"
                "- All robots: 'ROBOTS: {robot_1: kitchen_9, robot_2: dining_3, robot_3: corridor_7}'\n"
                "- By room: 'Robots in kitchen: [robot_1, robot_4] | No robots in: [bedroom_2, bathroom_5]'",
            "path_planning": 
                "Generate navigation paths under constraints:\n"
                "You should mention whether they have direct path or not\n"
                "- Simple path: 'A and C do not have direct path: A->B->C (each step must follow valid adjacency) / A and C have direct path: A->C'\n"
                "- Multiple paths: 'A and C do not have direct path: PATHS: [A->B->C, A->D->E->C]'\n"
                "- With waypoint: 'A and C have direct path but need to visit X: Via X: A->Y->X->Z->C'",
            "route_optimization": 
                "Select shortest valid path:\n"
                "- Compare paths: 'Path1: kitchen->corridor->bedroom (2 hops) | Path2: kitchen->dining->bedroom (2 hops)'\n"
                "- Choose shortest: 'OPTIMAL: kitchen->corridor->bedroom (2 hops is shortest)'",
            "physical_feasibility": 
                "Assess physical constraints for manipulation (reachable for only height):\n"
                "- Single object: 'apple_5: Pickable: yes (z=0.8m < max_height=2.2m, min_size=0.05m < gripper=0.1m, weight=0.2kg < capacity=3kg)'\n"
                "- Multiple objects: 'PICKABLE: [apple_5, pen_3] | NOT_PICKABLE: [ball_2-too_high(2.4m), notebook_64-too_high(2.4m)]'\n"
                "- By constraint: 'Within height reach (<2.2m): [table_items, floor_items] | Too heavy (>3kg): [microwave_4, chair_2]'",
            "task_dependency_analysis": 
                "Identify action dependencies and hardware constraints. "
                "Format: 'DEPENDENCIES: "
                "{action1: [prerequisites], action2: [prerequisites]}' + "
                "'CONSTRAINTS: [holding object blocks new picks (1 gripper), dual arms allow parallel actions]'"
                "Example: {pick_object}: [Need to place object if robot is holding something], {open_cabinet}: [Need to place object if robot is holding something], {place_apple}: [Need to pick up apple already]"
                "'CONSTRAINTS: [holding object blocks open (1 gripper)]'",
            "action_sequence_constraints": 
                "Define PARTIAL action ordering (NOT complete plan):\n"
                "- Linear sequence: 'MUST: navigate_to_object (might be several hops) -> pick -> navigate_to_target -> place'\n"
                "- Gripper constraints: 'BLOCKED_WHILE_HOLDING: [open, close, pick_another] - must place first for hand free'\n"
                "- Conditional: 'IF holding_object THEN cannot [open_door, close_cabinet] | IF cabinet_closed THEN open_before_pick'\n"
                "- Parallel allowed: 'PARALLEL_OK: [pick_left, pick_right] ONLY if dual_gripper'",
            "contextual_constraints": 
                "Extract implicit rules from context:\n"
                "- State-based: 'CLOSED_CONTAINERS: [cabinet_2, drawer_3] - require opening first'\n"
                "- Action-based: 'OPEN: [open_object] - requires hands free'\n"
                "- Safety rules: 'FRAGILE: [glass_5, vase_3] - handle with care | HOT: [stove_2] - avoid when on'\n"
                "- Access rules: 'BLOCKED: [item_in_cabinet] - need container open | FREE: [table_items]'"
        }
        return strategies.get(self.value, "Provide answer based on task instruction requirements")

# ==================== Type Ablation Variants (response letter only) ====================

class TaskType8(str, Enum):
    """8-type variant: merge similar types"""
    HARDWARE_ANALYSIS = "hardware_analysis"          # capability + validity
    OBJECT_DISCOVERY = "object_discovery"
    SCENE_UNDERSTANDING = "scene_understanding"
    ROBOT_DISCOVERY = "robot_discovery"
    NAVIGATION = "navigation"                        # path + route
    PHYSICAL_FEASIBILITY = "physical_feasibility"
    TASK_DEPENDENCY = "task_dependency"
    ACTION_CONSTRAINTS = "action_constraints"         # sequence + contextual

    @property
    def description(self) -> str:
        descriptions = {
            "hardware_analysis": "Identify robot capabilities, verify robot-object-action validity, and check multi-manipulation capacity",
            "object_discovery": "Find specific objects, their exact locations, container relationships, and affordances",
            "scene_understanding": "Understand room-object relationships and general environment: what items are in which rooms",
            "robot_discovery": "Determine robot's current room from its position coordinates",
            "navigation": "Generate valid room-to-room navigation paths using neighbor connections and select the best route",
            "physical_feasibility": "Calculate if manipulation is physically possible using exact positions and dimensions",
            "task_dependency": "Extract action rules (prerequisites) and action dependencies from instruction",
            "action_constraints": "Determine required action ordering and identify implicit rules from context and object states",
        }
        return descriptions.get(self.value, "")

    @property
    def response_strategy(self) -> str:
        strategies = {
            "hardware_analysis":
                "List the robot's hardware specs (gripper count, arm count, capacity) and determine which actions are valid for which objects:\n"
                "- 'robot_1: gripper=1, arms=1, CAPACITY=1 object | CAN pick: [apple_2, bowl_3] | CANNOT pick: [table_1-no_affordance, ball_4-too_high]'",
            "object_discovery":
                "Find objects with flexible queries:\n"
                "- Specific object: 'apple_5: LOCATION: kitchen_9 (on table_3) | AFFORDANCES: [pick, place] | STATE: accessible'\n"
                "- Object type: 'All apples: {apple_5: kitchen_9, apple_7: dining_12}'\n"
                "- By property: 'Objects with open affordance: [cabinet_2, door_3] | Closed state: [cabinet_2, refrigerator_4]'",
            "scene_understanding":
                "Map spatial relationships at different granularities:\n"
                "- Room inventory: 'kitchen_9: [sink_1, table_3, apple_5, bowl_2] | bedroom_4: [bed_1, lamp_2]'\n"
                "- Object relations: 'ON: {apple_5: table_3, bowl_2: sink_1} | IN: {pen_4: drawer_2}'\n"
                "- Room purposes: 'cooking: kitchen_9 | sleeping: bedroom_4 | hygiene: bathroom_3'",
            "robot_discovery":
                "Locate robots with flexible queries:\n"
                "- Specific robot: 'robot_1: ROOM: kitchen_9 | POSITION: [1.2, 3.4, 0] | STATUS: idle'\n"
                "- All robots: 'ROBOTS: {robot_1: kitchen_9, robot_2: dining_3}'\n"
                "- By room: 'Robots in kitchen: [robot_1] | No robots in: [bedroom_2]'",
            "navigation":
                "Find the robot's valid paths through neighboring rooms and pick the shortest one:\n"
                "- 'A to C: A->B->C (2 hops) vs A->D->E->C (3 hops) | OPTIMAL: A->B->C'",
            "physical_feasibility":
                "Check whether the robot can physically reach and manipulate each object given height, size, and weight limits:\n"
                "- 'PICKABLE: [apple_5 (z=0.8m OK, size=0.05m OK)] | NOT_PICKABLE: [ball_2 (z=2.4m > reach), notebook_64 (too heavy)]'",
            "task_dependency":
                "List what must happen before each action can execute:\n"
                "- 'DEPENDENCIES: {pick: [hand free], open_cabinet: [place held item], place_in: [container open]}'",
            "action_constraints":
                "Determine the required action order and identify implicit rules from object states:\n"
                "- 'ORDER: navigate -> pick -> navigate -> place | RULES: must drop before open, closed containers need opening first'",
        }
        return strategies.get(self.value, "Provide answer based on task requirements")


class TaskType5(str, Enum):
    """5-type variant: maximally merged"""
    HARDWARE_CHECK = "hardware_check"                # capability + validity
    SCENE_QUERY = "scene_query"                      # object_discovery + scene_understanding
    SPATIAL_REASONING = "spatial_reasoning"           # robot_discovery + path + route
    FEASIBILITY_CHECK = "feasibility_check"          # physical_feasibility
    CONSTRAINT_ANALYSIS = "constraint_analysis"      # dependency + sequence + contextual

    @property
    def description(self) -> str:
        descriptions = {
            "hardware_check": "Identify robot capabilities, verify robot-object-action validity, and check manipulation capacity",
            "scene_query": "Find objects, their locations, affordances, container relationships, and understand room-object spatial layout",
            "spatial_reasoning": "Determine robot positions, generate valid navigation paths through room connections, and optimize routes",
            "feasibility_check": "Calculate if manipulation is physically possible using positions, dimensions, weight, and reach",
            "constraint_analysis": "Extract action dependencies, determine required ordering, and identify implicit rules from context and object states",
        }
        return descriptions.get(self.value, "")

    @property
    def response_strategy(self) -> str:
        strategies = {
            "hardware_check":
                "List the robot's hardware specs and determine which actions are valid for which objects:\n"
                "- 'robot_1: gripper=1, arms=1, CAPACITY=1 object | CAN pick: [apple_2, bowl_3] | CANNOT: [table_1-no_affordance]'",
            "scene_query":
                "Find objects and describe the room layout:\n"
                "- 'apple_5: kitchen_9 (on table_3), affordances=[pick, place] | kitchen_9 contains: [sink_1, table_3, apple_5]'",
            "spatial_reasoning":
                "Determine where each robot is and find the shortest valid path to the destination:\n"
                "- 'robot_1 is in kitchen_9 | Path to bedroom: kitchen_9->corridor->bedroom (2 hops, shortest)'",
            "feasibility_check":
                "Check whether the robot can physically reach and manipulate each object given height, size, and weight limits:\n"
                "- 'PICKABLE: [apple_5 (z=0.8m OK, size=0.05m OK)] | NOT_PICKABLE: [ball_2 (z=2.4m > reach)]'",
            "constraint_analysis":
                "List what must happen before each action and determine the required order considering object states:\n"
                "- 'DEPS: {pick: [hand free], open: [drop held item]} | ORDER: navigate->pick->navigate->place | closed containers need opening first'",
        }
        return strategies.get(self.value, "Provide answer based on task requirements")


# Mapping from TaskType (11) to reduced types
TASK_TYPE_MAPPING_8 = {
    "robot_capability_analysis": "hardware_analysis",
    "action_validity": "hardware_analysis",
    "object_discovery": "object_discovery",
    "scene_understanding": "scene_understanding",
    "robot_discovery": "robot_discovery",
    "path_planning": "navigation",
    "route_optimization": "navigation",
    "physical_feasibility": "physical_feasibility",
    "task_dependency_analysis": "task_dependency",
    "action_sequence_constraints": "action_constraints",
    "contextual_constraints": "action_constraints",
}

TASK_TYPE_MAPPING_5 = {
    "robot_capability_analysis": "hardware_check",
    "action_validity": "hardware_check",
    "object_discovery": "scene_query",
    "scene_understanding": "scene_query",
    "robot_discovery": "spatial_reasoning",
    "path_planning": "spatial_reasoning",
    "route_optimization": "spatial_reasoning",
    "physical_feasibility": "feasibility_check",
    "task_dependency_analysis": "constraint_analysis",
    "action_sequence_constraints": "constraint_analysis",
    "contextual_constraints": "constraint_analysis",
}

# ====================================================================================


class ReasoningQuestion(BaseModel):
    """A reasoning question generated by decomposer"""
    model_config = ConfigDict(use_enum_values=True)
    
    question_id: str = Field(..., description="Unique question identifier (e.g., Q1, Q2)")
    question_type: TaskType = Field(..., description="Type of reasoning question") 
    prompt: str = Field(..., description="Clear, specific question for an agent to answer")
    rationale: str = Field(..., description="Why this question is needed for the task")
    priority: Optional[int] = Field(
        default=1, 
        description="Question priority (1=highest, lower numbers = higher priority)"
    )

class QuestionDecomposition(BaseModel):
    """Result of decomposing an instruction into reasoning questions"""
    model_config = ConfigDict(use_enum_values=True)
    
    instruction: str = Field(..., description="Original instruction")
    questions: List[ReasoningQuestion] = Field(..., description="List of reasoning questions with individual rationales")
    
class AgentTask(BaseModel):
    """
    Unified task structure for all agents
    
    All agents receive the same structure:
    - query: The main content to process (instruction/question)
    - metadata: Additional information
    
    Note: env_data is now stored in agent's filtered_env_data at initialization
    """
    model_config = ConfigDict(use_enum_values=True)
    task_id: str = Field(..., description="Task identifier")
    query: str = Field(..., description="The main query/instruction/question to process")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (task_type, operation, expected_outputs, etc.)"
    )


class TaskAllocation(BaseModel):
    """Single task allocation with reasoning"""
    model_config = ConfigDict(use_enum_values=True)
    task_id: str = Field(..., description="Task identifier")
    assigned_agent: AgentType = Field(..., description="Agent type assigned to this task")
    reasoning: str = Field(..., description="Why this agent was chosen for this task")

class AgentOutputStatus(str, Enum):
    SUCCESS = "success"  # Complete answer with verified data
    PARTIAL = "partial"  # Partial answer, needs additional information
    OUT_OF_SCOPE = "out_of_scope"  # Outside this agent's expertise/data


class AgentResponse(BaseModel):
   """Response format for all reasoning agents"""
   
   original_question: str = Field(..., description="The question that was asked")
   
   status: AgentOutputStatus = Field(..., description="Response status")
   
   answer_content: str = Field(
       ..., 
       description="Answer based on verified data only, never guess or assume but provide all relevant information as you can.\n" \
       "If you don't know the exact answer, give the all relevant data or information you have for next agent."

   )
   
   follow_up_question: Optional[str] = Field(
       default=None,
       description="What additional information is needed? Make the follow-up a question the agent can handle within tasktype (data) (only for PARTIAL or OUT_OF_SCOPE)"
   )
   
   follow_up_task_type: Optional[TaskType] = Field(
       default=None,
       description="Task type for the follow-up question (only for PARTIAL or OUT_OF_SCOPE)"
   )
   
   reasoning: str = Field(..., description="Agent's reasoning process and key considerations")



class SynthesizedQA(BaseModel):
    """Single synthesized Q&A pair — original question preserved, answer cross-validated"""
    question: str = Field(..., description="Original question exactly as asked — do NOT modify")
    answer: str = Field(..., description="Cross-validated answer — contradictions resolved, irrelevant info removed, task-relevant only")


class SynthesizedConstraints(BaseModel):
    """Output of synthesis agent — cross-validated, deduplicated constraints"""

    feasible_objects: List[str] = Field(
        ...,
        description="Objects that CAN be handled. For multi-robot: include which robot can do it."
    )

    infeasible_objects: List[str] = Field(
        ...,
        description="Objects that NO robot can handle and why, AND rooms that should not be entered (e.g., restricted, blocked, or instructed to avoid)"
    )

    manipulation_capacity: str = Field(
        ...,
        description="Per-robot capability summary: gripper/arm count, max objects held, action chain pattern. For multi-robot: describe each robot separately. 'N/A' if no manipulation."
    )

    constraints: List[SynthesizedQA] = Field(
        ...,
        description="ALL original Q&A pairs with cross-validated answers. Keep every original question. Only clean up the answers."
    )


class TaskPlan(BaseModel):
    """Plan synthesis output format for LLM-as-Planner and other baseline methods"""

    chain_of_thought: str = Field(
        ...,
        description="Break down the problem into intermediate reasoning steps. Think carefully about plan feasibility and valid navigation."
    )

    reasoning: str = Field(
        ...,
        description="Justify why the planned actions are important and correct. Also think about violating the rules or constraints."
    )

    plan: List[str] = Field(
        ...,
        description="List of High-level task plan consisting of executable robot actions. Think carefully about plan feasibility and valid navigation."
    )


class RobotPlan(BaseModel):
    """Individual robot's plan in a multi-robot scenario"""

    robot_id: str = Field(
        ...,
        description="Robot identifier (e.g., robot_1, drone_1)"
    )

    robot_type: str = Field(
        ...,
        description="Type of robot (e.g., mobile_manipulator, quadrotor)"
    )

    task_description: str = Field(
        ...,
        description="Brief description of what this robot will do"
    )

    actions: List[str] = Field(
        ...,
        description="Ordered list of actions for this specific robot"
    )


class MultiRobotTaskPlan(BaseModel):
    """Multi-robot plan synthesis output format"""

    chain_of_thought: str = Field(
        ...,
        description="Break down the problem considering multiple robots. Identify which robot should handle which subtask based on capabilities."
    )

    task_allocation: str = Field(
        ...,
        description="Explain how tasks are divided between robots and why this allocation is efficient."
    )

    robot_plans: List[RobotPlan] = Field(
        ...,
        description="Individual plans for each robot"
    )

    coordination_notes: Optional[str] = Field(
        default="",
        description="Notes about timing, dependencies, or coordination between robots if needed"
    )


