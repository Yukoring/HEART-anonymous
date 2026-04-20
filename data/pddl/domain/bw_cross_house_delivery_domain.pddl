;Header and description
(define (domain cross_house_delivery)

    (:requirements :strips :typing)

    (:types agent room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_container ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_in ?i1 - item ?i2 - item)
    )

    (:action goto
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (agent_at ?a ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    (:action pick
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_pickable ?i) (not(agent_loaded ?a)))
        :effect (and
            (not(item_at ?i ?r)) (agent_loaded ?a) (agent_has_item ?a ?i))
    )

    (:action drop
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and (agent_at ?a ?r) (agent_loaded ?a) (agent_has_item ?a ?i))
        :effect (and (item_at ?i ?r) (not(agent_loaded ?a)) (not(agent_has_item ?a ?i)))
    )

    ; place_in: put item into a container (all containers in this task are already open)
    (:action place_in
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i2 ?r) (item_pickable ?i1)
            (item_container ?i2) (item_accessible ?i2)
            (agent_loaded ?a) (agent_has_item ?a ?i1))
        :effect (and
            (item_in ?i1 ?i2) (not(agent_loaded ?a)) (not(agent_has_item ?a ?i1)))
    )
)
