# P1 protocol: how much incident information does metering need?

Status: **APPROVED (V99, 2026-10-19): author decisions A1–A10 = all defaults.** Revised after the design review (design, fairness and feasibility lenses). No tool-check or evaluation seed is run before the code is committed and has passed its code review.

**Paper question.** During non-recurring incidents at a freeway bottleneck, how much of the attainable delay reduction from metering needs incident information, and which information?
- **L0, none:** strong always-on control.
- **L1a, presence and timing:** the controller knows that an incident is on (onset and clearance), not its type.
- **L1b, plus type:** a stored plan per incident type.
- **L2, per-incident information:** a hindsight bound, bracketed (§6 S2; its exact meaning is set by A3).

Also: how robust is the L1b gain to detection imperfections?

**The meter.** BN4's meter is a traffic light across all 4 mainline lanes at node 3; BN4 has no on-ramp (`v5b/d1/netgen_bn4.py`, `v5b/d1/plant.py`). Under A1(a) the paper says "mainline (bottleneck) metering".

**Prior art** (`docs/research/prior_art_P1_P2.md`): incident-responsive metering exists (Sheu & Chang 2007; Dabiri & Kulcsár 2014; Wu et al. 2014; Gao & Xu 2026; FHWA plans). No new mechanism is claimed. Contributions: the information ladder L0 → L1a → L1b → L2; honest headroom bounds (selection on noise; Cameron et al. 2016, van Hasselt 2010); the imperfection map. The term "event-triggered" is not used.

## 1. Plant

- **Plant A only** (A1(a)): BN4 as ported for D1/D2 (`v5b/d1`, `v5b/d2`, commit `72ba8f2`), q ∈ {1600, 2000} veh/h. Edges 1–5 have 4/4/4/2/1 lanes; the meter sits at the end of edge 2.
- **Incidents:** as in screen D2, including Addendum A2:
  - **slow:** speed limit 5 m/s on edge 5 (one lane, 155 m);
  - **block:** lane 4_1 crawls at 1.0 m/s; lane changing is off (disclosed);
  - **onset** uniform in the first third of the 900-s control period, **duration** uniform 120–480 s, drawn from rng(seed + 3301): the same for every arm and both types.
- **Cells:** type {slow, block} × q: 4 claim cells. The no-incident cell (per q) is reported for every arm.
- **Plant B:** dropped and disclosed (A1(a)). The archive's MRG3 is not ready: it has no ramp signal, and its T1 capacity-drop check failed (`docs/lab/t2_mrg3_r1.md` on `claude/vsl-lab-core`).

## 2. Arms

| Level | Arm | Definition |
|---|---|---|
| L0 | **N** | Best of G on no-incident tuning runs, per q (as D2) |
| L0 | **FX** | Best constant rate of G, tuned on the pooled slow + block tuning runs, per q; runs from t = 0 |
| L0 | **FB** | Best feedback meter of G (integral law on the edge-4 count), tuned like FX |
| L0 | **PI** | PI-ALINEA-style law (Wang et al. 2014 [VERIFY]): q(k) = q(k−1) − K_P (n(k) − n(k−1)) + K_I (n_crit − n(k)), T = 30 s, other settings as FB. Grid: K_P ∈ {20, 40, 70} × K_I ∈ G's K_F values × n_crit, with n_crit ∈ G's values on the edge-4 count, or n_crit ∈ {2, 4, 6, 8, 10, 12} on the edge-5 count (the slow bottleneck). Tuned like FX |
| L0 | **AD** | FB with an adaptive set point, in the spirit of AD-ALINEA (Smaragdis et al. 2004 [VERIFY]; not its estimator). Every 30 s: n̂ ← clip(n̂ + η · sgn(Δφ) · sgn(Δn), 4, 20), where φ = vehicles leaving edge 5 in the last 30 s (runner arrival bins), n = edge-4 count, sgn(0) = 0. K_F and n̂(0) = FB's tuned values; η ∈ {0.5, 1, 2}, tuned like FX |
| L1a | **ID** | At onset, the single best action of A on the pooled slow + block tuning runs, per q (presence and timing, no type). No new runs |
| L1b | **IP** | At onset, the best action of A per (type, q) on the tuning seeds (as D2 + A12) |
| L2 | **OR_in** | Per seed, the best action of A on the main run: an upper bound (§6 S2) |
| L2 | **ORX_R** | Per seed, the action with the best mean over the first R replicate runs (§7), scored on the main run: a lower bound in expectation for every R; the largest R is the tightest |
| ref | **NC** | No meter; reference only |

