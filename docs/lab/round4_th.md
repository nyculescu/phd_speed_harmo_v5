# Round 4 T-H (harmonisation on LD3, H5, 0.2 s): results

*2026-10-02 12:20 · protocol `docs/lab/round4_harmonisation_protocol.md` · 660 runs · health {'PASS': 425, 'WARN': 234, 'FAIL': 1} · raw `/home/catalin/work/phd/vsl_lab_runs/t2/round4_th_1790965966`*

**T-H0 (posted VSL has authority over stops): PASS** · SPECIALIST applicable: True

## Cell 3900/0

NC-human median: delay 191.2 s, stops 0.19 per vehicle; NC with 25 % CACC vs NC-human delay: +93.0%; SPECIALIST isolated-jam minutes (median per run): 3.0

| controller (vs its NC) | Δ delay | 95 % CI (s) | Δ stops | 95 % CI (stops/veh) | Δ arrived | harmonises for free |
|---|---|---|---|---|---|---|
| const:0.8 | +2.1% | [+1.7, +5.9] | -63.4% | [-0.15, -0.08] | +0.0% | no |
| const:0.7 | +8.0% | [+13.9, +16.6] | -59.1% | [-0.13, -0.10] | +0.0% | no |
| const:0.6 | +16.9% | [+30.2, +38.6] | -43.0% | [-0.14, -0.05] | +0.0% | no |
| const:0.5 | +30.6% | [+54.1, +88.7] | -37.8% | [-0.14, +0.51] | +0.0% | no |
| mtfc:32:38:9:0.0015 | +1.3% | [+0.1, +4.6] | +0.0% | [-0.02, +0.01] | +0.0% | no |
| cavconst:0.6@cav0.25C | +7.5% | [+17.2, +47.8] | +8.9% | [+0.09, +0.67] | +0.0% | no |
| mtfc:25:38:9:0.0015 | +29.0% | [+41.2, +68.4] | +65.4% | [+0.08, +0.17] | +0.0% | no |
| cavpi@cav0.25P | +180.2% | [+628.3, +700.6] | +111.2% | [+3.79, +4.78] | +0.0% | no |
| mtfc:20:38:9:0.0015 | +63.0% | [+107.7, +133.9] | +267.9% | [+0.31, +0.60] | +0.0% | no |

## Cell 4500/0

NC-human median: delay 392.8 s, stops 4.00 per vehicle; NC with 25 % CACC vs NC-human delay: +45.7%; SPECIALIST isolated-jam minutes (median per run): 10.5

| controller (vs its NC) | Δ delay | 95 % CI (s) | Δ stops | 95 % CI (stops/veh) | Δ arrived | harmonises for free |
|---|---|---|---|---|---|---|
| mtfc:32:38:9:0.0015 | +9.5% | [+15.0, +62.7] | -19.3% | [-1.28, -0.10] | +0.0% | no |
| mtfc:25:38:9:0.0015 | +24.9% | [+45.2, +111.7] | -14.5% | [-1.21, +0.07] | +0.0% | no |
| const:0.8 | -7.6% | [-43.2, +14.0] | -12.7% | [-0.89, +0.19] | +0.0% | no |
| mtfc:20:38:9:0.0015 | +29.0% | [+98.2, +127.3] | -9.4% | [-0.67, +0.07] | +0.0% | no |
| const:0.7 | -3.6% | [-40.0, +9.5] | -1.0% | [-0.86, +0.15] | +0.0% | no |
| cavconst:0.6@cav0.25C | +3.8% | [+11.7, +33.3] | +5.2% | [-0.07, +0.71] | +0.0% | no |
| cavpi@cav0.25P | +118.7% | [+634.2, +765.9] | +15.5% | [+0.69, +1.85] | +0.0% | no |
| const:0.6 | +22.4% | [+44.0, +126.2] | +26.5% | [+0.27, +1.87] | +0.0% | no |
| const:0.5 | +33.9% | [+121.4, +154.0] | +43.6% | [+1.33, +2.44] | +0.0% | no |

