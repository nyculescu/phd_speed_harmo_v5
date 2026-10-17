# Confirmatory protocol #1: result (VALID-ONLY)

Draft for author approval (2026-10-16). It becomes final with decision V85, together with the two open items in §7.

## 1. Outcome and provenance

- **Outcome:** **VALID-ONLY**, the pre-registered result.
- **Run:**
  - protocol `confirmatory_1.md` (V84, sha256 `ac721bb5…`), run once on 2026-10-16;
  - code: the reviewed commit `47e7410`;
  - seeds 7,420,200 (bootstrap) and 7,420,201–220 (placebo);
  - measured: 43 s wall clock, 2.4 GB.
- **Data checks:** the row counts match the metadata. The re-fetched L1 probe matched MD5 `a9f2f0c1…`, so its sensitivity row ran.
- **Gating:** Stage 1 gated J = 2 cells, both on I-90/I-94 Moving. The Stage-1 power (≈ 1.0) is the chance that a well-calibrated threshold passes A1. It is not power for a win.

**Checks after the run** (scripts in the session scratchpad `wf7/`):
1. **Rule re-derivation:** every gating, validity, beats, win and harm flag, and the outcome of all 4 rows, re-derived from the stored numbers and the protocol text. 0 mismatches.
2. **Recomputation of both gated cells** from the raw CSVs by separate code: counts and miss shares identical, E within 7e-15. It reused the run's leader matching (`screen1b.leaders`), so that part was not checked independently.
3. **Re-run of the committed code:** all 7 cells reproduced.

## 2. Operating map (all cells; protocol §1 "always reported")

**Columns:**
- miss share / A1 bound, in %; a cell is A1-valid if its bound is ≤ 7.5 %;
- mean required gap, in m, for each of F, W, O, H and P;
- E, in %; negative means O used longer gaps.

Brackets are Bonferroni intervals (two-sided 1 − 0.05/J, J = 2). In report-only rows they are descriptive only. n = comparison windows; G = two-minute blocks.

| Cell | Status | n (G) | F | W | O | H | P | gap F/W/O/H/P | E(O,F) | E(O,W) |
|---|---|---|---|---|---|---|---|---|---|---|
| Moving R1 | gated | 5,673 (14) | 2.80/3.73 | 3.65/4.80 | 2.75/3.72 | 3.97/5.28 | 3.38/4.46 | 2.83/2.78/2.98/2.76/2.81 | −5.3 [−11.7, 1.1] | −7.4 [−14.1, −0.7] |
| Moving R2 | gated | 9,424 (15) | 7.21/8.45 | 6.73/7.93 | 4.05/4.96 | 3.99/5.05 | 4.17/5.17 | 3.05/3.08/3.83/3.37/3.38 | −25.6 [−39.4, −11.8] | −24.5 [−38.2, −10.8] |
| L1 R1 | report-only | 515 (3) | 1.36/4.95 | 0.00/0.58 | 1.55/6.85 | 3.69/12.10 | 0.47/1.43 | 2.82/3.19/2.99/2.70/2.91 | −6.1 | 6.2 |
| L1 R2 | report-only | 1,795 (5) | 3.45/4.76 | 2.62/4.00 | 3.18/5.72 | 3.90/5.22 | 3.47/4.82 | 3.05/3.15/3.13/3.00/3.06 | −2.5 | 0.6 |
| L1 R3 | report-only | 5,473 (22) | 10.18/12.88 | 4.79/6.63 | 3.82/4.97 | 3.96/5.50 | 4.27/5.61 | 3.30/4.97/10.79/5.25/5.75 | −227 | −117 |
| L2 R3 | report-only | 347 (8) | 7.20/13.04 | 6.34/12.38 | 5.19/9.92 | 3.46/7.45 | 5.26/9.98 | 3.30/3.50/4.22/4.09/3.75 | −28 | −21 |
| Moving R3 | report-only | 2,280 (12) | 15.61/19.49 | 9.47/13.03 | 4.12/5.65 | 3.95/6.25 | 5.02/7.61 | 3.30/3.95/9.43/9.63/7.71 | −186 | −139 |

