# Kill-test protocol #1: leader-adaptive RSS safety filter (NGSIM throw-away)

Draft v1, 2026-10-16. Sources: `docs/research/development_plan_v0.md` (titled "plan v2") §2 and its main-session check (the check wins), `docs/decisions.md` V1–V79, `CLAUDE.md`. **Parent rules:** the shared rules for the #1/#2 kill tests (draft v1), binding once accepted; where they differ, the stricter rule applies, except for the #1 rules listed in shared rules §5.
- **Status:** binding once the author accepts it (V83, with this file's sha256). "Before data" means before any NGSIM row is parsed beyond the MD5 and the row counts. Until then, changes are dated addenda (each with its own V entry and hash) that never relax a bound; after it, nothing changes. D- and Q-step counts and causal speeds never change a constant; they act only through the demotion and underpowered rules of §10.
- **Plan v2 fixes F1–F6** are applied in §4 (tracker), §7, §2 and §3.
- **Disclosure** (format only; no outcome statistic was computed on real data; the MD5s go into the data registry):
  1. NGSIM: agents read the metadata and a 100 MB export prefix, still on disk: `wf3/probe_ngsim/head.csv`, 782,767 rows, three locations, includes v_Vel, v_Acc and Space_Headway; MD5 0841a5b63849a9ed852560a571d97445.
  2. TGSIM, the confirmatory source: 20,000 rows each of I-90/I-94 Stationary, I-395 and I-294 L1, with speed_kf and acceleration_kf: `wf3/fc/tg_9uas-hf8b.csv`, `tg_97n2-kuqi.csv`, `tg_7zjf-a4zf.csv`; MD5 185b0055eb7d8227a4cb663d4e16195f, 1cf7a572eeae25e1177520e5df4d222e, a9f2f0c1249446350e99aafe2bd07212. No script computed statistics on them; what agents printed was not logged.
  3. On 2026-10-16 a reviewer printed the NGSIM header and 12 raw lines, and the TGSIM headers and line counts. The reviser printed the NGSIM header, one raw row and the TGSIM headers, and hashed the four files.
  4. The protocol verifier ran format-only scripts on the NGSIM prefix (location counts, lane and class sets, period time ranges, ID reuse counts, Space_Headway zero share) on 2026-10-16 and printed the TGSIM header line only.
  - **Pre-registered:** the confirmatory protocol excludes every TGSIM (id, run_index) present in these probe files (id alone for I-395, which has no run_index), read from those columns only. Deleting the probes stays on the author's to-do list.

## 1. Problem

- One automated car (the ego) follows a recorded leader in replay. The leader never reacts.
- A nominal adaptive cruise control (ACC) proposes a_nom. The filter applies min(a_nom, a_safe), so the gap g (m) stays ≥ d_safe(b̂) + s0. Only b̂, the leader's assumed maximum braking (m/s²), adapts, per traffic regime.
- **Claim type:** a calibrated planning margin. Safety comes from a separate emergency layer (8 m/s²). A miss is not a collision; α = 0.02 per 8-s window is about 9 misses per hour.
- **The kill test has no ego and no filter.** It asks: is per-regime online calibration valid across two sites, and does it shorten the required gap compared with strong static calibrations?

## 2. Safe gap d_safe(v_e, v_L, b̂)

- **Ego proper response:** accelerate at up to a_acc for ρ, then brake at b_min to a stop. The leader brakes at b̂ to a stop.
- **Definition,** for any v_e, v_L ≥ 0 (inputs clipped at 0): d_safe = max of [x_e(t) − x_L(t)] over t ∈ [0, t_E]. x: displacement (m); v: speed (m/s); t_E = ρ + (v_e + ρ·a_acc)/b_min is the ego's stop time (t_E ≤ H when v_e ≤ v_cap).
- **b̂ ≥ b_min:** Lemma 2 of Responsibility-Sensitive Safety (RSS; Shalev-Shwartz, Shammah & Shashua, arXiv 1708.06374v6). It is exact here, because the relative speed never falls before the leader stops: [v_e·ρ + ½·a_acc·ρ² + (v_e + ρ·a_acc)²/(2·b_min) − v_L²/(2·b̂)]₊.
- **b̂ < b_min** (active, since b_floor < b_min): the exact maximum of the piecewise-quadratic closing distance, evaluated at 0, ρ, min(v_L/b̂, t_E), t_E and the times of equal speed. Lemma 2 understates this case: (30, 20, 2) gives 41.50 m, but Lemma 2 gives 35.375 m.
- **G2 (lemma, tested by U3):** in a covered window (s_k ≤ q_k), for the smoothed leader at the 0.1-s grid: if g(t) ≥ d_safe(v_e, v_L, q_k) + s0 and the ego follows the proper response, then g ≥ s0 − x_tol on [t, t + H]. Exceptions: h < h_min, and motion between grid times.
  - The score uses the centred leader speed (≈ 0.5 s look-ahead), so the miss rate and G2 refer to an ego with that speed input. The confirmatory protocol must use the same speed estimator in the ego and in the score. It also sets the closed-loop rule (q_k held for the whole window, or e_k = 1{s_k > min b̂ over the window}).

## 3. Windows, score, regimes

- **Window:** frames are Δt = 0.1 s; W = H = ρ + (v_cap + ρ·a_acc)/b_min = 8.0 s.
- **Leaders:** every track piece (§5) of every v_Class. Windows with a leader lane change are scored.
- **Starts, per piece:** t_k = start + 4.5 s + j·W, while t_k + 2W + 0.5 s ≤ piece end. History L_k = min(10 s, t_k − start − 1.5 s) ≥ 3 s, so every causal value exists.
- **Excluded** from every arm, count, batch, block and gate:
  - windows whose leader is in a ramp lane (§5) at any frame of [t_k − L_k, t_k + 2W + 0.5 s];
  - windows whose t_k lies outside the nominal interval of their own data period p (§5). These are counted.
  - A window belongs to the nominal period that contains t_k.
- **Eligibility uses future data** (the leader stays 2W + 0.5 s in the section and off the ramp lanes). This selects windows. It does not leak into q_k, because eligibility is known at maturity, and all arms see the same windows.
- **Required braking.** v0 is the centred leader speed at t; X = y_SG(t+h) − y_SG(t) is the smoothed displacement (§5); v0⁺ = max(v0, 0); X′ = X + x_tol.
  - If X′ ≥ v0⁺·h/2: b_req = 2(v0⁺·h − X′)/h². Else if X′ > 0: b_req = v0⁺²/(2X′). Else: b_req = b_phys if v0⁺ > 0, otherwise 0.
  - So b̂ ≥ b_req means the leader moved at least as far as a leader braking at b̂, less x_tol.
- **Score:** s_k = min(b_phys, max(0, max of b_req over the 80 frames t ∈ [t_k, t_k + W) and h ∈ [h_min, H] in 0.1-s steps)). QC-flagged windows get s_k = b_phys: capped, never dropped (F6).
- **Miss:** e_k = 1{s_k > q_k}, where q_k is the b̂ in force at t_k (§4). It depends on the leader only, so replay coverage is exact for the eligible windows.
- **Regime** (causal, from v_c over [t_k − L_k, t_k]): R1: minimum < 2 m/s; else R2: mean < 10 m/s; else R3. R3 is report-only: the sections (I-80 ~503 m, US-101 ~640 m) cannot hold 26 s of leaders above ~19 or ~25 m/s.
- **Gated cells:** {R1, R2} × evaluation site (J = 4 before D and Q).

## 4. Online calibration

- **Tracker per regime r:** q_r ← max(b_floor, q_r + (η/c)·Σ_batch(e_k − α)). It clips from below only (F1).
  - Start: q_1,r = O2's regime-r threshold on the fitting site (for M and P).
  - It is never reset; its state carries across period gaps.
- **M (ours, gated):** per regime, one fleet-shared tracker over all regime-r windows of the evaluation site, in time order.
  - Updates happen at times n·Δ_u (n an integer; times in integer ms of Global_Time).
  - Window k matures at t_k + 2W + 0.5 s (the smoothing lag). It is applied at the first update at or after maturity. q_k is the value after all updates at times ≤ t_k.
  - c_r = the median batch size of non-empty updates on the fitting site (a count). O6 and O7 use the same grid.
- **No coverage bound is claimed** (shared rules §9). Validity is judged by the kill-test rules (§8, §10); A1 is reported for every arm.
  - Related work, not a basis: El Halabi & Brandt (2026), "Adaptive Conformal Inference Under Delayed Feedback: Coverage Guarantees and a Delay-to-Memory Diagnostic", arXiv 2609.07251v1, §4.3 Eq. (11), checked against the v1 PDF on 2026-10-16.
  - It bounds adaptive conformal inference (ACI) in α-space with a fixed delay τ, one outcome per step and no clip. Each iterate is updated from the one τ steps earlier (τ interleaved chains).
  - Our trackers are one score-space chain with a lower clip and batched, variable-delay feedback, so Eq. (11) does not transfer. Our own bound (plan F2) is a code check only (U4).
  - Guarantee wording, the one-car chain and the "claimed" rule move to the confirmatory protocol.

## 5. NGSIM data

- **Source:** US DOT FHWA, "Next Generation Simulation (NGSIM) Vehicle Trajectories and Supporting Data", data.transportation.gov `8ect-6jqj`, doi 10.21949/1504477, CC BY-SA 3.0 (derived data share-alike).
  - Legacy export: `/api/views/8ect-6jqj/rows.csv`. Its headers announce a sunset on 22 Dec 2026.
  - Fallback: `/resource/` with `$limit` and `$order=:id`.
  - [VERIFY the URL, the filter and the id at download.]
- **Periods (PDT = UTC − 7 h):**
  - I-80, 13 Apr 2005: P1 16:00–16:15, P2 17:00–17:15, P3 17:15–17:30.
  - US-101, 15 Jun 2005: P1 07:50–08:05, P2 08:05–08:20, P3 08:20–08:35.
- **Integrity:**
  - Store in `/home/catalin/work/phd/v5b1_data/ngsim`, in its own `systemd-run --user` unit with `nice -n 19`.
  - Record the file's MD5 and re-check it before each run.
  - Expected raw rows per Location, before de-duplication: i-80 4,566,387; us-101 4,802,933 [VERIFY same query].
  - A mismatch means STOP. The review may only re-download or correct the query. It never filters rows to match.
- **Columns used:** Vehicle_ID, Frame_ID, Total_Frames, Global_Time, Local_Y, v_Class, Lane_ID, Location. Never v_Vel or v_Acc (their smoothing is unknown).
- **Cleaning, in order:**
  0. Keep Location ∈ {i-80, us-101}; the export interleaves four locations.
  1. Drop and count exact duplicates (all 25 raw columns equal, compared as strings).
  2. Convert Local_Y from feet to metres (× 0.3048). Global_Time stays in ms UTC.
  3. **Period id p** = Global_Time − 100 ms·Frame_ID (the frame-0 time, constant within a recording period). Expect three values per site after rounding to the nearest second [VERIFY on the full file; otherwise a format STOP]. Periods overlap in time, and Vehicle_IDs repeat across them ("REPEATS ARE NOT ASSOCIATED", metadata).
  4. Sort by (Location, p, Vehicle_ID, Global_Time); never trust the file order. The same key with different values is a conflict: flag it.
  5. Global_Time must be a multiple of 100 ms and lie in [nominal start − 2 min, nominal end + 3 min] of p. This tolerance rests on a 100 MB prefix. A violation on the full file is a format STOP, never a tolerance change.
  6. Track key (Location, p, Vehicle_ID, piece): split at gaps > 0.15 s or Frame_ID jumps. Total_Frames mismatches and splits are reported per (Location, p, Vehicle_ID) only; they never change s_k.
- **Pipelines** (y = Local_Y in m; n = frame within the piece):
  - **Causal** (regimes, QC, O5): v_c(n) = (y(n) − y(n−5))/0.5 s; a_c(n) = (v_c(n) − v_c(n−10))/1.0 s; defined from frames 5 and 15. "Causal" refers to our own steps only; NGSIM's video processing may already smooth.
  - **Centred**, outcomes only: Savitzky–Golay (SG), 11 frames, order 2. y_SG is derivative 0; v0 is derivative 1 (delta = 0.1 s). Computed only where all 11 frames lie in the piece.
- **QC flag:** any frame in [t_k − L_k, t_k + 2W + 0.5 s] with |a_c| > b_phys, v_c < −0.5 or > 45 m/s, or a conflict.
- **Ramp set:**
  - US-101 {6, 7, 8}. The auxiliary lane counts as a ramp; coding from the 8ect-6jqj Lane_ID description.
  - I-80 {7} (Powell St on-ramp). Lane 1 (HOV) is kept.
  - [VERIFY the I-80 coding before the protocol commit; any correction by dated addendum before data.]

## 6. Split and data roles

- **NGSIM I-80 and US-101 are throw-away (D1).**
  - Cross-site, both directions: fit on I-80 and evaluate on US-101, and the reverse.
  - Online arms take only c_r and their start values from the fitting site.
- **O3** fits on evaluation P1 and scores P2–P3. I-80 P1 is 45 min earlier, at congestion onset.
- **The only fallback and INCONCLUSIVE block:** TGSIM I-294 L2 (`tpsq-zrwa`), burned once used [VERIFY freeway car-following with rebuildable leaders before the protocol commit].
  - Same code, constants and gates; analysed alone, never pooled with the NGSIM run.
  - O1, O2, O4, O5 and c_r are fitted on NGSIM I-80 + US-101 pooled. Gated cells {R1, R2}, J = 2; seeds 7,420,100–7,420,199.
  - Its GO or KILL is final (after an INCONCLUSIVE, reported "at the second look", shared rules §5). A GO there leads to the confirmatory protocol on the remaining TGSIM sets only; any other outcome there means the author re-plans.
  - Reconstructed I-80 (Montanino & Punzo [VERIFY]) is considered only after a Q STOP, under a new protocol.
- **Confirmatory set, fixed now:** TGSIM `9uas-hf8b`, `6a6e-vfvi`, `97n2-kuqi`, `7zjf-a4zf` (the four remaining freeway sets), with probe vehicles excluded.
  - A set is dropped only by that protocol's pre-data QC rule.
  - highD/exiD and I-24 MOTION come only after a GO.
- **The confirmatory protocol gates M as defined here** (same definition and constants).
  - The one-car chain (one tracker that follows one car's windows, plan §2) is reported there only as the guarantee row.
  - Making it, or any other variant, the primary arm needs its own kill test on new throw-away data.

## 7. Arms

All thresholds are clipped at b_floor. Static quantile = the ⌈(1−α)(n+1)⌉-th smallest capped fitting score, or b_phys if that rank exceeds n. Offline arms are O1–O5.

| ID | Arm | Role | Used by |
|---|---|---|---|
| O1 | Global quantile, fitting site | static | K0, K1, K3 |
| O2 | Per-regime quantile, fitting site | **strongest static** | K0, K1, K2, K3 |
| O3 | Per-regime quantile, evaluation P1 (scores P2–P3) | static, same site | K0, K3 |
| O4 | Per-v_Class quantile (< 50 windows: O1) | static | K0, K3 |
| O5 | Linear quantile regression (QR) at 1−α plus conformal offset | static | K0, K3 |
| M | Per-regime fleet tracker | **ours** | K3 |
| O6 | Global online tracker (one tracker for all regimes) | online opponent (K4) | K4 |
| O7 | Rolling per-regime quantile | online | N1, K4 |
| P | Placebo: M on permuted windows | control (F3) | K3 |
| Href | In-sample per-regime threshold per block | headroom reference | K0 only |
| RSS0 | Default b̂, Naumann et al., IV 2021, doi 10.1109/IV48863.2021.9575420 | report-only | report |

- **O5:**
  - Causal features at t_k: mean, minimum and SD (ddof = 0) of v_c, and minimum a_c, over the history; L_k; truck = 1{v_Class = 3} [VERIFY the coding before the protocol commit].
  - Features are standardised on fitting P1–P2. The QR linear programme (with intercept) is fitted on fitting P1–P2 by scipy.optimize.linprog(method='highs').
  - Offset = the ⌈(1−α)(n+1)⌉-th smallest residual s − ŷ on fitting P3 (b_phys if the rank exceeds n).
  - Threshold = min(b_phys, max(b_floor, ŷ + offset)).
- **O6:** M with one tracker for all regimes (same η, Δ_u, maturity and grid). c = the median non-empty batch size over all fitting-site windows (an integer ≥ 1). Start = O1's value.
- **O7:** at t_k, the threshold is max(b_floor, the ⌈(1−α)(n+1)⌉-th smallest of the last n = N_roll regime-r scores with maturity ≤ t_k), or b_phys if the rank exceeds n. The buffer starts with the fitting site's last N_roll regime-r scores in time order (the strongest version, disclosed).
- **P:**
  - Per regime r and placebo seed, permute the evaluation site's regime-r windows (all periods) with default_rng([seed, r]).
  - Walk them in batches of max(1, round(c_r)); each window takes the current q. Each batch is applied with M's update and no delay (so delay does not handicap P). Start = M's start.
  - τ_P,k is the median of window k's τ over the 20 permutations; P's miss rate is their mean. The spread is reported.
  - P uses future evaluation scores by design (an in-sample control).
- **Href:**
  - On the evaluation site, per nominal period, take the blocks (§9) in time order.
  - A block with fewer than 50 regime-r windows merges with the next one (the last block with the previous one) until n ≥ 50. If the period has n < 50, use the period pool. Never pool across periods.
  - Threshold = the ⌈(1−α)n⌉-th smallest score.
- **RSS0** stays only if its b̂ value is read in the paper before U1–U12 pass. Otherwise it is dropped, and the ledger says so.
- **Confirmatory only:** the recorded human time gap (HUM), the adaptation share G, ego references and further opponents (plan §2).

## 8. Metrics

- **Required time gap:** τ_k = [d_safe(v_e,k, v̄_k, q_k) + s0]/max(v_e,k, 1 m/s). v̄_k = the mean of v0⁺ over the 80 frames [t_k, t_k + W); v_e,k = min(v̄_k, v_cap).
- **Kill-test validity of M:** M is invalid in a gated cell if its point miss rate > α + δ. This is deliberately stricter for M than for the opponents (§10).
- **A1, reported for every arm × cell:** the one-sided 95 % upper bound of the miss rate is ≤ α + δ. The bound is the larger of the block-bootstrap and Clopper–Pearson bounds.
  - In this kill test, A1 filters K3's beats leg only: M must pass A1 in the cell where it beats (shared rules §5). A1 in every cell binds only in the confirmatory protocol. There it needs no Bonferroni adjustment, because "valid in every gated cell" is an intersection–union test.
  - The confirmatory protocol needs n_eff ≈ 2,070 per cell (≈ 4,100 windows at design effect 2) for an 80 % chance that a rate-α method passes all four cells.
- **Co-primary:** the median τ at nominal α, with M's validity as the filter.
- **Secondary:** capacity = median_k of 3600/(τ_k + L_e/max(v_e,k, 1 m/s)) veh/h/lane.
- **Also reported:**
  - the share of tied windows (paired τ difference exactly 0) for each pair of arms (shared rules §5);
  - the longest miss run (in order of t_k within an arm × cell; ties broken by track key);
  - misses per hour of scored leader time, misses/(n·W);
  - the worst rolling 10-min rate: windows with t_k in [s, s + 10 min) inside one nominal period, s in 1-min steps, ≥ 50 windows; the maximum over s.
- **Guards (report-only; stated only here):**
  - QC share;
  - share of s_k > 8 m/s² (the noise check; it never changes smoothing, QC or b_phys);
  - share of b_phys scores with v0 < 0.5 m/s;
  - dropped out-of-period windows;
  - per site and causal regime, the eligible share of leader time and the causal speeds of eligible vs ineligible windows;
  - deff_hat per arm × cell (bootstrap variance of the miss rate over the binomial variance).
- **Closed-loop metrics:** confirmatory protocol.

## 9. Statistics

- **Effect:** every τ effect, K0 included, is median_k of paired per-window differences (O3: P2–P3 windows only). Harm ratio = median_k(τ_M − τ_O)/median_k(τ_O).
- **Bootstrap:** fixed, non-overlapping 112.5-s blocks inside each nominal 15-min period, b = floor((t_k − nominal start)/112.5 s). This gives 8 blocks per period, 24 per site and 16 for O3.
  - A replicate draws 8 blocks with replacement in each period, independently per site. The same draw serves every arm and gate.
  - O1, O2, O4 and the O5 offset are refit on the fitting-site draw, and O3 on the evaluation-P1 draw. The O5 coefficients stay fixed (disclosed). Online and placebo q_k keep their real-order values.
  - B = 10,000; numpy.quantile(method='linear'); percentile CIs.
  - If U9 fails, miss-rate bounds use Clopper–Pearson on n_eff = n/max(1, deff_hat) instead (decided before data).
- **Blocks per cell** = blocks with ≥ 1 eligible window of that regime. Gated cells need 20.
  - O3 enters K3 with 16 blocks (P2–P3), as a disclosed conservative exception (listed in shared rules §5), if U9 passes at 16 clusters. Otherwise O3 is report-only.
- **Multiplicity:** J = the gated cells left after D and Q. K1, K2 and "beats" (K3, K4, N1) use two-sided Bonferroni CIs at 1 − 0.05/J. The harm rule uses uncorrected 95 %.
- **Beats:** the median paired difference is ≥ the threshold, and the Bonferroni CI lower bound is > 0.
- **Sensitivity rows only** (they never change the verdict): η (0.25, 1.0) and h_min (0.5, 2.0 s).
- **Seeds** (numpy.random.default_rng, PCG64):
  - 7,420,000: main bootstrap;
  - 7,420,001–7,420,020: the 20 placebo permutations (regime r: default_rng([seed, r]));
  - 7,420,021–7,420,029: sensitivity-row bootstraps;
  - 7,420,030–7,420,099: reserved;
  - 7,420,100–7,420,199: the fallback/INCONCLUSIVE re-run;
  - 7,420,200–7,420,499: confirmatory (shared rules §4);
  - unit tests: 1–99.
  - No other seed is used; every seed is logged.

## 10. KILL test

Order: D (counts only), then Q (flags only), both before any s_k; then K0–K4 and N1. D, Q and the power table form stage 1 (shared rules §6); scores and gates form stage 2. Every gate is computed and reported in every run. The operating map shows every arm × cell.

- **D:** a gated cell with < N_D eligible windows or < 20 blocks becomes report-only. Counts, causal regimes and causal speeds may be used here.
- **Q:** a gated cell whose flagged share of eligible windows is > α/4 becomes report-only.
- STOP if no gated cell remains after D or Q.
- **Power table** (stage 1, written to `gates.json` before any s_k), per gated cell, with design effect 2 (ASSUMPTION) and Bonferroni over J:
  - the A1 pass probability for an arm whose true miss rate is exactly α;
  - K2: the upper-side MDE at 80 % power, for the band [α/2, α + δ]. The lower side (rate < α/2) cannot be detected below n_eff ≈ 1,000 and is reported only;
  - K0, K1, K3: MDE = (z(1 − 0.05/(2J)) + z(0.80))·σ_b/√n_b, where n_b = the cell's blocks;
  - the Δb̂ around q = 4 m/s² that changes τ by 0.1 s and by 0.3 s at the cell's median causal speed (exact d_safe).
- **Underpowered** in a cell: the gate's MDE exceeds its threshold, or its threshold needs Δb̂ > 2 m/s², or (K2 only) the upper-side MDE is > 3α.
- **Remaining offline arm:** an offline arm leaves K0 and K3 in a cell only if it is significantly invalid there (one-sided 95 % lower bound of its miss rate > α + δ). Arms with a point estimate > α + δ that are not significant stay in, flagged.

| Gate | Passes if … (otherwise) | CI |
|---|---|---|
| K0 headroom | in ≥ 1 gated cell, median_k(τ_O − τ_Href) ≥ 0.1 s for every remaining offline arm O; a cell with no remaining offline arm passes (KILL) | point estimates |
| K1 | in ≥ 1 gated cell, the CI of median_k(τ_O1 − τ_O2) lies wholly outside (−0.3, 0.3) s (KILL) | Bonferroni |
| K2 | in ≥ 1 gated cell, O2's miss-rate CI (hull of bootstrap and Clopper–Pearson) lies wholly outside [α/2, α + δ] (KILL) | Bonferroni |
| K3 | M is valid in every gated cell; in no gated cell is M more than 5 % worse than a remaining offline arm (CI lower bound > 5 %); and in ≥ 1 gated cell where M passes A1, M beats every remaining offline arm and P by 0.1 s (KILL) | validity: point (every cell), A1 (the beats cell); harm: 95 %; beats: Bonferroni |
| K4 | neither O6 nor O7, if not significantly invalid, beats M in every cell where K3 passed (KILL, gate K4; the author may re-plan around the winning arm under a new protocol) | Bonferroni |
| N1 | O7 is not A1-valid, or M beats O7 in every cell where K3 passed (the claim narrows to "same efficiency as a rolling per-regime quantile") | Bonferroni |

- **Outcome** (shared rules §5; the first match wins):
  - STOP: the first STOP (D, Q, or an integrity or format STOP of §5);
  - else KILL, naming the first gate in the order K0, K1, K2, K3, K4 that fires decisively (shared rules §5) and is not underpowered (a gate counts as underpowered only if it is underpowered in every gated cell);
  - else INCONCLUSIVE, if any gate fired;
  - else GO (N1 may narrow it).
- **Actions:**
  - STOP: the named fallback block (§6), run as a new kill test; if it is unavailable (for example, licence), the author re-plans.
  - KILL (gate named): a decision entry; no #1 paper (S2); the author re-plans.
  - INCONCLUSIVE: one re-run on the named block (§6), analysed alone; its GO or KILL is final; a second INCONCLUSIVE, or an unavailable block, means the author re-plans.
  - GO or GO-narrowed: write the confirmatory protocol.

## 11. Run

- Shared rules §6 apply.
- The protocol sha256 must equal the hash in the accepting V entry (V83). The runner refuses a dirty tree.
- Each kill test (NGSIM, the named fallback) runs once, in the two stages of shared rules §6.
- A bug is code that disagrees with this protocol or its unit tests. A bug after results means: fix it, re-run everything affected with the same seeds, and log both (the failing unit test is committed first, shared rules §6).
- Changing a constant, threshold, arm, window rule or gate is a method change and needs new data.
- No score or score summary is written before Q passes.
- After a STOP, no score is computed on that site. The site is never reused for a kill test under changed QC, smoothing or regime rules.

```
require U1-U12 pass; clean tree; protocol sha256 = V83 entry; record commit, env lock
resource check (v6 idle or load < 15 %; night = Sleeping focus mode: CPU < 70 %); never touch fans
one process: systemd-run --user, nice -n 19, OMP_NUM_THREADS=1
# stage 1 (no s_k)
per site: verify MD5 + raw rows per Location; Location filter; clean (period id p)
          -> pieces -> windows (nominal period, ramps) -> causal regimes -> QC flags
write window table (track key, t_k, nominal period, regime, eligibility, QC flag); sha256 -> ledger
D (counts) -> demote / STOP?;  Q (flags per cell) -> demote / STOP?
power table + underpowered flags -> gates.json        # still no s_k
# stage 2
per site: centred scores s_k (cap, QC)
for (F, E) in [(I80, US101), (US101, I80)]:
    fit O1 O2 O4 O5 on F; O3 on E.P1; c_r and start values from F
    run M O6 O7 on E in time order (delayed, batched); P (20 permutations); Href
    per window: q, e, tau; bootstrap (B = 10,000)
gates -> outcome; outputs; ledger
```

## 12. Unit tests

All tests are synthetic and use seeds within 1–99. All must pass before any NGSIM row is parsed beyond the MD5 and the row counts.

- **U1. Safe gap vs brute force.**
  - Method: exact per-step kinematics (x += v·dt + ½·a·dt², with stops resolved inside the step), dt = 10⁻⁴ s.
  - Cases: all 7 × 7 × 8 = 392 combinations of v_e, v_L ∈ {0, 0.5, 5, 10, 20, 29, 35} m/s and b̂ ∈ {2, 3, 3.9, 4, 4.1, 6, 8, 10} m/s².
  - Pass: error ≤ 1 mm; equals Lemma 2 when b̂ ≥ b_min; anchors (30, 20, 2) → 41.50 m and (20, 20, 4) → 15.375 m; non-decreasing in b̂, i.e. d_safe(v_e, v_L, b̂₁) ≤ d_safe(v_e, v_L, b̂₂) whenever b̂₁ ≤ b̂₂.
- **U2.** b_req recovers constant braking (both branches). The cases v0 ∈ {−0.1, 0, 0.3, 0.6} m/s × X ∈ {−0.01, 0, 10⁻⁴, v0·h} m follow §3. A stationary leader with ±x_tol/2 jitter gives b_req ≤ 1 m/s².
- **U3.** G2 (gap ≥ s0 − x_tol) holds on random jerk-limited leaders, smoothed, at the 0.1-s grid.
- **U4.** The tracker's miss share never exceeds α + [c(b_phys − b_floor)/η + N_fl]/T_r on adversarial suites (delay, batches, clip, truncation). T_r = applied windows; N_fl = the maximum number of windows in flight.
  - **U4b:** update-time ties follow §4.
- **U5.** No leak: q_k, regimes and features ignore future data; q ≥ b_floor.
- **U6.** Cleaning handles duplicates, conflicts, shuffled rows, feet and time steps.
  - **U6b:** overlapping periods and ID reuse.
  - **U6c:** the Location filter (four interleaved locations, one with non-epoch Global_Time).
  - **U6d:** ramp exclusion.
- **U7.** On 200 exchangeable synthetic sets of 2,000 windows, the mean miss rate of O1, O2, O4 and O5 is within α ± 0.002. LP check: the share of O5 fitting points above the QR fit is within α ± (p + 1)/n (p = number of features).
- **U8.** On stationary data, |median_k(τ_M − τ_P)| < 0.02 s. After a 2 m/s² step in the score quantile, M beats P by ≥ 0.1 s.
- **U9.** Clustered binary misses at rate 0.02, design effects 2 and 5, 16 and 24 clusters, at the Bonferroni and one-sided 95 % levels. Pass: coverage ≥ nominal − 1.5 points.
  - **U9b:** every arm gets the same bootstrap indices.
- **U10–U11.** Synthetic site pairs trigger each row of the §10 table and each outcome.
- **U12.** Same seed, identical hashes.

## 13. Outputs and ledger

- **Run directory:** `/home/catalin/work/phd/v5b1_runs/k1_ngsim/<run_id>/`. It holds:
  - a data registry (URL, licence, citation, MD5s including the four probe files, counts);
  - the window table and its sha256;
  - arm × cell tables;
  - `gates.json` (the stage-1 power table and flags, then the gates);
  - the operating map and `report.md`.
- **Ledger:** every attempt, including failures. Fields: commit, protocol hash, window-table hash, MD5s, seeds, command, load, temperature, time, status, outcome.
- **Repo:** summaries only (< 5 MB). The outcome gets a V entry.

## 14. Time

(a) author; (b) Claude build and verify; (c) compute or download. Only (c) comes from probes, and its bootstrap and placebo figures are estimates.

| Step | (a) | (b) | (c) |
|---|---|---|---|
| Decisions | 0.5–1 h | – | – |
| Protocol review (with #2) | 1–2 h | 2–3 h | – |
| Download, MD5 | – | 0.1 h | 6–23 min |
| Build + tests | – | 5–8 h | minutes |
| Run + report | 0.25–0.5 h | 0.5–1 h | replay incl. 20 placebo runs < 5 min; bootstrap (B = 10,000) 13–50 min |
| **Total** | **1.75–3.5 h** | **8–12 h** | **≈ 20–80 min** |

## 15. Pending author items (defaults in bold; reply "accept defaults")

- **D1. NGSIM I-80 and US-101 are throw-away data for this kill test. The fallback/INCONCLUSIVE block is TGSIM I-294 L2 (tpsq-zrwa), burned once used. The confirmatory TGSIM set is fixed in §6.**
- **D2. All numbers in §10 and in the constants table (α = 0.02 per window, δ = 0.01, gate thresholds, K4).**
- Shared items S1–S7 are answered once, in the shared rules (V80–V82); this protocol is recorded as V83.
- Outside "accept defaults" (the shared rules' list): the TGSIM licence query, the highD/exiD access request and deleting the probe files.

## Constants and defaults (D2; fixed before data)

| Symbol | Meaning | Value | Sensitivity |
|---|---|---|---|
| ρ | ego response time | 0.5 s | – |
| a_acc | ego acceleration during ρ | 2.0 m/s² | – |
| b_min | ego braking, proper response | 4.0 m/s² | – |
| b_ego,max | emergency layer (closed loop, confirmatory) | 8.0 m/s² | – |
| b_floor | lower clip | 2.0 m/s² | – |
| b_phys | score cap; QC limit | 10.0 m/s² | – |
| s0 | standstill margin | 2.0 m | – |
| x_tol | position tolerance in b_req (ASSUMPTION) | 0.1 m | – |
| v_cap | ego speed cap (≈ 65 mph); fixed whatever the speed-limit check finds, which only adds a disclosure | 29.0 m/s | – |
| W = H | window, horizon | 8.0 s | – |
| first start | t_k offset from piece start | 4.5 s | – |
| h_min | shortest horizon | 1.0 s | 0.5, 2.0 s |
| L_k | causal history | 3–10 s | – |
| R1 / R2 | minimum / mean speed limits | 2 / 10 m/s | – |
| α, δ | miss target per window; validity tolerance | 0.02; 0.01 | – |
| q_1,r | tracker start | O2 value per regime (fitting site) | – |
| η | step size | 0.5 m/s² | 0.25, 1.0 |
| c | fleet: median batch size on the fitting site (P: max(1, round(c_r)); O6: integer ≥ 1) | count | – |
| Δ_u | update period | 1.0 s | – |
| N_roll | rolling window | 500 windows | – |
| SG | centred smoother | 11 frames, order 2 | – |
| causal diff | speed / acceleration | 5 / 10 frames | – |
| QC | speed range; track gap | −0.5 to 45 m/s; 0.15 s | – |
| period tolerance | Global_Time range per period | nominal start − 2 min to end + 3 min | – |
| L_e | vehicle length (capacity) | 5.0 m | – |
| B | bootstrap replicates | 10,000 | – |
| block | bootstrap block | 112.5 s (8 per period) | – |
| Q | flagged share per gated cell | α/4 | – |
| N_D | windows; blocks per gated cell | 1,000; 20 | – |
| deff | design effect, power table (ASSUMPTION) | 2 | – |
| σ_b | block SD of paired τ differences (ASSUMPTION; Claude's guess, no data) | 0.15 s | – |
| power | MDE power | 80 % | – |
| underpowered | K2 upper-side MDE; Δb̂ needed | > 3α; > 2 m/s² | – |
| K0, K3, K4, N1 | gap thresholds | 0.1 s | – |
| K1 | regime difference | 0.3 s | – |
| K2 | transfer band | [α/2, α + δ] (shared rules §5) | – |
| K3 harm | "never worse" margin | 5 % | – |
| J | gated cells for Bonferroni (after D and Q) | ≤ 4 (NGSIM); ≤ 2 (fallback) | – |
| seeds | see §9 | 7,420,000–7,420,499 | – |
