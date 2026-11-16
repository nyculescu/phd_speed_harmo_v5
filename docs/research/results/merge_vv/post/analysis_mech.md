## V3 lane-length mechanism: post hoc, descriptive (decides no reading)

**Bottom line:** both parts carry it, in different ways. The –37-point change against lr400_16_1 happens because the merge-area counts collapse at 600 m (and so does the merge spillback counted under "rest"). Edge-1 counts do not change at all. But WORSE (rather than a smaller positive edge) comes from v3w's fixed edge-1 deficit of about 22 samples per run. That deficit is –1.7 points at 300 m, where lr400_16_1's median total is 1,375.5, and about –28 points at 600 m, where that median is 76.5. A second, smaller cause: at 600 m the rules' typical-seed merge counts fell further than v3w's.

**Inputs and checks.** v3w = per-seed mean of the 5 learners; C-D5 values are the per-learner statistic.
- In all 8,640 rows, `m_road_ttc3` sums to `ttc_net`, the period keys match, `vv_stand_s` equals `end_stop`/`end_stop2`, and demand is paired.
- My extraction reproduces the reader exactly: 15.99 / –21.05, change –37.04, deficit +5.8 / +22.4 / +0.1, no-edge-1 +8.06.
- Groups: merge 1 = 3a + r + rj; merge 2 = 4a + r2 + rj2; edge 1 = road 1; rest = everything else.

### (1) Close-following per run: mean (median)

| arm | L | total | m1 | m2 | e1 (≥98 % hold) | rest |
|---|---|---|---|---|---|---|
| v3w | 300 | 1085 (1087) | 271 (257) | 623 (619) | 26.4 (25.4) | 165 (157) |
| lr400_16_1 | 300 | 1325 (1376) | 318 (280) | 792 (857) | 3.2 (2) | 211 (211) |
| grid_lr400_13_1 | 300 | 1386 (1390) | 339 (295) | 842 (845) | 3.3 (3) | 202 (198) |
| p333 | 300 | 1644 (1671) | 329 (296) | 986 (1054) | 28.0 (26) | 301 (268) |
| nc | 300 | 1378 (1340) | 359 (318) | 809 (794) | 1.8 (1) | 208 (198) |
| v3w | 600 | 195 (117) | 41 (25) | 120 (52) | 26.5 (25.2) | 7.0 (0.4) |
| lr400_16_1 | 600 | 255 (76.5) | 47 (15) | 191 (26.5) | 3.2 (3) | 14.9 (0) |
| grid_lr400_13_1 | 600 | 251 (87.5) | 50 (21) | 185 (36) | 3.3 (3) | 12.9 (0) |
| p333 | 600 | 269 (112.5) | 54 (20) | 178 (32.5) | 27.5 (27) | 9.7 (0) |
| nc | 600 | 680 (673.5) | 128 (66) | 483 (488.5) | 2.0 (2) | 66.4 (57) |

Edge 1 by period, both lengths, every arm: before 0, taper ≤0.1, after 0.1–0.5, rest 0. All the rest is hold.

### (2) Where the 300-m edge came from

| against | C-D5 | Shapley split m1 / m2 / rest / e1 | mean-based % m1 / m2 / rest / e1 | rule − v3w, samples per run (mean): merge / rest / e1 |
|---|---|---|---|---|
| lr400_16_1 | +15.99 | +2.84 / +11.89 / +2.98 / **–1.71** | +3.59 / +12.74 / +3.50 / –1.75 (total 18.08) | +216 / +46 / –23.2 |
| grid_lr400_13_1 | +21.70 | +3.78 / +17.09 / +2.40 / **–1.57** | +4.90 / +15.76 / +2.70 / –1.67 | +286 / +37 / –23.1 |

- The merge area supplied about 92 % (lr) and 96 % (grid) of the edge.
- Edge 1 cost about 1.6–1.7 points.
- In the traces (2 seeds only, so treat this as suggestive), "rest" at 300 m is mostly merge spillback:
  - edge-3 samples sit in the last ~150 m before 4a during the rest period;
  - edge-2 samples sit in the last 33 m before 3a.

### (3) Merge-area counts and lane-end standing at 600 m

Fraction kept (600 / 300), shown as mean | median:

| arm | m1 | m2 | merge | rest |
|---|---|---|---|---|
| v3w | 0.15 \| 0.10 | 0.19 \| 0.08 | 0.18 \| 0.10 | 0.04 \| 0 |
| lr400_16_1 | 0.15 \| 0.05 | 0.24 \| 0.03 | 0.21 \| 0.06 | 0.07 \| 0 |
| grid_lr400_13_1 | 0.15 \| 0.07 | 0.22 \| 0.04 | 0.20 \| 0.07 | 0.06 \| 0 |
| p333 | 0.16 \| 0.07 | 0.18 \| 0.03 | 0.18 \| 0.06 | 0.03 \| 0 |
| nc | 0.36 \| 0.21 | 0.60 \| 0.62 | 0.52 \| 0.52 | 0.32 \| 0.29 |

