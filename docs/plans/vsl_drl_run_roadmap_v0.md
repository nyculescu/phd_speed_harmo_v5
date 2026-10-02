# VSL / harmonisation DRL lab: run roadmap (v0)

*2026-10-01 · branch `claude/vsl-lab-core` · planning only; no simulation run yet · companion to `docs/plans/vsl_hybrid_screen_v0.md`*

**Goal (author, 2026-10-01).** Find, by systematic search, a road configuration and a state–action–reward (SAR) design in which a DRL controller (hybrid or not):
- learns: its reward converges and the policy is not degenerate;
- harmonises traffic;
- **really** beats something worth beating.

Refactor the environment and SAR as needed. Many branches are allowed. Hard limits: **≤ 100 workers** and **CPU package < 90 °C**.

---

## 0. Rules of the search (the honest version of "find a way")

The search may be as wide as we like; how it is reported must stay honest. Six rules make a positive result defensible in a viva:

1. **Every run is logged** in `vsl_lab/runs/ledger.csv`, including crashed, failed and abandoned ones, each with its git commit, config hash, seeds, health status and result summary. A claim always says "selected from N variants".
2. **Seed roles never mix:**
   - **training** episodes;
   - **validation** seeds, used only to screen variants and select checkpoints;
   - **test** seeds, for exploratory head-to-heads;
   - **confirmatory** seeds, used once per frozen candidate.
3. **Baselines get tuning effort on par with DRL.** Every baseline is tuned on tuning seeds (grids are logged), and the DRL hyperparameter budget and the baseline tuning budget are both reported.
4. **The primary metric is fixed per track before that track's first DRL run** (§9). The objective is door-to-door delay *including* origin and insertion queues, co-headlined with served throughput. No proxy (speed variance, smoothness) is ever a headline or the main reward (`docs/lessons_metric_gameability.md` §4).
5. **Picking the niche is legitimate; rigging it is not.** It is fair to pick conditions where DRL has a structural reason to win, such as measurement lag, partial observability, hidden non-stationarity or fast per-vehicle decisions. Three conditions apply:
   - the conditions are field-plausible;
   - the baselines get the same information and are tuned for those same conditions (e.g. a delay-compensated MTFC);
   - the report states where DRL does *not* win.
6. **Exploratory vs confirmatory.** Everything in R1–R5 below is exploratory. A thesis claim needs R6: a frozen candidate, pre-registered comparators and metric, and a single run on fresh seeds.

**Scope changes in the author's message that conflict with `CLAUDE.md`** (to confirm, §13):
- (a) direct DRL is allowed again ("hybrid or not");
- (b) exploratory DRL may start *before* a headroom gate;
- (c) the worker cap becomes 100, with < 90 °C, replacing 32 / 120.

## 1. Starting points: the most credible evidence

| What | Evidence (read status) | Use here |
|---|---|---|
| **Capacity drop in SUMO, and RL that learns at a bottleneck** | Vinitsky et al. 2018, ITSC, read in full: "Lagrangian control through deep-RL". 4→2→1-lane zipper bottleneck in SUMO/Flow; **outflow drops once inflow exceeds about 1,500 veh/h** (Fig. 6: sweep of 400–2,500 veh/h, 10 runs each). With 10 % AVs, RL holds outflow at about 1,000 veh/h, "a 25 % improvement at high inflows". Against **tuned** feedback ramp metering it "matches" above the critical inflow and "under-performs" below it. Reward: "simply … the outflow over the past 20 seconds"; TRPO with a GRU policy, 400 iterations. Geometry from the public Flow code (`flow/networks/bottleneck.py`): edges 100 / 310 / 140 m with 4 lanes, then 280 m with 2 lanes, then 155 m with 1 lane, 23 m/s, zipper nodes. | **Track 1:** reproduce first, to validate the whole pipeline on a known-positive case |
| **DRL that harmonises in the field** | CIRCLES 100-AV I-24 deployment, Lichtlé, Jang, Vinitsky, Shah, Lee & Bayen 2025, IEEE (IEEE doc. 10858625) [BAIR blog only, VERIFY]. The policy sees the AV's own speed, the leader's speed and the gap, and outputs an acceleration *or a desired speed* for the car's cruise control. Trained on replayed I-24 trajectories. The blog reports "15 to 20 % of energy savings around our controlled cars". Field-validated non-RL controllers: Stern et al. 2018, TR-C 89:205–221 [VERIFY the controller names and parameters in the full text]. | **Track 3:** TM21 CAV speed harmonisation, hybrid = DRL sets the set-point of a field-tested controller |
| **Honest prior for VSL against tuned controllers** | In microsimulation, direct RL beat a **tuned MTFC** by ≈ 1.6 %, or ≈ 9.7 % with ramp metering (Schmidt-Dumont & van Vuuren 2019). Published hybrids gain 1.5–6 % (screen §3). | **Track 2:** the thesis-core TM20 merge; we expect a small gap and test for it honestly |
| **Most room against SPECIALIST** | Macroscopic results: RL −23 % delay vs SPECIALIST and −12.4 % vs MPC (Han et al. 2022, computed from their numbers). In VISSIM, perfect-information control beat a tuned SPECIALIST by 3–19 % travel time (Malikopoulos 2019). | **Track 4:** moving jam waves |
| **TTS-type reward in a calibrated SUMO merge** | Li & Lasenby 2024, IEEE T-ITS 25(2), read: reward −TTS(k)/TTS_c, with a penalty for changes of 10 mph or more; 11 actions from 20 to 70 mph; capacity drop exhibited (Fig. 8). | R-TTS reward design |

