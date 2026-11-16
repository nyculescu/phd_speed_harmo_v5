# Screen R, slowdown recovery: protocol-ready draft (cheapest decisive design)

Stored-row numbers are EXPLORATORY (rows already read for verdicts). My scripts: `work/grid_repick.py`, `work/null_power.py` beside this file (outputs `work/cheap_*.out`). Code lines: the `planb_v23` copy. "Same" = an_x1x2_delay_edge.md.

## 1. Question; what a pass allows; what a KILL closes

**Question.** In X1, does v3w's delay edge of about 4 % survive a rule that reads v3w's own merge input and a rule searched for delay, and where does it arise? X2 does not run (§3).

**A pass** allows a protocol, never a claim. Under the PR-28 label (§7) it allows only a rules-only lane-end check.

**A KILL** closes the delay route on these slowdowns (memo directions R and D5), with a bound (§8).

**Stages.** 0: stored rows. 1: verdict rows. 2: a delay search. A KILL stops the screen.

## 2. Approvals and preconditions

1. **An author decision, labelled post hoc,** setting aside for X1 only: [A3], "no further training, tuning, plant change or seed round" (confirmatory_3.md:132; applied by V395), and "no rule is re-tuned there either" (planb.md:160). V466 (X2) stays in force. This is X1's fourth test (round_2_result.md:239), in a cell picked after control results (V456(3); planb.md:576).
2. **The author accepts a weaker bar, post hoc.** The recorded delay win needs 5 % for 4 of 5 policies (confirmatory_3.md:108); it read 0 of 5 and 2 of 5 (round_1_result.md:212; round_2_result.md:225). This screen uses 3 % at arm level. Without this decision R closes at stage 0, at zero cost.
3. The screen's own cap (proposed $7, inside the $40 per 7 days ceiling, planb.md:561), the rental and the seeds.
4. **Before any verdict row:** stored X1 rows reproduce on every key (as C1, planb.md:388); determinism; reader tests on planted rows; §10's binding check; an adversarial code review.

## 3. Stage 0: statements from stored rows

| Statement (EXPLORATORY) | Source | Decides |
|---|---|---|
| X2: edge over the nearest rule +1.9 % [+0.1, +4.3] at 97.5 % (120 seeds) | same:8 | K1 fires already; no X2 run |
| X1: +4.2 % [+2.4, +5.9] at 97.5 % against p333; no stored rule has a delay point below p333's | same:7, :44 | X1 open at 3 % |
| X1 learners against p333: +2.2, +2.7, +4.2, +6.1, +3.8 % | same:80 | recorded 5 % bar: 1 of 5 |
| Confirmatory 3's grid (69 rules, 7,440,160-179) re-ranked on delay, no close-following bound: lowest median lr1000_10_1, the stored delay opponent; 0 of 69 shown below p333; positive points only os0_10_10, lr1000_13_1, z31333 | my computation, `conf3/tune.jsonl` | no new grid run; the two rules without v3w rows join the arms |
| Against p333, 60 % of the difference is on road 4a; edge +0.5 % in the half of seeds with fewer lane-end stops, +7.5 % in the other | same:59, :74 | PR-28 label expected |
| The queue never clears (V398); v3w's lead still grows at 1,800 s | same:68 | the percentage depends on the window (§12) |
| X1: v3w has 16.6 % more close-following than no control (95 %: 8.4 to 25.1) | round_2_result.md:265 | a delay win cannot stand alone (planb.md:153) |

The samples are three 40-seed sets; the S0/S1 map repeats one (same:20).

## 4. Arms

