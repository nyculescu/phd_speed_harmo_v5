# Round 4 DRL pilots: screening (exploratory)

## P-H screening (2026-10-03 02:42) · run `/home/catalin/work/phd/vsl_lab_runs/t2/train/ph2_ld3/mrg3_ppo_tts_u500_e16_s0_1790971963_pid1486409`

| controller | J (mean, s) | delay (s) | stops/veh | n | FAIL |
|---|---|---|---|---|---|
| const:0.75 | 310.1 | 261.9 | 1.21 | 6 | 0 |
| mtfc:36:38:9:0.0015 | 322.3 | 273.8 | 1.21 | 6 | 0 |
| vslad:90:0.8 | 332.5 | 272.1 | 1.51 | 6 | 0 |
| rl_final | 342.7 | 279.0 | 1.59 | 6 | 0 |
| nc | 359.4 | 287.2 | 1.80 | 6 | 0 |
| rl_best | 361.7 | 287.4 | 1.86 | 6 | 0 |
| spec | 394.2 | 306.6 | 2.19 | 6 | 0 |

Criteria vs tuned classical `const:0.75`: {"rl_final": {"C_H1": false, "C_H2": false, "C_H3": true, "PASS": false}, "rl_best": {"C_H1": false, "C_H2": false, "C_H3": true, "PASS": false}}

