# skeptic_classify

**Basis.** Every V-number cited singly was read in full, with the plant JSON files, stored row settings and policy configs. No simulation ran.

**EXPL** = my exploratory number from rows already read for a verdict: paired seeds, median paired difference over the reference median, 95 % percentile bootstrap, 10,000 resamples, RNG 20261110. Positive = the policy has less delay. Scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit2/sk/`.

## Verification, 24 rows

- **Confirmed, plant, inputs, seeds and open defects (19):** V298, V304, V307, V317 (m32); V333, V337, V339, V344, V347, V351 (r1m3 P0); V355, V359, V368 (r2m3 with P0); V382, V395, V401, V409, V410, V496 (plant_c3).
  - Rows of phases 1-3 carry `lcAssertive` and `smooth` only. Confirmatory 3, 3b, the V409 and V410 files, round 2's test and S6 carry every plant_c3 flag and `all_delay`.
  - Baseline-v3 and v3w configs: plant_c3 flags, "running mean and SD".
  - CLK holds: policies `hold` 10.0, p333 none, default 30.0 (b_env.py:642; V351).
  - N1 holds (MSLaneChanger.cpp:864-865; MSCFModel_IDM.cpp:218-220).
- **Not verifiable from the row (5):** V411's plant; V475's seeds; the plant of V419, V429 and V449 (late tally not repeated).
- **No plant or input entry was found wrong.** The errors are verdicts (findings 1-7) and timeline line 7 (finding 8).

## Findings

**1. Major. V347 is not reversed on plant_c3** (classify_early:40, :53).
- X1, 120 seeds: no stored rule is below p333 by point; 11 of 13 are shown worse; lr1000_10_1 reads −1.3 [−2.4, −0.6] (an_x1x2_delay_edge.md:44, EXPL).
- Correction: V347 carries over in direction for rules. The cost shrank (−4.5 to −1.3). Only v3w is below p333. Memo M2 should say "v3w", not "arms that lengthen".

**2. Major. V395 and V401 are not superseded** (classify_late:26-27).
- Same plant, inputs and metric as v3w. Only the recipe differs (levels 4,500-6,000, checkpoints chosen on validation).
- EXPL, baseline-v3 against p333. X1, seeds 7,440,200-219: five points, −3.1 to −0.1; d3 −3.1 [−7.1, −0.5]; single learners −2.3 [−4.4, +2.7]. X2, 40 seeds: +0.4 [−1.0, +1.6].
- Correction: "carries over for baseline-v3; recipe-dependent".
- Both ways. Retraining moved delay by 3.5 % [1.2, 5.3] (V449), which weakens L1's "likely to fail". The X1 edge belongs to one selected recipe, a forking-path risk for screen R.

**3. Major. "The X1 edge predates plant_c3" is not supported** (classify_early:54).
- EXPL, the shot's 7 learners, r2m3 with P0, seeds 7,440,140-159, X1, against p333: points −1.4 to +4.5; 0 of 7 intervals above 0. My r4a1 value equals V368's record (−9.5 [−11.6, −5.1]).
- Correction: "7 of 10 P0 policies have a positive point; not shown".

**4. Major. PR-28 is applied to the X1 edge, not to the TRUCK tie** (classify_late:40, :46).
- The tie nets a lower road 4a (−4.38 % [−7.57, −1.29]) against a higher road 3 (+1.31 % [+0.73, +1.93]) (metric_audit.md:95, EXPL, not recomputed).
- The verification record ties PR-28 to "Any win against tuned rules" only (plant_vv_record_v0.md:87).
- Correction: V496 gets the X1 edge's label, "as measured; its sign depends on PR-28". If merge-2 lane ends are an artefact, the tie hides a loss. If sound, both stand.

**5. Minor. V337 and V359 cite V395's map as a delay re-test** (classify_early:36, :45). V395 read it for harm only.
- EXPL, baseline-v3 against p333; S, H1, H2 at 4,600 and 5,300; X1, X2 at 4,600: points −3.9 to +3.9. Of 40 intervals 36 include 0, 3 lie below, 1 above; up to 13.6 points wide at S 5,300.
- Correction: "a tie at 20-seed resolution (EXPL)".

**6. Minor. V355 "not in X1, X2"** (classify_early:44). Finding 1's source covers z33133, r4a1 and copy. Correction: carries over in X1; not shown either way in X2.

**7. Minor. S6 cell S "superseded"** (classify_late:41). A null is the project's own standard (V244), but the memo forbids re-reading S6 (memo:88). Correction: "arm-level estimator biased under its null; both readings exploratory".

**8. Missing records.**
- V255(2), V256(1), BN4: "a constant 1,800 veh/h meter ties the DRL"; R6 "beaten by a tuned constant rate". Timeline line 7 ("three plants only") contradicts its own BN4 row. Does not carry; withdrawn.
- The best rule changed with the plant. m32: a333 against p303 on delay +0.39 [−6.31, +6.46] (baseline_v0/headline_paired.csv:2446). P0: against no control, a333 +29.0 and p303 +23.2 (V333; no paired interval). INFERENCE: easier merging (ramp delay 229.8 to 79.9 s, V329) took value from lengthening at the merge. Direction: toward uniform 0.8 s, against any merge-targeted controller, rule or DRL.

**9. Missing defects.**
- N1 is absent from the timeline and the early table. It touches V274-V368 and V419: part of the "headway gain" is SUMO's gap test. Direction: toward short headways against no control, and toward the rules against lengthening.
- Evaluation is greedy; training samples (c_train.py:133, :208; confirmatory_3.md:42) at entropy 0.69-0.74 (memo:305). Direction unknown; not measured.

**10. Re-checks.** Later rows settle only findings 1, 5 and 6.
- Confirmatory 3's forms are headway rules (confirmatory_3.md:26-34). Plan B names headway rules and MPC-F; no speed, lane or meter arm (baseline_v5/BASELINE.md:22-28).
- So V344, V317, V333's ALINEA, V410, V448's variants, V475 and V491 stay open.
- The steady tie never ran on r1m3 after `ease`, where lane-end stops under no control rose from 30.5 to 361 (V371).

**11. Both directions.**
- Looser for DRL: findings 2, 3, 7.
- Stricter for DRL: finding 4.
- Stricter for the rules: findings 1, 6.
- Inherited: BN4's DRL pass was withdrawn for a plant artefact (V256); P0's ties "stand for that plant" (V367).
