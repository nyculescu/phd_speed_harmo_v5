## Angle: path 3, multi-agent algorithm families

### Findings (measured, with file and number)

Scripts: `/home/catalin/work/phd/v5b1_runs/sar3c/tmp/p3a_*.py`. Trace numbers come from an older policy (phase 3 shot C1) on 2 seeds, 1,046-1,069 decisions, so they are indicative only.

1. **Population.** The median number of ALKS on the road at once is 152-155 at 4,090 veh/h, 175-180 at 4,600 and 219-231 at 5,300. It is 273 in the X1 trace. Each update has about 76,000 decisions (`train/C*_episodes.jsonl` alks_s/steps; `C*_updates.jsonl` n; `drl_trace_X1.json`).
2. **The action has no effect about half the time.** The gate is open in 0.48-0.52 of ALKS-seconds, at updates 0-49 and 450-499 alike, so training did not change it (`C*_episodes.jsonl`, sum of `lv` / `alks_s`).
3. **The actor can see the gate.** P(gate on | leader-is-ALKS input = 1) is 0.99; with the input at 0 it is 0.00 (traces).
4. **Gated decisions still carry advantage.** When the gate stays closed for the whole next 10 s, the median absolute advantage is 1.64 (608 decisions). When it stays open it is 2.32 (365 decisions). Decisions whose action does nothing for 10 s thus carry about 70 % of the advantage size of decisions that act (traces, `adv`). *Inference:* most of that is noise in the policy gradient. The level is stored, so it has some delayed effect.
5. **The final baseline-v3 policies stay near random when gated.** On the trace inputs, entropy is 1.09-1.24 gated against 0.64-0.75 open (uniform is 1.386), and the median top probability is 0.42-0.52 gated. Evaluation uses the argmax (`b_train.py:116-117`, `Greedy`), so the gated choice rests on small differences between logits.
6. **Churn.** At updates 450-499 an ALKS changes level 0.33-0.45 times per 10 s, against 0.44-0.50 at updates 0-49. 50-58 % of changes reverse the previous one (`changes`, `reversals`).
7. **What makes the reward vary.** The shared part has about the mean size of the per-vehicle part (0.42 against 0.40), but it explains only 11 % of the per-decision reward variance (0.075 of 0.71). The safety term explains 76 % of the per-vehicle variance, and only 9 % of decisions have any safety flag in their 10 s. The follower part has variance 0.076 (traces, rebuilt from `sec` rows). *Inference:* the main credit problem is not a shared team reward. It is sparse individual safety spikes plus decisions with no effect.
8. **Compute.** The 5 learners ran in parallel: final checkpoints at 15:09-15:10, 3.3 h wall for all five on 15 workers.

### How the families fit, ranked

| Rank | Family | SAR it needs | Measured problem it addresses | Fit |
|---|---|---|---|---|
| 1 | Shared-parameter value-based (Double + Dueling DQN, n-step) | Same S and A; per-agent reward; greedy policy | 4, 5, 7 (replay reuses rare safety events; dueling A head can go to 0 when gated); evaluation is argmax anyway | good |
| 2 | Counterfactual per-agent Q baseline in PPO (COMA-style) | Critic Q(o_i, g, a_i), 4 outputs; S, A, R unchanged | 4, 5 | good, cheapest |
| 3 | Mean-field (MF-Q/MF-AC) | Adds the neighbours' mean level (the 200-m bin, or leader and follower levels) to the critic, and to the actor in MF-Q | follower term (7), others' changing policies | weak evidence |
| 4 | SAC-discrete | As 1 plus a temperature | as 1 | as 1, with more knobs [VERIFY stability reports] |
| 5 | VDN / QMIX | One team reward; QMIX needs a fixed agent set (pad to about 300) and a global-state mixer | the shared term, only 11 % of variance | poor |
| 6 | Independent learners (no sharing, or per-zone nets) | Local critic | none; it splits the data | poor |

Current parameter-shared PPO with a centralised critic is the reference.

### Options

