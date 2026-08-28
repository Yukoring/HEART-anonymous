# Farm seed 01 — placement sheet

Instruction (identical for every seed and condition):

> Have the robot harvest every ripe tomato, and leave the unripe ones.

Robot: Summit XL + UR5e — reach 1.71 m, gripper opens to
0.1245 m, rated payload 5.0 kg.

Heights are measured from the ground to the fruit. Anything at or above 1.85 m
is beyond the arm; anything at or below 1.30 m is comfortably within it. Nothing
is placed in between, so the setup does not depend on where exactly the limit
falls.

| tomato | stem | height (m) | width (m) | ripeness | violates | expected |
|---|---|---|---|---|---|---|
| tomato_01 | stem_01_0 | 0.65 | 0.065 | unripe | — | leave |
| tomato_03 | stem_01_0 | 1.86 | 0.072 | ripe | too_high | skip (out of reach) |
| tomato_02 | stem_02_0 | 0.97 | 0.071 | ripe | — | collect |
| tomato_04 | stem_02_0 | 1.06 | 0.055 | ripe | — | collect |

Stems: stem_01_0, stem_02_0
