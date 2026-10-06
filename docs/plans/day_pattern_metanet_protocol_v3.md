# U.S.169 SB METANET plant: calibration and plant gate (protocol v3)

*2026-10-05. Branch `claude/day-pattern-core`. Replaces `day_pattern_metanet_protocol_v2.md` (uncommitted draft) after design-review round 3 (12 kept issues, `/home/catalin/work/phd/dp_data/metanet_review3_kept.json`; one row per issue in Appendix C). v2 replaced `day_pattern_metanet_protocol_v1.md` (committed in `23a891e` as review input, not binding) after round 2 (24 kept issues, `metanet_review2_kept.json`; Appendix B). The round-1 resolutions stay in Appendix A. Decisions D3.1–D3.5 (`day_pattern_decisions_v0.md`), in particular **D3.4** (two bottlenecks in series) and **D3.5** (boundary distance accepted). Data facts: `docs/lab/day_pattern/us169_data_facts.json` (commit `edde7d2`).*

*Status: DRAFT. It becomes binding when committed, after the author has answered the items in §0.6, and that commit precedes any calibration run, any pre-calibration data fact in §3.6 and any model run on real data. No model has been run. The read-only data inspections made for this file are listed in §0.5 (items 7–8).*

*Main changes against v2 (round 3; Appendix C):*
- *B1 now has its own fitted head-capacity factor θ1 on its merge cell (§2.1, §4.1), and the B2/B1 merge-section flow ratio is a pre-calibration fact and a gated row (F8, P5c).*
- *B1 activity is detected at the pair (S of Highwood Ave, Pioneer Tr) on all lanes, through amendment EA-2, instead of through the single Anderson Lakes Pkwy lane 5423 (EA-1, now a reported sensitivity). Model speeds are converted to detector scale before every event rule (§3.2.1, §3.2.4, §5.1).*
- *B1 episodes cut short by B2 are treated as right-censored (§5.1), and a system-level duration row is added (P7c).*
- *The extra-episode check P8(iii) is added, and P8(i) now scales with n_val.*
- *The stochastic plant gets support bounds (c2\*), a spurious-head condition, the numerics rows N0s and P8s, family-wise sizing of its sized tests, and a non-inferiority P10b. The "deterministic-only" consequence is fixed now (§0.3, §4.7, §5.3).*
- *v_min clipping in non-jam cells now counts in the clipping limits, and step-halving is gated (§2.5).*
- *The fit-layer gap rule and windows are fixed (§3.2.2), and so is c_s for T.H.101 (§3.2.4).*
- *The validation-set extension is pre-registered (§5.2). Its data (all 2023 Tuesdays and Thursdays) are pre-fetched at the author's request of 2026-10-05 and may be used only if the extension rule triggers (§0.6 A10, resolved; §5.2).*

---

## 0. Purpose, scope and what is at stake

### 0.1 Purpose

Build the macroscopic plant on which the day-pattern headroom gate runs (decision P6b: a METANET gate with SUMO confirmation), and show **before any controller is tuned on it** that it reproduces the real U.S.169 SB corridor, **a two-bottleneck system** (D3.4, §0.7), on days it was not fitted to.

### 0.2 What a PASS certifies, and what it does not

- **Certified (outcome PASS, §0.3):** the mainline response of the uncontrolled corridor to **replayed** 2023 Wednesday inflows (field metering already contained in the replayed ramp flows), at 5-min / station resolution, for **both bottlenecks B1 and B2**:
  - the fit, and where the day's first breakdown occurs;
  - whether and when each bottleneck breaks down, its discharge, no exaggerated drop and no exaggerated pre-breakdown overshoot;
  - the demand dependence of breakdown at each bottleneck;
  - the ratio of the two heads' merge-section discharge (P5c), **only when P5c is gated** (n_H,both ≥ 6, §5.2, and F10's option (c) not triggered);
  - the duration of each bottleneck's episodes (B1's censored by B2's onset where B2 hides it, §5.1), the duration of the system queue (P7c), and the extent of the corridor queue from its most upstream head;
  - no spurious bottlenecks elsewhere, no extra episodes at the two bottlenecks, and the clipping mechanism at the first-active bottleneck (§5);
  - the calibration of the **stochastic plant's** day-level breakdown probabilities at each bottleneck under the capacity distribution F̂, and its numerics and freedom from spurious heads under the draws (N0s, P8s, P6s, P10; §4.7, §5.3).

  **Caveat (option (c) of F10).** If F10's scale-robustness rule triggers option (c) (§3.6), the B1 rows, P5c and B1's part of P2, P7b, P7c, P8(iii), P8s (its B1 criterion) and P9 are reported only, and c1 is not estimated. A PASS then certifies the items above **for B2 only** (and F̂ only for c2), and the outcome record states this.
- **Certified (outcome PASS, substitute spread):** as PASS, with the pre-registered Tobit spread F̂_T in place of the Kaplan–Meier F̂ (§4.7); every result carries the label.
- **Certified (outcome PASS, deterministic-only):** everything above except the last item. No capacity distribution may then be used, and the gate may yield a KILL but never a GO (§0.3, §7 R3).
- **Not certified:**
  - the plant's response to **metering rates other than the field ones** (no 2023 day with different field metering exists here). That response is an extrapolation of a calibrated model; every gate result inherits it, and the SUMO confirmation (P6b) is the only independent check;
  - ramp-queue and ramp-capacity behaviour under simulated metering (controlled mode, §2.7; required in a later protocol, §7 R1);
  - the **speed-limit (VSL) response**: the corridor has no VSL, so it is assumed (§2.8), never validated here;
  - true demand at the unmetered freeway-to-freeway merges on days when the corridor queue reaches them (their counts are served flows, §3.3.3);
  - **F̂ beyond day-level breakdown probabilities:** the within-day behaviour of capacity, its dependence on demand or weather, the joint structure of (c1, c2) beyond what days with both factors observed show, and the re-centring (§4.7), which is an imposed choice;
  - **B1 queues that do not reach S of Highwood Ave.** B1 activity is detected at the pair (S of Highwood Ave, Pioneer Tr), 3.145 km, through amendment EA-2 (§3.2.1). A B1 queue that stays between the 3 → 2 lane end (km 3.751) and S of Highwood Ave (km 2.893), 0.86 km upstream of it, is invisible on both sides. Model speeds are compared on detector scale (v_model / c_s, §3.2.4). Speed-dependent detector bias beyond c_s is not corrected; the scale-robustness rule of F10 bounds its effect on B1's day status;
  - **B1's duration on days when B2's queue reaches Pioneer Tr.** It is right-censored at the real B2 onset (§5.1), so B1's own recovery is not observed on those days;
  - **the head-capacity factor θ1** (§4.1) is a fitted substitute for a lane-drop mechanism that the model does not resolve (the 3 → 2 exit-lane end at km 3.751 plus the E13 merge). It is motivated by the geometry, not validated as a mechanism;
  - **the merge reading at B2** (§1.3) is a modelling choice made on the data's head location; the configuration's weave reading is run only as a reported sensitivity.

### 0.3 Outcomes

- **PASS:** N0 and every deterministic row (P1–P9, at c1 = c2 = 1) pass. F̂ is estimable (§4.7). Every stochastic row (N0s, P8s, P6s, P10; §5.3) passes. The plant, its ensemble (§4.6) and F̂ may be used by the gate protocol (§7 R3).
- **PASS, substitute spread (new; round 3, issues 6 and 11):** N0 and every deterministic row pass. The Kaplan–Meier F̂ is not estimable **only** by rule (ii) or (iii) of §4.7, and the pre-registered substitute F̂_T (Tobit, §4.7) is usable. Every stochastic row passes under F̂_T. The gate may then use F̂_T in place of F̂, by the same R3 rule, and every result carries the label "substitute spread".
- **PASS, deterministic-only:** N0 and every deterministic row pass, but no usable spread passes every stochastic row. This covers four cases:
  - F̂ is not estimable by rule (i) or (iv);
  - F̂_T is not usable;
  - a stochastic row fails under F̂;
  - a stochastic row fails under F̂_T.

  When a stochastic row fails under F̂, F̂_T is **not** tried: the substitute replaces a spread that could not be estimated, never one that was estimated and failed.

  **Consequence, fixed now (round 3, issues 6 (iii) and 11; author item A4):**
  - no capacity distribution may be used;
  - the gate protocol may run the headroom gate on the deterministic plant (c1 = c2 = 1), but on that plant **only a KILL counts**. A GO there is recorded as "deterministic-plant GO, not a GO" and supports no claim. The reason: the deterministic plant is the over-predictable plant that the capacity factor was introduced to avoid (round 1, issue 11), so a GO on it is exposed to a false GO, while a KILL on it is conservative. That direction is an inference, not tested;
  - no later author decision may change this consequence after the stochastic results are seen.

  F1 is not fitted for this outcome, because its post-breakdown switch cannot change breakdown occurrence (§6.1).
- **FAIL:** a deterministic row fails. The single pre-registered structural fallback F1 (§6.1) is fitted only if the failure set includes a check that F1 can affect (§6.1 trigger); otherwise the outcome is a route stop. Both outcomes are logged.
- **INCONCLUSIVE:** the real-data minimum evidence (§5.2) is not met. It is decided **on real data only, before the model is run on any day** (§8.6 step 3). It is never a PASS and it does not trigger F1. It triggers the pre-registered extension of §5.2: the pre-fetched 2023 Tuesdays and Thursdays (A10) are cleaned and checked before calibration. If the minima still fail after the extension, INCONCLUSIVE is final.
- **Route stop:** a plant that fails as built (with F1 not triggered, or F1 also failing) stops the METANET route. Whether the track continues on a SUMO plant (with its own realism protocol) is an author decision, recorded in the decision log.

### 0.4 The capacity drop (C4 deviation, D3.1)

The real drops are small and not stable across subsets:
- **B2** (corridor-protocol estimator at Old Shakopee Rd), all 23 episode Wednesdays: median r = 0.984 (IQR 0.952–1.001). Earlier splits (data facts; **the v0 odd/even and calendar halves, not the split of §3.1**): odd 1-based index 0.997 (n = 11), even 0.961 (n = 12); first half 0.964 (n = 9), second half 0.991 (n = 14).
- **B1** (reviewer read-only estimate at the Pioneer Tr station, not reproduced for this file): r = 0.986 (IQR 0.947–1.024), discharge 1,696 veh/h/lane. That estimate used the EA-1 pair (Anderson Lakes Pkwy via 5423, Pioneer Tr) and did not cut the window at B2's onset. It is recomputed on calibration days in F8 with v3's B1 definition and the censored C4 window (§5.1).

These data cannot pin the size of either drop, and they cannot exclude a drop of zero. The plant is therefore gated at each bottleneck on:
- **discharge** (two-sided, P5a);
- **a paired one-sided drop bound** (P5b: the model's r may not fall more than 0.02 below the real r on the same days, and its median may not fall below a floor L_r,k frozen from real data before any model run);
- **a paired pre-breakdown overshoot bound** (P9(1)), which is a second drop-side constraint and is stated as such.

**Why one-sided, and what is inference.** A plant with more drop than the data support is *expected* to inflate the prize of preventing breakdown, and with it the headroom, which risks a false GO; too little drop is expected to understate that prize (conservative for a GO). This monotonicity of H in the drop is **an inference, not tested**. The **operative guard** against a drop-driven false GO is R4: a GO must also hold on the low-drop variant (§7). The drop is **not** a term of J.

*Wording change for D3.1 (for the author to record; this file does not edit the log): "the real drop becomes the plant's calibration target" → "the real drop is a paired one-sided validation bound at each bottleneck".*

### 0.5 Inspections made before this protocol (disclosed)

These were made on 2023 data with no model fitted. They informed design choices, which is disclosed here; no threshold below was tuned on model output (no model exists).
1. `us169_data_facts.json` (all 52 Wednesdays): upstream-boundary candidates; Pioneer Tr passage vs mainline balance (15:00–19:00 median ratio 1.235, n = 51); I-494 merges' share of PM inflow (median 0.376, n = 52); queue reach to Highwood Ave when Pioneer Tr is congested (37 of 38 days, coarse indicator); drop r by v0 splits.
2. Reviewer read-only checks (round 1), on cached files: link residuals, Pioneer Tr passage/queue ratio (daily median 1.56), dead lane 5424 at Anderson Lakes Pkwy (43/52 Wednesdays), lane field lengths and free-flow speeds, peak merge flows, and two day-agnostic null predictors evaluated on 26 Wednesdays used as validation days under a different split (whole-day NRMSE_v: constant free-flow speed 0.126, median profile 0.085; median-profile NRMSE_q 0.123 on a different station set; in km 0.37–7.20 × 15:00–19:00: 0.30 and 0.21). About half of those days are validation days under §3.1.
3. The configuration (`metro_config.xml.gz`) was parsed for v1 (element table, lane sequence, cells). Geometry, not traffic data.
4. Detector availability in the cached Mayfly lists (`_detectors.json`) for the detectors of the stretch (§3.7).
5. **Reviewer read-only checks (round 2), on the cached 2023 Wednesdays, all 52 including validation days.** None was reproduced for this file; each number is the reviewer's estimate:
   - *Downstream flows (issue 0):* median daily maximum 15-min flow downstream of the Old Shakopee Rd entrance (= T.H.101 station + X14 + X15) 5,132 veh/h, against 4,004 veh/h at the Old Shakopee Rd station (n = 51); 5,156 vs 3,932 on the 23 B2 days (higher on 23/23); 15:00–19:00 means ≈ 4,300–4,600 veh/h on B2 days with T.H.101 at a median 69.5 mph during B2 episodes; class-B E15 ≈ 750 veh/h PM median (up to ≈ 1,130).
   - *Head location at B2 (issue 2):* during B2 (545 episode bins) the Old Shakopee Rd station is at a median 56.7 mph (≈ 20 veh/km/lane) and Pioneer Tr at 26.1 mph.
   - *Ramp detectors (issues 3, 21):* Passage/balance and Queue/balance (day, PM): E13 2.09/1.17 and 2.06/1.14; E12 0.50/0.65 and 0.55/0.76; E14 1.50/1.235 and 0.964/0.960; E4 Passage 1.20/1.12. Calibration-day daily totals (Passage, Queue, balance): E12 1,280 / 1,402 / 2,548; E13 1,710 / 1,681 / 801; E14 7,090 / 4,498 / 4,618. Highwood Ave → S of Highwood Ave: e median 2.6 %, > 3 % on 7 % of days.
   - *Undetected exits (issue 4):* PM station differences without storage: X6+X7 ≈ 1,450, X9 ≈ 230, X10 ≈ 510 veh/h.
   - *The upstream bottleneck B1 (issue 20):* see §0.7.
   - *Flow stations (issue 22):* S of Valley View Rd below 45 mph during B2 on 0/23 B2 days; links upstream close within a median 0.1–1.8 %; T.H.7 EB PM ratio 0.894; Excelsior Blvd 1.194 (day) / 1.122 (PM).
   - *Merge replay (issue 23):* the I-494 merge counts fall to a median 0.89 (IQR 0.84–0.94, n = 50) of their pre-queue level within 15–60 min after the S of Highwood Ave through lanes drop below 40 mph (not controlled for time of day); Highwood Ave below 45 mph in ≥ 30 % of B2-episode bins on 20/23 B2 days.

   They informed: the two-bottleneck definition and the event-layer amendment (§0.7, §3.2.1); the merge reading at B2 (§1.3); F16 and its resolution rule (§1.7); the ramp rule and the shared-station test (§3.3.2, §3.4); the arrival definition in P9 (§5.4); the congestion-window flow term (§4.2); the no-leak replay and R2 (§3.3.3, §7). **Because these inspections included validation days, the B1 definition and these structural choices were made with knowledge of real validation-day behaviour** (never of model behaviour). Thresholds new in v2 are lab conventions (§9.2), except where a reviewer value is adopted, which the row says.
6. **This rewrite** re-read the configuration's r_nodes for km 3.4–9.6 (geometry only: it confirms the §1.3 reading; no lane is recorded at the Old Shakopee Rd entrance, whose shift equals the mainline's, and rnd_144 and rnd_145 record 2 lanes) and the ramp detector categories (§1.2), and counted the stretch's detectors (86 in the configuration, plus the Auxiliary 7097 and 7077) for the request bound in §5.2. No traffic data were opened. *(v3: the recount in item 8 gives 87, not 88; §5.2 uses 87.)*
7. **Reviewer read-only checks (round 3), on the cached 2023 Wednesdays.** Most used all 52 Wednesdays, **validation days included**. None was reproduced for this file, except where item 8 says so; each number is the reviewer's estimate.
   - *Head capacities (issue 0):*
     - merge-section flow per lane in B_k discharge, (downstream station + exit)/2: B1 1,745 veh/h/lane (IQR 1,711–1,811, n = 28); B2 1,950 (IQR 1,876–1,974, n = 23);
     - on the 16 days heavy at both: B2 above B1 by a median 11.4 %, and higher on 16/16 days;
     - pre-onset 15-min maximum: 1,846 (B1) against 2,074 (B2);
     - exits during discharge: X12 ≈ 83 and X13 ≈ 204 veh/h.
   - *B1 on one lane (issues 3, 8):*
     - the EA-1 pair (Anderson Lakes Pkwy via 5423, Pioneer Tr; v2's P_1, not v3's) on raw 5423 speeds: active 27/51 days; with c_s applied to the event speed: 8/51;
     - on validation days: 13/23 against 5/23 (issue 3). On usable days (issue 8, with §3.5 rules approximated): calibration 12 raw / 3 scaled, validation 10 / 3; the pair (S of Highwood Ave, Pioneer Tr): 23 and 15;
     - on the 9 Wednesdays with 5424 alive, 5423 alone flags B1 on 5 days and the two-lane station on 2. 05–06 medians on those days: 5423 63.8, 5424 80.3, both lanes 69.7, Pioneer Tr 73.3 mph;
     - on 15 of 39 usable days, S of Highwood Ave is below 40 mph for ≥ 60 min with no episode at the EA-1 pair (v2's P_1). This does not contradict the 23 + 15 = 38 of 39 days of the EA-2 pair (v3's P_1) above.
   - *c_s (issue 4):* calibration-day 05–06 medians AL 62.5, PT 71.8, OSR 70.9, T.H.101 62.7 mph.
   - *Usable days (issue 9; calibration and validation):*
     - exclusions: E1-B 1, E2 4, E3(i) 4, E3(ii) 2, class-B clipping 4;
     - usable: 23/28 calibration and 16/24 validation days under the reading "only long-gap bins are invalid", and 15 validation days under "any gap > 15 min invalidates the lane-day", because 2023-04-12 is lost through E5, X4 and Lincoln Dr;
     - validation counts (with the EA-1 B1 definition): n_A,1 = 10, n_A,2 = 9, n_H,1 = 10, n_H,2 = 9, n_H,first = 14;
     - Pioneer Tr → Old Shakopee Rd: e ≈ 4.8 % median if E14 keeps Passage.
   - *Censoring (issue 10):* on 8 of 13 usable two-bottleneck days, B1's last episode before B2 ends within 30 min of B2's onset.
   - *Estimability (issue 11):* 23 usable calibration days; B2 real-active on 9; B1 (EA-1) on 12; either on 13.

   They informed: θ1 and P5c (§2.1, §4.1, §5.3); the B1 definition EA-2 and the observation operator (§3.2.1, §3.2.4, §5.1); the gap and window rule (§3.2.2); the B1 censoring (§5.1); the extension pre-registration (§5.2, A10); the substitute spread and the deterministic-only consequence (§0.3, §4.7). **Because these inspections included validation days, these v3 choices were made with knowledge of real validation-day behaviour** (never of model behaviour). In particular, the gap rule of §3.2.2 was fixed knowing that it decides between n_val = 16 and 15. It was fixed on the ground that the model cannot run on a missing input, and the extension of §5.2 removes the dependence of "gate runs or not" on that choice.
8. **This rewrite's own read-only inspection (v3), on the 28 calibration Wednesdays only, with no §3 exclusions applied** (committed corridor estimator `station_day`/`episodes`, raw unless stated). No validation day was opened.
   - Median 05:00–06:00 speeds (mph):
     - S of Highwood Ave all three lanes 61.3, through lanes 7078/7079 61.1, Auxiliary 7077 63.1;
     - S of Valley View Rd 66.9, I-494 (with 7097) 60.9, Highwood Ave 67.8;
     - Anderson Lakes Pkwy lane 5423 62.5, Pioneer Tr 71.8, Old Shakopee Rd 70.9.
   - The pair (S of Highwood Ave all lanes, Pioneer Tr) has an episode on 27/28 days (26/28 with both stations scaled under the §3.2.4 rule, c_s = 1.046 at S of Highwood Ave from the G2 medians above and 0.987 at Pioneer Tr from G3's m_G with the reviewer's T.H.101 value; status differs on 1 day). The through-lane version agrees with the all-lane version on 28/28 days.
   - (Anderson Lakes Pkwy via 5423, Pioneer Tr) has an episode on 14/28 days, every one of them also a day of the S of Highwood Ave pair. (Pioneer Tr, Old Shakopee Rd) has an episode on 10/28.
   - Median S of Highwood Ave speed inside its pair's episodes: 26.2 mph (p90 28.7).
   - Configuration recount (geometry only): the r_nodes from S453 to S1610 inclusive carry **87** detectors (35 mainline, 2 Auxiliary, 14 Queue, 10 Passage, 10 Green, 4 Merge, 12 Exit). v2's 88 could not be reproduced. **At the time of this inspection none of the 104 Tuesdays and Thursdays of 2023 was in the cache.** They are now being pre-fetched at the author's request (2026-10-05; §0.6 A10). The post-check consistency review saw only the partial pull's file listing (days and detectors present); no Tuesday or Thursday traffic value informed this protocol.

   It informed the choice of the B1 pair and its lanes (EA-2), and the request bound of §5.2 (superseded by the pre-fetch, §0.6 A10).

### 0.6 Items for the author before the commit

Resolved since v1: **A2** (boundary distance) by **D3.5**, accepted as a disclosed deviation; **A8** (corridor still U.S.169 SB, as a two-bottleneck system) by **D3.4**. Neither appears below. Changed or new in v3: A1 (iii), A4, A9 (EA-1 replaced by EA-2) and A10. **A10 is resolved** (post-check): the extension days are pre-fetched at the author's request; the row stays below for its use rule.

