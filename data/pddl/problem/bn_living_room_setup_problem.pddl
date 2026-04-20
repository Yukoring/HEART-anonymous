(define (problem benevolence_living_room_setup)
    (:domain living_room_setup)

    ; sunglass_65 (0.05kg, light) — sunglass_60 is 3.5kg (too heavy for jr2 payload 2.6kg)
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        sunglass_65 floor_lamp_8 wall_mounted_tv_49 sofa_10 - item
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

        ; All items in living room
        (item_at sunglass_65 living_room_12)
        (item_pickable sunglass_65) (item_accessible sunglass_65)

        (item_at floor_lamp_8 living_room_12)
        (item_turnable floor_lamp_8) (item_accessible floor_lamp_8)
        (item_state_off floor_lamp_8)

        (item_at wall_mounted_tv_49 living_room_12)
        (item_turnable wall_mounted_tv_49) (item_accessible wall_mounted_tv_49)
        (item_state_off wall_mounted_tv_49)

        (item_at sofa_10 living_room_12)
        (item_surface sofa_10) (item_accessible sofa_10)
    )

    (:goal
        (and
            (item_state_on floor_lamp_8)
            (item_state_on wall_mounted_tv_49)
            (item_on sunglass_65 sofa_10)
        )
    )
)
