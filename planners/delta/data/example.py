"""
DELTA Task Examples (HEART addition)

Task-specific configurations for DELTA's LLM-to-PDDL pipeline.
Each task defines:
  - add_act: Additional PDDL action descriptions for domain generation
  - goal: Natural language goal instruction
  - gt_cost: Ground truth optimal plan length (verified with Fast Downward)
  - item_keep: Objects that must appear in the generated PDDL problem
  - subgoal / subgoal_pddl: Goal decomposition for DELTA's subproblem solver

40 tasks across 3 scenes (Beechwood 15, Benevolence 15, Merom 10).
"""
CLEAN = {
    "scene": ["allensville"],
    "add_obj": None,
    "add_act": [
        "dispose(<agent>, <item_1>, <item_2>, <room>): For disposing, <item_1> must be pickable and accessible, <item_2> must be rubbish bin, <agent> and <item_2> should be in <room>, <agent> is loaded and has <item_1>, and <item_1> is not disposed. As result, <item_1> will be disposed, <agent> is not loaded and does not has <item_1> anymore, and battery will not be full.",
        "mop_floor(<agent>, <item>, <room>): For mopping floor, <item> must be mop and pickable, <agent> should be in <room>, <agent> is loaded and has <item>, mop is clean. As result, floor is clean in <room>, but mop will not be clean, and battery will not be full.",
        "clean_mop(<agent>, <item_1>, <item_2>, <room>): For cleaning mop, <item_1> must be mop and pickable, <item_2> must be sink, <agent> and <item_2> should be in <room>, <agent> is loaded and has <item_1>, and mop is not clean. As result, mop will be clean and lies in <room>, agent is not loaded and does not has mop anymore, and battery will not be full.",
        "charge(<agent>, <item>, <room>): For charging, <item> must be robot_hub and accessible, <agent> and <item> should be in <room>, <agent> is not loaded, and agent's battery is not full. As result, agent's battery will be full."
    ],
    "goal": "Identify and dispose the possible rubbish (e.g. food residue, drink bottles/cans etc.) in the house, mop the floor in living room and kitchen, note that all mops should be clean after mopping each room. The mop should be clean in the end, and the battery should be full.",
    "gt_cost": {
        "shelbiana": 43,
        "allensville": 39,
        "parole": 41
    },
    "item_keep": ["sink_1", "sink_2", "mop", "cola_can", "banana_peel", "rotting_apple", "rubbish_bin", "robot_hub"],
    "subgoal": [
        "Identify and dispose of the cola can",
        "Identify and dispose of the banana peel",
        "Identify and dispose of the rotting apple",
        "Mop the floor in the living room",
        "Clean the mop used for the living room",
        "Mop the floor in the kitchen",
        "Clean the mop used for the kitchen",
        "Charge the robot's battery to full"
    ],
    "subgoal_pddl": [
        """
    (:goal\n        (item_disposed cola_can)\n    )\n""",
        """
    (:goal\n        (item_disposed banana_peel)\n    )\n""",
        """
    (:goal\n        (item_disposed rotting_apple)\n    )\n""",
        """
    (:goal\n        (floor_clean living_room)\n    )\n""",
        """
    (:goal\n        (mop_clean mop)\n    )\n""",
        """
    (:goal\n        (floor_clean kitchen)\n    )\n""",
        """
    (:goal\n        (mop_clean mop)\n    )\n""",
        """
    (:goal\n        (battery_full robot)\n    )\n"""
    ],
    "env_state": [
        "item_is_mop(<item>): <item> is mop.",
        "item_is_sink(<item>): <item> is sink.",
        "item_is_rubbish_bin(<item>): <item> is rubbish_bin.",
        "item_is_robot_hub(<item>): <item> is robot_hub.",
        "item_disposed(<item>): <item> is disposed.",
        "floor_clean(<room>): floor in <room> is clean.",
        "mop_clean(<item>): <item> is mop and is clean.",
        "battery_full(<agent>): <agent>'s battery is full."
    ]
}


# Beechwood Tasks (5 tasks from HEART config)
TURN_OFF_LIGHTS = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item> at <room>. <item> must be turnable and currently on, <item> is accessible, <agent> and <item> should be in <room>, <agent> is hand-free. As result, <item> will be turned off."
    ],
    "goal": "Turn off all the turned-on floor lamps in the house",
    "gt_cost": {
        "beechwood": 9  # Estimated - need to turn off 3 lamps in different rooms
    },
    "item_keep": ["floor_lamp_23", "floor_lamp_11", "floor_lamp_14", "floor_lamp_29"],
    "subgoal": [
        "turn off floor_lamp_23 in dining room",
        "turn off floor_lamp_11 in living room",
        "turn off floor_lamp_14 in living room",
        "turn off floor_lamp_29 in lobby"],
    "subgoal_pddl": [
        """
    (:goal
        (item_turned_off floor_lamp_23)
    )\n""",
        """
    (:goal
        (item_turned_off floor_lamp_11)
    )\n""",
        """
    (:goal
        (item_turned_off floor_lamp_14)
    )\n""",
        """
    (:goal
        (item_turned_off floor_lamp_29)
    )\n"""
    ]
}

LAUNDRY = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "open(<agent>, <item>, <room>): <agent> opens <item> at <room>. <item> must be openable and closeable, <item> is accessible, <agent> and <item> in <room>, <item> is closed (not open), <agent> hand must be free (not loaded). As result, <item> will be open (not closed anymore).",
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2> at <room>. <item_1> must be pickable (clothes), <item_2> must be a container (washer), both are accessible, <agent> is holding <item_1> (agent loaded), <agent> and <item_2> in <room>, <item_2> must be open. As result, <item_1> will be in <item_2>, <agent> hand becomes free (not loaded).",
        "close(<agent>, <item>, <room>): <agent> closes <item> at <room>. <item> must be closeable and openable, <item> is accessible, <agent> and <item> in <room>, <item> is open (not closed), <agent> hand must be free (not loaded). As result, <item> will be closed (not open anymore).",
        "turn_on_washer(<agent>, <washer>, <clothes>, <room>): <agent> turns on <washer> to wash <clothes> at <room>. <washer> must be turnable, <washer> is accessible, <agent> and <washer> in <room>, <washer> is closed, <washer> is off, <clothes> must be in <washer>, <clothes> is dirty, <agent> hand must be free (not loaded). As result, <washer> will be on (not off), <clothes> will be clean (not dirty)."
    ],
    "goal": "Do laundry by putting dirty clothes into the washing machine and turning it on",
    "gt_cost": {
        "beechwood": 10
    },
    "item_keep": ["jeans_112", "washer_47"],
    "subgoal": [
        "pick jeans from lobby",
        "go to utility room",
        "open washer",
        "put jeans in washer",
        "close washer",
        "turn on washer"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_in jeans_112 washer_47)
    )\n""",
        """
    (:goal
        (item_closed washer_47)
    )\n""",
        """
    (:goal
        (item_turned_on washer_47)
    )\n""",
        """
    (:goal
        (item_clean jeans_112)
    )\n"""
    ]
}

MEAL_PREP = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2> at <room>. <item_2> must be a surface and accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> on <item_2> (item_on), <item_1> at <room>, hand free.",
        "close(<agent>, <item>, <room>): <agent> closes <item> at <room>. <item> is accessible, <agent> and <item> in <room>, <item> is open, <agent> is hand-free. As result, <item> will be closed."
    ],
    "goal": "Pick up the salad and the hamburger from the kitchen, place both on the dining table, and close the open fridge in the kitchen",
    "gt_cost": {
        "beechwood": 10
    },
    "item_keep": ["salad_116", "hamburger_114", "table_16", "fridge_57"],
    "subgoal": [
        "go to kitchen, close fridge, pick first item, place on dining table",
        "go back to kitchen, pick second item, place on dining table"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (and (item_closed fridge_57) (item_on hamburger_114 table_16))
    )\n""",
        """
    (:goal
        (and (item_on salad_116 table_16) (item_on hamburger_114 table_16))
    )\n"""
    ]
}

