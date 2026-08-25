(define (problem benevolence_nearest_food)
    (:domain nearest_food)

    ; sandwich_70 is in corridor (nearest to living_room start via corridor)
    ; and graspable by jr2 (0.05m min)
    (:objects
        robot - agent
        corridor_7 dining_room_9 kitchen_11 living_room_12 staircase_15 - room
        sandwich_70 table_1 - item
    )

    (:init
        (agent_at robot living_room_12)

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

        ; Sandwich in corridor
        (item_at sandwich_70 corridor_7)
        (item_pickable sandwich_70) (item_accessible sandwich_70)

        ; Dining table
        (item_at table_1 dining_room_9)
        (item_surface table_1) (item_accessible table_1)

        ; Restored objects — infeasibility is derived, not assumed

        ; Measured values (scene graph); weight 0.0 where unmeasured
        (= (item_weight sandwich_70) 0.0) (= (item_width sandwich_70) 0.050) (= (item_height sandwich_70) 0.850)
        (= (item_weight table_1) 0.0) (= (item_width table_1) 0.710) (= (item_height table_1) 0.380)

        ; jr2_kinova_gripper limits (URDF and published payload)
        (= (agent_payload robot) 2.6) (= (agent_gripper robot) 0.088) (= (agent_reach robot) 1.432)
    )

    (:goal (item_on sandwich_70 table_1))
)
