;Header and description
(define (domain evening_living_room)

    (:requirements :strips :typing :adl)

    (:types agent room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (item_lamp ?i - item)
        (item_tv ?i - item)
        (item_cleanable ?i - item)
        (item_turnable ?i - item)
        (item_state_on ?i - item)
        (item_state_off ?i - item)
        (item_clean ?i - item)
    )

    (:action goto
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (agent_at ?a ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    ; turn_off: turn off a lamp (must be on)
    (:action turn_off
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_turnable ?i) (item_state_on ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_state_on ?i)) (item_state_off ?i))
    )

    ; turn_on: turn on TV or lamp (must be off)
    (:action turn_on
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_turnable ?i) (item_state_off ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_state_off ?i)) (item_state_on ?i))
    )

    ; clean: clean an item (sofa, table, etc.)
    (:action clean
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_cleanable ?i) (not(agent_loaded ?a)))
        :effect (and (item_clean ?i))
    )
)
