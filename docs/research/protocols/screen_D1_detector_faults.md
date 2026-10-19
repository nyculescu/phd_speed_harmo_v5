# Screen D1 (DRAFT): is there headroom for fault-tolerant ramp metering?

Status: **APPROVED (V89); addenda below.** Outcome: **CONTINUE** or **STOP**; no claim.

**Question.** When the meter's mainline detector fails, how much better is healthy feedback metering (the oracle) than the best simple fallback? If even the oracle gains little, no fault-tolerant algorithm can, and direction 1 stops here.

## Plant (ported, not new)

- **Source:** the BN4 single-merge SUMO plant from `claude/vsl-lab-core` @ `2a79e5e`:
  - `vsl_lab/netgen/bn4.py`;
  - `vsl_lab/envs/bn4_env.py` (the `FBMeter` feedback meter, door-to-door metric including the ramp insertion queue);
  - the CPU guard `vsl_lab/ops/guard.py`.
- Each port is recorded in its commit message.
- Demand q ∈ {1600, 2000} veh/h, as in the archived scans. No other perturbation, so the effect of the fault is isolated.

## Rule 1. Tool checks first (before any arm comparison)

| Check | Pass condition | If it fails |
|---|---|---|
| T0 | The healthy meter beats no control (NC) by ≥ 10 % (median paired difference, CI excluding 0) | STOP |
| T1 | Teleports occur in < 5 % of runs | STOP |
| T3 | Two runs with the same seed are identical | fix the code, then repeat |

## Rule 2. Faults (fixed now)

- **Which detector:** the mainline loop(s) the meter reads.
- **Four fault types:**
  - **stuck-off:** reads 0;
  - **stuck-on:** reads saturated;
  - **noisy:** multiplicative noise, σ = 50 %;
  - **dropout:** no data.
- **Timing:** onset uniform in the first third of the controlled period; the fault lasts to the end of the episode.
- **Detection is assumed perfect and instant.** This favours the fallbacks, so the test is conservative.

## Rule 3. Arms

| Arm | What it does |
|---|---|
| **O** | Healthy meter: the true readings, fault ignored (oracle) |
| **FX** | On fault, switch to the best constant rate, tuned per demand on tuning seeds |
| **RF** | On fault, fill in the faulty loop from an upstream healthy loop × a ratio learned on tuning seeds |
| **NV** | Report only: the meter keeps using the faulty reading |
| **NC** | No control; reference only, never reported alone |

## Rule 4. Metric and statistics

- **Primary:** door-to-door delay including the ramp queue. Served throughput is co-headlined; TTT is reported alongside.
- **Statistics:** paired seeds; median of paired differences; 95 % percentile bootstrap CI, B = 2,000. Cells are fault type × demand (8 cells).

## Rule 5. Decision

- **Headroom:** HF = (best of FX, RF − O) / best of FX, RF.
- **CONTINUE** if HF ≥ 10 % with the CI's lower bound > 0 in at least 1 cell. **STOP** otherwise.
- The full operating map (all arms × cells, including NV and NC) is always reported.

## Seeds (proposed, from the approved v5.B block; needs the author's approval)

| Use | Seeds |
|---|---|
| T checks | 7,400,010–029 |
| Tuning FX and RF | 7,400,100–119 |
| Screen evaluation | 7,400,030–079 (50 seeds) |

## Cost (estimates)

- **Author:** about 0.5 h to read and approve.
- **Claude:** port, fault layer, arms and tests, about 6–10 h including review.
- **Compute:** 5 arms × 4 faults × 2 demands × 50 seeds = 2,000 short runs, minutes on 32 workers. Run under the CPU guard in its own systemd unit.

## Disclosures

- **Archived BN4 results were seen.** A constant rate was the best non-learning arm in the none, block and surge conditions (`t1_meter_bn4_confirm.md`). FX is therefore a strong rival, and **STOP is a likely outcome**.
- **The fault timing and severity are assumptions,** not taken from PeMS. PeMS health flags are kept for a later confirmatory test.

## Addendum (2026-10-19): review fixes before the run

Under the V89 policy, each item below adds a check, strengthens a rival or adds reporting. None relaxes a rule. All were fixed before any T-check or evaluation seed ran.

- **A1. FX tuning grid.** FX is the best constant rate on the grid {600, 800} ∪ {1000, 1100, …, 2600} veh/h (19 rates), tuned per demand on the tuning seeds (lowest median delay; the lower rate on a tie). It is a superset of the build grid (600–1600 in steps of 200, then 2000 and 2400). It was chosen after a review probe on calibration seeds 7,400,003–005 (disclosed): the gap between 1600 and 2000 could hold FX back. **If a tuned rate lies at a grid edge (600 or 2600), the screen halts before evaluation** with the decision "HALT (extend FX grid)". The evaluation seeds stay untouched, and any extension needs a new addendum.
- **A2. Fallback set = {FX, RF, HL}.** HL holds the last healthy meter rate from detection on. Under perfect detection its runs are the NV-dropout runs, identical by construction (a missing reading holds the rate), so it needs no new runs. **A cell passes only if HF_f ≥ 10 % with its CI lower bound > 0 against every fallback f in the set.** The Rule 5 HF against the best of FX and RF (by median delay) is still reported.
- **A3. Reporting, no rule change.**
  - The result reports RF's fill quality on the tuning seeds: the RMSE of ratio × the edge-3 count against the true edge-4 count, their correlation, and the SD of the true count. On BN4, edge 3 lies between the meter and edge 4, so RF may carry little information about the bottleneck.
  - Under perfect detection, O, FX, RF and HL do not depend on the fault type. The 4 fault cells of a demand therefore share these runs, and **the decision has 2 independent cells (one per demand)**. Only NV differs across fault types.
- **A4. T0 is checked per demand; both demands must pass, else STOP.** This is the strictest reading, as coded.
- **A5. Invalid runs.** A run is invalid if it is not drained, has missing trips, or has health FAIL (for example a teleport). If any O, FX, RF or HL evaluation run of a seed in a cell is invalid, the cell is also computed without those seeds. **It passes only if it passes both with and without them;** with no valid seed left, it fails. Both results are reported.
- **A6. Run once, enforced in code.**
  - Before the evaluation stage, the runner writes `/home/catalin/work/phd/v5b1_runs/D1_EVAL_STARTED.json` (out path, commit, page sha256, arguments). While it exists, any later non-smoke invocation is refused, except `--resume` of the same `--out` at the same commit.
  - Non-smoke runs refuse a dirty work tree and any K_F or n_crit other than 20 and 8. The FX grid is fixed in code (A1).
  - On `--resume`, a stored run is reused only if its arm, fault, demand, seed, q_fx, ratio, K_F, n_crit and code commit all match; otherwise the run is refused.
- **A7. Status.** V89 approved this page as written. The file was renamed from `screen_D1_detector_faults_draft.md` and its status line was updated. The "(DRAFT)" in the heading and "proposed" in the seeds heading are approved text, kept unchanged.