Lane-end standing (`vv_stand_s`, vehicle-seconds): median 300→600, then the cut by median and by mean. Standing vehicles per run (`vv_stand_n`) are in the last column.

| arm | 3a_0 | 4a_0 | vehicles 3a / 4a |
|---|---|---|---|
| v3w | 204→32 (0.84; 0.72) | 519→77 (0.85; 0.69) | 10→1.4 / 20.2→2.8 |
| lr400_16_1 | 274→11.5 (0.96; 0.73) | 900→23 (0.97; 0.68) | 12→1 / 25→2 |
| grid_lr400_13_1 | 282.5→9.5 (0.97; 0.78) | 843.5→26 (0.97; 0.70) | 12→1 / 26→1 |
| p333 | 232→7 (0.97; 0.75) | 905→22.5 (0.98; 0.76) | 11→1 / 29→1 |
| nc | 226.5→109.5 (0.52; 0.31) | 546→412.5 (0.24; 0.27) | 14→7 / 26→19 |

- In the typical seed (median), the rules' merges go nearly quiet at 600 m, while v3w keeps more standing.
- By mean, all controlled arms keep about 0.7 of the cut.
- The 600-m counts are strongly right-skewed. Merge area at p50 / p75 / p90: lr400_16_1 72 / 287 / 825; v3w 91 / 232 / 391.
- From v3.json: VV-D12 "removed" reads false at both merges only because of nc (lower bounds 0.36 and 0.15). v3w is at 0.818 and 0.803, the rules at ≥0.94.

### (4) Edge 1 between 300 and 600 m

**Geometry is unchanged, verified in `vv_lanes` and the offsets.**
- Lanes 1_* are 3,000 m and 2_* are 498.3 m in every row.
- Every lane other than 3a_* and 4a_* is identical in all 8,640 rows.
- The offsets of edges 1, 2 and 3a are unchanged; everything downstream moves +300 m.

**Edge-1 counts do not change.** Paired mean difference (600 − 300) with a post hoc 95 % interval:

| arm | per run 300→600 | paired diff |
|---|---|---|
| v3w | 26.39→26.50 | +0.11 [–0.28, +0.49] |
| lr400_16_1 | 3.16→3.17 | +0.01 [–0.29, +0.29] |
| grid_lr400_13_1 | 3.29→3.34 | +0.05 [–0.23, +0.34] |
| p333 | 27.98→27.53 | –0.45 [–1.27, +0.37] |
| nc | 1.79→1.98 | +0.19 [–0.02, +0.41] |

**No merge-1 spillback onto edge 1 at either length.**
- Before onset, no queue (<50 km/h) reaches back into edge 1 from its downstream end: 0 m for every arm at both lengths.
- Edge-2 speed before onset is 86.5 km/h at both lengths.
- Edge-1 and edge-2 speeds by period are unchanged to within 0.1 km/h.
- The hold-period queue reach on edge 1 is unchanged: median of the per-run maximum v3w 120→110 m, lr400_16_1 150→150 m, nc 200→200 m.
- Merge-1 spillback does reach the end of edge 2 at 300 m: v3w 29.5 edge-2 samples per run (after and rest periods), lr400_16_1 25.5, nc 52.5. These vanish at 600 m and count under "rest", not edge 1.

**Positions in the traces** (w1u500; 59 edge-1 samples over 2 seeds and both lengths):
- All are in the hold period, 10–42 m before the edge-1 end.
- Follower about 48 km/h, leader about 26 km/h, so these are vehicles slowing into the 30 km/h zone on edge 2.
- 54 of the 59 followers are ALKS.
- lr400_16_1 has 1–2 samples per run, and their followers are human cars.

Why v3w ≈ p333 ≫ the lr rules on edge 1 is an inference I did not test: by its definition, LocalRule widens ALKS headway when the roadside mean speed in the next 400 m drops below 16 m/s.

### (5) Reconciling deficit_600 with no_edge1_600 (against lr400_16_1, at 600 m)

| quantity | merge | e1 | rest | no_e1 | total |
|---|---|---|---|---|---|
| reader deficit: median over seeds of (v3w mean − rule) | +5.8 | +22.4 | +0.1 | +6.2 | +28.9 |
| mean over learners of median(P_l − R), the C-D5 numerator | –6.3 | +22.0 | 0.0 | –5.8 | +16.1 |
| mean(v3w − R) | –75.5 | +23.3 | –7.9 | –83.4 | –60.1 |
| rule median | 72 | 3 | 0 | 72 | 76.5 |
| C-D5 % | +8.75 | –733 | 0 | **+8.06** | **–21.05** |

