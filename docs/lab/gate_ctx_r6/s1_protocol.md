# Context-aware R6 gate, S1: BN4 plant realism and meter authority with loop detectors (pre-registration)

*Committed 2026-10-04 before any S1 run, including smoke runs. Branch `claude/vsl-lab-core`. Gate: README §7 of `docs/review/design_space/`.*

## 0. Authorisations and context

**Seed block, approved by the author.**
- Approval: Catalin, 2026-10-04, relayed by the lead session (phd-speed-harmo-v6-a1). The wording was "You continue your work", given after the lead recommended the block and option B.
- The block is **7,180,000–7,180,999**, with the Lead 1 role layout:
  - 000–099 plant / realism;
  - 100–299 tuning / MPC fit;
  - 300–499 validation;
  - 500–699 test;
  - 700–999 reserved confirmatory.
- The ledger showed no use of 7,180,xxx before this commit.

**Scope: option B with a HARD STOP.** The author approved a driver-variant family on BN4 geometry, gated in a fixed preference order. If no variant passes, S1 ends as outcome C ("the BN4 family is not realism-capable"), and the gate stops before S2.

**R6 disclosures, carried into every later document of this gate** (S0, `report_S0_20261004-1430.md`):
1. R6's protocol says "lr 3e-4 with decay". The trainer ignored `--lr-decay` for RecurrentPPO, so R6's learners trained at a constant 3e-4.
2. R6's learners fail the roadmap's C1 convergence check: final vs best +10.7 / +7.9 / +6.7 %, and entropy 0.10–0.21 nats against a 0.35 floor. The R6 claim stands as run, because its checkpoint was chosen on validation seeds.

**What was known before this protocol, disclosed:**
- BN4 with R6's vTypes (`t1_bn4_plant_checks.md` T1, 0.5 s step, lane changing off, 20-s exit-loop medians) peaks at 1,044 veh/h at q = 1,300 and settles at about 900 veh/h for q ≥ 1,400. The ratio is 0.862.
- **So variant B0 is expected to FAIL R-c (discharge),** whose floor is 1,600 veh/h/lane.
- No data exist for B2 or B3 on BN4.

## 1. Plant and variants

**Geometry:** BN4 as in R6 (`vsl_lab/netgen/bn4.py`):
- 4 → 4 → 4 → 2 → 1 lanes; zippers at x = 550 and 830 m; length 985 m; speed limit 23 m/s (82.8 km/h); TLS meter at node 3 (x = 410);
- lane changing **off** for every vType, as in Vinitsky et al. 2018 and R6. Lane connections i → i // 2 make lane changes unnecessary.

**Simulation:**
- step 0.5 s, `--time-to-teleport 300`, demand Poisson at a constant rate q from t = 0, `departLane="random"`, `departSpeed="10"` (all as in R6);
- **AV share 10 %,** drawn with the existing per-vehicle common-random-number draw. AVs are uncontrolled and use the variant's base car-following model with speedFactor exactly 1 (as R6's AVs).

**Variants, in preference order** (the first PASS becomes the S2/S3 plant):

| # | ID | Human vTypes | Source of values |
|---|---|---|---|
| 1 | **B0** (R6 plant) | IDM a 1.0, b 1.5, T 1.0 s, s0 2 m, δ 4, length 5, speedFactor normc(1, 0.2, 0.2, 2.0); AVs as R6 | Flow defaults, as R6. Reported; expected FAIL (§0) |
| 2 | **B2** (EIDM, SUMO defaults; H5-style) | `carFollowModel="EIDM"` with **no other car-following attribute set**, so every parameter, including accel, decel, tau, minGap, length, the EIDM error terms and the speed distribution, is SUMO 1.27's passenger default | SUMO defaults; no value chosen by me |
| 3 | **B3** (S2 population mix, nominal centre) | §1.1 | ad hoc, plausible orders of magnitude [VERIFY against driver-heterogeneity literature] |

### 1.1 B3: driver-population mix at its nominal centre (this also pre-registers S2's centre point)

**Base model:** EIDM; error terms at SUMO defaults. Each human class is a set of per-vehicle sampled vTypes. Attributes not listed stay at the SUMO default.

| Class | Weight among cars (centre) | accel (m/s²) | decel (m/s²) | tau (s) | minGap (m) | speedFactor |
|---|---|---|---|---|---|---|
| timid | 0.30 | 2.0 | 4.0 | 1.3 | 3.0 | normc(0.95, 0.08, 0.6, 1.3) |
| normal | 0.40 | 2.6 | 4.5 | 1.0 | 2.5 | normc(1.00, 0.10, 0.6, 1.5) |
| assertive | 0.30 | 3.2 | 5.0 | 0.8 | 1.8 | normc(1.08, 0.10, 0.7, 1.6) |
| truck (share of all vehicles 0.10) | — | 1.2 | 3.5 | 1.5 | 3.0 | normc(0.95, 0.05, 0.8, 1.1); length 12 m, maxSpeed 25 m/s |

