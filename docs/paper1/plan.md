# Article 1 skeleton (DRAFT, 2026-11-07)

Plan for `docs/paper1`: the plant, the method and the decision map (V457). Built by two ultracode workflows (inventory, two framings, judge, two adversarial verifiers; then a fixer and a checker, whose 14 remaining items were applied by hand), with the author picks V462 and the correction V463. Round-2 results are not in it: slots marked [round 2] are filled after the test (expected 2026-11-08). Nothing here is a claim.

## Framing

Question first. The article asks RQ3 of docs/thesis/outline_v1.md §2: where, on which measures and by how much do per-CAV DRL policies beat, tie or lose against tuned rule controllers and against no control? It asks this for one actuator: each ALKS is given a time headway of 1.6, 1.2, 1.0 or 0.8 s (HEADWAYS_S in docs/research/baseline_v1/constants.json).

Two method parts serve the question.
(i) The instrument: r2m3 with plant_c3 on SUMO 1.27.1, documented in a systems-engineering V&V record against one stated intended use (docs/testing/plant_vv_record_v0.md, draft, 'not yet reviewed or approved'; tally at commit 6a940b3: 6 met, 13 partial, 7 gap, 2 limit). The target standard is 'verified and validated for its intended use', never 'proven' (V456). Under V462(3) the article does not use 'verified and validated' in any title, abstract or claim sentence until the record is reviewed and PR-15, PR-24 and PR-28 are closed. Every requirement that is partial, gap or limit, plus the record §4 limits, is a numbered limit L1-L27 (field 'limits'). Every claim sentence says 'within limits L1-L27'.
(ii) The reading: a protocol fixed before round 2's evaluation data (round_2.md, approved in V454; the V462 tile rule and claim wording followed after validation rows existed and before any test row, V463). Round 2's T2 decides the comparison with tuned rules: at least 4 of 5 policies must beat every counting opponent, including a CMA-ES rule wherever one counts. The V459 bar decides the comparison with no control, with confirmatory 3's no-control clause beside it. Map tiles follow the descriptive 95 % rule of V462(1) and decide nothing.

A short section uses the decision ledger to show where plant checks and protocol elements changed a conclusion, or kept a pre-registered verdict apart from post-hoc statements (RQ2/C2).

W, G and N are three answers to the same question, given one sentence per cell (outline_v1.md §3 as amended by V462(2), commit 6a940b3). So the article stands whatever round 2 shows (V457). If the outcome is N, it is reported as the answer (V456).

Conventions:
- One sign convention: common.raw. Positive means the controller under test has less delay, close-following or braking, or more flow (round_1_result.md §1; conf3/common.py raw()). Numbers from V448, V449, V461, the cma3e final.json files and round_2.md's 3E-T table are converted, and each conversion is stated (V452). Every number carries its CI level and seed count.
- Every result sentence quotes, verbatim, confirmatory_3.md's model sentence, no-control clause and 'What this cannot show' items, plus round_2.md's 'Sentences allowed' and 'What this cannot show' (outline §3).
- TTC below 3 s is called 'close-following'. It is a surrogate, and on this plant it is mostly a low-speed queue (confirmatory_3.md Metrics).
- Rows outside the record's intended use say 'outside the plant's stated intended use' (V462(4)): the band, 3E-T's condition T, and history panel C's H1 and H2.
- No 'first', 'novel' or 'proven'. No claim of a gap in the literature until a systematic search exists. Every literature item is [VERIFY] with its read level, because none is recorded as read in full by the author.
- 'Per-CAV' names the baseline architecture. Claim sentences say 'these per-CAV PPO policies', never 'per-CAV DRL' as a method.

Timing: no round-2 test row exists yet. Validation started at 17:06 on 2026-11-07 (V461). outline_v1.md line 5 expects round 2's data on 2026-11-08, and no file gives a time of day. Drafting now: sections 1-4, section 5 apart from rows M5, M7 and M9, and sections 7.2-7.7. Waiting for round 2: sections 0, 6, 7.1 and 8.

## Title options (open decision)

- Win, tie or lose: per-CAV PPO headway policies against tuned rule controllers on a simulated freeway with two on-ramps
- Does learning pay over tuned rules for automated-vehicle headway control? A two-cell decision map from a protocol fixed before data
- Comparing learning and tuned rules for automated-vehicle headway control: a V&V record with numbered limits, a protocol fixed before data and a two-cell decision map
- Per-CAV deep reinforcement learning against tuned rules for ALKS time headways under two freeway slowdowns: a comparison fixed before data

## Contributions

- C3, the answer (RQ3): a two-cell decision map with report-only band and history panels (V462(2)), for per-CAV PPO headway control on r2m3 with plant_c3.
  - Decision cells: X1 and X2 at 5,300 veh/h, on 40 test seeds 7,440,840-879, used once (round_2.md Seeds). Both cells were chosen after earlier rounds in which DRL already looked best there, and this is disclosed (confirmatory_3.md and round_2.md Disclosures).
  - Measures: the deciding and side measures of T2. These are close-following seconds at TTC below 3 s; all-vehicle delay including the insertion queue; flow; braking at 3 m/s² counted every 0.1 s; moving full-emergency events; and collisions. Every other counter in confirmatory_3.md §Metrics goes in T15: TTC below 1.5 and 2 s, severe samples, braking at 4.5 and 7 m/s², free-road ALKS braking, fuel, jerk, undertakes, lane-end stops at both ramps and ramp delays. Fuel carries its emission-class disclosure.
  - Opponents:
  - no control;
  - the fixed 0.8-s rule p333;
  - confirmatory 3's grid: 6 tuned forms with 69 rules, plus the copy rule, entering as 12 rule arms with p333 and the copy rule included;
  - 3E-T, named 'a rule tuned by CMA-ES under the training slowdowns, not for this cell';
  - 3E-X1 and 3E-X2, named 'a rule tuned by CMA-ES for this cell on separate seeds' (round_2.md Naming).
  - Tiles, per cell, measure and opponent: the arm effect with its 95 % CI (common.raw), a descriptive W/T/L glyph by V462(1), side-limit markers, and the count of single policies meeting W. No tile is a verdict. A separate strip per cell gives T2's outcome (W, G or N, outline §3) and the V459 reading.
  - Report-only panels, hatched, with no verdict:
  - the band, 4,500-6,000 veh/h under the training slowdowns, outside the plant's stated intended use;
  - confirmatory 3's map cells for baseline-v3, whose H1 and H2 are outside the plant's stated intended use.
  - Beside the map: the replication history of X1 and X2, failed replications included (V359, V395, V401, V449/V452).
  - If the outcome is N, it is reported as the answer (V456). Everything holds within limits L1-L27.

