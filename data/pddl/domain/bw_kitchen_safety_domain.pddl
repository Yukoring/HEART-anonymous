;Header and description
(define (domain kitchen_safety)

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
        (item_turnable ?i - item)
        (item_closeable ?i - item)
        (item_openable ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (item_turned_on ?i - item)
        (item_turned_off ?i - item)
        (item_open ?i - item)
        (item_closed ?i - item)
    )
    ; End predicates

    ; Begin actions
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

    (:action turn_off
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_turnable ?i)
            (item_turned_on ?i)
            (not(agent_loaded ?a))  ; hand must be free
        )
        :effect (and
            (not(item_turned_on ?i))
            (item_turned_off ?i)
        )
    )

    (:action turn_on
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_turnable ?i)
            (item_turned_off ?i)
            (item_closed ?i)  ; fridge must be closed to turn on
            (not(agent_loaded ?a))  ; hand must be free
        )
        :effect (and
            (not(item_turned_off ?i))
            (item_turned_on ?i)
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
            (not(agent_loaded ?a))  ; hand must be free
        )
        :effect (and
            (not(item_open ?i))
            (item_closed ?i)
        )
    )
    ; End actions

)