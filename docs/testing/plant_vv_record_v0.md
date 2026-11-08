# Plant V&V record v0: r2m3 with plant_c3 (DRAFT, 2026-11-07)

Target fixed by V459: r2m3 with `docs/research/baseline_v3/plant_c3.json`, the plant of rounds 1 and 2. Standard (V456): verified and validated for its intended use, never "proven". Status: draft requirements list mapped to evidence and gaps; not yet reviewed or approved.

Structure follows the usual systems-engineering pattern: intended use, requirements, a verification method per requirement (I inspection, A analysis, D demonstration, T test), evidence, traceability, stated limits. Background sources to read before citing: IEEE 1012 (V&V), Sargent's validation framework for simulation models, FHWA Traffic Analysis Toolbox vol. III for microsimulation [VERIFY all three].

## 1. Intended use

**Use:** compare controllers that set the time headway of automated cars (ALKS; 1.6, 1.2, 1.0 or 0.8 s) against rule-based controllers and no control, on paired differences in door-to-door delay (with insertion queues), served flow, close-following (TTC below 3 s), braking at step resolution and severe events, on a synthetic three-lane freeway with two on-ramps, 50 % ALKS, demand 4,090-6,000 veh/h, steady or with tapered slowdowns (X1, X2).

**Not for:** absolute travel times or capacities of a real road; effects on a calibrated or field site (V245); lateral or merge-conflict safety; V2V with latency or loss; human adaptation to automated cars.

**Acceptance:** the plant is valid for this use when every requirement below is met, or its gap is stated as a limit that every claim sentence carries.

