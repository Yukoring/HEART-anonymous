(define (problem merom_evening_preparation)
    (:domain evening_preparation)

    ; Objects
    (:objects
        robot_1 robot_2 - agent
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        dishwasher_52 glass_93 table_20 window_77 window_82 stove_59 floor_lamp_31 floor_lamp_33 - item
    )

    ; Initial state
    (:init
        ; Agent locations - both start in bedroom
        (agent_at robot_1 bedroom_3)
        (agent_at robot_2 bedroom_3)

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
        (item_at dishwasher_52 kitchen_8)
        (item_at table_20 dining_room_7)
        (item_at window_77 dining_room_7)
        (item_at window_82 living_room_10)
        (item_at stove_59 kitchen_8)
        (item_at floor_lamp_31 living_room_10)
        (item_at floor_lamp_33 living_room_10)

        ; Glass is inside dishwasher
        (item_in glass_93 dishwasher_52)

        ; Item properties
        (item_dishwasher dishwasher_52)
        (item_container dishwasher_52)
        (item_openable dishwasher_52)
        (item_closeable dishwasher_52)
        (item_accessible dishwasher_52)
        (item_closed dishwasher_52)

        (item_pickable glass_93)

        (item_surface table_20)
        (item_accessible table_20)

        (item_window window_77)
        (item_openable window_77)
        (item_closeable window_77)
        (item_accessible window_77)
        (item_opened window_77)

        (item_window window_82)
        (item_openable window_82)
        (item_closeable window_82)
        (item_accessible window_82)
        (item_opened window_82)

        (item_stove stove_59)
        (item_turnable stove_59)
        (item_accessible stove_59)
        (item_state_on stove_59)

        (item_lamp floor_lamp_31)
        (item_turnable floor_lamp_31)
        (item_accessible floor_lamp_31)
        (item_state_on floor_lamp_31)

        (item_lamp floor_lamp_33)
        (item_turnable floor_lamp_33)
        (item_accessible floor_lamp_33)
        (item_state_on floor_lamp_33)
    )

    ; Goal
    (:goal
        (and
            (item_on glass_93 table_20)
            (item_closed window_77)
            (item_closed window_82)
            (item_state_off stove_59)
            (item_state_off floor_lamp_31)
            (item_state_off floor_lamp_33)
        )
    )
)