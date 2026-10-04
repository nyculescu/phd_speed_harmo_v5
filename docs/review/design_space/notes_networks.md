# Design-space notes: networks, geometry, demand and scenarios (v5 pipeline + vsl_lab)

*2026-10-04 · read-only review of branch `claude/vsl-lab-core` (no simulation run, no repo file changed except this one) · input for the design-space heatmap*

**Conventions**
- Every fact cites `file:line` or `doc:line/section`. Line numbers are from this checkout.
- **[INF]** = my inference, not checked by running anything.
- **[CALC]** = recomputed by me from repo files with numpy only (no SUMO).
- **[VERIFY]** = literature or claims taken from repo docs that I did not check against the source.
- "Lab" = `vsl_lab/` (Oct 2026). "v5" = the original May 2026 pipeline (`core/`, `traffic_environment/`, `train.py`, `evaluate_models.py`).
- G = (pooled-best − per-condition-best) / pooled-best (an oracle, biased upwards). H = (best non-learning − informed lookup I) / best non-learning (CLAUDE.md "Method").

---

## 0. Key findings

1. **12 plant families were simulated** (3 in v5, 9 in the lab; the lab ones had 20+ driver/geometry variants). Only **two** showed an artefact-free, measurable capacity drop, and both drops come from **SUMO zipper nodes**:
   - BN4: 1,044 → 900 veh/h (ratio 0.862);
   - ZM3-H5: Q_dis/Q_ff 0.967.

   Every **acceleration-lane merge** either:
   - had no drop (ramps_v1 −0.4 %, MRG3-v1 0.976, W99 1.056, EIDM+lcAssertive 1.011), or
   - stranded ramp vehicles, causing teleports (IDM).
2. **Stop-and-go waves are easy to get and realistic in SUMO.** They travel at −14 to −20 km/h and start at the bottleneck, in every MRG3/LD3/ZM3 variant. So R-b passes for every model and does not discriminate between them.
3. **Controllable mechanisms in the evidence:**

   | Plant | Actuator | Result |
   |---|---|---|
   | BN4 | mainline signal meter | **−45 %** door-to-door |
   | BN4 under perturbations (slow / block / surge) at q = 1,600 | meter-setting **scheduling** | H = 20.4 %. The only R6 DRL claim: −4.3 % / −2.5 % |
   | LD3 | posted VSL | harmonisation: −55 to −63 % stops |

   On LD3 a single constant limit captures almost all of the benefit (G ≤ 4 %).
4. **No headroom:**
   - posted VSL on BN4 (does not bind);
   - AV caps at 10–25 %;
   - MRG3 posted VSL (T0 −3.9 %);
   - CORR2 ALINEA (G 0.4 %);
   - ring (PI-with-saturation at 100.2 % of the equilibrium ceiling).
5. **The v5 failure was mostly scenario generation:**
   - **Bernoulli cap.** One Bernoulli draw per second per route capped the evaluation mainline at 3,600 veh/h. [CALC] On the 30 evaluation seeds: nominal mainline 4,430 veh/h (median), realised at most 3,459; the cap binds in 77 % of seconds.
   - **Train/eval mismatch:** training used the flat 5,500–7,250 pool, evaluation the capped 3-phase generator.
   - **Ramp burst:** the pool writer packs 30–39 ramp vehicles into one second at t = 100 s.
   - **No insertion checks:** `insertionChecks="none"` everywhere.
   - **`ramp_spike` injects nothing:** the anomaly uses an undefined vType.
   - **Teleports disabled** (`--time-to-teleport -1`).

---

## 1. Plant catalogue

### 1.1 Overview

| ID | Code | Topology (lanes) | Main lengths | Bottleneck type | Limits | Step | Drivers | Fate |
|---|---|---|---|---|---|---|---|---|
| **ramps_v0** (v5) | `traffic_environment/sumo/generate_ramp_network_v0.py`, `ramps_v0.net.xml` | 3L → 4L weave → 3L; on-ramp + off-ramp | 3 × 1,000 m up, weave 250 m, 1,000 m down; ramps 300 + 100 + 100 m (gen_v0:227-239) | weaving (4L lane 0 shared on/off) | 33.33 / 25 m/s (gen_v0:207, 295) | 1 s [INF: v5 default] | v5 fleet | named in README:6-7 but **not used** in the catalogued experiments (env is ramps_v2, `core/env_interact.py:36-47`) |
| **ramps_v1** (v5) | `generate_ramp_network_v1.py`, `network_config_ramps_v1.yaml` | 3L → 4L weave → 3L; on-ramp + off-ramp | 4 × 1,000 m up, weave 500 m, 1,000 m down; ramps 700 + 200 + 100 m each (gen_v1:58-75) | weaving + merge entry | 33.33 / 25 | 1 s | v5 fleet, 50 % CAV | NC diagnostic only (Mar 2026), `tests/persistent_results/summary_elaborated_18-03-2026_14-08-30.md` |
| **ramps_v2** (v5 main) | `generate_ramp_network_v2.py`, `network_config_ramps_v2.yaml` | 3L → 4L (lane 0 = 250 m acceleration lane, no successor) → 3L; on-ramp only | 4 × 1,000 m up, merge 250 m, 1,000 m down; ramp 700 + 200 + 100 m (gen_v2:83-104) | on-ramp merge, 4 → 3 drop | 33.33 / 25 (gen_v2:80, 123) | 1.0 s (`configurations/_common_config.yaml:9`; no `--step-length` in `env_interact.py:413-425`) | Krauss HDV + Krauss CAV | all v5 training (15 exp. × 5 seeds) |
| **BN4** (lab T1) | `vsl_lab/netgen/bn4.py`, `plants/bn4.py` | 4 → 4 → 4 → (zipper) 2 → (zipper) 1 | 100 / 310 / 140 / 280 / 155 m (nodes x = 0, 100, 410, 550, 830, 985; bn4.py:24-26) | two zipper lane drops; TLS node 3 at x = 410 (meter) | 23 m/s (bn4.py:23) | 0.5 s (`plants/bn4.py:138`) | IDM Flow defaults, LC off; 10 % AV (`plants/bn4.py:141-145`) | **the** working plant; R6 claim |
| BN4-L / -VSL / -AV25 / -M | same | as BN4 | — | — | — | 0.5 s | LC2013 on / posted VSL / 25 % AV / perturbations | robustness / actuator variants |
| **RING22** (lab T3) | `netgen/ring.py`, `plants/ring.py` | 1-lane ring, 22 vehicles | L = 220–270 m | none (closed ring, wave instability) | 30 m/s (ring.py:17) | 0.1 s (`plants/ring.py:32`) | own IDM + √dt noise; 1 AV | done; H ≈ 0 |
| **MRG3-v1/v2/v3** (lab T2) | `netgen/mrg3.py` `SPEC`, `plants/mrg3.py` | 3L up (5 edges) → 4L merge (lane 0 = acceleration lane, ends) → 3L down; 1-lane on-ramp | up3/up2/up1 1,000 m, up0a/up0b 500 m, merge 250 m, down 1,000 m, ramp 300 m nominal (mrg3.py:20-26). Built lengths: up0b 465.6 m, merge 277 m, ramp 263.8 m (`docs/lab/t2_mrg3_r1_protocol.md:7-13`) | acceleration-lane merge 4 → 3 | 33.33 / 25 | 0.5 s (plants/mrg3.py:20); 0.2 s in the realism re-check | v1 Krauss defaults; v2 IDM + `departSpeed=max`; v3 IDM + `departSpeed=avg` (plants/mrg3.py:24) | closed by the realism gate |
| MRG3 H0–H5, H5a/b, H3a/b | `plants/mrg3.py:29-48` | as MRG3 | — | — | — | 0.2 s (Addenda B, D-3) | IDM / IDM+ASL 1 s / IDM+driverstate / W99 / EIDM ad hoc / EIDM defaults / + `lcAssertive` 1.5 or 3.0 | all FAIL realism |
| **LD3** (lab T2, D-4) | `netgen/mrg3.py:29` `LD_SPEC` | 3L up → 3L merge edge (lane 0 ends) → 2L down; no ramp demand | as MRG3; merge edge 263 m (`docs/lab/round2_protocol.md:174`) | 3 → 2 lane drop | 33.33 | 0.2 s | H5 (EIDM defaults), H3, H0 | realism FAIL (R-a); used for Round 4 harmonisation; killed (G ≤ 4 %) |
| **ZM3** (lab T2, Lead 2) | `netgen/mrg3.py:32` `ZM_SPEC` | ramp lane + main lane 0 **zipper** into merge lane 0 (radius 20 m); merge and down 3L | as MRG3 | zipper on-ramp merge (4 lanes in → 3) | 33.33 / 25 | 0.2 s | H5, H3, H0 | realism FAIL (R-c discharge 1,528 < 1,600) |
| **CORR2** (lab T4) | `netgen/corr2.py`, `plants/corr2.py` | 3L, 9.5 km; 2 metered on-ramps (each with a 4L acceleration-lane merge), 1 off-ramp, 2 VSL areas | see §1.4.6 (corr2.py:33-46) | two acceleration-lane merges + diverge spillback | 33.33 / 25 | 0.2 s (`plants/corr2.py:44`) | H5 | killed (G 0.4 %) |

