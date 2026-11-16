## Angle: path 3, families that use prior knowledge or a different control level

### Findings (measured, with file and number)

"Fewer"/"less" means better than os1_15_10. Scripts: `sar3c/tmp/p3b_*.py`.

1. **Where the actions differ** (`lv` = level-seconds with the gate open, X2, `conf3_eval_primary` and `conf3b_eval_x2`). In the merge zone the rule holds 0.8 s 96-97 % of the time; DRL 74-83 %, with 1.0 s 10-20 %. Downstream the rule holds 0.8 s 71-80 % and 1.2 s 14-21 %; d3 and d4 hold 1.6 s 17-23 %. Upstream: rule 81 % at 0.8 s, DRL 70-77 %.
2. **Where the outcomes differ** (fresh seeds, `conf3b_eval_x2`, median paired difference). TTC: 258-470 fewer seconds against the rule's 1,845. Most of it is in the high-speed band (145-209 fewer of 600) and on road 3 (124-232 fewer of 478). Delay:
   - all-vehicle: 3,332-21,041 more vehicle-seconds against 206,897;
   - finishers: 2.7-8.2 s more against 95 s;
   - ramp 1: 3.2-12 s more against 113.5 s.

   On the original seeds both delays were less or equal.
3. **Noise.** Pooled over 40 seeds (both blocks), DRL all-vehicle delay ranges from 2.8 % less to 3.1 % more, every 95 % CI including 0, with 15-27 % fewer TTC. The per-seed SD of the paired delay difference is 9.3-11.1 % for DRL, 9.6-10.0 % for other rules, and 6.6 % for p333, which acts most like os1_15_10. Rule against rule, os1_10_0 swings from 3.9 % less delay (original seeds) to 7.0 % more (fresh), as large as DRL's swing. *Inference:* at 20 seeds the 2 % margin is at the noise floor, and a candidate closer to the rule should have a smaller spread (one data point).
4. **The rule needs no new inputs.** `OwnState` (`b_env.py:1007-1017`) reads the actor's own inputs [0], [4] and [15]. So imitation and residual control need no new sensors.
5. **The rule grid is coarse** (`conf3_tune`, X2, tuning seeds, 70 rules). Its Pareto front against os1_15_10 reaches 15-17 % fewer TTC at 2-3 % more delay (u2, a4400_10_1). os1_15_0 and os1_10_0 have 10-11 % fewer TTC within 2 % delay. Medians of paired differences are not transitive, so this does not contradict the selection.
6. **Earlier tries here (old plant m32):**
   - A residual around a static per-zone p303 base (`explore_v0/round1_screen.csv`, V317, 100 updates). At 4,600: 31 % fewer TTC, delay CI includes 0. At 5,300: 9.6 % more TTC, 1 collision.
   - A zone-level PPO agent (V279, V285) did not beat the fixed arms.
7. **Training:** it starts near uniform, with entropy 1.373 at update 0 against 1.386 (`C0_updates.jsonl`). The gate is open in 50-52 % of ALKS-seconds (`C*_episodes.jsonl`).

### Options

**A. Residual PPO on os1_15_10**
- *Problem it targets:* DRL wins TTC but its delay drifts by about 10 % per seed (3). The rule already has the delay (2).
- *Change:*
  - **Action:** an offset of -1, 0 or +1 level around the rule's level for that vehicle. At `b_env.py:656-657`, replace the static `self.residual[self._zone(v)]` with the `OwnState(1, 15, crowd=10)` level from the vehicle's `_obs` row (`:839`).
  - **State:** the 16 inputs plus the rule's level (`cav_sizes`, `:612`).
  - **Algorithm:** in `c_train.py` `Net` (`:41-52`), zero the output weights and bias so that P(offset 0) ≈ 0.9: it starts as the rule.
  - **Reward:** unchanged, to isolate the algorithm.
- *Cost:* build is small (the hook exists). Compute: smoke 0.1 h; 5 learners × 500 updates, 3.3 h; evaluation of 960 episodes, about 0.75 h (conf3b ran 360 episodes in 16 min). About **4.2 h**.
- *Risk:* the unchanged reward may teach the same deviations and delay cost. From a 0.8 s base, ±1 cannot reach 1.2 or 1.6 s, which DRL uses 5-14 % of the time in the merge zone. A win is only as strong as os1_15_10 (5). The prior residual try was mixed (6).
- *Smoke (exact):* with the offset forced to 0, one seed must reproduce the stored os1_15_10 row.
- *Simplest test:*
  - Arms: R0-R4, d0-d4 (baseline-v3), os1_15_10, p333, no control.
  - Cells: X2 and X1 at 5,300, **40 fresh seeds** (because of 3).
  - Statistic: median paired difference against os1_15_10 with a 95 % bootstrap CI, on TTC seconds and all-vehicle delay. Also residual against baseline-v3 delay, paired by seed and pooled over learners.
  - **KILL** if, in X2, fewer than 4 of 5 R have at least 10 % fewer TTC (CI excluding 0) with delay at most 2 % more. Also KILL if residual delay is not less than baseline-v3's: then the prior adds nothing.

