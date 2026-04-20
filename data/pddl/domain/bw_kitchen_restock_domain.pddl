;Header and description
(define (domain kitchen_restock)

    (:requirements :strips :typing :adl)

    ; Begin types
    (:types
        agent room item
    )
    ; End types

    ; Begin predicates
    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_container ?i - item)
        (item_openable ?i - item)
        (item_closeable ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_in ?i1 - item ?i2 - item)
        (item_open ?i - item)
        (item_closed ?i - item)
    )
    ; End predicates

    ; Begin actions
    (:action goto
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (agent_at ?a ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    (:action pick
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_pickable ?i)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i))
        )
        :effect (and
            (not(item_at ?i ?r))
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
        )
    )

    (:action drop
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
        )
        :effect (and
            (item_at ?i ?r)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i))
        )
    )

    ; place_in: put an item into an open container (fridge is already open initially).
    (:action place_in
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i2 ?r)
            (item_pickable ?i1)
            (item_container ?i2)
            (item_accessible ?i2)
            (item_openable ?i2)
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

    (:action close
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_closeable ?i)
            (item_open ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_open ?i))
            (item_closed ?i)
        )
    )
    ; End actions
)
