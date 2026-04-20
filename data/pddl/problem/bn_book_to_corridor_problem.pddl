(define (problem benevolence_book_to_corridor)
    (:domain book_to_corridor)

    ; book_72 (z=0.5m, jr2 reachable) — book_71 at z=1.8m exceeds jr2 reach
    ; pen_56 from kitchen
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        book_72 pen_56 console_table_9 - item
    )

    (:init
        (agent_at robot dining_room_9)

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

        ; Book on low shelf in living room
        (item_at book_72 living_room_12)
        (item_pickable book_72) (item_accessible book_72)

        ; Pen in kitchen
        (item_at pen_56 kitchen_11)
        (item_pickable pen_56) (item_accessible pen_56)

        ; Console table in corridor
        (item_at console_table_9 corridor_7)
        (item_surface console_table_9) (item_accessible console_table_9)
    )

    (:goal
        (and
            (item_on book_72 console_table_9)
            (item_on pen_56 console_table_9)
        )
    )
)
