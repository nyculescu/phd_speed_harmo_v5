## V1 visual check: MET. All 40 sampled seconds are real closing approaches; none is a non-event.

All 40 counted seconds are real closing approaches, each with TTC below 3 s (gap + minGap). 38 have the leader on the follower's own lane. 2 have it on the next lane of the follower's route (S13: r2_0→rj2_0, S35: 3_0→4a_1). Nothing turned up of the other kinds: no wrong or cross-lane leader, no leader off the route, no standing pair that was not closing, no count at the moment of a lane change, no teleport and no 1-Hz artefact.

- **Bound:** 0/40 gives a one-sided 95 % upper bound of **7.2 %** (two-sided 95 %: 8.8 %), which is the plan's "about 7 %".
- **Overall V1:** v1.json shows the wiring, definition and twin checks all empty ("CHECKS PASS; visual check pending"). By §2 V1 "Outcome", V1 therefore reads **MET**. I did not re-run those three checks.

**Draw reproduced:** the same sorted pool (15,684 samples from 18 traced runs) with rng 20261115 gives exactly v1.json's 40 samples. The field order [t, v, w, fk, wk, froad, flane, fpos, flen, wroad, wlane, wpos, wlen, gap, mingap, s, sl] matches `VV.hit` in vv_merge.py and the unpacking in read_vv.py `v1_row`. The input files pass their sha256 checks: both s6_rows.jsonl, v1.json and the 18 merge logs.

## Per sample
Gap means gap + minGap from positions, in metres. Speeds are follower vs leader, in m/s. "acc" = 3a_0 or 4a_0. Lane length is 294.72 m at 300 m and 594.72 m at 600 m; the lane-end zone is its last 30 m.

