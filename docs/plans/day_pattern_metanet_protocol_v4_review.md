# METANET protocol v4: design review record (2026-10-06)

Round 1: adversarial review (4 lenses; every blocking/major finding verified by a skeptic; workflow wf_b2576e5b-c87): 53 findings, 52 kept, deduplicated into 21 fixes (R1-1 … R1-21).
Round 2: fixes applied, then 4 independent data-free re-derivations (cell table, stability scan, A3 starts, completeness/P11; workflow wf_8f6e256a-210): all numbers reproduced; corrections R2-1 … R2-25.

**Round-1 verdict.** v4 should not be committed as drafted: there are 2 blocking and 11 major defects, listed below (21 fixes).

The 2 blockers:
- **No queue-backing gate.** A3 leaves the v3 'event without queue' false-PASS route open at B1.
- **Unit test 2 cannot be run.** It has no definition or tolerance and no consequence on failure, so T would be decided after seeing a failure.

**I recommend a narrow further check before the commit, not a full review round.** Four fixes add new binding rules, and these need one targeted verification pass that reproduces their stated numbers on synthetic inputs:
- the P11-k gated row and its unit test 21;
- the test-2 scan, including its ε value and the extra time-step condition (e) (the disclosed 0.75 / 1.0 / 1.25 s values should be reproduced);
- the A3 enforcement change, a graded penalty plus rejection-sampled starts (every base and F1 seed should reach A3 feasibility at evaluation 1);
- the full 39-row cell table, role concordance and correction list, checked against the prototype builder.

The other fixes are text, disclosure or path changes. They need no further review once the author settles the decision items:
- V6: reopening the METANET route as a disclosed deviation;
- V7: the single-look rule and what happens at the freeze if F̂ is not estimable;
- V8: adopting P11-k;
- whether to pre-register an E15 mitigation;
- F16 becoming report-only.

**What I re-ran myself.** I re-ran the reviewer's data-free replay of v3's restart initialisation with the v4 base seeds (scratchpad/v403/seeds_exact.py; restart() and cma_options taken from the repo). Seed 7,191,010 never reaches an A3-feasible point in 4,000 evaluations, and seed 7,191,012 needs 717. This assumes v4 reuses v3's initialisation unchanged.

**How certain these findings are.**
- The B1 false-PASS risk rests on synthetic toys, not on a fitted v4. That v_c,G2 will land on the A3 bound is an inference.
- The N4 stability-edge formula, the seed concordance and the (d)/(f) values were not independently re-verified. Check them before commit.

## R1-1 [blocking; author] §A3 'Why' and the lesson table (line 22); new §A12; v3 §4.8, §5.3, §5.5, §9.2; §A7; §A10

**Defect.** A3 only blocks the equilibrium route. If v_c,G2 sits on its bound, which is likely because v3 wanted 46.5–48.1 km/h against 67.7, S of Highwood Ave reads only 0.32 km/h above its own threshold. Other routes stay open: a queue headed at the 4→3 drop (cells 23–24), anticipation across 21→22, or δ_m in merge-fed station cells. Each can produce P_1 episodes with no cell between the pair's stations above ρ_cr, which is the v3 artefact class (142 of 147 bins unbacked), and no gated row checks for it. In data-free toys, 12 of 90 settings gave S1773 at 34–40 mph with cells 26–31 below critical. So a false B1 PASS stays open.

**Change.** (a) §A3 'Why', append: "A3 removes only the equilibrium route. With v_c,g on its bound, the capacity state reads within 0.32 km/h of S of Highwood Ave's threshold and exactly at I-494's. A queue headed upstream of a pair's upstream station (e.g. the 4→3 drop, cells 23–24), the anticipation term across a per-lane density increase (cell 21→22, S1771) and δ_m in merge-fed station cells (1, 4, 14) can still give sub-threshold station speeds with every cell ≤ ρ_cr,i. A3 is complemented by gated row P11-k (§A12)." In the lesson table, change 'must exceed' to 'must be ≥'.
(b) New §A12, 'P11-k queue backing (new gated deterministic row, added to v3 §5.3)':
- Qualifying bin: a 5-min bin inside a model P_k episode in which the pair condition holds on detector scale.
- Backed bin: a qualifying bin in which at least one cell strictly between the pair's station cells has bin-mean ρ_i > ρ_cr,i (B1: cells 26–31; B2: cells 33–34; station cells never count; ρ_cr,i includes θ1, c_k and the F1 state).
- Unbacked episode-day: a model P_k episode-day with < 50 % of its qualifying bins backed.
- PASS iff unbacked episode-days ≤ max(2, ⌈0.10·n⌉) at c1 = c2 = 1 [lab convention; P8 tolerance; fit-informed, disclosed under D4.4].
- Evaluated on usable calibration days at the freeze (a failure there is a route stop before any validation run) and on all usable validation days in the gate. Applies to the nominal plant, every ensemble member and F1. Not in the F1 trigger set.
- Reported: the pooled backed share per k; each unbacked day with its most downstream congested cell; under stochastic draws, the per-day share of draws with an unbacked episode (report-only).
(c) §4.8 and §5.5, report-only:
- per event station, the share of bins with event-scale model speed < 40 mph while every cell from its cell to the next downstream event station's cell is ≤ ρ_cr,i;
- v3 §2.3 mainstream-origin misfit minutes split by ρ_1 ≤ / > ρ_cr,1;
- per group, v_c,g − thr_g, flagged 'A3-active' if within 1 %.
(d) §A7: 'Every P-row … plus P11-k (new, §A12)'. §9.2: add the 50 % share, the strictly-between cell sets and the P8 tolerance for P11.
(e) §A10 test 21 (synthetic). Expected results: (i) G2 at the A3 bound, demand above 3-lane capacity at the 4→3 drop → unbacked; (ii) H1 queue spilling back to cell 25 → backed; (iii) only cell 25 above ρ_cr → unbacked; (iv) a 3→2 lane-drop toy at ν = 90, κ = 5 → non-zero station diagnostic at the last 3-lane cell.
Add §0.6 V8: 'P11-k gated row and its conventions | confirm'.

## R1-2 [blocking] §A10 test 2; §A2 T rule, 'New build assertions'; §A11; §9.2

**Defect.** Test 2 has no criterion that can be run: 'physically stable uniform state', the 'bound grid' and a tolerance are all undefined. Explicit Euler amplifies near-neutral modes at every T > 0 (about 1e-5 s⁻¹ at 0.75 s), so read literally the test fails at every rung. The alternative is a definition and tolerance chosen after a failure, which then decides T. The text gives no consequence for a failure. 'Replaced by' also drops v3's worst-case shock check.

