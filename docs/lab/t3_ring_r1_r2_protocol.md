# Track 3 (RING22), phases R1 (plant checks) and R2 (baseline tuning): protocol

*Committed before any R1/R2 ring run. 2026-10-01 · branch `claude/vsl-lab-core` · roadmap §6 (Track 3)*

## Plant (frozen)

**Ring and vehicles** (`vsl_lab/plants/ring.py`):
- a single-lane ring of circumference L, 22 vehicles: 21 humans and 1 AV;
- step 0.1 s; warm-up 75 s, during which the AV drives as a noisy human; control window 300 s, i.e. [75, 375) s. These are Flow's values.

**Human model:** IDM with Flow defaults (v0 30, T 1, a 1, b 1.5, δ 4, s0 2), plus acceleration noise √dt·N(0, 0.2) (Flow master form).

**Kinematics:** SUMO integrates with `speedMode` 6; our safe-following rule stops a vehicle whose predicted gap would fall below 0.5 m.

**AV controllers** (Stern et al. 2018; the equations were checked against arXiv 1705.01693 v1 §3):
- **FollowerStopper:** Δx0 = 4.5 / 5.25 / 6.0 m and d = 1.5 / 1.0 / 0.5 m/s²; command speed U.
- **PI with saturation:** 38 s window, g_l 7 m, g_u 30 m, v_catch 1 m/s, γ 2 m, Δx_s = max(2·Δv, 4).
- **Speed tracking:** a = clip((v_cmd − v)/0.1, −3, 1.5).

**Primary metric:** mean speed of all vehicles over the control window. On a closed ring this is throughput × L / N, so a slow uniform ring is penalised.

**Secondary metrics:**
- mean across-vehicle speed standard deviation (wave amplitude);
- stop share (fraction of time the slowest vehicle is below 1 m/s);
- minimum bumper gap;
- AV mean speed.

## Disclosure (seen before this protocol; throw-away seed 7,130,000, L = 260)

| Controller | Mean speed | Across-vehicle std | Stop share |
|---|---|---|---|
| NC | 4.09 m/s | 2.19 m/s | 0.50 |
| FollowerStopper, U = 4.5 | 4.51 m/s | 0.04 m/s | 0 |
| PI with saturation | 4.87 m/s | 0.19 m/s | 0 |

With `per_step` noise, NC gave 3.94 m/s and std 2.51. The IDM equilibrium speed at L = 260 is about 4.8 m/s, which is the ceiling for uniform flow.

## R1 plant checks (seeds 7,130,010–7,130,019)

### T1-ring: waves exist

- **Runs:** NC at L ∈ {220, 230, 240, 250, 260, 270} × 10 seeds = 60 runs.
- **PASS** if, in ≥ 90 % of the runs, the mean across-vehicle std is ≥ 1.0 m/s **and** the stop share is ≥ 0.10, with 0 health FAIL.

### Control matters

- **Runs:** FollowerStopper with U ∈ {3.0, 3.5, 4.0, 4.5, 5.0, 5.5}, and PI with saturation, at the same (L, seed) pairs = 420 runs.
- **PASS** if, for ≥ 4 of the 6 lengths, the best of these controllers raises the mean speed against NC by ≥ 5 % (median of paired differences, 95 % bootstrap CI excluding 0).

### Equilibrium ceiling (reported)

- **Measure:** the IDM equilibrium speed v_e(L) for 22 equal gaps of (L − 22·5)/22. It solves the IDM steady state 1 − (v/v0)⁴ − ((s0 + v·T)/gap)² = 0.
- **Reported:** each controller's mean speed as a share of v_e(L).

### T3: determinism

- **Runs:** 6 runs drawn at random (`random.Random(7130099)`) from T1-ring, re-run in fresh processes.
- **PASS** if all 6 hashes are identical.

## R2 baseline tuning (tuning seeds 7,130,100–7,130,119; L ∈ {220, 230, 240, 250, 260, 270})

| Family | Grid | Runs |
|---|---|---|
| NC | — | 120 |
| FollowerStopper | U ∈ {2.5, 2.75, …, 7.0} (19 values) | 2,280 |
| PI with saturation | v_catch ∈ {0.5, 1.0, 1.5} × window ∈ {20, 38, 60} s (9; the paper's (1.0, 38) is in the grid) | 1,080 |

**Score and selection:**
- score = the mean over the 6 lengths of the **median** (over 20 seeds) of the mean speed. **Higher is better.**
- Tuned per family = the highest score.
- The per-L best U is also reported: it is the informed reference I for the hybrid gate (hidden condition = ring length / density).

**Frozen output:** `docs/lab/t3_ring_baselines_frozen.json` and `docs/lab/t3_ring_r1_r2.md`, committed before any R5 head-to-head.

**Expected and reported regardless:** if tuned FollowerStopper or PI comes within about 2 % of v_e(L), the ring has no meaningful headroom for DRL over the classical controllers. The ring then serves only as the pipeline check (does DRL learn to harmonise from NC?), and that must be stated.
