# T1-M meter headroom scan: results

*2026-10-03 07:07 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/meter_gscan_1791035772`*

**Candidate DRL targets (G ≥ 10 %): ['q1600_all', 'q2000_all']**

| family | G | pooled best | per-condition best | J pooled (s) | J lookup (s) |
|---|---|---|---|---|---|
| q1600_slow | 3.8% | meter:40:8 | {'none': 'meter:40:6', 'slow': 'meter:40:8'} | 199.4 | 191.9 |
| q1600_block | 5.8% | meter:10:8 | {'none': 'meter:40:6', 'block': 'meter:20:12'} | 180.7 | 170.2 |
| q1600_surge | 4.8% | meter:40:6 | {'none': 'meter:40:6', 'surge': 'meter:5:8'} | 161.4 | 153.6 |
| q1600_all | 15.4% | meter:40:8 | {'none': 'meter:40:6', 'slow': 'meter:40:8', 'block': 'meter:20:12', 'surge': 'meter:5:8'} | 229.2 | 193.9 |
| q2000_slow | 8.8% | meter:40:6 | {'none': 'meter:40:6', 'slow': 'meter:40:8'} | 361.6 | 329.8 |
| q2000_block | 4.3% | meter:5:8 | {'none': 'meter:40:6', 'block': 'meter:20:10'} | 322.7 | 309.0 |
| q2000_surge | 1.8% | meter:40:6 | {'none': 'meter:40:6', 'surge': 'meter:5:10'} | 306.9 | 301.4 |
| q2000_all | 10.3% | meter:5:8 | {'none': 'meter:40:6', 'slow': 'meter:40:8', 'block': 'meter:20:10', 'surge': 'meter:5:10'} | 384.6 | 345.0 |

Teleport runs per condition: {'q1600_none': 0, 'q1600_slow': 0, 'q1600_block': 21, 'q1600_surge': 1, 'q2000_none': 0, 'q2000_slow': 2, 'q2000_block': 9, 'q2000_surge': 0}
FAIL runs per condition: {'q1600_none': 0, 'q1600_slow': 0, 'q1600_block': 21, 'q1600_surge': 1, 'q2000_none': 0, 'q2000_slow': 2, 'q2000_block': 9, 'q2000_surge': 0}

Median door-to-door (s) per condition: nc / best meter:

- q=1600 none: nc 319.8 · best meter:40:6 127.9 · meter:10:6 142.9
- q=1600 slow: nc 326.1 · best meter:40:8 255.9 · meter:10:6 390.8
- q=1600 block: nc 260.4 · best meter:20:12 212.4 · meter:10:6 286.1
- q=1600 surge: nc 396.1 · best meter:5:8 179.3 · meter:10:6 196.9
- q=2000 none: nc 589.8 · best meter:40:6 250.2 · meter:10:6 305.1
- q=2000 slow: nc 594.2 · best meter:40:8 409.4 · meter:10:6 593.4
- q=2000 block: nc 507.4 · best meter:20:10 367.7 · meter:10:6 459.5
- q=2000 surge: nc 663.6 · best meter:5:10 352.6 · meter:10:6 400.9