**Change.** Replace the test 2 row with:
"(i) v3's worst-case shock check is kept (no negative speed, ρ ≤ ρ_max). (ii) A2 assertions (a)–(d) at the bound corners. (iii) A frozen-coefficient von Neumann scan of the simulate() cell update, linearised about uniform states (constant λ; no ramps, δ_m, φ or boundaries):
A(θ) = [[−(v0/L)(1−e^{−iθ}), −(ρ0/L)(1−e^{−iθ})], [V′/τ − ν(e^{iθ}−1)/(τL(ρ0+κ)), −1/τ − (v0/L)(1−e^{−iθ})]]; the Euler eigenvalues are 1 + Tλ_k(θ).
- States: equilibria with ρ0/ρ_cr ∈ {0.1, 0.3, 0.6, 1, 1.25, 1.5, 2, 3, 5, 8, 12}, ρ0 ≤ ρ_max, V ≥ v_min; floor states (v0 = v_min, both with V′ = 0 and with V′ kept) where V < v_min; cap states v0 = 1.05·v_f at ρ0/ρ_cr ∈ {0.1, 0.3}.
- Grid: τ ∈ {10, 15, 30, 60} s; ν ∈ {5, 30, 60, 90} km²/h; κ ∈ {5, 20, 40, 60}; v_f ∈ {80, 120, 150}; ρ_cr ∈ {15, 30, 45}; a ∈ {1, 2, 3.5}; every distinct L_i; θ_j = jπ/181.
- A state is stable iff max Re λ ≤ 0 (semi-discrete; the continuum sub-characteristic condition is not used).
- GATE: in every stable state, max ln|1+Tλ|/T ≤ ε = 1e-4 s⁻¹ [lab convention].
- Report-only: the excess growth in unstable states (truncation error, tested by step-halving) and the count of continuum-stable but semi-discretely unstable states."
§A2: add '(e) the test-2 gate (iii) passes at T', and 'If no rung satisfies (a)–(e), the build fails before any calibration and the author decides between an amendment and a route stop.'
§A11 and §9.2: 'ε and the grid were fixed after data-free review scans. Worst stable-state growth: 1.1e-5 s⁻¹ at 0.75 s; 2.0e-5 at 1.0 s; 4.95e-3 at 1.25 s (floor state τ = 10, ν = 90, κ = 5, ρ = ρ_max, L = 300 m). Unchanged with 721 θ. T stays 0.75 s.'

## R1-3 [major; author] §A6 'Single look'; v3 §6.3 (last sentence); §A9 STOP guard; §A11 item 5; §0.6

**Defect.** The rule contradicts itself. It calls v4 the 'only METANET look', yet later plants judged on the same 97 days are merely labelled 'second look', and in v3 that label leaves a PASS GO-capable (v3 §6.3 also allows a new version). Several cases are open: a stop decided after seeing c2*, the F̂ verdict or §4.8 at the freeze; a 'PASS, deterministic-only' result; whether a pre-validation N0 stop uses up the look. A KILL-only outcome is foreseeable at the freeze (F̂ not estimable), and no pre-registered choice covers it. 'Plant selected after 2 attempts' is hard-coded.

**Change.** Replace the 'Single look' bullet with:
"(1) No model of any kind (smoke and debug runs included) runs on a validation day until metanet_v4_calibration.json is committed with stage 'freeze'. v4 smoke tests use synthetic inputs or calibration days.
(2) Once the first v4 CMA-ES evaluation has run, v4 ends only by an N0 route stop (§2.5), by the pre-registered freeze choice in (7), or by a §0.3 gate outcome (§8.6 steps 5–6; F1 if triggered). A §6.3 bug fix and its re-run is not a stop. Any other stop is recorded as 'abandoned after calibration'.
(3) After a v4 FAIL (with F1 if triggered), 'abandoned after calibration' or 'PASS, deterministic-only', any later plant judged on these 97 days (a new METANET version under §6.3, or SUMO) is labelled 'second look on the same validation days', and its gate can yield only a KILL. A GO-capable later plant needs validation days on which no model has run and which no design step has inspected, chosen by a rule committed before they are pulled. After an N0 route stop or the freeze stop in (7)(b), the days stay unlooked and the attempt is counted under A11.5.
(4) An F1 PASS keeps its v3 §6.1 status and label.
(5) An A4 imagery amendment may replace v4 only before the first v4 CMA-ES evaluation; after that, it is a later plant under (3).
(6) Until the v4 gate outcome is committed, only committed gate code reads validation-day real data.
(7) If F̂ is not estimable by rule (i) or (iv) at the freeze, then [author picks now: (a) run the gate anyway (deterministic-only, KILL-only; uses the look), or (b) stop at the freeze as a pre-registered end]."
This amends v3 §6.3's last sentence.
§A9: 'The v4 gate jobs (prep included) refuse to run unless metanet_v4_calibration.json is tracked by git, unchanged against HEAD, names protocol v4, has stage freeze and a route not starting with STOP. They never read the v3 record.'
A11.5: 'plant selected after N attempts (listed), where N counts every committed METANET or SUMO plant protocol for this corridor that reached calibration, stopped or abandoned ones included (N = 2 at v4)'.
Add §0.6 V7: 'Single-look rule, §6.3 amendment, freeze choice (7) | decide'.

## R1-4 [major] §A3 'Enforcement'; §A7 optimiser bullet; v3 §4.4–4.5; §A10 test 19

**Defect.** The flat J = 10 penalty sits over a constraint that admits only 13 % of the initial-mean box. I replayed v3's restart() initialisation with the v4 base seeds; this is data-free, because every J ties at 10 until the first feasible point. All 8 initial means violate A3. Seed 7,191,010 never evaluates an A3-feasible point in 4,000 evaluations, so its best J is 10 whatever the data. Seed 7,191,012 needs 717 evaluations. The v_f,G3 profile points at 80 and 88.75 km/h have no feasible completion (G4 needs v_f,G3 ≥ 97.05), which caps the flat share and overstates identifiability. The scope (continuation, F1, profiles) is only implicit. A3-activity is not reported. Violators are simulated before they are penalised.

**Change.** Replace 'Enforcement' with:
"(a) A3 is checked before simulation, on the bounded vector that would be simulated; a violator is not simulated.
(b) A violator gets J = 10 + Σ_g max(0, thr_g − v_c,g)/thr_g. This is above every admissible J and above the J = 10 for clipping or non-finite values. It counts as one evaluation and is counted per restart as 'inadmissible (A3)', separately from clipping.
(c) (a)–(b) apply identically in base, continuation, F1 and profile runs.
(d) Initial mean (amends v3 §4.4, base and F1): with rng = default_rng(seed), redraw x ~ U[0.25, 0.75]^n until A3 holds (at most 10,000 draws, else the job fails); pycma keeps the same seed. Disclosed: under v3's rule, seed 7,191,010 never reached an A3-feasible point (data-free replay).
(e) A restart with best J ≥ 10 is reported as 'no admissible point'. It is not re-run or replaced, and it counts in every restart statistic.
(f) Profiles: points with no A3-feasible completion (v_f,G3 = 80 and 88.75 km/h) are not run and are recorded as 'infeasible (A3)'. The warm start is the frozen optimum with each violating a_g raised to its smallest A3-feasible value. The flat share is reported over all 8 intervals and over the A3-feasible intervals; the non-identifiable flag uses the latter.
(g) Implied limits (disclosed, not new bounds): v_f,G1 ≥ 100.2, v_f,G2 ≥ 90.1, v_f,G3 ≥ 97.05 km/h; a_G1 ≥ 1.45, a_G2 ≥ 1.26, a_G3 ≥ 1.18, a_G4 ≥ 1.39.
(h) Reported per restart and at the optimum: v_c,g − thr_g; an 'A3-active' flag if within 1 %; the A3-violating share; the index of the first A3-feasible evaluation."
§A7: 'The optimiser settings … except §A3 (a)–(f).'
Test 19 checks:
- a violator is not simulated;
- the graded J increases with the violation;
- the rejection draw is deterministic and A3-feasible for every base and F1 seed;
- infeasible profile points are skipped;
- the admissible case is an explicit A3-feasible set, not midpoint_params (which violates G1 at 73.7 km/h).
Update the V3 text to match.

