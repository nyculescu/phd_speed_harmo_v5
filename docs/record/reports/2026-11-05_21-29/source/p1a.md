## Angle: the reward against the judged bar, and teaching to the test (path 1, PPO unchanged)

"Fewer" and "less" mean DRL is better; "more" means worse. Paired statistic: `decide3.raw`. Scripts: `sar3c/tmp/p1a_*.py`.

### Findings (measured, with file and number)

1. **Position against the bar** (`rows/conf3b_eval_x2`; `conf3/decide3.py` `fails`/`limits`). On fresh seeds, against os1_15_10, d0-d4 have 14-26 % fewer TTC seconds (the bar needs 10) and 1.6-10.2 % more delay (the bar allows 2, on the median). d2 passes; d1 and d4 miss by under 1 point. That leaves 4-16 points of TTC margin and a 0-8 point delay gap. The rule's own delay median moved from 238,397 to 206,897 vehicle-seconds between the two 20-seed blocks.
2. **The judged delay is a sum over vehicle-seconds.** `all_delay = N - distance/REF_SPEED` (`plant_sweep.py:304`), and REF_SPEED = LIMIT = 100 km/h, so the delay is the sum of (1 - v/limit), with the insertion queue counted at v = 0. N and all_delay correlate at 0.975 over the conf3b rows.
   - The own-speed term (weight 0.5) is exactly the ALKS's own share. That makes 1 own TTC flag (10) equal to 20 own vehicle-seconds of delay.
   - The bar's rate is 10 % TTC against 2 % delay: 19-23 vehicle-seconds per TTC second at the os1_15_10 medians on tuning seeds (`conf3_tune`). The two rates match.
   - Delay of everyone else (human drivers, ramp and insertion queues) reaches an agent only through the shared count term, at 1/419.3 per vehicle-second (`env.json`). For the deciding agent, one TTC second weighs as much as about 4,200 vehicle-seconds of others' delay, about 200 times the bar's rate.
   - Summed over the 207-252 ALKS present (`drl_trace`), the fleet weight is close to the bar's rate. **The weights are right in total; the attribution fails.**
3. **Which terms move** (`drl_lab.json`: one seed, an older policy, fixed-level fleets; exploratory).
   - Comparing all ALKS at 0.8 s with all at 1.6 s, the shared terms carry 77 % (S) and 97 % (X1) of the reward difference.
   - The terms one ALKS controls directly (flow + safety) prefer 1.6 s, by 0.029 and 0.068 per ALKS-second.
   - Trace means: flow is the largest per-vehicle term, 0.25-0.27. Safety is -0.11, of which own TTC is only 22-25 %; braking read at 1 Hz is 37-41 % and the follower 37-39 %.
4. **No gaming of the sampling, but braking gains are weaker** (`conf3_eval_primary`, `conf3b`, against os1_15_10).
   - TTC sampled half a second later is within 2 points of the judged count.
   - TTC below 1.5 s is 31-51 % fewer and the severe (deceleration-based) count 21-45 % fewer.
   - Braking at step resolution: b3_step only 5-15 % fewer, and b45_step anywhere from 5 % more to 27 % fewer.
   - Against no control on fresh seeds, ALKS hard braking at step resolution is up to 23 % more. The reward reads acceleration once a second (`b_env.py:761`).
5. **Shorter gaps do not buy the missing delay** (`conf3b`).
   - Ramp-1 mean delay is 2.8-10.7 % more than os1_15_10 for all 5 policies, and 3.8-11.6 % more than p333.
   - p333 (0.8 s everywhere) has about the same total delay as os1_15_10, 0.6 % more.

### Options

**A. Attributed delay replaces the spacing payment**
- **Measured problem:** findings 2, 3 and 5.
- **Change (reward only):** in `CavEnv._net_stats` (`b_env.py:754-791`):
  - in the existing leader loop, when a vehicle's leader is an ALKS, add the vehicle's lost time `1 - min(v/LIMIT, 1)` to the leader's slot, the way follower TTC is added at `:777`;
  - charge each accelerating-lane vehicle's lost time to the nearest mainline ALKS alongside, within 50 m;
  - the reward becomes `-0.5 × (own + followers' + merging vehicles' lost time) - 10 × safety`, with `w_flow` = 0;
  - the weight 0.5 equals the own-speed weight, so it carries the bar's rate and is fixed before data;
  - state, action and PPO are unchanged.
