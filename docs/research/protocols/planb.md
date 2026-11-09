# Plan B protocol v1: v3w under perturbations it was not trained on, against the tuned non-learning controllers tested in each cell

**Status: APPROVED, binding (V480, 2026-11-08).** The author accepted all 13 recommendations in §0 as written. Version v1, 2026-11-08. Time estimates in §9 and decision 7 use V475's 59-worker rate; a machine with quota for 100 workers would take about 40-48 h at the same cost (my arithmetic, not measured).

v1 revises v0 after three reviews (statistics, plant, record; 47 issues). Every change is listed in `planb_v1_changes.md` (beside this file). The planning files named below are under `docs/research/planb/planning/`; the three drafts and v0 are under `docs/research/planb/design/`. No Plan B seed, code or run existed when v1 was written; S0's 21 build-check runs are logged (V481, V482). Every number marked "planning" comes from stored X1/X2 rows (or confirmatory 3's rows, where named) used only as a proxy for size and cost, never as evidence (V478). Planning files: `synth/rule_v0.py` and `rule_v0.json`, `review_stats/*.py` and `*.log` (the statistics review's re-checks), `revise_v1/pp_power.py` and `.json` (per-policy power and side-constraint pass rates), `revise_v1/count_v1.py` (run counts). Literature not read is marked [VERIFY]. "My estimate" marks figures that are not measured.

```
S0 decisions, build, reviews ─► S1 smoke, identity (C1, C1b), T3 ─► S2 plant gates per cell (no control, p333, 3E-T, placebo; no v3w)
  ─► S3a grid re-pick ─► S4 3E-C and 3E-D to 100 generations, ASCH, MPC-F
  ─► S5 freeze, smoke ─► S6 evaluation, n = 240, read once by the committed script (S7)
KILL exit: S2 (about 600 runs, rented, under $1; V483)
```

## 0. Status and open decisions

The protocol becomes binding when the author decides the items below, it is committed in this file on `v5b1` with the status line changed, and a V# records the approval. No stage runs before that. Phase settings (CLAUDE.md table): the design review of this protocol is Extra High with ultracode on; the build is High; the checkpoint before S6 is High with ultracode on.

The approval V# also records: that Plan B's W rule amends V459's bar against tuned rules for Plan B sentences (decision 8); that round 2's T2 braking gate (braking at 3 m/s² at most 5 % worse, round_2.md:201) is replaced in Plan B by a robust-braking tolerance, with V478's "stated cost" as the reason (decision 9); that the cells were chosen after DRL results on related perturbations were known (V456(3), V245; §2.1, §4.4).

### Open decisions

1. **Seeds.**
   - Recommendation: approve 7,480,000-7,480,999 with the partition in §6 (510 seeds allotted to stages at n = 240, 490 reserved; 390 and 610 at n = 120).
   - Pros: no stored keyed seed at or above 7,472,000 and no 7,48x,xxx in any git ref or worktree file (`read_record/seed_scan_summary.txt`; confirmed by the record review); one range per opponent family.
   - Cons: one more block to track in the record.
   - Weaker: the rest of V354's block (7,440,920-999, 80 seeds; its other free space is fragmented) is too small for tuning plus evaluation.

2. **Cells.** Claude chose every candidate below after DRL results on related perturbations were known (H1, V410's profiles, X1/X2; §4.4). V456(3) requires "any disturbance is fixed before control results (V245 caveat)", so the choice is the author's.
   - Recommendation: **two cells** at 5,300 veh/h, 50 % ALKS (§4): **SURGE** (one equal-mean demand step, if the author accepts a profile, decision 3) and **TRUCK** (10 trucks chosen before the run, capped at 40 km/h). **One rung each, no ladder:** a cell that does not bind drops and is reported (V408). m = 2.
   - Pros: two kinds (demand, moving bottleneck), neither a slowdown; no plant file changes; the cell nearest [A3]'s "these slowdowns" and with the strongest DRL-favouring prior is gone; fewer comparisons (97.5 % instead of 98.33 %).
   - Cons: TRUCK and SURGE need new perturbation code; both priors still lean towards DRL (§4.4); TRUCK may not bind (its nearest stored proxy H1 fails G1a, §12), and then Plan B tests SURGE alone at m = 2; no supply-side restriction is tested.
   - Weaker:
     - three cells, adding **WORKZONE** (edge 2, from 600 s for 600 s): it keeps X2's slowdown kind (and, at 30 km/h, X2's own limit), so it is read as a fourth slowdown round; it ends at the merge-1 gore (merge-conflict dynamics the V&V record excludes); SUMO brakes at full decel before an edge with a lower limit (MSCFModel.cpp:112-115), so part of its braking cost would be an artefact; it may not queue at all (§4.3). If kept: 20 km/h, never X2's 30; m = 3; the extra specification in §4.2 applies;
     - a second TRUCK rung (20 trucks, grid 360 + 40k s, k = 0-19, 40 km/h), selected before the run: more chance to bind, one more forking point;
     - a ramped SURGE (300-s ramps, like V410's peak): V410's peak disfavoured DRL (69 % more close-following than the rules), so it balances the priors (decision 3);
     - ramp bursts (H2): the held wait is not counted as delay (perturb.py:48-56), and the load sits at merge 2, where PR-28 is a gap;
     - a corridor-wide 60 km/h limit: mostly delay that no controller can remove;
     - single-edge slowdowns only: a fourth slowdown round;
     - lane closure, outage, ALKS share, weather: excluded (§4.5).

3. **SURGE needs a demand profile (V408).**
   - The question: V408 says "You shouldn't have complicated with profiles. Straight demand level was enough. Keep it in mind for next time." A constant level inside v3w's training draw (4,500-6,000, V420) is not outside the draw. A constant level outside the draw but inside the intended range (4,090-4,499) is lighter traffic, not a disturbance, and would fail G1. So a demand perturbation needs a profile. Does the author accept one profile?
   - Recommendation: accept one profile, the **abrupt step** 5,300 → 6,000 → 4,600 at 600 and 1,200 s. Reason independent of V410: three constant segments are the simplest shape the existing FleetDemand segments express (fleet.py:325-339), with no interpolation; physically, traffic held upstream and released arrives with a sharp front [VERIFY before citing any source on queue-release fronts].
   - Pros: one profile, no variant; equal mean, so no delay comes from added vehicles.
   - Cons: against the author's stated preference; the step shape is the one that favoured DRL in V410 (36-42 % fewer close-following seconds than p333 and os1_15_10), and its sentence carries "shape chosen after V410 was known".
   - Weaker: the ramped shape (V410's peak disfavoured DRL; needs many short segments, as demand_osc.py:18-31 builds them); no SURGE (TRUCK alone, m = 1).

4. **Intended use.**
   - Recommendation: keep V462(4), which is binding: every SURGE and TRUCK row, table and sentence carries "outside the plant's stated intended use". The steady reference rows S (5,300, no event) lie inside the intended use and are not labelled.
   - Pros: follows the rule as written ("labelled, not added to it").
   - Cons: the contribution rests on labelled rows.
   - Weaker: a reviewed V&V amendment with validation evidence for each new condition, logged as superseding V462(4) before any v3w row. S1-S2 show determinism and binding, not validity, so they cannot be that evidence.

5. **Opponents.** V478's core: all 14 rules (here 15 carried: both 3E-X1 and 3E-X2 come along), the 3E rules re-tuned per cell to convergence (3E-C, round 2's close-following objective), and V457's MPC and/or adaptive scheduler. Each item below is an **addition beyond V478** for the author to approve or drop:
   - (a) up to 8 per-cell grid re-picks and 1 steady pick (S3a, 4,200 runs);
   - (b) a second per-cell search, 3E-D, for delay (doubles S4a: about 81,000 runs, $8-11);
   - (c) both ASCH and MPC-F where V457 says "and/or".
   - Recommendation: approve all three. Delay binds (read_power results.md §2): if a delay-tuned opponent beats the stored best rule by 1-3 delay points, W's planning power falls from 99 % to 32 % in X1-like cells and from 57 % to 17 % in X2-like cells at n = 120 (§8.9). A claim without (b) would rest on opponents nobody tuned for the measure that binds.
   - Cons: MPC-F is the heaviest build (about a day, my estimate) and may fail its gate; (b) is most of the rented compute.
   - Weaker: omit MPC-F (the wording names the omission); omit 3E-D (halves S4a; no opponent tuned for delay); 3E-D bounded on close-following (makes the delay half easier); a per-cell scheduler (it knows the cell).

6. **Convergence and budget.**
   - Recommendation: every 3E-C and 3E-D search runs to **100 generations**, with no data-dependent early stop. Checks at g = 20, 30, …, 100 on a check set kept apart from the search pool set the incumbent. At 100 the search is labelled "met the plateau criterion" only if the incumbent's check loss moved by less than a fixed **1.0 loss point (3E-C) or 0.5 delay point (3E-D)** over generations 60-100, otherwise "not converged at 100 generations". That label is a departure from V478's "to convergence", logged in a V# beside the result and named in every sentence. Budget ceiling: spend so far plus the projected cost of S5 and S6 reaches **$40**, or machine time reaches **7 days**; the action is fixed now (§9).
   - Pros: no stop that fires because the noise is large (v0's δ = 2 SE would have stopped most searches at 40 and called them converged); the plan's cost stays under the ceiling (two cells: $21-27 at n = 240; §9).
   - Cons: a search still improving at 100 is a lower bound; a minimum of noisy check losses biases the incumbent's check loss downwards (disclosed).
   - Weaker: v0's early stop with δ = max(1, 2 SE) (stats review: δ ≈ 2.4-3.4 delay points for a delay loss, about v3w's whole stored margin); cap 150; a fixed 40 generations (both round-2 searches were still falling there, round_2_result.md:9, :12, :100); stopping on the search median.

7. **Worker limit on rented machines.**
   - Recommendation: at most **100 worker processes** (CLAUDE.md) in every stage, on one rented machine at a time. At the measured 2,600-3,050 runs/h (V475, 59 workers; a 100-worker machine is assumed to cost the same per run), the two-cell plan at n = 240 takes about 69-81 h rented (§9).
   - Pros: follows the written limit; no V# lifts it (V448 ran validation at 244 workers and V461 ran 122 per search, with no recorded lift; disclosed).
   - Cons: the searches take about 53-62 h, against about 26 h at V461's rate with 244 workers (derived from V461's search timing, not measured).
   - Weaker: the author lifts the limit for rented machines in a V#, which roughly halves the wall time at the same cost.

8. **Claim rule and V459.**
   - Recommendation: PASS if at least one cell is W or W-b and no cell is L (§8.3-§8.4). W is read on the arm (per-seed mean over 5 learners) at 1 − 0.05/m, with at least 4 of 5 learners' point estimates above 0. Harm (L) is read at 95 %. Every W sentence carries two mandatory clauses: "[k] of 5 policies individually met the same W rule" and "[passes | fails] round 2's per-policy bar (T2) against the same opponents". The approval V# **amends V459** for Plan B sentences. Changes against T2 (round_2.md:199-202):
     - close-following margin: at least 10 % (CI excluding 0) → CI lower bound above 0; the 20-per-run floor is kept;
     - unit: each of 4 of 5 policies at the corrected level → the arm at the corrected level plus 4 of 5 learner point signs;
     - braking at 3 m/s² at most 5 % worse (a gate) → robust braking with a 10 % tolerance that can fail the claim (decision 9);
     - collisions and moving full-emergency events, median-type limits → mean-based paired non-inferiority (decision 9);
     - delay at most 2 % worse → delay superiority (stricter);
     - counting filter → none (stricter).
   - Pros: power (planning, n = 120: X1-like 98-99 %, X2-like 57-60 %, against 54.5 % and 1.5 % for the per-policy rule; `revise_v1/pp_power.json`); the per-policy result is printed in every sentence, never hidden.
   - Cons: weaker than the approved thesis bar in its unit and margin; the arm-level unit and the learner condition were set knowing that X2 failed T2's per-policy rule (s01_result.md:718; disclosed).
   - Weaker:
     - per-policy W (each of at least 4 of 5 learners with CIs above 0 at the corrected level on both measures, close-following at least 10 % and 20 per run, delay superiority): keeps V459's unit, no amendment of the unit; planning power at n = 120 is 54.5 % in X1-like and 1.5 % in X2-like cells (97 % and 2 % at n = 240), so X2-like cells are nearly unwinnable;
     - name every L beside the W, with no veto: a sentence could stand beside a shown harm in another pre-registered cell.

9. **Side-constraint tolerances** (fixed before S1, each with its reason).
   - Recommendation:
     - **robust hard braking per vehicle-km: tolerance τ = 10 %**, from V354 ("network TTC and braking at most 10 % worse", 2026-11-04, set before any r2m3 control result). If, against any opponent, the 95 % lower bound of v3w's excess is above 10 %, the cell is "metric win, braking constraint failed": no claim sentence. If the point excess is above 10 % but not shown, the cell is W-b and the sentence leads with the cost;
     - **collisions:** the one-sided 95 % upper bound of mean(P − O) at most **0.02 per run** (one extra collision in 50 runs) against every opponent;
     - **moving full-emergency events:** the same bound at most **0.10 per run** (one extra event in 10 runs).
   - Planning pass rates at stored values (`revise_v1/pp_power.json`): collisions at 0.02 pass in 99-100 % of studies. Full-emergency events at 0.10 pass in 58 % (n = 120) and 91 % (n = 240) of X1-like studies and 98-100 % of X2-like studies; at 0.05, in 0-24 %. So at n = 120 this constraint, not delay, would often decide X1-like cells: in X1, v3w's stored rate (0.100 per run) is twice the lowest opponents' (0.050, copy and z33133; `review_stats/sidecounts.log`).
   - Pros: each constraint can now fail; the braking tolerance comes from a source dated before r2m3's control results.
   - Cons: every value was chosen after the stored rows of all arms were seen, including v3w's braking excess of −7.2 % and −8.1 % (§5), which fall inside 10 % and outside T2's 5 % (disclosed). The choice of V354's 10 % over T2's 5 % was made knowing that.
   - Weaker: T2's 5 % (on a different measure, braking at 3 m/s²); v0's median-based gates (they cannot fail: every arm's median is 0); no failing bound on braking (breaks CLAUDE.md's "side constraints with stated tolerances").

10. **Pilot.**
    - Recommendation: **no pilot.** S2 stays the early, cheap KILL that CLAUDE.md asks for (control must matter); every cell that passes S2 gets both searches.
    - Pros: removes a choice left open until after data (could a pilot-KILLed cell still be W?) and the weaker veto in KILLed cells; one stage less.
    - Cons: a futile cell costs its two searches, about 81,200 runs, $8-11 (§9).
    - Weaker: v0's 30-seed F0 pilot (GO if every delay and close-following point estimate against every untuned opponent is at least 0). If chosen, two rules are added: a pilot-KILLed cell can only be T or L (if its S6 rows meet W, it is "metric win without a per-cell tuned opponent", with no claim sentence and no count toward PASS; its L still vetoes); and 3E-D runs in every cell that passed S2, so the veto in a KILLed cell is read against a delay-tuned opponent. Its operating characteristic at a realistic tie (v3w equal to the best rule, ahead of the others): GO in 9 % of X1-like and 30 % of X2-like studies at 30 seeds (`review_stats/power.log`, tieb). It screens only against untuned opponents and cannot predict the per-cell searches: with a delay opponent 1-3 points stronger than the stored best, W falls to 17-32 % while GO stays at 72-87 % (`review_stats/power_shift.log`).

11. **n.**
    - Recommendation: **240** evaluation seeds, the same in every cell and in S (7,480,400-639).
    - Pros: planning power in X2-like cells 91 % instead of 57 %; with a delay opponent 1 point better than the stored closest rule, 70 % instead of 17 %; the full-emergency constraint passes in 91 % instead of 58 % of X1-like studies (§8.9). Cost: +13,440 runs with two cells, about $1.4-1.9 and 5 h.
    - Cons: S6 roughly doubles; every n above 40 is resampled from 40 stored seeds, so these figures are approximate.
    - Weaker: n = 120 (80 % power needs v3w roughly 3 delay points ahead of the strongest opponent); n = 80.

12. **[A3] reading, code change and TRUCK's reading.**
    - Recommendation:
      - new perturbation code is a code change, not a plant change, when V475's 7 stored acceptance rows (C1) and an unconditional steady and rule-class replay (C1b) are bit-identical at the run commit (§7.2);
      - no Plan B run or tuning takes place in X1 or X2;
      - TRUCK is a perturbation, not a population change: the fleet composition, class shares and driver parameters stay as drawn; only 10 named trucks get a speed cap, as H1 did at run time (perturb.py:103-111). Weather and the ALKS share change every vehicle's behaviour, which is why they are excluded (§4.5);
      - a restriction cell (only if WORKZONE is kept) must differ from both X1 and X2 in at least two of edge set, limit, duration and number of events, and lie outside the training draw by edge or by limit (§2.2).
    - Pros: fixes [A3]'s undefined cell boundary and the code/plant line before data.
    - Cons: an examiner may still read TRUCK's cap as a population change.
    - Weaker: treat any new code as a plant change; Plan B would then need its own plant and V&V record.

13. **Place in the thesis.**
    - Recommendation: a V# amends outline_v1: chapter 6 becomes **"Disturbed plants: per-CAV DRL against tuned controllers under pre-registered perturbations"** (Plan B). It absorbs "Learning or adaptation?" (outline_v1.md:66; its MPC and scheduler are built here) and chapter 7 (outline_v1.md:67). "Resilience" enters the title only if the R reading passes in a W cell (§8.5). This narrows V478's working name "6. Plan B, resilience against tuned rules"; the author is told so.
    - Pros: the title never claims more than the data; chapter 7 already reads "disturbances fixed before control results".
    - Cons: an outline change after round 2; the working name changes.
    - Weaker: V478's working title whatever R shows (breaks §1's word rule); leave Plan B inside chapter 7.