- **Family G** (A5): D2's grid (constant 600, 800, 1000–2600 step 100; K_F ∈ {10, 20, 40, 70} × n_crit ∈ {6, 8, 10, 12}: 35 controllers), or under A5(a) one extension, fixed now: + rate 400, + K_F 120, + n_crit 14 and 16 (50 controllers). **A** = G × {stay, back}: 70 or 100 actions.
- **Tuning:** lowest median delay on the tuning seeds; ties as D2 (A4 c, A12). All L0 arms are tuned per q on the pooled incident mix, so they get no type information. Among the L0 and L1 arms, only IP uses the type.
- **No "best L0" selection.** Every statement against L0 must hold against **each** L0 arm (intersection-union, §5). The binding arm is reported.
- **Grid edges:** reported for every arm and grid dimension. No HALT and no further extension.
- **Max queue** per arm (median over seeds of the largest origin backlog plus vehicles on edges 1–2 during control): reported. No storage limit is imposed.

## 3. Tool checks (tool-check seeds, A9; before tuning; run once, as D2-A9)

| Check | What it requires | If it fails |
|---|---|---|
| T0 | The best **non-oracle** arm (ID, IP or an L0 arm, chosen in hindsight on these seeds as D2-A4 f) beats NC by ≥ 10 % in every incident cell (rel and 95 % CI as §5) | STOP |
| T1 | Teleports in < 5 % of runs per cell | fix with a test, then repeat |
| T3 | The same seed twice gives identical results (one pair each for PI, AD, a delayed switch and a VSL run, plus D2's pairs) | fix, then repeat |
| T4 | The incident changes the best fixed controller by ≥ 10 % in every incident cell (D2-A5) | STOP |
| T-AD | AD binds: per incident cell, the median over runs of max \|n̂ − n̂(0)\| during the incident is ≥ 2 vehicles (η = 1, FB_t's values) | report "AD not identifiable on BN4" for that cell; AD stays in every comparison |

**TV, the VSL check (V98; only under A6(a)).** Posted VSL on the gantry edges 2 and 3 only (as the archive; the incident lanes on edges 4–5 are untouched), b × 23 m/s from onset to clearance, rate-limited to |Δb| ≤ 0.2 per 10 s.
1. **TV-T0, binding:** NC vs NC + VSL at b = 0.4. The number of vehicles entering edge 4 between onset and clearance must change by ≥ 5 %, with the 95 % CI excluding 0, in ≥ 1 incident cell. If not, report "posted VSL cannot bind on BN4 (the gantry capacity is far above the incident bottleneck): a plant limit, not evidence against VSL", and TV ends.
2. **TV entry:** IP_t + VSL vs IP_t, b ∈ {0.8, 0.6, 0.4}. VSL enters iff rel ≥ 10 % with the Bonferroni CI (m = 12: 3 b × 4 cells) lower bound > 0 in ≥ 1 (b, cell). VSL alone vs NC is reported only. A failure reads "no ≥ 10 % gain detected on 20 seeds".
3. **If VSL enters:** b is tuned per cell on the tuning seeds; IP+VSL is one extra L1b row on the evaluation seeds. S1 stays on IP. A, L2 and the replicates do not change.

## 4. Imperfection map (L1b robustness; descriptive)

All rows apply to IP, one imperfection at a time; all others are perfect.

| Imperfection | Levels | New runs |
|---|---|---|
| Detection delay d | {0, 30, 60, 120, 240} s; the plan starts at onset + d; if onset + d ≥ clearance there is no switch (IP = N) | yes |
| Clearance detection delay c | {0, 60, 180} s; back plans only (a stay plan is unaffected) | yes |
| Never switch back | the (g, stay) action for IP's g | no (in A) |
| Misclassification p | per seed, the exact mixture (1 − p) · D(IP) + p · D(the other type's plan); p from 0 to 1 in steps of 0.01 | no (in A) |
| False alarm, rate f | clean-day runs: N, then at a seeded time (drawn like an onset, own salt) one type's plan for 240 s, then N. Both types' plans run; D(FA) = their per-seed mean (50/50) | yes |
| Combined row | d = 60 s, c = 60 s, p = 0.2 | yes |

**Break-even** (per cell, against each L0 arm; the smallest is reported, as the intersection-union rule). Let M(x) = the median over seeds of (L0 − IP at level x).
- **d\*, c\*:** linear interpolation between grid points to the first crossing of M = 0; "> max" if M > 0 on the whole grid; "IP never ahead" if M(0) ≤ 0.
- **p\*:** the first p with M ≤ 0; "> 1" if there is none.
- **f\*(π):** with the prevalence line (§6): the first f (steps of 0.01) at which IP's π-mixture delay, with clean days (1 − f) · D(N) + f · D(FA), stops beating the π-retuned L0 arm; "> 1" if never.
- **CIs:** percentile bootstrap over seeds of the same procedure (B = 20,000). Censored draws stay at their censoring value, and their share is reported.
- **Cost of one false alarm,** D(FA) − D(N) on clean days (s/veh, 95 % CI): always reported.

## 5. Metrics and statistics

- **Primary:** door-to-door delay including the origin queue and the **meter queue** (all vehicles held upstream of the meter), as D2-A4 h. Served throughput is co-headlined; TTT and the max queue are reported alongside.
- **rel** = median(r − t) / median(r) for reference r and treatment t (the D1/D2 code, `v5b/d1/stats.py`). Its CI is the **two-sided** percentile bootstrap of median(r − t), seeds resampled jointly, **B = 20,000**.
- **Mean version** (S2 only): rel_mean = mean(r − t) / mean(r), with the same bootstrap.
- **CI levels:** S1 at 1 − 0.05/8 (S1a and S1b × 4 cells); S2 at 1 − 0.05/4; TV entry at 1 − 0.05/12; everything else 95 %.
- **Intersection-union:** "t beats L0" in a cell needs the rule against every L0 arm (N, FX, FB, PI, AD), each at the same level, with no extra correction.
- **Invalid runs:** a run is invalid iff its `valid` flag is false. For each statistic, the invalid seeds are those with an invalid run that enters that statistic. Every statement must hold both on all seeds and with those seeds removed. Counts are reported per statistic.

## 6. Pre-registered statements

**S1, the information ladder (given that an incident occurs; A4).** For treatment t and reference r, the rule R(t, r) passes iff:
- (a) in ≥ 1 cell, rel ≥ 10 % and the CI lower bound of median(r − t) is > 0; **and**
- (b) in every cell, the **point** rel ≥ −5 % (A2), with its CI reported.

Statements:
- **S1a, presence and timing pay:** R(ID, r) passes for every L0 arm r, with (a) met in the same cell for all of them.
- **S1b, the type pays:** R(IP, ID) passes.
- If S1a fails: "knowing that an incident is on did not pay ≥ 10 % beyond strong always-on control". If S1b fails: "the incident type added no detected ≥ 10 % gain beyond presence and timing". IP vs each L0 arm is reported (descriptive).
- The clean-day delay of every arm is printed next to S1, because the L0 arms are tuned on incident runs only.
- **Prevalence line (report only under A4(a)):** for π ∈ {0.1, 0.25, 0.5}, the per-seed mixture π · (D_slow + D_block)/2 + (1 − π) · D_clean. Each L0 arm is re-tuned on the same mixture of the tuning seeds; ID and IP run N on clean days. Rel vs each L0 arm with 95 % CI, and f\*(π).

**S2, per-incident information (L2) beyond the type plan.** Per cell: OR_in and ORX_R (R in the A7 set, nested) vs IP, in the median and the mean version, and the placebo TP.
- "**Adds at most x %**": x = the upper CI bound of rel(IP, OR_in). Always stated. Valid for medians, because on every seed OR_in ≤ the main-run score of the truly best action.
- "**Adds at least y %**": y = the lower CI bound of rel_mean(IP, ORX_Rmax); stated only if y > 0. The mean is used because ORX is a lower bound only in expectation.
- "**Adds about ŷ % (biased low)**": ŷ = rel_mean(IP, ORX_Rmax); stated only if the plateau holds: the 95 % CI of rel_mean(ORX_{Rmax/2}, ORX_Rmax) lies within ±z points (A8).
- Otherwise only the bracket [y, x] is stated.
- **TP (placebo; report only, P2 methods):** per seed, IP's main run vs the best of IP's main run and its Rmax replicates, as rel(IP_main, min). It illustrates pure-noise inflation and is never subtracted from anything.

**S3, robustness (descriptive):** d\*, c\*, p\*, f\*(π) and the combined row, with 95 % CIs (§4). No significance claim.

**No novelty claims.** Every other number is descriptive.

**Paper outputs (A10):** Fig. 1 = the ladder per cell: strongest L0 → ID → IP → [ORX_Rmax, OR_in]. Table 1 = the operating map (every arm, every cell, clean day). One inset = the S2 bracket, the ORX_R curve, TP and one methods paragraph. One break-even table (d\*, p\*, f\*); the clearance delay in the text.

## 7. Seeds (from the approved v5.B block; the author approves the ranges)

| Use | Seeds |
|---|---|
| Tool checks (incl. T-AD, TV) | A9 (default 7,400,240–259) |
| Tuning | 7,400,200–239 |
| Evaluation | 7,400,500–599 (100 seeds) |
| Replicates k = 1 … Rmax | SUMO seed = evaluation seed + k × 10,000,000; under A3(a) the demand (arrival) seed too. The incident window always comes from the evaluation seed |
| Smoke and build runs only | 7,400,000–009 |

## 8. Operation, disclosures and cost

- **Machine:** 32 workers, CPU guard at 90 % (V93), its own systemd unit. The pad and fans are handled per the author's current instruction.
- **Code and tests** are committed before any tool-check seed is run. Run-once sentinels guard the tool checks (as D2-A9) and the evaluation. Resume only at the same commit.
- **Disclosures:**
  - screens D1 and D2 and their numbers were seen. D2 in the paired convention: IP beat N by 10–35 % per cell (V94's "16–41 %" were differences of arm medians);
  - the design review re-analysed D2's evaluation runs (seeds 7,400,140–189) and ran probes on smoke seeds 7,400,000–003 (VSL on BN4, MRG3); their outcomes were seen;
  - the D2 tuning and evaluation seeds are not reused;
  - the block substitute; no amber at the meter; mainline metering (A1); VSL's archived failure on BN4.
- **Cost (estimate; D2 measured 9.0 runs/s at 32 workers: 48,732 runs in 90 min):**
  - default (A5(a), A7(a)): about 300k runs (tool checks 15k; tuning 72k, of which PI 43k; evaluation 214k, of which replicates 160k), **about 9 h: one overnight run**;
  - range over A5 and A7: about 210k–460k runs, 6.5–14 h; A1(b) roughly doubles it;
  - build about 2–3 days (PI, AD, ID, replicate redraw, imperfection hooks, mixtures, VSL port, intersection-union statistics), plus a review; author about 1 h.

## Author decisions (resolved V99: all defaults)

| # | Question | Options | Default |
|---|---|---|---|
| A1 | Plant and framing | (a) BN4 only, framed as "mainline (bottleneck) metering"; plant B dropped; the prior-art positioning is re-checked against mainline metering and MTFC [VERIFY refs]. (b) Keep "ramp metering": a fully specified on-ramp plant becomes mandatory before any plant-A evaluation seed, with a queue-override rule for every arm (about +2–4 days build and ×2 compute, estimate) | (a) |
| A2 | S1(b), "never worse by > 5 %" | (a) on the point estimate, CI reported. (b) on the CI lower bound; slow_q1600 would then need several times the seeds (D2: IP vs FB +2.0 % [−17.6, 16.0] at n = 50) | (a) |
| A3 | What the replicates redraw | (a) demand and SUMO seed, incident kept: L2 = "the incident's type, onset and duration". (b) SUMO seed only, as D2: L2 is renamed "per-scenario clairvoyance (incident + demand realisation)" | (a) |
| A4 | Incident prevalence | (a) S1 "given that an incident occurs", clean-day cost printed, prevalence line report-only. (b) S1 on the π-weighted delay for each π ∈ {0.1, 0.25, 0.5}, L0 re-tuned per π, Bonferroni × 3 | (a) |
| A5 | Grid G | (a) one extension now (rate 400, K_F 120, n_crit 14 and 16; A = 100). (b) D2's grid (A = 70). Both: grid edges report-only | (a) |
| A6 | VSL check (narrows V98: entry only "on top of IP", not "alone") | (a) TV as in §3: binding check first, then IP+VSL vs IP with Bonferroni. (b) Drop TV; one sentence citing the archive (`docs/lab/round2_a_t0.md`: posted VSL does not bind on BN4) | (a) |
| A7 | Replicates R | (a) R ∈ {1, 2, 4}. (b) R ∈ {1, 2, 4, 8} (+160k runs, about +5 h). (c) (a) plus R = 8 on 40 of the evaluation seeds (report only; Rmax stays 4) | (a) |
| A8 | Plateau width z for "about ŷ %" (S2) | 1, 2 or 5 points | 1 |
| A9 | Tool-check seeds | (a) 7,400,240–259 (unused tuning range). (b) 7,400,300–319 (validation range). (c) 7,400,700–719 (reserved confirmatory range, as first drafted) | (a) |
| A10 | Paper scope (6 pages) | (a) the outputs listed in §6. (b) every row in the main text | (a) |

Approving the page also approves the seeds 7,400,200–239 and 7,400,500–599, the derived replicate seeds, and the chosen options.

## Addendum (2026-10-19): build interpretations I1-I16 and code-review changes

Recorded after the code review of the build (commits `8f204c6`, `b7d0578`), before any tool-check seed. **No item makes S1a, S1b or S2 easier than the page above:** R1 and R5 are stricter, R8 touches S3 only (descriptive), and I1-I16 only fill gaps where the page is silent. D1-D5 are open author decisions; the runner refuses to start without D1-D4 (required flags, no defaults). **Launch blocked until they are decided.**

### Build interpretations (the page is silent; the simplest reading)

- **I1 T0's best-of:** ID_t, IP_t, N_t, FX_t, FB_t and AD_t (η = 1, the T-AD runs). PI is not run on the tool-check seeds (§8 cost of 15k excludes its 14k-run grid); omitting it can only make T0 stricter. The seed views of T0 / T4 / TV are now decision D4.
- **I2 PI:** n(k−1) = n(k) at the first update (no P kick); "e5" reads the edge-5 vehicle count.
- **I3 AD:** φ = arrivals since the previous 30-s update (the runner's cumulative counter, equal to the sum of three 10-s bins). The first update has no previous (φ, n), so n̂ does not move there; the FB law uses the updated n̂. AD is tuned over η only, with FB's tuned (K_F, n_crit), also in the prevalence re-tuning (see D5). T-AD "during the incident" = the set point in effect at onset plus every update before clearance.
- **I4 VSL:** 10-s update grid anchored at the onset tick (1.0 → 0.8 at onset); after clearance the target is 1, ramping up on the same grid (the release starts up to 9 s after clearance); b clipped to [0.2, 1] as the archive; 23 m/s restored before the drain. Edge-4 entries = new vehicle ids on edge 4 per 0.5-s step between the incident's on and off ticks (window: decision D3). The TV-T0 "change" is two-sided. VSL alone vs NC is reported at b = 0.4 only (the TV-T0 runs). If VSL enters, b per cell over {0.8, 0.6, 0.4} (ties in that order).
- **I5 Delays** on the 1-s tick grid: no switch if the delayed tick is not before the clearance tick. Runs that cannot differ map to the identical existing run (no switch, or a plan to N itself → the N run; a stay plan ignores c; a back plan returning after control end → the stay plan).
- **I6 False alarm:** time ~ U(first third of control) from rng(seed + 5113); the plan's controller runs 240 s, then N, for stay and back plans alike; a plan whose controller is N is the N run.
- **I7 Misclassification / combined row:** "the other type's plan" = IP's action for the other type (same q); in the combined row the misclassified plan also has d = 60 s, c = 60 s.
- **I8 Break-even:** the smallest over the L0 arms; its CI bootstraps that minimum jointly; censored draws at the grid end ("> max", "> 1") or 0 ("IP never ahead"; also for p\*, f\* when M(0) ≤ 0); f\*(π) per q.
- **I9 L0 arms in incident cells** are their fixed runs from t = 0, N included (+400 evaluation runs); the hash equality of N fixed vs the N → N switch run is reported. Prevalence-retuned L0 arms get fixed evaluation runs only where they differ from the main arms.
- **I10 Invalid seeds:** OR_in's statistic includes all 100 main A runs of the seed; ORX_R's the R × 100 replicate runs and the chosen main run. S2 across views: "at most" the larger x, "at least" the smaller y (stated only if > 0 in both), "about" only if the plateau holds in both (all-seed ŷ stated, valid-only alongside). Descriptive rows (S3, prevalence, combined) are reported in both views. S1: see R5.
- **I11 Missing runs:** a seed enters a cell only if every run it needs exists (a run that failed twice drops the seed); counts are reported. S1 fails closed on a missing claim cell (R1); S3 drops seeds, not cells (R8).
- **I12 CIs:** x and y use the rel CI (percentiles of median(d\*) / median(r\*), the D1/D2 convention); S1(a), T0 and TV use the CI of median(r − t). The plateau CI is 95 % as written. TP uses the median version at 95 %. Bootstrap draws are fixed (seed 20261019) and shared by statistics with the same n.
- **I13 Ties:** ID over A's order; T0's best arm in the order ID, IP, N, FX, FB, AD; Fig. 1 "strongest L0" = the lowest median delay among the L0 arms in that cell (ties in L0 order).
- **I14 T3** adds pairs for both PI detector variants, a replicate (k = 1; its seed is decision D2) and a false alarm (13 pairs; 12 without the replicate).
- **I15 Max queue** is sampled at the 1-s control ticks. `--cpu-limit` defaults to 0.90 and is capped at 0.90.
- **I16 Smoke:** G / PI subsets; seeds 7,400,000-009 (tool checks 000-002, tuning 003-005, evaluation 006-009; replicates 17,400,006-47,400,009, derived), or with `--smoke-n 4` seeds 7,400,000-003 only (tool checks 000-001, tuning 002-003, evaluation 000-003). TV entry and the VSL rows are forced in the smoke to exercise the code.

### Code-review changes (applied, with tests)

- **R1 S1 fails closed.** S1a and S1b FAIL, with the missing cells named, if any of the 4 claim cells has no seed with every run it needs (before: decided on the cells that remained).
- **R5 One (a) cell in both views.** S1a needs a cell where (a) holds for every L0 arm in both views (all seeds and valid only); S1b needs a cell where (a) holds in both views. Before: each view could use its own cell. Strictly stricter.
- **R8 S3 drops seeds, not cells.** A seed whose imperfection runs (d, c, combined, misclassification, never-switch-back) are not all present is dropped from that cell's S3 rows and counted (before: one missing run removed the whole cell's S3 output).
- **Meter signal (finding R3; the choice is D1).** The P1 meters (constant, FB, PI, AD) take the signal mode explicitly: `d2` (D1/D2's FBMeter phase rule, unchanged) or `continuous` (the time since the last green start carries over when q changes; a new green starts at once if it already reaches the new cycle). Tested: `d2` reproduces D1's FBMeter and the D2 run; a constant rate gives the same signal in both modes; under `continuous` every green lasts 6 s, a red never exceeds c(q_min) − green = 138 s (+1 tick), and the green count matches the commanded rate within one cycle.
- **Decision plumbing.** D1-D4 are required runner flags (`--meter-signal`, `--t3-replicate`, `--tv-t0-window`, `--gate-views`), recorded in result.json, the tool-check record and the sentinel; a `--resume` must repeat them, and a stored run made with another meter signal is never reused. Every incident run also records `entered_e4_ext120` (edge-4 entries from the on tick to the off tick + 120 s). T0, T4, TV-T0 and TV entry are computed and reported in both views whatever D4 says; under the page window, a TV-T0 "binds" that does not bind over the extended window carries a travel-time-shift caveat.
- **Not applied:** R1's optional "drop a seed from S1 only for missing ID / IP / L0 runs". The fail-closed rule fixes the defect; one seed set per cell keeps S1-S3 paired.

### Author decisions needed before launch

| # | Question | Options | Recommended default |
|---|---|---|---|
| D1 | Meter signal (blocker). The D2 rule recomputes the cycle phase with the current q: when q changes the phase jumps and greens are skipped. In the smoke this gave reds up to 322 s (the longest commanded is 138 s); the 3 teleport runs waited at the meter stop line during such a red and had no teleports with the continuous rule. The review probe on seeds 7,400,000-009 moved FB / PI / AD cells by −15 % to +17 % (median per seed). | (a) `continuous`; disclose that the meter differs from D1/D2's, so D2 numbers are not directly comparable. (b) `d2`; disclose that realised reds exceed the commanded cycle | (a) |
| D2 | T3's replicate pair runs at the derived seed 17,400,240 (tool-check seed + 10^7), which §7 does not approve | (a) approve 17,400,240 (derived as §7's replicates; it overlaps no range). (b) drop the pair (the page does not require it; a unit test covers the seed arithmetic) | (a) |
| D3 | TV-T0 window. VSL on edges 2-3 delays arrivals by about 28 s, so the onset-clearance count can drop with no flow restriction (review probe: block 4.8 / 11.3 % in the page window, 0-0.8 % over clearance + 120 s) | (a) `page`: the rule as approved; the extended count and the caveat are reported. (b) `ext120`: count from onset to clearance + 120 s; the page window is reported | (a): TV entry (Bonferroni, ≥ 10 % delay gain) still guards VSL entry, so a false "binds" costs 240 runs and its wording carries the caveat |
| D4 | Seed views of T0, T4 (STOP gates), TV-T0 and TV entry (I1 used all seeds, as D2) | (a) `all_seeds`, valid-only reported. (b) `both`: as §5, every cell in both views for T0 / T4, the same cell or (b, cell) in both views for TV-T0 / entry; the hindsight arm is the one chosen on all seeds | (b) |
| D5 | Prevalence line: AD_π is re-tuned over η with the main FB's (K_F, n_crit), not FB_π's (report only; S3) | (a) disclose "AD_π keeps the main FB values". (b) add the AD runs η × FB_π on the tuning seeds (about 2.2k runs [estimate]; needs a follow-up build) | (a) |