PACK_WORK = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2> at <room>. <item_1> must be pickable (office supplies), <item_2> must be a container (briefcase/bag), both are accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>, <item_2> is open. As result, <item_1> in <item_2>, <agent> hand-free."
    ],
    "goal": "Pack work items by putting notebook and pen in briefcase",
    "gt_cost": {
        "beechwood": 9  # pick(note)→lobby→stair→kitchen→living place_in→living→office pick(pen)→office→living place_in
    },
    "item_keep": ["notebook_119", "pen_121", "briefcase_120", "table_28", "table_41"],
    "subgoal": [
        "put notebook in briefcase",
        "put pen in briefcase"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_in notebook_119 briefcase_120)
    )\n""",
        """
    (:goal
        (item_in pen_121 briefcase_120)
    )\n"""
    ]
}

KITCHEN_SAFETY = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item> at <room>. <item> must be turnable (appliance/lamp), <item> is accessible, <agent> and <item> in <room>, <item> is currently on, <agent> is hand-free. As result, <item> will be turned off.",
        "turn_on(<agent>, <item>, <room>): <agent> turns on <item> at <room>. <item> must be turnable (appliance/lamp), <item> is accessible, <agent> and <item> in <room>, <item> is currently off, <item> is closed (if openable like fridge), <agent> is hand-free. As result, <item> will be turned on.",
        "close(<agent>, <item>, <room>): <agent> closes <item> at <room>. <item> must be closeable (door/container), <item> is accessible, <agent> and <item> in <room>, <item> is open, <agent> is hand-free. As result, <item> will be closed."
    ],
    "goal": "Ensure kitchen safety by checking if stove and oven are on, and turning them off if needed, also close the refrigerator if it opened then turn-on it",
    "gt_cost": {
        "beechwood": 5 
    },
    "item_keep": ["oven_59", "fridge_57"],
    "subgoal": [
        "check oven and turn off if on",
        "check refrigerator and close if open",
        "turn on refrigerator after closing"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_turned_off oven_59)
    )\n""",
        """
    (:goal
        (item_closed fridge_57)
    )\n""",
        """
    (:goal
        (item_turned_on fridge_57)
    )\n"""
    ]
}

# Benevolence Tasks
PACK_ESSENTIALS = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2> at <room>. <item_1> must be pickable (notebook/pen), <item_2> must be a container (briefcase), both are accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> in <item_2>, <agent> hand-free."
    ],
    "goal": "Pack work essentials by putting any one notebook and pen in briefcase",
    "gt_cost": {
        "benevolence": 10
    },
    "item_keep": ["notebook_64", "notebook_54", "pen_56", "briefcase_61", "table_1", "sink_19", "chest_12"],
    "subgoal": [
        "pick notebook from dining room table",
        "place notebook in briefcase",
        "pick pen from kitchen sink",
        "place pen in briefcase"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_in notebook_64 briefcase_61)
    )\n""",
        """
    (:goal
        (item_in pen_56 briefcase_61)
    )\n"""
    ]
}

SERVE_FOOD = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2> at <room>. <item_1> must be pickable and accesible, <item_2> must be a accessible and surface, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> on <item_2>, <agent> hand-free."
    ],
    "goal": "Serve food to dining table by putting any one apple and then hamburger",
    "gt_cost": {
        "benevolence": 9
    },
    "item_keep": ["apple_62", "hamburger_58", "table_1", "countertop_21", "countertop_18"],
    "subgoal": [
        "pick apple from kitchen countertop",
        "place apple on dining room table",
        "pick hamburger from kitchen countertop",
        "place hamburger on dining room table"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_on apple_62 table_1)
    )\n""",
        """
    (:goal
        (item_on hamburger_58 table_1)
    )\n"""
    ]
}

CLEAN_KITCHEN = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "open(<agent>, <item>, <room>): <agent> opens <item> at <room>. <item> must be openable, <item> is accessible, <agent> and <item> in <room>, <item> is closed, <agent> is hand-free. As result, <item> will be open.",
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2> at <room>. <item_1> must be pickable, <item_2> must be a container, open, both are accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> in <item_2>, <agent> hand-free."
    ],
    "goal": "Clean kitchen by putting one small bowl into dishwasher",
    "gt_cost": {
        "benevolence": 7
    },
    "item_keep": ["bowl_63", "dishwasher_20", "table_1"],
    "subgoal": [
        "pick small bowl from dining room table",
        "go to kitchen",
        "open dishwasher if closed",
        "place bowl in dishwasher"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_open dishwasher_20)
    )\n""",
        """
    (:goal
        (item_in bowl_63 dishwasher_20)
    )\n"""
    ]
}

FIND_ITEMS = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2> at <room>. <item_1> must be pickable, <item_2> must be a surface, both are accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> on <item_2>, <agent> hand-free.",
        "close(<agent>, <item>, <room>): <agent> closes <item> at <room>. <item> must be closeable, <item> is accessible, <agent> and <item> in <room>, <item> is open, <agent> is hand-free. As result, <item> will be closed."
    ],
    "goal": "Find personal items by placing sunglass on countertop_18 and close open windows",
    "gt_cost": {
        "benevolence": 6  # pick(sun)→liv→corr→kitchen place_on→kitchen→dining close_window
    },
    "item_keep": ["sunglass_65", "countertop_18", "window_50"],
    "subgoal": [
        "pick sunglass from living room shelf",
        "go to kitchen",
        "place sunglass on countertop_18",
        "go to dining room",
        "close opened window"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_on sunglass_65 countertop_18)
    )\n""",
        """
    (:goal
        (item_closed window_50)
    )\n"""
    ]
}

