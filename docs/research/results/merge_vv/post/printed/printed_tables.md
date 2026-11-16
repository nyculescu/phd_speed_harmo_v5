# Merge V&V printed items (V2, V3a, V3b): post hoc assembly

Plan: merge_vv.md v1.1 (V532) §2, 'Printed, never deciding' and V2's missed share. Nothing here decides anything. Edges use C-D5 (c1_confirm.md §1): per learner the median over seeds of −(v3w − opponent)/median(opponent) × 100, mean of the 5 learners, joint seed resamples B = 20,000 (rng 20261108), **95 % percentile intervals** (the reader's printed level). Positive = v3w has less; for served flow (`passed`) positive = v3w serves more.

**Sources.** [v3] = `vv_remote/vv_screen/v3.json` (committed reader `read_vv.py` at 6e96988). [rows] = recomputed by `printed.py` in this folder from `vv_screen/s6_rows.jsonl` with an own implementation (does not import the reader). [smoke], [ident], [v1], [status] = the files of those names. Every [v3] number listed below was recomputed from [rows]: 752 numbers compared, largest absolute difference 0.0, so [v3] and [rows] agree exactly (`compare_v3.tsv`). Jams are the exception: [v3] only, not recomputed (they need read6's space-time reading of the `st/` side files).

Rows: 8640 (9 arms × 480 seeds 7,492,000-479 × 2 lengths), 0 missing, 0 dropped ([v3] `dropped` empty, `drops.json` empty); CPU ['AMD EPYC 7B13 64-Core Processor']; [v3] `bugs` all empty (meter, x_out, no_instruments, geometry, unpaired_seeds); [v3] `void` empty.

## 1. Smoke, identity and V1 automatic checks

| check | value | source |
|---|---|---|
| smoke overall | pass = True | [smoke] |
| missing / replay differs / side files differ / twin differs | 0 / 0 / 0 / 0 | [smoke] |
| T0 lane-length differences outside 3a/4a | 0 | [smoke] |
| meter bugs (whole-second = ttc_net, half = ttc_half) | 0 | [smoke] |
| remapped x outside the 300-m training range (x_out) | 0 in all 8 controlled L600 runs of seed 7,493,010 | [smoke] obs |
| column-15 cap share, L600 seed 7,493,010 | 0.0 for all 8 controlled arms | [smoke] obs |
| demand differs between lengths | 0 | [smoke] |
| wall time per run, s (300 m / 600 m) | 73.3-96.2 / 74.6-87.8 | [smoke] |
| identity replay (9 arms, stored E30 seeds 7,489,160-161): rule / learner / diagnostic differences, missing | 0 / 0 / 0, 0; traced replays the same: 0 / 0 / 0, 0 | [ident] |
| identity CPU = CF CPU | True (AMD EPYC 7B13 64-Core Processor); learner mismatch disclosed = False; tracer_bug = False; action = go | [ident] |
| V1 outcome | CHECKS PASS; visual check pending | [v1], [status] |
| V1 wiring / definition / twin failures | 0 / 0 / 0 | [v1] |
| V1 twins compared (traced vs untraced, smoke seeds) | 12, all equal | [v1] |
| V1 traced runs classified | 18 (12 smoke-seed traces, 6 stored-E30-seed traces) | [v1] |
| V1 visual sample drawn | 40 samples (rng 20261115); visual check still pending (not done here) | [v1] |

Smoke lane-end standing printed for the author (plan §4), one seed (7,493,010) [smoke]:

| run | `end_stop` merge 1 (veh-s) | `end_stop2` merge 2 (veh-s) | vehicles stood at 3a / 4a end |
|---|---|---|---|
| L300\|lr400_16_1 7493010 | 431 | 1062 | 12 / 39 |
| L300\|nc 7493010 | 27 | 193 | 6 / 11 |
| L600\|lr400_16_1 7493010 | 0 | 0 | 0 / 0 |
| L600\|nc 7493010 | 433 | 287 | 20 / 12 |

V1 per traced run (printed by the plan: distinct encounters, distinct vehicles standing per lane end; next-lane share = leader on the next lane of the route):

| run (cell\|arm seed) | counted samples | distinct encounters | next-lane share % | stood at 3a end (vehicles) | stood at 4a end (vehicles) | edge-1 samples |
|---|---|---|---|---|---|---|
| L600\|nc 7493000 | 655 | 291 | 2.3 | 1 | 40 | 3 |
| L600\|nc 7493001 | 453 | 203 | 0.0 | 11 | 14 | 2 |
| L600\|lr400_16_1 7493000 | 466 | 237 | 2.1 | 0 | 17 | 1 |
| L600\|w1u500 7493000 | 43 | 31 | 7.0 | 1 | 0 | 12 |
| L300\|lr400_16_1 7493000 | 417 | 211 | 5.0 | 9 | 1 | 2 |
| L300\|nc 7493000 | 1249 | 556 | 8.7 | 11 | 33 | 0 |
| L600\|lr400_16_1 7493001 | 41 | 32 | 0.0 | 0 | 2 | 1 |
| L300\|w1u500 7493000 | 752 | 341 | 5.2 | 19 | 17 | 8 |
| L600\|w1u500 7493001 | 178 | 93 | 2.2 | 2 | 12 | 12 |
| L300\|nc 7493001 | 1349 | 598 | 11.0 | 22 | 18 | 0 |
| L300\|w1u500 7493001 | 559 | 262 | 7.9 | 4 | 14 | 27 |
| L300\|lr400_16_1 7493001 | 1545 | 711 | 5.8 | 17 | 30 | 0 |
| E30\|nc 7489160 | 1379 | 558 | 8.0 | 2 | 27 | 0 |
| E30\|nc 7489161 | 1204 | 506 | 8.1 | 16 | 20 | 0 |
| E30\|lr400_16_1 7489161 | 1434 | 624 | 3.2 | 21 | 20 | 0 |
| E30\|w1u500 7489160 | 875 | 421 | 8.5 | 3 | 34 | 16 |
| E30\|lr400_16_1 7489160 | 1780 | 839 | 8.8 | 2 | 59 | 6 |
| E30\|w1u500 7489161 | 1305 | 597 | 7.8 | 19 | 22 | 18 |

V1 classification pooled over the 18 traced runs (15684 counted samples; pooling across arms and lengths is post hoc and descriptive only) [v1]:

| dimension | shares |
|---|---|
| follower lane | acc/ramp 57.6 %, main 42.4 % |
| leader relation | same lane 93.2 %, next lane 6.8 % |
| leader standing | - 93.4 %, leader standing 6.6 % |
| merged 5 s | - 96.6 %, merged 5 s 3.4 % |
| follower type | alks 60.8 %, car 32.3 %, truck 6.9 % |
| speed band | lo 36.0 %, mid 35.5 %, hi 28.5 % |
| period | rest 84.5 %, hold 5.9 %, before 4.5 %, after 4.3 %, taper 0.8 % |
| road group | 4a 60.2 %, 3a 20.9 %, 3 8.0 %, ramp2 6.9 %, junction 1.4 %, 2 1.3 %, 1 0.7 %, ramp1 0.7 % |

## 2. V2 resolution (300-m runs)

| opponent | 0.1-s edge | 1-Hz edge | difference (points) | within ±3 |
|---|---|---|---|---|
| lr400_16_1 | +16.2 [+12.9, +19.7] | +16.0 [+12.6, +19.8] | +0.23 [-0.41, +0.60] | True |
| grid_lr400_13_1 | +21.6 [+16.8, +24.8] | +21.7 [+16.8, +24.7] | -0.05 [-0.56, +0.47] | True |

Outcome [v3]: **MET**. Meter equality in every 300-m run [rows]: whole-second count ≠ `ttc_net` in 0 rows, half-second ≠ `ttc_half` in 0; 300-m rows without the meter 0, 600-m rows with it 0.

Missed share per arm = (0.1-s time − 1-Hz count × 1 s) / 0.1-s time. [v3] prints the median over seeds; the pooled ratio and the 10th-90th percentiles are [rows], post hoc.

| arm | missed share, median % [v3] | pooled % [rows] | 10th-90th pct of per-run share % | Σ 0.1-s time (veh-s) | Σ 1-Hz count |
|---|---|---|---|---|---|
| w0u250 | -0.081 | -0.082 | -1.66 to +1.24 | 497391 | 497798 |
| w1u500 | -0.128 | -0.140 | -1.49 to +1.18 | 525528 | 526266 |
| w2u250 | -0.003 | -0.028 | -1.37 to +1.55 | 533443 | 533591 |
| w3u500 | -0.100 | -0.153 | -1.46 to +1.21 | 518872 | 519665 |
| w4u500 | -0.205 | -0.181 | -1.50 to +1.08 | 525871 | 526824 |
| lr400_16_1 | -0.110 | -0.103 | -1.27 to +1.19 | 635153 | 635808 |
| grid_lr400_13_1 | -0.093 | -0.072 | -1.35 to +1.25 | 664630 | 665107 |
| p333 | -0.068 | -0.064 | -1.36 to +1.05 | 788571 | 789075 |
| nc | -0.007 | -0.011 | -1.10 to +1.09 | 661376 | 661450 |

## 3. Deciding readings, for context only [v3]

| reading | edge % [interval] | rule | outcome |
|---|---|---|---|
| V3a replication (`ttc_net`, 97.5 %) | +16.0 [+12.2, +20.3] | lr400_16_1 | REPLICATED |
| V3a replication (`ttc_net`, 97.5 %) | +21.7 [+16.2, +25.2] | grid_lr400_13_1 | REPLICATED |
| V3a main-lane (97.5 %) | +10.6 [+6.6, +14.5] | lr400_16_1 | also shown on main-lane samples |
| V3a main-lane (97.5 %) | +22.3 [+17.9, +26.4] | grid_lr400_13_1 | also shown on main-lane samples |
| V3b 600 m (98.75 % for WORSE) | -21.0 [-29.0, -11.4] | lr400_16_1 | WORSE |
| V3b 600 m (98.75 % for WORSE) | -6.6 [-16.3, +4.0] | grid_lr400_13_1 | WORSE |
| V3b change 600 − 300 (95 %) | -37.0 [-44.4, -28.9] | lr400_16_1 | depends on length |
| V3b change 600 − 300 (95 %) | -28.3 [-36.2, -19.1] | grid_lr400_13_1 | depends on length |

## 4. Close-following edges by road group, per merge and by period

Edges, % [95 %], [v3] = [rows]. Merge area = 3a, r, rj, 4a, r2, rj2; merge 1 = 3a + ramp 1; merge 2 = 4a + ramp 2; rest = all other roads incl. junctions. Periods are the row's `ttc3_p_*` keys; they equal the sums of the `m_road_ttc3` period keys in every row (0 mismatches) and sum to `ttc_net` (0 mismatches) [rows]. Road keys that ever carry a sample: 1, 2, 3, 3a, 4a, junction, ramp1, ramp2 (none on edges 4 or 5).

| measure | lr400_16_1 300 m | lr400_16_1 600 m | grid_lr400_13_1 300 m | grid_lr400_13_1 600 m |
|---|---|---|---|---|
| merge area | +18.1 [+14.6, +21.0] | +8.8 [+2.2, +15.7] | +24.2 [+20.2, +27.6] | +18.9 [+11.6, +26.2] |
| merge 1 | +9.4 [+5.5, +14.2] | -0.7 [-8.0, +4.0] | +16.2 [+11.6, +21.4] | +4.8 [+0.0, +11.4] |
| merge 2 | +18.5 [+15.0, +22.2] | +10.9 [+3.0, +23.4] | +27.2 [+22.5, +31.7] | +18.9 [+10.3, +30.6] |
| edge 1 | -1110.0 [-1145.0, -1080.0] | -733.3 [-753.3, -706.7] | -730.0 [-760.0, -706.7] | -726.7 [-750.0, -700.0] |
| rest | +15.3 [+9.4, +22.8] | +0.0 [+0.0, +0.0] † | +10.9 [+5.5, +18.8] | +0.0 [+0.0, +0.0] † |
| all but edge 1 | +17.8 [+14.4, +21.5] | +8.1 [+1.9, +15.1] | +23.3 [+18.5, +26.4] | +18.4 [+11.2, +25.6] |
| all (`ttc_net`) | +16.0 [+12.6, +19.8] | -21.0 [-27.3, -13.6] | +21.7 [+16.8, +24.7] | -6.6 [-14.5, +1.8] |
| period before | +5.5 [+1.4, +12.4] | +0.0 [+0.0, +0.0] | +10.6 [+4.8, +18.5] | +0.0 [+0.0, +0.0] |
| period taper | +0.0 [+0.0, +0.0] † | +0.0 [+0.0, +0.0] † | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] † |
| period hold | -63.4 [-71.2, -54.1] | -565.0 [-580.0, -540.0] | -61.9 [-70.3, -50.9] | -550.0 [-572.5, -525.0] |
| period after | -14.0 [-18.3, -9.3] | -28.6 [-40.0, -14.3] | -3.2 [-6.9, +0.8] | +0.0 [-10.0, +5.0] |
| period rest | +19.9 [+15.7, +23.8] | +9.3 [+2.8, +17.6] | +23.9 [+18.9, +27.8] | +16.3 [+8.6, +27.0] |

