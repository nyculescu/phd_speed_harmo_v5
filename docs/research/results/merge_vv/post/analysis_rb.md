## Recomputer B report: merge V&V V2/V3 readings, recomputed independently

**Verdict:** I re-implemented the readings from the plan text and `s6_rows.jsonl` alone. Every deciding reading in `v3.json` matches mine exactly. I opened `read_vv.py` and `v3.json` only after my own numbers and nulls were saved. The reader's null logic follows the plan. I found no defect that changes a deciding reading. Two printed items use a different definition from mine: the VV-D12 standing cut and the remaining-deficit figure. One of those, VV-D12, depends heavily on which definition is used (see M3).

**Integrity of the rows:** 8,640 rows, 9 arms × 480 seeds × 2 lengths. No duplicates, one commit (6e96988), no drops, no teleports. The per-road counts in `m_road_ttc3` add up to `ttc_net` in every row. At 300 m, `vv_m_whole` equals `ttc_net` and `vv_m_half` equals `ttc_half` in all 4,320 rows. `end_stop`/`end_stop2` equal `vv_stand_s` for lanes 3a_0 and 4a_0. One row, L600|nc seed 7,492,030, has `ttc_net` 0 and no `vv_ttc3_main`, `vv_enc` or `ttc3` keys; zero-valued keys look like they are simply not written. The reader reads a missing key as 0, which is correct here. No control is not in any deciding comparison.

### My numbers against v3.json
Statistic: C-D5 (c1_confirm §1). Per learner, the median over seeds of −(P−R)/median(R)×100, with the full-sample median as denominator; the effect is the mean of the five learners. Resamples: `default_rng(20261108).integers(0,480,(20000,480))`, seeds in ascending order.

| Reading | B (mine) | v3.json | Match |
|---|---|---|---|
| V2 vs lr400_16_1: 0.1-s edge [95 %] | +16.228 [12.88, 19.69] | +16.228 [12.885, 19.686] | exact |
| V2 vs lr400_16_1: 1-Hz edge [95 %] | +15.994 [12.61, 19.83] | same | exact |
| V2 vs lr400_16_1: difference [95 %] | +0.233 [−0.410, +0.598] | +0.233 [−0.410, +0.598] | exact |
| V2 vs grid_lr400_13_1: difference [95 %] | −0.054 [−0.558, +0.475] | same | exact |
| V2 outcome | MET (both intervals within ±3) | MET | yes |
| V3a replication vs lr400_16_1 (97.5 %) | +15.994 [12.177, 20.276] | same | exact |
| V3a replication vs grid_lr400_13_1 (97.5 %) | +21.698 [16.171, 25.182] | same | exact |
| V3a replication nulls (2,000 swaps; mine 2,000 resamples per swap, reader 1,000) | 0.95 %, 1.35 % | 1.175 %, 1.075 % | same range, both under 1.9 % |
| V3a replication outcome | REPLICATED | REPLICATED | yes |
| V3a main lane vs lr400_16_1 (97.5 %) | +10.640 [6.560, 14.496] | same | exact |
| V3a main lane vs grid_lr400_13_1 (97.5 %) | +22.287 [17.927, 26.447] | same | exact |
| V3a main-lane nulls | 1.025 %, 1.225 % | 1.075 %, 0.925 % | same range |
| V3a main-lane outcome | also shown on main-lane samples | same | yes |
| V3b at 600 m vs lr400_16_1: 97.5 % / 98.75 % | −21.046; [−28.235, −12.418]; [−29.020, **−11.373**] | same | exact |
| V3b at 600 m vs grid_lr400_13_1: 97.5 % / 98.75 % | −6.629; [−15.429, +2.971]; [−16.343, +4.000] | same | exact |
| HOLDS | no (both lower bounds below 0); my nulls 1.125 %, 1.0 % | not shown; nulls not computed (correct, bound below 0) | yes |
| WORSE null vs lr400_16_1 | **0.475 %** (2,000 swaps × 4,000 resamples, SE about 0.11 points) | 0.475 % (20,000 × 4,000) | same range; the exact equality is a coincidence |
| WORSE null vs grid_lr400_13_1 (not needed) | 0.425 % | not computed | — |
| V3b outcome | WORSE (vs lr400_16_1 only) | WORSE | yes |
| Change, 600 m minus 300 m, vs lr400_16_1 [95 %] | −37.040 [−44.363, −28.868] | same | exact |
| Change vs grid_lr400_13_1 [95 %] | −28.327 [−36.176, −19.126] | same | exact |
| Change outcome | depends on lane length (both rules) | same | yes |
| 600-m edge, edge 1 left out, vs lr400_16_1 [95 %] | +8.056 [1.944, 15.139] | same | exact |
| 600-m edge, edge 1 left out, vs grid_lr400_13_1 [95 %] | +18.353 [11.176, 25.647] | same | exact |
| Missed share per arm (printed only) | ratio of sums: −0.0001 to −0.0018 | median per run: −0.00003 to −0.00205 | mismatch M1 |
| Largest remaining deficit at 600 m | edge 1 (+22.0 / +21.8 samples per run) | edge 1 (+22.4 / +22.6) | same group; form differs, M2 |
| VV-D12 standing cut, "removed" | not removed at either merge | `removed` False at both merges | same outcome; form differs, M3 |

The bounds match to every printed digit because both implementations draw the same resample matrix. This independently checks the definition and the code, not bootstrap noise. With B = 20,000 that noise is small anyway.

