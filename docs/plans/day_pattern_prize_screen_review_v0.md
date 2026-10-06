> **ABANDONED (D4.8, 2026-10-06): never run, no seed used. Kept as history.**

# PS-S v0 design review: ranked fix list (2026-10-06; workflow wf_4cf4cd93-f6c; 65 findings, all kept after verification)

Uncommitted companion to `day_pattern_prize_screen_protocol_v0.md`. Fixes are applied before the commit.

**Overall verdict (review synthesis):** **Answer to your question: do you still need Ultracode and Extra High?**
I can't see or change your current settings; this is from the CLAUDE.md phase table.
- **Ultracode:** not needed now. The design review has finished with this synthesis, so you can switch it off for the rewrite.
- **Extra High:** keep it while the text is being rewritten. That work is protocol writing with criteria fixed before data, and items 3, 4 and 6 are subtle numerics.
- **Ultracode back on once:** for a single design review of the rewritten PS-S v1, before the commit.
- **After the commit:** High with ultracode off for the build. High with ultracode on for the checkpoint review before any evaluation run.
- Suggested one-liner: "Next: rewrite PS-S to v1. Suggest Extra High, ultracode off. Switch?"

**Can PS-S v0 be committed after these fixes?**
Not as v0. The 15 blocking items change too much: I*, the KILL statistic, the head model, the anchors, the drop rule, the arm and plant specifications, and the gate bindings. The result is effectively a new version. Commit it as PS-S v1 only when all of the following are done:
1. **Author decisions:** every item marked needs_author is decided in one dated entry (D4.8, item 15). That covers the new gate bindings, the seed uses (7,191,103 and the version reserve), the variant set and m, and the parametrisation, anchor-ratio and branching choices.
2. **Frozen specification:** the arm, plant and VSL specification is frozen, with its hash in the header, before any calibration-day run.
3. **Size checks:** the data-free synthetic checks (items 3 and 4) are committed with their results. Their results replace §14's "≤ 2.5 %" claim and the n_q = 6 floor.
4. **Re-review:** one more design review of v1 finds no new blocking gaps.

The major items are mostly text changes and should go in before the commit too. Where they add compute (items 18, 26, 27 and the head-ratio and merge-priority branches), the author may choose disclosure instead, but must record that choice.

**Does the KILL stay conservative on the screen plant?**
- **As drafted: no.** Five things break it:
  - F1 fails because of the feasibility filter and the I-side tuning parity (items 1 and 2).
  - F2 and the F5 size claim fail because B is re-selected and the above-capacity look uses t_21 at small n_q (items 3 and 4).
  - The above-capacity threshold counts c twice, as c² (item 5).
  - The head switch may never fire, so the plant can record a drop it does not carry (item 6).
  - The drop rule cannot be run without choices made after seeing the data (item 8).
- **After the fixes:** conservative in part, and the KILL record (K6) must label each part:
  - **Formal:** the I-side ordering, for I_plan and I_hero through the unconditional minimum and the grid oracles.
  - **Argued:** the I-side ordering for I_mpc.
  - **Formal for the screen's own arm set:** the ordering of the statistic (min-ratio form in the gate; a fixed-B or per-arm test in the screen).
  - **Approximate:** the false-KILL rate. It holds only to the extent the synthetic size check shows, and only conditional on the realised tuning; the multi-split rule in item 18 mitigates this but does not calibrate it.
  - **Argued, not proved:** B-side set inclusion, tuning parity, the median-form effects, and the transfer to METANET v4 (A1–A10, with the new R-PS bindings).

**Two cautions:**
- The fixes add branches, splits, oracle sweeps and probably a larger n_min. That lowers power and raises compute. §14 and §13 must be redone from measurements, and the author should check whether the screen still delivers D4.2's "early, cheap KILL" before committing.
- This synthesis relies on the reviewers' verification; I did not re-read the sources or run anything. Figures marked unverified (the merge-section anchors of about 1,817 and 1,967, and the stylised size-check rates) must be recomputed by script before use. One point is my own inference, not a verified finding: in item 3, a pre-selected B must be a single arm, not a composite of different arms per fold.

## 1. [blocking] §6 I* definition l.262-264; §2 F1 l.101; §8 l.318; §10 V4 l.361; §11 K0 l.372-373; §12 R-PS4 l.417; gate draft §4 l.118-121 [B4, PS-INT-03]

**Defect.** I* takes the per-unit minimum only over candidates that meet the side constraints, and that filter also applies to I_plan, I_hero and I_mpc. On any unit where a gate-defined arm violates a constraint and has the lowest raw J, F1 (J_I* <= J_X) and V4's 'by construction' are false. The gate never says how it scores a violating I, so it can keep the raw J and get H_gate > H_scr.

**Change.** (a) §6: J_I*,u = min{raw J of I_plan, I_hero, I_mpc and the item-2 oracles; raw J of every B trajectory; J of each extra (LP-OC, ideal-VSL caps, I_mpc_exact if still optional) that meets the side constraints on u}. Add: 'The filter applies to extras only; it is a power choice and cannot affect F1.' Dropping the filter entirely is also valid and strictly more conservative.
(b) l.101: replace 'with the same queue override and side constraints' with 'with the same queue override; gate-defined arms and B trajectories enter the minimum unconditionally'.
(c) l.318: 'feasibility conditions for the I* extras only, never for I_plan, I_hero, I_mpc or B trajectories; tuning penalties for B'.
(d) V4: assert against the raw per-unit J on every evaluation unit of every variant, cell and lambda, during the evaluation runs. A failure is a code bug under item 20, and INVALID until fixed. K0: V4 runs inside the evaluation, not before it. Log the gate arms' per-unit violations, report-only.
(e) R-PS4 (approved via item 15): 'The gate uses the raw J_I on every unit. A violation by I is reported and may only make a GO harder (loss of GO eligibility or a penalty >= 0). It never removes or down-weights units, substitutes another arm's J, or re-selects I per unit.' Mirror this in gate draft §4.

## 2. [blocking; needs author] §2 F1 l.96-101; §6 l.254-260; §12 R-PS3 l.408-412, R-PS4 l.414-417; §13 l.445-449; A11; §10 V4 [B3]

**Defect.** F1 bounds only the screen's own I implementations, which are tuned on 11 days with coarse grids. R-PS3 lets the gate's tod_cnt (and so I_plan) and HERO use richer grids and more tuning days, R-PS4 binds procedures but not fitted values, and the timing rule can drop I_mpc_exact and LP-OC (l.449 wrongly says F1 survives that). So H_gate(P_s) > H_scr(P_s) is possible on the same plant, with no cross-plant step.

**Change.** (1) §6: add I_plan-oracle and I_hero-oracle to I*. Each is the per-unit minimum of J over every point of a pre-registered grid G_I: for I_plan, the tod_cnt mapping parameters fed true demand; for I_hero, the set-point offsets x activation lead. Declare G_I as a superset of any grid the gate may use. These are envelope candidates only; the gate-defined arms stay the lookup-table I_plan and I_hero. Disclose that they only make a KILL harder.
(2) R-PS4: the gate's I_plan and I_hero parameters are constant per day and drawn from G_I (or the oracle covers the same within-day switching structure). I_plan's grid is decoupled from tod_cnt's, or R-PS3 caps tod_cnt's grid at a subset of G_I. The gate's I_mpc uses the screen's fit procedure.
(3) Make I_mpc_exact mandatory: remove it from the §13 timing rule and A11. If it is too slow the result is INVALID (= NO-KILL); it is never dropped. Add argued item A11': on CTM-2C an exact-model MPC is the limit of the fit procedure. LP-OC may stay optional.
(4) F1: formal for I_plan and I_hero via the oracles, argued for I_mpc. Delete or correct l.449. V4 asserts J_I* <= every oracle. §16: add 'I-side tuning parity'. §13: budget the oracle sweeps, labelled as an estimate.

## 3. [blocking; needs author] §9 l.335, l.340; §6 l.266; §2 F2 l.102, F5 l.105-107; K2(a) l.381; K6 l.392; §14 l.483; §12 R-PS9 l.424; §15 l.496; gate draft §4 l.125 [S1, M1, S4, PS-INT-15, PS-INT-10 (R-PS9 part)]

