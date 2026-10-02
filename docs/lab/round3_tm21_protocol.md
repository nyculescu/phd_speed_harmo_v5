# Round 3: TM21 speed harmonisation through CAVs vs TM20 posted VSL (merge plant), pre-registration

*Committed 2026-10-02, before any Round 3 run. Branch `claude/vsl-lab-core`. Runs only after the current queue: realism gate → B-P6 → MRG3-v3 R2.*

## Author decisions (2026-10-02)

- **Seeds:**
  - new block 7,150,000–7,150,299 for CAV-arm calibration, plant checks and tuning;
  - DRL training 7,250,000–7,259,999;
  - head-to-heads on the **shared** T2 test and reserved seeds (7,120,500–7,120,999), so the arms are paired seed by seed;
  - DRL validation uses the T2 validation range 7,120,300–7,120,499, the same range as every T2 DRL run;
  - all inside the approved 7,100,000–7,399,999 block.
- **CAV penetration:** 10, 25 and 50 %.
- **CAV dynamics:** SUMO ACC/CACC.
- **Arms:** all three (A, B, C below).

## ARC-IT framing (checked in the local ARC-IT copy, v6 `docs/arcitwebsite-20260715/`)

- **TM20 "Variable Speed Limits"** (sp138): limits set by lane and displayed by roadway equipment to all drivers.
- **TM21 "Speed Harmonization"** (sp68): speed recommendations (regulatory or advisory) sent through connected-vehicle V2I to upstream traffic approaching bottlenecks.

## Plant

**Base:** MRG3-v3 with the **primary human driver variant** chosen by the realism gate (`t2_realism_protocol.md`). If no variant passes, Round 3 does not run.

**CAVs:**
- vType `cav`, `carFollowModel="CACC"`, every ACC/CACC parameter at its SUMO default (SUMO vType table; `tau` 1.0 s);
- length 5 m; `speedFactor` 1 and `speedDev` 0 (exact compliance with whatever limit applies to them); LC2013 defaults;
- a share p ∈ {0.10, 0.25, 0.50} of **all** vehicles. Trucks stay at 10 % and human-driven. Human cars make up the rest, with the compliance mix p_nc applied to them.
- **Fallback to ACC:** a CACC vehicle behind a non-CACC leader is expected to behave like ACC. This is [VERIFY in the SUMO source]. It is checked behaviourally in T-CAV0.

**Known SUMO caveat** (ACC and CACC doc pages): the models "produce collisions at the default step-length of 1 s", and lower steps are recommended. The plant runs at 0.5 s, hence T-CAV0.

## Arms (same plant, same demand, same seeds)

| Arm | Actuator | Who is controlled |
|---|---|---|
| **A** (TM20) | posted VSL on up1 + up0a, as in T2 | all drivers, through human compliance (speedFactor groups); no CAVs |
| **B** (TM20 + enforcers) | the same posted VSL | all drivers; CAVs obey the posted limit exactly and so pace the humans behind them |
| **C** (TM21) | per-lane speed commands to the CAVs in the control zone (up1 and up0a: 2 sub-zones × 3 lanes = 6 targets); no posted VSL change | only CAVs |

**CAV speed mechanism (author specification, 2026-10-02; used in arms B and C):**
- The controller sets **discrete targets**. Each CAV moves its ACC/CACC **set speed** (`vehicle.setMaxSpeed`; CAVs identified **by ID**, the `av@<id>` lesson from BN4) toward its target in **1 km/h steps**.
- **When the next step is allowed:** when both of the following hold:
  - at least **X s** have passed since the last step;
  - the CAV has **reached** its current set speed: |v − v_set| ≤ 0.5 km/h, or v has gone beyond v_set in the direction of the change.
- **The ACC/CACC speed controller** does the tracking (SUMO default gain), so the effective ramp rate is also limited by the vehicle's own dynamics. It is reported.
- **Arm C targets:**
  - the 6 lane × zone targets on up1 and up0a;
  - a pre-zone staircase, mirroring arm A's Carlson safety VSLs: lane *i* on up2 gets min(1, b_up1,i + 0.2), and on up3 gets min(1, b_up1,i + 0.4);
  - a CAV that leaves the zone steps back up to the lane limit with the same mechanism.
- **Arm B targets:** the posted limit of the CAV's current lane, using the same mechanism. So B and C differ only in **who sets the target**.
- H-R7 asserts the set speeds.
- **X is chosen by the safety check T-X below,** before T0-C.