### Mismatches and resolution
- **M1, missed share (printed).** The reader takes the median over runs of the per-run ratio (`read_vv.py:150`). I used a ratio of sums. When I compute the median per run, I reproduce `v3.json` exactly. The plan (§2 V2, "Printed") defines the ratio but not how runs are combined, so both follow the plan. In every arm the 0.1-s time is about 0.1 % *below* the 1-Hz count, so the "missed" share is negative.
- **M2, remaining deficit (printed; feeds the "[group]" slot of the record sentence).** The reader takes the median over seeds of (per-seed mean of the learners minus the rule) (`:181-187` via `arm_series` at `:163-164`). That is the pooled arm, which c1_screen C-D5 calls biased. I reproduce its numbers exactly in that form. My form, the mean of the learners' medians, gives the same largest group, edge 1. The merge-area sign flips with the form: against lr400_16_1 the reader gives +5.8 (v3w more) and mine gives −6.3 (mean difference −75.5). The plan does not fix the form, so the group named in the sentence is unaffected. Any merge-area number quoted from `deficit_600` should name its form.
- **M3, VV-D12 cut.** The reader's cut is 1 − median(600)/median(300) per arm (`:167-178`). "Removed" there needs the 95 % lower bound to be at least 0.80 for v3w, both rules **and no control** (`:177`).
  - The plan fixes neither the form nor the arms ("its cut's 95 % lower bound", VV-D12, §1). I reproduce the reader's numbers exactly in its form (v3w pooled: merge 1 0.843 [lo 0.818], merge 2 0.852 [lo 0.803]).
  - **This reading depends on the definition:**
    - Reader's form: v3w and both rules clear 0.80 at both merges, and only no control fails (lower bounds 0.36 and 0.15). Without no control, both merges would read "removed".
    - Same form, v3w as the mean of the five learners: lower bounds 0.937 and 0.931.
    - Mean-based forms (pooled over the 9 arms, or ratio of sums per arm): no arm reaches 80 %. Pooled lower bounds are 66.1 % and 63.2 %; per arm the highest is 73.9 %. Standing at 600 m is heavy-tailed: for lr400_16_1 at merge 1 the median is 11.5 vehicle-seconds but the mean is 97.9.
  - Resolution: the outcome, no "standing removed" wording, is the cautious choice, and it is what the reader and my forms give. It holds only because no control is included or because a mean-based form is used. The record should state the form and that no control decides the result. Post hoc figures are in `posthoc_cut_forms_B.json`.

### Null logic in the reader, checked against the plan and c1_confirm §1
- **What is swapped:** one ±1 sign per learner and seed on the per-seed edge, with the denominator fixed (`read_cf.py:95-107`). This matches "one sign per learner and seed, on the per-seed edge".
- **Rate:** the mean of the false rates of "lower bound above 0" and "upper bound below 0", as the plan states.
- **Swaps and resamples:**
  - The 1.9 % bar uses 2,000 swaps × 1,000 resamples, re-estimated once at 20,000 swaps with a new seed if the rate is above the bar (`read_vv.py:28-31, 97-107`).
  - WORSE uses 20,000 swaps × 4,000 resamples directly, as §Conventions states.
  - The plan does not set the number of resamples for the 2,000-swap nulls. 1,000 is the same constant the E30 reader used (`read_cf.py:25`).
  - One resample matrix (seed+1) is reused across all swaps of a test. The plan says nothing on this. My nulls with fresh resamples on every swap land in the same range.
- **Percentiles:** 1.25/98.75 for the 97.5 % tests and 0.625/99.375 for WORSE. Bars 0.019 and 0.0094.
- **Bar comparison:** the reader passes at `rate <= bar`, while §V3b says "under 1.9 %". This only matters at exactly the bar, and every rate here is 0.475-1.175 %.
- Nulls run only where a bound clears 0 (`:120, 132`), which is enough, since a null can only void a positive reading.

### Reader defects (none changes a deciding reading here)
1. VV-D12 depends on the definition, and the outcome is set by no control (M3).
2. The cut (`:163-178`) and `deficit_600` use the pooled v3w arm, unlike C-D5. This pulls v3w's cut down (0.843 against 0.93-0.97 for each learner) and flips the sign of the merge-area deficit (M2).
3. `Cell.D` floors a zero rule median at 1e-9 (`:82`). At 600 m the "rest" group then prints 0.0 [0, 0] for both rules (`printed_600/*/g_rest`). By c1_screen's not-readable rule (rule median 0) it should read "not readable". The mean difference there is −7.9 and −6.0 samples per run, v3w fewer.
4. A missing or None key is read as 0 (`:46, :75`) without a flag. Here only the zero-count no-control row is affected.

### Context for the record (post hoc, not deciding)
- The 600-m WORSE is carried by edge 1. v3w has about 22 more edge-1 samples per run, unchanged from 300 m, against rule medians of only 76.5 and 87.5. With edge 1 left out, the 600-m edge is positive against both rules (above).
- With edge 1 left out, the change is −9.8 [−17.0, −1.8] against lr400_16_1 and −5.0 [−12.4, +3.1] against grid_lr400_13_1 (`posthoc_change_no_edge1_B.json`). Part of the −37-point change is a fixed edge-1 deficit divided by a denominator about 18 times smaller.

Files are in /home/catalin/work/phd/v5b1_runs/vv_post/recompute_B/:
- `readings_B.json`
- `nulls_B.jsonl`
- `posthoc_cut_forms_B.json`
- `posthoc_change_no_edge1_B.json`
- scripts: `load.py`, `readings.py`, `null.py`, `run_nulls.sh`
- data: `rows.pkl`, `edges_B.npz`
