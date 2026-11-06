## Angle: constrained PPO that matches the judged bar (path 2)

### Findings (measured, with file and number)

Scripts: `sar3c/tmp/thr.py`, `u250.py`. My bootstrap used 5,000 resamples at 97.5 %; the protocol uses 20,000.

1. **What is judged** (`docs/research/protocols/confirmatory_3.md`, lines 90-104): the network count of TTC below 3 s, read once a second (`ttc_net`), and all-vehicle delay. `all_delay` is the vehicle-seconds in the system, insertion queue included, minus distance over 27.8 m/s (`plant_sweep.py:304`). Delay may be at most 2 % worse than every opponent that counts.
2. **Reference values**, medians of 20 seeds (`conf3_tune`, `conf3_eval_primary`, `conf3b_eval_x2`, `conf3_eval_map_x`). Each entry is TTC seconds / delay in vehicle-seconds:

| Cell | os1_15_10 | p333 | 5 policies |
|---|---|---|---|
| X1 5,300, tuning | 2,658 / 254,618 | 3,455 / 243,051 | not run |
| X2 5,300, tuning | 2,070 / 233,950 | 2,691 / 229,146 | not run |
| X1 5,300, evaluation | 2,686 / 244,794 | 3,346 / 235,760 | 1,768-2,080 / 229,090-245,277 |
| X2 5,300, evaluation | 1,996 / 238,397 | 2,516 / 238,734 | 1,446-1,772 / 220,164-234,051 |
| X2 5,300, fresh | 1,845 / 206,897 | 2,364 / 211,957 | 1,370-1,604 / 210,378-222,579 |
| X1 4,600 | not run | 549 / 119,678 | 376-574 / 117,879-120,848 |
| X2 4,600 | not run | 798 / 121,630 | 410-572 / 119,949-124,641 |

3. **The policies sit on the safe side of the trade-off.** Against the lowest-delay rule that counts, they have 14-46 % fewer TTC seconds, two to four times the 10 % bar, but their delay sits at the limit: 0.1-3.1 % more in X1 (against p333), 1.6-10.2 % more in fresh X2 (against os1_15_10).
4. **The 2 % delay limit sits at the noise floor.** The per-policy interval of the paired delay effect is 9-13 points wide at 20 seeds, a standard error of about 3 %. Between the two X2 seed blocks the same policies shifted by 5-13 points (d0: 2.8 % less to 10.2 % more). Pairing helps little on fresh seeds: paired spread 8.9-11.5 %, unpaired 10.8 %.
5. **Fixed weights keep trading delay for TTC late in training** (`conf3_u250`; exploratory, 5 seeds). Against its update-250 checkpoint, the final policy has fewer TTC seconds in 9 of 10 policy-cells (update 250 had up to 47 % more) and more delay in 8 of 10 (2-9 % more).
6. **Delay hardly moves in training, and training does not compute it** (`conf3/train/C*_episodes.jsonl`). Vehicles in the system per second at 5,300: 390-410 over updates 0-49, 393-398 over 450-499; episodes spread by 6 % SD. The logs hold `N` but no distance, so there is no `all_delay`. Training seeds are deterministic (`b_env.py:132`).
7. **The reward pays the judged sample itself:** the same once-a-second TTC-below-3-s flag (`b_env.py:772`, `:790-791`; w_safety 10). There is no delay term, and the flow term pays for short spacing.

### Options

**A. PPO-Lagrangian: safety in the reward, delay as the constraint**
- **Problem it addresses:** findings 3, 5, 6 and 7. Fixed weights put the trade-off point in the wrong place, and it keeps drifting.
- **Reward** (`_net_stats`, `b_env.py:754-792`): safety only.
  - A continuous inverse-TTC hinge, max(0, closing speed/gap − 0.25 s⁻¹), averaged over the ten 0.1-s steps: own plus half the follower's.
  - Hard braking, collisions and the move charge stay as they are. The once-a-second flag goes.
- **Cost, a new channel** (returned in `info` by `step`, `:891-896`): own delay rate (1 − v/limit) + 200-m bin delay rate + network delay rate, (n − Σv/27.8)/n_ref(q).
  - The speed terms leave the reward; the flow term is dropped.
  - `_second` (`:395-437`) also sums speeds, so that training computes `all_delay`.
