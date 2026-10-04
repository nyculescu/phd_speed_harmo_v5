# DRL algorithm families for heterogeneous freeway control in SUMO: evidence notes

*Desk notes, 2026-10-04. Written by a Claude research agent for the restart design space. About 28 searches and fetches. This is not a systematic review.*

## Tags

| Tag | Meaning |
|---|---|
| **[TEXT §…]** | PDF text extracted and the named sections/tables read. Anything else in that paper is **[VERIFY]**. |
| **[ABSTRACT]** | Only the arXiv/venue abstract was read. **[VERIFY]** before citing. |
| **[SNIPPET]** | Search-engine snippet or a fetched summary only. **[VERIFY]**. |
| **[GK-VERIFY]** | From the model's general knowledge. Not fetched in this session. Check title, authors, venue and claim before citing. |

## Scope caveats (read first)

- **v6 exclusions.** `phd_speed_harmo_v6/CLAUDE.md` and `docs/handoff/lessons_learned.md` §1 exclude:
  - VSL / speed harmonisation;
  - building a new DRL car-following model.

  For that reason **no VSL papers were searched or cited here**.
- **CAV papers are cited for method only.** The Flow/CIRCLES CAV wave-damping papers below appear only as evidence about methods: PPO/TD3, domain randomisation, shields. Per-vehicle CAV acceleration/ACC policies would probably fall under the "new DRL car-following model" exclusion. Broadcast CAV speed set-points are probably "speed harmonisation". **Of the three action spaces in the brief, only ramp metering clearly survives the v6 rules.** The v6 ramp gate was itself killed by the cheap killer: SUMO's merge gave no usable capacity drop (`docs/feasibility/gate0_ramp.md`).
- **Family choice is second-order to headroom.** v6 rule: no DRL before an oracle beats the best tuned non-learning controller by ≥ 10 % with a CI excluding 0. No algorithm family creates headroom. The families below differ in how much of an *existing* gap they capture and how robustly they do so.

## 0. Bottom line

1. **The best-supported traffic RL successes rely on plain workhorses, not on exotic families.**
   - CIRCLES field test: single-agent PPO with a short history, a safety wrapper and trajectory-replay training.
   - Decentralised bottleneck work: TD3 with parameter sharing and penetration-rate randomisation.
   - RESCO: independent DQN had the best final-10-episode performance in 5 of 6 tasks. The DQN-based methods were far more sample-efficient than IPPO/FMA2C.
2. **No traffic paper found that shows distributional RL helping in freeway, ramp or CAV control.**
   - The only traffic hit is an IQN + vanilla **ensemble** for signal control (robustness to missing data and transfer) [ABSTRACT].
   - In general RL, distributional gains come from interaction with non-linear function approximation and can hurt in simpler settings [ABSTRACT].
   - It does not address partial observability, the dominant property here.
3. **The v5 evidence points at memory plus a validated actuator.** RecurrentPPO over 4 ramp-meter settings won. Frame-stack and plain PPO failed. The general literature agrees that recurrent model-free RL is a strong POMDP baseline (Ni et al. 2022 [ABSTRACT]).
4. **The v5 generalisation failure is a known pattern.**
   - Vinitsky et al. (TD3, SUMO bottleneck) found that a controller trained at one CAV penetration under-performs at another.
   - Randomising penetration per rollout gave a "universal" controller at "some small loss of performance" [TEXT].
5. **Two warning signs from the most-cited mixed-autonomy work:**
   - their decentralised RL only **equalled** an ALINEA traffic-light controller at 40 % penetration (it beat a hand-designed AV feedback controller) [TEXT];
   - the 2018 benchmark compared RL only against uncontrolled or default-actuated baselines, and PPO/TRPO were *worse* than default actuated signals on the grid [TEXT].
6. **Recommended restart families** (§6), in order:
   1. Context-conditioned recurrent PPO: RecurrentPPO + structured domain randomisation + a privileged/asymmetric critic or an RMA-style context encoder.
   2. Hybrid RL over tuned control: MaskablePPO over a menu of tuned controller settings, or residual PPO on ALINEA. RL-in-MPC (Airaldi et al.) is a stretch option.
   3. Non-RL policy search: BO/CMA-ES tuning of the baselines, plus ARS with a linear policy on the same features as the RL policy. It is both the comparator and the falsification test.

   **Deprioritise:** distributional, model-based (Dreamer/MBPO/MuZero), offline, transformers, and MARL (unless there are many actuators).

## 1. Problem properties used as scoring axes

| # | Property | Note |
|---|---|---|
| **P1** | Partial observability with **hidden per-episode context** | Driver/vehicle parameter mix, truck share, compliance, incidents, demand surges. This is a contextual / Bayes-adaptive MDP. The history carries information about the context. |
| **P2** | **Delayed effects** of 30–60 s at decision steps of 30–60 s | The effect lands 1–2 steps later, but congestion consequences last tens of minutes. |
| **P3** | **Expensive samples** | Inference from the lessons file (1 M decisions ≈ 82 PPO updates, so about 12 k decisions per update): ≥ 500 PPO updates means about 6 M decisions at that rollout size. "PPO-update-equivalents" are therefore not a sample measure. Pre-register the budget in env-steps **and** wall-clock. |
| **P4** | **Action type** | A small discrete menu worked in v5. Per-lane continuous speeds failed. A low-dimensional continuous rate or set-point is untested. |
| **P5** | **Robustness/generalisation** across vehicle/driver diversity and out-of-mix perturbations | — |
| **P6** | **Side constraints** | On-ramp queue/spillback, no harm to other users, no safety degradation. |
| **P7** | **Fit with the evaluation discipline** | Pre-registration, tuned baselines, paired seeds, 3–5 training seeds, validation-only checkpointing. Fewer hyper-parameters and native SB3 support help here. |

