# DRL lab: status (living document)

*Last update 2026-10-02 09:15 · branch `claude/vsl-lab-core` · every run is in `vsl_lab/runs/ledger.csv` · plan: `docs/plans/vsl_drl_run_roadmap_v0.md` · Round 2: `docs/lab/round2_protocol.md` · realism gate: `docs/lab/t2_realism_protocol.md`*

## Bottom line so far (honest)

**No DRL controller has beaten a tuned classical controller yet.** On fresh test seeds, DRL has not even significantly beaten no-control.

**The pattern** is the same on every plant: wherever an actuator has real authority, a simple, tuned, non-learning rule already captures most of the benefit. A ring with 1 AV is the exception, but there PI-with-saturation already reaches the ceiling.

**What remains open:**
- B: 25 % AVs on the bottleneck (more authority for the AV actuator);
- the merge plant with posted VSL against tuned MTFC, the thesis core. It now has a realistic insertion fix (v3) and is gated by a plant-realism check.

## Where we are

| Track | Plant | State | Key numbers |
|---|---|---|---|
| T1 | BN4: Vinitsky/Flow zipper 4 → 2 → 1, IDM, 10 % AVs | **Done for 10 % AVs: DRL ≈ NC** | <ul><li>Capacity drop PASS (1,044 → 900 veh/h); determinism PASS.</li><li>Tuned door-to-door (4 cells): NC 412 s · constant AV cap ≈ NC · AV feedback worse · **infrastructure meter 225 s (−45 %)**.</li><li>P1c passed screening.</li><li>F1 (3 seeds × 1,000 updates) and F2 (4× batch, learning-rate decay) on test seeds: **DRL ≈ NC** (e.g. F2 at q = 2,000: −1.7 s [−4.1, 0.0]). The screening pass was a false positive.</li><li>Limit: the actuator's authority.</li></ul> |
| T1-A | BN4 + posted VSL (all vehicles) | **Stopped** | <ul><li>A-T0 FAIL: posted VSL does not bind (outflow −0.8 % / +3.5 %, CIs include 0).</li><li>A-R2: every VSL / MTFC setting scores 427–430 s vs NC 430 s; meter 270 s.</li><li>A-P5 not run (`round2_protocol.md`, A-track stop).</li></ul> |
| T1-B | BN4 + 25 % AVs | **B-R2 done**; B-P6 (DRL pilot, F2 configuration) queued after the realism gate | <ul><li>Tuned door-to-door (4 cells): meter 226 s · best constant AV cap (`cap:18`) 408 s · NC 414 s · AV feedback 624 s.</li><li>0 FAIL in 1,360 runs.</li><li>**Even at 25 % AVs, no classical AV-actuator controller beats NC by more than about 1.5 %.**</li></ul> |
| T1-C | DRL scheduling the tuned meter | **Killed by the hybrid gate** | G = 4.1 % < 10 % (biased upwards) |
| T3 | RING22 (Stern / Flow), 1 AV | **Done: H ≈ 0** | <ul><li>PI-with-saturation reaches 100.2 % of v_e.</li><li>All DRL ring pilots collapse to U = 10 (lag / needle problem).</li></ul> |
| T2 | MRG3 merge, posted VSL vs tuned MTFC (thesis core) | <ul><li>v1 (Krauss): no capacity drop, R1 FAIL.</li><li>v2 (IDM): insertion failure (D-1).</li><li>**v3 (IDM + `departSpeed="avg"`)**: calibration → R1 → D-check queued (`run_v3.sh`).</li><li>**Realism gate** (5 driver variants) queued after it.</li><li>v3 R2 runs only if H0 passes the gate.</li></ul> | v3 insertion test: 0 pending vehicles at 1,500 s (vs 440 with `max`) |

## Queue (one batch at a time, thermal guard on)

1. `run_round2.sh`: B-R2 done → D-1 duplicate diagnosis (1 run; its output must reproduce the committed JSON).
2. `run_v3.sh`: MRG3-v3 calibration → R1 (T1, T1c, T0, T3) → D-check → R2. R2 now skips unless H0 passed the realism gate.
3. `run_realism_p6.sh`:
   - the realism gate (700 calibration runs + up to 205 check runs);
   - validation references at 25 % AVs, then B-P6 (PPO, 600 updates) with its screening report;
   - MRG3-v3 R2, if H0 passed.

## Plant-realism gate (new, pre-registered 2026-10-02)

**Why:** the author's observation that SUMO makes waves "from nowhere" at high demand and that its drivers act like idealised ADAS.

**Variants on MRG3-v3:**
- H0 IDM;
- H1 IDM with a 1 s action step;
- H2 IDM + `driverstate` perception errors;
- H3 W99;
- H4 EIDM with estimation and driving errors.

**Checks, against literature signatures:**
- **R-a** capacity drop, with a mean-based ratio in [0.82, 0.97];
- **R-b** internal wave speed in [−25, −10] km/h, by cross-correlating 10-s probe speeds;
- **R-c** no teleports or health FAILs, discharge 1,600–2,400 veh/h/lane, deterministic;
- **R-d** congestion must start at the bottleneck (≥ 80 %), not at the entry or on the open road.

Plus **R-0**: a variant that changes nothing is flagged INERT, because SUMO silently ignores unknown attributes.

## Silent failures caught so far (each fixed, re-run, and logged)

1. **Bottleneck "light" node.** netconvert's default signal program metered every "no-control" run. Fixed with a forced all-green program and the H-R7 assertion.
2. **Runner load counter** stuck at 0 (vehicles are loaded inside `start()`). Caught by H-S2.
3. **Conservation check off by one** (448 false FAILs). End-of-run conservation held in all runs.
4. **Emergency braking from abrupt AV caps.** Now rate-limited to −1.5 / +1.0 m/s².
5. **AV actuator silently disabled.** SUMO renames the vType to `av@<id>` after `setMaxSpeed`, so every cap baseline equalled NC to the decimal. AVs are now identified by ID, with an assertion.
6. **AV spec mismatch.** AVs had SUMO's default `speedDev` 0.1 (spec: speedFactor 1).
7. **Ring AV collisions** under direct DRL control. Fixed with a safety shield; baselines verified unchanged.
8. **Ring start-position clamp** (21 instead of 22 cars).
9. **IDM insertion failure** at `departSpeed="max"`: the origin queue reached 1,955 vehicles, and it looked like a "deadlock". Fixed with `avg` (MRG3-v3).
10. **SUMO silently accepts unknown vType attributes.** A typo runs as the base model. Hence the behavioural R-0 check.
11. **Quiet stderr hid worker tracebacks.** stderr now goes to per-process files, and jobs print an exception JSON.
12. **Discrete action spaces** crashed the BN4 evaluator (`shape == ()`).
13. **Thermal (the platform).**
    - Workers are pinned to the E-cores.
    - The guard has two timescales: a 10-min mean (pause at 90 °C, resume below 87 °C) and a 10-s cap at 93 °C.
    - Exceedances are logged, including spikes with no lab jobs running.
