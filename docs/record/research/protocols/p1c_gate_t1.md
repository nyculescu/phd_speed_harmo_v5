# P1c plant gate: plant v2 calibration and realism checks (T0, T1, T3)

**Status:** draft for author approval (V136). No run has been made on any seed of the V135 block.
**Line:** strengthened study P1c (`docs/research/strengthening_plan_v0.md`, V132-V135).
**Scope:** this page fixes the plant v2 choices, the calibration grid and rule, and the realism criteria *before* any calibration or tool-check run. The study protocol (statements, arms, tuning, evaluation) comes later, on its own page.

## 1. Fixed choices (not calibrated)

| Item | Choice | Reason (audit finding) |
|---|---|---|
| Topology | BN4: edges 4/4/4/2/1 lanes, nodes at x = 0, 100, 410, 550, 830, 985 m, 23 m/s; meter at node 3 across all 4 lanes | V133 S1; Flow / Vinitsky et al. 2018 geometry, cited |
| Lane changing | **on**, LC2013 (knobs in §2) | PLANT-F4, G2-F2 |
| Vehicles | one passenger type, all human-driven (no 10 % 'av' type) | G4-F4 (no reason for the AV type in this study) |
| Common random numbers | every vehicle's depart time, depart lane and speed factor are drawn from the demand seed and written into the route file; all arms read the same file | REPRO-F3 |
| Step | 0.5 s (stage 1); 0.25 s only in stage 2 | compute; EIDM is stated for 0.05-0.5 s |
| Amber | y = t_r + v / (2a), with t_r = 1 s, a = 3 m/s², v = 23 m/s → 4.83 s, rounded up to **5.0 s** (kinematic yellow-interval rule [VERIFY the ITE reference]) | PLANT-F3, F10 |
| Green, minimum red | 6 s, ≥ 2 s; cycle c(r) = max(13, 2·4·3600 / r) s with r = the **commanded rate** | G4-F5 |
| Rest in green | the signal rests in green whenever r ≥ r_cap = 2·4·3600 / 13 ≈ 2,215 veh/h | realistic activation |
| Rate floor | r_min = 0.4 × the measured queue discharge flow (QDF), rounded to 50 veh/h, fixed after T1 | G3R-F1 (Papageorgiou et al. 2008 use about 43 % of capacity) |
| Detectors | E1 loops on every lane of edge 4 (100 m after its start) and edge 5 (mid), plus an exit loop; 30-s periods aligned to the control grid; laws use the period occupancy (mean over the lanes of the chosen edge) | LIT-F5, detector part of G2-F2 |
| Warm-up | 300 s all-green (longer than a free-flow trip, about 45 s; a multiple of 30 s) | PLANT-F8 |
| End of horizon | demand stops at the end of control; **control stays active during the drain** (F3Z convention, `docs/architecture/interfaces.md:52`); cap 7,200 s | DRAIN |
| Delay | per vehicle: (arrival − desired departure) − route length / (speed factor × nominal speed limit); this includes the origin and meter queues and is measured against the nominal, not the incident-reduced, limit | PLANT-F7 |
| Window TTT | vehicle-time in network plus origin queue inside the control window, unfinished vehicles counted to the window end | COMETRIC |
| Safety counters | teleports, collisions (`--collision.check-junctions true`), forced stops at red (SUMO "emergency stop" warnings on the meter approach), emergency braking (≥ 9 m/s²) by edge | PLANT-F3, F13 |
| Incidents | **slowdown**: edge 5 speed limit 5 m/s; **lane closure**: lane 4_1 closed to all traffic (permission change), vehicles must change lanes; onset U(control start, + control/3), duration U(120, 480) s, from rng(seed + 3301) | PLANT-F4 |

## 2. Calibration (throw-away seeds 7,430,000-049, disclosed)

**Stage 1 grid** (54 configurations):

| Knob | Values |
|---|---|
| merge at nodes 4 and 5 | zipper, visibility 20 m · zipper, visibility 100 m (default) · lane end with forced lane change (priority node) |
| car following | IDM (a 1.0, b 1.5, T 1 s, s0 2 m: Flow defaults) · EIDM (SUMO defaults) · Krauss (SUMO defaults) |
| lcCooperative | 1.0 · 0.5 · 0.2 |
| speedDev of the speed-factor draw | 0.10 · 0.05 |

