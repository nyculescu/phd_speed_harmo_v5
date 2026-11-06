## Angle: PPO optimisation and training diagnostics (path 2)

Scripts: `/home/catalin/work/phd/v5b1_runs/sar3c/tmp/p2a_*.py`. Learner Ck is policy dk. Overlap, in one line: the missing delay term and the dilution by shared terms belong to the SAR and credit-assignment angles.

### Findings (measured, with file and number)

1. **Learning ends by about update 30-100.** Source: `conf3/train/C*_updates.jsonl`.
   - Median reward: -0.228 at u0-9, -0.178 at u20-29, -0.167 at u250-499.
   - Slope over u100-499: -0.002 to +0.001 per 100 updates, every CI inside ±0.0085.
   - Per-update SD 0.069-0.081, lag-1 autocorrelation -0.13 to 0.16: white noise from 3 episodes. The curve cannot see a change of less than about 0.025 over 400 updates.
2. **Outcomes stay flat while behaviour drifts.** Source: `C*_episodes.jsonl`, slopes over u100-499.
   - Merge TTC, braking, vehicles in the system, arrivals: all 60 CIs include 0.
   - Level changes and share at 0.8 s: 23 of 30 slopes exclude 0, with directions that differ by learner.
3. **The weights random-walk at constant speed.** Source: `C*_u50…u500.pt`.
   - Actor step per 50 updates: 2.1-2.9 against a norm of about 12.3, not shrinking.
   - Straight distance over path length, u50→u500: 0.37 in all 5 learners. A random walk gives 0.33; a directed path gives 1.0.
4. **Greedy actions flip.**
   - Probe of 20,000 draws from each learner's input statistics: u500 agrees with u450 on 83-87 % and with u250 on 72-81 %.
   - On 1,069 recorded decisions (`drl_trace_X1/S.json`; older plant, off-distribution): 43-67 % and 32-71 %, with 14-29 % near-ties (top two probabilities within 0.1).
   - Source `conf3_u250.jsonl.gz`, 5 seeds: in 9 of 10 learner-cells the final policy had 10-34 % fewer TTC seconds than u250, and in 9 of 10, 2-12 % more delay. The late updates traded delay for TTC, the direction that failed the bar on fresh seeds. d2 in X2 was worse on both.
5. **The trust region never binds.**
   - KL 0.0018-0.0026 and clip fraction 1.2-1.5 % from u50 on, with 180 minibatch steps per update.
   - Constant learning rate 3e-4 and entropy weight 0.01 (`c_train.py:31`, `:266`). The step is set by the learning rate times the noise, not by the clip.
6. **Training samples; evaluation is greedy.**
   - Sampling at `:138`, `Greedy` at `:87-102`, final entropy 0.65 nats (uniform 1.39).
   - Probe share at 0.8 s: 0.64-0.73 when sampled, 0.74-0.82 when greedy. The critic never saw the joint behaviour that gets evaluated.
7. **The critic stops improving early, and its scale differs by learner.**
   - Explained variance 0.596 at u0-9 and 0.580 at u250-499.
   - The scale is fixed at u0 (`:280-281`) at 2.84-4.00.
   - The late return SD (value loss / (1 - EV) × scale²) is 1.8-2.05 for all learners, so the target SD runs from 0.51 (C2) to 0.67 (C3): value weight differs about 1.7-fold.
   - C2 has the largest scale and is the weakest in all 3 cells. The Spearman correlation of scale with the TTC ratio against os1_15_10 is 0.9, 0.3 and 0.6; with n = 5 that is suggestive only.
8. **The logs are blind.** No policy loss, no gradient norms before the joint clip (`:235`), no per-term reward means, no network-wide TTC, no greedy evaluation on fixed seeds.

**My inference, not measured:**
- After about update 50, the gradient is mostly advantage noise. With a constant learning rate the weights diffuse, and the final policy is a random draw from a plateau.
- Near-ties amplify that draw under greedy evaluation, which explains the d2 spread and the gap between u250 and the final policy.
- A larger learning rate, more epochs or more updates add diffusion, not progress.

### Options

