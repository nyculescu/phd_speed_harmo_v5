# Plan B protocol, draft (breadth angle): v3w under three perturbation families, against every tuned non-learning controller

Status: DRAFT, 2026-11-08. Not approved. No Plan B data exists. Written from the record (V478 and earlier) and three read-only reader reports in this scratchpad folder (`read_record/`, `read_plant/`, `read_power/`). Sources are given as file:line or V-number. My own estimates are marked "(my estimate)". Literature not read in full is marked [VERIFY].

Angle of this draft: contribution first. Three distinct, realistic perturbation families, each its own pre-registered cell. One per-cell reading ladder. An operating map of win, tie and loss per cell and opponent. A resilience row (V343) and an adaptation-gain row (confirmatory 3's form). Bonferroni across cells. It is meant to stay the simplest design that answers "what is your improvement?".

## 0. Status and decisions needed from the author

Nothing runs until every row below is decided and logged (one V-number per decision, committed the same turn).

| # | Decision | Recommendation | Main alternative and why it is weaker |
|---|---|---|---|
| D-B1 | Seeds | Approve the new block 7,480,000-7,480,999 with the partition in §6 | The rest of V354's block (7,440,920-999, 80 seeds) is too small for tuning plus 80 evaluation seeds |
| D-B2 | Cells | L60 (corridor-wide temporary limit), SLOW50 (slow heavy vehicles), SURGE (demand surge), §4 | Reusing H1 (truck, 50 km/h every 300 s) as is: parameters fixed long ago, but its effect looked mild (no control +8 % delay at 5,300, medians, `baseline_v3/decide3_map.csv`), so it may fail the perturbation-matters gate |
| D-B3 | Intended use | Amend the V&V record §1 before any Plan B data to add the three kinds, each with its own verification (§2.3, §7) | Keep §1 and label every Plan B row "outside the plant's stated intended use" (V462(4)): the whole contribution would then rest on labelled rows |
| D-B4 | Opponents | The 15 rules already tuned on this plant, per-cell picks from confirmatory 3's grid, a per-cell CMA-ES rule for close-following (3E-c) and one for delay (3E-Dc), and a scheduler (SCH-c); MPC omitted with a disclosure (§3) | 3E-c only: about 45 % cheaper, but the "less delay" half would never meet a rule tuned for delay |
| D-B5 | MPC | Omit, disclosed with the reasons in §3.4 | Port MPC-F from `claude/v5b-core` (about a day of build time plus a few hundred runs per cell, my estimate): stronger answer to "did you compare with MPC?", real build risk |
| D-B6 | 3E convergence | Plateau rule checked every 10 generations, minimum 40, cap 100 (§3.3) | A fixed 40 generations as round 2: both 3E-X searches were still falling at 40 (V461) |
| D-B7 | Claim rule | Arm-level ladder N / C / D, plus an R tag, Bonferroni m = 3 cells, fixed sequence inside a cell (§8) | T2's "at least 4 of 5 policies": stricter, and X2 failed it in round 2; reported beside |
| D-B8 | n | 80 evaluation seeds per cell | 60: saves about 1.2 h of rental time, loses about 10 points of power on X1-like effects (§8.5) |
| D-B9 | Budget | Rental, hard cap $40, fetch-verify-destroy on any failure (V471 pattern); expected $13-36 and 42-117 h wall time (§9) | Laptop: 85-190 h by day only, and the night CPU cap applies; not practical |
| D-B10 | [A3] reading | New perturbation options in code are a code change, not a plant change, when every stored S, X1 and X2 row reproduces on every key; no Plan B run or tuning in X1 or X2 (§2.1) | Treat any new code as a plant change: Plan B would then need its own plant and a new V&V record |
| D-B11 | Thesis placement | Log an outline amendment: Plan B as chapter 6 (it also carries RQ4's scheduler), "Learning or adaptation?" merged into it | Put Plan B inside chapter 7 "Disturbed plants" (V459 outline): no outline change, but the contribution sits less visibly |

Phase note (CLAUDE.md table): this protocol is "writing a protocol", Extra High with ultracode on for its design review. The code checkpoint before S2 needs High with ultracode on (adversarial review).

Not blocking, but open in the record: claim review D1-D9 (`docs/thesis/claim_review_round2.md:34-40`, uncommitted). Plan B runs nothing in X1 or X2, so it does not depend on D1 or D8.

## 1. Question and claim sentence

**Question.** Under realistic perturbations that v3w was not trained on, does the per-CAV PPO headway policy v3w (5 learners, frozen, no retraining) have less door-to-door delay and less close-following than every tuned non-learning controller we can build on this plant, and at what hard-braking cost? Where it does not, where does it win, tie or lose?

**Claim shape (V478):** a conditional advantage, per pre-registered cell. Never universal. Never against p333 alone. Never against no control alone.

**Sentences that can be written, by outcome (filled from the rows, no other wording):**

| Outcome in a cell | Sentence |
|---|---|
| D with R | "Under [cell: one-line physical description], a perturbation outside its training conditions, the per-CAV PPO headway policy (5 independently trained learners, averaged per seed) had less door-to-door delay ([x] % [CI]) and less close-following ([y] % [CI]) than every one of [k] tuned non-learning controllers, and it lost less delay to the perturbation than each of them, at a hard-braking cost of up to [z] % [CI]. Synthetic three-lane freeway with two on-ramps, 50 % ALKS; limits L1-Ln." |
| D without R | The same sentence without the resilience clause, and: "its advantage over these controllers was not shown to be larger under the perturbation than in steady traffic." The word "resilience" is not used. |
| C | "... had less close-following ([y] % [CI]) than every one of [k] tuned non-learning controllers, with delay at most 2 % worse (bound [b] %), at a hard-braking cost of up to [z] % [CI]." |
| N | "Under [cell], the policy did not beat every tuned non-learning controller. It [won / tied / lost] against [lists], see the operating map." |

Every sentence also carries:
- all three cells' outcomes, never only the cell that was won;
- which opponents were CMA-ES searches that hit the generation cap without converging ("lower bounds");
- no control's delay and close-following, and "no control had fewer close-following seconds, at [w] % more delay" where v3w is shown worse than no control at the deciding level (V459, V467);
- the intended-use status of the rows (D-B3);
- the disclosures in §10.2.

**Words never used (outline §3, `docs/thesis/outline_v1.md:55`):** "proven"; "verified and validated" before the record review (V462(3)); "safe" or "safer" (close-following is a surrogate, and there is no severe-conflict claim); any field or calibrated-site claim; any win on a measure that is not pre-registered here; "first" or "novel".

**If every cell is N,** the thesis reports a null (V243(3), V456(3)): "against every tuned non-learning controller, under three perturbation families, the policy showed no advantage on delay and close-following together", with the full operating map. The contribution then rests on the plant, the method and the map (V457(1)), not on superiority.

## 2. Closures and intended use

### 2.1 X1 (V395, [A3]) and X2 (V466)

- [A3] closes "this DRL line ... on these slowdowns" (`confirmatory_3.md:132`). V466 and `round_2_result.md:432` close the DRL claim against tuned rules "in X2 on this plant". X1 has had three tests on fresh seeds (confirmatory 3, rounds 1 and 2) and X2 four (`round_2_result.md:239-246`).
- **No Plan B run takes place in X1 or X2, for any arm.** No rule is re-tuned there. This follows the literal reading of [A3], where "tuning" is not limited to DRL.
- **Boundary rule, fixed here:** no Plan B cell is a single-edge tapered slowdown, the kind of X1, X2 and v3w's training draw (`perturb.py:35-39`). So no Plan B cell can be read as a seed round in X2 or a fourth test of X1.
- **Stored X1/X2 rows are not evidence here (V478).** They appear only in a history appendix with their original readings, labelled "not Plan B evidence". Disclosed: this draft used them for planning only (paired SDs, effect sizes, costs; `read_power/results.md`).
- **3E-X1 and 3E-X2 run as transfer opponents in the new cells.** That runs them on new perturbations, not in X1 or X2. It is not tuning in X1 or X2.
- **Code changes and [A3]'s "plant change" (D-B10):** Plan B adds perturbation options (§4) and a scheduler rule. The network, `plant_c3.json`, fleet and models are unchanged. Check C1 (§7) shows that 7 stored rows (S, X1, X2, pack on) reproduce on every key at the Plan B commit. Under that check, the record should read the addition as a code change. The author confirms this reading.

### 2.2 Retraining

None. v3w is frozen at w0u250, w1u500, w2u250, w3u500, w4u500 (`round2/test/job_6c49e7e.json`). Disclosed: these checkpoints were chosen on round 2's X1/X2 validation seeds (`round_2.md:256-259`). So v3w was selected on slowdowns, though not on any Plan B cell.

### 2.3 Intended use (V462(4), D-B3)

The record's use covers "steady or with tapered slowdowns (X1, X2)" at 4,090-6,000 veh/h with 50 % ALKS (`plant_vv_record_v0.md:9`). V462(4) already labels condition T, H1 and H2 as outside it. All three Plan B cells are outside it as written.

**Recommended: amend §1 before any Plan B data.** Add "a corridor-wide temporary speed limit, slow heavy vehicles, and a demand surge within 4,090-6,000 veh/h, as specified in the Plan B protocol". Each kind gets requirements with a method, evidence and a status (new IDs, numbered in the record): its specification applies as written (like PR-13); T0-type binding (PR-10); it matters beyond seed noise (PR-25); no hidden 0.1-s braking (PR-09); no deadlock (PR-17, teleports are disabled); counters traced (PR-24); gains located by road, period and lane (PR-28).
- A kind whose verification fails at S1 is dropped before evaluation (§7). It is not run as "outside intended use".
- The amendment and its date are disclosed beside every sentence. It departs from V462(4)'s "labelled, not added". That rule was written for rows that already existed; here nothing exists yet.
- None of the three cells touches the record's "Not for" list (V2V loss, lateral or merge-conflict safety, human adaptation). SLOW50 does rely on overtaking, so the PR-08 lane-changing limit weighs more there (§12).

**If the author keeps §1 unchanged,** every Plan B row and sentence carries "outside the plant's stated intended use", and §1's sentences say so in their first clause.

**Excluded kinds, and why:**

| Kind | Reason |
|---|---|
| outage (V2V lost) | Excluded by name ("Not for: V2V with latency or loss"); v3w's commands have no effect during it (`b_env.py:764-786`) |
| lane closure or blocked-lane incident | Lateral and merge-conflict safety is "Not for"; lane changing is a limit (PR-08); teleports are off, so a stranded vehicle blocks the lane for the rest of the run (D2's closure stranded vehicles, `screen_D2_incidents.md:85-101`) |
| ALKS-share change | Changes the stated 50 % ALKS; a plant-level change (PR-04) |
| weather (`fleet.WEATHER`) | Calibrated on road ld32, not r2m3 (V204, V206); a change to the driver population |
| brake (one car brakes) | Formed no wave on r1m3 (V342); likely fails the perturbation-matters gate |
| burst (H2) | Similar demand-side role to SURGE, and its wait before release is not counted as delay (`perturb.py:48-56`) |
| oracle options | Use r1m3 positions (`perturb.py:27-30`); wrong on r2m3 |

## 3. Policy under test and opponents

### 3.1 Policy under test

v3w only, the arm named by V478: the per-seed mean over its 5 learners, as in T1 and the V462 tiles. tail and sw (round 2's finalists) are not run. They are the same line of evidence, chosen on X1/X2 validation, and adding them adds arms and forking paths.

What v3w can see (`b_env.py:896-952`, `c_train.py:69-95`): 16 local inputs. These are its own speed and position, leader and follower gaps and speed differences, its own 200-m roadside bin speed, the merge-1 zone speed and accelerating-lane counts. It never sees the speed limit, the demand, the time or any event. So it meets every Plan B perturbation only through local traffic. The rules are tuned per cell (they know the condition), and LocalRule-type rules read 400-1,000 m ahead. This favours the rules, by design, and is disclosed.

### 3.2 Opponents per cell (all count; no counting filter)

The deciding set is every opponent below. Round 2's counting filter (`round_2.md:66-68`) is not used. A filter removes opponents, so it would make "every tuned controller" easier. Each opponent's delay against p333 is reported beside.

| Group | Opponents | How tuned | Seeds | In the cell |
|---|---|---|---|---|
| Fixed reference | p333 (0.8 s everywhere) | Not tuned | none | Runs as is |
| Grid rules from confirmatory 3 | z33133, r4a1, lr400_13_2, lr1000_16_2, lr1000_10_1, lr400_16_1, a4400_10_1, os0_10_10, os1_15_10, os1_10_0 | Per-form picks for X1 or X2 (`confirmatory_3.md:48-64`) | 7,440,160-179 | Transfer: as tuned for X1/X2 |
| Traced rule | copy | Traced from baseline-v3's policies | 7,440,180-189 | Transfer |
| CMA-ES, earlier | 3E-T (g032i20), 3E-X1 (g003i02), 3E-X2 (g016i21) | 3E-T under condition T, 40 of 100 generations (V443); 3E-X per X cell, 40 generations, not converged (V461) | 7,440,700-779 | Transfer, lower bounds, disclosed |
| Per-cell grid picks | Per form (uniform, zone, on4a, local, adapt4a, own) the lowest-TTC admissible rule; the delay opponent; the front row; duplicates of the above dropped (at most 8 new arms) | Confirmatory 3's procedure, re-run in the cell: admissible if median paired delay at most 2 % worse than p333 and collisions at most p333's + 1; delay opponent = lowest median delay among rules with TTC at most 10 % worse than p333; front row = lowest TTC among rules with delay at most 10 % worse | 7,480,100-119 (20) | Tuned for the cell |
| 3E-c | Per-cell CMA-ES, ZoneOwnState (5 zones × 4 parameters) | Round 2's 3E-X objective: pooled TTC-seconds change against p333, +5 per % of delay above +1 %, +5 per extra collision; population 24, 16 seeds per generation; admission: delay at most 2 % above p333 at the level, collisions at most p333's + 1 | 7,480,100-139 (40), CMA seed 20261108 | Tuned for the cell, §3.3 |
| 3E-Dc | Same family, delay objective | Pooled delay change against p333 (%), +1 per % of close-following above p333's, +5 per extra collision; admission: close-following not above p333's (pooled point) and collisions at most p333's + 1 | 7,480,100-139, CMA seed 20261109 | Tuned for the cell, §3.3 |
| SCH-c | Adaptive scheduler | §3.4; threshold picked on tuning seeds | 7,480,120-139 | Tuned for the cell |

So each cell has up to 15 + 8 + 3 = 26 deciding opponents (counts after duplicates are dropped are fixed at S2 and reported). Plus no control in every table, never deciding alone.

Why 3E-Dc (D-B4): V478's claim needs less delay, but the 3E objective is TTC-centric (`round_2_prereg.md`, 3E objective). No current rule is delay-optimal. In the stored X1/X2 rows, delay is the binding measure, and close-following almost never binds (`read_power/results.md` §2). Without a delay-tuned opponent, an examiner can say the rules were never tuned for the half of the claim that decides it.

### 3.3 Convergence rule for 3E-c and 3E-Dc (D-B6)

- Searches run in blocks of 10 generations from generation 40.
- **Stop** at the first g in {40, 50, ..., 100} where the median search loss of generations g-9..g is less than 1.0 loss point lower than the median of g-19..g-10. This uses cma2's existing statistic (`cma2.py:293-317`), with a threshold added. The threshold of 1.0 is a chosen value, not derived from data.
- **Cap:** 100 generations, round 2's original plan (V441, cut to 40 by V443). A search that reaches the cap while still falling is used as is, and reported as "not converged at the cap, a lower bound" in every sentence.
- **Final step:** round 2 re-ran the 5 best distinct configurations plus the CMA mean on all 40 pool seeds (`cma2.py:334-382`). Plan B widens this to 10, because X1's admissible pick came from generation 3 when the better points broke admission (V461). The pick is the lowest loss among admissible configurations.
- The search hinge (+1 % on 16 seeds) and the admission (2 % on 40 seeds) stay as in round 2. The mismatch is disclosed.
- Code: `cma2.py --cond` accepts only T, S, X1, X2, H1 and H2 (`cma2.py:394`). The new conditions, the 3E-D loss and the stopping rule are code changes with unit tests (S0).
- Searches run without the measurement pack (it costs ×1.24 per run, V468). Picks are frozen in a committed JSON before S3.

### 3.4 Scheduler (SCH-c) and the MPC omission (V457)

**SCH-c, a non-learning adaptive scheduler:** a regime switch.
- Every 30 s it reads the roadside 200-m bin speeds that the LocalRule rules already read (`b_env.py:991-1015`), on edges 2 to 5.
- "Disturbed" when any bin is below θ m/s on two consecutive checks. "Undisturbed" after 60 s with every bin at θ + 2 m/s or more.
- Undisturbed, it runs 3E-T (the rule tuned under the same condition T as v3w). Disturbed, it runs the cell's 3E-c.
- θ ∈ {10, 13, 16, 19, 22} m/s, picked on 7,480,120-139: the lowest close-following with delay at most 2 % above p333 and collisions at most p333's + 1; if none is admissible, the lowest delay.
- About 50-100 lines plus tests (my estimate).

How it differs from the existing state-feedback rules: it switches strategy corridor-wide on a detected regime, rather than mapping local state to a level. The record never defines this distinction (`claim_review_round2.md:243`), so this definition is new and disclosed. An examiner may still call it a relabelled rule (§12).

**MPC omitted (D-B5), disclosed with these reasons:**
- no macroscopic model maps headway to capacity on this plant (the METANET line stopped, D5.5);
- an MPC without capacity-drop hysteresis would be a straw man (`docs/paper1/plan.md:515`, citing L62 [VERIFY]);
- the data-driven option, a port of MPC-F (`claude/v5b-core:vsl_lab/jobs/mpcf.py`, written for BN4 meters), costs author and build time that V457's "and/or" does not require.

If the author picks the port instead, it chooses among a few zone headway patterns every 30 s, from an MLP fitted on random held settings on seeds 7,480,200-299. It never gets the true model.

### 3.5 Adaptation-gain row (report-only)

This is confirmatory 3's "single rule" form (`confirmatory_3.md:61`), with 3E-T as the rule of equal information: both 3E-T and v3w were tuned only under condition T.
- Per cell and measure: e_v = effect(v3w vs 3E-T); e_c = effect(3E-c vs 3E-T), for 3E-Dc on delay.
- AG = e_v / e_c, bootstrapped on the same resamples.
- Read only if e_c's 95 % CI excludes 0, that is, if per-cell tuning matters.
- AG ≥ 1 means the frozen policy, untuned for the cell, did at least as well as the rule family tuned for the cell.

## 4. Perturbation cells

Every cell runs at one demand setting. Warm-up is 300 s and the run ends at 1,800 s (`b_env.py`, as rounds 1-2). The parameters below are fixed here, before any Plan B data. They were chosen by Claude in this draft, informed only by: the training support (`perturb.py:35-39`); the record's intended use; and H1/H2/X1/X2 medians for no control and p333 (`decide3_map.csv`). They were not informed by any v3w row in these perturbations, because none exists (`read_record`, training support).

| | L60 | SLOW50 | SURGE |
|---|---|---|---|
| Physical meaning | A corridor-wide temporary speed limit, as set for weather or downstream works, with no lane closed | A moving bottleneck: slow heavy vehicles (for example loaded trucks or special transports) entering at intervals | A surge of arrivals for 10 minutes, for example diverted traffic or the end of an event |
| Parameters | Limit 60 km/h on mainline edges 2, 3a, 3, 4a, 4 and 5 (from x = 3,000 m, both merges, to the exit), from 600 s to 1,500 s, 20-s taper down, instant return (as the existing kind); demand 5,300 veh/h | Truck (trailer class) max speed 50 km/h for its whole trip, applied to the first trailer departing at or after 360 + 120k s, k = 0..9 (last at 1,440 s), chosen from the demand list before the run, so every arm faces the same trucks; demand 5,300 veh/h | Demand 4,600 veh/h, 6,000 from 600 s to 1,200 s, back to 4,600; route shares fixed (70/15/15), so the ramps scale too; 30-s profile segments by V407's mechanism (`conf3/demand_osc.py`) |
| Code | `edge` accepts a list (a few lines in `Perturb._slowdown`) | `_truck` option to select by departure (about 10-20 lines, my estimate); the existing position-based selection, used by H1, is unchanged | A Plan B driver passes the profile, as `demand_osc.py` does; frozen code unchanged |
| Steady reference (for R) | S53: steady 5,300 | S53 | S46: steady 4,600 |
| Inside v3w's training draw? | No: the draw is one edge for 60-180 s; this covers 6 edges for 900 s (60 km/h is the draw's upper limit) | No: the draw has no truck caps | No: training used constant demand per episode (V407); the levels themselves (4,600, 6,000) are inside its 4,500-6,000 range |
| Inside the record's intended use? | No as written; yes if D-B3 amends §1 | No as written (H1-type rows labelled, V462(4)); yes if amended | No as written ("steady"); demand stays within 4,090-6,000; yes if amended |
| Distinct from X1/X2 by the boundary rule? | Yes: multi-edge, 900 s, 60 km/h | Yes: other kind | Yes: other kind |
| Why realistic | Temporary limits for weather and works are common traffic-management measures [VERIFY typical limits for the target country]; work zones and weather are commonly cited sources of non-recurrent congestion [VERIFY: FHWA, "Traffic Congestion and Reliability" (Cambridge Systematics, 2005), not read] | Slow vehicles act as moving bottlenecks [VERIFY: Gazis and Herman (1992), "The moving and 'phantom' bottlenecks", Transportation Science, not read]; the 50 km/h cap is H1's (confirmatory 3) | Demand fluctuation and special events are commonly cited congestion sources [VERIFY, same FHWA source]; the author's own open challenge (V407): the policies never saw changing demand |
| Prior information, disclosed | X1/X2 are tapered slowdowns where v3w led most rules (S0/S1 map, report-only) | H1 on baseline-v3 only: mild (`decide3_map.csv`); the period is 2.5× H1's, so that it binds | V410 (exploratory, baseline-v3's policies, 10 used seeds): the step profile favoured DRL on close-following and the peak profile did not; V408 asked for the simplest profile, hence one step up and one down |

My rough reasoning on L60 (not a fact): at 60 km/h the lane capacity depends strongly on the ALKS headway, so control should matter. The S1 gates (§7) decide, not this reasoning.

Not chosen: several demand levels per cell, repeated events or other variants (V408). One setting per cell.

## 5. Metrics

All metrics come from `plant_sweep.run_one` rows with the measurement pack on (`measure.py`, V468), at the run commit. The arm value is the per-seed mean over v3w's 5 learners.

| Role | Metric | Field | What it counts |
|---|---|---|---|
| Primary | Door-to-door delay | `all_delay` | Vehicle-seconds against the reference speed, insertion queues and unfinished vehicles included, fixed window (`plant_sweep.py:336`) |
| Co-headline | Served flow | `passed` | Vehicles entering edge 4 in the window; under L60 and SLOW50 the counting point lies inside the disturbed section (same for all arms) |
| Claim measure | Close-following | `ttc_net` | Vehicle-seconds with 1-Hz TTC below 3 s. It is a reward term (`claim_review_round2.md:30`): "teaching to the test", disclosed |
| Reported alongside | TTT | `N` | Vehicle-seconds in the network, fixed window |
| Gate | Collisions | `collisions` | New SUMO collision pairs per step, which include minGap intrusions and the warm-up (`read_plant` risks); T2's limit: at most the opponent's + 1 per run |
| Gate | Moving full-emergency events | `alks_full_moving` | ALKS −9 m/s² events while moving, lane-end creep excluded (V377); T2's limit: at most 5 % or 5 per run more |
| Gate | Flow | `passed` | T2's limit: at most 0.5 % worse (point) |
| Stated cost | Robust hard braking | `m_peak_car[2:]` + `m_peak_alks[2:]` + `m_peak_truck[1:]` per 1,000 vehicle-km (`m_dist_m_*`) | Braking events peaking at −4.0 m/s² or harder for cars and ALKS, −3.5 or harder for trucks (`measure.py:17-21, 390-404`; `s01_result.md:296-322`) |
| Reported cost | ALKS past their limit | `m_peak_alks[4:8]` | ALKS events peaking from −5 to −9 m/s² |
| Reported cost | Braking time | `b3_step` | Seconds at −3 m/s² or harder, at 0.1-s resolution |
| Report-only | Severe surrogates | `ttc2`, `ttc15`, `sev3`, by road, speed band and period | Not deciding; nearly subsets of the rewarded event for ALKS pairs |

**Not used as a braking measure:** the −4.5 m/s² count (`b45_*`, `events_ge45`). It sits on the car and ALKS braking limit and is speed-selective (`s01_result.md:287-324`). It appears only in a history appendix with that caveat.

**Braking tolerance (V478, D-B7):** there is no braking gate. The robust count's effect against every deciding opponent, with its CI at the deciding level, is stated in the sentence ("at a hard-braking cost of up to z %"). Where the harm rule (more than 10 % worse by point, 95 % CI upper bound below 0) flags an opponent, the sentence names it.
- This departs from T2's 5 % limit on braking at 3 m/s².
- The departure was set after S0/S1 showed v3w braking more than some rules (V475, V477), and is disclosed.
- The severe-event gates (collisions, moving full-emergency events) stay.

**Period bins:** `plant_sweep.period()` bins time only for kind slowdown (`read_plant` risks). Extend it to each cell's event window (L60 600-1,500 s, SLOW50 from 360 s, SURGE 600-1,200 s) for the "where and when" report. This is a measurement-code change, covered by check C1.

## 6. Seeds

Proposed fresh block for approval: **7,480,000-7,480,999.**
- Evidence that it is free (`read_record/seed_scan_summary.txt`): no stored keyed seed at or above 7,472,000 in `v5b1_runs`; no 7,48x,xxx in a strict git grep over all refs; no worktree or main-checkout file mentions it.
- Derived streams do not collide: kind random uses seed + 910,000, and Plan B does not use it; the CMA seeds are 20261108-9; the bootstrap rng is 20261108.
- Training-seed bounds rest on the recorded blocks and the `b_env` guard (`b_env.py:139-141`), not on stored rows.

| Seeds | Count | Use |
|---|---|---|
| 7,480,000-009 | 10 | Smoke, identity, T3 determinism (rows kept apart, never compared across arms) |
| 7,480,010-029 | 20 | Tool checks T0-P, T1-P, T2-P, drain (no control and p333 only) |
| 7,480,030-099 | 70 | Reserved for tool-check re-runs under the bug rule |
| 7,480,100-139 | 40 | Tuning pool, shared by cells: grid picks (100-119), 3E-c and 3E-Dc (all 40, moving window of 16), SCH θ (120-139) |
| 7,480,200-299 | 100 | MPC fitting data, only if D-B5 picks the port |
| 7,480,400-479 | 80 | Evaluation, used once: every cell and steady reference, every arm |
| 7,480,480-999 | 520 | Reserved (a bug-rule re-run on fresh seeds, or a later confirmatory round), each use approved by the author |

The same 80 evaluation seeds serve every cell and reference, so seeds pair across cells too. Bonferroni holds under any dependence between cells.

## 7. Tool checks and smoke checks (criteria fixed before they run)

Every check writes its rows to the ledger. A failed check stops the stage. A fix needs a new commit, all affected checks re-run, and a log entry with both outcomes.

| Check | Criterion | Runs (my estimate) | Stage |
|---|---|---|---|
| C1 identity | 7 stored rows (S, X1, X2 at 5,300, pack on, from `measure_s01_remote`) reproduce on every key at the Plan B commit; H1 with the old truck selection reproduces a stored confirmatory 3 row | 8 | S1 |
| C2 T3 determinism | Same seed twice per cell on the machine that runs the stage: rows equal on every key | 6 per machine | S1, start of S2 and S3 |
| C3 spec (T0-P) | A 0.1-s trace per cell shows the limit on every listed edge, the 20-s taper and the return (L60); the capped trucks' IDs, departures and maximum speeds (SLOW50); the inserted demand per 30-s segment, ±10 % per segment and exact in total (SURGE) | 3 | S1 |
| C4 pre-event identity | L60 and SLOW50 runs equal their S53 pair on per-minute series until the first event (the `perturb.py` docstring promise). For SURGE, the check is reported, not required | from C5 rows | S1 |
| C5 perturbation matters (T1-P) | For no control and for p333: the cell's median paired delay at least 5 % above its own steady reference, 95 % CI lower bound above 0, on 7,480,010-029 | 2 arms × 2 conditions × 20 × 3 cells = 240 (steady rows shared) | S1 |
| C6 placebo for C5 | C5's code on steady-against-steady pairs must FAIL (the gate can fail; "gate statistic needs a null") | 0 (re-uses rows) | S1 |
| C7 control matters (T2-P, CLAUDE.md early KILL) | p333 or 3E-T at least 10 % less delay than no control in the cell, 95 % CI lower bound above 0 | +20 per cell for 3E-T = 60 | S1 |
| C8 drain and deadlock | No mainline vehicle stationary for 300 s or more outside the insertion and ramp queues (1-Hz trace); finished share and pending vehicles reported | from C5 rows | S1 |
| C9 braking resolution (PR-09) | 1-Hz braking within 5 % of step braking for no control and p333 in each cell | from C5 rows | S1 |
| C10 smoke, outputs carry inputs | One run per arm type (v3w learner, grid rule, 3E rule, SCH-c) per cell on 7,480,000-002: the row records the cell spec, the controller and the seed; the pack's consistency sums hold; traced equals untraced (V386) | about 15 | S1 |
| C11 training support | By inspection, against `perturb.py:35-39` and the training configs: each cell lies outside the draw | 0 | S0 |
| C12 inputs (PR-15) | By inspection: no actor input or rule input carries the limit, the event time or the demand | 0 | S0 |

**Gate outcome per cell:** a cell that fails C3, C5, C7 or C8 is dropped before S2. The cell is reported with its gate values, m stays 3, and the cell is not re-parameterised in this study. A drop leaves the other cells' readings unchanged.

**Smoke rows** (C10) include v3w runs in the cells on seeds 000-002. They are checked only by script for consistency and never compared across arms. They are in the ledger.

**Before S2 and S3 on a rented machine,** the acceptance must pass first: C2 plus 3 C1 rows on that CPU (V475 pattern).

## 8. Statistics and the reading

### 8.1 Statistic (round 2, unchanged)

effect = sign × median(P − O) / median(O) × 100 over paired seeds, positive meaning v3w is better. Percentile bootstrap of the paired differences, 20,000 resamples, denominator fixed, rng 20261108. Arm = per-seed mean over 5 learners (`round_2.md:263-268`).

Known weakness, disclosed: the median statistic is lumpy when per-seed differences have a gap around 0. Its bound can then depend on the resample count (X1 against os0_10_10: 2.72 with 4,000 resamples against 3.2 with 20,000; `read_power/results.md` §1). One convention is kept (CLAUDE.md), so there is no alternative estimator.

### 8.2 Multiplicity

- **m = 3, the cells L60, SLOW50 and SURGE, fixed even if a cell drops.** Two-sided CIs at 1 − 0.05/3 = 98.33 %, percentiles 0.833 and 99.167.
- **Inside a cell:** "better than every opponent on delay and close-following" is an intersection-union test, so there is no correction across opponents or measures (`round_2.md:194`).
- **Fixed sequence inside a cell:** C first, then D, then R, each at 98.33 %, each tested only if the previous one passed. This keeps the family-wise error at or below 0.05 two-sided over all cells and steps.
- **Report-only rows** (tiles, AG, steady-reference readings, per-learner counts, the V459 bar against no control, severe surrogates) are read at 95 % and labelled report-only. Under V467 they feed no claim sentence. The only claim sentences come from §1's ladder, read at 98.33 %.

### 8.3 The per-cell ladder (deciding, arm level, against every deciding opponent)

All conditions below apply against every deciding opponent of the cell.

- **Gates** (all steps): flow at most 0.5 % worse (point); collisions at most the opponent's + 1 per run; moving full-emergency events at most 5 % or 5 per run more (T2's limits, `round_2.md:199-202`).
- **C** (close-following advantage at no material delay cost, T2-shaped as the existing thesis bar V459):
  - close-following at least 10 % better by point, CI lower bound above 0, and median paired difference at least 20 vehicle-seconds per run lower;
  - delay at most 2 % worse by point, with the CI's worse end below 5 % worse (D11's non-inferiority bound).
