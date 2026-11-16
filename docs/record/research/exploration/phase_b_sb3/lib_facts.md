# SB3 2.8.0 and SB3-Contrib 2.8.0: library facts for the ten families

## Sources and limits

- Installed source, both `version.txt` = 2.8.0. `S/` = `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/lib/python3.14/site-packages/stable_baselines3/`, `C/` = `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/lib/python3.14/site-packages/sb3_contrib/`.
- Docs opened, all under `/en/v2.8.0/` (the version is in the URL; the page text shows none): `stable-baselines3.readthedocs.io` index, guide/algos, guide/examples, guide/vec_envs, guide/custom_env, guide/rl_tips, guide/developer, misc/projects, misc/changelog; `sb3-contrib.readthedocs.io` guide/algos, modules/ppo_mask, modules/ppo_recurrent, modules/crossq, misc/changelog.
- The docs were read through a fetch tool that summarises pages. Doc quotes below are the fragments it returned and may not be character-exact. Source lines were read directly.
- Nothing was imported, constructed, installed or run. Statements that a route "works" are read from the code, not executed.

## Table (items 1-4)

| Family | Action spaces in source | Docs 2.8 table | Type, buffer, n_envs | Policy features | Defaults that set sample use |
|---|---|---|---|---|---|
| A2C | Box, Discrete, MultiDiscrete, MultiBinary (`S/a2c/a2c.py:113-118`) | same | on-policy (`a2c.py:16`); `RolloutBuffer` or `DictRolloutBuffer` (`S/common/on_policy_algorithm.py:119-123`); `rollout_buffer_class` argument (`a2c.py:81`); multi-env yes (`on_policy_algorithm.py:95`) | Mlp, Cnn, MultiInput (`a2c.py:60-64`); no mask, no memory | n_steps 5, gae_lambda 1.0, lr 7e-4, RMSprop (`a2c.py:70-78,126`); one gradient step on the whole rollout (`a2c.py:144`) |
| PPO | all four (`S/ppo/ppo.py:130-135`) | same | on-policy; as A2C; `rollout_buffer_class` (`ppo.py:98`) | Mlp, Cnn, MultiInput (`ppo.py:74-78`); no mask, no memory | n_steps 2048, batch_size 64, n_epochs 10, gae_lambda 0.95, lr 3e-4, clip 0.2, target_kl None (`ppo.py:84-100`) |
| DDPG | Box only, inherited: `class DDPG(TD3)` (`S/ddpg/ddpg.py:14`) | Box only | off-policy; replay buffers as TD3; multi-env via TD3 | TD3 policies; n_critics 1 (`ddpg.py:111-112`) | buffer 1e6, learning_starts 100, batch 256, train_freq 1, gradient_steps 1, n_steps 1, action_noise None (`ddpg.py:61-73`); policy_delay 1, target_noise_clip 0 (`ddpg.py:104-106`) |
| TD3 | `(spaces.Box,)` (`S/td3/td3.py:131`) | Box only | off-policy (`td3.py:19`); `ReplayBuffer`, `DictReplayBuffer` or `NStepReplayBuffer` (`S/common/off_policy_algorithm.py:178-187`); multi-env yes (`td3.py:132`) | Mlp, Cnn, MultiInput (`td3.py:69-73`); n_critics 2 (`S/td3/policies.py:126`); actor and critic targets | lr 1e-3, buffer 1e6, learning_starts 100, batch 256, tau 0.005, train_freq 1, gradient_steps 1, n_steps 1, policy_delay 2, target_policy_noise 0.2 (`td3.py:84-99`) |
| SAC | `(spaces.Box,)` (`S/sac/sac.py:147`) | Box only | off-policy (`sac.py:19`); as TD3; multi-env yes (`sac.py:148`) | Mlp, Cnn, MultiInput (`sac.py:81-85`); n_critics 2, extractor not shared (`S/sac/policies.py:230-231`); critic target (`sac/policies.py:300`) | lr 3e-4, buffer 1e6, learning_starts 100, batch 256, tau 0.005, train_freq 1, gradient_steps 1, n_steps 1, ent_coef auto, target_update_interval 1 (`sac.py:95-110`) |
| MaskablePPO | Discrete, MultiDiscrete, MultiBinary; no Box (`C/ppo_mask/ppo_mask.py:124-128`) | same (Box no) | on-policy (`ppo_mask.py:23`); `MaskableRolloutBuffer` or `MaskableDictRolloutBuffer` (`ppo_mask.py:156-160`); `rollout_buffer_class` (`ppo_mask.py:92`); multi-env yes | masks; Mlp, Cnn, MultiInput (`ppo_mask.py:68-72`); no `use_sde` argument (`ppo_mask.py:76-102`); docs page: recurrent policies "no" | n_steps 2048, batch_size 64, n_epochs 10 (`ppo_mask.py:80-83`) |
| RecurrentPPO | all four (`C/ppo_recurrent/ppo_recurrent.py:120-125`) | same | on-policy (`ppo_recurrent.py:23`); `RecurrentRolloutBuffer` or `RecurrentDictRolloutBuffer`, fixed in `_setup_model` (`ppo_recurrent.py:143`); no `rollout_buffer_class` argument (`ppo_recurrent.py:74-100`); multi-env yes | MlpLstm, CnnLstm, MultiInputLstm (`ppo_recurrent.py:68-72`); LSTM 256 units, 1 layer, separate critic LSTM by default (`C/common/recurrent/policies.py:82-85`); no mask | n_steps 128, batch_size 128, n_epochs 10 (`ppo_recurrent.py:78-81`) |
| TRPO | all four (`C/trpo/trpo.py:131-136`) | same | on-policy (`trpo.py:24`); as PPO; `rollout_buffer_class` (`trpo.py:97`) | plain `ActorCriticPolicy` aliases (`C/trpo/policies.py:3-7`) | n_steps 2048, batch_size 128 (value function only), cg_max_steps 15, cg_damping 0.1, line_search_shrinking_factor 0.8, line_search_max_iter 10, n_critic_updates 10, target_kl 0.01, sub_sampling_factor 1, lr 1e-3 (`trpo.py:85-101`); policy step on the whole rollout (`trpo.py:247`) |
| TQC | `(spaces.Box,)` (`C/tqc/tqc.py:140`) | Box only | off-policy (`tqc.py:20`); as SAC; multi-env yes (`tqc.py:141`) | Mlp, Cnn, MultiInput (`tqc.py:73-77`); n_quantiles 25, n_critics 2 (`C/tqc/policies.py:294-295`); critic target (`tqc/policies.py:364`) | as SAC (`tqc.py:87-102`); top_quantiles_to_drop_per_net 2 (`tqc.py:103`), so 46 of 50 target quantiles kept (`tqc.py:253`) |
| CrossQ | `(spaces.Box,)` (`C/crossq/crossq.py:132`) | Box only | off-policy (`crossq.py:18`); as SAC; multi-env yes (`crossq.py:133`) | MlpPolicy only, "TODO: Implement CnnPolicy and MultiInputPolicy" (`crossq.py:69-72`), so no Dict observations (the docs page agrees); BatchRenorm in actor and critic (`C/crossq/policies.py:18,70-73,264-267`); "no target networks, tau=1.0" (`crossq.py:114`, also `:238`) | lr 1e-3, buffer 1e6, learning_starts 100, batch 256, train_freq 1, gradient_steps 1, n_steps 1, policy_delay 3 (`crossq.py:81-95`); nets pi [256,256], qf [1024,1024] (`crossq/policies.py:406`); renorm_warmup_steps 100,000 (`crossq/policies.py:370`); Adam betas (0.5, 0.999) (`crossq/policies.py:388-389`) |

