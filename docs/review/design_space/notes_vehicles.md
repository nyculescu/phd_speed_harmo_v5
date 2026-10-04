# Design-space notes: vehicle diversity, vehicle types and CAVs (v5 pipeline + vsl_lab)

*Written 2026-10-04 for the design-space heatmap. Read-only review of branch `claude/vsl-lab-core` at `/srv/shared/Workspace/phd/phd_speed_harmo_v5`. Nothing was run except small read-only tallies of one committed scenario-pool file.*

**Tags.**
- [CODE] read in the code at the cited line.
- [FILE] counted in a committed artefact.
- [DOC] stated in a doc; not checked against code unless the text says so.
- [CALC] my own arithmetic.
- [INF] my inference.
- [VERIFY] a SUMO-semantics or literature point I could not confirm from the repo.

Paths: `vf` = `traffic_environment/vehicle_fleet.py`, `rw` = `traffic_environment/rou_writer.py`, `sg` = `traffic_environment/scenario_generator.py`, `sp` = `traffic_environment/scenario_pool.py`, `ei` = `core/env_interact.py`, `sh` = `tests/_sumo_helpers.py`, `ai` = `traffic_environment/anomaly_injector.py`, `m3` = `vsl_lab/plants/mrg3.py`, `lab/` = `docs/lab/`, `dl/` = `/srv/shared/Workspace/phd/docs_local/`.

---

## 0. Short answer

1. **v5 has one live fleet generator, `vf`.** Each scenario re-samples a library of **100 vTypes**: 4 classes × (10 normal HDV + 10 reckless HDV + 5 CAV) (`vf:213-371`; [FILE] 100 `<vType>` lines in the sample pool file). Each vehicle picks a class from FLEET_MIX, then a uniform variant (`vf:374-401`).
   - Within a vType, the only per-vehicle randomness is speedFactor (speedDev) and Krauss `sigma` noise.
   - It is **not** a vTypeDistribution, and the vTypes are **not** per vehicle.
2. **Most of that diversity never acted on a controller in the headline v5 results:**
   - The headline runs were at **100 % CAV** (ADR-008; `configurations/per_lane_stochastic.yaml:16`; `training_runs/*/config.yaml`). So no HDV was spawned, and the normal/reckless split, the HDV LC ranges, the tau/sigma ranges and the HDV weather effects were all dead at runtime.
   - What remained: CAV Krauss with `sigma 0`, `tau 1.0`, `minGap` 0.5 × base and `speedDev 0`, i.e. a deterministic, high-capacity fleet. The only variety was 4 lengths and the truck/trailer `maxSpeed` (`vf:146-154, 335-369`).
3. **Compliance in v5 was binary:**
   - CAVs got 100 % via `slowDown` (`ei:582-587, 593-648`). HDVs were never shown the VSL in Box(4).
   - The docs describe a "92 % comply / 8 % ignore" HDV model (`dl/slowDown_argument.md:89`; `dl/control_loop.md:88-93, 107`; `sar_components/actions/r44_action_v2.py:13-16`). **It does not exist in code.** `_is_non_compliant` is defined nowhere.
   - Box(5) (not the headline) posted `edge.setMaxSpeed` on `seg_1_before` (`ei:526-530`). There, every HDV complied up to its speedFactor: normal 1.00 ± 0.05, reckless 1.08–1.15.
4. **The v4 three-group compliance model is dead code:**
   - `rw:112-140` defines fc/uc/nc groups.
   - `flow_generation_single_file` raises because `traffic_environment/sumo/network_config_4_3.yaml` is missing (`rw:30, 637-645`; [FILE] `ls` fails).
   - Its only caller, `sg`, is imported by no module.
   - `obedience_level_HDV` is used only as a filename label (`sg:381, 555-563, 629`).
5. **v5 CAVs were Krauss, not ACC/CACC** (`vf:354`). They were actuated by `traci.vehicle.slowDown(v, limit, 30 s)`, re-issued every 5 SUMO steps on the controlled edges (`ei:540, 582, 607, 646`).
   - [CALC/VERIFY] If `slowDown` ramps linearly over its duration and each re-issue restarts the ramp, a CAV closes only about 67 % of the gap to its command in 30 s.
6. **vsl_lab replaced diversity with a few controlled knobs** (`m3:59-81`):
   - one `vTypeDistribution "mix"` with compliant cars, non-compliant cars and trucks;
   - per-vehicle speedFactor `normc(1.0, 0.05)` or `normc(1.15, 0.05)`; truck share; p_nc;
   - a driver-model registry H0–H5 (+ H3a/b, H5a/b) used as **plant variants**, not as hidden conditions (`m3:29-48`);
   - CAVs = SUMO **CACC/ACC with every model parameter at its default**, actuated through a per-vehicle `setMaxSpeed` set-speed staircase (`m3:51-56`; `vsl_lab/controllers/cav_staircase.py`).
7. **Realism gate:**
   - Waves (−14 to −19 km/h) and congestion origin pass for IDM, EIDM and W99.
   - A capacity drop **without artefacts was never obtained**: IDM strands ramp or lane-drop vehicles (teleports), W99 shows no drop, EIDM defaults rarely break down at the merge, and `lcAssertive` creates "waves from nowhere". ZM3 + H5 came closest: drop 0.967, but discharge 1,528 < 1,600 veh/h/lane (`lab/STATUS.md:36-52`; `lab/t2_realism_*.md`).
8. **Heterogeneity as a source of headroom was measured and was tiny** (Round 4 Addendum E, LD3/H5): compliance family **G = 0.8 %**, trucks **G = 4.0 %**, demand 2.2 %, incidents 2.5 % / 1.4 % (`lab/round4_gscan.md:9-13`).
9. **CAVs:**
   - SUMO default CACC at 25 % made delay **46–93 % worse** than humans on LD3 (`lab/round4_th.md:9, 25`), and the CAV arms had no authority. Round 3 (TM21) was parked.
   - At a 0.5 s step, CACC and ACC brake at 9 m/s² tens of times per run (`lab/round3_tm21_protocol.md:113-128`).
