# Algorithm and Objective Selection: Empirical Foundation

This document records the empirical process that led to the v5 design decisions. Every claim is supported by either (a) baseline simulation data from the ramps_v1 network or (b) published academic references. The data was collected on 2026-03-18 using SUMO 1.21 with the ramps_v1 topology (3L mainline × 4 km → 4L weaving 500 m → 3L downstream 1 km; on-ramp 1 km; off-ramp 1 km).

---

## 1. From v4 to v5: why the redesign was necessary

### 1.1 What failed in v4

The v4 system used QR-DQN (Dabney et al., 2018) [R2] with a 7-level discrete action space on a 4→3 lane-drop topology. After 3 years of experimentation, no configuration produced results that meaningfully outperformed the no-control baseline. Two independent root causes were identified:

1. **The environment** (4→3 lane-drop) had a microscopic bottleneck mechanism (forced lane-change gap acceptance) that was poorly observable from macroscopic E1 detector readings. The return distribution was genuinely bimodal (merge success vs. failure), but the agent could not distinguish the two regimes from its observations because the downstream merge point was not instrumented.

2. **The algorithm** (QR-DQN) was restricted to `gym.spaces.Discrete`, limiting the action space to 7 absolute speed levels. The ramps_v1 topology requires two independent control inputs (mainline VSL + ramp VSL), which maps naturally to a 2D continuous action space. Discretising this produces 7 × 7 = 49 actions, each needing independent quantile distribution estimation — computationally prohibitive and sample-inefficient.

### 1.2 What changed in v5

| Decision | v4 | v5 | Reason |
|---|---|---|---|
| Topology | 4→3 lane-drop | Ramp-on with weaving zone | Merge point is observable; causal chain is shorter |
| Action space | Discrete(7) | Box([60, 40], [120, 90]) | 2D continuous: mainline + ramp VSL independently |
| Algorithm | QR-DQN | TQC (primary), SAC (baseline) | Continuous-action distributional RL |
| Objective | Speed at merge zone | **Deceleration-acceleration reduction across upstream corridor** | Directly targets emissions; validated empirically below |

---

## 2. Objective selection: what to optimise and why

### 2.1 The academic grounding for deceleration-acceleration as objective

Speed harmonization aims to reduce spatiotemporal speed variations, which directly reduces the frequency and amplitude of vehicle decelerations and accelerations. The emissions connection is well-established:

- Hua & Fan (2023, IET-ITS, Table 2): Dynamic Speed Harmonization (DSH) reduces CO₂ by 5–10% and fuel consumption by 10–15% across CAV penetration rates, measured via cumulative emergency deceleration.
- Hua & Fan (2024, Physica A, §3.3): Safety-oriented DSH defines the reward as `r = −θ_t` where `θ_t` is the cumulative emergency deceleration above 4.5 m/s². They use this metric explicitly as a proxy for collision risk and emissions.
- Kušić et al. (2020, Applied Sciences, Table 1): RL-VSL systems achieve 18–51% TTS reduction; the R-MART approach additionally measured 20% CO₂ reduction, *"highlighting the correlation between vehicle speeds influenced by VSL and emissions."*
- MARVEL (Zhang et al., 2024, IEEE Access, §IV): Defines *adaptability* as the goal that *"recommended speed limits should closely reflect actual traffic speeds"* — i.e., minimise the gap between posted and actual speeds, which is operationally equivalent to minimising deceleration events.

The causal chain is: **high speed variance → frequent deceleration/acceleration → high fuel consumption → high emissions**. The mean absolute acceleration `E[|a(t)|]` over all vehicles is the standard kinematic input to emission models (MOVES, COPERT, HBEFA). Our objective directly targets this quantity.

### 2.2 Why NOT merge-zone speed deviation (the v0 reward)

The initial reward (`r44_reward_v0`) penalized `(seg_0_after_speed − 80 kph)²`. The baseline data revealed this is the wrong location:

| Demand | seg_0_after avg speed | seg_0_before avg speed | Where the problem is |
|---|---|---|---|
| 5000 | 110.5 kph | 110.7 kph | Nowhere — free-flow |
| 6500 | 94.8 kph | 93.4 kph | Mild — but merge zone is fine |
| 7000 | 91.2 kph | 47.1 kph avg, 30.3 min | **Upstream, not at merge** |
| 9000 | 78.1 kph | 47.0 kph avg | **Upstream corridor is congested** |

The 4-lane weaving zone (seg_0_after) never breaks down — even at 9000 vph, it maintains 78+ kph. The bottleneck forms upstream at seg_0_before (3 lanes), where the queue from the merge propagates backward. An agent rewarded for merge-zone speed would receive positive feedback while the upstream corridor is gridlocked at 30 kph.

---

## 3. Empirical validation: fixed-VSL diagnostic sweep

### 3.1 Methodology

To determine whether Lagrangian CAV control can reduce deceleration-acceleration activity, we ran a grid of 25 scenarios:

- **VSL levels**: no_control, 50, 70, 90, 110 kph
- **Demands**: 5000, 6000, 6500, 7000, 7500 vph
- **Control mechanism**: `traci.vehicle.slowDown(veh_id, target_ms, 30.0)` applied at every simulation second to all CAVs on the 3 upstream segments (seg_0/1/2_before) and on `ramp_on_transition`
- **CAV penetration**: 50%
- **Episode duration**: 3600 s; warmup: 150 s excluded from metrics
- **All 25 scenarios ran in parallel** (32-core machine, ~580 s total wall-clock)

Per-vehicle acceleration was collected via `traci.vehicle.getAcceleration()` at every simulation second for all vehicles on the upstream corridor (seg_0/1/2/3_before) and on the merge-downstream zone (seg_0_after, seg_1_after).

### 3.2 Metrics collected

