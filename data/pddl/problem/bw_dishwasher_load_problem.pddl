(define (problem beechwood_dishwasher_load)
    (:domain dishwasher_load)

    ; Objects — only items relevant to the task
    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        bowl_117 dishwasher_72 - item
    )

    ; Initial state
    (:init
        ; Agent starts in dining room
        (agent_at robot dining_room_10)

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
        (item_at bowl_117 dining_room_10)
        (item_at dishwasher_72 kitchen_12)

        ; Bowl — pickable
        (item_pickable bowl_117)
        (item_accessible bowl_117)

        ; Dishwasher — closed, off (needs open + place + turn_on)
        (item_container dishwasher_72)
        (item_openable dishwasher_72)
        (item_closeable dishwasher_72)
        (item_turnable dishwasher_72)
        (item_accessible dishwasher_72)
        (item_closed dishwasher_72)
        (item_turned_off dishwasher_72)
    )

    ; Goal: bowl in dishwasher + dishwasher running
    (:goal
        (and
            (item_in bowl_117 dishwasher_72)
            (item_turned_on dishwasher_72)
        )
    )
)