- **Cost:**
  - build about half a day, with a unit test;
  - smoke check in training mode, 0.3 h;
  - 5 learners in parallel, 3.3 h wall clock (measured 11,770-11,830 s, `conf3/train/C*_updates.jsonl`);
  - evaluation about 1 h;
  - about 4.5 compute hours in total.
- **Risk:**
  - The attribution is not causal: queue delay made at a bottleneck is charged to whichever ALKS leads the platoon, which adds noise.
  - Pricing slow followers may shorten gaps and spend the TTC margin.
  - It partly double-counts the near-speed term.
- **Test:**
  - arms: new n0-n4, v3 d0-d4, os1_15_10, p333, no control;
  - cells: X2 and X1 at 5,300, on 20 fresh, author-approved seeds;
  - statistic: the bar via `decide3.fails(margin 10)`, plus each learner's paired delay against os1_15_10;
  - **KILL** if fewer than 4 of 5 learners clear the bar in X2, or if the learners' median delay against the rule is not at least 2 points less than v3's on the same seeds.

**B. A graded safety signal at step resolution, so the judged count leaves the reward**
- **Measured problem:** finding 4 (braking hidden between the 1-Hz samples, as in V367) and the "paid for the test" critique.
- **Change:** in `_second()` (`b_env.py:397-404`), accumulate at every step, per ALKS and its follower:
  - dt × [braking ≥ 3 m/s²];
  - dt × max(0, 1/TTC - 1/3 s), a time-integrated inverse-TTC measure [VERIFY].

  These replace the 1-Hz flags at `:791`. Set the weight so that the mean penalty matches today's on the training-block pilot.
- **Cost:** build half a day. Extra leader queries may slow training by about 1.2-1.5 times (not measured), so about 5-6 h in total.
- **Risk:** it punishes close gaps harder, so gaps get longer and delay grows, which is the failing side of the bar. The TTC win may also shrink.
- **Test:** the same arms and cells. **KILL** if 2 or more learners fall below 10 % fewer TTC, or if step-resolution ALKS hard braking is not fewer than v3's.

**C. Spacing payment only at the bottlenecks**
- **Measured problem:** findings 3 and 5.
- **Change:** multiply the flow term (`b_env.py:790`) by a mask: the merge-1 zone up to `RAMP_ZONE_END`, and the 4a lane-end stretch before merge 2.
- **Cost:** build 1-2 h; about 4.5 compute hours.
- **Risk:** it rests on the unmeasured assumption that spacing matters only at active bottlenecks. The zone edges are arbitrary.
- **Test and KILL:** as in A.

### Recommendation

**A.**
- **Pros:**
  - it attacks the side of the bar that failed;
  - it uses the bar's own quantity at the bar's own rate, with no tuning;
  - it is one reward change;
  - a round costs about 4.5 compute hours.
- **Cons:**
  - the attribution is a heuristic;
  - TTC stays the judged count, although finding 4 shows no gaming of the sampling.
- **Inferior alternatives:**
  - **B** loses: it fixes credibility but pushes delay the wrong way. It is better as the next round.
  - **C** loses: it rests on an untested assumption, and finding 5 suggests spacing is not the lever.
  - **Lowering the TTC weight from 10 to 5** loses: it spends the TTC margin on shorter gaps, and p333 shows short gaps carry no delay edge.
  - **Raising the shared count weight** loses: per-agent credit stays at about 1/250 and the noise grows.
  - **An end-of-episode bar score** loses: one sample per episode for about 250 agents.
  - Lagrangian PPO belongs to path 2, and difference rewards to the credit angle.

### Open questions for the author

1. Is it acceptable to put the judged delay's own decomposition into the reward, with TTC staying the judged count? Or should B join A?
2. Evaluate on 20 or 40 fresh seeds? The rule's delay median moved 13 % between the two blocks, and the X2 verdict flipped from 4 of 5 to 1 of 5.
3. Pre-register the weight 0.5, or tune it on tuning seeds at the cost of one more round?