- **Policy:** v3w frozen, evaluation mode (checkpoints: planb.md:188); arm value = per-seed mean of the 5 learners.
- **Stage 1 opponents:** p333, lr1000_10_1, os0_10_10 (the three nearest); lr1000_13_1, z31333; the near-gap pick; no control, never deciding.
- **Near-gap rule (new class).** A mainline CAV wants 0.8 s. It takes headway L while an acceleration-lane vehicle is within d metres (observation column 14, b_env.py:924, :935). Grid: d = 25, 50, 100 m; L = 1.6, 1.2 s; every mainline lane or only the lane beside the acceleration lane: 12 rules. v3w reads this input; the searched family does not (b_env.py:1128). Selection, 20 seeds, with p333: lowest median paired delay among rules meeting 3E-D's admission (planb.md:228). Frozen before any verdict row.
- **Stage 2 opponent: 3E-D in X1,** Plan B's recipe unchanged (planb.md:223-229, :235-239): start p333 (the pooled delay leader in X1, same:44), population 24, 16 of 40 pool seeds per generation, 100 generations, checks on 40 other seeds, plateau label at 0.5 delay point. One change: the incumbent at generation 40 is frozen and run on the verdict seeds. If a KILL rule fires, the search stops; otherwise it runs to 100 and the final incumbent is run.
- **Equal exposure:** every opponent is tuned in X1 itself, on seeds apart from the verdict seeds; v3w's checkpoints were chosen on X1/X2 validation seeds (planb.md:188).

**Given up:** 11 stored rules with pooled edges of +5.5 to +14.1 %, every interval above 0 (same:29, :32), shown from stored rows; a second search start; a scheduler with a delay library (ASCH picked a single member in TRUCK, V491); MPC-F; X2 runs; a 3,000-s window (a second window-dependent percentage).

## 5. Measures

| Measure | Field | Role | Reward |
|---|---|---|---|
| Door-to-door delay, arm and per learner | `all_delay` (plant_sweep.py:347) | deciding | tied: speed-loss and flow terms (b_env.py:842-845) |
| Share of the difference on 4a, 4, ramp 2 | road-delay keys (planb.md:143, :341) | PR-28 label | tied (delay by road) |
| Lane-end stops; ramp-2 vehicles' delay | `end_stop2`, `delay_ramp2` (plant_sweep.py:294, :346) | report-only | not checked |
| Served flow; extra vehicles into road 4 at 1,200, 1,500, 1,800 s | `passed`, `flow_min` | report-only | tied: flow term |
| Close-following, TTC below 2 and 1.5 s, hard braking, against rules and no control | planb.md:327-338 | report-only, 95 % | reward terms or tied (b_env.py:845) |

## 6. Seeds proposed

The ledger shows no use of 7,485,000 or above; the author must confirm.

| Seeds | Purpose |
|---|---|
| 7,485,300-309 | smoke, identity, determinism; never read for performance |
| 7,485,310-329 | near-gap selection |
| 7,485,330-369 | 3E-D search pool |
| 7,485,370-409 | 3E-D check set |
| 7,485,420-499 | verdict set, 80 seeds, each arm once |

## 7. KILL rules

