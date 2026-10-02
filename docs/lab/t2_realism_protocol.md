# Track 2 (MRG3-v3): plant-realism gate, pre-registration

*Committed 2026-10-02, before any realism run. Branch `claude/vsl-lab-core`. The author chose "gate before DRL" on 2026-10-02.*

## Why

The author reports two things from earlier SUMO work. Stop-and-go waves appear at high demand even with randomised departures ("moving red triangles"). SUMO's car-following models (Krauss, IDM, EIDM) also behave like idealised ADAS.

Before any DRL claim on the merge plant, the plant must show the main empirical signatures of real merge congestion. Every driver variant below is tested against the same pre-registered checks. Only passing variants go on to MTFC tuning (R2) and DRL.

**What this gate does not test:**
- lane-change realism (LC2013 stays at its defaults in every variant);
- trajectory-level calibration;
- anything beyond the signatures listed below.

A PASS means "not contradicted by these signatures". It does not mean "validated".

## Plant and variants

The plant is MRG3-v3: geometry as in `vsl_lab/netgen/mrg3.py`; demand profile and compliance mix as in R1; `departSpeed="avg"`; step 0.5 s. Only the driver model changes. The vehicle length and the trucks' maximum speed are kept in every variant.

| ID | Driver model | What it adds | Source of the values |
|---|---|---|---|
| **H0** | IDM: cars a 1.0, b 1.5, T 1.0 s, s0 2 m, δ 4; trucks a 0.6, T 1.5 s, s0 2.5 m, length 12 m | nothing (identical to the MRG3-v3 vTypes) | Treiber-style values, as in v2/v3 |
| **H1** | H0 + `actionStepLength="1.0"` | about 1 s reaction delay (decisions every 1 s, at a 0.5 s simulation step) | ad hoc, plausible order of magnitude [VERIFY reaction-time literature] |
| **H2** | H0 + `driverstate` device (probability 1, `initialAwareness` 0.7, other coefficients at SUMO defaults) | perception errors in gap and speed difference (Ornstein–Uhlenbeck process) | ad hoc. SUMO's default awareness of 1.0 most likely produces no perception error, since the noise scales with lowered awareness [VERIFY in the SUMO docs] |
| **H3** | W99 (SUMO defaults) | a psycho-physical (Wiedemann 99) model | SUMO defaults |
| **H4** | EIDM with the H0 parameters + `sigmaleader` 0.2, `sigmagap` 0.2, `sigmaerror` 0.3, `treaction` 0.6 | estimation errors, a driving error and reaction time | ad hoc, plausible. The EIDM parameter meanings come from the SUMO EIDM documentation [VERIFY against Salles et al. 2020] |

## Seeds

**Reassigned before use, and disclosed.** These seeds come from the never-used T2 R2 range 7,120,100–7,120,299. Ranges 7,120,100–7,120,169 are already taken by MRG3-v3 (D-2).
- Calibration (throw-away): 7,120,170–7,120,179.
- Checks: 7,120,180–7,120,199.

**Smoke test:** one NC run per variant on 7,120,050, at 5,400 / 900. That seed is the D-1 throw-away. The smoke test checks only that each variant runs and is not inert. Its outputs are not used for any criterion.

## Stage 1: calibration (per variant)

**Runs:** NC at main_peak ∈ {4,200, 4,500, 4,800, 5,100, 5,400, 5,700, 6,000} × ramp_peak ∈ {600, 900} × 10 seeds. That is 140 runs per variant, 700 in total. The grid extends the v1/v3 grid downwards, for variants with lower capacity.

**Cell selection (same rule as R1):**
1. among cells with 0 teleports and 0 health FAIL, take the cell whose breakdown share (from `capdrop`, as in R1) is closest to 0.5;
2. ties go to the lower total demand.

**Early outcomes:**
- **No eligible cell:** the variant FAILS R-c.
- **Maximum breakdown share < 0.2 over the whole grid:** the variant FAILS R-a. It does not break down even at a downstream demand of about 2,300 veh/h/lane. No check runs follow.

