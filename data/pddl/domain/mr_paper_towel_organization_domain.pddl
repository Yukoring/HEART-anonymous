;Header and description
(define (domain paper_towel_organization)

    (:requirements :strips :typing :adl)

    ; Begin types
    (:types
        agent drone room item  ; agent and drone are separate types
    )
    ; End types

    ; Begin predicates
    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (drone_at ?d - drone ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_openable ?i - item)
        (item_closeable ?i - item)
        (item_container ?i - item)
        (item_open ?i - item)
        (item_closed ?i - item)
        (item_in ?i1 - item ?i2 - item)
        (item_on ?i1 - item ?i2 - item)
        (room_viewed ?r - room)
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

    ; goto_drone: use ONLY when the agent is a drone type. Converted from navigate(drone, ...).
    (:action goto_drone
        :parameters (?d - drone ?r1 - room ?r2 - room)
        :precondition (and
            (drone_at ?d ?r1)
            (neighbor ?r1 ?r2)
        )
        :effect (and
            (not(drone_at ?d ?r1))
            (drone_at ?d ?r2)
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

    ; take_view: use ONLY when the agent is a drone type. Converted from check(drone, ...).
    ; Note: take_view takes a room argument, not an item — drone surveys the whole room.
    (:action take_view
        :parameters (?d - drone ?r - room)
        :precondition (and
            (drone_at ?d ?r)
        )
        :effect (and
            (room_viewed ?r)
        )
    )

    ; Place_in action - only agent can perform
    (:action place_in
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i2 ?r)
            (item_accessible ?i2)
            (item_container ?i2)
            (item_open ?i2)
            (agent_loaded ?a)
            (agent_has_item ?a ?i1)
            (item_pickable ?i1)
        )
        :effect (and
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i1))
            (item_in ?i1 ?i2)
        )
    )

    ; Close action - only agent can perform
    (:action close
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_closeable ?i)
            (item_openable ?i)
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