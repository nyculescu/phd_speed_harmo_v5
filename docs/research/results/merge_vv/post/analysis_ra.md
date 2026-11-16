Recomputer A report: merge V&V V2/V3 readings, recomputed from vv_screen/s6_rows.jsonl

**Verdict:** my independent re-implementation agrees with v3.json. 337 of the 344 compared values match exactly (difference ≤ 1e-9), because we use the same resample construction: `default_rng(20261108).integers(0,480,(20000,480))`, full-sample rule median in the denominator, and numpy linear percentiles. The 7 that differ are 4 null rates, which differ only by Monte Carlo noise, and 3 printed g_rest edges that are undefined (see defect 3). None of the deciding readings changes: **V2 MET, V3a REPLICATED, main-lane shown, V3b WORSE** (against lr400_16_1), HOLDS false, and the change excludes 0 for both rules. I found three reader issues that affect wording or printed items (defects 1-3) and one check that cannot fail (defect 4). None of them flips a deciding reading.

My numbers were computed and hashed (`hashes_before_v3.txt`, 08:29 MST) before I opened read_vv.py or v3.json.

**Integrity**
- 8,640 rows, 18 (length, arm) groups × 480 seeds (7,492,000-479), no duplicates.
- Lane lengths are 294.72 / 594.72 m.
- In every row, the road groups of `m_road_ttc3` sum to `ttc_net`, and `m_ttc3_all` equals `ttc_net`.
- In all 4,320 rows at 300 m: `vv_m_whole` equals `ttc_net`, `vv_m_half` equals `ttc_half`, and `vv_m_time` equals 0.1 × `vv_m_step`.
- One row (L600, nc, seed 7492030, `ttc_net` = 0) has no `vv_ttc3_main` or `vv_enc` key, because the counter never fired. Both the reader and I treat it as 0. It is not in any deciding comparison.

**Mine vs v3.json** (C-D5, positive means v3w better; "=" means identical to ≤ 1e-9)