| Metric | Source | What it measures |
|---|---|---|
| `avg\|a\|` (m/s²) | `traci.vehicle.getAcceleration()` | Mean absolute acceleration across all upstream vehicle-seconds. Lower = smoother driving = fewer emissions. |
| Brake rate (per 1000 veh-s) | Count of a < −0.5 m/s² | Frequency of noticeable braking events |
| Hard brake rate (per 1000 veh-s) | Count of a < −2.0 m/s² | Frequency of safety-critical braking events |
| Brake amplitude (m/s²) | Mean \|a\| for a < −0.5 | Severity of braking events |
| σ_upstream (kph) | std(speed_s2b, speed_s1b, speed_s0b) per E1 window | Inter-segment speed variance (macroscopic harmonization) |
| Avg upstream speed (kph) | mean(speed_s2b, speed_s1b, speed_s0b) | Throughput proxy — speed must stay above a floor |
| DS flow (vph) | seg_1_after E1 flow | Downstream throughput |
| TTS (vehicle-hours) | Sum of all vehicle-seconds / 3600 | Total time spent — measures delay cost |

### 3.3 Results: deceleration-acceleration

**Mean absolute acceleration (avg|a|, m/s²) — lower is better:**

| VSL | 5000 vph | 6000 vph | 6500 vph | 7000 vph | 7500 vph |
|---|---|---|---|---|---|
| no_control | 0.510 | 0.691 | 0.780 | 0.838 | 0.869 |
| 50 kph | 0.400 (−22%) | 0.408 (−41%) | 0.508 (−35%) | 0.557 (−34%) | 0.569 (−35%) |
| 70 kph | 0.398 (−22%) | 0.412 (−40%) | 0.522 (−33%) | 0.475 (−43%) | 0.582 (−33%) |
| 90 kph | **0.355 (−30%)** | **0.361 (−48%)** | **0.437 (−44%)** | **0.433 (−48%)** | **0.480 (−45%)** |
| 110 kph | 0.387 (−24%) | 0.489 (−29%) | 0.454 (−42%) | 0.521 (−38%) | 0.535 (−38%) |

**Every fixed VSL reduces avg|a| compared to no-control. 90 kph is consistently the best, achieving 30–48% reduction across all demands.**

**Hard braking events (< −2.0 m/s², per 1000 vehicle-seconds):**

| VSL | 5000 vph | 6000 vph | 6500 vph | 7000 vph | 7500 vph |
|---|---|---|---|---|---|
| no_control | 19.3 | 38.0 | 46.1 | 43.9 | 42.9 |
| 50 kph | 14.2 (−26%) | 12.6 (−67%) | 19.7 (−57%) | 26.6 (−39%) | 28.3 (−34%) |
| 70 kph | 17.7 (−8%) | 15.0 (−61%) | 20.9 (−55%) | 16.1 (−63%) | 22.2 (−48%) |
| 90 kph | 20.2 (+5%) | **14.1 (−63%)** | **15.6 (−66%)** | **14.3 (−67%)** | **15.7 (−63%)** |
| 110 kph | 18.2 (−6%) | 19.1 (−50%) | 15.8 (−66%) | 20.5 (−53%) | 18.2 (−58%) |

**At 6000–7500 vph, 90 kph VSL reduces hard braking by 63–67%.** This is the safety-relevant metric — hard braking events are the primary contributor to rear-end collision risk.

### 3.4 Results: the cost of constant VSL

**TTS (vehicle-hours) — lower is better:**

| VSL | 5000 vph | 6000 vph | 6500 vph | 7000 vph | 7500 vph |
|---|---|---|---|---|---|
| no_control | **183.9** | **233.9** | **268.6** | **429.8** | **549.7** |
| 50 kph | 296.8 (+61%) | 388.6 (+66%) | 568.2 (+111%) | 643.1 (+50%) | 663.5 (+21%) |
| 70 kph | 371.9 (+102%) | 987.6 (+322%) | 738.4 (+175%) | 917.1 (+113%) | 782.3 (+42%) |
| 90 kph | 593.2 (+223%) | 998.0 (+327%) | 962.1 (+258%) | 1009.8 (+135%) | 973.7 (+77%) |
| 110 kph | 785.7 (+327%) | 842.8 (+260%) | 998.3 (+272%) | 849.0 (+98%) | 918.3 (+67%) |

**Constant VSL destroys TTS at every demand level.** 90 kph at 6000 vph: TTS increases from 234 to 998 vehicle-hours (+327%). The `slowDown()` command applied continuously to 50% of vehicles creates rolling roadblocks that trap HDVs behind decelerating CAVs.

**Downstream flow (vph):**

| VSL | 5000 vph | 6000 vph | 6500 vph | 7000 vph | 7500 vph |
|---|---|---|---|---|---|
| no_control | 4515 | **5393** | **5855** | **6026** | **6116** |
| 90 kph | 4813 | 5116 (−5%) | 4930 (−16%) | 4810 (−20%) | 5256 (−14%) |

Throughput drops 5–20% under constant 90 kph VSL. The road capacity is wasted because the VSL operates during free-flow periods when it adds no value.

### 3.5 The key insight: temporal selectivity is what the RL agent must learn

The data proves that:

1. **The physics works:** Lagrangian CAV control via `slowDown()` CAN reduce deceleration activity by 30–48% and hard braking by 63–67%.
2. **Constant application destroys throughput:** TTS increases by 77–327% because the VSL operates continuously, including during free-flow when it creates artificial congestion.
3. **The optimal policy is temporally selective:** Apply VSL only during the transitional regime (onset of congestion), not during free-flow and not during established congestion where it cannot help.

A constant policy cannot achieve this — it is all-or-nothing. The RL agent must learn **when** to activate (regime-dependent), **at what magnitude** (demand-dependent), and **for how long** (congestion-evolution-dependent). This is precisely the temporal and magnitude selectivity that continuous-action RL algorithms (SAC, TQC) are designed to learn.

