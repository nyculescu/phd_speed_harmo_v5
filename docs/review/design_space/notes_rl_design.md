# Design-space notes: the RL design (v5 pipeline and `vsl_lab`)

*2026-10-04 · read-only audit of `phd_speed_harmo_v5` on branch `claude/vsl-lab-core` · input for the design-space heatmap*

**Conventions**
- `file:line` is relative to the v5 repo root. `docs_local/` means `/srv/shared/Workspace/phd/docs_local/`. `runs/` means `/home/catalin/work/phd/vsl_lab_runs/`, which is outside the repo. From `runs/` I read only `config.json`, `summary.json`, `val.csv` and `progress.csv`, and I report scalars only.
- **[CALC]**: I computed this in this session from repo or run files (Python only, no SUMO).
- **[INF]**: an inference that I did not check by running anything.
- **[VERIFY]**: a literature claim relayed from repo docs. I did not read the paper.
- Numbers without a tag are quoted from the cited repo document.

---

## 0. Key findings (TL;DR)

1. **v5 never had a controllable problem, and its RL design hid that.**
   - The evaluation demand generator caps mainline insertion at 1 vehicle/s, i.e. 3,600 veh/h (`tests/_sumo_helpers.py:123`), so NC never broke down (audit T3).
   - Four of the five v4 reward terms are speed-dispersion proxies (`sar_components/rewards/r44_reward_v4.py:113-152`).
   - The policy (TQC, Box(4), 100 % CAV) earned +221 reward over NC by slowing the merge to about 54 km/h. That cost **+23 % TTS** and −5.9 % sampled arrivals against NC (`docs/audit_2026-05-20_fresh_thread.md:74-90`).
   - A constant 60 km/h cap Pareto-dominated it (`docs/lessons_metric_gameability.md:26-35`).
2. **v5's SAC/TQC training was badly under-updated.** With 48 `SubprocVecEnv` workers and SB3's default `train_freq=1`, `gradient_steps=1`, each 1 M-step run made only **20,611 gradient steps**, an update-to-data ratio of about 1/48.
   - Verified in the seed logs: `n_updates 20611` in `training_runs/experiment_20260518_133246/tqc_box4_seed0.log` [CALC].
   - The 50 %-CAV evaluation curves are flat; the 100 %-CAV curves were still moving at 1 M steps [CALC, §4.1].
3. **The case for TQC was never tested at the paper's scope.**
   - It rested on an expected bimodal return in the "transitional regime" (`docs_local/sac_tqc_argument.md:186-193`), but evaluation never reached that regime.
   - The only TQC-vs-SAC data are at 50 % CAV. There TQC wins on the *proxy* reward: paired +14.7 [13.1, 15.8] per episode [CALC]. Seed-level means overlap, and the merge speed is slightly lower.
   - The CVaR evaluation (`sac_tqc_argument.md:195-207`) was never implemented (no `cvar` in any `.py`).
   - `vsl_lab` never ran SAC or TQC: `train_sb3.py:130` accepts them, but `:237-238` raises `NotImplementedError`.
4. **`vsl_lab` fixed the protocol:**
   - fixed seed roles;
   - validation-only checkpoint selection;
   - the door-to-door metric including the origin queue;
   - tuned baselines, MPC-F and a lookup oracle;
   - G/H gates, paired median differences with bootstrap CIs, a ledger and a run-once R6.

   Under that protocol, **every direct-DRL design lost or tied** against the best constant or tuned rule:
   - BN4 AV caps (10 % and 25 % AVs);
   - the ring (direct and FollowerStopper-hybrid);
   - the LD3 posted-VSL pilots P-H2 and P-H3.
5. **There is one confirmatory success, R6** (`docs/lab/t1_meter_r6.md`).
   - **Design:** a RecurrentPPO (LSTM 64) policy picks one of **4 pre-tuned settings of a validated feedback ramp meter** every **30 s**. Its reward is **−TTS including the origin queue**. The plant is BN4, with demonstrated headroom: G 15.4 %, H 20.4 % at q = 1,600.
   - **Result:** −4.3 % vs the event scheduler and −2.5 % vs MPC-F on 210 reserved seeds.
   - **Limits:**
     - the lookup oracle is still 5.8 % better;
     - the policy does not transfer out of distribution (surges +16 %);
     - its training did not meet the roadmap's C1 convergence rule: the final validation was about 11 % worse than the selected checkpoint [CALC];
     - the "learning-rate decay" in its protocol was not applied, because the RecurrentPPO path ignores it (`vsl_lab/train/train_sb3.py:229`) [CALC from code].

---

## 1. Observation spaces

### 1.1 v5 SAR state components (`sar_components/states/`)

| Component | Dim | Per-frame features | Sensor level | History | Static extras | Normalisation | Used by |
|---|---|---|---|---|---|---|---|
| `r44_state_v0` (`r44_state_v0.py:1-127`) | 38 = 3×12+2 | seg_0_before speed/flow/occ; seg_0_after speed/flow/occ; ramp_on_approach flow; ramp_on_merge speed; seg_1_after flow; regime one-hot (3) | E1 loops, 30 s aggregate, "exit" position (`core/env_interact.py:55, 660-681`) | 3-frame stack (90 s), zero-padded at reset (`:241-244`) | prev action (mainline, ramp), normalised to [0, 1] with the 60–130 / 40–90 bounds | /36.1 m/s, /8,000 veh/h, /100 % occ; clip to [0, 1] (`:303-304`) | ramps_v1, early |
| `r44_state_v1` (`r44_state_v1.py:1-144`) | 56 = 3×18+2 | v0 plus seg_2_before and seg_1_before speed/flow/occ | E1, 30 s | 3-frame stack | prev action (2), bounds 60–120 / 40–90 | same | `_common_config.yaml:21` default |
| **`r44_state_v2`** (`r44_state_v2.py:1-167`) | **77 = 3×24+5** | seg_2/seg_1 aggregate (6), **seg_0_before per lane L0–L2** speed/flow/occ (9), seg_0_after (3), ramp approach flow, ramp merge speed, seg_1_after flow, regime one-hot (3) | E1 per-lane, 30 s (`env_interact.py:700-712`) | 3-frame stack | prev action 4-D (`:157-161`) + **anomaly_active flag** (`:162`) | same, clip [0, 1] | **all 15 v5 experiments** (`configurations/per_lane_stochastic.yaml:75`) |

**Notes on the v5 state:**
- **Regime one-hot.** It comes from `core/regime_detector.py:287-292`: FREE ≥ 75 km/h, CONGESTED < 45 km/h, plus an occupancy override at 8 %. The thresholds are "calibrated for a 100 km/h free-flow network" (`:239`), but the network limit is 130 km/h (`core/constants.py:4`).
- **Partial observability.**
  - Loops only, so no queue or insertion-backlog feature, and no demand or time-of-day feature.
  - The anomaly flag gives the agent oracle knowledge that an incident is active.
  - At reset, prev-action features read 0, which encodes "60 km/h posted", not "no action" [INF].
- **Fallback never tried.** The design doc names RecurrentPPO as the fallback "if SAC/TQC fail to learn temporal selectivity after 500 episodes" (`docs_local/sac_tqc_argument.md:286`). It was never tried in v5. The plan lists it only as a "POMDP-safe option, lower priority" (`docs/plans/phd_thesis_plan_v0.md:187`).
- **Unused monitor.** `core/monitoring.py` (`HarmonizationMonitor`) hard-codes the 56-dim v1 layout (`:40-57`) and is not wired into `train.py` (callbacks at `train.py:344`) [CALC].

