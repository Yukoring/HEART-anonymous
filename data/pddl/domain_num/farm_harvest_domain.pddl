;Header and description
(define (domain farm_harvest)

    ; Numeric variant. The hand-authored `item_accessible` flag is gone: whether
    ; a tomato can be picked now follows from its measured height and width
    ; against the robot's reach and jaw opening, so no object is declared
    ; unpickable by an author's judgement.
    ;
    ; Two ripeness states, not three. Rotten fruit and the `discard` action that
    ; went with it were removed: HEART lists rotten produce among the objects
    ; the robot cannot use, conflating a state with a physical limit, so the
    ; planner left it alone rather than throwing it away. That defect is worth
    ; recording, but it is not what this evaluation measures.

    (:requirements :strips :typing :adl :fluents)

    (:types
        agent room item
    )

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)

        (item_ripe ?i - item)
        (item_unripe ?i - item)

        (item_collected ?i - item)
    )

    (:functions
        (item_height ?i - item)     ; m, above the ground
        (item_width ?i - item)      ; m, narrowest extent
        (agent_reach ?a - agent)    ; m, highest graspable point
        (agent_gripper ?a - agent)  ; m, maximum jaw separation
    )

    (:action goto
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and
            (agent_at ?a ?r1)
            (neighbor ?r1 ?r2)
        )
        :effect (and
            (not(agent_at ?a ?r1))
            (agent_at ?a ?r2)
        )
    )

    ; pick: harvest a tomato. Reachability and grasp width are checked against
    ; the robot's own limits rather than a per-object flag.
    (:action pick
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_pickable ?i)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i))
            (<= (item_height ?i) (agent_reach ?a))
            (<= (item_width ?i) (agent_gripper ?a))
        )
        :effect (and
            (not(item_at ?i ?r))
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
        )
    )

    ; place_on_robot: load the held item onto the robot's on-board carrier.
    ;
    ; This domain has exactly one way to put something down, so the planners'
    ; two — "place" and "drop" — both map here, along with "put", "load" and
    ; "store", whatever target the plan names for them. There is nowhere else
    ; in this scene for harvested fruit to go.
    ;
    ; An earlier version forbade this at the dock, to force loading during
    ; traversal. That rule is nowhere in the instruction, so no planner could
    ; infer it, and it failed every plan that carried fruit back before loading.
    ; A rule that penalises every condition for something none of them can know
    ; measures nothing.
    (:action place_on_robot
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
        )
        :effect (and
            (item_collected ?i)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i))
        )
    )

)
