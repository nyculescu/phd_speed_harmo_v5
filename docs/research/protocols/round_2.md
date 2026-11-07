# Round 2: evaluation protocol

**Status: draft, revision 2, 2026-11-07 (V453).**
- **Written before any round-2 candidate was evaluated.** Only the training curves, the training checks and 3E's search exist. All 5 trained candidates passed their checks, with no collapsed learner and no fault, so every learner enters (V450).
- **Revision 1** had an ultracode design review: 4 lenses and a skeptic per finding; 56 findings, 50 confirmed. This revision applies them.
- **Path to the run:**
  1. The author approves this text, D1-D13 and the seeds.
  2. Build, then the build's code review.
  3. The run.
  Nothing is built or run, and no seed below is used, before that approval.

## Questions

- **Q1, method:** does any round-2 candidate beat v3w, round 1's winner, on fresh seeds? If one does, does it win confirmatory 3's tuned reading against the rules, with a CMA-ES-tuned rule among them?
- **Q2, the incumbent against a stronger opponent:** does v3w still win the tuned reading in X1 and X2 when a CMA-ES-tuned rule counts among the opponents? Round 1's T2 win was against the old grid only. Its protocol recommended this search before any thesis claim.
  - For any thesis sentence against the tuned rules, this round's T2 for v3w replaces round 1's. A cell that v3w does not win here is reported as not won, with round 1's win beside it.
  - Q2 is answered in a cell only if a 3E rule counts there (below). Otherwise that cell repeats round 1's reading on fresh seeds, and the report says so.
- **Q3, band (report-only):** across 4,500-6,000 veh/h, how does close-following under each tested policy compare with no control? Round 1's reading B stands: v3w's band is not shown.

## Arms

**Candidates.** Each is one change against v3w. The trained ones use round 1's training seeds and budget (V439, V444).

