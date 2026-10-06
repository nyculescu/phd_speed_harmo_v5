> **ABANDONED (D4.8, 2026-10-06): never run, no seed used. Kept as history.**

# Prize screen PS-S: protocol v0 (DRAFT, under design review; binding only once committed with every §0.6 item resolved)

**Purpose (D4.2).** A pre-registered, **KILL-only** screen of the size of the prize for day-pattern control (coordinated ramp metering + speed harmonisation) on U.S.169 SB. It runs on a fast, deliberately optimistic cell-transmission plant **before any METANET v4 compute**.
- If it KILLs, the day-pattern DRL route stops.
- If it does not KILL, METANET v4 is written as the gate plant (P6b unchanged).
- No outcome is ever a GO.

## 0. Status and decisions already taken

| Ref | Decision | Source |
|---|---|---|
| D4.2 | Prize screen first; KILL-only; METANET v4 next on NO-KILL | decision log 2026-10-06 |
| D4.3 | Seed block 7,191,000–7,191,999 with the roadmap §10 sub-range roles | decision log |
| D4.4 | Post-stop v3 lessons may be used as design input, with disclosure | addendum 2026-10-06 |
| D4.6 | Write PS-S from the design panel's outline | decision log |
| D4.7 | v3 §7 R4(d) (GO must hold on the low-drop variant) and R2(c) (GO must hold with zero uplift) are **bound unchanged** for the future gate protocol, so variants L and Z count (§5, K1) | decision log |

### 0.6 Author items still open (each must be resolved before the commit)

| # | Item | Proposed default |
|---|---|---|
| A1 | **R-PS1:** pin the gate's low-drop variant structurally (head drop ≤ δ_cap, checked by a pre-registered capacity probe) | bind, δ_cap = 1 %; if a METANET probe cannot be specified in v4, variant L falls back to the measured-r rule (disclosed) |
| A2 | Joint conjunct for the gate: a GO must also hold on the low-drop variant **with** zero uplift (enables variant LZ) | bind |
| A3 | R-PS2–R-PS4, R-PS7, R-PS9, R-PS10: requirements the future gate protocol must keep (§12) | bind as written |
| A4 | R-PS5: gate-draft T2 uses I* or becomes report-only; T1's "control matters" clause becomes report-only or I-vs-nc. Decided now, never after the screen | T2 → uses I*; T1 → report-only |
| A5 | R-PS8: the gate's GO cells exclude D2.2.2 surprise events (reported sensitivity / DRL test instead) | bind |
| A6 | Seed sub-ranges (§7): 000; 010–012; 100–102; 500–503 used; 013–019, 103–109, 504–509 reserved for the screen | approve |
| A7 | Optimistic settings and branches (§4–§5): drop ladder 0–15 % in 0.5 pp steps; s ∈ {1.000, 0.975, 0.950}; λ ∈ {0.95, 1.00, 1.05, 1.10}; spread U[0.80, 1.20] i.i.d., 3 draws per day; secondary-head branch with the κ rule; storage × 1.25; σ = 5 %; mtfc_rm kept in B; LP-MPC (120-min horizon, 5-min re-solve, ε = 2 %) | approve |
| A8 | Use the F11 floors L_r,1 = 0.990 and L_r,2 = 0.958 (real-data summaries of validation days; no model run on them) in variant Z's drop rule | approve, disclosed |
| A9 | IRIS storage unit, the s_jam source (R1(a) [VERIFY]) and r_min | to be looked up and cited before commit |
| A10 | Statistics: robust UCL = max(percentile, BCa, jackknife-t); one-sided level 1 − 0.025/m; intersection–union over cells and looks; LOO guard; ≥ 6 above-capacity days per cell | approve |
| A11 | Data-free inclusion rule on the throw-away day: I_mpc_exact and LP-OC included if the projected wall time is ≤ 24 h; J_LB if the full-day LP solves in ≤ 30 min and ≤ 8 GB | approve |
| A12 | What follows a KILL, decided now: the D1 supervised fallback, H2 (MTFC-VSL + ALINEA), or another track | author's choice |
| A13 | Build plan about one week (estimate), with a checkpoint code review (High effort, ultracode on) before the evaluation runs | accept |

## 0.5 Provenance of the design

**Choice of winner.** PS-C has the highest total (20; PS-B 16, PS-A 12). Its flagged flaws are all fixable before commit:
- storage omits "× storage lanes";
- the spread is narrower than the R3 clip;
- secondary heads are fixed rather than branched;
- its T1 amendment depends on the outcome;
- Γ_A is unpowered;
- compute is under-estimated.

**Grafted from PS-B:**
- the LP relaxation bound J_LB: solved per look, report-only, used as a label;
- the validity battery;
- branching on unresolved inputs;
- Bonferroni across conjunct variants;
- the early-exit idea;
- A_ctrl.

**Grafted from PS-A:** binding requirements on the gate (R-PS1 to R-PS3) and a code assertion that only calibration days are read.

**Grafted from the judges:**
- drops calibrated on measured r;
- the R2(c) conjunct;
- RM+VSL scope only;
- a robust UCL;
- the fixes listed above.

**Cut to keep the build near one week:**
- CMA-ES;
- the Γ_A grid and δ_top;
- u = 1.5 (beyond the R2(a) family);
- RM-only cells;
- the merge-dependent drop variant;
- the MILP rungs;
- PS-A's field-envelope computations;
- the optional run on the FAILed v3 plant.