### 1.2 v5 networks in detail

**Edges (from the shipped `.net.xml`, parsed) [CALC]**

| Net | Mainline edges (lanes, length) | Ramp edges (1 lane, 25 m/s) | Internal links | Junction notes |
|---|---|---|---|---|
| ramps_v0 | seg_2/1/0_before (3L, 1,000 m each) → seg_0_after (4L, 250 m) → seg_1_after (3L, 1,000 m) | on: approach 300, transition 100, merge 100; off: diverge 100, transition 100, departure 300 | **none** (hand-written net XML, no netconvert; gen_v0 docstring line 9) | 18 connections |
| ramps_v1 | seg_3…0_before (3L, 4 × 1,000 m) → seg_0_after (4L, 500 m) → seg_1_after (3L, 1,000 m) | on: 700 / 200 / 100; off: 100 / 200 / 700 | **none** (hand-written; gen_v1:127-140) | J6 typed `priority` with no outgoing edge (cosmetic) |
| ramps_v2 | seg_3…0_before (3L, 4 × 1,000 m) → seg_0_after (4L, 250 m) → seg_1_after (3L, 1,000 m) | on: 700 / 200 / 100; no off-ramp | 8 (netconvert, `--junctions.internal-link-detail 5`; gen_v2:295-304) | seg_0_before lane k → seg_0_after lane k+1; seg_0_after lane 0 has **no successor** (gen_v2:244-261) |

**Other v5 network facts**
- **Visual compression only:** shape multipliers of 0.5 compress the drawn geometry, but the `length` attributes set the physics (gen_v2:106-116, 214).
- **Route split:** ramps_v1 75 / 15 / 10 % (through / ramp-on / to off-ramp), `network_config_ramps_v1.yaml:4-17`. ramps_v2 75 / 25 % (`network_config_ramps_v2.yaml:22-31`).
  - The YAML fractions are **not** what the runtime generators use: they draw `ramp_fraction` per episode (§1.3).
- **Stale description:** `_common_config.yaml:4` calls ramps_v2 a "500m merge zone", but the edge is 250 m.

**Detectors (v5)**

| Net | E1 loops | Positions | Period | Other |
|---|---|---|---|---|
| v0 | 57 | entry 0 m, mid, exit L−1 per lane, every edge | 30 s | 5 E3; 5 `poi` "VSL" markers on seg_2/1/0_before and both ramp transitions |
| v1 | 75 | 5 / 50 / 95 % of each edge, per lane (`generate_detectors_v1.py:32`) | 30 s | 13 E3, incl. corridor-wide |
| v2 | 66 | 1-km edges 50 / 500 / 950 m; seg_0_after 10 / 125 / 240 m; ramp approach 35 / 350 / 665, transition 10 / 100 / 190, merge 5 / 50 / 95 | 30 s | 8 E3 (no seg_3_before) |

The env reads only the **exit** loops (`core/env_interact.py:55`), with `getLastIntervalVehicleNumber` / `MeanSpeed` / `Occupancy` (env_interact.py:665-667).

**VSL / actuation (v5)**
- **Box(4):** no posted limit changes. CAVs get `vehicle.slowDown(limit, 30 s)` every 5 s (`env_interact.py:540, 582-587`):
  - per lane on seg_0_before (the 1 km before the merge);
  - uniform on seg_1_before and seg_2_before (min of the seg_0 lanes, or explicit);
  - ramp approach + transition at the ramp limit.
  - After the merge is a "release point" (env_interact.py:58-68, 593-648). HDVs are never actuated.
- **Box(5):** Box(4) plus an edge-wide `setMaxSpeed` on seg_1_before (a physical sign for HDVs) (env_interact.py:526-530).
- **Box(7):** per-lane on seg_1_before as well.
- **Bounds and rate:** lanes 60–120 km/h, ramp 40–90 km/h (`configurations/per_lane_stochastic.yaml:43-46`); MUTCD step-down ≤ 16 km/h between seg_1 and seg_0 (`sar_components/actions/r44_action_v2.py:30-34, 78-80`); decisions every 30 s.

**SUMO options (v5):** `--step-method.ballistic`, `--collision.action warn`, `--time-to-teleport -1` (teleports **disabled**), socket TraCI (`env_interact.py:413-425`).

**Vehicles (v5, `traffic_environment/vehicle_fleet.py`)**
- **Fleet:** 70 % passenger, 12 % van, 12 % truck, 6 % truck-trailer (lines 98-104).
- **HDV:** Krauss, σ 0.30–0.50, τ 1.2–2.0 s, speedFactor 1.0 / dev 0.05; 2 % "reckless" (speedFactor 1.08–1.15, lcAssertive 1.5–3.0) (lines 124-142).
- **CAV:** Krauss, σ 0, τ 1.0, minGap × 0.5, all LC parameters 1.0 (lines 146-154, 353-368).
- **CAV share:** 50 % (May 16–17 runs) or 100 % (headline, ADR-008) (`docs/experiment_catalog.md` §2).
- **Weather:** multiplies the vType parameters (vehicle_fleet.py:196-210).

### 1.3 v5 demand, scenarios, anomalies

**Three demand generators (and one dead file)**

**A. On-the-fly 3-phase** (`traffic_environment/stochastic_demand.py`, written by `tests/_sumo_helpers.py:102-157`)
- **Shape and parameters:** peak U(5,500, 8,000) total veh/h; base = 0.4–0.6 × peak; linear rise to t_peak (0.15–0.30 T), plateau with 5 % Gaussian noise, linear fall from t_decay (0.65–0.80 T); ramp = 0.20–0.30 × total, perfectly correlated with the mainline (stochastic_demand.py:47-87; config `per_lane_stochastic.yaml:19-26`).
- **Arrival process:** one Bernoulli draw per second per route, `rng.random() < rate_veh_per_s` (`_sumo_helpers.py:121-131`). **This caps each route at 3,600 veh/h.** Ramp starts at 100 s; departures at integer seconds.
- **Used in:** **evaluation** (`evaluate_models.py:67-100`, "matching training conditions", which it does not), and the training "legacy fallback" (`train.py:138-151`).

**B. Focused pool** (`scenario_pool.py:188-304`, writer `:307-380`, CLI `generate_scenarios.py focused`)
- **Shape:** flat base U(5,500, 7,250) + N(0, 200) per 30-s bin, clipped to [0.8 × lo, 1.2 × hi]; ramp fraction 0.20–0.30.
- **Arrival process:** **deterministic uniform spacing** inside each bin; weather mix 70 / 20 / 10.
- **Used in:** **training** of every catalogued run: 200 scenarios, seed 42, 100 % CAV (`deploy_4vm.sh:76-88`), or seed 0, 50 % CAV (`launch_training.sh:163-170`). Also the SB3 `EvalCallback` (same pool, `train.py:257-259`).

**C. Hermite pool** (`demand_profiles.py:274-402`, `scenario_pool.py:94-185`)
- **Shape:** 5–10 control points; peaks 5,500–8,000, base 2,500–4,000, boundaries 2,500–3,500; Hermite splines plus heteroscedastic jitter and wander noise; ramp counts are a scaled copy of the mainline weights.
- **Arrival process:** uniform spacing per bin.
- **Used in:** not in any catalogued experiment [INF: the catalog lists only focused / on-the-fly configs].

