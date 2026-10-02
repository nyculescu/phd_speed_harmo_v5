# Track 1 (BN4), phase R5 head-to-head on test seeds: protocol

*Committed before any R5 run. 2026-10-02 · exploratory head-to-head (roadmap §7); the confirmatory run (R6) is separate.*

## When this runs

Only for a DRL candidate that passed the R3 screening (C1 + C2 + C3) and then an F-class training (3 learner seeds, ≥ 500 updates). The candidate is frozen: config, commit and model files are fixed before R5.

## Comparators (frozen in `docs/lab/t1_bn4_baselines_frozen.json`, tuned on seeds 7,110,100–7,110,119)

| Comparator | Why it is here |
|---|---|
| NC | sanity check |
| Best constant AV cap (`cap:18`) | yardstick on the same actuator |
| Tuned AV feedback (`avfb:2:10`) | tuned classical controller on the **same actuator** as the DRL |
| Tuned feedback meter (`meter:10:6`) | tuned classical controller on a **different**, infrastructure actuator; reported for context |

## Seeds and cells

- **Seeds:** test seeds 7,110,500–7,110,529 (30 per cell, fresh).
- **Cells:** q ∈ {1,200, 1,600, 2,000, 2,400} veh/h.
- **Pairing:** the same seed is run for every controller.

## Path and metrics

- **Path:** `vsl_lab/jobs/bn4_eval.py`, the same code path for every controller: 40 s warm-up, 900 s control, uncontrolled drain.
- **DRL policy:** deterministic, **final policy** of each learner seed. The best-validation checkpoint is reported as a secondary result.
- **Primary metric:** mean door-to-door time per vehicle, including the origin queue.
- **Co-headline:** outflow over the control window.
- **Statistics:** the median of paired differences (DRL − comparator) per cell, with a 95 % percentile bootstrap CI (10,000 resamples). The three learner seeds are reported separately and also pooled as the median over learners per test seed.

## Readings (fixed now)

- **DRL beats a comparator in a cell** if the median paired difference in door-to-door time is < 0 and its CI excludes 0, for the pooled learners **and** for at least 2 of the 3 learner seeds.
- **"DRL beats tuned classical control on the same actuator"** if it beats `avfb:2:10` **and** `cap:18` in ≥ 2 of the 3 congested cells (q ≥ 1,600), with no significant harm at q = 1,200 (CI upper bound ≤ +5 %).
- **Against the meter**, whatever happens is reported. No claim is made unless the same rule holds.
- **Side constraints:**
  - teleports 0;
  - health FAIL share ≤ 1 %;
  - emergency-braking warnings reported per controller.
