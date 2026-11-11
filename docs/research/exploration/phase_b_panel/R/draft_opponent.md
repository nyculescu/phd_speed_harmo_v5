# Screen R, slowdown recovery: protocol-ready draft (strongest opponents, plant validity)

Stored-row numbers are EXPLORATORY (rows already read for verdicts). Every interval states its level.

## 1. Question; what a pass allows; what a KILL closes

**Question.** In X1 (two tapered slowdowns to 25 km/h on edge 4; conf3/common.py:14) at 5,300 veh/h on plant_c3: does frozen v3w keep a delay edge over every non-learning arm the record can field, each tuned in X1 on separate seeds? Is the edge off the unvalidated merge-2 lane end, and does it outlast the 1,800-s window?

**A pass** allows a protocol for a new study, labelled post hoc (planb.md:576). It is never a claim and never stands without section 12's no-control clause (planb.md:153).

**A KILL** closes the delay route for per-CAV DRL in X1 and X2 on this plant; [A3] stands in full.

## 2. Approvals and preconditions

1. **Author override, post hoc, X1 only.** It sets aside [A3], "no further training, tuning, plant change or seed round" (confirmatory_3.md:132; V395); planb.md:160, "no rule is re-tuned there either"; and V456(3), because X1 is picked from control results. Delay was one of [A3]'s two routes and was read without a win in rounds 1 and 2 (round_1_result.md:212; round_2_result.md:282). This is X1's fourth test (round_2_result.md:239). V466 stays: X2 remains closed.
2. Its own cap (proposed $16), the rental, the seeds. Plan B's cap does not carry over.
3. **Plant checks before any v3w row; a failure stops the screen.**
   - PR-26, zero runs: the capacity-drop estimator with a computed null on stored no-control rows (plant_vv_record_v0.md:77). Report-only; while open, "capacity drop not settled" is carried.
   - PR-13, identity, determinism: `pert_log` shows both events; the 7 stored acceptance rows reproduce; a repeated seed is equal (planb.md:388-390).
   - PR-10 (no r2m3 T0 record, plant_vv_record_v0.md:46): uniform 1.6 s against 0.8 s on the grid seeds gives `tau_on_match`/`tau_on_n` ≥ 0.99 (plant_sweep.py:227); `passed` and `mean_v` differ, 95 % CI excluding 0.
   - PR-28 control: HYB (section 4) has fewer `end_stop2` seconds than p333, 95 % CI excluding 0. Otherwise the artefact control is void.

## 3. Stage 0: statements from stored rows (zero runs)

All EXPLORATORY.

- **X2 is decided.** Three 40-seed sets pooled, against os0_10_10: +1.9 % [+0.5, +4.0] (95 %), below 3 %. Round 2's test seeds, against lr1000_10_1: +4.1 % [−0.4, +5.8] (97.5 %) (an_x1x2_delay_edge.md:36; critic_R.md:23). It meets K1 with no new opponent. No X2 run.
- **X1 is open.** Against p333: +4.2 % [+2.4, +5.9] (97.5 %, 120 seeds; an_x1x2_delay_edge.md:7), 5 of 5 learners. The S0/S1 map repeats round 2's test seeds (an_x1x2_delay_edge.md:20).
- **Not a clean pass as stored.** Against p333, 60 % of the edge is on road 4a; Spearman 0.73 with lane-end stops; +0.5 % in the half of seeds with few (an_x1x2_delay_edge.md:59, :74).
- **No control.** v3w has 16.6 % more close-following [8.4, 25.1] (95 %; round_2_result.md:265). V459's harm half fires.

## 4. Arms