ORGANIZE_KITCHEN = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "open(<agent>, <item>, <room>): <agent> opens <item> at <room>. <item> must be openable, <item> is accessible, <agent> and <item> in <room>, <item> is closed, <agent> is hand-free. As result, <item> will be open.",
        "place_in_apple(<agent>, <item>, <container>, <room>): <agent> places the apple into <container>. <item> must be an apple (is_apple), <container> must be a container, accessible, and open, <agent> holding <item>, <agent> and <container> in <room>, apple not yet placed. As result, <item> in <container>, hand free, apple_placed.",
        "place_in_hamburger(<agent>, <item>, <container>, <room>): <agent> places the hamburger into <container>. <item> must be a hamburger (is_hamburger), <container> must be a container, accessible, and open, <agent> holding <item>, <agent> and <container> in <room>, apple must already be placed (apple_placed). As result, <item> in <container>, hand free.",
        "close(<agent>, <item>, <room>): <agent> closes <item> at <room>. <item> must be closeable, <item> is accessible, <agent> and <item> in <room>, <item> is open, <agent> is hand-free. As result, <item> will be closed."
    ],
    "goal": "Put the eatable food items on the kitchen countertop into the fridge from smallest to largest, then close the fridge",
    "gt_cost": {
        "benevolence": 8
    },
    "item_keep": ["apple_62", "hamburger_58", "fridge_27"],
    "subgoal": [
        "open fridge, pick apple, place apple in fridge first",
        "pick hamburger, place hamburger in fridge after apple, close fridge"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (and (item_in apple_62 fridge_27) (apple_placed))
    )\n""",
        """
    (:goal
        (and (item_in hamburger_58 fridge_27) (item_closed fridge_27))
    )\n"""
    ]
}

# Benevolence fetch tasks (bn_5, bn_6, bn_7)
MICROWAVE_APPLE = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_2> must be open container, <agent> holding <item_1>. As result, <item_1> in <item_2> (item_in), hand free.",
        "open(<agent>, <item>, <room>): <agent> opens <item>. Openable, closed, hand free. As result, open.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. Closeable, open, hand free. As result, closed.",
        "turn_on(<agent>, <item>, <room>): <agent> turns on <item>. Turnable, closed, off, hand free. As result, on.",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item>. Turnable, on, hand free. As result, off."
    ],
    "goal": "Put an apple in the microwave and heat it",
    "gt_cost": {"benevolence": 6},
    "item_keep": ["apple_62", "microwave_36"],
    "subgoal": [
        "pick small apple",
        "open microwave, place apple, close, turn on"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_in apple_62 microwave_36))\n""",
        """
    (:goal (item_turned_on microwave_36))\n"""
    ]
}

BOWL_TO_OVEN = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_2> must be open container, <agent> holding <item_1>. As result, <item_1> in <item_2> (item_in), hand free.",
        "open(<agent>, <item>, <room>): <agent> opens <item>. Openable, closed, hand free. As result, open.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. Closeable, open, hand free. As result, closed.",
        "turn_on(<agent>, <item>, <room>): <agent> turns on <item>. Turnable, closed, off, hand free. As result, on.",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item>. Turnable, on, hand free. As result, off."
    ],
    "goal": "Put a bowl in the oven and heat it",
    "gt_cost": {"benevolence": 7},  # Do not have to close the oven
    "item_keep": ["bowl_63", "oven_24"],
    "subgoal": [
        "pick small bowl from dining room",
        "go to kitchen, open oven, place bowl, close, turn on"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_in bowl_63 oven_24))\n""",
        """
    (:goal (item_turned_on oven_24))\n"""
    ]
}

SUNGLASS_IN_BRIEFCASE = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_2> must be a container, <agent> holding <item_1>. As result, <item_1> in <item_2> (item_in), hand free."
    ],
    "goal": "Put a sunglass in the briefcase",
    "gt_cost": {"benevolence": 3},
    "item_keep": ["sunglass_65", "briefcase_61"],
    "subgoal": [
        "pick light sunglass, place in briefcase"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_in sunglass_65 briefcase_61))\n"""
    ]
}


# Benevolence JR2 Kinova tasks (bn_8~11)
CHEESE_FROM_FRIDGE = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "open(<agent>, <item>, <room>): <agent> opens <item>. Openable, closed, hand free. As result, open.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. Closeable, open, hand free. As result, closed.",
        "pick_from(<agent>, <item_1>, <item_2>, <room>): <agent> picks <item_1> from inside <item_2>. <item_1> must be pickable and inside <item_2> (item_in), <item_2> must be open container, hand free. As result, <item_1> taken out (not item_in), in room (item_at), held by agent.",
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2>. <item_2> must be a surface. As result, <item_1> on <item_2> (item_on), hand free."
    ],
    "goal": "Take a cheese out of the fridge and place it on the dining table",
    "gt_cost": {"benevolence": 6},  # liv→corr→kitchen open(fridge) pick_from→kitchen→dining place_on
    "item_keep": ["cheese_66", "fridge_27", "table_1"],
    "subgoal": [
        "open fridge",
        "pick cheese from fridge",
        "go to dining room, place on table"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_open fridge_27))\n""",
        """
    (:goal (item_on cheese_66 table_1))\n"""
    ]
}

CLEAN_AND_CUP = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "clean(<agent>, <item>, <room>): <agent> cleans <item>. <item> must be cleanable, hand free. As result, <item> is clean (item_clean).",
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2>. <item_2> must be a surface. As result, <item_1> on <item_2> (item_on), hand free."
    ],
    "goal": "Clean all chairs in the dining room and bring a cup to the dining table",
    "gt_cost": {"benevolence": 7},  # corr→kitchen pick(cup)→kitchen→dining place_on clean×3
    "item_keep": ["cup_69", "chair_2", "chair_3", "chair_4", "table_1"],
    "subgoal": [
        "clean all 3 chairs in dining room",
        "go to kitchen, pick cup",
        "bring cup to dining table"
    ],
    "subgoal_pddl": [
        """
    (:goal (and (item_clean chair_2) (item_clean chair_3) (item_clean chair_4)))\n""",
        """
    (:goal (item_on cup_69 table_1))\n"""
    ]
}

NEAREST_FOOD = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2>. <item_2> must be a surface. As result, <item_1> on <item_2> (item_on), hand free."
    ],
    "goal": "Bring the nearest food item to the dining table",
    "gt_cost": {"benevolence": 4},  # liv→corr pick(sandwich)→corr→dining place_on
    "item_keep": ["sandwich_70", "table_1"],
    "subgoal": [
        "pick nearest graspable food",
        "place on dining table"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_on sandwich_70 table_1))\n"""
    ]
}