### 1.2 `vsl_lab` observations

| Env / mode | Dim | Features | Sensor level | Memory | Normalisation |
|---|---|---|---|---|---|
| **BN4 S-VIN** (`vsl_lab/envs/bn4_env.py:3-5, 158-183`) | 4 × 35 lane-pieces + 1 + n_prev. **AV caps: 163; meter_sched: 145** [CALC: edges with 4/4/4/2/1 lanes, `vsl_lab/netgen/bn4.py:26`; pieces 1/3/3/3/1, `bn4_env.py:30`] | per lane-piece: human count / jam capacity, human mean speed / 23, AV count / capacity, AV mean speed / 23; outflow over 20 s / 2,000; previous action (one-hot for meter_sched, `:362-365`) | **vehicle-level ground truth** (libsumo `edge.getLastStepVehicleIDs` + per-vehicle speed and position, `:164-174`), i.e. perfect area or probe data, not loops | optional `obs_stack` k (`:115, 148-156`; P-M3a used k = 4 → 580 dims); RecurrentPPO LSTM 64 (`train_sb3.py:226-231`) | fixed scaling, `Box(-1, 5)`, no `VecNormalize` (`:136`) |
| **MRG3 / LD3 S-HIST** (`vsl_lab/envs/mrg3_env.py:8-10, 92-109`) | 16 × hist (4) = 64, +1 with S-ORACLE | per edge (up3 … down): E1 30-s flow per lane / 2,400 and speed / 120; merge density (E2) / 60; ramp flow / 1,200; current b; time fraction | **E1 `getLastInterval*` + E2** (`vsl_lab/plants/mrg3.py:133-160`) | 4-snapshot history (`mrg3_env.py:176`) | fixed scaling |
| **RING22** (`vsl_lab/envs/ring_env.py:1-9, 49-53`) | 5 | AV speed, relative speed to leader, gap, 38-s mean AV speed, previous action | local AV sensing (CIRCLES-like) | 38-s running mean | fixed scaling |
| MPC-F features (comparator) | S-VIN + 120-s measured inflow + setting one-hot | same as DRL, plus inflow (`docs/lab/t1_meter_gscan_protocol.md:184-187`) | vehicle-level | none | standardised |
| Round 3 DRL-C (**planned, never run**) | — | per-lane loops, merge density, ramp flow, CAV probe means per lane and zone, last action | loops + probes | 4-step history | — (`docs/lab/round3_tm21_protocol.md:87-92`) |

**Partial-observability design in the one success.** The perturbation kind (none / slow / block / surge) and its timing are hidden (`bn4_env.py:309-317`). The policy must infer them from the vehicle-level state and its history. That is the stated niche (`docs/plans/vsl_drl_run_roadmap_v0.md:26-29`). The evsched and MPC-F comparators see comparable vehicle-level information (`vsl_lab/jobs/bn4_eval.py:87-95`; protocol `:184`).

---

## 2. Action spaces

### 2.1 v5 (`sar_components/actions/`)

| Component | Space | Mapping / actuation | Constraints | Decision interval |
|---|---|---|---|---|
| `r44_action_v0` (`r44_action_v0.py:1-64`) | Box([60, 40], [130, 90]) in **km/h** | mainline value to seg_0/1/2_before; ramp value to ramp_on_transition | clip | 30 s |
| `r44_action_v1` (`r44_action_v1.py:1-68`) | Box([60, 40], [120, 90]) | same | clip | 30 s |
| **`r44_action_v2` Box(4)** (`r44_action_v2.py:121-128, 200-216`) | Box(60…120 ×3, 40…90) | per-lane L0–L2 on seg_0_before; ramp; seg_1/seg_2 receive min(lanes) | **adjacent-lane gap ≤ 10 km/h** (`:54-66`) | 30 s |
| `r44_action_v2` Box(5) (`:111-120, 177-198`) | Box(4) + seg_1_before uniform | adds `edge.setMaxSpeed` on seg_1_before for **all** vehicles (`core/env_interact.py:525-530`) | step-down ≤ 16 km/h (`:51, 191`) | 30 s |
| `r44_action_v2` Box(7) (`:101-110, 140-175`) | per lane on seg_1 and seg_0, + ramp | — | lane gradient + step-down | 30 s, **never trained** (no experiment uses `use_box7`) [CALC] |

**Actuation detail.**
- Limits apply only to **CAVs**, via `traci.vehicle.slowDown(v, limit, 30 s)`, issued every **5 s** rather than every second (`env_interact.py:540, 582-587, 593-648`). The design doc says every 1 s (`docs_local/control_loop.md:103, 166`).
- CAVs are released past the merge (`env_interact.py:57-67`).
- HDVs are never actuated in Box(4).
- Box(5) applies the edge limit to all vehicles. The doc's "92 % HDV compliance" (`control_loop.md:107`) has no counterpart in the env code [CALC: no non-compliance logic in `core/` or `sar_components/`].
- NC in the v5 evaluation is not uncapped: it posts [120, 120, 120, 90] against a 130 km/h network (`evaluate_models.py:154-158`).

### 2.2 `vsl_lab`

| Env / mode | Space | Mapping | Rate limits / safety | Decision interval |
|---|---|---|---|---|
| BN4 `av_caps` (`bn4_env.py:123-125, 190-212`) | Box(22) in [−1, 1] | AV max speed per controlled lane-piece. `linear`: [1, 23] m/s. **`nocap_center`**: a ≥ 0 → no cap (`:195-197`) | cap change −1.5 dt / +1.0 dt; no AV asked to brake > 1.5 m/s² | **1 s** (default `decision_s`, `:67`) |
| BN4 `posted_vsl` (`:126-128, 214-221, 356-360`) | Box(2) | b per gantry (edges 2, 3), all vehicles | b ∈ [0.2, 1], \|Δb\| ≤ 0.2 | 10 s in eval (`bn4_eval.py:43-44`); **no DRL run** (A-T0 FAIL, `docs/lab/STATUS.md:24`) |
| **BN4 `meter_sched`** (`:129-131, 228-238, 361-365`) | **Discrete(4)** (`allow_off=false`), or Discrete(1 + grid) | chooses (K_F, n_crit) of the Vinitsky feedback meter (`:36-60`). R6 grid = {40:6, 40:8, 20:12, 5:8} = the q = 1,600 lookup settings (protocol `:92`) | the meter's own 30-s update and 6-s green | **30 s** |
| MRG3 `direct` (`mrg3_env.py:78-80, 193-196`) | Discrete(9): b ∈ {0.2 … 1.0} | posted VSL with the Carlson staircase (`:85-90`) | \|Δb\| ≤ 0.2 per period | **60 s** |
| MRG3 `direct_fine` (P-H2) (`:189-192`) | Discrete(11): b ∈ {0.5, 0.55 … 1.0} | contains the tuned const 0.75 | \|Δb\| ≤ 0.2 | 60 s |
| MRG3 `hybrid` (`:197-200`) | Discrete(7): MTFC density set-point ρ̂ ∈ {14 … 32} | Carlson MTFC computes b | set-point changes every 5 periods | 60 s / 300 s; **not trained** [CALC: no run config uses it] |
| MRG3 `residual` / **`residual_c`** (P-H3) (`:181-186, 201-205`) | Discrete(5) ±0.2 / **Box(1)** | b = clip(0.75 + 0.25a, 0.5, 1) around the frozen const 0.75 | \|Δb\| ≤ 0.2 | 60 s |
| Ring `hybrid` (`ring_env.py:3-4, 42-43`) | Box(1) | FollowerStopper command speed U ∈ [0, 10] m/s; FS drives at 0.1 s | AV safety shield (`docs/lab/r3_pilots_protocol.md:97`) | 1 s (P2b), 2 s (P2c), 5 s (P2d) |
| Ring `direct` | Box(1) | AV acceleration ∈ [−1, 1] m/s² | shield added after P3 collisions | 0.5 s |
| Round 3 DRL-C (**planned only**) | MultiDiscrete(6 × 8) | lane × zone CAV targets {50 … 120} km/h | 1 km/h staircase (`vsl_lab/controllers/cav_staircase.py:1-10`) | 30 s |