**Notes to the table:**
- **O on all windows** (A1 needs it too): Moving R1 3.31/4.54; R2 4.04/4.90.
- **The P bound** is from the bootstrap only.
- **Headroom:** E(H,F) / E(H,W) = 2.62 % / 0.69 % in Moving R1 and −10.41 % / −9.44 % in Moving R2. The O-of-H headroom share is undefined in both: F is not A1-valid in R2, and E(H,F) < 3 % in R1.
- **Arms:**
  - F = the margin transferred from the fitting sets, pooled (R1 1.35, R2 1.50 m/s²);
  - W = fitted on the first 300 windows, then frozen;
  - O = the online margin;
  - H = the hindsight constant;
  - P = the shuffled placebo.
- **Source:** `confirm_1_result.json`.

## 3. The pre-registered sentence

The thesis sentence, using the §6.4 wording with its required clauses:

> "In open-loop replay behind recorded leaders, on recordings of the I-90/I-94 freeway made on another day than its fitting recording (same segment [VERIFY]; collection mode differs, which set used which [VERIFY]), the self-calibrating margin was **valid in every gated regime; no win was shown.** A miss means the leader braked harder than the assumed limit; it is not a crash. Harm not excluded: Moving R1. Floor-bound: none. Report-only: I-294 L1 R1, R2, R3; I-294 L2 R3; Moving R3."

- **No "clearly more wasteful" clause applies.**
- **Moving R1, "harm not excluded":** E(O,W) = −7.39 %, uncorrected 95 % CI [−13.09, −1.70] %.
- **Moving R2:** the harm rule needs an A1-valid comparator. F and W both fail A1 there, so **harm was not assessed**. O's gaps were 25.6 % (vs F) and 24.5 % (vs W) longer, and both Bonferroni intervals lie wholly below −10 %.
- **What is excluded:** no closed-loop, collision, guarantee or DRL claim (§1, V83). No paper comes from this run (§6).

## 4. What was not testable: the "new road" claim

**No I-294 L1 cell met the gate.** The gate is R1 or R2, at least 1,000 comparison windows in at least 10 two-minute blocks, and a clip share of 5 % or less.
- L1 R1 had 515 windows in 3 blocks.
- L1 R2 had 1,795 windows in 5 blocks.
- L1 R3 is report-only by regime.

**Why**, computed after the run from the raw L1 CSV with the committed window code:
- L1 has 10 runs of 150–460 s.
- Run 8 (5.0–465.0 s) holds all 900 R1 windows and 2,043 of the 2,140 R2 windows. The other runs flow freely, with median speeds of 15–29 m/s.
- A 460-s run holds at most 4 blocks.

So the "new road" sentence was never reachable. The protocol's power section assumed 10–40 blocks per cell, and **we did not check how congestion was spread across runs before fixing the gate.** That is a planning lesson.

The protocol forbids adding cells afterwards (§6.1), and no unread TGSIM freeway set remains.

## 5. Descriptive observations (no claims)

- **Moving R2, the transferred margins.** F and W miss 7.21 % and 6.73 %, below the 7.5 % limit. They fail A1 only through their bounds, so they are not clearly invalid. **The screens' "fixed margins do not transfer" is therefore not confirmed here.** It stays a screen observation, not a thesis claim.
- **Headroom.** In R1 the best constant threshold in hindsight (H) was 2.6 % shorter than F and 0.7 % shorter than W, below the 3 % beats margin. H bounds constant thresholds only.
- **Why O's validity is weak evidence.** At these cell sizes, the tracker's update identity bounds O's miss share at about 4.6 % (R1) and 4.5 % (R2), given its observed q range (checked post hoc). A1 for O therefore mostly tested the width of the bounds.
- **O versus the others.** In both gated cells O had the longest mean gap of the five arms. Its longest miss run in R1 was 19 windows; F, W and H each had 8.
  - Per run: in each of Moving's 4 runs, E(O,F) and E(O,W) are negative. The value closest to zero is E(O,F) = −1.18 % in R1, run 3. These per-run values were computed post hoc and are not in the result file.