- **Algorithm** (`c_train.py`): a cost critic head in `Net` (`:41-66`) on the same 26 inputs; cost GAE in `collect` (`:155-210`); in `update` (`:213-243`) the two advantages normalised separately and combined as (Â_r − λÂ_c)/(1 + λ), with both value losses summed.
- **Dual update** (`train`, `:246-300`): J = the mean over the 3 levels of episode `all_delay` / d_ref(q), over the last 20 updates (60 episodes); λ ← clip(λ + (J − 0.97), 0, 10), starting at 1 and frozen for 20 updates; λ and J go to TensorBoard and λ into the checkpoint. This is the plain PPO-Lagrangian family [VERIFY]; PID-Lagrangian [VERIFY] only if λ oscillates.
- **Threshold:** d_ref(q) = the median `all_delay` of the lower-delay of os1_15_10 and p333, on 30 reference seeds per training level, under the training slowdown distribution. The target is 3 % less than that.
  - Why 3 %: by finding 4, a policy whose true delay equals the rule's fails the 2 % limit about one time in four. This is my normal-approximation estimate.
- **Teaching to the test, avoided:** the reward never sees the judged once-a-second TTC sample; the threshold comes from training conditions and reference seeds, never from X1, X2 or evaluation seeds; the untrained counters (TTC below 1.5 and 2 s, `sev3`, 0.1-s braking) are reported beside it; delay is a primary metric, not a surrogate.
- **Cost** (my estimate, about 20 s per training episode): step 0 (630 episodes) under 30 min on 32 workers; training, 5 learners together, 3.3-3.6 h; evaluation about 0.5 h; about 4.5 h in total. Build: the cost channel, a critic head and the dual update, plus a smoke check in training mode.
- **Risks:** the per-vehicle cost is only a proxy for episode delay, so λ could reach its cap without moving `all_delay`; λ could oscillate on the 6 % episode noise; a constraint met under training slowdowns may not carry over to X2 (finding 4); falling back to 0.8 s everywhere would meet it but lose the TTC edge; the arm changes two things (the surrogate and the algorithm).
- **Test:**
  - **Step 0, a pre-registered stop:** run the baseline-v3 policies and both rules on the reference seeds. If 4 of 5 policies already have J ≤ 0.97, the constraint would not bind: do not train. The fresh-seed failure would then be a transfer problem, not a trade-off problem.
  - **Step 1:** fresh, author-approved seeds, X2 and X1 at 5,300, 20 seeds. Arms: 5 new policies, 5 baseline-v3 policies, os1_15_10, p333, the other opponents that counted, no control. Statistic: the protocol's median paired difference over the opponent's median, 97.5 % bootstrap; confirmatory 3's tuned reading unchanged.
  - **KILL** if fewer than 4 of 5 new policies pass in X2; or their paired delay is not less than baseline-v3's (interval includes 0); or λ sits at its cap for the last 100 updates in 3 of 5 learners.

**B. The reverse: delay in the reward, TTC as the constraint.** The reward is A's cost with its sign flipped; the constraint asks for 20 % fewer TTC seconds than the rule, since the TTC interval half-width is about 10 points (targets: about 1,476 against os1_15_10's 1,845 in fresh X2; about 2,677 against p333's 3,346 in X1). Cost and test as A. Risk: it constrains the surrogate itself, so the policy sits just under a TTC level; that caps the claim and is the closer form of teaching to the test.

**C. Fixed weights, no dual variable.** A's reward split with w_safety lowered from 10 to 5 and to 2.5: 2 trainings, run one after the other (V392), about 7.5 h. Risk: by finding 5, the end point drifts with training length.

**D. Constrained checkpoint selection, no training** (overlaps the checkpoint-selection angle). Per learner, the checkpoint (u50-u500) with the fewest TTC seconds among those with validation delay at most 0.97 × the rule's: 2,000 episodes, about 1.5 h, plus a 0.5 h test. Risk: by finding 5, earlier checkpoints have far more TTC seconds; 10 points per learner is coarse.

### Recommendation

**A, behind its step-0 stop.**
- **Pros:** it has the bar's form (maximise the claim quantity subject to the limit that binds); one adaptive scalar replaces the weight search; it spends the measured TTC slack (finding 3); the reward stops paying the judged sample; step 0 can stop it within about 30 min of compute.
- **Cons:** more code than C; the proxy-to-metric mismatch; no training change removes the 20-seed noise in finding 4.
- **Why the alternatives lose:** B constrains the surrogate and caps the claim, while the measured failure is delay. C costs twice the compute for an end point that drifts, and A automates that weight search. D changes no algorithm and selects coarsely; it is only a zero-training check.
- **Overlaps:** credit assignment for the network delay term; checkpoint selection (D).

### Open questions for the author (at most 3)

1. Is a 3 % delay margin under training conditions acceptable? And since the 2 % limit is smaller than the standard error of a 20-seed median (about 3 %), should evaluation use 40 seeds per cell?
2. Should the reference be the lower-delay of os1_15_10 and p333 at each training level, or os1_15_10 alone?
3. Should the safety surrogate change in the same arm as the algorithm (my pick), or should the once-a-second flag stay so that the algorithm's effect is isolated?
