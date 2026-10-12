# Testbed stage 1b: metering authority screen (KILL-only), pre-registration v1

*2026-10-11 · branch `claude/day-pattern-core` · decisions D5.11 (lean path), D5.12 (10 meters) · v0 (14f2951) checked once, wf_02bb4f1f-1bb: 8 fixes, all folded in here (§10) · binding once committed with the author's go; it runs once*

## 1. Question and the only outcomes

**Question.** On the frozen v5 plant, can ramp metering at the 10 field-metered ramps beat no control (NC) by ≥ 10 % even when the controller is tuned for each day with foresight?

| Outcome | Meaning |
|---|---|
| **KILL** | The corridor testbed stops: no stage 2, no protocol v1. |
| **NEAR-MISS** | The KILL is not final (§6). |
| **GO** | Licenses writing protocol v1 only. It is not a claim, and no number from this screen may be quoted as a result. |

## 2. Days, plant, stepper, guards
- **Days:** the 12 train-source days of `docs/lab/day_pattern/testbed_day_split.json`.
	- The split is a stratified, hand-fixed position pattern, written after the design inputs of §9. **The author approves it explicitly with the go**; otherwise it is redrawn by a seeded stratified draw before the run.
	- 20230705 (the day after the 4 July holiday; its NC over-critical time at B1 is 25 min) is kept by the rule. A median-without-it row is reported.
- **Guards:** before building a stepper, the job asserts that every simulated day is in `split["train"]` and is not one of the 97 v5 validation days.
- **Plant:** the frozen v5 nominal, deterministic (c1 = c2 = 1).
- **Stepper:** `vsl_lab/plants/metanet_ctrl.py`, which reproduces `simulate()` bit for bit in replay (72e7e1c).
- **Cell numbering:** cells are 0-based code indices; document (1-based) numbers are in brackets.

## 3. Inputs, time window, metric, queue layer

**Demand at the 10 meters** (E1–E6, E9, E12, E13, E14):
- **Detectors:** Queue-detector arrivals with E1 3685; **E2 3678 only** (3678 and 5318 are in series and count the same vehicles: sum/replay = 2.002); E4 3673 + 3674 + 3675 (parallel lanes); **E5 3669 only**; E6 2000; E9 3663; E12 7103; E13 5426; E14 5431. E3 uses its replay counts (3679 has no 2023 data).
- **When arrivals are used:** a ramp-day uses arrivals only if both hold:
	1. they pass the inputs code's validity rule for an input lane (`metanet_inputs.py:114-145`: no gap > 15 min in 04–23 h, ≥ 90 % valid 5-min bins, non-zero 06–20 h counts, every listed detector valid);
	2. |Σ05–23 arrivals / Σ05–23 replay − 1| ≤ 0.05.
- **Fallback:** a failing ramp-day keeps the Queue timing, rescaled to the replay daily total; if no valid timing exists, it uses the replay series. This is disclosed.
- **Listing and test:**
	- the source and ratio for every ramp-day are listed in `testbed_screen_inputs.json`, committed before the run;
	- a unit test asserts that every ramp-day's 05–23 demand total is within 5 % of replay;
	- NC and every arm use the same demand.

**Other inputs:** replay as in v5 (exogenous, identical for every arm).

**Time window:**
- 04:00–05:00 is NC for every arm.
- After 23:00, 24 appended bins (2 h) have zero demand at every origin and β held at the last bin. Every arm is NC there, so the network drains.
- A test checks that the first 228 bins of the padded run are bit-identical to replay and that cells and queues are empty at the end.

**Metric J** (veh·h, from 05:00 to the end of the drain): Σ_steps T·(vehicles in the cells + in all 16 origin queues) − Σ_steps T·Σ_cells q·L/v_f. Vehicles still present at the end are reported per arm.

