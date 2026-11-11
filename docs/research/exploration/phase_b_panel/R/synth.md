# Screen R, slowdown recovery: protocol-ready text

Stored-row numbers are EXPLORATORY. "edge" = `phase_b_round1/an_x1x2_delay_edge.md`; "power" = `panel/R/rigor_work/power.out`, `power2.out`; code lines: `planb_v23`.

## 1. Question; what a pass allows; what a KILL closes
- **Question.** In X1 at 5,300 veh/h, is frozen v3w's delay at least 3 % below every non-learning arm tuned for delay there? Does the gap arise in traffic or at the unvalidated merge-2 lane end?
- **A pass** allows a protocol under §7's labels; never a claim or a delay-only sentence (planb.md:153).
- **A KILL** closes the delay route on these slowdowns; [A3] stands.

## 2. Approvals and preconditions
1. **Author decision (new V#), post hoc** (planb.md:576; V456(3)), X1 only. It sets aside [A3], "no further training, tuning, plant change or seed round" (confirmatory_3.md:132; V395), and "no rule is re-tuned there either" (planb.md:160). V466 (X2) stands. Delay was already one of [A3]'s two win routes; this is X1's fourth test (planb.md:159).
2. **A weaker bar, post hoc:** 3 % at arm level. The recorded delay win needs 5 % for 4 of 5 policies (confirmatory_3.md:108). It read 0 and 2 of 5 (round_1_result.md:212; round_2_result.md:225); pooled stored rows give 1 of 5 (edge:80). Without this decision R closes at stage 0.
3. Own cap ($10 proposed; at the cap the search stops at its next check, planb.md:561), rental, seeds; whether Plan B's $16-17.5 (V493) counts in the same $40 per 7 days.
4. **Checks before any v3w verdict row is read; a failure stops the screen:** identity, determinism, pack on equals pack off (planb.md:388-393); PR-13 (`pert_log`; plant_vv_record_v0.md:49); PR-10's T0 record (§10); p333 at least 10 % below no control on delay (planb.md:406).

## 3. Stage 0: statements from stored rows (zero runs)
- X2: +1.9 % [+0.1, +4.3] (97.5 %) over os0_10_10 (edge:8). K1 fires; X2 is not run.
- X1: +4.2 % [+2.4, +5.9] (97.5 %, 120 seeds) over p333, the nearest stored rule (edge:7, :44). Open: no delay search exists there (edge:10).
- Confirmatory 3's 69-rule grid, re-ranked on delay (`conf3/tune.jsonl`, recomputed): none shown below p333; positive points only os0_10_10, lr1000_13_1, z31333. No grid re-run.
- Over p333, 60 % of the edge is on road 4a; it is +0.5 % in the half of seeds with fewer lane-end stops (edge:59, :74). "PR-28-bound" is expected.
- v3w has 16.6 % [8.4, 25.1] more close-following than no control (95 %; round_2_result.md:265). "Trade-off" is expected.

## 4. Arms
Tuned arms are picked in X1 on their own seeds by median paired delay against p333; admission as 3E-D, no close-following bound (planb.md:228, :232). No control stands in every table and never decides (planb.md:448).

| Arm | Definition | Stage |
|---|---|---|
| v3w | 5 frozen learners, evaluation mode, per-seed mean (planb.md:188, :195) | 1 |
| Carried rules (15; planb.md:203) | p333, lr1000_10_1, os0_10_10, lr1000_16_2; the other 11 at stage 2 (10 have stored edges of +5.5 to +14.1 %; edge:29, :32) | 1, 2 |
| Grid picks (5) | lr1000_13_1, z31333; the best 3 of 20 new LocalRules: look-ahead 1,600 or 2,000 m with threshold 10, 13 or 16 m/s; 400 or 1,000 m with 7 or 20 m/s; each at 1.2 and 1.0 s | 1 |
| Merge-2 hybrid (HYB), fixed now | ZoneOwnState (b_env.py:1117-1129): os0_10_10's setting (conf3/common.py:39) in the merge-2 zone, p333 elsewhere | 1 |
| Near-gap pick (best of 12; new class) | a mainline CAV takes 1.6 or 1.2 s, else 0.8 s, while the nearest acceleration-lane vehicle is strictly nearer than 25, 50 or 75 m (observation column 14, b_env.py:935; unread by the searched family, b_env.py:1128); all mainline lanes or the adjacent one | 1 |
| 3E-D_X1 | planb.md §3.3 unchanged; start: HYB if it has less delay than p333 on the selection seeds, else p333; plateau label (planb.md:238) | 2 |
| ASCH-delay | planb.md §3.4's scheduler, 18 settings; undisturbed rule p333; disturbed rule from lr1000_10_1, lr1000_16_2, os0_10_10, HYB, the best LocalRule, 3E-D_X1; or never switch | 2 |

**Equal exposure.** v3w is not retrained; its checkpoints were chosen on X1/X2 validation seeds (planb.md:188). Tuned arms know the cell and read up to 2,000 m ahead; the search gets 40,640 rows (V490).

## 5. Measures
| Measure | Role | Reward |
|---|---|---|
| `all_delay`, arm and per learner | deciding | tied: speed and flow terms (b_env.py:841-843) |
| Location share against the closest delay arm (read6.py:487-499); `end_stop2` | label | outside |
| `ttc_net` against arms and no control | label | a term |
| `delay_ramp2`, delay by period, `passed`, TTT, hard braking, collisions, moving full-emergency events | report-only | flow, braking: terms; rest outside |

## 6. Seeds proposed
No ledger use from 7,485,000. The F and M drafts reach 7,485,799, so R proposes 7,486,000-399; the author must confirm.

| Seeds (7,486,…) | One purpose |
|---|---|
| 000-009 | smoke, determinism, near-gap binding |
| 010-029 | PR-10 and PR-13 records |
| 030-049 | selection of stage-1 picks and the search start |
| 050-089; 090-129 | 3E-D pool; check |
| 130-149; 150-169 | ASCH-delay tuning; check of its top 5 |
| 200-359 | verdict, n = 160 |

## 7. KILL rules
Statistic: median of paired differences over the arm's median (planb.md:424). Stage-1 picks and stage-2 settings are frozen before any verdict row; stage 2 never reads verdict rows.
- **K1.** KILL if, against any deciding arm, the point is below 3.0 % or the 97.5 % lower bound is at or below 0.
- **K2.** KILL if fewer than 4 of 5 learners have a positive point against every deciding arm (planb.md:438).
- **Reads:** KILL-only after stage 1, then final; a stage-1 KILL is also a final KILL.
- **97.5 % = 1 − 0.05/2:** Bonferroni for two cells (correction 4; planb.md:428); m stays 2 although X2 left after its stored rows were read. Arms form an intersection (planb.md:429).
- **3 %:** about the smallest edge a Plan B-sized study detects (planb.md:519). INFERENCE.

Pass labels, fixed now:
- **"PR-28-bound":** location share above 50 % (planb.md:143), or the closest arm's `end_stop2` shown higher than v3w's (95 %). R alone then allows no DRL protocol, only a rules-only PR-28 verification item, not designed here.
- **"trade-off":** close-following over 10 % worse than no control, 95 % upper bound below 0 (planb.md:141). The protocol carries the cost or adds a guard.
- **"opponent below plateau":** 3E-D_X1 misses the plateau criterion; the protocol continues the search.

**Author's alternative, two deciding cells.** X2 gets the same arms (V466 set aside too). Each cell is read alone at 97.5 % and closes on its own when K1 or K2 fires; R is KILLed only if both close; a pass names its cell. With no edge in either cell, at most 2 × 1.25 % = 2.5 % of studies show a lower bound above 0. About $6-8 more.

## 8. Null and power
EXPLORATORY (power): 120 stored X1 seeds resampled; a new opponent is p333 shifted to the true edge.

| True edge, % | 0 | 2 | 3 | 4 |
|---|---|---|---|---|
| Pass, n = 160 | 0.0 % | 5.1 % | 53 % | 91 % |

- Label-swap null: a lower bound above 0 in 1.1 % (nominal 1.25 %); re-checked before each read (planb.md:486).
- Stored rules alone pass in 94 % of resamples: it can fail and pass.
- Interval about −1.5 / +1.4 points: a KILL by a point just under 3 % leaves edges up to about 4.4 % unexcluded (INFERENCE).
- The labels have no computed null; they only restrict a pass.

## 9. Runs x rate = cost; machine-hours; build work in hours; author time, stated apart
| Step | Runs or rows | Hours | Cost |
|---|---|---|---|
| Stage 1: checks 130 (planb.md:384), T0 40, selection 34 × 20, verdict 17 × 160 | 3,570 | 1.2-2.1 | $0.4-1.3 |
| Stage 2: 3E-D_X1 40,640 rows (5,280 rows/h, $0.115 per 1,000; V490); ASCH-delay 110 × 20 + 6 × 20; verdict 13 × 160 | 45,040 | 8.8-10.3 | $5.2-6.3 |
| **All, with 6 % setup (V475)** | 48,610 | 11-13 | **$5.8-8.0** |

- Evaluation: $0.36 per 1,000 runs with the full pack and field (1,690 runs/h at $0.607/h; correction 7, V493), down to $0.10-0.13 (V475). A stage-1 KILL costs $0.4-1.4.
- Build, my estimate: 14-18 h with a code review (near-gap class; X1 as a search cell, cmab.py:40; a five-zone start, cmab.py:93-99; scheduler selection on delay). Author time, apart: about 2 h.

## 10. Plant and verification effect
- No plant file change; no new actuator value (b_env.py:37); the CAV contract holds.
- T0 is PR-10's missing r2m3 record (plant_vv_record_v0.md:46): uniform 1.6 s against 0.8 s, 20 seeds; `tau_on_match`/`tau_on_n` = 1 in every row (plant_sweep.py:225-227), as in 40 of 40 stored grid rows (recomputed); `passed` and `mean_v` differ (95 %).
- Smoke checks carry the new values: near-gap (per d, the share of 5-s decisions with the trigger held) and look-aheads of 8 and 10 200-m bins (b_env.py:58, :998).
- HYB manipulation check, report-only: `end_stop2` against p333's on the selection seeds.
- X1 at 5,300 is inside the intended use (plant_vv_record_v0.md:9).

## 11. Cells added to the count (N = 91) and post hoc labels
0 cells: a re-test of counted cell X1 at 5,300 (cells_tested.md:5, :30); N stays 91 (V487). Post hoc: the screen, the deciding cell, 3 %, HYB, the near-gap rule.

## 12. Must-carry disclosures
- §2's two decisions, the 5 % reading beside 3 %; X1 picked where DRL looked best, tested three times before (claim_review_round2.md:221).
- Against no control: more hard braking (s01_result.md:453). Moving full-emergency events: 15 of 200 learner-runs in X1, 24 of 200 in X2 (round_1_result.md:202).
- X2's queue never clears (V398); X1's drain is unchecked (rerun.py:87): the edge is also given in vehicle-seconds and vehicles served.
- X1's events never occur in training (cells_tested.md:29); no edge under the training family at nearby demand (s01_result.md:558, :561).
- One search start; MPC-F (optional, CLAUDE.md) and X2 not run; PR-28, PR-26, PR-08 open.

## 13. Expected outcome and your probability (a judgement, labelled so)
My judgement, not measured. KILL about 60 % (40 % at stage 1, 20 % at stage 2): the new arms act where 60 % of the stored edge sits. Labelled pass about 37 %; unlabelled about 3 %, since "trade-off" already holds on stored rows. Expected spend about $5.

## Synthesis notes
- Base: draft_rigor (rules judge), not draft_cheap (plant judge): neither judge found a fatal flaw in it; draft_cheap's staging, stage 0 and near-gap rule are grafted.
- The 11 far carried rules (rules judge: needed; plant judge: waste) run at stage 2 only: a pass faces all 15, a stage-1 KILL does not pay for them.
- HYB's `end_stop2` check is report-only (plant judge), not a gate (rules judge); the 3,000-s window (plant judge) goes to the later protocol: neither has a computed null.
- LocalRule grid: draft_opponent's 20 (plant judge) replace draft_rigor's 48, so the 700 and 1,500 m values (rules judge) are gone.
- Length: about 1,500 words before these notes, above the 1,400 limit; the excess is the grafts both judges asked for.
