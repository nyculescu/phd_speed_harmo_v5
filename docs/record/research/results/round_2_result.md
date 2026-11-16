# Round 2: result

**Outcome.** No round-2 candidate replaces v3w.
- **Validation:** none of the 5 trained candidates (2B, 1B, 1D, ahead, rep) was shown better than v3w. tail and sw advanced, each in one cell by path (a), and became the two finalists.
- **T1 (Q1):** on the test, used once, neither finalist was shown better than v3w in either cell, and neither was harmed. v3w stays the incumbent, and Q1 ends null on 7 candidates.
- **T2 (Q1, Q2), at 99.17 % (Bonferroni, m = 6):**
  - **X1, won:** v3w, tail and sw each win 5 of 5 against the counting rules p333, os0_10_10 and 3E-T.
    - 3E-T is "a rule tuned by CMA-ES under the training slowdowns, not for this cell". Its search ran 40 of 100 generations, unchecked for convergence (§7).
    - The per-cell CMA-ES rule 3E-X1 did not meet the delay filter; its search was still falling at generation 40, and its pick is from generation 3. So in X1, Q1 and Q2 against it read "not answered against the CMA-ES rule: not within the delay filter".
    - X1 does not close under D10. It had closed under confirmatory 3's [A3] (V395) before rounds 1 and 2 re-tested it; this is its third test on plant_c3.
  - **X2, not won:** fewer than 4 of 5 policies cleared the 10 % close-following margin against 3E-T and 3E-X2: tail 3, v3w 2, sw 0.
    - 3E-X2 is "a rule tuned by CMA-ES for this cell on separate seeds". Its search was still falling at generation 40 (last-10 median loss −30.9 against −26.0), so it is a lower bound on its family.
    - By point estimate (arm level), every policy arm has fewer close-following seconds and less delay than both rules. Against 3E-X2 the delay CIs include 0 at T2's level (§4).
    - **The DRL claim against tuned rules closes in X2 on this plant, under D10's T2 reading.**
      - The author decided that reading after the test data were known (V466).
      - At T2's 99.17 % level X2 closes under either reading. tail's delay win is 3 of 5 there, and 4 of 5 at confirmatory 3's 97.5 %.
      - The closing rests on 3E-T counting at −1.81 %, 0.19 points inside the delay filter.
- **Against no control:**
  - **X1:** v3w, tail and sw each have more close-following than no control (15-18 % more, 95 % CIs below 0), at 27-28 % less delay. baseline-v3 has 29 % more. Every rule has 43-122 % more, at 17-24 % less delay.
  - **X2:** the close-following of v3w, tail and sw is not shown to differ from no control's, at about 23 % less delay. Every rule has 12-70 % more close-following than no control (95 % CIs below 0), at 13-22 % less delay; 3E-X2 has 12.0 % more [1.4, 22.4] at 20.4 % less delay.
- **Band (Q3):** report-only, with no "shown" verdict (§5).

```
validation, 40 seeds ──────────────► test, 40 seeds, used once ─────────────────────────► band, 20 seeds
2B 1B 1D ahead rep   not shown better T1  tail, sw: shown better than v3w in neither cell     report-only
tail  advances (X2, path a)          T2   X1 won: v3w 5/5, tail 5/5, sw 5/5 (p333, os0_10_10, 3E-T)
sw    advances (X1, path a)               X2 not won: tail 3/5, v3w 2/5, sw 0/5 (margin vs 3E-T, 3E-X2)
finalists: tail, sw                  D10  incumbent v3w; X2 closes (T2 reading, V466); X1 does not (closed by [A3] in V395)
```

## 1. Provenance