---

## 4. Why SAC as the non-distributional baseline

### 4.1 Algorithm summary

Soft Actor-Critic (Haarnoja et al., 2018, ICML) is an off-policy actor-critic algorithm that maximises a maximum entropy objective:

```
J(π) = Σ_t E[ r_t + α · H(π(·|s_t)) ]
```

where `H(π)` is the entropy of the policy and `α` is the auto-tuned temperature parameter.

### 4.2 Why SAC fits this problem

**Continuous action space.** SAC natively outputs actions from a squashed Gaussian distribution, mapping directly to `Box([60, 40], [120, 90])`. No discretization is needed.

**Off-policy replay buffer.** Each SUMO episode costs 5–30 s wall-clock. Off-policy learning reuses past transitions, achieving 5–10× higher sample efficiency than on-policy methods (PPO, A2C) that discard experience after each update (Haarnoja et al., 2018). For traffic environments where data collection is the bottleneck, this is critical.

**Entropy regularization prevents policy collapse.** In the free-flow regime (5000 vph), any action between 90–120 kph yields similar outcomes. Without entropy regularization, the policy can collapse to an arbitrary constant and lose the ability to explore when conditions change. SAC's entropy term maintains stochastic exploration throughout training.

**Stability.** Double Q-learning mitigates overestimation bias; soft target updates (`τ = 0.005`) prevent oscillation. The Stable-Baselines3 implementation is production-grade.

### 4.3 Why not DDPG or TD3

**DDPG** (Lillicrap et al., 2016): Used by Hua & Fan (2023, 2024) for DSH, but they note: *"DDPG [...] is more difficult to converge. It may not learn anything at the beginning"* (p. 2525). SAC resolves this.

**TD3** (Fujimoto et al., 2018): Deterministic policy with state-independent Gaussian noise — cannot adapt exploration to the traffic regime. Superseded by SAC.

---

## 5. Why TQC as the primary algorithm

### 5.1 Algorithm summary

Truncated Quantile Critics (Kuznetsov et al., 2020, JMLR) extends SAC with distributional critic networks. Instead of learning `Q(s,a) = E[G]`, each critic learns the full quantile function `Z(s,a) ∈ ℝ^N`. The top quantiles are truncated before the Bellman target computation to control overestimation bias.

```
SAC critic output:  Q(s,a) ∈ ℝ       (scalar mean return)
TQC critic output:  Z(s,a) ∈ ℝ^25    (25 quantile values — full distribution)
```

### 5.2 Why distributional critics matter for this specific problem

The baseline data shows that the **transitional regime (6000–7000 vph) is stochastic**: at the same demand, the onset and severity of congestion varies between episodes due to microscopic vehicle insertion randomness (departure time jitter, lane choice, gap acceptance). This is visible in the no-control data:

- At 6500 vph: seg_0_before oscillates between 62 kph and 108 kph across different 30 s windows within a single episode, with σ_upstream reaching 20.8 kph maximum.
- At 7000 vph: breakdown occurs at different times (step 17–20, i.e., t=510–600 s) depending on the specific vehicle realization.

A mean-based critic (SAC) learns `E[G]`, which averages over these outcomes. TQC's quantile critics learn the full shape of `P(G | s, a)` and can distinguish actions that have the same mean return but different tail risks.

### 5.3 CVaR risk-averse evaluation

At evaluation time, the action selection policy can be switched from mean-optimal to risk-averse:

```python
# Standard (mean-optimal):
a* = argmax_a  mean(Z(s, a))

# Risk-averse (CVaR at α = 0.1):
a* = argmax_a  mean(Z(s, a)[:floor(α × N)])   # bottom 10% of quantiles
```

With `N = 25` and `α = 0.1`, the CVaR policy maximises the average of the worst 2–3 quantiles. This is operationally meaningful: the traffic operator cares more about avoiding breakdown (a catastrophic low-return event with high deceleration activity) than about marginally optimising the average case.

### 5.4 TQC inherits all SAC advantages

TQC is architecturally identical to SAC in the actor network. The only difference is in the critic output dimension (N quantile values instead of a scalar). Same entropy regularization, same replay buffer, same hyperparameter structure. The computational overhead is negligible — SUMO simulation dominates wall-clock time.

---

## 6. Observation space design

### 6.1 Available sensors

**E1 induction loops** (48 total, 30 s aggregation):
- 3 positions (entry 5%, mid 50%, exit 95%) × all lanes × 12 segments
- Per-loop: vehicle count, mean speed (m/s), occupancy (%)
- Macroscopic: segment-level flow (vph), space-mean speed, occupancy

**E3 multi-entry-exit zones** (13 total, 30 s aggregation):
- Per-segment: vehicle sum (throughput), mean travel time (s), mean time loss (s)
- Corridor-wide: end-to-end travel time and time loss
- E3 `meanTimeLoss` is a direct measure of delay; E3 `meanTravelTime` captures corridor-level TTS

### 6.2 Proposed observation vector

The state must contain enough information for the agent to:
1. Detect the onset of the transitional regime (speed gradient forming)
2. Assess the current severity of deceleration activity (speed differences between segments)
3. Know its own previous action (for smoothness, restoring Markov property)
4. Observe the ramp merge demand (to anticipate merge-related braking)

**Per-frame features (18 dimensions):**

