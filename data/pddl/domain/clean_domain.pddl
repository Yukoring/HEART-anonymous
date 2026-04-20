;Header and description
(define (domain clean)

    (:requirements :strips :typing :adl)

    ; Begin types
    (:types
        agent room item
    )
    ; End types

    ; Begin predicates
    (:predicates
        (agent_at ?a - agent ?r - room)
        (item_at ?i - item ?r - room)
        (item_pickable ?i - item)
        (item_accessible ?i - item)

        (neighbor ?r1 - room ?r2 - room)

        (agent_loaded ?a - agent)
        (agent_has_item ?a - agent ?i - item)

        (item_is_mop ?i - item)
        (item_is_sink ?i - item)
        (item_is_rubbish_bin ?i - item)
        (item_is_robot_hub ?i - item)
        (item_disposed ?i - item)
        (floor_clean ?r - room)
        (mop_clean ?i - item)
        (battery_full ?a - agent)

        (item_cleanable ?i - item)
        (item_clean ?i - item)
        (item_dirty ?i - item)

        ; Container and surface predicates
        (item_openable ?i - item)
        (item_closeable ?i - item)
        (item_container ?i - item)
        (item_surface ?i - item)
        (item_open ?i - item)
        (item_closed ?i - item)
        (item_in ?i1 - item ?i2 - item)
        (item_on ?i1 - item ?i2 - item)
        (item_turnable ?i - item)
        (item_turned_on ?i - item)
        (item_turned_off ?i - item)
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

    (:action dispose
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i2 ?r)
            (item_accessible ?i1)
            ; (item_accessible ?i2)
            (item_pickable ?i1)
            (item_is_rubbish_bin ?i2)
            (agent_loaded ?a)
            (agent_has_item ?a ?i1)
            (not(item_disposed ?i1))
        )
        :effect (and
            (item_disposed ?i1)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i1))
            (not(battery_full ?a))
        )
    )

    (:action mop_floor
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_accessible ?i)
            (item_pickable ?i)
            (item_is_mop ?i)
            (agent_loaded ?a)
            (agent_has_item ?a ?i)
            (not(floor_clean ?r))
            (mop_clean ?i)
        )
        :effect (and
            (floor_clean ?r)
            (not(mop_clean ?i))
            (not(battery_full ?a))
        )
    )

    (:action clean_mop
        :parameters (?a - agent ?i1 - item ?i2 - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i2 ?r)
            (item_accessible ?i1)
            ; (item_accessible ?i2)
            (item_pickable ?i1)
            (item_is_mop ?i1)
            (agent_loaded ?a)
            (agent_has_item ?a ?i1)
            (item_is_sink ?i2)
            (not(mop_clean ?i1))
        )
        :effect (and
            (mop_clean ?i1)
            (item_at ?i1 ?r)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i1))
            (not(battery_full ?a))
        )
    )

    (:action charge
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_is_robot_hub ?i)
            (not(battery_full ?a))
            (not(agent_loaded ?a))
        )
        :effect (and
            (battery_full ?a)
        )
    )

    ; clean: clean an item in the current room (sofa, table, toilet, etc.)
    (:action clean
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_cleanable ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (item_clean ?i)
        )
    )

    ; open: open a closeable container (e.g., fridge, oven, cabinet, dishwasher)
    (:action open
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_openable ?i)
            (item_closed ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_closed ?i))
            (item_open ?i)
        )
    )

    ; close: close an open container
    (:action close
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_closeable ?i)
            (item_open ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_open ?i))
            (item_closed ?i)
        )
    )

    ; pick_from: pick an item FROM inside an open container. As result, item is taken out (item_in removed).
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

    ; place_on: place a held item ON a surface (table, countertop, shelf). As result, item will be ON the surface (item_on).
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
            (item_on ?i1 ?i2)
            (item_at ?i1 ?r)
            (not(agent_loaded ?a))
            (not(agent_has_item ?a ?i1))
        )
    )

    ; place_in: place a held item INTO an open container. As result, item will be IN the container (item_in).
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

    ; turn_on: turn on an appliance (must be closed and off)
    (:action turn_on
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_turnable ?i)
            (item_closed ?i)
            (item_turned_off ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_turned_off ?i))
            (item_turned_on ?i)
        )
    )

    ; turn_off: turn off an appliance
    (:action turn_off
        :parameters (?a - agent ?i - item ?r - room)
        :precondition (and
            (agent_at ?a ?r)
            (item_at ?i ?r)
            (item_accessible ?i)
            (item_turnable ?i)
            (item_turned_on ?i)
            (not(agent_loaded ?a))
        )
        :effect (and
            (not(item_turned_on ?i))
            (item_turned_off ?i)
        )
    )
    ; End actions
)