(define (problem merom_party_preparation)
    (:domain party_preparation)

    ; Objects — only items requiring actions
    (:objects
        robot_1 robot_2 - agent
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        wine_bottle_94 cheese_99 table_20 shelf_58 shelf_61
        table_lamp_10 table_lamp_11 table_lamp_3
        window_77 window_82 - item
    )

    ; Initial state
    (:init
        ; Agent locations
        (agent_at robot_1 bedroom_3)
        (agent_at robot_2 living_room_10)

        ; Room neighbors (bidirectional)
        (neighbor bathroom_2 living_room_10)
        (neighbor bathroom_2 bedroom_3)
        (neighbor bathroom_2 corridor_6)
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
        (neighbor living_room_10 bathroom_2)
        (neighbor living_room_10 corridor_6)
        (neighbor living_room_10 dining_room_7)

        ; Wine bottle — on shelf in kitchen, pickable
        (item_at wine_bottle_94 kitchen_8)
        (item_pickable wine_bottle_94)
        (item_accessible wine_bottle_94)

        ; Cheese — on shelf_61 in kitchen, pickable
        (item_at cheese_99 kitchen_8)
        (item_pickable cheese_99)
        (item_accessible cheese_99)

        ; Shelves
        (item_at shelf_58 kitchen_8)
        (item_accessible shelf_58)

        (item_at shelf_61 kitchen_8)
        (item_accessible shelf_61)

        ; Dining table — surface for placing items
        (item_at table_20 dining_room_7)
        (item_surface table_20)
        (item_accessible table_20)

        ; Lamps that need turning on (currently off)
        (item_at table_lamp_10 bedroom_3)
        (item_lamp table_lamp_10)
        (item_accessible table_lamp_10)
        (item_state_off table_lamp_10)

        (item_at table_lamp_11 bedroom_3)
        (item_lamp table_lamp_11)
        (item_accessible table_lamp_11)
        (item_state_off table_lamp_11)

        (item_at table_lamp_3 childs_room_5)
        (item_lamp table_lamp_3)
        (item_accessible table_lamp_3)
        (item_state_off table_lamp_3)

        ; Windows that need closing (currently opened)
        (item_at window_77 dining_room_7)
        (item_window window_77)
        (item_closeable window_77)
        (item_accessible window_77)
        (item_opened window_77)

        (item_at window_82 living_room_10)
        (item_window window_82)
        (item_closeable window_82)
        (item_accessible window_82)
        (item_opened window_82)
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight cheese_99) 0.0) (= (item_width cheese_99) 0.018) (= (item_height cheese_99) 1.706)
        (= (item_weight shelf_58) 0.0) (= (item_width shelf_58) 0.550) (= (item_height shelf_58) 0.450)
        (= (item_weight shelf_61) 0.0) (= (item_width shelf_61) 0.111) (= (item_height shelf_61) 1.450)
        (= (item_weight table_20) 0.0) (= (item_width table_20) 0.800) (= (item_height table_20) 0.400)
        (= (item_weight table_lamp_10) 0.0) (= (item_width table_lamp_10) 0.230) (= (item_height table_lamp_10) 0.750)
        (= (item_weight table_lamp_11) 0.0) (= (item_width table_lamp_11) 0.230) (= (item_height table_lamp_11) 0.750)
        (= (item_weight table_lamp_3) 0.0) (= (item_width table_lamp_3) 0.210) (= (item_height table_lamp_3) 0.930)
        (= (item_weight window_77) 0.0) (= (item_width window_77) 0.111) (= (item_height window_77) 1.475)
        (= (item_weight window_82) 0.0) (= (item_width window_82) 0.060) (= (item_height window_82) 1.475)
        (= (item_weight wine_bottle_94) 0.0) (= (item_width wine_bottle_94) 0.060) (= (item_height wine_bottle_94) 0.959)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot_1) 6.0) (= (agent_gripper robot_1) 0.100) (= (agent_reach robot_1) 1.871)  ; fetch_gripper
        (= (agent_payload robot_2) 6.0) (= (agent_gripper robot_2) 0.100) (= (agent_reach robot_2) 1.871)  ; fetch_gripper
    )

    ; Goal
    (:goal
        (and
            (item_on wine_bottle_94 table_20)
            (item_on cheese_99 table_20)
            (item_state_on table_lamp_10)
            (item_state_on table_lamp_11)
            (item_state_on table_lamp_3)
            (item_closed window_77)
            (item_closed window_82)
        )
    )
)
