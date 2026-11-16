# classify_late: records V380-V502 behind "DRL cannot win on delay"

**Basis.** Ledger rows V377-V502 read in full. Read: `round_1_result.md`, `round_2_result.md`, `s01_result.md` §6, `baseline_v3/BASELINE.md`, `baseline_v5/BASELINE.md`, `planb.md` §3.3-3.5, the phase B round 1 reports, `timeline.md`, `metric_audit.md`, `plant_choice.md`. Timeline entries D16, D20, D24-D29 and D31 were checked against the ledger rows and files in my range and hold; D26's V359 and V368 parts are earlier rows and were not read.

**Provenance check (mine, flags and keys only).** Every row of these files carries all plant_c3 flags (`ease`, `smooth_s` 8.0, `ease_max` 4.4, `tau_rise` 0.2, `taper_fast`, `fix_x`, `geom` r2m3) and the `all_delay` key: V382's T0 (300), confirmatory 3 primary (720) and map (1,280), 3b (360), sweep V409 (1,728), profiles V410 (360), sweep V419 (1,680), round 1 stage 0b (980), validation (3,440), test (2,240) and band (1,300), round 2 validation (7,200) and test (2,800), S1 (360), S6 (13,920). Plan B's S2, S3a and S4 rows are slim and carry no plant keys.

**EXPL** = my exploratory number from stored rows already read for a verdict. Paired seeds, median of paired differences over the reference median, 95 % percentile bootstrap unless stated, 10,000 resamples, RNG 20261110. "Single learners" = the median over the 5 × n learner differences, seeds resampled together. No simulation ran.

**Direction codes.** R toward the rules, D toward DRL, A alike, U unknown. D-numbers are the timeline's. Two added here:
- **N1:** SUMO's lane-change gap test uses the follower's commanded tau (plant_choice.md §D; MSLaneChanger.cpp:864-879). A short tau admits mergers by construction. R against any arm that lengthens; size unknown.
- **N2:** the opponent's objective is not delay.

## 0. Answer

- Every result in this range ran on plant_c3 with all-vehicle delay, and every policy in it used normalised inputs, except V382's trace arm and the teaching traces of V385-V387, which are not results. So the question here is not "does it carry over to plant_c3" but "does it survive plant_c3's own open items".
- One delay conclusion carries over cleanly: **in S and TRUCK at 5,300 veh/h, v3w ties the best rules within about ±1 %** (S6, 240 seeds).
- "v3w is worse than p333 in steady traffic" does not carry over. It is the pooled-arm statistic.
- Outside those two cells the late records do not say "DRL cannot win on delay". In X1, X2 and at 7,000 veh/h v3w is ahead of every rule that ran there by point estimate, and by interval against most ("Of 58 delay CIs, 44 favour v3w and 14 are not shown to differ; 0 favour a rule", s01_result.md:511). What stops a claim is a rule ([A3], V466), a 5 % per-policy bar, an unvalidated merge and missing delay-tuned opponents.
- The learner variants, ASCH and MPC-F are not delay negatives.

## 1. Table