### R-0: parameter effect (per variant, H1–H4)

SUMO silently ignores unknown vType attributes. So, on the 140 calibration pairs (same cell and seed), a variant is compared with H0. If door-to-door time, arrivals and teleports are identical in every pair, the variant is **INERT**: it is dropped and reported, not counted as a realism result.

## Stage 2: checks (per variant)

**Runs:** NC on the check seeds:
- at the **selected cell**, 20 runs;
- at the **stress cell** 6,000 / 900, 20 runs (the same runs are used if the selected cell is the stress cell);
- plus 1 determinism re-run (seed 7,120,180 at the selected cell).

### Definitions

**Speed probes**, all from `probes10.csv`:
- the mean speed of the vehicles within ±50 m of 5 probe points, sampled every 10 s;
- probe points: up3 at 500 m (x ≈ 500), up2 at 500 m (≈ 1,500), up1 at 500 m (≈ 2,500), up0a at 250 m (≈ 3,250), up0b at 233 m (≈ 3,735);
- the merge starts at x = 4,000;
- exact x positions come from the lane shapes in the net.

**Exit flow** is the per-lane flow at the `down` end loops (30-s data, `features.csv`).

**Sustained onset t_b** is the first t ∈ [600, 3,600] s at which:
- the up0b probe's forward 2-min mean speed is < 60 km/h, and
- its forward 5-min mean speed is < 60 km/h.

**Recovery t_rec** is the first t > t_b at which the forward 5-min mean speed is > 70 km/h.

**Capacity-drop ratio (mean-based)** = mean exit flow over [t_b + 5 min, min(t_b + 20 min, t_rec)) ÷ mean exit flow over [t_b − 10 min, t_b).
- A discharge window shorter than 5 min excludes the run from the ratio.
- Both terms are means. This avoids the upward noise bias of the "pre-breakdown maximum" used in the R1 metric.
- The R1 max-based ratio is still reported, for continuity.

### Criteria

| Check | Signature | PASS if |
|---|---|---|
| **R-a** capacity drop | Queue discharge below the pre-queue flow. Reported drops at real bottlenecks range from a few % to about 20 % (Chung, Rudjanakanoknad & Cassidy 2007 [VERIFY]; Cassidy & Bertini 1999 [VERIFY]) | at the selected cell: breakdown share ≥ 0.3, **and** the median mean-based ratio of the breakdown runs is in **[0.82, 0.97]** (≥ 5 ratios required) |
| **R-b** internal wave speed | Stop-and-go waves inside congestion travel upstream at roughly −15 km/h, typically between −10 and −20 km/h (e.g. Treiber & Kesting, *Traffic Flow Dynamics*, 2013 [VERIFY]). The band below is widened to −25 km/h | pooled over both cells, median wave speed in **[−25, −10] km/h**, with ≥ 5 valid estimates. **n/a** (flagged, not a FAIL) if there are fewer than 5 |
| **R-c** sanity | no gridlock artefacts; plausible discharge | 0 teleports and 0 health FAIL in all check runs; median per-lane discharge flow (selected cell, breakdown runs) in **[1,600, 2,400] veh/h/lane**; the determinism re-run is hash-identical |
| **R-d** origin of congestion | At a merge on an otherwise homogeneous road, congestion should start at the bottleneck. It should not start at the entry or on the open road (this is the "waves from nowhere" artefact) | pooled over both cells, among runs in which any probe's forward 2-min mean speed drops below 60 km/h, the first such probe is up0b or up0a in **≥ 80 %** |

**Wave-speed estimator (R-b)**, applied per run:
1. **Probe pairs** (downstream → upstream), in order of preference: up1 → up2 (1,000 m); up0a → up1 (750 m); up0b → up0a (483 m).
2. **Window:** the first pair with a jointly congested contiguous segment of ≥ 15 min, where both probes' centred 5-min mean speed is < 60 km/h.
3. **High-pass filter:** each speed series minus its centred 5-min mean.
4. **Cross-correlation:** the Pearson correlation between downstream(t) and upstream(t + k), for lags k = 0 s up to k_max = min(600 s, segment length − 600 s), so that every lag keeps at least 60 overlapping samples.
5. **Validity:** the estimate is valid if the peak correlation is ≥ 0.3 and the peak lag k* lies strictly inside the evaluated range (10 s ≤ k* ≤ k_max − 10 s).
6. **Result:** c = −Δx / k*.

