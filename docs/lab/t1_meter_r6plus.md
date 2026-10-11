# R6+: the R6 hybrid vs a fair vanilla DRL and no control (bar D5.1), with the operating map

*2026-10-11 13:15 · protocol `docs/lab/t1_meter_gscan_protocol.md` Addendum G · seeds 7112700-7112909 (210) × 4 kinds · q = 1600 · hybrid d855ba4c7cf0… · vanilla 64a03374f320… · raw `/home/catalin/work/phd/vsl_lab_runs/t1/r6plus_1791749015`*

**Pre-registered bar: the hybrid beats the vanilla DRL and no control by ≥ 10 % each (CI upper bound < 0), hybrid FAIL share ≤ 5 %: FAIL** (vanilla: no, no control: yes)

Median J (mean over the 4 kinds of door-to-door time, s): vanilla 153.0, lookup 211.3, evsched 222.3, hybrid 235.1, pooled 235.6, mpcf 243.8, meter106 250.0, nc 314.9

| hybrid vs | median paired Δ (s) | 95 % CI (s) | rel | role |
|---|---|---|---|---|
| vanilla | +67.0 | [+52.3, +85.8] | +43.8% | bar |
| nc | -66.4 | [-84.5, -49.7] | -21.1% | bar |
| evsched | -5.3 | [-13.2, +0.4] | -2.4% | reported |
| mpcf | -5.3 | [-9.1, -1.0] | -2.2% | reported |
| pooled | -3.4 | [-11.2, +2.2] | -1.5% | reported |
| meter106 | -24.4 | [-29.5, -13.2] | -9.8% | reported |
| lookup | +13.1 | [+1.8, +22.8] | +6.2% | reported |

Vanilla DRL vs no control: -153.6 s [-175.9, -132.9] (-48.8%).

**Operating map** (per kind; regime from the Bonferroni CI over 16 comparisons):

| kind vs | Δ (s) [95 % CI] | rel | regime |
|---|---|---|---|
| none_vs_vanilla | +59.5 [+37.9, +83.5] | +56.4% | hybrid worse |
| none_vs_nc | -87.9 [-110.5, -67.4] | -28.3% | hybrid better |
| none_vs_evsched | -2.1 [-9.3, +14.8] | -1.7% | tie |
| none_vs_mpcf | -4.2 [-7.7, +3.9] | -2.1% | tie |
| slow_vs_vanilla | +54.1 [+44.1, +63.0] | +27.1% | hybrid worse |
| slow_vs_nc | -53.2 [-71.3, -31.1] | -16.2% | hybrid better |
| slow_vs_evsched | -12.8 [-19.7, -6.3] | -4.7% | hybrid better |
| slow_vs_mpcf | +0.0 [-7.3, +5.1] | +0.0% | tie |
| block_vs_vanilla | +40.4 [+27.1, +48.9] | +27.1% | hybrid worse |
| block_vs_nc | -33.3 [-59.1, -16.5] | -12.7% | hybrid better |
| block_vs_evsched | -45.2 [-61.1, -30.9] | -18.2% | hybrid better |
| block_vs_mpcf | -21.6 [-28.6, -7.2] | -9.3% | hybrid better |
| surge_vs_vanilla | +99.3 [+84.6, +120.1] | +67.1% | hybrid worse |
| surge_vs_nc | -106.5 [-123.3, -86.7] | -27.3% | hybrid better |
| surge_vs_evsched | +6.0 [-10.1, +35.8] | +3.0% | tie |
| surge_vs_mpcf | -6.7 [-18.6, +3.5] | -2.3% | tie |

**Robustness (report-only):** 90th-percentile J: vanilla 208.3, lookup 292.5, hybrid 327.2, meter106 328.3, mpcf 332.1, pooled 335.2, evsched 356.3, nc 415.0 · seeds where the hybrid is worse than no control: 20.0% · FAIL runs {'pooled': 24, 'meter106': 15, 'lookup': 20, 'mpcf': 19, 'vanilla': 19, 'nc': 57, 'hybrid': 21, 'evsched': 14}
