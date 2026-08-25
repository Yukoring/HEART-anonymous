(define (problem benevolence_serve_food)
    (:domain serve_food)

    ; Objects
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        apple_62 hamburger_58 table_1 countertop_21 countertop_18 apple_57 - item
    )

    ; Initial state
    (:init
        ; Agent location
        (agent_at robot living_room_12)

        ; Room neighbors (bidirectional)
        (neighbor corridor_7 kitchen_11)
        (neighbor corridor_7 living_room_12)
        (neighbor corridor_7 staircase_15)
        (neighbor corridor_7 dining_room_9)

        (neighbor dining_room_9 kitchen_11)
        (neighbor dining_room_9 living_room_12)
        (neighbor dining_room_9 staircase_15)
        (neighbor dining_room_9 corridor_7)

        (neighbor kitchen_11 staircase_15)
        (neighbor kitchen_11 corridor_7)
        (neighbor kitchen_11 dining_room_9)

        (neighbor living_room_12 staircase_15)
        (neighbor living_room_12 corridor_7)
        (neighbor living_room_12 dining_room_9)

        (neighbor staircase_15 kitchen_11)
        (neighbor staircase_15 living_room_12)
        (neighbor staircase_15 corridor_7)
        (neighbor staircase_15 dining_room_9)

        ; Item locations
        (item_at apple_62 kitchen_11)       ; on countertop_21
        (item_at hamburger_58 kitchen_11)   ; on countertop_18
        (item_at table_1 dining_room_9)
        (item_at countertop_21 kitchen_11)
        (item_at countertop_18 kitchen_11)

        ; Item properties - apple_62 (smaller apple)
        (item_pickable apple_62)
        (item_accessible apple_62)

        ; Item properties - hamburger_58
        (item_pickable hamburger_58)
        (item_accessible hamburger_58)

        ; Item properties - table_1 (surface for placing items)
        (item_surface table_1)
        (item_accessible table_1)

        ; Restored objects — infeasibility is derived, not assumed
        (item_at apple_57 kitchen_11) (item_pickable apple_57) (item_accessible apple_57)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight apple_57) 0.0) (= (item_width apple_57) 0.328) (= (item_height apple_57) 0.966)
        (= (item_weight apple_62) 0.0) (= (item_width apple_62) 0.066) (= (item_height apple_62) 0.966)
        (= (item_weight countertop_18) 0.0) (= (item_width countertop_18) 0.020) (= (item_height countertop_18) 0.890)
        (= (item_weight countertop_21) 0.0) (= (item_width countertop_21) 0.020) (= (item_height countertop_21) 0.890)
        (= (item_weight hamburger_58) 0.0) (= (item_width hamburger_58) 0.091) (= (item_height hamburger_58) 0.903)
        (= (item_weight table_1) 0.0) (= (item_width table_1) 0.710) (= (item_height table_1) 0.380)

        ; fetch_gripper limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)
    )

    (:goal
        (and
            (item_on apple_62 table_1)
            (item_on hamburger_58 table_1)
        )
    )
)
