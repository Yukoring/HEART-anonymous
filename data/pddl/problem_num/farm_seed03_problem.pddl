(define (problem farm_harvest_seed03)
    (:domain farm_harvest)

    ; Goal derived from the oracle, not hand-written: every ripe tomato the
    ; robot can actually grasp is collected, every rotten one it can grasp is
    ; discarded, and the rest are left where they are.
    (:objects
        robot - agent
        dock_0 door_0 stem_01_0 stem_02_0 - room
        tomato_01 tomato_02 tomato_03 tomato_04 tomato_05 tomato_06 - item
    )

    (:init
        (agent_at robot dock_0)

        (room_is_dock dock_0)

        (neighbor dock_0 door_0)
        (neighbor dock_0 stem_01_0)
        (neighbor dock_0 stem_02_0)
        (neighbor door_0 dock_0)
        (neighbor door_0 stem_01_0)
        (neighbor door_0 stem_02_0)
        (neighbor stem_01_0 dock_0)
        (neighbor stem_01_0 door_0)
        (neighbor stem_01_0 stem_02_0)
        (neighbor stem_02_0 dock_0)
        (neighbor stem_02_0 door_0)
        (neighbor stem_02_0 stem_01_0)

        (item_at tomato_01 stem_01_0) (item_pickable tomato_01) (item_ripe tomato_01)
        (= (item_height tomato_01) 0.951) (= (item_width tomato_01) 0.056)
        (item_at tomato_02 stem_02_0) (item_pickable tomato_02) (item_ripe tomato_02)
        (= (item_height tomato_02) 1.12) (= (item_width tomato_02) 0.06)
        (item_at tomato_03 stem_01_0) (item_pickable tomato_03) (item_ripe tomato_03)
        (= (item_height tomato_03) 2.049) (= (item_width tomato_03) 0.064)
        (item_at tomato_04 stem_02_0) (item_pickable tomato_04) (item_rotten tomato_04)
        (= (item_height tomato_04) 1.945) (= (item_width tomato_04) 0.068)
        (item_at tomato_05 stem_01_0) (item_pickable tomato_05) (item_rotten tomato_05)
        (= (item_height tomato_05) 0.958) (= (item_width tomato_05) 0.072)
        (item_at tomato_06 stem_02_0) (item_pickable tomato_06) (item_ripe tomato_06)
        (= (item_height tomato_06) 1.043) (= (item_width tomato_06) 0.068)

        ; summit_ur5e limits, from the URDF and the rated payload
        (= (agent_reach robot) 1.714) (= (agent_gripper robot) 0.1245)
    )

    (:goal (and
        (item_collected tomato_01)
        (item_collected tomato_02)
        (item_collected tomato_06)
        (item_discarded tomato_05)
        (agent_at robot dock_0)
    ))
)
