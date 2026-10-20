> **V100 bug re-run** of screen D2: meter signal d2 -> continuous (meter phase recomputed with the current cycle on every rate change (greens skipped, reds up to 322 s); fixed by the continuous signal rule (v5b/d1/meter_signal.py)). Same seeds, arms, grids, tuning and decision rules. Original result `/home/catalin/work/phd/v5b1_runs/screen_d2/v92/result.json` (code 72ba8f276c, decision STOP). Report both outcomes.

# Screen D2 result: **CONTINUE**

Page `docs/research/protocols/screen_D2_incidents.md` (sha256 a66e712c15d1), code 85f7d34da9. G = 35 controllers; IP / OR / ORX choose among G x {stay, back to N at clearance} (70 actions, A12). Metric: door-to-door delay (s) incl. origin and ramp (meter) queue; served = arrivals in the control period (veh/h); TTT ctrl = veh h in [0, control end].

## Tool checks (hindsight arms on the tool-check seeds)

| cell | best arm | its median | NC median | rel (NC-best)/NC | CI diff (s) | T0 | T4: N_t / best fixed | T4 rel [CI] | T4 |
|---|---|---|---|---|---|---|---|---|---|
| slow_q1600 | OR | 108.1 | 332.1 | 56.6 % | [163.3, 218.0] | PASS | c1900 / f70_8 | 32.1 [21.8, 48.4] | PASS |
| slow_q2000 | OR | 310.4 | 537.9 | 41.3 % | [177.6, 242.6] | PASS | f10_8 / f70_8 | 37.9 [27.8, 51.0] | PASS |
| block_q1600 | OR | 172.2 | 306.3 | 46.6 % | [72.1, 165.2] | PASS | c1900 / f70_8 | 23.4 [4.6, 48.1] | PASS |
| block_q2000 | OR | 324.3 | 527.4 | 35.5 % | [103.0, 232.3] | PASS | f10_8 / f20_12 | 28.4 [22.2, 33.7] | PASS |

T0 and T4 must pass in every incident cell (T4: Addendum D2-A5). T1 teleport runs per cell: none_q1600 0/720, slow_q1600 0/2120, block_q1600 0/2120, none_q2000 0/720, slow_q2000 0/2120, block_q2000 0/2120 (PASS). T3 PASS. Tool-check arms: {'1600': {'N': 'c1900', 'FX': 'c1900', 'FB': 'f70_8', 'IP': {'slow': 'c800+back', 'block': 'f40_12'}}, '2000': {'N': 'f10_8', 'FX': 'c2300', 'FB': 'f70_8', 'IP': {'slow': 'f70_8', 'block': 'f40_12'}}}

## Tuning

- q = 1600: N = c1900, FX = c2100, FB = f70_8, IP = {'slow': 'f70_8', 'block': 'f40_8'}
- q = 2000: N = c1800, FX = c1800, FB = f70_8, IP = {'slow': 'f70_6+back', 'block': 'f40_10'}
- at a grid edge (report only): ['1600:FB=f70_8 (K_F=70)', '1600:IP_slow=f70_8 (K_F=70)', '2000:FB=f70_8 (K_F=70)', '2000:IP_slow=f70_6+back (K_F=70, n_crit=6)']

## Headroom HD_f = (f - OR) / f, % [95 % CI] (Rule 5 and Addendum D2-A1)

A cell passes only if HD >= 10 % with CI lower bound > 0 against every fallback (FX, FB, IP), with and without seeds that have an invalid OR/FX/FB/IP run, BOTH with the page's OR (per-seed best run, scored on that run) and with the cross-fitted ORX (target picked on the SUMO-RNG replicate, scored on the main run).

| cell | OR used | n | median | vs FX | vs FB | vs IP | binding | inv seeds | pass all | pass valid | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| slow_q1600 | OR (page) | 50 | 123.6 | 57.8 [48.1, 62.3] | 37.8 [26.8, 42.8] | 30.8 [26.0, 38.1] | IP | 0 | yes | yes | no |
| slow_q1600 | ORX (cross-fit) | 50 | 213.2 | 23.5 [12.4, 32.2] | -15.4 [-32.2, 10.1] | -4.7 [-19.8, 11.4] | FB | 0 | no | no | no |
| slow_q1600 | **cell** | | | | | | | | | | **no** |
| slow_q2000 | OR (page) | 50 | 271.5 | 41.3 [37.0, 46.0] | 21.7 [18.0, 30.6] | 10.4 [9.3, 28.9] | IP | 0 | yes | yes | no |
| slow_q2000 | ORX (cross-fit) | 50 | 338.0 | 26.6 [11.9, 34.3] | 1.3 [-16.3, 7.7] | 3.8 [1.2, 8.5] | FB | 0 | no | no | no |
| slow_q2000 | **cell** | | | | | | | | | | **no** |
| block_q1600 | OR (page) | 50 | 194.0 | 30.5 [24.0, 43.4] | 24.8 [16.7, 30.6] | 32.6 [27.2, 36.8] | FB | 0 | yes | yes | yes |
| block_q1600 | ORX (cross-fit) | 50 | 231.2 | 23.6 [14.6, 30.4] | 17.4 [11.4, 28.3] | 23.8 [15.3, 31.4] | FB | 0 | yes | yes | yes |
| block_q1600 | **cell** | | | | | | | | | | **yes** |
| block_q2000 | OR (page) | 50 | 345.5 | 26.8 [20.3, 32.9] | 20.9 [17.7, 22.9] | 10.5 [7.9, 13.8] | IP | 0 | yes | yes | no |
| block_q2000 | ORX (cross-fit) | 50 | 370.3 | 24.3 [17.3, 29.1] | 16.0 [10.4, 20.0] | 6.1 [1.9, 9.4] | IP | 0 | no | no | no |
| block_q2000 | **cell** | | | | | | | | | | **no** |

