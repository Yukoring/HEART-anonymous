(define (problem benevolence_sunglass_in_briefcase)
    (:domain sunglass_in_briefcase)

    ; Only the light sunglass (sunglass_65, 0.05kg) — sunglass_60 is 8.0kg (over fetch payload 6.0kg)
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        sunglass_65 briefcase_61 sunglass_60 - item
    )

    (:init
        (agent_at robot dining_room_9)

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

        ; Both in living room
        (item_at sunglass_65 living_room_12)
        (item_at briefcase_61 living_room_12)

        (item_pickable sunglass_65) (item_accessible sunglass_65)
        (item_container briefcase_61) (item_accessible briefcase_61)

        ; Restored objects — infeasibility is derived, not assumed
        (item_at sunglass_60 living_room_12) (item_pickable sunglass_60) (item_accessible sunglass_60)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight briefcase_61) 0.0) (= (item_width briefcase_61) 0.346) (= (item_height briefcase_61) 0.606)
        (= (item_weight sunglass_60) 8.0) (= (item_width sunglass_60) 0.064) (= (item_height sunglass_60) 0.635)
        (= (item_weight sunglass_65) 0.05) (= (item_width sunglass_65) 0.064) (= (item_height sunglass_65) 0.635)

        ; fetch_gripper limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)
    )

    (:goal
        (and
            (item_in sunglass_65 briefcase_61)
        )
    )
)
