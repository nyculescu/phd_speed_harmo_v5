# Development plan v2: #1 calibrated RSS filter, #2 calibrated eco-approach

Date: 2026-10-16. Plan v1 with the findings of two verification reviews applied.

- No statistic has been computed on any trajectory or signal data. The repo is unchanged.
- Time is split three ways: **(a) author**, **(b) Claude build and verification**, **(c) machine** (compute plus download).
- Only (c) comes from probes (one sample each unless stated). All (a) and (b) numbers are my estimates.

## Re-check results

| | Still uncertain |
|---|---|
| #1 | Do regimes differ enough? NGSIM tail noise; enough windows per regime; TGSIM licence; El Halabi & Brandt theorem; Scopus/IEEE Xplore not searched |
| #2 | 2023 IDs vs 2026; no queues or detector calls (gains = upper bounds); archive end; Xue not read |

## 1. Verdict and fixes

**#1: GO, narrowed.** The contribution is empirical: score design, per-regime online calibration, recorded leaders at ≥ 2 sites. The method is online quantile tracking (Angelopoulos et al. 2023, Prop. 1; Gibbs & Candès 2021, Prop. 4.1); ACI is related work. Not new theory.

**#2: GO, narrowed.** Planner and chance constraint are published (Xue et al. 2026, TR-C 183:105460). Still open: online calibration of the commit margin per signal group, on public logs.

**The kill tests are independent** and are built in parallel sessions.

**Fixes adopted:**
- **F1. Clip only from below** (b_floor); cap scores at b_phys. Lean's upper clip gave a synthetic miss rate of 0.143 against a claimed 0.02.
- **F2. One tracker per regime, delayed and batched feedback,** normaliser c, start q_1 = 4 m/s².
  - Bound over any continuous stretch: miss share ≤ α + [c(b_phys − b_floor)/η + N_fl]/T_r. T_r counts windows whose outcome was applied; windows pending at a block end are left out (pre-registered), otherwise the term is 2·N_fl.
  - My derivation; synthetic adversarial runs found no violation (slack used ≤ 0.85). No novelty claim: compare with El Halabi & Brandt 2026 (arXiv 2609.07251) and Szabadváry 2024 (arXiv 2409.14792) first [VERIFY: abstracts only].
  - It says nothing about single windows, sub-groups, short stretches, other sites, gap length or collisions.
- **F3. Placebo.** Time-shuffled tracker; only the gain over it counts; median primary.
- **F4.** Windows starting below the safe gap after b̂ steps up are counted separately; gap restored at ≤ 3 m/s² (V36).
- **F5. Exact safe gap**, because RSS Lemma 2 holds only for b̂ ≥ b_min (Section 2).
- **F6.** QC-flagged scores are capped, not dropped. Also new in v2: honest guarantee wording; data-size STOP and INCONCLUSIVE outcome; headroom vs the best static arm; more opponents; #2 one CDT per group × program, capped forecast, latency model, local time, live recording.

## 2. #1: leader-adaptive RSS safety filter

**Problem.** One automated car (the ego) follows a recorded leader in replay; the leader never reacts.
- A nominal ACC proposes a_nom; the filter applies min(a_nom, a_safe), keeping the gap ≥ d_safe(b̂) + s0. Only b̂, the leader's assumed maximum braking, adapts per regime.
- d_safe(b̂) = largest closing distance over t ∈ [0, H] between the ego's proper response (react for ρ at up to a_acc, then brake at b_min) and a leader braking at b̂.
  - For b̂ ≥ b_min it equals Lemma 2 of Shalev-Shwartz, Shammah & Shashua (arXiv 1708.06374v6, Def. 1 and Lemma 2): [v_e·ρ + ½a_acc·ρ² + (v_e + ρa_acc)²/(2b_min) − v_L²/(2b̂)]₊.
  - For b̂ < b_min Lemma 2 understates the gap (synthetic: 35.4 m vs 41.5 m exact; ego 30, leader 20 m/s, b̂ = 2). Unit test against brute-force simulation, including b̂ < b_min.
- **Goal:** per regime, long-run miss share (leader brakes beyond b̂) ≤ α + slack, with the shortest gaps. Car-following only.
- **Claim:** "a calibrated planning margin" for comfort and efficiency. Safety comes from a separate emergency layer (ego maximum braking 8 m/s²). A miss is not a collision; α = 0.02 per 8-s window ≈ 9 misses per hour, reported as such.

