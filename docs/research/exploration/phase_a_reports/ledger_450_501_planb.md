# ledger_450_501_planb: V450-V501, Plan B protocol, S2 and S6

Sources: `docs/decisions.md:470-522` (D), `docs/research/protocols/planb.md` (PB), `planb_v23/docs/research/planb/cells_tested.md` (CT), `docs/research/results/planb_s2_result.md` (S2R), `round_2_result.md:1-22` (R2R), `v5b1_runs/planb_s6_read_v23/read6_v23.json` (J; named fields only, v2.3, deciding fields equal v1 per V501), `v5b1_runs/planb_s34_remote/` pick files (P). `read6_v23.log` holds one line: `study NULL {'TRUCK': ('T', 240, [])}`. Ledger defect: two rows are numbered V484 (D:504 replication plan, D:505 S1/S2); "V484b" below is D:505.

## (a) S6 verdict

One cell reached S6: TRUCK (SURGE dropped at S2, V487). TRUCK = T, "no clear difference; neither W nor L; harm not excluded"; study NULL (V496). 240 seeds, 58 arms, no drops, 0 of 1,200 v3w rows fail drain (V496). W fails on two components only (V496): the delay 97.5 % lower bound is at or below 0 against 9 of 23 opponents, and 3 of 5 learners (4 needed, PB:438) are positive on both measures against every opponent. k = 0 of 5 policies meet W alone; T2 passes 5 of 5, report-only (V496).

v3w against each opponent, effect % [97.5 % CI], positive = v3w better (J `cells.TRUCK.map`, `ci_m`); flow by point. The first 9 block delay.

| Opponent | Delay | Close-following | Flow |
|---|---|---|---|
| os0_10_10 | −0.58 [−0.93, +0.20] | +22.57 [+17.44, +27.90] | +0.11 |
| p333 | −0.25 [−0.83, +0.50] | +26.94 [+19.21, +35.30] | +0.14 |
| lr1000_10_1 | −0.25 [−0.83, +0.50] | +26.94 [+19.21, +35.30] | +0.16 |
| 3E-D_TRUCK | +0.08 [−0.57, +0.90] | +30.25 [+22.98, +38.45] | +0.10 |
| grid_os1_10_10 | +0.16 [−0.68, +1.05] | +27.17 [+19.98, +32.61] | +0.22 |
| os1_15_10 | +0.18 [−0.64, +0.94] | +25.75 [+18.38, +29.70] | +0.19 |
| lr1000_16_2 (= ASCH = steady pick) | +0.27 [−0.25, +0.90] | +28.80 [+21.81, +35.48] | +0.38 |
| lr400_13_2 | +0.72 [−0.04, +1.54] | +28.50 [+20.70, +34.07] | +0.33 |
| grid_lr400_13_1 | +0.83 [−0.05, +1.72] | +25.26 [+19.51, +31.33] | +0.52 |
| grid_z31333 | +0.98 [+0.56, +2.00] | +27.97 [+19.40, +36.08] | +0.30 |
| MPC-F | +1.09 [+0.56, +1.76] | +27.59 [+22.31, +32.01] | +0.42 |
| 3E-C_TRUCK | +1.12 [+0.75, +2.11] | +11.80 [+4.97, +19.71] | +0.13 |
| os1_10_0 | +1.33 [+0.56, +2.31] | +29.95 [+25.20, +35.15] | +0.34 |
| 3ex2 | +1.63 [+0.95, +2.23] | +25.11 [+19.26, +29.88] | +0.42 |
| grid_r4a2 | +2.12 [+1.07, +3.15] | +35.90 [+26.87, +40.78] | +0.55 |
| grid_a41000_10_2 | +2.12 [+1.07, +3.15] | +36.25 [+27.14, +41.30] | +0.55 |
| z33133 | +2.90 [+2.23, +4.03] | +33.08 [+24.65, +42.77] | +0.67 |
| lr400_16_1 | +3.09 [+1.81, +4.34] | +23.47 [+17.61, +32.32] | +0.88 |
| 3ex1 | +3.45 [+2.68, +4.35] | +31.35 [+24.21, +36.48] | +0.57 |
| r4a1 | +3.81 [+2.98, +5.22] | +34.85 [+28.35, +40.95] | +0.67 |
| a4400_10_1 | +4.55 [+3.41, +6.17] | +34.02 [+27.56, +38.86] | +0.78 |
| 3e (3E-T) | +4.62 [+3.75, +5.84] | +29.48 [+23.44, +35.52] | +0.56 |
| copy | +11.11 [+9.92, +12.48] | +33.33 [+29.17, +38.05] | +1.16 |

