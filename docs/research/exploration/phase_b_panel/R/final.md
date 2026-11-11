# Screen R, slowdown recovery: final text

## PART 1. Protocol-ready screen

Stored-row numbers are EXPLORATORY. "edge" = `phase_b_round1/an_x1x2_delay_edge.md`; "check" = my recomputation, `panel/R/final_work/`; code lines: `planb_v23`.

## 1. Question; what a pass allows; what a KILL closes
- **Question.** In X1 at 5,300 veh/h, is frozen v3w's delay at least 3 % below every non-learning arm tuned for delay there? Does the gap arise in traffic or at the unvalidated merge-2 lane end (PR-28)?
- **A pass** without the label "PR-28-bound" allows a DRL protocol; with it, only a rules-only PR-28 item. Never a claim or a delay-only sentence (planb.md:153).
- **A KILL** closes the delay route on these slowdowns; [A3] stands.

## 2. Approvals and preconditions
1. **Author decision (new V#), post hoc** (planb.md:576; V456(3)), X1 only. It sets aside [A3], "no further training, tuning, plant change or seed round" (confirmatory_3.md:132; V395), and "no rule is re-tuned there either" (planb.md:160). V466 (X2) stands. Delay was already one of [A3]'s two win routes; this is X1's fourth test (planb.md:159).
2. **A weaker bar, post hoc:** 3 % at arm level, the memo's number, without a record (drl_win_directions_v0.md:311). The recorded delay win needs 5 % for 4 of 5 policies (confirmatory_3.md:108) and read 0 and 2 of 5 (round_1_result.md:212; round_2_result.md:225). Stored rows pass 3 % in 93-98 % of resamples and 5 % in 1-2 % (check). Without this decision R closes at stage 0.
3. **Order:** R before the rules-only PR-28 item (default) or after it (plant_vv_record_v0.md:96).
4. Own cap ($12 proposed, inside the $40 per 7 days; stop rule of planb.md:561), rental, seeds.
5. **Before any v3w verdict row, or the screen stops:** identity, determinism and pack checks (planb.md:388-393); PR-13 (plant_vv_record_v0.md:49); PR-10's T0 record (§10); p333 at least 10 % below no control on delay (planb.md:406).

## 3. Stage 0: statements from stored rows (zero runs)
- X2 stays closed by V466 and is not run. Stored: +1.9 % [+0.1, +4.3] (97.5 %) over os0_10_10 (edge:8).
- X1: +4.2 % [+2.4, +5.9] (97.5 %; 120 seeds in three sets, and the S0/S1 map repeats one, edge:20) over p333, the nearest stored rule (edge:7, :44). Open: no delay search exists there (edge:10).
- Nearly decided: a pass is expected to be "PR-28-bound". Location shares (my proxy of planb.md:143, 40 seeds): p333 0.62, lr1000_10_1 0.58, os0_10_10 0.04. §7's label fires in 99-100 % of resamples; read against the closest arm alone, in 77-79 % (check).
- "Trade-off" is expected: 16.6 % [8.4, 25.1] more close-following than no control (95 %; round_2_result.md:265).

## 4. Arms
Tuned arms are picked in X1, on their own seeds, by median paired delay against p333; admission as 3E-D (planb.md:228, :232). **Deciding arms:** every non-learning arm but no control, which is in every table (planb.md:448): 13 at stage 1, 26 at the end; duplicates count once (planb.md:213).

| Arm | Definition | Stage |
|---|---|---|
| v3w | 5 frozen learners, evaluation mode, per-seed mean (planb.md:188, :195) | 1 |
| Carried rules (15; planb.md:203) | p333, lr1000_10_1, os0_10_10, lr1000_16_2; the other 11 at stage 2 | 1, 2 |
| Grid picks (5) | lr1000_13_1, z31333 (from the stored grid re-ranked on delay, `work/cheap_grid_repick.out`); the best 3 of 20 new LocalRules: look-ahead 1,600 or 2,000 m with threshold 10, 13 or 16 m/s; 400 or 1,000 m with 7 or 20 m/s; each at 1.2 and 1.0 s | 1 |
| Merge-2 hybrid | ZoneOwnState (b_env.py:1117-1129): os0_10_10's setting (conf3/common.py:39) in the merge-2 zone, p333 elsewhere | 1 |
| Near-gap picks (best 3 of 12; new class) | a mainline CAV (all lanes, or the adjacent one) asks for 1.6 or 1.2 s, else 0.8 s, while the nearest acceleration-lane vehicle is strictly nearer than 25, 50 or 75 m (column 14, b_env.py:923-935; unread by the searched family, :1128), at both merges (:912-914). One level step per 10-s hold (b_env.py:703-711; conf3/common.py:12): 1.6 s needs 20 s of trigger | 1 |
| 3E-D_X1 | planb.md §3.3 unchanged; CMA seed 20261118 + 2; start: the hybrid if it has less delay than p333 on the selection seeds, else p333; plateau label (planb.md:238) | 2 |
| ASCH-delay | planb.md §3.4's scheduler, 18 settings; undisturbed rule p333; disturbed rule from lr1000_10_1, lr1000_16_2, os0_10_10, the hybrid, the best LocalRule, 3E-D_X1; or never switch | 2 |

**Exposure.** v3w is not retrained; its checkpoints were chosen on X1/X2 validation seeds (planb.md:188). Tuned arms know the cell, read up to 2,000 m ahead and get a 40,640-row search (V490).

## 5. Measures
| Measure | Role | Reward |
|---|---|---|
| `all_delay`, arm and per learner | deciding | tied: speed and flow terms (b_env.py:841-843) |
| Location share (read6.py:487-499), `end_stop2` | label | outside |
| `ttc_net` against arms and no control | label | a term |
| `delay_ramp2`, delay by period, `passed`, TTT, hard braking, collisions, moving full-emergency events; delay and backlog to 3,000 s | report-only | flow, braking: terms; rest outside |

## 6. Seeds proposed
No ledger use from 7,485,000; the F and M drafts run inside 7,485,000-879. R proposes 7,486,000-439; the author must confirm.

| Seeds (7,486,…) | One purpose |
|---|---|
| 000-009 | smoke, determinism, near-gap and look-ahead binding |
| 010-029 | PR-10 and PR-13 records |
| 030-079 | selection of stage-1 picks and the search start |
| 080-119; 120-159 | 3E-D pool; check |
| 160-179; 180-199 | ASCH-delay tuning; check of its top 5 |
| 200-439 | verdict, n = 240; after the final read, v3w and the three closest arms run on to 3,000 s on 200-239, report-only |

## 7. KILL rules
Statistic: median of paired differences over the arm's median, percentile bootstrap (planb.md:424). Picks and stage-2 settings are frozen before any verdict row.
- **K1.** KILL if, against any deciding arm, the point is below 3.0 % or the 97.5 % lower bound is at or below 0.
- **K2.** KILL if fewer than 4 of 5 learners have a positive point against every deciding arm (planb.md:438).
- **Reads:** KILL-only after stage 1, then final, on the same rows.
- **97.5 % = 1 − 0.05/2:** Bonferroni for two cells (correction 4; planb.md:428); m stays 2 although X2 left after its stored rows were read. Arms form an intersection (planb.md:429).
- **3.0 %:** no record (§2). It is a minimum over 26 arms: 5 to 12 tied arms pass in 80 % only from a true edge of about 4.0 to 4.2 % (§8).

Pass labels, fixed now:
- **"PR-28-bound":** against any deciding arm within 1.5 points of the closest (a judgement), the location share is above 50 % (planb.md:143) or its `end_stop2` is shown higher than v3w's (95 %).
- **"trade-off":** close-following over 10 % worse by point, 95 % upper bound below 0 (uncorrected, planb.md:430), against no control (planb.md:141) or any deciding arm (planb.md:437). The protocol carries the cost or adds a guard.
- **"screen incomplete":** 3E-D_X1 misses the plateau criterion or stops at the cap. No protocol; a longer search needs a new approval.

**Author's alternative, two deciding cells** (V466 set aside too; about $13-19). X2 gets the same arms. Each cell is read alone at 97.5 % and closes on its own; R is KILLed only if both close; a pass names its cell. Family-wise: with no edge in either cell, at most 2 × 1.25 % = 2.5 % of studies show a lower bound above 0.

## 8. Null and power
EXPLORATORY (check; `skeptic_work/sk1.out` agrees at n = 160). 120 stored X1 seeds resampled to n = 240; the k nearest stored rules shifted to one true edge. Pass chance, %:

| k tied arms | 3 % | 3.5 % | 4 % | 4.24 % (stored) | 5 % |
|---|---|---|---|---|---|
| 1 | 54 | 85 | 96 | 98 | 100 |
| 5 | 9 | 46 | 83 | 94 | 100 |
| 12 | 2 | 22 | 69 | 81 | 97 |

- It can fail and pass: 0 % at a true edge of 0; 97.5 % as stored.
- At p333's stored edge, 5 to 12 tied arms KILL in 6-19 % with no opponent gain (16-43 % at n = 160).
- Label-swap null, one comparison: a lower bound above 0 in 1.1 % (nominal 1.25 %); re-checked before each read (planb.md:486).
- Interval about −1.3 / +1.1 points: a KILL by a point just under 3 % leaves edges up to about 4.1 % unexcluded (INFERENCE).
- Selection on 50 seeds: a setting truly 2 % below p333 is among the best 3 of 11 in 76 % (60 % on 20).
- The labels have no null; they only restrict a pass.

## 9. Runs x rate = cost; machine-hours; build work in hours; author time, stated apart
| Step | Runs or rows | Hours | Cost |
|---|---|---|---|
| Stage 1: checks 150 (planb.md:384's 130 plus near-gap smoke), T0 40, selection 34 × 50, verdict 19 × 240 | 6,450 | 2.1-3.8 | $0.6-2.3 |
| Stage 2: 3E-D_X1 40,640 rows (5,280 rows/h, $0.115 per 1,000; V490); ASCH-delay 110 × 20 + 6 × 20; verdict 13 × 240; 8 × 40 runs to 3,000 s (each costed as 1.67) | 46,400 | 9.7-11.2 | $5.3-6.8 |
| **All, with 6 % setup (V475)** | 52,850 | 12.5-16 | **$6.3-9.7** |

- Evaluation: $0.36 per 1,000 runs with the full pack and field (1,690 runs/h on 90 workers at $0.607/h; correction 7, V493), down to $0.10-0.13 (V475). A stage-1 KILL costs $0.7-2.5. Rate check as planb.md:563.
- Build, my estimate, 16-20 h with a code review: near-gap class and `run_one` key (plant_sweep.py:86-95); X1 search cell, seed constants, CMA seed, five-zone start (cmab.py:40-47, :93-99); scheduler selection on delay; 3,000-s job (rerun.py:87 is X2 only); reader. Author time, apart: about 2 h.

## 10. Plant and verification effect
- No plant file change; no new actuator value (b_env.py:37); the CAV contract holds; X1 at 5,300 is inside the intended use (plant_vv_record_v0.md:9).
- T0 is PR-10's missing r2m3 record (plant_vv_record_v0.md:46): uniform 1.6 s against 0.8 s, 20 seeds; `tau_on_match`/`tau_on_n` = 1 in every row (plant_sweep.py:225-227); `passed` and `mean_v` differ (95 %).
- Smoke checks carry the new values: look-aheads of 8 and 10 200-m bins (b_env.py:58, :998); near-gap, per setting and merge: the share of decisions with the trigger held and the share of triggered spells reaching the target level. Under 50 % on the second (a judgement), a setting is labelled "did not reach its target". It stays eligible: removing it could only weaken the opponents.

## 11. Cells added to the count (N = 91) and post hoc labels
0 cells: a re-test of counted cell X1 at 5,300 (cells_tested.md:5, :30); N stays 91 (V487). Post hoc: the screen, the deciding cell, 3 %, the hybrid, the near-gap rule, the label's reading.

## 12. Must-carry disclosures
- §2's decisions, with both bars and stored pass rates; X1 picked where DRL looked best, tested three times before (claim_review_round2.md:221); K1 a minimum over 26 arms (§8).
- Against no control: more hard braking (s01_result.md:453). Moving full-emergency events: 15 of 200 learner-runs in X1, 24 of 200 in X2 (round_1_result.md:202).
- X2's queue never clears (V398); X1's drain is unchecked (rerun.py:87); 28 % of the mainline edge over p333 accrues in 1,440-1,800 s (edge:68). The edge is also given in vehicle-seconds, vehicles served and to 3,000 s.
- X1's events never occur in training (cells_tested.md:29); no edge under the training family at nearby demand (s01_result.md:558, :561).
- One search start; ASCH-delay picked on 20 + 20 seeds; MPC-F (optional, CLAUDE.md) and X2 not run; PR-28, PR-26, PR-08 open.

## 13. Expected outcome and your probability (a judgement, labelled so)
My judgement, not measured. KILL about 55 % (35 % at stage 1, 20 % at stage 2); 3 to 19 points of it need no opponent gain (§8). Pass with "PR-28-bound" about 43 %. Pass that allows a DRL protocol: under 2 %. Expected spend about $6.

## PART 2. Skeptics' findings and handling

"check" = `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/final_work/` (`load.py`, `check1.py` to `check5.py`: my own code, not the skeptics'). Every number from it is EXPLORATORY: 120 stored X1 seeds, already read for verdicts; check2 uses the 40 seeds of the round-1 road split (`phaseB/x1x2/b1.pkl`).

Length: Part 1 has about 1,470 words. With bare numbers counted as words it has about 1,760 (the panel's count, by which synth.md had 1,506), above the 1,500 limit. The excess is the text the nine findings required; each remaining line carries a template item or a finding's change, so I cut no further.

| Id | Severity | Finding | Verified | Handling |
|---|---|---|---|---|
| R-all-1 | blocker | §8 gave the power of one comparison; K1 is a minimum over 24 deciding arms, so it can KILL by noise | Yes. check1 B at n = 160: k = 1 / 3 / 5 / 12 pass 52 / 22 / 10 / 1 % at a true edge of 3 %, 91 / 84 / 71 / 45 % at 4 %; 84 % and 57 % at 4.24 % for k = 5 and 12. Within 1 point of sk1.out B. The arm count is 26 after R-all-5 | §8's table is by k. §7 states the 80 % line. §12 carries it. §13 splits the KILL chance. Added by me: n raised from 160 to 240 (check4: noise KILL at the stored edge 6-19 % in place of 16-43 %), for 2,560 more runs, about $0.3-1.0; the cap proposal moves from $10 to $12 |
| R-all-2 | major | The 3 % bar was chosen after the numbers it tests; planb.md:519 is not its record | Yes. planb.md:519 is the 80 %-power effect of the W rule at n = 120, m = 3. Memo line 311 cites nothing. check1 C: as stored, the 3 % bar passes 93 % and a 5 % arm-level bar 2 % (97.5 % and 1 % at n = 240, check5) | §2 item 2 gives both bars and both rates; §7 says 3.0 % has no record. The planb.md:519 sentence is deleted. The choice is the author's |
| R-all-3 | major | "PR-28-bound" is read against the closest arm on verdict rows, so chance steers it | Yes. check1 C: closest is p333 59 %, lr1000_10_1 21 %, os0_10_10 20 %. check2 (40 seeds): shares 0.62, 0.58, 0.04; the closest-arm reading fires in 77-79 %, the revised reading in 99-100 % | §7 reads the label against every deciding arm within 1.5 points of the closest. §3 gives the shares and both rates. §1, §3 and §13 state the consequence: a pass is expected to carry the label |
| R-all-4 | major | §1 ("a pass allows a protocol") contradicts §7 (a PR-28-bound pass allows none) | Yes, by reading synth.md §1 and §7; plant_vv_record_v0.md:96 puts PR-28 at the head of the gap list | §1 rewritten. §2 item 3 adds the author's choice of order. §13 gives the chance of a pass that allows a DRL protocol (under 2 %, my judgement) |
| R-all-5 | major | Selection on 20 seeds picks by noise, which favours a pass | Yes. check1 E: a setting truly 2 % below p333 is picked as best of 11 in 28 % on 20 seeds and 41 % on 50; among the best 3 in 60 % and 76 %. `work/cheap_grid_repick.out`: os0_10_10 +1.3 % [−2.5, +4.1] on 20 seeds; edge:44: −2.4 % [−3.7, −0.5] on 120 | Selection on 50 seeds (7,486,030-079). The best 3 near-gap settings are carried. §8 gives the pick accuracy. §12 notes ASCH-delay's 20 + 20 seeds, kept as planb.md §3.4 |
| R-all-6a | major | A level moves one step per 10-s hold, so the near-gap arm cannot reach 1.6 s at once | Yes. b_env.py:703-711 (one step, hold); conf3/common.py:12, :47 (hold 10 s); b_env.py:781-782 and plant_c3.json (`tau_rise` 0.2 s per s) | §4 states the mechanics. §10 fixes the two binding shares and the 50 % line. Partly rejected: a setting under 50 % is labelled, not removed, because removal can only weaken the opponent set. Open item 6 |
| R-all-6b | major | Column 14 pools both acceleration lanes, so the rule also acts at merge 1 | Yes. b_env.py:912-914, :923-924 | §4 says so and keeps it: v3w reads the same column at both merges. §10 reports the trigger share per merge |
| R-all-7 | major | The queue never clears and the edge still accrues late; the synthesis dropped the 3,000-s window | Yes. V398 is an X2 record (rerun.py:87); edge:68 (28 % in 1,440-1,800 s) | A report-only row: v3w and the three closest arms on seeds 200-239 to 3,000 s, 320 runs, after the final read (§5, §6, §9, §12). Not a KILL clause: no stored X1 rows give its variance |
| R-all-8a | minor | Build items missing: seed constants, the near-gap key, X1's CMA seed, the 30-minute rate check | Yes. cmab.py:40, :42-43, :47, :93-99, :194; plant_sweep.py:86-95; planb.md:225, :563 | All in §9; the CMA seed is fixed in §4 (20261118 + 2, X1 as the third cell); build estimate raised to 16-20 h |
| R-all-8b | minor | The two-cell alternative costs more than the cap | Yes, by my arithmetic from §9: X2 adds about $6-10 | §7 states about $13-19 in all; open item 7 says the cap must follow |
| R-all-9a | minor | "Deciding arm" is not defined | Yes | §4 defines it: 13 at stage 1, 26 at the end; duplicates count once (planb.md:213) |
| R-all-9b | minor | Exploratory rows cannot fire K1; X2 stays closed by V466 | Yes: K1 is fixed now and those rows were already read | §3 reworded as proposed |
| R-all-9c | minor | "Trade-off" should also read the harm rule against each arm | Yes. planb.md:437. check3: on stored rows it fires against no control only (−19.7 % [−23.7, −15.2]); v3w is +19 to +44 % against each stored rule | §7's label reads no control and every deciding arm |
| R-all-9d | minor | A pass with the search below plateau is "screen incomplete" | Yes: the question asks for the strongest delay opponent; planb.md:238 | §7's third label renamed; it allows no protocol; a longer search needs a new approval |

Also changed, for consistency or length: "HYB" is written out as "merge-2 hybrid"; the seeds are re-laid in one block; the stored grid re-rank moved from §3 into §4's grid row; the hybrid's separate `end_stop2` line is dropped, because §5 reports `end_stop2` for every arm. Checked and kept from the skeptics' "found right" list: the one-arm row (now k = 1), the rates (V475, V490, V493), disjoint seeds, the closure records, N = 91, corrections 4 and 7.

### Open for the author
1. **Closure.** Set aside [A3] (confirmatory_3.md:132; V395) and planb.md:160 for X1, post hoc. Default: X1 only; V466 stands.
2. **The bar.** Default 3 % at arm level (no record; stored rows pass in 93-98 %). Alternative: the recorded 5 % (stored rows pass in 1-2 %), which closes R at stage 0.
3. **Order.** Default: R before the PR-28 item, because stage 1 costs $0.7-2.5 and can close the route. Alternative: the rules-only PR-28 item before R, because a pass of R is expected to be "PR-28-bound" either way.
4. **Seeds per verdict.** Default n = 240. With n = 160 the screen saves about $0.3-1.0, and the noise KILL at the stored edge is 16-43 % in place of 6-19 %.
5. **Arms against noise (R-all-1 against R-all-5).** More tied arms raise the noise KILL; fewer risk missing the strongest. Default: carry the 3 near-gap picks, 26 arms.
6. **Near-gap settings that do not reach their target.** Default: labelled and eligible. The skeptics proposed removing them.
7. **Cells.** Default: X1 decides. Alternative: two cells at 97.5 % each, about $13-19 with a cap to match, V466 set aside.
8. **Money and seeds.** Cap $12; rental; seeds 7,486,000-439, in one partition with F and M (one M draft names 7,486,000 for a later confirmation); whether Plan B's $16-17.5 (V493) counts in the same 7 days; the order of R, F and M under $40.
9. **Two judgement numbers** without a record: the label's 1.5-point window and the 50 % binding share.
