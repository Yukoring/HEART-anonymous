(define (problem beechwood_cross_house_delivery)
    (:domain cross_house_delivery)

    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        notebook_119 pen_121 salad_116 bottom_cabinet_39 chest_8 sink_43 - item
    )

    (:init
        (agent_at robot lobby_14)

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

        ; Item locations
        (item_at notebook_119 lobby_14)
        (item_at pen_121 home_office_11)
        (item_at salad_116 kitchen_12)
        (item_at bottom_cabinet_39 home_office_11)
        (item_at chest_8 kitchen_12)
        (item_at sink_43 utility_room_18)

        ; Pickable items
        (item_pickable notebook_119) (item_accessible notebook_119)
        (item_pickable pen_121) (item_accessible pen_121)
        (item_pickable salad_116) (item_accessible salad_116)

        ; Containers (all already open — no open/close needed)
        (item_container bottom_cabinet_39) (item_accessible bottom_cabinet_39)
        (item_container chest_8) (item_accessible chest_8)
        (item_container sink_43) (item_accessible sink_43)
    )

    (:goal
        (and
            (item_in notebook_119 bottom_cabinet_39)
            (item_in pen_121 chest_8)
            (item_in salad_116 sink_43)
        )
    )
)
