# Lead 1 stage S: headroom scan (varied severity/duration) results

*2026-10-03 20:10 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/m2scan_1791082000` · q = 1600 · seeds 7170000-7170009*

**Proceed to stage H (G ≥ 10 % and H_pre ≥ 10 % on all conditions): YES**

| family | G | H_pre | pooled best | J pooled | J lookup | J evsched |
|---|---|---|---|---|---|---|
| all | 12.0% | 12.0% | meter:5:10 | 243.1 | 213.9 | 264.2 |
| slow | 5.3% | 5.3% | meter:40:8 | 278.5 | 263.7 | 316.2 |
| block | 13.0% | 13.0% | meter:5:10 | 199.4 | 173.4 | 250.2 |
| surge | 2.2% | 2.2% | meter:5:10 | 160.5 | 156.9 | 188.4 |

Per-condition best fixed setting: {"none": "meter:10:8", "slow_v3_d150": "meter:40:8", "slow_v3_d300": "meter:40:8", "slow_v3_d600": "meter:20:12", "slow_v5_d150": "meter:40:8", "slow_v5_d300": "meter:40:8", "slow_v5_d600": "meter:40:12", "slow_v8_d150": "meter:10:10", "slow_v8_d300": "meter:40:8", "slow_v8_d600": "nc", "block_d60": "meter:40:8", "block_d180": "meter:20:10", "block_d360": "meter:10:12", "surge_f1.15_d150": "meter:10:8", "surge_f1.15_d300": "meter:5:8", "surge_f1.15_d600": "meter:5:10", "surge_f1.3_d150": "meter:5:10", "surge_f1.3_d300": "meter:5:10", "surge_f1.3_d600": "meter:5:10", "surge_f1.5_d150": "meter:5:10", "surge_f1.5_d300": "meter:20:6", "surge_f1.5_d600": "meter:5:10"}

FAIL runs: {'none': 0, 'slow_v3_d150': 1, 'slow_v3_d300': 0, 'slow_v3_d600': 3, 'slow_v5_d150': 0, 'slow_v5_d300': 1, 'slow_v5_d600': 1, 'slow_v8_d150': 1, 'slow_v8_d300': 0, 'slow_v8_d600': 1, 'block_d60': 13, 'block_d180': 13, 'block_d360': 209, 'surge_f1.15_d150': 0, 'surge_f1.15_d300': 0, 'surge_f1.15_d600': 0, 'surge_f1.3_d150': 0, 'surge_f1.3_d300': 0, 'surge_f1.3_d600': 0, 'surge_f1.5_d150': 0, 'surge_f1.5_d300': 0, 'surge_f1.5_d600': 0}
