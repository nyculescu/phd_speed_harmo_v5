## Angle: network architecture, critic and compute use (path 2)

### Findings (measured, with file and number)

Sources: `baseline_v3/conf3/train/C*_updates.jsonl`, `C*_episodes.jsonl` (scripts `sar3c/tmp/p2c_time.py`, `p2c_gate.py`), frozen code at d2b2ecc, `lscpu`, V392. One micro-benchmark (`p2c_bench.py`): a copy of `update()` and `gae()` on random tensors of the logged size, idle machine; nothing trained or saved.

1. **Time goes to the environment, not the network.** An update takes a median 23.1-23.2 s in all 5 learners, for about 76,000 decisions. The PPO update on those rows takes 0.92 s (about 4 %); GAE 0.02 s; an episode's forward passes 0.16 s. So about 95 % is collection (SUMO plus the per-second Python loops in `_net_stats`, `_v2v`, `_obs`); I did not measure that split.
2. **The 38 % CPU comes from the process count.** 5 × (3 SUMO workers + 1 master) = 20 processes on 32 threads (24 cores). Environments run in lockstep: vehicle-seconds per episode are 405k, 471k, 590k at 4,090/4,600/5,300, so the lighter two wait about 17 %. 15 × 0.83 × 0.96 ≈ 12 busy threads matches 38 % (my inference).
3. **Idle threads are not free capacity:** 16 extra SUMO workers took training from 23.5 to 40-45 s per update, even at nice 19 (V392).
4. **The critic does not improve.** Explained variance is 0.56-0.64 in updates 1-50 and 0.56-0.62 in 451-500, and falls in C0 and C4. It is overstated (the target contains its own values). No per-decision data of the conf3 policies exist: `conf3_trace` rows are per-run aggregates, and `drl_trace_*.json` holds 12 hand-picked trips of an older policy. **So nobody can tell yet whether the critic lacks capacity, information, or faces noise it cannot reduce.**
5. **The per-update signal is noisy and flat.** The mean reward per update has an SD of 0.075-0.082 around a 25-update moving mean. The change from updates 1-50 to 451-500 ranges from a 0.010 loss (C1) to a 0.078 gain (C0), and the last 100 updates have a slope near 0. KL is 0.0018-0.0022 and the clip fraction 0.013-0.015: the clip almost never binds.
6. **The learned function is simple, and inert half the time.** The gate is open in 0.50 of ALKS-seconds in every learner. Late in training, 0.8 s is held in 0.78-0.81 of gate-open seconds, under sampling. 51-57 % of level changes are reversals.

### Options

**O1. Critic diagnosis offline, then a richer critic only if the data justify one (actor unchanged).**
- *Problem:* finding 4, an unexplained critic ceiling of about 0.6, plus the credit noise from finding 6.
- *Change, step 1 (diagnosis):* add an opt-in dump to `collect` (`c_train.py:198-210`) that saves `lo`, `gl`, the rewards and the vehicle id per decision. Add read-only neighbour features in `_obs` (`b_env.py:855-874`, `getNeighbors`/`getLeader`, which write no state; check that the counters match an untraced run, V386). Fit 4 critics offline on Monte Carlo returns to exit (γ 0.933), on held-out episodes:
  - the current inputs at 64-64 (the reference);
  - the same inputs at 256-256 (capacity);
  - plus the vehicle's previous decision's inputs and action (a memory proxy);
  - plus the k = 6 nearest vehicles (information).

  The null is the same fit with neighbour rows shuffled across time.
- *Change, step 2:* only if step 1 passes, widen or extend `Net.critic` (`c_train.py:45, 65-66`) and carry the extra array through `_act` (`:132-139`), `collect` and `update` (`:214, 230`).
- *Cost:* step 1 is 3-4 h of build and under 0.3 compute h (30 episodes, 1-2 min; fits about 15 min). Step 2 is 3.3-3.8 h: a 256-unit critic adds about half of the measured 0.9 → 7.3 s, about 14 % more wall. Evaluation 0.2-0.4 h.
- *Risk:* a better return fit need not give a better policy. The exit-truncated target differs from training's, so only the four fits are compared with each other. A null does not prove that neighbours are useless to the actor.
- *Simplest test:*
  - Step 1 passes only if a feature set raises the held-out R² above the shuffled null's 95 % range across episode folds. Otherwise KILL critic work.
  - Step 2: arms n0-n4 (same net seeds) against d0-d4, with os1_15_10 and no control as references. X2 and X1 at 5,300, 20 fresh approved seeds, the protocol's median paired difference with a 95 % bootstrap. Count learners passing the conf3 bar against os1_15_10, and pair n_i with d_i on delay.
  - KILL if no more learners pass than baseline-v3's 1 of 5 on the same seeds, or if n_i's delay is not less than d_i's (CI spans 0).

