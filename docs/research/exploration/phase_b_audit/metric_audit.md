# metric_audit: can the delay definition explain p333's lead or v3w's X1 edge?

Every number is EXPLORATORY (rows already read for verdicts). Statistic: median of paired differences, 95 % percentile bootstrap, 10,000 resamples, RNG 20261110, in % of the reference arm's median. "Arm" = per-seed mean of the 5 learners. "Stacked" = median over the 5 × n single-learner differences, seeds resampled together. No simulation ran.

## 0. Answer

- **The definition is sound.** `all_delay` is rebuilt exactly from other stored fields. No alternative definition reverses a sign in S, TRUCK, X1 or X2.
- **p333's tie in S and TRUCK is robust. Its lead over v3w in S is not.** It comes from the statistic, not the metric: a 5-run mean against one run on a right-skewed measure. That statistic's no-effect null is +1.31 % in S and +0.46 % in TRUCK, toward the single-run rule.
- **v3w's X1 and X2 edge is robust to the definition and to the statistic.** Its size depends on the window end, and truncation understates it.

## A. Definition (code)

- **Delay:** `all_delay = N − dist_step / 27.78` (plant_sweep.py:347, :31).
  - N: each second after 300 s, vehicles in the network plus vehicles past their departure time and not yet inserted; any road, any class (b_env.py:427-429).
  - Distance: speed × 0.1 s, every vehicle, every step after 300 s (plant_sweep.py:123, :130-134).
- **Window:** 300 s warm-up without rule actions, then 1,500 s; demand constant to 1,800 s (b_env.py:102, :152-153, :179-185).
- **Unfinished vehicles** count up to 1,800 s, with credit for distance covered. Later delay is not counted (b_env.py:462).
- **Insertion:** fixed drawn lane, `departSpeed="max"` (fleet.py:365-366). A waiting vehicle counts 1 veh-s per second. None is dropped: `max-depart-delay` defaults to −1 (SUMO MSFrame.cpp:474) and is not set (day.py:133-137).
- **Trucks** are held to 100 km/h although capped at 25 m/s (fleet.py:29, :151-153).
- **Removal:** teleport off, `collision.action warn` (day.py:134-135).
- **Served flow:** `passed` = vehicles first seen on edge 4, 1 Hz (b_env.py:434-441); `arrived` = exits (b_env.py:417). **TTT** = N (plant_sweep.py:29).
- **`delay`, `delay_ramp`, `delay_ramp2`:** means over vehicles that departed and left inside the window, against their own speed factor (plant_sweep.py:326-337). Unfinished vehicles are left out (18 % in S). Not the headline (planb.md:326).
- **Per-road keys:** 1-Hz vehicle-seconds and metres by road group, insertion queues by route (measure.py:244-269, :306-313).

## B. Reconstruction (S, seed 7,480,400)

| Run | `all_delay` stored | Rebuilt from 13 road groups, 1 Hz | Residual |
|---|---|---|---|
| p333 | 138,827.93 | 138,822.21 | +5.73 |
| v3w learner w0u250 | 129,418.70 | 129,414.45 | +4.25 |
| no control | 239,810.22 | 239,794.75 | +15.47 |

- N equals the sum of the road groups exactly (591,287; 582,399; 684,311). Step distance equals the sum of the three class distances.
- Over 5,280 runs (11 arms, S and TRUCK): N residual 0; 1-Hz residual −47 to +66 veh-s.
- Not rebuildable from per-vehicle keys: `delay` × finished gives 111,757 veh-s for p333. The rows hold nothing for unfinished vehicles or those inserted before 300 s.

## C. Sensitivity

**S and TRUCK, 240 seeds. X against p333, % of p333's median; positive = p333 better.**

| Measure | S: v3w arm | S: v3w stacked | S: 3E-C | TRUCK: v3w arm | TRUCK: v3w stacked | TRUCK: 3E-C |
|---|---|---|---|---|---|---|
| `all_delay` | +1.57 [+0.55, +2.62] | +0.13 [−0.74, +0.98] | +2.09 [+0.69, +3.08] | +0.25 [−0.46, +0.78] | −0.13 [−0.65, +0.28] | +1.28 [+0.48, +2.06] |
| TTT | +0.32 [+0.11, +0.53] | +0.05 [−0.12, +0.21] | +0.36 [+0.11, +0.63] | +0.06 [−0.07, +0.19] | −0.02 [−0.15, +0.11] | +0.30 [+0.12, +0.49] |
| Per vehicle passed | +1.58 [+0.38, +2.72] | +0.13 [−0.85, +1.07] | +2.19 [+0.51, +3.50] | +0.21 [−0.60, +0.78] | −0.35 [−0.91, +0.17] | +1.53 [+0.88, +2.39] |
| Own speed, finished vehicles | +1.92 [+0.92, +3.06] | +0.29 [−0.73, +1.25] | +1.89 [+0.65, +3.41] | +0.31 [−0.29, +0.94] | +0.02 [−0.59, +0.52] | +1.29 [+0.40, +1.91] |
| Merge roads 3a + 4a | +4.33 [+0.22, +8.26] | −0.20 [−4.14, +2.48] | +1.52 [−3.52, +5.60] | −0.77 [−3.81, +2.02] | −3.17 [−5.26, −0.43] | −2.07 [−5.96, +0.71] |
| `passed` | +0.02 [−0.04, +0.10] | −0.05 [−0.09, +0.00] | +0.05 [−0.05, +0.09] | −0.14 [−0.23, −0.07] | −0.14 [−0.23, −0.05] | +0.18 [+0.07, +0.34] |

