# Testbed protocol v0: design review (ranked fix list)

*2026-10-11 · workflow wf_7d5e1292-b67 (5 lenses + per-lens skeptic + completeness critic + synthesis; 12 agents) · 79 findings: 48 confirmed, 21 partly, 0 refuted · raw `/home/catalin/work/phd/vsl_lab_runs/day_pattern/testbed_design/review`*

**Verdict:** 32 fixes (7 blocking, 22 major, 3 minor); another round needed: yes. The 7 blocking items change the design substantially. They add a new inferential target and probably a new day generator, a common queue-protection layer, new comparator arms (SW, DA, UP/PI-ALINEA, CONST), an MPC model identified on testbed data, a low-drop PASS condition and T1, a redefined condition-1 population with an informed KILL envelope, NC-labelled regimes (possibly with new ones), and the stage-4 move to 700-999. v1 will also write content the draft deferred: day lists, generator formulas, s_jam, HERO/DA laws, tuning budgets, seed map and power. No reviewer has seen any of it. One focused ultracode check round on v1 is warranted, following the D4.14 precedent. It should be limited to the new or changed text and the finding-by-finding disposition table, plus a stats lens on the generator if option (b) is chosen. A full five-lens re-review is not needed unless the author picks options that reopen the arm set or the bar.

## Fixes (ranked)

1. **[blocking, author] Fix the inferential target: test instances are nested in 6 source days (n_eff is about the number of days)** (§0 scope sentence (l.9); §3 split and generator (l.65-79); §7 unit and CI (l.166-167); sources stats-01, stats-07, completeness-07)
   - Issue: Draft l.166-167 makes the instance bootstrap primary and calls the 6-day cluster bootstrap 'coarse', while l.9 words the claim for 'demand days generated from those 22 days'. The generator (λ fixed at 1, ±30 min shift, ±10 % stretch, 5 % bin noise) adds little day-level variety. The review's crude check on calibration days (scratchpad icc.py: crude generator and meter, not protocol seeds) gave an ICC of the paired Δ of 0.87-0.96, so about 200 instances on 6 days give n_eff ≈ 7. The per-day effect also changes sign across days (−17.7 % to +73 %). With 6 clusters, a percentile cluster bootstrap excludes 0 whenever all 6 days share a sign (p = 1/32 under a symmetric null). A day-level Bonferroni-4 regime win needs ≥ 8 test days that all agree (sign test p = 2^(1−n)), and R-both has only 9 days in total. As drafted, a PASS can be dismissed as pseudo-replication, and an honest day-level test makes condition 2 nearly unreachable. D2.3.3 (decisions:15) already says 'fit a flexible multi-peak model to them, train on generated days'.
   - Fix: The author picks one target before data. Recommended: option (b).
(b) Fit a multi-peak day model (D2.3.3) with explicit between-day random effects on the 12 train-source days only. Every tuning, validation, training and test instance is an independent whole-day draw (seeded), so the instance bootstrap is valid for the declared population. The scope sentence then says 'on days drawn from a generator fitted to 12 of the 22 calibration days'. The 6 held-out real source days stay as a pre-registered report-only row, 'held-out real day shapes': old g, a two-stage bootstrap (days, then instances), and the count of days whose day-median Δ favours the candidate.
(a) Alternative: keep g on real days. Make the two-stage bootstrap primary and word every claim 'on generated variants of the 6 held-out source days (listed)'. Pre-register the label 'day-conditional only' when fewer than 5 of 6 test days favour the candidate, and state now that per-regime Bonferroni wins are then practically unreachable.
(c) Use K-fold rotation over the 22 days with retraining (cost ×K) only if compute allows.
Whichever is chosen, write its power calculation (see the seed-map item).
2. **[blocking, author] Restore the low-drop guard and T1, and record the deterministic-plant status** (§0 (l.7, l.9); §1 (l.24); §5 stage 1 (l.140-145) and stage-4 bar (l.149-153); sources scope-01, plant-03, stats-10, scope-03)
   - Issue: The draft never mentions a low-drop variant, T1 or a D-check; stage 1 has only M-EQ, P0, T0-M, T0-V and T3.
- D4.7 (decisions:59) binds v3 R4(d) ('A GO must also hold on the low-drop variant', v3:1058) and says the protocol 'may not drop or weaken' it; v5:612 repeats this. CLAUDE.md:78 defines T1 as 'capacity drop exists ... and control matters'.
- The frozen plant fails P5b-1: median r̂ − r = −0.030 against a limit of −0.02, and r_model is 0.977 against a real 1.006. The CI [−0.035, +0.008] includes 0, and only 15 of 17 days matched. δ_m = 3.47 against δ = 0.0122 in Hegyi et al. 2005 [VERIFY; only hegyi2.txt:898 read], and δ_m acts on the E12-E14 releases (metanet.py:617). A metering gain could therefore come from the drop.
- Separately, v3 R3(b)/A4 (v3:1057: on a deterministic plant 'only a KILL counts ... not open to a later decision') is neither applied nor set aside. D5.6, which is later and specific, authorises claims on this plant but says nothing about R3(b). v5 STOPped before reaching 'PASS, deterministic-only'. This part is a decision and disclosure gap, not a violation.
   - Fix: (1) Add T1 to stage 1, with the criterion fixed now: under NC on train-source instances, B1 and B2 each show a discharge drop (median r < 1), and some arm moves J by > 1 %.
(2) Build the R4(b)-(c) low-drop variant: an F1 switch on the bottleneck cells, with Δ_k found by bisection to the target median r = min(1, U_k) on the calibration heavy-day set (simulate() supports f1, metanet.py:500). Add a bar clause: 'conditions 1–3 also hold on the low-drop variant, for the frozen candidate and every arm as tuned on the nominal plant'. This is an intersection over two plants, so it needs no extra multiplicity.
(3) Add report-only rows: a δ_m variant (value fixed now) and a synthetic capacity perturbation (c1/c2 law fixed now), since no F̂ exists.
(4) The author records a dated decision. Either R3(b) is set aside for this testbed only, and a PASS is labelled 'deterministic synthetic-testbed result, never a gate GO, no transfer to U.S.169'; or R3(b) applies, and the testbed can only KILL. If R4(d) is also set aside, the scope sentence must say 'B1 capacity drop exaggerated (P5b-1 FAIL)'.
3. **[blocking, author] Add a non-learning adaptive switcher (SW) to the comparator set** (§0 (l.21); §4 (l.99, l.116, l.125); §5 (l.151); sources comparators-02, scope-07)
   - Issue: Every non-learning arm uses one parameter set for all regimes (l.99), and the only regime-aware arm, O-a, is report-only (l.116). Yet l.21 expects the wins 'mainly in disturbance or atypical regimes'. A learner win in R-inc or R-slow would then show that switching helps, not that learning beats tuned proven control.
- Binding and design text: CLAUDE.md:14 'no weak baselines'; CLAUDE.md:74 lists 'a non-learning adaptive scheduler' in 'best non-learning' (inside the now report-only H definition); roadmap:26-28 rule 5 'same information'; D2.3.5 (decisions:17) lists first-hour pattern matching, adaptive ALINEA and breakdown-triggered HERO.
- BN4 Addendum I included a non-learning adaptive scheduler, evsched (gscan:58, :366), and the candidate beat it; the testbed drops that precedent.
- L2 switches among the O-a sets (l.125) with no rule-based counterpart, so an L2 gain cannot be attributed to learning.
   - Fix: Add an arm SW that enters the B_k set. It is a rule-based detector, fixed now, that switches among the O-a^tune parameter sets of the best non-learning family.
- Example detector: 'disturbance mode' when the 60-s speed at any G3 station is below x km/h for ≥ k min while upstream density is below ρ*. The 05:00-06:00 volume at the upstream stations selects the R-B1 or the R-both plan.
- A switched-in controller starts at the current commanded rate.
- Tune (x, k, the volume threshold) on tuning instances under the common budget.
- Optionally also add an occupancy-adaptive ALINEA.
State that a regime win counts only if it holds against SW. This is automatic under the intersection-union rule (B_k item).
4. **[blocking, author] Ramp-queue handling: one pinned queue-protection layer for every arm** (§2 (l.34-41); §4 (l.103-108, l.120-121); §5 condition 4 (l.153); sources comparators-01, plant-04, drl-09, stats-11)
   - Issue: L.36 says: if w_i ≥ S_i, or w_i/r_i ≥ 240 s, 'the ramp releases at Q_O for that control period'. Q_O = 2,200 veh/h (metanet.py:25) is above the 1,714 cap, so an override means no metering for 60 s. That releases about 37 veh, more than any S_i (≈ 10-27 veh).
- **The handicap.** ALINEA, HERO and CONST-TOD have no queue term, so with this little storage they become meter/flush oscillators. L1, by contrast, sees the 4 queues (l.120) and can learn queue control. This is the 'queue-hobbled feedback' pattern the project's own review warns about (docs/review/day_pattern_research_v0.md:52, :98). IRIS density adaptive bounds the rate from below with wait, 75 % storage and backup limits (lit/iris/density_adaptive.md:110-151 [read in part, VERIFY]).
- **Unpinned details.** Per-step vs period-start evaluation matters: in the prototype, E14's maximum queue is 16.1 vs 23.5 veh with S = 17.1, and E9's override minutes are 13.3 vs 25.5. Also unpinned: whether 'releases at Q_O' bypasses the d + w/T and supply terms (metanet.py:583); the wait for r = 0; hysteresis; ALINEA windup during an override; and a low-rate trigger at w ≥ r/15 (16 veh at 240 veh/h).
- Bar condition 4 depends directly on these choices. v3 R1(b) (v3:1055) requires only one identical rule.
   - Fix: Replace l.36 with one layer applied to every arm, learning or not, and also inside MPC-E's internal model. It is evaluated every step T.