- Flow gate passes against all 23; the lowest interval is 3E-D_TRUCK [−0.02, +0.21] (J). Braking: largest point excess +2.00 % against 3e (V496). No L fires (V496).
- Learners (J `learner_signs`, `per_learner`): w0u250, w1u500, w2u250 positive everywhere. **w3u500** is negative on delay against os0_10_10 (−0.22), lr1000_10_1 (−0.33), p333 (−0.31) and 3E-D_TRUCK (−0.17); **w4u500** against os0_10_10 (−0.07). All 5 are positive on close-following against all 23.
- Against no control (report-only): delay +28.94 % [+28.07, +30.10] (V496); close-following +29.06 % [26.35, 33.31] at 95 %, `cf_shown_higher` false (J).
- Steady reference S on the same 240 seeds (J `S.map`, 97.5 %): v3w has **more** delay than p333, −1.57 % [−2.70, −0.24], than os0_10_10 −1.61 [−2.78, −0.89], than os1_15_10 −1.66 [−3.18, −0.66]; close-following +17.25 [+6.24, +36.75] against p333.
- Report-only: adaptation gain 1.56 [1.19, 2.09] on close-following, 1.05 [0.90, 1.33] on delay (V496). Resilience R (not read in a NULL): lower bound above 0 against 4 of 23 (3ex1, lr400_16_1, grid_z31333, MPC-F); against p333 1,156 veh-s [−831, +3,093], against 3E-C 682 [−753, +3,091] (J). Jam share against p333 +10.65 % [+0.02, +17.61] at 95 %, its 98.75 % interval includes 0 (V501).

## (b) Cells-tested count

PB:145: "Unit (V482): every (perturbation spec × demand level) cell on r2m3 in which a per-CAV DRL policy of this line ran, exploratory included: N = 90 (80 on this plant, 10 on its earlier P0 version, stated together), plus each Plan B cell that reaches S6 (92 with both, 91 with one, 90 after a KILL at S2); r1m3 and m32 rows are named, not counted". CT:5: "A re-test of the same pair (other policies, seeds or round) adds no cell ... Training-time episodes are not counted. Rules-only rows are not counted." CT:6: 80 = 10 (confirmatory 3) + 45 (V406 sweep) + 4 (V410 profiles) + 21 (V419 sweep). Now N = 91 (V487). PB:576: any cell proposed after these results is "a new study, labelled post hoc, never merged into this one's count". INFERENCE: each new condition a follow-up evaluates adds one cell per (spec × level) to the disclosed count.

## (c) Opponents

