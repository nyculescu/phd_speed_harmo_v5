# Track 1 (BN4), phase R2 baseline tuning: protocol

*Committed before any R2 run. 2026-10-01 · branch `claude/vsl-lab-core` · roadmap §6 (Track 1), §7 (R2)*

**Purpose:** tune every non-learning comparator on **tuning seeds only**, then freeze the result. DRL is later compared against these frozen, tuned baselines and never against defaults (v6 lesson: "Tune every baseline first").

## Common evaluation path (also used later for DRL)

- **Code:** `vsl_lab/jobs/bn4_eval.py`, which runs `BN4Env` with `drain_after=True`.
- **Plant:** BN4 exactly as in the R1 protocol (spec v2, IDM Flow defaults, LC off, 10 % AVs, step 0.5 s).
- **Episode:**
  - **40 s of uncontrolled warm-up**, as Vinitsky: "we allow the experiment to run uncontrolled for 40 seconds before each run". Congestion has not yet formed when control starts;
  - **900 s of control**, with decisions every 1 s (Vinitsky: actions held for two 0.5-s steps);
  - demand ends at 940 s;
  - then an **uncontrolled drain** (AV caps released, node-3 signal all-green) until the network and the origin queue are empty (cap 7,200 s).
- **Primary metric:** mean time in system per vehicle, i.e. door-to-door time including the origin and insertion queue = TTS_system (veh·s, network plus queue, integrated until drained) / generated vehicles.
- **Co-headlines:**
  - outflow over the control window [40, 940) s, in veh/h;
  - vehicles served by 940 s.
- **Health:** every run reports PASS / WARN / FAIL (roadmap §4). WARN H-R2 (origin queue) and H-R5 (long waits in the queue) are expected above capacity.

## Cells and seeds

- **Inflow cells:** q ∈ {1,200 (below critical, the "do no harm" cell), 1,600, 2,000, 2,400} veh/h.
- **Tuning seeds:** 7,110,100–7,110,119, i.e. 20 per cell, the same seeds in every cell and for every controller (paired).

## Controller families and grids

| Family | Parameters | Grid |
|---|---|---|
| NC | — | — |
| Constant AV cap (all AVs on edges 2–4, every lane-piece, from t = 40 s) | cap c (m/s) | {3, 5, 7, 9, 11, 13, 15, 18} (23 = NC) |
| Feedback meter (Vinitsky 2018, §III-E) at node 3 | K_F, n_crit (T = 30 s, 6 s green fixed) | K_F ∈ {10, 20, 40} × n_crit ∈ {4, 6, 8, 10, 12, 14}. The paper's (20, 8) is in the grid. |

That is 27 controllers × 4 cells × 20 seeds = 2,160 runs.

## Selection rule (fixed now)

- **Score:** for each controller, score = the mean over the 4 cells of the **median** (over the 20 seeds) of the mean time in system.
- **Tuned parameter per family:** the one with the lowest score. Ties within 0.1 % go to the parameter closest to NC: the highest cap, or the meter's paper values.
- **Also reported (not used for selection):**
  - the per-cell best parameter, which becomes the informed reference I for a later hybrid gate;
  - the median of paired differences against NC per cell, with the 95 % bootstrap CI.
- **Frozen output:** `docs/lab/t1_bn4_baselines_frozen.json` and `docs/lab/t1_bn4_r2_baselines.md`, committed before any R5 head-to-head.

## Expected and reported regardless

- **Below critical** (q = 1,200), no controller should beat NC by much, and some will harm. Any harm is reported.
- **If the tuned meter or a constant cap reaches peak capacity** (outflow ≈ 1,087 veh/h; R1 v2 numbers are informational only until R1 v3 is analysed), then the DRL headroom over tuned baselines on BN4 is small. That must be stated before any DRL claim.

## Addendum (before any R2 run, 2026-10-01): AV actuator rate limits

The DRL smoke test found SUMO emergency braking (9 m/s²) when AV caps dropped abruptly. Vinitsky et al. bounded the speed-limit change so that "unphysical accelerations are not commanded" (−1.5 / +1.0 m/s²).

So, for every controller that uses the AV actuator (constant caps and DRL alike), the following now hold:
- each lane-piece cap moves by at most −1.5·Δt and +1.0·Δt per decision;
- no AV is asked to brake harder than 1.5 m/s² (applied cap ≥ v − 1.5·Δt).

Emergency-braking warnings are counted as health WARN H-R4b.

T0b (already run) used the earlier abrupt caps. Its finding that the AV actuator has authority stands. Its exact cap numbers are not reused.