**v5 failure modes this roadmap must make impossible** (screen §1–§2):
- a plant that never breaks down;
- a capped demand generator;
- arrivals sampled once every 30 steps;
- the insertion backlog ignored;
- a variance-proxy reward;
- no-control as the yardstick;
- checkpoints selected on the training pool;
- state leaking across resets.

## 2. Your issues, and where the roadmap handles each

| Issue you raised | How it is handled | Where |
|---|---|---|
| **Reward function** | The reward is the objective, made dense: r_t = −(vehicles in network + vehicles waiting to enter) × Δt, which sums to −TTS including origin queues. Variants: outflow (Vinitsky), a difference against a no-control reference run on the same seed (lower variance, same optimum), and a small change penalty. Every reward passes the **degenerate-policy screen** (score it for no-control, constant caps and a random policy) before use. | §8 R-axis |
| **Discrete data collection** | Three sensing levels are compared: E1 loops at 30 s (field-realistic), E2 area detectors updated every step, and CAV probe data at penetration p (TM21 vehicle situation data). The aggregation interval is a variant (10 / 30 / 60 s). | §8 S-axis |
| **"What data is really needed?"** | **D-check before any DRL:** on no-control and random-policy rollouts, fit a small classifier that predicts "breakdown within 5 min" from each candidate feature set. If no feature set predicts it better than chance in advance, anticipation is impossible and DRL cannot beat reactive feedback on that plant. An **oracle-state** variant (true hidden condition) bounds the value of information. | §7 R1, §8 |
| **Discrete actions** | Variants: absolute discrete limits; **incremental Δ ∈ {−10, 0, +10} km/h with action masks** (the rate limit is built in, `MaskablePPO`); continuous actions quantised at the sign; hybrid parameters (MTFC set-point, FollowerStopper set speed); a bounded residual on MTFC. | §8 A-axis |
| **Lag between action and effect** | **Measured, not guessed:** a T0 step-response test per plant (dead time and time constant from a VSL change to the bottleneck flow). That sets the decision interval, a discount γ whose horizon is ≥ 3 × (dead time + time constant), the history length (frame stack), and whether `RecurrentPPO` is needed. Previous actions are always in the state. | §6, §8 T-axis |
| **Environment and SAR refactor** | A new `vsl_lab/` package: plant specs in YAML, generated configs (never hand-edited), a SAR registry with unit tests, controllers and envs separated. | §3 |
| **Silent failures (vehicles in ≠ vehicles out)** | Health checks at four levels (static, runtime checkpoints, end of run, across runs), plus golden-run regression and conservation identities. Each run is PASS / WARN / FAIL and nothing is silently dropped. | §4 |

## 3. Architecture (`vsl_lab/`, new code, v5 code untouched)

