# Screen D2 result: **STOP**

Page `docs/research/protocols/screen_D2_incidents.md` (sha256 a66e712c15d1), code 72ba8f276c. G = 35 controllers; IP / OR / ORX choose among G x {stay, back to N at clearance} (70 actions, A12). Metric: door-to-door delay (s) incl. origin and ramp (meter) queue; served = arrivals in the control period (veh/h); TTT ctrl = veh h in [0, control end].

## Tool checks (hindsight arms on the tool-check seeds)

| cell | best arm | its median | NC median | rel (NC-best)/NC | CI diff (s) | T0 | T4: N_t / best fixed | T4 rel [CI] | T4 |
|---|---|---|---|---|---|---|---|---|---|
| slow_q1600 | OR | 120.3 | 332.1 | 55.0 % | [158.6, 223.4] | PASS | c1900 / f70_8 | 33.1 [17.4, 41.2] | PASS |
| slow_q2000 | OR | 247.4 | 537.9 | 46.3 % | [198.5, 297.8] | PASS | c1700 / f70_8 | 32.0 [17.4, 37.8] | PASS |
| block_q1600 | OR | 189.4 | 306.3 | 39.8 % | [72.2, 168.6] | PASS | c1900 / f70_8 | 15.6 [5.4, 39.1] | PASS |
| block_q2000 | OR | 330.9 | 527.4 | 32.2 % | [121.6, 248.8] | PASS | c1700 / f70_8 | 16.3 [4.4, 39.0] | PASS |

T0 and T4 must pass in every incident cell (T4: Addendum D2-A5). T1 teleport runs per cell: none_q1600 0/720, slow_q1600 0/2120, block_q1600 0/2120, none_q2000 1/720, slow_q2000 1/2120, block_q2000 0/2120 (PASS). T3 PASS. Tool-check arms: {'1600': {'N': 'c1900', 'FX': 'c1900', 'FB': 'f70_8', 'IP': {'slow': 'c800+back', 'block': 'f40_8'}}, '2000': {'N': 'c1700', 'FX': 'c2300', 'FB': 'f70_8', 'IP': {'slow': 'c800+back', 'block': 'f40_12'}}}

## Tuning

- q = 1600: N = c1900, FX = c2100, FB = f70_10, IP = {'slow': 'c1000+back', 'block': 'f40_12'}
- q = 2000: N = c1800, FX = c1800, FB = f40_10, IP = {'slow': 'c800+back', 'block': 'f40_10'}
- at a grid edge (report only): ['1600:FB=f70_10 (K_F=70)', '1600:IP_block=f40_12 (n_crit=12)']

## Headroom HD_f = (f - OR) / f, % [95 % CI] (Rule 5 and Addendum D2-A1)

A cell passes only if HD >= 10 % with CI lower bound > 0 against every fallback (FX, FB, IP), with and without seeds that have an invalid OR/FX/FB/IP run, BOTH with the page's OR (per-seed best run, scored on that run) and with the cross-fitted ORX (target picked on the SUMO-RNG replicate, scored on the main run).

| cell | OR used | n | median | vs FX | vs FB | vs IP | binding | inv seeds | pass all | pass valid | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| slow_q1600 | OR (page) | 50 | 137.0 | 52.4 [46.7, 58.3] | 42.8 [35.6, 49.2] | 39.9 [25.8, 50.5] | IP | 0 | yes | yes | no |
| slow_q1600 | ORX (cross-fit) | 50 | 213.0 | 26.8 [14.3, 34.6] | 11.5 [-3.5, 23.1] | 1.2 [0.0, 10.6] | FB | 0 | no | no | no |
| slow_q1600 | **cell** | | | | | | | | | | **no** |
| slow_q2000 | OR (page) | 50 | 267.6 | 39.1 [36.3, 45.5] | 32.3 [24.4, 40.9] | 5.0 [4.0, 7.4] | IP | 0 | no | no | no |
| slow_q2000 | ORX (cross-fit) | 50 | 365.3 | 17.2 [8.1, 28.0] | 8.9 [1.3, 18.7] | -5.1 [-36.8, 0.0] | IP | 0 | no | no | no |
| slow_q2000 | **cell** | | | | | | | | | | **no** |
| block_q1600 | OR (page) | 50 | 207.9 | 28.4 [23.0, 37.3] | 24.3 [19.6, 30.4] | 12.1 [7.7, 17.6] | IP | 0 | yes | yes | no |
| block_q1600 | ORX (cross-fit) | 50 | 242.4 | 15.2 [9.8, 22.9] | 11.9 [4.0, 18.2] | 0.0 [-0.6, 2.1] | IP | 0 | no | no | no |
| block_q1600 | **cell** | | | | | | | | | | **no** |
| block_q2000 | OR (page) | 50 | 339.8 | 23.9 [17.8, 30.5] | 19.4 [15.2, 24.6] | 15.6 [12.1, 19.6] | IP | 0 | yes | yes | no |
| block_q2000 | ORX (cross-fit) | 50 | 425.0 | 12.5 [7.9, 17.4] | 10.6 [-1.8, 16.0] | 1.0 [-0.1, 8.3] | FB | 0 | no | no | no |
| block_q2000 | **cell** | | | | | | | | | | **no** |

