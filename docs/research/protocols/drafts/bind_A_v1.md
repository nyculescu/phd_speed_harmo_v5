# A bind check: does control have room on a drop ladder? (protocol draft v1)

Status: draft for the author, 2026-11-01, revised after a design review the same day. Nothing here is decided or run. Every number marked [A] is a Claude assumption or choice for review; [VERIFY] means not read in full or not yet checked; [R] means a figure the reviewer read from stored runs that this revision did not re-check. When approved, the criteria in §2.0-§8 are frozen (sha256 recorded in a V-entry) before any run.

## 1. Purpose

Before any DRL on track A (V246), answer one question cheaply: on a synthetic plant family whose capacity-drop size ∆ is fixed as an axis before any control result (V245), does control have room to beat no control (NC) by ≥ 10 % on the primary metric, and at which (∆, d), where d is the demand level? Control here means CAV speed harmonization (a driving algorithm acting through CAV speed caps) and a meter.

The check is a screen. Its output is a label per (∆, d) cell (GO, ROOM, NO-ROOM-F, NO-ROOM, UNCLEAR), an analytic headroom bound per cell, and the smallest ∆ with room. It is not a thesis claim. Confirmation needs fresh seeds and its own protocol.

## 2. Plant family

### 2.1 Base geometry: recommend BN4 (p1c `bn4`), not v199 ramp32

| Criterion | BN4 (`v5b/p1c/plant.py`, lanes 4/4/4/2/1, zipper 100 m, step 0.5 s) | v199 ramp32 (`v5b/fleet/corridor.py`) |
|---|---|---|
| Cost | IDM runs: median 0.0047 wall-s per simulated s per process, max 0.0083 (stage-1 store, 2,700-s runs, 24-way concurrency) [R]; Krauss about 0.0008 [R] | about 0.11 (task context), so about 13-23 × more |
| Drop controllable | to be shown: stage 0 (§2.0) must first prove the discharge is not a step artefact. The V139/stage-1 table spans 2.5-54 % for the configurations used, and also holds negative values (lane-end Krauss −75 %, lane-end IDM −17 %) [R]; all were max-based estimates (V143, V244) | no drop distinguishable from noise (V244); calibrating a drop was rejected (V245) |
| Bottlenecks | one active (2→1), no off-ramp | merge plus lane drop, interacting (V190); the lane drop was active on 20/20 days (V244) |
| Reproduction target | same network family as Vinitsky et al. 2023 (prior art C4, §2) | different network |
| Actuators already tested | release-tracking meter, T0 realised/commanded 0.996 (V147); ALINEA / PI-ALINEA code (`feedback_t1g.py`) | ramp meter (E1), ALKS caps |
| Fit for "ramp meter" | no on-ramp: the meter is a mainline all-lane signal at node 3, as in Vinitsky's traffic-light baseline | true on-ramp meter |

Recommendation: BN4, subject to stage 0. It has one bottleneck, so ∆ is the only lever (prior art §6.3), and the Vinitsky plant lands on the same map.

Costs of this choice, disclosed:
- the "ramp meter" of A becomes a mainline bottleneck meter, and no result transfers to on-ramp merges (B needs its own geometry);
- **∆ on this plant depends on the step and on SUMO's zipper junction model** (V180). In the stored stage-1 runs (zip100, IDM a = 1.0) every seed discharged exactly 7 or 8 vehicles per 30 s, i.e. 900.0 veh/h, one vehicle per 8 steps, with no seed-to-seed variance [R]. The 50-54 % drop of V139 may therefore be a junction-timing artefact. Stage 0 tests this before any knob is accepted;
- the network is short (985 m), so the origin queue is mostly an insertion queue. The primary metric counts it.

Our edge 2 is 310 m. The Vinitsky code uses 410 m (prior art §2). The ladder keeps the p1c `bn4` geometry, because its actuator passed T0. The Vinitsky set-up enters as a measured report-only rung R-V23 (§2.4). [D1]

### 2.0 Stage 0: discharge isolation and non-degeneracy (new; before stage 1)

Purpose: show that each candidate knob setting produces a queue discharge with real variability, not a step lattice. Inferred risk (not checked): QDF values sit on a lattice of about 3600 / (k · 0.5) veh/h (900, 1029, 1200, 1440, 1800), so ∆ would jump in steps of about 13-20 pp and the 5-18 % targets would be unreachable.

Runs (seeds §9, V139 ramp, 2,700 s, NC), for each candidate setting:
- the BN4 zipper at step 0.5 s and at 0.25 s;
- a 1-lane discharge from a fixed red-to-green signal (start-up discharge headways, no junction merge);
- a no-junction alternative: a lane end on edge 4 instead of the zipper (same lanes otherwise).

Measured per setting: the headway distribution at the exit loop during sustained discharge, the 30-s exit counts, the per-seed QDF.

Pre-registered criteria for a setting to enter stage 1 [A]:
1. at least 3 distinct 30-s exit-count values in the discharge window on ≥ 80 % of seeds;
2. seed-to-seed CV of QDF ≥ 1 %;
3. step stability: |median ∆̂(0.25 s) − median ∆̂(0.5 s)| ≤ 5 pp.

