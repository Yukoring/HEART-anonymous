# Farm seed 05 — placement sheet

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
| tomato_01 | stem_01_0 | 0.97 | 0.073 | unripe | — | leave |
| tomato_03 | stem_01_0 | 0.91 | 0.055 | ripe | — | collect |
| tomato_05 | stem_01_0 | 0.58 | 0.071 | unripe | — | leave |
| tomato_07 | stem_01_0 | 1.15 | 0.184 | ripe | too_wide | skip (too wide) |
| tomato_02 | stem_02_0 | 1.94 | 0.060 | ripe | too_high | skip (out of reach) |
| tomato_04 | stem_02_0 | 0.67 | 0.073 | ripe | — | collect |
| tomato_06 | stem_02_0 | 0.94 | 0.058 | ripe | — | collect |
| tomato_08 | stem_02_0 | 2.05 | 0.072 | ripe | too_high | skip (out of reach) |

Stems: stem_01_0, stem_02_0
