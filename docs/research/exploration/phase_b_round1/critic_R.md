# critic_R: attack on direction R and screen R (memo §1.1 H1, §3 D5, §5.3)

Abbreviations: tt2 = `round2/report/test_table.csv`; r1, r2 = `results/round_1_result.md`, `round_2_result.md`; s01 = `results/s01_result.md`; pb = `protocols/planb.md`; c3 = `protocols/confirmatory_3.md`; ct = `planb/cells_tested.md` (Plan B worktree); cr = `docs/thesis/claim_review_round2.md`; vv = `docs/testing/plant_vv_record_v0.md`.
EXPL = my computation from stored rows `v5b1_runs/measure_s01_remote/rows_test.jsonl` (seeds 7,440,840-879, already read for a verdict; 10,000 resamples, RNG 20261110; scripts `critic_R_x.py`, `critic_R_y.py` beside this file). It reproduces the recorded points; bounds differ by 0.1-0.2.

## Findings

**F1. BLOCKER. Screen R runs what three records forbid, and delay is not a new measure there.**
- [A3]: "A cell counts as won by the tuned reading or by a delay win. If no primary cell is won, this DRL line closes on these slowdowns: no further training, tuning, plant change or seed round" (c3:132). The delay win was one of its two routes, read each time and never met: confirmatory 3 X2 1 of 5 (V395), 3b 0 (V401), round 1 0 of 5 in both cells (r1:212), round 2 v3w 2 of 5 per cell (r2:225); "No delay-win sentence exists for v3w" (r2:282).
- Plan B's reading: "[A3]'s 'tuning' is not limited to DRL, so no rule is re-tuned there either" (pb:160). V466 closes X2. pb:576: a later cell is "a new study, labelled post hoc".
- V456(3): a disturbance "is fixed before control results". R picks its cells because of control results.
- INFERENCE: no record allows reopening for another measure, and this is the same measure. R needs an author V# overriding c3:132, V466 and pb:160, labelled post hoc.

**F2. MAJOR. The evidence base is one seed block counted twice, at the top of a varying series.**
- Verified, paired on 40 seeds, signs right: X1 +5.5 [+2.9, +8.0], X2 +6.1 [+3.4, +7.4] (tt2, 95 %, uncorrected). pb:304's "+5.0 to +11.6 %" and "13 of 14" match s01 §6.1-6.2.
- The memo's two "Against" bullets are the same rows: the S0 map is "deterministic re-runs with the measurement pack, no new seed" (ct A27); s01:436, :460 repeat tt2.
- Other reads of delay against p333: confirmatory 2 "+5.3, +0.6, +4.9, CIs including 0" (V359); V368 "delay about equal throughout"; 3b "−6.5 to +0.4 %" (V401, baseline-v3); round 1 test X1 +2.6 [−1.8, +5.4], X2 +3.7 [+1.7, +5.0] (r1:211).
- Under the training family at nearby demand it is not shown: 5,250 +1.3 [−8.9, +7.5], 5,500 −1.4 [−6.6, +2.8] (s01:558, :561, 20 seeds).
- EXPL: in X2 the arm (+6.1) exceeds every learner (3.6-5.7, mean 4.65). X1: 2.6-9.1, mean 5.24.
- X1's two events "never occur in training" (ct A7); both cells sit at the family's severe corner (25 km/h; 180 s).

**F3. MAJOR. X2 already meets R's KILL condition on stored rows, against a rule absent from R's arm list.**
- EXPL at the screen's 97.5 %: against lr1000_10_1 +4.1 [−0.4, +5.8]; os0_10_10 +2.4 [−0.9, +7.6]; 3E-X2 +3.0 [+0.4, +5.8]. Recorded: lr1000_10_1 has the lower median (226,204 against 226,353; s01:522); 3E-X2 at 99.17 % +3.0 [−0.1, +6.4] (r2:206).
- X1 is the only live cell: smallest stored margin +5.0 [+2.8, +8.9] against lr1000_10_1 (EXPL 97.5 %; recorded 95 % [+3.0, +8.8], s01:443).
- So "in both cells" means X1 alone decides, and the X2 search (about $4.5) buys nothing.

**F4. MAJOR. 3E-D from p333 is not shown to be the strongest delay opponent.**
- TRUCK order on delay (V496; `phase_a_reports/rows/recorded_table_out.txt`): os0_10_10, a carried grid rule, −0.58 % [−0.93, +0.20]; p333 and lr1000_10_1 −0.25 [−0.83, +0.50]; 3E-D third, +0.08 [−0.57, +0.90]; ASCH (= lr1000_16_2) +0.27; MPC-F +1.09 [+0.56, +1.76].
- "Ended at p333" is loose. The incumbent is another rule (g054i16, generation 60) whose check loss of −1.48 % became +0.01 % [−0.45, +0.25] on fresh seeds (`planb_s34_remote/cmab/TRUCK_delay/pick.json`; search rows, not evidence). INFERENCE: "met the plateau criterion" does not separate "optimal" from "cannot resolve 1-2 % on 16 seeds".
- The family has no look-ahead (pb:215, :223). The delay leaders by median in the slowdown cells are look-ahead rules: lr1000_16_2 (X1), lr1000_10_1 (X2) (s01:521). R lists no LocalRule.
- The opponent matched to "recovery" is a two-regime scheduler with a delay library; Plan B's ASCH switched only among close-following rule sets (pb:258).