P2 horizon (inference): at γ = 0.98 the effective horizon 1/(1−γ) is 50 steps, i.e. 25 min at 30 s steps and 50 min at 60 s steps. γ ≈ 0.95–0.99 is the plausible range. Higher γ raises the variance of the advantage estimates for on-policy methods.

## 2. Family-by-family profiles

### Summary table

| Family | Concrete algorithms | In SB3 / sb3-contrib? | P1 hidden context | P3 sample cost | P4 action fit | Traffic evidence (this search) | Verdict |
|---|---|---|---|---|---|---|---|
| On-policy actor-critic | PPO, A2C, TRPO | yes (PPO, A2C; TRPO contrib) | none without memory | poor; parallel envs help | discrete & low-dim continuous | CIRCLES PPO (field), Flow benchmarks, MAPPO; RESCO IPPO unstable | baseline only |
| Recurrent | RecurrentPPO (LSTM), GRU, GTrXL | RecurrentPPO only | **good** | poor (on-policy) | both | the v5 win; Ni 2022 (general) | **keep, extend** |
| Off-policy continuous | SAC, TD3, CrossQ, DDPG | yes (CrossQ contrib) | none without memory; no recurrent SAC in SB3 | **better** (replay) | low-dim continuous | Vinitsky 2020 TD3 (SUMO bottleneck); DDPG baseline in Airaldi | secondary |
| Distributional | QR-DQN, IQN, C51, TQC | QR-DQN, TQC only | does not address it | like the base algorithm | QR-DQN discrete, TQC continuous | only a signal-control ensemble [ABSTRACT] | **deprioritise** |
| Value-based discrete | DQN, Double/Dueling, Rainbow, DRQN | DQN (QR-DQN); no Rainbow/DRQN | none without memory | **better** | small menus | RESCO: IDQN best final performance (5/6); DQN-based methods far more sample-efficient than IPPO/FMA2C | possible, if memory is added |
| Multi-agent | IPPO, MAPPO, QMIX, shared-parameter TD3 | no (needs RLlib/EPyMARL/BenchMARL) [GK-VERIFY] | local observation only | worse | many actuators | Vinitsky 2020; RESCO (decentralised more robust) | only with ≥ 3 actuators |
| Model-based | Dreamer(V3), MBPO, MuZero; physics-model MPC | no | world model must infer context | best in principle | both | DreamerV3-TSC: no clear data-efficiency gain [ABSTRACT] | deprioritise (except physics-model hybrids) |
| Offline | CQL, IQL, BCQ, Decision Transformer | no (d3rlpy [GK-VERIFY]) | as base | n/a (data) | both | DataLight [ABSTRACT]; physics-informed ramp RL [SNIPPET] | not useful with simulator access |
| Hierarchical / options | option-critic, HIRO, RL-over-controllers | DIY via env wrapper | via high-level memory | good (short high-level horizon) | discrete modes | thin; the v5 win is de facto 2-level | **keep, in hybrid form** |
| Meta-RL / context | DR, RMA, VariBAD, PEARL, MAML (MetaLight) | DR is free; RMA/asymmetric critic need a custom policy | **designed for it** | DR costs more samples | both | Vinitsky 2020 (penetration DR); CIRCLES (data replay); MetaLight/BM-DQN (signals) | **keep (with recurrent)** |
| Safe / constrained | shields, action masking, PPO-Lagrangian, CPO, CBF filters | MaskablePPO (masks) | — | — | discrete masks are easy | CIRCLES failsafe wrapper; Airaldi constraints in MPC; CBF shields for CAVs [SNIPPET] | **add as a layer** |
| Hybrid RL + control | residual RL, RL-tuned ALINEA/MPC, MPC-as-Q-function (Airaldi) | residual is an env wrapper; MPC-RL needs CasADi | partial (via learned params) | **best** | both | Airaldi RL-in-MPC (METANET) [TEXT] | **keep** |
| Non-RL policy search | BO, CMA-ES, ES, ARS | ARS (contrib); BO via Optuna [GK-VERIFY] | none (static policy) unless the features carry history | good per wall-clock, embarrassingly parallel | low-dim params | Vinitsky 2018: ES best on 3/4 benchmarks; BO-tuned PI-ALINEA in Airaldi | **mandatory comparator** |

### 2.1 On-policy actor-critic (PPO / A2C / TRPO)

**Suitable**
- Stable and simple.
- Native "≥ 500 updates" accounting.
- Scales with 32 parallel SUMO workers (SubprocVecEnv).
- Handles discrete and low-dimensional continuous actions.

**Unsuitable**
- Memoryless MLPs cannot infer the hidden context (P1).
- Sample-hungry (P3).
- High γ gives noisy advantages (P2).

**Evidence**
- **CIRCLES, 100-AV I-24 field test** (Jang, Lichtlé et al., arXiv 2402.17050) [TEXT §2.2, §3.1–3.2, Table 1, I-210 sidebar]:
  - "single-agent Proximal Policy Optimization (PPO) with an augmented value function";
  - observations: ego speed, leader speed, gap, gap thresholds, **0.5 s of ego-speed history**, and speed-planner targets at 0/200/500/1000 m downstream;
  - no inter-AV communication.