10. **Worth reusing:**
    - the vsl_lab `vtypes_xml` pattern and the per-vehicle speedFactor compliance model;
    - the behavioural R-0 "inert attribute" check;
    - CAV tracking by ID (the `av@<id>` lesson);
    - the common-random-numbers CAV draw.
    - From v5: only the class table and the weather multipliers, as *candidate* hidden-condition generators. They are unvalidated.

---

## 1. Pipeline map

| Pipeline | Entry point | vType source | Live? | Used by |
|---|---|---|---|---|
| **v5 scenario pool** (training) | `generate_scenarios.py focused` → `sp:188-304` → `sp:_write_route_file` (`sp:307-380`) | `vf.generate_fleet_xml(seed, weather)` (`sp:317`) + `vf.pick_vehicle_type` (`sp:368-369`) | **yes** | all `training_runs/experiment_2026051*` (pools `shared_seed42_n200` at 50 % and `shared_seed42_n200_cav100` at 100 %, per each run's `config.yaml` / seed log). **These pools are not in the repo.** Only `scenario_pools/focused_20260404_225222` (50 % CAV) is committed. |
| **v5 on-the-fly** (evaluation; training fallback) | `ei._regenerate_routes` (`ei:247-310`) → `sh.generate_stochastic_route_file` (`sh:102-157`) | `vf.generate_fleet_xml(seed=seed)`, **no weather argument → always clear** (`sh:114`) | **yes** | `evaluate_models.py:87-98` (`demand_config` set, no pool) |
| **v5 fixed-headway helper** (tests, feasibility sweeps) | `sh.generate_route_file` (`sh:43-99`); `tests/run_feasibility_sweep_v52.py:109-140` | `vf` with a fixed seed (one fleet realisation per sweep) | tests only | feasibility sweeps |
| **v4 legacy** | `sg` → `rw.flow_generation_single_file` (`rw:603-867`) | `rw.create_vehicle_types_with_variants` / `create_homogeneous_vehicle_types` (`rw:393-599`) | **DEAD** (missing `network_config_4_3.yaml`, missing `4_3_merge.net.xml` (`sg:26-35`), no importer) | none |
| **vsl_lab BN4** | `vsl_lab/plants/bn4.py:24-37` → `vsl_lab/sim/demand.py` | 2 vTypes, `human` / `av` | yes | T1 tracks |
| **vsl_lab MRG3 / LD3 / ZM3** | `m3:59-96` | `vTypeDistribution mix` (+ `cav` vType) | yes | T2, realism gate, Rounds 3–4 |
| **vsl_lab CORR2** | `vsl_lab/plants/corr2.py:51-79` | reuses `m3.vtypes_xml`, driver H5 | yes | T4 |
| **vsl_lab RING22** | `vsl_lab/plants/ring.py:109-115` | 2 vTypes; all dynamics in Python | yes | T3 |

No YAML in `configurations/` has a vehicle or fleet section. FLEET_MIX, the reckless share, the CAV parameters and the weather table are hard-coded in `vf`. Weather reaches training only through the `generate_scenarios.py --weather` CLI: `deploy_4vm.sh:84-88` and `launch_training.sh:166-172` both pass `clear:0.7,rain:0.2,fog:0.1` [CODE].

Two config keys are never read by any Python file [CODE grep]: `_common_config.yaml:13` `speed_limit_direct_control_CAV` and `:18` `cavs_percentage: 50`.

---

## 2. Q1: every vType parameter set or sampled

### 2.1 v5 live generator (`vf`), per class

All classes use `carFollowModel="Krauss"` and `laneChangeModel="LC2013"`. Attributes **never set**: `emergencyDecel`, `emissionClass`, `lcKeepRight`, `lcLookahead*`, `jm*`, sublane/lateral attributes, `departSpeed` distributions. SUMO class defaults therefore apply [VERIFY values].

**Step length:** default 1.0 (`vf:217`). The pool and on-the-fly `.sumocfg` set no step-length (`sh:182-194`), so SUMO runs at 1 s, launched with `--step-method.ballistic` (`ei:419`).

| Parameter | passenger (70 %) | passenger_van (12 %) | truck (12 %) | truck_trailer (6 %) | Source |
|---|---|---|---|---|---|
| vClass | passenger | passenger | truck | **trailer** | `vf:55-96` |
| length (m) | 4.5 | 6.0 | 7.5 | 16.5 | same |
| base minGap (m) | 2.5 | 3.0 | 3.5 | 4.0 | same |
| accel (m/s²) | U(2.4, 2.8) | U(2.0, 2.4) | U(1.8, 2.2) | U(1.2, 1.5) | same |
| decel (m/s²) | U(4.3, 4.7) | U(4.0, 4.5) | U(3.5, 4.0) | U(3.0, 3.5) | same |
| maxSpeed (m/s) | U(35, 40) | U(30, 35) | U(27, 30) | U(23, 25) | same |
| `BASE_SPECS.sigma` | 0.40 | 0.40 | 0.35 | 0.35 | **unused**; the group sigma overrides it (`vf:255, 298, 351`) |
| class share | 0.70 | 0.12 | 0.12 | 0.06 | `FLEET_MIX` `vf:99-104` |

Lane limits: 33.33 m/s (120 km/h) on the ramps_v2 mainline and 25 m/s on the ramp lanes ([FILE] `ramps_v2.net.xml`). Trucks (97–108 km/h) and trailers (83–90 km/h) are therefore capped by their own `maxSpeed` and never see a VSL above about 100 km/h [CALC].

| Parameter | Normal HDV (98 % of HDVs in practice) | Reckless HDV (2 % of HDVs) | CAV | Source |
|---|---|---|---|---|
| sigma | U(0.30, 0.50) per variant | 0.50 | **0.0** | `vf:124-154` |
| tau (s) | U(1.2, 2.0) | U(1.0, 1.2) | **1.0** | same |
| minGap | base × U(0.9, 1.1) | base × U(0.75, 0.90) | base × **0.5** | same; `vf:300, 341` |
| accel | class range | class range × 1.1 | class range × 1.1 | `vf:295, 338` |
| decel | class range | class range | class range × 1.05 | `vf:339` |
| maxSpeed | class range | class range × **1.15** | class range | `vf:297, 340` |
| speedFactor (mean) | 1.00 | U(1.08, 1.15) per variant | 1.00 | `vf:258, 301, 362` |
| speedDev | 0.05 | 0.06 | **0.0** | same |
| actionStepLength | floor(tau / step) × step; tau clamped to ≥ step | same | = step (1 s) | `vf:266-271, 309-314, 361` |
| lcStrategic | U(0.4, 0.7) | U(0.6, 1.0) | 1.0 | `vf:108-120, 365-368` |
| lcCooperative | U(0.3, 1.0) | U(0.0, 0.3) | 1.0 | same |
| lcSpeedGain | U(2.0, 8.0) | U(5.0, 12.0) | 1.0 | same |
| lcAssertive | U(0.5, 1.0) | U(1.5, 3.0) | 1.0 | same |
| variants per class | 10 | 10 | 5 | `vf:214-215` |
| pick rule | uniform variant | uniform variant; `rng.random() < 0.02` | uniform variant | `vf:393-401` |

Notes on this table:
- **HDV lane-change ranges.** Normal HDVs are **less assertive** than the LC2013 default (lcAssertive < 1 *raises* the required gap, per SUMO docs as quoted in `lab/round2_protocol.md:139`). They are also less cooperative and much more eager to change for speed gain (2–8 × default) [INF].
- **CAV LC values (all 1.0)** most likely equal the LC2013 defaults [VERIFY].
- **Desired speed** (SUMO: min(maxSpeed, speedFactor × lane limit) [VERIFY]):
  - normal cars about 120 ± 6 km/h;
  - reckless cars 130–138 km/h;
  - CAV cars exactly 120 km/h;
  - van CAVs sometimes 108–120 km/h, because their maxSpeed of 30–35 m/s can bind [CALC].
- **SUMO default speedDev** is 0.1, according to the repo's own BN4 fix note (`vsl_lab/plants/bn4.py:3`). So v5's normal HDVs have **half** the default desired-speed dispersion.

### 2.2 v5 weather multipliers (`vf:160-210`)

| Weather | accel × | decel × | minGap × | tau × | speedFactor × | sigma + |
|---|---|---|---|---|---|---|
| clear | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0 |
| rain | 0.85 | 0.80 | 1.30 | 1.25 | 0.90 | +0.05 |
| heavy_rain (never sampled) | 0.75 | 0.70 | 1.50 | 1.50 | 0.80 | +0.10 |
| fog | 0.90 | 0.85 | 1.40 | 1.60 | 0.75 | +0.08 |

- **HDVs** get all six multipliers.
- **CAVs** get only accel, decel and minGap. Their tau, sigma and speedFactor are kept (`vf:343-351`).
- **Mix:** the training pools were generated with clear 0.7 / rain 0.2 / fog 0.1. The committed pool realised 156 / 27 / 17 of 200 scenarios [FILE].
- **Not in evaluation:** evaluation is always clear (`sh:114`).
- **Side effect on actionStepLength** [CALC from `vf:266-271`]. In clear weather every HDV has ASL 1 s. In rain, 50 % of normal variants get ASL 2 s. In fog the split is 6 % at 1 s, 78 % at 2 s and 16 % at 3 s. So weather silently switches many HDVs to 2–3 s decision intervals. Example: the committed fog pool file has `HDV_normal_passenger_v0 tau="2.86" actionStepLength="2.00" speedFactor="0.75"`.
- **CAV–HDV speed gap:** in fog at 50 % CAV, HDVs want 90 km/h and CAVs 120 km/h.

### 2.3 v4 legacy generator (`rw`, dead)

| Item | Value | Source |
|---|---|---|
| classes | the same 4 + **bus** (12 m, accel 1.5–1.8, maxSpeed 25–28) | `rw:51-102` |
| class mix | 0.60 / 0.20 / 0.05 bus / 0.10 / 0.05, each × U(1 ± 0.15) per file; or "passenger-heavy" scalars with p = 0.15 | `rw:104-110, 680-686, 737-758` |
| compliance groups | fc: sigma 0.25, sf 1.0, sd 0, maxSpeed × 1.0 · uc: 0.20, 1.0, 0.05, × 1.1 · nc: 0.20, **sf 1.1, sd 0.6**, × 1.2; shares 1 : 1 : 1 | `rw:112-140, 767-779` |
| tau | U(1.2, 2.0); actionStepLength = random integer steps ≤ tau | `rw:230, 473-484` |
| LC ranges | as `vf` normal, except lcCooperative U(0.2, 1.0) | `rw:233-239` |
| CAV | accel × 1.1, decel × 1.05, minGap × 0.5, sigma 0, tau 1, sf 1, sd 0 | `rw:241-251` |
| car-following model | configurable per HDV/CAV (`car_following_model_hdv/cav`), default Krauss | `rw:397-399` |
| weather | visibility/slip/wind → multipliers (`sg:189-211`); **sigma multiplier not applied** (FIXME) | `rw:332-333` |
| RNG | **global `np.random`, never seeded** in `rw` | `rw:462-515, 737-833` |
| hidden "obedience" | filename label only | `sg:381, 555-563, 629` |

### 2.4 vsl_lab plants

| Plant | Humans | Trucks | AV / CAV | Step | Per-vehicle randomness | Source |
|---|---|---|---|---|---|---|
| **BN4** (Vinitsky bottleneck) | IDM: accel 1.0, decel 1.5, tau 1.0, minGap 2.0, δ 4, length 5; speedFactor `normc(1, 0.2, 0.2, 2.0)`; **LC off** (`lcStrategic -1`, `lcSpeedGain 0`, `lcCooperative 0`, `lcKeepRight 0`); BN4-L restores LC2013 defaults | none | `av` = the same IDM, speedFactor 1.0, **speedDev 0** (a silent default of 0.1 applied until fix v3); av_share 0.10 (T1) or 0.25 (T1-B) | 0.5 s | speedFactor only | `bn4.py:1-37` |
| **MRG3-v1** | SUMO default Krauss cars (doc: sigma 0.5, tau 1) | length 12, accel 1.3, decel 4.0, maxSpeed 25, vClass truck | none | 0.5 s | speedFactor | `m3:24, 59-81`; docstring `m3:3-6` |
| **MRG3-v2 / v3** | IDM `_IDM_CAR` as BN4; departSpeed max (v2) or avg (v3) | IDM: accel 0.6, decel 1.5, tau 1.5, minGap 2.5, length 12, maxSpeed 25 | none | 0.5 s | speedFactor | `m3:24, 29-30` |
| **H0–H5** (realism variants) | H0 IDM · H1 = H0 + `actionStepLength 1.0` · H2 = H0 + driverstate device (awareness 0.7) · H3 W99 defaults · H4 EIDM + sigmaleader 0.2, sigmagap 0.2, sigmaerror 0.3, treaction 0.6 · H5 EIDM with every EIDM parameter at its default · H5a/b, H3a/b = + lcAssertive 1.5 / 3.0 | the same model as the cars, truck geometry | — | 0.5 or 0.2 s | speedFactor (+ EIDM/driverstate stochastic errors) | `m3:29-48` |
| **compliance** | `car_c`: speedFactor `normc(1.0, 0.05, 0.8, 1.2)`; `car_n`: `normc(1.15, 0.05, 0.95, 1.4)`; share p_nc (default 0.3) | trucks `normc(1.0, 0.05, 0.8, 1.2)`, share default 0.1 | — | — | per vehicle | `m3:59-81` |
| **CAV** (Rounds 3–4) | — | — | `cav`: `carFollowModel` CACC (or ACC), **all ACC/CACC parameters at their defaults**, length 5, maxSpeed 33.33, **speedFactor 1.5**, speedDev 0, no vClass, LC2013 defaults; cav_share p ∈ {0.10, 0.25, 0.50} planned, 0.25 run; truck share rescaled so that trucks stay 10 % of all vehicles; **all CAVs are cars** | 0.2 s (Round 3 Addendum A) | none | `m3:51-56, 63-65`; `lab/round3_tm21_protocol.md:26-30` |
| **CORR2** | MRG3 `vtypes_xml`, driver **H5**, p_nc 0.3 | 0.1 | none | 0.2 s | speedFactor | `corr2.py:3-5, 51, 65-79` |
| **RING22** | vType attributes only bound the kinematics (`minGap 0`, accel 5, decel 9, emergencyDecel 9, sigma 0, sf 1, sd 0, maxSpeed 30). Behaviour is Python IDM (v0 30, T 1, a 1, b 1.5, δ 4, s0 2) + Gaussian acceleration noise N(0, 0.2) × √dt; speedMode 6 | none | 1 AV (FollowerStopper / PI-saturation / RL) | 0.1 s | acceleration noise; ±1 m position jitter | `ring.py:1-20, 32-42, 109-120` |

SUMO options [CODE]:
- **vsl_lab** (`vsl_lab/sim/runner.py:101-105`): `--time-to-teleport 300`, `--collision.action warn`, `--collision.check-junctions false`.
- **v5** (`ei:418-421`): `--time-to-teleport -1` (teleports disabled, so gridlock is hidden), `--collision.action warn`, `--step-method.ballistic`.

---

## 3. Q2: how "each vehicle has its own characteristics" is implemented, and whether it reaches SUMO

**Mechanism (v5).**
1. Each scenario seed builds a **discrete library** of 100 vTypes with independently sampled parameters (`vf:236`; RandomState(seed)).
2. Each departing vehicle samples, in order: class (FLEET_MIX), then CAV vs HDV (`rng.random()*100 < cav_pct`; `sp:368`, `sh:147`), then reckless with p = 0.02, then a uniform variant index (`vf:388-401`).

So "own characteristics" means **1 of 10 HDV variants (or 1 of 5 CAV variants) per class**, plus SUMO's per-vehicle speedFactor draw (speedDev) and Krauss sigma noise. It is **not** per-vehicle vTypes, **not** `vTypeDistribution`, and **not** per-vehicle sampled accel, tau or minGap. The library is re-sampled every episode (on-the-fly: seed = `_seed_u32(ep_seed, 10_000)`, `ei:295`), so diversity exists *across* episodes, not only within them.

**Realised mix in the committed pool** (`scenario_0000_D6460_R24%_clear_s0.rou.xml`, 6,491 vehicles) [FILE]:
- 100 vTypes;
- CAV share 0.4996;
- class mix 70.7 / 11.9 / 11.6 / 5.8 %;
- reckless 50 / 3,248 HDVs = 1.5 %.

**What reaches SUMO:**

| Feature | Reaches SUMO? | Evidence |
|---|---|---|
| `vf` vType library (training pools, evaluation) | **yes** | pool file vTypes match `vf:275-288` |
| HDV diversity at **100 % CAV** (headline: 10 of 15 v5 runs, all May 18–19) | **no HDV is spawned**, so all of it is inert | `per_lane_stochastic.yaml:16`; `training_runs/experiment_20260518_*`, `_20260519_*` `config.yaml` (cav 100, pool `_cav100`); thesis plan `docs/plans/phd_thesis_plan_v0.md:542` ("HDV variants present in the fleet but not spawned") |
| HDV diversity at 50 % CAV (5 runs, May 16–17) | yes | catalog `docs/experiment_catalog.md:95-102` |
| HDV response to the VSL (Box(4), the default `use_box5: false`) | **no**: no lane or edge limit is ever changed; HDVs only follow CAVs | `ei:502-588`; `per_lane_stochastic.yaml:47` |
| HDV "92 % comply / 8 % ignore" (Box(5)) | **no**: not implemented. Box(5) is a plain `edge.setMaxSpeed`, so ~100 % comply × speedFactor | `ei:526-530`; `r44_action_v2.py:13-16, 190-193`; docs `dl/control_loop.md:88-93`, `dl/slowDown_argument.md:89`, `dl/speed_harmo_approach_v1.md:152-160` |
| Even the documented 8 % mechanism would not have worked | — | `dl/control_loop.md:93` uses `vehicle.setMaxSpeed(veh, 33.33)` to "ignore the sign", but vehicle maxSpeed does not override the lane limit × speedFactor [INF/VERIFY SUMO desired-speed rule] |
| v4 fc/uc/nc compliance groups | **no** (dead path) | §2.3 |
| Weather (training) | HDV: yes · CAV: accel, decel, minGap only · **at 100 % CAV only CAV traction** | `vf:343-351` |
| Weather (evaluation) | **no**, always clear | `sh:114`; `evaluate_models.py:87-98` |
| Reckless "~1 collision per 72–120 episodes" target | **not shown**. Krauss keeps safe gaps (audit `docs/audit_2026-05-20_fresh_thread.md:136`), and no collision result for reckless drivers is committed | `vf:140-141`; commit `eba2ce0` message |
| `ramp_spike` anomaly vehicles | **probably none inserted**: `typeID="HDV"` is not among the 100 vTypes; the exception is swallowed | `ai:193-205` [INF; also `docs/plans/vsl_hybrid_screen_v0.md:76-79`] |
| vsl_lab speedFactor groups | yes, checked behaviourally | `m3:76-81`; R-0 hashes differ (`lab/t2_realism_protocol.md:125`) |
| vsl_lab unknown vType attributes (e.g. H4 errors) | guarded: "SUMO silently ignores unknown vType attributes", so every variant is checked for INERT | `m3:26-28` (comment at `m3:27`); `lab/t2_realism_protocol.md:50-52`; STATUS item 10 |

**Docstring drift in `vf`.** The header says reckless 3–5 %, sigma 0.6, tau 0.6–0.9, minGap × 0.5–0.7 and speedFactor 1.15–1.25 (`vf:6-7, 19-25`). The code says 2 %, 0.5, 1.0–1.2, × 0.75–0.90 and 1.08–1.15 (`vf:133-142`). Commit `eba2ce0` tamed the reckless parameters and left the docstring stale. `NORMAL_HDV["share"] = 0.96` is unused (`vf:130`): normal = 1 − 0.02 = 98 %.

The thesis plan claims "140 vehicle types across 3 compliance groups" (`phd_thesis_plan_v0.md:542`). The code produces 100.

---

## 4. Q3: CAV modelling

| Aspect | v5 (`vf` + `ei`) | vsl_lab BN4 | vsl_lab MRG3 / LD3 (Rounds 3–4) |
|---|---|---|---|
| **Penetration** | 50 % (5 runs, May 16–17); **100 %** (10 runs, ADR-008). A 50 / 75 / 100 sweep was planned (`dl/speed_harmo_approach_v0.md:92`) but never run | 10 % (T1), 25 % (T1-B) | planned 10 / 25 / 50 % (`round3_tm21_protocol.md:13`); **only 25 % run** (Round 4 T-H); T-CAV0 and T-X never ran (`round4_harmonisation_protocol.md:58`) |
| **Car-following model** | **Krauss**, sigma 0, tau 1, minGap × 0.5 (not ACC/CACC) | IDM = the human model with speedFactor 1 | SUMO **CACC** (ACC as a fallback check), every parameter at its default |
| **Identification** | `"cav" in vtype.lower()` each actuation step (`ei:615`). Works because `slowDown` does not rename the vType [INF] | **by ID**: after `setMaxSpeed` SUMO renames the type to `av@<id>`; the earlier type-based test silently disabled the actuator (`bn4_env.py:323-325`; STATUS item 5) | by ID (`cav_staircase.py:3-4`) |
| **Actuation** | `traci.vehicle.slowDown(v, limit, 30 s)` every 5 s on seg_2/1/0_before (per lane on seg_0, and on seg_1 for Box(7)) and ramp approach/transition; released downstream (`ei:57-68, 540, 582-648`). Docs say "every step" (`dl/slowDown_argument.md:19`; `ei:9`); the code is every 5 steps | `vehicle.setMaxSpeed(av, max(cap, v − 1.5·dt, 0.5))` per lane-piece slot (`bn4_env.py:205-212`) | arms B/C: **set-speed staircase** `vehicle.setMaxSpeed` in 1 km/h steps, at most one step per X s, and only once the CAV has reached its set speed (`cav_staircase.py:34-70`; X = 1 s provisional). Arm P: `vehicle.setSpeed(PI-with-saturation)`, released by `setSpeed(-1)` (`vsl_lab/jobs/mrg3_run.py:179-191`) |
| **Compliance of the CAVs** | 100 % by construction | 100 % | arm B: exact (target = posted lane limit); **hazard:** with `speedFactor 1.5`, a CAV run without the staircase (`cav_arm` "none") would drive 1.5 × any posted limit, capped at 33.33 (`m3:55`; `mrg3_run.py:162`) [INF] |
| **Human compliance** | Box(4): 0 % (never shown the VSL). Box(5): ~100 % via speedFactor 1.00 ± 0.05 (reckless 1.08–1.15) | all drivers via `lane.setMaxSpeed` (track A); posted VSL does not bind on BN4 (A-T0 FAIL) | `car_n` share p_nc drives `normc(1.15, 0.05)` × posted limit, i.e. proportional over-speed, not "ignore the sign" |

**CAV results (vsl_lab).**

*Step-length artefact* (`round3_tm21_protocol.md:113-130`; throw-away seed, single runs):
- At 0.5 s, CACC 25 % produced 23 CAV emergency brakings and ACC 25 % produced 79, against 0–2 for humans.
- At 0.2 s and 0.1 s this fell to 8–9 per run.
- Door-to-door time at 0.2 s: CACC 25 % 367 s against 392 s human-only. This is MRG3-H0, one seed, not evidence.

*LD3 / H5, 30 seeds* (`round4_th.md:9, 18-20, 25, 34-35`):
- NC with 25 % CACC was **+93.0 %** delay at 3,900 and **+45.7 %** at 4,500, against NC-human.
- `cavconst:0.6`: +7.5 % / +3.8 % delay, and stops got worse.
- `cavpi` (PI-saturation on every CAV): +180 % / +119 % delay.
- The CAV arms showed no authority, so TM21 was parked (`round4_harmonisation_protocol.md:93`; `STATUS.md:29`). The share of this due to a SUMO CACC artefact rather than real ACC string instability was **not tested** (`round4_harmonisation_protocol.md:68`).

*BN4 AV caps* (`lab/t1_bn4_plant_checks.md:39-48, 59-68`; `STATUS.md:23-26`):
- 10 %, T0: caps do not bind once the bottleneck has broken down (Δ outflow −6.3 % to +1.6 %, CIs include 0).
- Preventive caps (T0b) **lower** outflow by 3–16 %, so they have authority only to hurt.
- 25 % AVs: DRL beat the tuned constant cap in 0 of 3 cells.

**v5 CAV actuator weakness.** [CALC + VERIFY that `slowDown` is a linear ramp over `duration` that restarts on each call.] Re-issuing a 30-s `slowDown` every 5 s closes 1/6 of the remaining gap per call. That leaves (5/6)^6 ≈ 33 % of the gap after 30 s and about 11 % after 60 s. A CAV crosses the 1 km per-lane zone `seg_0_before` in about 30–40 s, so it is released before it reaches its command. Per-lane "differential" commands were therefore heavily smoothed.

---

## 5. Q4: what the realism gates found, and which heterogeneity settings mattered for headroom

### 5.1 Driver models vs capacity drop (vsl_lab Track 2)

| Plant / variant | Breakdown? | Capacity drop | Waves (km/h) | Origin at bottleneck | Artefacts | Source |
|---|---|---|---|---|---|---|
| MRG3-v1 Krauss (SUMO defaults) | **none** up to 6,000/600; share 0.2 at 6,000/900 | 0.976 (max-based, biased) | — | — | 0 teleports | `lab/t2_mrg3_calibration.json`; `lab/t2_mrg3_r1.md:5-7` (R1 at 6,000/900: share 0.0, T0 FAIL −3.9 %) |
| MRG3-v2 IDM, departSpeed max | none | — | — | — | insertion failure; 6–12 teleports / 10 runs; door-to-door 1,100–1,670 s | `lab/t2_mrg3_calibration_v2.json` |
| MRG3-v3 IDM, departSpeed avg (= H0) | share 0.8–1.0 everywhere | 0.95–1.04 (biased) | — | — | **4–8 teleports / 10 runs: ramp vehicles stranded at the acceleration-lane end** ("wrong lane", > 300 s) | `lab/t2_mrg3_calibration_v3.json`; `lab/round2_protocol.md:117-129` (cause at `:121`) |
| H1 (IDM + ASL 1 s), 0.2 s | share 1.0 | not computable (no free runs) | −15.8 | 1.00 | teleports 2/5, FAIL 2/5; discharge 1,417 | `lab/t2_realism_step0.2.md:8` + json |
| H2 (driverstate 0.7), 0.2 s | — | — | — | — | no eligible cell (teleports / FAIL) | same, row H2 |
| H3 W99, 0.2 s | share 0.8 | **1.056 [1.002, 1.081]: no drop** | −18.0 | 0.89 | 0 teleports; FAILs in the stress cell | same, row H3 |
| H4 EIDM + large errors | **collapsed**: discharge 185 veh/h/lane, not drained (0.5 s); door-to-door 5,784 s (0.2 s) | — | −7.2 | origin up1 | — | `lab/t2_realism_protocol.md:127-135, 188-197` |
| H5 EIDM defaults, 0.2 s (merge) | share 0.25 at its cell | n/a (1 run with an onset) | −16.9 | 1.00 | clean; discharge 1,564 | `t2_realism_step0.2.md:11` |
| H5a / H5b (lcAssertive 1.5 / 3.0) | share 0.25 | 1.011 [1.000, 1.027] (H5b) | −16.4 | **0.54 / 0.15** | onsets move to the entry ("waves from nowhere") | `lab/t2_realism_d3.md:7-8`; `round2_protocol.md:167-170` |
| H3a / H3b | 0.10 / 0.95 | — | −18.9 | **0.50 / 0.00** | same | `t2_realism_d3.md:9-10` |
| LD3 (3 → 2 lane drop): H0 | — | — | — | — | stranded at the dropping-lane end; teleports | `t2_realism_ld3.md:9`; `round2_protocol.md:177-178` |
| LD3: H5 | share 0.6 | n/a (0 + 8 runs) | −16.4 | 1.00 | clean; stopped share 0.18 | `t2_realism_ld3.md:7` |
| LD3: H3 | 0.65 | 1.037: no drop | −18.9 | 1.00 | FAIL 14 in the stress cell | `t2_realism_ld3.md:8` |
| ZM3 zipper: **H5** | 0.80 | **0.967 [0.923, 0.982]: PASS** | −16.9 | 1.00 | **discharge 1,528 < 1,600: R-c FAIL** (the only failing check) | `t2_realism_zm.md:7`; json |
| ZM3: H3 / H0 | 0.65 / 0.95 | — | −18.0 | 0.83 / 1.00 | discharge 1,489 / 1,407 | `t2_realism_zm.md:8-9` |
| BN4 IDM, LC off (Vinitsky) | yes | **0.862** (1,044 → 900 veh/h), PASS | — | — | 0 teleports; the outflow plateau is exactly 900 (min 893, max 907) for q ≥ 1,400 [INF: a suspiciously discrete discharge, not investigated] | `lab/t1_bn4_plant_checks.md:5-33` |
| BN4-L (LC on) | yes | 0.698 (exploratory) | — | — | — | same, `:35-37` |

**Lessons for the heatmap:**
- **Waves are robust** across IDM, EIDM and W99.
- **The capacity drop depends on the driver model and is mostly an artefact.** IDM's drop coexists with stranding teleports. W99 has none. EIDM defaults rarely break down at a merge, because ramp drivers yield (`lab/t4_corr2_protocol.md:28`).
- **Increasing lane-change assertiveness**, the obvious "diversity" lever, produced unrealistic origins.
- **The reported 0.5 s verdict file `lab/t2_realism_verdict.json` is not in the repo.** Only the 0.2 s and later verdicts are committed. The md files still point to it (`t2_realism_*.md` last line).

### 5.2 Heterogeneity as a source of adaptivity headroom

**Round 4 Addendum E** (LD3, H5, 0.2 s; J = delay + 40 s/stop; 10 seeds; `lab/round4_gscan.md:7-27`; `lab/round4_harmonisation_protocol.md:226-277`):

| Family | Conditions | Best b per condition | G (= H) |
|---|---|---|---|
| compliance p_nc | C1 0.1 / D3 0.3 / C2 0.5 | 0.75 / 0.8 / 0.8 | **0.8 %** |
| truck share | K1 0.05 / D3 0.10 / K2 0.20 | 0.7 / 0.8 / 0.85 | **4.0 %** (largest of all families) |
| demand | 3,300–5,100 | nc / 0.8 / 0.8 / 0.75 | 2.2 % |
| incident | ± incident at 3,900 / 4,500 | — | 2.5 % / 1.4 % |

- The truck share moves the best limit monotonically (0.70 → 0.85), but a pooled constant is still within 4 % of the oracle.
- p_nc barely changes NC (J 499 / 535 / 504) and the best b (`round4_gscan.md:26`).
- The tuned adaptive rule is worse than the pooled constant in every family.

Other uses of the same knobs:
- **P-H DRL training** used p_nc ∈ {0.1, 0.3, 0.5} as a hidden condition (`round4_harmonisation_protocol.md:136`; `vsl_lab/envs/mrg3_env.py:12, 149`). Screening failed.
- **The CORR2 headroom scan** (H5, p_nc 0.3, trucks 0.1) varied only demand: G = 0.4 % (`lab/t4_gscan.md:5`).

**Never tested** [CODE/DOC]:
- the screen's Card A hidden condition, the **"driver-population class"** (tau, accel, lcAssertive / lcCooperative per vType; `docs/plans/vsl_hybrid_screen_v0.md:357-360`);
- per-vehicle tau, accel or minGap heterogeneity in vsl_lab;
- weather or CAV share as hidden conditions;
- CAV penetration sweeps beyond one value per track.

**v5:** no headroom gate was ever run. NC never broke down in evaluation: 83–86 km/h, 1.3 % of windows congested (`vsl_hybrid_screen_v0.md:48, 60`).
- [CALC, steady-state Krauss spacing ≈ length + minGap + v·tau, ignoring sigma and trucks] A 100 %-CAV car stream (4.5 m, minGap 1.25, tau 1.0) at 120 km/h carries about **3,070 veh/h/lane**. Normal HDVs (minGap 2.5, tau 1.6) carry about 1,990.
- So the 100 %-CAV fleet (σ = 0) has about 50 % more capacity than the HDV fleet [INF]. That is one more reason the headline plant never jammed, besides the evaluation demand cap (one Bernoulli draw per second per route caps the mainline at 3,600 veh/h; `sh:120-131`).

---

## 6. Q5: bugs, inconsistencies, design weaknesses; what to reuse

### 6.1 Defects (ranked by impact on the research question)

1. **Headline fleet inert:** 100 % CAV removed every HDV characteristic. "Diversity" then meant 4 lengths, 2 truck speed caps and σ = 0 Krauss. There was nothing for the controller to adapt to [CODE/FILE §3].
2. **Binary compliance** (CAV 100 %, HDV 0 % in Box(4)). The documented 92 / 8 model is absent (§3). The v4 three-group model is dead (`rw:30, 112-140, 637-645`).
3. **The CAV dynamics model is not a CAV model.** It is Krauss with σ = 0, tau 1 and half the minGap: no ACC/CACC dynamics, no string-stability property. It is also actuated by `slowDown`, whose re-issue pattern is sluggish (§4) [CALC/VERIFY].
4. **Train/eval mismatch on fleet conditions.** Weather 70/20/10 in the training pools, always clear in evaluation (`sh:114`). On top of that, the demand cap above (`sh:120-131`).
5. **`--time-to-teleport -1`** in v5 (`ei:421`). A stranded ramp vehicle would never show up. This matters because normal HDVs are timid mergers (lcAssertive 0.5–1.0, lcStrategic 0.4–0.7), and vsl_lab saw the stranding pattern at the same acceleration-lane geometry (`round2_protocol.md:121`) [INF: not measured in v5].
6. **`insertionChecks="none"` + `departPos="last"` + `departSpeed="desired"`** in every v5 route writer (`sp:370-375`; `sh:91-94, 149-152`; `rw:850-861`). Unsafe insertions are possible [VERIFY SUMO semantics]. The collision count is reported as "structurally 0" (audit `:136`).
7. **`ramp_spike` injects an undefined vType `HDV`** (`ai:198`), so it is probably a no-op [INF]. Even if it worked, it would add HDVs into a 100 %-CAV world. `speed_reduction` and Box(5) both write `edge.setMaxSpeed("seg_1_before")` and overwrite each other. Deactivation resets the edge to 120 km/h, overriding any posted VSL for the rest of the window (`ai:150, 172`; `ei:528`) [CODE].
8. **Weather silently changes `actionStepLength`** for HDVs: 2–3 s decision intervals in fog (§2.2). The CAV/HDV speed gap in fog is 90 vs 120 km/h. Neither was documented as intended.
9. **Docstrings and plans disagree with the code:**
   - reckless parameters (`vf:6-7, 19-25` vs `:133-142`);
   - "140 vTypes" (`plan:542`) vs 100;
   - "every step" (`dl/slowDown_argument.md:19`; `ei:9`) vs every 5 steps (`ei:540`);
   - "92 % comply" (`r44_action_v2.py:16`).
10. **Unused or unseeded machinery in dead code:**
    - `rw` uses unseeded global `np.random`;
    - `sg` seeds from Python `hash()` of strings (`sg:567, 589`), which differs per process unless `PYTHONHASHSEED` is fixed [VERIFY];
    - the sigma weather FIXME (`rw:332-333`);
    - `sigma_scale_range` is resolved but unused (`rw:228`);
    - `BASE_SPECS.sigma` is unused (`vf:63, 73, 83, 93`);
    - `NORMAL_HDV.share` is unused (`vf:130`).
11. **The reckless outliers cannot do their stated job.** "Collision 1 / 72–120 episodes" (`vf:140-141`) contradicts Krauss's safe-gap design. They are 1.5 % of HDVs (0 at 100 % CAV) [FILE].
12. **vsl_lab latent hazard:** the `cav` vType has `speedFactor 1.5` (`m3:55`). It depends on the staircase being active (`mrg3_run.py:162`). A CAV run with posted VSL and `cav_arm` "none" would make the CAVs non-compliant [INF].
13. **vsl_lab realism of CAVs.** CACC/ACC at their defaults. The 0.5 s artefact was caught. At 0.2 s the +46–93 % delay was never separated into "SUMO CACC artefact" vs "real ACC instability" (`round4_harmonisation_protocol.md:68`).
14. **vsl_lab missing artefact:** `lab/t2_realism_verdict.json` (the 0.5 s gate) is referenced but not committed (§5.1).
15. **Narrow, single-axis diversity in vsl_lab:** desired speed per vehicle only; all cars of a group share accel, decel, tau and minGap; all CAVs are cars. Real per-driver heterogeneity in reaction and acceleration (the author's "own characteristics") is absent [CODE].
16. **Pool portability:** the committed pool `.sumocfg` files hold absolute net paths into the *other* mirror (`/home/catalin/work/...`). The pools actually used for training (`shared_seed42_n200*`) are not committed, so their fleet and weather cannot be audited [FILE].

### 6.2 Worth reusing

| Item | Why | Where |
|---|---|---|
| `m3.vtypes_xml` pattern: `vTypeDistribution` + per-vehicle `normc` speedFactor groups + truck share kept constant when CAVs are added | compact, observable knobs (p_nc, truck share) that SUMO samples per vehicle; field-style proportional non-compliance (cf. Hegyi's α, `vsl_hybrid_screen_v0.md:266`) | `m3:59-81` |
| `DRIVERS` registry + realism gate (R-0 inert check, R-a..R-d) | turns "driver model" into a pre-registered plant axis with behavioural checks; catches silently ignored vType attributes | `m3:29-48`; `lab/t2_realism_protocol.md` |
| CAV tracking by ID; set-speed staircase; per-vehicle `setMaxSpeed` as the ACC set-point | avoids the `av@<id>` rename trap; actuates through the vehicle's own ACC (TM21-faithful) | `cav_staircase.py`; `bn4_env.py:323-325` |
| Common random numbers for the CAV share (one RNG draw per vehicle whatever `av_share`, so arrivals are identical across shares) | penetration sweeps become paired | `vsl_lab/sim/demand.py:52`; `m3:87` |
| v5 class table (lengths, accel/decel/maxSpeed ranges) and the weather multiplier table | a ready-made generator for a "fleet / weather class" hidden condition. **Unvalidated**; needs R-0-style behavioural checks and a realism re-check | `vf:55-104, 160-193` |
| v5 LC "reckless" ranges | a candidate assertive-population knob. **Caution:** D-3 showed lcAssertive 1.5–3 moves onsets to the entry | `vf:115-120`; `t2_realism_d3.md` |

**Do not reuse:** `rw` / `sg` (dead, unseeded); Krauss σ = 0 as a "CAV"; the `slowDown` 30 s / 5 s pattern; `--time-to-teleport -1`; `insertionChecks="none"`; the binary compliance model; the anomaly `ramp_spike`.

---

## 7. Axes for the heatmap (values actually exercised)

| Axis | Values tried | Pipeline | Outcome |
|---|---|---|---|
| CAV penetration | 50 %, 100 % | v5 (Krauss-σ0 CAV, `slowDown`) | 100 % headline: TTS +23 % vs NC; no breakdown (`vsl_hybrid_screen_v0.md:45, 48`) |
| AV share | 10 %, 25 % | BN4 (IDM AV, `setMaxSpeed` caps) | caps cannot help after breakdown; DRL ≈ NC; meter wins (`STATUS.md:23-26`) |
| CAV share × model | 25 % CACC (+ ACC smoke) | LD3 / MRG3 | +46–93 % delay; no authority; parked |
| CAV step length | 0.5 / 0.2 / 0.1 s | MRG3 smoke | 0.5 s gives an emergency-braking artefact |
| Human compliance p_nc | 0.1 / 0.3 / 0.5 | MRG3 / LD3 (speedFactor groups) | G 0.8 % |
| Truck share | 0.05 / 0.10 / 0.20 | LD3 | G 4.0 % |
| Driver CF model | Krauss, IDM, IDM + ASL, IDM + driverstate, W99, EIDM (± errors) | MRG3 / LD3 / ZM3 | waves OK; no artefact-free capacity drop |
| LC assertiveness | lcAssertive 1 / 1.5 / 3 | MRG3 (H5, H3) | waves from nowhere |
| Human desired-speed spread | sd 0.05 (v5, MRG3); 0.2 (BN4) | — | not varied as a factor |
| Reckless share | 2 % (fixed) | v5 | inert at 100 % CAV |
| Weather | clear / rain / fog (70/20/10) in training; heavy_rain unused | v5 pools | never evaluated |
| Per-vehicle accel / tau / minGap spread | 10 variants per class (v5 only) | v5 | inert at 100 % CAV; never tested as a condition |

---

## 8. Open items to verify (not resolved here)

- **SUMO semantics** [VERIFY]:
  - `slowDown`: linear ramp, behaviour on re-issue, what happens after `duration`;
  - desired speed = min(maxSpeed, speedFactor × lane limit), and whether `vehicle.setMaxSpeed` can override a lane limit;
  - the effect of `insertionChecks="none"`;
  - LC2013 defaults;
  - the vClass `trailer` / `truck` defaults for `emergencyDecel`;
  - the default speedFactor cut-offs when `speedDev` is given without `normc` (relevant to v4's sd 0.6).
- **Whether v5 had stranded ramp vehicles.** Not visible with teleports disabled; it needs a run with `--time-to-teleport 300` on ramps_v2 with the v5 fleet. Not run here (read-only task).
- **The BN4 900 veh/h discharge plateau** (exact, low spread). Its cause was not investigated in the repo docs I read.