| # | run | t | location | period | verdict | evidence |
|---|---|---|---|---|---|---|
| S00 | L300 lr400_16_1 7493001 | 1608 | 4a_1 @167.3 (main) | rest | EVENT, queue approach after own merge | car merged 4a_0→4a_1 at 1603.0 from standstill behind the standing ALKS (merge-log lead); gap 6.75→4.42; 1.71 vs 0.00; TTC 2.58 |
| S01 | L300 lr400_16_1 7493001 | 1553 | 4a_1 @276.9 (main) | rest | EVENT, stop-and-go creep | 3.27 vs 0.17; gap 4.22; same pair since 1523.6 (leader merged directly in front, merge log); single counted second; t+1 follower moved 1.81 m, so gap shrank ≥0.2 m if leader accel ≤2.6 m/s² (inference) |
| S02 | E30 nc 7489161 | 1590 | 4a_0 @11.0 (acc start) | rest | EVENT, queue-tail approach | ALKS in from :d_0_0; gap 13.9→9.6→6.1→4.9; 2.66 vs 0.39; TTC 2.69 |
| S03 | L300 w1u500 7493001 | 1428 | 4a_1 @116.5 (main) | rest | EVENT | 11.2 vs 0.96; gap 36.3→24.8→16.1→10.4→7.1 (5 counted s); TTC 2.43 |
| S04 | L300 lr400_16_1 7493001 | 1567 | 4a_0 @232.2 | rest | EVENT, pair braking into acc queue | from 16 m/s, leader brakes first; gap 19→7.26→4.75→2.9; TTC 2.62 |
| S05 | L600 nc 7493001 | 1223 | 3a_0 @556.1 (39 m before end) | rest | EVENT, leader standing at lane end | ALKS from 17 m/s onto car at 567.2 (zone), 0.16; gap 24→16→10.5→6.6→5.7; TTC 2.35 |
| S06 | L300 nc 7493001 | 1503 | 3_0 @1047.6 (main) | rest | EVENT | 13.1 vs 3.8; gap 27.8→19.3→12.8→8.5; TTC 2.99 |
| S07 | L300 nc 7493000 | 1375 | 4a_0 @40.6 | rest | EVENT | gap 7.2→5.0→3.6→2.7; 4.02 vs 2.15; TTC 2.67 |
| S08 | E30 w1u500 7489161 | 1448 | 4a_0 @14.4 | rest | EVENT, queue-tail approach | 12.6 onto ALKS standing at 47.7; gap 29.3→18.9→11.8→7.4; TTC 2.37 |
| S09 | E30 nc 7489161 | 1135 | 3a_0 @156.7 | rest | EVENT, stop-and-go | 4.07 vs 0.33; gap 12.1→8.15→6.1; TTC 2.18 |
| S10 | L600 lr400_16_1 7493000 | 1311 | 4a_0 @548.1 | rest | EVENT, queue creep | 1.87 vs 0.31; gap 5.57→3.37→2.96; TTC 2.16; leader merged out 1.7 s later |
| S11 | E30 lr400_16_1 7489161 | 1065 | 3a_0 @258.5 | rest | EVENT, leader standing at lane end | truck from 16 m/s onto car at 265.8 (zone), 0.0; gap 14.3→7.7→3.74→2.76; TTC 1.42 |
| S12 | L300 lr400_16_1 7493001 | 1244 | 3a_0 @162.1 | rest | EVENT | car 3.12 (from 9.3) onto ALKS stopped at 170.1 (mid-lane queue); gap 15.9→8.5→4.0→2.7; TTC 1.28 |
| S13 | L300 w1u500 7493000 | 1046 | r2_0 @387.9 → leader rj2_0 @6.4 | rest | EVENT, next lane | 4.19 vs 0.25; SUMO gap rebuilds with a 0.10 m internal lane (as all 174 r2→rj2 samples); 6 counted s from 18 m/s; TTC 1.34 |
| S14 | E30 w1u500 7489161 | 1702 | 3a_1 @178.7 (main) | rest | EVENT, stop-and-go re-approach | pair counted 1693-96 (gap 29→7), not 1697-1701; at t 6.72 vs 3.44, gap 8.11, TTC 2.47; next second not observable, so closing is shown by dv at t only |
| S15 | L600 w1u500 7493001 | 1441 | 4a_0 @548.8 | rest | EVENT | from 17 m/s onto ALKS standing at 563.0 (1.8 m short of zone); gap 21.5→14.7→9.2→6.3; TTC 1.97 |
| S16 | E30 nc 7489160 | 1080 | 4a_0 @21.8 | rest | EVENT | 7.0 onto ALKS standing at 40.5; gap 33.5→22.2→14.1→8.8→5.8; TTC 2.18 |
| S17 | E30 w1u500 7489160 | 1000 | 4a_0 @29.5 | rest | EVENT | 2.65 vs 0.19; gap 11.9→9.0→6.0→4.8; TTC 2.44 |
| S18 | E30 nc 7489161 | 1062 | 3a_0 @168.8 | rest | EVENT | 8.83 vs braking truck 1.66; gap 24.6→16.8→10.4→6.6; TTC 2.34 |
| S19 | L300 w1u500 7493000 | 457 | 3a_1 @193.4 (main) | before | EVENT | leader (ramp vehicle) merged at 446.2 directly ahead of the follower (merge-log lag), 10.8 s earlier; 12.68 vs 5.10; gap 15.7→10.1; TTC 2.07 |
| S20 | L300 nc 7493000 | 1140 | 4a_0 @233.4 | rest | EVENT | 7.29 vs truck 1.50; gap 21.7→14.2→9.8→6.8→4.6; TTC 2.45 |
| S21 | L300 nc 7493001 | 1284 | 3a_0 @33.1 | rest | EVENT | 2.22 onto truck standing at 54.6; gap 14.2→8.6→5.5→3.9; TTC 2.48 |
| S22 | E30 w1u500 7489161 | 1112 | 3a_1 @87.0 (main) | rest | EVENT | 8.41 vs 4.63; gap 13.7→9.1→6.2; TTC 2.41 |
| S23 | E30 nc 7489161 | 1181 | 4a_0 @92.1 | rest | EVENT | truck 7.95 vs 3.09; gap 16.8→11.7→8.2→5.6; 1182 not counted (TTC 3.17), 1183 counted |
| S24 | L300 nc 7493000 | 1495 | r2_0 @332.2 | rest | EVENT, ramp queue | truck 9.61 vs 3.06; gap 35.2→24.4→16.5→11.2; TTC 2.53 |
| S25 | L600 nc 7493001 | 1683 | 4a_1 @101.7 (main) | rest | EVENT | 5.55 vs 1.89; gap 21.9→15.4→10.8; TTC 2.95 |
| S26 | E30 nc 7489161 | 1195 | 2_0 @475.0 (main, 23 m before node m) | rest | EVENT | 2.93 vs 0.59; gap 22.1→14.9→9.7→6.6; TTC 2.81 |
| S27 | L300 lr400_16_1 7493001 | 1450 | 3_0 @1117.3 (main) | rest | EVENT | 9.93 vs 1.57; gap 27.5→17.6→10.8→6.9; TTC 2.11 |
| S28 | E30 nc 7489161 | 1180 | r_0 @213.6 | rest | EVENT, ramp queue tail | truck 18.4 vs truck 1.19; gap 50.0→34.3→22.0→13.0; TTC 2.91 |
| S29 | L300 nc 7493001 | 1251 | 4a_0 @192.5 | rest | EVENT, stop-and-go creep | 3.37 vs 1.23; gap 7.5→5.9→3.85; single counted second |
| S30 | L600 nc 7493001 | 1569 | 4a_0 @526.4 | rest | EVENT, end of approach | truck from 16 m/s; gap 9.6→5.74→3.07, then 3.08 at t+1 (stops 0.57 m past minGap); 1.57 vs 0.28 at t; TTC 2.39 |
| S31 | L300 w1u500 7493000 | 940 | 3a_0 @107.3 | rest | EVENT | 3.29 vs 0.93; gap 17.9→10.5→6.0→5.6; TTC 2.55 |
| S32 | E30 lr400_16_1 7489161 | 1196 | 3a_1 @64.7 (main) | rest | EVENT | 12.9 vs 4.11; gap 24.3→16.7; TTC 2.76 |
| S33 | L300 lr400_16_1 7493000 | 954 | 3a_1 @95.3 (main) | rest | EVENT | 13.5 vs 5.17; gap 33.0→23.2→16.2; TTC 2.78 |
| S34 | L300 nc 7493000 | 1249 | 4a_0 @107.1 | rest | EVENT | truck 13.9 (from 23) onto car standing at 141.6; gap 45→30.4→18.6→9.6→4.3; TTC 2.26 |
| S35 | E30 lr400_16_1 7489160 | 1346 | 3_0 @1178.5 → leader 4a_1 @7.2 | rest | EVENT, next lane | SUMO gap rebuilds with a 2.98 m internal lane (as all 188 3→4a samples); 12.8 vs 5.04; same leader on 4a_1 at 1348-49, gap 9.4→5.9 |
| S36 | E30 nc 7489161 | 988 | 3a_0 @180.1 | after | EVENT | car 11.7 onto ALKS standing at 202.5; gap 48→31.6→18.2→8.8→3.8; TTC 1.57 |
| S37 | L300 lr400_16_1 7493001 | 1218 | 3a_0 @143.8 | rest | EVENT, queue creep | 1.73 onto truck stopped at 163.2; gap 4.89→3.29→2.52, then stands at minGap 2.50; TTC 1.90 |
| S38 | E30 lr400_16_1 7489160 | 532 | 4a_0 @178.8 | taper | EVENT | 7.30 vs 3.40; gap 19.8→13.1→8.3→4.8; TTC 2.12 |
| S39 | E30 w1u500 7489160 | 1408 | 4a_0 @248.9 | rest | EVENT | 2.07 onto car standing at 259.2 (5.5 m short of zone); gap 21→13.2→8.5→6.0→5.4; TTC 2.91 |

