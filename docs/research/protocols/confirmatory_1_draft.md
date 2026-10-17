# Confirmatory protocol #1: self-calibrating safety margin on unread TGSIM data

Body: 1,498 words, without the title, this line, Markdown list and heading markers, and the constants table (plain `wc -w` of the same text: 1,588).

Fixed on 2026-10-16, before any trajectory row of the three confirmatory sets is read, except the disclosed L1 probe (§7). It binds once the author approves it in a V entry that records this file's hash. Later changes are dated addenda that never relax a rule. Other rules: `screen_1b.md`, `v5b/screen1b.py` (commit `ca48b58`).

## 1. Claim

As in the screens: open-loop replay behind real recorded leaders, scoring only the leader's braking against the assumed limit b̂ (m/s²); a miss is not a crash.

- **Rule A (V83),** tested against the transferred margin F, the freeze rival W and the shuffled placebo P (item 2):
  - **A1:** the online margin O is A1-valid (§4) in every gated cell;
  - **A2:** O wins (§5) in at least one gated cell and is clearly worse in none.
- **Always reported:**
  - the operating map (miss share, bound and mean gap per arm × cell);
  - E(H, F) and E(H, W);
  - E(O, F)/E(H, F), where F is A1-valid and E(H, F) ≥ 3 %.
- **Scope:** TGSIM only. No closed-loop, collision, guarantee or DRL claim (V83).

## 2. Data

- **Fitting** (F and c only): screen #1b's I-90/I-94 Stationary (`9uas-hf8b`) and I-395 (`97n2-kuqi`), pooled.
- **Confirmatory sets,** each read once:
  - **I-294 L1 (`7zjf-a4zf`):** a new road; the only source of a "between freeways" sentence.
  - **I-294 L2 (`tpsq-zrwa`):** report-only in every regime, fixed now (speed always ≥ 14.75 m/s).
  - **I-90/I-94 Moving (`6a6e-vfvi`):** Stationary's freeway, recorded on 27 May 2022 (Stationary: 6 Oct 2021; report p. 28). Its segment probably contains Stationary's [VERIFY].
- **Collection mode** differs (fixed views versus a following helicopter). Part of the difference between sites may come from processing, so sentences say "recordings".
- **Unit** = dataset × direction (on I-294, negative `lane_kf` is the other direction).
- **Cell** = dataset × regime. Gating: constants table (R1 or R2 only, as in the screens).
- **Processing** as in #1b, all lanes. Every L1 row is kept, including the 20,000 seen earlier (§7).
- **Test vehicles** (constants table) stay in leader matching, but their own windows are not scored (item 1).

## 3. Arms

Every arm uses the gap d = d_safe(b̂, v) + s0, the floor and the quantile rank (constants table). Windows are ordered by run, start, then vehicle id.

- **F:** per regime, the quantile of all fitting windows.
- **W ("calibrate briefly, then freeze"):** per unit × regime, the quantile of its first 300 windows, frozen once their outcomes are known. W = F if there are ≤ 300 windows.
- **Comparison windows:** per unit × regime, the windows that start after W froze (all windows, if W = F). Every arm is judged on them. O's A1 must also hold on all windows; this checks O's start-up after a wrong F.
- **O:** per unit × regime, starting from q = F. Each second:
  - q ← max(1, q + (η/c) · Σ(1{s > q_used} − α)), summed over the outcomes that became known in that second (constants table);
  - no update if there are none.
- **P:** O's rule, fed the same windows in shuffled order (constants table).
- **H:** per cell, the quantile of the comparison windows (hindsight; headroom only).

**Main changes from the screens** (tagged in the constants table):
1. c is #1b's c_r at the 90th percentile, not the median. A fixed step per window holds the per-window miss share at α. A per-second mean does not when busy seconds brake harder. The fixed step also overshoots less in large batches.
2. The floor covers every arm and stays at 1 m/s², although it bound in DC R2 (hindsight 0.57). Lowering it would tune O on that result. Unfloored rows are reported.

## 4. Metrics

- **A1-valid** (a miss is s > b̂): the larger of the one-sided 95 % block-bootstrap and Clopper–Pearson upper bounds is ≤ 0.075.
- **Clearly invalid:** the lower ends of both two-sided (1 − 0.05/J) intervals are > 0.075.
- **Efficiency:** E(X, Y) = 1 − mean(d_X)/mean(d_Y), paired on comparison windows.

## 5. Statistics

- **Stage 1 (no scores):**
  - check row counts against the metadata (L1 1,024,281; L2 137,928; Moving 1,784,748);
  - count windows and blocks;
  - fix and log c, the gated cells, J (their number) and the power below. The power figure never stops the run.
