(define (problem merom_home_security)
    (:domain home_security)

    ; Objects
    (:objects
        robot_1 - agent
        drone_1 - drone
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        window_77 window_82 table_lamp_17 floor_lamp_31 floor_lamp_33 - item
    )

    ; Initial state
    (:init
        ; Agent and drone locations
        (agent_at robot_1 living_room_10)
        (drone_at drone_1 living_room_10)

        ; Room neighbors (bidirectional)
        (neighbor bathroom_2 living_room_10)
        (neighbor bathroom_2 bedroom_3)
        (neighbor bathroom_2 corridor_6)
        (neighbor living_room_10 bathroom_2)
        (neighbor living_room_10 corridor_6)
        (neighbor living_room_10 dining_room_7)
        (neighbor bedroom_3 bathroom_2)
        (neighbor bedroom_3 childs_room_5)
        (neighbor bedroom_3 corridor_6)
        (neighbor childs_room_5 bedroom_3)
        (neighbor childs_room_5 corridor_6)
        (neighbor childs_room_5 kitchen_8)
        (neighbor corridor_6 living_room_10)
        (neighbor corridor_6 bathroom_2)
        (neighbor corridor_6 bedroom_3)
        (neighbor corridor_6 childs_room_5)
        (neighbor corridor_6 dining_room_7)
        (neighbor corridor_6 kitchen_8)
        (neighbor dining_room_7 living_room_10)
        (neighbor dining_room_7 corridor_6)
        (neighbor dining_room_7 kitchen_8)
        (neighbor kitchen_8 childs_room_5)
        (neighbor kitchen_8 corridor_6)
        (neighbor kitchen_8 dining_room_7)

        ; Item locations
        (item_at window_77 dining_room_7)
        (item_at window_82 living_room_10)
        (item_at table_lamp_17 bedroom_3)
        (item_at floor_lamp_31 living_room_10)
        (item_at floor_lamp_33 living_room_10)

        ; Item properties
        (item_window window_77)
        (item_accessible window_77)
        (item_window window_82)
        (item_accessible window_82)

        (item_lamp table_lamp_17)
        (item_accessible table_lamp_17)
        (item_state_on table_lamp_17)

        (item_lamp floor_lamp_31)
        (item_accessible floor_lamp_31)
        (item_state_on floor_lamp_31)

        (item_lamp floor_lamp_33)
        (item_accessible floor_lamp_33)
        (item_state_on floor_lamp_33)
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight floor_lamp_31) 0.0) (= (item_width floor_lamp_31) 0.370) (= (item_height floor_lamp_31) 0.755)
        (= (item_weight floor_lamp_33) 0.0) (= (item_width floor_lamp_33) 0.300) (= (item_height floor_lamp_33) 0.705)
        (= (item_weight table_lamp_17) 0.0) (= (item_width table_lamp_17) 0.270) (= (item_height table_lamp_17) 1.270)
        (= (item_weight window_77) 0.0) (= (item_width window_77) 0.111) (= (item_height window_77) 1.475)
        (= (item_weight window_82) 0.0) (= (item_width window_82) 0.060) (= (item_height window_82) 1.475)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot_1) 6.0) (= (agent_gripper robot_1) 0.100) (= (agent_reach robot_1) 1.871)  ; fetch_gripper
    )

    ; Goal - check all opened windows and turn off all lamps that are on
    (:goal
        (and
            (item_checked window_77)
            (item_checked window_82)
            (item_state_off table_lamp_17)
            (item_state_off floor_lamp_31)
            (item_state_off floor_lamp_33)
        )
    )
)
