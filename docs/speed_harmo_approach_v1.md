# Speed Harmonisation Research v5.1: Mixed Lagrangian-Eulerian Control with Distributional Reinforcement Learning

**Document version:** v5.1
**Date:** 2026-03-20
**Status:** Research Plan — post-feasibility
**Supersedes:** speed_harmo_approach_v0.md (v5.0)

---

## Table of Contents

1. [Evolution from v5.0: Empirical Findings](#1-evolution-from-v50-empirical-findings)
2. [Network Topology: ramps_v2](#2-network-topology-ramps_v2)
3. [Infrastructure Layout: VSL Placement and Sensing](#3-infrastructure-layout-vsl-placement-and-sensing)
4. [MDP Specification](#4-mdp-specification)
5. [Algorithm Selection: SAC and TQC](#5-algorithm-selection-sac-and-tqc)
6. [Stochastic Demand and Anomaly Injection](#6-stochastic-demand-and-anomaly-injection)
7. [Experimental Protocol](#7-experimental-protocol)
8. [References](#8-references)

---

## 1. Evolution from v5.0: Empirical Findings

The v5.0 design (documented in `speed_harmo_approach_v0.md`) proposed QR-DQN with a 7-level discrete action space on a 4→3 lane-drop topology. Two comprehensive feasibility sweeps — 990 scenarios each on the ramps_v1 and ramps_v2 topologies — revealed structural problems that necessitated a complete redesign of the environment, action space, and algorithm selection.

### 1.1 The 4→3 Lane-Drop Was the Wrong Bottleneck

The original merge_4_to_3 topology produced congestion through forced lane-change gap acceptance — a microscopic, stochastic process that upstream VSL cannot influence. Feasibility data (990 scenarios, demands 3000–10000 vph, 9 mainline × 6 ramp speed levels) showed:

- **No breakdown at any demand level** under no-control conditions — the network was unconditionally stable.
- **Every VSL combination caused equal or worse performance** at demands ≤ 6000 vph — the VSL created congestion that did not exist without it.
- **Above 6500 vph**, VSL reduced speed variance by 30–65% but at 8–10% flow loss — demand suppression, not harmonisation.

The root cause: the 4→3 lane-drop congestion mechanism is gap-acceptance driven, not flow-rate driven. Upstream speed control cannot create gaps in the dropping lane; it can only slow vehicles that would have merged successfully anyway.

### 1.2 The Ramps_v1 Topology Had a Dead Ramp Lane

The ramps_v1 network included a 4-lane buffer zone (seg_0_after) where lane 0 was a dedicated ramp weaving lane with an off-ramp escape valve. Lane diagnostic analysis confirmed:

- Lane 0 of seg_0_after carried only 27–29% of flow (below the 33% balanced share).
- Ramp vehicles either merged into lanes 1–3 or exited via the off-ramp — neither outcome was affected by upstream VSL.
- The mainline vehicles passed through lanes 1–3 unimpeded.
- The ramp VSL had **zero measurable effect** on any metric at any demand level.

### 1.3 The Static Optimum Was Trivially Simple

On the ramps_v2 topology (corrected: 3-lane merge, no off-ramp, ramp merges to lane 0 with yield), a uniform M110 (110 kph on all segments) achieved:

| Demand range | σ reduction vs NC | Braking reduction | Hard braking reduction | Flow loss |
|---|---|---|---|---|
| 5000–6750 vph | 17–33% | 28–41% | 40–57% | < 0.4% |

This was optimal across the entire trainable demand range. An RL agent would converge to "always output 110 kph" within 50 episodes — **no learning required**. The problem was too easy because: (a) demand was flat (constant rate), so the optimal policy was time-invariant; (b) the action space was 1D uniform (same speed for all lanes), so there was no differential control to discover; and (c) there were no stochastic disruptions, so the return distribution was unimodal.

### 1.4 Design Responses

These findings motivated three simultaneous changes:

| Problem | v5.0 design | v5.1 design |
|---|---|---|
| Bottleneck mechanism | 4→3 lane-drop (gap-acceptance) | Ramp-on merge to lane 0 (flow competition) |
| Action space | Discrete(7) or Box(2) uniform | Box(4)/Box(5) per-lane differential |
| Demand profile | Flat (constant rate) | Stochastic (ramp-up/peak/ramp-down + anomalies) |
| Algorithm | QR-DQN (discrete distributional) | TQC (continuous distributional) vs SAC |
| Ramp lane | Dedicated lane 0 + off-ramp | Shared lane 0 (ramp yields to mainline) |

---

## 2. Network Topology: ramps_v2

### 2.1 Geometry

The ramps_v2 network is a 5.5 km 3-lane highway with a single on-ramp merge. All segments have 3 lanes; there is no lane drop, no dedicated ramp lane, and no off-ramp.

```
Traffic flow →

km  0.0        0.5        1.0        1.5        2.0     2.5     3.0        3.5
    |          |          |          |          |       |       |          |
    J0─────────J1─────────J2─────────J3─────────────────J4──────J5─────────J6
    seg_3_before  seg_2_before  seg_1_before      seg_0_before    seg_0   seg_1
    (1000m, 3L)   (1000m, 3L)   (1000m, 3L)       (1000m, 3L)   _after   _after
                                                                 (500m)   (1000m)
                                                                   ↑
                                                     ramp_on_approach (700m, 1L)
                                                     ramp_on_transition (200m, 1L)
                                                     ramp_on_merge (100m, 1L, yield)
```

| Edge | Length | Lanes | Speed limit | Distance to merge (J4) |
|---|---|---|---|---|
| seg_3_before | 1000 m | 3 | 120 kph | 2500 m |
| seg_2_before | 1000 m | 3 | 120 kph | 2000 m |
| seg_1_before | 1000 m | 3 | 120 kph | 1500 m |
| seg_0_before | 1000 m | 3 | 120 kph | 0 m (ends at J4) |
| seg_0_after | 500 m | 3 | 120 kph | −500 m (downstream) |
| seg_1_after | 1000 m | 3 | 120 kph | −1500 m (downstream) |
| ramp_on_approach | 700 m | 1 | 90 kph | 300 m |
| ramp_on_transition | 200 m | 1 | 90 kph | 100 m |
| ramp_on_merge | 100 m | 1 | 90 kph | 0 m |

### 2.2 Merge Mechanism

At junction J4, two incoming edges compete for seg_0_after lane 0:

- `seg_0_before:0 → seg_0_after:0` with `state=M` (mainline priority)
- `ramp_on_merge:0 → seg_0_after:0` with `state=m` (ramp yields)

Ramp vehicles must find acceptable gaps in mainline lane 0 traffic to merge. Once on seg_0_after, they may lane-change to lanes 1–2 via SUMO's LC2013 model. There is no escape route — all vehicles exit via seg_1_after.

This creates a **flow-competition bottleneck** where the agent can influence merge dynamics by controlling the speed (and therefore headway spacing) of mainline lane 0 vehicles approaching J4. This is the mechanism studied by Li et al. [R25] (mainline VSL at I-880 ramp merge), Han et al. [R26] (VSL against jam waves at ramp merge), and Ko et al. [R24] (CAV speed harmonisation at merge).

### 2.3 Why 3 Lanes Throughout (Not 4→3)

The 4→3 lane-drop was discarded because:

1. **Gap-acceptance bottleneck vs. flow-competition bottleneck**: At a lane-drop, congestion forms because vehicles in the dropping lane cannot find gaps — a microscopic process uncontrollable by upstream VSL [§1.1]. At a ramp merge, congestion forms because ramp inflow competes with mainline flow for lane 0 capacity — a macroscopic process directly addressable by flow metering via speed control [R25], [R26].

2. **Observability**: The lane-drop merge outcome depends on individual vehicle gap distributions, which are not observable from aggregate E1 data. The ramp merge outcome depends on mainline lane 0 flow rate and speed, both directly measurable by E1 detectors at seg_0_before exit.

3. **Literature alignment**: Every successful RL-VSL study in the knowledge base uses a ramp-on merge or homogeneous freeway bottleneck — none use a pure lane-drop as the sole bottleneck [R3], [R4], [R10], [R24], [R25], [R26].

---

## 3. Infrastructure Layout: VSL Placement and Sensing

### 3.1 Control Zone Classification

The corridor is divided into five functional zones, consistent with Han et al. [R26] Area I–IV classification and SPECIALIST [R21] zone definitions:

| Zone | Segments | Function | VSL type |
|---|---|---|---|
| **Free-flow reference** | seg_3_before, seg_2_before | Uncontrolled; measures incoming traffic state | None |
| **Pre-conditioning** | seg_1_before | Uniform Eulerian VSL (posted sign + radar) | Physical |
| **Merge approach** | seg_0_before | Per-lane Lagrangian VSL (CAV slowDown) | Virtual |
| **Merge zone** | seg_0_after | Observation only; no control | None |
| **Downstream** | seg_1_after | Throughput measurement | None |
| **Ramp approach** | ramp_on_transition | Lagrangian VSL (CAV slowDown) | Virtual |

### 3.2 Physical VSL on seg_1_before: Eulerian Control

seg_1_before (1000–1500 m from merge) carries a physical overhead VSL gantry with radar speed enforcement, applying a **uniform speed limit to all vehicles** (HDVs and CAVs).

**Placement rationale:**

- **Distance from merge**: At 100 kph, vehicles entering seg_1_before reach J4 in 54 s (1.8 control steps). This provides sufficient lead time for the action to affect merge dynamics while remaining within the temporal credit assignment horizon of γ=0.99 [R12].
- **Deceleration distance**: 1000 m provides comfortable deceleration from 120 kph to any target ≥ 60 kph at a = 2.5 m/s² (Krauss model typical), requiring only 122 m for a 40 kph reduction. The remaining 878 m allows platoon spacing adjustment — essential for the flow-metering mechanism [R25], [R21].
- **MUTCD step-down constraint**: The posted speed must satisfy `v_seg1 ≥ max(v_seg0_L0, v_seg0_L1, v_seg0_L2) − 16 kph` (MUTCD §2C.08: maximum 10 mph step-down between adjacent signs). This is enforced as a hard constraint in the action space, not learned. MARVEL [R10] implements the same constraint: *"the maximum allowable speed limit difference between consecutive VSL gantries indicating slowdown patterns is 10 miles per hour"*.
- **Single gantry**: One overhead sign displaying one speed per direction. Per-lane physical signs exist (UK M25 managed motorway) but are rare; uniform posting is the standard assumption in the RL-VSL literature [R10], [R25], [R26].

**HDV compliance model:**

Real-world compliance with radar-enforced VSL is 90–95% (Hegyi & Hoogendoorn, 2010; MARVEL field data [R11]). Hua & Fan (2023) [R4] model imperfection at 50% compliance; with radar enforcement, compliance is substantially higher. The SUMO implementation:

- 92% of HDVs comply: Krauss car-following model follows `traci.edge.setMaxSpeed()` with 5% speed tolerance.
- 8% of HDVs ignore the sign: retain their free-flow `maxSpeed` (120 kph).
- CAVs comply at 100% via `traci.vehicle.slowDown()`.

This stochastic compliance creates **irreducible return variance** — the same action produces different outcomes depending on which HDVs comply. This is the primary source of distributional advantage for TQC over SAC [§5].

**Why seg_2_before is NOT controlled:**

seg_2_before is 2000–2500 m from the merge (72–90 s transit time = 2.4–3.0 control steps). At this distance: (a) the action effect arrives after the state has changed (stochastic demand shifts regime every 5–10 steps); (b) Han et al. [R26] define Area I (upstream of VSL control) as uncontrolled free-flow — it serves as a flow source, not a control zone; (c) SPECIALIST [R21] places VSL directly at the shock wave, not multiple kilometres upstream.

### 3.3 Virtual VSL on seg_0_before: Lagrangian Per-Lane Control

seg_0_before (0–1000 m from merge) receives **per-lane CAV speed commands** via `traci.vehicle.slowDown()`. Each lane has an independent speed target:

| Lane | Position | Control purpose |
|---|---|---|
| L0 (rightmost) | Merge lane — vehicles here encounter ramp traffic at J4 | Control merge gap spacing |
| L1 (middle) | Vehicles may lane-change to/from L0 | Inter-lane speed gradient management |
| L2 (leftmost) | Fast lane — least affected by merge | Independent speed; reduces cross-lane variance |

**Why per-lane here:**

1. **Physical proximity**: seg_0_before ends at J4 — per-lane speed differentials directly shape the merge. Vehicles are committed to their lane approach (limited lane-changing distance before J4).
2. **The inter-lane problem**: Feasibility data shows L0 is 7–13 kph slower than L2 under NC conditions. A uniform VSL (M110) reduces L2 from 120→110 but cannot differentiate — it wastes control authority on L0 (already slow). Per-lane control can slow L1–L2 toward L0, reducing the inter-lane speed gradient that causes dangerous lane-change manoeuvres at the merge.
3. **Literature precedent**: Wu et al. (2020) used differential per-lane VSL with DAC (deep actor-critic) because *"if we used discrete action space (e.g., DQN), we have to estimate the value function of all possible choices, which makes [it] unstable"*. Zhao et al. [R6] used TD3 for lane-level VSL in a CAV environment. Hua & Fan (2023) [R4] used DDPG with differential per-lane speed limits.
4. **CAV-only mechanism**: Per-lane control is feasible without physical signs because each CAV receives an individual digital command based on its current lane index. HDVs on seg_0_before are influenced indirectly through car-following behind CAVs [R3], [R24].

**Why NOT per-lane on seg_1_before:**

Lane changes between seg_1_before and seg_0_before erase any per-lane speed pattern set at seg_1_before. SUMO's LC2013 model redistributes vehicles based on the speed differential, so a slow-L2 pattern on seg_1_before would push vehicles to L0–L1 before reaching seg_0_before. Additionally, per-lane on seg_1_before would add 3 dimensions to the action space (Box(7) or Box(8)) for marginal benefit, degrading sample efficiency.

### 3.4 Virtual VSL on ramp_on_transition: Lagrangian CAV Control

The ramp transition segment (200 m, 100 m from merge) receives CAV speed commands. This controls the approach speed of ramp CAVs before they enter the merge curve.

**Why no physical sign on the ramp:**

- The ramp is 1 lane and only 200 m of controllable length. At 90 kph, a vehicle traverses it in 8 s — insufficient time for HDV perception–reaction–deceleration (minimum 300–500 m per MUTCD guidelines).
- MARVEL [R10] does not place VSL on ramps — only on mainline gantries.
- At 50% CAV penetration, every other ramp vehicle is directly controlled; the following HDV naturally matches the CAV's speed through car-following.

### 3.5 Sensor Infrastructure

The detector infrastructure provides 63 E1 induction loops and 10 E3 multi-entry-exit detectors, all aggregating at 30 s intervals:

**E1 detectors (per lane: entry + mid + exit positions):**

| Segment | Lanes | Loops | Purpose |
|---|---|---|---|
| seg_3_before, seg_2_before | 3 each | 18 | Free-flow reference; incoming demand measurement |
| seg_1_before | 3 | 9 | Pre-VSL and post-VSL compliance speed |
| seg_0_before | 3 | 9 | Per-lane state input for the agent |
| seg_0_after | 3 | 9 | Merge quality measurement |
| seg_1_after | 3 | 9 | Downstream throughput |
| ramp (3 segments) | 1 each | 9 | Ramp demand and speed |

**E3 detectors (per segment + corridor-level):**

| Detector | Measures |
|---|---|
| e3_seg_0_before | Travel time through merge approach (pre-conditioning effect) |
| e3_seg_0_after | **Travel time through merge zone** = direct merge delay measurement |
| e3_seg_1_after | Downstream clearance |
| e3_ramp_on_merge | **Halting count** = gap-wait measurement (ramp vehicles stopped waiting for merge gap) |
| e3_corridor | End-to-end travel time (full network) |

### 3.6 Infrastructure Diagram

```
Traffic flow →

    J0─────────J1─────────J2─────────J3─────────────────J4──────J5─────────J6
    seg_3       seg_2       seg_1       seg_0              seg_0   seg_1
    _before     _before     _before     _before            _after  _after

    ──────────────────────────────────────────────────────────────────────────
    UNCONTROLLED            ┌─PHYSICAL VSL─┐   ┌──VIRTUAL VSL──┐  OBSERVATION
    free-flow               │ posted sign   │   │ per-lane CAV  │  E1/E3 only
    E1/E3 reference         │ + radar       │   │ L0, L1, L2    │
                            │ HDV 92% + CAV │   │ CAV-only      │
                            │ uniform speed │   │ 3 independent │
                            │ Box(5) dim[4] │   │ Box dims[0-2] │
                            └───────────────┘   └───────────────┘
                                                            ↑ MERGE (J4)
                                                ramp_on_transition (200m)
                                                VIRTUAL VSL (CAV-only)
                                                Box dim[3]
```

---

## 4. MDP Specification

### 4.1 Action Space

Two experimental configurations:

**Box(4) — Pure Lagrangian:**

| Dimension | Controls | Range (kph) | Mechanism |
|---|---|---|---|
| a[0] | seg_0_before lane 0 | [60, 120] | CAV slowDown |
| a[1] | seg_0_before lane 1 | [60, 120] | CAV slowDown |
| a[2] | seg_0_before lane 2 | [60, 120] | CAV slowDown |
| a[3] | ramp_on_transition | [40, 90] | CAV slowDown |

seg_1_before receives `min(a[0], a[1], a[2])` as a passive uniform limit (CAV-only). seg_2_before is uncontrolled.

**Box(5) — Mixed Lagrangian-Eulerian:**

| Dimension | Controls | Range (kph) | Mechanism |
|---|---|---|---|
| a[0] | seg_0_before lane 0 | [60, 120] | CAV slowDown |
| a[1] | seg_0_before lane 1 | [60, 120] | CAV slowDown |
| a[2] | seg_0_before lane 2 | [60, 120] | CAV slowDown |
| a[3] | ramp_on_transition | [40, 90] | CAV slowDown |
| a[4] | seg_1_before (uniform) | [60, 120] | **Physical VSL sign + radar** (HDV 92% + CAV 100%) |

**Constraints:**
- Adjacent lane gradient: `|a[i] − a[i+1]| ≤ 10 kph` for i ∈ {0,1} (MUTCD safety).
- MUTCD step-down (Box(5) only): `a[4] ≥ max(a[0], a[1], a[2]) − 16 kph`.

**Why continuous, not discrete**: With 3 per-lane levels, a discrete formulation requires 7³ = 343 actions for seg_0_before alone. Adding the ramp: 343 × 6 = 2,058 actions. For QR-DQN at 25 quantiles: 51,450 output neurons. Wu et al. (2020) identified this as the primary motivation for continuous-action algorithms in per-lane VSL: *"if we used discrete action space (e.g., DQN), we have to estimate the value function of all possible choices, which makes [it] unstable for the DQN control problem."*

### 4.2 Observation Space — Box(0, 1, shape=(77,))

**3-frame stack × 24 features + 5 static features:**

| Index | Feature group | Features per frame | Source |
|---|---|---|---|
| 0–5 | Upstream aggregate | seg_2_before speed/flow/occ, seg_1_before speed/flow/occ | E1 exit |
| 6–14 | Merge approach per-lane | seg_0_before L0/L1/L2 speed/flow/occ | E1 per-lane exit |
| 15–17 | Merge zone | seg_0_after speed/flow/occ (aggregate) | E1 exit |
| 18–19 | Ramp | ramp_on_approach flow, ramp_on_merge speed | E1 |
| 20 | Downstream | seg_1_after flow | E1 exit |
| 21–23 | Regime | one-hot (FREE_FLOW, METASTABLE, CONGESTED) | RegimeDetector |

**Static features (appended once, outside stack):**

| Index | Feature |
|---|---|
| 72–75 | Previous action (normalised): a[0], a[1], a[2], a[3] |
| 76 | Anomaly active flag (0.0 or 1.0) |

The per-lane observations at seg_0_before (indices 6–14) are essential for the per-lane action: the agent must observe per-lane speed/flow/occupancy to make informed per-lane decisions. This follows the state design of Wu et al. (2020) and Zhao et al. [R6], who include per-lane detector readings when per-lane actions are available.

The `anomaly_active` flag is included because real-world traffic management centres have incident detection systems (camera feeds, probe vehicle alerts, automatic incident detection algorithms). The agent knowing an anomaly is active lets it learn reactive behaviour; without this flag, the agent would need significantly longer training to infer anomaly state from traffic patterns alone.

### 4.3 Reward Function — 5 terms

```
r_t = w_h · r_harmo + w_q · r_throughput + w_a · r_smooth + w_lg · r_lane_grad + w_m · r_merge
```

| Term | Weight | Formula | Purpose |
|---|---|---|---|
| r_harmo | 0.40 | `−min(σ_upstream / σ_max, 1)` | Upstream spatial + temporal speed variance reduction |
| r_throughput | 0.25 | `−max(0, 1 − flow_ds / flow_ref)` | Penalise throughput collapse at seg_1_after |
| r_smooth | 0.10 | `−‖Δaction‖₂ / ‖action_range‖` | Penalise oscillating commands (4D normalised) |
| r_lane_grad | 0.15 | `−min(max(|L0−L1|, |L1−L2|) / 20, 1)` | **New**: penalise inter-lane speed gaps at seg_0_before |
| r_merge | 0.10 | `−min(|L0_speed − ramp_merge_speed| / 30, 1)` | **New**: reward matching merge lane speed to ramp speed |

The 3-term core (r_harmo, r_throughput, r_smooth) follows MARVEL [R10]. The two new terms address the per-lane control problem: r_lane_grad discourages the agent from creating dangerous inter-lane speed differentials, while r_merge rewards reducing the speed mismatch at the merge point — the primary cause of merge shockwaves [R5], [R24].

---

## 5. Algorithm Selection: SAC and TQC

### 5.1 Why SAC

Soft Actor-Critic (Haarnoja et al., 2018) is the most reliable off-policy continuous-control algorithm in the SB3 ecosystem. Entropy regularisation prevents deterministic policy collapse — critical for a 4D action space where premature convergence to a single fixed output (e.g., "always post 110 kph") would fail under stochastic demand. SAC serves as the **non-distributional baseline** to isolate TQC's distributional contribution.

### 5.2 Why TQC

Truncated Quantile Critics (Kuznetsov et al., 2020) extends SAC with an ensemble of distributional (quantile) critics and truncates the top quantiles to control overestimation bias. TQC preserves the distributional RL contribution originally planned for QR-DQN (v5.0), but for continuous action spaces:

| Property | QR-DQN (v5.0) | TQC (v5.1) |
|---|---|---|
| Action space | Discrete only | Continuous (Box) |
| Return distribution | Z(s, a_k) per discrete action k | Z(s, a) for any continuous a |
| Overestimation control | Double DQN | Top-quantile truncation |
| Risk-sensitive inference | CVaR from quantile values | CVaR from quantile critics |
| SB3 availability | SB3-Contrib | SB3-Contrib |

**Why TQC should outperform SAC in this environment:**

1. **Bimodal returns from anomaly injection** (§6): 15% of episodes contain anomalies that dramatically change the return distribution. SAC's single Gaussian critic cannot represent bimodality; TQC's quantile critics capture both modes naturally.

2. **HDV compliance stochasticity** (Box(5) only): The physical VSL on seg_1_before produces stochastic outcomes due to the 8% HDV non-compliance rate. The same action a[4] produces a distribution of downstream speeds depending on which HDVs ignore the sign. TQC's distributional critics learn this variance; SAC averages over it.

3. **4D action overestimation**: Higher-dimensional continuous action spaces amplify overestimation bias in the critic [Kuznetsov et al., 2020]. TQC's truncation provides tighter value estimates, improving policy quality. This effect grows with action dimensionality — a 4D traffic action space is within the regime where TQC shows clear advantage over SAC on MuJoCo benchmarks.

4. **CVaR at evaluation**: TQC enables risk-averse action selection at inference: `a* = argmax_a CVaR_α[Z(s,a)]`. With α=0.10, this selects actions that are good in the worst 10% of outcomes — appropriate for a safety-critical traffic system where a single merge failure can cascade into network-wide congestion.

**No paper in the traffic control literature has applied TQC.** This is a directly publishable novel contribution.

### 5.3 Hyperparameters

| Parameter | SAC | TQC |
|---|---|---|
| Policy | MlpPolicy | MlpPolicy |
| learning_rate | 3e-4 | 3e-4 |
| buffer_size | 500,000 | 500,000 |
| batch_size | 256 | 256 |
| tau | 0.005 | 0.005 |
| gamma | 0.99 | 0.99 |
| ent_coef | "auto" | "auto" |
| net_arch | [256, 256] | [256, 256] |
| n_quantiles | — | 25 |
| n_critics | 2 | 5 |
| top_quantiles_to_drop_per_net | — | 2 |

### 5.4 Algorithm Comparison Matrix

| Algorithm | Action space | Distributional | Risk-sensitive | Role |
|---|---|---|---|---|
| No Control | — | — | — | Lower bound |
| Static M110 | Fixed uniform | — | — | Naive baseline |
| Rule-based (Hegyi-style) | M90 if METASTABLE else M120 | — | — | Classical baseline |
| DQN (Discrete 7) | Uniform discrete | No | No | Discrete baseline |
| **SAC** | Box(4) or Box(5) | No | No | Strong RL baseline |
| **TQC** | Box(4) or Box(5) | Yes (quantile critics) | Yes (CVaR) | **Primary** |

---

## 6. Stochastic Demand and Anomaly Injection

### 6.1 Why Stochastic Demand Is Necessary

With flat (constant-rate) demand, the optimal VSL policy is time-invariant — a fixed speed limit outperforms any adaptive controller because there is nothing to adapt to [§1.3]. Real traffic demand follows time-varying profiles with morning/evening peaks, random fluctuations, and occasional disruptions [R14], [R17].

Stochastic demand creates two conditions that justify distributional RL:

1. **Time-varying optimal policy**: The agent must learn to increase restriction during demand ramp-up, maintain it during peak, and release during ramp-down. A fixed policy cannot achieve this.
2. **Distributional return variance**: Episode-to-episode demand variation means the same policy produces different cumulative rewards depending on the sampled demand profile. TQC's quantile critics learn this distribution; SAC averages over it.

### 6.2 Demand Profile Generation

Each episode samples a demand profile with three phases:

```
Phase 1: Ramp-up    (0 → t_peak)      linear increase from base to peak
Phase 2: Peak       (t_peak → t_decay) sustained high demand with ±5% noise
Phase 3: Ramp-down  (t_decay → T)      linear decrease back to base
```

| Parameter | Distribution | Range |
|---|---|---|
| peak_demand_vph | Uniform | [5500, 8000] |
| base_fraction | Uniform | [0.4, 0.6] |
| ramp_fraction (of total) | Uniform | [0.20, 0.30] |
| t_peak (fraction of T) | Uniform | [0.15, 0.30] |
| t_decay (fraction of T) | Uniform | [0.65, 0.80] |

### 6.3 Anomaly Injection

15% of episodes contain a single anomaly injected during the peak phase:

| Anomaly type | SUMO mechanism | Duration | Effect |
|---|---|---|---|
| Ramp demand spike | Burst inject 2× ramp vehicles via `traci.vehicle.add()` | 60–120 s | Sudden merge overload |
| Speed reduction | `traci.vehicle.slowDown()` all vehicles on seg_1_before to 40 kph | 90–180 s | Simulates rubbernecking or debris |
| Lane closure (lite) | `traci.lane.setMaxSpeed("seg_0_before_2", 10/3.6)` | 120–240 s | Partial obstruction of fast lane |

The `anomaly_active` flag is observable in the state vector. Anomalies only start after warmup + 60 s minimum, ensuring the agent observes pre-anomaly normal flow.

**Why anomalies justify distributional RL**: Without anomalies, 100% of episodes follow the stochastic demand profile — the return distribution is unimodal (centred on the policy's response to that profile). With 15% anomaly rate, the distribution becomes bimodal: 85% of episodes cluster around "normal" returns, 15% cluster around "disrupted" returns. SAC's Gaussian critic averages these modes; TQC's quantile critics represent both, enabling risk-averse action selection during anomalies.

---

## 7. Experimental Protocol

### 7.1 Training

| Parameter | Value |
|---|---|
| Total timesteps | 1,000,000 |
| Steps per episode | 120 (3600 s / 30 s) |
| Episodes per training run | ~8,333 |
| Seeds per algorithm | 5 (seeds 0–4) |
| Evaluation frequency | Every 10,000 steps |
| Evaluation episodes | 20 (fixed demand profiles, 3 with pre-determined anomalies) |

### 7.2 Comparison Structure

| Experiment | Question |
|---|---|
| Exp 1: TQC vs SAC at Box(4) | Does distributional help in pure Lagrangian control? |
| Exp 2: TQC vs SAC at Box(5) | Does distributional help more with HDV compliance noise? |
| Exp 3: Box(4) vs Box(5) | Does the posted VSL add value beyond Lagrangian-only? |
| Ablation: Box(3) without ramp | Is ramp control contributing? |

### 7.3 Primary Metrics

| Metric | What it measures | TQC vs SAC prediction |
|---|---|---|
| Mean return | Overall policy quality | Comparable |
| **CVaR₁₀% return** | Return in worst 10% of episodes | **TQC higher** |
| Return std | Policy consistency | TQC lower |
| Anomaly episode return | Performance during disruptions | TQC better |
| Non-anomaly episode return | Baseline performance | Comparable |

### 7.4 Secondary Metrics

| Metric | Source |
|---|---|
| Inter-lane speed gradient at seg_0_before | Per-lane E1 data |
| L0–ramp speed differential at merge | E1 seg_0_after L0 vs ramp_on_merge |
| Downstream throughput (vph) at seg_1_after | E1 exit |
| Upstream speed σ (kph) | E1 exit seg_0_before, seg_1_before |
| Merge zone travel time | E3 seg_0_after |
| Ramp gap-wait halts | E3 ramp_on_merge |
| Corridor travel time | E3 corridor |

### 7.5 Statistical Testing

- **Mann-Whitney U test** on per-episode returns (non-parametric).
- **Kolmogorov-Smirnov test** on full return CDFs.
- **Bootstrap confidence intervals** (10,000 resamples) on CVaR₁₀% difference.
- **Cohen's d** effect size for mean return difference.
- Bonferroni correction for multiple comparisons.

---

## 8. References

Papers marked **[LOCAL]** are available in `docs/knowledge_base/`.

| Ref | Citation | Location |
|---|---|---|
| [R1] | Bellemare, M.G., Dabney, W., Munos, R. (2017). A Distributional Perspective on Reinforcement Learning. *ICML 2017*. | **[LOCAL]** `papers_DistRL/` |
| [R2] | Dabney, W., Rowland, M., Bellemare, M.G., Munos, R. (2017). Distributional Reinforcement Learning with Quantile Regression. *AAAI 2018*. | **[LOCAL]** `papers_DistRL/` |
| [R3] | Vinitsky, E. et al. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*. | **[LOCAL]** `papers_RL_VSL/` |
| [R4] | Hua, C., Fan, W. (2023). Dynamic Speed Harmonization for Mixed Traffic Flow on the Freeway Using Deep RL. *IET ITS, 17*(8). | **[LOCAL]** `papers_RL_VSL/` |
| [R5] | Ghiasi, A. et al. (2019). A Mixed Traffic Speed Harmonization Model with Connected Autonomous Vehicles. *TRC, 104*. | Web |
| [R6] | Zhao, D. et al. (2021). A Lane-Level VSL Approach Based on TD3 in a CAV Environment. *AAP, 160*. | **[LOCAL]** `papers_RL_VSL/` |
| [R10] | Zhang, Y. et al. (2024). MARVEL: Multi-Agent RL for Large-Scale VSL Control. *IEEE Access, 12*. | **[LOCAL]** `papers_RL_VSL/` |
| [R11] | Zhang, Y. et al. (2024). Field Deployment of MARL-Based VSL Controllers. *IEEE 2024*. | Web |
| [R12] | Sutton, R.S., Barto, A.G. (2018). Reinforcement Learning: An Introduction (2nd ed.). MIT Press. | **[LOCAL]** `papers_DistRL/` |
| [R14] | Dong, C. et al. (2022). Accounting for Dynamic Speed Limit Control in a Stochastic Traffic Environment. *TRC*. | **[LOCAL]** `papers_RL_VSL/` |
| [R17] | Alecsandru, C. et al. (2011). A Probabilistic Approach to Defining Freeway Capacity and Breakdown. *CJCE*. | **[LOCAL]** `papers_DistRL/` |
| [R21] | Hegyi, A. et al. (2008). SPECIALIST: A Dynamic Speed Limit Control Algorithm Based on Shock Wave Theory. *IEEE ITSC 2008*. | **[LOCAL]** `papers_RL_RM/` |
| [R24] | Ko, B. et al. (2020). Speed Harmonisation and Merge Control Using CAVs on a Highway Lane Closure. *IET ITS, 14*(8). | **[LOCAL]** `papers_RL_VSL/` |
| [R25] | Li, Z. et al. (2017). RL-Based VSL Control Strategy to Reduce Traffic Congestion at Freeway Recurrent Bottlenecks. *IEEE T-ITS, 18*(11). | **[LOCAL]** `papers_RL_VSL/` |
| [R26] | Han, Y. et al. (2022). A New RL-Based VSL Control Approach to Improve Traffic Efficiency Against Freeway Jam Waves. *TRC, 144*. | **[LOCAL]** `papers_RL_VSL/` |
| [R27] | Kuznetsov, A. et al. (2020). Controlling Overestimation Bias with Truncated Quantile Critics. *ICML 2020*. | Web |
| [R28] | Haarnoja, T. et al. (2018). Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL with a Stochastic Actor. *ICML 2018*. | Web |
| [R29] | Wu, Y. et al. (2020). Differential Variable Speed Limits Control for Freeway Recurrent Bottlenecks via Deep Actor-Critic Algorithm. *TRC, 117*. | **[LOCAL]** `papers_RL_VSL/` |

---

*End of document. Version controlled in `docs/speed_harmo_approach_v1.md`.*
