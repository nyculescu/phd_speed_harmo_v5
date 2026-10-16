# Kill-test protocol #2: decision-calibrated eco-approach at actuated signals (Hamburg 13–24 Sep 2023)

Draft v1, 2026-10-16. **Binding when the author answers the shared items S1–S7 (shared rules for the #1/#2 kill tests, draft v1) and §16**, in one line ("accept defaults"; recorded as V84 with this file's sha256); afterwards it changes only by dated addenda written before the run (§14). Sources: `docs/research/development_plan_v0.md` (titled "plan v2") §3 and its main-session check (which wins), `docs/decisions.md` V1–V79, `CLAUDE.md`, the shared rules. Every constant and threshold that can change the verdict is in the Annex, hashed in `constants.json`; gate and QC thresholds appear only there (Annex B). Paper target, if this test gives GO and the confirmatory test passes rule A: IEEE ITSC 2027.

## 1. Question

One automated car approaches one Hamburg signal group in a replay of recorded signal data. At 300 m before the stop line it decides once:
- **commit**: plan to pass in the forecast green;
- **no commit**: drive like the reference driver IDM-1.

A margin m (in seconds) shrinks the forecast green window. Conformal decision theory (CDT) adapts m online, for each signal group × signal program.

**Kill question.** On 18–24 Sep 2023, does online calibration of m save energy compared with every valid static and offline opponent, while the broken-commitment rate stays near its target? Safety comes from the hard layer (§5), not from CDT.

**Out of scope:** the live MQTT recording; the DP planner; all sensitivity variants (latency case (b), zero latency, other τ_q, η and ε values, matched loss), which move to the confirmatory protocol; the confirmatory data (25 Sep onward) and the hold-out intersections (§4), which stay untouched.

## 2. Data handling

- **Archive.** TU Dresden OPARA (Jeschor, Matthes, Springer, Pape & Fröhlich; doi 10.25532/OPARA-466; CC BY 4.0; source data dl-de/by-2-0, LSBG). Zip 33,813,300,354 B, MD5 `11d66d59bcd1fdf2b4a43737231e5f63`, holding one 164.5 GB CSV. Columns (checked on the probe): `phenomenon_time` (10-digit integer, s, epoch UTC), `result_time` and `received_time` (13-digit integers, ms, epoch UTC), `result`, `datastream_id`, `mqtt` (`t` = received live by MQTT; `f` = filled in later by HTTP polling).
- **Stream filter.** The zip stays on /srv/shared, never extracted; size and MD5 are checked first. One pass decompresses it in memory, keeps the filter ID set (§4), and writes gzip CSV parts per local date, joined after the pass (pyarrow is not pinned). It also counts all rows per minute of `phenomenon_time`, for dates before 25 Sep only. Rows dated 25 Sep or later, and hold-out intersections, are never written or summarised. The pass stops once `received_time` passes 27 Sep 00:00 local, if `received_time` never decreased (true in the 100 MB probe); otherwise it reads to the end. Rows dated before 25 Sep but received after 26 Sep 00:00 are kept; only their count is logged.
- **Seal.** 13–17 Sep go to `dev/`, 18–24 Sep to `sealed/`; the SHA-256 of each sealed file is committed the same day. The loader refuses `sealed/` unless git HEAD is the freeze tag (§14), except the §4 step-c script, which prints only per-group gap and `mqtt = f` shares. Build and tests use synthetic data and `dev/` only.
- **Metadata.** A hashed snapshot of the live SensorThings API (`tld.iot.hamburg.de/v1.1`): 2026 metadata for 2023 data, so §4 tests the IDs. Layers `primary_signal`, `signal_program`, `cycle_second`. States (read 2026-10-16): 0 dark, 1 red, 2 amber, 3 green, 4 red-amber, 5/6 flashing, 9 unknown.
- **Time.** Integer ms clocks. Dates and times of day are Europe/Berlin (CEST = UTC+2), from `phenomenon_time`.
- **Ground truth T** (all rows, t and f). Key = (`datastream_id`, `phenomenon_time`). Same key and value: a duplicate, keep one. Same key, other value: a conflict, won by the latest `result_time`, then the latest `received_time`, then `mqtt = t`. A state holds from its `phenomenon_time` until the next row; consecutive equal states merge. A cycle runs from one green onset to the next.
- **Quality check (QC) per cycle.** *Missing truth:* a gap, a state outside 1–4, or a broken order (green → amber → red (→ red-amber) → green; e.g. green → red with no amber). *Duration fail:* a duration outside the Annex B limits. A cycle with neither passes. **Gap:** more than 600 s without a `primary_signal` row of the group, or a minute with no row in the archive. The amber minimum is at least t_r + v_lim/(2 b_comf) = 2.82 s, so the §5 amber rule leaves no dilemma zone (where the car can neither stop comfortably nor clear on amber) up to v_lim.
- **Exclusion.** An approach is excluded for all arms only if [t_0, t_0 + 120 s] contains missing truth; duration fails are scored. Excluded approaches count nowhere and never enter a decision.
- **Split (E4, local dates; all throw-away, and the protocol says so).** Forecaster fitting: 13 Sep (from about 15:18), 14 and 16 Sep. Margin fitting: 15 and 17 Sep. Group selection: the full days 14–17 Sep. Kill evaluation: 18–24 Sep. Guard band: no fitting sample, fitting approach or arrival starts after 23:50 on 14, 15, 16, 17 and 24 Sep; forecaster targets stay inside their block.
- **Disclosure.** Workflow agents read the first ~100 MB of the zip (13 Sep afternoon, in the forecaster block); the file is still at the session scratchpad `wf3/probe_opara/head100MB.bin` (SHA-256 `07a59a463ac6e9af5ea62980b7e05b356dd5dc2e4b3cc48b1126ad4d8b3d5502`), and the author was asked to delete it. This draft printed 11 rows and one metadata page. Agents read only the abstract of Jeschor et al., IEEE IV 2024 (arXiv 2403.18830), a four-week Hamburg study (424 M cycles) by the archive's authors; if its weeks overlap ours [VERIFY], its per-light results are prior knowledge, so they are not read or used before the kill run. All reads served format and latency only; no outcome statistic was computed. Each addendum adds a data-access line (§14).

## 3. Latency model and the no-leak rule

**The leak.** A row about a switch always arrives after the switch; `mqtt = f` rows arrived about 295 s late in the first rows. A replay giving the planner rows at `phenomenon_time` would see the future.

**Visibility** (ms). Feed time, `mqtt = t` rows: vis = max(`received_time`, 1000·(`phenomenon_time` + 1)); the extra 1 s covers truncation to whole seconds. `mqtt = f` rows are never visible in real time (vis = ∞) but count in T. Learning time, all rows: vis_learn = the same maximum. T_L(t) is the truth rebuilt from rows with vis_learn ≤ t.

| Who | Sees at time t |
|---|---|
| Feed arms (O1–O4, O6, C) | the feed view F(t) (rows with vis ≤ t) and their own outcomes known by t |
| Learning arms (O5, O7, O8) | the same, plus T_L(t); all their targets and counterfactual outcomes come from T_L at the moment of use (O5 at 03:00 uses T_L(03:00)) |
| Hard layer, IDM | the physical signal head: the true state at t − t_r |
| R3, R4, P | **non-causal** (hindsight or placebo); labelled so in every table, never called deployable |

An outcome ℓ is known at the first trigger of ℓ = 1, otherwise when the car's front crosses the line; at t_0 if the car did not commit.

**Report-only.** Lag = `received_time` − 1000·(`phenomenon_time` + 1) ms; per layer, L̂ = max(0, median lag) over the `mqtt = t` rows of 14–17 Sep (for the confirmatory case (b)). Per group, the share of `mqtt = t` rows with `received_time` < 1000·`phenomenon_time` (a clock check, no gate).

**No-leak test U1** (synthetic streams; causal arms R1, R2, O1–O8, C). (1) F(t) and T_L(t) equal the views rebuilt from all rows with vis ≤ t and vis_learn ≤ t. (2) Changing any row whose `phenomenon_time`, vis and `received_time` are all > t, or any outcome known after t, leaves every decision and margin up to t bit-identical. (2b) With the outcomes known by t held fixed, the same holds for any row with vis > t (feed arms) or vis_learn > t (learning arms). (3) The planner accepts only F(t). If U1 fails, the run cannot start.

## 4. Signal-group selection (seeded; metadata and 14–17 Sep only)

1. **Candidates (metadata):** Things whose `laneType` contains "KFZ" (motor vehicles), with `primary_signal`, `signal_program` and `cycle_second` streams. An intersection is one integer `trafficLightsID`; a group is one candidate Thing.
2. **Hold-out.** The sorted intersections that have a candidate are permuted with `default_rng(hold-out seed).permutation`; the first 20 % (rounded up) are the confirmatory hold-out. They are excluded from the stream filter, this section and any re-run, and listed in the freeze tag.
3. **Draw.** The other intersections, sorted, are permuted with `default_rng(draw seed).permutation`. In each, take the candidate with the smallest `primary_signal` `@iot.id`. The filter keeps the three layers of these groups at the first 120 intersections.
4. **Scan** in rank order through a–c until 30 groups are eligible or the 120 intersections are used up. D0 counts resolve failures among ranks 1–40. Shares use the group's `primary_signal` rows.
   - a. **Resolve** (14–17 Sep): rows in at least q_res of the 64 hour bins (starting 06:00 … 21:00); all values in {0–6, 9}; program and cycle-second rows exist.
   - b. **Eligible** (14–17 Sep): a green onset in at least q_on of the 5-min windows 06:00–22:00; at least q_QC of cycles pass QC; `mqtt = f` share at most q_f; gap time below q_gap.
   - c. **Evaluation-day QC** (18–24 Sep, no outcomes): gap time of q_gap or more, or a `mqtt = f` share above q_f, over the 7 days drops the group for the week.

## 5. Approaches, car model and energy

- **Arrivals.** Per group and date, `default_rng([arrival seed, primary_signal_id, yyyymmdd])` draws the Annex A gaps: about 360 a day, random so they do not lock to the cycle. The guard band applies. All arms share them. Each approach starts at −300 m at v_lim; no queue, no detector calls.
- **Kinematics.** Positions are of the front bumper; the stop line is x = 0; car length plays no role. Acceleration is constant within each Δt step; stops and line crossings are solved exactly inside the step.
- **Planner (closed form),** one decision at t_0 from F(t_0) only.
  - ĝ0 = t_0 + Δ̂0, ĝ1 = min(t_0 + Δ̂1, t_0 + 120 s) (§6). Commit window [w0, w1] = [ĝ0 + τ_q + m, ĝ1 − m]; τ_q only if Δ̂0 > 0.
  - Feasible arrivals: t_0 + 21.6 s (cruise at v_lim) to t_0 + 52.1 s (brake at d_p to v_min, then cruise). Commit only if [w0, w1] overlaps them, targeting the earliest common time: brake at d_p to cruise speed v_c (closed-form root), cross at v_c, accelerate at a_p. Not claimed energy-optimal; the paper's DP planner replaces it.
  - No commit or no forecast: drive as IDM-1.
- **Hard layer (every arm).** Perceived state = true state at t − t_r; s = distance to the line (m), v = speed (m/s).
  - At perceived amber onset, decide once: STOP if s ≥ v²/(2 b_comf), else CLEAR.
  - Brake on perceived red or red-amber once s ≤ v²/(2 b_comf) + t_r·v, and at once after an amber STOP: a_hard = −min(b_max, v²/(2s)). Apply min(a_nominal, a_hard), clipped to [−b_max, a_p].
  - On perceived green, release and drive as IDM-1. Never enter on red.
- **Loss.** ℓ = 1 if the car committed and, before its front crossed the line, the hard layer braked or v fell below v_stop; otherwise ℓ = 0. ε, the tracker, T_r, A1, K2, O8 and the grid rule count only approaches **with a forecast**. Every table also shows the rate per commitment, the commit share and the no-forecast share.
- **IDM** (Treiber, Hennecke & Helbing 2000 [VERIFY: not re-read]). IDM-1: city-car values of Treiber & Kesting, *Traffic Flow Dynamics* (2013), Table 11.2, corrected by the 2017 errata (read), v0 = v_lim. IDM-2: the same table's gentler freeway-car a and b. A red or red-amber light, or an amber the car stops for, is a standing point leader s0 beyond the line, so the front stops at the line. Deceleration is capped at b_max.
- **Energy (E2)** over [−300, +300] m; a car below v_lim at +300 m is charged the energy of accelerating at a_p to v_lim.
  - **Combustion car (ICE), decides (mL):** VT-Micro (Rakha, Ahn & Trani 2004, TR-D 9(1):49–74 [VERIFY DOI]), composite light-duty vehicle coefficients of Ahn, Rakha, Trani & Van Aerde (2002), J. Transp. Eng. 128(2):182–190 (the first set listed if several).
  - **Electric car (EV), in every table, never decides (Wh at the battery):** VT-CPEM (Fiori, Ahn & Rakha 2016, Applied Energy 168:257–268), the paper's vehicle. If the paper gives no regenerative-braking function or auxiliary power [VERIFY], the fallback is none of either, disclosed.
  - Neither table has been read [VERIFY]; no coefficient is my choice. Both are transcribed (page and table numbers), tested (U8) and hashed in git before any real-data replay.

## 6. Forecaster (frozen lookup table)

Fitted on 13, 14 and 16 Sep, one sample per second, feed visibility. Targets come from T; features from F(t):

| Item | Rule |
|---|---|
| program | newest visible value; holds until the next, across midnight and date files; "unknown" before the group's first |
| state, time in state | from the newest visible `primary_signal` row; time in state = t − `phenomenon_time` of the newest visible state change (1-s bins, cap 120 s) |
| cycle second | newest visible value + seconds since its `phenomenon_time`, no modulo, cap 300 s; MISSING if that row is older than 300 s |
| targets | Δ0 = time to the next green onset (0 if green now); Δ1 = time to the amber onset ending that green; samples whose [t, t + Δ1] touches a failed cycle, a gap or the data end are dropped |
| prediction | numpy medians of Δ0 and Δ1; Δ̂1 > Δ̂0 asserted |
| fallback (n_min samples per level) | (group, program, state, time in state, cycle second) → (group, program, state, time in state) → (group, program, state) → (group, state) → no forecast; MISSING cycle second skips level 1 |
| no forecast | also if the newest visible `primary_signal` row is older than 600 s, or Δ̂0 > 120 s |

## 7. CDT tracker and what its bound covers

**Tracker.** One per cell = group × the program visible in F(t_0) ("unknown" is a cell). Every cell, table, fitting stream, R4 cell and operating-map row uses this program. Outcomes queue as (known time, ℓ). At each decision C first applies the queued outcomes with known time ≤ t_0:

  **m ← max(0, m + η(ℓ − ε))**, for approaches with a forecast only; start m_1 = the O4 margin at group × program level.

The run counts C's pending outcomes at each decision (N_fl). If ever > 0: fix, re-run everything with the same seeds, log both runs.

**Link to Lekeufack, Angelopoulos, Bajcsy, Jordan & Malik (2023), arXiv 2310.05921** (Def. 1, Thm 1, Lemma 1.1 read). With their aggressiveness λ = −m, their update λ ← λ + η(ε − ℓ) is ours. Def. 1 ("eventually safe") holds with K = 1, ε_safe = 0, λ_safe = −m_safe: for m ≥ m_safe = 60 s, w0 lies after the latest feasible arrival, so no commit and ℓ = 0. λ_1 ≥ λ_safe − η holds since m_1 ≤ 60 s. The clip at 0 only lowers λ; it turns their Eq. 7 identity into a safe-direction inequality, and Lemma 1.1 still holds (my own check). Thm 1 then gives, for every data sequence and t ≥ 1, a **pathwise** bound on the realised mean (not a probability; no lower bound):

  mean ℓ over the cell's first t scored decisions with a forecast ≤ ε + [(m_safe − m_1)/η + 1]/t.

**Delay.** Outcomes are known within 120 s and a group's approaches are ≥ 180 s apart, so N_fl = 0 (checked). El Halabi & Brandt (arXiv 2609.07251) is a preprint (v1, 7 Sep 2026), not peer reviewed; its abstract and §4.3 (read; protocol #1 §4) cover ACI with outcomes a fixed number of steps late, not CDT with a decision loss or batched, per-cell feedback. #2 does not need it.

**What the bound covers** (the kill test claims no guarantee: the slack per cell is a reported check, and the guarantee sentence is written only in the confirmatory protocol, shared rules §9): per cell, in this replay with this loss, the realised broken-commitment share over the first T_r decisions with a forecast is ≤ ε + slack, slack = [(m_safe − m_1)/η + 1]/T_r. The confirmatory protocol says "claimed" only if slack ≤ δ (m_1 = 0 needs T_r ≥ 1,240), otherwise "asymptotic only", with A1 as the empirical check. The weekdays open each cell's sequence, so they are covered.

**Not covered:** single approaches; time-of-day subsets; the weekend alone (a restarted bound, ε + 31/n, is my own corollary, a U3 check only); other groups or dates; energy or travel time; red-light safety (the hard layer's job); real traffic: the replay has no queues or detector calls, so gains are upper bounds.

## 8. Arms (all on the same approaches)

**Terms.** *Cell* = group × program (C, O8; P adds the regime); *table cell* = O4's; K2 and the A1 report use *group × regime*; the bootstrap cluster is the *group*. **Grid rule:** the smallest m on the grid M whose loss rate over approaches with a forecast is ≤ ε; static arms apply it to dense fitting streams on 15 and 17 Sep. A table cell is thin below n_cell approaches with a forecast.

| ID | Arm | Rule |
|---|---|---|
| R1 | IDM-1 | reference; never reported alone |
| R2 | IDM-2 | gentle variant |
| R3 | Perfect foresight | true Δ0, Δ1; m = 0; τ_q kept; non-causal; report-only |
| R4 | Hindsight margin | grid rule on the evaluation stream per O4 table cell × regime, with O4's final cell map (after fallback, fixed on 15 + 17 Sep); non-causal; used only for K1 and G |
| O1 | Deterministic GLOSA | m = 0 |
| O2 | Fixed global margin | one m for all groups pooled |
| O3 | Xue-style fixed confidence | per group: [ĝ0 + τ_q + max(0, Q0), ĝ1 − max(0, Q1)]; Q_k = the ⌈(n + 1)(1 − ε/2)⌉-th smallest residual r_k (r0 = g0 − ĝ0, r1 = ĝ1 − g1) over the group's dense-stream decisions with a forecast (15 + 17 Sep). My own reading; I have not read Xue et al. (2026, TR-C 183:105460) |
| O4 | Table, **strongest static** | per group × program × time-of-day bin; thin cells fall back to group × program, then group, then O2 |
| O5 | O4 + nightly refit | at 03:00, expanding window (Annex A) |
| O6 | Quantile regression + split conformal | O3's samples. Unpenalised linear quantile regression at level 1 − ε/2 (`scipy.optimize.linprog`, method `highs`) of r0, r1 on one-hot program, time-of-day bin, state and group, plus time in state (s). Per group, on the calibration half: scores r_k − q̂_k, c_k = the ⌈(n + 1)(1 − ε/2)⌉-th smallest. Window [ĝ0 + τ_q + max(0, q̂0 + c0), ĝ1 − max(0, q̂1 + c1)] (Romano, Patterson & Candès 2019 [VERIFY]) |
| O7 | Online forecaster | lookup refreshed every 15 min from T_L; O4 margins |
| O8 | Rolling window | per cell, grid rule on its last N_W approaches with a forecast (counterfactual outcomes from T_L); O4 margin until N_W exist |
| P | Placebo | seeded permutation of C's margins within each group × program × regime, replayed in a second pass after C's complete run, no feedback; non-causal |
| C | **CDT** | the candidate (§7) |

Confirmatory stage only: the Eteifa-style consensus gate and the DP planner.

**Valid set V(r):** the arms among O1–O7 that pass A1 in regime r (if none, V(r) = {O4}; a #2 rule listed in shared rules §5). C must beat every arm in V(r). B\*(r), the arm in V(r) with the smallest median saving of C over it (ties: lowest arm ID), is only reported, never selected for a test.

## 9. Metrics

- **A1 (validity), every arm, per regime:** broken commitments / approaches with a forecast (ratio of totals); pass if the larger of the one-sided 95 % group-cluster bootstrap and Clopper–Pearson upper bounds is ≤ ε + δ (shared rules). Per group × regime Clopper–Pearson bounds are reported, failing cells listed. *Deviation from plan §3* (per group × regime): such a cell spans 2–5 days, too few to gate with useful power (shared rules §5); the §7 bound still covers C per cell.
- **Energy (co-primary):** ICE fuel per approach (mL), A1 as a filter; EV (Wh) in every table, never deciding.
- **Guards** (per regime; they gate GO). **RC:** zero red crossings in every arm; a red crossing is an entry on red or red-amber more than t_RC after the switch, counted only after a truth amber of at least the QC minimum (other red entries are reported as data-driven); one is a bug (§14). **TT:** C's total travel time over [−300, +300] m, divided by IDM-1's on the same scored approaches, is ≤ TT_max as a point estimate; its group-cluster 95 % CI is reported.
- **Report-only:** hard brakes above b_comf (V36); stops; rate per commitment; commit, no-forecast and excluded shares; excluded share among committed approaches; A1 with excluded committed approaches as ℓ = 1; the old exclusion rule ([t_0 − 120 s, t_0 + 180 s] touching any failed cycle); R2, R3; slack per cell; §3 latency rows; the share of tied groups for each pair of arms (shared rules §5); the operating map (arm × regime × time of day × program).

## 10. Statistics

- **Regimes:** weekday (18–22 Sep) and weekend (23–24 Sep); time of day and program only in the operating map. Inference is conditional on 18–24 Sep 2023; the weekend regime is one weekend.
- **Cluster = group:** the bootstrap resamples groups with all their days in the regime. *Deviation from plan §3* ("intersection-days"): a group's days share tracker state, refits and timing plans, so they are not independent.
- **Paired saving** of arm A over arm B in group g: S_g = 100·(E_B,g − E_A,g)/E_B,g, E = the group's total ICE fuel over the regime's scored approaches. Effect = the median of S_g over groups (per approach, most paired differences are exactly zero).
- **CI:** percentile bootstrap, B group resamples shared by all arms (paired). Two-sided 97.5 % (Bonferroni over the 2 regimes) for "beats" and for half-widths; uncorrected two-sided 95 % for the harm limit (shared rules §1); the same resamples serve A1 and TT. Half-width = (upper − lower)/2 of the 97.5 % CI.
- **G** = median_g S_g(C over O4) / median_g S_g(R4 over O4), the share of the headroom closed. Defined in a regime only if median_g S_g(R4 over O4) ≥ G_floor, else the G leg fails there; waived where O4 fails A1.
- **Power check** (before the freeze; throw-away, disclosed): on 15 + 17 Sep, with the evaluation arrival rule, the 97.5 % half-width of median_g S_g(O2 over O4) over the eligible groups (scaled by √(n_used / n_eligible) if fewer have data), recorded in a dated addendum, together with the validity power per regime for a rate-ε arm (shared rules §5).

## 11. Decision rules (18–24 Sep, ICE; the first match wins)

1. **D0 STOP (data or design problem):** size or MD5 mismatch; fewer than n_res of ranks 1–40 resolve; fewer eligible groups than the minimum; a start-gate unit test fails; or the power-check half-width exceeds HW_max. The author re-plans; a STOP says nothing about the idea.
2. **K1 KILL (no headroom):** in both regimes, O4 passes A1 and median_g S_g(R4 over O4) < θ_K1. Where O4 fails A1, headroom counts as present. R3 vs R1 is report-only: simulation already shows 28–37 % (Shafik, Eteifa & Rakha 2022).
3. **K2 KILL (no drift):** fewer than θ_K2 of group × regime cells show drift: O4's loss-rate interval (1-h block bootstrap within the cell, two-sided 95 %) lies wholly above ε + δ, or wholly below ε/2 while O4's median margin there is > 0. No Bonferroni: the per-cell false-flag rate is ≤ 2.5 % per side, below θ_K2.
4. **K3 KILL (no online gain):** no regime r has all three point legs: the G leg (G ≥ G_min, or waived); smallest median_g S_g(C over A), A in V(r), ≥ θ_S; median_g S_g(C over P) ≥ θ_S.
5. **GO:** C passes A1 and RC in every regime; in no regime does a 95 % CI of S_g(C over A), A in V(r), lie wholly below −θ_harm; and in one regime r, C passes TT, all K3 legs hold, and every 97.5 % CI of S_g(C over A), A in V(r) or A = P, has its lower end > 0. N1 is judged in that regime.
6. **INCONCLUSIVE:** in some regime, C passes A1, RC and TT; no 95 % CI against an arm in V(r) or P lies wholly below −θ_harm; and every comparison failing its GO condition (median ≥ θ_S and lower end > 0) has a half-width above HW_max. Action: a decision entry; the author re-plans. No extension (plan §7).
7. **KILL** in all other cases.

**N1 (narrows a GO):** if median_g S_g(C over O8) < θ_N1 in the GO regime, the claim becomes "same energy as a rolling window, plus a finite-sample guarantee".

**Protocol-specific rules** (listed in shared rules §5 and approved with §16): point estimates for K1, the K3 legs, G, N1 and TT (GO's "beats" and harm legs and A1 use the shared CI rules); K1–K3 KILL on their own rules, and rule 6's half-width test takes the place of the shared decisive-firing test; K2 counts a share of group × regime cells; V(r) = {O4} when no opponent passes A1. Rules 6 and 7 split the runs that are neither KILL by rules 2–4 nor GO into undecided (INCONCLUSIVE) and decided (KILL), as in the shared outcome classes (STOP > KILL > INCONCLUSIVE > GO). Group clusters (§10), mL and Wh, and "INCONCLUSIVE leads to a re-plan" (no re-run block is named) follow the shared rules.

## 12. Pseudo-code (where it differs from the text, the text wins)

```
# Build, synthetic only: U1-U24 pass; energy tables hashed in git
# Stage 1 (shared rules §6), dev/ only (13-17 Sep) plus the §4 step-c counts:
#   T, F, T_L per group; selection log (§4);
#   forecaster (13, 14, 16 Sep); dense streams of 15 + 17 Sep, each approach
#   replayed once per distinct target time (cache) -> loss and fuel for all m in M;
#   fit O2, O3, O4, O6; power check -> dated addendum
# Freeze tag (§14); stage 2: only now may the loader open sealed/
assert head == freeze_tag and tree_clean and hashes_ok
for g in groups:                                   # one process; feed case (a) only
  T, F, TL = truth(g), feed(g), learn_view(g)
  for t0 in arrivals(g):                           # shared by all arms
    if excluded(T, t0): log(g, t0, "excluded"); continue
    fc = forecaster(F.view(t0))                    # None -> IDM-1
    c = (g, program(F.view(t0)))                   # cell
    for arm in (R1, R2, R3, O1..O8, C):            # O5 refits at 03:00 from TL(03:00)
      arm.apply(queue.known_by(arm, t0))           # outcomes with known time <= t0
      if arm is C: assert queue.pending(C, c) == 0
      m = arm.margin(c, t0)
      traj = replay_cached(commit_or_stop(fc, m), T, hard_layer)
      queue.push(arm, c, known_time(traj), loss(traj))
      log(g, t0, arm, ice(traj), ev(traj), metrics(traj))
# Pass 2: R4 from cached replays (grid rule per O4 table cell x regime);
#   P = C's margins permuted per group x program x regime, replayed, no feedback
assert red_crossings == 0
ledger.append(decide_section_11())
```

Compute (my arithmetic): O5's evaluation-day dense streams alone are 7 × 2,880 × 30 × 37 ≈ 22 M replays; caching by distinct target time keeps the run near 1 h on one core (estimate).

## 13. Unit tests (synthetic, non-project seeds; together they form the start gate)

Each test has a synthetic fixture and an exact expected value.

| ID | Checks |
|---|---|
| U1 | no-leak tests 1, 2, 2b and 3 (§3) |
| U2 | vis, vis_learn, integer ms |
| U3 | the Thm 1 bound with the clip on adversarial loss sequences; N_fl = 0; the weekend restart corollary (check only) |
| U4 | no commit for m ≥ m_safe, over 10⁶ random forecasts |
| U5 | closed-form arrival time vs the stepped replay, error < 0.01 s |
| U6 | strict: with a 3-s amber, zero line crossings after the replay red onset, over speeds in 0.5 m/s steps up to v_lim and 10 onset phases within a step; a 2-s amber fails QC |
| U7 | the IDM front stops within 0.5 m before the line |
| U8 | energy models vs published or hand-computed cases |
| U9 | Berlin local dates; the 23:50 guard band |
| U10 | stream filter on a synthetic zip: the reference rows; no uncompressed file; nothing from 25 Sep on written or summarised; the dev/sealed split; per-minute counts |
| U11 | bootstrap and Clopper–Pearson vs SciPy |
| U12 | identical arrivals in all arms, unchanged when the group order is permuted or groups are added |
| U13 | the placebo keeps C's margins per cell × regime and runs after C |
| U14 | every branch of §11 is reachable |
| U15 | A1, T_r, K2, O8 and grid-rule denominators count only approaches with a forecast |
| U16 | ground truth: duplicates, conflicts, tie order, state merge, cycle boundary |
| U17 | cycle-second and program carry-over with sparse rows, across a midnight file boundary |
| U18 | every level of the forecaster fallback |
| U19 | hard-layer state machine: amber decision, braking, release to IDM-1 |
| U20 | both ℓ branches, and a crawl-through (slowed to 0.6 m/s, released on green: ℓ = 1) |
| U21 | no queued outcome is applied before its known time |
| U22 | exclusion: missing truth excluded, duration fails scored |
| U23 | selection: a perfect feed starting at 15:18 on day 1 resolves and is eligible; rank and hold-out rules |
| U24 | the loader refuses `sealed/` when HEAD is not the freeze tag |

## 14. Freeze, re-runs, outputs and operations

- **Freeze tag** (shared rules §6). Before `sealed/` is opened, one git tag fixes this protocol and its addenda, `constants.json` (every Annex value), the code, and the SHA-256 of the metadata snapshot, every data file and the selection log. The runner checks HEAD = tag, a clean tree and the hashes. The kill test runs once.
- **Addenda** are dated and written before the run. Annex values do not change after the first real-data replay without an addendum naming the outputs seen. Each addendum lists the data files opened since the previous one.
- **Re-runs** only on a check fixed before the run (start-gate tests, §12 asserts, red crossings); the same checklist runs after every run, whatever the verdict. A bug fix re-runs everything with the same seeds; the post-fix verdict counts; both are logged (CLAUDE.md). Shared rules §6 also apply (an operations failure is re-run once; a bug counts only if a unit test derived from this text fails on the old code and is committed first).
- **Files.** Runs under `/home/catalin/work/phd/v5b1_runs/p2_kill/`; filtered data on /srv/shared. Committed (< 5 MB): verdict, operating map, slack per cell, selection, QC and exclusion logs, constants, hashes, seeds, git commit. Every run goes into the ledger, failed ones included.
- **Operations.** Check resources before each step. Download and filter run in their own `systemd-run --user` units with `nice -n 19`. The kill test is one process (S5 default: no CPU guard). At night CPU stays below 70 %. Never touch the fans.

## 15. Time (plan §3 estimates; download and filter rates measured)

| Step | (a) Author | (b) Claude build + verify | (c) Compute / download |
|---|---|---|---|
| Decisions (shared items, §16) | 0.5–1 h | – | – |
| Protocol review (with #1) | 1–2 h | 0.5–1 h | – |
| Download, MD5, metadata, filter | – | 1–2 h | 22–92 min; 2 min; 14–17 min |
| Timelines, QC, latency, forecaster, planner, IDM, energy | – | 6–8 h | minutes |
| CDT, arms, placebo, statistics, tests | – | 4–5 h | minutes |
| Kill run + report | 0.25–0.5 h | 1–2 h | ≤ ~1 h, one core, with caching (my estimate) |
| **Total** | **1.75–3.5 h** | **12.5–18 h** | **≈ 0.7–3 h, unattended** |

Reading Xue, Li–Wang–Hu and Lu (author, 4–9 h) is needed only for the confirmatory protocol.

## 16. Pending author items (one line answers all: "accept defaults")

Approving these also approves the shared items S1–S7 (V80–V82) and the protocol-specific rules named in §11, which shared rules §5 lists; this protocol is recorded as V84 with its sha256. From the shared seed block, this test uses 7,421,000–7,421,099 (Annex A). Outside "accept defaults" (the shared rules' list): starting the live recording and deleting the probe files.

- **E1.** Download the zip now to `/srv/shared/v5b1_data/opara/`; filter only 13–24 Sep, into `dev/` and `sealed/`. The live recording is not part of this item.
- **E2.** The combustion car (VT-Micro, mL) decides; the electric car (VT-CPEM, Wh) is in every table.
- **E3.** ε = 0.05 per approach with a forecast, with the loss of §5; δ = ε/2. ε = 0.02 moves to the confirmatory protocol.
- **E4 + E5 (merged).** The date split of §2 (25 Sep onward and the hold-out untouched) and the gates of Annex B.

## Annex A: constants and defaults (fixed before data)

| Symbol | Meaning | Value | Source |
|---|---|---|---|
| v_lim | approach speed and limit | 13.9 m/s (50 km/h) | plan §3 |
| segment | energy and travel-time segment | −300 m to +300 m | start: plan; end: default |
| Δt | replay step | 0.1 s | default |
| t_r | reaction to the physical signal | 0.5 s | plan (QC formula) |
| b_comf | comfortable deceleration; above = hard brake | 3.0 m/s² | V36 |
| b_max | deceleration cap (hard layer and IDM) | 8 m/s² | as #1 |
| a_p, d_p | planned acceleration, deceleration | 1.0, 1.0 m/s² | default |
| v_min | lowest planned cruise speed | 5 m/s | default |
| τ_q | queue allowance after a future green onset | 4 s | plan |
| ĝ1 cap | forecast horizon | 120 s | plan |
| ε, δ | broken-commitment target per approach with a forecast; tolerance | 0.05; 0.025 | E3 |
| η | CDT step | 2 s | default |
| m_1 | CDT start | O4 margin at its group × program level | default |
| m_safe | margin that forbids commits | 60 s | §7 |
| M | margin grid | 0–30 s in 1 s steps; 35–60 s in 5 s steps | default |
| arrivals | per group and date, evaluation | first at 00:00 + U[0, 240) s; then gaps of 180 s + U[0, 120) s | default |
| guard band | no sample, fitting approach or arrival after | 23:50 local on 14, 15, 16, 17 and 24 Sep | default |
| fitting stream | per group, 15 + 17 Sep | 1 per 30 s, seeded offset | default |
| time-of-day bins | local | 00–06, 06–10, 10–15, 15–19, 19–24 | default |
| n_min | forecaster samples per key, at each fallback level | 20 | default |
| n_cell | a table cell is thin below | 30 approaches with a forecast | default |
| N_W | O8 rolling window | 200 approaches with a forecast | default |
| O5 data | nightly refit at 03:00 local | dense streams of 15, 17 Sep and of every evaluation day so far, outcomes known in T_L(03:00) | default |
| O6 split | fit / calibration halves | seeded 50/50 split of the 15-min blocks of 15 + 17 Sep; level 1 − ε/2 at each end | default |
| O7 refresh | online lookup update | every 15 min, all targets known in T_L (expanding) | default |
| IDM-1 | v0, T, s0, exponent, a, b | 13.9 m/s, 1.0 s, 2 m, 4, 1.5 m/s², 2.0 m/s² | Treiber & Kesting 2013, errata 2017 (city cars) |
| IDM-2 | a, b (rest as IDM-1) | 1.0, 1.5 m/s² | same table, freeway cars |
| stop leader | standing point leader for IDM | s0 = 2 m beyond the line | default |
| gap / stale | no `primary_signal` row for | > 600 s | default |
| cycle second | usable if its row is younger than; cap | 300 s; 300 s | default |
| hold-out | confirmatory intersections | 20 %, rounded up | plan §3 |
| latency | kill test | feed case (a) only; other cases confirmatory | plan |
| bootstrap | group resamples (paired); intervals | B = 10,000; two-sided 97.5 % (beats, half-widths); two-sided 95 % (harm); A1 one-sided 95 % (larger of bootstrap and Clopper–Pearson); TT CI 95 % (reported) | default; shared rules |
| K2 interval | per group × regime | 1-h block bootstrap, two-sided 95 % | default |
| seeds | block 7,421,000–7,421,999 (shared rules); this test uses 7,421,000–099 | +000 hold-out; +001 group draw; +002 fitting-stream offsets; +003 O6 split; +004 arrivals; +005 placebo; +006 all bootstraps; +007–099 unused. Per-group streams: `default_rng([seed, primary_signal_id])`, plus yyyymmdd for daily streams. Bug re-runs reuse the same seeds. Unit tests: 0–9,999 | S3 (shared rules) |
| energy | ICE; EV | VT-Micro composite light-duty vehicle (first listed if several); VT-CPEM paper vehicle (fallback: no regeneration, zero auxiliary power) | E2 [VERIFY tables] |

## Annex B: gates and QC thresholds (hashed with the constants)

| Symbol | Rule | Value | Source |
|---|---|---|---|
| QC | amber; red-amber; green; cycle | 3–6 s; ≤ 2 s; ≥ 3 s; ≤ 300 s | §2 |
| q_res | resolve: share of the 64 hour bins with rows, at least | 90 % | E5 |
| n_res | resolve: of ranks 1–40, at least | 36 | E5 |
| q_on | 5-min windows with a green onset, at least | 90 % | default |
| q_QC | cycles passing QC, at least | 80 % | default |
| q_f | `mqtt = f` share, at most | 10 % | default |
| q_gap | gap time, below | 10 % | E5 |
| groups | target; minimum (D0); filtered intersections | 30; 20; 120 | E5 |
| HW_max | power-check and INCONCLUSIVE half-width | 1 % | default |
| θ_K1 | K1 headroom | 1 % | E5 |
| θ_K2 | K2 drift share; band | 10 %; [ε/2, ε + δ] | E5; shared rules §5 |
| G_min; G_floor | K3 G leg; G is defined if R4 saves at least | 0.10; 1 % | E5; plan §5 |
| θ_S | minimum saving vs V(r) and P | 1 % | E5 |
| θ_harm | harm limit | 5 % | plan §5 |
| θ_N1 | N1 | 1 % | E5 |
| TT_max | travel-time ratio vs IDM-1 | 1.02 | V37 |
| t_RC | red-crossing tolerance | 1 s | plan |
| v_stop | stop speed for ℓ = 1 | 0.5 m/s | default |
