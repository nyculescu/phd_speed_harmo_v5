# v5.1 Baseline: Validated SAR Framework and Training Infrastructure

*This document provides thesis-ready academic text describing the v5.1-baseline milestone — the validated research infrastructure from which all experimental results are produced. It covers the research motivation, the simulation environment, the control architecture, the state-action-reward framework, and the algorithmic choices, with inline citations suitable for a doctoral dissertation.*

---

## 1. Research Context and Motivation

Speed harmonisation is a traffic management strategy that reduces speed variance among vehicles to dampen shockwave propagation, decrease braking frequency, and improve fuel efficiency at bottleneck locations (Hegyi et al., 2008 [R21]; Li et al., 2017 [R25]). Variable Speed Limit (VSL) systems have been deployed on motorways worldwide since the 1990s, predominantly using rule-based reactive logic (Zhang et al., 2024 [R10]). However, these systems are constrained by the requirement for hand-tuned activation thresholds, dependence on macroscopic traffic models (the fundamental diagram), and inability to adapt to non-stationary demand patterns (Han et al., 2022 [R26]).

Reinforcement learning (RL) has emerged as a promising alternative because it learns control policies directly from interaction data without requiring an explicit traffic model (Kušić et al., 2020 [R27, overview paper]; Li et al., 2017 [R25]). The integration of Connected and Automated Vehicles (CAVs) further expands the control design space: whereas traditional VSL systems post speed limits on overhead gantries and rely on imperfect driver compliance, Lagrangian control via CAVs enables direct per-vehicle speed commands through vehicle-to-infrastructure (V2I) communication (Vinitsky et al., 2018 [R3]; Ko et al., 2020 [R24]).

Despite these advances, the existing RL-based VSL literature exhibits several limitations that this work addresses:

1. **Uniform control zones.** Most studies apply a single speed limit across all lanes (Li et al., 2017 [R25]; Han et al., 2022 [R26]; Zhang et al., 2024 [R10]). This ignores the inter-lane speed gradients that arise naturally at merge bottlenecks, where the merge lane (lane 0) is systematically slower than the fast lane (lane 2) — a difference of 7–13 km/h observed in our feasibility study.

2. **Deterministic demand scenarios.** Training on fixed-demand profiles produces policies that converge to trivially optimal static strategies. Our v5.0 feasibility study demonstrated that five DRL seeds independently converged to the same fixed 110 km/h policy, providing no advantage over a lookup table.

3. **Mean-optimal policies.** Standard RL algorithms (DQN, SAC) optimise the expected return, which is inappropriate for safety-critical traffic control where worst-case outcomes (merge failures, congestion cascades) carry disproportionate cost. No prior traffic RL study has applied distributional RL with risk-sensitive inference (CVaR) to VSL control.

4. **Discrete action spaces in continuous control problems.** Per-lane differential VSL with discrete actions creates combinatorial explosion: three lanes with seven speed levels each produce 343 actions, making DQN-family algorithms computationally prohibitive (Wu et al., 2020 [R29]; Hua & Fan, 2023 [R4]).

This work addresses all four limitations by introducing a per-lane Lagrangian control architecture with continuous action space, trained under stochastic demand with anomaly injection, using Truncated Quantile Critics (TQC; Kuznetsov et al., 2020 [R27]) — a distributional RL algorithm that has not previously been applied to traffic speed harmonisation.

---

## 2. Simulation Environment

### 2.1 Network Topology

The simulation environment is implemented in SUMO (Simulation of Urban Mobility, v1.26) using the ramps_v2 network: a 5.5 km, three-lane freeway mainline with a single on-ramp merge and no off-ramp. The merge point is located at junction J4, where a one-lane ramp (1000 m total: 700 m approach, 200 m transition, 100 m merge) merges into the mainline lane 0 with yield priority (SUMO state `m`). The mainline preserves three lanes throughout — there is no lane drop or dedicated ramp lane.

