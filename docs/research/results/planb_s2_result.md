# Plan B S1 and S2 result

Status: S1 passed. S2 as registered read KILL. Under the replacement drain test written after that result was known (V486), TRUCK continues and SURGE drops. Rows: `v5b1_runs/planb_remote/s2/`; registered read `s2.json`, repaired read `s2_v486.json` (read once at bf3eebc). Recomputed independently from the raw rows: 583 values, 0 differences.

| Gate (95 % CI) | SURGE | TRUCK |
|---|---|---|
| G1a delay above S, no control | +26.5 % [20.7, 29.2] | +17.2 % [14.0, 23.0] |
| G1a delay above S, p333 | +32.2 % [25.7, 37.6] | +23.9 % [19.8, 27.7] |
| G1b congestion above S, no control / p333 | +60 % / +97 % | +105 % / +148 % |
| G2 p333 below no control | 30.9 % [25.9, 37.8] | 29.6 % [27.8, 32.2] |
| G2-loss, report-only | +24.9 % [0.2, 47.2], passes | +11.0 % [-8.0, 36.8], fails |
| G4(ii)(c) stuck rows of 80 | 1 (p333, seed 7,480,037) | 0 |
| G4(ii)(a,b) as registered | fails | fails |
| G4(ii)(a,b) V486, largest mean excess, limit 2 vehicles | p333 ramp 2 +3.29 [1.70, 5.21], fails | no control ramp 2 +1.26 [-0.17, 2.77], passes |
| Outcome as registered | drops | drops (KILL) |
| Outcome under V486 | drops | continues |

The placebo fails G1, so the null holds.

## What may be said

- TRUCK bound the plant. It failed G4(ii) as registered, and it continues only under V486. Both verdicts go in every sentence.
- Only the point estimate of TRUCK's largest excess is below 2 vehicles; its interval reaches 2.77.
- TRUCK's window (1,500-1,800 s) lies inside its event (360-1,800 s), so the reading is a small queue excess at the end of the run, not a drain. The excess grows towards the end of the window on no control's ramp 2.
- On p333's ramp 2 in TRUCK the excess is small but not zero (+0.71 [0.13, 1.44]). The registered failure there was not only noise.
- SURGE bound the plant and failed the validity gate G4 on two parts, and it drops under both forms. Its stuck vehicle cannot be attributed to SURGE: the same seed holds 18 vehicles on ramp 2 in S with no perturbation. Its drain failure does not depend on that seed (+3.09 without it).
- TRUCK fails G2-loss, so the resilience reading is expected to fail (§7.3). A continuing study can give at best a level claim.

## Not to be said

"TRUCK passed S2" without the registered failure; "the queue drained"; "the excess is below 2 vehicles" as an established fact; "V486 corrected a bug" (§11 calls it a deviation); "false-fail is below 5 %" (§8.8); SURGE "did not bind"; SURGE "caused a blockage".

## Sensitivity of the limit

TRUCK fails at limit 1 and 1.25 and passes from 1.5 upward. SURGE's drain fails at 2 and 3 and passes from 3.5, but its stuck rule stands either way.
