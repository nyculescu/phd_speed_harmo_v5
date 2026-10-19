# Screen D2: is there headroom for incident-adaptive ramp metering?

Status: **DRAFT (V91).** The run waits for the author's approval of this page. The outcome is **CONTINUE** or **STOP**; no claim.

**Question.** When an incident hits the bottleneck (a slowdown or a blocked lane), can a controller that adapts to *this particular* incident beat the best simple responses? The particular incident means its own start time and duration. The simple responses are a fixed rate, a tuned feedback meter, and a plan stored per incident **type**.

If even a perfectly informed per-incident response gains less than 10 %, a table by incident type is enough, and direction 2 stops.

**Lesson from D1 (V90).** A screen must first show that control *matters* in the condition being tested. Rule 1 therefore includes T4.

## Plant

- **BN4 as ported in D1** (`v5b/d1/`, commit `a23613b`): constant demand q ∈ {1600, 2000} veh/h.
- **Incidents** are added from the archive's perturbation kinds (`bn4_env.py`, `claude/vsl-lab-core` @ `2a79e5e`):
  - **slow:** the bottleneck speed limit drops to 5 m/s;
  - **block:** one lane is closed on the bottleneck edge. Implemented as a lane closure, not a stopped vehicle, because the archive's stopped vehicle caused teleports.

## Rule 1. Tool checks first

| Check | What it requires | If it fails |
|---|---|---|
| T0 | The best of the arms beats no control (NC) by ≥ 10 % in every incident cell (median paired difference, CI > 0) | STOP |
| T1 | Teleports occur in < 5 % of runs per cell | STOP, or fix the incident code with a test and re-run the checks |
| T3 | The same seed run twice gives identical results | fix, then repeat |
| **T4 (new)** | In incident runs, the hindsight-best fixed controller differs from the no-incident tuned controller by ≥ 10 % in delay (the incident changes what is best) | STOP |

## Rule 2. Incidents (fixed now)

- **Two types:** slow and block.
- **Onset:** uniform in the first third of the 900-s control period.
- **Duration:** uniform 120–480 s.
- Both are seeded per seed, so every arm sees the same incident.
- **The incident and its type are known at onset** (perfect detection), which is conservative for the fallbacks.

## Rule 3. Arms

**Controller family G** (fixed now; 35 controllers):
- the D1 constant-rate grid (19 rates);
- feedback meters with K_F ∈ {10, 20, 40, 70} × n_crit ∈ {6, 8, 10, 12} (16).

| Arm | What it does |
|---|---|
| **N** | The no-incident controller: best of G on no-incident tuning runs. Used by every arm before onset |
| **FX / FB** | Keep N's class: the best single constant rate / best feedback meter, tuned on tuning seeds with incidents mixed in; no switching |
| **IP** | At onset, switch to the best controller of G **for that incident type**, tuned on tuning seeds (a stored plan per type) |
| **OR** | Oracle: at onset, switch to the best controller of G **for this seed's incident** (hindsight; an upper bound, never a method) |
| **NC** | No meter; reference only |

## Rule 4. Metric and statistics

- **Primary:** door-to-door delay including the ramp queue. Served throughput is co-headlined; TTT is reported alongside.
- **Statistics:** paired seeds; median of paired differences; 95 % percentile bootstrap CI, B = 2,000.
- **Cells:** incident type × demand (4 cells), plus a no-incident cell (report only).
- **Invalid runs:** a cell must also pass with seeds that have invalid runs removed (as in D1, A5).

## Rule 5. Decision

- **Headroom:** HD_f = (f − OR) / f, for each fallback f ∈ {FX, FB, IP}.
- **CONTINUE** if HD ≥ 10 % with the CI's lower bound > 0 against **every** fallback in at least 1 cell. **STOP** otherwise.
- The full operating map is always reported.

## Seeds (from the approved v5.B block)

| Use | Seeds |
|---|---|
| Tool checks | 7,400,080–099 |
| Tuning | 7,400,120–139 |
| Evaluation | 7,400,140–189 (50 seeds) |
| Smoke runs during build only | 7,400,000–009 |

## Cost and operation

- **Compute:** about 35 controllers × 50 seeds × 4 cells post-onset, plus tuning. Roughly 10,000 runs at about 1 s each, so minutes to under an hour on 16 workers.
- **Operation:** the CPU guard is on, in its own systemd unit, with the fan controller `vsl-cooling` running (author-authorised, "working" profile).

## Disclosures

- **The archive's BN4 results were seen.** A learned meter beat the best tuned non-learning arm by 17–28 % under slow and block (D5.10, chapter level, old seeds). This screen asks whether that headroom comes from **per-incident** adaptation or is already captured by a per-type plan.
- **D1's STOP was seen:** on constant demand, a constant rate beats the paper-gain feedback meter.
