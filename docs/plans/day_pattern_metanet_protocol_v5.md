# METANET plant of U.S.169 SB: protocol v5 (binding; author items W1–W13 answered 2026-10-08, D4.14; rev2 + answers)

**What v5 is.** v5 is plant attempt 3 (D4.13, option A′). It keeps v4's plant and changes one thing: the calibration objective. The objective now targets jam statistics (occurrence, onset, duration, discharge and extent at B1/B2) instead of per-bin speeds and flows. It is time-boxed: any pre-registered stop or FAIL closes the METANET route and pauses the day-pattern track (option E), with no further rescue (§B11).

**Form.** v5 = protocol v4 (`day_pattern_metanet_protocol_v4.md`, itself v3 + §A1–§A14) + the v4 addendum of 2026-10-07 (D4.10) + the amendments §B1–§B13 below.
- Every v3/v4 text not amended here applies word for word.
- Under v3 §6.3 a changed objective is a new protocol version: it is committed before it runs, uses fresh seeds (§B9) and gets a decision-log entry.
- Labels: v5's amendments are §B1–§B13; its author items are W1–W13 (§0.6 below).
- **rev1** folds in review round 1 (55 findings, skeptic-checked). The log is at the end. No real day was simulated for rev1.
- **rev2** folds in the check round on rev1 (27 issues, each verified against the texts and the code; sub-table "Check round" at the end) and the lead's binding resolutions on §B11.2 and P8g. No real day was simulated for rev2.
- **Answers (author, 2026-10-08, D4.14):** W1–W12 as proposed; **W13: the strict alternative** (every post-look FAIL → PASS from a fix is KILL-only), now the rule in §B11.2. The realism rows are recorded as a dated D4.13 note (§B1.3).

Decisions behind v5:
- D4.11: v4 stopped at the freeze under (7)(b).
- D4.12: the hidden-demand check found demand is not the cause; its follow-up diagnostic.
- D4.13: option A′, time-boxed, fallback E.

```
 why each amendment exists (v4 lesson -> v5 change)
 ---------------------------------------------------
 per-bin RMSE: a jam shifted by >= half its length    -> B1 J5: timing scored once (P4, capped at 90 min);
   scores worse than no jam (synthetic); v4 never jams;     sizes compared on matched pairs; per bottleneck-day
   G3 forced to 1,900 jams B1 on 21/22 days but             no outcome costs more than the s = 1 miss reference
   J 0.178 -> 0.455 (D4.12; inference, not proved)          on the B_k rows; P7b/P7c, P8g, s (unbacked dips),
                                                            guards and off-peak realism rows can still charge
                                                            a jam (bounded and listed, B1.6)
 v3: B1 "congestion" from speed dips with no queue;   -> B1.2 credit only for episodes backed on their own
   v4 P11: cell 26 or 27 alone backs a P_1 bin              bins, by a queue running from cell 26 into B1
 equal-weight event rows: a missed B2 day costs ~4x   -> B1.5 parity weight on B2 extras (exact on the
   an extra one (reviewer recomputation)                    P3-2 and X-2 rows)
 an event fit can ignore P1a/P1b/P1c (D4.12 plant:    -> B1.3 guard hinges, zero inside the gate's pass region
   whole-day NRMSE_q 0.235, NRMSE_v 0.314)
 J5 cannot see a G4 queue (rule (iv) stop path)       -> B1.3 P8g also charges a relocation at c = 1
 F-hat rules (i)-(iii) stopped v4                     -> B3 kept unchanged (not eased); only L_d -> J_d
 a discrete J changes what step-halving measures      -> B4 checked on J5 AND on the v4-form J
 ensemble filtered on validation days; more near-ties -> B6 members fixed on calibration days; gate refuses others
 "no further rescue" (D4.13)                          -> B11 no F1; every stop or FAIL -> E
 a post-result bug fix could flip an outcome unseen   -> B11.2 v3 §6.3 rule on every committed text, full re-run;
                                                            one pinned audit per freeze record and per gate
                                                            outcome; any post-look FAIL -> PASS is
                                                            KILL-only (W13 strict); both outcomes logged
 the 97 validation days are unlooked and GO-capable   -> B5 stop-only in-sample screen before the look
```

---

## B1. Objective J5

*Replaces v3 §4.3 and v4 §A7's "objective unchanged". v3 §4.2 is unchanged (NRMSE, W_d, S_q,d, S_v,d, Q_A, S_c,d). It is used by P1, by the guard and realism rows below, and by the v4-form J of §B4.*

### B1.1 Event layer: the gate's own code, with the real side frozen

**Model side.** It is exactly the gate's:
- `metanet_postcal.model_day` and `model_pairs`: the observation operator v/c_s, with real NaN bins and event-invalid station-days masked;
- the EA-2 corridor rule: v_u < 40 mph and v_d − v_u ≥ 20 mph in 5 of 7 bins, with episodes merged across gaps under 30 min;
- the overlap rule ±60 min: `metanet_postcal.overlaps` (and its identical inline copy in `metanet_events.p7c_pair`);
- `metanet_events`: one-to-one nearest-onset matching within ±90 min, B1 censored at the real t_c on both sides, C4, P7c unions;
- `metanet_gate.extent` and `metanet_postcal.p11_core`.

There is no second implementation. The gate's inline row logic in `metanet_gate.deterministic()` is refactored into per-day item functions that J5 and the gate share (test 30).

