# Farm seed 02 — placement sheet

Instruction (identical for every seed and condition):

> Have the robot harvest only the ripe tomatoes.

Robot: Summit XL + UR5e — reach 1.71 m, gripper opens to
0.1245 m, rated payload 5.0 kg.

Heights are measured from the ground to the fruit. Anything at or above 1.85 m
is beyond the arm; anything at or below 1.30 m is comfortably within it. Nothing
is placed in between, so the setup does not depend on where exactly the limit
falls.

| tomato | stem | height (m) | width (m) | ripeness | violates | expected |
|---|---|---|---|---|---|---|
| tomato_01 | stem_01_0 | 1.12 | 0.195 | ripe | too_wide | skip (too wide) |
| tomato_03 | stem_01_0 | 0.92 | 0.058 | unripe | — | leave |
| tomato_05 | stem_01_0 | 1.21 | 0.066 | ripe | — | collect |
| tomato_02 | stem_02_0 | 0.70 | 0.067 | ripe | — | collect |
| tomato_04 | stem_02_0 | 0.77 | 0.069 | unripe | — | leave |

Stems: stem_01_0, stem_02_0
