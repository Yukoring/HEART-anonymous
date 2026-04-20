(define (problem beechwood_room_survey)
    (:domain room_survey)

    ; Objects
    (:objects
        drone_1 - drone
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        floor_lamp_11 floor_lamp_14 floor_lamp_23 floor_lamp_24 floor_lamp_29 - item
    )

    ; Initial state
    (:init
        ; Drone starts in corridor
        (drone_at drone_1 corridor_8)

        ; Room neighbors (bidirectional)
        (neighbor bathroom_1 home_office_11)
        (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 staircase_16)
        (neighbor bathroom_1 utility_room_18)
        (neighbor bathroom_1 corridor_8)
        (neighbor corridor_8 bathroom_1)
        (neighbor corridor_8 home_office_11)
        (neighbor corridor_8 living_room_13)
        (neighbor corridor_8 staircase_16)
        (neighbor corridor_8 utility_room_18)
        (neighbor dining_room_10 kitchen_12)
        (neighbor dining_room_10 staircase_16)
        (neighbor home_office_11 bathroom_1)
        (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18)
        (neighbor home_office_11 corridor_8)
        (neighbor kitchen_12 dining_room_10)
        (neighbor kitchen_12 living_room_13)
        (neighbor kitchen_12 staircase_16)
        (neighbor living_room_13 home_office_11)
        (neighbor living_room_13 kitchen_12)
        (neighbor living_room_13 corridor_8)
        (neighbor lobby_14 bathroom_1)
        (neighbor lobby_14 staircase_16)
        (neighbor staircase_16 bathroom_1)
        (neighbor staircase_16 dining_room_10)
        (neighbor staircase_16 kitchen_12)
        (neighbor staircase_16 lobby_14)
        (neighbor staircase_16 corridor_8)
        (neighbor utility_room_18 bathroom_1)
        (neighbor utility_room_18 home_office_11)
        (neighbor utility_room_18 corridor_8)

        ; Lamps in the house — 5 lamps across 3 rooms
        (item_at floor_lamp_11 living_room_13)
        (item_lamp floor_lamp_11)
        (item_at floor_lamp_14 living_room_13)
        (item_lamp floor_lamp_14)
        (item_at floor_lamp_23 dining_room_10)
        (item_lamp floor_lamp_23)
        (item_at floor_lamp_24 dining_room_10)
        (item_lamp floor_lamp_24)
        (item_at floor_lamp_29 lobby_14)
        (item_lamp floor_lamp_29)
    )

    ; Goal: all lamps checked
    (:goal
        (and
            (item_checked floor_lamp_11)
            (item_checked floor_lamp_14)
            (item_checked floor_lamp_23)
            (item_checked floor_lamp_24)
            (item_checked floor_lamp_29)
        )
    )
)
