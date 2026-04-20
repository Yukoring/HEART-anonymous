(define (problem merom_zone_cleanup)
    (:domain zone_cleanup)

    (:objects
        robot_1 robot_2 - agent
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        floor_lamp_31 floor_lamp_33 stove_59 window_77 window_82 - item
    )

    (:init
        ; Robot identity
        (is_robot_1 robot_1)
        (is_robot_2 robot_2)

        ; Robot start positions — need navigation
        (agent_at robot_1 bedroom_3)
        (agent_at robot_2 childs_room_5)

        ; Room neighbors
        (neighbor bathroom_2 living_room_10) (neighbor bathroom_2 bedroom_3) (neighbor bathroom_2 corridor_6)
        (neighbor living_room_10 bathroom_2) (neighbor living_room_10 corridor_6) (neighbor living_room_10 dining_room_7)
        (neighbor bedroom_3 bathroom_2) (neighbor bedroom_3 childs_room_5) (neighbor bedroom_3 corridor_6)
        (neighbor childs_room_5 bedroom_3) (neighbor childs_room_5 corridor_6) (neighbor childs_room_5 kitchen_8)
        (neighbor corridor_6 living_room_10) (neighbor corridor_6 bathroom_2) (neighbor corridor_6 bedroom_3)
        (neighbor corridor_6 childs_room_5) (neighbor corridor_6 dining_room_7) (neighbor corridor_6 kitchen_8)
        (neighbor dining_room_7 living_room_10) (neighbor dining_room_7 corridor_6) (neighbor dining_room_7 kitchen_8)
        (neighbor kitchen_8 childs_room_5) (neighbor kitchen_8 corridor_6) (neighbor kitchen_8 dining_room_7)

        ; Zone A: robot_1 can access living, bathroom, bedroom, corridor
        (room_allowed_r1 living_room_10)
        (room_allowed_r1 bathroom_2)
        (room_allowed_r1 bedroom_3)
        (room_allowed_r1 corridor_6)

        ; Zone B: robot_2 can access kitchen, dining, childs_room, corridor
        (room_allowed_r2 kitchen_8)
        (room_allowed_r2 dining_room_7)
        (room_allowed_r2 childs_room_5)
        (room_allowed_r2 corridor_6)

        ; Floor lamps (on) — Zone A
        (item_at floor_lamp_31 living_room_10) (item_accessible floor_lamp_31)
        (item_turnable floor_lamp_31) (item_state_on floor_lamp_31)

        (item_at floor_lamp_33 living_room_10) (item_accessible floor_lamp_33)
        (item_turnable floor_lamp_33) (item_state_on floor_lamp_33)

        ; Window opened — Zone A
        (item_at window_82 living_room_10) (item_accessible window_82)
        (item_closeable window_82) (item_open window_82)

        ; Window opened — Zone B
        (item_at window_77 dining_room_7) (item_accessible window_77)
        (item_closeable window_77) (item_open window_77)

        ; Stove on — Zone B
        (item_at stove_59 kitchen_8) (item_accessible stove_59)
        (item_turnable stove_59) (item_state_on stove_59)
    )

    (:goal
        (and
            ; Robot_1 tasks (Zone A)
            (item_state_off floor_lamp_31)
            (item_state_off floor_lamp_33)
            (item_closed window_82)
            ; Robot_2 tasks (Zone B)
            (item_closed window_77)
            (item_state_off stove_59)
        )
    )
)