- **Carried rules (15)**, run unchanged (PB:203). p333 is `cav_rule [3,3,3]`, level 3 = 0.8 s (P `repick.json`; V477). 3E-T stopped at 40 of 100 generations (V443); 3E-X1/X2 were still falling at 40 (PB:216). copy is traced from DRL policies (PB:217).
- **Grid re-picks**, 69 tunable rules on seeds 7,480,100-119 (PB:204). TRUCK picks: zone z31333, on-4a r4a2, local lr400_13_1, adaptive a41000_10_2, own-state os0_10_10, plus os1_10_10; steady pick lr1000_16_2 (P `repick.json`).
- **3E-C / 3E-D**: ZoneOwnState, 5 zones × 4 parameters, diagonal CMA, population 24, 100 generations, pool 7,480,150-189, check 190-229 (PB:206-229). 3E-C starts from the own-state re-pick, loss = close-following against p333 + 10 per % of delay above +1 %. 3E-D starts from p333, loss = delay; no close-following bound. Each used 38,440 + 2,200 rows (V490). 3E-C "not converged at 100 generations" (incumbent from generation 98, P); 3E-D "met the plateau criterion" (V491).
- **ASCH**: two-regime scheduler on three zone speeds, grid θ × τ × h × library, seeds 230-269 (PB:255-260). Its pick is "never" switch, so it equals lr1000_16_2 (V491; P `asch.json`, 37 configurations).
- **MPC-F**: MLP (2 × 64) predicting 300-s cost, picks one of 4 held actions (p333, lr1000_16_2, 3E-T, 3E-C_TRUCK) every 30 s; fit seeds 270-309, gate 310-339 (PB:265-270; P). Held-out R² 0.81; gate passed (sum 291,151 against fixed p333 291,837), but fixed lr1000_16_2 scored 286,225 on the gate seeds (P `mpcf.json`).
- **Strength** (J `overfit_vs_p333`, opponent against p333 in TRUCK, 95 %): hardest on delay = os0_10_10 and p333. 3E-D ends at p333: +0.01 % [−0.45, +0.25]. No opponent is shown below p333 on delay; MPC-F is −1.24 % [−1.95, −0.77], copy −12.17 % [−13.05, −11.31], 3ex1 −3.64 %, 3e −4.45 %. Hardest on close-following = 3E-C_TRUCK: +21.18 % [14.77, 31.20] fewer than p333 at −1.28 % [−2.06, −0.48] delay.

## (d) TRUCK

- Spec: 10 main-route lane-0 trucks, the first at or after 360 + 80k s, each capped at 40 km/h for the whole trip, chosen from the demand list before the run, so every arm meets the same trucks (PB:286, :295).
- Chosen by a design workflow (V479), approved V480, "after DRL results on related perturbations were known (V456(3), V245)". Prior: H1 favoured DRL on close-following and did not bind (PB:303). "No v3w row existed when the cells were approved"; one crash-check row, not read (PB:164). V456(3): "any disturbance is fixed before control results".
- S2: G1 +17.2 % [14.0, 23.0] (no control) and +23.9 % [19.8, 27.7] (p333) above S; G2 p333 29.6 % [27.8, 32.2] below no control; G4(ii) as registered fails, so S2 reads KILL. TRUCK continues only under V486's replacement (largest excess +1.26 vehicles [−0.17, 2.77], limit 2), written after the result. It fails G2-loss, so "at best a level claim" (S2R; V487).
- Dropped: SURGE (step 5,300 → 6,000 → 4,600) at S2 on `stuck_n` and drain (+3.29 [1.70, 5.21]) (V487). WORKZONE recommended out: nearest [A3], may not bind (PB:319). Excluded (PB:312-320): V2V outage (not intended use), lane closure (teleports off, stranded vehicles), ALKS share or driver mix (plant change), weather (calibrated on another road), single brake (no wave, V342), burst H2 (held wait not counted), corridor 60 km/h limit (delay no controller can remove), oracle options.

## (e) Round 2

- None of 5 trained candidates (2B, 1B, 1D, ahead, rep) was shown better than v3w; Q1 null on 7 candidates (R2R:4-5). ahead (18 inputs with look-ahead) met its importance KILL (V465).
- **X1 T2 won** at 99.17 %: v3w, tail, sw each 5 of 5 against the counting rules p333, os0_10_10, 3E-T. 3E-X1 "did not meet the delay filter; its search was still falling at generation 40, and its pick is from generation 3", so the reading is "not answered against the CMA-ES rule" (R2R:7-9). The filter counts an opponent only within 2 % of p333's delay (V453). V461's tuning-seed value for the pick ("delay 1.05 % lower") is ambiguously signed; the failing test value was not read here.
- **X2 closed** (V466, T2 only, decided after the data): tail 3/5, v3w 2/5, sw 0/5 against 3E-T and 3E-X2. "The closing rests on 3E-T counting at −1.81 %, 0.19 points inside the delay filter" (R2R:16). V467: no delay-win sentence. X1: policies have 15-18 % more close-following than no control (R2R:18).

