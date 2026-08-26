(define (domain cross_delivery)

    (:requirements :strips :typing :fluents)

    (:types agent drone room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (drone_at ?d - drone ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_surface ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_on ?i1 - item ?i2 - item)
        (item_checked ?i - item)
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
        :precondition (and (agent_at ?a ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    (:action goto_drone
        :parameters (?d - drone ?r1 - room ?r2 - room)
        :precondition (and (drone_at ?d ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(drone_at ?d ?r1)) (drone_at ?d ?r2))
    )

    (:action pick
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_pickable ?i) (not(agent_loaded ?a))
            (<= (item_weight ?i) (agent_payload ?a))
            (<= (item_width ?i) (agent_gripper ?a))
            (<= (item_height ?i) (agent_reach ?a)))
        :effect (and
            (not(item_at ?i ?r)) (agent_loaded ?a) (agent_has_item ?a ?i))
    )

    (:action place_on
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i2 ?r) (item_accessible ?i2)
            (item_surface ?i2) (agent_loaded ?a) (agent_has_item ?a ?i1))
        :effect (and
            (item_on ?i1 ?i2) (item_at ?i1 ?r)
            (not(agent_loaded ?a)) (not(agent_has_item ?a ?i1)))
    )

    (:action check_drone
        :parameters (?d - drone ?i - item ?r - room)
        :precondition (and (drone_at ?d ?r) (item_at ?i ?r) (item_accessible ?i))
        :effect (and (item_checked ?i))
    )
)