## 1. Question and claim sentence

**Question.** Under pre-registered perturbations it was not trained on, does the frozen per-CAV DRL headway policy v3w have less door-to-door delay and less close-following than each of the non-learning controllers tested in the cell, on this plant, and at what hard-braking cost?

The claim is conditional (V478; the author's principle of conditional advantages). It speaks of the named cells only, at 5,300 veh/h, on `plant_c3`. m below is the number of cells the author approves (2 recommended: 97.5 %; 3: 98.33 %).

**"[x] % [CI]"** follows claim review D4's recommended form (claim_review_round2.md:55-60; not approved there): the per-learner point range against the closest opponent on that measure (the lowest arm lower bound), the lowest per-learner lower bound at 1 − 0.05/m, and the arm's effect with its CI at 1 − 0.05/m beside it.

**Sentence if PASS** (filled from S6 only):

> On the simulated r2m3 freeway (synthetic, uncalibrated, 50 % ALKS, 5,300 veh/h, outside the plant's stated intended use), under [cell: one-line spec], a pre-registered perturbation outside its training draw, chosen after DRL results on related perturbations were known (H1, V410, X1/X2)[; SURGE: shape chosen after V410 was known], the per-CAV DRL headway policy (5 independently trained learners) had [x] % [CI] less door-to-door delay and [y] % [CI] less close-following than each of the [k] non-learning controllers tested in this cell (p333 fixed; [j] tuned for this perturbation on separate seeds, among them CMA-ES rules for close-following and for delay, [each: met the plateau criterion at 100 generations | not converged at 100 generations]; [i] tuned for other conditions and run unchanged; one rule distilled from DRL policies; [ASCH; MPC-F | MPC-F failed its validity gate | omitted: reason]), with served flow [f] % [CI] against the closest opponent on flow. [k'] of 5 policies individually met the same rule; it [passes | fails] round 2's per-policy bar (T2). Its robust hard braking per vehicle-km was [z] % [95 % CI] higher than [opponent with the largest point excess]'s[, and [z'] % [95 % CI] higher than [opponent with the lowest upper bound]'s], [within | above, by point,] the 10 % tolerance. Merge-conflict and lane-change dynamics are not validated (PR-08, PR-28). In [other cell] it [showed no clear difference (neither W nor L; harm not excluded) | did not bind | …]. Cells not listed are not shown to be unharmed where the CI is wide. This line's per-CAV DRL policies have been tested in [N] perturbation cells on this plant: [list with outcomes].

Clauses, each filled by its own rule:
- **Resilience** (§8.5): "It also lost less delay to the perturbation than each of them." Only then may "resilience" or "resilient" be used. Otherwise: "This is a lower delay level under the perturbation; it was not shown to be resilience (its advantage was not shown to be larger than in steady traffic)."
- **W-b:** the braking clause comes first.
- **No control** (V459, reported in every case): "… and [d] % [CI] less delay than no control, with close-following [not shown to differ: e % [95 % CI] | shown higher by e % [95 % CI]] under round 2's harm rule." "Shown higher" if V459's harm half fires (point more than 10 % worse and the 95 % upper bound below 0, round_2.md:197; claim review D3's 95 %).
- **Opponent wording:** always the bounded form above, with the counts filled. Never "every tuned non-learning controller" or "every tuned controller" without the count and the breakdown, in any sentence, the NULL sentence included.
- **Limits:** the V&V limits L1-Ln; for TRUCK, "merge-conflict and lane-change dynamics not validated (PR-08, PR-28)", unconditionally; PR-28 also in any cell where more than 50 % of the delay reduction against the closest opponent on delay falls on roads 4a and 4 plus ramp 2 (r2, rj2), by the location report's road bins (§5). Amended by V482: share = the median paired difference (that opponent minus v3w's arm) of road delay (veh-s − dist / 27.78) summed over 4a, 4, ramp 2, the ramp-2 insertion queue and the junction lanes, divided by the same quantity summed over every road group, insertion queue and the junction lanes; read only when the denominator's point is above 0, otherwise "not read"; the reward overlap of the close-following measure.
- **Count of cells tested:** the list (at least X1, X2, H1, H2, the band and the Plan B cells, with which policies and outcomes) is compiled from the record before S1 and committed. Unit (V482): every (perturbation spec × demand level) cell on r2m3 in which a per-CAV DRL policy of this line ran, exploratory included: N = 90 (80 on this plant, 10 on its earlier P0 version, stated together), plus each Plan B cell that reaches S6 (92 with both, 91 with one, 90 after a KILL at S2); r1m3 and m32 rows are named, not counted (`docs/research/planb/cells_tested.md` on `planb/core`).