There is no contradiction once the conventions are aligned:
- **Sign:** the deficit is in samples, positive = v3w worse. C-D5 is in %, positive = v3w better.
- **Pooled vs per learner:** this flips the merge sign. The per-seed mean of 5 learners is pulled up by any learner with a breakdown on that seed: v3w's pooled median total is 117.3, single learners 89–108. c1_screen.md C-D5 rejected the pooled arm for exactly this bias.
- **Median vs mean:** in means, v3w has 75 fewer merge-area samples per run than lr400_16_1. The mean-based edge at 600 m is +23.6 % against lr400_16_1 and +22.3 % against grid_lr400_13_1.
- **Where v3w's advantage sits:** split the seeds into thirds by lr400_16_1's merge-area count. The share of learner runs with fewer samples is 3 %, 41 % and 78 %; the mean difference (rule − learner) is –79, –54 and +313. So v3w's 600-m advantage sits in the third of seeds where the rule's merges break down. The median seed is a quiet-merge seed where edge 1 dominates.
- **Medians are not additive, but close here:** (–5.8 + 22.0) / 76.5 = –21.2 %, against the actual –21.05.

### (6) The pre-statement, and what carries the change

**What holds:**
- Edge 1 is geometrically unchanged.
- The E30 description holds: 26–28 edge-1 samples per run for v3w and p333 against 3 for the lr rules, at least 98 % in hold.
- Those counts are also unchanged at 600 m.

**What only partly holds:** the edge-1 deficit is indeed not a lane-length effect. But the WORSE reading exists because the 600-m lanes removed the merge-area advantage that outweighed that deficit at 300 m.

Two ways to split the change, for lr400_16_1 (–37.04) and grid_lr400_13_1 (–28.33):

| split | lr400_16_1 | grid_lr400_13_1 |
|---|---|---|
| A. which counts changed (exact Shapley; 95 % post hoc interval) | merge –20.73 [–27.12, –14.27] (m1 –9.41, m2 –14.92); rest –16.56 [–20.96, –12.56]; e1 +0.26 [–0.74, +0.81] | merge –20.93 [–26.60, –14.75]; rest –7.60 [–11.36, –3.96]; e1 +0.20 [–0.66, +1.07] |
| B. what the number is made of (each part's median difference over the rule's total median) | outside edge 1: +17.8→+7.6 (–10.2); edge 1: –1.6→–28.8 (–27.2); sum –37.4 | outside: +23.3→+17.8 (–5.5); edge 1: –1.6→–24.9 (–23.3); sum –28.8 |
| level split at 600 m (Shapley) | e1 –28.38, m2 +5.31, m1 +2.08 | e1 –24.31, m2 +11.72, m1 +5.91 |

- In split B, the edge-1 numerator barely moves (22.2→22.0 samples); only its denominator shrinks, from 1,375.5 to 76.5.
- With edge 1 left out, the 600-m edge stays positive: +8.06 [1.94, 15.14] against lr400_16_1 and +18.35 [11.18, 25.65] against grid_lr400_13_1 (the reader's printed 95 % values; no null was computed).
- I tried a uniform-cut model on these 300-m rows and could not reproduce the plan's expectation table. Its exact model is not stated in the plan, so I draw no comparison (plan_model.txt).

### Consistency with the stored E30 rows (300 m, seeds 7,489,160–639)

Mean per run, E30 vs this screen at 300 m:

| arm | total | m1 | m2 | e1 | rest | end_stop / end_stop2 |
|---|---|---|---|---|---|---|
| v3w | 1060 vs 1085 | 264 vs 271 | 610 vs 623 | 25.6 vs 26.4 | 160 vs 165 | 229/529 vs 234/540 |
| lr400_16_1 | 1207 vs 1325 | 312 vs 318 | 714 vs 792 | 2.85 vs 3.16 | 178 vs 211 | 368/798 vs 366/905 |
| grid_lr400_13_1 | 1400 vs 1386 | 323 vs 339 | 866 vs 842 | 3.30 vs 3.29 | 209 vs 202 | – |
| p333 | 1607 vs 1644 | – | – | 26.6 vs 28.0 | – | – |
| nc | 1349 vs 1378 | – | – | 1.86 vs 1.79 | – | – |

- C-D5 against lr400_16_1: 9.93 in E30 vs 15.99 here. Against grid_lr400_13_1: 22.76 vs 21.70.
- The edge-1 term (mean-based) agrees: –1.88 vs –1.75 (lr) and –1.59 vs –1.67 (grid).
- v3w's counts agree within about 3 %. The larger edge against lr400_16_1 here comes from that rule's higher merge-2 and rest counts on these seeds. I made no test of that difference.

**Uncertainty and choices (all post hoc):**
- The <50 km/h congestion threshold is my choice.
- The 300-s warm-up is the MergeEnv default; it fits the field's 150 bins × 10 s = the 1,500-s episode.
- Trace positions rest on 2 seeds × 3 arms only.
- The Shapley and mean-based splits are accounting choices, not pre-registered.
- Bootstrap B = 2,000 (rng 20261116), seeds resampled jointly; no nulls.

No repo or run file was modified. Everything ran as one process at a time under `nice -n 19` with OMP_NUM_THREADS=1.

Files are in /home/catalin/work/phd/v5b1_runs/vv_post/mechanism/:
- extract.py
- analyze.py
- extra.py
- plan_model.py
- trace_rest.py
- runs.pkl
- cf_runs.pkl
- results.json
- extra.json
- plan_model.txt
- trace_rest.txt
- SHA256SUMS