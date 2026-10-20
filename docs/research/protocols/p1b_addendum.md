# P1b addendum to the P1 protocol (realism and fairness re-run)

Status: **DRAFT (V107), awaiting one lean review and the author's approval.**
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
