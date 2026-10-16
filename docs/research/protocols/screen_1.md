# Screen #1: leader-adaptive safety margin (NGSIM, throw-away)

Fixed 2026-10-16 before any data is read (V80, V81). It supports no claim: the outcome is **CONTINUE** or **STOP**.
The commit hash of this file is written into the result.

**Question.** One car follows a real recorded leader. Its safety gap assumes the leader can brake at most b̂ (m/s²).
- **Fixed margin:** b̂ is one value per traffic regime, fitted on another road.
- **Online margin:** b̂ is updated after every outcome.

Does the online margin give shorter safe gaps at the same safety, or stay safe where the fixed one fails?

## Rule 1: Data
- **Source.** NGSIM I-80 and US-101 (data.transportation.gov `8ect-6jqj`); every row is used, and all of it is throw-away.
- **Conversions.** Feet become metres. Exact duplicate rows are removed.
- **Tracks.** A track is (location, Vehicle_ID) split wherever the time gap exceeds 0.2 s. Vehicle IDs repeat across periods.
- **Leader speed.** v_L comes from `v_Vel` with a centred 1-s moving average. It is used for outcomes only.
- **Windows.** Each leader track is cut into consecutive 8-s windows, starting 5 s after the track starts. A window is used if the leader has data for the next 10 s.

## Rule 2: Score, regimes, arms
- **Score of window k.** s_k is the strongest braking the leader actually did: the maximum over t in the window and h ∈ {1, 2} s of (v_L(t) − v_L(t+h))/h, clipped to [0, 10] m/s².
- **Miss.** An arm misses window k if s_k > b̂_k.
- **Regime.** Set from the raw leader speed in the 5 s *before* the window starts (causal):
  - R1: minimum < 2 m/s (stop-and-go);
  - R2: mean < 10 m/s (congested);
  - R3: everything else, report-only.
- **Required gap.** d_k = d_safe(b̂_k, v) + 2 m, with v the leader speed at window start (steady following).
  - d_safe is the largest closing distance between two cars. The ego reacts for 0.5 s at +2 m/s², then brakes at 4 m/s² to a stop. The leader brakes at b̂ to a stop.
  - d_safe is computed exactly on a 0.01-s grid. That keeps it valid when b̂ < 4, where RSS Lemma 2 is not.
- **Arms** (α = 0.05; seed 7,420,001 for all random draws):
  - **F, fixed:** per regime, the (1 − α) quantile of s on the *other* site. This is the strongest static opponent.
  - **O, online:** one tracker per regime, shared by all cars at the site (roadside or V2X), starting from F's value.
    - Window k uses the tracker's value when the window starts.
    - Its outcome is applied when it becomes known (window end + 2 s): q ← max(1, q + 0.5·(1{s > q_used} − α)).
    - Events are processed in time order.
  - **H, hindsight:** per regime, the (1 − α) quantile on the evaluation site itself. It sees the future and is used for headroom only.
  - **P, placebo:** O run on the same windows in a random order. Report-only.

## Rule 3: Decision (both directions: I-80 → US-101 and US-101 → I-80; cells = R1, R2)
- **Valid** means a miss share ≤ α + 0.025 = 0.075.
- **Efficiency gain.** E = 1 − mean(d_O)/mean(d_F). The 95 % CI is a block bootstrap over 2-min blocks of window start time, B = 2,000.
- **A cell is a WIN** if O is valid and either:
  - (a) F is not valid there, or
  - (b) E ≥ 3 % with the CI lower bound > 0.
- **CONTINUE** if at least one gated cell is a WIN. **STOP** otherwise.
- **Reported always:** H's gain over F (the headroom), P vs O, and every cell's numbers.

## Rule 4: Sufficiency and noise
- A cell is gated only if it has ≥ 300 windows. That gives about 15 expected misses at α = 0.05.
- A cell is also not gated if more than 5 % of its windows hit the 10 m/s² clip, which marks the cell as "noise".
- If no cell is gated: **STOP (data)**, and the author re-plans.

## Rule 5: Integrity
- **Unit tests pass on synthetic data before any NGSIM read:**
  - d_safe matches Lemma 2 when b̂ ≥ 4, and brute-force simulation when b̂ < 4;
  - on stationary synthetic scores, the tracker's miss share comes within α ± 0.01;
  - regime labels and thresholds never use data from after the window starts.
- **Run once.** A bug found afterwards means: fix, re-run, and log both runs.
- **Scope.** Nothing here is tuned on NGSIM outcomes. All constants are as written: α, 0.5, 2 m, 0.5 s, 2 and 4 m/s², the clip, 300, 3 %.