- r_eff = min(r_max, max(r_cmd, r_wait, r_stor)).
- r_wait = 3,600·w/240 veh/h, which serves the current queue within the 240-s max_wait.
- r_stor = d̂ + 3,600·(w − 0.75·S_i)/60 when w > 0.75·S_i, with d̂ the mean arrivals over the last 60 s.
- q_o = min(d + w/T, Q_O, supply, r_eff), never above supply.
- Hard safety net: at w ≥ S_i, r_eff = r_max until w ≤ 0.5·S_i.

'Queue-layer minutes' are the minutes with r_eff > r_cmd; safety-net minutes are reported separately. ALINEA and HERO integrators are reset to r_eff while the layer binds (anti-windup).

Unit tests:
- w ≤ S_i plus one step's arrivals;
- q_o ≤ supply;
- r_cmd ≥ demand reproduces NC exactly.

Before stage 2, check that no tuned arm spends more than X % of its metered minutes in the layer on tuning instances (X fixed now, e.g. 20 %). Any arm that does gets its spec revised before stage 2.

If the author keeps a Q_O flush instead, pin per-step evaluation, hysteresis and anti-windup, and give L1 the flags.
5. **[blocking, author] Stage-1 actuator authority: a T0-M that can bind, storage fixed, and a cheap early informed screen** (§2 (l.35, l.37-41); §5 stage 1 and 2 (l.140-147); §10 item 5; sources plant-01, stats-12, plant-07, completeness-02)
   - Issue: T0-M (l.143) cuts E13 from 1,714 to 600 veh/h, but E13's demand never reaches 600. Its Queue arrivals peak at a 5-min maximum of 324 veh/h over the 22 calibration days. In the prototype ΔJ = 0.000 % on 22/22 days at 600 veh/h, and only −0.66 % to +0.10 % even at 240. Demand exceeds 240 veh/h in 1.9 % of bins at E12, 23 % at E9 and 40 % at E14.
- **T0-M fails by construction**, and no consequence of a T0-M FAIL is stated (CLAUDE.md:77: 'T0 the actuator binds').
- **Storage is tiny.** The IRIS metro_config gives storage of 300/450/500/420 ft and r_node lanes='1', with no storage-lane attribute. S ≈ 10-27 veh depending on s_jam, which is still open (l.40), so the B1 feeders can hold back only about 50 veh.
- **The KILL comes late.** HERO, MTFC-VSL and MPC-E are built and tuned before the stage-2 KILL, against CLAUDE.md:75 ('design so that the KILL comes early and cheap'). The untuned prototypes (all meters at 240 veh/h: J +9.4 %; PM metering of the B1 feeders: +1.2 %) do not show that stage 2 will KILL.
   - Fix: (1) Restate T0-M per head: B1 = E9 + E12 + E13 jointly, B2 = E14. Rate = max(240, 0.5 × the ramp's PM mean demand), queue layer on, ≥ 3 heavy train-source days or tuning instances. Criteria: the head inflow falls and |ΔJ| > 1 %. Consequences, fixed now: a FAIL at both heads is a stage-1 KILL; a FAIL at one head takes the regimes that depend only on that head out of condition 2, with disclosure.
(2) Report each controlled ramp's share of bins with demand above 240 veh/h (the controllable band, D4.11).
(3) Fix in v1: storage lanes = 1, stated from metro_config, and s_jam with a cited source. Recommended: the IRIS jam density of 180 veh per lane-mile, i.e. 8.94 m [VERIFY density_adaptive.md:252], disclosed as differing from ρ_max. Keep the ±25 % row.
(4) Add a stage 1b 'authority screen' before HERO, MTFC, DA and MPC-E identification are built. It runs the informed reference I (a true-model, perfect-forecast MPC; see the KILL item) and a coarse CONST-TOD grid on a stated subset of tuning instances. If I misses 10 % vs NC on the condition-1 population, the testbed is KILLed at stage 1b.
6. **[blocking] Split O-a into a tuning-set object and a test-set report-only bound, and guard the test seeds** (§4 (l.116, l.125); §5 (l.133, l.147); §7 (l.169); sources scope-02, drl-01, comparators-07, stats-08)
   - Issue: L.116 defines O-a as 'chosen on the test instances (cheats on purpose)'. Yet l.147 uses O-a in the stage-2 KILL on 'train-source tuning instances', and l.125 trains L2 to imitate 'O-a's labels'.
- **Leak.** Read literally, the test instances are touched in stage 2 and test information reaches a possible candidate (L2). That breaks 'One look' (l.169), roadmap:19-23 ('Seed roles never mix') and CLAUDE.md:73 ('Never use the best grid point per gate seed').
- **Too narrow.** O-a covers only CONST-TOD and ALINEA, so 'O-a vs the best single-tuned arm' can be negative when HERO or MPC-E is best.
   - Fix: Define two objects.
- **O-a^tune:** the per-regime best over every non-learning family, tuned on tuning instances (7,193,100-299). Used in the stage-2 KILL envelope, for the stage-2 adaptation gap, as H's lookup I, as SW's parameter library and as L2's menu.
- **O-a^test:** the same rule re-tuned on test instances. Run only in stage 4, after the candidate's result is computed; report-only; listed in the stage-4 computation order; labelled 'tuned on test'.
Add a seed guard (as in BN4) so that no code path before stage 4 can evaluate any arm on test seeds or test-source days. Neither O-a enters B_k.
7. **[blocking, author] Align reward, metric, warm-up and drain, and define every arm's behaviour after 23:00** (§0 (l.19); §4 L1 (l.122-123); §6 (l.158-161); §5 condition 4 (l.153); §10 item 4; sources drl-02, plant-11, scope-13, stats-11)
   - Issue: L1's episode and reward end at 23:00 (l.122-123). J runs 'from 05:00 until the drain ends', with demand 0 after 23:00 and a 2-h cap (l.158-160).
- **Behaviour undefined.** No line says what any arm does after 23:00 or during the 04:00-05:00 warm-up (the inputs start at 04:00, metanet.py:30-31). J is therefore not computable for L1, L2 and FIELD, and the confirmatory J depends on an unregistered choice.
- **Terms undefined.** β after 23:00 is undefined, and so is 'counted at the cap'. Free-flow time in model terms is undefined; the 1.05·v_f cap (metanet.py:28) can make per-cell delay negative.
- **Reward ≠ metric.** This contradicts the draft's own lesson, 'reward = the judged metric' (l.19).
The drain is small at λ = 1 (NC: 76-137 mainline vehicles at 23:00, no origin queues), but it is unpinned and gameable at high λ, after late incidents or with held queues.
   - Fix: Pin the following.
(1) 04:00-05:00 is an NC warm-up for every arm, with untransformed inputs, excluded from J.
(2) From 23:00 every arm switches to NC (meters off, VSL off); β = the last bin, held; demand = 0.
(3) The drain runs until the network and all queues are empty, capped at 2 h. If the cap is reached, each remaining vehicle is charged its time to the cap plus a fixed penalty (e.g. its free-flow time to the network end). Cap breaches are reported per arm.
(4) J = Σ_k T[Σ_i ρ_i L_i λ_i + Σ_o w_o] − Σ_k T Σ_i q_i L_i / v_f,i (nominal v_f), from 05:00 to the end of the drain.
(5) At 23:00, L1's env rolls the plant through the drain and gives a terminal reward of minus the drain-period delay. The per-step reward is −Δ(delay incl. queues)/normaliser, so the return equals −J/normaliser exactly; state this.
(6) Report the residual vehicles per arm at 23:00.
8. **[major, author] Condition-1 population and the stage-2 KILL: one population, an informed envelope, exact wording** (§3 regimes (l.83-90); §5 (l.134, l.147, l.150); §8; sources stats-04, scope-06, completeness-02)
   - Issue: Condition 1 (l.150) pools the comparison with NC over four regimes, with no stated weights or instance counts. Two of the four force an incident or a slowdown on every instance, so whether the pool reaches 10 % depends on a free mixing parameter.
- **KILL wording.** The stage-2 KILL (l.147) does not say whether it is pooled or per regime, nor whether a CI is needed. D5.6 (decisions:78) says 'no regime ≥ 10 % vs NC', so a disturbance-only regime can keep the testbed alive even though condition 1 would later fail.
- **KILL envelope.** It holds only the tuned arms and the per-regime O-a. CLAUDE.md:70 names 'a tuned proven controller, or an informed oracle', and D4.8 (decisions:60) requires 'the full informed envelope ... so that a KILL is conservative'. On BN4 a plain DRL beat a per-kind constant oracle by 16.6 % (t1_meter_r6plus_diag.md:16). The draft's KILL is therefore not conservative.
CLAUDE.md:20's 'realistic demand level' refers to λ, which the draft meets; the pooling is a design concern, not a breach of binding text.
   - Fix: The author picks the condition-1 population.
- Recommended: the undisturbed instances at their natural generator frequency (R-B1 ∪ R-both, plus R-atypical if it is added). The 4-regime equal pool and every per-regime comparison with NC are reported.
- Alternative: a pre-declared mixture with a cited incident and slowdown frequency [VERIFY a source].
Fix equal instance counts for the disturbed regimes.

Rewrite the stage-2 KILL: 'KILL if min{every tuned arm incl. SW, O-a^tune, the day oracle, the informed reference I} does not beat NC by ≥ 10 % (median paired difference, 95 % CI upper bound < 0) on the condition-1 population of tuning instances at λ = 1. Per-regime results are reported; a regime that reaches 10 % only through a disturbance is flagged.'

I is an MPC with the plant's true model and the instance's true demand and disturbance (a perfect forecast), at the common control period, run on a stated subset (e.g. 60 tuning draws). It is never a candidate and never in B_k. A result of 'tuned arms < 10 %, informed ≥ 10 %' is recorded as CONTINUE with that label. Record the deviation from D5.6's per-regime wording as an author decision.
9. **[major, author] Regimes: arm-independent labels, pinned disturbances, and the day-pattern hypothesis** (§0 (l.7); §3 (l.77-90); sources stats-03, completeness-07)
   - Issue: R-B1 and R-both (l.87-88) are labels of the real 2023 days, and the frozen plant often does not reproduce them under NC replay.
- **Labels.** B2 is not active on 20230920, a 'both' day. B1 is not active on 0621, 0802 and 1115 ('both' days), nor on 0503 and 0705 ('B1' days). The median NC delay is 1,523 veh·h on 'both' days against 1,713 on 'B1' days. The names therefore misdescribe the simulated conditions, and relabelling by simulated episodes would make the labels depend on the arm.
- **Disturbances.** In replay, a one-lane closure binds within its first 30 min in only ≈ 79 % of draws (39-85 % by day), so part of R-inc is effectively undisturbed.
- **H1 untested.** The project's main bet, H1 (adaptation to the day's demand pattern: D2.2.1, decisions:11; CLAUDE.md:62; multi-peak days in D2.3.2-D2.3.3), is not tested. The only pattern variation is a ±30-min shift and a ±10 % stretch.
- **Surge dropped.** Ramp-demand spikes, an approved surprise type (D2.2.2, decisions:12) and a BN4 regime (surge), are silently dropped.
   - Fix: (1) Label the undisturbed regimes from each instance's NC run, computed before any other arm runs; never from the candidate's or B_k's episodes. R-B1 = the NC run has a B1 episode and no B2 episode; R-both = it has both (EA-2 episode thresholds fixed now). Reach fixed counts by quota sampling of generator seeds on the NC label only. If the author keeps source-day labels instead, rename them 'S-noB2 / S-B2 source days' and report the simulated B1/B2 occurrence per regime.
