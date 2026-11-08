# Plan B protocol v0: v3w under perturbations it was not trained on, against every tuned non-learning controller

**Status: DRAFT v0, not approved.**

2026-11-08. A synthesis of three drafts (`draft_rigor.md`, `draft_breadth.md`, `draft_staged.md`), three judges and three readers in this folder. No Plan B seed, code or run exists. Every number marked "planning" comes from stored X1/X2 rows used only as a proxy for size and cost, never as evidence (V478). New planning files: `synth/rule_v0.py` and `rule_v0.json` (the null and power of §8's exact rule), `synth/count_v0.py` (run counts). Literature not read is marked [VERIFY]. "My estimate" marks figures that are not measured.

```
S0 decisions, build, reviews ─► S1 smoke, identity, T3 ─► S2 plant gates per cell (no control, p333, 3E-T, placebo; no v3w)
  ─► S3a grid re-pick ─► S3b pilot (v3w vs untuned opponents, 30 seeds) ─► S4 3E searches, ASCH, MPC-F
  ─► S5 freeze, smoke ─► S6 evaluation, n = 120, read once by the committed script (S7)
KILL exits: S2 (about 1,200 runs, laptop, $0)    S3b (about 9,400 runs in total, under $1.5)
```

## 0. Status and open decisions

The protocol becomes binding when the author decides the items below, it is committed as `docs/research/protocols/planb.md` on `v5b1`, and a V# records the approval. No stage runs before that. Phase settings (CLAUDE.md table): the design review of this protocol is Extra High with ultracode on; the build is High; the checkpoint before S6 is High with ultracode on.

### Open decisions

1. **Seeds.**
   - Recommendation: approve 7,480,000-7,480,999 with the partition in §6 (450 seeds used, 550 reserved).
   - Pros: no stored keyed seed at or above 7,472,000 and no 7,48x,xxx in any git ref or worktree file (`read_record/seed_scan_summary.txt`); one range per opponent family.
   - Cons: one more block to track in the record.
   - Weaker: the rest of V354's block (7,440,920-999, 80 seeds; its other free space is fragmented) is too small for tuning plus n = 120.

2. **Cells.**
   - Recommendation: three cells at 5,300 veh/h, 50 % ALKS (§4): **SURGE** (equal-mean demand surge), **TRUCK** (slow heavy vehicles chosen before the run), **WORKZONE** (incident-scene speed restriction on edge 2, upstream of both merges). Each has one stronger rung fixed now, used only if rung 1 does not bind. SURGE is one demand profile; the author accepts it under V408 with no variant.
   - Pros: three kinds (demand, moving bottleneck, fixed restriction), two of them not slowdowns; no plant file changes; WORKZONE needs no new code.
   - Cons: TRUCK and SURGE need new perturbation code; WORKZONE is the kind nearest [A3]'s "these slowdowns" and may not bind on edge 2; every prior favours v3w at least partly (§4.4).
   - Weaker:
     - two cells (drop WORKZONE): avoids the kind nearest [A3] but loses the supply side, and per-cell power rises only a few points (planning, n = 80: X2-like 33 to about 40 %);
     - ramp bursts (H2): the held wait is not counted as delay (perturb.py:48-56), and the load sits at merge 2, where PR-28 is a gap;
     - a corridor-wide 60 km/h limit (breadth's L60): mostly delay that no controller can remove;
     - single-edge slowdowns only (rigor's cells): a fourth slowdown round, outside the draw by duration or 5 km/h;
     - lane closure, outage, ALKS share, weather: excluded (§4.5).

3. **Intended use.**
   - Recommendation: keep V462(4), which is binding: every Plan B row and sentence carries "outside the plant's stated intended use".
   - Pros: follows the rule as written; no charge of moving the goalposts.
   - Cons: the contribution rests on labelled rows.
   - Weaker: amend V&V §1 for the cells that pass S2. This can only be a separate V#, logged before any v3w row (before S3b), with per-cell evidence from S1-S2. Its departure from V462(4), and the fact that it was decided after the X1/X2 results were known, are then disclosed beside every sentence. Amending before the evidence exists (breadth's and staged's timing) is not offered.

4. **Opponents.**
   - Recommendation: every opponent counts in every cell, with no counting filter: 15 carried rules, up to 8 per-cell grid re-picks, the steady pick, a per-cell CMA-ES rule for close-following (3E-C) and one for delay (3E-D, admitted on collisions and emergency events only), a cell-agnostic scheduler (ASCH) and an MPC with a fitted model and a validity gate (MPC-F) (§3).
   - Pros: meets V478's opponent list; serves outline chapter 6 (outline_v1.md:66); gives an opponent tuned for delay, the measure that binds.
   - Cons: MPC-F is the heaviest build (about a day, my estimate) and may fail its gate; 3E-D roughly doubles S4.
   - Weaker:
     - omit MPC-F: the wording falls to "every tuned rule-based controller and a non-learning adaptive scheduler";
     - omit 3E-D: halves S4, but no opponent is tuned for delay;
     - 3E-D bounded on close-following (rigor's): makes the delay half of the claim easier;
     - a per-cell scheduler (breadth's SCH-c): it knows the cell, so it is not adaptive with v3w's information.

5. **Convergence and budget.**
   - Recommendation: stop each search on a check set kept apart from its search pool, with δ = max(1.0, 2 SE), at least 40 and at most 100 generations; a ceiling of $40 or 7 days of machine time, whose action is fixed now (§3.3, §9).
   - Pros: answers V448 (search losses were optimistic); the ceiling cannot become a choice made after data.
   - Cons: a search still falling at 100 generations is a lower bound (labelled in the sentence).
   - Weaker: cap 150 (about 402,000 runs, projected $40-52, above the ceiling); a fixed 40 generations (both round-2 searches were still falling there, V461); stopping on the search median (breadth's), which tracks the population, not the incumbent.

6. **Claim rule.**
   - Recommendation: PASS if at least one cell is W or W-b and no cell is L. Harm is read at 95 %. At least 4 of 5 learners must agree. Hard braking is a stated cost whose 10 % tolerance per vehicle-km splits W from W-b (§8).
   - Pros: the same veto as D5.8's "not significantly worse … in any regime" and V83's A2 ("never clearly worse"); harm is not hidden by a corrected interval.
   - Cons: under a true tie in a cell, the harm rule fires in 5-14 % of planning studies with 14 opponents, and more with up to 28. So the veto can sink a true W elsewhere: with one X1-like cell and two tied cells, PASS falls from about 98 % to 73-88 % (planning, §8.9). The learner condition and the arm-level reading were set knowing that X2 failed T2's per-policy rule in round 2 (disclosed).
   - Weaker:
     - name every L beside the W, with no veto (staged's): more power, but a "resilience" sentence could stand beside a shown harm in another pre-registered perturbation;
     - braking as a non-inferiority gate (rigor's −15 % on raw counts): no stated reason, set just beyond the stored excess, and raw counts ignore exposure;
     - no braking tolerance (breadth's): breaks CLAUDE.md's "side constraints with stated tolerances".

7. **Pilot.**
   - Recommendation: a 30-seed pilot after the grid re-pick and before the searches, rule F0: GO if every delay and close-following point estimate against every pilot opponent is at least 0. A KILLed cell gets no 3E search, but it is still evaluated in S6 against the opponents it has, labelled, so the operating map is not limited to cells where v3w looked ahead.
   - Pros: the early, cheap KILL that CLAUDE.md asks for (a tie passes 0 %); it costs about 6 points of power in X2-like cells at n = 120 (planning).
   - Cons: untuned pilot opponents overstate GO; one more stage.
   - Weaker: F1 (delay at least +1 %, staged's): at n = 120 it drops about half of the cells with half X1's effects, where S6 would still win about 42 %; no pilot: a futile cell costs a full pair of searches (about 32,000-81,000 runs).

8. **n.**
   - Recommendation: 120 evaluation seeds, the same in every cell and in steady traffic.
   - Pros: planning power in X2-like cells 58 % instead of 35 % at n = 80.
   - Cons: 6,240 more runs (about 2-2.5 h on rental A, under $1).
   - Weaker: n = 80.

9. **[A3] reading and the cell boundary.**
   - Recommendation: new perturbation code is a code change, not a plant change, when V475's 7 stored acceptance rows (round 2, pack on) replay bit-identically at the run commit. No Plan B run or tuning takes place in X1 or X2. A restriction cell must differ from both X1 and X2 in at least two of edge set, limit, duration and number of events, and lie outside the training draw by edge or by limit (§2.2).
   - Pros: fixes [A3]'s undefined cell boundary before data.
   - Cons: an examiner may still read WORKZONE as a slowdown round.
   - Weaker: treat any new code as a plant change; Plan B would then need its own plant and V&V record.

10. **Place in the thesis.**
    - Recommendation: a V# amends outline_v1: chapter 6 becomes "Disturbed plants: resilience against tuned controllers" (Plan B). It absorbs "Learning or adaptation?" (its MPC and scheduler are built here) and chapter 7.
    - Pros: matches V478's "6. Plan B"; chapter 7 already reads "disturbances fixed before control results" (outline_v1.md:67).
    - Cons: an outline change after round 2.
    - Weaker: leave Plan B inside chapter 7; nothing changes, but V478 and the outline disagree.

## 1. Question and claim sentence

**Question.** Under realistic perturbations it was not trained on, does the frozen per-CAV DRL headway policy v3w have less door-to-door delay and less close-following than every tuned non-learning controller on this plant, and at what hard-braking cost?

The claim is conditional (V478; the author's principle of conditional advantages). It speaks of the named cells only, at 5,300 veh/h, on `plant_c3`.

**"[x] % [CI]"** (claim review D4): the effect against the closest opponent on that measure (the lowest CI lower bound), with its CI at the deciding level (98.33 %), plus the range of point effects over all opponents.

**Sentence if PASS** (filled from S6 only):

> On the simulated r2m3 freeway (synthetic, uncalibrated, 50 % ALKS, 5,300 veh/h, outside the plant's stated intended use), under [cell: one-line spec], a perturbation outside its training draw, the per-CAV DRL headway policy (5 independently trained learners, per-seed mean) had [x] % [CI] less door-to-door delay and [y] % [CI] less close-following than every one of [k] tuned non-learning controllers, including CMA-ES rules re-tuned for that perturbation on separate seeds ([converged | not converged at 100 generations]). Its robust hard braking per vehicle-km was at most [z] % [CI] higher than [opponent]'s. In [other cells] it [tied | was KILLed at the pilot | did not bind].

Clauses, each only if its own reading holds:
- **Resilience** (§8.5): "It also lost less delay to the perturbation than each of them." Only then may the words "resilience" or "resilient" be used. Otherwise: "Its advantage was not shown to be larger under the perturbation than in steady traffic."
- **W-b:** the braking clause comes first.
- **No control** (V459, reported in every case): "… and [d] % less delay than no control, with [no more | more] close-following."
- **Opponent wording:** "every tuned non-learning controller" only if ASCH and MPC-F were built and MPC-F passed its gate. Otherwise "every tuned rule-based controller and a non-learning adaptive scheduler; no MPC passed its validity gate", or "every tuned rule-based controller" if ASCH is missing too.
- **Limits:** the V&V limits L1-Ln; PR-08 (lane changing, not validated) for TRUCK; PR-28 if the location report puts the gain at merge 2; the reward overlap of the close-following measure.

**Sentence if NULL:**

> Under the pre-registered perturbations [cells], v3w was not shown to have both less delay and less close-following than every tuned non-learning controller. Per cell: [T | L | KILLed at the pilot | did not bind]. Closest opponents: [names, effects, CIs]. This is a null result, reported as one (V243, V456).

**Sentence if an L vetoes a W:** "In [cell], v3w had [x] % more [delay | close-following] than [opponent] ([95 % CI]), so no advantage is claimed in any cell." The W cell is reported as "W, vetoed".

**Words never used** (outline_v1.md:55; V462(3)): "proven", "safe" or "safer", "verified and validated", any field or calibrated-traffic claim, "first" or "novel", any win on a measure not pre-registered here.

## 2. Closures and intended use

### 2.1 X1 (V395, [A3]) and X2 (V466)

- [A3]: "If no primary cell is won, this DRL line closes on these slowdowns: no further training, tuning, plant change or seed round" (confirmatory_3.md:132). V395 closed X1 under it. V466 and round_2_result.md:432 close the DRL claim against tuned rules in X2 on this plant. X2 has had 4 tests and X1 3 (round_2_result.md:239-246).
- **Plan B runs nothing in X1 or X2:** no v3w row, no rule tuning, no seed round. [A3]'s "tuning" is not limited to DRL, so no rule is re-tuned there either.
- The only X1/X2 runs are identity replays of 7 stored rows (S1, check C1). They print bit-equality only, as V475's acceptance did.
- 3E-X1 and 3E-X2 run unchanged as transfer opponents in the new cells. Running a stored rule elsewhere is not tuning in X1 or X2.
- The stored X1/X2 rows are not evidence. They sized this protocol (power, cost, pilot rule), and that use is disclosed.
- Claim review D1 and D8 (claim_review_round2.md:34-40, :83-89) do not block Plan B, because Plan B makes no X1/X2 row. The approval V# says so.

### 2.2 Cell boundary (decision 9)

- A cell is new if its kind differs from X1/X2's (a tapered speed-limit drop on one edge, at constant demand).
- A restriction cell (here only WORKZONE) is new only if it differs from both X1 and X2 in at least two of edge set, limit, duration and number of events. It must also lie outside v3w's training draw by edge or by limit, not by duration alone and not by 5 km/h alone.
- Every cell lies outside the training draw (perturb.py:35-39; §4.1).

### 2.3 Plant change and code change

- No plant file changes: `plant_c3.json`, the network, the fleet composition and the 50 % share stay as they are.
- New code: the TRUCK selection kind, the SURGE profile, the period bins for the new kinds, the cma2 conditions and stopping rule, ASCH, MPC-F and the readers.
- This is a code change, not a plant change, if V475's 7 stored acceptance rows replay bit-identically at the run commit (C1); a steady row is added to that replay if one is stored on `plant_c3` (S0 checks). The author confirms this reading (decision 9).

### 2.4 Intended use (V462(4), decision 3)

- The V&V use is "steady or with tapered slowdowns (X1, X2)" at 4,090-6,000 veh/h with 50 % ALKS (plant_vv_record_v0.md:9). V462(4) labels condition T, H1 and H2 outside it (plant_vv_record_v0.md:15). All three Plan B cells are outside it as written.
- Default: every row and sentence carries "outside the plant's stated intended use".
- The cells avoid every explicit "Not for" item: no V2V loss, no lane closure, no change of driver mix or human adaptation. TRUCK rests on overtaking, and lane changing is a limit, not validated (PR-08). That limit is carried in TRUCK's sentence either way.
- The record is an unreviewed draft (6 met, 13 partial, 7 gap, 2 limit of 28; plant_vv_record_v0.md:3). "Verified and validated" stays out of every sentence (V462(3)).

### 2.5 No retraining

v3w stays at w0u250, w1u500, w2u250, w3u500, w4u500 (V478). Disclosed: these checkpoints were chosen on round 2's X1/X2 validation seeds (round_2.md:256-259), so v3w was selected on slowdowns, though not on any Plan B cell.

## 3. Policy under test and opponents

### 3.1 Policy under test

- v3w only, run as in round 2's test job (`round2/test/job_6c49e7e.json`), with only the perturbation and the seeds changed. S0 checks that the job settings match.
- Arm value per seed = the mean over the 5 learners (round_2.md:263-268).
- tail and sw are not run: they are the same line of evidence, chosen on the same validation.
- What v3w sees (b_env.py:896-952): 16 local inputs. It never sees the speed limit, the demand, the time or an event. The global vector, which holds time and flow, feeds the critic only (b_env.py:950-953). It meets every Plan B perturbation only through local traffic.

### 3.2 Opponents per cell

| Group | Members | How tuned | Seeds | In S3b | In S6 |
|---|---|---|---|---|---|
| Carried rules (15) | p333, z33133, r4a1, lr400_13_2, lr1000_16_2, lr1000_10_1, lr400_16_1, a4400_10_1, os0_10_10, os1_15_10, os1_10_0, copy, 3E-T, 3E-X1, 3E-X2 | As stored (baseline_v3/opponents.json; round 2), for X1, X2 or condition T; run unchanged | old | yes | yes |
| Grid re-picks (up to 8) | Per form (uniform, zone, on-4a, local, adaptive-4a, own-state) the lowest close-following admissible rule; the delay opponent; the front row | Confirmatory 3's procedure (confirmatory_3.md:48-64), 69 tunable rules, run in the cell | 7,480,100-119 | yes | yes |
| Steady pick (1) | The lowest close-following admissible rule in steady traffic at 5,300 | The same procedure in S | 7,480,100-119 | yes | yes |
| 3E-C (per GO cell) | ZoneOwnState, 20 parameters, close-following objective | §3.3 | pool 150-189, check 190-229 | no | yes |
| 3E-D (per GO cell) | The same family, delay objective | §3.3 | pool 150-189, check 190-229 | no | yes |
| ASCH | One cell-agnostic scheduler for every condition | §3.4 | 230-269 | no | yes |
| MPC-F | Fitted cost model, receding horizon, one model for every condition | §3.5 | 270-339 | no | if its gate passed |
| No control | | Never deciding, never alone, in every table | | yes | yes |

- Admissible in the grid: median paired delay at most 2 % worse than p333 and collisions at most p333's + 1. Delay opponent: the lowest median delay among rules with close-following at most 10 % worse than p333. Front row: the lowest close-following among rules with delay at most 10 % worse.
- Duplicates are run once and counted once. A cell has up to 28 deciding opponents.
- **No counting filter** (round_2.md:66-68): a filter removes opponents, which would make "every tuned controller" easier.
- Disclosed, favouring the rules: per-cell tuned rules know the condition in advance; LocalRule-type rules read 400-1,000 m of roadside speeds ahead, while v3w sees its own 200-m bin and a leader within 100 m (b_env.py:991-1015); ASCH and MPC-F read zone-level roadside data.
- Disclosed, favouring v3w: 3E-T stopped at 40 of 100 generations (V443); 3E-X1 and 3E-X2 were still falling at 40 (V461). They are carried as lower bounds. The per-cell searches carry the convergence requirement.
- copy was traced from DRL policies. It stays an opponent, because removing it would make the claim easier.

### 3.3 The per-cell CMA-ES searches

| Item | 3E-C | 3E-D |
|---|---|---|
| Family | ZoneOwnState, 5 zones × 4 parameters (cma2.py:39-60) | same |
| Search | Diagonal CMA, population 24, σ0 0.25, 16 seeds per generation in a moving window over the 40-seed pool; no measurement pack (V468) | same |
| CMA seed | 20261108 + cell index | 20261118 + cell index |
| Start | the cell's own-state re-pick | p333 (0.8 s everywhere) |
| Loss | pooled close-following change against p333 (%) + 10 per % of delay above +1 % + 5 per collision above p333's | pooled delay change against p333 (%) + 5 per collision above p333's |
| Admission (check seeds) | delay at most +2 % over p333 (point); collisions at most p333's + 1 | collisions at most p333's + 1; moving full-emergency events at most p333's + max(5 %, 5) |

- The delay penalty is 10 per % (round 2: 5), because round 2's X1 search drifted past admission and its pick came from generation 3 (V461).
- 3E-D's admission has no close-following bound. It is the strongest delay opponent the family can give; a close-following bound would make the delay half of the claim easier. The W rule's own gates still apply against it.

**Stopping rule:**
1. At generations 20, 30, 40, …, re-run on the 40 check seeds the 5 best distinct configurations since the last check (ranked by loss minus the generation median, cma2.py:293-317) and the current CMA mean.
2. Incumbent = the admissible configuration with the lowest check loss so far.
3. Stop at the first check g ≥ 40 where L(g − 20) − L(g) < δ, with δ = max(1.0 loss point, 2 × the bootstrap SE of that paired difference over the 40 check seeds).
4. Cap: 100 generations. A search that reaches it is "not converged at cap", still counts, and the sentence says so.
5. The opponent is the incumbent at the stop. Check-seed rows are not evidence. Picks are frozen in a committed JSON before S5.

Disclosed: picking the minimum of noisy check losses biases the incumbent's check loss downwards.

Code: cma2.py's `--cond` (cma2.py:405) and `common.COND` are extended to the new cells, with the stopping rule. A tuning-harness change, with unit tests (§7.1).

### 3.4 ASCH, the cell-agnostic scheduler

V457 asks for "a non-learning adaptive scheduler" without defining how it differs from the state-feedback rules. Here it is a two-regime gain scheduler.
- One controller for every condition (steady traffic and every cell). It does not know the cell.
- Inputs: the mean speed of three roadside zones from the existing roadside bins (b_env.py:991-1015): Z1 edges 1-2 (before merge 1), Z2 edges 3a-3 (between the merges), Z3 edges 4a-4-5 (after merge 2). Decision every 5 s, as the rules.
- Undisturbed: it runs the steady pick. Disturbed (any zone below θ for τ s): it runs R_dist. Back to undisturbed when every zone stays at or above θ + h for τ s.
- Library for R_dist: 3E-T and each GO cell's 3E-C.
- Grid: θ ∈ {40, 55, 70} km/h, τ ∈ {10, 30, 60} s, h ∈ {5, 15} km/h, R_dist from the library (at most 72 configurations), plus "never switch" (the steady pick alone).
- Tuning: every configuration on 20 seeds (230-249) in steady traffic and in every cell that passed S2. Pick: the lowest mean (over conditions) of the median paired delay change against p333, among configurations with close-following at most p333's and collisions at most p333's + 1 in every condition (points). The top 5 are re-run on 250-269; the best admissible one there is ASCH.
- It differs from LocalRule, AdaptiveOn4a and OwnState because it switches whole tuned rule sets corridor-wide on a detected regime. An examiner may still call it a relabelled rule (§12).

### 3.5 MPC-F, the fitted-model MPC

- Port of `claude/v5b-core:vsl_lab/jobs/mpcf.py` (written for BN4 meter scheduling). It never gets the true model.
- Actions, applied network-wide: p333, the steady pick, 3E-T and each GO cell's 3E-C (at most 6). Every 30 s it picks the action with the lowest predicted cost over the next 300 s.
- Model: an MLP (2 × 64, tanh) predicting the 300-s cost (delay in vehicle-seconds + 10 × close-following vehicle-seconds; weights chosen, not derived) from zone speeds and counts, accelerating-lane counts and ramp queues.
- Data: randomly held actions (holds of 30-120 s), 2 schedules per seed, on 40 seeds (270-309) in steady traffic and in every cell that passed S2. One model for every condition.
- **Validity gate, fixed now:** on 30 seeds per condition (310-339), summed over the conditions, MPC-F's median realised cost must not exceed that of its best single fixed action. If it fails, MPC-F is a disclosed failed build, it is left out of the deciding set, and the wording rule in §1 applies.
- Known limit: a data-driven model captures capacity-drop hysteresis only as far as the held-action data show it (docs/paper1/plan.md:515 warns about straw-man MPCs [VERIFY the L62 source cited there]). METANET was stopped (D5.5) and is not used.

## 4. Perturbation cells

### 4.1 The training draw every cell must avoid

v3w trained under kind `random` (perturb.py:35-39): no event in one third of episodes, otherwise one tapered slowdown on edge 3, 4 or 5 at 25-60 km/h for 60-180 s, starting at 400-1,200 s, at constant demand 4,500-6,000 veh/h. Steady traffic at 5,300 (S) lies inside the draw and inside the intended use; it serves only as the reference row.

Geometry (corridor.py:24, :45-48): edge 1 0-3,000 m, 2 to 3,500, 3a (merge 1) to 3,800, 3 to 5,000, 4a (merge 2) to 5,300, 4 to 6,300, 5 to 6,800. Run 0-1,800 s, warm-up 300 s. Route shares 70/15/15 (main, ramp 1, ramp 2).

### 4.2 Cells

| Cell | Physical meaning | Rung 1 | Rung 2 (only if rung 1 fails G1) | Outside the training draw by | Differs from X1/X2 by | Code |
|---|---|---|---|---|---|---|
| SURGE | The same number of vehicles, with 10 minutes concentrated at the plant's top level, as when traffic held upstream is released | Demand 5,300 to 600 s, 6,000 from 600 to 1,200 s, 4,600 from 1,200 to 1,800 s (mean 5,300 over the run and over the window) | none: 6,000 is the top of the intended-use range, and a longer surge needs a lull near 4,090 to keep the mean | kind (training demand is constant per episode, V407) | kind | profile through a Perturb hook or runner wrapper (as demand_osc.py), 3 segments only |
| TRUCK | Slow heavy vehicles (loaded or special transports) that others must overtake | The first main-route truck with sampled departure lane 0 departing at or after 360 + 120k s, k = 0-9, capped at 50 km/h for its whole trip, selected before the run | the same trucks capped at 40 km/h | kind (no truck caps in training) | kind | new kind: sets the selected trucks' `max_speed` before the route file is written (fleet.py:146, :164) |
| WORKZONE | A speed restriction at an incident scene with no lane closed | Existing `slowdown` kind: edge 2, 30 km/h, from 600 s for 600 s, 20-s taper, instant return | edge 2, 20 km/h, same times | edge (2 is not in {3, 4, 5}) and duration (600 > 180 s); rung 2 also by limit | edge set and duration | none (perturb.py:113-125) |

### 4.3 What each cell does to the measures

- **SURGE.** FleetDemand draws one arrival stream and restarts its clock at each segment edge (fleet.py:325-339). Vehicle attributes are drawn by index from separate streams (fleet.py:184-190). So the run is identical to S until 600 s; after that the departure times differ while the sequence of vehicles stays the same. Its comparison with S is seed-paired, not identical, after 600 s. Expected vehicles are equal, so no delay comes from added vehicles or lower limits.
- **TRUCK.** Every arm meets the same capped trucks, because they are chosen from the demand list before the run (unlike H1's run-time choice, perturb.py:103-111). They are inserted already capped, so no braking comes from applying the cap. The run is identical to S until the first capped truck departs. The capped trucks' own extra travel time is about 2,000 vehicle-seconds per run (my arithmetic: 10 trucks × about 220 s), about 1 % of no control's steady delay. The rest of any delay is the bottleneck effect.
- **WORKZONE.** Edge 2 carries the main route only (about 3,710 veh/h, about 1,240 per lane). The limit alone adds about 26,000 vehicle-seconds per run with no queue at all (my arithmetic: about 620 vehicles × 42 s), about 13 % of no control's steady median of 199,471 (decide3_map.csv, planning). So G1 must test congestion, not delay alone (§7.3). By my rough car-following estimate, lane capacity at 30 km/h may stay above edge 2's demand, so WORKZONE may fail G1 at both rungs.
- Realism: magnitudes are design choices, not taken from a measured site. Typical incident-scene limits and durations, moving-bottleneck theory and demand pulses are not read here [VERIFY before citing any; e.g. Gazis and Herman 1992 on moving bottlenecks, not read].

### 4.4 Prior information seen before this draft

| Cell | Prior | Direction |
|---|---|---|
| SURGE | V410 (baseline-v3 policies, not v3w; 10 used seeds; exploratory): the step profile gave 36-42 % fewer close-following seconds than p333 and os1_15_10 at the same or 4 % less delay; the peak profile gave 69 % more. S1 at 7,000 (report-only): v3w had the lowest delay | mixed; the step favoured DRL, and this profile is a step up then down |
| TRUCK | H1 at 5,300 (baseline-v3 policies only, decide3_map.csv): close-following 458-526 against p333's 534 and lr400_13_2's 1,254 at similar delay; no control +8 % delay against S (unpaired medians) | favours DRL on close-following |
| WORKZONE | S0/S1 map (report-only, s01_result.md §6): v3w better than all 14 rules on delay in X1 (+5.0 to +11.6 %) and than 13 of 14 in X2 | favours v3w; the same kind as the trained draw; strongest selection risk |

Claude chose every parameter knowing these priors. No v3w row exists under any Plan B cell.

### 4.5 Excluded kinds

| Kind | Reason |
|---|---|
| outage (V2V lost) | "Not for: V2V with latency or loss" (plant_vv_record_v0.md:11); v3w's commands are void while it lasts (b_env.py:764-786) |
| lane closure or blocked lane | lateral and merge-conflict safety is "Not for"; lane changing is a limit (PR-08); teleports are off, so a stranded vehicle blocks the lane until the run ends; D2's closure stranded vehicles (screen_D2_incidents.md) |
| ALKS share or driver mix | leaves the stated 50 % ALKS; a plant change |
| weather (`fleet.WEATHER`) | calibrated on road ld32, not r2m3 (V204, V206); a change to the driver population |
| brake (one car brakes) | no wave and delay within 2 % on r1m3 (V342); used here only as the placebo |
| burst (H2) | the held wait is not counted as delay (perturb.py:48-56); load at merge 2 (PR-28) |
| corridor-wide 60 km/h limit | mostly delay no controller can remove; driver behaviour unchanged, so not "weather" |
| oracle options | use r1m3 positions (perturb.py:27-30) |

## 5. Metrics

| Role | Measure | Field | What it counts |
|---|---|---|---|
| Primary | Door-to-door delay | `all_delay` | vehicle-seconds in the network and insertion queue minus distance at 100 km/h; unfinished vehicles included (plant_sweep.py:336) |
| Co-headline | Close-following | `ttc_net` | 1-Hz samples with TTC < 3 s, inside and after the window (plant_sweep.py:331); a reward term, disclosed |
| Co-headline | Served flow | `passed` | vehicles entering edge 4; upstream of every Plan B event location except moving trucks |
| Always reported | TTT | `N` | vehicle-seconds, fixed window |
| Stated cost | Robust hard braking | `m_peak_car[2:]` + `m_peak_alks[2:]` + `m_peak_truck[1:]`, per 1,000 vehicle-km (`m_dist_m_*`) | braking events peaking at −4.0 m/s² or harder for cars and ALKS, −3.5 or harder for trucks (measure.py:17-21; s01_result.md:296-322); raw and per vehicle served beside |
| Reported cost | ALKS past their limit | `m_peak_alks[4:8]` | events peaking from −5 to −9 m/s² |
| Gate | Collisions | `collisions` | new SUMO collision pairs per step; includes minGap intrusions and the warm-up; `contact_steps` beside |
| Gate | Moving full-emergency events | `alks_full_moving` | ALKS −9 m/s² events at 2 m/s or more; lane-end creep apart (V377; plant_sweep.py:141) |
| Validity | Drain | `finished_pct`, `flow_min`, ramp `pending` | teleports cannot fire (time-to-teleport −1), so drain and deadlock are checked directly (§7.3) |

- Never used for any reading: the −4.5 m/s² counts (`events_ge45`, `b45_step`), which sit on the braking limit and select by speed (s01_result.md:287-324).
- Disclosed: the stored all-class robust braking excess per vehicle-km reached −8.1 % [−11.0, −4.4] against lr400_16_1 in X1 and −7.2 % [−10.7, −4.9] against 3E-T in X2 (synth computation on stored rows). The 10 % tolerance was set knowing this. Its stated reason: it equals round 2's close-following harm margin.
- **Location report, required for every cell (PR-28):** close-following and delay by road and by period, and ramp-2 lane-end stops (`end_stop2`). `plant_sweep.period()` bins only the slowdown kind (plant_sweep.py:152-165). It is extended to each cell's event window (SURGE 600-1,200 s, TRUCK 360 s to the last capped truck's exit, WORKZONE 600-1,200 s), covered by C1.
- Reported, no reading: TTC < 2 s and < 1.5 s, `sev3`, `b3_step`, `gap25`, ramp delays, the pack's jam and congestion metrics.

## 6. Seeds

Proposed block for the author's approval: **7,480,000-7,480,999.** It collides with no derived stream (kind random's seed + 910,000 is not used; CMA seeds 20261108 and up; bootstrap rng 20261108).

| Seeds | Stage | Use |
|---|---|---|
| 7,480,000-009 | S1, S5 | smoke, identity, T3, traced against untraced |
| 7,480,010-049 | S2 | plant gates, rung 1 (cell and S rows) |
| 7,480,050-089 | S2 | plant gates, rung 2, only for cells that fail rung 1 |
| 7,480,090-099 | S1-S2 | re-runs under the bug rule |
| 7,480,100-119 | S3a | grid re-pick, per cell and in S |
| 7,480,120-149 | S3b | pilot; never evidence |
| 7,480,150-189 | S4 | 3E search pool |
| 7,480,190-229 | S4 | 3E check set (admission, incumbent, stopping) |
| 7,480,230-249 | S4 | ASCH tuning |
| 7,480,250-269 | S4 | ASCH check |
| 7,480,270-309 | S4 | MPC-F fitting data |
| 7,480,310-339 | S4 | MPC-F validity gate |
| 7,480,340-399 | | reserved |
| 7,480,400-519 | S6 | evaluation, n = 120, used once, the same seeds in every cell and in S |
| 7,480,520-999 | | reserved; any use needs its own V# |

No seed is used before approval. A re-run under the bug rule uses the same seeds and is not a new round.

## 7. Tool checks and smoke checks (criteria fixed before they run)

### 7.1 S0: build checks (no simulation except unit tests)

- **Unit tests on planted rows** for every reader: W, W-b, T, L, gate failures, one bad learner (W) and two (not W), pilot GO and KILL, G1 pass and fail, and R with its null.
- **Spec tests for new code:** TRUCK selects exactly the specified trucks and changes only their `max_speed`; SURGE's planned departures per segment, pooled over 40 seeds, lie within 3 SE of the profile, and inserted equals planned (PR-02); the extended period bins; the cma2 stopping rule fires on a planted plateau and not on a planted slope.
- **PR-15 by inspection:** no actor input and no rule, ASCH or MPC-F input carries the limit, the event time or the demand; the global vector stays critic-only.
- **Adversarial code review** (ultracode on) before S1, and again before S6.
- Code on branch `planb/core` from `r2/metrics` at `79b889b`, in a worktree under `~/work/phd/wt/planb`.

### 7.2 S1: smoke, identity, determinism (about 100 runs, laptop by day)

| Check | Pass criterion |
|---|---|
| C1 identity | V475's 7 stored acceptance rows (round 2, pack on) reproduce on every key at the Plan B commit; only identity is printed |
| C2 T3 | per cell and rung and S: no control, p333, one learner and 3E-T on seed 7,480,000, twice; every key equal; repeated on each later machine (V436, V465) |
| C3 spec | WORKZONE: a 0.1-s limit trace reaches the target at t0 + 20 s, holds and returns at t0 + 600 s. TRUCK: the capped truck IDs and departure times are identical across arms on each seed, and no capped truck exceeds its cap. SURGE: the per-segment counts as in §7.1 |
| C4 equal before onset | per-minute series equal S on the same seed and arm: SURGE and WORKZONE until 600 s, TRUCK until the first capped truck departs |
| C5 measurement | traced rows equal untraced rows (V386); pack-on rows equal pack-off rows (measure2.py smoke); no counter calls `CavEnv._x` |

Any failure stops the stage until it is fixed and logged.

### 7.3 S2: plant gates per cell (at most about 1,060 runs, laptop by day, pack on)

Arms: no control, p333 and 3E-T in the cell and in S on 7,480,010-049; the placebo with no control and p333. No v3w. Statistic: round 2's paired effect against each arm's own S row, 95 % percentile bootstrap, 20,000 resamples.

| Gate | Criterion |
|---|---|
| G1a it hurts | delay in the cell at least 10 % above S, CI lower bound > 0, for no control and for p333 |
| G1b it congests | congested vehicle-seconds (pack space-time cells below 60 km/h, measure.py:300) at least 10 % above S, CI lower bound > 0, for no control and for p333. For WORKZONE, cells on edge 2 and the 300 m before it are excluded while the limit is reduced, so only a queue reaching further upstream counts (V342's upstream rule) |
| Null of G1 | the placebo (V341: a human car slows by 5 % for 1 s every 180 s; `brake` kind, factor 0.95, hold 1 s) must fail G1a and G1b. If it passes either, the gate is broken: stop, fix, log |
| G2 control matters (CLAUDE.md early KILL) | p333 or 3E-T has at least 10 % less delay than no control in the cell, CI excluding 0; if both fail, every carried rule is run before a KILL. This gate cannot fail because of the cell: p333 already has about 37 % less delay than no control in steady traffic (decide3_map.csv medians, planning) |
| G2-loss (report-only) | the better of p333 and 3E-T loses at least 10 % less delay to the cell (cell minus S) than no control does, CI excluding 0 (V343). If it fails, the resilience reading is still run but is expected to fail; this is stated now |
| G4 artefacts | (i) PR-09: 1-Hz braking within 5 % of step braking for both arms; (ii) drain: after the event, `flow_min` and ramp `pending` return within 10 % of S within 300 s, and no vehicle stands still for 300 s outside a queue (traced on 3 seeds); (iii) p333's collisions and contact steps at most S's + 1 per run (medians); (iv) PR-24 counter traces on 2 seeds equal the row counts |
| Location (required report) | lane-end stops by road and close-following by road and period, for both arms |

- **Ladder.** If rung 1 fails only G1, rung 2 runs on 7,480,050-089 with S re-run on those seeds. If rung 2 fails too, the cell drops. A G2 or G4 failure drops the cell without rung 2. The rung choice sees only no control, p333 and 3E-T, never v3w.
- **Exit.** A dropped cell is reported with its gate values and is not re-parameterised. m stays 3. If no cell passes: **KILL at S2**.
- The report-only T2 mechanism check (CLAUDE.md T2) comes free from S3a: whether the per-cell re-picks differ from the steady pick.

### 7.4 Before S3b and before S6

- Before S3b: the code review is done; the protocol is unchanged, or each change is a V# with its reason; the intended-use V#, if the author takes decision 3's alternative.
- S5 smoke on 7,480,000-009 after the opponents are frozen: every row carries the cell spec, controller id and hash, learner id, seed and commit; `pert_log` shows each event; v3w's hashes equal the baseline_v4 checkpoints; the stored and new picks reproduce on the S6 machine on 3 seeds; the reading script runs end to end on the smoke rows. It prints pass or fail only; no performance field is read.

## 8. Statistics and the reading

### 8.1 Statistic

effect = sign × median(P − O) / median(O) × 100 over paired seeds; positive means v3w is better (round_2.md:263-268). P is the per-seed learner mean. Percentile bootstrap, 20,000 resamples of seeds, one index matrix for every comparison, denominator fixed, rng seed 20261108. Disclosed: the median's bootstrap is lumpy when the per-seed differences have a gap (read_power results.md §1); it is kept for comparability (V408).

### 8.2 Level

- Bonferroni **m = 3**, the pre-registered cells, fixed now and never lowered when a cell drops. Two-sided intervals at 98.33 %.
- Inside a cell, "better than every opponent on both measures" is an intersection over opponents and measures, so it needs no further correction (round_2.md:192-194).
- Harm is read at 95 %, because a corrected interval would hide harm (round_2.md:172-174).
- Every reading that feeds a sentence uses 98.33 % (V467), except harm.

### 8.3 Cell outcome (S6, against every opponent o in the cell's deciding set)

| Outcome | Rule |
|---|---|
| **L** | against any o: delay more than 2 % worse by point with the 95 % upper bound < 0, or close-following more than 10 % worse by point with the 95 % upper bound < 0 (round 2's harm rule) |
| **W** | against every o, all of: delay lower bound > 0; close-following lower bound > 0 and median paired reduction at least 20 per run; flow at most 0.5 % worse (point); collisions median(P) ≤ median(O) + 1; moving full-emergency median(P − O) ≤ max(5 % of median(O), 5) (T2's limits, round_2.md:199-202); at least 4 of 5 learners with point estimates > 0 on delay and close-following against every o; no v3w row fails drain |
| **W-b** | W, but robust braking per vehicle-km is more than 10 % worse (point) than some o; the sentence leads with that cost |
| **T** | neither W nor L |

If the two measure conditions hold but a gate or the learner condition fails, the cell is reported as "metric win, gate failure" or "arm win, learners inconsistent", with no claim sentence. No control is never an opponent in W and never stands alone.

### 8.4 Study outcome (decision 6)

- **PASS:** at least one cell W or W-b, and no cell L. The L veto covers every cell evaluated in S6, including pilot-KILLed cells.
- **NULL:** otherwise, including a KILL at S2 or S3b.
- The sentence names every cell's outcome. No cell can be added, removed or swapped after S1 starts.

### 8.5 Resilience reading (decides the word only)

- Read only in a W or W-b cell, at 98.33 %, after W (a fixed sequence, so the family error stays at 5 %).
- Per seed and arm: loss = delay in the cell − delay in S on the same seed, each controller as tuned for the cell (V343: "each controller's loss against its own run without X").
- R(o) = median(loss_o − loss_v3w) in vehicle-seconds, absolute, so no denominator can be near 0. Pass: lower bound > 0 against every o. Reported also as % of no control's median loss (G1 keeps that denominator away from 0).
- R is read only if its label-swap null (per seed, v3w's and o's cell-and-S pairs swap with probability 1/2; 2,000 swaps), computed by the report script before R is printed, gives a false "better" rate of at most 2 × nominal. Otherwise R is reported as "statistic failed its null".
- Close-following resilience is report-only. The power of R is unknown: no stored v3w rows pair steady and perturbed runs per controller. V395 saw v3w's edge in steady traffic too, so R may fail.

### 8.6 Pilot rule (S3b, decision 7)

Per cell, on 30 pilot seeds, against every pilot opponent (15 carried, up to 8 re-picks, the steady pick): **GO** if every delay and every close-following point estimate is at least 0. Otherwise the cell is **KILLed**: no 3E search, but it is still evaluated in S6 against the opponents it has (carried, re-picks, steady pick, ASCH, MPC-F), labelled "no per-cell CMA-ES opponent; KILLed at the pilot". Pilot rows are never evidence.

### 8.7 Report-only rows (95 %, labelled)

- The full operating map per cell and in S: every opponent × delay, close-following, flow, robust braking, ALKS past-limit events, with the 95 % and 98.33 % intervals and the V462(1) tile.
- The V459 bar against no control per cell, at 98.33 %, beside and never alone.
- Adaptation gain (CLAUDE.md asks for it to be pre-registered): AG = e(v3w vs 3E-T) / e(3E-C vs 3E-T) on close-following, and with 3E-D on delay. 3E-T is the rule with v3w's information (both tuned only under condition T). Read only if e(3E-C vs 3E-T)'s 95 % CI excludes 0.
- Per-learner counts; round 2's T2 with its counting filter, for comparison; each tuned opponent against p333 and on its own tuning seeds (the overfitting check); the pilot effects, labelled.

### 8.8 Nulls of the statistics

| Statistic | Null and its value |
|---|---|
| G1 | V341's placebo must fail it (§7.3) |
| W, one comparison | label-swap null at m = 3, n ≥ 40: false "better" 0.8-1.0 % against a nominal 0.83 % (read_power power_tables.md) |
| W, whole rule | 0 % under the global null; 0.5-1.5 % when only the closest opponent's delay is null (synth/rule_v0.json, 200 studies, noise about ±1 point) |
| L under a tie | v3w shifted to tie each opponent: L fires in 5-14 % of studies (14 opponents). Under the label-swap null it fires in 35-43 %, but the swap widens the paired spread when the true effects are large, so the shifted tie is the planning model |
| Pilot | GO 0 % when every effect is 0 (staged/pilot_oc.json) |
| R | its own label-swap null, computed before R is printed (§8.5) |

### 8.9 Power (planning, per cell, m = 3; 14 stored opponents; synth/rule_v0.json, 300 studies per row, noise about ±3-5 points; pilot from staged/pilot_oc.json)

| Effects (proxy) | n = 80 | n = 120 | n = 120 with the F0 pilot |
|---|---|---|---|
| X1-like × 1 | 92 % | 99 % | 98 % |
| X1-like × 0.75 | 80 % | 95 % | 92 % |
| X1-like × 0.5 | 10 % | 42 % | 35 % |
| X2-like × 1 | 35 % | 58 % | 52 % |
| X2-like × 0.75 | 9 % | 25 % | 19 % |
| X2-like × 0.5 | 0 % | 2 % | 1 % |

- These are W or W-b with every §8.3 condition. W-b is 3-9 % of the studies at stored effects. The learner condition costs up to 17 points at half effects (n = 120).
- Delay binds; close-following almost never does (read_power results.md §2).
- Study level, with the veto: one X1-like cell and two tied cells give PASS in about 73-88 % (without the veto about 98 %).
- The true power is lower: up to 28 opponents, converged per-cell searches, a delay-tuned opponent, and new kinds that may look like neither X1 nor X2. More opponents also raise the false-L rate. n above 40 is resampled from 40 stored seeds, so it is approximate. A null is likely in X2-like cells; it is reported as a null.

## 9. Stages, run counts, time and cost

Rates: rental A (V475, EPYC 7702, 59 workers) 2,450-3,050 runs/h measured with the pack on, $0.10-0.13 per 1,000 runs, about 6 % setup on top. Rental B (V461's kind, 244 workers) about 6,400 runs/h, **derived** from V461's search timing, not measured. Laptop 1,330 runs/h by day (V425-V426); at most 40 % CPU from 23:00 to 09:00 (V432). Counts: `synth/count_v0.py`, every cell passing every stage.

| Stage | Content | Runs | Where |
|---|---|---|---|
| S0 | decisions, build, unit tests, reviews | 0 | laptop |
| S1 | smoke, identity, T3 | about 100 | laptop by day |
| S2 | plant gates, both rungs at most | about 1,060 | laptop by day, about 1 h |
| S3a | grid re-pick: 69 rules × 20 seeds × (3 cells + S) | 5,560 | rental A |
| S3b | pilot: 3 cells × 30 arms × 30 seeds | 2,700 | rental A |
| S4a | 3E-C and 3E-D for 3 GO cells: 384 runs per generation + 240 per check | 96,720 (G = 40) to 243,600 (G = 100) | rental B or A |
| S4b | ASCH: 72 configurations × 4 conditions × 20 seeds + check | 6,160 | rental A |
| S4c | MPC-F data and validity gate | 1,160 | rental A |
| S5 | smoke, pick replays on the S6 machine | about 300 | rental A |
| S6 | evaluation: 120 seeds × (3 cells × 34 arms + S 54 arms) | 18,720 | rental A, one platform |

| Every search stops at | Total runs | All on rental A | Searches on rental B, rest on A | Cost (+6 % setup) |
|---|---|---|---|---|
| 40 generations | about 132,500 | 43-54 h | 15 h + 12-15 h | $13-17 ($14-18) |
| 100 (cap) | about 279,400 | 92-114 h | 38 h + 12-15 h | $28-36 ($30-39) |

- Searches are 73-87 % of all runs; the convergence rule sets the budget, and how many generations it takes is unknown.
- KILL at S2: about 1,200 runs, $0. KILL at S3b: about 9,400 runs in total, about 3-4 h rented, under $1.5.
- n = 80 instead of 120 saves 6,240 runs (2-2.5 h, under $1).
- **Budget ceiling, action fixed now:** if spend reaches $40 or machine time reaches 7 days, every running search stops at its next check, its incumbent is frozen and labelled "not converged (budget ceiling)", and the protocol continues. The author is not asked to choose after seeing data.
- Not costed: build and author time (my estimate: 1-2 days of code and tests, plus about a day for MPC-F), re-runs under the bug rule.
- **Operating rules:** check machine resources and that the v6 sessions are idle before every batch; the CPU guard; the night cap; no co-scheduling with training (V392); long runs in their own systemd unit; S6 from a frozen detached worktree at the run commit, with no commits there mid-run; one platform per stage with acceptance passed (V436, V465); rentals picked by the V473 rules, fetch-verify-destroy on any failure (V471).

## 10. What is reported in every outcome; ledger

| Outcome | What follows | Sentence |
|---|---|---|
| KILL at S2 | gate tables per cell and rung, placebo, cost | "As specified, the perturbations did not congest this plant enough to test resilience. No DRL claim." Null |
| Cell dropped at S2 | its gate values in the map | "did not bind at rungs 1-2" |
| KILL at S3b (no cell GO) | pilot effects with 95 % CIs, labelled pilot; re-picks; cost | "In a 30-seed pilot, v3w did not lead every untuned rule in any cell; the study stopped before per-cell CMA-ES tuning." Null |
| Cell KILLed at S3b | its S6 map against the opponents it has, labelled | listed with that label |
| NULL at S6 | the full map, every cell × measure × opponent, R, no control, braking, location, convergence status | §1's null sentence |
| W vetoed by an L | the same map | §1's veto sentence |
| PASS | the same map and the filled sentence with every clause | §1's pass sentence |

- Any T, L or KILLed cell closes the DRL claim against tuned controllers in that cell on this plant: no further training, tuning, plant change or seed round there (as [A3]).
- Any cell proposed after these results is a new study, labelled post hoc, never merged into this one's count.
- Every report also gives: each opponent's provenance (search loss trace, checks, stopping generation, convergence status; grid picks; ASCH configuration; MPC-F's gate result or omission); S2 gate values for every cell, including dropped ones; the planning null and power (§8.8-§8.9) labelled as X1/X2 proxies.
- Disclosures beside every sentence: the closures and that Plan B ran nothing in X1/X2; the intended-use label (or the amendment and its departure from V462(4)); v3w's checkpoint selection on X1/X2 validation; the reward overlap of close-following and 3 m/s² braking; informed per-cell opponents and the look-ahead difference; 3E-T and 3E-X carried as lower bounds; the arm-level rule and learner condition set after round 2; the braking tolerance set knowing the stored excess; the priors in §4.4; `collisions` counts minGap intrusions; teleports disabled; no retraining.
- **Ledger:** every run of every stage in the ledger, including smoke, gates, failed, crashed, KILLed and abandoned ones. Rows under `/home/catalin/work/phd/v5b1_runs/planb/`; summaries in `docs/research/results/planb_*.md`; a V# at each stage gate, committed the same turn.

## 11. Deviations policy

- Before S1: changes go into the protocol by a V#, and the design review sees them.
- After S1 starts: no change to the cells, rungs, opponents, measures, margins, n, m, the pilot rule or the reading. An unavoidable change is a V# with its reason before the affected stage runs. If it touches the reading after any S3b row exists, S6 needs a new seed range and a new V#.
- Bug rule (CLAUDE.md): fix, re-run everything affected on the same seeds, log and report both outcomes. A bug re-run is not a new round.
- A crashed run is re-run on the same seed and commit. A search that crashes resumes deterministically from its stored runs (as V443).
- A platform change mid-stage voids that stage's rows, or the split is disclosed as in V465.
- A broken null (the placebo passes G1), an identity failure or a determinism failure stops the stage until fixed and logged.
- An opponent that cannot be built, or fails its smoke check, is a disclosed omission. m does not change.
- A search at the cap or the budget ceiling is not a deviation; it is labelled as §3.3 and §9 say.

## 12. Risks and limits

| Risk | Effect | Handling |
|---|---|---|
| New cells look like X2, or opponents get stronger | planning power 19-52 % at X2-like effects | a null is a valid outcome, reported as one |
| False L from many opponents at 95 % | a true W elsewhere is vetoed (5-14 % per tied cell with 14 opponents) | stated now; decision 6's alternative |
| WORKZONE does not bind on edge 2 | it drops at S2 | the ladder, then a drop; m stays 3 |
| WORKZONE read as a fourth slowdown round | weakens [A3]'s boundary | the §2.2 rule; decision 2's two-cell alternative |
| Outside intended use | weakens the contribution | the label; decision 3 |
| Priors favour v3w (§4.4) | selection risk in the cell choice | disclosed; no v3w row exists in any cell |
| Searches still falling at 100 generations | opponents are lower bounds | labelled in the sentence |
| ASCH read as a relabelled rule; MPC-F fails its gate | weaker "non-learning" wording | the §1 wording rule |
| Reward overlap | a win on a trained-on measure | disclosed in every sentence |
| Lane changing (PR-08) and ramp-2 lane ends (PR-28) not validated | TRUCK and any merge-2 gain rest on them | carried in the sentences; location report |
| SURGE pairs with S only by seed after 600 s | R and G1 are seed-paired there | stated (§4.3) |
| The median statistic is lumpy | interval bounds jump between clusters | B and the rng fixed; disclosed |
| Rental B's rate is derived; build time not sized in detail | time may differ | a rate check after 5 generations; the ceiling |

**Limits every Plan B sentence carries:** a synthetic plant, not calibrated (V245); ideal V2V (PR-16); lane changing not validated (PR-08); ramp-2 lane-end behaviour not validated (PR-28); one demand level; five learners from one recipe; per-cell rules know the condition; simulation only.
