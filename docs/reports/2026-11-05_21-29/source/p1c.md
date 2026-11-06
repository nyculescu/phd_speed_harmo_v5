## Angle: state and action design (path 1, PPO unchanged)

Sources I read myself:
- the 5 final checkpoints (`policies/C*_final.pt`), whose input statistics cover about 38 M training decisions each;
- 1,069 per-decision raw inputs from `docs/extracts/2026-11-05_09-18/drl_trace_{S,X1}.json` (24 trips), with the baseline-v3 actors run on them. Caveat: these states were collected under an older phase-3 policy on one used seed, and their [14] still counted itself (pre-V389). The state distribution is therefore approximate;
- `C*_episodes.jsonl`;
- X2 and X1 at 5,300 in `conf3_eval_primary` and `conf3b_eval_x2`: medians of paired differences against os1_15_10 over 20 seeds.

Scripts: `sar3c/tmp/p1c_*.py`.

### Findings (measured, with file and number)

1. **[11] is dead.** Its SD is 0 in all 5 checkpoints and normalisation zeroes it. Its first-layer weight norms are 1.03-1.21, about PyTorch's initial value (≈1.15), against 1.37-2.33 for the other inputs, so those weights never trained. Ablating or permuting it changes 0 % of decisions.
2. **Saturation.** [1] sits at ±1 in 93 % of trace decisions. [14] sits at ±1 in 80 %.
3. **What the policies use.** Measured as permutation importance, the share of argmax decisions that change, over the 5 learners:
   - most used: [12] bin speed 12-35 %, [4] own speed 13-30 %, [7] leader is ALKS 13-32 %, [10] level 12-26 %, [15] accelerating-lane count 12-26 %, [14] 10-25 %, [0] 17-23 %;
   - least used: [2] ramp 0 %, [9] 5-11 %, [8] 8-12 %;
   - on road 3 and 4a only, [12] reaches 49 % and [4] 45 %. [13], the merge-1 zone speed, still moves 4-16 % of decisions there.
   - My reading: an own-state rule (the rule's three inputs) enriched with bin speed and leader type.
4. **Where the policies leave the rule is merge 2.** On trace states, at least 3 of 5 learners choose a different level than os1_15_10:
   - in 87 % of decisions on road 3 and 89 % on 4a, against 25-30 % upstream and at merge 1;
   - always toward longer gaps: mean level 0.9-1.0, against 1.8-2.5 for the rule.

   Realised mean levels in the X2 evaluation rows:

   | Road | Policies | os1_15_10 |
   |---|---|---|
   | Road 3 | 1.69-2.22 | 2.47 |
   | 4a | 1.06-1.74 | 2.15 |
   | Ramp 2 | 0.12-0.62 | 1.46 |

   The close-following gains sit there:

   | Measure | X2, original seeds | X2, fresh seeds |
   |---|---|---|
   | Road-3 TTC seconds | 177-234 fewer | 124-232 fewer |
   | Merge-2 lane-end stops | 161-754 fewer | from 454 fewer to 106 more |
   | Delay | - | 2.7-8.2 s more per vehicle (rule about 95 s) |

   **Merge 2 is exactly where [1] is saturated.** [13] is a merge-1 zone speed only (`_zone`, `b_env.py:483`). [15] adds 3a_0 and 4a_0 together (`:851-852`). No input describes merge 2 itself.
5. **Look-ahead.** The 400-m look-ahead rule lr400_16_1 has fewer road-3 TTC seconds than os1_15_10: 321 fewer on the original seeds and 210 fewer on the fresh seeds. That is more than any policy on road 3. But it has more lane-end stops and more delay. The policy sees nothing beyond its own 200-m bin.
6. **Action aliasing.** The level moves at most one step toward `want` per decision (`b_env.py:665-672`). So from level 0, actions 1-3 make the same move; from level 3, actions 0-2 do.
   - On trace states, 24-34 % of probability sits on aliased actions.
   - Entropy is 0.91-1.03 over the 4 levels, but 0.56-0.62 over the 3 real moves.
   - Learner pairs agree on 45 % of raw argmax choices (median pair), but on 59 % of moves.
   - **The evaluation argmax (`c_train.py:101`) makes a different move than the most probable summed move in 9.5-24 % of decisions.** It is mostly "stay" where a move had more total probability (8-19 %).
7. **Chatter.** In the last 10 % of training episodes (sampled actions), the level changes at 37-42 % of decisions, and 52-57 % of those changes reverse the previous one. The older policy under argmax: 43 % and 63 %.
8. **Gate.** Open in 56-57 % of ALKS-seconds for every arm (`tau_on_n` / `lv_n`). Learners agree on 65 % of choices with an ALKS leader, against 36 % without one.
9. **Start level and rate limit are not shown to bind.**
   - The rule's road-1 mean level of 2.69 is its start ramp.
   - The policies choose longer gaps than the rule anyway, including on ramp 2.
   - The full swing takes 20 s against about 1.2 km of road 3.

### Options

**O1. Merge-2 position and context (state).**
- **Problem:** findings 1, 2 and 4.
- **Change** (`_obs`, `b_env.py:864-874`):
  - [11] becomes (x − x_m2)/300, clipped to ±1, with x_m2 = `_x_base()["4a"]` (≈1,489 m);
  - append [16]: mean speed / limit in the merge-2 zone (`ZonePattern.EDGES_FIX`, x ≈ 1,389-2,084 m);
  - append [17]: the `4a_0` count / 40;
  - `CAV_LOCAL` goes from 16 to 18 (`:56`).
- **Rules stay unchanged.** [0]-[10] and [12]-[15] keep their meaning, because the rules read the policy's own observation: `CavRule` reads [0], [2] and [3] (`:906`), and `OwnState` reads [0], [4] and [15] (`:1016`).
- **Cost:**
  - build about 30 lines, plus a smoke check in training mode (about 0.1 h);
  - one arm of 5 parallel learners takes 3.3 h wall (`C*_updates.jsonl`: 11,770-11,830 s);
  - evaluation of 360 runs took 16 min (`conf3b_status.txt`).
- **Risk:**
  - the policy may already infer merge 2 from [0] and [14], so the new inputs could add nothing;
  - it could learn longer gaps at 4a more precisely, so close-following improves while delay still fails.
- **Test** (see Recommendation).

**O2. Look-ahead speed (state).**
- **Problem:** finding 5, and finding 3 ([12] as a stand-in).
- **Change:** append the mean bin speed / limit over the next 400 m and over the next 1,000 m (1 when there is none). Port `LocalRule._ahead` with its r2m3 `NEXT` and `N_BINS` (`:930-948`) into `CavEnv`. `self.bins` is refreshed in `_net_stats` (`:783`); a training-mode smoke check must show that it is current at `_obs` time (V294).
- **Cost:** the same as O1.
- **Risk:**
  - the bins are lane-averaged and lag;
  - 1-km information may teach long upstream gaps for queues that clear, which means more delay. That was lr400_16_1's failure mode.

**O3. Three-move action (action).**
- **Problem:** findings 6 and 7.
- **Change:**
  - n_act goes from 4 to 3, with a ∈ {longer, keep, shorter} and want = clip(cur + a − 1, 0, 3) (level 0 is 1.6 s);
  - behind a flag in `_apply` (`:655`), with n_level = 3 (`:633`), modelled on the existing `residual` branch (`:656-657`);
  - rules keep absolute targets (flag off); `Net(n_act=3)`.
- **Same reachable behaviour.** The rate limit already allows only one step per decision. What changes is that probability, entropy and argmax are no longer split across actions that do the same thing.
- **Cost:** the same compute, and about 10 lines.
- **Risk:**
  - the same expressivity, so the outcome may not change;
  - the entropy bonus now falls on real moves, so training chatter may rise, and the 0.01 move charge may then need revisiting (reward angle).

**O4. Decide only while the gate is open (action timing).**
- **Problem:** finding 8.
- **Change:** skip the decision and its transition while `v not in self.on`.
- **Risk:** a stale level applies the moment the gate opens.
- This is mostly credit assignment. It overlaps the credit-assignment angle, and I do not develop it here.

### Recommendation

**Recommendation: one arm, O1 + O3.** Both correct measured defects (an information gap at merge 2, and actions that alias); neither is a tuning variant. Keep O2 for a second round.

**Simplest test:**
- **arms:** new learners n0-n4; baseline-v3 d0-d4 re-evaluated on the same seeds; os1_15_10, p333, nc;
- **cells:** X2 and X1 at 5,300, 20 fresh author-approved evaluation seeds, plus fresh training seeds;
- **statistic:** per learner, the confirmatory-3 bar against os1_15_10, as a paired median difference: at least 10 % fewer TTC-below-3-s seconds with the CI excluding 0, and delay at most 2 % more;
- **mechanism check:** road-3 and 4a TTC seconds and merge-2 lane-end stops, plus the permutation importance of [11], [16] and [17] in the new checkpoints;
- **KILL** if any of these holds:
  - in X2, no more new learners than baseline-v3 learners pass the bar on the same seeds;
  - the new learners' median delay difference against os1_15_10 is not smaller than baseline-v3's;
  - the new inputs show about 0 importance.
- **Cost:** about 3.6 h of compute (3.3 h training + 0.3 h evaluation).

**Pros:**
- one training aimed at the cell that failed (merge 2 on fresh seeds);
- the opponents are unchanged;
- O3 also removes an evaluation artefact (finding 6) that affects how any result is read.

**Cons:**
- if it wins, the gain cannot be split between O1 and O3 without 2 more arms (6.6 h);
- the trace states come from an older policy.

**Inferior alternatives:**
- **O1 or O3 alone:** twice the arms for an attribution that only matters after a win.
- **O2 now:** the only evidence for it is a rule that bought road-3 safety with more delay, which is the failure being fixed.
- **Changing the start level or the rate limit:** not shown to bind (finding 9).
- **Speed or lane actions:** already declined or without headroom (V309, V339, V344).
- **Re-laying out all inputs (dropping [2]):** it would change what the rules read, and so the opponents.
- Memory and recurrent policies belong to paths 2 and 3.

### Open questions for the author

1. Is appending inputs acceptable, or do you want a clean input layout (which would require re-checking rule inputs and opponents)?
2. One combined arm (O1 + O3), or separate arms for attribution (3.3 h more each)?
3. Which fresh training and evaluation seed ranges do you approve?