## 1. Question

Take a fast, deliberately optimistic cell-transmission plant of U.S.169 SB (CTM-2C; §3). Run it on the 22 usable 2023 calibration Wednesdays. Is the gate's own headroom statistic below 10 % in every cell of a pre-registered grid, in both gate looks (all days pooled; above-capacity days), with a one-sided robust upper confidence limit? The statistic is
H = median_s(J_B,s − J_I,s) / median_s(J_B,s),
with:
- I replaced by an informed envelope I* that is at least as strong as every informed arm the gate may use;
- B the best tuned non-learning arm, drawn from a subset of the gate's B list.

The question is asked on plant variants that each dominate one conjunct of the gate's GO rule (§5).
- **Yes, for some bound variant:** KILL. The day-pattern DRL route stops before any METANET v4 compute.
- **Otherwise, or if any validity precondition fails:** NO-KILL. METANET v4 is written as the gate plant (D4.2; P6b unchanged).

No outcome supports a GO, and no screen number may be quoted as headroom.

## 2. KILL logic (explicit chain; formal vs argued)

**Notation.**
- P_s = a screen plant cell.
- P_g = the gate plant (METANET v4, or its R4/R2 variants).
- H_gate(P) = the gate's rule evaluated on plant P: the gate's B set, tuning and I.
- H_scr(P_s) = the screen statistic: the screen's B subset, and I* in place of I.

**Formal on the screen plant, given the bindings in §12.**
- **F1 (informed side).** Per unit u (day × capacity draw), J_I*,u = the minimum of J over:
  - exact implementations of every gate-defined informed arm (I_plan, I_hero, I_mpc), with the same frozen mappings fitted on the same tuning fold;
  - the extra informed candidates;
  - every B arm's realised trajectory.

  Hence J_I*,u ≤ J_X,u for X = I_plan, I_hero and I_mpc, and so for the gate's I, which is one of them (picked on tuning days). All candidates run on the same plant, with the same queue override and side constraints.
- **F2.** From F1, for any fixed B and any set of sequences, J_I*,s ≤ J_I,s pointwise. So median_s(J_B − J_I*) ≥ median_s(J_B − J_I) with the same denominator, and H(I*) ≥ H(I). This holds in every bootstrap resample, so the percentile-UCL ordering is preserved. **This removes the gate draft's T2 defect.** T2 pairs I_plan, which can be weaker than I, with one baseline, so G can understate H. The screen never does this.
- **F3 (B side, mean form only).** B_scr ⊆ B_gate (set inclusion, bound in R-PS3). In the ratio-of-means form H_mean = 1 − mean(J_I)/min_X mean(J_X), adding arms or lowering any J_X can only lower H_mean. So H_mean(gate set) ≤ H_mean(screen set) for the same per-arm J.
- **F4 (conjunct logic).** If the author binds, before the run, that the gate keeps R4(d) (a GO must also hold on the low-drop variant) and/or R2(c) (a GO must also hold with zero uplift), then a gate GO implies a GO on that conjunct variant. A KILL on a screen variant that dominates the conjunct therefore implies no gate GO. The domination itself is A3/A4.
- **F5 (statistics).**
  - Inside a variant: an intersection–union test over cells and both gate looks. A false KILL via a variant has probability ≤ α_v (approximately, see A7), with no multiplicity cost for adding cells.
  - Across m bound variants: Bonferroni, α_v = 0.025/m.
- **F6 (label only).** Where the per-look LP relaxation J_LB is computed and has passed the validity battery, J_LB ≤ J_π for every admissible controller π on the screen plant, DRL included. A KILL that also holds with J_LB in place of J_I* is labelled "bound-certified".

**Arguments, not proofs (each is stated in the KILL record).**
- **A1 (B parity).**
  - (a) The gate's B arms are at least as well tuned as the screen's: more days, grids ⊇, budgets ≥, sensing noise ≤ (bound in R-PS3). "More tuning ⇒ lower out-of-sample J" is not guaranteed.
  - (b) **The gate's median form is not monotone in J_B.** A ratio of medians can fall slightly when B weakens unevenly across sequences. Example: J_B = (10, 20, 30) and J_I = (9, 0, 28) give H = 2/20; raising the second sequence's J_B by 0.5 gives 2/20.5. The ratio-of-means form is monotone (F3). With many 14-day sequences, each J_s is a mean, so the median form is close to the mean form; that is an approximation.
- **A2 (cross-plant transfer).** H_gate(P_g) ≤ max over cells H_gate(P_s), because:
  - every direction expected to enlarge the prize is set at or beyond the gate's admissible range (§4);
  - every direction of unclear sign is branched (§5).

  The argument fails for mechanisms METANET has and CTM-2C lacks (§16).
- **A3 (drop domination).** The screen's drop at each head is at or beyond the drop that the gate's variant can carry while passing the same measured-r and S1 criteria. This uses the screen plant's own map from structural δ to measured r. That map may differ from v4's, so this is an argument, unless R-PS1 binds the gate's low-drop variant structurally. Even then, monotonicity of H in δ is an inference (protocol v3 §0.4 says so).
- **A4 (I_mpc across plants).** The gate's I_mpc on METANET uses a fitted, structurally mismatched model. It is assumed to be no stronger relative to B than the screen's fitted-model and exact-model LP-MPC are on CTM-2C.
- **A5 (grid coverage).**
  - The two capacity-spread points (c ≡ 1; U[0.80, 1.20]) bracket the gate's F̂.
  - The λ shift covers 2023→2024 drift and the ±5 % discharge freedom of P5a.
  - Storage × 1.25, detector noise on B, and FIFO are optimistic.
  - H is not assumed monotone between grid points; this is a disclosed gap.
