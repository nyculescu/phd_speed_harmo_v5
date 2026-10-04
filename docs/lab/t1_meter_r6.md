# R6 confirmatory: frozen DRL meter scheduler vs tuned non-learning control

*2026-10-03 19:37 · protocol `docs/lab/t1_meter_gscan_protocol.md` Addendum F · reserved seeds 7110790-7110999 (210) × 4 kinds · q = 1600 · candidate sha256 d855ba4c7cf0… · raw `/home/catalin/work/phd/vsl_lab_runs/t1/r6m_1791080803`*

**Pre-registered claim - the frozen DRL controller measurably improves on the best non-learning control (beats the event scheduler AND the fitted-model MPC; no kind significantly worse by > 5 %; FAIL share ≤ 5 %): YES**

Median over seeds of J (mean over the 4 kinds of door-to-door time, s): lookup 208.8, drl 219.3, evsched 220.3, mpcf 236.8, meter106 242.0, pooled 242.9, nc 313.7

| DRL vs | median paired Δ (s) | 95 % CI (s) | rel | beats |
|---|---|---|---|---|
| evsched | -9.4 | [-14.7, -4.9] | -4.3% | yes |
| mpcf | -6.0 | [-14.9, -0.8] | -2.5% | yes |
| pooled | -10.5 | [-17.9, -4.7] | -4.3% | yes |
| meter106 | -25.9 | [-31.6, -19.4] | -10.7% | yes |
| nc | -81.0 | [-97.2, -62.0] | -25.8% | yes |
| lookup | +12.1 | [+3.7, +19.1] | +5.8% | no |

| kind vs | Δ (s) [95 % CI] | rel |
|---|---|---|
| none_vs_evsched | -5.5 [-8.8, +2.7] | -4.1% |
| none_vs_mpcf | -0.6 [-5.6, +4.5] | -0.3% |
| slow_vs_evsched | -14.0 [-19.6, -9.9] | -4.9% |
| slow_vs_mpcf | +8.1 [+1.1, +14.3] | +3.1% |
| block_vs_evsched | -48.0 [-54.6, -37.1] | -19.0% |
| block_vs_mpcf | -20.5 [-31.0, -11.1] | -8.7% |
| surge_vs_evsched | +21.5 [-4.2, +39.4] | +11.4% |
| surge_vs_mpcf | -6.8 [-15.6, -1.3] | -2.5% |

FAIL runs: {'pooled': 20, 'meter106': 6, 'lookup': 29, 'mpcf': 23, 'drl': 14, 'nc': 63, 'evsched': 23} · DRL FAIL share 1.7%

## Caveats (stated with the claim)

1. **The effect sizes are modest:** −4.3 % against the event scheduler and −2.5 % against MPC-F. The MPC-F CI upper bound (−0.8 s) only just excludes 0.
2. **Per-kind trade-offs:**
   - DRL is significantly *worse* than MPC-F under slowdowns: +3.1 %, CI [+1.1, +14.3]. That is within the pre-registered 5 % tolerance.
   - DRL is worse than `evsched` under surges: +11.4 %, n.s.
   - The gains come mainly from blockages (−19 % / −8.7 %) and slowdowns against `evsched` (−4.9 %).
3. **Search history** (it must accompany the claim):
   - targets screened: LD3 harmonisation (killed), corridor (killed), and the BN4 meter (H = 20 % at q = 1,600);
   - pilots: P-M (void), P-M2, P-M3 a, b and c, the F class (seeds 1–2), and P-M4 (seeds 3–5);
   - R5-M was NO, R5-M2 was NO; the R6 candidate was selected on validation only.
4. **R6 used only untouched reserved seeds.** The earlier R5-M2 breach of the reserved range (7,110,700–789) is disclosed in the protocol.
5. **Scope.** The plant is SUMO BN4 (the Vinitsky/Flow zipper bottleneck, IDM, 10 % uncontrolled AVs) at q = 1,600, with synthetic perturbations: slowdown, broken-down vehicle and surge. No claim is made at q = 2,000, where H was −3 %, or for other plants.