This topology was selected after a systematic evaluation of alternatives. The initial v5.0 design employed a 4→3 lane-drop geometry, but a comprehensive feasibility sweep (990 scenarios, 18 demand levels × 55 VSL combinations) revealed that the lane-drop bottleneck is governed by microscopic gap-acceptance dynamics rather than macroscopic flow competition. Upstream VSL could not influence the gap-acceptance process, and every VSL combination either matched or degraded no-control performance. The ramp-merge topology, by contrast, creates a flow-competition bottleneck where upstream mainline speed control directly affects the gap structure available to merging ramp vehicles — the mechanism documented by Li et al. (2017) [R25] and Ko et al. (2020) [R24].

A second feasibility sweep on the ramps_v2 topology confirmed that moderate VSL (110 km/h uniform) reduces upstream speed variance by 17–33%, braking rate by 35–41%, and hard braking by 53–57% compared to no-control, with less than 0.5% throughput loss, across the demand range 5000–7250 vehicles per hour (vph).

### 2.2 Sensor Infrastructure

The network is instrumented with 63 E1 induction loop detectors and 10 E3 multi-entry-exit detectors, all operating at 30-second aggregation intervals. Per-lane E1 detectors (entry, mid-point, and exit) are placed on every segment, with particular density at the merge approach (seg_0_before) and merge zone (seg_0_after) where per-lane speed, flow, and occupancy are the primary observables. E3 detectors measure segment travel time, vehicle count, and halting events — the latter being a direct measure of merge delay that point-based E1 detectors cannot capture.

### 2.3 Mixed Traffic Fleet

The vehicle fleet models heterogeneous traffic at 50% CAV market penetration rate (MPR). Human-driven vehicles (HDVs) are generated with four base vehicle classes (passenger cars 70%, passenger vans 12%, trucks 12%, truck-trailers 6%) using the Krauss car-following model with randomised parameters: reaction time τ ∈ [1.2, 2.0] s, driving imperfection σ ∈ [0.30, 0.50], and minimum gap scaled ×[0.9, 1.1]. Among HDVs, 4% are classified as reckless outliers with elevated speed factor (1.15–1.25×), shortened reaction time (τ ∈ [0.6, 0.9] s), reduced following gap (×0.5–0.7), and aggressive lane-change parameters (lcAssertive ∈ [1.5, 3.0]) — modelling the real-world distribution of aggressive drivers that trigger merge conflicts.

CAVs are deterministic (σ = 0, τ = 1.0 s) with 10% higher acceleration capability and 50% smaller following gaps, reflecting platooning-capable V2I-connected vehicles (Vinitsky et al., 2018 [R3]).

Weather effects modify vehicle dynamics through multiplicative factors on acceleration, deceleration, minimum gap, reaction time, and speed factor. Four profiles are defined: clear (baseline), rain (15% reduced braking, 30% larger gaps), heavy rain (30% reduced braking, 50% larger gaps), and fog (60% increased reaction time, 25% speed reduction). Weather is sampled per scenario during pool generation, following the weighted distribution clear:0.7, rain:0.2, fog:0.1.

### 2.4 Stochastic Demand Generation

Each training episode uses a unique demand profile generated by piecewise cubic Hermite spline interpolation through N random control points (N ∈ [5, 10]), adapted from the v4 demand generation system. Control point positions are sampled uniformly along the episode timeline with minimum 5% spacing; control point demand levels are sampled from either a peak range (5500–8000 vph) or a base range (2500–4000 vph), with episode boundaries pinned to the base range. Tangent values at each control point are estimated from finite differences and randomised by a steepness multiplier (∈ [0.5, 4.0]).

Two-component noise is added to the interpolated curve: heteroscedastic white noise (amplitude proportional to local demand level) and a detrended random walk (low-frequency wander). The resulting profile exhibits the irregular peaks, secondary surges, dips within plateaus, and asymmetric rise/fall patterns characteristic of real detector data (Highway Capacity Manual, 6th Ed., Ch. 11).

For the training phase, a focused-band generator produces flat demand within the trainable range (5500–7250 vph) with ±200 vph Gaussian noise per 30-second bin. This ensures the agent trains predominantly in the regime where VSL has demonstrated efficacy. The full Hermite profiles are reserved for generalization evaluation.

Scenarios are pre-generated before training and stored as paired .rou.xml (vehicle schedule) and .sumocfg (SUMO configuration) files. A ScenarioManager provides each parallel SUMO worker with independently shuffled scenario sequences, ensuring diversity without inter-process synchronisation overhead.