BOOK_TO_CORRIDOR = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2>. <item_2> must be a surface. As result, <item_1> on <item_2> (item_on), hand free."
    ],
    "goal": "Put any graspable book and the pen on the console table in the corridor",
    "gt_cost": {"benevolence": 8},
    "item_keep": ["book_72", "pen_56", "console_table_9"],
    "subgoal": [
        "pick reachable book from living room",
        "place book on console table",
        "pick pen from kitchen",
        "place pen on console table"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_on book_72 console_table_9))\n""",
        """
    (:goal (item_on pen_56 console_table_9))\n"""
    ]
}


# Benevolence JR2 Kinova tasks (bn_12~13)
LIVING_ROOM_SETUP = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "turn_on(<agent>, <item>, <room>): <agent> turns on <item>. Turnable, off, hand free. As result, on (state_on).",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item>. Turnable, on, hand free. As result, off (state_off).",
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2>. <item_2> must be surface. As result, <item_1> on <item_2> (item_on), hand free."
    ],
    "goal": "Turn on the TV and the floor lamp, then put a sunglass on the sofa",
    "gt_cost": {"benevolence": 5},
    "item_keep": ["sunglass_65", "floor_lamp_8", "wall_mounted_tv_49", "sofa_10"],
    "subgoal": [
        "turn on TV and lamp",
        "pick light sunglass, place on sofa"
    ],
    "subgoal_pddl": [
        """
    (:goal (and (item_state_on floor_lamp_8) (item_state_on wall_mounted_tv_49)))\n""",
        """
    (:goal (item_on sunglass_65 sofa_10))\n"""
    ]
}

CLOSE_LARGEST_FURNITURE = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "close(<agent>, <item>, <room>): <agent> closes <item>. Closeable, open, hand free. As result, closed.",
        "clean(<agent>, <item>, <room>): <agent> cleans <item>. Cleanable, hand free. As result, clean (item_clean)."
    ],
    "goal": "Close the largest opened furniture and clean the sofa",
    "gt_cost": {"benevolence": 4},
    "item_keep": ["chest_11", "sofa_10"],
    "subgoal": [
        "close largest opened furniture (chest_11)",
        "clean sofa"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_closed chest_11))\n""",
        """
    (:goal (item_clean sofa_10))\n"""
    ]
}


VISIT_ROOMS = {
    "scene": ["benevolence"],
    "add_obj": None,
    "add_act": [
        "goto(<agent>, <room1>, <room2>): For visiting rooms, <agent> goes from <room1> to <room2>, where <room1> and <room2> should be neighbors. As result, <agent> will leave <room1> and locates in <room2>, and <room2> will be marked as visited. The visited predicate is permanent and does not reset."
    ],
    "goal": "Visit every room except the largest and the smallest",
    "gt_cost": {"benevolence": 2},
    "item_keep": [],
    "subgoal": [
        "visit dining room",
        "visit living room"
    ],
    "subgoal_pddl": [
        """
    (:goal (visited dining_room_9))\n""",
        """
    (:goal (visited living_room_12))\n"""
    ]
}


# Merom Tasks (including multi-robot tasks)
HOME_SECURITY = {
    "scene": ["merom"],
    "add_obj": ["drone"],  # drone is a separate type from agent
    "add_act": [
        "Note: robot_1 is agent type, drone_1 is drone type. They are different types and use different predicates.",
        "check(<agent>, <item>, <room>): <agent> checks <item> at <room>. <item> must be a window, <item> is accessible, <agent> and <item> in <room>, <agent> hand must be free (not loaded). As result, <item> will be checked.",
        "check_drone(<drone>, <item>, <room>): <drone> checks <item> at <room>. <item> must be a window, <item> is accessible, <drone> and <item> in <room>. As result, <item> will be checked. Drone has no arms so cannot pick/drop items.",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item> at <room>. <item> must be a lamp, <item> is accessible, <agent> and <item> in <room>, <item> is currently on (state_on), <agent> hand must be free (not loaded). As result, <item> will be off (state_off, not state_on anymore).",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2> (not at <room1> anymore). Uses drone_at predicate."
    ],
    "goal": "Inspect all opened windows in the house and turn off all lamps that are on",
    "gt_cost": {
        "merom": 8  # Estimated for multi-robot
    },
    "item_keep": ["window_77", "window_82", "table_lamp_17", "floor_lamp_31", "floor_lamp_33"],
    "subgoal": [
        "check opened window_77 in dining room",
        "check opened window_82 in living room",
        "turn off table_lamp_17 in bedroom",
        "turn off floor_lamp_31 in living room",
        "turn off floor_lamp_33 in living room"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_checked window_77)
    )\n""",
        """
    (:goal
        (item_checked window_82)
    )\n""",
        """
    (:goal
        (item_state_off table_lamp_17)
    )\n""",
        """
    (:goal
        (item_state_off floor_lamp_31)
    )\n""",
        """
    (:goal
        (item_state_off floor_lamp_33)
    )\n"""
    ],
    "robots": ["robot_1", "drone_1"]  # Multi-robot task
}

CLEAN_AND_INSPECT = {
    "scene": ["merom"],
    "add_obj": ["drone"],
    "add_act": [
        "Note: robot_1 is agent type, drone_1 is drone type. They are different types and use different predicates.",
        "clean(<agent>, <item>, <room>): <agent> cleans <item> at <room>. <item> must be cleanable, <item> is accessible, <agent> and <item> in <room>, <agent> hand must be free (not loaded). As result, <item> will be clean.",
        "inspect(<drone>, <item>, <room>): Only <drone> can inspect <item> at <room>. <item> must be pickable and accessible, <drone> and <item> in <room>. As result, <item> will be inspected. Only drone can perform inspect action.",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2> (not at <room1> anymore). Uses drone_at predicate."
    ],
    "goal": "Clean all cleanable items in the bathroom, and check all pickable items located above 2.0 meters height in the house",
    "gt_cost": {
        "merom": 7  # FD optimal
    },
    "item_keep": ["bathtub_71", "toilet_69", "medicine_103", "first_aid_kit_104"],
    "subgoal": [
        "robot cleans bathtub in bathroom",
        "robot cleans toilet in bathroom",
        "drone inspects medicine_103 (2.1m height) in kitchen",
        "drone inspects first_aid_kit_104 (2.25m height) in kitchen"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_clean bathtub_71)
    )\n""",
        """
    (:goal
        (item_clean toilet_69)
    )\n""",
        """
    (:goal
        (item_inspected medicine_103)
    )\n""",
        """
    (:goal
        (item_inspected first_aid_kit_104)
    )\n"""
    ],
    "robots": ["robot_1", "drone_1"]  # Multi-robot task
}

