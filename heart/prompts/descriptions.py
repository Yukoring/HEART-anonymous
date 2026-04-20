"""
Centralized Descriptions

Shared text descriptions for TaskTypes and AgentTypes used across prompts
(decomposition, allocation, reasoning) to ensure consistent terminology.
Also provides response strategy templates that guide each agent's output format.
"""

from typing import Dict, Set, List
from heart.core.schema import TaskType, AgentType


def get_task_type_descriptions() -> str:
    """
    Get descriptions of all task types from schema
    
    Returns:
        Formatted string with all task type descriptions
    """
    descriptions = []
    for task_type in TaskType:
        descriptions.append(f"- **{task_type.value}**: {task_type.description}")
    
    return "\n".join(descriptions)


def get_task_type_description(task_type: str) -> str:
    """
    Get description for a specific task type
    
    Args:
        task_type: Task type string value
        
    Returns:
        Description string for the task type
    """
    try:
        task_type_enum = TaskType(task_type)
        return task_type_enum.description
    except ValueError:
        return f"Unknown task type: {task_type}"


def get_agent_type_descriptions() -> str:
    """
    Get descriptions of all agent types from schema
    
    Returns:
        Formatted string with all agent type descriptions
    """
    descriptions = []
    for agent in AgentType:
        descriptions.append(f"""
**{agent.value.upper()}**:
{agent.description}
""")
    
    return "\n".join(descriptions)


def get_agent_description(agent_type: str) -> str:
    """
    Get description for a specific agent type
    
    Args:
        agent_type: Agent type string value
        
    Returns:
        Description string for the agent type
    """
    try:
        agent_enum = AgentType(agent_type)
        return agent_enum.description
    except ValueError:
        return f"Unknown agent type: {agent_type}"


def get_task_response_strategy(task_type: str) -> str:
    """
    Get response strategy for a specific task type
    
    Args:
        task_type: Task type string value
        
    Returns:
        Response strategy string for the task type
    """
    try:
        task_type_enum = TaskType(task_type)
        return task_type_enum.response_strategy
    except ValueError:
        return "Provide best available information"


# Affordance to Robot Action Mapping
AFFORDANCE_ACTION_MAP: Dict[str, str] = {
    # Basic manipulation
    'pick_up': "pick(<robot>, <item>): Pick up an item",
    'grab': "grab(<robot>, <item>): Grab an item firmly",  
    'hold': "hold(<robot>, <item>): Hold an item in gripper",
    'move': "move(<robot>, <item>, <location>): Move item to location",
    'place': "place(<robot>, <item>, <location>): Place held item at location",
    
    # Container operations
    'open': "open(<robot>, <container>): Open a container or door",
    'close': "close(<robot>, <container>): Close a container or door",
    'fill': "fill(<robot>, <container>, <liquid>): Fill container with liquid",
    
    # Appliance operations
    'turn_on': "turn_on(<robot>, <appliance>): Turn on an appliance",
    'turn_off': "turn_off(<robot>, <appliance>): Turn off an appliance",
    'set_on': "set_on(<robot>, <item>, <surface>): Set item on surface",
    'set': "set(<robot>, <appliance>, <setting>): Set appliance to specific setting",
    
    # Kitchen/cooking actions
    'cook': "cook(<robot>, <food>, <appliance>): Cook food using appliance",
    'heat': "heat(<robot>, <item>, <appliance>): Heat item using appliance",
    'peel': "peel(<robot>, <fruit>): Peel fruit or vegetable",
    'defrost': "defrost(<robot>, <frozen_item>): Defrost frozen item",
    'make': "make(<robot>, <recipe>, <ingredients>): Make something from ingredients",
    'break': "break(<robot>, <item>): Break item (e.g., eggs)",
    
    # Cleaning actions
    'clean': "clean(<robot>, <item>): Clean an item or surface",
    'wash': "wash(<robot>, <item>): Wash item with water",
    'flush': "flush(<robot>, <toilet>): Flush toilet",
    'tidy': "tidy(<robot>, <area>): Tidy up an area",
    'water': "water(<robot>, <plant>): Water a plant",
    
    # Consumption actions
    'eat': "eat(<robot>, <food>): Robot simulates eating (for demo)",
    'eat_from': "eat_from(<robot>, <container>): Eat from container",
    'bite': "bite(<robot>, <food>): Take a bite of food",
    
    # Sitting/positioning actions
    'sit_on': "sit_on(<robot>, <furniture>): Position robot on furniture",
    'sit_at': "sit_at(<robot>, <table>): Position robot at table",
    'lay_on': "lay_on(<robot>, <item>, <surface>): Lay item on surface",
    'step_on': "step_on(<robot>, <surface>): Step onto surface",
    
    # Misc actions
    'throw_away': "throw_away(<robot>, <item>): Dispose item in trash",
    'through_away': "throw_away(<robot>, <item>): Dispose item in trash",  # Handle typo
    'decorate': "decorate(<robot>, <item>, <decoration>): Decorate item"
}


def get_robot_actions_from_affordances(affordances: Set[str]) -> List[str]:
    """
    Get available robot actions based on affordances in scene
    
    Args:
        affordances: Set of affordance strings from scene graph
        
    Returns:
        List of robot action descriptions
    """
    actions = [
        "Available Robot Actions:",
        "- navigate(<robot>, <room>): Move robot to a connected room"  # Always available
    ]
    
    # Add actions based on found affordances
    for affordance in sorted(affordances):
        if affordance in AFFORDANCE_ACTION_MAP:
            action = AFFORDANCE_ACTION_MAP[affordance]
            action_with_dash = f"- {action}"
            if action_with_dash not in actions:
                actions.append(action_with_dash)
    
    # Always include basic pick and place if any manipulation affordances exist
    if any(aff in affordances for aff in ['pick_up', 'grab', 'hold', 'move']):
        place_action = "- place(<robot>, <item>, <location>): Place held item at location"
        if place_action not in actions:
            actions.append(place_action)
    
    return actions


def get_all_possible_robot_actions() -> List[str]:
    """
    Get all possible robot actions (for reference/documentation)
    
    Returns:
        List of all robot action descriptions
    """
    actions = [
        "All Possible Robot Actions:",
        "- navigate(<robot>, <room>): Move robot to a connected room"
    ]
    
    for affordance, action in sorted(AFFORDANCE_ACTION_MAP.items()):
        if affordance != 'through_away':  # Skip typo variant
            actions.append(f"- {action}")
    
    return actions