| Arm | Change | Policies | Code |
|---|---|---|---|
| 2B | learning rate and entropy decay; one critic scale | `round2_remote/train_2b` C0-C4 | `r2/2b-anneal` 5f9f5d3 |
| 1B | gate hold: a decision of a vehicle outside the V2V gate is dropped and its level holds, in training and at evaluation; that decision also leaves the policy loss | `train_1b` | `r2/1b-gate-mask` 5c10e6f |
| 1D | safety charge from 0.1-s braking (training only) | `train_1d` | `r2/1d-brake-10hz` e8107fc |
| ahead | two look-ahead speed inputs, [16] and [17] | `train_ahead` | `r2/ahead-lookahead` 66fa146 |
| rep | training draw with a repeated slowdown (training only) | `train_rep` | `r2/rep-slow` 08786f1 |
| tail | per learner, the argmax of the mean action probabilities of v3w's own u250, u300, …, u500 (6 members, equal weight, each with its own input statistics) | v3w's checkpoints | to build |
| sw | for every ALKS with route position x < 594.72 m (observation column 0 × 1000, from the start of 3a; 3E's zone edge after merge 1), os1_15_10's own output; for every due ALKS from 594.72 m on, ramp 2 included, v3w's greedy level | v3w's checkpoints | to build |

- **1B changes the actuator, not only the loss.**
  - In v3w, a decision of a vehicle outside the V2V gate still sets its level and starts the hold, and the level acts once the vehicle is in the gate.
  - In 1B that decision is dropped, so the level moves only inside the gate. In training, this applied to about 44 % of decisions (`ppo/mask_frac`).
  - A 1B result is the effect of the hold and the mask together (D12).
- **tail** has no checkpoint choice. Every other learner, v3w included, has its checkpoints chosen on the validation seeds, so at validation those learners carry the rule's in-sample gain and tail does not.
  - On round 1's rows (split-half), that gain was about 0.2-0.3 points of delay and 0.8-1.5 points of close-following.
  - At the test, on fresh seeds, there is no such bias.
- **sw:**
  - Its split point is fixed here and not swept (V408). It takes each v3w learner at u250 and at u500, and the checkpoint rule applies to it as to any learner.
  - os1_15_10 acts only from its x_min of 500 m; below that it sends 0.8 s, as p333 does. So in sw, ramp 1, the 3a lane and the road upstream get 0.8 s. The rule's own levels act on 500-594.72 m only.
  - A sw result reads "0.8 s upstream of 500 m, os1_15_10 to 594.72 m, v3w after".
- **Incumbent: v3w** (D1). Its 5 learners take their checkpoints by round 1's rule on this round's validation seeds (D8).
- **Report-only:** baseline-v3's 5 learners at u500, which are both its chosen checkpoints and its final policies.

**Opponents.**
- Every opponent of round 1's test: confirmatory 3's grid (`baseline_v3/opponents.json`, 12 rule arms, the copy rule included), p333 and no control.
- **3E (3E-T):** the CMA-ES per-zone own-state rule `g032i20`, tuned under condition T at 4,500, 5,000, 5,250, 5,500 and 6,000 on seeds 7,440,700-739 (V441, V443, V448). It is fixed and not re-tuned.
  - **Its definition** (`final.json`, `meta.json`) is copied into `docs/research/round2/3e/`. Their commit field is empty; the code is `r2/3e-cmaes` d2d0d04, whose `cma2.py` has sha256 1682fa6b….
  - **Per zone** (up, merge 1, between, merge 2, down), the rule has a speed threshold, a crowd threshold, the level used when its condition holds, and the free level used otherwise. The pre-registration's "on/off switch" is this free level.
  - **g032i20** holds 1.2 s in the between-merges zone whether its condition holds or not (level 1, free 1). Its default in the other zones is 0.8 s.
- **3E-X1 and 3E-X2** (D4, if approved): per-cell searches, run before validation.
  - **Kept from 3E:** family, diagonal CMA, population 24, 40 generations, sigma 0.25 and CMA seed 20261106.
  - **Changed:**
    - condition X1 or X2, at 5,300 only, on seeds 7,440,740-779;
    - **reference p333**, the counting reference, for all three terms of the objective: the pooled change in TTC seconds, the delay hinge, and collisions beyond the reference;
    - the delay hinge at **+1 % above p333**, which leaves a point of margin under the 2 % counting filter on fresh seeds;
    - **16 seeds per generation**, taken in turn from the 40. At one level, 8 seeds give a loss SD of about 15 points, 16 about 8.5;
    - **start:** X1 from os0_10_10's values (X1's own-state form), X2 from os1_15_10's; the upstream zone is off, as in 3E;
    - **shortlist:** each configuration is ranked by its loss minus its generation's median, because the seed window moved 3E's generation medians by 18-28 points. The 5 best distinct configurations and the final CMA mean are re-run on all 40 tuning seeds;
    - **pick:** the lowest loss among those whose delay on the 40 tuning seeds is at most 2 % above p333's (point) and whose collisions are at most p333's plus 1. If none qualifies, that cell has no 3E-X rule, and the report says so;
    - **convergence:** the median loss of the last 10 generations is reported against the 10 before. If the loss is still falling, that is disclosed beside every 3E-X result.
  - **Cells:** 3E-X1 joins X1's opponents only, and 3E-X2 joins X2's only.
- **Counting** follows confirmatory 3. An opponent counts in a cell if:
  - it is p333, one of the cell's forms, or a 3E rule for that cell; and
  - its delay is at most 2 % above p333's (point estimate).
  - Counting is decided on each phase's own rows: validation rows for the ranking, test rows for T2.
- **3E-T may not count.** Its search capped delay at +2 % against os1_15_10, not against p333.
  - On its tuning seeds (condition T) it has 3.2 % and 3.9 % more delay than os1_15_10 at 5,250 and 5,500.
  - os1_15_10 itself had 2.1 % (X1) and 2.2 % (X2) more delay than p333 on round 1's validation seeds, and 4.8 % and 1.2 % more on its test seeds.
- **A 3E rule that does not count in a cell** is listed as excluded, with its delay and close-following against p333 and os1_15_10.
  - Q1 and Q2 in that cell read "not answered against the CMA-ES rule: not within the delay filter", never a win against it.
  - If no 3E rule counts in either cell, Q2 is not answered.
- **No separate admissibility gate for 3E.** The pre-registration left 3E's side metrics to "round 2's admissibility checks". A gate could only remove 3E from the opponents, which makes the tuned reading easier to win. So:
  - The side metrics enter through the tuned reading's limits, applied to the policies against each counting opponent.
  - 3E's delay, flow, braking at 3 and 7 m/s², moving full-emergency events and collisions against p333 and os1_15_10 are reported per cell.
  - Its tuning rows hold no braking at 3 m/s², moving full-emergency or severe-conflict counts, so this round is the first to measure those for 3E.

## Build