**Algorithm.**
- **Window.** Ego speed capped at the posted limit; W = H = ρ + (v_lim + ρa_acc)/b_min ≈ 8.0 s at 65 mph [VERIFY: limits not in the FHWA fact sheets].
- **Score.** s_k = max of b_req(t, h) over t in window k, h ∈ [h_min, H]; b_req = 2(v0·h − X)/h² if X ≥ v0·h/2, else v0²/(2X) (X = leader displacement over h, v0 = v_L(t)). Leader-only, so coverage stays exact in replay.
- **Regime.** From the leader history that exists (3–10 s, causal). R1: minimum speed < 2 m/s; R2: mean < 10 m/s; R3: others. NGSIM sections (~503 m, ~640 m) cannot hold 10 s back plus 16 s ahead for leaders above about 19 or 25 m/s, so R3 is report-only there. Report the speed distribution of scored vs all windows, and the share cut at the exit.
- **Update.** q ← max(b_floor, q + (η/c)·Σ(1{s > q_used} − α)) as outcomes arrive. The one-car chain (c = 1, N_fl = 2) carries the F2 claim. The fleet-shared calibrator (V2X) reports miss rate, CI and slack without needing slack ≤ δ: its delay term alone is ≥ 16 s / D (≥ 0.018 for a 15-min block).
- **Guarantee.** (i) F2. (ii) Lemma: a covered window starting with gap ≥ d_safe(b̂) + s0 keeps the gap ≥ s0 within H under the proper response (h < h_min checked in replay). (iii) So near-miss (gap < s0) share ≤ miss share on those windows.
- **Constants.** ρ 0.5 s; a_acc 2, b_min 4, ego maximum 8, b_floor 2, b_phys 10 m/s²; s0 2 m; h_min 1 s (0.5, 2 s sensitivity); η = 0.5 and c = median batch size on the fitting site, fixed now (η 0.25, 1 sensitivity).

**Data.**
- **NGSIM** (CC BY-SA 3.0, doi 10.21949/1504477): I-80 Emeryville, 13 Apr 2005, 4:00–4:15 and 5:00–5:30 pm (block 1 is 45 min before blocks 2–3, at congestion onset); US-101 Los Angeles, 15 Jun 2005, 7:50–8:35 am.
- **Download now** via the legacy rows.csv export (speed measured; its headers announce Sunset 22 Dec 2026), ~1.5 GB, to `/home/catalin/work/phd/v5b1_data/ngsim`. Fallback: /resource/ with explicit $limit and $order=:id (default 1,000 rows, unordered). Check rows (I-80 4,566,387; US-101 4,802,933); record MD5.
- **Format traps:** duplicate, unordered rows; Global_Time scale may differ by location; Vehicle_ID may repeat across periods [VERIFY]; feet to metres. Derived NGSIM data we publish must be share-alike.
- **Per-source pipelines.** Causal smoothing for what the controller sees; centred Savitzky–Golay (1 s, 2nd order) only for outcome scores. TGSIM is already Kalman-filtered, with no Preceding column (leader rebuild 2–3 h Claude). Noise check: share of scores > 8 m/s² per source.
- **Split (D1).** All 45 min per NGSIM site are throw-away (tuning, kill test). Confirmatory: TGSIM I-90/94, I-395, I-294 (licence query now); highD/exiD (request access now [VERIFY procedure]) and I-24 MOTION after a GO.

**Baselines** (same tuning budget, throw-away data).
- **References:** recorded human (never alone); default RSS, b̂ from Naumann et al., IV 2021 [VERIFY values]; nominal ACC. OpenACC (Makridis, Mattas, Anesiadou & Ciuffo, TR-C 125:103047, 2021) is data, not parameters: cite a calibration study [VERIFY: not searched] or calibrate on throw-away OpenACC data (+ download, licence check).
- **Offline:** global quantile; **per-regime (Mondrian) quantile fitted cross-site, the strongest static opponent**; per-regime fitted on the same site's block 1, scored on blocks 2–3; per-vehicle-class (v_Class); quantile regression + split conformal.
- **Online:** global tracker (Zhou-style); rolling-window per-regime quantile.
- **Controls:** placebo; hindsight per-regime reference (headroom and G only).
- **Confirmatory only:** DtACI/AgACI; conformal PID; multivalid conformal (Bastani et al. 2022, arXiv 2206.01067 [VERIFY: abstract only]); tuned constant-time-headway ACC in closed loop at a matched near-miss rate; CDT on the near-miss loss.

