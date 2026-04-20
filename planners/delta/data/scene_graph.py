"""
DELTA Scene Graphs and Robot Configs (HEART addition)

Scene graph data for all 3 evaluation scenes (Beechwood, Benevolence, Merom)
in DELTA's expected format. Includes room connectivity, object affordances,
and robot configurations. Extended from original DELTA's single-scene format
to support HEART's multi-scene evaluation.
"""

import copy

# ============================================================
# ROBOT CONFIGS — referenced by task.robots field
# ============================================================
# Each task specifies which robots it uses via task.robots = {"name": "urdf_key"}.
# load_scene_graph() injects the appropriate configs into the scene graph's "robots" field.

ROBOT_CONFIGS = {
    "fetch_gripper": {
        "state": "hand-free",
        "robot_type": "fetch",
        "robot_specs": {
            "gripper": {
                "has_gripper": True, "num_grippers": 1,
                "max_opening": 0.1, "min_opening": 0.0,
                "force_range": [0.0, 60.0], "num_fingers": 2,
            },
            "arm": {"has_arm": True, "num_arms": 1, "degrees_of_freedom": 9, "max_reach": 1.88},
            "payload": {
                "max_weight": None,
                "max_torque": {
                    "r_wheel_joint": 8.85, "l_wheel_joint": 8.85,
                    "torso_lift": 450.0, "head_pan_joint": 0.32, "head_tilt_joint": 0.68,
                    "shoulder": 131.76, "upperarm_roll_joint": 76.94, "elbow": 66.18,
                    "forearm_roll_joint": 29.35, "wrist": 25.7,
                    "r_gripper_finger_joint": 60.0, "l_gripper_finger_joint": 60.0,
                },
            },
            "base": {
                "footprint": "base_link", "max_velocity": 17.4,
                "mobility_type": "wheeled", "has_mobility": True, "torso_lift": 0.386,
            },
            "sensors": {
                "has_camera": True, "has_depth": True, "has_lidar": True,
                "camera_height": 1.046,
            },
        },
        "capabilities": [
            "goto", "pick", "drop", "put_in", "place_in",
            "turn_on", "turn_off", "open", "close", "clean", "observe",
        ],
    },
    "quadrotor": {
        "state": "airborne",
        "robot_type": "quadrotor",
        "robot_specs": {
            "gripper": {"has_gripper": False},
            "arm": {"has_arm": False},
            "base": {
                "mobility_type": "flying", "has_mobility": True, "max_velocity": 5.0,
            },
            "sensors": {
                "has_camera": True, "has_depth": True, "has_lidar": False,
                "camera_height": None,
            },
        },
        "capabilities": ["goto_drone", "check_drone", "take_view", "inspect"],
    },
    "jr2_kinova_gripper": {
        "state": "hand-free",
        "robot_type": "mobile_manipulator",
        "robot_specs": {
            "gripper": {
                "has_gripper": True, "num_grippers": 1,
                "max_opening": 0.088, "min_opening": 0.0,
                "force_range": [0.0, 40.0], "num_fingers": 2,
            },
            "arm": {"has_arm": True, "num_arms": 1, "max_reach": 0.985},
            "payload": {"max_weight": 2.6},
            "base": {
                "mobility_type": "wheeled", "has_mobility": True,
            },
            "sensors": {
                "has_camera": True, "has_depth": True, "has_lidar": True,
            },
        },
        "capabilities": [
            "goto", "pick", "drop", "put_in", "place_in",
            "turn_on", "turn_off", "open", "close", "clean", "observe",
        ],
    },
}

# Default robot assignment per scene (used when task.robots is not specified)
SCENE_DEFAULT_ROBOTS = {
    "allensville": {"robot": ("fetch_gripper", "living_room")},
    "beechwood":   {"robot": ("fetch_gripper", "bathroom_1")},
    "benevolence": {"robot": ("fetch_gripper", "living_room_12")},
    "merom":       {
        "robot_1": ("fetch_gripper", "bedroom_3"),
        "drone_1": ("quadrotor", "bedroom_3"),
    },
}

ALLENSVILLE = {
    "name": "allensville",
    "rooms": {
        "bathroom_1": {
            "items": {
                "psu": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "sink_1": {
                    "accessible": True,
                    "affordance": ["clean_mop"],
                    "state": "free"
                },
                "toilet_1": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "plant_1": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "mop": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "clean_mop", "mop_floor"],
                    "state": "clean"
                }
            },
            "neighbor": ["corridor_2"]
        },
        "bathroom_2": {
            "items": {
                "gpu": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "sink_2": {
                    "accessible": True,
                    "affordance": ["clean_mop"],
                    "state": "free"
                },
                "toilet_2": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "plant_2": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                }
            },
            "neighbor": ["corridor_3"]
        },
        "bedroom_1": {
            "items": {
                "mainboard": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "glass": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "place_on"],
                    "state": "free"
                },
                "bed_1": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "shelf": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "load", "unload"],
                    "state": "loaded",
                    "content": {
                        "book": {
                            "accessible": True,
                            "affordance": ["pick", "place_in", "drop"],
                            "state": "free"
                        }
                    }
                }
            },
            "neighbor": ["corridor_2"]
        },
        "bedroom_2": {
            "items": {
                "cpu": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "rotting_apple": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "dispose"],
                    "state": "free"
                },
                "plate": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "place_on"],
                    "state": "free"
                },
                "bed_2": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "lamp": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                }
            },
            "neighbor": ["corridor_3"]
        },
        "corridor_1": {
            "items": {},
            "neighbor": ["lobby", "corridor_3"]
        },
        "corridor_2": {
            "items": {
                "fridge_1": {
                    "accessible": True,
                    "affordance": ["open", "close"],
                    "state": "closed, off"
                },
                "fridge_2": {
                    "accessible": True,
                    "affordance": ["open", "close"],
                    "state": "closed, off"
                }
            },
            "neighbor": ["bathroom_1", "bedroom_1", "corridor_3"]
        },
        "corridor_3": {
            "items": {},
            "neighbor": ["corridor_1", "corridor_2", "bathroom_2", "bedroom_2", "kitchen", "living_room"]
        },
        "dining_room": {
            "items": {
                "ssd": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "clock": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "cola_can": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "dispose"],
                    "state": "free"
                },
                "chair_1": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "chair_2": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "dining_table": {
                    "accessible": True,
                    "affordance": [],
                    "state": "free"
                }
            },
            "neighbor": ["kitchen", "living_room"]
        },
        "kitchen": {
            "items": {
                "knife": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "place_on"],
                    "state": "free"
                },
                "fork": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "place_on"],
                    "state": "free"
                },
                "spoon": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "place_on"],
                    "state": "free"
                },
                "microwave": {
                    "accessible": True,
                    "affordance": ["open", "close", "turnon", "turnoff"],
                    "state": "closed, off"
                },
                "oven": {
                    "accessible": True,
                    "affordance": ["turnon", "turnoff"],
                    "state": "closed, off"
                },
                "rubbish_bin": {
                    "accessible": True,
                    "affordance": ["dispose"],
                    "state": "free"
                },
                "fridge_3": {
                    "accessible": True,
                    "affordance": ["open", "close"],
                    "state": "free"
                },
                "chair_3": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                }
            },
            "neighbor": ["corridor_3", "dining_room"]
        },
        "living_room": {
            "items": {
                "desk": {
                    "accessible": True,
                    "affordance": [],
                    "state": "free"
                },
                "bowl_2": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "bowl_3": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "robot_hub": {
                    "accessible": True,
                    "affordance": ["charge"],
                    "state": "free"
                },
                "chair_4": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "chair_5": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                },
                "couch": {
                    "accessible": False,
                    "affordance": [],
                    "state": "free"
                }
            },
            "neighbor": ["corridor_3", "dining_room"]
        },
        "lobby": {
            "items": {
                "ram": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop"],
                    "state": "free"
                },
                "banana_peel": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "dispose"],
                    "state": "free"
                },
                "flower": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "place_on"],
                    "state": "free"
                },
                "locker": {
                    "accessible": True,
                    "affordance": ["pick", "place_in", "drop", "load", "unload"],
                    "state": "loaded",
                    "content": {
                        "paper": {
                            "accessible": True,
                            "affordance": ["pick", "place_in", "drop"],
                            "state": "free"
                        }
                    }
                }
            },
            "neighbor": ["corridor_1"]
        }
    },
}

