# R5-M: DRL (RecurrentPPO) scheduling the feedback meter vs tuned non-learning control

*2026-10-03 10:00 · protocol `docs/lab/t1_meter_gscan_protocol.md` Addendum D · test seeds 7110590-7110689 × 4 kinds · q = 1600 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/r5m_main2`*

**Pre-registered reading - DRL measurably improves on the best non-learning control (beats evsched AND MPC-F, pooled and in ≥ 2 of 3 learner seeds; no kind significantly worse by > 5 %; FAIL share ≤ 5 %): NO**

Median over seeds of J (mean over the 4 kinds of door-to-door time, s): lookup 206.3, drl0 219.8, evsched 227.5, drl1 228.4, drl_pooled 231.5, pooled 232.7, drl2 237.8, mpcf 239.9, meter106 243.5, nc 331.5

| DRL vs | pooled Δ (s) [95 % CI] | rel | seed 0 | seed 1 | seed 2 | beats (pooled & ≥ 2/3) |
|---|---|---|---|---|---|---|
| evsched | -2.4 [-13.1, +5.8] | -1.0% | -6.6 [-24.9, -0.3] | -9.9 [-18.9, +6.2] | -1.3 [-14.5, +9.6] | no |
| mpcf | -1.2 [-15.3, +7.2] | -0.5% | -17.0 [-25.5, -8.3] | -5.0 [-16.7, +5.0] | +2.5 [-7.2, +9.5] | no |
| pooled | -1.2 [-8.7, +5.2] | -0.5% | -11.6 [-23.7, -1.8] | +2.4 [-5.5, +9.5] | +3.1 [-4.1, +11.6] | no |
| meter106 | -18.1 [-38.2, -7.8] | -7.4% | -39.4 [-51.5, -22.6] | -19.9 [-39.7, -8.6] | -17.7 [-27.5, -4.2] | yes |
| nc | -54.4 [-95.4, -40.3] | -16.4% | -95.7 [-116.8, -42.3] | -55.7 [-101.1, -40.5] | -61.1 [-91.3, -31.5] | yes |
| lookup | +22.4 [+9.7, +30.5] | +10.9% | +7.9 [-5.3, +26.0] | +22.0 [+5.4, +33.5] | +26.8 [+11.9, +38.5] | no |

Per kind (pooled learners):

| kind vs | Δ (s) [95 % CI] | rel |
|---|---|---|
| none_vs_evsched | +2.4 [-4.5, +34.7] | +1.9% |
| none_vs_mpcf | -2.7 [-21.2, +4.6] | -1.4% |
| slow_vs_evsched | -17.3 [-21.6, -5.1] | -6.4% |
| slow_vs_mpcf | -4.0 [-10.7, +4.7] | -1.5% |
| block_vs_evsched | -26.9 [-51.9, -5.8] | -10.9% |
| block_vs_mpcf | -4.7 [-18.3, +10.4] | -2.0% |
| surge_vs_evsched | -2.0 [-16.8, +34.3] | -0.9% |
| surge_vs_mpcf | -8.9 [-31.2, +1.1] | -3.2% |

FAIL runs: {'drl2': 5, 'drl0': 5, 'pooled': 9, 'meter106': 5, 'lookup': 10, 'mpcf': 9, 'drl1': 10, 'nc': 27, 'evsched': 10}
Teleport runs: {'drl2': 5, 'drl0': 5, 'pooled': 9, 'meter106': 5, 'lookup': 10, 'mpcf': 9, 'drl1': 10, 'nc': 27, 'evsched': 10}

## Notes

- **MPC-F bug.** On the first pass, all 400 MPC-F runs crashed: their features were float64 against a float32 network. Fixed, and the arm was re-run before any analysis; no results were produced by the crashed runs. The other arms are unaffected.
- **Reading, unchanged from the pre-registration: NO.**
  - Only learner seed 0 (the P-M3b screening winner) beats `evsched` (−6.6 s, CI [−24.9, −0.3]) and MPC-F (−17.0 s, CI [−25.5, −8.3]).
  - Seeds 1 and 2 do not, so "≥ 2 of 3 learner seeds" fails.
- **The pooled DRL robustly beats** `meter:10:6` (−7.4 %) and NC (−16.4 %).
- **Per kind,** DRL beats `evsched` under slowdowns (−6.4 %) and blockages (−10.9 %), both with CIs excluding 0.
- **Interpretation:** the headroom (lookup ≈ 9 % ahead of `evsched` on these seeds) exists, and one learner exploits part of it. Training is not yet reliable across seeds.