**Metrics.**
- **A1.** Per regime × held-out site or block: upper 95 % bound of the miss rate ≤ α + δ, δ = α/2. Also longest miss run, worst rolling 10-min miss rate, misses per hour.
- **Co-primary.** Median required time gap at the regime's own speeds, at nominal α with A1 as validity filter; matched-rate comparison as sensitivity. Closed loop: median ego gap.
- **Secondary (S4):** gap-derived capacity (stated formula); ego travel time.
- **Guards:** zero collisions at ego maximum braking; near-miss ≤ miss; share starting below the safe gap; filter-active share; jerk; QC share.
- **Statistics:** paired medians; moving-block bootstrap over time, all lanes, 2-min blocks (≥ 20 clusters; 5 min sensitivity); Bonferroni across regimes.
- **"Claimed" rule.** Before data, compute expected T_r and N_fl per arm, regime and unit from vehicle counts × time in section (a count, not an outcome; needs your OK). Claimed only if expected slack ≤ δ and a power check predicts CI half-width ≤ δ; otherwise the bound is "asymptotic" and A1 empirical. The one-car chain needs ~1,000–3,400 windows per regime (synthetic), so NGSIM probably claims nothing.

**KILL test.** All NGSIM; fit on one site, evaluate on the other, both directions; no ego, no filter. Per regime, Bonferroni, same rule as A2. Outcomes: GO, KILL, or **INCONCLUSIVE** (minimum detectable effect, computed before data, too large → one re-run on a TGSIM block, then you re-plan).
- **Q (STOP).** > α/4 of windows QC-flagged. Fallback: TGSIM, or reconstructed I-80 (Montanino & Punzo [VERIFY availability, licence]).
- **D (STOP).** Expected T_r below the minimum.
- **K0 (headroom).** Hindsight reference shortens the median gap < 0.1 s vs the best static per-regime arm (default RSS report-only).
- **K1.** On both sites, the Bonferroni CI lower bound of the largest per-regime vs global difference < 0.3 s at each regime's speeds.
- **K2.** No regime, either direction, has a transferred miss-rate CI wholly outside [α/2, 2α].
- **K3.** At nominal α, online median gap < 0.1 s shorter than the best offline arm, **or** than the placebo.
- **N1 (narrows).** Rolling window within 0.1 s: "same efficiency, plus a guarantee".