| Index | Feature | Source | Normalization |
|---|---|---|---|
| 0 | seg_2_before speed | E1 exit | / 36.1 m/s |
| 1 | seg_2_before flow | E1 exit | / 8000 vph |
| 2 | seg_2_before occupancy | E1 exit | / 100% |
| 3 | seg_1_before speed | E1 exit | / 36.1 m/s |
| 4 | seg_1_before flow | E1 exit | / 8000 vph |
| 5 | seg_1_before occupancy | E1 exit | / 100% |
| 6 | seg_0_before speed | E1 exit | / 36.1 m/s |
| 7 | seg_0_before flow | E1 exit | / 8000 vph |
| 8 | seg_0_before occupancy | E1 exit | / 100% |
| 9 | seg_0_after speed | E1 exit | / 36.1 m/s |
| 10 | seg_0_after flow | E1 exit | / 8000 vph |
| 11 | seg_0_after occupancy | E1 exit | / 100% |
| 12 | ramp_on_approach flow | E1 exit | / 2000 vph |
| 13 | ramp_on_merge speed | E1 exit | / 25.0 m/s |
| 14 | seg_1_after flow | E1 exit | / 8000 vph |
| 15 | regime one-hot: FREE_FLOW | Computed | 0 or 1 |
| 16 | regime one-hot: METASTABLE | Computed | 0 or 1 |
| 17 | regime one-hot: CONGESTED | Computed | 0 or 1 |

**Temporal stack:** 3 frames × 18 = 54 dimensions (90 s look-back)

**Static features (2 dimensions):**
- Previous action[0]: (mainline_vsl − 60) / 60 (normalized to [0, 1])
- Previous action[1]: (ramp_vsl − 40) / 50 (normalized to [0, 1])

**Total observation: 56 dimensions.**

Including `prev_action` in the state restores the Markov property for the smoothness reward term (Li et al. [R25], p. 3205: *"two previous actions (speed limits)"* included in the state).

### 6.3 Why 3-frame stack is sufficient

The 3-frame stack provides 90 s of look-back (3 × 30 s windows). The question is whether this captures enough temporal context for the agent to detect congestion onset and learn temporal selectivity.

**Empirical answer from baseline data:**

At 7000 vph (no control), the transition from FREE_FLOW to CONGESTED takes **10 steps (300 s)**:
- Step 10 (t=300 s): seg_0_before drops to 72.6 kph (METASTABLE), seg_2_before still at 97.5 kph
- Step 20 (t=600 s): seg_0_before drops to 44.9 kph (CONGESTED), seg_2_before still at 102.7 kph

The 3-frame stack sees 3 of those 10 transition steps at any given time. But the agent does not need to see the entire transition — it needs to detect that the transition has *started*. The relevant signal is visible in a **single frame**: the spatial speed gradient (seg_0_before = 72 kph while seg_2_before = 97 kph). The 3 frames add the temporal derivative: "seg_0_before is dropping over consecutive windows."

At 6500 vph, the system oscillates in/out of METASTABLE without full breakdown (steps 23, 26, 27, 42, 117 show brief METASTABLE dips). The 3-frame stack captures these oscillations.

**Why not 5 frames (150 s)?** With γ = 0.99 and 120 steps per episode, credit assignment over 5 frames (γ^5 = 0.951) is no better than over 3 frames (γ^3 = 0.970). The marginal information from frames t−4 and t−5 is small — the speed gradient is already fully visible in the most recent 3 frames. The 5-frame stack from the v4 design (§6.1 of speed_harmo_approach_v0.md) was motivated by the 150 s control period at the time; with 30 s control, 3 frames is the right match.

**Fallback if 3 frames proves insufficient:** If SAC/TQC fail to learn temporal selectivity after 500 episodes, RecurrentPPO (SB3-Contrib) with LSTM replaces the frame stack entirely — the LSTM learns its own temporal features. If LSTM succeeds where frame stack fails, the bottleneck was temporal context and should be documented as such.

### 6.4 What about E3 data?

E3 `meanTimeLoss` per segment is a direct measure of delay and could replace or supplement the E1 speed-based features. However, E3 travel time is only available when vehicles have fully traversed the segment (entry-to-exit), introducing a measurement lag of 30–90 s depending on segment length and speed. For the 30 s control period, E1 data (available at every aggregation boundary) provides more timely feedback. E3 corridor-level `meanTravelTime` may be useful as a secondary reward signal (TTS proxy) but is not needed in the observation for regime detection.

**Decision:** Use E1 for the state; E3 `meanTimeLoss` is optionally available as a reward component if the E1-based reward proves insufficient. The sensor infrastructure supports both.

---

## 7. Action space design

### 7.1 Structure

```python
action_space = gym.spaces.Box(
    low=np.array([60.0, 40.0], dtype=np.float32),
    high=np.array([120.0, 90.0], dtype=np.float32),
)
```

- `action[0]`: Mainline VSL (kph), applied uniformly to seg_0/1/2_before via `traci.vehicle.slowDown()` on CAVs
- `action[1]`: Ramp VSL (kph), applied to `ramp_on_transition` via `traci.vehicle.slowDown()` on CAVs

### 7.2 Why [60, 120] for mainline

**Upper bound (120 kph):** The network speed limit is 130 kph (36.11 m/s). Posting 120 kph is effectively "mild restriction" — the `slowDown()` command at 120 kph only affects CAVs traveling above 120 kph, which is a small fraction. This serves as the agent's "do nothing" action without requiring a special no-op.

**Lower bound (60 kph):** Below 60 kph, the VSL is creating conditions more severe than typical congestion. The baseline data shows that no-control congestion at 7000 vph settles at ~45 kph upstream. Posting a VSL below the natural congestion speed is counterproductive — it means the control is making things worse than doing nothing. If conditions require speeds below 60 kph (accidents, severe weather), those are **non-recurrent scenarios** that require different control logic. The action floor of 60 kph explicitly scopes v5 to recurrent bottleneck management. Non-recurrent scenarios (modeled via SUMO TraCI incident injection) are planned for v5.1, with the action range extended downward at that point.

