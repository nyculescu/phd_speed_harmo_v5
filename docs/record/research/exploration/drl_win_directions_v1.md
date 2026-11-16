# Where could learning-based control beat the tuned controllers? Design memo v1

Written 2026-11-10 by the project-review session, from the brief `docs/handoff/2026-11-10_fable_drl_exploration_prompt.md`. State of the records: V502 (baseline v5). It replaces `drl_win_directions_v0.md`, which stays beside it as the Phase A text.

**Status.** A proposal. Nothing in it is decided. No simulation ran, no seed was used, no ledger row was written, nothing was installed or trained. Running any screen needs the author's approval of the rental, the spend and the seeds.

**How it was built.**
- Phase A: nine independent readers (ledger V1-V501, results, code, earlier sweeps, web literature, stored S6 rows). Reports: `phase_a_reports/`.
- Phase B, round 1: four critics and three stored-row analyses attacked the v0 screens. Reports and scripts: `phase_b_round1/`.
- Phase B, round 2: for each screen, three independent protocol drafts, two judges, one synthesis, one skeptic and a revision. Reports: `phase_b_panel/`.
- An evidence-quality audit in both directions: seven readers. Reports: `phase_b_audit/`.
- A desk comparison of ten Stable-Baselines3 families, with two verifiers. Reports: `phase_b_sb3/`.
- The author's seven corrections to v0 are applied; §8 lists where.

**Reading rules for this memo.**
- "Exploratory" marks a number computed for this memo from stored rows. Those rows were already read for a verdict, so such a number supports no claim.
- "Record" marks a number stored by a registered reading or report.
- Positive percentages mean the first-named arm is better (lower for delay, close-following, braking and fuel; higher for flow). The level of each interval is stated.
- Code lines refer to the Plan B copy, `~/work/phd/wt/planb_v23/v5b/fleet/`.
- Literature found on the web was opened through a summarising fetch tool, not read in full. Every paper named here is [VERIFY].

**Terms.**
- p333: the fixed rule "0.8 s time headway in every zone".
- v3w: the frozen per-CAV PPO policy set (5 learners).
- Close-following: seconds with time-to-collision below 3 s, read at 1 Hz. It is a reward term.
- Delay: door-to-door delay with origin and ramp queues, in vehicle-seconds over the fixed window, against 100 km/h.
- 3E-C, 3E-D: Plan B's per-cell CMA-ES rules, searched for close-following (C) or for delay (D).
- Merge 2: the second on-ramp, road 4a. Its lane-end behaviour is an open item of the plant's verification record (PR-28).

## 0. Summary

1. **On delay, per-CAV DRL ties the best tuned rules in the two cells where that was tested well:** steady and TRUCK conditions at 5,300 veh/h, within about ±1 %. Nothing in the records shows a delay win there, and nothing shows a loss.
2. **The wider statement "DRL cannot win on delay" is not established.** It leaned on records from earlier plants, on closing records for other actuators that do not carry over, and on one rule search. The audit (§4) says which conclusions carry over.
3. **In the slowdown cell X1 the stored rows show a replicated delay edge of about 4 % over every stored rule** (exploratory). It sits at the second merge, whose lane-end behaviour is not validated, and the cells are closed. Screen R is parked (§5.3).
4. **The close-following edge is real against rules, and it has costs.** It is a reward term. Against the best searched rule, v3w is shown worse on hard-braking events, jam count and jerk; outside the reward nothing adds a sentence (§1.3).
5. **The plant is a choice, and its gaps cut both ways.** One simulator rule acts against any controller that lengthens headways; the unvalidated merge could remove the X1 edge or hide a cost of short headways; the capacity drop is not settled (§4.3).
6. **Two screens are protocol-ready and one is parked** (§5).
   - M, headways above 1.6 s at merge 2: PASS chance 3 %; about $1.2 and 16-22 h of build.
   - F, the frontier claim in TRUCK: pass chance about 15 %; $3.3 for stage 1, $13.8 for both. It needs TRUCK reopened against planb.md:575 and a trade-off claim form against planb.md:153; neither is assumed.
   - R, slowdown recovery: parked; its precondition is a new pre-registered cell.
7. **No Stable-Baselines3 family changes the lever.** The honest count of follow-ups is one (memory, built in our own trainer), and it is not live now (§6).
8. **Recommendation (§9):** do the plant items first (about 1,000 rules-only runs, $0.1-0.4, plus build hours), decide screen F's two questions on paper, and run no DRL screen and no training until both are done. Write the DRL chapter as a bounded result.

## 1. Evidence map

### 1.1 The five working hypotheses

**H1. For delay, a fixed short headway is close to optimal. Supported in steady and TRUCK conditions. Not supported in the slowdown cell X1.**

For:
- r1m3, 5,300 veh/h: policies against p333 on delay +1.5 [−0.8, +4.0], +1.8 [+0.3, +3.1], +1.3 [−1.6, +3.1] % (V337).
- "0.8 s gaps cut delay at every level (11-40 % less, rules and policies alike): a property of the headway, not of DRL" (V419).
- Confirmatory 2: no delay win in any of 20 cells (V359).
- TRUCK, S6 (record): no opponent is shown below p333 on delay. The delay search 3E-D started from p333 and ended tied with it: +0.01 % [−0.45, +0.25] at 95 % (`overfit_vs_p333`; its pick is not p333 itself).
- Oracles on r1m3 with the earlier plant P0: the speed-cap oracle shows headroom in 0 of 8 cases (V344); the headway oracle (1.2 s near the slowdown) pays delay −4.5 [−5.5, −3.0] % (V347). Both need a re-check on plant_c3 (§4.2).
- Every stored rule that lengthens headways near a merge has more delay than p333 in steady traffic: −2.1 to −7.5 % (exploratory, S6 rows; `phase_b_round1/critic_M.md` F3). These are static zone rules, and a simulator rule handicaps lengthening (§4.3).

Against:
- **X1, three independent 40-seed sets pooled (exploratory): v3w has less delay than p333, +4.2 % [+2.6, +5.5] at 95 % on 120 seeds, 5 of 5 learners.** No stored rule has a point estimate below p333 there, and v3w's interval is above 0 against every stored rule (`phase_b_round1/an_x1x2_delay_edge.md`). The round 2 test alone reads +5.5 [+2.9, +8.0] (`round2/report/test_table.csv`, 95 %, arm level). The S0/S1 map (planb.md:304) is the same 40 seeds re-run, not a second sample. The edge belongs to the v3w recipe: the earlier baseline-v3 policies on the same plant read −3.1 to −0.1 % against p333 in X1 (exploratory, 20 seeds).
- X2, pooled: +3.7 % [+2.6, +5.1] against p333, but about +2 % against the nearest rule (os0_10_10 +1.9 [+0.5, +4.0]; 3E-X2 +2.3 [+0.6, +4.0] on 80 seeds).
- A tuned rule, os1_15_10, had the lower training-mode median delay than p333 at every level 4,500-6,000 except 5,500 (V429; two rules only, no interval).
- At 7,000 veh/h, outside the intended use and report-only: v3w +3.7 % [+2.6, +5.2] against p333, 4 of 5 learners; only three rules ran there (s01_result.md §6; V475).

Reading: "DRL ties the 0.8-s rule on delay" is right for steady and TRUCK conditions at 5,300 veh/h. In X1 the v3w policies are ahead of every stored rule by about 4-6 %. No delay-objective rule search was ever run in X1 or X2. Against p333 that edge sits at merge 2 and follows lane-end stops (§1.4), so it is neither a DRL delay edge nor an artefact until PR-28 is closed.

**H2. The persistent edge is on close-following, which is in the reward; against no control the policies are not safer. First half supported; second half depends on the cell.**

- In the reward: TTC below 3 s and braking at 3 m/s² or harder, for the vehicle and, at half weight, its follower, weight 10 (b_env.py:811-817, :842-843).
- Edge against rules (record, TRUCK, 97.5 %): from +11.80 % [+4.97, +19.71] against 3E-C to +36.25 % (read6 map); rounds 1 and 2 replication against p333 5 of 5 (round_1_result.md:126, round_2_result.md:224).
- Against no control it fails in X1: −16.6 [−25.1, −8.4] % (round_2_result.md:265). Moving full-emergency events: 15 of 200 learner-runs in X1 and 24 of 200 in X2, against 0 for no control; p333 has 3 of 40 and 6 of 40 (round_1_result.md:202-206).
- Against no control it holds in TRUCK, +29.06 % [+26.35, +33.31], and in steady traffic, +45.86 % [+42.20, +50.47] (record, 95 %).
- In steady traffic the edge over 3E-C_TRUCK is not shown: +7.99 % [−11.71, +31.46] at 97.5 % (record, `S.map`).
- Part of the edge is outside the rewarded pair: humans behind humans, +8.1 to +23.4 % against p333 (V398).

**H3. The lever is narrow. Supported by the code; widening it has not helped so far.**

- The only command is `setTau`. The target applies only behind an ALKS leader within 150 m, otherwise 1.6 s. MLP actor, no memory. The merge-zone speed input covers merge 1 only (b_env.py:774-784, :925-935, :499-509; c_train.py:41-42).
- "The policy sees only local state, never demand itself; it has no memory and cannot anticipate" (V407).
- Widening tried: a 12-action speed-and-headway set, declined 88-95 % of the time (V339); a lane action, 30 and 68 collisions in 10 runs, not traced (V317); two look-ahead inputs, no delay gain (round_2_result.md).
- No record was found of a test with memory, with headways outside 0.8-1.6 s, or with a validated lane or merge actuator (inference from the search, not a quoted statement).

**H4. Tuned and searched rules absorb the headroom. Supported for delay in steady and TRUCK conditions; partly for close-following.**

- Close-following: 3E-C cuts the TRUCK edge from about 27 % to 11.8 % and is labelled "not converged at 100 generations" (V496). In X2 the margin fell from 22-31 % against os1_15_10 to 7.5-14.1 % against 3E-X2 (round_1_result.md:120; round_2_result.md:197-198).
- Against: rules do not transfer between cells (in TRUCK, copy −12.17 %, 3ex1 −3.64 %, 3e −4.45 % delay against p333, record), and searched rules lost part of their gain on fresh seeds (3E-T from −14.3 % to −4.4 %, round_2_result.md:394).
- The CMA-ES rule reads 4 of the actor's 16 inputs and uses the same action (b_env.py:1117-1129). No richer rule family was searched.

**H5. Honest testing removes fragile wins. Supported.**

- Confirmatory 3: X2 won at the minimum, "won" in about 27-30 % of seed resamples, then 1 of 5 on fresh seeds (V395, V396, V401).
- Round 2: X1's win excludes the cell's own CMA-ES rule; X2 closes with 3E-T counting 0.19 points inside the delay filter (round_2_result.md:7-9, :16).
- Against: the close-following edge over p333 survived every recount, filter and fresh-seed check.

### 1.2 Reasons missing from the brief's list