- **Flow benchmarks** (Vinitsky et al., CoRL 2018) [TEXT §4–5, Table 1, App. A.4/B]. "gradient-based algorithms (TRPO and PPO) are more effective in merge scenarios, while gradient-free algorithms (ES) are better in figure eight, grid, and bottleneck benchmarks."
  - Grid delay (lower is better): actuated 280.8 s vs PPO 296.8 s and TRPO 296.2 s, so **PPO/TRPO were worse than SUMO default actuated**; ARS 270.2, ES 271.7.
  - Bottleneck 0 outflow (veh/h): PPO 1167 ± 264, ES 1360 ± 200, uncontrolled 1023 ± 263. 3 seeds, 500 iterations × 50 rollouts. "many of our experiments take over 10 hours to perform 500 iterations".
- **MAPPO** (Yu et al., NeurIPS 2022 D&B) [ABSTRACT]: PPO "often achieves competitive or superior results in both final returns and sample efficiency" vs off-policy MARL in four non-traffic testbeds.
- **RESCO** (Ault & Sharon, NeurIPS 2021 D&B) [TEXT §4.2–4.3, Table 1]:
  - IPPO "demonstrates significant instability";
  - IPPO and FMA2C need about 1,400 episodes vs about 100 for IDQN/MPLight.
- **v5 (project):** PPO lost about 10 % to a tuned constant limit in the stop-and-go band.

**Verdict:** keep only as the memoryless ablation of the recommended recurrent agent.

### 2.2 Recurrent policies (RecurrentPPO / LSTM / GRU / transformers)

**Suitable**
- Directly targets P1. The memory can perform implicit context inference (system identification in the loop).
- This is lessons-file hypothesis 3 ("partial observability where the history carries information").

**Evidence**
- **Ni, Eysenbach, Salakhutdinov (ICML 2022)** [ABSTRACT]. Meta-RL, robust RL and generalisation "can be cast as POMDPs". A carefully tuned recurrent model-free agent "performs on par with (and occasionally substantially better than)" specialised methods, and beats them on 18/21 environments.
- **Peng et al., ICRA 2018** (dynamics randomisation) [ABSTRACT]. Policies trained under randomised dynamics adapt and transfer sim-to-real. That their policy was an LSTM is [GK-VERIFY].
- **v5:** RecurrentPPO won by 2.5–4.3 % vs a tuned scheduler/MPC. Frame-stack PPO failed. This suggests the useful information sits in longer histories than a short frame stack, or that recurrence helped optimisation. Not tested.

**Unsuitable / risks**
- The memory learns the *training* context distribution. Out-of-mix failure in v5 is the expected behaviour without broader randomisation.
- Recurrent on-policy training is slower: truncated BPTT, smaller effective batches.
- sb3-contrib has RecurrentPPO only: no recurrent SAC/DQN, and no MaskableRecurrentPPO [GK-VERIFY].
- **Transformers** (GTrXL, Parisotto et al. 2020 [GK-VERIFY]): no traffic evidence found (not searched in depth). Not in SB3. With ≤ a few hundred decisions per episode, an LSTM/GRU should suffice (inference).

**Verdict:** core of recommendation R1.

### 2.3 Off-policy continuous (SAC / TD3 / CrossQ / DDPG)

**Suitable**
- Replay gives better sample efficiency (P3).
- Natural for one or a few continuous set-points (meter rate, target occupancy).

**Evidence**
- **Vinitsky, Lichtlé, Parvate, Bayen** (arXiv 2011.00120; ACM TCPS per the CIRCLES reference list, year [VERIFY]) [TEXT abstract, §III-B, §III-E, §IV-A/B]:
  - TD3 with a **shared policy** across AVs, in the SUMO Bay-Bridge-like bottleneck;
  - outflow at 3500 veh/h inflow: radar + aggregate observation 1817 ± 80 (5 % CAV) to 2034 ± 45 (40 %);
  - it beat a hand-designed AV feedback controller "despite extensive tuning". **But** "its performance at a 40% penetration equals the performance of a traffic light based controller" (ALINEA);
  - the authors note that TD3 as an independent learner suffers from stale replay when the other agents' policies change.
- **Airaldi et al. (2025)** [TEXT §V]. A DDPG baseline (293,380 parameters) learned the TTS reduction about as fast as the 53-parameter MPC-RL. Its "variability and violations are decreasing at a substantially lower rate."
- **v5:** TQC/SAC with per-lane continuous speeds failed. The project attributes this to the reward and the lack of headroom, not to the family.

