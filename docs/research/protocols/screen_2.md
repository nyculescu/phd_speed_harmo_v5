# Screen #2: online-calibrated green-light commit margin (Hamburg 13–24 Sep 2023, throw-away)

Fixed 2026-10-16 before any data is read (V80, V81). It supports no claim: the outcome is **CONTINUE** or **STOP**.
The commit hash of this file is written into the result. The data from 25 Sep onwards are never kept.

**Question.** A car approaches a traffic light and gets a forecast of the next green window.
- It **commits** to arrive inside the predicted green, shrunk by a margin m (s) at both ends.
- If the light is then not green on arrival, the commitment is **broken** (a loss).
- If no safe commit is possible, it plans to stop.

Does a margin updated online beat a margin fixed per signal from earlier days?

## Rule 1: Data
- **Archive.** TU Dresden OPARA archive (MD5 `11d66d59…f9280`; CC BY 4.0, source dl-de/by-2-0). It is streamed once and never extracted.
  - Kept: rows whose `received_time` falls on local dates (Europe/Berlin) 13–24 Sep 2023, and only for the selected datastreams.
- **Metadata.** One snapshot of the live SensorThings API maps each datastream to its signal group, lane type and layer.
- **Signals used.** Primary-signal datastreams of vehicle lanes (`KFZ`). Green means code 3; every other code is "not green".
- **Timing.** Switch times come from `phenomenon_time`. A switch becomes *known* to the car only at its `received_time` (no future information).
- **Selection.**
  - Eligible groups are those with a state change in ≥ 80 % of the 06–22 h hours of 14–17 Sep. The 13th is partial: the archive starts at about 15:18.
  - Up to 40 groups are drawn with seed 7,421,001.
  - If fewer than 20 are eligible: **STOP (data)**.

## Rule 2: Approaches, forecast, arms
- **Approaches.** One approach per group every 60 s, 06:00–22:00 local. It starts 200 m before the stop line at 13.9 m/s (50 km/h).
- **Commit window.** A constant speed in [8.3, 13.9] m/s gives a reachable arrival window [t + 14.4 s, t + 24.1 s].
- **Forecast,** using only what is known at t:
  - next green start = last known green start + median cycle length of the past 60 min;
  - green length = median green length of the past 60 min.
  - The light currently green is included. With no history: no forecast and no commit (counted).
- **Decision.** Commit if the reachable window overlaps [ĝ_start + m, ĝ_end − m]. Aim for the earliest such arrival; otherwise plan to stop.
- **Outcomes.** Loss ℓ = 1 if committed and the light is not green at arrival. **Pass** = committed and green at arrival, so no stop.
- **Arms** (ε = 0.05):
  - **F, fixed:** per group, the smallest m on a 0.5-s grid in [0, 20] s whose loss rate on 14–17 Sep is ≤ ε (m = 20 s if none is). This is the strongest static opponent.
  - **O, online:** per group, m ← max(0, m + 1.0·(ℓ − ε)) after each commit's outcome, applied when the outcome is known (at arrival). It starts at F's value.
  - **H, hindsight:** per group, F's rule fitted on the evaluation days. Used for headroom only.

## Rule 3: Decision (evaluation 18–24 Sep; cells = weekdays 18–22, weekend 23–24, pooled over groups)
- **Loss rate** = losses / commits. **Valid** means ≤ ε + 0.025 = 0.075.
- **Pass gain.** P = O's pass share minus F's pass share, over all approaches, in percentage points. The 95 % CI is a cluster bootstrap over group-days, B = 2,000, seed 7,421,002.
- **A cell is a WIN** if O is valid and either:
  - (a) F is not valid there, or
  - (b) P ≥ 2 points with the CI lower bound > 0.
- **CONTINUE** if at least one cell is a WIN. **STOP** otherwise.
- **Reported always:** H vs F (headroom), the no-forecast share, every cell's numbers.

## Rule 4: Sufficiency
- A cell is gated only if F and O each have ≥ 400 commits there.
- If no cell is gated: **STOP (data)**.

## Rule 5: Integrity
- **Unit tests pass on synthetic signal logs before any archive read:**
  - the forecast and the decision use no row with `received_time` > t (a no-leak test that perturbs future rows);
  - on stationary synthetic losses, the online margin's loss rate comes within ε ± 0.01;
  - the reachable-window arithmetic is checked.
- **Run once.** A bug found afterwards means: fix, re-run, and log both runs.
- **Scope.** All constants are as written. Energy models, queues and the live feed belong to the confirmatory stage.
