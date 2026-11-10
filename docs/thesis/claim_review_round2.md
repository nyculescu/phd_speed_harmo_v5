# Claim review after round 2 (V459), 2026-11-07

Status: review result for the author; nothing here is approved. Inputs: `docs/research/results/round_2_result.md` at e5543fa (V465-V467), outline §3, round 2 and confirmatory 3 protocols, the stored test rows. Method: 5 independent reviewers (outcome mapping, recomputation, `thesis2.py` code, wording, hostile examiner), one adversarial verifier per reviewer, one synthesis (ultracode; 11 agents). Full agent output: session scratchpad `claim_review.json`.

## 1. Outcome per cell

| Cell | Against tuned rules | Against no control (V459) |
|---|---|---|
| X1 | W, with the 3E-T bracket. Claimable under V459 only if the [A3] history goes in the same paragraph and the author logs decision D1. Not answered against 3E-X1. | not met (all three arms harmed on close-following) |
| X2 | N: the DRL claim against tuned rules closes in X2 under D10's T2 reading (V466). G's condition also holds; I recommend N precedence (decision D2). | met (harm not shown; sw's CI reaches 12.1 % more close-following) |

**X1.** T2: v3w, tail and sw each pass 5 of 5 against the counting rules p333, os0_10_10 and 3E-T (round_2_result.md:7, :190-192). Four independent codes reproduce this from test/rows_6c49e7e.jsonl. 3E-T counts at -0.94 (report:147), so W's condition 'a CMA-ES rule counts' holds (outline_v1.md:47), with the bracket '3E-T: a rule tuned by CMA-ES under the training slowdowns, not for this cell'. 3E-X1 is excluded at -2.31, so the reading against it is 'not answered against the CMA-ES rule: not within the delay filter' (round_2.md:74, :244; report:260-263). The win has slack: smallest margin 14.66 %, lowest 99.17 % lower bound 9.07 %, smallest delay slack 4.29 points (recompute rc7.py, verified). Post hoc: it stays 5/5/5 with 3E-X1 counting and under either alternative counting estimator. D10 does not close X1 (report:439). But [A3] closed X1 earlier (confirmatory_3.md:132; decisions.md:415 V395). The author re-picked the cell in V420 (decisions.md:440) and V423 without addressing [A3]. round_2.md:312-316 disclosed this before round 2's data (V453, V454). V459 (decisions.md:479) set round 2's T2 as the bar after that disclosure, so W stands, but only with the history carried (D1). Against no control (V459; arm level; delay at 99.17 %, harm at 95 %): v3w delay +27.3 [24.4, 31.1], TTC -16.6 [-25.1, -8.4]; tail +27.9, -15.3 [-27.1, -6.7]; sw +27.9, -18.4 [-27.4, -7.1]. All three are harmed. Single policies meeting the bar: 1, 0 and 0 of 5 (report:406-408; thesis_v459.json, recomputed to 1.07e-14). The verdict does not change if harm is read at 99.17 % (upper bounds -3.28, -2.25 and -6.05).

**X2.** T2 is not won. With 3E-T (-1.81) and 3E-X2 (+1.48) counting, v3w passes 2 of 5, tail 3 and sw 0 (report:11, :148, :190-192; recomputed independently). Both outline conditions hold. G, 'wins only against the grid', holds because the grid-only T2 is 5/5 for every arm (report:195). N, 'no T2 win where a 3E rule counts', holds too (outline_v1.md:48-49). I settled this from the protocol. D10's closing is mandatory in this case (round_2.md:261). Q2 prescribes 'reported as not won, with round 1's win beside it' (round_2.md:16). Line 243 says no sentence rests on T2 without 3E. Only N's row carries all three. G's 'limits missed' content (round_2.md:245) goes inside the N sentence, and the grid result is labelled as a comparison with round 1. 'Did not beat' must be reworded, because every arm has fewer close-following seconds and less delay than both rules by point estimate (report:13, :206-208). The negative depends on 3E-T counting 0.19 points inside the filter, and on the estimator: under either ratio estimator tail passes 4 of 5 (report:150-152, :445). The closing reading was decided after the test data (V466), but the frozen run code already closed on T2 alone (6c49e7e test2.py:84-87). Against no control: delay is 23.1-23.5 % lower with 99.17 % CIs above 0. TTC is v3w -0.9 [-5.8, +9.5], tail +1.4 [-4.4, +8.7], sw -6.7 [-12.1, +2.6], with every 95 % CI including 0. 5 of 5 single policies meet the bar for each arm (report:410-412). So 'met' means harm was not shown, not that there was no harm.

## 2. Blockers and major issues (after verification)

- No blocker survived verification. Every finding raised as a blocker (mapping F1 and F2, wording B1-B3, examiner F1) was downgraded to major, because no thesis or article sentence has been filled yet; the defects sit in the approved templates.
- MAJOR [A3] history: outline §3 (outline_v1.md:39, :47) and the W abstract template (plan.md:81) omit that [A3] closed X1 before rounds 1 and 2 re-tested it. Needs decision D1 and the history in the X1 sentence (mapping F1, examiner F3, wording M2).
- MAJOR D4 item: carried verbatim as outline:41 requires, round_2.md:345's 'With D4, it shows this...' misleads for both cells (3E-X1 did not count; 3E-X2 was not cleared). It needs the per-cell fill (mapping F2, wording B1).
- MAJOR X2 outcome form: X2 meets both G (outline:48) and N (outline:49), and the outline sets no precedence. N's 'did not beat' misreads a cell where every arm is better by point estimate. Needs decision D2 (mapping F4, examiner F1, wording M4).
- MAJOR fragility: in both cells the outcome depends on the counting filter's estimator. In X2 it also depends on 3E-T counting 0.19 points inside the filter (tail passes 4/5 without it). Outline:41's carry list lacks the Disclosures (mapping F6, wording M4, examiner F6).
- MAJOR 'fixed before data': the titles (plan.md:30-32), C2 (plan.md:52, :63), s4_the_reading.tex:65-78 and outline:5 omit V466 and V467, both decided after the test data (wording M1, M7).
- MAJOR naming: filled literally, outline:49's 'these per-CAV PPO policies (v3w[, finalists])' and plan.md:81, :89, :95 would call sw a per-CAV PPO policy, which round_2.md:249 forbids (wording B3; mapping F7).
- MAJOR W's '[x] % [CI]': the form is undecided (point range, envelope of CIs, or arm CI), and the report has no X1 CI at T2's 99.17 % level. Needs decision D4 and a report2.py addition (recompute R-W-CI).
- MAJOR V459 wording: 'close-following not harmed' (outline:51; plan.md:81, :89, :95; report:400) only means harm was not detected. sw's X2 CI reaches -12.1 %. Write 'not shown to be harmed' with the CI (code CV-2; examiner F7).
- MAJOR 'safety' in X1: the protocol permits it (report:287-289), but the X1 policies are worse than no control on every TTC threshold and on step braking at 3 m/s². Needs decision D5 (examiner F5).
- MAJOR teaching to the test: the 'counters outside the reward' label (report:319; round_2.md:338; plan.md:508, :642) is wrong. Braking at 3 m/s² is charged in the reward, and TTC<2 s, TTC<1.5 s and DRAC are nearly subsets of the rewarded TTC<3 s event for ALKS pairs (examiner F4, as corrected by its verifier).
- MAJOR 3E-X1 frontier: X1's 16-24 % margin is set by where the 2 % delay filter cuts the rule family; the lower-loss 3E-X1 points failed the cap at 2.4-2.6 % more delay. The X1 sentence must say so (decision D6; examiner F2).
- MAJOR V&V gaps under X1's W: the gain is partly on merge 2 (L24, PR-28 open), the record is a draft, and PR-15 and PR-24 are open. The X1 sentence must cite them, and the W wording should wait for a lane-level trace before submission (examiner F9).

## 3. Decisions for the author

### D1. May X1's W enter the thesis claim, given that [A3] closed X1 (V395) and rounds 1 and 2 re-tested it without any entry addressing [A3]?

- **Recommendation:** Yes, as W, with the history in the same paragraph as the X1 sentence. Add a ledger entry, dated after the data and disclosed as such, that records four things: [A3]'s closure was overridden implicitly by the V420/V423 choice of cells; round 2 disclosed it before its data (V453, V454); round 2's X1 test is the claim basis; there is no correction across rounds.
- **Pros:** It follows V459, which set round 2's T2 with D10 as the bar after V453 had disclosed the closure. X1 is the round's most robust reading: won in 99-100 % of seed resamples, with the CI part surviving Bonferroni at m > 500. The history becomes explicit instead of implied by plan.md's word 'reopened'.
- **Cons:** An entry made after the data can look like a rescue. Examiners may still count X1 as a forking path. Every X1 sentence carries a long history.
- **Alternatives:** (b) Move X1 to the history panel and rest the claim against rules on X2 (N) alone. Inferior: it discards a reading the approved bar names, and the discard would itself be a post-data choice. (c) W without the history. Inferior: misleading, and it contradicts round_2.md:312-316. (d) Declare X1 not claimable under [A3]. Inferior: round 2's approved protocol tested X1 knowing of the closure, and V459 was set after that.

### D2. X2 meets both G (outline_v1.md:48) and N (outline_v1.md:49). Which sentence form does X2 take, and what precedence rule does the outline state for future cells?

- **Recommendation:** Use the N class with G's content inside it: 'did not clear T2 against 3E-T and 3E-X2 (2 of 5, 4 required; limits missed: margin and CI); the DRL claim against tuned rules closes in X2 (D10, T2 reading, V466)'. Add the arm-level direction, round 1's win beside it, and the grid-only 5/5 labelled 'comparison with round 1; no sentence rests on it'. In the outline, N takes precedence whenever D10 closes a cell, and N's 'did not beat' becomes 'did not clear T2 against'.
- **Pros:** It carries D10's mandatory closing (round_2.md:261) and Q2's 'reported as not won, with round 1's win beside it' (round_2.md:16). It respects round_2.md:243, and no sentence opens with 'Won' in a cell that was not won.
- **Cons:** It sets aside round_2.md:245's specific G sentence, which the report uses (report:273). It needs an outline wording change after the data, though the bar is unchanged.
- **Alternatives:** G alone: it omits the mandatory closing, so inferior. G plus a closing clause (the examiner's option): the content is acceptable, but the sentence opens with 'Won against confirmatory 3's grid', which rests on T2 without 3E (round_2.md:243) and reads as a partial win in a closed cell. N verbatim with 'did not beat': misleading, because every arm is better by point estimate (report:208).

### D3. Scope of V467 and of the V459 reading. Does V467's 'every reading that feeds a sentence at T2's level' also move V459's harm half off 95 %? Is the arm-level reading, which V460 logged but no entry decided, confirmed?

- **Recommendation:** Log one line: V467 covers confirmatory 3's beside readings and the V459 delay half. V459's harm half stays at 95 % (round_2.md:197; plan.md:125). V459 is read on the arm (per-seed mean over 5 policies), with the single-policy count beside it (V460).
- **Pros:** It keeps the protocol's stated reason, that a corrected CI would hide harm, and removes a two-level ambiguity. No verdict changes either way: at 99.17 % the X1 arms stay harmed (upper bounds -3.28, -2.25, -6.05).
- **Cons:** It adds one more post-data entry, and the no-control sentence shows two CI levels.
- **Alternatives:** Harm at 99.17 %: favours DRL (single-policy counts rise: v3w 1 to 2, tail 0 to 1, sw 0 to 1), against V467's own direction. A 4-of-5 per-policy rule instead of the arm: same verdicts, but it departs from V460's code, committed before validation (68f405a, 15:19).

### D4. What form does W's '[x] % ... [CI]' take, and how is 'the share on 4a plus ramp 2' (plan.md:81, :437) computed?

- **Recommendation:** For [x]: the per-policy point range against the strongest counting rule, each policy's 99.17 % CI above 0 with the lowest lower bound, and the arm-level 99.17 % CI beside. For X1 v3w: 16.3-24.2 %; lowest lower bound 9.1 %; arm 20.3 [15.2, 23.6]. Add these to the report through report2.py before citing. For the share: quote the road medians with CIs and L24, as the report does. Put any share only in section 6.4, as a post-hoc ratio of sums (v3w 47.7 %).
- **Pros:** It matches T2's unit (single policies) and confirmatory_3.md:118's range form, and it introduces no undefined statistic into a claim sentence.
- **Cons:** The sentence gets longer, and plan.md:83 and :437 must change.
- **Alternatives:** Envelope of per-policy CIs (9.1-36.2 %): wide, and mixes policies. Arm CI only: the top of the policy range (24.2) lies above the arm CI's upper bound (23.6), and T2 is not read on the arm. Share as (107+80)/457 = 40.8 %: medians do not add, and the estimators span about 7 points for v3w.

### D5. Is the word 'safety' used for X1, where the severe check is met (report:226, :287-289)?

- **Recommendation:** No, not in the claim, abstract or titles. Write 'fewer seconds at 1-Hz TTC below 3 s than the counting rules'.
- **Pros:** It is stricter than the protocol, so it adds no post-data bias toward DRL. In X1 the policies are worse than no control on every TTC threshold and on step braking at 3 m/s². The flag is a reward term, and E1 has not run.
- **Cons:** It gives up a word the pre-registered protocol permits.
- **Alternatives:** Use it with the two companion clauses (report:287-289): permitted, but invites being quoted alone as an absolute safety result. Use 'safety against the counting rules only' (V396): still easy to strip of its qualifier.

### D6. Is X1's W described as 'beats tuned rules', and should 3E-X1's lower-loss shortlist points (g028i09, g038i05, CMA mean) be run on fresh seeds?

- **Recommendation:** Describe X1 as a T2 win against the rules the 2 % filter admitted, and carry the shortlist disclosure (2.44, 2.64 and 2.38 % more delay than p333 on tuning seeds; plan.md:431). Run nothing now. If the author later wants a frontier figure for examiners, approve a report-only run of the three points on unused reserved seeds; it would never be a reading.
- **Pros:** The scope is honest. No new seeds, CPU or post-data opponent are needed now.
- **Cons:** An examiner may still ask for the fresh-seed frontier.
- **Alternatives:** Run them now as a reading: a post-data opponent, which is a hidden variant. Say nothing: leaves the obvious objection (plan.md:639) half-answered.

### D7. How is 'met' against no control in X2 worded?

- **Recommendation:** 'Met; close-following not shown to be harmed', with each arm's 95 % CI. For sw add: 'its CI reaches 12.1 % more, so harm beyond the 10 % margin is not excluded'. Never write 'not harmed' or 'beats no control'. Say beside it that every rule meets the delay half.
- **Pros:** It matches confirmatory_3.md:126's own wording rule, and it is descriptive: no new reading.
- **Cons:** The headline is weaker.
- **Alternatives:** A 10 % non-inferiority framing (v3w and tail pass, sw fails): a new reading defined after the data. Per-vehicle-second rates: they depend on the exposure measure (per vehicle-km, sw is -5.2 [-10.3, +5.5]), so they are not robust.

### D8. After round 2, what is X1's and X2's status for later work, notably RQ4's non-learning opponents on the same plant (V457(2))?

- **Recommendation:** Log this before chapter 6's protocol. X2 is closed to DRL training, tuning, plant change and seed rounds (D10). X1's status follows D1. Frozen-policy evaluations against new non-learning opponents are allowed in both cells as a new question, with their own protocol and fresh seeds, report-only for the DRL claim.
- **Pros:** It unblocks V457(2) without repeating the round-1 drift past a stop rule.
- **Cons:** It is another post-data ruling, and [A3]'s 'seed round' wording has to be interpreted.
- **Alternatives:** Forbid any run in X1 or X2: blocks RQ4 on the plant that the V&V record targets. No ruling: repeats how X1 was re-tested without a decision.

### D9. Does 'fixed before data' stay in the article's title options and claim sentences?

- **Recommendation:** Drop it from the title options (plan.md:30-32). In the claim and abstract, write 'under a protocol fixed before round 2's evaluation data (exceptions disclosed: V459 bar, V460, V462/V463, V466, V467, X1's history)'.
- **Pros:** It stays true after V466 and V467.
- **Cons:** The title loses a phrase that signals the method.
- **Alternatives:** Keep it unqualified: partly unsupported. Qualify it in a footnote only: easily missed, and V463 asks for the timing list wherever the phrase appears.

## 4. Filled claim (DRAFT)

**Status.** DRAFT for the author, not approved. This text would replace outline_v1.md:39-55 once decisions D1-D9 are taken. Text in [brackets] depends on a pending decision. Numbers come from docs/research/results/round_2_result.md (HEAD e5543fa) or from docs/research/round2/report/. A † marks a number that at least two independent review scripts reproduced but that the report does not yet hold; it must go into the report through report2.py before any use.

### Thesis claim

On a synthetic freeway plant documented in a draft V&V record (not yet reviewed) for comparing controllers that set ALKS time headways (r2m3, plant_c3), within its limits L1-L27, and under round 2's protocol, fixed before its evaluation data with the exceptions listed below:
- these per-CAV PPO policies (v3w, at checkpoints chosen on validation seeds) met round 2's T2 reading against the counting rule controllers in X1;
- they did not meet it in X2, where the DRL claim against tuned rules closes;
- against no control, the thesis bar (V459) is not met in X1 and is met in X2.

A two-cell decision map with report-only band and history panels is reported in full. The opponents were rule controllers only; no MPC or non-learning adaptive scheduler was among them (V457(2)).

**Model:** an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds.

**Exceptions to "fixed before data", all disclosed:**
- The V459 no-control bar was set after confirmatory 3, 3b and round 1 were known, and its review ran after round 2's data (V459).
- The script that computes the bar was added after the protocol's approval and ran outside the frozen chain (V460).
- The claim wording, including the 3E-T bracket used in X1, and the tile rule were fixed after round-2 validation rows existed and before any test row (V462, V463).
- D10's closing was read by T2 alone. This was decided after the test data (V466).
- Every reading that feeds a sentence is read at T2's 99.17 %. This was decided after the test data, against the more favourable 97.5 % (V467).
- X1 had been closed by confirmatory 3's [A3] before rounds 1 and 2 re-tested it (V395, V420, V423; disclosed in round_2.md, V453, V454) [; V#### records that round 2's X1 test stands as the claim basis].

### X1 against tuned rules: W

Under two tapered slowdowns to 25 km/h for 120 s on edge 4, at 600 and 1,200 s (X1), 5 of 5 per-CAV PPO headway policies (v3w) had 16.3-24.2 % fewer seconds at TTC below 3 s than every counting rule. These are point estimates over the 5 policies against the counting rule with the lowest close-following, 3E-T. Every 99.17 % CI is above 0, with the lowest lower bound at 9.1 %†; at arm level the margin is 20.3 % [15.2, 23.6] at 99.17 %†.

The counting rules were:
- p333, which is fixed;
- os0_10_10, tuned on separate seeds;
- 3E-T, a rule tuned by CMA-ES under the training slowdowns, not for this cell. Its tuning condition lies outside the plant's stated intended use.

Delay, flow and the other side measures stayed within the pre-registered limits. The worst end of T2's delay CI was above -5 % against every counting opponent (report-only, D11). It tied or lost elsewhere: [map]. This is a surrogate.

Carried with it:
- **3E-T's search** ran 40 of 100 pre-registered generations, with convergence unchecked. Its 5 shortlisted configurations all came from 2 of 5 seed windows, so it is a lower bound on its family.
- **The CMA-ES-tuned rule 3E-X1 did not meet the delay filter in X1.** It had 2.3 % more delay than p333 (95 % CI from 0.5 % less to 5.7 % more) and 27.4 % fewer close-following seconds (95 % CI 25.0 to 33.9 %).
  - Against it, Q1 and Q2 read "not answered against the CMA-ES rule: not within the delay filter".
  - 3E-X1 is a rule tuned by CMA-ES for this cell on separate seeds. Its search was still falling at generation 40, and its pick is from generation 3.
  - Its shortlisted points with lower loss had 2.44, 2.64 and 2.38 % more delay than p333 on the tuning seeds, so they failed the 2 % cap.
  - So the X1 margin is measured against the rules that the 2 % delay filter admitted. It does not show the best close-following a tuned rule can reach.
- **Where the gain is** (v3w against 3E-T; median paired differences in TTC samples per run, 95 %; medians do not add up):
  - total: 457 [354, 516];
  - roads: edge 3 253 [206, 273], ramp 2 107 [77, 172], edge 4a 80 [40, 149];
  - follower speed: 10 m/s or more 205 [177, 218], 5-10 m/s 196 [163, 234], below 5 m/s 48 [13, 105].
  - Ramp 2 and 4a form merge 2, where lane-end behaviour is not validated (L24; PR-28 open).
- **History:** this is X1's third test on plant_c3, each on fresh seeds.
  - Confirmatory 3 closed X1 by its rule [A3] (V395).
  - Round 1 re-tested it without stating that closure (cells picked in V420, approved in V423), and won T2 against the old grid (V449).
  - Round 2's protocol disclosed the closure before its data (V453, V454).
  - No correction covers the repeated tests, and the cells were chosen where DRL already looked best.
- **Estimator:** under a ratio of medians or of means, 3E-T would not count in X1 and 3E-X1 would. The protocol fixes the median of paired differences, so this changes no reading.
- **Teaching to the test:** the judged 1-Hz flag (TTC below 3 s) and braking at 3 m/s² are reward terms. For pairs that include an ALKS, the TTC-below-2-s, TTC-below-1.5-s and severe (DRAC) counters lie almost entirely inside the rewarded event. Against 3E-T they agree in direction (v3w +39.7, +25.4 and +28.0 %). They are reported counters, not readings.
- **Beside, under their own names:** these are descriptive. tail and sw are built from v3w's checkpoints, so they are not independent confirmations.
  - The averaged action probabilities of 6 checkpoints of each PPO run (tail): 5 of 5, 15.7-24.9 %.
  - A hybrid: 0.8 s and os1_15_10 before 594.72 m, the PPO policy after (sw): 5 of 5, 14.7-25.2 %.
- [**"Safety"** is not used for X1 (D5), although the severe check is met.]

### X2 against tuned rules: N

Under one tapered slowdown to 30 km/h for 180 s on edge 3, between the merges, at 700 s (X2), two CMA-ES rules counted:
- 3E-T, a rule tuned by CMA-ES under the training slowdowns, not for this cell;
- 3E-X2, a rule tuned by CMA-ES for this cell on separate seeds. Its search was still falling at generation 40, so it is a lower bound on its family.

Against them, these per-CAV PPO policies (v3w) did not clear T2: 2 of 5 met it, against the 4 required. The limits missed were the 10 % close-following margin and its CI. Under D10, read by T2 alone (V466, decided after the test data), the DRL claim against tuned rules closes in X2 on this plant.

Carried with it:
- **Direction:** by point estimate, every policy arm has fewer close-following seconds and less delay than both rules.
  - At T2's 99.17 %, v3w against 3E-X2: TTC +12.3 [+2.5, +19.8]; delay +3.0 [-0.1, +6.4], not shown to differ.
  - v3w against 3E-T: TTC +11.5 [+5.1, +18.4]; delay +7.5 [+5.0, +10.0].
  - Per policy against 3E-X2: 7.5-14.1 %.
  - T2 decides on single policies (4 of 5 with the margin and its CI), not on the arm.
- **The closing hinges on 3E-T.**
  - 3E-T counts at -1.81 %, 0.19 points inside the delay filter, after it was excluded at validation (-3.4 [-5.3, -1.6]). Leaving out any one seed moves it only between -1.86 and -1.76.
  - Under a ratio of medians or of means, 3E-T would not count, and tail would pass 4 of 5.
  - Against 3E-X2, tail fails with one policy only (t0). Its policy t4 fails only against 3E-T (margin 8.4).
  - In a seed bootstrap that re-decides counting, some arm wins X2 in about 16-20 % of resamples† (post hoc, report-only).
- **Beside, under their own names:** tail 3 of 5 (margin and CI); sw 0 of 5 (margin, CI and the 20-s per-run limit).
- **Comparison with round 1** (no sentence rests on it): against confirmatory 3's grid alone, every arm passes 5 of 5 in round 2. Round 1 won X2 (v3w, 5 of 5, against p333 and os1_15_10, seeds 7,440,500-539, 97.5 %). Under D10, this round's T2 replaces it.
- **Replication:** the edge over the fixed 0.8 s rule held. In every arm, 5 of 5 policies were at least 30 % better than p333, at 99.17 %.
- **No delay-win sentence:** tail's X2 delay win is 3 of 5 at 99.17 % (V467). The severe check is not met, so "safety" is not used in X2.
- **What the closing means:** no further DRL training, tuning, plant change or seed round in X2 on this plant. It is a pre-registered stop, not evidence that the policies are no better than the rules.

### Against no control (V459)

This is a report-only thesis reading ("thesis reading, V459, not a round-2 verdict"). Its bar was set after confirmatory 3 and round 1 were known.
- It is read on the arm, the per-seed mean over 5 policies.
- The arm meets the bar if its delay is at least 10 % lower with the 99.17 % CI excluding 0, and its close-following is not harmed.
- Harm means more than 10 % worse by point, with the 95 % upper bound below 0. This is round 2's harm rule, which V467 does not change.
- The count of single policies meeting the bar is given beside.
- Every rule also meets the delay half (13-24 % less delay) and is harmed on close-following in both cells. So the bar separates controllers only on close-following.

**X1, not met.**
- v3w had 27.3 % less delay (99.17 % CI 24.4 to 31.1) but 16.6 % more close-following seconds (95 % CI 8.4 to 25.1 % more). That is harm under round 2's harm rule. 1 of 5 single policies met the bar.
- tail: 27.9 % less delay [24.8, 32.2] and 15.3 % more close-following [6.7, 27.1]; 0 of 5 policies met the bar.
- sw: 27.9 % less delay [24.0, 30.8] and 18.4 % more close-following [7.1, 27.4]; 0 of 5.
- Served flow was 5.1 % higher for v3w [4.9, 5.4].
- No control had 1,493 seconds at TTC below 3 s, 322,813 vehicle-seconds of delay and 3,177 vehicle-seconds of braking at 3 m/s² per run.
- For tail and sw, no control had fewer such seconds, at 42.0 % and 37.7 % more delay (4 of 5 policies clearly worse at 99.17 %). For v3w that clause does not trigger (3 of 5), so the arm-level harm above stands instead.
- The policies also braked at 3 m/s² more than no control did (v3w 3,651 against 3,177 vehicle-seconds per run).
- A W against the rules beside "not met" against no control is a trade-off, not a net win.

**X2, met.**
- v3w had 23.5 % less delay (99.17 % CI 20.9 to 26.7), and its close-following was not shown to be harmed (0.9 % more; 95 % CI from 5.8 % more to 9.5 % fewer). 5 of 5 single policies met the bar.
- tail: 23.5 % less delay [20.4, 26.5] and 1.4 % fewer close-following seconds (95 % CI from 4.4 % more to 8.7 % fewer); 5 of 5.
- sw: 23.1 % less delay [19.3, 27.5] and 6.7 % more close-following (95 % CI from 12.1 % more to 2.6 % fewer); 5 of 5. Harm beyond the 10 % margin is not excluded for sw.
- Served flow was 4.3 % higher for v3w [4.0, 5.0].
- No control had 1,580 seconds at TTC below 3 s, 287,340 vehicle-seconds of delay and 3,262 vehicle-seconds of braking at 3 m/s² per run.
- No policy is clearly worse than no control on close-following.
- Every rule had 12-70 % more close-following than no control (95 % CIs below 0), so no rule meets the bar.

**Both cells:**
- Collisions are too rare to compare: 4 single events over all test arms.
- No map cells were run in this round, so cells other than X1 and X2 at 5,300 are not shown to be unharmed.

### What this cannot show

**Confirmatory 3, verbatim** (confirmatory_3.md:180): "It says nothing about other actions, other networks, other spacings or real traffic. 4 of 5 is a statement about these trained policies, not the method in general. A rule outside these families could still match DRL. TTC below 3 s is a surrogate, and this model is not calibrated, so a win is not a safety result for real traffic. Only 2 conditions decide the claim."

**Round 2, verbatim** (round_2.md:343-345): "Any win holds for this uncalibrated SUMO model, these slowdowns, these demand levels and ideal V2V." "A null on 7 candidates in one round does not show that no other change would help." "Without D4, beating 3E-T does not show that a rule tuned per cell would be beaten. With D4, it shows this for one 40-generation search per cell. If that search has not converged, 3E-X is a lower bound on a per-cell tuned rule."

**Filled for this outcome** (this must follow the D4 item directly): D4 ran. In X1, 3E-X1 did not meet the delay filter, so the X1 result shows nothing about a CMA-ES rule tuned for X1. In X2, the policies did not clear 3E-X2. Neither 3E-X search had converged by its own check, so each 3E-X is a lower bound on a per-cell tuned rule. 3E-T ran 40 of 100 pre-registered generations, with convergence unchecked.

**Also:**
- The cells were chosen where DRL already looked best, and were tested repeatedly across rounds (X1 three times and X2 four times on plant_c3), with no correction across rounds.
- v3w, tail and sw come from v3w's training runs, so they are one line of evidence. The 5 learners sample training noise only, and that noise lies outside every CI.
- The counting filter depends on the estimator, in both cells.
- The deciding flag is a reward term, and close-following is read at 1 Hz. The 0.1-s meter E1 has not run (L19).
- X2's closing is a stop rule. It does not show that the policies are no better than the rules.

## 5. Required disclosures

- X1 history: closed by confirmatory 3's [A3] (V395). Re-tested in round 1: the author picked the cells in V420 and approved them in V423, neither of which addresses [A3]. Disclosed before round 2's data (round_2.md:312-316, V453, V454). This is X1's third test on plant_c3, with no correction across rounds.
- The 3E-T bracket in outcome W was added at 18:16 (V462, V463). Validation rows existed then, but no 3E or v3w row yet: those rows are in val/rows_6c49e7e.jsonl, made 19:36-20:14.
- 3E-X1 did not meet the delay filter (-2.3 % [-5.7, +0.5] vs p333), so X1 says nothing about a rule tuned for X1. Its lower-loss shortlist points had 2.44, 2.64 and 2.38 % more delay than p333 on tuning seeds (plan.md:431).
- 3E search limits. 3E-T: 40 of 100 generations, convergence unchecked, shortlist from 2 of 5 windows, tuned under condition T, which is outside the intended use. 3E-X1 and 3E-X2: still falling at generation 40, so each is a lower bound.
- X2's closing depends on 3E-T counting at -1.81 %, 0.19 points inside the filter; it was excluded at validation (-3.4). Under either ratio estimator tail passes 4 of 5. Against 3E-X2 alone tail passes 4 of 5. Post hoc seed bootstrap: some arm wins X2 in about 16-20 % of resamples.
- X1's counting set depends on the estimator: 3E-T out and 3E-X1 in under either ratio estimator (report:446). The protocol fixes the median of paired differences.
- V466, D10 read by T2 alone, was decided after the test data. The frozen run commit already applied T2 only (6c49e7e test2.py:84-87).
- V467, all sentence-feeding readings at 99.17 %, was decided after the test data, against the more favourable 97.5 %. It removes tail's X2 delay-win sentence. The 97.5 % values are reported beside.
- V459 bar: set after confirmatory 3, 3b and round 1 showed the same X2/X1 pattern; reviewed after round 2's data; computed by a script added after approval and run outside the frozen chain (V460).
- The delay half of the V459 bar did not fail for any controller: every rule has 13-24 % less delay than no control, and V419 shows the same across the sweep. The bar discriminates only on close-following, and no null exists for it.
- 'Met' in X2 means harm was not shown (arm 95 % CIs: v3w [-5.8, +9.5], tail [-4.4, +8.7], sw [-12.1, +2.6]). sw's CI reaches beyond the 10 % harm margin. Rough power to detect a true 10 % harm is about 31-47 %.
- In X1 the policies are worse than no control on every TTC threshold (TTC<3 s 15-18 %, <2 s and <1.5 s 25-29 %) and on step braking at 3 m/s² (v3w 3,651 vs 3,177 veh-s per run).
- Teaching to the test: the judged 1-Hz TTC<3 s flag and braking at 3 m/s² are reward terms (b_env.py@e97a4f6:798-843). For ALKS-involved pairs the TTC<2 s, TTC<1.5 s and DRAC counters are almost entirely inside the rewarded event. The report's label 'counters outside the reward' (report:319, round_2.md:338) is wrong.
- About half of X1's gain is on ramp 2 and edge 4a: report medians 107 and 80 of 457; 45-53 % on paired means. Lane-end behaviour there is not validated (L24, PR-28). The V&V record is a draft, and PR-15 and PR-24 are also open.
- The opponents are rule controllers only. No MPC with a fitted model and no non-learning adaptive scheduler was run (V457(2)); CLAUDE.md requires disclosing that the MPC was dropped.
- The cells were chosen where DRL already looked best (confirmatory_3.md:168). v3w, tail and sw are one line of evidence, not three. Bonferroni corrects within round 2 only.
- Platform deviations (V465): validation ran on two machines, so 2B, 1B, 1D and ahead were judged on laptop rows against remote v3w rows; checks 2 and 4 were not run on the rented machine; the remote stand-in and the job log were not kept.
- v3w's checkpoints were chosen between u250 and u500 on validation seeds, not final policies only. The 5 learners sample training noise only, outside every CI.
- The 2 % delay limit is a point rule that passes a policy truly 2 % worse about half the time (V435). The 5 % non-inferiority bound is reported beside it (worst end above -5 % everywhere).
- Round 1's X2 win (v3w 5/5 against p333 and os1_15_10, 97.5 %) is reported beside the X2 result. Under D10 it supports no sentence. The grid-only T2 of round 2 is a comparison with round 1 only (round_2.md:243).
- Check 7 was a lean review, not the adversarial review the protocol names (V455). Round 2's approval was read from 'Go on' (V454).

## 6. Fixes that follow

### Outline §3

- outline_v1.md:5: replace 'fixed **before round 2's data**' with 'fixed before any round-2 test row (V463); D10's closing reading (V466) and the sentence CI level (V467) were decided after the test data'.
- outline_v1.md:39: replace 'documented in a V&V record' with 'documented in a draft V&V record (not yet reviewed)' and 'L1-Ln' with 'L1-L27 (count from the record version current at submission)'. Follow 'under a protocol fixed before data' with the exception list (V459 bar, V460, V462/V463, V466, V467, X1's [A3] history).
- outline_v1.md:39, continued: make the subject 'these per-CAV PPO policies (v3w, at checkpoints chosen on validation seeds)', replace 'against the rule controllers' with 'against the counting rule controllers (no MPC or adaptive scheduler among them)', and replace '[outcome below] against no control' with '[met | not met], one clause per cell, against no control'.
- outline_v1.md:41: change the carry list to 'confirmatory 3's model sentence and "What this cannot show", and round 2's, verbatim, with round_2.md:345's D4 item followed directly by its per-cell fill (whether 3E-X counted, whether it was cleared, convergence); plus round 2's Disclosures that bear on the cell: history, 3E search limits, counting knife-edge and estimator dependence, V466/V467 timing, teaching to the test'.
- outline_v1.md:47 (W): define [x] as 'the per-policy point range against the strongest counting rule, each 99.17 % CI above 0 with the lowest lower bound, arm-level CI beside' (D4). Add the required companions: round_2.md:244's sentence when 3E-X did not count, the cell's history, the 3E search limits and L24. Subject v3w only; tail and sw go in separate clauses under round_2.md:249-250's names.
- outline_v1.md:48-49 (G, N): add 'N takes precedence over G whenever D10 closes the cell; G's limits missed go inside N; the grid-only result is reported as "comparison with round 1; no sentence rests on it" (round_2.md:243)'. Reword N to 'these per-CAV PPO policies (v3w) did not clear T2 against the strongest counting rules ([k] of 5, 4 required; limits missed [..]); by point estimate [direction]'. Name finalists separately, never in '(v3w[, finalists])'.
- outline_v1.md:51 (V459): state the reading as 'arm (per-seed mean over 5 policies, V460), delay CI at T2's level, harm at 95 % (round_2.md:197, unchanged by V467), single-policy count beside'. Sentence forms: 'met (close-following not shown to be harmed: [CI])' and 'not met (close-following harmed: [CI])'. Add served flow beside, and 'every rule meets the delay half, so the bar separates controllers only on close-following'.
- outline_v1.md:51, continued: the confirmatory-3 no-control clause is read at T2's level (V467). Where it does not trigger, the arm-level harm is stated instead (v3w in X1).
- outline_v1.md:53 (tiles): add 'beside an N cell: tiles are arm-level, 95 % and uncorrected, and decide nothing; T2 needs 4 of 5 single policies at T2's level'.
- outline_v1.md:55 (never says): add 'not harmed' without a CI; 'beats no control'; 'beats tuned rules' as shorthand; 'counters outside the reward' for TTC<2 s, TTC<1.5 s, DRAC or braking; 'reopened' for X1; [and 'safety' for X1 (D5)].
- outline_v1.md:31 (RQ3 evidence) and :65 (ch 5 status): after the author approves, fill in 'round 2: X1 W (3E-T bracket; not answered against 3E-X1), X2 N (closed, D10/V466); V459 not met in X1, met in X2'.
- outline_v1.md:32 (RQ4) and :66 (ch 6): record X1's and X2's status for later work once decision D8 is logged.

### Article 1 and the round-2 report

- plan.md:30-32: drop 'fixed before data' from the title options, or qualify it as 'with disclosed exceptions' (D9).
- plan.md:52 and :63 (C2): add 'the D10 closing reading (V466) and the CI level of sentence readings (V467) were decided after the test data' to 'fixed before round 2's evaluation data' and to 'sentences fixed before data'.
- plan.md:81 (W abstract): make the subject v3w only and name tail and sw in their own clauses. Add a slot for round_2.md:244's 3E-X non-counting sentence, the per-cell D4 fill, the X1 history and the corrected teaching-to-the-test label. Change 'not harmed' to 'not shown to be harmed [CI]'; add served flow beside no control; write 'draft V&V record'; give the band 'report-only, no verdict'; apply D5 on 'safety'.
- plan.md:83 (fill note): set the [x] form per D4. State that the delay half and the beside readings are at T2's level and harm is at 95 %.
- plan.md:89 (G abstract): add 'not used where D10 closes the cell (outline precedence)'.
- plan.md:95 (N abstract): replace 'did not beat' with 'did not clear T2 against'. Name finalists separately, and add the arm-level direction, the 3E-T knife-edge, the estimator dependence and the D4 fill.
- plan.md:403-406 (6.1): report the margin and the blocks against each counting 3E rule, not only the strongest; tail's X2 failure is t0 on both rules and t4 on 3E-T only (report:191).
- plan.md:413-414 (6.2): put the rules and a flow column beside the V459 rows. Fix the provenance: the r2-move poller wrote thesis_v459.json (move2r.sh:80-82) from thesis2.py at 68f405a, with imported modules identical to 6c49e7e; it was not a manual run.
- plan.md:437 (6.4): per D4, quote road medians with CIs and L24; any share only as a post-hoc ratio of sums.
- plan.md:468 (6.8): fill in round 2: X1 v3w/tail/sw 5/5/5 (3E-T counting, 3E-X1 excluded); X2 2/3/0, closed under D10.
- plan.md:479 (7.1): after the verbatim D4 sentence, add the per-cell fill: 3E-X1 did not count; 3E-X2 not cleared; neither 3E-X converged; 3E-T 40 of 100 generations.
- plan.md:503 and :641: replace 'X1 was reopened after [A3]' with 'X1 was re-tested after [A3] closed it (cells chosen in V420, approved in V423, without addressing [A3]); disclosed before round 2's data (V453, V454) [; D1 entry]'.
- plan.md:498-506 (7.4): add that X1's TTC comparison survives any plausible correction (0 of 20,000 bootstrap medians at or below 0); that v3w, tail and sw are one line of evidence; and the post-hoc X2 seed-bootstrap reversal of about 16-20 %.
- plan.md:508 and :642: relabel the counters. Braking at 3 m/s² is a reward term, and TTC<2 s, TTC<1.5 s and DRAC are nearly subsets of the rewarded TTC<3 s event for ALKS pairs; only pairs of human drivers and the 0.1-s resolution are unrewarded.
- plan.md:639 (objection 6): add the X1 frontier point (D6) and an explicit statement that no MPC or adaptive scheduler was run.
- s4_the_reading.tex:65-67: qualify 'fixed before data': D10's closing reading (V466) and the sentence CI level (V467) were decided after the test data.
- s4_the_reading.tex:69-78: add bullets for V466 ('read by T2 alone, decided after the test data; the frozen code already applied T2 only'), V467, X1's [A3] history and the V465 platform deviations.
- s4_the_reading.tex:129-131: replace 'A policy set passes' with 'The policy arm (per-seed mean over 5 policies) passes; delay CI at T2's level, harm at 95 %; the number of single policies meeting it is reported beside'. Use 'not shown to be harmed', and read the clause at T2's level.
- s4_the_reading.tex:133-137: add 'D10's closing is read by T2 alone (V466)' and the G/N precedence chosen in D2.
- round_2_result.md (feeds the article tables, V457), part 1: add X1's 99.17 % CIs against 3E-T, per policy and arm, through report2.py. Relabel line 319. Add rule rows and a flow column to the §6 table. Change line 16 to 'at T2's level, fixed after the data by V467'. Give 3E-X2's delay CI at line 431 (+1.5 [-0.1, +3.9]).
- round_2_result.md, part 2: quote §7.7 verbatim. Add to §8 'except round 2's harm rule, fixed at 95 %'. Note that w3's 95 % upper bound against no control is exactly 0.00 (a tie). Make table scripts read the beside readings at T2's level: test_result.json still stores 97.5 %, e.g. tail's X2 delay_won=true.

## 7. Checks

How the numbers were checked:
- Five reviewers recomputed the round-2 numbers from /home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl (2,800 rows, 70 arms x 40 seeds 7,440,840-879, no duplicates).
- Five adversarial verifiers then re-derived them with their own loaders, statistic and T2/V459 logic. No reviewer check was marked match=false, and every verifier reproduced its reviewer's checks.

Matched by at least two independent codes:
- **T2 counts:** X1 5/5/5 (baseline-v3 4), X2 2/3/0 (baseline-v3 2). Blocking reasons and margins are identical to test_result.json.
- **Counting filter:** X1 3E-T -0.94, 3E-X1 -2.31, os0_10_10 -1.43. X2 3E-T -1.81 (leave-one-out -1.86 to -1.76, 0 flips), 3E-X2 +1.48. Alternative estimators: X2 3E-T -2.02/-3.18; X1 3E-T -3.18/-2.02, 3E-X1 +1.59/-1.67. tail passes 4/5 in X2 without 3E-T.
- **Margins:** per-policy X1 vs 3E-T 16.3-24.2 / 15.7-24.9 / 14.7-25.2 %. X2 vs 3E-X2 and vs 3E-T match report:197-199.
- **X2 arm CIs at 99.17 %:** match report:206-207, e.g. v3w vs 3E-X2 +12.3 [+2.5, +19.8].
- **V459 rows:** all 8 arm rows and the 28 rule rows match thesis_v459.json, to 1.07e-14 in one code. Policies met: X1 1/0/0/0, X2 5/5/5/4. No flip over 20-50 other bootstrap seeds.
- **No-control clause:** X1 v3w 4/3/3, tail and sw 5/5/4 at 95/97.5/99.17 %; no control's extra delay 38.7/42.0/37.7 %.
- **Other values:** no-control medians (1,493 / 322,813 / 3,177; 1,580 / 287,340 / 3,262); collisions 4; non-inferiority minimum -3.96 (sw s4 vs 3E-X2, X2); where-the-gain medians; the teaching-to-the-test table; the 3E-X1 sentence values; the 3E-X convergence medians; the 3E-X1 shortlist delays 2.44/2.64/2.38 %.
- **Code and timing:** D10 flags; T2-only closing in frozen 6c49e7e test2.py:84-87 (11:33:05); V459 commit 15:18:23 and thesis2.py 68f405a at 15:19:51; 3E-T bracket at 18:16:30, before any 3E or v3w validation row.
- **Files:** sha256 of the report copies equals the run-directory files.

New values computed in the review and not yet in the report, each reproduced by at least two codes:
- X1 v3w vs 3E-T at 99.17 %: per-policy lower bounds 9.1-19.1 %, arm +20.3 [15.2, 23.6].
- X1 worst delay lower bounds: v3w -2.58, tail -2.51, sw -2.48.
- X1 v3w step braking vs no control: -13.2 [-15.6, -9.6].
- X1 survives Bonferroni at m > 500; X1 is won in 99-100 % of seed resamples.

Mismatches or corrections:
- A draft attached -4.0 to X1; that value belongs to X2.
- The X2 seed-bootstrap reversal came out 19.7 % in one code and 16.1 % in the other.
- The 4a-plus-ramp-2 share spans 40.8-48.2 % for v3w depending on the estimator.
- The per-vehicle-second sensitivity does not survive a per-vehicle-km denominator.
- Rough harm-power estimates differ slightly between codes (31-47 % against 34-45 % for a true 10 % harm).
- Several reviewers cited round_2_result.md at 9dc94cf, so their line numbers from about line 212 onward are 5 short of HEAD e5543fa.

What I checked myself, read-only:
- I recomputed no new statistic.
- I checked against the sources: V420 (decisions.md:440); b_env.py@e97a4f6:798-843 (the reward charges 1-Hz TTC<3 s and braking at 3 m/s² for the ALKS and 0.5 x its follower's); round_2.md:197, :243-249, :261, :315, :338, :343-345; confirmatory_3.md:126, :132, :168, :180.
- From the stored test_table.csv: v3w flow vs no control X1 +5.1 [4.9, 5.4] and X2 +4.3 [4.0, 5.0].

Repository state: git status still shows only the pre-existing modified .gitignore (already in the session's starting snapshot) and the two untracked folders. Nothing in the repository or the run directory was written.

## 8. Refuted or dropped

- recompute R-NC-LEVEL: refuted. The 'open' CI level was decided by V467 (decisions.md:487, committed 22:32:38); the report applies it at :267-271.
- mapping F5 and F8, and examiner F11: the parts calling the CI level 'open' are stale for the same reason (V467). The remaining content is folded into the disclosures.
- mapping F1 detail 'the re-test was never decided': wrong. The author picked X1 and X2 at 5,300 in V420 (decisions.md:440) and approved round 1 in V423; that decision ignored [A3]. Also, plan.md:465 says 'closed by [A3]'; only :503 and :641 say 'reopened'.
- mapping F1, F2 and F3 severities: blocker to major, blocker to major, and major to minor. The 3E-T bracket's companions are already required (V463, outline:41, :53).
- wording B1, B2, B3 and examiner F1: blocker to major, because no thesis or article sentence is filled yet. B2's claim that W lacks 3E-T's 'not for this cell' is refuted (outline:47, plan.md:81), and plan.md:52 is not a claim sentence.
- wording M2's claim that report:439 invites a 'live claim' reading: refuted; the same bullet carries the [A3] closure.
- wording M3, M5, M6 and M8: downgraded to minor and folded. M6's draft phrase 'outside the reward' would itself be wrong, per the corrected examiner F4.
- wording DRAFT 2 and m9 'worst 99.17 % delay bound -4.0 %' in X1: misattributed. -4.0 (-3.96) is sw s4 against 3E-X2 in X2; X1's worst lower bounds are v3w -2.58, tail -2.51 and sw -2.48.
- wording m2 (report §7.2 does not name arms or counts): dropped as low value; report:7 and :444-446 already give them.
- wording m7, second half (do not reuse V457's phrase): already covered by V462(3) and outline:55.
- examiner F4's proposed relabel 'only DRAC and step braking lie outside the reward': wrong. Braking at 3 m/s² is charged at 1 Hz (b_env.py@e97a4f6:798-843), and DRAC >= 3 m/s² implies TTC < 3 s when the closing speed is under 18 m/s (sev3 <= 0.101 x ttc3 in all 2,800 rows).
- examiner F6 'some arm wins X2 in about 20 % of resamples': corrected to about 16-20 %. The verifier's independent bootstrap gives 16.1 %, about 2 Monte Carlo SE from 19.7 %.
- examiner F7 'per unit of exposure sw is clearly worse than no control': not robust. Per vehicle-km it is -5.2 [-10.3, +5.5]; the per-vehicle-second rate is inflated by the lower delay. 'The delay half cannot fail' is overstated: it did not fail for any controller.
- examiner F9 'about 40 % of X1's gain at ramp 2 and 4a': the paired-means share is 45-53 %; 40.8 % comes from medians that do not add.
- examiner F8, F10, F11 and F12: kept as minor only (multiplicity wording, no-MPC disclosure, post-hoc sensitivities, 3E-T outside the intended use).
- code CV-1 'a corrected harm level goes against V467's own aim': over-read. V467's premise covers levels the protocol does not fix, and round_2.md:197 fixes harm at 95 %. Kept as minor (decision D3).
- code CV-3 'noise-free planted rows': the planted rows carry narrow noise. The finding stands: the test pins the sign, not the CI side or level.
- code CV-5 'never decided by the author': V467 now covers the delay half's level; only the arm-versus-policies choice remains (decision D3).
- recompute R-WHERE-SHARE 'about 2 points' spread: about 7 points for v3w (40.8-48.2 %). The finding stays minor (decision D4).
- mapping F7, F8, F9, F10, F11, F12; code CV-3, CV-4, CV-6; recompute R-W3-TIE, R-POSTHOC; wording m1, m3-m8, m10: confirmed or partly confirmed as minor. They appear only as fixes, not in blockers_and_majors.
