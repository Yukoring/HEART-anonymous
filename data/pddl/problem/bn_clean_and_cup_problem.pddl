(define (problem benevolence_clean_and_cup)
    (:domain clean_and_cup)

    ; Only small cup (cup_69) — cup_68 too large for jr2 gripper
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        cup_69 chair_2 chair_3 chair_4 table_1 - item
    )

    (:init
        (agent_at robot corridor_7)

        (neighbor corridor_7 kitchen_11) (neighbor corridor_7 living_room_12)
        (neighbor corridor_7 staircase_15) (neighbor corridor_7 dining_room_9)
        (neighbor dining_room_9 kitchen_11) (neighbor dining_room_9 living_room_12)
        (neighbor dining_room_9 staircase_15) (neighbor dining_room_9 corridor_7)
        (neighbor kitchen_11 staircase_15) (neighbor kitchen_11 corridor_7)
        (neighbor kitchen_11 dining_room_9)
        (neighbor living_room_12 staircase_15) (neighbor living_room_12 corridor_7)
        (neighbor living_room_12 dining_room_9)
        (neighbor staircase_15 kitchen_11) (neighbor staircase_15 living_room_12)
        (neighbor staircase_15 corridor_7) (neighbor staircase_15 dining_room_9)

        ; Cup in kitchen
        (item_at cup_69 kitchen_11)
        (item_pickable cup_69) (item_accessible cup_69)

        ; Chairs in dining room — all cleanable, empty
        (item_at chair_2 dining_room_9)
        (item_cleanable chair_2) (item_accessible chair_2)
        (item_at chair_3 dining_room_9)
        (item_cleanable chair_3) (item_accessible chair_3)
        (item_at chair_4 dining_room_9)
        (item_cleanable chair_4) (item_accessible chair_4)

        ; Dining table — surface for placing cup
        (item_at table_1 dining_room_9)
        (item_surface table_1) (item_accessible table_1)
    )

    (:goal
        (and
            (item_clean chair_2)
            (item_clean chair_3)
            (item_clean chair_4)
            (item_on cup_69 table_1)
        )
    )
)