PAPER_TOWEL_ORGANIZATION = {
    "scene": ["merom"],
    "add_obj": ["drone"],
    "add_act": [
        "Note: robot_1 is agent type, drone_1 is drone type. They are different types and use different predicates.",
        "take_view(<drone>, <room>): <drone> takes aerial view of <room>. <drone> must be at <room>. As result, <room> will be viewed.",
        "open(<agent>, <item>, <room>): <agent> opens <item> at <room>. <item> must be openable and closeable, <item> is accessible, <agent> and <item> in <room>, <item> is closed, <agent> hand must be free (not loaded). As result, <item> will be open.",
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2> at <room>. <item_1> must be pickable, <item_2> must be a container, both are accessible, <agent> is holding <item_1>, <agent> and <item_2> in <room>, <item_2> must be open. As result, <item_1> in <item_2>, <agent> hand free.",
        "close(<agent>, <item>, <room>): <agent> closes <item> at <room>. <item> must be closeable and openable, <item> is accessible, <agent> and <item> in <room>, <item> is open, <agent> hand must be free (not loaded). As result, <item> will be closed.",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2> (not at <room1> anymore). Uses drone_at predicate."
    ],
    "goal": "Take the aerial view of all rooms in the house, and collect the paper towel closest to the agent and place that paper towel into an opened cabinet in the kitchen then close the cabinet",
    "gt_cost": {
        "merom": 18  # FD optimal
    },
    "item_keep": ["paper_towel_105", "top_cabinet_54"],
    "subgoal": [
        "drone takes view of all rooms",
        "robot picks paper_towel_105 from dining room",
        "robot goes to kitchen",
        "robot places paper_towel in top_cabinet_54 (already opened)",
        "robot closes top_cabinet_54"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (and
            (room_viewed bathroom_2)
            (room_viewed bedroom_3)
            (room_viewed childs_room_5)
            (room_viewed corridor_6)
            (room_viewed dining_room_7)
            (room_viewed kitchen_8)
            (room_viewed living_room_10)
        )
    )\n""",
        """
    (:goal
        (item_in paper_towel_105 top_cabinet_54)
    )\n""",
        """
    (:goal
        (item_closed top_cabinet_54)
    )\n"""
    ],
    "robots": ["robot_1", "drone_1"]  # Multi-robot task
}

EVENING_PREPARATION = {
    "scene": ["merom"],
    "add_obj": None,
    "add_act": [
        "Note: robot_1 and robot_2 are both agent type. They use same predicates and actions.",
        "open_dishwasher(<agent>, <dishwasher>, <room>): <agent> opens <dishwasher> at <room>. <dishwasher> must be openable and closeable, <dishwasher> is accessible, <agent> and <dishwasher> in <room>, <dishwasher> is closed (not open), <agent> hand must be free (not loaded). As result, <dishwasher> will be open (not closed anymore).",
        "pick_from(<agent>, <item>, <container>, <room>): <agent> picks <item> from inside <container> at <room>. <item> must be pickable and currently inside <container> (item_in predicate shows <item> is in <container>), <container> must be open, <agent> and <container> in <room>, <agent> hand must be free (not loaded). As result, <item> not in <container> anymore (remove item_in), <item> now at <room>, <agent> has <item> (agent loaded). Note: Regular pick action cannot pick items that are inside containers (item_in predicate blocks it).",
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2> at <room>. <item_1> must be pickable, <item_2> must be surface, both are accessible, <agent> is holding <item_1> (agent loaded), <agent> and <item_2> in <room>. As result, <item_1> will be on <item_2>, <agent> hand becomes free (not loaded).",
        "close_window(<agent>, <window>, <room>): <agent> closes <window> at <room>. <window> must be closeable and openable, <window> is accessible, <agent> and <window> in <room>, <window> is opened (not closed), <agent> hand must be free (not loaded). As result, <window> will be closed (not opened anymore).",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item> at <room>. <item> must be turnable, <item> is accessible, <agent> and <item> in <room>, <item> is currently on (state_on), <agent> hand must be free (not loaded). As result, <item> will be off (state_off, not state_on anymore)."
    ],
    "goal": "Organize the house: if dishwasher is closed open it then take out the glass and place on dining table, close all the opened windows and turn off stove and all floor lamps that are on",
    "gt_cost": {
        "merom": 12  # Estimated for multi-robot
    },
    "item_keep": ["dishwasher_52", "glass_93", "table_20", "window_77", "window_82", "stove_59", "floor_lamp_31", "floor_lamp_33"],
    "subgoal": [
        "robot opens dishwasher",
        "robot takes glass from dishwasher",
        "robot places glass on dining table",
        "robot closes opened windows",
        "robot turns off stove",
        "robot turns off floor lamps"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_open dishwasher_52)
    )\n""",
        """
    (:goal
        (item_on glass_93 table_20)
    )\n""",
        """
    (:goal
        (and
            (item_closed window_77)
            (item_closed window_82)
        )
    )\n""",
        """
    (:goal
        (item_state_off stove_59)
    )\n""",
        """
    (:goal
        (and
            (item_state_off floor_lamp_31)
            (item_state_off floor_lamp_33)
        )
    )\n"""
    ],
    "robots": ["robot_1", "robot_2"]  # Multi-robot task
}

PARTY_PREPARATION = {
    "scene": ["merom"],
    "add_obj": None,
    "add_act": [
        "Note: robot_1 and robot_2 are both agent type. They use same predicates and actions.",
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2> at <room>. <item_1> must be pickable, <item_2> must be surface, both accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> on <item_2>, <agent> hand free.",
        "close_window(<agent>, <window>, <room>): <agent> closes <window> at <room>. <window> must be closeable, accessible, currently opened, <agent> hand must be free. As result, <window> closed.",
        "turn_on(<agent>, <item>, <room>): <agent> turns on <item> at <room>. <item> must be a lamp, accessible, currently off (state_off), <agent> hand must be free. As result, <item> on (state_on)."
    ],
    "goal": "Prepare for party: take wine bottle and cheese from the kitchen to the dining table, turn on all lamps in the house and ensure all windows are closed",
    "gt_cost": {
        "merom": 14  # FD optimal
    },
    "item_keep": ["wine_bottle_94", "cheese_99", "table_20",
                  "table_lamp_10", "table_lamp_11", "table_lamp_3",
                  "window_77", "window_82"],
    "subgoal": [
        "robot picks wine bottle from kitchen and places on dining table",
        "robot picks cheese from kitchen and places on dining table",
        "robot turns on all lamps that are off",
        "robot closes all opened windows"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_on wine_bottle_94 table_20)
    )\n""",
        """
    (:goal
        (item_on cheese_99 table_20)
    )\n""",
        """
    (:goal
        (and
            (item_state_on table_lamp_10)
            (item_state_on table_lamp_11)
            (item_state_on table_lamp_3)
        )
    )\n""",
        """
    (:goal
        (and
            (item_closed window_77)
            (item_closed window_82)
        )
    )\n"""
    ],
    "robots": ["robot_1", "robot_2"]
}


# Beechwood fetch tasks (bw_7, bw_8, bw_9)
KITCHEN_RESTOCK = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2> at <room>. <item_1> must be pickable, <item_2> must be an openable container and currently open (fridge starts open), <agent> holding <item_1>, both in <room>. As result, <item_1> will be in <item_2>, hand free.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. <item> must be closeable and currently open, hand free. As result, <item> will be closed."
    ],
    "goal": "Take the milk from the countertop and the cereal from the table in the kitchen, place both in the refrigerator, then close the refrigerator",
    "gt_cost": {
        "beechwood": 7
    },
    "item_keep": ["milk_118", "cereal_115", "fridge_57"],
    "subgoal": [
        "pick milk from countertop",
        "place milk in fridge (already open)",
        "pick cereal from table",
        "place cereal in fridge",
        "close fridge"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_in milk_118 fridge_57)
    )\n""",
        """
    (:goal
        (item_in cereal_115 fridge_57)
    )\n""",
        """
    (:goal
        (item_closed fridge_57)
    )\n"""
    ]
}

