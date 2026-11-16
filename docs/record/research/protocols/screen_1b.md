# Screen #1b: leader-adaptive safety margin on fresh TGSIM data

Fixed 2026-10-16 before any TGSIM trajectory is read (V82). It supports no claim: the outcome is **CONTINUE** or **STOP**.
The commit hash is written into the result. It is identical to `screen_1.md` except for the three changes below. Every other rule, constant and gate is copied unchanged: score, regimes, d_safe, arms F/O/H/P, α = 0.05, the validity limit 0.075, the 3 % gain, the 2-min blocks, B = 2,000, ≥ 300 windows, ≤ 5 % clipped, CONTINUE/STOP.

## Change 1: Data (fresh, never looked at)
- **Sites.** Two TGSIM datasets from data.transportation.gov:
  - **I-90/I-94 Stationary** (`9uas-hf8b`, Chicago, 6 runs);
  - **I-395** (`97n2-kuqi`, Washington DC, 1 run).
  - Each is one site, and cross-site fitting is used in both directions, as in #1.
- **Not touched.** I-294 L1/L2 and I-90/I-94 Moving stay unread for confirmation.
- **Units.** Speed is `speed_kf` (m/s), with the same centred 1-s average for outcomes. Raw `speed_kf` sets the regime.
- **Time.** Rounded to 0.1-s steps.
- **Tracks.** (run, id) split where the time gap is > 0.2 s. I-395 has no run column, so run = 0.
- **Blocks.** 2-min blocks never cross runs.

## Change 2: Leaders (TGSIM has no `Preceding` column)
- **Travel direction.** For each (run, lane_kf): the mean of the tracks' unit displacement vectors, start to end. This is geometry only.
- **Leader.** At each time step, a vehicle's leader is the nearest vehicle **ahead** in the same run and lane, by position projected on that direction. Only gaps of 0–150 m are accepted.
- **Leader window.** As in #1, a window counts if its vehicle is someone's leader at the window's start step.
- **Lanes.** All lanes are included, ramps too. A straight projection is an approximation on a curved camera view, and this is disclosed.

## Change 3: Tracker step (the fix found on throw-away NGSIM, disclosed in `screen_1_result.md`)
- **The problem.** The shared tracker got outcomes in large batches, and each moved q by a full step, so q swung widely.
- **New rule.** O updates once per second. All outcomes that became known in the last second are summed:
  q ← max(1, q + (0.5 / c_r) · Σ (1{s > q_used} − α)).
- **c_r.** For regime r, the median number of outcomes per non-empty second on the **fitting** site. These are counts of windows, never outcomes, so they are fixed before any score is computed.
- **Placebo P.** The same sum rule, applied to batches of c_r windows taken from the shuffled order.

## Integrity
- **Tests before data.** Screen #1's 7 tests pass, plus:
  - batch-normalised tracking reaches α ± 0.01 on synthetic data;
  - leader matching picks the nearest same-lane vehicle ahead, and ignores vehicles behind, in other lanes and in other runs.
- **Run once.** A bug found afterwards means: fix, re-run, and log both runs.
- **Reading the result.** The NGSIM lesson stays in view: a CONTINUE by rule 3(a) alone (only validity) is reported as such.
