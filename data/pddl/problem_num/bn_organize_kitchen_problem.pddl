(define (problem benevolence_organize_kitchen)
    (:domain organize_kitchen)

    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        apple_62 hamburger_58 fridge_27 apple_57 - item
    )

    (:init
        (agent_at robot living_room_12)

        ; Room neighbors
        (neighbor corridor_7 kitchen_11) (neighbor corridor_7 living_room_12)
        (neighbor corridor_7 staircase_15) (neighbor corridor_7 dining_room_9)
        (neighbor dining_room_9 kitchen_11) (neighbor dining_room_9 living_room_12)
        (neighbor dining_room_9 staircase_15) (neighbor dining_room_9 corridor_7)
        (neighbor kitchen_11 staircase_15) (neighbor kitchen_11 corridor_7)
        (neighbor kitchen_11 dining_room_9)
        (neighbor living_room_12 staircase_15) (neighbor living_room_12 corridor_7)
        (neighbor living_room_12 dining_room_9)
        (neighbor staircase_15 kitchen_11) (neighbor staircase_15 living_room_12)
        (neighbor staircase_15 corridor_7) (neighbor staircase_15 dining_room_9)

        ; Items
        (item_at apple_62 kitchen_11)
        (item_pickable apple_62) (item_accessible apple_62)

        (item_at hamburger_58 kitchen_11)
        (item_pickable hamburger_58) (item_accessible hamburger_58)

        (item_at fridge_27 kitchen_11)
        (item_container fridge_27) (item_openable fridge_27)
        (item_closeable fridge_27) (item_accessible fridge_27)
        (item_closed fridge_27)
    
        ; Restored objects — infeasibility is derived, not assumed
        (item_at apple_57 kitchen_11) (item_pickable apple_57) (item_accessible apple_57)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight apple_57) 0.0) (= (item_width apple_57) 0.328) (= (item_height apple_57) 0.966)
        (= (item_weight apple_62) 0.0) (= (item_width apple_62) 0.066) (= (item_height apple_62) 0.966)
        (= (item_weight fridge_27) 0.0) (= (item_width fridge_27) 0.900) (= (item_height fridge_27) 0.880)
        (= (item_weight hamburger_58) 0.0) (= (item_width hamburger_58) 0.091) (= (item_height hamburger_58) 0.903)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)  ; fetch_gripper
    )

    (:goal
        (and
            (item_in apple_62 fridge_27)
            (item_in hamburger_58 fridge_27)
            (apple_placed)
            (item_closed fridge_27)
        )
    )
)
