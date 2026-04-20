;Header and description
(define (domain close_largest_furniture)

    (:requirements :strips :typing :adl)

    (:types agent room item)

    (:predicates
        (neighbor ?r1 - room ?r2 - room)
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_accessible ?i - item)
        (item_closeable ?i - item)
        (item_cleanable ?i - item)
        (item_open ?i - item)
        (item_closed ?i - item)
        (item_clean ?i - item)
        (agent_loaded ?a - agent)
    )

    (:action goto
        :parameters (?a - agent ?r1 - room ?r2 - room)
        :precondition (and (agent_at ?a ?r1) (neighbor ?r1 ?r2))
        :effect (and (not(agent_at ?a ?r1)) (agent_at ?a ?r2))
    )

    ; close: close an opened furniture (chest)
    (:action close
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_closeable ?i) (item_open ?i) (not(agent_loaded ?a)))
        :effect (and (not(item_open ?i)) (item_closed ?i))
    )

    ; clean: clean an item (sofa)
    (:action clean
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r) (item_at ?i ?r) (item_accessible ?i)
            (item_cleanable ?i) (not(agent_loaded ?a)))
        :effect (item_clean ?i)
    )
)