---

## 3. Reward functions

### 3.1 v5 rewards (`sar_components/rewards/`)

| Version | Terms (formula; file:line) | Default weights | Notes |
|---|---|---|---|
| v0 (`r44_reward_v0.py`) | r_v = −min(((v_seg0_after − 80)/80)², 1) (`:56-63`); r_q = min(q_seg1_after / 5,000, 1) (`:68`); r_a = −clip(‖Δa/range‖, 0, 1) (`:79`) | 0.50 / 0.35 / 0.15 (`:41-43`) | "MARVEL structure" [VERIFY]. Wrong location: the merge zone never breaks down (`sac_tqc_argument.md:43-52`) |
| v1 (`r44_reward_v1.py`) | r_harmo = −min(σ(s2, s1, s0)/30, 1); below a 50 km/h floor, −1 + v̄/50 (`:77-83`); r_q as v0 with ref 6,000; r_a | 0.55 / 0.30 / 0.15 | σ over 3 points is "degenerate" (`sac_tqc_argument.md:356-361`) |
| v2 (`r44_reward_v2.py`) | r_spatial = −min(max adjacent \|Δv\|/30, 1) with the speed floor (`:150-163`); r_temporal = −min(\|Δv_seg0_after\|/15, 1) (`:169-178`); r_harmo = 0.5·spatial + 0.5·temporal; r_q = 0 if q/q_ref ≥ 0.85, else linear (`:186-195`); r_a | 0.55 / 0.30 / 0.15 (`_common_config.yaml:32-35`) | throughput is a **dead zone** above 85 % |
| v3 (`r44_reward_v3.py`) | v2 + r_lane_grad = −min(max lane gap / 20, 1) (`:154-158`) + r_merge = −min(\|v_L0 − v_ramp\|/30, 1) (`:160-163`) | 0.40 / 0.25 / 0.10 / 0.15 / 0.10 (`:67-71`) | described in `control_loop.md:143-157` as current, but **not** the v4 used in training |
| **v4** (`r44_reward_v4.py`) | r_harmo = −min(((σ_seg + σ_lane)/2 / 5)², 1) (`:113-117`); r_temporal = −min((\|Δv_ds\|/8)², 1) (`:124`); **r_throughput = clip(q/6,000 − 1, −1, +0.1)** (`:135`); r_lane_eq = −min((max lane gap/15)², 1) (`:141`); r_smooth = −min((‖Δa/range‖/0.5)², 1) (`:144-152`); total × **5** (`:162`) | w_h 0.35, w_t 0.20, w_q 0.25, w_l 0.15, w_s 0.05 (`per_lane_stochastic.yaml:95-100`) | 4 of 5 terms are dispersion proxies. **No delay, TTS or served-throughput term.** The header says "10×" and "merge term"; the code has neither (`:21-23` vs `:69`) |

**v4 weight ablations** (all TQC Box(4), 100 % CAV, 5 seeds; `docs/experiment_catalog.md:77-87`):

| Variant | (w_h, w_t, w_q, w_l, w_s) |
|---|---|
| base | 0.35, 0.20, 0.25, 0.15, 0.05 |
| no_smoothness | 0.37, 0.21, 0.26, 0.16, 0 |
| no_throughput | 0.47, 0.27, 0, 0.20, 0.06 |
| no_temporal | 0.44, 0, 0.31, 0.19, 0.06 |
| no_lane_eq | 0.41, 0.24, 0.29, 0, 0.06 |
| no_harmonization | 0, 0.31, 0.38, 0.23, 0.08 |
| harmo_pure | 0.70, 0, 0, 0.30, 0 |
| throughput_heavy | 0.20, 0.10, 0.55, 0.10, 0.05 |
| uniform | 0.2 × 5 |

**Gameability findings:**
- **Ablation result.** All 9 weightings land within about 2 % of each other on every non-gameable KPI, and all are about 23 % worse than NC on TTS (audit `:72-98`). The reward was mis-*specified*, not mis-weighted (audit Claim 5, `:141-142`).
- **The throughput term did not move:** r_throughput was −0.229 for NC and −0.223 for TQC (audit `:142`).
- **`lane_sigma` is monotone in posted speed:**

  | Policy | NC | M110 | M90 | M70 | M60 | DRL |
  |---|---|---|---|---|---|---|
  | `lane_sigma` | 17.65 | 15.58 | 12.69 | 4.64 | 3.59 | 1.61 |

  It is a slow-traffic detector (audit T2 `:51-62`).
- **Low-dimensional dispersion proxies are cheap to game.** `core/monitoring.py:8-13` records the per-step reward gap between "do-nothing" and "temporally selective" as about 0.007, which a noisy critic cannot see.
- **The deliberate TTS exclusion.** `docs_local/sac_tqc_argument.md:483-492` chose flow over TTS, "TTS is reported … not used in the reward". Training-time `tts_increment_s` counted vehicles in the network only (`env_interact.py:714-719`).
- **The five-test screen** (constant policy, degenerate extremes, decoupling, tautology, exposure) is in `docs/lessons_metric_gameability.md:61-75`.

### 3.2 `vsl_lab` rewards

