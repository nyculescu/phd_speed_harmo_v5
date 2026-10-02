# Track 2 (MRG3), phase R2 baseline tuning and T2 mechanism: protocol

*Committed before any R2 run. 2026-10-02 · runs only if T2 R1 passes T1 (capacity drop) and T0 (actuator), per the R1 decision rule.*

## Cells, seeds and path

- **Demand:** the cell selected by calibration (`docs/lab/t2_mrg3_calibration.json`).
- **Hidden condition:** the non-compliant share p_nc ∈ {0.1, 0.3, 0.5}, giving three cells.
- **Tuning seeds:** 7,120,100–7,120,119 (20 per cell, paired across controllers).
- **Path:** `vsl_lab/jobs/mrg3_run.py`: control from 300 s, period 60 s, safety staircase, uncontrolled drain.
- **Primary metric:** mean door-to-door time per vehicle, including the origin queue.
- **Side metric:** on-ramp users' door-to-door time.

## Controllers

| Family | Grid |
|---|---|
| NC | — |
| Constant VSL | b ∈ {0.5, 0.6, 0.7, 0.8, 0.9} |
| MTFC (Carlson 2013) | ρ̂ ∈ {14, 17, 20, 23, 26, 29, 32} veh/km/lane × gains ∈ {paper (K′P 38, K′I 9, K_I 0.0015), half (19, 4.5, 0.00075), double (76, 18, 0.003)} = 21 settings |

That is 27 controllers × 3 cells × 20 seeds = 1,620 runs.

## Selection and readings (fixed now)

- **Score** = the mean over cells of the median door-to-door time. Tuned per family = the lowest score.
- **Side constraint:**
  - the tuned controller's on-ramp users' median time must be ≤ +10 % of NC in every cell;
  - otherwise the next-best setting that satisfies it is selected and both are reported.
- **T2 mechanism (hybrid gate, CLAUDE.md):**
  - G = (cost of the pooled-best MTFC − cost of the per-class-best MTFC) / cost of the pooled-best, using the class means of the median costs, on these same seeds (biased upwards);
  - PASS if **G ≥ 10 %**.
- **Informed reference I:** the per-class-best MTFC (class → setting), frozen for later gates.
- **Frozen outputs:** `docs/lab/t2_mrg3_baselines_frozen.json` and `docs/lab/t2_mrg3_r2.md`.
