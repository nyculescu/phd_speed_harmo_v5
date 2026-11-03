# Baseline v0, 2026-11-03

The state of the B and C line on plant m32 before the exploration of V305. Any new direction is compared with this. Git tag `baseline-v0`. Decisions: V306, V307.

Everything here is exploratory. There is no claim, because no result has passed a pre-registered check on unused seeds.

## Check

The instrumented re-runs used the baseline's own copy of code and policies. Each row was compared field by field with its stored copy.

| Re-run | Seeds | Rows | Identical |
|---|---|---|---|
| All V304 evaluation rows | 7,419,650-669 | 1,000 | 1,000 |
| F0-F2, p303, a000, a333 | 7,419,960-979 | 240 | 240 |

So reading the extra data did not change the simulation, and the copy is self-contained.

## Where everything is

Full copy, read-only: `/home/catalin/work/phd/v5b1_runs/baseline_v0/` (ext4), with `SHA256SUMS` for every file.

| Path there | Content |
|---|---|
| `b_train/` | All runs: frozen code `code_*`, launchers, specs, rows, training logs, every checkpoint |
| `detail/runs/`, `detail_fresh/runs/` | One gzip JSON per run: every vehicle (planned and actual departure, edge entry times, lane and speed at entry, arrival, sampled driver parameters), lane density, speed and halts in 60-s bins, lane changes |
| `plant/` | Network, additional file, example routes, every vType, SUMO arguments, constants, policy structures |
| `system/` | Git state, Python and pip versions, machine, systemd journal of the `b-*` units |
| `repo_copy/` | A copy of this folder |

This folder in git, every file under 5 MB:

| File | Content |
|---|---|
| `rows_all.jsonl.gz` | All 8,202 unique evaluation rows with their source folders |
| `summary_all.csv` | Per source, controller and level: medians of every field, and paired comparisons with a000 and p303 |
| `arms.csv` | Every controller in every spec: model, settings, levels, seeds |
| `headline_absolute.csv`, `headline_paired.csv` | Seeds 650-669: delay, flow, safety; paired with a000, p303, a333 |
| `fresh_headline_absolute.csv`, `fresh_headline_paired.csv` | The same on seeds 960-979 |
| `detail_delay.csv`, `detail_delay_per_run.csv.gz` | Door-to-door delay by route and vehicle type |
| `detail_lanes.csv`, `detail_lanes_per_run.csv.gz`, `detail_lane_timeseries.csv.gz`, `fresh_detail_lanes.csv` | Flow, density, speed and halts per lane |
| `detail_lane_changes.csv`, `detail_edge_times.csv`, `detail_entry_lanes.csv` | Lane changes per edge, travel time per edge, lane used at each edge entry |
| `detail_demand.csv` | Fleet composition and driver parameter ranges |
| `training_updates.csv`, `training_episodes.csv`, `logs.tar.gz` | Learning curves and all raw training logs |
| `policies/` | All 24 final policies |
| `plant.json.gz`, `plant_*`, `constants.json`, `policies.json` | The plant, every constant, policy structures |
| `launchers.tar.gz`, `seeds_used.csv`, `system_*` | Launch scripts, seed use, environment |
| `SHA256SUMS` | Checksums of the full copy |
| `detail_run.py`, `plant_dump.py`, `build.py`, `headline.py`, `fresh_delay.py` | The scripts that made all of this |

Not stored: step-by-step vehicle positions, SUMO's temporary files. Other folders in `v5b1_runs` (older tracks) are only listed, in `system/v5b1_runs_listing.txt`.

## Software

Frozen code `b7c535a` for the re-runs, `c1e0ac3` for training F. Python 3.14.4, libsumo 1.27.1, CPU torch; exact versions in `system_pip_freeze.txt`. `unset SUMO_HOME; export OMP_NUM_THREADS=1`.

## Plant m32

Ramp32 without the 3-to-2 lane drop, ramp meter always green. Step 0.1 s, no teleporting, collisions warn only. Warm-up 300 s, then a 1,500-s window; constant demand within a run.

| Edge | Lanes | Length m |
|---|---|---|
| 1 | 3 | 3,000 |
| 2 | 3 | 498 |
| 3a (merge) | 4 | 295 |
| 3 | 3 | 1,196 |
| 4 | 3 | 1,000 |
| 5 | 3 | 500 |
| r (ramp) | 1 | 392 |
| rj (ramp) | 1 | 28 |

Speed limit 27.78 m/s everywhere. Route lengths: main 6,489 m, ramp 3,411 m.

SUMO: `--step-length 0.1 --seed S --route-steps 0 --time-to-teleport -1 --collision.action warn --collision.check-junctions true`.