**Dead: `scenario_generator.py`.** Imports a non-existent `make_counts_from_profile` (line 19); its topology map lacks ramps_v2 (lines 27-41); seeds come from Python `hash()` (lines 567, 589). The module cannot be imported, and nothing imports it (grep).

**[CALC] Effect of the Bernoulli cap on the 30 evaluation seeds.** Seeds `99,000 + ep`; episode seed = (env_seed · 100,000) mod 2³² & 0x7FFFFFFF, per `env_interact.py:192-201`; profiles regenerated with `stochastic_demand.generate_demand_profile`, numpy only.

| Quantity | Value |
|---|---|
| Nominal total peak | 5,632–7,957 veh/h (median 6,597) |
| Nominal peak mainline | 4,090–6,000 veh/h (median 4,957) |
| Mainline, hourly mean, nominal | median 4,430 veh/h |
| Mainline, hourly mean, **realisable under the cap** | **median 3,459** (3,217–3,583) |
| Seconds with mainline rate > 1 veh/s | median 77 % (54–92 %) |
| Ramp, nominal → realisable | 1,461 → 1,436 veh/h (the cap rarely binds on the ramp) |

This matches the audit's downstream flow of about 4,634–4,667 veh/h for every arm (`docs/audit_2026-05-20_fresh_thread.md:76-82`).

**[CALC] Pool sample** (`scenario_pools/focused_20260404_225222`, 200 scenarios, seeds 0–199):
- labelled D = 5,514–7,230 veh/h (median 6,404), R = 20–30 %;
- weather 156 clear / 27 rain / 17 fog; CAV share 0.50;
- realised scenario 0000: 4,954 mainline + 1,537 ramp vehicles in 3,600 s;
- **ramp burst:** 39 ramp vehicles in [100, 101) s (scenario 0000), 30 and 31 in scenarios 0001 and 0002. Cause: `ramp_t0 = max(t0, 100)`, `ramp_bs = max(1, …)` for the bins before 100 s (`scenario_pool.py:342-353`).
- All vehicles: `departPos="last" departLane="best" departSpeed="desired" insertionChecks="none"` (scenario_pool.py:370-375; `_sumo_helpers.py:91-94, 149-152`).
- The `.sumocfg` hard-codes `/home/catalin/work/...` net and detector paths, despite the portability comment (`_sumo_helpers.py:165-187`).

**Anomalies (v5)** (`traffic_environment/anomaly_injector.py`; config `per_lane_stochastic.yaml:27-30`). One anomaly in 15 % of episodes, starting in [max(warm-up + 60, 0.3 T), 0.7 T] (lines 71-96). The `anomaly_active` flag is in the state.

| Type | Duration | Implementation | Defect |
|---|---|---|---|
| `ramp_spike` | 60–120 s | `vehicle.add(type="HDV", route="ramp_route")` once per second (lines 187-205) | **no vType "HDV" exists** (types are `HDV_normal_*`, `HDV_reckless_*`, `CAV_*`; checked in a pool file), so the exception is swallowed and **nothing is injected**. As designed it would be +3,600 veh/h, not the "2×" its docstring claims (line 7). Episodes were flagged "anomaly" anyway |
| `speed_reduction` | 90–180 s | `edge.setMaxSpeed(seg_1_before, 40 km/h)`, restored to 120 (lines 147-153, 170-175) | conflicts with the Box(5) sign on the same edge; the restore overrides any controller limit. **0 occurrences in evaluation** (audit:43) |
| `lane_closure` | 120–240 s | `lane.setMaxSpeed(seg_0_before_2, 10 km/h)`, restored to 120 (lines 155-161, 177-182) | not a closure (the lane stays usable); the restore overrides the controller |

**Seeds (v5)**

| Role | Seeds | Source |
|---|---|---|
| Training env | env_seed = seed · 1,000 + worker; episode seed = env_seed · 100,000 + episode (mod 2³²) | `train.py:116`, `env_interact.py:192-201` |
| Route / anomaly / SUMO RNG | episode seed + 10,000 / + 50,000 / `--seed` episode seed | `env_interact.py:221-234, 274, 294-295` |
| Scenario (pool path) | pool file seeds 42–241 (deploy) or 0–199 | `deploy_4vm.sh:67-79`; pool names |
| Validation / checkpoint selection | EvalCallback env seed + 5,000 **on the same training pool** | `train.py:257-259`; screen §1 line 13 |
| Final evaluation | 30 episodes, env seeds 99,000–99,029, on-the-fly capped generator, clear weather | `evaluate_models.py:401, 443-447` |

There was no separate test pool, and no disjointness check beyond mod-2³² arithmetic [INF].

### 1.4 Lab plants in detail

#### 1.4.1 BN4: Vinitsky et al. 2018 / Flow bottleneck (Track 1)

- **Geometry:** edges "1"–"5": 100 / 310 / 140 / 280 / 155 m with 4 / 4 / 4 / 2 / 1 lanes; nodes 4 and 5 are `zipper` with radius 20 m; connections 3 → 4 lane i → i // 2, and 4 → 5 both lanes → 0 (`netgen/bn4.py:21-33, 57-65`).
  - Node 3 (x = 410, 140 m before the first zipper) is a TLS. It is held all-green by an extra program; netconvert's default 80 / 5 / 5 s program would otherwise meter NC (bn4.py:78-82; STATUS item 1). H-R7 asserts the state.
- **Vehicles** (`plants/bn4.py:141-154`):
  - IDM a 1.0, b 1.5, T 1.0 s, s0 2 m, δ 4, length 5;
  - human speedFactor normc(1, 0.2, 0.2, 2.0); AV speedFactor 1, speedDev 0 (the default 0.1 had silently applied until fix v3, docstring line 3);
  - lane changing **disabled** (lcStrategic −1 …); BN4-L enables LC2013;
  - depart: lane random, speed 10 m/s.
- **Detectors:** E1 `exit_5_0` at L − 15 m on edge 5; E1 `merge_3_{0..3}` at L − 10 m on edge 3; period 20 s (bn4.py:28-31, 68-77).
  - The **controllers and DRL use ground truth**: the meter reads `edge.getLastStepVehicleNumber("4")` (`envs/bn4_env.py:51-56`), and the S-VIN observation is per-lane-piece vehicle counts and speeds from vehicle positions (bn4_env.py:158-183). [INF] This is idealised sensing.
- **Actuators** (bn4_env.py:29-35, 38-62, 102-104):
  - **AV caps:** per lane-piece on edges 2, 3, 4 (22 values);
  - **posted VSL:** gantries on edge 2 (application) and edge 3 (acceleration);
  - **feedback meter** at node 3: q ← q + K_F (n_crit − n̂) every 30 s; 6 s green, red c = 2 · 4 · 3,600 / q.
  - The BN4 meter is a **mainline** signal that holds back all traffic, not an on-ramp meter.
- **Demand:**
  - R1: constant q over [0, 1,500) s, explicit Poisson arrivals; outflow measured over [1,000, 1,500) (`docs/lab/t1_bn4_plant_checks_protocol.md:18-19`).
  - R2 onwards: 40 s warm-up + 900 s control, demand ends at 940 s, then an uncontrolled drain (cap 7,200 s). Cells q ∈ {1,200, 1,600, 2,000, 2,400} (`t1_bn4_r2_baselines_protocol.md:7-25`).
- **Perturbations (T1-M):**
  - `slow`: edge-5 limit to 5 m/s for 300 s;
  - `block`: one vehicle stops mid-edge 4, lane 1, for 180 s (it brakes normally);
  - `surge`: inflow × 1.3 for 300 s;
  - start ~ U(warm-up + 100, end − dur − 100) (`t1_meter_gscan_protocol.md:12-21`; code `bn4_env.py:264-290`).
  - **T1-M2 grid:** slow v ∈ {3, 5, 8} m/s × {150, 300, 600} s; block {60, 180, 360} s; surge × {1.15, 1.3, 1.5} × {150, 300, 600} s (`t1_meter2_protocol.md:12-19`).
  - **AV share:** 10 % (T1), 25 % (B).

#### 1.4.2 RING22 (Track 3)

