# G-1 stage S1: narrow band + headroom with oracle stand-ins for DRL (pre-registration, 2026-10-09)

**Question.** Inside the demand band found by S0, is there anything a learned controller could win? No learning: the "artificial DRL" is a pair of **oracles that cheat on purpose** (author request 2026-10-09). If even the oracles cannot beat the best non-learning controller by 10 %, DRL cannot either, and the cell is a KILL. Plant facts and headroom only; no thesis claim.

## Cells (from S0, `g1_demand_extremes.md`; H5 only: H3 showed no capacity drop)
| cell | layout · ramp | S1a main_peak levels (veh/h) |
|---|---|---|
| M3 | merge · 300 | 5,400–6,600 step 200 |
| M9 | merge · 900 | 3,600–4,200 step 200 |
| Z3 | zipmerge · 300 | 4,800–6,000 step 200 |
| Z9 | zipmerge · 900 | 3,000–4,200 step 200 |
| L9 | lanedrop · 900 | 3,000–4,200 step 200 (S0: ramp level had no effect; reported, not explained here) |

## S1a: narrow the band (NC only)
- Seeds 7,170,100–109 (10 per level), 320 runs.
- **Chosen level per cell (fixed rule):** the level whose breakdown share is closest to 0.5; ties → the lower demand. A cell whose shares are all 0 or all 1 is reported and dropped.

## S1b: controllers at the chosen level
- Fresh seeds 7,170,200–209 (10), plant and options as S0.
- **Non-learning:** nc; const:b for b ∈ {0.5, 0.6, 0.7, 0.8, 0.9}; mtfc (default parameters; **untuned**, labelled).
  - **Tuned constant** = the b with the lowest median metric over the 10 seeds (in-sample, labelled).
  - **Best non-learning (BNL)** = the lowest median among nc, tuned constant, mtfc.
- **Oracles (upper bounds, cheat on purpose, never comparators):**
  - O1 = per seed, the minimum over nc and the 5 constants;
  - O2 = per seed, the minimum over O1's set and win:b:t0:t1 with b ∈ {0.6, 0.7, 0.8}, t0 = onset_nc − {300, 900} s, t1 = t0 + {1,800, 3,600} s, where onset_nc is that seed's NC onset (12 variants; seeds with no NC breakdown get O1's set only).
- **Metric:** door-to-door mean time in system incl. origin queues (`mean_time_in_system_s`; CLAUDE.md primary), co-reported: teleports and the drained flag (exit throughput is not in the job summary line; every run drains until empty, so all demand is served and the time metric carries the comparison).
- **Headroom H** = (median BNL − median O2) / median BNL, with the median of paired per-seed differences and a 95 % percentile bootstrap CI (10,000 resamples, seed 7,170,299).
- **Verdict per cell:** KILL if H < 10 % or its CI lower bound ≤ 0; otherwise "HEADROOM (oracle)", which only licenses the next stage (length sweep, then a real DRL protocol).

## Disclosed limits
- The oracles' per-seed minimum also picks lucky noise, so H is biased **upwards**: a KILL is conservative, a HEADROOM is optimistic.
- 10 seeds; the tuned constant is chosen in-sample (biases BNL down, i.e. H down) and mtfc is untuned (H up).
- S0's discharge ratios used 2 seeds; S1 reports them again on the S1a runs.