(2) For each disturbed regime, report the share of instances in which the disturbance binds under NC.
(3) Author decision, one of two:
- add R-atypical (instances whose latent generator pattern parameters fall beyond the fitted 10th/90th percentiles, thresholds fixed now) and R-surge (a ramp-demand spike law per D2.2.2, fixed now), with Bonferroni over the new regime count;
- or record a dated decision that D5.6 sets D2.2.1, D2.2.2, D2.3.2 and D2.3.3 aside here, and say in §0 and in the scope sentence that this testbed does not test H1 or demand surges.
10. **[major, author] Define the B_k set and use an intersection-union rule** (§4 (l.61, l.115-116); §5 (l.151-153); sources stats-06, comparators-12)
   - Issue: L.151 defines B_k as 'the tuned non-learning arm with the lowest median J in that regime'. It leaves open:
- **membership:** NC is not tuned; FIELD and O-a are report-only; MPC-E may be 'not tuned further' (l.115); MTFC-VSL is conditional;
- **the selection instances.**
If NC is the best arm in some regime (plausible where B1's ramps cannot bind), excluding NC lets a candidate 'beat the best' while losing to no control. With heterogeneous days, the arm with the lowest marginal median need not give the least favourable paired difference. 'Best tuned proven controller' (CLAUDE.md:21) then claims more than the listed set supports.
   - Fix: List the set: CONST, CONST-TOD, ALINEA and its variants, HERO, DA, SW, MTFC-VSL if kept, MPC-E as run (capped or not), and NC as a floor. Excluded: FIELD, O-a^tune, O-a^test, the day oracle, the informed reference I, and the exact-model and wrong-model MPC rows.
- **Condition 2** holds in regime k only if the Bonferroni CI upper bound is < 0 against every arm in the set (intersection-union, so no extra multiplicity).
- **Condition 3** fails if its criterion holds against any arm.
- **Conditions 4-5:** B_k is the set member with the lowest median J in regime k on the test instances.
Word every claim 'the best of {list}, tuned as in §4'.
11. **[major, author] Conditions 2-3: a relevance margin for wins and an explicit non-inferiority reading** (§0 (l.21); §5 conditions 2-3 (l.151-152); sources completeness-03, stats-07)
   - Issue: Condition 2 has no minimum effect: any regime win whose Bonferroni CI excludes 0 passes, however small. On a deterministic plant with common random numbers, a 0.5-1 % difference can be significant. Condition 3 tolerates up to 5 % worse, and the draft itself expects an informed optimum to beat good feedback by only about 2-9 % (l.21).
Condition 3 copies D5.8 and Addendum I faithfully ('worse by > 5 % with the Bonferroni CI lower bound > 0'). It is an absence-of-evidence test, and it becomes practically impossible to fail if the inference moves to day level (see the inferential-target item). Addendum H read a result as 'rel ≤ −5 % with the CI upper bound < 0' (gscan:326).
   - Fix: The author picks.
- Recommended: condition 2 requires a point rel ≤ −5 % and a Bonferroni CI upper bound < 0 against every arm in the set. This is symmetric with condition 3 and matches Addendum H's reading. It is stricter than D5.8, so it needs a dated decision.
- Minimum alternative: keep D5.8 as it is, but label a win with |rel| < 5 % 'detectable, below the 5 % relevance threshold', and always print rel with its CI in the claim sentence.
Condition 3: write the exact operational form ('point rel > +5 % and Bonferroni CI lower bound > 0 ⇒ FAIL'). Add a per-regime label, 'non-inferiority (5 %) shown' if and only if the Bonferroni CI upper bound is < +5 %, otherwise 'not shown', and list it in the claim sentence.
12. **[major] MPC-E: identify its model on testbed data and specify it completely** (§1 (l.25-26); §2 (l.32); §4 MPC-E (l.110-115); sources comparators-03, plant-06, comparators-04, comparators-11, drl-03, scope-04)
   - Issue: The MPC's model is CMA restart 7,192,014. It was fitted to real 2023 data, not to the testbed it controls (v3 R3(c), v3:1057: 'mpc_f's model is refitted on tuning-seed plant data'; CLAUDE.md:74: 'fitted on separate seeds').

**It is a qualitatively different plant:**
- rc2 sits on its lower bound; ν 5.1 vs 88.9; κ 59.7 vs 8.1; δ_m 0.21 vs 3.47;
- B1 head capacity 4,672 vs 3,560 veh/h (+31 %);
- a phantom bottleneck at cell 22 (2,160 veh/h, against replay maxima of 2,155-2,326);
- B2 model-active on 2 of 22 days, against 8.

**The spec is a strawman:**
- one move per ramp with 3 unspecified levels, re-planned every 5 min, which contradicts l.32;
- no objective, terminal cost, state source or override modelling.

**It breaks its own cap.** 81 plans × 15 min cost ≈ 0.33 s per decision, i.e. ≈ 70 s per day before the plant runs. That is above the l.115 cap of 60 s, so by the draft's own rule it is 'not tuned further'. The MPCs in the literature use 1-min steps with Nc = 3-5 (hegyi2.txt:1023-1031; bel.txt:926-932).

The mismatch row 7,192,017 (τ on its 60-s bound, r̂ − r = −0.245) is another calibration optimum, not a small perturbation.

Severity is major, not blocking: B_k is the best of at least 5 arms, and a fitted model would not see the disturbances anyway.
   - Fix: (1) **Identification.** Fit the 17 METANET parameters, or a declared subset, by least squares on 5-min station flow and speed at the 17 station cells. The data come from NC plus random-rate excitation of the four meters on tuning instances (seed sub-range stated), within a stated budget. Freeze the model before stage 2 and report its fit on validation instances.
(2) **Spec.**
- Objective: J's integrand (delay incl. origin queues) plus a terminal cost on queues and density.
- Np ≥ the congested E9-to-end travel time (≥ 15 min).
- Nc ≥ 3 moves of 60 s, re-planned every 60 s; or every 2-5 min if the stage-1 timing requires it, fixed before tuning.
- Levels = L1's level set, searched by a stated gradient-free optimiser warm-started from the previous plan.
- The queue layer and storage are modelled inside the prediction.
- A coarser internal step is allowed only if it satisfies the CFL condition on every cell.
(3) **Information.** The state comes from the 17 station readings and the queue counts (interpolation or a fitted observer); the forecast inputs equal L1's.
(4) **Budget.** Fixed now (e.g. the CPU-hours of one L1 learner), batched across instances. Tune Np, Nc and the queue weight on tuning instances.
(5) **Report-only rows.** A 'wrong-model MPC' (7,192,014) and an exact-model MPC. Describe 7,192,017 as 'another calibration optimum with a ≈ 25-pp larger B1 drop'.
13. **[major, author] Comparator set: add the incumbent-type and the strongest published metering laws** (§0 (l.7, l.18); §2 (l.35, l.61); §4 (l.99-109); sources comparators-05, comparators-06, scope-07)
   - Issue: (a) **No DA arm.** MnDOT IRIS density adaptive (DA) is absent. lit/iris/density_adaptive.md gives the full law: the segment density runs to the highest-density station within 3 miles, so E9 and E12 can anticipate B1; rates are 240-1,800 veh/h; queue limits are included. The IRIS release notes record SZM's removal in 4.44.0 (2016; release_notes_4.md:397-403), yet the draft takes its limits from SZM (l.35). Whether U.S.169 SB ran DA in 2023 is [VERIFY].
