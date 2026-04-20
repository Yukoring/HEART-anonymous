"""
LLM-CoT Planner Prompts

Prompt templates defining available robot actions, constraints, and few-shot
examples for the LLM chain-of-thought planner. Three prompt variants:
- Single robot: 8 actions (navigate, pick, pick_from, place, drop, open, close, turn_on/off)
- Drone only: 2 actions (navigate, check)
- Multi-robot: 10 actions including check for aerial robots

Key constraints enforced via prompts:
- Hand-free requirement for manipulation actions (open, close, turn_on/off)
- Drop preferred over place for freeing hands mid-task
- Room-by-room navigation using neighbor connections only
"""

def get_llm_as_planner_prompt() -> str:
    """
    Get LLM-as-Planner prompt template with embedded examples
    
    Returns:
        Prompt template string with variables:
        - {scene}: Scene graph for the query task  
        - {query}: Task instruction
        - {additional_actions}: Optional additional domain-specific actions
        - {format_instructions}: Parser format instructions
    """
    return """
You are a robot task planner. Given a scene graph and an instruction, generate an executable action plan.

Available Robot Actions with Constraints:

1. navigate(<robot>, <room>, <room>): Move robot to a connected room
   - Precondition: Rooms must be connected
   - Effect: Robot location changes to target room
   - Note: Robot keeps any held items during navigation
           Rooms must be neighboring to connect in Scene Graph.

2. pick(<robot>, <item>): Pick up an item in the current room
   - Precondition: 
     * Item must be in robot's current room
     * Item must be reachable (on floor or accessible surface)
     * Robot must have a free gripper/hand
     * If robot has only ONE arm: Cannot pick if already holding something
     * If robot has TWO arms: Can hold up to 2 items simultaneously — pick multiple items before navigating to minimize trips
   - Effect: Item is now held by robot (occupies one gripper)
   - IMPORTANT: If already holding item(s), must PLACE before picking new item (for single-arm robots)

3. pick_from(<robot>, <item>, <container>): Pick an item from inside a container (e.g., fridge, dishwasher)
   - Precondition:
     * Item must be INSIDE the container (not just in the same room)
     * Container must be open
     * Robot must have a free gripper/hand
   - Effect: Item is taken out of the container and held by robot
   - Use ONLY when the item is inside a container. For items on surfaces or floor, use regular pick.

4. place(<robot>, <item>, <surface or container>): Place held item on a surface or into a container
   - Precondition:
     * Robot must be holding the item
     * Target must be a surface (e.g., table, countertop) or container (e.g., briefcase, fridge, dishwasher)
     * Target must be in robot's current room
   - Effect: Item is placed on/in target, gripper becomes free
   - NOTE: Only use place when there is a valid surface or container. If no valid target exists, use drop instead.

5. drop(<robot>, <item>, <room>): Release held item in the specified room (no target needed)
   - Precondition:
     * Robot must be holding the item
     * Robot must be in <room>
   - Effect: Item is dropped in <room>, gripper becomes free
   - Use when: Robot needs to free its hand before performing manipulation actions (open, close, turn_on, turn_off)

6. open(<robot>, <container object>): Open a container object
   - Precondition:
     * Container must have 'open' affordance
     * Container must be in robot's current room
     * Robot must have at least one free hand (**********CANNOT open while holding items with all grippers**********)
   - Effect: Container becomes open
   - IMPORTANT: Drop or place any held items first if hands are full

7. close(<robot>, <container object>): Close a container object
   - Precondition:
     * Container must have 'close' affordance
     * Container must be in robot's current room
     * Container must be currently open
     * Robot must have at least one free hand (**********CANNOT close while holding items with all grippers**********)
   - Effect: Container becomes closed
   - IMPORTANT: Drop or place any held items first if hands are full

8. turn_on/turn_off(<robot>, <appliance>): Operate an appliance
   - Precondition:
     * Appliance must be in robot's current room
     * Robot should have at least one free hand for safety

Key Constraints to Remember:
- Single-arm robots: Can hold MAX 1 item at a time. Must drop before picking another.
- Dual-arm robots: Can hold MAX 2 items. Must drop at least one before picking a third.
- Manipulation actions (open/close/turn_on/turn_off): Require at least one free hand.
- When you need to free a hand for manipulation (open, close, turn_on, turn_off), always use DROP — not place.
- Use PLACE only for the final goal placement (e.g., placing item on the target surface/container).

## Example 1 - Simple Pick and Place:
Instruction: "Bring an object_1 to the object_2"

Scene: 
- room_1 contains object_1 (pickable)
- room_5 contains object_2
- Rooms connected: room_1 <-> room_5
- Robot is in room_1

Plan:
```
pick(robot object_1)
navigate(robot room_1 room_5)
place(robot object_1 object_2)
```

## Example 2 - Task with Container:
Instruction: "Put the book in the cabinet from the bed."

Scene:
- room_3 contains desk_3 and cabinet_4 (closed, openable)
- Robot and bed are in room_2 (connected to room_3)
- book_12 is on the bed_8

Valid Plan:
```
pick(robot book_12)
navigate(robot room_2 room_3)
drop(robot book_12 room_3) - Drop the book to free hand before opening cabinet
open(robot cabinet_4)
pick(robot book_12)
place(robot book_12 cabinet_4)
close(robot cabinet_4)
```

Invalid Plan:
```
pick(robot book_12)
navigate(robot room_2 room_3)
open(robot cabinet_4) - WRONG: Cannot open while holding item — must drop first
place(robot book_12 cabinet_4)
close(robot cabinet_4)
```

## Your Task:
Instruction: {query}

Scene Graph:
{scene}

Robot Data:
{robot}

Additional Constraints:
{additional_information}

Generate a plan to complete the instruction. 
Think step-by-step:
Use the provided scene/URDF info and Additional Constraints for internal reasoning with final structured plan.
Think about the status of held items and robot hands status at each step (refer to the previous steps).
Every navigate action must be grounded in the neighboring room connections.
Final structured plan should NOT violate additional constraints.
Use Drop action rather than Place if robot needs to free its hand even if there is a valid surface or container nearby.
Please USE Chain-of-Thought Reasoning for Planning!!!

{format_instructions}
"""


