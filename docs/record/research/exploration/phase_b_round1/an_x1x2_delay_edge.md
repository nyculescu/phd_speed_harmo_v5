# an_x1x2_delay_edge: v3w's delay edge in X1 and X2 (screen R)

Every number computed here is EXPLORATORY (the rows were already read for verdicts). Statistic: median of paired differences over the rule's median, in %, positive = v3w has less delay (`all_delay`, plant_sweep.py:347); 95 % percentile bootstrap, 10,000 resamples, RNG 20261110. The stored tables use 20,000 resamples and RNG 20261104 (conf3/common.py:79-89); my round 2 test values match them within 0.2. Arm = per-seed mean of the 5 learners. Scripts and outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/x1x2/` (a2, b2, c1, d1, e1; `.out` files).

## 0. Answer

- **X1: the edge is replicated, about 4 %.** The nearest rule is the fixed rule p333: +4.2 [+2.6, +5.5] on 120 seeds (97.5 %: [+2.4, +5.9]), 5 of 5 learners.
- **X2: the edge over the nearest rule is about 2 %, below screen R's 3 % threshold.** os0_10_10 +1.9 [+0.5, +4.0] (97.5 %: [+0.1, +4.3]); 3E-X2 +2.3 [+0.6, +4.0] on 80 seeds.
- **Against p333 the edge sits at merge 2** (road 4a and ramp 2) and appears only in seeds where p333 has many stopped vehicles at the acceleration-lane end. It is a plant-artefact candidate (V396).
- **"No rule searched for delay" needs one qualifier:** confirmatory 3 picked a "delay opponent" per cell from its grid. No delay-objective search exists for X1 or X2.

## 1. Paired effects, three seed sets

| Set | Seeds | v3w checkpoints | File under `/home/catalin/work/phd/v5b1_runs/` |
|---|---|---|---|
| r1 | 7,440,500-539 | round 1's (validate2.py:60) | `round1_remote/out/test/test.jsonl` |
| r2v | 7,440,800-839 | round 1's, so not chosen on these seeds | `round2/val/rows_6c49e7e.jsonl` |
| r2t | 7,440,840-879 | round 2's (`round2/val/chosen.json`) | `round2/test/rows_6c49e7e.jsonl` |

**The S0/S1 map is not a second sample.** `measure_s01_remote/rows_test.jsonl` holds the same seeds, and all 2,800 `all_delay` values equal the round 2 test rows. Memo line 45 repeats line 44.

40 seeds per set; 3E rules are absent from r1. SD = SD of the paired difference. Last column: learners with CI above 0, pooled.

| X1 rule | r1 | r2v | r2t | Pooled | n | SD | Learners |
|---|---|---|---|---|---|---|---|
| p333 | +2.6 [−1.8, +5.4] | +4.1 [+2.5, +6.8] | +5.5 [+2.9, +8.0] | +4.2 [+2.6, +5.5] | 120 | 7.5 | 5/5 |
| lr1000_10_1 | +4.3 [+2.4, +6.3] | +4.6 [+1.8, +8.4] | +5.0 [+3.0, +8.8] | +4.6 [+3.4, +6.0] | 120 | 7.4 | 5/5 |
| os0_10_10 | +4.8 [+0.0, +8.9] | +3.6 [+1.5, +8.4] | +5.5 [+3.2, +9.0] | +4.6 [+2.9, +6.9] | 120 | 10.3 | 5/5 |
| 3E-X1 | - | +6.3 [+1.7, +11.5] | +7.8 [+4.0, +11.3] | +6.5 [+3.9, +10.8] | 80 | 8.7 | 5/5 |
| no control | +28.0 [+25.4, +30.6] | +27.6 [+24.3, +31.6] | +27.3 [+24.7, +30.4] | +28.2 [+26.3, +29.6] | 120 | 6.9 | 5/5 |

Other X1 rules, pooled: 3E-T +5.5 (80 seeds), lr1000_16_2 +6.3, os1_15_10 +6.4, lr400_13_2 +6.7, z33133 +7.0, os1_10_0 +7.9, r4a1 +8.7, a4400_10_1 +10.6, lr400_16_1 +11.5, copy +14.1. Every CI is above 0.