**B. Imitate os1_15_10, then fine-tune with PPO**
- *Problem it targets:* every learner starts from uniform (7); the reward is flat after about update 100, and learners differ (d2 is weakest in every cell).
- *Change:* state, action and reward unchanged. Fit the actor by cross-entropy to the rule's level on rule rollouts (labels from `OwnState`, 4), and pre-fit the critic on the same rollouts so the first updates do not wreck the policy. Optionally a decaying KL-to-rule term in `update` (`c_train.py:213`). Load it through `train(..., resume=)` (`:246`).
- *Cost:* rollouts of 30 episodes plus the fit, under 0.2 h; PPO 3.3 h; evaluation 0.75 h. About **4.3 h**.
- *Risk:* with the same reward and a free action set, PPO may drift back to the from-scratch optimum. Measure the share of decisions that agree with the rule at u0, u250 and u500.
- *Test:* arms BC-only, B0-B4, d0-d4, os1_15_10, no control; same cells, seeds and statistic. **KILL** if B and baseline-v3 tie (CIs of B against d include 0 on both measures): then the start does not matter and the reward decides (path 1).

**C. Supervisory zone agent that sets the rule's parameters**
- *Problem it targets:* credit assignment. The shared terms are about 40 % of the reward magnitude (handoff §3; my reading of `drl_trace_X1.json` is consistent), and the gate is closed half the time (7).
- *Change:* state = the critic's 10 road-wide inputs plus both accelerating-lane counts. Action = per zone, th in {10, 15, 20} m/s and hit level in {1.2, 1.0} s, every 60 s, on `ZoneEnv` (`b_env.py:456-591`). Reward = the increment of all-vehicle delay plus a weight × TTC seconds. Single-agent PPO.
- *Cost:* build is medium. Compute is not tested: 25 decisions per episode, so roughly 30 envs × 300 updates, about 4-6 h, plus 0.5 h of evaluation.
- *Risk:* the two zone-agent runs here failed (6). It is sample-poor. It moves from per-CAV control to roadside supervision. It is close to the lookup arm "I".
- *Test:* Z0-Z2, os1_15_10, d0-d4, no control; X2 and X1; 40 seeds. **KILL** if no learner has less delay than os1_15_10 without more TTC (CI).

**D. CMA-ES over a per-zone own-state rule (direct policy search)**
- *Problem it targets:* the grid has 70 points, and its front reaches 15-17 % fewer TTC (5). DRL's edge may partly be a weak grid.
- *Change:* about 12 parameters (per zone: speed threshold, crowd threshold, hit level, free level). The objective is the bar's own quantities: TTC seconds with a penalty above 1.02 × os1_15_10's all-vehicle delay. Common seeds within a generation, new tuning seeds every generation. Built as a loop around `plant_sweep.py`.
- *Variant:* ES over a 16-16-4 actor started from B. It uses the same machinery but its fitness is noisier.
- *Cost:* population 16 × 20 seeds = 320 episodes per generation, about 0.25 h. 15 generations take 3.7 h per cell, about **4-8 h**, on about 28 workers under the CPU guard.
- *Risk:* overfitting to the tuning seeds; a 10 % per-seed spread against 2 % margins. The result is a **tuned non-learning controller**: an opponent, not a learning-based candidate.
- *Test:* CMA-best (picked on tuning seeds), os1_15_10, d0-d4, no control; X2; 40 fresh seeds. Reading: if CMA-best is within 2 % delay and matches DRL's TTC (CI includes 0), DRL's edge over the rules is gone.

### Recommendation

**A, residual PPO on os1_15_10.**

- *Pros:* it starts at the rule's delay, with a bounded, readable deviation and (inferred) a smaller paired spread (3). The hook exists, compute equals baseline-v3, and baseline-v3 alongside attributes any change to the framing.
- *Cons:* the ±1 cap; the reward still teaches to the test; a win is relative to one rule chosen on 20 seeds.

**Inferior alternatives:**
- **B** shares A's start but can forget it under the same reward. It is a diagnostic, not a candidate.
- **C** repeats a family that failed twice here, with fewer samples.
- **D** strengthens the opponent rather than the learner. It is worth running *before* any claim, not instead of A.
- **ES over network weights:** at a 10 % per-seed spread it needs many episodes per step.
- **Model-based RL:** a vehicle's own headway barely changes its own speed (V289), so a learned model of 200-300 vehicles must resolve tiny effects, and the planner would exploit its errors.

Overlap (one line): path-1 reward options and path-2 PPO settings (learning-rate schedule, validation checkpoints) apply to A and B unchanged.

Literature, all [VERIFY]: residual policy learning (Silver et al. 2018; Johannink et al. 2019), demonstration-augmented PG (Rajeswaran et al. 2018), kickstarting (Schmitt et al. 2018), ES (Salimans et al. 2017), CMA-ES (Hansen and Ostermeier 2001).

### Open questions for the author

1. Use 40 fresh seeds per cell instead of 20, given the 9-11 % per-seed spread of the delay difference? Which range?
2. Run D first as an opponent upgrade, since a residual win over os1_15_10 is only as strong as os1_15_10?
3. Should the residual offset be ±1, which cannot reach 1.6 s from a 0.8 s base, or ±2?
