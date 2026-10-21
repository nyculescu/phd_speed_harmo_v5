# Forensic audit of the paper_1 draft

**Paper:** "How Much Incident Information Does Mainline Metering Need? An Honest Headroom Decomposition in Microsimulation" (`papers/paper_1/paper.qmd`, repo HEAD `1e5e8d7`, last paper edit `4de404a`).
**Audit date:** 2026-10-21. **Mode:** read-only.
- No file in the repository or in the run folders was changed.
- No expensive experiment was re-run. The only simulations were 8 single SUMO spot runs of a few seconds each, run in their own systemd units after a CPU check.

**Files of this report** (all in `docs/audits/paper1_2026-10-21/`):
- this file;
- Appendix A, claim dossiers: `REPORT_appA_claims.md`;
- Appendix B, finding details with every verifier's reasoning: `REPORT_appB_findings.md`;
- Appendix C, every script and check: `REPORT_appC_scripts.md`;
- the findings-resolution register: `FINDINGS_REGISTER.md`.

**Scripts and outputs** are in `~/work/phd/v5b1_runs/audit_paper1_2026-10-21/` (copied from the session's tmpfs scratch folder on 2026-10-21, V131).
- Paths written as `audit/<dir>/...`, or as `/tmp/claude-1000/.../scratchpad/audit/<dir>/...` in the agents' records, map to `~/work/phd/v5b1_runs/audit_paper1_2026-10-21/<dir>/...`.
- Caches over 10 MB and extracted code were not copied. `EXCLUDED_CACHES.txt` there lists them and says how to regenerate them.

---

## 0. How the audit was done and how to read it

### 0.1 Method

The audit was organised as one main session plus 93 agents in three rounds: 48 in round 1, 38 in round 2 and 7 in round 3.

```
 Round 1                                Round 2                         Round 3
 ───────                                ───────                         ───────
 9 domain tracers ─┐                    14 unverified groups ─┐         3 new major groups
  PLANT  CTRL  S1  │                     2-3 skeptics each     │         2 skeptics each
  S23  C1  PROV    ├─► 123 findings      (reproduce / defend / │        + 1 gap follow-up
  REPRO LIT TEXT   │    merged into      impact lens)          │          (rate floor,
 1 BLIND re-deriv. ┘    83 groups        5 gap follow-ups      ├─► critic 2    actuation lag)
   of the headline      │                (crawl mechanism,     │    │
   numbers              ▼                junctions, physics,   │    ▼
                   30 skeptics on the    clearance rows,       │   1 follow-up
                   major/critical ones   citations)            │   (verdict conflicts)
                   5 re-checks of every
                   CONTRADICTED verdict
                   critic 1 ─► 1 follow-up (drain / co-metrics)
```

The rules every agent followed:
- **Primary evidence only.** Code at the commit that actually produced the data (`93ba655` for P1b, `e7dd561` for C1), raw per-run files in `~/work/phd/v5b1_runs/`, protocol text, and source papers. Results notes, earlier verification logs and decision records were treated as *claims*, not as proof.
- **Independent recomputation.** Every number was recomputed with fresh numpy code that does *not* import the project's `v5b` package, so a bug in `v5b` could not be reproduced silently. One agent (HEADLINE) worked *blind*: it computed the headline numbers before it was allowed to look at the reported values.
- **Adversarial verification.** Each major or critical finding was attacked by separate agents:
  - *reproduce*: re-derive the fact;
  - *defend*: argue as the author would;
  - *impact*: what changes in the paper if the finding is true.
- **Completeness critics.** Two critic agents looked for claims, failure modes and sources that nobody had checked; their gaps became follow-up tasks.
- **Main-session spot checks.** I also checked several items myself (list in §4.8).

### 0.2 Verdicts, basis and severity

| Verdict | Meaning |
|---|---|
| **VERIFIED** | Independently checked against primary evidence, and it matches *as written*. |
| **PARTIALLY SUPPORTED** | The numbers or core fact are right, but the wording overstates something or omits a material caveat; or only part of the claim could be checked. |
| **UNVERIFIED** | The evidence could not be found or checked within the read-only rules. |
| **CONTRADICTED** | The evidence shows the claim is false as written. |

*Basis* records how a verdict was reached:
- direct observation (seen in code, data or a source);
- derived (computed);
- assumption (taken from a document without a check);
- speculation.

| Severity | Meaning |
|---|---|
| **critical** | Would overturn or materially change a headline result (S1a/S1b verdicts, C1, Table II), **or** is a false statement about pre-registration or data integrity. |
| **major** | A paper statement is false or unsupported as written, or a methodological flaw or undisclosed deviation that a reviewer would require fixing; the headline survives. |
| **minor** | Wording, a small inconsistency, a missing detail. |
| **info** | Observation only. |

**Reconciliation rule.** When several agents gave a claim different verdicts:
1. A verdict based only on 'assumption' is dropped if an evidence-based one exists.
2. The most conservative of the rest is kept, in the order CONTRADICTED < PARTIALLY SUPPORTED < VERIFIED.

Every verdict from every agent remains visible in the matrix (§5) and in Appendix A. For finding severity:
- with 3 votes, I use the median vote;
- with 2 votes, the lower of the two;
- in 4 cases I overrode the rule, with the reason given in §6.

**What "VERIFIED" does *not* mean.** It means the paper's statement matches what was implemented and measured. It does not mean the simulated plant is realistic, or that the result generalises beyond this plant.

---

## 1. Bottom line

```
 ┌───────────────────────────────────────────────────────────────────────────────┐
 │ 1. DATA AND NUMBERS                                          ✔ SOLID           │
 │    All numbers in Table II, the C1 sentence, Fig. 2 and Fig. 3 reproduce       │
 │    exactly from 345,952 raw runs: 2 independent re-derivations + 1 blind one.  │
 │    4 SUMO re-runs are bit-identical. 99 unit tests pass. No data leakage.      │
 │    Every run carries its run commit; result JSONs are byte-identical to raw.   │
 ├───────────────────────────────────────────────────────────────────────────────┤
 │ 2. PRE-REGISTERED VERDICTS                                   ✔ CORRECT         │
 │    S1a FAIL · S1b PASS (slow_q2000, block_q1600) · C1 CONFIRMED, computed      │
 │    exactly as the protocols say.                                               │
 ├───────────────────────────────────────────────────────────────────────────────┤
 │ 3. WHAT THE TEXT SAYS                                        ✗ NEEDS FIXING    │
 │    False as written: "all statements were pre-registered before any data";     │
 │    "13.3 %" (a stale P1 number); the Table II caption's sign; N = "constant    │
 │    rate"; AD-ALINEA cited to the wrong paper; the promise to report wrong-type │
 │    and false-alarm tolerance and the incident-free cost (data exist, not       │
 │    shown).                                                                     │
 │    Undisclosed: the earlier P1 round; the post-hoc choice of the C1 cell;      │
 │    the post-data spill proxy; plant origin (Flow / Vinitsky 2018).             │
 ├───────────────────────────────────────────────────────────────────────────────┤
 │ 4. WHAT THE NUMBERS MEAN                                     ⚠ NARROWER THAN   │
 │                                                                THE FRAMING     │
 │    S1b "type pays": the size depends on how ID was tuned (other reasonable     │
 │    type-blind rules give 0-3 % in block_q1600) and on an uncontrolled drain    │
 │    after 940 s (83 % of the slow_q2000 gain); on the pre-registered TTT        │
 │    co-metric no cell reaches 10 %.                                             │
 │    C1 is robust across metrics (delay 16.2 %, window TTT 11.7 %, full TTT      │
 │    13.8 %), but:                                                               │
 │    - its comparator PI is Pareto-dominated, on two grid edges, and not the     │
 │      strongest always-on arm (FB);                                             │
 │    - the gain arises because the no-lane-change crawl lane fills PI's          │
 │      detector, so PI holds all 4 lanes at a 200 veh/h floor (135-s reds);      │
 │    - it reverses for incidents shorter than ~230 s;                            │
 │    - with 20 % wrong-type errors it is gone vs FB.                             │
 └───────────────────────────────────────────────────────────────────────────────┘
```

**In plain words.** The engineering is careful and the arithmetic is right. A reviewer who re-ran your code would get your numbers. What does not hold up is part of the *story* the text tells around the numbers:
- The paper says everything was fixed before any data. In fact this was the fourth round of experiments on the same plant and cells (D2 → P1 → P1b → C1), and each round was designed after seeing the previous one. Each round's own statements *were* fixed before its own data, which is good practice; the paper must say this accurately.
- "Knowing the type adds 11.8 % / 22.0 %" measures the type plan against one particular presence-only plan. That plan was picked by a pre-registered rule that happens to favour a weak candidate. Part of the S1b effect also lives in a phase after control has ended.
- The one confirmed result (C1) is real in this simulator. Its mechanism, however, is specific to this plant: no lane changes, one signal across all lanes, a very low rate floor. And its comparator was not the strongest always-on controller.

None of this makes the paper unpublishable. It changes what the paper can claim (§7) and what it must disclose.

### 1.1 The 12 findings that matter most

| # | Finding | Severity | Verified by | Section |
|---|---|---|---|---|
| 1 | "All statements were pre-registered before any data" is false as worded: D1/D2 → P1 → P1b → C1 on the same plant and cells; each study pre-registered only before its own data | critical | 3/3 lenses | 6.A1 |
| 2 | S1b magnitudes depend on the pooled-median ID tuning rule; alternative type-blind rules give 0.0-2.8 % in block_q1600; the tuned (IP, ID) pair returns in only 15-23 % of tuning-seed resamples | major (raised critical) | 3/3 | 6.B1 |
| 3 | Uncontrolled drain after 940 s (meter all-green, no demand) carries 55-106 % of every headline gain; slow_q2000 S1b: 83 %, window rel 1.7 % | major | 3/3 | 6.B2 |
| 4 | Pre-registered co-metrics (served throughput, TTT) missing; on fixed-window TTT S1b has no cell ≥ 10 % (C1 holds: 11.7 %) | major | 3/3 | 6.B2 |
| 5 | C1 comparator PI is Pareto-dominated, on two grid edges, and not the strongest L0 arm (FB) | major (override) | 2 + 2 | 6.B5 |
| 6 | C1 mechanism: crawl lane fills PI's edge-4 detector; PI holds all four lanes at the 200 veh/h floor (135-s reds); no lane changes | major | 3 + 2 | 6.B3 |
| 7 | The C1/crawl gain reverses for incidents shorter than ~230 s (replicated on two seed sets; post hoc) | major | 2/2 | 6.B4 |
| 8 | Earlier P1 round omitted although the P1b addendum says "both are reported"; in P1, IP vs PI in the C1 cell was −0.7 % | major | 2/2 | 6.A2 |
| 9 | Pre-registered outputs not reported: clean-day cost, false-alarm cost, p*, f*, c*, combined row; the omitted rows are the unfavourable ones (p* = 0.21 vs FB in the C1 cell) | major | 2 + 2 | 6.A3 |
| 10 | Text errors: "13.3 %" stale P1 value; Table II caption sign inverted; N is a feedback law at q2000 | major | 2/2 each | 6.D |
| 11 | "No vehicle crossed on red" is enforced by non-physical SUMO forced stops (about 26 m/s²); 12.8 % of runs contain them | major | 2/2 | 6.C2 |
| 12 | Plant and FB baseline taken from Flow / Vinitsky et al. 2018, not cited; AD-ALINEA cited to the wrong Smaragdis paper | major | 2/2 each | 6.D |

---

## 2. Big picture

### 2.1 Research objective

The research question (paper line 67): *how much incident information does a mainline meter need, beyond strong always-on feedback?* The paper splits "information" into a ladder and asks what each rung is worth.

```
  L0  always-on (no incident info)   N, FX, FB, PI, AD   one law, tuned once on pooled incident runs
  L1a presence (ID)                  knows onset (and clearance), not type → one plan for both types
  L1b type (IP)                      knows onset, clearance and type      → one plan per type
  L2  per-incident hindsight         best of 120 actions for each seed    → bracket [ORX_4 , OR_in]
```

### 2.2 Hypotheses (pre-registered statements) and their status

| Statement | Question | Decision rule (protocol) | Pre-reg. verdict | Reproduced | Robustness after audit |
|---|---|---|---|---|---|
| **S1a** | Does presence pay? | R(ID, r) for every L0 arm r: (a) in a common cell, rel ≥ 10 % and median-difference CI lower bound > 0, at level 0.99375; (b) rel ≥ −5 % in every cell | **FAIL** | yes, exactly | FAIL is robust. The wording "no detected gain ≥ 10 %" holds only for the pooled-median ID: with other type-blind ID rules, ID beats FB/PI by 13.7-18 % in crawl-1600, and S1a then fails only through (b) in slow_q1600 |
| **S1b** | Does the type pay over presence? | R(IP, ID) | **PASS** (slow_q2000 11.8 % [5.8, 16.7]; block_q1600 22.0 % [8.8, 31.4]) | yes, exactly | Moderately robust: PASS in ~74 % of tuning-seed resamples. Magnitudes fragile: ID rule, drain, window TTT (see 6.B1-B2) |
| **S2** | How much more would per-incident hindsight give? | bracket [y, x]; the plateau test must hold to give a point value | brackets only; plateau failed in all cells | yes | The plateau criterion (CI width ≤ 2 points) was unattainable at n = 100; the bracket mixes estimands (mean vs median) and levels |
| **S3** | How much imperfect detection is tolerated? | d*, c*, p*, f*(π), combined row (descriptive) | values computed | yes | The paper reports d* only; p*, f* and the combined row are unfavourable |
| **C1** | Does IP beat always-on PI in block_q1600 on fresh seeds? | rel ≥ 10 % and 95 % CI lower bound of median(PI − IP) > 0, in both views | **CONFIRMED**: 16.2 % [7.3, 23.7], 41.4 s/veh [16.6, 65.7] | yes, exactly + 4 bit-identical SUMO re-runs | Robust across metrics. Narrow in meaning: comparator, mechanism, duration, floor (6.B3-B5) |

### 2.3 System architecture (what was simulated)

```
 x (m):  0            100                       410          ~550                 ~830        ~965
         ├── edge 1 ──┼──────── edge 2 ─────────╫── edge 3 ──┼────── edge 4 ───────┼── edge 5 ──┤
 lanes:      4                   4              ║     4      │  2 (4_0, 4_1)       │  1 (5_0)   │ exit
                         queue storage 410 m    ║            │ 3_0,3_1 → 4_0       │ 4_0,4_1→5_0│
                         (tail never passed     ║ SIGNAL     │ 3_2,3_3 → 4_1       │            │
                          368.7 m; overflow =   ║ node 3     │ [CRAWL: lane 4_1    │[SLOWDOWN:  │
                          unlimited insertion   ║ GGGG/yyyy/ │  at 1 m/s, 240 m]   │ edge 5 at  │
                          backlog)              ║ rrrr       │                     │ 5 m/s]     │
                                                             └ detector: vehicle count on edge 4 (both lanes),
                                                               0.5-s snapshot; PI '_e5' laws use edge 5
 Lane changing: OFF (lcStrategic = −1). Lanes merge only at zipper junctions (about 40-m internal lanes).
 Vehicles: IDM (a = 1, b = 1.5 m/s², T = 1 s, s0 = 2 m), 90 % 'human' (speedFactor ~N(1, 0.2)), 10 % 'av' (factor 1).
 Geometry and the FB meter come from the Flow / Vinitsky et al. (2018) bottleneck (code docstrings).
```

```
 Control loop (every 1-s tick; the law updates every 30 s on a grid anchored at t = 40 s)
 ─────────────────────────────────────────────────────────────────────────────────────────
 Poisson demand q ∈ {1600, 2000} veh/h on [0, 940) s
        │
        ▼
 queue on 4 lanes ──► SIGNAL: cycle c(r) = max(11, 28 800 / r) s, 6 s green, 3 s amber, ≥ 2 s red
        ▲                        r = commanded rate, clipped to [200, 2618] veh/h
        │                        (r = 200 → c = 144 s → 135 s of red on all 4 lanes)
 controller ◄── n(k) = vehicles on edge 4
   N  : best of G (20 constants + 30 FB laws) on clean days     q1600: c1800    q2000: f10_8 (feedback)
   FX : best constant on pooled incident runs                   c2600 / c2000
   FB : r(k) = r(k−1) + K_F (n_crit − n(k))                     f40_10 / f20_12
   PI : r(k) = r(k−1) − K_P (n(k) − n(k−1)) + K_I (n_crit − n(k))   p70_120_8_e4 / p20_20_14_e4
   AD : FB + sign-rule set-point adaptation (own rule, not AD-ALINEA's estimator)
   ID : N until onset, then 1 action of A (pooled over types)   f40_10 / p20_20_14_e4
   IP : N until onset, then 1 action of A per type
        q1600 slow c1000+back, block p20_20_16_e4; q2000 slow p70_40_8_e4, block p20_20_14_e4
   A  : (G ∪ 10 best always-on PI laws) × {stay, back} = 120 actions
 t = 940 s: meter → all-green, demand stops, network drains with NO control (cap 7200 s)
 metric: mean over vehicles of (departDelay + timeLoss) from SUMO tripinfo
```

### 2.4 The research process that produced the data (timeline, machine time UTC−7)

```
 2026-10-19
  00:06  D1 screen data (BN4 plant)
  10:24-11:38  D2 screen data  ── same plant, same 4 cells (slow/block × 1600/2000)
  13:38  P1 protocol drafted → 14:12 approved → 16:32 amended after smoke runs
  17:07-18:42  V100 meter-phase bug found → D1 and D2 re-run
  18:42  P1 launched → 18:51 aborted by a mid-run docs commit → 19:06 resumed from a frozen worktree
  21:13 → 03:17 (10-20)  P1 evaluation (296,527 runs; no amber; A without PI-law plans)
 2026-10-20
  06:44  P1 verified; its limits (no amber, no PI-law plans) motivate P1b
  09:42 → 09:51  P1b addendum drafted and approved (amber, PI-law plans, rate clip, runner rows)
  10:38 → 20:28  P1b runs (344,852; evaluation sentinel 13:07:53, code 93ba655)
  20:31  P1b results → 21:03 verified
  21:09 → 21:11  C1 protocol drafted and approved: cell block_q1600 and comparator PI chosen from P1b results
  21:16  C1 code (e7dd561) → 21:27:50-21:29:00 C1 run (1,100 runs, seeds 7,400,700-799)
  22:03  paper drafting starts
```

### 2.5 How methods connect to conclusions, and where the chain can break

```
 protocol page ─► tuning on 40 seeds ─► frozen arms ─► 100 evaluation seeds ─► paired rel + bootstrap ─► rule ─► verdict ─► paper sentence
  (hash ✔)         (pooled-median rule;   (✔ no        (✔ fresh, paired;      (✔ exact; CI covers   (✔)     (✔)       (✗ several)
                    grid edges ⚠)         leakage)      drain convention ⚠)    evaluation noise only ⚠)
     ▲                 ▲                                    ▲                                                          ▲
  sequential        selection noise and                 plant artefacts: crawl without lane changes,           wording, omissions,
  design (D2→P1→    a weak ID / PI choice               200 veh/h floor, forced stops, q2000 oversaturated     stale numbers
  P1b→C1) ⚠
```

The numerical chain is sound. The weak links are at the two ends:
- **Upstream:** how the arms were selected, and how the sequence of studies was designed.
- **Downstream:** what the text claims and discloses.

The plant model is a further source of fragility *in the middle*.

---

## 3. Implementation: what the code does, intended versus verified

The code that ran is `93ba655` (P1b) and `e7dd561` (C1). Between them, the only change under `v5b/` is the new `confirm_c1.py`, and `v5b/` and `tests/` have not changed since `e7dd561`.

| Component | Paper says (line) | Code does (verified) | Status |
|---|---|---|---|
| Network | 4/4/4/2/1 lanes; one signal across 4 lanes upstream of the lane drop (110) | Exactly so (`v5b/d1/netgen_bn4.py@93ba655:22-34`; cached `bn4.net.xml`). Rebuilt from scratch: identical | ✔ |
| Origin of plant | not stated | Flow / Vinitsky et al. 2018 bottleneck, geometry copied (docstring `netgen_bn4.py:1-11`) | ✗ not cited |
| Lane changing | disabled (110) | `lcStrategic = −1`, other lc parameters 0; random depart lane, so the 4 lanes are 4 fixed queues and about half the vehicles must use lane 4_1 | ✔ as stated; consequences undisclosed |
| Demand | constant q (110) | Poisson arrivals at rate q on [0, 940) s; count varies by seed (SD about 20); **stops at 940 s** | ⚠ partially |
| Vehicles | "drivers" (149) | IDM; 10 % 'av' vType (speedFactor 1, no deviation) | ✗ not stated |
| Timeline | 40-s warm-up, 900-s control, until empty (110) | Same; **at 940 s the meter goes all-green and stays off**; drain capped at 7200 s (all runs drained) | ⚠ drain convention undisclosed |
| Signal | 6 s G, 3 s A, ≥ 2 s R; c(q) = max(11, 28 800/q) (110) | Same, but c uses the **commanded rate r**, not demand q | ⚠ notation |
| Rate limits | [200, 2618] veh/h (110) | Same (`v5b/p1b/meters.py@93ba655:31`). The 200 floor gives a 144-s cycle and 135-s reds; it is a code default inherited from the archive FBMeter; the protocol records only its consequence (red ≤ 138 s) | ⚠ consequence and rationale undisclosed |
| Amber behaviour | obey unless cannot stop comfortably (149) | SUMO `tls.yellow.min-decel` 3 m/s² (twice b). A vehicle that cannot stop before red is **forced to an instantaneous stop at the line** (implied about 26 m/s², overshoot up to 11 m): 44,816 events in 11.8 % of P1b runs | ⚠ non-physical |
| Runners | s ∈ {10, 30} % ignore amber and first 1.5 s of red (149) | `jmDriveAfterRedTime = 1.5`; realised shares 0.1009 / 0.3011. Runners also cross *any* red when they cannot brake; they include AV-type vehicles | ⚠ broader than stated |
| Slowdown | speed limit 5 m/s at the bottleneck (114) | Edge 5 (the 1-lane bottleneck) at 5 m/s | ✔ |
| Lane crawl | one lane at 1 m/s at the bottleneck (114) | Lane **4_1 of the upstream 2-lane edge 4** at 1 m/s; fed only by lanes 3_2 and 3_3 | ⚠ "at the bottleneck" only for the whole merge zone |
| Onset / duration | U(first third of control), U(120, 480) s (114) | U(40, 340) s, U(120, 480) s from `rng(seed + 3301)`; identical across arms | ✔ |
| Delay metric | door-to-door incl. meter queue and entry (93) | mean of SUMO `departDelay + timeLoss`. timeLoss is measured against the incident-reduced speed limit (3-8 s/veh of incident time not counted; ≤ 0.8 pt effect on rel); includes the uncontrolled drain | ⚠ two undisclosed conventions |
| Detector | "downstream vehicle count" (118) | `getLastStepVehicleNumber` on edge 4 (both lanes, so it includes the crawl lane), a 0.5-s snapshot at each 30-s update | ⚠ detail matters for C1 (6.B3) |
| FB | ALINEA-style integral law on count (118) | r(k) = r(k−1) + K_F(n_crit − n(k)), clipped; = Papageorgiou 2008 eq. (1) form | ✔ |
| PI | PI-ALINEA form (118) | r(k) = r(k−1) − K_P(n(k) − n(k−1)) + K_I(n_crit − n(k)); velocity form with counts; 180 laws on e4/e5 | ✔ form; tuning on grid edges ⚠ |
| AD | FB with online set point "in the spirit of AD-ALINEA" (118) | Own sign-rule hill-climb n̂ ← clip(n̂ + η·sgn(Δφ)·sgn(Δn), 4, 20); η at the grid edge; worse than FB on tuning seeds | ⚠ weak arm; wrong citation |
| N | "best constant rate on incident-free days" (118) | Best of G (constants **and** FB laws) on clean days: c1800 (q1600), **f10_8, a feedback law** (q2000) | ✗ contradicted at q2000 |
| ID | knows onset and end (100) / "only that an incident has started" (118) | Switch at onset (t_switch = t_on in 268,854 runs); "back" actions use the clearance time. ID's chosen plan = FB's law (q1600) and PI's law (q2000) | ⚠ inconsistent text; ID = delayed L0 law |
| IP | plan per type (101) | Best action per (type, q) on tuning seeds; IP = ID in block_q2000 (identical runs) | ✔ |
| Action set A | 50 + 10 PI plans, × {stay, back} = 120 (118) | Yes; the 10 PI plans are the 10 best *always-on* PI laws on tuning seeds | ✔ count; ⚠ wording |
| OR_in | best action per seed on the evaluated run (141) | min over 120 main runs per seed | ✔ |
| ORX_R | best mean over R replicates, scored on the main run (141) | Yes; replicates use seed + k·10⁷ for demand and SUMO; same incident window | ✔ |
| TP placebo | best of 5 runs of IP (141) | min(main, 4 replicates) with demand redrawn; exploits arrival-count luck; 5 vs OR_in's 120 candidates | ⚠ not a matched placebo |
| S3 | break-even detection delays (145) | d* (onset delay), c* (clearance delay, back plans only), p* (exact per-seed mixture, not simulated misclassification), f*(π), combined row | ⚠ paper narrows S3 |
| Counters | no collisions; no red crossing without runners (197) | Collisions: lane gap check with `collision.check-junctions false` (merges unchecked). Red crossings: vehicles leaving edge 2 during red; zero for non-runners **by SUMO construction** | ⚠ scope |
| Spill | "meter queue reached the upstream entry" (197) | Post-data proxy (V109): tail within 50 m of entry OR mean depart delay > 5 s. The pre-registered B4 flag never fired | ⚠ undisclosed proxy |

**Intended versus verified.** Where the code and the paper agree, the agents confirmed the behaviour on raw data, not only by reading code. Examples:
- switch ticks were checked on all 268,854 switch runs;
- incident windows were checked on all 420 seed groups;
- runner shares, cycle durations and seed pairing were measured.

The items marked ⚠ or ✗ are cases where the code does something the paper does not say, or says differently.

---

## 4. Experimental forensics

### 4.1 Run inventory

| Study | Code | Protocol page (sha256 prefix, matches commit) | Seeds (7,400,xxx) | Runs | Failed / teleport / collision / undrained | In the paper? |
|---|---|---|---|---|---|---|
| Pilot, line-#1 screens | various | own pages | own ranges | (not counted) | n/a | no (other line) |
| D1 screen (+ V100 bug re-run) | — | D1 page `@a23613b` | 010-079, 100-119 | 1,690 + 1,690 | — | no |
| D2 screen (+ V100 bug re-run) | — | D2 page `@72ba8f2` | 080-099, 120-189 | 48,682 + 48,682 (20 teleport runs in v92) | — | no |
| **P1** (no amber; A = 100 actions) | `85f7d34` | `fed27bf6…` = `p1_incident_information.md@0e8d49b` | 200-259; eval 500-599 | 296,527 | 0 / 0 / 0 / 0 | **no**, but 2 numbers leak in (87 %, 13.3 %) |
| **P1b** | `93ba655` | `2b3d3ccb…` = `p1b_addendum.md@75bcd2b` | tool 260-279; tune 300-339; eval 600-699 | 14,550 + 75,120 + 255,182 = 344,852 | 0 / 0 / 0 / 0 | yes |
| **C1** | `e7dd561` | `8b6005aa…` = `p1b_confirm_c1.md@7c6acc8` | 700-799 | 1,100 | 0 / 0 / 0 / 0 | yes |
| Smokes, verifier re-runs | various | — | 000-009 and repeats | several thousand | — | no |

Evidence: `audit/PROV/scan_runs.py`, `audit/PROV/page_sha.sh`, `audit/REPRO/chain_integrity.py`; `journalctl --user` unit starts.

### 4.2 Pre-registration: what was fixed before which data

```
           data seen before the page was written                    page fixed before its own data?
 P1   ◄── D1, D2 screens (same plant, same cells)                    ✔ (14:12 approved, 21:13 eval)
 P1b  ◄── P1 results (no amber, no PI plans ⇒ redesign)              ✔ (09:51 approved, 13:07 eval)
 C1   ◄── P1b results (cell and comparator = best report-only row)   ✔ (21:11 approved, 21:27 run)
```

- No protocol file or decision row was edited after any run started.
- The P1 page was amended at 16:32 after smoke runs on smoke seeds only.
- The C1 page itself discloses that its cell and arms were chosen after P1b. The *paper* does not.

### 4.3 Seeds

The approved block (CLAUDE.md):

| Seeds (7,400,xxx) | Label |
|---|---|
| 000-009 | calibration |
| 010-099 | tool checks |
| 100-299 | tuning |
| 300-499 | validation |
| 500-699 | test |
| 700-999 | reserved confirmatory |

The studies used:
- P1b tool checks on 260-279, in the *tuning* label range;
- P1b tuning on 300-339, in the *validation* range;
- P1 and P1b evaluation in the *test* range (500-599 and 600-699);
- C1 in the *reserved confirmatory* range (700-799).

Main seeds are **disjoint between studies**, so every round used fresh seeds. C1's seeds appear in no earlier run directory. The label deviation is disclosed in `p1b_result.md` (V108), not in the paper.

### 4.4 Data integrity

- Every P1b and C1 run file records the run commit and `code_dirty = false`.
- Every write time lies inside its run window.
- `docs/research/results/p1b_result.json` and `p1b_c1_result.json` are **byte-identical** to the raw `result.json` files.
- 0 invalid, teleported, collided or undrained runs; every run drained with `n_trips == generated`.
- **No data leakage was found.** Every tuned choice and the G_PI list were re-derived exactly from tuning-seed runs only. The only selections on evaluation seeds are OR_in (by design), the "strongest L0" bar in Fig. 2 and the d* binding arm; both of the latter are conservative.

### 4.5 Reproducibility

| Check | Outcome |
|---|---|
| Figure scripts re-run from scratch copies (Fig. 1-3) | pixel-identical PDFs; every plotted value recomputed from raw runs |
| `paper.pdf` vs `paper.qmd` | current (built 23:21:30 from `4de404a`); every body number present |
| Unit tests at `e7dd561` (scratch copy) | 94 pure + 5 SUMO tests pass. They do not cover the figure scripts or any regression against stored raw results |
| 4 SUMO spot re-runs (C1, seeds 7,400,700 and 760, arms IP and PI) | all fields identical to the stored runs, except wall time |
| 4 SUMO runs with `--collision.check-junctions true` | identical outputs, 0 collisions |
| Network regeneration | identical to the cached network |

### 4.6 Statistical validity

**What is right:**
- paired seeds;
- the median of paired differences, as pre-registered;
- percentile bootstrap that resamples seeds jointly (B = 20,000);
- Bonferroni 0.99375 = 1 − 0.05/8 for the S1 family, valid with intersection-union logic across cells;
- both views (all seeds and valid-only) computed;
- the rule fails closed.

**What the paper should say or fix:**
1. **The CIs cover evaluation noise only, not selection noise.** IP and ID are each minima over 120 actions on 40 tuning seeds. When the tuning seeds were resampled 1,000 times:
   - the tuned (IP, ID) pair came back in only 15-23 % of resamples;
   - the median re-selected IP-vs-ID gain was 4.4 % (slow_q2000) and 12.5 % (block_q1600), against the reported 11.8 % and 22.0 %;
   - the S1b verdict still passed in about 74 % of resamples.

   Script: `audit/HEADLINE/selection_bootstrap.py`.
2. **Bootstrap Monte Carlo error at the 0.99375 tails** is up to 1.6 points across RNG seeds. This exceeds the printed precision, but no verdict changes.
3. **Rel CI vs decision CI.** The printed S1 and C1 intervals are CIs of *rel*. The decision rule uses the CI of the *median difference*. Their signs agree in 44/44 rows, but the paper should say which interval is printed.
4. **Median vs mean.** In slow_q1600, IP vs PI is +4.5 % on the median but −13.5 % on the mean. IP sometimes loses heavily there.
5. **S2 plateau criterion** (95 % CI of ORX_2 vs ORX_4 inside ±1 point) needs a CI width of 2 points or less. The achieved widths were 4.0-15.1 points, so the test could not pass at n = 100. The bracket also combines a mean-version lower bound with a median-version upper bound.
6. **C1's rule tests rel ≥ 10 % on the point estimate.** The rel CI [7.3, 23.7] includes values below 10 %.

### 4.7 Is the comparison fair?

| Issue | Effect |
|---|---|
| L0 arms and ID are tuned on a 50/50 slow/block mix; IP per type | intended by design (L0 has no type information); but a type-tuned always-on law would beat IP (6.B1) |
| PI optimum at q1600 on two grid edges (K_P = 70, K_I = 120) and Pareto-dominated by 6 PI laws | the C1 comparator is weaker than "tuned PI-ALINEA" suggests; IP still beats better PIs by 14-21 % on P1b seeds |
| IP chooses among 120 actions per type; PI among 180 laws pooled | unequal tuning freedom (info) |
| ID and IP run N before onset | costs 1.5-6.4 % against the same law run from t = 0; S1a vs PI partly built into the design (6.B1) |

### 4.8 Checks I made myself in the main session

| Check | Command or source | Result |
|---|---|---|
| Origin of "13.3 %" | search of `p1_result.json` / `p1b_result.json` | `p1_result.json /eval/S2/slow_q2000/x = 0.13309` (P1). No P1b S2 value is 13.3 |
| Tuned N, ID, PI | `p1b_result.json tune.arms` | N: c1800 / f10_8; ID: f40_10 / p20_20_14_e4; PI: p70_120_8_e4 / p20_20_14_e4 |
| Drain convention | `git show 93ba655:v5b/p1b/episode.py` lines 228-256 | `plant.set_all_green()`, then `sim.drain(...)`; delay from tripinfo after the drain |
| Rate floor | `git show 93ba655:v5b/p1b/meters.py` line 31 | `Q_MIN, Q_CAP = 200.0, 2618.0`; P1 protocol line 187 notes "a red never exceeds c(q_min) − green = 138 s" |
| Floors in the cited source | `pdftotext` of Papageorgiou et al. 2008 | q_min = 4,500 veh/h at q_cap ≈ 10,500 (toll plaza); 1,000 veh/h at q_cap ≈ 2,300 (work zone): about 43 % of capacity |
| Table II caption sign | paper lines 145 and 165 | Line 145 defines rel so that positive favours t (the first-named arm, as in R(IP, ID)); the caption says "the second arm" |

---

## 5. Claim-evidence matrix

One row per substantive claim in `paper.qmd`. "Final verdict" applies the reconciliation rule of §0.2; "Verdicts by source" lists every agent verdict (R1/R2 = round, then agent label). Full Meaning / Evidence / Verification / Failure points for every claim and every source are in Appendix A.

Final verdicts over 86 claims: VERIFIED: 35, PARTIALLY SUPPORTED: 44, UNVERIFIED: 1, CONTRADICTED: 6.

| ID | Line | Claim (paper, abridged) | Final verdict | Why (reconciled) | Key evidence | Verdicts by source |
|---|---|---|---|---|---|---|
| C01 | 63 | Non-recurring events (crashes, breakdowns, lane blockages) reduce freeway bottleneck capacity at unpredictable times; currently marked [CITE needed]. | **UNVERIFIED** | Still a [CITE] placeholder. Two candidate sources with verified metadata (Knoop et al. 2008; Skabardonis et al. 2003); their full texts were not read. | papers/paper_1/paper.qmd:63 \citeneeded{non-recurrent congestion share / capacity drop}; macro defined at pap…; Candidate A (metadata verified on Crossref, abstract read on OpenAlex): Knoop, Hoogendoorn & van Zuylen 2008,… | R1 LIT: UNVERIFIED |
| C02 | 63 | Mainline metering regulates flow with signals across all lanes of the freeway upstream of a bottleneck; studied for lane drops at work zones and toll plazas [Papageorgio… | **VERIFIED** | Papageorgiou 2008 (full text, local PDF) covers toll plazas and work zones; Spiliopoulou 2010 and Tympakianaki 2014 were checked by abstract only. | Papageorgiou 2008 full text (papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf), §3.1 p. 543: toll plaza w…; Papageorgiou 2008 §4.1 p. 548: work zone, 3 lanes into 1; the example 'assumes that all upstream lanes are si… | R1 LIT: VERIFIED; R2 G8: VERIFIED |
| C03 | 63 | ...and for merges that combine mainline and ramp signals [Ghiasi2018; Hale2020]. | **VERIFIED** | Supported at abstract / landing-page level (Ghiasi 2018, Hale 2020); full texts not read. | Ghiasi 2018 abstract (OpenAlex): 'a dynamic signal control algorithm for an integrated ramp and mainline mete…; Hale 2020, FHWA-HRT-20-008, May 2020 (FHWA landing page fhwa.dot.gov/publications/research/operations/20008):… | R1 LIT: VERIFIED |
| C04 | 65 | For a known, stationary bottleneck, integral laws such as ALINEA [Papageorgiou1991] and PI extensions such as PI-ALINEA [Wang2014] keep the bottleneck near its critical… | **VERIFIED** | ALINEA law confirmed via the Papageorgiou 2008 full text (same first author, cites 1991). The 1991 original and the Wang 2014 full text were not read. | TRID 365587 (Papageorgiou, Hadj-Salem & Blosseville 1991, TRR 1320:58-64): 'ALINEA is a simple, robust, flexi…; Papageorgiou 2008 full text §2.7.1 p. 540, eq. (1): q(k) = q(k-1) + K_R[o_hat - o(k-1)]; p. 541: in steady st… | R1 LIT: VERIFIED |
| C05 | 65 | The same laws drive mainstream traffic flow control with variable speed limits [Carlson2010; Carlson2011] and remain strong benchmarks [Frejo2021b]. | **PARTIALLY SUPPORTED** | Carlson2010 is model-based optimal control, not "the same laws". The feedback MTFC benchmark Frejo uses is Carlson et al. 2014 (not cited). Carlson2011 not read in full. | Carlson 2010 (EPFL Infoscience 154946 abstract): uses a tool for 'optimal integrated motorway network traffic…; Carlson 2011 abstract (OpenAlex): 'A simple local MTFC feedback controller is designed in this paper'; 'no on… | R1 LIT: PARTIALLY; R2 G8: PARTIALLY |
| C06 | 65 | Set-point adaptation [Smaragdis2003] tracks slow changes in the bottleneck without an incident detector. | **CONTRADICTED** | Concept right, citation wrong: AD-ALINEA (online set-point estimation) is Smaragdis, Papageorgiou & Kosmatopoulos 2004 (TR-B 38(3)); the cited 2003 abstract covers other ALINEA extensions. The 2003 full text could not be read legally. | Smaragdis2003 abstract (Crossref and OpenAlex, TRR 1856:74-86): 'the following new local ramp metering strate…; Smaragdis, Papageorgiou & Kosmatopoulos 2004, TR-B 38(3):251-270, doi:10.1016/S0191-2615(03)00012-2 (IDEAS ab… | R1 LIT: CONTRADICTED; R1 recheck (LIT): CONTRADICTED; R2 G8: CONTRADICTED |
| C07 | 65 | Incident-responsive ramp metering switches or schedules the controller when an incident is reported [Sheu2007; Dabiri2014; Wu2014], usually compared with no control or w… | **PARTIALLY SUPPORTED** | Sheu 2007 detects incidents itself; Dabiri 2014 schedules gains continuously on estimated incident magnitudes (no plan switch on a flag); Wu 2014 full text unreachable. "Usually compared with no control or a fixed-parameter controller" holds for 2 of 3 cited works; as a generalisation it is unsupported. | Sheu2007 abstract (OpenAlex): 'identification of control-zone-based congestion patterns using the modified ge…; Dabiri2014 abstract (research.chalmers.se/publication/211200): 'The main idea is to use local freeway control… | R1 LIT: PARTIALLY; R2 G8: PARTIALLY |
| C08 | 67 | An incident-aware meter needs a detection and classification system, which adds delay and errors; research question: how much incident information does a mainline meter… | **PARTIALLY SUPPORTED** | Matches the protocol question, but "adds delay and errors" is uncited and the answer covers one plant with perfect detection in the main rows. | papers/paper_1/paper.qmd:67 (no citation on 'adds delay and errors'); docs/research/protocols/p1_incident_information.md:5-11 (paper question; robustness to detection imperfection… | R1 TEXT: PARTIALLY |
| C09 | 69 | One microsimulated bottleneck with a four-lane mainline signal in SUMO [Lopez2018]. | **VERIFIED** | One BN4 bottleneck, one signal across 4 lanes, SUMO 1.27.1. The geometry and the FB meter come from Flow / Vinitsky et al. 2018, which is not cited (LIT-F3). | v5b/d1/netgen_bn4.py@93ba655:22-34 (SPEC: nodes, edges 4/4/4/2/1, node 3 traffic_light); :58-66 connections;…; ~/work/phd/v5b1_runs/_netcache/bn4_e578788201/bn4.net.xml: junction 3 type traffic_light, incLanes 2_0..2_3,… | R1 PLANT: VERIFIED |
| C10 | 69 | Hindsight gains are inflated when the best plan is selected on the same noisy runs used for evaluation [Smith2006; Cameron2016]; so we bracket them between an in-sample… | **VERIFIED** | Smith & Winkler 2006, Cameron 2016 and van Hasselt 2010 support the bias argument; their results concern expectations, while the paper reports medians (LIT-F10). | Smith & Winkler 2006 abstract: 'we should expect the value of the chosen alternative to be less than its esti…; Cameron et al. 2016 full text (author copy cs.ubc.ca/~cchris13/docs/ijcai16_bias.pdf), abstract: 'this flawed… | R1 LIT: VERIFIED |
| C11 | 69 | All statements were pre-registered before any data were produced. | **CONTRADICTED** | Each study (P1, P1b, C1) was pre-registered before its own data (page hashes match). But P1b was redesigned after P1 data, C1 (cell, arms, comparator) was fixed after P1b data, and the D1/D2 screens ran first on the same plant and cells. "Before any data" is false as worded (PROV-F1). | P1 data: ~/work/phd/v5b1_runs/p1/v99/run.log lines 1-519 (2026-10-19 18:42 to 2026-10-20 03:17); p1b_addendum.md@75bcd2b:5-9 ('P1 stays in the record as the earlier run ... Why: ... V105 amber necessary; co… | R1 PROV: CONTRADICTED; R1 recheck (PROV): CONTRADICTED |
| C12 | 73 | Contribution 1: an information-ladder decomposition for incident-responsive mainline metering against a full set of tuned always-on controllers, including a PI law. | **PARTIALLY SUPPORTED** | The L0 set is N, FX, FB, PI, AD. PI at q1600 sits on two grid edges and is Pareto-dominated; FX is at the top rate (barely meters); AD is weak; no MPC/MTFC arm. "Full set of tuned" overstates. | paper.qmd:118, 126-136 (Table I), 174-179 (Table II); docs/research/protocols/p1_incident_information.md:29-46 (arms; grid edges 'reported for every arm ... No fur… | R1 TEXT: PARTIALLY |
| C13 | 74 | Contribution 2: honest bounds on the value of per-incident hindsight under simulation noise, with pre-registered statements, paired seeds and a confirmation on fresh see… | **PARTIALLY SUPPORTED** | The S2 bounds are computed as described, but C1 confirms only IP vs PI, not the bounds; pre-registration holds per study only (C11). | docs/research/protocols/p1_incident_information.md:105-110 (S2 rules; x = upper CI of the median rel vs OR_in…; p1b_result.json eval.S2.*.statements (x, y; level 0.9875); all 4 cells, plateau failed | R1 TEXT: PARTIALLY |
| C14 | 75 | Contribution 3: the sensitivity of the gains to detection delay and to red-light running at the meter. | **PARTIALLY SUPPORTED** | d* and the C1 delay/runner rows are correct. "Detection delay" is onset delay only (clearance perfect); the pre-registered c*, p*, f* and combined row are omitted, and they are the unfavourable rows. | paper.qmd:179 (d* row, no CIs), 187, 197; p1b_result.json eval.S3.*.d_star.all_seeds (slow_q2000 120.4 [20.1, 168.5]; slow_q1600 2.6 [0, 7.1]; block_q1… | R1 TEXT: PARTIALLY; R2 G5: PARTIALLY |
| C15 | 81 | A mainline meter holds traffic upstream with green, amber and red signals across all lanes; feedback laws developed for ramp metering apply directly [Papageorgiou2008; T… | **PARTIALLY SUPPORTED** | "Apply directly" is supported by Papageorgiou 2008 (which also reports tuning was needed). "Green, amber and red" is not: the cited works use green-red signals; the amber is this study's own design. | Papageorgiou 2008 §2.7.1 p. 540: 'This is the central task of the control algorithm that is essentially ident…; Papageorgiou 2008 §3.1 p. 543: 'Each traffic light has a constant green phase of 4 s'; 'The red phase is not… | R1 LIT: PARTIALLY |
| C16 | 81 | ALINEA integrates the deviation of a downstream measurement from its critical value [Papageorgiou1991]; PI-ALINEA adds a proportional term that helps when the bottleneck… | **VERIFIED** | ALINEA (via the 2008 full text) and PI-ALINEA (Wang abstract plus two secondary full texts) as described. | Papageorgiou 2008 §2.7.1 pp. 540-541 (citing Papageorgiou et al. 1991): eq. (1), and 'The regulator (1) appar…; Wang 2014 abstract: 'ALINEA may lead to a poorly damped closed-loop behavior in this case, but PI-ALINEA, whi… | R1 LIT: VERIFIED; R2 G8: VERIFIED |
| C17 | 81 | When an incident changes the bottleneck a fixed set point may no longer fit; adaptive schemes estimate it online [Smaragdis2003]; incident-scheduled controllers switch p… | **PARTIALLY SUPPORTED** | Smaragdis citation wrong (see C06). Dabiri is continuous gain scheduling on estimated incident parameters, not a plan switch on a flag. | Same Smaragdis 2003 and 2004 evidence as C06: the 2003 abstract has no adaptive strategy; the 2004 abstract i…; Dabiri 2014 abstract: control 'triggered by available incident parameter values'; the incident parameters 'ca… | R1 LIT: PARTIALLY; R2 G8: PARTIALLY |
| C18 | 85 | We report how long detection may take, and how often the type may be wrong or a false alarm occur, before the gain disappears. | **CONTRADICTED** | Only the onset-detection break-even d* is reported. The promised misclassification (p*) and false-alarm (f*) results are absent, although they are in p1b_result.json and A10 lists p* and f* as paper outputs. They are unfavourable: in the C1 cell the lead over FB is gone at p = 0.21. | paper.qmd:145 (S3 reduced to 'break-even detection delays'), :179 (d* only); p1b_result.json eval.S3.*.p_star: slow_q1600 0.13 [0, 0.30] PI; slow_q2000 0.53 [0.21, 0.89]; block_q1600 0.2… | R1 TEXT: PARTIALLY; R2 G5: CONTRADICTED |
| C19 | 85 | Field evaluations of ramp and work-zone meters report non-compliance at red [TOPS2005; Sun2013]. | **VERIFIED** | TOPS 2005 report (full text) and the Sun et al. companion report/thesis report red non-compliance; the cited TRR article itself was not reachable. TOPS2005 bib author is wrong (LIT-F9). | TOPS 2005 full text (files.topslab.wisc.edu/its/rampmetering/madison_beltline_meter_eval.pdf), §2.4: 'Vehicle…; Sun 2013 abstract: 'The compliance analysis showed that noncompliance could be a major safety issue in the de… | R1 LIT: VERIFIED; R2 G8: VERIFIED |
| C20 | 85 | We model the amber phase explicitly and add red-light runners as a sensitivity row. | **VERIFIED** | Amber state and runner rows exist in code and data (realised runner shares 0.1009 / 0.3011). | v5b/p1b/meters.py@93ba655:29-34 GREEN 6, AMBER 3, STATES y='yyyy'; :41-42 state_of; :127-128 setRedYellowGree…; v5b/p1b/runners.py@93ba655:15-16 RUNNER_JM, SHARES (0.10, 0.30); :39-52 apply_runners | R1 PLANT: VERIFIED |
| C21 | 89 | In-sample oracle selection is the optimizer's curse [Smith2006] and the virtual-best-solver bias [Cameron2016]; selecting on one set of runs and evaluating on another re… | **VERIFIED** | Full texts of Cameron 2016, van Hasselt 2010 and Smith & Winkler 2006 read; statements concern expectations. | The C10 sources; van Hasselt 2010 full text §2: 'The double estimator underestimates because the probabilities P(j = a*) sum t… | R1 LIT: VERIFIED |
| C22 | 93 | Constant demand q approaches a bottleneck where four lanes reduce to one; a single signal across the four mainline lanes releases vehicles at a commanded rate; the queue… | **PARTIALLY SUPPORTED** | Demand is a constant-rate Poisson stream that stops at 940 s; realised discharge is below the commanded rate (FX 25-46 % lower); on-road storage ends at about 369 m, beyond which the queue is an unlimited insertion backlog; with lane changing off the four lanes are four fixed queues. | netgen_bn4.py@93ba655:27 edges 4/4/4/2/1; p1b/meters.py@93ba655:37-38 cycle_s = max(11, 2*4*3600/q) | R1 PLANT: PARTIALLY |
| C23 | 93 | An incident of random type, onset and duration may occur at the bottleneck. | **PARTIALLY SUPPORTED** | Onset and duration are random as stated. The type is a design factor (both types run on every seed, analysed per cell), and the crawl acts on lane 4_1 of the 2-lane edge, not on the 1-lane bottleneck. | v5b/d2/incidents.py@93ba655:34-39 incident_window rng(seed+3301): onset U(t_ctrl0, t_ctrl0+300), duration U(1…; v5b/p1b/analysis.py@93ba655 cells: every seed is run under both types (slow, block), and results are reported… | R1 PLANT: PARTIALLY |
| C24 | 93 | The objective is the door-to-door delay per vehicle, including the time spent waiting in the meter queue and at the network entry. | **PARTIALLY SUPPORTED** | Delay = SUMO departDelay + timeLoss, which does include origin and meter waits. But timeLoss is measured against the incident-reduced speed limit (3-8 s/veh of incident time not counted; <= 0.8 pt effect), and the metric includes the uncontrolled all-green drain after 940 s, which carries 55-106 % of the headline gains (DRAIN). | v5b/p1b/episode.py@93ba655:253-255 delays = departDelay + timeLoss from tripinfo; valid requires all trips; SUMO v1_27_1 src/microsim/MSVehicle.cpp:4295-4304 updateTimeLoss uses vmax = myLane->getVehicleMaxSpeed(this)… | R1 PLANT: PARTIALLY; R1 FU1 (FU1-C1): PARTIALLY |
| C25 | 95 | Fig. 1 schematic: four lanes reduce to two and then to one; one mainline signal across all four lanes; two incident types (the drawing must match the simulated geometry). | **PARTIALLY SUPPORTED** | Topology, signal and incident lanes are drawn correctly. Incidents are drawn as local zones although they cover the whole edge or lane; the crawl-lane feed (3_2, 3_3 -> 4_1) is not shown; labels overlap. | papers/paper_1/figures/fig_plant.py@HEAD:14 edges (0,3,4),(3,6,4),(6,9,4),(9,12,2),(12,15,1); :24 signal at x…; v5b/d1/netgen_bn4.py@e7dd561:22-34 (nodes 1..6, node 3 traffic_light at x=410; edges lanes 4,4,4,2,1), :58-66… | R1 REPRO: VERIFIED; R2 G2: PARTIALLY |
| C26 | 99 | L0: the meter runs one always-on law (a constant rate or feedback), tuned once. | **VERIFIED** | L0 arms run one always-on law, tuned once per q on pooled incident runs (all 5 re-derived from tuning seeds). | v5b/p1b/analysis.py@93ba655:119-131 fit_fixed (N, FX, FB, PI), :149-154 fit_ad; v5b/p1b/run.py@93ba655:230-24…; fixed runs: make_spec(g, None, ...) has no post, so there is no switch (analysis.py:67-68) | R1 CTRL: VERIFIED |
| C27 | 100 | ID (presence): the meter knows when an incident starts and ends, and switches to one plan. | **VERIFIED** | ID switches exactly at onset (t_switch = t_on in all 268,854 main switch runs); back plans return at clearance. Conflicts with the line-118 wording (TEXT-F6). | v5b/p1b/analysis.py@93ba655:134-142 fit_switch: ID = best_by_median over the pooled per['slow'] + per['block'…; episode.py@93ba655:195-204 switch at t_sw_plan, back at t_bk_plan; p1/meters.py:203-217 switch_schedule | R1 CTRL: VERIFIED |
| C28 | 101 | IP (type): the meter also knows the incident type and switches to a plan for that type. | **VERIFIED** | IP picks one plan per (type, q). In block_q2000 IP = ID by construction (identical runs), so IP vs ID = 0.0 there is an identity. | v5b/p1b/analysis.py@93ba655:136-138 ip = {inc: best_by_median(per[inc], A_)}; result.json tune.arms IP: q1600 slow c1000+back, block p20_20_16_e4; q2000 slow p70_40_8_e4, block p20_20_14_… | R1 CTRL: VERIFIED |
| C29 | 102 | L2: in hindsight the best plan for each individual incident; an upper limit for any incident-aware controller using the same plans; cannot be measured without bias. | **PARTIALLY SUPPORTED** | OR_in bounds only policies that run N until onset and then take one action of A with perfect timing. Always-on PI beats even OR_in on 5-16 % of seeds, so "an upper limit for any incident-aware controller" is too broad. | analysis.py@93ba655:256-276 or_in, orx; every action of A runs N before onset (sw(N, a)); oracles.py: always-on PI beats OR_in (the per-seed minimum over all 120 actions) on 8/5/10/16 of 100 seeds (s… | R1 CTRL: PARTIALLY |
| C30 | 104 | All comparisons are made given that an incident occurs. | **VERIFIED** | Every evaluation cell contains an incident; clean days are a separate cell. | analysis.py@93ba655:335-400 evaluate loops over INCIDENTS x QS cells only; clean days in clean_and_prevalence…; confirm_c1.py@e7dd561: INC='block', Q=1600 | R1 CTRL: VERIFIED |
| C31 | 104 | Always-on controllers tuned on incident runs may pay a cost on incident-free days, which we report separately. | **PARTIALLY SUPPORTED** | The data exist (clean-day cost vs N: PI +12.0 s/veh at q1600, +151.6 s/veh at q2000) but the paper does not report them, despite "which we report separately". | docs/research/protocols/p1_incident_information.md:102 ('The clean-day delay of every arm is printed next to…; p1b_result.json eval.per_q.{1600,2000}.clean_day (medians N 45.4 / 151.6; PI 81.1 / 301.1; FX 227.8 / 388.4) | R1 TEXT: PARTIALLY |
| C32 | 110 | Single freeway bottleneck, lanes per edge 4/4/4/2/1; one signal across all four mainline lanes, upstream of the lane drop (mainline metering). | **VERIFIED** | Lanes 4/4/4/2/1; one TLS at node 3 across all four lanes, upstream of both lane drops. | netgen_bn4.py@93ba655:22-27; bn4.net.xml: edge 2 (310 m, 4 lanes) ends at junction 3 (traffic_light); edge 3 is 120 m; zipper junction 4 a… | R1 PLANT: VERIFIED |
| C33 | 110 | Demand is constant at q in {1600, 2000} veh/h. | **PARTIALLY SUPPORTED** | Constant rate, but Poisson arrivals (vehicle count varies by seed), demand stops at 940 s, and 10 % of vehicles are an "av" vType; none of this is stated. | v5b/d1/demand.py@93ba655:38-57 Poisson process (exponential gaps), seeded; v5b/p1b/episode.py@93ba655:133 profile [(0, warmup+control, q)] = [0, 940) s | R1 PLANT: PARTIALLY |
| C34 | 110 | Each run has a 40-s warm-up and a 900-s control period, and continues until the network is empty. | **PARTIALLY SUPPORTED** | Timeline correct, but the paper omits that demand stops and the meter goes all-green at 940 s, so 22-56 % of time in system accrues in an uncontrolled drain; the 40-s warm-up is shorter than a free-flow trip (about 45 s). | v5b/p1b/episode.py@93ba655:124-125 warmup_s 40, control_s 900, t_drain_max 7200; :153-161 all-green warm-up;…; analyze_plant.out: 0 undrained runs in P1b, C1 and P1 | R1 PLANT: PARTIALLY; R1 FU1 (FU1-C2): PARTIALLY |
| C35 | 110 | Signal cycle: 6 s green, 3 s amber, at least 2 s red; cycle length c(q) = max(11, 28800/q) s (two vehicles per lane per green); commanded rate limited to [200, 2618] veh… | **PARTIALLY SUPPORTED** | Durations and formula correct, but c uses the commanded rate, not the demand q; "two vehicles per lane per green" is a design target (realised discharge 0.54-0.99 of the command). The 200 veh/h floor means 135-s reds on all four lanes (G3R-F1). | v5b/p1b/meters.py@93ba655:29-31, 37-38, 41-42, 87-88 (clip to [200, 2618]), 117-129; v5b/d1/meter_signal.py@93ba655:24-34 continuous clock (V100) | R1 PLANT: VERIFIED; R2 G4: PARTIALLY |
| C36 | 110 | Lane changing is disabled in this plant, so a lane blockage is represented by a crawling lane. | **PARTIALLY SUPPORTED** | True of the code, but the crawl is not a faithful blockage: with no lane changes about half the inflow (lanes 3_2, 3_3) is forced through the 240-m crawl lane at about 1 m/s; the protocol itself calls it more severe than a closure. | v5b/d1/plant.py@93ba655:25-29 lcStrategic=-1 lcSpeedGain=0 lcCooperative=0 lcKeepRight=0 for both vTypes; bn4.net.xml connections 3_2,3_3 -> 4_1 (zipper) | R1 PLANT: PARTIALLY; R2 G2: PARTIALLY |
| C37 | 114 | Two incident types act on the bottleneck: a slowdown (speed limit 5 m/s) and a lane crawl (one lane at 1 m/s). | **PARTIALLY SUPPORTED** | Speeds correct. The slowdown acts on edge 5 (the 1-lane bottleneck); the crawl acts on lane 4_1 of the upstream 2-lane edge 4, so "act on the bottleneck" holds only for the whole merge zone. | v5b/d2/incidents.py@93ba655:28-29 SLOW_EDGE '5', 5.0; BLOCK_LANE '4_1', 1.0; :64-69 _apply; analyze_plant.out incident_log: ('slow','on','5_0',5.0) x160,930; ('block','on','4_1',1.0) x160,440 (P1b); 1,… | R1 PLANT: VERIFIED; R2 G2: PARTIALLY |
| C38 | 114 | Onset is uniform in the first third of the control period; duration uniform in 120-480 s. | **VERIFIED** | Onset U(40, 340) s (first third of control), duration U(120, 480) s, recomputed from 420 seed draws. | v5b/d2/incidents.py@93ba655:34-39; p1b/episode.py@93ba655:140 incident_window(seed, warmup_s=40, control_s=90…; analyze_plant.out: onset [40.70, 338.90]; duration [121.88, 478.15]; eval mean onset 198.3 (expected 190), me… | R1 PLANT: VERIFIED |
| C39 | 114 | Every controller sees the same incident in a given seed. | **VERIFIED** | Identical incident windows across arms and types on every seed. | v5b/d2/incidents.py@93ba655:31-39 rng(seed+3301), independent of the arm; analyze_plant.out: P1b 320 and C1 100 (seed, type) groups, 0 with more than one distinct (onset, duration, t_… | R1 PLANT: VERIFIED |
| C40 | 114 | The four evaluation cells are the two incident types at the two demand levels. | **VERIFIED** | Four cells (slow/block x 1600/2000), checked on every S1 run file. | v5b/p1b/analysis.py@93ba655:35 QS = (1600.0, 2000.0); :338-341 loop over INCIDENTS x QS calling cell_runs; result.json eval.cells: slow_q1600, slow_q2000, block_q1600, block_q2000, each n_seeds 100, n_dropped_seeds 0 | R1 S1: VERIFIED |
| C41 | 118 | N = the best constant rate on incident-free days. | **CONTRADICTED** | At q2000 N is f10_8, an integral-feedback law; "best constant rate" holds only at q1600 (c1800). | analysis.py@93ba655:124 'N': fam.best_by_median(none, G_) over all of G (20 constant + 30 feedback laws); result.json tune.arms['2000'].N = 'f10_8' (integral feedback, K_F=10, n_crit=8); q1600 N = 'c1800' | R1 CTRL: CONTRADICTED; R1 recheck (CTRL): CONTRADICTED |
| C42 | 118 | FX = the best constant rate tuned on incident runs. | **VERIFIED** | FX = c2600 at q1600 (top of the grid, barely meters) and c2000 at q2000. | analysis.py@93ba655:125 FX = best_by_median(pooled, CONST); result.json: FX q1600 c2600, q2000 c2000; tune.grid_edges_report_only['1600'].FX = ['rate=2600'] | R1 CTRL: VERIFIED |
| C43 | 118 | FB = an integral feedback law on the downstream vehicle count in the style of ALINEA [Papageorgiou1991]. | **VERIFIED** | Integral law on the edge-4 vehicle count (a 0.5-s snapshot, not a period average) = ALINEA form of Papageorgiou 2008 eq. (1). The edge-4 count includes the crawl lane (G2-F2). | v5b/p1b/meters.py@93ba655:150-151 q = clip(q + K_F (n_crit - n), 200, 2618); episode.py:147-150 n = ls.edge.g…; Papageorgiou et al. 2008 TR-C 16:535-553 (papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf) §2.7.1 eq.(1)… | R1 CTRL: VERIFIED |
| C44 | 118 | PI = a PI law in the form of PI-ALINEA [Wang2014], as used for mainstream signals at lane drops [Tympakianaki2014]. | **PARTIALLY SUPPORTED** | Code matches the PI-ALINEA velocity form with counts; Wang 2014's own equation not read. The PI optimum at q1600 is on two grid edges and Pareto-dominated (CTRL-F2). | meters.py@93ba655:152-155 q = clip(q - K_P*dn + K_I*(n_crit - n)); family.py@93ba655:30-35 grid; result.json PI q1600 p70_120_8_e4 (grid_edges: K_P=70, K_I=120), q2000 p20_20_14_e4 (K_P=20) | R1 CTRL: PARTIALLY; R2 G8: PARTIALLY |
| C45 | 118 | AD = FB with an online set point in the spirit of AD-ALINEA [Smaragdis2003]. | **PARTIALLY SUPPORTED** | AD is the study's own sign-rule hill-climb, not AD-ALINEA's estimator (the protocol says so, the paper does not); the citation is the wrong Smaragdis paper; tuned eta at the grid edge; AD is worse than FB on tuning seeds. | meters.py@93ba655:134-146; protocol p1_incident_information.md §2 AD row: 'in the spirit of AD-ALINEA (Smarag…; references.bib Smaragdis2003 = 'Series of New Local Ramp Metering Strategies', TRR 1856 (2003) | R1 CTRL: PARTIALLY |
| C46 | 118 | ID knows only that an incident has started; IP also knows its type. Both run N before the incident and then switch to an action from a set A of 120 actions: 50 constant-… | **PARTIALLY SUPPORTED** | 120 actions confirmed. "ID knows only that an incident has started" contradicts line 100 and Table I (back actions use clearance). The "10 best PI-law plans" are the 10 best always-on PI controllers on tuning seeds, not the best as plans. | p1b/family.py@93ba655:23-26 actions = fam.actions(G) + fam.actions(G_PI); p1/family.py:21-28 (20+30); result.…; run.py@93ba655:219-223 gpi_select uses FIXED (always-on, t=0) PI runs pooled over slow+block on the tuning se… | R1 CTRL: PARTIALLY |
| C47 | 118 | All arms are tuned on 40 tuning seeds; detection is perfect in the main rows. | **VERIFIED** | 40 tuning seeds 7,400,300-339; switches exactly at onset in main rows. Law plans act on a 30-s update grid (lag 1-29 s); no bias found (G3R-F3). | run.py@93ba655:51-52 SEEDS tune 7,400,300-339; :509 stage_tune(seeds['tune']); retune.json n_tune_seeds_per_a…; s3_tp.json: main_t_switch_ok 268,854/268,854; main_back_ok 133,868/133,868 | R1 CTRL: VERIFIED |
| C48 | 130 | Table I: L0 = N, FX, FB, PI, AD use no incident information; L1a ID uses incident onset (and clearance); L1b IP uses onset, clearance and type; L2 OR_in, ORX_R = full pe… | **VERIFIED** | Matches code and data, apart from the ID-knowledge wording conflict (C46). | analysis.py@93ba655:236-253 cell_runs (L0 fixed, ID/IP switch runs), 256-276 OR_in/ORX; result.json tune.arms; replicate runs share the incident window (oracles.py: 0 mismatches) | R1 CTRL: VERIFIED |
| C49 | 141 | OR_in picks, for each seed, the best action of A on the evaluated run itself; it is optimistic because noise makes some actions look better by chance. | **VERIFIED** | Recomputed exactly; optimistic by construction (minimum over 120 runs per seed). | analysis.py@93ba655:256-263 or_in = argmin_tie over the main runs; oracles.json OR_in median rel CI upper bounds: 47.78/25.55/19.29/22.37 % vs result.json x = 47.87/25.43/19.30… | R1 CTRL: VERIFIED |
| C50 | 141 | ORX_R picks the action with the best mean over R in {1,2,4} independent replicate runs (new demand and simulator seeds, same incident) and scores it on the evaluated run… | **VERIFIED** | Recomputed exactly (ORX_1/2/4, replicate seeds disjoint, incident fixed). "Low in expectation" holds for the mean version used; the paper reports medians elsewhere (LIT-F10). | analysis.py@93ba655:266-276 orx (reps[:R], mean, argmin_tie, main[i]); p1/meters.py@93ba655:233-239 replicate…; oracles.json: replicate_seed_rule_violations 0, incident_window_mismatches 0; ORX_4 mean lower CI -0.37/0.67/… | R1 CTRL: VERIFIED |
| C51 | 141 | The placebo TP picks the best of five replicate runs of IP itself and shows the size of pure-noise gains. | **PARTIALLY SUPPORTED** | TP is best of the main run plus 4 replicates with demand redrawn; it partly exploits luck in the arrival draw, and is best-of-5 vs OR_in's best-of-120 with shared demand. Not a matched placebo. | p1/stats.py@93ba655:145-149 tp_placebo: best = min(main, reps.min); analysis.py:370-372 (rmax = 4 replicates); s3_tp.json: the run TP picks has fewer generated vehicles than the main run (median -10.5/-10.5/-7.5/-15.5 ve… | R1 CTRL: PARTIALLY |
| C52 | 141 | In SUMO a change of controller also changes later random draws, so paired runs with equal seeds do not share common random numbers. | **PARTIALLY SUPPORTED** | 4 spot re-runs (2 seeds): equal seeds give identical vehicle streams until the controller changes insertion times (spillback); then the draws desynchronise. "A change of controller changes later random draws" is too general, and no evidence for "we found" is documented. | docs/research/prior_art_P1_P2.md:34 '(agent read the source): MSBaseVehicle::getRNG() uses the current lane's…; v5b/d1/plant.py@93ba655:28,34 speedFactor normc and depart_lane='random' (SUMO RNG draws) | R1 CTRL: UNVERIFIED; R1 REPRO: PARTIALLY |
| C53 | 145 | The protocol, its statements and the seed ranges were fixed and approved before any data were produced. | **CONTRADICTED** | As C11: true study by study, false as worded. | approval entries first committed: V99 7da4ab4 10-19 14:12; V100 c225049 16:54; V108 75bcd2b 10-20 09:51; V115…; P1b seeds 260-279/300-339/600-699 approved V108 before P1b start 10:38:06 (journal p1b-run.service) | R1 PROV: CONTRADICTED; R1 recheck (PROV): CONTRADICTED |
| C54 | 145 | Every study was run once from a frozen code version. | **PARTIALLY SUPPORTED** | True for P1b and C1 (one launch, clean committed code, every run tagged). P1 was aborted by a docs commit and resumed from a frozen worktree (reusing 6,146 tool-check runs); D1/D2 were re-run after the V100 bug. None of this is stated. | P1B_EVAL_STARTED.json args.resume=false; p1b/v108/run.log: every stage '0 reused', 'failed 0'; one p1b-run.se…; P1b result.json code_commit 93ba655, code_dirty false; all 344,852 run JSONs code_commit 93ba655; main HEAD a… | R1 PROV: PARTIALLY |
| C55 | 145 | Evaluation uses 100 seeds that are separate from the tuning seeds; comparisons are paired by seed. | **VERIFIED** | Evaluation seeds 7,400,600-699 disjoint from tuning 300-339; pairs share demand, SUMO seed and incident. | P1b result.json seeds: tune [7400300, 7400339], eval [7400600, 7400699]; tune.A_size 120; raw file names: P1b 160 distinct seeds 260-279, 300-339, 600-699 (scratch seed_sets.py) | R1 PROV: VERIFIED |
| C56 | 145 | rel = median(r - t)/median(r), positive favours t over reference r; percentile bootstrap CIs with B = 20,000. | **VERIFIED** | Definitions and B = 20,000 match the code; all 44 S1-level rows reproduced exactly. | v5b/p1/stats.py@93ba655:14 B_BOOT = 20_000; :35-41 boot_idx default_rng(20261019).integers(0, n, (B, n)); :52…; protocol p1_incident_information.md:86 and addendum I12 (line 176) | R1 S1: VERIFIED |
| C57 | 145 | S1 rule R(t, r): (a) in at least one cell rel >= 10 % with the lower CI bound of median(r - t) above zero, and (b) in every cell point rel >= -5 %. S1a requires R(ID, r)… | **VERIFIED** | Rule text matches the protocol and the code; re-implemented independently with the same outcome. | protocol p1_incident_information.md:94-100 (rule and statements), :90 intersection-union, A2(a) line 147; add…; v5b/p1/stats.py@93ba655:79-80 rule_cell, :83-90 rule_R, :93-102 s1a | R1 S1: VERIFIED |
| C58 | 145 | The S1 intervals are Bonferroni-corrected (level 0.99375). | **VERIFIED** | 0.99375 = 1 - 0.05/8 in all 44 rows. The family behind /8 is not explained in the paper; CI ends at this level move up to 1.6 points with the bootstrap RNG. | v5b/p1/stats.py@93ba655:17 LEVEL_S1 = 1.0 - 0.05/8; v5b/p1b/analysis.py@93ba655:353-355 ID vs L0, IP vs ID and IP vs L0 all at st.LEVEL_S1 | R1 S1: VERIFIED |
| C59 | 145 | S2 states the bracket of the gain of per-incident information over IP; S3 reports break-even detection delays (descriptive). | **PARTIALLY SUPPORTED** | S2 correct. S3 is described as detection delays only, but the pre-registered S3 includes c*, p*, f* and a combined row, and A10 lists p* and f* as paper outputs. | v5b/p1/stats.py@93ba655:112-142 (s2_cell, s2_statements: x, y, y_hat, plateau, 'bracket [y, x]' text); v5b/p1b/analysis.py@93ba655:356-369 (S2 per cell), 521-570 (imperfection_cell: d_star, c_star, p_star, combin… | R1 S23: PARTIALLY |
| C60 | 145 | A separate confirmation (C1) tested one cell on 100 fresh seeds with a single pre-fixed statement at the 95 % level. | **PARTIALLY SUPPORTED** | Fresh seeds, statement fixed before the run, run once: verified. Omitted: cell and comparator chosen after P1b data; the rule tests rel >= 10 % on the point estimate (rel CI lower bound 7.3 %); PI was not the strongest L0 arm there (FB). | p1b_confirm_c1.md@7c6acc8 (statement: rel >= 10 % AND lower bound of the 95 % CI of median(PI - IP) > 0, in b…; C1 runs: 1,100 files, seeds 7400700-7400799 only, commit e7dd561 (scan_runs.py) | R1 PROV: PARTIALLY |
| C61 | 149 | Drivers obey the amber unless they cannot stop comfortably. | **PARTIALLY SUPPORTED** | "Comfortably" = SUMO tls.yellow.min-decel 3 m/s2 (twice b = 1.5). Vehicles that cannot stop before red are forced to an instantaneous, non-physical stop. Not stated. | SUMO v1_27_1 MSVehicle.cpp:2793-2796 stopDecel = max(min(tls.yellow.min-decel, emergencyDecel), decel) and :2…; MSFrame.cpp:513 tls.yellow.min-decel default 3.0 (not overridden in sumo_runner.py@93ba655:102-107) | R1 PLANT: PARTIALLY; R2 G4: PARTIALLY |
| C62 | 149 | In report-only rows a share s in {10, 30} % of drivers ignore the amber and the first 1.5 s of red. | **PARTIALLY SUPPORTED** | Shares implemented as written; runners also cross any red when they cannot brake, are never emergency-stopped, and include AV-type vehicles. | v5b/p1b/runners.py@93ba655:15 jmDriveAfterYellowTime 3, jmDriveAfterRedTime 1.5, jmDriveRedSpeed 13.9; :33-37…; SUMO v1_27_1 MSVehicle.cpp:7605-7621 ignoreRed: with jmDriveAfterRedTime >= 0 always drive at yellow; at red… | R1 PLANT: PARTIALLY; R2 G4: PARTIALLY |
| C63 | 149 | Published field rates of metered-signal violations [TOPS2005; Sun2013] give context for these shares (s in {10, 30} %); they are model parameters, not field estimates. | **PARTIALLY SUPPORTED** | No numbers given in the paper. Field data (companion report/thesis) put s = 30 % inside observed work-zone non-compliance; permanent ramp meters are lower (<= 9 %); definitions differ. | TOPS 2005 Tables 3-14 and 3-15: SOV red-light violations 0.9-9.0 % per ramp and peak period. HOV 8.3-34.3 %,…; Sun 2013: the abstract gives no rates. A search-engine snippet (not opened, unverified) attributes 40.5-82.9… | R1 LIT: PARTIALLY; R2 G8: PARTIALLY |
| C64 | 155 | S1a fails: knowing only that an incident is on gave no detected gain of 10 % or more over strong always-on control. | **PARTIALLY SUPPORTED** | FAIL reproduced. "No detected gain >= 10 %" holds for the pre-registered pooled-median ID; with other type-blind ID rules fitted on tuning seeds, ID beats FB/PI by 13.7-18.0 % in crawl-1600 (S1a still fails, via (b)). ID is an L0 law started at onset by construction (CTRL-F3). | result.json eval.S1.S1a_pass = false, S1a_cells_both_views = []; s1_recompute.py: R(ID,FB) a_cells [] (rel -1.5, +4.8, -2.6, +6.6); R(ID,PI) a_cells [] and b fails in slow_q1… | R1 S1: PARTIALLY; R1 FU1 (FU1-C4): VERIFIED; R2 FU2 (C64): PARTIALLY; R2 FU2 (FU1-C4): PARTIALLY |
| C65 | 155 | Against always-on PI, ID was never better (rel between -17.9 % and -0.7 %). | **VERIFIED** | Values exact. In the q2000 cells ID is PI's own law started at onset, so this row measures the cost of running N before onset. | result.json eval.S1.per_cell_stats.<cell>.ID_vs.PI.all_seeds.rel: -0.1791, -0.0182, -0.0071, -0.0207; s1_recompute.py identical; CIs [-35.1,-6.7], [-5.2,0.0], [-10.1,6.7], [-6.6,0.0] | R1 S1: VERIFIED; R1 FU1 (FU1-C5): VERIFIED |
| C66 | 155 | S1b passes: knowing the type added 11.8 % [5.8, 16.7] (slowdown, 2000 veh/h) and 22.0 % [8.8, 31.4] (lane crawl, 1600 veh/h) over presence alone. | **PARTIALLY SUPPORTED** | Numbers and PASS reproduced exactly (two independent derivations). Attribution to "type knowledge" depends on the pooled-median ID rule (alternative type-blind rules: block_q1600 gain 0.0-2.8 %), and 83 % of the slow_q2000 gain is realised in the uncontrolled drain (window-TTT rel 1.7 %). | result.json eval.S1.per_cell_stats.slow_q2000.IP_vs_ID.all_seeds: rel 0.1183, rel_ci [0.0583, 0.1674], diff 4…; S1b_pass true, S1b_cells_both_views [slow_q2000, block_q1600] | R1 S1: VERIFIED; R1 FU1 (FU1-C3): PARTIALLY; R2 FU2 (C66): PARTIALLY; R2 FU2 (FU1-C3): PARTIALLY |
| C67 | 155 | Against always-on PI, IP's interval lay above zero only for the lane crawl at 1600 veh/h: 18.0 % [8.9, 31.6] (report-only row). | **VERIFIED** | 18.0 % [8.9, 31.6] exact; the "only" holds across 20 bootstrap seeds. | result.json eval.cells.<cell>.IP_vs_L0.PI.all_seeds: rel 4.5/7.4/18.0/-2.1 %, rel_ci lower -35.2/-2.7/8.9/-6.…; v5b/p1b/analysis.py@93ba655:355 ip_vs_l0 at LEVEL_S1; protocol line 101 'IP vs each L0 arm is reported (descr… | R1 S1: VERIFIED; R1 FU1 (FU1-C6): VERIFIED |
| C68 | 160 | Fig. 2: median delay along the information ladder in the four cells: strongest always-on arm (L0), ID, IP, and the two bounds on per-incident hindsight (ORX_4 low, OR_in… | **PARTIALLY SUPPORTED** | All 20 bars exact, but the ORX_4 and OR_in bars are marginal medians, not the bounds reported in Table II (paired CI ends; mean version for ORX). | papers/paper_1/figures/fig_ladder.py@HEAD:14 reads eval.fig1_ladder; :21-27 plots rungs[*].median_delay_s; v5b/p1b/analysis.py@93ba655:376-380: strongest = min over L0=(N,FX,FB,PI,AD) of the marginal median on the ev… | R1 REPRO: PARTIALLY |
| C69 | 174 | Table II rows: ID vs PI (-17.9, -1.8, -0.7, -2.1); IP vs ID (16.2, 11.8 bold, 22.0 bold, 0.0); IP vs PI (4.5, 7.4, 18.0 bold, -2.1); bold = interval above zero at the S1… | **PARTIALLY SUPPORTED** | All 12 values and the bold pattern exact; the caption's sign convention is inverted (positive favours the FIRST-named arm). | paper.qmd:174-176; paper.pdf Table II (pdftotext) identical; s1_recompute.py output rows ID_vs_PI, IP_vs_ID, IP_vs_PI; lower bounds > 0 only in IP_vs_ID slow_q2000, block… | R1 S1: VERIFIED; R2 FU2 (C69): PARTIALLY |
| C70 | 187 | The lane-crawl cell at 1600 veh/h was tested once on 100 fresh seeds. | **VERIFIED** | Seeds 7,400,700-799 unused before C1; one launch. | P1B_C1_STARTED.json 2026-10-20 21:27:50 (resume false); p1b_c1/v114/run.log: '1100 runs to do (0 reused)', 'f…; result.json cell block_q1600; seeds [7400700, 7400799]; n_runs 1100; invalid/teleport/collision 0 | R1 PROV: VERIFIED |
| C71 | 187 | C1 is confirmed: the type plan reduced median delay relative to always-on PI by 16.2 % [7.3, 23.7] (41.4 s/veh [16.6, 65.7]). | **PARTIALLY SUPPORTED** | Numbers reproduced exactly (two independent derivations; 4 spot re-runs bit-identical). Caveats: it is the median of paired differences over median(PI) (the medians differ by 17.3 %); the comparator PI is Pareto-dominated, on grid edges and not the strongest L0 arm (FB); the gain reverses for incidents shorter than about 230 s; it rests on the no-lane-change crawl and on PI sitting at the 200 veh/h floor. | v5b/p1b/confirm_c1.py@e7dd561:49-58 (cell, arms N=c1800, IP_PLAN=p20_20_16_e4, PI=p70_120_8_e4, SEEDS 7,400,7…; v5b/p1b/confirm_c1.py@e7dd561:121-136 (c1_view, statement_c1); v5b/p1/stats.py@e7dd561:48-64 (paired) | R1 C1: VERIFIED; R1 FU1 (FU1-C7): VERIFIED; R2 G2: PARTIALLY; R2 FU2 (C71): PARTIALLY; R2 FU2 (FU1-C7): PARTIALLY |
| C72 | 187 | ...with the same result when seeds with invalid runs are excluded. | **PARTIALLY SUPPORTED** | True but empty: no C1 run was invalid, so nothing was excluded. | v5b/p1b/episode.py@93ba655:255 valid = drained and len(trips) == gen and health != FAIL; v5b/p1b/confirm_c1.py@e7dd561:127-136 (keep = ~invalid) | R1 C1: PARTIALLY |
| C73 | 187 | The lead held with detection delays of 30-120 s (12.5-16.4 %). | **VERIFIED** | 15.5 / 16.4 / 12.5 % with 95 % CIs above 0. The tolerance comes from a slow-acting plan whose action is set by the traffic state, not the switch time (G3R-F4). | protocol p1b_confirm_c1.md 'Reported, descriptive (no claims)': IP vs PI with d in {30, 60, 120} s (pre-regis…; v5b/p1b/confirm_c1.py@e7dd561:71-77 (ip_spec via canon_sw), 179-183 (rows PI_vs_IP_d*, IP_vs_IP_d*, n_no_swit… | R1 C1: VERIFIED; R1 FU1 (FU1-C8): VERIFIED; R2 G5: VERIFIED |
| C74 | 187 | ...and with red-light runners (24.4 % at s = 10 %, 27.6 % at s = 30 %), where always-on PI itself degraded. | **VERIFIED** | 24.4 % and 27.6 % exact; PI vs itself -8.5 % and -11.0 % (95 % CIs below 0). | protocol p1b_confirm_c1.md: 'IP vs PI with runner share s in {10 %, 30 %}' descriptive (pre-registered as des…; result.json c1.descriptive: PI_s0.1_vs_IP_s0.1 24.4 [21.1, 29.8], diff 65.87 [55.19, 84.55]; PI_s0.3_vs_IP_s0… | R1 C1: VERIFIED; R1 FU1 (FU1-C8): VERIFIED |
| C75 | 189 | Fig. 3: delay reduction of IP over always-on PI with 95 % CI in C1 (lane crawl, 1600 veh/h, 100 fresh seeds); the dashed line marks 10 %. | **VERIFIED** | Fig. 3 rebuilt pixel-identical from a scratch copy; values recomputed from raw runs. | papers/paper_1/figures/fig_c1_robust.py@HEAD:15-22 (keys c1.C1.all_seeds; descriptive PI_vs_IP_d30/d60/d120,…; v5b/p1b/confirm_c1.py@e7dd561:51-57 (frozen arms, seeds 7,400,700-799, B=20,000, BOOT_SEED_C1=20261020, level… | R1 REPRO: VERIFIED |
| C76 | 193 | Per-incident hindsight beyond the type plan could only be bracketed, because the bracket did not converge as R grew. | **PARTIALLY SUPPORTED** | What failed is the plateau of ORX_R (R = 2 vs 4), not "the bracket"; the +-1-point criterion needs a CI width <= 2 points, unreachable at n = 100 (widths 4.0-15.1). | v5b/p1/stats.py@93ba655:123-125 (plateau = paired(orx[2], orx[4], 0.95, mean=True); ok iff CI within +-PLATEA…; result.json eval.S2.<cell>.all_seeds.plateau_holds = false in all 4 cells | R1 S23: PARTIALLY |
| C77 | 193 | The lower bounds were positive in the two lane-crawl cells (0.4 % and 3.5 %); the upper bounds ranged from 13.3 % to 47.9 %. | **CONTRADICTED** | Lower bounds correct; "13.3 %" is a stale P1 value (P1 slow_q2000 upper bound 0.1331). The P1b range is 19.3-47.9 %. | result.json eval.S2: y = 0.44 % (block_q1600), 3.52 % (block_q2000), -0.40 % (slow_q1600), -2.43 % (slow_q200…; paper Table II line 177: upper bounds 47.9, 19.3, 25.4, 22.4, so the range is 19.3-47.9 | R1 S23: CONTRADICTED; R1 recheck (S23): CONTRADICTED |
| C78 | 193 | The placebo alone gained 13.6-37.7 %, which shows how strongly in-sample selection on simulation noise inflates hindsight gains. | **PARTIALLY SUPPORTED** | TP values exact, but TP is not a like-for-like measure of OR_in's noise inflation (C51). | v5b/p1/stats.py@93ba655:145-149 (tp_placebo: min over main + 4 replicates, rel at 95 %); result.json eval.TP: 37.65 [23.80, 46.04], 16.77, 13.58, 15.71 % | R1 S23: PARTIALLY |
| C79 | 197 | Slowdown at 2000 veh/h: IP stayed ahead of the best always-on arm up to a detection delay of about 120 s. | **PARTIALLY SUPPORTED** | d* = 120.4 s exact, but its 95 % CI is [20.1, 168.5] s and the margin at 120 s is 0.14 s/veh; IP's lead over PI was not significant even at d = 0. | result.json eval.S3.slow_q2000.d_star.all_seeds: value 120.37, binding_arm PI, ci [20.14, 168.48], share_neve…; own recompute: M_PI(d) = 26.54, 16.54, 19.55, 0.14, -43.84 s/veh at d = 0, 30, 60, 120, 240; strongest L0 by… | R1 S23: PARTIALLY; R2 G5: PARTIALLY |
| C80 | 197 | Slowdown at 1600 veh/h: the tuned plan was an open-loop constant rate whose lead vanished within 3 s of detection delay and which lost 49.8 % with 30 % runners. | **PARTIALLY SUPPORTED** | "Open-loop constant rate" and "-49.8 % with 30 % runners" exact. "Within 3 s" is a linear interpolation between d = 0 and 30 s with no run in between; the d = 0 lead was never significant. | result.json tune.arms.1600.IP.slow = 'c1000+back', N = 'c1800'; v5b/p1/family.py@93ba655:5,22-25 ('c<rate>':…; result.json eval.S3.slow_q1600.d_star.all_seeds: 2.61, PI, ci [0, 7.10], share_never_ahead 0.20; own: M_PI =… | R1 S23: PARTIALLY; R2 G5: PARTIALLY |
| C81 | 197 | Lane crawl at 2000 veh/h: the best plan was PI's own law, and starting it only at onset never beat always-on PI. | **VERIFIED** | Re-derived: IP = PI's law in block_q2000; started at onset it never beats always-on PI (median statement). | result.json tune.arms.2000: IP.block = PI = ID = 'p20_20_14_e4'; own re-tuning: p20_20_14_e4 381.3 s vs runne…; result.json eval.S3.block_q2000.d_star: 'IP never ahead', binding PI, share_never_ahead 0.99975; own M_PI = -… | R1 S23: VERIFIED |
| C82 | 197 | The amber phase reduced the share of runs with an emergency stop from 87 % (no amber) to 12.8 %. | **PARTIALLY SUPPORTED** | Both shares exact (P1 43,370/50,061 = 86.6 %; P1b 7,396/57,782 = 12.8 %), but this compares two studies that differ in more than amber (min red 2 s, rate cap 4000 -> 2618, PI law, action set, tuned arms, seeds). "The amber reduced" is not established, and the 87 % is an undisclosed P1 number. | counter: v5b/d1/sumo_runner.py@93ba655:137 estops += libsumo getEmergencyStoppingVehiclesNumber (per step); g…; P1: ~/work/phd/v5b1_runs/p1/v99/runs, code 85f7d34, signal 'continuous'; P1 note docs/research/results/p1_res… | R1 C1: PARTIALLY |
| C83 | 197 | No collisions occurred, and no vehicle crossed on red without runners. | **PARTIALLY SUPPORTED** | Zero counts verified. But for non-runners zero red crossings are enforced by SUMO (forced stops), and collisions on junction internal lanes (the zipper merges) were not checked (4 re-runs with junction checks on: 0). | analyze_plant.out: collision runs 0 of 344,852 (P1b), 0 of 1,100 (C1), 0 of 296,527 (P1); red crossings 0 in…; v5b/d1/sumo_runner.py@93ba655:105 --collision.check-junctions false; :136 getCollidingVehiclesNumber; SUMO MS… | R1 PLANT: PARTIALLY; R2 G3: PARTIALLY |
| C84 | 197 | At 2000 veh/h the meter queue reached the upstream entry in 85-100 % of metered runs, so these cells assume unlimited upstream storage. | **PARTIALLY SUPPORTED** | The measure is a post-run proxy (recompute decided in V109 just before launch; thresholds tail within 50 m of the entry or mean depart delay > 5 s documented only post-run); FX, a metered arm, has 7 % and 42 %; the queue tail never passed 368.7 m of 410 m. | v5b/p1b/analysis.py@93ba655:50,284-285 pre-registered B4 (7 m) flag: 0 everywhere; v5b/p1b/confirm_c1.py@e7dd561:59,140-141 V109 indicator: tail >= avail - 50 m OR mean depart delay > 5 s (pos… | R1 PLANT: PARTIALLY |
| C85 | 2 | Title: 'How Much Incident Information Does Mainline Metering Need? An Honest Headroom Decomposition in Microsimulation'. | **PARTIALLY SUPPORTED** | Answers one plant, 2 demands, 2 incident types (one a substitute), perfect detection, conditional on an incident. "Honest" invites scrutiny of exactly the undisclosed items. | paper.qmd:2, :69 ('for one microsimulated bottleneck'); docs/research/results/p1b_result.md:76 (cannot say generality), :80 (one plant; block substitute) | R1 TEXT: PARTIALLY |
| C86 | 177 | Table II rows: S2 bracket ([-0.4, 47.9], [-2.4, 19.3], [0.4, 25.4], [3.5, 22.4]); placebo TP (37.7, 16.8, 13.6, 15.7); d* in s (2.6, 120.4, >240, never ahead). | **VERIFIED** | All values recomputed from 269,084 raw run files; exact under the page bootstrap seed. | result.json eval.S2.<cell>.statements.{x,y}; eval.TP.<cell>.rel; eval.S3.<cell>.d_star.all_seeds.{value,flag,…; own recompute s23_recompute_20261019.log: brackets [-0.40, 47.87], [-2.43, 19.30], [0.44, 25.43], [3.52, 22.3… | R1 S23: VERIFIED |

---

## 6. Findings, prioritised

The 101 merged finding groups are listed in full in §6.E and detailed in Appendix B. This section explains the critical and major ones by theme. Overlapping findings are explained together. The bracket after each heading gives the group ids and the verification votes.

### 6.A Research process and reporting integrity

#### A1. "All statements were pre-registered before any data were produced" is false as worded [PROV-F1, with TEXT-F1, REPRO-F4, C1-F1, CTRL-F7; **critical**; reproduce, defend and impact: all CONFIRMED / critical]

**What.** Paper lines 69 and 145 say that the statements, the protocol and the seed ranges were fixed "before any data were produced". In fact four rounds ran on the same BN4 plant and the same four cells:
1. D1/D2 screens;
2. P1;
3. P1b, designed after P1's results: amber, PI-law plans in A, the rate clip and runner rows were added *because* of P1's limits;
4. C1, whose cell, arms and comparator were chosen after P1b's evaluation data.

**Why critical, and why the numbers survive.** By the severity rubric, any false statement about pre-registration is critical. But each study's own page was committed and hashed *before that study's data*, and the hashes match:
- P1 `fed27bf6…@0e8d49b`;
- P1b `2b3d3ccb…@75bcd2b`;
- C1 `8b6005aa…@7c6acc8`.

So no number changes. The impact lens notes that P1 and P1b give the same S1a/S1b verdicts, so P1 works almost as a replication.

**Fix (text, your decision).** Say "each study's statements, seeds and code were fixed and hashed before that study's data". Then disclose the sequence D2 → P1 → P1b → C1 and the post-hoc choice of the C1 cell and comparator.

**Test.** `bash audit/PROV/page_sha.sh`. Compare `git log --format='%h %ad' -- docs/research/protocols/` with the `*_STARTED.json` times.

#### A2. The earlier P1 round is omitted, although the P1b addendum says "Both are reported" [PROV-F2, TEXT-F2; major; 2/2 CONFIRMED / major]

**What.** P1 tested the same S1-S3 on the same cells (296,527 runs, no amber, no PI-law plans). The paper never mentions it, yet it uses two P1 numbers without naming P1 (87 % emergency stops; 13.3 % in line 193).

**Why it matters.** P1's results differ in exactly the places the paper highlights:

| Quantity | P1 | P1b |
|---|---|---|
| C1 cell (block_q1600), IP vs PI | −0.7 % (CI of the difference [−15.8, 21.2] s) | +18.0 % |
| block_q2000, S2 lower bound | −1.8 % | +3.5 % |
| slow_q2000, d* | 26 s | 120 s |

So the C1 effect appeared only after the post-P1 design change, which added a PI-law type plan (`p20_20_16_e4`).

**Test.** `audit/PROV/p1_block1600.py`, `audit/PROV/p1_vs_p1b.py`.

#### A3. Pre-registered outputs are not reported, and they are the unfavourable ones [S23-F2 group and G5-F1 group; major; 2/2 and 2/2 CONFIRMED / major]

**What.** The protocol (`p1_incident_information.md:74, 81, 102, 112, 116`) pre-registers several outputs:
- the clean-day delay of every arm, printed next to S1;
- the false-alarm cost ("always reported");
- S3 = d*, c*, p*, f*(π) and a combined row with CIs;
- as paper outputs (A10, option a): "one break-even table (d*, p*, f*)".

The paper shows only d*, without CIs. Its own text promises more: line 85 promises wrong-type and false-alarm tolerance, and line 104 says the incident-free cost is "reported separately".

**The omitted values** (all in `p1b_result.json`, all recomputed from raw runs):
- clean-day cost of always-on PI vs N: +12.0 s/veh at q1600 and **+151.6 s/veh at q2000**;
- false-alarm cost: 39.5 [22.0, 69.6] and 120.4 [89.7, 147.5] s/veh;
- **p\* = 0.21 [0.12, 0.33] vs FB in the C1 cell**: with 21 % wrong-type errors the lead over FB is gone;
- combined row (d = 60 s, c = 60 s, p = 0.2): no cell has a CI above zero against the strongest L0 arm (block_q1600 +0.5 % [−6.1, 7.8] vs FB; slow_q1600 −52.0 %).

**Defence that holds in part.** The combined row is a pre-registered *study* output, not a pre-registered *paper* output under A10. Leaving it out of the paper is within scope. Leaving out p* and f* is not.

**Test.** `audit/S23/s23_extra.py`, `audit/G5/g5_recompute.py`.

#### A4. The C1 reporting is incomplete [TEXT-F9; major; 2/2 CONFIRMED / major]

The C1 description has five gaps:
- (a) the rule (point rel ≥ 10 % and diff-CI lower bound > 0) is not stated, and the rel CI [7.3, 23.7] dips below 10 %;
- (b) the cell and arms were chosen after P1b; the C1 page requires this disclosure;
- (c) only PI was tested, although FB was the strongest L0 arm in that cell (see B5);
- (d) "reduced median delay … by 16.2 %" misnames the statistic: the median delay itself fell by 17.3 % (254.7 → 210.6 s/veh), and 16.2 % is median(PI − IP)/median(PI);
- (e) "the same result when seeds with invalid runs are excluded" is empty, because no run was invalid.

#### A5. The spill statement uses an undisclosed post-data proxy [TEXT-F13, PLANT-F6, PROV-F7; major; 2/2 CONFIRMED / major]

Line 197 says that "at 2000 veh/h the meter queue reached the upstream entry in 85-100 % of metered runs". That is not what the data show:
- the queue tail never passed 368.7 m of 410 m;
- the pre-registered B4 flag never fired;
- the figure comes from a recomputed indicator: tail within 50 m of the entry *or* mean depart delay > 5 s. V109 (commit `8e10812`, 10:38:01, seconds before the P1b launch) decided that the flag would be recomputed after the run. The 50 m / 5 s thresholds are documented only in the post-run results (V113, `p1b_result.md` §5), and the paper defines neither the indicator nor its post-run origin;
- FX, a metered arm, has 7 % and 42 %.

Delay includes the insertion wait, so S1-S3 are unaffected. The sentence needs rewording and a definition.

### 6.B What the headline numbers mean

#### B1. S1b's size depends on how the presence-only plan (ID) was tuned; ID is an always-on law started at onset [CTRL-F1 (+HEADLINE-F1, FU2-1-F1/F2), CTRL-F3, CTRL-F4; major; CTRL-F1 3/3 CONFIRMED / major, raised as critical]

**What.**
- The pre-registered rule picks ID as the action with the lowest median delay over the *pooled* slow + block tuning runs.
- A pooled sample of two incident types has two modes, and its median lands between them.
- At q1600 the rule picked `f40_10`, which two other type-blind actions beat in *both* incident types.

With other reasonable type-blind rules, fitted on tuning seeds only:

| ID rule | ID plan | S1b result |
|---|---|---|
| pooled mean | — | S1b fails |
| mean of per-type medians | `p20_20_14_e4` | block_q1600 IP vs ID falls from 22.0 % to 2.8 %; presence alone then beats always-on PI there by 16.3 % |
| minimax | `p20_20_16_e4` | block_q1600 IP vs ID 0.0 % |

The blind HEADLINE agent also resampled the tuning seeds (see §4.6): the tuned pair returned in only 15-23 % of resamples, and S1b passed in about 74 %.

**Related design facts.**
- **ID equals an always-on law started late.** ID's chosen plan is FB's own law at q1600 and PI's own law at q2000, run after N until onset. ID vs PI at q2000 (−1.8 %, −2.1 %) therefore measures only the cost of running N before onset. In block_q2000, IP vs ID = 0.0 is an identity (the same run).
- **The gain comes from type-specific parameters, not from switching.** On the tuning seeds, IP's own law run from t = 0 is as good as switching to it at onset (222.0 vs 224.7 s). An always-on law tuned per type matches or beats IP out of sample (CTRL-F4). That comparator is not realisable without knowing the type, so it is not an L0 arm. But it shows that "knowing the type" pays by enabling a type-specific *set point*, not by timing.

**Impact.** The pre-registered verdicts stand: S1a FAIL, S1b PASS. But "knowing the type added 11.8 % / 22.0 %" overstates how stable these magnitudes are. "No detected gain ≥ 10 %" for presence holds only for this ID rule.

**Test.** `audit/CTRL/out/s1_sensitivity.json`, `audit/CTRL/out/pareto_id.txt`, `audit/HEADLINE/selection_bootstrap.py`, `audit/FU2-1/` scripts.

#### B2. An uncontrolled drain after 940 s carries most of every headline gain; the pre-registered co-metrics are missing [DRAIN (FU1-F1/F3/F4/F5/F7, PLANT-F2) and COMETRIC (FU1-F2/F8/F9); major; 3/3 and 3/3 CONFIRMED / major]

**What.** At the end of control (940 s):
- the meter switches to all-green;
- demand stops;
- the network drains with **no control** until empty.

The delay metric includes this phase. The paper says only "continues until the network is empty". The project's own architecture review rejected this convention for the later F3Z plant: "Control stays active during the drain" (`docs/architecture/interfaces.md:52`).

The share of the mean paired TTT gain that accrues *after* 940 s:

| Comparison | After 940 s | Window-TTT rel | Full-TTT rel | Delay rel (paper) |
|---|---|---|---|---|
| S1b slow_q2000, IP vs ID | **83 %** | **1.7 %** | 10.3 % | 11.8 % |
| S1b block_q1600, IP vs ID | 67 % | 9.9 % | 18.6 % | 22.0 % |
| C1, IP vs PI | 55 % | **11.7 % [6.8, 14.1]** | 13.8 % | 16.2 % |
| C1, PI vs NC | 112 % | −5.7 % [−12.6, −0.4] | — | +13.5 % |

**The co-metrics.** The protocol says "served throughput is co-headlined; TTT and the max queue are reported alongside" (`p1_incident_information.md:85`); the paper reports neither. On fixed-window TTT at the S1 level, IP vs ID is 7.4 / 1.7 / 9.9 / 0.0 % across the four cells, so **no cell reaches 10 %**. C1 holds on every metric.

**Fair reading.** Window TTT ignores the cost of the vehicles left in the system, so it is not neutral either. IP serves more vehicles during control, and per seed served × 0.25 h + n_left is exactly constant across arms. Pricing the leftover vehicles with a common, arm-neutral drain function gives:
- slow_q2000: **6.0 %**, with 44 % of its post-control difference due to arm-specific drain behaviour;
- block_q1600: 19.0 %;
- C1: 14.9 %.

So block_q1600 and C1 are robust; **slow_q2000's S1b pass depends on the drain convention**.

**Test.** `audit/FU1/drain_audit.py`, `audit/FU1/drain_dynamics.py`, `audit/verify2/DRAIN-reproduce/drain_split.py`.

#### B3. The C1 mechanism: PI holds all four lanes at a 200 veh/h floor because the crawl lane fills its detector [G2-F2 group (G2-F1, G2-F4), PLANT-F4, G3R-F1; major; G2-F2 reproduce CONFIRMED / major, defend CONFIRMED / minor (override to major); PLANT-F4 3/3 CONFIRMED / major; G3R-F1 single agent, numbers re-derived independently by critic 2]

**What, step by step.**
1. With lane changing off and random entry lanes, about half the vehicles (those entering on lanes 3_2 and 3_3) must drive the 240-m crawl lane 4_1 at about 1 m/s.
2. Vehicles stored on 4_1 raise the edge-4 count that FB, PI, AD and ID read.
3. Always-on PI therefore cuts its rate to the **200 veh/h floor about 126 s after onset in 97/100 runs**, and stays there.
4. At 200 veh/h the cycle is 144 s, with **135 s of red on all four lanes at once**. This also holds back vehicles bound for the free lane 4_0: in the spot runs, free-path exits fell from 724 to 424 veh/h and from 548 to 213 veh/h.
5. IP's type plan (`p20_20_16_e4`, n_crit 16) does not over-hold: about 85 vehicles enter edge 4 during the incident, against 45 under PI.

**Supporting statistics.**
- The per-seed C1 gain tracks PI's time at the floor: Spearman 0.84, and 0.48 with duration held fixed.
- The floor is a code default (`Q_MIN = 200`, `meters.py:31`) with no recorded rationale.
- The paper's own source for mainline/work-zone metering (Papageorgiou et al. 2008, checked in the local PDF) uses floors of about 43 % of capacity. Here the floor is about 14 %.

**Defence that holds in part.**
- The pre-registered grid already held 90 PI laws on the edge-5 count, which the crawl does not inflate, and all of them did badly in the crawl cell.
- Using a type-specific set point *is* what type information buys.

So "type value" is the right name. But the size of the effect plausibly depends on three plant choices: no lane changes, one signal state for all lanes, and a very low floor. A real blockage, with lane changes, was not tested.

**Test.**
- Existing data: `audit/G2/g2_mechanism.py`, `audit/verify3/G2-F2-reproduce/mech.py`, `audit/G3R/g3r_floor.py`.
- New runs (need your approval): (i) the C1 arms with a higher floor; (ii) a blockage variant with lane changing on; (iii) a lane-group-aware detector.

#### B4. The type-plan gain reverses for short incidents [G2-F3; major; 2/2 CONFIRMED / major; exploratory, post hoc]

In the crawl cell, IP vs PI depends strongly on incident duration:

| Duration | C1 seeds | P1b seeds |
|---|---|---|
| 120-240 s | **−19.2 % [−45.6, −6.5]** | −30.4 % [−43.6, −11.8] |
| 240-360 s | +23.7 % | — |
| 360-480 s | +33.8 % | +32.5 % |

- A bin-free OLS crossover sits at 231 s [204, 252] (C1) and 233 s [212, 249] (P1b), so about 31 % of U(120, 480) lies below it.
- For incidents of 120-180 s, IP is worse than PI in 18 of 18 C1 seeds.
- The pattern replicates on two independent seed sets.
- Duration is drawn from the seed, independent of the arm, so this is not selection on a post-treatment variable.

**Meaning.** The C1 sentence is true for the pre-registered duration law. But the lead is an *identifiable regime* (long incidents), not a uniform advantage. This fits your own "conditional advantages" design principle, but only as an exploratory, post-hoc result unless it is pre-registered.

**Test.** `audit/G2/g2_duration_split.py`, `audit/verify3/G2-F3-*`.

#### B5. The C1 comparator is neither the strongest always-on arm nor fully tuned [HEADLINE-F2 (+PROV-F3, REPRO-F9), CTRL-F2 (+TEXT-F11); major by override; each 2 votes: reproduce CONFIRMED / major, defend CONFIRMED / minor]

**What.**
- In P1b's block_q1600, the lowest-median L0 arm was **FB (247.9 s), not PI (252.1 s)**. IP vs FB is 15.9 % (diff-CI lower bound 17.8 s). C1 ran only IP, PI, N and NC.
- The C1 PI (`p70_120_8_e4`) sits on **two upper grid edges** (K_P = 70, K_I = 120), with the tuning surface still falling there. It is **Pareto-dominated**: 6 PI laws are better in both incident types, e.g. `p70_70_10_e4` 172.6 / 255.1 s vs 189.4 / 293.4 s.

**Defence.**
- The paper's wording "relative to always-on PI" is accurate.
- Fig. 2 labels FB as the strongest L0.
- On P1b seeds IP still beats better PIs by 14-21 %, so C1 probably survives in sign.

**Why I override to major.** The introduction frames the question as "beyond strong always-on feedback". The confirmed comparator is neither the strongest nor tuned to an interior optimum. CLAUDE.md requires "no weak baselines". A reviewer would ask for an extended PI grid and for FB in C1.

**Test.** `audit/CTRL/out/pareto_all.txt`, `audit/CTRL/out/pi_surface.txt`, `audit/HEADLINE/l0_medians.py`. New runs: extended PI grid + C1-style test on fresh seeds (needs approval).

### 6.C Plant realism

#### C1. q2000 is oversaturated even without an incident; the uncontrolled plant loses about 40 % of capacity [PLANT-F1; major; 2/2 CONFIRMED / major]

On clean days:
- the best metered arms serve about 1,450-1,610 veh/h;
- no control serves about 960-1,010 veh/h;
- at q2000 the median number of vehicles in the system at control end is 223.

The roughly 40 % "capacity drop" probably comes from zipper merges without lane changing. It is much larger than typical empirical values (the agent's general knowledge, not checked against a source). The paper presents q2000 as an incident cell, without saying that the plant is overloaded there regardless.

#### C2. "No vehicle crossed on red" and the emergency-stop statement rest on non-physical simulator behaviour [PLANT-F3 (+G3-F2, G4-F1, G4-F6..F8), PROV-F5, PLANT-F13 (+G3-F1, F4, F5); PLANT-F3 major 2/2 CONFIRMED; PLANT-F5 downgraded to minor]

**What SUMO does.**
- In SUMO 1.27.1 a non-runner cannot pass a red link. If it cannot stop, it is placed at the stop line with speed 0: an "emergency stop at the end of lane", with implied deceleration around 26 m/s² and overshoot up to 11 m.
- There are 44,816 such events in 11.8 % of P1b runs, and they *are* the "emergency stops" behind the paper's 12.8 %.

**Consequences for the paper's statements.**
- "No red crossing" is therefore true by construction, not a measured outcome.
- The comparison "87 % (no amber) → 12.8 %" is before/after across two studies that also differ in minimum red, rate cap, PI law, action set, tuned arms and seeds. On the 30 matched specs it is 67.6 % → 14.7 %. "The amber phase reduced" is not established as causal.
- Collisions were checked with `collision.check-junctions false`, so the zipper merges were not checked. 4 C1 re-runs with the check on found 0. The earlier claim that hard braking concentrates at the merges was mostly refuted: it is on the incident lanes.

#### C3. The plant is under-described, and its origin is not credited [TEXT-F12 (+PLANT-F12, G4-F4), LIT-F3 (+PLANT-F11); major; 2/2 each]

Not stated in the paper:
- the Flow / Vinitsky et al. (2018) origin of the geometry and of the FB meter defaults. The likely source is Vinitsky et al., ITSC 2018, pp. 759-765, doi 10.1109/itsc.2018.8569615; metadata verified, content not read;
- the 10 % 'av' vType;
- the IDM parameters;
- the 0.5-s step;
- the random depart lane;
- the crawl being on the 2-lane edge and more severe than a closure;
- the 50/50 type mix assumed in tuning;
- the drain cap.

A reviewer cannot rebuild the plant from the paper.

### 6.D Errors in the text and citations (no new data needed)

| Item | Paper line | What is wrong | Evidence | Votes |
|---|---|---|---|---|
| S23-F1 | 193 | "upper bounds ranged from 13.3 % to 47.9 %": 13.3 is P1's slow_q2000 upper bound; P1b's range is **19.3-47.9 %** | `p1_result.json /eval/S2/slow_q2000/x = 0.1331`; P1b x = 0.479, 0.193, 0.254, 0.224 | 2/2 major (+ my own check) |
| S1-F1 | 165 | Table II caption: "positive favours the second arm"; it favours the **first-named** arm (rel = median(r − t)/median(r) with t first, as in R(IP, ID)) | `v5b/p1b/analysis.py@93ba655:353-355`; `v5b/p1/stats.py:52-63` | 2/2 major + FU2 |
| TEXT-F5 | 118 | N = "best constant rate": at q2000 N is `f10_8`, a feedback law | `p1b_result.json tune.arms['2000'].N` | 2/2 major |
| TEXT-F6 | 100 vs 118 vs Table I | What ID knows: "starts and ends" vs "only that an incident has started" vs "onset (and clearance)" | text | reproduce major, defend minor |
| LIT-F1 (+G8-F4, CTRL-F10) | 65, 81, 118 | AD-ALINEA / set-point adaptation cited to Smaragdis & Papageorgiou 2003; it is Smaragdis, Papageorgiou & Kosmatopoulos **2004**, TR-B 38(3):251-270 (the protocol cites 2004 correctly). AD here is the study's own sign rule | abstracts of both; 2008 full-text attribution | 2/2 major + G8 |
| LIT-F2 (+G8-F5) | 65 | Carlson2010 is model-based optimal control, not "the same laws"; the feedback MTFC benchmark is Carlson et al. 2014 (TR-C 46:209-221, not cited) | abstracts; Frejo full texts | 2/2 minor |
| REPRO-F3 | 141 | "We found that a change of controller changes later random draws": no measurement was documented, and spot runs show CRN holds exactly until insertion times diverge | `audit/REPRO/crn_check.py`, `crn_check2.py` | 2/2 major |
| C18 | 85 | Promises wrong-type and false-alarm tolerance; not delivered (A3) | — | CONTRADICTED |
| C29 | 102 | "upper limit for any incident-aware controller": only for N-then-one-action policies; always-on PI beats OR_in on 5-16 % of seeds | `audit/CTRL/` oracles | PARTIALLY |
| LIT-F9 | bib | TOPS2005 lists the wrong author (the UW-Madison ITS Program prepared it for WisDOT, 13 Jan 2005) | report title page | minor |
| C01 | 63 | still `[CITE]`; candidates Knoop et al. 2008 and Skabardonis et al. 2003 (metadata verified, full text not read) | — | UNVERIFIED |
| C15, LIT-F4 | 81 | "green, amber and red signals": the cited works use green-red; the amber is your own design | Papageorgiou 2008 full text | minor |

Citation coverage:
- Read in full: Papageorgiou 2008, Cameron 2016, van Hasselt 2010, Smith & Winkler 2006, both Frejo 2021 papers, the TOPS 2005 report, Sheu 2007 and Dabiri 2014.
- Checked by abstract or landing page only, after every legal route failed (no paywall bypass was attempted): Tympakianaki 2014, Wang 2014, Spiliopoulou 2010, Sun 2013 (TRR article), Wu 2014, both Smaragdis papers, Carlson 2010/2011, Ghiasi 2018 and Hale 2020.
- Bib metadata: all 16 DOI entries match Crossref apart from known Crossref quirks; 4 of the 5 non-DOI entries were confirmed by hand, and TOPS2005 has the wrong author.

### 6.E All finding groups (generated)

Final severity applies the rule in §0.2, with four overrides:
- HEADLINE-F2 → major;
- CTRL-F2 → major;
- CTRL-F3 → major;
- G2-F2 → major.

Reasons are in B1, B3 and B5. "Not adversarially verified" means one agent's finding: for minor and info items that is by design (no skeptic budget was spent on them), and the only single-agent major is G3R-F1, whose numbers critic 2 re-derived independently.

| # | Group (rep id) | Final severity | Raised as | Title | Verification votes (lens: outcome/severity) | Members |
|---|---|---|---|---|---|---|
| 1 | PROV-F1 | **critical** | critical | 'Pre-registered before any data' is false: D2->P1->P1b->C1 sequence and post-hoc choices undisclosed | reproduce: CONFIRMED/critical, defend: CONFIRMED/critical, impact: CONFIRMED/critical | PROV-F1, TEXT-F1, REPRO-F4, C1-F1, CTRL-F7 |
| 2 | COMETRIC | **major** | major | Pre-registered co-metrics (served throughput, TTT) missing; on fixed-window TTT S1b has no passing cell | reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major | FU1-F2, FU1-F8, FU1-F9 |
| 3 | CTRL-F1 | **major** | critical | S1b magnitudes depend on a fragile/dominated ID plan chosen by the pooled-median rule | reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major | CTRL-F1, HEADLINE-F1, FU2-1-F1, FU2-1-F2 |
| 4 | CTRL-F2 | **major** | major | C1 reference PI is Pareto-dominated and on grid edges; tuned arms on grid edges undisclosed | reproduce: CONFIRMED/major, defend: CONFIRMED/minor | CTRL-F2, TEXT-F11 |
| 5 | CTRL-F3 | **major** | major | ID equals the always-on law with N before onset (and IP=ID in block_q2000); comparisons measure only pre-onset effect | reproduce: CONFIRMED/major, defend: CONFIRMED/minor | CTRL-F3, S1-F3, HEADLINE-F7, CTRL-F8 |
| 6 | CTRL-F4 | **major** | major | IP gain comes from type-specific parameters, not timing; controller-family confound undisclosed | reproduce: CONFIRMED/major, defend: CONFIRMED/major | CTRL-F4, C1-F5, TEXT-F10 |
| 7 | DRAIN | **major** | major | End-of-horizon convention (all-green, demand-free drain after 940 s) carries most of every headline gain | reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major | FU1-F1, FU1-F3, FU1-F4, FU1-F5, FU1-F7 |
| 8 | G2-F2 | **major** | major | C1/crawl gains come from L0/ID laws over-holding all four lanes (the crawl lane inflates the edge-4 count; no lane changes); untested with lane changing | reproduce: CONFIRMED/major, defend: CONFIRMED/minor | G2-F2, G2-F4, G2-F1 |
| 9 | G2-F3 | **major** | major | Exploratory: the type-plan gain over PI/ID reverses for incidents shorter than about 230 s and grows with duration (replicated on P1b and C1 seeds) | reproduce: CONFIRMED/major, defend: CONFIRMED/major | G2-F3 |
| 10 | G3R-F1 | **major** | major | The 200 veh/h floor (135-s reds on all four lanes) has no stated reason, is far below the paper's own cited source, binds in every C1 PI run and alone sets PI's rate there; the paper does not disclos… | not adversarially verified | G3R-F1, G3R-F5 |
| 11 | G5-F1 | **major** | major | Pre-registered S3 rows omitted: p*, f* (paper outputs under A10) and the combined row; under d=60, c=60, p=0.2 IP has no CI above zero vs the strongest L0 arm in any cell | reproduce: CONFIRMED/major, defend: CONFIRMED/major | G5-F1, G5-F2, G5-F3 |
| 12 | HEADLINE-F2 | **major** | major | C1 tests IP only against PI; FB was the strongest always-on arm in that cell | reproduce: CONFIRMED/major, defend: CONFIRMED/minor | HEADLINE-F2, PROV-F3, REPRO-F9 |
| 13 | LIT-F1 | **major** | major | AD-ALINEA cited to wrong Smaragdis paper/year; AD arm weak | reproduce: CONFIRMED/major, defend: CONFIRMED/major | LIT-F1, CTRL-F10, G8-F4 |
| 14 | LIT-F3 | **major** | major | Plant geometry and FB baseline from Flow / Vinitsky et al. 2018 not cited | reproduce: CONFIRMED/major, defend: CONFIRMED/major | LIT-F3, PLANT-F11 |
| 15 | PLANT-F1 | **major** | major | q2000 oversaturated without incident; uncontrolled plant loses ~40 % capacity | reproduce: CONFIRMED/major, defend: CONFIRMED/major | PLANT-F1 |
| 16 | PLANT-F2 | **major** | major | Meter off and demand stops after 900 s; large delay share in uncontrolled drain | reproduce: CONFIRMED/major, defend: CONFIRMED/major | PLANT-F2 |
| 17 | PLANT-F3 | **major** | major | No-red-crossing enforced by physically impossible SUMO emergency stops | reproduce: CONFIRMED/major, defend: CONFIRMED/major | PLANT-F3, G3-F2, G4-F1, G4-F6, G4-F7, G4-F8 |
| 18 | PLANT-F4 | **major** | major | Crawl lane forces half the inflow through 1 m/s lane with no lane change; not disclosed | reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major | PLANT-F4, REPRO-F6 |
| 19 | PROV-F2 | **major** | major | Earlier P1 round omitted despite addendum promise; its results differ | reproduce: CONFIRMED/major, defend: CONFIRMED/major | PROV-F2, TEXT-F2 |
| 20 | REPRO-F3 | **major** | major | CRN claim overstated and unsupported by reported experiment or citation | reproduce: CONFIRMED/major, defend: CONFIRMED/major | REPRO-F3, TEXT-F16 |
| 21 | S1-F1 | **major** | major | Table II caption inverts the sign convention | reproduce: CONFIRMED/major, defend: CONFIRMED/major | S1-F1, TEXT-F4, FU2-1-F3 |
| 22 | S23-F1 | **major** | major | Stale P1 value 13.3 % in S2 upper-bound range (should be 19.3-47.9 %) | reproduce: CONFIRMED/major, defend: CONFIRMED/major | CTRL-F5, S23-F1, REPRO-F1, TEXT-F3 |
| 23 | S23-F2 | **major** | major | Pre-registered outputs missing: clean-day cost, prevalence, p*, f*, c*, false-alarm cost, combined row | reproduce: CONFIRMED/major, defend: CONFIRMED/major | S23-F2, S1-F2, TEXT-F8, CTRL-F11, TEXT-F7 |
| 24 | TEXT-F12 | **major** | major | Plant details needed for reproduction missing from the paper | reproduce: CONFIRMED/major, defend: CONFIRMED/major | TEXT-F12, PLANT-F12, G4-F4 |
| 25 | TEXT-F13 | **major** | major | Spill share uses an undisclosed post-run proxy and excludes FX | reproduce: CONFIRMED/major, defend: CONFIRMED/major | TEXT-F13, PLANT-F6, PROV-F7 |
| 26 | TEXT-F5 | **major** | major | N described as constant rate but is a feedback law at q2000 | reproduce: CONFIRMED/major, defend: CONFIRMED/major | S1-F7, TEXT-F5 |
| 27 | TEXT-F9 | **major** | major | C1 reporting gaps (rule, CI, post-hoc, PI only, metric name) | reproduce: CONFIRMED/major, defend: CONFIRMED/major | TEXT-F9 |
| 28 | C1-F3 | **minor** | minor | Decision rule tests >=10 % on point estimate only; CIs include gains below 10 % | not adversarially verified | C1-F3, REPRO-F11, S1-F4 |
| 29 | C1-F7 | **minor** | minor | Emergency-stop population and braking warnings not stated | not adversarially verified | C1-F7 |
| 30 | C1-F8 | **minor** | minor | C1 descriptive rows not labelled descriptive | not adversarially verified | C1-F8 |
| 31 | CTRL-F12 | **minor** | minor | Wrong-type p* is a per-seed exact mixture, not simulated misclassification | not adversarially verified | CTRL-F12 |
| 32 | CTRL-F6 | **minor** | major | TP placebo is not a like-for-like measure of OR_in noise inflation | reproduce: CONFIRMED/minor, defend: CONFIRMED/minor | CTRL-F6, S23-F5 |
| 33 | CTRL-F9 | **minor** | minor | Fig. 2 strongest always-on arm chosen per cell on evaluation seeds | not adversarially verified | CTRL-F9 |
| 34 | G2-F5 | **minor** | minor | The gain over no control comes from avoiding a post-clearance zipper breakdown; the paper does not explain this | not adversarially verified | G2-F5 |
| 35 | G3R-F2 | **minor** | minor | Long-wait warnings (H-R5, a vehicle waiting > 120 s) appear only in arms that reach the floor and are not reported; the results survive excluding them | not adversarially verified | G3R-F2 |
| 36 | G3R-F3 | **minor** | minor | Actuation lag of switched law plans: real and pre-registered, with no measurable bias; the critic's proposed mechanism is not supported; the 30-s update period and the R3 'no P kick' rule are missing… | not adversarially verified | G3R-F3 |
| 37 | G3R-F4 | **minor** | minor | C1's tolerance of detection delay comes from a slow-acting plan, not from robust use of type information | not adversarially verified | G3R-F4 |
| 38 | G4-F5 | **minor** | minor | Cycle formula written with the demand q; the code uses the commanded rate | not adversarially verified | G4-F5 |
| 39 | G5-F4 | **minor** | minor | c* '> 180' in three cells is vacuous: the stay plans cannot be affected by a clearance delay | not adversarially verified | G5-F4 |
| 40 | G5-F5 | **minor** | minor | 'Detection delay' means onset delay only; Table I overstates which information the tuned plans use | not adversarially verified | G5-F5 |
| 41 | G8-F6 | **minor** | minor | 'Feedback laws ... apply directly' sits beside a source that reports calibration and auto-tuning were needed | not adversarially verified | G8-F6 |
| 42 | HEADLINE-F3 | **minor** | minor | Printed S1 intervals are rel CIs, not the decision-rule diff CIs | not adversarially verified | HEADLINE-F3 |
| 43 | HEADLINE-F4 | **minor** | minor | Bootstrap Monte Carlo error of 0.99375 bounds exceeds printed precision | not adversarially verified | HEADLINE-F4, S1-F5 |
| 44 | HEADLINE-F5 | **minor** | minor | 'Same result excluding invalid runs' is vacuous: zero invalid runs | not adversarially verified | HEADLINE-F5, C1-F4, PROV-F10, REPRO-F8 |
| 45 | HEADLINE-F6 | **minor** | minor | 'Reduced median delay by 16.2 %' is not the change in the median | not adversarially verified | HEADLINE-F6, C1-F2, FU2-1-F4 |
| 46 | LIT-F10 | **minor** | minor | Bias results concern expectations; paper reports medians | not adversarially verified | LIT-F10, G8-F8 |
| 47 | LIT-F11 | **minor** | minor | Cited mainline metering engages only in near-stopped traffic | not adversarially verified | LIT-F11 |
| 48 | LIT-F12 | **minor** | minor | C01 opening sentence uncited | not adversarially verified | LIT-F12 |
| 49 | LIT-F13 | **minor** | minor | C07 wording mismatches cited methods | not adversarially verified | LIT-F13, G8-F2, G8-F3 |
| 50 | LIT-F2 | **minor** | major | Carlson2010 is optimal control, not the same feedback laws | reproduce: CONFIRMED/minor, defend: CONFIRMED/minor | LIT-F2, G8-F5 |
| 51 | LIT-F4 | **minor** | minor | Amber presented beside sources using green-red signals | not adversarially verified | LIT-F4 |
| 52 | LIT-F5 | **minor** | minor | Feedback laws use 0.5-s count snapshot, undisclosed | not adversarially verified | LIT-F5 |
| 53 | LIT-F6 | **minor** | minor | AD arm is the paper's own sign rule, not stated | not adversarially verified | LIT-F6 |
| 54 | LIT-F7 | **minor** | minor | Runner shares not compared with field numbers | not adversarially verified | LIT-F7, G8-F1 |
| 55 | LIT-F9 | **minor** | minor | TOPS2005 wrong author and missing report details | not adversarially verified | LIT-F9 |
| 56 | PLANT-F10 | **minor** | minor | Amber threshold and dilemma zone not stated; 3-s amber short for 23 m/s | not adversarially verified | PLANT-F10, G4-F2, G4-F3 |
| 57 | PLANT-F5 | **minor** | major | Emergency braking at downstream merges in 94.5 % of metered runs unreported | reproduce: CONFIRMED/minor, defend: REFUTED/minor | PLANT-F5, G3-F3 |
| 58 | PLANT-F7 | **minor** | minor | Delay reference speed is the incident-reduced lane limit | not adversarially verified | PLANT-F7, FU1-F6 |
| 59 | PLANT-F8 | **minor** | minor | Emergency-stop share dominated by meter start-up transient | not adversarially verified | PLANT-F8 |
| 60 | PLANT-F9 | **minor** | minor | Runners cross later reds whenever they cannot brake | not adversarially verified | PLANT-F9 |
| 61 | PROV-F4 | **minor** | minor | 'Run once from frozen code' does not hold for P1 or D1/D2 | not adversarially verified | PROV-F4 |
| 62 | PROV-F5 | **minor** | minor | Amber 87 % -> 12.8 % emergency-stop reduction compares two different studies | not adversarially verified | PROV-F5, C1-F6, TEXT-F14 |
| 63 | PROV-F6 | **minor** | minor | Seed use departs from approved block labels; not disclosed in paper | not adversarially verified | PROV-F6 |
| 64 | REPRO-F2 | **minor** | major | Fig. 2 marginal medians disagree with paired statistics | reproduce: CONFIRMED/minor, defend: CONFIRMED/minor | REPRO-F2 |
| 65 | REPRO-F5 | **minor** | minor | Fig. 1 text labels overlap | not adversarially verified | REPRO-F5, G2-F6 |
| 66 | REPRO-F7 | **minor** | minor | 'Incident of random type may occur' does not match cell design | not adversarially verified | REPRO-F7 |
| 67 | S1-F6 | **minor** | minor | S1 family and interval construction not described | not adversarially verified | S1-F6 |
| 68 | S1-F8 | **minor** | minor | Table II shows S1a only against PI; FB also blocks S1a | not adversarially verified | S1-F8 |
| 69 | S23-F3 | **minor** | minor | 'Lead vanished within 3 s' is an interpolation artefact | not adversarially verified | S23-F3 |
| 70 | S23-F4 | **minor** | minor | 'Stayed ahead to ~120 s' omits wide CI and zero margin | not adversarially verified | S23-F4 |
| 71 | S23-F6 | **minor** | minor | Plateau criterion unattainable at n=100 and tests ORX only | not adversarially verified | S23-F6 |
| 72 | TEXT-F15 | **minor** | minor | Loaded or overstated wording | not adversarially verified | TEXT-F15 |
| 73 | TEXT-F17 | **minor** | minor | Small internal inconsistencies | not adversarially verified | TEXT-F17 |
| 74 | TEXT-F18 | **minor** | minor | Other protocol-required outputs absent (NC row, operating map, tool checks) | not adversarially verified | TEXT-F18 |
| 75 | TEXT-F6 | **minor** | major | What ID knows is defined inconsistently | reproduce: CONFIRMED/major, defend: CONFIRMED/minor | TEXT-F6 |
| 76 | C1-F9 | **info** | info | C1 throughput co-headline not reported | not adversarially verified | C1-F9 |
| 77 | CTRL-F13 | **info** | info | No data leakage found | not adversarially verified | CTRL-F13 |
| 78 | CTRL-F14 | **info** | info | Unequal tuning freedom across arms | not adversarially verified | CTRL-F14 |
| 79 | FU2-1-F5 | **info** | info | Round-1 VERIFIED verdicts on C66, C69, C71 contradict the tracers' own failure points | not adversarially verified | FU2-1-F5 |
| 80 | G2-F7 | **info** | info | The protocols give node-to-node lengths, not the simulated lane lengths | not adversarially verified | G2-F7 |
| 81 | G5-F6 | **info** | info | slow_q1600 c* is non-monotone and interpolated; a 60-s late return beats the exact return | not adversarially verified | G5-F6 |
| 82 | G8-F7 | **info** | info | Several cited works remain abstract-only after all legal routes failed | not adversarially verified | G8-F7 |
| 83 | HEADLINE-F8 | **info** | info | slow_q1600 median and mean disagree in sign | not adversarially verified | HEADLINE-F8 |
| 84 | HEADLINE-F9 | **info** | info | Headline numbers verified from raw data | not adversarially verified | HEADLINE-F9 |
| 85 | LIT-F14 | **info** | info | PI degradation with runners unexplained vs literature | not adversarially verified | LIT-F14 |
| 86 | LIT-F15 | **info** | info | Bib metadata state | not adversarially verified | LIT-F15 |
| 87 | LIT-F16 | **info** | info | FB and PI laws match ALINEA/PI-ALINEA structure | not adversarially verified | LIT-F16 |
| 88 | LIT-F8 | **info** | info | PI-ALINEA first proposed in Wang & Papageorgiou 2006 | not adversarially verified | LIT-F8 |
| 89 | PLANT-F13 | **info** | info | Collision check excludes junctions | not adversarially verified | PLANT-F13, G3-F1, G3-F4, G3-F5 |
| 90 | PLANT-F14 | **info** | info | Floating-point artefact in signal clock | not adversarially verified | PLANT-F14 |
| 91 | PLANT-F15 | **info** | info | Protocol edge lengths differ from built network | not adversarially verified | PLANT-F15 |
| 92 | PROV-F8 | **info** | info | Frozen worktrees deleted; frozen launch inferred | not adversarially verified | PROV-F8 |
| 93 | PROV-F9 | **info** | info | Hashed P1 page lists D1-D5 as open choices | not adversarially verified | PROV-F9 |
| 94 | REPRO-F10 | **info** | info | Reproducibility positives; build artefacts not versioned | not adversarially verified | REPRO-F10 |
| 95 | S1-F10 | **info** | info | summary.md labels page path with addendum hash | not adversarially verified | S1-F10 |
| 96 | S1-F11 | **info** | info | 'Never beat PI' is a median statement | not adversarially verified | S1-F11 |
| 97 | S1-F9 | **info** | info | Integrity checks passed; tiny selection margins for two IP plans | not adversarially verified | S1-F9 |
| 98 | S23-F7 | **info** | info | S2 bracket mixes estimands and confidence levels without disclosure | not adversarially verified | S23-F7 |
| 99 | S23-F8 | **info** | info | Table II d* row lacks CIs and binding arms | not adversarially verified | S23-F8 |
| 100 | S23-F9 | **info** | info | TP wording 'best of five replicate runs' is inaccurate | not adversarially verified | S23-F9 |
| 101 | TEXT-F19 | **info** | info | Draft state: limitations not written | not adversarially verified | TEXT-F19 |

---

## 7. What the paper can and cannot claim, after this audit

This section is my reading of the evidence, not a decision; the decisions are yours.

**Can claim** (evidence verified):
- On one SUMO bottleneck (BN4, from Flow / Vinitsky 2018), with one signal across four lanes, no lane changing, Poisson demand and an uncontrolled drain after 940 s, and given an incident:
  - **Presence alone did not meet the pre-registered bar** against the tuned always-on arms (S1a FAIL). This is robust.
  - **Type plans passed the pre-registered S1b rule** in two of four cells: 11.8 % [5.8, 16.7] and 22.0 % [8.8, 31.4], *under the pre-registered pooled-median tuning rule for ID*.
  - **In the lane-crawl cell at 1,600 veh/h, the type plan beat always-on PI on 100 fresh seeds**: 16.2 % [7.3, 23.7], i.e. 41.4 s/veh [16.6, 65.7]. The pre-registered C1 rule is met, and the result also holds on window TTT (11.7 %) and full TTT (13.8 %).
  - Per-incident hindsight can only be bracketed, and the in-sample oracle is strongly inflated by simulation noise.
- Each study's statements, seeds and code were fixed and hashed before that study's data. Every run is accounted for; nothing failed; the numbers are reproducible bit for bit.

**Cannot claim** (or only with stated caveats):
- That *all* statements were pre-registered before *any* data (A1).
- That "knowing the type adds 11.8 % / 22.0 %" as a stable information value. The magnitude depends on the ID tuning rule (B1), and for slow_q2000 on the drain convention (B2). On the pre-registered TTT co-metric no S1b cell reaches 10 %.
- That the type plan beats *strong* or *the strongest* always-on feedback. C1's comparator is PI, which is Pareto-dominated and sits on grid edges; FB was stronger there (B5).
- That the C1 gain is a general property of type information. It arises from a crawl without lane changes, a detector that counts the crawl lane, and a 200 veh/h floor (B3). It reverses for incidents shorter than about 230 s (B4). With 20 % wrong-type errors it is gone vs FB (A3).
- That amber *caused* the drop in emergency stops (C2), or that "no red crossing" is a safety result.
- Anything about tolerance to wrong type or false alarms, *unless* p* and f* are added. They are unfavourable.
- That q2000 metering is feasible: it needs unlimited upstream storage, and the plant is oversaturated there anyway (C1).
- Ramp metering, prevalence, generality or novelty (unchanged from `p1b_result.md` §6).

---

## 8. Actionable verification steps

Every step below is a proposal. Nothing has been changed.

### 8.0 Keep the evidence (done, V131)

- The report and the register are in `docs/audits/paper1_2026-10-21/`.
- The scripts and small outputs are in `~/work/phd/v5b1_runs/audit_paper1_2026-10-21/`: 76 MB, 1,004 files. Caches over 10 MB and extracted code are listed in `EXCLUDED_CACHES.txt` and can be regenerated.

### 8.1 Check the audit yourself (read-only, minutes)

Use the project venv with `PYTHONDONTWRITEBYTECODE=1`. The arguments for each script are in Appendix C.

| What to check | Command or script |
|---|---|
| "13.3 %" is P1's number | `python3 -c "import json;print(json.load(open('docs/research/results/p1_result.json'))['eval']['S2']['slow_q2000']['x'])"` gives 0.1331 |
| Table II caption sign | read `git show 93ba655:v5b/p1/stats.py \| sed -n 48,64p` (d = r − t) and `git show 93ba655:v5b/p1b/analysis.py \| sed -n 350,356p` (t = first-named arm) |
| N is a feedback law at q2000 | `python3 -c "import json;print(json.load(open('docs/research/results/p1b_result.json'))['tune']['arms']['2000']['N'])"` gives `f10_8` |
| Drain convention | `git show 93ba655:v5b/p1b/episode.py \| sed -n 236,252p` |
| Rate floor | `git show 93ba655:v5b/p1b/meters.py \| sed -n 29,40p` |
| Pre-registration timeline | `bash audit/PROV/page_sha.sh`; `git log --format='%h %ad %s' --date=iso -- docs/research/protocols/` |
| Headline numbers, blind | `audit/HEADLINE/load_runs.py`, then `headline.py`, `repo_seed_replay.py` |
| ID-rule sensitivity | `audit/HEADLINE/selection_bootstrap.py`; `audit/CTRL/` (`s1_sensitivity`, `pareto_id`) |
| Drain split and co-metrics | `audit/FU1/drain_audit.py`, `audit/verify2/DRAIN-reproduce/drain_split.py` |
| C1 mechanism and floor | `audit/G2/g2_mechanism.py`, `audit/G3R/g3r_floor.py`, `audit/verify3/G2-F2-reproduce/mech.py` |
| Duration dependence | `audit/G2/g2_duration_split.py` |
| Omitted S3 rows | `audit/G5/g5_recompute.py`, `audit/S23/s23_extra.py` |

### 8.2 Text fixes that need no new data (your decision)

1. Reword lines 69 and 145: pre-registration per study. Disclose D1/D2 → P1 → P1b → C1, the post-hoc choice of the C1 cell and comparator, and the C1 rule.
2. Report P1, at least in one paragraph and a supplementary table, as the P1b addendum promised. Say that the C1 effect appeared after adding PI-law plans to A.
3. Correct "13.3 %" to "19.3 %". Fix the Table II caption sign. Fix N's definition ("best of 20 constant rates and 30 FB laws on clean days"). Make ID's knowledge consistent (onset, plus clearance for back actions). Cite Smaragdis et al. 2004 for AD-ALINEA, and say AD uses its own sign rule. Replace or qualify Carlson2010 (consider Carlson et al. 2014). Credit Flow / Vinitsky et al. 2018. Fix the TOPS2005 author. Add a source for line 63, or rephrase it.
4. State the plant conventions:
   - Poisson demand stopping at 940 s;
   - the all-green drain;
   - the 30-s update grid on the edge-4 count;
   - the 200 veh/h floor and its 135-s reds;
   - the 10 % AV type and the IDM parameters;
   - lane changing off, and that the crawl lane is fed by two lanes;
   - SUMO's forced stops at red;
   - the collision check excluding junctions;
   - timeLoss measured against the incident speed limit.
5. Report the pre-registered outputs that exist in `p1b_result.json`:
   - clean-day cost per arm;
   - false-alarm cost;
   - p\* and f\* (A10 lists them as paper outputs);
   - optionally c\* and the combined row;
   - CIs for d\*.
6. Report the pre-registered co-metrics (served throughput as a paired difference; window TTT), at least for S1 and C1. State how much of the gain accrues after 940 s.
7. Soften or qualify wording:
   - "honest", "strong", "full set", "upper limit", "never better", "the lead held";
   - "reduced median delay by 16.2 %" → "the median paired reduction was 16.2 % of PI's median delay";
   - "the same result when seeds with invalid runs are excluded" → "no run was invalid";
   - "We found … common random numbers" → describe the spot-run evidence;
   - "85-100 % of metered runs" → define the indicator and give FX's values.
8. In the Discussion (still empty), name the C1 mechanism (B3), the duration regime (B4) and the selection sensitivity (B1).

### 8.3 Further analyses on existing data (no new simulation; label them post hoc and descriptive)

These run only on stored runs, in minutes:
- the S1b sensitivity to the ID tuning rule;
- the drain split;
- the duration split;
- the floor-time correlation;
- the tuning-seed resampling.

The audit scripts already do this. If any goes into the paper, it must be labelled exploratory.

### 8.4 New experiments (each needs a protocol, fresh approved seeds such as 7,400,800-999, and your approval)

Run-count estimates assume the measured 9.6 runs/s (`p1b_result.md` §8). They are rough; check them before planning.

| Question | Design sketch | Rough size |
|---|---|---|
| Is the C1 comparator too weak? | Extend the PI grid at q1600 past K_P = 70 and K_I = 120; re-tune on the tuning seeds; C1-style test of IP vs the new PI **and vs FB** on fresh seeds | about 8,000 tuning runs + 300 runs: under 20 min |
| Does the result depend on the drain? | Re-run the S1 and C1 arms with control kept active during the drain (the F3Z convention) | about 3,200 + 400 runs: under 10 min (more if re-tuning is required) |
| Does it depend on the 200 veh/h floor? | Floor at about 40 % of metered capacity (≈ 600 veh/h); re-tune, then re-test | P1b-size tuning (≈ 75,000 runs, ≈ 2.2 h) + evaluation |
| Is it an artefact of no lane changes? | Blockage variant with lane changing on (a real closure); tool checks T0/T1 first | comparable to P1b (≈ 345,000 runs, ≈ 10 h) |
| Is the duration regime real? | Pre-register a duration split (e.g. ≤ 230 s vs > 230 s) and test on fresh seeds | ≈ 400-800 runs: minutes |

---

## 9. Limits of this audit

- **Agents, not people.** 93 model agents and I did the checks. Their scripts and outputs are kept so they can be re-run (Appendix C). Agents can still make mistakes. The adversarial lenses reduce this risk but do not remove it. Wherever two agents disagreed, both verdicts are shown.
- **Not every finding was adversarially verified.** All critical and major groups were, except G3R-F1 (the rate floor). Its numbers were derived independently twice (critic 2 and G3R), and I checked the code value and the cited source myself, but it had no defend lens. Minor and info findings are single-agent.
- **Literature.** Several citations were checked only by abstract or landing page, because legal full-text access failed (§6.D). No paywall or bot protection was bypassed. "VERIFIED" for those citation sites means the abstract supports the sentence.
- **SUMO internals.** Statements about SUMO behaviour come from reading the SUMO 1.27.1 source and from the stored logs: forced stops, amber decisions, timeLoss against the current speed limit. Two of them were inferred from data and general knowledge rather than from the source; their dossiers in Appendix A say so.
- **Realism judgements are not field validation.** Comments on capacity drop, floors and runner shares compare against the cited sources and general knowledge, not against field data for this plant.
- **No new experiments.** Questions that need new simulations (§8.4) are open. The audit shows only that the paper's current evidence does not settle them.
- **Draft state.** The Abstract, Discussion and Conclusion are empty. Some omissions may be planned for those sections; the audit judges the text as it stands at `4de404a`.
