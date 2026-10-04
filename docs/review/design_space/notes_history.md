# Design-space notes: project history, decisions and lessons (v4 → v5 → vsl_lab)

*Written 2026-10-04 for the design-space heatmap / DRL-family choice. Read-only survey; nothing was run, nothing else was modified. Every fact carries a source. "[INF]" = my inference, not stated in a document. "[VERIFY]" = literature or tool claim I did not check against a primary source.*

## 0. Sources and aliases

| Alias | File (v5 repo `/srv/shared/Workspace/phd/phd_speed_harmo_v5`, branch `claude/vsl-lab-core`, unless stated) | Read |
|---|---|---|
| PLAN | `docs/plans/phd_thesis_plan_v0.md` (v0.6, 2026-05-19) | §1–4, §6, §8–12 in full; §5, §7 skimmed |
| CAT | `docs/experiment_catalog.md` (v0.2, 2026-05-19) | full |
| AUDIT | `docs/audit_2026-05-20_fresh_thread.md` | full |
| FEAS | `docs/feasibility_study_2026-05-20_harmonization_layer.md` | full |
| GAME | `docs/lessons_metric_gameability.md` (2026-05-21) | full |
| SCREEN | `docs/plans/vsl_hybrid_screen_v0.md` (2026-10-01) | §1–3.1, §3.4–§10 full; §3.2–3.3 paper table not read |
| ROAD | `docs/plans/vsl_drl_run_roadmap_v0.md` (2026-10-01) | full |
| STATUS | `docs/lab/STATUS.md` (2026-10-03 21:00) | full |
| lab/* | `docs/lab/*.md` (46 files; index in App. A) | all results files full; protocols: main text + addenda |
| RC | `docs/review/drl_vsl_reality_check_v0.md` (2026-10-04) | §0–3 full; §4–5 not read |
| SUP | `docs/review/supervisor_note_drl_vsl_v0.md` (2026-10-04) | full |
| RF | `docs/review/drl_vsl_red_flags_per_paper_v0.md` | flag-code table only |
| README, CLAUDE | `README.md`, `CLAUDE.md` | full |
| REP | `reports/2026-05-19_ablation/`, `reports/2026-05-20_full_matrix/` | cross-comparison summaries only |
| AV0 / AV1 | `/srv/shared/Workspace/phd/docs_local/speed_harmo_approach_v0.md` (2026-03-17) / `_v1.md` (2026-03-20) | §1–3 + §5–7 |
| STA | `docs_local/sac_tqc_argument.md` (2026-03-18) | §1–5, §8.6–§11 |
| SDA, CL, VPA, TBC | `docs_local/slowDown_argument.md`, `control_loop.md`, `vsl_placement_argument.md`, `thesis_baseline_chapter.md` | SDA full; CL §1, §4–5; VPA §5–6; TBC §1–2 |
| LLMP | `docs_local/llm_prompts/` (v4 prompt + v4 RBC51 train/eval log, 2026-02-24) | skimmed |
| NC18 | `tests/persistent_results/summary_elaborated_18-03-2026_14-08-30.md` | findings section |
| LL6 | v6 `docs/handoff/lessons_learned.md` | full (cross-reference only) |

Exclusions honoured: no v6 CF06 / feasibility paths were opened; no PDFs read; no raw run JSON printed (two small summary JSONs were inspected by key only).

---

## 1. The author's intent and constraints

| Item | Content | Source |
|---|---|---|
| Thesis | "Adaptive driving algorithms for intelligent road traffic systems"; ≈ 11 months left (submission ≈ Sept 2027); target 2 papers | CLAUDE "Thesis"; LL6 §1 |
| Core requirement | The thesis must show **DRL beating, or measurably improving on, rule-based, reactive or predictive control** | CLAUDE "Thesis"; LL6 §1 |
| Framing | ARC-IT functional view (TM20 VSL, TM21 speed harmonisation for v5); no SOTIF | CLAUDE; round4_harmonisation_protocol "Framing" |
| v5 original intent (Mar–May 2026) | One "cash cow" contribution: TQC + per-lane CAV-direct VSL on a ramp interchange under stochastic anomaly demand, then Papers 2–3 (active-baseline sweep; external comparators MPC/ALINEA/SPECIALIST deferred) | PLAN ADR-012, §3 |
| Oct 2026 spin-off intent | First: a validated, published controller stays in the loop and DRL adds value on top (scheduling, switching, residual, MPC correction). Second message: direct DRL allowed again; exploratory DRL before a gate allowed, but a thesis claim needs frozen candidate, pre-registered comparators, reserved seeds, tuned baselines | CLAUDE "Scope" + "Scope update" |
| Roadmap goal | Find a plant + SAR in which DRL (i) learns, (ii) harmonises, (iii) **really beats something worth beating**; honest-search rules | ROAD "Goal", §0 |
| Supervisor constraint | Supervisor will not approve a methodology or negative-results paper | round4_harmonisation_protocol Addendum E "Author context" |
| Current proposal | Reframe thesis around *when* DRL adds value over tuned control (DRL as scheduler/residual on validated controllers); Paper 1 = R6 + gates (+ optional Han 2024 reproduction); Paper 2 = audit of DRL-VSL evaluations; decisions (a)–(d) pending | SUP "What I propose", "Decisions" |
| Effort to date | v1–v4 2023–2025 "Fixed 3 years, no positive result — supervisor verdict"; "over 1,000 hours" on v4/v5 | PLAN §3; SUP |

---

## 2. The argument for distributional RL (TQC / SAC) and how it held up

### 2.1 How the argument was built (chronological)

| Date | Doc | Claimed reason for distributional RL |
|---|---|---|
| ≤ 2025 (v4) | AV0 §1, STA §1.1 | QR-DQN / C51 / Rainbow-style (RBC51DQN) on discrete posted VSL; the v4 return distribution was described as "genuinely bimodal (merge success vs failure)" but not distinguishable from observations (STA §1.1) |
| 2026-03-17 | AV0 §3.2, §7 | "Traffic return distributions are inherently multimodal" (smooth vs congestion collapse) → learn both modes; CVaR_α (α = 0.1–0.25) risk-averse inference; QR-DQN + NoisyNet chosen (doc says NoisyNet is in SB3-Contrib `QRDQN` [VERIFY — my recollection is that sb3-contrib QRDQN uses ε-greedy, not NoisyNet]) |
| 2026-03-18 | STA §5.2–5.3, §10 | Transitional regime (6,000–7,000 veh/h on ramps_v1) is stochastic: breakdown onset varies (t = 510–600 s); TQC can separate same-mean/different-tail actions; CVaR at evaluation. Pre-stated fall-back: "If TQC = SAC … publishable as a characterization" (§10.2) |
| 2026-03-20 | AV1 §5.2 | Four reasons: (1) bimodal returns from 15 % anomaly injection; (2) HDV compliance stochasticity (Box(5), 8 % non-compliance); (3) overestimation grows with 4-D action; (4) CVaR inference. Plus "No paper in the traffic control literature has applied TQC. This is a directly publishable novel contribution." Predictions: TQC ≈ SAC on mean return, **TQC higher on CVaR10 %**, lower return std, better on anomaly episodes (§7.3) |
| 2026-03-29 | TBC §1 item 3, §2.5 | "Mean-optimal policies … inappropriate for safety-critical traffic control"; anomaly injection exists "to create genuine bimodal return distributions" |
| 2026-05-16/18 | PLAN ADR-003, ADR-009, §6.2, §2.3 | TQC (5 critics × 25 quantiles, drop top-2) "methodologically supersedes TD3LVSL" (TD3 chosen there for overestimation); SAC kept as the "did distributional help?" ablation; "First TQC-based VSL controller" was the load-bearing paper claim. ADR-009: *distributional*, not *distributed* (MARL deferred to PhD) |
| 2026-05-20 | FEAS §3 | Re-scoped after the audit: distributional RL does **not** fit the low-level controller; fits a harmonisation layer only **conditionally**: wave amplification as a random variable, "CVaR of amplification ≤ 1" as probabilistic string stability; the honest contribution is the *necessity question* ("does wave damping need a distributional critic, or does plain SAC suffice?"); "Do not pre-assume TQC wins." Probe A (is amplification heavy-tailed?) is make-or-break |

### 2.2 How each claim held up

| Claim | Evidence | Verdict |
|---|---|---|
| TQC beats SAC | Only data point: 50 % CAV, base reward: TQC Box(4) −321 vs SAC Box(4) −335 reward, 5 seeds, no test; **never measured at 100 % CAV** (the paper scope) | Unsupported (AUDIT Claim 7; CAT §2) |
| TQC's overestimation control matters | No measurement of overestimation anywhere | Unmeasured (AUDIT Claim 7) |
| CVaR / tail improvements | I found **no document** reporting CVaR-based action selection or CVaR10 % returns for any run (searched PLAN §8.5, CAT, REP, AUDIT) | Not tested [INF from absence] |
| Bimodal returns from anomalies | Eval had n = 10 anomaly episodes per config (5 ramp_spike, 5 lane_closure, **0 speed_reduction**); configs with more per-lane differentiation degraded *more* under anomalies; `ramp_spike` adds vehicles with an undefined vType and "probably injects nothing" [INF in source] | Not demonstrated (AUDIT T1; SCREEN §2 (f5)) |
| The TQC controller is useful at all | 100 % CAV TQC Box(4) vs NC: TTS **+23.0 %**, completed trips **−5.9 %**, mean TT +23.3 %, merge 54.7 vs 85.3 km/h; a constant 60 km/h cap Pareto-dominated it (DRL better on 1 of 10 metrics, M60 on 6) | Falsified (AUDIT T3; GAME §2) |
| TQC is load-bearing in the design | FEAS §2 table: "TQC load-bearing — VSL work ✗ decorative" | Rejected by the project's own feasibility study |
| Novelty ("first TQC VSL") | "first to apply algorithm X" judged the weakest novelty class, moot given the negative result; per-lane CAV-direct VSL already in Vinitsky 2018 and Lu 2023 [quotes in AUDIT T4; I did not read the PDFs] | Withdrawn in effect (AUDIT Claim 1, T4) |
| Distributional angle in the Oct lab | Lab trainer accepts `--algo sac/tqc` but raises `NotImplementedError`; only PPO, RecurrentPPO, TRPO were run (`vsl_lab/train/train_sb3.py:130, 221–238`; ledger variants `*_ppo_*`, `*_recurrentppo_*`, `*_trpo_*`). The only confirmed DRL win (R6) is **RecurrentPPO** (memory, not distributional) | Distributional RL never re-tested after May; the positive case points to partial observability / memory instead |
| Probe A (heavy-tailed wave amplification) | Defined, "no probe results are in the repo" | Untested (SCREEN §1 line 15) |

**Net:** the distributional argument was always a *design rationale*, never an *experimental finding*. Its stochasticity premises (anomaly bimodality, HDV compliance noise) were either not exercised in evaluation or removed (100 % CAV). The one well-posed version (FEAS §3: CVaR of wave amplification, necessity question) was never tested.

---

## 3. The argument for per-vehicle diversity and how it held up

*The phrase is ambiguous in the documents; I read it two ways and cover both.*

### 3.1 (i) Heterogeneous per-vehicle fleet as a source of return variance

| Element | Content | Source |
|---|---|---|
| Fleet | 140 vehicle types, 3 compliance groups (from v4), added 2026-03-22 | PLAN §7.3; git `367dbc8` |
| Heterogeneity | HDVs: 4 classes (cars 70 %, vans 12 %, trucks 12 %, truck-trailers 6 %), Krauss τ ∈ [1.2, 2.0] s, σ ∈ [0.30, 0.50]; 4 % "reckless outliers" (speedFactor 1.15–1.25, τ 0.6–0.9 s, lcAssertive 1.5–3.0); CAVs deterministic; weather profiles (clear 0.7 / rain 0.2 / fog 0.1) | TBC §2.3 |
| Why | Box(5) posted sign with 92 % compliance: "creates **stochastic HDV compliance** as a source of return variance — the key differentiator for TQC vs SAC" | SDA §4; AV1 §5.2 reason 2 |
| What happened | Headline runs moved to **100 % CAV** (ADR-008): HDV variants "present in the fleet but not spawned" | PLAN ADR-008, §7.3 |
| | Compliance in Box(4) is binary (CAV 100 %, HDV 0 %); "the v4 three-group compliance model is **dead code**" (needs a missing `network_config_4_3.yaml`) | SCREEN §2 (f2) |
| | Box(5) (the compliance-noise variant) underperformed Box(4) (−335 vs −321) and was dropped by ADR-014 | PLAN ADR-004, ADR-014 |
| Lab re-test of human diversity | Realism gate driver variants: H1 1 s action step, H2 `driverstate` perception noise, H3 W99, H4 EIDM with estimation/driving errors, H5 EIDM defaults. None passed; **H4 collapsed** (not drained, 5,784 s door-to-door) | t2_realism_protocol §Plant, Addendum B |
| Diversity as a hidden condition for adaptation | LD3: compliance-mix family G = 0.8 %, truck-share family G = 4.0 % (no DRL target) | round4_gscan.md |
| | MRG3 R2 with hidden p_nc ∈ {0.1, 0.3, 0.5} never ran (plant failed R1) | t2_mrg3_r2_protocol; t2_mrg3_r1.md |
| Author observation | SUMO car-following models (Krauss, IDM, EIDM) "behave like idealised ADAS" | t2_realism_protocol "Why" |
| FEAS version | Heterogeneous HDVs → heavy tail of wave amplification (Probe A) | FEAS §3, §5; untested |

**Verdict:** per-vehicle driver diversity was argued as the noise source that would make distributional RL pay, but (a) it was switched off for the headline (100 % CAV), (b) the compliance model was not wired in, and (c) where diversity was tested as a hidden condition (compliance, trucks) it changed the best classical setting by ≤ 4 %.

### 3.2 (ii) Per-vehicle / per-lane CAV actuation ("Lagrangian" control)

| Claim | Evidence | Verdict | Source |
|---|---|---|---|
| CAV-direct removes HDV-compliance noise and enables per-lane granularity | Implemented as `slowDown()` on every CAV each 1 s step | Design choice | PLAN ADR-001; SDA §2 |
| Per-lane differential is the contribution | Per-lane base config ranks 4/9 on `lane_sigma`; beats uniform configs only by 1–3 units of *less harm*; at 100 % CAV it is "centralized fleet speed control", not VSL | Invalidated | AUDIT Claim 2, Claim 4 |
| Sparse AVs can act as a moving meter (Vinitsky) | BN4 10 % AVs: AV caps do not bind reactively (T0 FAIL: Δ outflow −6.3 % to +1.6 %, no cell binding), only preventively (T0b: −3 to −16 % outflow = harm); tuned AV feedback worse than NC (+122 to +270 s); DRL ≈ NC on test seeds | Not reproduced in SUMO BN4 | t1_bn4_plant_checks; t1_bn4_r2_baselines; r3_pilots "F1 … conclusion" |
| 25 % AVs gives authority | DRL beats tuned `cap:18` in 0/3 congested cells; meter 50–72 % better | No | r5_bf_av25.md |
| CACC CAVs harmonise | SUMO default CACC at 25 % worsens delay by 46–93 % vs humans; CAV arms show no authority; emergency-braking artefact at 0.5 s | Parked | round4_th.md; round3_tm21_protocol Addendum A |

---

## 4. Chronological table of every experiment / track

Legend: NC = no control; D2D = door-to-door time incl. origin queue; G = adaptivity headroom (pooled-best vs per-condition-best setting); H = headroom vs best non-learning; "rel" = relative change.

### 4.1 v4 and v5 (2023 → May 2026)

| # | Date | Experiment | Plant | Actuator / controller | DRL family | Reward / metric | Result | Verdict | Source |
|---|---|---|---|---|---|---|---|---|---|
| V4 | 2023–2025 (log 2026-02-24) | v1–v4 VSL | 4→3 lane drop (`merge_4_to_3`) | posted VSL (`lane.setMaxSpeed`), 5–7 discrete levels, 150 s window | DQN, QR-DQN, C51/Rainbow ("RBC51DQN") | v7: 9-term reward + mobility-budget constraint | Useful (metastable) regime only 16–27 % of episode; VSL binding share 0.00 on all segments; "Go (authority exists): False" | No positive result in 3 years | PLAN §3; AV0 §1.1–1.5; STA §1.1; LLMP log tail |
| V5.0 | 2026-03-17 | v5.0 plan + feasibility | 4→3 lane drop | Lagrangian CAV `slowDown`, Discrete(7) | QR-DQN + NoisyNet (planned) | 3-term (variance, throughput, smoothness) | 990-scenario sweep: NC never breaks down; every VSL ≤ 6,000 veh/h equal or worse; > 6,500: σ −30–65 % at 8–10 % flow loss ("demand suppression") | Topology abandoned | AV0; AV1 §1.1 |
| V5-r1 | 2026-03-18 | ramps_v1 NC + fixed-VSL sweep | 3L → 4L weave (500 m) → 3L, on+off ramp | fixed CAV `slowDown` 50–110 km/h at 50 % CAV | — | avg\|a\|, hard braking, TTS | NC breakdown onset ~6,000, full at 7,000 veh/h (NC18). 90 km/h: avg\|a\| −30–48 %, hard braking −63–67 %, **TTS +77–327 %**, flow −5–20 %. Ramp VSL "zero measurable effect". Capacity drop recomputed later: **−0.4 %** (6,733 vs 6,760 veh/h) | "Temporal selectivity is what RL must learn" (STA §3.5) | NC18; STA §3.3–3.5; AV1 §1.2; SCREEN §1 line 11 |
| V5-r2 | 2026-03-19/20 | ramps_v2 sweep (990 scen.) | 3L merge, ramp to lane 0 (yield), no off-ramp | uniform M110 | — | σ, braking, flow | M110: σ −17–33 %, hard braking −40–57 %, flow loss < 0.4 % → "no learning required"; 5 DRL seeds converged to fixed 110 | Response: add stochastic demand, anomalies, per-lane Box(4)/(5), TQC vs SAC | AV1 §1.3–1.4; TBC §1 item 2 |
| V5-A | 2026-05-16 | 4-VM vast.ai | ramps_v2, 50 % CAV, stochastic demand + 15 % anomalies | per-lane CAV `slowDown` Box(4); Box(5) adds posted sign | SAC, TQC (5 seeds × 1 M steps each) | r44 reward v4: 5 quadratic terms, 4 of them speed-variance proxies | Reward: SAC4 −335, **TQC4 −321**, SAC5 −343, TQC5 −335 | TQC4 chosen | CAT §2; PLAN ADR-004 |
| V5-B | 2026-05-17 | reproducibility | same | TQC Box(4) | TQC | same | −323.6 (within 2.4 of V5-A) | Pipeline reproducible | CAT §2 |
| V5-C | 2026-05-18/19 | 100 % CAV headline + 9-config reward ablation | ramps_v2, 100 % CAV | TQC Box(4) | TQC, 9 configs × 5 seeds × 1 M steps | reward weights varied | Base reward −164.8; +221 vs NC, +40 vs M60_active; `lane_sigma` 1.61; 0 collisions / 4,320 eval episodes | Declared RQ1 "YES" (later falsified) | PLAN §8.5; REP full_matrix |
| V5-D | 2026-05-20 | fresh-thread audit | same data | — | — | non-gameable metrics | vs NC: TTS +23.0 %, trips −5.9 %, TT +23.3 %; all 9 configs within ~2 % on real KPIs; NC merge 83–86 km/h, congested 1.3 % (**no breakdown**); `ramp_fraction` = 0 in every eval row | **Paper 1 falsified**; reward misspecified; `lane_sigma` gameable | AUDIT §1–2 |
| V5-E | 2026-05-21 | "smoothing rescue" re-eval | same | — | — | accel p95, hard decel, TTC, trips, TTS | M60_active Pareto-dominates DRL; smoothness monotone in posted speed | Rescue failed | GAME §2 |
| V5-F | 2026-05-20 | harmonisation-layer feasibility | ACC/CACC corridor (proposed) | DRL modulates ACC set-speed + time-gap | TQC vs SAC (proposed) | wave amplification under mobility constraint | Probes A and B defined | Never run | FEAS §5; SCREEN §1 line 15 |
| V5-G | 2026-10-01 | code + desk audit (screen) | v5 code | — | — | — | New: eval demand **capped at 3,600 veh/h** (one Bernoulli draw/s/route) vs training 5,500–7,250; arrivals polled 1 per 30 s; `best_model` chosen on the training pool; best non-learning only 2.6 % better than NC on in-network TTS | Root causes: no headroom + no capacity drop + gameable metric + DRL replacing the controller | SCREEN §1–2 |

### 4.2 vsl_lab (2026-10-01 → 2026-10-03), in commit order

| # | Date (Oct) | Track / step | Plant | Controller(s) / actuator | DRL family / structure | Result numbers | Verdict | Source |
|---|---|---|---|---|---|---|---|---|
| L1 | 01 22:09–23:12 | T1 R1 | BN4 (Flow/Vinitsky 4→2→1 zipper), IDM, 10 % AVs | NC, AV caps | — | Capacity drop PASS: peak 1,044 → 900 veh/h (ratio 0.862); T0 AV-cap FAIL (Δ −6.3…+1.6 %, no cell binding); T0b: cap −3…−16 % outflow (harm), **meter +20–22 % outflow**; T3 PASS | Plant has a mechanism; AV caps lack authority | t1_bn4_plant_checks.md |
| L2 | 01 23:36 | T1 R2 tuned baselines | BN4 | NC, cap grid, AV feedback (avfb), Vinitsky feedback meter grid | — | Score (mean D2D): **meter:10:6 224.8 s**, NC 412.3, cap:18 412.8, avfb:2:10 566.1 (meter −45 %) | Frozen baselines | t1_bn4_r2_baselines.md |
| L3 | 01 23:54 | T3 R1/R2 | RING22 (Sugiyama-type ring, IDM, 1 AV) | FollowerStopper (FS), PI-with-saturation | — | Waves in 100 % of NC runs; NC 85.2 % of v_e, FS 88.8 %, **PI 100.2 %** of equilibrium speed | H ≈ 0 by construction | t3_ring_r1_r2.md |
| L4 | 01 23:40–02 05:43 | T1 R3 pilots P1, P1b–f, F1, F2 | BN4 10 % AVs | direct DRL on 22 AV caps (Lagrangian) | PPO (P1, P1b, P1c, P1f, F1, F2), TRPO (P1d), RecurrentPPO (P1e); rewards R-OUT, R-TTS (P1f) | Only P1c (and P1d) passed single-seed screening; F1 (3 seeds × 1,000 updates): all FAIL; R5 test: DRL−NC +8.6 % at q 1,200 (harm), ≈ 0 at 1,600–2,400; F2 (4× batch, lr decay): ±0.3 % vs NC | **FAIL**: screening pass was a false positive; "authority" not "optimisation" | r3_pilots.md; r5_f1_final.md; r3_pilots_protocol Add. A–E |
| L5 | 01 23:57–02 07:59 | T3 R3 pilots P2/P2b–d, P3/P3b | RING22 | hybrid: DRL sets FS set-speed U; direct: DRL sets AV accel | PPO | P2 reward (speed − 0.1·\|a\|) traded vs speed (validation 3.85 → 3.55 m/s); P3 55 collisions → shield; P2b/P3b speed-only reward still FAIL (lag: credit horizon ≈ 20 s vs 30–60 s wave cost); P2c/P2d (γ 0.995, λ 0.99, 2–5 s hold) FAIL | **Done, no DRL win** (PI at ceiling) | r3_pilots.md; r3_pilots_protocol Add. B, E |
| L6 | 02 03:02 | T2 MRG3 v1 R1 | MRG3 merge (3 lanes, 250 m accel lane), Krauss, 30 % non-compliant | posted VSL const, Carlson MTFC | — | T1: breakdown share **0.0** at 6,000/900; T0 FAIL (−3.9 % at b = 0.4); T1c FAIL: every controller worse than NC (const 0.6 +14.4 %, MTFC ρ̂ 20 +87.3 %); D-check: no informative precursors (`t2_dcheck.json`: `precursors_informative` False, empty results) | Plant killed | t2_mrg3_r1.md; t2_dcheck.json (keys only) |
| L7 | 02 07:41 | Round 2 C: DRL schedules tuned meter | BN4 | meter grid (inflow as condition) | (hybrid, not trained) | G = **4.1 %** (from R2 v2 data) | Killed by gate, no runs | round2_protocol §C |
| L8 | 02 08:00–08:32 | Round 2 A: posted VSL on BN4 | BN4, all vehicles, speedFactor normc(1, 0.2) | const VSL, Carlson MTFC (`mtfcb`), meter | DRL pilot A-P5 planned | A-T0 FAIL (outflow −0.8 %, +3.5 %, CIs incl. 0); A-R2: all VSL/MTFC 427–430 s vs NC 430; meter 270 | Stopped: posted VSL cannot bind on a lane-drop that 4 lanes over-feed | round2_a_t0.md; round2_a_r2.md; round2_protocol "A-track stop" |
| L9 | 02 07:42–09:21 | Round 2 D: MRG3 v2 (IDM) → v3 (`departSpeed="avg"`) | MRG3 | — | — | v2: insertion failure (origin queue 1,955); v3: ramp vehicles stranded at accel-lane end, teleports in every cell (58 teleports / 100 runs) | No eligible cell | round2_protocol D-1, D-2 result |
| L10 | 02 09:09 | Round 2 B: 25 % AVs, R2 | BN4-AV25 | NC, caps, avfb, meter | — | meter 226, cap:18 408, NC 414, avfb 624 s | Frozen | round2_b_r2.md |
| L11 | 02 08:45–11:22 | T2 plant-realism gate (0.5 s, 0.2 s, D-3 lcAssertive, D-4 LD3) | MRG3-v3 + driver variants H0–H5; LD3 3→2 lane drop | NC (calibration) | — | 0.2 s: all FAIL (H3 Q_dis/Q_ff 1.056; H1/H5 drop not measurable); D-3 lcAssertive: no drop (H5b 1.011), onsets moved to network entry; LD3: H5 waves −16.4 km/h, origin 100 %, drop not measurable; H3 1.037 | **No plant with an artefact-free capacity drop** | t2_realism_step0.2.md; t2_realism_d3.md; t2_realism_ld3.md; round2_protocol D-3/D-4 |
| L12 | 02 09:20–12:22 | Round 3 TM21 vs TM20 (CAV arms) | MRG3/LD3 with 10/25/50 % CACC CAVs | arm A posted, B posted + CAV enforcers, C per-lane CAV set-speed staircase | MultiDiscrete PPO planned | CACC emergency braking at 0.5 s (23–79 events/run vs 0–2 human); step changes human plant (356 → 392 → 403 s); in T-H: NC with 25 % CACC +93 % / +46 % delay; `cavpi` +180 % / +119 % | **Parked** (no CAV authority; SUMO CACC artefact) | round3_tm21_protocol Add. A; round4_th.md |
| L13 | 02 11:26–15:42 | Round 2 B: B-P6 → B-F → B-R5 | BN4-AV25 | direct AV caps | PPO (F2 config), 3 seeds × 1,000 updates | B-P6 passed only via best checkpoint (1,033 vs NC 978); B-R5: beats `cap:18` in **0/3** congested cells; vs NC −2.3 % only at 1,600; +4.4 % at 1,200; meter 50–72 % better | **No DRL win** | r5_bf_av25.md; STATUS T1-B |
| L14 | 02 12:22–13:11 | Round 4 T-H + R2-H | LD3, H5 (EIDM defaults), 0.2 s | posted const, MTFC, adaptive rule `vslad`, SPECIALIST (2 variants), CAV arms | — | T-H0 PASS (posted VSL cuts stops); no controller "harmonises for free"; tuned `const:0.75` J 287.3 vs NC 380.5 (at 4,500: −25 % delay, −55 % stops); SPECIALIST worse than NC; adaptive rule worse than best constant | Tuned constant is the bar | round4_th.md; round4_r2.md |
| L15 | 02 13:12–03 06:08 | Round 4 DRL pilots P-H (abandoned), P-H2, P-H3 | LD3 | direct posted b (P-H2, 11 levels incl. 0.75); residual on `const:0.75` (P-H3) | PPO 500 updates; reward −(veh-s + 40·stops) | P-H2 final J 342.7 vs `const:0.75` 310.1 (+10.5 %), MTFC 322.3, NC 359.4; P-H3 degraded 1.222 → 1.39–1.44, abandoned at 382/500 | **FAIL** | round4_pilots.md; round4_harmonisation_protocol Add. C–D, outcome |
| L16 | 03 06:52 | Round 4 adaptivity headroom scan | LD3, 10 conditions | 7 constants + NC + `vslad` | — | G = H: demand 2.2 %, compliance 0.8 %, trucks 4.0 %, incident 2.5 % / 1.4 % | **Killed** (VSL harmonisation DRL on LD3) | round4_gscan.md |
| L17 | 03 07:07–07:27 | T1-M meter headroom scan + H step | BN4 + perturbations (slow, block, surge) | Vinitsky meter grid (21), lookup oracle, event scheduler `evsched` | — | G (all 4 kinds): **15.4 % @ q 1,600, 10.3 % @ 2,000**; single-kind families 1.8–8.8 %; H vs best NL: **20.4 % [CI +18, +79 s] @ 1,600**, −3.3 % @ 2,000 (marginal medians nearly equal: evsched 225.3 vs lookup 227.5; heavy tail) | DRL target at q 1,600 only | t1_meter_gscan.md; t1_meter_h.md |
| L18 | 03 07:30–08:57 | T1-M pilots P-M (void), P-M2, P-M3 a/b/c | BN4 + perturbations | **hybrid**: DRL picks 1 of 4 meter settings every 30 s | PPO, PPO + obs-stack 4, **RecurrentPPO (LSTM 64)**; R-TTS | P-M void (health stop at update 2); P-M2 ≈ evsched (+0.1 %, no learning visible); P-M3b RecurrentPPO **−9.6 % vs evsched** [−40.8, −6.7 s]; stack 4 +3.5 %; plain PPO +2.6 % (1 pass of 8 looks) | Exploratory signal | t1_meter_pm.md; t1_meter_gscan_protocol Add. B–D |
| L19 | 03 09:07–10:01 | MPC-F + R5-M | BN4 | MPC with MLP cost model fitted on separate seeds (held-out R² 0.90) | RecurrentPPO F class (3 seeds × 1,000 updates) | Pooled DRL vs evsched −1.0 %, vs MPC-F −0.5 % (CIs incl. 0); only seed 0 beats both; vs meter:10:6 −7.4 %, vs NC −16.4 % | **No claim** (unreliable training) | t1_meter_r5.md |
| L20 | 03 10:11–19:25 | P-M4 + R5-M2 | BN4 | same | RecurrentPPO, seeds 3–5 × 2,000 updates, 1,920 samples/update, checkpoint on 40 episodes | vs evsched −2.7 % [CI incl. 0]; vs MPC-F −4.7 % [−19.6, −4.3 s] but 1/3 learners; per kind: blockage −18 % vs evsched; **90 reserved seeds consumed by mistake** (disclosed) | **No claim** | r5m2.md; t1_meter_gscan_protocol "R5-M2 result" |
| L21 | 03 07:27–10:53 | T4 CORR2 corridor | 9.5 km, 2 metered on-ramps + off-ramp, EIDM H5, 0.2 s | ALINEA (8 settings) at both ramps | — | Calibration flagged (ramp drivers yield; no mainline breakdown); extended grid: off-ramp blocking ~6 of 65 min; **G = 0.4 %**, NC best pooled; ALINEA adds delay | **Killed** | t4_corr2_protocol; t4_gscan.md |
| L22 | 03 19:38 | **R6 confirmatory** | BN4 + 4 perturbation kinds, q 1,600 | frozen P-M4 seed-3 best-val checkpoint vs evsched, MPC-F, pooled, meter:10:6, NC, lookup | RecurrentPPO hybrid meter scheduler | 210 reserved seeds: vs evsched **−4.3 %** [−14.7, −4.9 s]; vs MPC-F **−2.5 %** [−14.9, −0.8 s]; vs lookup oracle +5.8 % (worse); gains from blockages (−19 % / −8.7 %); worse than MPC-F under slowdowns (+3.1 %, within 5 % tolerance) | **CLAIM YES** (only one) | t1_meter_r6.md |
| L23 | 03 19:46–20:47 | Lead 1 (T1-M2): incident severity/duration | BN4, 22 → 21 conditions | meter grid, re-tuned evsched2, MPC-F2 refit | — | Scan G = H_pre 12.0 % (12.2 % after excluding the 360 s blockage, which teleported in 209/220 runs); stage H: literal rule GO (H 11.1 % vs evsched2, picked by median level); under the paired convention best NL = R6-frozen `mpcf_old`, **H = 3.3 %, CI incl. 0** | **Killed** (conservative reading) | t1_meter2_scan.md; t1_meter2_h.md |
| L24 | 03 20:50 | Lead 1 OOD check (exploratory) | same | R6 policy on the new mix | RecurrentPPO | vs mpcf_old +2.8 %; surge outside training range **+16.1 %** vs pooled | R6 does not generalise | t1_meter2_h.md "Exploratory follow-up" |
| L25 | 03 19:48–20:11 | Lead 2: ZM3 zipper merge | merge rebuilt as zipper node; H5/H3/H0 | NC | — | IDM stranding gone; H5: R-a PASS (Q_dis/Q_ff 0.967), R-b −16.9 km/h, R-d 100 %, **R-c FAIL: discharge 1,528 < 1,600 veh/h/lane** | FAIL (near miss); bound not relaxed | t2_zipmerge_protocol; t2_realism_zm.md |
| L26 | 04 | Literature reality check | 39 DRL-VSL papers | — | — | 15/39 no classical comparator; 16 of 23 with one copy/hand-set/omit parameters; none tuned on separate scenarios; tuned comparators → RL loses, ties or wins ≈ 0–2 % | Supports reframing | RC §0–1.4; SUP |

Ledger totals: 136 ledger rows, ≈ 115,000 simulation runs summed over `n_runs`, 2026-10-01 22:09 → 2026-10-03 20:49 (`vsl_lab/runs/ledger.csv`, computed by me).

---

## 5. One row per lab track (requested format)

| Track | Plant | Question | Gate(s) | Result numbers | Verdict | Date |
|---|---|---|---|---|---|---|
| T1 (10 % AVs) | BN4 zipper bottleneck, IDM | Can DRL on AV caps beat tuned control (Vinitsky reproduction)? | R1 T0/T1/T3; R3 screening C1–C3; R5 same-actuator rule | Drop 1,044 → 900 veh/h; AV caps don't bind; F1/F2 ≈ NC (+8.6 % harm at q 1,200); meter −45 % vs NC | Done: DRL ≈ NC; meter dominates | 10-01/02 |
| T1-A | BN4, posted VSL all vehicles | Does TM20 posted VSL/MTFC help on BN4? | A-T0 (\|Δ outflow\| ≥ 5 %) | −0.8 %, +3.5 % (CIs incl. 0); VSL/MTFC 427–430 s vs NC 430 | Stopped (doesn't bind) | 10-02 |
| T1-B | BN4, 25 % AVs | Does more AV authority let DRL win? | B-R5 same-actuator rule | 0/3 cells vs `cap:18`; −2.3 % vs NC at 1,600; meter 50–72 % better | Done: no DRL win | 10-02 |
| T1-C | BN4 | DRL schedules the tuned meter over inflow? | G ≥ 10 % | G = 4.1 % | Killed | 10-02 |
| T3 | RING22 | DRL (hybrid FS set-speed or direct accel) vs PI-with-saturation | R1 waves + control matters; screening | PI = 100.2 % of v_e; all 8 pilots FAIL | Done: H ≈ 0 | 10-01/02 |
| T2 (MRG3 v1–v3) | on-ramp merge, Krauss/IDM | TM20 posted VSL / MTFC at a merge (thesis core) | T1 capacity drop, T0 binding, T1c control matters, realism gate | v1: breakdown share 0; v2: insertion failure; v3: stranded ramp vehicles | Closed by realism gate | 10-01/02 |
| Realism gate | MRG3-v3 × H0–H5, lcAssertive variants, LD3 | Does SUMO reproduce merge congestion signatures? | R-a drop [0.82, 0.97]; R-b waves −10…−25 km/h; R-c no artefacts + discharge ≥ 1,600; R-d origin ≥ 80 % | Waves −14 to −19 km/h everywhere; no artefact-free drop anywhere | FAIL (all) | 10-02 |
| Round 3 (TM21 vs TM20) | MRG3/LD3 + CACC | CAV speed harmonisation vs posted VSL | T-CAV0, T-X, T0-C/B, T1c-C | CACC alone +46–93 % delay; no CAV authority | Parked | 10-02 |
| Round 4 harmonisation | LD3, EIDM H5, 0.2 s | DRL Pareto-better on delay + stops than tuned classical? | T-H0; screening C-H1..3; adaptivity scan G, H ≥ 10 % | `const:0.75` −25 % delay / −55 % stops; P-H2 +10.5 % J vs it; G = H ≤ 4 % | Killed | 10-02/03 |
| T1-M (meter scheduling under perturbations) | BN4 + slow/block/surge | Hybrid DRL schedules validated meter vs event scheduler + fitted MPC | G, H ≥ 10 % (paired CI); screening; R5-M rules; R6 | G 15.4 %; H 20.4 % @ 1,600; R5-M/R5-M2 no claim; **R6: −4.3 % vs evsched, −2.5 % vs MPC-F** | **CLAIM YES (R6)**, scope: 4-kind mix, q 1,600 | 10-03 |
| T1-M2 (Lead 1) | BN4 + varied severity/duration | Does a memory policy add value when event severity varies? | Stage S (G, H_pre), stage H | G 12.2 %; H vs `mpcf_old` 3.3 % (CI incl. 0); R6 policy OOD +2.8 %, surge +16 % | Killed (conservative); R6 scope narrowed | 10-03 |
| T2 Lead 2 (ZM3) | zipper on-ramp merge | Can a zipper merge pass the realism gate? | realism gate | H5 drop 0.967 PASS, discharge 1,528 FAIL | FAIL (near miss) | 10-03 |
| T4 (CORR2) | 9.5 km corridor, 2 metered ramps + off-ramp | Coordinated metering via off-ramp spillback | calibration (≥ 5 blocking min); G ≥ 10 % | G = 0.4 %, NC best | Killed | 10-03 |

---

## 6. Design-space coverage (for the heatmap)

### 6.1 Plant × actuator/structure → outcome

| Plant ↓ / structure → | Posted VSL, direct DRL | Posted VSL, hybrid/residual on classical | AV/CAV speed caps, direct DRL | CAV set-speed of validated car-following controller (hybrid) | Direct CAV acceleration | Ramp meter, classical | Ramp meter, DRL scheduling (hybrid) |
|---|---|---|---|---|---|---|---|
| 4→3 lane drop (v4/v5.0) | v4: DQN/QR-DQN/C51/Rainbow, no positive result; VSL doesn't bind | — | v5.0 sweep: VSL equal/worse | — | — | — | — |
| ramps_v1/v2 weave/merge (v5) | Box(5) posted sign within TQC (−335 vs −321) | — | **TQC/SAC Box(4)**: +23 % TTS vs NC; M60 dominates | — | — | — | — |
| BN4 zipper (10 %/25 % AV) | A-T0 FAIL (doesn't bind) | MTFC on BN4 = NC | PPO/TRPO/RecurrentPPO ≈ NC (10 %); 0/3 vs cap:18 (25 %) | — | — | **meter −45 % vs NC** (dominant) | G 4.1 % (inflow only) → killed; **with perturbations: R6 −4.3 % / −2.5 %** |
| RING22 | — | — | — | FS U set by PPO: FAIL; PI at 100 % v_e | PPO direct accel: collisions → shield → FAIL | — | — |
| MRG3 merge v1–v3 | not reached (T0/T1 FAIL) | Card A (MTFC set-point) not reached | — | CACC staircase: parked | — | — | — |
| LD3 lane drop (EIDM) | PPO P-H2 +10.5 % J vs tuned const | PPO residual on const:0.75 degraded; G ≤ 4 % | CAV arms: no authority | `cavpi` +119–180 % delay | — | — | — |
| ZM3 zipper merge | not reached (realism FAIL, near miss) | — | — | — | — | — | — |
| CORR2 corridor | — | — | — | — | — | ALINEA adds delay; G 0.4 % | not reached |

### 6.2 Axes actually explored

| Axis | Values tried | Best observed | Source |
|---|---|---|---|
| DRL family | DQN, QR-DQN, C51/Rainbow (v4); SAC, TQC (v5); PPO, TRPO, RecurrentPPO (lab). Planned but never run: MaskablePPO, SAC/TQC in lab, DQN/QR-DQN in lab, CrossQ, IQN, MADDPG | RecurrentPPO hybrid scheduler (R6) | AV0; CAT; `train_sb3.py:130–238`; ROAD §8; STA §11; RC §3.2 |
| Structure | direct replacement; hybrid scheduler over discrete settings; residual on tuned constant; hybrid set-point of FS | hybrid scheduler | lab files above |
| Reward | 9-term (v4); 5-term variance proxy (v5); R-OUT (outflow 20 s); R-TTS incl. queue; mean speed ± accel penalty (ring); J = delay + 40 s·stops | R-TTS (hybrid) | AV0 §1.4; PLAN ADR-006; r3_pilots_protocol; round4 Add. A |
| Observation | 77-d (3-frame stack, regime one-hot, anomaly flag); S-VIN lane-piece densities/speeds + outflow + previous action; obs-stack 4; LSTM | LSTM (P-M3b) | PLAN §6.1; t1_meter_gscan_protocol Add. B–C |
| Decision interval | 30 s (v5, lab meter, Round 3), 60 s (Round 4 VSL), 1 s / 2 s / 5 s (ring) | — | as above |
| Hidden condition | demand level; compliance mix; truck share; incident yes/no; perturbation kind (slow/block/surge); severity/duration | perturbation kind mix (G 15.4 %) | round4_gscan; t1_meter_gscan; t1_meter2_scan |
| Penetration | 50 %, 100 % CAV (v5); 10 %, 25 % AV (BN4); 10/25/50 % CACC (Round 3, planned) | — | CAT; round2; round3 |

### 6.3 Headroom values measured (G = static adaptivity headroom; H = vs best non-learning)

| Plant / condition family | G | H | Source |
|---|---|---|---|
| BN4 meter, inflow only | 4.1 % | — | round2_protocol §C |
| LD3 VSL: demand / compliance / trucks / incident | 2.2 / 0.8 / 4.0 / 2.5 & 1.4 % | same | round4_gscan.md |
| LD3 R2-H tuning data | 0.38 % | — | round4 protocol "outcome" |
| CORR2 ALINEA, demand mix | 0.4 % | — | t4_gscan.md |
| BN4 meter, single perturbation kind | 1.8–8.8 % | — | t1_meter_gscan.md |
| BN4 meter, 4-kind mix | 15.4 % (q 1,600) / 10.3 % (q 2,000) | 20.4 % / −3.3 % | t1_meter_gscan.md; t1_meter_h.md |
| BN4 meter, 21 severity/duration conditions | 12.2 % | 11.1 % (vs evsched2, level-picked) / **3.3 %** (vs mpcf_old, paired) | t1_meter2_h.md |
| v6 cross-reference (other domains) | ≈ −1 to +4 % (fleet −0.9…+1.7; perimeter 2.5–2.7; bus 1.3–4.0; ramp 0.9) | < 10 % in all | LL6 §7; SUP |

Pattern [INF]: headroom ≥ 10 % appeared only where the hidden condition was a *mixture of qualitatively different discrete events* (blockage in particular) on a plant with a strong, binding classical actuator (the meter). Continuous nuisance variation (demand, compliance, trucks) gave ≤ 4 %. Even then, a fitted-model MPC or a well-tuned event rule closed most of it, and DRL kept ≈ 4 % (R6).

---

## 7. Lessons recorded → transferable design rules

### A. Metric and reward gameability
1. **Screen every headline metric and every reward term** against five tests before use: constant-policy, degenerate-extremes (optimum must be interior), decoupling from the objective, tautology/structural zero, exposure normalisation. A metric that fails one is a secondary report at most (GAME §4).
2. **Reward = the objective**, not a proxy: door-to-door delay *including origin/insertion queues*, co-headlined with served throughput; never speed variance, smoothness or comfort as headline or reward (GAME §5; ROAD §0 rule 4; CLAUDE "Metrics"). v5's 4-of-5 variance terms made the agent congest the road (AUDIT Claim 5).
3. **In-network TTS is gameable by insertion blocking**; count the origin queue and reconcile accounting (TTS ≈ 220 veh·h vs ~150 arrivals was unresolved) (GAME §5; SCREEN §1 line 12).
4. **Structural zeros are not evidence** ("0 collisions" under Krauss; 0 severe decelerations) (AUDIT Claim 3; GAME §2).
5. **Never compare raw rewards across reward configurations**, and never treat reward gains as performance (PLAN §8.5.4; AUDIT Claim 6).
6. **Penalty terms can be traded against the objective** even in small pilots (ring P2: AV-acceleration penalty traded against mean speed) (r3_pilots_protocol Add. B).
7. For co-primary objectives, **fix the scalarisation weight from the classical frontier before any DRL** (w = 40 s per stop) (round4 protocol Add. A).

### B. Plant realism and mechanism
8. **Show empirically that no-control breaks down in a controllable band** (some seeds, not all) before any controller work; never infer it from cited demand ranges (ADR-013 was wrong: NC never fell below 83 km/h) (GAME §5; AUDIT T3).
9. **Run a pre-registered realism gate**: capacity drop ratio in [0.82, 0.97], wave speed −10…−25 km/h, no teleports/FAILs and plausible discharge (≥ 1,600 veh/h/lane), congestion originating at the bottleneck (≥ 80 %) (t2_realism_protocol "Criteria").
10. **Known SUMO limits** (as measured here): waves realistic for IDM/EIDM/W99; an artefact-free capacity drop at an acceleration-lane merge was never achieved; IDM strands ramp/lane-drop vehicles; W99 shows no drop; `lcAssertive` creates "waves from nowhere"; zipper nodes give a drop (BN4 0.86; ZM3-EIDM 0.967) but ZM3 discharge was low (STATUS "Plant-realism gate"; t2_realism_zm.md).
11. **Check that the demand generator delivers nominal demand** (v5 eval was capped at 3,600 veh/h by one Bernoulli draw per second per route) and that insertion works (`departSpeed="max"` with IDM → 1,955-vehicle origin queue; use `"avg"`) (SCREEN §1 line 10; round2_protocol D-1).
12. **Test actuator authority (T0) first**: posted VSL on a lane-drop over-fed by 4 lanes does not bind; sparse AV caps do not bind reactively; posted VSL at MRG3 moved outflow only −3.9 % (t1_bn4_plant_checks; round2_a_t0; t2_mrg3_r1).
13. **Step length is part of the plant**: SUMO ACC/CACC brake at 9 m/s² at 0.5 s; the human plant itself changes with the step; re-run realism after changing it (round3_tm21_protocol Add. A).
14. **Guard against silent SUMO behaviour**: unknown vType attributes are accepted silently (behavioural R-0 check); vType rename `av@<id>` silently disabled the actuator; use `getLastInterval*` sensors (STATUS artefacts 5, 10; CLAUDE "Tool checks").
15. **Perturbations must not create teleport artefacts** (360 s blockage teleported in 209/220 runs; sudden lane closure caused artefact collisions → use a normally braking stopped vehicle) (STATUS 18; round4 protocol Add. E).
16. **Measure action→effect lag and set γ / decision interval / memory from it** (ring: credit horizon ≈ 20 s vs wave cost 30–60 s; v4: 150 s window = transit time broke credit assignment) (r3_pilots_protocol Add. E; AV0 §1.2).
17. **Direct acceleration control needs a safety shield** (ring P3: 55 collision episodes in 13 updates) (r3_pilots_protocol Add. B).

### C. Baselines
18. **The yardstick is the best tuned constant and the tuned validated controller, never NC alone** ("Beats NC ≠ is useful") (GAME §1, §5; ROAD §9 C2, C5).
19. **Tune every baseline on separate seeds with logged grids; report tuning and DRL budgets** (ROAD §0 rule 3). Literature-parameter controllers were often worse than NC (MRG3 MTFC +5 to +87 %; SPECIALIST on LD3) (t2_mrg3_r1; round4_r2).
20. **"Best non-learning" = tuned validated controller + non-learning adaptive scheduler + MPC with a model fitted on separate seeds (never the true model)** (CLAUDE "Method"; LL6 §5).
21. **Pick the best non-learning arm by the paired convention (minimum paired H over arms), not by median level** — the level rule picked an arm paired-worse than 4 of 5 rivals (STATUS 19; t1_meter2_h.md).
22. **Equal actuators and information for both arms**; asymmetric comparisons (B4) inflate RL gains in ≈ 19 of 39 papers (RC §1.3 item 2; T1 R5 same-actuator rule).
23. **The DRL action space must contain the tuned classical setting** (P-H grid lacked b = 0.75) (STATUS 17; round4 protocol Add. B–C).
24. **An infrastructure actuator can dominate any vehicle-level actuator** (BN4 meter −45 % vs NC; AV caps ≈ NC) — compare across actuators for context (t1_bn4_r2_baselines; r5_f1_final).

### D. Headroom gating
25. **Compute G before building DRL** (pooled-best vs per-condition-best classical setting on the same seeds; biased up, so G < 10 % is a conservative KILL) (CLAUDE "T2"; four kills: 4.1 %, ≤ 4 %, 0.4 %, Lead 1 H 3.3 %).
26. **Then H against best non-learning with a paired CI**; GO only if ≥ 10 % with CI > 0 (CLAUDE; LL6 §4).
27. **Expect DRL to capture a fraction of H**: with H = 20.4 %, the confirmed DRL gain was 2.5–4.3 % and stayed 5.8 % behind the oracle (t1_meter_h; t1_meter_r6). LL6 §2 prior: "realistically captures about half".
28. **Look for hidden conditions that move the best setting a lot** (discrete, qualitatively different events); continuous nuisance variation gave G ≤ 4 % (§6.3 here; round4_gscan; t1_meter_gscan).

### E. Statistics and protocol
29. **Pre-register before data; add an addendum before every new run; after a bug, fix, re-run everything affected, log both outcomes** (CLAUDE "Method"; STATUS artefact list of 19).
30. **Paired seeds, median of paired differences, 95 % percentile bootstrap (10,000)** — one convention everywhere (CLAUDE; t1_bn4_r5_protocol).
31. **Seed roles never mix**; reserved confirmatory seeds used once (R5-M2 breached 90 reserved seeds; disclosed) (ROAD §0 rule 2, §10; t1_meter_gscan_protocol "R5-M2 … breach").
32. **Single-seed screening passes are usually false positives** (P1c, B-P6): require ≥ 3 learner seeds, pooled + ≥ 2/3 seeds rule, test seeds (r3_pilots "F1 … conclusion"; r5_bf_av25 "Reading").
33. **Size screens for power** (10 seeds gave CI ±40 s against a 10 s target) and **count looks** (P-M3: 1 pass in 8 looks) (t1_meter_gscan_protocol Add. B–D).
34. **State scope and test transfer**: R6 policy lost 16 % on surges outside its training range (t1_meter2_h "Exploratory follow-up").
35. **Health-stop rules need a meaningful sample** (P-M stopped at update 2 on 1/96 FAIL; P-M4 seed 4 on 4/64) (t1_meter_gscan_protocol Add. B, E).
36. **Report every variant, including losers ("selected from N variants")** via a ledger (ROAD §0 rule 1; t1_meter_r6 caveat 3).

### F. Training budget and algorithm choice
37. **≥ 500 PPO updates per run, 3–5 learner seeds, convergence check, final policy or validation-selected checkpoint only** (CLAUDE "DRL budget"; LL6 §5). v5 selected `best_model` on the training pool and never checked convergence (SCREEN §1 line 13, §2 (e)).
38. **Distinguish authority from optimisation failure explicitly** (F2: 4× batch + lr decay stabilised learning but stayed ≈ NC → authority) (r3_pilots_protocol Add. D–E).
39. **Centre continuous action maps on "no control" and shrink initial exploration noise** when random actions are harmful (P1 → P1c `nocap_center`, log_std −0.5) (r3_pilots_protocol Add. A, C).
40. **Use memory (LSTM) when the hidden condition must be inferred from history**: RecurrentPPO passed where PPO and a 4-frame stack failed (P-M3) (t1_meter_pm.md; Add. D).
41. **Select checkpoints on enough validation episodes** (12 → 40 episodes fixed unreliable selection between R5-M and R5-M2) (t1_meter_gscan_protocol Add. E).
42. **Toolchain**: libsumo, one sim per process, unique file names (with PID), `torch.set_num_threads(1)` (default threads 7–50× slower), worker count by CPU load (CLAUDE "Toolchain").

### G. Framing and literature
43. **Mark unread literature [VERIFY]; never insert "first"** (the v5 plan inserted "first" into Vinitsky and MARVEL quotes and called per-lane Vinitsky "uniform-per-segment") (AUDIT Claim 10).
44. **Scope discipline must not exclude the falsifying metric** (plan §8.4 excluded TTS/travel time) (AUDIT Claim 9).
45. **Published DRL-VSL gains mostly come from untuned or asymmetric comparators**; tuned comparators give ≈ 0–2 % (RC §0, §1.4).
46. [INF] **Making a problem "need learning" by adding stochasticity is not headroom.** v5 reacted to "M110 is trivially optimal" by adding stochastic demand, anomalies and per-lane actions (AV1 §1.3–1.4) instead of testing whether any controller could beat the best constant; the headroom gate is the corrective.

---

## 8. Open questions the documents list as untested

| # | Question | Status in docs | Source |
|---|---|---|---|
| 1 | Probe A (is wave amplification heavy-tailed?) and Probe B (does ACC set-point modulation have damping authority?) | defined, never run | FEAS §5; SCREEN §1 line 15 |
| 2 | "Does wave damping need a distributional critic, or does plain SAC suffice?" | untested | FEAS §3 |
| 3 | TQC vs SAC at 100 % CAV; overestimation reduction | unmeasured | AUDIT Claim 7 |
| 4 | Anomaly robustness with ≥ 30 episodes per type, all 3 types | not run (judged off the critical path) | AUDIT T1 caveats |
| 5 | v5 code hygiene: `_current_speed_limits_ms` not cleared on reset; `ramp_spike` with undefined vType; `train_freq` / update count | [INF] in source, not re-run | SCREEN §2 (e), (f5) |
| 6 | TTS vs `n_arrived` accounting mismatch in v5 eval | "resolve before TTS becomes a reward" | GAME §5 |
| 7 | D-check: can breakdown be predicted ahead from any sensing level? | MRG3 v1 had no breakdowns (`precursors_informative` False); v3 D-check did not run | ROAD §2, §7; round2_protocol "D-2 result" |
| 8 | Round 3 T-CAV0, T-X; whether CACC falls back to ACC behind non-CACC leaders; how much of the CACC delay penalty is a SUMO artefact | not run / "[VERIFY in the SUMO source]" / "not tested here" | round3_tm21_protocol; round4 protocol "CAV-model note" |
| 9 | Track 3 OPEN corridor (CIRCLES-style replayed leaders); Track 4 COR10 moving-jam SPECIALIST domain | no results doc found | ROAD §6 |
| 10 | Cards A–C (MTFC set-point scheduler, SPECIALIST activation, MPC model correction) on a merge with a capacity drop; AD-ALINEA-style adaptive comparator; Hegyi MPC | blocked by the realism gate; not built | SCREEN §6–7 |
| 11 | ZM3: a new pre-registered variant to fix the low discharge (1,528 veh/h/lane) | author's decision | t2_zipmerge_protocol "Result" |
| 12 | Why the refitted MPC-F2 (better R² 0.94) controls worse than `mpcf_old` ("meter off" in its action set?) | "plausible cause, but not tested" | t1_meter2_h.md notes |
| 13 | R6 beyond its scope: q = 2,000, other plants, other event mixes | no claim; no OOD test proposed | t1_meter_r6 caveat 5; t1_meter2_h |
| 14 | P-H3 best-validation checkpoint; test-seed confirmation of `const:0.75` (`round4_r5refs`) | kept, not screened / pre-computed, no results doc found | round4 protocol outcome |
| 15 | Reproductions of Han 2024 (#34, SUMO, 10–15 days) and Vatani Nezafat 2019 (#39 lane drop, 8–12 days) against tuned, equally actuated comparators | proposed; author prior: neither clears 10 % | RC §3.1–3.2; SUP decision (c) |
| 16 | Supervisor decisions: reframing, one vs two papers, reproduction first, naming papers in an audit | pending | SUP "Decisions" |
| 17 | Realism gate scope: lane-change realism and trajectory-level calibration | explicitly not tested | t2_realism_protocol "What this gate does not test" |
| 18 | Unread key controller sources (Müller 2015 MTFC microsim; Carlson 2011; Hegyi & Hoogendoorn 2010 field test; Smaragdis 2004 AD-ALINEA) | [NOT READ] | SCREEN §3.4 item 8, §10 |
| 19 | Planned v5 extensions: IQN, MPR sweep 25–100 %, multi-topology, MARL "one TQC per gantry" | never started | STA §11; PLAN ADR-009, §3 |
| 20 | v5 convergence: 100 % CAV learning curves "still moving" at 1 M steps | not followed up (moot per SCREEN) | SCREEN §2 (e) |

---

## 9. Inventory of the other folders

**`/srv/shared/Workspace/phd/drl_algos/`** (2 cloned third-party repos, 63 `.py` files):
- `sac/` — `haarnoja/sac` (TensorFlow, MuJoCo/rllab era; README says "no longer maintained", points to Softlearning); includes DIAYN; last commit 2018-12-21.
- `tqc_pytorch/` — `alxlampe/tqc_pytorch`, PyTorch port of TQC built on the TD3 code base; gym 0.12.5, mujoco-py 1.50, PyTorch 1.3; last commit 2020-05-12.
- Neither is referenced anywhere in the v5 repo or `docs_local` (grep). v5 used SB3 `SAC` and sb3-contrib `TQC` (PLAN §6.2; STA §9.3); the lab trainer implements only PPO, RecurrentPPO and TRPO (`vsl_lab/train/train_sb3.py:221–238`). These clones look like reference reading, not used code [INF].

**`docs_local/`**: v5.0/v5.1 research plans (AV0, AV1), algorithm/objective rationale with the ramps_v1 fixed-VSL sweep (STA), `slowDown` rationale (SDA), control loop (CL), VSL placement (VPA), thesis-style baseline chapter (TBC), VM deployment guide, and `llm_prompts/` (a v4 analysis prompt for comparing C51/QR-DQN/DQN runs, and a v4 RBC51DQN train/eval log ending in "Go (authority exists): False"). All pre-date the May audit; their claims are superseded by AUDIT/GAME/SCREEN.

**`docs/knowledge_base/`** (PDFs not read): `framework/` (10: TQC paper, Gymnasium, Sutton & Barto, 3 SAC papers + Spinning Up page, SAC-AP, SB3 paper, `SUMO/` E1 and E3 doc pages); `papers_DistRL/` (12: C51, QR-DQN, Rainbow, NoisyNet, dual expectile-quantile, Expected-Sarsa C51, categorical analysis, a 1998 POMDP short-term-memory paper, Sutton & Barto, Lorenz & Elefteriadou capacity/breakdown, Chung et al. 2007 capacity drop, a C51 notebook); `papers_RL-DRL_CFM/` (9: 7 car-following papers incl. SECRM, plus 2 non-paper files); `papers_RL_RM/` (41 ramp-metering / integrated control files, incl. SPECIALIST and its field evaluation, Hegyi MPC); `papers_RL_VSL/` (43).

**`reports/`**: `2026-05-19_ablation/` (4 KPI reports + cross-comparison + 2 CSVs) and `2026-05-20_full_matrix/` (9 KPI reports + cross-comparison + 2 CSVs). They report reward-yardstick and physical KPIs (`lane_sigma`, `ds_flow`, 0 collisions / 4,320 episodes). The audit re-derived its non-gameable numbers from the same raw CSVs; the reports' framing is superseded.

---

## 10. Discrepancies and side findings worth knowing

1. **Capacity drop on ramps_v1**: NC18 (2026-03-18) called 7,000 veh/h "the classic capacity drop phenomenon"; SCREEN recomputed −0.4 % from the same NC CSV. Treat ramps_v1 as having congestion but no measurable drop (NC18 §2; SCREEN §1 line 11).
2. **TQC critic count** changed across documents: 2 critics (STA §9.3) → 5 critics × 25 quantiles, drop top-2 (AV1 §5.3; PLAN ADR-003).
3. **TQC citation**: STA §12 cites Kuznetsov et al. 2020 as "JMLR 21(167)". [VERIFY: my recollection is that TQC appeared at ICML 2020 (PMLR); I have not checked.]
4. **Possible protocol/implementation mismatch in the R6 candidate's training** [INF, code reading only, not verified against run logs]: the P-M3b/P-M4 protocols state "learning rate 3e-4 with decay", but in `train_sb3.py` the decay schedule `lr` is passed only to PPO; RecurrentPPO receives the constant `a.lr` (lines 213–231). If so, the candidate was trained with a constant learning rate. This would not invalidate R6 (the frozen file was evaluated as is), but the protocol text would be inaccurate. Check the run's command line before citing the training setup.
5. **T1-M H is a paired-only effect**: marginal medians were evsched 225.3 s vs lookup 227.5 s; the 20.4 % H comes from the paired median with a heavy seed tail (t1_meter_h.md per-kind check). The same level-vs-paired issue later reversed Lead 1's verdict.
6. **The roadmap's thermal cap** (< 90 °C) was replaced by the author's 99 °C 5-min-median guard and CPU-load scheduling (ROAD §5 vs CLAUDE "Limits"; STATUS "Compute").
7. **Pointers outside scope** (not read): v6 has newer reports per its git log ("Why v5 failed (human)", which names an "open within-run timing question", and "Where DRL beats tuned control in ARC-IT 9.4"). VSL is excluded in v6.

---

## Appendix A. `docs/lab/*.md` index (46 files)

| Track | Protocols | Results |
|---|---|---|
| Living status | — | STATUS.md |
| T1 BN4 | t1_bn4_plant_checks_protocol, t1_bn4_r2_baselines_protocol, t1_bn4_r5_protocol, r3_pilots_protocol | t1_bn4_plant_checks, t1_bn4_r2_baselines, r3_pilots, r5_f1_final, r5_f1_bestval, r5_f2_final |
| Round 2 (A posted VSL BN4, B 25 % AV, C meter gate, D merge repair) | round2_protocol | round2_a_t0, round2_a_r2, round2_b_r2, r5_bf_av25 |
| T3 ring | t3_ring_r1_r2_protocol | t3_ring_r1_r2 (pilots in r3_pilots) |
| T2 merge + realism | t2_mrg3_r1_protocol, t2_mrg3_r2_protocol, t2_realism_protocol, t2_zipmerge_protocol | t2_mrg3_r1, t2_realism_step0.2, t2_realism_d3, t2_realism_ld3, t2_realism_zm |
| Round 3 TM21 | round3_tm21_protocol | (outcome inside round4_th) |
| Round 4 LD3 harmonisation | round4_harmonisation_protocol | round4_th, round4_r2, round4_pilots, round4_gscan |
| T1-M meter scheduling | t1_meter_gscan_protocol (Add. A–F) | t1_meter_gscan, t1_meter_h, t1_meter_pm, t1_meter_r5, r5m2, r5m2_final, t1_meter_r6 |
| T1-M2 Lead 1 | t1_meter2_protocol | t1_meter2_scan, t1_meter2_h |
| T4 corridor | t4_corr2_protocol | t4_gscan |

## Appendix B. Literature red-flag codes (RF "Flag codes")

B1 NC/other-RL only · B2 comparator params copied/hand-set/unstated · B3 comparator tuned on test scenarios · B4 asymmetric actuators/information · E1 train = test · E2 selection on test results · S1 single/representative/best run · S2 replications unstated · S3 no dispersion/test · M1 origin/insertion queues excluded, throughput unreported · M2 proxy headline or hidden trade-off · P1 macroscopic capacity drop as an equation parameter · P2 micro: drop not demonstrated / no calibration / teleports unreported · N1 numerical inconsistency · R1 reproducibility gaps · C1 claims exceed evidence.
