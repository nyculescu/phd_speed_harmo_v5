# Handoff 2026-11-05: improve the state-action-reward, the DRL algorithm, and search for a better DRL algorithm

From the session that ran confirmatory 3 and 3b, the verification, the demand sweep and baseline v3, to the session `phd-speed-harmo-v5b1-3c`. Read this file first, then `docs/research/baseline_v3/BASELINE.md`. Repo `/srv/shared/Workspace/phd/phd_speed_harmo_v5b1`, branch `v5b1`, tag `baseline-v3` at `c6ab487`. Nothing in this thread has been pushed.

## 1. The author's request (verbatim, 2026-11-05)

> You have lots of measurements right now and a good idea on different paths we can take.
> 1. I want you to find a way to improve the state-action-reward (SAR)
> 2. I want you to find a way to improve the actual DRL algorithm including adjusting the SAR.
> 3. I want you to find a way to search for a better DRL algorithm including framing a SAR.
> This will be performed from the other started chat by you passing to it the full and needed context.
>
> It can start 9 agents for this brainstorming work, with 3 per each path given.

**This is brainstorming and design.** Produce options with a recommendation for each path. Per V310 and the project's CLAUDE.md:
- no build, training or simulation launch without the author's explicit pick;
- protocols are written before any data;
- seed ranges are approved by the author before use.

The author has explicitly allowed **9 agents, 3 per path**, for this work.

## 2. Where things stand

| Item | State |
|---|---|
| Plant | `docs/research/conf3/plant_c3.json` on r2m3: three lanes, two on-ramps 1.2 km apart, 50 % automated vehicles (ALKS), uncalibrated SUMO 1.27.1, ideal V2V and roadside speeds. P0d (baseline v2) plus `tau_rise` 0.2, `taper_fast`, `fix_x` |
| Code that ran | `d2b2ecc`, frozen copy `/home/catalin/work/phd/v5b1_runs/b_train/code_d2b2ecc` |
| Policies | 5 per-CAV PPO learners, `docs/research/baseline_v3/policies/C0-C4_final.pt` |
| Pre-registered results | Confirmatory 3: X2 won at the minimum, 4 of 5 (V395); X1 not won. Confirmatory 3b: X2 not confirmed on fresh seeds, 1 of 5 (V401) |
| Verification | `docs/research/conf3/verification_rev4.md` (V396), replays (V398) |
| Exploratory | Demand sweep (V409); demand profiles (V410) |
| Reports | `docs/reports/2026-11-05_19-22/` (results), `docs/reports/2026-11-05_20-51/` (sweep) |
| Teaching pages | `docs/extracts/2026-11-05_09-18/`: handoff page and DRL course page. The course explains the current SAR and PPO, with the code |
| Ledger | `docs/decisions.md`, last row V411 |

### Results in one table: "fewer" and "less" mean DRL is better

| Against | Close-following (TTC below 3 s) | Delay |
|---|---|---|
| 0.8 s rule (p333), slowdowns at 5,300 | 29-45 % fewer, all 5 policies, both seed blocks | about the same |
| Best tuned rule (os1_15_10), X2 original seeds | 24-30 % fewer (4 of 5 clear) | within 2 % |
| Best tuned rule, X2 fresh seeds | 14-26 % fewer, all 5 | 1.6-10 % more: the failure point |
| No control, X1/X2 at 5,300 | about the same in X2, 31 % more in X1 | 18-28 % less |
| No control, demand sweep | fewer only near congestion onset, about 4,500-5,400 veh/h | always 15-39 % less |
| Rules, demand sweep | 10-49 % fewer at most levels, also above the training range | mostly within ±3 % |

**Profiles (V410):**
- step: DRL best;
- slow sine: better than the rules;
- fast sine: no difference from the rules;
- peak: worse than the rules on close-following.

The author has chased training with varying demand before and it was not worth it (V411); do not propose it as the main lever.

## 3. The current SAR and algorithm, with code locations (frozen `d2b2ecc`)

### State: actor 16 inputs (`CavEnv._obs`, `v5b/fleet/b_env.py:839`), critic 16 + 10 road-wide

