# P1 result: how much incident information does mainline metering need?

**(P)** = pre-registered (rule or report-only row); **(D)** = descriptive, added after the data. Delay: door-to-door s/veh, incl. origin and meter queues. rel = median(r − t) / median(r), paired seeds. S1–S3 hold **given an incident** (A4(a)).

## 1. Provenance and verification

- Page `docs/research/protocols/p1_incident_information.md` (V99, V100); code `85f7d34` (frozen: `/home/catalin/work/phd/p1_frozen_85f7d34`); runs in `/home/catalin/work/phd/v5b1_runs/p1/v99/`.
- Run once; paused by a docs commit after the first tool-check stage, resumed with the same flags (6,146 runs reused).
- Tuning seeds 7,400,200–239; 210,061 evaluation runs (7,400,500–599), none failed, invalid or teleported. T0, T1, T3, T4 PASS.
- Evidence: `p1_verification/` (independent re-derivation matches all 3,364 compared `result.json` values; 26 re-runs identical).

## 2. Pre-registered statements

**S1 rule (P).** R(t, r) passes iff (a) in ≥ 1 cell, rel ≥ 10 % and the CI lower bound of median(r − t) > 0, and (b) in every cell, the point rel ≥ −5 %. Level 0.99375. S1a: R(ID, r) for every L0 arm r, with (a) in the same cell, in both seed views. S1b: R(IP, ID).

- **S1a FAIL.** ID meets (a) against neither FB nor PI in any cell, so **both bind** (`result.json` names FB by tie-break).
- **S1b PASS** in slow_q2000 and block_q1600, each with a weakness (D, Table 2): a near-tie in the ID choice (block_q1600), or detection delay (slow_q2000).
- **S2.** y (lower) = mean version vs ORX_4; x (upper) = median version vs OR_in. The plateau failed everywhere: no "about" value.
- **TP:** a report-only placebo (§4), never subtracted.
- **S3 (no test).** At d = 0, IP leads every L0 arm at 95 % in slow_q2000 and block_q2000 (D). Its lead over PI is not significant in slow_q1600. In block_q1600, IP and PI are not distinguishable, and d* is uninformative (CI spans the grid).

## 3. Tables

Table 1. Medians, 100 evaluation seeds: delay s/veh / served veh/h / TTT veh·h (control window) / max queue veh (origin backlog + edges 1–2) / emergency stops per run (D; the rest P). Clean days: ID = IP = N.