### 2.5 Anomaly Injection

In 15% of training episodes, one of three anomaly types is injected during the peak demand phase:

- **Ramp demand spike**: a 2× burst of ramp vehicle insertions for 60–120 seconds, simulating incident-triggered ramp overflow.
- **Speed reduction**: all vehicles on seg_1_before are slowed to 40 km/h for 90–180 seconds, simulating rubbernecking or debris on the roadway.
- **Lane closure (lite)**: the fast lane (lane 2) of seg_0_before is restricted to 10 km/h for 120–240 seconds, simulating a partial obstruction.

Anomaly status is observable in the state vector (binary flag), reflecting the realistic assumption that incident detection systems (e.g., video analytics or CAV reports) provide timely notification. The purpose of anomaly injection is to create genuine bimodal return distributions — a condition under which distributional RL (TQC) is expected to outperform standard RL (SAC) by learning to represent and act on both modes rather than averaging them.

---

## 3. Control Architecture

### 3.1 Mixed Lagrangian-Eulerian Design

The control architecture implements a two-zone mixed paradigm that combines Lagrangian control (direct CAV commands) with Eulerian control (zone-level posted speed limits):

**Zone 1 — Virtual per-lane VSL (seg_0_before, Lagrangian).** Three independent speed limits are applied to the three mainline lanes in the 1000 m segment immediately upstream of the merge. Each CAV on this segment receives a `traci.vehicle.slowDown()` command at every simulation second, with the target speed determined by its current lane index. HDVs are influenced indirectly through the car-following response to controlled CAVs ahead — at 50% MPR, approximately every second vehicle is a CAV, creating a pacing effect. This mechanism is consistent with the Lagrangian paradigm introduced by Vinitsky et al. (2018) [R3] and extended to per-lane control by Wu et al. (2020) [R29].

**Zone 2 — Physical VSL (seg_1_before, Eulerian; Box(5) only).** A single uniform speed limit is posted on the 1000 m pre-conditioning segment, 1000–1500 m upstream of the merge. Implementation uses `traci.edge.setMaxSpeed()`, which the Krauss car-following model enforces as a lane speed cap. HDV compliance is 92% (radar enforcement assumption; Hua & Fan, 2023 [R4]); the remaining 8% retain free-flow speed (120 km/h). This creates per-action stochastic response — the same posted speed limit produces a distribution of downstream speeds depending on which HDVs comply.

**Uncontrolled zones.** Segments seg_2_before and seg_3_before serve as free-flow reference and incoming demand measurement. The merge zone (seg_0_after) and downstream (seg_1_after) are observation-only.

### 3.2 Control Timing

The control period is 30 seconds, matching the E1 detector aggregation window. At each control step, the agent observes the latest 30-second traffic measurements, selects a 4D or 5D continuous action, and the environment applies the corresponding speed limits for the next 30 simulation seconds. Within each 30-second window, `slowDown()` commands are reissued every simulation second to capture newly arriving CAVs and handle lane changes (Vinitsky et al., 2018 [R3], p. 761). An episode lasts 3600 simulation seconds (120 control steps).

### 3.3 MUTCD Safety Constraints

Two operational constraints are enforced at the action application level, not learned:

1. **Adjacent lane gradient**: |a[i] − a[i+1]| ≤ 10 km/h for i ∈ {0,1} (MUTCD §2C.08: maximum speed differential between adjacent lanes to prevent dangerous lane-change conflicts).
2. **Step-down constraint (Box(5) only)**: a[4] ≥ max(a[0], a[1], a[2]) − 16 km/h (MUTCD maximum 10 mph drop between consecutive VSL gantries; Zhang et al., 2024 [R10]).

---

## 4. State-Action-Reward Framework

### 4.1 Observation Space

The observation is a 77-dimensional vector comprising a 3-frame temporal stack of 24 traffic features and 5 static context features, all normalised to [0, 1]:

