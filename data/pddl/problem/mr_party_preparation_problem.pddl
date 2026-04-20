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
