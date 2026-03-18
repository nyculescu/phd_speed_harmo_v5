# Algorithm Selection: TQC (Primary) and SAC (Baseline)

## 1. Why the algorithm changed

The v4/early-v5 approach used **QR-DQN** (Dabney et al., 2017) [R2] — a distributional RL algorithm restricted to `gym.spaces.Discrete` action spaces. After 3 years of experimentation on the 4→3 lane-drop topology with a 7-level discrete action set, no configuration produced results that meaningfully outperformed the no-control baseline.

Two independent problems contributed to this failure:

1. **The environment** (4→3 lane-drop) had a microscopic bottleneck mechanism (gap acceptance at the lane drop) that was poorly observable from macroscopic E1 detector readings. This has been addressed by switching to the ramps_v1 topology (see `docs/vsl_placement_reason.md`).

2. **The action space** was discrete and single-dimensional (one uniform speed for all segments). The ramps_v1 topology requires two independent control inputs — mainline VSL and ramp transition VSL — which maps naturally to a 2D continuous action space. DQN-family algorithms cannot handle `Box` action spaces without discretisation, which causes combinatorial explosion (7 mainline levels × 7 ramp levels = 49 actions, each needing independent Q-value estimation).

The switch to **continuous-action algorithms** (SAC, TQC) resolves both issues simultaneously.

---

## 2. Why SAC as the baseline

### 2.1 Algorithm summary

Soft Actor-Critic (Haarnoja et al., 2018) is an off-policy actor-critic algorithm that maximises a **maximum entropy objective**:

```
J(π) = Σ_t E[ r_t + α · H(π(·|s_t)) ]
```

where `H(π)` is the entropy of the policy and `α` is the temperature parameter (auto-tuned in SB3). The entropy bonus encourages exploration by preventing the policy from collapsing to a deterministic action prematurely.

### 2.2 Why SAC fits this problem

**Continuous action space.** SAC natively outputs actions from a continuous distribution (squashed Gaussian). The policy network's output layer parameterises `μ(s)` and `σ(s)`; actions are sampled as `a = tanh(μ + σ · ε)`, where `ε ~ N(0,1)`. This maps directly to the `Box([60,40], [130,90])` action space — no discretisation needed.

**Off-policy with replay buffer.** Each SUMO episode is expensive (~10–30 s wall-clock for 3600 s simulation). Off-policy learning reuses past transitions from the replay buffer, achieving higher sample efficiency than on-policy methods (PPO, A2C) that discard data after each update. For traffic control environments where data collection is the bottleneck, sample efficiency is critical. Haarnoja et al. (2018) demonstrate 5–10× sample efficiency improvement over on-policy baselines on continuous control benchmarks.

**Entropy regularisation prevents policy collapse.** In traffic environments, the reward landscape can have flat plateaus (e.g., any speed between 90–110 kph yields similar outcomes during free-flow). Without entropy regularisation, the policy can collapse to an arbitrary point on this plateau and lose the ability to explore when conditions change. SAC's entropy term maintains stochastic exploration throughout training — a property that Hua & Fan (2023) identified as important for DSH: *"DDPG [...] may not learn anything at the beginning, but it still can reach the optimal value in the end"* (p. 2525). SAC avoids this slow-start problem entirely.

**Stability.** SAC uses two independent critic networks (double Q-learning) to mitigate overestimation bias, plus soft target updates (`τ = 0.005`). The SB3 implementation is production-grade and widely validated. Compared to DDPG (used by Hua & Fan 2023, 2024), SAC is strictly more stable: it inherits DDPG's actor-critic structure but adds entropy regularisation, double critics, and automatic temperature tuning — all of which address known DDPG failure modes (brittleness to hyperparameters, deterministic policy collapse, overestimation).

### 2.3 Why not DDPG or TD3

**DDPG** (Lillicrap et al., 2016) was used by Hua & Fan (2023, 2024) for dynamic speed harmonisation. However, they note: *"compared with DQN, the DDPG algorithm based on actor-critic architecture is more difficult to converge. It may not learn anything at the beginning"* (p. 2525). SAC resolves this with entropy-driven exploration.

