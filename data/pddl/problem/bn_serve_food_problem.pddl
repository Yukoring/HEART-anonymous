(define (problem benevolence_serve_food)
    (:domain serve_food)

    ; Objects
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        apple_62 hamburger_58 table_1 countertop_21 countertop_18 - item
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
        (item_at apple_62 kitchen_11)       ; on countertop_21
        (item_at hamburger_58 kitchen_11)   ; on countertop_18
        (item_at table_1 dining_room_9)
        (item_at countertop_21 kitchen_11)
        (item_at countertop_18 kitchen_11)

        ; Item properties - apple_62 (smaller apple)
        (item_pickable apple_62)
        (item_accessible apple_62)

        ; Item properties - hamburger_58
        (item_pickable hamburger_58)
        (item_accessible hamburger_58)

        ; Item properties - table_1 (surface for placing items)
        (item_surface table_1)
        (item_accessible table_1)
    )

    (:goal
        (and
            (item_on apple_62 table_1)
            (item_on hamburger_58 table_1)
        )
    )
)
