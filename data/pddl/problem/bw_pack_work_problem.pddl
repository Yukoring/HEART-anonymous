(define (problem beechwood_pack_work)
    (:domain pack_work)

    ; Objects
    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        notebook_119 pen_121 briefcase_120 - item
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

        ; Item locations
        (item_at notebook_119 lobby_14)  ; on table_28
        (item_at pen_121 home_office_11)  ; on table_41
        (item_at briefcase_120 living_room_13)

        ; Item properties - notebook
        (item_pickable notebook_119)
        (item_accessible notebook_119)

        ; Item properties - pen
        (item_pickable pen_121)
        (item_accessible pen_121)

        ; Item properties - briefcase
        (item_accessible briefcase_120)
        (item_container briefcase_120)  ; briefcase can contain items
    )

    ; Goal
    (:goal
        (and
            (item_in notebook_119 briefcase_120)
            (item_in pen_121 briefcase_120)
        )
    )
)