**TD3** (Fujimoto et al., 2018) improves on DDPG with clipped double Q-learning and delayed policy updates, but lacks entropy regularisation. It is a deterministic policy algorithm — it explores only through additive Gaussian noise, which is state-independent and cannot adapt its exploration intensity to the traffic regime.

SAC supersedes both DDPG and TD3 for this application. It serves as the **non-distributional baseline** against which TQC's distributional critics are evaluated.

---

## 3. Why TQC as the primary algorithm

### 3.1 Algorithm summary

Truncated Quantile Critics (Kuznetsov et al., 2020, JMLR) extends SAC with **distributional critic networks**. Instead of learning `Q(s,a) = E[G]` (the mean return), each critic learns `Z(s,a)` — the full quantile function of the return distribution. The key innovation is truncation: when computing the Bellman target, the top quantiles from each critic are dropped, providing a principled mechanism to control overestimation bias without the conservatism of simply taking the minimum of two critics (as SAC does).

```
SAC critic output:  Q(s,a) ∈ ℝ           (scalar — mean return)
TQC critic output:  Z(s,a) ∈ ℝ^N         (N quantile values — full distribution)
```

With `n_critics = 2` and `n_quantiles = 25`, TQC maintains `2 × 25 = 50` quantile estimates per state-action pair, then drops the top `k` quantiles before averaging to form the Bellman target.

### 3.2 Why distributional critics matter for traffic control

The central thesis contribution is that **distributional RL captures the stochastic structure of traffic outcomes at a highway merge bottleneck**.

At demand levels near capacity (5500–6500 vph in the ramps_v1 baseline), the same agent action can produce qualitatively different outcomes depending on the microscopic vehicle configuration:

- **Favourable outcome:** Ramp vehicles find acceptable gaps, merge smoothly, weaving zone flow is maintained → high return.
- **Unfavourable outcome:** Gap distribution is unfavourable (short headways in through-lanes exactly when ramp vehicles arrive), merge conflicts occur, queue forms → low return.

This means the return distribution `P(G | s, a)` is **multimodal** in the transitional regime. A mean-based critic (SAC) learns `E[G]`, which may correspond to neither outcome. TQC's quantile critics learn the full shape of `P(G | s, a)` and can distinguish actions that have the same mean but different tail risks.

### 3.3 CVaR risk-averse evaluation

At evaluation time (not during training), the action selection policy can be switched from mean-optimal to risk-averse using Conditional Value-at-Risk (CVaR):

```python
# Standard (mean-optimal):
a* = argmax_a  mean(Z(s, a))

# Risk-averse (CVaR at α = 0.1):
a* = argmax_a  mean(Z(s, a)[:floor(α × N)])   # bottom 10% of quantiles
```

With `N = 25` quantiles and `α = 0.1`, the CVaR policy selects actions that maximise the average of the **worst 2–3 quantiles** — i.e., the actions whose worst-case outcomes are least bad. This is directly relevant to speed harmonisation: the operator cares more about avoiding breakdown (a catastrophic low-return event) than about marginally optimising throughput in the average case.

This CVaR evaluation capability is the specific academic contribution of using TQC over SAC. It is not available from SAC's scalar critics — you cannot compute CVaR from a single expected value.

Dabney et al. (2017) [R2] and Bellemare et al. (2017) [R1] established the theoretical foundations of distributional RL; Kuznetsov et al. (2020) extended it to continuous-action actor-critic architectures via TQC.

### 3.4 TQC inherits all SAC advantages

TQC is architecturally identical to SAC in the actor (policy) network — the same squashed Gaussian, the same entropy regularisation, the same automatic temperature tuning. The only difference is in the critic networks, which output `N` quantile values instead of a scalar. This means:

- Same `Box` action space compatibility
- Same off-policy replay buffer
- Same entropy-driven exploration
- Same hyperparameter structure (learning rate, batch size, τ, γ)
- Slightly higher compute per update (2 critics × 25 quantiles vs. 2 critics × 1 scalar)

The computational overhead is negligible for a 2D action space with a 38-dim observation — the SUMO simulation dominates wall-clock time by orders of magnitude.

