# P1b addendum to the P1 protocol (realism and fairness re-run)

Status: **APPROVED (V108, 2026-10-20): author decisions 1–5 = all defaults; the review fixes R1–R7 below override the sections above where they differ.**
- Everything not changed here is exactly as in `p1_incident_information.md`, V99 plus the V100 addenda: arms, statements S1a/S1b/S2/S3, statistics, both views, bracket, placebo, imperfection map, run-once, frozen worktree.
- P1 stays in the record as the earlier run. P1b becomes the paper's main result. Both are reported.

**Why.** Three reasons:
- the mainline-metering prior art (V105): field meters use amber or activate only at low speed, so amber is necessary;
- the controller-family confound (V103): the incident plans could not use PI-law control;
- realism: drivers who run amber or early red.

## B1. Meter signal with amber and minimum red

- **Cycle:** green → amber → red, with the cycle length c(q) as before (continuous signal rule, V100).
- **Green:** fixed 6 s, as before.
- **Amber:** **3 s**.
- **Red:** c − 6 − 3, at least **2 s**.
- **Rate cap:** the shortest cycle is 11 s, so the maximum commanded rate is capped at 2 × 4 × 3600 / 11 ≈ 2,618 veh/h. This is disclosed; the grid's top constant rate is 2,600.
- **SUMO:** vehicles see amber as state `y`. A vehicle continues through amber if it cannot stop comfortably (SUMO's default dilemma-zone rule).
- **Reported per arm:** emergency stops at the meter, and the approach speed of the first stopped vehicle at red.

## B2. Amber and red runners (sensitivity rows only)

- **Driver mix:** a vType distribution in which a share **s** of drivers are "runners", with:
  - `jmDriveAfterYellowTime` = 3 s (they ignore amber);
  - `jmDriveAfterRedTime` = 1.5 s;
  - `jmDriveRedSpeed` = 13.9 m/s.
- **Before any data, a test must show** that a runner crosses within 1.5 s of red onset and that a normal driver stops.
- **Main analysis (S1–S3):** s = 0, as in P1.
- **Sensitivity rows** (descriptive; S1-style relative CIs, no claims): s ∈ {10 %, 30 %} for the tuned arms N, PI, ID, IP. No re-tuning: the arms are tuned at s = 0. This measures the leakage the meter suffers.
- The reviewer looks up published meter-violation rates. If a sourced value exists, it is added as a third row before any data [VERIFY].

## B3. PI-law plans in the action set

- **Action set:** A grows to G ∪ G_PI, each with {stay, back}. G_PI is the PI-arm grid of P1 (as tuned in P1's §2). ID, IP, OR_in and ORX choose from the larger set.
- **Disclosed consequence:** A larger set inflates OR_in's selection-on-noise. The bracket rules handle this: ORX is a lower bound, and the placebo is reported.

## B4. Queue reporting

- **Per arm and cell:** the maximum meter queue (vehicles and metres) against the available upstream length (edges 1–2).
- **No queue cap.** If any arm's maximum queue exceeds the available length in more than 5 % of runs, this is flagged in the limits.

## B5. Seeds (proposed; need the author's approval)

| Use | Seeds |
|---|---|
| Tool checks | 7,400,260–279 |
| Tuning | 7,400,300–339 |
| Evaluation | 7,400,600–699 (100 seeds) |
| Replicates | as P1 (seed + k × 10,000,000) |
| Smoke runs only | 7,400,000–009 |

## B6. Cost (estimates)

- **Runs:** about 1.5–2× P1, because the action set is about twice as large and the runner rows are added.
- **Time:** about 12–18 h at 32 workers.
- **Mitigations if needed:** drop R = 4, or the runner rows at s = 10 %.
- **Lean mode (V107):** one reviewer for this page; one build agent; one code reviewer; one verifier.

## Review fixes (lean review, V108; these override B1–B6 where they differ)

- **R1 (B3/B6, cost):**
  - G_PI = the **10 PI controllers with the lowest pooled median on the P1b tuning seeds, per q**, fixed before evaluation.
  - A = (G ∪ G_PI) × {stay, back} = 120 actions; ties are broken in the order G, then G_PI.
  - Estimate: about 11–13 h at 32 workers.
- **R2 (B1, buildability):**
  - c(q) = max(11, 28,800 / q) s;
  - **every law clips q to [q_min, 2,618] veh/h** (anti-windup);
  - signal: G if phase < 6, y if 6 ≤ phase < 9, otherwise r;
  - a unit test checks that the continuous rule never cuts an amber, or a red shorter than 2 s.
- **R3 (switch into a PI plan):** the commanded q, the signal anchor and the 30-s update grid carry over; n(k−1) = n(k) at the plan's first update.
- **R4 (runners):**
  - runners are drawn **per vehicle in the route file** from rng(seed + a new salt), so the same vehicles run in every arm;
  - `jmDriveAfterRedTime` ≥ 0 also makes them always drive at amber (SUMO docs);
  - the pre-data test must show that the red age counts from the actual onset of `r`, even though the state is set every tick;
  - report the realised red-crossing share and collisions.
  - The share s is a model parameter, not a field violation rate. **Context:** Madison Beltline (WisDOT, 2005): 0.9–9.0 % of single-occupant vehicles did not stop at metered red; temporary work-zone meters: 45.5–75.0 % compliance (Edara et al. 2012). s ∈ {10 %, 30 %} brackets these; no third row.
- **R5 (B2 scope):** at each s, run every L0 arm (N, FX, FB, PI, AD), ID and IP. Rows: ID vs each L0 arm, IP vs ID, and each arm vs itself at s = 0. 95 % CIs; descriptive.
- **R6:** report the realised discharge (vehicles crossing on green, amber and red) against the commanded rate, per arm.
- **R7:** queue metres = the distance from the stop line to the last halted vehicle on edges 1–2.
- **Seeds (decision 5):** approved as in B5, all inside the approved v5.B block, with 700–999 untouched. Disclosed: the tool-check range sits in the block's tuning range, and tuning in its validation range.