| Index | Input |
|---|---|
| [0] | x / 1000, clipped -3.5 to 3.3 |
| [1] | x / 300, clipped to -1..1; centred on merge 1 only, at a limit in 93 % of decisions |
| [2] | on a ramp or an accelerating lane |
| [3] | lane / 3 |
| [4] | speed / limit |
| [5]-[7] | leader gap / 100, closing speed / 10, leader is ALKS (the V2V gate) |
| [8]-[9] | follower gap / 100, follower closing speed / 10 |
| [10] | level / 3 |
| [11] | hold left: always 0 at a decision, dead since V290 |
| [12] | 200-m bin speed / limit |
| [13] | merge-zone speed / limit (merge 1 only) |
| [14] | signed distance to the nearest accelerating-lane vehicle (counted itself until V389) |
| [15] | accelerating-lane count / 40 |

- **Normalisation:** a running mean and SD saved in the checkpoint, clipped at 5, with an input that never varied set to 0 (V388-V389). Before V388 the inputs were hand-scaled (V387).
- **Missing:** no time, no memory, no demand, no fine position for merge 2, no information beyond about 200 m ahead.
- **Critic extras:** zone speeds (3), zone counts (3), accelerating-lane count, insertion queue, time, smoothed flow.

### Action: `_apply` at `b_env.py:652`, `_v2v` at `:730`

- **Choice:** a target level among 1.6, 1.2, 1.0 and 0.8 s, chosen by each ALKS every 10 s. Decisions are staggered on a 5-s environment step.
- **Rate limit:** the level moves at most one step per 10 s (`hold`). Every ALKS starts at level 0 (1.6 s).
- **V2V gate:** the target acts only when the leader is an ALKS within 150 m with the same leader on 2 updates; otherwise the car holds 1.6 s. The gate is closed in about half of all ALKS-seconds, where the action has no effect.
- **Rise limit:** longer gaps grow at most 0.2 s per second (`tau_rise`, V377-V382).
- **Only tau is actuated:** no speed, lane or ramp control.
  - Earlier tries: a lane action (V309); a speed action that policies declined (V339); a speed-cap oracle with no headroom (V344).

### Reward per ALKS per second: `_net_stats` at `b_env.py:754`, `_shared` at `:534`

| Term | Formula |
|---|---|
| Own speed | 0.5 × (min(v/limit, 1) - 1) |
| Speed around | 0.5 × (min(bin v/limit, 1) - 1) |
| Flow | 0.4 × min((v/spacing)/0.6, 1.5); pays directly for short spacing, which teaches 0.8 s (V339) |
| Safety | -10 × (own TTC < 3 s + own braking ≥ 3 m/s² + 0.5 × (follower TTC + follower braking)), read once a second |
| Shared | (smoothed flow/demand - 1) + (mean speed/limit - 1) - (vehicles in system / no-control reference - 1); the same for all |
| Collision | -10 for all |
| Move | -0.01 per level change |

**Measured on the teaching trace:**
- the shared terms are 33-45 % of the mean magnitude;
- one vehicle among 200-300 hardly moves them;
- there is no explicit delay term; delay enters only through speed and vehicle count.

**The deciding metric is the same TTC count as the reward term**, so the policies are paid for the test ("teaching to the test", V377 and V396). They had more ALKS-follower conflicts than no control and fewer human-follower conflicts (V398).

### Algorithm: `v5b/fleet/c_train.py`

- **Architecture:** custom PPO with parameter sharing, one actor for all ALKS, centralised critic.
  - Actor MLP 16-64-64-4, tanh, 5,508 numbers.
  - Critic 26-64-64-1, 5,953 numbers.
- **Update settings:** GAE with γ 0.933 and λ 0.967 per 10-s decision (about a 150-s horizon); 10 epochs, minibatch 4,096, Adam at a constant 3e-4, clip 0.2, entropy 0.01, value weight 0.5, joint gradient clip 0.5. Advantages are normalised per minibatch.
- **Return scale:** fixed once at update 0; it came out at 2.8-4.0 across learners, so value-loss weights differ by learner.
- **Bootstrap:** a vehicle that leaves is cut off, and its last value bootstraps.
- **Budget:** 5 learners × 3 envs (one per demand level, 4,090, 4,600 and 5,300), 500 updates, final policies only. About 76,000 decisions per update, about 38 M per learner, 23-24 s per update, 3.3 h, CPU only 38 %.
- **Logs:** JSON lines plus `conf3/trainlog.json`; the next training logs only to TensorBoard (V394).