| Arm | slow_q1600 | block_q1600 | clean_q1600 | slow_q2000 | block_q2000 | clean_q2000 |
|---|---|---|---|---|---|---|
| NC | 310.7 / 948 / 23.5 / 40.5 / 0 | 313.2 / 920 / 24.2 / 59 / 0 | 265.7 / 996 / 20.7 / 29 / 0 | 515.4 / 946 / 37.2 / 144 / 0 | 520.5 / 932 / 36.7 / 148 / 0 | 504.9 / 964 / 35.8 / 140 / 0 |
| N | 310.8 / 934 / 24.1 / 42 / 7 | 332.0 / 906 / 24.8 / 65 / 6 | 58.3 / 1376 / 10.0 / 31 / 8 | 507.7 / 954 / 36.6 / 140 / 2 | 520.9 / 942 / 37.1 / 150.5 / 2 | 143.9 / 1584 / 19.5 / 88.5 / 2 |
| FX | 310.3 / 942 / 23.9 / 42.5 / 11.5 | 321.6 / 894 / 24.7 / 64 / 10 | 161.6 / 1160 / 15.0 / 27 / 14 | 511.4 / 952 / 36.7 / 139.5 / 2 | 523.2 / 940 / 37.3 / 148 / 2 | 225.3 / 1348 / 21.8 / 80.5 / 2.5 |
| FB | 206.4 / 1168 / 21.7 / 116.5 / 3 | 241.8 / 1086 / 23.9 / 139.5 / 3 | 139.5 / 1246 / 15.4 / 100 / 11 | 366.7 / 1212 / 33.6 / 197 / 2 | 413.2 / 1102 / 36.3 / 227.5 / 2 | 297.4 / 1284 / 28.8 / 179 / 3 |
| PI | 189.9 / 1178 / 20.8 / 114.5 / 2 | 242.8 / 1090 / 23.5 / 133 / 2 | 113.0 / 1286 / 14.3 / 87 / 8 | 326.6 / 1236 / 33.2 / 192.5 / 1 | 431.5 / 1082 / 38.4 / 232.5 / 1 | 197.8 / 1466 / 23.6 / 137.5 / 2 |
| AD | 216.0 / 1134 / 21.6 / 124 / 3 | 284.6 / 996 / 24.9 / 161 / 3 | 149.0 / 1226 / 15.7 / 105 / 8 | 395.7 / 1140 / 35.3 / 218.5 / 2 | 489.0 / 968 / 38.2 / 267.5 / 2 | 316.7 / 1254 / 29.0 / 189 / 3 |
| ID | 190.7 / 1178 / 21.2 / 115.5 / 2 | 287.9 / 1020 / 25.8 / 155 / 2 | = N | 373.6 / 1210 / 33.7 / 200.5 / 1 | 425.2 / 1106 / 35.6 / 235.5 / 1 | = N |
| IP | 190.7 / 1178 / 21.2 / 115.5 / 2 | 230.8 / 1114 / 22.2 / 119 / 4.5 | = N | 301.7 / 1282 / 31.5 / 161 / 1 | 378.6 / 1156 / 33.4 / 195.5 / 3 | = N |
| OR_in | 136.1 / 1338 / 17.8 / 85 / 3 | 186.1 / 1210 / 20.6 / 105 / 4 | – | 269.8 / 1360 / 30.1 / 163.5 / 1 | 329.8 / 1238 / 31.6 / 184 / 2 | – |

Table 2. "X vs Y": positive = X better. "X − N": positive = X worse. Bold: the pre-registered rule holds, or ID/IP lead at 95 % (prevalence).

