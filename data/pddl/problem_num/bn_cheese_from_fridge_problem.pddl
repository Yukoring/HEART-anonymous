(define (problem benevolence_cheese_from_fridge)
    (:domain cheese_from_fridge)

    ; Only small cheese (cheese_66) — cheese_67 too large for jr2 gripper
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        cheese_66 fridge_27 table_1 cheese_67 - item
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

        ; Cheese inside fridge
        (item_at fridge_27 kitchen_11)
        (item_in cheese_66 fridge_27)
        (item_pickable cheese_66) (item_accessible cheese_66)

        ; Fridge — closed
        (item_container fridge_27) (item_openable fridge_27) (item_closeable fridge_27)
        (item_accessible fridge_27) (item_closed fridge_27)

        ; Dining table
        (item_at table_1 dining_room_9)
        (item_surface table_1) (item_accessible table_1)
    
        ; Restored objects — infeasibility is derived, not assumed
        (item_at cheese_67 kitchen_11) (item_pickable cheese_67) (item_accessible cheese_67)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight cheese_66) 0.0) (= (item_width cheese_66) 0.040) (= (item_height cheese_66) 0.600)
        (= (item_weight cheese_67) 0.0) (= (item_width cheese_67) 0.090) (= (item_height cheese_67) 0.600)
        (= (item_weight fridge_27) 0.0) (= (item_width fridge_27) 0.900) (= (item_height fridge_27) 0.880)
        (= (item_weight table_1) 0.0) (= (item_width table_1) 0.710) (= (item_height table_1) 0.380)

        ; jr2_kinova_gripper limits (URDF and published payload)
        (= (agent_payload robot) 2.6) (= (agent_gripper robot) 0.088) (= (agent_reach robot) 1.432)
    )

    (:goal (item_on cheese_66 table_1))
)
