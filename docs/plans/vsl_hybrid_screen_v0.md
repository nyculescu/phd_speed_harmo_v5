# VSL hybrid spin-off, Step 1: desk audit and screen (v0)

*2026-10-01 · branch `claude/vsl-hybrid-v1` · desk work only, no simulation run · **STOP: the author chooses a card (§9)***

**Scope** (author decision, 2026-10-01; see `CLAUDE.md`):
- a validated, published VSL controller stays in the loop;
- DRL may only add value on top of it;
- DRL does not replace the controller.

**Read in full:**
- v5:
  - `README.md`
  - `docs/lessons_metric_gameability.md`
  - `docs/audit_2026-05-20_fresh_thread.md`
  - `docs/feasibility_study_2026-05-20_harmonization_layer.md`
  - `docs/experiment_catalog.md`
  - `reports/2026-05-20_full_matrix/cross_experiment_comparison.md`
  - `tests/persistent_results/summary_elaborated_18-03-2026_14-08-30.md`
- v6 (read only):
  - `docs/handoff/lessons_learned.md`
  - `docs/feasibility/gate0_perimeter.md`
  - `docs/plans/phase7_novelty_check.md`
  - `feasibility/results/bench/parallel_sweet_spot_20261001.md`

The prompt files (`docs/fresh_thread_audit_prompt.md`, `artifacts/prompts/`) are instructions, not results. They are not used as evidence.

**How this screen was produced (disclosure):**
- **Code facts** come from a read-only audit of the v5 code, with file:line evidence. I re-checked every load-bearing fact myself; those are marked ✓.
- **[CALC]** marks numbers recomputed from files in the repo (Python only, no SUMO). **[INF]** marks an inference that was not checked by running anything.
- **Literature:**
  - The local `docs/knowledge_base/` PDFs were converted to text (`pdftotext`) and read paper by paper.
  - There were 12 web searches in total: 8 for missing hybrids and 4 for controllers.
  - Read status is given per item; anything not read in full is marked [VERIFY].
- **ARC-IT:** taken from the local mirror at v6 `docs/arcitwebsite-20260715/`, read only. I checked seven quotes verbatim.

---

## 1. v5 in 15 lines

1. **Goal:** per-lane speed harmonisation at an on-ramp merge (`ramps_v2`: 3 lanes, 250 m acceleration lane, 4→3 drop; no off-ramp, despite `README.md:6-7`).
2. **Control:** TQC/SAC set per-lane **CAV** speeds directly via `traci.vehicle.slowDown` every 30 s; human drivers were never actuated in Box(4) (`core/env_interact.py:582-648`).
3. **Training:** 15 experiments × 5 seeds × 1 M steps on 48 socket-TraCI workers, 494–825 min per seed (`docs/experiment_catalog.md`; seed logs).
4. **Reward:** 4 of 5 terms are speed-variance proxies, with no delay or TTS term (`sar_components/rewards/r44_reward_v4.py:110-152`; audit, Claim 5).
5. **Baselines:** NC, constant caps M60–M110 and two differential rules; no SPECIALIST, MTFC, ALINEA or MPC (`evaluate_models.py:154-218`).
6. **Result (100 % CAV) vs NC:** `lane_sigma` −91 %, but TTS **+23 %**, mean travel time **+23 %**, sampled trips −5.9 % (audit §2, T3).
7. A constant 60 km/h cap **Pareto-dominated** the DRL policy on smoothing, safety proxies and mobility (`docs/lessons_metric_gameability.md` §2).
8. Nine reward configurations moved real KPIs by ≤ 2 %, and all nine were about 23 % worse than NC (audit, Claim 8).
9. **No breakdown in evaluation:** under NC the merge ran at 83–86 km/h, with 1.3 % of windows congested (audit, lines 100–112).
10. **New:** evaluation demand used one Bernoulli draw per second per route, capping the mainline at 3,600 veh/h; training used 5,500–7,250 veh/h (`tests/_sumo_helpers.py:120-131` ✓).
11. **New:** the only capacity-drop data (`ramps_v1`, March 2026) show NC discharge of 6,733 vs 6,760 veh/h before breakdown, i.e. **−0.4 %** [CALC ✓, `tests/persistent_results/…/nocontrol_7000vph.csv`].
12. **New:** KPIs leave out insertion queues, and arrivals were polled once per 30 s, i.e. about 1/30 sampled (`core/eval_metrics.py:265` ✓, `evaluate_models.py:266` ✓).
13. **New:** `best_model` was chosen on the *training* pool and is the one evaluated; convergence was never checked (`train.py:257-282` ✓, `evaluate_models.py:114-117` ✓).
14. **Why it stalled:** no controllable bottleneck, a gameable reward and KPI, NC as the yardstick, and DRL replacing the controller. The policy congested a free-flowing road and was paid for it.
15. **May 2026 pivot** (an ACC set-point layer for CAVs): its probes A and B are defined, but no probe results are in the repo (`docs/feasibility_study_2026-05-20_harmonization_layer.md` §5).

## 2. Diagnosis: why v5 stalled

| Cause | Verdict | Evidence |
|---|---|---|
| **(a) No headroom** | **Yes; root cause, together with (b)** | There was nothing to fix. NC never broke down in evaluation (audit lines 100–112; line 10 above). The best non-learning policy beat NC by only 2.6 % on in-network TTS: [CALC, code audit] `diff_aggressive_active` 214.2 vs NC 220.0 veh·h in `training_runs/experiment_20260518_133246/evaluation_20260521_095745`. No headroom gate was ever run. |
| **(b) No capacity drop, so no mechanism, in SUMO** | **Yes; root cause** | Never measured on `ramps_v2` with the v5 fleet. The only data (`ramps_v1`) show −0.4 % ✓. `tests/test_capacity_drop.py` has no results; it defines the "drop" as the flow difference between adjacent demand levels (l.410-426) and counts only lanes 0–2 of the 4-lane zone (l.231-236). The evaluation demand cap (line 10) made breakdown unlikely anyway. |
| **(c) Wrong yardstick, or metric gaming** | **Yes** | `lane_sigma` falls steadily as the posted speed falls (audit T2). Four reward terms are speed-variance proxies (Claim 5). The plan excluded TTS, total exposure time (TET) and total integrated time (TIT) from the KPIs (`docs/plans/phd_thesis_plan_v0.md:618`; audit, Claim 9). NC was the yardstick. Arrivals were sampled at 1/30 (line 12). Insertion backlog was ignored (`lessons_metric_gameability.md` §5). |
| **(d) DRL replacing the controller, without structure** | **Yes; it hid (a) and (b)** | DRL controlled each vehicle directly with a continuous per-lane action. No validated controller was in the loop or among the baselines; the plan deferred MTFC, ALINEA and MPC to "Paper 3" (plan l.91, 141-142, 777). The "SPECIALIST-style" baselines are not SPECIALIST: they post a fixed limit while a metastable flag is on, with no jam detection and no front construction (`evaluate_models.py:175-219`, 405-416). A tuned validated controller as a baseline would have shown at once that there was nothing to fix. |
| **(e) Training budget or convergence** | **Partly; secondary** | 1 M steps × 5 seeds. With SB3 defaults that is about 20.8 k gradient updates per run [INF; verify `train_freq`]. The 50 %-CAV learning curves are flat; the 100 %-CAV curves are still moving ([CALC] from `eval_logs/evaluations.npz`). Checkpoints were selected on the training pool. But (a)–(c) make (e) moot: all 9 reward configurations land within ~2 % on real KPIs, so more training would only have optimised the wrong objective harder. |
| **(f) Other** | **Yes** | See the list below the table. |