| X2 rule | r1 | r2v | r2t | Pooled | n | SD | Learners |
|---|---|---|---|---|---|---|---|
| os0_10_10 | +1.6 [−1.9, +6.0] | +1.9 [−0.4, +4.3] | +2.4 [−0.6, +7.5] | +1.9 [+0.5, +4.0] | 120 | 7.0 | 2/5 |
| 3E-X2 | - | +1.4 [−0.5, +4.8] | +3.0 [+0.7, +5.4] | +2.3 [+0.6, +4.0] | 80 | 6.3 | 3/5 |
| lr1000_10_1 | +3.0 [+0.1, +7.7] | +2.2 [−2.6, +6.1] | +4.1 [+0.2, +5.4] | +3.3 [+0.8, +5.1] | 120 | 6.9 | 4/5 |
| p333 | +3.7 [+1.7, +5.0] | +2.3 [−0.8, +4.7] | +6.1 [+3.4, +7.4] | +3.7 [+2.6, +5.1] | 120 | 6.1 | 5/5 |
| no control | +23.2 [+20.5, +25.6] | +22.2 [+20.3, +24.7] | +23.5 [+21.7, +25.4] | +23.0 [+21.9, +24.2] | 120 | 5.4 | 5/5 |

Other X2 rules, pooled: os1_10_0 +5.6, os1_15_10 +5.7, lr1000_16_2 +6.3, lr400_13_2 +6.6, z33133 +6.9, 3E-T +7.5 (80), r4a1 +7.6, a4400_10_1 +9.4, lr400_16_1 +9.8, copy +11.1. Every CI is above 0.

**Rules against p333, pooled.** X1: no rule has a point estimate below p333's delay, and 11 of 13 are shown worse (lr1000_10_1 −1.3 [−2.4, −0.6], os0_10_10 −2.4 [−3.7, −0.5]). X2: 3E-X2 +1.9 [−0.2, +3.8], lr1000_10_1 +0.8, os0_10_10 +0.7; none is shown better. The memo's X2 figure against p333 (+6.1) is the highest of the three sets.

## 2. How 3E-X1 and 3E-X2 were found

- **Objective:** pooled close-following change against p333, plus a delay hinge above +1 % and collisions (round_2.md:58-59). Population 24, 40 generations, 16 of 40 seeds per generation, seeds 7,440,740-779 (`round2/cma3e_x*/meta.json`).
- **Convergence:** `still_falling: true` in both `final.json` files (X1 −30.8 against −22.5; X2 −30.9 against −26.0; round_2_result.md:100). X1's pick is from generation 3; later points exceeded the delay cap (V461).
- **Delay on tuning seeds:** the picks are 1.05 % and 1.64 % below p333 (V461). The lowest shortlisted point, X2's g012i03, is 2.69 % below, as a by-product.
- **Delay-selected rules that exist:** confirmatory 3's "delay opponent", the lowest median delay in its grid among rules with close-following at most 10 % above p333 (confirmatory_3.md:62), on seeds 7,440,160-179: lr1000_10_1 (X1) and os1_10_0 (X2) (`baseline_v3/opponents.json`:19, :39). It is a grid pick, not a search. 3E-D exists for TRUCK only (V491).

## 3. Where the difference arises (r2t seeds; space-time files of the S0/S1 run)

Means of paired differences, as shares of the total. Mainline delay comes from the 10-s by 50-m field (measure.py:101). "Off-mainline" is the remainder: ramp roads, junctions and the main-origin queue, not separable.

| Rule minus v3w | Total, veh-s | Road 4a | Road 3 | Off-mainline |
|---|---|---|---|---|
| X1, p333 | +13,921 (+5.7 %) | 60 % | 21 % | 22 % |
| X2, p333 | +11,475 (+4.8 %) | 64 % | 18 % | 25 % |
| X1, os0_10_10 | +15,040 (+6.0 %) | 14 % | 93 % | −1 % |
| X2, os0_10_10 | +6,495 (+2.8 %) | 13 % | 93 % | 2 % |
| X2, 3E-X2 | +8,219 (+3.6 %) | −3 % | 132 % | −13 % |

The ramp insertion queues carry −2 to +3 %; only X2 against p333 is shown (+241 veh-s [+19, +542]).

By absolute time, mainline part against p333:
- **X1** (slowdowns 600-720 and 1,200-1,320 s): 300-840 s 4 %; 840-1,200 s 25 %; second slowdown 10 %; 1,320-1,440 s 8 %; 1,440-1,800 s 28 %. v3w has put 4 more vehicles into road 4 by 840 s, 15 by 1,200 s, 15 by 1,440 s and 20 by 1,800 s.
- **X2** (slowdown 700-880 s): before 3 %; slowdown 2 %; 880-1,000 s 0 %; 1,000-1,400 s 18 %; 1,400-1,800 s 51 %. No extra vehicles until 1,020 s, then about 2 per minute up to 25 at 1,800 s, with no levelling off.