## Notes on items 1-4

**1. Action spaces.**
- Source and both 2.8.0 docs tables agree for all ten families: no difference found.
- The list is enforced by an assert at construction (`S/common/base_class.py:180-184`). A Box must have finite bounds (`base_class.py:198-201`).
- Off-policy families store the action rescaled to [-1, 1] (`off_policy_algorithm.py:400-409`). On-policy families sample an unbounded Gaussian, clip it at the env step and store the unclipped value (`on_policy_algorithm.py:208-216,247-249`).
- INFERENCE for this plant: the 4 levels fit A2C, PPO, TRPO, MaskablePPO and RecurrentPPO as they are. A continuous headway range fits every family except MaskablePPO. DDPG, TD3, SAC, TQC and CrossQ cannot take the 4 levels directly: the action must be a Box (a continuous headway, or a Box value that the env maps to levels).
- Masks exist only in MaskablePPO: `action_masks` appears in no file outside `C/common/maskable/`, `C/common/wrappers/action_masker.py`, `C/common/envs/` and `ppo_mask.py` (grep). No class combines masks with an LSTM.
- The only discrete off-policy classes in the two packages are DQN and QR-DQN (docs table), which are value-based and outside the ten.

**2. Collection and buffers.**
- On-policy: the buffer is a rectangle of n_steps x n_envs (`S/common/buffers.py:392-399`), reset every rollout (`on_policy_algorithm.py:187`).
- Off-policy with several envs:
  - every loop iteration steps all envs once and adds n_envs to `num_timesteps` (`off_policy_algorithm.py:568-571`);
  - `train_freq` counts loop iterations (`S/common/utils.py:587-588`); the episode unit is refused with more than one env (`off_policy_algorithm.py:551-552`);
  - after each collection `train()` runs `gradient_steps` steps; -1 means the number of transitions just collected (`off_policy_algorithm.py:348-354,608`). With the default 1 the update-to-data ratio falls to 1/n_envs. The examples page (v2.8.0) says: "When using multiple environments with off-policy algorithms, you should update the `gradient_steps` parameter too";
  - the buffer holds buffer_size // n_envs rows of n_envs columns (`buffers.py:198,213`) and samples a random row, then a random column (`buffers.py:113-114,309`);
  - `learning_starts` is compared with `num_timesteps`; before it, actions come from `action_space.sample()` (`off_policy_algorithm.py:389-391`).
