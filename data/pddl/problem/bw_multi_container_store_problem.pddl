(define (problem beechwood_multi_container_store)
    (:domain multi_container_store)

    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        milk_118 cereal_115 fridge_57 chest_8 - item
    )

    (:init
        (agent_at robot bathroom_1)

        ; Room neighbors
        (neighbor bathroom_1 home_office_11) (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 staircase_16) (neighbor bathroom_1 utility_room_18)
        (neighbor bathroom_1 corridor_8)
        (neighbor corridor_8 bathroom_1) (neighbor corridor_8 home_office_11)
        (neighbor corridor_8 living_room_13) (neighbor corridor_8 staircase_16)
        (neighbor corridor_8 utility_room_18)
        (neighbor dining_room_10 kitchen_12) (neighbor dining_room_10 staircase_16)
        (neighbor home_office_11 bathroom_1) (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18) (neighbor home_office_11 corridor_8)
        (neighbor kitchen_12 dining_room_10) (neighbor kitchen_12 living_room_13)
        (neighbor kitchen_12 staircase_16)
        (neighbor living_room_13 home_office_11) (neighbor living_room_13 kitchen_12)
        (neighbor living_room_13 corridor_8)
        (neighbor lobby_14 bathroom_1) (neighbor lobby_14 staircase_16)
        (neighbor staircase_16 bathroom_1) (neighbor staircase_16 corridor_8)
        (neighbor staircase_16 dining_room_10) (neighbor staircase_16 kitchen_12)
        (neighbor staircase_16 lobby_14)
        (neighbor utility_room_18 bathroom_1) (neighbor utility_room_18 corridor_8)
        (neighbor utility_room_18 home_office_11)

        ; Items in kitchen
        (item_at milk_118 kitchen_12)
        (item_at cereal_115 kitchen_12)
        (item_at fridge_57 kitchen_12)
        (item_at chest_8 kitchen_12)

        (item_pickable milk_118) (item_accessible milk_118)
        (item_pickable cereal_115) (item_accessible cereal_115)

        ; Fridge — already opened
        (item_container fridge_57) (item_openable fridge_57) (item_closeable fridge_57)
        (item_accessible fridge_57) (item_open fridge_57)

        ; Chest — already opened
        (item_container chest_8) (item_openable chest_8)
        (item_closeable chest_8) (item_accessible chest_8)
        (item_open chest_8)
    )

    (:goal
        (and
            (item_in milk_118 fridge_57)
            (item_in cereal_115 chest_8)
            (item_closed fridge_57)
            (item_closed chest_8)
        )
    )
)