- **Geometry:** a single-lane ring of 4 arc edges, no internal links, so the lap equals the sum of the edge lengths; L ∈ {220, …, 270} m; 30 m/s (`netgen/ring.py:1-56`).
- **Vehicles:** 21 humans on our own IDM (v0 30, T 1, a 1, b 1.5, δ 4, s0 2) + √dt · N(0, 0.2) acceleration noise; 1 AV. SUMO runs speedMode 6 (it only integrates kinematics) plus our own 0.5 m safe-stop rule (`plants/ring.py:1-36`).
- **Timing:** step 0.1 s, warm-up 75 s, control [75, 375) s (`t3_ring_r1_r2_protocol.md:5-12`).
- **Detectors:** none; ground truth only.

#### 1.4.3 MRG3 family (Track 2)

- **Geometry:** up3 / up2 / up1 1,000 m, up0a 500 m, up0b 500 m (3 lanes) → merge 250 m (4 lanes; lane 0 is the acceleration lane, no successor) → down 1,000 m (3 lanes); 1-lane ramp, 300 m nominal, 25 m/s (`netgen/mrg3.py:20-26, 63-84`).
  - No explicit lengths, so the built edges are 465.6 / 277 / 263.8 m (R1 protocol:10-13).
- **VSL:**
  - application area up1 + up0a (1.5 km, x = 2,000–3,500 m) at rate b;
  - Carlson safety staircase: up2 = min(1, b + 0.2), up3 = min(1, b + 0.4);
  - acceleration area up0b = 0.9 while active;
  - VSL = b × 120 km/h;
  - `lane.setMaxSpeed` on all 3 lanes (`jobs/mrg3_run.py:4-5, 154-158`; `plants/mrg3.py:164-167`); decisions every 60 s (R1 protocol:25).
- **Compliance:** speedFactor groups. Compliant normc(1.0, 0.05, 0.8, 1.2); non-compliant share p_nc (default 0.3) normc(1.15, 0.05, 0.95, 1.4); trucks 10 % (`plants/mrg3.py:59-81`).
- **Detectors:**
  - E1 at L − 5 m per lane on up3…up0b and down, plus the ramp end;
  - E2 over all merge lanes, and over the first 300 m of down;
  - period 30 s (`netgen/mrg3.py:95-107`). The docstring's "60 s control loops" (line 7) does not exist in code.
  - Realism probes: mean speed within ±50 m at x ≈ 500 / 1,500 / 2,500 / 3,250 / 3,733 m, every 10 s (`jobs/mrg3_run.py:32-34`; verdict JSON `probe_x`).
- **Demand:** trapezoid. Mainline base 2,500 veh/h and ramp base 300; linear rise over [600, 1,200) s, plateau to 3,000 s, fall over 600 s, base to 3,900 s, then an uncontrolled drain to ≤ 10,800 s (`jobs/mrg3_run.py:63, 94-95`; `plants/mrg3.py:99-120`). Control from 300 s.
  - Peak grids: 4,800–6,000 × {600, 900} (v1–v3); 4,200–6,000 × {600, 900} (realism).
- **Driver variants** (`plants/mrg3.py:24-48`; `t2_realism_protocol.md:22-28, 160`; `round2_protocol.md:141-150`):

  | ID | Driver model |
  |---|---|
  | v1 | Krauss SUMO defaults, departSpeed max |
  | v2 | IDM (cars a 1.0 / b 1.5 / T 1.0; trucks a 0.6 / T 1.5 / length 12 / 25 m/s), max |
  | v3 / H0 | IDM, departSpeed avg |
  | H1 | + actionStepLength 1 s |
  | H2 | + driverstate (awareness 0.7) |
  | H3 | W99 defaults |
  | H4 | EIDM, ad hoc large errors |
  | H5 | EIDM, SUMO defaults |
  | H5a / H5b / H3a / H3b | + lcAssertive 1.5 / 3.0 |

- **Hidden conditions:**
  - p_nc ∈ {0.1, 0.3, 0.5}; truck share 0.05 / 0.10 / 0.20;
  - incident: a broken-down vehicle, lane 2 mid-up0a, for 15 min, start U(1,500, 2,400) s (`round4_harmonisation_protocol.md:236-240`; `jobs/mrg3_run.py:80-92, 201-208`). A sudden `setDisallowed` lane closure caused collision artefacts and was replaced (line 240).
  - CAV arms (Round 3/4): SUMO CACC/ACC defaults, shares 10 / 25 / 50 % (`round3_tm21_protocol.md:24-30`).

#### 1.4.4 LD3: lane drop (D-4)

- Same 4 km approach, VSL areas and probes as MRG3.
- `merge` = a 263 m 3-lane zone whose **lane 0 ends** (3 → 2), then a 2-lane `down`. No ramp demand; the ramp edge is kept unused so detector IDs stay valid (`netgen/mrg3.py:27-29, 63, 80-82`; `round2_protocol.md:172-175`).
- Grid: main 3,300–5,100 / ramp 0. Round 4 cells 3,900 / 0 and 4,500 / 0.

#### 1.4.5 ZM3: zipper on-ramp merge (Lead 2)

- Node n4 is a `zipper` with radius 20 m.
- Ramp lane + up0b lane 0 → merge lane 0; up0b lanes 1–2 → merge lanes 1–2; merge and down have 3 lanes (`netgen/mrg3.py:30-32, 54-56, 63, 80-82`; `t2_zipmerge_protocol.md:5-12`).
- Grid 4,200–6,000 × {600, 900}; 0.2 s.

#### 1.4.6 CORR2: corridor (Track 4)

- **Mainline (3 lanes):**

  | Segment | x (m) | Note |
  |---|---|---|
  | m0 | 0–1,500 | |
  | m1 | 1,500–2,500 | **VSL area 1** |
  | m2 | 2,500–3,000 | |
  | merge1 | 3,000–3,250 | 4 lanes; acceleration lane 0 ends |
  | m3 | 3,250–4,500 | |
  | — | 4,500 | **off-ramp O1** from m3 lane 0, 300 m |
  | m4 | 4,500–5,500 | **VSL area 2** |
  | m5 | 5,500–6,000 | |
  | merge2 | 6,000–6,250 | 4 lanes; acceleration lane 0 ends |
  | m6 | 6,250–7,500 | |
  | down | 7,500–9,500 | |

  Explicit lengths since v2, because the v1 geometric lengths were 31–37 m short (`netgen/corr2.py:1-46`).
- **Ramps:** origin edge 200 m + storage edge 400 m.
- **Meters:** TLS at the storage end; passage-terminated green of 2–4 s; yellow instead of red (red caused 9–14 m/s² stops) (`plants/corr2.py:15-29, 89-121`).
- **Detectors:**
  - E1 per lane at L − 5 m on every mainline edge (30 s);
  - ALINEA loops 40 m past each merge end (60 s);
  - ramp entrance and exit E1;
  - E2 over the storage and origin edges (queue);
  - off-ramp end E1 (corr2.py:16-21, 138-166).
- **Demand:** five OD routes; 20 % of the mainline-origin and R1 vehicles exit at O1; trapezoid with base = 50 % of peak (`plants/corr2.py:44-80`).
  - Grid: q_main 4,000–5,500, q_r1 0–600, q_r2 1,200–2,500 (`t4_corr2_protocol.md:12-50`).
- **VSL areas m1 / m4 were built but never exercised.** The headroom scan used only `nc` and ALINEA (t4 protocol:50).

### 1.5 Lab demand generator and runner (replacing the v5 path)

- **`vsl_lab/sim/demand.py`:**
  - explicit per-route **Poisson** arrivals with a piecewise-constant rate;
  - each depart snapped **up** to the step grid;
  - every vehicle written out, so `due(t)` is exact and conservation can be checked to the vehicle;
  - **no per-second cap** (docstring lines 1-5; lines 37-56);
  - no `insertionChecks` override; departSpeed per plant (BN4 "10", MRG3 v3+ / CORR2 "avg").
- **Runner** (`vsl_lab/sim/runner.py:1-17, 98-104`):
  - libsumo; `--time-to-teleport 300`; collisions `warn` with junction checks off; statistic-output;
  - health codes H-R1…H-R7 and H-E1…H-E4: conservation identities, insertion backlog, teleports FAIL, collisions, stuck vehicles, actuator asserts, drain and per-route arrivals;
  - metric = door-to-door time **including the origin queue**.

### 1.6 Perturbation / hidden-condition catalogue (all plants)

