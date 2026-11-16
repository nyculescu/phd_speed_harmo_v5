> **V100 bug re-run** of screen D1: meter signal d2 -> continuous (meter phase recomputed with the current cycle on every rate change (greens skipped, reds up to 322 s); fixed by the continuous signal rule (v5b/d1/meter_signal.py)). Same seeds, arms, grids, tuning and decision rules. Original result `/home/catalin/work/phd/v5b1_runs/screen_d1/v89/result.json` (code a23613be3d, decision STOP). Report both outcomes.

# Screen D1 result: **STOP**

Page `docs/research/protocols/screen_D1_detector_faults.md` (sha256 1991f3919192), code 85f7d34da9. Metric: door-to-door delay (s), incl. origin queue.

## Tool checks

| q | O median | NC median | rel (NC-O)/NC | CI diff (s) | T0 |
|---|---|---|---|---|---|
| 1600 | 72.5 | 276.3 | 36.8 % | [27.5, 247.3] | PASS |
| 2000 | 307.2 | 483.4 | 42.9 % | [46.6, 258.5] | PASS |

T1 teleport runs 0/90 (PASS); T3 PASS {'O': True, 'NC': True, 'NV': True, 'FX': True, 'RF': True}

## Tuning

FX rate per q: {'1600': 1800.0, '2000': 1800.0} (grid 600-2600, 19 rates; at an edge: none); RF ratio per q: {'1600': 1.6989, '2000': 1.6342}

- RF fill q=1600 (tuning seeds, A3): RMSE 8.47 vs SD of the true edge-4 count 6.79, corr(edge 3, edge 4) -0.07: no better than a constant (RF uninformative on BN4)
- RF fill q=2000 (tuning seeds, A3): RMSE 9.47 vs SD of the true edge-4 count 7.12, corr(edge 3, edge 4) -0.21: no better than a constant (RF uninformative on BN4)

## Headroom HF_f = (f - O) / f, % [95 % CI] (Rule 5; Addendum A2, A5)

A cell passes only if HF >= 10 % with CI lower bound > 0 against every fallback (FX, RF, HL), with and without seeds that have an invalid O/FX/RF/HL run. 'Rule 5 best' = best of FX, RF by median.

| cell | n | O | FX | RF | HL | Rule 5 best | binding | inv seeds | pass all | pass valid | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stuck_off_q1600 | 50 | 72.4 | -10.1 [-54.4, 8.6] | 5.3 [-11.1, 22.7] | -21.3 [-47.3, 4.2] | FX fail | FX | 0 | no | no | no |
| stuck_off_q2000 | 50 | 246.0 | -7.4 [-34.7, 6.6] | -2.0 [-23.3, 12.3] | -10.3 [-62.2, 2.5] | FX fail | HL | 0 | no | no | no |
| stuck_on_q1600 | 50 | 72.4 | -10.1 [-54.4, 8.6] | 5.3 [-11.1, 22.7] | -21.3 [-47.3, 4.2] | FX fail | FX | 0 | no | no | no |
| stuck_on_q2000 | 50 | 246.0 | -7.4 [-34.7, 6.6] | -2.0 [-23.3, 12.3] | -10.3 [-62.2, 2.5] | FX fail | HL | 0 | no | no | no |
| noisy_q1600 | 50 | 72.4 | -10.1 [-54.4, 8.6] | 5.3 [-11.1, 22.7] | -21.3 [-47.3, 4.2] | FX fail | FX | 0 | no | no | no |
| noisy_q2000 | 50 | 246.0 | -7.4 [-34.7, 6.6] | -2.0 [-23.3, 12.3] | -10.3 [-62.2, 2.5] | FX fail | HL | 0 | no | no | no |
| dropout_q1600 | 50 | 72.4 | -10.1 [-54.4, 8.6] | 5.3 [-11.1, 22.7] | -21.3 [-47.3, 4.2] | FX fail | FX | 0 | no | no | no |
| dropout_q2000 | 50 | 246.0 | -7.4 [-34.7, 6.6] | -2.0 [-23.3, 12.3] | -10.3 [-62.2, 2.5] | FX fail | HL | 0 | no | no | no |

Under perfect detection O, FX, RF and HL do not depend on the fault type: the 4 fault cells of a demand share these runs, so the decision has 2 independent cells (one per demand); only NV differs.

## Operating map (median delay s / served veh/h / TTT ctrl veh h; invalid runs; HL = NV-dropout runs)

| cell | O | FX | RF | NV | NC | HL |
|---|---|---|---|---|---|---|
| stuck_off_q1600 | 72.4 / 1356 / 10.3 | 46.3 / 1452 / 9.8 | 86.6 / 1362 / 12.4 | 165.7 / 1152 / 14.9 | 224.7 / 1058 / 18.2 | 50.5 / 1438 / 10.1 |
| stuck_off_q2000 | 246.0 / 1326 / 22.0 | 128.3 / 1596 / 18.9 | 229.6 / 1384 / 24.2 | 358.1 / 1136 / 28.0 | 494.0 / 968 / 35.2 | 131.9 / 1584 / 19.7 |
| stuck_on_q1600 | 72.4 / 1356 / 10.3 | 46.3 / 1452 / 9.8 | 86.6 / 1362 / 12.4 | 750.7 / 404 / 35.8 | 224.7 / 1058 / 18.2 | 50.5 / 1438 / 10.1 |
| stuck_on_q2000 | 246.0 / 1326 / 22.0 | 128.3 / 1596 / 18.9 | 229.6 / 1384 / 24.2 | 942.1 / 440 / 48.3 | 494.0 / 968 / 35.2 | 131.9 / 1584 / 19.7 |
| noisy_q1600 | 72.4 / 1356 / 10.3 | 46.3 / 1452 / 9.8 | 86.6 / 1362 / 12.4 | 98.1 / 1324 / 11.6 | 224.7 / 1058 / 18.2 | 50.5 / 1438 / 10.1 |
| noisy_q2000 | 246.0 / 1326 / 22.0 | 128.3 / 1596 / 18.9 | 229.6 / 1384 / 24.2 | 193.5 / 1402 / 21.7 | 494.0 / 968 / 35.2 | 131.9 / 1584 / 19.7 |
| dropout_q1600 | 72.4 / 1356 / 10.3 | 46.3 / 1452 / 9.8 | 86.6 / 1362 / 12.4 | 50.5 / 1438 / 10.1 | 224.7 / 1058 / 18.2 | 50.5 / 1438 / 10.1 |
| dropout_q2000 | 246.0 / 1326 / 22.0 | 128.3 / 1596 / 18.9 | 229.6 / 1384 / 24.2 | 131.9 / 1584 / 19.7 | 494.0 / 968 / 35.2 | 131.9 / 1584 / 19.7 |