- n-step returns: `n_steps` > 1 selects `NStepReplayBuffer` (`off_policy_algorithm.py:182-185`), which the SB3 changelog lists under 2.7.0. It is not available with Dict observations (`off_policy_algorithm.py:181`) or with `optimize_memory_usage` (`buffers.py:883-884`). It reads the next n rows of the same column as one trajectory (`buffers.py:908-914`). SAC, TD3, TQC and CrossQ use the returned `discounts` (`sac.py:220`, `td3.py:170`, `tqc.py:215`, `crossq.py:202`).

**3. Policy features.**
- RecurrentPPO:
  - LSTM only. The actor always has one; the critic has its own (default), shares the actor's with gradients detached (`shared_lstm`), or is feed-forward (`enable_critic_lstm=False`) (`recurrent/policies.py:112-144,237-246`);
  - the buffer stores the hidden and cell states of both for every step (`C/common/recurrent/buffers.py:133-145`);
  - sequences are cut at episode starts and env changes (`recurrent/buffers.py:84-91`), padded (`:17-40`), started from the stored state (`:218-229`), and padding is excluded from the losses (`:243`; `ppo_recurrent.py:343,364,382`);
  - minibatches keep time order: the index list is only rotated at a random point (`recurrent/buffers.py:186-188`).