- **Stage 2:** compute scores. A cell with clip share > 5 % becomes report-only (J unchanged).
- **Intervals** (constants table): the same bootstrap draws for all arms. Thresholds stay fixed in every resample, so the CI ignores the luck of W's 300 calibration windows (disclosed).
- **O beats X:** E(O, X) ≥ 3 %, and the lower end of its two-sided (1 − 0.05/J) CI is > 0.
- **Win** in a cell: O is A1-valid and beats P, and F and W are each clearly invalid or beaten. P's validity does not count, because its misses are means over permutations.
- **Clearly worse:** compare O with the A1-valid opponent in {F, W} that has the smallest mean gap. O is clearly worse if the whole uncorrected 95 % CI of E lies below −5 %. If only part of it does, the cell is named "harm not excluded".
- **Accepted risk:** a threshold at the true 95 % quantile passes A1 in a 1,000-window cell with probability 0.71–0.78 (10–40 blocks; design effect 2, assumed). Passing in all four cells: 0.26–0.37 (cells assumed independent).

## 6. Outcomes (first match wins)

1. **STOP-data** (Stage 1 only): row counts differ, or no cell is gated. No sentence. Re-plan with the Stage 1 counts disclosed; no addendum adds cells.
2. **KILL:** O clearly invalid in a gated cell (either window set). No sentence, no paper; decision entry.
3. **INCONCLUSIVE:** O not A1-valid in some gated cell, or clipping left no gated cell. No sentence and no re-run (no unread TGSIM freeway set remains).
4. **VALID-ONLY:** A1 passes; A2 fails. Thesis chapter only: "valid in every gated regime; no win was shown". Add "clearly more wasteful in <cells>" where O was clearly worse.
5. **PASS, new road:** rule A passes with a win on L1. Allowed sentence: "On recordings of a freeway it was not fitted on, the self-calibrating margin kept misses within the 7.5 % limit (target 5 %) in every gated regime. Its gaps were at least x % [CI] shorter than those of the transferred margin, a margin fitted on the road's first 300 windows, and its shuffled placebo, except where the first two clearly broke that limit." x = the smallest E(O, X) among the "beats" in winning cells.
6. **PASS, same road:** all wins are on Moving. The same sentence, but "on the same freeway on another day".

Every sentence names the floor-bound, "harm not excluded" and report-only cells, and the collection mode. Only a PASS becomes a paper (ITSC 2027).

## 7. Integrity

