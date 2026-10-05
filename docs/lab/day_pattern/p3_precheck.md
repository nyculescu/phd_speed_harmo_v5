# Day-pattern P3 pre-check: SUMO single-lane queue discharge, results

*2026-10-05 · protocol `p3_precheck_protocol.md` (commit `99c173a`, 07:55:07, before any run; Addenda A `a978de7` and B `978874c`, both before the check) · summary `p3_precheck.json` · raw `/home/catalin/work/phd/vsl_lab_runs/dp/p3_precheck_check_1791212259` · 88 runs (80 check + 8 determinism), seeds 7,190,001–010, 0 process errors, wall 5.5 s*

## Outcome: **P3-ALIVE**

One candidate, **K2 (IDM at SUMO defaults), passes at both steps.** SUMO stays the confirmation plant. The merge-realism work comes next and needs its own pre-registration.

| Candidate | Step | Median Q at 200 m (veh/h/lane) | Range over 10 seeds | Q at 600 m | Teleports / collisions | Determinism | Verdict |
|---|---|---|---|---|---|---|---|
| K0 Krauss defaults | 0.5 s | 2,535 | 2,509–2,562 | 2,540 | 0 / 0 | yes | FAIL (> 2,400) |
| K0 | 0.2 s | 2,649 | 2,632–2,679 | 2,663 | 0 / 0 | yes | FAIL (> 2,400) |
| K1 EIDM defaults | 0.5 s | 2,428 | 2,293–2,449 | 2,412 | 0 / 0 | yes | FAIL (> 2,400, by 28) |
| K1 | 0.2 s | 2,413 | 2,296–2,436 | 2,394 | 0 / 0 | yes | FAIL (> 2,400, by 13) |
| **K2 IDM defaults** | 0.5 s | **2,323** | 2,308–2,345 | 2,286 | 0 / 0 | yes | **PASS** |
| **K2** | 0.2 s | **2,335** | 2,320–2,356 | 2,293 | 0 / 0 | yes | **PASS** |
| K3 EIDM population mix (cars) | 0.5 s | 2,408 | 2,264–2,526 | 2,380 | 0 / 0 | yes | FAIL (> 2,400, by 8) |
| K3 | 0.2 s | 2,403 | 2,273–2,553 | 2,395 | 0 / 0 | yes | FAIL (> 2,400, by 3) |

- The start-up time of the first vehicle to the 200 m loop is 13–15 s for every candidate.
- The queue-formation assert held in every run.

## Reading

- **The prior was wrong in direction.** I expected K0 to pass and feared values below 1,600. Every candidate discharges a plain-lane standing queue at **2,300–2,650 veh/h/lane**: at or *above* the upper end of the realism band.
- **SUMO's car-following is therefore not what limited the v5 plants** (900–1,528 veh/h/lane at merges, zippers and lane drops).
  - This supports the hypothesis in `day_pattern_plants_v0.md` that merge and junction behaviour (lane changing, zipper and junction logic) caused those failures.
  - **[Inference]** It is not proven, because this test has no merge.
- **The fails of K1 and K3 are marginal** (3–28 veh/h above 2,400) and are recorded as fails, as pre-registered. Only K0 is clearly too fast.
- **What this means for the SUMO corridor build:**
  - the car-following candidates are K2, with K1 and K3 as near misses;
  - the work goes into the merge (lane-change parameters, acceleration-lane geometry, junction type), checked against the full realism gate R-a…R-d.

## Disclosures

- **Two setup defects were found in the smoke** (throw-away seed 7,190,000) and fixed before the check (Addenda A and B):
  1. insertion backlog at 3,000 veh/h;
  2. a head-vehicle teleport at a 600 s red with `--time-to-teleport 300`.
- **Smoke values** (not used for any criterion) were: K0 2,483, K1 2,392, K2 2,315, K3 2,384 veh/h/lane at 0.5 s.
- **Resolution:** headways are quantised to the step. The ±1 step error on a 100-headway window is about ±0.5 s over about 150 s, i.e. about ±0.3 %.
- **Scope:** discharge from a standing queue on one lane, released by a light. A freeway bottleneck queue discharges after a merge or lane drop, which this test deliberately leaves out.
