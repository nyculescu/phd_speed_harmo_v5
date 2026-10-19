# Screen D1 (DRAFT): is there headroom for fault-tolerant ramp metering?

Status: **DRAFT (V88), not approved.** No run before the author approves this page and its seeds. Outcome: **CONTINUE** or **STOP**; no claim.

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