If fewer than 4 settings with ∆̂ ≤ 20 % pass, stage 1 does not start; Claude reports and the author chooses the route [D9]: another knob (IDM `startupDelay` [VERIFY that SUMO 1.27.1 applies it to IDM], or the Krauss/IDM pair that already gave about 5.5 % on Krauss zip100, V147), or the no-junction geometry. The a = 1.0 point is a positive control only if it passes criteria 1-3.

### 2.2 Drop knob: human IDM acceleration `a`

- Human cars: IDM with the Flow parameters except `a` (b 1.5, T 1.0 s, s0 2.0 m, δ 4; `plant.vtype_xml`, where `accel` is hard-coded to 1.0 today, so the knob needs a code change), speedDev 0.10, lane changes on (LC2013, lcCooperative 1.0), zipper 100 m, step 0.5 s.
- Candidate knob `a` ∈ {1.0, 1.3, 1.6, 2.0, 2.6, 3.4, 4.5} m/s² [A]; only settings that pass stage 0 go on.
- Why this knob:
  - one continuous parameter inside one car-following model;
  - in the standard IDM, the equilibrium speed-gap relation does not contain a or b, so `a` should mainly move queue discharge and not free-flow capacity. SUMO's implementation is [VERIFY]; stage 1 measures it.
- Why not the V139 configurations: they switch between models (Krauss, EIDM, IDM), leave a gap between 12.4 % and 50 % with no artefact-free setting (the EIDM rows fail artefact-free in `p1c_calibration_stage1.json`), and were measured with the max-based statistic and the min(e3, e4) detector (V143, V244).
- Conflict to resolve: V153 E2/E3 (a closed plant and knob list) forbid a new knob. Adopting `a` needs an author V-entry. [D2]
- Each knob-to-∆ map is fitted on calibration seeds only and frozen before any control run (V245).
- Known limits: a = 3.4 and 4.5 m/s² are unrealistic accelerations, accepted only as synthetic rungs; a low `a` may also produce jam waves. A's axis is the standing-queue drop (prior art §6.4); jam-wave discharge is reported separately.

### 2.3 T1 drop estimator, with a like-for-like null (V244)

Measurement (NC only, one run per seed). BN4 loops: `e4` (edge 4, 100 m), `exit` (edge 5, −15 m); the zipper lies between them (`plant.py` loop table).
- **Activation t_b at the bottleneck**, not 180 m upstream: excess accumulation X(t) = N_e4(t) − N_exit(t) − X_ff, where N are cumulative counts over all lanes and X_ff is the median of N_e4 − N_exit over the first 10 min (free flow at 0.6 Q1). t_b is the first 30-s mark at which X stays ≥ X* for 4 consecutive intervals, with X* = max(10 veh, 3 × the SD of X over the first 10 min) [A]. Oblique cumulative exit curves are plotted for every run as a check.
- **Statistic.** PQ = mean exit flow over [t_b − 10 min, t_b); QDF = mean exit flow over [t_b + 5 min, t_b + 15 min); ∆̂ = 1 − QDF / PQ. Both are 10-min means of the same exit counter. No max is taken.
- **Estimator validation** (stage-1 pass 2): report the lag between t_b(X) and the old `up`-loop rule, and check that exit flow over [t_b − 10, t_b) has no step down inside the window (median of the last 2 min ≥ 0.97 × median of the first 8 min) on ≥ 80 % of runs [A]. If this fails, the window is shortened to 5 min before stage 2.
- **Valid run.** X stays ≥ X* through t_b + 25 min. Otherwise "no sustained queue", counted and reported.
- **Demand for T1 (slow ramp).** 10 min at 0.6 Q1, then a linear ramp from 0.75 Q1 to 1.15 Q1 over 160 min, then a 30-min hold at 1.15 Q1. Q1 is the setting's median pre-queue flow from pass 1 (V139 ramp, `calibrate.profile`, 5 seeds).
- **No-drop null, like-for-like.** Same geometry, with the 2→1 zipper replaced by a fixed-rate release-tracking signal at rate R0 (its discharge is the same with or without a queue, so ∆ = 0 by construction). Same slow ramp, same estimator, same windows, same t_b rule, so it carries the pre-queue Poisson noise, the surge-triggered onset selection and the activation lag. R0 ∈ {0.6, 0.8, 1.0} × the median Q1 of the stage-1 settings plus one at the Q1 of the highest-∆ setting [A]; 20 seeds each.
  - **τ_null(r)** is the 95th percentile of the bootstrap distribution of the median null ∆̂ at the stage-2 n, taken from the R0 nearest to rung r's Q1 (not pooled across rates).
  - Disclosed limit: a signal may discharge more regularly than a queue; the 30-s count variance of null and rungs is reported side by side.
  - The old in-queue placebo ∆̂⁰ is kept as a report-only diagnostic.
  - τ_null is frozen at the end of stage 1, before stage 2.