**Wording (V462):** "verified and validated" appears in no title, abstract or claim sentence until this record is reviewed and PR-15, PR-24 and PR-28 are closed. Every other partial or gap becomes a numbered limit (L1-Ln, §4) that each claim sentence cites. Rows outside the intended use (the band and 3E-T's condition T under the random training slowdown draw; history cells H1 and H2) are labelled "outside the plant's stated intended use".

**Tally (2026-11-07):** 6 met, 13 partial, 7 gap, 2 limit of 28.

## 2. Requirements, verification and evidence

Status: **met** (evidence exists and was checked), **partial**, **gap** (work needed), **limit** (stated, not fixed). "Locate" means the evidence probably exists but this record has not yet pointed at it.

### Road, demand and insertion

| ID | Requirement | Method | Evidence | Status |
|---|---|---|---|---|
| PR-01 | The network matches its specification: 3 main lanes, two on-ramps 1.2 km apart, 300-m acceleration lanes, 100 km/h limit | I | `baseline_v1/plant_spec.json` (r1m3); r2m3 plant files in `baseline_v2/` | partial: r2m3 inspection to record |
| PR-02 | Inserted demand equals the configured level and ramp share within sampling error, at every level | T | locate | gap |
| PR-03 | Vehicles that cannot enter wait in a counted insertion queue; none are dropped | T, A | baseline v1 door-to-door table counts planned and finished vehicles | partial |

### Drivers and fleet

| ID | Requirement | Method | Evidence | Status |
|---|---|---|---|---|
| PR-04 | Fleet shares as configured (50 % ALKS and 7.5 % trucks by `B_ALKS_SHARE`, `B_TRUCK_SHARE`; the rest to confirm in the plant file) | T | `fleet.py` constants; locate a share test | partial |
| PR-05 | Each human-driver parameter (tau, speed factor, sigma, lengths) is traced to a published source and lies in its range | A, I | `driver_params_hdv_cav_v0.md`, `irish_parameters_v0.md` | partial: parameter-by-parameter table to write |
| PR-06 | ALKS parameters as configured and applied by SUMO (IDM, tau 1.6 s, accel 2.6, decel 4.5, emergency 9.0 m/s², action step 0.5 s) | T | `ALKS_READBACK` in `b_merge`; locate its test | partial |
| PR-07 | ALKS tau and deceleration limits are consistent with UN R157 [VERIFY] | A | to write | gap |
| PR-08 | Lane changing (`lcAssertive` 1.4) gives plausible lane use and few undertakes | D, A | baseline v1 trace of passes on the right (one seed); baseline v2: 14 undertakes per run among about 1,300 ALKS | limit: not validated against real traffic |
| PR-09 | The smooth no-undertaking rule (our model, disclosed) brakes at most 4.4 m/s² and creates no hidden hard braking | T at 0.1 s | V367 found and V376 fixed it; baseline v2 (r1m3 P0d): 1-Hz within 2.2 % of step braking, steady traffic; V451 (plant_c3): check passes on every round-1 test arm under slowdowns | met for round-1 arms; rerun for each new plant |

### Actuator and sensing

| ID | Requirement | Method | Evidence | Status |
|---|---|---|---|---|
| PR-10 | The headway command binds: it changes held gaps, flow and density (T0) | T | V264 (m32 testable at every share); V380 bench: braking limited after `tau_rise` | partial: no r2m3 T0 record |
| PR-11 | Commands reach only ALKS; humans never receive them | T | `COMMANDED = ('alks',)`; locate test in `test_fleet_control.py` | partial |
| PR-12 | Longer gaps grow at most 0.2 s per second (`tau_rise`), so a command cannot force hard braking | T | V380 bench (-5.51 to -1.08 m/s² at 12 m/s); `test_conf3.py` | met |
| PR-13 | Slowdowns X1 and X2 apply as specified (edge, speed, duration, start, taper) | T | `taper_fast`, `fix_x` (V380); V446 checks the taper every 0.1 s for its draw | partial: X1/X2 record to write |
| PR-14 | Controller inputs are normalised and none is dead | T | V387-V389; `test_input_norm.py` | met from revision 4; earlier policies are a limit |
| PR-15 | Inputs carry no information a real vehicle could not have (no seed, event timing or future state) | I | to write | gap |
| PR-16 | V2V is ideal within 150 m | I | `V2V_RANGE` | limit |

### Numerics and reproducibility

| ID | Requirement | Method | Evidence | Status |
|---|---|---|---|---|
| PR-17 | No teleports; collisions rare, counted and reported for every arm | T | baseline v2 (r1m3 P0d, steady, not the V&V target): 0 and 0 in 80 runs; on plant_c3, round 1: no control 1 collision in 40 X1 runs, 0 in X2 (`round_1_result.md`); round reports count collisions and severe events (V452) | partial: no plant_c3 no-control check |
| PR-18 | Same code, plant and seed give identical rows on any machine and worker count (T3) | T | V398 (same-code replay at `d2b2ecc`); V437 and V461 (rows and training fingerprint equal across machines) | met |
| PR-19 | Tracing does not change the run | T | V386 (traced equals untraced) | met; rerun after tracing changes |
| PR-20 | Every result row ties to frozen code, plant file and seed; stored files hashed | I | `SHA256SUMS` in git for baselines v0, v1, v4 (v2, v3 only in the read-only copies); frozen copies; `toolchain/requirements_lock.txt`. Exceptions: 3E-X `meta.json` records no commit (V461); round-2 resume matches rows without a config hash (V455) | partial |

### Measurement

| ID | Requirement | Method | Evidence | Status |
|---|---|---|---|---|
| PR-21 | Door-to-door delay includes origin and insertion queues; unfinished vehicles count to the window end | T on a hand-computed case | V307; locate the unit test | partial |
| PR-22 | Braking is counted every 0.1 s | T | baseline v2; round-2 step metric | met |
| PR-23 | Close-following (TTC below 3 s) is computed as defined | T | `test_conf3.py`; E1 0.1-s meter, 6 tests on synthetic traces (V435) | partial: confirmatory readings use 1 Hz (limit) |
| PR-24 | Every reported counter is traced on a sample before it enters a claim (V283) | D | done for short gaps (V283) and passes on the right | gap: one trace per reported counter |

### Behaviour that makes control meaningful (validation)

| ID | Requirement | Method | Evidence | Status |
|---|---|---|---|---|
| PR-25 | Congestion forms at the merges without teleport or deadlock artefacts, and control changes outcomes beyond seed noise (T1) | T, A | V264 (m32); DRL policies have 18-37 % less delay than no control across scenarios (V405) | partial: no r2m3 T1 record |
| PR-26 | The capacity drop lies in a published range, measured by an estimator with a computed null | A | `capacity_drop_lit_v0.md`; V271 estimator has no null (V244) | gap |
| PR-27 | Per-lane flows and speeds are plausible against field detectors (a comparison, not a calibration) | A | baseline v1 lane table; MnDOT via Mayfly proposed | gap |
| PR-28 | No controller gains through a plant artefact; gains are located by road, period and lane | A | V396: part of the X2 gain sits at merge 2, where lane-end behaviour is not validated; ramp 2 has 608.5 lane-end stops per run against 7 at ramp 1 (baseline v2) | gap |

## 3. Traceability (requirement to claim)

| Claim element (outline §3) | Requirements it rests on |
|---|---|
| Delay against no control and rules | PR-02, PR-03, PR-21, PR-25 |
| Close-following and "safety" words | PR-09, PR-17, PR-22, PR-23, PR-24 |
| Any win against tuned rules | PR-10 to PR-15, PR-18, PR-28 |
| Plant "valid for intended use" | all; limits in §4 |

## 4. Stated limits (carried by every claim)

Uncalibrated SUMO model; synthetic geometry; lane changing and the no-undertaking rule are our model, not validated against real traffic (PR-08, PR-09); ideal V2V (PR-16); TTC at 1 Hz in the confirmatory readings (PR-23); lateral and merge conflicts not measured; capacity drop not settled (PR-26) unless closed.

## 5. Gaps, in proposed order

1. PR-28 artefact location and PR-24 counter traces: they can change a result, so first.
2. PR-26 capacity drop with a null, and PR-27 MnDOT comparison: the two validation items.
3. PR-02, PR-04, PR-06, PR-11, PR-21: locate or write the unit tests (cheap, no simulation for most).
4. PR-01, PR-05, PR-07, PR-10, PR-13, PR-15: inspection and analysis write-ups.
5. Replace the placeholder `docs/testing/test_strategy.md` with the test-to-requirement map.

Items needing runs wait for round 2 to free the CPU.
