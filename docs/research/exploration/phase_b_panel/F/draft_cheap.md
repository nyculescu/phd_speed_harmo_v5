# Screen F, frontier claim: cheapest decisive draft

Every stored-row number is EXPLORATORY (rows already read for a verdict). Positive = v3w better. Intervals are 97.5 % unless marked. J = `/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json`. Scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/cheap/`.

## 1. Question; what a pass allows; what a KILL closes

In TRUCK, at non-inferior delay, does v3w keep at least 10 % fewer close-following seconds than the best ZoneOwnState rule of the recorded search, once its pick is re-selected (stage 1) and the search is continued (stage 2)?
- Pass of both stages: a protocol for a TRUCK-only trade-off sentence may be written; never a claim.
- KILL: direction F closes, and a stage 1 KILL stops the screen. Retraining v3w for TRUCK does not reopen it (critic_F.md F7).

## 2. Approvals and preconditions

Author decisions before any spend:
1. Set aside planb.md:575: TRUCK = T (V496) closed the cell to "further training, tuning, plant change or seed round". F is a new study, post hoc (planb.md:576).
2. Accept the claim form: non-inferior delay with fewer close-following seconds. It sets aside planb.md:153 (no win "on one measure alone", V462(1)) and Plan B's W (delay lower bound > 0, planb.md:438). If refused, F closes at $0.
3. Scope: TRUCK only (row 0.1). If steady traffic must also hold, F is KILLed now at $0.
4. Re-use Plan B's search seeds 7,480,150-229. Fresh seeds from 7,485,000: no ledger row names them; the author confirms.
5. A cap ($2 for stage 1, $7 for stage 2) and a rental (V483). The $40 per 7 days ceiling already holds at least $18.3 (V475, V494, V499).

Preconditions: the smoke check and tests of §10.

## 3. Stage 0: statements from stored rows (zero runs)

| # | Statement | What it decides |
|---|---|---|
| 0.1 | Steady traffic: the rule of §7 fires against 3 rules, among them 3E-C_TRUCK +7.99 % [−11.71, +31.46] (J `S.map`). The delay bound holds against 16 of 23 (pooled arm, biased against v3w: an_s6_independent_measures.md §0.4). | F has no steady-traffic part; no S run. |
| 0.2 | TRUCK delay: the lower bound is above −2 % against all 23 rules (lowest os0_10_10 −0.58 % [−0.93, +0.20], J `map`). | The delay half holds today. |
| 0.3 | TRUCK close-following: nearest 3E-C_TRUCK +11.80 % [+4.97, +19.71]; next os0_10_10 +22.57 % [+17.44, +27.90]. | Only the 3E-C search can change the answer; the other 21 rules are not re-run. |
| 0.4 | At 95 % (J `map_report_only`; fuel from correction 5). Against 3E-C_TRUCK: braking events at 4.5 m/s² or harder −5.73 % [−8.28, −2.31], shown worse; oscillation +1.02 % [+0.55, +1.36]; fuel per km +0.1 % [−0.1, +0.2]; jam share not shown different. Against p333: jam share +10.65 % [+0.02, +17.61]; congested km −1.43 % [−3.04, −0.63]. | Outside the reward, shown differences from the nearest rule are about 1 % or less. No "outside the reward" gate; §5 limits the sentence. |
| 0.5 | 3E-C's pick is the lowest of 54 check losses on 40 seeds. Check −32.53 %; fresh seeds −21.18 % (J `overfit_vs_p333`). | Stage 1. |

## 4. Arms

- **v3w:** the 5 frozen learners, evaluation mode, as in S6; arm = per-seed mean (planb.md:194-195).
- **R1 (stage 1):** no new search; the 8 admissible stored candidates with the lowest check loss, ties to the earlier generation (g098i00 = today's 3E-C, g065i01, g070i09, g073i20, g086i12, mean_g060, g062i22, g043i20; `planb_s34_remote/cmab/TRUCK_ttc/checks.jsonl`), run with p333 on selection set A, no measurement pack. R1 = the lowest loss among those admitted (planb.md:227-228).
- **R2 (stage 2):** the same search continued, not restarted: CMA seed 20261109, pool 7,480,150-189 in the same moving window, in-search checks on 7,480,190-229, generations 100-199, a fixed budget with no early stop. The plateau label (160 against 200) is reported only. The 8 lowest check losses of generations 20-200, with g098i00 and R1, go to selection set B; the same rule picks R2. Correction 1 is read as: search seed lines unchanged, fresh seeds for all that decides; the author confirms.
- **g098i00:** deciding in each verdict. **p333, os0_10_10:** delay anchors (V496).
- **Exposure:** every arm runs once per verdict seed. The rule gets 200 generations in TRUCK, v3w none (planb.md:188, :215); this favours the rules.

Given up: no control and the other 21 rules in the verdict (stored S6 values carried); searches at delay hinge 0 % and +2 %; the richer family (no form or budget; CMA-ES on the actor's inputs is policy search, critic_F.md F5); decision trees; the 0.1-s meter; generations 200-300.

## 5. Measures

| Measure | Role | Class |
|---|---|---|
| Close-following (`ttc_net`, TTC below 3 s, 1 Hz) | deciding | reward term (b_env.py:811-812) |
| Delay (`all_delay`) | deciding, non-inferiority | tied (speed and flow terms, b_env.py:842) |
| `ttc2`, `ttc15`, `sev3`, braking events at 4.5 m/s² or harder, robust braking, collisions | report-only | tied or nested |
| Jam share, congested share, congested km, oscillation (side files, V498-V500); fuel per km; acceleration RMS; jerk; flow; TTT | report-only | outside |

Report-only rows: 95 %, against R, g098i00 and p333. Wording fixed now: the sentence names close-following only, calls it a reward term, and prints every measure on which v3w is shown worse. "Safe" and "safer" stay barred (planb.md:153).

## 6. Seeds proposed

| Seeds | One purpose |
|---|---|
| 7,480,150-189; 190-229 | stage 2 search pool; in-search checks (shortlist only) |
| 7,485,000-159 | selection A |
| 7,485,160-399 | verdict 1 |
| 7,485,400-559 | selection B |
| 7,485,560-799 | verdict 2 |

Re-base the block against screens M and R.

## 7. KILL rules

Statistic: planb.md:424, pooled arm; per-learner effects report-only. Level: 97.5 % two-sided, Plan B's, so S6's intervals compare. Multiplicity: one cell; a pass needs every rule, both measures and both verdicts (an intersection), so no correction (planb.md:429).

KILL at a verdict if:
- **K1:** against R or g098i00, the close-following point is below 10 %, or its lower bound is at or below 0. Source of 10 %: round_2.md:200 and V462(1), both older than S6. Disclosed: picked for this screen after 11.80 % was seen.
- **K2:** against R, g098i00, p333 or os0_10_10, the delay lower bound is at or below −2 %. This is the non-inferiority form of V435 and D11 (round_2.md:361), one-sided 98.75 %. Source of 2 %: planb.md:228 and :437. D11's 5 % served 40 seeds at SD 7-11 %; TRUCK has SD 5.2-6.5 % and 240 seeds.

## 8. Null and power

One rule with 3E-C's seed noise, delay at a true tie, 2,500 simulated studies (`cheap/oc_out.txt`):

| True edge | P(KILL), 240 seeds | 160 seeds |
|---|---|---|
| 0 % | 0.999 | 0.996 |
| 8 % | 0.828 | 0.777 |
| 10 % | 0.526 | 0.566 |
| 12 % | 0.297 | 0.382 |
| 15 % | 0.025 | 0.081 |

- The rule can fail (0 %: 99.9 %) and can pass (the stored 240 seeds pass it).
- K2 fires 0.0 % of the time at a true tie, 2-13 % at −1 %, 98 % at −2 %.
- The screen cannot separate 10 % from 12 %.
- Two rules and two verdicts raise P(KILL) (not simulated): a true 12 % edge passes both verdicts at most half the time (0.70²), a true 15 % edge at least 90 % (union bound).
- Selection loss SD: 7.9 points at 40 seeds, 6.2 at 80, 4.7 at 160; hence 160.

## 9. Runs x rate = cost; machine-hours; build work in hours; author time

| Step | Runs | Hours | Cost |
|---|---|---|---|
| Selection A, no pack | 9 × 160 = 1,440 | 0.3 | $0.17 at $0.115 per 1,000 (V490) |
| Verdict 1, pack and field | 9 × 240 = 2,160 | 1.3 | $0.78 at $0.36 per 1,000 (correction 7; V493) |
| **Stage 1 with 6 % setup** | about 3,700 | about 2 | **about $1.1** |
| Search, generations 100-199 | 100 × 384 + 10 × 240 = 40,800 | 7.7 | $4.69 |
| Selection B and verdict 2 | 1,760 + 2,160 | 1.6 | $0.98 |
| **Stage 2 with 6 % setup** | about 44,900 | about 9.9 | **about $6.0** |

Build: about 11 h (my estimate). Author: about 1.5 h.

## 10. Plant and verification effect

- No plant, network or reward change. ZoneOwnState commands 1.6, 1.2, 1.0 and 0.8 s only (cma2.py:41): no T0 run; PR-10 stays partial.
- Harness change: cmab.py:204-205 refuses a changed generation count. Tests: generations 0-99 replay to the stored vectors at 1e-9; the incumbent at 100 is g098i00.
- Smoke on the rented host before each stage: stored rows equal value by value (V499).
- Labels: TRUCK is outside the plant's stated intended use; PR-08 and PR-28 unconditional (planb.md:136). No departure from the CAV contract.

## 11. Cells added to the count (N = 91) and post hoc labels

Cells added: 0; N stays 91 (a re-test adds 0, cells_tested.md:5). The screen is post hoc.

## 12. Must-carry disclosures

- V486-V487 (G4 replacement; S2 as registered read KILL); TRUCK = T, study NULL (V496), closure set aside; cell chosen after related DRL results (planb.md:136).
- Claim form and 10 % fixed after S6; one rule family, one delay hinge (+1 %), 200 generations, planb.md:238's label.
- Close-following: a reward term, 1 Hz, about 75 % of its seconds on edge 4a at merge 2 (critic_F.md F6; PR-28); v3w shown worse on braking events at 4.5 m/s² or harder.
- Not shown in steady traffic; worse than no control in X1 (round_2_result.md:265); X2 closed (V466).
- Pooled-arm bias against v3w; no control not re-run; search seeds re-used.

## 13. Expected outcome and probability (a judgement, not measured)

Stage 1 KILL: about 45 % (at the recorded 11.8 % the rule already fires one time in three). Stage 2 KILL after a stage 1 pass: about 55 %. Pass of both: about 25 %. Expected spend: about $4.
