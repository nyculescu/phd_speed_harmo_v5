# Plan B protocol: perturbation resilience of v3w against every tuned non-learning controller (draft, rigor-first)

Draft for the author, 2026-11-08. Nothing here is approved. No Plan B data exist. Written from V478 and the record; every number marked "planning" comes from stored X1/X2 rows used only as variance inputs, never as evidence.

## 0. Status and the decisions it needs

Status: draft. It becomes binding when the author approves the decisions below, it is committed, and a ledger entry (V#) records the approval. Every stage below runs after that commit.

Angle: the claim an external examiner cannot break. So: few cells, one metric pair, one Bonferroni family, the strongest opponents the budget allows, side constraints as non-inferiority bounds, and a reading whose null was computed before data.

| # | Decision | Recommendation | Main alternative and why it is weaker |
|---|---|---|---|
| D-B1 | Seed block | Approve 7,480,000-7,480,999 with the partition in §6 | V354's remainder 7,440,920-999 (80 seeds) is too small for tuning plus n = 120 |
| D-B2 | Cells | Four candidate slowdown cells in a fixed priority order; the first two that pass the plant-only gates (§7) become the cells | Two cells picked now: cheaper by about 1,300 runs, but a cell that does not bind would waste the study |
| D-B3 | Intended use | After Stage A, amend the V&V record §1 to name the selected cells, with their verification evidence, before any opponent is tuned | Keep V462(4): every Plan B row then carries "outside the plant's stated intended use", and the claim sentence must say so |
| D-B4 | Opponents | 15 carried rules, per-cell grid re-selection, two CMA-ES searches per cell (close-following and delay objectives) to a convergence rule, a regime scheduler, and an MPC with a fitted model (§3) | Drop the delay-objective search or the MPC with a disclosure: dropping 3E-D saves 35-45 % of all runs, but delay is the binding metric (§8), so a delay-tuned opponent is what an examiner would ask for |
| D-B5 | Convergence rule | Check every 10 generations on a separate 40-seed check set; stop at the first check from generation 40 on where the incumbent improved by less than max(1.0 point, 2 SE) over 20 generations; cap 150 (§3.3) | A fixed 40 generations as in round 2: both round-2 searches were still falling there (round_2_result.md:9) |
| D-B6 | Reading rule | Per cell: delay and close-following both better than every opponent (CI lower bound above 0 at 1 − 0.05/m), plus non-inferiority on flow (−1 %) and robust hard braking (−15 %), collision and emergency limits, and 4 of 5 learners consistent (§8). No counting filter | Round 2's T2: delay is only a 2 % limit there, and its counting filter removes opponents (round_2.md:66-68), so it does not match V478's claim |
| D-B7 | n | 120 evaluation seeds per cell, the same seeds in every cell and in steady traffic | n = 80 (power reader's choice): 4,360 runs fewer (about 1.5 h, $0.45-0.57); planning power in X2-like cells 36 % instead of 64 % (§8.5) |
| D-B8 | Budget | Up to about 272,000 runs, 89-111 h and $27-35 on the V475 rental at the 150-generation cap; about 92,000 runs, 30-38 h and $9-12 if every search stops at 40 (§9) | |
| D-B9 | Place in the thesis | A ledger entry that makes Plan B chapter 6 and moves "Learning or adaptation?" (outline_v1.md:66) | Leave the outline: then V478's "6. Plan B" and outline_v1 disagree |
| D-B10 | Close-following measure | Keep `ttc_net` (1-Hz TTC < 3 s, vehicle-seconds) and disclose that it is a reward term | A measure outside the reward: none exists, TTC < 2 s and < 1.5 s are near subsets of the rewarded event (claim_review_round2.md:30) |

Effort and ultracode for the next steps follow the CLAUDE.md table: this protocol's design review is Extra High with ultracode on; the build is High; the checkpoint before Stage D is High with ultracode on.

## 1. Question and claim sentence

Question. Under realistic perturbations that v3w never met in training, does v3w have less door-to-door delay and less close-following than every tuned non-learning controller, at a stated hard-braking cost?

The claim is conditional (V478, the author's principle on conditional advantages). It speaks of the named cells only, at 5,300 veh/h, on plant_c3.

Sentence if the cell reading passes in cell P (W, §8) and the resilience reading passes too:

> On the simulated r2m3 freeway, under perturbation P (a [spec], not in the training draw), the per-CAV DRL headway policy (5 independently trained learners, arm mean) had x % [CI] less door-to-door delay and y % [CI] less close-following than every one of k tuned non-learning controllers, including per-cell CMA-ES re-tuned rules, a regime scheduler and a fitted-model MPC. Served flow was not worse by more than 1 %, and its robust hard-braking count was at most z % [CI] higher than the worst opponent's. v3w also lost less delay to the perturbation than every controller did.

Sentence if W passes and the resilience reading does not: the same first two sentences, then "The advantage is not shown to be specific to the perturbation; v3w also leads in steady traffic (report-only)."

Sentence if no cell is W (null):

> Under the pre-registered perturbations P1 and P2, v3w was not shown to have both less delay and less close-following than every tuned non-learning controller. The closest opponents were [names] ([metric], [effect, CI]). This is a null result, reported as one (V243, V456).

Sentence if a cell is L: "In P, v3w was worse than [opponent] on [metric] ([effect, CI])." It stands beside any W in the other cell.

Words never used (outline_v1.md:55; V462(3)): "proven", "safe", "verified and validated" before the V&V review, any field or calibrated-traffic claim, any win on a measure not pre-registered here. Every sentence also states: simulation only, one plant, plant within its intended use as amended (or "outside the stated intended use" if D-B3 is declined).

## 2. Closures and intended use

### 2.1 X1 (V395, [A3]) and X2 (V466)

- [A3] closes "this DRL line ... on these slowdowns": no further training, tuning, plant change or seed round (confirmatory_3.md:132). V395 applied it to X1. V466 and round_2_result.md:432 close X2 for DRL on this plant.
- Plan B runs nothing in X1 or X2. No v3w run, no rule tuning, no new seed round there. The only X1/X2 runs are identity replays of stored rows at the run commit (§7, check A2). They read bit identity only, as round 2's check 2 did, and print no performance field.
- The stored X1/X2 rows (round 2 test, S0/S1) are not read as evidence (V478). They were used only as variance inputs for the power planning in §8.5. This is disclosed.
- No plant change: Plan B uses the existing `slowdown` kind with new parameters (perturb.py:113-125). No plant file, perturb code or fleet code changes. The new harness code (tuning conditions, scheduler, MPC, reading script) is not plant code. The identity replays prove the plant is unchanged.
- No retraining (V478). v3w's checkpoints stay as they are.
- Cell boundary rule (new, fixed here because the record defines none): a Plan B cell must use an edge other than X1's (4) and X2's (3), and lie outside v3w's training draw in at least one parameter by a clear margin. So no Plan B cell can be read as an X1 or X2 seed round.
- Claim review D1 and D8 (claim_review_round2.md:34-40, 83-89) need no decision for Plan B, because Plan B makes no X1/X2 rows. The ledger entry approving this protocol should say so.

### 2.2 Intended use (V462(4))

- The V&V record's use covers steady traffic and "tapered slowdowns (X1, X2)" at 4,090-6,000 veh/h with 50 % ALKS (plant_vv_record_v0.md:9-11). V462(4) labels other slowdown parameters (condition T), H1 and H2 as outside it. So every Plan B cell is outside the use as written.
- The rigor-first route (D-B3): Stage A collects the verification evidence per cell (§7: spec trace, PR-09, PR-17, PR-25, PR-28, PR-24 counter traces, drain). The author then decides one amendment of §1 that names the selected cells, before Stage B. The amendment adds only those cells and departs from V462(4)'s label-not-add rule, so the ledger entry must say both.
- All Plan B cells are tapered speed-limit drops on one main edge at 5,300 veh/h with 50 % ALKS. They avoid every explicit "Not for" item: no V2V loss (outage), no lane closure (lateral or merge-conflict safety), no change of driver mix or human adaptation.
- If the author declines the amendment, every Plan B row and sentence carries "outside the plant's stated intended use" (V462(4)).
- The V&V record is an unreviewed draft (6 met, 13 partial, 7 gap, 2 limit of 28; plant_vv_record_v0.md:3). "Verified and validated" stays out of every sentence until the review (V462(3)).

## 3. Policy under test and opponents

### 3.1 Policy under test

- v3w only: learners w0u250, w1u500, w2u250, w3u500, w4u500 (baseline_v4 policies C0-C4), run exactly as in round 2's test job (`round2/test/job_6c49e7e.json`) except the perturbation and the seeds: the same action mode, hold and decision settings and plant_c3 (training used hold 10 s and decision 5 s, baseline_v4/policies/C0_config.json; Stage 0 checks that the job file matches).
- The arm value per seed is the mean over the 5 learners (round_2.md:263-268).
- Disclosed: the checkpoints were chosen on round 2's X1/X2 validation seeds (round_2.md:256-259). No Plan B data enter that choice.
- tail and sw are not run. They are the same line of evidence as v3w, and adding them adds comparisons with no independent support.

### 3.2 Opponents (the set O_c in cell c)

Every opponent counts in the reading. There is no counting filter (round 2's filter removes opponents, which would make "every tuned controller" easier).

| Group | Members | How tuned | Seeds |
|---|---|---|---|
| Carried rules (15) | p333, z33133, r4a1, lr400_13_2, lr1000_16_2, lr1000_10_1, lr400_16_1, a4400_10_1, os0_10_10, os1_15_10, os1_10_0, copy, 3E-T, 3E-X1, 3E-X2 | As stored (docs/research/baseline_v3/opponents.json; round 2). Tuned for X1, X2 or condition T, not for Plan B cells. Run unchanged | none new |
| Per-cell grid picks (up to 8) | Each form's best admissible rule from confirmatory 3's 70-rule grid, plus the cell's delay opponent | Confirmatory 3's procedure (confirmatory_3.md:48-64) on the new tuning seeds, per cell and in steady traffic | 7,480,180-219 |
| 3E-C_c | CMA-ES ZoneOwnState rule (20 parameters), close-following objective | §3.3, per cell | search 100-139, check 140-179 |
| 3E-D_c | The same family, delay objective | §3.3, per cell | search 100-139, check 140-179 |
| ASCH | Regime scheduler, one controller for every cell and steady traffic | §3.4 | 7,480,220-259 |
| MPC-F | MPC with a fitted cost model | §3.5 | fit 260-299, validity gate 300-329 |
| No control | | Reported in every table; not in O_c | |

Duplicates collapse: a grid pick equal to a carried rule is run once and counted once.

Disclosed, favouring the rules: per-cell tuned rules know which perturbation will happen (informed opponents); v3w does not. The LocalRule-type rules read roadside speeds 400-1,000 m ahead; v3w sees its own 200-m bin and a leader within 100 m (b_env.py:896-952, 991-1015). copy was traced from DRL policies.

Disclosed, favouring v3w: 3E-T stopped at 40 of 100 generations (V443) and 3E-X1/3E-X2 were still falling at 40 (round_2_result.md:9). They are carried as they are; the per-cell searches are where convergence is required.

### 3.3 The per-cell CMA-ES searches (3E-C and 3E-D)

Code: docs/research/round2/cma2.py extended to the new conditions (its `--cond` list and common.COND), with the checkpoint and stopping logic below. A tuning-harness change, not a plant change; it gets unit tests and the adversarial review.

| Item | 3E-C_c | 3E-D_c |
|---|---|---|
| Family | ZoneOwnState, 5 zones × 4 parameters (cma2.py:39-60) | same |
| Search | Diagonal CMA, population 24, σ0 0.25, 16 seeds per generation from the 40-seed search pool (moving window) | same |
| CMA seed | 20261108 + cell index | 20261118 + cell index |
| Reference | p333 on the same seeds | p333 |
| Loss | Pooled TTC-seconds change in % + 10 per % of delay above +1 % + 5 per collision above the reference | Delay change in % + 10 per % of close-following above the reference + 5 per collision above the reference |
| Admission (check seeds) | Delay at most +2 % over p333 (point); collisions at most p333's + 1 | Close-following at most p333's (point); collisions at most p333's + 1 |

Changes from round 2, with reasons: the delay penalty is 10 per % (round 2: 5) because round 2's X1 search drifted past the admission bound and its pick came from generation 3 (V461); admission and incumbent choice use a separate check set because search losses were optimistic (V448).

Convergence and stopping rule:

1. At generations 20, 30, 40, ... re-run on the 40 check seeds the 5 best distinct configurations since the last check (ranked by loss minus the generation median, cma2.py:293-317), the current CMA mean, and the incumbent.
2. Incumbent = the admissible configuration with the lowest check loss so far.
3. Stop at the first check g ≥ 40 where L(g − 20) − L(g) < δ, with δ = max(1.0 loss point, 2 × the bootstrap SE of that paired difference over the 40 check seeds).
4. Cap: 150 generations. A search that reaches the cap without meeting step 3 is marked "not converged at cap". The opponent still counts, and the claim sentence must say so.
5. The opponent is the incumbent at the stop. Its check-seed rows are not evidence.

### 3.4 The regime scheduler (ASCH)

V457 asks for "a non-learning adaptive scheduler". The record does not say how it differs from the state-feedback rules. Here it is defined as a gain-scheduling supervisor, to make the difference concrete:

- One controller for every condition. It does not know the cell.
- It reads the existing roadside bins (LocalRule._ahead, b_env.py:991-1015) in three detector zones: before merge 1, between the merges, after merge 2.
- Library: the steady-tuned grid pick, and each cell's 3E-C rule.
- Rule: if a zone's mean speed stays below θ for τ seconds, switch to the rule tuned for a disturbance in that zone; switch back when it stays above θ + h for τ seconds.
- Tuning: θ ∈ {40, 55, 70} km/h, τ ∈ {10, 30, 60} s, h ∈ {5, 15} km/h, 18 configurations, on 40 seeds in each cell and in steady traffic. Pick: lowest pooled delay among configurations whose close-following is at most p333's in every condition (point).
- It differs from LocalRule, AdaptiveOn4a and OwnState because it switches whole tuned parameter sets by a detected regime, not one headway by one threshold.

### 3.5 The fitted-model MPC (MPC-F)

- Port of `vsl_lab/jobs/mpcf.py` on `claude/v5b-core` (MPC-F, BN4 meter scheduling). It never gets the true model.
- Actions: the ASCH library plus p333 (at most 4 rule settings), applied network-wide. Every 30 s, choose the action with the lowest predicted cost over the next 300 s.
- Model: an MLP (2 × 64, tanh) predicting the 300-s cost (delay in veh-s + 10 × TTC < 3 s vehicle-seconds) from roadside zone speeds and counts, accelerating-lane counts and the insertion queue.
- Data: runs with randomly held actions (30-120 s holds) on 40 seeds in each cell and in steady traffic, 2 schedules per seed.
- Validity gate, fixed now: on 30 seeds per condition, MPC-F's realised cost must not exceed that of its best single fixed action (point). If it fails, MPC-F is a failed build: it is omitted from O_c, and the omission and the gate's numbers are disclosed.
- Known limit: a data-driven model captures capacity-drop hysteresis only as far as the held-action data show it (docs/paper1/plan.md:515 warns about straw-man MPCs [VERIFY the source cited there]). METANET was stopped earlier (D5.5) and is not used.
- If the author declines the build (D-B4), the omission is disclosed (CLAUDE.md; confirmatory_3.md:40).

## 4. Perturbation cells

Base for every cell: plant_c3 (r2m3, 3 main lanes, two on-ramps), 5,300 veh/h, 50 % ALKS, the existing `slowdown` kind (one main edge, linear 20-s taper on the 0.1-s clock, instant return; perturb.py:113-125), warm-up 300 s, run end 1,800 s. Edge positions from corridor.py:24, 45-47: edge 2 = 3,000-3,500 m (upstream of merge 1, mainline only, about 70 % of demand), edge 5 = 6,300-6,800 m (exit, downstream of edge 4).

v3w's training draw (perturb.py:35-39): no event in one third of episodes; otherwise one slowdown on edge 3, 4 or 5 at 25-60 km/h for 60-180 s, starting 400-1,200 s, at constant demand 4,500-6,000.

| Priority | Cell | Edge | Limit | Duration | Start | Outside training draw by | Distinct from X1/X2 by |
|---|---|---|---|---|---|---|---|
| 1 | P-long: long downstream restriction | 5 | 30 km/h | 600 s | 600 s | duration (600 > 180 s) | edge |
| 2 | P-up: deep upstream restriction | 2 | 20 km/h | 180 s | 700 s | edge (2 not in {3, 4, 5}) and limit (20 < 25) | edge |
| 3 | R-deep: deep downstream restriction (reserve) | 5 | 20 km/h | 180 s | 700 s | limit | edge |
| 4 | R-uplong: long upstream restriction (reserve) | 2 | 30 km/h | 600 s | 600 s | edge and duration | edge |

Selection rule, fixed now: Stage A runs all four. The first two in priority order that pass gates G1, G2 and G4 (§7) become the Plan B cells; m = their number. If only one passes, m = 1. If none passes, Plan B stops before any v3w run and the null-by-design is reported. No v3w row exists at that point, so this choice uses plant behaviour only.

Physical meaning: a temporary speed restriction on one section, such as a work zone or a reduced limit near an incident. The parameters were chosen to bind the plant and to lie outside the training draw. They are not taken from a measured site, and no literature on typical work-zone limits or durations has been read for this draft [VERIFY before citing any].

Expected binding, my rough estimate only: at 20-30 km/h a lane's car-following capacity falls to about the per-lane demand, which is why X1 (25 km/h) and X2 (30 km/h) form queues. Edge 2 carries only the mainline share, so P-up may not bind. G1 decides; this estimate is not evidence.

Inside or outside the intended use: outside as written for all four (§2.2); inside only if D-B3 amends §1 for the selected cells.

## 5. Metrics

| Role | Measure | Field | What it counts |
|---|---|---|---|
| Primary | Door-to-door delay | `all_delay` | Vehicle-seconds in the network and in the insertion queue minus distance / (100 km/h); unfinished vehicles and the insertion queue included (plant_sweep.py:336) |
| Primary | Close-following | `ttc_net` | 1-Hz samples with TTC < 3 s, network-wide (E30 + out_E30; plant_sweep.py:331, b_env.py:417-424). A reward term: disclosed |
| Co-headline | Served throughput | `passed` | Vehicles entering edge 4. For P-long the counting point is upstream of the slowdown and sees its spill-back |
| Always reported | TTT | `N` | Vehicle-seconds in the network plus the insertion queue, fixed window |
| Side constraint, stated cost | Robust hard braking | m_peak_car + m_peak_alks, bins 2 and up | Braking events (a ≤ −3.0 m/s² until the first step above) peaking at −4.0 m/s² or harder, cars and ALKS, step resolution (measure.py:17-21, 129-160). Reported raw and per vehicle-km |
| Side constraint | ALKS past their limit | m_peak_alks bins 4-7 | ALKS events peaking between −5 and −9 m/s² |
| Side constraint | Collisions | `collisions` | New SUMO collision pairs per step, which include minGap intrusions and the warm-up; `contact_steps` reported beside it |
| Side constraint | Moving full-emergency ALKS events | `alks_full_moving` | −9 m/s² events while moving, apart from lane-end creep (V377) |
| Validity | Teleports, drain | `teleports`, `finished_pct`, pending vehicles | `teleports` is 0 by construction (time-to-teleport −1), so drain is checked from the per-minute series |

Not used for any reading: the −4.5 m/s² counts (`events_ge45`, `b45_step`), which sit on the car and ALKS braking limit and select by speed (s01_result.md:287-324).

Reported, no reading: TTC < 2 s and < 1.5 s, DRAC, `b3_step`, `gap25`, ramp delays, lane-end stops by road (PR-28).

## 6. Seeds

Proposed fresh block for the author's approval: 7,480,000-7,480,999. The record reader found no keyed seed at or above 7,472,000 in the stored files and no 7,48x,xxx in any git ref or worktree file (read_record/seed_scan_summary.txt). It collides with no derived stream (kind random uses seed + 910,000, which is not used here).

| Seeds | Stage | Use |
|---|---|---|
| 7,480,000-009 | C | Smoke, traced vs untraced, T3 on the run machine |
| 7,480,010-049 | A | Tool checks and plant gates for the four candidate cells and steady traffic |
| 7,480,050-099 | A | Reserve for tool-check re-runs under the bug rule |
| 7,480,100-139 | B | CMA-ES search pool |
| 7,480,140-179 | B | CMA-ES check set (admission, incumbent, stopping rule) |
| 7,480,180-219 | B | Grid re-selection, per cell and steady |
| 7,480,220-259 | B | ASCH tuning |
| 7,480,260-299 | B | MPC-F data |
| 7,480,300-329 | B | MPC-F validity gate |
| 7,480,330-399 | | Reserved |
| 7,480,400-519 | D | Evaluation, n = 120, used once, the same seeds in every cell and in steady traffic |
| 7,480,520-999 | | Reserved (a later confirmatory round needs its own approval) |

A re-run under the bug rule uses the same seeds and is not a new round.

## 7. Tool checks and smoke checks (criteria fixed before they run)

Stage A runs no v3w. Arms: no control and the 15 carried rules.

| Check | What | Pass criterion |
|---|---|---|
| A1 spec trace | 0.1-s trace of the edge limit on 3 seeds per cell | Reaches the target at t0 + 20 s (± 0.1 s), holds, returns at t0 + duration |
| A2 identity | Stored S, X1 and X2 rows replayed at the run commit, 3 seeds × 2 arms each | Bit-identical rows; only identity is printed |
| A3 determinism (T3) | Same seed twice, each cell, 2 seeds × 3 arms | Identical rows |
| A4 equal before onset | Per-minute series of each cell against steady traffic, same seed and arm | Identical up to t0 (perturb.py:1-2) |
| G1 perturbation binds (T1) | No control and p333 delay in the cell against their own steady rows, 40 seeds | Median paired increase ≥ 10 % with the 95 % CI excluding 0, for both |
| G2 control matters (Early KILL) | Best carried rule against no control in the cell, 40 seeds | At least one carried rule has ≥ 10 % less delay with the 95 % CI excluding 0 |
| G3 mechanism (T2) | Best carried rule in the cell against the best in steady traffic | Report-only (CLAUDE.md T2) |
| G4 artefacts | (i) PR-09: 1-Hz braking within 5 % of step braking for every arm; (ii) drain: after the event ends, vehicle count and insertion queue fall within 300 s, and no vehicle stands still for more than 300 s outside a queue (traced on 3 seeds); (iii) collisions and contact steps not above steady traffic's + 1 per run for p333; (iv) lane-end stops by road reported (PR-28) | All of (i)-(iii) |
| A5 counters | PR-24 counter traces for `ttc_net`, the braking peaks and `passed` on 2 seeds | Trace counts equal the row counts; no counter calls CavEnv._x (V386) |

G1's null: under a sign flip of the paired differences its CI excludes 0 at the nominal 5 % rate; the power reader found the statistic near nominal from n = 40 (read_power/power_tables.md). A cell that fails G1, G2 or G4 is not used and is reported with its rows.

Stage B checks: unit tests of the extended cma2 on planted losses (the stopping rule fires on a planted plateau and not on a planted slope); ASCH switch logs on 2 seeds; MPC-F's validity gate (§3.5).

Stage C smoke on 7,480,000-009, after the opponents are frozen:

- every row carries cell spec, controller id and hash, learner id, seed and commit;
- `pert_log` shows each event at its set times;
- traced rows equal untraced rows (V386); pack-on rows equal pack-off rows (measure2.py smoke);
- v3w policy hashes equal the baseline_v4 checkpoints;
- the reading script runs end to end on the smoke rows.

The smoke script prints pass or fail only. No performance field of any arm is printed or read.

Reading-script unit tests on planted rows (committed before Stage D): a planted 10 % win on every opponent gives W; identical rows give T with a sign-flip false-W rate of 0; a planted 3 % delay loss against one opponent gives L; a planted 20 % braking cost gives "metric win, side-constraint failure"; one bad learner still gives W, two do not.

## 8. Statistics and the reading

### 8.1 Statistic

For opponent o and measure k in cell c: effect = s_k × median_i(P_i − O_i) / median_i(O_i) × 100 over the paired seeds i, with s_k chosen so that positive means v3w is better. P_i is the arm mean over the 5 learners. Percentile bootstrap, 20,000 resamples of seeds, one index matrix for every comparison, denominator fixed at the observed median, rng seed 20261108 (round_2.md:263-268, with a new rng seed).

Bonferroni: m = the number of selected cells (2, or 1 under §4's rule). Two-sided intervals at 1 − 0.05/m, read at percentiles 2.5/m and 100 − 2.5/m (round_2.md:192-194). Inside a cell, "better than every opponent on both measures" is an intersection over opponents and measures, so it needs no further correction. Every reading that feeds a sentence uses this level (V467).

### 8.2 Cell reading

Cell c is **W** if, against every opponent in O_c:

1. delay: lower bound > 0;
2. close-following: lower bound > 0, and the median paired reduction is at least 20 samples per run (T2's floor, round_2.md:199-202);
3. flow: lower bound > −1 % (non-inferiority);
4. robust hard braking (raw counts): lower bound > −15 % (non-inferiority);
5. collisions: median paired difference at most +1 per run; moving full-emergency ALKS events: at most the opponent's + 5 % or + 5 per run (T2);
6. at least 4 of 5 learners have point estimates > 0 on delay and close-following against every opponent;
7. no v3w row fails the drain check.

Cell c is **L** if, against any opponent, delay is more than 2 % worse by point with the 95 % upper bound below 0, or close-following more than 10 % worse by point with the 95 % upper bound below 0 (round 2's harm rule, read at 95 % so that harm is not hidden; round_2.md:172-174).

If 1 and 2 hold and any of 3-7 fails, the cell is reported as "metric win, side-constraint failure", with no claim sentence.

Otherwise the cell is **T** (no difference shown).

The claim passes if at least one cell is W and no cell is L. If both are W, the sentence may say "in both cells".

### 8.3 Resilience reading (secondary, fixed sequence)

Only in a W cell, at the same level 1 − 0.05/m, so the family error stays at 5 % (fixed-sequence testing).

For each opponent o and k in {delay, close-following}: resilience effect = median_i[(O_c,i − O_S,i) − (P_c,i − P_S,i)] / median_i(O_c,i − O_S,i) × 100, where S is steady traffic on the same seed and each controller runs as tuned for cell c (V343: "each controller's loss against its own run without X").

Pass: lower bound > 0 against every opponent, for both measures. Only then may the sentence say the advantage is specific to the perturbation, or use the word "resilience". Its power has not been computed: no stored v3w rows pair steady and perturbed runs per controller. V395 saw v3w's TTC edge in steady traffic too (from medians, not a test), so this reading may fail.

### 8.4 No control and steady traffic (report-only)

- No control is in every table, never alone. The V459 no-control bar (delay ≥ 10 % lower with the CI excluding 0, close-following not harmed under the harm rule) is read per cell at 1 − 0.05/m and reported. If close-following against no control is shown worse, the claim sentence must say so (in X1 it was: s01_result.md §6.1).
- Steady traffic at 5,300 on the evaluation seeds: the full operating map, report-only.
- Every cell: the full operating map, each opponent × measure, with the 95 % and the Bonferroni interval and the V462(1) tile.

### 8.5 The null and the power (planning, from stored X1/X2 rows at 5,300)

These numbers resample the 40 stored seeds with all 14 stored rules (read_power; this draft's rule_power.py). They are planning inputs only. New cells may behave like neither X1 nor X2, and the re-tuned opponents are likely stronger than the stored ones.

§8.2 rule, items 1-4 and 6 (braking on raw counts; item 5, collisions and emergency events, and item 7 not simulated), m = 2, 400 simulated studies per row (200 under the global null), 4,000 inner resamples (draft_rigor_calc/rule_power.py, rule_power.json):

| Scenario | X1-like n = 80 | X1-like n = 120 | X2-like n = 80 | X2-like n = 120 |
|---|---|---|---|---|
| Stored effects | 94 % | 99 % | 36 % | 64 % |
| Effects × 0.75 | 84 % | 97 % | 15 % | 36 % |
| Closest opponent's delay null (false W) | 0.8 % | 1.8 % | 0.8 % | 0.3 % |
| Global sign-flip null (false W) | 0 % | 0 % | 0 % | 0 % |

Cross-check: read_power's W3 alone at m = 2 (power_all.json) gives 94 % (X1) and 40 % (X2) at n = 80, which agrees within simulation noise. With 400 studies the noise is about ± 2-5 points. The nominal one-sided rate per comparison at m = 2 is 1.25 %; the 1.8 % (X1, n = 120) is within noise of it (SE about 0.7 points).

Reading of the table:

- The null holds: under the global sign-flip null the rule passes in 0 % of simulated studies. With only the closest opponent's delay null, it passes in 0.3-1.8 %, close to the nominal 1.25 %.
- In the stored data, the floor, flow and braking items never bound. Learner consistency cost at most about 4 points. Collisions and emergency events (item 5) were not simulated. So, at these margins, the simulated side constraints keep the claim honest and still reachable.
- Delay is the binding measure. Close-following almost never binds in X1-like cells.
- In X2-like cells a null is likely at any affordable n. That outcome is reported as a null.
- Going from n = 80 to n = 120 costs 4,360 evaluation runs (40 seeds × 109 runs; 1.4-1.8 h, $0.45-0.57).

## 9. Stages, run counts, time and cost

Rate: 2,450-3,050 runs per hour on the V475 rental (EPYC 7702, 59 workers). 2,450 is the measured rate of the X1/X2 rows at 5,300 (read_power, st mtimes); 3,050 the top of V475's mix. Price $0.10-0.13 per 1,000 runs (V475). Setup about 6 % on top. The CMA rate on 5,300 rows is not measured; it is assumed equal.

| Stage | What | Runs |
|---|---|---|
| 0 | Approval, build, unit tests, adversarial review, frozen run commit | 0 |
| A | 4 cells + steady × 40 seeds × 16 arms; traces, T3, identity | about 3,290 |
| B1 | Grid re-selection: 69 rules × 40 seeds × 3 conditions, plus no control | about 8,400 |
| B2 | 4 searches × (384 per generation + 240 per check) + references | 64,480 (G = 40), 162,400 (G = 100), 244,000 (G = 150) |
| B3 | ASCH: 18 configurations × 40 seeds × 3 conditions | 2,160 |
| B4 | MPC-F data and validity gate | about 690 |
| C | Smoke | about 200 |
| D | 120 seeds × 109 runs (2 cells × 33 arms + steady 43 arms) | 13,080 |

| Every search stops at | Total runs | Rental hours (+6 % setup) | Cost |
|---|---|---|---|
| 40 generations | about 92,300 | 30-38 h (32-40 h) | $9-12 |
| 100 generations | about 190,200 | 62-78 h (66-82 h) | $19-25 |
| 150 (cap) | about 271,800 | 89-111 h (94-118 h) | $27-35 |

The searches are 70-90 % of all runs. Four searches run together give 1,536 runs per generation round, about 30-38 min, so generation barriers leave little idle time. A larger rental such as V461's 122-worker instances cuts wall time at about the same price per run (the V461 rate of about 6,400 runs/h for two searches is a derivation, not a measurement).

Laptop: Stages A and C fit (about 2.6 h by day at 1,330 runs/h, V425-V426). Stages B and D do not, given the 40 % night cap (V432). Each stage runs on one platform (V436).

Build time (Claude, my estimate, uncertain): cma2 extension with checkpoints and tests a few hours; ASCH 50-100 lines plus tests; MPC-F port about a day; reading script and planted-row tests a few hours. Author time: the decisions in §0, the amendment after Stage A, the opponent freeze after Stage B.

Order and gates: 0 → A → amendment decision → B → opponent freeze (committed list with hashes) → C → D from a frozen worktree at the run commit (one platform, T3 there first) → E: the committed reading script runs once.

## 10. What is reported in every outcome

- The claim sentence for the outcome (§1), at the Bonferroni level, with the cell specs.
- Per cell and in steady traffic, the full operating map: every opponent × every measure in §5, effect, 95 % and Bonferroni intervals, V462(1) tile. No control and p333 never alone.
- The resilience table (§8.3) in W cells; the no-control bar (§8.4).
- The stated braking cost: the worst robust-braking effect over all opponents, with its interval, raw and per vehicle-km.
- Opponent provenance: each search's loss trace, checks, stopping generation, "converged" or "not converged at cap"; grid picks; ASCH configuration; MPC-F's validity gate result or the omission.
- Stage A gate results for all four candidate cells, including the ones not used.
- The planning null and power (§8.5) beside the result, with the note that they came from X1/X2 rows.
- Disclosures: X1/X2 closures and that Plan B ran nothing there; the intended-use amendment or the label; v3w's checkpoint selection on X1/X2 validation seeds; the reward overlap of `ttc_net` and 3 m/s² braking; informed per-cell opponents; the look-ahead difference; 3E-T and 3E-X carried as lower bounds; `collisions` counts minGap intrusions; teleports disabled; no retraining.
- Ledger: every run of every stage, including failed, crashed, re-run and abandoned ones, with commit, platform and seed range. A null is reported as a null (V243, V456).

## 11. Deviations policy

- Before Stage A: changes go into this draft and need the author's approval.
- After approval and before Stage D: any change gets a ledger entry with its reason before the affected stage runs, and is listed in the report.
- After the first Stage D run: no change of cells, opponents, measures, margins, n or reading. The only allowed change is the bug rule: fix, re-run everything affected on the same seeds and commit-tagged, log and report both outcomes.
- A crashed run is re-run on the same seed and commit and logged as such.
- A platform change mid-stage voids that stage's rows; the stage re-runs on one platform (V436, V465).
- Nothing is committed in the frozen run worktree while a stage runs.
- If a search hits the cap, that is not a deviation; it is reported as §3.3 says.

## 12. Risks and limits

- Every cell is outside the intended use as written. The amendment is decided after X1/X2 results were known, though before any Plan B data. An examiner may still see it as moving the goalposts. The evidence per cell and the ledger entry are the answer.
- The cells may not bind (P-up especially), or control may not matter in them. The reserves and the gates handle this, but two cells on edge 5 would be correlated and narrow.
- New cells may look like X2, where the planning power is low. A null is then likely and is still a valid chapter.
- Converged per-cell opponents, a delay-tuned search, ASCH and MPC-F are stronger than anything v3w met in round 2. Planning power at 0.75 × the stored effects already falls (§8.5).
- The stopping rule's δ uses a noisy check loss. Selecting the minimum of noisy estimates biases the incumbent's check loss downwards. The cap bounds the cost; the bias is disclosed.
- The median statistic is lumpy when per-seed differences have gaps (read_power results.md §1). Its bounds depend on B; B and the rng seed are fixed here.
- The resilience reading has no power estimate.
- The MPC-F port is a build risk, and its validity gate may remove it. A failed gate is disclosed, not hidden.
- `ttc_net` and 3 m/s² braking are reward terms (claim_review_round2.md:30). A win on them is partly a win on what the policy was trained to minimise.
- Lane changing and ramp-2 lane-end behaviour are not validated (PR-08 limit, PR-28 gap). P-long's spill-back reaches merge 2.
- One plant, one demand level, synthetic traffic. No transfer to field traffic is claimed.
- My estimates (binding at 20-30 km/h, build times, the CMA rate) are not measurements.