- In-network delay without insertion queues: within 0.15 of the headline in every column. Cars and ALKS only (arm): +1.64 [+0.70, +2.69], +0.24 [−0.41, +0.87]. Without lane-end stopped seconds (arm): +1.57 [+0.57, +2.79], +0.48 [−0.07, +0.85].
- Halves, edges 2 to 4a plus ramp queues (the only per-minute data), v3w stacked: S +0.87 [−0.22, +2.03] then +0.46 [−1.40, +2.32]; TRUCK +0.78 [−0.07, +1.57] then −1.12 [−3.02, +0.44].
- No control: +56.00 [+54.73, +59.14] (S), +41.87 [+40.08, +43.19] (TRUCK); at least +10.02 on every delay-type alternative.
- os0_10_10: 0.00 [0.00, 0.00] in S on every definition; it has p333's exact `all_delay` on 34 % of S seeds. Mean of paired differences −0.82 [−1.92, +0.31]. TRUCK: 0.00 [−0.01, +0.07].
- 3E-C's deficit also holds on the mean: +2.50 [+0.53, +4.50], +1.99 [+1.03, +3.03].
- v3w arm, mean of paired differences: S −0.31 [−1.74, +1.15], TRUCK −0.55 [−1.24, +0.10].

**X1 and X2, round 2 test, 40 seeds. v3w against X, % of X's median; positive = v3w better.**

| Measure | X1: p333 | X1: 3E-X1 | X2: p333 | X2: os0_10_10 | X2: 3E-X2 |
|---|---|---|---|---|---|
| `all_delay` | +5.48 [+2.91, +7.98] | +7.78 [+4.05, +11.30] | +6.12 [+3.38, +7.36] | +2.43 [−0.62, +7.49] | +3.03 [+0.75, +5.41] |
| TTT | +1.78 [+0.74, +2.54] | +2.50 [+1.36, +3.54] | +1.87 [+0.90, +2.30] | +0.70 [−0.23, +1.95] | +0.83 [+0.18, +1.62] |
| In network | +6.27 [+2.82, +8.17] | +7.76 [+4.15, +10.82] | +6.05 [+3.44, +7.34] | +2.49 [−0.59, +7.47] | +3.08 [+0.87, +5.51] |
| Own speed, finished | +5.47 [+2.08, +7.09] | +7.21 [+3.52, +10.54] | +5.73 [+2.80, +6.83] | +2.30 [−0.91, +5.03] | +2.35 [+0.42, +5.28] |
| Without lane-end stopped seconds | +5.09 [+2.46, +7.59] | +7.85 [+4.11, +11.23] | +5.53 [+2.71, +6.79] | +2.45 [−0.63, +7.19] | +2.89 [+0.82, +5.41] |
| `all_delay`, stacked | +5.24 [+2.62, +7.45] | +8.16 [+5.60, +10.69] | +4.69 [+2.54, +7.28] | +3.34 [+0.25, +5.51] | +2.56 [+1.16, +4.74] |
| `passed` | +0.96 [+0.74, +1.51] | +0.88 [+0.22, +1.69] | +1.41 [+0.95, +1.78] | +0.31 [−0.31, +0.70] | +0.64 [+0.31, +1.25] |

- Per vehicle passed: at or above the headline in all five columns. Cars and ALKS only: within 0.9 of it.
- 120 seeds, X1 against p333: +4.24 [+2.57, +5.54]; stacked +3.64 [+2.09, +5.37]; mean +3.76 [+2.42, +5.09]; TTT +1.25 [+0.76, +1.73].
- Ramp-route means, X1 against p333: ramp 1 +2.74 [+0.60, +7.10], ramp 2 +12.28 [+6.71, +20.31]. A main-route mean cannot be formed: no finished count per route.
- Halves, edges 2 to 4a, X1 against p333: +4.08 [+1.04, +7.01] then +12.94 [+8.17, +16.10].

## D and E. Candidates

