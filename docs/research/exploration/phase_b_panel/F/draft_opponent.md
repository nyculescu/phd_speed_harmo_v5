# Screen F, the frontier claim: protocol-ready draft (strongest opponents, plant validity)

Positive = v3w better; intervals 97.5 % unless stated. EXPLORATORY = from stored S6 rows already read for a verdict; "mine" = `f_stage0.py`, `f_oc.py`, `f_oc2.py` in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/`.

## 1. Question; what a pass allows; what a KILL closes

- **Question.** In TRUCK on `plant_c3` at 5,300 veh/h, does frozen v3w keep fewer close-following seconds, at delay within 2 %, than every non-learning arm, once 3E-C has run a fixed longer budget and the rules have every advantage the record allows? TRUCK only: stage 0 closes steady traffic.
- **A pass** allows a protocol for one two-measure TRUCK sentence, never a claim.
- **A KILL** closes the frontier claim in TRUCK; retraining v3w for TRUCK may not reopen it. The rules were tuned there and v3w was not (planb.md:186-188, :215): conservative on tuning, but the cell was chosen after related DRL results (planb.md:164).

## 2. Approvals and preconditions

Author decisions:
1. Set aside planb.md:575: TRUCK ended T (V496), so "no further training, tuning, plant change or seed round there".
2. Section 6's seeds, the Plan B pool reused (correction 1).
3. A rental and this study's own cap: $15 for stage 1, $13 for stage 2 (V488's cap does not carry over).
4. That "delay non-inferior and fewer close-following seconds" meets planb.md:153 ("No sentence claims a win on one measure alone").
5. That a fixed 26-parameter threshold rule found by CMA-ES counts as non-learning, as 3E's 20 parameters do (planb.md:206); critic_F.md:46 calls it policy search.

Plant checks before any search; a failure stops the screen:
- Identity C1, C1b; determinism per machine (planb.md:388-390).
- **T0, PR-10** ("partial: no r2m3 T0 record", plant_vv_record_v0.md:46): uniform 1.6, 1.2, 1.0, 0.8 s on 2 smoke seeds; the median held time gap of commanded ALKS follows the command order; `tau_mismatch` = 0 in every row.
- **PR-09** per new rule (planb.md:408); **PR-24** planted-trace tests (planb.md:339).
- **PR-26** (capacity drop "not settled", plant_vv_record_v0.md:77): a carried limit, no gate, since F claims no delay gain. Its zero-run estimator with a null (critic_ranking_audit.md:42) precedes any protocol.

## 3. Stage 0: statements from stored rows (zero runs)

- **Steady traffic decides itself.** The edge over 3E-C_TRUCK, not tuned there, is +7.99 % [−11.71, +31.46] (record, read6_v23.json `S.map`). "Worse on delay than three rules" is partly a pooled-arm effect (an_s6_independent_measures.md:12; "an_s6" below).
- **TRUCK (V496):** edge over 3E-C +11.80 % [+4.97, +19.71]; delay against os0_10_10 −0.58 % [−0.93, +0.20].
- **PR-28, EXPLORATORY (mine).** 78 % of v3w's counted seconds lie on roads 4a, 4 and ramp 2. Off them the edge over 3E-C is +9.05 % [+4.50, +18.73] (3 of 5 learners' lower bounds above 0); without the 5 s after a lane change, +11.26 % [+6.10, +20.63]. The edge is not confined to merge 2 or to lane changes.
- **PR-10, EXPLORATORY (mine).** `tau_mismatch` is 0 in 13,920 rows; 99.98 % of commanded ALKS-seconds hold the commanded headway.
- **Outside the reward, 95 %, uncorrected** (correction 5; read6_v23_supplement.json). Against p333: jam share +10.65 % [+0.02, +17.61], mean congested length −1.43 % [−3.04, −0.63] (record, V501), fuel per km +0.2 % [+0.0, +0.3] (EXPLORATORY). Against 3E-C: shown worse on jerk, −0.5 % [−0.6, −0.3] (EXPLORATORY, an_s6:64), and jam count, −8.57 % [−14.29, −4.29] (pooled-arm caution); shown better on oscillation and mean congested length; not shown on jam share, fuel and acceleration RMS (an_s6:97-101). This fixes the wording now: no statement beyond the two measures.

## 4. Arms

| Arm | Definition | Tuning seeds | Stage |
|---|---|---|---|
| v3w | 5 frozen learners, evaluation mode (planb.md:188) | none in TRUCK | 1, 2 |
| 23 stored opponents | Plan B's TRUCK deciding set (V491), today's 3E-C (g098i00) among them | as stored | 1 |
| 3E-C300 | **Continuation.** Generations 0-99 replayed from stored vectors (cmab.py:216-224), then 100-299: same pool, window, CMA state and loss (planb.md:223-229). Fixed budget, no stop rule | 7,480,150-189 | 1 |
| 3E-C2 | **Restart, said so.** Same family, start g098i00, delay hinge +2 % (v3w's margin), 100 generations | new pool | 2 |
| 3E-G | **Restart, said so.** ZoneOwnState plus 6 global parameters (26): a trigger on leader gap over closing speed, a lane-0 trigger on distance to the nearest accelerating-lane vehicle, each with its level; LocalRule's look-ahead range and threshold (b_env.py:991-1026). Recipe of 3E-C2 | new pool | 2 |
| No control | never deciding, in every table | | 1, 2 |

- **Incumbent.** Every 10th generation the 5 best configurations and the CMA mean (planb.md:235) run on 80 fresh selection seeds. Incumbent = lowest selection loss with delay at most +2 % over p333 by point (planb.md:228). Plan B's check seeds picked g098i00 and are not reused. The plateau label (planb.md:238, generations 260 against 300) is reported, never a stop. The continuation is a logged harness change (cmab.py:204-205).
- **Exposure.** Rules are tuned in the cell, read 400-1,000 m ahead and answer every 5 s; v3w every 10 s (planb.md:215; V381(2)). No counting filter (planb.md:214).
- Stage 2 runs only after a stage 1 pass, and reruns p333, os0_10_10, g098i00 and 3E-C300 beside its two new arms.

## 5. Measures

| Measure (field) | Role | Class |
|---|---|---|
| Door-to-door delay (`all_delay`) | deciding, non-inferiority | tied (speed and flow terms, b_env.py:842) |
| Close-following, 1 Hz (`ttc_net`) | deciding | reward term (b_env.py:812, :843) |
| The same off roads 4a, 4, ramp 2 (`m_road_ttc3`) | location guard (PR-28) | reward term |
| The same without lane-change samples; `ttc_half` | validity rows | reward term |
| Flow, collisions, moving full-emergency events, robust braking, drain | constraints of planb.md:438-446 | reward term or tied |
| TTC below 2 s and 1.5 s, `sev3`, braking events at 4.5 m/s² or harder, `E30` | cost rows, 95 % | tied (an_s6:21) |
| Acceleration RMS, jerk, seconds at −3 ≤ a < −1.5, `osc_kmh`, fuel per km, jam share, jam count, congested km, `pass_straight`, `end_stop2` | cost rows, 95 % | outside |

Cost rows are read against each searched arm and os0_10_10, single learners beside the arm. Each "shown worse" leads the pass sentence (as planb.md:439). The 0.1-s meter is dropped: it lacks the thresholds and never ran (critic_F.md:30).

## 6. Seeds proposed

The ledger has no 7,485,xxx entry (grep, 0 hits). The author must confirm. 3E-C300 keeps 3E-C's CMA seed (planb.md:225); the restarts take 20261128 and 20261138 (proposed).

| Seeds | One purpose |
|---|---|
| 7,485,000-009 | smoke, identity, determinism, T0 |
| 7,480,150-189 (Plan B pool) | 3E-C300 search |
| 7,485,100-179 | selection of every incumbent |
| 7,485,200-279 | pool of the two restarts |
| 7,485,400-639 | stage 1 verdict, used once |
| 7,485,640-879 | stage 2 verdict, used once |

## 7. KILL rules

Statistic of planb.md:424. Level 97.5 % two-sided: Plan B's m = 2, not lowered when a cell dropped (planb.md:428). An intersection over arms, measures and stages needs no further correction (planb.md:429).

KILL F if, against any arm:
1. **Delay:** the lower bound of v3w's delay effect is at or below −2 % (non-inferiority, V435 and round_2.md:361; 2 % is the harm limit and 3E-C's admission, planb.md:437, :228).
2. **Edge:** the close-following lower bound is at or below 0, or the median paired reduction is below 20 s per run (planb.md:438, fixed before S6). The 10 % point, written after 11.80 % was seen (critic_F.md:25), is dropped.
3. **Learners:** fewer than 4 of 5 have a positive close-following point and a delay point above −2 % (after planb.md:438).
4. A constraint of planb.md:438-446 fails.

**Neither pass nor KILL:** rules 1-4 hold, but the off-merge-2 lower bound is at or below 0 against a searched arm. PR-28 then closes before any protocol. **Pass:** no rule fires in either stage and the guard holds.

## 8. Null and power

EXPLORATORY (mine): 1,500 resampled 240-seed studies; v3w shifted to a true value against 3E-C (edge) or os0_10_10 (delay).

| True edge | 0 % | 5 % | 8 % | 10 % | 12 % | 15 % |
|---|---|---|---|---|---|---|
| P(KILL) | 0.987 | 0.693 | 0.369 | 0.233 | 0.114 | 0.011 |

- False pass at zero edge: 1.3 % (nominal 1.25 %). Rule 1 fires in 0.0 % of studies at a true delay tie, 3.0 % at 1 % worse, 98.8 % at 2 % worse. It is read on the arm, which reads about 0.6 points worse than the single learners (drl_win_directions_v0.md:86): conservative.
- At the recorded effects: KILL 14.2 %, guard fails 19.2 %, clean pass 73.8 %.
- Smallest edge it can bound: between 10 % and 12 % (80 % pass). A KILL does not show a zero edge. At 80 seeds a true 12 % edge was KILLed 61 % of the time (critic_F.md:16-22); hence 240.
- Before the reading, the binding comparisons get planb.md:486's label-swap null.

## 9. Runs x rate = cost

| Item | Runs | Hours | Cost |
|---|---|---|---|
| Stage 1 search (200 × 24 × 16) and selection (20 × 6 × 80 + 160) | 86,560 | 16.4 | $10.0 |
| Stage 1 smoke (160) and verdict (30 arms × 240) | 7,360 | 4.4 | $2.7 |
| Stage 2 searches (2 × 100 × 24 × 16) and selection (2 × 9 × 6 × 80 + 160) | 85,600 | 16.2 | $9.8 |
| Stage 2 smoke (160) and verdict (12 arms × 240) | 3,040 | 1.8 | $1.1 |

Rates: searches and selection 5,280 rows/h, $0.115 per 1,000 (V490); verdicts 1,690 runs/h, $0.36 per 1,000 (V493-V494). Stage 1 alone: $12.6. Both: about 39 machine-hours and $23.5, about $25 with 6 % setup (planb.md:538), inside $40 per 7 days. Build, my estimate: 13 h for stage 1, 9 h for stage 2. Author time, apart: about 1.5 h of approvals, 1 h per reading.

## 10. Plant and verification effect

- No plant file changes. Headways stay 1.6, 1.2, 1.0, 0.8 s (cma2.py:41): no new actuator value. Each code change gets a smoke check and section 2's checks.
- TRUCK is outside the plant's stated intended use (planb.md:181-182); its PR-08, PR-28 clause is unconditional (planb.md:183).
- 3E-G reads the actor's own inputs and LocalRule's roadside bins only; PR-15 inspection before its search. v3w's CAV contract is unchanged.

## 11. Cells added to the count (N = 91) and post hoc labels

0: TRUCK is counted (V487); a re-test and rules-only rows add 0 (cells_tested.md:5). Post hoc: the whole screen (planb.md:576); the guard, the measure classes and the 2 % margin, written after the S6 rows were read.

## 12. Must-carry disclosures

- TRUCK only; in steady traffic the edge over the same rule is not shown.
- Close-following is a reward term read at 1 Hz. Delay is non-inferior at 2 %, not equal.
- Outside the plant's stated intended use. S2 as registered read KILL; the V486 replacement (V487). PR-08, PR-28, PR-26 limits. Plan B closed the cell (planb.md:575).
- Each searched rule's plateau label; the reused pool; 3E-G's place between rule and policy search.
- Every cost row shown worse. Today: braking events at 4.5 m/s² or harder against 3E-C, −5.73 % [−8.28, −2.31] at 95 % (record).
- Jam metrics rest on rebuilt side files (V498-V500). No safety wording (planb.md:153).

## 13. Expected outcome and your probability

Judgement, not measured: KILL at stage 1 about 45 %; both stages pass about 30 %; pass with the guard holding about 25 %. Today's rule alone gives a 14 % KILL rate at the recorded edge; three more searches only add opponents.