| Statistic | q1600: slow / block | q2000: slow / block |
|---|---|---|
| S1a: ID vs FB, rel % [S1 CI] (P) | +8.5 [−0.9, 16.6] / −14.0 [−21.6, −2.7] | −0.8 [−4.6, 1.5] / −3.0 [−5.5, 1.2] |
| S1a: ID vs PI, rel % [S1 CI] (P) | +3.1 [−3.0, 9.2] / −15.1 [−26.5, −8.6] | −13.3 [−20.1, −6.0] / +0.7 [−2.9, 6.0] |
| S1b: IP vs ID, rel % [S1 CI] (P) | 0.0 (same plan) / **+18.4 [10.0, 29.7]** | **+17.2 [11.4, 26.0]** / +6.9 [0.8, 15.3] |
| S1b sensitivity, rel % [S1 CI] (D) | – / with ID = f40_10: +6.5 [−1.8, 17.9] | IP 30 s late (ID undelayed): +9.8 [−5.8, 18.5]; 60 s late: −28.1 [−35.4, −21.9] / – |
| IP vs FB at d = 0, s/veh [95 %] (D) | +17.4 [4.4, 28.5] / +11.3 [−4.6, 25.3] | +64.0 [32.8, 77.5] / +18.4 [4.6, 50.8] |
| IP vs PI at d = 0, s/veh [95 %] (D) | +5.9 [−1.5, 16.5] / −1.7 [−15.8, 21.2] | +22.5 [10.0, 31.0] / +42.1 [15.0, 78.4] |
| S2 bracket [y, x], % (P) | [−7.1, 39.7] / **[3.4, 26.6]** | [−9.1, 13.3] / [−1.8, 19.8] |
| TP placebo, % (P, report only) | 22.0 / 14.6 | 16.8 / 12.2 |
| S3 d*, s [95 %], binding arm (P, no test) | 45.3 [0, 140.9] PI / never ahead [0, 240] PI | 25.8 [9.9, 34.9] PI / 210.1 [7.6, 240] FB |
| S3 p* [95 %], binding arm (P, no test) | 0.13 [0.00, 0.25] PI / never ahead [0.00, 0.30] PI | 0.17 [0.10, 0.22] PI / 0.08 [0.02, 0.21] FB |
| S3 c*, s [95 %] (P, no test) | n/a (stay plan) / n/a (stay plan) | 46.3 [24.6, 58.6] PI / n/a (stay plan) |
| Combined row vs IP, rel % (P, no test) | −4.1 / −6.0 | −28.0 / −12.4 |
| *Clean day and prevalence (per q)* | q1600 | q2000 |
| Clean day: PI − N, paired median / mean, s/veh (D) | +7.4 [−9.9, 37.5] / −9.8 [−32.0, 11.7] | +14.5 [−13.6, 35.0] / −17.8 [−45.2, 8.0] |
| Clean day: FB − N / AD − N, paired median, s/veh (D) | +10.1 [−10.7, 40.9] / +2.7 [−8.2, 49.9] | +125.1 [96.2, 146.3] / +129.5 [103.9, 158.3] |
| Clean day: FX − N, paired mean, s/veh (D) | +46.9 [25.7, 68.3] | +42.2 [14.0, 71.3] |
| One false alarm: FA − N, paired median, s/veh (P, report only) | −1.6 [−3.1, 5.3] | +150.1 [124.2, 171.8] |
| PI_π at π = 0.1 / 0.25 / 0.5 | p20_10_10_e4 / p40_120_6_e4 / p70_70_8_e4 | p40_40_8_e4 / p70_70_8_e4 / p70_70_8_e4 |
| ID vs PI_π, rel % [95 %] (P, report only) | **+6.6 [3.2, 10.9]** / −5.2 [−15.2, 0.3] / −10.3 [−18.3, −4.7] | −6.6 [−9.8, −2.5] / −0.3 [−7.9, 8.2] / −2.5 [−7.1, 0.9] |
| IP vs PI_π, rel % [95 %] (P, report only) | **+10.0 [6.1, 12.9]** / −4.7 [−12.3, 6.3] / −2.7 [−11.3, 3.1] | −3.1 [−7.7, 0.2] / +5.3 [−3.2, 14.6] / +6.5 [−0.8, 12.4] |
| IP vs PI_π, mean gain, s/veh [95 %] (D) | −25.8 [−45.2, −7.6] / −30.5 [−45.9, −16.0] / −18.2 [−31.7, −5.3] | −9.0 [−32.1, 13.2] / −6.8 [−29.0, 14.2] / +4.3 [−14.0, 21.1] |
| f*(π) [95 %], PI binding (P, no test) | 0.20 [0.08, 1.00] / never ahead [0.00, 0.14] / never ahead [0.00, 0.11] | never ahead [0.00, 0.01] / 0.12 [0.00, 0.33] / 0.31 [0.00, 0.44] |
| Grid edges (P, report only) | AD η=0.5; PI_0.1 K_P=20, K_I=10; PI_0.25 K_I=120, n_crit=6; PI_0.5 K_P=70; N_0.25, FB_0.25 K_F=120, n_crit=6; N_0.5, FB_0.5 K_F=120; AD_0.1, AD_0.25 η=2; AD_0.5 η=0.5 | PI K_P=70; IP block plan n_crit=16; AD η=0.5; PI_0.25, PI_0.5 K_P=70; FB_0.1 K_F=10; N_0.5, FB_0.5 n_crit=6; AD_π η=0.5 (every π) |

## 4. What the paper can honestly say

