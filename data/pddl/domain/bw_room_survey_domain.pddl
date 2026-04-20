;Header and description
(define (domain room_survey)

    (:requirements :strips :typing)

    ; Begin types — drone-only task (no manipulation)
    (:types
        drone room item
    )
    ; End types

    ; Begin predicates
    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (drone_at ?d - drone ?r - room)
        (item_at ?i - item ?r - room)
        (item_lamp ?i - item)
        (item_checked ?i - item)
    )
    ; End predicates

    ; Begin actions
    ; goto_drone: drone flies between neighboring rooms
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

    ; check_drone: drone visually inspects a lamp in the same room
    (:action check_drone
        :parameters (?d - drone ?i - item ?r - room)
        :precondition (and
            (drone_at ?d ?r)
            (item_at ?i ?r)
            (item_lamp ?i)
        )
        :effect (and
            (item_checked ?i)
        )
    )
    ; End actions
)