```
vsl_lab/
  plants/        YAML plant specs: geometry, vTypes, compliance, demand, detectors, VSL areas
  netgen/        spec → .net.xml / .rou.xml / .add.xml / .sumocfg (content-hashed; never hand-edited)
  sim/           libsumo runner (one sim per process; file names = all params + PID), health.py, metrics.py
  controllers/   NC, constant cap, MTFC (Carlson 2013), ALINEA/FB metering (Vinitsky 2018 form),
                 SPECIALIST (Hegyi 2008), FollowerStopper / PI-saturation (Stern 2018), later MPC
  envs/          gymnasium envs per plant; reset() rebuilds everything (no state leak)
  sar/           state / action / reward components (registry + unit tests + degenerate-policy screen)
  train/         SB3 / sb3-contrib launchers (PPO, MaskablePPO, RecurrentPPO, DQN/QR-DQN, SAC/TQC, TRPO)
  eval/          paired evaluation, median of paired differences, 95 % percentile bootstrap
  ops/           thermal-aware scheduler, sim-start gate, ledger, golden runs
  tests/         pytest: conservation, determinism, SAR screens, metric accounting
```

- **Environment:** `venv314` (SUMO / libsumo 1.27.1, SB3 2.8.0, CPU torch). Before every launch: `unset SUMO_HOME; export OMP_NUM_THREADS=1`, and `torch.set_num_threads(1)` per learner.
- **Run options:**
  - `--time-to-teleport 300`, with teleports counted;
  - `--collision.action warn` and `--collision.check-junctions false` (junction checks create artefact crashes, v6 lesson);
  - `--summary-output` and `--statistic-output` for cross-checks;
  - `--tripinfo-output.write-unfinished`.
- **Sensors:** `getLastInterval*` only. A unit test fails on any `getInterval*` call.
- **Storage:** raw runs in `/home/catalin/work/phd/vsl_lab_runs/` (ext4). Only summaries are committed (< 5 MB per file).

## 4. Health checks and checkpoints (the defence against silent failures)

**Static, before any run, for every new config hash:**
- **H-S1:** network and config load with 0 errors; every warning is listed.
- **H-S2:** the vehicles in the route files equal the generator's counts *exactly*, with 0 "no valid route" or "discarded" messages. This catches v5's swallowed-vType bug.
- **H-S3:** every detector lies within its lane length, IDs are unique, and the detector period divides the decision interval.
- **H-S4:** realised demand per route matches nominal within Poisson noise, and **no per-second insertion cap binds**. This catches v5's 3,600 veh/h truncation.

**Runtime checkpoints**, every 300 simulated seconds and at the end, using libsumo counters:
- **H-R1, conservation:** `loaded − departed − pending = 0` and `departed − arrived − running − removed = 0`, exactly.
- **H-R2, insertion backlog:**
  - log the pending count and the maximum insertion delay;
  - WARN if any vehicle waits more than 60 s to enter when the scenario does not intend an origin queue;
  - FAIL if the backlog grows without bound (entrance gridlock).
- **H-R3, teleports:** FAIL if there are any in plant-validation or evaluation runs; causes (jam / yield / wrong lane) are parsed from SUMO warnings.
- **H-R4, collisions and emergency stops:** collisions → FAIL. Emergency stops → WARN above a rate threshold, since they flag actuator abuse such as an abrupt limit drop.
- **H-R5, stuck vehicles:** speed < 0.1 m/s for more than 120 s at a lane end (e.g. the end of an acceleration lane) → WARN, or FAIL if persistent.
- **H-R6, numerics:** any NaN or infinity in observations or rewards → FAIL immediately.
- **H-R7, actuator:** the commanded limit equals `lane.getMaxSpeed`, on every controlled lane and every decision.
- **H-R8, detector consistency:**
  - between consecutive detector stations, inflow − outflow = Δstorage within tolerance over 5-min windows;
  - exit-detector counts match arrivals within ±2 %.

**End of run:**
- **H-E1, drain:** after demand ends plus a cool-down, `running = 0` and `pending = 0`. Otherwise WARN "unfinished N"; censored delays still count in the metric.
- **H-E2:** arrivals per destination equal generated vehicles per destination, exactly (after the drain).
- **H-E3:** the `--statistic-output` and `--summary-output` totals agree with the TraCI counters.
- **H-E4:** SUMO warning counts by category go to the ledger; any `Error` → FAIL.