**Training diagnostics, median of 5 learners, updates 1-50 → 451-500:**

| Diagnostic | Change |
|---|---|
| Reward | -0.206 → -0.185, flat after about update 100 |
| Entropy | 0.91 → 0.68 (uniform is 1.386) |
| Explained variance | 0.60 → 0.57; overstated, since its target contains the critic's own values |
| KL | 0.0028 → 0.0021 |
| Clip fraction | 0.017 → 0.014 |
| Value loss, reward units | 2.1 → 1.6 |

The policies were still changing at update 500: update 250 against final differs by up to 32 % on TTC (V396). Learners differ; d2 is weakest in every cell.

## 4. Measurements available (all read-only)

Each path is relative to `docs/research/baseline_v3/rows/` (gzipped) unless stated; full copies are under `/home/catalin/work/phd/v5b1_runs/baseline_v3/`.

| File | What it is |
|---|---|
| `conf3_eval_primary.jsonl.gz` | X1, X2 at 5,300: 36 arms × 20 evaluation seeds. Every counter: TTC by road, speed band and period; severe conflicts; step braking; delay; ramp delays; flow; fuel; jerk; lane-end stops; undertakes; per-road level means; tau match |
| `conf3_eval_map*.jsonl.gz` | Map cells S, H1, H2 at 4,600 and 5,300; X1, X2 at 4,600 |
| `conf3_tune*.jsonl.gz` | 70 rules × 2 cells × 20 tuning seeds; no control; copy rule |
| `conf3_trace.jsonl.gz`, `conf3_u250.jsonl.gz` | Policy traces on tracing seeds; update-250 checkpoints |
| `conf3b_eval_x2.jsonl.gz` | Replication on fresh seeds |
| `phase3_scratch_rerun_base/long.jsonl.gz` | Replays with TTC on the 4a lanes and by follower and leader class; runs to 3,000 s |
| `sweep_sweep.jsonl.gz` | 16 random demand levels × S, X1, X2 × 9 arms × 4 seeds |
| `osc_osc.jsonl.gz` | 4 demand profiles × 9 arms × 10 seeds |
| `/home/catalin/work/phd/v5b1_runs/baseline_v3/conf3/train/` | C*_updates/episodes.jsonl per update, pilot statistics, checkpoints u50-u500 |
| `docs/extracts/2026-11-05_09-18/drl_trace_*.json`, `drl_lab.json` | Per-decision rows of an older P0 policy, reward terms, a reward lab |
| `docs/research/conf3/verification_rev4_digest.txt` | 15-agent verification: every finding and skeptic verdict |

## 5. Evidence-based weak points, as starting material

These are measured facts and Claude's readings, not decisions. Test them; do not assume them.

1. **Reward against the judged bar.** The bar was "at least 10 % fewer TTC seconds with delay at most 2 % worse than the best rule", and the policies failed it on delay on fresh seeds. The reward has no delay term, weights TTC at -10 per 1-Hz flag, and pays per-vehicle short spacing. A constraint formulation could match the bar: maximise safety subject to delay, for example Lagrangian PPO, or reward shaped on the bar's own quantities.
2. **Teaching to the test.** Reward and metric share the same 1-Hz TTC samples, the severe check is a sub-count of them, and lateral and merge conflicts are not measured.
3. **Credit assignment.** The shared terms are 33-45 % of the reward; the action has no effect in about half of the seconds (gate closed); 200-300 agents share one policy; the move charge is small.
4. **State gaps.**
   - Merge 2 has no fine position input, though the gain and the lane-end stops sit there.
   - There is no look-ahead beyond the 200-m bin, no memory or time, and one input is dead.
   - A simple rule using own speed, position and accelerating-lane count (os1_15_10) comes close.
