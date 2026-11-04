# Baseline v1: r1m3 P0, 2026-11-03

The frozen plant for phase 1, with no controller. Any controller on P0 is compared with this. Git tag `baseline-v1`. Decisions: V314, V322-V329. Baseline v0 keeps the earlier plant as history.

Exploratory: this describes the plant. There is no claim.

## The plant

r1m3 as in baseline v0 (road, demand pattern, fleet, 300-m acceleration lane, meter green, ALKS tau 1.6 s, 0.5-s delay), with two changes, in `plant_p0.json`:

1. `lcAssertive` 1.4 for all vehicles.
2. The smooth no-undertaking rule for ALKS (V326): SUMO's abrupt rule is off for ALKS; above 60 km/h, and not on the acceleration lane, the desired speed is capped at that of a slower vehicle ahead in the left lane within 5 s, dropping by at most a ratio of 1.1 per second. Our model, so it must be disclosed.

Humans keep SUMO's no-undertaking rule. Frozen code `124b930`.

## Check on unused seeds 7,419,640-649

0 collisions and 0 teleports at all 4 levels. All 12 metrics below improve at 5,300 except braking at 7 m/s², whose CI includes 0.

| Level | Metric | Earlier plant | P0 | % better, CI |
|---|---|---|---|---|
| 4090 | Flow | 1696.5 | 1707.5 | +0.8 [+0.2, +1.4] |
| 4090 | Vehicle-seconds | 466212 | 456201 | +1.0 [-1.3, +2.4] |
| 4090 | Delay s | 49.68 | 44.27 | +9.1 [-4.2, +18.0] |
| 4090 | Delay p95 s | 122.28 | 94.63 | +23.4 [-1.2, +31.8] |
| 4090 | Ramp delay s | 62.98 | 34.61 | +43.7 [+18.9, +76.4] |
| 4090 | Fuel mg/km | 80508.9 | 76470.9 | +5.4 [+3.5, +6.2] |
| 4090 | Network TTC | 1059.5 | 11 | +99.2 [+49.6, +141.3] |
| 4090 | Braking 3+ | 3528.5 | 1038 | +69.7 [+50.6, +75.5] |
| 4090 | Braking 4.5+ | 386.5 | 29 | +91.7 [+56.4, +105.8] |
| 4090 | Braking 7+ | 2.5 | 0.5 | +80.0 [+40.0, +160.0] |
| 4090 | Free-road ALKS braking | 1319.5 | 101 | +92.2 [+82.8, +99.6] |
| 4090 | Lane-end stops | 1296 | 9.5 | +99.4 [+57.9, +149.7] |
| 4600 | Flow | 1878.5 | 1908 | +1.8 [+1.2, +4.0] |
| 4600 | Vehicle-seconds | 576172 | 548596 | +3.2 [+0.8, +5.5] |
| 4600 | Delay s | 82.3 | 65.29 | +12.3 [+3.5, +25.0] |
| 4600 | Delay p95 s | 194.31 | 123.64 | +35.0 [+21.4, +55.4] |
| 4600 | Ramp delay s | 116.93 | 47.54 | +62.5 [+33.7, +88.2] |
| 4600 | Fuel mg/km | 84057.9 | 77537.5 | +7.5 [+6.3, +9.0] |
| 4600 | Network TTC | 1950 | 13.5 | +90.8 [+74.5, +112.1] |
| 4600 | Braking 3+ | 4413 | 1260.5 | +68.6 [+62.9, +82.1] |
| 4600 | Braking 4.5+ | 435.5 | 44 | +88.7 [+79.3, +110.4] |
| 4600 | Braking 7+ | 4 | 0.5 | +50.0 [+25.0, +200.0] |
| 4600 | Free-road ALKS braking | 1548 | 120 | +91.9 [+81.9, +108.1] |
| 4600 | Lane-end stops | 1790.5 | 24.5 | +85.8 [+69.2, +156.0] |
| 5300 | Flow | 1957 | 2097.5 | +6.9 [+5.1, +7.8] |
| 5300 | Vehicle-seconds | 806145 | 757092 | +6.0 [+4.5, +6.4] |
| 5300 | Delay s | 146.39 | 126.93 | +11.3 [+9.4, +15.7] |
| 5300 | Delay p95 s | 356.34 | 212.24 | +42.0 [+33.7, +45.2] |
| 5300 | Ramp delay s | 229.82 | 79.9 | +66.3 [+51.3, +72.3] |
| 5300 | Fuel mg/km | 88204 | 80338.7 | +9.6 [+7.8, +10.2] |
| 5300 | Network TTC | 1903.5 | 618 | +71.7 [+58.3, +96.5] |
| 5300 | Braking 3+ | 4887.5 | 2092.5 | +56.1 [+47.8, +63.6] |
| 5300 | Braking 4.5+ | 500 | 156 | +61.6 [+55.7, +77.2] |
| 5300 | Braking 7+ | 3 | 1 | +83.3 [-100.0, +166.7] |
| 5300 | Free-road ALKS braking | 1897 | 205 | +90.0 [+79.7, +94.0] |
| 5300 | Lane-end stops | 2606.5 | 147 | +89.9 [+66.4, +116.9] |
| 6000 | Flow | 1997.5 | 2115 | +5.6 [+4.1, +7.6] |
| 6000 | Vehicle-seconds | 1.07184e+06 | 1.03484e+06 | +4.3 [+2.3, +6.2] |
| 6000 | Delay s | 231.52 | 209.17 | +9.3 [+2.7, +11.1] |
| 6000 | Delay p95 s | 484.01 | 370.26 | +22.5 [+18.0, +34.3] |
| 6000 | Ramp delay s | 279.6 | 119.38 | +52.8 [+38.5, +74.4] |
| 6000 | Fuel mg/km | 88565.4 | 82912.5 | +7.5 [+5.8, +8.3] |
| 6000 | Network TTC | 1668 | 1386 | +18.5 [-1.0, +29.8] |
| 6000 | Braking 3+ | 4704.5 | 2681 | +40.5 [+37.9, +50.8] |
| 6000 | Braking 4.5+ | 480 | 304 | +40.8 [+30.9, +47.3] |
| 6000 | Braking 7+ | 3.5 | 3 | +42.9 [-85.7, +114.3] |
| 6000 | Free-road ALKS braking | 1857.5 | 273 | +85.9 [+78.7, +87.7] |
| 6000 | Lane-end stops | 2052.5 | 564 | +59.9 [+47.7, +104.0] |

