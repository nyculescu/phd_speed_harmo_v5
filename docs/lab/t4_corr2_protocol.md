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
