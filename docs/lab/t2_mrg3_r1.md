# Track 2 (MRG3), R1 plant checks: results

*2026-10-02 03:02 · protocol `docs/lab/t2_mrg3_r1_protocol.md` · cell 6000/900 · raw `/home/catalin/work/phd/vsl_lab_runs/t2/r1_1790935037`*

## T1 capacity drop: **FAIL**

- {"n": 30, "breakdown_share": 0.0, "median_ratio": null, "share_ratio_le_095": null, "teleports": 0, "fail": 0, "PASS": false}

## T1c control matters: **FAIL**

| controller | rel. Δ door-to-door vs NC | 95 % CI (s) | ramp users Δ (s) | median min b |
|---|---|---|---|---|
| const:0.6 | +14.4% | [+23.2, +31.0] | +0.6 | 0.6 |
| const:0.8 | +3.4% | [+4.5, +9.2] | +0.4 | 0.8 |
| mtfc:32:38:9:0.0015 | +5.3% | [+3.6, +18.4] | -0.1 | 0.4000000000000001 |
| mtfc:25:38:9:0.0015 | +36.4% | [+56.4, +82.9] | -1.5 | 0.2 |
| mtfc:20:38:9:0.0015 | +87.3% | [+155.9, +178.6] | -4.5 | 0.2 |

## T0 actuator binds: **FAIL** (application-area outflow -3.9% at b = 0.4)

## T3 determinism: **PASS**