**Passes on the right.** The counter rose at 5,300 (72 to 86.5 per run, CI of the change including 0), so the literal V328 item failed there. Traced on one seed at 5,300:

| Plant | All passes | Accel lane | ALKS itself changing lane | Both going straight |
|---|---|---|---|---|
| Earlier plant | 63 | 6 | 16 | 41 |
| P0 | 81 | 56 | 23 | 2 |
| ALKS allowed to undertake | 813 | 14 | 21 | 778 |

Only "both going straight" is undertaking in the plain sense. Passing on the acceleration lane is normal merging, and it rises because the ramp now flows.

## Door-to-door delay, 7,419,623-649

Vehicles planned and finished in the window; seeds 623-639 were used to choose P0, so this table is not independent of the choice.

| Level | Group | Delay s, earlier | Delay s, P0 | p95 s, earlier | p95 s, P0 | Finished %, earlier | Finished %, P0 |
|---|---|---|---|---|---|---|---|
| 4090 | all | 41.3 | 44.3 | 93 | 95 | 82.1 | 82.1 |
| 4090 | main | 41.7 | 46.3 | 93 | 97 | 81.0 | 80.8 |
| 4090 | ramp | 44.0 | 33.6 | 96 | 60 | 88.1 | 89.5 |
| 4090 | main_alks | 48.1 | 60.9 | 113 | 105 | 80.6 | 79.7 |
| 4090 | main_hdv | 35.6 | 32.8 | 76 | 72 | 80.8 | 81.6 |
| 4090 | ramp_alks | 55.5 | 45.1 | 113 | 63 | 88.8 | 89.7 |
| 4090 | ramp_hdv | 35.8 | 21.6 | 84 | 44 | 88.5 | 89.4 |
| 4600 | all | 76.9 | 68.4 | 184 | 124 | 79.4 | 80.5 |
| 4600 | main | 71.5 | 72.9 | 180 | 127 | 78.5 | 78.9 |
| 4600 | ramp | 103.2 | 47.1 | 189 | 75 | 82.7 | 88.7 |
| 4600 | main_alks | 76.0 | 88.7 | 206 | 134 | 78.6 | 78.5 |
| 4600 | main_hdv | 67.3 | 56.9 | 159 | 101 | 78.5 | 79.5 |
| 4600 | ramp_alks | 116.6 | 59.0 | 193 | 77 | 82.0 | 88.5 |
| 4600 | ramp_hdv | 89.3 | 34.7 | 162 | 63 | 84.2 | 89.3 |
| 5300 | all | 144.3 | 130.1 | 358 | 215 | 71.3 | 74.7 |
| 5300 | main | 135.6 | 139.0 | 358 | 217 | 71.8 | 72.9 |
| 5300 | ramp | 200.5 | 73.3 | 335 | 102 | 68.7 | 85.6 |
| 5300 | main_alks | 145.0 | 158.5 | 386 | 237 | 70.5 | 72.4 |
| 5300 | main_hdv | 128.3 | 121.9 | 326 | 193 | 72.4 | 74.3 |
| 5300 | ramp_alks | 209.5 | 82.2 | 335 | 104 | 68.4 | 86.4 |
| 5300 | ramp_hdv | 193.3 | 65.4 | 340 | 99 | 69.8 | 85.8 |
| 6000 | all | 235.3 | 207.5 | 483 | 355 | 62.2 | 65.6 |
| 6000 | main | 225.9 | 231.4 | 493 | 360 | 61.7 | 62.9 |
| 6000 | ramp | 269.0 | 101.9 | 457 | 169 | 61.6 | 80.2 |
| 6000 | main_alks | 233.9 | 252.6 | 515 | 383 | 60.8 | 61.8 |
| 6000 | main_hdv | 215.1 | 211.9 | 451 | 325 | 62.6 | 64.7 |
| 6000 | ramp_alks | 286.3 | 110.4 | 460 | 173 | 61.8 | 79.2 |
| 6000 | ramp_hdv | 266.1 | 93.9 | 444 | 165 | 61.0 | 81.2 |

