# R3 pilots (P class, exploratory): protocol

*Committed before any R3 training run. 2026-10-01 · roadmap §5 (run classes), §8 (variant axes), §9 (criteria)*

**Purpose:** prove the DRL pipeline *learns* on credible plants before going wide. Pilots are screening runs:
- 150 PPO updates;
- 1 learner seed;
- validated on fixed validation seeds;
- nothing here is a claim.

Every run goes into the ledger.

## Common settings

- **Trainer:** `vsl_lab/train/train_sb3.py`.
  - The learner and all env workers are pinned to E-cores; `torch.set_num_threads(1)`.
  - Two-timescale thermal watchdog (10-min mean 90 / 87 °C; 10 s cap 93 °C).
  - Validation every 25 updates and at the end, deterministic policy, fixed validation conditions and seeds. The best-validation checkpoint and the final policy are both saved.
  - The health stop rule is a FAIL share > 1 %.
- **PPO:** MLP [128, 128] (tanh) for BN4 and [64, 64] for the ring; 10 epochs; lr 3e-4; γ 0.99; GAE λ 0.95; clip 0.2; no entropy bonus.
- **Seeds:** learner seed 0.
  - Training episodes: 7,210,000–7,211,999 (T1) and 7,230,000–7,231,999 (T3).
  - Validation: T1 uses 7,110,300–7,110,301 × q ∈ {1,600, 2,000, 2,400}; T3 uses 7,130,300–7,130,302 × L ∈ {230, 260}.
- **Reference values on the same validation seeds and conditions:** NC, the best constant, and the frozen R2 tuned baselines. They are computed with the same env code and logged next to the pilot.

## Pilots

| ID | Plant | Structure | S | A | R | Envs × n_steps (samples per update) |
|---|---|---|---|---|---|---|
| **P1** | BN4, q ~ U[1,000, 2,000] (Vinitsky's training range), 40 s warm-up, 900 s control, Δt 1 s | direct, Lagrangian (10 % AVs) | S-VIN: per lane-piece human and AV density and speed, outflow 20 s, previous action | A-VIN: 22 AV caps, rate-limited | R-OUT: outflow over the last 20 s | 8 × 225 (1,800) |
| **P2** | RING22, L ~ U[220, 270], 75 s warm-up, 300 s control, Δt 1 s | **hybrid**: DRL sets FollowerStopper's U ∈ [0, 10] m/s; FollowerStopper drives at 0.1 s | AV speed, relative speed, gap, 38 s mean AV speed, previous action | U | mean speed of all vehicles / 5 − 0.1·\|a_AV\| | 8 × 150 (1,200) |
| **P3** | RING22, as P2 | direct: DRL sets AV acceleration ∈ [−1, 1] m/s², Δt 0.5 s | as P2 | acceleration | as P2 | 8 × 300 (2,400) |

## Screening criteria (P class; written now)

- **Learns (C1-pilot):**
  - the validation metric of the final policy beats the initial (untrained) policy on the same seeds;
  - the progress curve's mean episode reward over the last 25 updates is higher than over updates 1–25.
- **Does something useful (C3-pilot):** the final or best-validation policy beats **NC** on the mean validation metric by:
  - **≥ 5 %** for P1 (outflow over the control window);
  - **≥ 5 %** for P2 / P3 (mean speed).
- **Not degenerate (C2-pilot):**
  - P1 must also beat the best constant cap on validation;
  - P2 / P3 must beat the best fixed U from R2.
- **Health:** 0 FAIL among training episodes.

A pilot that meets C1 + C3 + C2 goes to an **F-class** run: ≥ 500 updates, 3 learner seeds, convergence check C1 (roadmap §9). Pilots that fail are logged with their curves, and the next SAR variant on the §8 axes is tried. A failed pilot is never re-run on the same validation seeds and then reported as if it had been the first try.

## Honest expectations, written before training

- **P1:** Vinitsky's RL "matches" tuned feedback metering above the critical inflow. T0b shows the paper meter brings outflow to about the plant capacity. So the realistic best outcome is DRL ≈ meter, which is better than NC and than constant caps, but **not** better than the tuned meter.
- **P2 / P3:** PI-with-saturation already reaches the ring's equilibrium speed in the calibration run. The realistic best outcome is DRL ≈ PI and better than NC. **No beat over the tuned classical controller is expected on the ring.**
- Both are pipeline validations. The thesis-relevant search for a real DRL edge starts with T2 (merge with tuned MTFC), with the niches in roadmap §6.