**Speed compliance:** a share **p_nc = 0.20** of cars (any class) is non-compliant. Their speedFactor is replaced by normc(1.20, 0.10, 0.8, 1.8). This is the lab's normc compliance pattern.

**Per-vehicle sampling:** every car and truck draws accel, decel, tau and minGap as the class value × an independent U(0.85, 1.15) factor.
- **Mechanism:** if SUMO 1.27 accepts distribution strings for these attributes natively, that is used. This is checked in the S1 tool check, §4.1. Otherwise, each run generates **20 sampled vTypes** per (class × compliance) cell and per truck class from `rng(seed + 7)`, inside one `vTypeDistribution` id `human`.
- **Probabilities:** the distribution's probabilities give cars and trucks their shares among non-AV vehicles. Trucks are 0.10 / 0.90 of non-AVs, so 10 % of all vehicles; the rest are split by class weight × compliance.
- **Health count:** every run counts spawned vehicles per class from their departed vType ids.

**Lane-change parameters are not a population axis on BN4,** because lane changing is off (§1). Varying them would be inert, which is exactly the trap the R-0 check exists for. This is a deviation from the session brief, decided before any data. If the author wants lane-change heterogeneity, a lane-changing BN4 variant needs its own realism gate. (T1-L, run in `t1_bn4_plant_checks.md` and not part of this gate, had a drop ratio of 0.698, outside R-a.)

## 2. Loop detectors (E1): positions and aggregation

**New 10-s E1 loops** go in a separate additional file (`bn4.loops.add.xml`), loaded only when loops are enabled. They do not change the R6 network or its detectors.
- **Positions** are in lane coordinates of the netconvert lanes, one loop per lane, upstream → downstream:

| Loop | Edge | Position | Lanes | Approx. x (m) |
|---|---|---|---|---|
| L1 | 1 | 50 m | 4 | 50 |
| L2m | 2 | lane length / 2 | 4 | 255 |
| L2e | 2 | lane length − 10 m (upstream of the meter stop line) | 4 | 400 |
| L3e | 3 | lane length − 10 m | 4 | 540 |
| L4a | 4 | 10 m | 2 | 560 |
| L4m | 4 | lane length / 2 | 2 | 690 |
| L4e | 4 | lane length − 10 m | 2 | 820 |
| L5a | 5 | 10 m | 1 | 845 |
| L5m | 5 | lane length / 2 | 1 | 905 |
| Lx | 5 | lane length − 15 m (exit) | 1 | 970 |

- **Aggregation period: 10 s for all loops.** Reads use `getLastIntervalVehicleNumber`, `getLastIntervalOccupancy` and `getLastIntervalMeanSpeed`, polled once per interval just after it closes. These are not `getInterval*`, the current-interval value (CLAUDE.md).
- **Section speed** (for a loop group): count-weighted mean of the lane speeds over lanes with count > 0. If every lane has count 0 and the mean occupancy is ≥ 50 %, the speed is **0** (a standing queue over the loop). Otherwise it is NaN (no traffic).
- **Controllers and observations aggregate the 10-s intervals to 30 s.**

**Loop-fed meter (the validated controller with a measurement change).** This is the Vinitsky feedback meter, q ← q + K_F (n_crit − n̂), every T = 30 s, with n̂ estimated from loops instead of the ground-truth count on edge 4:
- n̂ = Σ over lanes 4_0 and 4_1 of (lane length / ℓ_eff) × the mean over {L4a, L4m, L4e} of the 30-s occupancy fraction;
- ℓ_eff = 5.0 m, the controller's assumed vehicle length; it does not know the truck share.

The ground-truth-fed meter stays as a **reference arm** (§5), so the measurement effect is reported.

**Loop observation S-LOOP** (for any later learner or MPC; defined here so that every controller sees the same sensors):
- per loop and lane: the 30-s count / (30 s × 0.6 veh/s), occupancy fraction, and speed / 23 (NaN → 0, with a validity bit);
- plus the previous action.

No ground-truth count, vehicle id or AV/human split enters any controller from S1 on.

## 3. Seeds (sub-ranges of 7,180,000–099)

