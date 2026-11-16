# critic_ranking_audit: memo `drl_win_directions_v0.md`

Primary sources: ledger `docs/decisions.md`; `/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json` (R6); `docs/research/round2/report/test_table.csv` (TT2); code in `/home/catalin/work/phd/wt/planb_v23/v5b/fleet/`. Scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit/` (f1-f5.py, tail.py, fuel.py). Numbers marked EXPLORATORY are mine, from stored rows already read for a verdict.

## JOB 1. Citation audit (30 items)

| # | Memo claim | Primary record | Verdict |
|---|---|---|---|
| 1 | 3E-D vs p333 +0.01 % [−0.45, +0.25] | R6 `overfit_vs_p333.3E-D_TRUCK.delay` +0.012 [−0.445, +0.245], 95 % (read6.py:626) | correct; level unlabelled |
| 2 | search "started from p333, ended at p333" | start p333: planb.md:228. Pick (`s6_picks.json`) is not p333: 0.8 s free level in all 5 zones plus triggers; cf +2.12 [−3.90, +5.35] | wording: "ended tied with p333 on delay" |
| 3 | steady −1.57 % [−2.70, −0.24] | R6 `S.map.p333.delay` −1.574, ci_m [−2.702, −0.238] (97.5 %); ci95 [−2.62, −0.54] | value correct; reading misleading (see F2) |
| 4 | +11.8 % [+5.0, +19.7] | R6 map 3E-C_TRUCK cf +11.80 [+4.97, +19.71] (97.5 %); V496 | correct |
| 5 | "to +36.3 %" | R6 grid_a41000_10_2 +36.25; not in V496's text | correct; cite R6 |
| 6 | round 2 +5.5 [+2.9, +8.0], +6.1 [+3.4, +7.4] | TT2 `delay_vs_p333_95`, v3w arm | correct (95 %) |
| 7 | planb.md:304, +5.0 to +11.6 %, 13 of 14 | quote exact; s01_result.md §6.1-6.2 agrees | correct, but the same 40 test seeds as #6 (V468: deterministic re-runs); listed as two "Against" bullets = double count |
| 8 | "plant was tuned to have a minimal capacity drop (V314)" | V314: "a reasonably minimal capacity drop" is one of about nine goals; the score has no drop term. V327: the picked plant `sm_as1.4_h0` reads 11.7 % (3 runs) / 10.8 % (11) against 1.7 / 4.2 % before, "not clearly met". plant_vv_record_v0.md:77, :92: PR-26 "gap", "capacity drop not settled" | **wrong as a fact about the frozen plant**; the drop is unknown |
| 9 | V315 "leaves less room for any controller" | exact | correct |
| 10 | V429, os1_15_10 lower "at most levels" | "at every level except 5,500 (p333)"; two rules only, training-mode medians under training slowdowns (round_1.md:65), no CI | correct; D1's "best rule barely changes with demand" is not supported by it |
| 11 | V413 "about 200 times" | exact ("per vehicle") | correct |
| 12 | b_env.py:811-812, :842-843 | correct in the planb_v23 copy; the v5b1 copy has 1,100 lines, offset 3. The term also charges `hard` braking | correct; name the copy |
| 13 | b_env.py:37, :774-784, :499-509, :1117-1129; c_train.py:41-42 | all as described; rule reads columns 0, 2, 4, 15 | correct |
| 14 | N = 91 (V487); cells_tested.md:5 | exact | correct |
| 15 | V410: 36-42 %, same or 4 % less, peak 69 % more | exact | correct |
| 16 | X1 vs no control −16.6 [−25.1, −8.4] | TT2 `ttc_vs_nc_95`; round_2_result.md:265 | correct |
| 17 | "15 and 24 moving full-emergency events" in X1 | round_1_result.md:202-206: 15/200 is X1, 24/200 is X2; p333 3/40 and 6/40 (same or higher rate) | misleading |
| 18 | V496 AG 1.56 [1.19, 2.09], 1.05 [0.90, 1.33] | exact | correct |
| 19 | TRUCK vs nc +29.06 [+26.35, +33.31]; steady +45.86 [+42.20, +50.47] "this memo's computation" | both stored: `no_control.cf95`, `S.map_report_only.nc.cf` | correct; provenance wrong for the second |
| 20 | steady 3E-C +7.99 [−9.72, +25.32] "exploratory" | stored `S.map` +7.99, ci95 [−9.72, +25.43], ci_m [−11.71, +31.46] | upper bound differs; cite stored |
| 21 | V337 three CIs; 82-98 % | exact (V339: training episodes with exploration) | correct |
| 22 | V419 quote | exact | correct |
| 23 | V344 0 of 8; V347 −4.5 [−5.5, −3.0], +56.8 | exact | correct |
| 24 | V401 −1.6 to −10.2 % | exact (baseline-v3 policies) | correct |
| 25 | X2 medians 229,111 vs 226,353; "within about 1 %" | medians exact; paired statistic +3.0 [+0.7, +5.6] at 95 %, [−0.1, +6.4] at 99.17 % (round_2_result.md:203, :206) | misleading; use the paired value |
| 26 | "tuned rules take most of that back" | true only in X2. X1: smallest margin +5.0 [+3.0, +8.8], 3E-X1 +7.8 [+4.0, +11.3] | misleading |
| 27 | V475 3.7 %; V398 +8.1 to +23.4; V377(3) 48-62 % | exact; V377(3) is p333 on one seed, not a policy | correct; caveat |
| 28 | copy −12.17, 3ex1 −3.64, 3e −4.45; MPC-F −1.24 [−1.95, −0.77]; −14.3 to −4.4 | R6 overfit; round_2_result.md:394 | correct |
| 29 | ASCH picked "never switch" (V491) | V491: "ASCH choosing a single member"; the phrase is planb.md:259 | quote not in V491 |
| 30 | "Never tried: memory…" (claim_review_round2.md:214) | line is confirmatory 3's limits sentence; it does not say "never tried" | not found as cited; INFERENCE |

## JOB 2. Findings

**F1 (high). M1 and summary point 2 rest on an unverified premise.** The frozen plant's capacity drop is "not settled" (PR-26), and the one estimate after tuning is larger than before (V327). Change: reword M1 to "drop unknown; V314 stated the intent". Add a zero-cost screen 0: PR-26's estimator with a null on stored no-control rows. It is a V&V item the thesis needs anyway (plant_vv_record_v0.md:97), and it decides whether M's and P5's reasoning holds.

**F2 (high). R is under-stated; F is over-stated.**
- R, for: round 1's test, on other seeds (7,440,500-539, round_1.md:192), also shows it: X1 +2.6 [−1.8, +5.4] and X2 +3.7 [+1.7, +5.0] against p333; +5.5 [+3.1, +10.5] and +4.7 [+1.3, +7.2] against os1_15_10 (`round1/report/test_table.csv`). So "the only edge that replicated" (§4, §6) is wrong: the slowdown delay edge replicated at arm level.
- R, against, missing from the memo: V466 closed X2 by author decision; X1 fails V459's harm rule against no control. Screen R searches only the ZoneOwnState family, while the best X1 rule is a LocalRule (lr1000_16_2). Its 60 seeds are V435's count for a 95 % bound; the memo's 97.5 % needs 80.
- F, against, stored and not cited: v3w has more braking events at 4.5 m/s² or harder than 3E-C, −5.73 % [−8.28, −2.31] at 95 %, [−8.80, −1.29] at 97.5 % (R6 `map_report_only.events_ge45`, medians 700.2 against 668.0, report-only). This already meets screen F's own "safety" KILL wording. For: ttc15 +37.5 [+27.4, +46.7], ttc2 +40.5 [+34.8, +45.6] against 3E-C.
- Screen F cannot pass as sized. INFERENCE: the 240-seed lower bound is +4.97; at 80 check seeds the interval widens by √3 and the lower bound sits near 0 with no change in the true edge. Change: 240 check seeds (2,160 runs, about $1.1).
- Steady "v3w worse than p333" is a pooled-arm effect: per-learner average −0.11 % [−0.99, +0.73] (EXPLORATORY). Add M4's caveat to H1.

**F3 (medium). Verdicts stronger than evidence.**
- H-1 "KILLed by the stored rows": the rows test a per-seed choice among whole-run rules, with one proxy, exploratory. A within-run switch is untested. The real record is ASCH's tuning (V491) and `sw` (round_2_result.md:177-178, not cited). Change to "likely to fail"; keep KILL for pre-registered criteria.
- P3 "closed by the record" while V367 says V339 and V344 "need a look". Change to "likely to fail; record flawed".
- M2 "can only lengthen, which trades delay": in X1 and X2 the rules and v3w that lengthen have less delay than p333. Limit M2 to steady and TRUCK.
- Screen M at 40 seeds: X1's paired SD is 7-11 % (V435), not TRUCK's 5.3 %. A KILL there does not bound a 3 % effect. Use 80 seeds or state the bound.

**F4 (medium). Missing directions; none beats the top three.**

| Direction | Record | Equal exposure | View |
|---|---|---|---|
| Energy | V339: "the energy objective itself is untested". EXPLORATORY S6 fuel per km: v3w vs p333 +0.22 % [+0.12, +0.32] TRUCK; no control within 0.6-1.1 % | CMA-ES with a fuel loss | no headroom; list as closed |
| Comfort | EXPLORATORY jerk per distance within 1 % of p333 | same | closed |
| Ramp/mainline equity | R6 report-only: ramp-1 delay vs p333 −1.68 [−2.34, −0.66]; ramp-2 vs 3E-C −4.04 [−5.58, −2.32] | yes | against DRL |
| Tail measures | EXPLORATORY TRUCK worst-10 % mean: vs p333 +1.99 [+0.01, +4.07], vs os0_10_10 +0.32 [−1.95, +2.59] | yes | not shown |
| Sensing noise, V2V loss | plant_vv_record_v0.md:11 "Not for: V2V with latency or loss"; outage60 −4 % delay (V342) | rules re-tuned under noise | needs a V&V change; LocalRule depends most on roadside bins; unlisted, worth one block |
| Penetration below 50 % | planb.md:316 "a plant change"; the gate needs an ALKS leader | yes | INFERENCE: the lever shrinks for all |
| Period below 10 s | V381(2): rules 5 s; PR-12 rate limit | rules already faster | low |
| Human reaction | "Not for: human adaptation" (same line) | n/a | out of intended use |
| Preference-conditioned policy | V304: the weight "moves C along the rules' trade-off and not beyond it" (old plant) | rule searches at several hinges | add as F stage 3, not alone |

**F5 (medium). Brief compliance.**
- F, R and M have no §3 block; L4 and D5 point to "§4", a table row. Missing for each: equal exposure of the later DRL study, V&V effect (M's 2-4 s headways), risks, cells added.
- Cost is absent in L3, P1, P3, P4, P5, D2, D3, D4, H-1, H-2, H-3, H-5. Cells added appear only in L1, D1, D2. Author time only in L1, P2 and the screens.
- "The only delay mechanism the literature supports" (§0, §4) has no [VERIFY]; write "found".
- D1's step equals V410's profile, already seen with control results: label it post hoc (V456 rule).
- CI levels are mixed (95 %, 97.5 %, 99.17 %) without labels. The b_env.py copy is not named.
- Unsourced: D3's +31.5k / +33.2k-33.6k; "central merge cap unused since run 3". No "first/novel" wording found.

**F6. Probabilities (my judgement, not measured).** F about 15 % (memo 30-40 %): unconverged 3E-C sits 1.8 points above the 10 % KILL line, the richer family reads gap and closing speed, steady edge not shown, events_ge45 adverse. R about 10-15 %, X1 only, and X1 cannot meet V459. M at most 5 %: V347, V349, V355 and V419 all show longer headways cost delay here. D1 about 10 %, above M. Order I would defend: screen 0 (PR-26), M (cheap, 80 seeds), R in X1 with a LocalRule delay search, then F stage 1 at 240 seeds.
