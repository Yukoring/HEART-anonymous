;Header and description
(define (domain home_security)

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
        (item_checked ?i - item)
        (item_state_on ?i - item)
        (item_state_off ?i - item)
        (item_window ?i - item)
        (item_lamp ?i - item)
    )
    ; End predicates

    ; Begin actions
    ; Goto action for agent
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

    ; Pick action for agent only (drone cannot pick)
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

    ; Drop action for agent only (drone cannot drop)
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

    ; check: use ONLY when the agent is a robot type (not drone).
    (:action check
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_window ?i)
        )
        :effect (and
            (item_checked ?i)
        )
    )

    ; check_drone: use ONLY when the agent is a drone type (not robot).
    (:action check_drone
        :parameters (?d - drone ?i - item ?r - room)
        :precondition (and
            (drone_at ?d ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_window ?i)
        )
        :effect (and
            (item_checked ?i)
        )
    )

    ; Turn_off action - only agent (robot_1) can perform
    (:action turn_off
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_lamp ?i)
            (item_state_on ?i)
        )
        :effect (and
            (not(item_state_on ?i))
            (item_state_off ?i)
        )
    )
    ; End actions
)