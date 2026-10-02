# Track 1 (BN4), R1 plant checks: results

*2026-10-01 22:19 · protocol `docs/lab/t1_bn4_plant_checks_protocol.md` · raw runs `/home/catalin/work/phd/vsl_lab_runs/t1/r1_1790917936` · workers 12*

## T1 capacity drop (lane changing off): **FAIL**

- 220 runs; health {'PASS': 81, 'WARN': 16, 'FAIL': 123}; runs with codes {'H-R1': 123, 'H-R2': 76}; teleports 0.
- Peak median outflow **1087 veh/h** at q = 1200; mean median outflow at q = 2,200–2,500 **900 veh/h**; ratio **0.828** (PASS needs ≤ 0.95).

| q (veh/h) | median outflow | min | max |
|---|---|---|---|
| 400 | 410 | 317 | 468 |
| 500 | 500 | 410 | 612 |
| 600 | 634 | 526 | 677 |
| 700 | 680 | 626 | 878 |
| 800 | 796 | 684 | 922 |
| 900 | 893 | 792 | 1051 |
| 1000 | 990 | 878 | 1152 |
| 1100 | 1004 | 900 | 1123 |
| 1200 | 1087 | 900 | 1260 |
| 1300 | 904 | 893 | 1174 |
| 1400 | 900 | 900 | 958 |
| 1500 | 900 | 900 | 950 |
| 1600 | 900 | 900 | 907 |
| 1700 | 900 | 893 | 907 |
| 1800 | 900 | 900 | 900 |
| 1900 | 900 | 893 | 907 |
| 2000 | 900 | 893 | 900 |
| 2100 | 900 | 900 | 907 |
| 2200 | 900 | 900 | 907 |
| 2300 | 900 | 893 | 900 |
| 2400 | 900 | 893 | 900 |
| 2500 | 900 | 900 | 900 |

## T1-L (lane changing on; exploratory)

- 220 runs; health {'PASS': 81, 'WARN': 16, 'FAIL': 123}; teleports 0; peak 1141 veh/h at q = 1200; high mean 900; ratio 0.789.

## T0 actuator (AV cap): **FAIL**

- 60 runs; health {'PASS': 11, 'WARN': 4, 'FAIL': 45}.

| cell | none median | median Δ (cap − none) | 95 % CI | rel. | binds | median lag (s) |
|---|---|---|---|---|---|---|
| q1200_cap10 | 900 | +0 | [-166, +7] | +0.0% | False | 25.0 |
| q1200_cap5 | 900 | -11 | [-158, +18] | -1.2% | False | 0.0 |
| q2000_cap10 | 900 | +0 | [+0, +0] | +0.0% | False | 210.0 |
| q2000_cap5 | 900 | +0 | [-32, +4] | +0.0% | False | 0.0 |

## T3 determinism: **PASS**

- 10/10 identical hashes.

