(define (problem merom_glass_delivery)
    (:domain glass_delivery)

    (:objects
        robot_1 - agent
        drone_1 - drone
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        fridge_57 - item
    )

    (:init
        (agent_at robot_1 living_room_10)
        (drone_at drone_1 living_room_10)

        ; Room neighbors
        (neighbor bathroom_2 living_room_10) (neighbor bathroom_2 bedroom_3) (neighbor bathroom_2 corridor_6)
        (neighbor living_room_10 bathroom_2) (neighbor living_room_10 corridor_6) (neighbor living_room_10 dining_room_7)
        (neighbor bedroom_3 bathroom_2) (neighbor bedroom_3 childs_room_5) (neighbor bedroom_3 corridor_6)
        (neighbor childs_room_5 bedroom_3) (neighbor childs_room_5 corridor_6) (neighbor childs_room_5 kitchen_8)
        (neighbor corridor_6 living_room_10) (neighbor corridor_6 bathroom_2) (neighbor corridor_6 bedroom_3)
        (neighbor corridor_6 childs_room_5) (neighbor corridor_6 dining_room_7) (neighbor corridor_6 kitchen_8)
        (neighbor dining_room_7 living_room_10) (neighbor dining_room_7 corridor_6) (neighbor dining_room_7 kitchen_8)
        (neighbor kitchen_8 childs_room_5) (neighbor kitchen_8 corridor_6) (neighbor kitchen_8 dining_room_7)

        ; Fridge is closed
        (item_at fridge_57 kitchen_8)
        (item_openable fridge_57) (item_accessible fridge_57) (item_closed fridge_57)
    )

    (:goal
        (item_checked fridge_57)
    )
)
