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

## P-M screening (2026-10-03 08:53) · seeds 7110340-7110389 · q=1600 · run `/home/catalin/work/phd/vsl_lab_runs/t1/train/pm3a_bn4/bn4_ppo_tts_u1000_e16_s0_1791039044_pid3286313`

Median over seeds of J(s) = mean over the 4 kinds of door-to-door time (s): drl_best 210.0, lookup 228.2, meter106 237.6, evsched 239.1, drl_final 262.9, pooled 272.9, nc 310.2

| comparison | median paired Δ (s) | rel | 95 % CI (s) |
|---|---|---|---|
| drl_final_vs_evsched | +8.4 | +3.5% | [-9.6, +29.3] |
| drl_final_vs_pooled | -3.9 | -1.4% | [-9.3, +7.3] |
| drl_final_vs_lookup | +28.1 | +12.3% | [+2.6, +51.1] |
| drl_final_vs_meter106 | -8.1 | -3.4% | [-29.8, +9.5] |
| drl_final_vs_nc | -27.6 | -8.9% | [-64.7, -0.9] |
| drl_best_vs_evsched | -4.9 | -2.1% | [-21.5, +6.4] |
| drl_best_vs_pooled | -8.0 | -2.9% | [-30.0, +1.1] |
| drl_best_vs_lookup | -4.8 | -2.1% | [-13.5, +26.6] |
| drl_best_vs_meter106 | -29.3 | -12.3% | [-40.0, -17.4] |
| drl_best_vs_nc | -69.6 | -22.4% | [-106.6, -38.3] |

FAIL runs: {'pooled': 7, 'meter106': 2, 'lookup': 7, 'nc': 14, 'evsched': 4, 'drl_best': 5, 'drl_final': 9}
**final PASS: False** · best PASS: False

## P-M screening (2026-10-03 08:57) · seeds 7110340-7110389 · q=1600 · run `/home/catalin/work/phd/vsl_lab_runs/t1/train/pm3b_bn4/bn4_recurrentppo_tts_u1000_e16_s0_1791039044_pid3286315`

Median over seeds of J(s) = mean over the 4 kinds of door-to-door time (s): drl_final 208.4, drl_best 223.6, lookup 228.2, meter106 237.6, evsched 239.1, pooled 272.9, nc 310.2

| comparison | median paired Δ (s) | rel | 95 % CI (s) |
|---|---|---|---|
| drl_final_vs_evsched | -23.0 | -9.6% | [-40.8, -6.7] |
| drl_final_vs_pooled | -28.0 | -10.2% | [-39.9, -7.5] |
| drl_final_vs_lookup | -2.4 | -1.0% | [-22.2, +10.6] |
| drl_final_vs_meter106 | -31.6 | -13.3% | [-43.3, -17.0] |
| drl_final_vs_nc | -79.8 | -25.7% | [-111.1, -48.9] |
| drl_best_vs_evsched | -11.8 | -4.9% | [-25.8, +11.2] |
| drl_best_vs_pooled | -7.5 | -2.7% | [-32.6, +3.6] |
| drl_best_vs_lookup | +13.6 | +6.0% | [-7.2, +21.9] |
| drl_best_vs_meter106 | -21.4 | -9.0% | [-30.5, -10.5] |
| drl_best_vs_nc | -65.0 | -20.9% | [-89.8, -29.5] |

FAIL runs: {'pooled': 7, 'meter106': 2, 'lookup': 7, 'nc': 14, 'evsched': 4, 'drl_best': 6, 'drl_final': 3}
**final PASS: True** · best PASS: False

## P-M screening (2026-10-03 09:02) · seeds 7110340-7110389 · q=1600 · run `/home/catalin/work/phd/vsl_lab_runs/t1/train/pm3c_bn4/bn4_ppo_tts_u1000_e16_s0_1791039044_pid3286316`

Median over seeds of J(s) = mean over the 4 kinds of door-to-door time (s): lookup 228.2, meter106 237.6, evsched 239.1, drl_best 253.5, drl_final 262.5, pooled 272.9, nc 310.2

| comparison | median paired Δ (s) | rel | 95 % CI (s) |
|---|---|---|---|
| drl_final_vs_evsched | +6.3 | +2.6% | [-17.4, +23.8] |
| drl_final_vs_pooled | -4.4 | -1.6% | [-13.3, +5.2] |
| drl_final_vs_lookup | +31.9 | +14.0% | [+1.9, +52.7] |
| drl_final_vs_meter106 | -13.8 | -5.8% | [-28.4, +25.0] |
| drl_final_vs_nc | -26.1 | -8.4% | [-65.5, -11.8] |
| drl_best_vs_evsched | +0.8 | +0.3% | [-20.4, +21.5] |
| drl_best_vs_pooled | -3.5 | -1.3% | [-14.5, +2.2] |
| drl_best_vs_lookup | +24.2 | +10.6% | [+2.4, +44.6] |
| drl_best_vs_meter106 | -16.0 | -6.7% | [-32.8, +5.6] |
| drl_best_vs_nc | -27.4 | -8.8% | [-72.7, -11.8] |

FAIL runs: {'pooled': 7, 'meter106': 2, 'lookup': 7, 'nc': 14, 'evsched': 4, 'drl_best': 7, 'drl_final': 6}
**final PASS: False** · best PASS: False