5. **Action limits.** One knob only; the rate limit means 20 s from 1.6 to 0.8 s; every car starts at 1.6 s; action steps are staggered.
6. **Algorithm.**
   - Reward flat after update 100, while weights still move to update 500.
   - Constant learning rate, fixed return scale per learner, explained variance about 0.57.
   - Final policy only; no checkpoint selection on validation.
   - Small MLP with no attention to neighbours.
   - CPU idle at 38 % during training: more learners or environments per update are possible. But running other SUMO work beside training slowed it by 75 % (V392).
7. **Search space.** PPO with parameter sharing (close to MAPPO) is the only family tried on this line. Unexplored candidates, all [VERIFY] before citing:
   - value decomposition (QMIX/VDN) or counterfactual credit (COMA);
   - SAC-discrete or DQN-family methods;
   - residual RL on top of the best rule;
   - imitation of the tuned rules, then RL fine-tuning;
   - graph or attention policies;
   - recurrent policies for memory;
   - constrained RL (CPO, PPO-Lagrangian);
   - model-based RL;
   - evolutionary strategies.

## 6. Rules to keep (project CLAUDE.md applies; key points and memory)

- **Process:**
  - Discuss first; recommendation format (recommendation, pros and cons, inferior alternatives and why).
  - No build or launch without the author's pick (V310).
  - Protocols before data; fresh, author-approved seeds per round.
  - **Keep tests simple:** the simplest test first, no unrequested variants (V408).
- **Writing:**
  - Short replies; the author's tokens matter.
  - Visual results: HTML in a timestamped folder under `docs/reports/`.
  - Every number in words: "fewer" or "less" is better, "more" is worse. Never signed percentages (V403).
  - Mark literature not read in full [VERIFY]; never invent sources; no "first" or "novel".
  - Comments simple, no forced alignment; Markdown tables as `| a | b |`.
- **Ledger and git:**
  - Every author decision or result becomes a V row in `docs/decisions.md`. **This session (3c) owns the ledger from V412**; the earlier session stops writing to it.
  - Commits: one imperative line of at most 50 characters, no body, no Co-Authored-By, no AI mention. Never push unless asked.
- **Claims and terms:**
  - The thesis claim bar is the author's and Claude's, with no supervisor (V95, V402).
  - Say "per-CAV control", never "C". The plant m32 is called r1m3; r2m3 has 2 ramps.
- **Runs:**
  - Frozen `git archive` copy per run.
  - Own systemd user unit, launched through `/bin/bash` (exFAT drops the executable bit).
  - CPU guard `v5b.ops.watch`; the author allowed up to 95-100 % for single runs when asked.
  - Temp files on ext4.
  - Resource check before batches.
  - Smoke check in training mode after any change.
  - Traces must not change the run (`_x` writes `xlast`, V386).
  - Nothing runs beside synchronous training (V392).
- **Logging:** the next training uses TensorBoard only, float32 scalars, with the same checks via event files (V394).
- **Reading pitfalls (V396):**
  - period bins are absolute simulation time after a 300-s warm-up;
  - medians of map cells are not tests;
  - use the protocol's paired statistic;
  - say which reference the harm cells use;
  - fill the allowed sentence completely.
- **Boundaries:**
  - Never modify v6; read only v6 `docs/handoff/`; never open the v6 CF06 paths; never read v6's sumo-src (own clone in `phd_speed_harmo_v5b1_toolchain/sumo-src`).
  - Archive branches are read-only.
  - Never run `loud` or `unlock`, never touch `vsl-cooling`, no power-profile or system changes.
- **Effort:** per the phase table in CLAUDE.md, ask the author in one line to switch effort or ultracode before each phase.

## 7. Suggested deliverable

One options memo for the author, as an HTML report in `docs/reports/<timestamp>/`, with 3 sections, one per path:
- the measured problem each option addresses;
- the change to state, action, reward and algorithm;
- expected cost in compute hours;
- the risk;
- a recommendation, and how it would be tested against baseline v3 (tag `baseline-v3`) on fresh seeds.

Then wait for the author's pick.
