;Header and description
(define (domain laundry_heart)

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
        (item_turnable ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_in ?i1 - item ?i2 - item)
        (item_open ?i - item)
        (item_closed ?i - item)
        (item_turned_on ?i - item)
        (item_turned_off ?i - item)
        (item_clean ?i - item)
        (item_dirty ?i - item)
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
            (not(item_at ?i ?r))
            (item_accessible ?i)
            (item_pickable ?i)
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

    (:action open
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_openable ?i)
            (item_closed ?i)
            (not(agent_loaded ?a)) ; hand must be empty
        )
        :effect (and
            (not(item_closed ?i))
            (item_open ?i)
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
            (not(agent_loaded ?a)) ; hand must be empty
        )
        :effect (and
            (not(item_open ?i))
            (item_closed ?i)
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

    ; turn_on_washer: use ONLY when the target object is a washer/washing_machine.
    ; For other "turn_on" actions, use generic turn_on if available.
    (:action turn_on_washer
        :parameters (?a - agent ?washer - item ?clothes - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?washer ?r)
            (item_accessible ?washer)
            (item_turnable ?washer)
            (item_closed ?washer)
            (item_turned_off ?washer)
            (item_in ?clothes ?washer)
            (item_dirty ?clothes)
            (not(agent_loaded ?a)) ; hand must be empty
        )
        :effect (and
            (not(item_turned_off ?washer))
            (item_turned_on ?washer)
            (not(item_dirty ?clothes))
            (item_clean ?clothes)
        )
    )
    ; End actions

)