**Across runs:**
- **H-X1, determinism:** 1 run in 50 is re-run in a fresh process and must give an identical summary hash.
- **H-X2, golden runs:** per plant, a fixed-seed no-control run whose hash is stored. A code or config change that alters it must be logged as intended; otherwise it is a regression.
- **H-X3, no cross-talk:** output names carry the PID, and no file is overwritten. Parallel route-file overwrites happened twice in v6.

**During training:**
- **H-T1:** per-episode health goes in `info`. A FAIL rate above 1 % stops the learner.
- **H-T2:** for R-TTS, Σ reward must equal −TTS / scale as recomputed from `--summary-output`, which catches reward-accounting bugs.
- **H-T3:** action-saturation share, policy entropy, explained variance and gradient norm are logged.

**Phase checkpoints** (go / no-go between phases) are in §7. A phase does not start until the previous checkpoint is green and committed.

## 5. Compute and thermal plan

- **Caps:** ≤ 100 worker processes, **and** CPU package (`coretemp` "Package id 0") **< 90 °C**.
  - On 2026-10-01 the v6 benchmark measured **96–100 °C at 32+ saturated libsumo workers** in the `performance` profile (`parallel_sweet_spot_20261001.md`).
  - So **temperature, not the 100-worker cap, will bind.** I expect about 16–24 concurrent simulations; R0 measures it.
- **Thermal guard** (`ops/thermal.py`):
  - polls the package temperature every 2 s;
  - at ≥ 88 °C for 10 s, it stops new launches and SIGSTOPs the lowest-priority job group;
  - below 82 °C it resumes (SIGCONT);
  - every launch decision is logged. A pause does not change results, because the simulation is not real-time.
- **Sim-start gate:** before each batch, check that the v6 Claude sessions are idle or finished, or that CPU load is below 15 %. On 2026-10-01 at 21:47 both v6 sessions were idle and the load was about 2.
- **Thermal calibration (R0.4):**
  - run 8 / 16 / 24 / 32 / 48 workers for 3 min each on the T1 and T2 plants;
  - record the steady temperature and simulation throughput;
  - set N_max as the largest N with a steady temperature ≤ 87 °C.
- **DRL layout:** L learners × E envs ≤ N_max (e.g. 2 × 12), with `torch.set_num_threads(1)`.
- **Run classes:**

  | Class | Purpose | Size |
  |---|---|---|
  | S (smoke) | health checks only | ≤ 5 min, 1 seed |
  | P (pilot) | variant screening (exploratory) | 100–150 PPO updates, 2 seeds |
  | F (full) | the only class reported as a DRL result | ≥ 500 PPO updates, 3–5 seeds; convergence check; final policy, or a checkpoint selected on validation seeds |
  | C (confirmatory) | thesis claim | frozen candidate, reserved seeds, run once |

## 6. Tracks

All tracks share the §4 health checks and the §9 criteria. In each, the controller family and baselines are fixed before any DRL run. Kill rules are in §12.

### Track 1: bottleneck reproduction (pipeline validation; most credible SUMO case)

- **Plant BN4:**
  - **geometry:** the Flow bottleneck (100 / 310 / 140 m with 4 lanes, 280 m with 2 lanes, 155 m with 1 lane; zipper merges; 23 m/s);
  - **humans:** IDM, desired speed ~ N(limit, 20 %), lane changing disabled as in the paper;
  - **AVs:** 10 %.
  - **Variant BN4-L:** lane changing enabled (LC2013), to check robustness.
- **Plant checks:**
  - **T1:** an inflow sweep of 400–2,500 veh/h in steps of 100, 10 seeds each (210 runs, minutes of compute). PASS if outflow at the highest inflows is ≤ 0.95 × the peak outflow, with 0 teleports and the conservation checks PASS.
  - **T0:** a step-response test of the AV speed limit to bottleneck outflow, recording dead time and time constant.
  - **T3:** determinism.
- **Baselines (tuned on tuning seeds):**
  - no-control (NC);
  - constant AV caps (grid);
  - feedback metering of the Vinitsky form, with the published T = 30 s, K_F = 20, n_crit = 8 as the starting point of a grid;
  - **posted VSL with MTFC** for all vehicles (the TM20 variant).
