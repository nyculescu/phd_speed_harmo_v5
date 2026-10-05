# Day-pattern track, P3 pre-check: SUMO single-lane queue-discharge test (pre-registration)

*Committed 2026-10-05 before any run of this check. Branch `claude/vsl-lab-core`. Decision context: the gate plant is P6b (METANET gate, SUMO confirmation; author, 2026-10-05; `docs/plans/day_pattern_gate_draft_v0.md`).*

## Question

Can SUMO 1.27's car-following alone discharge a standing queue at a realistic freeway rate, ≥ 1,600 veh/h/lane, with candidate freeway vTypes?

**Why ask it:**
- Five v5 freeway plants failed the realism discharge floor (900–1,528 veh/h/lane).
- The v6 signalised plant passed with Krauss (1,854).
- **Hypothesis [Inference, `day_pattern_plants_v0.md`]:** the v5 failures come from the merge and junction (lane-change and zipper) behaviour, not from car-following.

This test removes merging entirely. It is a pre-check, not the realism gate.

**What each outcome means:**
- If **no** candidate passes, SUMO cannot serve as the confirmation plant, and the fallback in the draft gate §1 applies.
- If **some** candidate passes, a SUMO corridor is worth building later. It must then pass the full realism gate (R-a…R-d) with merges.

## Plant

- **Road:** a single-lane straight road, speed limit 29 m/s (≈ 105 km/h, the order of MnDOT freeway limits).
  - edge `up`: 2,000 m, ending at node `stop` (a traffic light);
  - edge `down`: 1,000 m.
- **Lane changing:** none possible (one lane).
- **Simulation:** `--time-to-teleport 300`; collisions counted (`--collision.action warn`).

**Queue formation:**
- 150 vehicles are inserted at x = 0 at a constant 3,000 veh/h (one every 1.2 s, snapped to the step; `departSpeed="max"`) over t ∈ [0, 180) s.
- The light is red until **t = 300 s** and green afterwards (set with TraCI). Every vehicle has stopped in the queue before release.
- **Assert:** at t = 299 s, the 150 vehicles are on `up` with speed < 0.1 m/s. Otherwise the run is FAIL (H-Q) and not used.

**Measurement:**
- The crossing time of each vehicle at an E1 loop **200 m downstream** of the stop line.
- First-seen time of each vehicle id on the loop, per step. The 0.5-s step quantises headways; this is disclosed.
- Vehicles are ranked by passage order.
- **Discharge Q** = 100 × 3,600 / (t₁₂₁ − t₂₁) veh/h, i.e. 100 headways from vehicle 21 to vehicle 121. This skips the start-up transient, as signal saturation-flow practice does.
- **Reported, not gated:** the same quantity at a loop 600 m downstream; the start-up time of vehicle 1; the mean speed at the 200 m loop.

## Candidates (vTypes, no lane changing needed)

| ID | Model | Parameters |
|---|---|---|
| K0 | Krauss | **SUMO defaults** (no attribute set) |
| K1 | EIDM | **SUMO defaults** (as B2 in S1) |
| K2 | IDM | SUMO defaults (no attribute set) |
| K3 | EIDM population mix | the S1 B3 car classes (timid / normal / assertive, compliance groups, per-vehicle U(0.85, 1.15) jitter), **cars only** (truck share 0), drawn per vehicle from a `vTypeDistribution` |

**Steps:** 0.5 s (primary) and 0.2 s (reported; a candidate passes if it passes at 0.5 s *or* 0.2 s, and the step that passes is named).

## Seeds and runs

From the approved block 7,190,000–7,190,999, plant-check role:
- **7,190,000:** smoke (one run per candidate at 0.5 s, throw-away; checks that the queue forms and the loops read);
- **7,190,001–010:** the check (10 seeds).

**Runs:** 4 candidates × 2 steps × 10 seeds = 80, plus 4 smoke runs. Each run is short (about 600 s simulated).

## Criteria (per candidate and step)

**PASS** if all hold:
1. the **median Q over the 10 seeds is in [1,600, 2,400] veh/h/lane**;
2. 0 teleports and 0 collisions in all 10 runs;
3. a determinism re-run (seed 7,190,001) is hash-identical.

**Outcome:**
- **P3-ALIVE** if at least one candidate passes. SUMO stays the confirmation plant, and the merge-realism work is next, in a separate pre-registration.
- **P3-OUT** if none passes.

**Prior (written before any run):**
- K0 is likely to pass. Krauss at default settings reached 1,854 veh/h/lane at v6 signals; that was a different geometry, but also a discharge from standstill.
- K1 reached 1,440 at the BN4 zipper. A plain lane may be higher.
- K2 is uncertain, because IDM is deterministic and its default accel is 2.6.

## Compute

- Resource check before the batch.
- The batch scheduler with the compute guard (CPU > 90 % for 2 min → pause; v6 thermal hysteresis; CLAUDE.md "Limits", `vsl_lab/ops/guard.py`).
- At most 16 workers.

## Outputs

- Raw runs: `/home/catalin/work/phd/vsl_lab_runs/dp/p3_precheck_*`.
- Summary: `docs/lab/day_pattern/p3_precheck.json` and `p3_precheck.md`.
- One ledger row.

## Addendum A (2026-10-05, after the smoke, before any check run)

**Smoke result.** Throw-away seed 7,190,000, raw `/home/catalin/work/phd/vsl_lab_runs/dp/p3_precheck_smoke_1791212172`; not used for any criterion.
- **The queue-formation assert failed for all 4 candidates.**
- **Cause:** at 3,000 veh/h with `departSpeed="max"`, SUMO cannot insert at a safe gap. Insertions backed up: the last vehicle (v149) was inserted at about t = 280 s and was still at 27 m/s on `up` at t = 299 s.
- **Also measured:** a stopped queue takes about 10 m per vehicle with Krauss defaults (1,517 m for 150 vehicles), more than the 7.5 m I assumed.
- The smoke discharge values (2,315–2,483 veh/h) came from incomplete queues, so they are invalid.

**Fix (setup only; criteria unchanged):**
- insertion rate **1,200 veh/h** (one vehicle every 3.0 s, over [0, 450) s);
- red until **t = 700 s** (the queue-formation assert is checked at t = 699 s);
- upstream edge `up` lengthened to **3,000 m** (stop line at x = 3,000; `down` still 1,000 m with loops at 200 and 600 m);
- simulation horizon 2,000 s.

The smoke is re-run once on 7,190,000 with the fix, to confirm that the queue forms, before the check.