**(f) details:**
- **(f1) Train/evaluation demand mismatch** (line 10). This contradicts plan l.579 and l.626.
- **(f2) Compliance:**
  - 100 % CAV direct control is fleet speed control, not VSL (audit, Claim 4).
  - Compliance with the speed limit is binary: CAVs 100 %, HDVs 0 % (`env_interact.py:540, 582-587`).
  - The v4 three-group compliance model is **dead code**. `traffic_environment/rou_writer.py:112-140` needs a missing `network_config_4_3.yaml`.
  - No v5 data treat compliance as a hidden condition.
- **(f3) Toolchain:** socket TraCI cost ~9.5 h per 1 M-step run on an EPYC (`README.md:150`). The v5 `.venv` in this (exFAT) mirror has no `python` executable, because exFAT drops symlinks.
- **(f4) Literature:** over-claims and misquotes (audit, Claim 10).
- **(f5) Hygiene:**
  - [INF] `_current_speed_limits_ms` is not cleared on reset, so the previous episode's last action drives the first window of the next one (`env_interact.py:203-245, 502`).
  - [INF] The `ramp_spike` anomaly adds vehicles with an undefined vType, so it probably injects nothing (`traffic_environment/anomaly_injector.py:195-205`).
  - No `speed_reduction` anomaly was observed in evaluation (audit T1).

**Ranking:**
- (a) and (b) come first: there was no controllable breakdown.
- (c) let that go unnoticed.
- (d) removed the structure that would have exposed it.
- (e) is secondary.

**So for the spin-off:**
- No v5 *result* carries over as evidence.
- **Reusable:**
  - the `ramps_v2` geometry, as a starting point that must be re-validated for capacity drop;
  - the detector layout;
  - the metric lessons.
- **Not reusable without a rewrite:**
  - the evaluation metrics: arrival sampling, no insertion backlog;
  - the on-the-fly demand generator (capped);
  - the socket-TraCI environment;
  - the binary compliance model.

## 3. Literature recount

### 3.1 Count and method

