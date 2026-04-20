(define (problem beechwood_kitchen_safety)
    (:domain kitchen_safety)

    ; Objects
    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        burner_77 fridge_57 - item
    )

    ; Initial state
    (:init
        ; Agent location
        (agent_at robot lobby_14)

        ; Room neighbors
        (neighbor bathroom_1 home_office_11)
        (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 staircase_16)
        (neighbor bathroom_1 utility_room_18)
        (neighbor bathroom_1 corridor_8)
        (neighbor home_office_11 bathroom_1)
        (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18)
        (neighbor home_office_11 corridor_8)
        (neighbor corridor_8 bathroom_1)
        (neighbor corridor_8 home_office_11)
        (neighbor corridor_8 living_room_13)
        (neighbor corridor_8 staircase_16)
        (neighbor corridor_8 utility_room_18)
        (neighbor living_room_13 home_office_11)
        (neighbor living_room_13 kitchen_12)
        (neighbor living_room_13 corridor_8)
        (neighbor kitchen_12 dining_room_10)
        (neighbor kitchen_12 living_room_13)
        (neighbor kitchen_12 staircase_16)
        (neighbor dining_room_10 kitchen_12)
        (neighbor dining_room_10 staircase_16)
        (neighbor lobby_14 bathroom_1)
        (neighbor lobby_14 staircase_16)
        (neighbor staircase_16 bathroom_1)
        (neighbor staircase_16 corridor_8)
        (neighbor staircase_16 dining_room_10)
        (neighbor staircase_16 kitchen_12)
        (neighbor staircase_16 lobby_14)
        (neighbor utility_room_18 bathroom_1)
        (neighbor utility_room_18 corridor_8)
        (neighbor utility_room_18 home_office_11)

        ; Item locations - all in kitchen
        (item_at burner_77 kitchen_12)
        (item_at fridge_57 kitchen_12)

        ; Item properties - burner
        (item_turnable burner_77)
        (item_accessible burner_77)
        (item_turned_on burner_77)  ; oven is initially on (needs to be turned off)

        ; Item properties - fridge
        (item_turnable fridge_57)
        (item_closeable fridge_57)
        (item_openable fridge_57)
        (item_accessible fridge_57)
        (item_open fridge_57)  ; fridge is initially open
        (item_turned_off fridge_57)  ; fridge is initially off
    )

    ; Goal
    (:goal
        (and
            (item_turned_off burner_77)
            (item_closed fridge_57)
            (item_turned_on fridge_57)
        )
    )
)