## R1-5 [major; author] Lesson table line 23; new §A11 item 8; §0.6 V1, V5; §4.8/§5.5

**Defect.** v3's relocation (a) at the E15 merge cell (6 of 22 days at c = 1; at least 7 days at c1 0.80–0.82, c2 0.80) is untouched. E15 still merges with the shared δ_m, now in a shorter cell. A single occurrence at c2 ≤ 1.00 on any usable calibration day makes F̂ not estimable by rule (iv), so the best outcome is 'PASS, deterministic-only', which is KILL-only. The lesson table claims A4 addresses this. The author is asked to confirm V1 and V5 without this failure map.

**Change.** (1) Lesson-table row: 'relocation at the E15 merge (v3: branch (a) at cell 33 on 6/22 days at c = 1; ≥ 7 days at c1 0.80–0.82, c2 0.80); lane count unknown → A4: §1.7 step (b). The E15 relocation is NOT addressed; see A11 item 8.'
(2) New A11 item 8, 'Known failure paths (consequences unchanged from v3)':
- (a) E15 relocation → c2* < 1.00 → rule (iv) → neither F̂ nor F̂_T → at best deterministic-only, KILL-only. Days that relocate at every pair also count toward rule (i). An E15 queue reaching cell 35 shows as a model P_2 episode: on real-B2-inactive days it is a P8(iii) extra; on real-B2 days it is agreement at the wrong head.
- (b) B2 knife edge (v3 grid at c1 = 1: B2 active on 22/22 days at c2 = 0.90, 2/22 at 1.00). P3-2 or P8(iii) failing alone → route stop. P4-2 or P5a-2 failing → F1 is fitted, then a FAIL is expected.
- (c) B1 after A3: P3-1 and P4-1 fail together → F1 → expected FAIL.
- (d) Step-halving tie (see the diagnostics item).
(3) Append to V1 and V5: 'confirmed knowing A11 item 8'.
(4) §4.8 and §5.5, report-only: for each model P_2 episode, the most upstream over-critical cell; flag episodes whose only over-critical cells are 35–39.
(5) Author decides before commit, never after the fit, whether to pre-register a data-free mitigation (e.g. 'under step (b), E15 is lane-adding, δ_m = 0 at E15', disclosed under D4.4 with the alternatives considered) or none. No per-ramp δ_m.

## R1-6 [major; author] Header 'What v4 is'; 'Decisions behind v4'; §A11 items 1, 5; §0.6

**Defect.** A11.1 misquotes D4.1: the phrase 'amendment to pass v3' appears nowhere. D4.1's options were '(a) accept the stop as pre-registered; (b) a post hoc v4 amendment', and v4 is in form option (b). 'Framing decided by the author (D4.2–D4.8)' overstates the record: the 'not a rescue' wording comes from the design-study judge. Reopening the METANET route deviates from v3 §0.3/§6.2, which stopped the route and named only SUMO as a continuation, and v4 does not disclose this. D4.2 is missing from the decision list.

**Change.** (1) Replace A11 item 1 with: 'History. v3 failed N0. Its pre-registered consequence (v3 §0.3, §6.2) was a route stop that "stops the METANET route"; §0.3 named only SUMO as a continuation. D4.1 offered (a) "accept the stop as pre-registered" or (b) "a post hoc v4 amendment"; the author chose (a). In form v4 is a post hoc amendment of v3 that reopens the METANET route. This is a deviation from v3 §0.3 decided by the author after the v3 results (D4.2, conditional on the prize screen; D4.8, unconditional), made after the post-stop diagnostics diagnosed a numerical defect. v4 differs from option (b) in these ways: v3's FAIL and route stop stand as attempt 1; under the D4.4 addendum no v3 result is re-labelled, re-run to pass or replaced; v4 refits from cold starts on new seeds; its single validation look is governed by §A6.'
(2) Header: replace 'It is not a rescue of v3: …' with 'In form it is a post hoc amendment of v3 that reopens the METANET route stopped by v3 §0.3, a disclosed deviation (A11.1). Under the D4.4 addendum, no v3 result is re-labelled, re-run to pass, or replaced.'
(3) Decision list: add 'D4.2: METANET v4 as the gate plant, originally conditional on the prize screen'; change D4.8 to 'skip the prize screen; METANET v4 unconditionally next'.
(4) A11.5 label: '… (METANET v3 stopped; v4 reopened the route as a disclosed deviation from v3 §0.3)'.
(5) Add §0.6 V6: 'v4 reopens the METANET route stopped by v3 §0.3/§6.2, on the same 97 validation days, as a disclosed deviation decided by the author after the v3 results | confirm'. Record V6 in the decision log in the D3.1/D3.5 style.

## R1-7 [major] §A1 'Disclosed consequence (D4.4)'; §A7; §A11 item 2; §0.6 V2

**Defect.** The B-set rule (station cells unscaled) mechanically eases v3 failure paths. It removes relocation (b), which fired on 869 of 902 points at c2 = 0.80. So c2* can only rise, rule (iv) becomes less likely, and non-empty consistent sets become likelier. v4 says only that it 'changes how c2* and F̂ behave'. F1's cells shrink from 26–32 to 28–31 ∪ 33–34 without disclosure. A7 lists these rules as 'unchanged', and the rejected alternative (head-only) is never named.

**Change.** (1) In A1 'Disclosed consequence', replace bullets 2–3 with:
- 'Candidates (2026-10-06 design study, neither simulated): (a) head-only, B1 = {28}, B2 = {33}; (b) v3 §1.4's sets on v4 cells (B1 = 27–32, B2 = 33–35) minus the station cells, giving B1 = 28–31 and B2 = 33–34. The A1 rule reproduces (b), selected from 2. Data-free reason: (b) departs least from v3, removing only station cells, while (a) makes c_k inert above saturation and truncates F̂'s upper tail.'
- 'Direction (expected, not tested): B-set membership acts only where c_k ≠ 1 and under F1. Removing relocation (b) at low c2 means c2* can only rise, rule (iv) becomes less likely, and rules (i)/(iii) become less likely to fire. Each eases a v3 failure path toward an estimable F̂ and a stochastic PASS. Relocation (a) at E15 is not eased.'
- 'F1's cells change from v3's 26–32 to 28–31 ∪ 33–34.'
- 'Designed after seeing v3's capacity grid.'
(2) A7: 'F̂ rules (i)–(iv) …: text unchanged; their effective behaviour changes through A1's B-sets'; 'F1 (Δ, η, trigger unchanged; cells = B1 ∪ B2, changed from 26–32 to 28–31 ∪ 33–34)'.
(3) A11.2: append 'The A1 B-set rule eases relocation (b), rule (iv) and F̂ estimability, and shrinks F1's domain; every F̂-based result names this.'
(4) V2: add 'rejected alternative: head-only (28; 33); selected from 2'.
(5) Optional, report-only and never replacing the primary: after the primary §4.7 result is committed, re-run the §4.7 grid on calibration days at the frozen parameters with v3's sets on v4 cells (B1 = 27–32 with θ1 on 28, B2 = 33–35, relocation (a) on 36–39). Report c2*, the F̂ verdict and the rules triggered. Add the cost to V1.