| Reward | Definition | Where | Proxy or objective | Finding |
|---|---|---|---|---|
| R-OUT | outflow over the last 20 s / 2,000 per decision | `bn4_env.py:374-375` | proxy (Vinitsky's) | BN4 AV caps learned ≈ NC (F1, F2). A small validation (6 episodes) produced false-positive screening passes (`docs/lab/r3_pilots.md` F1 section) |
| **R-TTS** | −(Δ veh-s in network + origin queue)/Δt/200 | `bn4_env.py:376-377`; queue counted in `vsl_lab/sim/runner.py:138-141` | **objective** (sums to −TTS incl. queue) | used by P1f and by all P-M meter-scheduling runs, **including R6** |
| R-TTS + stops | −(veh-s in system + 40·new stops)/30,000 per 60-s decision | `mrg3_env.py:111-131, 212` | objective + stop proxy, w fixed from the T-H frontier (`round4_harmonisation_protocol.md:73-74, 132`) | P-H2: J 342.7 vs const 0.75 at 310.1 (FAIL) |
| Ring speed − α\|a\| | mean speed/5 − α·mean\|a_AV\| | `ring_env.py:106` | objective on a closed ring + proxy | with α = 0.1, the |a| penalty traded against speed (`r3_pilots_protocol.md:77`); α = 0 still FAIL (lag) |
| Planned but never run | R-DIFF (vs NC on the same seed), change penalty, terminal backlog penalty | `docs/plans/vsl_drl_run_roadmap_v0.md:273` | — | — |

---

## 4. Every DRL algorithm and configuration tried

### 4.1 v5: SAC and TQC (SB3 / sb3-contrib), `train.py`

**Common settings** (`configurations/per_lane_stochastic.yaml:102-135`; `train.py:288-330`):
- **Hyperparameters:**
  - lr 3e-4, buffer 500k, learning_starts 10k, batch 256, τ 0.005, γ 0.99;
  - automatic entropy, MLP 256×256;
  - TQC: 25 quantiles, **5 critics**, drop the top 2 per net.
  - The design doc's table says buffer 200k and 2 critics (`docs_local/sac_tqc_argument.md:519-534`). The code differs.
  - `train_freq` and `gradient_steps` are not set, so SB3's defaults apply.
- **Environment:** 1 M steps per seed (999,360), 48 `SubprocVecEnv` workers, socket TraCI (`launch_training.sh:85`). The 5 seeds of an experiment ran concurrently, giving 240 SUMO processes per VM (`:217-231`).
- **Checkpoint selection:**
  - `EvalCallback` every 50k/48 vec-steps, 10 episodes, deterministic, `best_model` saved (`train.py:257-282`);
  - **the eval env reads the same training scenario pool** (`:258-260`);
  - `evaluate_models.py` prefers `best_model` over `final_model` (`:114-117`).
- **Budget per seed:** about 8,300 episodes of 120 decisions; **20,611 gradient steps** (seed log) [CALC]; 25–33 fps; **494–819 min wall-clock** (seed-0 logs) [CALC].

| Experiment (`training_runs/…`) | Algo / action | CAV | Reward | Eval reward (30 eps × 5 seeds) vs NC | Real KPIs | EvalCallback curve [CALC] |
|---|---|---|---|---|---|---|
| `20260516_094221` | SAC Box(4) | 50 % | v4 base | −335.1 vs NC −406.0 [CALC] | not logged in this eval | flat: first-5 mean −358…−362, last-5 −357…−363 |
| `20260516_094738` | **TQC Box(4)** | 50 % | base | −321.2 [CALC] | — | flat: −358…−362 → −354…−360 |
| `20260516_095013` | SAC Box(5) | 50 % | base | −343.7 | — | flat |
| `20260516_095542` | TQC Box(5) | 50 % | base | −335.2 | — | flat |
| `20260517_174654` | TQC Box(4), reproduction | 50 % | base | −323.6 (catalog `:108`) | — | flat |
| **`20260518_133246`** | **TQC Box(4)** | **100 %** | base | **−164.8** vs NC −386.2, M60_active −204.9 (`reports/2026-05-20_full_matrix/experiment_20260518_133246_kpi.md:11-26`) | **TTS 270.5 vs NC 220.0, M60_active 257.2, `diff_aggressive_active` 214.2 veh·h**; sampled arrivals 145.2 vs 154.3; merge 54.7 vs 85.3 km/h [CALC from `evaluation_20260521_095745`, matching audit `:74-90`] | rising: −319…−325 → −267…−279; best −251…−263 at 0.6–0.8 M; final below best |
| `20260518_133504` | TQC Box(4) | 100 % | harmo_pure | −196.6 | about +23 % TTS vs NC (audit `:82`) | noisy, 4× seed spread |
| `20260518_144123` | TQC Box(4) | 100 % | no_smoothness | −172.9 | same band | rising |
| `20260518_142808` (3 seeds, retired) and `20260519_100431` | TQC Box(4) | 100 % | no_throughput | — | same band | rising |
| `20260519_102240` / `102247` / `102845` / `103431` / `104158` | TQC Box(4) | 100 % | no_temporal / no_lane_eq / throughput_heavy / no_harmonization / uniform | — | all within 1.21–1.75 `lane_sigma`, TTS 269–274 (audit `:82`) | rising |

**Other v5 facts:**
- **Algorithms never trained in v5:** PPO and RecurrentPPO (listed in `sac_tqc_argument.md:507-515`, rejected in plan ADR-003 `:187`), and QR-DQN.
- **QR-DQN (7 discrete levels) was the v4 lineage** that "failed after 3 years" (`sac_tqc_argument.md:9-15`; v4 is not in this repo) [VERIFY].
- **Convergence was never checked** (`docs/plans/vsl_hybrid_screen_v0.md:64`).
- **Best-seed selection:** `--best-seed-only` picks by the final `evaluations.npz` entry, which comes from the training pool (`evaluate_models.py:486-505`).

### 4.2 `vsl_lab` (`vsl_lab/train/train_sb3.py`)

**Trainer** (`train_sb3.py:126-347`):
- **Algorithms:** PPO, RecurrentPPO (`MlpLstmPolicy`, LSTM 64) and TRPO. SAC/TQC raise `NotImplementedError`.
- **Policy network:** tanh MLP (`:212`).
- **Training loop:** `model.learn` one update at a time.
- **Validation:** on fixed validation seeds every `val_every` = 25 updates; `best_val_model.zip` is selected on validation only, and `final_model.zip` is also saved (`:292-320`).
- **Health stop:** stops on a FAIL share above 1 % (later configurable).
- **Seeds:** training pools 7,2t0,000 + 2,000·seed (`:163-165`).
- **Run records:** every run is appended to the ledger (`:334-341`).
- **Defects found (both from code, [CALC]):**
  - **lr decay is wired for PPO only.** RecurrentPPO and TRPO always run constant lr (`:213-217` vs `:229, :235`). The decay code was added on 2026-10-02 (commit c357a8f); the RecurrentPPO line dates from 2026-10-01 (bb6decd) per `git blame`.
  - Learner seed 5 trains on 7,220,000–7,221,999, which lies inside the **Track-2 DRL range** (roadmap §10 `:318`). Harmless across plants, but it breaks the approved layout.

| Run (tag; ledger row) | Plant / actuator | Obs | Reward | Algo + hyperparameters | Budget | Wall-clock [CALC from `runs/…/summary.json`] | Checkpointing | Outcome |
|---|---|---|---|---|---|---|---|---|
| P1 (`p1_bn4`; 31) | BN4, 10 % AV, 22 AV caps, linear map, Δt 1 s | S-VIN | R-OUT | PPO 8×225 (1,800 per update), batch 300, 10 epochs, lr 3e-4, γ 0.99, λ 0.95, 128×128 | 150 updates, 270k steps | 3.3 min | val 2 seeds × 3 q (6 episodes) | FAIL: 961 → 976 veh/h vs NC 992, const 1,054; entropy barely moved (`r3_pilots_protocol.md:57-61`) |
| P1b (43) | same | same | R-OUT | PPO, log-std −1 | 600 updates | 12.9 min | same | FAIL (≈ 950–985) |
| P1c (42) | `nocap_center` map | same | R-OUT | PPO, log-std −0.5 | 600 | 12.6 | same | screening PASS (1,095), later a false positive |
| P1d (46) | linear | same | R-OUT | **TRPO** | 400 | 9.6 | same | pass on best-val (1,155); final 1,015 |
| P1e (47) | `nocap_center` | same | R-OUT | **RecurrentPPO** LSTM 64, log-std −0.5 | 400 | 30.0 | same | FAIL (986 vs NC 992) |
| P1f (50) | `nocap_center` | same | **R-TTS** | PPO, log-std −0.5 | 600 | 12.5 | same | FAIL (final 915) |
| **F1** (52-54), 3 seeds | P1c config | S-VIN | R-OUT | PPO 8×225 | 1,000 updates × 3 | 23 min each | val 9 episodes | 0/3 pass. **R5 test** (7,110,500-529): +8.6 % worse than NC at q = 1,200, ≈ NC elsewhere (`r3_pilots.md`; `docs/lab/r5_f1_final.md`) |
| **F2** (67-69), 3 seeds | same | same | R-OUT | PPO 16×450 = 7,200 per update, batch 900, lr decay | 1,000 × 3 (7.2 M steps) | 46 min each | same | stable but ≈ NC (±0.3 % congested, +1.5 % at 1,200) → "authority" explanation (`r3_pilots_protocol.md:127-129`; `docs/lab/r5_f2_final.md`) |
| P6 / **BF** (87-97) | BN4 **25 % AV** | S-VIN | R-OUT | F2 config | 600 / 1,000 × 3 | 48.5 / 66 min each | val 9 episodes | B-R5: beats `cap:18` in **0 of 3** congested cells; vs NC only at q = 1,600 (−2.3 %); the meter is 50–72 % better (`docs/lab/r5_bf_av25.md:49-63`) |
| P2 (37) | RING22 hybrid (FS U) | local, 5-D | speed − 0.1\|a\| | PPO 8×150, 64×64 | 150 | 1.9 | val 3 seeds × 2 L | FAIL: speed 3.85 → 3.55 (reward–metric misalignment) |
| P3 (39) | ring direct accel, 0.5 s | same | same | PPO 8×300 | 13 (health stop) | 0.3 | — | 55 collision FAILs → shield added |
| P2b / P3b (62, 64) | hybrid / direct + shield | same | speed only | PPO | 600 | 7.3 / 9.7 | same | FAIL; P2b sets U = 7.5–8.3 m/s ≫ v_e ("action→effect lag", `r3_pilots_protocol.md:132-134`) |
| P2c / P2d (72-77) | hybrid, U held 2 s / 5 s | same | speed | PPO, γ 0.995, λ 0.99 | 600 | 22.1 / 15.4 | same | FAIL: collapse to the maximum set-point; PI-saturation at the ceiling (ledger row 77) |
| P-H (95) | LD3 posted VSL `direct` Discrete(9), 60 s | S-HIST 4 | R-TTS + 40·stops | PPO 16×120, batch 480 | abandoned at 10/500 (260 s per update) | — | — | abandoned; the grid lacked b = 0.75 (`round4_harmonisation_protocol.md:186-193`) |
| **P-H2** (100) | LD3 `direct_fine` Discrete(11) | S-HIST 4, p_nc hidden | R-TTS + stops | PPO 16×120 (1,920 per update), batch 480, lr decay, γ 0.99 | 500 updates (960k decisions) | **807 min** | val `score_h`, 2 cells × 3 seeds | FAIL: J 342.7 vs const 0.75 at 310.1, MTFC 322.3, NC 359.4; best-val ≈ NC (`docs/lab/round4_pilots.md`) |
| P-H3 (102) | LD3 `residual_c` Box(1) around const 0.75 | same | same | PPO 14×120, log-std −1 | abandoned at 382/500 | — | val degraded 1.222 → 1.39–1.44 | abandoned (energy); G on LD3 = 0.38 % |
| P-M (110) | BN4 `meter_sched` Discrete(4), 30 s, perturbation mix | S-VIN | R-TTS | PPO 16×60 (960), batch 240, lr decay | 2 updates (health stop) | 0.1 | val 12 episodes | VOID: it screened an untrained policy (`t1_meter_gscan_protocol.md:112-114`) |
| P-M2 (112) | same | S-VIN | R-TTS | same, max-fail 5 % | 500 | 15.4 | 12 episodes | FAIL: +0.1 % vs evsched; validation shows no learning (16.0 → 17.4) |
| P-M3a (115) | same | **S-VIN × stack 4** (580-D) | R-TTS | PPO | 1,000 | 48.5 | 12 episodes | FAIL: +3.5 % (final), −2.1 % (best), n.s. |
| **P-M3b** (116) | same | S-VIN | R-TTS | **RecurrentPPO** LSTM 64 (constant lr, see the defect above) | 1,000 | 57.5 | 12 episodes | **PASS: −9.6 % vs evsched [−40.8, −6.7] s** on 50×4 seeds; 1 PASS out of 8 looks (`t1_meter_gscan_protocol.md:142-155`) |
| P-M3c (114) | same | S-VIN | R-TTS | plain PPO | 1,000 | 47.6 | 12 episodes | FAIL (+2.6 %), validation not learning |
| PMF s1, s2 (120-121) + P-M3b as s0 | same | S-VIN | R-TTS | RecurrentPPO | 1,000 × 3 | 47 each | 12 episodes | **R5-M: NO.** Pooled −1.0 % vs evsched and −0.5 % vs MPC-F, both n.s.; only s0 beats both (`docs/lab/t1_meter_r5.md`) |
| **P-M4** s3, s4, s5 (127-129) | same | S-VIN | R-TTS | RecurrentPPO 16×120 (1,920 per update), batch 480 | **2,000 × 3** (3.84 M decisions each) | 213–240 min each | **40 episodes** (7,110,400–409 × 4 kinds) | **R5-M2: NO.** Pooled −2.7 % vs evsched (n.s.), −4.7 % vs MPC-F (only 1/3 learners significant) (`docs/lab/r5m2.md`) |
| **R6** (132) | frozen P-M4 s3 best-val (SHA-256 d855ba4c…) | — | — | — | run once (`vsl_lab/jobs/t1_meter_r6.py:40-43`) | — | — | **CLAIM YES:** −4.3 % [−14.7, −4.9 s] vs evsched; −2.5 % [−14.9, −0.8 s] vs MPC-F; +5.8 % vs lookup; −25.8 % vs NC; 210 seeds × 4 kinds (`docs/lab/t1_meter_r6.md`) |
| M2-R6OOD (137) | R6 policy on the Lead 1 mix | — | — | — | — | — | — | does not transfer: surge family +16.1 %; +0.3 to +4.1 % vs `mpcf_old` (`docs/lab/t1_meter2_h.md:71-99`) |

**Convergence of the R6 learners** (roadmap C1: final within 2 % of the maximum over the last 100 updates, EV > 0.6, entropy stable) [CALC from `runs/t1/train/pm4_bn4/*/val.csv`, `progress.csv`]:

| Learner | Validation `tts_system_ctrl_vehh` start → best (at update) → final | EV (last 100 updates) | Policy entropy (start → end) |
|---|---|---|---|
| s3 (**R6 candidate**) | 17.01 → **13.92 (1,600)** → 15.41 (**+10.7 %** vs best) | 0.85 | 1.31 → 0.22 nats |
| s4 (rerun) | 17.03 → 14.37 (650) → 15.51 (+7.9 %) | 0.84 | 1.32 → 0.16 nats |
| s5 | 16.70 → 14.68 (1,975) → 15.66 (+6.7 %) | 0.84 | 1.28 → 0.10 nats |

- The EV criterion passes.
- The "final within 2 % of best" criterion **fails for all three learners**.
- The policy entropy collapses to almost deterministic. ln 4 = 1.39 nats is the uniform 4-way policy.
- The R6 claim is valid as stated, because the frozen checkpoint was chosen on validation seeds, but training was **not converged** in the roadmap's sense.

---

## 5. Protocol evolution (v5 → `vsl_lab`)

| Dimension | v5 original | `vsl_lab` |
|---|---|---|
| **Plant validity** | assumed from demand parameters; NC never < 83 km/h in evaluation (audit `:100-112`) | T0 (actuator binds), T1 (mechanism / capacity drop), T3 (determinism); the realism gate R-a…R-d (`docs/lab/STATUS.md:36-52`); every plant is checked before any DRL run |
| **Demand, train vs eval** | train: pre-generated pool `shared_seed42_n200(_cav100)`, 200 scenarios (seed logs). Eval: on-the-fly generator, **capped at 3,600 veh/h mainline** (`evaluate_models.py:95`; `tests/_sumo_helpers.py:123`), with `insertionChecks="none"` (`:94, 152`) | per-episode seeded demand from `seed_pool`; validation and test use fixed `eval_seeds` (`bn4_env.py:300-305`); health check H-S4 for insertion caps (roadmap `:101`) |
| **Seed roles** | train pool = EvalCallback pool (`train.py:258-260`); eval seeds 99,000 + ep (`evaluate_models.py:401, 447`), never pre-registered | calibration / plant / tuning / validation / test / reserved per track (roadmap §10 `:306-318`); one disclosed breach (R5-M2 used 90 reserved seeds, `t1_meter_gscan_protocol.md:240-243`) |
| **Checkpoint** | `best_model` = best of 20 evals × 10 episodes **on the training pool** | best-validation on validation seeds only; the final policy is always reported too; validation grew from 6 to 40 episodes after false positives |
| **Primary metric** | proxy reward; KPIs `lane_sigma`, ds_flow; TTS/TT excluded from the KPI list (audit Claim 9) | **door-to-door time including the origin/insertion queue**, co-headlined with served throughput (roadmap `:25, :295-303`); drain until empty (`bn4_eval.py:3-6`) |
| **Metric accounting** | TTS = in-network vehicles × 30 s (`core/eval_metrics.py:207`): no insertion backlog; arrivals and hard brakes polled once per 30 s (`:230, :265`), i.e. ~1/30 sampled; depart time = first 30-s sighting (`:221`) | `SumoSim.tts_system` adds pending vehicles at each step (`runner.py:138-141`); conservation identities H-R1…H-E3 (`runner.py:8-15, 172-251`) |
| **Yardstick** | NC (itself capped at 120/90, `evaluate_models.py:154-158`) | NC + best constant + tuned validated controller + non-learning adaptive + MPC-F + lookup oracle (`CLAUDE.md` "best non-learning") |
| **Statistics** | means ± std over 30 episodes; no paired CIs (eval tables `evaluate_models.py:675-720`). The paired structure existed (same env_seed per policy) but was unused | median of paired differences, 95 % percentile bootstrap, 10,000 resamples (`vsl_lab/eval/stats.py:8-19`); "beats" = CI excludes 0, pooled **and** ≥ 2 of 3 learners (R5), single frozen candidate (R6) |
| **Pre-registration** | none; plan v0.6 conclusions drawn from a 4-of-9 subset (audit Claim 8) | protocol + addenda committed before each run; multiple looks disclosed (`t1_meter_gscan_protocol.md:138, 153-155`); R6 run-once marker + SHA assertions (`t1_meter_r6.py:40-43`) |
| **Gates** | none | **G** = (J_pool − J_lookup)/J_pool ≥ 10 % (`t1_meter_gscan_protocol.md:30-39`); **H** = median(J_NL − J_I)/median(J_NL) ≥ 10 % with paired CI lower bound > 0 (`:75-81`); the 2026-10-03 fix takes the minimum over non-learning arms (`STATUS.md:74`) |
| **Logging** | `experiment_catalog.md` (curated) | `vsl_lab/runs/ledger.csv` (136 rows incl. abandoned runs; `vsl_lab/ops/ledger.py`) |
| **Health** | collision count only (structurally 0, audit Claim 3) | H-S/H-R/H-E/H-X/H-T checks (roadmap §4); FAIL share as a side constraint; teleports reported |

### 5.1 Baselines that existed

| Baseline | v5 (`evaluate_models.py`) | `vsl_lab` (where) | Tuned? |
|---|---|---|---|
| NC | yes (`:154-158`; CAV cap 120/90) | all plants (`bn4_eval.py:66-67`, `mrg3_run.py`) | — |
| Constant cap | `M110_uniform`, `diff_mild` static (`:161-172, 526-530`) | BN4 `cap:<m/s>` (frozen `cap:18`), LD3 `const:b` (frozen 0.75), ring `fs:U` | grid on tuning seeds (`docs/lab/t1_bn4_r2_baselines.md`; `round4_r2.md`) |
| "Regime-aware" fixed (SPECIALIST-*style*) | M60…M110_active, `diff_mild_active`, `diff_aggressive_active`: post a constant while the regime one-hot says METASTABLE (`:405-416, 551-561`). Not SPECIALIST (`vsl_hybrid_screen_v0.md:63`). It probably **latches**: posting 60 drops speed below 75 → stays "metastable" (M60_active merge 60.5 km/h) [INF] | — | 6-level ladder, untuned |
| SPECIALIST | no | `vsl_lab/controllers/specialist.py` (Hegyi 2008/2009 [VERIFY]); `spec` on LD3 | variants (Round 4 Addendum B) |
| MTFC | no | `vsl_lab/controllers/mtfc.py` (Carlson 2013 [VERIFY]); LD3 `mtfc:36:38:9:0.0015`; BN4 `mtfcb` (posted) | grid (R2-H) |
| ALINEA-type feedback meter | no | Vinitsky FB meter `meter:K_F:n_crit` (`bn4_env.py:36-60`) [label "ALINEA-type" = my INF]; frozen `meter:10:6` | grid; **−45 % vs NC** on BN4 (`t1_meter_gscan_protocol.md:7`) |
| AV feedback (same actuator as DRL) | no | `avfb:K:n` (`bn4_eval.py:74-79`); frozen `avfb:2:10`. It is weak: its tuning score is 566 s, worse than NC (412) and `cap:18` (413); the meter scores 225 (`docs/lab/t1_bn4_r2_baselines.md:9, 27-28, 35`) | grid |
| Non-learning adaptive | no | `evsched:v:t:f` (event detection → lookup setting, `bn4_eval.py:87-100`); LD3 `vslad:θ:b` (`mrg3_run.py:135-140`); `madapt` / `msfix` (BN4 meter) | H1 grid of 27 (`t1_meter_gscan_protocol.md:64-66`) |
| MPC with a fitted model | no | **MPC-F** (`vsl_lab/jobs/mpcf.py`): MLP 2×64 predicting the 300-s veh-s cost; val R² 0.90 (`docs/lab/t1_mpcf_fit.json`); fitted on seeds 7,110,200–299 | frozen before R5-M |
| Oracle lookup I | no | per-(q, kind) best setting (`docs/lab/t1_meter_lookup.json`) | oracle, reported only |
| PI-with-saturation / FollowerStopper | no | `vsl_lab/controllers/pi_saturation.py` (Stern 2018 [VERIFY]) | grid |

---

## 6. Why distributional RL (TQC) was chosen, and the evidence

| Claim (source) | Status | Evidence |
|---|---|---|
| The "transitional regime is stochastic / bimodal", so quantile critics help (`docs_local/sac_tqc_argument.md:186-193`); v4's bimodal merge success/failure (`:11-15`) | **untested premise** | Evaluation never reached breakdown (NC 83–86 km/h, 1.3 % congested; audit `:100-112`), so there was no bimodality to exploit [INF] |
| CVaR risk-averse action selection (`:195-207`) | **never implemented** | no `cvar` in any `.py` [CALC]. SB3's TQC has an actor, not argmax over Z, so the described rule needs extra code [INF] |
| "TQC strictly supersedes TD3's overestimation motivation" (plan ADR-003 `:180-181`) | **never measured** | audit Claim 7 (`:147-148`) |
| TQC > SAC (catalog −321 vs −335, 50 % CAV) | **proxy only** | [CALC], episode-paired over 30 episodes, learner seeds pooled: TQC4 − SAC4 = +14.7 [13.1, 15.8] reward; TQC5 − SAC5 = +8.0 [5.6, 11.4]. Seed means overlap: TQC4 −316.5…−329.6 vs SAC4 −321.8…−353.4. TQC4 merge speed 56.7 vs 57.8 km/h, action std 9.8 vs 2.2 km/h. The CI ignores learner-seed variance. No TTS was logged in those CSVs. At 100 % CAV, TQC vs SAC is unmeasured |
| "Box(5) underperforms Box(4)" → ADR-014 | proxy only | TQC4 − TQC5 = +13.3 [11.0, 15.5] reward [CALC], same caveats |
| Off-policy sample efficiency (`sac_tqc_argument.md:161`) | **not realised** | UTD ≈ 1/48 (20,611 gradient steps per 1 M transitions) [CALC]. A UTD of 1/48 is far below typical SAC practice [INF] |
| `vsl_lab` follow-up | **none** | SAC/TQC not implemented in `train_sb3.py:237-238`; the roadmap A-CONT axis (`:275`) was never run |

**Verdict.** There is no evidence that distributional RL helped. The only measured TQC advantage is on a gameable proxy, and that proxy anti-correlates with TTS. The thesis-plan claim of "first TQC VSL" was judged a thin novelty wrapper (audit Claim 1, `:129-130`).

---

## 7. What the only success (R6) had that the failures lacked

| Factor | v5 TQC | T1 AV caps (F1/F2/BF) | Ring (P2–P3) | LD3 P-H2/P-H3 | P-M2 / P-M3a / P-M3c | **R6 (P-M4 s3)** |
|---|---|---|---|---|---|---|
| Headroom established before DRL | no (no breakdown) | no (meter ≫ any AV policy; const ≈ NC) | no (PI at ceiling, H ≈ 0) | **no** (G 0.38 %; `round4_gscan.md` G ≤ 4 %) | yes (same plant) | **yes: G 15.4 %, H 20.4 % [+18, +79 s]** (`t1_meter_h.md`) |
| Actuator authority | CAV slowDown; NC fine | weak (10 % / 25 % AVs, lane changing off) | 1 AV of 22 | posted VSL works (−25 % delay for const) but the constant is optimal | strong (meter −45 % vs NC) | strong |
| Action = choice over validated controllers | no (raw km/h) | no (22-D continuous caps) | FS set-point (hybrid) or accel | P-H3 residual on const 0.75 | yes (4 lookup settings) | **yes: Discrete(4) meter settings; meter always on** |
| Decision interval vs dynamics | 30 s | **1 s** (900 decisions per episode) | 0.5–5 s; credit horizon ≈ 20 s vs 30–60 s wave lag | 60 s | 30 s | **30 s** (= meter update period) |
| Memory | 3-frame stack (90 s) | none (P1e: LSTM, failed) | 38-s mean | 4 snapshots | none / stack 4 / none | **LSTM 64** |
| Reward = objective | no (variance proxies) | R-OUT (proxy); R-TTS in P1f | speed − α\|a\| (misaligned) | TTS + 40·stops | **R-TTS incl. queue** | **R-TTS incl. queue** |
| Train dist = eval dist | no (pool vs capped generator) | yes | yes | yes | yes | yes (q ~ U[1,400, 1,800], 4 kinds; eval q = 1,600) |
| Checkpoint validation size | 10 eps, training pool | 6–9 eps | 6 eps | 6 eps | 12 eps | **40 eps** |
| Budget | 20.6k gradient steps | 1,000 updates × 7,200 | 600 updates | 500 updates | 500–1,000 updates × 960 | **2,000 updates × 1,920 (≈ 3.8 M decisions), 3 learners, best-of-3 on validation** |

**Interpretation [INF].**
- The decisive differences are:
  1. a plant with measured, mechanism-driven headroom that depends on a **hidden, time-varying condition** (perturbation kind and timing);
  2. a **small discrete action set made only of validated controller settings**, so even a degenerate policy is competitive (the pooled fixed setting lies inside the action set);
  3. an objective-aligned reward;
  4. memory to infer the hidden condition.
- **The effect of memory is confounded.** Frame-stack PPO and plain PPO were tested only at the P-M3 budget (1,000 updates, 12-episode validation). The single-seed P-M3b pass was 1 of 8 looks, and R5-M (3 learners × 1,000 updates) was NO. Reliability came with P-M4's larger rollout, 2,000 updates and 40-episode validation.
- **The gain is modest and narrow:**
  - −2.5 % vs MPC-F, with the CI upper bound at −0.8 s;
  - +3.1 % worse than MPC-F under slowdowns;
  - most of the gain comes from blockages (`t1_meter_r6.md:18-27`);
  - no transfer to other severities and durations (`t1_meter2_h.md:96-99`).
- **Not done:** no policy-behaviour inspection of the R6 policy (setting-switch frequency, regime use) is in the repo. `vsl_lab/eval/inspect_bn4_policy.py` covers AV caps only.

---

## 8. Reusable vs must be rewritten

| Item | Verdict | Why |
|---|---|---|
| v5 SAR plugin pattern (`core/sar_frame.py`, `sar_components/registry.py`, `discovery.py`) | reuse the **pattern** | clean registry. But `RewardFunction` has no `reset()` (`sar_frame.py:126-146`) while `env.reset()` calls it (`env_interact.py:215`): v0/v1 rewards would raise [CALC from code, not run] |
| v5 `TrafficEnv` (`core/env_interact.py`) | **rewrite** | socket TraCI (~9.5 h per 1 M steps, `README.md:150`); CAV-only actuation; state leak (`_current_speed_limits_ms` survives reset, `:203-245, 502`); slowDown every 5 s; no queue metrics |
| v5 rewards v0–v4 | **discard as objectives** | fail the five-test screen; keep v4 components only as **reported secondary** diagnostics |
| v5 states v0–v2 | partial | E1 per-lane feature extraction is reusable. The regime one-hot thresholds need recalibration; add queue and backlog features |
| v5 `eval_metrics.py` `sumo_step()` accel/jerk (`:294-343`) | reuse as **secondary** metrics | per-step, artefact-filtered; TTS / arrivals / hard-brake parts must be replaced (1/30 sampling, no backlog) |
| v5 `evaluate_models.py` | rewrite | baselines are weak; means only; best-model-from-training-pool; hard-codes 4-D actions and `ramp_frac = 0` (`:241, 354`; the audit read that as "ramp sweep not exercised", which is a logging artefact [CALC]) |
| v5 `train.py` SAC/TQC config | reuse only as a **reference config** if A-CONT is ever tried | must set `gradient_steps` / `train_freq` for multi-env UTD; validation-pool checkpointing |
| `ScenarioManager` (`traffic_environment/scenario_pool.py`) | optional | per-worker shuffling is fine; superseded by seed-pool demand |
| `vsl_lab/train/train_sb3.py` | **reuse, with fixes** | fix lr decay for RecurrentPPO/TRPO; add SAC/TQC/MaskablePPO/QR-DQN if needed; fix the seed-pool formula for seeds ≥ 5; add an automatic C1 convergence report |
| `vsl_lab/envs/bn4_env.py`, `mrg3_env.py`, `ring_env.py` | reuse | fresh SUMO per reset; actuator asserts (H-R7); perturbation mix; hybrid / residual modes |
| `vsl_lab/sim/runner.py` (health, `tts_system` incl. pending, drain, identities) | **reuse as is** | the metric basis for the door-to-door primary |
| `vsl_lab/eval/stats.py`, `jobs/*_r5*.py`, `t1_meter_r6.py` | reuse | paired median + bootstrap; pooled and per-learner rules; run-once + SHA |
| Controllers (MTFC, SPECIALIST, PI-sat, FB meter, evsched, MPC-F, CAV staircase) | reuse | implemented from read papers per their headers [VERIFY each]; frozen tuned parameters in `docs/lab/*_frozen.json` |
| Ledger, thermal watchdog, scheduler (`vsl_lab/ops/`) | reuse | — |

---

## 9. Code-level defects and discrepancies found in this pass

1. **v5 UTD.** About 1/48: 20,611 gradient steps per 1 M transitions (seed log `n_updates`) [CALC].
2. **v5 doc vs code:**
   - TQC critics 5 (code) vs 2 (doc); buffer 500k vs 200k (`per_lane_stochastic.yaml:121-133` vs `sac_tqc_argument.md:519-534`);
   - slowDown interval 5 s (`env_interact.py:540`) vs "every 1 s" (`control_loop.md:103`);
   - reward in `control_loop.md:143-157` is v3, but training used v4;
   - v4 header "10× scale" and "merge term" vs code `_SCALE = 5` and no merge term.
3. **v5 Box(5).** The described 92 % HDV compliance is not implemented in the env [CALC].
4. **v5 `HarmonizationMonitor`.** Assumes the 56-D v1 observation and is not attached to training [CALC].
5. **v5 NC is not uncapped.** It posts 120/120/120/90 km/h to CAVs (`evaluate_models.py:154-158`).
6. **v5 evaluation routes use `insertionChecks="none"`** (`tests/_sumo_helpers.py:94, 152`). This can force unsafe insertions [INF].
7. **`vsl_lab` RecurrentPPO and TRPO ignore `--lr-decay`** (`train_sb3.py:213-217` vs `:229, :235`). The P-M3b / PMF / P-M4 protocols state "3e-4 with decay". The R6 candidate was trained at constant lr [CALC from code and `git blame`; not executed].
8. **`vsl_lab` seed pool.** Learner seed 5 (P-M4) drew training episodes from 7,220,000–7,221,999, the Track-2 DRL range (`train_sb3.py:163-165`; ledger row 128) [CALC].
9. **`vsl_lab` R6 learners did not meet roadmap C1** (final vs best +6.7 to +10.7 %) [CALC, §4.2].
10. **`vsl_lab` R6 per-kind rule.** "Significantly worse by > 5 %" is coded as point estimate > 5 % **and** CI lower bound > 0 (`t1_meter_r6.py:79-83`). That is a lenient reading, but it is the pre-registered code.

---

## 10. Design-space cells tried (heatmap input)

One row per tested cell. "Best NL" means the best non-learning comparator on the pre-registered metric. "—" means not reached.

| Plant | Actuator / action | Obs + memory | Reward | Algo | Δt | vs NC | vs best constant | vs best NL / tuned | Status |
|---|---|---|---|---|---|---|---|---|---|
| v5 ramps_v2, 50 % CAV | CAV per-lane slowDown, Box(4)/(5) continuous | E1 30 s, stack 3 | v4 proxies | SAC, TQC | 30 s | better on reward; TTS not logged | not compared | none existed | proxy "win", real KPI unknown |
| v5 ramps_v2, 100 % CAV | CAV per-lane, Box(4) | E1, stack 3 | v4 (9 weightings) | TQC | 30 s | **TTS +23 %** (worse) | worse than M60 / M70 on TTS | — | LOSS |
| BN4, 10 % AV | AV caps, Box(22) | vehicle-level S-VIN, none | R-OUT / R-TTS | PPO, TRPO, RecurrentPPO | 1 s | ≈ NC; +8.6 % at q = 1,200 | ≈ `cap:18` | DRL +62 to +98 % vs the tuned meter at q ≥ 1,600 (F1, `r5_f1_final.md`) | LOSS |
| BN4, 25 % AV | AV caps, Box(22) | S-VIN | R-OUT | PPO | 1 s | −2.3 % at q = 1,600 only | 0/3 cells | meter 50–72 % better | LOSS |
| BN4 | posted VSL Box(2) | — | — | — | 10 s | actuator does not bind (A-T0 FAIL) | — | — | not run |
| RING22 | FS set-point (hybrid) / accel (direct) | local 5-D | speed (− α\|a\|) | PPO | 0.5–5 s | worse than NC on validation | worse than fixed U | PI-sat at ceiling | LOSS |
| LD3 (EIDM / H5, 0.2 s) | posted VSL Discrete(11) | E1 + E2, hist 4 | TTS + stops | PPO | 60 s | J 342.7 vs NC 359.4 (better) | worse than const 0.75 (310.1) | worse than MTFC (322.3) | LOSS |
| LD3 | residual on const 0.75, Box(1) | hist 4 | TTS + stops | PPO | 60 s | — | validation degraded | — | abandoned |
| BN4 + perturbations, q = 1,600 | meter-setting scheduler, Discrete(4) | S-VIN, none / stack 4 | R-TTS | PPO | 30 s | −8 to −20 % | ≈ pooled | ≈ or worse than evsched | LOSS (screening) |
| **BN4 + perturbations, q = 1,600** | **meter-setting scheduler, Discrete(4)** | **S-VIN + LSTM 64** | **R-TTS incl. queue** | **RecurrentPPO** | **30 s** | **−25.8 %** | **−4.3 %** (pooled fixed) | **−4.3 % evsched, −2.5 % MPC-F; +5.8 % vs oracle** | **WIN (R6, narrow, in-distribution)** |
| BN4 Lead 1 mix (OOD) | same frozen policy | same | — | — | 30 s | — | +16 % on surges | +0.3 to +4.1 % vs `mpcf_old` | LOSS (exploratory) |
| MRG3 merge v1–v3, ZM3, CORR2, LD3 G-scan | — | — | — | — | — | — | — | realism / G gate killed before DRL | not run |
| Round 3 CAV arm C (MultiDiscrete) | planned | — | R-TTS | PPO | 30 s | — | — | parked (no CAV authority) | not run |

**Never tried anywhere:**
- SAC or TQC in `vsl_lab`;
- MaskablePPO with incremental ±10 km/h actions (roadmap A-INC);
- the DQN family (v4 only);
- R-DIFF reward;
- S-ORACLE for DRL (the env supports it, `mrg3_env.py:107-108`);
- E1-only observations for the BN4 meter (S-VIN is vehicle-level);
- the MTFC set-point `hybrid` mode on MRG3;
- posted-VSL DRL on any plant where G ≥ 10 %.