(b) **E13's ALINEA watches B2, not B1.** It senses at cell 32 (S1140), ≈ 1.8 km downstream of B1's head cell 28. In replay, in bins where only B1 is congested, cell 32's ρ/ρ_cr has a median of 0.70 and never exceeds 1, while S1147 (cell 27) exceeds 1 in 58 % of them. So E13's ALINEA and HERO's master track B2; tuning ρ* compensates only in part.
(c) **PI-ALINEA and LB-TFC are absent.** PI-ALINEA is the RM layer of the MTFC+PI-ALINEA benchmark that CLAUDE.md:33 cites (frejo2.txt:104-118 and 1337-1346: mean TTS reductions of 12.7, 18.9 and 20.6 %).
(d) **FIELD is ill-defined.** It replays Passage counts open loop on shifted and stretched days.
   - Fix: Add the following arms. Each is tuned under the common budget and enters the B_k set.
- DA from density_adaptive.md, in two versions: 'field DA' with the default constants, and 'tuned DA'.
- UP-ALINEA for E13, measured at S1147, cell 27 [VERIFY Smaragdis & Papageorgiou].
- A PI-ALINEA variant of the local layer [VERIFY Wang et al. 2014 before citing it].
- LB-TFC (frejo1.txt), only if VSL stays in [VERIFY that an RM-only form exists].
Use one release range for every arm, with its source. Recommended: the IRIS 240-1,800 veh/h (density_adaptive.md [VERIFY]).
Run FIELD as report-only on untransformed source days only.
If any of these arms is ruled out, the claim says 'the best of {list}'.
14. **[major, author] VSL: decide now, and make the actuators symmetric** (§2 VSL (l.43); §4 (l.109, l.121); §5 T0-V (l.144); §10 item 2; sources comparators-09, plant-09, drl-11, scope-04)
   - Issue: The VSL spec omits v3 R6's binding rules (v3:1060): T0 under both response forms (the Hegyi min form and the MTFC modified FD), the sign kept at α = 0.0 and 0.2, and no new bottleneck. metanet.py:609-612 implements only the min form.
- **Little authority.** On the frozen G2 (speed at capacity 79.2 km/h), the min form at b = 60 cuts static capacity by 6.7, 3.3 and 1.0 % at α = 0, 0.1 and 0.2. The cut is ≈ 0 at b = 70 and zero for b ≥ 80, although those levels still lower free-flow speed. T0-V's '> 3 %' threshold (l.144) therefore hinges on the unidentified α.
- **Unspecified.** The VSL area (km 1.06-2.56) cuts through cells 21 and 24. MTFC-VSL (l.109) has no law, set-point, gains, sensing cell, rate limit or RM-first ordering.
- **Asymmetric actuators.** If VSL stays, B_k may be a VSL arm while L1 (l.121) and MPC-E act on the meters only. CLAUDE.md:26 says a fair DRL acts 'on the same actuators'.
   - Fix: The author decides before data, not after T0-V. Recommended: VSL out for this testbed. The implemented form has little static authority, the modified-FD form is not implemented, and the learner would need a fifth action head. The claim is then worded 'ramp metering only', and the title's speed-harmonisation part is disclosed as not tested here.

If VSL stays in:
- list the VSL cells;
- implement the modified-FD response, and run T0-V under both forms and α ∈ {0.0, 0.1, 0.2}, with R6's keep/drop rule stated now;
- restrict b to the levels that have an effect, or report the inert ones;
- add R6's no-new-bottleneck check (P_1/P_2 counts per arm);
- write the MTFC law: station sensing per R13(b), set-point, gains, and b down to Carlson's lower bound with its rate limit [VERIFY Carlson et al. 2011/2014];
- give L1, L3 and MPC-E a VSL action, and update the compute estimate.
15. **[major, author] Pre-register outcome, post-look and termination rules** (§0 (l.7); §5 flowchart (l.131-138); §7 (l.169); §8 (l.178); sources stats-09, completeness-04)
   - Issue: §7 says only 'One look'.
- **Post-look fixes.** Under CLAUDE.md:85 ('fix, re-run everything affected, log both outcomes'), a post-look FAIL → PASS from a fix is allowed as long as both outcomes are logged. W13-strict (v5:11, D4.14) was decided for v5 only.
- **No freeze.** There is no SHA freeze of the evaluator and analysis code, and no order for the test computations.
- **No FAIL branch.** The flowchart has no FAIL branch after S4. Roadmap:23 allows confirmatory seeds 'once per frozen candidate', so new candidates could be confirmed until one passes. The incentive is real: under the 2026-10-05 thesis decision, only positive DRL results count.
- **No claim level.** BN4's was 'chapter-level ... reported whatever it is. Run once.' (gscan:378).
- **Conflicting binding lines** on whether DRL alone can be the thesis candidate: CLAUDE.md:17 ('DRL alone is a reference arm only') and :89, against D5.8 and CLAUDE.md:19.
- **No time box** for the testbed, although D4.13 time-boxed v5 and about 11 months are left.
   - Fix: Add an 'Outcomes' subsection.
(a) Stage 4 runs once, the job refuses a second run, and the result is reported whatever it is.
(b) Before the look, commit the SHA-256 of the candidate, the evaluator, the analysis code and the bootstrap RNG seed. List every test computation in order: candidate and the B_k set → bar → robustness and artefact rows → O-a^test → day oracle on test → held-out-day rows.
(c) W13-strict: a post-look FAIL → PASS caused by any fix is KILL-only and reported; a PASS → FAIL counts.
(d) A FAIL closes this protocol's claim path. A later candidate needs a new dated protocol version and fresh seeds, and every claim states 'confirmatory attempt k of k; earlier: FAIL'.
(e) State the claim level now (recommended: 'chapter-level, declared synthetic testbed').
(f) The author confirms that D5.8 governs whether DRL alone is eligible, and CLAUDE.md:17 and :89 are corrected.
(g) A calendar time box for stages 1-2 and stages 3-4 (dates set by the author). On expiry the result is a stop, as in D4.13.
16. **[major] Day split: a mechanical, stratified, committed rule, plus disclosure of the review's looks** (§3 split (l.65-70); §7 (l.167); sources stats-02, scope-10, drl-08, completeness-01)
   - Issue: Applied to the 22 calibration Wednesdays (metanet_v5_precal_facts.json 'days'), the stated cycle 'train, train, validation, train, test, train' gives 15/4/3, not 12/4/6. The test days would be 20230329, 20230621 and 20231004. Only 20230621 is a qualifying 'both' day, and B1 is inactive on it in the frozen nominal, so R-both would rest on one test day.
- **Pre-protocol looks.** The design review has already run controlled prototypes on all 22 days (icc.py, simctrl.py, run1-run4, p0_check.py, nc_spread.py, inc_bind.py, alinea_loc.py, caps.py), with per-day metering effects from −17.7 % to +73 %. Day lists chosen by hand could be informed by which days favour metering. CLAUDE.md:81 ('Protocol before data ... disclose it') and D4.4 (decisions:56) require disclosure.
- **Holiday stratum.** The holiday-adjacent day 20230705 (precal F15; v3:1211, holiday stratum) is not handled.
   - Fix: Fix the split by a seeded random draw stratified by the real B2-heavy label: R-both 5/2/2 and R-B1 7/2/4, i.e. 12/4/6. Commit the RNG seed and the code in v1, and print the resulting day lists there. Place 20230705 by rule, or exclude it and list it.
Add a disclosure paragraph that lists every review computation on the 22 days, labelled 'design input taken before the split'.
State that no controlled-mode run touches a test-source day before stage 4: stage-1 checks run on train-source days, M-EQ runs in replay, and R1(d) runs on the non-test days under inferential option (a).
17. **[major, author] Instance design, seed map and power** (§7 (l.166); §8 (l.171-180); sources stats-05, scope-12, drl-08)
   - Issue: §8 gives only '500–699 test instances (stage 4)'. Missing:
- a map from seed to (day, regime, generator draw), and the counts per regime;
- separate random streams for noise and for disturbances;
- whether a generator seed is reused across regimes, which correlates the units of the pooled bootstrap;
- whether policies act deterministically at evaluation.

**Seed roles.** The confirmatory run sits on 500-699, which is the 'test (exploratory head-to-head)' role. The 'reserved confirmatory' range 700-999 (CLAUDE.md:83; CLAUDE.md:13: 'one confirmatory run on reserved seeds') goes unused. The DRL block 7,280,000-7,289,999 breaks the 7,2t0,000 pattern (CLAUDE.md:84) for the day-pattern track digit 9.

**Power.** If instances are independent (see the inferential-target item): the per-instance SD of the paired Δ is ≈ 10-25 % of J (≈ 50 % in the disturbed regimes, back-calculated from Addendum I). At α = 0.05/4 with 80 % power, that needs ≈ 70-440 instances per regime for δ = 5 %, and ≈ 18-110 for δ = 10 %.
   - Fix: Write a balanced table: for each regime and split, the instance count and the seed formula. Each seed gives a base-day draw from a generator sub-stream, a disturbance from a separate sub-stream, and noise from a third. State whether a base day is reused across regimes; if it is, pooled bootstraps resample seeds as clusters. Every arm runs on the same instance (common random numbers), and policies act deterministically (argmax) at evaluation. Include the power calculation, its assumptions and the minimum detectable effect per regime.

