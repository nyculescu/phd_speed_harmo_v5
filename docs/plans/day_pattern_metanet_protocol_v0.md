# U.S.169 SB METANET plant: calibration and plant gate (protocol v0, DRAFT under design review)

*2026-10-05. Branch `claude/day-pattern-core`. Decisions D3.1–D3.3 (`day_pattern_decisions_v0.md`). This file becomes binding when it is committed, and that commit precedes any calibration run.*

## 0. Purpose and what is at stake

**Purpose:** build the macroscopic plant on which the day-pattern headroom gate runs (decision P6b, a METANET gate with SUMO confirmation), and prove that it reproduces the real U.S.169 SB corridor **before** any controller is tuned on it.
- **A plant that fails this gate stops the track**, after at most one pre-registered structural fallback (§6).
- **C4 deviation (D3.1):** the real capacity drop at the bottleneck is small. The median r is 0.984 (IQR 0.952–1.001). The plant must reproduce *that* drop, not a literature band.

## 1. Network (from the MnDOT configuration, `vsl_lab/data/mndot.py`, `US169_METERS`, `all_entrances=True`)

**Stretch:** U.S.169 southbound from **N of I-394 (km −11.79)** to **T.H.101 (km +9.39)**, about 21.2 km. km 0 is the Valley View Rd entrance.
- **Mainline links:** links between stations, split into cells of 350–650 m (target 500 m). The cell length L_i and lane count λ_i come from the configuration.
  - Lane counts change: 2 lanes upstream, 3 at the I-494 interchange (km 0.37–1.14 and 2.89), and 2 downstream.
  - Lane drops get the METANET lane-drop term (§2).
- **Entrances (20):**
  - **Metered on-ramps:** 13 upstream ramps, plus the 4 controlled ramps (Valley View Rd, Marth Rd, Anderson Lakes Pkwy, **Pioneer Tr**). Each has a store-and-forward queue with storage from the configuration (vehicles).
  - **Freeway-to-freeway ramps** (T.H.62 WB/EB, I-494 WB/EB; Merge detectors): unmetered origins.
  - Old Shakopee Rd (km 7.52) has no detectors. Its inflow is estimated as the flow balance between the Pioneer Tr / Old Shakopee Rd stations and T.H.101 (§3.3).
- **Exits (16):** turning rates per 5 min, from exit counts divided by upstream mainline flow (§3.3).
- **Boundaries:**
  - **Upstream:** mainline origin at N of I-394, with demand equal to the measured flow plus an origin queue. A day is unusable if this station is congested; checked in §3.4.
  - **Downstream:** free outflow, with a downstream density boundary equal to the measured density at T.H.101 (one cell beyond).

## 2. Model

METANET (Papageorgiou, Blosseville & Hadj-Salem 1990; Kotsialos et al. 2002 [VERIFY both]). Time step **T = 10 s**; the CFL condition is T ≤ min L_i / v_f,max, checked at build.

**Density:**

ρ_i(k+1) = ρ_i(k) + T/(L_i λ_i) · [q_{i−1}(k) − q_i(k) + r_i(k) − s_i(k)]

**Speed:**

v_i(k+1) = v_i(k) + (T/τ)[V(ρ_i) − v_i] + (T/L_i) v_i (v_{i−1} − v_i) − (ν T)/(τ L_i) · (ρ_{i+1} − ρ_i)/(ρ_i + κ) − δ T r_i v_i / (L_i λ_i (ρ_i + κ)) − φ T Δλ ρ_i v_i² / (L_i λ_i ρ_cr)

The last term is the lane-drop term, applied only where lanes drop, with Δλ = λ_i − λ_{i+1}.

**Fundamental diagram:** V(ρ) = v_f · exp(−(1/a)(ρ/ρ_cr)^a), with one parameter set per **section group**:
- G1: km −11.8 to −0.4, 2 lanes, 55 mph limit;
- G2: km −0.4 to 3.5, the interchange, 2–3 lanes;
- G3: km 3.5 to 9.4, 65 mph limit.

**Speed-limit extension, for H2 later and not calibrated now:**

V_i = min(V(ρ_i), (1 + α) · b_i · v_lim)

(Hegyi, De Schutter & Hellendoorn 2005 [read]; α is the non-compliance parameter.) It is inactive (b = 1) throughout calibration.

**Origins:**
- queue w(k+1) = w(k) + T(d − r);
- metered ramps release r = min(metered rate, d + w/T, Q_ramp · (ρ_max − ρ_i)/(ρ_max − ρ_cr));
- unmetered origins release r = min(d + w/T, capacity-limited term).