- **DRL v1 (reproduction):**
  - S: density and mean speed per lane-piece, for all vehicles and for AVs; bottleneck outflow; previous action;
  - A: AV maximum speed per lane-piece;
  - R: outflow over 20 s;
  - algorithm: PPO with a frame stack, then `RecurrentPPO` (the paper used a GRU and TRPO; `TRPO` is available in sb3-contrib).
- **Success:**
  - the pipeline reproduces "RL ≫ NC at high inflow" (C1–C3, §9);
  - the honest comparison against tuned feedback metering and MTFC is reported, whatever it shows.
- **Reward variants next:** R-TTS including the entry queue, and R-diff.

### Track 3: TM21 CAV speed harmonisation (most credible field-proven DRL; fast plant)

- **Plant RING22:**
  - 22 vehicles on a ring of 230–260 m; Sugiyama / Stern setting [VERIFY the exact length from Stern 2018];
  - humans: IDM with noise;
  - 1 AV, i.e. about 4.5 %.
- **Plant OPEN:** a straight corridor fed by replayed wave-like leader trajectories (CIRCLES-style), with the AV share at 2–10 %.
- **Validated controllers:** the Stern 2018 controllers (FollowerStopper; PI with saturation), with parameters from the paper [read the arXiv 1705.01693 full text first].
- **Hybrid:** DRL sets the controller's command speed every 1–2 s, from its own speed, the leader's speed and the gap (the CIRCLES observation), plus optional downstream probe speed (TM21).
- **Direct:** DRL outputs an acceleration (Flow-ring style).
- **Metrics:**
  - primary: system mean speed, which is throughput on a closed ring, so a slow uniform ring is *penalised*;
  - secondary: wave amplitude (speed standard deviation), fuel (HBEFA4), and the minimum time gap.
- **Plant check T1:**
  - under NC, stop-and-go waves appear in ≥ 90 % of seeds (speed standard deviation above a threshold, periodicity);
  - FollowerStopper reduces speed standard deviation by ≥ 30 % without lowering mean speed by more than 5 %.

### Track 2: TM20 posted VSL at a merge (thesis core)

- **Plant MRG3:**
  - the `ramps_v2` geometry: 4 × 1 km with 3 lanes, an on-ramp with a 250 m acceleration lane, then 1 km;
  - VSL gantries every 500 m upstream;
  - Krauss or IDM humans, LC2013;
  - compliance classes as speedFactor groups;
  - demand rises, peaks and falls, calibrated so that NC breaks down in about half of the seeds.
- **Variant MRG-M25:** a geometry like Li & Lasenby's M25 J12 merge.
- **Plant checks:**
  - T0 and T1 exactly as in the screen (§6, Card A);
  - **if no capacity drop is found, Track 2 is killed in this plant.**
  - Calibration may use only one disclosed throw-away seed, within literature parameter ranges.
- **Baselines:** NC, constant caps, a **tuned MTFC** (Carlson 2013), and a delay-compensated MTFC when the information lag is part of the niche.
- **DRL v1:**
  - S: E1 30-s flow, speed and occupancy per segment, ramp flow and queue, previous action, history of 4;
  - A: incremental ±10 km/h per gantry with masks;
  - R: R-TTS including the insertion queue, as a difference against NC on the same seed;
  - algorithm: `MaskablePPO`.
  - Hybrid variants: MTFC set-point scheduling, and a bounded residual.
- **Honest expectation:** a small gap against tuned MTFC (prior ≈ 1.6 %). The niches worth testing:
  - detector aggregation and communication lag;
  - hidden compliance or driver mix;
  - **CAV probe data at low penetration**, which a loop-based MTFC cannot use but DRL can (TM21-style sensing for a TM20 actuator).

### Track 4: moving jam waves, SPECIALIST domain (later)

- **Plant COR10:** a 3-lane corridor of 8–14 km, near capacity, with perturbation-triggered jams.
- **Plant check:** T1b as in the screen (moving jams with reduced outflow in ≥ 50 % of seeds).
- **Comparators:** tuned SPECIALIST and an adaptive SPECIALIST.
- **DRL:** a hybrid (activation and parameters) and a direct version in the style of Han et al. 2022.
- **Started only if** T1–T3 leave capacity, or T2 is killed.

## 7. Phase sequence and checkpoints