The 24 per-frame features include: aggregate speed, flow, and occupancy for seg_2_before, seg_1_before (6 features); per-lane speed, flow, and occupancy for seg_0_before lanes 0, 1, 2 (9 features); aggregate speed, flow, and occupancy for the merge zone seg_0_after (3 features); ramp approach flow and ramp merge speed (2 features); downstream seg_1_after flow (1 feature); and a one-hot regime indicator (free-flow, metastable, congested; 3 features). The static features are the four previous action values (normalised) and the anomaly-active binary flag.

The 3-frame stack provides 90 seconds of temporal context, allowing the agent to observe demand trends and speed wave propagation without requiring recurrent architecture (Sutton & Barto, 2018 [R12], §17.3).

### 4.2 Action Space

**Box(4) (pure Lagrangian)**: a ∈ ℝ⁴ with a[0:3] ∈ [60, 120] km/h (per-lane mainline) and a[3] ∈ [40, 90] km/h (ramp transition).

**Box(5) (mixed Lagrangian-Eulerian)**: Box(4) augmented with a[4] ∈ [60, 120] km/h (physical VSL on seg_1_before).

The continuous action space avoids the combinatorial explosion of discrete per-lane control: three lanes at seven discrete levels produce 343 combinations, which would require 8,575 output neurons for QR-DQN with 25 quantiles (Wu et al., 2020 [R29]).

### 4.3 Reward Function (v4)

The reward function uses five terms with quadratic penalties and no dead zones:

r_t = κ · (w_h · r_harmo + w_t · r_temporal + w_q · r_throughput + w_l · r_lane + w_s · r_smooth)

where κ = 5 is a scale factor calibrated to produce episode returns in [−600, 0], matching SAC/TQC default hyperparameters.

| Term | Weight | Formula | Purpose |
|---|---|---|---|
| r_harmo | 0.35 | −min((σ_combined / 5.0)², 1.0) | Upstream speed variance (segment + per-lane) |
| r_temporal | 0.20 | −min((Δv_ds / 8.0)², 1.0) | Downstream temporal speed stability |
| r_throughput | 0.25 | clip(flow_ds/flow_ref − 1, −1, 0.1) | Continuous throughput signal (no dead zone) |
| r_lane | 0.15 | −min((max_lane_gap / 15.0)², 1.0) | Inter-lane speed equalisation |
| r_smooth | 0.05 | −min((‖Δa‖/0.5)², 1.0) | Action smoothness (4D L2 norm) |

The three-term core (harmonisation, throughput, smoothness) mirrors the reward structure of the MARVEL field-deployed controller (Zhang et al., 2024 [R10]). The two additional terms address per-lane control specifics: r_lane penalises dangerous inter-lane speed differentials that cause lane-change conflicts near the merge, and r_temporal rewards downstream speed stability.

The quadratic penalty form was adopted after diagnostic analysis of the initial linear-clipped reward (v3) revealed a signal of only 3.0 reward points between the no-control baseline and the known-optimal static policy over a full 120-step episode. The quadratic form amplifies the signal to 85.8 points (28.6× improvement), with four of five terms rewarding productive VSL actions rather than penalising them.

---

## 5. Algorithm Selection

### 5.1 Soft Actor-Critic (SAC)

SAC (Haarnoja et al., 2018 [R28]) serves as the non-distributional baseline. Its maximum-entropy objective J(π) = Σ E[r + α H(π(·|s))] prevents policy collapse to degenerate solutions, and the automatically tuned temperature parameter α maintains exploration throughout training without a decaying ε-schedule. SAC is implemented via Stable-Baselines3 (v2.7.1).

### 5.2 Truncated Quantile Critics (TQC)

TQC (Kuznetsov et al., 2020 [R27]) is the primary algorithm. It extends SAC with N_c distributional critics, each outputting N_q quantile estimates of the return distribution Z(s, a). Overestimation bias — amplified in higher-dimensional continuous action spaces — is controlled by truncating the top d quantiles per critic before computing the Bellman target.

TQC is hypothesised to outperform SAC in this environment for three reasons:

1. **Bimodal return structure.** Anomaly injection (15% of episodes) creates a bimodal return distribution. SAC's single Gaussian critic averages the two modes; TQC's quantile critics represent both, enabling risk-sensitive action selection via CVaR at α = 0.10 (selecting actions that maximise the mean of the worst 10% of outcomes).

