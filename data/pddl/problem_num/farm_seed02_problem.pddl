(define (problem farm_harvest_seed02)
    (:domain farm_harvest)

    ; Goal derived from the oracle, not hand-written: every ripe tomato the
    ; robot can actually grasp is collected, and the rest are left where they are.
    (:objects
        robot - agent
        stem_01_0 stem_02_0 - room
        tomato_01 tomato_02 tomato_03 tomato_04 tomato_05 - item
    )

    (:init
        (agent_at robot stem_01_0)

        (neighbor stem_01_0 stem_02_0)
        (neighbor stem_02_0 stem_01_0)

        (item_at tomato_01 stem_01_0) (item_pickable tomato_01) (item_ripe tomato_01)
        (= (item_height tomato_01) 1.118) (= (item_width tomato_01) 0.195)
        (item_at tomato_02 stem_02_0) (item_pickable tomato_02) (item_ripe tomato_02)
        (= (item_height tomato_02) 0.697) (= (item_width tomato_02) 0.067)
        (item_at tomato_03 stem_01_0) (item_pickable tomato_03) (item_unripe tomato_03)
        (= (item_height tomato_03) 0.915) (= (item_width tomato_03) 0.058)
        (item_at tomato_04 stem_02_0) (item_pickable tomato_04) (item_unripe tomato_04)
        (= (item_height tomato_04) 0.765) (= (item_width tomato_04) 0.069)
        (item_at tomato_05 stem_01_0) (item_pickable tomato_05) (item_ripe tomato_05)
        (= (item_height tomato_05) 1.21) (= (item_width tomato_05) 0.066)

        ; summit_ur5e limits, from the URDF and the rated payload
        (= (agent_reach robot) 1.714) (= (agent_gripper robot) 0.1245)
    )

    (:goal (and
        (item_collected tomato_02)
        (item_collected tomato_05)
        (not (item_collected tomato_03))
        (not (item_collected tomato_04))
    ))
)