**Queue layer** (identical for every arm; as coded at `metanet_ctrl.py:31-37, 186-199`):
- r_eff = min(1,800, max(r_cmd, r_wait, r_stor)), where
	- r_wait = 3,600·w/240;
	- r_stor = d̂ + 3,600·(w − 0.75 S)/60 for w > 0.75 S;
	- a hard net forces r_max from w ≥ S until w ≤ 0.5 S.
- r ∈ [240, 1,800] veh/h [VERIFY: IRIS density-adaptive range].
- max_wait = 240 s is an **assumed IRIS default**: the metro_config gives no max_wait for these 10 meters (97 other meters carry 120 s) [VERIFY].
- **Storage:** S_i = config storage × 0.3048 / 8.94 m × lanes. The foot unit, the single lane and the 8.94 m (IRIS 180 veh per lane-mile) are all [VERIFY].
	- Config storage values: E1 326, E2 350, E3 550, E4 660, E5 480, E6 370, E9 300, E12 450, E13 500, E14 420.
- **Two storage rows:**
	- **S×1:** one lane everywhere;
	- **S_gen:** E4 × 3 (its Queue detectors split the flow 0.47 / 0.24 / 0.32, so 3 lanes at the detector), every other ramp × 1.25.
- **Consequence, disclosed:** at S×1 the meters can withhold at most about Σ 0.75 S ≈ 113 veh (10 meters), 102 of them at the B1 feeders, and 43 for the 4-meter set. max_wait binds only above 16 veh (E4 only).

## 4. Arms (one control period = 60 s; per-day arms are tuned on that day, i.e. with foresight)

