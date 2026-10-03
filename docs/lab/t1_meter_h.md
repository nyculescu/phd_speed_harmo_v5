# T1-M H step (gate seeds 7,110,180-7,110,199): results

*2026-10-03 07:27 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/meter_h2_1791037477` · evsched tuned on H1: `evsched:7:20:1.15`*

**DRL target (H ≥ 10 % and CI lower bound > 0): ['1600']**

| q | nc | meter:10:6 | pooled fixed | evsched | lookup I (oracle) | best non-learning | H | Δ (s) [95 % CI] |
|---|---|---|---|---|---|---|---|---|
| 1600 | 324.8 | 237.8 | 300.2 | 225.3 | 227.5 | evsched | 20.4% | +46.0 [+18.2, +78.9] |
| 2000 | 572.5 | 420.6 | 363.8 | 379.9 | 400.6 | pooled | -3.3% | -11.9 [-36.1, +10.0] |

J = per-seed mean over the 4 kinds (none, slow, block, surge) of door-to-door time (s); table shows medians over seeds.

**Per-kind check at q = 1,600** (medians over 20 gate seeds, door-to-door in s):

| Controller | none | slow | block | surge |
|---|---|---|---|---|
| lookup | 150.4 | 266.5 | 278.4 | 171.3 |
| evsched | 190.2 | 295.4 | 279.2 | 215.2 |

- The lookup beats `evsched` in 16 of 20 seeds; the per-seed paired differences range from −70 to +171 s.
- The near-equal marginal medians of the per-seed means (225 vs 227) reflect a heavy tail across seeds. The pre-registered statistic is the median of paired differences.
- `evsched` loses mostly in `none` and `surge`: its tuned surge threshold (1.15) fires falsely in normal traffic.
