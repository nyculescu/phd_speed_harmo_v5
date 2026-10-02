# Track 2 (MRG3 merge, TM20 posted VSL), phase R1 plant checks: protocol

*Committed before any MRG3 simulation. 2026-10-01 · roadmap §6 (Track 2) · code `vsl_lab/{netgen,plants}/mrg3.py`, `vsl_lab/controllers/mtfc.py`, `vsl_lab/jobs/mrg3_run.py` (commit d622739)*

## Plant (frozen for R1)

**Network.** MRG3 spec v1 (cache `mrg3_59dd5c699d`):
- 3-lane mainline at 33.33 m/s;
- VSL application area `up1` + `up0a` (1.5 km);
- acceleration area `up0b` (465.6 m after the junction);
- merge edge 277 m: 4 lanes, where lane 0 is the acceleration lane and ends;
- downstream 3 lanes, 1 km;
- 1-lane on-ramp, 263.8 m, at 25 m/s.

**Simulator and vehicles.**
- Step 0.5 s, `--time-to-teleport 300`.
- Cars use SUMO defaults (Krauss σ 0.5, τ 1 s, LC2013). Trucks are 10 %: length 12, accel 1.3, maxSpeed 25 m/s.
- Compliance: a non-compliant share p_nc = 0.3 drives at speedFactor ~ normc(1.15, 0.05). Compliant drivers use normc(1.0, 0.05).

**Demand.**
- Mainline base 2,500 veh/h; on-ramp base 300 veh/h.
- Linear rise over [600, 1,200) s, peak until 3,000 s, linear fall over 600 s, end at 3,900 s, then an uncontrolled drain.
- Peaks are set by calibration (below).

**Control.** Starts at t = 300 s, period 60 s. The VSL rate b applies to `up1` and `up0a`; `up2` gets b + 0.2 and `up3` gets b + 0.4 (the safety staircase); `up0b` gets 0.9 while active.

**Primary metric.** Mean door-to-door time per vehicle, including the origin queue. Reported for mainline and on-ramp users separately.

## Calibration (throw-away seeds 7,120,000–7,120,009; disclosed in the report)

- **Runs:** NC at main_peak ∈ {4,800, 5,100, 5,400, 5,700, 6,000} × ramp_peak ∈ {600, 900} × 10 seeds = 100 runs.
- **Recorded per cell:** breakdown share, capacity-drop ratio (5-min discharge / pre-breakdown 5-min max at the exit loops), teleports and health.
- **Fixed cell-selection rule:**
  1. Among cells with 0 teleports and 0 health FAIL, take the cell whose NC breakdown share is closest to 0.5.
  2. Ties go to the lower total demand.
  3. If no cell has a breakdown share between 0.2 and 0.9, the R1 checks run at the two cells nearest to 0.5, and this is reported.

## Checks (seeds 7,120,010–7,120,049; at the selected cell)

### T1: capacity drop exists (mechanism)

- **Runs:** NC, seeds 7,120,010–7,120,039 (30 runs).
- **PASS** if all hold:
  1. breakdown in ≥ 30 % of the seeds;
  2. among breakdown seeds, the capacity-drop ratio is ≤ 0.95 in ≥ 2/3;
  3. 0 teleports and 0 health FAIL.
- **If it FAILs**, mainstream VSL has no capacity-drop mechanism in this plant, and Track 2's mainstream-metering hypothesis is killed for MRG3 (roadmap §12).

### T1c: control matters (exploratory but pre-registered)

- **Runs:** seeds 7,120,010–7,120,039, controllers:
  - const:0.6 and const:0.8;
  - MTFC (ρ̂, K′P, K′I, K_I) ∈ {(32, 38, 9, 0.0015) paper, (25, 38, 9, 0.0015), (20, 38, 9, 0.0015)}.
- **PASS** if any of them reduces the median door-to-door time against NC by ≥ 5 % (median of paired differences, 95 % bootstrap CI excluding 0).

### T0: the actuator binds

- **Runs:** seeds 7,120,040–7,120,049; const:0.4 vs NC (b = 1.0).
- **Measure:** application-area outflow `up0a` (per lane, 30-s loops), averaged over [1,500, 2,700) s, at peak demand.
- **PASS** if the median of paired differences is ≤ −10 % of NC with the CI excluding 0.

### T3: determinism

- **Runs:** 5 runs drawn at random (`random.Random(7120099)`) from the T1 runs, re-run in fresh processes.
- **PASS** if the hashes are identical.

## Decision

| Outcome | Next step |
|---|---|
| T1 and T0 PASS | R2 tunes MTFC and constant VSL on the tuning seeds 7,120,100–7,120,299. |
| T1 FAIL | Report the measured capacity-drop status of this SUMO merge. Do not build DRL for mainstream VSL here. The re-scoped options are a moving-jam corridor (Track 4) or a hidden-compliance niche, which needs a new pre-registration. |