The agent must be *capable of being aware* of critical situations even in v5: the regime detector in the observation classifies CONGESTED when speed < 45 kph, giving the agent a signal that conditions are beyond its control range. The correct learned behavior is to post 60 kph (the floor) and wait for recovery, rather than posting an even lower limit that would compound the problem.

### 7.3 Why [40, 90] for ramp

The ramp merge curve geometry forces vehicles to ~22–29 kph regardless of VSL (baseline data: ramp_on_merge speed is 20–29 kph at all demands). The ramp VSL on `ramp_on_transition` (200 m upstream of the merge curve) controls the approach speed. At 90 kph, vehicles arrive at the merge curve at the geometric limit — effectively no restriction. At 40 kph, vehicles approach slowly, increasing their time-to-merge and reducing merge conflict severity.

### 7.4 Why 2D continuous rather than 1D or discrete

**Why not 1D (mainline only):** The baseline data shows ramp merge speed is 20–29 kph regardless of demand, suggesting the ramp approach speed is an independent control lever. Li et al. [R25] use mainline-only control; Hua & Fan (2023, 2024) also use mainline-only. Independent ramp control is a novel aspect of this work.

**Why not discrete:** As argued in §1, discretizing a 2D action space creates combinatorial explosion. With 7 levels per dimension: 7 × 7 = 49 actions, each needing independent Q-value estimation. SB3's TQC and SAC handle continuous Box spaces natively.

---

## 8. Reward function design

### 8.1 The objective in mathematical terms

The speed harmonization objective is to reduce spatiotemporal speed variance across the upstream corridor, subject to maintaining acceptable throughput and travel time. This definition is consistent with the canonical formulation of speed harmonization in the VSL literature (Kušić et al., 2020; Hua & Fan, 2023; Zhang et al., 2024/MARVEL). Mathematically:

```
min  spatial_gradient(t) + temporal_instability(t)   across the upstream corridor
s.t. throughput ≥ (1 − δ) × throughput_no_control
```

where `spatial_gradient` is the maximum adjacent inter-segment speed difference and `temporal_instability` is the speed change at the downstream observation point between consecutive windows.

The microscopic mean absolute acceleration `avg|a|` (measured via `traci.vehicle.getAcceleration()`) is used as an **independent post-training validation metric** — not as the reward objective — to confirm that macroscopic harmonization translates to vehicle-level driving comfort and emission reduction. This follows the methodology of Hua & Fan (2024, Physica A), who validate their DRL-based DSH using cumulative emergency deceleration as a post-hoc measure of effectiveness.

### 8.2 Reward design principles and their academic basis

The reward must satisfy four requirements:

1. **Penalise spatial speed gradients** — the shockwave front steepness between adjacent segments, which directly causes braking as vehicles traverse the corridor. This is the activation signal used by SPECIALIST (Hegyi et al., 2008).
2. **Penalise temporal speed instability downstream** — measured where the agent has no direct control, so that the signal reflects genuine traffic dynamics (merge conflicts, shockwave arrival), not the agent's own VSL activation.
3. **Constrain throughput** — penalise flow collapse, but not reward flow above a threshold (throughput is a constraint, not an objective).
4. **Penalise action oscillation** — smooth VSL transitions for operational acceptability.

### 8.3 Why r_spatial uses max adjacent gradient, not std()

**The problem with std() over 3 points:** v1 used `np.std([s2, s1, s0])`. With N=3, standard deviation is a degenerate statistic dominated by the single largest outlier. Two fundamentally different traffic conditions get nearly identical penalties:

- `speeds = [100, 100, 50]` → σ = 23.6 kph (shockwave: seg_0 congested, seg_1/2 free)
- `speeds = [100, 75, 50]` → σ = 20.4 kph (smooth gradient: a well-functioning VSL creates this)

No published RL-VSL paper uses σ over 3 spatial points as the reward. Li et al. [R25] use density at the bottleneck (single-point measurement). Han et al. [R26] use jam length and jam speed. MARVEL [R10] uses the gap between posted and actual speeds. Hegyi et al. (2008/SPECIALIST) use the speed *difference* between adjacent cells as the activation trigger.

**The fix:** Replace σ with `max(|s2−s1|, |s1−s0|)` — the maximum adjacent speed difference. This directly measures the shockwave front steepness: if seg_1 is at 100 kph and seg_0 is at 50 kph, vehicles crossing that boundary must decelerate by 50 kph. The adjacent gradient captures this; the std() does not distinguish it from a smooth transition.

```python
adj_diff_21 = abs(s2_kph - s1_kph)
adj_diff_10 = abs(s1_kph - s0_kph)
max_gradient = max(adj_diff_21, adj_diff_10)

r_spatial = -min(max_gradient / 30.0, 1.0)    # ∈ [-1, 0]
```

Normalization: `_GRADIENT_NORM = 30.0 kph`. From baseline data at 7000 vph: seg_2 = 97 kph, seg_0 = 45 kph → adjacent differences up to ~25 kph. 30 kph maps severe gradients to the maximum penalty.

### 8.4 Why r_temporal measures downstream, not upstream

**The critical flaw in the v2-draft temporal term:** The original design measured speed changes across the 3 upstream segments — the same segments where the agent applies VSL. When the agent activates control (drops VSL from 120 to 85 kph), upstream speeds decrease by design. This beneficial speed change would be penalised identically to a harmful stop-and-go oscillation. The agent would be maximally punished for doing exactly the right thing at the moment of activation.

Concrete example:
- Step t: agent posts 120 kph, seg_0_before = 100 kph
- Step t+1: agent posts 85 kph, seg_0_before = 82 kph
- Old temporal term: |82 − 100| = 18 kph → r_temporal = −1.0 (maximum penalty)

This creates a perverse incentive: the agent learns to either never activate or to activate with tiny changes (conflicting with the need to pre-empt breakdown quickly).