| Record | Used for | Plant | Network, demand | Inputs, policies, training | Seeds, status | Open defects touching it (direction) | Verdict |
|---|---|---|---|---|---|---|---|
| V382, `conf3/prerun_output.txt` | Early-KILL check: p333 against no control, delay +29.6 / +19.9 / +12.8 % (S / X1 / X2). Trace arm in S: policy 51.3 s, p333 58.2 s | plant_c3, its first rows (`fae4620`) | r2m3, 5,300 | One stored policy "trained on P0", hand-scaled (the row's `pt` is shot `C0_final.pt`); trace only | 7,440,065-074, 10 seeds; tool check, "not evaluated for any claim" | The printed delay is finishers' delay (prerun.py:32, :54): U. 10 seeds, unpaired medians: U | SUPERSEDED by S6. EXPL: on these 10 seeds z31333 reads +13.3 % [−1.9, +16.8] against p333 in S; the same setting (pattern 3,1,3,3,3) on S6's 240 seeds reads −2.11 % [−3.50, −0.99]. The policy arm (+10.6 % [+0.4, +16.1], EXPL) was never run again |
| V395, V396, V398 | [A3] closes X1 (3 of 5: "d2 and d3 exceed the 2 % delay limit"); X2 "Delay win: 1 of 5". Used for D5/R "closed" and H5 | plant_c3 (`d2b2ecc`) | r2m3, 5,300, X1 and X2 | baseline-v3 d0-d4: normalised, 500 updates, 4,090 / 4,600 / 5,300, final only | 7,440,200-219, 20 seeds; registered | The 2 % limit is a point on 20 seeds, intervals 7-12 points wide (V413): U; "X1's closure is equally knife-edge" (V396). D24 U (to 3,000 s, delay "equal or better", V398). D25 R. D26 D. D20 D | SUPERSEDED as delay evidence by rounds 1 and 2. The closure stands as a rule that needs the author's override. It is not a finding that delay cannot be won |
| V401 | X2 not replicated: delay against os1_15_10 −10.2 to −1.6 %, against p333 −6.5 to +0.4 %. Used for H5 | plant_c3 | r2m3, 5,300, X2 | baseline-v3 | 7,440,220-239, 20 fresh seeds; registered replication | 20 seeds, paired SD 7-11 % (V435): U. D24, D25 | SUPERSEDED for the sign. v3w on 120 seeds: +5.7 % against os1_15_10, +3.7 % [+2.6, +5.1] against p333 (an_x1x2_delay_edge.md:39, :42; EXPL). The loss holds for the baseline-v3 recipe only |
| V407 | H3: "no memory and cannot anticipate" | none: a design note | none | baseline-v3's actor | none | none | CARRIES OVER as a code fact. It is not a test: memory was never tried on any plant |
| V409 | Sweep: against the rules "delay mostly within ±3 %" | plant_c3 | r2m3; 16 levels 3,920-5,910; S, X1, X2 | baseline-v3, trained up to 5,300 | 7,440,200-203, 4 used seeds; exploratory | D26 D ("tilts other levels toward DRL", V406). Levels above 5,300 are outside training: R. 4 seeds: U | CARRIES OVER IN DIRECTION ONLY. Replaced for v3w by the band and S1 |
| V410, V411, V487 | D1 "against": peak "69 % more"; varying-demand training "wasn't worth it"; SURGE dropped | V410 plant_c3. V411 not stated; INFERENCE: archived lines, since V407 says training "used constant demand per episode". V487 plant_c3 + SURGE (INFERENCE from the protocol; rows carry no plant keys) | r2m3; four profiles; a 5,300 step | V410: baseline-v3. V487: none ("No v3w row exists in S2") | V410: 7,440,200-209, 10 used seeds, exploratory. V487: 40 gate seeds, read under V486's post-read rule | V410: the rules never saw the profile either; delay "the same or 4 % less" in the step: U. V487 is a plant gate on no control and p333 (D29) | NEEDS A RE-CHECK before D1 is called either way. Cheapest: the memo's 4,140 + 960 runs, about $0.5-1.8. V487 carries no information on DRL |
| V413 | M3, L1: gate-closed decisions, "about half", unmasked; others' delay priced "about 200 times below"; reward flat after update 100 | plant_c3 | none | baseline-v3; the same trainer made v3w | code read; pooled 40 used seeds, exploratory | D27 R | CARRIES OVER as code facts. They weaken "cannot win": no stored policy was trained to win on delay |
| V419 | H1: "0.8 s gaps cut delay at every level (11-40 % less, rules and policies alike)" | plant_c3 (`6d3a1a6`) | r2m3; 21 levels 2,500-7,500; training slowdowns | baseline-v3 | 7,440,600-609, 10 fresh seeds; range readings registered, the band post hoc | No paired interval between policies and rules in the record: U. D25 R. D26 D off 5,300. Above 5,300 outside training: R. Outside the intended use (V462(4)) | CARRIES OVER for "the gain over no control is the headway". It is not a test of policy against rule |
| V429 | os1_15_10 the lower-delay rule "at every level except 5,500"; baseline-v3 J 1.016-1.026; checkpoint ranks reverse (M8) | plant_c3 (`93ec97e`) | r2m3; 4,500-6,000 by 250; training slowdowns | baseline-v3 | 7,440,340-359, 20 seeds; report-only | Two rules, medians, no interval; `delay_s` is the 1-s training-mode form: U | CARRIES OVER IN DIRECTION ONLY. A tuned rule below p333 weakens H1 as much as it supports H4 |
| V448, V449, round_1_result.md §3 | L1, H-2, M7: res delay −1.6 % [−3.5, +1.5]; attr −13.5 % [−14.5, −11.4]; lagr out, λ at its cap | plant_c3 | r2m3, 5,300, X1 and X2 | normalised; 7 levels 4,500-6,000; 5 learners, 500 updates; checkpoints on validation | 7,440,400-439, 40 seeds; registered validation | D27 R: res "cannot reach 1.2 s from 0.8 s" (:274); lagr's target "about 6 % below the rules' mean delay, not 3 %" (:65); attr untuned; each recipe trained once | NEEDS A RE-CHECK to count against learner-side delay gains: a training (about $2-3 per set) and about 160 seeds for 3 % (V435) |
| V449 test, round_1_result.md §4 | "No delay wins over the rules": delay-win reading 0 of 5 | plant_c3 | r2m3, 5,300, X1 and X2 | v3w | 7,440,500-539, 40 seeds, used once; registered | The reading needs 5 % per policy; policies reach 0.2-3.8 % and 1.9-4.3 % (:212). D25 R, D26 D, D20 D, D24 U | DIRECTION ONLY, and the direction is toward DRL: the arm has less delay than os1_15_10 (+5.5 [+3.1, +10.5], +4.7 [+1.3, +7.2]) and than p333 in X2 (+3.7 [+1.7, +5.0]) (:209-211) |
| V465, round_2_result.md §3 | H3, L1, L2: 2B, 1B, 1D, ahead, rep "not shown better"; ahead delay −0.7 [−3.2, +0.3], −0.8 [−1.6, +0.6] | plant_c3 | r2m3, 5,300, X1 and X2 | normalised; one change each to v3w's recipe, same training seeds; ahead has 18 inputs | 7,440,800-839, 40 seeds, 95 %, no correction; registered validation | D27 R: 40 seeds cannot see 1-2 %. D31 U: laptop candidate rows against remote v3w rows. Both arms are pooled, so D28 cancels | CARRIES OVER IN DIRECTION ONLY: no change moved delay by more than about 3 %. DRL against DRL, so plant defects act on both arms |
| Round 2 test; V466, V467 | H-1: sw against v3w −0.1 [−2.7, +1.7], −0.5 [−3.0, +1.8]; X2 closes; no delay-win sentence (v3w 2 of 5 per cell) | plant_c3 | r2m3, 5,300, X1 and X2 | v3w, tail, sw | 7,440,840-879, 40 seeds, used once; registered. V466 and V467 decided after the data | X2 closes on close-following margins. 3E-T counts 0.19 points inside the filter and not under two other estimators (:445): U. 3E-X "still falling at generation 40": D. D20, D24 | CARRIES OVER for sw and tail. V466 has no delay content: by point every policy arm has less delay than both 3E rules (:13) |
| V475, V477, s01_result.md §6 | Memo H1 "against": "one point estimate" at 7,000 | plant_c3 | r2m3; 3,500 and 7,000; band 4,500-6,000; training slowdowns | v3w | 7,440,900-919 and 880-899, 20 seeds; report-only; outside the intended use | Only p333, os1_15_10 and 3E-T ran there (:535): D. D28 R | The memo understates it. Record: +3.7 [+2.6, +5.2] against p333 at 7,000, 4 of 5 learners; "0 of 58 delay CIs" favour a rule (:497, :511, :574). NEEDS A RE-CHECK before H1 is stated above 5,300: 2,660-2,940 runs (:540-542), about $0.3-1.1 |
| V491 | L2, H-1, H4: ASCH "choosing a single member"; MPC-F; 3E-D "met the plateau criterion" | Rows carry no plant keys. INFERENCE: plant_c3, from the 3E-D search's `ref_cfg` (`cmab/TRUCK_delay/meta.json`) and S1's replay at `96fde8d` (V490) | r2m3, 5,300, S and TRUCK | none | ASCH 7,480,230-269; 3E pool 150-189, check 190-229; MPC-F 270-339; tuning rows, "not evidence" (planb.md:239) | N2: ASCH's library is 3E-T and 3E-C, and its steady member was picked for close-following (planb.md:205, :258; `asch.json`). MPC-F's cost is delay + 10 × close-following (:267). 20 tuning seeds | NEEDS A RE-CHECK if used for delay scheduling: a scheduler with a delay library never ran. Rules only: 1,760 tuning rows (V490) plus 3 arms × 240 seeds, under $1 |
| V496, read6 v1 | H1, H4: TRUCK = T; delay bound at or below 0 against 9 of 23; 3E-D +0.08 % [−0.57, +0.90] | plant_c3 + TRUCK (`b0c9360`) | r2m3, 5,300 | v3w, frozen, never trained on TRUCK | 7,480,400-639, 240 seeds; registered, read once | D28 R: single learners give 6 of 23 (EXPL). lr1000_10_1 equals p333 on 194 of 240 seeds. D25 R. D24 R (last 5 minutes, edges 2 to 4a: −3.31 % [−6.27, −0.60], metric_audit.md:79). N1 R. Cell chosen after DRL results (V480): D. 3E-D's check loss −1.48 % became +0.01 % on fresh seeds (critic_R.md:29): D. D29 | CARRIES OVER: a tie within about ±1 %, under every definition and both statistics. No opponent is shown below v3w (0 of 23). The count "9" is direction only |
| S6 cell S, `S.map` | "v3w worse than p333 in steady": −1.57 % [−2.70, −0.24] | plant_c3 | r2m3, 5,300, no event | v3w | the same 240 seeds; report-only | D28 R: the statistic's null is +1.31 % toward the single run (metric_audit.md:85). No rule was searched for delay in S: D | SUPERSEDED (EXPL): single learners −0.13 % [−0.99, +0.74]. At 97.5 %, 4 opponents show v3w worse at arm level and 0 with single learners. A tie |
| §1.4: power, delay split, demand against capacity (an_delay_floor.md) | H1: S6 detects about 1 %; 0.5 % unserved; v3w below p333 on no component | plant_c3 | S and TRUCK, 5,300 | v3w arm | S6 rows; exploratory | Arm-level component signs carry D28: R. Every class held to 100 km/h: A | CARRIES OVER, except the arm-level signs: redo with single learners (zero-run) |
| §1.4: hindsight scheduler (stored_rows_headroom.md §3) | H-1: best of 23 per seed 3.42 % [+2.70, +4.17]; split-half scheduler +0.01 % [−0.91, +1.02] | plant_c3 | TRUCK | none | S6 rows; exploratory | One conditioning variable, whole-run choice: U | DIRECTION ONLY. It bounds a per-run choice among stored rules. A switch inside a run is untested |
| §1.4: merge excess (critic_M.md F2) | M, P1: ceiling 9.2 % [8.4, 11.2] (S), 11.1 % (TRUCK) | plant_c3 | S and TRUCK, 5,300 | none | S6 rows; exploratory | D20 U: it sits where lane ends are not validated. N1 R. D1: a plant with a drop adds flow loss, R against every state controller | NEEDS A RE-CHECK with PR-28 |
| Dose-response (critic_M.md F3) | H1: every stored lengthening rule has more delay than p333, −2.1 to −7.5 % | plant_c3 | S; TRUCK −1.4 to −3.9 % (EXPL) | none | S6 rows; exploratory | N1 R. The rules are static, zone-wide, 1.0-1.2 s; no triggered, lane-0 or above-1.6-s form | CARRIES OVER for static zone rules. The sign also holds on finishers' delay, −2.4 to −8.2 % (EXPL). It does not cover state-triggered lengthening |
| §1.4: X1 edge (an_x1x2_delay_edge.md) | Discounts the edge: +4.2 % [+2.6, +5.5] on 120 seeds, +0.5 % in the half with few lane-end stops | plant_c3 | X1, 5,300 | v3w | 3 × 40 seeds; exploratory | The split is on an outcome ("a longer queue also produces more lane-end stops", :108): U. Truncation understates it (metric_audit.md:78): R. Nearest rule picked on the same seeds: R. Cells chosen where DRL looked best: D. D20 D | NEEDS A RE-CHECK (PR-28). Until then it is neither a DRL delay edge nor an artefact |

## 2. Reading

### (i) H1, H3, H4

- **H1, steady and TRUCK at 5,300.** It rests on S6, which carries over: plant_c3, normalised policies, 240 paired seeds, all-vehicle delay. The reading is a tie, not a loss. The steady "loss" disappears with single learners.
- **H1's stronger half, "close to optimal".** It leans on records that need a re-check or are narrow:
  - 3E-D is one search in one family that reads 4 of the 16 inputs.
  - The dose-response covers static zone rules only, and N1 pushes it toward p333.
  - The oracles (V344, V347) are early records on P0.
  - No oracle or ceiling run exists on plant_c3.
- **H1 outside those two cells.** No late record supports it. X1 (+4.2 %, 120 seeds, EXPL), X2 (+3.7 % against p333, about +2 % against the nearest rule, EXPL) and 7,000 veh/h (+3.7 [+2.6, +5.2], record) point the other way. They are disputed on PR-28, on missing delay-tuned opponents and on the intended use.
- **H3.** The code facts carry over. "Widening has not helped" rests on three attempts. Only `ahead` ran on plant_c3 with normalised inputs, and it stopped at validation, where 1-2 % is invisible. The speed action (V339) and the lane action (V317) are early records.
- **H4.** For delay in S and TRUCK it carries over (S6). For delay in X1 and X2 it is untested: no delay-objective search ever ran there. The unconverged searches bias toward DRL, so H4 on close-following is a lower bound.

### (ii) Directions of memo §3

- **L1.** Its S and TRUCK verdict rests on S6: carries over, for those cells. `1B` carries over in direction only. `lagr`, `attr` and `res` need a re-check.
- **L2.** `ahead`: direction only. ASCH: needs a re-check (N2).
- **L3.** M8 (V429; round_1_result.md:250-251) carries over.
- **P1.** "Ramp queues near zero" carries over at 5,300 only. At 6,000 the ramp-2 queue is 5,760.5 veh-s (critic_M.md F8, EXPL). V194-V195 are early.
- **P2, P3, P4, P5, D4, H-5.** The closing records are early (V317; V339, V344, V241, V149; V333; V256, V245; V342; V304). They are outside this file.
- **D1.** No closing record. V410 is 10 used seeds with baseline-v3. V411 is not on plant_c3. V487 has no policy row.
- **D2, D3, D6.** No closing record: inference or protocol exclusions.
- **D5 / R.** Closed by rules ([A3] in V395, V466, planb.md:160), not by delay findings. V395 is superseded as evidence.
- **H-1.** `sw` carries over. The hindsight bound is direction only. ASCH and MPC-F did not test delay scheduling.
- **H-2.** Inference from H1; it holds where H1 holds.
- **H-4.** V368 is early. The late copy rule agrees for a hand-traced static copy: −12.17 % against p333 in TRUCK, −7.2 % [−12.6, −4.8] in X1 (round_2_result.md:285). A tree on the actor's inputs was never built.

### (iii) Three re-checks that would change the most

1. **PR-28, lane ends at merge 2.**
   - It decides the X1 edge and the 9-11 % merge ceiling.
   - If the behaviour is sound, X1 is a replicated delay edge over every stored rule, and H1 fails in slowdowns.
   - If it is an artefact, the edge goes and p333's own delay at merge 2 changes in every cell.
   - Cost: a trace of `end_stop2` (about 12 runs, my estimate), then no control, p333, os0_10_10, lr1000_10_1, r4a1 and 5 learners × S and X1 × 120 seeds = 2,400 runs, about $0.24-0.86, on a merge-2 variant that needs code.
2. **A delay-objective rule search in X1.**
   - It is the only cell with a replicated delay edge, and H4 was never tested for delay there.
   - If the search finds no rule below p333, "tuned rules absorb the headroom" fails for delay in X1.
   - Cost: 40,640 rows × $0.115 per 1,000 = about $4.7, plus 16 arms × 120 seeds = 1,920 runs, about $0.2-0.7.
   - It needs the author's override of [A3] and planb.md:160, and it is post hoc.
3. **N1, the lane-change gap test tied to the commanded tau.**
   - It touches H1 on every plant where a headway is commanded through `setTau` (INFERENCE: m32 to plant_c3; I checked the code path on plant_c3 only, b_env.py:784).
   - If the dose-response flips once the gap test no longer reads the commanded tau, targeted lengthening opens for rules and DRL alike.
   - Cost: a lane-change trace, 4 arms × 20 seeds = 80 runs, under $0.03. Then 6 arms × 240 seeds × S and TRUCK = 2,880 rules-only runs, about $0.3-1.0, after a code or SUMO change.
   - I did not check whether SUMO offers a switch for it.

Zero-run re-checks done here (EXPL): the single-learner recount of S6, and the dose-response on finishers' delay.

### (iv) Biases against the rules or for DRL

Where these apply, "DRL cannot win" is, if anything, stronger than recorded.

- **Cells chosen after DRL results.** X1 and X2 ("chosen where DRL already looked best", claim_review_round2.md:221); TRUCK (V480). S6 is still a tie.
- **Searches that overfit or did not converge.**
  - 3E-T lost from −14.3 % to −4.4 % on fresh seeds (round_2_result.md:394).
  - 3E-X was "still falling at generation 40".
  - 3E-C is "not converged at 100 generations".
  - 3E-D lost 1.5 points from check to fresh seeds.
  - Each weakens the opponent.
- **Sweeps off 5,300.** The rules were "tuned at 5,300 only" (V406, V409, V419).
- **Thin opponent sets.** The band and S1 carry three rules; 12 never ran there (s01_result.md:535). No rule was searched for delay in S, X1 or X2.
- **Checkpoints chosen on validation.** An in-sample gain of "about 0.2-0.3 points of delay" (round_2_result.md:107); r1's seeds also confirmed v3w as incumbent.
- **D20, if it is an artefact.** It favours the arm that lengthens at merge 2.

Biases the other way on the same records: D25, D27, D28, N1, truncation.

## 3. Never tested on plant_c3 with normalised inputs

- A per-CAV speed action, a speed-cap oracle, a headway oracle or any ceiling run.
- A lane action; ramp metering (ALINEA).
- r1m3 with a policy. Only one no-control row of r1m3 P0d was reproduced (V382, T3).
- A policy trained with delay as its objective and a correct target (`lagr` mis-set, `attr` untuned).
- A policy retrained for TRUCK, or trained with time-varying demand.
- A delay-objective rule search in S, X1 or X2, or at 5,500-7,000.
- Memory, headways outside 0.8-1.6 s, a CAV share other than 50 %.
- A scheduler or MPC with a delay objective.
- The 20-cell delay reading of V359. Confirmatory 3's map (S, H1, H2 at 4,600 and 5,300, 20 seeds, baseline-v3) was read for harm only (V395: "no harm cells").

## Limits

- Rows before V377 were not read; early closing records are named, not classified.
- `read6_v23.json` was not opened; S6 values come from V496, the reports and my recount, which reproduces the 9 blockers and their points.
- The single-learner statistic is not a registered reading.

## Files

`/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit2/late/`: `prov.py`, `prov2.py` (provenance tallies), `s6x.py`, `dose.py` (dose-response on three delay definitions), `s6all.py`, `block.py` (blockers, arm level and single learners), `t0.py` (V382 rows), each with `*_out.txt`.
