(define (problem beechwood_appliance_inspection)
    (:domain appliance_inspection)

    ; Objects
    (:objects
        drone_1 - drone
        bathroom_1 corridor_8 dining_room_10 home_office_11 kitchen_12 living_room_13 lobby_14 staircase_16 utility_room_18 - room
        burner_77 microwave_60 fridge_57 washer_47 dryer_48 - item
    )

    ; Initial state
    (:init
        ; Drone starts in corridor
        (drone_at drone_1 corridor_8)

        ; Room neighbors (bidirectional)
        (neighbor bathroom_1 home_office_11)
        (neighbor bathroom_1 lobby_14)
        (neighbor bathroom_1 staircase_16)
        (neighbor bathroom_1 utility_room_18)
        (neighbor bathroom_1 corridor_8)
        (neighbor corridor_8 bathroom_1)
        (neighbor corridor_8 home_office_11)
        (neighbor corridor_8 living_room_13)
        (neighbor corridor_8 staircase_16)
        (neighbor corridor_8 utility_room_18)
        (neighbor dining_room_10 kitchen_12)
        (neighbor dining_room_10 staircase_16)
        (neighbor home_office_11 bathroom_1)
        (neighbor home_office_11 living_room_13)
        (neighbor home_office_11 utility_room_18)
        (neighbor home_office_11 corridor_8)
        (neighbor kitchen_12 dining_room_10)
        (neighbor kitchen_12 living_room_13)
        (neighbor kitchen_12 staircase_16)
        (neighbor living_room_13 home_office_11)
        (neighbor living_room_13 kitchen_12)
        (neighbor living_room_13 corridor_8)
        (neighbor lobby_14 bathroom_1)
        (neighbor lobby_14 staircase_16)
        (neighbor staircase_16 bathroom_1)
        (neighbor staircase_16 dining_room_10)
        (neighbor staircase_16 kitchen_12)
        (neighbor staircase_16 lobby_14)
        (neighbor staircase_16 corridor_8)
        (neighbor utility_room_18 bathroom_1)
        (neighbor utility_room_18 home_office_11)
        (neighbor utility_room_18 corridor_8)

        ; Kitchen appliances — 3 items in kitchen_12
        (item_at burner_77 kitchen_12)
        (item_appliance burner_77)
        (item_at microwave_60 kitchen_12)
        (item_appliance microwave_60)
        (item_at fridge_57 kitchen_12)
        (item_appliance fridge_57)

        ; Utility room appliances — 2 items in utility_room_18
        (item_at washer_47 utility_room_18)
        (item_appliance washer_47)
        (item_at dryer_48 utility_room_18)
        (item_appliance dryer_48)
    )

    ; Goal: all appliances checked (kitchen + utility)
    (:goal
        (and
            (item_checked burner_77)
            (item_checked microwave_60)
            (item_checked fridge_57)
            (item_checked washer_47)
            (item_checked dryer_48)
        )
    )
)
