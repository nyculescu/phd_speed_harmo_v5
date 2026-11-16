## Merge V&V printed items: tables built, every reader number checked

All tables are in `/home/catalin/work/phd/v5b1_runs/vv_post/printed/printed_tables.md`, with the source of every number marked. I ran no simulations and changed no repo or run file. The only compute was two `nice -n 19` processes, run one after the other (about 80 s each).

**Spot-check:** I recomputed v3.json's numbers from the 8,640 rows with my own code (it does not import `read_vv.py`). That covers 752 numbers: every printed_300 and printed_600 edge (pt, lo95, hi95, se), collisions, P0, `standing_vehicles`, `missed_share`, `c15_cap_share_600`, the VV-D12 cut, `deficit_600` and the V2 edges. All 752 match exactly (largest difference 0.0). Jams are the one gap: they come from v3.json only, because recomputing them needs read6's reading of the `st/` side files.

A bug in my own first pass: I read absent keys as NaN, and the comparison skipped NaN. I fixed it so absent counters are read as 0 (as the reader does) and a NaN counts as a mismatch, then re-ran. The match still holds.

### Checks
- **Smoke** (smoke.json): pass. Missing, replay, side-file, twin, T0-length, meter and demand checks are all 0.
  - `x_out` = 0 and the column-15 cap share = 0.0 on all 8 controlled arms at 600 m.
  - Lane-end standing on seed 7,493,010 (merge 1 / merge 2, veh-s): no control 27/193 at 300 m and 433/287 at 600 m; lr400_16_1 431/1062 at 300 m and 0/0 at 600 m.
- **Identity** (ident.json): 0 rule, learner or diagnostic differences, nothing missing, for both the plain and the traced replays. The CPU equals CF's (AMD EPYC 7B13). `tracer_bug` false.
- **V1** (v1.json, status.txt): "CHECKS PASS; visual check pending". 0 wiring, definition or twin failures; 12 twin pairs equal; 18 traced runs classified.
  - Leaders: 93.2 % same lane, 6.8 % next lane, 0 cross-lane or off-route (pooled, descriptive).
  - The 40-sample visual check is drawn but not yet plotted or judged.
- **v3.json:** n = 480, nothing dropped; `bugs` and `void` are empty.
  - My row checks found 0 mismatches: meter whole-second = `ttc_net` and half-second = `ttc_half` in every 300-m run; `vv_stand_s` = `end_stop`; period keys equal the `m_road_ttc3` period sums and add up to `ttc_net`; seeds paired across lengths; lane lengths 294.72 and 594.72.

### V2 (v3.json = rows)
| rule | 0.1-s edge | 1-Hz edge | diff (95 %) |
|---|---|---|---|
| lr400_16_1 | +16.2 [+12.9, +19.7] | +16.0 [+12.6, +19.8] | +0.23 [−0.41, +0.60] |
| grid_lr400_13_1 | +21.6 [+16.8, +24.8] | +21.7 [+16.8, +24.7] | −0.05 [−0.56, +0.47] |

Outcome MET. The missed share (median over seeds) is between −0.003 % and −0.205 % for all 9 arms, so the 1-Hz count is slightly above the 0.1-s time. Per-run spread is about ±1.5 %. I have not established why the bias is negative.

### Close-following edges, % [95 %], v3w against each rule (v3.json = rows)
| measure | lr 300 m | lr 600 m | grid 300 m | grid 600 m |
|---|---|---|---|---|
| merge area | +18.1 [+14.6, +21.0] | +8.8 [+2.2, +15.7] | +24.2 [+20.2, +27.6] | +18.9 [+11.6, +26.2] |
| merge 1 | +9.4 [+5.5, +14.2] | −0.7 [−8.0, +4.0] | +16.2 [+11.6, +21.4] | +4.8 [+0.0, +11.4] |
| merge 2 | +18.5 [+15.0, +22.2] | +10.9 [+3.0, +23.4] | +27.2 [+22.5, +31.7] | +18.9 [+10.3, +30.6] |
| edge 1 | −1110 [−1145, −1080] | −733 [−753, −707] | −730 [−760, −707] | −727 [−750, −700] |
| rest | +15.3 [+9.4, +22.8] | 0.0 [0, 0]† | +10.9 [+5.5, +18.8] | 0.0 [0, 0]† |
| without edge 1 | +17.8 [+14.4, +21.5] | +8.1 [+1.9, +15.1] | +23.3 [+18.5, +26.4] | +18.4 [+11.2, +25.6] |
| before | +5.5 | 0.0 | +10.6 | 0.0 |
| taper | 0.0† | 0.0† | 0.0 | 0.0† |
| hold | −63.4 [−71.2, −54.1] | −565 [−580, −540] | −61.9 | −550 |
| after | −14.0 | −28.6 | −3.2 | 0.0 |
| rest period | +19.9 [+15.7, +23.8] | +9.3 [+2.8, +17.6] | +23.9 | +16.3 [+8.6, +27.0] |

† The rule's median is 0, so the denominator is 1e-9 and the cell is not a real percentage.