**The fix:** Measure temporal speed stability at `seg_0_after` (the weaving zone), where the agent has **no direct control** — CAVs are released downstream of the merge point and accelerate freely. Speed changes at seg_0_after reflect genuine traffic dynamics: merge conflicts, shockwave arrival from the bottleneck, and flow instability. They do NOT reflect the agent's VSL commands.

```python
ds_speed_kph = seg_0_after_speed_ms * 3.6

if prev_ds_speed is not None:
    ds_delta_v = abs(ds_speed_kph - prev_ds_speed)
    r_temporal = -min(ds_delta_v / 15.0, 1.0)   # ∈ [-1, 0]
```

**Academic grounding:**
- Hua & Fan (2024, Physica A, §3.1): Their reward `r = −θ_t` uses a 4.5 m/s² threshold that explicitly filters out controlled decelerations (VSL-induced slowdown is smooth, ~0.1-0.3 m/s²) and only penalises uncontrolled harsh braking. Measuring downstream achieves the same separation between controlled and uncontrolled speed changes.
- SPECIALIST (Hegyi et al., 2008): The detection logic monitors speed changes downstream of the control zone to determine whether the VSL is having the intended effect.

**Normalization:** `_DS_DELTA_V_NORM = 15.0 kph`. seg_0_after at 7000 vph breakdown onset shows per-window speed swings of 15-25 kph. 15 kph maps "moderate instability" to the maximum penalty.

### 8.5 Reward structure: 3 terms (v2)

```
r_t = w_h · r_harmo + w_q · r_throughput + w_a · r_smooth
```

where `r_harmo = blend · r_spatial + (1 − blend) · r_temporal`.

**Term 1a — Spatial harmonization (r_spatial):**
```python
adj_diff_21 = abs(s2_kph - s1_kph)
adj_diff_10 = abs(s1_kph - s0_kph)
max_gradient = max(adj_diff_21, adj_diff_10)

if mean_speed >= 50.0:
    r_spatial = -min(max_gradient / 30.0, 1.0)    # ∈ [-1, 0]
else:
    # Established congestion regime transition: speed-recovery signal.
    # Below 50 kph mean upstream speed, harmonization is no longer
    # actionable.  The reward incentivises the agent to raise speeds
    # back above the floor.  At mean_speed=0 → r=-1; at floor → r=0.
    r_speed_recovery = -1.0 + (mean_speed / 50.0)
    r_gradient_penalty = -min(max_gradient / 30.0, 1.0)
    r_spatial = min(r_speed_recovery, r_gradient_penalty)
```

**Term 1b — Temporal harmonization (r_temporal):**
```python
ds_speed_kph = seg_0_after_speed_ms * 3.6   # downstream, uncontrolled

if prev_ds_speed is not None:
    ds_delta_v = abs(ds_speed_kph - prev_ds_speed)
    r_temporal = -min(ds_delta_v / 15.0, 1.0)   # ∈ [-1, 0]
```

Captures merge-zone instability without penalising the agent's own VSL activation. First step after reset returns 0.

**Term 2 — Throughput constraint (r_throughput):**
```python
flow_ratio = seg_1_after_flow_vph / ref_flow_vph
threshold = 0.85

if flow_ratio >= threshold:
    r_throughput = 0.0                                              # acceptable — no penalty
else:
    r_throughput = -(threshold - flow_ratio) / threshold            # ∈ [-1, 0]
```

Throughput is a **constraint, not a bonus**. When downstream flow is above 85% of the reference (6000 vph), the agent receives no reward and no penalty for throughput. Below 85%, a linear penalty activates proportional to the shortfall. This is consistent with the thesis framing ("subject to maintaining throughput") and with MARVEL [R10] (§IV: *"mobility: speed limits should not substantially compromise traffic flow"*). The threshold-based design avoids rewarding the agent for artificially smoothing flow while destroying TTS — a failure mode observed with the original linear bonus design at 5000 vph.

**Term 3 — Action smoothness (r_smooth):**
```python
delta = (action - prev_action) / action_range
r_smooth = -min(np.linalg.norm(delta), 1.0)    # ∈ [-1, 0]
```

Prevents VSL oscillation. SAC's entropy regularization already encourages smooth exploration, but this explicit term penalizes large action jumps that would confuse the traffic flow and create transient deceleration spikes.

**Weights (initial, subject to ablation):**

| Weight | Value | Rationale |
|---|---|---|
| w_h | 0.55 | Primary objective: spatiotemporal speed harmonization |
| w_q | 0.30 | Throughput constraint — the fixed-VSL data shows throughput loss is the main risk |
| w_a | 0.15 | Operational constraint: smooth VSL transitions |
| blend | 0.50 | Equal weight spatial (gradient) + temporal (downstream stability); ablation: 0.3/0.7 and 0.7/0.3 |

### 8.5 Reward component reporting

`r44_reward_v2` reports 5 components in `RewardSignal.components`:

| Key | Range | Meaning |
|---|---|---|
| `harmonization` | [−1, 0] | Blended r_harmo (what enters the total) |
| `spatial` | [−1, 0] | Max adjacent speed gradient (shockwave steepness) |
| `temporal` | [−1, 0] | Downstream (seg_0_after) inter-window speed change |
| `throughput` | [−1, 0] | Throughput penalty (0 when flow ≥ 85% of ref; linear penalty below) |
| `smoothness` | [−1, 0] | Action delta penalty |

During training, Tensorboard can plot `spatial` and `temporal` separately to verify that the temporal term provides signal when spatial alone is flat (the 7500+ vph regime). The throughput component should be near-zero during free-flow and mildly negative during over-restriction.

### 8.6 What about TTS as a reward term?