**Count.** I count **42 distinct RL/DRL VSL papers**:
- **39 read from the local full texts** in `docs/knowledge_base/` (53 text files, 44 relevant). Of these, 34 were read in full (some with image-only tables, marked †), 2 nearly in full, and 3 in part (#2, #15, #39);
- **3 found only on the web** (abstract or snippet).

That supports your "more than 40". **Counting rule:** RL or DRL sets freeway speed limits or speed recommendations, including joint VSL + ramp metering (RM) and CAV-actuated per-lane limits.

**Not counted:**
- 2 non-RL references and 1 neuroevolution paper (§3.3);
- 1 review;
- 3 files that are not VSL: Gu 2023 (ramp metering), Belletti 2018 (ramp metering), Kheterpal 2018 (Flow framework);
- 1 duplicate (an ICAUS 2024 book chapter that is the same paper as a standalone file);
- the controller and capacity-drop papers listed in §4.

**Method:**
- Six reader agents plus two of my own sub-reads went through the full texts.
- Tables that exist only as images were read from the rendered PDF pages (marked †).
- "c." means I computed the number from printed values; the authors do not report it.
- Numbers marked ✓ I re-checked against the text myself.

| Structure | Papers |
|---|---|
| Direct | 29 |
| Direct, joint with RM | 6 |
| Direct, switched on by a fixed rule ("rule-gated") | 4 |
| Direct with a SPECIALIST fallback | 1 |
| **Hybrid** (classical controller in the loop) | **2** |

**Simulator** (of the 39 read): 9 macro (METANET, CTM, LDNL) and 30 micro (19 SUMO, 5 VISSIM, 2 AnyLogic, 2 TransModeler, 1 MOTUS, 1 custom).

**Strongest classical baseline** (of the 39 read from full text):

| Strongest baseline | Papers |
|---|---|
| No control (NC), or other RL only | 14 |
| Fixed VSL only | 2 |
| Other rule-based VSL | 8 |
| MTFC / PI-type feedback VSL | 10 |
| ALINEA only | 2 |
| SPECIALIST (+ MPC) | 1 |
| MPC | 2 |

**Baseline tuning:** no paper tunes its baselines on scenarios kept separate from the test scenarios. Most train and test on the same scenarios, and few report seeds or CIs.

### 3.2 Paper table

Gains are against the **strongest non-trivial baseline**; negative means RL is better on a cost.

**Macroscopic**

| # | Paper | Structure | Simulator · network | Strongest baseline [tuned?] | Gain vs strongest | Read · red flags |
|---|---|---|---|---|---|---|
| 1 | Walraven et al. 2016, EAAI 52:203–212 | direct (QL) | METANET, 24 km | best fixed assignment (oracle search) | **RL loses:** +0.4…+2.6 % veh·h (c.) | full · train = test |
| 2 | Zhu & Ukkusuri 2014, TR-C 41 | direct | LDNL, Sioux Falls | NC only | −18 % TTT vs NC (during learning) | partial · no separate test |
| 3 | Li Z. et al. 2017, IEEE T-ITS 18(11) | direct (QL) | CTM, I-880 | Carlson FB VSL ["calibrated to optimize"; method not stated] | −32.5 % / −12.2 % TTT (c.) | full · replications not stated |
| 4 | Li Z. et al. 2021, IEEE ITS Mag. | direct (QL) | stochastic CTM, I-880 | GA-optimised rule VSL [**tuned**] | **RL loses** on crash risk (TCR 867.6 vs 825.2) | full |
| 5 | Han Y., Hegyi et al. 2022, TR-C 144:103900 | direct (tabular Q); SPECIALIST for unseen states | METANET + extended CTM, 7.5 km, jam waves | SPECIALIST ["trial-and-error"]; MPC on a mismatched CTM | Delay vs NC: RL −35.1 %, MPC −25.9 %, SPECIALIST −15.5 % ✓. So RL is −12.4 % vs MPC (c.) and −23 % vs SPECIALIST (c.). The 35.1 % holds only once ≥ 80 % of states had appeared in training data ✓. | full · no CI |
| 6 | Zheng S. et al. 2023, J. Adv. Transp. | direct (MADDPG) | CTM with a 7.6 % capacity drop | Carlson 2011 FB [params not re-tuned] | −10.9 % / −11.7 % TTS (c.) | full |
| 7 | Ke Z. et al. 2021, IEEE T-ITS 22(7) | direct (DDQN, transfer learning) | CTM, 8.4 % drop, I-880 | NC only | claims "50.47 %"; the printed values give 20.4 % | full · inconsistent numbers |
| 8 | Tabadkani Aval 2019, ICCKE | direct + RM | CTM, M62 | NC only | figures only | full |
| 9 | **Sun, Jamshidnejad & De Schutter 2024**, IEEE T-ITS 25(7):6756–6769 | **hybrid: DRL residual on MPC**; RM + VSL | METANET (Hegyi benchmark), mismatched model | MPC, high-frequency MPC, parameterised MPC [weights fixed] | −0.9…−4.5 % TTS vs the same MPC; **0.5–4.9 % worse than the best MPC variant in all 6 scenarios** (c., Table V†) | full† · 10 replications, means only |

**Microscopic**

| # | Paper | Structure | Simulator · network | Strongest baseline [tuned?] | Gain vs strongest | Read · red flags |
|---|---|---|---|---|---|---|
| 10 | Vinitsky et al. 2018, ITSC | direct, via AVs (per-lane VSL) | SUMO/Flow, 4→2→1 lanes | FB ramp metering ["tuned empirically"] | **≈ 0:** "matches" FB above the critical inflow and "under-performs" below it ✓ | full · capacity drop exhibited |
| 11 | Schmidt-Dumont & van Vuuren 2019, J. SAICE 61(3) | direct + RM (hierarchical MARL) | AnyLogic, N1 Cape Town (calibrated) | ALINEA, PI-ALINEA, **MTFC**, Carlson-2014 integrated FB [**tuned**, on the same scenario] | **VSL-only RL vs tuned MTFC: 6.45 % vs 4.91 % TTS reduction, ≈ 1.6 % relative.** Hierarchical MARL vs integrated FB: 12.70 % vs 3.36 %, ≈ 9.7 % relative (c. ✓) | full · train = test |
| 12 | Schmidt-Dumont & van Vuuren, "2015" [venue VERIFY: header looks like a template] | direct + RM | AnyLogic, Hegyi benchmark | ALINEA [params not stated] | −2.9…−9.9 % (c.) | full · train = test |
| 13 | Wang C. et al. 2019, IEEE Access 7 | direct (MARL) | MOTUS, A16 Drechttunnel | NC only | −29.9 % TTT vs NC | full · train = test |
| 14 | Kušić et al. 2020 (WL-VSL), ITSC [VERIFY] | direct (W-learning) | SUMO, synthetic | NC, single-agent Q | local TTS −4.5 %; overall ≈ NC | full · single seed |
| 15 | Wu Y. et al. 2020, TR-C 117 | direct, per lane | SUMO, I-405 | NC, other RL | −2.9 % / −5.7 % ATT vs best RL (c.) | partial · fails at speedFactor 1.1 |
| 16 | Chai G. et al. 2021, ISCTT | direct + RM (MADDPG) | SUMO merge, all CACC | "feedback integrated" [identity and params not stated] | −21.5 % TTT | full · single run |
| 17 | Gregurić et al. 2020, ELMAR | direct (DQN) | VISSIM, 8 km | SPSC [not stated] | local speed +12.7 %, density −25 % (c.) | full · one "representative" run |
| 18 | Gregurić et al. 2022, EAAI 112:104850 | direct (DDPG) | VISSIM, 8 km | SPSC P-feedback [gain 4.5 taken from Wang 2011; **not tuned**] | bottleneck TTS −9.1 %; network −3.1 % / −3.3 % (c.) | full · "last 10 best" runs |
| 19 | **Cheng M. et al. 2022**, J. Adv. Transp. | **hybrid: parameter tuning** of the authors' own VSL law (λ re-chosen every 2 min) | VISSIM merge | same law with the best of 30 random λ [weak] | merge flow +7 % / +14 % | full · unvalidated law; single run |
| 20 | Vrbanić et al. 2022a, Sustainability 14:932 | direct (QL), CAV only | SUMO, 8 km | HCM rule VSL [not stated] | −0.2…−4.6 % TTS (c.) | full · hyperparameters picked on test |
| 21 | Vrbanić et al. 2022b, MED | direct (QL) | SUMO, 8 km | HCM rule VSL [not stated] | 0…−1.5 % TTS (c.) | full |
| 22 | Xiao et al. 2022, IET ITS 16 | rule-gated direct (QL) | VISSIM, Wuhan | queue-rule VSL [not stated] | −14.5 % TTT | full · single scenario |
| 23 | Wang C. et al. 2022, IEEE T-ITS 23(9) | direct, joint RM + VSL (DDPG, TD3) | SUMO, 2 networks | IFBC = PI-ALINEA + integral FB VSL [fixed gains; not stated how chosen] | ≈ −9.5 % TTT (c., Fig. 11); the text says "slightly outperformed" | full† · evaluated on training episodes |
| 24 | Lu W. et al. 2023, TR-C 153 | direct, lane-level (TD3) | SUMO, SR-91, 100 % CAV | other RL | −1.8 % TTS; −16.4 % vs NC | full · no classical baseline |
| 25 | Chen X. et al. 2023, ICCSSE | direct (TD3) | SUMO | NC only | speed +12.3 % | full |
| 26 | Hua & Fan 2023, IET ITS 17 | direct (DDPG) | SUMO, I-80 weave | NC only | mean travel time −4.5…−5.2 % | full |
| 27 | Zhang Yuhang et al. 2023, SMARTCOMP | direct (MAPPO) | TransModeler, I-24 | NC only | **delay +5.0 % / +6.5 % (worse)** | full |
| 28 | Zhang Y. et al. 2024 (MARVEL), IEEE Access 12 | direct (MAPPO) | TransModeler, I-24 | deployed Speed-Matching ["carefully searched"] | safety +63.4 %; "the No Control baseline has the minimum queue length" | full† · uncalibrated |
| 29 | Pelenczei et al. 2024, ICINCO | direct (MARL) | SUMO, lane closures | MCS; MTFC [params not stated; **MTFC worse than NC**] | −11.8 % / −6.3 % TT vs MCS | full · baselines untuned |
| 30 | Jin J. et al. 2024, Accid. Anal. Prev. 201 | rule-gated direct (Dyna-Q) | SUMO, tunnel | MCTM-MPC [GA; not stated whether tuned] | −1.9 % / −0.9 % time loss (c.) | near-full · 2 runs |
| 31 | Jin J. et al. 2025, ESWA 267 | rule-gated direct (D3QN) | SUMO, tunnel | fixed limit | no dominance | full |
| 32 | Kang K. et al. 2024, CACIE 39 | direct (DQN) | VISSIM, Seoul ring | NC only | density −53 % | near-full |
| 33 | Li D. & Lasenby 2024, IEEE T-ITS 25(2) | direct (I2A) | SUMO, M25 merge (calibrated) | other RL | ≈ −2.5 % TTS (c.); −11.9 % vs NC | full† · capacity drop exhibited |
| 34 | Han et al. 2024, TRR 2678(9) | direct (MADDPG) | SUMO, G15 Shenzhen | Carlson FB VSL [gains "0.0004, 10, and 38" set, no tuning ✓] | −21.34 % / −16.75 % vs FB; −12.88 % / −10.24 % vs DDPG ✓ | full · one limit for all lanes vs per-lane RL; no CI |
| 35 | Hua & Fan 2024, Physica A 634 | direct (DDPG) | SUMO, I-80 + incident | NC only | −2.4…−8.7 % ATT (c.) | full |
| 36 | Ko et al. 2020, IET ITS 14(8) | direct (DQN) + merge sequencing | SUMO, lane closure | FIFO, rule-based speed harmonisation [not stated] | throughput −10.9…+19.2 % vs FIFO, depending on CAV share (c.) | full · 1 training run |
| 37 | Yang et al. 2024, Sustainability 16:965 | rule-gated direct (I-DDPG) | SUMO, HZM bridge | rule VSL [not stated] | −2.5…−5.7 % ATT (c.) | full |
| 38 | Wang Yan / Yan W. 2025, LNEE 1379 (ICAUS 2024) | direct, via CAV moving bottlenecks | SUMO merge | other RL | "≈ 40 % higher" (ambiguous) | full |
| 39 | Vatani Nezafat 2019, PhD dissertation (ODU) | direct (A3C) | custom micro (IDM + LMRS) | ALINEA-like P-FB VSL [**grid-search tuned**] | remaining delay −21 % / −54 % / −7 % (c.) | partial · not peer-reviewed; no seeds or CI |

**Web only, not read**

| # | Paper | Structure | Setting | Strongest baseline | Gain | Read |
|---|---|---|---|---|---|---|
| 40 | ElSamadisy, Smirnov, Wang & Abdulhai 2025, TRR, doi:10.1177/03611981251333340 | direct, joint RM + VSL | Aimsun, QEW | regulator-based RM / VSL | no number in abstract; DRL "chooses ramp metering" in heavy congestion | abstract [VERIFY] |
| 41 | Zhang Y. et al. 2025, arXiv 2503.01017 | direct MARL, with action masking and rule guards | **field**, I-24, 67 VSL controllers | prior non-RL VSL | warning accuracy +14 %; crash rate −26 % (baseline unclear); **no delay figure** | abstract [VERIFY] |
| 42 | "Field deployment of MARL-based VSL controllers", arXiv 2407.08021 (ITSC 2024) | direct MARL | field, I-24 | — | — | snippet [VERIFY] |

### 3.3 Non-RL references and adjacent hybrids

**Non-RL references (read in full):**
- **Lu X.-Y. et al. 2010** (ITSC, Aimsun): VSL plus MPC-coordinated RM. No numbers.
- **Li Z. et al. 2019** (ITSC, VISSIM): MPC-VSL with a line of CAVs. Delay −3.7 % vs NC.
- **Malikopoulos et al. 2019** (IEEE T-ITS 20(7), VISSIM): optimal control. **Vs SPECIALIST ("tuned with several iterations"): travel time −3 to −19 %, fuel −12 to −17 % ✓.** This is confounded: 100 % AVs with perfect information.
- **Feng et al. 2023** (Sensors, neuroevolution, not RL): the evolution-strategy controller beat RL in 3 of 4 shifted test conditions.

**Adjacent hybrids, not VSL (the source of the 1.5–6 % prior):**
- Sun, Jamshidnejad & De Schutter, IFAC 2023 (DQN tunes ALINEA): +1.9–6.0 % [read in v6].
- Önür, Dabiri & De Schutter, arXiv 2512.07417 (MARL tunes PI-ALINEA / PI-DTA): ≈ 1.5 % [v6, HTML summary].
- Önür et al., arXiv 2608.20858 (MPC + DRL for RM and routing) [abstract + automated summary, VERIFY]. The summary suggests that pure hierarchical MPC beat the hybrid with a perfect model.
- Airaldi, De Schutter & Dabiri, IEEE T-ITS 2025 (MPC as the RL function approximator, RM only) [snippet, VERIFY].

**Reviews:**
- Kušić et al. 2020, Appl. Sci. 10(14) [partial, §3–5]: most studies compare only with NC, and "Walraven … failed to achieve a better result" than the best fixed speed limit.
- Han, Wang & Leclercq 2023, Commun. Transp. Res. 3 [metadata only].
- He, Laval, Han, Hegyi et al. 2025, arXiv 2504.11372, VSL vs jam-absorption driving [abstract only].

### 3.4 Answer, and "what did I miss"

**Is there a hybrid shown to beat a TUNED validated controller in microsimulation by ≥ 10 %? None found.** No paper read has a validated controller (SPECIALIST, MTFC) kept in the loop in microsimulation.
- **The only microsimulation hybrid** (#19, Cheng 2022) tunes the authors' own unvalidated law against a weak baseline.
- **The only VSL hybrid with a validated-class controller** (#9, Sun 2024, a residual on MPC) is macroscopic and **loses to a stronger MPC in all 6 scenarios**.

**What you may have missed:**
1. **The one microsimulation comparison against a *tuned* MTFC (#11) found ≈ 1.6 %** for VSL-only RL. RL there was direct and unconstrained, and tested on its training scenario. This is the most relevant prior for Card A, and it is far below 10 %.
2. **The largest gain over a tuned feedback controller in microsimulation needed ramp metering** (#11, ≈ 9.7 % vs integrated feedback), and was still below 10 %.
3. **≥ 10 % wins over validated-type controllers appear only in three settings:**
   - macro: #3, #5, #6;
   - against baselines whose parameters were set rather than tuned, or not stated: #16, #29, #34 (#34 also gives RL per-lane limits vs one limit for FB);
   - a non-peer-reviewed custom simulator: #39.
4. **RL loses or ties when the comparator is tuned:**
   - #1 vs the best fixed limits;
   - #4 vs a GA-tuned rule;
   - #10 vs tuned FB metering;
   - #28 on mobility vs NC.
5. **SPECIALIST appears to leave more room than MTFC:**
   - MPC and RL beat it in macro (#5);
   - perfect-information optimal control beat a tuned SPECIALIST in VISSIM (Malikopoulos 2019).

   This helps Card B's G, but it also means an MPC comparator may beat SPECIALIST outright. Then H fails whatever G is (§6).
6. **SUMO can show a capacity drop in some setups:** #10 (Fig. 6) and #33 (Fig. 8). That matters for T1; v5 simply never produced one.
7. **The field I-24 MARL VSL (#41) runs behind rule-based safety guards.** It is the closest thing to a deployed "hybrid", but it reports safety and warning metrics, not delay.
8. **Worth reading before Step 2**, in this order:
   - **Müller et al. 2015**, IEEE T-ITS 16(1):512–523: MTFC in microsimulation, which feeds T0 and T1 directly;
   - **Carlson et al. 2011**, IEEE T-ITS 12(4);
   - **Hegyi & Hoogendoorn 2010**: the SPECIALIST field-test results;
   - **Smaragdis et al. 2004 (AD-ALINEA)**: the template for an adaptive set-point comparator;
   - the two post-2022 reviews.

   All are [NOT READ].

## 4. Validated controllers to anchor on

| Controller | Primary sources (read status) | Control law | Published parameters | Field evidence | Open-source code |
|---|---|---|---|---|---|
| **SPECIALIST** (shock-wave theory) | **Read in full locally:** Hegyi, Hoogendoorn, Schreuder, Stoelhorst, Viti, IEEE ITSC 2008, pp. 827–832; Hegyi, Hoogendoorn, Schreuder, Stoelhorst, ECC 2009, pp. 1770–1775 (offline evaluation on field data). **Abstract only [VERIFY]:** Hegyi & Hoogendoorn, ITSC 2010, pp. 519–524, doi:10.1109/ITSC.2010.5624974 (field test); Jonkers et al., ITSC 2011, doi:10.1109/ITSC.2011.6082830 | Detect a jam (q ≤ q_max **and** v ≤ v_max per segment). Estimate the states of the jam and of the free-flow areas. Post a speed-limited area that turns the jam into a low-density state. Act only if the jam is solvable (the fronts converge, q5 > q1, v6 above the limit, the area fits). Detectors report speed and flow every minute; the front locations are recalculated "frequently (e.g., every second)" ✓. | **2008 (METANET, A12, 3 lanes):** 60 km/h, assumed fully obeyed; ρ4 = 33 and ρ5 = 26 veh/km/lane; q5 = 6,100 veh/h; head speed −15 km/h; q_max = 1,500 veh/h/lane, v_max = 50 km/h. **2009:** v_max 80 km/h, q_max 3,600 veh/h, v5 = 75 km/h, q5 = 6,600 veh/h. Field-tuned values not read. | **2008 simulation:** TTS 853 → 775 veh·h (**−9.1 %**), outflow +4.2 % ✓. **2009, 407 field shock waves:** 0–35 % solvable depending on the effective limit and delay. **2010 field test, A12, 14 km [abstract, VERIFY]:** resolved shock waves in "nearly 80 %" of the cases where it activated for one; about half of activations were for other jam types. Delay and throughput effects not read. | None found; implement from the papers |
| **MTFC by VSL** (Carlson, Papamichail, Papageorgiou) | **Read in full:** Transportes 21(3):56–65, 2013, doi:10.4237/transportes.v21i3.694. **Not read [VERIFY]:** IEEE T-ITS 12(4):1261–1276, 2011, doi:10.1109/TITS.2011.2156792; TR-C 46:209–221, 2014 (integrated with ramp metering); JITS 17(4):268–281 | **Cascade.** Outer PI loop on bottleneck density gives the flow set-point q̂c. Inner I loop on the flow just downstream of the VSL area gives b = VSL / legal limit. Traffic is held back about 500 m upstream of the bottleneck. | ρ̂ = 32 veh/km/lane (34 with b = 0.9 in the acceleration area); K′P = 38 km/h, K′I = 9 km/h, KI = 0.0015 h·lane/veh; b in steps of 0.1, ≥ 0.2, changing by ≤ 0.2 per step and between adjacent signs; period 60 s ✓ | **Simulation only** (calibrated METANET A10; NC TTS = 14,163 veh·h ✓). **Feedback: −34.2 %** ✓; with constraints −35.2 %; optimal control −38.8 % ✓. Across the gain grid, TTS changed by −32.2 % to −34.7 %, i.e. it **barely moves with the gains**. No field trial found; in 2013 the authors wrote it "should be attempted". **Microsimulation, not read [VERIFY]:** Müller et al., ITSC 2013; IEEE T-ITS 16(1):512–523, 2015. **SUMO, not read:** Pelenczei et al., ICINCO 2024 reported mean travel time **rising** from 314.7 to 434.0 s vs NC, a warning about mis-tuning. | None found. `sumoITScontrol` has ALINEA, HERO and METALINE ramp metering but no VSL [README only]. Implement from the paper. |
| **MPC-VSL** (Hegyi, De Schutter, Hellendoorn): **yardstick only, not an anchor** | **Read locally:** IEEE T-ITS 6(1):102–112, 2005, doi:10.1109/TITS.2004.842408; ACC 2003 (some symbols lost in OCR) | Rolling-horizon minimisation of TTS plus a penalty on limit changes. The predictor is extended METANET with desired speed = min(density speed, (1+α)·VSL), where **α is a non-compliance parameter**. | T = 10 s, τ = 18 s, κ = 40, ρcrit = 33.5, a = 1.867, v_free = 102 km/h; limits 50–110 km/h in 10 km/h steps, at most 10 km/h drop per minute | Benchmark in which the predictor equals the plant (the authors say this probably flatters MPC): TTS −20.1 % (continuous limits), −17.3 % (discrete limits, safety constraints). No field test. | None found |
| **Deployed rule-based VSL** | I-24 "speed-matching", as described in MARVEL (IEEE Access 12, 2024); Dutch MTM/AID, as a baseline in Pelenczei 2024 | Threshold triggers; display the slowest nearby speed, stepping up per gantry | **Thresholds not published** in anything read | Safety-oriented | — |

**Capacity drop: field anchor.** Chung, Rudjanakanoknad & Cassidy, TR-B 41(1):82–95, 2007 (read in full; Table 1 checked ✓):

| Site | Drop | Density at drop | Notes |
|---|---|---|---|
| I-805 merge, 12 days | **5–18 %**, median 13 % [CALC ✓] | 188–254 veh/km over 4 lanes | The rainy day showed 5 %. |
| SR-24 lane drop | 5.1–8.5 % | — | — |
| Gardiner curve | 3–12 % | — | No drop on a day when density stayed below 129 veh/km. |

**Choice of anchor (my ranking):**
1. **MTFC** for a standing merge bottleneck.
   - It has the clearest control law and parameters.
   - It fits the v5 geometry.
   - It needs capacity drop (lesson 6).
2. **SPECIALIST** for moving jam waves.
   - It is the only mobility-oriented VSL here with a field test of the algorithm itself.
   - It needs SUMO to produce realistic moving jams.
3. **Hegyi MPC** is the natural "MPC with a model fitted on separate seeds" comparator for both.

**Not anchors:** the I-24 and MTM rules. Their thresholds are unpublished and they target safety.

## 5. What every card needs first (shared front end)

1. **New testbed** in `feasibility/vsl_hybrid/`.
   - libsumo `venv314`, one simulation per process, file names that include every varying parameter and the PID.
   - Start from the `ramps_v2` merge geometry: 4 × 1 km upstream segments give room for a VSL area plus the 500 m MTFC acceleration area.
   - Count teleports with `--time-to-teleport 300`. v5 used −1, which hides gridlock.
2. **Compliance model** (v5 has none for HDVs).
   - Post the VSL with `lane.setMaxSpeed` on the VSL-area lanes.
   - Model compliance per vehicle with speedFactor classes: compliant ≈ 1.0; non-compliant drivers drive above the posted limit.
   - The share of each class is a scenario parameter.
   - For a TM21 variant, CAVs comply fully.
3. **Metric harness** (`lessons_metric_gameability.md` §4–§5):
   - **primary:** door-to-door delay per vehicle = (arrival or censor time) − *desired* departure − free-flow time. This includes the origin and insertion queue: tripinfo `departDelay` + `timeLoss`, with `--tripinfo-output.write-unfinished`, plus vehicles never inserted;
   - **co-headline:** served throughput;
   - **side metrics:**
     - on-ramp users' delay;
     - an exposure-normalised safety proxy (e.g. vehicle-seconds with TTC < 1.5 s per vehicle-km);
     - teleports.
   - **Accounting check:** demand = served + in network + pending, exactly.
   - **Sensors:** `getLastIntervalVehicleNumber` and `getLastIntervalMeanSpeed`; never `getInterval…`.
4. **The first cheap kill is the capacity-drop check (T1).**
   - v5's only data show −0.4 % (§1, line 11).
   - SUMO did produce a drop in two published setups (§3.2 #10, #33), so it is possible but not guaranteed.
   - **No capacity drop means no mechanism for mainstream VSL** (lesson 6). That kills cards A and C in this testbed. Card B survives only if moving jams with reduced outflow exist (a re-scoped mechanism).
5. **Simulation start rule** (author, 2026-10-01): before any run, wait for the v6 Claude instance to finish. If that cannot be determined, start only when CPU load is under 15 %.

## 6. Design cards

All three cards share the §5 front end and these definitions (binding; `CLAUDE.md`):
- **Headroom:**
  - H = (best non-learning − I) / best non-learning, on the primary metric.
  - **GO** if H ≥ 10 % with the paired 95 % CI lower bound > 0, in at least one cell, with the side constraints holding.
- **I (the informed reference)** = the *same* controller, with parameters from a lookup table (hidden class → parameters) tuned on the tuning seeds. It is never the best grid point per gate seed.
- **Best non-learning** = the best of:
  - the tuned validated controller;
  - a non-learning adaptive scheduler (online estimation);
  - an MPC whose model is fitted on separate "historical" seeds.
- **Yardsticks reported alongside:** NC (sanity check only) and the best constant cap, tuned on the tuning seeds.
- **Statistics:** paired seeds, medians, 95 % percentile bootstrap CIs, and one convention: the median of paired differences.
- **Proposed side constraints** (to be fixed in the Step-2 protocol):
  - on-ramp users' median delay ≤ +10 % vs the best non-learning controller;
  - exposure-normalised safety proxy ≤ +5 %;
  - served throughput ≥ −1 %;
  - 0 teleports;
  - no gridlock.
- **T2 mechanism:**
  - G = (cost at the pooled-best parameter − cost at the class-best parameter) / pooled cost, on the same seeds.
  - PASS if G ≥ 10 %.
  - G is biased upwards, so a FAIL is a conservative KILL.
- **T3 determinism:** two fresh processes on the same seed give identical metrics.

**Why every card is a long shot: the anchor's strength cuts both ways.** Under this H, a hybrid can pass only if two things are true together:
1. The anchor is about the best non-learning controller already, so that I can beat the MPC and adaptive comparators.
2. The anchor's best parameters move strongly with a hidden condition.

The literature puts these in tension:
- **A strong anchor** (MTFC: TTS barely moves across gains in Carlson 2013; direct RL beat a tuned MTFC by only ≈ 1.6 % in microsimulation, §3.2 #11) leaves little G.
- **A weaker anchor** (SPECIALIST: beaten by MPC and RL in macro, §3.2 #5) may leave G. But then the MPC comparator can beat I outright.

The cards are designed so that the cheap checks expose this early.

### Card A: MTFC with a learned set-point scheduler (recommended first)

- **Kept controller:** the Carlson et al. MTFC cascade (PI on bottleneck density, I on the VSL-area outflow).
  - It always computes the limit.
  - Its rate, range and adjacent-sign constraints act as the shield; a fallback to the fixed tuned set-point is always available.
- **DRL layer:** parameter scheduling. Every 10–15 min it chooses the density set-point ρ̂ (and optionally K′P, K′I) from a bounded grid. It never chooses the speed limit itself.
  - Gains alone are a poor lever: in Carlson 2013, TTS barely moved across the gain grid (−32.2 to −34.7 %).
- **Hidden condition h:** the **driver-population class** of the day.
  - It is the mix of cautious and assertive car-following and lane-changing (SUMO `tau`, `accel`, `lcAssertive`/`lcCooperative` per vType).
  - It shifts the bottleneck's critical density and the size of the capacity drop.
  - It is not directly measured by loops; truck share, by contrast, is observable from loop vehicle lengths and is therefore treated as an *observed* covariate available to every comparator.
- **Why the comparators may miss it:**
  - A fixed set-point is too high on "cautious" days, so the bottleneck breaks down and pays the drop. It is too low on "assertive" days, so capacity is wasted.
  - An MPC with a pooled METANET fit carries the average ρcrit and capacity-drop parameters.
  - **The adaptive comparator is the real threat.** It estimates the critical density online from the bottleneck's flow–density data, in the style of AD-ALINEA (Smaragdis et al. 2004 [NOT READ, VERIFY]).
  - **Prior evidence against:** in microsimulation, an unconstrained direct RL tested on its training scenario beat a tuned MTFC by only ≈ 1.6 % (§3.2 #11).
- **ARC-IT anchor (local, checked):** TM20 Variable Speed Limits (`html/servicepackages/sp138.html`).
  - **The controller:** PSpec **9.3.3.3 Manage Vehicle Speed on Roadway** (`html/pspecs/pspec328.html`): "monitoring the speeds of vehicles, calculating optimal speed limit by lane, and adjusting speed limits" ✓. Its functional object is TMC Variable Speed Limits, with requirement 02, "calculate and set suitable speed limits by lane" ✓ (`html/functionalobjects/funobj24.html`).
  - **Inputs:** 1.1.1.1 Process Traffic Sensor Data (`traffic_sensor_data_for_variable_speed_limits`).
  - **Output:** `variable_speed_limit_control` (TMC → ITS Roadway Equipment), to 9.3.3.1 and on to 1.2.7.2.5 (DMS).
  - **The scheduler** writes the "parameters provided by traffic operations personnel for use by a roadside process to determine optimal speed limits by lane" ✓ (`html/dataflows2/df5749.html`).
  - In ARC-IT those parameters come from *personnel* (via 1.1.4.2). An automated scheduler is therefore **an extension inside 9.3.3.3**, or a new process feeding it. That should be stated as such, not claimed as an existing flow.
- **Comparators:**
  - NC (sanity);
  - best constant cap (yardstick);
  - tuned MTFC (pooled-best ρ̂ and gains);
  - adaptive MTFC (online ρcrit estimation);
  - Hegyi-type MPC (METANET fitted on historical seeds);
  - I = MTFC with a class → ρ̂ table.
- **Tool checks** (criteria to be committed before running):
  - **T0, actuator:** in the mid compliance class, posting b = 0.5 cuts the VSL area's maximum 5-min outflow by **≥ 10 %** vs b = 1.0, and the bottleneck density responds within 5 min.
    - [CALC, my arithmetic; assumes full compliance, Krauss tau 1 s, 7.5 m length + gap] Lane capacity is about 2,930 veh/h at 120 km/h, 2,480 at 60 km/h (−15 %) and 2,150 at 40 km/h (−27 %).
    - Non-compliance shrinks this.
  - **T1, capacity drop:** under NC, with demand above capacity for ≥ 30 min, the queue discharge (5-min mean, ≥ 500 m downstream of the merge, excluding the first 5 min after onset) is **≤ 0.95 ×** the pre-breakdown maximum 5-min flow.
    - This must hold in ≥ 2/3 of breakdown seeds, with **0 teleports**.
    - **Control matters:** literature-parameter MTFC beats NC on median door-to-door delay by **≥ 5 %**, with the CI excluding 0.
  - **T2, mechanism:** 4 classes × 7 set-points (0.80–1.10 × the reference ρcrit) × 5 seeds = 140 runs. **G ≥ 10 %**, and the class-best ρ̂ differs from the pooled-best by at least one grid step in ≥ 2 classes.
  - **T3:** determinism.
- **Gate-0 sketch:**
  - cells: 2 demand cells (peak ≈ 1.05× and ≈ 1.15× capacity for 45 min) × the natural class mix;
  - 20 paired gate seeds per cell;
  - the 6 controllers above;
  - GO/KILL as defined at the top of §6.
- **Build and compute:**
  - testbed and metric harness: 3–4 days;
  - MTFC: 1 day;
  - T0–T3: about 1 h of compute on 32 workers (my estimate; the T3 benchmark measures it). **The T2 verdict is about 1 week away.**
  - adaptive MTFC: 1 day; METANET fit and MPC: 4–6 days;
  - gate: < 2 h of compute. **The gate verdict is about 2.5–3 weeks away.**
- **Fit to the thesis:**
  - High: "adaptive" scheduling of a field-oriented feedback controller, a TM20 PSpec anchor, and a direct "DRL vs reactive / rule / predictive" comparison.
  - If KILLed, the non-DRL findings are the SUMO capacity-drop status and "condition-aware MTFC set-points are worth X %". These are modest.
- **Kill probability: ≈ 93 %** (my estimate, anchored on lesson 3: published hybrid gains are 1.5–6 %, and three v6 gates found 0–5 %). The chain, so you can substitute your own numbers:
  - P(T1 passes) ≈ 0.6: v5 shows −0.4 %, but SUMO produced a drop in #10 and #33; the field shows 3–18 %;
  - P(G ≥ 10 % | T1) ≈ 0.3: a merge with a capacity drop should have a sharper cost curve than v6's flat MFD, where G was 2.66 %, but MTFC is gain-insensitive and §3.2 #11 found ≈ 1.6 %;
  - P(H ≥ 10 % | T2) ≈ 0.4: the adaptive and MPC comparators can only shrink H;
  - overall pass ≈ 0.07.

### Card B: SPECIALIST with learned activation and parameter scheduling

- **Kept controller:** SPECIALIST (Hegyi et al. 2008/2009).
  - It detects the jam, tests solvability and constructs the fronts.
  - Its solvability test is the shield.
- **DRL layer:** activation switching plus parameter scheduling.
  - Per detected jam it chooses go or skip, and the displayed limit V ∈ {50, 60, 70} km/h, ρ4 and (ρ5, q5) from bounded grids.
- **Hidden condition h:** the **compliance share**, i.e. the effective speed in the controlled area under the displayed limit, plus the detection delay.
  - The 2009 field-data analysis shows that solvability depends on exactly these (0–35 % solvable, depending on the effective limit and delay).
  - Two field failure modes have been reported: the limit did not cut flow enough, or area 4 became too dense and triggered new jams (as reported by Han et al. 2022; secondary source).
- **Why the comparators may miss it:**
  - Tuned SPECIALIST assumes one effective speed.
  - The MPC carries a pooled α, the non-compliance parameter in Hegyi's METANET extension.
  - **The adaptive comparator is the threat:** it re-estimates the effective speed from area-4 detectors after each activation. Compliance becomes *observable* once the limit is on, so DRL's edge would have to come from anticipating it.
- **ARC-IT anchor:** the same 9.3.3.3 and `variable_speed_limit_control` as Card A.
  - 9.3.3.1 Collect Vehicle Speed supplies `vehicle_speed_data_from_roadside` (`html/pspecs/pspec330.html`).
  - For a CAV-delivered variant: **TM21** (`sp68.html`), with 9.3.3.5 Manage Speeds at Roadside → `speed_management_data_to_vehicle` (`pspec683.html`).
- **Comparators:**
  - NC;
  - best constant cap;
  - tuned SPECIALIST;
  - adaptive SPECIALIST (online effective-speed estimate);
  - Hegyi MPC (α and the METANET parameters fitted on historical seeds);
  - I = SPECIALIST with a class → (V, ρ4, q5) table.
- **Tool checks:**
  - **T0:** as in Card A, plus: in the low compliance class, the effective speed in the controlled area at V = 60 is **≥ 10 km/h** above the high-compliance class. This shows the hidden condition is real.
  - **T1b, moving jams:** under NC, upstream-moving jam waves (front speed −10 to −25 km/h, lasting ≥ 5 min, detected by the SPECIALIST criteria) occur in **≥ 50 %** of seeds.
    - Jam outflow must be **≤ 0.95 ×** the pre-jam maximum flow, with 0 teleports.
    - **Control matters:** literature-parameter SPECIALIST resolves **≥ 30 %** of detected waves and lowers median delay vs NC by **≥ 3 %**.
  - **T2:** 3 compliance classes × 9 (V, ρ4) combinations × 5 seeds = 135 runs. **G ≥ 10 %**.
  - **T3:** determinism.
- **Gate-0 sketch:** as in Card A, with SPECIALIST as the controller family and cells defined by the natural compliance mix × 2 demand levels.
- **Build and compute:**
  - SPECIALIST: 3–4 days (detection, state estimation, fronts, solvability, sign mapping), plus 1–2 days of disclosed throw-away-seed calibration to get moving jams.
  - **The T2 verdict is about 2 weeks away; the gate about 3–4 weeks.** Compute is similar to Card A.
- **Fit to the thesis:**
  - High: a field-tested Dutch controller and an adaptive layer, with a TM20/TM21 anchor.
  - Prior art: Han et al. 2022 (TR-C 144:103900) replaced SPECIALIST with RL in METANET. A *hybrid in microsimulation* is "not found in the papers read". That is not a novelty claim.
- **Kill probability: ≈ 95 %.**
  - P(T1b: SUMO moving jams with a reduced outflow) ≈ 0.35;
  - P(G | T1b) ≈ 0.45: compliance enters SPECIALIST's equations directly, and SPECIALIST leaves room (§3.2 #5; Malikopoulos 2019);
  - P(H | T2) ≈ 0.3: compliance is observable once the limit is active, and an MPC may beat SPECIALIST outright, as in #5;
  - overall pass ≈ 0.05.

### Card C: MPC-VSL with learned model correction, MTFC as fallback

- **Kept controllers:**
  - a Hegyi-type MPC-VSL, with a METANET predictor fitted on historical seeds;
  - the tuned MTFC as fallback shield (switch to MTFC if the MPC is infeasible or bottleneck density exceeds a guard).
  - **Caveat:** the MPC is published but **not field-validated**, a weaker "validated" status than SPECIALIST.
- **DRL layer:** model correction. Every 10–15 min it corrects the MPC's predictor parameters (ρcrit, the capacity-drop factor, α) from bounded grids.
  - Closest published patterns, all macroscopic:
    - Sun, Jamshidnejad & De Schutter, IEEE T-ITS 25(7):6756–6769, 2024, doi:10.1109/TITS.2023.3342651: a DRL residual on MPC for RM + VSL [abstract only, VERIFY];
    - Airaldi, De Schutter & Dabiri, IEEE T-ITS 2025: RL tunes the MPC; ramp metering only [snippet, VERIFY];
    - Önür, Dabiri & De Schutter, arXiv 2608.20858 [abstract + automated summary, VERIFY].
- **Hidden condition h:** the same as Card A (driver-population class), optionally crossed with Card B's compliance share. Both change METANET's parameters.
- **Why the comparators may miss it:**
  - A pooled-fit MPC is wrong on non-average days. This is lesson 2's mechanism 1, model mismatch.
  - **The adaptive comparator:** online recursive estimation of the METANET parameters ("adaptive MPC").
  - If the tuned MTFC beats every MPC, then I_C must beat MTFC by 10 %.
- **ARC-IT anchor:**
  - 9.3.3.3 as above, plus **1.1.3 Generate Predictive Traffic Model**, which is in TM20's PSpec list (`sp138.html`).
  - **No data flow connects 1.1.3 and 9.3.3.3** in the local pages; the correction needs a **new data flow**.
- **Comparators:**
  - NC;
  - best constant cap;
  - tuned MTFC;
  - adaptive MPC;
  - pooled-fit MPC;
  - I = MPC with a class → fitted-model table.
- **Tool checks:**
  - T0, T1 and T3 are shared with Card A.
  - **T2_C:** 4 classes × {MPC pooled fit, MPC class fit} × 5 seeds = 40 runs.
    - PASS if G_C ≥ 10 % **and** the class-fit MPC beats the tuned MTFC on median delay.
- **Gate-0 sketch:** as in Card A.
- **Build and compute:** the MPC is built for Card A's gate anyway. Add 1–2 days for the correction interface.
  - **The T2_C verdict is about 2 days after Card A's MPC exists.**
  - MPC runs are slower; T2_C costs < 1 h of compute (estimate).
- **Fit to the thesis:** good for the "beats predictive control" clause. Weaker on "validated controller in the loop".
- **Kill probability: ≈ 96 %.**
  - P(T1) ≈ 0.6, shared with Card A;
  - P(G_C ≥ 10 % and MPC competitive | T1) ≈ 0.35;
  - P(H ≥ 10 % vs tuned MTFC and adaptive MPC | T2) ≈ 0.2: the closest published pattern (§3.2 #9) lost to a stronger MPC in all 6 scenarios;
  - overall pass ≈ 0.04.

**Considered but not carded:**
- **Coordinated MTFC + ALINEA** (Carlson et al. 2014, TR-C 46 [NOT READ]). A DRL hand-over between ramp metering and VSL would add a second ARC-IT package.
  - It is the strongest literature signal: the largest microsimulation gain over tuned feedback needed ramp metering (≈ 9.7 %, §3.2 #11), still below 10 %.
  - But ElSamadisy et al. 2025 (Aimsun, TRR [abstract only, VERIFY]) found that a DRL controller chose ramp metering over VSL in heavy congestion, which hints that the hybrid would collapse to ALINEA.
- **A residual on MTFC.** The gate's I (a parameter lookup table) cannot bound what a residual could do, so H as defined does not apply to it.

## 7. Recommendation

All three cards have a kill probability of about 90 % or more. Those are honest priors, not pessimism. The order is therefore set by **cost-to-kill and shared work**:

1. **Round 1, shared:** T0 (actuator), T1 (standing-bottleneck capacity drop), T1b (moving jams) and T3 (determinism), on one testbed with one set of committed criteria.
   - Cost: about 1 week of build and < 1 h of compute.
   - **This one round can kill all three cards.**
2. **If T1 passes:** Card A's T2 (140 runs). MTFC takes about 1 day to build.
3. **If T1b passes:** Card B's T2 (135 runs; SPECIALIST takes 3–4 days to build). This is the re-scoped "shockwave damping" mechanism of lesson 6.
   - If both T1 and T1b pass, run both T2s. Their compute is minutes; the only extra cost is building SPECIALIST.
4. **Build the adaptive comparator and the MPC only after some T2 passes.** With the MPC built, T2_C for Card C is nearly free.
5. **If neither T1 nor T1b passes:** KILL VSL in SUMO.
   - Survives as a non-DRL finding: the measured capacity-drop and moving-jam status of SUMO's default models at a merge, with numbers.

## 8. Seeds: preliminary inventory and a *proposal* (for Step 2; not approved, not used)

**Used in v5** (code audit; the full inventory is Step 2's job):
- **Training:** seeds 0–4.
  - Env seed = seed·1000 + w, w = 0–47 (`train.py:116`).
  - Episode seed = (env_seed·100000 + count) mod 2³² (`core/env_interact.py:192-201`), with offsets +10,000 (routes) and +50,000 (anomalies).
  - EvalCallback env seed = (seed + 5000)·1000 (`train.py:259`).
- **Scenario pools:** 0–199 (in the repo) and 42–241 (on the VMs; not in the repo). Vehicle types use the pool seed + 10,000.
- **Evaluation:** 99000–99029, reused across more than 10 evaluation rounds and for baseline selection (`evaluate_models.py:401, 443`).
- **Tests:** 0–29 (+10,000, +20,000), 42, 99, 1000+.
- **v6** (for safety): 2051–2055, 2101–2110, 2151–2160, 2201–2240, 2990–2999.

**Proposed block 7,100,000–7,399,999:**
- **Collision check:**
  - v5 training episode seeds lie in blocks e·100,000 + c, for e ∈ {0–47, 1000–1047, …, 4000–4047}. Here e = 71–73, so there is no overlap.
  - The evaluation and EvalCallback episode seeds wrap to about 1.31 × 10⁹ and 1.78–2.2 × 10⁹. No overlap.

| Use | Seeds |
|---|---|
| Throw-away calibration | 7,100,000 |
| Round-1 tool checks | 7,100,001–7,100,019 |
| T2 | 7,100,020–7,100,039 |
| Tuning | 7,100,100–7,100,149 |
| MPC fitting ("historical") | 7,100,150–7,100,199 |
| Gate | 7,100,200–7,100,299 |
| Reserved confirmatory | 7,100,500–7,100,999 |
| DRL training (after a GO only) | 7,200,000–7,299,999 |
| DRL validation (checkpoint selection) | 7,300,000–7,300,099 |

## 9. Decisions for the author

1. **Which card**, or the shared Round 1 first (recommended)?
2. **Testbed:** start from the `ramps_v2` merge geometry (recommended), or a new lane-drop bottleneck?
3. **Hidden-condition family:** driver-population class (Cards A and C), compliance share (Card B), or both crossed (costs ×3 in T2)?
4. **Calibration:** may I use one disclosed throw-away seed to tune vType parameters until NC shows a capacity drop? If yes, what is the allowed parameter range? Tuning SUMO *until* a drop appears is itself a threat to validity; it needs bounds and literature-plausible values.
5. **Seed block** (§8): approve, or name another.
6. **`main`:** commit `ebba794` (the pending v5 work) is local only. Push `main` too, or leave it on the branch?

## 10. Limits of this screen

- **Coverage:** 12 web searches with no Scopus, Web of Science or Scholar. TRB, ITSC and Chinese-language venues are probably under-covered.
- **Read status:** several key items (the SPECIALIST field-test results, MTFC microsimulation by Müller et al., AD-ALINEA, the Sun et al. 2024 MPC+DRL framework) are abstract-only or not read, and are marked as such.
- **Kill probabilities** are subjective; the chains are shown so they can be replaced.
- **Compute estimates** are not measured; the Round-1 benchmark measures them.
- **Code-audit items** marked [INF] were not re-run.