| Plant | Kind | Parameters | Artefact notes |
|---|---|---|---|
| v5 ramps_v2 | ramp_spike / speed_reduction / lane_closure | 15 % of episodes, 60–240 s | `ramp_spike` is a no-op (undefined vType); "closure" is a 10 km/h lane; restores override the controller |
| v5 ramps_v2 | weather | 9 profiles (scenario_generator, dead) or 70 / 20 / 10 clear / rain / fog vType multipliers (pool) | training pool only; evaluation clear |
| BN4 | slow | edge 5 → 3 / 5 / 8 m/s × 150 / 300 / 600 s | 3 m/s caused a teleport in the smoke run, so T1-M used 5 m/s (gscan protocol:17) |
| BN4 | block | one stopped vehicle on edge 4 lane 1, 60 / 180 / 360 s | **360 s teleports in 209 of 220 runs** (excluded); 180 s blocks: 21 FAIL runs at q 1,600 in the gscan (`t1_meter_gscan.md:18`); R6 NC FAIL 63 of 840 (`t1_meter_r6.md:29`) |
| BN4 | surge | × 1.15 / 1.3 / 1.5 × 150 / 300 / 600 s | clean |
| BN4 | AV share | 10 % / 25 % | — |
| MRG3 / LD3 | p_nc, trucks, demand level, incident (stopped vehicle, 15 min) | Round 4 gscan D1–D4, C1–C2, K1–K2, I1–I2 | lane closure via `setDisallowed` produced collisions (replaced) |
| MRG3 / LD3 | CAV share (ACC/CACC) 10 / 25 / 50 % | — | CACC at 0.5 s: 23 emergency braking events per run (79 for ACC) with no command; 9 at 0.2 s (`round3_tm21_protocol.md` Add. A) |
| CORR2 | demand conditions A–D (5,000 / 300 / 2,000 ± one stream) | — | clean (0 teleports) |
| RING22 | ring length L 220–270 | — | none after the collision / start-clamp fixes (STATUS items 7-8) |

### 1.7 Lab seed splits

**Approved layout:** 7,100,000–7,399,999, per track t (`docs/plans/vsl_drl_run_roadmap_v0.md:306-318`; `CLAUDE.md`):

| Role | Seeds |
|---|---|
| calibration | 7,1t0,000–009 |
| plant checks | 010–099 |
| tuning | 100–299 |
| validation | 300–499 |
| test | 500–699 |
| reserved | 700–999 |
| DRL training | 7,2t0,000+ |

**Seeds actually used:**

| Plant | Calibration / smoke | Plant checks | Tuning | Validation | Test | Reserved | DRL train |
|---|---|---|---|---|---|---|---|
| BN4 (t = 1) | 7,110,000–009 (smoke + thermal) | T1 010–019; T0 020–029; T0b 030–049; A-T0 050–059 | R2 100–119; A-R2 120–139; B-R2 140–159; M-gscan / H1 160–179; M-H2 gate 180–199 | A-P5 310–312; P-M checkpoints 320–322; P-M screen 330–339 | R5 500–529; B-R5 560–589; R5-M 590–689; R5-M2 690–789 | R5-M2 **consumed 90 reserved seeds**, 700–789 (disclosed); **R6 790–999 (210)** | 7,210,000+ |
| Lead 1 (BN4-M2) | scan 7,170,000–009; smoke 099 | — | evsched2 7,170,100–119 | — | — | gate 7,170,220–239 | — |
| MRG3 (t = 2) | v1 7,120,000–009; D-1 / smoke 050; v2 050–059; v3 100–109; realism 0.5 s 170–179 (abandoned), 0.2 s 260–269 | v1 R1 010–049; realism 0.2 s checks 270–289 | (never run) | R4 300–302 | R5-H refs 500–529 | — | 7,220,000+ |
| Block 7,160,000–999 (T2 plant development, approved 2026-10-02) | D3 000–009; LD3 010–019; ZM3 020–029 | D3 100–119; LD3 120–139; ZM3 140–159 | R4 T-H 200–229; R2-H 300–319; gscan 400–409 | — | — | — | — |
| CAV block | 7,150,000–299 (Round 3, never run beyond smoke) | — | — | — | — | — | 7,250,000+ |
| RING22 (t = 3) | 7,130,000 | R1 010–019 | R2 100–119 | (P2/P3 validation) | — | — | — |
| CORR2 (t = 4) | 7,140,000 smoke; calibration 001–003 | gscan 010–019 | — | — | — | — | — |

Sources: the protocols named in §1.4, `round2_protocol.md:31-46, 92-98, 152-156, 185`, `round4_harmonisation_protocol.md:24, 107, 141`, `t1_meter_gscan_protocol.md:24, 102-109, 170, 215, 241-242, 257`, `t1_meter_r6.md:3`, `t1_meter2_h.md:3`. Several reassignments within a track's range were disclosed in each protocol.

---

## 2. Mechanism evidence per plant

