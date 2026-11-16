# Screen F, protocol-ready draft (angle: statistical rigor)

Effect = −median(P − O) / median(O) × 100 over paired seeds, positive = v3w better, P = per-seed mean of the 5 learners, percentile bootstrap (planb.md:424). EXPL = EXPLORATORY: stored S6 rows, already read for a verdict. R6 = `baseline_v5/readings/read6_v23_supplement.json`. OC = `rigor_oc_out.txt`, `rigor_oc2_out.txt`: n seeds resampled from the 240 stored TRUCK seeds, v3w shifted to a stated true effect.

## 1. Question; what a pass allows; what a KILL closes
In TRUCK at 5,300 veh/h, does frozen v3w keep at least 10 % fewer close-following seconds than the per-zone own-state rule searched for 300 generations, with delay shown within 1 % of the rules'?
- Pass: a confirmatory protocol may be written for one TRUCK-only trade-off sentence; no claim.
- KILL: closes F for v3w on this plant, with its dependent arms (other hinges, richer families, H-3, H-4). No second seed round; no retraining to reopen it (critic_F F7a). The interval is reported, a bounded null.

## 2. Approvals and preconditions
Author decisions:
1. Reopen TRUCK. Plan B read it T (V496), which closes it: "no further training, tuning, plant change or seed round there" (planb.md:575). The screen is a new study, labelled post hoc (planb.md:576). New in this draft.
2. Allow a one-measure sentence at non-inferior delay, against "No sentence claims a win on one measure alone" (planb.md:153, V462(1)). Without it the screen has no pass sentence.
3. The numbers of §7, the seeds of §6, a $15 cap, the rental.
4. A harness change: 300 generations by replay (cmab.py:204-205 refuses it today).

Checks before any verdict row: stored S6 rows of v3w, 3E-C, p333 and no control on 7,480,400-402 replay equal by value (V499); a repeated run is equal; generations 0-99 replay to the stored vectors (cmab.py:224) and incumbent trace; a planted-row test per harness change (planb.md:243).

## 3. Stage 0: stored rows (zero runs, EXPL)
- **Steady traffic is decided.** K1 fires: +7.99 % [−11.71, +31.46] against 3E-C_TRUCK. K2 fires: delay lower bound −3.18 % against os1_15_10 (R6 `S.map`). More seeds cannot rescue it: interval half-width 20.5 points at 240 seeds, 15.2 at 480 (OC). Scope: TRUCK only; every sentence carries the S reading.
- **TRUCK passes every rule of §7** (+11.80 % [+4.97, +19.71]; lowest delay lower bound −0.93 %, os0_10_10; R6). Those rows chose the hypothesis: not evidence.
- **Nothing outside the reward supports a sentence (correction 5).** Against 3E-C_TRUCK, 95 %: fuel per km +0.1 % [−0.1, +0.2]; jam share −0.57 % [−7.30, +11.32]; congested km mean +1.17 % [+0.05, +2.69]; shown worse on 0.1-s jerk, −0.5 % [−0.6, −0.3], and on braking events peaking at 4.5 m/s² or harder, −5.73 % [−8.28, −2.31] (jam and braking: R6; fuel: correction 5; jerk: an_s6 §2). Against p333: jam share +10.65 % [+0.02, +17.61], congested km mean −1.43 % [−3.04, −0.63] (V501), fuel +0.2 % [+0.0, +0.3]. F is a claim on the rewarded count, with a braking cost.

## 4. Arms
| Arm | Definition | Tuned on |
|---|---|---|
| v3w | 5 frozen learners, evaluation mode (planb.md:188) | nothing in TRUCK |
| 3E-C | today's pick g098i00, 20 parameters | pool 7,480,150-189, check 190-229 |
| 3E-C+ | the continuation below | the same, plus the selection set |
| p333, os0_10_10, 3E-D_TRUCK, no control | as stored; no control never decides | as stored |

