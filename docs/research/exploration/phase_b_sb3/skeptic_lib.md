# Skeptic report: library claims in sb3_table.md

Method. I opened every line below in the installed 2.8.0 source (`sb3/version.txt`, `contrib/version.txt`). Nothing was built, trained or run. `sb3/` = `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/lib/python3.14/site-packages/stable_baselines3/`, `contrib/` = `.../site-packages/sb3_contrib/`. Docs pages came through a summarising fetch: quotes may not be character-exact, and no page shows a version in its text, only `v2.8.0` in the URL.

## Wrong or overstated (4)

**W1. Column 3, off-policy rows: "at the default of one gradient step per collected step ... 47 million steps".** The default is `train_freq=1, gradient_steps=1` (`sb3/sac/sac.py:101-102`). One step is one `env.step` of the whole VecEnv, so n_envs transitions (`sb3/common/off_policy_algorithm.py:568-571, 608`; `sb3/common/utils.py:587-588`). One gradient step per transition holds only with n_envs = 1 or `gradient_steps=-1` (`off_policy_algorithm.py:351`). With K car slots the default gives 47 million / K. In the own-loop route no default applies: `train(gradient_steps, batch_size)` takes what the caller passes (`sac.py:202`). "27 times" is an upper reading, not the default.

**W2. Build routes: "SB3's losses are plain means, so padding enters the loss unless `train()` is rewritten".** Confirmed for PPO (`sb3/ppo/ppo.py:227, 244, 252`), A2C (`sb3/a2c/a2c.py:159, 162`), TRPO (`contrib/trpo/trpo.py:281, 365`), MaskablePPO (`contrib/ppo_mask/ppo_mask.py:357, 374, 382`). Wrong for RecurrentPPO: its `train()` applies a per-row mask to the advantage normalisation and to the policy, value and entropy terms (`contrib/ppo_recurrent/ppo_recurrent.py:343, 356, 364, 382, 391`). The stock buffer sets the mask to 1 for stored rows and 0 only for sequence padding (`contrib/common/recurrent/buffers.py:243`), so empty slots need a changed buffer, not a rewritten `train()`.

**W3. Note (ii): MaskablePPO "does the same in effect" as 1B and "adds only" sampling.** Zero entropy for a one-action row follows from `contrib/common/maskable/distributions.py:56-61, 72-82`; its zero policy gradient is INFERENCE, not executed. But MaskablePPO normalises advantages over all rows and averages the policy and entropy terms over all rows (`ppo_mask.py:347-349, 357, 382`). 1B does both over open rows only (`/home/catalin/work/phd/v5b1_runs/round2/code_5c10e6f/v5b/fleet/c_train.py:269, 293-299`). INFERENCE: the policy and entropy terms are scaled by the open share (about 0.56). Not the same update.

**W4. Note (iii): flat-buffer route "closed without a subclass".** The fact holds: no `rollout_buffer_class` argument (`ppo_recurrent.py:74-100`), buffer class fixed (`:143, :176`). "Closed" is overstated: `train()` reads only `self.rollout_buffer.get()` (`:336`), an attribute that can be replaced after construction (INFERENCE, not executed). The replacement must yield `lstm_states`, `episode_starts`, `mask` (`recurrent/buffers.py:233-244`).

**Docs possibly stale, [L8].** The page does say `ActionMasker` cannot be used with `SubprocVecEnv`. The installed worker resolves `env_method` through `get_wrapper_attr`, which searches wrappers (`sb3/common/vec_env/subproc_vec_env.py:56-58`). INFERENCE: the restriction may not hold in 2.8.0; not executed.

## Confirmed

- **Box only:** TD3 `sb3/td3/td3.py:131`, SAC `sac.py:147`, TQC `contrib/tqc/tqc.py:140`, CrossQ `contrib/crossq/crossq.py:132`; DDPG inherits (`sb3/ddpg/ddpg.py:14, 81`).
- **Box, Discrete, MultiDiscrete, MultiBinary:** A2C `a2c.py:113-118`, PPO `ppo.py:130-135`, TRPO `trpo.py:131-136`, RecurrentPPO `ppo_recurrent.py:120-125`.
- **MaskablePPO, no Box:** `ppo_mask.py:124-128`; its buffer raises on other spaces (`contrib/common/maskable/buffers.py:71-72`).
- **Enforcement:** an assert, only when an env is passed (`sb3/common/base_class.py:168, 180-184`); finite Box bounds `:198-201`.
- **No discrete SAC:** "discrete" matches 0 files in `sac`, `td3`, `ddpg`, `tqc`, `crossq`.
- **Mask fetch:** `np.stack(env.env_method("action_masks"))` before each policy call (`contrib/common/maskable/utils.py:16-17`; `ppo_mask.py:227-230`); error if absent (`:216-217`); stored per sample (`maskable/buffers.py:75-84`); re-applied in the update (`ppo_mask.py:339-343`).
- **n-step: present.** `NStepReplayBuffer` (`sb3/common/buffers.py:847-954`), chosen when `n_steps > 1` and the observation is not a Dict (`off_policy_algorithm.py:178-187`); default 1 in `sac.py:107`, `td3.py:96`, `ddpg.py:73`, `tqc.py:99`, `crossq.py:92`. It reads consecutive rows of one env column (`buffers.py:908-914`). INFERENCE: unusable with flat per-car rows.
- **Off-policy n_envs > 1: accepted.** `support_multi_env=True` at `td3.py:132`, `sac.py:148`, `tqc.py:141`, `crossq.py:133`; guard `base_class.py:186-189`; step-unit `train_freq` required (`off_policy_algorithm.py:551-552`); the buffer holds buffer_size // n_envs rows (`buffers.py:198`), so 1 million is total transitions.
- **At the cited lines:** [L1]; [L5], with the noise code at `off_policy_algorithm.py:404-406` and the first 100 steps uniform random (`:389-391`, `sac.py:97`); [L6]; [L7]; [L9]; [L10]; [L11] (`contrib/tqc/policies.py:294-295` re-read); [L12], also `sb3/sac/policies.py:288-297`; [L13]; [L14] (logger assigned at `base_class.py:265, 431`, no default, `:104`); DDPG's removed additions (`ddpg.py:102-112`; `td3.py:174-176, 197`).
- **Docs:** both algos tables agree with the source for all ten; ppo_mask page "Recurrent policies: ❌"; the ppo_recurrent signature lists no `rollout_buffer_class`; the examples-page quote is there, and its example (4 envs, `gradient_steps=2`) supports W1; the PettingZoo quote is there, with no version and nothing on varying agent counts.

## Not verifiable

- Character-exact docs quotes.
- Every "fits", "needs" and build route: read, not executed.
- The W3 gradient and the W4 attribute swap: read, not run.
