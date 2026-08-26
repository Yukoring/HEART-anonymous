(define (problem benevolence_find_items)
    (:domain find_items)

    ; Objects
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        sunglass_65 countertop_18 window_50 sunglass_60 - item
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
        (item_at sunglass_65 living_room_12)
        (item_at countertop_18 kitchen_11)
        (item_at window_50 dining_room_9)

        ; Item properties - sunglass_65
        (item_pickable sunglass_65)
        (item_accessible sunglass_65)

        ; Item properties - countertop_18 (surface)
        (item_surface countertop_18)
        (item_accessible countertop_18)

        ; Item properties - window_50
        (item_closeable window_50)
        (item_accessible window_50)
        (item_open window_50)  ; window starts open

    
        ; Restored objects — infeasibility is derived, not assumed
        (item_at sunglass_60 living_room_12) (item_pickable sunglass_60) (item_accessible sunglass_60)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight countertop_18) 0.0) (= (item_width countertop_18) 0.020) (= (item_height countertop_18) 0.890)
        (= (item_weight sunglass_60) 8.0) (= (item_width sunglass_60) 0.064) (= (item_height sunglass_60) 0.635)
        (= (item_weight sunglass_65) 0.05) (= (item_width sunglass_65) 0.064) (= (item_height sunglass_65) 0.635)
        (= (item_weight window_50) 0.0) (= (item_width window_50) 0.219) (= (item_height window_50) 1.250)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)  ; fetch_gripper
    )

    ; Goal - sunglass on countertop and window closed
    (:goal
        (and
            (item_on sunglass_65 countertop_18)
            (item_closed window_50)
        )
    )
)
