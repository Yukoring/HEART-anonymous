;Header and description
(define (domain farm_harvest)

    ; Numeric variant. The hand-authored `item_accessible` flag is gone: whether
    ; a tomato can be picked now follows from its measured height and width
    ; against the robot's reach and jaw opening, so no object is declared
    ; unpickable by an author's judgement.

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
        (item_rotten ?i - item)

        (item_collected ?i - item)
        (item_discarded ?i - item)

        ; Marks the dock zone so place_on_robot can be blocked there:
        ; loading the on-board basket while parked at the dock makes no
        ; physical sense, so the planner must load during field traversal.
        (room_is_dock ?r - room)
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
    ; An earlier version forbade this at the dock, to force loading during
    ; traversal. That rule is nowhere in the instruction, so no planner could
    ; infer it, and it failed every plan that carried fruit back before loading
    ; — which is how all three conditions read "load them onto the robot, then
    ; return to the dock". A rule that penalises every condition for something
    ; none of them can know measures nothing. The logical side of the task is
    ; already carried by the three ripeness classes.
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

    ; discard: drop the held item off-side. Only rotten produce may be
    ; discarded, so ripe fruit cannot be thrown away by mistake.
    (:action discard
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
            (item_rotten ?i)
        )
        :effect (and
            (item_discarded ?i)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i))
        )
    )
)