| #1 step | (a) Author | (b) Claude | (c) Machine |
|---|---|---|---|
| Decisions | 0.5–1 h | – | – |
| NGSIM download | – | 0.1 h | 6–23 min (rows.csv, 1.1–4.1 MB/s) |
| Protocol + review (one sitting with #2) | 1–2 h | 2–3 h | – |
| Build + unit tests | – | 5–8 h | – |
| Run + report | 0.25–0.5 h | 0.5–1 h | < 5 min (3.8·10⁶–1.5·10⁷ steps/s per core, synthetic; ~4–8·10⁶ at NGSIM's ~170 concurrent vehicles) |
| **Kill test total** | **1.75–3.5 h** | **8–12 h** | **≈ 10–30 min** |
| Confirmatory P1 | 0.5 h + 20–35 h writing | 1–2 session-days | TGSIM ~1.0 GB, 4–15 min; compute < 1 h |

## 3. #2: calibrated eco-approach at actuated signals

**Problem.** One automated car approaches one Hamburg signal group (KFZ primary, served every cycle; chosen on throw-away days by a seeded rule).
- A frozen forecaster predicts the next green [ĝ0, ĝ1], ĝ1 capped at now + 120 s.
- Commit only if a comfortable trajectory reaches the stop line inside [ĝ0 + τ_q + m, ĝ1 − m]; otherwise approach to stop, no commitment, ℓ = 0.
- A hard layer keeps "stop at b_comf" or "clear on amber" possible; never enter on red.
- **Objective:** energy. **Loss:** ℓ = 1 if the car committed, then had to stop or brake harder than b_comf.

**Algorithm.**
- **Time.** Days and time of day in Europe/Berlin local time (received_time is epoch ms UTC; CEST = UTC+2).
- **Latency model.** mqtt=t rows: visible at received_time. mqtt=f rows were back-filled by HTTP polling (~295 s late in the first rows): report (a) dropped and (b) visible at phenomenon_time plus a lag fitted on mqtt=t rows of throw-away days. STOP for a group above a fixed mqtt=f share. Switch times from phenomenon_time (1 s); red crossing beyond 1 s; zero latency only as an upper-bound row.
- **Forecaster.** Lookup on program, cycle second, state, time in state.
- **Approaches.** 300 m upstream at 13.9 m/s; one seeded arrival stream for all methods, ≥ 180 s apart; late outcomes applied when known.
- **Planner.** Kill test: closed-form commit-or-stop, energy-minimising profile. Paper DP cost = groups × days × 480 × arms × 7.8 ms (20 groups, 7 days, 8–10 arms ≈ 1–1.5 h on one core), less if cached per arrival window.
- **CDT, one tracker per group × program (Mondrian):** m ← max(0, m + η(ℓ − ε)).
  - "Eventually safe" with K = 1 (Lekeufack et al., Def. 1): never committing gives ℓ = 0, valid because ĝ1 is capped.
  - Their Theorem 1 has no feedback delay. Delayed version (my derivation, as F2): long-run mean loss ≤ ε + [(m_safe − m_1)/η + 1 + N_fl]/T_r, N_fl ≈ 1.
  - η, m_1, m_safe fixed before data; slack stated per group × program. A weekend has ≤ ~960 approaches per group, so slack may exceed δ = 0.025 unless η is large. Time-of-day and weekday regimes: A1 empirical only.
- **Fallback.** IDM when there is no forecast; share reported.

**Data.**
- **Archive.** OPARA zip, 33,813,300,354 B, MD5 11d66d59bcd1fdf2b4a43737231e5f63, CC BY 4.0 (source dl-de/by-2-0, attribution LSBG), doi 10.25532/OPARA-466 (Jeschor, Matthes, Springer, Pape, Fröhlich). One 164.5 GB CSV, streamed once, never extracted, stored on /srv/shared (/ has 14 GB free).
- **Metadata.** Hashed snapshot of the live SensorThings API (80,276 datastreams, ~2 min).
- **Live recording, start now:** SensorThings/MQTT (tld.iot.hamburg.de; licence [VERIFY]), unattended, on /srv/shared. Fresh confirmatory data with current IDs and real latency.
- **QC (before data).** Complete state sequences; plausible amber and red-amber; amber ≥ v/(2b_comf) + 0.5 s ≈ 2.8 s; gap cycles excluded; split by mqtt; drop rate reported.
- **Split by local date.** Throw-away 13–24 Sep 2023 (13 Sep partial, from ~15:20). Forecaster: 13 (Wed afternoon), 14 (Thu), 16 (Sat). Offline margins: 15 (Fri), 17 (Sun). Kill evaluation: 18–24 Sep (Mon–Sun).
- **Confirmatory.** 25 Sep to the archive end (extrapolated ~16–17 Oct 2023; record the last received_time), 20 % of intersections held out, plus the live recording.
- **Regimes.** Program; weekday vs weekend; 2–3 Oct; data-gap periods. School holidays (16–27 Oct 2023 [VERIFY official calendar]) may overlap the last 1–2 days: report-only.

**Baselines.**
- **References:** IDM uninformed driver (red = stopped virtual leader; parameter source not yet named [VERIFY]; 2 variants); perfect foresight (report-only); hindsight margin per group × program (headroom and G only).
- **Static:** deterministic GLOSA (m = 0); fixed global margin; Xue-style fixed confidence level; **group × program × time-of-day table with coarser fallback, the strongest static opponent**, plus its nightly expanding-window refit; quantile regression + split conformal.
- **Other:** online-updated forecaster with a fixed table margin; rolling-window margin (N1); placebo CDT; Eteifa-style consensus gate (confirmatory only).

**Metrics.**
- **A1.** Per group × regime: upper 95 % bound of the broken-commitment rate ≤ ε + δ.
- **Co-primary.** Energy per approach, paired, at nominal ε with A1 as filter; matched loss as sensitivity. ICE primary: VT-Micro (Rakha, Ahn & Trani 2004, TR-D 9(1):49–74). EV in every table: VT-CPEM (Fiori, Ahn & Rakha 2016, Applied Energy 168:257–268, doi 10.1016/j.apenergy.2016.01.097; vehicle parameters [VERIFY]).
- **Guards.** Zero red crossings; hard brakes > 3 m/s² (V36); stops; travel time ≤ +2 % vs IDM (V37); no-forecast share; τ_q ∈ {0, 4, 8} s.
- **Statistics.** Paired medians; cluster bootstrap over intersection-days; Bonferroni.

**KILL test** (18–24 Sep). Per group × regime, Bonferroni, same rule as A2; GO, KILL or INCONCLUSIVE.
- **D0 (STOP).** MD5 mismatch; < 90 % of selected IDs resolve; < 20 groups after dropping those with ≥ 10 % gaps; the mqtt=f STOP.
- **K1 (headroom).** Hindsight margin saves < 1 % energy vs the best static table arm. Perfect foresight vs IDM is report-only: Shafik et al. 2022 report 28–37 % in simulation, so that gate would decide nothing.
- **K2.** < 10 % of group-regimes have a table-loss CI wholly outside [ε/2, 2ε].
- **K3.** At nominal ε, any of: online closes < 10 % of the gap from the best offline arm to the hindsight margin; saves < 1 % vs the best offline arm; saves < 1 % vs the placebo.
- **N1.** Rolling window within 1 %: claim narrows.

| #2 step | (a) Author | (b) Claude | (c) Machine |
|---|---|---|---|
| Decisions | 0.5–1 h | – | – |
| Read Xue, Li–Wang–Hu, Lu (gates the confirmatory protocol only) | 4–9 h | – | – |
| Download, MD5, metadata, filter, live recorder | – | 1–2 h | 57–92 min single stream (3 probes) or ~22 min with 4 parallel ranges + reassembly + MD5 (1 probe); + 2 min metadata; + 14–17 min filter |
| Timelines, QC, latency, forecaster, planner, IDM, energy | – | 6–8 h | minutes |
| CDT, opponents, placebo, statistics, no-leak test | – | 4–5 h | – |
| Protocol + review (one sitting with #1), run + report | 1–2 h | 2–3 h | minutes |
| **Kill test total** | **1.5–3 h** (+ reading) | **13–18 h** | **≈ 0.7–2 h, unattended** |

Papers: Xue Y, Bai D, Zhou Y, Ding C, Vu H & Yu B (2026), TR-C 183, 105460, doi 10.1016/j.trc.2025.105460; Li, Wang & Hu, TR-C 177 (2025) 105198; Lu et al., TR-D 132 (2024) 104270.

## 4. Shared code

`v5b/` exists but is empty; NumPy, pandas, SciPy are pinned.

```
v5b/calib/   tracker  cdt  rolling  placebo  offline (global, Mondrian, class, table+refit, QR+conformal)
v5b/stats/   bootstrap  matched  validity  power  multiplicity  opmap
v5b/ops/     ledger (ported)  datareg (URL, licence, citation, MD5, rows)  seeds
v5b/follow/  ngsim tgsim smooth score regimes safegap acc replay killtest
v5b/signal/  opara_stream livefeed meta timeline latency qc forecast planner dp idm energy replay killtest
tests/       tracker bound (delayed, batched, block end)  b_req, safe gap vs brute force  cdt  no-leak
```

- **Build rule:** vectorise by frame (a scalar loop measured 80–335× slower, synthetic). One process per kill test.
- **Ops:** check resources before every run; downloads, stream filter and live recorder in their own `systemd-run --user` units with `nice -n 19`.
- **Ports** (`claude/day-pattern-core` 8eb0343, recorded per commit): `vsl_lab/ops/ledger.py`, `paired_median_diff` (`vsl_lab/eval/stats.py`); `ops/guard.py` per S5; never SUMO, CORR2X or DRL.

## 5. Claim rule replacing D5.8 (author decides; record as V80)

- **A. "Valid and not wasteful" (recommended).**
  - **A1:** in every pre-registered regime × held-out site or time, the upper 95 % bound of the miss or loss rate ≤ α + δ.
  - **A2:** the online method beats the best offline arm and the placebo in ≥ 1 regime (Bonferroni CI excludes 0), never > 5 % worse. An arm that fails A1 in a regime counts as failing A2 there (by analogy with V6, which concerned invalid SUMO runs).
  - **A3:** the headroom gate (K0 for #1, K1 for #2). Full operating map reported.
- **B. Adaptation gain (secondary).** G = (fixed − online)/(fixed − hindsight) at nominal α, defined only if fixed − hindsight ≥ 0.1 s (#1) or 1 % (#2). Passes if G ≥ 0.5 with CI lower bound > 0 in ≥ 1 regime, plus A1.
- **C. Keep D5.8 (not recommended):** trivial on safety and probably impossible on gaps (#1); measures signal data, not adaptation (#2); never tests validity.
- **If A:** the term becomes "online-adaptive algorithm" (a run-time parameter update with a stated rule and guarantee); vanilla DRL is dropped with disclosure; learned offline opponents keep "learning" in the comparison.

## 6. Author decisions (at most five per option; the rest is in the annex)

**Shared**
- **S1.** Claim rule A (B secondary), the term, DRL dropped; V80. Check with your supervisor (calendar time). The kill tests use throw-away data and need not wait; V80 is final before any confirmatory data.
- **S2. New null rule** (the 2026-10-05 decision named DRL and is not in v5b1 `docs/decisions.md`): only positive online-adaptive results count; a KILL gives no paper; A1 pass with A2 fail is a thesis chapter (new clause). Record as a V entry.
- **S3. Seeds and data burn.** The approved block is tied to F3Z protocol P0–P2 (V66, V71, V74; on hold under V77). Choose (a) a new block for #1/#2, or (b) record P0–P2 as abandoned and relabel. Unit tests use non-project seeds. Fresh seeds give no fresh recordings, so each confirmatory block or date range is evaluated once; a later protocol change needs new data.
- **S4. Metric rule.** CLAUDE.md makes door-to-door delay with queues, throughput and TTT primary. Replace it for #1/#2 (miss or loss rate; gap or energy), with capacity and travel time secondary. V entry.
- **S5. Guard.** CLAUDE.md wants the CPU guard before the first batch. Does a single-process kill test need it?

**#1**
- **D1.** All NGSIM throw-away; confirmatory TGSIM (+ highD, I-24 after a GO); licence query and access request now.
- **D2.** α = 0.02 per window (0.01 secondary); δ = α/2.
- **D3.** One-car chain carries the F2 claim; fleet arm empirical; vehicle counts allowed for the data-size STOP.
- **D4.** Thresholds: Q α/4; K0 0.1 s; K1 0.3 s; K2 the CI rule; K3 and N1 0.1 s; the INCONCLUSIVE action.

**#2**
- **E1.** Zip on /srv/shared, download now; live recording now.
- **E2.** ICE primary; EV in every table.
- **E3.** ε = 0.05 (0.02 secondary); δ = ε/2.
- **E4.** The local-date split and confirmatory sources above.
- **E5.** Gates: 90 % IDs; drop groups with ≥ 10 % gaps; ≥ 20 groups. Kill: K1 1 %; K2 10 %; K3 10 % and 1 %; N1 1 %.

**Annex: technical defaults.** Every other parameter in Sections 2–3 (constants, q_1, η, c, m_1, m_safe, the ĝ1 cap, near-miss = gap < s0 with s0 inside the safe gap, τ_q = 4 s as an assumption, latency cases, block lengths) is Claude's, disclosed in the protocol and changeable only before data. ARC-IT VS01 (#1), ST08 + ST09 (#2) replace TM20/TM21 [VERIFY version]. Boundary: #2 is vehicle-side control at signals, close to the secondary v6 line; no v6 code or data are used.

## 7. Timeline at machine speed

```
Fri 16 Oct  (a) decisions 1-2 h     (c) background, outcome-blind:
                                        NGSIM 6-23 min | Hamburg 22-92 min + filter ~15 min | live recorder
  session A: #1 protocol (b 2-3 h) -+                     +-> #1 build (b 5-8 h)   -> #1 KILL TEST (c <5 min)
  session B: #2 protocol (b 2-3 h) -+-> (a) both reviews -+-> #2 build (b 11-15 h) -> #2 KILL TEST (c minutes)
                                        one sitting, 2-4 h
  best case: #1 verdict 17-18 Oct, #2 verdict 19-21 Oct; each day of review delay adds a day
  KILL / STOP / INCONCLUSIVE: decision entry, you re-plan  |  GO: confirmatory (TGSIM; 25 Sep-end; live data)
  supervisor check for S1 runs in parallel (calendar time)
26 Oct      IV 2027 go/no-go (are 20-35 h of writing free?)
15 Nov      IEEE IV 2027 deadline: stretch target for P1
1 Feb 2027  IEEE IV 2027 workshop papers (notification 1 Mar)
1 Mar 2027  IEEE ITSC 2027: default for P1 and P2 (notification 1 May; Boston, 21-24 Sep)
Jun-Aug     thesis writing  ->  Sept 2027 submission
```

**Deadlines.** IV and ITSC 2027 dates verified on the official sites. TR-C, T-ITS: rolling, 3–6 months to a first decision [VERIFY]. TRB 2028 (~1 Aug 2027 [VERIFY]) decides after submission. Check whether your university needs accepted or submitted papers.

## 8. Risks and honest priors

**#1**
- Most likely KILL: K2 (two Californian freeways from 2005 may transfer). Fallback: NGSIM vs TGSIM (+2–3 h).
- NGSIM noise can create fake tails (Q may fire). Too few windows per regime. Rare events limit α to ~0.01–0.02. No cut-ins or reacting leaders.
- Zhou et al. 2026 (v1 28 Sep 2026) is about 2.5 weeks old; at least two groups publish on adaptive conformal safety filters (Zhiruo Zhou … Houde Liu; Hao Zhou … Wenhao Luo).

**#2**
- Gains are upper bounds: the replay ignores queues and the virtual car's own detector calls (green extension, side-street demand), which biases loss and energy.
- An EV may fail K1. IDs may have drifted since 2023. The latency model is uncertain. The Dresden group owns the data and may publish first.
- Field evidence is small: Matthes (2024, TU Dresden dissertation), cyclists in Hamburg, about 1.4 % estimated energy saving overall, with slightly more stops and waiting.

**Both**
- Your hours are the bottleneck, not compute.
- Subjective priors, not evidence: #1 passes 30–40 %, #2 25–40 %, both 10–20 %. Plan for at least one KILL; if both die, you re-plan, the bar stays.
- No "first" claims; one Scopus/IEEE Xplore search before each submission.

**Files.** Synthetic check scripts are in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/59738c75-cfe8-434e-99ee-b78b7087de37/scratchpad/wf3/final/ and /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/59738c75-cfe8-434e-99ee-b78b7087de37/scratchpad/wf3/review/. Deletion was denied, so ~205 MB of format probes remain under /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/59738c75-cfe8-434e-99ee-b78b7087de37/scratchpad/wf3/ (probe_ngsim/, probe_opara/, fc/); please delete them.
## Main-session check (2026-10-16)

- **Deadlines confirmed on the official sites:**
  - IEEE IV 2027 (Perth, 15–18 Jun 2027): conference papers 15 Nov 2026, notification 15 Jan 2027; workshop papers 1 Feb 2027.
  - IEEE ITSC 2027 (Boston, 21–24 Sep 2027): papers 1 Mar 2027, notification 1 May 2027.
- **El Halabi & Brandt (arXiv 2609.07251, 7 Sep 2026) exists:** "Adaptive Conformal Inference Under Delayed Feedback: Coverage Guarantees and a Delay-to-Memory Diagnostic". It gives a finite-sample, delay-dependent bound on long-run coverage.
  - So the delayed-feedback bound F2 is **not** a contribution here; cite their result and use it.
  - Not read beyond the abstract [VERIFY assumptions vs batched per-regime feedback].
- **How outcome-blind the agents stayed.** The workflow agents read file headers and the first rows of NGSIM and TGSIM, and the first ~100 MB of the Hamburg zip (13 Sep 2023, afternoon), for format and latency structure only. No outcome statistic was computed. 13 Sep is inside the planned throw-away block. Disclose this in the protocol.
- **The decision load is still too high for V77.** The plan lists 5 shared decisions plus 4 for #1 plus 5 for #2, and an annex. A one-line "accept defaults" answer is offered.
- **Probe leftovers:** about 205 MB under the session scratchpad `wf3/`. Deletion was blocked by permissions, and the files are left for the author to delete.