| Phase | Content | Exit checkpoint (all must hold and be committed) | Estimate |
|---|---|---|---|
| **R0: infrastructure** | `vsl_lab/` skeleton, netgen, runner, health checks H-*, metrics (door-to-door delay including the queue), thermal guard, ledger, golden runs, unit tests | pytest green; on a smoke run (S class) of BN4 and RING22, every H-* check passes; the golden hashes are stored; the thermal calibration gives N_max | ~4–6 h of build; < 30 min of compute |
| **R1: plant validation** | T0 (step response → lag), T1 (mechanism), T3 (determinism) for BN4 and RING22, then MRG3; D-check (predictability of breakdown from each sensing level) | each plant marked PASS / KILL, with numbers and health logs; lag measured | ~1–2 h of compute |
| **R2: baselines** | grid-tune every baseline on tuning seeds for each surviving plant | frozen baseline table; best constant and best tuned controller per plant | ~1–2 h |
| **R3: DRL pipeline validation** | BN4 reproduction (v1 SAR): pilots, then a full run of 3 seeds; RING22 hybrid and direct | C1–C3 hold on validation seeds (§9). If not, debug the SAR before going wide. | ~3–6 h (depends on measured simulation speed) |
| **R4: variant search** | sequential screening of the §8 axes on the plant(s) where DRL learned; then MRG3 with the same pipeline | the ledger holds every variant; the 1–3 best candidates are frozen as configs and commits | rolling, hours to days |
| **R5: head-to-head (exploratory)** | frozen candidates vs tuned baselines on test seeds; paired median differences, bootstrap CIs; hybrid I/G/H numbers where relevant | report with every variant listed, including the losers | ~1 h per candidate |
| **R6: confirmatory** | one run on reserved seeds, with comparators and metric pre-registered | GO or KILL per candidate, as written | ~1 h |

**Order** (by credibility, then cost; your choice in §13):
1. **R0.**
2. **R1–R3 on BN4 and RING22.** They are small and fast plants; whichever trains first validates the pipeline.
3. **R1–R4 on MRG3**, the thesis core, using the validated pipeline.
4. **Track 4** only if there is capacity left.

While a track trains, the next plant is built (coding needs no CPU budget).

## 8. Variant axes (screened one axis at a time, then combined)

**Procedure per plant:**
1. Hold the other axes at their v1 values.
2. Screen each axis with P-class runs (2 seeds, 100–150 updates).
3. Keep the top 1–2 values.
4. Run the combined top configuration at F class (3–5 seeds, ≥ 500 updates).

Every run goes into the ledger.

| Axis | Values |
|---|---|
| **R** reward | R-OUT (outflow over 20 s) · **R-TTS** (−(N_net + N_queue)·Δt, i.e. −TTS including origin queue) · R-DIFF (R-TTS minus NC on the same seed; same optimum, lower variance) · R-TTS + small change penalty · terminal backlog penalty (stops delay being pushed past the horizon) |
| **S** state | S-E1 (loops, 30-s aggregates, field-realistic) · S-E2 (area detectors, every step) · S-PROBE (CAV probes at penetration p) · S-HIST (frame stack k = 4–8) · S-REC (`RecurrentPPO`) · **S-ORACLE** (adds the true hidden condition; an upper bound on the value of information) · S-MIN (bottleneck only) |
| **A** action | A-ABS (discrete absolute limits) · **A-INC** (Δ ∈ {−10, 0, +10} km/h, masks) · A-CONT (continuous, quantised at the sign; SAC / TQC) · A-HYB (MTFC set-point or FollowerStopper set speed) · A-RES (bounded residual on MTFC) |
| **T** timing | decision interval Δt ∈ {measured lag/2, 30 s, 60 s} for VSL, {0.5, 1, 2} s for Lagrangian control · γ chosen so that the horizon is ≥ 3 × lag · action hold |
| **Algorithm** | PPO (reference) · `MaskablePPO` · `RecurrentPPO` · DQN / QR-DQN · SAC / TQC · TRPO (to reproduce Vinitsky) · CrossQ (optional) |
| **Domain** | demand ±15 % · compliance mix · driver parameters · AV / CAV share; out-of-distribution test sets reported separately |

## 9. Success criteria, defined before any DRL run