**Reported but not gated:**
- the share of congested probe samples with v < 10 km/h (how often the "red triangles" are stopped);
- the R1 max-based ratio;
- per-cell values.

## Verdict and use

**Per variant:** **INERT** (by R-0), **FAIL** (any of R-a, R-c, R-d fails, or R-b fails with ≥ 5 valid estimates), or **PASS** (R-b may be n/a, flagged).

**Primary plant for DRL.** If several variants pass, the primary plant is the first passing variant in the order H4, H2, H1, H3, H0. This orders them by how much human imperfection they model explicitly. The other passing variants become robustness plants.

**Next steps:**
- **H0** = MRG3-v3, so its R1 checks come from the v3 chain.
- **Passing H1–H4** get their own R1 (T1c / T0 per `t2_mrg3_r1_protocol.md`, on fresh seeds approved before use) before R2.
- **If no variant passes:** Track 2 stops at this gate, and the author decides.

**Interaction with the queued v3 chain.** `run_v3.sh` (calibration → R1 → D-check → R2 on MRG3-v3 ≡ H0) was queued before this gate. Its R2 step now requires an H0 PASS in `docs/lab/t2_realism_verdict.json`, otherwise it skips. Its calibration and R1 run as queued. No running process was stopped.

---

## Addendum A (2026-10-02, after the smoke test, before any calibration or check run)

### What the smoke test showed

**Setup:** one NC run per variant at 5,400 / 900 on the throw-away seed 7,120,050, raw in `realism_smoke_*`.

**Every variant runs, and none is INERT:** all 5 result hashes differ.

| Variant | Wave speed (km/h) | Congestion origin | Notes |
|---|---|---|---|
| H0 | −19.0 | up0b | 1 teleport |
| H1 | −14.4 | up0b | 1 teleport |
| H2 | none (no 15-min jointly congested window) | up0b | — |
| H3 | −20.0 | up0b | — |
| H4 | −7.2 | **up1** | discharge 185 veh/h/lane; not drained at 3 h (H-E1); a run takes about 5 min instead of 15–25 s |

**The H4 cause.** Its error magnitudes are far above SUMO's documented EIDM defaults. The SUMO vType table gives sigmaleader 0.02, sigmagap 0.10, sigmaerror 0.10 and treaction 0.50; H4 uses 0.2, 0.2, 0.3 and 0.6.

### Fixes, pre-registered now

**1. Bug fix in the R-a estimator.**
- **Symptom:** every smoke breakdown began at t ≈ 1,210 s, exactly when peak demand arrives. The "10 min before onset" window therefore measured the demand ramp-up, not the pre-queue capacity, and the ratios came out at 1.2–1.5.
- **New estimator (between runs, same cell):**
  - Q_ff = median, over the selected-cell runs **without** a sustained onset, of the mean exit flow per lane over the demand plateau as seen at the exit, (1,400, 3,000] s;
  - Q_dis = median, over the runs **with** a sustained onset, of the mean exit flow per lane over [t_b + 5 min, min(t_b + 20 min, t_rec, 3,900 s)), with a window of at least 5 min;
  - **ratio = Q_dis / Q_ff.**
- **Why this is conservative:** the bottleneck demonstrably carried Q_ff without breaking down, so Q_ff is a lower bound on free-flow capacity, and the ratio understates the drop.
- **R-a PASS** if all hold: sustained-onset share ≥ 0.3; ≥ 3 runs with and ≥ 3 runs without an onset; ratio in [0.82, 0.97]. If it cannot be computed, R-a FAILS.
- **Reported, not gated:**
  - a 95 % percentile-bootstrap CI of the ratio (runs resampled within the two groups, 2,000 resamples);
  - a field-style within-run ratio, ramp-corrected (pre-window (t_b − 5 min, t_b] only when t_b ≥ 1,700 s);
  - the original 10-min estimator, as values only;
  - the R1 max-based ratio.

