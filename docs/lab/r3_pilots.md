# R3 pilots: results

Protocol: `docs/lab/r3_pilots_protocol.md`. Exploratory; nothing here is a claim.

## p1_bn4 (t1) · 2026-10-01 23:40

References on the same validation seeds (mean_val_outflow): no control 992.0, best constant 1054.0, tuned classical 1343.3333333333333.

![p1_bn4](figs/p1_bn4.png)

| seed | updates | initial | final | best val (update) | C1 val | C1 reward | C3 ≥ NC+5% | C2 > const | beats tuned classical | health FAIL | screening |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 150 | 960.6666666666666 | 976.0 | 1026.0 (125) | True | True | False | False | False | 0 | **FAIL** |

## p2_ring_hyb (t3) · 2026-10-01 23:57

References on the same validation seeds (mean_val_speed): no control 3.579283333333333, best constant 3.847716666666667, tuned classical 4.1594500000000005.

![p2_ring_hyb](figs/p2_ring_hyb.png)

| seed | updates | initial | final | best val (update) | C1 val | C1 reward | C3 ≥ NC+5% | C2 > const | beats tuned classical | health FAIL | screening |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 150 | 3.850058112795961 | 3.549239861016535 | 3.549239861016535 (25) | False | True | False | False | False | 0 | **FAIL** |

## p3_ring_dir (t3) · 2026-10-01 23:57

References on the same validation seeds (mean_val_speed): no control 3.579283333333333, best constant 3.847716666666667, tuned classical 4.1594500000000005.

![p3_ring_dir](figs/p3_ring_dir.png)

| seed | updates | initial | final | best val (update) | C1 val | C1 reward | C3 ≥ NC+5% | C2 > const | beats tuned classical | health FAIL | screening |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 13 | 3.8769198255967487 | 3.556864546016508 | None (None) | False | False | False | False | False | 55 | **FAIL** |

## p1b_bn4 (t1) · 2026-10-02 00:12

References on the same validation seeds (mean_val_outflow): no control 992.0, best constant 1054.0, tuned classical 1343.3333333333333.

![p1b_bn4](figs/p1b_bn4.png)

| seed | updates | initial | final | best val (update) | C1 val | C1 reward | C3 ≥ NC+5% | C2 > const | beats tuned classical | health FAIL | screening |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 600 | 960.6666666666666 | 956.0 | 986.0 (525) | False | True | False | False | False | 0 | **FAIL** |

## p1c_bn4 (t1) · 2026-10-02 00:12

References on the same validation seeds (mean_val_outflow): no control 992.0, best constant 1054.0, tuned classical 1343.3333333333333.

![p1c_bn4](figs/p1c_bn4.png)

| seed | updates | initial | final | best val (update) | C1 val | C1 reward | C3 ≥ NC+5% | C2 > const | beats tuned classical | health FAIL | screening |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 600 | 992.0 | 1095.3333333333333 | 1158.6666666666667 (475) | True | True | True | True | False | 0 | **PASS** |