Everything is on one branch, `r2/eval`, from `v5b1`. The candidate branches are not changed.
- `b_env.ZoneOwnState`, moved from `cma2.py` unchanged, with a `plant_sweep` key;
- `c_train.TailMean`, with a `pts` key;
- `b_env.ZoneSwitch`, with its key;
- **only if D4 is approved:** `docs/research/round2/cma2.py`, copied from `r2/3e-cmaes` d2d0d04, with these changes:
  - `--ref` (default os1_15_10);
  - `--seed-block` (default 7,440,700-739; recorded in `meta.json`);
  - `--hinge`, `--start`, `--seeds-per-gen`;
  - the shortlist, pick and convergence rules above;
  - the rule built through `b_env.ZoneOwnState`.
  - With the defaults, the objective on 3E's stored final rows reproduces `final.json`, and `r2/3e-cmaes` stays as it is.
- `docs/research/round2/run2.py SNAPSHOT ARMS_JSON LEVELS SEEDS OUT`: runs `plant_sweep.matrix` on the given arms in a new process whose working directory and `PYTHONPATH` are a frozen copy of SNAPSHOT. It writes `OUT/rows_<commit>.jsonl`, with the commit read from the copy, and logs that commit in the status file;
- `docs/research/round2/importance2.py`: the decision trace and the shuffles for ahead's KILL, run from ahead's snapshot;
- `docs/research/round2/{common2e.py, validate2.py, test2.py, decide2.py}`;
- `tests/test_round2.py`.

**Where each arm runs.**
- Each trained candidate runs from a frozen copy of the code that trained it: 2B 5f9f5d3, 1B 5c10e6f, 1D e8107fc, ahead 66fa146 and rep 08786f1. ahead's and 1B's policies need environment options (`obs_ahead`, `gate_hold`) that exist only there.
- Every other arm runs from a frozen copy of `r2/eval`'s run commit.
- `validate2.py` and `test2.py` give each snapshot its arms through `run2.py`, one process per snapshot, and read the union of the rows files. Rows pair by seed, whatever process wrote them.
- The chain stops if a rows file's commit is not its arms' snapshot, or if an arm is missing from the union.
- **One platform (V436):** all arms of a phase run on one machine.

## Checks before the run

Any failure stops the chain and goes to the author.

1. **Identity:**
   - **3E:** ZoneOwnState with g032i20's parameters reproduces 3E's stored rows in `final_runs.jsonl`: g032i20's and the reference's, at seeds 7,440,700-702 and at 4,500 and 6,000 veh/h, under condition T as `cma2.cfg_for(ctrl, 'T')` builds it.
     - Each new row is reduced by `cma2.slim`, so a counter that never fired reads 0, as in the stored rows.
     - It must equal the stored row exactly on the 8 metrics: all_delay, ttc_net, collisions, passed, teleports, alks_b45_step, alks_full_events and finished_pct. `wall_s` is run time and is not compared.
     - At X2 and 5,300 on one seed, the `plant_sweep` key also reproduces a full row from `cma2.py`'s own worker route, on every key but name and cfg.
   - **tail:** TailMean([u500]) and TailMean([u500, u500]) reproduce Greedy(u500) on v3w C0, on every numeric key. A unit test on 1,000 observations recorded from the smoke run shows that TailMean equals the argmax of the explicit mean of the six members' softmax, each member with its own input statistics.
   - **sw:** ZoneSwitch at x_from = −1e9 reproduces v3w's rows, and at +1e9 os1_15_10's.
2. **Stored rows, on every numeric key, from `r2/eval` and each candidate snapshot:**
   - `checks1.py rows`: confirmatory 3's os1_15_10 and baseline-v3 d0 rows (X2, seed 7,440,200), the zero-offset residual against that rule row, and baseline v2's no-control row (`r2_p0d`, seed 7,440,045). None is a v3w row.
   - On `r2/eval` also: round 1's stored v3w rows `X1|w0` and `X2|w0` (C0 at u250, `round1_remote/out/test/test.jsonl`), one seed per cell.
3. **Reading replay:** `decide2.py`, given round 1's incumbent (baseline-v3) and level (m = 2, percentiles 1.25-98.75, V452), reproduces round 1's T1 and T2 for v3w from its stored test rows:
   - T1 better in both cells, with the stored CIs;
   - T2 5 of 5, counting [p333] in X1 and [p333, os1_15_10] in X2.
   - On round 1's validation rows with v3w as incumbent, it gives res and attr harmed in both cells.
