(define (problem merom_zone_delivery)
    (:domain zone_delivery)

    (:objects
        robot_1 robot_2 - agent
        bathroom_2 bedroom_3 childs_room_5 corridor_6 dining_room_7 kitchen_8 living_room_10 - room
        notebook_101 wine_bottle_94 bottom_cabinet_8 table_20 - item
    )

    (:init
        ; Robot identity
        (is_robot_1 robot_1)
        (is_robot_2 robot_2)

        ; Robot start positions — need navigation
        (agent_at robot_1 bathroom_2)
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

        ; Zone A: robot_1
        (room_allowed_r1 living_room_10)
        (room_allowed_r1 bathroom_2)
        (room_allowed_r1 bedroom_3)
        (room_allowed_r1 corridor_6)

        ; Zone B: robot_2
        (room_allowed_r2 kitchen_8)
        (room_allowed_r2 dining_room_7)
        (room_allowed_r2 childs_room_5)
        (room_allowed_r2 corridor_6)

        ; Notebook in living room (Zone A)
        (item_at notebook_101 living_room_10)
        (item_pickable notebook_101) (item_accessible notebook_101)

        ; Wine bottle in kitchen (Zone B)
        (item_at wine_bottle_94 kitchen_8)
        (item_pickable wine_bottle_94) (item_accessible wine_bottle_94)

        ; Bedroom cabinet — delivery target for robot_1 (Zone A)
        (item_at bottom_cabinet_8 bedroom_3)
        (item_surface bottom_cabinet_8) (item_accessible bottom_cabinet_8)

        ; Dining table — delivery target for robot_2 (Zone B)
        (item_at table_20 dining_room_7)
        (item_surface table_20) (item_accessible table_20)
    
        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight bottom_cabinet_8) 0.0) (= (item_width bottom_cabinet_8) 0.355) (= (item_height bottom_cabinet_8) 0.250)
        (= (item_weight notebook_101) 0.0) (= (item_width notebook_101) 0.050) (= (item_height notebook_101) 0.408)
        (= (item_weight table_20) 0.0) (= (item_width table_20) 0.800) (= (item_height table_20) 0.400)
        (= (item_weight wine_bottle_94) 0.0) (= (item_width wine_bottle_94) 0.060) (= (item_height wine_bottle_94) 0.959)

        ; Robot limits (URDF and published payload)
        (= (agent_payload robot_1) 6.0) (= (agent_gripper robot_1) 0.100) (= (agent_reach robot_1) 1.871)  ; fetch_gripper
        (= (agent_payload robot_2) 6.0) (= (agent_gripper robot_2) 0.100) (= (agent_reach robot_2) 1.871)  ; fetch_gripper
    )

    (:goal
        (and
            (item_on notebook_101 bottom_cabinet_8)
            (item_on wine_bottle_94 table_20)
        )
    )
)