## Lanes at the merge, 7,419,623-649

| Level | Lane | Flow veh/h, earlier | Flow veh/h, P0 | Speed m/s, earlier | Speed m/s, P0 |
|---|---|---|---|---|---|
| 4600 | 3a_0 | 377 | 221 | 3.6 | 18.8 |
| 4600 | 3a_1 | 949 | 1256 | 4.1 | 17.0 |
| 4600 | 3a_2 | 1569 | 1355 | 17.1 | 21.3 |
| 4600 | 3a_3 | 1632 | 1763 | 24.6 | 23.9 |
| 4600 | 3_0 | 1206 | 1206 | 20.2 | 18.2 |
| 4600 | 3_1 | 1565 | 1434 | 22.3 | 20.6 |
| 4600 | 3_2 | 1719 | 1950 | 24.4 | 22.9 |
| 5300 | 3a_0 | 368 | 330 | 2.6 | 14.9 |
| 5300 | 3a_1 | 901 | 1262 | 3.5 | 12.6 |
| 5300 | 3a_2 | 1771 | 1487 | 16.4 | 18.5 |
| 5300 | 3a_3 | 1766 | 2045 | 23.9 | 21.3 |
| 5300 | 3_0 | 1240 | 1383 | 19.3 | 16.5 |
| 5300 | 3_1 | 1726 | 1546 | 21.0 | 17.7 |
| 5300 | 3_2 | 1831 | 2126 | 23.7 | 20.0 |

## Where everything is

Read-only full copy, with `SHA256SUMS`: `/home/catalin/work/phd/v5b1_runs/baseline_v1/`: frozen code, one file per instrumented run with every vehicle and lane, all sweep rows in `check/`, the plant as SUMO sees it in `plant/`, environment in `system/`.

In git here: `check_rows.jsonl.gz`, `check_table.csv`, `detail_*`, `plant.json.gz`, `plant_*`, `constants.json`, the scripts. Sweep rows: `docs/research/plant_v1/`.

Fuel is per run (`check_rows.jsonl.gz`, `docs/research/plant_v1/stage_d3.jsonl.gz`), sampled each second from SUMO's HBEFA4 models, not per vehicle. Other run-level fields, including jerk, are in the same rows.

## Known gaps

- Capacity drop is not settled: the V271 estimator has no null and is unreliable when few runs break down.
- SUMO's lane-change behaviour at `lcAssertive` 1.4 is not validated against real traffic.
- The merge is better, not perfect: at 5,300 about 95 % of demand is served.
- At 4,090, on the choosing seeds, delay was worse than the earlier plant (44.4 vs 39.1 s); on the check seeds it was not clearly different (44.3 vs 49.7 s).
- Stored results from the earlier plant contain the sawtooth (V324).
- Tracing of passes on the right is one seed.