- **The R3 cells, all arms.**
  - L1 R3: F 10.18 % (A1-invalid), W 4.79 % (A1-valid, gap 4.97 m), O 3.82 % (gap 10.79 m; clearly worse than W under the §5 rule), H gap 5.25 m.
  - Moving R3: F and W both A1-invalid, O 4.12 % with gap 9.43 m, H gap 9.63 m.
  - L2 R3: no arm except H was A1-valid; O was not A1-valid either.
- **Placebo** (the secondary claim was not tested): E(O,P) = −6.05 % (R1) and −13.36 % (R2).
- **Report rows** (labels and gated numbers almost unchanged):
  - floor 0: VALID-ONLY, E(O,F) −5.8 % / −25.8 %;
  - test vehicles scored: VALID-ONLY, E(O,F) −5.2 % / −24.0 %;
  - probe vehicles dropped: VALID-ONLY, identical to main;
  - W with N = 1,000: E(O,W1000) = −1.99 % [−7.12, 3.13] in R1 and −27.09 % [−40.19, −13.99] in R2.
- **Single-site F** (m/s²): I-395 R1 1.00 and R2 1.00 (floor); Stationary R1 1.36 and R2 1.82.
- **Leader matching and exclusions:** matched-leader share L1 0.86, L2 0.77, Moving 0.96. Test windows excluded: L1 664, L2 30, Moving 153.
- **Scope of the gated evidence:** I-90/I-94 Moving only, one day, one direction, 4 runs, 1,507 s.

## 6. Reading for the thesis

- **What this line gives:** one validity paragraph for a thesis chapter, and no paper.
- **The question it was built for stays open:** whether a self-calibrating margin helps on a new road. TGSIM can no longer answer it.
- **What the gated data actually show:** on the same freeway on another day, the online margin was valid but used longer gaps than every alternative. The transferred margin failed only by its confidence bound, not by a gross error.
- **Open question, formed after seeing report-only cells (not a finding):** does recalibration help where a transferred margin is badly wrong? In the one well-populated new-road cell (L1 R3), F was badly wrong, but the simple freeze rival W fixed it with half of O's gap. That points against O.
- **Something to reconcile:** CLAUDE.md still states the D5.8 bar, which V83 replaced for this line.

## 7. Open author items and options

**Open items for V85:**
- **(i) Scope of the result lists.** The run named "harm not excluded" and "clearly worse" for gated cells only. The literal per-cell reading would add L1 R1 and R2 (harm not excluded) and L1 R3 (clearly worse than W). The outcome label is the same either way. **Default:** keep the gated lists in the sentence, and disclose the per-cell flags as report-only (done in §5).
- **(ii) d_safe grid end.** The run's 0.01-s grid runs to the batch's latest ego stop, not to each window's own stop. Measured effect: mean gaps change by at most 1.5e-8 m, single gaps by at most 1.7e-5 m, and E by at most 4.8e-9. **Default:** not a §7 bug, because both are 0.01-s grids that cover the ego's stop. **Alternative:** treat it as a bug: fix it, add a failing test, re-run with the same seeds (about 1 min); the corrected run decides, and both runs are reported. The label stays provisional until this is settled.

**Options for the next step:**
1. **Close out:** V85 and the ledger entry.
   - Cost: author 0.5 h; Claude 1 h, or 2 h with the re-run; compute 1 min or none.
2. **Thesis-level decision**, with the academic supervisor: where the positive result comes from, and which claim bar applies.
   - Cost: author 1–2 h; Claude 0.5–1 h for a one-page status; no compute.
3. **A new screen, then a confirmatory protocol,** for a redesigned algorithm on genuinely unread data (not TGSIM, not NGSIM I-80/US-101).
   - Cost: author several hours, plus waiting for data access [VERIFY]; Claude 1–2 days; compute under 1 h per stage.
   - Conditions: protocol and seeds approved before data, and this run's influence disclosed.
   - Risk: high.

**Not allowed:** re-gating L1, re-scoring TGSIM, tuning on it, or writing a paper from this run.

**Recommendation:** option 1 now, option 2 in parallel. Option 3 only if option 2 decides that line #1 deserves fresh data.
