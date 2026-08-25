(define (problem benevolence_microwave_apple)
    (:domain microwave_apple)

    ; Only the small apple (apple_62) — large apple_57 is infeasible for gripper
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        apple_62 microwave_36 apple_57 - item
    )

    (:init
        (agent_at robot living_room_12)

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

        (item_at apple_62 kitchen_11)
        (item_at microwave_36 kitchen_11)

        (item_pickable apple_62) (item_accessible apple_62)

        (item_container microwave_36) (item_openable microwave_36) (item_closeable microwave_36)
        (item_turnable microwave_36) (item_accessible microwave_36)
        (item_closed microwave_36) (item_turned_off microwave_36)

        ; Restored objects — infeasibility is derived, not assumed
        (item_at apple_57 kitchen_11) (item_pickable apple_57) (item_accessible apple_57)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight apple_57) 0.0) (= (item_width apple_57) 0.328) (= (item_height apple_57) 0.966)
        (= (item_weight apple_62) 0.0) (= (item_width apple_62) 0.066) (= (item_height apple_62) 0.966)
        (= (item_weight microwave_36) 0.0) (= (item_width microwave_36) 0.350) (= (item_height microwave_36) 1.555)

        ; fetch_gripper limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)
    )

    (:goal
        (and
            (item_in apple_62 microwave_36)
            (item_turned_on microwave_36)
        )
    )
)