| Reading | Mine | v3.json |
|---|---|---|
| V2 0.1-s edge, lr400_16_1 | +16.23 [95 % +12.88, +19.69] | = |
| V2 1-Hz edge, lr400_16_1 | +15.99 [+12.61, +19.83] | = |
| V2 difference, lr400_16_1 | +0.23 [−0.41, +0.60] | = |
| V2 0.1-s edge, grid_lr400_13_1 | +21.64 [+16.77, +24.81] | = |
| V2 1-Hz edge, grid_lr400_13_1 | +21.70 [+16.81, +24.72] | = |
| V2 difference, grid_lr400_13_1 | −0.05 [−0.56, +0.47] → MET | = |
| V3a replication, lr400_16_1 (97.5 %) | +15.99 [+12.18, +20.28], null 1.175 % | =, null 1.175 % |
| V3a replication, grid (97.5 %) | +21.70 [+16.17, +25.18], null 1.05 % | =, null 1.075 % |
| Main-lane, lr400_16_1 | +10.64 [+6.56, +14.50], null 1.125 % | =, null 1.075 % |
| Main-lane, grid | +22.29 [+17.93, +26.45], null 1.10 % | =, null 0.925 % |
| V3b at 600 m, lr400_16_1 (97.5 %) | −21.05 [−28.24, −12.42] | = |
| V3b at 600 m, grid (97.5 %) | −6.63 [−15.43, +2.97] | = |
| WORSE, lr400_16_1 (98.75 % upper bound) | −11.37, null 0.51 % (20,000 swaps × 4,000 resamples) | =, null 0.475 % |
| WORSE, grid (98.75 % upper bound) | +4.00, so not worse | = |
| Change 600 − 300 m, lr400_16_1 (95 %) | −37.04 [−44.36, −28.87] | = |
| Change 600 − 300 m, grid (95 %) | −28.33 [−36.18, −19.13] | = |
| 600-m edge without edge-1 samples, lr400_16_1 (95 %) | +8.06 [+1.94, +15.14] | = |
| 600-m edge without edge-1 samples, grid (95 %) | +18.35 [+11.18, +25.65] | = |
| Missed share per arm (median of runs) | −0.003 % to −0.21 % | = |
| Standing cut, ratio of medians (reader's form, lower bound) | v3w 0.818 / 0.803; rules ≥ 0.938; p333 0.942 / 0.967; nc 0.363 / 0.153 | = |
| Printed group edges at 300 m and 600 m (merge area, merges 1 and 2, edge 1, rest) | all equal | = |

My nulls also pass at 600 m at the HOLDS level (1.05 % for each rule), but that is moot, because both lower bounds there are below 0.

**Null logic in read_vv.py (lines 97-108, 114-136, and `read_cf.null_rate`)**
It matches merge_vv.md §Conventions and c1_confirm.md §1:
- Each learner's per-seed edge gets its own random sign, which is the same as swapping P and R in the numerator with median(R) held at its full-sample value.
- 2,000 swaps; a rate above 1.9 % is re-estimated once with 20,000 swaps (seed + 7,919).
- The rate is the mean of the two false rates: lower bound above 0, and upper bound below 0.
- For the 1.9 % bar the percentiles are (1.25, 98.75). For WORSE they are (0.625, 99.375), with 20,000 swaps × 4,000 resamples and a bar of 0.94 %. A null passes if its rate is ≤ the bar.
- A null is computed only where a bound clears 0, which is correct for each reading.
- 1,000 resamples per swap for the 1.9 % nulls: the plan says nothing here; this is the C1 reader's convention.

My separate implementation of the null (2,000 resamples per swap) gives rates within about 1 SE of the reader's.

**Reader defects or omissions that could change a sentence (none changes a deciding reading)**
1. **WORSE is carried by edge 1, and the reader's label does not say so.** The plan states in advance (§V3b) that "a WORSE or NOT SHOWN carried by edge 1 is not a lane-length effect". `reading` and status.txt print a bare "V3b WORSE".
   - With edge-1 samples left out, the 600-m edge against lr400_16_1 is +8.1 % [+1.9, +15.1] (+1.11 at the 97.5 % lower bound).
   - v3w has 26.5 edge-1 samples per run against 3.2 for lr400_16_1 at 600 m, and 26.4 against 3.2 at 300 m, so edge 1 is unchanged by lane length.
   - The record sentence must carry this qualifier.
   - Post hoc, mine: the change with edge 1 left out is −9.8 [−17.0, −1.8] against lr400_16_1 and −5.0 [−12.4, +3.1] against grid. The −37 / −28 change is inflated because a roughly constant 22-sample edge-1 deficit is divided by a rule median that fell from 1,375 to 76.5. That is about 29 points by arithmetic; it is approximate, since medians of differences do not add.
2. **"Standing removed" (VV-D12) depends on a definition the plan does not give** (read_vv.py:167-178). The reader uses 1 − median600/median300 and requires v3w (pooled), both rules and nc to pass, leaving p333 out. Both merges read "not removed" only because nc is included.
   - Without nc, v3w (0.818, 0.803) and the rules would pass at both merges.
   - Under a ratio-of-means form, nothing passes: the best lower bound is grid at merge 1, 0.739; v3w pooled is 0.687 and 0.656.
   - The median form is zero-inflated. 18-36 % of runs by controlled arms (17-36 % across all 9 arms) have no standing at 600 m, yet mean standing stays at 22-34 % of its 300-m level.
   - My judgment: "not removed" is the defensible wording, but the record should state the cut's definition and which arms it covers.
3. **Printed items only.**
   - `deficit_600` (lines 181-187) takes the pooled per-seed mean of the learners before the median, not the C-D5 form. Against lr400_16_1 it gives a merge-area deficit of +5.8, while the C-D5 form gives −6.3, and the printed merge-area edge is +8.75 % [+2.2, +15.7], with v3w better. The largest group, edge 1 at about 22 samples, is the same under both forms. Do not quote its merge value.
   - g_rest at 600 m prints "0.0 [0.0, 0.0]" for lr400_16_1, grid and p333. The rule's median there is 0, and `D()` floors the denominator at 1e-9 (lines 80-83). The edge is undefined and should print as not readable.
4. **The CPU VOID check cannot fail.** It reads a single CPU from meta.json (lines 386-387), and rows carry no CPU field, so a mixed-CPU screen would pass. This has no effect here: one instance ran everything (AMD EPYC 7B13).
5. **Trivial:** V2's `within` and the null `ok` tests use strict and ≤ inequalities. Nothing sits near a boundary.

Files are in /home/catalin/work/phd/v5b1_runs/vv_post/recompute_A/:
- Scripts: extract.py, checks.py, stats.py, extra.py, nulls.py, posthoc.py, compare.py
- Outputs: results_A.json, nulls_A.json, posthoc_A.json, compare_A.json, hashes_before_v3.txt