2. **Per-action stochastic response (Box(5)).** The physical VSL on seg_1_before produces different downstream speeds for the same posted limit, depending on which HDVs (8%) ignore the sign. This irreducible variance is captured by TQC's distributional critics but marginalised by SAC's expected-value critic.

3. **Overestimation control.** With 4D continuous actions, the maximum over randomly sampled actions in the critic target can systematically overestimate Q-values. TQC's top-quantile truncation provides tighter estimates (Kuznetsov et al., 2020), preventing the mid-training instability observed in SAC seed 2 during the v5.0 validation run.

The configuration uses 5 critics with 25 quantiles each and drops the top 2 quantiles per critic network, following the original paper's recommended settings.

### 5.3 Novelty

To the best of our knowledge, no prior work has applied TQC to traffic speed harmonisation. The closest precedents are QR-DQN for discrete VSL (not applied in the traffic literature) and SAC for continuous VSL (Hua & Fan, 2023 [R4]; Wu et al., 2020 [R29]). This work contributes the first application of distributional continuous-action RL to per-lane VSL control in mixed CAV traffic under stochastic demand conditions.

---

## 6. Experimental Design

### 6.1 Protocol

The experimental protocol consists of four experiments designed to isolate the contributions of distributional critics and the physical VSL dimension:

| Experiment | Algorithms | Action space | Research question |
|---|---|---|---|
| Exp. 1 | SAC vs TQC | Box(4) | Does distributional RL improve pure Lagrangian control? |
| Exp. 2 | SAC vs TQC | Box(5) | Does the distributional advantage increase with HDV compliance noise? |
| Exp. 3 | Box(4) vs Box(5) | Both algos | Does the physical VSL add value beyond Lagrangian-only? |
| Ablation | Box(3) | Both algos | Does ramp speed control contribute? |

Each experiment trains 5 independent seeds for 1,000,000 timesteps (~8,333 episodes). Training uses pre-generated scenario pools (200 scenarios per pool) with focused demand in the trainable band (5500–7250 vph) and weather sampling (clear 70%, rain 20%, fog 10%). Evaluation occurs every 10,000 timesteps on 10 episodes with deterministic policy (no exploration noise).

### 6.2 Metrics

**Primary metrics** (algorithmic comparison):
- Mean episodic return and standard deviation across seeds
- CVaR at α = 0.10 (mean of worst 10% of evaluation episodes)
- Return variance trajectory (does it grow or shrink during training?)
- Seed-to-seed reproducibility (inter-seed standard deviation)

**Secondary metrics** (traffic performance):
- Upstream speed variance σ (km/h) at seg_0_before
- Inter-lane speed gradient max(|L0−L1|, |L1−L2|) at seg_0_before
- Downstream throughput (vph) at seg_1_after exit
- Merge zone travel time (s) from E3 seg_0_after
- Ramp gap-wait halts from E3 ramp_on_merge
- Braking rate and hard braking rate per 1000 vehicle-seconds

### 6.3 Statistical Analysis

Comparisons use Welch's t-test for mean returns, Mann-Whitney U for non-parametric comparison, and bootstrap 95% confidence intervals (10,000 resamples) for CVaR differences. Effect sizes are reported as Cohen's d. Multiple comparisons across experiments are corrected with the Bonferroni method.

---

## 7. Baseline Validation Results

The v5.1-baseline milestone was established through three validation phases:

**Phase 1 — Feasibility sweep (990 scenarios).** A comprehensive 2D action space mapping across 18 demand levels (3000–10000 vph) and 55 mainline/ramp VSL combinations confirmed that moderate mainline VSL (110 km/h) reduces upstream speed variance by 17–33% with <0.5% throughput loss in the 5000–7250 vph range. Below 5000 vph, no VSL improves on the no-control baseline. Above 7250 vph, only aggressive restriction (60–70 km/h) helps, at significant throughput cost. Critically, the ramp VSL dimension showed negligible independent effect — the mainline speed limit dominates merge dynamics.

**Phase 2 — Reward function calibration.** The initial reward function (v3, linear-clipped) produced a signal of only 3.0 reward points between no-control and optimal over a full episode, with three of five terms penalising productive actions. Reward v4 (quadratic penalties, no dead zone, 5× scale) amplified the signal to 85.8 points (28.6×), enabling gradient-based learning.