- **D** (V478's shape):
  - C holds;
  - delay at least 2 % better by point, with CI lower bound above 0.
- **R** (resilience, V343: "each controller's loss against its own run without X"):
  - D holds;
  - per seed and controller, L = delay(cell) − delay(steady reference) in vehicle-seconds;
  - the statistic on L (v3w against each opponent) has CI lower bound above 0 against every deciding opponent.
  - R is read only if its sign-flip null (computed by the report script before the reading is printed, 2,000 label swaps) gives a false-"better" rate no more than 2 × nominal. Otherwise R is reported as "statistic failed its null".

Outcome per cell: N (C fails), C, D, or D+R. Per-learner counts (how many of 5 learners meet each step against every opponent) are shown beside and do not decide. Disclosed: round 2's T2 used "at least 4 of 5 policies", and X2 failed it. The arm-level rule here was chosen with that known (V460 and V462 already read arms).

### 8.4 Operating map and other report-only rows

- **Tiles:** the V462(1) rule per cell × measure × opponent: delay, close-following, flow, robust braking, ALKS past-limit events. 95 %, arm level, steady references included. Markers show T2 side-limit breaches.
- **Resilience row:** L for every controller, and v3w's L against each opponent's, at 95 %.
- **Adaptation gain:** §3.5.
- **Steady references S53 and S46:** v3w against every opponent, the same ladder at 95 %, report-only. This shows whether any advantage is specific to perturbations (V395 noted the edge in steady traffic too).
- **No control:** in every table. The V459 bar against no control is read at 98.33 % beside, never alone.
- **Each tuned opponent against p333** and against its own tuning seeds, as an overfitting check.
- **Where and when:** counters by road, speed band and period (event window against the rest); lane-end behaviour at ramp 2 (PR-28).

### 8.5 Nulls and power at n = 80

All numbers below come from `read_power/` on the stored X1/X2 rows. They are planning proxies, not evidence. New cells and stronger opponents may differ.

- **Null of the statistic:** under label swaps, the per-comparison one-sided false-"better" rate at m = 3 is 0.8-1.0 % for n ≥ 40, against a nominal 0.83 % (`power_tables.md`). For the whole intersection rule it is at most 1.4 % at m = 3 when only the closest opponent is null. The statistic is slightly liberal at n = 20 only.
- **Power of D (≈ W3 in the reader's terms; the point margins rarely bind at n = 80, my inference, to be checked in S0), per cell, m = 3, n = 80:**

| Effects like | Stored effects | 0.75 × stored |
|---|---|---|
| X1 | 92 % | 81 % |
| X2 | 33 % | 12 % |

- **At least one of 3 cells reaching D (m = 3, n = 80, independent cells):** 100 % if all are X1-like, 97 % if half are, 70 % if all are X2-like. At 0.75 × effects: 99 / 85 / 31 % (`combos.md`).
- **Power of C:** not computed. S0 re-runs `read_power/power.py` with the exact ladder (margins, fixed sequence) on the stored rows before approval. This takes about 1 h on 4 processes (my estimate) and runs no simulation.
- **What lowers power here:**
  - the deciding set is larger and stronger than the reader's 14 rules (3E-Dc, converged 3E-c, per-cell grid picks, SCH-c);
  - delay already binds in the stored rows;
  - the stored 3E-X picks were lower bounds.
- **A null is the likely outcome in X2-like cells.** This is stated before data.
- n = 80 also matches V435's figure for 80 % power of a 5 % non-inferiority bound at 97.5 %.

## 9. Stages, run counts, time and cost

Rates (measured): rental A, V475: EPYC 7702, 59 workers, 2,450-3,050 runs per hour with the pack on, $0.312/h, batch 88 % of wall time. Rental B, V461: 244 workers, about 6,400 runs per hour derived from the 3E searches, $0.81/h. Laptop: 1,330 runs per hour by day (V425-V426); night cap 40 % CPU (V432).

| Stage | Content | Runs | Where |
|---|---|---|---|
| S0 | Author decisions; ultracode design review; V&V amendment text (if D-B3); code (multi-edge limit, truck by departure, SURGE driver, period bins, cma2 conditions, 3E-D loss and stopping rule, SCH-c); unit tests; adversarial code review; power re-run for the exact ladder | 0 | Laptop, no simulation except unit tests |
| S1 | C1-C12 | about 330 | Laptop by day (about 15 min) |
| S2 | Per cell: grid picks 70 × 20 = 1,400; 3E-c and 3E-Dc, each 384 per generation × G + 40 reference + 440 final; SCH θ 5 × 20 = 100. Picks frozen and committed | 99,540 (G = 40) to 237,780 (G = 100) | Rental |
| S3 | Evaluation, used once: per cell 32 arms × 80; S53 43 arms × 80; S46 32 arms × 80 (upper bounds, before duplicates are dropped) | 13,680 | Rental, one machine (V436) |
| S4 | Scripted reading (code frozen before S3), report, ultracode verification, ledger | 0 | Laptop |

| Design | Total runs | Rental A wall | Rental A cost | Rental B wall | Rental B cost |
|---|---|---|---|---|---|
| Recommended, searches stop at 40 | about 113,500 | 42-53 h | $13-16 | about 20 h | about $16 |
| Recommended, searches reach the cap of 100 | about 251,800 | 94-117 h | $29-36 | about 45 h | about $36 |
| 3E-c only (no 3E-Dc), 40 | about 66,000 | 25-31 h | $8-10 | about 12 h | about $9 |
| 3E-c only, 100 | about 135,100 | 50-63 h | $16-20 | about 24 h | about $19 |

- **The searches are 88-94 % of all runs.** The cost is set by the convergence rule, and how many generations it takes is unknown (§3.3).
- Evaluation alone takes about 5-6 h on rental A.
- Search runs need no pack, so they are probably faster than the pack-on rate used above. That saving is not counted.
- Sequential floor: one search alone needs about 437 s per generation on 122 workers (V461), about 12 h for 100 generations. Six searches sharing one machine are throughput-bound, as in the table.
- Fresh seeds used: 150 (10 + 20 + 40 + 80), plus 100 if the MPC is built.
- Not costed: author time for S0 decisions and the amendment; build time (my estimate: 1-2 days of code and tests for all S0 items); MPC build if chosen.
- Counting method: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/planb/count_breadth.py`, from the formulas above and the reader's rates.

## 10. What is reported in every outcome, and the ledger

### 10.1 Always reported

- Every cell's ladder outcome (N, C, D, D+R), including dropped cells with their gate values.
- The full operating map: every opponent, every cell and steady reference, every tile measure, no control in every table.
- Each opponent's tuning record: seeds, generations, the convergence statistic per block, the pick, admission status, and "not converged at the cap" where it applies. Each opponent's delay against p333.
- The braking costs (robust count, ALKS past-limit events, `b3_step`) against every opponent, with CIs.
- Resilience and adaptation-gain rows, with their nulls.
- Per-learner counts.
- Every run in the ledger, including smoke, tool checks, failed and abandoned runs.

### 10.2 Disclosures carried beside every sentence

1. The closures (V395, V466) and the boundary rule. No Plan B run in X1/X2. Planning used stored X1/X2 rows.
2. The intended-use status (amended before data, or labelled).
3. v3w's checkpoints were chosen on X1/X2 validation seeds.
4. Close-following and braking at 3 m/s² are reward terms.
5. The rules know the condition and look further ahead.
6. Opponents that hit the generation cap; the 3E-T and 3E-X transfer opponents are lower bounds.
7. The MPC omission, if chosen.
8. SCH-c's definition is new.
9. No braking gate, a departure from T2 set after S0/S1.
10. The arm-level rule, chosen after round 2's per-policy X2 result.
11. The cell parameters were chosen by Claude in this draft, with the priors in §4.
12. The `collisions` counter includes minGap intrusions.
13. Limits L1-Ln from the V&V record.

### 10.3 What follows from each outcome (fixed now)

| Outcome | What follows |
|---|---|
| D or D+R in at least one cell | §1's sentences for those cells, with the other cells' outcomes beside; Plan B becomes the chapter's claim |
| C only (no D) | The T2-shaped sentence; no "less delay" wording anywhere |
| N in every cell | A null, reported as such; the chapter is the operating map; no further Plan B cells are added to rescue the claim |
| Any N cell | The DRL claim against tuned rules closes in that cell on this plant: no further training, tuning, plant change or seed round there (as [A3]) |
| Any new cell proposed after these results | A new study, labelled post hoc, never merged into this one's count |

### 10.4 Ledger

- One V-number for the approval (with all D-B decisions), one at each stage start and end, and one per deviation.
- Rows go under `/home/catalin/work/phd/v5b1_runs/planb/`.
- Code lives on branch `planb/core`, from `r2/metrics` at `79b889b` (branch-per-approach rule), in a worktree under `~/work/phd/wt/planb`. Long stages run from a frozen detached worktree at the run commit, with no commits there mid-run.
- The protocol goes in `docs/research/protocols/planb.md` on `v5b1` after approval.

## 11. Deviations policy

- **Before S3 starts:** any change is logged with a V-number, a reason, and a statement of which Plan B rows existed at that time (only S1 check rows and S2 tuning rows can exist).
- **After S3 starts:** cells, opponents, n, metrics, margins and the ladder do not change.
- **Bug rule:** a bug found after results means fix, re-run everything affected, and log both outcomes (CLAUDE.md). A re-run under the bug rule is not a new round.
- **A cell dropped at S1** keeps m = 3 and is reported. It is not re-parameterised.
- **A search that reaches the cap** is used as is and disclosed. A search that crashes resumes deterministically from stored runs (as V443). Its seeds are not changed.
- **An opponent that cannot be built** (SCH-c), or whose S1 smoke fails, is a disclosed omission. m does not change.
- **One platform per stage (V436).** If a stage moves machines, C2 and C1 run on the new machine first, and the break is disclosed (V465 pattern).
- **Rental failure:** fetch, verify by SHA-256 and destroy (V471). Rows resume by (name, cell, seed). The worker count does not change rows.
- **The CPU rules and the 23:00-09:00 cap apply to every laptop step.**

## 12. Risks and limits

1. **Power.** If the new cells behave like X2, or the converged and delay-tuned opponents shrink v3w's delay margins, D is unlikely (12-33 % per cell at X2-like effects). A null is a real possibility, stated before data.
2. **Intended use.** Without the amendment (D-B3), every deciding row is labelled outside the intended use. With it, the amendment rests on an unreviewed draft record (6 met, 13 partial, 7 gap, 2 limit of 28).
3. **Realism of magnitudes.** The cells are realistic in kind, not calibrated. Their magnitudes (60 km/h, 50 km/h every 120 s, 4,600 to 6,000) are design choices. "Not for calibrated sites" (V245) stays.
4. **Lane changing (PR-08, a limit)** weighs more in SLOW50, where overtaking matters. Lane-end behaviour at ramp 2 is unvalidated (PR-28), and L60's bottleneck may sit there.
5. **Opponent strength.** The transfer rules are tuned for other cells. 3E-T stopped at 40 of 100 generations. The convergence threshold (1.0 loss point) is a chosen value. The 3E-D loss weights are chosen, not derived.
6. **SCH-c may be read as a relabelled rule.** The MPC is omitted (if D-B5 is taken).
7. **Teaching to the test.** The deciding close-following measure is a reward term.
8. **Selection.** v3w's checkpoints were picked on X1/X2 validation. The cell parameters were picked by Claude knowing the X1/X2, H1 and V410 priors (§4).
9. **Statistic.** The median statistic is lumpy. Delay non-inferiority at n = 80 has limited power at a true tie (V435). The power of C is not yet computed.
10. **Counters.** `collisions` includes minGap intrusions and the warm-up. Teleports cannot fire, so deadlock rests on C8. The period bins are new code.
11. **Cost uncertainty.** The searches dominate, and their length is unknown: 113k to 252k runs, $13-36.
12. **Process.** The outline change (D-B11) and the open claim review D1-D9 need ledger entries. "Fixed before data" must mean before any Plan B row except S1 check rows and S2 tuning rows, and the disclosure must say so.
