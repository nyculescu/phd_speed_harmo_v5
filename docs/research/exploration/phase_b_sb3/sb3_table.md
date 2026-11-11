# Ten SB3 actor-critic families for per-CAV headway control: desk comparison

**Status.** Desk work only: nothing was installed, built, trained or simulated. Library facts come from the installed 2.8.0 source [L1]. Six documentation pages were opened through a summarising fetch tool, so their quotes may not be character-exact.

## Cost basis, common to every row

- One training set = 5 learners × (500 updates × 3 environments + 3 pilot episodes) = **7,515 simulated episodes** [P2].
- About 31,000 decisions per episode, so about 47 million per learner and 236 million per set [P3].
- Wall time per set: 500 × 23.5 s ≈ 3.3 h on the idle laptop (V391-V392); 500 × 29.6 s ≈ 4.1 h in v3w's stored event files; 500 × 81 s ≈ 11.3 h for 1B with 40 learners sharing the rented machine [P3][P4].
- As plain runs at V475's rate: 7,515 ÷ 2,600-3,050 runs/h ≈ 2.5-2.9 h, $0.75-0.98. ESTIMATE, and a floor. The memo's figure is $2-3 per set, also an estimate [P4].
- Simulator share of an update: not logged. INFERENCE from the event files: one collect is about 14-19 s of a 29.6-s update (first logged time 43-49 s, with the pilot collect). SUMO is roughly half to two thirds of the wall time: the larger share, not the whole.
- No family changes this: every decision needs a SUMO run, and nothing can run beside training (V392).

## Build routes named in the table (INFERENCE, read from code, not executed)

SB3 holds no multi-agent code [L13].

- **Flat buffer.** Keep our `collect`, which already yields flat per-car samples with per-car advantages [P2]. Hand them to the SB3 class through a custom `rollout_buffer_class`, then call `train()` [L6][L14].
- **Car slots.** Show K car slots per SUMO process as K environments. Empty slots give padding rows, and SB3's losses are plain means [L6], so padding enters the loss unless `train()` is rewritten. Cars not due at a step need pseudo-rows, the no-effect samples V290 removed.
- **Centralised critic.** In every family the actor and the critic read the same observation [L12]. A critic with 10 extra global inputs needs a custom policy class.
- **Replay (off-policy).** One transition = the car's observation at its decision, its action scaled to [−1, 1], the mean reward over the 10-s interval, and its observation at its next decision [L5][L10]. Nothing is terminal: leaving and the horizon are cut-offs. A car's last transition has no next observation (about 1 in 30). The critic is Q(16 local + 10 global, own action).

## (A) Table

