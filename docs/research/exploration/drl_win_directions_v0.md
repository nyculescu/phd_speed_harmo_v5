# Where could learning-based control beat the tuned controllers? Design memo v0

Written 2026-11-10 by the project-review session, from the brief `docs/handoff/2026-11-10_fable_drl_exploration_prompt.md`. State of the records: V501.

**Status of this memo.** It is a proposal. Nothing in it is decided, no simulation ran, no seed was used, and no ledger row was written. Every number computed for this memo from stored rows is exploratory, because those rows were already read for a verdict.

**How it was built.** Nine independent readers covered the ledger (V1-V501), the round 1, round 2 and Plan B results, the code, the earlier direction sweeps, the web literature, and the stored S6 rows. Their reports are in `phase_a_reports/` beside this file and carry the file:line citations. Literature found on the web was opened through a summarising fetch tool, not read in full, so every paper named here is [VERIFY].

**Terms.**
- p333: the fixed rule "0.8 s time headway in every zone".
- v3w: the frozen per-CAV PPO policy set (5 learners).
- Close-following: seconds with time-to-collision below 3 s, read at 1 Hz.
- Delay: door-to-door delay with origin and ramp queues, in vehicle-seconds over the fixed window.
- 3E-C, 3E-D: the per-cell CMA-ES rules of Plan B, searched for close-following (C) or for delay (D).
- Positive percentages mean the first-named arm is better.

## 0. Summary

1. **A delay win over tuned rules on this plant, with this actuator, is unlikely.** The fixed rule p333 ties for the lowest delay among 23 opponents in the TRUCK cell. A 100-generation delay search that started from p333 ended at p333 (+0.01 % [−0.45, +0.25]). The S6 study could detect about 1 % (exploratory power estimate), so any true delay edge there is below about 1 %.
2. **The cause is structural, and two parts of it are missing from the brief's list.** The plant was tuned to have a minimal capacity drop (V314), so there is little breakdown for a controller to prevent. The action is one-sided: 0.8 s is both the floor of the action set and the best rule, so against p333 a policy can only lengthen headways.
3. **The close-following edge is real and has replicated**, against all 23 opponents in TRUCK and 5 of 5 learners in rounds 1 and 2. It has four open threats: the measure is in the reward, it is read at 1 Hz, it arises mostly in a queue at the unvalidated second merge, and the rule search that came nearest (3E-C) was not converged.
4. **Fifteen directions are listed in §3.** Most are called "likely to fail", with the record that says so.
5. **The top three,** each with a screen that can KILL it before any DRL training (§5):
   - **F, the frontier claim:** equal delay and fewer close-following seconds than any searched rule. Screen: exhaust the rule frontier. About $5 for the first stage.
   - **R, slowdown recovery:** a delay edge over rules after a transient slowdown, seen only in report-only rows. Screen: a converged delay-objective rule search in X1 and X2. About $10.
   - **M, merge coordination with a wider headway range:** the only delay mechanism the literature supports. Screen: a no-merge reference and a long-headway sweep, rules only. Under $1. Expected to KILL.
6. **Recommendation (§6):** run screen M first because it is nearly free and closes the delay question for three directions, then screen F stage 1. Do not train anything until a screen passes.

## 1. Evidence map

### 1.1 The five working hypotheses

**H1. For delay, a fixed short headway is close to optimal. Supported, strongly in steady and TRUCK conditions, less cleanly in the slowdown cells.**

For:
- r1m3, 5,300 veh/h: policies against p333 on delay +1.5 [−0.8, +4.0], +1.8 [+0.3, +3.1], +1.3 [−1.6, +3.1] %; they spend 82-98 % of the time at 0.8 s (V337, V339).
- "0.8 s gaps cut delay at every level (11-40 % less, rules and policies alike): a property of the headway, not of DRL" (V419).
- Confirmatory 2: no delay win in any of 20 cells (V359).
- TRUCK, S6: no opponent is shown below p333 on delay. 3E-D, the delay search, ends at p333: +0.01 % [−0.45, +0.25] (read6_v23.json `overfit_vs_p333`; V491, V496).
- Steady reference on the S6 seeds: v3w has more delay than p333, −1.57 % [−2.70, −0.24] (read6_v23.json `S.map`).
- Oracles on r1m3: the speed-cap oracle shows headroom in 0 of 8 cases (V344); the headway oracle (1.2 s near the slowdown) pays delay −4.5 [−5.5, −3.0] % for close-following +56.8 % (V347).

