# R3 pilots: results

Protocol: `docs/lab/r3_pilots_protocol.md`. Exploratory; nothing here is a claim.

## p1_bn4 (t1) · 2026-10-01 23:40

References on the same validation seeds (mean_val_outflow): no control 992.0, best constant 1054.0, tuned classical 1343.3333333333333.

![p1_bn4](figs/p1_bn4.png)

| seed | updates | initial | final | best val (update) | C1 val | C1 reward | C3 ≥ NC+5% | C2 > const | beats tuned classical | health FAIL | screening |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 150 | 960.6666666666666 | 976.0 | 1026.0 (125) | True | True | False | False | False | 0 | **FAIL** |
