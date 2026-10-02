# Track 1 (BN4), R2 tuned baselines: results (frozen)

*2026-10-01 22:56 · protocol `docs/lab/t1_bn4_r2_baselines_protocol.md` · 2160 runs · health {'PASS': 641, 'WARN': 1519, 'FAIL': 0} · raw `/home/catalin/work/phd/vsl_lab_runs/t1/r2_1790919086`*

Primary: median over 20 tuning seeds of the mean time in system per vehicle (s, door-to-door incl. queue). Score = mean over the 4 cells.

| controller | q=1200 | q=1600 | q=2000 | q=2400 | score | outflow q=2000 (veh/h) |
|---|---|---|---|---|---|---|
| meter:10:6 | 78.8 | 149.2 | 282.8 | 398.6 | 227.3 | 1440 |
| meter:40:6 | 69.8 | 171.4 | 285.6 | 422.1 | 237.2 | 1332 |
| meter:10:8 | 73.8 | 118.3 | 302.1 | 485.3 | 244.9 | 1410 |
| meter:20:6 | 73.5 | 116.7 | 337.4 | 543.9 | 267.9 | 1372 |
| meter:40:8 | 65.3 | 185.4 | 326.2 | 516.8 | 273.4 | 1236 |
| meter:10:10 | 71.3 | 142.9 | 381.2 | 558.9 | 288.6 | 1146 |
| meter:10:4 | 82.3 | 191.7 | 338.6 | 571.0 | 295.9 | 1234 |
| meter:20:8 | 68.4 | 137.7 | 385.5 | 599.3 | 297.7 | 1126 |
| meter:20:4 | 84.4 | 185.8 | 393.0 | 594.9 | 314.5 | 1174 |
| meter:20:10 | 66.3 | 230.2 | 386.3 | 579.5 | 315.6 | 1148 |
| meter:40:10 | 64.1 | 226.4 | 409.6 | 599.0 | 324.8 | 1178 |
| meter:40:12 | 63.2 | 208.7 | 399.6 | 632.9 | 326.1 | 1130 |
| meter:20:12 | 65.0 | 221.9 | 415.7 | 609.6 | 328.0 | 1144 |
| meter:10:12 | 69.1 | 207.1 | 431.2 | 614.8 | 330.6 | 1116 |
| meter:40:4 | 88.4 | 208.9 | 449.2 | 597.8 | 336.1 | 1100 |
| meter:20:14 | 64.0 | 240.2 | 435.6 | 633.3 | 343.3 | 1154 |
| meter:10:14 | 66.7 | 227.0 | 445.5 | 649.4 | 347.1 | 1040 |
| meter:40:14 | 62.8 | 253.9 | 462.3 | 682.4 | 365.3 | 1114 |
| nc | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:3 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:5 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:7 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:9 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:11 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:13 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:15 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |
| cap:18 | 57.5 | 308.2 | 536.0 | 755.0 | 414.2 | 954 |

## Tuned (frozen)

- **nc**: `nc` (score 414.2 s)
- **cap**: `cap:3` (score 414.2 s)
- **meter**: `meter:10:6` (score 227.3 s)

- Per-cell best (informed reference for a later hybrid gate): {1200: 'nc', 1600: 'meter:20:6', 2000: 'meter:10:6', 2400: 'meter:10:6'}

## Tuned vs NC (paired, median of paired differences in mean time in system, s; negative = better)

- cap @ q=1200: +0.0 s [+0.0, +0.0]
- cap @ q=1600: +0.0 s [+0.0, +0.0]
- cap @ q=2000: +0.0 s [+0.0, +0.0]
- cap @ q=2400: +0.0 s [+0.0, +0.0]
- meter @ q=1200: +19.0 s [+11.6, +20.7]
- meter @ q=1600: -163.2 s [-203.3, -53.8]
- meter @ q=2000: -296.1 s [-309.2, -243.5]
- meter @ q=2400: -351.7 s [-365.5, -300.6]

---

**INVALID for the cap family (2026-10-01 23:00).** Every constant cap is byte-identical to NC because of BUG 1:
- SUMO renames a vehicle's type to `av@<vid>` after `setMaxSpeed`;
- the env identified AVs with `getTypeID == "av"`;
- so AVs were capped once, mildly, and never again.

BUG 2 affects all BN4 runs so far: AVs had SUMO's default `speedDev` 0.1, while the protocol says speedFactor 1.

Both are fixed, with a new actuator assertion H-R7. R1, T0b and R2 are re-run in full, and the corrected tables replace this file. This version is kept in git history and in the ledger.