**F5. MAJOR. The edge is a discharge difference in a queue that does not clear, at the unvalidated merge.**
- "The queue never clears at 5,300 in any arm (last 10 minutes 80-82 veh/min, backlog at 1,800 s 430-530)" (V398). EXPL: 74-80 % of planned vehicles finish in every arm. Flow edge +1.0 [+0.7, +1.6] and +1.4 [+0.9, +1.8] (tt2).
- EXPL proxy (mean delay of ramp vehicles), against p333: ramp 2 +12.3 [+7.1, +19.8] (X1), +20.7 [+10.4, +24.0] (X2); ramp 1 +2.7, +2.3. Against 3E-X2, ramp 2 is −9.2 [−14.8, −3.4]. These rows have no road-delay keys, so pb:143's share cannot be computed.
- PR-28 is a gap: "ramp 2 has 608.5 lane-end stops per run against 7 at ramp 1" (vv:79), first to close (vv:96).
- INFERENCE: 5 % of delay here is about 1 % more discharge through merge 2 inside a truncated window. Checklist items due first (ledger_early §b): "Merge model is not the result"; "Drain and window"; "pre-queue flow not demand-limited"; lane-end crawl (V291).

**F6. MAJOR. A delay win in X1 does not stand alone.**
- "No sentence claims a win on one measure alone" (pb:153).
- Against no control in X1: close-following −16.6 [−25.1, −8.4], TTC<2 s −27.1, TTC<1.5 s −27.4 (r2:265, :323); b3 −13.2 [−15.6, −9.6], b45 −28.8 [−32.4, −17.8] (s01:453). V459's harm half fires.
- "A W against the rules beside 'not met' against no control is a trade-off, not a net win" (cr:197).
- Correction to memo §1.1 H2: moving full-emergency events are 15 of 200 learner-runs in X1 and 24 of 200 in X2, not both in X1; p333 has 3 of 40 in X1 (r1:202-206).

**F7. MINOR. Power, seeds, cost.**
- V435's "60 seeds" is non-inferiority at a 5 % margin and a 95 % bound; 80 at 97.5 %; about 160 at 3 %.
- EXPL: paired SD of the arm difference 6.3-9.7 %. My normal approximation, n = 60, 97.5 %: half-width 2.3-3.5 points; a true 3 % edge survives a cell about half the time, a true 5 % edge 0.8-0.95, a true 0 under 1 %. The false-pass risk is a weak opponent (F4), not noise.
- The memo's "check" seeds serve incumbent selection and the reading. Plan B kept them apart (pb:239); TRUCK's incumbent lost 1.5 points from check to fresh seeds, so sharing biases towards KILL.
- Costs hold for what is listed: 81,280 rows (V488) at 5,278-5,500 rows/h, $0.605/h (V490, V493): about 15 h, $9.0-9.3; 1,560 check runs $0.2-0.8. F4's opponents add a 69-rule grid on 20 seeds (1,380 runs), 10 carried rules and an ASCH tune (1,760 rows in Plan B, V490).

## Changes to the screen text

1. Open with: "Needs a V# setting aside c3:132 (X1), V466 (X2) and pb:160, post hoc. X1's fourth and X2's fifth test on plant_c3; the count stays 91."
2. Decide on X1 only. X2: carried rules on the same fresh seeds, report-only, no search.
3. Opponents in X1: all 15 carried rules; the grid's lowest-delay pick with no close-following bound; 3E-D from p333 and from that pick; ASCH with a delay library. MPC-F optional, disclosed.
4. Three disjoint seed sets: pool 40, search check 40, evaluation 80.
5. KILL: "against any non-learning arm, the arm's delay advantage has a point below 3 % or a 97.5 % lower bound at or below 0; or fewer than 4 of 5 learners have a positive point against every arm; or the point falls below 3 % on a window extended to 3,000 s."
6. Road-delay keys on; pb:143's share reported. Above 50 %: "survives, PR-28 open", and no protocol until a rules-only lane-end check passes.
7. Report-only generality row: fresh draws from a pre-declared severe sub-family (one new cell, N = 92, a new study by pb:576).
8. Must-carry: F6's no-control figures in the same sentence.

## Verdict

R is not worth its cost as drafted: it tests a closed route, omits the cells' delay leaders, and spends half its budget on a cell already at the KILL line. Amended and X1-only it costs about $6 with one 3E-D start and about $10-11 with two (my arithmetic from V490's rates), and is defensible only after the author's override. Run it after M and F stage 1, or not at all.

My probability (judgement, not measured): the amended screen survives in X1 about 30 %; X2 under 5 %; a sentence usable in the thesis after PR-28, the window check and the no-control trade-off about 5-10 %, below the memo's 15-25 %.