- **Protocol:** `docs/research/protocols/round_2.md` revision 2 (V453), approved with D1-D13 and seeds in V454 (D6 changed to the laptop). Built and reviewed in V455.
- **Run commit:** `6c49e7e` on `r2/eval`. Each trained candidate ran from a frozen `git archive` copy of its own branch: 2B `5f9f5d3`, 1B `5c10e6f`, 1D `e8107fc`, ahead `66fa146`, rep `08786f1`. Every rows file's name matches its copy's COMMIT file and the Arms table.
- **Machines (disclosed deviations from V454's laptop, D6):**
  - **3E-X searches:** rented instance 59611488, 11:59-16:53 MST (18:59-23:53 UTC), from run commit `6c49e7e` (V461). The fetch was verified by SHA-256, after a safe stop at 17:00 caused by locale-sorted checksum lists, and the instance was destroyed at 17:06.
    - Their meta.json records no commit, because the deploy had no `.git` or COMMIT file. The link to `6c49e7e` rests on check 1 on the picks, which the laptop reproduced exactly.
    - The laptop chain was frozen 11:49-17:06 MST. Its partial local searches are kept in `round2/local_partial_3ex`, unused.
  - **Validation:**
    - **Laptop, 17:06-19:31 MST:** 3,201 rows. These are 2B, 1B, 1D and ahead complete, plus one rep row.
    - **Rented instance 59653253, 19:36-20:14 MST (V464):** the other 3,999 rows. These are 799 rep rows and every evaluation-snapshot row: v3w, sw, tail, the rules and no control.
  - **Test and band:** the rented machine only, 20:15-21:04 MST.
  - The instance was destroyed at 21:15, after a fetch verified by SHA-256 (23 files).
  - **"One platform (V436): all arms of a phase run on one machine" was broken at validation** (V465).
    - The finalists' advances compare remote rows with remote rows.
    - The non-advance of 2B, 1B, 1D and ahead compares laptop candidate rows with remote v3w rows.
  - **Cross-machine evidence:**
    - check 1 on the 3E-X picks: the laptop reproduced the remote search rows (8 keys × 3 seeds × 2 cells);
    - the remote acceptance reproduced 4 stored rows at `6c49e7e`;
    - ahead's importance KILL re-ran 20 ahead runs on the remote from `66fa146`, and they matched the laptop's validation rows on every stored key;
    - the demand fingerprint (`finished_pct`) agrees at 40 of 40 seeds.
  - **Checks 2 and 4 did not run on the rented machine** at the candidate snapshots, which the protocol's "Operation" line asks for (V465).
    - On `r2/eval`, only the acceptance's 4 rows ran. Round 1's stored v3w rows X1|w0 and X2|w0 were not re-run there, although every v3w, sw and tail row was made there.
    - Nothing covers rep's 799 remote rows at `08786f1`. rep's effects are far from every path (§3).
- **The first remote start failed** before any job was written. The frozen copies resolve their commit with `git rev-parse`, and the rented machine has no repository.
  - A stand-in that answers only `rev-parse` from the copies' COMMIT files fixed it.
  - It was committed as `1367c84`, dated 69 s after the remote restart. The copy that ran and the remote job log were not fetched before the destroy, so which stand-in ran rests on that commit only (V465).
  - The failed start's logs are in `v5b1_runs/round2_evalremote/`.
- **The laptop's `chain.log`** ends at the 17:06 pick check. Its validation-step lines were lost when the unit was stopped at 19:31. The rows and job files are complete (V465).
- **Resume across machines** matched rows by (name, level, seed), without a config hash (V455's disclosure).
  - The 4 laptop files are byte-identical in the final set.
  - rep's laptop row is the byte prefix of its final file.
  - Every row's `cfg` equals its job's config: 12,400 final rows, plus the 3,201 laptop partial rows.
- **Seeds,** as approved:
  - 3E-X tuning: 7,440,740-779;
  - validation: 7,440,800-839;
  - test: 840-879, used once;
  - band: 880-899, used once.
  - No seed falls outside its block, and no row is duplicated (validation 7,200, test 2,800, band 2,400).
- **Data and tables:**
  - The raw rows are in `/home/catalin/work/phd/v5b1_runs/round2/` (`val/`, `test/`, `band/`).
  - The readings are in `validation.json`, `test_result.json` and `thesis_v459.json`, copied to `docs/research/round2/report/`.
  - The same folder holds `test_table.csv`, `band_table.csv`, `where_gain.json` and `report_extra.json`. They come from `docs/research/round2/report2.py` (`r2/eval` `e97a4f6`; `source.json` records its sha256), which reads stored rows only.
  - `test_table.csv` holds every arm's and rule's counters by road, speed and period (`ttc3_*`, `sev3_*`), with 95 % effects against no control, p333, os1_15_10, both 3E rules and every counting rule.
- **Independent check (ultracode):**
  - Four agents re-derived every reading from the raw rows with their own code, and five adversarial verifiers tried to refute each verdict. A completeness critic checked the result against the protocol.
  - Two more agents re-derived `report2.py`'s tables and reviewed its code, and three reviewers checked this text.
  - No verdict was refuted. Every point estimate matches, and every decisive CI matches the stored routine and the exact bootstrap law.
- **Sign convention:** effect = sign × median(P − O) / median(O) × 100 over paired seeds. Positive means P has **less** delay, close-following or braking, or **more** flow.

## 2. Build and checks

- **Checks 1-6** passed on the laptop at the run commit (`checks/PASSED` = `6c49e7e`, 11:48). Check 1 passed again on the 3E-X picks, on the laptop and on the rented machine.
- **Check 7 deviated from the protocol** (V455). It was a lean code review (one deep reviewer, ultracode off), not the adversarial ultracode review the protocol names. Its 1 blocker, 4 major and 9 minor findings were fixed before the run.
- **Smoke (check 5):**
  - tail's action differs from Greedy(u500) on 9,273 of 39,311 decisions (23.6 %, X2|t0).
  - ahead has 18 inputs. Its look-ahead inputs read 1.0 on 2.4 % and 2.3 % of decisions.
  - 1B drops 16,460 of 38,684 decisions (42.5 %), against 0.44 in training.
  - Traced rows equal untraced ones for every smoked arm.
- **3E-X picks** (D4; V461), against p333 on each phase's seeds, 95 % (positive = 3E-X better):

| Cell | Pick | TTC, tuning | Delay, tuning | TTC, validation | Delay, validation | TTC, test | Delay, test |
|---|---|---|---|---|---|---|---|
| X1 | g003i02 | +32.6 [+24.0, +37.7] | +1.0 [−2.2, +4.6] | +31.4 [+27.5, +35.0] | −2.2 [−6.6, +2.9] | +27.4 [+25.0, +33.9] | −2.3 [−5.7, +0.5] |
| X2 | g016i21 | +39.7 [+29.3, +44.1] | +1.6 [−1.2, +4.2] | +32.0 [+25.4, +35.2] | +2.1 [−2.4, +5.0] | +33.3 [+26.7, +41.6] | +1.5 [−0.1, +3.9] |

  - The drop from tuning to fresh seeds is the protocol's overfitting check.
    - 3E-X1 lost about 3 points of delay and failed the delay filter on both fresh seed sets.
    - 3E-X2 kept its delay and lost 6-8 points of close-following.
  - **Both searches were still falling at generation 40.** X1's median loss over the last 10 generations is −30.8, against −22.5 for the 10 before; its pick comes from generation 3. X2's is −30.9 against −26.0.
  - So each 3E-X is a lower bound on what a per-cell tuned rule of this family can do. This applies beside every 3E-X result below.

## 3. Validation (40 seeds, 95 % CIs, no correction)

Effects against the v3w arm (positive = candidate better). Each arm is the per-seed mean over 5 learners at their chosen checkpoints.

tail has no checkpoint choice. So at validation v3w, tail's comparator in the advance rule, carries the checkpoint rule's in-sample gain and tail does not, which works against tail. The rules have no checkpoints. On round 1's split-half rows that gain was about 0.2-0.3 points of delay and 0.8-1.5 points of close-following. The test, on fresh seeds, has no such bias.

| Candidate | Checkpoints | X1 delay | X1 TTC | X2 delay | X2 TTC | Verdict |
|---|---|---|---|---|---|---|
| 2B | u500 ×5 | −1.6 [−2.9, +1.0] | −0.8 [−5.8, +2.3] | +0.1 [−2.5, +1.2] | 0.0 [−3.0, +3.2] | not shown better |
| 1B | u250 ×2, u500 ×3 | −0.8 [−4.2, +1.0] | +0.2 [−5.1, +4.3] | −1.2 [−3.0, +0.2] | +0.3 [−4.4, +6.3] | not shown better |
| 1D | u250 ×1, u500 ×4 | +1.0 [−1.8, +2.9] | +4.4 [−0.1, +6.5] | +0.1 [−1.0, +1.7] | +2.2 [−0.2, +5.5] | not shown better |
| ahead | u250 ×3, u500 ×2 | −0.7 [−3.2, +0.3] | +1.5 [−1.4, +7.3] | −0.8 [−1.6, +0.6] | +7.3 [+2.4, +11.2] | not shown better (KILL not met) |
| rep | u250 ×3, u500 ×2 | −0.4 [−1.6, +1.0] | +0.2 [−3.1, +4.2] | +0.2 [−1.7, +1.7] | +2.5 [−0.5, +5.7] | not shown better |
| tail | none | −0.2 [−2.1, +1.3] | −3.2 [−7.2, +3.3] | **+1.4 [+0.5, +2.4]** | −2.9 [−5.9, +3.9] | advances: X2, path (a) |
| sw | u500 ×5 | **+2.1 [+0.4, +3.8]** | +2.0 [−1.1, +5.4] | +0.2 [−0.6, +1.4] | −5.5 [−9.2, −1.2] | advances: X1, path (a) |

- **v3w's checkpoints:** u250 for C0 and C2, u500 for C1, C3 and C4. They differ from round 1's for C1 and C2. All 70 learner-checkpoints were within 2 % of os1_15_10's delay in both cells, so every choice fell to the close-following tie-break.
- **No harm and no floor KILL.** Every u500 arm had 36.9-48.4 % fewer TTC seconds than p333, and 22-29 % less delay than no control.
- **ahead's KILL** (V444): the median permutation importance over the 5 learners is 0.220 for input [16] and 0.171 for [17], both above 0.02, so ahead stays in.
  - importance2 writes a reading only when the traced re-runs equal the untraced rows, and an error otherwise.
  - The traced rows are not stored.
- **Harm is looser than round 1's on delay.** A clear delay loss under 2 % is allowed. No candidate had one at validation (every delay CI reaches above 0), so this changed no advance.
- **Harm on close-following is new.** sw's X2 close-following is clearly worse than v3w's (−5.5 [−9.2, −1.2]). It is not harm, because harm needs a point estimate worse than −10.
- **Counting** (delay at most 2 % above p333, point, validation rows):
  - X1: p333, os0_10_10 (−0.8), 3E-T (−0.9). Excluded: 3E-X1 (−2.2; search not converged), z33133 (−2.3), lr400_13_2 (−2.6).
  - X2: p333, os1_15_10 (−1.9), 3E-X2 (+2.1; search not converged). Excluded: 3E-T (−3.4), lr1000_16_2 (−2.9), r4a1 (−7.0), a4400_10_1 (−8.3).
- **Ranking:** learners passing the tuned reading at 95 %, summed over the cells.
  - The 5 trained candidates got 10 each but did not advance.
  - tail got 9 (one X2 policy blocked by 3E-X2) and sw got 7 (three X2 policies blocked by 3E-X2).
  - Both advancing candidates became finalists (D3 allows 2), so m(T1) = 4 and m(T2) = 6.
- **Selection:** 7 candidates × 2 cells were tested at 95 % with no correction. Under no difference, at least one of the 14 tests passes up to about 30 % of the time; here 2 passed. Advancing is a selection step, not a finding.
- **v3w at round 1's checkpoints** (report-only, validation rows, T2's level): X1 4 of 5, won; X2 2 of 5, not won.
- **Against no control** (validation, 95 %, at the chosen checkpoints), each u500 arm has 22-29 % less delay (above). The tested arms at test are in §6.

## 4. Test, used once (X1 and X2 at 5,300 veh/h, 40 seeds)

**Cells** (as round 1):
- X1 has two tapered slowdowns to 25 km/h for 120 s on edge 4, at 600 and 1,200 s.
- X2 has one tapered slowdown to 30 km/h for 180 s on edge 3 (between the merges), at 700 s.

**Counting** (test rows, delay against p333, point):

| Cell | Counting | Excluded |
|---|---|---|
| X1 | p333; os0_10_10 −1.4; 3E-T −0.9 | 3E-X1 −2.3 (search not converged); z33133 −3.3; lr400_13_2 −4.3 |
| X2 | p333; lr1000_16_2 −1.4; os1_15_10 −1.8; 3E-T −1.8; 3E-X2 +1.5 (search not converged) | r4a1 −4.0; a4400_10_1 −7.3 |

- **3E-T in X2:** it counts at −1.81, 0.19 points inside the filter, after it was excluded at validation (−3.4 [−5.3, −1.6]).
  - The protocol's noise-floor disclosure applies: the counting filter can flip near 2 %.
  - Under the protocol's statistic (median of paired differences), leaving out any one seed moves the point only between −1.86 and −1.76, so the counting decision flips for 0 of 40 seeds.
- **Each 3E rule against p333 and os1_15_10** (95 %, positive = 3E better):

| Phase | Cell | Rule | Counts | Delay vs p333 | TTC vs p333 | Delay vs os1_15_10 | TTC vs os1_15_10 |
|---|---|---|---|---|---|---|---|
| validation | X1 | 3E-T | yes | −0.9 [−4.1, +1.7] | +36.2 [+30.5, +42.4] | +1.4 [−1.8, +6.0] | +18.7 [+14.9, +24.7] |
| validation | X1 | 3E-X1 | no | −2.2 [−6.6, +2.9] | +31.4 [+27.5, +35.0] | −1.2 [−3.9, +5.3] | +10.9 [+1.4, +18.2] |
| validation | X2 | 3E-T | no | −3.4 [−5.3, −1.6] | +36.4 [+28.5, +44.5] | −1.6 [−4.7, +2.2] | +18.6 [+14.5, +27.4] |
| validation | X2 | 3E-X2 | yes | +2.1 [−2.4, +5.0] | +32.0 [+25.4, +35.2] | +3.6 [+0.8, +5.1] | +12.7 [+7.4, +21.1] |
| test | X1 | 3E-T | yes | −0.9 [−5.7, +2.4] | +32.0 [+29.3, +38.1] | 0.0 [−5.9, +5.0] | +16.6 [+9.9, +21.7] |
| test | X1 | 3E-X1 | no | −2.3 [−5.7, +0.5] | +27.4 [+25.0, +33.9] | +1.2 [−2.7, +4.5] | +7.8 [+4.3, +13.1] |
| test | X2 | 3E-T | yes | −1.8 [−5.8, +0.5] | +32.0 [+22.4, +41.7] | −1.5 [−4.6, +4.0] | +20.2 [+12.9, +26.5] |
| test | X2 | 3E-X2 | yes | +1.5 [−0.1, +3.9] | +33.3 [+26.7, +41.6] | +3.0 [+1.1, +5.8] | +16.8 [+11.9, +23.1] |

  - **Against the counting forms** (test, 95 %; all forms in `test_result.json` `e3_status.vs_forms`):
    - X1, against os0_10_10: 3E-T delay +0.2 [−9.7, +4.1], TTC +16.3 [+7.6, +20.2]; 3E-X1 delay −2.7 [−6.6, +2.0], TTC +10.0 [+4.5, +13.5].
    - X2, against lr1000_16_2: 3E-T delay −2.3 [−5.4, +2.0], TTC +15.0 [+10.3, +26.2]; 3E-X2 delay +1.2 [−1.3, +5.0], TTC +21.9 [+9.5, +27.6].
  - On the test rows, each 3E rule has 4-13 % less braking at 3 m/s² than p333 and os1_15_10. Flow is within ±0.5 % of p333's. Moving full-emergency events are at most 9 per 40 runs for any of these rules, and there are no collisions. Braking at 7 m/s² is in `report_extra.json` (`e3_side`); for example, 3E-T in X2 has +33.0 [+19.1, +40.4] against p333.

**Reading T1** (Q1, against v3w, 98.75 %: percentiles 0.625 and 99.375):

| Finalist | Cell | Delay | TTC seconds | Verdict |
|---|---|---|---|---|
| tail | X1 | +0.9 [−0.8, +3.1] | +1.0 [−4.5, +3.3] | not shown better |
| tail | X2 | −0.4 [−3.4, +2.0] | −1.8 [−5.2, +5.0] | not shown better |
| sw | X1 | −0.1 [−2.7, +1.7] | −0.9 [−3.5, +1.6] | not shown better |
| sw | X2 | −0.5 [−3.0, +1.8] | −5.8 [−10.5, +0.1] | not shown better; not harm at 95 % (−5.8 [−9.4, −1.7], point above −10) |

Against no control (test, 95 %; delay, TTC):
- X1: tail +27.9, −15.3; sw +27.9, −18.4; v3w +27.3, −16.6.
- X2: tail +23.5, +1.4; sw +23.1, −6.7; v3w +23.5, −0.9.

The CIs are in §6.

**Reading T2** (confirmatory 3's tuned reading, 99.17 %: percentiles 0.417 and 99.583). No control: X1 1,493 TTC seconds and 322,813 vehicle-seconds of delay per run; X2 1,580 and 287,340.

| Arm | X1 | X2 | X2: why policies fail |
|---|---|---|---|
| v3w | **won, 5 of 5** | not won, 2 of 5 | w1: 3E-T margin 8.1; 3E-X2 margin and CI. w2: 3E-T margin 9.96 and CI; 3E-X2 margin and CI. w4: 3E-T CI; 3E-X2 margin and CI |
| tail | **won, 5 of 5** | not won, 3 of 5 | t0: 3E-T and 3E-X2, margin and CI. t4: 3E-T margin 8.4 |
| sw | **won, 5 of 5** | not won, 0 of 5 | s0, s2: both rules, margin and CI. s1: 3E-T margin 9.59. s3: 3E-X2 margin 9.70. s4: 3E-T margin, CI and 20-s per-run limit; 3E-X2 margin and CI |
| baseline-v3 (report-only) | won, 4 of 5 | not won, 2 of 5 | d0: both, margin and CI. d1: 3E-T margin 9.9. d2: both, margin, CI and per run |

- **No grid rule blocks any policy in either cell.** T2 without the 3E rules (old grid only, a comparison with round 1) is 5 of 5 for v3w, tail and sw in both cells.
- **Margin over the strongest counting rule**, per policy (point estimates; the stored intervals are at 97.5 %):
  - X1, against 3E-T: v3w 16.3-24.2 %, tail 15.7-24.9 %, sw 14.7-25.2 %.
  - X2, against 3E-X2: v3w 7.5-14.1 %, tail 8.3-15.7 %, sw 2.0-11.5 %.
  - X2, against 3E-T: v3w 8.1-18.4 %, tail 8.4-16.4 %, sw −0.7-14.3 %.
  - Against 3E-X2, 8 of the 15 policies are below the 10 % margin, 7 of them with a CI that does not exclude 0 at T2's 99.17 % (5 at the stored 97.5 %).
  - In X2 the strongest counting rule is 3E-X2, nearly tied with 3E-T: medians of 1,732 and 1,736.5 TTC seconds.
- **The arms against the 3E rules** (arm level, 95 %, positive = arm better):
  - X2, against 3E-X2: TTC v3w +12.3 [+5.0, +18.7], tail +14.1 [+6.2, +16.8], sw +7.2 [−0.0, +11.7]. Delay +3.0, +2.7 and +3.1.
  - X2, against 3E-T: TTC +11.5, +10.7 and +5.7; delay +7.5, +7.2 and +7.6.
  - X1, against the non-counting 3E-X1: TTC v3w +26.2 [+22.9, +28.9], tail +25.4, sw +24.1; delay +7.8, +8.7 and +8.0.
  - At T2's level (99.17 %), against 3E-X2: TTC v3w +12.3 [+2.5, +19.8], tail +14.1 [+3.0, +18.8], sw +7.2 [−1.6, +14.4]; delay +3.0 [−0.1, +6.4], +2.7 [−0.7, +7.2] and +3.1 [−1.4, +7.2], not shown to differ.
  - At T2's level, against 3E-T: TTC +11.5 [+5.1, +18.4], +10.7 [+4.5, +19.8], +5.7 [−2.2, +19.7]; delay +7.5 [+5.0, +10.0], +7.2 [+3.7, +12.2], +7.6 [+3.8, +10.7].
  - X2 is "not won" because fewer than 4 of 5 policies cleared the 10 % margin with its CI. By point estimate, each arm has fewer close-following seconds and less delay than both rules. One policy, sw s4, has 0.7 % more close-following seconds than 3E-T.
  - The figures against 3E-X1 are not a win against it: it did not meet the delay filter, so Q1 and Q2 are not answered against it.
- **Non-inferiority on delay** (report-only, D11): the worst end of T2's corrected delay CI (its lower bound here) is above −5 % for every policy against every counting opponent in both cells. The minimum is −4.0, for sw s4 against 3E-X2.
- **Round 1's T2 beside it** (Q2; `round_1_result.md`, at 97.5 %, m = 2): X1 won 5 of 5 against p333 only; X2 won 5 of 5 against p333 and os1_15_10.
  - **X2 is reported as not won in round 2, with round 1's win beside it.**
  - Per D10, this round's T2 replaces round 1's for any thesis sentence, so round 1's X2 win can no longer support one.

**Reported beside (confirmatory 3's readings at its 97.5 % level; the severe check at T2's level).**

At T2's 99.17 %, which feeds every sentence (V467), replication is 5 of 5 everywhere. The other changes are:
- tail's X2 delay win drops to 3 of 5;
- tail's and sw's policies clearly worse than no control in X1 drop to 4 of 5;
- everything else is unchanged.

| Reading | X1 v3w / tail / sw | X2 v3w / tail / sw |
|---|---|---|
| Replication against p333 (TTC ≥ 30 % better) | 5 / 5 / 5 of 5 | 5 / 5 / 5 of 5 |
| Delay win (≥ 5 % less delay than the lower-delay of p333 and the delay opponent on the test rows: X1 p333, against delay opponent lr1000_10_1; X2 os1_10_0) | 2 / 3 / 0 of 5 | 2 / 4 / 2 of 5 |
| Severe-conflict check ("safety" wording) | met / met / met | 2 / 3 / 0 of 5: not met |
| Policies clearly worse than no control on TTC | 3 / 5 / 5 of 5 | 0 / 0 / 0 of 5 |
| No control's extra delay against the policies | 38.7 / 42.0 / 37.7 % | 31.4 / 31.2 / 29.5 % |

- **tail's X2 delay win** is 4 of 5 at 97.5 % and 3 of 5 at T2's 99.17 %.
  - Policy t2's point, 5.16, passes at both levels. What moves it is its CI's lower bound: +0.80 at 97.5 % and −0.38 at 99.17 %.
  - The author ruled that this route does not count toward D10's closing (V466).

### Sentences allowed (confirmatory 3's table and round 2's additions, filled from T2)

Model: an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds.
- Collisions are too rare to compare: 4 single events over all test arms.
- No map cells were run in this round, so cells other than X1 and X2 at 5,300 are not shown to be unharmed.
- **Cells' history:** this is X1's third test and X2's fourth on plant_c3, each on fresh seeds.
  - Confirmatory 3 won X2 by the tuned reading and closed X1 by its rule [A3] (V395).
  - X2 did not replicate on 20 fresh seeds (V401).
  - Round 1 won T2 in both cells (V449). Round 1's protocol did not state that [A3] had closed X1.
  - "Does not close" in this report is D10's rule for this round only.
  - X2 did not replicate in confirmatory 3b: 1 of 5 policies cleared (V401).
  - Earlier r2m3 plants tested both cells too (V359, V368).

**X1, v3w (Q2):** Under two tapered slowdowns to 25 km/h for 120 s on edge 4 (X1), 5 of 5 per-CAV PPO headway policies (v3w) had fewer seconds at TTC below 3 s than each of the 3 counting rules:
- p333, which is fixed;
- os0_10_10, tuned on separate seeds;
- 3E-T, a rule tuned by CMA-ES under the training slowdowns, not for this cell.

Over the 5 policies the margin was 16.3-24.2 % against the counting rule with the lowest TTC (3E-T), with delay and flow within the stated limits. This is a surrogate.
- **3E-T's tuning** ran 40 of 100 pre-registered generations (V443), with convergence unchecked. Its 5 shortlisted configurations were ranked by losses from different seed windows, and all 5 came from 2 of the 5 windows. So 3E-T is a lower bound on what its rule family can do, and in X1 it was not tuned for the cell at all.
- *Where the gain is* (v3w's arm against 3E-T; median paired difference in TTC samples per run, 40 seeds, 95 % CI; medians do not add up):
  - **Total:** 457 [354, 516].
  - **Roads:** edge 3 (between the merges) is the largest, 253 [206, 273]. Ramp 2 adds 107 [77, 172] and edge 4a 80 [40, 149].
  - **Speeds:** 10 m/s or more 205 [177, 218], and 5-10 m/s 196 [163, 234]. Below 5 m/s: 48 [13, 105].
  - **Time:** after each slowdown 141 [123, 162], during the hold 104 [62, 128], and in "rest" 158 [93, 222].
  - tail's and sw's totals are 412 [327, 580] and 460 [345, 552]. Edge 3 is the largest road for both, and the after and rest periods carry most of the gain (`where_gain.json`).
- **The CMA-ES-tuned rule 3E-X1 did not meet the delay filter in X1.** 3E-X1 is "a rule tuned by CMA-ES for this cell on separate seeds"; its search was still falling at generation 40, and its pick is from generation 3.
  - Against p333: 2.3 % more delay (95 % CI from 0.5 % less to 5.7 % more) and 27.4 % fewer close-following seconds (95 % CI 25.0 to 33.9 %).
  - Against os1_15_10: 1.2 % less delay (95 % CI from 2.7 % more to 4.5 % less) and 7.8 % fewer close-following seconds (95 % CI 4.3 to 13.1 % fewer).
  - **Q1 and Q2 against 3E-X1: not answered against the CMA-ES rule: not within the delay filter.**
- **No control:** medians per run of 1,493 TTC seconds, 322,813 vehicle-seconds of delay and 3,177 vehicle-seconds of braking at 3 m/s².
  - **The v3w arm has more close-following seconds than no control:** 16.6 % more (95 % CI 8.4 to 25.1 % more).
  - No control pays 38.7 % more delay (median over the 5 policies; 38.2 % at arm level).
  - Confirmatory 3's 4-of-5 clause is not triggered for v3w: 3 of 5 policies are clearly worse at its 97.5 % level and at T2's, and 4 of 5 at 95 %, where w2's upper bound is −0.03. So the arm-level result is stated here instead.

**X1, tail:** the same sentence, naming the arm "the averaged action probabilities of 6 checkpoints of each PPO run": 5 of 5, 15.7-24.9 % against 3E-T. **No control had fewer such seconds, at 42.0 % more delay** (median over policies; 5 of 5 policies clearly worse at 97.5 %, 4 of 5 at T2's 99.17 %).

**X1, sw:** the same sentence, naming the arm "a hybrid: 0.8 s and os1_15_10 before 594.72 m, the PPO policy after" (never "per-CAV PPO headway policies"): 5 of 5, 14.7-25.2 % against 3E-T. **No control had fewer such seconds, at 37.7 % more delay** (median over policies; 5 of 5 clearly worse at 97.5 %, 4 of 5 at 99.17 %).

**X2, every arm:** "Won against confirmatory 3's grid, not against the CMA-ES rules 3E-T (a rule tuned by CMA-ES under the training slowdowns, not for this cell) and 3E-X2 (a rule tuned by CMA-ES for this cell on separate seeds; its search was still falling at generation 40)."
- **Limits missed:**
  - v3w (2 of 5): the 10 % close-following margin, and its CI;
  - tail (3 of 5): the margin, and its CI;
  - sw (0 of 5): the margin, its CI and the 20-s per-run limit.
- No sentence says X2 was won. The severe check is not met, so the word "safety" is not used in X2.
- **Replication yes, tuned no:** "The edge over the fixed 0.8 s rule held on the fixed plant (5 of 5 policies at least 30 % better than p333 in every arm, at T2's 99.17 %), but fewer than 4 of 5 policies cleared the margins against 3E-T and 3E-X2 (v3w 2, tail 3, sw 0).
  - Close-following margin per policy (point): against 3E-X2, v3w 7.5-14.1 %, tail 8.3-15.7 %, sw 2.0-11.5 %; against 3E-T, v3w 8.1-18.4 %, tail 8.4-16.4 %, sw −0.7-14.3 %.
  - Delay, arm level at T2's 99.17 %: against 3E-X2, v3w +3.0 [−0.1, +6.4], tail +2.7 [−0.7, +7.2], sw +3.1 [−1.4, +7.2] %, not shown to differ; against 3E-T, +7.5 [+5.0, +10.0], +7.2 [+3.7, +12.2], +7.6 [+3.8, +10.7] % less."
- **Delay-win sentence:** none. Readings that feed sentences are read at T2's level (V467), and there tail's X2 delay win is 3 of 5 (4 of 5 at confirmatory 3's 97.5 %). V466 separately rules that the route does not count toward D10's closing. No delay-win sentence exists for v3w or sw in either cell.
- **No control:** medians per run of 1,580 TTC seconds, 287,340 vehicle-seconds of delay and 3,262 vehicle-seconds of braking at 3 m/s². The policies' close-following is not shown to differ from no control's (95 %: v3w −0.9 [−5.8, +9.5], tail +1.4 [−4.4, +8.7], sw −6.7 [−12.1, +2.6]). No control pays 31.4, 31.2 and 29.5 % more delay (median over policies).

- **The copy rule did not meet the delay filter.** It is confirmatory 3's fixed per-road rule, traced from baseline-v3's policies. X1: 2,272.5 TTC seconds per run, delay −7.2 [−12.6, −4.8] against p333. X2: 1,957 TTC seconds, delay −7.6 [−10.3, −4.9] (95 %).

**"Safety"** is permitted in X1 only, with two things beside it:
- the arm-level statement: v3w, tail and sw each have 15-18 % more close-following seconds than no control, 95 % CIs below 0;
- confirmatory 3's limit: a win on this surrogate in an uncalibrated model is not a safety result for real traffic.

### Counters with no control beside (medians over 40 runs)

- Each policy arm is the per-seed mean over 5 learners, so its collision figure is per learner: 0.2 is one collision in 200 learner-runs.
- Delay is in vehicle-seconds and includes unfinished vehicles and the insertion queue.
- Flow is the number of vehicles reaching edge 4 in the 1,500-s window.

| Cell | Arm | Delay | Flow | TTC < 3 s | Severe | Braking ≥ 3 m/s² (step) | Braking ≥ 7 m/s² (step) | Collisions (40 runs) |
|---|---|---|---|---|---|---|---|---|
| X1 | tail | 226,251 | 2,144 | 1,850 | 92 | 3,628 | 3.8 | 0 |
| X1 | sw | 231,688 | 2,144 | 1,845 | 91 | 3,619 | 4.0 | 0.2 |
| X1 | v3w | 230,763 | 2,139 | 1,809 | 90 | 3,651 | 3.8 | 0 |
| X1 | baseline-v3 | 233,601 | 2,118 | 1,893 | 91 | 3,608 | 4.0 | 0.2 |
| X1 | p333 | 242,346 | 2,119 | 3,365 | 167 | 4,460 | 4.8 | 0 |
| X1 | os0_10_10 | 248,766 | 2,123 | 2,598 | 156 | 4,047 | 4.4 | 0 |
| X1 | 3E-T | 250,054 | 2,114 | 2,255 | 129 | 3,815 | 4.2 | 0 |
| X1 | 3E-X1 (not counting) | 238,503 | 2,124 | 2,419 | 132 | 3,958 | 3.8 | 0 |
| X1 | no control | 322,813 | 2,037 | 1,493 | 88 | 3,177 | 3.1 | 0 |
| X2 | tail | 221,093 | 2,152 | 1,504 | 81 | 3,391 | 3.7 | 0 |
| X2 | sw | 221,376 | 2,158 | 1,578 | 83 | 3,455 | 3.6 | 0 |
| X2 | v3w | 226,353 | 2,157 | 1,534 | 80 | 3,420 | 3.5 | 0.2 |
| X2 | baseline-v3 | 227,987 | 2,141 | 1,594 | 83 | 3,345 | 3.8 | 0 |
| X2 | p333 | 237,372 | 2,127 | 2,711 | 144 | 3,914 | 4.7 | 0 |
| X2 | lr1000_16_2 | 238,162 | 2,128 | 2,259 | 123 | 3,682 | 4.1 | 0 |
| X2 | os1_15_10 | 240,654 | 2,124 | 2,152 | 133 | 3,732 | 4.8 | 0 |
| X2 | 3E-T | 242,170 | 2,134 | 1,737 | 111 | 3,355 | 3.8 | 0 |
| X2 | 3E-X2 | 229,111 | 2,146 | 1,732 | 112 | 3,521 | 4.0 | 0 |
| X2 | no control | 287,340 | 2,060 | 1,580 | 100 | 3,262 | 3.5 | 0 |

**Teaching to the test.** The judged 1-Hz flag (TTC below 3 s) is a term of every learner's reward. The counters outside the reward, arm against the strongest counting rule (X1 3E-T, X2 3E-X2) and against no control (95 %, positive = arm better):

| Cell | Arm | TTC < 2 s vs rule | TTC < 1.5 s vs rule | Severe vs rule | TTC < 2 s vs no control | TTC < 1.5 s vs no control | Severe vs no control |
|---|---|---|---|---|---|---|---|
| X1 | v3w | +39.7 [+36.3, +44.6] | +25.4 [+16.1, +40.4] | +28.0 [+23.0, +37.3] | −27.1 [−31.1, −17.9] | −27.4 [−36.8, −15.2] | 0.0 [−11.2, +7.3] |
| X1 | tail | +39.7 [+35.2, +43.5] | +24.9 [+17.9, +36.9] | +28.1 [+22.8, +38.1] | −24.6 [−28.9, −12.1] | −28.7 [−35.9, −12.0] | −1.9 [−11.4, +8.5] |
| X1 | sw | +38.7 [+33.0, +45.8] | +30.1 [+16.4, +38.1] | +27.2 [+20.9, +34.7] | −27.1 [−35.0, −19.5] | −25.5 [−36.6, −10.8] | −0.8 [−12.8, +7.7] |
| X2 | v3w | +40.5 [+33.6, +44.9] | +40.6 [+27.0, +47.1] | +25.8 [+20.4, +34.3] | 0.0 [−7.3, +5.6] | +11.4 [+5.3, +15.8] | +21.0 [+8.5, +29.1] |
| X2 | tail | +40.8 [+32.6, +44.4] | +42.5 [+22.3, +49.6] | +27.8 [+18.1, +35.6] | −0.7 [−8.2, +10.7] | +10.4 [+1.8, +17.5] | +18.6 [+9.8, +27.2] |
| X2 | sw | +31.0 [+22.6, +36.3] | +29.9 [+15.2, +43.7] | +19.6 [+13.8, +26.5] | −15.8 [−19.3, −1.7] | −4.9 [−12.8, +6.3] | +14.0 [0.0, +21.6] |

**1-Hz against step braking (blind-spot check, 5 % limit):**
- **Test:** one single-learner row is over the limit: baseline-v3's d2 in X1, ratio 0.948 (report-only). No reading uses the 1-Hz braking count.
- **Band, braking:** 5 single-learner rows are over it (0.944-0.950), and so is p333 at 5,000 (0.949).
- **Band, whole against half-second TTC:** 6 single-learner rows (1.055-1.142) and 3E-T at 4,500 (0.944) are over it. The band is report-only.
- **Validation:** no row is over the limit.

## 5. Band (Q3, report-only; 20 fresh seeds, training slowdowns, 95 %)

Close-following seconds and delay against no control (positive = fewer). Share = the share of the 20 seeds with fewer close-following seconds than no control.

| Arm | veh/h | TTC vs no control | Delay vs no control | Share with fewer TTC seconds |
|---|---|---|---|---|
| tail | 4,500 | −68 [−122, −7] | +22.5 [+21.7, +26.6] | 0.30 [0.10, 0.50] |
| tail | 5,000 | +51 [+5, +100] | +33.7 [+26.5, +39.9] | 0.85 [0.70, 1.00] |
| tail | 5,250 | +43 [+25, +48] | +33.6 [+30.3, +40.1] | 0.75 [0.55, 0.95] |
| tail | 5,500 | +2.2 [−15.7, +21.0] | +32.0 [+27.6, +36.0] | 0.50 [0.30, 0.70] |
| tail | 6,000 | +1.1 [−10.4, +11.1] | +27.4 [+21.4, +31.7] | 0.50 [0.30, 0.70] |
| sw | 4,500 | −117 [−154, +2] | +22.5 [+21.0, +26.9] | 0.30 [0.10, 0.50] |
| sw | 5,000 | +35 [+9, +93] | +35.1 [+26.8, +40.7] | 0.85 [0.70, 1.00] |
| sw | 5,250 | +33 [+20, +59] | +36.3 [+31.0, +41.7] | 0.85 [0.70, 1.00] |
| sw | 5,500 | 0.0 [−17.6, +20.9] | +31.2 [+27.2, +36.3] | 0.50 [0.30, 0.70] |
| sw | 6,000 | −7.9 [−22.7, +8.8] | +29.0 [+22.9, +31.8] | 0.45 [0.25, 0.65] |
| v3w | 4,500 | −122 [−155, +7] | +22.9 [+20.8, +26.3] | 0.35 [0.15, 0.55] |
| v3w | 5,000 | +48 [+6, +94] | +33.8 [+24.8, +39.9] | 0.75 [0.55, 0.90] |
| v3w | 5,250 | +38 [+15, +55] | +35.4 [+29.4, +38.8] | 0.85 [0.70, 1.00] |
| v3w | 5,500 | +1.7 [−12.5, +17.7] | +33.7 [+29.4, +35.5] | 0.50 [0.30, 0.70] |
| v3w | 6,000 | −0.6 [−14.2, +13.4] | +26.4 [+22.5, +28.7] | 0.50 [0.30, 0.70] |
| baseline-v3 | 4,500 | −96 [−172, −17] | +23.3 [+21.6, +27.4] | 0.25 [0.10, 0.45] |
| baseline-v3 | 5,000 | +35 [+4, +84] | +33.9 [+23.4, +39.4] | 0.80 [0.60, 0.95] |
| baseline-v3 | 5,250 | +39 [+21, +47] | +35.6 [+31.2, +38.8] | 0.80 [0.60, 0.95] |
| baseline-v3 | 5,500 | −2.5 [−18.6, +12.5] | +31.5 [+27.5, +35.1] | 0.50 [0.30, 0.70] |
| baseline-v3 | 6,000 | −6.7 [−22.8, +2.1] | +26.5 [+19.4, +28.0] | 0.45 [0.25, 0.65] |
| p333 | 4,500 | −109 [−178, −54] | +23.3 [+21.0, +27.6] | 0.20 [0.05, 0.40] |
| p333 | 5,000 | +52 [+3, +77] | +37.3 [+21.4, +41.9] | 0.70 [0.50, 0.90] |
| p333 | 5,250 | +22 [−57, +55] | +31.9 [+27.6, +42.5] | 0.60 [0.40, 0.80] |
| p333 | 5,500 | −60 [−94, −1] | +32.6 [+26.4, +40.1] | 0.30 [0.10, 0.50] |
| p333 | 6,000 | −69 [−94, −44] | +24.8 [+19.7, +28.0] | 0.00 [0.00, 0.00] |
| os1_15_10 | 4,500 | −109 [−178, −54] | +23.1 [+21.0, +27.6] | 0.20 [0.05, 0.40] |
| os1_15_10 | 5,000 | +27 [−2, +67] | +34.2 [+24.5, +38.6] | 0.65 [0.45, 0.85] |
| os1_15_10 | 5,250 | +27 [−32, +53] | +32.3 [+25.6, +43.6] | 0.60 [0.40, 0.80] |
| os1_15_10 | 5,500 | −51 [−64, −13] | +30.4 [+25.3, +37.0] | 0.30 [0.10, 0.50] |
| os1_15_10 | 6,000 | −37 [−40, −16] | +23.7 [+18.3, +27.4] | 0.25 [0.05, 0.45] |
| 3E-T | 4,500 | −86 [−191, −4] | +22.0 [+18.9, +25.9] | 0.30 [0.10, 0.50] |
| 3E-T | 5,000 | +15 [−8, +52] | +30.1 [+21.1, +38.0] | 0.65 [0.45, 0.85] |
| 3E-T | 5,250 | +0.3 [−30.4, +34.7] | +31.4 [+24.8, +37.8] | 0.50 [0.30, 0.70] |
| 3E-T | 5,500 | −37 [−54, −25] | +24.2 [+16.1, +32.2] | 0.20 [0.05, 0.40] |
| 3E-T | 6,000 | −26 [−42, −9] | +22.5 [+16.7, +28.8] | 0.15 [0.00, 0.30] |

- **No "shown" verdict** (D5; report-only).
  - At 5,000 and 5,250 the four policy arms (with baseline-v3) have fewer close-following seconds than no control, with 95 % CIs above 0. At 5,500 and 6,000 their 95 % CIs include 0.
  - At 4,500, tail and baseline-v3 have more close-following than no control, with 95 % CIs below 0. sw's and v3w's CIs reach above 0 (+2 and +7). No control there has very few such seconds, a median of 37 per run, so the percentages are large.
- **Delay** against no control is lower for every arm at every level, with 95 % CIs above 0.
- **p333 and os1_15_10** give identical rows on every key on 17, 10, 6, 1 and 0 of 20 seeds at 4,500, 5,000, 5,250, 5,500 and 6,000. So on those seeds, "3E-T against os1_15_10" is in effect 3E-T against p333.
- **The share CIs** come from a fixed-seed percentile bootstrap, so the same k of 20 can give slightly different bounds. tail at 5,250 shows 0.95 and os1_15_10 at 6,000 shows 0.05, where the exact law gives 0.90 and 0.10.
- **3E-T against os1_15_10** on the band's fresh seeds (positive = more than os1_15_10), beside its tuning seeds (stored; protocol table):

| veh/h | TTC, fresh | Delay, fresh | TTC, tuning | Delay, tuning |
|---|---|---|---|---|
| 4,500 | −15.2 [−35.9, +19.2] | +2.3 [+1.1, +3.5] | +24.9 | +1.5 |
| 5,000 | +15.9 [−45.5, +126.2] | +4.6 [−1.8, +13.9] | −7.9 | +2.1 |
| 5,250 | −8.7 [−43.0, +54.3] | +6.1 [−0.05, +10.9] | −7.4 | +3.2 |
| 5,500 | −4.3 [−14.5, +1.1] | +7.1 [+3.0, +15.4] | −12.2 | +3.9 |
| 6,000 | −5.6 [−22.5, +8.8] | +0.6 [−4.1, +6.7] | −20.0 | −0.5 |

  - The pooled close-following change is −4.4 % on fresh seeds, against −14.3 % on tuning seeds. There is no verdict on overfitting.
  - The pooled tuning result hides +3.2 % and +3.9 % delay at 5,250 and 5,500.
  - The band and condition T are outside the plant's stated intended use (V462(4)).

## 6. Thesis reading V459 (report-only; "thesis reading, V459, not a round-2 verdict")

**Met** = delay at least 10 % lower than no control, with the CI excluding 0 at T2's level, and close-following not harmed. Harm here means a point estimate more than 10 % worse with the 95 % upper bound below 0.

**Timing:** the bar was fixed at 15:18 on 2026-11-07, before any round-2 validation row but after confirmatory 3 and round 1 were known (V459(2)). Its claim review runs after round 2's data (V459(4)).

| Cell | Arm | Delay vs no control (99.17 %) | TTC vs no control (95 %) | Met | Policies met |
|---|---|---|---|---|---|
| X1 | tail | +27.9 [+24.8, +32.2] | −15.3 [−27.1, −6.7] | no (TTC harmed) | 0 of 5 |
| X1 | sw | +27.9 [+24.0, +30.8] | −18.4 [−27.4, −7.1] | no (TTC harmed) | 0 of 5 |
| X1 | v3w | +27.3 [+24.4, +31.1] | −16.6 [−25.1, −8.4] | no (TTC harmed) | 1 of 5 |
| X1 | baseline-v3 | +25.1 [+22.4, +27.8] | −29.2 [−32.9, −17.0] | no (TTC harmed) | 0 of 5 |
| X2 | tail | +23.5 [+20.4, +26.5] | +1.4 [−4.4, +8.7] | **yes** | 5 of 5 |
| X2 | sw | +23.1 [+19.3, +27.5] | −6.7 [−12.1, +2.6] | **yes** | 5 of 5 |
| X2 | v3w | +23.5 [+20.9, +26.7] | −0.9 [−5.8, +9.5] | **yes** | 5 of 5 |
| X2 | baseline-v3 | +21.6 [+19.3, +23.6] | −5.9 [−9.8, +2.7] | **yes** | 4 of 5 |

- **Every rule** (all 14 per cell, the 3E rules included) has delay at least 10 % lower than no control but harmed close-following, so none meets the bar in either cell.
- In X1, v3w's learner w2 misses by its TTC upper bound of −0.03.

## 7. What this means

1. **No candidate was shown better than the incumbent (Q1 null).**
   - The five trained changes were not shown better than v3w in either cell at validation: annealing, the gate hold, the 0.1-s braking charge, the look-ahead inputs and the repeated-slowdown training.
   - tail (the averaged action probabilities of 6 checkpoints of each PPO run) and sw (a hybrid: 0.8 s and os1_15_10 before 594.72 m, the PPO policy after) advanced on one cell each. Neither was shown better at test.
   - With 7 candidates, this does not show that no other change would help.
2. **X1 is won against the fixed rule p333, the grid rule os0_10_10 (tuned on separate seeds) and 3E-T** (a rule tuned by CMA-ES under the training slowdowns, not for this cell; 40 of 100 generations, unchecked for convergence).
   - It is not answered against the per-cell CMA-ES rule 3E-X1, which did not meet the delay filter on either fresh seed set; its search had not converged.
   - v3w, tail and sw each have 15-18 % more close-following than no control in X1.
   - X1 had closed under confirmatory 3's [A3] (V395); this is its third test on plant_c3 (§4).
3. **X2 is not won against the CMA-ES rules 3E-T and 3E-X2.**
   - Fewer than 4 of 5 policies cleared the 10 % margin: v3w 2, tail 3, sw 0.
   - By point estimate (arm level), every policy arm has fewer close-following seconds and less delay than both rules; against 3E-X2 the delay CIs include 0 at T2's level. Against 3E-X2 the margins are 2-16 % per policy, with 8 of 15 policies below 10 %.
   - 3E-X2, tuned for X2 on separate seeds, has 1.5 % less delay than p333 and 33 % fewer close-following seconds. Its search had not converged, so it is a lower bound on its family.
   - Under D10's T2 reading (V466, decided after the test data), the DRL claim against tuned rules closes in X2 on this plant. As under [A3], no further DRL training, tuning, plant change or seed round is run in X2 on this plant. The negative result is reported, with round 1's X2 win beside it.
4. **Against no control:**
   - v3w, tail and sw give 23-28 % less delay in both cells, against 13-24 % for the rules.
   - They pay more close-following in X1 and are not shown to differ in X2. The rules pay 43-122 % (X1) and 12-70 % (X2) more.
   - This meets the V459 bar in X2 only (report-only; "thesis reading, V459, not a round-2 verdict"; bar fixed after confirmatory 3 and round 1 were known, §6).
5. **Where the DRL claim against tuned rules stands on this plant (D10):**
   - X2 closes.
   - X1 does not close under D10. It is won against p333, os0_10_10 and 3E-T, and not answered against 3E-X1. It had closed under confirmatory 3's [A3] (V395) before rounds 1 and 2 re-tested it.

   Per V457, the parallel track continues with non-learning opponents (an MPC with a model fitted on separate seeds and/or a non-learning adaptive scheduler), and article 1 reports this map.
6. **Disclosures from the protocol**, beyond §1-§2:
   - **Q2 and Q3 follow round 1's readings:** 3E was planned before round 1 (V413). Q2 asks about v3w because v3w won round 1's T2 (V449). The band was chosen after the sweep's data (V419), and round 1 did not show it.
   - **The counting filter depends on the estimator, in both cells.** This was found after the data and changes nothing under the protocol, which fixes the median of paired differences.
     - **X2:** under a ratio of medians or a ratio of means, 3E-T would not count (−2.02 and −3.18). With T2's effects still read by the paired median, tail would then pass 4 of 5. r4a1, which joins under a ratio of medians at −1.52, blocks no tail policy.
     - **X1:** 3E-T would not count (−3.18 and −2.02), and 3E-X1 would count under either (+1.59 and −1.67). Several grid forms change status too.
   - **The 2 % delay limit is judged on a point estimate.** At 40 seeds it passes a policy truly 2 % worse about half the time (V435). The other noise-floor figures are in the protocol's Disclosures.
   - **The 5 learners per arm** sample training noise only.
   - **3E's references differ:** 3E-T's is os1_15_10, and 3E-X's is p333. 3E-X starts from each cell's own-state form. Confirmatory 3's grid forms were tuned per cell.
   - **Shared training:** every trained candidate shares v3w's training seeds. 1B acts through the gate hold. rep carries X1's two-event structure in training.
   - **The checkpoint choice** is between u250 and u500, not final policies only.
   - **Literature:** families are [VERIFY], and none is claimed as new.
7. **What this cannot show:**
   - Any win holds only for this uncalibrated SUMO model, these two slowdowns at 5,300 veh/h, and ideal V2V. The band at 4,500-6,000 is report-only.
   - A null on 7 candidates does not show that no other change would help.
   - X1's win does not show that a CMA-ES rule tuned for X1 would be beaten (3E-X1 did not count).
   - 5 of 5 is a statement about these trained policies, not about the method in general. A rule outside these families could still match them.
   - X2's "not won" is against CMA-ES rules that may not be the best of their families. 3E-X2's search was still falling at generation 40, and 3E-T ran 40 of 100 generations with convergence unchecked.

## 8. Open, for the author

- **Decided after the test data were known (V466):** D10's closing reads T2 only, and confirmatory 3's [A3] delay-win route is not read into it.
  - At T2's 99.17 % X2 closes under either reading, because tail's delay win is 3 of 5 there. It is 4 of 5 at confirmatory 3's 97.5 %.
- **Decided (V467):** every reading that feeds a claim sentence is read at T2's level (99.17 %).
  - Effects: no delay-win sentence (tail X2 3 of 5).
  - The no-control clause still applies to tail and sw in X1 (4 of 5), and not to v3w (3 of 5).
  - Replication stays at 5 of 5.
  - The 97.5 % values stay in the beside table for comparison with round 1.
- The deviations in §1 and §2 are logged as V465 and V455: two platforms at validation; checks 2 and 4 not run on the rented machine; the remote stand-in and job log not kept; the laptop's chain log ending at 17:06; and check 7 as a lean review.