**3E-C+ (correction 1; critic_F F4).** Replay generations 0-99 from the stored evaluations, then run 100-299 with planb.md §3.3 unchanged: the original pool and check set, population 24, 16 seeds per generation, the same loss (delay hinge +1 %), a check every 10 generations. Fixed budget, no data-dependent stop; the plateau label (check loss at 260 minus at 300 below 1.0) is reported only. Shortlist: the 8 admissible check candidates with the lowest check loss, g098i00, and the CMA mean at 300. Each runs on the selection seeds with p333; 3E-C+ is the lowest selection loss among those admissible there (planb.md:228), committed before its verdict rows.

Exposure: one run per arm and verdict seed, on one machine, commit and pack. The rule has 300 generations in the cell, v3w none.

Not arms (critic_F F5): other hinges; a richer family (no form or budget on record; a flexible searched rule is policy search); decision trees.

## 5. Measures
| Role | Measure | Class |
|---|---|---|
| Deciding | close-following, TTC < 3 s at 1 Hz (`ttc_net`) | reward term (b_env.py:843) |
| Deciding bound | door-to-door delay (`all_delay`) | tied: the reward pays speed (b_env.py:842) |
| Side conditions | flow, collisions, moving full-emergency events, robust braking, drain (planb.md:438) | reward term or tied |
| Report-only, tied | `ttc2`, `ttc15`, `sev3`, `b3_step`, `b45_step`, `events_ge45`, `alks_past_limit`, `E30` | subsets of rewarded events (an_s6 §1) |
| Report-only, outside | fuel per km; acceleration RMS; 0.1-s jerk; jam share, congested km (mean, max), jams, `osc_kmh`; `end_stop`, `end_stop2`; `pass_straight` | no reward term |
| Not read | `gap25`, `b7*`, `E15`; the 0.1-s meter | too few counts; never run (critic_F F3) |

The 19 report-only measures decide nothing: 38 readings at 95 % give about 1 false "shown worse" at true zero. Sentence rule: each one shown worse than 3E-C or 3E-C+ is named before the edge (planb.md:439). The draft's one-word gate is deleted; planb.md:153's words stay barred.

## 6. Seeds proposed (author must confirm 7,485,000-999 is free)
| Seeds | Purpose |
|---|---|
| 7,480,150-189 | search pool, as in Plan B (correction 1) |
| 7,480,190-229 | in-search checks: shortlist and plateau label only |
| 7,485,000-009 | smoke, identity, determinism |
| 7,485,010-129 | selection of 3E-C+ |
| 7,485,200-679 | verdict, 480 seeds, used once |
| the rest | reserved; any use needs its own V# |