**Defect.** The KILL statistic re-selects B = argmin of the numerator inside every resample, which causes three problems.
(i) The minimum is biased low at near-ties, and percentile, BCa and jackknife UCLs do not correct it. The bias favours a KILL; stylised synthetic checks, not run on the plant, gave false-KILL rates above alpha_v.
(ii) F2 ('H(I*) >= H(I) in every resample') holds only for fixed B. A corrected counterexample gives H(I*) < H(I) under re-selection (the original S4 numbers were arithmetically impossible).
(iii) R-PS9 points at an untracked draft whose §4 does not match the screen and contradicts lesson 19.

**Change.** (a) Define the gate statistic once and restate it in full in R-PS9; it overrides gate draft §4. Record the draft's sha256 or commit the draft.
- H = min over gate B arms of H_X, with H_X = median_s(J_X - J_I)/median_s(J_X), re-selected per resample (conservative for a GO).
- Sequences: 14 Wednesdays (R12). 10,000-resample percentile bootstrap. Two looks.
- GO iff H >= 0.10 and the 97.5 % CI lower limit > 0. The delta_field conditional is kept.
- Correct gate draft l.125 to match lesson 19.
(b) Screen KILL test with no selection on evaluation data. Recommended: KILL a cell-look only if, for one and the same arm X, the robust UCL_X at 1 - alpha_v/5 (Bonferroni over 5 arms) is < 0.10 and every LOO H_X is < 0.10. Alternative with no multiplicity cost: pre-select ONE B arm per cell-look from tuning-fold J only, frozen and logged before evaluation, and bootstrap with B fixed. It must be a single arm, not a per-fold composite: a composite that uses different arms on the two folds can be pointwise below both and break H_gate <= H_B. That last point is my inference, not one of the verified findings.
(c) Rewrite F2: 'For each fixed X, median_s(J_X - J_I*) >= median_s(J_X - J_I) with the same denominator, so H_X(I*) >= H_X(I) >= min_X H_X(I) = H_gate(I): formal for the same arm set.' Delete 'holds in every bootstrap resample'. F5 names the selection step.
(d) The VSL-B-independent and bound-certified labels use the same rule; the re-selected H* is report-only. K6: 'I-side domination and statistic ordering formal on the screen plant for the screen's arm set; B-side set inclusion, tuning parity and transfer to METANET v4 argued (A1-A10).'
(e) Before commit, run a pre-registered, data-free synthetic size check of the final rule:
- n = 22, K = 5, rho in {0, 0.5, 0.8, 0.95, 0.99};
- two cases: all arms tied at the boundary, and one arm at the boundary with the others far away;
- LOO guard included; pass if size <= alpha_v + 2 MC SE.
Commit the script, seed and result, and replace l.483's 'False KILL <= 2.5 %' with the measured value.
(f) Fallback if the author keeps the numerator-argmin form in the gate: the screen KILLs on H_cons = min_X median_s(J_X - J_I*)/min_X median_s(J_X). This still needs (e).

## 4. [blocking] §9 l.338, l.342; K2(c) l.383; A7 l.127; A10 l.31; F5; §14 [S2, S6 (statistics part), PS-14 (t_21 part)]

**Defect.** The above-capacity look may rest on only n_q = 6 qualifying days, but the jackknife-t always uses t_21 (one-sided 98.75 %: t_5 = 3.163 against t_21 = 2.414). Percentile and BCa limits undercover further at small n, and the LOO guard adds nothing. The gate draft names this band as the hypothesis locus, so the least-favourable IUT case (pooled H < 0.10, above-capacity H about 0.10) is the expected one; the variant's size then equals this look's size. Stylised checks gave about twice nominal at n_q = 6, and still above nominal under right skew even with t_5.

**Change.** (a) Above-capacity look: delete-one jackknife over the n_q qualifying days, factor (n_q-1)/n_q, critical value t_(n_q-1). The pooled look keeps t_21.
(b) Replace the fixed floor of 6 with n_min, set before data by a committed synthetic size check of the full §9 pipeline at H = 0.10:
- 14-day sequences, the item-3 B rule, max of the three limits;
- near-tied arms and right-skewed day-level differences over a stated family.
A cell-look with n_q < n_min blocks the KILL. Expect n_min > 6 (stylised evidence only).
(c) After commit and before any model run, compute n_q per (variant, lambda, look) from arm-independent inputs only, using the item-5 threshold, and ledger it. A variant with any cell below n_min cannot KILL, and its evaluation is skipped (a logged, compute-only exit).
(d) §14: give the margin per look. Pooled: SD/sqrt(22) x t_21. Above-capacity: SD/sqrt(n_q) x t_(n_q-1); §14's own assumed 3-6 % SD gives about 3.9-7.7 pp at n_q = 6 (arithmetic, not measured). Lower the variant-Z and overall power ranges, or mark them unknown until n_q is logged.
(e) A7 and F5: this look's cluster count is n_q, not 22, and the LOO guard adds nothing beyond the UCL for it.

## 5. [blocking; needs author] §9 l.331-338; §3 l.146; K2(c) l.383; A10 l.31; §4 O12 l.200; §12 R-PS7 l.422; §10 V2(c), V5 [B5, PS-11, S5, PS-INT-16, PS-INT-10 (R-PS7 part), S6 (threshold part), M3 (point 5)]

**Defect.** The threshold 1.05*c_k*Q_free,k has four problems.
- It counts c_k twice: Q_free already contains c_k, so the threshold scales with c_k^2, a range of 0.64-1.44 over the spread.
- It moves with delta and s across variants.
- It cannot be implemented on METANET v4, which has no Q_free without R-PS1, so R-PS7 ('identical to §9') and O12 ('aligned') are unfounded.
Also undefined: day vs draw aggregation, what a 'qualifying day' is, the location and time shift of arriving demand, and empty sequences or resamples (about 1.2 % of 14-day sequences at n_q = 6).

**Change.** (a) Use one reference per head that does not depend on plant, variant or c: Q_ref,k = 2 x the item-7 merge-section anchor q_k (per lane). Define two branches per unit u = (day, draw), with c_k entering once:
- T_fix = 1.05*c_k(u)*Q_ref,k;
- T_rel = 1.05*s*c_k(u)*Q_ref,k/(1-delta_k), or the plant's own Q_free under item 6's form.
K2 must hold under both (IUT, no alpha cost). Reviewers proposed the station value as the reference; use the merge-section anchor because arrivals are counted at the head.
(b) Arrivals A_k: v3 §5.4's A_b form ending at the head cell, i.e. mainline plus entrances up to and including E13/E14, minus exits upstream of the head; X12 and X13 are not subtracted. Shift each term by its free-flow travel time. Use true demand including uplift and lambda, in fixed 15-min clock bins from 05:00. Unit test as v3 test 12.
(c) Aggregation:
- a day qualifies if at least 1 draw qualifies;
- a day's look-J = the mean over its qualifying draws, with I* taken per unit first;
- J_s = the mean over the sequence's qualifying days, with multiplicity;
- the minimum count is of distinct days in the original sample only; LOO replicates and resamples apply the same rules without re-checking K2(c).
(d) Empty cases: a sequence with no qualifying day is redrawn from the same stream, and the redraw share is reported. A resample with no qualifying day gets H* = +inf, which counts against a KILL. The mirror case counts against a GO in the gate.
(e) R-PS7 becomes: 'The gate's above-capacity look uses T_fix exactly as in §9(a)-(d), from arm-independent true demand and the gate's c draws; no capacity probe is needed; any plant-relative look on the gate is report-only.'
(f) O12 becomes 'direction unclear across plants; branched (T_fix, T_rel); R-PS7 binds T_fix', with status argued. Add it to §16.
(g) State that V2(c) and V5 day sets use T_rel.

## 6. [blocking; needs author] §3 Heads l.142-148; §5 l.208, l.226-229; §10 V1 l.350; §4 O5/O6 l.193-194; §14; §16 [PS-1, M3, PS-3 (b)]

**Defect.** As written (m = 1 when rho_head > rho_c), the switch cannot fire in a triangular Godunov CTM where the head's receiving function caps inflow and downstream cells do not bind. Under the Courant rule the head density approaches rho_c from below, so the switch fires only on B2 spillback or by rounding (analytic argument, not simulated). Measured r is then flat, the rules pick 15 %, the plant carries about zero drop, and no V-check notices. Separately, Q_free = Q_dis/(1-delta) makes breakdown rarer as delta rises, unlike the gate's F1/R4(c) form, so 'larger delta => prize up' (O5, O6, A3) is not established for this family.