**Unsuitable**
- No memory in SB3. A recurrent SAC/TD3 needs custom code (e.g. Ni et al.'s implementation [GK-VERIFY]).
- Replay of transitions from different hidden contexts without context features biases the critic (inference).
- High-dimensional continuous actions (per lane, per segment) widen the exploration problem.

**Verdict:** secondary. Use only with a low-dimensional action and context features; CrossQ is a cheap SB3-native trial [GK-VERIFY for CrossQ's claims].

### 2.4 Distributional (C51 / QR-DQN / IQN / TQC). See also §3.

**Verdict:** does not address P1/P2. No freeway/CAV traffic evidence found. Poor fit for the restart.

### 2.5 Value-based discrete (DQN / Double / Dueling / Rainbow / DRQN)

**Suitable**
- An exact fit for a small menu of validated settings (P4).
- Replay improves sample efficiency (P3).

**Evidence**
- **RESCO** [TEXT §4.2–4.3]. "When examining the performance of each algorithm in the final 10 episodes of training, IDQN outperforms all other algorithms in all tasks except the 'Cologne Regional'." RESCO also concludes that "decentralized control algorithms are more robust" and that RL "should give increased attention to hyper-parameter sensitivity".
  - Caveat: RESCO Table 1 reports the **best training episode**, not the final policy. The project's validation-only checkpointing rule forbids that.
- **MetaLight** builds on DQN (FRAP++) [SNIPPET].

**Unsuitable**
- No memory in SB3 (DRQN would be custom).
- Frame stacks are the SB3-native substitute, and frame-stack PPO already failed in v5.
- Rainbow is not in SB3. Its distributional component is one of its parts.

**Verdict:** a reasonable discrete off-policy alternative to RecurrentPPO only if memory is added. Not a first pick.

### 2.6 Multi-agent (IPPO / MAPPO / QMIX / shared-parameter independent learners)

**Suitable**
- Many actuators (several ramps, or a CAV fleet at 10–100 % penetration).
- Decentralised execution with local sensing.

**Evidence**
- Vinitsky 2020 [TEXT] (above).
- MAPPO [ABSTRACT].
- RESCO: coordinated methods (FMA2C, MPLight) are fragile on realistic layouts; MPLight diverged with heterogeneous intersections ("shared control parameters between significantly different control tasks") [TEXT].
- Vinitsky 2018 lists "decentralization" as open and centralised control as unrealistic [TEXT §5].

**Unsuitable here**
- With one to three ramps, a centralised single policy is simpler.
- CAV per-vehicle MARL collides with the v6 exclusions.
- Not in SB3; RLlib/EPyMARL bring more hyper-parameters (P7). QMIX [GK-VERIFY] needs discrete cooperative settings with a joint reward.

**Verdict:** only if a coordinated multi-ramp corridor is chosen. Then use shared-parameter IPPO/MAPPO.

### 2.7 Model-based (Dreamer / MBPO / MuZero-style; physics-model MPC)

**Suitable**
- In principle the best sample efficiency (P3).
- Freeway traffic has good macroscopic models (METANET, CTM), which favours *physics* models over learned world models.

**Evidence**
- **DreamerV3 for traffic signal control** (Li, Lin, Luo, Yu, arXiv 2503.02279) [ABSTRACT]. "it can only be confirmed that larger model sizes exhibit modest data-efficiency, and no evidence was found that increasing the training ratio accelerates convergence."
- **ModelLight** (model-based meta-RL for signal control) [SNIPPET].
- MBPO (Janner et al. 2019) and MuZero (Schrittwieser et al. 2020) [GK-VERIFY]: no freeway evidence found.

**Unsuitable**
- Learned world models must themselves infer the hidden context. Model bias is worst exactly where DRL is supposed to win (model mismatch).
- Separate JAX/PyTorch codebases with heavy tuning (P7).
- MuZero-style tree search over 30–60 s steps is overkill for a 4-option menu.

**Verdict:** deprioritise learned world models. The useful model-based idea is a physics model inside a hybrid (§2.12).

### 2.8 Offline RL (CQL / IQL / BCQ / Decision Transformer)

**Suitable**
- Only when real logged data exist and online interaction is unsafe.

**Evidence**
- **DataLight** (Zhang, Zhang, Deng, Li; arXiv 2303.10828, venue listed as ECML PKDD 2026 [VERIFY]) [ABSTRACT]: offline signal control beats online and offline baselines.
- **Physics-informed RL ramp metering** (Han et al., TR-C 137, 2022; authors [VERIFY]) [SNIPPET]: trains on historic + model-generated data, iteratively adding new field batches. Claims to outperform feedback ramp metering and a simulator-only RL.

**Unsuitable here**
- There is no field data, and SUMO is available, so offline RL only adds extrapolation error (inference).
- One marginal use: warm-start from logs of the tuned baselines (IQL/CQL, Kostrikov 2022 / Kumar 2020 [GK-VERIFY]) and then fine-tune online. This is unlikely to be worth the code.

**Verdict:** deprioritise.

### 2.9 Hierarchical / options

**Suitable**
- A high-level policy choosing among validated low-level controllers shortens the effective horizon (P2) and inherits the low level's safety (P6).
- **The v5 RecurrentPPO win already has this shape**: RL picks among 4 settings of a validated meter every 30 s.

**Evidence (thin)**
- Vinitsky 2018: "many of the systems are clearly composed of distinct sub-units, suggesting that hierarchical approaches could be viable" [TEXT §5].
- CMU "Learning highway ramp merging via RL with temporally-extended actions" [SNIPPET].
- High-level RL over a low-level controller for safety [SNIPPET, source unclear].
- Options framework (Sutton, Precup, Singh 1999) [GK-VERIFY].

**Verdict:** adopt in the practical form "RL over a menu of tuned controllers / parameter sets" (merged into R2). Do not build option-critic/HIRO machinery.

### 2.10 Meta-RL and context-conditioned policies (DR, RMA, VariBAD/PEARL, MAML)

**Suitable**
- Designed for P1/P5.
- DR spreads training over the hidden-condition distribution.
- Context encoders (RMA) or belief inference (VariBAD [GK-VERIFY]) make the policy condition on the inferred condition.

**Evidence**
- **RMA** (Kumar, Fu, Pathak, Malik, RSS 2021) [ABSTRACT]: a base policy plus an adaptation module, trained fully in simulation, deployed "without any fine-tuning". The two-phase privileged-teacher → history-student scheme is [GK-VERIFY] detail.
- **Peng et al. 2018** [ABSTRACT]: dynamics randomisation gives robustness to "significant calibration error".
- **Vinitsky 2020** [TEXT §IV-B]: penetration-rate DR with p ~ U(0.05, 0.4) gives a single controller "that performs effectively across penetration rates albeit with some small loss of performance". This is the closest traffic analogue to the v5 generalisation failure.
- **CIRCLES** [TEXT §2.2, §3]:
  - heterogeneity came from **replaying real I-24 leader trajectories** (varying time of day, direction, congestion) and string-unstable IDM followers with "zero-mean Gaussian noise ... added to the acceleration";
  - a data-driven lane-change model tested robustness to cut-ins;
  - an I-210 SUMO controller trained at 10 % penetration "appears robust to changes in the penetration rate".
  - They moved off SUMO microsimulation to a fast single-lane simulator, citing calibration effort and run time.
- **Signal control:** MetaLight (Zang et al., AAAI 2020; MAML-style, DQN base) [SNIPPET]; BM-DQN Bayesian meta-RL (Zou & Qin, arXiv 2010.00163) [ABSTRACT]: faster and more robust adaptation "in heterogeneous scenarios".

**Unsuitable / risks**
- DR breadth trades off in-distribution performance. v5's edge was 2.5–4.3 %, and a "small loss" could erase it.
- MAML-style meta-RL needs per-task fine-tuning at deployment, which is a poor fit for a fixed evaluated policy.
- An asymmetric (privileged) critic and RMA need a custom SB3 policy (split observation dict).

**Verdict:** core of R1. Use DR plus history inference, not gradient-based meta-learning.

### 2.11 Safe / constrained RL and shielding

**Suitable**
- P6 constraints are explicit (queue ≤ limit, no harm to side traffic).
- Shields keep the evaluated policy inside the validated envelope.

**Evidence**
- **CIRCLES:** the RL acceleration is "wrapped by a gap-closing component and a failsafe component"; the failsafe brakes when the modified TTC < 6 s [TEXT].
- **Airaldi et al.:** constraints inside the MPC; the agent learned to avoid queue-constraint violations "within the first 5 episodes" [TEXT].
- **CBF safety shields** for CAV lane changing (arXiv 2505.01453) [SNIPPET].
- CPO / PPO-Lagrangian (Achiam et al. 2017 [GK-VERIFY]); shielding (Alshiekh et al. 2018 [GK-VERIFY]).

**Implementability**
- MaskablePPO (sb3-contrib) gives discrete action masking for free.
- Lagrangian methods need an extra library (e.g. OmniSafe [GK-VERIFY]).

**Verdict:** add a mask or shield layer to R1/R2. It is not a family to restart on.

### 2.12 Hybrid RL + control (residual RL, RL-tuned controllers, RL-in-MPC)

**Suitable**
- Starts at the tuned baseline, so it cannot be much worse at initialisation.
- Small parameter count, so it is sample-efficient (P3) and constraint-aware (P6).
- Matches the "adaptive control" thesis framing.

**Evidence**
- **Airaldi, De Schutter, Dabiri, "Reinforcement Learning With Model Predictive Control for Highway Ramp Metering"** (IEEE T-ITS 26(5):5988–6004, 2025; arXiv 2311.08820) [TEXT §V].
  - **Method:** second-order LSTD Q-learning tunes 53 MPC parameters. The parametrised MPC is the Q-function approximator.
  - **Setting:** METANET, not SUMO. Control every 60 s (Np = 24); 80 training episodes of 4 h with random two-peak demand; 15 evaluation seeds.
  - **Result:** TTS fell from about 1100 to about 700 veh·h (≈ 35 %) with zero constraint violations. It beat a DDPG agent, nominal MPC, and PI-ALINEA with queue management "fine-tuned ... via Bayesian Optimisation".
  - **Caveat for headroom:** the MPC was **deliberately mis-initialised** (30 % model error, untuned weights). The 35 % is relative to that poor start. All controllers shared the same wrong parameters.
- **Residual RL** (Johannink et al. 2019; Silver et al. 2018) [GK-VERIFY]: no freeway traffic example found in this search.

**Unsuitable / risks**
- If the tuned controller is near the reference (lessons §2: tuned rules or MPC within 0–5 % of the oracle), the residual learns about 0.
- Reviewers may attribute the gain to the controller structure rather than to DRL.
- MPC-RL needs CasADi/IPOPT and a model; the authors' `mpcrl` code is public [GK-VERIFY].

**Verdict:** core of R2. A residual or menu-selection wrapper is SB3-native; MPC-RL is a stretch.

### 2.13 Non-RL policy search (BO / CMA-ES / ES / ARS)

**Suitable**
- Low-dimensional controller parameters, black-box noisy objectives, embarrassingly parallel on 32 cores.
- No reward-shaping or credit-assignment issues (it optimises the episode metric directly).

**Evidence**
- **Vinitsky 2018** [TEXT]:
  - ES best on figure-eight/grid/bottleneck: "exploration-oriented algorithms (ARS or ES) are less prone to being trapped in local optima";
  - a linear ARS policy was competitive;
  - caveat: "ARS on the bottleneck simply learn to block a lane" (a fairness hack).
- **Mania, Guy, Recht 2018 (ARS)** [ABSTRACT]: matches state-of-the-art sample efficiency on MuJoCo with static linear policies, and is "at least 15 times more efficient" computationally. It reports "high variability in performance" across seeds.
- **Airaldi et al.:** PI-ALINEA gains tuned by BO [TEXT].

**Unsuitable**
- A static policy cannot adapt to hidden context unless the features summarise history (e.g. a filtered estimate).
- Not "deep", so it does not satisfy the thesis claim by itself.

**Verdict:** mandatory as (a) the tuner of every baseline and (b) a learned-policy ablation (ARS-linear on the RL policy's features). If ARS-linear ≈ RecurrentPPO, there is no DRL claim.

## 3. Distributional RL: when it helps, and the fit here

**When it helps (general RL)**
- **Atari:** C51 (Bellemare, Dabney, Munos, ICML 2017), QR-DQN (Dabney et al., AAAI 2018), Rainbow (Hessel et al., AAAI 2018) [GK-VERIFY]. IQN "improved performance on the 57 Atari 2600 games" and "gives rise to a large class of risk-sensitive policies" [ABSTRACT].
- **Continuous control:** TQC (Kuznetsov et al., ICML 2020 [GK-VERIFY]). It uses quantile critics mainly to **control overestimation bias** by truncating top quantiles. Its MuJoCo gains are as much about bias control as about distribution modelling (my reading [GK-VERIFY]).
- **Mechanism:** Lyle, Castro, Bellemare (AAAI 2019) [ABSTRACT]. "in many realizations of the tabular and linear approximation settings, distributional RL behaves exactly the same as expected RL. In cases where the two methods behave differently, distributional RL can in fact hurt performance". The gains are linked to non-linear function approximation (auxiliary-task-like representation effects).
- **Genuinely distributional uses:** risk-sensitive objectives (CVaR, quantile targets), multimodal or heavy-tailed returns, and exploration from return uncertainty.

**Traffic evidence (this search)**
- **Shi, Devailly, Larocque, Charlin** (arXiv 2306.01925) [ABSTRACT]: IQN-based DisRL in a GCN signal controller. "an ensemble of standard RL and DisRL yields superior performance" under missing sensor data and in zero-shot network transfer. This is an ensemble, so it does not isolate the distributional effect.
- A "distributionally robust MARL" signal-control paper (arXiv 2512.18558) [SNIPPET] is **robust optimisation over demand distributions**, not distributional RL. It uses PPO fine-tuned on worst-case demand. Do not conflate the two.
- **No freeway, ramp or CAV-wave paper found** that shows a distributional-RL gain. This is the absence of evidence within about 28 searches, not proof of absence.

**Poor fit here because**
1. **P1 is not addressed.** A distributional critic models the spread of return *given the observation*. With hidden context, that spread mixes the context uncertainty into apparent "aleatoric" noise. The policy still cannot act on the context; memory or context inference is what helps (inference).
2. **The objective is risk-neutral.** The objective is pre-registered as a median of paired differences of an episode aggregate (TTS/delay over many vehicles). Within-episode returns over many vehicles are likely close to unimodal (inference).
   - A plausible exception is **bistable breakdown vs no-breakdown** near capacity, where returns may be bimodal. Even then, a mean-maximising policy gains nothing from knowing the shape unless the objective is risk-sensitive.
3. **The v5 failures were reward and headroom**, not value-estimation quality.
4. **SB3 limits.** SB3 has QR-DQN and TQC but no IQN, C51, Rainbow or recurrent distributional agent. QR-DQN acts on the quantile mean [GK-VERIFY], so risk-sensitive action selection needs custom code.

**When to revisit:** only if a pre-registered **tail objective** becomes primary, e.g. P(breakdown), 90th-percentile delay, or a CVaR of queue spillback. Then IQN/QR-DQN with CVaR action selection on a small discrete menu is the natural design.

## 4. Heterogeneity and sim-to-real: what the literature does

1. **Domain/dynamics randomisation** (Peng 2018 [ABSTRACT]; Vinitsky 2020 penetration DR [TEXT]).
   - Cheap and SB3-native: randomise SUMO vType distributions per episode (length, maxSpeed, speedFactor/dev, accel/decel, tau, sigma, carFollowModel, lcStrategic/lcCooperative…), truck share, compliance and incident onset.
   - Expect a small in-distribution loss.
2. **Real-data replay instead of parametric randomisation** (CIRCLES [TEXT]). The leaders replay real I-24 trajectories, so heterogeneity comes from data, not from assumed parameter ranges. There are no I-24-like data here; SUMO randomisation is the substitute.
3. **History-based context inference.**
   - Recurrent policies: Ni 2022 [ABSTRACT]; the v5 RecurrentPPO.
   - RMA-style encoders: teacher with the privileged context vector, then a student that regresses it from history [ABSTRACT + GK-VERIFY].
   - **Diagnostic:** train an auxiliary head to predict the hidden context (truck share, compliance, incident flag). If it cannot, the history does not carry the information and DRL's main argument (lessons §2, hypotheses 1 and 3) fails for this cell.
4. **Asymmetric / privileged critic** (Pinto et al. 2018 [GK-VERIFY]). The critic sees the true context and the full state, and the actor sees only sensors. CIRCLES used "PPO with an augmented value function" [TEXT]; that it means privileged critic inputs is [VERIFY].
5. **Meta-RL with adaptation steps** (MetaLight [SNIPPET], BM-DQN [ABSTRACT]). Signal-control only; deployment-time gradient steps are a poor fit for a frozen evaluated policy.
6. **Evaluation pattern implied** (inference). Pre-register an **in-mix test** and **held-out context ranges** (OOD truck share, compliance, incident timing). Report both, because v5's win did not survive OOD.

## 5. Pairing with the evaluation discipline; implementability

| Family | Pre-registration & tuned baselines | ≥ 500 PPO-update-equivalents | 3–5 seeds on 32 cores | Validation-only checkpointing | SB3 effort |
|---|---|---|---|---|---|
| RecurrentPPO + DR (+ privileged critic) | easy | native | feasible if the episode is short. Budget: about 12 k decisions/update × 500 ≈ 6 M decisions/seed at the v5 rollout size (inference) | EvalCallback on validation seeds | low; privileged critic = custom policy (medium) |
| MaskablePPO over a tuned-controller menu / residual PPO | easy; the baseline is inside the action set | native | as above, often converges sooner (inference) | native | low (env wrapper + masks); no recurrent masking in contrib [GK-VERIFY] |
| SAC/TD3/CrossQ | define the budget in env-steps, not updates | n/a; match env-steps | cheaper per seed | needs a custom eval loop | low (memoryless) / high (recurrent) |
| DQN/QR-DQN | as above | n/a | cheaper | as above | low (memoryless) |
| MARL | many extra hyper-parameters | — | expensive | — | high (other library) |
| Dreamer/MBPO/MuZero | hard to tune fairly | — | expensive | — | high |
| Offline | needs a data protocol | — | — | — | high |
| BO/CMA-ES/ARS | easy; give the **same simulation budget** to baseline tuning as to DRL training (fairness; inference) | n/a | trivially parallel | select on validation seeds | low (Optuna; contrib ARS) |

## 6. Recommendation: 2–3 families for a restart

All three are conditional on a passed headroom gate. The gate reference should be an **h-informed (context-aware) rule**, as in the v6 gates. A context-inferring RL policy can at best approach that reference, so the gate already bounds what R1 can win.

### R1. Context-conditioned recurrent on-policy actor-critic

**Algorithms**
- **RecurrentPPO** (sb3-contrib, LSTM) with **structured domain randomisation** over SUMO vType distributions and per-episode hidden conditions;
- an **asymmetric critic** that sees the privileged context;
- an **auxiliary context-prediction head**;
- optionally an **RMA-style two-phase** teacher/student.

**Adds over v5 RecurrentPPO**
- Generalisation across hidden heterogeneity, which is exactly what failed.
- Lower value-estimate variance from the privileged critic.
- A falsifiable diagnostic of whether the history carries context information.
- An OOD test protocol.

**Main risk:** DR breadth costs in-distribution performance ("small loss", Vinitsky 2020). Against a 2.5–4.3 % edge, the net gain may fall inside the CI. The custom SB3 policy is moderate work.

### R2. Hybrid RL over tuned control

**Algorithms**
- **MaskablePPO** choosing among a menu of BO-tuned controller parameter sets (ALINEA/PI-ALINEA gains and set-points, MPC weights), with masks enforcing queue constraints;
- or a **residual PPO** (bounded Δ on a tuned ALINEA rate, zero-initialised);
- stretch: **MPC-parametrised Q-learning** (Airaldi et al.).

**Adds over v5 RecurrentPPO**
- Starts at the tuned baseline.
- Constraint handling and shielding (P6).
- Fewer samples.
- Interpretable actions.
- A framing as "adaptive control" that reviewers in traffic engineering accept (inference).

**Main risk**
- With a 0–5 % oracle gap the residual ≈ 0.
- Reviewers may credit the controller, not DRL.
- No MaskableRecurrentPPO in contrib, so combining masks with memory needs custom code [GK-VERIFY].

### R3. Non-RL policy search as co-primary comparator and falsification

**Algorithms**
- **BO (Optuna TPE / GP)** or **CMA-ES** to tune every baseline on tuning seeds;
- **ARS (sb3-contrib)** with a linear policy on the *same* observation features, including filtered history, as the RL agent.

**Adds over v5:** makes "DRL beats tuned control" defensible. It separates "the features carry information" from "deep recurrent learning extracts it". It is cheap and fully parallel.

**Main risk:** it may match RecurrentPPO, which removes the DRL claim for that cell. That is a real result, and better learned early.

### Not recommended for the restart

- **Distributional** (§3).
- **Learned world models:** DreamerV3-TSC shows no clear data-efficiency gain [ABSTRACT].
- **Offline** (no field data).
- **Transformers** (no evidence; not in SB3).
- **MARL** (only for multi-ramp corridors).
- **Per-vehicle CAV control** (v6 exclusions).

## 7. Sources (as read in this session)

1. Vinitsky, Kreidieh, Le Flem, Kheterpal, Jang, Wu C., Wu F., Liaw, Liang, Bayen. "Benchmarks for reinforcement learning in mixed-autonomy traffic." CoRL 2018, PMLR 87. https://proceedings.mlr.press/v87/vinitsky18a.html. [TEXT §4–5, Table 1, App. A.4/B]
2. Jang, Lichtlé, Vinitsky, Shah, Bunting, Nice, Piccoli, Seibold, Work, Delle Monache, Sprinkle, Lee, Bayen. "Reinforcement Learning Based Oscillation Dampening: Scaling up Single-Agent RL algorithms to a 100 AV highway field operational test." arXiv 2402.17050v2 (2024). [TEXT §2.2, §3.1–3.2, Table 1, sidebars] Table 1 "Deployed" row reading is uncertain [VERIFY].
3. Lichtlé, Jang, Vinitsky, Shah, Lee, Bayen. BAIR blog "Scaling Up Reinforcement Learning for Traffic Smoothing: A 100-AV Highway Deployment", 2025-03-25. https://bair.berkeley.edu/blog/2025/03/25/rl-av-smoothing/. [SNIPPET: fetched summary] Claims: up to 20 % fuel savings in simulation with < 5 % AVs; field "trend of 15 to 20% of energy savings around our controlled cars". [VERIFY]
4. Vinitsky, Lichtlé, Parvate, Bayen. "Optimizing Mixed Autonomy Traffic Flow With Decentralized Autonomous Vehicles and Multi-Agent RL." arXiv 2011.00120; ACM TCPS (year [VERIFY]). [TEXT abstract, §III-B, §III-E, §IV-A/B]
5. Airaldi, De Schutter, Dabiri. "Reinforcement Learning With Model Predictive Control for Highway Ramp Metering." IEEE T-ITS 26(5):5988–6004, 2025; arXiv 2311.08820. [TEXT §V]
6. Ault, Sharon. "Reinforcement Learning Benchmarks for Traffic Signal Control." NeurIPS 2021 Datasets & Benchmarks. https://people.engr.tamu.edu/guni/papers/NeurIPS-signals.pdf. [TEXT abstract, §4.2–4.3, Table 1]
7. Shi, Devailly, Larocque, Charlin. "Improving the generalizability and robustness of large-scale traffic signal control." arXiv 2306.01925. [ABSTRACT]
8. Lyle, Castro, Bellemare. "A Comparative Analysis of Expected and Distributional Reinforcement Learning." AAAI 2019; arXiv 1901.11084. [ABSTRACT]
9. Dabney, Ostrovski, Silver, Munos. "Implicit Quantile Networks for Distributional Reinforcement Learning." ICML 2018; arXiv 1806.06923. [ABSTRACT]
10. Ni, Eysenbach, Salakhutdinov. "Recurrent Model-Free RL Can Be a Strong Baseline for Many POMDPs." ICML 2022; arXiv 2110.05038. [ABSTRACT]
11. Peng, Andrychowicz, Zaremba, Abbeel. "Sim-to-Real Transfer of Robotic Control with Dynamics Randomization." ICRA 2018; arXiv 1710.06537. [ABSTRACT]
12. Kumar, Fu, Pathak, Malik. "RMA: Rapid Motor Adaptation for Legged Robots." RSS 2021; arXiv 2107.04034. [ABSTRACT]
13. Zang et al. "MetaLight: Value-Based Meta-Reinforcement Learning for Traffic Signal Control." AAAI 2020. [SNIPPET]
14. Zou, Qin. "Bayesian Meta-reinforcement Learning for Traffic Signal Control." arXiv 2010.00163. [ABSTRACT]
15. Zhang, Zhang, Deng, Li. "DataLight: Offline Data-Driven Traffic Signal Control." arXiv 2303.10828 (venue line on arXiv says ECML PKDD 2026 [VERIFY]). [ABSTRACT]
16. Han et al. "A physics-informed reinforcement learning-based strategy for local and coordinated ramp metering." Transportation Research Part C 137 (2022). Authors [VERIFY]. [SNIPPET]
17. Li, Lin, Luo, Yu. "DreamerV3 for Traffic Signal Control: Hyperparameter Tuning and Performance." arXiv 2503.02279. [ABSTRACT]
18. "ModelLight: Model-Based Meta-Reinforcement Learning for Traffic Signal Control." arXiv 2111.08067. [SNIPPET]
19. Yu, Velu, Vinitsky, Gao, Wang, Bayen, Wu. "The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games." NeurIPS 2022 D&B; arXiv 2103.01955. [ABSTRACT]
20. Mania, Guy, Recht. "Simple random search provides a competitive approach to reinforcement learning." arXiv 1803.07055 (2018). [ABSTRACT]
21. Belletti, Haziza, Gomes, Bayen. "Expert Level control of Ramp Metering based on Multi-task Deep Reinforcement Learning." arXiv 1701.08832. [ABSTRACT] Multi-task RL with Mutual Weight Regularization for PDE-modelled freeway control. Not used above beyond noting shared-experience MARL.
22. "Dissipating Stop-and-Go Waves in Closed and Open Networks via Deep Reinforcement Learning" (ITS Berkeley publication page). Authors (Kreidieh, Wu, Bayen?) and venue (ITSC 2018?) [GK-VERIFY]. [SNIPPET]
23. "Safe and Efficient CAV Lane Changing using Decentralised Safety Shields." arXiv 2505.01453. [SNIPPET]
24. "Learning highway ramp merging via reinforcement learning with temporally-extended actions." CMU RI publication page. [SNIPPET]
25. "Distributionally Robust Multi-Agent Reinforcement Learning for Intelligent Traffic Control." arXiv 2512.18558. [SNIPPET]
26. sb3-contrib documentation (master): ARS, CrossQ, MaskablePPO, RecurrentPPO, QR-DQN, TQC, TRPO. https://sb3-contrib.readthedocs.io/en/master/. [TEXT: index page]

Mentioned from general knowledge only, all **[GK-VERIFY]**:

- PPO (Schulman 2017), SAC (Haarnoja 2018), TD3 (Fujimoto 2018), C51 (Bellemare 2017), QR-DQN (Dabney 2018), TQC (Kuznetsov 2020), Rainbow (Hessel 2018), CrossQ (Bhatt 2024);
- QMIX (Rashid 2018), MBPO (Janner 2019), DreamerV3 (Hafner 2023), MuZero (Schrittwieser 2020), CQL (Kumar 2020), IQL (Kostrikov 2022);
- VariBAD (Zintgraf 2020), PEARL (Rakelly 2019), residual RL (Johannink 2019; Silver 2018), CPO (Achiam 2017), shielding (Alshiekh 2018), asymmetric actor-critic (Pinto 2018), GTrXL (Parisotto 2020), options (Sutton, Precup, Singh 1999);
- libraries: Optuna, OmniSafe, d3rlpy, RLlib/EPyMARL/BenchMARL.

## 8. Not checked / open

- No VSL papers, by rule.
- Transformers for traffic RL: not searched.
- Recurrent off-policy traffic papers: not searched.
- Explicit BO-vs-DRL head-to-heads on ramp metering in SUMO: one search, nothing usable.
- Whether CIRCLES' "augmented value function" means privileged critic inputs.
- The exact CIRCLES Table 1 values for the deployed controller.
- Whether `RecurrentMaskablePPO` exists anywhere maintained.
- X6 count (≥ 15 DRL papers) per family/application: not done here.