On one simulated freeway bottleneck with mainline metering (one signal across 4 lanes), and given that an incident occurs, no gain of 10 % or more from presence-and-timing information alone was detected against a tuned always-on feedback meter or a PI law in the PI-ALINEA form; in 2 of 4 cells it was significantly worse than always-on PI (−13.3 % [−20.1, −6.0] and −15.1 % [−26.5, −8.6], S1 level). Given an incident, the incident type added 17.2 % [11.4, 26.0] and 18.4 % [10.0, 29.7] over presence alone in two of four cells; one gain depends on the presence-only plan chosen, the other shrinks with 30 s of detection delay. Per-incident hindsight information beyond the type plan is only bracketed per cell, from a mean lower bound (ORX_4) to a median upper bound (OR_in): [−7.1, 39.7] (slow_q1600), [−9.1, 13.3] (slow_q2000), [3.4, 26.6] (block_q1600) and [−1.8, 19.8] % (block_q2000); no single value exists because the plateau check failed. For scale only, a placebo that picks the best of the type plan's own 5 runs (demand and SUMO seed redrawn, incident fixed) already gains 12–22 %.

It cannot say that:
- gains ≥ 10 % from presence and timing are excluded (against FB in slow_q1600 the CI reaches 16.6 %);
- IP beats PI by ≥ 10 % (S1 rule) anywhere; smaller significant leads exist (slow_q2000, block_q2000);
- PI has a clean-day cost: **not resolved**. Clean days are bimodal; PI is worse on N's good days, better on breakdown days. FB and AD at q2000, and FX (mean), do pay;
- incident plans win at a realistic prevalence (none is sourced). In the prevalence line (P, report only), IP and ID lead every π-retuned arm only at q1600, π = 0.1; elsewhere no lead is detected, or PI_π leads;
- anything about ramp metering, general or novel.

## 5. Limits

- **One plant, mainline metering.** BN4: one signal across 4 lanes, no on-ramp. PI is a PI law in the PI-ALINEA form (Wang et al. 2014 [VERIFY]) on the edge-4 vehicle count, not occupancy.
- **Mainline-metering prior art is NOT yet checked** (A1(a) open) [VERIFY]. The cited works (`prior_art_P1_P2.md`) are incident *ramp* metering. Check mainline metering and MTFC before any paper text.
- **No amber phase.** Every metered arm, IP included, causes emergency stops at the meter (Table 1; none under NC; 87 % of 50,061 non-replicate evaluation runs). No collisions.
- **Unlimited meter queue.** No storage limit; median max queue up to 196 veh (IP) and 268 (AD), block_q2000.
- **Bistable plant.** In slow_q2000 under N, the edge-4 count saturates at 60 to the end of control (seed 7,400,501: from 430 s; clearance 538 s); IP with d = 60 s jams too. So IP's gain over N falls from 191.4 s/veh to 0 at d ≥ 60 s: the cell mostly measures "breakdown or not". This likely also widens TP and the clean-day spread (untested).
- **Controller-family confound.** A has no PI-law plans (only constant-rate and integral-only feedback), so "ID/IP vs PI" mixes information with controller family. S1a still fails without PI: FB also blocks it.
- **Grid edges** (Table 2) could move S1a and S3 against PI (a stronger PI only reinforces S1a FAIL), S1b in block_q2000 (IP's n_crit=16; OR_in picks it on 36–41 % of block seeds, so x could rise), and the prevalence line. q0 and snapshot counts are untuned.
- **Disclosures (V100; page §8).** (1) D1(a): corrected "continuous" meter signal; pre-V101 D1/D2 numbers are not directly comparable. (2) Screens D1, D2 and the design-review probes (smoke seeds 7,400,000–003) were seen before the page was fixed. (3) D5(a): AD_π keeps the main FB's (K_F, n_crit). (4) No amber. (5) The block incident is a substitute.

## 6. Next steps (estimates at 9.6 runs/s)

1. **Separate information from controller family** (addendum, fresh seeds): PI-law plans in A, and a "PI by default + type plan" arm. Tuning: 28,800 runs (50 min) with stay plans, 57,600 (1.7 h) with back plans, plus up to 73,600 switch runs from PI (2.1 h). Evaluation: under 20 min unless S2/ORX are re-run over the larger A (720,000 runs, 21 h).
2. **Re-test both S1b cells** on confirmatory seeds 7,400,700–999 (author approval), pre-registering the ID choice and detection timing: under 5,000 runs, 10 min.