def get_llm_as_planner_drone_prompt() -> str:
    """
    Get LLM-as-Planner prompt template for drone-only (aerial) single-robot tasks.
    Drones have no manipulation capability — only fly and observe/check.

    Returns:
        Prompt template string with the same variables as get_llm_as_planner_prompt.
    """
    return """
You are an aerial robot (drone) task planner. Given a scene graph and an instruction, generate an executable flight and inspection plan.

Available Drone Actions with Constraints:

1. navigate(<drone>, <room>, <room>): Fly from one room to a neighboring room
   - Precondition: Rooms must be connected (neighbor) in the scene graph
   - Effect: Drone location changes to target room

2. check(<drone>, <item>): Visually inspect an item in the current room
   - Precondition:
     * Item must be in drone's current room
     * Drone must have a camera (refer to robot data)
   - Effect: Information about the item's state is obtained (item becomes "checked")

## Example 1 - Single-room Inspection:
Instruction: "Check object_1"

Scene:
- room_1 contains object_1
- Drone is in room_2 (connected to room_1)

Plan:
```
navigate(drone_1 room_2 room_1)
check(drone_1 object_1)
```

## Example 2 - Multi-room Survey:
Instruction: "Check object_1 and object_2"

Scene:
- room_1 contains object_1
- room_3 contains object_2
- Rooms connected: room_1 <-> room_2 <-> room_3
- Drone is in room_1

Plan:
```
check(drone_1 object_1)
navigate(drone_1 room_1 room_2)
navigate(drone_1 room_2 room_3)
check(drone_1 object_2)
```

## Your Task:
Instruction: {query}

Scene Graph:
{scene}

Robot Data:
{robot}

Additional Constraints:
{additional_information}

Generate a plan to complete the instruction.
Think step-by-step:
Use the provided scene/URDF info and Additional Constraints for internal reasoning with final structured plan.
Every navigate action must be grounded in the neighboring room connections.
Final structured plan should NOT violate additional constraints.
Please USE Chain-of-Thought Reasoning for Planning!!!

{format_instructions}
"""