**Real masks are read live.** These gate functions read the real per-bin NaN mask, the station-day validity and the real downstream flows (for the model's C4 window) from the Mayfly cache at run time. They are not in the facts file. So:
- a sha256 manifest of the cache files for the 22 calibration days is committed before the protocol commit (§B8 step 1);
- it is verified before every J5 batch; a mismatch stops the batch.

**Real side.** It covers the 22 usable calibration days only. It is computed once and committed in `metanet_v5_precal_facts.json`, with its sha256, before the first J5 evaluation (§B8). It holds:
- episodes per pair, t_c and heavy flags;
- C4 (Q_dis, r), merge-section ratios, extents and P7c unions;
- W_d, F_d, and the P1c sets with their leave-one-day-out nulls;
- per day, N1⁻ᵈ − N2⁻ᵈ, and the counts of days with N1⁻ᵈ − N2⁻ᵈ < 0.02 and < 0 (§B1.7);
- every qualifying set (P5c's included, §B1.3), the row set R and the weights ω_k;
- the full-precision ρ_cr,G3 of the three D4.12 plants (§B7);
- the git blob hashes of the reused v3 and v4 facts files (§B8 step 4).

J5 refuses to run if the hash differs (test 35).

### B1.2 Creditability (queue backing inside J5; rewritten in rev1)

v4 §A12's "qualifying bin" and "congested cell" are used unchanged. Two terms are new.

**J5-backed bin.**
- P_1: a qualifying bin in which cells 26, 27 and 28 are all congested. That is, the congested run that reaches cell 26 continues without a gap into B1 (cells 28–31).
- P_2: a qualifying bin in which cell 33 (B2's head) is congested.

**Creditable episode.** A model P_k episode whose **own** qualifying bins are ≥ 50 % J5-backed. An episode with no valid qualifying bin is not creditable. It is computed per episode from the per-bin arrays `p11_core` already builds.

**What creditability gates (only these):**
- the P3-k hit credit on a real-active day;
- the P4-k, P5a-k and P7a-k matches. Matching itself is the gate's, over all model episodes. A match to a non-creditable episode scores the miss value 1. A nearer non-creditable episode therefore takes the match, as in the gate, and that item scores 1.

**Everything else uses all model episodes, exactly as the gate does:** P5c, P7b, P7c, the extras (P3-k on real-inactive days, X-k, P8(iii)) and P8g's spurious and extra flags, including P8g's hit-day condition, which is the gate's P3 agreement (any overlap, creditable or not; rev2, lead decision 1). So test 30's equalities hold on these rows.

**Consequences.**
- If all of a day's model P_k episodes are non-creditable, the P3-k hit credit and the P4-k, P5a-k and P7a-k matches of that day take their miss values. If one of these episodes overlaps a real episode or has a bin in a shaping window, s = 1 (§B1.4).
- Non-creditable episodes still count wherever the gate counts extra or spurious episodes.

**Differences from the gated P11-k (disclosed; rev2).** The gated P11-k (at the freeze and at the gate) stays v4 §A12 unchanged: pooled over the day's P_k episodes, any one congested cell in 26–31 (P_1) or 33–34 (P_2). J5's rule differs from it in three ways:
- **per bin, stricter.** A J5-backed bin (cells 26–28 all congested; cell 33) is always P11-backed;
- **head location, stricter.** Under v4 §A12, cell 26 or 27 alone backs a P_1 bin. A queue headed in G2 or at the 4 → 3 drop, whose acceleration zone is over-critical, would then earn credit while c1 and θ1 act on cells that hold no queue (review, physics-02);
- **per episode, both directions.** Stricter where pooling would let a backed extra make an unbacked dip that overlaps the real episode creditable. Looser where an unbacked extra pulls the day's pooled share below 50 %: J5 still credits the backed hit, while P11-k counts the day as unbacked (review, math-3; check round). So J5 credit does not imply P11 backing, and a J5-optimal plant can fail P11-k at the freeze (§B13 item 9 (m)). Unbacked extras are charged as extras (P8g (ii), P3-k, X-k), not through backing.

**Residual (disclosed; widened in rev2).** The rule still credits a queue headed just upstream of B_k whose acceleration zone makes the cells up to B_k's first cell over-critical:
- P_1: a head at cell 26 with the zone over cells 27–28; or a head at the unscaled lane-end cell 27 (v4 §A1) with a one-cell zone over cell 28. A one-cell zone is the case D4.10 describes (synthetic evidence), so the second case may be the likelier one [inference, untested];
- P_2: a head at the unscaled cell 32 (Pioneer Tr) with a one-cell zone over cell 33.

Test 40 documents all three as creditable. No report can separate them from a queue headed in B_k: the §B5 head cell is then B_k's first cell (28 or 33), so §B5 flags those days "residual not excluded"; §B3's upper-half c1 count is a further, partial signal.

**Not adopted:** a speed-based backing rule (review physics-01 (a)). It does not exclude its own example.

**Reported per restart:** the distribution of ρ_i/ρ̄_cr,i in the backing cells; the share of model P_k episodes that are P11-backed (v4) but not creditable (J5); the number of calibration days with a creditable P_k hit on a day P11-k counts as unbacked (rev2).

### B1.3 Rows

J5 = Σ_r w_r·A_r / Σ_r w_r, where A_r is the mean of row r's items over its qualifying set.
- Qualifying sets are anchored on real data and fixed at prep.
- A row whose set is empty on the calibration days is dropped. Known now: X-1 is dropped, because B1 is real-active on 22/22 days.
- Expected |R| = 18, so Σ_r w_r = 17 + ω_2. Items lie in [0, 1], except P3-k, which can reach 1 + ε.

**Target rows** (the D4.13 statistics, with gate definitions, capped):

| Row | Gate row | Qualifying set | Item | w |
|---|---|---|---|---|
| P3-k | P3-k | all days | real-active: 0 if a creditable model P_k episode overlaps a real one (±60 min), else 1 + ε·s; real-inactive: 1[any model P_k episode] | 1 |
| X-2 | P8(iii)-2 | real-B2-inactive days | 1[any model P_2 episode] | ω_2 (§B1.5) |
| P4-k | P4-k | every real B_k episode | matched to a creditable episode: min(\|Δonset\|, 90)/90; otherwise 1 | 1 |
| P5a-k | P5a-k | heavy B_k days | matched to a creditable, C4-usable episode: min(\|Q̂_dis/Q_dis − 1\|, 0.15)/0.15; otherwise 1 | 1 |
| P5c | P5c | the gate's `both_q`: days heavy at both with the real merge-section ratio defined (row kept if the days heavy at both number ≥ 6, as the gate) | min(\|ρ̂/ρ − 1\|, 0.15)/0.15 on the merge-section ratio (the gate's matched episodes); 1 if the model ratio is unusable | 1 |
| P7a-k | P7a-k | heavy B_k days | min(\|dur_m − dur_r\|, 90)/90 on the matched longest episode if it is creditable (B1 censored at the real t_c on both sides); otherwise 1 | 1 |
| P7b | P7b | days heavy at B1 or B2 | the gate's extent (all model episodes): min(\|error in extent-station index\|, 3)/3, in event-valid station order; 1 if no matched model episode at either bottleneck | 1 |
| P7c | P7c | days heavy at B1 or B2 | the gate's model union (all model P_1/P_2 episodes): min(\|dur_sys,m − dur_sys,r\|, 90)/90; 1 if no model union interval overlaps | 1 |

**Deliberate departures from the gate statistic.** "Otherwise 1" and creditability are needed for miss dominance (§B1.6) and for §B1.2:
- the gate scores an unmatched P7a and a non-overlapping P7c as |0 − dur_r| and leaves unmatched days out of P5a and P5c; J5 scores them 1;
- the gate's P3 and P4 credit any overlap or match; J5 credits creditable episodes only.

Test 30 checks the mapping.

**Guard rows.** They are zero, or near zero, inside the gate's pass region, and steer the fit away from plants that would fail the gate.

| Row | Gate row | Qualifying set | Item | w |
|---|---|---|---|---|
| P8g | P8(ii); P8(i) at pairs sharing no station with a real-active pair; P8(iii) on hit days (the gate's P3 agreement); relocation (rule (iv)) | all days | 1 if (i) ≥ 1 spurious episode at a pair outside {P_1, P_2} (the gate's P8 definition), or (ii) on a real-B_k-active day where some model P_k episode overlaps a real P_k episode (±60 min; the gate's P3 agreement, creditable or not), ≥ 1 model P_k episode that overlaps no real P_k episode (the gate's P8(iii) flag; all model episodes), or (iii) relocation (a) (D4.10 form) or (b) at c = 1 on day d; else 0 | 1 |
| P1a^h | P1a | all days | clip((NRMSE_q(d, S_q,d) − 0.10)/0.20, 0, 1) | 1 |
| P1b^h | P1b | all days | clip((NRMSE_v(d, S_v,d) − 0.20)/0.40, 0, 1) | 1 |
| P1c^h | P1c | real-active days | clip(D_d/s_d, 0, 1) on the gate's P1c set (formulas below) | 1 |

For P1c^h:
- D_d = NRMSE_v(model) − NRMSE_v(N2⁻ᵈ);
- s_d = max(0.02, NRMSE_v(N1⁻ᵈ) − NRMSE_v(N2⁻ᵈ));
- N1⁻ᵈ and N2⁻ᵈ are the v3 §5.4 nulls built from the other 21 calibration days.

**P8g (ii) on hit days only (rev2).** The gate's P8(iii) flags, on every day, any model P_k episode that overlaps no real one (`metanet_gate.deterministic`, P8 block). P8g (ii) mirrors it on the days the gate's P3 counts as agreeing at a real-active B_k. On real-inactive days extras are charged by P3-k and X-k; on miss days a mistimed jam is charged once, as the P3 miss (§B1.8).

**P8g's relocation clause (new in rev1).** J5 otherwise cannot see a G4 queue confined to cells 36–38: it makes no event, and G4 has no target row. Relocation at c = 1 on any calibration day means c2\* < 1.00, i.e. rule (iv) and a stop at the freeze. So the clause is zero for every plant that can reach the gate. It also catches relocation (b) on real-B2-active days, which P8's spurious rule exempts (the pair shares Old Shakopee Rd with P_2). It sees c = (1, 1) only: relocation at any other grid pair with c2 ≤ 1.00 still stops the route and is unseen by J5 (§B13 item 9 (c)).

**Free-flow realism rows (off-peak F_d):**

| Row | Item (all days) | w |
|---|---|---|
| P1a^ff | min(1, NRMSE_q(d, S_q,d ∩ F_d)/0.30) | 1 |
| P1b^ff | min(1, NRMSE_v(d, S_v,d ∩ F_d)/0.60) | 1 |

- F_d = 05:00–23:00, minus W_d, minus ±30 min around every real episode at any event pair.
- v3's ≥ 100-pair rule applies to every NRMSE. An unscored item is left out of its row mean and counted.
- **They are off-peak rows, not whole-day rows:** W_d removes 15:00–19:00 at every station.
- **Share of the weight:** 2/(17 + ω_2), about 9 % at ω_2 ≈ 5.8.
- **Provenance.** The D4.13 log entry did not mention them. The review traced them to the option text the author approved on 2026-10-07 ("+ a small weight on whole-day speeds/flows (free-flow realism)"). On 2026-10-08 the author confirmed them; this is recorded as a dated note to D4.13 in D4.14.
- **Not changed (review physics-10, disclosed).** Because F_d drops 15:00–19:00 everywhere, PM bins at the G1 stations and at T.H.101 are scored only by the P1 hinges and P8g (with its relocation clause). Scoring them would double-penalise a longer or mistimed queue that reaches G1.

**Taper** (P5a, P5c, P7a, P7b, P7c):
- item ← t + (1 − t)·item, with t = clip((|Δonset| − 45)/45, 0, 1) for the matched pair;
- P5c and P7b use the larger t of the episodes involved; P7c uses the difference between the union intervals' start times;
- full credit up to 45 min, the miss value at 90 min, and no cliff at the match tolerance.

**Inadmissible** (unchanged; test 38):
- an A3 violator scores 10 + Σ shortfall (v4 §A3);
- clipping > 1 % or a non-finite value on any day scores 10;
- every admissible J5 is ≤ 1 + ε.

### B1.4 Shaping (only for a miss on a real-active (k, d))

A miss on (k, d) means: no creditable model P_k episode overlaps any real P_k episode that day.

**Windows.** For each real B_k episode j of the day:
- I_j = [onset_j − 60 min, end_j + 60 min];
- for a censored B1 episode, I_j = [onset_j − 60 min, t_c];
- there is no window spanning several episodes.

**g (speed margin, mph).**
- Per-bin margin m(b) = min(40 − v_u, (v_d − v_u) − 20), model speeds after the observation operator and the real mask. m(b) = −∞ where either speed is masked (NaN), as the event rule counts NaN as not qualifying.
- g_j = the maximum, over the 7-bin windows that overlap I_j, of the 5th-largest m(b) in the window; g = max_j g_j.
- g ≥ 0 iff some window has ≥ 5 bins with v_u ≤ 40 and v_d − v_u ≥ 20. This is the event rule except at v_u = 40.0 mph exactly, where the rule needs v_u < 40.

**h (backing margin).** Per bin, β(b) = min over cells 26–28 of ρ_i/ρ̄_cr,i for P_1, and ρ_33/ρ̄_cr,33 for P_2 (bin means; ρ̄_cr,i as in v4 §A12). β(b) > 1 exactly when the bin's cells meet §B1.2's J5-backed rule. h = the maximum of β(b) over every bin of every 7-bin window used for g. (rev1: h follows §B1.2's cells, so shaping does not reward congestion that cannot back a bin.)

**s.**
- s = 0.5·clip(−g/40 mph, 0, 1) + 0.5·clip(1 − h, 0, 1), with ε = 0.5.
- s = 1 if a model P_k episode overlaps a real P_k episode that day (±60 min), or if a non-creditable model P_k episode has a bin in a 7-bin window used for g. On a miss every overlapping episode is non-creditable. So an unbacked dip earns no shaping, wherever it lies near the real episodes and whatever other episodes the day has. Episodes with no bin in any window do not set s.
- (rev2, check round: rev1's rule, "s = 1 if all of the day's model P_k episodes are non-creditable", let a backed episode anywhere else on the day restore shaping to an unbacked overlapping dip, and let a non-creditable jam far from every window raise P3-k.)

**Why.** Without shaping, J5 is flat across never-jamming plants. With tolflatfitness disabled, pycma 4.5.0 gives a flat population no step-size boost (source checked in the design review). s is part of J5. It can change the ranking of plants that miss any real-active (k, d), the J5 optimum included. Its term is zero on every (k, d) with a creditable overlap; a miss can also reach s = 0 (g ≥ 0 and h ≥ 1 from a backed episode just outside the overlap tolerance, or at the v_u = 40.0 mph edge). The sensitivities ε = 0 and ε = 1 are reported (§B1.7).

### B1.5 Occurrence parity (weight ω_k)

For each real-active B_k calibration day d:
- U_k,d = 1/N(P3-k) + e_k,d/N(P4-k) + H_k,d·(1/N(P5a-k) + 1/N(P7a-k)) + b_d/N(P5c), where:
  - e_k,d = the number of real B_k episodes that day;
  - H_k,d = 1 if the day is heavy at B_k;
  - b_d = 1 if the day is in P5c's qualifying set and P5c is kept.
- U_k = the mean of U_k,d over those days. (Not R4's U_k.)
- ω_k = N(X-k)·(U_k − 1/N(P3-k)).
- ω_k uses real counts only and is committed at prep.

**What parity gives (exact only on P3-k and X-k).** One extra P_k day on a real-B_k-inactive day raises Σ_r w_r·A_r by exactly U_k on the P3-k and X-k rows (1/N(P3-k) + ω_k/N(X-k)). J5 therefore rises by U_k/Σ_r w_r.

**What it leaves out.**
- **The ε·s term.** U_k counts the P3-k miss at 1/N(P3-k), i.e. at s = 0. A miss costs up to ε/N(P3-k) more: 0.5/22 ≈ 0.023 numerator units, about 4.6 % of U_2 (review computation).
- **Rows a miss only partly determines:** P7b, P7c and P1c^h.
- **Rows an extra can also move:** P7c (in either direction: an extra near the real union can even lower it), P7b (through the speeds `extent()` reads), P8g (spurious episodes at other pairs, relocation), the P1 hinges and the realism rows.
- The net direction of the remaining imbalance is therefore not known. (The draft's "parity leans slightly towards extras" is withdrawn.)

**Expected value (review computation from committed counts; the committed value governs).** If the v5 facts reproduce the v3/v4 calibration events (B2 real-active on 9 days, one episode each, all heavy and all in P5c's set; 13 real-B2-inactive days), then U_2 = 1/22 + 4/9 ≈ 0.490 and ω_2 = 13·4/9 = 52/9 ≈ 5.78. Then Σ_r w_r ≈ 22.78, and one extra raises J5 by ≈ 0.0215.

**Why.** The gate's P3-k counts a miss and an extra alike. With equal row weights, a missed B2 day cost about 4 times an extra one on J5's own rows (4.00 at s = 0; 4.19 at s = 1; 4.9 with s = 1 if P7b and P7c are also counted as full misses; review computations from committed counts). The draft's "≈ 5×" came from the design review, whose row set is not recorded here. J5's optimum would then lean to over-predicting B2 and fail P3-2 or P8(iii). Tolerances: P8(iii)-2 allows 3 of 22 extra days in-sample and 10 of 97 at the gate; P3-2 allows 5 of 22 and 24 of 97 disagreements.

### B1.6 Properties (pre-registered; tests in §B10)

**Miss dominance (restated in rev1).** Two reference outcomes:
- **(k, d)-reference:** on a real-B_k-active day, "no model P_k episode, s = 1", with the other bottleneck's model episodes held fixed;
- **day reference:** "no model episode at P_1 or at P_2, s = 1".

Claims:
1. **Per (k, d).** Every model outcome at P_k scores no more than the (k, d)-reference on P3-k, P4-k, P5a-k, P7a-k and P5c. Each of these items takes its maximum at the reference (1 + ε on P3-k, 1 elsewhere).
2. **Per day.** Every model outcome scores no more than the day reference on every target-row item at a real-active bottleneck, and on P5c, P7b and P7c. Excluded by design: P3-k and X-k at a bottleneck that is real-inactive on d, where extras are charged.
3. So the weighted sums of the items in 1 and in 2 are dominated too.

**Disclosed bound.** With the other bottleneck's episodes fixed, a P_k jam (overlapping or not) can raise P7b and P7c by up to one item each, i.e. Σ_r w_r·A_r by up to 1/N(P7b) + 1/N(P7c) (2/22 on the calibration counts; review computation). It acts through the model union interval (P7c) and through the extent's start station, window and speeds (P7b). Example (review, with the committed `p7c_pair`): a B1 jam that neither matches nor overlaps the real B1 episode merges with the model's B2 episode and moves P7c from 0 to 0.975. Against a hit's P3-k saving of (1 + ε·s)/N(P3-k), the per-(k, d) target subtotal can rise by up to (1 − ε)/22 (0.5/22 at ε = 0.5; 1/22 at ε = 0) when P4-k, P5a-k and P7a-k gain nothing; for a jam that does not overlap, by up to 2/22.

**Where a jam can cost more than no jam** (complete list; test 25 checks the rows that depend on the P_1/P_2 episodes; the realism, hinge and P8g (i)/(iii) entries are listed by reasoning):
- **P7b and P7c**, per (k, d), within the bound above.
- **P3-k at a real-active bottleneck, through s** (rev2): on a miss, a model P_k episode that overlaps a real one, or a non-creditable one with a bin in a shaping window, sets s = 1 (§B1.4). P3-k then sits up to ε/N(P3-k) (0.5/22 on the calibration counts) above the same day without it, where s < 1. This is by design: an unbacked dip earns no shaping. Any jam can also move g and h through the speeds it changes, in either direction.
- **P8g:** an extra P_k episode on a day where some model P_k episode overlaps a real one (the gate's P3 agreement, creditable or not; rev2); a spurious episode at another pair (for example the jam's queue tail); a relocation at c = 1.
- **Realism rows P1a^ff and P1b^ff:** jam bins inside F_d, i.e. before 15:00 or after 19:00 and more than 30 min from every real episode at any event pair (weight 2/Σ_r w_r; items capped at 1). Calibration onsets are 14:15–16:30, so such jams are possible.
- **P1 hinges:** P1a^h and P1b^h when the jam pushes the day's whole-day NRMSE past 0.10 or 0.20; P1c^h when the model does worse than N2⁻ᵈ in the queue-area windows.
- **P3-k and X-k at a real-inactive bottleneck:** an extra, charged by design.

The header diagram's old wording "a miss is never cheaper than any jam" is withdrawn; claims 1–2 replace it. Both claims compare with the s = 1 references, not with the same day's no-episode outcome at its own s (rev2).

**Other properties.**
- **Parity:** §B1.5.
- **Zero cost:** J5 = 0 at the real series, given a synthetic cell state in which every qualifying bin of every real episode is J5-backed. (Real data have no cell state; with no backing every episode is non-creditable and J5 equals the miss values. Test 24.)
- **Real-anchored denominators:** no qualifying set or weight depends on model output.
- **Per-day form.** J_d = Σ_r w_r·a_r,d / Σ_{rows with units on d} w_r, where a_r,d is the mean of row r's items on day d. J_d is used only as the §4.7 selector (§B3) and is reported.

### B1.7 Why these numbers (data-free)

- **Caps** = 3 × the row's gate tolerance: duration 30 → 90 min; Q_dis 0.05 → 0.15; P5c 0.05 → 0.15; extent ±1 → 3 stations; P1a 0.10 → 0.30; P1b 0.20 → 0.60.
- **Hinges** ramp from the gate threshold to 3 × that threshold.
- **Onset cap** 90 min = P4's score for an unmatched episode = the match window. The **taper** starts at 45 min, half of it.
- **P1c^h** runs from the N2 null (0) to the N1 null (1).
  - On days with N1⁻ᵈ − N2⁻ᵈ ≥ 0.02 a never-congesting plant scores about 1.
  - On other days the row does not fully penalise it; it scores 0 if N2 does worse than N1 that day.
  - P1c^h references N2 only, so on those days it does not guard the gate's N1 criterion.
  - The per-day N1⁻ᵈ − N2⁻ᵈ and the counts of days < 0.02 and < 0 are committed with the facts before the first J5 evaluation (§B1.1). The 0.02 floor is a lab convention.
- **Shaping constants** are lab conventions: ε = 0.5, the 0.5/0.5 split, G = 40 mph (the event threshold) and the ±60-min window (the overlap tolerance). ε and G were changed during synthetic design iterations (disclosed, §B13 item 6). h's cell set changed in rev1 by reasoning (§B1.4).
- **Equal weights** are the least-informed allocation for a gate that is a conjunction of rows. ω_k is set by §B1.5.
- No value was set from real-day model output.
- **Sensitivities** are report-only. They re-score the 8 restarts' best points with the caps at ×2/3 and ×4/3, the taper off, ε = 0 and ε = 1, and equal weights without parity. They are never used to select a plant.

### B1.8 Which gate rows J5 touches

| Status | Rows |
|---|---|
| Targeted (statistic fitted) | P3-k, P8(iii)-2 on real-B2-inactive days, P4-k, P5a-k, P5c, P7a-k, P7b, P7c |
| Guarded (penalised only near or beyond the threshold) | P1a, P1b, P1c; P8(ii); P8(i) at pairs sharing no station with a real-active pair; P8(iii) on hit days (the gate's P3 agreement: any overlap); relocation at c = 1 (rule (iv)) |
| Steered, not scored or enforced (rev2) | P11-k: J5 credits only J5-backed episodes and charges unbacked ones as misses or extras, but a credited day can still be P11-unbacked (§B1.2); gated at the freeze (§B13 item 9 (m)) |
| Indirectly targeted (bounded or largely determined by fitted rows) | P6-k (P3-k/X-k occurrence regrouped by demand half; \|M_h − R_h\| ≤ the P3-k disagreements in the half); P2 (largely P3/P4/P8g; onset order only); P6s-k and P10a/b-k (F̂ is fitted to calibration-day occurrence, with J_d as the selector) |
| Untargeted (independent of J5's fit) | N0 (with §B4), N0s, P5b-k, P9, P8s; P8(i) at pairs sharing a station with a real-active pair; P8(iii) on miss days (charged only as a P3 miss); P3-1 and P8(iii)-1 on real-B1-inactive days (no calibration-day set) |

- **Gate unchanged:** every v3 §5.3 row, threshold, minimum and Bonferroni level, plus v4's P11-k, on the same 97 validation days.
- **v3 §0.4 kept:** the drop is not a term of J5 (W6).
- **What a PASS certifies** (amends v3 §0.2). Every result states all of this:
  - out-of-sample reproduction, on 97 days, of the event statistics fitted on 22 days, plus the guarded, indirectly targeted and untargeted rows;
  - fitted on 22 Wednesdays; validated on 97 days, at least 73 of them Tuesdays or Thursdays (computed from v3 §3.1's ≤ 24 validation Wednesdays and n_val = 97). R12 applies. v3 §0.2's "replayed 2023 Wednesday inflows" reads "replayed 2023 Tuesday–Thursday inflows";
  - the validation days are not data-blind (§B13 item 5); the plant was selected after 3 attempts;
  - queue speed and density are certified only through P1c (vs N1/N2). Replay delay is constrained through discharge, onset and duration.

## B2. Optimiser (v3 §4.4 and v4 §A3, §A5 unchanged except J and seeds)

- pycma 4.5.0, n = 17 in v4 §A5 order, in the normalised space [0, 1]^17 (log scale for τ, ν, κ).
- σ0 = 0.25, λ = 12, **8 restarts on seeds 7,192,010–017**, 4,000 evaluations each.
- x0 ~ U[0.25, 0.75]^17 per seed; tolerance stops disabled; A3 checked before simulation, with the graded penalty.
- **Continuation unchanged:** if the best restart improved by > 1 % over its last 20 % of evaluations, every restart continues once to 8,000. With a discrete J5 this is expected to trigger, and it is budgeted (§B12).
- The nominal plant is the restart with the lowest J5.
- Bounds unchanged and **none widened**; T = 0.75 s.
- `simulate()` records the bin-mean ρ and the effective ρ_cr of **cells 25–39** in every evaluation (rev1: 35–39 added for P8g's relocation clause), as §B1.2, §B1.3 and §B1.4 need.
- **Reported per restart:**
  - J5 and its rows;
  - inadmissible counts (A3, clipping);
  - the share of evaluations with ≥ 1 creditable model B1 episode;
  - flat generations;
  - bound-active parameters;
  - at the best point: the backing-cell ρ_i/ρ̄_cr,i distribution, the P11-backed-but-not-creditable share and the days with a creditable hit that P11-k counts as unbacked (§B1.2); the number of calibration days with relocation (a) or (b) at c = 1, and at (c1, c2) = (1.20, 1.00) (rev2; one extra run per calibration day; report-only, the freeze grid decides c2\*); the medians of r̂ − r (P5b) and Ŝ1 − S1 (P9) on heavy matched days.

## B3. Capacity factors (v3 §4.7, v4 §A1 and D4.10 unchanged except the selector)

**Not in the fit.** Stage 1 fits the plant at c1 = c2 = 1.
- v3 §4.7 re-centres F̂ on its median, so c = 1 is the median gate day.
- "J5's capped per-day items make the c = 1 fit a robust central fit across the 22 days" is **an inference, untested**. Stage 1 (misses allowed at a cost) and the selector (C_d requires every real-active overlap) are different criteria, so the KM median m_k need not be near 1.

**After the freeze**, v3 §4.7 runs unchanged on the frozen plant:
- the 41 × 41 grid over 0.80–1.20, and c2\*;
- relocation (a) (with D4.10) and (b);
- C_d from E_k, O_k and Z_d, with exact and right-censored components;
- Kaplan–Meier marginals, joint draws by day, re-centring and clipping;
- rules (i)–(iv), the Tobit substitute F̂_T, and v4 §A6 (7)(b).

**One change.** The within-C_d selector L_d = NRMSE_v(d, S_c,d) is replaced by J_d(c1, c2) (§B1.6). Ties are broken as before: nearest to (1, 1), then the smaller c1. Reason: L_d is the per-bin statistic that carries the double penalty. Disclosed.

**O_k,d unchanged.** Any overlapping model episode counts, as in the gate's P3 and in the stochastic rows (W12).
- J_d charges a non-creditable overlap as a miss, so within C_d a creditable pair is usually preferred. This is not guaranteed: P7b, P7c, P8g on hit days, the realism rows and the hinges can outweigh the P3 saving (§B1.6). So an exact ĉ_k,d can rest on an unbacked episode even where C_d holds a creditable pair (rev2).
- Reported: the backing of each exact ĉ_k,d (v4 §A13 item 7); the number of exact ĉ_k,d whose overlap is non-creditable; the per-draw unbacked share next to P6s and P10 (v4 §A12).

**Also reported in the freeze record (rev1; report-only):**
- the share of exact ĉ_k equal to 1.00, and the signed re-centring factor 1/m_k per k, next to m_k;
- **c1-inert days** (rev2): calibration days on which, at every c2 ∈ G₂, E_1,d and O_1,d are the same at every c1 ∈ G, and no cell of 28–31 is congested in any P_1 qualifying bin at any grid point (cells 25–39 are recorded, §B2). On such days c1 acts on cells that hold no B1 queue. J_d is not used: c1 scales ρ_cr in cells 28–31, which moves V(ρ) at every density, so J_d's continuous terms differ at every c1;
- **upper-half c1-inert days** (rev2): calibration days on which, at c2 = 1, E_1,d and O_1,d are the same at every c1 ∈ [1.00, 1.20]. This is the signature of a queue headed upstream of B1 (the §B1.2 residual), but a B1 queue that persists at every c1 shows it too; the count cannot tell them apart.

**Reading of D4.13's "with the random capacity factors" (W2).** The stochastic plant keeps c1 and c2, drawn from F̂ (or F̂_T), for N0s, P8s, P6s, P10 and the later gate. v3 §7 R3 is unchanged.

**Rejected alternatives** (recorded, so no variant is hidden):
- (a) σ1 and σ2 fitted inside CMA-ES with K = 4 common-random-number draws and fair scores (design "v5-S"):
  - it takes 4 × the work per evaluation. On synthetic inputs, 32 concurrent processes gave no more total throughput than 8, and 16 gave ≈ 1.3–1.4 × (design-review timings);
  - estimated cost: 26–34 h for the base fit, 39–51 h with the continuation. The process layout behind this estimate is not recorded. A review recomputation at 16 processes gives ≈ 3 × the base: ≈ 18–20 h for the base fit, ≈ 37–40 h with the continuation;
  - cost is not the only reason: it would also retire rules (i)–(iv), the rules that stopped v4, and amend R3(a).
- (b) Per-day c1, c2 profiled inside each evaluation: at least 25 × the compute, and the per-day factors would absorb timing error.
- (c) A post-freeze parametric spread fitted by fair scores, in place of KM: it would substitute for the rules that stopped v4, which makes it a rescue.

## B4. Step-halving (amends v4 §A2 "Step-halving"; gated as part of N0)

Compare T = 0.75 s with T/2 = 0.375 s on the 22 calibration days, at the frozen plant. **PASS iff all three hold** (test 37):
1. |ΔJ5|/J5 ≤ 0.05;
2. |ΔJ_v4|/J_v4 ≤ 0.05, where J_v4 is the v3 §4.3 objective computed at both steps;
3. the P_1 and P_2 model-episode day sets are identical (no tolerance).

- Disclosed: N0's statistic is now evaluated on a new J; keeping the v4-form J makes the check no weaker than v4's.
- v4's report-only margins and T/4 check are kept. They are reported before the §B4 verdict is recorded and cannot change it.
- The flip risk under J5 is expected to be higher than in v4 (§B13 item 9 (e)).

## B5. In-sample screen (new; stop-only, before the look)

**When:** after P11-k at the freeze, before the capacity grid.

**What:** every deterministic gate row, run with the gate's code on the 22 calibration days at c = 1:
- rows: N0 clipping, P1a, P1b, P1c, P2, P3-k, P4-k, P5a-k, P5b-k, P5c, P6-k, P7a-k, P7b, P7c, P8, P9 and P11-k;
- the §5.3 thresholds, and the §5.2 model-side minima at the calibration n;
- the P8 tolerance max(2, ⌈0.10·22⌉) = 3;
- **P5b(ii) uses F8's calibration-day floor Lc_k** (the lower limit of the CI of the real median r on calibration heavy days; v3 R4(b)), not F11's validation floor L_r,k (rev1). The screen reads no F11 field;
- P9 reads its replayed exit flows from `metanet_v5/calib_screen_data.npz` (§B8 step 4);
- leave-one-day-out P1c nulls;
- bootstrap seed 7,192,099.

A row whose real-data minimum (§5.2) is not met on the calibration days is reported, not screened.

**Consequence:**
- If any screened row fails, the route STOPs at the freeze and the track goes to E. The 97 days stay unlooked.
- A screen PASS supports nothing: the statistics are in-sample, and most of them were fitted.
- Stochastic rows are not screened (W8).

**False-STOP risk (disclosed).** The screen's false-STOP rate, for a plant that would pass at the gate's n = 97, is not computed. At n = 22 (and about 9 B2 heavy days) the statistics are noisier than at the gate. The risk is highest for the CI-based P1c-vs-N1 criterion, for the B2 medians, and for the untargeted rows (P5b, P9), which get no in-sample advantage.

**Reported alongside (report-only; cannot change the verdict):**
- each guarded row's in-sample margin to its threshold, with its CI (P1a, P1b, P1c, P8);
- per calibration day, the head cell of each model P_1 and P_2 episode: the most downstream cell of the contiguous congested run that contains cell 26 (P_1) or cell 33 (P_2), modal over the episode's qualifying bins, "none" if no run; and the count of days whose P_1 head lies outside cells 28–31. In METANET's acceleration zone this cell can lie one or two cells downstream of the true head (D4.10); the report says so. Days whose reported head is B_k's first cell (28 for P_1, 33 for P_2) are flagged "residual not excluded": the §B1.2 residual (true head at 26 or 27, or at 32) reports exactly there (rev2);
- the excess vehicle-hours ratio (v3 §5.5) and the median in-episode v_u error.

## B6. Ensemble (amends v3 §4.6 and the v4 §A12 row "Ensemble candidate")

- **Candidates:** restarts with J5 ≤ 1.02·J5_best, taken farthest first in normalised (τ, ν, κ, δ_m, φ).
- **Admissibility, on calibration days only.** Each candidate must pass its own:
  1. step-halving (§B4);
  2. P11-k;
  3. in-sample screen (§B5);
  4. §4.7 check: F̂ estimable, or F̂_T usable (§B3).
- **Grids:** only the first 2 candidates that pass checks 1–3 get a capacity grid; no further grid is run, which bounds the compute.
- **Members** = the candidates that pass checks 1–4 (at most 2). The freeze record holds them in a separate `members` list, committed **before the look**. The other candidates stay recorded as candidates only.
- **On validation:** each member runs the gate once. A member that fails is reported and dropped from R5, and is **never replaced**. The gate refuses any other seed (§B8).
- **Members never decide the route.** A member's gate result only keeps or drops that member (§B11.1).

## B7. Pre-launch premise check (new; report-only, with one blocking anchor)

**When:** after the facts commit and after the §B12 budget notice is settled, before the first CMA-ES evaluation. No budget change follows it.

**Plants:**
- the v4 nominal plant;
- the three D4.12 diagnostic plants: the v4 nominal with only ρ_cr,G3 changed, to Q/(v_f,G3·e^(−1/a_G3)) for Q ∈ {2,400, 2,100, 1,900} veh/h/lane, at the **full-precision** frozen v4 parameters. These are ≈ 31.70, 27.74 and 25.10 veh/km/lane (review recomputation from `metanet_v4_calibration.json`); the full-precision values are committed in the facts (§B1.1). The draft's 31.69/27.73/25.09 came from rounded parameters. Every other parameter stays at the v4 nominal.

**Run:** the 22 calibration days at T = 0.75 s.

**Reproducibility anchor (blocks the launch).** J_v4 at the v4 nominal must equal the committed 0.17801580823665977 (`metanet_v4_calibration.json`) to a relative 1e-9. A mismatch is a code deviation. It blocks the CMA-ES launch until fixed under §B11.2; both values are logged.

**D4.12 comparison (report-only).** J_v4 at the three diagnostic plants is compared with the ledgered 0.187, 0.224 and 0.455.
- The diagnostic ran from uncommitted code (ledger row `capacity_forcing_diagnostic`, commit `a2cfc00+dirty`), and only 3 decimals were kept. Whether it used exact or rounded ρ_cr,G3 is unknown.
- |ΔJ_v4| ≤ 0.0015 is recorded as consistent. A larger difference is logged and investigated on both sides. It is not by itself a v5 code deviation.

**Reported:** J5 and its rows for all 4 plants, sent to the author. **Apart from the anchor, the run proceeds regardless.**

**Limits:**
- It cannot change J5, any weight or threshold, or the route.
- A code deviation it reveals is fixed under §B11.2.
- Any other change would be a new version, i.e. attempt 4, which D4.13 excludes; it therefore leads to E.
- An author abort after the check is recorded as "abandoned after the premise check" and leads to E (§B11.1); it counts as attempt 3.

## B8. Order of work, single look, paths

1. **Before the protocol commit** (status 2026-10-08, D4.14: every item below done, in the protocol commit):
   - commit the sha256 manifest of `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v4/` (done: `docs/lab/day_pattern/metanet_v4_raw_manifest.sha256`, 180 files);
   - set tag `metanet-v4-stop` at `037d717` (done; local tag);
   - the untracked synthetic design files in the repo root (`raw_*.pkl`, `scan_*.pkl`, `truth_c1.pkl`) were moved out of the repo to the session scratchpad on 2026-10-07 (done);
   - archive the design scripts, logs and JSON outputs from the session scratchpad under `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v5_design/` (the synthetic pickles are listed there with sha256 and size), and commit a sha256 manifest of that directory (§B13 item 6) (done, as far as recoverable after the 2026-10-08 reboot: §B13 item 6; manifest `docs/lab/day_pattern/metanet_v5_design_manifest.sha256`);
   - in the same directory and manifest, under `review/`: the review round-1 scripts and inputs (scratchpad `v5review/`, including `cal_counts.json`), the findings file `v5review_rows.json` and the check-round issues file `v5_rev1_check_issues.json`. Every "review computation" and every skeptic verdict cited in this protocol rests on them (rev2). A file that no longer exists is recorded as missing;
   - commit a sha256 manifest of the Mayfly cache files for the 22 calibration days (§B1.1) (done: `docs/lab/day_pattern/metanet_v5_mayfly_calibration_manifest.json`: per day, the file count and the sha256 of its sorted file-hash lines; the full 38,079-line list, 4 MB, is in the design archive and its sha256 is in the JSON);
   - the realism-row provenance: a dated D4.13 note, or the rows stand as a lab choice under W3 (§B1.3) (done: dated note in D4.14);
   - the D4.12 capacity-forcing diagnostic script: committed as found if it still exists; otherwise its absence is recorded (§B7) (done: it ran as an inline heredoc, never a file; recovered verbatim from the session transcript as `docs/lab/day_pattern/d412_capacity_forcing_diagnostic_recovered.py`);
   - show the author §B13 item 9 (known failure paths) with W2 and W11 (done 2026-10-08).
2. Answer W1–W13; commit the protocol; add the decision-log entry.
3. **Code and unit tests (§B10):** this includes the gate refactor with its regression test. Then synthetic timing (§B12; the 24-h notice is settled here), and the adversarial code-review checkpoint (CLAUDE.md phase table). The checkpoint's exact procedure (prompt or checklist, reviewer set, effort, one pass) and the audit module list are committed with its record and named in its ledger row; both §B11.2 audits reuse them unchanged (rev2).
4. **Facts:** commit `metanet_v5_precal_facts.json` (§B1.1).
   - `calib_data.npz` is rebuilt into `metanet_v5/` and must equal v4's array for array.
   - `calib_screen_data.npz` is built into `metanet_v5/` by `build_data(cal_days, exit_flows=True)` for the screen's P9; the arrays it shares with `calib_data.npz` must be equal bit for bit.
   - The facts recomputed in v4 (v4 §A6) are reused read-only from `metanet_v4_precal_facts.json`; v3's reused facts from the v3 file. Both git blob hashes are recorded in the v5 facts.
5. Premise check (§B7).
6. **CMA-ES (§B2), then the freeze stops in this order:**
   1. A3 "no admissible restart" (v4 §A3 (d));
   2. step-halving (§B4);
   3. P11-k (v4 §A12);
   4. in-sample screen (§B5);
   5. §4.7 and (7)(b) (§B3).

   **Stops are evaluated in order.** The first failure sets the route label "STOP (<stop>)" and E follows, after the freeze audit (below). Later stops, candidate checks and grids are not run and are recorded as "not run (route stopped at <stop>)" (`freeze --partial`).

   If no stop fires: the **ensemble step** (§B6; never a stop).

   **In either branch** (rev2): commit `metanet_v5_calibration.json` with stage "freeze" and the route label (`--partial` on a STOP), run the freeze audit once (§B11.2) and commit its record. Only then record E or continue to step 7.
7. **Gate on the 97 validation days, single look:** the nominal plant, then each member: deterministic rows and P11-k, then stochastic rows. Commit the outcome, then run the gate audit once (§B11.2) and commit its record, PASS or FAIL.
8. **Report-only:** profiles (only after a PASS; §B12) and sensitivities (§B1.7).

**Single look.** v4 §A6 (1)–(6) and (7)(b) apply, with v5 names. v4 stopped at (7)(b), so the 97 days are unlooked and v5's gate is GO-capable. Any stop before step 7 leaves them unlooked; v4 §A6 (3) is extended to the §B5 stop and to "abandoned after the premise check".

**Paths:**
- raw output: `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v5/`;
- design archive: `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v5_design/`;
- records: `docs/lab/day_pattern/metanet_v5_calibration.{json,md}`;
- facts: `docs/lab/day_pattern/metanet_v5_precal_facts.json`.

Every v3 and v4 path is read-only, including the v4 records, `demand_check.*` and the `metanet_v4/` raw directory. **The v3 and v4 manifests are both re-verified after every v5 batch.**

**Gate guard (test 36).**
- The gate jobs refuse to run unless the v5 freeze record is tracked, unchanged against HEAD, names protocol v5, has stage "freeze", and has a route not starting with STOP; and unless the freeze-audit record (§B11.2) is committed (rev2).
- **First freeze record only** (rev2): the guard accepts only the first committed v5 freeze record with stage "freeze", unless a §B11.2 fix record names a later one.
- The freeze record holds `nominal` and a separate `members` list (≤ 2, §B6). The gate refuses any seed other than these.
- **Start record** (rev2): before a gate job reads any validation-day input, it writes, per seed, a ledger row and a lock file in `metanet_v5/` holding the code commit hash and the freeze record's blob hash. A seed with a start record is refused unless both hashes are unchanged (a plain re-run after a crash, a kill or a scope stop) or a §B11.2 fix re-run is recorded for that seed (the fix commit and its failing-before test named). This covers runs that ended without a committed outcome. The outputs of an interrupted run are kept in `metanet_v5/` and listed in the ledger.

## B9. Seeds (replaces v4 §A8; block 7,192,000–7,192,999, W1)

| Seeds | Use |
|---|---|
| 7,192,010–017 | base CMA-ES restarts (8) |
| 7,192,018–025 | reserved, unused (v4's F1 slot; there is no F1, §B11) |
| 7,192,026–097 | profiles (report-only, after a PASS): seed = 7,192,026 + 9p + j, parameters in the v3 order, j = 0…8 |
| 7,192,098 | bootstrap of the §4.7 correlations (calibration days) |
| 7,192,099 | bootstrap of the in-sample screen CIs (calibration days) |
| 7,192,300 | bootstrap of the gate statistics (validation-role range) |
| 7,192,301 | joint capacity-factor draws for the stochastic rows (nominal plant and members) |
| all others | unused |

- The layout follows roadmap §10: 000–009 throw-away calibration, 010–099 plant checks, 300–499 validation.
- Ledger check (2026-10-07): no row mentions 7192.
- No 7,190 or 7,191 seed is used for a new draw. F8 (7,190,094) and F11 (7,190,097) are reused as committed. Test 30 runs the tag's code and the refactored code at the tag's bootstrap seed 7,191,300 on synthetic inputs only: a regression check, not a new draw.
- Cold starts only. A re-run after a bug fix reuses the original seeds (§B11.2).
- The design sessions used non-protocol synthetic seeds: numpy 0, 1, 777, 12345, 1000 + r and 5000 + r; pycma 1–3. They get report-only ledger rows at the protocol commit.

## B10. Unit tests (added to v4 §A10; synthetic inputs only)

| Test | Checks |
|---|---|
| 24 | Zero cost: J5 = 0 when the model equals the real series (through the inverse observation operator), with a synthetic cell state ρ_i = 1.1·ρ̄_cr,i in cells 26–28 (P_1) or cell 33 (P_2) on every qualifying bin. Companion case with no backing: J5 returns the miss values (P3-k = 1 + ε with s = 1; P4-k, P5a-k, P7a-k = 1) |
| 25 | Miss dominance (§B1.6) on ≥ 3,000 randomized outcomes on synthetic days. The generator must include two-bottleneck days (both real-active, censored B1, heavy at both, multi-episode days) with model episodes at both pairs. Asserts claim 1 per (k, d) with the other bottleneck's episodes fixed (P3-k, P4-k, P5a-k, P7a-k, P5c) and claim 2 per day (every target item at a real-active bottleneck, plus P5c, P7b, P7c). **Item-level convention (rev2):** the reference changes only the P_1/P_2-dependent items (P3-k, X-k, P4-k, P5a-k, P5c, P7a-k, P7b, P7c, P8g (ii)); P8g (i)/(iii), the realism and the hinge items keep the outcome's values. Asserts J5(out) − J5(ref) ≤ Σ over the rows §B1.6 lists of w_r·max(0, ΔA_r)/Σ_r w_r. Also compares each outcome with the same day without its P_k episodes at a drawn s_0 ∈ [0, 1]: every increase is on a listed row, P3-k through s included. Reports the violation share and the largest P7b + P7c increase |
| 26 | Parity: on a synthetic real-B2-inactive day built so that the extra touches no other row (not heavy at B1; the extra lies outside F_d and more than 30 + 60 min from any model or real P_1 episode; the P1 hinges are unchanged), one extra P_2 episode raises Σ over {P3-2, X-2} of w_r·ΔA_r by U_2, and J5 by U_2/Σ_r w_r (both to within 1e-12); the prep weights match §B1.5 |
| 27 | Items are continuous in Δonset across 45 and 90 min, to within one 5-min-bin increment |
| 28 | Shaping: s ∈ [0, 1]; its contribution is 0 once every real-active (k, d) has a creditable overlap; s = 1 on a miss with an overlapping (non-creditable) episode, also when a backed, creditable episode that overlaps nothing exists elsewhere on the day (P3-k stays 1 + ε; rev2); s = 1 when a non-creditable episode has a bin in a g window without overlapping; a non-creditable episode with no bin in any g window leaves s to g and h; an unbacked episode earns no credit; a masked bin gives margin −∞ (no NaN reaches s); v_u = 40.0 exactly gives margin 0 while the event rule fails; a multi-episode day uses per-episode windows (no spanning window); a censored B1 episode uses [onset − 60, t_c]; h ranges over every bin of the g windows, on §B1.2's cells |
| 29 | Real anchoring: qualifying sets (P5c's `both_q` included), denominators, ω_k, F_d, the nulls and the per-day N1⁻ᵈ − N2⁻ᵈ are unchanged under arbitrary model output |
| 30 | Gate refactor. (a) The per-day item functions reproduce the row outputs of the gate at tag `metanet-v4-stop` bit for bit, on ≥ 3 synthetic validation sets, both codes at the tag's bootstrap seed 7,191,300. (b) On matched, creditable items J5's uncapped values equal the gate statistics: \|Δonset\| → P4, D_i → P5a, \|Δdur\| → P7a. On the rows that use all model episodes they equal the gate's: D_i → P5c, index error ≤ 1 ⇔ gate P7b hit, \|Δdur_sys\| → P7c, per-day spurious and extra flags → P8; P8g (ii) = 1 exactly on the real-B_k-active days where the gate's P3 agrees and the gate's P8(iii) flags B_k, creditable or not (rev2). (c) Unmatched and non-creditable items score 1 in J5 (P3-k: 1 + ε·s), while the gate gives \|0 − dur_r\| (P7a, P7c) or leaves the day out (P5a, P5c); the gate's P3 and P4 still use any overlap or match |
| 31 | Hinges are 0 inside the pass region and linear up to 3 × the threshold; the P1c nulls leave out day d; the s_d floor applies; P8g's relocation clause is 0 for a non-relocating plant |
| 32 | Step-halving returns J5, J_v4 and both day sets at T and at T/2 |
| 33 | The J5 evaluator (P8g included), the CMA-ES driver, the §4.7 grid and its selector J_d, ensemble selection, the screen and the premise check open no validation-day input: `val_data.npz`, the raw validation-date files and the per-day validation facts. From the committed facts they read no F11 field (key-access audit; rev2 widened the scope: the freeze job at tag `metanet-v4-stop` loads the whole v3 facts file, F11 included, to read F8). (The draft's "as test 22" was wrong: v4 test 22 covers writes, not reads) |
| 34 | The screen applies the gate thresholds and the minima at the calibration n, P5b(ii) on F8's Lc_k, P9 from `calib_screen_data.npz`, and returns STOP for a synthetic failing plant |
| 35 | J5 refuses to run if the facts hash differs; J_d equals the per-day form; the §4.7 selector uses J_d with the old tie rule |
| 36 (new) | Gate guard: refuses a recorded non-member candidate, a STOP route, a missing freeze-audit record, a freeze record other than the first committed one (unless a §B11.2 fix record names it), and a seed with a start record when the code or freeze hash changed (unless a §B11.2 fix re-run is recorded), including a seed whose run crashed or was killed before its outcome was committed; accepts a plain re-run at unchanged hashes, the nominal and the members (rev2) |
| 37 (new) | §B4 conjunction: a one-day set flip with ΔJ5 = 0 gives FAIL; \|ΔJ_v4\|/J_v4 > 0.05 alone gives FAIL; all three met gives PASS |
| 38 (new) | J5 scoring: an A3 violator is not simulated and scores 10 + Σ shortfall; clipping > 1 % or a non-finite value scores 10; every admissible J5 ≤ 1 + ε; non-creditable extras are charged in P3-k (real-inactive days), X-2 and P8g, and P8g (ii) charges an extra on a day whose only overlap is non-creditable (rev2) |
| 39 (new) | Freeze route labels: each stop yields its exact label "STOP (<stop>)"; later stops are recorded "not run (route stopped at <stop>)"; the ensemble step is never a stop |
| 40 (new) | Creditability (§B1.2): a 4 → 3-drop queue (head at 23/24) whose acceleration zone makes cells 25–26 over-critical → non-creditable; cell 27 alone → not J5-backed (still P11-backed); an H1 queue spilling back to cell 25 → creditable; P_2: cell 34 alone → not J5-backed, cell 33 → backed; an episode exactly 50 % J5-backed → creditable; a backed extra does not make an unbacked overlapping episode creditable, and P3-k stays 1 + ε (rev2); an unbacked extra does not strip a backed P3-k hit (it can take a P4/P5a/P7a match by nearer onset, as in the gate, and that item then scores 1), while P11-k counts that day as unbacked when the pooled share falls below 50 % (rev2); the disclosed residuals are creditable: head at cell 26 with the zone over 27–28, head at cell 27 with a one-cell zone over 28, and (P_2) head at cell 32 with a one-cell zone over 33 (rev2); v4 test 21 still passes (gated P11-k unchanged) |
| 41 (new) | P8g relocation: relocation (a) (D4.10 form) or (b) at c = 1 sets P8g = 1, including (b) on a real-B2-active day, where the spurious rule exempts the pair; cells 35–39 are recorded in every evaluation |
| 22 (extended) | No v5 job writes to a v3 or v4 path |

## B11. Time box and outcomes (D4.13; amends v3 §0.3 and §6, and v4 §A6 (2))

### B11.1 Time box

**No F1.** v3 §6.1 does not apply: F1 would be a second optimisation judged on the same days, i.e. a rescue.

**Route stops.** Each one leads to E:
- no admissible restart;
- a step-halving FAIL;
- a P11-k FAIL at the freeze;
- a STOP from the in-sample screen;
- the freeze stop (7)(b);
- "abandoned after the premise check" (§B7);
- any deterministic row or P11-k failing at the gate, on the nominal plant;
- any stochastic row failing under F̂ or F̂_T, on the nominal plant.

**The nominal plant alone decides.** Route stops and outcomes are judged on the nominal plant only. A member's gate result keeps or drops that member (§B6). It never substitutes for the nominal.

v3's "PASS, deterministic-only" is recorded under its v3 label but counts as a v5 FAIL for the route. Only positive DRL results count, and that plant could only KILL.

**GO-capable plant:** needs PASS or "PASS, substitute spread" (v3 §0.3, unchanged).

**After E:**
- no further METANET version, no refit, no threshold change. A §B11.2 fix is not a refit;
- resuming the track needs a new dated author decision. Any later plant is attempt ≥ 4 and discloses the v3–v5 calibration-day results as design inputs (D4.4 style);
- a pre-look stop that a §B11.2 fix reverses is not a resumption: the route continues as attempt 3 on the original seeds, disclosed, and the author is told before the next step (§B11.2 item 4; rev2);
- a stop before the look leaves the 97 days unlooked for any later plant (v4 §A6 (3)). After a gate FAIL, any later plant judged on them is a "second look" and can only KILL.

### B11.2 Post-result fixes (new in rev1; rewritten in rev2 on the lead's binding resolutions; W13)

**1. Rule.** v3 §6.3's fix rule applies, extended in scope and timing:
- **Scope:** any deviation of the committed code from any committed protocol text: v3, v4, the v4 addendum and v5 (rev2: no partial list). Code may change only to match the text. A change to any text, threshold or criterion stays a new protocol version (v3 §6.3); D4.13 excludes it, so it leads to E.
- **Deviation (one reading only).** A deviation exists only where the committed text has one reading and the code contradicts it. Where the text admits more than one reading, the reading of the code that passed the pre-launch code-review checkpoint (§B8 step 3) stands, before and after any result. The ambiguity is logged and disclosed. It is never "fixed" after a result; only a later protocol can resolve it.
- **Record.** Each fix record quotes the committed text and says why the old code contradicts its only reading. It is committed with the test below, before the re-run.
- **Test:** each fix comes with a unit test, committed with the fix, that fails on the code that produced the result and passes after.
- **When:** from the premise check (§B7) on: before and after the look, and before and after E. This includes fixes after a pre-look stop, which v3 §6.3 did not cover.
- **Not a refit.** A fix and its re-run are not a "refit" or a "further version" under §B11.1. They never reset the attempt count (§B13 item 1).
- **Re-run (v3 §6.3 as written):** calibration and the gate are re-run in full on the original seeds (§B9): CMA-ES, the freeze stops, the screen, the ensemble step and the grids, then the gate if the route reaches it. Nothing is re-run selectively. The premise check is repeated only to confirm a fix to its own anchor. Both outcomes are logged (CLAUDE.md).

**2. Order.** The original outcome (premise anchor, freeze record or gate outcome) is committed before any fix. Each audit's findings are committed before any fix they lead to. Every later result cites both outcomes.

**3. Audits (pre-registered; one pass each, whatever the outcome).**
- **Procedure pinned.** Each audit is an adversarial code review that runs the checkpoint procedure committed at §B8 step 3 (prompt or checklist, reviewer set, effort) once, unchanged.
- **Freeze audit:** once, after the freeze record is committed, whatever its route. Its record is committed before the gate runs (gate guard, §B8).
- **Gate audit:** exactly once, after the gate outcome is committed, PASS or FAIL.
- **Scope:** the J5, freeze, screen and gate path against every committed text: `vsl_lab/jobs/metanet_{calibrate,postcal,freeze,gate}.py`, the new J5/item-function and screen code, and every vsl_lab module they import, directly or indirectly. The list is fixed by name at §B8 step 3. Today it includes `vsl_lab/data/metanet_{events,facts,inputs}.py` (`event_pairs`: the EA-2 corridor rule; `model_inputs`, `fit_targets`), `vsl_lab/data/corridor_analysis.py` (`episodes`: the 5-of-7 rule and the 30-min merge), `vsl_lab/data/mndot.py` and `vsl_lab/plants/metanet.py`.

**4. Which outcome counts (W13, answered 2026-10-08: strict).**
- **Before the look:** any fix, found by the freeze audit or otherwise, follows item 1. A stop that a fix reverses lets the route continue as attempt 3 on the original seeds. It is not a resumption after E (§B11.1). Disclosed.
- **After the look (W13, strict; author 2026-10-08):** every bug, found by the gate audit or otherwise, at any time, in any session, is still fixed, re-run and logged (item 1). A PASS → FAIL counts. A FAIL → PASS is labelled **"second look on the same validation days"** and can only KILL. A fix that leaves the outcome unchanged, or changes only the frozen nominal or the `members` list without turning a FAIL into a PASS, carries the label **"after post-result fix"** and both outcomes in every result.
- In every case the author is told before the next step.
- **Not adopted (W13 proposed default):** a fix from the gate audit could have turned a FAIL into a labelled, GO-capable PASS. Rejected by the author because it eases the inherited rule after the validation days are seen (item 5).

**5. Against the inherited rules (disclosed; §B13 item 3).**
- **Before the look** §B11.2 adds the one-reading test, the failing-before test and the full re-run to fixes that v3 §6.3 did not govern (it starts at the first validation evaluation; v4 §A6 (2) says only that such a fix is not a stop). It also lets a fix reverse a pre-look stop, which v4 §A6 (2)–(3) did not provide for.
- **After the look v5 keeps the inherited direction** (W13 strict): under v3 §6.3's last sentence as amended by v4 §A6 (3), a post-look fix outside v3 §2–§3 was a new version, KILL-only on these days. v5 keeps every post-look FAIL → PASS KILL-only, whoever finds the bug; it adds the full re-run and the audit, which can only confirm or lower an outcome after the look.

## B12. Compute (amends v4 §A9)

| Stage | Projection |
|---|---|
| Base fit compute: 8 restarts × 4,000 evaluations, 8 processes | 6.1–6.7 h per restart |
| Guard pauses (observed in v4; not scaled) | 0 to ≈ 3.5 h per CMA-ES batch |
| Base fit wall time (slowest restart) | ≈ 6.7–10.2 h |
| With the continuation to 8,000 | 12.3–13.5 h compute; ≈ 20.4 h with one observed-size pause in each CMA-ES batch |
| Premise check, step-halving, P11-k, screen | < 0.3 h |
| Nominal capacity grid (1,681 grid points × 22 days) | ≈ 0.9 h |
| ≤ 2 ensemble grids, plus their checks | ≤ 2 h |
| Gate: deterministic rows + 200 draws × 97 days, ≤ 3 plants | ≈ 1 h wall time |
| **Route-critical worst case** | **≈ 17.7 h with no pause; ≈ 21 h with one observed-size pause; ≈ 24.6 h with one in each CMA-ES batch** |
| Profiles (report-only; run automatically after a PASS) | + ≈ 10–11.5 h |
| **All stages that can run without a new author decision (v4 §A9)** | **≈ 28–36 h** |

**Basis** (rev1 separates compute from guard pauses):
- v4's measured restart wall times on 8 processes: 5.42–5.74 h for seven restarts. The eighth (7,191,017) took 8.22 h, of which ≈ 3.47 h were guard pauses and ≈ 4.75 h compute. The v4 batch `thermal.csv` logs two emergency pauses of that restart: from 10 s to 12,304 s (≈ 3.42 h) and from 25,152 s to 25,355 s (≈ 203 s) (review; rechecked in the check round);
- cell recording adds 11.6–16 % (two synthetic measurements in the design review, cells 25–35; rev1 records 25–39 and re-measures);
- the event layer, P11 and shaping add 1.3 %;
- so compute per restart = 5.42 × 1.116 × 1.013 to 5.74 × 1.16 × 1.013 h;
- v4's projection for one capacity grid.

**Layout:** one restart per process, 8 processes. On synthetic inputs the design review measured about the same total throughput for 32 concurrent `simulate()` processes as for 8 (≈ 5.7 vs ≈ 5.6 single-process equivalents), and ≈ 7.9 for 16. Grid and member jobs may use up to 16 processes.

**The 24-h notice applies now.** v4 §A9 applies the 24-h rule to all stages that can run without a new author decision. That projection (≈ 28–36 h) exceeds 24 h, so the author is told now (W11), and again with the measured timings before launch. A second observed-size guard pause in a CMA-ES batch takes the route-critical part alone past 24 h. The budget is never cut silently.

**Fix re-runs (rev2).** A §B11.2 re-run repeats calibration and the gate in full, so each one costs about the route-critical time again. Its projection is sent to the author before it launches.

**Every batch:** resource check, v6-idle check, CPU and thermal guard, a ledger row, and its own systemd scope.

## B13. Disclosures (added to v3 §0.5 and v4 §A11)

1. **Plant attempts.** N = 3: METANET v3 (N0 stop), v4 (freeze stop under (7)(b)) and v5. Every result states "plant selected after 3 attempts (listed)". A §B11.2 re-run does not change N.
2. **Post hoc design inputs (D4.4 style).** v5 was designed after seeing:
   - v4's calibration-day fit: G3 capacity 2,700–3,400 veh/h/lane, and 21 of 22 days not reproducible;
   - the D4.12 check and its follow-up diagnostic, in which only ρ_cr,G3 was varied: J went from 0.178 to 0.455, with whole-day NRMSE_q/v of 0.235/0.314 at 1,900.

   The double-penalty diagnosis is an inference supported by synthetic checks. It is not proved on the real plant.
3. **Changes to items v4 froze:**
   - the objective J (v4 §A7);
   - the statistic N0's step-halving check is evaluated on (§B4);
   - the §4.7 selector L_d (§B3);
   - v3 §4.6 admissibility (§B6);
   - F1 dropped, and "deterministic-only" counted as a FAIL (§B11);
   - profiles moved to after the gate;
   - v3 §6.3's fix rule widened in scope and timing (§B11.2). Before the look it tightens fixes v3 §6.3 did not govern (one-reading test, failing-before test, full re-run) and lets a fix reverse a pre-look stop. **After the look nothing is eased** (W13 strict): every post-look FAIL → PASS from a fix is KILL-only, as under v3 §6.3 with v4 §A6 (3) (§B11.2 item 5).

   **Not eased:** every bound, T, A3, P11-k, the event layer; every gate row, threshold and minimum; rules (i)–(iv) and (7)(b); R1–R13, with R2(c) and R4(d) bound by D4.7. v4 §A9's 24-h rule is not narrowed (§B12).
4. **Calibration days are used a third time:** the v3 fit, then the v4 fit with the D4.12 diagnostic, now v5. Every calibration-day result, including the screen and the premise check, is in-sample.
5. **Validation days:** never simulated, but not data-blind. F11 and the per-day real facts are committed, and the Wednesdays were inspected in the v3 reviews.
   - This synthesis read the committed F11 counts: n_val 97, n_A,2 39, n_H,both 38, P8 tolerance 10.
   - One design read the real-episode summaries of the calibration days: onsets 14:15–16:30; B1 active 22/22, B2 9/22.
   - No validation-derived value enters the fit (the J5 evaluator, P8g included, and the CMA-ES driver), the §4.7 grid and its selector J_d, F̂, the ensemble selection, the screen or the premise check (rev1: P5b(ii) uses F8's Lc_k; rev2: test 33's key-access audit covers all of these, since the freeze job loads the whole v3 facts file, F11 included).
6. **Design runs:**
   - all synthetic; no real day was simulated (a spot check of the scripts in review found synthetic truth-plant days only);
   - variants tried, all disclosed: ε ∈ {0, 0.5} (runs `s3_event_0.0_*`, `s3_event_0.5_*`, `s3b_event_0.0_*`, `s3b_event_0.5_*`), with v4-form comparison runs (`s3_v4_0.5_*`); shaping G ∈ {20, 40} mph; the taper off and on (added after a synthetic cliff);
   - three designs were judged: event matching (J_event), transport (J5-UOT) and in-fit σ (v5-S). J5 was chosen with grafts from the others (design synthesis). The outcome of each run is in the archive;
   - parity, the guard rows and the dual step-halving were added in review, by reasoning, not from data. So were rev1's changes (per-episode creditability with the head rule, h's cells, P8g's relocation clause, P5c's set); no synthetic run was repeated for them;
   - the session scratchpad (scripts, logs, JSON outputs, `cal_counts.json`) was wiped by a machine reboot on 2026-10-08, before archiving. The archive (§B8 step 1, committed manifest `metanet_v5_design_manifest.sha256`) therefore holds: every agent transcript of the design panel, the review, the revision and the check round (each holds every command and its output); the scripts rebuilt from them (`recovered/`, including those written by shell heredocs); `recovered/RECOVERY_REPORT.json`, which lists the 52 mentioned paths that could not be rebuilt (outputs of runs, logs); the review findings and check-round issues (`review/`, rebuilt from the workflow journals);
   - one design's scripts wrote synthetic pickles into the repo root (4 × 27,288,750 B `raw_?.pkl`, `scan_?.pkl`, 1,364,538 B `truth_c1.pkl`; untracked). They were moved out of the repo on 2026-10-07, before any commit, and were lost in the 2026-10-08 reboot; no sha256 was taken.
7. **Same statistics in the fit and the test:**
   - the day sets are disjoint and every definition is frozen before the fit, so this is held-out validation;
   - the rows independent of J5's fit are N0/N0s, P5b, P9 and P8s, and P11 in part (§B1.8). P2 and P6 are largely determined by the targeted occurrence rows; P6s and P10 depend on F̂, which is fitted to calibration-day occurrence;
   - the guarded rows lose part of their independence. Their hinges are zero inside the pass region, so the fit may leave them near their thresholds; §B5 reports their in-sample margins.
8. **Literature:** none is cited. "Double penalty" is a forecast-verification term [VERIFY: not read here].
9. **Known failure paths under v5** (replaces the consequences in v4 §A11 item 8; every path ends in E; shown to the author with W2 and W11 before the commit):
   - (a) **F̂ estimability, rule (iii).** About 9 B2-active calibration days against rule (iii)'s 8 exact observations; v3 §4.7 itself predicts a false "not estimable" here for a sound plant. Path: F̂_T, usable only with ≥ 5 exact B2 observations and neither rule (i) nor (iv); otherwise (7)(b) → E.
   - (b) **Rule (i):** more than 20 % of the 22 real-active calibration days (i.e. ≥ 5) not reproducible → (7)(b) → E.
   - (c) **Relocation → rule (iv) → E.** J5 sees relocation only at c1 = c2 = 1 (P8g). Relocation at any grid pair with c2 ≤ 1.00 and c1 ≠ 1 (for example c1 = 1.20 passing more flow to a weak G4) still gives c2\* < 1.00 → rule (iv) → E, and J5 cannot see it; §B2 reports (1.20, 1.00) per restart. Relocation only at c2 > 1.00 truncates G₂ and is not a stop (rev2; v3 §4.7's c2\*).
   - (d) **B2 knife edge.** P3-2 or P8(iii)-2 failing at the screen or at the gate → E. v4 §A11 item 8 (b)–(c)'s "→ F1" reads "→ E (no F1, §B11)".
   - (e) **Step-halving's zero-tolerance day sets.** Under J5 the model has episodes on far more days than under v4 (v4: B1 model-active on 1 day, B2 on none), so the v4 §A11 item 7 flip risk is expected to be higher. This was not measured.
   - (f) **In-sample screen false STOP** (§B5): not computed; highest for the CI-based P1c, the B2 medians and the untargeted rows.
   - (g) **P1c,** rated in the design synthesis as the most likely out-of-sample FAIL; the hinge leaves the fit indifferent below each day's threshold.
   - (h) **Exaggerated drop (inference, untested).** J5 has no drop or overshoot term (W6 default). Parity makes extras on the 13 overloaded real-B2-inactive days expensive while P5a pins discharge, so a deterministic fit can buy occurrence with a larger drop or overshoot → P5b-2 or P9 STOP at the screen, or FAIL at the gate. r̂ − r and Ŝ1 − S1 are reported per restart (§B2).
   - (i) **B1 head outside B1's cells.** Partly closed by §B1.2's head rule. The acceleration-zone residual (head at 26 or 27 for P_1, at 32 for P_2) is not excluded, and no report can confirm it: §B5 flags the days on which it cannot be excluded, and §B3 counts c1-inert and upper-half c1-inert days (rev2).
   - (j) **Bound-active ν and φ in v4:** event agreement may rest on non-physical parameter values.
   - (k) **Calendar transfer:** fitted on 22 Wednesdays; at least 73 of the 97 validation days are Tuesdays or Thursdays.
   - (l) **Implementation:** one bug in an 18-row J5 (the design prototype covered 13 rows) can end the track; §B11.2 governs fixes.
   - (m) **P11-k FAIL at the freeze** (rev2). J5 credit is per episode on cells 26–28 (P_1) or 33 (P_2); P11-k pools a day's episodes over cells 26–31 or 33–34. A J5-optimal plant can still have more than 3 of 22 P11-unbacked days, when unbacked episodes pull a credited day's pooled share below 50 % → stop → E.
10. **J5 credit differs from the gated P11-k** (§B1.2): stricter per bin and on head location (the queue must run from cell 26 into B1 for P_1, or hold cell 33 for P_2); per episode it differs in both directions, so J5 can credit a day that P11-k counts as unbacked. The acceleration-zone residual (heads at 26, 27 or 32) stays creditable. The gated P11-k is unchanged, so no gate row is eased.

## 0.6 Author items for v5 (each answered before the commit)

| # | Item | Proposed default | Alternative |
|---|---|---|---|
| W1 | Seeds | Block 7,192,000–7,192,999 with the §B9 sub-ranges | Reuse the 7,191,1xx tuning range: rejected, because it erodes that range's role |
| W2 | Capacity factors (D4.13's "with the random capacity factors") | Fit at c = 1; v3 §4.7 F̂ unchanged after the freeze, with selector J_d (§B3). Read with §B13 item 9 (a)–(c): rule (iii) may give a false "not estimable" → F̂_T → else E | σ inside CMA-ES (v5-S): ≈ 3–4 × the base fit (layout-dependent, §B3), and it retires the rules that stopped v4 |
| W3 | Objective J5 (§B1: rows, caps, taper, creditability with the head rule, shaping, equal weights; system rows on all model episodes; realism rows as a lab choice unless a dated D4.13 note records them) | As written | The original J_event (P3/P8 max-rule, P2 and one-sided P5b rows), or the J5-UOT transport objective |
| W4 | Occurrence parity ω_2 (§B1.5) | Adopt (exact on P3-2 and X-2; ω_2 ≈ 5.78 expected) | Equal weights (a missed B2 day ≈ 4 × an extra on J5's rows) |
| W5 | Guard rows P1a^h, P1b^h, P1c^h, P8g (with the relocation clause) | Adopt. Note: P1c is the likeliest out-of-sample FAIL, and the hinges let the fit sit near the thresholds (§B13 items 7, 9 (g)) | Leave P1 and P8 to the screen only; or add an onset-registered queue-speed row |
| W6 | Keep v3 §0.4: no drop term; P2, P5b, P6, P9 not targeted | As written; failure path §B13 item 9 (h) disclosed; r̂ − r and Ŝ1 − S1 reported per restart. Keeps P5b and P9 independent of the fit | One-sided guard hinges, zero inside the pass region: P5b^h-k = clip((−0.02 − (r̂_d − r_d))/0.04, 0, 1) and P9^h = clip(((Ŝ1_d − S1_d) − 0.03)/0.06, 0, 1), on real heavy (first-active) days, 0 if unmatched; P5b and P9 then become guarded |
| W7 | Step-halving on both J5 and J_v4 (§B4) | Adopt. The flip risk is expected to be higher than in v4 (not measured; §B13 item 9 (e)) | J5 only |
| W8 | In-sample screen (§B5) | A gated stop, deterministic rows only. Its false-STOP rate is not computed and is higher for P1c and the untargeted rows | Add the stochastic rows; or make it report-only |
| W9 | Premise check (§B7) | Report-only and proceed, except the blocking anchor (J_v4 at the v4 nominal) | Abort-only: abort, leading to E, if the v4 nominal has a lower J5 (is preferred by J5) than all three D4.12 plants |
| W10 | Ensemble (§B6) | Admissibility on calibration days, a `members` list fixed before the look, ≤ 2 grids, no replacement; the gate refuses other seeds; members never decide the route | v3 §4.6 as written |
| W11 | Time box (§B11, §B12) | No F1; "deterministic-only" counts as a FAIL, leading to E; profiles only after a PASS. Route-critical ≈ 18–25 h (no pause to two observed-size pauses); with the automatic post-PASS profiles ≈ 28–36 h, so the v4 §A9 24-h notice applies now | Keep F1 (+≈ 15 h; a rescue) |
| W12 | §4.7: O_k,d requires a creditable overlap | No: §4.7 keeps the gate's P3 occurrence definition (any overlap), which the stochastic rows also use; J_d usually prefers creditable pairs, but not always (§B3, §B1.6); the count of exact ĉ_k,d on non-creditable overlaps is reported | Yes: matches J5's definition of a breakdown; also raises the risk of a stop under rules (i)/(iii) |
| W13 | Post-result fixes (§B11.2). **Answered 2026-10-08: the alternative (strict).** | (proposed, not adopted) Any deviation of the code from any committed text (v3, v4, addendum, v5) is fixed with a failing-before test; where the text has more than one reading, the checkpointed code's reading stands (logged, disclosed). Calibration and the gate are re-run in full on the original seeds; both outcomes in every result. One pinned audit after the freeze record (either route) and exactly one after the gate outcome, PASS or FAIL. Before the look, any fix counts and a reversed stop continues attempt 3, disclosed. After the look, a fix from the gate audit counts, labelled "after post-result fix" (also when only the nominal or members change); outside that audit a PASS → FAIL counts and a FAIL → PASS is "second look on the same validation days", KILL-only. **This eases v3 §6.3/v4 §A6 (3) after the look for gate-audit bugs (§B13 item 3)** | Every post-look FAIL → PASS from a fix is KILL-only, whoever finds the bug: the inherited consequence (a post-look fix outside v3 §2–§3 was a new version, KILL-only on these days) |

---

## Review round 1 log

Severity is shown as reviewer → skeptic. Every finding is listed, notes included. The findings, the review scripts and inputs and the check-round issues are archived under `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v5_design/review/` (§B8 step 1).

| Finding | Verdict | Action |
|---|---|---|
| math-1 | confirmed; must-fix → must-fix | Applied with change. §B1.6 restated as two claims (lead decision 1). Claim 2 excludes P3-k/X-k at a real-inactive bottleneck (skeptic's correction; a literal "all target rows" is false there). The bound is stated for any P_k jam, not only a hit. The "can cost more" list is rewritten. Test 25 rewritten with two-bottleneck days |
| math-2 | confirmed; should-fix → should-fix | Applied. §B1.5: Σ w·A rises by U_k, J5 by U_k/Σw; exact on P3-k/X-k only; other rows listed; "leans towards extras" withdrawn. Test 26 rewritten |
| math-3 | confirmed; should-fix → should-fix | Applied. Per-episode creditability (§B1.2); pooled P11-k unchanged, J5 disclosed as stricter; both directions in test 40 |
| math-4 | partly; should-fix → note | Applied. §B1.4 last sentence replaced; §B1.5: U_k at s = 0, a miss costs up to ε/N(P3-k) more |
| math-5 | confirmed; should-fix → should-fix | Applied. §B1.4: NaN margin −∞, per-episode windows, censored window [onset − 60, t_c], h over the g windows, the v_u = 40 edge; cases in test 28 |
| math-6 | confirmed; should-fix → note | Applied. Zero cost stated with a backed synthetic cell state; test 24 with a no-backing companion |
| math-7 | confirmed; note → should-fix | Applied. Departure line in §B1.3; test 30 split into (a)–(c) |
| math-8 | confirmed; note → note | Applied. §B1.7 reworded; per-day N1⁻ᵈ − N2⁻ᵈ and the counts committed with the facts |
| math-9 | partly; note → note | Applied. ω_2 = 52/9 as a labelled review computation; ratio ≈ 4 (4.2; 4.9); tolerances corrected |
| integrity-01-bugfix-rerun-loophole | partly; must-fix → must-fix | Applied. §B11.2 (lead decision 3), W13. The audit also runs after the freeze, as the pre-look extension of the same symmetry |
| integrity-02-member-vs-nominal-and-gate-guard | partly; must-fix → should-fix | Applied (lead decision 4). Nominal-only outcomes (§B11.1); `members` list; gate refusals; test 36. A second run is allowed only as a recorded §B11.2 re-run |
| integrity-03-known-risks-omitted | partly; should-fix → should-fix | Applied. §B13 item 9, with the skeptic's correction (rule (iii) goes to F̂_T first); shown with W2 and W11 |
| integrity-04-pass-certifies-overclaims-independence | partly; should-fix → should-fix | Applied. §B1.8 table split; certificate extended (calendar, not data-blind, 3 attempts); §B13 item 7 aligned |
| integrity-05-later-plant-path-after-E | refuted; should-fix → note | Applied (clarity sentence in §B11.1) |
| integrity-06-premise-check-reference-and-ordering | partly; should-fix → should-fix | Applied. Blocking anchor on the v4 nominal (relative 1e-9); D4.12 values report-only; abort → E; budget settled before §B7; W9's "below" defined. The diagnostic script is committed if it still exists |
| integrity-07-realism-rows-not-whole-day-and-unlogged-wording | partly; should-fix → note | Applied. Provenance stated (dated D4.13 note or W3 lab choice); rows renamed off-peak |
| integrity-08-false-preregistered-properties | confirmed; should-fix → should-fix | Applied. Realism rows (weight 2/Σw) in the list; test 25 checks full-J5 violations against the list; ε·s in §B1.5 |
| integrity-09-hinges-fit-to-gate-boundary | partly; should-fix → note | Applied. §B5 reports guarded-row margins with CIs; §B13 items 7 and 9 (g); W5 note |
| integrity-10-test-specs-contradict-J5 | confirmed; should-fix → should-fix | Applied (tests 26 and 30) |
| integrity-11-design-evidence-ephemeral-variants-incomplete | confirmed; should-fix → should-fix | Applied. Archive and manifest before the commit (§B8 step 1); §B13 item 6 lists every variant. Run outcomes are not restated here (they stay in the archive) |
| integrity-12-screen-uses-validation-derived-floor | partly; note → note | Applied through route-6: the screen uses F8's Lc_k and reads no F11 field; test 33 defines the forbidden set |
| consistency-01 | confirmed; must-fix → must-fix | Applied. Option (a): property restated, bound disclosed, diagram corrected; B1.2 settled (system rows use all model episodes, lead decision 1); test 25 references explicit. Option (b) not adopted |
| consistency-02 | partly; should-fix → note | Applied. §B1.1 says masks are read live; a Mayfly manifest for the 22 calibration days is committed and verified before every J5 batch |
| consistency-03 | partly; should-fix → note | Applied. `calib_screen_data.npz` (§B8 step 4, §B5) |
| consistency-04 | confirmed; should-fix → should-fix | Applied with math-2. Test 26 on a day not heavy at B1; P7c and ε·s disclosed |
| consistency-05 | partly; should-fix → should-fix | Applied. P5c on `both_q`; test 30 at the tag's seed; test 24 cell state |
| consistency-06 | confirmed; should-fix → note | Applied. P8(i) at station-sharing pairs, P8(iii) on miss days, P3-1/P8(iii)-1 on real-B1-inactive days listed as untargeted |
| consistency-07 | confirmed; should-fix → should-fix | Applied. Full-precision ρ_cr governs (≈ 31.70/27.74/25.10, review recomputation); anchor on the v4 nominal; \|ΔJ_v4\| ≤ 0.0015 report-only. Anchor tolerance relative 1e-9 (route-7) rather than 1e-6 |
| consistency-08 | confirmed; should-fix → should-fix | Applied. The quotation no longer speaks as D4.13; dated note or W3 lab choice; share 2/(17 + ω_2) |
| consistency-09 | confirmed; note → note | Applied. §B8 step 4 (v4 facts reused read-only, blob hashes recorded); v3 and v4 manifests re-verified after every batch |
| consistency-10 | refuted; note → note | Applied (wording in §B1.1 only; no code change) |
| consistency-11 | confirmed; note → note | Applied (§B1.5 "Why") |
| consistency-12 | confirmed; note → note | Applied with change. §B12 recomputed with compute and pauses separated (route-10): route-critical ≈ 17.7–24.6 h instead of ≈ 23.5 h; the pause is not scaled |
| route-1 | partly; must-fix → should-fix | Applied. §B11.2 scope covers v5 text; a pre-look reversal continues; post-look label; W13 holds the FAIL → PASS choice |
| route-2 | partly; should-fix → note | Applied with integrity-02 (test 36) |
| route-3 | partly; should-fix → note | Applied. Stops short-circuit in order; the ensemble step is not a stop; test 39 |
| route-4 | partly; should-fix → note | Applied. §B13 item 9 (e), W7. The "lowest-J5 restart that passes §B4" alternative is not offered (it would ease N0) |
| route-5 | partly; should-fix → note | Applied. §B12 all-stages row; W11: the notice applies now; v4 §A9 not narrowed |
| route-6 | partly; should-fix → should-fix | Applied. Lc_k in the screen; false-STOP disclosure in §B5, §B13 and W8 (the "thresholds set for 97 days" premise corrected, per the skeptic) |
| route-7 | confirmed; should-fix → should-fix | Applied with consistency-07 |
| route-8 | confirmed; should-fix → should-fix | Applied (test 26 at row level and J5 level) |
| route-9 | confirmed; should-fix → should-fix | Applied. Tests 36–39 and the test-28 edge cases; margin −∞ on masked bins; the v_u = 40 edge stated |
| route-10 | confirmed; note → note | Applied. Compute and pauses separated in §B12 |
| route-11 | partly; note → note | Applied. The v5-S layout is unrecorded; the review recomputation at 16 processes is stated |
| physics-01 | partly; must-fix → note | Applied in part. Per-episode creditability (with math-3); backing-cell ratio reported. Speed-based backing (fix (a)) not adopted: it fails its own case (lead decision 2) |
| physics-02 | confirmed; must-fix → must-fix | Applied with change (lead decision 2). P_1 needs cells 26–28 congested, P_2 cell 33. The "most downstream cell in 28–31, or 32" clause is not adopted. The acceleration-zone residual is disclosed and tested as creditable. §B5 head cell, §B3 c1-inert days; h aligned to the new cells |
| physics-03 | partly; should-fix → note | Applied. §B1.8 sentence; excess vehicle-hours and in-episode v_u error reported in §B5 |
| physics-04 | partly; should-fix → note | Not applied. Shaping is worth at most ε of one P3 item, the ε = 0 sensitivity is reported, and a backing condition on g would remove the gradient it exists to give. (h now uses §B1.2's cells) |
| physics-05 | confirmed; should-fix → should-fix | Applied. Cells 25–39 recorded; P8g relocation clause; relocation days per restart; tests 31 and 41 |
| physics-06 | partly; should-fix → note | Applied. W12 rationale restated on physics; reports added in §B3 |
| physics-07 | confirmed; should-fix → should-fix | Applied, second branch of the fix. W6 default kept (no drop term; keeps P5b and P9 independent of the fit); failure path in §B13 item 9 (h); r̂ − r and Ŝ1 − S1 reported per restart; the hinge formulas are the W6 alternative, with real-anchored qualifying sets (item 0 if unmatched) instead of the fix's heavy-matched sets |
| physics-08 | confirmed; should-fix → should-fix | Applied (§B1.8, §B13 item 7) |
| physics-09 | confirmed; note → note | Applied. v4 §A11 item 8 (b)–(c) → E; known failure paths; v4 §A2 margins reported before the §B4 verdict |
| physics-10 | partly; note → note | Not applied (F_d unchanged): a trade-off, now disclosed in §B1.3; T.H.101's PM is covered by P8g's relocation clause |
| physics-11 | partly; note → note | Applied. Sentence marked [inference, untested]; freeze record adds the share of exact ĉ_k = 1.00 and 1/m_k |

### Check round (rev1 → rev2)

27 checker issues on rev1 (lens: integrity, coverage, consistency; the coverage and consistency ids repeat, so the lens is part of the id). Each was verified against v3, v4, the addendum, rev1 and the code (`metanet_gate.py` P8 block and `metanet_postcal.model_day` for P3/P8(iii); `metanet_freeze.py` l.394 for the facts read; the jobs' imports; the v4 batch `thermal.csv`). Binding lead resolutions (a)–(d) governed §B11.2 and P8g.

| Issue | Real? | Action |
|---|---|---|
| integrity R1-fix-asymmetry | yes | Fixed per lead (c): audit procedure pinned at §B8 step 3, one pass each; after the look, a FAIL → PASS from a bug found outside the gate audit is KILL-only ("second look on the same validation days"), a PASS → FAIL counts; gate guard requires the committed freeze-audit record (test 36); label also for a changed nominal or members. Not adopted: "only the two audits change an outcome" before the look, and a dated author decision for a reversed pre-look stop (lead (c): any pre-look fix follows (a); the route continues, disclosed, author told) |
| integrity R1-fix-ambiguity | yes | Fixed per lead (b): one-reading rule; the checkpointed code's reading stands; ambiguities logged, never fixed after a result; fix records quote the text (§B11.2 item 1) |
| integrity R1-fix-scope | yes | Fixed per lead (a): scope = every committed text (v3, v4, addendum, v5); text, threshold or criterion changes stay a new version (→ E) |
| integrity R1-guard-lock | yes | Fixed: per-seed start record and lock file (code and freeze hashes) before any validation input is read; plain crash re-run allowed at unchanged hashes; first committed freeze record only; test 36. Partial outputs are kept in `metanet_v5/` and listed in the ledger, not committed (raw runs stay out of the repo, CLAUDE.md) |
| integrity R1-easing-disclosure | yes | Fixed: §B11.2 item 5, §B13 item 3 and W13 state that the default eases v3 §6.3/v4 §A6 (3) after the look (gate-audit bugs) and adds tightening before it; the alternative keeps the inherited consequence |
| integrity R1-head-residual | yes | Fixed: residual widened to heads at 27 (one-cell zone over 28) and, for P_2, at 32 (zone over 33); §B5 flags heads at B_k's first cell "residual not excluded"; §B3 adds upper-half c1-inert days; the false "shows"/"is reported" sentences corrected (§B1.2, §B13 items 9 (i), 10); test 40. All report-only |
| integrity R1-dominance-s1 | yes | Fixed: s rule made local (§B1.4), so a non-creditable jam away from the shaping windows no longer sets s = 1; the remaining case (an overlapping or in-window unbacked dip) is listed in §B1.6 as a P3-k-through-s cost, by design; diagram reworded to "the s = 1 miss reference"; test 25 also compares with the no-episode outcome at a drawn s_0 |
| integrity R1-p8g-credit | yes | Fixed per lead (d): P8g (ii) hit day = the gate's P3 agreement (any overlap; `model_day`'s `agree`), extras = the gate's P8(iii) flag (every model episode overlapping no real one); §B1.2, §B1.3, §B1.6, §B1.8, tests 30 and 38 |
| integrity R1-reloc-disclosure | yes | Fixed: §B13 item 9 (c) rewritten on v3 §4.7's c2\* (relocation at c2 ≤ 1.00, any c1 → rule (iv) → E; only c2 > 1.00 → truncation); §B1.3 note; optional (1.20, 1.00) relocation count per restart added to §B2 (report-only) |
| integrity R1-test33-scope | yes | Fixed: test 33 covers the J5 evaluator (P8g included), the CMA-ES driver, the §4.7 grid and selector; §B13 item 5 widened |
| coverage R1-01 | yes | Fixed with integrity R1-fix-scope (lead (a)); the full re-run and both-outcomes rule kept |
| coverage R1-02 | yes | Fixed with integrity R1-p8g-credit (lead (d)); no change to decision 1 to log |
| coverage R1-03 | yes | Fixed, in a stronger form: s = 1 if any model P_k episode overlaps a real one or a non-creditable one has a bin in a g window (the proposed day-level clause would still let a backed extra restore shaping to an unbacked dip just outside the tolerance); tests 28 and 40 |
| coverage R1-04 | yes | Fixed: §B1.2 "differences" (stricter per bin and on head location; both directions per episode); §B1.8 P11-k row "steered, not scored or enforced"; §B13 item 9 (m) and item 10 |
| coverage R1-05 | yes | Fixed: §B8 step 6 commits the freeze record and runs the freeze audit in either branch, before E or step 7 |
| coverage R1-06 | yes | Fixed with integrity R1-reloc-disclosure |
| coverage R1-07 | yes | Fixed: §B8 step 1 archives the review scripts, inputs, `v5review_rows.json` and the check-round issues under `metanet_v5_design/review/` in the same manifest; §B13 item 6; log header cites the path |
| consistency R1-01 | yes | Fixed per lead (a): calibration and the gate re-run in full on the original seeds (v3 §6.3 as written); "everything affected" removed; cost noted in §B12 |
| consistency R1-02 | yes | Fixed: scope per lead (a); audit modules = everything the jobs import, fixed by name at §B8 step 3, today including `metanet_inputs.py`, `corridor_analysis.py`, `mndot.py` and `plants/metanet.py` (imports checked) |
| consistency R1-03 | yes | Fixed with integrity R1-p8g-credit, option (a) |
| consistency R1-04 | yes | Fixed with coverage R1-04; per-restart count of creditable hits on P11-unbacked days (§B1.2, §B2); test 40 case |
| consistency R1-05 | yes | Fixed with coverage R1-03 (local s rule). Not adopted: dropping the override (g would still reward an unbacked dip). "Zero only for plants with no miss" corrected; test 28 case |
| consistency R1-06 | yes | Fixed: §B3 and W12 say "usually preferred, not guaranteed" |
| consistency R1-07 | yes | Fixed: c1-inert days defined on E_1,d, O_1,d and cells 28–31 (J_d dropped) |
| consistency R1-08 | yes | Fixed per lead (c): §B11.1 says a reversed pre-look stop is not a resumption; it continues attempt 3, disclosed, author told |
| consistency R1-09 | yes | Fixed: test 25 states the item-level convention and the asserted inequality |
| consistency R1-10 | yes | Fixed: §B12 basis names both pauses (10 → 12,304 s and 25,152 → 25,355 s in `thermal.csv`, rechecked) |

Superseded round-1 wording: math-3's "J5 disclosed as stricter" (now "differs", §B1.2) and integrity-01's "everything affected" re-run (now in full).
