# Screen D1 result: **STOP**

Page `docs/research/protocols/screen_D1_detector_faults.md` (sha256 1991f3919192), code a23613be3d. Metric: door-to-door delay (s), incl. origin queue.

## Tool checks

| q | O median | NC median | rel (NC-O)/NC | CI diff (s) | T0 |
|---|---|---|---|---|---|
| 1600 | 106.2 | 276.3 | 54.6 % | [23.5, 242.1] | PASS |
| 2000 | 359.2 | 483.4 | 25.1 % | [5.7, 215.4] | PASS |

T1 teleport runs 0/90 (PASS); T3 PASS {'O': True, 'NC': True, 'NV': True, 'FX': True, 'RF': True}

## Tuning

FX rate per q: {'1600': 1700.0, '2000': 1700.0} (grid 600-2600, 19 rates; at an edge: none); RF ratio per q: {'1600': 2.0728, '2000': 2.056}

- RF fill q=1600 (tuning seeds, A3): RMSE 11.13 vs SD of the true edge-4 count 8.29, corr(edge 3, edge 4) -0.18: no better than a constant (RF uninformative on BN4)
- RF fill q=2000 (tuning seeds, A3): RMSE 11.98 vs SD of the true edge-4 count 8.79, corr(edge 3, edge 4) -0.16: no better than a constant (RF uninformative on BN4)

## Headroom HF_f = (f - O) / f, % [95 % CI] (Rule 5; Addendum A2, A5)

A cell passes only if HF >= 10 % with CI lower bound > 0 against every fallback (FX, RF, HL), with and without seeds that have an invalid O/FX/RF/HL run. 'Rule 5 best' = best of FX, RF by median.

| cell | n | O | FX | RF | HL | Rule 5 best | binding | inv seeds | pass all | pass valid | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stuck_off_q1600 | 50 | 106.1 | -49.0 [-76.5, 2.9] | 17.9 [4.0, 36.5] | -64.0 [-93.7, -1.1] | FX fail | HL | 0 | no | no | no |
| stuck_off_q2000 | 50 | 377.0 | -49.5 [-118.8, -18.2] | 5.2 [-2.4, 19.5] | -64.2 [-138.5, -22.2] | FX fail | HL | 0 | no | no | no |
| stuck_on_q1600 | 50 | 106.1 | -49.0 [-76.5, 2.9] | 17.9 [4.0, 36.5] | -64.0 [-93.7, -1.1] | FX fail | HL | 0 | no | no | no |
| stuck_on_q2000 | 50 | 377.0 | -49.5 [-118.8, -18.2] | 5.2 [-2.4, 19.5] | -64.2 [-138.5, -22.2] | FX fail | HL | 0 | no | no | no |
| noisy_q1600 | 50 | 106.1 | -49.0 [-76.5, 2.9] | 17.9 [4.0, 36.5] | -64.0 [-93.7, -1.1] | FX fail | HL | 0 | no | no | no |
| noisy_q2000 | 50 | 377.0 | -49.5 [-118.8, -18.2] | 5.2 [-2.4, 19.5] | -64.2 [-138.5, -22.2] | FX fail | HL | 0 | no | no | no |
| dropout_q1600 | 50 | 106.1 | -49.0 [-76.5, 2.9] | 17.9 [4.0, 36.5] | -64.0 [-93.7, -1.1] | FX fail | HL | 0 | no | no | no |
| dropout_q2000 | 50 | 377.0 | -49.5 [-118.8, -18.2] | 5.2 [-2.4, 19.5] | -64.2 [-138.5, -22.2] | FX fail | HL | 0 | no | no | no |

Under perfect detection O, FX, RF and HL do not depend on the fault type: the 4 fault cells of a demand share these runs, so the decision has 2 independent cells (one per demand); only NV differs.

## Operating map (median delay s / served veh/h / TTT ctrl veh h; invalid runs; HL = NV-dropout runs)

| cell | O | FX | RF | NV | NC | HL |
|---|---|---|---|---|---|---|
| stuck_off_q1600 | 106.1 / 1224 / 12.3 | 54.7 / 1432 / 10.6 | 159.8 / 1160 / 16.2 | 162.2 / 1160 / 15.0 | 224.7 / 1058 / 18.2 | 53.0 / 1414 / 10.3 |
| stuck_off_q2000 | 377.0 / 1112 / 27.8 | 143.0 / 1582 / 20.7 | 348.0 / 1146 / 29.4 | 399.2 / 1104 / 29.5 | 494.0 / 968 / 35.2 | 132.1 / 1574 / 20.0 |
| stuck_on_q1600 | 106.1 / 1224 / 12.3 | 54.7 / 1432 / 10.6 | 159.8 / 1160 / 16.2 | 725.4 / 412 / 35.7 | 224.7 / 1058 / 18.2 | 53.0 / 1414 / 10.3 |
| stuck_on_q2000 | 377.0 / 1112 / 27.8 | 143.0 / 1582 / 20.7 | 348.0 / 1146 / 29.4 | 932.0 / 452 / 48.2 | 494.0 / 968 / 35.2 | 132.1 / 1574 / 20.0 |
| noisy_q1600 | 106.1 / 1224 / 12.3 | 54.7 / 1432 / 10.6 | 159.8 / 1160 / 16.2 | 139.1 / 1182 / 12.9 | 224.7 / 1058 / 18.2 | 53.0 / 1414 / 10.3 |
| noisy_q2000 | 377.0 / 1112 / 27.8 | 143.0 / 1582 / 20.7 | 348.0 / 1146 / 29.4 | 358.8 / 1116 / 29.8 | 494.0 / 968 / 35.2 | 132.1 / 1574 / 20.0 |
| dropout_q1600 | 106.1 / 1224 / 12.3 | 54.7 / 1432 / 10.6 | 159.8 / 1160 / 16.2 | 53.0 / 1414 / 10.3 | 224.7 / 1058 / 18.2 | 53.0 / 1414 / 10.3 |
| dropout_q2000 | 377.0 / 1112 / 27.8 | 143.0 / 1582 / 20.7 | 348.0 / 1146 / 29.4 | 132.1 / 1574 / 20.0 | 494.0 / 968 / 35.2 | 132.1 / 1574 / 20.0 |