**A. COMA-style counterfactual advantage in the current PPO**
- *Problem:* findings 4-5. The state-value baseline cannot tell an action with no effect from one that acts, so gated decisions feed noise into the gradient.
- *Change:* only the algorithm.
  - Critic head becomes 4 outputs Q(o, g, a) (`c_train.py:45`, `:65-66`).
  - Train Q on TD(λ) targets for the taken action (`collect` `:198-210`, `update` `:230`).
  - The advantage becomes Q(a) minus the sum over a' of π(a')Q(a'), in place of GAE (`:201`, `:226`).
  - S, A and R are unchanged. The family is from Foerster et al. [VERIFY].
- *Cost:* build about half a day. Compute: smoke 0.2 h; 5 learners × 500 updates 3.3 h wall (16.5 learner-hours); evaluation 0.3 h. Total about 3.8 h.
- *Risk:*
  - One level step per 10 s changes little, so the Q differences may sit below the critic's error. Advantages would then be near 0 everywhere and nothing is learned.
  - Q is trained only on taken actions.
  - Benchmark reports put COMA below MAPPO [VERIFY].
- *Simplest test:* see "Shared test" below.
- *Pre-registered diagnostic:* the spread of the counterfactual advantage in gated decisions is smaller than in open ones. If it is not, the mechanism did not work, whatever the outcome.

**B. Shared-parameter Double-Dueling DQN with n-step returns**
- *Problem:* findings 4, 5, 7 and the argmax evaluation. Its targets are greedy by construction, the A head can learn that actions do not matter when gated, and replay reuses the 9 % of decisions with safety events.
- *Change:* a new trainer beside `c_train.py`.
  - Reuse `_worker`, `_act` (ε-greedy) and the input normalisation `Net._scaled`/`observe` (frozen after the pilot so that replay stays consistent).
  - Replay of about 3 M transitions (tiny at 16 floats), a target net, n of about 5 decisions with γ 0.933, Huber loss.
  - S, A and R are unchanged; the centralised inputs are dropped (Q is local). Dueling, Double and n-step are known DQN variants [VERIFY].
- *Cost:* build 1-1.5 days. Compute: smoke 0.2 h; 2 pilot runs of 100 updates on training seeds for learning rate and ε, about 1.4 h (disclosed as tuning); 5 learners with the same environment-step budget, 3.5-5 h wall (my estimate: gradient steps go on the idle cores, not measured); evaluation 0.3 h. Total about 5.5-7 h.
- *Risk:*
  - Replay holds transitions shaped by older policies of 150-270 neighbours, so the data the Q-learner sees keeps shifting [VERIFY: IQL replay literature].
  - The -10 safety spikes can cause overestimation or divergence.
  - The algorithm needs more tuning than PPO.
  - The rate limit plus ε-greedy explores slowly.
- *Simplest test:* see "Shared test" below.

**C. Mean-field critic (neighbour levels as critic input)**
- *Change:* add the leader's level, the follower's level and the bin's mean level to the critic's global input (`b_env.py:885`, `CAV_GLOBAL`) [VERIFY Yang et al.].
- *Problem:* only the follower part (variance 0.076), so the evidence is weak.
- *Cost:* about 3.8 h, as A. *Risk:* a small effect, buried in seed noise.

**Shared test (A and B), against baseline-v3 on fresh seeds**
- *Cell and seeds:* X2 at 5,300 veh/h, where confirmatory 3b failed, on 20 fresh, author-approved seeds.
- *Arms:* the 5 new learners, baseline-v3 d0-d4, os1_15_10, p333, and no control for context. About 260 runs, 0.3 h.
- *Statistic:* the protocol's median of paired differences with a 95 % bootstrap CI, per policy, against os1_15_10, on the bar: at least 10 % fewer close-following seconds with delay at most 2 % more. Plus a head-to-head: per seed, the median of the 5 new learners against the median of d0-d4.
- *KILL:* the new family passes the bar in fewer than 3 of 5 learners, **or** in the head-to-head neither close-following nor delay has a CI clear of 0 in the new family's favour.

### Recommendation

**Screen A first, then B. Run C only if A shows that inter-agent terms matter.**

**Pros:**
- A changes about 40 lines of a trainer that is already checked, and keeps S, A, R, the evaluation and the budget. Any difference is therefore down to the advantage estimator.
- Its pre-registered diagnostic shows whether the mechanism worked, whatever the outcome.
- B is the only family here that is genuinely different and also matches findings 5 and 7. Its argmax targets fit how the policies are judged.

**Cons:**
- Neither family touches the reason confirmatory 3b failed: delay, with no delay term in the reward. Algorithm changes cannot fix an objective mismatch, which is path 1's lever. A null result may therefore reflect the reward, not the family.
- B needs pilot tuning, which is a confound to disclose.

**Inferior alternatives:**
- **VDN/QMIX:** they solve team-reward credit, but the shared part is 11 % of variance. QMIX also needs a fixed agent set, while the population is 150-270 and changes all the time.
- **Independent learners:** they address no measured problem and split 76,000 decisions per update across networks.
- **SAC-discrete:** same targets as B, plus a temperature to tune for 4 actions.
- **Mean-field first:** its target term is the smallest measured one.

Overlap, in one line: dropping gated decisions from the loss, or not asking gated cars to decide, is a SAR change (paths 1 and 2), and is a cheaper rival to A.

### Open questions for the author

1. Should the family screen wait for path 1's reward fix, so that a null result is not caused by the missing delay term?
2. Is a disclosed 1.4 h pilot for tuning B acceptable on training seeds, or must B run on untuned standard settings?
3. One fresh 20-seed block for both A and B, or a separate block for each?
