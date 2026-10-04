# Lead 1 stage H: headroom gate against tuned non-learning control

*2026-10-03 20:46 · protocol `docs/lab/t1_meter2_protocol.md` Addendum A · gate seeds 7170220-7170239 × 21 conditions · q = 1600 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/m2h2_1791085170`*

**Pre-registered rule - H = (best non-learning − I) / best non-learning ≥ 10 % with the paired 95 % CI lower bound > 0 → DRL stage: GO**

Best non-learning B = `evsched2`. H = +11.1% (median paired Δ +31.3 s, 95 % CI [+21.4, +54.2] s). Secondary (oracle restricted to A6): H_A6 = +13.4% [+24.9, +59.0] s.

| arm | median J (s) | median served (veh) | FAIL runs | B − arm (s) [95 % CI] |
|---|---|---|---|---|
| IA6 | 252.1 | 301 | 4 | +37.8 [+24.9, +59.0] |
| family | 253.5 | 298 | 5 | +30.0 [+22.9, +52.3] |
| I | 257.0 | 300 | 5 | +31.3 [+21.4, +54.2] |
| evsched2 | 281.9 | 277 | 1 | — |
| pooled | 282.0 | 288 | 3 | +11.8 [+1.6, +26.0] |
| mpcf_old | 285.1 | 283 | 6 | +29.5 [+21.6, +42.4] |
| evsched_old | 291.2 | 279 | 4 | +14.7 [+1.0, +34.2] |
| mpcf2 | 297.0 | 270 | 4 | +8.2 [-5.3, +17.7] |
| nc | 360.8 | 252 | 8 | -18.0 [-115.6, +2.4] |

Per family (B fixed as above; informative only):

| family | best non-learning in family | H vs B [95 % CI] |
|---|---|---|
| none | pooled | +0.0% [+0.0, +0.0] s |
| slow | mpcf_old | +14.7% [+39.1, +81.8] s |
| block | mpcf_old | +22.3% [+23.3, +113.4] s |
| surge | pooled | +6.0% [+2.1, +48.8] s |

evsched2 = `evsched:9:40:1.35:t1_meter2_lookup.json` (tuned on 7170100-7170119); MPC-F2 sha256 38b57fb3ae87…; lookup sha256 abd3b253151a…

## Notes (written after the gate, before any further run)

**The literal pre-registered rule says GO, but its choice of B is flawed. The conservative reading is KILL.**

Addendum A picked B as the arm with the lowest *median level* of J_s. The binding convention (CLAUDE.md) is the *median of paired differences*, and with 20 seeds the two disagree, because seed-to-seed spread is large (`evsched2` J_s ranges from 194 to 464 s). `evsched2` (median level 281.9) beats `pooled` (282.0) by 0.1 s on levels. On paired seeds, however, it is worse than four of the five other non-learning arms.

Paired median differences, row minus column, in seconds (negative = row better):

| | pooled | evsched2 | mpcf2 | evsched_old | mpcf_old |
|---|---|---|---|---|---|
| pooled | — | −11.8 | −5.4 | +4.8 | +12.6 |
| evsched2 | +11.8 | — | +8.2 | +14.7 | +29.5 |
| mpcf2 | +5.4 | −8.2 | — | +6.5 | +25.4 |
| evsched_old | −4.8 | −14.7 | −6.5 | — | +12.7 |
| mpcf_old | −12.6 | −29.5 | −25.4 | −12.7 | — |

**`mpcf_old` is the best non-learning arm on every pairwise comparison**, with mean J 274.4 against 288.0 for `pooled`. This is the R6-frozen MPC-F: 4 settings, fitted on the T1-M mix.

Headroom against each non-learning arm, H_arm = median(J_arm − J_I) / median(J_arm):

| arm | H vs I [95 % CI of Δ, s] | H vs I_A6 |
|---|---|---|
| mpcf_old | **+3.3 % [−3.8, +22.9]** | +4.2 % |
| evsched_old | +6.0 % [+3.1, +27.5] | +6.9 % |
| pooled | +7.6 % [+12.7, +28.4] | +8.9 % |
| mpcf2 | +10.1 % [+15.0, +46.0] | +11.6 % |
| evsched2 (pre-registered B) | +11.1 % [+21.4, +54.2] | +13.4 % |
| nc | +20.3 % | +22.5 % |

**Reading, both logged:**
- The literal rule gives **GO** (H = 11.1 %).
- With B chosen under the binding paired convention (`mpcf_old`), H = **3.3 %**, CI including 0. That is a **KILL**, and it agrees with the A.6 prior.
- The lead is treated as **KILL for training a new DRL controller on this mix**. The author may overrule this.

**Further observations:**
- The refitted MPC-F2 has a better held-out R² (0.94 against 0.90) but controls worse than `mpcf_old`: it is worse by 25.4 s paired, and worse than `pooled` too. Its A6 action set includes "meter off", which is a plausible cause, but this was not tested.
- The re-tuned `evsched2` sits at the corner of its tuning grid (v_slow = 9, t_block = 40, f_surge = 1.35). It is still worse than its untuned predecessor here (+14.7 s).
- H measures the headroom of *static* per-condition settings. A dynamic scheduler (MPC-F, DRL) can in principle beat I; `mpcf_old` already gets within 3.3 % of it.

## Exploratory follow-up: the R6-frozen DRL candidate on this mix (not a claim)

*`vsl_lab/jobs/t1_meter2_r6ood.py`, run on the same gate seeds 7,170,220–239 (already used, tuning role), 420 runs, raw under `m2r6ood_*`. Purpose: decide whether a pre-registered out-of-distribution test on fresh seeds is worth proposing.*

Median paired Δ of DRL − arm, s [95 % CI], relative to the arm:

| arm | DRL − arm |
|---|---|
| `mpcf_old` | +7.9 [−2.3, +12.9] (+2.8 %) |
| `pooled` | −1.7 [−10.5, +4.2] (−0.6 %) |
| `evsched_old` | +2.3 [−14.5, +14.0] (+0.8 %) |
| `evsched2` | −23.2 [−40.2, −3.6] (−8.2 %) |
| `I` (oracle) | +16.1 [+2.8, +31.5] (+6.3 %) |

Per family, against `pooled`:

| family | DRL − `pooled` |
|---|---|
| slow | −12.0 % |
| block | −11.4 % |
| surge | **+16.1 %** (CI [+21.9, +52.7] s) |

Against `mpcf_old`, the DRL is +0.3 % to +4.1 % in every family.

**Reading:**
- The R6 policy does **not** generalise to the varied severities and durations. Its gains under slowdowns and blockages are cancelled by surges outside its training range (factors 1.15–1.5 and 150–600 s, against 1.3 and 300 s in training).
- It is not better than the R6-frozen MPC-F here.
- **No out-of-distribution test is proposed. Lead 1 is closed.**
- The R6 claim (`t1_meter_r6.md`) is unaffected: it was made on the pre-registered 4-kind mix. Its scope must be stated as that mix only, because this check shows it does not transfer.
