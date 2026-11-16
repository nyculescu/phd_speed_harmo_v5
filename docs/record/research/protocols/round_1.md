# Round 1: three candidates against baseline-v3, by the search procedure 3A

Status: draft, revision 2, for the author's approval (V414, V416-V421). Revision 2 sets the training range to 4,500-6,000 veh/h from the demand sweep (V419, V420), adds a control arm and a band reading. Nothing runs before the author approves this text and the seed ranges below.

## Question

On the baseline-v3 plant, with policies trained over 4,500-6,000 veh/h:
1. At 5,300 veh/h under the X1 and X2 slowdowns, does any of three changes to per-CAV DRL give **less delay than baseline-v3's policies while keeping their edge in close-following** (TTC below 3 s, read once a second)? Does a winner pass confirmatory 3's tuned reading on fresh seeds?
2. Under the training slowdowns, do the policies have fewer close-following seconds than no control **at every level of the band 5,000-5,500**, and what happens at its edges, 4,500 and 6,000 (V418, V420)?
3. Is a gain due to the method or to the wider training range? A control arm, baseline-v3's recipe on the new range, answers this.

Why delay: baseline-v3 failed confirmatory 3b on delay, not on close-following (V401). Over 40 seeds pooled, its delay against os1_15_10 is a tie within noise (V413, exploratory).

## What stays fixed

- **Plant:** `docs/research/conf3/plant_c3.json` on r2m3, as in baseline-v3 (tag `baseline-v3`). No plant change.
- **Opponents:** baseline-v3's `opponents.json`, unchanged. No rule is re-tuned. "Counting" opponents are found per cell on this round's seeds, exactly as confirmatory 3 does: delay within 2 % of p333.
- **Incumbent:** baseline-v3's learners C0-C4, with their stored checkpoints u50-u500 and final.
- **Training budget and settings, for every candidate:**
  - 5 learners × 3 environments, 500 updates, as baseline-v3; the environments cycle through the 7 training levels 4,500, 4,750, …, 6,000 (each update covers 3 consecutive levels, each level 3 times per 7 updates), where baseline-v3 used one environment per level at 4,090, 4,600 and 5,300 (V420);
  - γ 0.933, λ 0.967, PPO settings of `c_train.py`, input normalisation as V388;
  - environment config as baseline-v3's `env.json` (hold 10 s, random slowdowns), except the reward references, computed at the 7 training levels in stage 0c, and what the candidate changes;
  - network seeds 20261205 + learner; the **same training seed streams for all candidates** (common random numbers).
- **Code:** baseline-v3 code (`d2b2ecc`) plus the round-1 changes. Every change sits behind an option whose default is the old behaviour. The run commit is frozen before stage 0.

## The candidates

| | Control arm (v3w) | 1A attributed delay | 2C PPO-Lagrangian | 3B residual on the rule |
|---|---|---|---|---|
| Option | none | `reward_mode: "attr"` | `reward_mode: "lagr"` + trainer `--lagr` | `base_rule: os1_15_10` |
| State | unchanged (16) | unchanged (16) | unchanged (16) | 16 + the rule's level |
| Action | unchanged (4 levels) | unchanged (4 levels) | unchanged (4 levels) | 3 offsets around the rule's level |
| Reward | unchanged | changed | safety only | unchanged |
| Algorithm | unchanged | unchanged | cost critic + dual variable | unchanged, initialised at the rule |

The control arm is baseline-v3's recipe trained on the new range with this round's seeds and references (V420). It takes part in validation like any candidate, and it is always tested, so each method can be compared with it.

### 1A. Attributed delay replaces the spacing payment

Per ALKS per second, `lost(v) = 1 - min(v / limit, 1)`. The per-vehicle reward becomes:

- the own term, as now: −0.5 × lost(own);
- plus −0.5 × the lost time of every vehicle whose leader (within 200 m, the same lookup that charges follower TTC) is this ALKS;
- plus −0.5 × the lost time of every accelerating-lane vehicle (3a_0, 4a_0) whose nearest mainline ALKS on the same edge, within 50 m along the lane, is this ALKS;
- minus 10 × safety, as now;
- no flow term (weight 0) and no speed-around term (weight 0).

The shared term and the collision charge are unchanged. The weight 0.5 equals the own-speed weight: one close-following flag costs as much as 20 vehicle-seconds of delay, the bar's own rate (V413, F4). It is fixed now, not tuned.

