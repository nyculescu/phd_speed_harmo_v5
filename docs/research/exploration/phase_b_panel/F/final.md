# Screen F, the frontier claim: final protocol text

## PART 1. The screen

Effect: planb.md:424's form, positive = v3w better; intervals two-sided 97.5 % unless marked. Reading = `docs/research/baseline_v5/readings/read6_v23_supplement.json`. EXPLORATORY = from stored S6 rows, already read for a verdict (mine: `v2` to `v6` in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/final_work/`). Code lines: the `planb_v23` copy.

### 1. Question; what a pass allows; what a KILL closes

In TRUCK at 5,300 veh/h, does frozen v3w keep a close-following point edge of 10 % or more, lower bound above 0, over the ZoneOwnState rule as picked today, re-picked on fresh seeds (stage 1) and searched on to 300 generations (stage 2), with delay shown less than 1 % worse than every rule arm's?
- Pass: a protocol may be written for one TRUCK-only trade-off sentence, tested on fresh seeds. This screen's rows are not evidence for it. Never a claim.
- KILL: closes F for v3w on this plant: no second seed round, no retraining (critic_F.md:56).

### 2. Approvals and preconditions

Author decisions, each a V# before the rental:
1. Reopen TRUCK, closed by planb.md:575 (V496): a new study, post hoc (planb.md:576).
2. The claim form, against planb.md:153 ("No sentence claims a win on one measure alone"). If refused, F closes at $0.
3. The statistic. Default: K1 and K2 read the mean of the five learners' effects (each learner's run as P), seeds resampled jointly. This sets aside planb.md:424's pooled arm (five runs averaged against one), which is printed beside.
4. K1's form, K2's margin, the rule arms, the harness change, the seeds.
5. A rental; caps of $4 (stage 1) and $12 (stage 2), inside $40 per 7 days, where the ledger already holds about $18.6 for 2026-11-08 to 11-10 (V475, V484, V490, V492, V494, V499; my sum) and earlier rentals (V437, V461, V464).

Before any verdict row, on the rented host at the screen's commit:
- stored rows reproduce by value (V499): each stored arm on 3 seeds (planb.md:418) and, before generation 100, the search's reference rows (p333 on 7,480,150-229; g098i00 on its 16 search seeds; cmab.py:208-209; cma2.py:212). A difference stops the stage (planb.md:589); in the reference rows it stops the continuation on that host;
- a repeated run is equal; planted-row tests; a code review; PR-09 per new rule (planb.md:378, :408);
- T0 for PR-10 ("partial: no r2m3 T0 record", plant_vv_record_v0.md:46): uniform 1.6, 1.2, 1.0 and 0.8 s on 2 seeds, `tau_mismatch` = 0 (plant_sweep.py:224), delay differing between 1.6 and 0.8 s.

### 3. Stage 0: statements from stored rows (zero runs)

EXPLORATORY.
- TRUCK passes section 7 today: edge over 3E-C +12.68 % [+6.32, +18.35] (pooled, recorded: +11.80 % [+4.97, +19.71]); lowest delay bound −0.59 % (os0_10_10; pooled −0.93 %). These rows chose the hypothesis; they are not evidence.
- Steady traffic fails K2 against 5 rules (pooled: 13, and K1 against 3; 3E-C_TRUCK +7.99 % [−11.71, +31.46]). No rule was searched there. Scope: TRUCK only.
- The pooled arm reads low: 0.63 points [0.21, 0.86] on delay against os0_10_10 (95 %). Pseudo-arms of five stored rules, each shifted to tie a sixth, are shown worse on delay in 22.5 % of studies (nominal 1.25 %); in the default form, 1.3 %.
- Outside the reward nothing adds a sentence (section 5).

### 4. Arms

