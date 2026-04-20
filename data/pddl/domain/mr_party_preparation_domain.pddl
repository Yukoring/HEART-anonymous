;Header and description
(define (domain party_preparation)

    (:requirements :strips :typing :adl)

    ; Begin types
    (:types
        agent room item  ; two ground robots (robot_1, robot_2)
    )
    ; End types

    ; Begin predicates
    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_on ?i1 - item ?i2 - item)
        (item_surface ?i - item)
        (item_window ?i - item)
        (item_closeable ?i - item)
        (item_opened ?i - item)
        (item_closed ?i - item)
        (item_lamp ?i - item)
        (item_state_on ?i - item)
        (item_state_off ?i - item)
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

    ; place_on: place item on a surface (e.g., dining table)
    (:action place_on
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i2 ?r)
            (item_accessible ?i2)
            (item_surface ?i2)
            (agent_loaded ?a)
            (agent_has_item ?a ?i1)
        )
        :effect (and
            (item_on ?i1 ?i2)
            (item_at ?i1 ?r)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i1))
        )
    )

    ; close_window: use ONLY when the target object is a window (item_window)
    (:action close_window
        :parameters (?a - agent ?w - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?w ?r)
            (item_accessible ?w)
            (item_window ?w)
            (item_closeable ?w)
            (item_opened ?w)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_opened ?w))
            (item_closed ?w)
        )
    )

    ; turn_on: for lamps
    (:action turn_on
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_lamp ?i)
            (item_state_off ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_state_off ?i))
            (item_state_on ?i)
        )
    )
    ; End actions

)
