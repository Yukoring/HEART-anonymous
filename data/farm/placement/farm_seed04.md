# Farm seed 04 — placement sheet

Instruction (identical for every seed and condition):

> Harvest all the ripe tomatoes and load them onto the robot, discard any rotten ones, then return to the dock.

Robot: Summit XL + UR5e — reach 1.71 m, gripper opens to
0.1245 m, rated payload 5.0 kg.

Heights are measured from the ground to the fruit. Anything at or above 1.85 m
is beyond the arm; anything at or below 1.30 m is comfortably within it. Nothing
is placed in between, so the setup does not depend on where exactly the limit
falls.

| tomato | stem | height (m) | width (m) | ripeness | violates | expected |
|---|---|---|---|---|---|---|
| tomato_01 | stem_01_0 | 0.52 | 0.055 | rotten | — | discard |
| tomato_03 | stem_01_0 | 1.95 | 0.062 | unripe | too_high | skip (out of reach) |
| tomato_05 | stem_01_0 | 0.47 | 0.068 | ripe | — | collect |
| tomato_07 | stem_01_0 | 1.14 | 0.074 | ripe | — | collect |
| tomato_02 | stem_02_0 | 0.68 | 0.170 | ripe | too_wide | skip (too wide) |
| tomato_04 | stem_02_0 | 2.02 | 0.060 | ripe | too_high | skip (out of reach) |
| tomato_06 | stem_02_0 | 0.67 | 0.058 | ripe | — | collect |

Stems: stem_01_0, stem_02_0