| # | Candidate | Evidence | Verdict |
|---|---|---|---|
| i | Truncation | Unfinished at 1,800 s, v3w − p333 (stacked): S 0.0 [−1.0, +2.0], TRUCK −2.0 [−4.0, −1.0] vehicles; no control − p333 +73.5 and +76.0. X1, X2: p333 − v3w +1.06 [+0.56, +1.21] and +1.43 [+0.89, +1.82] points of planned vehicles. The arm with more delay always has the larger backlog (Spearman +0.57 to +0.89). | Understates every difference. Could favour p333 in X1 and X2. No reversal. |
| i-b | Window end | X1, veh-s upstream of edge 4, p333 − v3w, window ending at 600 / 1,200 / 1,800 s: 0 [−120, +180] / +3,990 [+1,020, +5,880] / +12,150 [+7,140, +17,760]. TRUCK, last 5 minutes, edges 2 to 4a, v3w − p333 (stacked): −3.31 % [−6.27, −0.60]. | X1's percentage is a function of the window. A longer TRUCK window could favour v3w; size unknown. |
| ii | Insertion | Main origin queue under p333: 4,404 veh-s. v3w − p333 (stacked): −14.0 [−30.0, +4.0] (S), −2.0 [−19.0, +13.0] (TRUCK). No control − p333: +51.5 [+19.5, +85.5], +70.5 [+48.0, +86.0]. Ramp queues 126-131 veh-s in every arm. | Equal offset, 3.5 % of p333's S delay. |
| iii | 100 km/h for trucks | Offset at least 3,739 veh-s (2.9 %). v3w − p333 (stacked): +0.7 [0.0, +1.3] (S), +1.7 [+0.3, +3.2] (TRUCK). The 10 capped trucks are the same in every arm (perturb.py:103-115); rows do not separate them. | Equal offset. |
| iv | Lane-end stops | Counted like any stopped vehicle. Median stopped seconds: S 468 (p333), 422 (v3w); TRUCK 968, 629. X1: +1,280 [+1,011, +1,593] more under p333, of a delay difference of +13,288. | No definitional effect. The queue behind them is plant behaviour (PR-28), not tested here. |
| v | Gate | No class or leader test in either counter (b_env.py:427; plant_sweep.py:130-134). | No effect. |
| vi | Removal | Teleports 0 in all 6,080 extracted runs. Collisions: 1 in 5,280 S6 runs, 1 in 800 round 2 test runs; not removed. S6: 1 stuck vehicle in one p333 run and in its twin lr1000_10_1; 0 dropped. | No effect. |
| vii | Pooled arm | Null: mean of four learners minus the fifth, each in turn. S +1.31 % toward the single run, 3 of 5 intervals above 0. TRUCK +0.46, 2 of 5. X1 −0.04 (one interval below 0), X2 +0.58 (none clear). Within-seed SD across learners: 7.1 % (S). | Favours p333 and every single-run rule in S and TRUCK. It equals p333's S lead. |
| viii | Served flow | The arm with less delay never passes fewer vehicles (tables). | Consistent. |
| ix | Offsets | Under p333 in S, `all_delay` is 22 % of TTT. Reference-speed offset 9.5 % (an_delay_floor.md §4, not recomputed). | Equal offset. It shrinks every percentage alike, so fixed-percent bars depend on it. |

- Caveat on vii: the learners are not identical policies, and the null uses four runs, not five.
- INFERENCE: planb.md:462 and :484-485 describe label-swap nulls. A swap makes the two arms exchangeable, so it cannot show this asymmetry. I did not read that code.
- S6's verdict does not change: W needs v3w shown below every opponent, and the unbiased forms show a tie.

## Verdict

p333's tie on delay in S and TRUCK holds under every definition the rows support: TTT, in-network delay, per served vehicle, own-speed reference, cars only, merge roads, with or without lane-end stopped seconds. p333's lead over v3w in S does not hold: with single learners it is +0.13 [−0.74, +0.98], and the arm-level +1.57 matches the statistic's null. The same bias sits in every arm-level delay figure against a single-run rule, for example an_delay_floor.md §2 (S total, p333 − v3w, −1,988 [−3,303, −693]). Stacked, in TRUCK, v3w is lower on road 4a (−4.38 % [−7.57, −1.29]) and higher on road 3 (+1.31 % [+0.73, +1.93]). v3w's X1 edge holds under every definition and all three statistics. What stays open is not the metric: the window end, and the lane-end behaviour at merge 2.

## Files

`/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit2/`: scripts `ext.py`, `meas.py`, `recon.py`, `sens_s6.py`, `s6b.py`, `sens_x.py`, `window.py`; outputs `sens_s6.out`, `s6b.out`, `sens_x.out`, `window.out`.

Not available: per-minute N for the whole network in S6; per-vehicle records; planned counts in the round 2 rows.
