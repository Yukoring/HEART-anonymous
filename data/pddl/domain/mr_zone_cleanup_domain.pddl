(define (domain zone_cleanup)

    (:requirements :strips :typing)

    (:types agent room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_accessible ?i - item)
        (item_turnable ?i - item)
        (item_closeable ?i - item)
        (item_state_on ?i - item)
        (item_state_off ?i - item)
        (item_open ?i - item)
        (item_closed ?i - item)
        (agent_loaded ?a - agent)
        (is_robot_1 ?a - agent)
        (is_robot_2 ?a - agent)
        (room_allowed_r1 ?r - room)
        (room_allowed_r2 ?r - room)
    )

    ; goto for robot_1 — restricted to Zone A
    (:action goto_r1
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (is_robot_1 ?a) (agent_at ?a ?r1) (neighbor ?r1 ?r2) (room_allowed_r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    ; goto for robot_2 — restricted to Zone B
    (:action goto_r2
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (is_robot_2 ?a) (agent_at ?a ?r1) (neighbor ?r1 ?r2) (room_allowed_r2 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    (:action turn_off
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_turnable ?i) (item_state_on ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_state_on ?i)) (item_state_off ?i))
    )

    (:action close
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_closeable ?i) (item_open ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_open ?i)) (item_closed ?i))
    )
)
