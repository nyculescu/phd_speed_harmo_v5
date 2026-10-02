# Track 1 (BN4), phase R1 plant checks: protocol

*Committed before any of these checks run. 2026-10-01 · branch `claude/vsl-lab-core` · roadmap `docs/plans/vsl_drl_run_roadmap_v0.md` §6–§7*

## Plant (frozen for R1)

- **Network:** BN4 spec v2, cache `bn4_e578788201`. It is the Flow / Vinitsky et al. (2018) zipper bottleneck:
  - edges of 100, 310, 140, 280 and 155 m;
  - 4, 4, 4, 2 and 1 lanes;
  - 23 m/s;
  - node 3 held at all-green (program `allgreen`, checked by H-R7).
- **Simulator:** SUMO / libsumo 1.27.1, step 0.5 s, `--time-to-teleport 300` (teleports counted).
- **Vehicles:**
  - **Model:** IDM with Flow defaults (a 1.0, b 1.5, T 1.0 s, s0 2.0 m, δ 4, length 5 m).
  - **Human desired speed:** `speedFactor = normc(1, 0.2, 0.2, 2.0)`.
  - **Lane changing:** disabled for everyone (as in the paper). The variant BN4-L keeps LC2013 defaults.
  - **Departure:** 10 % AVs (IDM, speedFactor 1), `departLane="random"`, `departSpeed="10"`.
- **Demand:** constant inflow q over [0, 1,500) s as explicit Poisson arrivals, followed by a drain until empty (cap 7,200 s).
- **Outflow measure:** arrivals over [1,000, 1,500) s, the paper's "last 500 seconds" of the demand period.

## Disclosure (seen before this protocol)

One smoke run on the throw-away seed 7,110,000 (q = 1,800 veh/h, 900 s of demand) gave an outflow of **900 veh/h** over [400, 900) s. Health was PASS and two fresh processes gave the same hash.

The thermal calibration (R0.4) runs BN4 at q = 2,000 on seeds 7,110,000–7,110,009. Its outputs are used **only** for temperature.

## Checks, seeds and PASS criteria

### T1: capacity drop (mechanism)

- **Runs:** q ∈ {400, 500, …, 2,500} veh/h (22 levels) × seeds 7,110,010–7,110,019 = 220 runs. Lane changing off.
- **Measure:** Q(q) = median over the 10 seeds of the outflow at inflow q.
  - peak = max over q of Q(q);
  - high = mean of Q(q) over q ∈ {2,200, 2,300, 2,400, 2,500}.
- **PASS** if **all three** hold:
  1. high ≤ 0.95 × peak;
  2. 0 runs with health FAIL;
  3. 0 teleports in every run.
- **Reported, not part of PASS:** the argmax of Q (critical inflow); the high / peak ratio; Q at q = 2,500; and a comparison with Vinitsky's text: "At inflows above 1500 vehicles per hour, congestion becomes the equilibrium state", and RL "stabilize[s] the outflow … at 1000 vehicles per hour: 200 vehicles per hour above the" uncontrolled one.

### T1-L: robustness variant (exploratory, not a gate)

- **Runs:** the same 220 (q, seed) pairs with lane changing on (BN4-L).
- **Reported:** the same statistics.

### T0: actuator binds, and lag (AV speed cap, the Lagrangian actuator)

- **Runs:** seeds 7,110,020–7,110,029 × q ∈ {1,200, 2,000} × arm ∈ {none, cap 10 m/s, cap 5 m/s} = 60 runs.
  - From t = 600 s, every 20 s, every AV on edges 2–4 gets `setMaxSpeed(cap)`. The cap persists after an AV leaves edge 4.
  - Comparisons are paired by seed against "none".
- **Measures:**
  - Δoutflow over [900, 1,500) s: the median of paired differences, with a 95 % percentile bootstrap CI (10,000 resamples);
  - **lag**: the first time after 600 s at which the 60-s moving outflow of the capped run differs from the paired "none" run by more than 10 %. Report its median over seeds.
- **PASS (the actuator binds)** if, for at least one (q, cap) cell, |median Δoutflow| ≥ 5 % of the "none" median **and** the CI excludes 0.
- Its sign is reported. Either direction shows authority.

### T3: determinism

- **Runs:** 10 (q, seed) pairs drawn at random (with `random.Random(7110099)`) from the T1 sweep, re-run in fresh processes.
- **PASS** if all 10 summary hashes are identical to the originals.

## Health rules (roadmap §4)

- Every run reports PASS / WARN / FAIL with codes. A FAIL run is **counted and reported, never dropped**.
- **WARN H-R2** (insertion backlog) is *expected* at q above capacity: the origin queue is real demand and is part of the primary metric. It does not fail T1.
- **WARN H-R5** (vehicles waiting > 120 s) is expected inside the congested queue. Teleports (H-R3) remain FAIL.

## Decision

- **T1 PASS:** Track 1 proceeds to R2 (tuned baselines) and R3 (DRL reproduction).
- **T1 FAIL:** BN4 in SUMO 1.27 does not reproduce the paper's capacity drop. That is recorded as a finding. T1 stops and T3 (ring) continues.
- **T0 FAIL:** the AV cap has no authority. DRL with this actuator is pointless, and T1 stops.

---

## Addendum (2026-10-01, written after R1 v3 and before T0b runs): T0 v1 design error and T0b pre-registration

**T0 v1 (as committed) FAILED.** No cell changed the outflow by ≥ 5 %. The design was wrong for the question:
- the cap was applied at t = 600 s, after the bottleneck had already broken down in those seeds (even at q = 1,200, the "none" median outflow over [900, 1,500) was 900 veh/h);
- so T0 v1 tested whether 10 % capped AVs can *dissolve* an established jam. They cannot, consistent with Vinitsky: "once the congestion forms … it does not dissolve".

The question that matters for Track 1 is whether the actuators can **prevent** breakdown. That is a new check: it gets a new pre-registration and fresh seeds, and T0 v1 stays FAIL in the ledger.

### T0b: preventive actuator authority

- **Path:** the R2 evaluation path (`vsl_lab/jobs/bn4_eval.py`): 40 s warm-up, then 900 s of control, then an uncontrolled drain.
- **Seeds:** 7,110,030–7,110,049 (20 fresh plant-check seeds).
- **Cells:** q ∈ {1,600, 2,000} veh/h.
- **Arms:**
  - `nc`;
  - `cap:5` and `cap:10` (all AVs on edges 2–4 capped from t = 40 s);
  - `meter:20:8` (Vinitsky's feedback meter, paper values).
  - That is 160 runs.
- **Measure:** outflow over the control window [40, 940) s. Δ = the median of paired differences (arm − nc), with a 95 % bootstrap CI.
- **PASS per actuator family** (AV cap; meter): in at least one cell, |Δ| ≥ 5 % of the nc median **and** the CI excludes 0.
- **Decision:**
  - If the AV-cap family FAILs T0b, the Lagrangian actuator has no preventive authority in this plant, and the Vinitsky reproduction (DRL v1) is stopped.
  - If only the meter passes, the meter is the only working actuator here. That is reported.