---

## 4. What TQC must demonstrate to justify its use

The thesis claim is: *TQC's distributional critics provide measurable benefit over SAC for speed harmonisation at a highway merge bottleneck.*

This will be evaluated through:

1. **Mean return comparison:** TQC vs. SAC over 100+ evaluation episodes at each demand level (5000–7000 vph). If TQC's mean return is statistically significantly higher, the distributional critics provide an optimisation benefit.

2. **Tail risk comparison:** Compare the 10th-percentile return (worst 10% of episodes) between TQC and SAC. If TQC's worst-case performance is substantially better, the distributional representation enables risk-aware control.

3. **CVaR ablation:** Compare TQC with mean evaluation vs. TQC with CVaR(α=0.1) evaluation. If CVaR reduces the frequency of breakdown events (episodes where weaving zone speed drops below 60 kph), the risk-averse inference is practically useful.

4. **Distributional diagnostics:** Visualise the learned quantile distributions `Z(s,a)` for representative states in the free-flow, metastable, and congested regimes. If the distributions are visually multimodal or heavy-tailed in the metastable regime, this confirms the hypothesis that the return structure at a merge bottleneck is genuinely stochastic and not well-captured by a scalar mean.

If TQC does not outperform SAC on criteria 1–3, that is a publishable negative result: *"distributional critics provide marginal improvement in this regime, suggesting that the merge dynamics are sufficiently deterministic for mean-based optimisation at the aggregate observation level."*

---

## 5. SB3 / SB3-Contrib implementation

| Parameter | SAC (baseline) | TQC (primary) |
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

All hyperparameters are identical between SAC and TQC except for the distributional critic parameters (`n_quantiles`, `top_quantiles_to_drop_per_net`). This ensures a fair comparison: any performance difference is attributable to the distributional representation, not to hyperparameter differences.

---

## 6. Why not other algorithms

| Algorithm | Reason for exclusion |
|---|---|
| **QR-DQN** [R2] | Discrete actions only; failed in v4 after 3 years |
| **C51** [R1] | Discrete actions only; fixed support `[V_min, V_max]` requires calibration |
| **DQN** | Discrete actions only; no distributional component |
| **PPO** | On-policy — discards data after each update; poor sample efficiency for expensive SUMO episodes |
| **DDPG** | Superseded by SAC; deterministic policy; known instability (Hua & Fan 2023, p. 2525) |
| **TD3** | No entropy regularisation; deterministic exploration; superseded by SAC |
| **DSAC** | Not in SB3; requires custom implementation; continuous distributional but immature |
| **IQN** | Not in SB3; discrete actions in original formulation; future extension (v5.1) |

---

## 7. References

- **[R1]** Bellemare, M.G., Dabney, W., Munos, R. (2017). A Distributional Perspective on Reinforcement Learning. *ICML 2017*.
- **[R2]** Dabney, W., Rowland, M., Bellemare, M.G., Munos, R. (2018). Distributional Reinforcement Learning with Quantile Regression. *AAAI 2018*.
- **[R3]** Vinitsky, E. et al. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*, 759–765.
- **[R10]** Zhang, Y. et al. (2024). MARVEL: Bringing Multi-Agent Reinforcement-Learning Based Variable Speed Limit Controllers Closer to Deployment. *IEEE Access, 12*, 161995–162012.
- Haarnoja, T. et al. (2018). Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor. *ICML 2018*.
- Kuznetsov, A., Shvechikov, P., Grishin, A., Vetrov, D. (2020). Controlling Overestimation Bias with Truncated Mixture of Continuous Distributional Quantile Critics. *JMLR, 21*(167), 1–56.
- Lillicrap, T.P. et al. (2016). Continuous Control with Deep Reinforcement Learning. *ICLR 2016*.
- Fujimoto, S., van Hoof, H., Meger, D. (2018). Addressing Function Approximation Error in Actor-Critic Methods. *ICML 2018*.
- Hua, C., Fan, W.D. (2023). Dynamic Speed Harmonization for Mixed Traffic Flow on the Freeway Using Deep Reinforcement Learning. *IET-ITS, 17*, 2519–2530.