BEECHWOOD = {
    "name": "beechwood",
    "rooms": {
        "bathroom_1": {
            "location": [-2.64407, 3.17261, 1.157961],
            "size": [2.0274, 2.63428, 2.38526],
            "items": {
                "sink_51": {
                    "location": [-3.01, 4.05, 0.45],
                    "size": [1.26, 0.48, 0.9],
                    "affordance": ["empty_to_sink", "fill_from_sink", "place_in_sink"],
                    "accessible": True
                },
                "toilet_53": {
                    "location": [-2.025, 3.925, 0.4],
                    "size": [0.51, 0.73, 0.8],
                    "affordance": ["clean", "flush"],
                    "accessible": True
                }
            },
            "neighbor": ["home_office_11", "lobby_14", "staircase_16", "utility_room_18", "corridor_8"]
        },
        "corridor_8": {
            "location": [-2.608525, 0.477575, 1.166395],
            "size": [2.98659, 4.22923, 2.36339],
            "items": {},
            "neighbor": ["bathroom_1", "home_office_11", "living_room_13", "staircase_16", "utility_room_18"]
        },
        "dining_room_10": {
            "location": [-9.19996, -1.09664, 1.163251],
            "size": [3.84848, 4.1661, 2.366217],
            "items": {
                "table_16": {
                    "location": [-9.105, -1.0, 0.3775],
                    "size": [1.03, 2.04, 0.745],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "floor_lamp_23": {
                    "location": [-10.7, 0.36, 0.83],
                    "size": [0.42, 0.42, 1.66],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "floor_lamp_24": {
                    "location": [-7.79, 0.545, 0.7],
                    "size": [0.42, 0.37, 1.4],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_off"],
                    "accessible": True
                },
                "bowl_117": {
                    "location": [-8.97, -1.06, 0.833],
                    "size": [0.18, 0.18, 0.09],
                    "affordance": ["pick", "place_in", "drop", "clean"],
                    "state": ["empty"],
                    "parent": ["table_16"],
                    "relation": ["on"],
                    "accessible": True
                }
            },
            "neighbor": ["kitchen_12", "staircase_16"]
        },
        "home_office_11": {
            "location": [-0.17087, 0.10506, 1.178382],
            "size": [3.85742, 3.04248, 2.384757],
            "items": {
                "swivel_chair_0": {
                    "location": [0.695, 0.565, 0.45],
                    "size": [0.659, 0.664, 0.9],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "bottom_cabinet_35": {
                    "location": [0.005, -1.155, 0.35],
                    "size": [0.75, 0.43, 0.7],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "shelf_36": {
                    "location": [-1.8975, -0.77, 1.2],
                    "size": [0.375, 1.24, 2.4],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "table_37": {
                    "location": [1.36, 0.185, 0.35],
                    "size": [0.611, 1.121, 0.7],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "table_38": {
                    "location": [0.395, 1.31, 0.35],
                    "size": [1.31, 0.6, 0.7],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "bottom_cabinet_39": {
                    "location": [1.358, -0.787, 0.35],
                    "size": [0.609, 0.786, 0.7],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["opened"],
                    "accessible": True
                },
                "table_41": {
                    "location": [1.365, 1.18, 0.35],
                    "size": [0.61, 0.84, 0.7],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "pen_121": {
                    "location": [1.454, 0.137, 0.707],
                    "size": [0.016, 0.135, 0.016],
                    "affordance": ["pick", "place_in", "drop"],
                    "parent": ["table_41"],
                    "relation": ["on"],
                    "accessible": True
                }
            },
            "neighbor": ["bathroom_1", "living_room_13", "utility_room_18", "corridor_8"]
        },
        "kitchen_12": {
            "location": [-5.38437, -4.11597, 1.18717],
            "size": [5.51159, 5.33513, 2.41015],
            "items": {
                "table_7": {
                    "location": [-3.395, -5.57, 0.375],
                    "size": [1.37, 0.76, 0.75],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "chest_8": {
                    "location": [-5.235, -6.52, 0.15],
                    "size": [0.57, 0.32, 0.3],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["opened"],
                    "accessible": True
                },
                "shelf_9": {
                    "location": [-5.403, -5.926, 0.4],
                    "size": [0.399, 0.692, 0.8],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_54": {
                    "location": [-5.0, -1.81, 0.425],
                    "size": [1.02, 0.58, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_55": {
                    "location": [-4.22, -1.81, 0.425],
                    "size": [0.5, 0.58, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "countertop_56": {
                    "location": [-4.72, -1.8, 0.86],
                    "size": [1.58, 0.6, 0.02],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "fridge_57": {
                    "location": [-6.85, -1.85, 0.875],
                    "size": [0.94, 0.64, 1.75],
                    "affordance": ["close", "open", "place_in", "turn_on", "turn_off"],
                    "state": ["opened", "turned_off"],
                    "accessible": True
                },
                "bottom_cabinet_58": {
                    "location": [-5.945, -1.825, 0.15],
                    "size": [0.83, 0.59, 0.3],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "oven_59": {
                    "location": [-5.945, -1.825, 0.825],
                    "size": [0.83, 0.59, 1.05],
                    "affordance": ["clean", "close", "open", "place_in", "turn_off", "turn_on"],
                    "state": ["closed", "turned_off"],
                    "accessible": True
                },
                "microwave_60": {
                    "location": [-5.945, -1.825, 1.55],
                    "size": [0.83, 0.59, 0.4],
                    "affordance": ["clean", "close", "open", "place_in", "turn_off", "turn_on"],
                    "state": ["opened", "turned_off"],
                    "accessible": True
                },
                "shelf_61": {
                    "location": [-6.43, -1.89, 2.075],
                    "size": [1.8, 0.46, 0.65],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "top_cabinet_62": {
                    "location": [-5.0, -1.67, 1.875],
                    "size": [1.02, 0.34, 1.05],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_63": {
                    "location": [-4.22, -1.665, 1.875],
                    "size": [0.5, 0.35, 1.05],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "sink_64": {
                    "location": [-7.37, -5.335, 0.45],
                    "size": [1.024, 1.018, 0.9],
                    "affordance": ["empty_to_sink", "fill_from_sink", "place_in_sink"],
                    "accessible": True
                },
                "countertop_65": {
                    "location": [-7.88, -4.861, 0.86],
                    "size": [0.799, 0.801, 0.02],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "countertop_66": {
                    "location": [-7.755, -4.035, 0.86],
                    "size": [0.61, 1.55, 0.02],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "countertop_67": {
                    "location": [-6.24, -5.735, 0.86],
                    "size": [1.26, 0.65, 0.02],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "countertop_68": {
                    "location": [-6.897, -5.788, 0.86],
                    "size": [0.755, 0.76, 0.02],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "countertop_69": {
                    "location": [-7.801, -5.850, 0.86],
                    "size": [1.521, 1.479, 0.02],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_70": {
                    "location": [-7.765, -3.64, 0.425],
                    "size": [0.611, 0.74, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_71": {
                    "location": [-7.765, -4.425, 0.425],
                    "size": [0.611, 0.79, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "dishwasher_72": {
                    "location": [-5.985, -5.735, 0.425],
                    "size": [0.67, 0.63, 0.85],
                    "affordance": ["clean", "open", "close", "place_in", "turn_on", "turn_off"],
                    "state": ["closed", "turned_off"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_73": {
                    "location": [-6.595, -5.735, 0.425],
                    "size": [0.51, 0.65, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_74": {
                    "location": [-6.255, -5.875, 1.875],
                    "size": [1.19, 0.37, 1.05],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_75": {
                    "location": [-7.8975, -3.6675, 1.875],
                    "size": [0.335, 0.845, 1.05],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "countertop_76": {
                    "location": [-5.615, -3.825, 0.865],
                    "size": [1.85, 0.91, 0.01],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "burner_77": {
                    "location": [-5.755, -3.98, 0.905],
                    "size": [0.89, 0.56, 0.07],
                    "affordance": ["turn_off", "turn_on"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_78": {
                    "location": [-4.985, -3.96, 0.425],
                    "size": [0.59, 0.6, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_79": {
                    "location": [-6.38, -3.96, 0.425],
                    "size": [0.3, 0.6, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_90": {
                    "location": [-5.75, -3.98, 0.425],
                    "size": [0.89, 0.56, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "hamburger_114": {
                    "location": [-3.001, -5.570, 0.751],
                    "size": [0.08, 0.08, 0.04],
                    "affordance": ["pick", "place_in", "drop"],
                    "parent": ["table_7"],
                    "relation": ["on"],
                    "accessible": True
                },
                "cereal_115": {
                    "location": [-3.5, -5.570, 0.751],
                    "size": [0.08, 0.17, 0.25],
                    "affordance": ["pick", "place_in", "drop", "pour"],
                    "parent": ["table_7"],
                    "relation": ["on"],
                    "accessible": True
                },
                "salad_116": {
                    "location": [-7.760, -4.040, 0.878],
                    "size": [0.458, 0.681, 0.094],
                    "affordance": ["pick", "place_in", "drop"],
                    "parent": ["countertop_66"],
                    "relation": ["on"],
                    "accessible": True
                },
                "milk_118": {
                    "location": [-6.24, -5.73, 0.87],
                    "size": [0.08, 0.08, 0.20],
                    "affordance": ["pick", "place_in", "drop", "pour"],
                    "parent": ["countertop_67"],
                    "relation": ["on"],
                    "accessible": True
                },
            },
            "neighbor": ["dining_room_10", "living_room_13", "staircase_16"]
        },
        "living_room_13": {
            "location": [-0.503, -3.743, 1.097],
            "size": [4.455, 4.547, 2.561],
            "items": {
                "shelf_10": {
                    "location": [-0.825, -1.79, 0.125],
                    "size": [1.65, 0.54, 0.25],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "floor_lamp_11": {
                    "location": [-1.865, -1.77, 0.75],
                    "size": [0.33, 0.38, 1.5],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "coffee_table_12": {
                    "location": [-0.98, -4.4, 0.2],
                    "size": [0.88, 0.76, 0.4],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "table_13": {
                    "location": [-2.155, -3.85, 0.35],
                    "size": [0.71, 0.52, 0.7],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "floor_lamp_14": {
                    "location": [0.42, -5.755, 0.7],
                    "size": [0.42, 0.45, 1.4],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "bottom_cabinet_15": {
                    "location": [1.4925, -5.4675, 0.15],
                    "size": [0.365, 1.055, 0.3],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "rail_fence_80": {
                    "location": [-2.654, -4.742, 0.5],
                    "size": [0.068, 2.525, 1.0],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "wall_mounted_tv_81": {
                    "location": [-0.795, -1.56, 1.305],
                    "size": [1.07, 0.08, 0.71],
                    "affordance": ["turn_off", "turn_on"],
                    "state": ["turned_off"],
                    "accessible": True
                },
                "sofa_82": {
                    "location": [-1.2, -5.455, 0.4],
                    "size": [2.76, 1.07, 0.8],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "bottom_cabinet_84": {
                    "location": [1.402, -2.152, 0.425],
                    "size": [0.537, 1.248, 0.85],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "shelf_85": {
                    "location": [1.535, -2.155, 1.625],
                    "size": [0.271, 1.251, 1.55],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "hat_113": {
                    "location": [-1.55, -5.35, 0.398],
                    "size": [0.23, 0.28, 0.09],
                    "affordance": ["pick", "place_in", "drop"],
                    "parent": ["sofa_82"],
                    "relation": ["on"],
                    "accessible": True
                },
                "briefcase_120": {
                    "location": [-0.98, -4.4, 0.508],
                    "size": [0.376, 0.396, 0.346],
                    "affordance": ["pick", "drop", "place_in"],
                    "accessible": True
                }
            },
            "neighbor": ["home_office_11", "kitchen_12", "corridor_8"]
        },
        "lobby_14": {
            "location": [-6.934, 3.28, 2.468],
            "size": [7.163, 5.735, 5.002],
            "items": {
                "piano_1": {
                    "location": [-6.87, 1.245, 0.6],
                    "size": [1.4, 0.47, 1.2],
                    "affordance": ["clean", "play"],
                    "accessible": True
                },
                "armchair_25": {
                    "location": [-9.975, 4.949, 0.425],
                    "size": [0.951, 0.95, 0.85],
                    "affordance": ["fix", "clean"],
                    "state": ["broken"],
                    "accessible": True
                },
                "table_28": {
                    "location": [-8.245, 5.71, 0.375],
                    "size": [1.61, 0.72, 0.75],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "floor_lamp_29": {
                    "location": [-6.22, 5.17, 0.88],
                    "size": [0.52, 0.46, 1.76],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "table_30": {
                    "location": [-6.4, 4.7, 0.25],
                    "size": [0.463, 0.431, 0.5],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "countertop_88": {
                    "location": [-10.422, 3.235, 1.316],
                    "size": [0.305, 2.01, 0.029],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "notebook_119": {
                    "location": [-8.391, 5.711, 0.774],
                    "size": [0.05, 0.214, 0.271],
                    "affordance": ["pick", "place_in", "drop"],
                    "parent": ["table_28"],
                    "relation": ["on"],
                    "accessible": True
                },
                "jeans_112": {
                    "location": [-9.85, 4.98, 0.219],
                    "size": [0.09, 0.098, 0.242],
                    "affordance": ["pick", "place_in", "drop"],
                    "state": ["dirty"],
                    "accessible": True
                }
            },
            "neighbor": ["bathroom_1", "staircase_16"]
        },
        "staircase_16": {
            "location": [-5.41491, -0.10924, 2.47127],
            "size": [4.21836, 2.56022, 4.98616],
            "items": {},
            "neighbor": ["bathroom_1", "corridor_8", "dining_room_10", "kitchen_12", "lobby_14"]
        },
        "utility_room_18": {
            "location": [0.00311, 3.01641, 1.1711],
            "size": [3.41379, 2.59674, 2.37866],
            "items": {
                "sink_43": {
                    "location": [-1.115, 4.0, 0.525],
                    "size": [0.79, 0.58, 1.05],
                    "affordance": ["empty_to_sink", "fill_from_sink", "place_in_sink"],
                    "accessible": True
                },
                "bottom_cabinet_44": {
                    "location": [-0.49, 4.0, 0.45],
                    "size": [0.42, 0.58, 0.9],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_45": {
                    "location": [-0.895, 4.14, 1.9],
                    "size": [1.25, 0.3, 1.0],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "washer_47": {
                    "location": [1.215, 2.83, 0.65],
                    "size": [0.911, 0.66, 1.3],
                    "affordance": ["turn_on", "turn_off", "place_in", "open", "close"],
                    "state": ["closed", "turned_off"],
                    "accessible": True
                },
                "dryer_48": {
                    "location": [1.215, 2.14, 0.65],
                    "size": [0.911, 0.66, 1.3],
                    "affordance": ["turn_on", "turn_off", "place_in", "open", "close"],
                    "state": ["opened", "turned_off"],
                    "accessible": True
                }
            },
            "neighbor": ["bathroom_1", "corridor_8", "home_office_11"]
        }
    },
}

BENEVOLENCE = {
    "name": "benevolence",
    "rooms": {
        "corridor_7": {
            "location": [-2.030, -3.526, 1.192],
            "size": [5.0, 8.0, 2.44],
            "items": {
                "chair_5": {
                    "location": [-2.280, -2.515, 0.600],
                    "size": [0.372, 0.402, 1.200],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "shelf_6": {
                    "location": [-2.300, -1.990, 0.730],
                    "size": [0.326, 0.500, 1.460],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "shelf_7": {
                    "location": [-2.295, -3.385, 0.230],
                    "size": [0.390, 1.138, 0.460],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "console_table_9": {
                    "location": [-3.295, -6.980, 0.350],
                    "size": [0.572, 0.324, 0.700],
                    "affordance": ["place_on", "clean"],
                    "accessible": True
                },
                "sandwich_70": {
                    "location": [-2.0, -3.5, 0.85],
                    "size": [0.12, 0.07, 0.05],
                    "affordance": ["pick", "place_in", "place_on"],
                    "accessible": True,
                    "parent": ["console_table_9"],
                    "relation": ["on"]
                },
                "shelf_41": {
                    "location": [-2.285, -3.105, 1.030],
                    "size": [0.364, 0.580, 0.360],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "shelf_47": {
                    "location": [-3.700, -6.305, 1.600],
                    "size": [0.108, 0.430, 0.800],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "notebook_54": {
                    "location": [-3.650, -6.315, 2.504],
                    "size": [0.025, 0.107, 0.135],
                    "affordance": ["pick", "place_on", "place_in"],
                    "parent": ["shelf_47"],
                    "relation": ["on"],
                    "accessible": True
                }
            },
            "neighbor": ["kitchen_11", "living_room_12", "staircase_15", "dining_room_9"]
        },
        "dining_room_9": {
            "location": [0.248, -2.201, 1.149],
            "size": [2.608, 3.282, 2.330],
            "neighbor": ["kitchen_11", "living_room_12", "staircase_15", "corridor_7"],
            "items": {
                "table_1": {
                    "location": [0.110, -2.345, 0.380],
                    "size": [1.140, 0.710, 0.760],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "chair_2": {
                    "location": [0.620, -2.365, 0.400],
                    "size": [0.339, 0.368, 0.800],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "chair_3": {
                    "location": [-0.450, -2.345, 0.400],
                    "size": [0.333, 0.362, 0.800],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "chair_4": {
                    "location": [0.100, -2.905, 0.400],
                    "size": [0.365, 0.336, 0.800],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "countertop_14": {
                    "location": [0.210, -1.090, 1.050],
                    "size": [2.320, 0.460, 0.100],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "window_50": {
                    "location": [1.491, -2.325, 1.250],
                    "size": [0.219, 1.851, 1.500],
                    "affordance": ["open", "close", "clean"],
                    "accessible": True,
                    "state": ["opened"]
                },
                "notebook_64": {
                    "location": [-0.101, -2.351, 0.781],
                    "size": [0.050, 0.214, 0.271],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["table_1"],
                    "relation": ["on"]
                },
                "bowl_55": {
                    "location": [0.400, -2.350, 0.842],
                    "size": [0.330, 0.294, 0.170],
                    "affordance": ["pick", "place_in", "drop", "clean"],
                    "accessible": True,
                    "parent": ["table_1"],
                    "relation": ["on"]
                },
                "bowl_63": {
                    "location": [0.500, -2.550, 0.842],
                    "size": [0.100, 0.052, 0.050],
                    "affordance": ["pick", "place_in", "drop", "clean"],
                    "accessible": True,
                    "parent": ["table_1"],
                    "relation": ["on"]
                }
            }
        },
        "kitchen_11": {
            "location": [-0.269, 0.444, 1.169],
            "size": [3.598, 2.827, 2.358],
            "neighbor": ["staircase_15", "corridor_7", "dining_room_9"],
            "items": {
                "bottom_cabinet_no_top_15": {
                    "location": [0.595, -0.545, 0.440],
                    "size": [0.336, 0.574, 0.880],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_16": {
                    "location": [-0.470, -0.555, 0.440],
                    "size": [0.926, 0.580, 0.880],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_17": {
                    "location": [0.213, -0.551, 0.440],
                    "size": [0.404, 0.581, 0.880],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "countertop_18": {
                    "location": [0.695, 1.520, 0.890],
                    "size": [1.310, 0.620, 0.020],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "sink_19": {
                    "location": [1.060, 0.145, 0.450],
                    "size": [0.580, 0.770, 0.900],
                    "affordance": ["empty_to_sink", "fill_from_sink", "place_in_sink"],
                    "accessible": True
                },
                "dishwasher_20": {
                    "location": [1.063, 0.877, 0.440],
                    "size": [0.533, 0.553, 0.880],
                    "affordance": ["clean", "open", "close", "place_in", "turn_on", "turn_off"],
                    "state": ["closed", "turned_off"],
                    "accessible": True
                },
                "countertop_21": {
                    "location": [0.205, -0.555, 0.890],
                    "size": [2.290, 0.570, 0.020],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_22": {
                    "location": [0.420, 1.515, 0.440],
                    "size": [0.700, 0.590, 0.880],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "countertop_23": {
                    "location": [1.065, 0.880, 0.890],
                    "size": [0.570, 0.660, 0.020],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "cup_68": {
                    "location": [-0.3, 1.5, 0.93],
                    "size": [0.10, 0.10, 0.12],
                    "affordance": ["pick", "place_in", "place_on"],
                    "accessible": True,
                    "parent": ["countertop_23"],
                    "relation": ["on"]
                },
                "cup_69": {
                    "location": [-0.5, 1.5, 0.93],
                    "size": [0.07, 0.07, 0.09],
                    "affordance": ["pick", "place_in", "place_on"],
                    "accessible": True,
                    "parent": ["countertop_23"],
                    "relation": ["on"]
                },
                "oven_24": {
                    "location": [-0.340, 1.500, 0.440],
                    "size": [0.781, 0.642, 0.880],
                    "affordance": ["clean", "close", "open", "place_in", "turn_off", "turn_on"],
                    "state": ["closed", "turned_off"],
                    "accessible": True
                },
                "bottom_cabinet_no_top_25": {
                    "location": [-0.885, 1.515, 0.440],
                    "size": [0.270, 0.630, 0.880],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "countertop_26": {
                    "location": [-0.885, 1.515, 0.890],
                    "size": [0.270, 0.630, 0.020],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "fridge_27": {
                    "location": [-1.500, 1.390, 0.880],
                    "size": [0.920, 0.900, 1.760],
                    "affordance": ["close", "open", "place_in", "turn_on", "turn_off"],
                    "state": ["closed", "turned_on"],
                    "accessible": True
                },
                "cheese_66": {
                    "location": [-1.4, 1.4, 0.6],
                    "size": [0.06, 0.06, 0.04],
                    "affordance": ["pick", "place_in", "place_on"],
                    "accessible": True,
                    "parent": ["fridge_27"],
                    "relation": ["in"]
                },
                "cheese_67": {
                    "location": [-1.4, 1.3, 0.6],
                    "size": [0.12, 0.09, 0.09],
                    "affordance": ["pick", "place_in", "place_on"],
                    "accessible": True,
                    "parent": ["fridge_27"],
                    "relation": ["in"]
                },
                "top_cabinet_28": {
                    "location": [-1.490, 1.505, 1.950],
                    "size": [0.920, 0.650, 0.300],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_29": {
                    "location": [-0.890, 1.655, 1.735],
                    "size": [0.260, 0.350, 0.730],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_30": {
                    "location": [-0.350, 1.655, 1.920],
                    "size": [0.780, 0.350, 0.360],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_31": {
                    "location": [0.410, 1.655, 1.735],
                    "size": [0.700, 0.350, 0.730],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_32": {
                    "location": [1.270, 0.965, 1.735],
                    "size": [0.260, 0.630, 0.730],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_33": {
                    "location": [0.955, 1.655, 1.735],
                    "size": [0.350, 0.350, 0.730],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_34": {
                    "location": [1.273, 1.379, 1.735],
                    "size": [0.266, 0.162, 0.730],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "top_cabinet_35": {
                    "location": [1.285, -0.565, 1.735],
                    "size": [0.290, 0.353, 0.730],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "microwave_36": {
                    "location": [-0.350, 1.655, 1.555],
                    "size": [0.780, 0.350, 0.370],
                    "affordance": ["clean", "close", "open", "place_in", "turn_off", "turn_on"],
                    "state": ["closed", "turned_off"],
                    "accessible": True
                },
                "pen_56": {
                    "location": [1.368, 0.184, 0.087],
                    "size": [0.016, 0.135, 0.016],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["sink_19"],
                    "relation": ["in"]
                },
                "apple_57": {
                    "location": [0.851, -0.542, 0.966],
                    "size": [0.228, 0.455, 0.511],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["countertop_21"],
                    "relation": ["on"]
                },
                "apple_62": {
                    "location": [0.871, -0.522, 0.966],
                    "size": [0.066, 0.132, 0.130],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["countertop_21"],
                    "relation": ["on"]
                },
                "hamburger_58": {
                    "location": [0.700, 1.520, 0.903],
                    "size": [0.177, 0.159, 0.091],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["countertop_18"],
                    "relation": ["on"]
                }
            }
        },
        "living_room_12": {
            "location": [-0.530, -6.022, 1.165],
            "size": [4.752, 4.956, 2.356],
            "neighbor": ["staircase_15", "corridor_7", "dining_room_9"],
            "items": {
                "shelf_0": {
                    "location": [1.210, -4.405, 0.400],
                    "size": [0.359, 1.058, 0.800],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "floor_lamp_8": {
                    "location": [-2.335, -4.385, 0.715],
                    "size": [0.290, 0.330, 1.430],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_off"],
                    "accessible": True
                },
                "sofa_10": {
                    "location": [-0.715, -5.866, 0.415],
                    "size": [1.650, 2.912, 0.770],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "chest_11": {
                    "location": [0.215, -8.135, 0.250],
                    "size": [0.950, 0.430, 0.500],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["opened"],
                    "accessible": True
                },
                "chest_12": {
                    "location": [-1.785, -6.235, 0.250],
                    "size": [0.35, 0.35, 0.30],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["opened"],
                    "accessible": True
                },
                "shelf_42": {
                    "location": [-2.285, -3.695, 1.830],
                    "size": [0.384, 0.540, 0.360],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "book_71": {
                    "location": [-0.5, -6.0, 1.80],
                    "size": [0.04, 0.15, 0.20],
                    "affordance": ["pick", "place_in", "place_on"],
                    "accessible": True,
                    "parent": ["shelf_42"],
                    "relation": ["on"]
                },
                "book_72": {
                    "location": [-0.5, -5.8, 0.50],
                    "size": [0.04, 0.15, 0.20],
                    "affordance": ["pick", "place_in", "place_on"],
                    "accessible": True,
                    "parent": ["shelf_0"],
                    "relation": ["on"]
                },
                "wall_mounted_tv_49": {
                    "location": [1.381, -6.369, 1.200],
                    "size": [0.158, 1.201, 0.600],
                    "affordance": ["turn_off", "turn_on"],
                    "state": ["turned_off"],
                    "accessible": True
                },
                "window_51": {
                    "location": [1.513, -7.836, 1.250],
                    "size": [0.212, 0.949, 1.500],
                    "affordance": ["open", "close", "clean"],
                    "state": ["closed"],
                    "accessible": True
                },
                "window_53": {
                    "location": [0.315, -8.515, 1.250],
                    "size": [1.651, 0.201, 1.500],
                    "affordance": ["open", "close", "clean"],
                    "state": ["closed"],
                    "accessible": True
                },
                "hat_59": {
                    "location": [-0.710, -5.870, 0.385],
                    "size": [0.234, 0.275, 0.124],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True
                },
                "sunglass_60": {
                    "location": [1.400, -4.266, 0.635],
                    "size": [0.210, 0.112, 0.064],
                    "weight": "3.5kg",
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["shelf_0"],
                    "relation": ["on"]
                },
                "sunglass_65": {
                    "location": [1.275, -4.266, 0.635],
                    "size": [0.210, 0.112, 0.064],
                    "weight": "0.05kg",
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["shelf_0"],
                    "relation": ["on"]
                },
                "briefcase_61": {
                    "location": [-1.790, -6.231, 0.606],
                    "size": [0.376, 0.396, 0.346],
                    "affordance": ["pick", "drop", "place_in"],
                    "accessible": True,
                    "parent": ["chest_12"],
                    "relation": ["in"]
                }
            }
        },
        "staircase_15": {
            "location": [-3.183, -3.136, 2.568],
            "size": [0.992, 3.413, 5.141],
            "neighbor": ["kitchen_11", "living_room_12", "corridor_7", "dining_room_9"],
            "items": {}
        }
    },
}

MEROM = {
    "name": "merom",
    "rooms": {
        "bathroom_2": {
            "location": [3.717, 4.002, 1.752],
            "size": [2.796, 2.881, 4.078],
            "neighbor": ["living_room_10", "bedroom_3", "corridor_6"],
            "items": {
                "toilet_69": {
                    "location": [3.685, 5.050, 0.375],
                    "size": [0.450, 0.600, 0.750],
                    "affordance": ["clean", "flush"],
                    "accessible": True
                },
                "top_cabinet_70": {
                    "location": [2.720, 4.490, 1.625],
                    "size": [0.760, 0.300, 0.650],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bathtub_71": {
                    "location": [4.618, 4.274, 0.250],
                    "size": [0.931, 2.112, 0.500],
                    "affordance": ["clean"],
                    "accessible": True
                },
                "sink_72": {
                    "location": [3.685, 3.355, 0.550],
                    "size": [0.670, 0.310, 1.100],
                    "affordance": ["empty_to_sink", "fill_from_sink", "place_in_sink", "clean"],
                    "accessible": True
                }
            }
        },
        "bedroom_3": {
            "location": [3.234, 0.138, 1.207],
            "size": [3.959, 4.362, 2.501],
            "neighbor": ["bathroom_2", "childs_room_5", "corridor_6"],
            "items": {
                "bed_7": {
                    "location": [4.004, -0.146, 0.600],
                    "size": [2.128, 1.764, 1.200],
                    "affordance": ["drop", "clean", "make"],
                    "state": ["unmade"],
                    "accessible": True
                },
                "bottom_cabinet_8": {
                    "location": [4.808, -1.223, 0.250],
                    "size": [0.435, 0.355, 0.500],
                    "affordance": ["close", "open", "place_in", "drop"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_9": {
                    "location": [4.838, 0.938, 0.250],
                    "size": [0.435, 0.355, 0.500],
                    "affordance": ["close", "open", "place_in", "drop"],
                    "state": ["closed"],
                    "accessible": True
                },
                "table_lamp_10": {
                    "location": [4.845, 0.940, 0.751],
                    "size": [0.230, 0.260, 0.499],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_off"],
                    "accessible": True,
                    "parent": ["bottom_cabinet_9"],
                    "relation": ["on"]
                },
                "table_lamp_11": {
                    "location": [4.815, -1.220, 0.751],
                    "size": [0.230, 0.260, 0.499],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_off"],
                    "accessible": True,
                    "parent": ["bottom_cabinet_8"],
                    "relation": ["on"]
                },
                "bottom_cabinet_12": {
                    "location": [1.550, 0.525, 0.490],
                    "size": [0.461, 0.811, 0.980],
                    "affordance": ["close", "open", "place_in", "drop"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_13": {
                    "location": [1.550, -0.305, 0.490],
                    "size": [0.461, 0.811, 0.980],
                    "affordance": ["close", "open", "place_in", "drop"],
                    "state": ["closed"],
                    "accessible": True
                },
                "basket_14": {
                    "location": [1.501, -1.051, 0.280],
                    "size": [0.388, 0.601, 0.560],
                    "affordance": ["pick", "place_in"],
                    "accessible": True
                },
                "basket_15": {
                    "location": [1.521, -1.576, 0.280],
                    "size": [0.374, 0.399, 0.560],
                    "affordance": ["pick", "place_in"],
                    "accessible": True
                },
                "table_lamp_17": {
                    "location": [1.530, 0.725, 1.270],
                    "size": [0.320, 0.270, 0.560],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True,
                    "parent": ["bottom_cabinet_12"],
                    "relation": ["on"]
                },
                "window_79": {
                    "location": [2.260, -1.905, 1.375],
                    "size": [1.320, 0.150, 1.350],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "window_80": {
                    "location": [5.136, 1.665, 1.375],
                    "size": [0.188, 0.931, 1.350],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "atomizer_96": {
                    "location": [1.541, -0.299, 1.046],
                    "size": [0.042, 0.042, 0.158],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["bottom_cabinet_13"],
                    "relation": ["on"]
                },
                "backpack_102": {
                    "location": [2.432, -1.140, 0.027],
                    "size": [0.415, 0.350, 0.426],
                    "affordance": ["pick", "drop", "place_in"],
                    "accessible": True
                }
            }
        },
        "childs_room_5": {
            "location": [-0.705, 0.188, 1.212],
            "size": [4.023, 4.348, 2.516],
            "neighbor": ["bedroom_3", "corridor_6", "kitchen_8"],
            "items": {
                "bed_1": {
                    "location": [-2.035, -0.720, 0.550],
                    "size": [1.150, 2.080, 1.100],
                    "affordance": ["drop", "clean", "make"],
                    "state": ["unmade"],
                    "accessible": True
                },
                "bottom_cabinet_2": {
                    "location": [-1.175, -1.545, 0.330],
                    "size": [0.510, 0.370, 0.660],
                    "affordance": ["close", "open", "place_in", "drop"],
                    "state": ["closed"],
                    "accessible": True
                },
                "table_lamp_3": {
                    "location": [-1.245, -1.555, 0.931],
                    "size": [0.210, 0.230, 0.539],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_off"],
                    "accessible": True,
                    "parent": ["bottom_cabinet_2"],
                    "relation": ["on"]
                },
                "armchair_4": {
                    "location": [0.577, -1.031, 0.450],
                    "size": [1.134, 1.146, 0.900],
                    "affordance": ["fix", "clean"],
                    "state": ["broken"],
                    "accessible": True
                },
                "bottom_cabinet_6": {
                    "location": [-0.345, 1.325, 0.600],
                    "size": [0.630, 0.350, 1.200],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "window_75": {
                    "location": [-2.666, 0.917, 1.375],
                    "size": [0.123, 0.826, 1.350],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "window_78": {
                    "location": [0.335, -1.915, 1.375],
                    "size": [1.570, 0.130, 1.350],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "paper_towel_97": {
                    "location": [0.593, -1.036, 0.480],
                    "size": [0.060, 0.130, 0.220],
                    "affordance": ["pick", "place_in", "drop", "clean"],
                    "accessible": True,
                    "parent": ["armchair_4"],
                    "relation": ["on"]
                }
            }
        },
        "corridor_6": {
            "location": [1.277, 3.882, 1.223],
            "size": [2.170, 3.298, 2.465],
            "neighbor": ["living_room_10", "bathroom_2", "bedroom_3", "childs_room_5", "dining_room_7", "kitchen_8"],
            "items": {}
        },
        "dining_room_7": {
            "location": [-1.286, 7.585, 1.237],
            "size": [2.841, 2.566, 2.462],
            "neighbor": ["living_room_10", "corridor_6", "kitchen_8"],
            "items": {
                "table_20": {
                    "location": [-0.850, 7.690, 0.400],
                    "size": [1.520, 0.920, 0.800],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "chair_21": {
                    "location": [-0.040, 7.700, 0.430],
                    "size": [0.471, 0.471, 0.860],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "chair_22": {
                    "location": [-0.880, 8.170, 0.430],
                    "size": [0.460, 0.460, 0.860],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "chair_23": {
                    "location": [-0.850, 7.190, 0.430],
                    "size": [0.471, 0.471, 0.860],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "chair_24": {
                    "location": [-1.660, 7.650, 0.430],
                    "size": [0.481, 0.481, 0.860],
                    "affordance": ["clean", "drop"],
                    "accessible": True
                },
                "window_77": {
                    "location": [-2.665, 7.545, 1.475],
                    "size": [0.111, 1.130, 1.250],
                    "affordance": ["open", "close"],
                    "state": ["opened"],
                    "accessible": True
                },
                "window_92": {
                    "location": [-1.225, 8.690, 1.475],
                    "size": [1.650, 0.120, 1.250],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bowl_98": {
                    "location": [-0.850, 7.690, 0.884],
                    "size": [0.160, 0.124, 0.090],
                    "affordance": ["pick", "place_in", "drop", "clean"],
                    "accessible": True,
                    "parent": ["table_20"],
                    "relation": ["on"]
                },
                "paper_towel_105": {
                    "location": [-1.200, 7.600, 0.900],
                    "size": [0.050, 0.050, 0.150],
                    "affordance": ["pick", "place_in", "drop", "clean"],
                    "accessible": True,
                    "parent": ["table_20"],
                    "relation": ["on"]
                }
            }
        },
        "kitchen_8": {
            "location": [-1.255, 4.408, 1.231],
            "size": [2.999, 4.044, 2.466],
            "neighbor": ["childs_room_5", "corridor_6", "dining_room_7"],
            "items": {
                "bottom_cabinet_49": {
                    "location": [-2.290, 5.555, 0.450],
                    "size": [0.617, 0.499, 0.900],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_50": {
                    "location": [-2.290, 6.075, 0.450],
                    "size": [0.617, 0.499, 0.900],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "bottom_cabinet_51": {
                    "location": [-2.283, 3.643, 0.450],
                    "size": [0.625, 0.295, 0.900],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "dishwasher_52": {
                    "location": [-2.285, 4.095, 0.450],
                    "size": [0.632, 0.571, 0.900],
                    "affordance": ["clean", "open", "close", "place_in", "turn_on", "turn_off"],
                    "state": ["closed", "turned_off"],
                    "accessible": True
                },
                "sink_53": {
                    "location": [-2.290, 4.840, 0.550],
                    "size": [0.620, 0.880, 1.100],
                    "affordance": ["empty_to_sink", "fill_from_sink", "place_in_sink"],
                    "accessible": True
                },
                "top_cabinet_54": {
                    "location": [-2.435, 3.940, 1.890],
                    "size": [0.290, 0.880, 0.980],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["opened"],
                    "accessible": True
                },
                "top_cabinet_55": {
                    "location": [-2.430, 5.820, 1.890],
                    "size": [0.300, 1.000, 0.980],
                    "affordance": ["close", "open", "place_in"],
                    "state": ["closed"],
                    "accessible": True
                },
                "fridge_57": {
                    "location": [-0.272, 3.913, 0.855],
                    "size": [0.791, 0.787, 1.710],
                    "affordance": ["close", "open", "place_in", "turn_on", "turn_off"],
                    "state": ["closed", "turned_on"],
                    "accessible": True
                },
                "shelf_58": {
                    "location": [-0.155, 4.900, 0.450],
                    "size": [0.550, 1.160, 0.900],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "stove_59": {
                    "location": [-0.265, 5.910, 0.600],
                    "size": [0.770, 0.820, 1.200],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "range_hood_60": {
                    "location": [-0.168, 5.918, 2.050],
                    "size": [0.585, 0.805, 0.700],
                    "affordance": ["use"],
                    "accessible": True
                },
                "shelf_61": {
                    "location": [0.075, 5.155, 1.450],
                    "size": [0.111, 0.550, 0.500],
                    "affordance": ["drop"],
                    "accessible": True
                },
                "medicine_103": {
                    "location": [0.075, 5.155, 2.100],
                    "size": [0.080, 0.060, 0.100],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["shelf_61"],
                    "relation": ["on"]
                },
                "first_aid_kit_104": {
                    "location": [0.075, 5.300, 2.250],
                    "size": [0.150, 0.100, 0.080],
                    "affordance": ["pick", "place_in", "drop", "open", "close"],
                    "state": ["closed"],
                    "accessible": True,
                    "parent": ["shelf_61"],
                    "relation": ["on"]
                },
                "window_76": {
                    "location": [-2.670, 4.840, 1.725],
                    "size": [0.100, 0.860, 0.750],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "glass_93": {
                    "location": [-2.200, 3.940, 0.949],
                    "size": [0.100, 0.100, 0.145],
                    "affordance": ["pick", "place_in", "drop", "clean"],
                    "accessible": True,
                    "parent": ["dishwasher_52"],
                    "relation": ["in"]
                },
                "wine_bottle_94": {
                    "location": [-0.250, 4.900, 0.959],
                    "size": [0.060, 0.060, 0.226],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["shelf_58"],
                    "relation": ["on"]
                },
                "cheese_99": {
                    "location": [-0.270, 3.802, 1.706],
                    "size": [0.105, 0.084, 0.018],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["fridge_57"],
                    "relation": ["on"]
                },
                "olive_oil_100": {
                    "location": [-0.300, 4.200, 1.705],
                    "size": [0.037, 0.037, 0.108],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["fridge_57"],
                    "relation": ["on"]
                }
            }
        },
        "living_room_10": {
            "location": [2.638, 7.995, 1.219],
            "size": [5.916, 5.057, 2.495],
            "neighbor": ["bathroom_2", "corridor_6", "dining_room_7"],
            "items": {
                "sofa_25": {
                    "location": [3.121, 9.281, 0.410],
                    "size": [2.677, 0.978, 0.780],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "armchair_26": {
                    "location": [4.172, 6.281, 0.410],
                    "size": [1.057, 1.043, 0.780],
                    "affordance": ["fix", "clean"],
                    "accessible": True
                },
                "coffee_table_27": {
                    "location": [3.598, 7.815, 0.210],
                    "size": [0.605, 1.169, 0.380],
                    "affordance": ["drop", "clean"],
                    "accessible": True
                },
                "bottom_cabinet_30": {
                    "location": [0.915, 10.015, 0.350],
                    "size": [1.110, 0.330, 0.700],
                    "affordance": ["close", "open", "place_in", "drop"],
                    "state": ["closed"],
                    "accessible": True
                },
                "floor_lamp_31": {
                    "location": [4.715, 9.855, 0.755],
                    "size": [0.390, 0.370, 1.510],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "floor_lamp_33": {
                    "location": [4.810, 5.910, 0.705],
                    "size": [0.300, 0.300, 1.410],
                    "affordance": ["turn_on", "turn_off"],
                    "state": ["turned_on"],
                    "accessible": True
                },
                "window_81": {
                    "location": [5.125, 9.490, 1.475],
                    "size": [0.164, 0.731, 1.250],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "window_82": {
                    "location": [5.070, 6.310, 1.475],
                    "size": [0.060, 0.840, 1.250],
                    "affordance": ["open", "close"],
                    "state": ["opened"],
                    "accessible": True
                },
                "window_83": {
                    "location": [2.745, 10.250, 1.475],
                    "size": [2.470, 0.120, 1.250],
                    "affordance": ["open", "close"],
                    "state": ["closed"],
                    "accessible": True
                },
                "medicine_95": {
                    "location": [0.930, 10.026, 0.700],
                    "size": [0.048, 0.048, 0.080],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True,
                    "parent": ["bottom_cabinet_30"],
                    "relation": ["on"]
                },
                "notebook_101": {
                    "location": [4.089, 6.367, 0.408],
                    "size": [0.050, 0.214, 0.271],
                    "affordance": ["pick", "place_in", "drop"],
                    "accessible": True
                }
            }
        }
    },
}


# Helper functions for HEART scenes (compatible with DELTA's scene_graph.py interface)
def load_scene_graph(scene: str, task_robots: dict = None, task_positions: dict = None, domain: str = None):
    """
    Load a scene graph by name and inject robots into it.

    Args:
        scene: Scene name ("beechwood", "benevolence", "merom", "allensville")
        task_robots: Per-task robot override {robot_name: urdf_key}. If None, uses SCENE_DEFAULT_ROBOTS.
        task_positions: Per-task robot start positions {robot_name: room_name}. Optional.
        domain: (Deprecated) Kept for backward compatibility. Ignored.

    Returns:
        A deep-copied scene graph dict with a "robots" field populated from ROBOT_CONFIGS.
    """
    scene_name = scene.upper()

    if scene_name not in globals():
        raise ValueError(f"Scene '{scene}' not found. Available: ALLENSVILLE, BEECHWOOD, BENEVOLENCE, MEROM")

    sg = copy.deepcopy(globals()[scene_name])
    sg_name = sg.get("name", scene.lower())

    # Determine robot assignments for this scene/task
    defaults = SCENE_DEFAULT_ROBOTS.get(sg_name, {})
    # Scene-level fallback position: first default robot's room
    default_position = next(iter(defaults.values()))[1] if defaults else next(iter(sg["rooms"]))

    if task_robots:
        # Task override: use provided robots, positions from task_positions or scene defaults
        robot_assignments = {}
        for robot_name, urdf_key in task_robots.items():
            if urdf_key not in ROBOT_CONFIGS:
                raise ValueError(f"Unknown robot urdf_key: {urdf_key}")
            position = None
            if task_positions and robot_name in task_positions:
                position = task_positions[robot_name]
            elif robot_name in defaults:
                position = defaults[robot_name][1]
            else:
                # Robot name not in scene defaults: use scene's default room
                position = default_position
            robot_assignments[robot_name] = (urdf_key, position)
    else:
        robot_assignments = defaults

    # Inject robots into scene graph
    sg["robots"] = {}
    for robot_name, (urdf_key, position) in robot_assignments.items():
        robot_config = copy.deepcopy(ROBOT_CONFIGS[urdf_key])
        robot_config["position"] = position
        sg["robots"][robot_name] = robot_config

    return sg


def extract_accessible_items_from_sg(sg: dict):
    """Extract all accessible items from scene graph"""
    accessible_items = []
    for room_name, room_data in sg["rooms"].items():
        items = room_data.get("items", {})
        for item_name, item_data in items.items():
            if item_data.get("accessible", True):
                accessible_items.append(item_name)
    return accessible_items


def prune_sg_with_item(sg: dict, item_keep: list):
    """Prune scene graph to keep only specified items and their parent relationships"""
    pruned_sg = copy.deepcopy(sg)

    # First pass: collect all items to keep (including parent items of kept items)
    items_to_keep = set(item_keep)
    for room_name, room_data in sg["rooms"].items():
        room_items = room_data.get("items", {})
        for item_name, item_data in room_items.items():
            if item_name in item_keep:
                # If this item has a parent, keep the parent too
                if "parent" in item_data:
                    for parent_item in item_data["parent"]:
                        items_to_keep.add(parent_item)

    # Second pass: prune items
    for room_name, room_data in pruned_sg["rooms"].items():
        pruned_items = {}
        room_items = room_data.get("items", {})

        for item_name, item_data in room_items.items():
            # Keep item if it's in the keep list or is a parent of kept items
            if item_name in items_to_keep:
                pruned_items[item_name] = copy.deepcopy(item_data)

                # If this item has parent, check if parent is also kept
                if "parent" in item_data:
                    kept_parents = [p for p in item_data["parent"] if p in items_to_keep]
                    if kept_parents:
                        pruned_items[item_name]["parent"] = kept_parents
                    else:
                        # Remove parent/relation if parent is not kept
                        del pruned_items[item_name]["parent"]
                        if "relation" in pruned_items[item_name]:
                            del pruned_items[item_name]["relation"]

        room_data["items"] = pruned_items

    return pruned_sg


# Export all scenes and helper functions
__all__ = ['ALLENSVILLE', 'BEECHWOOD', 'BENEVOLENCE', 'MEROM',
           'ROBOT_CONFIGS', 'SCENE_DEFAULT_ROBOTS',
           'load_scene_graph', 'extract_accessible_items_from_sg', 'prune_sg_with_item']