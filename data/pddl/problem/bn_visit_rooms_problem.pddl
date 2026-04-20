(define (problem benevolence_visit_rooms)
    (:domain visit_rooms)

    ; Visit living_room_12, kitchen_11, dining_room_9
    ; Exclude corridor_7 (largest, 25.1m²) and staircase_15 (smallest, 3.4m²)
    (:objects
        robot - agent
        dining_room_9 kitchen_11 living_room_12 - room
    )

    (:init
        (agent_at robot kitchen_11)
        (visited kitchen_11)

        (neighbor dining_room_9 kitchen_11) (neighbor dining_room_9 living_room_12)
        (neighbor kitchen_11 dining_room_9)
        (neighbor living_room_12 dining_room_9)
    )

    (:goal
        (and
            (visited living_room_12)
            (visited kitchen_11)
            (visited dining_room_9)
        )
    )
)