**O1. Anneal, and give every learner the same critic unit.**
- Problem: findings 3-7.
- Change (SAR unchanged):
  - learning rate linear to 0 (`LambdaLR` at `:266`, stepped after `:282`);
  - entropy weight 0.01 to 0 over the second half (`:31`, `:232`);
  - a constant critic unit of 2.0 for all learners (from the measured late SD), replacing `:280-281`;
  - TensorBoard scalars for the policy loss, gradient norms and per-term reward means (V394).
- Cost: half a day to build; 3.3 h of compute plus 0.3 h of evaluation.
- Risk:
  - Annealing freezes the walk wherever it stands; the bar (delay) may not move.
  - With entropy at 0, the flow term may push every car to 0.8 s (V339).
- Test:
  - d0-d4 against a0-a4, with os1_15_10 and no control, in X2 and X1 at 5,300 on 20 fresh, approved seeds.
  - The protocol's per-policy median of paired differences against os1_15_10 (TTC and delay, bootstrap CIs), plus the learner spread.
  - KILL if a0-a4 pass in no more policy-cells than d0-d4 and the spread is not smaller.

**O2. Choose checkpoints on validation seeds, using existing checkpoints (no training).**
- Problem: finding 4. The final policy is not the best, and the drift went toward more delay.
- Change:
  - Evaluate u250 … u500 greedily (30 policies) in X2 at 5,300 on validation seeds.
  - For each learner, pick by the bar's rule: fewest TTC seconds with delay at most 2 % above os1_15_10.
  - One selection script; the runs use `b_train matrix` with `{"pt": FILE}`.
- Cost: about 1 worker-minute per run (inferred from V392: about 2,200 rows in 80 minutes at 24 workers). Validation 600 runs, about 0.3 h; test about 0.25 h.
- Risk:
  - Winner's curse on near-ties.
  - Overfitting X2. The rule must be pre-registered.
- Test:
  - d0-d4 against selected s0-s4, with os1_15_10 and no control, in X2 and X1 on fresh seeds, with the same statistic.
  - KILL if s0-s4 pass in no more policy-cells, or are not less delayed with TTC no worse.

**O3. A larger batch, on top of O1.**
- Problem: findings 1, 3 and 5.
- Change: `--n-envs 6` (check the level assignment around `:258`) and `BATCH` 8,192 (`:30`). I infer about half the gradient variance per step.
- Cost: an estimated 3.5-5 h. 35 processes on 32 threads, and V392 saw contention nearly double the update time, so time 5 updates first.
- Risk: it may cut the noise without raising a plateau that the SAR sets.
- Test: as O1.

**O4. 10 learners × 200 updates, with annealing.**
- Problem: finding 1.
- Change: two batches of 5, about 2.7 h; either select with O2 or report all 10.
- Risk: it may lose slow progress the noisy curve hides, and best-of-10 strengthens the winner's curse.
- Test: as O1.

### Recommendation

**O2 first, then O1 only if O2 shows the drift matters.**
- If selected checkpoints pass where the final ones failed, the limit is diffusion, and O1 fixes it at the baseline's compute.
- If no checkpoint beats the final one beyond noise, PPO tuning cannot move the bar, and the effort goes to the SAR and credit-assignment paths.

Pros: under 1 h of compute, no trainer build, it tests the measured trade of delay for TTC, and it yields the validation rule O1 needs. Cons: winner's curse, it needs fresh seeds, and it does not improve training itself.

Inferior alternatives:
- **A larger learning rate, more epochs or 1,000 updates:** the clip is idle and the curve flat, so these add diffusion.
- **PopArt or a running SD:** more code than one constant, for the same confound.
- **A lower λ:** the evidence is indirect, and it adds bias at an explained variance of 0.58.
- **O3 and O4:** only after O1 shows the plateau can move.

### Open questions for the author (at most 3)

1. Do you approve fresh validation and test seeds for O2? Should selection be on X2 only, or on X2 and X1?
2. CLAUDE.md says both "final policy only" and "checkpoints chosen on validation seeds only". May a checkpoint chosen on validation be the reported policy?
3. For O1: should the entropy weight go to 0 or keep a floor? And may training add greedy evaluations between updates? They lengthen the run, because nothing may run beside training (V392).
