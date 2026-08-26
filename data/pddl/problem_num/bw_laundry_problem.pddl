(define (problem beechwood_laundry)
    (:domain laundry_heart)

    ; Objects
    (:objects
        robot - agent
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        jeans_112 washer_47 - item
    )

    ; Initial state
    (:init
        ; Agent location
        (agent_at robot bathroom_1)

        ; Room neighbors
        (neighbor bathroom_1 home_office_11)
        (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 staircase_16)
        (neighbor bathroom_1 utility_room_18)
        (neighbor bathroom_1 corridor_8)
        (neighbor home_office_11 bathroom_1)
        (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18)
        (neighbor home_office_11 corridor_8)
        (neighbor corridor_8 bathroom_1)
        (neighbor corridor_8 home_office_11)
        (neighbor corridor_8 living_room_13)
        (neighbor corridor_8 staircase_16)
        (neighbor corridor_8 utility_room_18)
        (neighbor living_room_13 home_office_11)
        (neighbor living_room_13 kitchen_12)
        (neighbor living_room_13 corridor_8)
        (neighbor kitchen_12 dining_room_10)
        (neighbor kitchen_12 living_room_13)
        (neighbor kitchen_12 staircase_16)
        (neighbor dining_room_10 kitchen_12)
        (neighbor dining_room_10 staircase_16)
        (neighbor lobby_14 bathroom_1)
        (neighbor lobby_14 staircase_16)
        (neighbor staircase_16 bathroom_1)
        (neighbor staircase_16 corridor_8)
        (neighbor staircase_16 dining_room_10)
        (neighbor staircase_16 kitchen_12)
        (neighbor staircase_16 lobby_14)
        (neighbor utility_room_18 bathroom_1)
        (neighbor utility_room_18 corridor_8)
        (neighbor utility_room_18 home_office_11)

        ; Item locations
        (item_at jeans_112 lobby_14)
        (item_at washer_47 utility_room_18)

        ; Item properties
        (item_pickable jeans_112)
        (item_accessible jeans_112)
        (item_dirty jeans_112)

        (item_container washer_47)
        (item_openable washer_47)
        (item_closeable washer_47)
        (item_turnable washer_47)
        (item_accessible washer_47)
        (item_closed washer_47)  ; washer is initially closed
        (item_turned_off washer_47)  ; washer is initially off
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight jeans_112) 0.0) (= (item_width jeans_112) 0.091) (= (item_height jeans_112) 0.219)
        (= (item_weight washer_47) 0.0) (= (item_width washer_47) 0.660) (= (item_height washer_47) 0.650)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)  ; fetch_gripper
    )

    ; Goal
    (:goal
        (and
            (item_clean jeans_112)
        )
    )
)