## R1-8 [major] §A1 header and 'Station readings'; §A10 test 9; §A11

**Defect.** The header replaces the '§1.5 first bullet' and the body says 'first two bullets', but only bullet 2 (station reading) is restated. That deletes v3's ramp-placement rule (an entrance on a boundary feeds the downstream cell; an exit on a boundary leaves the upstream cell), which now assigns almost every ramp because gores are break points. The correction list is also wrong. Under that rule, which is the one the code uses, the same-cell correction applies at S461 (cell 17, +X8), S1770 (cell 19, +X9) and S1771 (cell 21, +X10), all flow-scored in J. The text lists only cell 1, and its 'inside' wording excludes these. The surviving v3 '−E13 at Anderson Lakes' no longer applies.

**Change.** (1) Header: replace 'and the §1.5 first bullet' with 'and the second bullet of §1.5; §1.5's first bullet (ramp placement) applies unchanged and is binding; its third bullet applies with 400 steps in place of 60'.
(2) Body heading: 'Station readings (§1.5 second bullet replaced; first bullet restated; third bullet with 400 steps)'. Add as the first bullet: 'Ramp placement (v3 §1.5 bullet 1, unchanged): an entrance at km x feeds the cell containing x, and one exactly on a boundary feeds the downstream cell; an exit leaves the cell containing x, and one exactly on a boundary leaves the upstream cell. On the step-(b) table: E1→1, E2→4, E3→5, E4→7, E5→10, E6→13, E7→14, E8→15, E9→19, E10/E11/E12→23, E13→28, E14→33, E15→36; X1→1, X2→2, X3→5, X4→8, X5→11, X6+X7→13, X8→17, X9→19, X10→21, X11→26, X12→31, X13→34, X14→38, X15→39.'
(3) Replace the correction parenthetical with: '… applies to every ramp assigned to the station's cell by the placement rule and lying downstream of the station, including an exit on the cell's downstream boundary: S453 (cell 1: −E1, +X1; input only), S461 69th St (cell 17: +X8), S1770 S of Valley View Rd (cell 19: +X9), S1771 I-494 (cell 21: +X10); no other station. Anderson Lakes no longer needs −E13 (E13 feeds cell 28); T.H.101 needs none (X15 is upstream of it).'
(4) Test 9: '… and, per station and variant, its cell and corr_entr/corr_exit lists, checked against §A1.'
(5) A11: disclose the change of correction set against v3.

## R1-9 [major; author] §A1 '§4.7 relocation rule (a)' and '§1.7 F16 domain' sentences; §A4; §A7; §A10; §0.6 V5

**Defect.** 'Unchanged meaning' and 'same stretch' are false. v4 cells 35–39 span km 7.017–9.390, while v3's 33–36 spanned 7.199–9.390. The 182 m between them moves from v3's c2-scaled cell into unscaled cell 35, which holds the OSR station and no ramp. v3's literal F16 domain on v4 cells is {27, 32, 35–39}, and v4 narrows it silently. Cell 35 (A_35 = OSR flow only; R ≈ 1.06–1.08 by reviewer arithmetic, against a 1.10 limit) lies outside G4. So a flag there leaves v3's 'calibration is blocked until a step resolves it' with no applicable step, and the reading would be chosen after the fact. v3's f16() code (range(32, N), one A = OSR + E15 for every cell) would give cell 35 R = 1.371 and would cover B2's cells.

**Change.** (1) Replace the A1 relocation sentence with: 'Relocation (a) in v4: any cell downstream of B2's last scaled cell (cells 35–39) with ρ_i > ρ_cr,i for ≥ 3 consecutive bins. This is a change of domain: v3's cells 33–36 spanned km 7.199–9.390, v4's span 7.017–9.390, and 7.017–7.199 moves from v3's c2-scaled cell 32 into unscaled cell 35 (OSR station, no ramp), so relocation (a) can fire upstream of E15.'
(2) Replace the F16 sentence and §A4's 'Its outcome cannot change the step …' with: 'Replaces v3 §1.7's domain sentence and "Rule" for v4. (i) G4 = cells 36–39 is adopted without condition (lane check inconclusive, D4.5; v3's F16 on the same arriving flow gave R = 1.371, so v3's rule would also select step (b)). (ii) F16 is recomputed cell by cell by v3's A_i definition on cells 27, 32, 35–39 (cell 35: OSR only; cells 36–38: OSR + E15; cell 39: OSR + E15 − X14). The domain comes from the build, never from a fixed index, and v3's f16() loop is not reused. (iii) F16 is report-only in v4: no outcome changes geometry or blocks calibration. A ratio > 1.10 at cell 27, 32 or 35 is listed in F14 as a capacity question, because there it compares a station's own peak with discharge and is not a lane test. (iv) This removes v3's blocking clause (disclosed).'
(3) A7: 'Relocation (a)/(b) definitions (domain re-cut per §A1; disclosed change)'.
(4) §A10: 'F16 per-cell sources on synthetic flows: A_35 excludes E15, A_36 includes it, A_39 subtracts X14; cells 33–34 are not in the output.'
(5) V5: add 'F16 report-only on cells 27, 32, 35–39'.

## R1-10 [major] §A1 'Groups'; §A3 table and rule; §A10 test 19

**Defect.** A1 defines G3 = 27–39, which overlaps G4 = 36–39. 'Read in g' is undefined, and the committed F6 c_s table labels S1610 as G3 (its scaling group). Both natural readings of the A3 rule therefore put S1610 in G3. That gives G3 a 72.9 km/h threshold instead of 64.4, and G4 possibly no constraint, which contradicts A3's own table. The G1 row lists S453, which has no c_s. v3 code's G4 rule (mid ≥ 7.199) would put cell 35 into G4.

