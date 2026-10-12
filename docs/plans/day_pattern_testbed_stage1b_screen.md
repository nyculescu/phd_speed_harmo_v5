# Testbed stage 1b: metering authority screen (KILL-only), pre-registration

*2026-10-11 · branch `claude/day-pattern-core` · decisions D5.11 (lean path), D5.12 (10 meters) · binding once committed with the author's go; it runs once*

## 1. Question and the only two outcomes

**Question.** On the frozen v5 plant, can ramp metering at the 10 field-metered ramps beat no control (NC) by ≥ 10 % even when the controller knows the day in advance?

- **KILL:** the corridor testbed stops. No stage 2, and no protocol v1.
- **GO:** this only licenses writing protocol v1 (the review's fix list). It is not a claim, and no number from this screen may be quoted as a result.

## 2. Days, plant and stepper
- **Days:** the 12 train-source days of `docs/lab/day_pattern/testbed_day_split.json` (stratified fixed rule, no RNG): 5 heavy at both heads, 7 at B1 only. No validation-source or test-source day is simulated in controlled mode.
- **Plant:** the frozen v5 nominal (`metanet_v5_calibration.json`, `frozen_params`), deterministic (c1 = c2 = 1).
- **Stepper:** `vsl_lab/plants/metanet_ctrl.py` (72e7e1c; reproduces `simulate()` bit for bit on the 22 days in replay).

## 3. Inputs, time window and metric
- **Metered ramps (10):** E1–E6, E9, E12, E13, E14.
	- Demand = the summed Queue-detector arrivals when that ramp-day's Queue data pass the inputs code's validity rule (≥ 9 of 10 samples per 5-min bin, gaps ≤ 15 min interpolated); otherwise the replay inflow.
	- Queue detectors: E1 3685; E2 3678 + 5318; E4 3673 + 3674 + 3675; E6 2000; E9 3663; E12 7103; E13 5426; E14 5431.
	- E3 and E5 always use their replay counts (no 2023 Queue data at 3679 / 3670).
	- Per ramp-day, the source used and the arrivals-to-replay daily-total ratio are reported (v3 R1(c), reported, not gating).
- **All other inputs:** replay as in v5 (exogenous, identical for every arm).
- **Warm-up:** 04:00–05:00, NC for every arm.
- **After 23:00:** 24 appended bins (2 h) with zero demand at every origin and β held at the last bin. Every arm is NC there, so the network drains.
- **Metric J** (veh·h): Σ over steps of T · (vehicles in the cells + vehicles in all 16 origin queues) − Σ over steps of T · Σ_cells q·L/v_f, from 05:00 to the end of the drain. Any vehicles still present at the end are reported per arm.
- **Queue layer** (identical for every arm; `metanet_ctrl.QueueLayer`):
	- r ∈ [240, 1,800] veh/h [VERIFY: IRIS density-adaptive range];
	- max_wait = 240 s (the MnDOT config value for these meters);
	- storage S_i = config storage (ft) × 0.3048 / 8.94 m, × 1 storage lane. 8.94 m comes from the IRIS jam density of 180 veh per lane-mile [VERIFY];
	- the config storage values: E1 326, E2 350, E3 550, E4 660, E5 480, E6 370, E9 300, E12 450, E13 500, E14 420.
	- **Report row:** S × 1.25.

## 4. Arms (one control period = 60 s for every arm)
- **NC:** no metering.
- **CONST:** one rate per ramp for the whole of 05:00–23:00, tuned in-sample on the same 12 days (lowest median J). Optimistic by construction.
- **TOD-day (informed):** a constant rate per ramp in each of 4 periods (05–10, 10–15, 15–19, 19–23), tuned **per day on that day** (foresight).
- **ALINEA-day (informed):** density form, r ← clip(r + K_R (ρ* − ρ̄_s), 240, 1,800) every 60 s.
	- ρ̄_s = the 60-s mean density (veh/km/lane) of the first real-station cell downstream of the ramp's cell.
	- (K_R, ρ*) is tuned per ramp, **per day on that day** (foresight).
	- The start rate is 1,800.
- **Optimiser for the tuned arms:** pycma 4.5.0, CMA-ES.
	- Normalised box coordinates; x0 = the box centre; σ0 = 0.3.
	- 100 generations at the default population size.
	- Seeds: 7,193,010 + a fixed index per (day, arm, control set).
	- The objective is deterministic.

**Informed envelope:** E_d = min(J_CONST,d, J_TOD-day,d, J_ALINEA-day,d).

**Disclosure.** E_d is not the global optimum: a plan with finer timing could do better. So a KILL is *approximately* conservative, not strictly. Per-day-tuned feedback and time-of-day plans are the families the literature finds close to optimal on real corridors (Schmitt et al.; Frejo & De Schutter 2021) [VERIFY].

## 5. Tool checks (reported before the decision)
- **T0, per head.** On ≥ 3 of the 12 days, setting all the head's meters to 240 veh/h (with the queue layer) must lower the head's 15:00–19:00 mean inflow and change J by > 1 %.
	- B1's meters: E1–E6, E9, E12, E13.
	- B2's meter: E14 alone.
	- A head that fails T0 is reported as "no metering lever".
- **T3:** two runs give identical J.

## 6. Decision rule (10-meter set; fixed now)
- rel_d = (E_d − J_NC,d) / J_NC,d.
- **KILL if median over the 12 days of rel_d > −10 %. Otherwise GO.**
- **Reported alongside:**
	- the per-day rel_d;
	- the median per stratum (both-heavy / B1-only);
	- the percentile bootstrap CI over days (10,000 resamples; the bootstrap is seeded from the approved block);
	- each arm's median rel_d;
	- the queue-layer minutes;
	- the S × 1.25 row;
	- the T0 results;
	- the **4-meter set** (E9, E12, E13, E14) through the same arms (report-only).
- Ledger rows before and after. The job refuses a second run. The outputs are `docs/lab/day_pattern/testbed_screen.{json,md}`.

## 7. Compute (estimate, to be confirmed by the first generation's timing)
- **Scale:** ≈ 24 (day × set) optimisations per tuned arm, each 100 generations of one batched day run (B ≈ 12–15).
- **Wall time:** run as one process per (day, set) within the 32-worker rule; a few hours.

## 8. Author items
1. Approve seed block **7,193,000–7,193,999** for the testbed:
	- 000–009 smoke;
	- 010–099 this screen and plant checks;
	- 100–299 tuning;
	- 300–499 validation;
	- 500–699 exploratory head-to-head;
	- 700–999 the confirmatory run.
2. The go to run.
