;Header and description
(define (domain visit_rooms)

    (:requirements :strips :typing :adl)

    (:types agent room)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (visited ?r - room)
    )

    ; goto: move to neighboring room and mark as visited
    (:action goto
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (agent_at ?a ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2) (visited ?r2))
    )
)