- MaskablePPO:
  - before each policy call the mask is fetched with `env.env_method("action_masks")` on a VecEnv, or `get_wrapper_attr("action_masks")()` (`C/common/maskable/utils.py:5,16-19`; `ppo_mask.py:227-230`);
  - an env without the method is wrapped in `ActionMasker` (`C/common/wrappers/action_masker.py:7-32`). The docs page says a `SubprocVecEnv` needs "the `action_masks` inside the environment";
  - the mask is any function of the env's current state, so it can follow whatever the observation is built from. It is not computed from the observation tensor;
  - it is stored per sample (`C/common/maskable/buffers.py:75,84`) and re-applied in the update (`ppo_mask.py:339-343`). Invalid logits become -1e8 and add no entropy (`C/common/maskable/distributions.py:59-61,76-82`);
  - INFERENCE: a sample with one valid action (gate closed) has log-probability 0, so it adds nothing to the policy or entropy terms, but it still enters the value loss and the advantage normalisation (`ppo_mask.py:349`).
- Separate networks: `net_arch=dict(pi=[64,64], vf=[64,64])` is the default (`S/common/policies.py:500`); shared MLP layers were removed in 1.8.0 (`policies.py:488`).
- Critic-only inputs: not available without custom policy code, in any family. Actor and critic extractors are built from the same class and kwargs on the same observation space (`policies.py:118-120,506-514`; off-policy `policies.py:96-116`, `sac/policies.py:288-297`). A critic with 10 extra global inputs needs a policy subclass (INFERENCE: a Dict observation whose global key the actor's extractor ignores).

**4. Sample use.** With defaults, PPO, TRPO and MaskablePPO use 2048 x n_envs transitions per update, RecurrentPPO 128 x n_envs, A2C 5 x n_envs. The five off-policy families take one gradient step per collection step. The rl_tips page (v2.8.0) names "`SAC`, `TD3`, `CrossQ` and `TQC`" for continuous actions in a single process. The CrossQ page says it works "without requiring high update-to-data ratios".

## 5. Custom collection loop

- On-policy entry points:
  - `RolloutBuffer.add(obs, action, reward, episode_start, value, log_prob)` (`buffers.py:440-448`);
  - `compute_returns_and_advantage(last_values, dones)` (`buffers.py:403`);
  - `get()`, which asserts the buffer is full (`buffers.py:482`);
  - `train()` takes no arguments and reads `self.rollout_buffer` (`ppo.py:184,207`; `a2c.py:132,144`; `trpo.py:232,247`);
  - `collect_rollouts` is an ordinary method (`on_policy_algorithm.py:162`); MaskablePPO and RecurrentPPO override it (`ppo_mask.py:181`; `ppo_recurrent.py:195`).
- Rectangular assumption: GAE runs down the step axis of each env column and cuts at `episode_starts` (`buffers.py:426-435`). The PPO, A2C and TRPO losses are plain means with no per-sample weight (`ppo.py:227,244`; `a2c.py:159,162`; `trpo.py:365`).
- INFERENCE: a varying car count needs either fixed slots with padding, which enters the loss unless `train()` is rewritten, or a custom `rollout_buffer_class` whose `get()` yields flat per-car samples with advantages computed outside. The second is what the project trainer's `collect` already produces (`/home/catalin/work/phd/wt/planb_v23/v5b/fleet/c_train.py:227-297`). RecurrentPPO offers no buffer argument.
- Off-policy entry points:
  - `ReplayBuffer.add(obs, next_obs, action, reward, done, infos)`, one row of n_envs transitions per call (`buffers.py:247-283`);
  - `train(gradient_steps, batch_size)` is public (`sac.py:202`, `td3.py:157`, `tqc.py:197`, `crossq.py:183`);
  - INFERENCE: with n_envs = 1, per-car transitions can be added in any order for 1-step targets, because rows are sampled independently. `NStepReplayBuffer` needs each car's transitions contiguous and closed by a done or timeout flag. Actions must be stored already scaled.
- Preconditions for calling `train()` directly:
  - the logger is set only by `set_logger` (`base_class.py:255-267`) or `_setup_learn` (`base_class.py:431`), and `_update_learning_rate` uses it (`base_class.py:296`);
  - with `env=None` the constructor sets no spaces and no `n_envs` (`base_class.py:168-174`), which `_setup_model` needs, so a model needs an env object or spaces set by hand.
- Episode ends:
  - the VecEnv resets by itself and puts `terminal_observation` and `TimeLimit.truncated` ("truncated and not terminated") in `info` (vec_envs page v2.8.0);
  - on-policy: when both keys are present, `rewards[idx] += self.gamma * terminal_value` (`on_policy_algorithm.py:236-245`; `ppo_mask.py:251-260`; `ppo_recurrent.py:270-285`);
  - off-policy: `timeouts` is filled from `TimeLimit.truncated` (`buffers.py:277-278`), the sampled done is `dones * (1 - timeouts)` (`buffers.py:322`), and the next observation is the terminal one (`off_policy_algorithm.py:484-495`);
  - a hand-filled buffer must reproduce both steps. INFERENCE: both need an observation after the last decision. A car that has left has none; the project trainer bootstraps from the car's last value instead (`c_train.py:3-4,259-262`).
- Docs (developer guide and examples pages, v2.8.0): calling `train()` directly and filling buffers by hand: not found.

## 6. Multi-agent in the documentation

- SB3 2.8.0 index, algos, examples, vec_envs, custom_env, rl_tips and developer pages; Contrib ppo_mask, ppo_recurrent and crossq pages: not found.
- Installed source of both packages: no match for multi-agent, PettingZoo, SuperSuit or MARL (grep).
- SB3 projects page (v2.8.0), SuperSuit entry: "A wrapper is included that allows for using regular single agent RL libraries" to "learn simple multi-agent PettingZoo environments". SUMO-RL entry: "Supports Multiagent RL".
- PettingZoo tutorial page `pettingzoo.farama.org/tutorials/sb3/` (no version shown): "SB3 is designed for single-agent RL and does not directly support multi-agent algorithms or environments"; "PPO with parameter sharing, allowing a single model to control all the agents".
- Varying number of agents: not found on any page opened. Whether the SuperSuit vector wrapper needs a fixed agent count: not verified. Its GitHub README (no version shown) calls the project "semi-depricated, and is unmaintained except for being kept operational".
- SuperSuit is not installed in the venv; pettingzoo 1.27.0 is.

## 7. Changelog

- SB3 changelog (v2.8.0 URL): top entry "Release 2.8.0 (2026-04-01)". Python 3.9 dropped, 3.13 supported, `strict=True` on every `zip`. No behaviour change to A2C, PPO, DDPG, TD3 or SAC was listed.
- Contrib changelog (v2.8.0 URL): top entry "Release 2.8.0 (2026-04-01)". Bug fixes:
  - `n_updates` counting in MaskablePPO and RecurrentPPO when `target_kl` stops an update early;
  - action reshaping before clipping in `forward` and `predict` of both;
  - RecurrentPPO no longer calls `forward()` directly;
  - a "Simplex" crash in `MaskableCategorical.apply_masking()` on torch 2.9+ (the fix is visible at `distributions.py:67-69`; the venv has torch 2.11 per the project CLAUDE.md).
- TRPO, TQC and CrossQ: no 2.8.0 entry.
- 2.7.0 (2025-07-25), both packages: n-step returns for off-policy algorithms through `n_steps`, with `NStepReplayBuffer`.
- 2.6.0, Contrib: MaskablePPO with `SubprocVecEnv` fixed through `vec_env.has_attr()`.

## Not verified

- No route in section 5 was executed.
- The per-algorithm docs pages of A2C, PPO, DDPG, TD3, SAC, TQC and TRPO were not opened; their Dict-observation support is taken from `policy_aliases` in the source.
- The changelogs were read as summaries, not verbatim.
