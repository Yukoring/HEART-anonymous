(define (domain kitchen_survey)

    (:requirements :strips :typing)

    (:types agent drone room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (drone_at ?d - drone ?r - room)
        (item_at ?i - item ?r - room)
        (item_accessible ?i - item)
        (item_turnable ?i - item)
        (item_state_on ?i - item)
        (item_state_off ?i - item)
        (item_open ?i - item)
        (item_closed ?i - item)
        (agent_loaded ?a - agent)
        (room_viewed ?r - room)
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

    (:action turn_off
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_turnable ?i) (item_state_on ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_state_on ?i)) (item_state_off ?i))
    )

    (:action close_window
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_open ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_open ?i)) (item_closed ?i))
    )

    ; take_view: drone surveys a room. Converted from check(drone, room) or capture_aerial_view(drone, room).
    (:action take_view
        :parameters (?d - drone ?r - room)
        :precondition (and (drone_at ?d ?r))
        :effect (and (room_viewed ?r))
    )
)