## Operating map (median delay s / served veh/h / TTT ctrl veh h; invalid runs)

| cell | OR | IP | N | FX | FB | NC | ORX | controllers | OR picks (top 3) |
|---|---|---|---|---|---|---|---|---|---|
| slow_q1600 | 123.6 / 1370 / 17.1 | 193.8 / 1150 / 20.4 | 299.0 / 982 / 23.0 | 289.0 / 990 / 22.6 | 180.9 / 1178 / 19.5 | 301.4 / 954 / 23.3 | 213.2 / 1136 / 20.5 | {'N': 'c1900', 'FX': 'c2100', 'FB': 'f70_8', 'IP': 'f70_8'} | {'c1000+back': 16, 'f70_6+back': 5, 'f70_12+back': 4} |
| slow_q2000 | 271.5 / 1362 / 29.5 | 361.0 / 1246 / 32.9 | 480.8 / 1020 / 35.5 | 480.8 / 1020 / 35.5 | 327.2 / 1192 / 31.9 | 501.0 / 952 / 36.4 | 338.0 / 1208 / 31.9 | {'N': 'c1800', 'FX': 'c1800', 'FB': 'f70_8', 'IP': 'f70_6+back'} | {'c1000+back': 13, 'c800+back': 6, 'f70_12+back': 4} |
| block_q1600 | 194.0 / 1160 / 20.8 | 282.8 / 990 / 24.7 | 303.6 / 954 / 23.7 | 299.1 / 946 / 23.3 | 260.3 / 1038 / 23.5 | 289.0 / 942 / 22.8 | 231.2 / 1100 / 22.0 | {'N': 'c1900', 'FX': 'c2100', 'FB': 'f70_8', 'IP': 'f40_8'} | {'f40_12': 12, 'f70_12': 7, 'f20_12': 6} |
| block_q2000 | 345.5 / 1210 / 32.5 | 398.1 / 1160 / 34.9 | 496.1 / 980 / 36.2 | 496.1 / 980 / 36.2 | 421.9 / 1056 / 36.2 | 513.2 / 938 / 37.8 | 370.3 / 1138 / 33.3 | {'N': 'c1800', 'FX': 'c1800', 'FB': 'f70_8', 'IP': 'f40_10'} | {'f40_12': 11, 'f20_12': 11, 'f70_12': 6} |

Noise and selection (report only, Addendum D2-A1): IP main vs replicate |rel diff| median / p90; HD(OR) - HD(ORX) per fallback, points:

- slow_q1600: 21.8 / 44.7 %; FX 34.3, FB 53.3, IP 35.5
- slow_q2000: 15.2 / 72.8 %; FX 14.8, FB 20.4, IP 6.6
- block_q1600: 12.7 / 27.8 %; FX 6.9, FB 7.4, IP 8.8
- block_q2000: 9.4 / 23.3 %; FX 2.6, FB 4.8, IP 4.4

Emergency braking / stops, median per run (Addendum D2-A8, report only): meter edge 2 / bottleneck edges 4+5 / edges 4+5 during the incident:

- slow_q1600: OR 15.5 / 4.0 / 4.0; IP 11.0 / 4.0 / 4.0; N 31.0 / 4.0 / 4.0; FX 42.0 / 4.0 / 4.0; FB 20.0 / 3.5 / 3.5; NC 0.0 / 2.0 / 2.0; ORX 14.0 / 4.0 / 4.0
- slow_q2000: OR 7.0 / 4.0 / 4.0; IP 6.0 / 4.0 / 4.0; N 8.0 / 4.0 / 4.0; FX 8.0 / 4.0 / 4.0; FB 9.5 / 4.0 / 4.0; NC 0.0 / 2.0 / 2.0; ORX 6.0 / 4.0 / 4.0
- block_q1600: OR 16.0 / 4.0 / 4.0; IP 12.0 / 4.0 / 4.0; N 26.5 / 4.0 / 4.0; FX 38.0 / 4.0 / 4.0; FB 18.0 / 4.0 / 4.0; NC 0.0 / 4.0 / 4.0; ORX 16.5 / 4.0 / 4.0
- block_q2000: OR 7.0 / 4.0 / 4.0; IP 7.0 / 4.0 / 4.0; N 8.0 / 4.0 / 4.0; FX 8.0 / 4.0 / 4.0; FB 11.0 / 5.0 / 5.0; NC 0.0 / 2.5 / 2.5; ORX 7.0 / 4.0 / 4.0

No-incident cell (report only; IP = OR = N):

- none_q1600 (n 50): N c1900 49.4 / 1424 / 10.1, FX c2100 82.3 / 1334 / 10.7, FB f70_8 122.9 / 1308 / 16.0, NC NC 268.5 / 998 / 20.7
- none_q2000 (n 50): N c1800 142.2 / 1638 / 19.2, FX c1800 142.2 / 1638 / 19.2, FB f70_8 262.6 / 1388 / 26.8, NC NC 487.9 / 960 / 35.2
