(define (domain zone_delivery)

    (:requirements :strips :typing :fluents)

    (:types agent room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_surface ?i - item)
        (item_accessible ?i - item)
        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)
        (item_on ?i1 - item ?i2 - item)
        (is_robot_1 ?a - agent)
        (is_robot_2 ?a - agent)
        (room_allowed_r1 ?r - room)
        (room_allowed_r2 ?r - room)
    )

    ; goto for robot_1 — restricted to Zone A
    (:functions
        (item_weight ?i - item)     ; kg
        (item_width ?i - item)      ; m, narrowest extent of the bounding box
        (item_height ?i - item)     ; m, above the floor
        (agent_payload ?a - agent)  ; kg, rated
        (agent_gripper ?a - agent)  ; m, maximum jaw separation
        (agent_reach ?a - agent)    ; m, highest graspable point
    )

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

    (:action pick
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_pickable ?i) (not(agent_loaded ?a))
            (<= (item_weight ?i) (agent_payload ?a))
            (<= (item_width ?i) (agent_gripper ?a))
            (<= (item_height ?i) (agent_reach ?a)))
        :effect (and
            (not(item_at ?i ?r)) (agent_loaded ?a) (agent_has_item ?a ?i))
    )

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
