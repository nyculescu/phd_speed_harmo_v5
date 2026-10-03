# T1-M DRL pilots (P-M): screening

## P-M screening (2026-10-03 07:31) · seeds 7110330-7110339 · q=1600 · run `/home/catalin/work/phd/vsl_lab_runs/t1/train/pm_bn4/bn4_ppo_tts_u500_e16_s0_1791037840_pid3228525`

Median over seeds of J(s) = mean over the 4 kinds of door-to-door time (s): lookup 197.1, evsched 197.9, drl_final 237.6, meter106 242.2, pooled 256.1, nc 323.4

| comparison | median paired Δ (s) | rel | 95 % CI (s) |
|---|---|---|---|
| drl_final_vs_evsched | +34.3 | +17.3% | [+17.5, +73.0] |
| drl_final_vs_pooled | -16.9 | -6.6% | [-38.9, +41.8] |
| drl_final_vs_lookup | +46.7 | +23.7% | [+7.6, +76.5] |
| drl_final_vs_meter106 | -8.1 | -3.3% | [-25.2, +27.0] |
| drl_final_vs_nc | -62.2 | -19.2% | [-130.8, +16.6] |

FAIL runs: {'pooled': 0, 'meter106': 0, 'lookup': 1, 'nc': 1, 'evsched': 0, 'drl_final': 0}
**final PASS: False** · best PASS: None

## P-M screening (2026-10-03 07:49) · seeds 7110330-7110339 · q=1600 · run `/home/catalin/work/phd/vsl_lab_runs/t1/train/pm2_bn4/bn4_ppo_tts_u500_e16_s0_1791037951_pid3229997`

Median over seeds of J(s) = mean over the 4 kinds of door-to-door time (s): lookup 197.1, evsched 197.9, drl_final 225.9, drl_best 240.6, meter106 242.2, pooled 256.1, nc 323.4

| comparison | median paired Δ (s) | rel | 95 % CI (s) |
|---|---|---|---|
| drl_final_vs_evsched | +0.2 | +0.1% | [-26.3, +51.3] |
| drl_final_vs_pooled | -14.0 | -5.5% | [-51.9, +18.3] |
| drl_final_vs_lookup | +12.7 | +6.5% | [-10.1, +67.6] |
| drl_final_vs_meter106 | -26.5 | -11.0% | [-52.9, +34.0] |
| drl_final_vs_nc | -65.7 | -20.3% | [-124.8, -22.1] |
| drl_best_vs_evsched | +10.3 | +5.2% | [-15.6, +48.5] |
| drl_best_vs_pooled | -5.7 | -2.2% | [-63.7, +27.7] |
| drl_best_vs_lookup | +19.0 | +9.7% | [-4.2, +57.8] |
| drl_best_vs_meter106 | -18.5 | -7.7% | [-42.2, +11.3] |
| drl_best_vs_nc | -64.7 | -20.0% | [-140.2, -19.8] |

FAIL runs: {'pooled': 0, 'meter106': 0, 'lookup': 1, 'nc': 1, 'evsched': 0, 'drl_best': 1, 'drl_final': 2}
**final PASS: False** · best PASS: False