**2. One breakdown definition.** "Breakdown" now means a sustained probe onset t_b exists (definition above) in every place: cell selection, the early outcomes and R-a. The R1 `capdrop` flag is reported. In the smoke test the two definitions disagreed once: H2 had an onset at 1,380 s, but the `capdrop` flag was false.

**3. R-c teleport scope.**
- Teleports and health FAILs are gated on the selected-cell check runs and the determinism re-run, i.e. the operating point.
- Teleports at the 6,000 / 900 stress cell are reported and flagged, not gated. That cell exists to measure waves and origins at high demand.
- **This change is informed by the smoke test** (one teleport each for H0 and H1 at 5,400 / 900). The verdict under the **original** rule (teleports over all check runs) is reported next to the amended one.

**4. New variant H5:** EIDM with the H0 IDM-shared parameters, and every EIDM-specific parameter left at its SUMO default (estimation and driving errors included, per the SUMO vType documentation table). No value is chosen by me.
- It is added because H4's ad hoc magnitudes collapsed the plant.
- It gets the same grid, seeds and checks.
- H4 stays as pre-registered and will be reported, whatever its outcome.
- **Preference order for the primary plant:** H4, H5, H2, H1, H3, H0.

**Run counts:** 840 calibration runs, plus up to 6 × 41 check runs.

**5. The same flaw in R1 T1 (MRG3-v3), pre-registered before the v3 R1 runs.**
- R1's T1 ratio (`capacity_drop()`: maximum 5-min flow in the 15 min before the onset) is confounded in the same way. When breakdown starts during the demand ramp, the "pre" flow is demand-limited, which biases the ratio towards 1. When it starts on the plateau, the maximum of noisy 5-min flows biases it the other way. The v1 T1 result (0.976) may therefore be distorted; this is noted and not re-litigated.
- **For MRG3-v3**, the T1 gate before R2 keeps its share part (≥ 0.3), its teleport part and its FAIL part from R1. Its ratio part is replaced by realism R-a, through the H0 verdict.
- The R1 T1 max-based values are still reported.

---

## Addendum B (2026-10-02): re-check at a 0.2 s step, pre-registered before the 0.5 s verdict is known

**Reason.** On 2026-10-02 the author chose a 0.2 s step for Round 3 (TM21 vs TM20; `round3_tm21_protocol.md` Addendum A), because SUMO's ACC/CACC CAVs brake hard at 0.5 s. The step also changes the human plant. In the throw-away diagnostics, IDM's door-to-door time went from 356 to 392 s, and a ramp teleport disappeared. So the 0.5 s realism verdict does not carry over to 0.2 s.

**Re-check design:**
1. **Smoke** (throw-away seed 7,120,050, 5,400 / 900, all six variants at 0.2 s). A variant whose smoke run is **not drained** within t_max (H-E1) is classed **COLLAPSED**: excluded, and reported. The cost of collapsed EIDM runs (about 5 min each at 0.5 s) would make a full re-check take hours.
2. **Scope:** every variant that is neither INERT (at 0.5 s) nor COLLAPSED.
3. **Seeds:** calibration 7,120,260–7,120,269 (throw-away); checks 7,120,270–7,120,289; the determinism re-run uses 7,120,270. These come from the T2 tuning range, reassigned and disclosed.
4. **Same as at 0.5 s:** grid, cell rule, criteria and Addendum A estimators. R-0 is not repeated, since inertness is a property of the parameters, already tested at 0.5 s.
5. **Primary plant for Round 3** = the first 0.2 s PASS in the order H4, H5, H2, H1, H3, H0.
6. **Outputs:** `t2_realism_verdict_step0.2.json` and `t2_realism_step0.2.md`.
7. **Both verdicts (0.5 s and 0.2 s) are reported.**