Against:
- Round 2 test, arm level, descriptive and uncorrected: v3w has less delay than p333 in X1, +5.5 [+2.9, +8.0] %, and in X2, +6.1 [+3.4, +7.4] % (`round2/report/test_table.csv`).
- S0/S1 map, report-only: v3w better than all 14 rules on delay in X1, +5.0 to +11.6 %, and than 13 of 14 in X2 (planb.md:304).
- A tuned rule that is not fixed, os1_15_10, has less delay than p333 at most demand levels 4,500-6,000 (V429).
- At 7,000 veh/h, one point estimate outside the intended use: v3w 3.7 % below p333 (V475).

Reading: the brief's sentence "DRL ties the 0.8-s rule on delay" is exact for steady and TRUCK conditions. In the slowdown cells the policies are ahead of p333 by about 5 %, but tuned rules take most of that back (X2: 3E-X2 at 229,111 against v3w 226,353 veh-s by medians; confirmatory 3b: delay against os1_15_10 −1.6 to −10.2 %, V401). No delay-objective rule search was ever run in X1 or X2 (the 3E-X searches minimised close-following with a delay hinge, round_2.md:58-59).

**H2. The persistent edge is on close-following, which is in the reward; against no control the policies are not safer. First half supported; second half depends on the cell.**