Statistic: planb.md:424 (median of paired differences over the opponent's median; percentile bootstrap).

| Rule | Fires when | Record |
|---|---|---|
| K1 | against any non-learning arm, the delay edge has a point below 3 % or a 97.5 % lower bound at or below 0 | 80 % power needs about 3 points at 120 seeds (planb.md:519); the W rule (planb.md:438) |
| K2 | fewer than 4 of 5 learners have a positive delay point against every non-learning arm | planb.md:438 |
| Label | over 50 % of the difference against the closest delay opponent lies on 4a, 4 and ramp 2: "survives, PR-28 open" | planb.md:143 (V482) |

**Multiplicity (correction 4).** One cell decides, because X2 cannot pass. The level stays 1 − 0.05/2 = 97.5 %, so X1 reads the same under the two-cell form. A pass is an intersection over opponents and needs no further correction (planb.md:429).

**Two-cell form, the author's alternative.** Each cell is read alone at 97.5 %. A cell is KILLed when K1 or K2 fires in it, and closes on its own. R is KILLed only when both are. The chance of a false lower bound above 0 in either cell is at most 5 %, two-sided. It adds about 42,000 runs and $5 in X2, where K1 already fires on stored rows.

## 8. Null and power

EXPLORATORY: 80 seeds resampled from the 120 stored X1 seeds, three stored rules, 1,500 studies, v3w shifted to each true edge against p333.

| True edge | 0 % | 2 % | 3 % | 4.2 % (stored) | 5 % | 6 % |
|---|---|---|---|---|---|---|
| KILL | 100 % | 97 % | 72 % | 24 % | 7 % | 1 % |

- The screen can fail and can pass. K2 alone fires in 96 % of studies at 0 %.
- Interval half-width: about 2.0 points. A KILL by a point just under 3 % bounds the edge below about 5 %.
- 120 seeds would halve the false KILL at the stored edge (12 %) for about 500 more runs. Not proposed.
- Not computable: the three later opponents. INFERENCE: each look can only add KILLs.

## 9. Runs x rate = cost; machine-hours; build work in hours; author time, stated apart

Rates: evaluation $0.10-0.13 per 1,000 runs (V475), $0.36 with the full pack and field (1,690 runs/h at $0.607/h, V493); search $0.115 per 1,000 rows, 5,280 rows/h (V490).

| Stage | Runs | Machine-hours | Cost |
|---|---|---|---|
| 1: checks about 130 (planb.md:384); selection 260; verdict 12 arms × 80 | 1,350 | 0.5-0.8 | $0.15-0.5 |
| 2a: 40 generations × 384, 3 checks × 240, 80 verdict runs | 16,160 | 3.1 | $1.9 |
| 2b: to generation 100 (40,640 rows in all, V490), 80 verdict runs | 24,640 | 4.7 | $2.8 |
| All, with 6 % setup (V475) | 42,150 | about 8.5 | $5.1-5.5 |

A KILL at stage 1 ends the screen under $1. Build: 10-12 hours (new rule, reader, X1 search option, chain with the stop, review). Author time: about 1.5 hours.

## 10. Plant and verification effect

- No plant file changes. X1 is inside the stated intended use (plant_vv_record_v0.md:9).
- Headways stay at 1.6, 1.2, 1.0, 0.8 s: no new actuator value, no departure from the CAV contract.
- The near-gap rule is new code: planted-row unit tests, then a binding check on 3 smoke seeds (the command changes when the trigger holds, and the held gaps change). PR-10 has no r2m3 T0 record (plant_vv_record_v0.md:46).
- Open gaps carried: PR-26, PR-28 (plant_vv_record_v0.md:77, :79).

## 11. Cells added to the count (N = 91) and post hoc labels

Cells added: 0; a re-test adds none (cells_tested.md:5; V487). Post hoc: the screen, X1 as the deciding cell, the 3 % threshold, and the near-gap rule, designed after v3w's mechanism was read.

## 12. Must-carry disclosures

- The override of [A3]; the cell was chosen where DRL looked best and tested three times before (claim_review_round2.md:221).
- The 3 % threshold is weaker than the recorded 5 % bar (confirmatory_3.md:108), whose reading is shown beside.
- No control in every table; §3's close-following figure beside any delay figure.
- The road share and the PR-28 label. The edge is given in vehicle-seconds over 300-1,800 s and in vehicles served, never as a bare percentage. A later protocol needs a queue that clears.
- Opponents: counts, tuning, 3E-D's plateau label; no scheduler, no MPC.
- X2 was not run.

## 13. Expected outcome and your probability

My judgement, not measured. KILL at stage 1: about 50 % (noise at the stored edge, the near-gap rule, regression from a selected cell). KILL at stage 2, if reached: about 35 %. Survives both: about 30 %, nearly always as "survives, PR-28 open". A pass that allows a DRL protocol directly: about 3 %. Expected spend: about $2.5.