† the opponent's median is 0, so the C-D5 denominator is 1e-9: the cell is 0 only because most paired differences are exactly 0; it is not a percentage.

Medians per arm, samples per run (opponent: its median, the C-D5 denominator; v3w: mean of the 5 learners' medians) [rows]:

| measure | v3w 300 m | v3w 600 m | lr400_16_1 300 m | lr400_16_1 600 m | grid_lr400_13_1 300 m | grid_lr400_13_1 600 m | p333 300 m | p333 600 m | nc 300 m | nc 600 m |
|---|---|---|---|---|---|---|---|---|---|---|
| merge area | 907.5 | 70.4 | 1139.0 | 72.0 | 1172.0 | 85.0 | 1321.5 | 80.5 | 1149.5 | 599.5 |
| merge 1 | 240.4 | 17.9 | 280.0 | 15.0 | 294.5 | 21.0 | 296.0 | 20.0 | 317.5 | 66.0 |
| merge 2 | 634.4 | 28.0 | 856.5 | 26.5 | 845.0 | 36.0 | 1054.0 | 32.5 | 793.5 | 488.5 |
| edge 1 | 25.2 | 25.0 | 2.0 | 3.0 | 3.0 | 3.0 | 26.0 | 27.0 | 1.0 | 2.0 |
| rest | 147.5 | 0.0 | 211.0 | 0.0 | 197.5 | 0.0 | 267.5 | 0.0 | 198.0 | 57.0 |
| all but edge 1 | 1055.4 | 70.8 | 1373.5 | 72.0 | 1388.5 | 85.0 | 1640.0 | 82.5 | 1338.0 | 671.0 |
| all (`ttc_net`) | 1082.1 | 98.3 | 1375.5 | 76.5 | 1389.5 | 87.5 | 1671.0 | 112.5 | 1340.0 | 673.5 |
| period before | 27.0 | 1.0 | 29.0 | 1.0 | 33.0 | 1.0 | 33.5 | 1.0 | 34.5 | 0.0 |
| period taper | 0.6 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 | 4.0 | 0.0 |
| period hold | 53.0 | 27.2 | 32.0 | 4.0 | 32.0 | 4.0 | 61.0 | 29.0 | 68.0 | 3.0 |
| period after | 104.2 | 5.2 | 89.5 | 3.5 | 99.0 | 4.0 | 115.5 | 6.0 | 75.0 | 4.0 |
| period rest | 825.1 | 50.4 | 1124.0 | 49.5 | 1141.5 | 63.0 | 1335.5 | 54.5 | 1054.5 | 653.0 |

Largest remaining deficit at 600 m, samples per run (median over seeds of v3w's learner mean − rule) [v3] = [rows]: lr400_16_1: merge area +5.8, edge 1 +22.4, rest +0.1 → g_edge1; grid_lr400_13_1: merge area -6.1, edge 1 +22.6, rest +0.2 → g_edge1.

## 5. Delay, TTT, served flow, braking and stricter close-following measures

TTC below 3 s and braking at 3 m/s² or harder are terms of v3w's training reward; TTC below 2 s and 1.5 s are stricter versions of the rewarded event and `b45_step` of the rewarded braking; only DRAC (`sev3`) is outside the reward.

TTT is present: `N` is the per-step count of vehicles in the network plus the insertion queue, summed over the fixed window (vehicle-seconds; `b_env.py:440-442`; `plant_sweep.py:30` names it `ttt`). `all_delay` = `N` − distance / (100 km/h), insertion queue and unfinished vehicles included (`plant_sweep.py:432`). At 600 m the network holds 600 m more lane, so TTT and delay are compared within a length only.

| measure | lr400_16_1 300 m | lr400_16_1 600 m | grid_lr400_13_1 300 m | grid_lr400_13_1 600 m |
|---|---|---|---|---|
| delay (`all_delay`) | +2.3 [+1.2, +3.1] | +0.7 [+0.4, +1.0] | +0.9 [+0.1, +1.7] | +0.2 [-0.1, +0.5] |
| TTT (`N`) | +0.5 [+0.2, +0.7] | +0.2 [+0.1, +0.2] | +0.2 [-0.0, +0.4] | +0.0 [-0.0, +0.1] |
| served flow (`passed`, + = v3w more) | +0.6 [+0.4, +0.8] | +0.0 [+0.0, +0.0] | +0.2 [+0.1, +0.4] | +0.0 [-0.0, +0.0] |
| `b45_step` | +5.3 [+2.7, +7.5] | -5.1 [-7.1, -3.2] | +5.3 [+2.6, +7.8] | -5.3 [-7.4, -3.1] |
| `ttc2` | +35.3 [+31.6, +38.5] | +26.0 [+16.0, +39.0] | +42.7 [+38.9, +47.1] | +30.0 [+18.0, +40.0] |
| `ttc15` | +24.7 [+20.0, +28.2] | +0.0 [+0.0, +40.0] | +38.4 [+34.4, +42.6] | +10.0 [+0.0, +40.0] |
| `sev3` (DRAC) | +21.8 [+18.3, +25.6] | +0.0 [+0.0, +0.0] | +24.2 [+19.6, +29.1] | +0.0 [+0.0, +20.0] |
| distinct encounters (`vv_enc`) | +12.1 [+8.5, +15.4] | -34.8 [-40.5, -26.8] | +17.7 [+13.6, +21.7] | -20.8 [-28.2, -12.7] |
| main-lane count (`vv_ttc3_main`) [rows] only | +10.6 [+7.1, +14.0] | -31.0 [-37.8, -23.3] | +22.3 [+18.4, +25.9] | -7.5 [-14.6, +1.3] |

† the opponent's median is 0, so the C-D5 denominator is 1e-9: the cell is 0 only because most paired differences are exactly 0; it is not a percentage.

Medians per arm [rows]:

| measure | v3w 300 m | v3w 600 m | lr400_16_1 300 m | lr400_16_1 600 m | grid_lr400_13_1 300 m | grid_lr400_13_1 600 m | p333 300 m | p333 600 m | nc 300 m | nc 600 m |
|---|---|---|---|---|---|---|---|---|---|---|
| delay (`all_delay`) | 168797.9 | 159530.1 | 173370.3 | 160421.4 | 169778.6 | 159960.0 | 169136.1 | 158217.2 | 238730.9 | 234307.0 |
| TTT (`N`) | 617222.7 | 652898.5 | 621051.0 | 654526.0 | 617855.5 | 654913.5 | 617172.5 | 651967.0 | 680156.0 | 718863.0 |
| served flow (`passed`, + = v3w more) | 2185.4 | 2195.9 | 2169.0 | 2191.0 | 2175.5 | 2192.0 | 2181.0 | 2196.0 | 2104.0 | 2108.0 |
| `b45_step` | 416.4 | 159.3 | 447.5 | 148.1 | 441.1 | 146.5 | 494.5 | 157.1 | 428.6 | 240.1 |
| `ttc2` | 169.9 | 6.8 | 279.5 | 10.0 | 309.0 | 10.0 | 429.0 | 10.0 | 207.0 | 112.5 |
| `ttc15` | 37.0 | 0.8 | 51.0 | 2.0 | 62.0 | 2.0 | 91.5 | 1.0 | 51.5 | 33.0 |
| `sev3` (DRAC) | 53.5 | 0.6 | 71.0 | 1.0 | 74.0 | 1.0 | 92.0 | 1.0 | 82.0 | 28.0 |
| distinct encounters (`vv_enc`) | 510.4 | 63.0 | 614.5 | 44.0 | 632.0 | 49.0 | 759.5 | 68.0 | 570.5 | 286.5 |
| main-lane count (`vv_ttc3_main`) [rows] only | 534.1 | 87.3 | 625.0 | 60.0 | 699.5 | 76.0 | 976.0 | 102.0 | 384.5 | 160.0 |

Runs (of 480) with a zero count, per arm [rows]. These counters are written to a row only once they count something, so an absent key is 0; the reader reads it as 0 too (`r.get(k, 0.0)`), and no row stores an explicit 0 for them. A median of 0 for the opponent makes the C-D5 denominator 1e-9 (`max(median, 1e-9)`), so such an edge is not a percentage at all.

| arm | ttc2 300 m | ttc2 600 m | ttc15 300 m | ttc15 600 m | sev3 300 m | sev3 600 m | vv_enc 300 m | vv_enc 600 m |
|---|---|---|---|---|---|---|---|---|
| w0u250 | 0 | 74 | 3 | 237 | 5 | 258 | 0 | 0 |
| w1u500 | 0 | 51 | 0 | 221 | 1 | 234 | 0 | 0 |
| w2u250 | 0 | 63 | 2 | 223 | 5 | 228 | 0 | 0 |
| w3u500 | 0 | 61 | 2 | 209 | 0 | 231 | 0 | 0 |
| w4u500 | 0 | 71 | 3 | 242 | 2 | 245 | 0 | 0 |
| lr400_16_1 | 0 | 66 | 1 | 190 | 1 | 211 | 0 | 0 |
| grid_lr400_13_1 | 0 | 55 | 0 | 192 | 1 | 200 | 0 | 0 |
| p333 | 0 | 54 | 1 | 191 | 1 | 205 | 0 | 0 |
| nc | 0 | 9 | 0 | 15 | 0 | 14 | 0 | 1 |

## 6. Collisions and jams

| arm | collisions 300 m (sum over 480 runs) [v3]=[rows] | collisions 600 m | stuck vehicles 300 m [rows, post hoc] | stuck 600 m | teleports 300 m [rows, post hoc] | teleports 600 m |
|---|---|---|---|---|---|---|
| w0u250 | 0 (0 runs) | 0 (0 runs) | 0 | 0 | 0 | 0 |
| w1u500 | 0 (0 runs) | 0 (0 runs) | 0 | 0 | 0 | 0 |
| w2u250 | 0 (0 runs) | 0 (0 runs) | 0 | 0 | 0 | 0 |
| w3u500 | 0 (0 runs) | 0 (0 runs) | 0 | 1 | 0 | 0 |
| w4u500 | 0 (0 runs) | 0 (0 runs) | 1 | 0 | 0 | 0 |
| lr400_16_1 | 1 (1 runs) | 0 (0 runs) | 6 | 0 | 0 | 0 |
| grid_lr400_13_1 | 2 (2 runs) | 1 (1 runs) | 1 | 0 | 0 | 0 |
| p333 | 1 (1 runs) | 0 (0 runs) | 2 | 1 | 0 | 0 |
| nc | 0 (0 runs) | 1 (1 runs) | 0 | 0 | 0 | 0 |

Jam edges [v3] only (not recomputed): % [95 %], + = v3w fewer jams.

| opponent | 300 m | 600 m |
|---|---|---|
| lr400_16_1 | +0.0 [+0.0, +5.0] | +0.0 [+0.0, +0.0] |
| grid_lr400_13_1 | +0.0 [-1.2, +1.2] | +0.0 [+0.0, +0.0] |
| p333 | +0.0 [-10.0, +0.0] | +0.0 [+0.0, +0.0] |
| nc | +22.0 [+20.0, +26.0] | +42.9 [+37.1, +42.9] |

## 7. Lane-end standing per arm and merge

`end_stop` (3a end, merge 1) and `end_stop2` (4a end, merge 2): vehicle-seconds below 1 m/s in the last 30 m; distinct vehicles = `vv_stand_n`. `vv_stand_s` equals `end_stop`/`end_stop2` in every row (0 mismatches) [rows]. Median (mean) over 480 seeds; 'zero' = share of runs with no standing vehicle. Vehicle medians [v3] `standing_vehicles` = [rows].

| arm | 300 m merge 1 veh-s | 300 m merge 1 vehicles | 300 m merge 2 veh-s | 300 m merge 2 vehicles | 600 m merge 1 veh-s | 600 m merge 1 vehicles | 600 m merge 2 veh-s | 600 m merge 2 vehicles |
|---|---|---|---|---|---|---|---|---|
| w0u250 | 152 (212) | 8 (10.3); zero 1 % | 494 (561) | 20 (20.7); zero 0 % | 6 (62) | 1 (2.4); zero 31 % | 21 (153) | 2 (5.2); zero 22 % |
| w1u500 | 128 (199) | 8 (9.9); zero 1 % | 436 (515) | 20 (20.9); zero 0 % | 10 (63) | 1 (2.6); zero 30 % | 32 (177) | 2 (6.0); zero 18 % |
| w2u250 | 192 (261) | 10 (11.3); zero 1 % | 513 (562) | 21 (21.0); zero 0 % | 10 (64) | 1 (2.4); zero 30 % | 29 (172) | 2 (5.8); zero 22 % |
| w3u500 | 192 (269) | 11 (11.6); zero 1 % | 453 (507) | 20 (20.7); zero 0 % | 6 (71) | 1 (2.3); zero 35 % | 29 (179) | 2 (6.3); zero 22 % |
| w4u500 | 156 (230) | 9 (10.3); zero 2 % | 482 (555) | 20 (20.7); zero 0 % | 5 (67) | 1 (2.2); zero 36 % | 21 (160) | 1 (5.5); zero 27 % |
| lr400_16_1 | 274 (366) | 12 (13.4); zero 2 % | 900 (905) | 25 (25.6); zero 0 % | 12 (98) | 1 (3.0); zero 35 % | 23 (289) | 2 (7.5); zero 25 % |
| grid_lr400_13_1 | 282 (373) | 12 (13.3); zero 2 % | 844 (894) | 26 (25.9); zero 0 % | 10 (82) | 1 (2.6); zero 31 % | 26 (266) | 1 (7.2); zero 24 % |
| p333 | 232 (315) | 11 (12.2); zero 1 % | 905 (962) | 29 (27.6); zero 0 % | 7 (78) | 1 (2.5); zero 35 % | 22 (233) | 1 (6.0); zero 26 % |
| nc | 226 (276) | 14 (15.3); zero 1 % | 546 (589) | 26 (27.8); zero 0 % | 110 (192) | 7 (9.3); zero 12 % | 412 (430) | 19 (19.4); zero 2 % |

VV-D12 cut = 1 − median(600 m)/median(300 m) of standing vehicle-seconds, 95 % lower bound (v3w = per-seed mean of learners) [v3] = [rows]; 'removed' needs every lower bound of v3w, both rules and no control ≥ 80 %:

| merge | arm | median 300 m | median 600 m | cut % | 95 % lower % |
|---|---|---|---|---|---|
| merge1 | v3w | 204.4 | 32.1 | 84.3 | 81.8 |
| merge1 | lr400_16_1 | 274.0 | 11.5 | 95.8 | 93.8 |
| merge1 | grid_lr400_13_1 | 282.5 | 9.5 | 96.6 | 94.6 |
| merge1 | p333 | 232.0 | 7.0 | 97.0 | 94.2 |
| merge1 | nc | 226.5 | 109.5 | 51.7 | 36.3 |
| merge2 | v3w | 519.4 | 76.7 | 85.2 | 80.3 |
| merge2 | lr400_16_1 | 900.0 | 23.0 | 97.4 | 96.5 |
| merge2 | grid_lr400_13_1 | 843.5 | 26.0 | 96.9 | 95.5 |
| merge2 | p333 | 905.0 | 22.5 | 97.5 | 96.7 |
| merge2 | nc | 546.0 | 412.5 | 24.5 | 15.3 |

Per learner (post hoc, [rows]): cut = 1 − median(600 m)/median(300 m) of each learner's own runs, the form the single-arm rows above use. The v3w row above is the median of the per-seed mean of the 5 learners; with these skewed counts (means far above medians at 600 m) that median sits above every single learner's median, so v3w's 600-m medians (32.1, 76.7) are not comparable with the rules' single-arm medians.

| learner | merge 1 median 300 m | merge 1 median 600 m | merge 1 cut % | merge 2 median 300 m | merge 2 median 600 m | merge 2 cut % |
|---|---|---|---|---|---|---|
| w0u250 | 151.5 | 6.0 | 96.0 | 493.5 | 21.0 | 95.7 |
| w1u500 | 128.0 | 9.5 | 92.6 | 435.5 | 32.0 | 92.7 |
| w2u250 | 191.5 | 10.0 | 94.8 | 513.0 | 29.0 | 94.3 |
| w3u500 | 192.5 | 5.5 | 97.1 | 453.0 | 29.0 | 93.6 |
| w4u500 | 156.0 | 5.0 | 96.8 | 482.0 | 21.0 | 95.6 |

removed [v3]: merge 1 False, merge 2 False (no control's cut is far below 80 %).

## 8. Does any rule beat no control on delay by 10 % at 600 m? (P0 form)

Single arm against no control: median over seeds of −(arm − nc)/median(nc) × 100 on `all_delay`, 95 % percentile interval over seed resamples (B = 20,000, rng 20261108). [v3] prints the point and the lower bound; the upper bound and the learner rows are [rows] (learners post hoc). P0 passes if any rule has a point ≥ 10 % and a lower bound > 0.

| arm | 300 m: % less delay than nc [95 %] | 300 m: median delay arm / nc (veh-s) | 600 m: % less delay than nc [95 %] | 600 m: median delay arm / nc |
|---|---|---|---|---|
| lr400_16_1 | +27.5 [+26.5, +28.4] | 173370 / 238731 | +29.3 [+28.2, +30.0] | 160421 / 234307 |
| grid_lr400_13_1 | +28.3 [+27.3, +29.1] | 169779 / 238731 | +29.3 [+28.5, +30.0] | 159960 / 234307 |
| p333 | +29.1 [+28.2, +29.9] | 169136 / 238731 | +30.3 [+29.6, +31.3] | 158217 / 234307 |
| w0u250 (learner, post hoc) | +29.5 [+28.6, +30.7] | 167021 / 238731 | +30.8 [+29.9, +31.6] | 158659 / 234307 |
| w1u500 (learner, post hoc) | +27.8 [+27.0, +28.7] | 170294 / 238731 | +29.7 [+28.8, +30.3] | 159865 / 234307 |
| w2u250 (learner, post hoc) | +29.0 [+27.9, +30.1] | 169642 / 238731 | +29.6 [+28.8, +30.4] | 159749 / 234307 |
| w3u500 (learner, post hoc) | +28.6 [+27.8, +29.6] | 168987 / 238731 | +29.9 [+29.2, +30.7] | 160349 / 234307 |
| w4u500 (learner, post hoc) | +29.3 [+28.2, +29.9] | 168046 / 238731 | +29.9 [+29.0, +31.0] | 159028 / 234307 |

Any rule passes: 300 m True ([v3] True); 600 m True ([v3] True).

## 9. The reader's other printed opponents: p333 and no control

| measure | p333 300 m | p333 600 m | nc 300 m | nc 600 m |
|---|---|---|---|---|
| merge area | +31.4 [+27.0, +35.8] | +14.7 [+8.1, +22.7] | +22.9 [+20.2, +25.3] | +76.9 [+72.5, +81.2] |
| merge 1 | +14.3 [+9.7, +18.7] | +5.5 [+0.0, +12.5] | +23.9 [+18.4, +29.4] | +55.5 [+41.5, +67.7] |
| merge 2 | +34.8 [+29.3, +39.7] | +9.8 [+2.8, +20.3] | +21.0 [+16.8, +24.4] | +79.3 [+73.8, +83.9] |
| edge 1 | +6.2 [+2.7, +8.1] | +3.0 [+0.4, +5.6] | -2340.0 [-2420.0, -2260.0] | -1150.0 [-1200.0, -1120.0] |
| rest | +36.5 [+23.6, +47.8] | +0.0 [+0.0, +0.0] † | +26.7 [+22.1, +32.2] | +88.9 [+80.0, +98.1] |
| all but edge 1 | +34.2 [+27.8, +38.8] | +14.1 [+7.5, +21.8] | +23.5 [+20.8, +26.0] | +76.7 [+72.3, +81.9] |
| all (`ttc_net`) | +33.8 [+27.4, +38.2] | +11.9 [+6.8, +17.3] | +21.7 [+19.0, +24.2] | +72.7 [+68.4, +77.6] |
| delay (`all_delay`) | -0.4 [-1.1, +0.3] | -0.6 [-0.9, -0.3] | +28.8 [+28.1, +29.6] | +30.0 [+29.2, +30.7] |
| TTT (`N`) | -0.2 [-0.3, +0.0] | -0.1 [-0.2, -0.1] | +9.1 [+8.8, +9.3] | +8.6 [+8.4, +8.9] |
| served flow (`passed`, + = v3w more) | +0.1 [+0.0, +0.2] | +0.0 [-0.0, +0.0] | +3.9 [+3.8, +4.0] | +4.1 [+4.0, +4.2] |
| `b45_step` | +14.4 [+11.7, +17.3] | +1.0 [-0.5, +3.0] | +3.8 [+1.7, +5.6] | +28.8 [+27.0, +30.9] |
| `ttc2` | +59.0 [+51.0, +66.6] | +22.0 [+14.0, +36.0] | +17.2 [+14.7, +19.8] | +80.8 [+76.8, +85.5] |
| `ttc15` | +57.3 [+51.3, +63.9] | +0.0 [+0.0, +60.0] | +29.9 [+26.6, +33.2] | +86.1 [+80.6, +90.6] |
| `sev3` (DRAC) | +39.2 [+33.4, +44.6] | +0.0 [+0.0, +20.0] | +35.7 [+33.4, +38.9] | +81.4 [+75.7, +88.6] |
| distinct encounters (`vv_enc`) | +31.1 [+26.3, +35.9] | +9.7 [+5.0, +14.4] | +14.2 [+11.2, +17.1] | +64.4 [+60.6, +68.4] |

† the opponent's median is 0, so the C-D5 denominator is 1e-9: the cell is 0 only because most paired differences are exactly 0; it is not a percentage.

## 10. Column 15 and position remap at 600 m

| arm | column 15 at cap / decisions [rows] | x outside training range / positions read on 3a, 4a [rows] | c15_cap_share_600 [v3] |
|---|---|---|---|
| w0u250 | 0 / 32149077 | 0 / 6255465 | 0.0 |
| w1u500 | 0 / 32261793 | 0 / 6360161 | 0.0 |
| w2u250 | 0 / 32223850 | 0 / 6319975 | 0.0 |
| w3u500 | 0 / 32253939 | 0 / 6342175 | 0.0 |
| w4u500 | 0 / 32219361 | 0 / 6312619 | 0.0 |
| lr400_16_1 | 0 / 32308737 | 0 / 6389779 | not in [v3] |
| grid_lr400_13_1 | 1566 / 32252311 | 0 / 6340729 | not in [v3] |
| p333 | 2991 / 32141555 | 0 / 6262459 | not in [v3] |

## 11. Spot-checks and notes (post hoc)

**Spot-checks.** All 752 [v3] numbers listed in `compare_v3.tsv` were recomputed from the rows by `printed.py`; every one matches exactly (largest difference 0.0; a NaN on either side would count as a mismatch). Five of them, with a hand check of the arithmetic where it is simple:

| number | [v3] | [rows] | hand check |
|---|---|---|---|
| printed_600 lr400_16_1 g_edge1 pt | −733.3 | −733.3 | rule median 3.0, v3w ≈ 25 samples: −(25 − 3)/3 × 100 ≈ −733 |
| printed_300 grid_lr400_13_1 ttc2 pt | +42.69 | +42.69 | medians 169.9 vs 309.0; per-learner medians of paired % differ from the ratio of medians (+45 %) |
| printed_600 rule_beats_nc_by_10 p333 pt / lo95 | +30.31 / +29.57 | +30.31 / +29.57 | medians 158,217 vs 234,307 veh-s: 32.5 % on the ratio of medians |
| printed_600 lr400_16_1 all_delay pt [lo95, hi95] | +0.66 [+0.39, +0.95] | +0.66 [+0.39, +0.95] | - |
| standing_vehicles L600 nc 4a_0 | 19 | 19 | - |
| v2 missed_share w4u500 | −0.205 % | −0.205 % | - |
| printed_300 collisions grid_lr400_13_1 | 2 | 2 | 2 runs with 1 collision each |
| v3b cut merge1 v3w lo95 | 81.77 % | 81.77 % | - |

**Notes.**

- Edge 1 shows −730 % to −2,340 %: the rules and no control have medians of 1-3 samples per run on edge 1 against about 25 for v3w (and 26-27 for p333), at both lengths. In samples per run the 600-m deficit there is +22.4 (lr400_16_1) and +22.6 (grid_lr400_13_1) [v3]. The plan's pre-stated E30 figures (22-26 against 2-3) recur here.
- At 600 m v3w's total median is 98.3 against 76.5 (lr400_16_1), a gap of about the size of the edge-1 deficit (medians are not additive, so this is an inference). With edge-1 samples left out the 600-m edge is +8.1 [+1.9, +15.1] against lr400_16_1 and +18.4 [+11.2, +25.6] against grid_lr400_13_1 (95 %, printed only). The plan pre-stated that a WORSE carried by edge 1 is not a lane-length effect. V3b's deciding WORSE rests on lr400_16_1 alone (98.75 % upper bound −11.4, null 0.475 % at 20,000 swaps) [v3].
- The 'rest' group at 600 m has median 0 for the rules and p333, so its cells read +0.0 [+0.0, +0.0] (marked †): an artefact of a zero denominator, not a tie. The taper period (a 20-s window) has medians of 0-4 and reads the same way.
- Hold period at 600 m: -565.0 [-580.0, -540.0] against lr400_16_1 (medians 27.2 against 4.0); in the V1 traces every edge-1 sample falls in the hold period (w1u500 93 samples, 86 of them with an ALKS follower; lr400_16_1 10 and no control 5, all car followers) [v1]. Most close-following of every arm falls in the 'rest' period (after the event end + 120 s): v3w's median there is 825 against a median total of 1,082 per run at 300 m.
- `ttc15` and `sev3` at 600 m are 0 in 40-54 % of the controlled arms' runs (and `ttc2` in 11-15 %); opponent medians are 1-2 events, so the percentages move on a coarse lattice and intervals such as [+0.0, +40.0] are lattice effects. Read them as 'a few events per run'.
- `b45_step` changes sign between lengths: +5.3 [+2.7, +7.5] at 300 m and -5.1 [-7.1, -3.2] at 600 m against lr400_16_1 (grid_lr400_13_1: +5.3 [+2.6, +7.8], -5.3 [-7.4, -3.1]); distinct encounters too (+12.1 [+8.5, +15.4] → -34.8 [-40.5, -26.8]). Printed, never deciding.
- The V2 missed share is slightly negative for every arm (median −0.003 % to −0.205 %; pooled −0.01 % to −0.18 %): the 1-Hz count × 1 s is a little larger than the 0.1-s time, so the 1-Hz count misses no close-following time in aggregate. Per run the share spreads about ±1.5 %. I have not established why the bias is negative.
- `c15_cap_share_600` = 0.0 is a real zero, not an empty denominator: 0 of about 32 M decisions per learner. grid_lr400_13_1 (1,566) and p333 (2,991) do hit the cap; those arms also carry the observation counters (the smoke shows the same). What column 15 encodes was not traced here.
- No control at 600 m, seed 7,492,030, has `ttc_net` = 0 (its 300-m run: 717). The seed is light for every arm (600 m: 7-87 samples; delay below the medians) and the row looks complete (2,149 passed, 644 merges, 0 collisions, 0 teleports). One run; not investigated further.
- No control keeps most of its close-following and standing at 600 m (`ttc_net` median 1,340 → 673.5; standing medians 110 and 412 veh-s), while every controlled arm's `ttc_net` median falls by 91-94 % and its standing medians by 92-97 %. Hence the large edges against no control at 600 m (+72.7 %) and VV-D12's 'removed' = False at both merges (no control's lower bounds 36 % and 15 %).
- Lane-end standing at 600 m is heavy-tailed (e.g. lr400_16_1 merge 2: median 23, mean 289 veh-s; 18-36 % of controlled runs have no standing vehicle). v3w's VV-D12 row uses the per-seed mean of the learners, whose median exceeds every single learner's median (§7), so its cut (84-85 %) is not comparable with the rules' single-arm cuts (95-97 %). Per learner the cuts are 92.6-97.1 % (post hoc).
- Collisions: 0 in all 2,400 learner runs at each length; rules and p333 0-2 per 480 runs; no control 0 at 300 m and 1 at 600 m. Teleports 0 in all 8,640 runs. Stuck vehicles (post hoc): at most 6 per 480 runs (lr400_16_1 at 300 m).
- Jams were not recomputed. At 600 m the rules' jam edges are +0.0 [+0.0, +0.0] [v3]; whether that is a zero median (as in the † cells) cannot be told from v3.json.
- No close-following sample was ever counted on edges 4 or 5 in the 8,640 runs (road keys in `m_road_ttc3`).
- The V1 visual check (40 samples, rng 20261115) is drawn but not plotted or judged; V1 stays 'CHECKS PASS; visual check pending' [status].

