# Shared rules for the #1/#2 kill tests

Draft v1, 2026-10-16; **not binding** until approved (box at the end; recorded as V80–V82, with protocol #1 as V83 and protocol #2 as V84). Sources: `docs/research/development_plan_v0.md` (titled "plan v2"; its "Main-session check" wins), `docs/decisions.md` V1–V79, `CLAUDE.md`. Values are set only in the table. Each protocol sets its units, block lengths, gate thresholds, metric formulas and the gates with their own confidence-interval (CI) rule. It may tighten these rules, never relax them, except for the protocol-specific rules listed in §5, which are approved with these rules (item S7).

## 1. Claim rule (replaces D5.8 for #1/#2; plan §5)

- **Terms.**
  - *Online-adaptive algorithm:* a run-time parameter update with a stated rule (#1: b̂, the leader's assumed maximum braking, m/s²; #2: the commit margin m, s). It has a cited guarantee only where the assumptions hold (§9); otherwise "empirical validity only (A1)".
  - *Cell* (gated cell): the unit in which A1 or a gate is judged: one regime at one evaluation site (#1); one regime (weekday or weekend) pooled over signal groups (#2; group × regime cells are report-only, except in #2's K2); or a pooled cell (§5). Protocol #2 also uses "cell" for its tracker unit (group × program).
  - α: target share of 8-s windows with a miss (#1). ε: target share of approaches with a forecast that end in a loss, a broken commitment (#2). δ: the tolerance. J: the number of gated cells of a gate (for Bonferroni).
  - *Placebo:* the online method with its timing destroyed (#1: the tracker run on permuted windows; #2: the online margins permuted within group × program × regime). *Hindsight arm:* the per-regime threshold or margin fitted on the evaluation data (non-causal; headroom and G only).
  - *Named opponent:* the strongest static arm, fixed in each protocol (#1: O2; #2: O4). *Best opponent:* the A1-valid opponent with the best median in the cell, chosen on evaluation data (this selection step favours the opponent).
  - Not opponents: the references (recorded human; IDM, the Intelligent Driver Model; default RSS, Responsibility-Sensitive Safety; nominal ACC, adaptive cruise control), the rolling-window arm (N1; in #1 also K4) and the hindsight arm.
  - K gates can KILL; N gates only narrow a GO. Both are set in each protocol (#1: K0–K4 and N1; #2: K1–K3 and N1).
- **Rule A ("valid and not wasteful")**, judged on confirmatory data:
  - **A1:** in every A1 cell (held-out site or period), the rate bound (table) is ≤ α + δ (#2: ε + δ). The same bound holds for all arms, and filters the kill tests (§5).
  - **A2:** in ≥ 1 cell the online method beats (§5) every A1-valid opponent, offline or online, and the placebo. **Harm limit:** in every cell, the online median must not be clearly worse than the best opponent's by more than the harm margin. "Clearly" means the whole uncorrected 95 % CI of the difference lies beyond the margin. A cell whose CI upper end exceeds the margin is labelled "harm not excluded" and named in the claim sentence.
  - **A3:** the kill test's headroom gate passed (#1 K0, #2 K1). Confirmatory headroom is reported, not re-tested.
  - The full operating map (arm × cell: validity, win, tie, loss) is always reported.
- **Adaptation share** G = (fixed − online)/(fixed − hindsight), "fixed" = the named opponent. Report-only in the claim; shown only when fixed − hindsight reaches the G floor. A protocol may use G as an extra kill-test leg (#2 K3). G and the secondary α/ε levels never make a paper or a chapter, and never turn a failed gate into a pass.
- **D5.8 is dropped** (it never tests validity), and so is **DRL** (deep reinforcement learning), with disclosure: "no DRL arm was run; D5.8 was replaced by rule A, V80".
- V80 (with the supervisor's view) is final before any confirmatory data; kill tests need not wait. A change to rule A after any kill-test outcome may only tighten it, and is logged as made after seeing throw-away results.

## 2. Null rule (plan item S2)

Only a positive rule-A result becomes a paper. A **KILL** gives no paper: a decision entry, then the author re-plans; the bar stays. A1 passes but A2 fails: a thesis chapter. STOP or INCONCLUSIVE: no claim either way. This replaces the 2026-10-05 DRL-only rule (memory notes, never in `docs/decisions.md`).

## 3. Metrics (plan item S4; replaces CLAUDE.md's freeway metrics for #1/#2)

- **Co-primary, always together:** the validity rate (misses per window, #1; losses per approach with a forecast, #2) and efficiency (required time gap in s, #1; fuel per approach in mL for the combustion car, which decides, with the electric car's energy in Wh in every table, #2). **Secondary:** capacity (#1); travel time (#1: confirmatory only; #2: also a guard).
- **Guards.** A collision (#1, closed loop only) or a red crossing (#2) is a bug check: scoring stops for a bug review (§6). Travel time (#2): an arm fails in a cell if the 95 % CI upper end of its paired median change vs IDM-1 (protocol #2) is above the travel-time limit. That counts as failing A2 there; in a kill test the cell cannot pass an efficiency gate. Protocol #2's kill test uses its own travel-time rule (§5, protocol-specific rules). Hard brakes: report-only until the author sets V25's tolerance.
- **Never a reference alone:** it stands next to the named opponent and the placebo. Every arm, ours included, is fitted by its protocol's rule on the throw-away fitting data only; no arm gets an extra search. References are not tuned.

## 4. Seeds and data roles (each data block is evaluated once; plan item S3)

- **7,400,000–7,419,999 stays untouched** (CLAUDE.md, V62): reserved for F3Z P0–P2 (V66; on hold, V77), not relabelled.
- **New block 7,420,000–7,429,999** (unused in v5b1 docs and in the v6 handoff, which uses 8,000,000–8,099,999): #1 uses 7,420,000–7,420,999 and #2 uses 7,421,000–7,421,999. A kill test takes every random draw (bootstrap, placebo, arrivals, group draw) from the named seeds and streams that its protocol lists before data (#1 §9; #2 Annex A). A bug-fix re-run reuses these seeds. The confirmatory protocol names its seeds from the rest of the block (#1 reserves 7,420,200–7,420,499).
- **Roles** (fresh seeds give no fresh recordings):
  - **throw-away** (fitting, tuning, kill test; disclosed): #1 all 90 min of NGSIM I-80 and US-101; #2 local dates 13–24 Sep 2023 (kill evaluation 18–24 Sep);
  - **INCONCLUSIVE re-run:** one block, named in each protocol before data (#1: TGSIM I-294 L2, also the STOP fallback; #2: none, so an INCONCLUSIVE #2 leads to a re-plan);
  - **confirmatory:** #1 TGSIM (later highD/exiD, I-24 MOTION); #2 25 Sep 2023 to the archive end, 20 % of intersections held out, plus the live recording.
- Throw-away data may later be reused for fitting only. A protocol change after a look needs new data.

## 5. Statistics

- **Effect:** the median of paired differences over the protocol's pairing unit: #1 the window; #2 the signal group, with the effect in % = 100·(E_opponent − E_online)/E_opponent per group (E = the group's total combustion-car fuel over the regime's scored approaches). Never use a unit where most paired differences are exactly zero; report the share of tied units for each pair of arms. Miss and loss rates are compared as rates with their own bounds, never as medians of 0/1 differences.
- **CI:** percentile bootstrap over blocks or clusters (unit set per protocol; no block crosses a recording period), with B replicates (table). Each replicate refits the arms fitted on resampled data, including the hindsight arm when a CI uses it (a block-local one, #1 Href, moves with its block), and, in confirmation, redoes the best-opponent choice among the arms that passed A1 on the full data. #2 CIs are labelled "conditional on the 7 evaluation days". The verdict uses the §4 streams; other seeds are reported Monte Carlo checks only. The placebo's spread over its seeds is reported (#1: its 20 permutations); further placebo seeds are sensitivity only (#2: confirmatory).
- **Outcome-free count** (stage 1, §6): windows, approaches, blocks, cell covariates. Before any outcome it fixes the gated cells (at least the minimum blocks; the rest report-only), J for each gate, and the validity power. Validity power: for each A1 cell, the binomial chance that an arm whose true rate is exactly α (ε) passes A1 (design effect stated as an ASSUMPTION). Where A1 must hold in every cell (confirmation; #2's GO), cells are pooled until the product of these chances reaches the validity-power target (#2 default: regimes pooled over groups; group × regime cells, 2–5 days, report-only). In #1's kill test, A1 binds only in the cell where the online arm wins, so the per-cell chance is reported and no cells are pooled. A cell with fewer expected misses (losses) than the minimum is "validity not tested": reported with its bound and named in the claim sentence. Confirmatory power checks assume an effect equal to the gate threshold, never a kill-test estimate.
- **Multiplicity:** "in ≥ 1 cell" uses Bonferroni over the J gated cells. "In every cell" and "beats every opponent" need none. #1 and #2 are separate families.
- **Beats:** paired median ≥ the beats floor and Bonferroni lower bound > 0, with the online arm passing A1 in that cell. In the claim, a cell where no opponent passes A1 gives no efficiency win; it is reported as "validity-only" (kill tests: the protocol's rule, listed below). Opponents removed by the A1 filter are listed with their bounds. The matched-rate comparison stays a sensitivity row (confirmatory).
- **Gates.** A K gate passes if ≥ 1 gated cell meets its rule, unless its protocol says "every gated cell"; otherwise it fires. A gate with no gated cell is a STOP, never a pass or a KILL. A cell passes an efficiency gate only if the online arm passes A1 there. Own CI rules stay, but no validity band has an upper edge looser than A1's: a static arm fails transfer in a cell if its CI lies wholly above α + δ or wholly below α/2 (#2: ε). K2 KILLs only if every gated cell's CI lies wholly inside [α/2, α + δ] (#2: ε); the protocols' K2 rows use these bands (#2 counts a share of cells, below).
- **Decisive firing.** A fired gate is a KILL only if the data exclude its pass condition. Threshold gate: the uncorrected 95 % CI upper end of the effect is below the threshold in every gated cell. CI-rule or validity gate: the CI lies wholly outside the pass region (online validity filter: its 95 % lower bound is above α + δ, #2: ε + δ). Otherwise the gate is undecided. The protocols apply this with the protocol-specific rules below.
- **Outcome, first match wins:**
  1. **STOP:** a precondition fails (integrity, quality control, counts, a gate with no gated cell, a start-gate unit test, a pre-data power check where the protocol has one); stage 1 only. A STOP says nothing about the idea; next comes the protocol's fallback block if it names one (#1), otherwise the author re-plans.
  2. **KILL:** a gate fires decisively.
  3. **INCONCLUSIVE:** no decisive firing, at least one gate undecided. One re-run on the named block, analysed alone or pooled with the first run as each protocol states before data (pooled: the significance level is split over two looks). Its GO or KILL is final, reported as "at the second look". A second INCONCLUSIVE, or an unavailable block (for example, licence, or no block named, #2), means the author re-plans.
  4. **GO:** no gate fires. The claim stays broad only if the online arm beats the rolling-window arm where it won (kill test: the cells where K3 passed; claim: the cells where A2 passed); otherwise N1 narrows it. Each protocol states its N1 rule.
- **Protocol-specific rules** (approved with these rules, item S7; each protocol names them too):
  - **#1:** (a) a fired gate is a KILL only if it fires decisively **and** is not underpowered in every gated cell (the stage-1 power table; plan §2's INCONCLUSIVE rule); (b) O3 enters K3 with 16 blocks (P2–P3) if U9 passes at 16 clusters, otherwise it is report-only; (c) in the kill test, A1 cells are not pooled (above), and offline opponents leave K0 and K3 only if significantly invalid (protocol #1 §10).
  - **#2:** (a) K1, the K3 legs (G included), N1 and the travel-time guard use point estimates (travel time: C's total over IDM-1's ≤ 1.02, with its 95 % CI reported), while GO's "beats" and harm legs and A1 use the CI rules above; (b) instead of the decisive-firing test, K1–K3 KILL on their own rules, a pre-data power check (half-width > HW_max) is a STOP, and the remaining runs are INCONCLUSIVE or KILL by protocol #2 §11 rules 6–7 (INCONCLUSIVE needs every comparison that fails its GO condition to have a half-width above HW_max); (c) K2 KILLs if fewer than θ_K2 of group × regime cells show drift; (d) if no opponent passes A1 in a regime, C must still beat O4 there.

## 6. Ledger and run-once

- Before the protocol commit, code sees only synthetic data and the §8 probes (downloads, MD5 and row counts may run). The commit hash enters the ledger **before any data are read**. Each kill test then runs once, in two stages. Stage 1 computes only the outcome-free count and the STOP checks and logs them (commit hash, time); in #2 these are the steps before the freeze tag (protocol #2 §12). Stage 2 computes the gate statistics only if stage 1 passed; once it starts, no STOP can be declared.
- Ledger (port of `vsl_lab/ops/ledger.py`, `claude/day-pattern-core` 8eb0343): protocol and code hash, data MD5, seed, arm, cell, outcome. Every run is logged. The runner refuses a dirty tree or a missing protocol hash.
- **Re-runs, three kinds only.** (i) Operations failure: re-run once; the failed run is logged, not scored. (ii) Bug fix: the corrected run's verdict replaces the first; both are logged and reported. A bug (code that disagrees with the protocol, not a method change) counts only if a unit test derived from the protocol text fails on the old code and is committed before the corrected run, which reuses the same seeds. The same post-run checks run after every outcome, GO or KILL. (iii) The INCONCLUSIVE re-run. No other re-run changes a verdict.

## 7. Operations

- Before every run, check CPU (`/proc/stat`), RAM, disk, and that v6 is idle (if unknown, the load limit). Launch only below the CPU limits (night = Focus mode "sleeping"). Never touch fans, the cooling pad or power settings.
- Downloads, the Hamburg filter and the live recorder run in `systemd-run --user` units at low priority. A single-process kill test needs no CPU guard (plan item S5); the guard is ported before any multi-process batch.
- The Hamburg zip and its filtered files live on /srv/shared (~203 GB free). NGSIM (~1.5 GB) goes to `/home/catalin/work/phd/v5b1_data/ngsim` (plan §2; / has 13 GB free), and runs go under `/home/catalin/work/phd/`. The Hamburg zip is streamed, never extracted. The repo gets summaries only.

## 8. Disclosures (copy into each protocol)

- Agents read, for format and latency structure only: an NGSIM 100 MB export prefix, with format-only counts, and 20,000 rows of each of three TGSIM sets (details and MD5s: protocol #1 disclosure); the Hamburg zip listing and first ~100 MB (13 Sep 2023 afternoon, inside the throw-away block), where back-filled mqtt=f rows arrived ~295 s late (details: protocol #2 §2). The latency model's structure was chosen after seeing this; its lag is fitted on throw-away days only and is used only in the confirmatory latency case.
- No outcome statistic (score, gap, miss or loss rate, signal timing, energy) was computed on real data; plan rates and window counts are synthetic.

## 9. Guarantees

1. Kill tests claim no guarantee. Own derivations (plan F2; the delayed conformal decision theory (CDT) bound) are checks only (unit tests, synthetic adversarial runs), never results.
2. A guarantee sentence is written only in a confirmatory protocol, after the full text of the cited result is read. Sources: #1 delayed adaptive conformal inference (ACI), El Halabi & Brandt (2026), arXiv 2609.07251v1 (abstract and §4.3 Eq. (11) read; the rest [VERIFY]; protocol #1 §4 finds that Eq. (11) does not transfer to the kill test's fleet tracker); #1 no delay, Angelopoulos, Candès & Tibshirani (2023), arXiv 2307.16895, Prop. 1; #2, Lekeufack et al. (2023), arXiv 2310.05921, Thm 1, with no outcome pending at a cell's next decision (asserted in the run).
3. Check before citing: delay in steps (theirs) vs in time and variable (ours); ACI's level scale vs our score-scale tracking; the lower clip; batched outcomes; per-regime subsequences. If one fails, claim only empirical validity (A1). Cite only finite-sample bounds.
4. Each guarantee sentence is one-sided (miss or loss share ≤ target + slack; with the lower clip, waste is not bounded). It gives the numerical slack for the actual T_r (outcomes applied in cell r) and lag, and says "claimed" only if slack ≤ δ, else "asymptotic only". It holds only for the replayed, open-loop sequence, never for single windows, other sites or collisions. A1 is always an empirical result. No "first" or "novel".

## 10. Timing

(a) Author: 0.25–0.5 h to read these rules (estimate), inside the "Decisions" rows of both protocols' time tables (0.5–1 h each); (b) Claude: inside the plan's build estimates; (c) machine: seconds.

## Constants and defaults

| Item | Value | Source |
|---|---|---|
| α (#1), misses per 8-s window | 0.02 (0.01 secondary: confirmatory, report-only) | plan D2 |
| ε (#2), losses per approach with a forecast | 0.05 (0.02 secondary: confirmatory, report-only) | plan E3 |
| δ, validity tolerance | α/2 (#1); ε/2 (#2) | plan D2, E3 |
| Rate bound (A1) | one-sided 95 % upper bound, all arms, kill tests and confirmation; the larger of the block-bootstrap and Clopper–Pearson bounds | plan §5; Claude |
| Harm margin (A2) | 5 % of the best opponent's median (kill tests: of each opponent in the protocol's set) | plan §5 |
| Beats floor (= the test's K3 threshold) | 0.1 s (#1); 1 % (#2) | plan D4, E5 |
| G floor (fixed − hindsight) | 0.1 s (#1); 1 % (#2) | plan §5 |
| CI | 95 % percentile bootstrap; Bonferroni level 1 − 0.05/J | CLAUDE.md |
| Bootstrap replicates B | 10,000, or 2,000·J if larger (≥ 50 replicates beyond each Bonferroni endpoint) | Claude |
| Dependence unit | #1: 112.5-s blocks inside a nominal 15-min period; #2: signal groups (all their days in the regime) | plan annex; protocols |
| Minimum blocks (clusters) per gated cell | 20 (#2: 20 groups); #1's O3 comparison: 16 (§5 protocol-specific rules) | plan |
| Minimum expected misses (losses) per A1 cell | 20 | Claude |
| Validity-power target (product over A1 cells) | ≥ 0.80 | Claude |
| Placebo seeds | #1: 20 permutation seeds, spread reported; #2: one permutation (further seeds: confirmatory) | protocols |
| Gate rule | ≥ 1 gated cell: median ≥ threshold and Bonferroni lower bound > 0 (default; a gate may have its own CI rule) | Claude, after CLAUDE.md headroom rule |
| KILL | decisive firing (§5); #1 also not underpowered; #2 its listed rule | Claude; plan §2 |
| Outcome precedence | STOP > KILL > INCONCLUSIVE > GO | Claude |
| Travel-time limit (#2) | +2 % vs IDM-1: 95 % CI upper end (default, confirmation); point estimate in #2's kill test (§5 protocol-specific rules) | V37 |
| Hard brake | > 3 m/s²; report-only until V25's tolerance is set | V36; V25 |
| Seeds | #1 7,420,000–7,420,999 (protocol #1 §9; re-run 7,420,100–7,420,199); #2 7,421,000–7,421,999 (protocol #2 Annex A; no re-run); unit tests 0–9,999 | Claude |
| CPU | < 90 % by day; < 70 % at night; v6 idle or load < 15 % | CLAUDE.md; author 2026-10-15 |
| Priority; repo files | `nice -n 19`; < 5 MB | plan; CLAUDE.md |

> **Pending author approval (defaults).** Reply **"accept defaults"** to approve S1–S7 below, protocol #1 §15 (D1, D2) and protocol #2 §16 (E1–E5). Claude records them as V80–V84 and commits the same turn.
> - **S1 (V80) Claim rule for #1/#2:** rule A replaces D5.8; DRL dropped, with disclosure (§1). Supervisor check in parallel.
> - **S2 (V80) Null rule:** a KILL gives no paper; A1 pass with A2 fail = a thesis chapter (§2).
> - **S3 (V81) Seeds and data roles:** block 7,420,000–7,429,999 and the roles of §4.
> - **S4 (V81) Metrics:** §3 replaces CLAUDE.md's freeway metrics for #1/#2.
> - **S5 (V81) No CPU guard** for a single-process kill test (§7). With S3 and S4, "accept defaults" also approves a short "Exceptions for #1/#2" section in CLAUDE.md that points to this file; the diff is shown in the same commit.
> - **S6 (V82) Confirm:** you have never analysed NGSIM I-80/US-101 or the Hamburg 2023 signal archive. "Accept defaults" means "confirmed"; otherwise name what you saw.
> - **S7 (V80) Statistics and outcome classes (§5)**, including the protocol-specific rules listed there: Claude's technical defaults (plan §6 annex), disclosed and changeable only before data.
> - V83 records protocol #1 and V84 protocol #2, each with its file's sha256.
>
> **Not covered by "accept defaults"** (only the author can do these; none blocks the NGSIM or Hamburg kill runs): the TGSIM licence query and the highD/exiD access request (emails); starting the live Hamburg recording; deleting the ~205 MB of probe files in the session scratchpad `wf3/`.
