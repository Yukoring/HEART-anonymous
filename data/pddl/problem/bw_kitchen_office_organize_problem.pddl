(define (problem beechwood_kitchen_office_organize)
    (:domain kitchen_office_organize)

    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        pen_121 chest_8 bottom_cabinet_35 - item
    )

    (:init
        (agent_at robot dining_room_10)

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

        ; Items
        (item_at pen_121 home_office_11)
        (item_at chest_8 kitchen_12)
        (item_at bottom_cabinet_35 home_office_11)

        ; Pen — pickable
        (item_pickable pen_121) (item_accessible pen_121)

        ; Chest in kitchen — opened (needs to be closed)
        (item_container chest_8) (item_openable chest_8)
        (item_closeable chest_8) (item_accessible chest_8)
        (item_open chest_8)

        ; Cabinet in home office — closed (needs to be opened)
        (item_container bottom_cabinet_35) (item_openable bottom_cabinet_35)
        (item_closeable bottom_cabinet_35) (item_accessible bottom_cabinet_35)
        (item_closed bottom_cabinet_35)
    )

    (:goal
        (and
            (item_closed chest_8)
            (item_in pen_121 bottom_cabinet_35)
        )
    )
)
