# Track 1 (BN4), R1 plant checks: results

*2026-10-01 23:12 · protocol `docs/lab/t1_bn4_plant_checks_protocol.md` · raw runs `/home/catalin/work/phd/vsl_lab_runs/t1/r1_1790920729` · workers 10*

## T1 capacity drop (lane changing off): **PASS**

- 220 runs; health {'PASS': 136, 'WARN': 84, 'FAIL': 0}; runs with codes {'H-R2': 77, 'H-R4b': 9}; teleports 0.
- Peak median outflow **1044 veh/h** at q = 1300; mean median outflow at q = 2,200–2,500 **900 veh/h**; ratio **0.862** (PASS needs ≤ 0.95).

| q (veh/h) | median outflow | min | max |
|---|---|---|---|
| 400 | 414 | 302 | 446 |
| 500 | 493 | 410 | 605 |
| 600 | 626 | 490 | 691 |
| 700 | 680 | 634 | 878 |
| 800 | 803 | 677 | 929 |
| 900 | 900 | 785 | 1073 |
| 1000 | 972 | 850 | 1130 |
| 1100 | 1030 | 900 | 1274 |
| 1200 | 1033 | 893 | 1109 |
| 1300 | 1044 | 900 | 1267 |
| 1400 | 900 | 893 | 1354 |
| 1500 | 900 | 893 | 1267 |
| 1600 | 900 | 900 | 900 |
| 1700 | 900 | 900 | 907 |
| 1800 | 900 | 893 | 900 |
| 1900 | 900 | 893 | 907 |
| 2000 | 900 | 893 | 907 |
| 2100 | 900 | 893 | 907 |
| 2200 | 900 | 893 | 900 |
| 2300 | 900 | 893 | 907 |
| 2400 | 900 | 893 | 900 |
| 2500 | 900 | 893 | 907 |

## T1-L (lane changing on; exploratory)

- 220 runs; health {'PASS': 129, 'WARN': 91, 'FAIL': 0}; teleports 0; peak 1289 veh/h at q = 1400; high mean 900; ratio 0.698.

## T0 actuator (AV cap): **FAIL**

- 60 runs; health {'PASS': 10, 'WARN': 50, 'FAIL': 0}.

| cell | none median | median Δ (cap − none) | 95 % CI | rel. | binds | median lag (s) |
|---|---|---|---|---|---|---|
| q1200_cap10 | 972 | -4 | [-198, +86] | -0.4% | False | 10.0 |
| q1200_cap5 | 972 | -61 | [-238, +7] | -6.3% | False | 5.0 |
| q2000_cap10 | 900 | +0 | [+0, +0] | +0.0% | False | 120.0 |
| q2000_cap5 | 900 | +14 | [-14, +25] | +1.6% | False | 0.0 |

## T3 determinism: **PASS**

- 10/10 identical hashes.


## T0b (preventive actuator authority): results

*2026-10-01 23:14 · 160 runs · health {'PASS': 113, 'WARN': 47} · raw `/home/catalin/work/phd/vsl_lab_runs/t1/t0b_1790921574`*

**AV cap family: PASS · meter: PASS**

| cell | nc median outflow | arm median outflow | Δ outflow [95 % CI] | rel. | Δ time in system (s) [95 % CI] |
|---|---|---|---|---|---|
| q1600_cap:5 | 1054 | 878 | -172 [-270, -100] | -16.3% | +149.5 [+92.9, +221.6] |
| q1600_cap:10 | 1054 | 936 | -110 [-198, -58] | -10.4% | +95.5 [+48.4, +149.0] |
| q1600_meter:20:8 | 1054 | 1372 | +212 [+88, +370] | +20.1% | -93.9 [-175.9, -34.9] |
| q2000_cap:5 | 966 | 884 | -84 [-102, -56] | -8.7% | +78.8 [+52.5, +95.6] |
| q2000_cap:10 | 966 | 936 | -32 [-60, -10] | -3.3% | +31.9 [+7.6, +55.1] |
| q2000_meter:20:8 | 966 | 1164 | +214 [+56, +368] | +22.1% | -192.9 [-255.2, -69.0] |