- **A6 (days).** 22 heavy 2023 Wednesdays plus λ shifts stand in for 2024 Wednesdays. There are no light days and no generated transition-band days.
- **A7 (small n).** With 22 day clusters the percentile bootstrap undercovers. The robust UCL and the leave-one-day-out (LOO) guard mitigate this but do not remove it.
- **A8 (secondary heads).** The two secondary-head branches bracket v4's behaviour at km 2.39 and at E15.
- **A9 (surprise events).** These are covered only if the gate's GO cells exclude D2.2.2 events (R-PS8).
- **A10 (background delay).** The triangular FD has no free-flow-branch delay, so J_B,scr is smaller than METANET's J and the screen ratio is larger, which is conservative. The exception: if v4's speed–density (background) delay is controllable, it is a prize source the screen lacks (§16).

## 3. Plant: CTM-2C (new code `vsl_lab/plants/ctm2c.py`, numpy, vectorised over days, draws and arms)

**Geometry:** the protocol v3 model geometry and its 36-cell table (§1.3–1.5).
- Ramp placement and station-reading cells as v3 §1.5: S of Highwood reads cell 23, Pioneer Tr cell 30, Old Shakopee Rd cell 32.
- No fitted v3 parameter is used.

**Fundamental diagram:** triangular per group.
- v_f per group = the median of the F6 lane free-flow medians of that group's stations [lab convention, proposed].
- ρ_jam = 180 veh/km/lane (v3 §2.3).
- w = Q/(ρ_jam − Q/v_f).

**Heads** (two-capacity switch, the F1 form of v3 §6.1):
- **B1:** head cell 26 (E13 merge). Q_dis,1 = s·c1·2·1,774 veh/h (F8 merge-section discharge per lane).
- **B2:** head cell 31 (E14 merge). Q_dis,2 = s·c2·2·1,853.
- Q_free,k = Q_dis,k/(1 − δ_k).
- **Memory:** m = 1 when ρ_head > ρ_c, and it stays 1 while ρ > 0.9·ρ_c (η = 0.9 as in R4(c)).
- Only the head cells carry the switch. Station cells are never capacity-scaled (D4.4 lesson 4).

**Other cells:** capacity ≥ max(1.1 × the cell's maximum arriving 15-min flow, λ_i·1,853), so they do not bind, except in the secondary-head branch (§5).

**Diverges and merges:**
- Diverges: strict FIFO, exogenous β_e(t) from v3 §3.3.5.
- Merges: Daganzo priority with a fixed ratio [lab convention].

**Inputs: mode C, per R1–R2.**
- Exogenous and identical across arms within a day: the Minnetonka Blvd boundary, the 6 upstream metered ramps (replayed), and the class-B balances.
- The 4 controlled ramps (E9, E12, E13, E14) take Queue-detector arrivals, with the R1(c) P0 rule. If fewer than 80 % of ramp-days are valid, the replay inflow is used instead (disclosed).
- Freeway-to-freeway merges (E7, E8, E10, E11) take either:
  - the R2(a) uplift s_m,d·P_m(t) in that day's queued bins, with P_m the median over the 22 calibration days; or
  - served counts, depending on the variant.
- Inputs reuse `vsl_lab/data/metanet_inputs.py`.

**Ramps:**
- Storage = IRIS storage × 0.3048 × storage lanes / s_jam × 1.25 (R1(a); the unit and s_jam are [VERIFY]).
- Queue override at storage or at a max_wait of 240 s, using FIFO cumulative curves (R1(b)). It binds every arm, I* included.
- Meter rate within [r_min, 2,200] veh/h, plus "off".

**Origins:** boundary and unmetered merges have unbounded point queues that count in J.

**VSL:** only in the R6 areas (B1: km 1.06–2.56; B2: km 3.12–4.62).
- B arms use the R6 primary min form, translated to the CTM: v' = min(v_f, (1 + α)v_VSL), Q' = v'wρ_jam/(v' + w), α_0 = 0.1.
- I* candidates may additionally use an ideal flow cap in [0, S] on the area cells' boundary flows. This is a superset.

**Numerics:**
- T = the largest value in {10, 8, 5, 4} s with v_f,max·T/L_min ≤ 1 and w·T/L_min ≤ 1 (a data-free rule; L_min = 352 m).
- Step-halving check at T/2 (§10).

**Day:**
- 04:00–05:00: uncontrolled warm-up, identical for all arms.
- 05:00–23:00: control.
- After 23:00: no new demand; the plant drains until empty or 01:00.
- Deterministic given (day, c, controls).

## 4. Optimistic settings: value and the direction each pushes the prize