## Operating map (median delay s / served veh/h / TTT ctrl veh h; invalid runs)

| cell | OR | IP | N | FX | FB | NC | ORX | controllers | OR picks (top 3) |
|---|---|---|---|---|---|---|---|---|---|
| slow_q1600 | 137.0 / 1326 / 18.0 | 242.2 / 1038 / 20.9 | 299.0 / 982 / 23.0 | 289.0 / 990 / 22.6 | 242.3 / 1072 / 22.1 | 301.4 / 954 / 23.3 | 213.0 / 1116 / 20.0 | {'N': 'c1900', 'FX': 'c2100', 'FB': 'f70_10', 'IP': 'c1000+back'} | {'c1000+back': 9, 'c800+back': 7, 'f40_6+back': 4} |
| slow_q2000 | 267.6 / 1336 / 30.3 | 281.2 / 1296 / 30.9 | 480.8 / 1020 / 35.5 | 480.8 / 1020 / 35.5 | 384.7 / 1152 / 33.4 | 501.0 / 952 / 36.4 | 365.3 / 1136 / 32.8 | {'N': 'c1800', 'FX': 'c1800', 'FB': 'f40_10', 'IP': 'c800+back'} | {'c1000+back': 9, 'c800+back': 8, 'f40_12+back': 4} |
| block_q1600 | 207.9 / 1146 / 20.7 | 251.8 / 1060 / 22.3 | 303.6 / 954 / 23.7 | 299.1 / 946 / 23.3 | 282.3 / 1010 / 24.7 | 289.0 / 942 / 22.8 | 242.4 / 1052 / 22.7 | {'N': 'c1900', 'FX': 'c2100', 'FB': 'f70_10', 'IP': 'f40_12'} | {'f40_12': 12, 'f10_12': 8, 'f20_12': 5} |
| block_q2000 | 339.8 / 1174 / 32.0 | 417.7 / 1098 / 35.5 | 496.1 / 980 / 36.2 | 496.1 / 980 / 36.2 | 435.0 / 1054 / 36.3 | 513.2 / 938 / 37.8 | 425.0 / 1092 / 34.2 | {'N': 'c1800', 'FX': 'c1800', 'FB': 'f40_10', 'IP': 'f40_10'} | {'f40_12': 11, 'f20_12': 7, 'f70_8': 5} |

Noise and selection (report only, Addendum D2-A1): IP main vs replicate |rel diff| median / p90; HD(OR) - HD(ORX) per fallback, points:

- slow_q1600: 37.6 / 121.1 %; FX 25.6, FB 31.3, IP 38.7
- slow_q2000: 13.3 / 75.4 %; FX 21.9, FB 23.3, IP 10.0
- block_q1600: 11.8 / 37.1 %; FX 13.2, FB 12.4, IP 12.1
- block_q2000: 9.2 / 25.5 %; FX 11.3, FB 8.8, IP 14.6

Emergency braking / stops, median per run (Addendum D2-A8, report only): meter edge 2 / bottleneck edges 4+5 / edges 4+5 during the incident:

- slow_q1600: OR 13.0 / 4.0 / 4.0; IP 11.5 / 4.0 / 4.0; N 31.0 / 4.0 / 4.0; FX 42.0 / 4.0 / 4.0; FB 27.0 / 3.0 / 3.0; NC 0.0 / 2.0 / 2.0; ORX 14.0 / 4.0 / 4.0
- slow_q2000: OR 6.0 / 4.0 / 4.0; IP 5.0 / 4.0 / 4.0; N 8.0 / 4.0 / 4.0; FX 8.0 / 4.0 / 4.0; FB 13.0 / 3.0 / 3.0; NC 0.0 / 2.0 / 2.0; ORX 7.0 / 4.0 / 4.0
- block_q1600: OR 17.0 / 4.0 / 4.0; IP 18.0 / 4.0 / 4.0; N 26.5 / 4.0 / 4.0; FX 38.0 / 4.0 / 4.0; FB 32.0 / 4.0 / 4.0; NC 0.0 / 4.0 / 4.0; ORX 16.0 / 4.0 / 4.0
- block_q2000: OR 9.5 / 4.0 / 4.0; IP 9.0 / 4.0 / 4.0; N 8.0 / 4.0 / 4.0; FX 8.0 / 4.0 / 4.0; FB 14.5 / 5.0 / 5.0; NC 0.0 / 2.5 / 2.5; ORX 10.0 / 4.0 / 4.0

No-incident cell (report only; IP = OR = N):

- none_q1600 (n 50): N c1900 49.4 / 1424 / 10.1, FX c2100 82.3 / 1334 / 10.7, FB f70_10 184.4 / 1138 / 17.7, NC NC 268.5 / 998 / 20.7
- none_q2000 (n 50): N c1800 142.2 / 1638 / 19.2, FX c1800 142.2 / 1638 / 19.2, FB f40_10 325.4 / 1250 / 30.2, NC NC 487.9 / 960 / 35.2