### 2C. PPO-Lagrangian: safety in the reward, delay as a constraint

- **Reward:** the per-vehicle safety charge as now (−10 × own TTC flag, own hard braking, half the follower's), the collision charge and the move charge. No speed, flow or shared terms.
- **Cost, per vehicle per second:** lost(own) + lost(its 200-m bin's mean speed) + the network delay rate, (vehicles in the system or waiting − Σ speeds / 27.78) / n_ref(q), with n_ref from stage 0c's references (V424).
- **The judged 1-Hz close-following flag stays in the reward.** The candidate then differs from baseline-v3 in the algorithm, not in the safety signal. The step-resolution signal (memo 1D) waits for a later round.
- **Algorithm:**
  - a second critic of the same shape for the cost, with its own scale fixed at update 0 like the reward critic;
  - GAE for the cost with the same γ and λ;
  - the reward and cost advantages are normalised per minibatch separately, then combined as (A_r − λ·A_c) / (1 + λ);
  - the value loss is the sum of both critics' losses.
- **Dual variable:**
  - λ starts at 1.0 and stays there for the first 20 updates;
  - after every later update, λ ← clip(λ + 1.0 × (J − 0.97), 0, 10);
  - J = the mean, over the episodes of the last 20 updates, of each episode's training-mode delay divided by d_ref at its demand level.
- **Training-mode delay** = vehicle-seconds in the system or waiting, minus the sum of speeds read once a second over 27.78 m/s. This is the judged all-vehicle delay, sampled once a second. Training and the reference compute it with the same code.
- **d_ref(q):** from stage 0. It is the median training-mode delay of the lower-delay of os1_15_10 and p333 at each training level, under the training slowdown distribution, on the reference seeds. The target, 3 % below that, leaves room for the 20-seed noise (V413, F1).
- **Parameters fixed now:** start 1.0, freeze 20, window 20, step 1.0, cap 10, target 0.97. They are not tuned. The family is PPO-Lagrangian [VERIFY]; PID variants are not used.

### 3B. Residual PPO on os1_15_10

- **Base:** every 5-s step, the environment computes the rule's level for every ALKS from that ALKS's own observation. This is `OwnState(level 1, th 15, crowd 10)`, as the rule arm uses it.
- **Offset:** each vehicle holds an offset of −1, 0 or +1 level. It changes only at the vehicle's own 10-s decision. A new vehicle starts at 0. The vehicle's target is clip(base + offset, 0, 3); the hold and the V2V gate act as before.
- **State:** the 16 inputs plus the rule's level / 3.
- **Initialisation:** the actor's last layer starts with zero weights and biases (0, ln 18, 0), so offset 0 has probability 0.9 for every input. Training starts as the rule.
- **Range ±1:** this keeps the rule's delay prior tight and matches the earlier residual convention (V317). It cannot reach 1.2 s from 0.8 s; the from-scratch policies use longer gaps partly where they lose delay (V413, F5). Disclosed.
- **Build check, exact:** with every offset 0, a run reproduces the stored os1_15_10 row of `rows/conf3_eval_primary.jsonl.gz` (X2, seed 7,440,200) on every numeric key.

## Logging (V394)

- Training logs only to TensorBoard: float32 scalars, one value per tag per update.
- **Tags:**
  - `ppo/*` as in conf3;
  - `ep/e<slot>/<counter>` per environment slot, with the slot's level `ep/e<slot>/q`, its seed and training-mode delay. Per-level tags could not hold one value per update, with 7 levels cycling through 3 slots (V424);
  - for 2C, also `lagr/lambda`, `cost/per_decision` and `cost/value_loss`, and `lagr/J` from update 21, once λ moves.
- **Kept besides:** checkpoints every 50 updates, the pilot statistics and the config, as before.
- **Checks read the event files back:**
  - every update once, every tag present, no missing or non-finite value;
  - every seed and level as expected, per slot;
  - constant critic scales; the settings as pinned.
- A planted-fault test shows each check firing.

## Stage 0: calibration, no training

**Stage 0a, checkpoint calibration (report-only).**
- **Runs:** C0-C4 at u50, u100, …, u500 (50 policies), plus os1_15_10, p333 and no control. X1 and X2 at 5,300, on 20 seeds. About 2,120 runs.
- **Reports, per cell:**
  - each checkpoint's close-following and delay against os1_15_10;
  - the rank correlation of the checkpoint-selection score at u100, u150 and u250 against u500;
  - whether a checkpoint chosen by the rule below clears the bar where the final one does not.

**Stage 0b, 2C reference and its stop.**
- **Runs:** os1_15_10, p333 and the five baseline-v3 final policies, under training conditions (random slowdowns) at the 7 training levels, on 20 seeds. 980 runs.
- **d_ref(q)** is computed from the two rules.
- **Stop for 2C:** if at least 4 of 5 baseline-v3 policies already have J ≤ 0.97 on these runs (J as defined above), the constraint would not bind, and 2C is not trained. It is reported as "constraint not binding". The round goes on with the other candidates.

**Stage 0c, reward references.** No control in steady traffic at the 7 training levels, on 20 seeds (140 runs): per level, the median per second of braking at 3 m/s², close-following and vehicles in the system, computed as confirmatory 3's `make_env.py` did. They replace `env.json`'s references, which exist only at 4,090, 4,600 and 5,300, for every candidate, the control arm included.

## Training

- **Order:** one candidate per slot, run serially in the order v3w, 3B, 1A, 2C. The 5 learners of a slot run in parallel, and nothing else runs beside training (V392).
- **Isolation:** each slot runs from a frozen copy of the run commit, in its own systemd unit, under the CPU guard.
- **Crash:** a learner that crashes restarts once with the same seeds and is logged.
- **Collapse check, per learner, on its own reward series:**
  - a = |mean reward over updates 401-500 − mean over 301-400|;
  - b = mean over 401-500 − mean over 1-50;
  - σ = SD of the per-update reward over updates 101-500;
  - **pass:** a ≤ 0.4 σ, and b ≥ 0. For 2C, b is not required, because a rising λ may lower the safety-only reward by design.
  - On baseline-v3's logs, 0.4 σ is about confirmatory 3's fixed 0.03. A test checks that it gives the same verdicts there.
  - Each update covers 3 of the 7 levels, so the reward has a 7-update cycle that baseline-v3 did not have. Each phase's mean over updates 101-500 is taken out before a, b and σ are computed, so σ stays the noise it was calibrated on (review, V424).
- **Failing learners:** a failing learner stays in with a disclosure. If more than one learner of a candidate fails, that candidate is out of the round. Any other failed training check (a log or settings fault, or an error) stops the chain and goes to the author (V424).
- **2C mechanism stop:** if λ sits at its cap over the last 100 updates in at least 3 of 5 learners, 2C is out of the round, reported as "constraint not met at the cap".

## Validation

- **Cells and seeds:** X1 and X2 at 5,300, on 40 validation seeds.
- **Arms:**
  - each candidate's learners at u250 and u500;
  - baseline-v3's learners at u250 and u500;
  - os1_15_10, p333 and no control.
- **Checkpoint rule, the same for every learner, the incumbent included:**
  - for each of u250 and u500, count the cells where its delay is within 2 % of os1_15_10 (the protocol statistic's point estimate at least −2);
  - choose the checkpoint with more such cells;
  - on a tie, choose the one with fewer close-following seconds, summing the two cells' medians;
  - if that also ties, choose u500.
- **Arm values:** a candidate's arm is the mean over its 5 learners, per seed, at the chosen checkpoints. The incumbent's arm is the same.
- **Advance rule, per candidate:**
  - in at least one cell, its delay is less than the incumbent arm's, with the 95 % CI excluding 0;
  - in that same cell, it has at least 10 % fewer close-following seconds than os1_15_10 (point estimate);
  - in neither cell is its delay more than the incumbent's with the 95 % CI excluding 0.
- **Floor KILL, per candidate:** the candidate is out if, in either cell, its u500 arm has less than 10 % fewer close-following seconds than p333, or more delay than no control with the CI excluding 0.
- **Ranking:** at most 2 candidates advance. If more qualify, they are ranked by their largest delay effect against the incumbent.
- **Round KILL:** if no candidate advances, the round ends. Baseline-v3 stays, no test seed is used, and the result is reported.

Validation selects, so its 95 % CIs carry no multiplicity correction.

## Test, used once

- **Cells and seeds:** X1 and X2 at 5,300, on 40 fresh test seeds.
- **Arms:**
  - each finalist's 5 learners at their chosen checkpoints;
  - baseline-v3's 5 learners at their chosen checkpoints, and their final policies (report-only);
  - every opponent confirmatory 3 ran in these cells (`opponents.json`), plus p333 and no control.
  - the control arm v3w at its chosen checkpoints, whether or not it is a finalist.
- **Multiplicity:** Bonferroni over finalists × cells. With m tests, the CIs are at 1 − 0.05/m, two-sided: 98.75 % for m = 2, 99.375 % for m = 4.

**Reading T1, decides "better than baseline-v3".** Per finalist, per cell: delay less than the incumbent arm's with the corrected CI excluding 0, and close-following not more than 10 % above the incumbent's (point estimate).

**Reading T2, decides the claim against the rules.** Confirmatory 3's tuned reading, per finalist, per cell, unchanged except for the CI level and n = 40:
- at least 4 of 5 policies have, against every opponent that counts in that cell: close-following at least 10 % better (CI excluding 0) and at least 20 per run lower;
- delay at most 2 % worse; flow at most 0.5 % worse; braking at 3 m/s² at most 5 % worse; moving full-emergency events at most 5 % or 5 per run more; collisions at most the opponent's plus 1;
- against p333: delay at most 5 % worse and flow at most 1 % worse.

**Reading B, decides "band shown" (V418, V420).**
- **Runs:** under the training slowdowns at 4,500, 5,000, 5,250, 5,500 and 6,000 veh/h, on 20 fresh band seeds: the tested candidates (finalists and v3w), baseline-v3 at its chosen checkpoints, no control, p333 and os1_15_10.
- **Shown, per arm:** at each of 5,000, 5,250 and 5,500, the arm has at least 10 % and at least 20 per run fewer close-following seconds than no control, with the CI clear of 0. All three must hold, so there is no correction within an arm; Bonferroni applies over the arms read. Baseline-v3's band is reported at the same level, report-only.
- **Edges (4,500 and 6,000):** reported, not required either way. A policy trained over the range may extend the band; the profile across the five levels shows where the impact fades.

**Reading A, attribution (report-only):** each method finalist's arm against the control arm v3w at 5,300, delay and close-following, 95 % CIs. It says whether a gain comes from the method or from the wider range.

**Reported beside:**
- confirmatory 3's replication, delay-win, "safety" and severe-conflict readings;
- every arm's counters by road, speed and period;
- the 1-Hz against step-braking check;
- no control in every table.

## Statistic

The protocol statistic of confirmatory 3:
- effect = sign × median(P − O) / median(O) × 100 over paired seeds;
- percentile bootstrap of the paired differences, 20,000 resamples, denominator fixed.

Arm-level comparisons use the per-seed mean over the 5 learners. One convention throughout (V396).

## Seeds, proposed for approval

| Use | Range | Count |
|---|---|---|
| Smoke checks in training mode | 7,419,899, the seed of `c_train.py smoke`, used before | 1 |
| Stage 0a, checkpoint calibration | 7,440,300-319 | 20 |
| Stage 0b, 2C reference | 7,440,340-359 | 20 |
| Stage 0c, reward references | 7,440,370-389 | 20 |
| Validation | 7,440,400-439 | 40 |
| Test, used once | 7,440,500-539 | 40 |
| Band test, used once | 7,440,540-559 | 20 |
| Training, shared by all candidates | 7,464,000-7,471,799 (worker 9 starts at 7,464,000, 520 per worker) | 7,800 |

The 7,440,xxx ranges lie in the block approved in V354, and are unused: the ledger and the code use up to 7,440,239, and the sweep used 600-609. The training range follows confirmatory 3's (7,456,000-7,463,999). Determinism and reproduction checks re-run stored rows on their own seeds (7,440,200 and 7,440,045); they create no new data.

## Order and checks before the run

1. **Build** (one commit):
   - environment options; trainer cost critic, dual variable and residual start;
   - TensorBoard logging and the event-file checks;
   - the evaluation hook that gives a residual policy its environment;
   - round-1 scripts.
2. **Tests:**
   - unit tests of every new term, the combined advantage, the dual update, the residual start, the collapse rule on baseline-v3's logs, the event-file read-back and its planted faults;
   - the round-1 reading reproduces confirmatory 3's tuned counts from the stored rows.
3. **T3, determinism:** at the run commit, with defaults, stored rows reproduce on every numeric key:
   - baseline-v3's d0 and os1_15_10 rows (X2, seed 7,440,200);
   - baseline v2's no-control row (`r2_p0d`, seed 7,440,045, 5,300).
4. **3B exact check:** a zero-offset residual reproduces the stored os1_15_10 row (above).
5. **Default training path unchanged:** in training mode, the old frozen code and the new code give identical per-vehicle rewards and episode counters on the smoke seed.
6. **Smoke in training mode, each candidate, 2 updates on the smoke seed:**
   - rewards finite and varying; 1A's follower and merging charges non-zero;
   - 2C's costs present in training mode, λ written, the cost critic trained;
   - 3B's offsets reaching the levels;
   - TensorBoard events read back.
7. **Code review:** adversarial, of the build commit, as `CLAUDE.md` requires before long runs (ultracode on).
8. **Run:** stage 0, then training (v3w, 3B, 1A, 2C), the collapse checks, validation, the advance decision, the test and the reading. Any failed check stops the chain and goes to the author.

## Compute

Measured rates: about 1,500 evaluation runs per hour on 28-32 workers (V409, V417); a 5-learner slot takes 3.3 h (baseline-v3). Runs at the higher training levels take longer.

| Step | Runs | Hours |
|---|---|---|
| Stage 0a | 2,120 | 1.4 |
| Stage 0b, 0c | 1,120 | 0.8 |
| Training, 4 slots | – | 13-14 |
| Validation | 4,240 | 2.8 |
| Test at 5,300 | up to 3,040 | 2.0 |
| Band test | up to 2,300 | 1.5 |
| **Total** | | **about 22** |

64 workers for evaluation on 32 hardware threads, by the author's choice to measure throughput and total time; the CPU guard's limit at 100 %, so it pauses nothing (author: "Go for 95-100% CPU load", V421). Training is unchanged: 5 learners × 3 environments per slot.

## Stop rules

- No change to the plant, opponents, rewards, budget, parameters or reading after stage 0 starts, except by a logged author decision, disclosed, with fresh seeds afterwards.
- A bug found after results: fix, re-run everything affected, log both outcomes.
- A trace can add an explanation; it cannot change the outcome of a reading.

## Disclosures

- **Noise floor:** the 2 % delay limit is judged on the point estimate. Even at 40 seeds, the delay CI half-width is about 3-6 points (V413, F1), so a true tie can still fail T2.
- **Checkpoint selection** between u250 and u500 is a departure from "final policy only". It is applied to every learner alike, the incumbent included, and baseline-v3's final policies are reported beside.
- **Teaching to the test:** 2C keeps the judged 1-Hz flag in its reward, as baseline-v3 did. The counters outside the reward (TTC below 1.5 and 2 s, the severe check, braking counted every 0.1 s) are reported.
- **Attribution in 1A is a heuristic, not causal.** A follower's lost time is charged to its ALKS leader, and an ALKS-ALKS pair counts the follower twice. An accelerating-lane vehicle behind a ramp ALKS is charged both to that leader and to the nearest mainline ALKS.
- **2C's J is measured on the sampled actions of training,** while d_ref comes from the rules and the 0b stop from greedy policies. Exploration may raise training delay, so λ may rise partly from exploration.
- **3B's range:** ±1 cannot reach every level the from-scratch policies use.
- **The band was read after the sweep's data** (V419, post hoc). Reading B tests it on fresh seeds with policies trained for it.
- **New reward references** at the 7 training levels, from no control on fresh seeds, replace baseline-v3's; the control arm v3w uses them too, so it differs from baseline-v3 in range, seeds and references, not in method.
- **No map cells** are run (H1, H2, 4,600 in X1 and X2). The harm map of confirmatory 3 is not repeated.
- **The opponents are not re-tuned** for this round. A CMA-ES rule search (memo 3E) is not part of the round; it is recommended before any thesis claim.
- **Literature:** PPO-Lagrangian, residual policy learning and the attribution idea are named families [VERIFY]. None is claimed as new.

## What this cannot show

- A win holds for this uncalibrated SUMO model, these slowdowns, these demand levels and ideal V2V.
- With 3 candidates and one round, a null result does not show that no change to the SAR or the algorithm would help.
