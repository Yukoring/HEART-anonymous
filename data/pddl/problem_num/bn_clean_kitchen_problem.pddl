(define (problem benevolence_clean_kitchen)
    (:domain clean_kitchen)

    ; Objects
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        bowl_63 dishwasher_20 table_1 countertop_18 countertop_21 countertop_23 countertop_26 countertop_14 bowl_55 - item
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
        (item_at bowl_63 dining_room_9)
        (item_at dishwasher_20 kitchen_11)
        (item_at table_1 dining_room_9)
        (item_at countertop_18 kitchen_11)
        (item_at countertop_21 kitchen_11)
        (item_at countertop_23 kitchen_11)
        (item_at countertop_26 kitchen_11)
        (item_at countertop_14 dining_room_9)

        ; Bowl — pickable
        (item_pickable bowl_63)
        (item_accessible bowl_63)

        ; Dishwasher — closed container
        (item_container dishwasher_20)
        (item_openable dishwasher_20)
        (item_closeable dishwasher_20)
        (item_accessible dishwasher_20)
        (item_closed dishwasher_20)

        ; Surfaces — tables and countertops
        (item_surface table_1) (item_accessible table_1)
        (item_surface countertop_18) (item_accessible countertop_18)
        (item_surface countertop_21) (item_accessible countertop_21)
        (item_surface countertop_23) (item_accessible countertop_23)
        (item_surface countertop_26) (item_accessible countertop_26)
        (item_surface countertop_14) (item_accessible countertop_14)
    
        ; Restored objects — infeasibility is derived, not assumed
        (item_at bowl_55 dining_room_9) (item_pickable bowl_55) (item_accessible bowl_55)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight bowl_55) 0.0) (= (item_width bowl_55) 0.170) (= (item_height bowl_55) 0.842)
        (= (item_weight bowl_63) 0.0) (= (item_width bowl_63) 0.050) (= (item_height bowl_63) 0.842)
        (= (item_weight countertop_14) 0.0) (= (item_width countertop_14) 0.100) (= (item_height countertop_14) 1.050)
        (= (item_weight countertop_18) 0.0) (= (item_width countertop_18) 0.020) (= (item_height countertop_18) 0.890)
        (= (item_weight countertop_21) 0.0) (= (item_width countertop_21) 0.020) (= (item_height countertop_21) 0.890)
        (= (item_weight countertop_23) 0.0) (= (item_width countertop_23) 0.020) (= (item_height countertop_23) 0.890)
        (= (item_weight countertop_26) 0.0) (= (item_width countertop_26) 0.020) (= (item_height countertop_26) 0.890)
        (= (item_weight dishwasher_20) 0.0) (= (item_width dishwasher_20) 0.533) (= (item_height dishwasher_20) 0.440)
        (= (item_weight table_1) 0.0) (= (item_width table_1) 0.710) (= (item_height table_1) 0.380)

        ; fetch_gripper limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)
    )

    ; Goal - bowl in dishwasher
    (:goal
        (and
            (item_in bowl_63 dishwasher_20)
        )
    )
)