- **C1, convergence:**
  - the validation return (on validation seeds) over the last 100 updates is within 2 % of its maximum;
  - the slope over that window is < 0.5 % per 100 updates;
  - value-function explained variance > 0.6;
  - entropy has stabilised;
  - all of this holds for every training seed; the curves are reported for every seed.
- **C2, not degenerate:** the policy is not a constant (its action variance exceeds a threshold), and it beats the **best constant cap** on validation seeds. This is the rule that would have caught v5.
- **C3, does something:** on validation seeds, the paired median improvement over NC **and** over the best constant cap is > 0, with the 95 % bootstrap CI excluding 0, and the primary metric is not worse on served throughput.
- **C4, health:** 0 FAIL runs in evaluation; ≤ 1 % WARN.
- **C5, the real bar (R5, then R6):** against the **tuned validated controller** (and, in the hybrid design, against best non-learning per `CLAUDE.md`). We report whatever comes out. "DRL ≈ tuned rule" is an honest engineering result. "DRL > tuned rule in niche X" is the target.

**Primary metric per track** (fixed now):

| Track | Primary | Co-headline / secondary |
|---|---|---|
| T1 and T2 | door-to-door delay including origin and insertion queue | served throughput |
| T3 | system mean speed (ring) or door-to-door delay (open road) | wave amplitude and fuel (secondary) |
| T4 | as T2 | — |

**Side constraints:**
- on-ramp users' delay ≤ +10 %;
- exposure-normalised safety proxy ≤ +5 %;
- 0 teleports.

## 10. Seeds (layout proposal: **needs your approval** before any run)

All seeds lie inside the block proposed in the screen (§8: 7,100,000–7,399,999), which does not collide with the v5 and v6 seed spaces. Track digit *t* ∈ {1, 2, 3, 4}.

| Role | Seeds |
|---|---|
| Throw-away calibration (one per plant, disclosed) | 7,1t0,000–7,1t0,009 |
| Plant checks T0 / T1 / T3, D-check | 7,1t0,010–7,1t0,099 |
| Baseline tuning | 7,1t0,100–7,1t0,299 |
| Validation (screening, checkpoint selection) | 7,1t0,300–7,1t0,499 |
| Test (exploratory head-to-head) | 7,1t0,500–7,1t0,699 |
| **Reserved confirmatory** | 7,1t0,700–7,1t0,999 |
| DRL training episodes | 7,2t0,000–7,2t9,999 |

## 11. Branches, ledger, reporting

- **Branches:**
  - `claude/vsl-lab-core` holds the infrastructure;
  - one branch per track: `claude/vsl-lab-t1-bottleneck`, `-t2-merge`, `-t3-ring`, `-t4-corridor`;
  - extra branches only where the code diverges (e.g. `…-t1-recurrent`); otherwise variants are configs.
- **Git:** run `git branch --show-current` before every push; push via SSH.
- **Committed:** `vsl_lab/runs/ledger.csv`, per-phase reports in `docs/lab/` and plots (each < 5 MB). Never raw runs.
- **Reporting to you:**
  - one short note at each phase checkpoint, plus anything surprising;
  - logs tailed at most every 10 minutes;
  - no raw JSON in chat.

## 12. Kill and stop rules

| Situation | Action |
|---|---|
| A plant fails T1 (no mechanism) | Kill the plant. Record the numbers; that is a non-DRL finding. |
| No DRL variant meets C1 + C2 after 3 SAR variants at P class on a plant that passed T1 | Stop that track and write up why. Debugging the SAR comes before widening. |
| DRL meets C3 but not C5 | Honest result. Then try the hybrid and niche variants (§6, Track 2 niches) before stopping. |
| Any FAIL from a health check during a phase | Stop the phase, fix it, re-run everything affected and log both outcomes (`CLAUDE.md`). |
| CPU ≥ 90 °C despite the guard | Halve N_max and log it. |

## 13. Decisions needed before R0 runs anything

1. **Approve the seed layout** in §10 (`CLAUDE.md` requires approval before use).
2. **Confirm the scope changes:** direct DRL allowed, exploratory DRL before a headroom gate, and caps of ≤ 100 workers and < 90 °C. If confirmed, I update `CLAUDE.md` to match.
3. **Thermal control:** worker throttling only, or may I also switch the power profile from `performance` to `balanced` during runs?
4. **Track order:** T1 + T3 first (recommended: credible and fast), or T2 (thesis core) first?