- **Rung tests** (stage 2, fresh seeds): *has a drop*: the lower 95 % bound of the median ∆̂ is above τ_null(r); *∆ ≈ 0*: the CI of the median ∆̂ includes 0 and the median is below τ_null(r).
- **ô_c,r** (critical occupancy, used by M and C): the median e4/e5 occupancy over [t_b − 10, t_b) at the activation estimator, from stage-2 NC runs.
- **Reported, not tested:** PQ, QDF, breakdown probability within the hold, the in-queue speed variance (a jam-wave proxy), and the max-5 V139 statistic next to its own null.

### 2.4 Ladder

- **Candidate targets** ∆ ≈ {0, 3, 5, 7, 10, 14, 18, 30, 50} % [A] (spares at 3, 7, 14). The highest rung that passes stage 0 is the **positive control** P5 (prior: tuned controllers gained 21-43 % on a plant with a 40-54 % drop, V139, V116; D5.10 found +49 % against NC there; both on the plant now under the §2.1 artefact suspicion). The ≤ 20 % rungs cover the field range quoted in prior art §3 (3-18 %, Han et al. 2026).
- **Stage 1 selection** (calibration seeds): per target, the knob setting whose median ∆̂ is closest, tolerance ±2 pp for targets ≤ 10 % and ±5 pp above [A]. A target with no setting inside tolerance is dropped and disclosed. No new knob search.
- **Fallback** if no setting reaches ∆ ≈ 0: the ∆ ≈ 0 rung is dropped and the negative control is the §2.3 null plant run under control arms [D3].
- **Power, fixed before stage 2:** from the stage-1 pass-2 per-run SD of ∆̂, n per rung is the smallest of {20, 30, 40} giving ≥ 80 % power (resampling simulation) to resolve adjacent rungs. Adjacent rungs that cannot be resolved at n = 40 are merged before stage 2 (keep the one nearer its target).
- **Stage 2 ladder PASS** (fresh seeds, CRN by seed across rungs):
  1. every run is artefact-free (0 physical contacts per V211, 0 teleports, all valid);
  2. ≥ 75 % of seeds per rung have a sustained queue;
  3. each rung passes its rung test (§2.3);
  4. the medians increase along the ladder, and the 95 % CI of the paired median difference of each adjacent pair kept after merging excludes 0;
  5. **≥ 3 rungs with ∆̂ ≤ 20 %** (including ∆ ≈ 0 if it exists), plus the positive control [D14].

  Rungs that fail are dropped from the map and disclosed. If criterion 5 fails, stop for the author.
- **The map axis** is the stage-2 measured median ∆̂ with its CI, never the target value.
- **R-V23** (report-only): the Vinitsky set-up from prior art §2 (fork geometry with edge 2 = 410 m; IDM 2.6 / 4.5 / T 1.0 / minGap 2.5; step 0.5 s; lane changes off), ∆̂ from the same estimator on 20 ladder seeds, plus the stage-0 non-degeneracy rows. The paper-text conflict (Krauss against IDM) stays logged.
- **T1b** (field QDF range [1,770, 2,330] veh/h per lane) is report-only for synthetic rungs [D4].

## 3. CAVs and shares

- CAVs are **human twins** [A]: the vType parameters of the rung's human car, so in NC a CAV drives like a human and the share changes actuator authority only. CAVs with sourced ACC/CACC gaps cut capacity by about 17 % (V189), which would move ∆ with the share (prior art §6.7); excluded here. [D5]
- **Labels from a separate stream:** u_i from `default_rng(seed + 104729)` [A], drawn after all other per-vehicle draws; a CAV is u_i < p. `plant.Demand` already uses `rng(seed)` and `rng(seed + 7919)`, which stay untouched, so lanes, speed factors and departures are identical across shares and the shares nest (CRN). P1b checks it.
- Shares p ∈ {10 %, 40 %} [A], bracketing Vinitsky's 5-40 %; 25 % optional [D6]. Meter and NC run at p = 0. A share whose T0-C fails is dropped and disclosed.

## 4. Demand

