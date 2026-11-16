## Angle: credit assignment (path 1, SAR only, PPO unchanged)

Scripts: `sar3c/tmp/p1b_credit*.py`. Data: the per-decision rows behind the teaching trace, `v5b1_runs/phase3/scratch/drl/t2_{S,X1}_policy.npy` and `.json` (30,344 and 37,099 full 10-s decisions), the fixed-level arms `t2_*_0/3.json`, and `drl_trace_*.json` (12 long trips per condition, with the gate flag every second). **Caveat:** an older greedy policy (phase-3 shot C1, hand-scaled inputs) on one seed. Its reward form and weights match baseline-v3 training (`C0_config.json`), so the numbers are indicative, not measurements of d0-d4.

### Findings (measured, with file and number)

1. **Shared terms: large in the mean, small in the per-decision variance, large in the advantage.**
   - Share of the summed mean magnitude, term by term (`drl_lab.json`): 32 % in S and 43 % in X1. Taken as the net shared part per decision (`.npy`): 22 % and 43 %.
   - Share of the per-decision reward variance: 1 % in S and 9 % in X1. The local terms carry 98 % and 84 %.
   - Share of the GAE advantage that is common to every vehicle deciding in the same second: 27 % of its variance in S and 51 % in X1. In X1 the advantage correlates at 0.66 with the discounted shared-reward sum. My reading: the shared terms persist from one decision to the next, so GAE adds them up, while the local noise partly averages out.
2. **One vehicle hardly moves the shared terms.** Putting every ALKS at 0.8 s instead of 1.6 s moves them by 0.21 per ALKS-second in S and 0.18 in X1, with 210-290 ALKS present (`t2_*_0/3.json`). Shared out linearly, that is about 0.001 per vehicle (my inference). Their per-decision SD is 0.07 in S and 0.23 in X1.
3. **The noise comes from the sparse safety flag.** The per-decision reward has an SD of 0.70 in S and 0.76 in X1. The safety term alone has an SD of 0.60 and 0.57, but it is non-zero in only 6.5 % and 6.7 % of decisions. Each flagged second costs 1.0 per decision.
   - The safety charge in flag-seconds (`t2_*_policy.json`): own braking 41 % and 37 %, follower terms 37 % and 38 %, own TTC 22 % and 24 %.
4. **The signal from one decision is small.** Within one vehicle, with the gate open at both decisions, the flow term rises by 0.034 after an up move and by 0.004 after a stay. The difference, about 0.03, is roughly 1/25 of the per-decision SD and 1/60 to 1/100 of the advantage SD (1.8 in S, 3.3 in X1).
   - The other terms are confounded by state: around-speed, which one car cannot move, also rises by 0.029 after up moves.
5. **The gate.** The leader-is-ALKS input [7] is off at 43 % of decisions in both conditions. It matches the per-second gate flag at 469 of 471 and 576 of 579 trip decisions.
   - In the trips, it stays closed for the whole 10-s window in 273 of 471 and 318 of 579 decisions; 92 % and 94 % of closed decisions are still closed at the next one.
   - With the gate closed at both decisions, the flow term changes by 0.001 to 0.003 whatever the move: no immediate effect.
   - Closed decisions move the level more often (30 %, 35 %) than open ones (21 %, 26 %).
   - All of them enter the PPO loss: `c_train.py:164-169` adds every due vehicle and `update()` (`:213-243`) has no mask. At about 76,000 decisions per update (`C*_updates.jsonl`), that is about 33,000 no-effect rows (applying the 43 %).
   - Caveat: a closed decision still sets `lvl` (`b_env.py:672`), which acts once the gate opens: deferred, not zero.
6. **The move charge** is 0.005 per moving decision, about 1/140 of the per-decision SD. Reversals are 34 % (S) and 44 % (X1) of level changes.
7. **Aliased actions:** 13-15 % of decisions asked for a level more than one step away and executed one step. The 4-way categorical has at most 3 distinct effects. (Overlap with the action angle.)

### Options

**O1. Gate mask: hold the level and drop no-effect decisions from the policy loss.**
- *Problem addressed:* findings 5 and 4. 43 % of the policy-gradient rows carry no immediate effect and add pure noise to the gradient of the 4 logits.
- *Change:*
  - `b_env.py:652` `_apply`: under a flag `gate_hold`, skip vehicles not in `self.on`, so the level holds.
  - `:881-889` `_obs`: return the gate flag per vehicle. `c_train.py:97`: `Greedy` unpacks `o[:4]`.
  - `:130-146` `_act` and `:155-210` `collect`: keep the flag per row.
  - `:213-243` `update`: average the policy and entropy terms over gate-open rows only, and normalise the advantage over them. The value loss and the GAE chain keep every row.
  - The reward is unchanged.