| Range | Role |
|---|---|
| 7,180,000 | smoke and tool checks (throw-away; never used for any criterion) |
| 7,180,001–009 | throw-away reserve (unused unless an addendum says otherwise) |
| 7,180,010–019 | realism calibration (cell selection) |
| 7,180,020–039 | realism checks; determinism re-run on 7,180,020 |
| 7,180,040–059 | T0 authority |
| 7,180,060–099 | reserved for S2 (population health and R-0 checks) |

## 4. Realism gate (per variant; t2_realism_protocol.md incl. Addendum A, adapted to BN4 as stated)

### 4.1 Smoke and tool check (seed 7,180,000)

- One NC run per variant at q = 2,000.
- Checks that each variant runs, that its loops report, and, for B3, which mechanism SUMO 1.27 supports for sampled attributes (native distribution strings or generated vTypes, §1.1).
- **Outputs are not used for any criterion.** If the smoke shows an estimator defect, an addendum is committed before calibration, as Addendum A was in t2.

### 4.2 Calibration (seeds 7,180,010–019)

**Runs:** NC, q ∈ {1,000, 1,200, …, 3,000} (11 cells) × 10 seeds. Horizon 2,440 s at constant q; no drain needed.

**Cell rule (as t2):**
1. among cells with 0 teleports and 0 health FAIL, take the cell whose sustained-onset share is closest to 0.5;
2. ties go to the lower q.

**Early outcomes:**
- no eligible cell → FAIL R-c;
- maximum onset share < 0.2 → FAIL R-a, and the checks do not run.

**R-0, inertness:** B2 is compared with B0, and B3 with B2, on the 110 calibration pairs. Identical result hashes in every pair → **INERT**, dropped and reported.

### 4.3 Checks (seeds 7,180,020–039)

**Runs:** NC at the selected cell (20 runs), at the stress cell q = 3,000 (20 runs; shared if it is the selected cell), and 1 determinism re-run.

**Definitions (BN4 adaptation):**
- **Onset probe (the "up0b" analogue): L4m,** the middle of the 2-lane section, 140 m upstream of the final zipper.
- **Speed thresholds,** scaled from t2's 60 / 70 km/h by the ratio of speed limits, 82.8 / 120 (t2's MRG3 limit is 33.33 m/s):
  - congested < **41.4 km/h**;
  - recovered > **48.3 km/h**.

  Reason: the thresholds express a fraction of the limit (0.50 / 0.58). Fixed before any BN4 loop speed was seen.
- **Sustained onset t_b:** the first t ∈ [300, 2,400] s at which L4m's forward 2-min **and** forward 5-min mean section speeds are both < 41.4 km/h.
- **Recovery t_rec:** the first t > t_b with a forward 5-min mean > 48.3 km/h.
- **Exit flow:** Lx count per 10 s → veh/h/lane, on 1 lane.

**R-a, capacity drop** (Addendum A estimator):
- Q_ff = the median over selected-cell runs **without** an onset of the mean exit flow over (300, 2,400] s.
- Q_dis = the median over runs **with** an onset of the mean exit flow over [t_b + 300, min(t_b + 1,200, t_rec, 2,440)), with a window of at least 300 s.
- **PASS** if the onset share is ≥ 0.3, there are ≥ 3 runs with and ≥ 3 without an onset, and **Q_dis / Q_ff ∈ [0.82, 0.97]**.
- A 2,000-resample bootstrap CI is reported, not gated.

**R-b, wave speed:**
- Loop pairs (downstream → upstream), in preference order: L4e → L4a (≈ 260 m), L3e → L2m (≈ 285 m), L2m → L1 (≈ 205 m).
- Section speeds at 10 s; the t2 estimator unchanged (≥ 15-min jointly congested segment under the centred 5-min mean, high-pass, cross-correlation for lags 0…min(600 s, segment − 600 s), valid if r ≥ 0.3 with an interior peak), with "congested" at 41.4 km/h.
- **PASS** if the pooled median of the valid estimates over both cells is in **[−25, −10] km/h**. **n/a** (flagged, not a FAIL) with fewer than 5 valid estimates.
- **Why R-b is not n/a by design:** BN4's sections are short. At 15 km/h, a wave crosses 260 m in about 62 s, which the 10-s lag grid resolves to about ±8 %. That resolution is disclosed. Short congested segments will often make R-b n/a, and that is allowed.

