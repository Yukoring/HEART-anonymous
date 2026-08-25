(define (problem benevolence_pack_essentials)
    (:domain pack_essentials)

    ; Objects
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        notebook_64 pen_56 briefcase_61 table_1 sink_19 chest_12 shelf_47 notebook_54 - item
    )

    ; Initial state
    (:init
        ; Agent location
        (agent_at robot living_room_12)

        ; Room neighbors (bidirectional)
        (neighbor corridor_7 kitchen_11)
        (neighbor corridor_7 living_room_12)
        (neighbor corridor_7 staircase_15)
        (neighbor corridor_7 dining_room_9)

        (neighbor dining_room_9 kitchen_11)
        (neighbor dining_room_9 living_room_12)
        (neighbor dining_room_9 staircase_15)
        (neighbor dining_room_9 corridor_7)

        (neighbor kitchen_11 staircase_15)
        (neighbor kitchen_11 corridor_7)
        (neighbor kitchen_11 dining_room_9)

        (neighbor living_room_12 staircase_15)
        (neighbor living_room_12 corridor_7)
        (neighbor living_room_12 dining_room_9)

        (neighbor staircase_15 kitchen_11)
        (neighbor staircase_15 living_room_12)
        (neighbor staircase_15 corridor_7)
        (neighbor staircase_15 dining_room_9)

        ; Item locations
        (item_at notebook_64 dining_room_9)  ; on table_1
        (item_at pen_56 kitchen_11)          ; in sink_19
        (item_at briefcase_61 living_room_12); in chest_12
        (item_at table_1 dining_room_9)
        (item_at sink_19 kitchen_11)
        (item_at chest_12 living_room_12)
        (item_at shelf_47 corridor_7)

        ; Item properties - notebook_64
        (item_pickable notebook_64)
        (item_accessible notebook_64)

        ; Item properties - pen_56
        (item_pickable pen_56)
        (item_accessible pen_56)

        ; Item properties - briefcase_61
        (item_accessible briefcase_61)
        (item_container briefcase_61)
    
        ; Restored objects — infeasibility is derived, not assumed
        (item_at notebook_54 corridor_7) (item_pickable notebook_54) (item_accessible notebook_54)

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight briefcase_61) 0.0) (= (item_width briefcase_61) 0.346) (= (item_height briefcase_61) 0.606)
        (= (item_weight chest_12) 0.0) (= (item_width chest_12) 0.300) (= (item_height chest_12) 0.250)
        (= (item_weight notebook_54) 0.0) (= (item_width notebook_54) 0.025) (= (item_height notebook_54) 2.304)
        (= (item_weight notebook_64) 0.0) (= (item_width notebook_64) 0.050) (= (item_height notebook_64) 0.781)
        (= (item_weight pen_56) 0.0) (= (item_width pen_56) 0.016) (= (item_height pen_56) 0.087)
        (= (item_weight shelf_47) 0.0) (= (item_width shelf_47) 0.108) (= (item_height shelf_47) 1.600)
        (= (item_weight sink_19) 0.0) (= (item_width sink_19) 0.580) (= (item_height sink_19) 0.450)
        (= (item_weight table_1) 0.0) (= (item_width table_1) 0.710) (= (item_height table_1) 0.380)

        ; fetch_gripper limits (URDF and published payload)
        (= (agent_payload robot) 6.0) (= (agent_gripper robot) 0.100) (= (agent_reach robot) 1.871)
    )

    ; Goal - put one notebook (either 64 or 54) and pen in briefcase
    (:goal
        (and

            (item_in notebook_64 briefcase_61)
            (item_in pen_56 briefcase_61)
        )
    )
)