| # | Reason | Records |
|---|---|---|
| M1 | **The plant was tuned so that no control is as good as possible, and its capacity drop is not settled.** The author's intent was "a reasonably minimal capacity drop" and accepted that this "leaves less room for any controller". The drop itself is unknown: the estimator has no null, and its one reading after tuning was higher, not lower (11.7 % and 10.8 % against 1.7 % and 4.2 %, on r1m3 variants). Disturbances other than an imposed slowdown form no wave. | V314, V315, V327, V342; plant_vv_record_v0.md PR-26 (gap) |
| M2 | **The action is one-sided and gated.** 0.8 s is the floor of the action set and the best rule in steady and TRUCK conditions. The action binds only behind an ALKS leader. There, against p333, a policy can only lengthen headways. In X1 and X2 the stored rules that lengthen also have more delay than p333; only v3w has less. | b_env.py:37, :774-779 (inference) |
| M3 | **The reward does not carry the headline metric to the vehicle.** Delay enters as a shared count and as local speed; others' delay is priced about 200 times below the bar's rate per vehicle; about half of the decisions are gate-closed and enter the loss unmasked; the reward is flat after about update 100. | V413, V385, V364; b_env.py:554, :842 |
| M4 | **The bar is conjunctive.** A win needs delay and close-following against every opponent, for 4 of 5 single learners. With H1 true, NULL is the expected outcome. Also, the pooled arm (per-seed mean of 5 runs) is compared with single runs on a right-skewed measure: the pooled delay point against os0_10_10 is −0.58 % while the five per-learner points average +0.04 % (exploratory). **This pooled-arm point is for the design of future protocols only. It is no basis to re-read S6, which was read once.** | planb.md:438, :519, :531 |
| M5 | **Information favours the rules.** Rules are tuned per cell with the condition known; they answer every 5 s, the policy every 10 s; LocalRule reads 400-1,000 m ahead; v3w was not retrained for TRUCK. | V381(2), V478; planb.md:197, :215 |
| M6 | **The measure where DRL leads is weakly validated.** Against p333, 77-86 % of the reduction is on road 4a (merge 2) and about 40 % is below 5 m/s (exploratory). Merge-2 lane-end behaviour was never validated. The count is read at 1 Hz. Against the best rule (3E-C) the picture differs: the margin is not shown below 5 m/s and is shown at 10 m/s or more (+24.0 % [+16.0, +30.2], exploratory). | V396, V398; PR-28; `phase_b_round1/an_s6_independent_measures.md` §3 |
| M7 | **The learner variants are not clean negatives.** `res` had a confounded action range, `lagr` a mis-set target (about 6 % below the rules' delay, not 3 %), `attr` an untuned weight; five of seven round-2 candidates stopped at validation on 40 seeds, where a 1-2 % delay gain is not detectable (paired SD 7-11 %). | round_1_result.md:65, :243, :273-275; round_2_result.md:133; V435 |
| M8 | **Training-recipe variance exceeds method effects.** Learner SD 0.3-4.1 %; checkpoint rank at update 100-250 is opposite to update 500. | round_1_result.md:250-251; V429 |

### 1.3 Measures outside the reward, from stored rows

TRUCK cell, 240 paired seeds. "Record" values are from the report supplement read6 v2.3 (`docs/research/baseline_v5/readings/read6_v23_supplement.json`, report-only, 95 %). The others are exploratory, from the S6 rows (`phase_b_round1/an_s6_independent_measures.md`).

**In or tied to the reward** (TTC below 3 s and braking at 3 m/s² or harder are reward terms; stricter thresholds are nested in them):

| Measure | v3w against p333 | against os0_10_10 | against 3E-C_TRUCK | against no control |
|---|---|---|---|---|
| Close-following, TTC below 3 s (record) | +26.94 [+19.89, +33.24] | +22.57 [+17.70, +27.20] | +11.80 [+6.23, +18.95] | +29.06 [+26.35, +33.31] |
| TTC below 1.5 s (record) | +51.85 [+43.11, +60.30] | +50.52 [+41.38, +55.00] | +37.47 [+27.37, +46.74] | +43.19 [+36.17, +46.81] |
| Braking events peaking at 4.5 m/s² or harder (record) | +9.93 [+4.54, +15.82] | +2.92 [−0.47, +5.84] | **−5.73 [−8.28, −2.31]** | +15.42 [+11.19, +19.09] |
| Seconds of braking at 4.5 m/s² or harder (record) | +13.26 [+7.26, +18.14] | +5.70 [+1.61, +8.55] | −1.55 [−4.44, +2.37] | +13.92 [+10.98, +17.58] |

**Outside the reward:**

| Measure | v3w against p333 | against os0_10_10 | against 3E-C_TRUCK | against no control |
|---|---|---|---|---|
| Jam share (record) | +10.65 [+0.02, +17.61] | +7.75 [−1.39, +16.90] | −0.57 [−7.30, +11.32] | +62.91 [+57.65, +70.86] |
| Congested km, mean (record) | −1.43 [−3.04, −0.63] | −1.55 [−3.43, −0.34] | +1.17 [+0.05, +2.69] | +54.10 [+52.08, +56.67] |
| Congested km, maximum (record) | −3.91 [−6.52, −1.74] | −2.50 [−4.17, 0.00] | +3.85 [+1.54, +6.15] | +47.71 [+46.25, +49.58] |
| Number of jams (record) | +2.86 [−2.86, +8.57] | −2.86 [−5.71, +2.86] | −8.57 [−14.29, −4.29] | +28.00 [+26.00, +32.00] |
| Speed oscillation (record) | −0.15 [−0.36, +0.28] | +0.33 [+0.01, +0.67] | +1.02 [+0.55, +1.36] | +6.94 [+6.36, +7.63] |
| Fuel per km (exploratory) | +0.2 [+0.0, +0.3] | +0.1 [+0.0, +0.3] | +0.1 [−0.1, +0.2] | +0.6 [+0.4, +0.7] |
| Acceleration RMS of ALKS, 0.1 s (exploratory) | +2.1 [+1.6, +2.6] | +1.2 [+0.8, +1.6] | +0.0 [−0.4, +0.4] | −1.3 [−1.7, −0.8] |
| Jerk per step, 0.1 s (exploratory) | +0.7 [+0.5, +0.9] | +0.3 [+0.1, +0.4] | −0.5 [−0.6, −0.3] | −4.9 [−5.1, −4.7] |
| Lane-end stops at merge 2 (exploratory) | +31.1 [+21.4, +45.8] | +21.1 [+10.5, +31.7] | +3.0 [−11.9, +13.9] | +1.2 [−5.5, +15.4] |

Notes:
- The jam share's 98.75 % interval against p333 includes 0 (V501). The reading spec gives the congestion measures no "better" direction; the sign only says which arm is lower.
- Fuel per km in steady traffic (exploratory): −0.0 [−0.1, +0.1] against p333, −0.1 [−0.3, +0.1] against 3E-C_TRUCK, +1.1 [+1.0, +1.3] against no control. Fuel was never in the reward or in a registered reading.
- Reading: on stricter versions of the rewarded counts the edge is larger. On measures of another kind v3w is slightly better than p333, not shown different from 3E-C on most, and shown worse than 3E-C on hard-braking events, jerk and the number of jams. Outside the reward, the differences from the best searched rule are a few percent at most and go both ways.

### 1.4 What the stored rows add on delay (exploratory)

- **S6 was not underpowered.** Paired SD of the delay difference in TRUCK: 5.3 % of the median. A study of that size detects about 1 %.
- **Hindsight selection.** Picking the best of the 23 opponents per seed is 3.42 % [+2.70, +4.17] below the best single opponent, but picking the best of the five nominally equal v3w learners "gains" 2.09 %, and a scheduler fitted on half of the seeds gains +0.01 % [−0.91, +1.02] on the other half.
- **Where delay sits under p333 in steady traffic.** Upstream of the merges 30 %, merge 1 4 %, between the merges 14 %, merge 2 14 %, downstream 31 %; ramp insertion queues under 1 % (`phase_b_round1/an_delay_floor.md`). With single learners, in TRUCK, v3w is lower than p333 on road 4a (−4.38 % [−7.57, −1.29]) and higher on road 3 (+1.31 % [+0.73, +1.93]); the two cancel in the total (`phase_b_audit/metric_audit.md`).
- **Demand against capacity.** Under p333, 0.5 % of planned vehicles are unserved at 5,300 veh/h; demand is about 95-96 % of p333's saturated throughput. Merge 2 is metastable: road 4a is below 60 km/h for a median 7 of 25 minutes.
- **The ceiling at the merges.** The delay on roads 3a and 4a above the adjacent upstream road's rate, plus ramp insertion queues, is 9.2 % [8.4, 11.2] of p333's delay in steady traffic and 11.1 % in TRUCK, almost all at merge 2. The part tied to merge-2 slow minutes is about 15-18 % (a regression across seeds, not an intervention). These are upper bounds for a merge controller, at the location PR-28 leaves open.
- **The X1 delay edge.** Against p333, 60 % of it is on road 4a and 22 % off the mainline. It correlates with the difference in lane-end stops at merge 2 (Spearman 0.73). In the half of the seeds where p333 has few lane-end stops the edge is +0.5 %; in the other half +7.5 %. The queue never clears (V398), so the percentage depends on the window end.

### 1.5 What the literature adds (all [VERIFY])

- The freeway cases found where RL beat a tuned or shortest-headway baseline with the same actuator use spatially targeted lengthening of headways upstream of a merge, from section-level state: Veksler et al. 2024 (arXiv 2412.02520; "up to" 7 % average speed at 100 % CAV; its 1.5-s default is the floor and the action only lengthens) and Elmorshedy, Smirnov and Abdulhai 2023-2024 (delay "up to" 22-57 % against static headways; abstracts only).
- Vinitsky et al. 2020/2023 (ACM TCPS): CAVs that meter inflow beat a tuned feedback rule by about 15 % outflow at 5 % penetration, equal a traffic-light ALINEA at 40 %, with lane changing disabled.
- Hybrids beat their base controller by an amount that tracks how badly the base is tuned: 35 % from a deliberately mis-set MPC (Airaldi et al.), about 1.5 % derived over hand-tuned PI gains (Önür et al. 2025).
- No freeway study was found in which the conventional controller was re-tuned per condition.
- Cautions: Jayawardana et al. 2022 (NeurIPS): fixed-time and max-pressure beat four DRL methods once evaluation covers a family of scenarios. The I-24 field test reports energy trends, not delay.
- The local synthesis reached a similar view before this memo: "at a realistic drop, the mobility headroom at a bottleneck is small *for every controller*" (`rl_value_synthesis_v0.md`:49). That sentence rests on V149's "realistic 5-8 % drop", a premise the audit of V255(4) withdrew, so it is context and not evidence.

## 2. Cost basis

| Item | Rate | Source |
|---|---|---|
| Evaluation run with the measurement pack, 59 workers | 2,600-3,050 runs/h; $0.10-0.13 per 1,000 runs | V475 |
| S6-style evaluation, full pack with the space-time field, 90 workers | 1,690 runs/h at $0.607/h: about $0.36 per 1,000 runs (the rate) | V493, V494 |
| The same, whole cost of rental 2 | $7.35 for 13,920 runs: about $0.53 per 1,000. It includes a host outage hour and the steps before S6, so it is not a rate. | V494 |
| CMA-ES rule search | 40,640 rows in 7 h 42 min at $0.605/h: about 5,280 rows/h and $0.115 per 1,000 rows | V490 |
| One PPO training set (5 learners × 3 environments, 500 updates) | 500 × 23.5 s ≈ 3.3 h on an idle machine. On a rental, about $1.4 or less per set when sets share the machine: V450 records about $11 for eight sets, one search and an evaluation. Not measured per set. | V391-V392, V450 |
| Budget | $40 per 7 days. Plan B's $20 cap (about $17.50 used) belongs to Plan B; a screen is a new study and needs its own cap. | V488, planb.md:561 |

**Cells-tested count.** N = 91 (V487). A new (perturbation × demand level) cell in which a per-CAV DRL policy runs adds 1. Rules-only rows add 0. A re-test of a counted cell adds 0 (cells_tested.md:5). A cell proposed after results is a new study, labelled post hoc (planb.md:576).

## 3. Candidate directions

Each block gives the fields the brief asks for. "Verdict" is this memo's judgement. "Likely to fail" is a judgement; "KILL" is kept for criteria fixed before data.

### Route 1: improve the learner

**L1. Training repair package** (mask gate-closed decisions, tune the attributed-delay weight, correct the Lagrangian target, inputs for merge 2).
- Mechanism: v3w is under-trained on delay (M3) and half-blind at merge 2 (input 13 covers merge 1 only).
- Why a rule could not match; exposure: none stated. The learner still acts through the same lever (M2). Rules keep their per-cell tuning.
- For: `lagr`, `attr` and `res` were not clean negatives (M7); v3w's retraining gave about 3.4 % delay over baseline-v3 (round_1_result.md:105-106).
- Against: H1; 3E-D ended tied with p333; `1B` (mask and hold) showed nothing at validation.
- Literature: none found for learner-only gains against tuned baselines [VERIFY].
- Build and verification effect: code only; no plant change.
- Cost: 3 training sets ≈ $4 or less (§2); evaluation 3 recipes × 5 learners × 80 seeds × 2 cells = 2,400 runs × $0.36 per 1,000 ≈ $0.9. Author time about 1 h.
- Risks: forking paths (many knobs, each trained once). Cells added: 0 in existing cells.
- **Verdict: likely to fail on delay in steady and TRUCK conditions; untested with a correct delay objective (§4.2).** A component only of a study that a screen has opened.

**L2. Memory (recurrent actor or stacked observations).**
- Mechanism: infer hidden state: wave phase, event onset, demand trend.
- Why a rule could not match; exposure: a memoryless rule cannot; a rule with a timer or hysteresis can, and would be tuned on the same conditions.
- For: no test on record; the policy does shift by condition (V386).
- Against: look-ahead inputs gave no delay gain; the two-regime scheduler ASCH, which has memory, chose a single member in TRUCK (V491).
- Build: code only. Cost as L1. Cells added: 0 in existing cells. Risks: one more recipe.
- **Verdict: likely to fail alone.** See §6 for the library side.

**L3. Other algorithm classes.** See §6. **Verdict: likely to fail**: recipe variance exceeds method effects (M8), and H1 bounds every algorithm that uses the same lever.

**L4. Wider headway range with spatial targeting.** The learner side of screen M (§5.1).

### Route 2: change the plant or the actuators

**P1. Cooperative gap creation for a named ramp vehicle.**
- Mechanism: a lane-0 CAV opens a gap when a ramp vehicle approaches.
- Why a rule could not match; exposure: it can. A targeted-gap rule with the same inputs is the natural opponent.
- For: input 14 exists; Veksler et al. [VERIFY]; v3w's X1 edge is consistent with letting ramp-2 vehicles in (inference, §1.4).
- Against: ramp insertion queues are near zero at 5,300 (§1.4); "Expect a small mobility effect" (prior_art_B_v0.md:205); the lane-change gap rule takes back most of a longer headway (§4.3). The courtesy-gap failure (V194, V195: 10 teleports) was on another plant with one seed and does not carry over.
- Build and verification effect: `openGap` is forbidden by the CAV contract; `setTau` lengthening is inside it only up to 1.6 s. Cost: see M. Cells added: 0 for rules-only rows.
- **Verdict: folded into M.**

**P2. Lane assignment upstream of the merges.**
- Mechanism: CAVs leave lane 0 before a merge.
- Why a rule could not match: a fixed "keep left before the merge" rule probably captures most of it.
- Against: the lane action failed as built, 30 and 68 collisions in 10 runs, not traced (V317); lane changing is not validated (planb.md:183); the contract forbids `changeLane` (V309).
- Build and verification effect: a lane actuator, new tool checks T0-T3, and a lane-change validation that does not exist. Author time: days. Compute cost small beside the build. Cells added: 1 per cell with a DRL policy.
- **Verdict: high cost, high artefact risk; not tested on this plant.** No ceiling for it is on record (§5.1 item 3).

**P3. Per-CAV speed commands.**
- Against: policies declined the speed action (V339); the speed-cap oracle shows 0 of 8 (V344); all six MTFC arms "clearly worse" (V241); mainline metering KILL (V149).
- Caveat: V367 found hidden hard braking in the smooth cap, so V339 and V344 "need a look".
- Cost to re-open: an oracle re-run after the braking fix, about 8 cases × 20 seeds × 3 arms = 480 runs ≈ $0.1-0.2. Cells added: 0 (rules-only).
- **Verdict: likely to fail; the record that closes it is flawed.**

**P4. Coordination with ramp metering.**
- Against: r2m3 has a signal at one ramp only (corridor.py:72-73); ramp queues do not bind at 5,300 (§1.4). "ALINEA gains nothing" (V333) is from the earlier plant P0, with one setpoint that never acted; it does not carry over as a test.
- **Verdict: likely to fail; not tested on this plant.** Not costed.

**P5. A plant with a verified capacity drop.**
- Mechanism: a drop makes breakdown costly, so preventing it saves delay. This is where the literature's delay gains were found [VERIFY].
- Against: "closed for SUMO" (V256); the calibrated-plant study was rejected (V245).
- Build: a new plant and a full verification record. Weeks of author time.
- **Verdict: outside the writing-phase plan (V456).** PR-26 (the drop of the present plant, with a null) is a verification item the thesis needs in any case. A first reading from stored no-control rows is in §4.3; it cannot settle the question for the 0.8-s fleet.

### Route 3: disturb the plant

**D1. Demand that changes inside a run, with rules tuned on the same distribution.**
- Mechanism: the best headway pattern differs by demand level; a state-dependent policy follows the change.
- Equal exposure: one rule tuned on the whole distribution, a scheduler tuned on it, and a per-level lookup table that knows the level.
- For: exploratory, 10 used seeds: under a step, 36-42 % fewer close-following seconds than the two rules at the same or 4 % less delay (V410).
- Against: under a ramped peak, 69 % more (V410); SURGE was dropped at gate S2 (V487); "a tie is likely" (explore2/candidates.md:37); the author judged varying-demand training not worth it (V411). Whether the best rule changes with demand is not known: V429 compares two rules only.
- Build: none for the plant. Cost: rule grid 69 × 20 seeds × 3 levels = 4,140 runs ≈ $0.5; evaluation 80 seeds × 12 arms = 960 runs ≈ $0.35. Cells added: 1 per profile. A step like V410's is post hoc (V456).
- **Verdict: a candidate cell for a later frontier study, not a delay direction.**

**D2. Shift not seen in tuning (CAV share, driver mix).**
- Mechanism: regret against re-tuned rules.
- Against: p333 has no parameters and transfers perfectly, and it is the delay reference; a share or driver-mix change is a plant change (planb.md:312-320); below 50 % the gate (an ALKS leader) binds less often, so the lever shrinks for every controller (inference).
- Cells added: 1 per variant and level. Not costed: each variant needs a verification note first.
- **Verdict: weak.**

**D3. Incidents or work zones.**
- Against: a headway lever cannot remove a blocked lane; lane closure and WORKZONE were excluded from Plan B (planb.md:312-320); the incident code is on another plant.
- **Verdict: likely to fail; heavy build.**

**D4. String-unstable human drivers and wave damping; energy and comfort objectives.**
- Against: the plant absorbs disturbances (V342); making humans unstable by design is the straw-man the local synthesis warns of (rl_value_synthesis_v0.md:26-28); fuel per km is within ±0.2 % of every rule and jerk within 1 % (exploratory, §1.3).
- **Verdict: likely to fail.**

**D5. Slowdown recovery (the X1/X2 family).** See screen R, §5.3. Parked.

**D6. Sensing noise or V2V loss.**
- Mechanism: rules that read 400-1,000 m of roadside speeds depend on ideal sensing more than a local policy does.
- Against: "Not for: V2V with latency or loss" (plant_vv_record_v0.md:11); V2V outage was excluded from Plan B as not intended use; rules would be re-tuned under the noise.
- Build: a sensing model and a change of the intended use. Not costed.
- **Verdict: not ranked; needs a verification change first.** Listed because no record tests it.

### Route 4: hybrids

**H-1. A scheduler over a library of whole rules.**
- Against: ASCH's tuning chose a single member (V491); the zone-switched hybrid `sw` did not hold at test (round_2_result.md:177-178); the hindsight bound is mostly selection (§1.4, exploratory); MPC-F is −1.24 % [−1.95, −0.77] against p333 (record). A switch inside a run driven by a learner is untested.
- **Verdict: likely to fail.**

**H-2. Residual policy on the best rule, full action range.** With p333 as the base this is v3w's own problem. **Verdict: likely to fail.**

**H-3. A rule-based guard under the policy.**
- Mechanism: remove the policy's harmful modes in X1 (more close-following and hard braking than no control).
- Note: in X1 every short-headway controller is worse than no control on close-following (claim_review_round2.md:187).
- Build: code only; the guard's conditions are a new forking path. Cost: one evaluation, 80 seeds × 8 arms = 640 runs ≈ $0.25.
- **Verdict: a component, only if X1 stays in scope.**

**H-4. Policy distilled into a rule (decision tree on the actor's inputs).**
- Mechanism: the policy finds a control law that hand design and a 20-parameter search did not; a tree makes it testable as a rule.
- Against: if a tree matches v3w, the run-time controller is a rule and the sentence becomes "learning as a design method". r4a1, traced from the policies, did not hold on fresh seeds (V368). A flexible rule found by search on the actor's inputs is close to policy search itself.
- Cost: 5 trees × 80 seeds × 2 cells = 800 runs ≈ $0.3.
- **Verdict: report-only arm in a later study.**

**H-5. A policy conditioned on a preference weight** (one policy that covers the delay against close-following trade-off).
- Against: on the old plant the safety weight "moves C along the rules' trade-off and not beyond it" (V304).
- **Verdict: only after F passes.**

## 4. Evidence-quality audit, in both directions

The same scepticism the project applied to DRL wins is applied here to the records that say DRL cannot win on delay. Seven readers did this: a version timeline, the plant as a choice, the metric definitions, two classifiers and two skeptics (`phase_b_audit/`). Each possible bias is given a direction: toward the rules, toward DRL, every controller alike, or unknown. Numbers computed from stored rows are exploratory.

### 4.1 Plant, input and metric versions

Results that compare DRL with rules exist on three plants only.

| Plant | Rows | What differs | Inputs of the policies | Delay metric | Known defects at the time |
|---|---|---|---|---|---|
| m32 (the plant before V314's tuning) | V259-V317 | default lane-change setting; SUMO's own no-undertaking rule | hand-scaled; 30-s clock | none until V307, then finishers only | sawtooth braking about every 4 s (V324); stopped queues counted as short gaps (V283); the per-vehicle reward absent in training for C runs 1-4 (V294); no delay in any bar (V307) |
| P0, on r1m3 and r2m3 | V329-V368 | `lcAssertive` 1.4; the smooth no-undertaking rule | hand-scaled; one input dead, two saturated (V387) | finishers only | hidden 9 m/s² ALKS braking, missed at 1 Hz (V367); a jump from 0.8 to 1.6 s on V2V loss (V377); r2m3 positions built on r1m3's lengths (V365(4)); unequal clocks in V337 and V339 (policies 10 s, p333 30 s) |
| plant_c3, on r2m3 | V382-V502 | P0 plus `ease`, `tau_rise` 0.2, `taper_fast`, `fix_x` | normalised from confirmatory 3 revision 4 (V388-V390) | all vehicles, with unfinished vehicles and insertion queues | 1-Hz close-following; merge-2 lane ends not validated (PR-28); the queue never clears at 5,300 (V398); rules answer every 5 s, policies every 10 s; the pooled-arm statistic; capacity drop not settled (PR-26) |

P0c and P0d carried no-control checks and traces only. Every stored row of phases 1-3 and confirmatory 2 carries the P0 flags; every row from confirmatory 3 on carries all plant_c3 flags (checked on the row files).

**So every record before V382 ran on a plant or a metric that was later fixed, and every policy in it used hand-scaled inputs.** The fixes did not all push one way. `tau_rise` cost p333 about 10-13 % delay under slowdowns on 2 development seeds (V380), so slowdown records on P0 leaned toward p333. The unequal clocks leaned toward DRL by about 1.6-2.3 % (V351). The hand-scaled inputs handicapped the learner by an unmeasured amount.

### 4.2 Which conclusions carry over to plant_c3

| Conclusion | Rests on | Status | Cheapest re-check |
|---|---|---|---|
| In steady and TRUCK conditions at 5,300 veh/h, v3w ties the best rules on delay within about ±1 % | S6 (plant_c3, normalised, 240 seeds) | **Carries over, as a tie.** Its sign at merge 2 depends on PR-28: v3w is lower on road 4a (−4.38 % [−7.57, −1.29]) and higher on road 3 (+1.31 % [+0.73, +1.93]) | PR-28 check |
| "v3w has more delay than p333 in steady traffic" | S6 steady reference, arm level | **Does not carry as a loss.** The arm-level statistic reads +1.31 % toward the single-run rule with no true effect; with single learners p333 is ahead by 0.13 % [−0.74, +0.98], a tie. Both readings are exploratory; S6 is not re-read | none needed |
| "A fixed short headway is close to optimal" (the stronger half of H1) | 3E-D (one search, a family that reads 4 of 16 inputs); the stored lengthening rules; the oracles V344 and V347 | **Leans on records that need a re-check.** V344 (speed-cap oracle) used the cap that carried the hidden braking. V347 (headway oracle) ran on P0; its direction holds for rules on plant_c3 (in X1, 11 of 13 stored rules are shown worse than p333). No oracle or ceiling run exists on plant_c3 | headway oracle in steady traffic and one slowdown: about 400 rules-only runs, $0.04-0.14 |
| "No delay win" in the slowdown cells (V359, V395, V401) | 20-seed readings with a 5 % per-policy bar | **Not an absent edge for v3w.** The bar could not detect 5 % on 20 seeds. v3w is ahead of every stored rule in X1 on 120 seeds (§1.1). The edge is recipe-dependent: the earlier baseline-v3 policies on plant_c3 read −3.1 to −0.1 % against p333 in X1 | closed cells; see §5.3 |
| At 7,000 veh/h v3w is ahead of p333 | S1 map, 20 seeds, report-only: +3.7 % [+2.6, +5.2], 4 of 5 learners | Outside the intended use; only three rules ran there | not proposed |
| "Widening the lever has not helped" (H3) | V339 (speed action), V317 (lane action), `ahead` | **V339 and V317 need a re-check.** The speed action carried the hidden braking and ran with unequal clocks. The lane action was a broken actuator (lane rules collided too), never traced. Only `ahead` ran on plant_c3, and it stopped at validation, where 1-2 % is invisible | speed-cap oracle on plant_c3: about 480 rules-only runs, $0.05-0.17 |
| "Tuned rules absorb the delay headroom" (H4) | S6 for steady and TRUCK | Carries over there. **Untested for delay in X1 and X2**: no delay-objective search ran there. Every early support (V300, V304, V351, V361) is superseded | closed cells |
| Learner variants do not help (L1, L2) | rounds 1 and 2 | Direction only: no change moved delay by more than about 3 %. `lagr`, `attr` and `res` are not clean negatives. Retraining alone moved delay by 3.5 % [1.2, 5.3] (V449), which weakens "likely to fail" for L1 and makes any single recipe's edge a forking-path risk | a training; not proposed |
| Schedulers do not help (H-1) | ASCH, MPC-F, `sw` | `sw` carries over. ASCH's library and MPC-F's cost were built for close-following, so neither tested delay scheduling | rules only, under $1; not proposed |
| Closed: P1 gap creation, P2 lane action, P3 speed commands, P4 ramp metering | V194-V195 (other plant, one seed); V317; V339, V344, V241, V149; V333 | **None of the closing records carries over as a test.** Each ran on an earlier plant or a different actuator. For P3 only the mechanism carries ("caps only move the delay"), and it depends on PR-26. V333's ALINEA had one setpoint that never acted, on a plant whose hidden braking had eased merging | as above for P3; others need a build |

Never tested on plant_c3 with normalised inputs (none found): a speed action or speed-cap oracle; a headway oracle or any ceiling run; a lane action; a ramp meter; a policy trained with delay as its objective and a correct target; a policy retrained for TRUCK or with time-varying demand; a delay-objective rule search in steady traffic, X1 or X2; memory; headways outside 0.8-1.6 s; a scheduler with a delay objective; any controller on r1m3.

Where the bias ran for DRL, so that a tie is if anything stronger than recorded: cells chosen after DRL results (X1, X2, TRUCK); searches that did not converge or lost on fresh seeds (3E-T, 3E-X, 3E-C, 3E-D); rules tuned at 5,300 only in the sweeps; thin opponent sets off 5,300.

### 4.3 The plant as a choice

**V314 (tune the plant so that no control is as good as possible).**
- What was frozen: `lcAssertive` 1.4 for all vehicles and the smooth no-undertaking rule. Only no-control runs were scored.
- Before to after at 5,300 on r1m3: delay 146.4 to 126.9 s; ramp delay 229.8 to 79.9 s (V329); lane-end stops 1,969 to 86 (V327). After the hidden braking was removed: delay 127.5 s and lane-end stops 361 (V371).
- Effect on headroom: the tuning removed merge friction, the thing a state-feedback controller works on. That takes headroom from searched rules and from DRL alike; the author accepted this (V315).
- It was scored at the no-control headway of 1.6 s only. Under p333 merge 2 is not smooth: lane-end stops have a median of 391.5 in steady traffic and 2,518 in X1 against 728 for no control (exploratory). "No control is best" describes the 1.6-s fleet, not the plant the controllers run on.
- Does it favour the fixed rule over other controllers? Not shown. Fixed 0.8 s already led on m32 before the tuning (V285).

**V256 ("capacity drop closed for SUMO").**
- What it rested on: zipper models that gave 7 % or 50 % drops (V139); 54 and 216 work-zone configurations, none passing (V142-V145); a lane-end corridor passing only after a detector change made after data (V186-V187); a statistic that read 10.8-12.65 % with no drop at all (V244); and bn4L's stage 0, where "'No real drop' is supported only for lane-end Krauss" (V255).
- What it is: a decision to stop that line ("closed for SUMO by decision"), not a finding about SUMO, and not about realism. Every plant in it is a lane drop. No drop calibration at an on-ramp merge, the present bottleneck, was found in the records.
- Does it hold on plant_c3? For no control, no flow loss above about 1 % after breakdown is shown (exploratory, with a placebo). For the 0.8-s fleet the stored rows cannot tell: demand is about 96 % of the saturated throughput, so a discharge loss up to about 4 % would pass unseen. The measurement pack's own drop statistic reads about 3 % on runs with no breakdown. **PR-26 stays a gap; both "minimal" and "11.7 %" are unsupported.**
- What a verified drop would change: breakdown would cost flow as well as speed, so headroom above p333 would exist, first for searched state-feedback rules and for DRL through the same lever. The local synthesis found no case of RL beating tuned classical control at a bottleneck [VERIFY]. A plant built now would be post hoc; the drop would have to be fixed before any control result (V245).

**Plant gaps and the direction of their possible bias.** The verification record is a draft, "not yet reviewed or approved": 6 requirements met, 13 partial, 7 gaps, 2 limits (plant_vv_record_v0.md).

| Gap or choice | Mechanism | Direction |
|---|---|---|
| SUMO's lane-change gap rule (PR-08) | The rear gap a merging vehicle needs is the follower's speed × commanded headway, divided by `lcAssertive` (confirmed in the SUMO 1.27.1 source). So the rule takes back 71 % of every metre a longer ALKS headway adds. A real merging driver does not know the follower's setting. | Against every rule and policy that lengthens headways to let vehicles in; toward the fixed short headway. Size unknown. |
| Merge-2 lane ends (PR-28) | The X1 edge over p333 and the two halves of the TRUCK tie sit at this merge. A blocked SUMO merger waits; a driver who forces in would make a short-headway platoon brake. | Unknown. It could remove the X1 edge, or hide a cost of short headways. |
| Capacity drop (PR-26) | Without a flow loss, breakdown costs speed only. | Unknown for the present plant; with a drop, toward every state-feedback controller against the fixed rule. |
| ALKS as IDM with no actuation lag (PR-06) | 0.8 s carries no stability cost; switching headway is also free. | Mixed. |
| Ideal V2V and roadside inputs (PR-15, PR-16) | Rules read 400-1,000 m ahead; the policy's inputs are noise-free too. | Mixed. |
| Headway bind check on r2m3 (PR-10) | V382 holds a check ("commanded level reached 100 %") that the record does not cite; the held gap is not shown. | Every controller alike. |
| Lane changing not validated; instant lane changes (PR-08, PR-09) | Less friction than real traffic. | Every controller alike. |
| 1-Hz close-following (PR-23) | The policy is paid on the same sample phase that judges it. | Toward DRL on close-following; not measured. |
| Evaluation is greedy, training samples | A different policy is judged than the one trained. | Unknown. |

### 4.4 Metric definitions

- **The delay definition is sound.** The stored value is rebuilt from the per-road vehicle-seconds and distances within 6-16 veh-s per run. No vehicle is dropped: teleporting is off, and collisions do not remove vehicles.
- **No alternative definition reverses a sign** in steady traffic, TRUCK, X1 or X2: total travel time, in-network delay, per served vehicle, own-speed reference for finished vehicles, cars only, with or without lane-end stopped seconds.
- **The statistic matters more than the metric.** A five-run mean against a single run on a right-skewed measure reads +1.31 % (steady) and +0.46 % (TRUCK) toward the single run when nothing differs. That is the size of S6's blocking margins. It favours p333 and every single-run rule.
- **Window end.** No arm has less delay and a larger backlog, so truncation understates every difference. In X1 the edge over p333 grows with the window (0, about 4,000 and about 12,000 veh-s at 600, 1,200 and 1,800 s). In TRUCK, charging unfinished vehicles moves the tie by at most about 0.4 % toward v3w.
- **Equal offsets shrink every percentage.** The main insertion queue (3.5 % of p333's steady delay), trucks held to 100 km/h (2.9 %) and the reference speed (9.5 %) are the same in every arm. Delay is 22 % of total travel time. So a fixed-percent bar depends on the reference: v3w's X1 edge reads +9.8 %, +5.2 % and +3.9 % at references of 80, 100 and 120 km/h.
- **Lane-end stops** are counted like any stopped vehicle. The queue behind them is plant behaviour (PR-28), not a counting matter.

### 4.5 What the audit changes

1. "DRL cannot win on delay" is established for two cells only: steady and TRUCK conditions at 5,300 veh/h, as a tie within about ±1 %.
2. The stronger statement, that a fixed short headway is close to the best any controller can do, rests on one rule search, on static lengthening rules that a simulator rule handicaps, and on oracles from an earlier plant. No ceiling run exists on plant_c3.
3. The records that closed the speed, lane, metering and gap-creation actuators do not carry over as tests. They are "not tested on this plant", not "closed".
4. In X1, X2 and at 7,000 veh/h the late records point toward v3w on delay. What stops a claim there is a closing rule, a plant gap (PR-28), missing delay-tuned opponents and the intended use, not a finding.
5. The plant gaps cut both ways. One is shown to act against any controller that lengthens headways (the lane-change gap rule). One could act for or against the X1 edge (PR-28).
6. The arm-level statistic should not be used in a future protocol without its null.

## 5. Screens

Each screen went through three independent drafts, two judges, a synthesis, one skeptic and a revision. The full texts, with their null computations and scripts, are `phase_b_panel/M/final.md`, `phase_b_panel/F/final.md` and `phase_b_panel/R/final.md`. This section carries their protocol content. §8 lists the skeptics' findings and their handling.

Rules common to all screens:
- No DRL training. Frozen v3w in evaluation mode only.
- Nothing runs without the author's approval of the rental, the spend and the seeds. Each screen is a new study with its own cap; Plan B's cap does not carry over.
- Criteria are fixed before data. Paired seeds; the median of paired differences over the opponent's median; percentile bootstrap.
- A pass allows a protocol to be written. It is never a claim, and a screen's own rows are not evidence for a later claim.
- Numbers from stored rows in a screen text are exploratory planning values.
- Seeds are proposals. The ledger shows no use from 7,485,000 up.

### 5.1 Screen M: headways above 1.6 s at merge 2

**1. Question.** In steady traffic at 5,300 veh/h on r2m3, does a 2.0-4.0 s headway on lane-0 automated cars at merge 2 cut delay by at least 5 % against p333, and beat every opponent that stays inside 0.8-1.6 s?
- A pass allows, in order: a PR-28 check with its own criterion; a rules-only search of the rule family; then a DRL protocol with its bar set against the searched rule. The passing controller is a rule. A learner would need actions above 1.6 s and retraining; what it could add is unknown.
- A KILL closes this always-on lane-0 zone family as a 5 % delay lever at merge 2 at 5,300 veh/h. A triggered form (P1) and lane actuators (P2) stay open.

**2. Approvals and preconditions.**
- A new post hoc study (planb.md:576) with a cap of $3, one rental, the seeds below.
- Headways above 1.6 s for this screen only: a departure from the CAV contract, as V273.
- V355's KILL of fixed zone patterns set aside for these arms.
- Checks in order: identity and smoke (a failure stops the screen until fixed); tool check T0 (a failed arm is VOID); a trace of the lane-end stop counter (PR-24).
- PR-28 stays open and every result sentence carries it. The capacity-drop estimator with its no-drop null (PR-26) is report-only.

**3. Stage 0: stored rows, zero runs (exploratory).**

| Statement | Value | What it decides |
|---|---|---|
| Delay on roads 3a and 4a above the upstream road's rate, plus ramp insertion queues, under p333 | 9.20 % [8.35, 11.38] of delay (97.5 %); 7.13 % at merge 2 | nothing alone: it is a descriptive split, not a bound. It reads 5.72 % in the 22 seeds with no slow minute |
| Delay tied to minutes with road 4a below 60 km/h | 14.6 % of mean delay (TRUCK 18 %); an association across seeds | the delay sits at merge 2 |
| Stored rules with 1.0-1.2 s near a merge (4 rules) | −2.1 % [−3.8, −0.6] to −7.5 % [−10.0, −4.3] against p333 (97.5 %) | nothing inside 0.8-1.6 s needs a re-run; above 1.6 s there is no record |

**No simulated no-merge reference is run** (the author's correction 2). No tested ceiling is on record. The three candidates, with what each loads and changes:
- *Ramp vehicles entering at the main origin* (the v0 draft): edges 1-2 carry 5,300 instead of 3,710 veh/h and the insertion point 1,767 instead of 1,237 veh/h per lane; each rerouted vehicle drives 3.08 or 4.57 km more, about +15 % delay by the definition alone. It is a plant change and would KILL for a reason unrelated to merges.
- *No-ramp arm* (ramp vehicles dropped, main-route delay compared): it removes 1,590 veh/h below the merges. A valid ceiling, but it reads the speed-flow curve: near 55 % by the stored 3,500-veh/h rows (inference). No 5 % rule on it can fire.
- *Flow-matched ideal merge* (ramp vehicles inserted on the mainline at speed): SUMO's insertion check replaces the lane-change model; unvalidated.

**4. Arms.** Cells: steady traffic at 5,300 veh/h (deciding) and 6,000 veh/h (report-only). X1 is not used.

| Arm | Definition |
|---|---|
| Z20, Z30, Z40 | A new lane-indexed rule class. Headway T = 2.0, 3.0 or 4.0 s on lane `3_0` in its last 600 m and on `4a_1`, the lane beside the accelerating lane; 0.8 s elsewhere, so the arm equals p333 outside its zone. Hold 10 s |
| U30 | Z30 without `4a_1` |
| Z16 | The same zone at 1.6 s: the in-range anchor, and an opponent |
| In range | p333 and os0_10_10 (no stored rule of 22 has less delay than p333 by point); at 6,000 also os1_15_10. No control is shown beside, never deciding |

Equal exposure: one long-headway arm is picked on 60 selection seeds at 5,300 (lowest median paired delay against p333 among arms that passed T0, collisions at most p333's + 1), frozen before the verdict. The in-range rules had 240 stored seeds.

**5. Measures.** Deciding: `all_delay`. Pass conditions: flow (`passed`), collisions, moving full-emergency events, stuck vehicles. Report-only: the merge split, slow minutes on 4a, total travel time, delay on 4a and ramp 2; close-following and braking at 3 m/s² (reward terms of v3w); braking at 0.1 s, lane-end stops, fuel per km, jam share (outside the reward).

**6. Seeds proposed.**

| Seeds | One purpose |
|---|---|
| 7,480,000-002 (stored rows) | identity replay; equality only |
| 7,485,000-009 | tool checks: T0, determinism, traced against untraced |
| 7,485,010-019 | lane-end counter trace |
| 7,485,020-099 | reserved for smoke repeats after a code fix |
| 7,485,100-159 | selection at 5,300 |
| 7,485,200-439 | verdict at 5,300, n = 240, used once |
| 7,485,440-499 | report rows at 6,000, n = 60 |

**7. KILL rules.** Intervals are two-sided 97.5 % (Plan B's level, kept although one cell decides).
- T0: a long-headway arm that fails T0 is VOID: the command did not bind in this zone, and nothing about delay is closed. With no arm left at 5,300 the screen is VOID.
- At 5,300, the picked arm against p333, os0_10_10 and Z16:
  - PASS: point at least 5 % against p333; against each opponent, lower bound above 0, flow at most 0.5 % lower by point, mean excess at most 0.02 collisions and 0.10 moving full-emergency events per run (one-sided 95 % upper bound), stuck rows at most p333's + 2.
  - BOUNDED: upper bound against p333 below 5 %.
  - Otherwise NOT SHOWN.
- The screen is KILLed if BOUNDED. The sentence: "at merge 2, where lane-end behaviour is not validated (PR-28), the picked arm is bounded below 5 % against p333; the other long arms that passed T0 lost a 60-seed selection". NOT SHOWN and VOID close nothing and allow no protocol.
- 6,000 veh/h is report-only.
- Where the numbers come from: 5 % is V354's "coordination matters" rule on r2m3 (5 % against uniform 0.8 s, CI excluding 0, flow at most 0.5 % worse) and the delay tile of V462(1); it is about half of the 9.2 % split. The v0 draft's 3 % is dropped with the reference it belonged to; as a size it came from X1 and X2 noise. The 600-m zone, "the last 100 m", 0.8 × T and "p333's + 2" are design values with no record.

**8. Null and power** (exploratory planning from four stored merge rules, n = 240, 1,000 studies per row).

| True effect against p333 | PASS | BOUNDED |
|---|---|---|
| 0 | 0.0 % | 99.7-100 % |
| 3 % | 0.0-3.7 % | 23-90 % |
| 5 % | 44-52 % | 1.4-1.8 % |
| 6 % | 81-95 % | 0.0-0.2 % |
| 7 % | 94-100 % | 0.0 % |

With the 60-seed pick before it, PASS is 39-46 % at a true 5 % and 72-95 % at 6 %. A sign-flip null gives a lower bound above 0 in 1.2-1.7 % of studies (nominal 1.25 %).

**9. Runs × rate = cost.**

| Stage | Runs |
|---|---|
| 1: identity 15, determinism and traced twins 4, lane-end trace 8, T0 160 (8 arms × 10 seeds × 2 cells) | 187 |
| 2: selection at 5,300, 60 seeds × 5 arms | 300 |
| 3: verdict at 5,300, 240 seeds × 5 arms | 1,200 |
| 4: report at 6,000, 60 seeds × 9 arms | 540 |
| Total | 2,227 |

At $0.36 per 1,000 runs, with the 6,000 runs about 1.46 times slower (inference): about 1.5 h of runs, 1.8-2.2 machine-hours, $1.1-1.3. A stop at T0 costs 187 runs, about $0.2. Build: 16-22 h (a lane-indexed rule class, a headway path above 1.6 s, T0's meters, tests). Author time, apart: about 1.5 h.

**10. Plant and verification effect.**
- Identity: four stored arms on 7,480,000-002 equal their stored rows by value; the new class with an empty zone equals stored p333 except on the keys whose length follows the level table.
- Smoke: the run configuration carries T and the zone; seconds at T appear inside the zone only; traced equals untraced.
- T0 (PR-10 has no r2m3 record): the zone at 1.0, 1.2, 1.6, 2.0, 3.0 and 4.0 s, U30 and p333; 10 seeds; both cells. Pass: commanded and read-back headway agree; the median time gap of gated lane-0 automated cars in the last 100 m of `3_0` is above p333's in 10 of 10 seeds and at least 0.8 × T. Reported: lane-0 flow, the share of time the gate is off, ramp entries ahead of a commanded car, braking at 0.1 s.
- Label on every row at 2.0-4.0 s: "outside the plant's stated intended use: headway above the checked range 0.8-1.6 s; merge-conflict and lane-change dynamics not validated (PR-08, PR-28)".

**11. Cells added:** 0 (rules only). Post hoc: the cells, the zone, the values and the thresholds follow the S6 results.

**12. Must-carry disclosures.**
- Exploratory and post hoc; a pass is headroom for a rule.
- The target binds only behind an automated leader within 150 m (56 % of ALKS-seconds under p333), rises 0.2 s per second and moves one level per 10-s hold. At the stored 73.9 km/h the 4.0-s command is reached 328-431 m into the zone; a 3-4 s target meters lane 0 (inference).
- SUMO blocks a merge when the rear gap is below the follower's speed × headway / `lcAssertive`: 79.4 m at 4.0 s and 100 km/h. Results hold for this lane-change model only.
- 6,000 veh/h is above p333's capacity estimate; no rule was tuned there.
- PR-28 open; capacity drop not settled (PR-26). No literature support is claimed.

**13. Expected outcome** (a judgement): KILL. PASS 3 %; VOID at T0 5 %; BOUNDED 82 %; NOT SHOWN 10 %.

**Open for the author on M:** whether to buy the no-ramp arm (about 240 more runs; a loose ceiling); 6,000 veh/h as report-only, dropped, or deciding; the PASS form (5 % against p333 only, or against each opponent, which passes a true 5 % only 10-38 % of the time); whether PR-28 must be checked before the screen; the four design values; the level; the approvals of item 2.

### 5.2 Screen F: the frontier claim in TRUCK

**1. Question.** In TRUCK at 5,300 veh/h, does frozen v3w keep a close-following point edge of 10 % or more, with the lower bound above 0, over the searched rule as picked today, re-picked on fresh seeds (stage 1) and searched on to 300 generations (stage 2), while its delay is shown less than 1 % worse than every rule arm's?
- A pass allows a protocol for one TRUCK-only trade-off sentence, to be tested on fresh seeds.
- A KILL closes F for v3w on this plant: no second seed round and no retraining.

**2. Approvals and preconditions.** Each is an author decision before any rental.
1. **Reopen TRUCK.** planb.md:575 closed it after S6 in the words of [A3]: "no further training, tuning, plant change or seed round there". F tunes a rule and runs a seed round there. This memo does not assume that override.
2. **The claim form.** planb.md:153 says "No sentence claims a win on one measure alone". F's sentence would be a trade-off: close-following better, delay not worse by 1 %. If the author refuses that form, F closes at no cost.
3. **The statistic.** Default: the mean of the five learners' effects, each learner's run against the rule's run, seeds resampled jointly. It sets aside Plan B's pooled arm, which is printed beside. Reason: the pooled arm fails a no-effect null (§4.4).
4. The KILL forms, the rule arms, the harness change and the seeds below.
5. A rental with caps of $4 (stage 1) and $12 (stage 2). The ledger already holds about $18.6 of rentals for 2026-11-08 to 11-10.

Before any verdict row, on the rented host: stored rows reproduce by value (each stored arm on 3 seeds, and the search's reference rows: p333 on 7,480,150-229 and today's pick on its 16 search seeds); a repeated run is equal; planted-row tests; a code review; and T0 for PR-10's missing r2m3 record (uniform 1.6, 1.2, 1.0 and 0.8 s on 2 seeds).

**3. Stage 0: stored rows, zero runs (exploratory).**
- TRUCK passes the rules of item 7 today: edge over 3E-C +12.68 % [+6.32, +18.35] in the default statistic (pooled, recorded: +11.80 % [+4.97, +19.71]); lowest delay bound −0.59 % (pooled −0.93 %). These rows chose the hypothesis and are not evidence.
- Steady traffic fails the delay rule against 5 rules (pooled: 13). No rule was searched there. So the scope is TRUCK only.
- Outside the reward nothing adds a sentence (item 5).

**4. Arms.**
- **v3w:** 5 frozen learners, never tuned in TRUCK.
- **3E-C:** today's pick, the lowest of 47 admissible check losses.
- **3E-C-R (stage 1, no search):** the 9 lowest admissible stored check losses, run with p333 on selection set A; the lowest loss admitted wins. It removes the luck of a minimum over noisy 40-seed checks.
- **3E-C+ (stage 2; the author's correction 1): the search continued, not restarted.** Generations 0-99 replay from the stored evaluations and must reproduce today's pick. Generations 100-299 run under the Plan B recipe unchanged: the original search pool 7,480,150-189, the original check set 7,480,190-229, the same CMA seed and loss. It is a harness change, because the search code refuses a changed generation count. Fixed budget, no result-dependent stop; the plateau label is reported only. Selection set B then runs p333, the 8 lowest admissible check losses of generations 20-300, today's pick, 3E-C-R and the final CMA mean; the lowest loss admitted wins and is committed before its verdict rows. Plan B's own incumbent at generation 300 is a verdict arm too.
- **Stored rule arms:** the 9 with an S6 delay lower bound at or below 0: os0_10_10, p333, lr1000_10_1, grid_os1_10_10, os1_15_10, 3E-D_TRUCK, lr1000_16_2, grid_lr400_13_1, lr400_13_2. No control beside, never deciding.
- **Not run:** the other 13 stored rules (recorded lower bounds at least +0.56 % on delay and +17.61 % on close-following); other delay hinges, decision trees, richer rule families (no form or budget on record).
- **Exposure:** the rule gets 300 generations in the cell and answers every 5 s; v3w gets none and answers every 10 s. This is conservative on tuning. A KILL is not rescued by retraining.

**5. Measures.**
- Deciding: close-following (TTC below 3 s at 1 Hz, a reward term) and delay (`all_delay`).
- Side conditions: flow, collisions, moving full-emergency events, robust braking.
- Report-only, tied to the reward: TTC below 2 s and 1.5 s; braking events at 4.5 m/s² or harder, where v3w is shown worse than 3E-C: −5.73 % [−8.28, −2.31] (record).
- Report-only, outside the reward (the author's correction 5): the jam metrics and fuel per km of §1.3, jerk, speed oscillation, acceleration RMS. Stored costs to print: congested km against p333 (mean −1.43 % [−3.04, −0.63], maximum −3.91 % [−6.52, −1.74]), os0_10_10 and 3E-D_TRUCK; jam count and jerk against 3E-C.
- Validity read-outs for PR-28: drain; lane-change share; the edge off roads 4a, 4 and ramp 2.
- A sentence names close-following only, as a reward term, and leads with every measure shown worse. The 0.1-s meter never ran and is not read.

**6. Seeds proposed.**

| Seeds | One purpose |
|---|---|
| 7,480,150-189 | search pool, as in Plan B (correction 1) |
| 7,480,190-229 | in-search checks: shortlist and plateau label, as in Plan B |
| 7,487,000-009 | smoke, T0 |
| 7,487,010-129 | selection set A |
| 7,487,130-249 | selection set B |
| 7,487,300-779 | verdict, 480 seeds; each arm run once, read at both stages |

**7. KILL rules.** Two-sided 97.5 %, the level at which TRUCK was read. A pass is one intersection over rule arms and both stages, read in a fixed order. Stage 2 runs only after a stage 1 pass. KILL if, against any rule arm:
- **K1, edge:** the close-following point is below 10 %, or the lower bound is at or below 0. The 10 % is round 2's per-policy size; it was written after the stored 11.80 % was seen.
- **K2, delay non-inferiority (the author's correction 3; the form of V435 and of round 2's decision D11):** the lower bound of the delay effect at 97.5 % is at or below −1 %. The 1 % margin is the search's own penalty-free slack. Round 2's 5 % margin is not used: it exceeds every delay difference among the nine tied rules.
- **K3, learners:** fewer than 4 of 5 have, against every rule arm, a close-following point above 0 and a delay point above −1 %.
- **K4, side conditions:** flow more than 0.5 % worse by point; mean excess above 0.02 collisions or 0.10 moving full-emergency events per run; robust-braking excess above 10 %.
- Before a pass, K1's label-swap null must be within 1.5 times nominal. A pass with the plateau label unmet reads "pass at the fixed budget".

**8. Null and power** (exploratory: 480 seeds resampled from the 240 stored, v3w shifted to the stated truth).

| True single-learner edge | 0 % | 8 % | 10 % | 12 % | 15 % |
|---|---|---|---|---|---|
| P(KILL by K1) | 1.000 | 0.853 | 0.503 | 0.156 | 0.003 |
| P(pass K1 to K3) | 0.000 | 0.147 | 0.497 | 0.844 | 0.997 |

The screen separates 5 % from 15 %, not 10 % from 12 %. K2 passes 0.987 if every learner ties every arm, 0.165 at 0.5 % worse and 0.000 at 1 % worse, so it bounds a 1 % deficit. With Plan B's pooled arm instead, K1 KILLs a true 12 % edge 0.379 of the time and K2 passes a true tie only 0.359 of the time.

**9. Runs × rate = cost.**

| Stage | Runs or rows | Hours | Cost |
|---|---|---|---|
| 1: smoke, T0 and selection A (1,400); verdict 17 runs × 480 seeds (8,160) | 9,560 | 5.1 | $3.10 |
| 2: continuation 200 generations × 384 rows + 20 checks × 240 + 96 reference rows; selection B and smoke (1,720); verdict up to 2 arms × 480 | 84,376 | 16.4 | $9.94 |

Rates: verdict runs with the full pack at 1,690 per hour, $0.36 per 1,000; search and selection rows at 5,280 per hour, $0.115 per 1,000. With 6 % setup: stage 1 about $3.3 and 5.4 machine-hours, where a KILL ends the screen; both stages about $13.8 and 23 h. If a rate check projects stage 2 above its cap, the continuation stops and the outcome is "stage 2 not run": no pass, no KILL. Build: 12-16 h (my estimate). Author time, apart: about 2 h.

**10. Plant and verification effect.** No plant file, reward, input, period or actuator value changes. Headways stay at the four checked values. TRUCK is outside the plant's stated intended use; PR-08 and PR-28 are carried; PR-26 is a gap.

**11. Cells added:** 0 (TRUCK is counted). The whole screen is post hoc: its statistic, sizes, seed count, rule arms and measure classes followed the stored rows.

**12. Must-carry disclosures.**
- TRUCK only, outside the intended use, not shown in steady traffic; TRUCK passed gate S2 only under V486's replacement; the cell was chosen after related DRL results.
- Close-following is a reward term read at 1 Hz; 78 % of v3w's counted seconds lie on roads 4a, 4 and ramp 2 (exploratory).
- Stored costs: braking events, jam count and jerk against 3E-C; congested km against p333, os0_10_10 and 3E-D_TRUCK. Delay is non-inferior at 1 %, not equal.
- The statistic's form followed the stored rows.
- v3w not retrained; rules tuned in the cell; one rule family, one hinge, 300 generations; 13 rules not re-run; verdict seeds read at both stages.

**13. Expected outcome** (a judgement): stage 1 pass about 50 %; stage 2 given stage 1 about 30 %; **overall pass about 15 %** (about 10 % with the pooled arm). Expected spend about $8.5.

**Open for the author on F:** the two decisions that can close it at no cost (items 2.1 and 2.2); the statistic; K1's form (the alternative, Plan B's own form, passes a true 5 % edge 0.575 of the time); K2's margin (1 % or 2 %); the rule arms (11 by default); the reading of correction 1 (if "fresh seeds for the check only" means the verdict alone, the two selection sets drop and Plan B's incumbent is the pick); what a budget stop means; the caps and the 7-day sum.

### 5.3 Screen R: slowdown recovery. Parked

**Status (author, 2026-11-10).** Parked. Confirmatory 3's rule [A3] (confirmatory_3.md:132; V395), V466 and planb.md:160 stay closed. Nothing runs in X1 or X2: no v3w row, no rule tuning, no seed round.

**What the stored rows hold (exploratory; they support no claim).**
- X1: v3w +4.2 % [+2.4, +5.9] (97.5 %) on delay against p333, the nearest stored rule, on 120 seeds in three sets, 5 of 5 learners. The edge belongs to the v3w recipe (§4.2).
- X2: about +1.9 % [+0.1, +4.3] against os0_10_10.
- Location: against p333 and lr1000_10_1, 58-62 % of the edge sits on road 4a; against os0_10_10, 4 %. On stored rows a pass of the panel's design would carry the label "PR-28-bound" in 99-100 % of resamples.
- Against no control in X1, v3w has 16.6 % [8.4, 25.1] more close-following.
- Under the training slowdown family at nearby demand no edge is shown: +1.3 % [−8.9, +7.5] at 5,250 and −1.4 % [−6.6, +2.8] at 5,500 veh/h (s01_result.md, 20 seeds). X1's two events never occur in training.

**Precondition for asking the question again: a new pre-registered slowdown cell.** It is a new study. It needs all of the following before any run:
1. A cell that is not X1 or X2, with its perturbation and demand level written and approved before any control result on it exists (V456(3)). It is labelled post hoc, because X1's stored rows motivate it (planb.md:576), and it adds 1 to the cells-tested count (N = 92).
2. The PR-28 item first: a rules-only check of lane-end behaviour at merge 2 with its own criterion. Without it a pass would again be bound to the unvalidated merge. A slowdown that is not directly below merge 2 would also separate recovery from lane-end behaviour.
3. Opponents tuned for delay in the new cell, with equal exposure: the carried rules, grid picks that include look-ahead rules, a merge-2 hybrid, a rule that reads the distance to the nearest accelerating-lane vehicle (the one input v3w has and the searched family lacks), a delay-objective CMA-ES search, and a scheduler with a delay library.
4. A bar with a record. The recorded delay win is 5 % for 4 of 5 policies (confirmatory_3.md:108). A 3 % arm-level bar has no record, and the stored X1 rows pass it in 93-98 % of resamples, so it would be chosen after the number it tests.
5. Verdict seeds sized for a minimum over many tied arms: with 240 seeds, 5 to 12 tied arms pass in 80 % of studies only from a true edge of about 4.0-4.2 %.
6. v3w frozen; or, if a recipe is retrained for the cell, every opponent re-tuned in it and the count of recipes read stated.
7. An informed oracle before anything else, by the project's early-KILL rule: a rule that is told the place and time of the slowdown, against the best rule that is not. Rules only. If the oracle shows no delay gain, the cell is KILLed for a few hundred runs.

**What the panel's design would cost on one cell** (for planning only): stage 1 about 6,450 runs, $0.6-2.3; with the search and the scheduler about 52,850 runs and rows, 12.5-16 machine-hours, $6.3-9.7; build 16-20 h. Its judged chance of a pass that allows a DRL protocol on X1 was under 2 %, because a pass was expected to be bound to PR-28. For a new cell that chance is unknown.

The panel's full protocol text stays in `phase_b_panel/R/final.md` as a template. It is not a proposal to run.

## 6. Stable-Baselines3 families: desk comparison

Nothing was installed, built, trained or simulated. Library facts are from the installed 2.8.0 source (`stable_baselines3`, `sb3_contrib`), checked line by line by a second reader; the 2.8 documentation tables agree with the source for all ten families. Build routes are read from code, not executed. Full table with file:line sources: `phase_b_sb3/sb3_table.md`; verifiers: `phase_b_sb3/skeptic_lib.md`, `skeptic_fit.md`.

**Common to every family.**
- One training set is 5 learners × (500 updates × 3 environments + 3 pilot episodes) = 7,515 simulated episodes, with about 31,000 car-decisions per episode (stored event files of v3w).
- Wall time per set: about 3.3 h on an idle laptop (V391-V392); 4.1 h in v3w's stored event files; 11.3 h for round 2's 1B when 40 learners shared a rented machine. V450 puts eight sets, one search and an evaluation at about $11, so a set costs about $1.4 or less when sets share a machine (not measured per set).
- SB3 is single-agent and holds no multi-agent code. The project's trainer decision (ADR-001) rejects fixed car slots, and a slot adapter also fails mechanically: per-car 10-s clocks against one global step, no validity field in the rollout buffer, losses that are plain means over all rows. So the only sound route is our own collection loop with SB3 as an algorithm library. For PPO that rebuilds what `c_train.py` already holds.
- In every family the actor and the critic read the same observation. The centralised critic (10 extra global inputs) needs a custom policy class.
- No family changes the action's floor. 0.8 s stays the lowest headway and the best delay rule in steady and TRUCK conditions (M2), so H1 bounds every family that uses the same lever.

| Family | Action spaces in 2.8.0; design here | Per-CAV shared policy with a varying car count | Sample use against simulator cost | Hypothesis; what bounds it | Record |
|---|---|---|---|---|---|
| A2C | Box, Discrete, MultiDiscrete, MultiBinary. The 4 levels as Discrete(4). No masks. | Own loop, flat per-car buffer, custom critic. | 7,515 episodes per set. One gradient step per batch against about 220 minibatch steps now: more episodes for the same learning (estimate). | None. Same lever. | Nothing. |
| PPO | All four. Discrete(4) as now. | Own loop; this is `c_train.py` with SB3's `train()`. | The present budget. Each batch of about 93,000 decisions is used for 10 epochs, then dropped. | None new. The reference arm for any follow-up. | v3w and every variant of rounds 1 and 2 (10 trained recipes, 2 evaluation-only). SB3's own PPO ran the early central coordinator (V263, V265). |
| DDPG | Box only. Forces a continuous headway sent by `setTau`. Any value other than 1.6, 1.2, 1.0 and 0.8 s is outside the plant's record, so each needs tool check T0. | Own loop; replay of per-car transitions (state at a decision, action, mean 10-s reward, state at the car's next decision; nothing is terminal). Needs an action-noise object. | Transitions are not scarce (31,000 per run); runs are. How many gradient steps per sample to take is a free choice with no record here. A saving needs far fewer than 1,503 episodes per learner: unknown. | None. A continuous action is a new action design, not a repair. Above 1.6 s, screen M bounds it; inside 0.8-1.6 s, H1 does. | Nothing. |
| TD3 | Box only. As DDPG. | As DDPG, with twin critics and delayed updates. | As DDPG. | As DDPG. | Nothing. |
| SAC | Box only. Neither package holds a discrete SAC. | As DDPG; stochastic actor, no noise object. | As DDPG. | As DDPG. | Nothing. Named in the earlier fair-vanilla rule (below). |
| MaskablePPO | Discrete, MultiDiscrete, MultiBinary; no Box. Discrete(4) plus one mask per decision; gate closed means one allowed level. | Own loop; the buffer stores one mask per sample. | As PPO. About 44 % of rows would carry no policy gradient (1B's logged share). | M3, the gating half only. | Round 2's 1B masked gate-closed rows in our trainer, with a gate hold: not shown better than v3w (delay −0.8 % [−4.2, +1.0] and −1.2 % [−3.0, +0.2]). MaskablePPO is not the same update: it averages and normalises over all rows, 1B over open rows only. It would be a new recipe. |
| RecurrentPPO | All four. Discrete(4). Masks not supported. | The hardest on-policy row: one LSTM state per environment slot, zeroed at an episode start, no buffer argument. A recurrent layer in our own trainer, with one state per car, is less work (inference). | Same episodes; more learner time (LSTM of 256 units by default). | L2, memory. **No screen bounds it**: screens compare a memoryless policy with memoryless rules. | Nothing. No test of memory is on record. |
| TRPO | All four. Discrete(4). No masks. | As PPO. | Same episodes; one policy step per batch. No saving (estimate). | None. | Nothing. |
| TQC | Box only. As DDPG. | As SAC, with quantile critics. | As DDPG. | As DDPG. | Nothing. |
| CrossQ | Box only. As DDPG. | As SAC; only `MlpPolicy` exists, so the critic's extra inputs need custom code. | As DDPG. | As DDPG. | Nothing. |

**Notes.**
- **Discrete against continuous.** PPO, A2C, TRPO and RecurrentPPO also accept a Box, so a continuous headway would not be a reason to change family.
- **Off-policy replay.** The reward's shared terms were 33 and 43 % of its mean magnitude on one teaching trace (V386) and depend on what about 200 other cars do. A replay keeps rewards earned under older policies; a PPO batch has every car under one policy (inference). No record supports a replay design here.
- **M8, recipe variance.** No family addresses it, and adding families makes it worse: one PPO recipe change already moved delay by 3.4 % without attribution (round_1_result.md:246-248), and the learner SD is 0.3-4.1 %. With 5 learners per arm, a family effect below about 3 % could not be attributed (inference).
- **PPO-Lagrangian.** The record holds: λ ended at its cap of 10 with a target about 6 % below the rules' delay (V429, V448). Its stored training files show an entropy of 1.10-1.13 against v3w's 0.69-0.74 (exploratory), so the policy did not concentrate. That is a credit-assignment matter (M3), outside any family.

**Conditional follow-ups: the honest count is one, and it is not live now.**
1. **Memory, built in our own trainer** (a recurrent layer with one state per car, or the last few observations stacked), with RecurrentPPO's source as the reference for sequence handling. Conditions, in order: (a) a slowdown cell that is open for study, which today needs a new pre-registered cell because X1 and X2 stay closed (§5.3); (b) a rules-only check that a rule told the phase of the recovery beats the best memoryless rule, about 16 level pairs × 60 seeds × 2 cells = 1,920 runs ≈ $0.2-0.7; (c) one memory form fixed before data. Cost if it ever runs: 2 training sets (memory on, and the same code with memory off), a timer-rule opponent tuned on the same cells, checkpoint validation and evaluation: about $12-13 in all (estimate), a third of the weekly ceiling. V347 and the scheduler's "never switch" pick lean toward a KILL at (b).
2. **None as a family.** The clean test of M3's gating half is a flag in our trainer (hold alone against hold plus mask), not MaskablePPO. It is worth running only as a component of a study that a screen has opened.

**The earlier "fair vanilla" rule.** The project's claim rules read: "a standard algorithm (PPO; SAC for continuous actions) acting directly on the same actuators, with the same observations; the same training and tuning budget; checkpoints chosen on validation only" (CLAUDE.md). That text is historical: the claim bar is set by the author per study (V95). With the present Discrete(4) action, v3w's PPO is the algorithm the rule named. If a continuous headway were ever introduced, the rule would name SAC; PPO with the Box would be the like-for-like continuation of v3w, and SAC a second recipe with a replay design that has no record here. Reviving the rule is the author's decision.

## 7. Ranking, revised

Screen R is parked and is not ranked. Chances are judgements, not measurements.

| Rank | Item | Status | Chance of a usable result | Cost |
|---|---|---|---|---|
| 1 | **Plant items** (not DRL screens): a lane-end and a lane-change trace at merge 2; a PR-28 check with a criterion written first; the capacity-drop statistic with its null (PR-26); a re-check of the speed-cap oracle on plant_c3 | Needs a short protocol of its own and the author's approval. Rules-only and no-control runs; 0 cells added | High. Every outcome goes into the verification record the thesis needs (V456), and tells how the delay tie and the X1 edge must be read | About 1,000 runs, $0.1-0.4 (my estimate: 8 + 80 + 480 + 120 + 320 runs at $0.10-0.36 per 1,000). Build hours for a merge-2 variant and the traces are not estimated |
| 2 | **Screen F** (§5.2) | Protocol-ready. Conditional on two author decisions that can close it at no cost: reopening TRUCK against planb.md:575, and the trade-off claim form against planb.md:153 | Pass about 15 % (10 % with Plan B's pooled arm). A pass allows a protocol for one TRUCK-only trade-off sentence | Stage 1 about $3.3 and 5.4 machine-hours; both stages about $13.8 and 23 h; build 12-16 h |
| 3 | **Screen M** (§5.1) | Protocol-ready. Needs a CAV-contract departure and V355 set aside | PASS 3 %. A KILL (82 %) bounds one rule family, under SUMO's lane-change rule and with PR-28 open | $1.1-1.3 and about 2 machine-hours; build 16-22 h |
| parked | **Screen R** (§5.3) | Closed cells. Needs a new pre-registered cell | Unknown for a new cell; under 2 % on X1 | Not proposed |

**What changed against v0, and why.**

1. **R moved from rank 2 to parked.** Its evidence is stronger than v0 said: the X1 edge replicates on three seed sets. Its standing is weaker: the cells are closed by rules the author keeps, the edge sits at the unvalidated merge, and it belongs to one training recipe.
2. **F kept its place but lost half of its chance** (from "about 30-40 %" to about 15 %) and gained two preconditions.
   - In steady traffic the stored rows already fail its delay rule, so it is a TRUCK-only question.
   - A fair test needs 480 verdict seeds and a continued rule search, so it costs $3.3 to $13.8, not "about $5".
   - On hard-braking events, jam count and jerk, v3w is shown worse than the best searched rule.
   - TRUCK is closed by planb.md:575 in the same words as [A3]. The author kept [A3] closed for R, so this memo does not assume F may run.
3. **M kept its low chance and lost most of its meaning.**
   - No sound no-merge reference exists, so it no longer bounds "all merge actuators"; a KILL closes one always-on rule family.
   - SUMO's lane-change rule takes back 71 % of every metre a longer headway adds (§4.3), so a KILL would partly measure the simulator.
   - Its build is 16-22 h, not half a day.
4. **A new first item: the plant.** The audit shows that the sign of the TRUCK tie's two halves, the X1 edge, M's outcome and the finding "lengthening costs delay" all hang on merge-2 lane ends and the lane-change gap rule. These are verification items the thesis needs in any case, they need no DRL run, and they are cheaper than either screen.
5. **Four directions changed label, not rank.** Speed commands (P3), the lane action (P2), ramp metering (P4) and gap creation (P1) are "not tested on this plant", because their closing records do not carry over (§4.2). None moves up: each needs a build or a change to the verification record first. The speed-cap oracle re-check is the one that costs runs only, so it is in item 1.
6. **The learner side is "untested for delay", not "likely to fail".** No stored policy was trained with delay as its objective and a correct target, and retraining alone moved delay by 3.5 %. It is still not recommended now: the tie in steady and TRUCK conditions leaves about ±1 % to win there, every extra recipe is another forking path, and no library family changes the lever (§6).

## 8. Skeptics' findings and how each was handled

### 8.1 The author's seven corrections to v0

| # | Correction | Where applied |
|---|---|---|
| 1 | Screen F's continued search must use the original tuning seeds, with fresh seeds for the check only | §5.2 items 4 and 6: original pool 7,480,150-189 and check set 190-229; fresh selection sets and verdict seeds. One reading is left open for the author (§5.2, last paragraph) |
| 2 | Screen M: define the no-merge reference, justify 5 % / 3 %, label 2-4 s headways | §5.1 item 3 (three candidates, what each loads and changes, none run); item 7 (5 % from V354 and V462(1); 3 % dropped); item 10 (label, T0, smoke) |
| 3 | Screen F: delay equivalence in non-inferiority form | §5.2 item 7, K2: lower bound at 97.5 % above −1 % |
| 4 | Screen R: KILL rule for two cells | R is parked. The corrected two-cell form is on record in `phase_b_panel/R/final.md` §7: each cell read alone at 97.5 % (1 − 0.05/2), R KILLed only if both close, at most 2.5 % family-wise with no edge |
| 5 | Measures outside the reward from stored rows | §1.3 (jam metrics from the v2.3 supplement, fuel per km from the S6 rows); §5.2 item 5 |
| 6 | The pooled-arm point is for future protocols only | §1.2 M4; §4.2; §4.4 |
| 7 | $0.53 per 1,000 runs is a whole cost, the rate is about $0.36 | §2; used in §5 and §7 |

### 8.2 Round 1: critics of the v0 screens

| Finding | Severity | Handling |
|---|---|---|
| R reopens cells closed by [A3], V466 and planb.md:160; delay was already a win route there | blocker | R parked by the author (§5.3) |
| X2 already meets R's KILL on stored rows | major | Recorded in §5.3; X2 not proposed |
| R's opponent (one delay search from p333) is not the strongest | major | Opponent list for a new cell in §5.3 item 3 |
| The X1 edge follows lane-end stops at merge 2 | major | §1.4, §4.3; PR-28 first in §5.3 and §7 |
| F's own rule fires in steady traffic; scope must be stated | blocker | F is TRUCK only (§5.2 items 1, 3, 12) |
| F at 80 seeds KILLs a true 12 % edge 61 % of the time | blocker | 480 verdict seeds; power table in §5.2 item 8 |
| F's "measures outside the reward" gate was mis-specified; stored rows already show an adverse braking row | blocker | Gate removed; measures classified and stored costs printed (§1.3, §5.2 item 5) |
| "Continue to the plateau" undefined; overfits its check set | major | Fixed budget to generation 300, no result-dependent stop, re-pick on fresh seeds (§5.2 item 4) |
| "Richer rule family" has no form or budget | major | Not run (§5.2 item 4) |
| F had no delay test | major | K2 (§5.2 item 7) |
| M's no-merge reference measures route length and upstream load | blocker | Reference withdrawn (§5.1 item 3) |
| Stored rows already show longer headways near a merge cost delay | blocker | Stage 0 of M; arms start above 1.6 s only (§5.1) |
| Actuator limits for 2-4 s; lane-change gap rule | major | T0 definition and disclosures (§5.1 items 10, 12); §4.3 |
| M's cells: X1 unsuitable | major | Steady traffic at 5,300 and 6,000 (§5.1 item 4) |
| v0's "minimal capacity drop" is not supported | high | M1 reworded (§1.2); §4.3 |
| v0 double-counted the round 2 test and the S0/S1 map | major | §1.1 H1 |
| v0's verdicts "KILLed by stored rows" (scheduler) and "closed" (speed) stronger than the evidence | medium | §3 H-1 and P3 reworded; §4.2 |
| Missing directions (energy, comfort, equity, tails, sensing noise, penetration, period, preference-conditioned policy) | medium | §3 D4, D6, H-5; none ranks above the screens |
| Events misattributed to X1; wrong citation lines | minor | §1.1 H2, H3 corrected |

### 8.3 Round 2: the panel's skeptic on each revised screen

**Screen M** (8 findings, none rejected).

| Id | Severity | Finding | Handling |
|---|---|---|---|
| M-all-1 | blocker | The merge split is not a bound; the stage-0 KILL could not fire; correction 2 was not met | Split called descriptive; that KILL deleted; candidates for a reference listed with why none is run |
| M-all-2 | blocker | The 6,000 cell decided without a null or a sourced threshold | 6,000 made report-only |
| M-all-3 | major | The power table tested one comparison, the rule asked 5 % against each opponent | Rule set to 5 % against p333 and a lower bound above 0 against each; table recomputed; the stricter form left to the author |
| M-all-4 | major | A T0 stop was called a KILL; three design values have no record | T0 failure is VOID; values labelled and left to the author |
| M-all-5 | major | Preconditions had no criteria; the trace checks a counter, not lane-end behaviour | Trace renamed (PR-24); PR-28 carried in every sentence; order left to the author |
| M-all-6 | major | The identity check cannot pass by value on the five-level path | Excepted keys listed; build estimate raised |
| M-all-7 | minor | Runs at 6,000 are slower | Costed at 1.46 times; cap $3 |
| M-all-8 | minor | Side-constraint bound, spare seeds, U30's return | All three stated |

**Screen F** (8 findings, none rejected).

| Id | Severity | Finding | Handling |
|---|---|---|---|
| F-all-1 | blocker | The delay rule read a five-run mean against one run, so it did not test "within 1 %" | Default statistic changed to the mean of single-learner effects; pooled form printed beside; left to the author |
| F-all-2 | major | Recorded adverse rows missing (congested km) | Printed as stored costs |
| F-all-3 | major | A budget stop of stage 2 had no outcome | "Stage 2 not run": no pass, no KILL |
| F-all-4 | major | New generations scored against reference rows that no check reproduces | Reference rows reproduced before generation 100 |
| F-all-5 | minor | "At least 10 %" cannot be bounded by the rule | Question reworded; what the screen separates is stated |
| F-all-6 | minor | Rules set aside had lower delay bounds than a kept rule | All 9 delay-tied rules are arms (+$1.0) |
| F-all-7 | minor | A pass could be read as the claim | "This screen's rows are not evidence" |
| F-all-8 | minor | Build items, a generation range and a T0 statement missing | Added |

**Screen R** (9 findings; one partly rejected). They are kept for the template; R is parked.

| Id | Severity | Finding | Handling in the panel text |
|---|---|---|---|
| R-all-1 | blocker | The KILL is a minimum over many tied arms and can fire by noise | Power table by number of tied arms; n raised to 240 |
| R-all-2 | major | The 3 % bar was chosen after the numbers it tests | Both bars and their stored pass rates stated; in §5.3 item 4 |
| R-all-3 | major | The PR-28 label was read against the closest arm only | Read against every arm within 1.5 points |
| R-all-4 | major | "A pass allows a protocol" contradicted the label | A labelled pass allows only a PR-28 item |
| R-all-5 | major | Selection on 20 seeds picks by noise | 50 selection seeds |
| R-all-6 | major | The near-gap rule cannot reach 1.6 s at once; it also acts at merge 1 | Mechanics stated; settings that do not reach target are labelled, not removed (partly rejected: removing them weakens the opponents) |
| R-all-7 | major | The queue never clears; the long window was dropped | Report-only rows to 3,000 s |
| R-all-8 | minor | Build items; the two-cell cost | Added |
| R-all-9 | minor | Definitions and labels | Added |

### 8.4 Verifiers of the SB3 comparison

| Finding | Severity | Handling in §6 |
|---|---|---|
| No screen bounds memory | blocker | Table cell changed; follow-up 1 given a rules-only precondition |
| The plant record covers four headway values only | blocker | "Any value other than the four is outside the record" |
| Car slots contradict the trainer decision record and fail mechanically | major | Own loop is the only route |
| The off-policy "27 times" rested on an assumed update ratio | major | "A free choice with no record" |
| The follow-up's cost omitted opponents and validation | major | About $12-13 in all |
| Forking paths named, not counted; recipe variance gets worse | major | 10 trained recipes stated; note on M8 |
| MaskablePPO is not the same update as 1B | minor | "A new recipe" |
| RecurrentPPO's losses do mask rows; its buffer can be replaced | minor | Wording corrected |

### 8.5 Skeptics of the evidence audit

| Finding | Severity | Handling in §4 |
|---|---|---|
| V347 is not reversed on plant_c3: stored rules that lengthen still lose in X1 | major | §1.2 M2 and §4.2 say only v3w is below p333 |
| V395 and V401 are not superseded: the earlier recipe shows no X1 edge | major | "Recipe-dependent" in §1.1 and §4.2 |
| "The X1 edge predates plant_c3" is not supported | major | Not claimed |
| PR-28 was applied to the X1 edge but not to the TRUCK tie | major | §4.2 first row; §4.3 |
| The capacity-drop estimate cannot fail for the 0.8-s fleet | major | §4.3: untested for that fleet; direction unknown |
| The lane-change rule was mis-stated as "short headway admits mergers" | major | §4.3: it takes back 71 % of every added metre |
| Several stated bias directions could run the other way; the plant report went easy on DRL | major | Directions in §4.3 reduced to what is shown |
| The steady reading is not "superseded"; S6 is not re-read | minor | §4.2 second row |
| The TRUCK tie is not "robust" at the window end | minor | §4.4: at most about 0.4 % toward v3w |
| Missing records and defects (BN4's withdrawn DRL pass; greedy evaluation; unequal clocks) | minor | §4.1 and §4.3 |

## 9. Recommendation

**Recommended: do the plant items first, decide screen F's two questions on paper, and run no DRL screen and no training until both are done.**

In order:
1. **Write and run the plant items** (§7, rank 1) as part of the verification record: the lane-end and lane-change traces, a PR-28 check with its criterion written first, the capacity-drop statistic with its null, and the speed-cap oracle re-check. About 1,000 rules-only and no-control runs, $0.1-0.4, plus build hours that need their own estimate.
2. **Decide at no cost whether F may exist:** whether TRUCK is reopened against planb.md:575, and whether a trade-off sentence is allowed against planb.md:153. If either answer is no, F is parked beside R.
3. **Only then, F stage 1** ($3.3), if both answers are yes and the plant items did not change how the TRUCK rows read.
4. **M last, or not at all.** Run it only if the lane-change trace shows that the gap rule does not decide its outcome.
5. **Write the DRL chapter now as a bounded result:** a delay tie within about ±1 % in two cells, the close-following edge with its stored costs, the X1 edge as an open plant question, and the list of what was never tested on this plant.

Pros:
- Every dollar of item 1 produces verification evidence the thesis needs whatever DRL does (V456).
- It settles the two things that every result here hangs on, in the direction of the rules as well as of DRL.
- It keeps the cells-tested count at 91 and reopens nothing.
- It costs less than a tenth of screen F's two stages.

Cons:
- It does not, by itself, give DRL a chance to win anything.
- A PR-28 check needs a criterion and a reference for lane-end behaviour that the record does not hold; writing them is author time.
- If the lane ends prove to be an artefact, the plant changes, and the stored results would have to be re-read on the changed plant.

Weaker alternatives, and why each is weaker:
- **F stage 1 now.** It spends $3.3 on a 15 % chance of a protocol for one trade-off sentence, in a cell closed by the same rule the author kept shut for R, on rows whose location at merge 2 is not validated.
- **M now.** Cheap in dollars, but two to three days of build for a 3 % chance, and its expected KILL would partly measure SUMO's lane-change rule.
- **A new slowdown cell now** (R's successor). It is the only place with a replicated delay hint, but without the PR-28 item a pass would again be bound to the unvalidated merge.
- **Train a repaired or different learner now** (L1, memory, another SB3 family). The steady and TRUCK tie leaves about ±1 % there, no family changes the lever, and each recipe adds a forking path.
- **Build a plant with a verified capacity drop.** It is where delay headroom would be, for rules first. It is weeks of work and post hoc.
- **Stop exploring and write the null as it stands.** Defensible. It leaves PR-28 and PR-26 open, which the verification record must close before any sentence about a win or a tie against tuned rules.

**Decisions this memo asks of the author** (none is assumed):
1. Whether the plant items get a short protocol and a rental.
2. Screen F: TRUCK's closure (planb.md:575) and the claim form (planb.md:153); then its statistic, K1 form, K2 margin, rule arms and the reading of correction 1.
3. Screen M: the CAV-contract departure, V355, the four design values, and whether PR-28 comes first.
4. Whether a new pre-registered slowdown cell is wanted at all (§5.3).
5. Seeds 7,485,000-499 (M) and 7,487,000-779 (F), caps of $3, $4 and $12, and the order under the $40 per 7 days.

## 10. Files

- `drl_win_directions_v0.md`: the Phase A memo.
- `phase_a_reports/`: nine reader reports and the first stored-row scripts.
- `phase_b_round1/`: four critics, three analyses, scripts.
- `phase_b_panel/M`, `F`, `R`: drafts, judges, synthesis, skeptic, final text, scripts.
- `phase_b_sb3/`: library facts, project facts, table, two verifiers.
- `phase_b_audit/`: timeline, plant choice, metric audit, two classifications, two skeptics, scripts.

All files are untracked. Nothing was committed.