**Field metering is replayed:** during calibration, the metered ramps release the **measured passage flow** (the field meter's output), so that metering is not re-simulated.

## 3. Data

### 3.1 Days

The 104 days of 2023 already selected (52 Wednesdays, 26 Saturdays, 26 Sundays), complete-corridor pull D3.3.
- **Calibration set: Wednesdays with odd index** in date order (26).
- **Validation set: Wednesdays with even index** (26).
- Weekend days: a reported check only (§5.3).

2024 is not used.

### 3.2 Cleaning (fixed now)

- Lane-day validity as in the corridor protocol (≥ 90 % valid bins); dead lanes (zero counts 06:00–20:00) are invalid (Addendum B).
- Gaps ≤ 15 min are linearly interpolated; longer gaps make the station-day invalid for fitting.
- Stations whose median 05:00–06:00 speed lies outside 50–80 mph (field-length suspect) are **excluded from the speed term** but kept for flows.
- **A day is used only if:** the upstream boundary, every entrance and every exit are valid, and ≥ 80 % of interior stations are valid.

### 3.3 Inputs

**Inputs:** the upstream boundary flow; all entrance flows (passage for metered ramps, merge for freeway ramps); exit flows converted to turning rates against the upstream station flow.
- **Old Shakopee Rd inflow:** the 15-min balance (flow at T.H.101 + exits in between − flow at Old Shakopee Rd), clipped at ≥ 0.
- **Station flow conservation check:** for each link between two stations, |inflow − outflow − Δ stored| summed over the day ≤ 5 % of the throughput. A failing link's day is flagged, and that day is used only if fewer than 2 links fail.

**Ramp demand** (queue detector arrivals, for the controlled-plant use later) is reconstructed but **not used for calibration**.

### 3.4 Reported data facts

- valid days per set;
- conservation-check failures;
- upstream boundary congestion share. The boundary must be uncongested (v ≥ 45 mph) in ≥ 95 % of bins on every used day; otherwise the day is excluded and counted.

## 4. Estimation

**Parameters (19):**
- for each of G1–G3: v_f, ρ_cr, a (9);
- shared: τ, ν, κ, δ, φ (5);
- the ramp-capacity scale and ρ_max (2);
- one free-flow speed offset per group for detector bias (3, bounded ±5 %).

**Bounds** (literature-typical; [VERIFY], to be checked against Kotsialos et al. 2002 and Wang et al. 2022 before the commit):

| Parameter | Bounds |
|---|---|
| v_f | 90–135 km/h |
| ρ_cr | 18–45 veh/km/lane |
| a | 1.0–3.0 |
| τ | 5–40 s |
| ν | 5–90 km²/h |
| κ | 5–60 veh/km/lane |
| δ | 0–2 |
| φ | 0–4 |
| ρ_max | 140–200 veh/km/lane |

**Objective:** over the calibration days and 05:00–23:00, at 5-min resolution:

J = 0.5 · NRMSE_q + 0.5 · NRMSE_v

The NRMSE is taken over interior valid stations; speed uses only the stations not excluded in §3.2.

**Optimiser:** CMA-ES with 8 restarts, from seeds **7,190,011–018** (plant-check range 000–099; approved block), with a budget of 4,000 evaluations each. The best restart is frozen. The model is deterministic given its inputs.

**Identifiability (reported):**
- parameter spread across the restarts that come within 2 % of the best J;
- the coefficient of variation of each parameter;
- profile curves for v_f, ρ_cr, τ, ν and κ.

A parameter with a CV above 30 % is flagged **non-identifiable**; it is reported, not gated.

## 5. Plant gate (validation Wednesdays; real data as the reference; fixed now)

The model is driven by each validation day's measured inputs, with replayed metering. **PASS requires all of P1–P6.**

| ID | Check | Criterion |
|---|---|---|
| **P1 fit** | Median over validation days of NRMSE_q and NRMSE_v at interior stations | NRMSE_q ≤ 0.10 **and** NRMSE_v ≤ 0.20 [lab convention; to be compared with reported METANET fits before the commit, VERIFY] |
| **P2 where** | On days when the real bottleneck B (Pioneer Tr → Old Shakopee Rd) is active, the model's first congested cell (v < 40 mph for ≥ 15 min) lies in the merge area of B: Pioneer Tr ± 1 cell | ≥ 80 % of those days |
| **P3 whether** | Agreement of the day classification "B active" (model vs real) | ≥ 75 % of validation days |
| **P4 when** | On days active in both: \|model onset − real onset\| | median ≤ 15 min |
| **P5 discharge and drop** | The model's queue discharge per lane at Old Shakopee Rd (the corridor-protocol estimator), and the drop r, on days active in both | discharge median within **±5 %** of the real median **on the same days**; median r inside the real **IQR on the same days** |
| **P6 the narrow band** | Breakdown share by quartile of daily demand at the upstream boundary (validation days; real quartile edges) | the model's share within **±20 percentage points** of the real share in **every** quartile |

**Reported, not gated:**
- the speed of congestion propagating upstream, against the real one;
- weekend days: the same metrics;
- the **D-check:** on heavy days, the model's counted flow at B plateaus at the discharge level (the 15-min peak ≤ discharge + 5 %) while the reconstructed demand exceeds it. The real data show this; the model must too, otherwise the day-pattern mechanism is absent;
- non-identifiable parameters.

## 6. Failure handling (fixed now)

**If P1–P6 do not all pass:** **one** pre-registered structural fallback is fitted and judged on the same criteria.
- **F1:** a two-capacity fundamental diagram at the bottleneck cells, with a memory switch (the capacity drop modelled explicitly, after Srivastava & Geroliminis 2013 [VERIFY, SAGE-free, TR-C]), plus per-cell v_f for the merge cells.
- **If F1 also fails:** the METANET route **stops** and the track is reported to the author. The SUMO corridor (P3) is the remaining plant option, and it needs its own realism protocol.

**No criterion is relaxed.** Both outcomes are logged if F1 is used.

## 7. Outputs, compute, statistics

**Outputs:**
- `docs/lab/day_pattern/metanet_calibration.json` (parameters, fits, P1–P6, identifiability);
- `…/metanet_calibration.md`;
- ledger rows;
- code in `vsl_lab/plants/metanet.py` (model) and `vsl_lab/jobs/metanet_calibrate.py`;
- unit tests: mass conservation, CFL, free-flow steady state, and a queue-spillback sanity test.

**Compute:** CMA-ES on ≤ 32 workers under `vsl_lab/ops/guard.py`. One model-day takes about 0.1–1 s (estimate).

**Statistics:** medians over days. There are no seeds to pair here, since real days are the units. **Validation days are never used for fitting.**
