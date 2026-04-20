(define (problem benevolence_bowl_to_oven)
    (:domain bowl_to_oven)

    ; Only the small bowl (bowl_63) — large bowl_55 is infeasible for gripper
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        bowl_63 oven_24 - item
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

        ; Bowl in dining room
        (item_at bowl_63 dining_room_9)
        (item_pickable bowl_63) (item_accessible bowl_63)

        ; Oven in kitchen — closed, off
        (item_at oven_24 kitchen_11)
        (item_container oven_24) (item_openable oven_24) (item_closeable oven_24)
        (item_turnable oven_24) (item_accessible oven_24)
        (item_closed oven_24) (item_turned_off oven_24)
    )

    (:goal
        (and
            (item_in bowl_63 oven_24)
            (item_turned_on oven_24)
        )
    )
)