TTS (Total Time Spent) is available via `tts_increment_s` in TrafficMetrics (vehicle count × aggregation time). It could replace or supplement the throughput term. However, TTS conflates two effects:

- Vehicles spending more time because they are traveling slower (the intended harmonization effect — acceptable)
- Vehicles spending more time because they are queued (the unintended congestion effect — unacceptable)

The throughput term (downstream flow) distinguishes these: if flow is maintained but TTS increases slightly, the agent is slowing vehicles (good). If flow drops AND TTS increases, the agent is creating congestion (bad). TTS alone cannot make this distinction.

**Decision:** Use throughput (flow) rather than TTS as the constraint term. TTS is reported as an evaluation metric but not used in the reward.

---

## 9. Training strategy

### 9.1 Demand sampling

Each episode samples demand uniformly from [3000, 8000] vph. This ensures:
- The agent sees free-flow episodes (3000–5500) where it must learn to do nothing
- The agent sees transitional episodes (6000–7000) where it must learn to intervene
- The agent sees congested episodes (7000–8000) where it must learn to accept partial control

This is consistent with MARVEL [R10] (*"each agent must adapt to the surrounding traffic conditions"*) and Li et al. [R25] (training on both stable and fluctuating demand scenarios).

### 9.2 Algorithm comparison

| Algorithm | Role | Library | Key difference |
|---|---|---|---|
| PPO | On-policy baseline | `stable_baselines3.PPO` | No replay buffer; fresh rollouts |
| SAC | Off-policy non-distributional | `stable_baselines3.SAC` | Scalar critics; mean return |
| TQC | Off-policy distributional (primary) | `sb3_contrib.TQC` | Quantile critics; full return distribution |

All three use identical hyperparameters where applicable (learning rate, network architecture, γ, τ) to ensure fair comparison. The only difference between SAC and TQC is the critic representation.

### 9.3 SB3 / SB3-Contrib configuration

| Parameter | SAC | TQC |
|---|---|---|
| Library | `stable_baselines3.SAC` | `sb3_contrib.TQC` |
| Policy | `MlpPolicy` | `MlpPolicy` |
| `learning_rate` | 3e-4 | 3e-4 |
| `buffer_size` | 200,000 | 200,000 |
| `learning_starts` | 10,000 | 10,000 |
| `batch_size` | 256 | 256 |
| `tau` | 0.005 | 0.005 |
| `gamma` | 0.99 | 0.99 |
| `train_freq` | 1 | 1 |
| `gradient_steps` | 1 | 1 |
| `net_arch` | [256, 256] | [256, 256] |
| `n_critics` | 2 | 2 |
| `n_quantiles` | — | 25 |
| `top_quantiles_to_drop_per_net` | — | 2 |

### 9.4 The "do nothing" region: why no action reparameterization is needed

SAC's initial policy is a squashed Gaussian centered near the middle of the action range. For the mainline dimension, this is ~90 kph — a moderate restriction. During free-flow episodes (3000–5500 vph), this initial restriction is harmful: it creates rolling roadblocks that increase σ_upstream and reduce flow.

**Concern:** The top portion of the action range [~100, 120 kph] produces near-identical outcomes at free-flow (all are effectively "do nothing"). Exploration in this plateau wastes early training episodes.

**Analysis — the reward signal is clear and immediate:**

With the v2 reward (max adjacent gradient, downstream temporal, threshold-based throughput penalty):

| Scenario (5000 vph) | Max gradient | DS flow | r_spatial | r_q (thr=0.85) | r_harmo (approx) | Total (approx) |
|---|---|---|---|---|---|---|
| No control | ~2–3 kph | 4515 (0.753) | −0.08 | −0.114 | −0.04 | **−0.056** |
| 90 kph VSL | ~30 kph | 4813 (0.802) | −1.00 | −0.056 | −0.50 | **−0.292** |

The gap between no-control and 90 kph VSL at free-flow is **−0.056 − (−0.292) = +0.236** in favour of no-control. This is a strong, unambiguous learning signal: unnecessary restriction is clearly worse than doing nothing. The throughput penalty is mild in both cases (flow is near the 85% threshold), so the signal is dominated by the spatial gradient term — the agent learns that creating a large speed gradient at free-flow is costly.

**Why SAC self-corrects within ~50–100 episodes:**

1. **Entropy regularization** ensures the policy samples broadly during early training, including the high-action [100, 120] kph region where "do nothing" is optimal.
2. **The regime one-hot** (FREE_FLOW / METASTABLE / CONGESTED) in the state gives the critic a direct feature to condition on. After observing a few dozen episodes where FREE_FLOW + low action → negative reward and FREE_FLOW + high action → positive reward, the critic learns the conditional value function.
3. **The off-policy replay buffer** retains both good and bad episodes. The critic learns from both simultaneously — it does not need to re-explore the plateau each epoch.

**Why action reparameterization (e.g., restriction fraction ∈ [0, 1]) is not necessary:**

SB3's SAC implementation uses tanh squashing: raw policy output ∈ ℝ → tanh → [−1, 1] → affine → [60, 120]. The initial μ ≈ 0 maps to ~90 kph. After the critic learns the regime-dependent value landscape, the actor's μ shifts to a regime-conditional value. The plateau at [100, 120] is not a problem because:
- The critic correctly assigns similar Q-values to all actions in the plateau → the actor gradient is small there → the policy naturally moves toward the informative region [60, 100] during transitional episodes.
- During free-flow episodes, the critic gradient points toward high actions → the policy converges to ~120 kph.

**Conclusion:** No code change needed. The reward signal is strong enough (0.236 gap) and SAC's architecture handles plateaus by design. Monitor the first 100 episodes: if the mean episode reward at 5000 vph is not trending positive by episode 100, the issue is elsewhere (likely reward weights, not action parameterization).

---

## 10. What TQC must demonstrate