| Arm | Definition | Tuning seeds (7,485,…) |
|---|---|---|
| v3w | 5 frozen learners (planb.md:188), evaluation mode; per-seed mean | none |
| Carried (15) | planb.md:203's list, unchanged; holds lr1000_10_1, lr1000_16_2, os0_10_10 | old |
| Grid delay picks (3) | 69-rule grid (conf3/common.py:28-36) plus 20 LocalRules (r 1,600 or 2,000 m × th 10, 13, 16 m/s; r 400 or 1,000 m × th 7 or 20 m/s; each at 1.2 and 1.0 s); the 3 lowest median delays with collisions ≤ p333's + 1; no close-following bound (confirmatory 3's delay opponent had one, confirmatory_3.md:62) | 350-369 |
| HYB | ZoneOwnState (b_env.py:1107-1129), fixed now: zone merge 2 = os0_10_10's setting (1.6 s below 10 m/s with ≥ 10 accelerating-lane vehicles, else 0.8 s); other zones = p333 | none |
| 3E-D, two starts | planb.md:221-239 unchanged; starts p333 and HYB; CMA seeds 20261130, 20261131 | pool 370-409; check 410-449 |
| ASCH-D | planb.md:253-260's scheduler and grid; undisturbed p333; disturbed rule from both 3E-D picks, grid pick 1, os0_10_10, lr1000_16_2; lowest median delay with collisions ≤ p333's + 1 | 450-469; check 470-489 |
| No control | never deciding, never alone | none |

- HYB, INFERENCE: against p333 the edge is at merge 2; against os0_10_10 it is on road 3 (93 %, an_x1x2_delay_edge.md:61).
- 22 deciding arms; duplicates run once (planb.md:213). 3E-D alone is not enough: in TRUCK it ranked behind os0_10_10 and p333 on delay (V496; recorded_table_out.txt:3-6). MPC-F is omitted, disclosed: optional (CLAUDE.md), last on delay there (recorded_table_out.txt:13).
- **Equal exposure.** v3w's checkpoints were chosen on X1/X2 validation seeds (planb.md:188). Every tuned arm is tuned in X1, knows the cell, may read up to 2,000 m ahead; each search gets 40,640 rows (V490). This favours the rules (planb.md:215).

## 5. Measures

| Measure (key) | Role | Reward |
|---|---|---|
| Door-to-door delay (`all_delay`) | deciding | tied to terms (code_lever.md:24) |
| Close-following (`ttc_net`) | harm guard | a term |
| Served flow, collisions, moving full-emergency events, drain (planb.md:328-334) | guards | flow, collisions: terms |
| Merge-2 share (planb.md:143); `end_stop2`; 3,000-s delay (`episode` 2,700, rerun.py:89) | label | outside; delay tied |
| `delay_ramp2`, robust braking, −4.5 m/s² events, fuel per km, jam metrics (planb.md:330, :338) | report-only | outside |

## 6. Seeds proposed

The ledger shows no use from 7,485,000; the author must confirm.

| Seeds | One purpose |
|---|---|
| 7,485,300-309 | smoke, identity, determinism |
| 350-369 | grid picks, PR-10, PR-28 control |
| 370-409; 410-449 | 3E-D pool; check |
| 450-469; 470-489 | ASCH-D tuning; check |
| 500-619 | verdict, n = 120, one round |
| 310-349, 490-499, 620-699 | reserved |

## 7. KILL rules

