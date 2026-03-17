# Speed Harmonisation Research v5: Lagrangian CAV Control with Distributional Reinforcement Learning

**Document version:** v5.0
**Date:** 2026-03-17
**Status:** Research Plan
**Supersedes:** All prior SAR framework versions (v1–v4)

---

## Table of Contents

1. [Why v4 Failed: A Forensic Diagnosis](#1-why-v4-failed-a-forensic-diagnosis)
2. [Paradigm Shift: From Eulerian to Lagrangian Control](#2-paradigm-shift-from-eulerian-to-lagrangian-control)
3. [Theoretical Foundations](#3-theoretical-foundations)
4. [Literature Grounding](#4-literature-grounding)
5. [New Problem Formulation](#5-new-problem-formulation)
6. [MDP Specification](#6-mdp-specification)
7. [Algorithm Selection: Distributional RL](#7-algorithm-selection-distributional-rl)
8. [Implementation Plan](#8-implementation-plan)
9. [Evaluation Protocol](#9-evaluation-protocol)
10. [References (Local Paper Index)](#10-references-local-paper-index)

---

## 1. Why v4 Failed: A Forensic Diagnosis

The v4 system was a series of engineering patches on top of a structurally flawed idea. The plant compliance sweep conducted in the v4 feature branch (`feature/plant-compliance-test`) quantified the root causes:

### 1.1 The Regime Problem

Plant compliance experiments at demands 1600–3200 veh/h showed the following regime distribution per episode:

| Regime | Fraction of Episode | VSL Effect |
|---|---|---|
| FREE_FLOW (≥75 kph) | ~50% | Harmful: restricts traffic that doesn't need it; reduces throughput with no safety benefit |
| METASTABLE (45–75 kph) | ~16–27% | Useful: speed variance reduction achievable |
| CONGESTED (<45 kph) | ~25–30% | Futile: limits don't bind, traffic is already blocked |

**The agent was only capable of doing useful work during 16–27% of each episode.** For the other 73–84% of the time, any action it took was either harmful or irrelevant. No reward signal can train a good policy under these conditions.

The regime gate (v7/v8) partially addressed this, but it is a band-aid: the agent still receives observations and computes actions during FREE_FLOW and CONGESTED periods, wasting sample budget and polluting the policy gradient.

### 1.2 The Lag Problem

The 150s E1 aggregation window equals the physical corridor transit time (3 segments × ~1000 m / 65 kph ≈ 165 s). This means:

- When the agent observes a speed change in segment `seg_0_before`, it was already caused by an action taken one full window ago.
- Credit assignment is structurally broken: the agent cannot reliably attribute any reward to the action that caused it.
- The plant sweep confirmed this: upstream speed responds within the same window (E1 at 150s), but the downstream flow effect is indistinguishable from noise at 150s resolution.

### 1.3 The Compliance Problem

Physical VSL signs rely on HDV compliance through the Krauss car-following model. In the SUMO simulations used here, compliance is ~99.9% by construction (the speedFactor/speedDev parameters force it). This is **not representative of real-world conditions** where compliance is 60–80% and highly stochastic ([R9], [R16]). A framework that depends on HDV compliance to generate signal will not transfer to the real world.

### 1.4 The Reward Complexity Problem

The v7 reward function contained 9 terms (w_throughput, w_tts, w_ttt, w_queue, w_shock, w_action, w_tail_ttt, w_tail_tts, w_low_speed) plus a mobility-budget parity constraint with adaptive weights and penalty ramp. This created a reward landscape so complex that no consistent gradient existed during the 16–27% of useful episode time. The mobility-budget parity constraint targeted values (throughput drop 2–5%, TTS increase 18–35%) that were impossible to reach from the restricted METASTABLE windows alone.

### 1.5 Summary of Root Causes

| Root Cause | Effect | v5 Fix |
|---|---|---|
| Eulerian VSL with HDV compliance | Signal depends on 73–84% irrelevant windows | Switch to Lagrangian CAV control |
| 150s window = propagation lag | Credit assignment broken | 30s E1 sampling; stack 5 frames |
| Regime not in state | Agent cannot learn conditional policy | Regime indicator in state; mask training to METASTABLE |
| 9-term reward + mobility constraint | No learnable gradient | 3-term reward: variance, throughput, smoothness |
| DQN action collapse | Epsilon exploitation finds do-nothing safe | QR-DQN with NoisyNet exploration |

---

## 2. Paradigm Shift: From Eulerian to Lagrangian Control

### 2.1 Eulerian VSL (v1–v4)

In the Eulerian approach, the agent posts a speed limit to a fixed road segment (via `traci.lane.setMaxSpeed()`). Vehicles passing through the segment respond (or not) according to their car-following model parameters. The agent observes aggregated loop-detector readings and infers the effect.

**Fundamental weakness:** The control signal propagates through the vehicle population passively. The agent controls infrastructure, not vehicles.

### 2.2 Lagrangian CAV Control (v5)

In the Lagrangian approach, the agent directly commands the speed of Connected and Automated Vehicles (CAVs) as they travel through the network. Each CAV is a mobile actuator. The physical VSL signs remain in the network and continue to influence HDVs through the Krauss model, but **the agent's primary control channel is CAV speed commands via `traci.vehicle.slowDown()`**.

This is the approach demonstrated in:
- Vinitsky et al. (2018): "Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion" [R3] — ring-road and bottleneck experiments where RL-controlled CAVs absorb shockwaves without any fixed infrastructure.
- Flow framework (Wu et al., 2017/2021) [R13]: integrates SUMO/TraCI with RL for mixed-autonomy traffic.
- Ghiasi et al. (2019) [R5]: theoretical framework for CAV-based speed harmonisation in mixed traffic.

### 2.3 The Physical VSL Signs Are Not Removed

HDVs continue to follow `traci.lane.setMaxSpeed()` limits through the Krauss model. The agent may still post limits for HDVs as a secondary mechanism. But **the primary actuator is the CAV population**, and the agent's reward signal comes from what CAVs achieve — not from whether HDVs happened to comply.

This design allows the research to address a range of CAV market penetration rates (MPR = 50%, 75%, 100%) and compare performance across them, which is a directly publishable contribution.

---

## 3. Theoretical Foundations

### 3.1 Traffic Flow: Bottlenecks, Capacity Drop, and Shockwaves

The merge_4_to_3 network creates a recurrent bottleneck. At demands above ~2000 veh/h, the 4-to-3 lane reduction acts as a capacity funnel. The empirical capacity drop at activation (typically 5–15% below theoretical capacity) means congestion, once formed, is self-sustaining ([R17], [R18]).

Shockwave theory (Lighthill-Whitham-Richards model) explains the propagation: a speed discontinuity at the bottleneck propagates upstream at −15 to −25 kph. A CAV that decelerates smoothly ahead of the shockwave absorbs the wave energy and prevents it from propagating further. This is the core mechanism in [R3] and [R5].

**Key insight:** The speed variance across consecutive E1 detector windows is a direct proxy for shockwave intensity. Minimising E1 speed variance across the 3 upstream segments is equivalent to minimising shockwave intensity, which is the stated PhD objective (reducing braking/acceleration intensity as a fuel consumption proxy).

### 3.2 Distributional Reinforcement Learning

Standard DQN learns `Q(s,a) = E[G_t | s_t=s, a_t=a]` — the *mean* of the return distribution. Bellemare et al. (2017) [R1] showed that the full *distribution* `Z(s,a)` over returns is more informative and yields better policies because:

1. **Risk sensitivity:** The agent can choose actions based on any statistic of Z (mean, CVaR, worst-case).
2. **Stability:** Distributional targets reduce gradient variance compared to bootstrapped scalar targets.
3. **Representation:** The distributional Bellman operator preserves more information than its scalar counterpart.

Traffic return distributions are inherently multimodal. A given state-action pair `(s, a)` may lead to `G = +0.8` (smooth traffic achieved) or `G = −1.5` (congestion collapse triggered), depending on stochastic demand, incident timing, and HDV behaviour. The expected value `E[G]` is not a useful summary of this bimodal distribution. Distributional RL learns both modes and can select actions conservatively.

**C51** (Categorical DRL, Bellemare et al. 2017) [R1]: approximates Z with a fixed categorical distribution over N=51 atoms. The Bellman update projects onto the atom grid. Strong results on Atari; included in Rainbow [R7].

**QR-DQN** (Quantile Regression DRL, Dabney et al. 2017) [R2]: approximates Z by learning N quantile values using the asymmetric Huber (pinball) loss. No fixed atom grid; the distribution is represented implicitly as a mixture of N Dirac masses at learned quantile locations. Advantages over C51: no projection step, more flexible support, better theoretical guarantees (minimises Wasserstein distance), and easy extraction of risk measures at inference.

**Why QR-DQN is preferred for this application:**

| Property | C51 | QR-DQN |
|---|---|---|
| Support | Fixed grid (e.g., −10 to +10) | Learned, unbounded |
| Loss | KL divergence (cross-entropy) | Pinball (quantile regression) |
| Risk measure extraction | Requires post-hoc CDF integration | Direct: use τ < 0.5 quantiles |
| Support mismatch | Atoms outside [V_min, V_max] wasted | None |
| SB3 support | Yes (SB3-Contrib) | Yes (SB3-Contrib) |
| Convergence | Cramer distance convergence [R19] | Wasserstein convergence [R2] |

Traffic returns can be negative and unbounded (e.g., severe capacity drops). QR-DQN's unbounded support is therefore superior to C51's fixed atom grid.

**Risk-averse inference:** At evaluation, instead of the mean policy `argmax_a E[Z(s,a)]`, use a CVaR policy: `argmax_a CVaR_α[Z(s,a)]` with α = 0.1–0.25. This selects actions that are good even in the worst-α fraction of outcomes — appropriate for a system where capacity collapse is irreversible within an episode.

### 3.3 NoisyNet Exploration

NoisyNet (Fortunato et al., 2017) [R8] replaces ε-greedy exploration with learnable per-weight noise in the Q-network. Advantages:
- State-dependent exploration: in high-uncertainty states (metastable), the network explores more; in clear states (free-flow, congested), it converges faster.
- No ε schedule to tune.
- Particularly relevant here because the agent should explore only in METASTABLE states — NoisyNet achieves this automatically.
- QR-DQN + NoisyNet is the QR-DQN variant shipped with SB3-Contrib as `QRDQN`.

---

## 4. Literature Grounding

### 4.1 Distributional RL Applied to Traffic Problems

**Bellemare, M.G., Dabney, W., Munos, R. (2017).** A Distributional Perspective on Reinforcement Learning. *ICML 2017*. [R1]
Foundational paper for C51. Establishes the distributional Bellman operator and proves convergence. Demonstrates on Atari that distributional learning improves over DQN even when the mean policy is used.

**Dabney, W., Rowland, M., Bellemare, M.G., Munos, R. (2017).** Distributional Reinforcement Learning with Quantile Regression. *AAAI 2018*. [R2]
Introduces QR-DQN. Proves that minimising the quantile regression loss is equivalent to minimising the Wasserstein-1 distance between the predicted and target distributions. Achieves new SOTA on Atari. The paper is available locally in `papers_DistRL/`.

**Rowland, M., Bellemare, M.G., Dabney, W., Munos, R., Teh, Y.W. (2018).** An Analysis of Categorical Distributional Reinforcement Learning. *AISTATS 2018*. [R19]
Proves that C51 minimises the Cramer distance (not KL) under projection. Provides theoretical comparison with QR-DQN. Available locally.

**Hessel, M. et al. (2018).** Rainbow: Combining Improvements in Deep Reinforcement Learning. *AAAI 2018*. [R7]
Combines DQN + double DQN + prioritised replay + dueling networks + multi-step + distributional (C51) + NoisyNet. C51 is identified as the single largest contributor. This motivates combining QR-DQN with NoisyNet and PER in the v5 architecture.

### 4.2 Lagrangian and CAV-Based Speed Harmonisation

**Vinitsky, E., Kreidieh, A., Le Flem, L., Kheterpal, N., Jang, K., Wu, F., Liaw, R., Liang, E., Bayen, A. (2018).** Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*. [R3]
Directly controls a small fraction of vehicles (5–10%) as CAVs in a SUMO bottleneck scenario using PPO. Without any fixed VSL infrastructure, CAVs reduce throughput loss from 30% to <5%. Key result: **a 10% CAV penetration rate is sufficient to eliminate the bottleneck capacity drop**. This is the most direct precedent for the v5 approach.

**Wu, C., Parvate, K., Kheterpal, N., Dickstein, L., Mehta, A., Vinitsky, E., Bayen, A. (2021).** Flow: A Modular Learning Framework for Mixed Autonomy Traffic. *IEEE Trans. Robotics 38(2), 2021*. [R13]
The Flow framework integrates SUMO/TraCI with RLlib. Provides the software architecture that demonstrated CAV-based RL is tractable in SUMO at scale. Relevant to the v5 implementation approach.

**Ghiasi, A., Hussain, O., Ma, J., Qian, Z., Li, X. (2019).** A Mixed Traffic Speed Harmonization Model with Connected Autonomous Vehicles. *Transportation Research Part C, 104, 210–233*. [R5]
Proposes a model-based (LWR-derived) CAV speed harmonisation controller for mixed traffic. Analytically demonstrates that CAVs with a look-ahead information horizon can absorb stop-and-go waves. Establishes the theoretical viability of the approach.

**Hua, X. et al. (2023).** Dynamic Speed Harmonization for Mixed Traffic Flow on the Freeway Using Deep Reinforcement Learning. *IET Intelligent Transport Systems, 17(8)*. [R4]
DRL-based dynamic speed harmonisation for CAV/HDV mixed traffic at multiple CAV market penetration rates (MPR = 20–100%). Uses DDPG for continuous action space. Reports: (i) shockwave dampening improves monotonically with MPR; (ii) at MPR ≥ 50%, DRL-CAV outperforms both no-control and rule-based baselines on speed variance and fuel consumption. This directly validates the choice of 50–100% MPR for the v5 experiments. Available locally in `papers_RL_VSL/`.

**Zhao, D. et al. (2021).** A Lane-Level Variable Speed Limit Approach Based on Twin Delayed Deep Deterministic Policy Gradient in a Connected Automated Vehicle Environment. *Accident Analysis and Prevention, 160*. [R6]
Uses TD3 (actor-critic) for lane-level VSL with CAVs. Relevant for comparison: actor-critic with continuous action is an alternative to QR-DQN with discrete action. The lane-level design (different limits per lane rather than per segment) is noted as a future extension in v5. Available locally.

### 4.3 Multi-Agent VSL — MARVEL and Field Deployment

**Zhang, Y., Quiñones-Grueiro, M., Zhang, Z., Wang, Y., Barbour, W., Biswas, G., Work, D. (2023/2024).** MARVEL: Multi-Agent Reinforcement Learning for Large-Scale Variable Speed Limit Control. *arXiv:2310.12359; IEEE Trans. ITS 2024*. [R10]
The most advanced VSL RL deployment in the literature. 67 agents controlling VSL over 17 miles of I-24 near Nashville, TN. Key design decisions: (i) uses only real-world observable sensors (loop detectors + radar); (ii) parameter sharing for scalability; (iii) reward = weighted sum of speed variance, throughput delta, and action smoothness — exactly the 3-term structure proposed in v5. Deployed March 2024, achieving 32.7% reduction in coefficient of speed variation (CSV). **This paper directly validates the v5 reward design.** Available locally in `papers_RL_VSL/`.

**Zhang et al. (2024).** Field Deployment of MARL-Based Variable Speed Limit Controllers. *arXiv:2407.08021; IEEE 2024*. [R11]
Six-month field deployment results for MARVEL. 28 million vehicle trips; CSV reduced 32.7% vs. pre-deployment. Demonstrates real-world viability of RL-based VSL.

### 4.4 Stochastic Traffic and Distributional VSL

**Alecsandru, C., Boucher, J.P., Tarko, A.P. (2011).** A Probabilistic Approach to Defining Freeway Capacity and Breakdown. *Canadian Journal of Civil Engineering*. [R17]
Demonstrates that freeway capacity is a random variable, not a deterministic constant. At any given demand level, breakdown probability follows a logistic distribution. This is the theoretical basis for using distributional RL: the *distribution* of returns matters because the traffic system itself has stochastic capacity.

**Hall, F.L., Agyemang-Duah, K. (1991).** Relation between Traffic Density and Capacity Drop at Three Freeway Bottlenecks. *Transportation Research Record*. [R18]
The classic capacity drop paper. Documents 5–15% capacity reduction at activation of recurrent bottlenecks. Establishes that the bottleneck activation is a threshold phenomenon — another source of distributional return bimodality.

**Dong, C., Wang, H., Chen, X. et al. (2022).** Accounting for Dynamic Speed Limit Control in a Stochastic Traffic Environment: A Reinforcement Learning Approach. *Transportation Research Part C*. [R14]
Explicitly models traffic stochasticity in the RL formulation for VSL. Uses a scenario-based approach to handle demand variability. The stochastic traffic environment described is the direct motivation for distributional RL over standard DQN. Available locally in `papers_RL_VSL/`.

### 4.5 State Design: Speed Transition Matrices and Multi-Frame Observation

**Li, S. et al. (2023).** Reinforcement Learning Based Variable Speed Limit Control for Mixed Traffic Flows Using Speed Transition Matrices for State Estimation. *IEEE Trans. ITS*. [R15]
Represents traffic state as a speed transition matrix — effectively a 2D histogram of (speed at t-1, speed at t) per segment. This is a dense temporal representation that preserves more information than a scalar mean speed. The v5 stacked-frame approach is a temporal analogue: stacking 5 consecutive 30s E1 observations to represent the trajectory of the traffic state. Available locally.

### 4.6 Influence of VSL on Fuel Consumption

**Xu, X. et al. (2023).** Influence of Variable Speed Limit Control on Fuel and Electric Energy Consumption, and Exhaust Gas Emissions in Mixed Traffic Flows. *Transportation Research Part D*. [R16]
Directly measures fuel consumption and CO2 emissions under VSL control with mixed CAV/HDV traffic. Finds that VSL reduces fuel consumption primarily by reducing stop-and-go cycles — directly validating the PhD objective. CAV speed harmonisation achieves greater fuel savings than HDV-only VSL at equivalent penetration rates. Available locally.

---

## 5. New Problem Formulation

### 5.1 Network and Scenario

- **Network:** merge_4_to_3 (existing SUMO network)
- **Bottleneck:** 4-lane → 3-lane merge
- **Controlled zone:** 3 upstream segments: `seg_2_before`, `seg_1_before`, `seg_0_before` (each ~1000 m)
- **Demand range:** 1600–3200 veh/h (existing scenario set)
- **Simulation step:** 1 s
- **Episode duration:** 7950 s (existing)

### 5.2 CAV Penetration

The simulation creates vehicles with type `CAV` or `HDV` at the specified market penetration rate (MPR). The experiment sweeps:
- MPR = 0% (baseline, no CAV control, VSL signs only)
- MPR = 50% (primary training condition)
- MPR = 75%
- MPR = 100%

HDVs follow `traci.lane.setMaxSpeed()` through the Krauss model (existing behaviour, unchanged). CAVs receive direct speed commands via `traci.vehicle.slowDown(veh_id, target_ms, step_length)`.

### 5.3 Control Architecture

Two simultaneous control channels:

| Channel | Mechanism | Actuator | Agent controls? |
|---|---|---|---|
| Infrastructure | `traci.lane.setMaxSpeed()` | HDVs (natural Krauss compliance) | Optional: agent may post segment limits |
| Lagrangian | `traci.vehicle.slowDown()` | CAVs (direct) | Yes — primary channel |

For simplicity in v5.0, the agent posts a single target speed per segment, applied via:
1. `traci.lane.setMaxSpeed(lane_id, target_ms)` — for HDV guidance
2. `traci.vehicle.slowDown(cav_id, target_ms, sumo_step_length)` — for CAVs

At 50% MPR, roughly half the vehicles in each upstream segment are directly controlled. This is sufficient, per [R3], to suppress bottleneck-induced shockwaves.

---

## 6. MDP Specification

### 6.1 Observation Period and Control Period

**Key change from v4:**

| Parameter | v4 | v5 |
|---|---|---|
| E1 aggregation window | 150 s | 30 s |
| Control period (action frequency) | 150 s (= 1 E1 window) | 150 s (held for 5 E1 windows) |
| State at each control step | 1 observation | Stack of last 5 × 30s observations |

The 30s E1 window is achievable in SUMO by setting `freq="30"` on E1 detectors. The corridor transit time at 65 kph = 165 s ≈ 5.5 windows. Stacking 5 observations gives the agent a 150s temporal context with 5× finer resolution than v4. The agent still acts once every 150s, maintaining consistency with real-world VSL operational constraints.

### 6.2 State Space

The state vector `s_t ∈ ℝ^(5 × F)` is the concatenation of the last 5 E1 feature vectors, where each feature vector `f_k ∈ ℝ^F` is computed at 30s E1 windows.

**Per-step feature vector `f_k` (F = 22 dimensions):**

| Group | Features | Dimensions |
|---|---|---|
| Upstream E1: seg_2_before | space mean speed (kph), flow (veh/h), occupancy (%) | 3 |
| Upstream E1: seg_1_before | space mean speed (kph), flow (veh/h), occupancy (%) | 3 |
| Upstream E1: seg_0_before | space mean speed (kph), flow (veh/h), occupancy (%) | 3 |
| Downstream E1: seg_0_after | space mean speed (kph), flow (veh/h), occupancy (%) | 3 |
| Speed gradient | seg_0_before speed − seg_0_after speed (kph) | 1 |
| Flow gradient | seg_0_before flow − seg_0_after flow (veh/h) | 1 |
| Regime indicator | one-hot: [FREE_FLOW, METASTABLE, CONGESTED] | 3 |
| CAV density | fraction of vehicles tagged as CAV in seg_0_before | 1 |
| Previous action | index of the last posted action (normalised) | 1 |
| Demand indicator | current demand level (normalised 0–1) | 1 |
| Time in episode | simulation time / episode_duration | 1 |
| E3 increments | TTS increment (s), TTT increment (s) since last control step | 2 |

**Total state dimension:** 5 × 22 = **110**

All features are normalised to `[0, 1]` or `[−1, 1]` using known physical bounds (speed: 0–130 kph; flow: 0–4000 veh/h; occupancy: 0–100%; etc.).

**Regime indicator:** Computed from `seg_0_before` E1 readings using `RegimeDetector` (canonical implementation in `core/src/regime_detector.py`). The one-hot encoding makes the regime explicitly observable to the agent, so it can learn a conditional policy without a regime gate wrapper.

### 6.3 Action Space

**Discrete, 7 actions** — a target speed delta (kph) applied relative to the segment free-flow speed (default 100 kph):

| Action index | Delta (kph) | Resulting target speed |
|---|---|---|
| 0 | −30 | 70 kph |
| 1 | −20 | 80 kph |
| 2 | −10 | 90 kph |
| 3 | 0 | 100 kph (no change / release) |
| 4 | +0 | Hold current posted limit |
| 5 | −15 | 85 kph |
| 6 | −25 | 75 kph |

The 7-action design covers the operationally relevant range (70–100 kph) with sufficient resolution. A single action is applied uniformly to all 3 upstream segments (one-zone controller). This is simpler than the per-segment design of v4 and avoids combinatorial explosion; multi-zone control is listed as a future extension.

**Implementation note:** The posted limit is absolute (not additive delta), computed once per control step. CAVs receive `slowDown(target_ms, sumo_step_length)` every simulation step until the next control decision. HDVs see `setMaxSpeed(lane_id, target_ms)`.

### 6.4 Reward Function

The reward function uses exactly 3 terms, mirroring the MARVEL deployment design [R10] and the energy-focused literature [R16]:

```
r_t = −w_v · σ²_speed + w_q · Δflow_pct − w_a · |Δaction|
```

| Term | Formula | Purpose |
|---|---|---|
| Speed variance penalty | `σ²(speeds at all upstream E1 detectors in window k)` | Minimise shockwave intensity; proxy for fuel consumption |
| Throughput reward | `(flow_downstream_k − flow_nocontrol_reference) / flow_nocontrol_reference` | Maintain mobility |
| Action smoothness penalty | `|action_t − action_{t-1}|` / max_delta | Prevent oscillating VSL that confuses drivers/vehicles |

**Weights (initial values; ablation study planned):**

| Weight | Value | Rationale |
|---|---|---|
| w_v | 0.50 | Primary objective: shockwave reduction |
| w_q | 0.35 | Secondary: throughput must not collapse |
| w_a | 0.15 | Smoothness: operational constraint |

**No mobility-budget constraint.** The throughput term is a soft reward, not a hard constraint. The agent will naturally learn to balance variance reduction and throughput because reducing traffic too aggressively collapses flow (negative throughput reward), while not acting enough leaves shockwaves (negative variance reward).

**Speed variance `σ²_speed` computation:**

```python
speeds = [e1.space_mean_speed_kph(seg, window=30)
          for seg in ("seg_2_before", "seg_1_before", "seg_0_before")]
sigma2 = np.var(speeds)  # variance across segments at time k
```

This is normalised by the maximum observed variance (empirical: ~400 kph² at full congestion) to produce a `[0, 1]` penalty.

**Reference flow:** The `flow_nocontrol_reference` is a per-demand, per-step lookup from the existing no-control baseline CSV (already available from v6/v7 experiments). At each control step, the appropriate reference value is indexed by `(demand_vph, control_step_idx)`.

---

## 7. Algorithm Selection: Distributional RL

### 7.1 Primary: QR-DQN

**Implementation:** `stable_baselines3_contrib.QRDQN` with the following configuration:

```yaml
algorithm: QRDQN
policy: MlpPolicy
learning_rate: 0.0001
buffer_size: 300000
batch_size: 256
tau: 1.0            # hard target update
gamma: 0.99
train_freq: 4       # collect 4 steps then update
gradient_steps: 4   # gradient steps per update
target_update_interval: 2000
exploration_fraction: 0.0   # NoisyNet replaces epsilon-greedy
exploration_initial_eps: 0.0
exploration_final_eps: 0.0
policy_kwargs:
  n_quantiles: 25         # N quantile atoms
  net_arch: [256, 256]    # 2-layer MLP
  # NoisyNet enabled through SB3-Contrib QRDQN default
```

**Why N=25 quantiles (not 200):**
- N=25 gives a 4% quantile resolution — sufficient to compute CVaR at τ=0.1 (worst 2–3 quantiles).
- Higher N (e.g., N=200) offers finer resolution but N=25 has been shown to perform comparably on practical domains [R2].
- Reduces memory and compute, allowing larger batch sizes and more training envs.

**Risk-sensitive inference:**
At evaluation, the action selection policy becomes:
```python
# Standard (mean policy):
action = argmax_a E[Z(s,a)]  = argmax_a mean(quantiles(s,a))

# Risk-averse (CVaR policy, alpha=0.1):
action = argmax_a CVaR_0.1[Z(s,a)] = argmax_a mean(quantiles(s,a)[:2])  # bottom 2 of 25
```
The risk-averse policy is evaluated only; training uses the standard mean policy.

**NoisyNet:** Enabled by default in SB3-Contrib QRDQN. Replaces all ε-greedy exploration. The noise parameters are learned per layer, enabling state-dependent exploration intensity.

### 7.2 Comparison: C51 / Categorical DQN

C51 [R1] is included as a comparison algorithm to isolate the effect of QR-DQN's unbounded support. Implementation via a custom SB3-Contrib wrapper or direct Stable Baselines3 extension:

```yaml
algorithm: C51
n_atoms: 51
v_min: -20.0    # minimum return (severe congestion episode)
v_max: 10.0     # maximum return (smooth episode)
```

`V_min` and `V_max` are calibrated from the distribution of returns observed under the no-control baseline and the best v4 DQN episodes. **This is the key hyperparameter risk for C51**: if the actual return distribution has non-negligible mass outside `[V_min, V_max]`, the projection step loses information. QR-DQN avoids this entirely.

### 7.3 Future Extension: IQN

Implicit Quantile Networks (Dabney et al., 2018) [R20] generalise QR-DQN by conditioning the quantile function on a sampled τ rather than learning N fixed quantile values. This enables:
- Smoother quantile function interpolation.
- Arbitrary CVaR evaluation at any τ without retraining.
- A single model that can be queried for different risk preferences.

IQN is listed as a v5.1 extension after QR-DQN baseline results are established.

### 7.4 Algorithm Comparison Matrix

| Algorithm | SB3 Support | Discrete Action | Unbounded Support | Risk Measure | Recommendation |
|---|---|---|---|---|---|
| DQN | Core | Yes | N/A | No | Baseline only |
| C51 | SB3-Contrib | Yes | No (fixed grid) | Requires post-hoc | Comparison |
| QR-DQN | SB3-Contrib | Yes | Yes | Direct quantile | **Primary** |
| IQN | External | Yes | Yes | Direct, any τ | v5.1 extension |
| DSAC | External | Continuous | Yes | Yes | Future work |

---

## 8. Implementation Plan

### 8.1 Phase 0: Baseline Infrastructure (2 weeks)

**O1.** Reconfigure SUMO E1 detectors from 150s to 30s aggregation frequency.
- File: SUMO `.add.xml` detector definition files.
- Change: `period="30"` on all `<e1Detector>` entries in the upstream segments.

**O2.** Add CAV vehicle type to SUMO network.
- File: SUMO `.rou.xml` route files.
- Add `vType` with `id="CAV"` at specified MPR fraction.
- Parameters: `speedFactor="1.0"` `speedDev="0.0"` (CAVs fully comply with speed commands).
- HDV type parameters unchanged (Krauss with existing speedFactor/speedDev).

**O3.** Add CAV detection to `_apply_speed_limits()` in `core/src/drl_vsl.py`.
- Extend the per-vehicle loop to compute `cav_density_per_segment` (fraction of vehicles tagged as CAV).
- Add to the per-window metrics collection.

**O4.** Create new SAR components:

| Component | File | Description |
|---|---|---|
| `m43_state_v0` | `sar_components/states/m43_state_v0.py` | Stacked 5-frame 30s E1 observation (110-dim) |
| `m43_action_v0` | `sar_components/actions/m43_action_v0.py` | 7-action discrete speed target |
| `m43_reward_v0` | `sar_components/rewards/m43_reward_v0.py` | 3-term reward (variance, throughput, smoothness) |

### 8.2 Phase 1: State Component `m43_state_v0` (1 week)

The state component collects 30s E1 windows and maintains a rolling buffer of the last 5 frames.

```python
class M43StateV5(BaseStateRepresentation):
    FRAME_DIM = 22
    N_FRAMES = 5
    OBS_DIM = N_FRAMES * FRAME_DIM  # 110

    def __init__(self, sar_config):
        self._buffer = deque(maxlen=self.N_FRAMES)
        # Pre-fill with zeros
        for _ in range(self.N_FRAMES):
            self._buffer.append(np.zeros(self.FRAME_DIM, dtype=np.float32))

    def compute_state(self, metrics, prev_action, sim_time, episode_duration):
        frame = self._extract_frame(metrics, prev_action, sim_time, episode_duration)
        self._buffer.append(frame)
        return np.concatenate(list(self._buffer), axis=0)

    def _extract_frame(self, metrics, prev_action, sim_time, episode_duration):
        # 22-dim feature vector (see Section 6.2)
        ...
```

The observation space is `Box(low=-1.0, high=1.0, shape=(110,), dtype=np.float32)`.

### 8.3 Phase 2: Reward Component `m43_reward_v0` (1 week)

```python
class M43RewardV5(BaseRewardFunction):
    W_VARIANCE = 0.50
    W_THROUGHPUT = 0.35
    W_SMOOTHNESS = 0.15
    MAX_VARIANCE_KPH2 = 400.0   # calibrated from no-control episodes
    MAX_FLOW_REF_VPH = 3200.0

    def compute_reward(self, metrics, action, prev_action, demand_vph, control_step):
        # Term 1: speed variance (lower is better)
        speeds = [metrics.space_mean_speed_kmh_seg2,
                  metrics.space_mean_speed_kmh_seg1,
                  metrics.space_mean_speed_kmh_seg0]
        sigma2 = float(np.var(speeds)) / self.MAX_VARIANCE_KPH2

        # Term 2: throughput delta vs no-control reference
        ref_flow = self._lookup_reference_flow(demand_vph, control_step)
        actual_flow = metrics.flow_veh_hr_downstream
        delta_flow = (actual_flow - ref_flow) / self.MAX_FLOW_REF_VPH

        # Term 3: action smoothness
        action_delta = abs(action - prev_action) / 6.0  # normalised by max_delta

        reward = (-self.W_VARIANCE * sigma2
                  + self.W_THROUGHPUT * delta_flow
                  - self.W_SMOOTHNESS * action_delta)

        return float(np.clip(reward, -1.5, 1.0))
```

### 8.4 Phase 3: New Config Version `m43_v0` (1 week)

Create `train_eval/config/m43_v0/_common.yaml` with:
- `sar.algorithm: QRDQN`
- `sar.state: m43_state_v0`
- `sar.action: m43_action_v0`
- `sar.reward: m43_reward_v0`
- `training.num_train_envs: 500` (at 50% MPR, each env is slightly heavier)
- `training.total_timesteps: 1000000`
- `training.eval.num_evaluations: 20`
- `sumo.custom_config.cav_penetration_rate: 0.5`
- `sumo.custom_config.regime_gate_enabled: false` (regime is in state; no separate gate needed)

Per-algorithm configs `dqn_config.yaml`, `qrdqn_config.yaml`, `c51dqn_config.yaml` in `s0_0/`.

### 8.5 Phase 4: Training and Ablation (4 weeks)

| Run ID | Algorithm | MPR | N_quantiles | Notes |
|---|---|---|---|---|
| v9-qrdqn-50 | QR-DQN | 50% | 25 | Primary |
| v9-qrdqn-75 | QR-DQN | 75% | 25 | MPR sweep |
| v9-qrdqn-100 | QR-DQN | 100% | 25 | MPR sweep |
| v9-c51-50 | C51 | 50% | 51 atoms | Algorithm comparison |
| v9-dqn-50 | DQN | 50% | N/A | Baseline comparison |
| v9-qrdqn-50-cvar | QR-DQN | 50% | 25 | Risk-averse inference (CVaR α=0.1) |

---

## 9. Evaluation Protocol

### 9.1 Metrics

The evaluation measures the direct PhD objective (reduce braking/acceleration intensity) and secondary objectives:

| Metric | Symbol | Computation | Target |
|---|---|---|---|
| Coefficient of Speed Variation | CSV | `std(speed) / mean(speed)` across all E1 readings in episode | Lower is better |
| Speed Variance (per segment) | σ²_seg | `var(30s speeds per segment)` across episode | Lower is better |
| Throughput ratio | TQ | `mean_downstream_flow / no_control_flow` | ≥ 0.97 (≤3% sacrifice) |
| TTS ratio | TTS_r | `episode_TTS / no_control_TTS` | ≤ 1.10 |
| Shockwave occurrence | SW_frac | Fraction of windows with speed drop > 15 kph vs upstream | Lower is better |
| Fuel proxy (acceleration variance) | AV | Variance of vehicle-step speeds within controlled zone | Lower is better |
| Return distribution spread | IQR_Z | Interquartile range of episode returns across seeds | Lower is better (robustness) |

### 9.2 Baselines

| Controller | Description |
|---|---|
| No_Ctrl | No VSL, no CAV control |
| StaticV2_75kph | Fixed 75 kph on all segments, all episode |
| StaticV2_80kph | Fixed 80 kph on all segments |
| RBC_SPECIALIST | SPECIALIST rule-based shockwave algorithm [R21] |
| DQN_50pct | Standard DQN at 50% MPR |
| QR-DQN_mean | QR-DQN with mean policy (no risk aversion) |
| QR-DQN_cvar10 | QR-DQN with CVaR α=0.1 policy |
| C51_50pct | C51 at 50% MPR |

### 9.3 Statistical Protocol

- 10 independent seeds per demand level × 9 demand levels × 10 repetitions per seed-demand = 900 evaluation episodes per controller.
- Confidence intervals: bootstrapped 95% CI on all aggregate metrics.
- Significance test: Mann-Whitney U test (non-parametric, appropriate for non-Gaussian return distributions) between QR-DQN and each baseline.

### 9.4 Return Distribution Analysis

A unique contribution of the distributional approach: publish the full **return distribution** for each controller, not just the mean. This directly demonstrates:
1. Whether QR-DQN has lower variance in outcomes (robustness).
2. Whether risk-averse inference (CVaR) shifts probability mass away from catastrophic episodes (capacity collapse).
3. The shape of Z(s,a) in METASTABLE vs. other regimes.

---

## 10. References (Local Paper Index)

Papers marked **[LOCAL]** are available in `phd_speed_harmo_v4/docs/academic_papers/`. All others are cited from verified web sources.

| Ref | Citation | Location |
|---|---|---|
| [R1] | Bellemare, M.G., Dabney, W., Munos, R. (2017). A Distributional Perspective on Reinforcement Learning. *ICML 2017*. | **[LOCAL]** `papers_DistRL/A distributional perspective on reinforcement learning.pdf` |
| [R2] | Dabney, W., Rowland, M., Bellemare, M.G., Munos, R. (2017). Distributional Reinforcement Learning with Quantile Regression. *AAAI 2018*. | **[LOCAL]** `papers_DistRL/Distributional Reinforcement Learning with Quantile Regression.pdf` |
| [R3] | Vinitsky, E. et al. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*. | **[LOCAL]** `papers_RL_VSL/Lagrangian Control through Deep-RL Applications to Bottleneck Decongestion.pdf` |
| [R4] | Hua, X. et al. (2023). Dynamic Speed Harmonization for Mixed Traffic Flow on the Freeway Using Deep Reinforcement Learning. *IET Intelligent Transport Systems*. | **[LOCAL]** `papers_RL_VSL/Dynamic speed harmonization for mixed traffic flow on the freeway using deep.pdf` |
| [R5] | Ghiasi, A. et al. (2019). A Mixed Traffic Speed Harmonization Model with Connected Autonomous Vehicles. *Transportation Research Part C, 104*. | Web: https://doi.org/10.1016/j.trc.2019.05.002 |
| [R6] | Zhao, D. et al. (2021). A Lane-Level Variable Speed Limit Approach Based on TD3 in a CAV Environment. *Accident Analysis and Prevention, 160*. | **[LOCAL]** `papers_RL_VSL/A lane-level variable speed limit approach based on twin delayed deep deterministic policy gradient in a connected automated vehicle environment.pdf` |
| [R7] | Hessel, M. et al. (2018). Rainbow: Combining Improvements in Deep Reinforcement Learning. *AAAI 2018*. | **[LOCAL]** `papers_DistRL/Rainbow - Combining Improvements in Deep Reinforcement Learning.pdf` |
| [R8] | Fortunato, M. et al. (2017). Noisy Networks for Exploration. *ICLR 2018*. | **[LOCAL]** `papers_DistRL/Noisy networks for exploration.pdf` |
| [R9] | Lu, X.Y., Shladover, S.E. (2014). Review of Variable Speed Limits and Advisories. *Transportation Research Record*. | (General reference; HDV compliance literature) |
| [R10] | Zhang, Y. et al. (2023/2024). MARVEL: Multi-Agent Reinforcement Learning for Large-Scale Variable Speed Limit Control. *arXiv:2310.12359; IEEE Trans. ITS 2024*. | **[LOCAL]** `papers_RL_VSL/MARVEL Bringing Multi-Agent Reinforcement- Learning Based Variable Speed Limit Controllers Closer to Deployment.pdf` |
| [R11] | Zhang, Y. et al. (2024). Field Deployment of MARL-Based Variable Speed Limit Controllers. *arXiv:2407.08021; IEEE 2024*. | Web: https://arxiv.org/abs/2407.08021 |
| [R12] | Sutton, R.S., Barto, A.G. (2018). Reinforcement Learning: An Introduction (2nd ed.). MIT Press. | **[LOCAL]** `papers_DistRL/SuttonBartoIPRLBook2ndEd.pdf` |
| [R13] | Wu, C. et al. (2021). Flow: A Modular Learning Framework for Mixed Autonomy Traffic. *IEEE Trans. Robotics*. | **[LOCAL]** `papers_RL_VSL/Flow Deep reinforcement learning for control in sumo.pdf` |
| [R14] | Dong, C. et al. (2022). Accounting for Dynamic Speed Limit Control in a Stochastic Traffic Environment. *Transportation Research Part C*. | **[LOCAL]** `papers_RL_VSL/Accounting for dynamic speed limit control in a stochastic traffic environment A reinforcement learning approach.pdf` |
| [R15] | Li, S. et al. (2023). RL-Based VSL Control for Mixed Traffic Using Speed Transition Matrices. *IEEE Trans. ITS*. | **[LOCAL]** `papers_RL_VSL/Reinforcement Learning Based Variable Speed Limit Control for Mixed Traffic Flows Using Speed Transition Matrices for State Estimation.pdf` |
| [R16] | Xu, X. et al. (2023). Influence of VSL Control on Fuel and Electric Energy Consumption in Mixed Traffic Flows. *Transportation Research Part D*. | **[LOCAL]** `papers_RL_VSL/Influence of Variable Speed Limit Control on Fuel and Electric Energy Consumption, and Exhaust Gas Emissions in Mixed Traffic Flows.pdf` |
| [R17] | Alecsandru, C. et al. (2011). A Probabilistic Approach to Defining Freeway Capacity and Breakdown. *Canadian Journal of Civil Engineering*. | **[LOCAL]** `papers_DistRL/A Probabilistic Approach to Defining Freeway Capacity and Breakdown.pdf` |
| [R18] | Hall, F.L., Agyemang-Duah, K. (1991). Relation between Traffic Density and Capacity Drop at Three Freeway Bottlenecks. *Transportation Research Record*. | **[LOCAL]** `papers_DistRL/Relation between traffic density and capacity drop at three freeway bottlenecks.pdf` |
| [R19] | Rowland, M. et al. (2018). An Analysis of Categorical Distributional Reinforcement Learning. *AISTATS 2018*. | **[LOCAL]** `papers_DistRL/An analysis of categorical distributional reinforcement learning.pdf` |
| [R20] | Dabney, W. et al. (2018). Implicit Quantile Networks for Distributional Reinforcement Learning. *ICML 2018*. | Web: https://arxiv.org/abs/1806.06923 |
| [R21] | Hegyi, A. et al. (2008). SPECIALIST: A Dynamic Speed Limit Control Algorithm Based on Shock Wave Theory. *IEEE ITSC 2008*. | **[LOCAL]** `papers_RL_RM/SPECIALIST A dynamic speed limit control algorithm based on shock wave theory.pdf` |
| [R22] | Cooperative Multi-Agent RL for Large Scale VSL Control. | **[LOCAL]** `papers_RL_VSL/Cooperative Multi-Agent Reinforcement Learning for Large Scale Variable Speed Limit Control.pdf` |
| [R23] | Multi-agent RL-Based VSL Strategy by Leveraging CAVs in Mixed Traffic Flow. | **[LOCAL]** `papers_RL_VSL/Multi-agent Reinforcement Learning-Based Variable Speed Limit Strategy by Leveraging Connected and Autonomous Vehicles in Mixed Traffic Flow.pdf` |

---

## Appendix A: Key Design Decisions Summary

| Decision | v4 choice | v5 choice | Justification |
|---|---|---|---|
| Primary control mechanism | Eulerian VSL (lane setMaxSpeed) | Lagrangian CAV (slowDown) | [R3], [R4]: CAV direct control more effective than sign compliance |
| HDV control | setSpeed on all vehicles | Krauss natural compliance only | Realistic; removes simulation artefact |
| Algorithm | DQN | QR-DQN | [R2]: distributional returns for stochastic traffic |
| Risk measure | None | CVaR α=0.1 at inference | [R1],[R2]: distributional RL enables risk-averse policies |
| Exploration | ε-greedy | NoisyNet | [R8]: state-dependent exploration; no ε schedule |
| Observation window | 150s | 30s (stack ×5) | Removes lag; 5× temporal resolution |
| Control period | 150s | 150s (unchanged) | Operational constraint; matched to physical response time |
| State dimension | ~20 | 110 (5-frame stack) | Temporal context needed for credit assignment |
| Reward terms | 9 terms + constraint | 3 terms | [R10]: MARVEL field deployment uses exactly this structure |
| Regime gate | External wrapper | Regime in state | Agent learns conditional policy; no gate needed |
| CAV penetration | Not modelled | 50%, 75%, 100% sweep | [R3], [R4]: MPR is key independent variable |

---

*End of document. Version controlled in `phd_speed_harmo_v4/docs/speed_harmo_approach_v0.md`.*
