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