Statistic: planb.md:424 (median of paired differences over the opponent's median; positive = v3w has less delay).

- **K1.** KILL if, against any deciding non-learning arm, the point is below 3 % or the 97.5 % lower bound is at or below 0.
- **K2.** KILL if fewer than 4 of 5 learners have a positive point against every arm (planb.md:438).
- **K3.** KILL if close-following is more than 10 % worse by point with the 95 % upper bound below 0 against any arm (planb.md:437).
- A failed guard (planb.md:438): "metric survives, gate failure", no protocol.
- **Order.** Search settings are frozen in code before any verdict row. A script reads K1-K3 after the cheap arms, KILL only, and again at the end. The early read cannot pass anything.

**Numbers.** 3 %: the smallest edge a later study detects with 80 % power at n = 120 (planb.md:519), above the 2 % tie band (confirmatory_3.md:52). Alternative: 5 %, [A3]'s delay-win size (confirmatory_3.md:108). 97.5 %: m = 2 is kept although X1 alone decides; X1 is what remains of a two-cell look, and m is never lowered when a cell drops (planb.md:428).

**Author's alternative, two deciding cells (correction 4).** X2 gets the same arms and searches; V466 is then set aside too. Each cell is read alone at 1 − 0.05/2 = 97.5 % and survives or closes on its own; R is KILLed if neither survives. Family-wise: with no edge in either cell, a lower bound is above 0 in at most 5 % of studies. No pooling. About $14 more.

**A survivor while PR-28 is open.** A clean pass needs, against the closest delay opponent: (a) a merge-2 share of at most 50 % (planb.md:143); (b) that opponent's `end_stop2` not shown higher than v3w's (95 %); (c) K1 on the 3,000-s window. Otherwise: "survives, PR-28 open" or "survives at 1,800 s only". Neither allows a DRL protocol; only a rules-only verification item follows.

## 8. Null and power

EXPLORATORY, my computation (script path at the end): 120 pooled X1 seeds, 12 stored rules, v3w shifted to a true edge over the closest rule; 400 studies, n = 120.

| True edge | 0 % | 2 % | 3 % | 4 % | 5 % |
|---|---|---|---|---|---|
| Survives K1 and K2 | 0.0 % | 0.2 % | 32.8 % | 86.5 % | 99.0 % |

- The lower bound alone passes a true 0 in 1.0 % (nominal 1.25 %). n = 160 gives 89.2 % at 4 %, so n = 120.
- It can fail (stored X2) and pass (stored X1 against stored rules).
- Paired SD 7.5 %; the 97.5 % half-width, about 1.8 points, is the smallest edge a KILL bounds.
- Limits: resampled used seeds; a new opponent enters only as a shift.

## 9. Runs × rate = cost

| Step | Runs or rows | Hours | Cost |
|---|---|---|---|
| Smoke; grid, 91 arms × 20 | 1,950 | 0.4 | $0.26 |
| Cheap arms, 25 × 120 | 3,000 | 1.8 | $1.08 |
| 3E-D × 2 | 81,280 | 15.4 | $9.35 |
| ASCH-D; new arms, 3 × 120 | 2,320 | 0.6 | $0.36 |
| 3,000-s window, 28 × 120, survivor only | 3,360 | 3.3 | $2.02 |

Rates: correction 7 ($0.36 per 1,000 runs with the pack; $0.115 per 1,000 search rows); long runs costed at 1.67 times (INFERENCE). Full path: 91,910 runs, about 23 h and $14 with 6 % setup (V475). KILL at the early read: about $1.4. Build (my estimate): about 13 h with tests and review. Author time, apart: about 1.5 h.

## 10. Plant and verification effect

- No plant file changes. No new actuator value (1.6, 1.2, 1.0, 0.8 s only); T0 here is PR-10's missing record.
- X1 at 5,300 is inside the intended use (plant_vv_record_v0.md:9). The 3,000-s window has one report-only precedent (V398).
- Harness changes only (search cell and seeds, grid names, scheduler library, reader, the longer window with the pack), each with a planted-row test; then a smoke check.
- No departure from the CAV contract: every arm commands ALKS headway levels through existing rule classes (b_env.py:991, :1117, planb_v23 copy).

## 11. Cells added to the count (N = 91) and post hoc labels

Cells added: 0. X1 at 5,300 is counted (cells_tested.md:30); a re-test adds 0 (cells_tested.md:5). N stays 91 (V487). Post hoc: the screen, the cell choice, HYB, the 3 % threshold.

Rejected: critic_R.md:59's generality row. It adds a cell (N = 92) with untuned opponents, so it cannot decide; it belongs in a later protocol.

## 12. Must-carry disclosures

- The override; X1 chosen where DRL looked best and tested three times before (claim_review_round2.md:221).
- Against no control: more close-following and hard braking (round_2_result.md:265; s01_result.md:453), so a delay edge is a trade-off (claim_review_round2.md:197; planb.md:153).
- Moving full-emergency events: 15 of 200 learner-runs in X1, 24 of 200 in X2 (round_1_result.md:202).
- The queue never clears in X2 (V398); X1 is unchecked, hence read-out (c). PR-08, PR-26, PR-28 open; X1's two events never occur in training (cells_tested.md:29).
- Tuned arms know the cell; MPC-F omitted; plateau labels.

## 13. Expected outcome and probability

My judgement, not measured. KILL about 65 %: HYB, or a search started from it, targets the 60 % of the edge at merge 2. "Survives, PR-28 open" or "at 1,800 s only" about 25 %. Clean pass about 10 %; even then V459 is not met on stored rows.

Files: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/draft_opponent.md`; power script and its output: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/opp_work/power.py`, `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/opp_work/power_X1.out`. `fin.py` in that folder is a side check that feeds no number here.