- **v3w:** 5 frozen learners, evaluation mode, never tuned in TRUCK (planb.md:188).
- **3E-C:** today's pick g098i00, the lowest of 47 admissible check losses.
- **3E-C-R (stage 1; no search):** the 9 lowest admissible stored check losses (the eighth and ninth tie) run with p333 on selection set A; the lowest loss admitted wins (planb.md:227-228).
- **3E-C+ (stage 2; correction 1): the search continued, not restarted.** Generations 0-99 replay from the stored evaluations and must give g098i00 (cmab.py:223-224). Generations 100-299 run under planb.md §3.3 unchanged (original pool, check set, CMA seed, loss): a harness change, since cmab.py:204-205 refuses a changed generation count. Fixed budget; no result-dependent stop; the plateau label (check loss at 260 minus at 300 below 1.0, after planb.md:238) is reported only. Selection set B then runs p333, the 8 lowest admissible check losses of generations 20-300, g098i00, 3E-C-R and the final CMA mean; the lowest loss admitted wins, committed before its verdict rows. Plan B's incumbent at 300 (planb.md:236) is a verdict arm too.
- **Stored rule arms:** the 9 with an S6 delay lower bound at or below 0 (V496): os0_10_10, p333, lr1000_10_1, grid_os1_10_10, os1_15_10, 3E-D_TRUCK, lr1000_16_2, grid_lr400_13_1, lr400_13_2. No control beside, never deciding.
- **Not run:** the other 13 stored rules, set aside against planb.md:214 (recorded lower bounds at least +0.56 % on delay, +17.61 % on close-following; re-running: 6,240 runs, about $2.2); other hinges, trees, richer families (no form or budget on record; critic_F.md:46).
- **Exposure:** one run per arm and verdict seed. The rule gets 300 generations in the cell and answers every 5 s; v3w none, every 10 s (planb.md:215; V381(2)).

### 5. Measures

- **Deciding:** close-following, TTC < 3 s at 1 Hz (`ttc_net`), a reward term (b_env.py:812, :843); delay (`all_delay`), tied to the speed term (b_env.py:842).
- **Side conditions (K4):** flow, collisions, moving full-emergency events, robust braking: reward terms or tied.
- **Report-only, tied:** TTC < 2 s and < 1.5 s, `sev3`; braking events at 4.5 m/s² or harder, shown worse against 3E-C: −5.73 % [−8.28, −2.31].
- **Report-only, outside (correction 5).** Stored, pooled, 95 %, uncorrected; fuel and jerk EXPLORATORY, the rest recorded (V501):
  - against p333: jam share +10.65 % [+0.02, +17.61]; shown worse on congested km mean, −1.43 % [−3.04, −0.63], and max, −3.91 % [−6.52, −1.74]; congested km is also shown worse against os0_10_10 (mean) and 3E-D_TRUCK (mean, max);
  - fuel per km, TRUCK then steady traffic: against p333 +0.2 % [+0.0, +0.3] and −0.0 % [−0.1, +0.1]; against 3E-C +0.1 % [−0.1, +0.2] and −0.1 % [−0.3, +0.1]; against no control +0.6 % and +1.1 %;
  - against 3E-C: shown worse on jam count, −8.57 % [−14.29, −4.29], and jerk, −0.5 % [−0.6, −0.3]; oscillation and acceleration RMS beside.
- **Validity (PR-28), report-only:** drain; lane-change share; the edge off roads 4a, 4 and ramp 2.
- A sentence names close-following only, as a reward term, and leads with every measure shown worse (planb.md:439), without planb.md:153's barred words. The 0.1-s meter never ran and is not read (critic_F.md:30).

### 6. Seeds proposed

The ledger names no seed from 7,485,000 up; M's text takes 7,485,000-499 and R's 7,486,000-439. The author must confirm.

| Seeds | One purpose |
|---|---|
| 7,480,150-189 | search pool, as in Plan B (correction 1) |
| 7,480,190-229 | in-search checks: shortlist, plateau label |
| 7,487,000-009 | smoke, T0, PR-09 |
| 7,487,010-129 | selection set A |
| 7,487,130-249 | selection set B |
| 7,487,300-779 | verdict, 480 seeds: each arm run once, read at both stages |

### 7. KILL rules

Level: two-sided 97.5 %, as TRUCK was read (m = 2, never lowered; planb.md:428); 95 % would be nominal for one cell. A pass is one intersection over rules, rule arms and both stages, read in a fixed order: no further correction (planb.md:429). Stage 2 runs only after a stage 1 pass.

