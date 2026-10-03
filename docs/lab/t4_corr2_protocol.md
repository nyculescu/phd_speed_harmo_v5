# T4 CORR2: corridor calibration, pre-registered 2026-10-03 before any calibration run

**Plant:** CORR2 (`netgen/corr2.py`, `plants/corr2.py`, `jobs/corr_run.py`). Built by a delegated agent; build tests 6/6; smoke on 7,140,000.
- 3-lane mainline, 9.5 km;
- on-ramp R1 at x = 3,000 m and R2 at x = 6,000 m, each with a meter (TLS, passage-terminated green, no red phase);
- off-ramp O1 at x = 4,500 m;
- VSL areas m1 and m4;
- EIDM SUMO-default drivers (H5), 0.2 s step.

**Why this plant.** It targets the mechanism by which coordinated metering pays off without a capacity drop: the queue from merge 2 spills back past the off-ramp, delaying exiting traffic. The smoke run at 4,500 / 600 / 900 showed no such spillback, because merge 1 was the active bottleneck.

**Calibration** (NC, `--stops`; T4 throw-away seeds 7,140,001–7,140,003, approved layout):
- **Grid:** q_main ∈ {4,000, 4,500} × q_r1 ∈ {300, 600} × q_r2 ∈ {1,200, 1,500, 1,800}, i.e. 12 cells, 36 runs.
- **Measures per run:**
  - **off-ramp blocking minutes:** 30-s intervals with the end-of-`m3` speed (the diverge point) < 60 km/h, × 0.5;
  - m4 congestion minutes;
  - door-to-door time by group (including off-ramp users);
  - teleports and health FAIL.
- **Selection:** among cells with 0 teleports and 0 FAIL in all 3 seeds, the lowest-total-demand cell with ≥ 5 blocking minutes in ≥ 2 of 3 seeds.
  - If none qualifies, the cell with the most blocking minutes, flagged.
  - The chosen cell is frozen for the T4 headroom scan, which is pre-registered separately.

## Result and Addendum A (2026-10-03, before the extended grid)

**Calibration result** (`t4_corr2_calibration.json`): **FLAGGED.**
- No cell has ≥ 5 off-ramp blocking minutes in ≥ 2 of 3 seeds. The best case is 6.5 minutes in 1 seed, at 4,500 / 600 / 1,200.
- Higher R2 demand raises door-to-door time (e.g. 271 → 377 s), but the excess queues **on the ramp**: `m4` stays above 60 km/h almost always.
- With EIDM / LC2013, ramp drivers yield instead of forcing a mainline breakdown. This is consistent with the realism-gate findings.

**Extended grid (one pre-registered try):**
- **Cells:** overload merge 2 from the mainline side: q_main ∈ {5,000, 5,500} × q_r1 ∈ {0, 300} × q_r2 ∈ {1,500, 2,000}. That is 8 cells on the same seeds 7,140,001–7,140,003, 24 runs.
- **Rule:** the same selection rule.
- **If still flagged:** T4 is closed, because the off-ramp blocking mechanism does not arise in this SUMO plant.

**Extended-grid result** (`t4_corr2_calibration_ext.json`): selected cell **5,000 / 300 / 2,000** (not flagged).
- Off-ramp blocking minutes: 0.5, 6.0 and 5.5. Teleports 0, FAIL 0.
- The mechanism exists but is modest: about 6 of 65 minutes.

## Addendum B: corridor headroom scan, pre-registered before any scan run

**Conditions** (hidden; q_main / q_r1 / q_r2):

| ID | Demand | Variant |
|---|---|---|
| A | 5,000 / 300 / 2,000 | base |
| B | 5,000 / 300 / 2,500 | high R2 |
| C | 5,500 / 300 / 2,000 | high mainline |
| D | 5,000 / 600 / 2,000 | high R1 |

**Controllers:** `nc` + `alinea:o_set:K_R` at both ramps, with o_set ∈ {8, 10, 12, 14} % and K_R ∈ {40, 70}, i.e. 9 in total.
**Seeds:** T4 plant-check range 7,140,010–7,140,019 (10); 360 runs.
**Score:** J = door-to-door time (all users, including the ramp and origin queues), median over seeds. Stops are reported.

**G** = (J of the pooled best setting − mean of the per-condition best J) / J of the pooled best, over {A, B, C, D}.

**Rule:**
- **G ≥ 10 %:** go to an H step with a non-learning adaptive / coordinated rule and the MPC requirement, pre-registered then.
- **G < 10 %:** T4 is killed for DRL. G is biased upwards, so this is a conservative KILL.