- Clean days, no incidents. Poisson arrivals with per-vehicle lane and speed factor drawn from the seed (`plant.Demand`, CRN).
- **Demand is a second axis**, d ∈ {1.05, 1.20} [A], both binding [D7]. On a synthetic plant no level is "realistic", and the headroom depends on d about as much as on ∆ (reviewer's point-queue illustration at ∆ = 5 %: about 60 % at d = 1.05, 45 % at 1.10, 25 % at 1.25). Profile per rung, scaled by its stage-2 median PQ_r:
  - 10 min at 0.6 PQ_r; 15 min up to d · PQ_r; a 30-min hold; 15 min down to 0.6 PQ_r; 10 min at 0.6 PQ_r.
- **Drain cap per rung:** T_cap,r = hold start + max(1.5 × N_total / QDF_r, time to last departure + 60 min) [A], fixed from stage-2 values before stage 3. At the highest rung QDF_r may lie below 0.6 PQ_r (about 900 against 1,080 veh/h on the a = 1.0 point), so NC stays congested to the end of demand; the old 60-min cap was marginal there.
- **Undrained runs** are that arm's failure on that seed (V6), not invalid: unfinished vehicles get their delay censored at T_cap,r, the count of undrained runs per arm and cell is reported, and a cell where > 10 % of NC runs are undrained is flagged. `episode.run` today marks undrained runs invalid and caps at 7,200 s; the A code changes both (§7 smoke).

## 5. Arms

All arms are tuned per (rung, d) cell on the tuning seeds only (n = 10). Selection: lowest median door-to-door delay; a tie within 1 % goes to the law with fewer nonzero gains; a best setpoint on an outer grid edge extends the grid once by one step (V148 rule).

| Arm | Definition | Role |
|---|---|---|
| NC | meter at rest in all green; CAVs uncontrolled | reference |
| M | ALINEA (30 laws) and PI-ALINEA (60 laws), V148 gains, on e4 or e5 occupancy; release-tracking actuator (V141); r_min = 0.4 × QDF_r; **r_max,r = 1.1 × d × PQ_r** [A], above the peak demand so the rest state never binds, and r starts at r_max,r. Setpoints ô_c,r × {0.7, 0.8, 0.9, 1.0, 1.1} [A] (V154 grid-coverage lesson). Plus **constant rates** {QDF_r + j (PQ_r − QDF_r)/4, j = 0..4} ∪ {1.05 PQ_r} [A], active over the ramp-up, hold and ramp-down, resting in green otherwise | tuned meter, informed per cell (the CLAUDE.md lookup I) |
| C(p) | Zone speed harmonization: CAVs on edges 2-3 get the cap min(v_c, 23 · sf_i) through `vehicle.setMaxSpeed`; at rest (v_c = v_free) no call is made, and on leaving the zone each CAV's own max speed is restored. Updated every 30 s: v_c ← clip(v_c − K_I (o − ô) − K_P (o − o_prev), v_min, v_free), o the e5 occupancy. Grid: ô ∈ ô_c,r × {0.8, 0.9, 1.0}; (K_P, K_I) ∈ {(0, 0.5), (1.0, 0.5), (2.0, 1.0)} m/s per pp; v_min ∈ {5, 10} m/s; 18 laws. Plus **constant caps** v_c ∈ {10, 14, 18} m/s over the same window [A] | tuned simple CAV rule, per cell and share |
| MF | The M law tuned at the reference rung, applied unchanged at every rung (same d). Reference rung: the rung whose measured median ∆̂ is closest to 7 %, ties to the lower one | report-only: adaptation reference; T2 gap G_r = rel(M) − rel(MF) |
| O_r | The maximum, over the union of all M and C(p) laws in the cell, of the tuning-seed rel (in-sample, n = 10). No per-seed choice, no evaluation data | family-optimistic value, used by ROOM |
| B_r | **Analytic no-drop bound:** per seed, the delay of a point queue that serves the actual demand file at PQ_r with no drop (no simulation), B_r = median paired (D_NC − D_PQ) / median D_NC with its bootstrap CI. It ignores pre-bottleneck noise and lane imbalance [A] | headroom: H_r = B_r − best tuned rel, with CI |

- **Oracle disclosure.** O_r bounds only the declared families and only in expectation. B_r is a bound on what any controller could gain if it removed the drop entirely; no arm is known to reach it. A per-seed oracle is report-only (V238). A full-grid oracle on the evaluation seeds would add about 200-400 process-hours at the IDM rate [D8].
- **Not in the check:** a combined M + C arm, an MPC (it would have to model hysteresis, prior art §6.6), CAVs with sourced gaps or higher acceleration, and DRL.

## 6. Metrics

- **Primary:** mean door-to-door delay per vehicle = arrival − scheduled departure − free-flow time (free-flow time uses each vehicle's own sf × 23 m/s), over all vehicles in the demand file, censored at T_cap,r (§4). It includes the insertion and meter queues. Co-headline: served throughput, exits per hour over [hold start, hold end + 15 min].
- **Effect:** rel = median of paired differences (D_NC − D_arm) / median D_NC, 95 % percentile bootstrap CI over seeds (10,000 resamples, fixed RNG seed): the E1 convention (`e1_lite.md`). Bootstrap p-values for §8 use the same resamples (100,000 when Holm needs the tail).
- **Alongside:** TTT over the fixed window (start to T_cap,r), unfinished vehicles counted to the window end.
- **Safety side constraints:**
  - physical contacts must be 0 (V211 contact/intrusion split, ported, §7); any contact stops the batch for the author;
  - minGap intrusions are counted; an arm above NC (paired CI excluding 0) gets a safety flag;
  - teleports must be 0; emergency braking and the CAV deceleration p99 are reported;
  - a contact or teleport makes the arm invalid for that cell; an undrained run is a failure, not invalid (§4).

## 7. Launch preconditions, tool checks, placebos and smoke check

**Launch preconditions** (every batch; the launch script refuses to start otherwise):
- the CPU guard ported from the archive (`vsl_lab/ops/guard.py`, with `tests/test_guard.py` passing): pause rules > 90 % for 2 min (CLAUDE.md);
- v6 sessions idle, or system CPU load < 15 % if that cannot be determined;
- the batch runs in its own `systemd-run --user` unit, from a frozen detached worktree at the run commit (no commits there mid-run);
- ≤ 27 worker processes (task brief; CLAUDE.md caps at 100 and plain runs at 32) [VERIFY the V-entry that set 27].

**Code ports before stage 0**, each with a unit test and one V-entry: the V170 empty-lane fix (`episode._mean` maps −1 to 0 today via `max(fn(i), 0.0)`; empty loops must be excluded); the V211 contact/intrusion split (`day._bumper` in `v5b/fleet`; p1c counts raw SUMO collisions); the knob in `vtype_xml`; the per-rung r_max; the C cap rule of §5; the drain cap and censoring of §4; the separate label stream of §3.

| Row | Check | Criterion (fixed now) |
|---|---|---|
| T0-M | Meter delivers the command: constant rates {0.4, 0.6, 0.8} × QDF_r at 2 rungs (lowest and highest ∆) × 5 seeds | realised/commanded within 0.97-1.03 (V147 range) |
| T0-M2 | The feedback meter binds in time: the mid law (ô = ô_c,r, middle gains) at d = 1.20, 2 rungs × 5 seeds | r enters [r_min, PQ_r] before the median NC t_b of the same seeds on ≥ 4/5 seeds |
| T0-C | The CAV cap binds, at **every** share used: constant v_c = 10 m/s against NC, 2 rungs × 5 seeds, near-capacity demand 0.95 PQ_r | over the hold: paired median change in zone density and in the flow arriving at the 2→1 merge (e4 count), each with a 95 % CI excluding 0 (the P1a inert runs give the no-effect value, 0); plus median ∣v − v_c∣ ≤ 0.5 m/s for free CAVs in the zone [A]. A share that fails is dropped |
| T3 | Determinism | 5/5 repeats identical |
| P1a | Inert arms: the meter code active but resting in green; C at rest (no setMaxSpeed call) | identical to NC on every seed (5 evaluation seeds per rung) |
| P1b | Label placebo: NC with 40 % CAV labels against NC with none | identical trajectories; if not, the label stream is fixed before any control run (no fallback) |
| P2 | Drop-estimator null (§2.3, null plant) | defines τ_null(r) in stage 1 |
| P3 | ∆ ≈ 0 rung (or the null plant, §2.4) as the negative control | prediction: NO-ROOM or NO-ROOM-F. A GO or ROOM there is flagged as a non-drop channel (breakdown postponement, prior art §6.3) and attributed before mapping |
| P4 | Best-of-K selection null for O_r: sign-flip the paired differences jointly across all laws of the cell (10,000 flips), take the maximum rel | p95 frozen per cell before the labels are read |
| P5 | Positive control (highest rung passing stage 0) | prediction: GO or ROOM. If it fails, STOP: the check is broken |

**Smoke check (V231)**, before every batch, from the launch script; it stops on any failure. One 60-min run per distinct (rung, d, arm family, share) in the job list. Each must:
- echo its rung, d, seed, share, arm and law;
- read back the vType `accel` from libsumo;
- show a realised CAV share within ±3 pp, and identical departures and lanes to the p = 0 run;
- read back the meter constants, including r_max,r;
- show that each law's occupancy input equals the mean of its non-empty loops over its window at every update;
- show that the controller acted (at least one non-rest command);
- show that the C cap of each CAV equals min(v_c, 23 · sf_i) while active;
- pass P1a on one seed.

The smoke also measures wall-s per simulated s. If IDM runs cost more than 0.0083 or CAV runs more than 0.024 (§10), Claude re-costs the batch and asks before stage 3.

## 8. Decision rules, fixed before data

**Stage order:** launch preconditions and code ports → smoke → T0/T3/P1 → stage 0 (isolation) → stage 1 (calibration, null plant) → stage 2 (ladder PASS) → stage 3 (tuning, rungs from the highest ∆ down; P5 is read first, and a P5 failure stops the rest) → **operating characteristics** → stage 4 (evaluation) → ROOM replication.

**Operating characteristics (new, as V240), after stage 3 and before stage 4:** simulate the full §8 rule from the stage-2 NC delays and the stage-3 tuning paired SDs (sensitivity range: the V241 SDs 0.16-0.28). Targets [A]: P(false A-GO | global null) ≤ 0.05; P(A-KILL | one cell with true rel 0.15) ≤ 0.10; P(A-KILL | global null) reported. If a target fails at n = 20, Claude computes the n that meets it and asks the author before stage 4.

**Per cell (r, d)**, labels from evaluation seeds, in this order:
1. **GO:** some tuned arm (M or C(p)) has evaluation rel ≥ 0.10 and is significant (rel > 0) after **Holm across all arm families × cells** (M, C10, C40 × rungs × d), on bootstrap p-values at a nominal α of 0.0294 per look (Pocock, 2 looks).
2. **NO-ROOM-F** (these families cannot realise 10 %): O_r < 0.10, or every tuned arm's evaluation CI upper bound is < 0.10.
   - **NO-ROOM:** NO-ROOM-F and the upper CI of B_r < 0.10 (no room for any controller under the point-queue bound).
3. **ROOM:** O_r ≥ 0.10 and above its P4 p95, the best tuned arm's upper CI ≥ 0.10, and B_r's lower CI ≥ 0.10. ROOM counts towards A-GO only after **replication**: the top 5 laws of the cell by tuning rel re-run on fresh seeds (n = 20); replicated if their maximum rel is ≥ 0.10 and above its own P4 p95 (K = 5).
4. **UNCLEAR:** otherwise. Extended once to n = 40 at the same Pocock level. If still UNCLEAR, reported with the best arm's upper CI as the largest effect not excluded (V240 rule 2). UNCLEAR is never a KILL.

Labels are also reported per family (M; C at 10 %; C at 40 %). ∆*(d) is the smallest measured ∆̂ with GO or replicated ROOM.

**Track A** (applies to this plant family only):
- **STOP (check broken):** stage 0 or the ladder PASS fails without an author route, P1a or P1b fails, or P5 is NO-ROOM-F.
- **A-GO:** at least one cell with ∆̂ ≤ 20 % is GO or replicated ROOM. The DRL phase may be planned (its own protocol), ROOM cells as the main targets, GO cells as "DRL against strong tuned".
- **A-NARROW:** GO or replicated ROOM only at ∆̂ > 20 %. The author decides whether A continues as a map whose paying region lies above the field range [D3].
- **A-KILL:** every eligible cell below the positive control is NO-ROOM-F (CLAUDE.md early KILL: no tuned arm reaches 10 %) [D13]. Cells where B_r ≥ 10 % are listed as "family-limited"; reopening them needs an author V-entry with a new pre-registered arm, not DRL directly.
- **Inconclusive, no GO:** no GO or replicated ROOM, and at least one eligible cell UNCLEAR or unreplicated ROOM.
- **CAV framing:** if C is NO-ROOM-F in every cell while M has room, Claude reports that CAV actuation has no room here and asks the author about A's CAV framing.

**Reported, not decided:** monotonicity of the best tuned rel in ∆ (Jin & Jin 2015 predict growth with ∆ and none at ∆ = 0 in a macroscopic model; prior art C2) [VERIFY]; H_r and B_r per cell; G_r; R-V23's position; served throughput and TTT.

## 9. Seeds (author approval and a V-entry needed before any use)

Proposed fresh sub-block 7,432,000-7,432,999, inside the reserved part of the V135 block. A grep of `v5b1_runs`, `docs`, `v5b` and `tests` for a seed field equal to 7432xxx found nothing [R]; three trip files under `v5b1_runs/pilot_20261013/` contain the digit string 7432xxx, probably not as seeds [VERIFY]. A full seed check runs before first use. 7,100,000-7,399,999 are never used.

| Range | Use |
|---|---|
| 7,432,000-004 | stage 1 pass 1 (V139 ramp; throw-away, disclosed) |
| 7,432,005-009 | stage 0 isolation (throw-away) |
| 7,432,010-029 | stage 1 pass 2 (slow ramp; throw-away; power for stage 2) |
| 7,432,030-049 | null plant (sets τ_null) |
| 7,432,100-114 | T0-M, T0-M2, T0-C (100-109), T3 (110-114) |
| 7,432,140-149 | smoke (throw-away) |
| 7,432,200-239 | stage 2 ladder PASS (n up to 40), R-V23 on 200-219 |
| 7,432,300-309 | stage 3 tuning (n = 10) |
| 7,432,400-419 | stage 4 evaluation (n = 20) |
| 7,432,420-439 | second look, UNCLEAR cells only |
| 7,432,450-469 | ROOM replication |
| 7,432,500-999 | reserved for A follow-ups (each use needs its own V-entry) |

## 10. Cost (re-costed at the IDM rate)

Rates [R]: IDM median 0.0047, max 0.0083 wall-s per simulated s per process; CAV runs assumed 2-5 × IDM (0.0094-0.024) [A], measured by the smoke. Run lengths: slow ramp 12,600 s; peaked day about 8,000 s with the per-rung drain cap [A]; V139 ramp 2,700 s. Assumes 8 rungs × 2 d levels.

| Stage | Runs | Process-hours (median rate; max rate) |
|---|---|---|
| Smoke, T0, T3, P1 | about 150 | 2; 3 |
| Stage 0 | about 105 | 1; 1 |
| Stage 1 and null plant | about 305 | 4; 7 |
| Stage 2 (8 × 30 + R-V23 20) | about 260 | 4; 8 |
| Stage 3 meter (8 × 2 × ≤ 110 laws × 10) | ≤ 17,600 | 184; 325 |
| Stage 3 CAV (8 × 2 × 21 laws × 2 shares × 10) | 6,720 | 140-351 (2-5 ×); 620 |
| Stage 4 and ROOM replication | about 2,400 | 31-51; 92 |
| **Total** | **about 27,500** | **about 370-600; up to 1,050** |

On 27 workers: about 14-22 h of machine at the median rate, up to about 39 h at the max rate, plus CPU-rule pauses and analysis between stages. The two big items are the meter grid and the d axis (each doubles stage 3) [D16]. The same design on v199 (0.11) would cost roughly 15-25 × more.

## 11. What the result feeds

- **A's operating map:** the stage-2 ∆ axis (measured) × d, the per-cell labels, rel CIs for M and C(p), B_r and H_r, ∆*(d), G_r and the safety rows. These form the classical layer of the map (V153 G2-G3, revised). Map cells claimed later need fresh seeds and a confirmatory protocol.
- **DRL phase:** only after A-GO. It selects the cells and shares (replicated ROOM first) and sets the opponents (tuned M and C per cell, MF for the adaptation gain).
- **The Vinitsky reproduction (G1):** R-V23 places the target plant on the ladder with A's estimator, replacing the inferred ≈ 33 % (prior art §2). The tuned M at the nearest rung says whether "AV-RL = ALINEA at 40 %" sits in a GO, ROOM or NO-ROOM-F cell. Proposed scope: this check blocks new DRL training on the ladder, not the replay of the stored Vinitsky checkpoints [D12].
- **B:** no direct feed (different geometry). The CAV-cap T0 code, the label stream, the label placebo and the V211 counters are reused.

## 12. Assumptions and caveats (summary)

- [A] Knob values, ladder targets and spares, tolerances, the stage-0 floors, X*, the CAV and constant grids, r_max,r = 1.1 d PQ_r, d ∈ {1.05, 1.20}, the drain cap, the 7 % reference rung, the OC targets, the 2-5 × CAV cost factor, the 60-min smoke runs, the label-stream offset.
- [R] The 900 veh/h degenerate discharge, the IDM wall-time rates, the negative V139 entries, the empty seed grep: read by the reviewer from stored runs, not re-checked in this revision.
- [VERIFY] SUMO's IDM equilibrium independence of a, b; `startupDelay` with IDM; Vinitsky's driver model and geometry (prior art §2); the 7,432xxx digit hits; the source of the 27-worker limit; Jin & Jin 2015.
- O_r is an in-sample value over the declared families only; NO-ROOM-F means "these families cannot realise 10 %", which is what the CLAUDE.md early-KILL rule tests. B_r is analytic and approximate, not an arm.
- Synthetic rungs make no field-realism claim (V245). ∆ on this plant depends on the step and the junction model, disclosed. The axis is fixed and measured before any control result.

## Author decisions needed

Each: recommendation, then pros / cons, then inferior alternatives and why.

- **D1 Geometry.** Rec.: BN4 p1c `bn4`, subject to stage 0. Pros: cheap, one bottleneck, T0-tested meter. Cons: mainline meter, not an on-ramp; ∆ is step- and junction-dependent. Inferior: v199 (no drop, 13-23 × cost); the Vinitsky 410-m geometry as the ladder base (its actuator has no T0).
- **D2 New knob `a`.** Rec.: approve `a` in a V-entry that lifts V153 E2/E3 for A. Pros: one continuous parameter in one model. Cons: needs a code change; may be lattice-bound (stage 0 decides). Inferior: the V139 model switches (12.4-50 % gap, max-based estimates).
- **D3 No ∆ ≈ 0 rung, and A-NARROW.** Rec.: use the null plant as the negative control; for A-NARROW, decide after the map is seen, with the field range stated up front. Pros: keeps a ∆ = 0 reference by construction. Cons: the signal is not a queue. Inferior: dropping the negative control (no check on non-drop channels).
- **D4 T1b report-only.** Rec.: yes. Pros: synthetic rungs cannot match field QDF by design. Cons: no realism anchor. Inferior: binding T1b (fails every high rung by design).
- **D5 CAVs as human twins.** Rec.: yes. Pros: share changes authority only, ∆ fixed. Cons: no sourced CAV dynamics. Inferior: sourced ACC gaps (moves ∆ with the share, about −17 % capacity, V189).
- **D6 Shares.** Rec.: {10, 40} %. Pros: brackets Vinitsky, halves CAV cost against three shares. Cons: no mid point. Inferior: adding 25 % (+50 % CAV cost before any room is shown).
- **D7 Demand axis.** Rec.: d ∈ {1.05, 1.20}, both binding, tuned per cell. Pros: labels no longer hinge on one arbitrary level. Cons: doubles stages 3-4. Inferior: one level with a source-backed rule (none found in this search); tune at one d and evaluate at two (confounds retuning with d).
- **D8 Full-grid evaluation oracle.** Rec.: no. Pros: saves about 200-400 process-hours. Cons: no out-of-sample family bound. Inferior: running it (B_r and ROOM replication cover most of its use).
- **D9 Stage-0 failure route.** Rec.: first the no-junction lane-end geometry with the `a` knob; second the Krauss zip100 point (about 5.5 %, V147) as one low rung. Pros: removes the junction model from the mechanism. Cons: new geometry needs its own T0. Inferior: `startupDelay` with IDM (support unverified); going ahead on a lattice (unreachable targets, degenerate nulls).
- **D10 Null plant.** Rec.: fixed-rate release-tracking signal under the same slow ramp. Pros: ∆ = 0 by construction with the same lag and onset selection. Cons: may discharge more regularly than a queue (reported). Inferior: the in-queue placebo (lacks lag, selection and demand noise, V244).
- **D11 Second look.** Rec.: Pocock nominal 0.0294 at both looks, inside Holm. Pros: controls α across looks. Cons: slightly less power at look 1. Inferior: unadjusted second look with disclosure (inflated α); no second look (more UNCLEAR cells).
- **D12 Vinitsky replay scope.** Rec.: this check blocks new DRL training on the ladder only, not replay of stored checkpoints. Pros: G1 can proceed in parallel. Cons: replay results may be read before the map exists. Inferior: block everything (delays G1 with no gain in rigour).
- **D13 Role of B_r in the KILL.** Rec.: keep the CLAUDE.md early KILL binding on tuned arms (NO-ROOM-F everywhere → A-KILL); list B_r ≥ 10 % cells as "family-limited", reopenable only by a V-entry with a new pre-registered arm. Pros: no rule bending; KILL stays reachable. Cons: may kill a plant where per-CAV DRL could realise room. Inferior: let B_r count as the informed oracle (by the reviewer's illustration B_r is about 45 % at ∆ = 5 %, so the KILL would almost never fire wherever ∆ > 0).
- **D14 Ladder size.** Rec.: spares at 3, 7, 14 % and require ≥ 3 rungs ≤ 20 %. Pros: one lost rung no longer stops the check. Cons: more stage-1/2 runs (about +5 process-hours). Inferior: 4 rungs with no spares (fails by design if one rung drops); 3 rungs with no spares (thin map).
- **D15 Seeds.** Rec.: approve 7,432,000-999 with the §9 layout, in a V-entry, after the full seed check. Pros: fresh, inside the reserved block. Cons: uses part of the reserve. Inferior: the E1 reserve 7,430,280-399 (too small for the layout).
- **D16 Cost.** Rec.: accept about 14-22 h of machine (median rate), with a re-cost stop if the smoke measures more. Pros: full design. Cons: up to about 39 h at the max rate. Inferior: halve the meter grid to one occupancy sensor (saves about 90 process-hours but reopens the V154 grid-coverage risk); one d level (see D7).
- **D17 Meter upper clip.** Rec.: r_max,r = 1.1 × d × PQ_r, r starting there, disclose that V149 used 9,600 veh/h. Pros: the meter can bind before breakdown (T0-M2 checks it). Cons: one more assumption. Inferior: r_max in the tuning grid (3 × meter cost); keeping 9,600 veh/h (handicaps M, biases towards KILL).

## Changes from review

- B1 degenerate discharge: fixed. New stage 0 (§2.0) with headway, signal and lane-end isolation runs and three pre-registered non-degeneracy criteria; disclosure in §2.1; the a = 1.0 positive control is conditional on stage 0; route on failure is D9.
- B2 biased T1 estimator and non-like-for-like null: fixed. Activation from excess accumulation between e4 and exit (§2.3), estimator validation on pass 2, null from a fixed-rate signal plant under the same ramp and estimator, τ_null per rate, not pooled.
- M1 meter clip: fixed. r_max,r = 1.1 × d × PQ_r, start at r_max,r, T0-M2, V149 disclosure (D17).
- M2 CAV rest state: fixed. Cap min(v_c, 23 · sf_i), no call at rest, own max speed restored; P1a restated; smoke checks the cap.
- M3 false-GO control and A-KILL logic: fixed. OC simulation before stage 4, Holm across families × cells, ROOM needs fresh-seed replication, A-KILL only when every eligible cell is NO-ROOM-F, all-UNCLEAR is "inconclusive, no GO".
- M4 O_r not a bound: fixed. Analytic B_r and H_r added; NO-ROOM split into NO-ROOM-F and NO-ROOM; ROOM needs B_r ≥ 10 %; B_r's role in the KILL put to the author (D13), with the recommendation to keep the CLAUDE.md rule binding.
- M5 demand level: fixed. d is a binding second axis with 2 levels (D7); labels per (∆, d).
- M6 T0-C: fixed. Every share, density and merge-arrival flow at 0.95 PQ_r, no-effect value from P1a; a failing share is dropped.
- M7 ladder power: fixed. n per rung from the pass-2 SD of ∆̂, merging of unresolvable rungs, spares at 3/7/14 %, criterion 5 relaxed to 3 rungs (D14).
- M8 drain cap: fixed. Per-rung cap from QDF_r, undrained runs as failures with censored delay, re-costed at 8,000-s days.
- m1 constant rivals: fixed. Constant rates in M, constant caps in C, inside O_r and GO.
- m2 batch hygiene: fixed. Launch preconditions (guard port and test, v6 idle or < 15 %, systemd-run, frozen worktree, ≤ 27 workers); the 27-worker source marked [VERIFY].
- m3 V170 and V211 not in p1c: fixed. Listed as code ports with unit tests and a V-entry, checked by the smoke.
- m4 IDM cost: fixed. §10 re-costed at 0.0047-0.0083; the total grew to about 370-600 process-hours mainly because of the new d axis and constant rivals (D16).
- m5 seeds and second look: fixed. Approval and V-entry required before use; Pocock 0.0294 per look (D11); new ranges for stage 0, null plant and replication.
- m6 label RNG: fixed. Separate stream rng(seed + 104729) after all other draws; P1b has no fallback.
- m7 definitions: fixed. ô_c,r defined at the activation estimator; MF rung by a fixed rule (closest to 7 %, ties low); V139 range statement corrected with the negative entries [R].
- Not fixed: the reviewer's figures read from stored runs (900 veh/h, wall times, negative V139 entries) were not re-checked here; they are marked [R] for checking before freeze.
