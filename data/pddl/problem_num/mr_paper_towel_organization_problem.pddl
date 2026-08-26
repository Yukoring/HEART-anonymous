(define (problem merom_paper_towel_organization)
    (:domain paper_towel_organization)

    ; Objects
    (:objects
        robot_1 - agent
        drone_1 - drone
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        paper_towel_105 top_cabinet_54 - item
    )

    ; Initial state
    (:init
        ; Agent and drone locations
        (agent_at robot_1 living_room_10)
        (drone_at drone_1 living_room_10)

        ; Room neighbors (bidirectional)
        (neighbor bathroom_2 living_room_10)
        (neighbor bathroom_2 bedroom_3)
        (neighbor bathroom_2 corridor_6)
        (neighbor living_room_10 bathroom_2)
        (neighbor living_room_10 corridor_6)
        (neighbor living_room_10 dining_room_7)
        (neighbor bedroom_3 bathroom_2)
        (neighbor bedroom_3 childs_room_5)
        (neighbor bedroom_3 corridor_6)
        (neighbor childs_room_5 bedroom_3)
        (neighbor childs_room_5 corridor_6)
        (neighbor childs_room_5 kitchen_8)
        (neighbor corridor_6 living_room_10)
        (neighbor corridor_6 bathroom_2)
        (neighbor corridor_6 bedroom_3)
        (neighbor corridor_6 childs_room_5)
        (neighbor corridor_6 dining_room_7)
        (neighbor corridor_6 kitchen_8)
        (neighbor dining_room_7 living_room_10)
        (neighbor dining_room_7 corridor_6)
        (neighbor dining_room_7 kitchen_8)
        (neighbor kitchen_8 childs_room_5)
        (neighbor kitchen_8 corridor_6)
        (neighbor kitchen_8 dining_room_7)

        ; Item locations
        (item_at paper_towel_105 dining_room_7)
        (item_at top_cabinet_54 kitchen_8)

        ; Item properties
        (item_pickable paper_towel_105)
        (item_accessible paper_towel_105)

        (item_container top_cabinet_54)
        (item_openable top_cabinet_54)
        (item_closeable top_cabinet_54)
        (item_accessible top_cabinet_54)
        (item_open top_cabinet_54)  ; Already opened
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight paper_towel_105) 0.0) (= (item_width paper_towel_105) 0.050) (= (item_height paper_towel_105) 0.900)
        (= (item_weight top_cabinet_54) 0.0) (= (item_width top_cabinet_54) 0.290) (= (item_height top_cabinet_54) 1.890)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot_1) 6.0) (= (agent_gripper robot_1) 0.100) (= (agent_reach robot_1) 1.871)  ; fetch_gripper
    )

    ; Goal - view all rooms, place paper towel in cabinet, and close cabinet
    (:goal
        (and
            (room_viewed bathroom_2)
            (room_viewed bedroom_3)
            (room_viewed childs_room_5)
            (room_viewed corridor_6)
            (room_viewed dining_room_7)
            (room_viewed kitchen_8)
            (room_viewed living_room_10)
            (item_in paper_towel_105 top_cabinet_54)
            (item_closed top_cabinet_54)
        )
    )
)