Fleet at 5,300 veh/h, vehicles per run including warm-up:

| Route | Class | Vehicles | Speed factor p5-p95 | Tau s p5-p95 | Sigma p5-p95 | Length m p5-p95 |
|---|---|---|---|---|---|---|
| main | alks | 1113 | 1.0-1.0 | 1.6-1.6 | - | 3.617-4.937 |
| main | hdv_car | 963 | 0.78-1.178 | 0.378-1.465 | 0.11-0.749 | 3.627-4.945 |
| main | truck | 175 | 0.789-0.972 | - | - | 15.546-16.449 |
| ramp | alks | 191 | 1.0-1.0 | 1.6-1.6 | - | 3.611-4.932 |
| ramp | hdv_car | 170 | 0.774-1.178 | 0.378-1.459 | 0.111-0.777 | 3.614-4.941 |
| ramp | truck | 30 | 0.784-0.961 | - | - | 15.547-16.462 |

Every vehicle has its own vType (2,650 in the example run), so drivers differ. The human drivers are less uniform than "perfect traffic" suggests, but demand is constant, there are no incidents, and no capacity drop was measurable (V244, V271).

ALKS: tau 1.6 s by default, speed factor 1.0, accel 2.6, decel 4.5, emergency 9.0 m/s², minGap 2.5 m, action step 0.5 s used as a sensing and actuation delay. V2V rule: an ALKS uses the commanded headway only behind another ALKS within 150 m, with the same leader on two 1-s updates; otherwise 1.6 s.

Headway levels: 0 = 1.6 s, 1 = 1.2 s, 2 = 1.0 s, 3 = 0.8 s. Zones: merge = last 100 m of edge 2, all of 3a, first 300 m of edge 3; up = before it; down = after it.

## Controllers

| Name | What it does | Rate limit |
|---|---|---|
| a000 | Delay alone: every ALKS at 1.6 s | none |
| a`umd` | Fixed target per zone (up, merge, down), by level | one level per 60 s per zone |
| p`umd` | The same pattern applied per vehicle, no learning | one level per 30 s per vehicle |
| r2_0.8_02 | The tuned rule from V283 | as zones |
| A | Central PPO capping speed of the mainline ALKS nearest the merge | not used since run 3 |
| B | Central PPO choosing 3 zone targets every 10 s | as zones |
| C | One shared PPO policy for all ALKS, choosing an absolute level | one level per 30 s per vehicle; each vehicle decides on its own 30-s clock |

Policies: F = C, safety weight 10. G = C, weight 20. H = C, weight 40. B0-B2 = B with C's shared reward. L = run 5 zone policies.

**C network:** actor MLP 16-64-64-4, critic MLP 26-64-64-1, 11,461 parameters. PPO: gamma 0.8, lambda 0.9, 10 epochs, batch 4,096, lr 3e-4, clip 0.2, entropy 0.01, value 0.5, gradient 0.5. 3 learners x 3 environments, 250 updates, levels 4,090, 4,600, 5,300. Environment step 5 s.

**C local observation (16):** position, position near merge, on ramp, lane, speed, leader gap, closing speed to leader, leader is ALKS, follower gap, follower closing speed, own level, hold left, 200-m bin speed, merge zone speed, nearest ramp vehicle, vehicles on 3a_0.

**C global, critic only (10):** 3 zone speeds, 3 zone counts, vehicles on 3a_0, insertion queue, time, smoothed flow.

**B network:** SB3 MlpPolicy, 51 inputs, 15,821 parameters. Gamma 0.95, lambda 0.95, 101 steps x 3 environments, batch 75, 10 epochs, 500 updates, 151,500 steps, reward normalised.

## Reward

Per vehicle per environment step, C:

shared + 0.5 (own v / limit - 1) + 0.5 (200-m bin v / limit - 1) + 0.4 min((v / spacing) / 0.6, 1.5) - w_safety (ttc + hard + 0.5 (follower ttc + follower hard)) - 0.01 per move

shared = smoothed flow / demand - 1 + mean speed / limit - 1 - (vehicles in system / reference - 1). w_safety is 10, 20 or 40; the code default is 20. A vehicle that leaves is cut off with its last value bootstrapped.

B with cfg 8: shared only, minus 0.1 per target change. It has no safety term.

## Metrics