FRIDGE_THEN_OVEN = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "open(<agent>, <item>, <room>): <agent> opens <item> at <room>. <item> must be openable and closeable, <item> is closed, <agent> hand must be free. As result, <item> will be open.",
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_1> must be pickable, <item_2> must be an openable container and currently open, <agent> holding <item_1>. As result, <item_1> will be in <item_2>, hand free.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. <item> must be closeable and open, hand free. As result, <item> will be closed.",
        "turn_on(<agent>, <item>, <room>): <agent> turns on <item>. <item> must be turnable, closed, off, hand free. As result, <item> will be turned on.",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item>. <item> must be turnable, on, hand free. As result, <item> will be turned off."
    ],
    "goal": "Open the oven and place the hamburger from the kitchen table inside, close the oven and turn it on, then take the milk from the countertop and place it in the refrigerator",
    "gt_cost": {
        "beechwood": 8 
    },
    "item_keep": ["hamburger_114", "milk_118", "oven_59", "fridge_57"],
    "subgoal": [
        "pick hamburger from kitchen table",
        "open oven",
        "place hamburger in oven",
        "close oven",
        "turn on oven",
        "pick milk from countertop",
        "place milk in fridge (fridge already open)"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_in hamburger_114 oven_59)
    )\n""",
        """
    (:goal
        (item_turned_on oven_59)
    )\n""",
        """
    (:goal
        (item_in milk_118 fridge_57)
    )\n"""
    ]
}

DISHWASHER_LOAD = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "open(<agent>, <item>, <room>): <agent> opens <item> at <room>. <item> must be openable and closeable, <item> is closed, <agent> hand must be free. As result, <item> will be open.",
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_1> must be pickable, <item_2> must be an open container, <agent> holding <item_1>. As result, <item_1> will be in <item_2>.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. <item> must be closeable and currently open, hand free. As result, <item> will be closed.",
        "turn_on_dishwasher(<agent>, <item>, <room>): <agent> turns on <item>. <item> must be turnable, closed, and currently off, hand free. As result, <item> will be turned on."
    ],
    "goal": "Take the bowl from the dining table, open the dishwasher, place the bowl inside, and turn the dishwasher on",
    "gt_cost": {
        "beechwood": 7  # robot starts at dining with bowl: pick→goto(dining→kitchen)→open→place_in→close→turn_on
    },
    "item_keep": ["bowl_117", "dishwasher_72"],
    "subgoal": [
        "pick bowl from dining table",
        "go to kitchen",
        "open dishwasher",
        "place bowl in dishwasher",
        "close dishwasher",
        "turn on dishwasher"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_in bowl_117 dishwasher_72)
    )\n""",
        """
    (:goal
        (item_closed dishwasher_72)
    )\n""",
        """
    (:goal
        (item_turned_on dishwasher_72)
    )\n"""
    ]
}


# Beechwood JR2 Kinova tasks (bw_10, bw_11, bw_12)
MULTI_CONTAINER_STORE = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_1> must be pickable, <item_2> must be an openable container and currently open, <agent> holding <item_1>. As result, <item_1> will be in <item_2> (item_in), hand free.",
        "open(<agent>, <item>, <room>): <agent> opens <item>. <item> must be openable and closed, hand free. As result, <item> will be open.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. <item> must be closeable and open, hand free. As result, <item> will be closed."
    ],
    "goal": "Put the milk in the refrigerator and the cereal in the chest in the kitchen, then close both",
    "gt_cost": {"beechwood": 8},
    "item_keep": ["milk_118", "cereal_115", "fridge_57", "chest_8"],
    "subgoal": [
        "pick milk and place in fridge",
        "pick cereal and place in chest (already open)",
        "close chest and close fridge"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_in milk_118 fridge_57))\n""",
        """
    (:goal (item_in cereal_115 chest_8))\n""",
        """
    (:goal (and (item_closed fridge_57) (item_closed chest_8)))\n"""
    ]
}

CROSS_HOUSE_DELIVERY = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_2> must be a container and accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> in <item_2> (item_in), hand free."
    ],
    "goal": "Put the notebook in the opened cabinet in the home office, the pen in the opened chest in the kitchen, and the salad in the sink in the utility room",
    "gt_cost": {"beechwood": 13},
    "item_keep": ["notebook_119", "pen_121", "salad_116", "bottom_cabinet_39", "chest_8", "sink_43"],
    "subgoal": [
        "pick notebook from lobby, place in opened cabinet in home office",
        "pick pen from home office, place in opened chest in kitchen",
        "pick salad from kitchen, place in sink in utility room"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_in notebook_119 bottom_cabinet_39))\n""",
        """
    (:goal (item_in pen_121 chest_8))\n""",
        """
    (:goal (item_in salad_116 sink_43))\n"""
    ]
}

MILK_TO_UTILITY = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "goto(<agent>, <room1>, <room2>): <agent> goes from <room1> to <room2>. <room1> and <room2> must be neighbors, and <room2> must be allowed (room_allowed). Rooms not marked as room_allowed cannot be entered. As result, <agent> at <room2>.",
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_2> must be a container, accessible, and open, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> in <item_2> (item_in), hand free."
    ],
    "goal": "Pick up the milk from the kitchen and place it in the sink in the utility room without going through the dining room, staircase, or corridor",
    "gt_cost": {"beechwood": 6},  # goto(liv→kit) pick goto(kit→liv→office→util) place_in(milk,sink)
    "item_keep": ["milk_118", "sink_43"],
    "subgoal": [
        "go to kitchen and pick milk",
        "navigate to utility room via living room and home office, place milk in sink"
    ],
    "subgoal_pddl": [
        """
    (:goal (and (agent_has_item robot milk_118) (agent_at robot kitchen_12)))\n""",
        """
    (:goal (item_in milk_118 sink_43))\n"""
    ]
}


# Beechwood JR2 Kinova tasks (bw_13, bw_14)
EVENING_LIVING_ROOM = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item>. <item> must be turnable and on (state_on), hand free. As result, <item> will be off (state_off).",
        "turn_on(<agent>, <item>, <room>): <agent> turns on <item>. <item> must be turnable and off (state_off), hand free. As result, <item> will be on (state_on).",
        "clean(<agent>, <item>, <room>): <agent> cleans <item>. <item> must be cleanable, hand free. As result, <item> will be clean (item_clean)."
    ],
    "goal": "Turn off all turned-on floor lamps in the living room, turn on the TV, and clean the sofa",
    "gt_cost": {"beechwood": 6},
    "item_keep": ["floor_lamp_11", "floor_lamp_14", "wall_mounted_tv_81", "sofa_82"],
    "subgoal": [
        "turn off floor_lamp_11",
        "turn off floor_lamp_14",
        "turn on TV",
        "clean sofa"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_state_off floor_lamp_11))\n""",
        """
    (:goal (item_state_off floor_lamp_14))\n""",
        """
    (:goal (item_state_on wall_mounted_tv_81))\n""",
        """
    (:goal (item_clean sofa_82))\n"""
    ]
}

KITCHEN_OFFICE_ORGANIZE = {
    "scene": ["beechwood"],
    "add_obj": None,
    "add_act": [
        "place_in(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> into <item_2>. <item_2> must be an openable container and open, <agent> holding <item_1>. As result, <item_1> in <item_2> (item_in), hand free.",
        "open(<agent>, <item>, <room>): <agent> opens <item>. <item> must be openable and closed, hand free. As result, <item> will be open.",
        "close(<agent>, <item>, <room>): <agent> closes <item>. <item> must be closeable and open, hand free. As result, <item> will be closed."
    ],
    "goal": "Close the opened chest in the kitchen, then open the closed cabinet in the home office and place the pen inside",
    "gt_cost": {"beechwood": 7},  # dining→kitchen close(chest)→kitchen→living→office open(cab) pick(pen) place_in
    "item_keep": ["pen_121", "chest_8", "bottom_cabinet_35"],
    "subgoal": [
        "close chest in kitchen",
        "go to home office, pick pen, open cabinet, place pen in cabinet"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_closed chest_8))\n""",
        """
    (:goal (item_in pen_121 bottom_cabinet_35))\n"""
    ]
}