**O2. More episodes per update (compute use).**
- *Problem:* findings 2, 3 and 5: about 3 episodes of signal per update, a noisy flat reward, and policies still moving at update 500 (update 250 differs from the final policy by up to 32 % on TTC, V396).
- *Change:* `train --n-envs 6`, two episodes per level (`c_train.py:256-263`). Optionally profile one episode (about 0.02 h) and trim the per-second loops (`b_env.py:730-792`), reproducing stored rows exactly.
- *Cost:* a 10-update timing smoke first (about 0.15 h). If speed degrades as in V392 (40-45 s per update), 500 updates take 5.6-6.3 h; equal samples (250 × 6) about 3 h.
- *Risk:* Adam's step hardly depends on batch size, so plateau drift may continue. Equal-sample and equal-update designs answer different questions. Gain unknown.
- *Test:* as O1 step 2 (m0-m4 against d0-d4); same KILL.

**O3. Attention policy over neighbouring vehicles (actor and critic).**
- *Problem, indirect only:* ALKS followers hold 58-66 % of close-following seconds, with more than under no control (V398). The gain and the lane-end stops sit at merge 2, where the actor sees only one accelerating-lane vehicle and a count.
- *Change:* `_obs` adds a padded set of k = 8 vehicles within 150 m (relative x, lane offset, speed difference, ALKS flag, level, gate). `Net` gets a shared encoder with one attention-pooling head (d = 32), joined to the 16 own inputs, then 64-64-4; masks in `Greedy`/`_act` (`c_train.py:96-102, 130-146`).
- *Cost:* 1.5-2 days of build. Compute 4-4.7 h (update likely 5-10 s on CPU, estimated from the 256-unit benchmark); evaluation 0.2-0.4 h.
- *Risk:* many more inputs on a plateau-limited problem (finding 5) can learn more slowly or overfit training seeds. Teaching to the test remains.
- *Test:* as O1 step 2; same KILL.

### Recommendation

**Not now for any new policy architecture. Do O1 step 1 first: one cheap dump, with four offline fits.** It answers capacity, memory and neighbour information at once, for under 0.3 compute h. Then train the richer critic only if a feature set beats its null. O3 waits for step 1 to show that neighbour features carry return information.

- **Pros:** architecture spend is tied to a measured gap; plant and actor are unchanged; the dump fills the per-decision data gap that every angle shares.
- **Cons:** a dump hook outside TensorBoard-only logging (V394); a pass still needs a 3.5 h train. The evidence (a simple learned function, a flat noisy reward, the update at 4 % of wall) points more to the signal (reward against the bar; path 1) and to step size or checkpoint choice (other path 2 angles) than to the network.

**Inferior alternatives:**
- **Per-agent counterfactual (COMA-style) Q-head:** one vehicle barely moves the shared terms, so their counterfactual is the term itself. The gate state is known exactly, so masking the closed-gate half beats a learned "all actions equal". An on-policy Q-head is harder to fit than V. (Overlap: credit-assignment angles.)
- **Recurrent (GRU) actor:** no measured memory failure (the failure is delay at constant demand on fresh seeds). The memory-sensitive profiles are exploratory with small counts (V410, V411). It needs sequence batching and hidden state in `collect`, `Greedy` and evaluation; O1's memory proxy tests the need first.
- **Wider actor MLP:** the actor learned "mostly 0.8 s"; 256 units take 7.3 s instead of 0.9 s per update (about 27 % more wall) for no shown gap.
- **GPU:** the update is about 4 % of wall; SUMO cannot move to it.
- **Idle CPU beside training:** measured to slow training by about 70 % (V392).

### Open questions for the author

1. Approve a throw-away seed range for O1's dump (30 training-mode episodes, under 0.05 compute h)?
2. Is a per-decision dump acceptable as an opt-in exception to TensorBoard-only logging (V394)?
3. If a new critic is trained, keep 5 learners × 3 envs exactly, so the comparison with baseline-v3 is direct?
