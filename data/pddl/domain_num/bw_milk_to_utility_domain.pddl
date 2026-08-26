(define (domain milk_to_utility)

    (:requirements :strips :typing :fluents)

    (:types
        agent room item
    )

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_accessible ?i - item)
        (item_container ?i - item)
        (item_open ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_in ?i1 - item ?i2 - item)
    )
    (:functions
        (item_weight ?i - item)     ; kg
        (item_width ?i - item)      ; m, narrowest extent of the bounding box
        (item_height ?i - item)     ; m, above the floor
        (agent_payload ?a - agent)  ; kg, rated
        (agent_gripper ?a - agent)  ; m, maximum jaw separation
        (agent_reach ?a - agent)    ; m, highest graspable point
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

    (:action pick
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_pickable ?i)
            (not(agent_loaded ?a))
        
            (<= (item_weight ?i) (agent_payload ?a))
            (<= (item_width ?i) (agent_gripper ?a))
            (<= (item_height ?i) (agent_reach ?a)))
        :effect (and
            (not(item_at ?i ?r))
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
        )
    )

    (:action place_in
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i2 ?r)
            (item_pickable ?i1)
            (item_container ?i2)
            (item_accessible ?i2)
            (item_open ?i2)
            (agent_loaded ?a)
            (agent_has_item ?a ?i1)
        )
        :effect (and
            (item_in ?i1 ?i2)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i1))
        )
    )
)