| Plant | Breakdown under NC? | Capacity drop | Stop-and-go waves | Teleports / artefacts | Realism verdict | Actuator authority (T0) | Headroom G / H | Authority band |
|---|---|---|---|---|---|---|---|---|
| **ramps_v2** (v5 evaluation) | **No.** Merge 83–86 km/h; 1.28 % congested windows (max 1.67 %), min merge speed 82.9 km/h, at nominal peaks up to 7,560 (audit:100-112) | never measured on ramps_v2 (screen §2 (b)) | none observed | teleports disabled (−1); `insertionChecks none`; ramp burst at 100 s | never gated | DRL slowed the merge to about 54 km/h: TTS +23 % vs NC (audit:74-90) | best non-learning vs NC only **2.6 %** on TTS (screen §2 (a)); no gate run | none (the realised demand was capped) |
| **ramps_v1** (v5 NC sweep, 2,500–7,000) | onset about 6,000 (seg_0_before 62 km/h); **full at 7,000** (seg_0_before 30 km/h, queue 2 km upstream, 592 vehicles) (summary_elaborated:16-38) | **−0.4 %** (6,733 vs 6,760, screen §1 line 11). [CALC] my rough recheck: exit flow 6,672 before vs 6,728 after the seg_0_before < 60 km/h onset (ratio ≈ 1.01) | queue propagation reported; wave speed not measured | unknown (pre-health-check era) | — | — | — | 6,000–7,000 (breakdown only) |
| **BN4** (LC off) | yes, for q ≥ 1,400 (median outflow 900 at every q ≥ 1,400) | **1,044 → 900 veh/h, ratio 0.862** (`t1_bn4_plant_checks.md:8-33`); peak at q = 1,300 | standing queue upstream of the zipper ("once the congestion forms … it does not dissolve", T0 Add.); wave speed not measured | 0 teleports in 220 runs; WARN = expected origin queue (H-R2 77, H-R4b 9). The outflow is quantised at 893–907 veh/h when congested [INF: zipper alternation] | **never put through R-a…R-d.** [INF] It would fail R-c: 900 veh/h discharge on one lane is far below the 1,600 veh/h/lane floor | **meter:** +20 / +22 % outflow (T0b). **AV caps:** bind but only reduce outflow (−3 to −16 %). **Posted VSL: no** (−0.8 / +3.5 %, CIs incl. 0) (`round2_a_t0.md`) | tuned meter −45 % vs NC (`t1_bn4_r2_baselines.md`: 224.8 vs 412.3 s). Inflow-scheduled meter: G **4.1 %** (`round2_protocol.md:7-14`). Tuned AV cap ≈ NC | meter helps at q ≥ 1,600 (−203 to −345 s) and **hurts at 1,200** (+19 s) |
| **BN4-L** (LC on) | yes | peak 1,289 @ 1,400 → 900; ratio **0.698** (plant checks:37) | — | 0 teleports | — | — | — | — |
| **BN4-AV25** | yes | as BN4 | — | — | — | caps bind weakly | tuned `cap:18` vs NC −1.5 % (`round2_b_r2.md`); DRL beats `cap:18` in 0 of 3 congested cells (STATUS:25) | — |
| **BN4 + perturbations** (T1-M) | yes | as BN4 | — | 180-s block FAILs (teleports) in about 5 % of runs, every controller | — | meter-setting choice | **G 15.4 % (q 1,600), 10.3 % (q 2,000)**; single kinds 1.8–8.8 % (`t1_meter_gscan.md`). **H 20.4 % [+18.2, +78.9 s] at q 1,600; −3.3 % at 2,000** (`t1_meter_h.md`) | **q ≈ 1,600 only**. R6: DRL −4.3 % vs evsched, −2.5 % vs MPC-F; still +5.8 % behind the oracle lookup (`t1_meter_r6.md:5-16`) |
| **BN4-M2** (varied severity) | yes | — | — | `block_d360` teleports in 209 of 220 runs (excluded) | — | — | G 12.0 % (12.2 % without d360); literal H 11.1 % vs `evsched2`, but **3.3 % (CI incl. 0) vs `mpcf_old`** → KILL (`t1_meter2_h.md`; STATUS:9-12) | the R6 policy does not transfer (surge +16 %) |
| **RING22** | waves in 100 % of NC runs (std ≥ 1 m/s and stop share ≥ 0.10); NC = 85.2 % of the IDM equilibrium speed v_e | n/a (closed ring) | yes; amplitude (NC throw-away std 2.19 m/s, stop share 0.50); wave speed not measured | the first R1 had 75 FAIL (AV collisions), fixed (ledger 2026-10-01T23:11) | — | FollowerStopper +12.6 to +20.2 % mean speed vs NC (`t3_ring_r1_r2.md:11-18`) | PI-with-saturation = **100.2 % of v_e** → H ≈ 0 | every L |
| **MRG3-v1** (Krauss) | **almost never**: 2 of 10 at 6,000 / 900 in calibration; **0 of 30** in R1 | 0.976 (2.4 %) (R1 protocol:78-81) | — | 0 teleports | (gate later) | **posted VSL T0 FAIL:** −3.9 % application-area outflow at b = 0.4. T1c: every controller worse than NC (+3.4 % to +87 %) (`t2_mrg3_r1.md`) | — | none |
| **MRG3-v2** (IDM, max) | no: **insertion failure**, origin queue about 1,955–1,968 vehicles; median time 1,100–1,670 s | — | — | 6–12 teleports and 5–9 FAIL per 10-run cell (calibration v2 JSON) | — | — | — | artefact |
| **MRG3-v3 = H0** (IDM, avg) | breakdown share 0.8–1.0 in every cell | ratios 0.946–1.042 (max-based, confounded) | smoke −19.0 km/h at 0.5 s | **58 of 100 runs teleport**, all ramp vehicles stranded at the acceleration-lane end ("wrong lane") (`round2_protocol.md:117-129`) | FAIL (R-c) at 0.5 s and 0.2 s (215 teleports in 140 calibration runs at 0.2 s) | — | — | artefact |
| **MRG3 H1** (IDM + ASL 1 s, 0.2 s) | 1.0 at every cell | not measurable (n_free 0) | −15.8 (40 of 40 valid) | 2 operating + 5 stress teleports | FAIL | — | — | — |
| **MRG3 H2** (driverstate) | 0.9–1.0 | — | none (smoke) | 132 teleports in calibration | FAIL | — | — | — |
| **MRG3 H3** (W99) | 0.6–1.0 at ≥ 4,500 / 900 | **1.056 [1.002, 1.081]: no drop** (discharge 3–6 % above free flow) | −18.0 | 0 teleports; collisions in heavy congestion (STATUS:48) | FAIL (R-a) | — | — | — |
| **MRG3 H4** (EIDM ad hoc) | collapse: discharge 185 veh/h/lane, not drained | — | −7.2 (smoke) | — | COLLAPSED / excluded | — | — | — |
| **MRG3 H5** (EIDM defaults) | 0–1.0 by cell; checks onset share 0.25 at 4,200 / 900 | not computable (n = 1 + 15); within-run ramp-corrected ratio 0.963 | −16.9 | 0 teleports, 0 FAIL | FAIL (R-a) | — | — | — |
| **D3 H5a / H5b / H3a / H3b** (lcAssertive) | onset share 0.10–0.95 | H5b **1.011 [1.000, 1.027]**; the others not computable | −16.4 / −16.4 / −18.9 / −18.9 | 0 teleports | FAIL. **Onsets moved to the network entry**: R-d bottleneck origin 0.54 / 0.15 / 0.50 / 0.00 ("waves from nowhere") (`t2_realism_d3.md`) | — | — | — |
| **LD3 H5** | 0.1 at 3,300; 0.6 at 3,600; **1.0 at ≥ 3,900** | not computable (no runs with a ≥ 5-min discharge window); Q_ff about 1,575 veh/h/lane | **−16.4 km/h, 100 % at the bottleneck** | 0 teleports | FAIL (R-a only) | **posted VSL has authority over stops** (T-H0 PASS) | **G = H:** demand 2.2 %, compliance 0.8 %, trucks 4.0 %, incident 2.5 / 1.4 % (`round4_gscan.md`); per-cell constants vs pooled 0.38 % | 3,900: `const:0.8` −63 % stops, +2.1 % delay. 4,500: tuned `const:0.75` −25 % delay, −55 % stops (tuning seeds). By J = delay + 40 s/stop, only D3 = 4,500 gains (−21 %); D1/D2 NC ≈ best; D4 −1 % |
| **LD3 H3 / H0** | H3 0.3–1.0; H0 1.0 | H3 1.037 (no drop) | −18.9 | H0: 99 teleports in calibration (stranded at the lane end) | FAIL | — | — | — |
| **ZM3 H5** | 0–1.0 by cell; checks onset share 0.80 at 4,500 / 900 | **0.967 [0.923, 0.982]: the only merge R-a PASS** | −16.9 | 0 teleports | **FAIL R-c only:** discharge **1,528** < 1,600 veh/h/lane (`t2_zipmerge_protocol.md:29-38`) | not tested | — | — |
| **ZM3 H0** (IDM) | 0.7–1.0 | **not computable** (n = 19 + 1), although Q_dis 1,407 vs Q_ff 1,732 (≈ 0.81) and the within-run ratio is 0.866 [CALC from verdict JSON] | −18.0 | **0 teleports** (the zipper removed IDM stranding) | FAIL (R-a n/a; R-c 1,407) | not tested | — | — |
| **ZM3 H3** | 0–1.0 | not computable | −18.0 | 2 calibration teleports | FAIL | — | — | — |
| **CORR2** (H5) | merge-2 queue spills back to the off-ramp only briefly: **about 6 of 65 min** at 5,000 / 300 / 2,000. Ramp drivers yield, so the queue forms **on the ramp** and m4 stays above 60 km/h (`t4_corr2_protocol.md:23-37`) | none expected (the plant targets spillback) | not measured | 0 teleports in calibration and scan | not gated | ALINEA has authority but only adds delay | **G 0.4 %**; NC is the pooled best (`t4_gscan.md`) | none |

**Driver-model capacity (relevant to R-c)**
- Q_ff measured at the exit loops with the "Treiber-style" parameters (cars a 1.0, T 1.0 s; 10 % trucks with T 1.5 s) is **1,470–1,790 veh/h/lane** in every 0.2 s variant (verdict JSONs: H3 1,544; H5 1,492; H5a 1,787; LD3 1,575; ZM3 H5 1,581; ZM3 H0 1,732).
- [INF] So the R-c discharge floor of 1,600 veh/h/lane is at or above the free-flow throughput these driver parameters can deliver. A 3 % drop then lands below the floor almost automatically. R-c failures on ZM3 are therefore more about driver-parameter capacity than geometry.

---

## 3. Which features created controllable mechanisms, and which did not

