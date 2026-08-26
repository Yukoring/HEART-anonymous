(define (problem beechwood_milk_to_utility)
    (:domain milk_to_utility)

    (:objects
        robot - agent
        bathroom_1 home_office_11 kitchen_12 living_room_13 lobby_14 utility_room_18 - room
        milk_118 sink_43 - item
    )

    (:init
        ; Agent starts in living room
        (agent_at robot living_room_13)

        ; Room neighbors — EXCLUDING dining_room_10, staircase_16, corridor_8
        (neighbor home_office_11 bathroom_1)
        (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18)
        (neighbor living_room_13 home_office_11)
        (neighbor living_room_13 kitchen_12)
        (neighbor kitchen_12 living_room_13)
        (neighbor bathroom_1 home_office_11)
        (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 utility_room_18)
        (neighbor lobby_14 bathroom_1)
        (neighbor utility_room_18 bathroom_1)
        (neighbor utility_room_18 home_office_11)

        ; Item locations
        (item_at milk_118 kitchen_12)
        (item_pickable milk_118)
        (item_accessible milk_118)

        (item_at sink_43 utility_room_18)
        (item_container sink_43)
        (item_accessible sink_43)
        (item_open sink_43)
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight milk_118) 0.0) (= (item_width milk_118) 0.080) (= (item_height milk_118) 0.873)
        (= (item_weight sink_43) 0.0) (= (item_width sink_43) 0.580) (= (item_height sink_43) 0.525)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot) 2.6) (= (agent_gripper robot) 0.088) (= (agent_reach robot) 1.432)  ; jr2_kinova_gripper
    )

    ; Goal: milk placed in the sink in the utility room
    (:goal
        (item_in milk_118 sink_43)
    )
)
