(define (problem beechwood_evening_living_room)
    (:domain evening_living_room)

    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        floor_lamp_11 floor_lamp_14 wall_mounted_tv_81 sofa_82 - item
    )

    (:init
        (agent_at robot bathroom_1)

        ; Room neighbors
        (neighbor bathroom_1 home_office_11) (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 staircase_16) (neighbor bathroom_1 utility_room_18)
        (neighbor bathroom_1 corridor_8)
        (neighbor corridor_8 bathroom_1) (neighbor corridor_8 home_office_11)
        (neighbor corridor_8 living_room_13) (neighbor corridor_8 staircase_16)
        (neighbor corridor_8 utility_room_18)
        (neighbor dining_room_10 kitchen_12) (neighbor dining_room_10 staircase_16)
        (neighbor home_office_11 bathroom_1) (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18) (neighbor home_office_11 corridor_8)
        (neighbor kitchen_12 dining_room_10) (neighbor kitchen_12 living_room_13)
        (neighbor kitchen_12 staircase_16)
        (neighbor living_room_13 home_office_11) (neighbor living_room_13 kitchen_12)
        (neighbor living_room_13 corridor_8)
        (neighbor lobby_14 bathroom_1) (neighbor lobby_14 staircase_16)
        (neighbor staircase_16 bathroom_1) (neighbor staircase_16 corridor_8)
        (neighbor staircase_16 dining_room_10) (neighbor staircase_16 kitchen_12)
        (neighbor staircase_16 lobby_14)
        (neighbor utility_room_18 bathroom_1) (neighbor utility_room_18 corridor_8)
        (neighbor utility_room_18 home_office_11)

        ; Items in living room
        (item_at floor_lamp_11 living_room_13)
        (item_at floor_lamp_14 living_room_13)
        (item_at wall_mounted_tv_81 living_room_13)
        (item_at sofa_82 living_room_13)

        ; Lamps — both turned on
        (item_lamp floor_lamp_11) (item_turnable floor_lamp_11)
        (item_accessible floor_lamp_11) (item_state_on floor_lamp_11)

        (item_lamp floor_lamp_14) (item_turnable floor_lamp_14)
        (item_accessible floor_lamp_14) (item_state_on floor_lamp_14)

        ; TV — turned off
        (item_tv wall_mounted_tv_81) (item_turnable wall_mounted_tv_81)
        (item_accessible wall_mounted_tv_81) (item_state_off wall_mounted_tv_81)

        ; Sofa — cleanable
        (item_cleanable sofa_82) (item_accessible sofa_82)
    )

    (:goal
        (and
            (item_state_off floor_lamp_11)
            (item_state_off floor_lamp_14)
            (item_state_on wall_mounted_tv_81)
            (item_clean sofa_82)
        )
    )
)