| Field | Definition |
|---|---|
| `passed` (flow) | Vehicles first seen on edge 4 in the window, sampled each second |
| `mean_v` | Mean speed over all live vehicles each second, summed |
| `N` | Vehicles in the network plus insertion queue each second, summed |
| `E30`, `E15` | Follower-seconds with closing rear TTC below 3 s and 1.5 s, **merge lanes only**: last 100 m of 2_0, 3a_0, 3a_1, first 300 m of 3_0 |
| `brake3`, `brake45` | Vehicle-seconds braking at 3 and 4.5 m/s² or harder, merge lanes only |
| `out_E30`, `out_b3` | The same two counts for the rest of the network |
| `gap25`, `stop_gap` | Follower-seconds with bumper gap below 2.5 m, moving and stopped (V283: mostly stopped queues at SUMO's minGap) |
| `collisions`, `contact_steps` | Collision events, steps in contact |
| delay | Arrival minus planned departure minus route length / (27.78 x speed factor), vehicles planned and finished inside the window |
| time in system | Arrival or window end, minus planned departure, all vehicles planned in the window |
| lane flow | Density x speed, estimated each second, 60-s bins |

Every percentage: median of paired differences across seeds, higher is better, 95 % percentile bootstrap CI.

Delay and lane data exist only for seeds 650-669 and 960-979.

## Results: absolute medians

Seeds 7,419,650-669:

| Level | Controller | Flow | Delay s | Main s | Ramp s | Delay p95 s | Time in system s | Insertion wait s | TTC merge | TTC network | Brake merge | Brake network | Collisions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4600 | a000 | 1866 | 75.3 | 72.1 | 92.8 | 184.1 | 269.0 | 4.1 | 1170 | 1600 | 1276 | 4392 | 0 |
| 4600 | p303 | 1906 | 51.5 | 49.4 | 67.3 | 125.6 | 249.6 | 3.9 | 1217 | 1374 | 1595 | 4102 | 0 |
| 4600 | a333 | 1898 | 57.4 | 53.8 | 79.9 | 132.6 | 254.2 | 3.8 | 1720 | 1948 | 1756 | 4443 | 0 |
| 4600 | p302 | 1904 | 52.3 | 48.0 | 67.4 | 119.4 | 249.7 | 3.8 | 1322 | 1358 | 1592 | 4025 | 0 |
| 4600 | p312 | 1890 | 52.3 | 51.3 | 69.2 | 120.3 | 251.3 | 4.0 | 1290 | 1417 | 1486 | 3952 | 0 |
| 4600 | F0 | 1903 | 51.4 | 48.5 | 61.1 | 108.4 | 248.8 | 3.9 | 1095 | 1228 | 1488 | 4121 | 0 |
| 4600 | F1 | 1910 | 51.5 | 50.5 | 64.3 | 115.3 | 248.8 | 3.9 | 1082 | 1116 | 1523 | 3868 | 0 |
| 4600 | F2 | 1900 | 50.1 | 49.2 | 58.7 | 117.3 | 248.0 | 3.7 | 957.0 | 1110 | 1358 | 3832 | 0 |
| 4600 | G0 | 1898 | 53.4 | 49.5 | 60.9 | 121.9 | 251.0 | 3.7 | 1165 | 1288 | 1551 | 4258 | 0 |
| 4600 | G1 | 1904 | 49.5 | 48.7 | 58.9 | 108.6 | 247.3 | 3.9 | 910.0 | 1044 | 1400 | 3838 | 0 |
| 4600 | G2 | 1910 | 51.6 | 49.5 | 67.5 | 117.3 | 249.5 | 4.0 | 1176 | 1328 | 1468 | 4155 | 0 |
| 4600 | H0 | 1908 | 55.8 | 51.8 | 75.3 | 122.9 | 253.2 | 3.9 | 1316 | 1467 | 1596 | 4285 | 0 |
| 4600 | H1 | 1900 | 52.4 | 50.4 | 70.5 | 118.2 | 251.7 | 3.7 | 1190 | 1364 | 1512 | 4226 | 1 |
| 4600 | H2 | 1912 | 51.9 | 51.4 | 62.9 | 110.5 | 249.6 | 3.9 | 1148 | 1188 | 1464 | 3886 | 0 |
| 4600 | B0 | 1892 | 58.7 | 54.3 | 76.7 | 130.6 | 255.3 | 3.7 | 1486 | 1818 | 1637 | 4590 | 0 |
| 4600 | B1 | 1892 | 57.8 | 53.8 | 76.5 | 131.7 | 253.8 | 3.7 | 1747 | 1928 | 1766 | 4313 | 0 |
| 4600 | B2 | 1894 | 50.6 | 49.8 | 59.5 | 112.1 | 250.1 | 3.7 | 1316 | 1394 | 1505 | 4030 | 0 |
| 5300 | a000 | 1968 | 144.5 | 134.6 | 201.4 | 367.6 | 327.8 | 37.9 | 1103 | 1944 | 1158 | 5054 | 0 |
| 5300 | p303 | 2052 | 115.3 | 107.4 | 151.5 | 273.8 | 302.9 | 35.6 | 1359 | 2389 | 1420 | 5456 | 0 |
| 5300 | a333 | 2050 | 111.8 | 106.8 | 173.5 | 265.2 | 301.7 | 32.8 | 2036 | 3236 | 1696 | 6004 | 0 |
| 5300 | p302 | 2052 | 120.9 | 108.9 | 171.6 | 261.5 | 308.6 | 35.6 | 1356 | 2622 | 1361 | 5632 | 0 |
| 5300 | p312 | 2033 | 117.1 | 108.4 | 193.9 | 285.3 | 305.2 | 35.1 | 1580 | 2722 | 1503 | 5600 | 0 |
| 5300 | F0 | 2069 | 109.4 | 106.5 | 150.0 | 251.5 | 298.1 | 34.7 | 1446 | 2427 | 1476 | 5496 | 0 |
| 5300 | F1 | 2066 | 113.5 | 106.6 | 147.1 | 252.2 | 300.8 | 35.5 | 1504 | 2403 | 1565 | 5370 | 0 |
| 5300 | F2 | 2072 | 107.1 | 103.2 | 135.7 | 240.3 | 294.6 | 35.1 | 1394 | 2334 | 1462 | 5334 | 0 |
| 5300 | G0 | 2064 | 110.2 | 103.8 | 168.4 | 250.2 | 301.0 | 36.0 | 1502 | 2368 | 1512 | 5458 | 0 |
| 5300 | G1 | 2063 | 113.1 | 102.0 | 181.0 | 250.2 | 300.9 | 34.8 | 1382 | 2358 | 1497 | 5454 | 0 |
| 5300 | G2 | 2070 | 110.9 | 106.3 | 142.4 | 231.2 | 299.1 | 34.7 | 1550 | 2536 | 1473 | 5369 | 0 |
| 5300 | H0 | 2054 | 117.0 | 104.3 | 178.3 | 263.7 | 303.0 | 35.0 | 1304 | 2187 | 1418 | 5245 | 0 |
| 5300 | H1 | 2057 | 112.8 | 103.8 | 158.5 | 261.0 | 301.4 | 34.9 | 1340 | 2294 | 1481 | 5354 | 0 |
| 5300 | H2 | 2058 | 116.3 | 107.6 | 159.2 | 250.1 | 303.9 | 35.0 | 1515 | 2396 | 1470 | 5473 | 0 |
| 5300 | B0 | 2036 | 116.7 | 110.0 | 192.3 | 282.9 | 305.3 | 33.8 | 1740 | 2908 | 1534 | 5685 | 0 |
| 5300 | B1 | 2038 | 118.6 | 111.5 | 167.8 | 274.3 | 307.1 | 33.4 | 1857 | 2882 | 1578 | 5830 | 0 |
| 5300 | B2 | 2053 | 111.5 | 106.5 | 173.5 | 259.9 | 300.1 | 32.9 | 2074 | 3240 | 1715 | 6004 | 0 |

Seeds 7,419,960-979:

| Level | Controller | Flow | Delay s | Main s | Ramp s | Delay p95 s | Time in system s | Insertion wait s | TTC merge | TTC network | Brake merge | Brake network | Collisions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4600 | a000 | 1874 | 77.4 | 70.9 | 111.5 | 184.2 | 269.3 | 4.4 | 1190 | 1854 | 1358 | 4380 | 0 |
| 4600 | p303 | 1906 | 56.9 | 54.2 | 75.0 | 133.2 | 252.5 | 4.4 | 1327 | 1582 | 1590 | 4290 | 0 |
| 4600 | a333 | 1900 | 56.0 | 52.2 | 83.7 | 129.5 | 253.2 | 4.1 | 2028 | 2079 | 1880 | 4582 | 1 |
| 4600 | F0 | 1890 | 52.0 | 47.7 | 63.0 | 111.3 | 248.9 | 4.5 | 1154 | 1252 | 1599 | 4174 | 0 |
| 4600 | F1 | 1907 | 52.2 | 48.0 | 69.0 | 119.5 | 250.1 | 4.4 | 1284 | 1497 | 1635 | 4017 | 0 |
| 4600 | F2 | 1906 | 55.9 | 50.5 | 78.7 | 129.2 | 251.2 | 4.5 | 1570 | 1706 | 1764 | 4382 | 0 |
| 5300 | a000 | 1956 | 138.8 | 133.8 | 202.9 | 367.7 | 329.9 | 34.7 | 1185 | 1964 | 1215 | 4970 | 0 |
| 5300 | p303 | 2056 | 114.2 | 105.5 | 185.4 | 263.0 | 303.2 | 31.2 | 1345 | 2468 | 1445 | 5402 | 0 |
| 5300 | a333 | 2054 | 111.0 | 101.1 | 166.4 | 250.8 | 299.4 | 29.5 | 2117 | 3277 | 1640 | 5800 | 0 |
| 5300 | F0 | 2064 | 103.0 | 94.7 | 167.4 | 234.6 | 292.1 | 31.4 | 1470 | 2392 | 1556 | 5396 | 0 |
| 5300 | F1 | 2068 | 109.3 | 100.9 | 185.4 | 261.3 | 299.0 | 33.3 | 1471 | 2264 | 1479 | 5360 | 0 |
| 5300 | F2 | 2058 | 114.2 | 103.6 | 197.2 | 256.1 | 302.1 | 32.7 | 1689 | 2529 | 1543 | 5446 | 0 |

## Results: against p303, % with CI

| Level | Seeds | Policy | Flow | Delay | Main delay | Ramp delay | TTC merge | TTC network | Brake network |
|---|---|---|---|---|---|---|---|---|---|
| 4600 | 650-669 | F0 | +0.3 [-0.5, +0.7] | +6.8 [-3.6, +11.6] | +4.8 [-1.3, +8.1] | +13.5 [-15.0, +29.7] | +27.9 [+3.7, +51.4] | +26.1 [-0.7, +44.5] | +6.8 [-6.5, +13.4] |
| 4600 | 650-669 | F1 | +0.5 [-0.1, +0.7] | +2.5 [-9.2, +6.5] | +0.4 [-6.6, +3.3] | +6.1 [-12.8, +21.2] | +9.3 [-19.1, +27.3] | +11.7 [-21.0, +24.9] | -1.5 [-6.7, +9.3] |
| 4600 | 650-669 | F2 | -0.2 [-0.5, +0.4] | +5.2 [-4.0, +12.7] | +4.1 [-1.2, +6.6] | +8.2 [-5.8, +27.6] | +17.9 [-11.1, +29.2] | +13.1 [-9.1, +32.1] | +5.8 [-6.2, +10.9] |
| 4600 | 650-669 | G0 | -0.2 [-0.8, +0.5] | +3.1 [-2.1, +9.3] | +2.7 [-1.9, +6.2] | +4.8 [-5.3, +21.5] | +3.9 [-23.3, +27.9] | +0.8 [-18.1, +29.7] | +1.2 [-6.6, +11.5] |
| 4600 | 650-669 | G1 | -0.1 [-0.6, +0.7] | +1.6 [-1.8, +9.7] | +3.2 [-0.6, +5.1] | -2.4 [-8.5, +27.6] | -4.2 [-14.4, +24.7] | +0.4 [-12.3, +24.2] | +2.4 [-3.7, +8.4] |
| 4600 | 650-669 | G2 | +0.0 [-0.2, +0.2] | +2.4 [-4.3, +9.1] | +1.6 [-2.1, +6.4] | +5.5 [-7.5, +23.2] | +11.4 [-10.5, +32.0] | +4.7 [-12.3, +33.3] | +1.9 [-3.7, +9.7] |
| 4600 | 650-669 | H0 | +0.2 [-0.6, +0.3] | -6.1 [-11.8, +5.4] | -2.8 [-7.7, +3.9] | -15.0 [-27.1, +13.8] | -9.6 [-39.9, +23.5] | -3.4 [-40.4, +16.7] | -4.2 [-11.4, +3.6] |
| 4600 | 650-669 | H1 | +0.2 [-0.6, +0.8] | +0.3 [-5.8, +7.1] | +1.1 [-3.8, +4.7] | +3.4 [-20.5, +16.3] | +7.8 [-27.6, +34.9] | +8.5 [-25.1, +39.6] | +3.7 [-7.2, +9.4] |
| 4600 | 650-669 | H2 | +0.3 [-0.2, +0.7] | +3.8 [-6.8, +13.7] | +1.6 [-3.4, +8.9] | +13.5 [-18.7, +32.6] | +19.1 [-24.4, +35.9] | +21.3 [-19.0, +42.8] | +7.0 [+0.0, +11.3] |
| 4600 | 650-669 | B0 | -0.5 [-1.1, +0.1] | -7.6 [-20.9, +3.7] | -6.5 [-13.5, +1.8] | -13.7 [-47.2, +9.3] | -6.0 [-62.9, +10.8] | -15.2 [-72.8, +4.0] | +1.8 [-20.4, +4.5] |
| 4600 | 650-669 | B1 | -0.6 [-0.8, -0.2] | -3.8 [-10.3, +3.4] | +0.1 [-7.8, +2.9] | -13.0 [-24.1, +3.5] | -39.9 [-51.8, -17.5] | -34.8 [-44.1, -12.6] | -7.8 [-11.3, +4.7] |
| 4600 | 650-669 | B2 | -0.3 [-0.7, +0.1] | +1.2 [-10.3, +5.5] | -0.5 [-5.9, +5.2] | +4.8 [-26.3, +9.4] | -30.3 [-49.0, +2.0] | -23.5 [-49.3, +7.2] | -1.8 [-11.2, +1.8] |
| 4600 | 650-669 | a333 | -0.1 [-0.8, +0.2] | -5.1 [-15.0, +4.7] | -1.5 [-8.3, +3.2] | -15.4 [-42.8, +10.1] | -42.4 [-70.7, -26.4] | -33.4 [-68.1, -16.2] | -7.8 [-18.4, +0.9] |
| 4600 | 960-979 | F0 | +0.2 [-1.0, +0.9] | +4.4 [-3.5, +14.3] | +5.5 [-0.9, +10.4] | +3.1 [-14.7, +28.3] | -0.9 [-14.2, +29.2] | -0.5 [-12.4, +32.5] | -0.7 [-5.4, +11.6] |
| 4600 | 960-979 | F1 | +0.1 [-0.2, +0.4] | +13.4 [-8.0, +17.9] | +8.9 [-2.4, +12.3] | +29.0 [-17.6, +35.8] | +2.8 [-10.4, +36.9] | +25.3 [-10.2, +37.7] | +6.5 [-5.8, +14.5] |
| 4600 | 960-979 | F2 | +0.0 [-0.7, +0.7] | +4.8 [-7.8, +11.4] | +3.5 [-5.4, +9.0] | +4.0 [-15.8, +21.6] | -13.4 [-24.7, +3.9] | +0.0 [-20.0, +21.4] | +0.1 [-7.5, +9.2] |
| 4600 | 960-979 | a333 | +0.1 [-0.6, +0.6] | +0.9 [-7.9, +10.1] | +2.9 [-1.3, +6.8] | -3.7 [-20.9, +16.0] | -36.3 [-59.9, -8.2] | -27.5 [-49.1, -3.3] | -2.8 [-9.8, +1.8] |
| 5300 | 650-669 | F0 | +0.8 [-0.3, +1.6] | +6.5 [+3.3, +10.0] | +5.7 [+3.0, +7.8] | +4.8 [-1.8, +23.5] | -9.5 [-16.9, -0.8] | +3.5 [-8.3, +6.3] | -0.9 [-2.9, +5.9] |
| 5300 | 650-669 | F1 | +0.3 [-0.2, +1.2] | +5.3 [-4.3, +12.9] | +2.4 [-0.9, +8.3] | +8.1 [-24.5, +31.8] | -12.7 [-19.6, -4.1] | -0.7 [-11.7, +5.2] | -0.9 [-4.8, +4.2] |
| 5300 | 650-669 | F2 | +0.7 [-0.1, +1.8] | +5.5 [+0.8, +9.7] | +4.3 [+2.1, +8.8] | +6.7 [-4.3, +24.0] | -3.3 [-14.0, +8.1] | +5.7 [+0.6, +10.4] | +3.3 [-2.2, +5.8] |
| 5300 | 650-669 | G0 | +0.3 [-0.5, +1.4] | +3.7 [-3.5, +10.2] | +2.9 [+0.4, +5.7] | +9.0 [-8.8, +27.9] | -10.0 [-15.0, -5.5] | -2.5 [-5.1, +6.5] | -1.3 [-2.5, +6.0] |
| 5300 | 650-669 | G1 | +0.3 [-0.2, +1.0] | +4.9 [-0.3, +7.8] | +5.0 [+1.2, +6.9] | -2.6 [-17.8, +15.8] | -6.9 [-16.9, +4.0] | +2.5 [-5.6, +8.1] | +0.2 [-1.9, +6.0] |
| 5300 | 650-669 | G2 | +0.7 [+0.3, +1.8] | +5.9 [-0.8, +13.3] | +4.4 [+1.1, +7.7] | +1.6 [-11.7, +49.2] | -14.6 [-22.7, -9.2] | -6.6 [-9.3, +1.6] | +0.6 [-3.7, +4.2] |
| 5300 | 650-669 | H0 | -0.1 [-0.7, +1.3] | +3.1 [-5.9, +10.2] | +3.1 [+0.4, +7.7] | -4.8 [-25.5, +22.0] | -2.8 [-6.0, +6.7] | +7.7 [-4.1, +12.9] | +5.8 [+0.3, +7.1] |
| 5300 | 650-669 | H1 | +0.1 [-1.2, +1.7] | +1.9 [-2.5, +6.8] | +1.3 [-1.1, +6.3] | -4.8 [-10.9, +13.8] | -3.8 [-8.5, +3.0] | +2.5 [-0.2, +6.9] | +2.2 [-1.7, +4.8] |
| 5300 | 650-669 | H2 | +0.1 [-0.4, +1.2] | +3.6 [-0.8, +8.2] | +3.3 [+0.4, +6.3] | -6.9 [-17.6, +28.0] | -10.4 [-15.5, -2.1] | -2.4 [-8.1, +4.5] | -0.1 [-3.6, +5.6] |
| 5300 | 650-669 | B0 | -1.0 [-1.6, -0.3] | -2.4 [-6.4, +2.5] | +0.9 [-2.7, +3.4] | -20.0 [-35.4, +2.5] | -30.2 [-36.3, -24.0] | -20.6 [-29.0, -18.8] | -3.8 [-6.8, -0.3] |
| 5300 | 650-669 | B1 | -0.7 [-0.9, -0.1] | -2.5 [-6.4, +0.9] | +0.0 [-3.7, +1.3] | -11.5 [-27.4, -1.5] | -41.9 [-46.8, -25.5] | -20.0 [-33.6, -14.8] | -6.2 [-10.0, -1.6] |
| 5300 | 650-669 | B2 | -0.0 [-0.7, +0.4] | +1.1 [-5.6, +6.5] | +0.2 [-2.4, +5.0] | -12.8 [-23.6, +25.5] | -55.6 [-64.7, -50.6] | -37.8 [-43.3, -33.4] | -10.3 [-12.2, -7.7] |
| 5300 | 650-669 | a333 | -0.0 [-0.7, +0.2] | +0.4 [-6.3, +6.5] | +4.2 [-1.5, +6.0] | -14.9 [-23.6, +25.5] | -55.6 [-64.0, -48.6] | -37.8 [-42.8, -31.5] | -9.8 [-11.5, -7.0] |
| 5300 | 960-979 | F0 | +0.5 [-0.2, +0.8] | +1.7 [-1.6, +8.6] | +3.7 [+0.2, +8.0] | -0.9 [-10.3, +14.4] | -11.5 [-16.8, -4.2] | +0.8 [-2.1, +8.8] | +1.1 [-0.5, +5.8] |
| 5300 | 960-979 | F1 | +0.8 [-0.2, +1.8] | +1.1 [-4.5, +6.3] | +3.5 [-0.2, +5.3] | +0.6 [-20.5, +13.8] | -12.4 [-16.8, -1.8] | +7.3 [+0.6, +13.3] | +1.6 [-1.1, +6.2] |
| 5300 | 960-979 | F2 | -0.1 [-0.5, +0.8] | -0.7 [-4.5, +3.3] | -0.3 [-2.2, +4.1] | -3.2 [-15.9, +8.6] | -23.4 [-28.2, -12.5] | -6.4 [-12.2, -0.2] | -0.3 [-1.9, +2.6] |
| 5300 | 960-979 | a333 | +0.1 [-1.0, +0.9] | +0.4 [-2.7, +6.7] | +2.2 [-2.9, +3.7] | -5.9 [-13.6, +25.6] | -61.4 [-72.8, -50.0] | -36.8 [-47.5, -29.9] | -9.1 [-10.3, -5.0] |

## What the bars decided

| Decision | Test | Outcome |
|---|---|---|
| V297 | F on seeds 930-949, V296 bar | Met at 5,300, 3 of 3; safety test applied in 1 of 39 comparisons |
| V298 | F on seeds 960-979, same bar | Not met: 1 of 3 at 5,300; under one vehicle separated 1 from 2 |
| V300 | F against p303 in 10 cells | 0 wins |
| V304 | F, G, H, B against the highest-flow pattern, seeds 650-669 | No setting passes |

These stand. The readings below came afterwards and cannot change them.

## Measured for the first time here

These are post hoc: chosen after seeing the data, not pre-registered.

1. **Door-to-door delay, the project's primary metric, had never been reported on this line, and no bar used it.** Against a000, p303 cuts delay by 29 % at 4,600 and 20 % at 5,300 on seeds 650-669.
2. **C's delay edge over p303 did not replicate.** At 5,300 it was +6.5, +5.3, +5.5 % on seeds 650-669, and +1.7, +1.1, -0.7 % on seeds 960-979, all three CIs including 0. On the mainline route alone, F0 is the only policy with a CI above 0 on both seed sets.
3. **C's extra TTC events are local to the merge lanes.** Against p303 at 5,300 on seeds 960-979: merge lanes -11, -12, -23 %, whole network +1, +7, -6 %. Network-wide it is a tie or slightly better on all three seed sets (930-949, 650-669, 960-979), except F2, clearly worse on 960-979. V298 and V304 used merge lanes only.
4. **Lanes are very unbalanced, under every controller.** On edge 3 at 5,300, p303: 1,212 / 1,790 / 1,952 veh/h on lanes 0 / 1 / 2. Lane 0 stays near 1,200 at both demand levels and for every controller checked. On 3a, lanes 0 and 1 crawl at 2-7 m/s beside lane 3 at about 25 m/s. No controller here has a lane action. This may be partly a simulation artefact: SUMO's lane-change behaviour here is not validated.
5. **At 4,600 flow is capped by demand.** p303 serves 99.4 %, so flow cannot separate good controllers there. Delay and safety can.

## Run ledger

| Run | Folder | Frozen code | Decisions | Status |
|---|---|---|---|---|
| A runs 1-3 | `run1`, `run2`, `run3` | `4b146b0`, `7b01783`, `2863282`, `47076bb` | V263-V272 | Slowed down, flow unchanged |
| Offset sweeps | `sweep1`, `sweep2`, `night/sweep` | `ae7b191`, `60ffd6d`, `b9ccc54` | V263 on | Fixed arms |
| Headway sweep | `headway1` | `08787b4` | V273-V274 | First efficiency room |
| V2V sweep | `v2v1` | `d992f92` | V275-V276 | About half to two-thirds of the gain survives |
| B run 4 | `run4` | `a325198` | V277-V278 | Abandoned after minutes |
| B run 4b | `run4b` | `11b3ebc` | V278-V279 | Did not beat the best fixed arm |
| B run 5 | `night/run5`, `night/run5b` | `b2928c7`, `539b65e` | V283 on | Failed: flow +0.2 to +1.5 % |
| C 1-5 | `night/c/train` to `train5`, validation `valC`, `valD`, `valE` | `51429bc`, `69f96ad`, `3aa49fc`, `4fdfc5d`, `f314bdd` | V286-V293 | **No per-vehicle reward reached training (V294)**; valid only as a shared-reward policy |
| C 6 | `night/c/train6` | `c1e0ac3` | V294-V295 | Stopped at 84 updates at 06:00; final weights not kept |
| C 7 = F | `night/c/train7`, `valF`, `freshF`, `robustF` | `c1e0ac3` | V296-V300 | Current C |
| G, H, B cfg 8, grid | `night/c8/*` | `b7c535a` | V302-V304 | No pass |

Launch commands for all of them are in `launchers.tar.gz`.

## Seeds

| Range | Use |
|---|---|
| 7,410,000-7,419,599 | Training, 400 per worker, workers 0-23 (B 0-8, C 9-17); reused between runs |
| 7,419,600-609 | Pattern grid, V302 |
| 7,419,610-649 | Approved in V302, unused |
| 7,419,650-669 | V304 test, then the instrumented re-run |
| 7,419,670-799 | Unused; proposed for the exploration, **not yet approved** |
| 7,419,800-899 | A runs, sweeps (V268-V276) |
| 7,419,900-929 | Earlier checks, run 4b |
| 7,419,930-949 | Validation, used many times |
| 7,419,950-959 | Tuning |
| 7,419,960-979 | Fresh check of p303, then F, then the instrumented re-run |
| 7,419,980-989 | Robustness map |
| 7,419,990-999 | Unused |

Exact use per seed for runs with rows: `seeds_used.csv`.

## Known gaps

- `*_config.json` in the C runs records the default environment, not the `--env` overrides. The safety weights are only in the launchers. Reward values confirm that they applied.
- The reward was calibrated knowing p303, so C matching p303 does not show it found that unaided.
- Seeds 930-949 and 960-979 have been looked at many times. Only unused seeds can support a claim.
- H1's collision at 4,600 is not traced. Earlier traced ones were crawl-speed contact behind an ALKS stopped at the end of 3a_0.
- No capacity drop on this plant. Realism of IDM at 0.8 s with a 0.5-s action step is unchecked.
- C's limits so far: headway is its only action, a 30-s clock, gamma 0.8 per 30-s decision looks about 150 s ahead (corrected in V309; the tagged version says 25 s).
- Free-flow numbers are bounds. The true ceiling is unknown.

## Reproduce one row

```
D=/home/catalin/work/phd/v5b1_runs/baseline_v0/b_train/code_b7c535a
unset SUMO_HOME; export OMP_NUM_THREADS=1; cd $D
PYTHONPATH=$D python <repo>/docs/research/baseline_v0/detail_run.py SPEC.json STORED_ROWS.jsonl OUT_DIR 2 F0 5300 7419650
```

`SPEC.json` is `detail_spec.json` in the full copy. The script prints how many rows equal the stored ones.
