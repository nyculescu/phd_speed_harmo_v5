# Testbed stage-1b metering authority screen (KILL-only)

*2026-10-11 · prereg `docs/plans/day_pattern_testbed_stage1b_screen.md` v1 + §11 · 12 train-source days · run 20261011-222825 · raw `/home/catalin/work/phd/vsl_lab_runs/day_pattern/testbed_screen/run_20261011-222825`*

**Outcome: KILL (T0: no metering lever at either head).** Pre-registered rule §5: both heads fail T0 -> KILL. The run was stopped by the author after the checks (during the CONST batch); the informed arms did not run (report-only; they cannot change a T0 KILL).

| head | days with lower 15-19 h head inflow AND |ΔJ| > 1 % (all head meters at 240 veh/h) | needed | T0 |
|---|---|---|---|
| B1 (E1-E6, E9, E12, E13) | 1/12 | 3 | FAIL |
| B2 (E14) | 2/12 | 3 | FAIL |

Median ΔJ/J_NC at 240 veh/h: B1 meters +27.89%, B2 meter +4.61%.
T3 (determinism, incl. metered arms in mixed batches): PASS.
T1 NC over-critical minutes (05-23 h), B1 cell 26: [126, 144, 191, 165, 225, 178, 26, 112, 91, 200, 46, 242]; B2 cells 32-33: [70, 10, 62, 112, 146, 149, 45, 142, 113, 78, 86, 91].

Reading: with 10-23 vehicles of ramp storage and the 240-s wait limit, the common queue layer releases held vehicles almost at once, so metering at these ramps cannot move the bottleneck inflow on this plant (consistent with the storage disclosure of §3).