# Beechwood drone-only tasks (bw_5, bw_6)
ROOM_SURVEY = {
    "scene": ["beechwood"],
    "add_obj": ["drone"],  # drone is a separate type from agent
    "add_act": [
        "Note: drone_1 is drone type. This is a drone-only task with no manipulation.",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2> (not at <room1> anymore). Uses drone_at predicate.",
        "check_drone(<drone>, <item>, <room>): <drone> visually inspects <item> at <room>. <item> must be a lamp (item_lamp), <drone> and <item> in <room>. As result, <item> will be checked (item_checked). Drone has no arms so cannot pick/drop items."
    ],
    "goal": "Fly to every room in the house and check the state of all lamps",
    "gt_cost": {
        "beechwood": 10  # corr→living check(11,14)→living→kitchen→dining check(23,24)→dining→stair→lobby check(29) = 5 flights + 5 checks
    },
    "item_keep": ["floor_lamp_11", "floor_lamp_14", "floor_lamp_23", "floor_lamp_24", "floor_lamp_29"],
    "subgoal": [
        "drone flies to living_room_13 and checks floor_lamp_11",
        "drone checks floor_lamp_14 in living_room_13",
        "drone flies to dining_room_10 via kitchen and checks floor_lamp_23",
        "drone checks floor_lamp_24 in dining_room_10",
        "drone flies to lobby_14 via staircase and checks floor_lamp_29"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_checked floor_lamp_11)
    )\n""",
        """
    (:goal
        (item_checked floor_lamp_14)
    )\n""",
        """
    (:goal
        (item_checked floor_lamp_23)
    )\n""",
        """
    (:goal
        (item_checked floor_lamp_24)
    )\n""",
        """
    (:goal
        (item_checked floor_lamp_29)
    )\n"""
    ],
    "robots": ["drone_1"]  # Drone-only task
}

APPLIANCE_INSPECTION = {
    "scene": ["beechwood"],
    "add_obj": ["drone"],  # drone is a separate type from agent
    "add_act": [
        "Note: drone_1 is drone type. This is a drone-only task with no manipulation.",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2> (not at <room1> anymore). Uses drone_at predicate.",
        "check_drone(<drone>, <item>, <room>): <drone> visually inspects <item> at <room>. <item> must be an appliance (item_appliance), <drone> and <item> in <room>. As result, <item> will be checked (item_checked). Drone has no arms so cannot pick/drop items."
    ],
    "goal": "Fly through the kitchen and the utility room to verify the presence and location of the burner, microwave, fridge, washer, and dryer",
    "gt_cost": {
        "beechwood": 9  # corr→utility check(washer,dryer)→utility→bath→stair→kitchen check(burner,micro,fridge) = 4 flights + 5 checks
    },
    "item_keep": ["burner_77", "microwave_60", "fridge_57", "washer_47", "dryer_48"],
    "subgoal": [
        "drone flies to kitchen_12 and checks burner_77",
        "drone checks microwave_60 in kitchen_12",
        "drone checks fridge_57 in kitchen_12",
        "drone flies to utility_room_18 via corridor and checks washer_47",
        "drone checks dryer_48 in utility_room_18"
    ],
    "subgoal_pddl": [
        """
    (:goal
        (item_checked burner_77)
    )\n""",
        """
    (:goal
        (item_checked microwave_60)
    )\n""",
        """
    (:goal
        (item_checked fridge_57)
    )\n""",
        """
    (:goal
        (item_checked washer_47)
    )\n""",
        """
    (:goal
        (item_checked dryer_48)
    )\n"""
    ],
    "robots": ["drone_1"]  # Drone-only task
}


# Helper functions for DELTA integration
GLASS_DELIVERY = {
    "scene": ["merom"],
    "add_obj": None,
    "add_act": [
        "Note: robot_1 is agent type, drone_1 is drone type. They are different types and use different predicates.",
        "open(<agent>, <item>, <room>): <agent> opens <item> at <room>. <item> must be openable, accessible, and closed, <agent> and <item> in <room>, hand free. As result, <item> will be open.",
        "check_inside_drone(<drone>, <container>, <room>): <drone> inspects inside an opened container at <room>. <container> must be accessible and currently open, <drone> and <container> in <room>. As result, <container> will be checked.",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2>. Uses drone_at predicate."
    ],
    "goal": "Open the fridge in the kitchen so the drone can inspect what is inside",
    "gt_cost": {"merom": 6},
    "item_keep": ["fridge_57"],
    "subgoal": [
        "robot navigates to kitchen and opens fridge",
        "drone navigates to kitchen and inspects inside fridge"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_open fridge_57))\n""",
        """
    (:goal (item_checked fridge_57))\n"""
    ],
    "robots": ["robot_1", "drone_1"]
}

CROSS_DELIVERY = {
    "scene": ["merom"],
    "add_obj": None,
    "add_act": [
        "Note: robot_1 is agent type, drone_1 is drone type. They are different types and use different predicates.",
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2>. <item_2> must be a surface and accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> on <item_2>, hand free.",
        "check_drone(<drone>, <item>, <room>): <drone> checks <item> at <room>. <item> must be accessible, <drone> and <item> in <room>. As result, <item> will be checked.",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2>. Uses drone_at predicate."
    ],
    "goal": "Bring the atomizer to the coffee table in the living room and the notebook to the dining table, and have the drone check the opened windows",
    "gt_cost": {"merom": 13},
    "item_keep": ["notebook_101", "atomizer_96", "table_20", "coffee_table_27", "window_77", "window_82"],
    "subgoal": [
        "robot delivers atomizer to coffee table and notebook to dining table",
        "drone checks opened windows"
    ],
    "subgoal_pddl": [
        """
    (:goal (and (item_on atomizer_96 coffee_table_27) (item_on notebook_101 table_20)))\n""",
        """
    (:goal (and (item_checked window_77) (item_checked window_82)))\n"""
    ],
    "robots": ["robot_1", "drone_1"]
}