- *Cost:* build about 2-3 h plus a training-mode smoke (about 0.2 h). Training: 5 learners in parallel, about 3.3 h wall, as baseline v3 (each `C*_updates.jsonl` ends at 3.28 h). Evaluation: about 0.4 h on 32 workers (conf3b ran 360 runs in 16 min).
- *Risk:*
  - The deferred pre-setting of the level is lost, and the level at gate opening may be stale.
  - About 57 % of the policy samples are left per update.
  - It may not touch the delay failure, if that comes from the reward design rather than credit.
- *Simplest test:*
  - Arms: O1 learners e0-e4 (the net seeds of d0-d4), baseline-v3 d0-d4, os1_15_10, no control. Cells X2 and X1 at 5,300, 20 fresh approved seeds.
  - Statistic: the per-seed mean over the 5 learners, then the median of paired differences e − d with a 95 % percentile bootstrap CI, for close-following seconds and for delay. Also the conf3 bar against os1_15_10, k of 5.
  - Free check: with the same reward, the training curves and learner spread compare directly with baseline v3.
  - **KILL** if in X2 the e learners have neither fewer close-following seconds nor less delay than d (both CIs include zero), or more delay with a CI excluding zero.

**O2. Local credit: replace the shared terms with a direct-follower speed term.**
- *Problem addressed:* findings 1 and 2. 27-51 % of the advantage variance is common to all vehicles at once, driven by terms each car moves by about 0.001.
- *Change:*
  - `b_env.py:797-801`: the actor's reward drops `_shared` and keeps the collision cost. The critic keeps its globals as inputs.
  - In `_net_stats` (`:775-778`, where follower TTC and braking are already charged to an ALKS leader), add 0.5 × (min(v_follower/limit, 1) − 1) to the leader. Delay then enters through the car that the gap actually slows.
- *Cost:* as O1, about 4 h compute.
- *Risk:*
  - It removes the only system-delay signal (vehicles in system, including the insertion queues), where the policies failed: delay on fresh seeds.
  - A leader could game the follower term by tailgating.
  - It mixes credit with reward design.
- *Test:* the same arms and statistic as O1. **KILL** if delay is more than baseline v3 (CI excluding zero) in X2 or X1.

**O3. Follower charge only for human-driven followers.**
- *Problem addressed:* finding 3. Follower terms are 37-38 % of the safety charge, and an ALKS follower already pays its own TTC, so its leader is charged again for the follower's level. The class split per agent is not measured.
- *Change:* `b_env.py:775-778`: charge the follower's `ttc` and `hard` to the leader only if the follower is not in `self.alks_all`.
- *Cost:* as O1, plus about 0.5 h to measure the class split from a trace.
- *Risk:* the effect is hard to predict, and the component is smaller than O1's.
- *Test and KILL:* as O1, with ALKS-follower close-following seconds as an added read-out.

### Recommendation

**O1.**
- *Pros:*
  - It targets the largest clean measured no-effect fraction: 43 % of the rows, with no immediate effect confirmed.
  - The reward stays identical, so the test isolates credit, and the training curves compare with baseline v3 at no cost.
  - It is cheap (about 4 h compute), reversible, and adds no new gameable term.
- *Cons:*
  - The deferred level-setting is lost.
  - There are fewer effective policy samples.
  - The shared-term common mode (51 % of the advantage variance in X1) stays.
  - It may leave the delay failure unchanged.
- *Inferior alternatives:*
  - O2 changes what is optimised exactly where the policies failed (delay), so its result would not say whether credit matters. It is the second step if O1 shows that it does.
  - O3 targets a smaller, unmeasured component.
  - A larger move charge treats the chatter, not its cause.
  - A dense safety term would cut the main per-decision noise, but it overlaps the reward angle.
  - A relative down/stay/up action overlaps the action angle.

### Open questions for the author

1. In O1, while the gate is closed, should the level be **held** (my recommendation, the simplest) or **reset to 1.6 s**?
2. Which fresh training and evaluation seed ranges may this test use?
3. Should the primary read-out be O1 against baseline-v3 DRL (the credit question), or against os1_15_10 by the conf3 bar (the claim question)?
