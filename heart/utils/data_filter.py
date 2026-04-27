"""
Data Filtering — Role-Aligned Environment Data

Extracts only the relevant subset of environment data for each agent type.
This is a core mechanism of HEART: each expert agent receives filtered data
to reduce context size and improve reasoning accuracy.

Filtering rules per agent:
- capability_reasoner: Robot URDF specs only (no objects, no scene)
- environmental_reasoner: Object affordances, states, parent relations (no robot, no connectivity)
- path_reasoner: Room connectivity graph + robot position (no objects)
- feasibility_reasoner: Robot kinematics + object physical properties (position, size, weight)
- constraint_reasoner: Object affordances, states, dependencies (no robot specs)
- homogeneous_reasoner: Full unfiltered data (baseline)
- physical_reasoner: covers capability + feasibility (3-agent ablation)
- spatial_reasoner: covers environmental + path (3-agent ablation)
"""

from typing import Dict, Any
import copy
import re


def filter_data_for_agent(agent_type: str, env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter environment data based on agent type.
    Returns only the data subset relevant to the given agent.
    
    Args:
        agent_type: Type of agent (e.g., "capability_reasoner")
        env_data: Full environment data
        
    Returns:
        Filtered data specific to the agent type
    """
    
    # Homogeneous agent - returns complete data without filtering
    if agent_type == "homogeneous_reasoner":
        return env_data  # Return complete environment data
    
    # Reasoning agents
    if agent_type == "capability_reasoner":
        return _filter_for_capability(env_data)
    elif agent_type == "environmental_reasoner":
        return _filter_for_environmental(env_data)
    elif agent_type == "path_reasoner":
        return _filter_for_path(env_data)
    elif agent_type == "feasibility_reasoner":
        return _filter_for_feasibility(env_data)
    elif agent_type == "constraint_reasoner":
        return _filter_for_constraint(env_data)

    # 3-agent ablation (combined-scope agents)
    elif agent_type == "physical_reasoner":
        return _filter_for_physical(env_data)
    elif agent_type == "spatial_reasoner":
        return _filter_for_spatial(env_data)

    # Orchestrator agents
    elif agent_type == "decomposer":
        # Decomposer uses full env_data for comprehensive understanding
        return env_data if env_data else {}
    elif agent_type == "allocator":
        # Allocator doesn't need env_data (uses question metadata)
        return {}
    elif agent_type == "synthesizer":
        # Synthesizer needs minimal env_data for context
        return _filter_for_synthesizer(env_data)
    
    else:
        # Unknown agent type - return empty dict
        return {}


def _filter_for_capability(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for capability reasoner
    - Robot URDF (parsed), state, and capability information
    - NO object information (encourages collaboration)
    - Skip empty arrays/fields
    """
    expert_data = {}
    
    # Robot capabilities extraction - only robot-specific data
    if env_data and "robots" in env_data:
        robots_data = env_data["robots"]
        if isinstance(robots_data, dict):
            filtered_robots = {}
            for robot_id, robot_info in robots_data.items():
                if isinstance(robot_info, dict):
                    robot_data = {}
                    
                    # Include URDF if available and not empty
                    urdf = robot_info.get("urdf")
                    if urdf and urdf != []:
                        robot_data["urdf"] = urdf
                        
                        # Extract key multi-arm/gripper info for capability reasoning
                        if isinstance(urdf, dict):
                            if "arm" in urdf and urdf["arm"].get("num_arms"):
                                robot_data["num_arms"] = urdf["arm"]["num_arms"]
                            if "gripper" in urdf and urdf["gripper"].get("num_grippers"):
                                robot_data["num_grippers"] = urdf["gripper"]["num_grippers"]
                    
                    # Include state if available and not empty
                    state = robot_info.get("state")
                    if state and state != []:
                        robot_data["state"] = state
                    
                    # Include capability if available and not empty
                    capability = robot_info.get("capability")
                    if capability and capability != []:
                        robot_data["capability"] = capability
                    
                    # Only add robot if it has at least some data
                    if robot_data:
                        filtered_robots[robot_id] = robot_data
            
            # Only add robots section if there are robots with data
            if filtered_robots:
                expert_data["robots"] = filtered_robots
    
    # No object or scene information - focuses only on robot capabilities
    
    return expert_data


def _filter_for_environmental(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for environmental reasoner
    - Room-object mapping with affordance, accessible, parent, relation
    - Room locations for object context
    - NO robot data (Path agent handles that)
    - NO connectivity (Path agent handles that)
    - NO type field
    - Skip empty arrays/fields
    """
    expert_data = {}
    
    # Scene structure with items and their relationships (NO robot data)
    if env_data and "scene_graph" in env_data:
        scene = env_data["scene_graph"]
        
        # Handle wrapped structure
        if len(scene) == 1 and "rooms" not in scene:
            scene_key = list(scene.keys())[0]
            scene = scene[scene_key]
        
        if "rooms" in scene:
            filtered_rooms = {}
            for room_id, room_data in scene["rooms"].items():
                room_items = {}
                
                # Include affordance, accessible, parent, relation (NO type)
                if "items" in room_data:
                    for item_id, item_data in room_data["items"].items():
                        item_filtered = {}
                        
                        # Include affordance if available and not empty
                        affordance = item_data.get("affordance")
                        if affordance and affordance != []:
                            item_filtered["affordance"] = affordance

                        # Include state if available and not empty
                        state = item_data.get("state")
                        if state and state != []:
                            item_filtered["state"] = state
                        
                        # Include accessible if available and not empty
                        accessible = item_data.get("accessible")
                        if accessible and accessible != []:
                            item_filtered["accessible"] = accessible
                        
                        # Include parent if available and not empty
                        parent = item_data.get("parent")
                        if parent and parent != []:
                            item_filtered["parent"] = parent
                        
                        # Include relation if available and not empty
                        relation = item_data.get("relation")
                        if relation and relation != []:
                            item_filtered["relation"] = relation
                        
                        # Only add item if it has at least some data
                        if item_filtered:
                            room_items[item_id] = item_filtered
                
                # Only add room if it has items with data
                if room_items:
                    filtered_rooms[room_id] = {"items": room_items}
            
            # Only add scene_graph if there are rooms with data
            if filtered_rooms:
                expert_data["scene_graph"] = {"rooms": filtered_rooms}
    
    return expert_data


def _filter_for_path(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for path reasoner
    - Room connectivity graph for navigation
    - Room positions and sizes for path calculation
    - Robot positions and location for starting point
    - NO item information (get from Environmental agent)
    - Skip empty arrays/fields
    """
    expert_data = {}
    
    # 1. Robot position and location for starting point
    if env_data and "robots" in env_data:
        robots_data = env_data["robots"]
        if isinstance(robots_data, dict):
            filtered_robots = {}
            for robot_id, robot_info in robots_data.items():
                if isinstance(robot_info, dict):
                    robot_data = {}
                    
                    # Include position if available and not empty
                    position = robot_info.get("position")
                    if position and position != []:
                        robot_data["position"] = position
                    
                    # Include location if available and not empty  
                    location = robot_info.get("location")
                    if location and location != []:
                        robot_data["location"] = location
                    
                    # Only add robot if it has at least some data
                    if robot_data:
                        filtered_robots[robot_id] = robot_data
            
            # Only add robots section if there are robots with data
            if filtered_robots:
                expert_data["robots"] = filtered_robots
    
    # 2. Room connectivity and positions only (NO items)
    if env_data and "scene_graph" in env_data:
        scene = env_data["scene_graph"]
        
        # Handle wrapped structure
        if len(scene) == 1 and "rooms" not in scene:
            scene_key = list(scene.keys())[0]
            scene = scene[scene_key]
        
        # Extract neighbor connections, room positions and sizes
        if "rooms" in scene:
            filtered_rooms = {}
            for room_id, room_data in scene["rooms"].items():
                room_filtered = {}
                
                # Include neighbor if available and not empty
                neighbor = room_data.get("neighbor")
                if neighbor and neighbor != []:
                    room_filtered["neighbor"] = neighbor
                
                # Include location if available and not empty
                location = room_data.get("location")
                if location and location != []:
                    room_filtered["location"] = location
                
                # Include size if available and not empty
                size = room_data.get("size")
                if size and size != []:
                    room_filtered["size"] = size
                
                # Only add room if it has at least some data
                if room_filtered:
                    filtered_rooms[room_id] = room_filtered
            
            # Only add scene_graph if there are rooms with data
            if filtered_rooms:
                expert_data["scene_graph"] = {"rooms": filtered_rooms}
    
    return expert_data


def _filter_for_feasibility(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for feasibility reasoner
    - Robot physical capabilities from parsed URDF specs and position
    - Object physical properties with size, weight, material, type, parent
    - Calculate min_size from object dimensions for graspability
    - Skip empty arrays/fields
    """
    expert_data = {}
    
    # 1. Robot physical capabilities from parsed URDF specs
    if env_data and "robots" in env_data:
        robots_data = env_data["robots"]
        if isinstance(robots_data, dict):
            filtered_robots = {}
            for robot_id, robot_info in robots_data.items():
                if isinstance(robot_info, dict):
                    robot_metrics = {}
                    
                    # Current position for distance calculations
                    position = robot_info.get("position")
                    if position and position != []:
                        robot_metrics["position"] = position
                    
                    # Use parsed URDF specs directly (no more XML parsing needed!)
                    urdf_specs = robot_info.get("urdf")
                    if urdf_specs and isinstance(urdf_specs, dict):
                        # Extract key metrics from parsed specs
                        
                        # Gripper specs (including multi-gripper support)
                        if "gripper" in urdf_specs:
                            gripper = urdf_specs["gripper"]
                            if gripper.get("has_gripper"):
                                if gripper.get("max_opening") is not None:
                                    robot_metrics["gripper_max_opening_cm"] = round(gripper["max_opening"] * 100, 2)
                                if gripper.get("min_opening") is not None:
                                    robot_metrics["gripper_min_opening_cm"] = round(gripper["min_opening"] * 100, 2)
                                if gripper.get("force_range"):
                                    robot_metrics["gripper_force_range"] = gripper["force_range"]
                                if gripper.get("num_grippers") is not None:
                                    robot_metrics["num_grippers"] = gripper["num_grippers"]
                                if gripper.get("num_fingers") is not None:
                                    robot_metrics["num_fingers_per_gripper"] = gripper["num_fingers"]
                        
                        # Arm specs (including multi-arm support)
                        if "arm" in urdf_specs:
                            arm = urdf_specs["arm"]
                            if arm.get("has_arm"):
                                if arm.get("max_reach") is not None:
                                    robot_metrics["max_reach_cm"] = round(arm["max_reach"] * 100, 2)
                                # if arm.get("workspace_height"):
                                #     robot_metrics["workspace_height_range"] = arm["workspace_height"]
                                if arm.get("degrees_of_freedom") is not None:
                                    robot_metrics["arm_dof"] = arm["degrees_of_freedom"]
                                if arm.get("num_arms") is not None:
                                    robot_metrics["num_arms"] = arm["num_arms"]
                        
                        # Base specs  
                        if "base" in urdf_specs:
                            base = urdf_specs["base"]
                            if base.get("footprint"):
                                robot_metrics["base_footprint"] = base["footprint"]
                            if base.get("torso_lift") is not None:
                                robot_metrics["torso_lift_range"] = base["torso_lift"]
                        
                        # Payload capacity (only manipulation-relevant torques)
                        if "payload" in urdf_specs:
                            payload = urdf_specs["payload"]
                            if payload.get("max_weight") is not None:
                                robot_metrics["max_payload_weight"] = payload["max_weight"]
                            if payload.get("max_torque"):
                                # Filter to only shoulder/elbow/wrist torques for grasp feasibility
                                manip_keywords = ('shoulder', 'elbow', 'wrist', 'grip', 'finger')
                                manip_torques = {k: v for k, v in payload["max_torque"].items()
                                                 if any(kw in k.lower() for kw in manip_keywords)}
                                if manip_torques:
                                    robot_metrics["manipulation_torques"] = manip_torques
                        
                        # Robot type
                        if urdf_specs.get("robot_type"):
                            robot_metrics["robot_type"] = urdf_specs["robot_type"]
                    
                    # Mobility type for locomotion feasibility
                    if "base" in urdf_specs:
                        base = urdf_specs["base"]
                        if base.get("mobility_type"):
                            robot_metrics["mobility_type"] = base["mobility_type"]

                    # Only add robot if it has data
                    if robot_metrics:
                        filtered_robots[robot_id] = robot_metrics
            
            # Only add robots section if there are robots with data
            if filtered_robots:
                expert_data["robots"] = filtered_robots
    
    # 2. Object physical properties from scene graph
    if env_data and "scene_graph" in env_data:
        scene = env_data["scene_graph"]
        
        # Handle wrapped structure
        if len(scene) == 1 and "rooms" not in scene:
            scene_key = list(scene.keys())[0]
            scene = scene[scene_key]
        
        # Extract physical properties for feasibility analysis
        if "rooms" in scene:
            filtered_objects = {}
            for room_id, room_data in scene["rooms"].items():
                for item_id, item_data in room_data.get("items", {}).items():
                    obj_filtered = {}
                    
                    # Include location if available and not empty
                    location = item_data.get("location")
                    if location and location != []:
                        obj_filtered["position"] = location
                    
                    # Include size in cm for clear graspability comparison
                    size = item_data.get("size")
                    if size and size != [] and len(size) >= 3:
                        obj_filtered["min_size_cm"] = round(min(size[:3]) * 100, 2)
                    
                    # Include weight if available and not empty
                    weight = item_data.get("weight")
                    if weight and weight != []:
                        obj_filtered["weight"] = weight
                    
                    # Include material if available and not empty
                    material = item_data.get("material")
                    if material and material != []:
                        obj_filtered["material"] = material
                    
                    # Only add object if it has data
                    if obj_filtered:
                        filtered_objects[item_id] = obj_filtered
            
            # Only add objects section if there are objects with data
            if filtered_objects:
                expert_data["objects"] = filtered_objects
    
    return expert_data


def _filter_for_constraint(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for constraint reasoner
    - Object affordances, state, accessibility
    - Material, weight for physical constraints
    - Parent/relation for logical dependencies
    - Skip empty arrays/fields
    Note: Original instruction comes from metadata in prompts
    """
    expert_data = {}
    
    # Object properties for constraint checking
    if env_data and "scene_graph" in env_data:
        scene = env_data["scene_graph"]
        
        # Handle wrapped structure
        if len(scene) == 1 and "rooms" not in scene:
            scene_key = list(scene.keys())[0]
            scene = scene[scene_key]
        
        # Extract constraint-relevant properties for all items
        if "rooms" in scene:
            filtered_properties = {}
            for room_id, room_data in scene["rooms"].items():
                for item_id, item_data in room_data.get("items", {}).items():
                    prop_filtered = {}
                    
                    # Include affordance if available and not empty
                    affordance = item_data.get("affordance")
                    if affordance and affordance != []:
                        prop_filtered["affordance"] = affordance
                    
                    # Include state if available and not empty
                    state = item_data.get("state")
                    if state and state != []:
                        prop_filtered["state"] = state
                    
                    # Include accessible if available and not empty
                    accessible = item_data.get("accessible")
                    if accessible and accessible != []:
                        prop_filtered["accessible"] = accessible
                    
                    # Include weight for weight-based constraints
                    weight = item_data.get("weight")
                    if weight and weight != []:
                        prop_filtered["weight"] = weight
                    
                    # Include material for material-based constraints
                    material = item_data.get("material")
                    if material and material != []:
                        prop_filtered["material"] = material
                    
                    # Include parent for dependency constraints
                    parent = item_data.get("parent")
                    if parent and parent != []:
                        prop_filtered["parent"] = parent
                    
                    # Include relation for understanding relationships
                    relation = item_data.get("relation")
                    if relation and relation != []:
                        prop_filtered["relation"] = relation
                    
                    # Only add item if it has constraint-relevant data
                    if prop_filtered:
                        filtered_properties[item_id] = prop_filtered
            
            # Only add object_properties if there are items with data
            if filtered_properties:
                expert_data["object_properties"] = filtered_properties
    
    return expert_data


def _filter_for_synthesizer(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for synthesizer
    - High-level environment context only
    - Robot identities and positions
    - Room structure
    """
    expert_data = {}
    
    # 1. Robot basic info (ID and position only)
    expert_data["robots"] = {}
    if env_data and "robots" in env_data:
        robots_data = env_data["robots"]
        if isinstance(robots_data, dict):
            for robot_id, robot_info in robots_data.items():
                if isinstance(robot_info, dict):
                    expert_data["robots"][robot_id] = {
                        "position": robot_info.get("position", "Unknown")
                    }
    
    # 2. High-level scene structure (room names and connections only)
    expert_data["scene_structure"] = {}
    if env_data and "scene_graph" in env_data:
        scene = env_data["scene_graph"]
        
        # Handle wrapped structure
        if len(scene) == 1 and "rooms" not in scene:
            scene_key = list(scene.keys())[0]
            scene = scene[scene_key]
        
        # Extract room structure only
        if "rooms" in scene:
            for room_id, room_data in scene["rooms"].items():
                expert_data["scene_structure"][room_id] = {
                    "connected_to": room_data.get("connected_to", [])
                }

    return expert_data


# ==================== 3-Agent Ablation (Combined-Scope Filters) ====================

def _filter_for_physical(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for the physical reasoner (covers capability + feasibility).
    Combines: robot specs (capability) + object physical properties (feasibility).
    """
    cap_data = _filter_for_capability(env_data)
    feas_data = _filter_for_feasibility(env_data)

    merged = {}
    # Merge robots: capability has urdf/state/capability, feasibility has metrics
    # Use feasibility's robot data (more detailed) and add capability fields
    if "robots" in feas_data:
        merged["robots"] = copy.deepcopy(feas_data["robots"])
        if "robots" in cap_data:
            for robot_id in cap_data["robots"]:
                if robot_id not in merged["robots"]:
                    merged["robots"][robot_id] = {}
                for key, val in cap_data["robots"][robot_id].items():
                    if key not in merged["robots"][robot_id]:
                        merged["robots"][robot_id][key] = val
    elif "robots" in cap_data:
        merged["robots"] = cap_data["robots"]

    # Object physical properties from feasibility
    if "objects" in feas_data:
        merged["objects"] = feas_data["objects"]

    return merged


def _filter_for_spatial(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for the spatial reasoner (covers environmental + path).
    Combines: scene items/affordances (environmental) + room connectivity (path) + robot position.
    """
    env_data_filtered = _filter_for_environmental(env_data)
    path_data = _filter_for_path(env_data)

    merged = {}
    # Scene graph: merge items (from env) with connectivity (from path)
    env_rooms = {}
    if "scene_graph" in env_data_filtered and "rooms" in env_data_filtered["scene_graph"]:
        env_rooms = copy.deepcopy(env_data_filtered["scene_graph"]["rooms"])

    path_rooms = {}
    if "scene_graph" in path_data and "rooms" in path_data["scene_graph"]:
        path_rooms = path_data["scene_graph"]["rooms"]

    all_rooms = set(list(env_rooms.keys()) + list(path_rooms.keys()))
    merged_rooms = {}
    for room_id in all_rooms:
        room = {}
        if room_id in env_rooms:
            room.update(env_rooms[room_id])
        if room_id in path_rooms:
            room.update(path_rooms[room_id])
        if room:
            merged_rooms[room_id] = room

    if merged_rooms:
        merged["scene_graph"] = {"rooms": merged_rooms}

    # Robot position from path data
    if "robots" in path_data:
        merged["robots"] = path_data["robots"]

    return merged