**R-c, sanity: taken as written, NOT adapted to BN4.**
- 0 teleports and 0 health FAIL in the selected-cell check runs and the determinism re-run. Stress-cell teleports are reported, not gated (t2 Addendum A.3).
- **Median per-lane discharge (Q_dis per onset run, selected cell) ∈ [1,600, 2,400] veh/h/lane**, measured at Lx, the single exit lane.
- The determinism re-run is hash-identical.
- **Justification for not adapting the floor:**
  - The floor is a per-lane property of human queue discharge. A one-lane exit does not lower it; if anything, a single lane has no lane-imbalance losses.
  - Lowering it after seeing B0's ≈ 900 veh/h would make the criterion unfalsifiable for this plant.
  - The verdict under the original t2 teleport rule (teleports over all check runs) is reported alongside.

**R-d, origin of congestion:**
- Among runs in which any loop group's forward 2-min mean section speed drops below 41.4 km/h, take the first such group (ties go to the most downstream).
- **PASS** if it is one of the bottleneck groups {L3e, L4a, L4m, L4e} in **≥ 80 %** of runs, pooled over both cells.
- Congestion that starts at L1, L2m or L2e (entry or open road) or at L5a, L5m or Lx (downstream of the final zipper) counts against.

**Reported, not gated:**
- the stopped-sample share (< 10 km/h);
- the R1-style ratio;
- per-cell tables;
- for B3, spawned vehicles per class.

**Verdict per variant:** INERT, FAIL (any of R-a, R-c, R-d fails, or R-b fails with ≥ 5 valid estimates), or PASS (R-b may be n/a, flagged).

**Primary plant** = the first PASS in the order B0, B2, B3. **If none passes: HARD STOP (outcome C).** T0 is then not run, and the S1 report closes the gate.

## 5. T0: meter authority with loop detectors (on the primary plant only, seeds 7,180,040–059)

**Episode:** the R6 episode, i.e. 40 s warm-up, 900 s control, uncontrolled drain. The metric is door-to-door time, including the origin queue, with served vehicles co-reported.

**Cell:** the lowest calibration q at which the primary variant's NC onset share is ≥ 0.8, so that NC is congested and the meter has something to prevent. If no cell reaches 0.8, the highest-share cell is used.

**Arms (20 paired seeds each):**
- `nc`;
- the **loop-fed meter** at K_F ∈ {5, 20} × n_crit ∈ {4, 8, 12} (6 settings; n_crit in loop-estimated vehicles);
- the **ground-truth-fed meter** at the same 6 settings (reference arms).

That is 13 arms and 260 runs.

**Criteria (paired over seeds; median of paired differences; 95 % percentile bootstrap, 10,000 resamples):**

| Check | PASS if |
|---|---|
| **T0-a, binds** | for the loop-fed meter at the paper setting (20, 8): Δ door-to-door vs `nc` has a CI excluding 0, **and** Δ mean L4 occupancy over the control window vs `nc` has a CI excluding 0 |
| **T0-b, control matters** | the best loop-fed setting (lowest median door-to-door) improves on `nc` by ≥ 5 % of `nc`'s median, with the CI upper bound < 0 |
| **T0-c, sensor reads** | in every T0 run, the Lx interval counts summed over the run equal the network arrivals within 1 % (the exit loop is 15 m before the sink, so nearly every arrival crosses it) |
| **T3, determinism** | already gated in R-c |

**Reported, not gated:**
- the measurement effect: loop-fed vs ground-truth-fed at each setting (paired Δ and CI);
- the correlation of n̂_loop with the ground-truth edge-4 count at the meter updates.

**S1 PASS** = the primary plant exists (§4) **and** T0-a, T0-b and T0-c hold.
- **T0 FAIL:** stop, report, and wait for the lead and the author.

## 6. Statistics, health and outputs

- Paired seeds; medians; 95 % percentile bootstrap CIs of the median paired difference. FAIL runs stay in the metrics and are counted.
- **Raw runs:** `/home/catalin/work/phd/vsl_lab_runs/t1/gate_ctx_r6/s1_*`.
- **Committed summaries:** `docs/lab/gate_ctx_r6/s1_realism.json`, `s1_t0.json` and `report_S1_<stamp>.md`.
- One ledger row per batch.
- **Compute:** background jobs through `vsl_lab/ops/scheduler.py`, concurrency by CPU utilisation (≤ 48 workers), the 99 °C median guard.

## 7. Expected outcome (written before any run)

- **B0:** FAIL R-c (about 900 veh/h).
- **B2:** SUMO's default accel (2.6 m/s²) should raise discharge well above B0. Whether it reaches 1,600 on a single lane after a zipper with speedFactor spread is uncertain. ZM3-H5, with a = 1.0, reached 1,528.
- **B3:** similar to B2. Trucks and timid drivers lower it.
- **Probability that at least one variant passes:** my estimate is about 40–50 %. This is a judgement, not a measurement.
