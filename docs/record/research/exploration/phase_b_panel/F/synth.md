# Screen F, the frontier claim: protocol-ready text

Statistic: planb.md:424; positive = v3w better; intervals 97.5 % unless marked. Reading = `docs/research/baseline_v5/readings/read6_v23_supplement.json`. EXPLORATORY = from stored S6 rows, already read for a verdict. Code lines: the `planb_v23` copy. Scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/` (mine: `synth_work/`).

## 1. Question; what a pass allows; what a KILL closes

In TRUCK at 5,300 veh/h, does frozen v3w keep at least 10 % fewer close-following seconds than the ZoneOwnState rule, once that rule is re-picked (stage 1) and searched to 300 generations (stage 2), with delay within 1 % of every rule arm?
- Pass: a protocol may be written for one TRUCK-only trade-off sentence. Never a claim.
- KILL: closes F for v3w on this plant. No second seed round; no retraining to reopen it (critic_F.md:56).

## 2. Approvals and preconditions

Author decisions:
1. Reopen TRUCK, which Plan B read T and closed (V496; planb.md:575): a new study, post hoc (planb.md:576).
2. The claim form, against "No sentence claims a win on one measure alone" (planb.md:153). If refused, F closes at $0.
3. §4's set-aside and harness change; §6's seeds; §7's numbers and two choices.
4. A rental; caps of $3 (stage 1) and $12 (stage 2). At rent time, the last 7 days' rental spend plus the cap must stay within $40. The ledger shows at least $18.3 for 2026-11-08 to 11-10 (V475, V494, V499), and more before (V450).

Before any verdict row:
- stored S6 rows reproduce by value (V499); a repeated run is equal; planted-row tests (planb.md:243); a code review; PR-09 per new rule (planb.md:408);
- a T0 record for PR-10 ("partial: no r2m3 T0 record", plant_vv_record_v0.md:46): uniform 1.6, 1.2, 1.0 and 0.8 s on 2 seeds, `tau_mismatch` = 0 (plant_sweep.py:224), delay differing between 1.6 and 0.8 s.

## 3. Stage 0: statements from stored rows (zero runs)

EXPLORATORY.
- Steady traffic is decided, so the scope is TRUCK only. K1 fires against 3 rules (3E-C_TRUCK: +7.99 % [−11.71, +31.46]). K2 fires against 13 of 23 (reading, `S.map`), partly a pooled-arm effect (an_s6_independent_measures.md:12). At 480 seeds the edge interval would still span ±15.2 points.
- TRUCK passes §7 today: 3E-C +11.80 % [+4.97, +19.71]; lowest delay lower bound −0.93 %. These rows chose the hypothesis; they are not evidence.
- Outside the reward nothing adds a sentence (§5).

## 4. Arms

- **v3w:** 5 frozen learners, evaluation mode, never tuned in TRUCK (planb.md:188).
- **3E-C:** today's pick g098i00, the lowest of 54 check losses on 40 seeds: −32.53 % there, 21.18 % [14.77, 31.20] on S6's seeds (95 %; reading).
- **3E-C-R (stage 1; no new search):** the 8 lowest admissible stored check losses (`planb_s34_remote/cmab/TRUCK_ttc/checks.jsonl`) run with p333 on selection set A. The lowest loss admitted there wins (planb.md:227-228).
- **3E-C+ (stage 2; correction 1): the search continued, not restarted.** Generations 0-99 replay from the stored evaluations at 1e-9 (cmab.py:223-224; cma2.py:49) and must give g098i00. Generations 100-299 run under planb.md §3.3 unchanged, with the original pool, check set, CMA seed and loss. This is a harness change: cmab.py:204-205 refuses a changed generation count. Fixed budget; no data-dependent stop. The plateau label (check loss at 260 minus at 300 below 1.0, after planb.md:238) is reported only. The 8 lowest admissible check losses, g098i00, 3E-C-R and the final CMA mean run with p333 on selection set B. The lowest loss admitted wins, committed before its verdict rows.
- **Stored arms:** p333, os0_10_10, 3E-D_TRUCK (V491); no control, never deciding.
- **Exposure:** one run per arm and verdict seed. The rule gets 300 generations in the cell and answers every 5 s; v3w gets none and answers every 10 s (planb.md:215; V381(2)).
- **Set aside (planb.md:214, no counting filter):** the other 19 stored rules are not re-run (their lowest stored lower bound is +17.61 %, lr400_16_1). Re-running them costs 9,120 runs, about $3.3.
- **Not arms:** other hinges, decision trees, richer families (no form or budget on record, and a searched flexible rule is policy search; critic_F.md:46).

## 5. Measures

- **Deciding:** close-following, TTC < 3 s at 1 Hz (`ttc_net`), a reward term (b_env.py:812, :843); delay (`all_delay`), tied to the speed term (b_env.py:842).
- **Side conditions:** flow, collisions, moving full-emergency events, robust braking; reward terms or tied.
- **Report-only, tied:** `ttc15` (+37.47 % against 3E-C), `ttc2`, `sev3`; braking events at 4.5 m/s² or harder (−5.73 % [−8.28, −2.31], shown worse).
- **Report-only, outside (correction 5; 95 %, uncorrected; fuel and jerk EXPLORATORY).** Against p333: jam share +10.65 % [+0.02, +17.61], congested km mean −1.43 % [−3.04, −0.63] (reading; V501), fuel per km +0.2 % [+0.0, +0.3]. Against 3E-C: fuel +0.1 % [−0.1, +0.2]; oscillation +1.02 % [+0.55, +1.36]; congested km max +3.85 % [+1.54, +6.15]; jam share and acceleration RMS not shown different; shown worse on jam count, −8.57 % [−14.29, −4.29], and jerk, −0.5 % [−0.6, −0.3]. Against no control: fuel +0.6 %. TTT beside.
- **Validity (PR-28), report-only:** drain; the edge without lane-change samples; the edge off roads 4a, 4 and ramp 2 (stored +9.05 % [+4.50, +18.73]), whose lower bound, if at or below 0, goes into the sentence.
- The sentence names close-following only, as a reward term, and leads with every measure shown worse (planb.md:439); planb.md:153's barred words stay out. The 0.1-s meter lacks the named thresholds, never ran and is not read (critic_F.md:30).

## 6. Seeds proposed

No ledger row names a seed from 7,485,000 up. Screen M's text proposes 7,485,000-439 and screen R's 7,486,000-499, so F proposes inside 7,487,000-779. The author must confirm.

| Seeds | One purpose |
|---|---|
| 7,480,150-189 | search pool, as in Plan B (correction 1) |
| 7,480,190-229 | in-search checks: shortlist, plateau label |
| 7,487,000-009 | smoke, T0, PR-09 |
| 7,487,010-129 | selection set A |
| 7,487,130-249 | selection set B |
| 7,487,300-779 | verdict, 480 seeds: run once, read at both stages |

## 7. KILL rules

Level: 97.5 % two-sided, Plan B's (m = 2 approved cells, never lowered; planb.md:428). A pass needs every rule against every rule arm at both stages: an intersection, so no further correction (planb.md:429). Stage 2 runs only after a stage 1 pass.

KILL if, against any rule arm:
- **K1, edge:** point below 10 %, or lower bound at or below 0. 10 % is round 2's deciding size (round_2.md:200). Alternative: planb.md:438's form (lower bound above 0, at least 20 s per run).
- **K2, delay non-inferiority (correction 3; V435; round_2.md:361):** lower bound (one-sided 98.75 %) at or below −1 %, the search's free slack (planb.md:227). Round 2's 5 % exceeds every delay difference among the tied rules (critic_F.md:50). Alternative: 2 % (planb.md:437), which owes a +2 % hinge search (critic_F.md:44). Single-learner delay effects are printed beside.
- **K3, learners:** fewer than 4 of 5 have, against every rule arm, a close-following point above 0 and a delay point above −1 % (planb.md:438's delay half, moved to K2's margin).
- **K4 (planb.md:438; decision 9; unchanged):** flow over 0.5 % worse by point; one-sided 95 % upper bound of the mean excess above 0.02 collisions or 0.10 moving full-emergency events per run; 95 % lower bound of the robust-braking excess above 10 %.

Before a pass, K1's label-swap null must be within 1.5 × nominal (planb.md:486). A pass with the plateau label unmet reads "pass at the fixed budget".

## 8. Null and power

EXPLORATORY: 480 seeds resampled from the 240 stored TRUCK seeds, v3w shifted to a true edge (`rigor_oc_out.txt`, `rigor_oc2_out.txt`).

| True edge | 0 % | 8 % | 10 % | 12 % | 15 % |
|---|---|---|---|---|---|
| P(KILL by K1) | 1.000 | 0.903 | 0.530 | 0.232 | 0.005 |
| planb.md:438's form | 0.985 | 0.101 | 0.028 | 0.006 | 0.000 |

- Label-swap false pass: 1.05 % (nominal 1.25 %). A true 12 % edge is KILLed 60-72 % of the time at 80 seeds and 30-42 % at 240: hence 480.
- K2 passes 0.92 at the stored differences, where the pooled arm reads about 0.6 points low (drl_win_directions_v0.md:86), 0.99 at a true tie and 0.48 if 0.5 % worse. False pass if 1 % worse: 1.3-1.7 %.
- K3 and K4 (mine) fire 0 % at the stored values. K3 fires 82 % if every learner is 1 % worse on delay (planb.md:438's unmoved half would fire 82 % at the stored values). K4 fires 96 % at 0.02 planted collisions per run, 72 % at 0.10 full-emergency events, 70 % at 0.6 % less flow, 99.8 % at 12 % more braking.
- Drain has no usable null (0 failures in 1,200 stored v3w rows, V496): a validity row.
- All rules: pass 0.26-0.44 at a true 10 %, 0.66-0.71 at 12 %, 0.91 at 15 %. The screen separates 5 % from 15 %, not 10 % from 12 %.

## 9. Runs x rate = cost; machine-hours; build work in hours; author time, stated apart

| Step | Runs | Hours | Cost |
|---|---|---|---|
| Stage 1: smoke; selection A, 9 × 120 | 1,250 | 0.3 | $0.18 |
| Stage 1 verdict, 11 arms × 480 | 5,280 | 3.1 | $1.90 |
| Continuation, 200 × 384 + 20 × 240 | 81,600 | 15.5 | $9.38 |
| Stage 2: selection B, 12 × 120; smoke; verdict, 480 | 2,080 | 0.7 | $0.40 |

- Rates (correction 7): pack runs 1,690/h, $0.36 per 1,000 (V493-V494); search and selection rows 5,280/h, $0.115 per 1,000 (V490).
- With 6 % setup: stage 1 about $2.2 and 3.6 machine-hours, where a KILL ends the screen; both stages about $12.6 and 21 h.
- A rate check after 30 minutes stops a stage whose projected cost exceeds its cap. After a host change or loss (V494), stage 1 rows must reproduce or are re-run ($1.9).
- Build (my estimate): 12 h. Author time, apart: 2 h.

## 10. Plant and verification effect

No plant file, reward, input, period or actuator value changes. Headways stay 1.6, 1.2, 1.0 and 0.8 s (b_env.py:37): no new T0 is owed. A smoke check follows each code change, host and new rule vector (rows carry the controller hash, planb.md:418). TRUCK is outside the plant's stated intended use; PR-08 and PR-28 are carried unconditionally (planb.md:181-183), PR-26 as a limit (plant_vv_record_v0.md:77). No departure from the CAV contract.

## 11. Cells added to the count (N = 91) and post hoc labels

0. TRUCK is counted (V487); a re-test and rules-only rows add 0 (cells_tested.md:5). The whole screen is post hoc: the 10 % size, the margin, the 480 seeds and the measure classes followed the stored 11.80 % (critic_F.md:25).

## 12. Must-carry disclosures

- TRUCK only; not shown in steady traffic. S2 as registered read KILL (V487). The cell was chosen after related DRL results (planb.md:164).
- Close-following is a reward term read at 1 Hz; 78 % of v3w's counted seconds lie on roads 4a, 4 and ramp 2 (EXPLORATORY).
- Stored costs: braking events, jam count, jerk. Delay is non-inferior, not equal.
- v3w not retrained; rules tuned in the cell; one family, one hinge, 300 generations and its plateau label; 19 rules not re-run; verdict seeds read twice.

## 13. Expected outcome and your probability (a judgement, labelled so)

A judgement, not measured. Stage 1 pass: about 50 % (0.59 if the true edge is drawn around the stored 11.8 %; lower, since that edge chose the hypothesis). A continued rule needs 17 fewer close-following seconds per run (1.8 % of its median, 951) to pull the point under 10 %, so pass given stage 1: about 30 %. **Overall pass: about 15 %.** Expected spend: about $7.

## Synthesis notes

Base: the rigor draft (both judges), with the cheap draft's re-pick, caps and window sum and the opponent draft's validity rows and T0. Where the judges differ: the location guard binds the wording but is no third outcome (rules judge over plant judge), since it has no null and fires in 19 % of studies at the recorded effects (`f_oc_out.txt`); the margin is 1 % (plant judge: the search's slack), with 2 % as the author's choice (rules judge); K3 gets a delay half (plant judge) at K2's margin, named as a move (rules judge); the 19 distant rules stay out by a named set-aside (plant judge: re-running is waste). K4's nulls are computed here; drain has none, so it left the KILL rules. Length: sections 1-13 hold about 1,450 words with a letter in them; numbers and table syntax bring the count to about 1,950, as long as the drafts (1,683-1,954).