**Change.** (1) A1 Groups: 'G3 = cells 27–35 and G4 = cells 36–39 as FD groups (the cell's v_f, ρ_cr, a). Under step (b), v_f,G4 ≡ v_f,G3, and ρ_cr,G4 and a_G4 are fitted. G4 runs from the cell fed by E15 to the stretch end. Where v3 says "G3" for the whole 2-lane section (§3.2.4 m_G and T.H.101's c_s, §2.2 g(N), F16), it means G3 ∪ G4 (cells 27–39). The "group" field of F6 is the scaling group, not the FD group.'
(2) A3: 'A station is read in g if the cell it reads (§A1) belongs to FD group g. Only event-layer stations count. c_s comes from F6; F6's group field is not used. The table is binding; if code and table differ, the build fails.' G1 row: 'S455–S462 (S453 is the upstream boundary, has no c_s and is not used)'. G4 row: 'S1610 (T.H.101, cell 39), although F6 labels it G3 for scaling'.
(3) Test 19 and test 9: the per-group station sets and thresholds derived from the cell→FD-group map equal G1 75.3, G2 67.7, G3 64.4, G4 72.9 km/h (to 0.1); group(35) = G3 and group(36) = G4.

## R1-11 [major] 'Form' bullet 1; §A1 (new concordance); v3 §2, §2.1, §2.4, §4.7, §6.1, §1.5, §2.5, §2.6, §4.1, §1.7, §8.2, §1.4 weave; §A1 merge log

**Defect.** 'The amended value applies everywhere' for cell numbers has no v3→v4 mapping. Several v3 numbers had two roles, which are now in different cells: 26 = B1 head and Anderson Lakes (now 28 and 27); 30 = X12 and Pioneer Tr (31, 32); 32 = X13 and OSR (34, 35). §2.1's FD bullets ('B1: 27–30; B2: 31–32', 'ρ_cr,26'), §4.7's Definition and §2.4's example remain in v3 cells. Under §6.3, which allows post-result code fixes 'to §2 equations', an ambiguous §2.1 is a forking path. Derived values are also not restated: 60 steps, N = 36, the §8.2 cost basis, the clipping example, the 'τ lower = 2T' row and the 319-m clause. The merge log is not in rule order (the 23-m piece merges first).

**Change.** (1) Form bullet 1: 'Where an amendment changes T or seeds, the amended value applies everywhere. v3 cell numbers in text v4 does not restate are read by role through the §A1 concordance; where v4 restates a v3 section in v4 cells, the restatement governs.'
(2) Add to A1 a binding concordance (v3 → v4):
- stations: 69th St 15→17; S of Valley View 18→19; I-494 20→21; Highwood Ave 21→22; S of Highwood Ave 23→25; Anderson Lakes / 3→2 lane end 26→27; Pioneer Tr 30→32 (unscaled); OSR 32→35 (unscaled); T.H.101 36→39;
- φ and E10–E12: 22→23; X11: 25→26;
- B1 head (E13, θ1) 26→28; B1 non-head 27–30→29–31; X12 30→31;
- B2 head (E14) 31→33; B2 31–32→33–34; X13 32→34;
- E15 33→36; X14 36→38; X15 36→39; G4 33–36→36–39; relocation (a) 33–36→35–39;
- F1 26–32→{28–31, 33–34}; N 36→39;
- new role with no v3 counterpart: cell 32, an unscaled G3 cell between B1 and B2.
(3) Restate in v4 cells:
- §2.1: 'ρ_cr,i = c1·ρ_cr,G3 in cells 29–31; ρ_cr,28 = c1·θ1·ρ_cr,G3; ρ_cr,i = c2·ρ_cr,G3 in cells 33–34; Δλ_i = 1 in cell 23 only';
- §4.7 Definition: the same cells;
- §2.4: 'X12 in cell 31, X13 in cell 34; X14 in cell 38 sees q_37; X15 in cell 39 sees q_38'.
Mark §3.2.1's physical reading and §4.7 'Why' as informative, with the notes 'lane-end cell 27 is outside B1 and unscaled' and 'c2-driven relocation lands in OSR's cell 35'.
(4) Add to A2, 'Derived values': 400 steps per 5-min bin (§1.5, §2.6); N = 39; 91,200 steps per model-day (§8.2); step-halving at 0.375 s; the §2.5 clipping example becomes ≈ 22.5 km/h; §4.1's τ row reads '10–60 s (prior bound)'; §1.7's 319-m clause is void; the weave sensitivity runs at the frozen v4 parameters.
(5) List the merge log in rule order: 23 m, 31 m, 80 m, 173 m, 249 m.

## R1-12 [major] §A1 Rule 4 and line 64 ('Cells 1–22 are listed in the build manifest'); §A6; §A9 'Before any v4 code change'; v3 §8.6, §3.6 F1

**Defect.** 18 of the 39 cells (12 of 17 stations, all of G1) exist only in a manifest that code has yet to generate, so the F1 'must equal §1' check and test 9 become circular for them. A1 needs build_network('v4') output 'committed with this protocol', while v3 §8.6 puts code after the protocol commit and A9 adds a pre-code guard with no stated order. A full table would have exposed the missing corrections at cells 17, 19 and 21.

**Change.** (1) Replace line 64 with rows 1–22 of the table, in the same columns, and add a 'same-cell correction' column to all 39 rows. Rows (km):
1 −8.413/−8.074 S453 E1, X1 (−E1, +X1); 2 −8.074/−7.670 X2; 3 −7.670/−7.233 S455; 4 −7.233/−6.835 S456 E2; 5 −6.835/−6.221 E3, X3; 6 −6.221/−5.896 S457; 7 −5.896/−5.450 E4; 8 −5.450/−5.003 X4; 9 −5.003/−4.576 S458; 10 −4.576/−4.034 E5; 11 −4.034/−3.492 X5; 12 −3.492/−2.901 S459; 13 −2.901/−2.300 E6, X6+X7; 14 −2.300/−1.866 S460 E7; 15 −1.866/−1.435 E8; 16 −1.435/−1.005 —; 17 −1.005/−0.574 S461 X8 (+X8); 18 −0.574/0.000 S462; 19 0.000/0.466 (λ 3, G2) S1770 E9, X9 (+X9); 20 0.466/0.911 —; 21 0.911/1.355 S1771 X10 (+X10); 22 1.355/1.730 (λ 2) S1772.
Regenerate the rows from the prototype builder and check them before commit.
(2) Rule 4: 'The 39-row table and the merge log above are binding. build_network("v4", step) must reproduce them (test 9), and the build fails if it differs. The draft table came from a data-free prototype on configuration geometry (disclosed). No repository v4 code is required before the protocol commit.'
(3) A6: add the order. 'v3 §8.6 applies with: step 0, before the protocol commit, the A9 sha256 manifest and the tag metanet-v3-stop; step 1, author items V1–V8, then the protocol commit; step 2, code, unit tests and synthetic timing; step 3, the A6 recompute list committed to metanet_v4_precal_facts.json before any CMA-ES evaluation; steps 4–7 unchanged. v3 §3.8 steps 1–10 are not re-run.'

## R1-13 [major] 'Form' clause; §A9 'v4 paths and guards'; §A6 'Recomputed'; v3 §3.6, §8.3; code metanet_facts.py, metanet_calibrate.py

**Defect.** The Form rule's 'v3 read as v4 for the outputs, paths and seeds named in §A9' has nothing to act on: no v3 path contains 'v3', §A9 names no facts file, and seeds are in §A8. The default target for the recomputed F16 is therefore the committed v3 metanet_precal_facts.json, which the v3 facts code rewrites wholesale. That breaks 'committed v3 records are never edited'. The reused precal_part1.json and calib_data.npz sit in the sha256-frozen v3 raw directory, and prep() writes calib_data.npz back into it. v4 does not say whether these inputs are read-only, verified or rebuilt.

**Change.** (1) Form: 'Every v3 section not amended below applies word for word. Seeds are those of §A8 and output paths those of §A9; any v3 path not listed in §A9 is read-only for v4.'
(2) §A9, add:
- 'v4 pre-calibration facts: docs/lab/day_pattern/metanet_v4_precal_facts.json. It holds exactly the items §A6 lists as recomputed, records protocol v4 and the git blob hash of the reused v3 metanet_precal_facts.json, and is committed before any CMA-ES evaluation. v4 code reads reused facts from the v3 file and never writes it.'
- 'Reused v3 raw inputs are read only from /home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet/, after their sha256 matches the committed manifest; a mismatch stops the run. calib_data.npz is rebuilt into metanet_v4/ and must equal v3's array for array (day list, station order and masks bit-for-bit); any difference is a logged deviation that stops the run until the author decides. The v3 manifest is re-verified after every v4 batch.'
(3) §A10: a new test checks that, with v4 paths set, no v4 job (facts, calibrate prep/fit, postcal, freeze, gate) opens a v3 path in write mode. Run it against a read-only copy.

## R1-14 [minor] §A2 (a)–(d), rationale sub-bullet, 'New build assertions'; §A1 rule 2

**Defect.** 'L_min' means 250 m in A1 and the table minimum (300 m) in A2; read as 250 m, rule (a) picks 0.625 s (the number would be exactly 0.25). Units and the value of (d) are not stated, and (d) uses a single Q_o rather than the sum over merging entrances. 'Explicit Euler needs ≤ 0.5' is the FTCS heat-equation limit; for this scheme 0.25 is the zero-speed edge (reviewer derivation). The speed-update sink terms are never asserted together, and the φ term has no assertion at all.

**Change.** (1) In §A2 replace L_min with 'L_tab = min_i L_i of the generated table (300 m on step (b)); not the §A1 merge threshold L_merge = 250 m'.
(2) State units: T and τ in h, L in km, ν in km²/h, speeds in km/h, Q_o in veh/h, κ in veh/km/lane.
(3) Write (d) with ΣQ_o over the merging entrances of cell i.
(4) Give the values at 0.75 s: (a) 0.208; (b) 0.234; (c) 0.075; (d) max 0.541 (cell 1). Unit test 2 asserts them.
(5) Add (f): 'in every cell, T/τ_min + δ_m,max·T·ΣQ_o/(L_iλ_iκ_min) + v_cap·T/L_i < 1 (max 0.713, cell 1)'. Report-only: the maximum per-step φ factor 2φTρv/(Lλρ_cr) in cell 23.
(6) Replace 'explicit Euler needs ≤ 0.5' with 'for this scheme the shortest-wave edge is 0.25 as v → 0 and ≈ 0.3 at v_min (2026-10-06 scan); 0.25 is a design margin, not a necessary condition'.
(7) Replace 'necessary linear conditions, not sufficient ones' with 'frozen-coefficient linear conditions without boundaries or clipping'.

## R1-15 [minor] §A2 'New, report-only' margins and Payne diagnostic; §A11 item 7; §0.6 V1

**Defect.** The Payne diagnostic is undefined. Neither report-only diagnostic says it has no consequence, and a margin-0 day invites a 'tie artefact' waiver of an N0 FAIL. The residual risk that a converged scheme flips a margin-0 day between T and T/2 (20230517: count margin 0 at 2.5, 1.25 and 0.625 s) is not disclosed. The absolute-value margins lose the sign, and 'deciding bins' is undefined.

**Change.** (1) Payne diagnostic: 'per group g and ρ ∈ {1.0, 1.25, 1.5, 1.75, 2.0}·ρ_cr,g at the frozen parameters: c = √(νρ/(τ(ρ+κ))) vs ρ|V′(ρ)|, and the maximum semi-discrete growth rate (s⁻¹) on g's shortest cell.'
(2) Margins, replace with: 'per day and pair at T and T/2: the count margin (best 7-bin count − 5) and, for every bin of the window reaching it plus every bin whose status differs between T and T/2, the signed m_v = 40 − v_u and m_d = (v_d − v_u) − 20 (mph, detector scale).'
(3) Add: 'The margins and the stability diagnostic are report-only. They cannot waive, re-judge or soften N0 or any gated row, and cannot select the nominal plant or ensemble members.'
(4) Add: 'If the day sets differ, the differing days are also run at T/4 = 0.1875 s, and v_u and v_d − v_u per deciding bin at T, T/2 and T/4 are reported with r = |x(T/2) − x(T/4)|/|x(T) − x(T/2)|. Numbers only: no label, no effect on N0, the route or T.'
(5) A11.7 and V1: 'Residual risk: a day at a threshold can flip between T and T/2 even when converged (v3: 20230517 at margin 0 at every converged step). Such a flip is an N0 FAIL (no tolerance).'

## R1-16 [minor] §A1 (after relocation (a)); §4.7 report-only

**Defect.** Pioneer Tr's cell 32 is now an unscaled G3 cell between B1 and B2, with no v3 counterpart. At high c1, B1's discharge could be capped there and c1 would become inert, with no report. A synthetic probe showed no flat region, so this is undisclosed rather than demonstrated. The C6/V4-09 fix ('cell 32 ρ > ρ_cr' as relocation) would fire on every B2-queue day and force F̂ to be non-estimable.

**Change.** Add to §A1: 'Cell 32 (Pioneer Tr) is unscaled between B1 and B2. At high c1, B1's discharge may be capped there (static estimate c1 ≳ (1 + X12/(2·Q_cap,G3))/θ1; model-dependent). No relocation rule on cell 32's density is used: it lies in B2's queue on B2 days and can lie in B1's acceleration zone.'
Add to §4.7, report-only:
- days: usable calibration days with a real P_1 and no real P_2 episode;
- pairs: model P_1 with no P_2 and no relocation;
- quantity: the median model B1 discharge (Pioneer Tr + X12) over the C4 window vs c1 at c2 = 1, and R(g) = median increment per 0.05 step / (0.05 × median at c1 = 1.00).
Do not adopt a cell-32 density relocation rule.

## R1-17 [minor] §A6 'Reused as committed' / 'Recomputed'; §A11 item 6

**Defect.** F14's 'G1/G2 cells with a §1.7 ratio > 1.10' depends on the cell table and was never computed in v3, so 'None depends on the cell table' is false. F3, F7 and F15 have no stated status. The recompute list points to a manifest that does not exist.

**Change.** A6:
- Reused as committed: add F3, F7 (outcome base/base) and F15. Delete 'None depends on the cell table'.
- Recomputed: list explicitly: F1 (cell table and merge log, must equal §A1); F14's G1/G2 §1.7 ratios on v4 cells 1–26 (report-only); F16 per the F16 fix; F7's cell references restated (X12 in cell 31, X13 in cell 34).
A11.6: add 'v3's F14 omitted the G1/G2 ratios required by v3 §1.7; computed for v4 only.'

## R1-18 [minor] §A8

**Defect.** 'No v3 seed is reused' is literally false: the reused F8 bootstrap and F11 floors were computed with 7,190,094 and 7,190,097. A8 also gives no v3→v4 concordance, and 7,190,094 had two uses.

**Change.** Replace with: 'No v3 seed is used for any new draw. F8 (7,190,094) and F11 (7,190,097) are reused as committed and are not re-drawn.' Add a 'replaces v3 seed' column taken from v3 §8.1 (reviewer's mapping: 011–018→010–017; 021–028→018–025; 030–092 and 100–108→026–097; 093→300; 094, §4.7 correlations only, →098; 095→301; 096→302; verify against v3 before commit).

## R1-19 [minor] §A10 tests 9, 18; §A2 'New build assertions'; §A9 records

**Defect.** Several smaller test and code gaps:
- Test 9 drops v3's 'the split builder reproduces §3.1'.
- v3 has two tests numbered 18, and the clipping test still compares 2.5 s with 5 s.
- Nothing requires the A2 assertions to run against the T each simulate() call uses; the v3 code defaults to T = 5 s at several call sites.
- The v3 freeze record has no T field.

**Change.** Test 9: append 'and the split builder reproduces the §3.1 date lists'. Renumber v3's tests 18 as 18a (P7c) and 18b (clipping); 18b compares T and T/2 (0.75 vs 0.375 s). Test 2: add 'simulate() on the v4 table at T = 5 s and at 2.5 s raises'. §A2: 'Assertions (a)–(f) are evaluated inside every simulate() call against the T that call uses.' §A9: 'The v4 record stores T and T/2; every ledger row of a simulating batch states its T, and a mismatch is a bug (fix, re-run, log both).'

## R1-20 [minor] §A9 'Compute'; §0.6 V1

**Defect.** The 17-h figure covers only the base stages. The continuation (about +6 h), F1 (+6–12 h plus a grid) and the ensemble grids are excluded, so a worst case above 24 h escapes the 24-h notice rule.

**Change.** 'Projections (to be measured on synthetic inputs before launch): base ≈ 17 h; with continuation ≈ 23 h; with F1 and continuation ≈ 30–36 h, plus ≈ 0.8 h of grid per ensemble member and the optional v3-set sensitivity. The 24-h rule applies to the worst-case projection of all stages that can run without a new author decision.' Repeat the figures in V1.

## R1-21 [minor] §A1 'Geometry variants' (weave sensitivity)

**Defect.** The B-cell rule starts B2 at 'the cell fed by B2's merging entrance', but in the weave reading E14 is lane-adding, so B2 is undefined there.

**Change.** Add: 'In the weave sensitivity, B2 = the cell fed by E14 through the cell holding X13, whatever E14's lane event.'

# Round 2

**Verdict.** The revised v4 is not ready yet for the author to confirm §0.6. It will be once the 5 major corrections are made and the author settles the A3 (d) choice. The numerical content holds up: four independent data-free checks reproduced the 39-cell step-(b) table, the merge log, the FD groups, the station and ramp placements, the A2 values at 0.75 s, the test-2 growth figures (1.1e-5, 2.0e-5 and 4.95e-3 s⁻¹), the A3 thresholds (75.3, 67.7, 64.4 and 72.9 km/h) with their implied limits, F16 R = 1.371 and n_val = 97, with no mismatch. All 21 review fixes are present. Five majors remain, and they bear directly on the items the author is asked to confirm. (1) The A3 (d) disclosure is false under v4's own graded penalty, so V3 currently rests on a wrong justification, and the author must choose to keep (d) as insurance or drop it. (2) P11-k (V8) cannot be implemented for ensemble members and F1 as written. (3) Its backed-cell set conflicts with its own "station cells never count" sentence, and it reuses the B1/B2 names. (4) Freeze choice (7) (V7) leaves out the deterministic-only case in which F̂_T is not usable, which reopens the forking path it was meant to close. (5) The Form path rule contradicts the ledger appends and code changes v4 needs, so test 22 would fail by construction. All five are text fixes and need no new computation, simulation or real-day data. The 20 minors are wording, precision and test-specification gaps. They should go in before commit, because the document becomes binding word for word. V7 and V9 remain "decide" items by design. Caveat: I merged the checkers' reported replays and scans without re-running their scripts. I spot-checked the cited v4 lines and v3 §0.3 lines 52–58 (which confirm the F̂_T-not-usable case). The replay numbers in the A3 (d) correction depend on pycma 4.5.0 and numpy 2.5.3 and should be cited with those versions.

## R2-1 [major] §A3 (d), sentence "Disclosed: under v3's rule, seed 7,191,010 never reached an A3-feasible point in 4,000 evaluations" (feeds A11 item 11, §0.6 V3, test 19)

This sentence is false under v4's own penalty. Replace it with: "Disclosed (data-free replay, pycma 4.5.0, numpy 2.5.3): under v3's initialisation, seed 7,191,010 reached no A3-feasible point in 4,000 evaluations with a flat J = 10. With (b)'s graded penalty it reaches one at evaluation 16, and every base seed by evaluation 27." Then the author decides in V3: (i) keep (d) as insurance so that every restart starts A3-feasible, and say that this is the reason; or (ii) drop (d), leaving v3 §4.4 unchanged, and delete it from A11 item 11, the V3 row and test 19.

## R2-2 [major] §A12 rows 'Evaluated on' and 'Plants' (lines 426–427)

Split the rows by plant. Nominal: usable calibration days at the freeze, where a failure is a route stop before any validation run, plus all usable validation days in the gate (gated). Ensemble candidate: a failure on calibration or validation days makes that candidate inadmissible, as with its own step-halving under v3 §4.6; no route stop. F1: calibration days at F1's own freeze, where a failure is an F1 FAIL (route stop) before F1's gate run, plus validation days in F1's gate (gated). As written, an ensemble candidate failing would stop the route, and F1, which is fitted only after a base-gate FAIL, would be judged 'at the freeze'.

## R2-3 [major] §A12 'Backed bin' (line 423) and §A14 P11-k bullet (line 449)

Replace "B1: cells 26–31; B2: cells 33–34. Station cells never count." with "P_1: cells 26–31; P_2: cells 33–34. The pair's own station cells (25 and 32 for P_1; 32 and 35 for P_2) never count; cell 27 (S1147, fit layer only) counts." Use the same text in §A14. The rename to P_1/P_2 avoids a clash with §A1/V2, where B1 = 28–31 and B2 = 33–34 are the bottleneck sets. Excluding cell 27 instead (P_1 = 26, 28–31) would be a design change for the author, not a fix.

## R2-4 [major] §A6 (7) (line 291), §0.6 V7 (line 464), A11 item 8(a)

Replace "if F̂ is not estimable by rule (i) or (iv) at the freeze" with "if no usable spread exists at the freeze, that is, F̂ is not estimable by rule (i) or (iv), or F̂ is not estimable by (ii)/(iii) and F̂_T is not usable (v3 §0.3, §4.7)". Make the same change in V7 and A11 item 8(a). v3 §0.3 lines 54–56 confirm that 'F̂_T not usable' is also a deterministic-only case, and it is known from calibration days at the freeze.

## R2-5 [major] Form paragraph (line 5: "any v3 path not listed in §A9 is read-only for v4"), §A9, §A10 test 22

In §A9, define 'v3 path' as the v3 raw-run directory plus the v3 records (metanet_precal_facts.json, metanet_calibration.{json,md}, the v3 addenda). List vsl_lab/runs/ledger.csv (append-only), vsl_lab/plants/metanet.py, vsl_lab/jobs/metanet_calibrate.py and tests/test_metanet.py as shared paths that v4 may modify. Restrict test 22 to v3 paths as defined. As written, test 22 fails by construction, because ledger.append opens LEDGER_PATH in 'a' mode (vsl_lab/ops/ledger.py:40).

## R2-6 [minor] §A3 'Why' (line 228), "δ_m in merge-fed station cells (1, 4, 14)"

Write: "δ_m in merge-fed event-station cells (4, 14; cell 1 is S453, input only)".

## R2-7 [minor] §A3 'Why' (fit-informed narrowing disclosure)

Add the bullet: "v3's restarts also fall below the A3 thresholds at G3 (7 of 8 restarts, by 0.26–1.94 km/h) and G1 (2 of 8: 7,190,011 by 1.85 and 7,190,014 by 3.21 km/h); A3 is expected to be active at G2 and probably at G3."

## R2-8 [minor] §A3 (g) implied limits (line 225)

Round every limit up so that each stated value is feasible: v_f,G1 ≥ 100.2, v_f,G2 ≥ 90.1, v_f,G3 ≥ 97.06 (through G4); a_G1 ≥ 1.451, a_G2 ≥ 1.26, a_G3 ≥ 1.183, a_G4 ≥ 1.39. Alternatively, write each one with '≈'. Exact values: 100.18, 90.08, 97.0501, 1.4506, 1.2568, 1.1821, 1.3867.

## R2-9 [minor] §A3 Constraint and threshold table; test 19 ("to 0.1")

Add: "thr_g is computed at full precision from F6's c_s (75.2829, 67.6900, 64.3738, 72.9309 km/h); the table shows it to 0.1 km/h." The choice changes optimiser trajectories: seed 7,191,012 first becomes feasible at evaluation 27 with exact values and at 39 with tabled ones.

## R2-10 [minor] §A3 (d) for F1 seeds 7,191,018–025 (n = 19), and §A5

Fix the order of the 19-vector, e.g. "v4 base parameter order, then Δ, η". The rejection-sampled x0 depends on it, and test 19 can check exact draws only if the order is fixed.

## R2-11 [minor] §A3 (f) flat share and the non-identifiable flag

Write: "the non-identifiable flag applies v3's ≥ 50 % rule to the width of the A3-feasible intervals (j = 2…8, 6 intervals, 97.5–150 km/h)". Alternatively, keep the full 70-km/h width and say so explicitly.

## R2-12 [minor] §A1 cell-table caption (line 64); §A10 test 9

Caption: "km to 3 decimals, except split points that are exact at 4 decimals (−5.4495, 0.9105, 4.9365, 6.5675); every split is an exact equal division, and test 9 compares exact values (tolerance ±0.5 m), not printed ones." At present 4.49575 and 5.37725 print as 4.496 and 5.377, which contradicts the caption.

## R2-13 [minor] §A1 'Geometry variants'; test 9 ("per station and variant ... checked against §A1")

Add one binding line: "Variants (cells 1–35 the same everywhere): weave: λ = 3 in cells 33–34; step (a): λ = 3 in 36–39, merge 4 goes into the λ = 3 piece 8.999–9.217 (X15 lane end moves to km 9.390, logged); step (c): N = 35, merges 1–3 and 5, no G4, relocation (a) = cell 35. Stations, ramp cells, corrections, B1 = 28–31, B2 = 33–34 and station cells are unchanged."

## R2-14 [minor] §A1 concordance table

Optional: add the row "Origin cell; E1, X1, S453 | 1 | 1 (unchanged)", since v3 §2.3 and §2.4 cite cell 1.

## R2-15 [minor] §A1 Groups, bullet 3 (line 61)

Remove "§2.2 g(N)" from the list of v3 'G3' uses that mean G3 ∪ G4, or write "g(N) = G4 (cell 39)". g(N) must be a single group.

## R2-16 [minor] §A2 sub-bullet (a) (line 183)

Write: "for this scheme the shortest-wave edge is νT/L² = (ρ+κ)/(4ρ) as v → 0 (≥ 0.257 within bounds, → 0.25 as κ/ρ → 0). It is ≈ 0.32 at v_min with τ = 10 s, κ = 5, ρ = ρ_max, L = 300 m, and larger for larger τ (≈ 0.66 at τ = 60 s). 0.25 is a design margin, not a necessary condition."

## R2-17 [minor] §A2 table row (a) / 'So T = 0.75 s' bullet

Optional transparency: add "At 1.0 s only (a) fails; (b)–(f) pass ((c) 0.100 exactly at its limit, (f) 0.950). At 1.25 s, (a), (c), (e) and (f) fail." This shows that a margin condition sets the rung.

## R2-18 [minor] A11 item 9 (line 414)

Write: "Worst stable-state growth: 1.1e-5 s⁻¹ at 0.75 s and 2.0e-5 at 1.0 s (floor state with V′ kept: τ = 10, ν = 30, κ = 60, v_f = 120, ρ_cr = 30, a = 3.5, ρ = 2ρ_cr, L = 304 m); 4.95e-3 at 1.25 s (floor state with V′ = 0: τ = 10, ν = 90, κ = 5, ρ = ρ_max, L = 300 m; 217 stable states > ε)."

## R2-19 [minor] §A10 test 2 (ii) and (iii), Grid (line 390)

(ii): change "(a)–(f)" to "(a)–(d), (f)", because (e) is the test's own gate (iii). (iii): write "θ_j = jπ/181, j = 0, …, 181 (A(−θ) is the conjugate of A(θ))". State that growth = ln|1 + Tλ|/T with T in s, since §A2's units line puts T in h. Give a zero tolerance, e.g. 'stable iff max Re λ ≤ 1e-9·max|λ|'. The scan found no state with Re λ in (0, 1e-12], so the tolerance does not change any classification.

## R2-20 [minor] §A10 test 21 (line 377)

State that (i)–(iii) test the P11-k classifier on synthetic per-bin ρ, v and station-speed arrays with known answers. If a simulated 4→3-drop case is kept, pin its full parameter vector and demand, and state the expected result when no P_1 episode arises (in review toys only 12 of 90 produced one). For (iv), pin the full parameters, demand and c_s, not only ν and κ.

## R2-21 [minor] §A12 'Backed bin' / 'Reported' (F1 and c_k interaction)

Fix the ρ_cr reference: either the bin mean of the per-step effective ρ_cr,i (record it in simulate(), which now records only bin-mean ρ) or the base ρ_cr,i (conservative). Add: "qualifying bins are pooled over all model P_k episodes of the day" and "congested = bin-mean ρ_i > ρ_cr,i". Add to §A13, report-only: the backed share of the model episodes behind each exact ĉ_k,d in §4.7, because P11-k is gated only at c = 1.

## R2-22 [minor] §A12 or §A7 (v3 §0.3 PASS text and the §6.1 non-trigger list, not amended)

Add: "v3 §0.3 reads 'P1–P9 and P11-k'; P11-k joins §6.1's non-trigger list (a P11-k-only failure is a route stop)." Under the word-for-word rule, neither v3 text names P11-k.

## R2-23 [minor] §A6 'Recomputed' (F1, line 269); test 9 (line 370), A11 item 2 (line 398), A11 item 8(a)

Add "the per-entrance merging flags (E15 under V9)" to the F1 recompute list. Mark every clause that depends on V9 ("E15 δ_m = 0 under step (b)") with 'if V9 adopted', since V9 is still 'decide'.

## R2-24 [minor] Section and item labels (§0.6, §A1–§A14)

Add one line under Form: "Bare 'A1'–'A10' and '§0.6' inside v3 text mean v3's own author items; v4's are §A1–§A14 and V1–V9." Alternatively, rename v4's labels (e.g. v4-A1…). Without this, v3 references such as 'A4' and 'A10' are ambiguous.

## R2-25 [minor] §0.6 V8 (line 465), "blocking review fix 1"

Drop the reference, or cite a committed review record. The review exists only in a session scratchpad, so a binding protocol would point to something that cannot be found.

## Round-2 disposition

- R2-1: option (ii) applied (no rejection-sampled start); option (i) shown as the alternative in V3 (author decides).
- R2-19: tolerance 1e-9·max|λ| adopted with a report-only count; the reviewer's 'changes no classification' claim not adopted.
- R2-20 (iv): toy parameter values pinned in the test source at §A6 step 2, before any CMA-ES evaluation.
- Final check (workflow wf_146b659f-4ba): 1 major (V3 alternative not shown) and 8 minor items, all applied by the main session.