### Other measures (v3.json = rows)
I added the plan's fixed sentence beside this table in the file.

| measure | lr 300 m | lr 600 m | grid 300 m | grid 600 m |
|---|---|---|---|---|
| delay | +2.3 [+1.2, +3.1] | +0.7 [+0.4, +1.0] | +0.9 [+0.1, +1.7] | +0.2 [−0.1, +0.5] |
| TTT (`N`) | +0.5 [+0.2, +0.7] | +0.2 [+0.1, +0.2] | +0.2 [−0.0, +0.4] | +0.0 [−0.0, +0.1] |
| served flow (`passed`) | +0.6 [+0.4, +0.8] | +0.0 | +0.2 [+0.1, +0.4] | +0.0 |
| `b45_step` | +5.3 [+2.7, +7.5] | −5.1 [−7.1, −3.2] | +5.3 [+2.6, +7.8] | −5.3 [−7.4, −3.1] |
| `ttc2` | +35.3 | +26.0 [+16, +39] | +42.7 | +30.0 [+18, +40] |
| `ttc15` | +24.7 | +0.0 [0, +40] | +38.4 | +10.0 [0, +40] |
| `sev3` | +21.8 | +0.0 [0, 0] | +24.2 | +0.0 [0, +20] |
| `vv_enc` | +12.1 [+8.5, +15.4] | −34.8 [−40.5, −26.8] | +17.7 | −20.8 [−28.2, −12.7] |

- **TTT is present.** `N` is vehicle-seconds over the fixed window, insertion queue included (`b_env.py:440-442`; `plant_sweep.py:30` labels it "ttt").
- **Collisions** (sum over 480 runs, 300 m / 600 m): learners 0/0, lr 1/0, grid 2/1, p333 1/0, no control 0/1. Teleports are 0 in all runs.
- **Jams** (v3.json only): +0.0 against both rules at 600 m. Against no control: +22.0 at 300 m and +42.9 at 600 m.

### Lane-end standing (rows; vehicle medians = v3.json)
Medians in veh-s at merge 1 / merge 2; vehicles in brackets.
- **300 m:** learners 128-192 / 436-513 (8-11 / 20-21); lr 274/900; grid 282/844; p333 232/905; no control 226/546 (14 / 26 vehicles).
- **600 m:** learners 5-10 / 21-32 (1 / 1-2); rules and p333 7-12 / 22-26; no control 110/412 (7 / 19 vehicles).

VV-D12 cut, 95 % lower bound (v3.json = rows):

| | v3w | lr | grid | p333 | no control |
|---|---|---|---|---|---|
| merge 1 | 81.8 % | 93.8 % | 94.6 % | 94.2 % | 36.3 % |
| merge 2 | 80.3 % | 96.5 % | 95.5 % | 96.7 % | 15.3 % |

"Removed" is false at both merges, because of no control.

### Does a rule beat no control on delay by 10 %? (95 %)
- **600 m:** lr +29.3 [+28.2, +30.0], grid +29.3 [+28.5, +30.0], p333 +30.3 [+29.6, +31.3]. **Yes**, all three.
- **300 m:** lr +27.5 [+26.5, +28.4], grid +28.3 [+27.3, +29.1], p333 +29.1 [+28.2, +29.9].
- v3.json prints only the point and the lower bound; the upper bounds are from the rows.

### Things that look odd, explained where I could
1. **Edge-1 percentages around −700 % to −2,340 %:** the rules have 2-3 samples per run there, against about 25 for v3w, at both lengths. In V1 every edge-1 sample is in the hold period; v3w's are mostly ALKS followers. At 600 m this is the largest deficit (+22.4 and +22.6 samples per run). That roughly equals the whole `ttc_net` gap against lr (98.3 vs 76.5), but medians don't add, so that last point is an inference. The deciding WORSE rests on lr alone (98.75 % upper bound −11.4).
2. **"rest" at 600 m and the taper period read 0 [0, 0]** because the opponent's median is 0. That is not a tie.
3. **`ttc15` and `sev3` at 600 m** are 0 in 40-54 % of controlled runs. With medians of 1-2 events the percentages move in coarse steps.
4. **`b45_step` and `vv_enc` change sign** between 300 m and 600 m against both rules.
5. **`c15_cap_share_600` = 0.0 is a real zero:** 0 of about 32 M decisions per learner, while grid hit the cap 1,566 times and p333 2,991. I did not trace what column 15 encodes.
6. **No control at 600 m, seed 7,492,030, has `ttc_net` = 0.** All 9 arms are light on that seed and the row looks complete. I did not investigate further.
7. **v3w's cut is not comparable with the rules' (post hoc).** Its row uses the median of the per-seed mean of the 5 learners. With these heavy-tailed counts, that median is above every single learner's median. Per learner the cuts are 92.6-97.1 %.
8. **No close-following sample appears on edges 4 or 5** in any of the 8,640 runs.

Files are in /home/catalin/work/phd/v5b1_runs/vv_post/printed:
- printed_tables.md
- recomputed.json
- compare_v3.tsv
- printed.py
- tables.py
- time.log (left over from timing the script; I could not delete it)