;Header and description
(define (domain clean_and_inspect)

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
        (item_cleanable ?i - item)
        (item_clean ?i - item)
        (item_inspected ?i - item)
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
            (agent_at ?a ?r)
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
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i))
        )
    )

    ; Clean action - only agent can perform
    (:action clean
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_cleanable ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (item_clean ?i)
        )
    )

    ; inspect: use ONLY when the agent is a drone type. Converted from check(drone, ...).
    (:action inspect
        :parameters (?d - drone ?i - item ?r - room)
        :precondition (and
            (drone_at ?d ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_pickable ?i)
        )
        :effect (and
            (item_inspected ?i)
        )
    )
    ; End actions
)