**Change.** (a) Give each head one triangular FD (v_f, rho_jam, w from Q_free,k). m only changes the cap Q_m (Q_free when m = 0, Q_dis when m = 1) in S = min(v_f*rho, Q_m) and R = min(Q_m, w(rho_jam - rho)). Define rho_c,k explicitly.
(b) Trigger on the queue side: m_k <- 1 when D_k = S_u + ramp releases into the head > (1 + 1e-6)*R_head (u = 25 for B1, 30 for B2). Release only when rho_u <= rho_c,u and D_k < 0.9*Q_dis,k. The same rule applies to the secondary heads. Never test equality at the fixed point.
(c) New V1(b), data-free, run before the drop ladder: an isolated head with synthetic demand ramped past Q_free, held, then ramped below 0.9*Q_dis, at every rung of Lambda, both heads and both secondary heads, at T and T/2. Pass if:
- the pre-activation maximum = Q_free +-1 %;
- the queued outflow = Q_dis +-1 %;
- release happens only after D < 0.9*Q_dis;
- there is exactly one on and one off transition per crossing.
(d) In replay, report activation days and minutes per head and rung. INVALID if, at a rung that is used, a head is active on fewer days than the model's own EA-2 B_k episode days minus 1, or if the median outflow while m = 1 deviates from Q_dis,k by more than 2 % [lab convention].
(e) Author choice of parametrisation:
- either the gate form: Q_free fixed across delta, Q_dis = (1-delta)*Q_free, s chosen once per variant at delta = 0, and the anchor pre-registered on the item-7 basis (never F8 pre_max15, which v3 §5.5 calls upward-biased);
- or keep the Q_dis-anchored form and branch both anchorings as cells, KILLing only if both KILL.
(f) O5/O6 and l.228: restate 'prize up' as an inference conditional on the chosen form. If the current form is kept, say in §14/§16 that variant L at the 15 % fallback is expected (by inference) to end INVALID or K2(c)-blocked without R-PS1.

## 7. [blocking; needs author] §3 Heads l.144-145 (and outline l.127-128); §10 V2; §2 A5 l.123; §4 O7 l.195; §16 [M2, PS-INT-11, PS-5]

**Defect.** 1,774 and 1,853 are F8's station Q_dis_per_lane_median (Pioneer Tr, Old Shakopee Rd), not merge-section discharge. Because the heads lie upstream of X12 and X13, the model's station discharge comes out about 2 % low at B1 and 5-7 % low at B2. The head ratio becomes 1.045 against F8's paired 1.114 (CI 1.095-1.123), outside P5c's +-5 %. V2 has floor rows only, so nothing catches this, and A5's 'lambda covers P5a +-5 %' is false at B2. This repeats v3 round-3 issue 0.

