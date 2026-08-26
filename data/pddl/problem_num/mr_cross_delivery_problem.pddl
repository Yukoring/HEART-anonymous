(define (problem merom_cross_delivery)
    (:domain cross_delivery)

    (:objects
        robot_1 - agent
        drone_1 - drone
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        notebook_101 atomizer_96 table_20 coffee_table_27 window_77 window_82 - item
    )

    (:init
        (agent_at robot_1 childs_room_5)
        (drone_at drone_1 childs_room_5)

        ; Room neighbors
        (neighbor bathroom_2 living_room_10) (neighbor bathroom_2 bedroom_3) (neighbor bathroom_2 corridor_6)
        (neighbor living_room_10 bathroom_2) (neighbor living_room_10 corridor_6) (neighbor living_room_10 dining_room_7)
        (neighbor bedroom_3 bathroom_2) (neighbor bedroom_3 childs_room_5) (neighbor bedroom_3 corridor_6)
        (neighbor childs_room_5 bedroom_3) (neighbor childs_room_5 corridor_6) (neighbor childs_room_5 kitchen_8)
        (neighbor corridor_6 living_room_10) (neighbor corridor_6 bathroom_2) (neighbor corridor_6 bedroom_3)
        (neighbor corridor_6 childs_room_5) (neighbor corridor_6 dining_room_7) (neighbor corridor_6 kitchen_8)
        (neighbor dining_room_7 living_room_10) (neighbor dining_room_7 corridor_6) (neighbor dining_room_7 kitchen_8)
        (neighbor kitchen_8 childs_room_5) (neighbor kitchen_8 corridor_6) (neighbor kitchen_8 dining_room_7)

        ; Notebook in living room
        (item_at notebook_101 living_room_10)
        (item_pickable notebook_101) (item_accessible notebook_101)

        ; Atomizer in bedroom
        (item_at atomizer_96 bedroom_3)
        (item_pickable atomizer_96) (item_accessible atomizer_96)

        ; Surfaces
        (item_at table_20 dining_room_7)
        (item_surface table_20) (item_accessible table_20)

        (item_at coffee_table_27 living_room_10)
        (item_surface coffee_table_27) (item_accessible coffee_table_27)

        ; Windows for drone check
        (item_at window_77 dining_room_7) (item_accessible window_77)
        (item_at window_82 living_room_10) (item_accessible window_82)
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight atomizer_96) 0.0) (= (item_width atomizer_96) 0.042) (= (item_height atomizer_96) 1.046)
        (= (item_weight coffee_table_27) 0.0) (= (item_width coffee_table_27) 0.380) (= (item_height coffee_table_27) 0.210)
        (= (item_weight notebook_101) 0.0) (= (item_width notebook_101) 0.050) (= (item_height notebook_101) 0.408)
        (= (item_weight table_20) 0.0) (= (item_width table_20) 0.800) (= (item_height table_20) 0.400)
        (= (item_weight window_77) 0.0) (= (item_width window_77) 0.111) (= (item_height window_77) 1.475)
        (= (item_weight window_82) 0.0) (= (item_width window_82) 0.060) (= (item_height window_82) 1.475)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot_1) 6.0) (= (agent_gripper robot_1) 0.100) (= (agent_reach robot_1) 1.871)  ; fetch_gripper
    )

    (:goal
        (and
            (item_on notebook_101 table_20)
            (item_on atomizer_96 coffee_table_27)
            (item_checked window_77)
            (item_checked window_82)
        )
    )
)
