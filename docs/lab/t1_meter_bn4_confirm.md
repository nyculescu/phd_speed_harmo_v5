# BN4 confirmatory under the conditional bar (Addendum I; D5.8)

*2026-10-11 15:04 · seeds 7112400-7112609 (210) × 4 kinds · q = 1600 · candidate (plain-DRL meter) 64a03374f320… · ALINEA alinea:70:8 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/bn4_confirm/test_1791755535`*

**Conditional bar: PASS** · 1_vs_nc: yes · 2_beats_best_in_a_regime: yes · 3_never_worse_gt5: yes · 4_fail_share: yes

Median J (s): candidate 153.6, const 186.8, hybrid 218.7, evsched 222.9, mpcf 235.2, alinea 246.3, pooled 246.7, nc 328.0

| candidate vs (pooled) | Δ (s) [95 % CI] | rel |
|---|---|---|
| pooled | -80.4 [-90.6, -73.9] | -32.6% |
| mpcf | -65.5 [-81.4, -60.5] | -27.9% |
| const | -35.1 [-42.0, -26.5] | -18.8% |
| nc | -161.6 [-178.9, -144.4] | -49.3% |
| hybrid | -59.8 [-67.5, -50.2] | -27.3% |
| evsched | -58.2 [-70.0, -50.2] | -26.1% |
| alinea | -77.3 [-83.3, -70.9] | -31.4% |

| regime | best tuned non-learning B | candidate vs B: Δ (s) [Bonferroni CI] | rel | beats B | worse > 5 % |
|---|---|---|---|---|---|
| none | const | -0.8 [-3.5, +4.7] | -0.8% | no | no |
| slow | pooled | -42.7 [-57.0, -34.3] | -17.0% | yes | no |
| block | const | -63.1 [-81.0, -48.5] | -27.9% | yes | no |
| surge | const | +5.7 [-2.0, +14.3] | +4.5% | no | no |

Candidate FAIL share 2.1% · FAIL runs {'pooled': 26, 'mpcf': 24, 'const': 21, 'nc': 50, 'hybrid': 25, 'evsched': 14, 'candidate': 18, 'alinea': 27}