- In the reward: `gap/dv < 3.0` for the vehicle and, at half weight, its follower, weight 10 (b_env.py:811-812, :842-843).
- Edge against rules: TRUCK +11.8 % [+5.0, +19.7] (smallest, against 3E-C) to +36.3 % (V496); rounds 1 and 2 replication against p333 5 of 5 (round_1_result.md:126, round_2_result.md:224).
- Against no control it fails in X1: −16.6 [−25.1, −8.4] % in round 2, with more hard braking and 15 and 24 moving full-emergency events in 200 learner-runs against 0 (round_2_result.md:265; round_1_result.md:202-206).
- Against no control it holds in TRUCK, +29.06 % [+26.35, +33.31], and in steady traffic, +45.86 % [+42.20, +50.47] (read6_v23.json `no_control.cf95`; the steady value is this memo's exploratory computation).
- Part of the edge is outside the rewarded pair: humans behind humans, +8.1 to +23.4 % against p333 (V398).

**H3. The lever is narrow. Supported by the code; widening it has not helped so far.**

- Code: the only command is `setTau`; the target applies only behind an ALKS leader within 150 m, otherwise 1.6 s; MLP actor, no memory; the merge-zone speed input covers merge 1 only (b_env.py:774-784, :925-935, :499-509; c_train.py:41-42).
- "The policy sees only local state, never demand itself; it has no memory and cannot anticipate" (V407).
- Widening tried: a 12-action speed-and-headway set, declined 88-95 % of the time (V339); a lane action, 30 and 68 collisions in 10 runs, not traced (V317); two look-ahead inputs (`ahead`), no delay gain, X2 close-following +7.3 [+2.4, +11.2] % against v3w (round_2_result.md).
- Never tried: memory, headways outside 0.8-1.6 s, a validated lane or merge actuator (claim_review_round2.md:214).

**H4. Tuned and searched rules absorb the headroom. Supported for delay; about two thirds supported for close-following.**

- Delay: see H1.
- Close-following: 3E-C cuts the TRUCK edge from about 27 % to 11.8 % and was "not converged at 100 generations" (V496). In X2 the margin fell from 22-31 % against os1_15_10 to 7.5-14.1 % against 3E-X2 (round_1_result.md:120; round_2_result.md:197-198). In steady traffic the edge over 3E-C_TRUCK is not shown: +7.99 [−9.72, +25.32] % (exploratory).
- Against: rules do not transfer between cells (in TRUCK, copy −12.17 %, 3ex1 −3.64 %, 3e −4.45 % delay against p333), and searched rules lost part of their gain on fresh seeds (3E-T from −14.3 % to −4.4 %, round_2_result.md:394; r4a1, V368).
- The CMA-ES rule reads 4 of the actor's 16 inputs and uses the same action (b_env.py:1117-1129). So the rule family that was searched is a strict subset of what the actor can represent. No richer rule family was searched.

**H5. Honest testing removes fragile wins. Supported.**

- Confirmatory 3: X2 won at the minimum (4 of 5), "won" in about 27-30 % of seed resamples, then 1 of 5 on fresh seeds (V395, V396, V401).
- Round 2: X1's win excludes the cell's own CMA-ES rule; X2 closes with 3E-T counting 0.19 points inside the delay filter (round_2_result.md:7-9, :16).
- Against: the close-following edge itself survived every recount, filter and fresh-seed check. What failed each time was the delay condition.

### 1.2 Reasons missing from the brief's list

| # | Reason | Records |
|---|---|---|
| M1 | **The plant has a minimal capacity drop by design.** The author tuned it so that no control is the best possible and accepted that this "leaves less room for any controller". Disturbances other than an imposed slowdown form no wave. Without a drop, delay headroom is mostly redistribution. | V314, V315, V342, V304, V244, V255(5) |
| M2 | **The action is one-sided and gated.** 0.8 s is the floor of the action set and is the best rule. The action binds only behind an ALKS leader. Against p333 a policy can only lengthen headways, which trades delay for close-following. | b_env.py:37, :774-779 (reader's inference) |
| M3 | **The reward does not carry the headline metric to the vehicle.** Delay enters as a shared count and as local speed; others' delay is priced about 200 times below the bar's rate; about half of the decisions are gate-closed and enter the loss unmasked; the reward is flat after about update 100. | V413, V385, V364; b_env.py:554, :842 |
| M4 | **The bar is conjunctive.** A win needs delay and close-following against every opponent, for 4 of 5 single learners. With H1 true, NULL is the expected outcome. The pooled arm (per-seed mean of 5 runs) is compared with single runs on a right-skewed measure: the pooled point against os0_10_10 is −0.58 % while the five per-learner points average +0.04 % (exploratory). | planb.md:438, :519, :531; `phase_a_reports/stored_rows_headroom.md` §1 |
| M5 | **Information favours the rules.** Rules are tuned per cell with the condition known; they answer every 5 s, the policy every 10 s; LocalRule reads 400-1,000 m ahead; v3w was not retrained for TRUCK. | V381(2), V478; planb.md:197, :215 |
| M6 | **The measure where DRL leads is weakly validated.** It is mostly low-speed queue following (48-62 % below 7 m/s), concentrated at merge 2, whose lane-end behaviour was never validated; part of the gain is moved from the accelerating lane to the mainline; it is read at 1 Hz. The 0.1-s meter was built and not run. | V377(3), V396, V398, V433-V435 |
| M7 | **The learner variants are not clean negatives.** `res` had a confounded action range, `lagr` a mis-set target (about 6 % below the rules' delay, not 3 %), `attr` an untuned weight; five of seven round-2 candidates stopped at validation on 40 seeds, where a 1-2 % delay gain is not detectable (paired SD 7-11 %). | round_1_result.md:65, :243, :273-275; round_2_result.md:133; V435 |
| M8 | **Training-recipe variance exceeds method effects.** Learner SD 0.3-4.1 %; checkpoint rank at update 100-250 is opposite to update 500. | round_1_result.md:250-251; V429 |

### 1.3 What the stored S6 rows add (exploratory)

From `phase_a_reports/stored_rows_headroom.md` (240 paired seeds, TRUCK):
- The best single opponent removes 29.3 % of no-control delay, v3w 28.9 %. The rows hold no free-flow or no-merge run, so the share that any controller could still remove is unknown.
- A hindsight oracle that picks the best of the 23 opponents per seed is 3.42 % [+2.70, +4.17] below the best single opponent. This is an upper bound inflated by selection: picking the best of the five nominally equal v3w learners per seed "gains" 2.09 %, and a scheduler fitted on half of the seeds gains +0.01 % [−0.91, +1.02] on the other half.
- No opponent is shown better than v3w on delay or on close-following. At delay within ±1 % of the nine tied rules, v3w has 22.6-30.3 % fewer close-following seconds. The nearest rule on close-following, 3E-C, pays 1.1 % more delay.
- Paired SD of the delay difference: 5.3 % of the median. A study of the S6 size detects about 1 % with 80 % power. A 3 % delay effect needs about 30 seeds, a 5 % effect about 11 (pooled arm, normal approximation).

### 1.4 What the literature adds (all [VERIFY])

- The only freeway cases found where RL beat a tuned or shortest-headway baseline with the same actuator use **spatially targeted lengthening of headways upstream of a merge**, from section-level state: Veksler et al. 2024 (arXiv 2412.02520; "up to" 7 % average speed at 100 % CAV, headways 1.5-6 s) and Elmorshedy, Smirnov and Abdulhai 2023-2024 (delay "up to" 22-57 % against static headways; abstracts only; the local review notes 100 % ACC and no tuned feedback baseline).
- Vinitsky et al. 2020/2023 (ACM TCPS): CAVs that meter inflow beat a tuned feedback rule by about 15 % outflow at 5 % penetration, equal a traffic-light ALINEA at 40 %, with lane changing disabled.
- Hybrids beat their base controller by an amount that tracks how badly the base is tuned: 35 % from a deliberately mis-set MPC (Airaldi et al.), about 1.5 % derived over hand-tuned PI gains (Önür et al. 2025).
- No freeway study was found in which the conventional controller was re-tuned per condition.
- Cautions: Jayawardana et al. 2022 (NeurIPS): fixed-time and max-pressure beat four DRL methods once evaluation covers a family of scenarios. The I-24 field test reports energy trends, not delay.
- The local synthesis reached the same view before this memo: "at a realistic drop, the mobility headroom at a bottleneck is small *for every controller*" (`rl_value_synthesis_v0.md`:49).

## 2. Cost basis

| Item | Rate | Source |
|---|---|---|
| Evaluation run with the measurement pack, rented machine | 2,600-3,050 runs/h on 59 workers; $0.10-0.13 per 1,000 runs | V475 |
| S6-style evaluation on 90 workers | about 1,690 runs/h; about $0.53 per 1,000 runs | V493, V494 (reader's arithmetic) |
| CMA-ES rule search | about 5,500 rows/h; about $0.11 per 1,000 rows; one 100-generation search is 38,440 + 2,200 rows, about 7.7 h | V490, V493 |
| One PPO training set (5 learners × 3 environments, 500 updates) | 500 × 23.5 s ≈ 3.3 h on an idle machine; about $2-3 on a rental (my estimate from V450, not measured per set) | V391-V392, V450 |
| Budget | $40 per 7 days; Plan B's $20 cap stands at about $17.50 used | V488, planb.md:561 |

Every simulation below runs on a rented machine (V483) and needs the author's approval, a rental and a seed range.

**Cells-tested count.** N = 91 (V487). A new (perturbation × demand level) cell in which a per-CAV DRL policy runs adds 1. Rules-only rows add 0 (cells_tested.md:5). A cell proposed after the Plan B results is a new study, labelled post hoc (planb.md:576).

## 3. Candidate directions

Each block gives: the mechanism; why a tuned rule could not match it and how opponents get equal exposure; evidence for and against; literature; what to build and the effect on the plant's verification record; cost; risks; cells added. "Verdict" is this memo's judgement.

### Route 1: improve the learner

**L1. Training repair package (mask gate-closed decisions, tune the attributed-delay weight, correct the Lagrangian target, merge-2 inputs).**
- Mechanism: v3w is under-trained on delay (M3) and half-blind at merge 2 (input 13 covers merge 1 only; `LEN_3`, `LEN_4` are r1m3's lengths, V365(4)).
- Why a rule could not match: none stated. A repaired learner still acts through the same one-sided lever (M2).
- For: `lagr`, `attr` and `res` were not clean negatives (M7). v3w's retraining gave about 3.4 % delay over baseline-v3 (round_1_result.md:105-106).
- Against: H1. 3E-D ends at p333. `1B` (mask and hold) showed nothing at validation.
- Literature: none found that supports learner-only gains against tuned baselines [VERIFY].
- Build: code only, no plant change. Cost: 3 training sets ≈ $6-9 plus evaluation 3 × 5 × 80 × 2 cells = 2,400 runs ≈ $0.3. Author time: 1 h.
- Risks: forking paths (many recipe knobs, each trained once). Cells added: 0 if evaluated in existing cells.
- **Verdict: likely to fail on delay.** Worth doing only as a component of F or R after a screen passes.

**L2. Memory (recurrent actor or stacked observations).**
- Mechanism: infer hidden state: wave phase, event onset, demand trend.
- Why a rule could not match: a memoryless rule cannot; a rule with a timer or hysteresis (ASCH) can, and ASCH would be tuned on the same conditions.
- For: never tried (claim_review_round2.md:214). The policy does shift by condition (V386).
- Against: look-ahead inputs gave no delay gain; ASCH, which has memory, picked "never switch" in TRUCK (V491).
- Build: code only. Cost as L1. Risks: one more recipe; small expected effect.
- **Verdict: likely to fail alone.** Memory matters only where the best action changes in time, which D1 would have to show first.

**L3. Other algorithm classes (QMIX, SAC-discrete, model-based RL, evolution strategies, imitation then fine-tuning).**
- Mechanism: none specific to this plant.
- Against: recipe variance exceeds method effects (M8); H1 bounds every algorithm that uses the same lever.
- Literature: listed and unverified in the 2026-11-05 handoff; Ault and Sharon 2021 report instability of IPPO on signal control [VERIFY].
- **Verdict: likely to fail.** Not recommended.

**L4. Wider headway range with spatial targeting (longer than 1.6 s before a merge; see M below).**
- This is the learner side of direction M in §4. It needs only `setTau`, the actuator the plant record already covers.

### Route 2: change the plant or the actuators

**P1. Cooperative gap creation for a named ramp vehicle.**
- Mechanism: a lane-0 CAV opens a gap when a ramp vehicle approaches, so the ramp queue (in the primary metric) shrinks and the merge causes less braking.
- Why a rule could not match: it can. A targeted-gap rule with the same inputs is the natural opponent; the learner would have to time gaps better.
- For: input 14 (distance to the nearest accelerating-lane vehicle) exists. Literature: Veksler et al. [VERIFY].
- Against: the courtesy-gap rule failed with 10 teleports (V194, V195); the central merge cap is unused since run 3; "Expect a small mobility effect" (prior_art_B_v0.md:205); M1.
- Build: `openGap` is forbidden by the CAV contract, so use `setTau` lengthening (as in M). Otherwise a contract change and new T0-T3 checks.
- **Verdict: folded into M.** Alone, likely small.

**P2. Lane assignment upstream of the merges.**
- Mechanism: CAVs leave lane 0 before a merge; ramp vehicles enter a lighter lane.
- Why a rule could not match: a fixed "keep left before the merge" rule probably captures most of it.
- Against: the lane action failed as built, 30 and 68 collisions in 10 runs, never traced (V317); lane changing is not validated on this plant (planb.md:183); the contract forbids `changeLane` (V309); Vinitsky et al. report that lane changing degrades their controllers [VERIFY].
- Build: a safe lane actuator, new tool checks T0-T3, and a lane-change validation that does not exist. Author time: days.
- Cost: build dominates. Risks: a result that is a property of SUMO's lane-change model.
- **Verdict: high cost, high artefact risk.** Screen M's no-merge reference bounds its delay headroom first.

**P3. Per-CAV speed commands (CAVs as a moving meter).**
- Against: policies declined the speed action (V339); the speed-cap oracle shows 0 of 8 (V344); all six MTFC arms "clearly worse" (V241); mainline metering KILL (V149); "the actuator can only slow" (V271); M1.
- Caveat: V367 found hidden hard braking in the smooth cap, so V339 and V344 "need a look".
- **Verdict: closed by the record.**

**P4. Coordination with ramp metering.**
- Against: "ALINEA gains nothing" on r1m3 (V333); r2m3 has a signal at one ramp only (corridor.py:72-73); Pan et al. 2021 report metering is not significant at high CAV shares [VERIFY].
- **Verdict: likely to fail.**

**P5. A plant with a verified capacity drop.**
- Mechanism: a drop makes breakdown costly, so preventing or delaying it saves delay. This is where the literature's delay gains live.
- Against: "closed for SUMO" (V256); the calibrated-plant study was rejected (V245); V314 chose the opposite on purpose; "no controller has yet been tested on a plant with a verified drop, because no such plant exists in this project" (V255(5)).
- Build: a new plant and a full verification record. Weeks of author time, not hours of compute.
- **Verdict: the only route with documented delay headroom, and the most expensive.** Outside the writing-phase plan (V456). Listed so that the thesis can state why delay headroom is small here.

### Route 3: disturb the plant

**D1. Demand that changes inside a run (step or surge), with rules tuned on the same distribution.**
- Mechanism: the best headway pattern differs by demand level; a state-dependent policy follows the change, a rule tuned at one level does not.
- Equal exposure: one rule tuned on the whole distribution, a two-regime scheduler (ASCH) tuned on it, and a per-level lookup table that knows the level (the project's arm "I").
- For: exploratory, 10 used seeds: under a step, 36-42 % fewer close-following seconds than the two rules at the same or 4 % less delay (V410).
- Against: under a ramped peak, 69 % more than the rules (V410); the rules were tuned at 5,300 only; os1_15_10 is the lower-delay rule at almost every level, so the best rule barely changes with demand (V429); SURGE was dropped at gate S2 for stuck vehicles and drain (V487); "a tie is likely" (explore2/candidates.md:37); the author judged varying-demand training not worth it (V411).
- Build: none for the plant; a drain-safe step profile. Cost: rule grid 69 rules × 20 seeds × 3 levels = 4,140 runs ≈ $0.5; evaluation 80 seeds × 12 arms = 960 runs ≈ $0.1-0.5.
- Risks: the expected gain is on close-following only, so this is a cell for claim F, not a delay claim. Cells added: 1 per profile.
- **Verdict: a candidate regime for F, not a direction of its own.**

**D2. Shift not seen in tuning (CAV share 30-70 %, driver-mix scale), frozen policy against frozen rules and against re-tuned rules.**
- Mechanism: regret. For each condition the re-tuned rule is the reference; the claim is that one frozen policy loses less than one frozen rule.
- For: searched rules transfer badly (copy −12.17 %, 3ex1 −3.64 %, 3e −4.45 % delay in TRUCK) while frozen v3w ties p333. The report-only adaptation gain in TRUCK is 1.56 [1.19, 2.09] on close-following and 1.05 [0.90, 1.33] on delay (V496).
- Against: p333 is itself a parameter-free rule that transfers perfectly, and it is the delay reference. So the regret claim reduces to the close-following edge again. A share or driver-mix change is a plant change (excluded from Plan B for that reason, planb.md:312-320). Vinitsky et al. report that RL trained at 10 % penetration does "significantly worse" at 40 % [VERIFY].
- Build: plant variants and a verification note per variant. Cells added: 1 per variant and level.
- **Verdict: weak as a delay claim; usable as robustness rows of F.**

**D3. Incidents or work zones.**
- Against: a headway lever cannot remove a blocked lane (the TRUCK lesson: the truck-induced delay was +31.5k veh-s for v3w and +33.2k to +33.6k for four of the best rules, exploratory); lane closure was excluded for stranded vehicles, WORKZONE as "may not bind" (planb.md:312-320); the incident code is on another plant (incident.py).
- **Verdict: likely to fail; heavy build.**

**D4. String-unstable human drivers and wave damping.**
- Against: the plant absorbs disturbances (V342); making humans unstable "by design" is the straw-man the local synthesis warns of, and "non-RL controllers do as well" (rl_value_synthesis_v0.md:26-28); fuel barely separates controllers, 79.4-80.0 g/km (V339); the field evidence is energy, not delay [VERIFY].
- **Verdict: likely to fail, with a straw-man risk.**

**D5. Slowdown recovery (the X1/X2 family). See R in §4.**

### Route 4: hybrids

**H-1. A DRL scheduler over a library of whole rules.**
- Against, from stored rows (exploratory): the hindsight bound is 3.42 % and is mostly selection; a fitted scheduler realises +0.01 %; ASCH picked "never switch"; MPC-F is −1.24 % [−1.95, −0.77] against p333.
- **Verdict: KILLed by the stored rows.**

**H-2. Residual policy on the best rule, full action range.**
- Against: with p333 as the base and the full range, this is v3w's own problem again. `res` on os1_15_10 tied on delay and kept a third to a half of the close-following margin (round_1_result.md:241).
- **Verdict: likely to fail.**

**H-3. A rule-based guard under the policy (shield).**
- Mechanism: remove the policy's harmful modes in X1 (more close-following and hard braking than no control) while keeping its edge over rules.
- Why a rule could not match: not a win mechanism. It repairs the half of claim F that fails in X1.
- Build: a guard that forces 1.6 s (the no-control headway) under named conditions; code only. The guard's conditions are a new forking path.
- **Verdict: a component of F if X1 stays in scope.** Note that in X1 every short-headway controller, rule or DRL, is worse than no control on close-following (claim_review_round2.md:187).

**H-4. Policy distilled into a rule (decision tree on the actor's 16 inputs).**
- Mechanism: the neural policy finds a control law that hand design and a 20-parameter search did not; a small tree makes it inspectable and testable as a rule.
- For: "DRL led to" the rule r4a1 (V361); the per-road copy fails on delay (V395), so the state dependence carries value.
- Against: if a tree matches v3w, the run-time controller is a rule. The claim becomes "learning as a design method", not "DRL beats tuned rules". r4a1 did not hold on fresh seeds (V368).
- Build: fit trees to logged state-action pairs; evaluation only. Cost: 5 trees × 80 seeds × 2 cells = 800 runs ≈ $0.1-0.4.
- **Verdict: a report-only arm inside screen F.** It tells which sentence the thesis can write.

**H-5. RL-tuned rule parameters, or a learned forecast inside MPC-F.**
- Against: the literature gain over a hand-tuned base is about 1.5 % (Önür et al., derived) [VERIFY]; MPC-F is weak here; H-1's bound applies.
- **Verdict: likely to fail.**

## 4. First ranking

| Rank | Direction | Chance of a credible result (my estimate, not measured) | Cost of the KILL screen | Why |
|---|---|---|---|---|
| 1 | **F. Frontier claim** (equal delay, fewer close-following seconds than any searched rule; D1, D2, H-3, H-4 as its cells and arms) | about 30-40 % | about $5 (stage 1) | The only edge that replicated. Its threats are testable without training. |
| 2 | **R. Slowdown recovery, delay** (D5) | about 15-25 % | about $10 | The only delay edge over rules in the records, report-only. One search decides it. |
| 3 | **M. Merge coordination with a wider headway range** (L4, P1; bounds P2) | about 10 % | under $1 | The only delay mechanism with literature support. The screen also bounds all merge actuators. |
| 4 | D1 as a delay claim | under 10 % | about $1 | V429: the best rule barely changes with demand. |
| 5 | L1, L2 alone | under 10 % | $6-9 each | H1 bounds them. |
| 6 | P2, P5 | unknown | days to weeks of build | Outside the writing-phase plan. |
| closed | P3, P4, D3, D4, H-1, H-2, H-5, L3 | | | See each block. |

The probabilities are judgement, stated so that they can be argued with.

## 5. Headroom screens for the top three (draft, before the adversarial review)

Common rules for the three screens:
- No DRL training. Frozen v3w only, evaluation mode.
- Criteria fixed before data. Paired seeds, median of paired differences, 97.5 % percentile bootstrap CIs.
- A smoke check after any code change, and tool check T0 (the command binds) for any new headway value.
- Seeds are proposals. The ledger shows 7,480,000-639 as the highest used range; I propose a block from 7,485,000, and the author must confirm it is free.
- Each screen is exploratory. A pass allows a protocol, not a claim.

### 5.1 Screen M: is there delay left to win at the merges?

**Question.** If merge friction were removed, or if CAVs opened long gaps before the merges, would delay fall below the best tuned rule by a margin worth a study?

**Arms (rules only), cells S (steady, 5,300) and X1:**
1. p333 and no control (anchors); os0_10_10 (the best TRUCK rule on delay).
2. **No-merge reference:** the same vehicles and departure times, with the ramp vehicles entering at the main origin, all CAVs at 0.8 s. It is a reference with a capability no controller has, not a strict bound.
3. **Long-headway sweep:** lane-0 CAVs within 300 m or 600 m upstream of each merge at 2.0, 3.0 or 4.0 s; 0.8 s elsewhere (6 arms).
4. **Targeted gap rule:** a lane-0 CAV within d of an accelerating-lane vehicle takes 2.0 or 3.0 s for 10 s; d = 50 or 100 m (4 arms).

**KILL thresholds.**
- KILL all merge-coordination directions for delay (M, P1, P2) if the no-merge reference is not at least 5 % below p333 on delay, with the CI lower bound above 3 %.
- KILL the headway-based version (M, P1) if no arm of 3 or 4 beats the best of p333 and os0_10_10 by at least 3 % with the CI lower bound above 0.
- A pass of the first and a KILL of the second leaves only lane or merge actuators, which need the contract change and validation of P2.

**Runs and cost.** 14 arms × 40 seeds × 2 cells = 1,120 runs ≈ 0.4 h ≈ $0.15-0.6. Build: a route variant, three headway values in the rule code, one rule; about half a day of code and tests. Author time: about 1 h. Seeds proposed: 7,485,000-039. Power: 40 seeds detect about 3 % (from the S6 variance, exploratory).

**Expected outcome:** KILL (V347, V349, V355, M1).

### 5.2 Screen F: can a searched rule reach v3w's point?

**Question.** Is v3w's close-following edge at equal delay still there when the rule search is finished and the rule family is as rich as the actor's inputs?

**Stage 1 (TRUCK).** Continue 3E-C from generation 100 until the Plan B plateau criterion holds, at most 200 more generations. Then evaluate on fresh check seeds: v3w (5 learners), the converged rule, p333, os0_10_10, no control.

**Stage 2, only if stage 1 passes.** (a) Two more searches at delay hinges 0 % and +2 %, to trace the rule family's frontier. (b) One search of a richer rule family that reads the actor's inputs the current family lacks: leader gap, closing speed, lane, distance to the nearest accelerating-lane vehicle. (c) Report-only: decision trees of depth at most 6 fitted to each learner (H-4).

**Measures.** Close-following at 1 Hz (the stored definition) and, fixed before data, measures outside the reward from the 0.1-s meter (`explore2/e1_meter.py`): TTC below 1.5 s, DRAC, braking events at 4.5 m/s² or harder.

**KILL thresholds.**
- KILL F if, against any searched rule whose delay is not shown worse than v3w's by more than 2 %, v3w's close-following edge has a point estimate below 10 % or a CI lower bound at or below 0.
- KILL the word "safety" if v3w is shown worse than the best rule on any measure outside the reward, or is not shown better on at least one.
- The decision trees are report-only. A tree that matches v3w changes the sentence (H-4); it does not KILL the controller.

**Runs and cost.** Stage 1: up to 76,800 search rows ≈ 14 h ≈ $8.5 at most (about $4 if the plateau comes within 100 generations), plus the check: 80 seeds × 9 arms = 720 runs ≈ $0.4. Stage 2: 3 searches ≈ 122,000 rows ≈ 22 h ≈ $13.5, plus the check. Author time: about 2 h. Seeds proposed: search pool 7,485,100-139, check 7,485,200-279. Cells added: 0 (TRUCK is already counted).

**Expected outcome:** uncertain. The steady-traffic reading (edge over 3E-C_TRUCK not shown) argues for a KILL; the 11.8 % lower-bounded edge in TRUCK argues against.

### 5.3 Screen R: does the slowdown delay edge survive a delay-searched rule?

**Question.** In X1 and X2, v3w is ahead of p333 on delay by about 5 % (descriptive). No rule was ever searched for delay there. Does a converged delay rule close the gap?

**Arms.** A 3E-D search (delay objective, start from p333, the Plan B recipe) to plateau in X1 and in X2. Then on fresh check seeds: v3w (5 learners), the two delay rules, p333, os0_10_10, os1_15_10, 3E-X1, 3E-X2, no control.

**KILL threshold.** KILL R if, in both cells, v3w's delay advantage over the best non-learning arm has a point estimate below 3 % or a CI lower bound at or below 0.

**Runs and cost.** 2 searches × 40,640 rows ≈ 81,000 rows ≈ 15 h ≈ $9; check 60 seeds × 13 arms × 2 cells = 1,560 runs ≈ $0.2-0.8. Author time: about 1 h. Seeds proposed: pool 7,485,300-339, check 7,485,400-459 (60 seeds, the count V435 gives for a 5 % margin). Cells added: 0 (X1 and X2 are counted).

**Must-carry disclosures.** X1 and X2 were chosen where DRL looked best and were tested repeatedly (claim_review_round2.md:221). The gain arises in the recovery queue at merge 2, whose lane-end behaviour was never validated (V396). In X1 the policies are worse than no control on close-following.

**Expected outcome:** KILL in X2 (3E-X2 is already within about 1 % by medians); open in X1.

## 6. Recommendation (draft)

**Recommended: run screen M, then screen F stage 1, and train nothing until a screen passes.**

Pros:
- M costs under $1 and replaces three build-heavy directions with one number. Whatever it shows goes into the thesis as a bound.
- F tests the only edge that has replicated, and its screen needs no training.
- Both keep the count of cells tested at 91.
- A KILL of both gives the thesis a clean, bounded null (V456 accepts a null).

Cons:
- F, if it survives, is a trade-off claim (equal delay, fewer close-following seconds), not a delay win, and in X1 it fails against no control.
- Screen F stage 2 would use most of a week's budget.

Weaker alternatives:
- **R first.** It is the only delay hint, but it rests on two cells with the strongest selection history, and X2 is nearly closed already.
- **Train an improved learner now (L1, L2).** It spends $6-9 per recipe against a ceiling that H1 and 3E-D put at about 0.
- **Build a new actuator or plant (P2, P5).** Days to weeks of build and a new verification record, in the writing phase.
- **Stop exploring and write the null.** Defensible now. It leaves the frontier question open, which a reviewer of the thesis will ask.