def get_llm_as_planner_multi_robot_prompt() -> str:
    """
    Get LLM-as-Planner prompt template for multi-robot scenarios

    Returns:
        Prompt template string with variables:
        - {scene}: Scene graph for the query task
        - {query}: Task instruction
        - {additional_actions}: Optional additional domain-specific actions
        - {format_instructions}: Parser format instructions
    """
    return """
You are a multi-robot task planner. Given a scene graph and an instruction, generate an executable action plan for multiple robots working together.

Available Robot Actions with Constraints:

1. navigate(<robot_id>, <room>, <room>): Move specific robot to a connected room
   - Precondition: Rooms must be connected (for ground robots) or within flight range (for aerial robots)
   - Effect: Specified robot's location changes to target room
   - Note: Robot keeps any held items during navigation
           ALL robots (ground and aerial) must navigate room-by-room using neighboring connections

2. pick(<robot_id>, <item>): Specific robot picks up an item
   - Precondition:
     * Item must be in robot's current room
     * Item must be reachable by THIS robot type (check robot capabilities)
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
     * Robot must have a free gripper/hand
     * If robot has only ONE arm: Cannot pick if already holding something
     * If robot has TWO arms: Can hold up to 2 items simultaneously — pick multiple items before navigating to minimize trips
   - Effect: Item is now held by specified robot (occupies one gripper)
   - IMPORTANT: Aerial robots (drones) CANNOT pick items

3. pick_from(<robot_id>, <item>, <container>): Pick an item from inside a container
   - Precondition:
     * Item must be inside the container (not just in the same room)
     * Container must be open
     * Robot must have a free gripper/hand
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
   - Effect: Item is taken out of container, held by robot
   - Use when: Item is stored inside a container (e.g., glass inside dishwasher, cheese inside fridge)

4. place(<robot_id>, <item>, <surface or container>): Specific robot places held item
   - Precondition:
     * Specified robot must be holding the item
     * Target must be a surface (e.g., table, countertop) or container (e.g., briefcase, fridge, dishwasher)
     * Target must be in robot's current room
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
   - Effect: Item is placed on/in target, gripper becomes free
   - NOTE: Only use place when there is a valid surface or container. If no valid target exists, use drop instead.
   - CRITICAL: Aerial robots (drones) CANNOT place items

5. drop(<robot_id>, <item>, <room>): Release held item in the specified room (no target needed)
   - Precondition:
     * Robot must be holding the item
     * Robot must be in <room>
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
   - Effect: Item is dropped in <room>, gripper becomes free
   - Use when: Robot needs to free its hand before performing manipulation actions (open, close, turn_on, turn_off)

6. open(<robot_id>, <container object>): Specific robot opens a container
   - Precondition:
     * Container must have 'open' affordance
     * Container must be in robot's current room
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
     * Robot's gripper must be free (not holding items)
   - Effect: Container state changes to 'opened'
   - IMPORTANT: Aerial robots CANNOT open containers

7. close(<robot_id>, <container object>): Specific robot closes a container
   - Precondition:
     * Container must have 'close' affordance
     * Container must be in robot's current room
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
     * Robot's gripper must be free
   - Effect: Container state changes to 'closed'
   - IMPORTANT: Aerial robots CANNOT close containers

8. turn_on(<robot_id>, <device>): Specific robot turns on a device
   - Precondition:
     * Device must have 'turn_on' affordance
     * Device must be in robot's current room
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
   - Effect: Device state changes to 'turned_on'

9. turn_off(<robot_id>, <device>): Specific robot turns off a device
   - Precondition:
     * Device must have 'turn_off' affordance
     * Device must be in robot's current room
     * Robot must have manipulation capability (NOT available for drones/quadrotors)
   - Effect: Device state changes to 'turned_off'

10. check(<robot_id>, <object>): Robot observes/checks an object's state
   - Precondition:
     * Object must be in robot's current room or visible from current position
     * Robot must have sensing capability (camera/sensors)
   - Effect: Information about object state is obtained
   - Note: This is ideal for aerial robots to scout/observe

Key Constraints to Remember:
- Single-arm robots: Can hold MAX 1 item at a time. Must drop before picking another.
- Dual-arm robots: Can hold MAX 2 items. Must drop at least one before picking a third.
- Manipulation actions (open/close/turn_on/turn_off): Require at least one free hand.
- When you need to free a hand for manipulation (open, close, turn_on, turn_off), always use DROP — not place.
- Use PLACE only for the final goal placement (e.g., placing item on the target surface/container).

MULTI-ROBOT SPECIFIC GUIDELINES:

1. **Robot Capabilities**:
   - Ground robots (fetch_1, robot_1, etc.): Can navigate, manipulate objects, open/close containers
   - Aerial robots (drone_1, quadrotor_1, etc.): Can fly between rooms, check/observe, but CANNOT manipulate

2. **Parallel Execution**:
   - Actions by different robots can happen simultaneously
   - Use parallel notation when possible: [action1 || action2] for simultaneous execution
   - Sequential actions for same robot: action1; action2

3. **Task Distribution**:
   - Assign observation/checking tasks to aerial robots
   - Assign manipulation tasks to ground robots
   - Consider efficiency: robots can work in different rooms simultaneously

4. **Coordination**:
   - Aerial robots can scout/check objects while ground robots manipulate
   - Each robot type should focus on tasks matching their capabilities
   - Plan should minimize total time by maximizing parallelism

## Example 1 - Two Mobile Robots with Different Tasks:
Instruction: "Put all dirty dishes in the dishwasher and move all toys to the toy box"

Scene:
- kitchen_3 contains: dishwasher_5 (closed), plate_7 (dirty), cup_9 (dirty)
- living_room_12 contains: toy_car_14, teddy_bear_16, toy_box_18
- bedroom_20 contains: lego_set_22, puzzle_24
- Rooms connected: kitchen_3 <-> hallway <-> living_room_12 <-> bedroom_20

Robots:
- robot_1 (mobile robot with gripper)
- robot_2 (mobile robot with gripper)

Plan:
```
# Robot_1's tasks (handle dishes):
open(robot_1, dishwasher_5)
pick(robot_1, plate_7)
place(robot_1, plate_7, dishwasher_5)
pick(robot_1, cup_9)
place(robot_1, cup_9, dishwasher_5)
close(robot_1, dishwasher_5)

# Robot_2's tasks (collect toys):
pick(robot_2, toy_car_14)
place(robot_2, toy_car_14, toy_box_18)
pick(robot_2, teddy_bear_16)
place(robot_2, teddy_bear_16, toy_box_18)
navigate(robot_2, living_room_12, bedroom_20)
pick(robot_2, lego_set_22)
navigate(robot_2, bedroom_20, living_room_12)
place(robot_2, lego_set_22, toy_box_18)
navigate(robot_2, living_room_12, bedroom_20)
pick(robot_2, puzzle_24)
navigate(robot_2, bedroom_20, living_room_12)
place(robot_2, puzzle_24, toy_box_18)
```

## Example 2 - Ground and Aerial Robot Division:
Instruction: "Close all open cabinets and check all smoke detectors"

Scene:
- kitchen_2 contains: cabinet_4 (opened), cabinet_6 (opened), smoke_detector_8
- bathroom_10 contains: medicine_cabinet_12 (opened), smoke_detector_14
- bedroom_16 contains: wardrobe_18 (closed), smoke_detector_20
- Connections: kitchen_2 <-> hallway <-> bathroom_10, hallway <-> bedroom_16

Robots:
- robot_1 (Fetch robot with gripper)
- drone_1 (Quadrotor with camera)

Plan:
```
# Robot_1's tasks (close cabinets):
close(robot_1, cabinet_4)
close(robot_1, cabinet_6)
navigate(robot_1, kitchen_2, hallway)
navigate(robot_1, hallway, bathroom_10)
close(robot_1, medicine_cabinet_12)

# Drone_1's tasks (check smoke detectors):
check(drone_1, smoke_detector_8)
navigate(drone_1, kitchen_2, hallway)
navigate(drone_1, hallway, bathroom_10)
check(drone_1, smoke_detector_14)
navigate(drone_1, bathroom_10, hallway)
navigate(drone_1, hallway, bedroom_16)
check(drone_1, smoke_detector_20)
```

## Your Task:
Instruction: {query}

Scene Graph:
{scene}

Robot Data:
{robot}

Additional Constraints:
{additional_information}

Generate a multi-robot plan to complete the instruction.
Think step-by-step:
1. Identify which subtasks each robot type should handle
2. Plan parallel execution where possible
3. Ensure robot capabilities match assigned tasks
4. Use scene graph and robot capabilities for planning
5. Coordinate robots efficiently
Final structured plan should NOT violate additional constraints.
Please USE Chain-of-Thought Reasoning for Planning!!!

Use notation:
- Each robot's tasks should be listed separately
- Use robot_id as first parameter: action(robot_1, ...)
- List actions in execution order for each robot

{format_instructions}
"""