| Family | 1. Actions in 2.8.0 and the design here | 2. Per-CAV shared policy, varying car count | 3. Sample use against simulator cost | 4. Hypothesis and bounding screen | 5. Record |
|---|---|---|---|---|---|
| A2C | Box, Discrete, MultiDiscrete, MultiBinary [L2]. The 4 levels fit as Discrete(4). No masks. | Flat buffer or car slots; custom critic class. | 7,515 episodes at the same update count. One gradient step per batch [L7], against about 220 minibatch steps now. ESTIMATE: more episodes for the same learning, not fewer. | None. Same lever, so H1 bounds it. No screen makes it worth training. | Nothing. |
| PPO | All four [L2]. Discrete(4) as now. Also accepts a Box, clipped at the env step [L5]. No masks. | Flat buffer and custom critic class. This rebuilds `c_train.py` with SB3's `train()`. | The present budget: 7,515 episodes. Each batch of about 93,000 decisions is used for 10 epochs, then dropped. | None new: it is the method on record. Reference arm for any follow-up (F or R). | v3w, own trainer. Also PPO: 1B, lagr, res, attr, ahead. SB3's own PPO ran the earlier central coordinator with 6 fixed slots (V263, V265) [P5]. |
| DDPG | Box only; a subclass of TD3 [L2]. Forces a continuous headway: Box(0.8, 1.6) in seconds, sent by `setTau` when the gate is open, 1.6 s otherwise [P1]. SB3 stores it scaled to [−1, 1] [L5]. Outside 0.8-1.6 s the plant is unchecked. No masks. | Own loop, replay as above, then `train(gradient_steps, batch_size)` [L10]. One critic. Needs an action-noise object to explore [L5]. | Could reuse each transition many times. But transitions are not scarce here (31,000 per run); runs are. At the default of one gradient step per collected step [L10], a learner would take about 47 million steps of 256 samples, against about 110,000 of 4,096 now: about 27 times the sample passes (my arithmetic). Learner compute would then bound the run. A saving needs far fewer than 1,503 episodes per learner: unknown. | None directly. A Box is a new action design, not a repair: 0.8 s stays the floor (M2). Bounded by screen M above 1.6 s, and by H1 inside 0.8-1.6 s. | Nothing. |
| TD3 | Box only [L2]. As DDPG. | As DDPG, with the TD3 additions that DDPG switches off [L2]. | As DDPG. | As DDPG. | Nothing. |
| SAC | Box only [L2]. As DDPG. Neither package holds a discrete SAC [L4]. | As DDPG, but the actor is stochastic, so no noise object. | As DDPG. | As DDPG. | Nothing. Named in the earlier fair-vanilla rule (section D). |
| MaskablePPO | Discrete, MultiDiscrete, MultiBinary; no Box [L2]. Discrete(4) plus one mask per decision; gate closed = one allowed level. | As PPO. The adapter must also expose `action_masks`, and the buffer must store one mask per sample [L8]. | As PPO. About 44 % of rows would carry no policy gradient (1B's logged share [P3]). | M3, the gating half only. F or R: the memo allows it only "as a component of F or R after a screen passes" [P6]. | 1B did this in our trainer, with a gate hold: not shown better than v3w (delay −0.8 [−4.2, +1.0] and −1.2 [−3.0, +0.2] %). Hold and mask confounded; laptop rows against rented rows [P5]. |
| RecurrentPPO | All four [L2]. Discrete(4) fits. No masks: the MaskablePPO page lists recurrent policies as unsupported [L8]. | The hardest on-policy row. No `rollout_buffer_class` argument, and one LSTM state per environment slot [L9]. So car slots, or a subclass (note iii). | Same 7,515 episodes. Learner time up: LSTM of 256 units by default [L9]. ESTIMATE, not measured. | L2 memory. Screen R: the slowdown cells are where the best action can change in time. Memo: "likely to fail alone" [P6]. | Nothing. Memory was never tried (memo:64). |
| TRPO | All four [L2]. Discrete(4) fits. No masks. | As PPO; it has the `rollout_buffer_class` argument [L6]. | Same episodes. One policy step per batch plus 10 critic passes [L7]. ESTIMATE: no saving. | None. Same lever; H1 bounds it. | Nothing. |
| TQC | Box only [L2]. As DDPG. | As SAC, with quantile critics [L11]. | As DDPG. | As DDPG. | Nothing. |
| CrossQ | Box only [L2]. As DDPG. | As SAC, but only `MlpPolicy` exists [L11], so the 16 + 10 split needs custom code on a flat vector. | As DDPG. | As DDPG. | Nothing. |

M8 (recipe variance): no family addresses it. Each family is one more recipe trained once, so M8 limits how any row can be read [P9].

## (B) Notes

**(i) Discrete against continuous.** The lever is four levels, moved one level per 10-s hold [P1]; DDPG, TD3, SAC, TQC and CrossQ accept only a Box [L2], and SB3 2.8.0 has no discrete SAC [L4]. So they force a continuous headway, a new action path (the level index feeds the hold, one input and the counters), a rate limit in place of "one level per hold", and a new T0 bind check for every value between the four levels [P6]. PPO, A2C, TRPO and RecurrentPPO accept the same Box, so a continuous action is not a reason to change family (INFERENCE).

**(ii) MaskablePPO against 1B.** 1B took gate-closed rows out of the policy and entropy terms and kept them in the critic [P5]; with one allowed action MaskablePPO does the same in effect (log-probability 0, zero entropy, row kept in the value loss; INFERENCE from [L8]), and adds only that the mask also acts at sampling and can forbid single levels. The interface fits an observation-dependent gate, because the mask is read from the environment's state before each policy call [L8]. The catch is in the plant: in v3w a gate-closed decision still sets a level that acts once the gate opens, so a mask needs 1B's hold, and the confound returns [P5].

**(iii) RecurrentPPO and per-car state.** It keeps one LSTM state per environment slot and zeroes it at an episode start [L9], so each car needs its own slot from entry to exit, a start flag when a new car takes the slot, and a way to keep empty slots out of the loss. It has no buffer argument, so the flat-buffer route is closed without a subclass [L9]. INFERENCE: a recurrent layer in our own trainer is less work than bending the class.

**(iv) A2C and TRPO against PPO.** Same action spaces and buffers as PPO [L2][L6]. Each takes one policy step per batch, A2C a plain gradient step and TRPO a trust-region step [L7]. Neither addresses a listed weakness, and each would be one more recipe.

**(v) Off-policy replay.** The shared reward terms were 33 and 43 % of the reward's mean magnitude on one teaching trace [P7], and they depend on what about 200 other cars do. A replay keeps rewards earned under older policies; a PPO batch has every car under one policy (INFERENCE). A buffer of 1 million transitions, the SB3 default [L10], holds about 32 runs, which is about 11 of our updates.

## (C) Conditional follow-ups

**The honest count is one family.**

**Follow-up 1: a recurrent actor, with RecurrentPPO as the reference, only if screen R passes.**
- Mechanism (L2): the policy sees current states only and has no memory (V407, as quoted at memo:62; `b_env.py:5`). After a slowdown the best headway may depend on the phase of the recovery, which memory could carry.
- Build: RecurrentPPO cannot be used as is (note iii). INFERENCE: add an LSTM layer to `c_train.py` with one state per car, and check its sequence handling against RecurrentPPO's source. A cheaper first arm needs no new family: the last few observations stacked, in the present trainer (memo:139).
- Cost: 2 training sets (memory on, and the same code with memory off as the matched control) = 15,030 episodes, about $4-6 at the memo's $2-3 per set (estimate). Evaluation: 2 arms × 5 learners × 80 seeds × 2 cells = 1,600 runs ≈ 0.5-0.6 h, $0.16-0.21 at V475's rate. Code and tests: about a day (ESTIMATE). Author time, apart: about 1-2 h for the protocol, seeds and approvals.
- Risk: a second trained recipe (forking paths). A rule with a timer gets the same memory and is tuned on the same cells (memo:141). R itself is post hoc, and a first-round critic reports that X2 already meets R's KILL on stored rows (relayed to me, not checked).

**Follow-up 2: none as a family.**
- Masking is the nearest. For this gate MaskablePPO does what 1B's mask already does (note ii), and 1B's code exists. If F or R passes, the clean test of M3's gating half is in our trainer: hold alone against hold plus mask. 2 sets = 15,030 episodes, about $4-6; 1,600 evaluation runs, about $0.2; hours of code. It is a flag, not a family.
- No off-policy family is proposed. All five need a continuous headway (note i), and screen M decides whether a wider range pays at all. If M passes, the first step is more levels in the present PPO, whose actor size follows the level list (`c_train.py:70`).

**Plain statements.** No family changes the action's floor: 0.8 s stays both the lowest headway and the best delay rule (M2). A family changes how the policy is fitted, not what the lever can do. The memo's H1 bounds every family that uses the same lever (memo:149). Every extra family is another recipe trained once, against a learner spread of 0.3-4.1 % [P9].

## (D) The earlier "fair vanilla" rule (historical)

The project's earlier rule read: "Fair vanilla DRL: a standard algorithm (PPO; SAC for continuous actions) acting directly on the same actuators, with the same observations; the same training and tuning budget; checkpoints chosen on validation only" [P8]. It is historical: the project instructions call the D5.8 text "the historical bar", and V95 says "D5.8 is history" and that the author and Claude set the claim bar per study. With the present Discrete(4) action, v3w's PPO is the algorithm that rule named. If a continuous headway were ever introduced, the rule would name SAC as the vanilla baseline, on the same observations and budget, with checkpoints chosen on validation. INFERENCE: PPO also accepts a Box [L2], so PPO with the Box would be the like-for-like continuation of v3w and SAC a second recipe, with a replay design that has no record here. Reviving the rule is the author's decision.

## Not verified

- No build route was executed. "Fits" and "needs" are read from code.
- The docs pages carry their version in the URL only. The per-algorithm pages of A2C, PPO, DDPG, TD3, SAC, TRPO, TQC and CrossQ were not opened.
- Whether SuperSuit's wrappers handle a varying number of agents; the peak number of ALKS present at once, which sizes the car slots.
- How many episodes an off-policy family would need here; which machine v3w's 4.1-h set ran on.
- Two corrections to proj_facts: V386 replaces V385's reward shares (33 and 43 %, not 33-45 %); a collect is about 14-19 s of 29.6 s by my reading, not "about 20 of 28 s".

## Sources

`sb3/` = `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/lib/python3.14/site-packages/stable_baselines3/`; `contrib/` = `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/lib/python3.14/site-packages/sb3_contrib/`. Lines were read by me unless marked.

- [L1] Versions: `sb3/version.txt`, `contrib/version.txt`, both 2.8.0.
- [L2] Action spaces: `sb3/a2c/a2c.py:113-118`; `sb3/ppo/ppo.py:130-135`; `sb3/td3/td3.py:131`; `sb3/ddpg/ddpg.py:14` (`class DDPG(TD3)`), `:102-112` (TD3's additions removed, one critic); `sb3/sac/sac.py:147`; `contrib/ppo_mask/ppo_mask.py:124-128`; `contrib/ppo_recurrent/ppo_recurrent.py:120-125`; `contrib/trpo/trpo.py:131-136`; `contrib/tqc/tqc.py:140`; `contrib/crossq/crossq.py:132`. Enforced by an assert, `sb3/common/base_class.py:180-184`; a Box needs finite bounds, `:198-201`.
- [L3] Docs tables, opened by me: `https://stable-baselines3.readthedocs.io/en/v2.8.0/guide/algos.html` and `https://sb3-contrib.readthedocs.io/en/v2.8.0/guide/algos.html`. Version 2.8.0 is in the URL only. Both agree with [L2] for all ten.
- [L4] No discrete SAC: no match for "discrete" in `sb3/sac/`, `sb3/td3/`, `sb3/ddpg/`, `contrib/tqc/`, `contrib/crossq/` (grep, any case). In [L3] the only discrete off-policy classes are DQN and QR-DQN.
- [L5] Actions: on-policy, a Box action is clipped at the env step, `sb3/common/on_policy_algorithm.py:208-216`; off-policy, the stored action is rescaled to [−1, 1] and the env gets the unscaled value, `sb3/common/off_policy_algorithm.py:400-410`; deterministic actors explore through an action-noise object, `:379-381`, default None at `sb3/ddpg/ddpg.py:69`.
- [L6] On-policy buffers: n_steps × n_envs arrays, `sb3/common/buffers.py:391-399`; `rollout_buffer_class` at `sb3/ppo/ppo.py:98`, `sb3/a2c/a2c.py:81`, `contrib/trpo/trpo.py:97`, `contrib/ppo_mask/ppo_mask.py:92`; `get()` asserts a full buffer, `buffers.py:482`; `train()` takes no arguments, `ppo.py:184`, `a2c.py:132`, `trpo.py:232`; plain-mean losses, `ppo.py:227, 244`.
- [L7] Gradient use: A2C one pass per rollout, `a2c.py:143-144`, n_steps 5 at `:71`; PPO n_steps 2048, batch 64, 10 epochs, `ppo.py:85-87`; TRPO one pass per rollout, `trpo.py:246-247`, conjugate-gradient settings and 10 critic updates, `:89-93`.
- [L8] MaskablePPO: mask fetched from the environment before each policy call, `contrib/common/maskable/utils.py:16-19`, `ppo_mask.py:227-230`; wrapper, `contrib/common/wrappers/action_masker.py:7-32`; stored per sample, `contrib/common/maskable/buffers.py:75-84`; re-applied in the update, `ppo_mask.py:339-343`; masked logits set to −1e8 with zero entropy, `contrib/common/maskable/distributions.py:56-61, 73-83`; advantages normalised over the whole minibatch, `ppo_mask.py:347-349`. Docs page opened by me, `https://sb3-contrib.readthedocs.io/en/v2.8.0/modules/ppo_mask.html` (2.8.0 in the URL only): recurrent policies not supported; with `SubprocVecEnv`, "you must implement the action_masks inside the environment".
- [L9] RecurrentPPO: no `rollout_buffer_class` argument, `contrib/ppo_recurrent/ppo_recurrent.py:74-100`; buffer fixed at `:143`; one LSTM state per environment, `:161`; state zeroed at an episode start, `contrib/common/recurrent/policies.py:197-203`; states stored per step, `contrib/common/recurrent/buffers.py:133-145`; sequences cut at episode starts, `:84-91`; defaults 256 units, 1 layer, separate critic LSTM, `recurrent/policies.py:82-85`. Docs page opened by me: `https://sb3-contrib.readthedocs.io/en/v2.8.0/modules/ppo_recurrent.html` (2.8.0 in the URL only).
- [L10] Off-policy: `train(gradient_steps, batch_size)` at `sb3/sac/sac.py:202`, `sb3/td3/td3.py:157`, `contrib/tqc/tqc.py:197`, `contrib/crossq/crossq.py:183`; `ReplayBuffer.add`, `sb3/common/buffers.py:247`; buffer choice and n-step, `off_policy_algorithm.py:178-187`; sampled done = done × (1 − timeout), `buffers.py:322`; gradient steps after each collection, `off_policy_algorithm.py:348-354`; defaults buffer 1,000,000, batch 256, one gradient step per collection step, `sac.py:96-102`. Docs page opened by me, `https://stable-baselines3.readthedocs.io/en/v2.8.0/guide/examples.html` (2.8.0 in the URL only): "When using multiple environments with off-policy algorithms, you should update the `gradient_steps` parameter too."
- [L11] CrossQ: `MlpPolicy` only, `contrib/crossq/crossq.py:69-72` (read by me). TQC's 25 quantiles × 2 critics, `contrib/tqc/policies.py:294-295` (from lib_facts, not re-read).
- [L12] Critic inputs: actor and critic extractors come from the same call on the same observation space, `sb3/common/policies.py:118-120, 506-514`.
- [L13] Multi-agent: no match for multi-agent, PettingZoo, SuperSuit or MARL in either package (grep, 0 files). `https://pettingzoo.farama.org/tutorials/sb3/` (opened by me, no version shown): "SB3 is designed for single-agent RL and does not directly support multi-agent algorithms or environments." The page says nothing on a varying number of agents.
- [L14] Calling `train()` outside `learn()`: the logger is set by `set_logger` or `_setup_learn`, `sb3/common/base_class.py:255, 383`, and used at `:296`; `n_envs` comes from the env, `:174`.

Project. `c_train.py`, `b_env.py` = `/home/catalin/work/phd/wt/planb_v23/v5b/fleet/`; `1B/` = `/home/catalin/work/phd/v5b1_runs/round2/code_5c10e6f/v5b/fleet/`; memo = `/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/exploration/drl_win_directions_v0.md`; V-numbers = `/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/decisions.md`.

- [P1] Lever: `b_env.py:36-37` (150 m; 1.6, 1.2, 1.0, 0.8 s), `:774-784` (`setTau` to the level when the gate is open, else 1.6 s), `:703-711` (one level per hold), `:942-945` (own clock).
- [P2] Trainer: `c_train.py:1-4` ("SB3 needs fixed agent counts, hence this loop"; a leaving car is cut off and bootstrapped), `:30` (10 epochs, minibatch 4,096), `:70-73` (actor on 16, critic on 16 + 10), `:227-297` (collect), `:259-262` (exit), `:426-429` (pilot).
- [P3] Sizes: event files under `/home/catalin/work/phd/v5b1_runs/round1_remote/out/train_v3w/tb` and `/home/catalin/work/phd/v5b1_runs/round2_remote/train_1b/tb`, tags `ppo/n` (median 93-94k per update), `ppo/wall_s` (29.6-29.8 s; 80-82 s), `ppo/mask_frac` (0.44), read by me with `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/sb3/tbread.py`.
- [P4] Costs: V443 (21 s idle, about 55 s under full load), V391-V392, V447, V475, memo:116, V483.
- [P5] Record: v3w, V449; lagr, V429, V448, `c_train.py:35, 63-66`; 1B, `1B/b_env.py:691-693`, `1B/c_train.py:293-301`, `docs/research/protocols/round_2.md:34-37`, `docs/research/results/round_2_result.md:112`, V465; SB3 PPO for the central coordinator, V263, V265; trainer choice, V17.
- [P6] Memo: M2 `:84`, M3 `:85`, M8 `:90`, H1 `:19, :33-49`, L1 `:129-137`, L2 `:139-145`, L3 `:147-151`, T0 for new headway values `:263`, screens `:267-317`.
- [P7] Reward shares: V386, which replaces V385's trace numbers (gate open 51.0 and 51.7 %; shared terms 33 and 43 %; one teaching trace, not a result). Gate-closed rows unmasked: V413.
- [P8] Fair vanilla: `/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/CLAUDE.md:22-25` (four bullet lines, joined in the quote); status `:12` and V95 (`decisions.md:114`).
- [P9] Noise: learner SD 0.3-4.1 %, `docs/research/results/round_1_result.md:250-251`; paired delay SD 7-11 %, V435; checkpoint ranks reverse, V429.
