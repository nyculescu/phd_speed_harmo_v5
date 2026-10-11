# R6+ diagnostics (Addendum H; post-result, cannot change the R6+ FAIL)

*2026-10-11 14:10 · tuning seeds 7112100-7112199 · test = R6+ seeds · OOD seeds 7112300-7112399 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/r6plus_diag`*

## (a) Constant metering rate: **adaptive learning beyond a constant rate**

Pooled-best constant rate on tuning seeds: **1800 veh/h** (per-kind oracle: {'none': 'rate1800', 'slow': 'rate1800', 'block': 'rate1800', 'surge': 'rate1800'}).

Median J on the R6+ test seeds (s): vanilla 153.0, const_pooled 193.6, const_per_kind_oracle 193.6, lookup 211.3, evsched 222.3, hybrid 235.1, mpcf 243.8, nc 314.9

| comparison | Δ (s) [95 % CI] | rel |
|---|---|---|
| vanilla_vs_const | -32.2 [-43.3, -25.4] | -16.6% |
| hybrid_vs_const | +15.4 [+9.0, +23.9] | +8.0% |
| const_vs_nc | -96.5 [-113.6, -76.5] | -30.6% |
| vanilla_vs_const_oracle | -32.2 [-43.3, -25.5] | -16.6% |

R6's tuned non-learning set missed a strong baseline: **yes** (the pooled-best constant rate beats the hybrid with the CI excluding 0).

## (b) Out-of-distribution: **no robustness advantage of the hybrid on BN4**

Degradation ratio (median J, OOD families pooled / in-distribution): hybrid 1.21, vanilla 1.27.

| family | const | evsched | hybrid | mpcf | nc | vanilla |
|---|---|---|---|---|---|---|
| block_ood | 207.8 | 205.2 | 202.0 | 226.7 | 307.6 | 147.3 |
| in_dist | 196.3 | 213.3 | 208.4 | 242.7 | 324.4 | 149.7 |
| inflow_1200 | 107.9 | 114.0 | 105.7 | 106.8 | 103.6 | 91.7 |
| inflow_2000 | 336.3 | 380.5 | 382.1 | 417.3 | 569.4 | 294.5 |
| slow_ood | 327.7 | 341.6 | 319.0 | 315.7 | 358.5 | 248.0 |
| surge_ood | 165.4 | 209.2 | 254.0 | 285.3 | 422.8 | 161.6 |

| hybrid vs (family) | Δ (s) [95 % CI] | rel | regime (Bonferroni) |
|---|---|---|---|
| block_ood_vs_vanilla | +50.0 [+38.7, +64.2] | +34.0% | hybrid worse |
| block_ood_vs_nc | -59.2 [-98.1, -28.5] | -19.2% | hybrid better |
| block_ood_vs_evsched | -19.5 [-33.0, +7.3] | -9.5% | tie |
| block_ood_vs_const | -14.0 [-27.7, -7.1] | -6.7% | hybrid better |
| in_dist_vs_vanilla | +50.5 [+44.4, +56.7] | +33.7% | hybrid worse |
| in_dist_vs_nc | -90.7 [-120.6, -65.0] | -28.0% | hybrid better |
| in_dist_vs_evsched | -7.3 [-15.7, -1.8] | -3.4% | tie |
| in_dist_vs_const | +1.5 [-8.2, +9.9] | +0.8% | tie |
| inflow_1200_vs_vanilla | +13.7 [+10.5, +18.4] | +14.9% | hybrid worse |
| inflow_1200_vs_nc | +2.0 [-3.2, +6.0] | +2.0% | tie |
| inflow_1200_vs_evsched | -5.7 [-10.0, -0.8] | -5.0% | tie |
| inflow_1200_vs_const | -2.3 [-5.6, +0.6] | -2.2% | tie |
| inflow_2000_vs_vanilla | +97.0 [+81.2, +114.5] | +32.9% | hybrid worse |
| inflow_2000_vs_nc | -177.2 [-204.1, -151.8] | -31.1% | hybrid better |
| inflow_2000_vs_evsched | -11.7 [-33.2, +11.6] | -3.1% | tie |
| inflow_2000_vs_const | +15.3 [+1.7, +40.4] | +4.6% | tie |
| slow_ood_vs_vanilla | +63.7 [+56.4, +73.4] | +25.7% | hybrid worse |
| slow_ood_vs_nc | -16.1 [-43.1, -5.7] | -4.5% | tie |
| slow_ood_vs_evsched | -23.0 [-26.7, -19.8] | -6.7% | hybrid better |
| slow_ood_vs_const | -3.9 [-6.8, +2.2] | -1.2% | tie |
| surge_ood_vs_vanilla | +84.3 [+66.9, +105.6] | +52.2% | hybrid worse |
| surge_ood_vs_nc | -132.6 [-175.2, -106.6] | -31.4% | hybrid better |
| surge_ood_vs_evsched | +25.7 [+10.1, +39.7] | +12.3% | hybrid worse |
| surge_ood_vs_const | +74.9 [+56.3, +83.7] | +45.3% | hybrid worse |