**Sentence if NULL:**

> Under the pre-registered perturbations [cells], v3w was not shown to have both less delay and less close-following than each of the [k] non-learning controllers tested in each cell ([breakdown as above]). Per cell: [T (no clear difference; harm not excluded) | L | W, vetoed | metric win, gate failure | metric win, braking constraint failed | arm win, learners inconsistent | did not bind]. Closest opponents: [names, effects, CIs]. Cells not listed are not shown to be unharmed where the CI is wide. This is a null result, reported as one (V243, V456). [count of cells tested, as above]

**Sentence if an L vetoes a W:** "In [cell], v3w had [x] % more [delay | close-following] than [opponent] ([95 % CI]), so no advantage is claimed in any cell." The W cell is reported as "W, vetoed".

**Words never used** (outline_v1.md:55; V462(3)): "proven", "safe" or "safer", "verified and validated", "realistic", "tied" or "no more" for a T outcome, "converged" (use the plateau wording), "resilience" or "resilient" unless R passes, any field or calibrated-traffic claim, "first" or "novel", any win on a measure not pre-registered here. **No sentence claims a win on one measure alone; tiles are descriptive (V462(1)).**

## 2. Closures, selection and intended use

### 2.1 X1 (V395, [A3]), X2 (V466) and what the stored rows were used for

- [A3]: "If no primary cell is won, this DRL line closes on these slowdowns: no further training, tuning, plant change or seed round" (confirmatory_3.md:132). V395 closed X1 under it. V466 and round_2_result.md:432 close the DRL claim against tuned rules in X2 on this plant. X2 has had 4 tests and X1 3 (round_2_result.md:239-246).
- **Plan B runs nothing in X1 or X2:** no v3w row, no rule tuning, no seed round. [A3]'s "tuning" is not limited to DRL, so no rule is re-tuned there either.
- The only X1/X2 runs are identity replays of 7 stored rows (S1, check C1). They print bit-equality only, as V475's acceptance did.
- 3E-X1 and 3E-X2 run unchanged as transfer opponents in the new cells. Running a stored rule elsewhere is not tuning in X1 or X2.
- The stored X1/X2 rows are not evidence. They were used, and this is disclosed, for: power and cost; the braking tolerance choice and the side-constraint tolerances (decision 9); the shape of the W rule (arm level plus the learner condition, decision 8); and the priors of every cell (§4.4).
- **Selection (V456(3), V245):** V456(3) requires that "any disturbance is fixed before control results (V245 caveat)", and V245 says "tuning the plant after seeing control results would breach the 'no lie with statistics' rule". Plan B's cells were chosen after DRL results on related perturbations were known (H1, V410's profiles, X1/X2). No v3w row existed when the cells were approved (V480); one S0 crash-check row exists (TRUCK, w0u250, 7,480,000), not read for performance (V482). The cell choice is the author's (decision 2), and every sentence carries the disclosure.
- Claim review D1 and D8 (claim_review_round2.md:34-40, :83-89) do not block Plan B, because Plan B makes no X1/X2 row. The approval V# says so.

### 2.2 Cell boundary (decision 12)

- A cell is new if its kind differs from X1/X2's (a tapered speed-limit drop on one edge, at constant demand). SURGE and TRUCK differ by kind.
- Only if WORKZONE is kept: a restriction cell is new only if it differs from both X1 and X2 in at least two of edge set, limit, duration and number of events, and lies outside v3w's training draw by edge or by limit, not by duration alone and not by 5 km/h alone. This rule was written while WORKZONE was being designed (disclosed).
- Every cell lies outside the training draw (perturb.py:35-39; §4.1).

### 2.3 Plant change and code change

