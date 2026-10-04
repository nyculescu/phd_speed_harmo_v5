# R5-M: DRL (RecurrentPPO) scheduling the feedback meter vs tuned non-learning control

*2026-10-03 14:37 · protocol `docs/lab/t1_meter_gscan_protocol.md` Addenda D/E · policy `final_model.zip` · test seeds 7110690-7110789 × 4 kinds · q = 1600 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/r5m_1791062797`*

**Pre-registered reading - DRL measurably improves on the best non-learning control (beats evsched AND MPC-F, pooled and in ≥ 2 of 3 learner seeds; no kind significantly worse by > 5 %; FAIL share ≤ 5 %): NO**

Median over seeds of J (mean over the 4 kinds of door-to-door time, s): lookup 205.2, drl0 216.3, drlf0 216.3, drl2 216.7, drlf2 216.7, drl_pooled 216.8, evsched 226.3, drl1 228.2, drlf1 228.2, mpcf 235.1, meter106 240.7, pooled 241.5, nc 326.9

| DRL vs | pooled Δ (s) [95 % CI] | rel | seed 0 | seed 1 | seed 2 | beats (pooled & ≥ 2/3) |
|---|---|---|---|---|---|---|
| evsched | -6.0 [-13.2, +0.9] | -2.7% | -11.6 [-22.6, +0.4] | -8.5 [-15.2, -3.2] | -0.2 [-15.5, +8.6] | no |
| mpcf | -3.3 [-18.8, +2.2] | -1.4% | -11.5 [-22.1, +2.5] | -11.7 [-20.3, -1.1] | -3.6 [-17.4, +3.6] | no |
| pooled | -7.0 [-17.4, +0.8] | -2.9% | -19.0 [-25.6, -8.0] | -6.8 [-15.9, +1.0] | -5.7 [-23.2, +4.2] | no |
| meter106 | -30.1 [-41.5, -21.8] | -12.5% | -35.8 [-43.1, -21.5] | -32.0 [-45.3, -23.2] | -26.0 [-33.9, -15.2] | yes |
| nc | -96.3 [-116.8, -67.9] | -29.5% | -92.2 [-117.9, -67.7] | -86.8 [-113.5, -67.5] | -95.2 [-123.4, -53.9] | yes |
| lookup | +5.0 [-1.5, +23.2] | +2.4% | +6.9 [-1.0, +19.7] | +5.8 [-5.2, +24.1] | +7.7 [-2.3, +24.8] | no |

Per kind (pooled learners):

| kind vs | Δ (s) [95 % CI] | rel |
|---|---|---|
| none_vs_evsched | -0.1 [-10.0, +16.4] | -0.1% |
| none_vs_mpcf | -4.4 [-23.4, +3.3] | -2.3% |
| slow_vs_evsched | -15.3 [-22.6, -9.1] | -5.4% |
| slow_vs_mpcf | +6.1 [-2.9, +17.8] | +2.3% |
| block_vs_evsched | -33.1 [-58.1, -20.7] | -13.9% |
| block_vs_mpcf | -18.5 [-45.7, +4.6] | -8.2% |
| surge_vs_evsched | -0.7 [-16.4, +17.9] | -0.3% |
| surge_vs_mpcf | -24.9 [-42.9, +3.3] | -8.9% |

FAIL runs: {'drl2': 10, 'drl0': 8, 'pooled': 9, 'meter106': 5, 'lookup': 8, 'mpcf': 3, 'drl1': 7, 'nc': 26, 'drlf0': 5, 'evsched': 5, 'drlf2': 10, 'drlf1': 4}
Teleport runs: {'drl2': 10, 'drl0': 8, 'pooled': 9, 'meter106': 5, 'lookup': 8, 'mpcf': 3, 'drl1': 7, 'nc': 26, 'drlf0': 5, 'evsched': 5, 'drlf2': 10, 'drlf1': 4}
