;Header and description
(define (domain cheese_from_fridge)

    (:requirements :strips :typing :adl)

    (:types agent room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_container ?i - item)
        (item_openable ?i - item)
        (item_closeable ?i - item)
        (item_surface ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_in ?i1 - item ?i2 - item)
        (item_on ?i1 - item ?i2 - item)
        (item_open ?i - item)
        (item_closed ?i - item)
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
        :effect (and (not(item_at ?i ?r)) (agent_loaded ?a) (agent_has_item ?a ?i))
    )

    (:action drop
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and (agent_at ?a ?r) (agent_loaded ?a) (agent_has_item ?a ?i))
        :effect (and (item_at ?i ?r) (not(agent_loaded ?a)) (not(agent_has_item ?a ?i)))
    )

    ; open: open a container (fridge)
    (:action open
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_openable ?i) (item_closed ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_closed ?i)) (item_open ?i))
    )

    ; close: close an open container
    (:action close
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_closeable ?i) (item_open ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_open ?i)) (item_closed ?i))
    )

    ; pick_from: pick item FROM inside an open container
    (:action pick_from
        :parameters (?a - agent ?i - item ?c - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?c ?r)
            (item_in ?i ?c) (item_pickable ?i)
            (item_container ?c) (item_open ?c)
            (not(agent_loaded ?a)))
        :effect (and
            (not(item_in ?i ?c)) (item_at ?i ?r)
            (agent_loaded ?a) (agent_has_item ?a ?i))
    )

    ; place_on: place item on a surface
    (:action place_on
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i2 ?r) (item_accessible ?i2)
            (item_surface ?i2) (agent_loaded ?a) (agent_has_item ?a ?i1))
        :effect (and
            (item_on ?i1 ?i2) (item_at ?i1 ?r)
            (not(agent_loaded ?a)) (not(agent_has_item ?a ?i1)))
    )
)