Markers against p333:
- **Lane-end stops.** Stopped seconds in the last 30 m of acceleration lane 4a_0 (`end_stop2`, plant_sweep.py:294), medians: X1 p333 2,518, v3w 1,278, no control 728; X2 1,912, 819, 592.
- **Ramp-2 vehicles.** Their mean delay differs by +18.9 s [+12.0, +26.2] (X1) and +14.3 s [+9.1, +19.2] (X2), against +6.0 s and +4.6 s over all vehicles. They are about 300 of 2,150 vehicles entering 4a.
- **Per seed (120).** The delay edge correlates with the `end_stop2` difference: Spearman 0.73 (X1), 0.78 (X2). In the half of the seeds where p333 has fewer lane-end stops the edge is +0.5 % (X1) and 0.0 % (X2); in the other half +7.5 % and +6.9 %.

Against os0_10_10 and the 3E-X rules, `end_stop2` and ramp-2 delay are not shown to differ. The difference is the queue on road 3.

## 4. Learners

The edge is in all five. Pooled against p333: X1 +2.2, +2.7, +4.2, +6.1, +3.8; X2 +3.0, +2.2, +2.9, +3.7, +3.6; all ten CIs above 0. Against X2's nearest rule: +0.9 to +2.8, 2 of 5. On one 40-seed set the single-learner counts are unstable (X1 against os0_10_10 on r2t: 1 of 5). baseline-v3 does not show the edge: +1.7 [−1.0, +4.6] and +2.4 [−0.5, +4.3] against p333 (`round2/report/test_table.csv`).

## 5. Seed overlap

- **r2t chose nothing.** Checkpoints were chosen on 800-839 (decide1.py:19-26), 3E-X on 740-779, 3E-T on 700-739, the grid rules on 7,440,160-179.
- **r2v** with round 2's checkpoints is selected on its own seeds; I used round 1's there.
- **r1:** v3w was confirmed as the incumbent on these seeds (V449). A small bias toward v3w is possible; against p333, r1 gives the lowest X1 value.
- **"Nearest rule"** is picked afterwards from 13-15 rules on the same seeds. This understates v3w's edge.
- Not at seed level: the cells were chosen where DRL looked best (claim_review_round2.md:221).

## 6. Variance and seeds needed

Paired SD against the nearest rule, arm level: X1 p333 7.5 % (6.7-8.3 by set); X2 os0_10_10 7.0 % (5.8-8.1). Single learner: 8.9-11.2 % and 8.1-9.4 %.

| 80 % power, 97.5 % CI | 3 % | 5 % |
|---|---|---|
| Normal approximation on the mean, SD 7.5 | 59 | 22 |
| Resampled stored differences, median statistic, X1 p333 | 80 | 30 |
| Same, X2 os0_10_10 | 100 | 25 |

The memo's 60 check seeds are sized for 5 %, not for its 3 % threshold.

Resampling 60 of the 120 seeds under the drafted rule (point at least 3 % and 97.5 % lower bound above 0), stored rules only: X1 survives in 83 % of resamples against p333 and in 70 % against the nearest rule picked on the same seeds; X2 in 35 % (lowest-median-delay rule) and 9 % (nearest rule).

## 7. INFERENCE

- **Mechanism against p333-like rules:** v3w lets ramp-2 vehicles in. It keeps ALKS on ramp 2 near 1.6 s (s01_result.md:403) and reads the distance to the nearest acceleration-lane vehicle, which the searched rule family does not (code_lever.md:13, :53). Fewer vehicles stop at the lane end, and merge 2 discharges about 1 % more while its queue lasts. Static versions lose to p333 in X1 (r4a1 −4.9 %, copy −10.6 %), so the timing matters.
- **Mechanism against own-state and 3E-X rules:** they lengthen headways in slow traffic to cut close-following and pay for it on road 3. That is their objective, not a v3w skill. A delay search would drop it, as 3E-D did in TRUCK (V496).
- **Artefact candidate: yes, for the part against p333.** 82-89 % of it is on road 4a and off the mainline, and it follows lane-end stops, whose realism was never validated (V396). The correlation is not proof of cause: a longer queue also produces more lane-end stops.
- **Window dependence:** the queue never clears (V398), and in X2 the gap still grows at 1,800 s, so the percentage depends on the window end.
- **For screen R:** X2 is likely KILLed by stored rules alone. X1 likely survives unless the search finds a rule below p333, and no stored rule is. The KILL needs both cells, so R as drafted would probably pass on X1 alone, on a lane-end effect. Suggested additions: screen M's targeted-gap rule as an arm; `end_stop2` and the road split as fixed read-outs; 80-100 check seeds; a longer window.

Not found: a per-time record of the main-origin queue; any delay-objective search in X1 or X2.
