# Screen R, slowdown recovery: draft (statistical rigor)

Every number in §3 and §8 is EXPLORATORY: stored rows already read for verdicts, three 40-seed sets pooled to 120 (an_x1x2_delay_edge.md:14-18). Scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/rigor_work/` (`power.py`, `power2.py`, `.out`).

Round 1 findings: closure §2; evidence §3; deciding cells §7; opponents §4; artefact §5, §7; no control §1, §7; seeds §6, §8. Not adopted: a 3,000-s window as a KILL clause (the queue never clears, V398; §5 has time read-outs); a new severe cell (a forking path); X2 report-only rows (V466 stays untouched).

## 1. Question; what a pass allows; what a KILL closes
- **Question:** in X1 at 5,300 veh/h, is frozen v3w's door-to-door delay at least 3 % below every non-learning controller tuned for delay there, and where does the difference arise?
- **A pass allows** a protocol for a two-measure study in X1. It is not a claim; no delay-only sentence follows (planb.md:153).
- **A KILL closes** the delay route against tuned controllers on these slowdowns; [A3] stands as written.

## 2. Approvals and preconditions
1. **Author decision (new V#), labelled post hoc** (planb.md:576; V456(3)). For this screen only it sets aside "no further training, tuning, plant change or seed round" (confirmatory_3.md:132; X1 closed by V395) and "no rule is re-tuned there either" (planb.md:160). It records that delay was already a win route there, read four times without a win (critic_R.md:9). X2 is not run, so V466 stands.
2. The screen's own cap ($10 proposed), the rental, the seeds (§6).
3. Before any other run: the 7 stored rows replay on every key; each arm class runs twice with equal rows; pack on equals pack off (planb.md:388-393).
4. Before the reading: p333 has at least 10 % less delay than no control, 95 % CI excluding 0 (planb.md:406). Stored, 95 %: +24.7 % [+23.7, +25.9].

## 3. Stage 0: statements from stored rows
| Statement | Value | Decides? |
|---|---|---|
| X1, nearest rule p333 | +4.2 % [+2.4, +5.9] at 97.5 %; 5 of 5 learners; no rule's point is below p333 (an_x1x2_delay_edge.md:7, :44). The S0/S1 map repeats round 2's test seeds (:20) | No: no delay-tuned opponent exists |
| X2, nearest rule os0_10_10 | +1.9 % [+0.1, +4.3] at 97.5 %; 3E-X2 +2.3 % (an_x1x2_delay_edge.md:8) | Scope: §7's rule passes in 0.4-5 % of resamples at n = 160; X2 leaves the deciding set |
| Location against p333 | 60-64 % on road 4a; Spearman 0.73-0.78 with lane-end stops (an_x1x2_delay_edge.md:59-60, :74) | Fixes §5's read-outs |
| No control, X1 | close-following −19.7 % [−23.7, −15.2] at 95 %; recorded −16.6 % [−25.1, −8.4] (round_2_result.md:265) | Fixes the pass wording |

## 4. Arms
X1 only. Every tuned arm is selected on delay, on its own seeds.

| Arm | Definition | Selection |
|---|---|---|
| v3w | 5 frozen learners, evaluation mode; per-seed mean (planb.md:195) | none |
| Carried rules (15) | planb.md:203, unchanged | none |
| Grid delay pick | confirmatory 3's 69 rules plus 48 more LocalRules, completing the grid: look-ahead 400, 700, 1,000, 1,500 m; threshold 7, 10, 13, 16, 19 m/s; slow-traffic headway 1.6, 1.2, 1.0 s | lowest median delay, collisions at most p333's + 1, no close-following bound (planb.md:232); top 5 re-run on check seeds |
| 3E-D_X1 | planb.md §3.3 unchanged: 100 generations, no early stop, start p333 | incumbent on check seeds; plateau label (planb.md:238) |
| ASCH-delay | planb.md §3.4; steady member p333; library lr1000_10_1, lr1000_16_2, os0_10_10, the grid pick, 3E-D_X1; 18 settings each, plus never switch | lowest median paired delay against p333; top 5 re-run on check seeds |
| No control | every table, never deciding | |

- **Deciding set:** up to 18 non-learning arms; duplicates run once.
- **Not run, disclosed:** MPC-F (optional, CLAUDE.md; −1.24 % against p333 in TRUCK, critic_ranking_audit.md:36); a second search start (+$4.7).
- **Exposure:** tuned arms are tuned in X1 and know it. v3w is not retrained; its checkpoints were chosen on X1/X2 validation seeds (planb.md:188).

## 5. Measures
| Measure | Role | Reward |
|---|---|---|
| `all_delay` | deciding | tied (speed and flow terms, b_env.py:841-843, Plan B copy) |
| `ttc_net` against every arm and no control | labels a pass | reward term |
| `passed`, TTT, robust braking, moving full-emergency events, collisions | reported, 95 % | flow tied; braking a reward term; others outside |
| Location share against the closest arm (read6.py:487-499) | labels a pass | outside |
| `end_stop2`, `delay_ramp2`, delay by period, end backlog, last-10-minute flow, mainline delay to 1,440 s and 1,800 s | reported | outside |

## 6. Seeds proposed
The author must confirm; the ledger shows no use from 7,485,000.

| Seeds | One purpose |
|---|---|
| 7,485,300-309 | smoke, replay, determinism |
| 7,485,310-329; 330-349 | grid selection; grid check |
| 7,485,350-389; 390-429 | search pool; search check |
| 7,485,430-449; 450-469 | ASCH-delay tuning; check |
| 7,485,500-659 | verdict, n = 160, read once |
| 7,485,470-499; 660-699 | reserved |

## 7. KILL rules
**Statistic:** median over seeds of (arm − v3w) / median(arm) × 100 on `all_delay` (planb.md:424); percentile bootstrap, 20,000 resamples, rng 20261110.

**KILL R if, against any deciding arm,** the point is below 3.0 %, or the lower end of the two-sided 97.5 % interval is at or below 0; or if fewer than 4 of 5 learners have a positive point against every arm.

| Number | Record |
|---|---|
| 97.5 % = 1 − 0.05/2 | Bonferroni for two cells (planb.md:428); X2 left after its stored rows were read, so the level is not lowered |
| 3 % | about the smallest edge a Plan B-sized study confirms (planb.md:519); above the 2 % harm margin (planb.md:437). INFERENCE |
| every arm; 4 of 5 | an intersection, no further correction (planb.md:429); planb.md:438 |

**Pass labels, fixed now:**
- "PR-28-bound" if the location share exceeds 50 % (planb.md:143): no protocol until a rules-only lane-end check closes PR-28.
- "trade-off" if close-following against no control is more than 10 % worse with the 95 % upper bound below 0 (planb.md:141): the protocol carries the cost or adds a guard.
- "opponent below plateau" if 3E-D_X1 misses the plateau criterion: the protocol begins by continuing the search.

**Closed paths:** the threshold, n and the cell form are fixed at approval; no look at v3w rows before the verdict; no arm, seed or measure added after the run starts; crashed runs by planb.md:447; the label-swap null is checked before the reading (planb.md:486); at the cap the search stops at its next check, labelled so (planb.md:561).

**Author's alternative, two deciding cells:** §4's arms in X2 too; the same rule per cell at 97.5 %. A failed cell closes; R is KILLed only if both fail; a pass names its cell. Family-wise: with no edge in either cell, any pass has at most 2 × 1.25 % = 2.5 % chance. It needs V466 set aside and $7-8 more.

## 8. Null and power
Model: a new opponent is p333 shifted to the stated true edge; other stored rules stay.

| True edge, % | 0 | 1 | 2 | 3 | 3.5 | 4 |
|---|---|---|---|---|---|---|
| Pass, n = 160 | 0.0 % | 0.2 % | 5.1 % | 53 % | 80 % | 91 % |

- Label-swap null, one comparison, n = 160: "above 0" in 1.1 % (nominal 1.25 %); with the 3 % clause 0.05 %.
- It can pass and fail: stored rules alone pass in 94 % of resamples at n = 160; an arm cutting the edge to 2 % passes in 5 %.
- Smallest bound: the interval is about −1.5 / +1.4 points at n = 160; a true 4 % edge is KILLed 9 % of the time (14 % at n = 120, 4 % at n = 240).
- Limits: p333's paired SD (7.5 %) is kept; the lower bound is in count form (585 of 600 agree with the direct bootstrap).

## 9. Runs x rate = cost; machine-hours; build work; author time
| Step | Rows | Rate | Hours | Cost |
|---|---|---|---|---|
| Grid: 117 × 20 + 6 × 20 | 2,460 | $0.115-0.36 per 1,000 | 0.5-1.5 | $0.3-0.9 |
| 3E-D_X1 | 40,640 | 5,280 rows/h, $0.115 per 1,000 (V490) | 7.7 | $4.7 |
| ASCH-delay: 92 × 20 + 6 × 20 | 1,960 | as the grid | 0.4-1.2 | $0.2-0.7 |
| Verdict: 24 arms × 160, pack and field | 3,840 | 1,690 runs/h, $0.36 per 1,000 (V493) | 2.3 | $1.4 |
| **Total with 200 smoke runs and 6 % setup** | 49,100 | | 11.6-13.5 | **$7.0-8.2** |

- Build: 12-16 h (my estimate: two tuning scripts, a reader with planted-row tests, a driver).
- Author time: about 1.5 h.

## 10. Plant and verification effect
- No plant file change, no new headway value (so no new T0), CAV contract unchanged. PR-10 stays partial (plant_vv_record_v0.md:46); §2 item 4 adds an r2m3 line.
- New parameter values (LocalRule, scheduler library): a unit test each, and a smoke run whose rows carry them and show both headways commanded.
- X1 at 5,300 is inside the intended use (plant_vv_record_v0.md:9). Open: PR-28, PR-26, PR-08.

## 11. Cells added to the count (N = 91) and post hoc labels
0 cells; N stays 91 (a re-test adds 0, cells_tested.md:5). X1's fourth test (planb.md:159). A new study, post hoc.

## 12. Must-carry disclosures
- Post hoc; [A3] set aside; X1 chosen where DRL looked best (claim_review_round2.md:221).
- The queue never clears at 5,300 (V398): the percentage depends on the 1,800-s window.
- PR-28 open: against p333 the stored edge sits at merge 2 and follows lane-end stops.
- v3w has more close-following than no control in X1.
- Under the training family at nearby demand the edge is not shown (s01_result.md:558, :561).

## 13. Expected outcome and your probability (a judgement, labelled so)
KILL about 50 %; pass labelled "PR-28-bound" and "trade-off" about 43 %; a pass that lets a protocol start at once about 7 %. INFERENCE: closing PR-28 before this screen would spare the $7 if the lane-end check fails.