| # | Setting | Value | Direction | Status |
|---|---|---|---|---|
| O1 | I* strength | per-unit minimum over the gate-defined I_plan, I_hero and I_mpc (fitted model); plus LP-MPC on the exact model, LP-OC (open-loop full-day LP plan, executed with the override), ideal VSL flow caps, and every B arm's trajectory | J_I* down, prize up | F1 formal; extras optional by a data-free timing rule (§13) |
| O2 | B set | subset of the gate list: {const (grid includes off, so nc is nested), tod_cnt, alinea, hero, mtfc_rm}. Excluded: pm1h, pialinea, ad_alinea, alinea_tod, specialist (needs waves), mpc_f (an exact-ish CTM model would be stronger than the gate's mismatched one) | J_B up, prize up | F3 formal (mean form) |
| O3 | B tuning | one 11-day fold, cross-fitted; coarse pre-registered grids; budgets the gate must equal or exceed | J_B up | A1 |
| O4 | B sensing | station cells only (R13(b)), 60-s aggregation, multiplicative noise σ = 5 % [lab convention], 60-s update, also for the counts tod_cnt is fitted to. I* uses no detectors | J_B up | A1 (the gate's noise must be ≤ σ, R-PS3) |
| O5 | Drop, variant L | measured-r rule (§5), or δ_cap if R-PS1 is bound | prize up | A3 |
| O6 | Drop, variant Z | the largest drop admissible under loosened P5b and P9(1), plus one rung | prize up | A3 |
| O7 | Demand drift | λ ∈ {0.95, 1.00, 1.05, 1.10} on every exogenous input, on evaluation days only; B and the I mappings are tuned at λ = 1. This also covers P5a's ±5 % discharge freedom | mistunes B; overload changes either way, so it is gridded | A5 |
| O8 | Uplift | variant L: R2(a) family; variant Z: zero (the gate's own conjunct) | L: more demand at the I-494 merges (argued prize up). Z: fixed by the gate rule | F4 plus argument |
| O9 | Storage | × 1.25 (top of the R1(a) ±25 %) | more pre-metering authority for I* | argued; × 1.0 reported |
| O10 | FIFO at diverges | strict | raises the value of placing or avoiding queues (X9–X13 blocking) | argued |
| O11 | Ramp information | I* knows the true demand, including uplift and λ; never c (R3(c)) | as the gate | bound |
| O12 | Above-capacity look | arm-independent rule bound on the gate (§9) | none; the definitions are aligned | bound |
| O13 | Decision rule | robust UCL < 10 % in every cell and both looks, plus the LOO guard | a KILL is harder | formal |
| O14 | Background delay | none (triangular FD) | smaller denominator, ratio up | A10 |

## 5. Variants (gate conjuncts) and cells

**Variant L (R4(d) conjunct; uplift on).**
- **If R-PS1 is bound:** δ_L,k = δ_cap (default 1.0 % structural at both heads).
- **Otherwise (measured rule):** δ_L,k = min(15 %, max{δ ∈ Λ : r_k(δ) ≥ 0.995} + 0.5 pp). This is one rung past the largest drop still inside R4's low-drop band (target min(1, U_k) = 1 at both heads, since U_1 = 1.059 and U_2 = 1.026; tolerance ±0.5 pp). 15 % is R4(c)'s Δ bound and is the fallback.

**Variant Z (R2(c) conjunct; served counts at E7, E8, E10, E11).**
- δ_Z,k = min(15 %, max{δ ∈ Λ : head k passes the loosened drop-side rows} + 0.5 pp). The rows:
  - P5b(ii): median r_k ≥ L_r,k − 0.02, with L_r,1 = 0.990 and L_r,2 = 0.958 (F11);
  - P5b(i): median(r_model − r_real) ≥ −0.04;
  - at B1, which is first-active on 22/22 days (F10), P9(1): median(S1_model − S1_real) ≤ +0.05.
- The 0.02 slack [lab convention, proposed] is for the calibration-to-validation day-set difference. For example, the real B1 median r is 1.021 on calibration days (F8) and 1.003 on validation days (F11).

**Variant LZ (optional).** Only if the author binds a joint low-drop-with-zero-uplift conjunct. It uses δ_L with served counts.

**Variant P (fallback).** If neither R4(d) nor R2(c) is bound: uplift on, δ_Z. Then m = 1 and power is low.

**Drop measurement (shared).**
- Ladder Λ = {0, 0.5, …, 15} %.
- Replay configuration: mode C with each controlled meter at its replay inflow, served counts, c = 1, λ = 1.
- Data: the 22 calibration days.
- Model station series pass through the EA-2 event layer with the observation operator, and then the committed C4 block. C4 is r = the mean flow from onset + 10 min to the episode end, divided by the mean flow of the 15 min before onset, at the downstream station. B1's window is censored at the real B2 onset.
- **Why measured r and not δ = 1 − L_r:** under EA-2, B1's onset is detected at S of Highwood, at least 0.86 km upstream of the head, so the 15 min before onset may already be discharge. B1's measured r can therefore stay near 1 for sizeable δ (inference).
- Both heads move together, as in R4(c). If the joint run moves a head back inside its band, that head is raised rung by rung (the optimistic direction only).

**Capacity level s.** The largest s ∈ {1.000, 0.975, 0.950} at which the realism floor V2 passes for that variant, with the drop rule re-run at each s. If none passes, the result is INVALID.

**Cells per variant (16):**
- λ ∈ {0.95, 1.00, 1.05, 1.10};
- spread ∈ {c ≡ 1; c1, c2 i.i.d. U[0.80, 1.20] per head per day, 3 draws per day}. That is the full R3 clip range, hidden from every arm;
- secondary heads ∈ {off; on}.
  - **On:** a two-capacity switch (η = 0.9, δ = max(δ_1, δ_2) of the variant) at cell 23 (just after the km 2.390 merging drop, in B1's R6 area) and at cell 33 (E15 merge; this stands for the 2-lane reading, since D4.5 was inconclusive).
  - Their capacity = the smallest κ ∈ {1.10, 1.075, …, 0.90} × the cell's median daily maximum arriving 15-min flow at which replay shows model episodes on that cell's station pair on ≤ 3 calibration days that have no real episode there. 3 is the P8(i) limit max(2, ⌈0.10 × 22⌉).

**Fixed in every cell:** RM+VSL scope (the author's scope, 2026-10-05), α_0 = 0.1, storage × 1.25, σ = 5 %.

**Gate looks per cell:** pooled, and above-capacity. That makes 32 UCLs per variant.

## 6. Arms and quantities

**Yardstick (reported, not in B):** nc.

**B arms (each tuned per configuration of variant × spread × secondary heads, on fold A and evaluated on fold B, then swapped; shared across λ):**
- `const`: rate per controlled ramp; the grid includes off.
- `tod_cnt`: a 15-min Wednesday plan fitted to noisy counted bottleneck volumes under nc on tuning-fold days, with a frozen counts→schedule mapping.
- `alinea`: one loop per controlled ramp, with stations per R13(b).
- `hero`: clusters per R13(c). B1: E13 master with E12 and E9. B2: E14 master with E13. E13 takes the lower of its two commands.
- `mtfc_rm`: the existing `vsl_lab/controllers/mtfc.py`, one loop per R6 area, with tuned HERO; jointly tuned.
- Side constraints enter the tuning as penalties.

**Informed candidates (the true demand of the unit, including uplift and λ; c = 1 in every model, R3(c)):**
- `I_plan`: the tod_cnt structure fed the true demand through the same frozen mapping.
- `I_hero`: HERO whose set-point offsets and activation lead come from a lookup table (true-demand features → parameters) tuned on the tuning fold. This is the CLAUDE.md I definition, never the best grid point per evaluation day.
- `I_mpc`: the gate-defined LP-MPC. It runs on a CTM model fitted by a pre-registered procedure to screen-plant data on tuning seeds (7,191,102). Horizon 120 min; re-solved every 5 min; head margin ε = 2 % [lab convention, proposed]; meters and VSL.
- **Optional extras** (included or not by the data-free timing rule of §13):
  - `I_mpc_exact` (the same, on the exact model);
  - `LP-OC` (a full-day open-loop LP plan, executed with the override).

**I\* per unit** = the minimum J over:
- the candidates that meet the side constraints, with the served-vehicles bound taken against the least-serving B arm (the loosest reading);
- every B arm's trajectory.

**Statistic per variant, cell and gate look:** H* in the gate form (§9), with B re-selected inside each resample.

**Reported only (never a KILL path):**
- **H_LB:** H with J_LB, the per-look LP relaxation. It uses Q_free of that look (fixing PS-B's δ-independence error), c known, holding allowed, storage and max_wait as linear cumulative constraints. Computed for the deterministic cells only, if the throw-away timing allows.
- **A_ctrl** = 1 − ΣJ_LB/ΣJ_nc.
- **T2 as drafted,** G_plan = (J_tod_cnt − J_I_plan)/J_tod_cnt, next to G* = (J_tod_cnt − J_I*)/J_tod_cnt. In the mean form G* ≥ H, because J_tod_cnt ≥ J_B and J_I* ≤ J_I. The difference G* − G_plan quantifies how much T2 understates.
- **T1's statistic** (tuned ALINEA vs nc on above-capacity days). It is not a valid KILL path here: the screen's ALINEA is deliberately weakened, so a T1 failure on the screen does not bound T1 on v4.
- **H\* with B restricted to RM arms** (label only).
- **Per-arm diagnostics:**
  - episode occurrence, onset, duration and extent at B1/B2 and P7c, per R13(d);
  - origin-queue share (gameability);
  - FAIL counts;
  - exit volumes vs nc;
  - J_LB ≤ J_I* ≤ min J_B gaps.
- **Sensitivities:** storage × 1.0, σ = 0, and (optional) an argued background-delay term in the denominator.

## 7. Days, folds and seeds

**Days**
- Only the 22 usable 2023 calibration Wednesdays (F2, F8): B1 active 22/22, B2 9/22 (F10).
- Folds alternate by date (11 + 11). This rule uses no data. Every reported J is out-of-fold.
- The 97 validation days are never simulated, and 2024 stays unopened (D3.3). No other 2023 day is pulled.
- The code asserts the day list.
- **Throw-away input:** one synthetic day, the per-clock-time median of every calibration-day input. It is used only for timing, solver settings and smoke tests (disclosed).

**Seeds** (block 7,191,000–999, D4.3; roadmap §10 roles; to be approved):

| Seed | Use |
|---|---|
| 7,191,000 | throw-away (synthetic day) |
| 7,191,010 | plant checks: S-T0, S-T3 |
| 7,191,011 | 100 random feasible actuator schedules per day, for the bound-validity battery |
| 7,191,012 | V5 positive-control draws |
| 7,191,100 | tuning-fold capacity draws (SeedSequence spawned per configuration; common random numbers across arms) |
| 7,191,101 | tuning-side detector noise |
| 7,191,102 | data for fitting the I_mpc model |
| 7,191,500 | evaluation capacity draws |
| 7,191,501 | evaluation detector noise |
| 7,191,502 | 14-day sequence draws |
| 7,191,503 | day-cluster bootstrap |

- 7,191,013–019, 103–109 and 504–509 are reserved inside the screen.
- 001–009, 020–099, 110–299, 300–499, 510–699 and 700–999 stay untouched for v4 and the gate.
- A re-run after a bug fix reuses the same seeds.

## 8. Metric, side constraints and stop rule (gate draft §4–§5, restated because the draft is untracked)

**J per unit** = door-to-door delay per vehicle, 05:00 to the end of the drain:
- it includes origin queues (boundary and unmetered merges) and ramp queues;
- it equals (time spent in cells + ramp queues + origin queues − Σ_i (L_i/v_f,i) × cell-i throughput) / vehicles entering;
- co-headline: vehicles served by 23:00.

**Side constraints** (all arms; they are tuning penalties for B and feasibility conditions for I*):
- ramp queue ≤ storage in ≥ 95 % of minutes;
- served ≥ B − 1 %;
- drain within 2 h after 23:00.

**Stop rule:** FAIL-GRIDLOCK if either of these holds:
- an internal cell is at jam density with zero outflow for ≥ 10 min;
- network exit flow is 0 for ≥ 10 min while vehicles are inside and demand > 0.

The insertion backlog never stops a run. FAIL runs stay in the metric with censored delay plus the run's maximum observed delay. If any arm has a FAIL share > 5 % in a cell, that cell blocks a KILL.

## 9. Statistics

**Paired unit:** the day. Draws are averaged within the day, with common random numbers across arms.

**Sequences:** 14-day sequences of Wednesdays (R12), drawn with replacement from the 22 out-of-fold days.
- J_s = the mean daily J.
- H = median_s(J_B,s − J_I*,s) / median_s(J_B,s), where B = argmin over the screen's B arms of median_s(J_X,s − J_I*,s).
- The point estimate uses 2,000 sequences.

**Above-capacity look.** A (day, draw, λ) unit is above capacity if its arm-independent arriving true demand at B1 or B2 exceeds 1.05·c_k·Q_free,k in some 15-min window. Arriving demand is computed by conservation with the day's splits and no queues. J_s is taken over each sequence's above-capacity units. A cell with fewer than 6 qualifying days blocks a KILL.

**Uncertainty:** a day-cluster bootstrap, 10,000 resamples. Each resample redraws 500 sequences and re-selects B.

**Robust upper limit:** UCL_v = max(percentile, BCa, delete-one-day jackknife-t with t_21) at the one-sided level 1 − 0.025/m. With m = 2, that is 98.75 %.

**LOO guard:** every leave-one-day-out point estimate must be < 0.10.

**Convention:** one convention throughout, the median of paired differences, as in the gate.

## 10. Tool checks and validity preconditions (criteria committed before data; any failure → INVALID → NO-KILL, logged)

- **V1 (S-T0, actuators bind).** On plant-check runs, a ±20 % change in each controlled meter rate, and in each VSL area setting under both forms, moves the release and the downstream head density in the expected direction.
- **V2 (realism floor and D-check, per variant, in replay on calibration days).**
  - (a) The median system queue duration (P7c union construction, EA-2 with the observation operator) is ≥ the real median − 30 min.
  - (b) B1 is active on ≥ 17/22 days.
  - B2 occurrence and extent (P7b) are reported only; the B2 knife edge is a D4.4 lesson.
  - (c) Gate draft D-check under nc on above-capacity days: the counted peak 15-min flow is ≤ discharge + 5 %, and the plateau is ≥ 1.2 × the time demand exceeds capacity (medians).
- **V3 (S-T3).**
  - Re-runs are bit-identical.
  - At T/2, |ΔJ|/J ≤ 1 % for nc and I_plan (pooled).
  - The head-activation day sets change by at most 1 day per head [lab convention, proposed; v3 failed on a single near-tie day].
- **V4 (ordering and information hygiene).**
  - J_I* ≤ J_I_plan, J_I_hero and J_I_mpc on every unit (by construction; asserted).
  - Unit tests check that B observations contain only noisy station-cell, ramp-detector and queue readings, and that no arm reads c.
  - Where J_LB exists, J_LB ≤ J_I* on every unit.
- **V5 (positive control for the informed side).** In a reported prize-rich cell (δ = 15 % at both heads, λ = 1.10, c = 1, uplift on), I* must beat nc by ≥ 10 % on above-capacity days (point estimate). Failure means the informed side is broken.
- **V6 (bound-validity battery; only if J_LB is computed).**
  - J_LB ≤ J_sim for nc, for every B grid point evaluated, for 100 random feasible schedules per day and for every I* candidate.
  - The LP accepts each fixed simulated trajectory as feasible.
  - Realised ramp waits are ≤ 240 s + one step.
  - A failure removes J_LB and triggers a review of the shared LP builder used by I_mpc. Any bug found there means: fix it, re-run everything affected, and log both outcomes.

## 11. KILL rules and outcome labels

1. **K0.** V1–V5 must pass before any evaluation run; otherwise INVALID, which counts as NO-KILL.
2. **K1.** The variants are fixed by the author's bindings before the run.
   - Variant L counts only if R4(d) is bound.
   - Variant Z counts only if R2(c) is bound.
   - Variant LZ counts only if the joint conjunct is bound.
   - With neither R4(d) nor R2(c) bound, only variant P runs.
   - m = the number of variants.
3. **K2.** Variant v KILLs only if all of the following hold in every one of its 16 cells and both gate looks:
   - (a) UCL_v(H*) < 0.10;
   - (b) every LOO point estimate < 0.10;
   - (c) above-capacity look: ≥ 6 qualifying days;
   - (d) no arm has a FAIL share > 5 %.
4. **K3.** Overall: KILL if some variant KILLs; otherwise NO-KILL.
5. **K4 (early exit; affects compute only).**
   - Variants run in order L (or LZ), then Z (or P).
   - Inside a variant, cells run in a pre-registered prize-rich-first order: λ = 1.10, secondary on, c = 1, then the rest.
   - The first cell-look with UCL ≥ 0.10 ends that variant.
6. **K5.** Not KILL paths: the T1 statistic, G_plan and G*, H_LB, A_ctrl, H* with RM-only B, and the information-only gap.
7. **K6 (labels fixed now; they never change the outcome).**
   - Every KILL record states: "conservative on the screen plant by F1–F6; transfer to METANET v4 argued (A1–A10), not proved".
   - Sub-labels:
     - the variant(s) that fired;
     - "bound-certified" if K2 also holds with J_LB;
     - "VSL-B-independent" if K2 also holds with B restricted to {const, tod_cnt, alinea, hero}.
8. **K7.** A bug after results: fix it, re-run everything affected with the same seeds, log both outcomes, and decide on the fixed run. Any change of setting or threshold after data is a new version, committed first, with both outcomes in the ledger.
9. **K8.** Outcome labels are only KILL and NO-KILL (including INVALID); never GO. No screen value is cited as evidence of headroom.

## 12. Requirements bound on the gate protocol (committed with the screen; each one the KILL relies on)

- **R-PS1 (optional, recommended).** The gate's low-drop variant is checked by a pre-registered capacity probe in the plant: an isolated head with a ramped demand, measuring Q_free/Q_dis. Its structural head drop must be ≤ δ_cap (default 1 %). Without it, variant L uses the measured-r rule, and power may collapse at B1.
- **R-PS2 (J pinned).**
  - Door-to-door delay per vehicle against each cell's free-flow time.
  - Origin and ramp queues counted.
  - 05:00 to the end of the drain.
  - Censoring as gate §5.
- **R-PS3 (B).**
  - The gate's B list ⊇ {const with off, tod_cnt, alinea, hero, mtfc_rm}, with identical definitions.
  - Station locations per R13(b); HERO clusters per R13(c).
  - Sensing noise ≤ σ; update period ≤ 60 s.
  - Grids ⊇ the screen's; tuning days ≥ 11.
  - nc nested in const.
- **R-PS4 (I).**
  - The gate's I ∈ {I_plan, I_hero, I_mpc}, exactly as defined in the screen protocol, including the mappings and the I_mpc model-fit procedure. No stronger I may be added later.
  - I is blind to c (R3(c)).
  - max_wait 240 s (R1(b)) and the side constraints apply to I.
- **R-PS5 (decided now, never after the screen).**
  - T2 uses I* (min over all informed arms), or becomes report-only.
  - T1's "control matters" clause becomes report-only or I-vs-nc.
- **R-PS6 (bound, D4.7).** R4(d) and R2(c) carry over unchanged to v4 and the gate. The joint low-drop-with-zero-uplift conjunct is optional (A2 below).
- **R-PS7.** The above-capacity-day rule is identical to §9.
- **R-PS8.** The gate's GO cells exclude D2.2.2 surprise events; those are a reported sensitivity or DRL test. Otherwise the screen must add a matching layer before it runs.
- **R-PS9.** The gate's statistic and looks are those of gate draft §4 (median over 14-day Wednesday sequences, B re-selected, two looks at 97.5 %).
- **R-PS10.** VSL areas = the R6 areas; α_0 = 0.1 primary.

If any binding is later relaxed, a dated addendum must state that a past KILL lost the corresponding step.

## 13. Compute and one-week build (all [estimate], unmeasured)

**Build, after the protocol commit:**

| Day | Work |
|---|---|
| D1 | CTM-2C and unit tests: conservation with queues, FIFO, switch hysteresis, override, VSL forms, Courant assertion, the LP accepting fixed trajectories |
| D2 | Mode-C inputs (P0, R2 uplift, λ); EA-2 event layer and C4 on CTM station series (reusing `metanet_events` and `metanet_facts`); drop ladder; realism floor; calibration-day assertion |
| D3 | B arms (HERO is new; MTFC exists) with the sensing model; batched cross-fit tuning |
| D4 | I_plan and I_hero mappings; LP builder (scipy 1.18.1 HiGHS, in venv314); I_mpc fit procedure; LP-MPC |
| D5 | Statistics (sequences, re-selection bootstrap, robust UCL, LOO); runner under `vsl_lab/ops/guard.py`; ledger rows; V1–V6; throw-away timing. Then the checkpoint code review (High effort, ultracode on) |
| D6 | Runs and report |

- Protocol writing and review come first: about 1.5–2 days (Extra High effort, ultracode on for the review).
- This is tight. The three source designs estimated 1.5–3 weeks; the saving comes from the cuts listed in §0.

**Data-free inclusion rule, applied on the throw-away day only and logged before any calibration-day run:**
- `I_mpc_exact` and `LP-OC` are included if the projected total wall time is ≤ 24 h;
- J_LB is included if the full-day LP solves in ≤ 30 min and ≤ 8 GB.

Dropping an extra informed candidate only makes a KILL easier while keeping F1, since the gate-defined arms are always included.

**Compute:**

| Item | Estimate |
|---|---|
| B tuning (8 configurations; batched CTM, on the order of 10^5–10^6 day-runs) | ~2–10 CPU-h |
| I_mpc and I_mpc_exact (~1,408 units per pair of variants, × 2 configurations × 216 LP solves × 0.2–1 s) | ~35–170 CPU-h, i.e. ~1–6 h wall on 32 workers |
| LP-OC | ~4–24 CPU-h |
| J_LB (optional; 352 LPs, memory-bound) | ~1–12 h wall |
| Bootstrap | minutes |

- Expected total: under one day of wall time. A NO-KILL with early exit should take hours.
- Before every batch: a resource check, the v6-idle check, and the CPU and thermal guard. One ledger row per batch.
- Raw output goes under `/home/catalin/work/phd/vsl_lab_runs/day_pattern/prize_screen/`.

## 14. Power (judgement estimates; nothing simulated)

**P(KILL | gate's true H ≤ 3 %):**

| Setting | Estimate |
|---|---|
| Variant L with R-PS1 bound | ~0.3–0.6 |
| Variant L on the measured-r rule | ~0.1–0.4 (low if B1's r(δ) is flat and δ_L,1 reaches the 15 % fallback) |
| Variant Z alone | ~0.05–0.25 |
| Overall, with R4(d), R2(c) and R-PS1 bound | ~0.3–0.6 |
| Overall, without R-PS1 | ~0.15–0.45 |
| Only variant P | < 0.15 |

**Basis:**
- small low-drop prize;
- max_wait 240 s and small storage (PS-C's arithmetic: about 15–25 vehicles per ramp at × 1.25, [VERIFY] unit);
- offset by the ideal VSL caps of I*, the λ extremes, the secondary-on branch, the 32 UCLs per variant and a robust UCL about 1.5–3 pp above the point estimate (assumed day-level SD of 3–6 %).

**False KILL:** ≤ 2.5 % nominal within the screen plant. Cross-plant risk is not quantified.

## 15. Disclosures

- **D4.4 post-stop design inputs used** (each taken after seeing v3 calibration-day model output):
  - the time-step stability lesson (the T rule plus step-halving);
  - the B1 speed–density artefact (explicit head capacities; the event layer read through the observation operator);
  - the B2 knife edge (spread branch; B2 occurrence report-only in V2);
  - station cells not capacity-scaled;
  - relocation at E15 (the secondary-head branch).
- F11 floors L_r,k are real-data summaries of validation days. No model has been run on any validation day. They are used only in variant Z's drop rule.
- The 22 calibration days were already used for the v3 fit and the post-stop diagnostics. The screen fits only on them: drop rungs, s, secondary-head κ, B tuning and the I mappings, all by pre-registered rules.
- The throw-away input is a synthetic median day.
- The gate draft is untracked; the screen protocol restates gate §3–§6 as used.
- The source designs and judgements came from a multi-agent workflow. This outline is a design; its numbers are estimates.
- Literature anchors are [VERIFY].
- The PS-A field envelope and the v3 cross-structure check are not run.

## 16. Where it is not conservative (stated in every KILL record)

- **First-order plant.** It has no waves, no anticipation, no METANET merge (δ_m) or lane-drop (φ) speed terms at E13, E14 and km 2.39, and no transient flows above static capacity. Feedback, for example ALINEA, HERO or MTFC, may work worse in METANET than in CTM-2C, and wave-based VSL (SPECIALIST) is unbounded.
- **Drop map.** The screen's r(δ) map may differ from v4's, unless R-PS1 is bound. Monotonicity of H in δ is an inference.
- **Background delay.** Speed–density delay may be controllable in v4 (a ≈ 1 in v3 G2).
- **Grid points only.** Effects that are not monotone between grid points (λ, spread, κ) are not covered. The spread is i.i.d. uniform per head; v4's F̂ may be correlated or shaped differently.
- **Days.** 2023 Wednesdays only, all heavy at B1. There are no light days, and the gate's real 2024 days may hold more transition-band days (thesis path §5.3).
- **Demand.** True I-494 demand is unobservable (served flows are capped; about 38 % of PM inflow between Valley View Rd and Pioneer Tr enters there, protocol v3 §3.3.3). The boundary is clipped by the I-394 queue (F13). Controlled-ramp demand rests on P0.
- **Statistics.** n = 22 clusters; undercoverage is mitigated, not removed.
- **B tuning parity and the median-form monotonicity** (A1).
- **I_mpc cross-plant strength** (A4).
- **Bindings.** If any R-PS item is relaxed later, the corresponding step is lost.
- **Storage unit.** If IRIS storage is not in feet, storage and pre-metering authority change [VERIFY].

## 17. What each outcome implies

- **KILL:**
  - the day-pattern DRL route stops before any METANET v4 compute (D4.2);
  - the result is ledgered and the author is informed;
  - what follows was decided before the run (author item: the D1 supervised fallback, H2, or another track);
  - only positive DRL results count, so it is not written up as a result paper.
- **NO-KILL** (including INVALID and early exit):
  - METANET v4 is written as the gate plant (D4.2), with P6b unchanged and SUMO as the confirmation plant;
  - the SUMO S0 merge pre-check should be pre-registered;
  - the R-PS bindings stay in the gate protocol;
  - the CTM-2C plant, B arms, LP-MPC and statistics code carry over (the gate's CTM model family for mpc_f, and the fallback cross-check);
  - the screen's r(δ) map and diagnostics may be used as disclosed design input for v4's R4 construction;
  - NO-KILL says nothing about a GO.