| Feature | Effect in SUMO | Evidence | Controllable? |
|---|---|---|---|
| **Zipper lane drop** (SUMO `zipper` node), 4 → 2 → 1, LC off | sharp critical inflow (about 1,300–1,400) and a **13.8 % drop** (30 % with LC on), deterministic | `t1_bn4_plant_checks.md:8, 37` | **Yes, by metering** (mainline signal 140 m upstream: −45 %). **Not** by posted VSL (4-lane storage still overfeeds the bottleneck, `round2_protocol.md:108`) or by 10–25 % AV caps |
| **Zipper on-ramp merge** (ZM3) | drop 3.3 % (H5) and possibly about 13–19 % (H0, not measurable under the rule); no IDM stranding | `t2_realism_zm.md`; verdict JSON | **untested** (stopped at R-c) |
| **Acceleration-lane merge** (ramps_v2, MRG3, CORR2 merges), LC2013 | Krauss: hardly breaks down. IDM: strands ramp vehicles → teleports. EIDM / W99: merge smoothly, **no drop** (ratios 0.98–1.06). Assertive LC moves onsets to the entry | §2 rows MRG3 / D3; STATUS:36-52 | **No.** Posted VSL does not bind (T0 −3.9 %); MTFC / constant VSL only add delay (T1c) |
| **4-lane weave with off-ramp** (ramps_v1) | breaks down at 7,000 but jams **without** losing throughput (−0.4 %) | screen §1 line 11 | no mechanism for throughput VSL |
| **3 → 2 lane drop** (LD3, H5) | realistic waves (−16 km/h) starting at the drop, many stops (0.19 → 4.0 per vehicle from 3,900 → 4,500), **no measurable drop** | `round4_th.md`; `t2_realism_ld3.md` | **yes, for harmonisation** (stops −55 to −63 %), but **a constant limit is near-optimal** (G ≤ 4 %, DRL lost by about 10 %) |
| **Demand band** | authority exists only in a narrow band just above critical: BN4 q ≈ 1,600–2,400 (meter), LD3 about 4,500 (VSL by J), ramps_v1 7,000 | §2 | the band itself is observable from upstream flow, so scheduling by inflow gives G 2–4 % |
| **Hidden non-stationary capacity events** (slowdown, blockage, surge) on top of a capacity-drop bottleneck | the best meter setting changes strongly by event kind | `t1_meter_gscan.md` (all-kinds G 15.4 %; single kinds ≤ 8.8 %) | **yes: the only DRL target found.** Value comes from **mixing** kinds (single-kind families < 10 %) and mostly from blockages (R6 block −19 % vs evsched) |
| **Varying severity and duration** of the same events | G 12 %, but a fitted-model MPC closes it (H 3.3 %) | `t1_meter2_h.md` | no (KILL) |
| **Demand / compliance / truck share / incident** at a lane drop with posted VSL | best constant b moves only 0.65–0.85 | `round4_gscan.md` | no (G ≤ 4 %) |
| **Multi-bottleneck corridor with spillback to an off-ramp** | the mechanism exists but is small (6 of 65 min) | `t4_corr2_protocol.md:35-37` | no (ALINEA G 0.4 %) |
| **Closed ring, 1 AV** | robust waves | `t3_ring_r1_r2.md` | yes, but PI-with-saturation reaches the ceiling (H ≈ 0) |
| **CAV share (ACC/CACC, SUMO defaults)** | CACC at 25 % alone **worsens** delay by 46–93 %; hard braking at 0.5 s | `round4_th.md:9, 25`; `round3_tm21_protocol.md` Add. A | no authority (CAV arms parked) |
| **Step length** | changes the human plant: IDM door-to-door 356 → 392 → 403 s at 0.5 / 0.2 / 0.1 s; 0.5 s ramp teleports vanish at 0.2 s | `round3_tm21_protocol.md` Add. A; `t2_realism_protocol.md` Add. B | the realism verdict is step-specific |
| **departSpeed** | IDM + `max` / `desired` / `random` / `0` leaves 380–546 vehicles pending at 1,500 s; only `avg` inserts the full demand | `round2_protocol.md:80-88` | an insertion artefact that can masquerade as "no breakdown" |

**Synthesis (for the heatmap):**
- A controllable throughput mechanism needed all three of:
  - (i) a **junction-level discharge loss** (only SUMO zipper nodes produced one);
  - (ii) **upstream storage plus an actuator that actually holds back flow** (a signal meter; posted VSL did not);
  - (iii) demand **just above critical**.
- DRL headroom over tuned control additionally needed **(iv) hidden, mixed, non-stationary capacity events** whose best response differs by kind.
- Waves and stops (the harmonisation mechanism) exist almost everywhere with EIDM / IDM / W99, but a tuned constant limit captures them.

---

## 4. Bugs and design weaknesses

### 4.1 v5 scenario and demand generation

| # | Where | Issue | Consequence | Status |
|---|---|---|---|---|
| V1 | `tests/_sumo_helpers.py:120-131` | one Bernoulli draw per second per route caps each route at **3,600 veh/h** | evaluation mainline realised ≤ 3,459 veh/h median vs nominal 4,430 [CALC]; NC never broke down | the lab replaced it (`vsl_lab/sim/demand.py:1`; roadmap H-S4) |
| V2 | `evaluate_models.py:67-100` vs `train.py:120-136` | training on the focused pool (flat, uniform spacing, 100 % CAV, weather mix) vs evaluation on the capped 3-phase generator (clear) | train/eval distribution mismatch (screen §2 (f1)) | — |
| V3 | `traffic_environment/scenario_pool.py:342-353` | ramp vehicles of the bins before 100 s are crammed into [100, 101) s | 30–39 ramp vehicles inserted within 1 s on a 1-lane ramp [CALC, pool files] | never fixed |
| V4 | `_sumo_helpers.py:91-94, 149-152`; `scenario_pool.py:370-375` | `insertionChecks="none"`, `departPos="last"`, `departSpeed="desired"` | unsafe insertions; with collisions on `warn` they may go unnoticed [INF] | — |
| V5 | `core/env_interact.py:421` | `--time-to-teleport -1` | gridlock could not be detected as teleports (moot, since there was no breakdown) | — |
| V6 | `traffic_environment/anomaly_injector.py:195-205` | `ramp_spike` adds `typeID="HDV"`, which exists in no route file; the exception is swallowed | anomaly-flagged episodes had **no** perturbation; as designed it would be +3,600 veh/h, not "2×" | screen §2 (f5) [INF], confirmed here by reading the route files |
| V7 | `anomaly_injector.py:147-182` | `speed_reduction` and `lane_closure` restore 120 km/h at the end; the "closure" is a 10 km/h lane | overrides controller limits; with Box(5) the next window overwrites the anomaly; the anomaly set is not what it claims | — |
| V8 | `stochastic_demand.py:85-87`; `demand_profiles.py:375-381` | ramp = fixed fraction × total, sharing the mainline's time shape | ramp and mainline perfectly correlated; no independent ramp surge (the one designed surge is V6) | — |
| V9 | `scenario_generator.py:19, 27-41, 567, 589` | imports a missing function; no ramps_v2; seeds from Python `hash()` (randomised per process) | dead and non-reproducible; the curriculum and weather machinery in it is unused | — |
| V10 | `rou_writer.py:30, 112-140` (screen (f2)) | the compliance-group writer needs a missing `network_config_4_3.yaml` | HDVs fully non-compliant in Box(4) (binary compliance) | — |
| V11 | `_sumo_helpers.py:179-187`; pool `.sumocfg` | absolute `/home/catalin/work/...` paths despite the "portable" comment | pools are not portable to the `/srv/shared` mirror | — |
| V12 | `env_interact.py:693-698` | `upstream_demand_vph` sums the flows of 4 **serial** segments (about 4× demand) | unused metric (grep), harmless but misleading | — |
| V13 | `evaluate_models.py:238-241`; audit:112 | demand parameters are not logged (`ramp_fraction` = 0 in every evaluation row) | demand sweeps cannot be analysed after the fact | — |
| V14 | `train.py:257-259` | EvalCallback on the same 200-scenario training pool | checkpoint selection on training scenarios (screen §1 line 13) | — |
| V15 | docs | README:6-7 says ramps_v0 with an off-ramp; `_common_config.yaml:4` says a "500 m merge zone"; v0 / v1 nets have no internal links (hand-written XML) | stale descriptions; v0 / v1 merges lacked junction geometry | — |
| V16 | `demand_profiles.py:152-157` | the minimum-spacing fix can push interior control points to the 0.95 clip, giving duplicate times (zero-length Hermite segments) [INF] | rare, minor | Hermite path unused |

### 4.2 Lab plants, generators and gates