**The 40 samples at a glance:**
- **Follower location:** 27 on an acceleration lane or ramp (24 on 3a_0/4a_0, 3 on r/r2), 13 on main lanes.
- **Period:** rest 37, before 1, after 1, taper 1, hold 0.
- **Speed band:** lo 19, mid 11, hi 10.
- **Follower type:** ALKS 23, car 10, truck 7.
- **Flags:** leader standing in the lane-end zone 2 (S05, S11); merged in the last 5 s 1 (S00); edge 1: none.

## Checks across samples (post hoc, not in the plan)
- **Acceleration-lane samples:** for all 24 samples on 3a_0/4a_0, the separate 1-Hz lane trace (`end_trace`) shows the counted leader as the nearest vehicle ahead, with the same positions and speeds to 1e-6.
- **Cross-junction samples:** all 620 samples whose leader is on the next normal lane (all 18 runs) give back the SUMO gap from positions with one fixed internal-lane length per transition (spread < 1e-9 m): 1→2, r→rj, r2→rj2 0.10 m; 2→3a, 3→4a 2.98 m; rj→3a, rj2→4a 9.82 m. This extends the plan's same-lane gap check to those samples. The 215 samples with a vehicle on an internal lane are not covered.
- **Teleports and collisions:** teleports 0 and collisions 0 in all 18 traced runs. No position jumps in any window.
- **Lane changes:** no sample was counted at the moment of a move. Merges do create close following that is counted later (S00 own merge 5 s before; S19 leader merged 10.8 s before). That is plant behaviour under instantaneous lane changes, already a stated limit.