- C2, the reading (RQ2): an evaluation protocol fixed before round 2's evaluation data (round_2.md, approved in V454; the V462 tile rule and claim wording followed after validation rows existed and before any test row, V463). Round 2's T2 decides 'beats tuned rules', and the V459 bar decides 'beats no control'.
  Elements:
  - paired seeds from an approved block (V354);
  - effect = sign × median(P − O) / median(O) × 100 over paired seeds, with a percentile bootstrap of the paired differences: 20,000 resamples, denominator fixed (common.py raw());
  - Bonferroni at a test used once; validation at 95 % without correction, because it selects;
  - harm read at 95 %;
  - a 2 % point delay filter against p333 that decides which opponents count, with a 5 % non-inferiority bound reported beside it (D11);
  - opponents tuned on separate seeds, including one CMA-ES search per decision cell, each reported with its counting status, its drop from tuning to test seeds and its convergence;
  - fresh seeds every round; frozen code; traced runs equal to untraced runs; braking counted every 0.1 s;
  - no-effect nulls where they were computed, all under the V244 principle: confirmatory 3 [A2] (0 of 3,000 no-effect resamples passed), the collapse check (null at most 0.027, measured on hand-scaled learners) and round 2's T1 path (b) (0 of 1,000 null resamples of round 1's rows passed);
  - no null yet, and this is disclosed, for the 10 % no-control delay bar (V419, an exploratory sweep outside the plant's stated intended use, suggests it cannot discriminate on this plant), the 2 % counting filter, the 2 %, 10 % and 20-per-run margins, or the V462(1) tile rule;
  - sentences fixed before data (round_2.md 'Sentences allowed'; outline §3 as amended by V462(2)).
  With it comes the ledger of where an element changed a conclusion or kept a pre-registered verdict apart from post-hoc statements: V244, V367, V377, V386, V396, V401, V405 and V452, plus V99 from the earlier metering line (M25).

- C1, the instrument (RQ1): a systems-engineering V&V record for r2m3 with plant_c3 (docs/testing/plant_vv_record_v0.md, draft, 'not yet reviewed or approved'), written against one stated intended use. The plant is a 6.8-km synthetic three-lane freeway with two single-lane on-ramps and 50 % ALKS, run in SUMO 1.27.1.
  - 28 requirements, PR-01 to PR-28. Each has a verification method (I, A, D or T), evidence, a status and traceability to the claim elements (record §3).
  - Tally at commit 6a940b3: 6 met, 13 partial, 7 gap, 2 limit.
  - V462 re-graded PR-17 to partial: on plant_c3, no control had 1 collision in 40 runs in round 1's X1 test (docs/research/round1/report/test_table.csv, collisions_total 1.0).
  - V462 re-graded PR-20 to partial: the 3E-X meta.json has 'commit': null (V461), and round 2 resumes rows without a config hash (V455).
  - The first draft had 8 met, 11 partial, 7 gap, 2 limit.
  - 27 numbered limits, L1-L27:
  - one per requirement that is partial, gap or limit (22);
  - PR-09 and PR-14, whose 'met' status carries a stated limit;
  - three record §4 items that have no requirement.
  Every claim sentence cites them.
  - 'Verified and validated' is not claimed until the record is reviewed and PR-15, PR-24 and PR-28 are closed (V462(3)). The counts and the limit numbering change when that happens.

## Abstract templates (one per outcome, outline §3)

**W.** Where, on which measures and by how much do deep reinforcement learning (DRL) policies that set the time headway of each automated car (per-CAV control) beat, tie or lose against tuned rule controllers and against no control? We answer on r2m3, a synthetic 6.8-km three-lane freeway with two on-ramps and 50 % automated cars (ALKS), simulated in SUMO 1.27.1. A systems-engineering V&V record documents the plant against one stated intended use: comparing controllers that set ALKS time headways. Its open items are stated as numbered limits, and every result below holds only within limits L1-L27. Under a protocol fixed before data, five per-CAV PPO policies choosing among 1.6, 1.2, 1.0 and 0.8 s [and up to two finalists from 7 candidate changes, selected on 40 validation seeds] were tested once, on 40 fresh paired seeds, under two tapered slowdowns at 5,300 veh/h. Their opponents were no control; a fixed 0.8-s rule; a grid of rules tuned per slowdown on separate seeds; a rule tuned by CMA-ES under the training slowdowns, not for this cell; and, per cell, a rule tuned by CMA-ES for this cell on separate seeds. An opponent counted only if its delay was at most 2 % above the fixed rule's (point estimate). Model: an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds. In [cell], these per-CAV PPO policies had [x] % less close-following [CI] than every counting rule (p333 fixed, the others tuned on separate seeds), including [3E-X: a rule tuned by CMA-ES for this cell on separate seeds | 3E-T: a rule tuned by CMA-ES under the training slowdowns, not for this cell], with delay, flow and the other side measures within the pre-registered limits; it tied or lost elsewhere: [map]. This is a surrogate. [Then confirmatory_3.md's sentence-table row 'Cell won on TTC', verbatim, filled from T2, with its [Where the gain is]: the share on 4a plus ramp 2, and the follower-speed split.] [Other cell: its own outline §3 sentence, W, G or N.] Against no control (V459 reading), delay was [y] % lower [CI at T2's level], and close-following was [not harmed | harmed] under round 2's harm rule. No control had [a] seconds at TTC below 3 s, [b] vehicle-seconds of delay and [c] vehicle-seconds of braking at 3 m/s² per run[; no control had fewer such seconds, at [y'] % more delay]; collisions, which are too rare to compare: [counts per 40 runs]. Across 4,500-6,000 veh/h under the training slowdowns (report-only, outside the plant's stated intended use), close-following against no control ranged over [range] (95 %, 20 seeds). Any win holds for this uncalibrated SUMO model, these slowdowns, these demand levels and ideal V2V. A null on 7 candidates in one round does not show that no other change would help. Without D4, beating 3E-T does not show that a rule tuned per cell would be beaten. With D4, it shows this for one 40-generation search per cell. If that search has not converged, 3E-X is a lower bound on a per-cell tuned rule. It says nothing about other actions, other networks, other spacings or real traffic. 4 of 5 is a statement about these trained policies, not the method in general. A rule outside these families could still match DRL. TTC below 3 s is a surrogate, and this model is not calibrated, so a win is not a safety result for real traffic. Only 2 conditions decide the claim. We report in full the two-cell decision map with its report-only band and history panels, the protocol, and where its elements changed earlier conclusions.
[Fill notes:
- [x] is the range over the passing policies against the strongest counting rule, in common.raw (positive = fewer close-following seconds), with the CI at T2's Bonferroni level (97.5, 98.75 or 99.17 %).
- The bracketed no-control phrase appears only when at least 4 of 5 policies are clearly worse on TTC (confirmatory_3.md).
- Write 'safety' only if the severe-conflict check passes.
- If the arm is sw, tail, rep or 1B, use its round_2.md naming. sw is never called 'per-CAV PPO headway policies'.
- Both 3E-X searches were still falling at generation 40 (final.json), so state that 3E-X is a lower bound, in section 6.3.]

**G.** Where, on which measures and by how much do deep reinforcement learning (DRL) policies that set the time headway of each automated car (per-CAV control) beat, tie or lose against tuned rule controllers and against no control? We answer on r2m3, a synthetic 6.8-km three-lane freeway with two on-ramps and 50 % automated cars (ALKS), simulated in SUMO 1.27.1. A systems-engineering V&V record documents the plant against one stated intended use: comparing controllers that set ALKS time headways. Its open items are stated as numbered limits, and every result below holds only within limits L1-L27. Under a protocol fixed before data, five per-CAV PPO policies choosing among 1.6, 1.2, 1.0 and 0.8 s [and up to two finalists from 7 candidate changes, selected on 40 validation seeds] were tested once, on 40 fresh paired seeds, under two tapered slowdowns at 5,300 veh/h. Their opponents were no control; a fixed 0.8-s rule; a grid of rules tuned per slowdown on separate seeds; a rule tuned by CMA-ES under the training slowdowns, not for this cell; and, per cell, a rule tuned by CMA-ES for this cell on separate seeds. An opponent counted only if its delay was at most 2 % above the fixed rule's (point estimate). Model: an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds. [Cell]: Won against confirmatory 3's grid, not against the CMA-ES rule [name]: [limits missed]. | [Cell]: The CMA-ES-tuned rule [name] did not meet the delay filter in [cell]: [delay and close-following against p333]. Against that rule the question reads 'not answered against the CMA-ES rule: not within the delay filter'. [Then the confirmatory 3 sentence-table row for the rules that counted, naming only those rules.] We do not claim that these policies beat tuned rules on this plant. Against no control (V459 reading), delay was [y] % lower [CI at T2's level], and close-following was [not harmed | harmed] under round 2's harm rule. No control had [a] seconds at TTC below 3 s, [b] vehicle-seconds of delay and [c] vehicle-seconds of braking at 3 m/s² per run[; no control had fewer such seconds, at [y'] % more delay]; collisions, which are too rare to compare: [counts per 40 runs]. Across 4,500-6,000 veh/h under the training slowdowns (report-only, outside the plant's stated intended use), close-following against no control ranged over [range] (95 %, 20 seeds). Any win holds for this uncalibrated SUMO model, these slowdowns, these demand levels and ideal V2V. A null on 7 candidates in one round does not show that no other change would help. Without D4, beating 3E-T does not show that a rule tuned per cell would be beaten. With D4, it shows this for one 40-generation search per cell. If that search has not converged, 3E-X is a lower bound on a per-cell tuned rule. It says nothing about other actions, other networks, other spacings or real traffic. 4 of 5 is a statement about these trained policies, not the method in general. A rule outside these families could still match DRL. TTC below 3 s is a surrogate, and this model is not calibrated, so a win is not a safety result for real traffic. Only 2 conditions decide the claim. We report in full the two-cell decision map with its report-only band and history panels, the protocol, and where its elements changed earlier conclusions.
[Fill notes:
- No margin against the grid appears in any G sentence. The grid margin goes only in T8's 'T2 without 3E' column, labelled as a comparison with round 1 (round_2.md).
- No sentence says the cell was won.
- A cell where no 3E rule counts does not close (D10).]

**N.** Where, on which measures and by how much do deep reinforcement learning (DRL) policies that set the time headway of each automated car (per-CAV control) beat, tie or lose against tuned rule controllers and against no control? We answer on r2m3, a synthetic 6.8-km three-lane freeway with two on-ramps and 50 % automated cars (ALKS), simulated in SUMO 1.27.1. A systems-engineering V&V record documents the plant against one stated intended use: comparing controllers that set ALKS time headways. Its open items are stated as numbered limits, and every result below holds only within limits L1-L27. Under a protocol fixed before data, five per-CAV PPO policies choosing among 1.6, 1.2, 1.0 and 0.8 s, and 7 candidate changes to them were screened on 40 validation seeds; v3w [and up to two finalists] were then tested once, on 40 fresh paired seeds, under two tapered slowdowns at 5,300 veh/h. Their opponents were no control; a fixed 0.8-s rule; a grid of rules tuned per slowdown on separate seeds; a rule tuned by CMA-ES under the training slowdowns, not for this cell; and, per cell, a rule tuned by CMA-ES for this cell on separate seeds. An opponent counted only if its delay was at most 2 % above the fixed rule's (point estimate). Model: an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds. On this plant, these per-CAV PPO policies (v3w[, finalists]) did not beat the strongest counting rules; the DRL claim against tuned rules closes in [cells]. In [cells], where a CMA-ES rule counted, [k] of 5 policies met T2, against the 4 required; the limits missed were [list]. Round 1's win against the grid alone is reported beside it (v3w, 5 of 5 policies; X1 against p333 only, X2 against p333 and os1_15_10; seeds 7,440,500-539, 97.5 %). Against no control (V459 reading), delay was [y] % lower [CI at T2's level], and close-following was [not harmed | harmed] under round 2's harm rule. No control had [a] seconds at TTC below 3 s, [b] vehicle-seconds of delay and [c] vehicle-seconds of braking at 3 m/s² per run[; no control had fewer such seconds, at [y'] % more delay]; collisions, which are too rare to compare: [counts per 40 runs]. Across 4,500-6,000 veh/h under the training slowdowns (report-only, outside the plant's stated intended use), close-following against no control ranged over [range] (95 %, 20 seeds). Any win holds for this uncalibrated SUMO model, these slowdowns, these demand levels and ideal V2V. A null on 7 candidates in one round does not show that no other change would help. Without D4, beating 3E-T does not show that a rule tuned per cell would be beaten. With D4, it shows this for one 40-generation search per cell. If that search has not converged, 3E-X is a lower bound on a per-cell tuned rule. It says nothing about other actions, other networks, other spacings or real traffic. 4 of 5 is a statement about these trained policies, not the method in general. A rule outside these families could still match DRL. TTC below 3 s is a surrogate, and this model is not calibrated, so a win is not a safety result for real traffic. Only 2 conditions decide the claim. We report in full the two-cell decision map with its report-only band and history panels, the protocol, and where its elements changed earlier conclusions.
[Fill notes:
- Edge case, a cell where no CMA-ES rule counts. D10 says that cell does not close, so drop the closing clause for it. Write 'The CMA-ES-tuned rule [name] did not meet the delay filter in [cell]: [delay and close-following against p333].', name only the rules that counted, and add the confirmatory 3 sentence-table row that applies ('Replication yes, tuned no' or 'Neither reading').
- Never attribute the change from round 1 to the CMA-ES rule. That sentence would rest on T2 without 3E, which round_2.md forbids.
- If a finalist is sw, tail, rep or 1B, use its round_2.md naming beside 'these per-CAV PPO policies (v3w)'.]

## Sections

### 0 Abstract (about 400 words)

Purpose: State the question, the instrument, the reading and the answer for each outcome, with the binding sentences quoted verbatim.

- Fill one of the W, G or N templates after round 2, one outcome sentence per cell (outline §3 as amended, V462(2), commit 6a940b3).
  - Mixed outcomes, such as W in X2 and N in X1, get one sentence each.
  - A cell where no CMA-ES rule counts uses round_2.md's fixed sentence and does not close (D10).
- Mandatory and verbatim:
  - confirmatory 3's model sentence;
  - the V459 reading, with confirmatory 3's no-control clause beside it: no control's TTC, delay and braking; 'no control had fewer such seconds, at [y] % more delay' when at least 4 of 5 policies are clearly worse on TTC; and 'collisions, which are too rare to compare';
  - the 'What this cannot show' items of confirmatory_3.md and round_2.md;
  - 'within limits L1-L27'.
- Never write:
  - 'verified and validated' (V462(3)), until the record is reviewed and PR-15, PR-24 and PR-28 are closed;
  - 'proven';
  - 'safe' or 'safety' without the severe-conflict check;
  - 'first' or 'novel';
  - a margin against the grid in a G sentence (round_2.md);
  - any sentence that rests on T2 without 3E;
  - an opening sentence about what the literature 'rarely' does.
- Each number states:
  - its convention: common.raw, positive = the policies better;
  - its CI level: T2's Bonferroni level is 97.5, 98.75 or 99.17 % for 0, 1 or 2 finalists; the V459 delay half is read at T2's level and harm at 95 %; the band at 95 %;
  - its seeds: 40 test seeds 7,440,840-879, or 20 band seeds 7,440,880-899.
- Take the limit count from the record version current at submission: today 27 (L1-L27). The verbatim items make the abstract about 400 words, which may exceed a venue limit (open decision).

Inventory ids: M15, M23, R18, R22, P9, P20

### 1 Introduction: the question (about 950 words)

Purpose: Pose RQ3 as the article's question. Say what the reviewed studies report, why the answer depends on the instrument and the reading, preview the answer and list the contributions.

- Para 1, the question (RQ3, outline_v1.md §2), asked for one actuator. Each ALKS is given 1.6, 1.2, 1.0 or 0.8 s. The command acts only behind another ALKS within 150 m, with the same leader on two consecutive updates (P15).
- Para 2, what the reviewed studies report. This is not a systematic search (prior_art_A_v0.md §5), and the sample is mostly ramp-metering studies, not per-CAV headway control. Each item names its actuator and keeps its read level, and all are [VERIFY].
  - L2, Vinitsky et al. 2018, RL-controlled AVs at a bottleneck: RL 'matches the performance of feedback ramp metering', against a meter 'tuned empirically'. 10 RL runs, 20 meter runs, no CIs. Read level FT-kw.
  - L1, Vinitsky et al. 2023, multi-agent RL AVs: at 40 % AVs, RL 'equals' a traffic-light controller. Agent FT of arXiv v1; the TCPS version was not read.
  - L57, Belletti et al. 2018, RL ramp metering: matches an ALINEA 'calibrated by traffic engineers' (congested-period TTS 10,575 against 10,514 veh·h). Agent FT; venue [VERIFY].
  - L58, Liu et al. 2020, DRL ramp metering. Against no control, negative = less time: peak median mainline travel time −20 % for DRL and −11.7 % for a fine-tuned PI-ALINEA, 20 seeds. The metric is mainline only, and the evaluation reuses the training demand. Agent FT.
  - L8, Elmorshedy 2023, PPO sets ACC headways every 10 s (100 % ACC, Aimsun): 27.24-32.43 % less total delay than the best static 0.8-s headway (reductions as reported). Ramp delay rose by 120.97 % and 115.60 % against 0.8 s in the single-merge network (positive = more ramp delay; 2023_Elmorshedy.md, Ch. 3 table). No seeds, CIs or test split. Agent read of the thesis text.
  - Field tests: MARVEL (RL variable speed limits) reports no measured mobility effect (L17, agent FT). CIRCLES has no quantified peer-reviewed outcome (L16, agent FT of arXiv v1).
- Para 3, why the answer depends on the instrument and the reading.
  - A survey says that 'offline-trained RL performance is highly reliant on the accuracy of the training simulator' (L70, ABS, [VERIFY]).
  - In this project, P0 hid hard braking from every 1-Hz metric: on seeds 7,419,640-641 at 5,300, 1,749 and 972 vehicle-s of ALKS braking at 7 m/s² or harder (V367).
  - A won cell did not replicate: X2, 1 of 5 policies on 20 fresh seeds 7,440,220-239 (V401).
  - Statements were withdrawn on verification or review (V396, V405, V452).
  Section 5 gives the details.
- Para 4, what we do.
  - The plant is r2m3 with plant_c3, within limits L1-L27.
  - The opponents are no control, p333, confirmatory 3's grid, 3E-T and the per-cell CMA-ES rules 3E-X1 and 3E-X2, each with its round_2.md naming.
  - The verdicts are T2 and the V459 bar. The tiles are descriptive (V462(1)).
  - The test runs once, on 40 fresh paired seeds 7,440,840-879.
  - Order of events: round_2.md was committed at c1bf797 before any round-2 candidate was evaluated, and its approval was read from the author's 'Go on' (V454). The 3E-X picks ran on a rented machine and passed check 1 (V461). Validation started at 17:06 on 2026-11-07. The tile rule and the outline wording were fixed after the validation rows existed and before any test row (V462).
  - Section 4.3 lists every timing disclosure.
- Para 5, the answer: one outline §3 sentence per cell [W | G | N, filled after round 2], with the model sentence, 'within limits L1-L27', confirmatory 3's no-control clause, and confirmatory_3.md's and round_2.md's 'What this cannot show' items, verbatim. A null is the answer 'no, not on this plant' (V456), and the article stands whatever the outcome (V457).
- Para 6, the contributions C3, C2 and C1, labelled as in outline_v1.md §2, and a roadmap of the paper. Wording rules:
  - no 'first' or 'novel';
  - 'close-following', not 'safety', unless the severe-conflict check passes;
  - no 'gap in the literature';
  - no 'verified and validated' (V462(3)).

Inventory ids: L1, L2, L8, L16, L17, L57, L58, L70, M1, M15, M25, P15, R10, R16

### 2 Related work: learned and rule-based per-CAV control, and how their claims are evaluated (about 1050 words)

Purpose: Place the question among learned and non-learning CAV controllers and among evaluation practices. Use only works recorded in the repo, each with its read level and [VERIFY], and make no claim that something is absent from the literature.

- Rule for the whole section, stated once at its head. No item below is recorded as read in full by the author, so every item carries [VERIFY] and its read level as the repo records it: FT (full text, read by a research agent), FT-kw (checked by keyword), PART, ABS, SNIP, REC, secondary, DEV (developer statement) or not read. Agent reads are written 'read in full by a research agent (FT), [VERIFY]', never 'read in full'.
- 2.1 Learned per-CAV control in mixed traffic.
  - Flow and its benchmarks: L3 (FT per prior_art_B, FT-kw per prior_art_A) and L4 (ABS). Flow's last master commit is from 2020-12-11, and its docs state it is incompatible with current SUMO; this bears on reproducibility.
  - The Wu 2018 and Kreidieh 2022 theses (L6, L7; agent reads of the thesis text) compare RL against humans or against a rule calibrated at one density, with no CIs.
  - L2 (FT-kw); L1 (agent FT of arXiv v1); Yan et al. 2023 (L5, FT-kw).
  - Elmorshedy 2023 (L8, agent read): PPO sets the ACC headway every 10 s, and the learned policy works as ramp metering.
  - Shi 2025 (L9, agent read of Ch. 1 and 4-6): ALINEA layered on the learned drivers changes TTT by −2.9 to +7.2 % across four demand levels (the reviewer's arithmetic, negative = lower TTT).
  - Multi-agent RL at on-ramps: L21 (agent FT) and L22 (agent HTML extract).
  - The move to field tests: L10 (REC and SNIP), L15 (agent FT), L16 (agent FT of arXiv v1) and L17 (agent FT).
- 2.2 Non-learning per-CAV comparators.
  - FollowerStopper and PI with saturation (L26, agent FT). An optional sentence, to drop if space is short: on an archived branch, the ring constants with 25 % CACC had 119-180 % more delay than no control on the LD3 lane-drop plant. This is not r2m3; positive = more delay (literature_v0.md lines 800 and 839, citing docs/lab/round4_th.md on claude/v5b-core).
  - Hayat 2023 (L27, agent FT of arXiv v1); Kesting 2008 (L31, metadata only, not read); Davis 2007 (L33, agent FT); Scarinci 2015, with 30 seeds per flow (L34, agent FT); FHWA-HRT-21-008 (L28, relevant chapters, agent); Ghiasi 2019 (L29, ABS); Malikopoulos 2019 (L30, ABS, author list differs between sources).
  - The ACC base model (L32, secondary only), with field ACC evidence as a counterweight (L42 and L43, tagged FT in a source list, claims not checked).
  - Čičić 2019 and 2022 (L36 and L35, agent FT and FT-kw); Jerath 2024 (L37, agent FT of the first 100k characters); Vishnoi 2023, LQR against PI and MPC (L40, FT-kw).
  - Freeway feedback control as background: ALINEA (L47, agent FT of an OCR scan) and Frejo & De Schutter 2021 (L54, audit FT). The project's cap figures of about 2-3 % and 9 % stay [VERIFY] and are not quoted.
  Position our rule families (fixed 0.8 s, own-state forms, CMA-ES zone rules) as tuned members of this class. State that this article has no MPC or adaptive opponent (RQ4, V457).
- 2.3 Evaluation practice (Table T1), per study as each review file records it: whether the baseline was tuned, the number of seeds, whether intervals are reported, and whether there is a held-out test.
  - Examples: a tuned PI-ALINEA with 20 seeds (L58, agent FT); CIs reported only for the proposed method (L59, agent FT); single-run or weak baselines (L64 and L65, agent reads of the thesis text; L71, SNIP); a position paper (L69, FT of the relevant passage only).
  - Selection after search: Cameron 2016, Smith & Winkler 2006 and van Hasselt 2010 (L72-L74, recorded as read in full by the paper-1 audit, not by the author); Boesel 2003 (L75, mostly abstracts).
  - Benchmarks: RESCO (L67, ABS) and Flow (L3).
  - Replication: Isser 2026 is located but not read (L68).
  - Paired seeds in SUMO: L76 and L77 (mostly abstracts), plus the repo's own disagreement (L78: prior_art_P1_P2.md against audit REPRO-F3). Section 4 therefore states what pairing guarantees, backed by a measurement.
  - Robustness: L19 and L20 (ABS).
- 2.4 Plant validity as a precondition for control claims.
  - Field capacity drop of 2-11 % at 27 bottlenecks (Zhang & Levinson 2004, L83, agent FT). Other ranges: L85 (agent read of a poster) and L88 (agent FT).
  - In SUMO's models the drop depends on the model: IDM's standard set gives none (L90, agent FT); Krauss (L93, PART); a calibrated EIDM shows one on a ring (L92, PART). SUMO developers say the drop is an outcome of the configuration (L95, DEV, not peer reviewed). Calibration practice: L97 and L98 (tagged FT in a source list).
  - SSAM's default TTC threshold is 1.5 s (L80, FT per crash_model_evidence_v0.md, agent). This motivates the companion counters at 1.5 s and 2 s.
  - The V&V frameworks IEEE 1012, Sargent and FHWA TAT vol. III are named in the record but not read (L82).
- Positioning rule: describe the comparison made here (per-CAV DRL against per-cell CMA-ES-tuned rules, paired seeds, CIs, readings fixed before data) without saying that the literature lacks it. That statement needs the systematic WoS/Scopus search first (prior_art_A_v0.md §5).
- Citations to obtain before drafting; none is in the repo:
  - PPO; CMA-ES ('Hansen and Ostermeier 2001' appears only in a report source, [VERIFY]); the percentile bootstrap; Bonferroni; non-inferiority testing; pre-registration.
  - RL evaluation methods. These are candidates from general knowledge, not in the repo, to verify before use: Henderson et al. 2018, Agarwal et al. 2021, Colas et al. 2018.
  - references.bib holds 21 entries from the metering line, with known defects (audit LIT-F1, LIT-F2, LIT-F9). None of the works above is in it.

Inventory ids: L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L15, L16, L17, L19, L20, L21, L22, L26, L27, L28, L29, L30, L31, L32, L33, L34, L35, L36, L37, L40, L42, L43, L47, L54, L58, L59, L64, L65, L67, L68, L69, L71, L72, L73, L74, L75, L76, L77, L78, L80, L82, L83, L85, L88, L90, L92, L93, L95, L97, L98

### 3 The instrument: the r2m3 plant, its V&V record and its numbered limits (about 1950 words)

Purpose: Describe the plant as built and read back. Show, requirement by requirement, what supports this comparison and which numbered limits every result carries. This is contribution C1, and it feeds thesis chapter 4.

- 3.1 Intended use, quoted word for word from plant_vv_record_v0.md §1:
  - 'Use: compare controllers that set the time headway of automated cars (ALKS; 1.6, 1.2, 1.0 or 0.8 s) against rule-based controllers and no control, on paired differences in door-to-door delay (with insertion queues), served flow, close-following (TTC below 3 s), braking at step resolution and severe events, on a synthetic three-lane freeway with two on-ramps, 50 % ALKS, demand 4,090-6,000 veh/h, steady or with tapered slowdowns (X1, X2).'
  - 'Not for: absolute travel times or capacities of a real road; effects on a calibrated or field site (V245); lateral or merge-conflict safety; V2V with latency or loss; human adaptation to automated cars.'
  - 'Acceptance: the plant is valid for this use when every requirement below is met, or its gap is stated as a limit that every claim sentence carries.'
  Rows outside this use are labelled 'outside the plant's stated intended use' (V462(4)), not added to it:
  - the band and 3E-T's condition T, both under the random training slowdown draw on edge 3, 4 or 5 at U(25, 60) km/h (perturb.py; P3);
  - history panel C's H1 (slow truck) and H2 (ramp bursts).
  The band's demand, 4,500-6,000 veh/h, lies inside the stated 4,090-6,000. History rows on P0 or P0d are labelled 'not the V&V target'. The intended use was written on 2026-11-07 (V459), after confirmatory 3 and round 1 had used the plant; this is disclosed (3.9).
- 3.2 Network (F1, T2; P1, P5, P12).
  - 6.8 km, 3 main lanes, two single-lane on-ramps, 100 km/h on every lane including the ramps, 3.2-m lanes, flat, no off-ramps, no lane drop.
  - Acceleration lanes 3a and 4a are 294.72 m long, against a nominal 300 m (L1).
  - Both reference points are stated. '1.2 km apart' runs from the end of 3a to the start of 4a (edge 3, 1,194.3 m); junction to junction is 1,500 m.
  - Ramp 1's signal is held green under no control. Ramp 2 has no signal and no detectors.
  - The r2m3 route lengths (about 6,778, 3,700 and 2,211 m, junction internal lanes excluded) are derived, and labelled as derived.
- 3.3 Demand, window and flow (P17).
  - One Poisson stream at q veh/h, constant within a run. Route shares 70/15/15 (corridor.py); departSpeed 'max'.
  - Each run lasts 0-1,800 s: a 300-s warm-up, then a 1,500-s window.
  - Flow is the number of vehicles reaching edge 4 in the window, written as 'vehicles per 1,500 s'. For scale, 2,132 vehicles is about 5,120 veh/h (round_1_result.md).
  - No test shows that inserted demand matches the configured level and ramp share (L2).
- 3.4 Fleet and drivers (P13, P14, P6, P23; full table T11).
  - Class is drawn per vehicle. Configured: 7.5 % trucks (fleet.py B_TRUCK_SHARE 0.075), 50 % ALKS (B_ALKS_SHARE 0.5) and 42.5 % HDV cars.
  - Realised over 106,128 draws: HDV 42.76 %, trucks 7.68 %, ALKS 49.56 % (plant_readback.json draws.shares). The draws use r1m3 routes, and the caption says so (L4).
  - HDVs follow Krauss. Their tau scale 0.8 and action-step scale 0.5 were calibrated on the human-only ld32 lane-drop corridor (V187, V188). The realised HDV tau mean is therefore 0.934 s, against a sourced 1.15 s [VERIFY] (L5).
  - HDV accel 2.6, decel 4.5 and emergencyDecel 9.0 m/s² are SUMO defaults, above the sourced ranges of 1.8-2.2, 3-4 and 7.0-8.4 [VERIFY]. lcAssertive 1.4 has no source (L5, L8).
  - ALKS follow IDM with tau 1.6 s, taken from an R157 table that covers speeds up to 60 km/h only [VERIFY]. The R157 consistency analysis is a gap (PR-07, L7).
  - Emission classes, read back (r1m3 routes): cars HBEFA4/PC_petrol_Euro-4, trucks HBEFA4/TT_AT_gt34-40t_Euro-VI_A-C. Fuel is reported in T15 with this disclosure.
  - Every parameter source stays [VERIFY] until the author has read it.
- 3.5 Actuator and sensing (F2; P15).
  - Four headway levels. The command acts only behind another ALKS within 150 m, with the same leader on two consecutive updates; otherwise the ALKS keeps 1.6 s.
  - Decisions every 10 s, each held 10 s. Longer gaps grow at most 0.2 s per second (tau_rise). Action step 0.5 s.
  - V2V and roadside speeds are ideal (L15).
  - The smooth no-undertaking rule is our model and is disclosed: look-ahead 8 s, above 60 km/h, ratio 1.1 per s, braking at most 4.4 m/s². It runs in b_env, not in SUMO (L9).
  - No inspection yet shows that policy inputs carry no information a real vehicle could not have (PR-15, L14).
  - Do not cite docs/architecture/system_context.md: it describes the superseded F3Z design (P21).
- 3.6 Slowdowns (F3; P3, P16).
  - X1: edge 4's limit drops to 25 km/h at 600 s and again at 1,200 s. Each event lasts 120 s, including a 20-s linear taper, and then the limit is released at once.
  - X2: edge 3's limit drops to 30 km/h from 700 s, for 180 s including the 20-s taper, then is released at once (common.py COND; perturb.py _slowdown lines 113-121).
  - The taper is updated on the 0.1-s clock (V378, V380).
  - Why the taper: on one seed at 4,600, 57 of 59 vehicle-seconds of braking at 7 m/s² fell in the first 10 s of the untapered events (V345).
  - The X1/X2 record is not written (PR-13, L12), and no stored file gives a field source for the X1/X2 values (L12).
- 3.7 Simulation and reproducibility (P18).
  - SUMO 1.27.1 through libsumo, step 0.1 s, teleporting off, collision.action warn, junction collision checks on.
  - Ballistic update is used because the vTypes set an action step (V367). No plant_c3 log line confirms it yet. The stored SUMO arguments come from the r1m3 baseline v1, and the text says so.
  - Replays reproduce stored rows: V398, 200 base replays at frozen d2b2ecc, 28,555 keys.
  - Rows are equal across machines:
  - V437: checks1.py rows on a rented EPYC 7B13 reproduce the laptop's rows, and the training fingerprint matches;
  - V461: the laptop reproduces the remote 3E-X rows on 3 seeds per cell, 8 keys each.
  - Stored files are hashed. SHA256SUMS is in git for baseline_v0, v1 and v4; all of v0-v4 have one in the read-only copies (/home/catalin/work/phd/v5b1_runs/baseline_v0 to baseline_v4/SHA256SUMS). The toolchain is pinned (toolchain/requirements_lock.txt).
  - Deviations (L17): the 3E-X meta.json records no commit, only cma2.py's sha256 (V461). Round 2 resumes rows by (name, q, seed) without a config hash (V455).
- 3.8 The V&V record (T3; full requirement table T10; P9, P19, P20, P24).
  - Structure: intended use, requirements, method (I/A/D/T), evidence, status, traceability (record §3), limits (record §4, extended here to L1-L27 in T19).
  - Tally at commit 6a940b3: 6 met, 13 partial, 7 gap, 2 limit of 28, after the V462 re-grades of PR-17 and PR-20. Regenerate it from the reviewed record.
  - Evidence the record does not yet cite: the V382 pre-run (prerun_output.txt; prerun.py line 54). These are finishers' delay ('delay' key), 95 % CIs over 10 seeds 7,440,065-074, positive = less delay.
  - p333 against no control: S +29.6 [24.8, 48.7], X1 +19.9 [15.8, 22.1], X2 +12.8 [9.0, 24.8].
  - Flow: +3.5 [1.6, 4.6], +4.4 [3.0, 5.8], +3.0 [2.3, 4.8] (positive = more flow).
  - 0 collisions in every arm; a 1-Hz-to-step braking ratio of 0.965-0.991.
  The article uses this as partial, DRL-independent evidence for PR-10 and PR-25. The record's PR-25 cites DRL results (V405), which is circular (L21).
  - Steady-traffic check, baseline v2 (T13; P7), labelled 'r1m3, P0d, not the V&V target': C1-C6 pass; C7 fails and was counted as met with disclosure (V376); 0 collisions and 0 teleports in 80 runs (20 seeds 7,440,045-064 × 4 levels).
  - On plant_c3, no control had 1 collision in 40 runs in round 1's X1 test and 0 in X2 (test_table.csv), so PR-17 is partial (L16).
  - No-control demand response (F9; P2): descriptive only, on reused evaluation seeds.
- 3.9 What verification changed, and when (T4; P11, M12). Section 5 reads this against the ledger.
  - P0 to P0d, V367: on seeds 7,419,640-641 at 5,300, 1,749 and 972 vehicle-s of ALKS braking at 7 m/s² or harder, which the stored 1-Hz metric saw as 0 and 0.
  - P0d to plant_c3:
  - V377: one seed (7,419,640), r2m3 P0d at 5,300, p333. The instant tau rise gave 71.3 and 75.3 vehicle-s of braking at 7 m/s² in X1 and X2, against 11 and 5 at 1 Hz.
  - V345: untapered slowdowns, one seed at 4,600.
  - Effect of the fixes (V380): p333 only, 2 used development seeds 7,419,640-641, r2m3 P0d at 5,300, 'not a check'. Moving full-emergency events went from 72, 63, 78 to 0, 0, 0 in S, X1 and X2, at about 10-13 % more delay for p333 under the slowdowns.
  - Timeline against the control results (T4):
  - P0d came after phase 1 and confirmatory 2 (V359). Its look-ahead and braking limit were chosen after a check failed on undertakes (confirmatory_3.md Disclosures).
  - plant_c3 came after confirmatory 2 and the V368 shot. The own-state family was derived from P0 policies, and the reward was shaped by runs that knew p333 (same Disclosures).
  - The V&V target and intended use were fixed on 2026-11-07 (V459), after confirmatory 3 and round 1.
  - Each change corrected a measured defect (V367, V377, V345), not a controller ranking. plant_c3 stays unchanged for the later chapters (V456(3), V457(2)). V245's caveat (fix controllability properties before control results) is quoted and answered here.
  - Baseline v4 stores policies only.
- 3.10 Limits carried by every claim (T19; field 'limits').
  - L1-L27: one per requirement that is partial (13), gap (7) or limit (2); PR-09 and PR-14, whose 'met' status carries a stated limit; and three record §4 items with no requirement (uncalibrated model; synthetic geometry; lateral and merge conflicts not measured).
  - Every claim sentence says 'within limits L1-L27'.
  - PR-15 (L14), PR-24 (L20) and PR-28 (L24) must close before 'verified and validated' appears anywhere (V462(3)).
  - When a limit closes, the numbering is regenerated from the reviewed record.

Inventory ids: P1, P2, P3, P4, P5, P6, P7, P9, P10, P11, P12, P13, P14, P15, P16, P17, P18, P19, P20, P21, P23, P24, P25, L82, M12, M13

### 4 The reading: controllers, measures and the protocol fixed before data (about 1850 words)

Purpose: Define every arm, measure and reading before any result, precisely enough to re-implement, so that the results section only fills them in. This is contribution C2, and it feeds thesis chapter 3.

- 4.1 Controllers (T5).
  - No control: every ALKS keeps 1.6 s.
  - p333: a fixed 0.8 s (cav_rule [3, 3, 3]).
  - Confirmatory 3's grid: 6 tuned forms with 69 rules (uniform 4, by zone 30, on road 4a 3, local adaptive 12, adaptive on 4a 12, own state 8), tuned per primary cell on seeds 7,440,160-179 (V376). The seventh form is the copy rule, traced from baseline-v3's policies on seeds 7,440,180-189, which makes 70 rules (confirmatory_3.md). On evaluation seeds they enter as 12 rule arms, p333 and the copy rule included (baseline_v3/opponents.json), so p333 is not counted twice.
  - 3E: per-zone own-state rules found by CMA-ES. 5 zones (zone edges at −100, 594.72, 1,389.02 and 2,083.74 m from the start of 3a), 20 parameters, diagonal CMA, sigma 0.25, population 24, CMA seed 20261106 (cma3e_x1/meta.json; round_2_prereg.md).
  - 3E-T (g032i20): tuned under condition T (outside the plant's stated intended use) at 4,500-6,000 veh/h on seeds 7,440,700-739. Its reference is os1_15_10, with a +2 % delay cap against os1_15_10, not p333. It ran 40 of 100 generations (V443), and its convergence was not checked (round_2.md Disclosures). Named 'a rule tuned by CMA-ES under the training slowdowns, not for this cell'.
  - 3E-X1 (g003i02) and 3E-X2 (g016i21): X1 or X2 at 5,300 only, seeds 7,440,740-779, reference p333, a +1 % delay hinge. Admission requires delay at most 2 % above p333's and collisions at most p333's plus 1. 16 seeds per generation, 40 generations; starts from os0_10_10 (X1) and os1_15_10 (X2) (meta.json; round_2.md D4). Run on a rented machine from commit 6c49e7e (V461). Named 'a rule tuned by CMA-ES for this cell on separate seeds'.
  - DRL: per-CAV PPO headway policies, 5 learners per recipe. The arms are v3w (round 1's winner, stored as baseline-v4, V455) and any round-2 finalist, named as round_2.md 'Naming' requires.
  - Policy inputs are normalised by running statistics (M20). The judged 1-Hz close-following flag is also a reward term, and this is disclosed. Checkpoints u250 or u500 are chosen on validation seeds only (M22).
  - Take the training budget and training-seed ranges from round_1.md and round_2_prereg.md. The training-curve files are not yet located.
- 4.1 continued: fairness in both directions. The rules know the condition and the demand level and act on a 5-s grid. The policies act every 10 s and choose among 4 levels (confirmatory_3.md). There is no MPC and no adaptive opponent (V457, RQ4).
- 4.2 Cells and measures (P10, P22, M24, R9).
  - Decision cells: X1 and X2 at 5,300 veh/h.
  - Band: 4,500, 5,000, 5,250, 5,500 and 6,000 veh/h under the training slowdown draw, 20 seeds, report-only (D5), outside the plant's stated intended use.
  - History cells: confirmatory 3's map, for baseline-v3 only, which 'support no claim'. H1 and H2 are outside the plant's stated intended use.
  - Close-following: follower-seconds with a closing rear TTC below 3 s, sampled at 1 Hz (L19). The threshold came from training needs (V265) and has no literature source. Companions: TTC below 1.5 s and 2 s, and severe samples needing at least 3 m/s² of deceleration.
  - All-vehicle delay: vehicle-seconds in the system minus distance over free speed, including unfinished vehicles and the insertion queue (L18). Finishers' delay is labelled separately wherever it appears.
  - Also: flow; braking at 3 and 7 m/s², counted every 0.1 s; moving full-emergency events; collisions. Every other counter of confirmatory_3.md §Metrics goes in T15.
- 4.3 Pre-registration (M1). Protocols, seeds, readings and allowed sentences were approved before round 2's evaluation data. round_2.md was committed at c1bf797 and approved in V454. The outline's §3 sentences were fixed before round 2's data (V459), and their wording was amended after round 2's validation rows existed and before any test row (V462(2), commit 6a940b3; V463). The tile rule (V462(1)) has the same timing.
  Disclose:
  - the registry is the git repo and the decision ledger, not an external registry;
  - round_2.md's status line still reads 'draft, revision 2', and its approval was read from 'Go on' (V454);
  - round_2.md was written after the candidates were trained and 3E-T's search results were known (its status line: 'Only the training curves, the training checks and 3E's search exist');
  - Q2 and Q3 follow round 1's readings (round_2.md Disclosures);
  - the V459 bar was set after confirmatory 3 and round 1 were known, and the claim review of the bar and the filled sentences runs after round 2's data (V459(4));
  - thesis2.py (V460) was added after the protocol's approval and runs after the test, outside the frozen chain;
  - the tile rule (V462(1)) was logged after round 2's validation rows existed (validation started 17:06, V461) and before any test row;
  - the intended use was written after the plant had been used (V459(3));
  - confirmatory 2 had no adversarial review (V356). Round 1 and the round-2 build had lean single-reviewer code reviews (V423, V455).
  'Fixed before data' means before round 2's evaluation data for the protocol (V454) and the V459 bar, and before any round-2 test row for V462's tile rule and outline wording (V463).
- 4.4 Seeds and pairing (M2, M10; F4; T14).
  - Approved block 7,440,000-999 (V354): 3E-X tuning 740-779, validation 800-839, test 840-879 used once, band 880-899.
  - An invalid run counts as that arm's failure on that seed (V6).
  - Pairing across machines was checked (V437; V461, 3 seeds per cell).
  - What paired seeds guarantee in SUMO is stated with a measurement, because the repo sources disagree (L78).
- 4.5 Statistic and sign convention (M3, M4; T18).
  - Effect = sign × median(P − O) / median(O) × 100 over paired seeds.
  - Percentile bootstrap of the paired differences: 20,000 resamples, denominator fixed, generator seed 20261104 (common.py raw()).
  - An arm is the per-seed mean over its 5 learners. The CIs cover evaluation seeds only.
  - One convention throughout: common.raw. On the earlier metering line, the paired convention once changed a reported figure: V94's 16-41 % became 10-35 % (V99).
- 4.6 Multiplicity (M5).
  - Validation runs at 95 % with no correction, because it selects. Disclose that across its 14 tests, at least one passes by chance up to about 30 % of the time (round_2.md Disclosures).
  - T1 uses m = finalists × 2.
  - T2 uses m = (finalists + v3w) × 2, which gives 97.5, 98.75 or 99.17 % for 0, 1 or 2 finalists. Extra 3E opponents do not change m, because T2 is an intersection over opponents.
  - Map tiles use 95 % with no correction over tiles. This is why they are descriptive and decide nothing (V462(1)).
- 4.7 Readings (T6; M6, M7, M8, M15, M16, M23).
  - Counting: an opponent counts only if its delay is within 2 % of p333's, on the point estimate. Disclose that this filter can drop a rule with lower TTC (M8 notes).
  - T2: at least 4 of 5 policies, against every counting opponent, have close-following at least 10 % better (CI excluding 0) and at least 20 per run lower. They must also stay within the limits on delay (2 %), flow (0.5 %), braking at 3 m/s² (5 %), full-emergency events (5 % or 5 per run) and collisions (opponent's plus 1), and against p333 within 5 % on delay and 1 % on flow.
  - Harm is read at 95 %, because a corrected CI would hide it.
  - The 5 % non-inferiority bound is reported beside T2 (D11), because the 2 % point rule passes a policy that is truly 2 % worse 52 % of the time (V435).
  - Against no control: the V459 bar, computed by thesis2.py on branch r2/eval (V460), with confirmatory 3's no-control clause beside it.
  - Outcomes W, G and N, one sentence per cell (outline §3), with the D10 closing rule: a cell where no 3E rule counts does not close.
  - Floor KILL and early KILL (M16).
- 4.8 Integrity rules (M11-M14, M17-M22):
  - every run uses a frozen copy of its commit (origin V102; replay V398);
  - traced runs must equal untraced runs (V386);
  - the bug rule: fix, re-run everything affected, log both outcomes;
  - a no-effect null before a gate statistic is used (V244 principle). It was computed for confirmatory 3 [A2], the collapse check and round 2's T1 path (b). There is none yet for the 10 % no-control delay bar, the 2 % counting filter, the margins or the tile rule, and this is disclosed;
  - trace what a counter measures before it enters a claim (V283; only partly done, PR-24, L20);
  - smoke checks in training mode (V294);
  - an input audit (V387-V389);
  - the collapse check;
  - adversarial reviews (M21: V377, V453), with the lean reviews disclosed (V423, V455).
- 4.9 Map tile rule, quoted from V462(1). It is descriptive: logged after round 2's validation rows existed and before any test row.
  - Per tile (cell X1 or X2 at 5,300 × measure × opponent), on the arm (the per-seed mean over the 5 policies, as T1), with a 95 % percentile bootstrap and common.raw signs.
  - W if close-following is at least 10 % better (delay tile: at least 5 %), with the CI lower bound above 0.
  - L if close-following is more than 10 % worse (delay: more than 2 %) by point, with the CI upper bound below 0 (round 2's harm rule).
  - T otherwise.
  - Flow, braking at 3 m/s², moving full-emergency events and collisions appear as markers where they breach T2's side limits. The count of single policies meeting W is shown beside.
  - No tile is a verdict: only T2 and the V459 bar decide.

Inventory ids: M1, M2, M3, M4, M5, M6, M7, M8, M9, M10, M11, M12, M13, M14, M15, M16, M17, M18, M19, M20, M21, M22, M23, M24, M26, P10, P22, R9, R16, R18, R21, L78

### 5 Where the plant checks and the protocol changed a conclusion [round 2] (about 650 words)

Purpose: Show from the project's decision ledger which elements of sections 3 and 4 changed a conclusion, which kept a pre-registered verdict apart from post-hoc statements, and which never did. It feeds thesis chapter 3 ('metric traps'). Round 2 can change it most, so it is marked round-2 dependent.

- Table T7 has one row per element M1-M24: where it is defined (a protocol section or V#) and one line on its ledger event (M25). Rows M5, M7 and M9 are completed after round 2's test.
- Plant checks that changed conclusions:
  - V367 (seeds 7,419,640-641 at 5,300, P0): 1,749 and 972 vehicle-s of ALKS braking at 7 m/s² or harder, seen at 1 Hz as 0 and 0. The braking and free-road statements behind V328's plant pick no longer held.
  - V377 (one seed, 7,419,640, r2m3 P0d at 5,300, p333): the instant tau rise gave 71.3 and 75.3 vehicle-s of braking at 7 m/s², against 11 and 5 at 1 Hz.
  - V380 (p333 only, 2 used development seeds 7,419,640-641, 'not a check'): with both fixes, moving full-emergency events went from 72, 63, 78 to 0, 0, 0.
- Protocol elements that changed conclusions:
  - V244 (plant v199, not r2m3): a capacity-drop gate whose statistic has a null median of 10.8-12.65 %, against a 2 % stop line, could not fail.
  - V386: tracing changed the run (X1 flow 2,131 traced against 2,164 untraced).
  - V368: a rule match did not hold on fresh seeds. V401: confirmatory 3's X2 win did not replicate (1 of 5 policies on 20 fresh seeds).
  - V283: the short-gap counter counted stopped queues.
  - V294: the per-vehicle reward never reached training.
  - V387-V389: a dead input, and inputs not normalised.
  - From the earlier metering line, not the DRL plant: V99, where the paired convention turned V94's 16-41 % into 10-35 %.
- Verdicts kept apart from post-hoc statements:
  - V396 kept confirmatory 3's pre-registered verdict apart from three post-hoc statements, which were withdrawn. That verdict then failed replication (V401).
  - V452: 45 findings, 42 confirmed, no verdict change. The review found mixed sign conventions.
  - V405: an overstatement against no control was withdrawn. It became the close-following half of the V459 bar.
- Fragility, reported before replication: a full seed bootstrap gave confirmatory 3's X2 'won' a probability of 0.27-0.30 (R11, V396). Confirmatory 3b then did not replicate (R10, V401).
- Elements with no changing event, stated as such:
  - Bonferroni: labelling corrected, no verdict change (V452).
  - Non-inferiority: report-only, round 2 pending.
  - Early KILL: never fired in the DRL line (V382).
  V256 (mobility results withdrawn as a plant artefact) belongs to thesis chapter 8 and is an optional row.
- Round-2 rows: whether a counting 3E rule decided a cell (M9), the non-inferiority bound (M7) and the T2 level used (M5). Write them only from round 2's test_result.json. A change from round 1 is not attributed to 3E (round_2.md: no sentence rests on T2 without 3E). [round 2]

Inventory ids: M25, M3, M5, M7, M9, M10, M12, M13, M14, M17, M18, M19, M20, P11, R10, R11

### 6 Results: the two-cell decision map (about 2100 words)

Purpose: Fill the readings defined in sections 3-4. For each cell, measure and opponent, say whether these per-CAV PPO policies win, tie or lose, by how much, and where. Report the replication history and the report-only rows beside them. Filled after round 2.

- 6.1 Decision rows (T8; F5 verdict strip; R16, R22). Per cell, report:
  - the counting set, with each 3E rule's counting status and its delay against p333 with CI, at validation and at test;
  - k of 5 learners passing T2 at its Bonferroni level (97.5, 98.75 or 99.17 % for 0, 1 or 2 finalists);
  - the close-following margin range against the strongest counting rule (common.raw, positive = the policies fewer);
  - the limits missed;
  - the outcome, as an outline §3 sentence per cell, plus the confirmatory 3 sentence-table row filled from T2, both with the model sentence and 'within limits L1-L27';
  - report-only columns: T2 without 3E, labelled 'comparison with round 1; no sentence rests on it' (round_2.md), and the 5 % non-inferiority bound (D11).
  Round 1 beside it, at 97.5 %, common.raw, seeds 7,440,500-539 (R2; V449, V452):
  - X1: v3w 5 of 5, with only p333 counting; 35-46 % fewer close-following seconds than p333.
  - X2: v3w 5 of 5, with p333 and os1_15_10 counting; 22-31 % against os1_15_10.
  Round 1's T2 alone is at most outcome G, because no 3E rule existed then. No sentence attributes a change between rounds to 3E. [round 2]
- 6.2 Against no control (T9).
  - The V459 reading for every arm and rule, rules included: delay at least 10 % lower with the CI excluding 0 at T2's level, and close-following not harmed under round 2's harm rule (95 %). The number of single policies meeting it goes beside.
  - Source: /home/catalin/work/phd/v5b1_runs/round2/thesis_v459.json. A manual run writes it after the test: thesis2.py OUT VALIDATION_JSON on r2/eval (68f405a). chain2.sh does not call it, and the frozen code_6c49e7e does not contain it (V460).
  - Beside it, confirmatory 3's no-control clause, filled from T2:
  - no control's TTC, delay and braking at 3 m/s² per run;
  - 'no control had fewer such seconds, at [y] % more delay' when at least 4 of 5 policies are clearly worse on TTC;
  - 'collisions, which are too rare to compare'.
  Round 2 runs no map cells, so the clause's map-cell part has no round-2 rows, and the text says so.
  - The delay half is unlikely to fail on this plant. In the exploratory sweep (V419; 2,500-7,500 veh/h under the training slowdown draw, outside the plant's stated intended use), every controller had at least 10 % (11-40 %) less delay than no control, even at 2,500 veh/h (baseline-v3 policies, 10 seeds 7,440,600-609, code 6d3a1a6). V419 calls this 'a property of the headway, not of DRL'. Only the close-following half has failed in earlier readings (R4).
  - Provisional reading from round 1, exploratory, 95 %, common.raw (R4):
  - v3w close-following −24.4 [−33.1, −15.4] in X1 and −1.9 [−7.1, +9.2] in X2; delay +28.0 and +23.2;
  - os1_15_10 close-following −78.4 and −33.6; p333 −114.4 and −64.5;
  - round 1's X1 clause: 'No control had fewer such seconds, at 39.2 % more delay' (round_1_result.md). [round 2]
- 6.3 The CMA-ES rules on fresh seeds (R16).
  - 3E-X tuning values, converted to common.raw (positive = 3E-X has less than p333), on 40 tuning seeds 7,440,740-779 at 5,300 (cma3e_x1 and cma3e_x2 final.json; V461 states them as changes, with delay negative = less):
  - X1 g003i02: close-following +32.6 % (median paired difference −1,067.5 s over p333's median of 3,275 s); delay +1.05 %.
  - X2 g016i21: close-following +39.7 % (−980 s over 2,469.5 s); delay +1.64 %.
  - These values use the protocol's statistic form (median of paired differences over the reference median; cma2.py objective() at one level). They are in-sample values of a selected pick, with no CI, so the drop from tuning to test seeds is the overfitting check (round_2.md).
  - Neither search converged. Median loss of the last 10 generations against the 10 before (negative = better): X1 −30.77 against −22.51, X2 −30.92 against −26.01, 'still_falling' true in final.json. Under round_2.md, 3E-X is therefore a lower bound on a per-cell tuned rule, and this is disclosed beside every 3E-X result.
  - In X1 the pick comes from generation 3. The shortlisted points with lower loss (g028i09, g038i05 and the CMA mean) had 2.44, 2.64 and 2.38 % more delay than p333 and failed the 2 % admission cap (final.json, cma2 sign).
  - 3E-T against os1_15_10 per band level, with the sign converted from round_2.md's table (which uses positive = more) to common.raw (positive = 3E-T has less):
  - close-following −24.9, +7.9, +7.4, +12.2 and +20.0 % at 4,500, 5,000, 5,250, 5,500 and 6,000;
  - delay −1.5, −2.1, −3.2, −3.9 and +0.5 %;
  - its pooled value sums TTC seconds over the levels: +14.3 % close-following at −2.0 % delay, with 68 % of the gain at 6,000.
  Condition T is outside the plant's stated intended use. [round 2]
- 6.4 Where the gains or losses sit (T15; R7, R11, R15). Report road, follower-speed and period splits for every arm. Every win sentence names the share on 4a plus ramp 2 and the follower-speed split.
  - Round 1, X2 against os1_15_10. Median paired differences in TTC samples, 40 seeds, 95 % (round_1_result.md §4):
  - edge 3 219 [164, 254] and edge 4a 131 [105, 217], about three quarters of the gain;
  - follower speed below 5 m/s 135 [96, 200], 5-10 m/s 145 [99, 180], 10 m/s or more 230 [179, 249], which is under half the gain.
  - What the count is made of:
  - mostly a low-speed queue, at median 5-7 m/s on one seed, largely around merge 2 (confirmatory_3.md Metrics);
  - p333 on one seed: median follower speed 5.0 and 7.4 m/s, 48-62 % of records below 7 m/s, 61-79 % with a leader stopped on 4a or ramp 2 (V377).
  - Confirmatory 3's verification (baseline-v3): 82-96 % of the X2 gain fell in the recovery period, and 46-61 % of the gain against os1_15_10 sat on 4a plus ramp 2, where lane-end behaviour is not validated (V396; L24).
  - V398, quoted in full. Exploratory: baseline-v3 d0-d4, 97.5 %, common.raw, same evaluation seeds.
  - Excluding lane 4a_0, the gain against os1_15_10 stays at +15.9 to +29.9 % (4 of 5 CIs above 0), and against lr1000_16_2 at +10.4 to +31.5 %.
  - 'On the 4a mainline lanes, policies have more TTC than r4a1 (d0 −45.7 [−65.5, −13.7] %) and far more than no control: part of the gain is moved from the accelerating lane to the mainline'.
  - ALKS followers: +16.6 to +35.5 % against os1_15_10, but above no control (−13 to −42 %).
  - Human and truck followers: +4.2 to +17.0 % against os1_15_10, and +9.3 to +20.9 % against no control.
  - ALKS followers hold 58-66 % of TTC seconds.
  - The follower-class split exists only for baseline-v3 (V398); round 2 has none for v3w. [round 2]
- 6.5 Delay-TTC plane (F6; R20). The verification's finding that the policies lie on a better frontier than all 70 rules is labelled exploratory (R11). [round 2]
- 6.6 Band (F8; R5), outside the plant's stated intended use (training slowdowns). Per level: close-following and delay against no control, and the share of seeds below no control. There is no verdict (D5).
  Round 1 beside it, 95 %, common.raw, seeds 7,440,540-559:
  - v3w close-following −17 [−112, +642], +38 [−10, +71], +36 [−1, +76], +29 [+5, +50] and +7.6 [+2.4, +13.8] at 4,500 to 6,000;
  - delay +23 to +32 at every level;
  - verdict 'not shown'. [round 2]
- 6.7 Candidate selection (T17; R6). Which candidates advanced; harm; floor KILL; ahead's importance KILL; T1 against v3w. This is selection, not a finding. Round 1's nulls stay reported:
  - res did not qualify;
  - attr was out by harm (delay −13.5 and −10.4, common.raw, 95 %);
  - lagr was out by the mechanism stop. [round 2]
- 6.8 Replication history (F7, T16; R8, R10, R12, R13, R19):
  - phase 1 on r1m3 P0, headway action only (step 2, V337): delay against p333 +1.5, +1.8 and +1.3 % at 5,300, and +0.6 to +1.9 % at 4,600 (positive = less delay; read the CI level from docs/research/phase1 before use). This is a tie. Step 3 (V338-V339) is a different actuator, speed cap plus headway with 12 actions (+0.8, 0.0 and +2.3 % at 5,300), and is labelled so;
  - confirmatory 2: 1 of 20 cells, on the earlier plant, finishers' delay (V359);
  - confirmatory 3: X2 won 4 of 5; X1 got 3 of 5 and was closed by [A3] (V395);
  - confirmatory 3b: X2 1 of 5 (V401);
  - round 1: 5 of 5 against the old grid (V449, V452);
  - round 2: [pending].
  Annotate each entry with its plant (P0 and P0d rows: 'not the V&V target'), policy set, delay metric and seed block.
- Exploratory rows go in the text only, labelled exploratory and baseline-v3 only: the demand sweeps (R14) and the demand profiles (both outside the plant's stated intended use), and the 3,000-s replays (R15). Side metrics go in T15 with no control beside them (R3). Every sentence comes from round_2.md 'Sentences allowed', confirmatory 3's sentence table and outline §3, and cites 'within limits L1-L27'.

Inventory ids: R1, R2, R3, R4, R5, R6, R7, R8, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, M5, M7, M8, M9

### 7 Discussion: what the map answers, and threats to validity (about 1150 words)

Purpose: Interpret the answer within its scope and limits L1-L27, and state every threat with what the article does about it.

- 7.1 The answer and what it cannot show. Quote verbatim.
  - round_2.md: 'Any win holds for this uncalibrated SUMO model, these slowdowns, these demand levels and ideal V2V.' 'A null on 7 candidates in one round does not show that no other change would help.' 'Without D4, beating 3E-T does not show that a rule tuned per cell would be beaten. With D4, it shows this for one 40-generation search per cell. If that search has not converged, 3E-X is a lower bound on a per-cell tuned rule.' Add that by final.json's own check neither 3E-X search had converged, so 3E-X is a lower bound.
  - confirmatory_3.md: 'It says nothing about other actions, other networks, other spacings or real traffic. 4 of 5 is a statement about these trained policies, not the method in general. A rule outside these families could still match DRL. TTC below 3 s is a surrogate, and this model is not calibrated, so a win is not a safety result for real traffic. Only 2 conditions decide the claim.'
  - Also: the cells were selected after earlier rounds, and limits L1-L27 apply. [round 2]
- 7.2 Threats from the plant (V&V record; limits L1-L27):
  - uncalibrated model (L25); synthetic geometry with one spacing (L26);
  - HDV scales from ld32 (V187) and SUMO default accel and decel above the sourced ranges (L5);
  - merge-2 lane ends (L24); capacity drop not settled (L22); no field comparison (L23);
  - rows outside the intended use: the band, 3E-T's condition T, and panel C's H1 and H2.
  Threats that are not yet record requirements, and so not numbered limits (open decision):
  - no sensitivity analysis;
  - constant Poisson demand;
  - warm-up and window not checked on 6.8 km.
  The missing field source for the X1/X2 values is limit L12.
- 7.3 Threats from the opponents:
  - no MPC or adaptive opponent (the V457 parallel track);
  - 3E-X is a lower bound: one search per cell, not converged by its own check, with the X1 pick from generation 3;
  - 3E-T ran 40 of 100 generations (V443), with its delay cap against os1_15_10, not p333;
  - the grid was tuned at 5,300 only, which favours DRL in the band and the map cells;
  - information and update-rate asymmetries run in both directions.
- 7.4 Threats from the statistics:
  - learner variance lies outside every CI: 5 learners, each recipe trained once (round_1_result.md §6.2);
  - the 2 % point delay rule does not bound harm (V435);
  - no coverage check exists for the bootstrap at Bonferroni-extreme percentiles with n = 40;
  - the margins come from internal runs. V363 set the 10 % close-following and 2 % delay numbers, in an exploratory rule. V346 set the 20-per-run margin. The options memo's F4 (docs/reports/2026-11-05_21-29/drl_options_2026-11-05_21-29.html) gives the exchange rate the bar implies, 19-23 vehicle-seconds per close-following second, which agrees with the bar but is not its source. No external source exists;
  - X1 and X2 were tested repeatedly across rounds without a correction, and X1 was reopened after [A3] (round_2.md Disclosures);
  - the cells were chosen where DRL already looked best (confirmatory_3.md Disclosures);
  - the tiles carry no correction over many tiles, so they are descriptive (V462(1));
  - confirmatory 3's seed-bootstrap P(won) was 0.27-0.30 (R11).
- 7.5 Threats from the surrogate and the registry:
  - TTC below 3 s at 1 Hz is mostly a low-speed queue (6.4) and also a reward term. So the counters outside the reward are reported, and 'safety' is gated by the severe-conflict check;
  - the 0.1-s TTC meter E1 has not run (L19);
  - the registry is internal, and round 2's approval was read from 'Go on' (V454);
  - the claim review runs after the data (V459(4)).
- 7.6 Relation to the literature, all [VERIFY] with read levels:
  - compare the answer with the pattern of matching rather than beating (L1, L2, L57), with the L58 exception and its mainline-only metric, and with Elmorshedy's comparison against a static headway and its ramp-delay increase (L8);
  - external-validity cautions, without generalising: compliance errors (L19, ABS) and uncertain penetration (L41, FT-kw);
  - an MPC opponent must model capacity-drop hysteresis, or it is a straw man (L62, FT-kw).
- 7.7 Next steps:
  - non-learning adaptive opponents on the same, unchanged plant (RQ4, V457);
  - disturbed plants, each disturbance fixed before control results (RQ5, V456);
  - closing PR-15, PR-24 and PR-28, then the record review, before any 'verified and validated';
  - the field comparison PR-27, which is a comparison, not a calibration.

Inventory ids: M4, M7, M9, M10, M16, M23, P6, P14, P20, R11, R14, R16, L1, L2, L8, L19, L41, L57, L58, L62

### 8 Conclusion (about 250 words)

Purpose: Answer the question in one paragraph, within its scope and limits, and state data and code availability.

- The answer per cell, as outline §3 sentences, with:
  - the model sentence;
  - 'within limits L1-L27';
  - the V459 reading and confirmatory 3's no-control clause;
  - confirmatory_3.md's and round_2.md's 'What this cannot show' items, verbatim.
  Then one sentence each for C2 and C1. C1 says 'documented in a V&V record', not 'verified and validated' (V462(3)). [round 2]
- Availability statement:
  - frozen commits;
  - hashed stored files: SHA256SUMS in git for baselines v0, v1 and v4, and in the read-only copies for v0-v4;
  - the pinned toolchain (toolchain/requirements_lock.txt);
  - the disclosed exceptions (L17).
  Whether and where the code and data are archived is an open decision.

Inventory ids: M11, M15, P9, P18, P20

### A Supplementary material (outside the main word count) (about 1450 words)

Purpose: Hold the full tables a reviewer needs to audit the plant, the readings and the history, without crowding the main text.

- The full V&V requirement table, PR-01 to PR-28, with method, evidence, status and traceability, as at commit 6a940b3 or the reviewed version (T10; P9). The numbered limits L1-L27 go beside it (T19).
- Driver and vehicle parameters by class, with source and status (T11), and the sampled distributions against their sources (F10).
- No-control reference values on plant_c3, with both delay metrics labelled, and the V382 pre-run with its labels: finishers' delay, 95 %, 10 seeds (T12). The no-control demand response (F9).
- The baseline v2 steady-traffic check, labelled 'r1m3, P0d, not the V&V target' (T13). Resolve the 'undertakes' naming first.
- Conditions, levels, seeds and run window, with the rows outside the intended use marked (T14).
- Side metrics per arm and cell (T15): every counter of confirmatory_3.md §Metrics, including fuel with its emission classes, with road, speed and period splits and no control beside. The follower-class split exists only for baseline-v3 (V398).
- Earlier readings, phase 1 to round 1 (T16); round 2 validation and candidate selection (T17).
- The sign convention and CI level of every stored file, and every converted number (T18; V452).
- Reproducibility and deviations, as text:
  - SUMO arguments;
  - same-code replay (V398, 28,555 keys); cross-machine equality (V437; V461, 3 seeds per cell, 8 keys each);
  - frozen commits per phase;
  - confirmatory 3 ran on two commits (fae4620, d2b2ecc);
  - 3E-X ran on a rented machine from deploy folder code/6c49e7e, and its meta.json records 'commit': null with cma2.py's sha256 (V461);
  - round 2 resumes rows by (name, q, seed) without a config hash (V455);
  - thesis2.py runs manually after the test (V460).

Inventory ids: P2, P4, P6, P7, P8, P9, P10, P18, R3, R6, R8, R10, R12, R13, R21, M11

Total target: about 11800 words, supplement included.

## Figures and tables

| ID | Kind | Title | Section | Generation | Round 2 | Sources | Shows |
|---|---|---|---|---|---|---|---|
| F1 | figure | r2m3 to scale: edges, lanes, on-ramps, acceleration lanes, slowdown edges X1/X2 and detectors | 3.2 | script to write | no | docs/research/baseline_v2/r2m3_spec.json; docs/research/baseline_v2/r2m3_net.xml; docs/research/baseline_v2/r2m3_add.xml; docs/research/conf3/common.py; docs/extracts/2026-11-05_09-18/2026-11-05_09-18_extract.html | The mainline nodes at 0, 3,000, 3,500, 3,800, 5,000, 5,300, 6,300 and 6,800 m, with 3 lanes, and 4 lanes on 3a and 4a (294.72 m each, nominal 300 m; L1). Ramps r and r2 (391.66 m, one lane each); the signal at node rm only. X2 on edge 3 between the merges; X1 on edge 4, downstream of 4a. Induction loops from r2m3_add.xml. Both reference distances are marked: 1,194.3 m from the end of 3a to the start of 4a, and 1,500 m junction to junction. The caption says whether node coordinates or route positions are drawn (P1, P12). The extract's SVG is a template only. |
| F2 | figure | Plant, environment code and controller: the boundary as built | 3.5 | drawn by hand | no | v5b/fleet/b_env.py; v5b/fleet/fleet.py; docs/research/baseline_v3/plant_c3.json; docs/research/baseline_v3/env.json; docs/research/baseline_v0/BASELINE.md | SUMO (Krauss HDVs and trucks, IDM ALKS, slowdown speed limits, 0.1-s step) next to the b_env layer: the V2V gate (150 m, same leader on two updates; ideal, L15), tau_rise of 0.2 s per s, and the smooth no-undertaking rule (our model, L9). Next to them, the controllers: p333, grid rules, 3E and PPO policies, setting per-ALKS levels every 10 s. Observation and actuation paths are drawn; the measurement counters (1 Hz and 0.1 s) use ground truth. A note marks PR-15 (inputs carry no information a real vehicle could not have) as a gap (L14). It replaces the superseded F3Z context in system_context.md (P15, P21). |
| F3 | figure | Speed-limit profiles of X1 and X2, and the training slowdown draw | 3.6 | script to write | no | docs/research/conf3/common.py; v5b/fleet/perturb.py; docs/research/protocols/confirmatory_3.md | The limit against absolute time, with the 300-s warm-up and the 300-1,800-s window shaded. X1: on edge 4, at 600 and 1,200 s, each event 120 s including a 20-s linear taper down to 25 km/h, then an instant release. X2: on edge 3, from 700 s, 180 s including the 20-s taper down to 30 km/h, then an instant release (perturb.py _slowdown lines 113-121). Inset, the training draw, labelled 'outside the plant's stated intended use': one third of episodes unperturbed; the rest get one slowdown on edge 3, 4 or 5 at U(25, 60) km/h for U(60, 180) s, starting at U(400, 1,200) s (P3). |
| F4 | figure | Evaluation pipeline with seed blocks, CI levels and stop rules | 4.4 | drawn by hand | no | docs/research/protocols/round_2.md; docs/research/protocols/round_1.md; docs/research/results/round_1_result.md; docs/decisions.md | Boxes in order: - build and checks 1-7, with the frozen run commit; - 3E-X tuning on 7,440,740-779 (rented machine, V461); - validation on 7,440,800-839 (95 %, uncorrected, selection); - the tile rule logged (V462(1)) after validation started and before any test row; - test on 7,440,840-879, used once (Bonferroni 1 − 0.05/m); - band on 7,440,880-899 (report-only, outside the plant's stated intended use); - readings; - the manual thesis2.py step (V460), outside the frozen chain. Each box carries its stop rule: floor KILL, harm, D10 closing (M26). |
| F5 | figure | Two-cell decision map: cells × measures × opponents with descriptive W/T/L tiles, a verdict strip, and band and history panels | 6.1 | script to write | yes | docs/research/round1/report/test_table.csv; docs/research/round1/report/test_result.json; docs/research/round1/report/band_table.csv; docs/research/baseline_v3/decide3_map.csv; docs/research/baseline_v3/rows/conf3_eval_map.jsonl.gz; docs/research/baseline_v3/rows/conf3_eval_map_x.jsonl.gz; docs/research/baseline_v3/rows/conf3_eval_primary.jsonl.gz; docs/reports/2026-11-05_19-22/source/results_build.py; /home/catalin/work/phd/v5b1_runs/round2/test_result.json; /home/catalin/work/phd/v5b1_runs/round2/val/validation.json; /home/catalin/work/phd/v5b1_runs/round2/thesis_v459.json | Panel A: X1 and X2 at 5,300 from round 2's test. The column groups are no control, p333, the strongest counting grid rule, 3E-X (that cell's) and 3E-T, each with close-following and all-vehicle delay. - Each tile shows the arm effect with its 95 % CI (common.raw, positive = the policy arm better), the descriptive glyph by V462(1), side-limit markers, and the count of single policies meeting W. - Excluded rules show 'not counting'. - A separate verdict strip per cell gives T2's outcome (W, G or N) and the V459 reading. No tile is a verdict. Panel B: band rows, hatched, no verdict, labelled 'outside the plant's stated intended use'. Panel C: confirmatory 3's map cells for baseline-v3, hatched, 'support no claim'; H1 and H2 labelled 'outside the plant's stated intended use'. Built on results_build.py grid(), repointed to the in-git rows. Until round 2 reports, round 1's rows fill a provisional panel A labelled 'round 1, old grid'. The three round-2 files do not exist yet (R22); thesis_v459.json comes from a manual thesis2.py run after the test (V460). |
| F6 | figure | Delay against close-following per deciding cell, with the counting region (delay at most 2 % above p333's median, point estimate) | 6.5 | script to write | yes | docs/research/baseline_v3/rows/conf3_tune.jsonl.gz; docs/research/baseline_v3/rows/conf3_eval_primary.jsonl.gz; docs/reports/2026-11-05_19-22/source/results_build.py; /home/catalin/work/phd/v5b1_runs/round2/test/ | Same-seed test medians for no control, p333, every grid rule, the copy rule, 3E-T, 3E-X, each learner and the arm mean, with the counting region (delay at most 1.02 × p333's median, point estimate) shaded. The 70 tuned rules on their tuning seeds go in a separate labelled panel, never on unlabelled shared axes. Built on scatter_cell() (R20). The round-2 test folder does not exist yet (R22). |
| F7 | figure | Replication history of the slowdown cells X1 and X2 | 6.8 | script to write | yes | docs/research/phase3/decide_table.csv; docs/research/baseline_v3/decide3_table.csv; docs/research/conf3/replicate_x2_output.txt; docs/research/round1/report/test_result.json; /home/catalin/work/phd/v5b1_runs/round2/test_result.json | One strip per cell: - confirmatory 3 (X2 4 of 5, X1 3 of 5, V395); - 3b (X2 1 of 5, V401); - round 1 (5 of 5 against the old grid, V449/V452); - round 2 (pending; its test_result.json does not exist yet, R22). Each mark shows the learners passing and the margin range against the strongest counting rule, annotated with plant, policy set, delay metric and seed block. Confirmatory 2 (pre-plant_c3, finishers' delay, Bonferroni over 20) goes in a separate panel labelled 'not the V&V target' (R19). |
| F8 | figure | Band 4,500-6,000 veh/h against no control (report-only, outside the plant's stated intended use) | 6.6 | script to write | yes | docs/research/round1/report/band_table.csv; docs/research/results/round_1_result.md; /home/catalin/work/phd/v5b1_runs/round2/test_result.json | Per level and arm (finalists, v3w, baseline-v3, p333, os1_15_10, 3E-T): close-following and delay against no control with 95 % CIs, and the share of seeds with fewer close-following seconds than no control. No verdict (D5). Round 1's v3w rows sit beside them: close-following −17 to +38 %, delay +23 to +32 %, common.raw, 'not shown'. The caption says the band uses the training slowdown draw, outside the plant's stated intended use. Round 2's file does not exist yet (R22). Candidate for merging into F5 panel B (R5). |
| F9 | figure | No-control served flow and delay against demand on plant_c3 (descriptive, reused seeds) | A | script to write | no | docs/research/baseline_v3/rows/sweep_sweep.jsonl.gz; docs/research/baseline_v3/runs/sweep_levels.json | The 192 no-control rows (S, X1, X2): passed vehicles, all_delay, delay and finished_pct at 16 levels from 3,920 to 5,910 veh/h, 4 seeds each (7,440,200-203, reused evaluation seeds). Shows where congestion sets in without a controller. Labelled descriptive: it is not a test and not a T1 record (P2; L21). |
| F10 | figure | Sampled driver and vehicle parameter distributions against their sources | A | script to write | no | docs/extracts/2026-11-05_09-18/plant_readback.json; docs/extracts/2026-11-05_09-18/plant_readback.py; docs/research/driver_params_hdv_cav_v0.md | Histograms over 106,128 sampled vehicles (HDV 42.76 %, trucks 7.68 %, ALKS 49.56 %): HDV tau (p50 0.94 s), sigma, action step, speed factor and lengths; truck speed and lengths; ALKS tau and length. Sourced shapes are drawn beside them, e.g. tau with mean 1.15 s and SD 0.43 [VERIFY]. The caption says the draws use r1m3 routes and predate plant_c3 (P4; L4, L5). |
| T1 | table | Evaluation practice in the reviewed per-CAV and DRL freeway studies | 2.3 | drawn by hand | no | docs/research/prior_art_A_v0.md; docs/research/prior_art_B_v0.md; docs/research/lit_reviews/web_sweep_rl_value.md; docs/research/lit_reviews/2018_Wu.md; docs/research/lit_reviews/2022_Kreidieh.md; docs/research/lit_reviews/2023_Elmorshedy.md; docs/research/lit_reviews/2025_Shi.md; docs/research/lit_reviews/2026_Mansouryar_2019_Zhou.md | For each work (L1, L2, L3, L6, L7, L8, L9, L57, L58, L59, L64, L65): actuator, simulator, baseline and whether it was tuned, seeds, intervals, held-out test, and read level as the repo records it (agent FT, FT-kw, ABS, SNIP), with [VERIFY] on every row, because none is recorded as read in full by the author. It describes these works only and makes no claim about the literature as a whole. |
| T2 | table | The plant at a glance: geometry, demand, fleet, actuator, slowdowns, simulation settings | 3.2 | script to write | no | docs/research/baseline_v2/r2m3_spec.json; docs/research/baseline_v2/r1m3_spec.json; docs/extracts/2026-11-05_09-18/2026-11-05_09-18_extract.md; v5b/fleet/fleet.py; v5b/fleet/corridor.py; docs/research/baseline_v1/constants.json; docs/research/baseline_v3/plant_c3.json; docs/research/baseline_v1/plant.json.gz | Edges with lanes, lengths and positions from the start of 3a; speed limit 27.78 m/s; lane width 3.2 m; route shares 70/15/15. Fleet shares configured as HDV 42.5 %, trucks 7.5 %, ALKS 50 %, and realised as HDV 42.76 %, trucks 7.68 %, ALKS 49.56 % (r1m3 routes). Headway levels, V2V gate, 10-s decisions, tau_rise 0.2; X1 and X2 with their taper wording; SUMO 1.27.1, step 0.1 s, teleporting off, 0-1,800 s with a 1,500-s window. The r2m3 route lengths are labelled 'derived'. The SUMO arguments come from the r1m3 baseline v1, and the table says so (P5, P12, P17, P18). |
| T3 | table | V&V summary: requirements by group and status, traceability to claim elements, numbered limits | 3.8 | existing file | no | docs/testing/plant_vv_record_v0.md; docs/research/conf3/prerun_output.txt; docs/research/round1/report/test_table.csv | 28 requirements in six groups: road, demand and insertion; drivers and fleet; actuator and sensing; numerics and reproducibility; measurement; validation. Tally at commit 6a940b3: 6 met, 13 partial, 7 gap, 2 limit, after the V462 re-grades of PR-17 and PR-20. Also shown: the map from claim elements to requirements (record §3), the pointer to L1-L27 (T19), and the gaps that block 'verified and validated' (PR-15, PR-24, PR-28; V462(3)). V382 is added as partial evidence for PR-10 and PR-25 (finishers' delay, 95 %, 10 seeds). Regenerated from the reviewed record (P9, P19, P20). |
| T4 | table | Plant lineage: what verification found, what it changed, and when relative to the control results | 3.9 | drawn by hand | no | docs/research/baseline_v1/plant_p0.json; docs/research/baseline_v2/plant_p0d.json; docs/research/baseline_v3/plant_c3.json; docs/research/baseline_v1/BASELINE.md; docs/research/baseline_v2/BASELINE.md; docs/research/baseline_v3/BASELINE.md; docs/research/baseline_v4/SHA256SUMS; docs/decisions.md | The three plants: - P0: smooth rule; code 124b930. - P0d: ease, smooth_s 8, ease_max 4.4; code 823eb7f; trigger V367 (2 seeds at 5,300). - plant_c3: tau_rise 0.2, taper_fast, fix_x, r2m3; code d2b2ecc; triggers V377 (one seed) and V345 (one seed at 4,600). The measured effect of the fixes: p333 only, 2 used development seeds, 'not a check' (V380). Moving full-emergency events 72/63/78 went to 0/0/0, at about 10-13 % more delay for p333 under the slowdowns. A timeline column places each change against the control results (V359, V368, V395, V449) and the V459 choice of target and intended use. Baseline v4 stores policies only. Section 5 reuses the table; it is a candidate for merging into T3 (P11, M12). |
| T5 | table | Controllers compared: action, information, update interval, tuning seeds, counting and required naming | 4.1 | drawn by hand | yes | docs/research/protocols/confirmatory_3.md; docs/research/protocols/round_2.md; docs/research/protocols/round_2_prereg.md; docs/research/baseline_v3/BASELINE.md; docs/research/baseline_v3/opponents.json; /home/catalin/work/phd/v5b1_runs/round2/cma3e_x1/meta.json; /home/catalin/work/phd/v5b1_runs/round2/cma3e_x2/meta.json | Rows: - no control; p333; - the grid: 6 tuned forms with 69 rules, tuned on 7,440,160-179, plus the copy rule, traced on 7,440,180-189; entering as 12 rule arms with p333 and the copy rule included; - 3E-T (g032i20; condition T, outside the plant's stated intended use; 7,440,700-739; reference os1_15_10); - 3E-X1 and 3E-X2 (g003i02 and g016i21; 7,440,740-779; reference p333; +1 % hinge; meta.json commit null; V461); - v3w; round 2's finalists [after validation]; baseline-v3 (report-only). Columns: information, action grid and interval, counting rule, and the naming round_2.md requires (M8, M9, R16). |
| T6 | table | Readings and thresholds fixed before data | 4.7 | drawn by hand | no | docs/research/protocols/round_2.md; docs/research/protocols/confirmatory_3.md; docs/thesis/outline_v1.md; docs/research/conf3/common.py; docs/decisions.md | The statistic; CI levels by phase; counting (delay within 2 % of p333); the T2 thresholds (4 of 5 policies; close-following at least 10 % better with the CI excluding 0 and at least 20 per run lower; the side limits on delay, flow, braking, full-emergency events and collisions); harm at 95 %; the non-inferiority bound (report-only); the V459 bar with confirmatory 3's no-control clause; outcomes W/G/N, one sentence per cell, and D10 closing; the band without a verdict (outside the plant's stated intended use); the V462(1) tile rule (95 %, descriptive, logged after the validation rows and before the test rows); which readings have a no-effect null; the sign convention (M3-M8, M15, M16, R18, R21). |
| T7 | table | Protocol and plant-check elements: where defined, and the ledger event that changed a conclusion or kept a verdict apart | 5 | drawn by hand | yes | docs/decisions.md; docs/thesis/outline_v1.md; docs/research/protocols/confirmatory_3.md; docs/research/protocols/round_1.md; docs/research/protocols/round_2.md | One row per element M1-M24: its definition (protocol section or V#) and one line on its ledger event, e.g. V367, V244, V386, V401, V396 (verdict kept apart, then not replicated), V452, V405, and V99 (earlier metering line). Rows with no changing event say so: Bonferroni, non-inferiority, early KILL. The round-2 rows (M5, M7, M9) are completed after the test (M25). |
| T8 | table | T2 per cell: counting set, 3E status, learners passing, margin, limits missed, outcome; round 1 beside | 6.1 | script to write | yes | docs/research/round1/report/test_result.json; docs/research/round1/report/test_table.csv; docs/research/results/round_1_result.md; docs/research/protocols/round_2.md; /home/catalin/work/phd/v5b1_runs/round2/test_result.json; /home/catalin/work/phd/v5b1_runs/round2/cma3e_x1/final.json; /home/catalin/work/phd/v5b1_runs/round2/cma3e_x2/final.json | For v3w and each finalist in X1 and X2: - the counting opponents; - each 3E rule's counting status, with its delay against p333 and CI at validation and at test; - its tuning-seed values, in the protocol's statistic form, in-sample, with no CI: X1 +32.6 % close-following and +1.05 % delay; X2 +39.7 % and +1.64 %; common.raw; - its convergence: last against previous 10-generation median loss, X1 −30.77 against −22.51, X2 −30.92 against −26.01, still falling, so a lower bound; - k of 5 passing at T2's level; the close-following margin range against the strongest counting rule; the limits missed; the outcome W, G or N. Report-only columns: T2 without 3E (comparison with round 1, no sentence rests on it); the non-inferiority bound. Round 1's row: 5 of 5 in both cells; 35-46 % against p333 (X1) and 22-31 % against os1_15_10 (X2); 97.5 %; at most outcome G (R2, R16, R22). The two cma3e final.json files exist; round 2's test_result.json does not exist yet (R22). |
| T9 | table | Every arm and rule against no control: the V459 reading with confirmatory 3's no-control clause | 6.2 | script to write | yes | docs/research/round1/report/test_table.csv; docs/research/results/round_1_result.md; /home/catalin/work/phd/v5b1_runs/round2/thesis_v459.json; /home/catalin/work/phd/v5b1_runs/round2/test_result.json | For every arm and rule, per cell: - delay against no control with its CI at T2's Bonferroni level; - close-following against no control with the harm verdict at 95 %; - whether the bar is met; - the number of single policies meeting it. Beside it, the no-control clause: no control's TTC, delay and braking at 3 m/s²; whether at least 4 of 5 policies are clearly worse on TTC, which triggers 'no control had fewer such seconds, at [y] % more delay'; collisions per 40 runs. Round 2's input, thesis_v459.json, does not exist yet. It is written by a manual run of docs/research/round2/thesis2.py OUT VALIDATION_JSON on r2/eval (68f405a) after the test, outside the frozen chain (V460). Round 2's test_result.json does not exist yet either (R22). Round 1's 95 % columns are shown as a provisional reading, labelled exploratory (R4). |
| T10 | table | Full requirement table PR-01 to PR-28 | A | existing file | no | docs/testing/plant_vv_record_v0.md | For each requirement: verification method (I/A/D/T), evidence, status and traceability, as in record §2 at commit 6a940b3 (PR-17 and PR-20 partial; PR-18 evidence V398 for same-code replay, V437 and V461 across machines). Each non-met row points to its limit number in T19. Regenerated after the record's review (P9). |
| T11 | table | Driver and vehicle parameters by class, with source and status | A | script to write | no | docs/extracts/2026-11-05_09-18/plant_readback.json; docs/research/baseline_v1/constants.json; docs/research/baseline_v2/constants.json; v5b/fleet/fleet.py; docs/research/driver_params_hdv_cav_v0.md; docs/research/baseline_v3/env.json; docs/research/baseline_v2/plant_p0d.json; docs/decisions.md | One row per parameter and class (HDV Krauss, truck Krauss, ALKS IDM), with a status column: sourced distribution, sourced range, calibrated (V187), SUMO default, or our model. Departures from the sourced ranges are flagged with a reason or with 'no stated reason': HDV accel 2.6 against 1.8-2.2, decel 4.5 against 3-4, emergencyDecel 9.0 against 7.0-8.4, lcAssertive 1.4. Emission classes are read back. Every source is [VERIFY] (P6, P13, P14, P23; L5, L6, L7). |
| T12 | table | No-control references on the V&V target, and evidence that the command binds | A | script to write | no | docs/research/conf3/prerun_output.txt; docs/research/conf3/prerun.py; docs/research/baseline_v3/rows/conf3_tune_nc.jsonl.gz; docs/research/baseline_v3/rows/conf3_eval_map.jsonl.gz; docs/research/baseline_v3/rows/conf3_eval_primary.jsonl.gz; docs/research/results/round_1_result.md; docs/research/round1/report/test_table.csv | No-control rows on the tuning seeds (4,090, 4,600, 5,300), the evaluation seeds and the V382 pre-run. - Pre-run values in S/X1/X2: finishers' delay 88.8/147.3/129.6 s, flow 2,136/2,034/2,051 per 1,500 s, network TTC 1,206/1,389/1,664, 0 collisions. - Beside them, p333 against no control: finishers' delay +29.6 [24.8, 48.7], +19.9 [15.8, 22.1] and +12.8 [9.0, 24.8] %; flow +3.5, +4.4 and +3.0 %. 95 % CI, 10 seeds 7,440,065-074, positive = less delay or more flow (prerun.py line 54). - The 1-Hz-to-step braking ratio, 0.965-0.991. - Round 1's no-control collisions: 1 in 40 X1 runs, 0 in X2. The 'delay' (finishers) and 'all_delay' (vehicle-seconds) columns are labelled separately (P8, P19). |
| T13 | table | Steady-traffic plant check, baseline v2 (r1m3, P0d against the earlier plant; not the V&V target) | A | existing file | no | docs/research/baseline_v2/BASELINE.md; docs/research/baseline_v2/check2_table.csv; docs/research/baseline_v2/check2_output.txt; docs/research/baseline_v2/check2_rows.jsonl.gz | 20 seeds (7,440,045-064), 4 levels, r1m3, '% better' with positive = P0d better. At 5,300: delay +8.6 [+4.0, +13.1]; step braking at 3 m/s² or more +59.1; full-emergency events +78.3. C1-C6 pass; C7 fails and was counted as met with disclosure (V376). 0 collisions and 0 teleports in 80 runs. Labelled 'r1m3, P0d, not the V&V target'. Before use: the 'Undertakes' row is the pass_straight field, and baseline v1's braking columns must not be used (P7). |
| T14 | table | Conditions, demand levels, seeds and run window | A | drawn by hand | no | docs/research/conf3/common.py; docs/research/protocols/confirmatory_3.md; docs/research/protocols/round_2.md; v5b/fleet/perturb.py; docs/research/baseline_v3/BASELINE.md; v5b/fleet/corridor.py; v5b/fleet/fleet.py | Conditions S, X1, X2, H1, H2 and T, with H1, H2 and T marked 'outside the plant's stated intended use'. Levels for the plant checks, training, the confirmatory 3 cells and round 2's band. Every seed range used, for confirmatory 3, round 1 and round 2. Demand generation and the 0-1,800 s run with its 1,500-s window. Notes that the intended use starts at 4,090 and the band at 4,500 (P10, P17, M2, M10). |
| T15 | table | Side metrics per arm and cell, with road, speed and period splits and no control beside | A | script to write | yes | docs/research/round1/report/test_table.csv; docs/research/round1/report/report1_output.txt; docs/research/results/round_1_result.md; /home/catalin/work/phd/v5b1_runs/round2/test_result.json | Medians over 40 runs of every counter in confirmatory_3.md §Metrics: all-vehicle delay (vehicle-seconds), flow per 1,500 s, close-following, TTC below 1.5 and 2 s, severe samples, braking at 3, 4.5 and 7 m/s² every 0.1 s, free-road ALKS braking, moving full-emergency events, collisions, fuel (emission classes disclosed), jerk, undertakes, lane-end stops at both ramps, ramp delays, and the 1-Hz-to-step check. Splits by edge, follower speed and period add up to the deciding count. Every arm, the 3E rules and no control. Round 1's values beside, e.g. no control in X1: 325,289 vehicle-s and 1,436 close-following seconds. The follower-class split exists only for baseline-v3 (V398). Round 2's file does not exist yet (R22) (R3, R7). |
| T16 | table | Earlier readings: phase 1, confirmatory 2, 3 and 3b, round 1 (different plants and policies) | A | script to write | no | docs/research/phase1/step2_eval.jsonl.gz; docs/research/phase1/step3_eval.jsonl.gz; docs/research/phase3/decide_table.csv; docs/research/baseline_v3/decide3_table.csv; docs/research/conf3/replicate_x2_output.txt; docs/research/conf3/verification_rev4_digest.txt; docs/research/round1/report/test_result.json | Each row carries its plant, delay metric, CI level and sign convention (R1, R8, R10, R11, R12, R13): - Phase 1 on r1m3 P0: step 2, the headway action only, gave delay against p333 of +1.3 to +1.8 % at 5,300 and +0.6 to +1.9 % at 4,600 (positive = less delay; V337), a tie. Step 3 is a different actuator (speed cap plus headway, 12 actions): +0.8, 0.0 and +2.3 % at 5,300 (V339). - Confirmatory 2: 1 of 20 cells, finishers' delay, earlier plant (V359). - Confirmatory 3: X2 won 4 of 5, X1 3 of 5 (V395); its verification gave P(won) 0.27-0.30 (V396). - 3b: 1 of 5 (V401). - Round 1: T1 and T2 (V449, V452). P0 and P0d rows are labelled 'not the V&V target'. |
| T17 | table | Round 2 validation: candidates, checkpoints, advance, harm and KILLs (selection, not a finding) | A | script to write | yes | docs/research/round1/report/validation.json; /home/catalin/work/phd/v5b1_runs/round2/val/validation.json | For 2B, 1B, 1D, ahead, rep, tail and sw: the chosen checkpoints; paths (a) and (b) against v3w at 95 %; harm; floor KILL; ahead's importance KILL; the ranking key. Round 1's validation sits beside: v3w advanced, res did not qualify, attr was out by harm, lagr was out by the mechanism stop (R6). Round 2's validation.json does not exist yet; Round 2's validation.json does not exist yet (R22). |
| T18 | table | Statistic, CI levels and sign conventions per reading and stored file, with every converted number | A | drawn by hand | no | docs/research/conf3/common.py; docs/research/round1/decide1.py; docs/research/phase3/decide.py; docs/research/protocols/confirmatory_3.md; docs/research/protocols/round_2.md; docs/research/results/round_1_result.md; docs/decisions.md | The one convention used (common.raw, positive = controller under test better) and each reading's CI level: confirmatory 3/3b 97.5 %; round 1 T1/T2 97.5 %, with validation, band and no-control comparisons at 95 %; confirmatory 2 Bonferroni over 20; round 2 at 1 − 0.05/m, harm and tiles at 95 %. Each conversion applied: - V449's negated T1 values; - V448 and V461, stated as changes or in words; the cma2 final.json values (negative = better), converted for 3E-X; - round_2.md's 3E-T table (positive = more), converted, with its pooled −14.3 % (sum of TTC seconds over levels) labelled 'pooled' (R21, M3, M5). |
| T19 | table | Numbered limits L1-L27 carried by every claim sentence | 3.10 | drawn by hand | no | docs/testing/plant_vv_record_v0.md; docs/research/round1/report/test_table.csv; docs/research/protocols/confirmatory_3.md; docs/decisions.md; /home/catalin/work/phd/v5b1_runs/round2/cma3e_x1/meta.json | One row per limit L1-L27 (field 'limits'): the requirement or record §4 item it comes from, its status, the evidence and what is missing, and whether it blocks 'verified and validated' (L14, L20, L24 for PR-15, PR-24 and PR-28; V462(3)). Regenerated when the record is reviewed or a limit closes. |

## Numbered limits (V462(3))

- L1 (PR-01, partial): the network's match to its specification (3 main lanes, two on-ramps 1.2 km apart, 300-m acceleration lanes, 100 km/h) is inspected for r1m3 (baseline_v1/plant_spec.json), but the r2m3 inspection is not recorded. r2m3's acceleration lanes 3a and 4a are 294.72 m long, against a nominal 300 m (r2m3_spec.json).
- L2 (PR-02, gap): no test shows that inserted demand equals the configured level and ramp share (70/15/15, corridor.py) within sampling error at every level.
- L3 (PR-03, partial): that the insertion queue is counted and no vehicle is dropped rests on baseline v1's door-to-door table, on r1m3, not on r2m3 plant_c3.
- L4 (PR-04, partial): no share test is located. The readback over 106,128 draws, on r1m3 routes, gives HDV 42.76 %, trucks 7.68 % and ALKS 49.56 %, against 42.5, 7.5 and 50 % configured (plant_readback.json).
- L5 (PR-05, partial): the parameter-by-parameter source table is not written. HDV tau scale 0.8 and action-step scale 0.5 were calibrated on the human-only ld32 lane-drop corridor (V187, V188); the realised HDV tau mean is 0.934 s, against a sourced 1.15 s [VERIFY]. HDV accel 2.6, decel 4.5 and emergencyDecel 9.0 m/s² are SUMO defaults above the sourced ranges of 1.8-2.2, 3-4 and 7.0-8.4 [VERIFY]. lcAssertive 1.4 has no source.
- L6 (PR-06, partial): the ALKS parameters as SUMO applies them (IDM, tau 1.6 s, accel 2.6, decel 4.5, emergency 9.0 m/s², action step 0.5 s) rest on ALKS_READBACK in b_merge, whose test is not located.
- L7 (PR-07, gap): no analysis shows the ALKS tau and deceleration limits to be consistent with UN R157. The R157 table behind tau 1.6 s covers speeds up to 60 km/h only [VERIFY], while the plant commands 0.8-1.6 s at up to 100 km/h.
- L8 (PR-08, limit; record §4): lane changing (lcAssertive 1.4) is our model, not validated against real traffic. Baseline v2 reports 14 'undertakes' per run among about 1,300 ALKS at 5,300 on r1m3; that row is the pass_straight field (P7).
- L9 (PR-09, met for round-1 arms; record §4): the smooth no-undertaking rule (look-ahead 8 s, above 60 km/h, ratio 1.1 per s, braking at most 4.4 m/s², run in b_env) is our model, not validated against real traffic. Its step-braking check passed on every round-1 test arm on plant_c3 (V451). It must be read again for round 2's arms from the 1-Hz against step-braking check.
- L10 (PR-10, partial): there is no r2m3 T0 record. The V382 pre-run (10 seeds 7,440,065-074, 5,300 veh/h) is partial evidence that the command binds and changes delay and flow.
- L11 (PR-11, partial): that commands reach only ALKS rests on COMMANDED = ('alks',); the test in test_fleet_control.py is not located.
- L12 (PR-13, partial): X1 and X2 (edge, speed, duration, start, taper) are checked through taper_fast and fix_x (V380), and V446 checks the 0.1-s taper for the training draw. The X1/X2 record is not written, and no stored file gives a field source for the X1/X2 values.
- L13 (PR-14, met from input revision 4): policies trained before revision 4 (phase 1, confirmatory 2) had hand-scaled inputs and a dead input (V387-V389). This affects history rows only.
- L14 (PR-15, gap): no inspection shows that policy inputs carry no information a real vehicle could not have (seed, event timing or future state). It must close before 'verified and validated' is used (V462(3)).
- L15 (PR-16, limit; record §4): V2V is ideal within 150 m, and roadside speeds are ideal, with no latency or loss (confirmatory_3.md Disclosures).
- L16 (PR-17, partial since V462, commit 6a940b3): the requirement now reads 'No teleports; collisions rare, counted and reported for every arm'. Baseline v2 gives 0 collisions and 0 teleports in 80 runs, but on r1m3 P0d in steady traffic, which is not the V&V target. On plant_c3, no control had 1 collision in 40 runs in round 1's X1 test and 0 in X2 (test_table.csv collisions_total). There is no plant_c3 no-control check. Collisions are too rare to compare.
- L17 (PR-20, partial since V462): the 3E-X search's meta.json records 'commit': null (deploy folder code/6c49e7e without .git; cma2.py's sha256 fed9bdc0… is recorded; V461). Round 2 resumes rows by (name, q, seed) without a config hash (V455). SHA256SUMS is in git for baselines v0, v1 and v4 only; v2 and v3 have one only in the read-only copies.
- L18 (PR-21, partial): that door-to-door delay includes origin and insertion queues and counts unfinished vehicles to the window end rests on V307. The unit test on a hand-computed case is not located.
- L19 (PR-23, partial; record §4): close-following is read at 1 Hz in the confirmatory readings. The 0.1-s meter E1 has 6 unit tests on synthetic traces (V435) but has not run on any test arm.
- L20 (PR-24, gap): only short gaps (V283) and passes on the right were traced on a sample; every other reported counter lacks its trace. It must close before 'verified and validated' is used (V462(3)).
- L21 (PR-25, partial): no r2m3 T1 record shows congestion forming at the merges without teleport or deadlock artefacts. The record's evidence cites DRL results (V405), which is circular. The article uses the V382 pre-run (p333 against no control, finishers' delay, 95 %) instead, which is still 10 seeds at one level.
- L22 (PR-26, gap; record §4): the capacity drop is not settled. The V271 estimator has no null (V244), and no comparison with a published range exists for r2m3.
- L23 (PR-27, gap): per-lane flows and speeds are not compared with field detectors (MnDOT via Mayfly is only proposed). Lane-level tables exist only for r1m3 P0 (baseline v1).
- L24 (PR-28, gap): merge-2 lane-end behaviour is not validated. There are 608.5 lane-end stops per run at ramp 2 against 7 at ramp 1 (r2m3 P0d at 5,300, no control, baseline v2, report-only), and 46-61 % of confirmatory 3's X2 gain against os1_15_10 sat on 4a plus ramp 2 (V396). It must close before 'verified and validated' is used (V462(3)).
- L25 (record §4): the SUMO model (1.27.1) is uncalibrated. No absolute travel time or capacity is claimed (record §1 'Not for').
- L26 (record §4): the geometry is synthetic: one network, with merges 1.2 km apart. Other spacings are untested (confirmatory_3.md Disclosures).
- L27 (record §4): lateral and merge conflicts are not measured. Close-following is longitudinal TTC only.

## Reviewer objections and answers

1. 'Verified and validated' overclaims for an uncalibrated synthetic plant with open gaps and no field comparison. Answer: - the article does not use the phrase in any title, abstract or claim sentence until the record is reviewed and PR-15, PR-24 and PR-28 are closed (V462(3)); - the record's acceptance clause ('every requirement below is met, or its gap is stated as a limit that every claim sentence carries') is met by citing limits L1-L27 in every claim sentence; - every status is shown (T3, T10, T19), with PR-17 and PR-20 re-graded to partial (commit 6a940b3); - the intended use and its 'Not for' list are quoted word for word (3.1); - 'proven' never appears (V456).
2. Some reported rows lie outside the plant's intended use. Answer: they are labelled 'outside the plant's stated intended use', not added to the use (V462(4)). These are the band and 3E-T's condition T (random training draw on edge 3, 4 or 5 at 25-60 km/h), and panel C's H1 and H2. None decides a claim. History rows on P0 and P0d are labelled 'not the V&V target'.
3. The plant co-evolved with the controllers, and the V&V record is retrospective. P0 became P0d and then plant_c3 after control results were known (V359, V368); the fixes cost p333 about 10-13 % delay (V380, 2 used seeds); P0d's look-ahead and braking limit were chosen after a check failed; the own-state family and the reward were shaped by runs that knew p333; the intended use was written after rounds 1 and confirmatory 3 (V459). V245's caveat asks for controllability fixed before control results. Answer: - T4 gives the timeline against the control results; - each change corrected a measured defect (V367 hidden 9 m/s² braking; V377 instant tau rise; V345 untapered slowdowns), not a controller ranking; - the timing is disclosed (3.1, 3.9, 4.3); - plant_c3 stays unchanged for every later chapter (V456(3), V457(2)).
4. Control may 'win' through a plant artefact at merge 2. Ramp 2 has 608.5 lane-end stops per run against 7 at ramp 1 (baseline v2, report-only), and 46-61 % of confirmatory 3's X2 gain against os1_15_10 sat on 4a plus ramp 2 (V396). Answer: - PR-28 is a gap (L24), and it blocks 'verified and validated'; - section 6.4 reports where every gain sits, by road, speed and period (T15), and every win sentence names the share on 4a plus ramp 2. - V398 is quoted in full (exploratory, baseline-v3 only, 97.5 %). Excluding lane 4a_0, the gain against os1_15_10 stays at +15.9 to +29.9 %. But 'on the 4a mainline lanes, policies have more TTC than r4a1 (d0 −45.7 [−65.5, −13.7] %) and far more than no control: part of the gain is moved from the accelerating lane to the mainline'. ALKS followers are above no control (−13 to −42 %). - Closing PR-28 before submission is an open decision; the record (§5) ranks it first.
5. 'Beats no control' is trivial. Answer: - section 6.2 says that the delay half is unlikely to fail on this plant: in the exploratory sweep, every controller had at least 10 % less delay than no control even at 2,500 veh/h (V419, baseline-v3, 10 seeds; outside the plant's stated intended use), from shorter headways, not learning; - the V459 bar adds the close-following harm clause, which can fail: in round 1's X1 every rule was worse than no control on close-following (os1_15_10 −78.4, p333 −114.4, common.raw, 95 %, exploratory); - confirmatory 3's no-control clause is carried beside the bar; - the verdict against tuned rules rests on T2, not on no control; - no no-effect null exists for the 10 % bar (disclosed in C2 and 4.8).
6. The opponents are weak: no MPC or adaptive controller, 3E-T truncated at 40 of 100 generations, 3E-X one search per cell, rules tuned only at 5,300. Answer: - per-cell CMA-ES rules tuned on separate seeds count as opponents, next to a grid of 70 rules tuned per cell, and T2 is an intersection over every counting opponent; - each 3E rule's counting status, tuning-to-test drop and convergence are reported (T8, 6.3); - 3E-X's tuning values use the protocol's statistic form but are in-sample, with no CI; - by final.json's own check both 3E-X searches were still falling at generation 40, so 3E-X is disclosed as a lower bound (round_2.md); in X1 the more-converged points failed the 2 % admission cap; - the band and map cells are hatched, with no claim; - the missing MPC is disclosed and deferred to RQ4 (V457). An MPC that ignores capacity-drop hysteresis would be a straw man (L62, FT-kw, [VERIFY]).
7. Cell selection and map breadth: X1 and X2 were chosen because DRL already looked best there, and the 'map' has only 2 deciding cells at one demand level. Answer: - the selection is disclosed (confirmatory_3.md: 'This run is chosen after those results, on the cell where DRL already looked best'; round_2.md Disclosures); - the contribution is described as 'a two-cell decision map with report-only band and history panels' (V462(2)), and no title says 'operating map'; - 'Only 2 conditions decide the claim' is quoted in every result sentence; - the only multi-condition map is for baseline-v3 and 'supports no claim'.
8. Garden of forking paths: X2 has been tested four times and X1 three times on plant_c3; X1 was reopened after [A3] closed it; the no-control bar was set after confirmatory 3 and round 1 were known. Answer: - F7 and T16 show every test, including the 3b failure and confirmatory 2's 1 of 20; - round 2's readings, the D10 rules and the allowed sentences were fixed before its data (round_2.md at c1bf797; outline §3 wording amended after validation rows existed and before any test row, V462(2), V463); - the missing correction across rounds, the reopening of X1, the timing of the bar, and the claim review after the data (V459(4)) are disclosed (4.3, 7.4).
9. The deciding measure, TTC below 3 s at 1 Hz, has no literature source, is mostly a low-speed queue, and is also a reward term, so the policies are taught to the test. Answer: - it is called 'close-following', a surrogate, and 'safety' is gated by the severe-conflict check; - what the count is made of is stated: median follower speed 5-7 m/s on one seed (confirmatory_3.md Metrics; V377: 48-62 % below 7 m/s, 61-79 % with a stopped leader on 4a or ramp 2), so stopped-queue proximity is not claimed as a safety result (the V283 lesson); - every win sentence reports the follower-speed split (round 1 X2: 10 m/s or more 230 [179, 249] TTC samples, under half the gain); - the follower-class split exists only for baseline-v3 (V398: ALKS followers hold 58-66 % of TTC seconds); - counters outside the reward are reported: braking every 0.1 s, full-emergency events, severe samples, collisions, and TTC below 1.5 s and 2 s (SSAM default 1.5 s, L80, [VERIFY]); - running the 0.1-s meter E1 on the stored test arms is an open decision (L19).
10. Many tiles, no multiplicity control: each cell × measure × opponent gets a glyph. Answer: - the tile rule is fixed in V462(1): a 95 % percentile bootstrap on the arm, W at 10 % on close-following or 5 % on delay with the CI lower bound above 0, L by round 2's harm rule, T otherwise; - it is labelled descriptive, and no tile is a verdict: only T2, at its Bonferroni level, and the V459 bar decide; - it was logged after round 2's validation rows existed (validation started 17:06, V461) and before any test row; this is disclosed (4.3).
11. The statistics are fragile. The percentile bootstrap of a median with a fixed denominator has unknown coverage at Bonferroni-extreme percentiles with n = 40; learner variance is excluded; the 4-of-5 vote rests on a plug-in power estimate; the 2 % point delay rule passes a truly 2 %-worse policy 52 % of the time (V435). Answer: - per-learner counts appear in every tile; - the 5 % non-inferiority bound is reported beside T2 (D11), with V435's power figures; - harm is read at 95 %, so Bonferroni cannot hide it; - the CIs are stated to cover evaluation seeds only; - confirmatory 3's seed-bootstrap P(won) of 0.27-0.30 is reported (R11); - a coverage simulation, a learner-variance analysis and a seed bootstrap of round 2's T2 are open decisions.
12. The margins (2 % delay, 10 % and 20 per run on close-following) are internal choices. Answer: - their origin is disclosed: V363 set the 10 % close-following and 2 % delay numbers, in an exploratory rule; V346 set the 20-per-run margin; - the options memo's F4 (docs/reports/2026-11-05_21-29/drl_options_2026-11-05_21-29.html) computes the exchange rate the bar implies, 19-23 vehicle-seconds per close-following second, which agrees with the bar but is not its source; - the margins were fixed before round 2's data; - every tile shows the effect and CI, not only the verdict, so a reader can apply another margin; - any re-reading at other margins is labelled exploratory and changes no verdict.
13. Checkpoint selection departs from 'final policy only', so part of the gain is in-sample. Answer: selection uses validation seeds only, and the test on 40 fresh seeds runs once. tail has no selection. The in-sample gain from round 1's split-half analysis (0.2-0.3 points of delay, 0.8-1.5 points of close-following) is disclosed (round_2.md Arms; section 4.1).
14. The comparison is unfair to one side: the rules know the condition and the level, while the policies act every 10 s on 4 discrete levels. Answer: the asymmetries in both directions are tabulated (T5) and discussed (sections 4.1 and 7.3). The actuator is fixed by the intended use and is the same for every arm.
15. The driver model is weakly grounded: the HDV scales were calibrated on a different, human-only corridor (V187); several values are SUMO defaults above the sourced ranges; lcAssertive 1.4 is unsourced; there is no sensitivity analysis. Answer: T11 gives each parameter a status column and flags each departure. These are limits L5 and L8, cited by every claim sentence. The claims are paired comparisons, but the article does not claim the ranking is insensitive. A one-factor sensitivity check after round 2 frees the CPU, and adding it to the record as a requirement, are open decisions.
16. The window and demand are questionable: a 300-s warm-up on 6.8 km, a queue that never clears within the 1,500-s window at 5,300, and constant Poisson demand. Answer: - all-vehicle delay counts unfinished vehicles and the insertion queue; - the V398 3,000-s replays and the V410 demand profiles (outside the plant's stated intended use) are reported as exploratory robustness rows (baseline-v3 only); - the band covers 4,500-6,000 veh/h, labelled outside the intended use; - constant demand and the unchecked warm-up are stated threats (7.2). Making them record requirements, and so numbered limits, is an open decision.
17. Vehicles labelled ALKS receive commanded headways down to 0.8 s at up to 100 km/h, while the tau 1.6 s source is an R157 table that covers speeds up to 60 km/h only. Answer: the R157 consistency analysis is a gap (PR-07), stated as limit L7 in every claim sentence. 'ALKS' names a vehicle class in the model, not regulatory compliance. What R157 permits at these speeds is not settled in the repo and needs checking against the regulation text [VERIFY].
18. What is new relative to Vinitsky et al. or Elmorshedy? Answer: the article makes no novelty claim. It positions itself by its question and its evaluation practice (section 2, T1), without claiming any absence, and every literature statement keeps its read level and [VERIFY]. A systematic WoS/Scopus search before any absence statement is an open decision.
19. Pre-registration is internal and therefore weak. Answer: the protocols carry commit hashes and dated approvals in the ledger (M1). Disclosed: - the approval read from 'Go on' (V454); - round_2.md's 'draft, revision 2' status line; - round_2.md written after training and 3E-T's search; - thesis2.py added after approval (V460); - the tile rule logged after the validation rows (V462(1)); - confirmatory 2's missing review (V356). An external timestamped deposit, at least before submission, is an open decision.
20. Reproducibility and deviations: 3E-X ran on a rented machine and its meta.json records no commit; confirmatory 3 ran on two commits; round 2 resumes rows without a config hash. Answer: - replays reproduce stored rows (V398: 200 base replays, 28,555 keys, same code); - rows are equal across machines (V437; V461, 3 seeds per cell, 8 keys each); - hashed stored files (SHA256SUMS in git for v0, v1, v4, and in the read-only copies for v0-v4), frozen commits and the pinned toolchain are listed; - each deviation is disclosed and is limit L17.
21. Mixed sign conventions and metric names make the numbers hard to audit: V452 found mixed signs, and 'undertakes' is ambiguous. Answer: one convention is stated once (T18), and every imported number is converted with its source convention named (V449, V461, cma2 final.json, round_2.md's 3E-T table). The undertake field is resolved before the word is used (P7).
22. A null result is not a contribution. Answer: the question is answered either way. The map shows where these policies win, tie or lose against strong, fully reported opponents, and section 5 shows the readings changing earlier conclusions. The venue choice should favour journals that accept null results (open decision).

## Open decisions (for the author)

1. Record changes still to make, then the review (V459 step 3). Commit 6a940b3 already re-graded PR-17 and PR-20 and fixed PR-18's evidence. Remaining: (a) PR-25: replace the V405 evidence, which rests on DRL results, with the V382 pre-run (p333 against no control) and a no-control T1 record; (b) extend record §4 to the numbered limits L1-L27, matching T19; (c) review the record. Recommended before section 3 is drafted.
2. Close PR-15, PR-24 and PR-28, the precondition for any 'verified and validated' (V462(3)). Compute this after round 2 frees the CPU, together with: - PR-25, a T1 congestion record on r2m3; - PR-26, the capacity drop with a null; - PR-27, the MnDOT comparison; - PR-07, the R157 analysis [VERIFY]; - a no-control space-time contour and lane tables; - a plant_c3 readback with the ballistic log line. Decide which gaps to close and which stay as limits.
3. Add record requirements, and so numbered limits, for threats that are not yet requirements: the warm-up and window check on 6.8 km; parameter sensitivity; constant Poisson demand (the X1/X2 field source is already L12). Until then they are threats in 7.2, not limits.
4. Venue: not chosen. docs/paper1/main.tex uses a generic article class, and only sections/introduction.tex exists, as a 3-line placeholder. Criteria: - accepts null results and decision-map results; - a word limit compatible with about 10,000 words plus supplementary material; - an abstract limit that fits the verbatim sentences (about 400 words), or the author's choice of which verbatim items the abstract carries; - LaTeX class; data policy; review time against the September 2027 submission. Also decide on one .tex file per section, with tables generated from stored results (V457).
5. Title: pick one of the four options. 'Verified and validated' is excluded by V462(3). Still open: whether 'pre-registered' may appear, given the internal registry.
6. Display items: the main text has 8 figures and 10 tables, counting T19. Candidates to move to the supplement or merge: F8 into F5 panel B; T4 into T3; T19 into T3; T1 shortened into text; F6.
7. Which arms the article reports: v3w only, or also round-2 finalists. This depends on validation. If sw, tail, rep or 1B reaches the test, use the round_2.md naming.
8. Action after round 2's test: run thesis2.py OUT VALIDATION_JSON on r2/eval (68f405a) by hand, because chain2.sh does not call it (V460). Without it, T9 and the V459 reading have no input.
9. Undertake naming (P7): decide whether claim text means pass_straight or undertakes before the word appears.
10. Report-only extras, each labelled exploratory: - the 0.1-s TTC meter E1 on round 2's stored test arms (L19); - a bootstrap coverage simulation (M4); - a learner-variance analysis (M23); - a seed-bootstrap fragility analysis of round 2's T2, as V396 did for confirmatory 3 (R11); - a no-effect null for the 10 % delay bar (M16); - a follower-class split for v3w, which today exists only for baseline-v3 (V398).
11. History scope: show confirmatory 2 and phase 1 (earlier plants, finishers' delay) as a separate panel of F7, keep them in T16 only, or omit them. Also decide whether confirmatory 3's map cells stay as F5 panel C.
12. Whether article 1 goes out without a non-learning adaptive or MPC opponent (disclosed; RQ4 deferred) or waits for the V457 parallel track.
13. Calibration transfer from ld32 (V187) and the HDV defaults above the sourced ranges: a written justification, or limit L5 as it stands. Changing the plant now would invalidate rounds 1 and 2.
14. Literature before drafting section 2: - run a systematic WoS/Scopus search before any positioning sentence (prior_art_A_v0.md); - read in full, or keep [VERIFY]: IEEE 1012, Sargent, FHWA TAT vol. III, R157, and the L-items read only as abstracts or by agents; - add citations for PPO, CMA-ES, the bootstrap, Bonferroni, non-inferiority and pre-registration; - verify the general-knowledge candidates (Henderson 2018, Agarwal 2021, Colas 2018); - fix the references.bib defects (audit LIT-F1, LIT-F2, LIT-F9).
15. Record round 2's approval explicitly: round_2.md's status line still reads 'draft, revision 2', and V454 infers the approval. Also decide on an external timestamped deposit of the protocol.
16. Sign convention: adopt common.raw throughout and convert the numbers from V448, V449, V461, the cma2 final.json files and round_2.md's 3E-T table. Recommended; needs the author's confirmation.
17. Fuel placement: fuel is counted, so it is reported, never omitted. Leaving it out would be a hidden variant (CLAUDE.md). It goes in T15 with its disclosure: cars HBEFA4/PC_petrol_Euro-4 and trucks HBEFA4/TT_AT_gt34-40t_Euro-VI_A-C (plant_readback.json, r1m3 routes). Open: supplement only, or one line in the main text.
18. Code and data release policy, and the matching availability statement.
19. Author list and the supervisor's role: not recorded in the files read.
20. Abstract length: the templates quote confirmatory 3's and round 2's clauses verbatim and run to about 600 words, against a usual limit of about 250. Proposed: the abstract keeps the outcome sentence per cell, the model sentence, 'within limits L1-L27' and one scope sentence, and points to section 7.1 for the full 'What this cannot show' lists, verbatim there. This changes where the verbatim clauses appear, so it needs the author's decision (V#) before the abstract is written.
