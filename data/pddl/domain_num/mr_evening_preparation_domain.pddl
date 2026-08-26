;Header and description
(define (domain evening_preparation)

    (:requirements :strips :typing :adl :fluents)

    ; Begin types
    (:types
        agent room item  ; only agent type, no drone
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
        (item_openable ?i - item)
        (item_closeable ?i - item)
        (item_container ?i - item)
        (item_open ?i - item)
        (item_closed ?i - item)
        (item_in ?i1 - item ?i2 - item)
        (item_on ?i1 - item ?i2 - item)
        (item_surface ?i - item)
        (item_window ?i - item)
        (item_opened ?i - item)
        (item_lamp ?i - item)
        (item_stove ?i - item)
        (item_turnable ?i - item)
        (item_state_on ?i - item)
        (item_state_off ?i - item)
        (item_dishwasher ?i - item)
    )
    ; End predicates

    ; Begin actions
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
        :precondition (and
            (agent_at ?a ?r1)
            (neighbor ?r1 ?r2)
        )
        :effect (and
            (not(agent_at ?a ?r1))
            (agent_at ?a ?r2)
        )
    )

    ; Regular pick - cannot pick items that are inside containers
    (:action pick
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_pickable ?i)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i))
        
            (<= (item_weight ?i) (agent_payload ?a))
            (<= (item_width ?i) (agent_gripper ?a))
            (<= (item_height ?i) (agent_reach ?a)))
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

    ; open_dishwasher: use ONLY when the target object is a dishwasher (item_dishwasher).
    ; For other "open" actions, use a generic open if available.
    (:action open_dishwasher
        :parameters (?a - agent ?d - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?d ?r)
            (item_accessible ?d)
            (item_dishwasher ?d)
            (item_openable ?d)
            (item_closeable ?d)
            (item_closed ?d)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_closed ?d))
            (item_open ?d)
        )
    )

    ; pick_from: use ONLY when the item is INSIDE a container (item_in).
    ; For picking items from surfaces or floor, use regular pick.
    (:action pick_from
        :parameters (?a - agent ?i - item ?c - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?c ?r)
            (item_in ?i ?c)
            (item_pickable ?i)
            (item_container ?c)
            (item_open ?c)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_in ?i ?c))
            (item_at ?i ?r)
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
        )
    )

    ; Place on surface action
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
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i1))
            (item_on ?i1 ?i2)
            (item_at ?i1 ?r)
        )
    )

    ; close_window: use ONLY when the target object is a window (item_window).
    ; For closing other containers, use a generic close if available.
    (:action close_window
        :parameters (?a - agent ?w - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?w ?r)
            (item_accessible ?w)
            (item_window ?w)
            (item_closeable ?w)
            (item_openable ?w)
            (item_opened ?w)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_opened ?w))
            (item_closed ?w)
        )
    )

    ; Turn off action — for any turnable item (lamps, stove)
    (:action turn_off
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_turnable ?i)
            (item_state_on ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_state_on ?i))
            (item_state_off ?i)
        )
    )
    ; End actions
)