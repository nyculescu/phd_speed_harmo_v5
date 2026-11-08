# Round 2, addendum M: the measurement pack (report-only)

**Status: draft, 2026-11-07 (V468). Written before any measured row exists. Fixed here: the metrics and their definitions. Nothing here changes a round-2 reading, verdict or sentence.**

## Purpose

Round 2's rows hold totals and a few counts. For the article and the thesis, the author asked for the distributions behind them:
- speeds and accelerations;
- hard braking and how it spreads;
- merge bottlenecks;
- waves;
- petrol fuel.

This addendum fixes how each one is measured and summarised.

## What runs

- **Runs:** the round-2 test and band runs again, with the same configurations, seeds and code, plus the pack.
  - Test: 70 arms × 40 seeds = 2,800 runs.
  - Band: 24 arms × 5 levels × 20 seeds = 2,400 runs.
- **No new seed.** The runs are deterministic, so a measured run is the same trajectory as the stored one.
- **The pack only reads the simulation** (libsumo getters).
- **Gate before the batch (smoke, `measure2.py smoke`).** Seven sample runs must match their stored rows on every key, after the same JSON round trip. The sample covers no control, a v3w policy, tail, sw, 3E-X2, a band rule and a band policy. The pack's own sums must also match the plant's counters:
  - speed and acceleration bins = vehicle-steps;
  - distance and fuel = `dist_step` and `fuel_step`;
  - braking-event time = `b3_step`;
  - merge-2 outflow ≈ `passed`.
- **Code:** `v5b/fleet/measure.py` and `docs/research/round2/measure2.py` on branch `r2/metrics`, with tests in `tests/test_measure.py`. The batch runs from a frozen copy of that commit.

## Metrics

**Window:** after the 300-s warm-up, to 1,800 s, as every round-2 counter.

**Classes:**
- car (human-driven);
- ALKS (automated car);
- truck.

Cars and ALKS use SUMO 1.27.1's default class, HBEFA4 PC_petrol_Euro-4. Trucks use the default articulated diesel Euro VI class. These defaults were checked in the SUMO source, so **petrol fuel = cars + ALKS only**, and trucks are reported apart.

| Group | Metric | Definition |
|---|---|---|
| Speed | distribution per class | vehicle-steps (0.1 s) in 5-km/h bins; report the 5th, 25th, 50th, 75th and 95th percentiles |
| Acceleration | distribution per class | vehicle-steps in 0.5-m/s² bins from −10 to +5; the same percentiles; RMS acceleration |
| Hard braking | events | a run of consecutive steps with a ≤ −3 m/s²; its peak (bins at −3, −3.5, −4, −4.5, −5, −6, −7, −8, −9 m/s²) and duration (braking steps × 0.1 s; bins at 0.5, 1, 2, 3, 5, 10 s) |
| Hard braking | cascade share | share of events whose vehicle's leader (within 200 m) started an event at most 3 s earlier |
| Fuel | petrol, g/km | fuel of cars and ALKS integrated per step, divided by their distance; L/100 km printed with 745 g/L [VERIFY] |
| Merges (m1 = 3a → 3, m2 = 4a → 4) | discharge | vehicles leaving each acceleration section per minute (1-Hz road changes) |
| Merges | breakdown | first minute whose acceleration-section mean speed is below 60 km/h for 2 minutes in a row; recovery: 2 minutes above 60 km/h again |
| Merges | capacity drop | the best 5-minute discharge before breakdown against the mean discharge from breakdown to recovery or the end, % |
| Merges | slow minutes | minutes with the acceleration section below 60 km/h |
| Merges | merge position | where on the acceleration lane a vehicle left it (10 bins of its length, 1-Hz) |
| Ramps | queue | ramp vehicles below 1 m/s, plus vehicles waiting to be inserted on that ramp's route; mean and maximum per minute |
| Waves | space-time field | 1-Hz samples of every mainline vehicle (edges 1 → 5, 6,778 m, lanes pooled) in 10-s × 50-m cells: mean speed and vehicle-seconds |
| Waves | jam and congested share | vehicle-weighted share in cells below 30 and below 60 km/h |
| Waves | jam clusters | 8-connected groups of cells below 30 km/h, at least 3 cells; per cluster, duration, extent and front speed (linear fit of the upstream front over time; negative = moving upstream) |
| Waves | oscillation | the temporal standard deviation of cell speed at each station occupied in at least 80 % of the time bins, averaged over stations |
| Waves | congested length | cells below 60 km/h × 50 m per time bin; its mean and maximum |

## Statistics and reading

- **Report-only.** Per arm and cell, the distribution over seeds is shown as ASCII panels like the speed panels (range, middle half, median). Policy arms are the per-seed mean of their 5 learners.
- **Paired effects** use round 2's statistic (median of paired differences, 95 % percentile bootstrap) and are labelled descriptive.
- **No claim sentence rests on these metrics without a new protocol.**
- **Limits:**
  - 1-Hz road changes can place a merge up to one second late;
  - the space-time field leaves out junction lengths (a few metres);
  - the 30 and 60 km/h thresholds are conventions, not calibrated values [VERIFY against the literature before citing].

## Smoke result (2026-11-07, before any measured batch)

- **`measure2.py smoke`: PASS.**
  - All 7 sample runs equal their stored rows on every key, after the JSON round trip.
  - Every consistency check holds: bins = vehicle-steps; distance, fuel and braking time = the plant's counters; merge-2 outflow ≈ `passed`.
  - Folders: `v5b1_runs/round2_measure_smoke_2331`, and `_2329`, the first pass. It stopped on two checker defects, with no difference in the simulation: the tuple/list form of `pert_log`, and an ill-defined −9 m/s² comparison. Both checks were fixed before the second pass.
- **Unit tests:** `tests/test_measure.py`, 9 tests on inputs with known answers (a jam front at −18 km/h, a 14.3 % capacity drop, braking events and cascades). The full suite passes: 514 tests.
- **Cost of the pack:** one run takes 29.8 s with it against 24.1 s without (×1.24, idle laptop). Side files are about 93 KB per run (about 0.5 GB for the batch), and rows about 10 KB.
- **Job files** are written (`v5b1_runs/round2_measure/job_test.json`, `job_band.json`). Nothing has run.

## Compute

5,200 runs (runs × rate):
- **Laptop, day:** about 1,330 runs per hour untraced at 31 workers (V425), ÷ 1.24 ≈ 1,070 runs per hour, so about 4.9 h.
- **Laptop, night:** the 40 % cap from 23:00 to 09:00 allows about 12 workers, so about 12 h.
- **The last rental** (122.9 CPUs, about 58 runs per minute untraced): about 47 per minute with the pack, so about 1.9 h, or about $1.5 at $0.774/h.

The batch runs through the CPU guard (laptop) or the rented-machine finisher, from a frozen copy of `r2/metrics` `765bdc2`, only after the author starts it.