**References:**
- **NC-human:** arm A's NC.
- **NC-p:** CAVs present, no control. This is the NC for arms B and C.
- **The CAV-dynamics effect** (NC-p − NC-human) is reported separately from the control effects. ACC/CACC dynamics alone change traffic, and that change must not be credited to control.

## Tool checks (criteria fixed now)

| Check | Seeds | Runs | PASS / rule |
|---|---|---|---|
| **T-CAV0**: CAV sanity (throw-away, disclosed) | 7,150,000–7,150,009 | NC-p at p ∈ {10, 25, 50 %}, at the primary variant's selected cell; plus at 50 %, CAV vType = ACC instead of CACC | **0 collisions** (H-R4) and 0 health FAIL at every p (emergency-braking warnings reported). **CACC vs ACC:** if the two give identical hashes, CACC never acts cooperatively in this traffic; reported as such. **If any collision at 0.5 s:** stop, report to the author, and do not change the step length unilaterally (it would change the realism-validated plant) |
| **T-X**: step interval X (safety) | 7,150,070–7,150,089 | p = 50 % (worst case), at the selected cell. NC-p vs arm C under a stress schedule (all 6 targets alternate between b = 0.4 and b = 1.0 every 300 s in the control window), for X ∈ {0.5, 1.0, 2.0} s; 80 runs | **X = the smallest candidate** that has 0 collisions, 0 health FAIL, and an emergency-braking rate (SUMO emergency-braking warnings per 1,000 veh-km) whose median paired difference vs NC-p is ≤ +10 % of NC-p's median rate. **If none passes:** stop and report to the author. Effective CAV ramp rates are reported |
| **T0-C**: CAV commands bind (per p) | 7,150,010–7,150,039 (10 per p) | NC-p vs arm C with all 6 targets at 0.4 × 33.33 m/s | application-area outflow (up0a end loops, per lane, [1,500, 2,700) s), median paired difference ≤ −10 % of NC-p with the CI excluding 0 (same rule as T2 T0). **A p that fails is dropped from arm C** (a cheap KILL) |
| **T0-B**: posted VSL with enforcers binds (per p) | same seeds | NC-p vs arm B `const:0.4` | same rule. Also reported against arm A's T0 at the same seeds |
| **T1c-C**: control matters (per p passing T0-C) | 7,150,040–7,150,069 | NC-p vs arm C constant targets b ∈ {0.6, 0.8}, and MTFC with its rate b sent as the CAV target (ρ̂ ∈ {20, 25, 32}, paper gains) | any controller reduces median door-to-door time by ≥ 5 % vs NC-p (median of paired differences, 95 % bootstrap CI excluding 0) |
| **T3**: determinism | 5 re-runs drawn from the T1c seeds | NC-p at 25 % | hash-identical |

**Run counts:**
- T-CAV0: 40.
- T0: 3 p × 10 seeds × 3 runs (NC-p, C, B) = 90.
- T1c: up to 3 p × 30 seeds × 6 runs = 540 (only p values that pass T0-C).
- T-X: 80.
- T3: 5.

## Later stages (each pre-registered as an addendum before its runs)

**R2 tuning** (seeds 7,150,100–7,150,299, for the surviving p values, arms B and C):
- constant targets;
- MTFC through the arm's actuator;
- for C only, a density-feedback rule on the CAV targets;
- the grid size is set in the addendum, from T-CAV0 run times.

**DRL on arm C** (the author's note: the commands stay discrete):
- PPO with a MultiDiscrete action: 6 lane × zone targets, each from {50, 60, …, 120} km/h;
- 30-s decisions; the low-level 1 km/h staircase above does the actuation;
- observations: per-lane loop data, merge density, ramp flow, CAV probe means per lane and zone, the last action, and a 4-step history;
- reward: door-to-door TTS, including origin queues, with the degenerate-policy screen;
- budget: the F class of `CLAUDE.md`.

**Comparison** (the thesis result), per p:
- tuned A vs tuned B vs tuned C vs DRL-C on the shared test seeds, paired;
- door-to-door time co-headlined with throughput, plus on-ramp users' delay and an exposure-normalised emergency-braking rate;
- a claim needs R6 on the reserved seeds.

## Honest prior

BN4's AV caps (10 % and 25 % AVs) were a coarse, discrete version of arm C. There, constant caps gained at most −1.5 % vs NC and AV feedback was worse. Sparse AVs on a multilane road slow only their own lane.

Arm C differs in three ways: per-lane coordinated targets, a penetration sweep, and a merge mechanism. A T0-C FAIL at 10 % and 25 % is a plausible, cheap outcome, and it would be reported as a result about TM21 at low penetration.