### 10.1 Success criteria

1. **SAC/TQC > no-control:** The primary agent reduces avg|a| (measured post-hoc via `traci.vehicle.getAcceleration()`) by at least 15% at 6000–7000 vph while limiting TTS increase to < 30%.
2. **SAC/TQC > fixed-VSL-90:** The agent achieves comparable deceleration reduction (avg|a| ≤ 0.45 m/s²) with less throughput loss (< 10% vs. the 14–20% from constant 90 kph).
3. **TQC ≠ SAC:** TQC produces measurably different policies (different action distributions, different tail-risk behavior, or different breakdown avoidance rates).

### 10.2 If TQC = SAC (negative distributional result)

If TQC and SAC produce identical policies, the thesis documents this as:

> *"The return distribution at a ramp merge under Lagrangian CAV control is sufficiently unimodal in the transitional regime that distributional critics provide no additional information beyond the mean. This suggests that the stochasticity in merge outcomes is smoothed by the 30 s aggregation window and the 50% CAV penetration rate."*

This is publishable as a characterization of when distributional RL does and does not add value in traffic control.

### 10.3 If neither beats no-control

If no RL agent reduces deceleration activity without destroying throughput:

1. The reward ablation study identifies which terms conflict
2. The fixed-VSL data proves the physics works — the failure is in the RL formulation, not the control mechanism
3. The thesis documents the design space exploration as a systematic negative result with clear recommendations for future work (e.g., model-based components, MPC+RL hybrid)

---

## 11. Future extensions (v5.1+)

| Extension | Scope | Why deferred |
|---|---|---|
| Non-recurrent scenarios (accidents, weather) | Extend action range below 60 kph; add incident flag to state | Requires SUMO TraCI incident modeling |
| Multi-zone differential VSL | Per-segment independent actions (6D Box) | Combinatorial; validate single-zone first |
| MPR sensitivity sweep | Train at 25%, 50%, 75%, 100% CAV | Independent variable; run after architecture is validated |
| IQN (Implicit Quantile Networks) | Replace TQC quantile critics with implicit quantiles | Not in SB3; requires custom implementation |
| E3-based reward components | Add `meanTimeLoss` to reward for TTS control | Evaluate whether E1-only reward is sufficient first |

---

## 12. References

- **[R1]** Bellemare, M.G., Dabney, W., Munos, R. (2017). A Distributional Perspective on Reinforcement Learning. *ICML 2017*.
- **[R2]** Dabney, W., Rowland, M., Bellemare, M.G., Munos, R. (2018). Distributional Reinforcement Learning with Quantile Regression. *AAAI 2018*.
- **[R3]** Vinitsky, E. et al. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*, 759–765.
- **[R10]** Zhang, Y. et al. (2024). MARVEL: Bringing Multi-Agent Reinforcement-Learning Based Variable Speed Limit Controllers Closer to Deployment. *IEEE Access, 12*, 161995–162012.
- **[R15]** Gregurić, M. et al. (2020). Application of Deep Reinforcement Learning for Variable Speed Limit Control. *Applied Sciences, 10*, 4917. doi:10.3390/app10144917
- **[R25]** Li, Z., Liu, P., Xu, C., Duan, H., Wang, W. (2017). Reinforcement Learning-Based Variable Speed Limit Control Strategy to Reduce Traffic Congestion at Freeway Recurrent Bottlenecks. *IEEE T-ITS, 18*(11), 3204–3217.
- **[R26]** Han, Y. et al. (2022). A New Reinforcement Learning-Based Variable Speed Limit Control Approach to Improve Traffic Efficiency Against Freeway Jam Waves. *TRC, 144*, 103903.
- Haarnoja, T. et al. (2018). Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor. *ICML 2018*.
- Kuznetsov, A. et al. (2020). Controlling Overestimation Bias with Truncated Mixture of Continuous Distributional Quantile Critics. *JMLR, 21*(167), 1–56.
- Hua, C., Fan, W.D. (2023). Dynamic Speed Harmonization for Mixed Traffic Flow on the Freeway Using Deep Reinforcement Learning. *IET-ITS, 17*, 2519–2530.
- Hua, C., Fan, W.D. (2024). Safety-Oriented Dynamic Speed Harmonization of Mixed Traffic Flow in Nonrecurrent Congestion. *Physica A, 634*, 129439.
- Kušić, K. et al. (2020). An Overview of Reinforcement Learning Methods for Variable Speed Limit Control. *Applied Sciences, 10*, 4917.
- Lillicrap, T.P. et al. (2016). Continuous Control with Deep Reinforcement Learning. *ICLR 2016*.
- Fujimoto, S. et al. (2018). Addressing Function Approximation Error in Actor-Critic Methods. *ICML 2018*.

---

## Appendix A: Raw data location

All baseline data is stored in `tests/results/`:

| Dataset | Path | Contents |
|---|---|---|
| No-control baseline (2500–7000 vph) | `nocontrol_ramps_v1_18-03-2026_14-08-30/` | Per-step CSV per demand; E1 speed/flow/occ |
| No-control extended (7500–9000 vph) | `nocontrol_extended_18-03-2026_16-04-06/` | Per-step CSV per demand |
| Fixed-VSL sweep v1 (no accel data) | `fixed_vsl_sweep_18-03-2026_16-44-23/` | Per-step CSV; speed/flow/sigma only |
| Fixed-VSL sweep v2 (with accel/decel) | `fixed_vsl_sweep_v2_18-03-2026_17-09-52/` | Summary CSV with all metrics from §3 |

Reproduction: `python3 tests/run_fixed_vsl_sweep_v2.py` (requires SUMO ≥ 1.21, ~10 min on 25 cores).

---

*Document version: v2.0, 2026-03-18. Supersedes the algorithm-only v1.0.*