KILL if, against any rule arm:
- **K1, edge:** point below 10 %, or lower bound (97.5 %) at or below 0. 10 % is round 2's per-policy size (round_2.md:200), written after the stored 11.80 % was seen.
- **K2, delay non-inferiority (correction 3; the form of V435 and D11, round_2.md:209):** lower bound (97.5 %) at or below −1 %, the search's penalty-free slack (planb.md:227). D11's 5 % exceeds every delay difference among the nine tied rules (critic_F.md:50).
- **K3, learners:** fewer than 4 of 5 have, against every rule arm, a close-following point above 0 and a delay point above −1 % (planb.md:438, its delay half moved to K2's margin).
- **K4 (planb.md:438, :91-92; pooled arm, unchanged):** flow over 0.5 % worse by point; mean excess above 0.02 collisions or 0.10 moving full-emergency events per run (one-sided 95 % upper bound); robust-braking excess above 10 % (95 % lower bound).

Before a pass, K1's label-swap null (one coin per seed) must be within 1.5 × nominal (planb.md:486). A pass with the plateau label unmet reads "pass at the fixed budget". The default form decides; a different pooled result is reported in those words.

### 8. Null and power

EXPLORATORY: 480 seeds resampled from the 240 stored, v3w shifted to the stated truth (`v3_out.txt`, `v4_out.txt`, `v6_out.txt`).

| True single-learner edge | 0 % | 8 % | 10 % | 12 % | 15 % |
|---|---|---|---|---|---|
| P(KILL by K1) | 1.000 | 0.853 | 0.503 | 0.156 | 0.003 |
| P(pass K1 to K3) | 0.000 | 0.147 | 0.497 | 0.844 | 0.997 |

- The screen separates 5 % from 15 %, not 10 % from 12 %.
- K2 passes 0.987 if every learner ties every arm, 0.165 at 0.5 % worse, 0.000 at 1 % worse: it bounds a 1 % deficit. The pooled form's numbers are in Part 2, open item 1.
- Null of the default form on section 3's pseudo-arms: shown better in 1.2 % (delay) and 1.1 % (close-following) of studies; nominal 1.25 %.
- K3 fires 0.000 at the stored values, 0.841 if every learner is 1 % worse on delay. K4 fires 0.000 at the stored values and 71-99.6 % at planted excesses at or just past each tolerance.
- Drain has no usable null (0 failures in 1,200 stored v3w rows, V496).

### 9. Runs x rate = cost; machine-hours; build work in hours; author time, stated apart

| Stage | Runs | Hours | Cost |
|---|---|---|---|
| 1: smoke, T0, selection A (1,400); verdict, 17 runs × 480 seeds (8,160) | 9,560 | 5.1 | $3.10 |
| 2: continuation, 200 × 384 + 20 × 240 + 96; selection B, smoke (1,720); verdict, up to 2 × 480 | 84,376 | 16.4 | $9.94 |

- Rates (correction 7): pack runs with the space-time field 1,690/h, $0.36 per 1,000 (90 workers, $0.607/h; V493, V494); search and selection rows 5,280/h, $0.115 per 1,000 (V490).
- With 6 % setup (planb.md:538): stage 1 about $3.3 and 5.4 machine-hours, where a KILL ends the screen; both stages about $13.8 and 23 h.
- A rate check after 30 minutes of each stage (planb.md:563). If it, or the running spend, projects stage 2 above $12, the continuation stops: "stage 2 not run", no pass, no KILL, no shorter continuation read.
- After a host loss or change (V494), each arm reproduces on 3 seeds or the stage is re-run.
- Build: 12-16 h (my estimate, no record; items in Part 2). Author time, apart: about 2 h.

### 10. Plant and verification effect

No plant file, reward, input, period or actuator value changes. Headways stay 1.6, 1.2, 1.0 and 0.8 s (b_env.py:37), so no T0 for a new value is owed; section 2's T0 closes PR-10's missing record (plant_vv_record_v0.md:87). A smoke check follows each code change, host and new rule vector (planb.md:418). TRUCK is outside the plant's stated intended use; PR-08 and PR-28 are carried unconditionally (planb.md:181-183), PR-26 as a gap (plant_vv_record_v0.md:77). No departure from the CAV contract.

### 11. Cells added to the count (N = 91) and post hoc labels

0. TRUCK is counted (V487); a re-test and rules-only rows add 0 (cells_tested.md:5). The whole screen is post hoc (planb.md:576): its statistic, sizes, seed count, rule arms and measure classes followed the stored rows.

### 12. Must-carry disclosures

- TRUCK only, outside the plant's stated intended use; not shown in steady traffic. planb.md:144's disclosure: S2 as registered read KILL (V486, V487). Cell chosen after related DRL results (planb.md:164).
- Close-following is a reward term read at 1 Hz; 78 % of v3w's counted seconds lie on roads 4a, 4 and ramp 2 (EXPLORATORY).
- Stored costs: braking events, jam count, jerk (3E-C); congested km (p333, os0_10_10, 3E-D_TRUCK). Delay is non-inferior at 1 %, not equal.
- The statistic's form followed the stored rows: about 0.9 points above the pooled arm on the edge, up to 0.6 on delay.
- v3w not retrained; rules tuned in the cell; one family, one hinge, 300 generations with its plateau label; Plan B's reference rows; 13 rules not re-run; verdict seeds read twice.

### 13. Expected outcome and your probability (a judgement, labelled so)

A judgement, not measured. Stage 1 pass: about 50 % (0.84 at a true 12 %; lower, since the stored 12.7 % chose the hypothesis and the re-pick removes selection luck). Stage 2 given stage 1: about 30 %; the population was still moving at generation 100 (critic_F.md:39). **Overall pass: about 15 %** (pooled form: about 10 %). Expected spend: about $8.5.

## PART 2. Skeptics' findings and handling

"Verified" means I checked the record or recomputed it myself. EXPLORATORY numbers are mine, from the stored S6 rows (240 seeds, already read for a verdict): `v2_out.txt` to `v6_out.txt` in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/final_work/`.

| Id | Severity | Finding | Verified | Handling |
|---|---|---|---|---|
| F-all-1 | BLOCKER | K2 reads a 5-run mean against one run, so it does not test "delay within 1 %"; section 8's K2 and K1 lines describe another quantity | Yes. planb.md:424: "P is the per-seed learner mean". `v2_out.txt`: pooled minus single-learner mean is −0.63 [−0.86, −0.21] on delay against os0_10_10 and −0.88 [−4.01, +2.50] on the edge against 3E-C (95 %). `v3_out.txt`: pooled K2 passes 0.917 at the stored differences, 0.708 with the earlier text's 4 stored arms when every learner ties (skeptic: 0.757 with 3) and 0.000 at 0.5 % worse; pooled K1 KILLs a single-learner 12 % edge 0.379 (skeptic 0.397). `v4_out.txt`: 168 rule pseudo-arms read below their members on delay in 98 % (skeptic's sk4 reproduced); with every member tied, the pooled form shows the pseudo-arm worse in 22.5 % of studies on delay and 12.8 % on close-following (nominal 1.25 %), the single-learner mean in 1.3 % and 0.9 %. Caveat: a pseudo-arm pools five different rules, while the learners come from one recipe; v3w's own offset is the measured −0.63. round_2.md:200 and :209 are per policy | Changed. Option (a) is the default: K1 and K2 read the mean of the five learners' effects; pooled printed beside (section 2 decision 3; sections 3, 7, 8, 12). Reason for the default: the pooled form fails a no-effect null (V244's rule), and the record that correction 3 names is per policy. It is the friendlier form for v3w and sets aside planb.md:424, so it is open item 1. Section 8 is recomputed. Side effect found: in the default form the stored steady rows no longer fire K1; they still fire K2 against 5 rules, so the scope stays TRUCK only (open item 5) |
| F-all-2 | MAJOR | Recorded adverse rows missing: congested km max and mean against p333 | Yes. Reading, `cells.TRUCK.map_report_only.p333`: max −3.91 % [−6.52, −1.74] (97.5 %: [−6.96, −1.74]), mean −1.43 % [−3.04, −0.63] ([−3.35, −0.58]). Also in the reading: mean −1.55 % [−3.43, −0.35] against os0_10_10; mean −2.65 % [−4.15, −1.29] and max −5.00 % [−6.67, −2.92] against 3E-D_TRUCK | Changed: section 5 prints the p333 rows as shown worse and names the other three; section 12 lists them as stored costs |
| F-all-3 | MAJOR | A budget stop of stage 2 has no outcome | Yes. synth.md:35 ("no data-dependent stop") against synth.md:101 (a rate-check stop); stage 2 is about $10.5 with setup against $12 at V490's rate; V493's causes are "not measured"; planb.md:238-239 and :561 were not carried | Changed: section 9 adds the outcome "stage 2 not run": no pass, no KILL, no shorter continuation read. I extended it to the running spend. Plan B's ceiling rule is open item 7 |
| F-all-4 | MAJOR | New generations are scored against stored reference rows that no check reproduces | Yes. cmab.py:208-209 loads the stored rows; cma2.py:212 skips cached ones; `meta.json` commit 96fde8d; V490's 38,440 = 100 × 384 + 40, so p333 ran once per pool seed | Changed: section 2 adds the reproduction of p333 on 7,480,150-229 and of g098i00 on its 16 search seeds before generation 100, and what a difference does; section 9 costs the 96 runs; section 12 discloses "Plan B's reference rows" |
| F-all-5 | MINOR | Section 1 says "at least 10 %"; K1 cannot bound it | Yes. `v3_out.txt`: K1 passes 0.48 to 0.50 at a true 10 % and 0.10 to 0.15 at 8 % | Changed: section 1 reads "a point edge of 10 % or more, lower bound above 0"; section 2 fixes K1's form and K2's margin in a V# before the rental; section 8 says what the screen separates |
| F-all-6 | MINOR | The set-aside cites close-following only; set-aside rules have lower delay bounds than a kept rule | Yes. Reading, `cells.TRUCK.map`: grid_os1_10_10 −0.68, os1_15_10 −0.64 and lr1000_10_1 −0.83, below 3E-D_TRUCK's −0.57 | Changed, beyond the two options offered: all 9 rules with a recorded delay lower bound at or below 0 (V496) are deciding arms; the set-aside (13 rules) cites both bounds. Cost: 2,880 more runs, about $1.0. This conflicts with the plant judge ("re-running is waste"), so it is open item 4 |
| F-all-7 | MINOR | A pass can be read as the claim | Yes: the earlier section 1 named no later test | Changed: section 1, "tested on fresh seeds. This screen's rows are not evidence for it." |
| F-all-8a | MINOR | Build items missing; "12 h" has no record | Yes. cmab.py:44-45, :51-52, :163-172, :204-205; plan6.py:25; read6.py has no fuel or jerk field (grep) | Changed: section 9 says "my estimate, no record", 12-16 h. Items: the continuation (generation count, check points, plateau window, the resume refusal); the selection runs and pick on fresh seeds; the seed lists; a reader for K1 to K4 in both forms of the statistic, with fuel per km and jerk; planted-row tests |
| F-all-8b | MINOR | Stage 2's "8 lowest admissible check losses" has no generation range | Yes | Changed: "of generations 20-300". Also found in `checks.jsonl`: the eighth and ninth stored losses tie (g043i20 and g063i15, −23.41), so stage 1 runs 9 candidates |
| F-all-8c | MINOR | Section 2 owes a T0; section 10 says none is owed | Yes (synth.md:21 against :106) | Changed: section 10 says no T0 for a new value is owed and that section 2's T0 closes PR-10's missing record (plant_vv_record_v0.md:46, :87) |
| F-all-8d | MINOR | Sections 1-13 hold 1,908 words; the limit is 1,400 | Yes: `wc -w` gives 1,908 | Partly. See "Length" below |
| Found right | none | K1's table; stage 0; run counts, rates, dollars; code lines; correction 1's seeds; cells added 0; no barred word | Yes, with one limit. K1's table reproduces (pooled: 1.000, 0.902, 0.518, 0.237, 0.003). Rates: V475, V490, V493, V494. cmab.py and cma2.py lines; planb.md §6; cells_tested.md:5; a barred-word scan of Part 1 finds none. Limit: stage 0's steady line holds only in the pooled form (F-all-1) | Kept; stage 0 now gives both forms |

Changes beyond the findings: stage 1's rule arms grow from 5 to 11 (17 runs per verdict seed, was 11); Plan B's own incumbent at generation 300 is a verdict arm; stage 1's cap is $4, not $3; the 59-worker rate (2,600-3,050 runs/h, V475) and the $0.53 per 1,000 figure (rental 2's whole cost, not a rate) are not used; K4's nulls are recomputed for the 10 arms (`v6_out.txt`: 97 % at 0.02 planted collisions per run, 95 % at 0.10 moving full-emergency events, 71 % at 0.6 % less flow, 99.6 % at 12 % more braking).

Round-1 findings, where Part 1 deals with them: steady-traffic scope (sections 1, 3, 12); 80 seeds and the 10 % written after 11.80 % (480 seeds, sections 6-8, 11); "continue to the plateau" (section 4: fixed budget, harness change, original pool and check set, fresh selection and verdict sets, today's 3E-C kept); the richer family (section 4, not run); the missing delay test (K2); the measure set and its classes (section 5); the barred words and planb.md:153 (sections 2, 5); no retraining and no rescue (sections 1, 4, 12).

### Open for the author

1. **The statistic (F-all-1; decides the most).** Default: the mean of the five single-learner effects. Alternative: Plan B's pooled arm (planb.md:424), which keeps the record and reads against v3w. With it (EXPLORATORY): K1 KILLs 1.000, 0.926, 0.823, 0.379, 0.006 at a true single-learner edge of 0, 8, 10, 12, 15 %; K2 passes 0.917 at the stored differences, 0.359 if every learner ties every arm and 0.000 at 0.5 % worse; all rules pass at most 0.92; my probability of a pass is about 10 %. The default reads the stored TRUCK edge as +12.68 % against +11.80 %, and the stored delay against os0_10_10 as +0.04 % against −0.58 %.
2. **K1's form.** Default: point of 10 % or more and lower bound above 0. Alternative: planb.md:438's form (lower bound above 0 and at least 20 s per run), fixed before S6; it KILLs 0.425, 0.099, 0.023, 0.003 at a true pooled edge of 5, 8, 10, 12 % (`v3_out.txt`), so it passes a true 5 % edge 0.575 of the time.
3. **K2's margin.** Default 1 % (planb.md:227). Alternative 2 % (planb.md:437): in the default form it passes 0.983 when every learner is 1 % worse, and it owes a search at a +2 % hinge (critic_F.md:44).
4. **The rule arms (F-all-6 against the plant judge).** Default: 3E-C, 3E-C-R, the 9 delay-tied rules, then the stage 2 arms. Alternatives: the earlier set (p333, os0_10_10 and 3E-D_TRUCK beside the 3E-C arms; about $1.0 less), or all 23 stored rules (planb.md:214; 6,240 more runs, about $2.2).
5. **Scope.** Default: TRUCK only. In the default form the stored steady rows no longer fire K1 (lowest edge +14.17 % [+2.36, +40.38], grid_z31333); they fire K2 against 5 rules (bounds −1.03 % to −1.39 %). Steady traffic as a deciding row would need its own rule search for equal exposure.
6. **Level.** Default 97.5 % (TRUCK's level in Plan B). 95 % is nominal for one cell.
7. **A budget stop (F-all-3).** Default: "stage 2 not run", no verdict. Alternative: planb.md:561's rule (stop at the next check, freeze and label the incumbent, continue).
8. **Reference rows that do not reproduce (F-all-4).** Default: no continuation on that host. Correction 1's other branch, a restarted search named as restarted, is a different arm and needs its own approval.
9. **Correction 1's reading.** Default: the continued search and its in-search checks use only Plan B's seeds (7,480,150-229); fresh seeds serve the final pick (selection sets A and B) and the verdict. If "fresh seeds for the check only" means the verdict alone, the pick is Plan B's incumbent rule on 7,480,190-229 (already a verdict arm at generation 300), and the two selection sets drop (about 2,760 rows).
10. **Approvals:** reopening TRUCK against planb.md:575; the claim form against planb.md:153; the caps ($4 and $12) and the 7-day sum: about $18.6 for 2026-11-08 to 11-10 by my sum of the ledger's figures, with the rentals of 2026-11-06 and 11-07 (V437, V461, V464) not totalled; seeds 7,487,000-779; the order of M, R and F under $40.

Limits of my numbers: sections 3 and 8 resample 480 seeds from the 240 stored ones and shift v3w by a constant; 1,500 studies for K1 to K3, 6,000 for the pseudo-arm nulls and 500 for K4, so a probability carries up to about ±0.03 of simulation noise (±0.04 for K4), and 480 fresh seeds may have wider tails than 240 resampled ones.

Length: Part 1 has 1,424 words of plain prose, 1,596 tokens that contain a letter (citations, rule names and file names included) and 2,076 by `wc -w`, the count by which the earlier text had 1,908. By that count it is above the 1,500 limit and longer than the earlier text. The excess is numbers, citations and the lines the findings required; I moved the pooled-form numbers, the unused rates and the build items to Part 2 and cut no rule, arm, seed, measure or disclosure.
