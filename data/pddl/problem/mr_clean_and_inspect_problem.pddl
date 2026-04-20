(define (problem merom_clean_and_inspect)
    (:domain clean_and_inspect)

    ; Objects — only items requiring actions
    (:objects
        robot_1 - agent
        drone_1 - drone
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        bathtub_71 toilet_69 medicine_103 first_aid_kit_104 - item
    )

    ; Initial state
    (:init
        ; Agent and drone locations
        (agent_at robot_1 bedroom_3)
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

        ; Cleanable items in bathroom
        (item_at bathtub_71 bathroom_2)
        (item_cleanable bathtub_71)
        (item_accessible bathtub_71)


        (item_at toilet_69 bathroom_2)
        (item_cleanable toilet_69)
        (item_accessible toilet_69)


        ; High pickable items (above 2.0m) — for drone inspection
        (item_at medicine_103 kitchen_8)
        (item_pickable medicine_103)
        (item_accessible medicine_103)

        (item_at first_aid_kit_104 kitchen_8)
        (item_pickable first_aid_kit_104)
        (item_accessible first_aid_kit_104)
    )

    ; Goal — robot cleans bathroom, drone inspects high items
    (:goal
        (and
            (item_clean bathtub_71)
            (item_clean toilet_69)
            (item_inspected medicine_103)
            (item_inspected first_aid_kit_104)
        )
    )
)