**Phase 3 — Static strategy comparison (270 episodes).** Nine fixed strategies (no-control + 4 uniform + 4 differential per-lane) were evaluated across 30 stochastic demand seeds with anomaly injection. Results confirmed: (a) no single static strategy dominates across all seeds (reward std 55–78); (b) anomaly episodes are 135–152 points worse with 3–4× higher variance, creating the bimodal return structure that justifies distributional RL; (c) per-lane control measurably changes lane speed distributions; (d) the problem is non-trivially solvable.

**Phase 4 — Training run validation (experiment_20260320_201005).** SAC completed 1M steps and TQC reached ~860k steps across 5 seeds each. Both algorithms showed continuous monotonic improvement without training collapse. TQC demonstrated statistically significantly better policies than SAC (Welch's t-test p < 0.001, Cohen's d = 0.79), with 2.3× lower evaluation variance, 12.6× better cross-seed reproducibility, and zero catastrophic failures (vs. 2% for SAC). The distributional advantage was concentrated in tail risk: TQC's worst-case evaluation episode was 26 points better than SAC's (9.3% of mean reward).

---

## References

[R3] Vinitsky, E., Parvate, K., Kreidieh, A., Wu, C., Bayen, A. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE 21st International Conference on Intelligent Transportation Systems (ITSC)*, 759–765.

[R4] Hua, C., Fan, W. (2023). Dynamic Speed Harmonization for Mixed Traffic Flow on the Freeway Using Deep Reinforcement Learning. *IET Intelligent Transport Systems, 17*(8), 2519–2530. https://doi.org/10.1049/itr2.12429

[R10] Zhang, Y., Quinones-Grueiro, M., Zhang, Z., Wang, Y., Barbour, W., Biswas, G., Work, D. (2024). MARVEL: Bringing Multi-Agent Reinforcement-Learning Based Variable Speed Limit Controllers Closer to Deployment. *IEEE Access, 12*, 161995–162012.

[R12] Sutton, R.S., Barto, A.G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press.

[R21] Hegyi, A., Hoogendoorn, S.P., Schreuder, M., Stoelhorst, H., Viti, F. (2008). SPECIALIST: A Dynamic Speed Limit Control Algorithm Based on Shock Wave Theory. *IEEE ITSC 2008*.

[R24] Ko, B., Ryu, S., Park, B.B., Son, S.H. (2020). Speed Harmonisation and Merge Control Using Connected Automated Vehicles on a Highway Lane Closure: A Reinforcement Learning Approach. *IET Intelligent Transport Systems, 14*(8), 947–957.

[R25] Li, Z., Liu, P., Xu, C., Duan, H., Wang, W. (2017). Reinforcement Learning-Based Variable Speed Limit Control Strategy to Reduce Traffic Congestion at Freeway Recurrent Bottlenecks. *IEEE Transactions on Intelligent Transportation Systems, 18*(11), 3204–3217.

[R26] Han, Y., Hegyi, A., Zhang, L., He, Z., Chung, E., Liu, P. (2022). A New Reinforcement Learning-Based Variable Speed Limit Control Approach to Improve Traffic Efficiency Against Freeway Jam Waves. *Transportation Research Part C, 144*, 103903.

[R27] Kuznetsov, A., Shvechikov, P., Grishin, A., Vetrov, D. (2020). Controlling Overestimation Bias with Truncated Mixture of Continuous Distributional Quantile Critics. *Proceedings of the 37th International Conference on Machine Learning (ICML)*.

[R28] Haarnoja, T., Zhou, A., Abbeel, P., Levine, S. (2018). Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor. *Proceedings of the 35th International Conference on Machine Learning (ICML)*.

[R29] Wu, Y., Tan, H., Ran, B. (2020). Differential Variable Speed Limits Control for Freeway Recurrent Bottlenecks via Deep Actor-Critic Algorithm. *Transportation Research Part C, 117*, 102649.

[R27-overview] Kušić, K., Ivanjko, E., Gregurić, M., Miletić, M. (2020). An Overview of Reinforcement Learning Methods for Variable Speed Limit Control. *Applied Sciences, 10*(14), 4917.