## 7. KILL rules
n = 480. Intervals at 97.5 %: Bonferroni m = 2 (the edge was read in S and TRUCK; the level is not lowered when S drops, planb.md:428). A pass needs every rule against every opponent: no further correction (planb.md:429). D = {3E-C, 3E-C+}, fixed before verdict data, with no counting filter (planb.md:214); the next-closest stored opponent's lower bound is +17.44 % (os0_10_10, R6). The statistic stays planb.md:424's; an_s6's pooled-arm bias runs against v3w (§12).
- **K1 edge.** KILL if against any o in D the point is below 10 % or the lower bound is at or below 0. 10 % is V462(1)'s tile size and the harm rule's size (planb.md:437), both older than S6. Disclosed: the memo attached it after seeing 11.80 %.
- **K2 delay bound (correction 3; V435, D11's form).** KILL if the lower bound of v3w's delay effect is at or below −1 % against any of D, p333, os0_10_10, 3E-D_TRUCK. 1 % is the delay slack the search itself has (planb.md:227). The tied rules differ by under 1 % (critic_F F6), so D11's 5 % would be empty here.
- **K3 learners.** KILL if fewer than 4 of 5 have a positive close-following point against each o in D (planb.md:438).
- **K4.** planb.md:438's side conditions, unchanged.
- Before PASS is printed, K1's label-swap null must be at most 1.5 × nominal (planb.md:486).

Stage 1 reads K1-K4 against today's arms; a frozen script stops the job on KILL. Stage 2 adds 3E-C+.

## 8. Null and power (EXPL, OC; n = 480)
| True edge | P(KILL by K1), one opponent | two opponents (3ex1's noise as stand-in) |
|---|---|---|
| 0 % | 1.000 | 1.000 |
| 8 % | 0.903 | 0.965 |
| 10 % | 0.530 | 0.729 |
| 12 % | 0.232 | 0.304 |
| 15 % | 0.005 | 0.012 |

- At a true 12 %: KILL 0.30-0.42 at 240 seeds, 0.60-0.72 at 80.
- Null: no pass in 2,000 studies at a true 0; label-swap false "lower bound > 0" 1.05 % (nominal 1.25 %).
- K2: within 1 % of all four with probability 0.92 at the stored differences, 0.99 at a true tie, 0.48 if truly 0.5 % worse. False pass if truly 1 % worse: 1.3-1.7 % per opponent (nominal 1.25 %). At 240 seeds the stored case gives 0.55: hence n = 480.
- K3 fails 1.2 % at a true 5 %, never from 8 %.
- K4: flow and braking sit more than 4 interval half-widths from their limits (R6); the collision and full-emergency nulls must be computed before data.
- All rules, delay as stored: PASS 0.03-0.09 at a true 8 %, 0.26-0.44 at 10 %, 0.66-0.71 at 12 %, 0.91 at 15 %.
- Bounds: a K1 KILL is unlikely (about 1 %) from 15 %; a PASS (1.3 %) up to 5 %. Upper bound: point + 5.7 on average.
- INFERENCE: a continued rule resembles 3E-C more than 3ex1 does, so the truth lies between the columns.

## 9. Runs × rate = cost
| Step | Runs | Rate (correction 7) | Hours | Cost |
|---|---|---|---|---|
| Smoke, identity | about 160 | 1,690/h, $0.36 per 1,000 | 0.1 | $0.06 |
| Stage 1 verdict, 10 arms × 480 | 4,800 | same | 2.8 | $1.73 |
| Continuation, 200 × 384 + 20 × 240 | 81,600 | 5,280/h, $0.115 per 1,000 | 15.5 | $9.38 |
| Selection, 11 × 120 | 1,320 | same | 0.25 | $0.15 |
| Stage 2 verdict | 480 | 1,690/h | 0.3 | $0.17 |

Stage 1 alone: about $1.8, 3 h. Both: about $11.5, 19 h; $12.2 and 20 h with 6 % setup (planb.md:538). Build: 10-14 h (my estimate). Author time: about 2 h.

## 10. Plant and verification effect
No plant file, actuator value, input or period changes. Headways stay 1.6, 1.2, 1.0, 0.8 s (b_env.py:37): no T0; PR-10 stays partial. TRUCK is outside the intended use; PR-08 and PR-28 are carried (planb.md:183).

## 11. Cells added
0. TRUCK at 5,300 is counted (N = 91, V487); a re-test adds 0 (cells_tested.md:5). Post hoc; never merged into Plan B's reading.

## 12. Must-carry disclosures
- Hypothesis, cell and closest opponent picked after S6; not shown in steady traffic; G4(ii): S2 as registered read KILL (V486, V487).
- Close-following and 3 m/s² braking are reward terms; about 75 % of counted seconds lie on edge 4a (critic_F F6).
- Stored costs: braking events and jerk (§3). v3w not retrained; rules tuned in the cell; one rule family, one hinge, 300 generations.
- The 10 % size, the 1 % margin and n were set with stored rows in view.
- The per-seed learner mean reads 0.9 points below the per-learner average in TRUCK (11.80 against 12.68, EXPL).

## 13. Expected outcome (judgement, not measured)
Stage 1 pass: about 0.6 (0.59 with the true edge drawn from N(11.8, 3.3), ignoring selection). Stage 2: 17 fewer seconds per run, 2 % of the rule's median, pull the point under 10 %; the search was still moving at generation 100 (critic_F F4). Pass given stage 1: about 0.3. **Overall pass: about 15-20 %.**