4. **T3, determinism:** check 2 runs again on the machine that runs the phase, at each snapshot's frozen run commit.
5. **Smoke,** on the smoke seed, at the evaluation settings, each snapshot through `run2.py`:
   - Any counter added for this must not call `CavEnv._x`, and a traced row must equal the untraced row on every numeric key (V386). Outputs must carry the inputs:
   - **sw:** decisions served from each side of 594.72 m are both more than 0, and each side's levels come from its own controller;
   - **3E:** each zone with decisions gives only its own level or free value;
   - **tail:** the share of due decisions whose level differs from Greedy(u500) is reported;
   - **ahead:** its policy gets 18 inputs, and both look-ahead inputs vary over the run (SD > 0; 0.15 and 0.13 in training). The share of decisions that read 1.0 is reported;
   - **1B:** some decisions are dropped (the environment's `masked` output is not empty), and their share is reported beside training's 0.44.
6. **Unit tests** (`tests/test_round2.py`) on planted rows:
   - TailMean on two members with known probabilities, and ZoneSwitch at a middle x_from;
   - decide2's checkpoint rule, path (a), path (b), harm, the floor KILL, the ranking and its tie-break, the corrected levels and the "what follows" rule;
   - the 3E counting and exclusion outputs;
   - if D4, cma2's new options and the pick rule.
7. **Code review:** adversarial review of the build (ultracode), as `CLAUDE.md` requires before long runs.

## Order of the run

1. Build on `r2/eval`, then checks 1-7. The run commit is frozen, and the chain runs from a detached copy of it, where nothing is committed mid-run.
2. **If D4:** the 3E-X1 and 3E-X2 searches and picks. Check 1's 3E identity also passes on each pick's stored final rows.
3. In this order: validation, checkpoints, ahead's KILL, advance and ranking, test, band, readings.
   - The chain goes on between steps without the author.
   - Any failed check stops it and goes to the author.
- **Operation:**
  - The standing rules hold. On the laptop: 31 workers (V426), the CPU guard, 40 % CPU from 23:00 to 09:00 (V432), and the 5-minute health unit (V428).
  - On a rented machine: its rate is measured on the first batch, checks 2 and 4 run there, and the unattended finisher fetches and destroys it (V442).
  - The raw rows go under `/home/catalin/work/phd/v5b1_runs/round2/`.

## Validation (40 fresh seeds, X1 and X2 at 5,300, 95 % CIs, no correction: validation selects)

- **Arms:**
  - each trained candidate at u250 and u500;
  - v3w and sw at u250 and u500;
  - tail;
  - every opponent, the 3E rules included, and no control.
- **Checkpoint rule,** the same for every learner (round 1's):
  - for each of u250 and u500, count the cells where its delay is within 2 % of os1_15_10's;
  - choose the checkpoint with more such cells;
  - on a tie, choose the one with fewer close-following seconds, summing the two cells' medians;
  - if that also ties, choose u500.
- **Arm values:** each arm is the per-seed mean over its 5 learners at their chosen checkpoints; tail is taken as it is.
- **ahead's pre-registered KILL** (V444), read before its advance rule. ahead is out if its policies ignore both look-ahead inputs.
  - **Measure:** the memo's measure (p1c), permutation importance. It is the share of decisions whose argmax level changes when one input is shuffled across the decisions of a run, averaged over 10 shuffles with a fixed seed.
  - **Read** for each learner at its chosen checkpoint, on validation seeds 7,440,800 and 7,440,801 in both cells, from traced re-runs. Those re-runs must equal the untraced rows on every numeric key (V386).
  - **"About 0"** means the median over the 5 learners is below 2 % for input [16] and below 2 % for [17]. If so, ahead is out, reported as "look-ahead inputs not used". For scale: a dead input changes 0 % of decisions, and baseline-v3's least-used live inputs 5-12 % (p1c).
  - Both inputs' importance is always reported. The KILL's other half (delay not below v3w's, close-following no better) is covered by the advance rule.
- **Advance rule, per candidate, against the v3w arm (D2).** A candidate must be **better in at least one cell**, by either path:
  - (a) delay less than v3w's, CI excluding 0, and close-following at most 10 % more than v3w's (point);
  - (b) close-following at least 10 % less than v3w's, CI excluding 0, and delay at most 2 % more than v3w's (point).
- **Harm,** in either cell, puts the candidate out:
  - delay more than 2 % above v3w's (point), with the CI's upper bound below 0; or
  - close-following more than 10 % above v3w's (point), with the CI's upper bound below 0.
- **Floor KILL,** as round 1's, on the candidate's u500 arm (every learner at u500; tail as it is; sw with v3w at u500). The candidate is out if, in either cell:
  - that arm has less than 10 % fewer close-following seconds than p333 (point); or
  - it has more delay than no control, with the CI excluding 0.
- **Ranking:** at most 2 finalists (D3).
  - First key: the number of learners, at their chosen checkpoints, that pass the tuned reading (below, at 95 %) against the counting opponents, summed over the two cells.
  - Ties go to the larger score against v3w. The score is the largest value, over the cells where the candidate is better, of its delay effect divided by 2 or its close-following effect divided by 10 (point estimates). This weighs the two paths at the bar's own 2 : 10 rate.
  - Remaining ties follow the order of the Arms table.
  - **The count is expected to tie.** On round 1's validation rows only p333 counted in either cell, and v3w and res both scored 10 of 10.
- **No finalist:** Q1 ends with a null result. The test still runs for Q2 (D9).

## Test, used once (40 fresh seeds, X1 and X2 at 5,300)

- **Arms:**
  - the finalists at their chosen checkpoints;
  - v3w at its chosen checkpoints;
  - baseline-v3 (report-only);
  - every opponent, the 3E rules included, and no control.
- **Multiplicity:** Bonferroni. Each m gives two-sided CIs at 1 − 0.05/m, which are bootstrap percentiles 2.5/m and 100 − 2.5/m.
  - **T1** uses m = finalists × 2 cells. Its two paths each use one tail, so the bound on a false "better" is 0.05 over the family, against 0.025 for round 1's single path. Path (b) also needs a 10 % point estimate: 0 of 1,000 null resamples of round 1's rows passed it.
  - **T2** uses m = (finalists + v3w) × 2 cells. So v3w's level for Q2 depends on how many finalists advance: 97.5 % with none, 98.75 % with one, 99.17 % with two. Adding 3E rules does not change m: the tuned reading is an intersection over counting opponents, so each extra opponent only makes it harder.

**Reading T1 (Q1), per finalist and cell:** better than v3w by path (a) or (b), at T1's corrected level.
- **Harm at test:** validation's harm rule, at 95 %, because a corrected CI would hide harm. A finalist harmed in either cell is better in neither.

**Reading T2 (Q1, Q2), which decides the claim against the rules:** per finalist, for v3w, and per cell. Confirmatory 3's tuned reading, at T2's corrected level and n = 40:
- at least 4 of 5 policies have, against every counting opponent: close-following at least 10 % better (CI excluding 0) and at least 20 per run lower;
- delay at most 2 % worse; flow at most 0.5 % worse; braking at 3 m/s² at most 5 % worse; moving full-emergency events at most 5 % or 5 per run more; collisions at most the opponent's plus 1;
- against p333: delay at most 5 % worse and flow at most 1 % worse.

**Reported beside:**
- T2 without the 3E rules (the old grid only), as a comparison with round 1. Where no 3E rule counts, it is the same as T2, and the table says so;
- each 3E rule's counting status and its delay against p333 with the CI, per cell, at validation and at test;
- **each 3E rule against os1_15_10 (its search reference), p333 and each of the cell's counting forms.** If D4 runs, 3E-X's values on its own tuning seeds are shown beside. The drop to fresh seeds is 3E-X's overfitting check;
- **v3w at round 1's checkpoints** (C0 and C1 at u250, C2-C4 at u500): the tuned reading at T2's level on the validation rows, which already hold these policies. Report-only;
- per policy and counting opponent, the upper end of T2's corrected delay CI against a 5 % margin. This is a non-inferiority bound, report-only (D11). At n = 40 it passes a true tie only about half the time, so a miss is not harm;
- confirmatory 3's replication, delay-win, "safety" and severe-conflict readings, on T2's counting set;
- every arm's counters by road, speed and period;
- the 1-Hz against step-braking check;
- no control in every table.

## Band (Q3, report-only; 20 fresh seeds, training slowdowns, 4,500, 5,000, 5,250, 5,500 and 6,000 veh/h)

- **Arms:**
  - the finalists and v3w;
  - baseline-v3;
  - no control, p333, os1_15_10 and 3E-T.
- **Reported, per arm and level:**
  - close-following and delay against no control, with 95 % CIs;
  - the share of seeds on which the arm has fewer close-following seconds than no control, with its 95 % CI.
  - **There is no "shown" verdict.** At 5,000, 9 of round 1's 20 seeds had more close-following under v3w than under no control and 11 had fewer. The median of paired differences jumps across that gap. Resampling round 1's rows gives v3w a 3-13 % chance of "shown" at 40 seeds (D5).
- **3E-T against os1_15_10 at each level** on these fresh seeds, beside the same statistic on its 40 tuning seeds, report-only, with no verdict on overfitting.
  - The band's slowdowns are 3E's condition T, and its levels are 3E's tuning levels, so 3E-T is read in its own tuning condition.
  - Change against os1_15_10 on the tuning seeds (positive = more):

    | | 4,500 | 5,000 | 5,250 | 5,500 | 6,000 |
    |---|---|---|---|---|---|
    | close-following | +24.9 % | −7.9 % | −7.4 % | −12.2 % | −20.0 % |
    | delay | +1.5 % | +2.1 % | +3.2 % | +3.9 % | −0.5 % |

  - The pooled −14.3 % close-following at +2.0 % delay sums TTC seconds over the levels; 68 % of its gain is at 6,000.
- A finalist rep is read under the training draw kind random, not its own (random_rep).

## Sentences allowed

Confirmatory 3's model sentence, sentence table and no-control clause apply, filled from T2. These additions are fixed now:
- **Counting set:**
  - The severe-conflict check that permits the word "safety", the strongest counting rule and the margin in the sentence all use T2's counting set, every counting 3E rule included.
  - Replication stays against p333. The delay win stays against `opponents.json`'s delay opponent and p333.
- **T2 without 3E** is only a comparison with round 1. No sentence rests on it.
- **A 3E rule did not count in a cell:** "The CMA-ES-tuned rule [name] did not meet the delay filter in [cell]: [delay and close-following against p333]." That cell's sentence names only the rules that counted.
- **Won against the grid, not with a counting 3E rule:** "Won against confirmatory 3's grid, not against the CMA-ES rule [name]: [limits missed]". No sentence says the cell was won.
- **Naming:**
  - **3E-T:** "a rule tuned by CMA-ES under the training slowdowns, not for this cell".
  - **3E-X:** "a rule tuned by CMA-ES for this cell on separate seeds".
  - **sw:** "a hybrid: 0.8 s and os1_15_10 before 594.72 m, the PPO policy after". It is never called "per-CAV PPO headway policies".
  - **tail:** "the averaged action probabilities of 6 checkpoints of each PPO run".
  - **rep in X1:** "trained with a repeated-slowdown draw that contains X1's two-event structure".
  - **1B:** "with the V2V gate hold".

## What follows from each outcome (D10)

- **Incumbent:**
  - A finalist replaces v3w as the incumbent only if it is better than v3w in at least one cell (T1), harmed in neither, and wins T2 in at least as many cells as v3w on the same seeds.
  - If two finalists qualify, choose the one with more T2 cells; then the one with more learners passing T2, summed over the two cells; then the larger score against v3w at test.
  - Otherwise v3w stays.
- **Claim:** this round's T2 replaces round 1's for any thesis sentence, and round 1's T2 is reported beside it.
- **Closing:** if, in a cell where a 3E rule counts, neither v3w nor a finalist wins T2, the DRL claim against tuned rules closes in that cell on this plant (as confirmatory 3's [A3]). The negative result is reported. A cell where no 3E rule counts does not close by this rule.

## Statistic

The same as round 1, unchanged:
- effect = sign × median(P − O) / median(O) × 100 over paired seeds;
- percentile bootstrap of the paired differences, 20,000 resamples, denominator fixed;
- arm comparisons use the per-seed mean over 5 learners.

## Seeds, proposed for approval (block 7,440,000-999, V354)

| Use | Range | Count |
|---|---|---|
| Smoke, the seed of `c_train.py smoke`, used before | 7,419,899 | 1 |
| 3E-X1 and 3E-X2 tuning, only if D4 is approved | 7,440,740-779 | 40 |
| Validation | 7,440,800-839 | 40 |
| Test, used once | 7,440,840-879 | 40 |
| Band, used once | 7,440,880-899 | 20 |

- **Used so far in the block:** 000-074, 100-189, 200-239, 300-319, 340-359, 370-389, 400-439, 500-559, 600-609 and 700-739.
- **The proposed ranges are unused.** The review checked them against the 1,708 rows files under `v5b1_runs` and a `git grep` over 31 refs.
- The identity, replay and determinism checks re-run stored rows on their own seeds, so they create no new data. ahead's KILL re-runs 2 validation seeds traced.

## Compute

**Measured rates:**
- laptop, 31 workers: about 1,330 runs per hour (V425, V426);
- rented 2 × EPYC 7B13, 244 workers:
  - round 1's validation: 3,440 runs in 39 minutes;
  - its test and band: 3,540 runs in 38 minutes;
  - about 5,350-5,650 per hour, measured while round 2's 25 learners shared the CPUs (V449, V450).

| Step | Runs | Laptop hours | Rented hours |
|---|---|---|---|
| Validation: 89 arms (91 with D4) × 2 cells × 40 | 7,120 (7,280) | 5.5 | 1.4 |
| ahead's KILL: traced re-runs | 20 | 0.1 | 0.1 |
| Test: up to 34 arms (36 with D4) × 2 × 40 | 2,720 (2,880) | 2.2 | 0.55 |
| Band: up to 24 arms × 5 levels × 20 | 2,400 | 1.8 | 0.45 |
| 3E-X1 and 3E-X2 (D4): 2 × 40 generations × (24 + reference) × 16 seeds, plus the final pick | about 32,500 | 24 | about 3.5: set by 40 sequential generations, not throughput |
| **Total** | **about 12,300, or 44,900 with D4** | **about 9.5, or 34** | **about 2.5, or 6** |

On the laptop, 40 % CPU from 23:00 to 09:00 (V432) stretches these hours overnight. Runs at 6,000 take longer.

## Stop rules

- No change to the arms, opponents, checkpoints, readings or seeds after validation starts, except by a logged author decision, disclosed, with fresh seeds afterwards.
- A bug found after results: fix, re-run everything affected, log both outcomes.
- A trace can add an explanation; it cannot change the outcome of a reading. The one exception is ahead's pre-registered importance KILL.

## Disclosures

- **The cells' history on this plant (plant_c3):**
  - Confirmatory 3 won X2 by the tuned reading and closed X1 by its rule [A3] (V395).
  - X2 did not replicate on 20 fresh seeds: 1 of 5 policies cleared (V401).
  - The author then continued the DRL line (V411-V414). Round 1 tested both cells again with retrained policies, and v3w won T2 in both (V449). Round 1's protocol did not state that [A3] had closed X1.
  - Q2 is X2's fourth test on this plant and X1's third, each on fresh seeds. Earlier r2m3 plants tested both cells too (V359, V368).
- **Q2 and Q3 follow round 1's readings.** 3E was planned before round 1 (V413), but Q2 asks about v3w because v3w won T2 (V449). The band was chosen after the sweep's data (V419) and was not shown in round 1.
- **3E-T's search:**
  - It ran 40 of the 100 pre-registered generations (V443), and its convergence was not checked.
  - The 5 configurations re-run on all 40 seeds were shortlisted by losses from different seed windows. All 5 came from 2 of the 5 windows.
  - Its pooled result hides +3.2 % and +3.9 % delay at 5,250 and 5,500.
  - Confirmatory 3's grid forms were tuned per cell.
- **3E-X's reference is p333; 3E-T's is os1_15_10.** 3E-X starts from each cell's own-state form.
- **Training seeds:** every trained candidate shares v3w's training seeds (option A). A difference is the change, not the seeds, but 5 learners sample training noise only thinly.
- **Checkpoint selection** between u250 and u500 departs from "final policy only". It is applied to every learner alike. tail has no selection, so at validation it is compared without the in-sample gain its comparators carry.
- **Selection at validation:** 7 candidates × 2 cells at 95 %, without correction.
  - If no candidate differs from v3w, path (a) passes by chance about 2.5 % per candidate and cell, and path (b) almost never. So at least one of the 14 tests passes up to about 30 % of the time.
  - Advancing is not a finding; only the test is.
- **Harm is looser than round 1's.** Round 1 put out any candidate whose delay was clearly worse than the incumbent's. Here a clear delay loss under 2 % is allowed, matching path (b)'s allowance. On round 1's validation rows, res in X2 had delay −1.4 % [−3.0, −0.0] against v3w: out under round 1's rule, not under this one. Harm on close-following is new.
- **Noise floor:**
  - The delay limits and the counting filter are judged on point estimates. E2 (V435): the paired delay SD against os1_15_10 is 7-11 %.
  - At 40 seeds, the 2 % point rule passes a true tie about 86 % of the time and a policy truly 2 % worse about half the time, so it does not bound harm for a single policy.
  - With 4 of 5 policies and round 1's counting opponents, all 5 pass the delay limit about 75 % (X1) and 86 % (X2) of the time at a true tie.
  - The counting filter can flip near 2 %: os1_15_10 counted in X2 at round 1's test but not at its validation.
- **1B** acts through the gate hold at evaluation, as in training.
- **sw's** rule side is 0.8 s below 500 m and os1_15_10 on 500-594.72 m.
- **rep** has X1's structure in its training draw, so it is judged on fresh seeds only.
- **Teaching to the test:** the policies' reward still contains the judged 1-Hz flag (1D adds the 0.1-s braking charge). The counters outside the reward are reported.
- **Literature:** policy averaging, look-ahead inputs, annealing, gate masks and CMA-ES rule tuning are named families [VERIFY]. None is claimed as new.

## What this cannot show

- Any win holds for this uncalibrated SUMO model, these slowdowns, these demand levels and ideal V2V.
- A null on 7 candidates in one round does not show that no other change would help.
- Without D4, beating 3E-T does not show that a rule tuned per cell would be beaten. With D4, it shows this for one 40-generation search per cell. If that search has not converged, 3E-X is a lower bound on a per-cell tuned rule.

## Decisions for the author

| # | Decision | Recommendation | Why | Alternatives, and why not |
|---|---|---|---|---|
| D1 | Incumbent, and baseline v4 | v3w as the comparator, stored as baseline-v4 before validation: a tag, checkpoints u250-u500 and final with configs and input statistics, and round 1's rows | It beat baseline-v3 on T1 in both cells, and every candidate is one change against it. Today v3w exists only as run copies | baseline-v3: already beaten. No store: the comparator can change or be lost between rounds |
| D2 | What "better than v3w" means | delay path (a) **or** close-following path (b); harm at more than 2 % or 10 % | 1D and rep aim at close-following and robustness. A 10 % cut at delay within 2 % is a gain | delay only, as round 1: it rejects a pure close-following gain |
| D3 | Finalists | at most 2 | T1 m = 4 (98.75 %), T2 m = 6 (99.17 %) | 3: T2 m = 8, wider CIs at n = 40 |
| D4 | Per-cell 3E (3E-X1, 3E-X2), with p333 as the reference and 16 seeds per generation | **yes**, before validation | 3E-T will probably not count, so without D4, Q2 likely tests nothing new. The claim rules ask for the strongest tuned rule; confirmatory 3's forms were tuned per cell | 3E-T only: free, but Q2 likely void. Add g032i14 as a second 3E-T opponent (−9.2 % close-following at −0.6 % delay against os1_15_10 on tuning seeds): a post-hoc pick from 3E's final 5, a deviation from the prereg |
| D5 | Band | report-only profile, 20 seeds | Resampling round 1's rows: 3-13 % chance of "shown" at 40 seeds. It would also be v3w's second test | 40 seeds as a reading: 2,400 more runs for a likely miss, a disclosed second look. Drop the band: Q3 unanswered |
| D6 | Machine | rented, about 6 h of runs with D4 | 4× faster; no night limit; D4's sequential generations fit a big machine | laptop: about 34 h plus night slowdowns |
| D7 | Seeds | as in the table | Unused, inside the approved block | |
| D8 | v3w's checkpoints | re-chosen on this round's validation by the same rule; round 1's set reported beside | Same rule, same seeds for every learner | round 1's choice: made on other seeds |
| D9 | Test when no candidate advances | yes, for v3w (Q2) and the band | Q2 is the open claim question | no: Q2 waits for another round |
| D10 | What follows from each outcome | the rules in "What follows", fixed now | Round 1 left this open (round_1_result.md §7); deciding after the data is a hidden variant | the author decides after the test |
| D11 | Delay limit | keep the 2 % point rule (comparable with round 1), with a 5 % non-inferiority bound reported beside T2 | E2: the point rule passes a truly 2 % worse policy half the time | non-inferiority as the rule: 80 % power at a true tie needs about 90 seeds per cell at T2's level, so the test grows from 2,800 to about 6,300 runs (V435) |
| D12 | Splitting a 1B result into hold and mask | no; disclosed | Keep the round simple (V408) | a report-only arm v3w-gate (v3w with `gate_hold`) at validation: 800 runs |
| D13 | tail and sw (evaluation only, from V444's search) | keep both | No training; tail tests averaging against F2's drift, and sw a spatial operating map | drop either: less build and fewer null passes at validation |

E1, the 0.1-s safety meter (V434, V435), is not part of this round. It runs report-only on round 1's or round 2's stored test arms when the author picks a time and seeds.