## Classification over all traced runs (v1.json 'runs', 18 runs, 15,684 samples, pooled, descriptive)
| class | n | share |
|---|---|---|
| follower on a main lane | 6,648 | 42.4 % |
| follower on acceleration lane or ramp | 9,036 | 57.6 % |
| same lane | 14,615 | 93.2 % |
| next lane | 1,069 | 6.8 % |
| cross-lane or off route | 0 | 0 |
| leader standing in lane-end zone | 1,035 | 6.6 % |
| either vehicle merged in last 5 s | 530 | 3.4 % |
| speed lo / mid / hi | 5,645 / 5,568 / 4,471 | 36.0 / 35.5 / 28.5 % |
| period rest / hold / before / after / taper | 13,253 / 929 / 699 / 676 / 127 | 84.5 / 5.9 / 4.5 / 4.3 / 0.8 % |
| road group 4a / 3a / 3 / ramp2 / junction / 2 / 1 / ramp1 | 9,445 / 3,272 / 1,247 / 1,089 / 215 / 203 / 108 / 105 | 60.2 / 20.9 / 8.0 / 6.9 / 1.4 / 1.3 / 0.7 / 0.7 % |

Main vs acc/ramp by run set: E30 replay 3,388 / 4,589, L300 2,518 / 3,353, L600 742 / 1,094.

**Edge-1 samples:** 108 in total, all in the **hold** period. All sit at 2,885-2,993 m of the 3,000-m edge (median 2,968 m), so within the last 115 m before edge 2, where the 30 km/h slowdown is. Median follower speed is about 13 m/s. By arm:

| arm | edge-1 samples per run |
|---|---|
| w1u500 | 16, 18 (E30); 8, 27 (L300); 12, 12 (L600) |
| lr400_16_1 | 0-6 |
| nc | 0-3 |

No cause is assumed. None fell in the 40-sample draw (about 0.3 expected).

## Limits and uncertainty
- **What the bound covers:** the pooled counted samples of the 18 traced runs only: arms w1u500, lr400_16_1 and nc; smoke seeds 7,493,000-001 at 300 and 600 m; stored E30 seeds 7,489,160-161. Runs with more samples weigh more. It does not cover the 9-arm screen or E30's other arms.
- **What can be reconstructed:** the tracer logs only counted seconds. Off the acceleration lanes a pair is seen only in counted seconds, so for 7 samples the gap one second later is not observable from positions:
  - S13, S35: their t+1 seconds were counted, with a smaller SUMO gap.
  - S00, S25, S26: the gap falls over the counted seconds leading into t.
  - S01: rests on an inference that the ALKS acceleration is at most 2.6 m/s² (`ALKS_DEFAULTS` in fleet.py). I did not check whether the arm's speed mode keeps that limit.
  - S14: closing is shown only by dv > 0 at t.

  I applied the plan's definition, where closing means closing at the counted second. If "observed closing over the next second" were required instead, S14 would be UNCLEAR, which is still not a non-event found.
- **Interpretation point for the committee (post hoc):** 19/40 samples are below 5 m/s. Four are creeps inside standing queues (S01, S10, S29, S37: 1.7-3.4 m/s, bumper gaps 3.3-5.9 m). They meet the definition because the gap is closing. They are not "standing, not closing": with gap + minGap ≥ 2.5 m, a sample needs a closing speed of at least 0.83 m/s to count. So part of `ttc_net` is low-speed queue creep, which this exposure measure counts by design.
- **Rules followed, with two small departures:**
  - Nothing in the repo or run folders was modified, and no simulations were run.
  - Two hash-list files were written to the session scratchpad.
  - A few sub-second read-only Python prints ran without `nice`, though always one process at a time.
  - A `__pycache__` folder is left in the output folder because the delete was denied.

## Files
All in /home/catalin/work/phd/v5b1_runs/vv_post/v1_visual/:
- v1_visual.py (reconstruction and plots)
- s00.png … s39.png (position, speed and gap against time, ±10 s; I viewed all 40)
- evidence.json (per-sample reconstruction and internal-lane lengths)
- verdicts.csv (40 rows: location, period, TTC, relation, verdict, kind, evidence)