(define (problem beechwood_meal_prep)
    (:domain meal_prep)

    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        salad_116 hamburger_114 table_16 fridge_57 - item
    )

    (:init
        (agent_at robot bathroom_1)

        ; Room neighbors
        (neighbor bathroom_1 home_office_11) (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 staircase_16) (neighbor bathroom_1 utility_room_18)
        (neighbor bathroom_1 corridor_8)
        (neighbor corridor_8 bathroom_1) (neighbor corridor_8 home_office_11)
        (neighbor corridor_8 living_room_13) (neighbor corridor_8 staircase_16)
        (neighbor corridor_8 utility_room_18)
        (neighbor dining_room_10 kitchen_12) (neighbor dining_room_10 staircase_16)
        (neighbor home_office_11 bathroom_1) (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18) (neighbor home_office_11 corridor_8)
        (neighbor kitchen_12 dining_room_10) (neighbor kitchen_12 living_room_13)
        (neighbor kitchen_12 staircase_16)
        (neighbor living_room_13 home_office_11) (neighbor living_room_13 kitchen_12)
        (neighbor living_room_13 corridor_8)
        (neighbor lobby_14 bathroom_1) (neighbor lobby_14 staircase_16)
        (neighbor staircase_16 bathroom_1) (neighbor staircase_16 corridor_8)
        (neighbor staircase_16 dining_room_10) (neighbor staircase_16 kitchen_12)
        (neighbor staircase_16 lobby_14)
        (neighbor utility_room_18 bathroom_1) (neighbor utility_room_18 corridor_8)
        (neighbor utility_room_18 home_office_11)

        ; Items
        (item_at salad_116 kitchen_12)
        (item_pickable salad_116) (item_accessible salad_116)

        (item_at hamburger_114 kitchen_12)
        (item_pickable hamburger_114) (item_accessible hamburger_114)

        (item_at table_16 dining_room_10)
        (item_surface table_16) (item_accessible table_16)

        (item_at fridge_57 kitchen_12)
        (item_accessible fridge_57) (item_open fridge_57)
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight fridge_57) 0.0) (= (item_width fridge_57) 0.640) (= (item_height fridge_57) 0.875)
        (= (item_weight hamburger_114) 0.0) (= (item_width hamburger_114) 0.040) (= (item_height hamburger_114) 0.751)
        (= (item_weight salad_116) 0.0) (= (item_width salad_116) 0.031) (= (item_height salad_116) 0.878)
        (= (item_weight table_16) 0.0) (= (item_width table_16) 0.745) (= (item_height table_16) 0.378)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)  ; fetch_gripper
    )

    (:goal
        (and
            (item_on salad_116 table_16)
            (item_on hamburger_114 table_16)
            (item_closed fridge_57)
        )
    )
)