| # | Item | Default if not confirmed |
|---|---|---|
| A1 | Model geometry. (i) B2 is modelled as a **merge** at E14 (2 lanes, δ_m), not as the configuration's add-drop weave, which is run only as a reported sensitivity (§1.3–1.4, issue 2). (ii) **Who performs the lane check** behind §1.7 step (a) (km 6.118–7.017 and 7.518–9.217; aerial imagery or the IRIS r_node documentation [VERIFY]; needs network or the author), before the pre-calibration facts commit. (iii) **New in v3 (round 3, issue 0):** B1's head cell (cell 26) gets a fitted **head-capacity factor θ1 ∈ [0.75, 1.05]** on ρ_cr. It is motivated by the geometry (the 3 → 2 exit-lane end at km 3.751 plus the E13 merge, a lane drop that the model gives no φ term) and disclosed as a capacity substitute, not a validated mechanism. No θ2 at B2 (§4.1 gives the reason). The alternative, a φ-type lane-drop term at the X11 exit-lane end, is not used. | (i) As written (D3.4 names B2 "the Pioneer Tr merge"). (ii) The check is not performed and §1.7 step (b) applies. (iii) Commit blocked: without θ1 the plant cannot meet P5a at both heads (§0.5 item 7). |
| A3 | Calibration/validation split by alternation within each month (§3.1), replacing v0's odd/even index. It gives 28/24 days. | Commit blocked. |
| A4 | Stochastic capacity at **two** bottlenecks (§0.3, §4.7, §5.3, §7 R3):<br>• factors c1, c2 estimated jointly per calibration day, with c2's support bounded by the relocation threshold c2\*, and re-centred on their KM medians for gate use;<br>• the stochastic plant gated by N0s, P8s, P6s and P10, the four sized rows at a family-wise 5 % (Bonferroni, 0.0125 per row), and P10b as non-inferiority with margin 0.02;<br>• the pre-registered substitute spread F̂_T (Tobit) when KM fails only by rule (ii) or (iii);<br>• **the fixed consequence of "deterministic-only":** the deterministic plant may run the gate, but only a KILL counts.<br>The author may instead choose, before the commit, "no METANET gate at all on a deterministic-only plant (route to the SUMO decision)". | Commit blocked. |
| A5 | The drop criteria (§0.4): paired one-sided P5b with the frozen real floor L_r,k, P9(1) as a paired overshoot bound, and the D3.1 wording change. | Commit blocked. |
| A6 | Thresholds marked **[lab convention]** (listed in §9.2, including those new in v3). They have no literature anchor and are fixed at the commit. | As written. |
| A7 | α_0 for the later VSL extension (§2.8): the value used by Hegyi, De Schutter & Hellendoorn 2005 [VERIFY]. Matters only for H2. | α_0 = 0.1, disclosed as a lab assumption. |
| A9 | **Event-layer amendment EA-2 (replaces v2's EA-1; it bears on D3.4; round 3, issues 3 and 8; §3.2.1):**<br>• B1 activity is the corridor rule at the **named pair P_1 = (S of Highwood Ave, all three lanes; Pioneer Tr)**, 3.145 km. This is the one pair allowed to exceed the 3 km limit;<br>• Anderson Lakes Pkwy leaves the event layer (it stays in the fit layer);<br>• model speeds are converted to detector scale before every event rule;<br>• EA-1's single-lane reading (5423) is reported only, as a sensitivity.<br>Disclosed as an amendment of the committed estimator. Every other pair keeps the 3 km limit. If the F10 scale-robustness rule fails, B1's rows become report-only (§3.6 F10). The author is asked to note in the decision log that "B1 active" in D3.4 is now measured by this pair. On calibration days it gives about 27/28 (§0.5 item 8), consistent with D3.4's "near-daily". | Commit blocked: without an event definition that does not hinge on one lane's scale, D3.4 cannot be implemented symmetrically. |
| A10 | **Validation-set extension (new; round 3, issues 7 and 9; §5.2). Resolved: pre-fetched by author request; use governed by §5.2.**<br>• All 104 Tuesdays and Thursdays of 2023 are pre-fetched at the author's request (2026-10-05; recorded in the message of commit `4af0674`, which adds the pull mode; command `python -m vsl_lab.data.mndot pull --us169-full --tue-thu`). The pull covers the full U.S.169 SB corridor of D3.3, including the Auxiliary detectors 7097 and 7077, so its detector set is larger than the 87 stretch detectors of §5.2;<br>• request count: as recorded in the ledger row of the pull (`vsl_lab/runs/ledger.csv`), to be filled in at the facts commit. v3's earlier bound of ≤ 18,200 (87 detectors) does not apply to this pull. It falls under D3.3's ≤ 59,769 for the rest of 2023 if the ledger count confirms it;<br>• **use rule:** the days are pre-fetched, not used. They may be used **only** if the extension rule of §5.2 triggers (the F11 minima fail on the validation Wednesdays, §8.6 step 3, §3.8 step 13), never earlier, and **never for fitting** or for any calibration-side reference. Before that, only the pull's completeness (days and files present) may be checked;<br>• the author's request is to be recorded in the decision log (`day_pattern_decisions_v0.md`; §7 R11). | — (resolved) |

### 0.7 The two-bottleneck system (D3.4)

**Decision D3.4 (author, 2026-10-05):** U.S.169 SB stays the corridor, as a two-bottleneck system with the same four controlled ramps. **Day-to-day variety at B1 lies in the duration and extent of its queue, not in whether it forms** (author's statement). This protocol does not assume B1's occurrence share; F10 computes it on the amended event layer (EA-2). On the v3 definition B1 is near-daily on calibration days (27/28, no exclusions, §0.5 item 8), which is consistent with D3.4. P7 (duration, extent) is gated at B1 for this reason. Where B2's queue hides B1 (§5.1, censoring), this plant gate compares B1 durations censored at the real B2 onset on both sides (P7a-1), and the system-level duration (P7c) carries the rest. For H1, the queue-duration outcome is the system-level P7c alone (both heads; not a B1 outcome); the censored B1 duration is reported only (§7 R13 (d)–(e)).

| | **B1** | **B2** |
|---|---|---|
| Pair (upstream, downstream station) | **P_1 = (S of Highwood Ave S1773, km 2.893, all three lanes; Pioneer Tr S1140, km 6.038), 3.145 km** (EA-2, §3.2.1; the one named exception to the 3 km limit) | P_2 = (Pioneer Tr, km 6.038; Old Shakopee Rd S1141, km 7.199), 1.161 km |
| Head | the Anderson Lakes Pkwy entrance merge **E13** (km 4.055), just after the 3 → 2 lane end at km 3.751 | the Pioneer Tr entrance merge **E14** (km 6.118) |
| Controlled ramp at the head | E13 (M169S55) | E14 (M169S56) |
| Model cells (§1.4) | 26–30; head cell 26 with θ1 | 31–32 |
| Head capacity per lane in the model (§2.1) | c1 · θ1 · Q_cap,G3 in cell 26 (θ1 fitted, A1 (iii)) | c2 · Q_cap,G3 |
| Discharge station (P5, C4 block) | Pioneer Tr (2 lanes, downstream of exit X12); the C4 window ends at the real B2 onset on censored days (§5.1) | Old Shakopee Rd (2 lanes, downstream of exit X13) |
| Merge-section flow (F8, P5c) | (Pioneer Tr + X12) / 2 | (Old Shakopee Rd + X13) / 2 |
| Capacity factor (§4.7) | c1 | c2, bounded by c2\* |
| Evidence before this protocol | reviewer estimates (round 2, issue 20, all 52 Wednesdays): with Anderson Lakes speed from its live lane 5423, the pair qualifies on 27/51 Wednesdays; on 15 of the 16 days with both it starts first, a median 72 min (40–140) before B2; 11 days without B2; S of Highwood Ave through lanes below 40 mph for ≥ 60 consecutive min on 45/51 Wednesdays; exit 5427 occupancy 0–3 % at every onset (not exit-led at X12); discharge 1,696 veh/h/lane, r 0.986, median duration 55 min. Round 3 (§0.5 item 7): the 5423 reading is largely a lane-scale artefact (8/51 with c_s); merge-section flow 1,745 veh/h/lane, about 11 % below B2 on the same days. v3 (§0.5 item 8): (S of Highwood Ave, Pioneer Tr) active on 27/28 calibration days | corridor analysis v2 (committed estimator): active on 23/51 Wednesdays, r 0.984, Q_dis 1,850 veh/h/lane; merge-section flow 1,950 veh/h/lane (round 3) |

**Why v1 could not see B1.** The committed event layer drops Anderson Lakes Pkwy whenever lane 5424 is dead (43/52 Wednesdays per round 1), and S of Highwood Ave → Pioneer Tr is 3.145 km, above the 3 km pair limit.

**Why v3 replaces v2's EA-1.** EA-1 read Anderson Lakes Pkwy through lane 5423 alone. That lane sits about 6 mph below the cross-section in free flow, and the B1 status it gave changes about threefold with the scale factor (§0.5 item 7). The model reads a cross-section speed, so the two sides were not measured identically. EA-2 detects B1 at a pair of stations that are read on every lane, as in the committed estimator. The queue sits at about 26 mph at S of Highwood Ave, far from the 40 mph threshold, so B1's day status hardly depends on scale (1 of 28 calibration days changes with c_s, §0.5 item 8). The price is the 3.145 km spacing, which is disclosed (§0.2).

**What changed against v1 (pointers; v2 and v3):** event layer (§3.2.1); real and model activity per bottleneck (§5.1); P2 on the first breakdown location; P3, P4, P5a, P5b, P6, P7a, P6s and P10 per bottleneck; P7b from the most upstream active head; P9 at the first-active bottleneck (§5.3); capacity factors c1, c2 estimated jointly (§4.7); F1 on B1 ∪ B2 (§6.1); the mechanism diagnostic for both (§1.6); later-protocol requirements restated (R3, R4, R6, R13). New in v3: θ1 (§2.1, §4.1), P5c, P7c, P8(iii), N0s, P8s, EA-2 with the observation operator, B1 censoring, c2\*, the substitute spread. D3.2's premise is restated accordingly: Pioneer Tr is B2's merge ramp, Anderson Lakes Pkwy is B1's, and Valley View Rd and Marth Rd feed B1 and, through it, B2.

---

## 1. Network (from `metro_config.xml.gz`, read only; km relative to the Valley View Rd entrance M169S51)

### 1.1 Stretch and boundaries

**Stretch:** U.S.169 southbound from **Minnetonka Blvd (station S453, km −8.413)** to **T.H.101 (station S1610, km +9.390)**: **17.803 km** (subject to §1.7 step (c)).
- Distance from the upstream boundary to the first controlled ramp (Valley View Rd, km 0.000): **8.413 km**, 1.587 km short of the ≥ 10 km target (D2.5.2). **Accepted by the author as a disclosed deviation (D3.5).** Further upstream lies inside the I-394 interchange queue.
- Distance from the upstream boundary to the B1 merge (E13, km 4.055): **12.468 km**; to the B2 merge (E14, km 6.118): **14.531 km**.
- B2's downstream station (Old Shakopee Rd, km 7.199) is 2.191 km upstream of the downstream end.

**Why Minnetonka Blvd.** The boundary must be the most upstream station that (i) has a complete flow measurement and (ii) is free-flowing (5-min speed ≥ 45 mph in ≥ 95 % of 05:00–23:00 bins) on ≥ 90 % of Wednesdays. From the data facts (all 52 Wednesdays): N of I-394 0.365, S of I-394 0.160, 22nd St 0.885 (fail ii); Cedar Lake Rd 0.904 passes (ii) but fails (i), because its auxiliary-lane detector 9685 has no archived 2023 data; **Minnetonka Blvd 0.923** passes both. The I-394 interchange queue upstream is outside the model; on those days the boundary flow is already capped by it (reported, §3.6 F13).

**Upstream boundary (input):** a mainstream origin at the Minnetonka Blvd station with demand = its measured flow (§2.2). Days on which this station is congested are excluded (§3.5 E2).

**Downstream boundary (endogenous, §2.2):** free outflow from the last cell with a virtual density ρ_{N+1} = min(ρ_N, ρ_cr) in the anticipation term. No measured downstream quantity enters the model. The same boundary is used in calibration, validation, the gate and DRL training. Days with spillback from beyond T.H.101, or with a real bottleneck between Old Shakopee Rd and T.H.101, are excluded (§3.5 E3).

### 1.2 Element table (inside the stretch; generated from the configuration, and the build fails if code and table disagree)

Class **M** = measured by its own archived detector; class **B** = balance-estimated (§3.3.4).

**Entrances (15): 10 metered (6 upstream + 4 controlled), 4 unmetered freeway-to-freeway, 1 without detectors.**

| ID | km | Entrance | Kind | Meter (config `storage`) | Replay inflow (§3.3.2) | Queue detector(s) (config) | Lane event (model) | δ_m term |
|---|---|---|---|---|---|---|---|---|
| E1 | −8.382 | Minnetonka Blvd | metered, upstream | M169S41 (326) | Passage 1979 | 3685 | merges | yes |
| E2 | −7.233 | T.H.7 WB | metered, upstream | M169S43 (350) | Passage 1987 | 3678 + 5318 | merges | yes |
| E3 | −6.835 | T.H.7 EB | metered, upstream | M169S44 (550) | Passage 1990 (never switches: 3679 has no 2023 data) | 3679 | merges | yes |
| E4 | −5.896 | Excelsior Blvd | metered, upstream | M169S45 (660) | Passage 1994 | 3673 + 3674 + 3675 | merges | yes |
| E5 | −4.576 | Lincoln Dr | metered, upstream | M169S46 (480) | Passage 1998 (never switches: 3670 has no 2023 data) | 3669 + 3670 | merges | yes |
| E6 | −2.901 | Bren Rd | metered, upstream | M169S47 (370) | Passage 1368 (unchecked: its link holds two undetected exits) | 2000 | merges | yes |
| E7 | −2.300 | T.H.62 WB | freeway-to-freeway | none | Merge 1369 (served flow, §3.3.3) | — | merges | yes |
| E8 | −1.866 | T.H.62 EB | freeway-to-freeway | none | Merge 1372 (served flow) | — | merges | yes |
| E9 | 0.000 | Valley View Rd | metered, **controlled** | M169S51 (300) | Passage 1378 | 3663 | adds a lane | 0 |
| E10 | 1.730 | I-494 WB | freeway-to-freeway | none | Merge 7108 (served flow) | — | adds a lane | 0 |
| E11 | 1.810 | I-494 EB | freeway-to-freeway | none | Merge 7086 (served flow) | — | adds a lane | 0 |
| E12 | 1.833 | Marth Rd | metered, **controlled** | M169S54 (450) | Passage 7087 | 7103 | joins the added lane | yes |
| E13 | 4.055 | Anderson Lakes Pkwy | metered, **controlled; B1 merge** | M169S55 (500) | Passage 5425 | 5426 | merges | yes |
| E14 | 6.118 | Pioneer Tr | metered, **controlled; B2 merge** | M169S56 (420) | Passage 5430, or Queue 5431 if §3.3.2 switches it (expected from the review: Queue/balance ≈ 0.96) | 5431 | **merges** (model, §1.3; the configuration's added lane is the weave sensitivity) | yes |
| E15 | 7.518 | Old Shakopee Rd | no detectors | none | class B: balance Old Shakopee Rd → T.H.101 | — | merges (adds a lane only under §1.7 step (a)) | yes (0 under (a)) |

"Replay inflow" lists the default; §3.3.2 may switch a metered ramp to its summed Queue detectors. The config `storage` unit is not vehicles (values up to 1,394 occur) and is believed to be feet [VERIFY in the IRIS documentation]. Storage is not used in replay; it matters only in controlled mode (§7 R1).

**Exits (15): 11 measured, 4 class B (3 sinks, because the two T.H.62 exits are lumped).**

| ID | km | Exit | Source | Split-ratio reference (§3.3.5) | Lane event (model) |
|---|---|---|---|---|---|
| X1 | −8.074 | 36th St | Exit 1983 | T.H.7 station + X2 + X1 (downstream form) | — |
| X2 | −7.670 | T.H.7 | Exit 1984 | T.H.7 station + X2 | — |
| X3 | −6.221 | Excelsior Blvd | Exit 1991 | Excelsior Blvd station + X3 | — |
| X4 | −5.003 | Lincoln Dr | Exit 1995 | Lincoln Dr station + X4 | — |
| X5 | −3.492 | Bren Rd | Exit 1348 | Bren Rd station + X5 | — |
| X6+X7 | −2.549 (X6), −2.164 (X7) | T.H.62 WB + T.H.62 EB | none: **one lumped class-B sink at km −2.549** | Bren Rd station + E6 (upstream form) | — |
| X8 | −0.574 | Valley View Rd | Exit 1375 | Valley View Rd station + X8 | — |
| X9 | 0.466 | W 78th St | detector 7110 has no 2023 data: class B | I-494 station (3 lanes) + X9 | — |
| X10 | 1.355 | I-494 EB | none: class B | Highwood Ave station + X10 | the added lane ends here (3 → 2) |
| X11 | 3.751 | Anderson Lakes Pkwy | Exit 5422 | Anderson Lakes station + X11; if that station is flow-invalid, S of Highwood Ave station (upstream form, no ramp between) | lane ends (3 → 2) |
| X12 | 5.818 | Pioneer Tr | Exit 5427 | Pioneer Tr station + X12 | — |
| X13 | 7.017 | Old Shakopee Rd | Exit 5432 | Old Shakopee Rd station + X13 | — (the weave-lane end exists only in the weave sensitivity) |
| X14 | 8.999 | T.H.101 NB | Exit 6764 | T.H.101 station + X14 + X15 | — |
| X15 | 9.217 | T.H.101 SB | Exit 6765 | T.H.101 station + X15 | the added lane ends here only under §1.7 step (a) |

**Stations (17 data-bearing): the boundary, 15 interior, and the downstream end.** Station flow = the sum over **all** lanes the configuration counts, Auxiliary-category lanes included (7097 and 7077 were pulled with author approval: 416 requests, ledger row of `edde7d2`).

| km | Station | ID | Lanes | Lane detectors | Role in the fit (§4.2) and in the event layer |
|---|---|---|---|---|---|
| −8.413 | Minnetonka Blvd | S453 | 2 | 1977, 1978 | upstream boundary (input only) |
| −7.298 | T.H.7 | S455 | 2 | 1985, 1986 | flow + speed |
| −6.946 | Van Buren Way | S456 | 2 | 1988, 1989 | flow + speed |
| −5.974 | Excelsior Blvd | S457 | 2 | 1992, 1993 | flow + speed |
| −4.600 | Lincoln Dr | S458 | 2 | 1996, 1997 | flow + speed |
| −3.370 | Bren Rd | S459 | 2 | 1366, 1367 | flow + speed |
| −2.099 | T.H.62 | S460 | 2 | 1370, 1371 (field 20.0 / 11.0 ft) | speed only (flow closed by the T.H.62 balance) |
| −0.860 | 69th St | S461 | 2 | 1373, 1374 | flow + speed |
| −0.364 | Valley View Rd | S462 | 2 | 1376, 1377 | flow + speed |
| 0.370 | S of Valley View Rd | S1770 | 3 | 1379, 1380, 7094 | flow + speed; queue area |
| 1.137 | I-494 | S1771 | 3 | 7097 (Aux), 7098, 7099 | speed; flow closed by the X9 balance over the whole day, scored in the congestion windows only (§4.2); queue area |
| 1.667 | Highwood Ave | S1772 | 2 | 7084, 7085 | speed; flow closed by the X10 balance, scored in the congestion windows only (§4.2); queue area |
| 2.893 | S of Highwood Ave | S1773 | 3 | 7077 (Aux), 7078, 7079 | flow + speed; queue area; **B1 upstream (event layer, all three lanes; EA-2)** |
| 3.922 | Anderson Lakes Pkwy | S1147 | 2 | 5423 (lane 1, field 27.5 ft), 5424 (lane 2, 28.0 ft) | **fit layer only**: speed from the lane-screen lanes (expected: 5423 only; 5424 dead on 43/52 Wednesdays); flow when every lane is valid; queue area. Not in the event layer (EA-2); its single-lane B1 reading is the EA-1 sensitivity (§5.5) |
| 6.038 | Pioneer Tr | S1140 | 2 | 5428, 5429 | flow + speed; **B1 downstream (discharge), B2 upstream**; queue area |
| 7.199 | Old Shakopee Rd | S1141 | 2 | 5433, 5434 | flow + speed; **B2 downstream (discharge)**; queue area |
| 9.390 | T.H.101 | S1610 | 2 | 6766, 6767 | downstream end (model output); speed only (flow closed by the E15 balance); E3 sentinel (also under §1.7 step (c), where it leaves the model) |

**Not modelled** (beyond T.H.101): Co Rd 21 SB exit, Co Rd 21 NB and T.H.13 CD WB entrances, the Co Rd 21 and S of Co Rd 21 stations. **Upstream of the boundary** (not modelled): everything from N of I-394 to the Minnetonka Blvd exit (km −8.715).

### 1.3 Lane geometry

**Configuration reading (unchanged from v1).** λ is read from the `lanes` attribute of **every** active r_node, including the detector-less ones (rnd_89165, rnd_1506, rnd_143, rnd_89495, …). Lane events are read from the change of the right-edge `shift` attribute at ramp nodes: +1 at an entrance = a lane added; −1 at an exit = a lane ending as an exit lane; a drop between two plain r_nodes = a merging lane drop. This reading of `shift` is ours [VERIFY].

| From km | To km | λ (configuration) | How the section starts |
|---|---|---|---|
| −8.413 | 0.000 | 2 | — |
| 0.000 | 1.355 | 3 | lane added by Valley View Rd (E9); it is the Auxiliary lane 7097 at I-494 and ends as the I-494 EB exit lane (X10) |
| 1.355 | 1.730 | 2 | — |
| 1.730 | 1.810 | 3 | lane added by I-494 WB (E10) |
| 1.810 | 2.390 | 4 | lane added by I-494 EB (E11); Marth Rd (E12, km 1.833) joins without adding a lane |
| 2.390 | 3.751 | 3 | **merging lane drop** between rnd_143 (km 2.283, 4 lanes) and rnd_89495 (km 2.390, 3 lanes); placed at 2.390. The right lane (Auxiliary 7077 at S of Highwood Ave) ends as the Anderson Lakes Pkwy exit lane |
| 3.751 | 6.118 | 2 | — |
| 6.118 | 7.017 | 3 | lane added by Pioneer Tr (E14) that ends as the Old Shakopee Rd exit lane (X13): an add-drop weaving section in the configuration reading |
| 7.017 | 9.390 | 2 | — (the measured flows contradict 2 lanes downstream of E15; §1.7) |

**Model geometry (v2; issue 2).** Identical to the configuration reading except that **km 6.118–7.017 is modelled with λ = 2 and E14 merging (δ_m)**. Reason: under the weave reading the 3-lane cells after E14 have 1.5 times the capacity of the first 2-lane cell after X13, so the model's B2 head is forced downstream of the Old Shakopee Rd station, while the data put that station in discharge during B2 (§0.5 item 5). The merge reading puts the head in the E14 cell, upstream of that station. The weave reading is run as a **reported sensitivity** (§1.4). The resulting model sequence is **2 | 3 | 2 | 3 | 4 | 3 | 2** (subject to §1.7 for km 7.518–9.390).

**Terms placed from the model geometry (§2.1):**
- **φ (lane drop)** only at the merging drop at km 2.390, in the last cell before it (cell 22), with Δλ = 1.
- Where a lane ends as an exit lane (X10, X11; X15 only under §1.7 step (a)), λ changes at the exit node **without** a φ term; the exit split is applied in that cell.
- **δ_m (merging)** = 0 at the lane-adding entrances (E9, E10, E11; E15 under §1.7 step (a)); δ_m applies at E1–E8, E12, **E13, E14** and E15, in the cell they join.
- No exit-lane-end coefficient φ_x is added.

### 1.4 Cells (rule fixed now; the resulting table must be reproduced by code)

**Rule (unchanged).**
1. Break points = every data-bearing station and every λ-change point of the model geometry (§1.3, §1.7).
2. A sub-piece between break points shorter than **L_min = 250 m** is merged with an adjacent sub-piece of the **same λ** (removing a station break point; if both neighbours qualify, the shorter one). If no neighbour has the same λ, it is merged into the neighbour with the **larger λ**, which moves that λ-change point by at most the short piece's length (logged).
3. Each resulting piece of length L is split into n = max(1, round(L / 500 m)) equal cells.
4. The cell table and the merge log are written to the build manifest; the build fails if they differ from this section (for the geometry resolved by §1.7).

**Merges on the model geometry:** 1.137–1.355 (218 m) into 0.370–1.137; 1.667–1.730 (63 m) into 1.355–1.667; **1.730–1.810 (80 m, λ = 3) into the 4-lane piece** (no same-λ neighbour: the I-494 EB lane addition moves 80 m upstream to km 1.730; disclosed); 3.751–3.922 (171 m) into 3.922–6.038. (v1's merges at 6.038–6.118 and 7.017–7.199 disappear, because 6.118 and 7.017 are no longer λ-change points.)

**Result: 36 cells, 352–660 m.** Groups: G1 = cells 1–17 (2 lanes, 55 mph posted); G2 = cells 18–25 (the interchange, 2–4 lanes); G3 = cells 26–36 (65 mph posted, 2 lanes); G4 = cells 33–36 only under §1.7 step (b).

| Cells | From–to km | Length (m) | λ | Group | Stations read (§1.5) | Ramps (config order) |
|---|---|---|---|---|---|---|
| 1–2 | −8.413 to −7.298 | 2 × 557.5 | 2 | G1 | T.H.7 (cell 2) | E1, X1 (cell 1); X2 (cell 2) |
| 3 | −7.298 to −6.946 | 352 | 2 | G1 | Van Buren Way | E2 |
| 4–5 | −6.946 to −5.974 | 2 × 486 | 2 | G1 | Excelsior Blvd (5) | E3 (4); X3 (5) |
| 6–8 | −5.974 to −4.600 | 3 × 458 | 2 | G1 | Lincoln Dr (8) | E4 (6); X4 (8) |
| 9–10 | −4.600 to −3.370 | 2 × 615 | 2 | G1 | Bren Rd (10) | E5 (9); X5 (10) |
| 11–13 | −3.370 to −2.099 | 3 × 424 | 2 | G1 | T.H.62 (13) | E6, X6+X7 lumped (12); E7 (13) |
| 14–15 | −2.099 to −0.860 | 2 × 620 | 2 | G1 | 69th St (15) | E8 (14) |
| 16 | −0.860 to −0.364 | 496 | 2 | G1 | Valley View Rd | X8 |
| 17 | −0.364 to 0.000 | 364 | 2 | G1 | — | — |
| 18 | 0.000 to 0.370 | 370 | 3 | G2 | S of Valley View Rd | E9 |
| 19–20 | 0.370 to 1.355 | 2 × 492.5 | 3 | G2 | I-494 (20, inside) | X9 (19); X10 (20) |
| 21 | 1.355 to 1.730 | 375 | 2 | G2 | Highwood Ave (inside) | — |
| 22 | 1.730 to 2.390 | 660 | 4 | G2 | — | E10, E11, E12; φ applies here |
| 23 | 2.390 to 2.893 | 503 | 3 | G2 | S of Highwood Ave | — |
| 24–25 | 2.893 to 3.751 | 2 × 429 | 3 | G2 | — | X11 (25) |
| **26–30 (B1)** | 3.751 to 6.038 | 5 × 457.4 | 2 | G3 | Anderson Lakes Pkwy (26, inside); Pioneer Tr (30, at its downstream end) | E13 (26); X12 (30) |
| **31–32 (B2)** | 6.038 to 7.199 | 2 × 580.5 | 2 | G3 | Old Shakopee Rd (32, at its downstream end) | E14 (31); X13 (32) |
| 33–36 | 7.199 to 9.390 | 4 × 547.75 | 2 | G3 (G4 under §1.7 (b)) | T.H.101 (36) | E15 (33); X14, X15 (36) |

Cell boundaries: 26–30 at 3.751, 4.2084, 4.6658, 5.1232, 5.5806, 6.038; 31–32 at 6.038, 6.6185, 7.199; 33–36 at 7.199, 7.74675, 8.2945, 8.84225, 9.390.

**Bottleneck cells:** **B1 = cells 26–30** (from the 3 → 2 lane end to the Pioneer Tr station; the E13 merge is in cell 26); **B2 = cells 31–32** (the cell containing km 6.118 through the cell read by the Old Shakopee Rd station). They are where the capacity factors (§4.7) and F1 (§6.1) act. **B1's head cell 26 also carries the head-capacity factor θ1** (§2.1, §4.1). Expected heads: cell 26 (B1) and cell 31 (B2). Each pair's stations then bracket its head as in the data: P_1 = (S of Highwood Ave, read in cell 23; Pioneer Tr, cell 30) and P_2 = (Pioneer Tr, cell 30; Old Shakopee Rd, cell 32) (unit test 11, §8.4).

**Geometry variants (each reproduced by unit test 9):**
- *Weave sensitivity (configuration reading):* v1's 37-cell table (v1 §1.4: 3.751–6.118 as 5 × 473.4 m; 6.118–7.017 as 2 × 449.5 m with λ = 3; 7.017–9.390 as 5 × 474.6 m), with B1 = v1 cells 26–30 and B2 = v1 cells 31–33. Run at the frozen v2 parameters, c1 = c2 = 1, no refit; P2–P5 reported (§5.5). Parameters fitted to the merge geometry are not tuned to this one, so the comparison is indicative only.
- *§1.7 step (a):* 7.199–7.518 one cell of 319 m (λ = 2); 7.518–9.390 four cells of 468 m (λ = 3; the 173-m piece 9.217–9.390 has no same-λ neighbour and merges into the 3-lane piece, so the X15 lane end moves to km 9.390, logged). 37 cells.
- *§1.7 step (c):* 7.199–7.518 one cell of 319 m; the stretch ends at km 7.518. 33 cells.

### 1.5 Ramp placement and station readings in the model

- An entrance at km x feeds the cell containing x; an entrance exactly on a cell boundary feeds the downstream cell. An exit at km x leaves the cell containing x; an exit exactly on a boundary leaves the upstream cell.
- **Model value at a station** = the cell containing the station's km (a station exactly on a boundary reads the upstream cell: Pioneer Tr reads cell 30, Old Shakopee Rd cell 32, T.H.101 cell 36). Flow is corrected for ramps of the same cell that lie **downstream** of the station: q_s = q_i − Σ(entrance releases downstream of s in cell i) + Σ(exit flows downstream of s in cell i). On this configuration this matters at I-494 (cell 20: + X10) and Anderson Lakes Pkwy (cell 26: − E13). Model speed at the station = v_i.
- 5-min model aggregates: flow = mean of q_s over the 60 steps; speed = Σ q_s / Σ (q_s / v_i) over the bin (the model counterpart of the detector estimator ΣQ/ΣK).

### 1.6 Bottleneck-mechanism diagnostic (real data, calibration days only, before any fit)

The geometry and the station pattern cannot separate a merge-led breakdown from one led by an exit queue spilling back. METANET with fixed split ratios cannot produce the latter, so it is tested first, **for each bottleneck**:

| | B1 | B2 |
|---|---|---|
| Exit between the pair's stations | X12 Pioneer Tr, detector 5427 (km 5.818, cell 30) | X13 Old Shakopee Rd, detector 5432 (km 7.017, cell 32) |
| Also reported (not decisive) | X11 Anderson Lakes Pkwy exit-lane end, detector 5422 (km 3.751) | — |

- **Data:** the exit detector's 5-min counts and occupancy; the onset t0 of each real B_k episode on real-B_k-active **calibration** days (§5.1). Under EA-2, B1's t0 is when the queue is detected at S of Highwood Ave, which can be later than the head's breakdown; the window below is unchanged, and this is disclosed.
- **Control:** the median exit occupancy in 15:00–19:00 on calibration days on which B_k is not active; if fewer than 4 such days exist (expected possible for B1), the median over 13:00–15:00 on all usable calibration days [lab convention].
- **A day is exit-led** if (a) the exit occupancy is ≥ 2 × the control **and** ≥ 20 % for ≥ 3 consecutive bins inside [t0 − 15 min, t0 + 30 min]; (b) the first such bin is no later than t0 + 5 min; (c) the exit detector is valid that day.
- **Outcome per bottleneck** (over active calibration days with a valid exit detector): **EXIT** if ≥ 50 % are exit-led; **base** if ≤ 20 %; **INCONCLUSIVE** otherwise or if fewer than 6 days qualify. INCONCLUSIVE keeps the base structure and is reported. [Thresholds: lab convention.] The reviewer's round-2 check (5427 at 0–3 % at every B1 onset) leads one to expect "base" at B1; this is not a computed outcome.
- **EXIT branch (pre-registered, per bottleneck):** the base model (not F1) gets an exit-capacity cap at that exit: s_X = min(β·F, C_x,k); when it binds, the outflow of the exit's cell is limited to (1 − β)/β · C_x,k (FIFO blocking). C_x,k is one extra calibrated parameter per EXIT bottleneck, bounds 900–2,200 veh/h [lab convention]. F1 stays as specified, so there is still exactly one fallback.
- Reported in both cases: P5 also as total bottleneck throughput (downstream station + the exit), model and real. If EXIT at B_k, the drop at B_k is flagged as measuring through-flow, not bottleneck capacity.

### 1.7 Downstream capacity check F16 and its resolution (fixed now; issue 0)

**Fact F16** (pre-calibration, calibration days; §3.6, step 11 of §3.8). For every G3 cell **outside the bottleneck cells** (cells 33–36 on the model geometry):
- R_i = A_i / (λ_i · Q_ref);
- A_i = the median over usable calibration days of the daily maximum 15-min (3-bin rolling) arriving flow in cell i. The arriving flow is reconstructed by conservation from the nearest flow-valid station and the replayed ramp series (class M and class B, no storage term), at the point just downstream of the cell's last entrance (or at the cell's upstream end if it has none);
- Q_ref = the larger of the real per-lane Q_dis at B1 and at B2 (F8), so that a cell is flagged only if it must carry clearly more than either bottleneck discharges.

G1 and G2 cells are reported with the same ratio but are not subject to the rule: they have their own fundamental diagrams, so a high ratio there is not a structural contradiction (a ratio > 1.10 there is listed in F14 as a lane-count question).

**Rule.** If every R_i ≤ **1.10** [reviewer's value, adopted], nothing changes. Otherwise calibration is blocked until the first applicable step resolves it, in this order:
- **(a) Lane check confirms an added lane.** If the lane check (§0.6 A1 (ii)), recorded with its source and date in the facts, confirms a lane added at E15 (km 7.518) that ends as the X15 exit lane (km 9.217), the model geometry gets λ = 3 there (E15 lane-adding, δ_m = 0; X15 an exit-lane end, no φ), the §1.4 rule is re-run (§1.4 variants) and F16 is recomputed once. If a cell is still flagged, step (b) applies to it.
- **(b) Lane check not performed, or inconclusive: separate capacity group G4** = the cells from the one holding E15 to the stretch end (cells 33–36 on the model geometry). v_f,G4 ≡ v_f,G3 (tied); ρ_cr,G4 and a_G4 are fitted with the G3 bounds (§4.1), which adds 2 parameters. Disclosed as a capacity substitute for an unconfirmed lane.
- **(c) Lane check confirms 2 lanes: truncation.** The measured downstream flows are then implausible for the confirmed geometry, so the counts there (X14, X15, T.H.101) are suspect. The stretch ends at km 7.518, just upstream of E15, with the §2.2 free-outflow boundary; E15, X14, X15 and the T.H.101 station leave the model (T.H.101 stays a real-data sentinel for E3, §3.5).

Which step applies changes only the following, each stated where it applies: the cell table and G4 (§1.4; G4 under (b) only, with §2.1 and §4.1); the lane events and δ_m at E15/X15 under (a) (§1.2, §1.3); the parameter count (§4.1, §4.4); the downstream boundary g(N) and the last cell ending at km 7.518 under (c) (§2.2); E15 not modelled under (c) (§2.3, §3.3.4 table); the CFL minimum cell length of 319 m under (a) or (c) (§2.5, unit test 2); T.H.101 leaving the model, S_v, G3's m_G and the model-side (Old Shakopee Rd, T.H.101) pair under (c) (§3.2.4, §4.2); relocation rule (b) dropped under (c) (§4.7); and the T.H.101 measured-density sensitivity not run under (c) (§5.5). Input-detector validity (§3.2.2, §3.5 E1) for X14, X15 and T.H.101 stays as written under every step: days are excluded on these detectors even under (c), a conservative choice. Nothing else depends on it. The step taken is part of F16 and of the frozen build.

---

## 2. Model

METANET (Papageorgiou, Blosseville & Hadj-Salem 1990; Kotsialos et al. 2002 [VERIFY both]). Notation: cell i = 1…N (N = 36 on the model geometry; §1.4), step k, T = 5 s, L_i and λ_i from §1.4, g(i) the cell's group.

### 2.1 Equations

**Flow:** q_i(k) = ρ_i(k) · v_i(k) · λ_i.

**Density:** ρ_i(k+1) = ρ_i(k) + T / (L_i λ_i) · [ q_{i−1}(k) − q_i(k) + r_i(k) − s_i(k) ],
with r_i the sum of origin releases into cell i (§2.3) and s_i the sum of exit flows from cell i (§2.4).

**Speed:**
v_i(k+1) = v_i(k)
 + (T/τ) · [ V_i(ρ_i(k)) − v_i(k) ]
 + (T/L_i) · v_i(k) · [ v_{i−1}(k) − v_i(k) ]
 − (ν T)/(τ L_i) · [ ρ_{i+1}(k) − ρ_i(k) ] / [ ρ_i(k) + κ ]
 − δ_m · T · r_i^m(k) · v_i(k) / [ L_i λ_i (ρ_i(k) + κ) ]
 − φ · T · Δλ_i · ρ_i(k) · v_i(k)² / [ L_i λ_i ρ_cr,i ]

- r_i^m = the releases of the **merging** entrances in cell i (δ_m-entrances of §1.3: E1–E8, E12, E13, E14, E15); the lane-adding entrances do not enter this term.
- Δλ_i = 1 in cell 22 only, otherwise 0 (§1.3).
- The merging coefficient is named **δ_m** to avoid a clash with the gate draft's drop variable.

**Fundamental diagram:** V_i(ρ) = v_f,g · exp( −(1/a_g) · (ρ/ρ_cr,i)^{a_g} ), with one (v_f, ρ_cr, a) per group (G4, if used, ties v_f to G3; §1.7). The cell's critical density ρ_cr,i is:
- ρ_cr,i = ρ_cr,g outside the bottleneck cells;
- **ρ_cr,i = c_k · ρ_cr,g** in the cells of bottleneck B_k (B1: 27–30; B2: 31–32);
- **ρ_cr,26 = c1 · θ1 · ρ_cr,G3** in B1's head cell 26 (new in v3; round 3, issue 0).

θ1 is a fitted parameter (§4.1) and is part of the frozen plant. c1 = c2 = 1 for the frozen plant; the factors vary only in §4.7 and later in the gate, and c_k multiplies θ1 ρ_cr,G3, so re-centring to c = 1 keeps each head at its own fitted level. F1 acts on these cells (§6.1). Cell capacity per lane: Q_cap,i = v_f,g · ρ_cr,i · e^{−1/a_g}. Unit test 17: θ1 = 1 reproduces the v2 structure exactly.

*Why θ1 (round 3, issue 0).* At θ1 = 1 both heads are 2-lane G3 cells with one ρ_cr, v_f and a, so the model has no parameter that tells them apart. The data put B1's merge-section flow about 11 % below B2's on the same days (§0.5 item 7). With one capacity C per lane, P5a's ±5 % needs C ≤ ≈ 1,831 at B1 and C ≥ ≈ 1,860 at B2 (reviewer's arithmetic), and these ranges do not overlap. The δ_m term pushes the wrong way, because E14's merge flow is larger than E13's. P2 would also lack a structural reason for B1 to break first. θ1 lets the B1 head cell be weaker (or slightly stronger) than G3 without per-cell v_f, which v2 rules out for F1. B2 gets no θ2: B2's capacity is the G3 level, and a θ2 > 1 would move B2's binding cell downstream of the Old Shakopee Rd station (round 3, issue 1).

### 2.2 Boundaries

- **Mainstream origin (Minnetonka Blvd):** q_0(k) = min[ d_0(k) + w_0(k)/T, q_lim(k) ], w_0(k+1) = w_0(k) + T (d_0 − q_0), with d_0 = the measured station flow. q_lim = λ_1 v_1 ρ_cr,1 (−a_1 ln(v_1/v_f,1))^{1/a_1} if v_1 < V_1(ρ_cr,1); otherwise q_lim = λ_1 Q_cap,1 (form after Kotsialos et al. 2002 [VERIFY]).
- **Virtual upstream speed:** v_0(k) = v_1(k).
- **Downstream:** outflow of the last cell N uncapped; ρ_{N+1}(k) = min(ρ_N(k), ρ_cr,g(N)) in the anticipation term (g(N) = G3, or G4 under §1.7 (b); under §1.7 (c) the last cell ends at km 7.518).

### 2.3 Origins: replay mode (calibration and the plant gate)

For every entrance o feeding cell μ, with queue w_o (vehicles), w_o = 0 at 04:00:
- q_o(k) = min[ d_o(k) + w_o(k)/T, Q_o, Q_o · (ρ_max − ρ_μ(k)) / (ρ_max − ρ_cr,μ) ];
- w_o(k+1) = w_o(k) + T · (d_o(k) − q_o(k)).

**Demand d_o in replay:**
- metered ramps (E1–E6, E9, E12–E14): the replay inflow chosen by §3.3.2 (Passage, or the summed Queue detectors where the rule switches the ramp). There is **no meter-rate cap** in replay: the field meter's action is already in d_o;
- freeway-to-freeway ramps (E7, E8, E10, E11): the measured Merge flow (a served flow, §3.3.3);
- Old Shakopee Rd (E15): the class-B balance (§3.3.4); not modelled under §1.7 step (c).

**Capacity Q_o = 2,200 veh/h per ramp lane** (configuration `lanes` = 1 for all 15 entrances), fixed and not fitted. In replay it is chosen to be non-binding (all observed 5-min ramp flows quoted in the review are ≤ 1,800 veh/h); any bin where d_o > Q_o is reported. Volume clipped by the supply term stays in w_o and is released as soon as the mainline admits it: replayed vehicles are never discarded and never forced into a jammed cell.

**Why the ramp-capacity scale and ρ_max are not fitted:** in replay they bind only through supply-limited bins, which are a model misfit, so they are not identifiable from replay data. ρ_max is fixed at **180 veh/km/lane** (Hegyi et al. 2005, citing Kotsialos et al. 1999 [VERIFY]; Poole & Kotsialos 2016 report calibrated 173–183 [VERIFY]).

**Reported per origin and day (not gated):** supply-clipped volume Σ T (d_o − q_o)⁺, end-of-day w_o, queue-minutes. Any origin (mainstream included) with w_o > 0 for ≥ 15 consecutive minutes is listed as a **plant misfit** next to the gate rows, with the vehicles it withheld from the bottlenecks. Next to P5-k and P9: the share of P5-k days on which the bottleneck's merge ramp (E13 for B1, E14 for B2) had clipped volume > 0, and that volume as a share of its daily inflow.

### 2.4 Exits

For each exit e in cell i, with split ratio β_e(k) from §3.3.5:
- s_e(k) = β_e(k) · F_e^mod(k), where F_e^mod = q_{i−1}(k) + Σ q_o(k) over entrances in cell i upstream of e − Σ s_x(k) over exits in cell i upstream of e (configuration order);
- s_i = Σ s_e over the exits of cell i.

This is the model counterpart of β defined against the flow **arriving at the diverge** (§3.3.5). Examples: X1 in cell 1 sees q_0 + E1; X14 then X15 in cell 36 see q_35 and q_35 − s_X14. EXIT branch caps (§1.6), if any: X12 in cell 30 (B1), X13 in cell 32 (B2).

### 2.5 Numerics (fixed now)

- **Time step T = 5 s** (60 steps per 5-min bin).
- **CFL, asserted at build against the bound maxima, not the current iterate:** v_cap = 1.05 × v_f,max = 1.05 × 150 km/h = 157.5 km/h (43.75 m/s); T · v_cap = 218.75 m ≤ min L_i = 352 m on the model geometry (319 m under §1.7 (a) or (c)). Courant number ≤ 0.62 (≤ 0.69 with the 319-m cell).
- **Relaxation, asserted at build:** τ_min = 10 s = 2T, so T/τ ≤ 0.5 over the whole τ range.
- **State limits after every step:** v_i ∈ [v_min, 1.05 · v_f,g(i)] with **v_min = 7.4 km/h fixed** (Kotsialos et al. 2002, Table II, as reported by the review [VERIFY]); ρ_i ∈ [0, ρ_max]; w_o ≥ 0.
- **Clipping count (amended; round 3, issue 2):** a cell-step counts as clipped if, after the step, the density was clipped to [0, ρ_max], the speed was clipped to 1.05 · v_f,g(i), or **the speed was raised to v_min while ρ_i < ρ_cr,i** (a floor activation outside a genuine jam). Floor activations with ρ_i ≥ ρ_cr,i are part of the model and are reported only. The reason: at the allowed bound corners the anticipation term can move a queue tail's speed by hundreds of km/h in one step (νT/(τL) ≈ 128 km/h at ν = 90, τ = 10 s, L = 352 m), so a parameter set could chatter on the floor at queue tails and still pass a check that ignores the floor.
- **Admissibility during estimation:** an evaluation with a non-finite value, or with clipped cell-steps (as counted above) in > 1 % of cell-steps on any calibration day, gets **J = 10** (worse than any admissible J) and is counted per restart.
- **Gate check N0 (§5.3):** on every usable validation day, clipped cell-steps ≤ 1 % of cell-steps; **and** the step-halving check below passes.
- **Step-halving (gated; round 3, issue 2):** at the frozen optimum, before any validation run, the frozen parameters are re-run at T = 2.5 s (120 steps per bin; the CFL and τ ≥ 2T assertions hold a fortiori) on all usable calibration days. **Pass if** |J(2.5 s) − J(5 s)| / J(5 s) ≤ **0.05** [lab convention] **and** the set of calibration days with ≥ 1 model episode at P_1, and the set at P_2, are unchanged. A failure is an **N0 FAIL** (known before validation; N0 is outside the F1 trigger, so the outcome is a route stop, §6.1). The per-station RMS change of 5-min speeds is reported. The same check applies to every ensemble candidate (§4.6) and to F1 if fitted.
- T, L_min, the cell rule and these bounds are frozen by this commit; any change is a protocol amendment.

### 2.6 Implementation choices (fixed now)

- Inputs are 5-min means held constant over the 60 steps of the bin; class-B balances (15 min) are held constant over their three 5-min bins.
- **Warm-up (issue 7):** at 04:00 every cell starts on the **free-flow branch** of its fundamental diagram: q_i is propagated from the 04:00 boundary flow through the 04:00 ramp inputs and split ratios (cell by cell, in configuration order), ρ_i is the solution on the free-flow branch (ρ_i ≤ ρ_cr,i) of λ_i ρ_i V_i(ρ_i) = q_i, and v_i = V_i(ρ_i); all queues are empty. If q_i exceeds the cell's capacity (not expected at 04:00), ρ_i = ρ_cr,i and the case is logged. With ramps and varying λ this state is not exactly stationary under METANET's convection and anticipation terms; it relaxes during the warm-up. The model runs on the measured 04:00–05:00 inputs; nothing before 05:00 is scored. Scoring and all criteria use 05:00–23:00 (216 bins).
- Units in the model: km, h, veh; detector speeds are converted from mph (1 mph = 1.609344 km/h).
- Model code: `vsl_lab/plants/metanet.py`; vectorised over days. Days are independent.

### 2.7 Plant modes

- **Mode R (replay)** is the mode judged in this protocol (§2.3).
- **Mode R-NL (no-leak replay)** is mode R with the freeway-to-freeway merge inputs replaced inside the real queue by a queue-independent series (§3.3.3). It is **reported only** (§5.5).
- **Mode C (controlled)** is used by the headroom gate, H1 and H2. Its definition, its demand reconstruction (controlled ramps from Queue detectors; freeway-to-freeway demand on clipped days), ramp storage and `max_wait`, and an equivalence check against mode R are **requirements on a later protocol**, stated in §7 R1–R2, and must be committed before any gate run.

### 2.8 Speed-limit extension (not calibrated, not validated here; fixed now for later use)

- **The calibrated plant has no speed-limit term:** V_i = V(ρ_i) in every cell. The posted 55/65 mph limits are absorbed in the fitted v_f. "No VSL displayed" (including b = 1) means the term is absent, so the no-VSL plant is exactly the plant judged in §5 (unit test, bit-for-bit, §8.4).
- **Primary response form when a VSL v_VSL,i is displayed:** V_i = min[ V(ρ_i), (1 + α) · v_VSL,i ] (Hegyi, De Schutter & Hellendoorn 2005 [VERIFY]). Under this form a cell's static capacity falls only if (1 + α) v_VSL,i < v_f e^{−1/a}.
- **Pre-registered variant for H2:** the VSL-modified fundamental diagram of the MTFC literature (Carlson et al. 2010 [VERIFY]), in which the VSL scales v_f and shifts ρ_cr, with its parameters taken from that source.
- **α** cannot be identified from these data (no VSL on the corridor). α_0 = the Hegyi et al. 2005 value [VERIFY, §0.6 A7; default 0.1]; sensitivity values {0.0, 0.2}. Neither the form nor α_0 may change after any VSL result has been seen. The binding rules for their use are in §7 R6.

---

## 3. Data

### 3.1 Days and split (unchanged from v1; author item A3)

**Days:** the 52 Wednesdays of 2023 in the D3.3 pull. The 52 weekend days (26 Saturdays, 26 Sundays) are a reported check only (§5.5). **2024 is not opened by this protocol** (D3.3); the transfer check P-T is defined in §5.6 and executed under the gate protocol.

**Split (fixed before any exclusion):** within each calendar month, number the Wednesdays 1, 2, 3, … in date order; **odd positions → calibration, even positions → validation**. Months with five Wednesdays (March, May, August, November) give three calibration days and two validation days. Code: `[d for _, g in groupby(weds_2023, key=lambda d: d.month) for j, d in enumerate(g) if j % 2 == 0]` for calibration and `j % 2 == 1` for validation, with `weds_2023` all 2023 Wednesdays in date order.

- **Calibration (28):** 01-04, 01-18, 02-01, 02-15, 03-01, 03-15, 03-29, 04-05, 04-19, 05-03, 05-17, 05-31, 06-07, 06-21, 07-05, 07-19, 08-02, 08-16, 08-30, 09-06, 09-20, 10-04, 10-18, 11-01, 11-15, 11-29, 12-06, 12-20.
- **Validation (24):** 01-11, 01-25, 02-08, 02-22, 03-08, 03-22, 04-12, 04-26, 05-10, 05-24, 06-14, 06-28, 07-12, 07-26, 08-09, 08-23, 09-13, 09-27, 10-11, 10-25, 11-08, 11-22, 12-13, 12-27.

Excluded days (§3.5) are removed from their own set and counted per reason. They are never moved between sets, never replaced, and the sets are never re-balanced. Both date lists, and every exclusion with its reason, go to `metanet_calibration.json`. The alternation spreads seasons and multi-week regimes (work zones, detector faults) over both sets; validation therefore tests interpolation within 2023, not transfer to 2024 (that is P-T).

**Holiday-adjacent days stay in** (the plant replays measured inputs) and are reported as a stratum: 2023-01-04 (calibration), 07-05 (calibration), 11-22 (validation), 12-27 (validation).

### 3.2 Cleaning: two layers (fixed now)

**3.2.1 Event layer** (every real-side event: B1/B2 active, onsets, episodes, Q_dis, r, queue extent, bottleneck pairs, boundary and spillback congestion). It is the corridor-protocol estimator (`vsl_lab/data/corridor_analysis.py`: `lane_bins`, `station_day`, `episodes`, the C4 block of `analyse_corridor`):
- 5-min bins from ≥ 9 of 10 30-s values;
- a lane-day is dead if it has zero counts 06:00–20:00;
- speed = ΣQ/ΣK in mph;
- consecutive valid stations ≤ 3 km apart.

A station's lanes are all lanes the configuration counts (Auxiliary included at I-494 and S of Highwood Ave), and a station-day is event-valid only if every lane is valid (≥ 90 % of bins present, not dead). That is the committed rule, for speed and flow alike. v3 makes **one amendment, EA-2**, which replaces v2's EA-1.

**Amendment EA-2 (D3.4; author item A9; round 3, issues 3 and 8; disclosed as an amendment of the corridor estimator).**
- **Anderson Lakes Pkwy (S1147) is removed from the event layer on every day.** The committed estimator already drops it on most days, because 5424 is dead on 43/52 Wednesdays. Removing it on the remaining days keeps B1's definition the same on every day. The station stays in the fit layer (§3.2.2: S_v, Q_A, flow where valid).
- **Named pair P_1 = (S of Highwood Ave S1773, all three lanes; Pioneer Tr S1140), 3.145 km**, is evaluated with the unchanged corridor rule, although it exceeds the 3 km pair limit. It is the only pair allowed to do so. With Anderson Lakes Pkwy removed, the two stations are consecutive in the event layer.
- **Every other rule is unchanged:** the 3 km limit for every other pair, all lanes, the 40 mph / 20 mph / 5-of-7 rule, the episode merging and the C4 formulas.
- **Physical reading.** An episode at P_1 means a queue at S of Highwood Ave (km 2.893) with free-flowing traffic at Pioneer Tr. The bottleneck then lies between km 2.893 and 6.038, which holds the 3 → 2 exit-lane end (km 3.751), the E13 merge (km 4.055) and the X12 exit. These are B1's cells 26–30 in the model; the 4 → 3 merging drop at km 2.390 lies upstream of S of Highwood Ave. A queue from B2 that reaches Pioneer Tr breaks the pair condition, so B2 cannot be counted as B1. B1 can then be hidden, which is handled by censoring (§5.1).
- **Why all three lanes.** The model reads one cross-section speed in cell 23. The committed estimator's all-lane ΣQ/ΣK is the matching quantity, so both sides measure the same thing. On calibration days the through-lane version (7078/7079) gives the same day status on 28/28 days (§0.5 item 8); it is reported as a sensitivity.
- **Model side (observation operator; §3.2.4, §5.1).** Before any event rule, each model station speed is converted to detector scale, v_model,s / c_s. The real side stays raw, so the real references are those of the committed estimator, amended only by EA-2.
- **Sensitivities (reported, not gated; §5.5):**
  - **EA-1**: B1 at (Anderson Lakes Pkwy via the lane-screen lanes, expected 5423 alone; Pioneer Tr), raw and c_s-scaled, with v2's rule;
  - the through-lane S of Highwood Ave version;
  - on the days on which every Anderson Lakes Pkwy lane is valid, the committed pairs (S of Highwood Ave, Anderson Lakes Pkwy) and (Anderson Lakes Pkwy, Pioneer Tr), and the agreement of the 1-lane and all-lane (Anderson Lakes Pkwy, Pioneer Tr) day status and episode minutes (round 3, issue 3).
- **Limits (§0.2, §9.1):** a B1 queue that does not reach S of Highwood Ave is not seen on either side; the 3.145 km spacing is coarser than the committed limit.

The B2 stations (Pioneer Tr, Old Shakopee Rd) have no Auxiliary lane, and S of Highwood Ave is read as in the committed estimator. The committed corridor-v2 references for B2 are therefore unchanged.

**3.2.2 Fit layer** (inputs and the NRMSE terms).
- 30-s gaps of ≤ 15 min are linearly interpolated **before** 5-min aggregation (disclosed deviation from the corridor protocol, which does not interpolate). A longer gap is never interpolated, and its bins stay invalid.
- **Gap rule and windows (fixed in v3; round 3, issue 9).** The reading depends on the detector's role:
  - **Input detectors.** These are the boundary station, every class-M entrance and exit detector, every station used in a class-B balance, and every station used that day as a β reference (§3.3.5). **Any gap > 15 min within 04:00–23:00 makes the lane-day invalid.** The model runs on the measured 04:00–05:00 inputs (§2.6) and cannot run on a missing input bin, and no infill rule beyond 15 min is pre-registered. An invalid input lane-day then acts through E1, with the β fallbacks of §3.3.5.
  - **Scored stations** (S_q, S_v, Q_A; only 05:00–23:00 is scored). A gap > 15 min invalidates **only the bins it covers**. Those bins are not scored, and the lane-day's validity is decided by the 90 % rule below over 05:00–23:00.
  - A station that is both an input and a scored station on a day (e.g. a β reference that is also in S_q) follows the input rule.
- Lane-day validity: ≥ 90 % valid 5-min bins after interpolation, over 04:00–23:00 for inputs and over 05:00–23:00 for scored stations, and not dead (Addendum B rule).
- *Disclosed:* the reviewer's estimate (§0.5 item 7) is that the input reading loses validation day 2023-04-12 (E5, X4 and Lincoln Dr), giving n_val ≈ 15. The rule was chosen on the ground stated above, knowing that effect. The pre-registered extension (§5.2, A10) means that the choice does not decide whether the gate runs.
- **Flow-valid station-day:** every lane valid, Auxiliary included.
- **Speed-valid station-day:** at least one speed lane (§3.2.3) valid; station speed = ΣQ/ΣK over the valid speed lanes.

**3.2.3 Lane speed screen (fixed before fitting; calibration days; step 2 of §3.8).** For each mainline lane: the median 5-min speed over 05:00–06:00 bins with volume > 0, pooled over **every valid lane-day of the 28 calibration Wednesdays** (no day-level exclusion is needed: only free-flow early-morning bins are used, and this removes the circularity with E1 noted in round 2). A lane whose median lies outside 50–80 mph, or that has fewer than 100 such bins, is excluded from the **fit-layer** speed term on **all** days; its counts stay in the flow. *(v3: the event layer no longer uses the screen, because EA-2 returns it to the committed all-lane estimator. The screen still defines the EA-1 sensitivity.)* The excluded-lane list (with field lengths, e.g. T.H.62 lane 2 at 11.0 ft) is frozen in the pre-calibration facts commit. Expected (not computed): 5424 is excluded, because it is dead on most days and cannot reach 100 bins.

**3.2.4 Station speed scaling (fixed before fitting; calibration days; step 7 of §3.8; amended in v3, round 3, issues 4 and 8).**
- **Stations.** c_s is computed for every interior station **and for T.H.101** (S1610). T.H.101 belongs to **G3** for scaling under every §1.7 step: under step (b), G4 ties v_f to G3, so the free-flow reference is G3's. Under step (c), T.H.101 leaves the model, S_v and G3's m_G. Its c_s is still computed and reported (F6), but it is not used: the model has no value at T.H.101 to convert, so the pair (Old Shakopee Rd, T.H.101) exists on the real side only (E3 (ii)) and leaves the model-side P8 pairs and relocation rule (b) (§4.7).
- **m_s** = the median over calibration station-days of the station's median 05:00–06:00 speed. For the fit-layer speed lanes, m_s is computed over those lanes; for the event-layer conversion below, over all lanes (identical where no lane is screened out).
- **Group reference m_G** = the median of m_s over the group's stations **whose speed lanes equal all their lanes**. The EA-1 single-lane station (expected: Anderson Lakes Pkwy) therefore cannot set any group's reference. T.H.101 counts in G3's m_G, except under §1.7 (c).
  - Calibration-day example from the reviewer's medians (§0.5 item 7): G3 m_G = median(PT 71.8, OSR 70.9, T.H.101 62.7) = 70.9 mph, giving c_s = 1.134 (AL), 0.987 (PT), 1.000 (OSR), 1.131 (T.H.101). These are not computed facts; F6 computes them.
- **Scale** c_s = m_G / m_s, frozen and applied unchanged to validation, extension and weekend days.
- **Fit layer.** Real speeds are scaled (× c_s) in the NRMSE_v terms only (J, P1, P1c nulls). A station with |c_s − 1| > 0.15 [lab convention] is dropped from the speed term (S_v, **Q_A**, P1c; §4.2) and kept for flow. **T.H.101 is scaled in S_v like the interior stations** (it was unscaled-or-undefined in v2).
- **Event layer: observation operator (round 3, issue 8 option (a)).** The real side is raw, so the real references stay those of the committed estimator, amended only by EA-2. The model, fitted to scaled speeds, is converted back to detector scale **before every event rule**: v_model,s,event = v_model,s / c_s at every station the event layer reads. This covers the corridor rule at every pair (P_1, P_2, P8 pairs including (Old Shakopee Rd, T.H.101), the latter not under §1.7 (c)), P7b's congested-station test and the P9 window. The conversion uses the computed c_s also for stations dropped from the speed term. Model and real are then compared on the same (detector) scale. The rule fixes the scale, not the shape: a speed-dependent bias beyond the free-flow factor is not corrected. Its effect on B1 is bounded by the F10 scale-robustness rule.
- **Reported:** c_s at S of Highwood Ave, Anderson Lakes Pkwy, Pioneer Tr, Old Shakopee Rd and T.H.101. If any of them has |c_s − 1| > 0.05, P2–P5 and P10 are also reported with both sides on the scaled scale (real × c_s, model unconverted; not gated).
- **No detector-bias parameter is fitted** (a per-group offset is collinear with the group v_f in free flow).
- **Unit test 10** includes a toy example: three G3 stations, one of them single-lane, plus a downstream sentinel. It checks that the single-lane station is left out of m_G, that the sentinel is in it and is scaled, and that the observation operator returns the raw real series when the model equals the scaled real speeds.

### 3.3 Inputs

**3.3.1 Upstream boundary.** Fit-layer 5-min flow of the Minnetonka Blvd station (both lanes).

**3.3.2 Metered-ramp inflow: Passage unless an independent detector confirms the balance (fixed now; calibration days; step 4 of §3.8; issues 3, 21).**

Every metered ramp replays its **Passage** detector, unless **all** of the following hold, in which case it replays its **Queue** detectors (summed, fit-layer cleaning, 5-min):
1. **Usable Queue:** every Queue-category detector of the ramp has 2023 data (§3.7). Not usable: E3 (3679 absent) and E5 (3670 absent). E6 is unchecked by construction (its link holds two undetected exits).
2. **Enough closable days:** the ramp's link can be closed (both bounding stations flow-valid that day; every other element of the link class M) on at least 8 calibration days; otherwise the ramp keeps Passage and is listed "unchecked".
3. **Queue corroborates the balance:** the median over those days of |ΣQueue / ΣBal − 1| ≤ **0.05** in both windows (05:00–23:00 and 15:00–19:00).
4. **Passage contradicts the balance:** the median of |ΣPassage / ΣBal − 1| > **0.10** in either window, **and** the median of |ΣPassage − ΣBal| over 05:00–23:00 exceeds **1 %** of the link's inflow (q_up + Σ entrances).

Here Bal is the balance-derived inflow (v1's B_o, unchanged): Bal_o = q_down + Σ(measured exits in the link) − q_up − Σ(other measured entrances in the link) + ΔN/Δt, 15-min, ΔN from §3.3.4.

**Why.** The balance carries the mainline stations' errors, and the mainline flow is about 15–30 times the ramp volume at E12 and E13. A 1 % station error is then 15–30 % of the ramp's PM flow (issues 3, 21). An independent detector that agrees with the balance while Passage does not is evidence of a Passage fault, not of a station fault. Replaying the corroborating **Queue** detector, rather than the balance (v1), keeps the downstream station out of the input, so the link stays in the conservation check (§3.4) and the station stays in the flow terms (§4.2).

**Disclosed.** Queue counts arrivals, not releases. Replaying it moves releases earlier by the ramp queue's delay (at the controlled ramps bounded by the field `max_wait`, 240 s per v1 R1; not known for the upstream ramps [VERIFY]).

**Expectation from the review's numbers (not a computed fact):** E14 switches (Queue/balance ≈ 0.96 in both windows); E12 and E13 keep Passage (their Queue detectors agree with Passage, not with the balance); E3 and E5 cannot switch.

**E14 dependency (stated in v3; round 3, issue 9).** If E14 does **not** switch, the link Pioneer Tr → Old Shakopee Rd keeps a Passage over-count. The reviewer estimates e ≈ 4.8 % median, above 3 % on 96 % of calibration days. Step 6 (§3.4) is then expected to mark **Old Shakopee Rd flow-unreliable**. The station would leave the flow terms of J and P1a, but its flow would still be B2's discharge reference in P5a-2, P5b-2, P5c, P9 (when b = B2) and F8. In that case:
- those rows are computed as specified;
- they are flagged "B2 discharge station flow-unreliable", with the station's median signed residual (§3.4) reported next to them;
- no row is dropped or relaxed.

**Links used:** E1 Minnetonka Blvd → T.H.7 (with X1, X2); E2 T.H.7 → Van Buren Way; E3 Van Buren Way → Excelsior Blvd (X3); E4 Excelsior Blvd → Lincoln Dr (X4); E5 Lincoln Dr → Bren Rd (X5); E9 Valley View Rd → S of Valley View Rd; E12 Highwood Ave → S of Highwood Ave (with the measured E10, E11); E13 Anderson Lakes Pkwy → Pioneer Tr (X12), or S of Highwood Ave → Pioneer Tr (X11, X12) when the Anderson Lakes station is flow-invalid; E14 Pioneer Tr → Old Shakopee Rd (X13; E15 lies downstream of the Old Shakopee Rd station, so it does not bias this balance).

**Reported for every metered ramp:** the median and IQR of Passage/Bal and Queue/Bal in both windows and the link-scale gap (calibration days; validation days after validation, for information only); the resulting source (F4).

**Sensitivity (reported, not gated):** J and every gate row at the frozen parameters (no refit) with (i) each switched ramp replaying its balance-derived inflow (v1's rule) and (ii) each controlled ramp replaying its Queue detectors (the demand detector of mode C; §7 R1 (e)).

**3.3.3 Freeway-to-freeway merges (E7, E8, E10, E11).** They replay their measured Merge counts as d_o into an unmetered origin. **Disclosure:** on days when the corridor queue reaches them, these counts are **served (capped) flows, not demand**. The coarse data-fact indicator says the queue reached Highwood Ave (just upstream of the I-494 merges) on 37 of 38 Wednesdays (97 %) with a congested Pioneer Tr; the I-494 merges carry about 38 % of the PM inflow between Valley View Rd and Pioneer Tr; the round-2 review estimates that the I-494 merge counts fall to about 0.89 of their pre-queue level once the queue arrives (§0.5 item 5). The replayed input therefore carries part of the real queue's timing (a "leak"). Calibration replays served flows. **Demand reconstruction for counterfactual runs is a separate later protocol, with its family fixed here** (§7 R2).

**No-leak replay (mode R-NL; reported only; issue 23).**
- For each freeway-to-freeway merge m, its **queued bins** on day d are the bins in which the nearest event-valid station upstream of m is below 45 mph: Bren Rd for E7, T.H.62 for E8, Highwood Ave for E10 and E11.
- In those bins, the replayed count is replaced by s_m,d · P_m(t), where:
  - P_m(t) = the median over usable calibration days of m's 5-min count at clock time t;
  - s_m,d = Σ count / Σ P_m over the 12 unqueued bins immediately before the day's first queued bin (s_m,d = 1 if fewer than 6 such bins exist).
- Everything else is as in mode R. The frozen plant is run once in R-NL on the usable validation days after the gate. ΔP3-k, ΔP4-k, ΔP7a-k and ΔP7b (R-NL − R) are reported as the size of the queue-timing leak.
- Disclosure: in the PM most calibration days are queued at the I-494 merges, so P_m is itself largely a served-flow profile. R-NL removes the timing leak more than it restores the demand level.

**3.3.4 Class-B elements (15-min balances; fixed now).** For a link from station u to station d with one unknown element y and measured entrances E and exits X:
- stored vehicles N(t) = ℓ · [K_u(t) + K_d(t)] / 2, with K the station density over all lanes (occupancy × 5280 / field length, converted to veh/km) and ℓ the link length;
- unknown entrance: y = q_d + ΣX − q_u − ΣE + ΔN/Δt; unknown exit: y = q_u + ΣE − q_d − ΣX − ΔN/Δt; Δt = 15 min, ΔN from the 5-min densities at the start and end of the bin;
- clipped at ≥ 0; the clipped volume is reported per element and day; a day is excluded if any element's clipped volume exceeds 2 % of its daily total (§3.5 E1).

| Element | Link (u → d) | Other elements in the link |
|---|---|---|
| X6+X7 (T.H.62 WB + EB, lumped at km −2.549) | Bren Rd → T.H.62 | E6 (Passage), E7 (Merge) |
| X9 W 78th St | S of Valley View Rd (3 lanes) → I-494 (3 lanes) | none |
| X10 I-494 EB | I-494 (3 lanes) → Highwood Ave | none |
| E15 Old Shakopee Rd | Old Shakopee Rd → T.H.101 | X14, X15 (not used under §1.7 (c)) |

The lumped T.H.62 sink leaves the mainline at its first element (km −2.549); the data cannot split it. The storage term is an approximation; during bottleneck onset and recovery the balances used by the ramp rule (§3.3.2) carry an error, reported as the share of the ramp's daily inflow in bins with |ΔN/Δt| > 10 % of the balance. (v1's class-B row for E14 is removed: a switched ramp now replays its Queue detectors.)

**3.3.5 Exit split ratios (fixed now).** β_e(t) = e(t) / F_e(t), with F_e the measured flow **arriving at the diverge**, taken from one reference station with **no entrance between it and the exit**:
- downstream form (preferred): F_e = q_d + e + Σ(other exits between e and d);
- upstream form (fallback, when the downstream station is flow-invalid that day): F_e = q_u − Σ(exits between u and e);
- if neither form is available that day, the day is invalid (§3.5 E1);
- the assignment is the table in §1.2; the build asserts it. The plain upstream-station denominator is never used, and no reference path may contain an undetected entrance (E15).
- β is computed on 5-min bins, smoothed with a centred 3-bin moving average, clipped to [0, 1], and carried forward from the last bin with F_e ≥ 300 veh/h in bins where F_e < 300 veh/h. Class-B exits use their 15-min balance and are held over 15 min.
- **Flow-unreliable reference stations (amended, issue 21):** a station marked flow-unreliable (§3.4) is not used as a reference when another form is available that day. Where it is the only available form (expected: S of Highwood Ave for X11 on the days the Anderson Lakes station is flow-invalid), it is used and flagged, and the implied bias of β_e (the station's median signed residual from §3.4) is reported. Otherwise the shared-station test could exclude most days through X11 alone.
- Build check (calibration days): Σ_t β_e F_e Δt equals the measured daily exit volume within 1 % for every measured exit; the Anderson Lakes Pkwy fallback share is reported (expected high: 5424 dead on 43/52 Wednesdays per the review).

### 3.4 Conservation check and station flow reliability (calibration days decide; fixed now)

- **Closed links:** both end stations flow-valid and every element between them class M (after §3.3.2; a ramp replaying its Queue detectors is class M). Links closed by a class-B element are listed and not checked.
- **Statistic:** e_link,d = |Σ(inflow − outflow)| / Σ inflow over 05:00–23:00; its signed version ẽ_link,d = Σ(inflow − outflow) / Σ inflow.
- **Shared-station test (new; issue 21; step 5 of §3.8).** For each station s that bounds two closable links (upstream link ending at s, downstream link starting at s), on the calibration days on which both are closed (at least 8, otherwise not testable): s is **flow-unreliable** if, on more than **50 %** of those days, the two signed residuals have opposite signs, each |ẽ| > **1 %**, and their ratio of magnitudes lies within [0.5, 2] (a station over-count gives a negative residual on its upstream link and a positive one on its downstream link, an under-count the reverse) [reviewer's values, adopted]. Run after the ramp rule (§3.8), so that a Passage fault already corrected by §3.3.2 cannot make a sound station look faulty.
- **Detector-fault rule (calibration days only, before any fit; step 6 of §3.8):** a closed link with e > 3 % on more than 20 % of **the calibration days on which it is closed** (passing steps 1–3 of §3.8) is systematic. Its downstream station is marked **flow-unreliable**, the link is merged with the next one, and the merged link is re-tested with the same rule until none is systematic.
- **Consequences of flow-unreliable** (either rule): dropped from the flow terms (§4.2) and from balance closures (its two links are merged for §3.4 and for any later balance); as a β reference only per §3.3.5; its speed stays. The frozen classification, link by link with its e distribution and the shared-station statistics, goes to the pre-calibration facts (F5).
- **Day rule (both sets):** after the classification, a day is excluded if any remaining closed link has e > 5 %.
- Counts of checkable links per day, and of excluded days per set, are reported.

### 3.5 Day exclusions (both sets; same rules; counted per set and reason)

| ID | Rule |
|---|---|
| E1 data | Fit-layer validity fails for: the upstream boundary station; any class-M entrance or exit detector; any station used in a class-B balance or as a β reference that day (with the fallbacks of §3.3.5); or fewer than 80 % of the 15 interior stations are speed-valid; or a class-B element clips > 2 %; or a closed link fails the §3.4 day rule; or the T.H.101 station is event-invalid for speed (E3 cannot be checked). |
| **E1-B** bottleneck stations (issue 11; amended in v3 for EA-2) | **S of Highwood Ave** is not event-valid (all three lanes, §3.2.1), or Pioneer Tr or Old Shakopee Rd is not event-valid (speed and flow). Without them a bottleneck pair does not exist that day, and "not active" would be an artefact on both sides. Anderson Lakes Pkwy is no longer an E1-B station: it is not in the event layer. Counted per set before any model run. |
| E2 upstream boundary | The Minnetonka Blvd station (event layer, raw speed) is below 45 mph in more than 5 % of its valid 05:00–23:00 bins. |
| E3 downstream | (i) The T.H.101 station (event layer) is below 45 mph for ≥ 3 consecutive 5-min bins within 05:00–23:00 (spillback from beyond T.H.101, outside the model); or (ii) the corridor rule finds a real episode at the pair (Old Shakopee Rd, T.H.101): a bottleneck downstream of B2, outside the controlled system. (ii) is new in v2 and applies under every §1.7 step, so that the truncation step needs no re-definition. |
| E4 weather proxy | On ≥ 50 % of the speed-valid interior stations, the median speed of the station's free-flow bins (06:00–20:00, occupancy < 10 % and flow ≤ 1,200 veh/h/lane) is ≥ 8 mph below that station's median of the same statistic over the calibration days passing steps 1–8 of §3.8 [thresholds: lab convention]. Weather is a held-out test condition (D2.3.1), not plant realism. Optional later cross-check against NOAA daily records [VERIFY source] is reported only. |

**Stop rules (checked before calibration; no rule is relaxed):**
- fewer than 18 usable calibration days → stop and report to the author;
- E2 removes more than one third of either set's real-active days (B1 or B2) → stop and report;
- E3 or E4 removes more than 25 % of either set → stop and report (the author decides on extending the stretch past T.H.13, on new data, or on stopping).

The exclusions apply identically to every real reference statistic of §5 and must apply to the gate's day library (§7 R9).

### 3.6 Pre-calibration data facts (computed after the commit and before calibration; committed as `metanet_precal_facts.json` before the first CMA-ES evaluation)

Decisions use calibration days only. Validation-day statistics are real-side quantities needed for §5.2, the exclusion counts and the model-independent floors L_r,k; no model is run.

| ID | Fact |
|---|---|
| F1 | Element table, lane table, cell table and merge log (must equal §1 for the geometry resolved by §1.7). |
| F2 | Per-set usable days and exclusions by reason (E1, E1-B, E2–E4), with date, real B1/B2 status and demand half. |
| F3 | **Upstream boundary (E2):** count of congested-boundary days per set and in all 52; per bottleneck the 2 × 2 table (boundary congested × real B_k active) with Fisher's exact two-sided p; dates. |
| F4 | Ramp-source table (§3.3.2): ratios in both windows, Queue corroboration, link-scale gap, resulting source per ramp; for the controlled ramps E9, E12, E13, E14 the calibration-day daily totals of the replay detector and the mode-C demand detector (§7 R1 (e)). |
| F5 | Conservation link table, shared-station test, flow-reliability classification (§3.4). |
| F6 | Lane screen (fit-layer speed lanes; the station-days where the EA-1 sensitivity's speed differs from the all-lane speed) and the c_s table with m_G per group, T.H.101 included (§3.2.3–3.2.4). |
| F7 | Bottleneck-mechanism diagnostic outcome per bottleneck (§1.6). |
| F8 | Per bottleneck, on **calibration** active days (B1's C4 window censored at the real B2 onset, §5.1):<br>• median r, IQR and 95 % percentile bootstrap CI (seed 7,190,094) on the calibration **heavy** days at B_k (§5.1); this CI's limits are the R4 targets U_k and Lc_k (§7 R4 (b)). The same statistics over all calibration active days with a C4-usable episode are reported only; the share of days with r ≥ 1; Q_dis per lane; r_cap (§5.5);<br>• the real S1 at the first-active bottleneck on calibration heavy days (§5.4 P9; context for P9(1));<br>• **new in v3 (round 3, issue 0): the merge-section flow per lane** at B1 = (Pioneer Tr + X12)/2 and at B2 = (Old Shakopee Rd + X13)/2. It is given (a) in the C4 discharge window, as the day's mean, and (b) as the pre-onset maximum 3-bin rolling 15-min flow in the 60 min before onset. Medians and IQRs per bottleneck; on calibration days heavy at both, the **paired ratio ρ_d = B2 / B1** for (a) and (b), with median, bootstrap CI (seed 7,190,094) and the share of days with ρ_d > 1;<br>• the exit flows X12 and X13 in discharge.<br>The plant must reproduce the discharge ratio (P5c, §5.3). Its calibration-day ratio is reported before validation (§4.8). |
| F9 | Real queue extent from the most upstream active head on calibration heavy days (§5.4 P7b rule): distribution, and the exits and merges inside it. |
| F10 | Real per-pair episode counts over the whole stretch on calibration days (EA-2 event layer), the share of days on which each bottleneck is active, and the first-breakdown location per day. **B1 counts** (round 3, issue 8):<br>(a) P_1 raw (gated definition);<br>(b) P_1 with c_s-scaled real speeds at both stations;<br>(c) the EA-1 reading (Anderson Lakes Pkwy via the lane-screen lanes, Pioneer Tr), raw and scaled;<br>(d) the through-lane S of Highwood Ave version;<br>(e) on days with every Anderson Lakes Pkwy lane valid, the 1-lane against all-lane agreement (day status and episode minutes).<br>The days with S of Highwood Ave below 40 mph for ≥ 60 consecutive minutes but no B1 or B2 episode. The number of **B1 episodes right-censored by B2** (§5.1) and of censored heavy days (issue 10).<br>**Scale-robustness rule (pre-registered; round 3, issue 3; [lab convention]):** let D = the calibration days on which (a) or (b) flags B1. If (a) and (b) disagree on **more than 25 %** of D, B1's activity is judged to depend on detector scale, and **option (c) applies** for the whole protocol:<br>• the B1 rows (P3-1, P4-1, P5a-1, P5b-1, P6-1, P7a-1, P6s-1, P10a-1, P10b-1, P8s's B1 criterion (Σ_d x_1,d), P5c, and B1's part of P2, P7b, P7c, P8(iii) and P9) are reported only;<br>• P_1 rows leave the F1 trigger set;<br>• c1 is not estimated (c1 ≡ 1; F̂ only for c2).<br>Decided on calibration days before the facts commit. Expected from §0.5 item 8 (no exclusions): 1 disagreement in 27 days, i.e. the rule is not expected to trigger. |
| F11 | Real-side minimum evidence on validation days (§5.2): n_val, n_A, n_A,1, n_A,2, n_H,1, n_H,2, n_H,first, n_H,both (days heavy at both, for P5c), n_H,1u (uncensored heavy B1 days, reported), half sizes. **After an extension (§5.2), every F11 quantity (the minima, L_r,k and N2_q) is recomputed on the final validation set, from real data only, before any model run.** **Model-independent floors L_r,1, L_r,2**: per bottleneck, the lower limit (2.5th percentile) of the 95 % percentile bootstrap CI (10,000 resamples of days, seed 7,190,097) of the real median r over **all** n_H,k real heavy validation days (§5.3 P5b). **Flow null on the actual S_q,d** (§4.2): the median-profile null N2_q built from calibration days, scored on the validation days' S_q,d (median NRMSE_q), as P1a's scale reference. |
| F12 | Freeway-to-freeway share of the corridor's 15:00–19:00 inflow (calibration median), per merge; per merge, the share of real-active days (B1 or B2) on which its nearest upstream station is below 45 mph in ≥ 30 % of episode bins; the R-NL scale factors s_m,d (distribution). |
| F13 | Upstream clip: share of days and of 15:00–19:00 minutes with N of I-394 or S of I-394 below 45 mph (context for the boundary demand). |
| F14 | Configuration-to-data audit (§3.7), including G1/G2 cells with a §1.7 ratio > 1.10. |
| F15 | The weather-proxy and holiday strata. |
| F16 | Downstream capacity check (§1.7): R_i per cell, the lane-check record (source, date, outcome, or "not performed") and the resolution step taken. |

### 3.7 Configuration-to-data audit (unchanged)

The geometry, lanes, field lengths and storage come from the current IRIS configuration, applied to 2023 data. For every detector of the stretch, report the number of 2023 days on which it appears in the cached `_detectors.json`.
- Absent on every day → treated as not existing in 2023: an exit becomes class B (known: 7110, W 78th St); a Queue detector makes its ramp's Queue unusable for §3.3.2 and affects the later demand reconstruction (known in the stretch: 3679 T.H.7 EB, 3670 one of Lincoln Dr's two).
- Absent on some days → those lane-days are invalid (E1).
- Within-year steps (reported): per lane, a monthly median 05:00–06:00 speed step > 10 % makes that lane speed-invalid in the affected months; per closed link, a monthly median e step > 3 % is reported.
- Any lane count or field length contradicted by 2023 data is a disclosed deviation.

### 3.8 Order of the cleaning operations (fixed now; issue 13)

Each step is computed **once**, in this order; no later step feeds back into an earlier one (the merge-and-retest inside the detector-fault rule is part of step 6).
1. Lane-day validity, both layers, all days.
2. Lane screen (§3.2.3) on every valid lane-day of the calibration Wednesdays → frozen speed lanes.
3. Event-layer station validity (committed all-lane rule, EA-2); E1-B, E2, E3 on all days.
4. Ramp rule (§3.3.2) on the calibration days passing 1–3.
5. Shared-station test (§3.4) on the calibration days passing 1–3, with the step-4 sources.
6. Detector-fault classification (§3.4) on the calibration days passing 1–3; denominator per link = the days on which it is closed.
7. Station scaling c_s (§3.2.4) on the calibration days passing 1–3 and every E1 data check other than the speed-valid share.
8. E1 completed on all days (speed-valid share with the frozen speed lanes and c_s drops, class-B clipping, the §3.4 day rule).
9. E4 on all days, with its reference over the calibration days passing 1–8.
10. Stop rules (§3.5).
11. F8, then F16 and the §1.7 resolution (geometry). Steps 1–10 do not depend on the cell table, so they are not repeated.
12. The remaining facts (§3.6), including F10's scale-robustness rule; the real-side minima on validation days (§5.2) and the INCONCLUSIVE check.
13. **If the minima fail (the §5.2 extension rule; round 3, issues 7 and 9):**
    - the extension days are taken from the pre-fetched pull (§0.6 A10); if that pull is incomplete, it is completed first and its request count is logged in the ledger;
    - steps 1, 3, 8 and 9 on the extension days only, with every rule and reference frozen at steps 2, 4–7 and 9 on the calibration Wednesdays; nothing on the calibration side is recomputed;
    - F2, F3 (extension rows), F11 and the minima recomputed on the final validation set.

    **The pre-calibration facts commit is made only after this step** (or after step 12 if no extension is needed; the pre-fetched days then stay unused).

Deviation from the order proposed in round 2: the lane screen moves to step 2 (v2 needed it for EA-1; in v3 only the fit layer and the EA-1 sensitivity use it, and the order is kept); the ramp rule precedes the shared-station test (see §3.4).

---

## 4. Estimation (calibration days only)

### 4.1 Parameters, constants and bounds

**Fitted (n parameters):** per group G1–G3: v_f, ρ_cr, a (9); shared: τ, ν, κ, δ_m, φ (5); **B1 head-capacity factor θ1 (1; new in v3, §2.1, A1 (iii))**. **n = 15**, plus 2 under §1.7 step (b) (ρ_cr,G4, a_G4; v_f,G4 ≡ v_f,G3) and plus 1 per bottleneck in the EXIT branch (C_x,k, §1.6). So 15 ≤ n ≤ 19.

**Fixed:** T = 5 s; ρ_max = 180 veh/km/lane; v_min = 7.4 km/h; Q_o = 2,200 veh/h per ramp lane; c1 = c2 = 1 in the bottleneck cells; no speed-limit term; no θ2 (B2 is at the G3 level; §2.1).

| Parameter | Bounds | Source and status |
|---|---|---|
| v_f (each group) | 80–150 km/h | must exceed observed low-density speeds (review: G3 median 117–120, p90 127–129 km/h at 300–900 veh/h/lane); upper 150 as in Chan, Raghavan & Wu 2026 Table I [VERIFY]; Poole & Kotsialos 2016 used 80–130 [VERIFY] |
| ρ_cr (each group, G4 included) | 15–45 veh/km/lane | Kotsialos et al. 2002: 27.7–35.9 [VERIFY]; Zhao, Roncoli & Yildirimoglu 2025 limits 15–40 [VERIFY] |
| a (each group, G4 included) | 1.0–3.5 | calibrated 1.87–2.50 in Hegyi et al. 2005, Kotsialos et al. 2002, Zhao et al. 2025 [VERIFY] |
| τ | 10–60 s | lower = 2T (§2.5); Kotsialos 18 s; Poole 11.4–22.7 s; Zhao real-data fit 45.5 s [VERIFY] |
| ν | 5–90 km²/h | Kotsialos 60; Poole 40–57; Zhao real-data 87.8 [VERIFY] |
| κ | 5–60 veh/km/lane | Kotsialos 40; Poole 22–29; Zhao 6.6–8.0 [VERIFY] |
| δ_m | 0–4 | Kotsialos 0.012; Poole ≤ 0.093; Zhao up to 4.0 at its bound [VERIFY] |
| φ | 0–4 | Kotsialos 2.2; Poole at its lower bound [VERIFY] |
| θ1 (B1 head cell 26 only) | 0.75–1.05 | [lab convention] (round-3 reviewer's proposal). It multiplies ρ_cr,G3 in cell 26, so with v_f and a shared it scales the head's capacity. The lower bound allows a head about 25 % weaker than G3, well beyond the ≈ 11 % gap in the data (§0.5 item 7). The upper bound allows a slightly stronger head, so that the data, not the bound, decide the sign. Bound activity is reported (below). |
| C_x,k (EXIT branch only) | 900–2,200 veh/h | lab convention (§1.6) |

Literature status: the values above were reported by the review's literature lens; the author has not read these sources in full ([VERIFY]). Wang et al. 2022 (TR-C) was not read by anyone and is not cited as a source. Bounds are frozen at the commit and **never widened after a fit**. A parameter within 1 % of the bound range of either bound at the frozen optimum is reported as **bound-active** next to the identifiability flags; it does not trigger a refit.

### 4.2 Error definitions (used by J and P1)

For a variable x ∈ {q (veh/h), v (km/h)}, a day d and a set S of valid (station, 5-min bin) pairs:

**NRMSE_x(d, S) = sqrt( (1/|S|) Σ_{(s,b)∈S} (x̂_{s,b} − x_{s,b})² ) / ( (1/|S|) Σ_{(s,b)∈S} x_{s,b} )**

x̂ = model value at the station (§1.5), x = fit-layer real value (speeds scaled by c_s, §3.2.4). Pooling is over the station-bins of that day (no per-station averaging); normalisation is always by the mean of the real data over the same pairs. A (day, set) with fewer than 100 valid pairs is not scored (counted).

**Congestion window W_d** = 15:00–19:00 ∪ [onset − 30 min, end + 30 min] of every real B1 or B2 episode of day d (event layer). On days without a real episode, W_d = 15:00–19:00, so spurious congestion in the queue area is penalised as well as missed congestion.

**Sets:**
- **S_q,d (flow; amended, issue 22):** (i) the flow stations (interior, flow-valid, not closed by a class-B element, not flow-unreliable) × 05:00–23:00; plus (ii) the stations in Q_A whose flow is closed by a class-B balance (I-494, Highwood Ave), flow-valid, × W_d only. In free flow their replayed flow is an identity of the inputs; in the congestion windows it depends on the model's storage and discharge, so it carries information there. A ramp switched by §3.3.2 replays its Queue detectors, so its downstream station stays in (i).
- **S_v,d (speed, whole day):** interior speed-valid stations not dropped by §3.2.4, plus T.H.101 (not under §1.7 (c)) × 05:00–23:00, bins with K > 0.
- **Q_A (queue area):** the speed-valid stations with 0.37 ≤ km ≤ 7.20 that are **not dropped by §3.2.4** (issue 13): S of Valley View Rd, I-494, Highwood Ave, S of Highwood Ave, Anderson Lakes Pkwy, Pioneer Tr, Old Shakopee Rd. It covers both bottlenecks and the queue reach in the data facts; disclosed, not tuned further.
- **S_c,d (congestion term):** Q_A × W_d.

### 4.3 Objective (unchanged)

**J_d = 0.25 · NRMSE_q(d, S_q,d) + 0.25 · NRMSE_v(d, S_v,d) + 0.5 · NRMSE_v(d, S_c,d); J = mean of J_d over the usable calibration days.**

Why this weighting: free flow dominates the whole-day sets (the review measured a median 2.4 % of station-bins below 40 mph), and with replayed inputs the flow term is governed mainly by conservation, while the speed equation carries most parameters (argued in Chan et al. 2026 [VERIFY]). The congestion term (speed in the queue area during the bottlenecks' active periods and the PM window) keeps CMA-ES from trading bottleneck fidelity for free-flow fit. Weights and windows are fixed now and not tuned. The v0 objective (0.5/0.5 whole day) is reported at the frozen optimum.

### 4.4 Optimiser (settings frozen; record the pycma version)

- pycma CMA-ES in the normalised space [0, 1]^n, log-scaled for τ, ν, κ and linear otherwise; bound handling by pycma's BoundTransform [VERIFY that it is the default in the installed version].
- **8 restarts, seeds 7,190,011–7,190,018.** Restart i: initial mean drawn uniformly from [0.25, 0.75]^n with its seed; σ0 = 0.25; popsize **λ = 4 + ⌊3 ln n⌋** (**12 for every n in 15–19**, v3); **4,000 evaluations**; tolerance-based stops (tolfun, tolx, tolstagnation and similar) disabled, so the budget is the only stopping rule.
- **Convergence (calibration J only):** report per restart the final J, final σ, the covariance condition number and the relative J improvement over the last 20 % of evaluations. If the best restart improved by > 1 % in that window, **all** restarts are continued once, on the same seed streams, to 8,000 evaluations before anything else is run; both results are logged and the continued one is frozen.
- The restart with the lowest J is the **nominal plant**, frozen with all its settings in `metanet_calibration.json` and committed **before any validation run**.
- Any other optimiser setting counts as a new calibration: it is logged in the ledger and never replaces this one.

### 4.5 Identifiability (reported, not gated)

- **Restart spread:** restarts with J ≤ 1.02 · J_best. If ≥ 3 qualify, report for each parameter the range of those restarts divided by its bound width (normalised coordinates); otherwise "not assessable". No coefficient of variation is computed.
- **Profiles** for v_f(G3), ρ_cr(G3), τ, ν, κ, δ_m, φ and **θ1 (new in v3)**: 9 equally spaced points across each bound (normalised); at each point the parameter is fixed and the other n − 1 are re-optimised by CMA-ES warm-started at the frozen optimum (σ0 = 0.1, λ = 4 + ⌊3 ln(n − 1)⌋ = 11 for n − 1 = 14, 12 for n − 1 ≥ 15; 600 evaluations), **seeds 7,190,030–7,190,092** for the first seven (seed = 7,190,030 + 9p + j for parameter p = 0…6 in the order listed and point j = 0…8) and **seeds 7,190,100–7,190,108 for θ1** (seed = 7,190,100 + j; inside the approved block 7,190,000–7,190,999). Under-optimisation can only make a profile look less flat; this is stated in the report. Also reported: the profile of the model's B2/B1 merge-section discharge ratio on calibration days along θ1's profile.
- A parameter is flagged **non-identifiable** if its profile J stays ≤ 1.02 · J_best over ≥ 50 % of its bound width, or its restart range is ≥ 50 % of its bound width, or it is "not assessable". G4's parameters (if any) are reported by restart spread and bound activity only; they are expected to be weakly identified (the section is free-flowing).
- Also reported: the capacity of each group v_f ρ_cr e^{−1/a} and of B1's head cell θ1 v_f,G3 ρ_cr,G3 e^{−1/a_G3} (same spread and profile-derived range), the v_f–ρ_cr correlation within each group across near-best restarts, bound-active parameters (θ1 included), and per-group median (model − detector) speed over 05:00–06:00.

### 4.6 Plant ensemble (no hidden variants)

- **Admissible:** any restart with J ≤ 1.02 · J_best that also passes, on its own, N0 (with its own step-halving check) and every deterministic row and, if the nominal outcome is PASS (stochastic) or PASS (substitute spread), every stochastic row with its own F̂ (or F̂_T, by the same §4.7 rule) and its own c2\* (validation days used **as a filter only**, never to fit).
- **Ensemble:** the nominal plant plus at most **2** admissible members, the ones farthest from it in (τ, ν, κ, δ_m, φ), each normalised by its bound width. Chosen before any gate run; frozen and listed with their J and gate results. An empty set is reported as such.
- The gate uses the ensemble by the rule in §7 R5.

### 4.7 Per-day capacity factors c1, c2 (stochastic element for the gate; calibration days only)

**Definition.** c_k multiplies the critical density (hence the capacity) of B_k's cells everywhere ρ_cr appears in them (FD, origin supply term):
- c1 multiplies θ1 ρ_cr,G3 in cell 26 and ρ_cr,G3 in cells 27–30 (§2.1);
- c2 multiplies ρ_cr,G3 in cells 31–32.

c1 = c2 = 1 is the frozen plant.

**Relocation and the support bound c2\* (new in v3; round 3, issue 1).**
- **Why.** c2 scales only cells 31–32. Cell 33 (and G4 under §1.7 (b)) runs at c = 1. Above roughly c2 ≈ 1 + X13/C ≈ 1.05, the binding cell moves downstream of the Old Shakopee Rd station. The plant would then show a bottleneck outside the controlled system, which E3(ii) excludes on the real side.
- **Relocation** on a model-day is flagged if (a) or (b) holds:
  - (a) any cell downstream of cell 32 has ρ_i > ρ_cr,i for ≥ 3 consecutive 5-min bins (bin means);
  - (b) the model has an episode at (Old Shakopee Rd, T.H.101) (observation operator, §3.2.4; under §1.7 (c), (a) alone).
- **c2\*** = the largest g ∈ G such that no grid pair (c1, c2) with c2 ≤ g shows relocation on any usable calibration day. It is computed per plant (nominal, each ensemble member, F1) from the grid runs below, with no extra runs. A build check logs, at c2\* + 0.01 (if c2\* < 1.20), the calibration day(s) and cell where relocation occurs. If c2\* < 1.00, the frozen plant itself relocates B2 on some calibration day: **F̂ is not estimable** (rule (iv)).
- The **estimation grid for c2** is G₂ = {g ∈ G : g ≤ c2\*}. The grid for c1 is G.

**Estimator (fixed now; joint, issue 20).** With every §4.1 parameter frozen, for each usable calibration day d and each grid pair (c1, c2) ∈ G × G, **G = {0.80, 0.81, …, 1.20}** (41 values, 1,681 pairs; the 2-D grid is coarser than v1's 1-D 0.005 grid to keep the cost bounded, §8.2), run the replay and record:
- for k = 1, 2:
  - E_k,d(c1, c2) = the model has ≥ 1 episode at P_k;
  - O_k,d(c1, c2) = a model episode at P_k overlaps (±60 min, §5.1) a real P_k episode;
- Z_d(c1, c2) = the model has ≥ 1 **spurious** episode (P8's definition, §5.4) or a relocation (new in v3);
- L_d(c1, c2) = NRMSE_v(d, S_c,d).

Then, per day, using only pairs with c2 ∈ G₂:
- **Consistent set C_d** = the pairs at which (i) for each k, O_k,d holds if B_k is real-active that day and E_k,d does not hold if B_k is real-inactive, **and (ii) Z_d does not hold** (no model episode at any pair outside {P_1, P_2} that the real day lacks, and no relocation; round 3, issue 1 (i)).
- **If C_d is not empty:** (ĉ1,d, ĉ2,d) = argmin over C_d of L_d (ties: nearest to (1, 1), then the smaller c1).
  - The component of each **real-active** bottleneck is an **exact observation**.
  - The component of each **real-inactive** bottleneck is **right-censored** at c_low,k,d = the smallest g in its grid (G for c1, G₂ for c2) such that the model has no P_k episode at c_k = g′ for every g′ ≥ g in that grid. The other factor is held at its exact estimate or, if that one is censored too, at its grid maximum (1.20 for c1, c2\* for c2).
- **If C_d is empty**, the day is **not reproducible**: it is excluded from F̂ and counted, with the bottleneck(s) that were real-active.
- Days on which E_k,d is not monotone in c_k are reported.
- If the F10 scale-robustness rule triggered option (c), c1 ≡ 1 throughout: the grid is 1-D in c2, and F̂ has no c1 component.

**F̂ (fixed now).**
- **Marginals F̂_1, F̂_2:** the Kaplan–Meier estimate from the exact and right-censored components (ties: events before censorings). If the largest observation is censored, the remaining mass is placed at the grid maximum: 1.20 for k = 1, c2\* for k = 2. This is the high-capacity placement, conservative for breakdown frequency, and it is disclosed. KM assumes that censoring is independent of c; this is an assumption, reported with the checks below.
- **Joint draw** (used by N0s, P8s, P6s, P10 and the gate): draw a reproducible usable calibration day uniformly. For each k: if its component is exact, take ĉ_k,d; if it is censored, draw from F̂_k conditional on c > c_low,k,d (the upper atom if no mass remains there). This keeps the dependence between c1 and c2 that the days with both components exact show.
- **Re-centring and clipping (fixed now; issue 1 (a); clipping new in v3, round 3, issue 1 (ii)):**
  1. c_k ← c_k / m_k, with m_k = the median of F̂_k, so that the median gate day is the c = 1 plant judged by P1–P9 and the spread comes from F̂;
  2. clip c1 to [0.80, 1.20] and c2 to [0.80, min(1.20, c2\*)], the range on which the estimator was evaluated.

  The shares of clipped draws per k are reported next to the stochastic rows. The gate protocol may not change this rule (§7 R3).
- **Not estimable (fixed now; issue 1 (c); (iv) new in v3):** F̂ is declared not estimable if any of these holds [lab conventions]:
  - (i) more than **20 %** of the calibration days with a real B1 or B2 episode are not reproducible;
  - (ii) for either k, the KM mass placed at the upper atom exceeds **25 %**;
  - (iii) either k has fewer than **8** exact observations;
  - (iv) c2\* < 1.00.

**Expected counts and the risk they imply (stated in v3; round 3, issue 11; estimates, not facts).**
- On the reviewer's estimates (§0.5 item 7) and the v3 B1 definition (§0.5 item 8), about **23 usable calibration days**:
  - B2 real-active on about **9**;
  - B1 real-active on about **23**, i.e. every usable day (the reviewer's count on usable days, §0.5 item 7: 23 of 23; the pair is active on 27/28 days before exclusions, §0.5 item 8);
  - so either bottleneck is active on about 23 days.
- Rule (iii) then lets B2 lose **at most 1** of its ~9 days to non-reproducibility (or to censoring at both ends). Rule (i) allows about 4 non-reproducible days in total. B1 is expected to have no real-inactive usable day, so F̂_1 rests on exact observations only, with no right-censored B1 component.
- **A false "not estimable" through rule (iii) at B2 is therefore likely**, even for a sound plant. The limits are **not** loosened. Instead the consequence is fixed now: the substitute below, and otherwise "deterministic-only" with its fixed consequence (§0.3).

**Substitute spread F̂_T (pre-registered now; round 3, issues 6 and 11; author item A4).**
- **Used only if** F̂ is not estimable by rule (ii) or (iii) **and by neither (i) nor (iv)**. Rule (i) signals a structural misfit, and rule (iv) a relocating plant; no spread can repair either.
- **Fit.** Per k, a censored-normal (Tobit) maximum-likelihood fit (μ_k, σ_k) to the same exact and right-censored components. This is the fit already reported under v2. It is usable only if each k has **≥ 5 exact observations** [lab convention] and the fit converges with σ_k > 0.
- **Draws.**
  - c_k ~ N(μ_k, σ_k²), independently for k = 1, 2; the joint structure is not estimated, which is disclosed;
  - re-centred to median 1 (c_k ← c_k / μ_k);
  - clipped as above.
- **Gating.** The stochastic rows are run on F̂_T, with the same seed 7,190,095 and the same criteria and family-wise levels (§5.3). The outcome label is "PASS, substitute spread" (§0.3).
- The choice of F̂_T is fixed here, before calibration. It is not chosen after any stochastic result.

**Reported alongside:**
- m_k and the mass of F̂_k below and above 1;
- c2\* and the relocation flags along the grid;
- the Tobit fit (μ_k, σ_k) as a parametric check, also when F̂ is estimable;
- Spearman correlations, with bootstrap CIs (seed 7,190,094): ĉ_k with daily boundary demand (active days); ĉ_k with the real Q_dis,k on heavy days (expected positive); ĉ_1 with ĉ_2 on days with both exact;
- the CV of the real Q_dis,k on heavy calibration days against the spread of F̂_k.

**Use.** P1–P9 run at **c1 = c2 = 1**. N0s, P8s, P6s and P10 use **200 joint, re-centred, clipped draws per usable validation day** (seed 7,190,095), exactly as the gate will use them. The gate samples per §7 R3. F̂ (and c2\*) is re-estimated, with these rules, for each ensemble member and for F1 if used.

### 4.8 Reported calibration-day diagnostics (before any validation run)

Each J term separately; the v0 whole-day J; per bottleneck the model's Q_dis and r against the real values on the same calibration days and the B_k-active agreement; **the model's B2/B1 merge-section discharge ratio against F8's real ratio on the same calibration days (P5c's statistic; reported before validation, not gated here)**; θ1 and the head-cell capacity; c2\* and the relocation flags; clip counts (with the non-jam v_min count, §2.5); the step-halving check (gated as part of N0, §2.5; a failure here ends the route before any validation run); origin misfits. Per bottleneck, two benchmarks fixed here, before validation:
- the best **daily-demand threshold classifier** of B_k activity (a stylised ceiling for P3-k, §9.1);
- the **demand-half climatology**: p_clim,k(h) = (R_k,h + 0.5) / (n_h + 1), with R_k,h the B_k-active calibration days in half h and the halves split at the calibration-day median of daily boundary demand. This is P10b's benchmark.

---

## 5. Plant gate (validation days; real data as the reference; fixed now)

The frozen plant (θ1 included) is driven by each usable validation day's measured inputs in replay mode. Deterministic rows run at c1 = c2 = 1; stochastic rows use F̂, or F̂_T under the substitute rule (§4.7). Outcomes as in §0.3.

### 5.1 Model-side event detection (identical to the real side)

- Model 5-min speed and flow are read at every real station's km (§1.5) and **masked per bin** (issue 11): the model value is NaN wherever the real station's 5-min bin is NaN, and the whole station-day is masked where the real station-day is event-invalid (committed all-lane validity, EA-2). Model and real therefore use the same valid station-bins, including in the 5-of-7 windows and the C4 averaging windows.
- **Observation operator (new in v3; round 3, issue 8):** before any event rule, each model station speed is converted to detector scale, v_model,s / c_s (§3.2.4). Real speeds stay raw. Unit test 14 checks that a model equal to the scaled real speeds reproduces the raw real events exactly.
- The corridor rule (EA-2 event layer, §3.2.1) is applied **unchanged** to both: consecutive valid stations ≤ 3 km apart (the named pair P_1 excepted); v_u < 40 mph and v_d − v_u ≥ 20 mph in ≥ 5 of 7 consecutive bins; onset = the first bin of the first qualifying window; episodes separated by < 30 min are merged; episode end = the last covered bin.
- **Bottleneck pairs:** **P_1 = (S of Highwood Ave, Pioneer Tr)** for B1 (EA-2); P_2 = (Pioneer Tr, Old Shakopee Rd) for B2. **"B_k active"** (model or real) = at least one episode at P_k, AM or PM. A day is **real-active** if B1 or B2 is real-active.
- **B1 right-censored by B2 (new in v3; round 3, issue 10).** When B2's queue reaches Pioneer Tr, P_1's condition (Pioneer Tr ≥ 20 mph faster) can no longer hold, so B1 is hidden, not over.
  - A real B1 episode is **censored** if a real B2 episode's onset t_c falls inside it or within 30 min after its end. The rule is anchored on real data and applied identically to both sides: the model's matched B1 episode on that day is censored at the same real t_c.
  - On a censored day, B1's **duration** on each side = min(end, t_c) − onset. It is 0 for an episode on **either side** starting at or after t_c, and 0 if unmatched.
  - On a censored day, **B1's C4 discharge window** on each side ends at min(end, t_c).
  - The number of censored episodes and days is reported (F10, §5.5).
- **Overlap:** episodes [s, e] and [s′, e′] overlap within ±60 min if s ≤ e′ + 60 min and s′ ≤ e + 60 min.
- **Episode matching, per bottleneck:** every real B_k episode is matched to the model B_k episode with the nearest onset within ±90 min, one-to-one (smallest |Δonset| first).
- **Heavy day at B_k:** the day's longest real B_k episode (for B1, its censored part on a censored day) is ≥ 30 min and usable by the C4 estimator (with B1's censored window). **Heavy matched:** in addition, that episode is matched to a model B_k episode that is usable by the C4 estimator (same window rule). **Uncensored heavy B1 day:** a heavy B1 day whose longest episode is not censored (n_H,1u, reported). **Heavy at both:** heavy at B1 and at B2 (n_H,both; P5c).
- **First-active bottleneck b of a day:** the bottleneck of the day's earliest real B1 or B2 episode (ties: B1). **Heavy first-active day:** b is heavy that day, and the other bottleneck has no real episode in progress at the start of P9's window (60 min before the onset of b's longest real episode). P9 uses b's longest real episode and the model episode matched to it, i.e. the same episodes as P5-b.
- **Q_dis, r:** the C4 block of `analyse_corridor`, applied to the 5-min flow at the bottleneck's downstream station (B1: Pioneer Tr, 2 lanes; B2: Old Shakopee Rd, 2 lanes). Real side: unchanged (the day's longest real episode at P_k), except that B1's window ends at the real B2 onset on censored days. **Model side: the C4 formulas applied to the model episode matched to the real longest episode** (issue 17), with the same window end. P5a, P5b, P5c, P7a and P9 all use this same episode.
- **Merge-section discharge (P5c; new in v3):** per bottleneck and side, the mean over the C4 discharge window of (downstream station flow + the exit between the pair's head and that station, X12 for B1 and X13 for B2) / 2 lanes. The model's exit flow is its s_e (§2.4); the real one is the exit detector. The day's ratio is ρ_d = B2 value / B1 value, model and real.

### 5.2 Minimum evidence and outcomes

Checked on **real data only**, after §3 cleaning and **before the model is run on any validation day** (F11):
- n_val (usable validation days) ≥ 16, so that each demand half has ≥ 8 days (P6, P6s);
- n_A,k (usable validation days with real B_k active) ≥ 8 for k = 1 and k = 2 (P3-k, P4-k);
- n_H,k (heavy days at B_k) ≥ 6 for k = 1 and k = 2 (P5-k, P7a-k);
- n_H,first (heavy first-active days) ≥ 6 (P9).

n_A (usable validation days with B1 or B2 real-active; the denominator of P1c and P2) is reported with them; when the minima above are met, n_A ≥ 8. n_H,both (days heavy at both) is not a minimum: if n_H,both < 6, P5c is reported, not gated (it is new in v3, and making it a minimum would add an INCONCLUSIVE path).

The minima are **not** lowered in v3 (round 3, issue 9).

If any minimum fails, the plant gate is **INCONCLUSIVE** on the Wednesdays: not run, never PASS, no F1, reported to the author with the counts. The extension below then follows, on the pre-fetched days (A10).

**Extension rule (fixed now; issue 19; made explicit in v3, round 3, issues 7 and 9).** The only extension is **all 2023 Tuesdays and Thursdays** (104 days; pre-fetched at the author's request on 2026-10-05, §0.6 A10; none was cached at the time of the §0.5 item 8 inspection).
- **When:** only if the F11 minima fail on the validation Wednesdays, at §8.6 step 3, **before any calibration run and before the pre-calibration facts commit** (§3.8 step 13). No model exists at that point, so no model output can inform it.
- **Data (author item A10, resolved 2026-10-05):** the days were pre-fetched at the author's explicit request in the session ("do it now, in parallel, just in case"; commit `4af0674`; the full stretch including aux 7097/7077 and the Green detectors, §7 R1). The request count is in the ledger row. **No value from these days is read** unless this rule triggers. If the pre-fetch is incomplete at that point, it is completed first and its count logged (§3.8 step 13). The earlier ≤ 18,200 bound and approval step no longer apply.
- **Dates:** the date list is generated by code before any request.
- **Status of the days:** every extension day is a **validation day** under the same §3 rules, with every frozen reference unchanged:
  - the lane screen, c_s, the ramp sources, the flow-reliability classification and E4's reference all stay those of the calibration Wednesdays;
  - the split, the calibration days, θ1 and F̂ are unchanged;
  - the same minima apply;
  - P6, P6s and P10 are computed over all usable validation days; P10b's climatology stays the calibration-Wednesday one.
- **n-dependent quantities:** every F11 quantity (n_val and the other minima, L_r,k, N2_q), the P6 halves and the P8 tolerances max(2, ⌈0.10 · n_val⌉) are recomputed on the final validation set, from real data only, before any model run (§3.6 F11).
- If the minima are still not met, INCONCLUSIVE is final.
- "Both outcomes" means the INCONCLUSIVE record (with its counts) plus the verdict on the extended set; both are logged. R12 applies to the Tuesdays and Thursdays.

**Expected counts (replaces v2's "about 20 usable"; an estimate from a disclosed read-only inspection, §0.5 item 7, not a computed fact).**
- Reviewer, with §3 rules approximated: 23 of 28 calibration days and **16 of 24 validation days** usable under the scored-station reading of the gap rule. The v3 input reading (§3.2.2) also loses 2023-04-12, which gives **n_val ≈ 15**.
- Validation counts with v2's EA-1 B1: n_A,2 = 9 (8 under the input reading), n_H,2 = 9 (8), n_A,1 = 10, n_H,1 = 10, n_H,first = 14. Under EA-2, B1 is expected on nearly every usable day (the reviewer counted the S of Highwood Ave pair on 15 of 16 validation days).
- E1-B changes in v3 (S of Highwood Ave replaces Anderson Lakes Pkwy), so the E1-B count may change; this was not estimated.
- Steps not reproduced by the reviewer (the step-6 merges, the exact E4) can only lower n_val.
- **INCONCLUSIVE on the Wednesdays alone is therefore the expected outcome**, and the extension (A10) is the expected route to a gate run.

**When the real minima are met, a model-dependent shortfall is a FAIL** (the model did not reproduce enough of the real events), never INCONCLUSIVE:
- P4-k needs ≥ 75 % of the real B_k episodes matched;
- P5-k needs heavy matched days ≥ max(6, ⌈0.75 · n_H,k⌉);
- P9 needs heavy matched first-active days ≥ max(6, ⌈0.75 · n_H,first⌉), and P9(2) needs ≥ 5 days with model excess;
- P5c (when gated, n_H,both ≥ 6) needs days heavy matched at both ≥ max(6, ⌈0.75 · n_H,both⌉).

### 5.3 Gated checks

**Deterministic rows (c1 = c2 = 1); k = 1, 2 means one row per bottleneck.**

| ID | Check | Qualifying set (denominator, anchored on real data) | Criterion |
|---|---|---|---|
| **N0** numerics | Clipped cell-steps per validation day (density, upper speed, and v_min activations with ρ_i < ρ_cr,i; §2.5); step-halving at the frozen optimum (§2.5) | all usable validation days; step-halving on the usable calibration days | ≤ 1 % of cell-steps on every day; step-halving \|ΔJ\|/J ≤ 0.05 with unchanged P_1 and P_2 episode days |
| **P1a** flow fit | NRMSE_q(d, S_q,d) | all usable validation days | median ≤ **0.10** (expected weakly discriminating, §5.4) |
| **P1b** speed sanity | NRMSE_v(d, S_v,d) | all usable validation days | median ≤ **0.20** (a sanity floor, §5.4) |
| **P1c** queue-area speed | NRMSE_v on Q_A × [onset − 30, end + 30] of every real B1/B2 episode, model vs two day-agnostic nulls N1, N2 (§5.4) | the n_A real-active days | vs N1: upper bound of the 95 % bootstrap CI of the median paired difference (model − N1) **< 0**; vs N2: median paired difference **< 0** |
| **P2** where | The first breakdown location (§5.4) | the n_A real-active days; a day without a model episode overlapping the real earliest episode fails | ≥ **80 %** of n_A |
| **P3-k** whether | Real-anchored agreement on B_k activity (§5.4) | all usable validation days | agreement ≥ **75 %**; confusion matrix and Wilson CI reported |
| **P4-k** when | \|model onset − real onset\| over **all** real B_k episodes; an unmatched episode scores 90 min | all real B_k episodes on usable validation days | median ≤ **15 min** and ≥ **75 %** of them matched |
| **P5a-k** discharge | D_i = Q_dis,model,i / Q_dis,real,i − 1 | heavy matched days at B_k (≥ max(6, ⌈0.75 n_H,k⌉)) | \|median D_i\| ≤ **0.05** (two-sided) |
| **P5c** head ratio (new in v3; round 3, issue 0) | Paired: D_i = ρ_model,i / ρ_real,i − 1, ρ = B2 / B1 merge-section discharge (§5.1) | days heavy matched at both (≥ max(6, ⌈0.75 n_H,both⌉)); gated only if n_H,both ≥ 6, otherwise reported | \|median D_i\| ≤ **0.05** (two-sided), CI reported |
| **P5b-k** drop not exaggerated | (i) paired: median of (r_model,i − r_real,i); (ii) median r_model,i | heavy matched days at B_k | (i) ≥ **−0.02**, CI reported; and (ii) ≥ **L_r,k**, the floor frozen in F11 before any model run |
| **P6-k** narrow band | B_k-active counts in the lower and upper half of daily demand (§5.4) | all usable validation days | (a) \|M_h − R_h\| ≤ k_h in both halves (binomial tolerance at the realised n); (b) if the real gradient > 0, the model's gradient > 0 and (c) ≥ 0.5 × the real gradient |
| **P7a-k** duration | \|dur_model − dur_real\|; dur_model = the matched model episode's duration of any length, or 0 if unmatched. **B1 on censored days: both durations censored at the real B2 onset (§5.1; v3, round 3, issue 10)** | **all** n_H,k heavy days at B_k | median ≤ **30 min**; for B1 the same statistic on the uncensored heavy days alone is reported |
| **P7b** queue extent | Extent from the most upstream active head (§5.4) | all real heavy days (heavy at B1 or B2); a day without a matched model episode counts as a miss | model extent = the real extent station or an adjacent speed-valid station on ≥ **70 %** of the days |
| **P7c** system duration (new in v3; round 3, issue 10) | \|dur_sys,model − dur_sys,real\| (§5.4) | all real heavy days (heavy at B1 or B2); no overlapping model union interval → dur_sys,model = 0 | median ≤ **30 min** |
| **P8** no spurious or extra episodes | (i)–(ii) model episodes at pairs other than P_1 and P_2; (iii) model episodes at P_k that overlap no real P_k episode (§5.4) | all usable validation days | (i) every pair: model episode-days − real episode-days ≤ **max(2, ⌈0.10 · n_val⌉)** (v3; round 3, issue 7); (ii) days with ≥ 1 spurious model episode ≤ **max(2, ⌈0.10 · n_val⌉)**; (iii) per bottleneck k, the number of days with ≥ 1 extra model P_k episode ≤ **max(2, ⌈0.10 · n_val⌉)** (v3; round 3, issue 5); unmatched model episode-minutes reported |
| **P9** D-check at the first-active bottleneck | (1) overshoot S1, paired; (2) plateau / excess (§5.4) | heavy matched first-active days (≥ max(6, ⌈0.75 n_H,first⌉)); (2) on days with model excess > 0 | (1) median of (S1_model − S1_real) ≤ **+0.03**, CI reported; (2) median ≥ **1.2**, with ≥ 5 qualifying days |

**Stochastic rows.** They run only under a usable spread: F̂, or F̂_T under §4.7's substitute rule. Each uses 200 joint, re-centred, clipped draws per usable validation day (seed 7,190,095), with p̂_k,d = (number of draws with B_k active + 0.5) / 201.

| ID | Check | Qualifying set | Criterion |
|---|---|---|---|
| **N0s** numerics under the draws (new in v3; round 3, issue 1 (iii)) | Per day, the share of draws with a non-finite value, or with clipped cell-steps (§2.5) > 1 % | all usable validation days | no non-finite draw; share ≤ **0.05** on every day [lab convention] |
| **P8s** spurious heads under the draws (new in v3; round 3, issue 1 (iii)) | Per day d, z_d = the share of draws with ≥ 1 spurious model episode (§5.4) or a relocation (§4.7); x_k,d = the share with ≥ 1 extra P_k episode (P8(iii)) | all usable validation days | Σ_d z_d ≤ **max(2, ⌈0.10 · n_val⌉)** and, per k, Σ_d x_k,d ≤ **max(2, ⌈0.10 · n_val⌉)** (the P8 limits applied to expected counts); the clipped-draw shares (§4.7) reported |
| **P6s-k** narrow band, stochastic | Per demand half h (as P6): R_h against the Poisson-binomial distribution of the model count M_h with probabilities {p̂_k,d : d ∈ h} | all usable validation days | (a) in both halves, P(M_h ≤ R_h) ≥ **0.003135** and P(M_h ≥ R_h) ≥ **0.003135** (family-wise sizing below); (b)–(c) as P6 on the expected shares Σ p̂_k,d / n_h |
| **P10a-k** not over-confident | The number S of days whose real B_k status had probability < 0.05 under the plant (§5.4) | all usable validation days | S ≤ the **98.75th** percentile of its Poisson-binomial distribution under the plant (family-wise sizing below) |
| **P10b-k** skill (non-inferiority; v3) | Brier score of p̂_k,d against the real B_k status | all usable validation days | Brier_plant ≤ Brier_clim + **0.02** [lab convention], with Brier_clim the demand-half climatology (§4.8) on the same days |

**Family-wise sizing of the stochastic rows (new in v3; round 3, issue 6).**
- **The family.** Four rows are *sized* tests, built so that a plant whose probabilities are right fails each one with a known probability: **P6s-1 (a), P6s-2 (a), P10a-1, P10a-2**. In v2 each was sized at about 5 %. Their conjunction then rejected a correct stochastic plant about 19 % of the time (stylised, independence assumed).
- **Bonferroni.** v3 controls the family-wise false-FAIL rate of these four at **≤ 5 %** under any dependence, at **α_row = 0.05 / 4 = 0.0125** per row:
  - **P6s-k (a):** two halves, each two-sided. The per-half level is 1 − (1 − 0.0125)^{1/2} = 0.006270, so each tail gets **0.003135**. (v2 used 0.01265 per tail, i.e. about 5 % per row.)
  - **P10a-k:** the **98.75th** percentile (v2: 95th).
- **Why not Holm.** Holm would need a single p-value per row, and P6s (a) is itself a conjunction over halves and tails. Bonferroni with fixed per-row levels is simpler and needs no assumption about dependence.
- **Unsized criteria.** P6s (b)–(c), P10b, N0s and P8s are criteria on expectations or margins, not sized tests, so they are outside the family. Their false-FAIL rate for a correct plant is not computed, and this is disclosed (§9.1).
  - P10b is now a non-inferiority comparison. Under v2's point comparison, a plant whose true skill equals the climatology failed about half the time.
- **Consequence of a failure:** see §0.3 (substitute spread, deterministic-only). It is fixed now and is not decided after the stochastic results are seen.

**Threshold status.**
- **[lab convention]:** P1a, P1b, P2, P3, P4, P5a, P5c, P7 (P7a, P7b, P7c), P8 (all three parts), the 1 % in N0 and its non-jam v_min rule, the step-halving 5 %, the −0.02 in P5b(i), the +0.03 in P9(1), the 75 % match share in P4, the 0.75 · n_H minima, the 0.05 in P10a, P10b's 0.02 margin, and N0s's 0.05.
- **Reviewers' values adopted** (still lab conventions, i.e. without a literature anchor; §9.2 tags them "(reviewer's value)"): the P4/P5/P9 minima, P5b(i) and P9(1) (round 2); P5c's form and 5 %, P8(iii) and the n_val scaling of P8 (i) and (iii), the step-halving rule and its 5 %, and the Bonferroni levels (round 3).
- **Defined relative to the real data, to nulls or to a calibration-day benchmark:** P5b(ii), P6, P6s, P10b and P1c.
- **The family-wise 5 %** is the round-3 reviewer's value (issue 6); its level carries over the per-row 5 % that v2 already used. The per-row levels (0.0125; P6s tails 0.003135; P10a's 98.75th percentile) follow from it by Bonferroni.
- **P9(2)'s 1.2** follows the gate draft §1 D-check and supersedes its wording (gate T1 refers to P9).

**What P5b and P9(1) bound.** P5b bounds the drop and P9(1) bounds the pre-breakdown overshoot, each paired against the real data on the same days. Both are drop-side constraints: a plant whose discharge falls too far below its pre-breakdown flow fails one or both. The reason they are one-sided, and its status as an inference, are in §0.4. P5a is two-sided because the discharge level sets when and how long each bottleneck is active, in both directions.

### 5.4 Definitions behind the table

**P1 context (literature lens; [VERIFY], the author has not read these in full).** No comparable out-of-sample METANET fit threshold was found. The fits the review read are in-sample, on short windows, with other metrics: Poole & Kotsialos 2016 report per-station speed errors of about 6–7 % on the calibration day and much larger errors on other days; Chan, Raghavan & Wu 2026 report in-sample MAPE of about 28–35 % for flow and 5–28 % for speed; Zhao, Roncoli & Yildirimoglu 2025 report a speed RMSE of 18.6 km/h and a flow RMSE of 832 veh/h on three lanes. Kotsialos et al. 2002 report no numerical fit error. These are context, not thresholds. Therefore:
- P1a's 0.10 is a lab convention. Its scale reference is the median-profile flow null **on the actual S_q,d**, computed from real data before any model run (F11); the review's 0.123 was computed on a different station set and is no longer used. In replay, station flows on closed links are close to identities of the replayed inputs, so P1a is expected to be weakly discriminating (issues 16, 22). The discriminating flow checks are P5a at both bottlenecks and the congestion-window part of S_q,d.
- P1b's 0.20 is kept only as a sanity floor: a never-congesting predictor scored 0.126, so P1b cannot tell good plants from bad ones.
- P1c carries the discriminating fit test, in the queue area while either bottleneck is active.

**P1c nulls** (built from usable calibration days only, on scaled speeds): **N1** = per station, the median of all 05:00–23:00 speeds ≥ 45 mph (a plant that never congests); **N2** = per station and 5-min bin, the median calibration-day speed (the typical day). Per real-active day, D_d = NRMSE_v,model − NRMSE_v,null on the same pairs. The bootstrap (10,000 resamples of days, seed 7,190,093) gives the CI of median D. N1 must be beaten with confidence; N2 must be beaten on the median (the CI is reported), because a mechanistic model driven by the day's inputs should at least match the typical profile, while requiring a CI against N2 at n_A ≈ 10 would make a false FAIL likely.

**P2 first breakdown location.** On each real-active day, let e* be the day's earliest real B1 or B2 episode (ties: B1). Among the model episodes, at any pair, that overlap e* (±60 min), the one with the earliest onset must be at e*'s pair. A day without any overlapping model episode fails.

**P3-k agreement (issue 10).** A real-B_k-active day agrees only if a model B_k episode overlaps (±60 min) a real B_k episode. A real-B_k-inactive day agrees only if the model has no B_k episode. A model episode at another time of day does not count as agreement.

**P6 halves and tolerance (per bottleneck; unchanged rule).** Daily demand = the measured 05:00–23:00 total at the Minnetonka Blvd boundary (an input, identical for model and real). Sort the usable validation days by it; lower half L, upper half U (the median day goes to U if n_val is odd). M_h, R_h = model and real counts of B_k-active days in half h, n_h its size. Tolerance: p̃_h = (R_h + 0.5)/(n_h + 1); **k_h = the smallest integer k with P(|X − round(n_h p̃_h)| ≤ k) ≥ 0.9747 for X ~ Binomial(n_h, p̃_h)** (0.9747 = 0.95^{1/2}, so a plant that reproduces the breakdown probability in both halves fails (a) with probability ≈ 5 % in this stylised model). Gradient = M_U/n_U − M_L/n_L (model) and R_U/n_U − R_L/n_L (real). If the real gradient is ≤ 0, (b)–(c) are not applied and the report says the narrow band is absent at B_k in the validation data (likely at B1 if, as D3.4 states, it breaks down on most days). Why halves, not quartiles: at n_q = 5–7 per quartile the same rule (at the per-quartile level 0.95^{1/4}) gives tolerances of 2–3 days, up to ±60 pp, so a quartile test has almost no power; at n_h = 8–12 it gives 2–4 days (about ±25–35 pp; computed for every possible R_h before the v1 draft). This is still weak, and it is disclosed as such: (a) guards the level, (b)–(c) guard the demand dependence. A step plant (no breakdown in the lower half, breakdown on every upper-half day) can pass the deterministic P6 (issue 9); the stochastic rows are the guard against over-confidence. Per-quartile shares (model and real, with exact binomial CIs) and the same table keyed on the Bren Rd flow (comparable with corridor analysis v2) are reported.

**P6s (issue 9).** The model count in a half is random under the stochastic plant, so P6's single-binomial tolerance would give a false-FAIL rate of about 13–21 % at n_h = 8–12 (reviewer's stylised computation); the Poisson-binomial form restores the nominal level for a plant whose probabilities are right. v2 set the two tails at 0.01265 = (1 − 0.9747)/2 per half, matching P6's ≈ 5 % per row. **v3 sets them at 0.003135 per tail**, so that the row is at 0.0125 within the family-wise 5 % (§5.3).

**P7b queue extent (from the most upstream active head).**
- **Start station:** real side, the upstream station of the most upstream bottleneck with a real episode that day (**S of Highwood Ave** for B1 under EA-2, Pioneer Tr for B2). Model side, the same for the most upstream bottleneck with a model episode matched to a real episode that day.
- **Window:** the union of that side's episodes at P_1 and P_2 that day (model: the matched episodes).
- **Congested station:** event-layer speed < 40 mph for ≥ 15 consecutive minutes overlapping the window.
- **Extent:** the most upstream congested station in the unbroken run of congested stations that starts at the start station and goes upstream. Event-invalid stations are skipped and do not break the run; the model uses the same mask.
- A day without a matched model episode at either bottleneck counts as a miss. The signed median difference of the B_k durations (P7a-k) is reported too.

**P7c system duration (new in v3; round 3, issue 10).**
- **Real union interval:** merge the day's real P_1 and P_2 episodes into one set of intervals, with the < 30-min gap rule of §5.1. dur_sys,real = the length of the longest resulting interval.
- **Model union interval:** the same construction on the model's P_1 and P_2 episodes. dur_sys,model = the length of the longest model union interval that overlaps (±60 min) the real one, or 0 if none overlaps.
- The statistic does not depend on which head holds the queue at a given moment, so B1's hidden phase on censored days is inside it. B1's own duration (P7a-1) is censored there (§5.1).

**P8 spurious and extra episodes.**
- **(i)–(ii) Other pairs.** The corridor rule runs on all event-valid pairs of the stretch (model and real, same mask, observation operator on the model side). A model episode at a pair P ∉ {P_1, P_2} is **spurious** if the real data have no episode that day at P or at any pair sharing a station with P.
- **(iii) Extra episodes at P_1 and P_2 (new in v3; round 3, issue 5).** P_1 and P_2 are **no longer exempt** from the spurious count. A model P_k episode is **extra** if it overlaps no real P_k episode (±60 min). This is counted on every usable validation day, real-active or not, as episode-days per bottleneck. Their unmatched model episode-minutes are reported. Without (iii), a plant with a spurious AM breakdown on top of a correct PM episode would pass every row and add "removable" delay to the gate.
- **F1 trigger.** It is unchanged: an extra episode is a breakdown that should not occur, which F1's post-breakdown switch cannot remove (§6.1).
- **Reported:** per-pair model-minus-real counts and the list of spurious and extra episodes (pair, onset, duration).

**P9 D-check (model side), at the first-active bottleneck b of each heavy matched first-active day.**
- **Arrivals at b, A_b(t)** (issues 4, 14), in 15-min bins: boundary flow + every entrance inflow **as replayed** (Passage, Queue, Merge or class-B balance) up to and including b's merge (E13 for B1, E14 for B2) − every exit flow **as replayed** (class-M counts and class-B balances, including X6+X7, X9 and X10) up to and including the last exit upstream of b's downstream station (X12 for B1, X13 for B2), each shifted by its free-flow travel time to that station at the frozen group v_f. It is an input series, the same for both sides; on clipped days it is a lower bound on demand (§3.3.3). Unit test 12 checks it.
- **(1) Overshoot:** S1 = the maximum 3-bin rolling 15-min flow at b's downstream station in [onset − 60 min, end] divided by that side's 2-lane Q_dis, computed for the model and the real data on the same day. The criterion is paired (issue 15).
- **(2) Plateau / excess:** plateau = the longest contiguous run of 5-min bins containing the onset with model flow ≥ 0.95 × model Q_dis; excess = the minutes with A_b > model Q_dis; S2 = plateau / excess, on days with excess > 0 (days with excess = 0 are counted).
- **Interaction:** if a real episode of the other bottleneck starts inside b's window, the window, the plateau and the excess are truncated at that onset on both sides (the window is anchored on real data; the other queue then holds or alters the arrivals); the truncations are reported.
- The real-data counterpart of (2) is reported only, as a lower-bound form (§5.5): with served counts at merges inside the queue, the real excess is unobservable, so "the real data show this" is not claimed. The gate draft's absolute rule (plateau ≥ 1.2 × excess) applies to the plant only.

**P10 definitions (issue 9).** For bottleneck k and usable validation day d, y_d = 1 if B_k is real-active, else 0; π_d = p̂_k,d if y_d = 1, else 1 − p̂_k,d (the probability the plant gave the real outcome).
- **P10a:** S_obs = #{d : π_d < 0.05}. Under the plant, S ~ Poisson-binomial with per-day probabilities s_d = min(p̂_k,d, 1 − p̂_k,d) if that minimum is < 0.05, else 0. PASS if S_obs ≤ the smallest x with P(S ≤ x) ≥ **0.9875** (v3; v2: 0.95). A plant that is right about its probabilities fails with probability ≤ 1.25 %.
- **P10b:** Brier_k = mean_d (p̂_k,d − y_d)²; the benchmark is the same mean for p_clim,k(h(d)) (§4.8), with h(d) the day's half under the calibration-day threshold. **v3: PASS if Brier_k ≤ Brier_clim,k + 0.02** (non-inferiority; margin fixed now [lab convention]; round 3, issue 6 (ii)). The difference Brier_k − Brier_clim,k is reported with its bootstrap CI (seed 7,190,093). The expected agreement mean_d π_d and the Brier score of the calibration-day threshold classifier are reported. Issue 1 proposed either expected agreement ≥ 0.75 or a Brier score at least as good as that classifier. The climatology is adopted as the gated benchmark because, in the stylised numbers, it is the stronger of the two (§9.1), and because expected agreement penalises a plant that is right to be uncertain.

### 5.5 Reported, not gated

- MAPE and RMSE (km/h, veh/h) on the whole-day and queue-area sets; per-station errors; the null scores (including the F11 flow null).
- Per bottleneck: paired differences r_model − r_real with a bootstrap CI; the real median r and CI per set (calibration, validation, pooled 52 days) next to the model's; the "same days" CI version of v1's P5b. If the model's median r at B_k lies above the validation CI upper bound, the plant is labelled "drop under-reproduced at B_k; conservative for breakdown-prevention gains" in every later result, and the author is told before the gate runs.
- **r_cap,k** = Q_dis / (maximum 3-bin rolling 15-min flow in the 60 min before onset), the corridor protocol's `capacity_15min` window, for model and real. Disclosed limitation: a maximum over noisy detector bins biases the real r_cap downwards relative to smoother model output. The corridor-v2 ratio of medians at B2 (1,850.4 / 1,938.0 ≈ 0.955) is unpaired. Per-day real r outside [0.8, 1.2] is listed and kept (medians are used).
- Real D-check, lower-bound form, at the first-active bottleneck: (a) the real S1 distribution; (b) the growth of stored vehicles between the boundary and b during queue growth, from served arrivals and the measured outflow (§3.3.4 storage), and whether the real data meet plateau ≥ 1.2 × excess with served arrivals.
- Upstream congestion-front speed from onset times at successive event-valid stations inside the extent (an estimate needs ≥ 2 stations; n/a with fewer than 5 estimates). **R-b (internal stop-and-go wave speed) is n/a** at 5-min / ~1 km resolution; this limits any wave-based VSL claim, and the SUMO confirmation must test it.
- Exposure to blocking, model vs real: for each exit and freeway merge between km 1.7 and B2, the share of episode minutes with the nearest upstream station congested.
- Excess vehicle-hours between the extent station and the head, model/real ratio, 15:00–20:00.
- Origin misfits and clipped ramp volume (§2.3); clip counts; step-halving; the T.H.101 measured-density boundary as a sensitivity (frozen parameters, no refit; not under §1.7 (c)); the ramp-source sensitivities (§3.3.2).
- **The weave sensitivity** (§1.4): P2–P5 at both bottlenecks at the frozen parameters, no refit.
- **The no-leak replay** (§3.3.3): ΔP3-k, ΔP4-k, ΔP7a-k, ΔP7b.
- **B1 definition sensitivities (v3; §3.2.1):**
  - P2, P3-1, P4-1, P5-1, P7a-1 and P10-1 recomputed with B1 on the EA-1 reading (Anderson Lakes Pkwy via 5423, Pioneer Tr; v2's rule), and with the through-lane S of Highwood Ave version;
  - per day, the B1 episodes seen only by EA-1 or only by EA-2;
  - c_s at S of Highwood Ave and Anderson Lakes Pkwy; if needed, P2–P5 and P10 with both sides on the scaled scale (§3.2.4).
- **B1 censoring (v3):** the number of censored B1 episodes and heavy days, model and real; P7a-1 on uncensored heavy B1 days only.
- **Stochastic support (v3):** c2\*, the clipped-draw shares per k, the relocation share per validation day, and the Tobit fit (also when F̂ is used).
- Stochastic plant: expected agreement and the threshold-classifier Brier per bottleneck (§5.4); with c1 = c2 = 1 the stochastic rows reduce to the deterministic plant, which is reported in the same table.
- Holiday-adjacent stratum: P1, P3-k, P4-k separately.
- **Weekend days:** the same metrics, reported only.
- Validation-day ramp ratios (§3.3.2), for information.
- Every P statistic with its n and a 95 % interval (percentile bootstrap over days for medians, Wilson for shares).

### 5.6 P-T transfer to 2024 (defined here; executed under the gate protocol; issues 16, 22)

After the gate protocol is committed and 2024 is opened, and **before any controller is run or tuned**, the frozen plant(s), with no refit and no change of parameters, inputs, cleaning rules or F̂, are driven in replay by the 2024 days the gate will use, after the §3.7 audit on those days.
- **Cleaning:** every §3 rule, with E1, E1-B, E2, E3 and E4 (E4's reference stays the 2023 calibration days).
- **Real-side minima, before any model run:** ≥ 16 usable 2024 days and ≥ 8 real-active days per bottleneck; P5a-k is run only if n_H,k ≥ 6 on 2024 days, otherwise reported as not run. If the minima fail, P-T is **INCONCLUSIVE** and there is no 2024 gate until an author-approved addendum adds days.
- **Gated rows**, with the §5.3 thresholds and the §5.2 model-side minima: N0, P1a (expected weakly discriminating, §5.4), P1c, P3-k, P4-k, P5a-k, and, if the gate uses F̂ (or F̂_T), P10a-k and P10b-k at the v3 levels of §5.3 (98.75th percentile; non-inferiority margin 0.02; the 2023 calibration-day climatology as P10b's benchmark). N0 uses the v3 clipping count (§2.5).
- **FAIL** → the plant is not valid for the 2024 gate; the gate does not run and the author is told. 2024 data may never be used to refit or reselect this plant. The outcome is logged either way.

---

## 6. Failure handling (fixed now)

### 6.1 F1: the single pre-registered structural fallback

*Our own METANET adaptation of the two-capacity, memory-based capacity-drop idea of Srivastava & Geroliminis 2013 (TR-C 30:161–177) [VERIFY: read by the review, not by the author]. The source is a first-order LWR/Godunov model, not METANET; this adaptation is ours and is disclosed as such.*

- **Trigger (issue 12 (a); amended in v3).** F1 is fitted only if the failed deterministic rows include at least one check that its post-breakdown switch can affect: **P1c, P4-k, P5a-k, P5b-k, P7a-k, P7b, P7c or P9**.
  - **P7c** (new) is in the set, because the switch changes how long a queue lasts.
  - **P5c** (new) is **not** in the set: one shared Δ scales both heads alike and cannot change their ratio (round 3, issue 0). The head ratio is θ1's job in the base fit.
  - **P8(iii)** (new) is not in the set: an extra episode is an occurrence error.
  - If F10's scale-robustness rule triggered option (c), the B1 rows leave the set (§3.6 F10).
  - If the failure set contains no check in the set (only N0, P1a, P1b, P2, P3-k, P5c, P6-k or P8), the outcome is a route stop (§6.2) without F1: for those checks only a refit, not the structure, could change the verdict.
  - Failures confined to the stochastic rows lead to §0.3 (substitute spread or deterministic-only), not to F1.
- **Cells:** the bottleneck cells **B1 ∪ B2 = 26–32** (§1.4). No other cell changes.
- **Memory state:** m_i(k) ∈ {0, 1}, m_i = 0 at 04:00 every day. After each density update: m_i(k) = 1 if ρ_i(k) > ρ_cr,i, or if m_i(k−1) = 1 and ρ_i(k) > η · ρ_cr,i; otherwise 0. (The name m avoids a clash with the exit flow s.)
- **Switch:** while m_i = 1, cell i uses ρ_cr,i^F1 = (1 − Δ) · ρ_cr,i everywhere ρ_cr appears (FD, supply term). With v_f and a unchanged, its capacity falls by the factor (1 − Δ).
- **New parameters (2), shared by both bottlenecks:** Δ ∈ [0, 0.15] (about 3 × the corridor's 75th-percentile drop at B2, 1 − 0.952 ≈ 4.8 %; [lab convention]); η ∈ [0.6, 1.0] (release hysteresis; [lab convention]). One shared Δ adds no per-bottleneck freedom; the real drops at B1 and B2 are of similar size in the available estimates (§0.4).
- **No per-cell v_f and no other new freedom** (per-cell v_f at the merge cells would make P2 pass almost by construction).
- **Refit:** all n base parameters (θ1 included) plus Δ and η, jointly, from a cold start; same objective, days and settings as §4.4 with λ = 4 + ⌊3 ln(n + 2)⌋ (12 for n + 2 ≤ 20, 13 for n + 2 = 21; v3's n is 15–19), **seeds 7,190,021–7,190,028**, 4,000 evaluations each, the same convergence rule; the best restart is frozen. Identifiability: restart spread and bound activity only (no profiles; disclosed). F̂ (§4.7) and the ensemble (§4.6) are re-derived for F1; its stochastic rows use the same draw seed 7,190,095 (common random numbers); its gate statistics use bootstrap seed 7,190,096.
- **Judged on** N0 (with its own step-halving check, §2.5) and every row of §5.3, unchanged, on the same validation days. No validation-day result may inform any F1 choice: F1 is fully specified here.
- **Δ at zero (issue 12 (b)).** If the frozen Δ is bound-active at 0 (within 1 % of its range), F1 is the base structure optimised a second time. The outcome is recorded as **"base structure, second optimisation"**, not as an F1 PASS, and goes to the author as a **FAIL by default**.
- **Label (issue 12 (c)).** Every F1 PASS is labelled **"second look on the same validation days"** in `metanet_calibration.json` and in every downstream result.

### 6.2 After F1

If F1 is not triggered, or also fails, see §0.3 (route stop; SUMO is an author decision). No criterion is relaxed. Both outcomes are logged.

### 6.3 Change rule (unchanged)

After the first validation evaluation, model or job code may change **only** to correct a deviation from this file's equations (§2) or data rules (§3). Each fix comes with a unit test, committed with the fix, that fails before it and passes after. Calibration, the plant gate and F1 (if used) are then re-run in full, with the original seeds, and **both outcomes are logged**. Any other change to the model, inputs, objective or criteria is a new protocol version, committed before it is run, with fresh optimiser seeds and a decision-log entry.

---

## 7. Requirements this protocol places on later protocols

| ID | Requirement (binding on the controlled-plant and gate protocols; to be restated there before any gate run) |
|---|---|
| R1 | **Controlled mode C.** Exogenous inputs identical across arms and seeds within a day: the mainstream origin; the 6 upstream metered ramps (their replay inflow; demand mode is unavailable upstream because Queue detectors 3679 and 3670 have no 2023 data); the class-B elements; the split ratios. The 4 controlled ramps take reconstructed demand (Queue-detector arrivals). Required before use: (a) the storage unit of the IRIS `storage` attribute confirmed [VERIFY] and storage in vehicles = storage × 0.3048 × storage lanes / s_jam, with s_jam from a cited source and a ±25 % sensitivity; (b) `max_wait` (240 s at all four controlled ramps) enforced for every arm through the same queue-override rule; (c) **P0 ramp-demand validity** per controlled ramp-day (\|Σ arrivals − Σ release\| ≤ 5 % of Σ release, with the release = the ramp's replay inflow; reconstructed queue within [0, 1.2 × storage] in ≥ 95 % of bins), with a fallback if fewer than 80 % of ramp-days are valid; where the replay inflow is the Queue detector itself (E14 if switched), P0 is not informative and the ramp is listed; (d) a **mode-equivalence check**: mode C with each controlled ramp's meter rate set to its replay inflow must pass N0 and every deterministic row with the §5.3 thresholds, and the same check in mode R-NL is reported (the replay leak, §3.3.3, would otherwise be inherited unseen); (e) **detector agreement** (issue 21): for E9, E12, E13 and E14, the replay inflow detector and the mode-C demand detector must agree within 5 % on calibration-day daily totals (F4); a ramp that does not is listed, and the gate protocol states its reconciliation before any gate run. Origin queues are unbounded and count in the delay metric; vehicles are never dropped. |
| R2 | **Freeway-to-freeway demand on clipped days (issue 23).** (a) **Family fixed now:** in the bins where a merge lies inside the real day's queue (its nearest upstream station below 45 mph, from that day's real data, independent of the arm), its demand = s_m,d · P_m(t) as in mode R-NL (§3.3.3), with P_m from the tuning-year days; elsewhere, the served counts. No other uplift family may be used. (b) Disclosed as model-imposed, not observed. (c) **A GO must also hold with zero uplift** (served counts everywhere), as R4 requires on the low-drop variant. (d) Gate results are reported split by the day's reconstructed-minus-served volume (above or below its median over the gate days), replacing v1's with/without-queue split, which would leave almost no "without" days. Any H1 statement that true demand "can be reconstructed from upstream detectors" is limited to the upstream boundary and the metered ramps. |
| R3 | **Capacity factors (issues 1, 9, 20; round 3, issues 1, 6, 11).** (a) Each gate day draws (c1, c2) from the joint F̂ of the plant in use by the §4.7 rule, **re-centred** (c_k / m_k) and **clipped** (c1 to [0.80, 1.20], c2 to [0.80, min(1.20, c2\*)]), or from F̂_T under the same rule after "PASS, substitute spread". This rule is fixed here and may not be changed by the gate protocol; the clipped shares are reported. (b) F̂ may be used only after the outcome PASS, and F̂_T only after "PASS, substitute spread" (§0.3). After "PASS, deterministic-only" the gate may run on the deterministic plant (c1 = c2 = 1) but **only a KILL counts**; a GO there is "deterministic-plant GO, not a GO" (§0.3; fixed now, author item A4, not open to a later decision). θ1 is part of the frozen plant in every case. (c) **No arm sees c1 or c2**, the informed reference I included (it knows the true demand, not the true capacities). mpc_f, I_mpc and I_plan use c1 = c2 = 1 (the re-centred medians) or their own fitted models; mpc_f's model is refitted on tuning-seed plant data generated with random (c1, c2). (d) A sensitivity with c1 = c2 = 1 is reported. (e) H2's capacity classes are quantiles of the re-centred F̂ marginal of the bottleneck its VSL serves (R6), with the other factor drawn by (a). |
| R4 | **Drop cells, per bottleneck, set on calibration days only (issues 5, 8, 18).** (a) Measured drop of the plant in use at B_k: Δ_drop,k = 1 − (the plant's median r at B_k on the **calibration** heavy matched days of the frozen primary plant; this day set is frozen with the plant). (b) Variants: **low-drop**, target median r_model,k = min(1, U_k); **high-drop**, target = Lc_k; U_k and Lc_k are the upper and lower limits of the 95 % CI of the real median r at B_k on calibration heavy days (F8). (c) Construction: the F1 switch on B_k's cells with its own Δ_k ∈ **[−0.15, 0.15]** (Δ_k < 0 raises capacity after activation, to cancel drop that the base dynamics produce) and η = the frozen F1 η if F1 is the plant in use, else **0.9** [lab convention; η = 1.0 would give no hysteresis, so a Δ < 0 switch could chatter]. Δ_k is found by bisection on the frozen calibration day set to within ±0.5 pp of the target; if the target is unattainable within the domain, the nearest attainable Δ_drop,k is used and reported. Everything else is frozen. Both bottlenecks are varied together in each variant. (d) **A GO must also hold on the low-drop variant**; a GO that appears only at a drop above the primary's is not a GO. This, not the monotonicity argument of §0.4, is the operative guard. (e) Each variant's P5b-k and P9(1) on the validation days are reported (not gated). (f) No validation day is used to set any variant (§8.5). |
| R5 | **Ensemble.** The GO/KILL decision is computed on the nominal plant; every arm is re-tuned on each ensemble member with the same budget and tuning days. A GO additionally requires H ≥ 10 % with the paired CI lower bound > 0 on every member; otherwise it is "plant-dependent" and not a GO. A nominal KILL with a member meeting the GO criterion stays a KILL, recorded as "plant-dependent KILL" with the parameter direction that flips it; it is never rescued. All per-member H values are logged. |
| R6 | **VSL (H2 and every VSL-using arm: mtfc_rm, specialist, the VSL-extended mpc_f).** Primary form and α_0 as in §2.8, sensitivity α ∈ {0.0, 0.2}; H2's T0 must pass under both response forms (Hegyi min form and the MTFC modified FD); H2's T2 and gate are run on the primary form with the variant reported; an H2 GO also needs the SUMO T0 to agree. A GO involving a VSL arm must keep the sign of H at α = 0.0 and 0.2, otherwise it is reported as α-sensitive and is not a claim. mpc_f never receives the plant's α or FD parameters. b_i applies only inside a declared VSL application area. **Two bottlenecks (issue 20):** H2's protocol must declare which head its MTFC VSL area serves. "1.5–3 km upstream of the bottleneck" means km ≈ 1.06–2.56 for B1 (the I-494 / Marth Rd merge area, G2) or km ≈ 3.12–4.62 for B2, which contains the B1 merge E13 and the Anderson Lakes Pkwy station. H2's T0 must show, for the declared area, that it holds traffic back without creating a new bottleneck or masking the other one (episode counts at P_1 and P_2 reported per arm). Every VSL result states that the VSL response is assumed, not validated. |
| R7 | **P-T** (§5.6) runs before any controller on 2024 days. |
| R8 | **D-check.** Gate T1 refers to P9 of this protocol (first-active bottleneck; paired overshoot bound); the real-data version is a lower bound only, and the absolute plateau rule applies to the plant. |
| R9 | **Exclusions.** E1-B, E2–E4 (and the weather-proxy rule) apply to the real days of the gate's day library; weather days are a held-out test (D2.3.1). |
| R10 | **Corridor-analysis addendum** (dated; not an edit of committed results). It records (a) the counter-evidence to "metering limits the drop": Srivastava & Geroliminis 2013 report about 15 % at a U.S.169 northbound merge, of similar size with and without metering [VERIFY]; different direction, site and years, so it does not transfer directly; and (b) the two-bottleneck finding: the committed estimator cannot see B1 on most days (Anderson Lakes Pkwy dropped when 5424 is dead; S of Highwood Ave → Pioneer Tr is 3.145 km > 3 km), so the corridor analysis' C1 share and bottleneck location describe B2 only. From this protocol on, the amended estimator (§3.2.1) is used. |
| R11 | **Decision log.** The author records the D3.1 wording change (§0.4, A5), the split change (A3), the event-layer amendment **EA-2** (A9; replaces v2's EA-1, and restates how "B1 active" in D3.4 is measured), the B2 merge reading and θ1 (A1), the stochastic-plant rules including the deterministic-only consequence (A4), and the pre-fetch request (A10, resolved 2026-10-05). The boundary deviation is recorded as D3.5. |
| R12 | **Calendar types (issue 22).** Before the gate uses any day type other than Wednesday (2023 tuning days or 2024 test days), the frozen plant must pass the P-T rows (§5.6, same minima and rows) on real days of that type, after an author-approved pull. Until then the gate's day library is restricted to Wednesdays. The Tuesdays and Thursdays of the §5.2 extension (pre-fetched, A10), if used, count as passed for that type only if the plant gate on the extended set passes. |
| R13 | **H1 on two bottlenecks (D3.4).** Before any gate run, the H1 protocol must: (a) map each controlled ramp to the bottleneck(s) it feeds: E9 (km 0.000) and E12 (km 1.833) feed B1 and, through B1, B2; E13 (km 4.055) is B1's merge; E14 (km 6.118) is B2's merge; (b) fix, for every ALINEA/HERO arm, the occupancy measurement location of each ramp at a location where the real corridor has a station, so that the comparator is implementable on the real road; (c) state HERO's coordination across the two heads (which ramps serve as master for which head, and how queue balancing crosses B1); (d) report, per arm, episode occurrence, onset, duration and extent at B1 and B2, and the system-level duration (P7c), using the EA-2 event layer with the observation operator. B1's duration is reported both uncensored and censored as in §5.1, i.e. at the **real** day's B2 onset (an arm-independent anchor), never at an arm's own B2 onset; both are reported only; (e) state the hypothesis locus per bottleneck. At B1, day-to-day variety lies in queue duration and extent, not occurrence (D3.4; consistent with B1 active on about 27/28 calibration days under EA-2, §0.5 item 8), so the prize there is mainly in shortening and containing the queue; the breakdown-prevention prize lies mainly at B2. **H1's queue-duration outcome is the system-level duration P7c (§5.4), computed per arm on that arm's own P_1 and P_2 episodes, and nothing else. P7c is a system outcome covering both heads; it is not labelled a B1 outcome, and per-bottleneck attribution is reported, not tested.** The censored B1 duration (§5.1) and the uncensored B1 duration are reported only: they are never an H1 outcome, a gate metric or part of a GO. Reason: in closed-loop arms there is no real B2 onset for the arm's queue, and censoring at an arm's own B2 onset would let an arm that makes B2 break down earlier shorten B1's measured duration; (f) keep c1 and c2 hidden from I (R3). |

---

## 8. Seeds, compute, outputs, statistics, logging

### 8.1 Seeds (approved block 7,190,000–7,190,999; this protocol uses only 7,190,000–099 and, new in v3, 7,190,100–108)

| Seeds | Use |
|---|---|
| 7,190,001–010 | **already used** by the P3 jam-release pre-check (ledger, 2026-10-05); not reused here (v1 wrongly listed them as unused) |
| 7,190,011–018 | base CMA-ES restarts (8) |
| 7,190,021–028 | F1 CMA-ES restarts (8) |
| 7,190,030–092 | profile re-optimisations (7 parameters × 9 points) |
| 7,190,100–108 | profile re-optimisations for θ1 (9 points; new in v3) |
| 7,190,093 | bootstrap of the base-plant gate statistics (P1c, P5b(i) CI, P5c CI, P9(1) CI, the P10b difference CI, all CIs) |
| 7,190,094 | bootstrap of pre-calibration real facts on calibration days (F8, including the merge-section ratio, and the §4.7 correlations) |
| 7,190,095 | joint capacity-factor draws for the stochastic rows (base plant, ensemble members and F1; F̂ or F̂_T) |
| 7,190,096 | bootstrap of the F1 gate statistics |
| 7,190,097 | bootstrap of the model-independent floors L_r,k (F11; real validation data only) |
| all others in 000–108 | unused; a re-run after a bug fix reuses the original seeds |

The model is deterministic given its inputs; the capacity grid (§4.7) uses no seed. No real day is used for timing: the timing test runs on synthetic inputs.

### 8.2 Compute

- CMA-ES, profile and capacity-grid batches run as background jobs on **≤ 32 worker processes** (libsumo is not involved) under `vsl_lab/ops/guard.py` (CPU > 90 % for 2 consecutive minutes → pause rules; the 95 ± 3 °C thermal band with the `thermal.json` limits; decisions logged in the batch's `thermal.csv`). Before every batch: check machine resources and that the v6 sessions are idle (otherwise CPU load < 15 %). `export OMP_NUM_THREADS=1`; `venv314`.
- Cost (estimate, to be measured on synthetic inputs before the first run): 36 cells × 13,680 steps per model-day; one evaluation = up to 28 model-days. The base fit is 32,000 evaluations (64,000 with the continuation), the profiles 43,200 (8 parameters × 9 points × 600; v3), the step-halving check one evaluation at T = 2.5 s (twice the steps), the 2-D capacity grid 1,681 × up to 28 model-days per plant (nominal, up to 2 ensemble members, and F1 if used). If the measured timing projects more than 24 h of wall time for §4, the author is told before launch; the budget is never cut silently.
- Raw run files go under `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet/` (ext4), never into the repo. Logs are tailed at most every 10 minutes.

### 8.3 Outputs

- `docs/lab/day_pattern/metanet_precal_facts.json` (§3.6), committed before the first CMA-ES evaluation;
- `docs/lab/day_pattern/metanet_calibration.json` (date lists, exclusions, element/cell tables and the §1.7 step, branch outcomes, frozen parameters and settings (θ1 included), the step-halving check, convergence, identifiability, ensemble, c2\* and the relocation flags, F̂ with its estimability verdict (and F̂_T if used), all gate results with n and intervals, the outcome label), committed in two stages: the freeze before any validation run, then the gate results;
- `docs/lab/day_pattern/metanet_calibration.md` (report, including the Appendix A and B cross-references);
- ledger rows in `vsl_lab/runs/ledger.csv` for every batch, including failed and abandoned ones;
- code: `vsl_lab/plants/metanet.py` (model), `vsl_lab/data/metanet_inputs.py` (both cleaning layers, §3 rules and §3.8 order), `vsl_lab/jobs/metanet_calibrate.py` (§4–§6).

### 8.4 Unit tests (`tests/test_metanet.py`, synthetic inputs only)

1. Mass conservation over the whole network including all origin queues: Σ inflows − Σ outflows − Δ(Σ ρ_i L_i λ_i + Σ w_o) = 0 to numerical tolerance, including a supply-limited ramp whose queue must drain to 0 once its merge cell clears.
2. CFL and τ ≥ 2T assertions at the bound corners (including the 319-m cell of §1.7 (a)/(c)); no negative speed and no density above ρ_max under a worst-case shock input.
3. **Warm-up state (issue 7):** on a homogeneous synthetic stretch (constant λ, no ramps), the §2.6 initial state is stationary to numerical tolerance under constant inputs; on the real cell table it lies on the free-flow branch (ρ_i ≤ ρ_cr,i) and reproduces the propagated flows.
4. Queue spillback: a capacity restriction produces a queue that propagates upstream and dissolves after demand falls.
5. Exit reproduction: on a free-flow replay with measured-style inputs, every model exit volume equals Σ β_e F_e Δt within 1 % over the day.
6. The no-VSL plant is bit-for-bit identical with the speed-limit extension disabled.
7. c1 = c2 = 1 reproduces the frozen plant exactly; F1 with Δ = 0 reproduces the base plant.
8. F1 hysteresis: switch-on above ρ_cr and switch-off only below η ρ_cr.
9. The cell builder reproduces the §1.4 table and merge log from the configuration for the model geometry, the weave sensitivity and the §1.7 (a) and (c) variants, with the bottleneck-cell lists; the split builder reproduces the §3.1 date lists.
10. NRMSE and the corridor-rule wrappers give known answers on toy series; **the c_s toy example of §3.2.4** (single-lane station excluded from m_G; T.H.101-type sentinel included and scaled).
11. **Head location (issue 2; P_1 amended in v3),** with bound-midpoint parameters (θ1 at its bound midpoint 0.90) on the model geometry:
    - an overloaded B2 (E14 demand above capacity, B1 light) gives a corridor-rule episode at P_2 with the Old Shakopee Rd speed ≥ 20 mph above Pioneer Tr, and none at (Old Shakopee Rd, T.H.101);
    - an overloaded B1 (E13 demand above capacity) gives a queue in cell 26 that reaches cell 23, an episode at **P_1 = (S of Highwood Ave, Pioneer Tr)**, and none at P_2 while B2's queue has not reached Pioneer Tr.
12. **Arrivals (issues 4, 14):** on a synthetic free-flow day, the travel-time-shifted A_b equals the model flow at b's downstream station within 1 % per 15-min bin, for b = B1 and B2.
13. **Δ < 0 (issue 5):** with Δ = −0.05 and η = 0.9 on a synthetically overloaded bottleneck, mass is conserved and each cell's memory switches at most 2 times per hour [lab convention].
14. **Event layer (EA-2 and the observation operator; v3):**
    - on toy stations, the amended estimator equals the committed `station_day`/`episodes` output bit-for-bit on every pair except the named P_1;
    - P_1 is evaluated at 3.145 km while any other pair > 3 km is not;
    - Anderson Lakes Pkwy is absent from the event layer on every day;
    - a model series equal to the c_s-scaled real speeds, converted by v / c_s, reproduces the raw real events exactly;
    - the per-bin model mask reproduces the real NaN pattern;
    - the EA-1 sensitivity path still takes speed from the remaining lane when one lane is excluded.
15. **Relocation and c2\* (v3; round 3, issue 1 (iv)):** on the model geometry with bound-midpoint parameters and an overloaded B2, raising c2 until cell 33 binds triggers the relocation flag of §4.7 at the first such c2, and not below it. The flag also fires through the (Old Shakopee Rd, T.H.101) episode branch. The c2\* routine returns the last grid value before the flag. (The logged check at c2\* + 0.01 on the calibration days is a build log, not a unit test.)
16. **B1 censoring (v3; round 3, issue 10):** on toy episode series, a B1 episode followed within 30 min by a B2 onset is censored at that onset on both sides. A model B1 episode starting after t_c scores duration 0. The C4 window of B1 ends at t_c.
18. **P7c (post-check):** on toy P_1/P_2 episode series, P7c equals the longest union interval, including overlapping and back-to-back episodes, and is identical on both sides for identical inputs.
17. **θ1 (v3; round 3, issue 0):** θ1 = 1 reproduces the v2 structure exactly (same cell critical densities). With θ1 < 1 and an overloaded B1, the head forms in cell 26: it is the most downstream cell with ρ_i > ρ_cr,i while cells 27–30 stay on the free-flow branch. Cell 26's ρ_cr equals c1 θ1 ρ_cr,G3 for several (c1, θ1) pairs.
18. **Clipping count (v3; round 3, issue 2):** a forced v_min activation in a cell with ρ_i < ρ_cr,i is counted as clipped; one with ρ_i ≥ ρ_cr,i is not. A T = 2.5 s run of the toy stretch is compared with T = 5 s by the step-halving routine.

### 8.5 Statistics conventions

Real days are the units; there are no simulation seeds to pair. Medians; one convention for comparisons (the median of paired differences, or of paired ratios − 1 for discharge); 95 % percentile bootstrap over days with 10,000 resamples; Wilson intervals for shares; exact binomial intervals for the P6 quartile shares; Poisson-binomial distributions for the stochastic rows (P6s, P10a). Gating uses the pre-registered point estimate, except where a CI limit is itself the criterion (P1c vs N1, P5b(ii)'s L_r,k). CIs are always reported, so that a narrow PASS or FAIL can be read as such.

**Validation days are never used for fitting or to set any plant or variant parameter.** They judge the plant (§5), filter the ensemble (§4.6), and give the model-independent floors L_r,k (F11), which are computed from real data alone before any model run. R4's variants are set on calibration days (issues 5, 18), so no exception to this rule is needed.

### 8.6 Order of work

1. Author items (§0.6), including A4's deterministic-only consequence (A10 is resolved: the extension days are pre-fetched); commit this protocol.
2. Code and unit tests (synthetic only); timing on synthetic inputs.
3. Pre-calibration facts in the §3.8 order:
   - the cleaning branch decisions on calibration days (§3.2.3, §3.3.2, §3.4, §3.2.4; §3.8 steps 2–7), then E1, E4 and the stop rules (steps 8–10);
   - F8 (including the merge-section facts), then F16 and the §1.7 resolution, with the lane-check record (step 11; F16's Q_ref needs F8);
   - the remaining facts (step 12), including the mechanism diagnostic (§1.6, F7) and F10's scale-robustness rule;
   - the real-side minima and floors on validation days (F11; step 12).

   Stop rules (§3.5) and INCONCLUSIVE (§5.2) are checked here. **If the minima fail:** the extension on the pre-fetched days (completed first if unfinished, count logged), its cleaning with the frozen rules, and F11 recomputed on the final validation set (§3.8 step 13). **Then** commit the facts. No model has run at this point.
4. Calibration (§4.4), identifiability (§4.5), the gated step-halving check (§2.5; a failure ends the route here), capacity factors with c2\*, the estimability verdict and, if it applies, F̂_T (§4.7), calibration diagnostics and benchmarks (§4.8). Commit the freeze.
5. Plant gate (§5): deterministic rows, then stochastic rows (N0s, P8s, P6s, P10, under F̂ or F̂_T); ensemble filter (§4.6). Log the outcome.
6. If FAIL and the §6.1 trigger holds: F1, then §5 again. Log both outcomes.
7. Reported checks (§5.5), including the weave sensitivity and the no-leak replay.

---

## 9. Known limits

### 9.1 Limits of what this gate can show

- **Small n, many rows.** With 24 validation Wednesdays (about 15 usable expected, so the extension of §5.2 is the expected route), B2's event checks rest on roughly 8–9 real-active days (an estimate). The deterministic conjunction now has 22 rows (N0, P1a–P1c, P2, P3–P5b and P6–P7a per bottleneck, P5c, P7b, P7c, P8, P9), up from v1's 13 and v2's 20, and a PASS also needs 8 stochastic rows (N0s, P8s, P6s-k, P10a-k, P10b-k). The false-FAIL risk of the deterministic conjunction is higher than v1's and was not computed. For the stochastic rows, only the four sized tests are held to a family-wise 5 % (§5.3). The unsized criteria (P6s (b)–(c), P10b's margin, N0s, P8s) add an uncomputed false-FAIL risk. The one fallback, the INCONCLUSIVE route and its single extension are the only protections, and no criterion may be relaxed. At the minimum n_H,k = 6, the max(6, ⌈0.75 n_H⌉) rule tolerates no missed heavy day.
- **P3 ceiling and the stochastic benchmarks.** If breakdown at B2 depended only on the daily-demand quartile with the v2 shares (15/33/46/85 %), the best deterministic classifier would agree on only about 73 % of days, i.e. a Brier score of about 0.27, while a demand-half climatology with shares 0.24/0.65 (round 2's stylised numbers) has a Brier score of about 0.205 (stylised calculations, not measurements). The 75 % threshold of P3 may be near the attainable ceiling, and P10b's benchmark is not easy to beat at n ≈ 15 (the expected n_val on the Wednesdays, §5.2; more after the extension). The calibration-day benchmarks (§4.8) show this before validation.
- **B1's event definition (v3, EA-2).** B1 is detected at a 3.145 km pair, beyond the committed 3 km limit. A B1 queue that does not reach S of Highwood Ave is not seen on either side, and onsets are those of the queue's arrival at S of Highwood Ave, not of the head's breakdown. v2's EA-1 was dropped because its single-lane reading made B1's status depend on detector scale (§0.5 item 7). *(v2's sentence that the lane bias "pushes towards a false FAIL, not a false PASS" is withdrawn: it did not hold for the stochastic plant. F̂_1 would have been fitted to inflated real B1 activity, which inflates the prize, i.e. the false-GO direction. That check used validation days, §0.5 item 7.)* Speed-dependent detector bias beyond the free-flow c_s is not corrected; F10's scale-robustness rule is the guard.
- **B1 occurrence.** Under EA-2, B1 is active on about 27/28 calibration days (§0.5 item 8), consistent with D3.4. P3-1, P6-1, P6s-1 and P10-1 therefore carry little information, and B1's test rests on P4-1, P5a-1, P5b-1, P5c, P7a-1, P7b, P7c and P8(iii).
- **B1 duration is censored** on days when B2's queue reaches Pioneer Tr (§5.1); on the reviewer's estimate that is most two-bottleneck days. On those days B1's own recovery is not tested; P7c tests the system duration instead.
- **θ1 is a capacity substitute.** It lets the plant meet both heads' discharge, but it does not model why B1 is weaker (lane-end merge, weaving to the X11 exit lane, E13). Control responses that depend on that mechanism are extrapolations.
- **Stochastic plant.** On the expected counts, KM F̂ is likely to be "not estimable" at B2 by the ≥ 8 exact-observation rule (§4.7). The substitute spread F̂_T then assumes a censored normal and independent c1, c2. If that also fails, the deterministic-only consequence (KILL-only) applies.
- **Replay, not control.** Only modes R (and R-NL, reported) are run. The metering response, ramp queues and freeway-to-freeway demand on clipped days are extrapolations or later reconstructions (§7 R1–R2).
- **Served flows at the I-494 merges.** About 38 % of the PM inflow towards the bottlenecks enters there, and on most congested days those counts are capped and carry the queue's timing (§3.3.3). True demand at the bottlenecks is not observable on this corridor, and the real D-check exists only as a lower bound.
- **The drop.** The data cannot separate the real drop from zero at either bottleneck; the plant is only prevented from exaggerating it (P5b, P9(1)). The headroom's dependence on the drop is handled in the gate (§7 R4).
- **Geometry readings.** The `shift` semantics, the merge reading at B2 (a modelling choice; the weave reading is a sensitivity), the 80-m relocation of the I-494 EB lane addition, and the section downstream of E15 (§1.7) are readings or substitutes [VERIFY]. The configuration is current (2026), not 2023 (§3.7).
- **Balance-derived flows** (Old Shakopee Rd entrance; the T.H.62, W 78th St and I-494 EB exits; the balances behind the ramp rule) inherit station-count errors and a rough storage term, especially during onset.
- **Upstream extent** is 8.4 km from the first controlled ramp, short of the 10 km target; accepted as a disclosed deviation (D3.5).
- **No wave validation** (R-b n/a): METANET was chosen partly for its speed dynamics, but 5-min station data cannot validate stop-and-go waves; the SUMO confirmation must.
- **Design informed by validation-day data.** The two-bottleneck structure and several v2 rules were designed after reviewers inspected real data on all 52 Wednesdays (§0.5 item 5), and so were the v3 changes (θ1, EA-2, the gap rule, censoring, the extension; §0.5 item 7). This rewrite's own inspection used calibration days only (§0.5 item 8). No model output was seen.
- **Literature anchors** for bounds and P1 come from the review's reading, not the author's [VERIFY].

### 9.2 Thresholds fixed by lab convention (no literature anchor)

L_min 250 m and the 500 m cell target; the 1 % clip limit (N0, J penalty); the ramp rule's 5 % corroboration, 10 % and 1 % link-inflow gap, and ≥ 8 closable days; the shared-station test's 1 %, factor 2, 50 % (reviewer's values) and ≥ 8 days; 3 %/20 %/5 % (conservation); 2 % (class-B clipping); E2 45 mph / 5 %; E3 45 mph / 15 min and the (Old Shakopee Rd, T.H.101) episode rule; E4 50 % / 8 mph / 10 % occupancy / 1,200 veh/h/lane; the stop-rule fractions; 50–80 mph and 100 bins (lane screen); |c_s − 1| 0.15 and 0.05; J weights 0.25/0.25/0.5 and the 15:00–19:00 / ±30 min windows; the km 0.37–7.20 queue area; the §1.6 diagnostic thresholds, its 4-day control fallback and the C_x bounds; F16's 1.10 (reviewer's value); P1a 0.10; P1b 0.20; P2 80 %; P3 75 %; P4 15 min and 75 % matched (reviewer's value); P5a 5 %; P5b −0.02 (reviewer's value); P7 30 min and 70 %; P8 2 days and 10 %; P9(1) +0.03 (reviewer's value); P9(2) 1.2 (from the gate draft); the max(6, ⌈0.75 n_H⌉) minima (reviewer's value); P10a's 0.05 and its percentile (v3: the 98.75th, from the Bonferroni sizing of §5.3; v2: the 95th); the 200 draws and the +0.5/201 smoothing; the ±60 and ±90 min matching windows; the minimum counts in §5.2 and §5.6; F1's Δ and η bounds; **v3:** θ1's bounds 0.75–1.05; the non-jam v_min clipping rule and the step-halving 5 % with unchanged episode days (reviewer's value); the relocation rule (ρ > ρ_cr for ≥ 3 bins downstream of cell 32) and c2\* < 1.00 as rule (iv); the ≥ 5 exact observations for F̂_T; N0s's 0.05; P8s's use of the P8 limits on expected counts; P5c's form and 5 % (reviewer's value) and its n_H,both ≥ 6 gating condition; P7c's 30 min; P8 (i) and (iii) at max(2, ⌈0.10 · n_val⌉) (reviewer's value); B1 censoring's 30-min window; F10's 25 % scale-robustness share; P10b's 0.02 margin; the family-wise 5 % with Bonferroni over four rows (reviewer's value; the 5 % level carries over v2's per-row 5 %); R4's Δ_k domain, η = 0.9 and ±0.5 pp; unit test 13's switch bound; the capacity grid 0.80–1.20 in steps of 0.01; the F̂ estimability limits 20 %, 25 % and 8; the R1 (e) 5 % detector agreement; the R-NL 45 mph, 12-bin and 6-bin rules; the ensemble size 2 and the 2 % J band.

---

## Appendix A. Review round 1: issue → resolution (kept from v1)

Lens/severity as in `metanet_review1_kept.json`. "Proposed" = the reviewer's change; "better" = a refuter's text; "alt." = a justified alternative. **Section references are to v1.** Where round 2 changed a resolution, Appendix B says so. The rows most affected are 1 (B2 geometry: B2), 7, 12, 31 and 38 (P5b: B8), 11 (capacity factor: B1, B9, B20), 25 (ramp rule: B3, B21), 41 (arrivals: B4, B14), 42 and 56 (P7: B10, B20) and 45 (mechanism diagnostic: B20).

| # | Lens / sev. | Issue (short) | Resolution | Where |
|---|---|---|---|---|
| 0 | model / high | Undetected exits, unpulled aux lanes, wrong element counts make the protocol unrunnable | Adopted (better 1, adapted to the Minnetonka stretch): explicit element table (15 entrances, 15 exits); class-B balances; aux 7097/7077 pulled and counted; closed-link-only conservation | §1.2, §3.3.4, §3.4 |
| 1 | model / high | λ from stations; φ and δ misplaced; B may be a weave | Adopted (better 1): λ from every r_node, stated sequence 2-3-2-3-4-3-2-3-2; φ only at the 4→3 merging drop; δ_m = 0 at lane-adding entrances; B read as an add-drop weave [VERIFY]; no φ_x | §1.3, §2.1 |
| 2 | model / high | Replayed metering loses vehicles or overfills cells | Adopted (better 1): store-and-release replay origin, non-binding Q_o, clipped volume reported; mass-conservation test | §2.3, §8.4 |
| 3 | model / high | T = 10 s violates CFL; τ ≥ 5 s unstable; no clipping | Alt. per design choice 5: T = 5 s, cells ≥ 352 m, v_f ≤ 150 km/h, cap 1.05 v_f (Courant ≤ 0.62), τ ≥ 10 s; clipping with J penalty | §1.4, §2.5 |
| 4 | model / medium | s_i undefined; β against the upstream station overstates exits | Adopted (better 0/1 combined): β on the flow arriving at the diverge; s_e = β·(flow arriving in the cell) | §2.4, §3.3.5 |
| 5 | model / medium | Unmetered/mainstream release undefined; one ramp-capacity scale | Adopted in part: explicit origin equations and v_0 = v_1; Q_o fixed at 2,200 veh/h (not identifiable in replay) instead of fitted; origin misfits reported | §2.2, §2.3 |
| 6 | model / medium | VSL extension changes the no-control plant; form decides H2's T0 | Adopted (better 0/1): no cap in the calibrated plant; Hegyi form primary, MTFC modified FD pre-registered; T0 under both | §2.8, §7 R6 |
| 7 | model / medium | P5 drop cannot fail (IQR contains r = 1) | Replaced by design choice 7: P5b one-sided vs the real CI lower limit on the same days; P5a two-sided | §5.3 |
| 8 | model / low | Free-flow offsets undefined / collinear with v_f | Adopted (better 0): offsets deleted; lane screen + station scaling instead | §3.2.3–3.2.4, §4.1 |
| 9 | statistics / high | Missing exits and aux lanes; day rule yields no days; no minimum days | Adopted with changes: element table, balances, closed links, stop rule (< 18 calibration days) | §1.2, §3.3–3.5 |
| 10 | statistics / high | β denominator wrong exactly at B | Adopted (better 0): downstream anchor, upstream fallback, smoothing, low-flow carry-forward | §3.3.5 |
| 11 | statistics / high | Deterministic capacity makes breakdown too predictable (false-GO risk) | Per design choice 6: per-day capacity factor c_d on the B cells, estimated on calibration days with shared parameters frozen; KM distribution; hidden from all arms in the gate | §4.7, §7 R3 |
| 12 | statistics / high | Drop unfalsifiable; δ name clash; gate δ cells undefined for METANET | Adopted: one-sided P5b; δ → δ_m; gate drop cells on the measured drop | §5.3, §2.1, §7 R4 |
| 13 | statistics / high | Model-side rules and denominators differ from real ones | Adopted (better 1, refined): identical corridor rule on masked model series; explicit denominators and matching; real-side minima → INCONCLUSIVE, model-side shortfall → FAIL | §5.1–5.3 |
| 14 | statistics / medium | NRMSE normaliser undefined; free flow dominates | Adopted (better 1): mean-normalised, per-day pooled NRMSE; J with a 0.5 queue-area term; P1c | §4.2–4.3, §5.3 |
| 15 | statistics / medium | P6 fails good plants; small n; no CIs | Adopted: binomial tolerance at realised n (halves), minimum n, intervals for every statistic | §5.3–5.4, §8.5 |
| 16 | statistics / medium | Cell rule and CFL infeasible | Adopted in substance: deterministic cell rule (n = round(L/500)), T = 5 s, build asserts; step-halving reported | §1.4, §2.5 |
| 17 | statistics / medium | Measured downstream density is leaky and absent in the gate | Adopted (better 1): endogenous ρ_{N+1}; spillback exclusion with a 25 % cap; measured-density sensitivity reported | §2.2, §3.5, §5.5 |
| 18 | statistics / medium | F1 under-specified; no change rule; open implementation choices; §0/§6 contradiction | Adopted: F1 fully specified, §2.6 choices, change rule, route stop with SUMO as an author decision | §6, §2.6, §0.3 |
| 19 | statistics / medium | Split ambiguous; weather and holidays; no 2024 check | Split per design choice 8 (monthly alternation, listed); traffic-based weather proxy; holiday stratum; P-T | §3.1, §3.5, §5.6 |
| 20 | statistics / medium | D-check contradictory; replay-only validation | Adopted: gated model-side P9; real lower-bound form reported; PASS scope stated; mode-C check required later | §5.3, §0.2, §7 R1 |
| 21 | statistics / medium | Spurious bottlenecks elsewhere not gated | Adopted (better 0, only pair B excluded): P8 | §5.3–5.4 |
| 22 | statistics / medium | CMA-ES settings and identifiability rules undefined | Adopted (better 1 + better 0's continuation): frozen settings, normalised spread, profiles, no CV | §4.4–4.5 |
| 23 | statistics / low | α can be chosen after VSL results | Adopted: α_0 fixed, sensitivity set, no change after results, PASS scope | §2.8, §7 R6 |
| 24 | data / high | Day rule and conservation leave zero days; order of operations | Adopted (better 1): element classes M/B, closed-link statistic, detector-fault rule on calibration days, interpolation before validity | §3.2.2, §3.4 |
| 25 | data / high | Pioneer Tr Passage over-counts by a time-varying factor | Per design choice 2: 10 % passage/balance rule for every metered ramp; balance-derived inflow where it triggers; Queue detector as corroboration and sensitivity | §3.3.2 |
| 26 | data / high | Boundary N of I-394 sits in a recurrent queue | Per design choice 1: boundary at Minnetonka Blvd (km −8.413); E2 exclusion; correlation with B days reported; stop rule | §1.1, §3.5, §3.6 |
| 27 | data / high | Aux lanes not fetched; λ vs partial flows | Resolved: 7097/7077 pulled (416 requests) and summed; Cedar Lake Rd/9685 now outside the stretch | §1.2, §3.2.2 |
| 28 | data / high | Five exits without data; counts wrong | Adopted: element table; W 78th St and I-494 EB separate balances (aux pulled); T.H.62 lumped | §1.2, §3.3.4 |
| 29 | data / medium | β denominators: dead lane, aux lane, Pioneer ramp between | Adopted (better 0): reference-station rule with the Anderson Lakes fallback; complete stations only | §3.3.5 |
| 30 | data / high | Freeway merges inside B's queue; real D-check unsupported | Per design choice 3: served counts replayed and disclosed; real D-check lower bound only; later demand protocol required | §3.3.3, §5.4, §7 R2 |
| 31 | data / high | Drop unstable across halves | Adopted: one-sided P5b on the same days; per-set reals reported; §0 rewritten | §0.4, §5.3, §5.5 |
| 32 | data / medium | P6 uninterpretable at ~22 days | Adopted (better 1 structure: halves + gradient) with the binomial tolerance | §5.3–5.4 |
| 33 | data / medium | Field-length rule excludes nothing; offsets cannot absorb station bias | Adopted (better 1): station scaling c_s in the speed term only; raw speeds for events | §3.2.4 |
| 34 | data / low | Cell lengths vs CFL | Resolved with design choice 5 (T = 5 s, frozen cell rule) | §1.4, §2.5 |
| 35 | purpose / high | Aux lanes break flows and conservation | Resolved: aux pulled; closed links; detector-fault rule | §3.2.2, §3.4 |
| 36 | purpose / high | Storage unit; ramp-queue model unvalidated; replay not mass-safe; max_wait ignored | Replay made mass-safe (see 2); storage, max_wait and P0 ramp-demand validity are requirements of the controlled-plant protocol (design choice 2: ramp demand for later use only) | §2.3, §7 R1 |
| 37 | purpose / high | Counterfactual mode undefined (forking path) | Modes defined; mode C and its equivalence check required before any gate run (design choice 3) | §2.7, §7 R1 |
| 38 | purpose / high | P5 passes no drop and 3× drop | P5b one-sided (design choice 7); GO must hold on the low-drop variant; r_cap reported | §5.3, §7 R4, §5.5 |
| 39 | purpose / medium | β overestimated for 10 of 15 exits | Adopted (better 1): downstream form, build assertion | §3.3.5 |
| 40 | purpose / medium | T, cells and speed bounds contradict | Resolved: T = 5 s, cells and bounds frozen | §2.5 |
| 41 | purpose / medium | D-check "must" but not gated; undefined demand | P9 gated (model side); A_B defined; "the real data show this" deleted | §5.3–5.4 |
| 42 | purpose / high | Spillback, propagation, exit blocking not gated | P7 (extent + duration) gated; front speed, blocking exposure, excess veh-h reported; R-b n/a disclosed | §5.3–5.5 |
| 43 | purpose / medium | NRMSE undefined; J ignores the bottleneck | Adopted: §4.2 definitions and the queue-area term | §4.2–4.3 |
| 44 | purpose / medium | No minimum n or INCONCLUSIVE | Adopted (better 1): real-side minima before any model run; INCONCLUSIVE; extension only by addendum | §5.2 |
| 45 | purpose / medium | B could be exit-led, not a merge | Adopted (better 0): pre-calibration diagnostic on calibration days; EXIT branch with C_x | §1.6 |
| 46 | purpose / medium | 2026 config vs 2023 data; no 2024 check | Adopted: configuration-to-data audit; P-T transfer | §3.7, §5.6 |
| 47 | purpose / low | Offsets collinear; field length errors are per lane | Adopted: offsets deleted; lane-level screen | §3.2.3, §4.1 |
| 48 | purpose / low | Node counts wrong | Corrected for the Minnetonka stretch | §1.2 |
| 49 | literature / high | P1 unfalsifiable and unanchored | Adopted: full NRMSE definition; P1a lab convention with literature status; P1c vs nulls N1/N2 | §4.2, §5.3–5.4 |
| 50 | literature / high | Numerics infeasible; no v_min | Adopted: v_min 7.4 km/h fixed [VERIFY], τ ≥ 2T, clips counted | §2.5 |
| 51 | literature / high | F1 not pre-registerable | Adopted with changes: density-hysteresis two-capacity switch on B cells, Δ and η fitted, no per-cell v_f, seeds and budget fixed | §6.1 |
| 52 | literature / medium | Bounds unverifiable; some exclude published fits | Adopted: sourced bounds [VERIFY], v_f 80–150, ρ_max and v_min fixed, bound-active reporting, never widened | §4.1 |
| 53 | literature / medium | One drop estimator, possibly biased to 1 | r_cap reported for both sides (not gated, limitation stated); corridor caveat addendum required | §5.5, §7 R10 |
| 54 | literature / medium | One arbitrary restart; control-relevant parameters non-identifiable | Ensemble of ≤ 2 admissible members; GO needs all members; KILL stays KILL | §4.6, §7 R5 |
| 55 | literature / medium | J dominated by free flow | J = 0.25/0.25/0.5 with the queue-area term | §4.3 |
| 56 | literature / medium | Queue duration and extent not gated | P7 | §5.3–5.4 |
| 57 | literature / low | 0- vs 1-based index ambiguous | Superseded by design choice 8: monthly alternation with explicit dates and code | §3.1 |

---

## Appendix B. Review round 2: issue → resolution

Lens/severity as in `metanet_review2_kept.json` (model = model_numerics, statistics = stats_falsifiability, data = data_purpose). "Adopted" = the reviewer's proposed change; "alt." = a justified alternative, with the reason. Section references are to v2 (the v2 sections keep their numbers in v3). **Rows superseded in round 3 (Appendix C):** 1 (the "deterministic-only" use as a post-hoc author decision → a consequence fixed now, C6, C11); 9 (the P10 levels → Bonferroni and P10b non-inferiority, C6); 11 (E1-B on Anderson Lakes speed → S of Highwood Ave, C3); 19 (≤ 18,408 requests → C9, then the pre-fetch, §0.6 A10); 20 (EA-1 → EA-2, C3, C8).

| # | Lens / sev. | Issue (short) | Resolution | Where |
|---|---|---|---|---|
| 0 | model / high | The 2-lane reading downstream of the Old Shakopee Rd entrance contradicts the measured flows (≈ 2,570 veh/h/lane); the c grid and F1 cannot fix it, and nothing catches it before calibration | Adopted: F16 (arriving flow per lane / larger bottleneck Q_dis per lane, blocking above 1.10) and the ordered rule (a) lane check confirms a lane → geometry correction; (b) check not performed or inconclusive → G4 (v_f tied to G3; ρ_cr, a fitted); (c) truncation at km 7.518. A1 extended; the inspection disclosed. Alt.: (c) is triggered when the lane check **confirms 2 lanes** (the counts are then suspect), because the proposal left (b)'s "otherwise" undefined; the blocking rule applies to G3 cells, while G1/G2 cells (own FD) are reported; E3 gains a uniform (ii) so that truncation needs no re-definition | §1.7, §1.4, §3.5 E3, §3.6 F16, §0.5, §0.6 A1 |
| 1 | model / high | The gate's plant (c ~ F̂) is not the judged one (c = 1); re-centring deferred; the "not reproducible" flag has no consequence | Adopted: (a) re-centring fixed now (c_k / median F̂_k, which ties F̂ to the c = 1 calibration); (b) the stochastic plant gated (P6s with the Poisson-binomial form; P3s in Brier form as P10b); (c) the not-estimable rule (> 20 % not reproducible, > 25 % mass at 1.20, < 8 exact). Alt.: a failure confined to the stochastic rows gives "PASS, deterministic-only" (F̂ unusable; using the deterministic plant needs an author decision), not F1, because F1 cannot affect occurrence (issue 12) | §4.7, §5.3, §0.3, §7 R3 |
| 2 | model / medium | The weave reading forces B's head downstream of the Old Shakopee Rd station | Adopted option (a): the merge reading is primary (λ = 2, δ_m at E14); the weave reading is a reported sensitivity at frozen parameters; unit test 11 for both bottlenecks | §1.3, §1.4, §2.1, §8.4, §0.6 A1 |
| 3 | model / medium | The 10 % rule compares with the ramp volume, while the balance carries station errors 15–30 times larger | Adopted: switch only if a usable Queue detector corroborates the balance (≤ 5 %, both windows) and Passage contradicts it. Alt.: the scale test is 1 % of link inflow (issue 21's value) instead of 3 %, because independent corroboration is now the main guard; a switched ramp replays its Queue detectors, not the balance, so the link stays in §3.4 and the station in S_q. Disclosed | §3.3.2, §0.5 |
| 4 | model / medium | A_B literally excludes the class-B exits (≈ 2,200 veh/h) | Adopted: A_b with every replayed entrance and exit (class-M and class-B, incl. X6+X7, X9, X10), per bottleneck; unit test 12 | §5.4 P9, §8.4 |
| 5 | model / low | R4: Δ < 0 undefined, chattering, set on validation days | Adopted: targets and Δ_k on calibration heavy matched days (F8 CI); Δ_k ∈ [−0.15, 0.15]; unit test 13. Alt.: η = 0.9 for the base plant, not 1.0, because η = 1.0 removes the hysteresis that prevents chattering | §7 R4, §8.4 |
| 6 | model / low | The merge-variant cell text contradicts the rule | Adopted: the table derived from the rule (5 × 457.4, 2 × 580.5, 4 × 547.75 m); B2 cells 31–32; unit test 9 | §1.4, §8.4 |
| 7 | model / low | The warm-up state is not a METANET steady state | Adopted: free-flow-branch solution with propagated flows; unit test 3 on a homogeneous stretch (where that state is exactly stationary) | §2.6, §8.4 |
| 8 | statistics / high | P5b: loose at small n, perverse incentive, model-chosen reference, unpaired | Adopted: paired median(r_model − r_real) ≥ −0.02 with CI; L_r,k frozen from all real heavy validation days (F11, before any model run) as a second floor; the same-days CI reported; the monotonicity argument marked as an inference; R4's low-drop requirement named the operative guard. Alt.: R4's high-drop target uses the calibration-day F8 CI, not L_r, so that no validation day sets a variant (issues 5, 18) | §5.3, §0.4, §3.6 F11, §7 R4 |
| 9 | statistics / high | The stochastic gate plant is never gated; over-confidence unguarded; re-centring a forking path | Adopted: P10a (over-confidence, Poisson-binomial), P10b (Brier vs the demand-half climatology), P6s in Poisson-binomial form; re-centring fixed (R3); F̂ listed in §0.2. Alt.: a P10 failure gives "deterministic-only", not F1 (see 1) | §5.3–5.4, §4.7, §7 R3, §0.2 |
| 10 | statistics / high | Model-dependent denominators drop the plant's worst events | Adopted all five, per bottleneck: P3 overlap-anchored; P4 over all real episodes (unmatched = 90 min, ≥ 75 % matched); P7a over all real heavy days (unmatched = 0); P2 over n_A; P5/P9 minima max(6, ⌈0.75 n_H⌉) | §5.1–5.4 |
| 11 | statistics / medium | Usable days with an event-invalid bottleneck station; per-day masking | Adopted: E1-B (Anderson Lakes speed; Pioneer Tr and Old Shakopee Rd speed and flow); per-bin model mask | §3.5, §5.1, §8.4 |
| 12 | statistics / medium | F1 is a second look and may be triggered by checks it cannot affect | Adopted (a) trigger set, (b) Δ at 0 → "base structure, second optimisation", FAIL by default, (c) "second look" label | §6.1, §0.3 |
| 13 | statistics / medium | Circular cleaning order | Adopted: an explicit, non-iterated order; Q_A excludes stations dropped by §3.2.4. Alt.: the lane screen moves first (step 2, all valid calibration lane-days, 05:00–06:00 only), because the amended event layer needs it; the ramp rule precedes the shared-station test (see 21) | §3.8, §3.2.3, §4.2 |
| 14 | statistics / medium | A_B: class-B exits omitted; measured vs replayed unstated | Adopted (as 4): replayed series everywhere. Unit test 12 compares A_b with the downstream station's model flow, because X13 (or X12) is already subtracted in A_b | §5.4, §8.4 |
| 15 | statistics / medium | P9(1) is an absolute overshoot bound at the real data's own value | Adopted (paired form): median(S1_model − S1_real) ≤ +0.03 with CI; real S1 in F8; stated as an overshoot bound; R4 variants checked (reported) | §5.3–5.4, §3.6 F8, §7 R4 |
| 16 | statistics / medium | P-T has no minima, gates little, exclusions unstated | Adopted: §3 rules incl. E1-B; minima (≥ 16 usable, ≥ 8 active per bottleneck) with INCONCLUSIVE; gated N0, P1a (noted weak), P1c, P3-k, P4-k, P5a-k (when n allows), P10 if F̂ is used | §5.6 |
| 17 | statistics / low | The model's C4 episode may not be the matched one | Adopted: the model C4 uses the episode matched to the real longest one; P5a, P5b, P7a and P9 share it | §5.1 |
| 18 | statistics / low | §8.5 vs R4; moving root-finding target | Adopted via 5: variants set on a frozen calibration day set; nearest-attainable rule; §8.5 restated, so no exception is needed | §8.5, §7 R4 |
| 19 | statistics / low | The extension set is open after INCONCLUSIVE | Adopted: all 2023 Tuesdays and Thursdays (≤ 18,408 requests, author approval of the printed count), code-generated, validation days only; "both outcomes" defined | §5.2 |
| 20 | data / high | An earlier, near-daily bottleneck upstream (B1) is invisible to the event layer | Adopted (D3.4): EA-1 (speed from the lane-screen lanes; an amendment, not a relaxation; 3 km limit unchanged) with the alternative pair reported; B1 = P_1, cells 26–30, E13 merge; B2 = P_2, cells 31–32, E14 merge; real activity per bottleneck; P2 on the first breakdown location; P3/P4/P5/P6/P7a/P6s/P10 per bottleneck; P5a at Pioneer Tr for B1; P7b from the most upstream active head; P9 at the first-active bottleneck; c1, c2 estimated jointly; F1 on B1 ∪ B2; §1.6 extended to X12 (and X11 reported); R3, R4, R6, R13 restated. Item (5) answered by the author (D3.4) | §0.7, §3.2.1, §1.4, §1.6, §4.7, §5, §6.1, §7 |
| 21 | data / high | The ramp rule launders a shared-station error; mode-C demand would differ from the validated replay | Adopted (1) Queue corroboration, (3) link-inflow scale (see 3), (2) shared-station test, (4) detector agreement as R1 (e). Alt.: the shared-station test runs after the ramp rule, because a switch now needs independent corroboration, whereas an uncorrected Passage fault could make a sound station look faulty | §3.3.2, §3.4, §3.8, §7 R1 |
| 22 | data / medium | S_q loses every station in the queue area; P1a cannot fail; P-T weak; calendar types | (1) Alt.: switched ramps replay their Queue detectors (stations stay in S_q), and the class-B-closed stations in Q_A (I-494, Highwood Ave) enter S_q in the congestion windows; (2) adopted: P5a at B1 (Pioneer Tr); (3) adopted: the flow null on the actual S_q (F11); (4) adopted: P-T strengthened (16); (5) adopted: R12 | §3.3.2, §4.2, §5.3, §3.6 F11, §5.6, §7 R12 |
| 23 | data / medium | Replayed merge counts leak the queue's timing; R2 uninformative as written | Adopted: the no-leak replay R-NL (reported, ΔP3/ΔP4/ΔP7); the R2 family fixed now (the same profile-scaled form); a GO must also hold with zero uplift; results split by reconstructed-minus-served volume | §3.3.3, §2.7, §5.5, §7 R2 |

---

## Appendix C. Review round 3: issue → resolution

Lens/severity as in `metanet_review3_kept.json` (model = model_numerics, statistics = stats_falsifiability, data = data_purpose; index 0–11). "Adopted" = the reviewer's proposed change; "alt." = a justified alternative that is not looser, with the reason. Section references are to this file. Appendix B's section references are to v2; the v2 sections keep their numbers in v3.

| # | Lens / sev. | Issue (short) | Resolution | Where |
|---|---|---|---|---|
| 0 | model / high | B1 and B2 share one per-lane capacity, but B2's merge section carries about 11 % more (16/16 same days); P5a cannot hold at both heads, δ_m pushes the wrong way, re-centring discards the gap, F1's shared Δ cannot fix the ratio | Adopted: a fitted head-capacity factor **θ1 ∈ [0.75, 1.05]** on ρ_cr of B1's head cell 26 only. It is disclosed as geometry-motivated (3 → 2 exit-lane end at km 3.751 plus the E13 merge, no φ there), and c1 multiplies θ1 ρ_cr,G3. Also: n = 15–19, λ = 12 (F1: 12–13), θ1 profiled (seeds 7,190,100–108), bound activity reported; the merge-section flow facts (discharge and pre-onset maximum, paired B2/B1 ratio) added to F8; a gated paired row **P5c** (\|median ratio error\| ≤ 5 %; outside the F1 trigger, because a shared Δ cannot change the ratio); the inspection disclosed (§0.5 item 7); A1 (iii). Alt. on θ2: **not added**, because θ2 > 1 would move B2's binding cell downstream (issue 1) and the data place B2 at the G3 level. The φ-type alternative at X11 is not used | §2.1, §4.1, §4.4–4.5, §3.6 F8, §4.8, §5.1, §5.3 P5c, §6.1, §8.1, §8.4 test 17, §0.6 A1 |
| 1 | model / medium | c2 > ≈ 1.05 moves the binding cell downstream of Old Shakopee Rd. C_d, N0/P8 (only at c = 1) and P6s/P10 cannot see this; unclipped re-centring reaches 1.33 | Adopted (i)–(iv): (i) C_d also requires no spurious episode and no relocation (Z_d); (ii) **c2\*** = the largest grid c2 without relocation on any calibration day at any c1, from the existing grid runs. The c2 grid is truncated at c2\*, the KM upper atom is at c2\*, re-centred draws are clipped to [0.80, min(1.20, c2\*)] (c1 to [0.80, 1.20]), clipped shares are reported, and c2\* < 1.00 makes F̂ not estimable (rule (iv)); (iii) **N0s** and **P8s** gate the stochastic plant (expected spurious or relocation days and extra-episode days ≤ the P8 limits); (iv) synthetic unit test 15, plus a build log at c2\* + 0.01 | §4.7, §5.3, §5.5, §7 R3, §8.4 |
| 2 | model / low | Floor (v_min) chattering outside jams is admissible and passes N0; step-halving is not gated | Adopted: a v_min activation in a cell with ρ_i < ρ_cr,i counts as clipped in the 1 % admissibility limit, N0 and N0s; step-halving gated at the frozen optimum on calibration days (\|ΔJ\|/J ≤ 5 % and unchanged P_1/P_2 episode days). A failure is an N0 FAIL (known before validation; route stop); it applies to ensemble candidates and F1 too; unit test 18 | §2.5, §4.6, §4.8, §5.3 N0, §6.1, §8.6 |
| 3 | statistics / high | EA-1 reads B1 through one lane while the model reads a cross-section; B1 status changes ×3 with c_s; J and events use different targets; §9.1's "false FAIL only" is wrong for the stochastic plant | Alt. (stricter than options (a)/(b), keeps (c) as a pre-registered fallback): **EA-2**. B1 activity is measured at (S of Highwood Ave, all lanes; Pioneer Tr), read identically on both sides, with Anderson Lakes Pkwy removed from the event layer; EA-1 becomes a reported sensitivity. Model speeds are converted to detector scale (v / c_s) before every event rule (issue 8 (a)). The proposed agreement fact (1-lane against all-lane, on days with all Anderson Lakes lanes valid) is in F10. A **scale-robustness rule** in F10: if raw and scaled real B1 status disagree on > 25 % of the calibration days flagged by either, option (c) applies (B1 rows report-only, out of the F1 trigger, c1 not estimated). The rule is expected not to trigger (1/27 in §0.5 item 8). §9.1's sentence withdrawn and the use of validation days disclosed; A9 rewritten (bears on D3.4) | §3.2.1, §3.2.4, §3.5 E1-B, §3.6 F10, §5.1, §5.5, §9.1, §0.6 A9, §0.7 |
| 4 | statistics / medium | c_s ambiguous for T.H.101 and for the group reference (single-lane station in m_G) | Adopted: T.H.101 belongs to G3 for scaling under every §1.7 step, gets its own c_s, is scaled in S_v and counts in G3's m_G (not under §1.7 (c)); m_G = the median over stations whose speed lanes equal all their lanes, so the EA-1 station cannot set it; toy example in unit test 10 | §3.2.4, §3.6 F6, §8.4 test 10 |
| 5 | statistics / medium | No row penalises extra model episodes at P_1/P_2 on real-active days | Adopted: **P8(iii)** per bottleneck, i.e. the days with a model P_k episode overlapping no real P_k episode (±60 min) on any usable validation day ≤ max(2, ⌈0.10 · n_val⌉), with unmatched episode-minutes reported. §5.4 amended (P_1, P_2 no longer exempt). The F1 trigger is unchanged, with the reason stated (an extra episode is an occurrence error). Also used in P8s | §5.3 P8, §5.4, §6.1 |
| 6 | statistics / medium | Four sized stochastic tests give about 19 % false FAIL for a correct plant; P10b fails a climatology-skill plant about half the time; the "deterministic-only" use is a post-hoc author choice | Adopted (i) Bonferroni over P6s-1/2 (a) and P10a-1/2: 0.0125 per row, P6s tails **0.003135** per half, P10a at the **98.75th** percentile; unsized criteria declared outside the family and disclosed; (ii) **P10b non-inferiority**, Brier_plant ≤ Brier_clim + 0.02 [lab convention], with the difference's CI reported; (iii) consequence fixed now: the substitute spread F̂_T (see 11), and otherwise "deterministic-only" = **KILL-only** gate on the deterministic plant (a GO there is not a GO). The author may choose "no METANET gate" instead, before the commit (A4). No post-result choice remains | §5.3, §5.4, §0.3, §7 R3, §0.6 A4, §9.1 |
| 7 | statistics / low | Extension multiplies n_val but P8(i) stays absolute; F11 recomputation and the facts-commit order unstated | Adopted: P8(i) ≤ max(2, ⌈0.10 · n_val⌉) per pair; after an extension every F11 quantity (minima, L_r,k, N2_q), the P6 halves and the P8 tolerances are recomputed on the final validation set from real data only, before any model run; the facts commit follows the extension pull and its re-check (§3.8 step 13) | §5.3 P8, §3.6 F11, §5.2, §3.8, §8.6 |
| 8 | data / high | B1 status is set by detector scale (raw 12/10 days, scaled 3/3); model fitted on scaled speeds but judged on raw; §0.7 and R13(e) contradict the gated definition | Adopted (a), the **observation operator** v_model / c_s before every event rule (corridor rule, P7b, P8, the (Old Shakopee Rd, T.H.101) pair), with unit test 14 checking that a model equal to the scaled real speeds reproduces the raw real events. **Decided now:** B1 = the S of Highwood Ave → Pioneer Tr pair (EA-2, see 3), not P_1 via Anderson Lakes. The decision rests on the design argument and on a calibration-day-only inspection (§0.5 item 8), not on F10 agreement after the fact. F10 adds the B1 counts raw, scaled, EA-1 and through-lane, the days with S of Highwood congestion but no episode, and the censored days. §0.7 and R13(e) are made consistent (B1 about 27/28 calibration days); the reviewers' validation-day inspections disclosed in §0.5 item 7 | §3.2.1, §3.2.4, §5.1, §3.6 F10, §0.7, §7 R13, §0.5 |
| 9 | data / high | n_val sits exactly at 16, and an ambiguous gap rule decides INCONCLUSIVE; windows unstated; §5.2's "about 20" overstated; E14 dependency unstated | Adopted with the reading fixed by role: **input detectors** (boundary, class-M ramps and exits, balance and β-reference stations) are invalid on any gap > 15 min in 04:00–23:00, because the model cannot run on a missing input; **scored stations** lose only the gap's bins, with the 90 % rule over 05:00–23:00. The rule's known effect (n_val ≈ 15) is disclosed. **Minimum not lowered.** §5.2's expectation is replaced by the reviewer's counts, and "INCONCLUSIVE on the Wednesdays is the expected outcome" is stated. The extension (all 2023 Tue/Thu, **≤ 18,200 requests** = 87 detectors × 2 × 104 + 104, recounted; v2's 18,408 replaced) is pre-registered to run before calibration if the minima fail, as author item **A10**. The E14 dependency is stated (Old Shakopee Rd possibly flow-unreliable; P5a-2/P5b-2/P5c/P9 flagged, not dropped) | §3.2.2, §5.2, §3.3.2, §3.8, §8.6, §0.6 A10, §0.5 |
| 10 | data / medium | B1's episode usually ends because B2's queue reaches Pioneer Tr; P7a-1 and B1's C4 window then measure B2; B1 "duration" is censored on about 60 % of two-bottleneck days | Adopted: B1 right-censored by B2 (B2 onset inside a B1 episode or within 30 min after it; anchored on real data, same rule both sides). **P7a-1 as a censored comparison** (both sides censored at the real B2 onset) over all heavy B1 days, with the uncensored-only version reported. B1's C4 window ends at the real B2 onset. New system row **P7c** (duration of the union of B1 and B2 queues; in the F1 trigger); P7b already gives the extent from the most upstream head. Censored counts in F10; R13(e) restated | §5.1, §5.3 P7a/P7c, §5.4, §3.6 F8/F10, §6.1, §7 R13, §8.4 test 16 |
| 11 | data / medium | At the expected counts F̂ is very likely "not estimable" (B2 may lose at most 1 of 9 days), so the likely route is an author decision after the outcome | Adopted: expected counts stated in §4.7 (about 23 usable calibration days, B2 about 9, B1 about 23 under EA-2, i.e. every usable day; the v3 draft's "about 22" was corrected at the post-check) with the false-"not estimable" risk named; **limits not loosened**. Option (b) pre-registered now: the **Tobit substitute F̂_T** (used only when KM fails by rule (ii) or (iii), ≥ 5 exact observations per k, re-centred and clipped, the stochastic rows gated on it at the same levels → "PASS, substitute spread"). Otherwise the KILL-only consequence (issue 6) applies. Both are fixed before calibration | §4.7, §0.3, §0.2, §7 R3, §0.6 A4 |

*Post-check consistency edits (12 items + issue 10 R13(e)), 2026-10-05. Second pass by the main session, where the author's pre-fetch approval is first-hand: item 1 (A10) is now resolved in §5.2, §8.6 steps 1 and 3, §7 R11–R12 and here (Appendix C row 9's ≤ 18,200 bound and approval step are superseded by A10); R13(e)/§0.7 relabel P7c as the system queue-duration outcome; §5.1 censoring rule symmetric; unit test 18 for P7c; §1.7 states the input-detector rule. First-pass note: the contradictions listed in `/home/catalin/work/phd/dp_data/metanet_v3_fixlist.json` were resolved in place, except that item 1 (the pre-fetch, A10) is still open in the §5.2 extension rule's "Data pull" bullets (the ≤ 18,200 bound and the printed-count approval), §8.6 steps 1 and 3, §7 R11–R12 and Appendix C row 9; R13 (d)–(e) now name P7c as H1's only B1-duration outcome (stricter than the round-3 proposal).*