- **Code and tests are committed before the download.** Both stages run that commit unchanged.
- **Synthetic tests:** #1b's 13 (adapted), plus one per new rule. These include:
  - heavier scores in busy seconds;
  - the order-statistic quantile (not numpy's default);
  - O carried across runs;
  - Stage 1 unchanged when scores are shuffled.
- **Run once,** niced, in a `systemd-run --user` unit after a resource check; fans untouched.
- **A later bug** (code that disagrees with this text, never a method change):
  - fix it, and add a test that fails on the old code;
  - re-run with the same seeds;
  - the corrected run decides, and both runs are reported.
- **Records:** the result and the ledger record the protocol hash, commit, CSV MD5s (at download), row counts, seeds and outputs.
- **Disclosures:**
  1. The screens' results were seen. W, §3's changes, the gate sizes and item 2's alternative respond to them. The tracker rule was picked in synthetic runs, some shaped like #1b: per-second-mean variants failed when busy seconds braked harder, and running-count variants did about as well (scripts committed).
  2. Seen for the confirmatory sets: the Socrata metadata (rows per run, lane and time value; ranges; nulls), the data dictionaries, and the whole FHWA-JPO-24-133 report, text-extracted by agents. Which pages were read was not logged. Ch. 4 of the report calibrates L1 test vehicles and gives braking values. No score was computed.
  3. Earlier agents downloaded 20,000 L1 rows (MD5 a9f2f0c1249446350e99aafe2bd07212). They report no statistics, but what they printed was not logged, and they deleted the file. At download, the export's first 20,000 rows are MD5-checked against this file. On a match, a sensitivity row drops those (run, id) pairs.
  4. [VERIFY]: chronological `run_index` order; Moving's segment; whether `speed_kf` is two-sided (constants table); licence (none stated; rights "public").
- **Timing (estimates):**
  - (a) author: about 0.5 h;
  - (b) Claude build and verify: 1–2 h;
  - (c) download (about 210 MB): minutes; compute: 10–30 min.

## 8. Author items (default applies if unanswered)

1. **Test-vehicle windows.**
   - Default: not scored (cruise-control braking; 5.8 % of L1 rows), with a sensitivity row that scores them.
   - Alternative: score them.
2. **Placebo role.**
   - Default (approved, "3 yes"): every win needs O to beat P.
   - Alternative, only by explicit answer (proposed after #1b's placebo matched O): P leaves the win and the PASS sentence. If rule A passes, a secondary claim, "O beats P in a gated cell" (same J), is tested. The sentence then adds "and it beat its shuffled placebo", or else "tracking over time was not shown (no win over its shuffled placebo)".

## Constants (fixed before data)

| Constant | Value | Source |
|---|---|---|
| α; validity limit | 0.05; 0.075 | screens |
| Window; history; look-ahead; tick | 8 s; 5 s; 2 s; 1 s | screens |
| Score | max over the window and h ∈ {1, 2} s of (v(t) − v(t+h))/h, on the centred 1-s mean of `speed_kf`, clipped to [0, 10] m/s² | screens |
| Regimes | from `speed_kf` in the 5 s before the window. This is the provider's Kalman smoothing, possibly two-sided [VERIFY], so the label may see into the window. R1 min < 2 m/s; R2 mean < 10 m/s; R3 otherwise (report-only) | screens |
| d_safe; s0 | ρ 0.5 s, a_acc 2 m/s², b_min 4 m/s², exact on a 0.01-s grid that ends at the ego's stop time, v = leader speed at window start; 2 m | screens |
| Leader | nearest vehicle ahead in the same run and lane, projected gap 0–150 m | #1b |
| Unit | dataset × direction; O, W and P carried across runs in `run_index` order | new |
| Test vehicles | any row with `acc`/`av` = yes, any case; on I-395, `type_most_common` = 4. Their own windows are not scored at any site, so F is fitted without them | new |
| Outcome known | window end + 2.5 s (the centred mean needs 0.5 s more) | changed (#1b: + 2 s) |
| F | per regime, fitting sites pooled; single-site F report-only | screens, changed |
| O | η 0.5; one update per second; sum / c; starts at F | #1b, changed |
| c | per regime, the 90th percentile of outcomes per non-empty second, fitting sites pooled, counts only | #1b (median), changed |
| Floor | 1 m/s², every arm; report-only rows with floor 0 m/s², all arms | #1b, extended |
| Quantile | ⌈(1 − α)(n + 1)⌉-th smallest | new |
| W | N = 300 per unit × regime; W = F with ≤ 300 windows; report-only: N = 1,000, judged on the windows after its own freeze | new |
| P | O's rule on O's timeline (same update seconds and batch sizes), fed its unit × regime's windows in random order, each window keeping its own score and speed; 20 permutations; per window, gap and miss are means over them, also in the CI; miss bounds by block bootstrap only | drafts, changed |
| Gated cell | R1/R2; ≥ 1,000 comparison windows in ≥ 10 two-minute blocks; clip share ≤ 5 % | screens (300 windows), changed |
| Floor-bound | O at the floor in > 50 % of a cell's windows | new |
| Beats; harm margin | E ≥ 3 %; 5 % | screens; drafts |
| A1 bound | one-sided 95 %, the larger of block bootstrap and Clopper–Pearson | drafts |
| Intervals | bootstrap over 2-min blocks within runs, per cell, B = 10,000. Each interval or bound = estimate ± t(G − 1) · SD_boot · √(G/(G − 1)) at its stated level, G = blocks in that window set. Percentile intervals also reported | screens; drafts; t-scaling new |
| Bonferroni | two-sided 1 − 0.05/J over the J gated cells, used one-sided: the routes "clearly invalid" and "beaten" together spend 0.05/J per cell, and "every opponent" needs no correction. Harm at uncorrected 95 % | drafts |
| Guards (report-only) | longest run of misses per arm; matched-leader share per dataset; excluded windows | new |
| Seeds | 7,420,200 bootstrap; 7,420,201–7,420,220 placebo; approving this protocol approves them | drafts' confirmatory reservation |

---
## Main-session note (2026-10-16): DRAFT, not binding

- **Power check (main session, same formula as the workflow's `power.py`).**
  - Setup: a threshold exactly at its target quantile, design effect 2 (assumed), t-scaled bounds.
  - Pass probability for A1 per cell / in all 4 cells:
    - target 5 %, n = 1,000: 0.71–0.78 / **0.26–0.37**;
    - target 4 %, n = 1,000: 0.96–0.98 / **0.85–0.91**;
    - target 5 %, n = 2,000, G = 20: 0.96 / 0.83.
  - **Proposed author item 0:** every arm aims at α = 0.04 (quantile rank, tracker target), with the 7.5 % validity limit unchanged.
- **Item 2 (placebo role)** must be settled in the approving V entry. The workflow defaulted to the author's literal "3 yes", which conflicts with V83's recorded hierarchy.
