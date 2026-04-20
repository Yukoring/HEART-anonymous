(define (problem benevolence_close_largest_furniture)
    (:domain close_largest_furniture)

    ; chest_11 is the largest opened furniture (0.95m max dim)
    ; chest_12 is smaller (0.77m) — not required
    ; sofa_10 is cleanable
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        chest_11 sofa_10 - item
    )

    (:init
        (agent_at robot kitchen_11)

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

        ; Chest_11 in living room — opened, largest furniture
        (item_at chest_11 living_room_12)
        (item_closeable chest_11) (item_accessible chest_11) (item_open chest_11)

        ; Sofa in living room — cleanable
        (item_at sofa_10 living_room_12)
        (item_cleanable sofa_10) (item_accessible sofa_10)
    )

    (:goal
        (and
            (item_closed chest_11)
            (item_clean sofa_10)
        )
    )
)