**Change.** (1) Set Q_dis,k (or Q_free,k under item 6's gate form) = s*c_k*2*q_k.
- q_k = the median over F8 heavy days at B_k of merge_section[d].discharge, computed by a committed script, with the values and the facts-file commit hash written into §3.
- Label: 'F8 merge-section discharge, (station + X12)/2 for B1, (station + X13)/2 for B2, per lane'.
- Relabel any remaining 1,774/1,853 as 'F8 station Q_dis_per_lane_median'.
- A reviewer's reading gives about 1,817 and 1,967 (unverified; the script decides).
- Do not use v3 §0.5's 1,745/1,950, which include validation days.
(2) Head ratio, decided before data. Either:
- a 2-point branch with B2 at the P5c band edges, 1.114 x 0.95 and x 1.05 times q_1 (doubles cells; keeps A2 true); or
- list 'head capacity ratio' as an A2 exception and in §16. The unpaired-median ratio is about 1.083 against the paired 1.114 (-2.8 %); disclose this.
(3) Gated V2 rows, failure = INVALID. Run in replay at the chosen s and each variant's delta, through EA-2, the observation operator and C4:
- V2(d), per head: |median(Q_dis,model/Q_dis,real) - 1| <= 0.05 on heavy matched days (P5a form);
- V2(e): the B2/B1 merge-section ratio within 5 % of F8's, on days heavy at both heads; gated if n >= 6, otherwise reported (P5c form).
s becomes 'the largest s at which V2(a)-(e) pass'.
(4) A5/O7: state coverage relative to the merge-section anchor. If the chosen s < 1, add lambda = s x 0.95, or disclose that the light end of P5a is not covered.

## 8. [blocking] §5 drop measurement, variants L/Z, s and kappa rules l.206-236; §10 V2; K0 [M4, PS-INT-06, PS-10, B1 fix (d)]

**Defect.** The delta_L, delta_Z, s and kappa rules cannot be run without choices made while r_k(delta) is visible. Missing:
- the day set and episode matching for r_k and the P5b/P9 rows;
- a minimum count (B2 has 9 real heavy days and was a knife edge in v3);
- a definition for the max over an empty set;
- a joint-head raise for Z;
- the secondary-head state during calibration, the kappa order and the V2 branch.
A post-hoc choice that lowers delta makes a KILL easier.

**Change.** Add a 'Drop-rule specification' block to §5.
(1) Frozen real day sets: D_1 = the 22 real heavy B1 days, D_2 = the 9 real heavy B2 days; the code asserts both. B1's C4 window is censored at the real B2 onset.
(2) Per rung and head: Q_k(delta) = the days of D_k whose real longest episode is matched to a C4-usable model episode (v3 §5.1: +-90 min, one-to-one).
- r_k(delta) = the median model r over Q_k(delta); write 'median' into the L rule.
- P5b(i) is paired over Q_k(delta); P9(1) is taken over B1's heavy first-active matched days.
- Recompute at every rung.
(3) n_min,k = max(6, ceil(0.75*|D_k|)) = 17 at B1 and 7 at B2 (v3 §5.2).
- A rung below n_min is 'undetermined' and counts as inside the band (L) or admissible (Z), the prize-up direction.
- Do NOT import v3 §5.2's 'shortfall = FAIL'.
- Search the max over all of Lambda; do not stop at the first failure.
- Disclose the number of undetermined rungs.
(4) Empty sets:
- if r_k(0) < 0.995 (L), branch that head at {0.5 pp, 15 %} and KILL only if K2 holds in both. Reviewers split between this and a single 0.5 pp; branching is the conservative choice.
- if no Z rung passes even at delta = 0, variant Z is INVALID: it cannot KILL, and m is unchanged.
(5) Joint heads: common-delta ladder, then the per-head choice, then a joint run at (delta_1, delta_2). Raise every head that is still inside (L) or admissible (Z) one rung at the same time. Raise only, cap at 15 %, stop when nothing changes (at most 30 iterations, order-independent).
(6) Order per variant, for s = 1.000, 0.975, 0.950: drop ladder and joint check with secondary heads OFF, then kappa at (s, delta) with delta_sec = max(delta_1, delta_2), then V2 with heads off; take the first s that passes. The on-branch reuses (s, delta, kappa) and its V2 and r_k are reported. If the on-branch fails V2(a)-(b), the KILL record drops the A8 coverage claim.
(7) Freeze every rung (s, delta, head, n, median r, P5b(i), P9(1), kappa rungs, V2 per branch) in a hashed table with a ledger row before any B or I* evaluation run. K0 requires it, and the code asserts that evaluation reads only the frozen values. Unit-test synthetic r(delta) curves: empty set, undetermined rung, non-monotone, joint raise.

## 9. [blocking; needs author] §12 R-PS6 l.421 (new R-PS11); §2 A3 l.119; §5 l.206-215; §0.6 A3 list; §16; K6; v3 §7 R4(a)-(c), §5.3 P5b/P9(1); D4.7 [B1, PS-INT-01 (point 4)]

**Defect.** The KILL via L or Z needs the gate's low-drop and primary drops to be <= delta_L and delta_Z. Only R4(d) and R2(c) are bound. R4(a)-(c) are not (target, band, day set, estimator, Delta domain), nor are v3's drop-side rows P5b(i), P5b(ii) and P9(1). R4(c)'s 'nearest attainable Delta' can also keep a larger drop than delta_L covers. A3 and §12 claim more than is bound, and the gap is not disclosed.

**Change.** Add R-PS11, committed with the screen.
(a) R4(a)-(c) carry over to v4 unchanged:
- target min(1, U_k), with U_1 = 1.059 and U_2 = 1.026 from F8;
- band +-0.5 pp; Delta_k in [-0.15, 0.15]; eta as in R4(c);
- frozen calibration heavy matched days; EA-2 + observation operator + matched-episode C4 (v3 §5.1), with B1 censored at the real B2 onset.
(b) One-sided fallback: if the attained median r_model,k of the gate's low-drop variant is below min(1, U_k) - 0.005 at either head, the R4(d) conjunct is not met (no GO). 'Nearest attainable' remains only for r above the band at Delta = +0.15, which the screen's 15 % fallback already mirrors. If R-PS1 is bound, a low-drop variant whose probe drop exceeds delta_cap also fails R4(d).
(c) v4's drop-side rows stay gated and at least as strict as v3, on the same heavy matched validation days:
- P5b(i): median paired (r_model - r_real) >= -0.02;
- P5b(ii): median r_model,k >= L_r,k (F11: 0.990 and 0.958, recomputed only by F11's rule);
- P9(1): median paired (S1_model - S1_real) <= +0.03.
Any loosening is a relaxation under §12's last sentence.
(d) A3 reads 'the criteria bound in R-PS6 and R-PS11'. §16 names R-PS11. K6: every KILL via L or Z cites R-PS11.

## 10. [blocking; needs author] §0.6 A1 l.22; §5 variant L l.207; §12 R-PS1 l.402, last sentence l.427; A3 l.119; §16 l.504; outline l.556 [B2, PS-INT-01]

**Defect.** A1's fallback ('if a METANET probe cannot be specified in v4, L falls back to the measured-r rule') can only be evaluated when v4 is written, which never happens after a KILL. The probe is also under-specified (merge share, delta_m, theta1, windows). In METANET the head drop depends on the merge flow through delta_m, so an isolated mainline-only probe can read <= 1 % while the in-corridor drop is larger. Precedence against R4(c) is undefined. Variant L with R-PS1 is §14's main power source, so this is where a non-conservative KILL is most likely.

**Change.** Decide once, at commit: bind R-PS1 completely now, or do not bind it (then L uses the measured-r rule from the start). Either way, delete the A1 fallback clause and answer the outline l.556 question in §12.
If bound:
(a) Probe specification.
- Cells: the head cell plus pre-registered upstream and downstream cells (v3 §1.4).
- Parameters: the plant's frozen theta1, delta_m, phi, tau, nu and kappa; c = 1; free outflow downstream.
- Demand: a fixed-rate mainline ramp plus a release at E13/E14, with the share on a pre-registered grid from 0 to the largest calibration-day share in the 60 min before onset.
- Q_free = the largest 15-min head outflow before first activation. Q_dis = the mean head outflow over a fixed plateau of at least 30 min starting at activation + 10 min, taken on model flows (not through EA-2).
- Probe drop = the max over shares of 1 - Q_dis/Q_free, per head.
(b) Precedence. The gate's low-drop domain becomes [-0.15, Delta_cap,k]. R4(c)'s bisection runs inside it. If no Delta_k >= -0.15 meets the cap, the gate cannot GO; there is no return to measured r. Record a dated author ruling that this tightens R4(d).
(c) Build. Unit-test that the probe returns delta_cap on CTM-2C at every share, with a tolerance fixed now. Also run it once on the frozen v3 plant code as an implementability test. Ledger both before any calibration-day run.
(d) Replace l.427 with: 'Every binding is specified to implementation level, and its probe is code-tested in this build, before the screen commit, because after a KILL no gate protocol will exercise it. A later relaxation needs a dated addendum stating which step a past KILL lost.'
(e) Keep in A3 and §16 that monotonicity of H in delta remains an inference. Do not use max(delta_cap, delta_measured) as the main fix.

## 11. [blocking; needs author] §6 l.254-264; §4 O4 l.192; §2 F1 l.97; §7 seed 7,191,102 l.301; §12 R-PS4; gate draft §3 l.101, l.106-108; §0.6; §13 build order; outline l.559 [PS-2, PS-INT-02 (informed part), M5, PS-INT-18, PS-8 (LP fallback)]

**Defect.** Missing: I_plan's mapping and input series; I_hero's base law, features, bins, grid, objective and information set; I_mpc's model class, fit data, estimator and fold, and its LP (Delta t, objective, terminal cost, epsilon, VSL, state input, infeasibility fallback). 'I* uses no detectors' contradicts a HERO loop. R-PS4 binds the gate to these undefined objects and silently replaces gate draft §3's I_mpc (mpc_f on a fitted METANET) with an LP on a fitted CTM. Under §13 they would be written on D4, after D2 and D3 have run on all 22 days, which is a hidden-variant risk. A weak I also collapses I* to min-B and makes a KILL easy.

**Change.** Add a §0.6 item A14, 'arm and plant specification frozen'.
Add an appendix 'Informed arms (binding on the screen and the gate)' and an arm-spec JSON. Put its SHA-256 in the header, in R-PS3/R-PS4 and in every ledger row; the runner refuses to start on a mismatch. For each arm give the information set, plant-agnostic pseudo-code, hyperparameters, tuning procedure and frozen artefacts.
- I_plan: the exact tod_cnt formula and the variable it is fed (e.g. arriving demand at the head by conservation, with any cap stated).
- I_hero: the base HERO law, shared with the B hero, from a source read in full, otherwise [VERIFY]; features from true demand only; bins; a grid that contains the B hero grid; a defined activation lead; the objective.
- I_mpc: model class and free parameters; fit data under seed 7,191,102 (tuning-fold days, per fold, a stated control set, (c1, c2) per v3 R3(c)); estimator; the LP's Delta t, variables, an objective consistent with §8 J, terminal cost and the exact meaning of epsilon; VSL as boundary caps with the inverse map to v_VSL (item 14); state at each re-solve; max_wait and storage as soft constraints with a stated slack penalty; on infeasibility or time-out, the shifted previous plan, else the I_hero command, with the share logged.
New row O4b, replacing 'I* uses no detectors':
- I_plan and LP-OC are open-loop on true demand.
- I_mpc and I_mpc_exact read the true noise-free state at each re-solve and never read c.
- I_hero enters I* twice, each with its own table: I_hero^clean (noise-free station-cell values every step) and I_hero^B (the B hero's exact sensing and noise streams).
- Unit tests: the state equals the plant array; the clean variant draws nothing from the noise RNG; no I reads c.
List the solver settings tuned on the throw-away day, with their candidate values, and freeze them in the spec. Ledger the throw-away runs and the §13 inclusion decision.
Amend gate draft §3 in the same commit and name the amendment in R-PS4.
Freeze the spec before D2's calibration-day replays and diagnose only on the throw-away day. Any change is a dated spec amendment made before the affected run.
Fallback: if any part cannot be fixed before commit, K6 labels F1 'argued'.

## 12. [blocking] §6 B arms l.246-252; §4 O3/O4 l.191-192; §3 l.135; §8 l.320; §12 R-PS3 l.408-413; §15 l.494; §13 [PS-7, PS-INT-02 (B part), M7 (B objective part)]

**Defect.** No B arm can be built from the text.
- const: no grid.
- ALINEA: no stations, conversion or grids. E13 is a real fork: Anderson Lakes reads head cell 26, while Pioneer Tr is 2 km downstream.
- HERO: no algorithm and no code.
- MTFC: measurement points and grid are missing, and mtfc.py hard-codes rho_set = 32 and acc_b = 0.9, which conflicts with R6.
- tod_cnt: no mapping.
- No noise model, tuning objective, penalties or budget; 'served >= B - 1 %' is circular during tuning.
So R-PS3's 'identical definitions' points at nothing, and §15 l.494's claim is false.

**Change.** Add §6.1 'Arm specification' to the item-11 frozen spec, before D2.
(1) Sensing: per station cell, every 60 s, mean density (veh/km/lane) and flow; ramp queues from the FIFO curves.
- Noise: y = x*max(0, 1+eps), eps ~ N(0, 0.05^2) i.i.d. per sample, quantity and station; streams 7,191,101 and 7,191,501. R-PS3's sigma is the SD of this factor.
- tod_cnt counts are these noisy flows summed into 15-min bins.
- Extend l.135 to every cell B may read.
(2) Stations, by a data-free rule: E9 cell 18; E12 cell 23; E14 cell 32; E13 Pioneer Tr (cell 30). Anderson Lakes (head cell 26) is excluded from B sensing and the exclusion disclosed (a weaker B, which is conservative).
(3) Laws and numeric grids:
- const: per-ramp or shared, stated; the grid includes off.
- ALINEA: r(k) = r(k-1) + K_R(rho_hat - rho_meas), clipped to [r_min, 2,200]; rho_hat = theta*rho_c; grids for K_R and theta; an activation rule. Define 'weakened' (l.272) or delete it.
- HERO: a full algorithm from a source read in full ([VERIFY] until then), including E13's min-of-two rule, with grids.
- mtfc_rm: area cells (item 14), rho_out and q_c cells, rho_hat as a fraction of rho_c, gains fixed or gridded, acc_b = 1, and a joint grid with HERO.
- tod_cnt and I_plan share one formula.
(4) Tuning:
- objective: mean J over tuning-fold days x draws at lambda = 1, with the reason for the mean against F3;
- side constraints: a hard filter with a min-violation fallback, or an exact penalty form with weights;
- during tuning, 'served >= served_nc - 1 %';
- budget: full enumeration, with counts per arm and configuration.
(5) R-PS3 refers to §6.1 and adds 'same J objective and penalty form, weights no larger than the screen's, budgets >='. A V4/K0 unit test checks that the coded grids, stations and laws equal the table. Correct §15 l.494.

## 13. [blocking] §3 Diverges and merges l.152-154; Geometry/stations l.134-136; Day l.179-183; FD/v_f [PS-3, PS-INT-02 (merge ratio)]

**Defect.** The merge priority ratio has no value and no rule for assigning it across merge types. Entrance placement (node or in-cell) and the mixed diverge/merge nodes are unstated. The CTM station series (which flux, which speed) are undefined, although they drive EA-2, C4, the drop ladder and V2. beta after 23:00 is undefined (the inputs end at 23:00 and the drain runs to 01:00). v_f taken as 'the median of the F6 lane medians' mis-scales c_s, which is defined against m_G. A priority chosen after the throw-away output would be a hidden variant, and it could starve E13 so that I* falls back to B.

**Change.** Add §3 'Node model and observation', fixed before commit, with a unit test for each item.
(1) Each entrance and exit acts at the upstream node of its v3 §1.5 cell, with movements in km order. Write out nodes 0|1, 11|12, 35|36 and the 4-input node 21|22. Same-node diverges limit through flow by strict FIFO.
(2) Merge priority proportional to approach lanes: ramps 1, mainline = upstream lanes, giving 2:1 at E13/E14 and 2:1:1:1 at 21|22; lane-adding E9/E10/E11 take 1/n_down. Never adjusted to pass V2. Author option, because the sign on H is unclear: add a branch with mainline priority 0.9 at every merge (IUT, no alpha cost, more compute), or disclose the choice in §16.
(3) Station series: q = the mainline Godunov flux from cell i to i+1, with the v3 §1.5 correction; v = q/(n_i*rho_i), or v_f when rho = 0; 5-min flow = mean q; 5-min speed = sum(q)/sum(n*rho).
(4) v_f per group = F6 m_G, so that v_f/c_s = m_s.
(5) 04:00 state on the free-flow branch (v3 §2.6), queues 0, m = 0. Inputs held per 5-min bin; class-B balances held per 15 min.
(6) Drain 23:00-01:00: all demand 0; each beta_e held at its last valid bin (v3 §3.3.5).
(7) §0.6 and §15 record that every value was fixed before any calibration-day run.

## 14. [blocking; needs author] §3 VSL l.171-173; §6 mtfc_rm l.251 and I* caps; §10 V1 l.350; §12 R-PS10 [PS-9]

**Defect.** There is no map from MTFC's b to v_VSL. The R6 areas cut through cells 20, 23, 24 and 27 and no membership rule is given. rho_c under VSL is undefined, so B2's VSL loop fires B1's cell-26 switch with no queue under one reading and never under the other. mtfc.py's acceleration-area output conflicts with R6. MTFC sensing points and I_mpc's VSL representation are unstated. V1's 'both forms' cannot be run if it means the MTFC modified FD. A builder choice that gives mtfc_rm more authority than v4 would lowers J_B and can make a KILL non-conservative.

**Change.** Add 'VSL translation' to §3, add a §0.6 item, and extend R-PS10 to bind it.
(1) v_VSL,i = b*v_f,g(i), with b in {0.2,...,1.0} from mtfc.py; b = 1 means no VSL term.
(2) Area cells listed by number, and the list binds: proposed B1 = {20, 21, 22} and B2 = {25, 26, 27}, i.e. cells with more than 50 % of their length inside the R6 range. Cell 24 is a knife edge, which is why the list must bind.
(3) In a VSL cell: S = min(v'*rho, Q', head cap) and R = min(Q', w(rho_jam - rho)), with w and rho_jam unchanged. rho_c stays at its no-VSL value. V1 reports whether VSL alone fires the cell-26 switch.
(4) No acceleration area: discard mtfc.py's second output, disclosed as a deviation from the source design.
(5) Name MTFC's rho_out and q_c cells and its grid (item 12).
(6) I* caps: a time-varying absolute cap u_b(t) in [0, min(S_up, R_down)] on the inflow and outflow boundary of every listed area cell. I_mpc's VSL enters the LP as these caps.
(7) V1 reads 'min form (B) and ideal caps (I*)'. The MTFC modified FD is not run, unless the author supplies its CTM form and a source that has been read before commit.
(8) Author backstop, which costs power: if (1)-(6) cannot be pinned identically for v4 before commit, K2 must also hold with B = {const, tod_cnt, alinea, hero}.

## 15. [blocking; needs author] §12 header and R-PS1-R-PS10 (+ new R-PS11/12); §0.6; decisions log; gate draft (untracked) [process item consolidating the binding changes in items 1-3, 5, 9-11, 14, 16, 17, 26; PS-INT-21 (R-PS5)]

**Defect.** Many fixes add or change commitments on the future gate (R-PS1, R-PS3, R-PS4, R-PS7, R-PS9, R-PS10, new R-PS11 and the plant-settings binding) and amend the untracked gate draft. D4.7 bound only R4(d) and R2(c). A KILL's conservativeness rests on these bindings, and after a KILL no gate will ever test them. R-PS5 is a gate-design change, not something the KILL relies on, which makes §12's header claim inaccurate.

**Change.** Record one dated decision (D4.8) that lists each new or extended binding verbatim and states that each one only tightens the gate and never weakens a baseline. Commit the gate draft with the screen, or record its sha256. Move R-PS5 to the decisions log as a gate-draft amendment. Keep §12's header claim true item by item.

## 16. [major; needs author] §6 l.246, l.254-257; §7 l.301; §12 R-PS3/R-PS4; §2 A1(a) l.112; §12 l.427; new §0.6 item [M6]

**Defect.** The screen re-tunes B per variant, but nothing binds the gate to re-tune B or refit I on the conjunct variants (the R4(d) low-drop, R2(c) zero-uplift and joint conjuncts). A natural reading evaluates arms tuned on the primary plant, which over-meter on L and raise H_gate(L). The screen's own I side is also not stated to be fitted per configuration.

**Change.** (1) R-PS3: 'On every conjunct variant and every R5 ensemble member, every B arm is re-tuned on that variant's plant, with the same days, folds, grids, budgets, noise and update period; no arm is evaluated on a variant with settings tuned on another plant.'
(2) R-PS4: the same rule for I_plan's mapping, I_hero's table and the I_mpc model.
(3) §6: these are fitted per configuration (variant x spread x secondary heads), cross-fitted on the same fold as B. Seed 7,191,102 is spawned per configuration via SeedSequence.
(4) A1(a): 'on the same variant plant'. §12: relaxing these clauses voids A1 for the affected variants.
(5) Only if the author wants frozen-policy robustness checks instead: tune on P, evaluate on L, Z and LZ, and KILL only if both branches KILL (about twice the tuning compute).

## 17. [major; needs author] §3 Ramps l.165-167; §4 O9 l.197; §0.6 A9 l.30; §6; §8; §12 R-PS2/R-PS3/R-PS4 [M7, PS-8 (binding part)]

**Defect.** Several settings that move the prize are not bound on the gate:
- storage: the unit and s_jam are [VERIFY], and x1.25 is relative to the screen's own source;
- r_min (A9 still open);
- the 2,200 veh/h maximum;
- max_wait for B (240 s is bound for I only);
- the control window and warm-up;
- B's tuning objective and penalty weights;
- I's side-constraint tolerances.
A gate with a smaller s_jam, a lower r_min or B tuned on another objective has a larger H than the screen covers, so A2's premise is undefined for these settings.

**Change.** (1) Close A9 with numbers: storage in vehicles at x1.0 and x1.25, and r_min, for E9, E12, E13 and E14, each with its unit and a cited source.
(2) New binding 'plant settings shared by all arms':
- gate storage <= the screen's x1.25 value at every controlled ramp;
- gate r_min >= the screen's;
- maximum meter rate 2,200 veh/h per ramp lane;
- one plant-level override at storage or max_wait = 240 s, with the release law of item 25, for every arm; no B arm gets a stricter override than I;
- control 05:00-23:00 after an identical uncontrolled 04:00-05:00 warm-up, then the §3 drain.
Bind numbers, not 'the same source'.
(3) §6 states the screen's B objective (item 12).
(4) R-PS3: the gate tunes B on the same J, with the same penalty form, weights no larger than the screen's, and budgets >=.
(5) R-PS4: I's side-constraint tolerances are no looser than §8.
(6) Add these to the A3 list and to the KILL-record text.

## 18. [major; needs author] §7 l.286; §6 l.246; §9 l.340-344; §11 K2/K4; §13; F5; §14 l.483; §16; K6 [S3]

**Defect.** Every arm is tuned once per fold on 11 days, and the bootstrap, jackknife and LOO never re-tune. The UCL is therefore conditional on one split and one tuning realisation and leaves out tuning variance, which is anti-conservative for a KILL. The gate re-tunes on its own days, so A1 does not cover luck in the screen's tuning on either side.

**Change.** (1) §7: pre-register R = 5 splits. Split 1 is the existing date-alternating 11/11 split; splits 2-5 are random balanced permutations from seed 7,191,103 (tuning-side reserve; not 504-509, which are test-role; seed use needs author approval). For each split, redo the fold-dependent pipeline: B tuning, the tod_cnt/I_plan/I_hero mappings, and the I_mpc fit and runs. State whether the I_mpc fit uses fold days.
(2) K2: a variant KILLs only if K2(a)-(d) hold on every split.
(3) K4: run splits 2-5 only for a variant that passes on split 1, so a NO-KILL costs nothing extra. Budget this in §13 as an estimate.
(4) Do not stratify the bootstrap by fold, because that narrows the UCL.
(5) Optional, on the KILL path only: a pipeline LOO that re-tunes the fold without the deleted day.
(6) F5, §14, §16 and K6: the false-KILL rate is nominal conditional on the realised tuning; the max over splits is a mitigation, not a calibration. The UCL is also conditional on s, the drop rungs and kappa, which are fitted on the same 22 days and chosen in the prize-up direction.

## 19. [major; needs author] §11 K1 l.374-379, K4 l.386-389, K0; §5 l.217, l.229; §9 l.342; §0.6 A2 l.23; §12 R-PS6 l.421; §13; §14 [PS-14 (a, d), m1, S7, S11, PS-INT-14]

**Defect.** With A2 bound by default, K1 counts L, Z and LZ (m = 3, 99.17 %). K4's 'L (or LZ)', §9's 'm = 2, 98.75 %', §13 and §14 all assume two variants, and running three at 98.75 % gives a Bonferroni bound of 3.75 %, not 2.5 %. Also unclear: INVALID-variant semantics; whether m changes when a variant is skipped or exits early; whether Z runs after L KILLs; R2(c)'s reading; and the A1-A10 labels, which clash between §0.6 and §2.

**Change.** (1) K1 binding table, cited by §9, K4, §13 and §14:
- {L, Z}: m = 2, 98.75 %;
- neither bound: {P}, m = 1, 97.5 %;
- R4(d), R2(c) and A2 all bound: the author picks {LZ} (m = 1), {LZ, Z} (m = 2) or {L, Z, LZ} (m = 3, 99.17 %).
'm = the number of variants tested, fixed by this table before the run.' Skips, early exits and INVALID never change m or alpha_v.
(2) A dated author ruling on whether v3 R2(c) ('as R4 requires on the low-drop variant') already imposes the joint conjunct.
(3) An INVALID variant cannot KILL and does not block the other variants. Align l.229, the §10 header and K0.
(4) K4: 'The first cell-look failing any of K2(a)-(d) ends that variant. Every bound variant runs to its own end, even after another KILLs. Unrun cells are ledgered as not run.'
(5) Rename the §2 arguments (e.g. G1-G10) and fix the cross-references, including R-PS6's '(A2 below)'.

## 20. [major; needs author] §11 K7 l.397; §10 header l.348; K0 l.373; §7 l.307-309; §16-§17 [PS-INT-08]

**Defect.** 'Bug' is undefined, so an INVALID or unwelcome result can be 'fixed' and re-run on the same seeds. New versions have no seed rule and no accounting, and each re-tests the same 22 days, so KILL-shopping across versions inflates the false-KILL rate.

**Change.** (1) Replace K7 with an adapted v3 §6.3. After the first calibration-day replay, code may change only to correct a deviation from this file's written §2-§10. Each fix comes with a unit test, committed with it, that fails before the fix and passes after. Everything affected is re-run on the original seeds, both outcomes are logged, and the fixed run decides. Any other change (plant, cell or drop rules, ladders, the s set, kappa, V thresholds, arms, grids, statistics, labels) is a new version.
(2) A new version is committed and author-approved before it runs. It uses fresh reserved seeds (013-019, 104-109, 504-509, mapped role for role and approved by the author; 103 is used by item 18). Version k, counting every version that reached an evaluation run, KILLs only at one-sided 1 - 0.025/(m*k). Every KILL record states 'version k of N' and the earlier outcomes.
(3) Within a version, an INVALID can be reversed only through the bug rule, never by changing a V criterion, the s set or a cell rule.

## 21. [major] §10 V5 l.364; §11 K0 l.373; §7 seed 7,191,012; §14 [PS-INT-09, PS-17 (a)]

**Defect.** V5 requires I* to beat nc by >= 10 % in the delta = 15 %, lambda = 1.10 cell before any KILL. That confounds a broken I* with a genuinely small prize, which is the very case the screen exists to detect, so INVALID is positively correlated with the KILL condition. The cell's s, branch and minimum day count are unspecified, and seed 012 is assigned to draws that do not exist.

**Change.** Replace V5 with V5a, which gates and is data-free, and V5b, which is report-only.
V5a, run before any calibration-day run:
- inputs: synthetic, either the throw-away median day (seed 7,191,000) or a pre-registered trapezoidal overload, at delta = 15 %, c = 1, s = 1, secondary heads off;
- a pre-registered feed-forward reference pi_ref (cap at each area exit = (1-eps)*Q_free,k minus the arrivals between that area and its head, active while the uncapped arriving flow exceeds the cap) gives J_ref;
- pass if the exact-model LP-MPC recovers >= X % of (J_nc - J_ref), with X fixed now; the I_mpc fit recovers Q_free, Q_dis and v_f of a known CTM-2C within a fixed tolerance; and I_plan and I_hero reproduce their frozen mappings in unit tests;
- a failure is a pre-data bug to fix, not an INVALID.
On the rich cell, with s, branch and minimum days stated: the exact-model LP-MPC's J <= J_pi_ref + tau*(J_nc - J_pi_ref) per unit, with tau fixed now. Add pi_ref to the I* candidates.
V5b reports (J_nc - J_I*)/J_nc and the recovered fraction of (J_nc - J_LB). Never gate on J_LB.
K0 becomes 'V1-V4 and V5a'. Relabel or drop seed 7,191,012. Disclose the change in §14.

## 22. [major] §10 V3 l.359; §15 l.486-492 [PS-INT-07]

**Defect.** V3 relaxes v3's strict step-halving rule to '<= 1 day per head', citing 'v3 failed on a single near-tie day'. The stop record (metanet_calibration.md l.87) says the opposite. The relaxed rule would have passed the defective v3 plant (one P_2 day changed, |dJ|/J = 0.0023). The near-tie fact comes from an undisclosed post-stop probe. A looser validity check makes a KILL easier.

**Change.** Restore the strict rule: identical head-activation day sets at T/2, keeping |dJ|/J <= 1 %. Specify the arms (nc and I_plan), the units (every day x draw at lambda = 1, c = 1, at each variant's highest and lowest rung, or every evaluated cell if compute allows) and what counts as a change (the symmetric difference of the day sets). Delete the bracketed rationale. If a tolerance is still wanted, it needs all of the following: a data-free CTM argument, a §0.6 item, a §15 disclosure of the post-stop step-probe input, a KILL allowed only if it holds at both T and T/2, and a positive control that the check must fail.

## 23. [major] §5 secondary heads l.235-236; §3 l.135, l.147-148; §6 B stations [PS-INT-05, PS-6, m2 (kappa pairs)]

**Defect.** The km 2.39 secondary head sits in cell 23, which S of Highwood Ave (P_1's upstream EA-2 station) reads. That contradicts l.148 and repeats D4.4 lesson 4: in the on-branch, B1 events, V2 and r_1 are driven by the secondary switch. The kappa rule's 'that cell's station pair' is undefined; read as P_1 (active 22/22 days), it is vacuous and kappa falls to 0.90. Cell 26 (Anderson Lakes) also makes l.148 literally false.

**Change.** (a) Move the km 2.39 head to the 22->23 boundary flow: f = min(S_22, R_23, C*(1 - delta*m)), with memory driven by rho_22 under item 6's trigger. That cell is the last before the merging drop, and no station reads it. Pre-register whether B1's VSL may act there (cell 22 is in B1's area, item 14), or disclose the overlap.
(b) Name the kappa pairs:
- km 2.39: (Highwood Ave S1772, cell 21; S of Highwood S1773, cell 23);
- E15 head (cell 33): (Old Shakopee Rd S1141, cell 32; T.H.101 S1610, cell 36);
- never P_1.
Define 'no real episode' by P8(i); count an event-invalid station day as a false-episode day; state whether kappa scales Q_free or Q_dis and which replay setting is used; log, per rung, the days with a model episode and no real one.
(c) Restate l.148 with a named station set: event-layer and B-sensing stations never read a switched cell, and Anderson Lakes is excluded from B sensing and V/event checks, disclosed. Add a D1 build check that derives the switched-cell set and the station-to-cell map and fails on any intersection.
(d) Optional: a secondary head triggers only while it is the active head.

## 24. [major] §3 Other cells l.150; §3 FD; §10 (new V7); K0; K2; §4 O7 [PS-INT-12, PS-4, m2 (cap part), PS-13 (l.150 part)]

**Defect.** Non-head capacity is only a floor, and its maximum is not defined over days, lambda or uplift.
- The 2-lane floor (3,706 veh/h) is below Q_free,1 at c1 = 1.2, delta = 15 % (about 5,009).
- Under the F16 median-day reading, cell 27 binds at c = 1 for delta above about 12 %.
- lambda = 1.10 reaches the cap exactly, and override flushes can exceed it.
- lambda_i (lanes) collides with the demand multiplier lambda.
Nothing checks for binding. A binding non-head cell truncates the drop and lowers H (non-conservative) while the record claims the full delta.

**Change.** (1) Rename lanes lambda_i to n_i throughout §3.
(2) C_i = n_i * max(a_i, b_i, max_k q_k/(1-0.15)), where:
- a_i = 1.10 x the largest per-lane Q_free of any head upstream of cell i over the whole grid (c = 1.20, delta = 15 %, s = 1), for cells between that head and the next;
- b_i = 1.10 x the maximum over the 22 days and both input modes, at lambda = 1.10, of queue-free arriving demand per lane at the 5-min input resolution (not the F16 median), plus 2,200 veh/h for each controlled meter that feeds cell i with no head in between.
Compute these once from inputs and commit them as a facts row.
(3) Trapezoidal FD for non-head cells: a flat top at C_i, with w and rho_jam fixed per group from the reference capacity, so a raised cap does not change spillback. Re-check w*T/L_min <= 1.
(4) New V7 / K2(e): log every step in which a non-head, non-secondary cell's sending or receiving flow is >= 0.999*C_i, in every run. Any such step makes that cell-look INVALID (it blocks a KILL). Run it under nc at lambda = 1.10 before evaluation (K0).
(5) Report delta_eff,k = 1 - Q_dis,k/min(Q_free,k, the smallest downstream C_i) next to delta_k, and argue A3 on delta_eff.

## 25. [major] §3 Ramps l.164-167; §6 H_LB l.269; §2 F6 l.108; §10 V6 l.365-369, V4, header [PS-8]

**Defect.** The override release law and the meaning of 'off' are unspecified. Under Daganzo merges, max_wait cannot be enforced for any arm when the head is congested, so V6's 'waits <= 240 s + one step' and 'the LP accepts each simulated trajectory' fail by construction. With hard storage and max_wait constraints, J_LB is not a relaxation of what the plant can produce and F6's 'admissible' is undefined. V4 also contains J_LB <= J_I*, so a J_LB that is not a relaxation can make the whole screen INVALID.

**Change.** (1) Release law: q_rel = min(S_merge(t), max(r_cmd(t), [A(t-240 s) - D(t)]+/T, [N(t) - N_max]+/T)). 'Off' means r_cmd = infinity. State that this minimal-intervention law is the optimistic direction and add a §4 row. Log merge-capped excess waits and excess storage per arm as plant physics.
(2) Compute J_LB without max_wait and storage (merge split free, holding allowed, Q_free, c known) so that it is a true relaxation. An optional J_LB,mw with those constraints is report-only. Use no soft penalties in a bound. F6: 'admissible' = any controller acting through the plant's actuators, with the plant override in force.
(3) V6: 'in every step where q_rel < S_merge, the realised wait <= 240 s + T'. Keep 'the LP accepts each trajectory' and 'J_LB <= J_sim'. Move 'J_LB <= J_I*' from V4 to V6. The §10 header matches K0: a V1-V5 failure means INVALID; a V6 failure removes J_LB only.
(4) Soft constraints and the fallback for I_mpc and LP-OC are as in item 11.

## 26. [major; needs author] §3 Inputs l.156-161; §4 O7 l.195; §2 A2, A5 l.123; v3 §7 R1(c)-(e) [PS-13, PS-INT-13]

**Defect.** The scope of lambda ('every exogenous input') is ambiguous: it is unclear whether it covers the controlled-ramp arrivals, the f2f merges (with or without uplift) and the class-B exits or beta. Under one reading the head demand shifts by less than 10 %, and A5's coverage claim fails.
P0's 80 % rule is not stated per ramp or pooled, invalid ramp-days have no rule, and the storage scale inside P0 is unstated. R1(e) detector agreement is absent (F4 holds no replay-vs-Queue comparison). R1(d) is silently replaced by V2. A2's claim that every unclear-sign direction is branched is false for the demand source.

**Change.** (1) lambda multiplies, bin by bin, the boundary and all 15 entrances: the 6 upstream replay inflows, the 4 controlled-ramp arrivals or their fallback, E7/E8/E10/E11 after uplift when it is on (served counts in Z), and the E15 class-B balance. It never multiplies an exit volume or beta_e. Build assertion: A_k(lambda)/A_k(1) = lambda to within 1e-9. Keep the P5a-coverage claim only if it holds under this definition; otherwise argue it in A5.
(2) P0 per controlled ramp over its 22 days, with storage x1.0. A ramp with >= 18/22 valid days uses Queue arrivals, and each invalid ramp-day uses that ramp's replay inflow (flagged, counted, never dropped). A ramp with < 18 valid days uses replay inflow on all days, disclosed. List E14 per R1(c); P0 is not informative there.
(3) R1(e): commit replay-vs-Queue daily totals for E9, E12 and E13 before evaluation. Any ramp outside 5 % gets a demand-source branch {Queue, replay} (IUT), plus a binding that the gate states its reconciliation.
(4) State that R1(d) does not apply as written. Add a CTM-internal check (mode C with meters at replay inflow vs mode R) with a tolerance fixed at commit [lab convention].
(5) Report 'all controlled ramps at replay inflow' as a sensitivity.

## 27. [major; needs author] §3 FD l.139-141; §10 V2; §4 O10 l.198; §2 A2; §16 [PS-12]

**Defect.** rho_jam = 180 is v3's METANET rho_max cap, not a triangular jam density. With w = Q/(rho_jam - Q/v_f), G2 gets w of about 11.4 km/h, so CTM queues near S of Highwood run at about 9-12 mph against about 26 mph recorded in v3 §0.7. Queues will be denser and shorter (inference). Real B1 queues pass the I-494 merges on 17/22 days (F9), and V2 does not check queue extent. Prize that depends on extent is under-represented, and its sign is unclear, yet this direction is not set optimistically, not branched and not listed in §16.

**Change.** (1) Relabel: 'rho_jam = 180: v3 §2.3 rho_max carried over as a triangular jam density [lab convention]'.
(2) Long-queue branch: try the ladder rho_jam in {150, 120, 100, 80} and take the first rung at which v3 §5.4's P7b rule passes one-sided in replay. If none passes, use the last rung and disclose it; this is not an INVALID.
(3) Make the FD branch {base, long-queue} a cell dimension; the KILL needs both (IUT). Run long-queue first in K4's order. Re-run the drop ladder, s and kappa per branch, and use each branch's w and rho_jam in VSL's Q'.
(4) V2(d), report-only: the B1 extent distribution against F9, and the share of days the nc queue covers X10, X9, E10/E11 and E12.
(5) Qualify O10 as conditional on extent, and add a §16 bullet.
Minimum if the compute is refused: (1), (4), (5), plus a line in A5 that the lambda >= 1.05 cells are the only cover for queue extent.

## 28. [minor; needs author] §5 variant Z l.211-215; §0.6 A8 l.29; §0.5 l.54; §15 l.493; §17 [PS-INT-04]

**Defect.** delta_Z is selected against the F11 floors L_r,k, which are statistics of 97 validation days (15 Wednesdays + 82 Tue/Thu). That conflicts with v3 §8.5, R4(f) and the A10 use rule. The 0.02 slack rationale points the wrong way: calibration-day real medians exceed validation-day ones, by 0.018 at B1 and 0.031 at B2. The §0.5 assertion is also overstated. The KILL stays conservative, because a looser floor admits a larger delta_Z.

**Change.** Preferred: remove P5b(ii) from variant Z's rule and keep P5b(i) >= -0.04 and P9(1) <= +0.05 on calibration-day replays. A subset of the gate's rows admits a larger delta_Z, so A3 holds. Report r_k at delta_Z next to L_r,k as a label only. Delete A8, the slack sentence at l.215 and the §15 F11 bullet. §0.5 becomes: 'only the 22 calibration days are simulated or read as raw data; no validation-day statistic enters any screen rule'.
If P5b(ii) is kept instead, A8 becomes a dated deviation that names v3 §8.5, R4(f) and the A10 rule, states the 97-day composition, rewrites the slack as an optimism margin, and adds to §17 that delta_Z is not design input for v4.
Never use F8's Lc_k as the floor: at B1 it is tighter (0.994 vs 0.970), which shrinks delta_Z and is non-conservative.

## 29. [minor] §10 V2(c) l.355 [PS-INT-17, PS-17 (b), PS-1 fix (6)]

**Defect.** V2(c) restates the gate draft's D-check ('counted peak <= discharge + 5 %'), which v3 §5.3 and R8 say is superseded by P9. 'Discharge' is also undefined for the screen plant: read as Q_dis, the check rejects every delta above about 4.8 % in a plant whose switch works.

**Change.** Make V2(c) v3 P9, as R8 requires: P9(1) paired S1 overshoot against the real S1 on calibration heavy first-active matched days, and P9(2) quoted verbatim from v3 (a reviewer reads it as >= 1.2 on >= 5 days). Restate P9's arrival definition and discharge station, and give a minimum day count with an INVALID rule if it is not met.

## 30. [minor] §9 l.336, l.340, l.344; §7 l.304-305 [S9, PS-14 (b, c)]

**Defect.** The point estimate uses 2,000 sequences, the resamples use 500, and the LOO/jackknife sequence count and seed are unstated. The different amounts of Monte Carlo selection noise distort BCa's z0, and fresh draws in each LOO replicate inflate the jackknife variance.

**Change.** Draw one fixed matrix U (2,000 x 14 uniforms) from seed 7,191,502. Every estimate (full sample, each delete-one sample for LOO, jackknife-t and the BCa acceleration, and each resample) maps U onto its own day list with index = floor(U*n). Stream 7,191,503 draws only the day-cluster resamples. If compute forces 500 sequences in the resamples, use U's first 500 rows there and compute z0 and the percentile comparison against a 500-row point estimate. K2, LOO and the jackknife use all 2,000.

## 31. [minor] §9 l.346; §6 l.270-271; §10 V3 l.358, V5 l.364; A1(b) [S10]

**Defect.** 'One convention throughout' does not hold. A_ctrl is a ratio of sums. G_plan, G* and the V3/V5 forms are unstated, although V3 and V5 decide INVALID. And a median over 14-day sequence means behaves as a smoothed mean of day differences, not a per-day median.

**Change.** Give V3, V5b, G_plan and G* the gate form (median over the same sequences of paired differences, divided by the median of the reference), or state the mean form explicitly. Label A_ctrl as a ratio of sums. Add the smoothed-mean sentence to §9.

## 32. [minor] §2 F4 l.104; §1 l.82; K6 [S8, PS-INT-15 (F4 part)]

**Defect.** F4's 'a KILL implies no gate GO' conflates the true H with the gate's sample H. The gate can still GO through noise when its true H is below 10 %.

**Change.** Rewrite F4 and the KILL-record sentence: 'A KILL supports, at level alpha on the screen plant, that the gate's true H < 10 % on the conjunct variant, followed by an argued transfer. A gate GO after a KILL would be a false GO, which the gate's CI and the confirmatory run handle.'

## 33. [minor] §2 A5 l.121-125; §4 table; §5 l.229, l.233; K6 l.391-396 [m3, m4, PS-INT-19]

**Defect.** A5 says c = 1 and i.i.d. U[0.80, 1.20] 'bracket' the gate's F_hat. That needs H to be monotone in spread, which §2 disclaims, and it ignores F_hat's atoms at the clip bounds and the c1-c2 dependence. §4 has no row for s, although s is set at the least-congested admissible end. KILL records do not state 'selected from N' for s (3 values), kappa (9) and the delta rungs.

**Change.** Restate A5 as an argument, not a bracket. Alternatively add one comonotone two-point cell {0.8, 1.2} with c1 = c2 and keep the i.i.d. cell. Add a §4 row: 's: direction unclear; covered by lambda in {1.05, 1.10} (argued, A5)'. Add 'selected from N' for s, kappa and delta to the K6 labels.

## 34. [minor] §17 l.526-527; §2 A4 l.120 [PS-INT-20, PS-INT-21 (A4 part)]

**Defect.** After a NO-KILL, CTM-2C with its deliberately optimistic settings is named as the gate's fallback cross-check, and nothing limits how screen H* values may shape gate design. A4 relies on I_mpc_exact, which the timing rule can drop if item 2 is not adopted.

**Change.** §17: any cross-check uses a separately pre-registered neutral CTM configuration. Screen H* values may not inform gate choices outside the R-PS bindings, and any such use is disclosed. A4: if I_mpc_exact stays optional, give fallback wording for when it is excluded.

## 35. [minor] §13 Compute and build l.431-461 [PS-15]

**Defect.** The budgets are not measured. The one measured analogue (ledger row metanet_capacity_grid) implies roughly 0.24-0.37 CPU-s per day-run, against the table's 0.036-0.072 s (a reviewer inference). The LP-OC and J_LB times are mutually inconsistent by about 10x. The LP-MPC solve time has no basis (Delta t is unspecified, and venv314 has scipy 1.18.1 without highspy). The mandatory I_mpc has no slow-path rule. D1's LP-trajectory test needs the LP builder scheduled for D4. The protocol-phase estimate ignores this fix list.

**Change.** Measure per-day-run CTM cost and per-solve LP time on the throw-away day before stating budgets, following the CLAUDE.md resource and thermal rules. Give the grid sizes and the resulting day-run count, including the oracle sweeps, extra splits and new branches from items 2, 7, 13, 18, 26 and 27. Specify the LP Delta t. Add a data-free slow-path rule for I_mpc (e.g. coarsen Delta t to 60 s if the projection exceeds 24 h wall; otherwise INVALID per item 2). Move the LP-trajectory test to D4. Re-estimate the protocol phase.

## 36. [minor] §3 Numerics l.176; §8 J l.313-316 [PS-16, PS-17 (c)]

**Defect.** The T ladder includes 8 s, which divides neither the 60-s control period nor the 300-s input bin. The rule depends on v_f from F6, so it is not fully data-free. J does not say how a run not drained by 01:00 is censored, what 'vehicles entering' counts, or how vehicles present at 05:00 are counted.

**Change.** Use a T ladder of divisors of 60 s (e.g. {10, 6, 5, 4, 3} s) and call it 'fixed before data except v_f from F6'. Apply §8's censoring rule to any run that is not empty at 01:00. Set the denominator to origin arrivals 05:00-23:00, and state how vehicles present at 05:00 are counted.