Seeds, for author approval:
- 7,193,000-009: smoke;
- 010-099: plant checks;
- 100-299: tuning;
- 300-399: checkpoint and candidate selection;
- 400-499: stage-3 go/no-go;
- 500-699: exploratory head-to-head;
- 700-999: the one confirmatory run. If the power calculation needs more than 300 seeds, ask for a larger approved block;
- DRL training: 7,290,000-7,299,999, with disjoint per-learner pools.
A seed guard enforces these roles.
18. **[major, author] Condition 4 and side constraints: statistic, tolerance and consequence** (§5 condition 4 (l.153); §6 (l.161-162); sources stats-11, completeness-09, drl-02)
   - Issue: Condition 4 ('override-active minutes ≤ 1.1 × B_k's', l.153) is under-defined. It gives no statistic (sum, or a median per instance), no scope (pooled or per regime, although B_k is per regime) and no CI, and it requires exactly 0 when B_k has 0 minutes.
- **No tolerances.** Served-by-23:00 (l.161) has no tolerance, and per-ramp delay (l.162) is only reported. CLAUDE.md:89 requires 'side constraints with stated tolerances', and roadmap:301-302 sets 'on-ramp users' delay ≤ +10 %'.
- **Gaming route.** A candidate can win J by moving delay onto the 4 metered ramps.
- **Constraints that cannot bind.** The roadmap's safety-proxy and teleport constraints are structurally empty in METANET (lessons_metric_gameability.md §4), and the draft does not say so.
   - Fix: Per regime k, against B_k (as defined in the B_k item):
(4) the median per-instance queue-layer minutes ≤ max(1.1 × B_k's, B_k's + m0), with m0 fixed now (e.g. 10 min per day);
(5) the median per-instance total delay on the controlled ramps ≤ 1.10 × B_k's (the roadmap tolerance), and a breach blocks the PASS;
(6) vehicles served by 23:00 ≥ 99 % of B_k's (tolerance fixed now).
Report the maximum and 95th-percentile wait, the override onsets, and J split into mainline and ramp delay. State that the safety and teleport constraints do not apply in METANET, and why.
19. **[major] Specify every non-learning arm and its tuning (HERO law, CONST, ALINEA cells, budgets)** (§4 (l.99-108); §9 (l.186); sources comparators-10, comparators-08, comparators-13, plant-13, scope-07)
   - Issue: **HERO** (l.106-108) cannot be implemented from the text:
- E13 is both B1's master and B2's slave, with no rule for conflicting commands;
- v3 R13(c) (v3:1067) requires stating 'how queue balancing crosses B1', and the draft does not;
- the activation, release and slave laws and the queue source are open, and joint tuning with ALINEA is not stated.

**Tuning:**
- 'A common budget' (l.99) has no number; roadmap:24 rule 3 requires both budgets reported. For comparison, L1 gets ≈ 32,000 day-episodes per learner.
- The CONST-TOD grid {240, 400, …, 1,714} with 160 steps ends at 1,680, not 1,714.
- Coordinate descent over 16 parameters has no start, sweep count or stop rule.
- (K_R, ρ*) per ramp is an 8-D grid.
- No tuning is stated for MTFC or MPC-E, and the tuning objective, λ and regime mix are unstated.

**Missing baseline.** The plain all-day constant rate per ramp, the baseline that exposed R6 (r6plus_diag.md: 8.0 %), is not an explicit arm, although l.18 calls it mandatory.

**Measurement:**
- ALINEA's E9 cell contradicts the draft's own rule: S1770 (cell 19, km 0.370) is the first station downstream of the E9 gore (v4:88), not S1771 in cell 21, which lies past exits X9 and X10.
- The aggregation of measurements at 60-s decisions is not pinned.
   - Fix: (1) **HERO, written out:**
- activation when the master queue ≥ a·S_i and the master's ρ_s ≥ b·ρ*;
- slaves get minimum-queue targets that balance relative queues;
- release when the master queue ≤ c·S_i, or ρ_s < d·ρ* for m min;
- local layer = ALINEA plus the queue layer;
- E13 takes the lower of its two commands;
- state whether B2's cluster recruits E12 and E9 once E13 saturates, and why;
- tune (a, b, c, d) jointly with ALINEA, and keep [VERIFY] until Papamichail et al. 2010 is read in full.
(2) **CONST arm:** one rate per ramp all day (4 parameters). CONST-TOD's descent starts from CONST's optimum.
(3) **ALINEA cells:** E9 → 19 (S1770), E12 → 25, E13 → 32 (plus the upstream variant), E14 → 35. Every arm reads the 60-s mean of its station cell.
(4) **Tuning table, per arm:**
- the parameter vector and ranges, with the grid written out (e.g. {240, 400, …, 1,680, r_max});
- the method and its start, sweeps, stop rule and edge-extension rule;
- the number of day-evaluations;
- the instances: tuning seeds, λ = 1, and the same regime mix as L1's training;
- the objective: J as judged.
Report the learner and baseline budgets side by side.
20. **[major, author] R1-R13 disposition table, mode equivalence and controlled-path tests** (§1; §2 (l.30-31, l.61); §3; §5 stage 1; sources scope-04, plant-05)
   - Issue: v3 §7 binds R1-R13 on 'the controlled-plant and gate protocols' (v3:1053), and v5:612 keeps them 'not eased', but the draft cites them selectively.
- **R1(d) replaced silently.** R1(d) (v3:1055: mode C at replay meter rates must pass N0 and the deterministic rows) is replaced by M-EQ (l.31), which checks the stepper only against simulate() in replay and never tests the controlled path. R1(d) cannot pass literally anyway, because the frozen plant fails P1c, P2, P3-1, P4-1, P5a-1, P5b-1, P6-1 and P7a-1 in replay.
- **M-EQ is self-contradictory:** 'bit for bit' vs '≤ 1e-12'. A prototype achieved exact equality.
- **FIELD never meters E14.** FIELD (l.61) uses E14's Passage detector, which reads ≈ 1.58 × its Queue detector.
- **Other requirements:** R5 is moot (the record has 'members': []). R13(d) (B1 censoring at the real day's B2 onset) is undefined on generated days, and the R13(e) hypothesis locus is missing. R9 does not apply: synthetic slowdowns are D2.2.2's local slowdowns.
   - Fix: Add a table: R1-R13 × {adopted / adapted (how) / set aside (dated decision)}. Concretely:
- **M-EQ** = exact equality on the replay path.
- **R1(d), testbed form:** mode C at FIELD rates vs replay. FIELD uses each ramp's replay source; for E14 that is its Queue replay, i.e. unmetered, disclosed. Criteria: per-day J within 2 %, identical P_1/P_2 episode-day sets, N0 ≤ 1 %. It runs on the 22 days under inferential option (b), or on the 16 non-test days under option (a). R-NL is reported.
- **Controlled-path unit tests:** r_cmd ≥ demand reproduces NC exactly; vehicles are conserved (Σ arrivals = Σ releases + w_end); the queue-layer invariants hold.
- **R3(c)** → the MPC item. **R5:** 'no members; the mismatch row is report-only'. **R6** → the VSL item.
- **R13(d):** anchor B1 censoring at the same instance's NC B2 onset, which is arm-independent. **R13(e):** state the locus per bottleneck.
21. **[major, author] P0 fallback and demand reconciliation at the controlled ramps** (§2 demand (l.45-49); §5 P0 (l.142); sources plant-02)
   - Issue: L.142 says 'P0: valid on ≥ 80 % of ramp-days, otherwise the v3 R1 fallback'. v3 R1(c) (v3:1055) only says 'with a fallback'; no fallback is defined in v3-v5 or in hybrid_combinations.
- **The fallback will trigger.** E12 fails P0's totals criterion on 18 of 22 days, whatever s_jam is (median Queue − Passage = +8.85 %). Valid ramp-days are therefore at most 48/66 = 73 % (79.5 % with E14), so the fallback branch is certain.
- **No latent demand at E12.** L.48 already sends failing ramp-days to their Passage replay, so E12 runs without latent demand on 18 of 22 days.
- **Gaps.** The binding R1(e) detector-agreement listing and its reconciliation are omitted, and P0's time resolution and window are not pinned.
   - Fix: The author pre-registers the fallback.
- Recommended: on each failing ramp-day, keep the Queue-arrival timing and rescale it to the Passage daily total. This keeps the timing of latent demand and conserves the served volume; disclose it.
- Alternatives: the Passage replay (no latent demand), or dropping E12 as a controlled ramp.
Restate R1(e) with its listing (per ramp: the replay source, the mode-C demand source and their daily-total agreement) and the reconciliation. Pin P0 at 5-min bins over 04:00-23:00. Add a stage-1 report row: NC in mode C vs replay J, per source day.
22. **[major] Incident and slowdown: one capacity law each, vehicle-conserving, with start laws** (§3 generator (l.77-79, l.95); sources plant-08, plant-10, stats-03)
   - Issue: **Incident:**
- Scaling both the per-lane ρ_cr and λ by (λ−1)/λ (l.78) cuts capacity by ((λ−1)/λ)², because flow = ρ·v·λ (metanet.py:573). The B1 head falls from 3,560 to 890 veh/h, against 1,780 for a λ change alone; the 3-lane cells 24-26 get ×0.44 instead of ×0.67.
- Changing λ without rescaling ρ destroys or creates vehicles, since vehicles = ρ·L·λ (metanet.py:537, 607).
- A lower ρ_cr in cells 28 and 33 also cuts the E13/E14 supply term (metanet.py:582).
- Cells 25, 27 and 32 are station cells, which v4:113 keeps unscaled.
- The numerics checks use only the table's λ (metanet.py:798-812).

**Slowdown:**
- v_f × 0.7 at fixed ρ_cr is a 30 % capacity cut (3,560 → 2,492 veh/h), and the held-out × 0.5 halves capacity.
- G4 reuses vf3 (metanet.py:479-480), so the cell set is ambiguous.
- There is no start-time law, and 'weather-like' has no source.
   - Fix: **Incident:**
- λ_c → λ_c − 1 with the per-lane ρ_cr unchanged, so capacity scales by (λ−1)/λ;
- rescale ρ_c by λ_old/λ_new at both switch instants;
- state whether φ applies;
- exclude station cells, or state the consequence for the event layer;
- re-assert §A2 (a)-(f) for each modified table;
- disclose that the incident response is unvalidated.

**Slowdown:**
- state the cells (27-35 or 27-39);
- start ~ U(06:00, 20:00), or the chosen law;
- ramp v_f linearly over ≥ 5 min, or exclude the switch steps from the clip counts;
- state whether ρ_cr moves, and the capacity cut in veh/h;
- J's free-flow time uses the nominal v_f;
- drop 'weather-like' unless a source supports a 30 % cut [VERIFY].

Report the share of instances in which the disturbance binds (see the regimes item).
23. **[major] Pre-register the adaptation gain, H and G** (§4 O-a (l.116); §5 (l.147, l.155); sources stats-08, scope-09, comparators-07)
   - Issue: CLAUDE.md:31 requires the adaptation gain to be pre-registered ('the share of the fixed-tuned → per-day-tuned gap that the helper closes'), and D5.6 stage (4) lists it. CLAUDE.md:71 and :79 keep H and G as measured, report-only diagnostics.
The draft has only a per-regime 'adaptation gap' (O-a vs the best single-tuned arm, l.147). It has no per-day reference and no stage-4 row.
The binding texts disagree slightly: CLAUDE.md:31 says per-day tuning, D5.6 says per-regime. Report both.
   - Fix: Define the following, all report-only and fixed now.
- J_fixed,k: the best fixed-parameter (pooled-tuned) arm.
- Day oracle: CONST-TOD or ALINEA tuned per instance. Tuned on tuning instances for stage 2; re-tuned on test instances only after the look, and listed in the computation order.
- AG_k(day) = (J_fixed,k − J_cand,k)/(J_fixed,k − J_dayoracle,k), and AG_k(regime) with O-a^tune in the denominator. Both use paired medians with bootstrap CIs and Bonferroni over regimes; report 'n/a' when the denominator's CI includes 0.
- H per CLAUDE.md:72-74, with I = O-a^tune (a lookup on the hidden regime, tuned on tuning seeds).
- G per regime (T2).
These rows appear in stage 2 and in stage 4.
24. **[major, author] Robustness, artefact and numerics rows, with readings fixed now** (§1 (l.24); §2 (l.41); §3 (l.92-95); §5 (l.155); sources completeness-05, completeness-06, plant-12, scope-14)
   - Issue: The robustness rows (λ points, the mismatch plant, held-out severities, s_jam ±25 %) have no instances, comparator, re-tuning rule, statistic, multiplicity or reading. Yet 'robustness improvements' are a contribution type, and CLAUDE.md:30-32 requires the rows pre-registered and reported 'with multiplicity control'.
- **Artefacts.** The learner is the only arm that optimises directly against a plant with known weak spots: an exaggerated B1 drop, δ_m = 3.47, and a clipped share up to 0.77 % against the 1 % N0 limit (v3:437-438). It could also act implausibly for the field, e.g. jumping between 240 and r_max every 60 s. No artefact screen exists.
- **Health.** No health or N0 criterion exists; BN4's Addendum I had one.
- **Seed spread.** The candidate's seed-to-seed spread is not reported.
   - Fix: A row table: the instances (the test instances with the row's change, common random numbers), the arms, whether arms are re-tuned (recommended: no), and the statistic (candidate vs the B_k set and vs NC), with Bonferroni over rows × regimes.

**Readings, fixed now:**
- 'Robust' if and only if every condition-2 regime win keeps its sign in every row. Otherwise the PASS is labelled 'plant-dependent' or 'severity-dependent' (the R5 precedent, v3:1059).
- 'Robustness improvement' only through an Addendum-H-style degradation-ratio test (gscan:340).

**Artefact rows** (report-only; the PASS is labelled 'artefact-sensitive' if any fails):
- step-halving at T = 0.375 s: each win keeps its sign and ≥ 50 % of its size;
- the δ_m and low-drop variants;
- actuation statistics per arm: rate changes per hour, share at extreme levels, queue-layer onsets;
- a rate-change-limited version of the candidate (the limit law fixed now).

**Numerics:** report the clipped share and a non-finite flag per instance and arm. An instance above 1 % is flagged; if more than 5 % of any arm's stage-4 instances are flagged, the result is labelled numerics-limited.

**Seed spread:** add a row with every training seed's final policy of the candidate's learner type on test.
25. **[major, author] Stage-3 governance: candidate rule, stop rule, caps and ledger** (§4 (l.118, l.124, l.127); §5 (l.136); §8 (l.176); sources drl-07, drl-06, scope-08, stats-13, drl-05, comparators-13, scope-14)
   - Issue: **Candidate rule.** 'The best validation score among L1–L3' (l.127) defines no metric, λ, weights or instance set, and no rule for best checkpoint vs final policy. The binding text is itself split (CLAUDE.md:28 vs :90), and BN4 used best-validation checkpoints (gscan:291). A pooled pick can select a learner that fails conditions 3-4.

**Stop rule.** The stage-3 stop (l.136) has no margin, CI or comparator, and ends in 'author decides'. It is judged on the same validation instances that choose the checkpoints, so the winner's curse biases it towards spending the one look.

**Missing caps and records:**
- no cap on variants or pilots (BN4's hybrid needed 7 pilots);
- no 'selected from N' (roadmap:18);
- the ledger duty is not stated, although it binds anyway through CLAUDE.md:9;
- no L2/L3 budgets, against CLAUDE.md:27's same-budget rule.

**Convergence checks.** C1 has no consequence. All three BN4 vanilla learners failed C1, with best checkpoints at updates 1,950, 1,075 and 1,975. Roadmap C2 (beat the best constant on validation, roadmap:288) is missing.
   - Fix: (1) **Candidate rule.** Per learner, the checkpoint is the one with the lowest J on a fixed subset of 300-399, evaluated every 25 updates on the condition-1 population at λ = 1. A learner is eligible only if, on 300-399, rel vs the B_k set is ≤ +5 % in every regime and the condition 4-5 statistics hold. The candidate is the eligible learner with the lowest pooled J; if none is eligible, the lowest overall, disclosed. Report the final policy beside it, and freeze the candidate with SHA-256.
(2) **Go/no-go** on 400-499, touched once. Proceed only if the frozen candidate vs B_k^val has a median rel ≤ −3 % (or a Bonferroni CI upper bound < 0) in at least one regime, and a point rel ≤ +5 % in every regime. Otherwise stop; continuing needs a new protocol version, not 'author decides'.
(3) **Cap,** for example ≤ 1 pilot + ≤ 2 L1 configurations + L2 (+ L3 if kept), and a CPU-hour limit fixed now. Every run goes in the ledger, and claims say 'candidate selected from N policies'.
(4) **C1** is report-only, with one pre-registered +50 % extension if C1a or C1c fails and the best checkpoint lies in the last 10 % of training.
(5) **C2** is reported.
(6) **Labels:** stage-3 numbers are 'selection-optimistic'; operating-map labels are either Bonferroni-adjusted over all map comparisons or marked 'unadjusted, descriptive'.
26. **[major] L1 specification and information parity across arms** (§2 (l.32); §4 L1 (l.119-124); sources drl-04, drl-09, drl-10, comparators-11, drl-08, drl-14)
   - Issue: **Hyperparameters missing.** No γ, GAE, n_steps, batch, epochs, lr schedule, network, LSTM size, normaliser or observation scaling is given.

**Horizon.** The 60-s, 1,080-step episode is 36× BN4's 30-decision episode. Keeping γ = 0.99 gives a horizon of about 100 min, the regime that hybrid_combinations_v0.md:72-74 links to convergence failure (roadmap:276: 'horizon ≥ 3 × lag').

**Action set.** The 8 levels (l.121) are not listed, so the action set may not contain the tuned constant plan. BN4's Discrete(14) contained the tuned 1,800.

**Information parity.**
- L1 sees 5-min station aggregates (l.120) while deciding every 60 s, whereas ALINEA reads ρ_s every 60 s and BN4 used the last 20 s (bn4_env.py:3-5).
- L1 gets no density, no queue-layer flag and no realised release.
- L2's and L3's observations are not stated (CLAUDE.md:26: 'same observations').

**Training data.** L1's training mixture (λ, regime weights, source-day sampling) and its seed reuse (≈ 3× on 10,000 seeds) are not stated.

**Δc wording.** 'Δc = 60 s for every arm' (l.32) conflicts with MPC-E (5 min) and L2 (15 min).
   - Fix: Pre-register a hyperparameter table.
- Keep the BN4 values where unchanged: lr 3e-4, GAE 0.95, 10 epochs, 128×128, LSTM 64, ent 0.
- Fixed physical observation scaling (no VecNormalize), and the normaliser's value.
- γ justified by the horizon rule: either 60-s decisions with γ ≈ 0.995-0.997, or L1 deciding every 5 min with γ ≈ 0.98 (the meters still act at 60 s). Allow at most one ledgered pilot between the two, inside the stage-3 cap.

Action levels: the written-out CONST grid, e.g. MultiDiscrete(4 × 11).

One observation vector for L1, L2 and L3:
- per station, the 60-s mean flow, speed and density;
- ALINEA's 4 ρ_s;
- the queues divided by S_i, and the queue-layer flags;
- the last realised release;
- time of day as sin/cos;
- the previous action.

Fix the training mixture now: regimes at equal weight; λ = 1 or U(0.95, 1.05); base days as in the inferential-target item. Use disjoint per-learner seed pools and state the reuse factor.

Add an information table per arm (sensors, period, queue source, forecast, state), and state Δc per arm.

Reward: the plain −Δdelay is primary. The difference reward (R-DIFF, roadmap:273) is allowed only as one capped stage-3 variant, with the decision recorded.
27. **[major, author] L2 labels and the L3 decision** (§4 L2 and L3 (l.125-126); sources drl-01, drl-12)
   - Issue: **L2.** It imitates day-level regime labels every 15 min (l.125).
- An R-inc incident starts at U(06:00, 20:00) (l.78), so before onset the label cannot be inferred and the classifier learns base rates.
- R-B1 vs R-both shows mainly at the PM B2 breakdown.
- A 15-min cadence can switch only after a short incident has ended.
- There is no switch-in rule for ALINEA's integrator.

**L3.** It is optional (l.126), but D5.6(3) lists 'a DRL helper'.
- Under the same-budget rule (CLAUDE.md:27), L3 doubles DRL compute.
- The BN4 evidence argues against R6-type hybrids: the plain DRL beat the R6 hybrid by 43.8 % (r6plus.md:11), the tuned constant beat it by 8.0 % (r6plus_diag.md:14), and it showed no OOD advantage (r6plus_diag.md:20).
   - Fix: **L2.**
- Train on DRL-training seeds.
- Use time-resolved labels: label(t) = the O-a^tune set with the lowest remaining J from t onwards, computed batched from saved states.
- Decide every 5 min, and switch ALINEA in at the current commanded rate.
- Train L2 only in regimes whose stage-2 adaptation gap (O-a^tune vs the best fixed arm) is ≥ a threshold fixed now (e.g. 3 %). Otherwise report 'L2 not attempted', with the gap.

**L3.** The author decides. Recommended: drop L3 for this testbed, with a dated decision that records the departure from D5.6(3) and cites the BN4 evidence and the compute cost.
28. **[major] Compute plan: a batched closed-loop stepper and a CPU plan within the rules** (§4 (l.115, l.124); §9 (l.182-187); sources drl-03, drl-13)
   - Issue: Measured with venv314 on synthetic inputs with the frozen parameters, at load 1.5-2.7:
- **The plant is ≈ 3× slower than assumed.** Single-instance simulate() costs ≈ 157-176 µs per step, ≈ 14-18 s per day, against the ≤ 5 s that l.186 assumes. Batching helps: ≈ 1 s per instance-day at B = 16, ≈ 0.19 s at B = 264.
- **Gradient time is missing.** RecurrentPPO train() (1 thread) takes ≈ 17.5-18.2 s per update at 16 × 1,080, i.e. ≈ 10 h of serial gradient per learner, which §9 omits.
- **L1 as drafted** costs ≈ 128 CPU-h of plant per learner. Three learners × 17 processes = 51 processes would trip the > 90 % rule (CLAUDE.md:101-105) and exceed the 32-worker default.
- **Stage 2.** One CONST-TOD evaluation on 200 instance-days at B = 1 takes ≈ 48 CPU-min, so 'a few CPU-hours' holds only if batched.
- **MPC-E** exceeds its own 60-s cap (see the MPC item).
   - Fix: Make a batched closed-loop stepper a stage-1 requirement: B instances per numpy pass, controller state vectorised, queue layer included, with a logged timing check (e.g. ≤ 1.5 s per instance-day at B = 16).
Run L1 as one in-process batched VecEnv per learner (1 core each). Tune and evaluate every arm batched.
Rewrite §9 with the measured per-step and gradient costs, the validation and stage-4 costs, and a CPU plan:
- learners × processes ≤ 32;
- the guard and scheduler (vsl_lab/ops/guard.py);
- long jobs in their own systemd scope, as background jobs with an exit notification;
- a v6-overlap check before each batch.
29. **[major] Review schedule, v1 check round and plant pinning** (§1 (l.24); §9 (l.188); content deferred at l.24, l.40, l.70, l.72; sources scope-11, drl-13, completeness-08)
   - Issue: **Review schedule.** 'Reviews: this design review ... and one code checkpoint before stage 3's long runs. Nothing else.' (l.188) contradicts the binding phase table:
- CLAUDE.md:133 requires an adversarial checkpoint when the plant and all opponents are done, before the gate runs. As drafted, stage 2 decides the KILL on unreviewed code.
- CLAUDE.md:135 requires verification before a confirmatory result is reported.

**Unreviewed plant code.** metanet.py and metanet_inputs.py 'were reviewed by no lens' (metanet_v5_stop_verification.json, 'disclose').

**Deferred content.** The draft defers load-bearing content to 'the approved version': the SHA-256 (l.24), s_jam (l.40), the day lists (l.70) and the generator formulas (l.72). This review adds laws, budgets, maps and thresholds on top, and no check of that new text is scheduled. The D4.14 precedent is a review round plus a check round, with the logs in the protocol.
   - Fix: (1) v1 carries a disposition table: each finding ID → fixed (where), rejected (reason), or author decision (D-ID).
(2) Before v1 is committed as binding, run one ultracode check round limited to the new formulas, lists, laws and thresholds and to the dispositions. Append its log and record the round in the decision log.
(3) Run an ultracode adversarial code checkpoint after the stage-1 build and before stage 1b/2. Scope: metanet_ctrl.py, the queue layer, the generator, every non-learning arm, MPC-E and its identification, the batched env and the training code, plus an independent check of the metanet.py and metanet_inputs.py equations against v3/v4.
(4) Run ultracode verification before stage 4 is reported.
(5) Pin the plant in v1: the SHA-256 of frozen_params and the commit hash of the imported CODE_PATHS files. State that a later v5 §B11.2 re-run does not change the testbed plant unless a new testbed version says so.
30. **[minor] Scope sentence: full disclosure, and 'reinterpreted, not rescued'** (§0 scope sentence and Not in scope (l.9, l.11-14); sources scope-05, scope-03)
   - Issue: v5:597 (B13.1) requires every result to state 'plant selected after 3 attempts (listed)'; the draft never says it.
- **Undisclosed failures.** The record shows 12 of the 24 screened rows failed. The exaggerated B1 drop (P5b-1) and the B1 discharge of −5.6 % (P5a-1) bear directly on a metering gain and are not named.
- **Ambiguous phrase.** 'So that a later realism gate stays possible' (l.13) can be read as reopening the stopped v5 plant on the 97 days (v5:366, :531-535; D5.6: 'reinterpreted, not rescued').
The finding is partly refuted: the sentence mirrors D5.6's chosen wording and already says the demand is generated from the 22 days.
   - Fix: Scope sentence: '... calibrated to 22 Wednesdays of 2023, selected after 3 plant attempts, not validated (protocol v5 stopped at its in-sample screen: 12 of 24 screened rows failed, including B1 occurrence 16/22, B1 discharge −5.6 % and an exaggerated B1 drop), deterministic capacity, driven by demand days generated from the same 22 days [, ramp metering only].'
Not in scope: 'Track E is reinterpreted, not rescued (D5.6). The v5 plant is never gated on the 97 days; they stay reserved for a later plant (attempt ≥ 4) under a new dated decision.'
31. **[minor] Generator details to pin** (§3 generator (l.72-76, l.81); sources plant-14, completeness-10)
   - Issue: Not pinned:
- whether β is shifted and stretched with demand;
- padding when a ±30-min shift runs past 04:00-23:00 (metanet.py:30-31);
- the warm-up inputs (the initial state is propagated from bin 0, metanet.py:519-535);
- whether the P0 source choice comes before the noise;
- the PM-peak window and its centre;
- whole-day vs window-only shift, and the edge blending.
A stretch about the peak centre at fixed rates changes the window's volume by ±10 %, which confounds the stretch with λ. The review's ICC check used no stretch, so the generator as drafted has not been exercised.
   - Fix: Under inferential option (b), these become the generator-model spec. State:
- P0 source selection per source day, before the generator;
- β shifted and stretched with demand (or held, with the reason);
- padding = hold the first or last bin;
- 04:00-05:00 inputs untransformed;
- the peak window per source day, by a rule from that day's station-flow profile;
- whole-day or window-only shift, with the blending rule;
- a volume-conserving stretch (renormalised to the window's source volume × λ).
Report each instance's realised daily and PM volume relative to its source, and define λ on the realised daily volume.
32. **[minor] Units, citations and loose definitions** (§0 (l.21); §2 (l.43); §3 (l.81); §6 (l.158, l.163); sources stats-14, scope-14)
   - Issue: **Units.** The rel thresholds apply to total delay (l.158, consistent with CLAUDE.md:87). On this plant delay is ≈ 22 % of mainline TTS, so 10 % of delay ≈ 2.2 % of TTS. BN4's J was door-to-door time, and the literature anchor '≈ 2–9 %' (l.21) has no unit: frejo2.txt reports both TTS and delay reductions, and its 18.0 vs 20.6 % figures are delay (:1264).

**Loose definitions:**
- 'The refined λ rule' (l.81) is defined nowhere in the repo.
- Hegyi's α = 0.1 (l.43) lacks [VERIFY], which v3:458-460 has.
- The ARC-IT TM20/TM21 mapping is absent. It is a thesis-level rule (CLAUDE.md:44), optional here.
   - Fix: Put the unit beside every percentage. For each bar comparison, report absolute veh·h, rel-to-delay and rel-to-TTS. Never place a delay-% next to BN4's time-% or a literature TTS-% without units, and check the unit of the 2–9 % anchor in its source.
Define the λ rule in the text and cite where it was decided (D4.11/D4.12). Mark α = 0.1 [VERIFY].
Optionally, add one paragraph mapping the arms to ARC-IT service packages, checked against the v6 ARC-IT export [VERIFY].

## Author decisions (with the review's recommendation)

1. **Inferential target: what population does a stage-4 claim generalise to?**
   - Recommended: (b) Fit a multi-peak day generator (D2.3.3) on the 12 train-source days only, and draw every instance as an independent whole new day. The instance bootstrap is then valid for the declared synthetic population. The 6 held-out real days become a report-only 'held-out real day shapes' row, analysed with a two-stage bootstrap.
   - Options: (a) Keep g on real days; the two-stage bootstrap is primary; claims are day-conditional on the 6 listed test days (per-regime Bonferroni wins then become practically unreachable) | (b) New-day generator fitted on the train-source days, plus a held-out real-day row | (c) K-fold rotation over the 22 days with retraining (cost ×K)
2. **Deterministic plant and drop guards: do v3 R3(b) and R4(d), the latter bound by D4.7, apply to the D5.6 testbed?**
   - Recommended: Set R3(b) aside for this testbed by a dated decision, and label any PASS 'deterministic synthetic-testbed result, never a gate GO'. Keep R4(d): the bar must also hold on the low-drop variant. Add T1 to stage 1, and report-only δ_m and capacity-perturbation rows.
   - Options: R3(b) set aside, R4(d) kept as a PASS condition, T1 added (recommended) | R3(b) and R4(d) both set aside; the scope sentence names the exaggerated B1 drop (P5b-1 FAIL) | R3(b) applies: the testbed can only KILL
3. **Add a non-learning adaptive switcher (SW) to the B_k set?**
   - Recommended: Yes. SW is a rule-based detector, tuned on tuning instances, that switches among the O-a^tune parameter sets. A regime win must also hold against SW.
   - Options: Add SW (and optionally an occupancy-adaptive ALINEA) to the B_k set | Do not add SW; word every claim 'against fixed-parameter controllers only' and drop the disturbance-regime framing
4. **Ramp-queue handling: what form does the common rule take (v3 R1(b))?**
   - Recommended: One IRIS-style queue-protection layer for every arm, learners included: r_eff = max(r_cmd, r_wait, r_stor), evaluated every step, with a hard safety net at S_i, never above supply, and ALINEA anti-windup.
   - Options: Common queue-protection layer for every arm (recommended) | Queue-control floor for the non-learning arms only, with a shared, pinned Q_O flush override | Keep the Q_O flush for every arm, pinned (per step, hysteresis, anti-windup), with flags given to L1
5. **Stage-1 authority: s_jam, the consequences of a T0-M FAIL, and an early informed screen?**
   - Recommended: s_jam = the IRIS jam density of 180 veh per lane-mile (8.94 m) [VERIFY], with the ±25 % row. A T0-M FAIL at both heads is a KILL; a FAIL at one head drops the regimes that depend on it. Add a stage 1b authority screen with a true-model, perfect-forecast MPC before the costly arms are built.
   - Options: s_jam = 8.94 m (IRIS), plus the T0-M consequences and the stage 1b screen (recommended) | s_jam = 7.5 m (vehicle-length convention), same consequences | s_jam = 1/ρ_max ≈ 5.6 m, same consequences | No stage 1b; rely on the stage-2 KILL only
6. **Condition-1 population, and the stage-2 KILL rule?**
   - Recommended: Condition 1 on the undisturbed instances at their natural generator frequency, with the 4-regime pool reported. The stage-2 KILL is evaluated on that same population, against the full envelope (tuned arms, SW, O-a^tune, day oracle, informed MPC). Record the deviation from D5.6's per-regime wording.
   - Options: Undisturbed natural mix plus the informed-envelope KILL on the same population (recommended) | 4-regime equal pool with fixed equal counts; KILL per regime as in D5.6 | Mixture with a cited incident and slowdown frequency [VERIFY a source]
7. **Regime definitions and the day-pattern hypothesis (H1) and surges (D2.2.2)?**
   - Recommended: Label the undisturbed regimes from each instance's NC run, arm-independently and with quota sampling. Add R-atypical (demand-pattern tails) and R-surge (ramp-demand spikes), with Bonferroni over 6 regimes.
   - Options: NC-run labels, plus R-atypical and R-surge (recommended) | NC-run labels only; a dated decision that the testbed does not test H1 or surges, stated in the scope sentence | Keep source-day labels, renamed S-noB2 / S-B2, and report the simulated occurrence
8. **B_k comparator rule for conditions 2-3?**
   - Recommended: Intersection-union against every arm in an explicitly listed set that includes NC as a floor and excludes FIELD, both O-a's, the oracles and the reference MPCs.
   - Options: Intersection-union over the listed set (recommended, stricter) | As drafted: the single arm with the lowest median J per regime, chosen on the test set as in Addendum I
9. **Condition 2: require a minimum relevant effect?**
   - Recommended: Yes. Require a point rel ≤ −5 % and a Bonferroni CI upper bound < 0, symmetric with condition 3's 5 % (stricter than D5.8, so it needs a dated decision). Add a per-regime label for non-inferiority shown or not shown.
   - Options: A symmetric −5 % margin (recommended) | D5.8 unchanged, with a 'detectable, below the 5 % relevance threshold' label and rel always printed with its CI
10. **Side constraints: tolerances and consequences for override minutes, ramp delay and vehicles served?**
   - Recommended: Per regime vs B_k: queue-layer minutes ≤ max(1.1×, +10 min per day); controlled-ramp delay ≤ +10 % (roadmap), which blocks the PASS when breached; vehicles served by 23:00 ≥ 99 % of B_k's.
   - Options: Blocking tolerances as recommended | The same tolerances, reported as labels only (no PASS block)
11. **Which extra metering laws enter the comparator set, and which release range?**
   - Recommended: Add CONST, DA (field defaults and tuned), UP-ALINEA for E13 at S1147, and a PI-ALINEA variant [VERIFY its source]. Add LB-TFC only if VSL stays in. Use the IRIS range of 240-1,800 veh/h [VERIFY] for every arm.
   - Options: The full recommended set, with the IRIS range | CONST and DA only; claims worded 'the best of {list}' | As drafted, with the SZM range of 240-1,714; claims worded 'the best of {list}'
12. **VSL: in or out, decided before data?**
   - Recommended: Out for this testbed. The implemented min form has little static authority (≤ 3.3 % at α = 0.1, inert for b ≥ 80), the modified-FD form is not implemented, and learners would need a VSL head. Word the claim 'ramp metering only'.
   - Options: Out (recommended) | In, with the full v3 R6 restatement (both forms, α ∈ {0, 0.1, 0.2}, no new bottleneck), an MTFC law, and a VSL action for L1, L3 and MPC-E
13. **L3 (R6-type DRL hybrid): in or out?**
   - Recommended: Out, with a dated decision recording the departure from D5.6(3), citing the BN4 evidence (plain DRL beat R6 by 43.8 %; no OOD advantage) and the doubled compute under the same-budget rule.
   - Options: Drop L3 (recommended) | Keep L3 at L1's budget
14. **P0 fallback for controlled ramps that fail P0 (E12 is certain to fail)?**
   - Recommended: Keep the Queue-arrival timing, rescaled to the Passage daily total on each failing ramp-day, disclosed.
   - Options: Rescaled Queue timing (recommended) | Passage replay (no latent demand), as the draft's l.48 implies | Drop E12 as a controlled ramp
15. **Seed blocks and roles?**
   - Recommended: Use 7,193,000-999 with 300-399 for selection, 400-499 for the stage-3 go/no-go, 500-699 for exploratory head-to-head and 700-999 for the one confirmatory run. DRL training on 7,290,000-7,299,999 (track digit 9). Enlarge the confirmatory block if the power calculation needs it.
   - Options: The recommended layout | As drafted (stage 4 on 500-699, DRL on 7,280,000-7,289,999), with the role swap justified
16. **Outcome rules: claim level, DRL-alone eligibility and time box?**
   - Recommended: Chapter-level, declared synthetic testbed; run once and report whatever it is; W13-strict for post-look fixes; a FAIL closes this claim path. D5.8 governs (DRL alone may be the candidate), and CLAUDE.md:17 and :89 are corrected. A calendar time box for stages 1-2 and 3-4 is set by the author.
   - Options: As recommended | Paper-level claim (would need a realism argument the plant lacks) | CLAUDE.md:17 governs: DRL alone is a reference only, so L2 (or L3) is the only possible candidate
17. **Drain rule (draft author item 4)?**
   - Recommended: NC for every arm from 23:00 and during the 04:00-05:00 warm-up; drain until empty with a 2-h cap and a fixed penalty per remaining vehicle; L1 gets a terminal drain reward, so its return equals −J.
   - Options: As recommended | Each arm keeps its own law after 23:00 (L1 would then act outside its training domain)
18. **Stage-3 stop rule and cap?**
   - Recommended: A go/no-go on 400-499, touched once: rel ≤ −3 % (or a Bonferroni CI upper bound < 0) in at least one regime and ≤ +5 % in every regime, else stop and write a new protocol version. Cap of ≤ 1 pilot + ≤ 2 L1 configurations + L2, with a CPU-hour limit fixed now.
   - Options: As recommended | Keep 'author decides' (open forking path)
19. **R1-R13 set-asides?**
   - Recommended: Adopt the disposition table: a testbed form of R1(d) (FIELD vs replay with tolerances), R1(e) restated, R3(c) met by refitting the MPC, R5 moot, R6 per the VSL decision, R13(d) anchored at the NC B2 onset, and R13(e) stated. Each set-aside gets a dated decision.
   - Options: Adopt the table as recommended | Set the R1(d) equivalence check aside entirely (dated decision; weaker)