- No plant file changes: `plant_c3.json`, the network, the fleet composition and the 50 % share stay as they are.
- New code: the `surge` and `truck_fixed` perturbation kinds, the reorder in `MergeEnv.reset` for SURGE, the period bins for the new kinds, the new measurement keys (§5), the cma2 changes (§3.3), ASCH, MPC-F and the readers.
- This is a code change, not a plant change, if C1 (V475's 7 stored acceptance rows) and C1b (an unconditional replay of S and of every rule class) are bit-identical at the run commit (§7.2). The author confirms this reading (decision 12).

### 2.4 Intended use (V462(4), decision 4)

- The V&V use is "steady or with tapered slowdowns (X1, X2)" at 4,090-6,000 veh/h with 50 % ALKS (plant_vv_record_v0.md:9). V462(4) labels condition T, H1 and H2 outside it (plant_vv_record_v0.md:15). Both Plan B cells are outside it as written; the S reference rows are inside.
- Default: every SURGE and TRUCK row, table and sentence carries "outside the plant's stated intended use".
- **Both cells involve dynamics the V&V record excludes.** "Not for: … lateral or merge-conflict safety" (plant_vv_record_v0.md:11). TRUCK runs capped trucks in lane 0 through both merges: lane 0 of edges 2 and 3 feeds the lane next to each acceleration lane (corridor.py:84, :89), so ramp vehicles merge around them and others pass by lane change. SURGE loads both merges. Lane changing is not validated (PR-08), and ramp lane-end behaviour is a gap (PR-28). Every TRUCK sentence carries "merge-conflict and lane-change dynamics not validated (PR-08, PR-28)" unconditionally; SURGE carries PR-28 under §1's location rule. (If WORKZONE is kept: it ends at the merge-1 gore, edge 2 ends at node m, x = 3,500, where 3a starts and ramp 1 joins (corridor.py:24-25, :82), and ramp 1 stays at 100 km/h, so it also carries the unconditional clause.)
- The record is an unreviewed draft (6 met, 13 partial, 7 gap, 2 limit of 28; plant_vv_record_v0.md:3). "Verified and validated" stays out of every sentence (V462(3)).

### 2.5 No retraining

v3w stays at w0u250, w1u500, w2u250, w3u500, w4u500 (V478). Disclosed: these checkpoints were chosen by round 1's rule on round 2's X1/X2 validation seeds (round_2.md:45, :158-162), so v3w was selected on slowdowns, though not on any Plan B cell.

## 3. Policy under test and opponents

### 3.1 Policy under test

- v3w only, run as in round 2's test job (`round2/test/job_6c49e7e.json`), with only the perturbation and the seeds changed. S0 checks that the job settings match.
- Arm value per seed = the mean over the 5 learners (round_2.md:163, :263-268).
- tail and sw are not run: they are the same line of evidence, chosen on the same validation.
- What v3w sees (b_env.py:896-952): 16 local inputs. It never sees the speed limit, the demand, the time or an event. The global vector, which holds time and flow, feeds the critic only (b_env.py:950-953). It meets every Plan B perturbation only through local traffic.

### 3.2 Opponents per cell

| Group | Members | How tuned | Seeds | In S6 |
|---|---|---|---|---|
| Carried rules (15; V478 core) | p333, z33133, r4a1, lr400_13_2, lr1000_16_2, lr1000_10_1, lr400_16_1, a4400_10_1, os0_10_10, os1_15_10, os1_10_0, copy, 3E-T, 3E-X1, 3E-X2 | As stored (baseline_v3/opponents.json; round 2), for X1, X2 or condition T; run unchanged | old | yes |
| Grid re-picks (up to 8; addition (a)) | Per form (uniform, zone, on-4a, local, adaptive-4a, own-state) the lowest close-following admissible rule; the delay opponent; the front row | Confirmatory 3's procedure (confirmatory_3.md:48-64), 69 tunable rules, run in the cell | 7,480,100-119 | yes |
| Steady pick (1; addition (a)) | The lowest close-following admissible rule in steady traffic at 5,300 | The same procedure in S | 7,480,100-119 | yes |
| 3E-C (per cell that passed S2; V478 core) | ZoneOwnState, 20 parameters, close-following objective | §3.3 | pool 150-189, check 190-229 | yes |
| 3E-D (per cell that passed S2; addition (b)) | The same family, delay objective | §3.3 | pool 150-189, check 190-229 | yes |
| ASCH (V457; addition (c) if both) | One cell-agnostic scheduler for every condition | §3.4 | 230-269 | yes |
| MPC-F (V457; addition (c) if both) | Fitted cost model, receding horizon, one model for every condition | §3.5 | 270-339 | if its gate passed |
| No control | | Never deciding, never alone, in every table | | yes |

- Admissible in the grid: median paired delay at most 2 % worse than p333 and collisions at most p333's + 1. Delay opponent: the lowest median delay among rules with close-following at most 10 % worse than p333. Front row: the lowest close-following among rules with delay at most 10 % worse.
- Duplicates are run once and counted once. A cell has up to 28 deciding opponents.
- **No counting filter** (round_2.md:66-68): a filter removes opponents, which would make the claim easier.
- Disclosed, favouring the rules: per-cell tuned rules know the condition in advance; LocalRule-type rules read 400-1,000 m of roadside speeds ahead (b_env.py:991-1015), while v3w sees its own 200-m bin and a leader within 100 m; ASCH and MPC-F read zone-level roadside data (computed in `_net_stats`, b_env.py:788-846).
- Disclosed, favouring v3w: 3E-T stopped at 40 of 100 generations (V443); 3E-X1 and 3E-X2 were still falling at 40 (round_2_result.md:9, :12, :100). They are carried as lower bounds. The per-cell searches run to 100 generations (§3.3).
- copy was traced from DRL policies. It stays an opponent, because removing it would make the claim easier.

### 3.3 The per-cell CMA-ES searches

| Item | 3E-C | 3E-D |
|---|---|---|
| Family | ZoneOwnState, 5 zones × 4 parameters (cma2.py:39-60) | same |
| Search | Diagonal CMA, population 24, σ0 0.25, 16 seeds per generation in a moving window over the 40-seed pool; no measurement pack (V468) | same |
| CMA seed | 20261108 + cell index | 20261118 + cell index |
| Start | the cell's own-state re-pick (V482: if S3a picks none in the cell, its lowest close-following own-state rule ignoring admission, disclosed), encoded as cma2.start: upstream zone off | p333 (th 0 and free 3 in every zone) |
| Loss | pooled close-following change against p333 (%) + 10 per % of delay above +1 % + 5 per collision above p333's | pooled delay change against p333 (%) + 5 per collision above p333's |
| Admission (check seeds) | delay at most +2 % over p333 (point); collisions at most p333's + 1 | collisions at most p333's + 1; moving full-emergency events at most p333's + max(5 %, 5) |
| Generations | 100, no early stop | same |

- The delay penalty is 10 per % (round 2: 5), because round 2's X1 search drifted past admission and its pick came from generation 3 (V461; round_2_result.md:9).
- 3E-D's admission has no close-following bound. It is the strongest delay opponent the family can give; a close-following bound would make the delay half of the claim easier. Admission stays permissive (median-type), because it only makes the opponent stronger; the W rule's own mean-based constraints still apply against it.

**Incumbent and plateau label:**
1. At generations 20, 30, …, 100, re-run on the 40 check seeds the 5 best distinct configurations since the last check (ranked by loss minus the generation median) and the current CMA mean.
2. Incumbent = the admissible configuration with the lowest check loss so far.
3. Every search runs to generation 100. There is no data-dependent early stop.
4. Label: "met the plateau criterion" if the incumbent's check loss at 60 minus that at 100 is below 1.0 loss point (3E-C) or 0.5 delay point (3E-D), fixed and not scaled by any SE; otherwise "not converged at 100 generations". The second label, and any stop by the budget ceiling (§9), is a departure from V478's "to convergence", logged in a V# beside the result.
5. The opponent is the incumbent at generation 100 (or at the ceiling stop). Check-seed rows are not evidence. Picks are frozen in a committed JSON before S5.

Disclosed: picking the minimum of noisy check losses biases the incumbent's check loss downwards.

**Code (a tuning-harness change; each item with a planted-row unit test, §7.1):**
- (V481: built as `docs/research/planb/cmab.py`, which imports cma2's functions and fixes every setting of this section in code; cma2.py is unchanged) `common.COND` gains the new cells;
- `--objective {ttc, delay}`, with a delay objective beside the pooled-TTC `objective()` (cma2.py:117-139);
- `alks_full_moving` added to `KEYS` (cma2.py:45), which 3E-D's admission needs;
- `--start-params` taking an encoded zone list, because `start()` reads only own-state rules from the opponents file (cma2.py:68-73): p333 = th 0 and free 3 in every zone; an own-state re-pick encoded from its dict;
- periodic checks at g = 20, 30, …, 100 on the check seeds, with a persistent incumbent file;
- a shortlist limited to the generations since the last check (the current one ranks over all generations).

### 3.4 ASCH, the cell-agnostic scheduler

V457 asks for "a non-learning adaptive scheduler" without defining how it differs from the state-feedback rules. Here it is a two-regime gain scheduler.
- One controller for every condition (S and every cell). It does not know the cell. **Disclosed: switching is cell-agnostic; its components are cell-tuned.**
- Inputs: the mean speed of three roadside zones from the existing roadside bins (computed in `_net_stats`, b_env.py:788-846): Z1 edges 1-2 (before merge 1), Z2 edges 3a-3 (between the merges), Z3 edges 4a-4-5 (after merge 2). Decision every 5 s, as the rules.
- Undisturbed: it applies the steady pick. Disturbed (any zone below θ for τ s): it applies R_dist. Back to undisturbed when every zone stays at or above θ + h for τ s.
- Both rule objects are called at every decision and only the chosen one's action is applied, so the stateful rules (RoadLevels' `last`, AdaptiveOn4a's `on_4a`; b_env.py:1056-1103) stay current.
- Library for R_dist: 3E-T and each S2-passing cell's 3E-C.
- Grid: θ ∈ {40, 55, 70} km/h, τ ∈ {10, 30, 60} s, h ∈ {5, 15} km/h, R_dist from the library (54 configurations with two cells, 72 with three), plus "never switch" (the steady pick alone).
- Tuning: every configuration on 20 seeds (230-249) in S and in every cell that passed S2, with p333 on the same seeds as the reference. Pick: the lowest mean (over conditions) of the median paired delay change against p333, among configurations with close-following at most p333's and collisions at most p333's + 1 in every condition (points). The top 5 are re-run on 250-269 with p333; the best admissible one there is ASCH.
- It differs from LocalRule, AdaptiveOn4a and OwnState because it switches whole tuned rule sets corridor-wide on a detected regime. An examiner may still call it a relabelled rule (§12).

### 3.5 MPC-F, the fitted-model MPC

- Port of `claude/v5b-core:vsl_lab/jobs/mpcf.py` (written for BN4 meter scheduling; it holds each setting for 10 decisions × 30 s and labels the next 300 s, "constant input over the prediction horizon"). The port's source branch and commit go into the commit message (CLAUDE.md). It never gets the true model.
- Actions, applied network-wide: p333, the steady pick, 3E-T and each S2-passing cell's 3E-C (5 with two cells). Every 30 s it picks the action with the lowest predicted cost over the next 300 s, assuming that action is held.
- Model: an MLP (2 × 64, tanh) predicting the 300-s cost (delay in vehicle-seconds + 10 × close-following vehicle-seconds; weights chosen, not derived).
- Inputs, fixed now: zone speeds and counts from the roadside bins; accelerating-lane counts on 3a_0 and 4a_0; ramp queues = vehicles below 1 m/s on r/rj and r2/rj2 (measure.py QUEUE_V). No pending list (a virtual origin backlog that roadside detectors cannot measure, PR-15), no time, no demand.
- Data: each action held for 300 s with a random initial offset; label = the 300-s cost under the held action. 4 schedules per seed on 40 seeds (270-309), in S and in every cell that passed S2. One model for every condition. Held-out MSE is reported at 50 % and 100 % of the data.
- **Validity gate, fixed now:** the best single fixed action is chosen on the fitting seeds (270-309), by the sum over conditions of per-condition median realised cost. On 30 gate seeds per condition (310-339), MPC-F passes if the sum over conditions of its per-condition median realised cost does not exceed that of the chosen fixed action. If it fails, MPC-F is a disclosed failed build, it is left out of the deciding set, and §1's wording names it.
- Known limit: a data-driven model captures capacity-drop hysteresis only as far as the held-action data show it (docs/paper1/plan.md:515 warns about straw-man MPCs [VERIFY the L62 source cited there]). METANET was stopped (D5.5) and is not used.

## 4. Perturbation cells

### 4.1 The training draw every cell must avoid

v3w trained under kind `random` (perturb.py:35-39): no event in one third of episodes, otherwise one tapered slowdown on edge 3, 4 or 5 at 25-60 km/h for 60-180 s, starting at 400-1,200 s, at constant demand 4,500-6,000 veh/h (V420). Steady traffic at 5,300 (S) lies inside the draw and inside the intended use; it serves only as the reference row.

Geometry (corridor.py:24, :45-48; `R2_NODES`): edge 1 0-3,000 m, 2 to 3,500, 3a (merge 1) to 3,800, 3 to 5,000, 4a (merge 2) to 5,300, 4 to 6,300, 5 to 6,800; the main route is about 6,800 m. Run 0-1,800 s, warm-up 300 s (b_env.py:152). Route shares 70/15/15 (main, ramp 1, ramp 2).

### 4.2 Cells

| Cell | Physical meaning | Specification (one rung) | Outside the training draw by | Differs from X1/X2 by | Code |
|---|---|---|---|---|---|
| SURGE | The same number of vehicles, with 10 minutes concentrated at the plant's top level, as when traffic held upstream is released | `{"kind": "surge", "profile": [[0, 600, 5300], [600, 1200, 6000], [1200, 1800, 4600]]}`: mean 5,300 over the run; 6,000 is the top of the intended-use range | kind (training demand is constant per episode, V407) | kind | new perturb kind: `Perturb.demand()` sets `env.dem = fl.FleetDemand(seed, profile, cfg)`; in `MergeEnv.reset`, b_env.py:154-159 (ramp, alks, alks_all, desired) move after `self.pert.demand()`; added to cma2's COND. No runner wrapper |
| TRUCK | Slow heavy vehicles (loaded or special transports) that others must overtake | 10 trucks: for k = 0-9, the first main-route truck with sampled departure lane 0, not already selected, departing at or after 360 + 80k s; each capped at 40 km/h for its whole trip, set before the route file is written. Event window 360-1,800 s | kind (no truck caps in training) | kind | new kind `truck_fixed`: sets the selected trucks' `max_speed` in `Perturb.demand()` (fleet.py:146, :164) |
| WORKZONE (only if the author keeps three cells) | A speed restriction at an incident scene with no lane closed | Existing `slowdown` kind: edge 2, **20 km/h** (not X2's 30), from 600 s for 600 s, 20-s taper, instant return | edge and duration; limit below the draw's 25 km/h | edge set, limit and duration | none (perturb.py:113-125); plus the braking exclusion (§5) and the merge-1 location items |

- TRUCK timing: the last grid time is 1,080 s. At 40 km/h the route takes about 612 s and merge 2 (5,300 m) is reached after about 477 s, so a truck departing before 1,200 s passes merge 2 by about 1,680 s and nearly always exits by 1,800 s. Spec test (amended by V481): exactly 10 distinct trucks per seed, each departing at or after its slot and before 1,800 s; the last truck's departure is reported per seed. Measured over the whole seed block before any run: the 10th truck departs at or after 1,200 s on 9.4 % of seeds (median 1,115 s, 99th percentile 1,306 s, max 1,427 s), so on those seeds the last truck may not reach merge 2 inside the window; the rule is the same for every arm on a seed. (v1 said "all departing before 1,200 s" and "the 80-s grid rarely runs out of trucks"; that was wrong.)
- WORKZONE, if kept, also needs: the braking-event location keys (§5) and the pre-registered exclusion of events peaking on edge 1 within 300 m of edge 2 while edge 2's limit is below 100 km/h; a merge-1 split (3a close-following, ramp-1 `end_stop`, `delay_ramp`); a report-only G4 row for ramp-1 `end_stop` against S; its G1b exclusion (§7.3).

### 4.3 What each cell does to the measures

- **SURGE.** FleetDemand draws one arrival stream and restarts its clock at each segment edge (fleet.py:325-339). Class, route and attributes are drawn by vehicle index (fleet.py:184-203, :343-346). So the run is identical to S until 600 s; after that the departure times differ while the sequence of vehicles stays the same up to the shorter list. With the reorder, the ALKS, ramp and desired-speed sets are taken from SURGE's own list, so extra vehicles are commanded like any other (without it they would be uncommanded ALKS counted as cars by the pack, measure.py:82, :127). Its comparison with S is seed-paired, not identical, after 600 s. Expected vehicles are equal, so no delay comes from added vehicles or lower limits. After the surge the demand is 4,600, below S's 5,300, so SURGE's flow after the queue clears sits about 13 % below S by design (§7.3 does not compare flow with S).
- **TRUCK.** Every arm meets the same capped trucks, because they are chosen from the demand list before the run (unlike H1's run-time choice, perturb.py:103-111). They are inserted already capped, so no braking comes from applying the cap. The run is identical to S until the first capped truck departs. The capped trucks' own extra travel time is at most about 3,700 vehicle-seconds per run (my arithmetic: 10 trucks × (612 − 245) s against 100 km/h; less if a truck's normal speed is lower), about 2 % of no control's steady median of 199,471 (decide3_map.csv, planning). The rest of any delay is the bottleneck effect.
- Realism: magnitudes are design choices, not taken from a measured site. Typical slow-vehicle speeds, moving-bottleneck theory and demand pulses are not read here [VERIFY before citing any; e.g. Gazis and Herman 1992 on moving bottlenecks, not read]. No sentence uses "realistic".

### 4.4 Prior information seen before this draft

| Cell | Prior | Direction |
|---|---|---|
| SURGE | V410 (baseline-v3 policies, not v3w; 10 used seeds; exploratory): the step profile 4,200 → 5,600 → 4,200 gave 36-42 % fewer close-following seconds than p333 and os1_15_10 at the same or 4 % less delay; the ramped peak 4,000 → 5,600 → 4,000 gave 69 % more. S1 at 7,000 (report-only): v3w had the lowest delay | the step favoured DRL and SURGE is a step; the ramped shape disfavoured DRL |
| TRUCK | H1 at 5,300 (baseline-v3 policies only, decide3_map.csv): close-following 458-526 against p333's 534 and lr400_13_2's 1,254 at similar delay. Paired H1 against S (20 seeds): no control +6.3 % [+1.5, +8.4], p333 +4.4 % [−1.0, +8.9] (`review_stats/g1proxy.log`) | favours DRL on close-following; H1 did not bind by G1a |
| WORKZONE (if kept) | S0/S1 map (report-only, s01_result.md §6): v3w better than all 14 rules on delay in X1 (+5.0 to +11.6 %) and than 13 of 14 in X2 | favours v3w; the same kind as X2; strongest selection risk |

Priors that disfavour DRL, seen in the same material: V410's ramped peak (above); in X1 and X2, no control, 3E-T and copy lead on hard braking (s01_result.md §7(d)); from 3,500 to 5,250, nothing is shown against p333 and os1_15_10 (s01_result.md §7(d)). Claude chose every parameter knowing these priors (§2.1). No v3w row existed when the cells were approved (V480); one S0 crash-check row exists (TRUCK, w0u250, 7,480,000), not read for performance (V482).

### 4.5 Excluded kinds

| Kind | Reason |
|---|---|
| outage (V2V lost) | "Not for: V2V with latency or loss" (plant_vv_record_v0.md:11); v3w's commands are void while it lasts (b_env.py:764-786) |
| lane closure or blocked lane | lateral and merge-conflict safety is "Not for"; lane changing is a limit (PR-08); teleports are off, so a stranded vehicle blocks the lane until the run ends; D2's closure stranded vehicles (screen_D2_incidents.md) |
| ALKS share or driver mix | leaves the stated 50 % ALKS; changes every vehicle's draw; a plant change |
| weather (`fleet.WEATHER`) | calibrated on road ld32, not r2m3 (V204, V206); changes every driver's parameters, a population change (TRUCK caps 10 named vehicles and leaves the population as drawn, decision 12) |
| brake (one car brakes) | no wave and delay within 2 % on r1m3 (V342); used here only as the placebo |
| burst (H2) | the held wait is not counted as delay (perturb.py:48-56); load at merge 2 (PR-28) |
| corridor-wide 60 km/h limit | mostly delay no controller can remove; driver behaviour unchanged, so not "weather" |
| WORKZONE (recommended out, decision 2) | nearest [A3]'s slowdowns; merge-1 gore; SUMO limit-braking artefact; may not bind |
| oracle options | use r1m3 positions (perturb.py:27-30) |

## 5. Metrics

| Role | Measure | Field | What it counts |
|---|---|---|---|
| Primary | Door-to-door delay | `all_delay` | vehicle-seconds in the network and insertion queue minus distance at 100 km/h; unfinished vehicles included (plant_sweep.py:336) |
| Co-headline | Close-following | `ttc_net` | 1-Hz samples with TTC < 3 s, inside and after the window (plant_sweep.py:331); a reward term, disclosed |
| Co-headline | Served flow | `passed` | vehicles entering edge 4 (b_env.py:430-431), counted at the entry of edge 4 (5,300 m), downstream of every Plan B event location; capped trucks pass it |
| Always reported | TTT | `N` | vehicle-seconds, fixed window |
| Stated cost, with tolerance | Robust hard braking | `m_peak_car[2:]` + `m_peak_alks[2:]` + `m_peak_truck[1:]`, per 1,000 vehicle-km (`m_dist_m_*`) | braking events peaking at −4.0 m/s² or harder for cars and ALKS, −3.5 or harder for trucks (measure.py:17-21; s01_result.md:296-322); raw and per vehicle served beside |
| Reported cost | ALKS past their limit | `m_peak_alks[4:8]` | events peaking from −5 to −9 m/s² |
| Side constraint | Collisions | `collisions` | new SUMO collision pairs per step; includes minGap intrusions and the warm-up; `contact_steps` beside; mean-based non-inferiority (decision 9) |
| Side constraint | Moving full-emergency events | `alks_full_moving` | ALKS −9 m/s² events at 2 m/s or more; lane-end creep apart (V377; plant_sweep.py:141); mean-based non-inferiority (decision 9) |
| Validity | Drain | insertion backlog, ramp queues, `stuck_n` (new) | teleports cannot fire (time-to-teleport −1), so drain and deadlock are checked directly (§7.3, §8.3) |

- **Braking reading (decision 9):** against each opponent, the effect on robust braking per vehicle-km with its 95 % CI. Constraint failed if the 95 % lower bound of the excess is above 10 % against any opponent. The sentence's [z] = the largest point excess over all opponents, with that opponent and its 95 % CI, plus the opponent with the lowest upper bound if it differs.
- **Disclosed:** the stored all-class robust braking excess per vehicle-km reached −8.2 % [−10.9, −4.4] against lr400_16_1 in X1 and −7.2 % [−10.7, −4.9] against 3E-T in X2 (`review_stats/observed.log`; the record review's recomputation gives −8.1 % [−11.0, −4.4] in X1). The 10 % tolerance was chosen knowing this; its source is V354, not the stored rows.
- **Reported, no reading,** in every table: the −4.5 m/s² counts (`events_ge45`, `b45_step`) and `b3_step`, with the caveat that the −4.5 count sits on the braking limit and selects by speed (s01_result.md:287-324); TTC < 2 s and < 1.5 s, `sev3`, `gap25`, ramp delays, the pack's jam and congestion metrics.
- **New measurement keys** (new key families only; every existing key unchanged, so C1 is unaffected; each with a planted-trace unit test (PR-24) and included in C5):
  - `ttc3_road_<road>` for roads 1, 2, 3a, 3, 4a, 4, 5, ramp 1 (r, rj), ramp 2 (r2, rj2); the existing labels (3, 4a, ramp2, rest; plant_sweep.py:180) stay;
  - `veh_s_road_<road>` and `dist_road_<road>`, giving delay by road as veh-s − dist / 27.78, each also split by the cell's period;
  - for each braking event, the road, lane position and time of its peak (measure.py:141-157 stores none);
  - TRUCK: the share of TTC < 3 s samples within 5 s after a lane change by the follower or the leader (lane_t exists, plant_sweep.py:219-226);
  - `stuck_n` (amended by V481): vehicles below 0.1 m/s for 300 consecutive seconds and not behind a stopped leader (below 0.1 m/s) within 50 m; a moving leader or no leader within 50 m both count, so a lane-end deadlock is caught (a per-row deadlock count);
  - TRUCK: a speed field without the capped trucks' own samples (for G1b).
- **Location report, required for every cell (PR-28):** close-following, delay and braking by road and by period, and ramp-2 lane-end stops (`end_stop2`). `plant_sweep.period()` bins only the slowdown kind (plant_sweep.py:152-165); it is extended to each cell's event window (SURGE 600-1,200 s, TRUCK 360-1,800 s) as new labels.

## 6. Seeds

Proposed block for the author's approval: **7,480,000-7,480,999.** It collides with no derived stream (kind random's seed + 910,000 is not used; CMA seeds 20261108 and up; bootstrap rng 20261108).

| Seeds | Stage | Use |
|---|---|---|
| 7,480,000-009 | S1, S5 | smoke, identity (C1b on 000-002), T3, traced against untraced |
| 7,480,010-049 | S2 | plant gates (cell and S rows) |
| 7,480,050-089 | | reserved (a second rung, only if the author keeps a ladder) |
| 7,480,090-099 | S1 | spare for smoke repeats after a fix; never for gates |
| 7,480,100-119 | S3a | grid re-pick, per cell and in S |
| 7,480,120-149 | | reserved (the pilot, only if the author keeps it) |
| 7,480,150-189 | S4 | 3E search pool |
| 7,480,190-229 | S4 | 3E check set (admission, incumbent, plateau label) |
| 7,480,230-249 | S4 | ASCH tuning |
| 7,480,250-269 | S4 | ASCH check |
| 7,480,270-309 | S4 | MPC-F fitting data and the choice of its best fixed action |
| 7,480,310-339 | S4 | MPC-F validity gate |
| 7,480,340-399 | | reserved |
| 7,480,400-639 | S6 | evaluation, n = 240, used once, the same seeds in every cell and in S (400-519 if n = 120) |
| 7,480,640-999 | | reserved; any use needs its own V# (520-999 if n = 120) |

No seed is used before approval. A re-run under the bug rule uses the same seeds and is not a new round.

## 7. Tool checks and smoke checks (criteria fixed before they run)

CLAUDE.md's tool checks map as follows: T0 (the actuator binds) and T1 (control matters) are G2 (§7.3); T2 (the mechanism) is the report-only G from S3a (§7.3); T3 (determinism) is C2.

### 7.1 S0: build checks (no simulation except unit tests)

- **Unit tests on planted rows** for every reader: W, W-b, T, L, "braking constraint failed", the mean-based side constraints, gate failures, one bad learner (W) and two (not W), the per-policy and T2 clauses, the plateau labels, G1 pass and fail, the drain gate (a planted SURGE row with lower post-surge demand passes; a planted deadlock fails), R with its null, AG's denominator rule.
- **Spec tests for new code:** TRUCK selects exactly the specified trucks (10 distinct per seed, all departing before 1,200 s) and changes only their `max_speed`; SURGE (a), pure Python: planned departures per segment, pooled over 40 seeds, lie within 3 SE of the profile; SURGE after reset: `env.alks_all` equals the set of ALKS in `env.dem`, the route file equals S's for every departure before 600 s, and `row['cfg']` carries the profile; the extended period bins; each cma2 change in §3.3 on planted rows.
- **PR-15 by inspection:** no actor input and no rule, ASCH or MPC-F input carries the limit, the event time, the demand or the pending list; the global vector stays critic-only.
- **Adversarial code review** (ultracode on) before S1, and again before S6.
- Code on branch `planb/core` from `r2/metrics` at `79b889b`, in a worktree under `~/work/phd/wt/planb`.

### 7.2 S1: smoke, identity, determinism (about 130 runs, rented machine; V483)

| Check | Pass criterion |
|---|---|
| C1 identity | V475's 7 stored acceptance rows (round 2, pack on; measure2.py:37-38) reproduce on every key at the Plan B commit; only identity is printed |
| C1b identity | at 79b889b, unchanged, run S on 7,480,000-002 for no control, p333, lr400_13_2, a4400_10_1, z33133, copy, os1_15_10, 3E-T and one v3w learner, plus the brake placebo (factor 0.95, hold 1 s, period 180 s) on one seed; replay at the Plan B commit; every key equal. It covers the `self.pert = None` path (b_env.py:163) and the rule classes C1 misses |
| C2 T3 | per cell and S: no control, p333, one learner, 3E-T, ASCH and MPC-F on seed 7,480,000, twice; every key equal; repeated on each later machine (V436, V465) |
| C3 spec | TRUCK: the capped truck IDs and departure times are identical across arms on each seed, and no capped truck exceeds 40 km/h. SURGE (b): for every planned vehicle, inserted plus pending at each minute equals the planned cumulative count, and no vehicle is dropped by the run's end (PR-03) |
| C4 equal before onset | per-minute series equal S on the same seed and arm: SURGE until 600 s, TRUCK until the first capped truck departs |
| C5 measurement | traced rows equal untraced rows (V386), the new key families included; pack-on rows equal pack-off rows (measure2.py smoke); no counter calls `CavEnv._x` |

Any failure stops the stage until it is fixed and logged.

### 7.3 S2: plant gates per cell (about 460 runs with two cells, the same rented machine as S1, pack on with its space-time field saved; V483)

Arms: no control, p333 and 3E-T in the cell and in S on 7,480,010-049; the placebo with no control and p333. No v3w. Statistic: round 2's paired effect against each arm's own S row, 95 % percentile bootstrap, 20,000 resamples. Each gate is read on medians over the 40 gate seeds.

| Gate | Criterion |
|---|---|
| G1a it hurts | delay in the cell at least 10 % above S, CI lower bound > 0, for no control and for p333 |
| G1b it congests | congested vehicle-seconds (pack space-time cells below 60 km/h, measure.py:300) at least 10 % above S, CI lower bound > 0, **and** a congested length (`congested_km`) of at least 0.3 km for at least 5 minutes, for no control and for p333. For TRUCK, the field without the capped trucks' own samples is used, so only the platoon behind them counts. (If WORKZONE is kept: cells on edge 2 and the 300 m before it, and the first 100 m of 3a from 600 to 1,230 s, are excluded, so only a queue reaching further upstream counts, V342's upstream rule) |
| Null of G1 | the placebo (V341: a human car slows by 5 % for 1 s every 180 s; `brake` kind, factor 0.95, hold 1 s) must fail G1a and G1b. If it passes either, the gate is broken: stop, fix, log |
| G2 early-KILL check (CLAUDE.md; T0, T1) | p333 or 3E-T has at least 10 % less delay than no control in the cell, CI excluding 0; if both fail, every carried rule is run before a KILL. Expected to pass (p333 has about 37 % less delay than no control in steady traffic, decide3_map.csv medians, planning), but not certain: a disturbance can move or shrink the merge congestion that headway control removes. Not evidence that the cell binds; it has no informative null |
| G2-loss (report-only) | the better of p333 and 3E-T loses at least 10 % less delay to the cell (cell minus S) than no control does, CI excluding 0 (V343). If it fails, the resilience reading is still run but is expected to fail; this is stated now |
| G4 artefacts | (i) PR-09: 1-Hz braking within 5 % of step braking for both arms. (ii) drain, medians over the gate seeds: (a) total insertion backlog (all routes) averaged over 1,500-1,800 s at most S's + 10 % (SURGE: at most S's); (b) ramp-1 and ramp-2 queue means (`ramp*_queue_mean`) over 1,500-1,800 s at most S's + 10 %; (c) `stuck_n` (V481's definition) is 0 on every gate row of both arms (amended by V482; S's own stuck rows reported beside). Flow is not compared with S. (iii) p333's collisions and contact steps at most S's + 1 per run (medians). (iv) PR-24 counter traces on 2 seeds equal the row counts |
| Location (required report) | lane-end stops by road and close-following by road and period, for both arms |

- **One rung (decision 2).** A cell that fails G1 drops. A G2 or G4 failure drops the cell too. The gates see only no control, p333 and 3E-T, never v3w.
- **Exit.** A dropped cell is reported with its gate values and is not re-parameterised. m stays at its approved value. If no cell passes: **KILL at S2**.
- **T2 mechanism (report-only, from S3a):** G = (cost of the steady pick in the cell − cost of the per-cell pick) / cost of the steady pick, per cell, on delay and on close-following, beside whether the per-cell re-picks differ from the steady pick.

### 7.4 Before S6

- Before S3a: the code review is done; the protocol is unchanged, or each change is a V# with its reason.
- S5 smoke on 7,480,000-009 after the opponents are frozen: every row carries the cell spec, controller id and hash (MPC-F: its model's SHA-256), learner id, seed and commit; `pert_log` shows each event; v3w's hashes equal the baseline_v4 checkpoints; v3w, the stored and new picks, ASCH and MPC-F reproduce on the S6 machine on 3 seeds, every key equal; the reading script runs end to end on the smoke rows. It prints pass or fail only; no performance field is read.

## 8. Statistics and the reading

### 8.1 Statistic

effect = sign × median(P − O) / median(O) × 100 over paired seeds; positive means v3w is better (round_2.md:263-268). P is the per-seed learner mean. Percentile bootstrap, 20,000 resamples of seeds, one index matrix for every comparison, denominator fixed, rng seed 20261108. Disclosed: the median's bootstrap is lumpy when the per-seed differences have a gap (read_power results.md §1); it is kept for comparability (V408). The side constraints use paired means on the same index matrix (decision 9).

### 8.2 Level

- Bonferroni over the approved cells: **m = 2** (recommended; two-sided intervals at 97.5 %) or 3 (98.33 %), fixed at approval and never lowered when a cell drops.
- Inside a cell, "better than every opponent on both measures" is an intersection over opponents and measures, so it needs no further correction (round_2.md:194).
- Harm is read at 95 %, because a corrected interval would hide harm (round_2.md:197).
- Every reading that feeds a sentence uses 1 − 0.05/m (V467), except harm and the braking and side-constraint bounds (95 %).

### 8.3 Cell outcome (S6, against every opponent o in the cell's deciding set)

| Outcome | Rule |
|---|---|
| **L** | against any o: delay more than 2 % worse by point with the 95 % upper bound < 0, or close-following more than 10 % worse by point with the 95 % upper bound < 0 (round 2's harm rule) |
| **W** | against every o, all of: delay lower bound > 0; close-following lower bound > 0 and median paired reduction at least 20 per run; flow at most 0.5 % worse (point); collisions and moving full-emergency events within decision 9's mean-based tolerances; braking constraint not failed; at least 4 of 5 learners with point estimates > 0 on delay and close-following against every o; no v3w row fails drain |
| **W-b** | W, but the point excess of robust braking per vehicle-km is above 10 % against some o (not shown at 95 %); the sentence leads with that cost |
| **metric win, braking constraint failed** | the delay and close-following conditions hold, but the 95 % lower bound of the braking excess is above 10 % against some o; no claim sentence; does not count toward PASS |
| **metric win, gate failure** | the delay and close-following conditions hold, but flow, a side constraint or drain fails; no claim sentence |
| **arm win, learners inconsistent** | every arm condition holds, but fewer than 4 of 5 learners have positive points; no claim sentence |
| **T** | none of the above and not L; reported as "no clear difference (neither W nor L; harm not excluded)" |

- **Mandatory clauses in every W or W-b sentence** (sentence-feeding, not report-only): "[k] of 5 policies individually met the same W rule" (each learner's own effects at 1 − 0.05/m, the same deciding set, no counting filter), and "[passes | fails] round 2's per-policy bar (T2)" (round_2.md:199-202 per policy at 1 − 0.05/m against every opponent, no counting filter).
- **Drain per row:** a row fails drain if `stuck_n` > 0, or its end-of-run insertion backlog (all routes) exceeds 1.5 × the largest no-control value in that cell's S2 rows. Fixed now; S2 has no v3w row.
- **Seeds and rows:** every seed and every drain-failed row stays in the data. A run that crashes is re-run on the same seed and commit, up to 3 attempts (cma2's ATTEMPTS); a seed that crashes on every attempt is dropped from every arm of that cell, and the drop is reported.
- No control is never an opponent in W and never stands alone.

### 8.4 Study outcome (decision 8)

- **PASS:** at least one cell W or W-b, and no cell L. The L veto covers every cell evaluated in S6.
- **NULL:** otherwise, including a KILL at S2.
- Every cell's outcome is named in the sentence, a braking-constraint failure included. No cell can be added, removed or swapped after S1 starts.
- (Only if the author keeps the pilot, decision 10: a pilot-KILLed cell can only be T or L; if its rows meet W, it is "metric win without a per-cell tuned opponent", with no claim sentence and no count toward PASS; its L still vetoes.)

### 8.5 Resilience reading (decides the word only)

- Read only in a W or W-b cell, at 1 − 0.05/m, after W (a fixed sequence, so the family error stays at 5 %).
- Per seed and arm: loss = delay in the cell − delay in S on the same seed, each controller as tuned for the cell (V343: "each controller's loss against its own run without X").
- R(o) = median(loss_o − loss_v3w) in vehicle-seconds, absolute, so no denominator can be near 0. Pass: lower bound > 0 against every o. Reported also as % of no control's median loss (G1 keeps that denominator away from 0).
- **Null check:** run per opponent before R is printed: per seed, v3w's and o's cell-and-S pairs swap with probability 1/2; 2,000 swaps; inner bootstrap B = 20,000. R is read only if the false "better" rate is at most **1.5 × nominal** (tighter than v0's 2×; the proxy below puts the sign-flip rate at 0.5-1.3 % against 0.83 %, so 1.5× still passes a well-behaved statistic). Otherwise R is reported as "statistic failed its null".
- **Planning proxy (baseline-v3, not v3w; confirmatory 3's rows, 20 seeds; `review_stats/resil.log`):** R against p333 is negative in every stored cell: −8,101 veh-s [−16,995, +8,333] in X1, −1,726 in X2, −3,636 in H1. Planning power at n = 120 is about 0 against p333 and 0.86-0.99 against lr400_13_2. The per-seed SD of R is 17,000-24,000 veh-s; the correlation of the paired differences between cell and S is only 0.06-0.45. No control's median loss in H1 is 12,522 veh-s, so small-loss cells such as TRUCK may leave R unpowered. The sign-flip null at m = 3 gives 0.5-1.3 % against a nominal 0.83 %.
- So R is expected to fail. A W without R is reported as "a lower delay level under the perturbation, not shown to be resilience" (§1), and the chapter title stays neutral (decision 13).
- Close-following resilience is report-only.

### 8.6 Pilot

None (decision 10). The alternative and its rules are in decision 10 and §8.4.

### 8.7 Report-only rows (95 %, labelled)

- The full operating map per cell and in S: every opponent × delay, close-following, flow, robust braking, ALKS past-limit events, `b45_step` and `b3_step` (no reading), with the 95 % and 1 − 0.05/m intervals and the V462(1) tile.
- The V459 bar against no control per cell, at 1 − 0.05/m for the delay half and 95 % for the harm half, beside and never alone.
- **Adaptation gain** (CLAUDE.md asks for it to be pre-registered): AG = e(v3w vs 3E-T) / e(3E-C vs 3E-T) on close-following, and with 3E-D on delay. 3E-T is the rule with v3w's information (both tuned only under condition T). Percentile CI from the same index matrix. AG is read only if the denominator's 95 % lower bound is at least half its point estimate; otherwise the two effects are reported side by side with no ratio.
- Per-learner counts; round 2's T2 with its counting filter, for comparison; each tuned opponent against p333 and on its own tuning seeds (the overfitting check); the T2 mechanism G (§7.3); MPC-F's held-out MSE.

### 8.8 Nulls of the statistics

| Statistic | Null and its value |
|---|---|
| G1 | V341's placebo must fail it (§7.3) |
| G2 | no informative null; a CLAUDE.md check, not evidence that the cell binds (§7.3) |
| W, one comparison | label-swap null at m = 3, n ≥ 40: false "better" 0.8-1.0 % against a nominal 0.83 % (read_power power_tables.md) |
| W, closest delay opponent | 4,000 studies of the label-swap null (`review_stats/lfc.log`): n = 120 gives 0.70-0.93 %, every Clopper-Pearson interval including 0.83 %; with B = 20,000 (2,000 studies), 0.80 % in X1 and 1.10 % in X2; n = 40 up to 1.35 % |
| W on the S6 rows | before any sentence is printed, W's binding comparisons get the same label-swap null check as R (2,000 swaps, B = 20,000, at most 1.5 × nominal). If it fails, "statistic failed its null", no claim sentence |
| L under a tie | v3w shifted once to tie the closest rule on delay (still ahead of the others): L fires in 0.3 % (X1-like) and 0.1 % (X2-like) of studies at n = 120, 0.9 % and 0.5 % at n = 80; with v3w 0.5 % worse than the best rule, 1.4 % and 2.0 % (`review_stats/power.log`). v0's per-opponent tie (every opponent tied at once: 5-14 %) is kept only as a labelled worst case |
| R | its own label-swap null per opponent, computed before R is printed (§8.5) |

### 8.9 Power (planning, per cell, m = 3; 14 stored opponents, none tuned for delay; X1/X2 rows at 5,300, n above 40 resampled from 40 seeds)

These are lower-information proxies. m = 2 would raise them slightly; it was not simulated.

**Arm-level W, every §8.3 condition except the mean-based side constraints and drain** (synth/rule_v0.json, 300 studies per row, noise about ±3-5 points; the statistics review's re-check, 1,000 studies, agrees within noise: X1-like 99/94/40 %, X2-like 57/26/1.8 % at n = 120; `review_stats/power.log`, `power_n240.log`):

| Effects (proxy) | n = 80 | n = 120 | n = 240 |
|---|---|---|---|
| X1-like × 1 | 92 % | 99 % | not computed (about 100 %, my implementation without flow) |
| X1-like × 0.75 | 80 % | 95 % | not computed |
| X1-like × 0.5 | 10 % | 42 % | not computed |
| X2-like × 1 | 35 % | 58 % | 91 % |
| X2-like × 0.75 | 9 % | 25 % | not computed |
| X2-like × 0.5 | 0 % | 2 % | not computed |

A smoothed bootstrap gives 77 % instead of 57 % for X2-like × 1 at n = 120, so the resampling model moves that figure by about 20 points.

**A stronger delay opponent** (one opponent k delay points better than the stored closest rule; `review_stats/power_shift.log`, 600 studies; `power_n240.log`, 400 studies):

| k | X1-like, n = 120 | X2-like, n = 120 | n = 240 |
|---|---|---|---|
| 0.5 | not computed | 46 % | not computed |
| 1 | 98 % | 17 % | X2-like 70 % |
| 1.5 | not computed | 4 % | not computed |
| 2 | 83 % | not computed | not computed |
| 3 | 32 % | not computed | X1-like 46 % |
| 4 | 1 % | not computed | X1-like 4 % |

Minimum detectable effect: about 80 % power needs v3w roughly 3 delay points ahead of the strongest opponent at n = 120.

**Per-policy W and side constraints** (`revise_v1/pp_power.json`, my proxy, 200 studies per row, B = 1,000, without flow, drain and side constraints in the W columns):

| Cell, effects | Per-policy W, n = 120 | Per-policy W, n = 240 | Full-emergency ≤ 0.10, n = 120 / 240 | Collisions ≤ 0.02, n = 120 / 240 |
|---|---|---|---|---|
| X1-like × 1 | 54.5 % | 97 % | 58 % / 91 % | 100 % / 100 % |
| X1-like × 0.75 | 0.5 % | 8.5 % | (stored values, not scaled) | |
| X2-like × 1 | 1.5 % | 2 % | 98 % / 100 % | 99 % / 100 % |
| X2-like × 0.75 | 0 % | 0 % | | |

- If the full-emergency constraint and W were independent, W with it would be about 57 % in X1-like cells at n = 120 and about 91 % at n = 240 (my rough product, not simulated).
- Delay binds among the measure conditions; close-following almost never does (read_power results.md §2).
- Study level, with the veto and a realistic tie: one X1-like W cell and one tied cell give PASS in about 0.99 × 0.997 ≈ 99 % (two tied cells: about 98 %), before the side constraints.
- The true power is lower: up to 28 opponents, searches run to 100 generations, a delay-tuned opponent, and new kinds that may look like neither X1 nor X2. A null is likely in X2-like cells; it is reported as a null.
- If only SURGE survives S2, the study is that one cell at m = 2 (m is never lowered): its per-cell power is the study's power.

## 9. Stages, run counts, time and cost

Rates: rental A (V475, EPYC 7702, 59 workers) **2,600-3,050 runs/h** measured; file times of the X1/X2 rows gave about 2,450 (read_power/results.md:72); 5-minute windows in V475's performance log ranged 2,313-3,052 (plant review). $0.10-0.13 per 1,000 runs (V475), about 6 % setup on top. A 100-worker rental is assumed to cost the same per run (not measured). V470 measured about 154 s per run per worker on another machine against about 75 s implied by V475, and SURGE at 6,000 veh/h or long queues may slow runs, so times may differ. Laptop 1,330 runs/h by day (V425-V426); at most 40 % CPU from 23:00 to 09:00 (V432). Counts: `revise_v1/count_v1.py`, every cell passing every stage.

| Stage | Content | Runs, two cells | Runs, three cells | Where |
|---|---|---|---|---|
| S0 | decisions, build, unit tests, reviews | 0 | 0 | laptop |
| S1 | smoke, identity (C1, C1b), T3 | 130 | 134 | rented (V483) |
| S2 | plant gates, one rung | 460 | 580 | rented, same machine as S1 (V483) |
| S3a | grid re-pick: 69 rules × 20 seeds × (cells + S), plus no control | 4,200 | 5,600 | rented |
| S4a | 3E-C and 3E-D per cell to 100 generations: 384 runs per generation + 240 per check, 9 checks | 162,400 | 243,600 | rented |
| S4b | ASCH: configurations × conditions × 20 seeds, top-5 check, p333 references, never switch | 3,720 | 6,400 | rented |
| S4c | MPC-F: 4 schedules × 40 seeds per condition, fixed actions on the fitting seeds, validity gate | 1,620 | 2,440 | rented |
| S5 | smoke, pick replays on the S6 machine | about 300 | about 300 | rented |
| S6 | evaluation at n = 240: 240 × (cells × 34 arms + S with 24 + 10 × cells arms) | 26,880 | 37,440 | rented, one platform |

| Design | Total runs | Rented time at ≤ 100 workers (with 6 % setup) | Cost (with 6 % setup) |
|---|---|---|---|
| two cells, n = 240 (recommended) | about 199,700 | 69-81 h | $21-27 |
| two cells, n = 120 | about 186,300 | 65-76 h | $20-26 |
| three cells, n = 240 | about 296,500 | 103-121 h | $31-41 |
| three cells, n = 120 | about 277,800 | 96-113 h | $29-38 |

- Searches are 81-88 % of all runs. One futile cell's two searches cost about 81,200 runs, $8-11.
- KILL at S2: about 600 runs (two cells), rented, under $1 (V483).
- **Budget ceiling, action fixed now:** if spend so far plus the projected cost of S5 and S6 at the measured rate reaches $40, or machine time reaches 7 days, every running search stops at its next check, its incumbent is frozen and labelled "stopped at the budget ceiling", which is logged as a departure from V478's "to convergence" (§3.3), and the protocol continues to S5 and S6. The author is not asked to choose after seeing data. With three cells at n = 240, the ceiling may bind at the slow end of the rate range.
- Not costed: build and author time (my estimate: 2-3 days of code and tests, MPC-F included), re-runs under the bug rule.
- **Operating rules:** check machine resources and that the v6 sessions are idle before every batch; the CPU guard; the night cap; no co-scheduling with training (V392); long runs in their own systemd unit; at most 100 workers unless the author lifts it (decision 7); a rate check in the first 30 minutes of every rented stage, against the range above; **S3a and S4 run from a frozen detached worktree at the run commit**; the picks are then committed on the branch, and S5-S6 run from a new detached worktree at that commit, whose diff from the run commit holds only the picks file (checked); no commits in a run worktree mid-run; one platform per stage with acceptance passed (V436, V465); rentals picked by the V473 rules, fetch-verify-destroy on any failure (V471).

## 10. What is reported in every outcome; ledger

| Outcome | What follows | Sentence |
|---|---|---|
| KILL at S2 | gate tables per cell, placebo, cost | "As specified, the perturbations did not congest this plant enough to test v3w against tuned controllers. No DRL claim." Null |
| Cell dropped at S2 | its gate values in the map | "did not bind" |
| NULL at S6 | the full map, every cell × measure × opponent, R, no control, braking, location, plateau labels | §1's null sentence |
| W vetoed by an L | the same map | §1's veto sentence |
| PASS | the same map and the filled sentence with every clause | §1's pass sentence |

- Any cell that is not W or W-b closes the DRL claim against tuned controllers in that cell on this plant: no further training, tuning, plant change or seed round there (as [A3]).
- Any cell proposed after these results is a new study, labelled post hoc, never merged into this one's count.
- Every report also gives: each opponent's provenance (search loss trace, checks, incumbent, plateau label; grid picks; ASCH configuration; MPC-F's gate result, held-out MSE or omission); S2 gate values for every cell, including dropped ones; the planning null and power (§8.8-§8.9) labelled as proxies.
- Disclosures beside every sentence: the closures and that Plan B ran nothing in X1/X2; the cells chosen after DRL results on related perturbations were known (H1, V410, X1/X2; V456(3), V245); SURGE's shape chosen after V410; the intended-use label; v3w's checkpoint selection on X1/X2 validation; the reward overlap of close-following and 3 m/s² braking; informed per-cell opponents and the look-ahead difference; 3E-T and 3E-X carried as lower bounds; the arm-level rule and learner condition set after round 2, and V459 amended for Plan B; the braking and side-constraint tolerances chosen after the stored rows were seen; the priors in §4.4; `collisions` counts minGap intrusions; teleports disabled; no retraining; the worker limit as decided.
- **Ledger:** every run of every stage in the ledger, including smoke, gates, failed, crashed and abandoned ones. Rows under `/home/catalin/work/phd/v5b1_runs/planb/`; summaries in `docs/research/results/planb_*.md`; a V# at each stage gate, committed the same turn.

## 11. Deviations policy

- Before S1: changes go into the protocol by a V#, and the design review sees them.
- After S1 starts: no change to the cells, opponents, measures, margins, tolerances, n, m or the reading. An unavoidable change is a V# with its reason before the affected stage runs. If it touches the reading after any S3a row exists, S6 needs a new seed range and a new V#.
- Bug rule (CLAUDE.md): fix, re-run everything affected on the same seeds, log and report both outcomes. A bug re-run is not a new round. **After S6 rows exist,** a corrected verdict counts only if a test written before the fix fails on the old code; both verdicts go in every sentence; every post-S6 bug search is logged with what triggered it.
- A crashed run is re-run on the same seed and commit (§8.3). A search that crashes resumes deterministically from its stored runs (as V443).
- A platform change mid-stage voids that stage's rows, or the split is disclosed as in V465.
- A broken null (the placebo passes G1), an identity failure or a determinism failure stops the stage until fixed and logged.
- An opponent that cannot be built, or fails its smoke check, is a disclosed omission. m does not change.
- A search labelled "not converged at 100 generations" or stopped at the budget ceiling is a departure from V478's binding "to convergence": it is logged in a V# beside the result and named in every sentence.

## 12. Risks and limits

| Risk | Effect | Handling |
|---|---|---|
| New cells look like X2, or opponents get stronger | planning power 2-58 % at X2-like effects (n = 120), lower with a stronger delay opponent | n = 240 (decision 11); a null is a valid outcome, reported as one |
| TRUCK may fail G1 (H1 proxy: no control +6.3 %, p333 +4.4 % [−1.0, +8.9]; TRUCK is denser and slower, so the outcome is uncertain) | Plan B tests SURGE alone at m = 2 | stated now; decision 2's second-rung alternative; m not lowered |
| SURGE's queue still present at 1,500-1,800 s | it fails G4(ii)(a) and drops | the criterion allows S's backlog; stated now |
| Full-emergency constraint decides X1-like cells at n = 120 | W fails on a side constraint, not on the measures | n = 240; decision 9's tolerance |
| False L from many opponents at 95 % | rare under a realistic tie (0.1-0.3 % per tied cell at n = 120) | stated now |
| Outside intended use; merge-conflict and lane-change dynamics excluded by the V&V record | weakens the contribution | the label and the PR-08, PR-28 clause in TRUCK's sentences; decision 4 |
| Priors favour v3w (§4.4); cells chosen after related DRL results | selection risk in the cell choice | disclosed in every sentence; the choice is the author's (decision 2); no v3w row existed when the cells were approved; one S0 crash-check row, not read for performance (V482) |
| Searches still improving at 100 generations | opponents are lower bounds | labelled; a departure from V478 logged |
| ASCH read as a relabelled rule; MPC-F fails its gate | weaker opponent wording | §1's bounded wording names it |
| Reward overlap | a win on a trained-on measure | disclosed in every sentence |
| SURGE pairs with S only by seed after 600 s | R and G1 are seed-paired there | stated (§4.3) |
| The median statistic is lumpy | interval bounds jump between clusters | B and the rng fixed; disclosed |
| Run time per run unknown on the new cells (V470's 154 s against V475's about 75 s) | time and cost may differ | a rate check in the first 30 minutes of every rented stage; the ceiling |
| (WORKZONE, if kept) limit braking at the edge-2 boundary (MSCFModel.cpp:112-115), about 300 events per run against about 4,300 robust events in X1 (my estimate, not traced) | a braking cost partly made by SUMO | the location keys, a C3 trace on 2 seeds, the pre-registered exclusion (§4.2) |

**Limits every Plan B sentence carries:** a synthetic plant, not calibrated (V245); ideal V2V (PR-16); lane changing not validated (PR-08); ramp-2 lane-end behaviour not validated (PR-28); merge-conflict dynamics outside the V&V record; one demand level; five learners from one recipe; per-cell rules know the condition; simulation only.
