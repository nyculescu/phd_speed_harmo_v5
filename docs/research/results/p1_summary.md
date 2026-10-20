# P1 result

Page `docs/research/protocols/p1_incident_information.md` (sha256 fed27bf6cb2f), code 85f7d34da9. |G| = 50, |A| = 100, |PI| = 180. Delay: door-to-door s/veh incl. origin and meter queue.

## Tool checks

| cell | T0 best | rel vs NC | CI diff | T0 | T4 N_t / g* rel | T4 | T-AD med | TV-T0 rel |
|---|---|---|---|---|---|---|---|---|
| slow_q1600 | IP | 32.8 % | [74.0, 148.8] | PASS | f20_8 / f70_8 34.6 % | PASS | 3.0  | 5.1 % |
| slow_q2000 | IP | 40.2 % | [184.8, 267.2] | PASS | c1800 / f40_10 26.6 % | PASS | 2.5  | 0.0 % |
| block_q1600 | IP | 23.5 % | [45.2, 94.9] | PASS | f20_8 / f40_16 29.9 % | PASS | 4.0  | 8.7 % |
| block_q2000 | IP | 28.6 % | [78.4, 215.8] | PASS | c1800 / f20_16 23.5 % | PASS | 4.0  | 0.5 % |

Author decisions: {'meter_signal': 'continuous', 't3_replicate': 'run', 'tv_t0_window': 'page', 'gate_views': 'both'}. Gates (both): T0 PASS (all seeds True, valid only True); T4 PASS (all seeds True, valid only True); TV-T0 window page.

T1 PASS; T3 PASS; TV-T0 binds (caveat: binds in the onset-clearance window but not over [onset, clearance + 120 s): the change may be a travel-time shift of arrivals (VSL slows edges 2-3), not a flow restriction); TV entry: no >= 10 % gain detected on 20 seeds.

## Tuning (arms per q)

- q = 1600: N c2000, FX c2400, FB f40_10, PI p40_40_10_e4, AD ad0p5_f40_10, ID f70_8, IP {'slow': 'f70_8', 'block': 'f40_14'}
- q = 2000: N c1800, FX c1900, FB f40_10, PI p70_70_8_e4, AD ad0p5_f40_10, ID f40_10, IP {'slow': 'c800+back', 'block': 'f40_16'}
- grid edges (report only): {'1600': {'AD': ['eta=0.5'], 'PI_pi0.1': ['K_P=20', 'K_I=10'], 'AD_pi0.1': ['eta=2'], 'N_pi0.25': ['K_F=120', 'n_crit=6'], 'FB_pi0.25': ['K_F=120', 'n_crit=6'], 'PI_pi0.25': ['K_I=120', 'n_crit_e4=6'], 'AD_pi0.25': ['eta=2'], 'N_pi0.5': ['K_F=120'], 'FB_pi0.5': ['K_F=120'], 'PI_pi0.5': ['K_P=70'], 'AD_pi0.5': ['eta=0.5']}, '2000': {'PI': ['K_P=70'], 'AD': ['eta=0.5'], 'IP_block': ['n_crit=16'], 'FB_pi0.1': ['K_F=10'], 'AD_pi0.1': ['eta=0.5'], 'PI_pi0.25': ['K_P=70'], 'AD_pi0.25': ['eta=0.5'], 'N_pi0.5': ['n_crit=6'], 'FB_pi0.5': ['n_crit=6'], 'PI_pi0.5': ['K_P=70'], 'AD_pi0.5': ['eta=0.5']}}

## S1 (information ladder)

- S1a: **FAIL**: knowing that an incident is on did not pay >= 10 % beyond strong always-on control (cell in both views: [])
- S1b: **PASS**: the type pays: IP beats ID (cell in both views: ['slow_q2000', 'block_q1600'])