## (f) Cost and rate facts

- V443: a loaded rented run takes about 55 s (21 s idle laptop).
- V450: rest of round 1, five round-2 trainings (5 learners each) and 3E: about 13.5 h at $0.81/h, about $11.
- V464: 9,150 evaluation runs, about 2.6 h at about 58 runs/min, $0.774/h, 120 workers.
- V475: 5,560 pack-on runs in 2 h 08 min, 59 workers, $0.76; 2,600-3,050 runs/h; **$0.10-0.13 per 1,000 runs**.
- V483: no laptop runs. V484b: S1 + S2, about 820 runs, $0.33.
- V488: $20 hard cap; ceiling $40 or 7 days (PB:561).
- V490: rental 1, 100 workers, $0.605/h, 06:32-22:51, about $9.9; one search 7 h 42 min.
- V493: S6 ran at 1,690 runs/h on 90 workers (190-250 s per run per worker, full pack); the searches at about 5,500/h.
- V494: S6 13,920 runs, about $7.35; both rentals about $17.50. V492: a stuck instance $0.22. V499: 14-run rebuild $0.02.
- INFERENCE (my arithmetic): one new cell at Plan B scale costs about $17.5 and about 28 machine-hours; S6 about $0.53 per 1,000 runs, searches about $0.11.

## (g) Hypotheses

- **H1, supported strongly.** A 100-generation, 20-parameter delay search started at p333 ended at p333 (+0.01 %). No opponent beats p333 on delay in TRUCK. In steady traffic v3w is shown worse than p333 (−1.57 % [−2.70, −0.24]). V477: 0 of 58 CIs show a rule better than v3w on delay. Against: PB:304 records v3w better than all 14 rules on delay in X1 (+5.0 to +11.6 %, report-only); V475: at 7,000 veh/h v3w 3.7 % below p333 (point, outside intended use).
- **H2, split.** Edge on close-following against all 23 (+11.8 to +36.3 %), a reward term (PB:327). Second half holds in X1 (R2R:18) and at 3,500 and 7,000 (V477). It **fails in TRUCK**: 29.06 % fewer than no control.
- **H3, partly.** v3w "never sees the speed limit, the demand, the time or an event" (PB:197); rules read 400-1,000 m ahead (PB:215). Against: adding look-ahead (ahead) did not help (V465; R2R:4). V469: about 6 excess changes per ALKS, 0.48 reversals per change (one run).
- **H4, partly.** 3E-C, not converged, cuts the edge from about 27 % to 11.80 % [4.97, 19.71]. Against: the lower bound stays above 0 against all 23; rules do not transfer (copy −12.17 %, 3ex1 −3.64 %, 3e −4.45 % delay against p333), while one frozen v3w ties p333.
- **H5, supported.** X1's win excludes its own CMA-ES rule; X2 closes by 0.19 points; the counting filter counts 14, 7 or 6 opponents by universe (V501); G4 had no null (V486). Against: the close-following edge survived every recount and filter (5 of 5).
- **Other.** (1) W is conjunctive: delay and close-following against every opponent; "Delay binds among the measure conditions" (PB:531); 80 % power needs about 3 delay points (PB:519). INFERENCE: with H1, NULL is the expected outcome of this bar. (2) INFERENCE: TRUCK raises delay for every headway controller alike; the lever cannot remove a moving bottleneck. (3) v3w was not retrained (V478) while rules were tuned in the cell. (4) The demand-step prior favoured DRL (PB:302), but SURGE never reached S6. (5) Every Plan B row is outside the intended use; lane changing is not validated (PB:183).
