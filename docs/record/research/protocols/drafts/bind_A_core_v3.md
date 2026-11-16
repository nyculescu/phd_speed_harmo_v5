# A bind check, core gate (draft v3, slim)

Status: draft for the author, 2026-11-01, per V248(4); nothing decided or run. The full v1 (`docs/research/protocols/drafts/bind_A_v1.md`) and `prior_art_A_v0.md` stay as reference. Tags: [A#] Claude assumption, approved with its decision (list at the end); [C] computed or read in code by Claude from stored runs (quick filter: 30-s intervals with e4 speed < 5 m/s; it differs slightly from V249's filter); [R] read by others, not re-checked; [VERIFY] unread or unchecked. On approval the criteria below are frozen (sha256 in a V-entry) before any run.

Question: on a BN4 family whose drop size ∆ is fixed and measured before any control result (V245), does a tuned CAV cap rule or an informed feed-forward cap beat no control (NC) by ≥ 10 % on door-to-door delay, and at which (∆, CAV share)?

## Plant geometry and policies (fixed before stage 0)

- Net bn4L: p1c `bn4` (lanes 4/4/4/2/1, nodes 0/100/410/550/830/985 m, 23 m/s [C]) with edge 1 lengthened from 100 to 1,100 m [A1], so every later node moves +1,000 m (4→2 drop at 1,550 m, 2→1 drop at 1,830 m). Reason [C]: E1's zones (`control.ZONES`, `ZONE_END` 892 m, taper about 234 m at `V_ALKS` 27.78 m/s) are v199 coordinates and cannot fit, with insertion at x = 0, upstream of the 4→2 drop on the 550-m net.
- Both drops use the row's merge type (zipper rows: zipper at both, as p1c; lane-end rows: laneend at both, as V180 stage 2 [R]). Stage 0, the null plant, the ladder and the gate all run on bn4L; the stored short-net runs below are context only.
- Zones in bn4L terms [A1]: ZONE_END_A = 1,250 m (300 m of recovery before the 4→2 drop, `RECOVERY_SPAN`); cap holds over E1's lengths, 300 m (short) or 508 m (long) before ZONE_END_A; commands start one taper earlier, taper = (v_ref² − (B_MIN v_ref)²)/(2 A_CAP) with v_ref = 23 m/s (about 160 m). MTFC b is relative to 23 m/s × sf, never `V_ALKS`.
- Teleporting off in every stage (V197, as B). Replaces "0 teleports": a stuck limit (stage 0) and a standing guard (gate).
- Seeds: SUMO seed = demand seed (common random numbers, as B).

## Stage 0: BN4 artefact and drop-mechanism check (first, V248(1))

Stored runs (short net, `calib_stage1_8c594f8/runs`, 0.5 s, V139 ramp, seeds 7,430,000-009, lcCoop 1, sd 0.1) [C]:
- zipper discharge is near-deterministic for every model: QDF seed-to-seed CV zip100 IDM 0.04 % (900 veh/h every seed, V249), zip20 IDM 0.03 %, zip100/zip20 EIDM 0.06-0.08 % (about 1,437), zip100 and zip20 Krauss 0.31-0.33 %; lane end IDM 1.9 % (median about 1,409), EIDM 1.15 %, Krauss 0.88 % but only 4/10 seeds queued;
- lane-end IDM a = 1.0 had 1 teleport on seeds 7,430,004, 007 and 008 (time-to-teleport 300) [C]; `calibration_stage1.json` marks it not artefact-free [R]; the likely cause is the V193 LC2013 lane-end artefact [R];
- V180 (Krauss): zipper QDF 1,954 at 0.5 s against 1,345 at 0.25 s; the junction model and the step set the zipper discharge [R]. All stored drops are max-based (V244); nothing exists at 0.25 s or on bn4L.

New runs (NC, human only; slow ramp: 10 min at 0.6 Q1, linear 0.75 → 1.15 Q1 over 160 min, 30-min hold; 10 seeds each). Q1 per (row, step): median pre-activation exit flow of a 3-seed V139-ramp pre-pass on bn4L (seeds 060-062) [A2]; it only scales the ramp.

| Row | Steps | Why |
|---|---|---|
| zip100 + IDM a = 1.0 (Flow) | 0.5, 0.25 | the D5.10 / P1 / P1b mechanism |
| zip100 + Krauss | 0.5, 0.25 | the V139/V147 plant |
| lane end + IDM a = 1.0, a = 2.6 | 0.5, 0.25 | no junction model; a = 2.6 at 0.25 s is the named IDM fallback |
| lane end + Krauss | 0.5, 0.25 | model contrast without the junction (fallback route) |
| archive build (optional): the D5.10 net and vtypes from `git show` | 0.5 | puts the D5.10/P1 label on a measurement, minutes of machine |

Estimator (v1 §2.3): activation t_b from excess accumulation between e4 and exit; PQ = mean exit flow over [t_b − 10, t_b) min, QDF = mean over [t_b + 5, t_b + 15) min, ∆̂ = 1 − QDF/PQ; no max. Null plant: the 2→1 merge replaced by a fixed-rate release-tracking signal, same ramp, estimator and t_b rule, at 0.8/1.0/1.2 × the median PQ of the rows meeting criteria 1-3 [A3], 20 seeds each. τ_null(n) = p95 of the bootstrap distribution of the median null ∆̂ at sample size n, from the nearest rate; n = 10 in stage 0, n = 20 in the ladder.

Criteria per row (fixed now; the criterion-1 floor sits between stored zipper and lane-end values, calibration data, disclosed):
1. non-degenerate: QDF CV across seeds ≥ 0.5 % and ≥ 4 distinct 30-s exit counts in the QDF window on ≥ 8/10 seeds [A4];
2. step-stable: |QDF(0.25)/QDF(0.5) − 1| ≤ 5 % and |median ∆̂(0.25) − median ∆̂(0.5)| ≤ 3 pp [A4]; failing only this → 5 seeds at 0.1 s (seeds 063-067); 0.25 and 0.1 agree within the same bounds → pass at 0.25 s;
3. valid: a sustained queue on ≥ 8/10 seeds; no vehicle standing > 300 s on ≥ 9/10 seeds [A5]; 0 SUMO collision events;
4. drop: the lower 95 % bound of the median ∆̂ > τ_null(10). Meeting 1-3 but not 4 → only usable as the ∆ ≈ 0 rung.

Route (D1, fixed now): the first of (a) a lane-end IDM row meeting 1-4 (knob: human IDM `a`), (b) the zip100 IDM row meeting 1-4, (c) the lane-end Krauss row meeting 1-4 (knob: Krauss `accel`, same grid). None → **A-UNTESTABLE(BN4)**: a defined result, reported, author told. Cost about 230 runs, about 0.4 h on 27 workers.

Archive re-read (read-only, after stage 0, logged in a V-entry): `git show claude/day-pattern-core:` `vsl_lab/plants/bn4.py`, `vsl_lab/netgen/bn4.py`, `vsl_lab/envs/bn4_env.py`, `vsl_lab/jobs/run_r6plus.sh`, `docs/lab/t1_meter_r6plus.md`, row D5.10 of `docs/plans/day_pattern_decisions_v0.md`; P1b `93ba655:v5b/d1/plant.py`, `netgen_bn4.py` (V112); the P1 commit from `v5b1_runs/P1_EVAL_STARTED.json` [VERIFY]. First look [C]: both set 0.5 s, Flow IDM (accel 1.0), zipper radius 20; R6+ ran in v6's `venv314`, SUMO version [VERIFY]. Rule: if the archive row (or zip100 IDM 0.5 s, if the row is skipped) fails criterion 1 or 2, D5.10 and P1/P1b are labelled "measured on a step-locked discharge". Nothing is re-run.

## Ladder (stage L)

- Knob (D1): grid {1.0, 1.5, 2.0, 2.6, 3.4} m/s² [A6], 10 calibration seeds, slow ramp, stage-0 estimator. Needs a V-entry that lifts V153 E2/E3 for A.
- At most 4 rungs: R0 ∆̂ ≈ 0 (negative control; the null plant if no setting gets there), R1 ≈ 5 %, R2 ≈ 10 %, R3 = the largest ∆̂ meeting criteria 1-3 (positive control). Pick: the median closest to the target, within ±2 pp (±5 pp for R3) [A6].
- Confirmation at p = 0, 20 fresh seeds: R1 and R2 lower 95 % bound > τ_null(20), R0 lower bound ≤ τ_null(20); adjacent rungs resolved by an unpaired bootstrap of the median difference (95 % CI excludes 0; each rung has its own demand), otherwise merged. PASS needs R1 or R2 plus R0 (or the null plant) and R3; otherwise A-UNTESTABLE(BN4). The map axis is the measured ∆̂, never the target.
- Per share (D4): PQ_r(p), QDF_r(p), ∆̂_r(p) and ô_c,r(p) on NC at 25/50/80 %, 10 seeds per rung (040-049). These, not the p = 0 values, scale each cell's demand and the C and O targets.
- R-V23 (V248(2)), report-only: the Vinitsky et al. 2023 set-up (prior art A §2) on 10 seeds, NC, with criteria 1-2; it is mapped as "artefact, not a rung" if it fails them; never gated.

## CAV contract (V248(3), shared with B)

- Same text as `bind_B_core.md` §3 (vType, actuator, restore, counters, share axis, label stream) with two stated differences: A's background is the bn4L humans (no trucks), and A issues no lane-change lock, so `lcmode_restore_mismatch` does not apply.

- Commanded CAV: the v199 ALKS vType (IDM, τ 1.6 s `fleet.ALKS_TAU`, v199 speedFactor draws), taken from `fleet.PLANTS['v199']` (`cav_models` alks IDM [C]; V209 trace [R]). Only the vType is used; the v199 geometry and other settings are not. A has no ACC/CACC: its non-ALKS vehicles are the bn4L humans (B's background is the v199 mix; V248(3) allows this).
- Actuator: `control.command(cap, v, own_max, dt=step)` with the step passed explicitly (the default `STEP` = 0.1 would make the taper 0.3 m/s² at 0.5 s [C]); `SumoALKS` gets a step parameter for its decel stats; unit tests at 0.1, 0.25 and 0.5 s. V226 exact restore; desired speed = min(own maxSpeed, sf × 23). Counters `cap_violations`, `restore_mismatch`, `allowed_mismatch` must be 0. O uses the same path and counters.
- Shares p ∈ {25, 50, 80} % of all vehicles, labelled from a separate RNG stream so departures and lanes match across shares. A null at 25 % alone is never a KILL.
- CAV step check (stage C0, per share, rung R2, seeds 070-079 [A7]): NC at the chosen step and at 0.1 s must meet criteria 1-2; plus an ALKS-only (100 %) NC run and a constant 14-m/s cap run, whose QDF and median |v − cap| of free capped ALKS agree within 5 % between the steps [A7]. A failing share runs at 0.1 s (about 5× its cost, author told); still failing against 0.05 s → UNTESTABLE(p).

## Core gate

Demand per cell (rung r, share p): 10 min at 0.6 PQ_r(p), 15 min up to 1.10 PQ_r(p) (D4), 30-min hold, 15 min down, 10 min at 0.6 PQ_r(p). Drain cap T_cap = max(hold start + 1.5 N/QDF_r(p), last departure + 60 min), N = vehicles in the demand file [A8]. Undrained (B's rule [A8]): an undrained or failed arm run takes the worst value of that arm over the cell's seeds or of all arms, whichever is worse; an undrained NC run drops the pair; > 2 of 20 dropped → cell report-only. > 10 % of NC runs undrained in a cell is flagged.

Primary outcome: mean door-to-door delay per vehicle = arrival − scheduled departure − own free-flow time, over every vehicle in the demand file, insertion queue included. Effect: rel = median of paired (D_NC − D_arm) / median D_NC; 95 % percentile bootstrap, 100,000 resamples, fixed RNG. TTT reported alongside (fixed window, unfinished vehicles counted to its end); emergency-braking events and the CAV deceleration p99 reported.

| Arm | Definition | Role |
|---|---|---|
| NC | CAVs at share p, never commanded | reference |
| C (D2) | V213 I-type MTFC on the ALKS: bn4L zone, feedback on the 2→1 drop-loop occupancy, setpoint ô_c,r(p); 6 K_I × 2 zone lengths (V213 Q1 values [A9]) plus constant caps {10, 14, 18} m/s: 15 laws per cell; lowest tuning median delay wins, ties within 1 % go to the simpler law, one grid-edge extension (V148) | the one tuned rule |
| O (D3) | informed feed-forward cap: knows the seed's scheduled departures and PQ_r(p) from ladder seeds. q_pred = forecast zone-entry flow over the next 5 min: departures shifted by the free-flow time to the zone, plus the current insertion backlog, released at the insertion edge's free-flow time. If q_pred > κ PQ_r(p), zone CAVs get max(v_min, v_ref κ PQ_r(p) / q_pred). κ ∈ {0.90, 0.95, 1.00}, v_min ∈ {5, 10} m/s, tuned on tuning seeds only [A10] | informed heuristic, not an upper bound |
| NCμ | NC, same seeds; at t = 600 s the first zone ALKS within 1 m/s of its maxSpeed gets a cap 0.5 km/h lower for 1 s, then exact restore (B's definition) | no-effect null (V244), every evaluation seed |

- NCμ divergence check (fixed now, as B [A11]): NCμ and NC arrival times differ by > 1 s for ≥ 80 % of window vehicles; else the perturbation repeats every 300 s on the first eligible ALKS; still failing → twin null: same demand file, SUMO seed + 5,000 (V213 Q4/Q5 style) [A11]. SUMO's IDM may have no dawdling term, so divergence is not assumed [VERIFY].
- Threshold (one estimator with B): per cell, θ = p95 of |rel(NCμ vs NC)| (20 pairs, 100,000 resamples, the gate's estimator); τ = max(10 %, θ); θ > 30 % → cell report-only [A11].
- Guards (one form with B): served throughput over [hold start, hold end + 15 min] blocks GO if the lower 95 % bound of the loss > g, g = max(2 %, p95 of |throughput change NCμ vs NC|) [A12]; NCμ's p97.5 of that change > 20 % → the guard is uninformative and blocks GO in that cell. Vehicles standing > 300 s not different from NC (two-sided 95 % CI).
- Collision rule (V211 gap: restricted, not fixed): no intrusion split; every SUMO collision event counts, with or without a same-lane bumper distance, so the lateral and junction events `day._bumper` cannot measure are covered. Any event in a gated run stops the batch for the author and is settled by replay (V209). Cost: a near-miss can stop a batch (disclosed).

Per cell (evaluation, n = 20). Family: C and O × R1, R2 × 3 shares = 12 tests; Pocock for 2 looks (nominal 0.0294, v1 D11 [R]) inside Bonferroni: 0.0294/12 two-sided per test, a 99.755 % CI at both looks. R0 and R3 cells are outside the family, read at unadjusted 95 % and disclosed as such.
- GO-C: rel ≥ τ, the family lower bound > 0, guards hold, no stop event. GO-O: the same for O, with C not GO.
- NO-ROOM: the 95 % upper bounds of both C and O < τ.
- UNCLEAR: otherwise; extended once to n = 40 (seeds 220-239) at the same Pocock level. Then: GO as above; NO-ROOM(15) if both upper 95 % bounds < 0.15 (no gain ≥ 15 % plausible, V213 Q7 form); else UNCLEAR, reported with the upper bound as the largest effect not excluded.
- Operating characteristics (V240), after tuning, before evaluation: simulate the full rule (looks, extension, KILL) from the tuning-seed NC delays and paired SDs (sensitivity range V241's 0.16-0.28). Targets (v1 [A13]): P(false A-GO | global null) ≤ 0.05; P(A-KILL | one cell at true rel 0.15) ≤ 0.10; P(A-KILL | global null) stated before data. A target failing at n = 20 → Claude computes the n that meets it and asks the author.

Share state: UNTESTABLE(p) (C0 step check); NON-BINDING(p) if T0-C fails at p; otherwise from its cells.

Overall (this plant family only):
- STOP (setup broken, never an outcome): smoke, T3, inert C ≠ NC, a counter ≠ 0, or a collision stop event before replay settles it.
- A-GO: GO-C or GO-O in at least one R1/R2 cell. GO-C: DRL must beat a strong tuned rule there; GO-O only: room for learning above C.
- A-NARROW: GO only at R3; the author decides whether A continues.
- A-KILL: no GO, and at 50 % and at 80 % the share is NON-BINDING or every R1/R2 cell is NO-ROOM or NO-ROOM(15). Labelled "strong" when C and O are also NO-ROOM at R3 at every share. Meaning: "this tuned cap rule and this informed feed-forward cap found no room here", not "no control has room" (the meter is not tested). UNTESTABLE at 50 % or 80 % → no KILL; reported.
- A-INCONCLUSIVE: anything else, with the upper bounds per cell.
- R0 GO: flagged as a non-drop channel (breakdown postponement), attributed before mapping; never counts for A-GO.

## Checks, smoke, launch, seeds, cost

- Ports before the smoke, each with a unit test, a V-entry and its source in the commit message: the CPU guard (`vsl_lab/ops/guard.py`, `tests/test_guard.py`, archive), the V170 empty-lane fix in `p1c/episode._mean`, the human `accel` knob in `plant.vtype_xml`, bn4L with edge 1 lengthened, the sustained estimator and null signal, `SumoALKS` with bn4L zones and an explicit step, NCμ and its divergence check, the collision-event stop, the standing count, drain cap and worst-value rule.
- Tool checks (fixed now). T0-C (the cap binds, per share): constant cap 10 m/s against NC at 0.95 PQ_r(p), R1 and R3, 5 seeds; the paired median change of zone density and of e4 inflow each has a 95 % CI excluding the NCμ value, and free capped ALKS track |v − v_c| ≤ 0.5 m/s in ≥ 90 % of their zone seconds [A14]. T3: 5/5 repeats identical. Inert C ≡ NC on 5 seeds.
- Smoke (V231), before every batch: one 60-min run per distinct (row, step, rung, share, arm); echo config and seed; read back car-following model, `accel`, step, merge type at both drops, teleport off; realised share within ±3 pp, departures and lanes identical to p = 0; law constants, and the occupancy input = mean of its non-empty loops; C and O acting; per-step decel of a commanded ALKS ≤ A_CAP; NCμ command log has one entry; the three counters at 0; wall-s per simulated s, re-costing the batch if needed.
- Launch: the guard running (> 90 % for 2 min pauses work), v6 idle or CPU < 15 %, own `systemd-run --user` unit, frozen detached worktree, ≤ 27 workers.

Seeds (proposed; author approval and a V-entry needed). 7,432,000-999 (V135 reserve): a grep of `docs/`, `v5b/`, `tests/` and run-file names under `~/work/phd` found only float digits and the v1 proposal [C]; B's core uses 7,431,110-190, no overlap.

| Range | Use |
|---|---|
| 000-009 | stage 0 (throw-away, disclosed) |
| 010-029 | null plant |
| 030-039 | knob calibration (throw-away) |
| 040-059 | ladder confirmation; 040-049 also per-share NC and R-V23 |
| 060-079 | Q1 pre-pass (060-062), 0.1-s step references (063-067), CAV step check (070-079) |
| 090-099 | smoke, T0-C, T3, inert C |
| 100-109 | tuning |
| 200-219 | evaluation |
| 220-239 | UNCLEAR extension |
| 300-999 | reserved |

Cost: rates [C] median 0.0018 / max 0.0042 wall-s per simulated s for IDM at 0.5 s on the short net (v1 [R] 0.0047-0.0083); budgeted at 0.005 (bn4L is longer), ×2 at 0.25 s, ×5 at 0.1 s, CAV runs 2-5 × [A15].

| Stage | Runs | Machine on 27 workers |
|---|---|---|
| Stage 0 + null + pre-pass + refs | about 230 | about 0.4 h |
| Ladder + per-share NC + R-V23 + C0 | about 320 | about 0.6-1.2 h |
| Smoke, T0-C, T3 | about 80 | about 0.2 h |
| Gate tuning (22 × 10 × 12) | 2,640 | 2.2-5.4 h at 0.5 s; 4.4-11 h at 0.25 s |
| Gate evaluation (4 × 20 × 12) | 960 | 0.8-2 h; 1.6-4 h |
| UNCLEAR extension (worst case) | ≤ 960 | ≤ 2 h; ≤ 4 h |

Total about 4-11 h at 0.5 s, or 7-21 h at 0.25 s, plus CPU-rule pauses; a share moved to 0.1 s by C0 adds up to about 5× its share of the gate.

## Author decisions (5)

- **D1 Plant, stage-0 route and drop knob.** Rec.: bn4L (edge 1 at 1,100 m), teleport off, the route order of stage 0 (lane-end IDM, then zip100 IDM, then lane-end Krauss; none → A-UNTESTABLE(BN4)); a V-entry lifts V153 E2/E3 for A. Pros: room for the E1 zones; no junction model in the preferred mechanism (V180); one continuous knob; lane-end IDM is the only stored IDM row with seed spread (CV 1.9 % [C]); stage 0 cannot end without a route. Cons: lane-end IDM a = 1.0 teleported on 3/10 stored seeds [C], so with teleport off it may jam (the stuck limit catches it); stored max-based lane-end drops were negative [R]; new geometry and code. Inferior: the short net (zones do not fit); zipper at 0.25 s (V180: the junction sets the discharge); an imposed-drop release signal (gain built in, the "gamable" risk of V245); EIDM/Krauss switching (no continuous knob).
- **D2 Tuned rule: the CAV zone cap C, not the meter.** Rec.: C. Pros: the same actuator as A's later DRL; one CAV contract with B (V248); fits the thesis title; the BN4 meter is a mainline signal and was KILLed in V147. Cons: E1-lite MTFC was 13-36 % worse than NC (V238), so a KILL is likelier and means only "caps found no room". Inferior: the meter (different actuator); both (breaks the one-rule core, doubles tuning).
- **D3 Oracle: the informed feed-forward cap O.** Rec.: O, with B_r (analytic point-queue no-drop bound, v1 §5) report-only. Pros: informed in the CLAUDE.md sense (hidden input → parameters tuned on tuning seeds); no per-seed choice. Cons: not an upper bound; new code. Inferior: the per-seed best grid point (noise-dominated, V238); the in-sample family maximum (optimistic); B_r as the oracle (about 45 % at ∆ = 5 % in v1's illustration, so the KILL would never fire).
- **D4 Shares and demand.** Rec.: p ∈ {25, 50, 80} %, NC per share; demand and C/O targets scaled per share from PQ_r(p), one level 1.10 PQ_r(p). Pros: meets V248's axis; separates a share effect from overload (at fixed p = 0 demand, ALKS gaps could make 80 % an overload, V189 [R]); 12 cells. Cons: headroom depends on demand (v1 illustration: about 60 % at 1.05 against 25 % at 1.25), so labels hold at 1.10 only; per-share calibration runs. Inferior: fixed p = 0 demand (confounded); {10, 40} % (fails V248); two levels (doubles the gate).
- **D5 Seeds, statistics and budget.** Rec.: 7,432,000-999 with the layout above; Pocock-in-Bonferroni looks, the OC step with its targets, NO-ROOM(15); about 4-11 h at 0.5 s (7-21 h at 0.25 s), re-cost stop after the smoke. Pros: fresh seeds, no overlap with B; the KILL is reachable and its probability is stated before data. Cons: uses part of the V135 reserve; NO-ROOM(15) is a weaker KILL, disclosed. Inferior: E1's unassigned 7,430,280-399 (too small); no OC step (A tends to end inconclusive).

Assumptions approved with their decision: D1: A1 bn4L length and zones, A2 Q1 pre-pass, A3 null rates, A4 criteria 1-2 bounds, A5 stuck limit, A6 knob grid and rung tolerances. D2: A9 C grid transfer, A14 T0-C tracking. D3: A10 O grid and q_pred. D4: A7 C0 step check, A8 drain cap and worst-value rule. D5: A11 NCμ divergence, twin offset and θ cap, A12 guard tolerance, A13 OC targets, A15 cost factors.

Review changes: bn4L geometry with E1 zones in BN4 terms, teleport off with a stuck limit and a named stage-0 route order, explicit step in `command`/`SumoALKS` plus a per-share CAV step check, and the v199 ALKS vType stated.
Per-share demand and targets; B's worst-value and guard forms; B's θ/τ null with a divergence check; T0-C with CIs and NON-BINDING toward the KILL; the R3 STOP removed (R3 NO-ROOM now strengthens the KILL); OC step, NO-ROOM(15) and Pocock looks.
τ_null at the n used, null rates from criteria 1-3, Q1 defined; 100,000 resamples, unpaired rung test, R3 level stated; q_pred, KILL wording, reported rows, archive row, seed pairing and A1-A15. B's core should adopt the NCμ-calibrated throughput tolerance g.