| cell | ID vs N | vs FX | vs FB | vs PI | vs AD | IP vs ID | (rel %, all seeds; S1 level) |
|---|---|---|---|---|---|---|---|
| slow_q1600 | 37.7 | 34.7 | 8.5 | 3.1 | 11.8 | 0.0 | |
| slow_q2000 | 26.5 | 26.7 | -0.8 | -13.3 | 5.4 | 17.2 | |
| block_q1600 | 12.6 | 13.7 | -14.0 | -15.1 | 3.5 | 18.4 | |
| block_q2000 | 17.8 | 17.3 | -3.0 | 0.7 | 12.2 | 6.9 | |

## S2 (per-incident information beyond IP)

- slow_q1600: adds at most 39.7 %; bracket [-7.1, 39.7] %; TP 22.0 %
- slow_q2000: adds at most 13.3 %; bracket [-9.1, 13.3] %; TP 16.8 %
- block_q1600: adds at most 26.6 %; adds at least 3.4 %; bracket [3.4, 26.6] %; TP 14.6 %
- block_q2000: adds at most 19.8 %; bracket [-1.8, 19.8] %; TP 12.2 %

## S3 (break-even, smallest over L0 arms, all seeds)

| cell | d* | c* | p* | combined vs IP |
|---|---|---|---|---|
| slow_q1600 | 45.28 (crossing, PI) | 180.00 (> max, N) | 0.13 (crossing, PI) | -4.1 % |
| slow_q2000 | 25.80 (crossing, PI) | 46.29 (crossing, PI) | 0.17 (crossing, PI) | -28.0 % |
| block_q1600 | 0.00 (IP never ahead, PI) | 0.00 (IP never ahead, PI) | 0.00 (IP never ahead, PI) | -6.0 % |
| block_q2000 | 210.06 (crossing, FB) | 180.00 (> max, N) | 0.08 (crossing, FB) | -12.4 % |

Clean day (median delay s; ID = IP = N): q 1600: N 58.3, FX 161.6, FB 139.5, PI 113.0, AD 149.0, NC 265.7; q 2000: N 143.9, FX 225.3, FB 297.4, PI 197.8, AD 316.7, NC 504.9


Per q: false-alarm cost (s/veh) and f*(pi):

- q 1600: FA cost -1.64 [-3.12, 5.33]; f* pi 0.1: 0.20, pi 0.25: 0.00, pi 0.5: 0.00
- q 2000: FA cost 150.13 [124.23, 171.82]; f* pi 0.1: 0.00, pi 0.25: 0.12, pi 0.5: 0.31

## Table 1 (median delay s / served veh/h / max queue; invalid)

- slow_q1600: NC 310.7/948/40; N 310.8/934/42; FX 310.3/942/42; FB 206.4/1168/116; PI 189.9/1178/114; AD 216.0/1134/124; ID 190.7/1178/116; IP 190.7/1178/116; OR_in 136.1/1338/85; ORX_1 233.8/1102/88; ORX_2 195.6/1166/92; ORX_4 187.1/1194/94
- slow_q2000: NC 515.4/946/144; N 507.7/954/140; FX 511.4/952/140; FB 366.7/1212/197; PI 326.6/1236/192; AD 395.7/1140/218; ID 373.6/1210/200; IP 301.7/1282/161; OR_in 269.8/1360/164; ORX_1 356.6/1204/164; ORX_2 328.7/1274/164; ORX_4 311.5/1292/164
- block_q1600: NC 313.2/920/59; N 332.0/906/65; FX 321.6/894/64; FB 241.8/1086/140; PI 242.8/1090/133; AD 284.6/996/161; ID 287.9/1020/155; IP 230.8/1114/119; OR_in 186.1/1210/105; ORX_1 227.9/1096/124; ORX_2 221.4/1112/122; ORX_4 218.5/1122/122
- block_q2000: NC 520.5/932/148; N 520.9/942/150; FX 523.2/940/148; FB 413.2/1102/228; PI 431.5/1082/232; AD 489.0/968/268; ID 425.2/1106/236; IP 378.6/1156/196; OR_in 329.8/1238/184; ORX_1 393.2/1146/208; ORX_2 391.9/1154/210; ORX_4 375.5/1164/208

Runs 210061, failed 0, teleport runs 0, invalid 0, N fixed vs N->N hash mismatches 0.