**Calibration run.** Clean day, no control (all-green), 10 seeds per configuration. Demand ramps from 1,200 to 2,400 veh/h over 20 min after the warm-up, holds 2,400 veh/h for 20 min, then stops. About 540 runs.

**Measurement (from the 30-s loop data, following the cumulative-count practice in `capacity_drop_lit_v0.md` §1):**
- **Breakdown:** the first time the mean speed at the edge-4 loops stays below 50 % of the free speed for 2 consecutive minutes.
- **Pre-queue flow:** the maximum 5-min exit flow before breakdown.
- **QDF:** the mean exit flow from 5 min after breakdown to the end of the hold, while the queue persists.
- **Drop:** 1 − QDF / pre-queue flow. A run without breakdown has no drop (recorded).

**Selection rule.**
1. Among the configurations that meet every T1 criterion (§3), on the calibration seeds, take the one with the fewest knobs away from the SUMO/Flow defaults.
2. If tied, take the drop closest to 7 % (HCM default [VERIFY]).
3. **Stage 2** runs only if no configuration passes: step 0.25 s; lcCooperativeSpeed {0, 0.5}; b {3.0, 4.5} m/s². Same rule.
4. If stage 2 also fails: **KILL plant BN4-LC** and fall back to a work-zone lane-drop plant (V133). The KILL is reported.

The calibration data are throw-away; they are reported as calibration, never as results.

## 3. Tool checks on fresh seeds 7,430,050-099 (criteria fixed here, before any run)

| Check | Criterion | Seeds |
|---|---|---|
| **T1a** capacity drop | median drop over seeds in [3, 20] %, and ≥ 75 % of seeds with a drop in that range | 050-069 (20) |
| **T1b** discharge | median QDF of the one-lane bottleneck in [1,770, 2,330] veh/h [VERIFY: the note's field range is in pcplph] | same |
| **T1c** artefacts | 0 teleports, 0 collisions (lanes and junctions) in every run, all runs drained | all T runs |
| **T1d** meter physics | forced stops at red < 1 % of approach-lane red onsets, in metered runs (constant rates 800, 1,200, 1,600 veh/h, clean and incident days) | 070-079 |
| **T1e** closure | the lane closure runs without teleports or stuck vehicles (H-R5), drains, and lowers the uncontrolled exit flow during the incident (paired, CI excluding 0) | 070-079 |
| **T1f** control matters | at the near-capacity demand, under at least one incident type, the best constant rate of a coarse grid (on seeds 070-079) beats no control by ≥ 10 % median delay on seeds 080-089. Otherwise **KILL** (CLAUDE.md early-KILL rule) | 070-089 |
| **T0** actuator binds | in undersaturated downstream conditions, realised meter discharge tracks the commanded rate (median within ±10 % for r in {800, 1,200, 1,600}); sim speed measured | 090-094 |
| **T3** determinism | the same spec run twice gives an identical result hash; two arms on one seed share every vehicle's depart time, lane and speed factor | 095-099 |

**Outcome.**
- All pass → plant v2 frozen (commit), and r_min = 0.4 × QDF is fixed.
- T1a/T1b fail on fresh seeds after passing in calibration → report it, and run stage 2 once.
- T1c-T1e fail → fix the code (not the criteria) and re-run on seeds 100-119.
- T1f fails → KILL.

## 4. What is reported

Every calibration configuration and its measurements; every tool-check run; the chosen configuration and why; any KILL. Raw runs go under `~/work/phd/v5b1_runs/p1c/`; summaries go in the repo.

## 5. Open points for the author

1. Confirm the T1 tolerances. The ranges come from desk research marked [VERIFY] in `capacity_drop_lit_v0.md`.
2. Confirm all-human traffic (the 10 % AV type removed).
3. Confirm the amber rule (5.0 s) and the rest-in-green rule.
4. Missing papers for WP2 (not needed for this gate): please download **Smaragdis, Papageorgiou & Kosmatopoulos 2004** (TR-B 38(3):251-270) and **Wang et al. 2014** (PI-ALINEA) into `papers/refs_papers/`. The AD-ALINEA and PI-ALINEA laws will be implemented from their equations, not from memory.