**Benchmark arms:**
- **NC:** no metering.
- **CONST:** one rate per ramp for 05–23 h, tuned on the median over the 12 days of rel_d (one pooled process per control set).
- **TOD-day:** one rate per ramp in each of the periods 05–10, 10–15, 15–19 and 19–23.
- **TOD-fine-day:** per meter, an on window (t_on, t_off) inside 12:00–20:00 at 60-s resolution, with one rate in [240, that ramp-day's maximum 5-min demand], and NC outside the window (30-D).

**Two ALINEA arms**, density form, r ← clip(r_prev + K_R (ρ* − ρ̄_s), 240, 1,800) every 60 s, where ρ̄_s is the 60-s mean density (veh/km/lane) of the sensed cell:

| Arm | Sensed cell per ramp |
|---|---|
| **ALINEA-day** (local sensing) | the first real-station cell downstream of the ramp's cell: E1 → 2 [3]; E2 → 5 [6]; E3 → 5 [6]; E4 → 8 [9]; E5 → 11 [12]; E6 → 13 [14]; E9 → 20 [21]; E12 → 24 [25]; E13 → 31 [32]; E14 → 34 [35] |
| **ALINEA-B-day** (bottleneck sensing) | every B1 feeder (E1–E6, E9, E12, E13) senses cell 26 [27] (S1147, just upstream of the B1 head); E14 senses the maximum density over cells 32–33 [33–34] |

Common rules for both ALINEA arms:
- **Tuning boxes:** K_R ∈ [5, 300] veh/h per (veh/km/lane), log scale [VERIFY against the density-ALINEA source]; ρ* ∈ [0.6, 1.2] × ρ_cr of the sensed cell (frozen parameters, after θ1).
- **Anti-windup:** r_prev ← the applied r_eff whenever the queue layer or the hard net binds.
- **State:** 1,800 veh/h at 05:00; discarded at 23:00 (NC in the drain).

**Optimiser:** pycma 4.5.0, CMA-ES.
- **Rate boxes:** per ramp, [240, that ramp-day's maximum 5-min demand]. A coordinate whose demand never exceeds 240 veh/h inside the arm's window is fixed at NC and dropped.
- **Starting point:** for TOD arms, x0 = the CONST optimum, so each starts no worse than CONST; for the others, a demand-matched plan. σ0 = 0.3 in normalised coordinates.
- **Stopping:** in 50-generation blocks until the best-so-far improves by < 0.2 % of J_NC,d over 50 generations, capped at 400 generations.
- **Restarts:** 2 per (day, arm), keeping the best.
- **Reported:** best-so-far traces and the restart spread.
- **Seeds:** pycma seed = `SeedSequence([7193010 + k(set, arm), day_index, restart])`, where k enumerates (set, arm) in a fixed listed order; bootstrap seed 7,193,099.

**Envelope:** E_d = min(J_NC,d and every arm's optimum on day d).

**What E_d means.** E_d bounds what these families achieve, not the optimum. D5.1 (Frejo & De Schutter 2021 Part 2, read in full) puts the room over a tuned MTFC+PI-ALINEA at about 9 % on SE-30, the order of the bar. A KILL here is therefore "no ≥ 10 % room for the tested informed families", not a proof that no controller could find it.

## 5. Tool checks (reported before the decision)

**T0 per head.** Measured as the 15:00–19:00 mean head inflow:
- B1 inflow = the flow from cell 26 into cell 27 (the B1 head), plus E13's release;
- B2 inflow = the flow from cell 31 into cell 32, plus E14's release.

T0 passes for a head if, on ≥ 3 of the 12 days, setting all of its meters to 240 veh/h (with the queue layer) lowers that head inflow and changes J by > 1 %. The head's meters are E1–E6, E9, E12 and E13 for B1, and E14 for B2.

| T0 outcome | Consequence |
|---|---|
| Both heads FAIL | KILL |
| One head FAILs | reported and disclosed; the rule is unchanged |

**T1** (reported): NC over-critical minutes per day at cell 26 and at cells 32–33.

**T3:** two runs give identical J. A FAIL means: stop, fix, re-run everything affected, and log both.

**Smoke:** one train day on seeds 7,193,000–009, for timing only; no J-versus-NC figure is shown.

## 6. Decision rule (10-meter set; fixed now)
rel_d = (E_d − J_NC,d) / J_NC,d. For each storage row (S×1, S_gen), m = the median over the 12 days of rel_d.

| Condition | Outcome |
|---|---|
| m ≤ −10 % in **either** storage row | **GO** |
| −10 % < m ≤ −7 % in the better row | **NEAR-MISS**: the KILL is not final. A true-model, perfect-forecast MPC (review item 5(4)) is built and run first on train days 20230118, 20230517 and 20230816, under an addendum written before it runs. |
| otherwise | **KILL** |

**Reported alongside:**
- the per-day rel_d;
- the median per stratum;
- the bootstrap CI over days;
- each arm's median rel_d;
- the queue-layer and hard-net minutes;
- the median without 20230705;
- the T0 and T1 results;
- the **4-meter set** (E9, E12, E13, E14) through the same arms, report-only.

**Running:** ledger rows are written before and after; the job refuses a second run. The outputs are `docs/lab/day_pattern/testbed_screen.{json,md}`.

## 7. Compute
- One padded 12-day NC run takes about 20 s in one process.
- Each per-day optimisation runs up to 400 generations × 2 restarts of a batched day run (B = the population size).
- The jobs run one process per (day, set, arm) within the 32-worker rule and the CPU rule.
- **Estimate:** several hours; it is timed by the smoke run.

## 8. Author items (with the go)
1. Approve seed block **7,193,000–7,193,999**:
	- 000–009 smoke;
	- 010–099 this screen and plant checks;
	- 100–299 tuning;
	- 300–499 validation;
	- 500–699 exploratory head-to-head;
	- 700–999 the confirmatory run.
2. Approve the hand-fixed split, or ask for a seeded redraw.
3. The go to run.

## 9. Design inputs taken before this pre-registration (disclosed)
1. The full-testbed review's controlled prototypes on all 22 days: per-day effects −17.7 % to +73 %; all meters at 240 veh/h gave J +9.4 %; E13 T0-M gave −0.66 % to +0.10 %.
2. The D5.12 demand look that changed the control set.
3. The stepper tests' controlled runs on 20230118 (asserts only).
4. The v0 check's NC-only runs on the 12 train days: the E2 ratio, NC J, the onsets (B1 onset before 15:00 on 6 of 12 days), and the drain.
5. The hand-fixed split, written after items 1 and 2.
6. Plant status: the frozen nominal fails P5b-1, an exaggerated B1 drop (r_model 0.977 vs real 1.006), and B1 jams on 16 of 22 calibration days.

## 10. Changes from v0 (check wf_02bb4f1f-1bb)
| Fix | What changed |
|---|---|
| F1 | demand: E2 double count, the plausibility rule, E5 3669 |
| F2 | TOD-fine-day and ALINEA-B-day added; the near-miss band; the optimality sentence softened |
| F3 | optimiser boxes, warm starts, convergence, restarts, CONST on rel_d |
| F4 | ALINEA boxes, anti-windup, state, sensed-cell tables |
| F5 | the layer as coded, the storage rows S×1 and S_gen, max_wait assumed |
| F6 | T0 inflow definition and consequences, T1, T3, seeds, guards, the drain test |
| F7 | E_d includes NC; the 20230705 row |
| F8 | the disclosures of §9 |

## 11. Implementation readings (code check wf_932c84c8-fe9, fixed before any run)
The check found two blocking bugs, both fixed and covered by tests:
- the ALINEA arms read a density buffer that was cleared before use, so they never metered;
- per-day arms built a ragged batch, so they crashed at generation 1.

It found one major gap, also fixed: worker failures and stale results went unseen. Every opt file now carries the run id, HEAD and J_nc; the run asserts that every worker succeeded and refuses foreign results; a failure writes a ledger row.

The readings below are fixed now:

**Optimiser**
- **TOD-fine-day windows** are evaluated per 60-s period (t_on ≤ minute < t_off; minutes from 04:00), not per 5-min bin.
- **Box tops:** TOD-day and TOD-fine-day use the ramp-day's 05–23 h maximum 5-min demand; the drop rule still uses the window's maximum. CONST's box top is the maximum over the 12 days (it is pooled).
- **Warm starts, as coded:**
	- CONST starts at the box top (the max-demand corner, ≈ NC);
	- TOD-day starts at the CONST rate, clipped to its box;
	- TOD-fine-day starts with its window over all of 12:00–20:00 at the CONST rate (NC outside);
	- ALINEA arms start at K = 38.7 (log-centre) and ρ* = ρ_cr.
	- The warm start is **evaluated at generation 0**, so best-so-far starts there and the first convergence test falls at generation 50.
- **Seeds:** each CMA-ES instance draws from its own generator `np.random.default_rng(seed_for(...))`, passed through pycma's `randn` option with `seed = nan`, so the global RNG plays no part. Pooled CONST uses day_index 99. Seeds are shared across the two storage rows (independent runs, as §4 states).

**ALINEA arms**
- **Anti-windup:** if the queue layer or the hard net bound at **any** step of the 60-s period, r_prev ← the last bound applied r_eff.
- **E14 in ALINEA-B-day** senses the maximum of the 60-s means of cells 32 and 33.

**Checks and run layout**
- **T1** counts steps with ρ > ρ_cr (05–23 h).
- **T3** compares NC twice, plus fixed CONST, TOD-fine and ALINEA-B candidates evaluated alone and inside a mixed batch, all bitwise. The run also asserts that each day's re-evaluated best equals its recorded best.
- **Layout:** one process per (set, storage row, arm), each batching its 12 days × 2 restarts × population. That is 4 CONST processes, then 16 arm processes, against §7's "per (day, set, arm)".
- **Gate:** a load gate (load < 15 % within 30 min) runs before the arms batch. On a timeout the run pauses with a ledger row and resumes by run id.
- **Provenance:** the calib_data hash must equal the committed facts; no screen day may be a v5 validation day; the padded inputs' hash must equal the committed listing; the prereg, the listing, the split and both code files must be committed and unchanged.
- **Smoke:** times one full TOD-day generation (12 days × 2 restarts) on seeds 7,193,000–023.
