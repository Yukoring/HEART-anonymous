(define (domain glass_delivery)

    (:requirements :strips :typing)

    (:types agent drone room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (drone_at ?d - drone ?r - room)
        (item_at ?i - item ?r - room)
        (item_openable ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (item_open ?i - item)
        (item_closed ?i - item)
        (item_checked ?i - item)
    )

    (:action goto
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (agent_at ?a ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    (:action goto_drone
        :parameters (?d - drone ?r1 - room ?r2 - room)
        :precondition (and (drone_at ?d ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(drone_at ?d ?r1)) (drone_at ?d ?r2))
    )

    (:action open
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_openable ?i) (item_closed ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_closed ?i)) (item_open ?i))
    )

    ; check_inside_drone: drone inspects inside an opened container
    (:action check_inside_drone
        :parameters (?d - drone ?c - item ?r - room)
        :precondition (and
            (drone_at ?d ?r) (item_at ?c ?r)
            (item_accessible ?c) (item_open ?c))
        :effect (and (item_checked ?c))
    )
)