| # | Where | Issue | Consequence |
|---|---|---|---|
| L1 | `netgen/mrg3.py:64-73` | no explicit edge lengths: up0b 465.6 m, merge 277 m, ramp 263.8 m vs 500 / 250 / 300 nominal | geometry drift (disclosed in the R1 protocol). CORR2 v2 fixed it with explicit lengths (`netgen/corr2.py:35-36`) |
| L2 | `netgen/mrg3.py:7` vs `:25, 95-107`; `plants/mrg3.py:144` | the docstring promises 60 s control loops; the code has only 30 s loops, and `Sensors` hard-codes 30 s | latent mismatch if the loop period changes |
| L3 | `envs/bn4_env.py:51-56, 158-183` | the BN4 meter and DRL read **ground-truth** counts and speeds, not E1 data | optimistic sensing for every BN4 result, including R6 [INF] |
| L4 | `bn4_env.py:272-281`; `t1_meter2_protocol.md` A.1 | the blockage stops a vehicle longer than the 300 s teleport time | `block_d360` teleports in 209 of 220 runs; 180 s blocks FAIL in about 2–5 %; NC FAIL 63 of 840 in R6 |
| L5 | `t2_realism_protocol.md:42-44` + Add. A:141-146 | the calibration cell is chosen at breakdown share ≈ 0.5, but R-a needs ≥ 3 runs without an onset; at the check seeds the shares drifted (ZM3 H0 0.95, LD3 H5 0.6 with 0 discharge windows) | R-a is "not computable" in 9 of the 15 gated variant runs, even where the within-run ratio suggests a drop (ZM3 H0 0.866) |
| L6 | `eval/realism.py:85-99` | Q_ff and Q_dis are measured at the `down` exit loops, about 1 km downstream, averaged over **all** lanes (ZM3 lanes 1–2 do not pass the zipper) | dilutes a lane-local drop [INF] |
| L7 | `t2_realism_protocol.md:88` | R-c floor 1,600 veh/h/lane vs driver parameters whose free-flow throughput is 1,470–1,790 | R-c is close to unattainable for these vTypes [INF]; BN4 (900 veh/h on 1 lane) was never gated and would fail it [INF] |
| L8 | R-b | the wave-speed band [−25, −10] km/h passes for every model (−14 to −20) | not a discriminating realism check |
| L9 | `plants/mrg3.py:99-120`; `t2_realism_protocol.md:140` | one trapezoid shape (30-min plateau starting at 1,200 s): breakdown begins as the plateau arrives (t ≈ 1,210 s) | confounded the first drop estimator (fixed in Add. A); no stochastic demand shapes in T2 |
| L10 | `plants/mrg3.py:24`; `round2_protocol.md:78-88` | IDM + `departSpeed="max"` → insertion failure (origin queue of about 1,955 vehicles) | MRG3-v2 was an insertion artefact; fixed by `avg` |
| L11 | `plants/corr2.py:15-29` | meters have no red phase (yellow acts as red), so leakage | disclosed; ramp flow ≈ min(arrivals, r) + leakage |
| L12 | `plants/ring.py:1-20` | own IDM integration with speedMode 6, not SUMO car-following | ring results do not test SUMO's driver models |
| L13 | seed use | R5-M2 (test seeds 7,110,690–789) consumed 90 seeds of the reserved range 7,110,700–999 (`t1_meter_gscan_protocol.md:241-242`); many within-track reassignments (all disclosed) | the confirmatory reserve for BN4 shrank to 210 seeds |
| L14 | CORR2 | VSL areas m1 / m4 built but never tested; the scan compared only ALINEA vs NC | the posted-VSL cell on the corridor is empty |

### 4.3 Worth reusing / not reusing

**Reuse**
1. **`vsl_lab/sim/demand.py`:** explicit Poisson, step-snapped, exact `due(t)`, no cap.
2. **`vsl_lab/sim/runner.py` health checks:** conservation, insertion backlog, teleport FAIL, drain, door-to-door metric including the origin queue.
3. **The netgen pattern:** spec → plain XML → netconvert, content-hashed cache, explicit lengths (CORR2 v2); `check_net` structural tests (`tests/test_corr2_build.py`).
4. **BN4:** a validated, deterministic capacity-drop plant (T3 determinism PASS) and a known-positive test bed. Add E1-based sensing before any new claim (L3).
5. **LD3-H5 at 0.2 s:** artefact-free waves and stops for harmonisation / TM21 work.
6. **ZM3-H5:** the closest merge to a realism PASS. Re-gating needs a capacity-calibrated driver parameterisation, pre-registered (do not relax the bound post hoc, `t2_zipmerge_protocol.md:38`).
7. **CORR2:** a multi-bottleneck corridor with meters, off-ramp, VSL areas and E1/E2 detectors (VSL untested).
8. **The perturbation library:** slow / block / surge with severity and duration, broken-down vehicle via `setStop`. Keep blockages shorter than the teleport time, or detect stuck vehicles explicitly.
9. **The realism gate R-a…R-d and its estimator code**, with fixes for L5–L8.
10. **From v5:** the ramps_v2 geometry as a starting point (must be re-gated), the E1 entry/mid/exit-per-lane layout, the `vehicle_fleet` vType families (as ideas), and the ramps_v1 NC data.

**Do not reuse:** the v5 on-the-fly generator (V1), the pool writer (V3, V4), `anomaly_injector.py` (V6, V7), `scenario_generator.py` (V9), the socket-TraCI env (`--time-to-teleport -1`), and binary compliance.

---

## 5. Gaps: heatmap cells with no measurement

1. BN4 through the realism gate (R-b wave speed and R-c discharge) was never run.
2. ZM3 has no actuator checks (T0 / T1c) for posted VSL, metering or CAVs.
3. CORR2 posted VSL (areas m1, m4) was never tested; CORR2 with a capacity-drop junction (zipper merges) was never built.
4. Ramp metering on MRG3 / ZM3: no on-ramp meter was built for the merge plants.
5. **Within-run timing headroom** (a hindsight-optimal limit per 5-min block vs a constant limit) on LD3 is unmeasured. Every LD3 G is per run or per condition (open question in v6 `reports/Why v5 failed (human).md`, "One question is still open").
6. Lab plants never used stochastic demand shapes (every lab demand is a fixed trapezoid or constant). Realistic demand variability, the v5 Hermite idea, was never combined with a valid plant.
7. Detector-based (E1, 30 s) vs ground-truth sensing on BN4 (L3).
8. Wave speed on ramps_v1, BN4, ring and CORR2 was not measured.
9. ramps_v2 with the lab generator and runner (uncapped demand, health checks) was never run; MRG3 is its re-build, with different drivers.

## 6. Suggested plant × property matrix (values for the heatmap)

| Plant | Artefact-free | Breakdown | Capacity drop | Waves (km/h) | Posted VSL binds | Meter binds | AV/CAV binds | Best G | Best H | DRL outcome |
|---|---|---|---|---|---|---|---|---|---|---|
| ramps_v2 (v5) | no (V1–V6) | no (capped) | n/m | none | n/a (CAV-only Box 4) | n/a | CAV slowDown slows the merge | n/m | n/m (NC +2.6 %) | TQC +23 % TTS vs NC |
| ramps_v1 (v5) | unknown | at 7,000 | −0.4 % | n/m | n/m | n/m | n/m | n/m | n/m | — |
| BN4 | yes | q ≥ 1,400 | **13.8 %** | n/m | **no** | **yes (+20 %)** | caps negative only | 4.1 % (inflow) | — | AV-cap DRL ≈ NC |
| BN4 + perturbations | ~5 % FAIL (block) | yes | 13.8 % | n/m | — | yes | — | **15.4 %** | **20.4 %** | **R6: −4.3 % / −2.5 %** |
| BN4-M2 | `block_d360` artefact | yes | 13.8 % | n/m | — | yes | — | 12.2 % | 3.3 % (CI ∋ 0) | KILL |
| RING22 | yes | waves | n/a | waves, speed n/m | — | — | AV yes (+13–20 %) | — | ≈ 0 | pilots FAIL |
| MRG3-v1 | yes | rarely | 2.4 % | n/m | **no (−3.9 %)** | — | — | — | — | — |
| MRG3-v2 / v3 (IDM) | **no** (insertion / stranding) | yes | 0.95–1.04 | −19 | — | — | — | — | — | — |
| MRG3 H3 / H5 / D3 | yes | partly | **none** (1.01–1.06) | −16 to −19 | — | — | — | — | — | — |
| LD3-H5 | yes | ≥ 3,900 | n/c | **−16.4** | **yes (stops)** | — | CACC worsens | 4.0 % | 4.0 % | P-H2 +10 % J vs const |
| ZM3-H5 | yes | yes | **3.3 %** | −16.9 | n/t | n/t | n/t | — | — | — |
| CORR2-H5 | yes | ramp queues | n/a | n/m | n/t | ALINEA only adds delay | — | 0.4 % | — | — |

**Legend:** n/m = not measured; n/c = not computable under the rule; n/t = not tested; n/a = not applicable.