KITCHEN_SURVEY = {
    "scene": ["merom"],
    "add_obj": None,
    "add_act": [
        "Note: robot_1 is agent type, drone_1 is drone type. They are different types and use different predicates.",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item> at <room>. <item> must be turnable, accessible, currently on (state_on), hand free. As result, <item> will be off (state_off).",
        "close_window(<agent>, <window>, <room>): <agent> closes <window> at <room>. <window> must be accessible and currently open, hand free. As result, <window> will be closed.",
        "take_view(<drone>, <room>): <drone> takes aerial view of <room>. <drone> must be at <room>. As result, <room> will be viewed.",
        "goto_drone(<drone>, <room1>, <room2>): <drone> flies from <room1> to <room2>. <drone> is at <room1>, <room1> and <room2> are neighbors. As result, <drone> will be at <room2>. Uses drone_at predicate."
    ],
    "goal": "Turn off the stove in the kitchen and close the opened window in the dining room, and have the drone survey the bedroom, child's room, and bathroom",
    "gt_cost": {"merom": 10},
    "item_keep": ["stove_59", "window_77"],
    "subgoal": [
        "robot turns off stove and closes window",
        "drone surveys bedroom, childs room, bathroom"
    ],
    "subgoal_pddl": [
        """
    (:goal (and (item_state_off stove_59) (item_closed window_77)))\n""",
        """
    (:goal (and (room_viewed bedroom_3) (room_viewed childs_room_5) (room_viewed bathroom_2)))\n"""
    ],
    "robots": ["robot_1", "drone_1"]
}


ZONE_CLEANUP = {
    "scene": ["merom"],
    "add_obj": None,
    "add_act": [
        "Note: robot_1 and robot_2 are both agent type. They have zone restrictions on movement. Do NOT use a generic goto action — use goto_r1 for robot_1 and goto_r2 for robot_2.",
        "goto_r1(<agent>, <room1>, <room2>): robot_1 goes from <room1> to <room2>. <room1> and <room2> must be neighbors, <room2> must be allowed for robot_1 (room_allowed_r1). Only robot_1 can use this action (is_robot_1).",
        "goto_r2(<agent>, <room1>, <room2>): robot_2 goes from <room1> to <room2>. <room1> and <room2> must be neighbors, <room2> must be allowed for robot_2 (room_allowed_r2). Only robot_2 can use this action (is_robot_2).",
        "turn_off(<agent>, <item>, <room>): <agent> turns off <item> at <room>. <item> must be turnable, accessible, currently on (state_on), hand free. As result, <item> will be off (state_off).",
        "close(<agent>, <item>, <room>): <agent> closes <item> at <room>. <item> must be closeable, accessible, currently open, hand free. As result, <item> will be closed."
    ],
    "goal": "Turn off all the floor lamps that are on, turn off the stove, and close all opened windows. robot_1 cannot enter the kitchen, dining room, or child's room. robot_2 cannot enter the living room, bathroom, or bedroom.",
    "gt_cost": {"merom": 9},
    "item_keep": ["floor_lamp_31", "floor_lamp_33", "stove_59", "window_77", "window_82"],
    "subgoal": [
        "robot_1 turns off floor lamps and closes window in living room",
        "robot_2 turns off stove in kitchen and closes window in dining room"
    ],
    "subgoal_pddl": [
        """
    (:goal (and (item_state_off floor_lamp_31) (item_state_off floor_lamp_33) (item_closed window_82)))\n""",
        """
    (:goal (and (item_state_off stove_59) (item_closed window_77)))\n"""
    ],
    "robots": ["robot_1", "robot_2"]
}

ZONE_DELIVERY = {
    "scene": ["merom"],
    "add_obj": None,
    "add_act": [
        "Note: robot_1 and robot_2 are both agent type. They have zone restrictions on movement. Do NOT use a generic goto action.",
        "goto_r1(<agent>, <room1>, <room2>): robot_1 goes from <room1> to <room2>. <room1> and <room2> must be neighbors, <room2> must be allowed for robot_1 (room_allowed_r1). Only robot_1 can use this action (is_robot_1).",
        "goto_r2(<agent>, <room1>, <room2>): robot_2 goes from <room1> to <room2>. <room1> and <room2> must be neighbors, <room2> must be allowed for robot_2 (room_allowed_r2). Only robot_2 can use this action (is_robot_2).",
        "place_on(<agent>, <item_1>, <item_2>, <room>): <agent> places <item_1> on <item_2>. <item_2> must be a surface and accessible, <agent> holding <item_1>, <agent> and <item_2> in <room>. As result, <item_1> on <item_2>, hand free."
    ],
    "goal": "Put the notebook on the bottom cabinet in the bedroom and the wine bottle on the dining table. robot_1 cannot enter the kitchen, dining room, or child's room. robot_2 cannot enter the living room, bathroom, or bedroom.",
    "gt_cost": {"merom": 9},
    "item_keep": ["notebook_101", "wine_bottle_94", "bottom_cabinet_8", "table_20"],
    "subgoal": [
        "robot_1 picks notebook from living room and places on bedroom cabinet",
        "robot_2 picks wine bottle from kitchen and places on dining table"
    ],
    "subgoal_pddl": [
        """
    (:goal (item_on notebook_101 bottom_cabinet_8))\n""",
        """
    (:goal (item_on wine_bottle_94 table_20))\n"""
    ],
    "robots": ["robot_1", "robot_2"]
}


def get_example(domain: str):
    """Get task example by domain name"""
    domain_upper = domain.upper()
    if domain_upper in globals():
        return eval(domain_upper)
    else:
        raise ValueError(f"Domain '{domain}' not found in HEART examples")

def get_scenes(domain: str):
    """Get available scenes for a domain"""
    return get_example(domain)["scene"]

# Export all tasks
__all__ = [
    # Beechwood tasks (bw_0~9)
    'TURN_OFF_LIGHTS', 'LAUNDRY', 'MEAL_PREP', 'PACK_WORK', 'KITCHEN_SAFETY',
    'ROOM_SURVEY', 'APPLIANCE_INSPECTION',
    'KITCHEN_RESTOCK', 'FRIDGE_THEN_OVEN', 'DISHWASHER_LOAD',
    'MULTI_CONTAINER_STORE', 'CROSS_HOUSE_DELIVERY', 'MILK_TO_UTILITY',
    'EVENING_LIVING_ROOM', 'KITCHEN_OFFICE_ORGANIZE',
    # Benevolence tasks
    'PACK_ESSENTIALS', 'SERVE_FOOD', 'CLEAN_KITCHEN',
    'MICROWAVE_APPLE', 'BOWL_TO_OVEN', 'SUNGLASS_IN_BRIEFCASE',
    'CHEESE_FROM_FRIDGE', 'CLEAN_AND_CUP', 'NEAREST_FOOD', 'BOOK_TO_CORRIDOR',
    'LIVING_ROOM_SETUP', 'CLOSE_LARGEST_FURNITURE', 'VISIT_ROOMS',
    # Merom tasks (multi-robot)
    'HOME_SECURITY', 'CLEAN_AND_INSPECT', 'PAPER_TOWEL_ORGANIZATION',
    'EVENING_PREPARATION', 'PARTY_PREPARATION',
    'GLASS_DELIVERY', 'CROSS_DELIVERY', 'KITCHEN_SURVEY',
    'ZONE_CLEANUP', 'ZONE_DELIVERY',
    # Helper functions
    'get_example', 'get_scenes'
]