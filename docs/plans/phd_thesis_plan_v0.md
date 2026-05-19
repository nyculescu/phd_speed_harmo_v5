# PhD Thesis Plan — Speed Harmonization via Distributional Deep RL (v0)

| Field | Value |
|---|---|
| Doc version | v0.6 (2026-05-19 results: 100 % CAV headline + 4-config reward-weight ablation) |
| Status | **Active** — paper-1 cash-cow scope (see ADR-012) |
| Last updated | 2026-05-18 |
| Primary author | Catalin Niculescu |
| Audience | PhD supervisor; paper co-authors; new collaborators (human or LLM) onboarding the project |
| Companion docs | [README.md](../../README.md) (operational), [docs/knowledge_base/](../knowledge_base/) (literature corpus, gitignored) |
| Scope split | This doc owns **research design + architecture + traceability**. README owns **how to run + repo layout + remote VM bootstrap**. Zero overlap. |

> **Reading guide.** Sections 1–3 give the academic framing (problem, RQs, contribution). Section 4 is the canonical record of every load-bearing design decision (ADR-style with academic justification). Sections 5–7 are the engineering reference (architecture, DRL, traffic model). Section 8 anchors the evaluation. Sections 9–11 cover roadmap, risks, and the literature positioning. New collaborators should read §1, §3, §11, then skim §4's ADR titles before touching code.

---

## 1. Glossary

| Term | Definition |
|---|---|
| **VSL** | Variable Speed Limit — posted speed limit that varies in time and/or space to manage traffic flow |
| **CAV-direct VSL** | VSL delivered to CAVs as in-vehicle speed commands (e.g. `traci.vehicle.slowDown()`); no roadside sign is involved. Our learned controller is CAV-direct. |
| **Posted VSL** | VSL delivered via roadside signs / gantries — the regulatory and field-deployed form. Discrete by hardware (LED panel) and by regulation (MUTCD §2B.13, EU codes). Comparison baselines (NC, M110_uniform, diff_mild) are posted. |
| **CAV** | Connected Automated Vehicle — assumed to comply 100 % with CAV-direct commands |
| **HDV** | Human-Driven Vehicle — out of scope for the paper; deferred to the PhD chapter |
| **SAR** | State / Action / Reward — the three pluggable components of the MDP, swappable via the `sar_components/` registry |
| **TQC** | Truncated Quantile Critic — distributional continuous-control RL (Kuznetsov et al., 2020) |
| **NC** | No-Control baseline — free-flow limits, no intervention |
| **METASTABLE** | Traffic regime near capacity; the only regime where VSL is theoretically useful per [core/regime_detector.py:37-39](../../core/regime_detector.py#L37-L39) |
| **MUTCD** | US Manual on Uniform Traffic Control Devices — source of the lane gradient (≤10 kph) and step-down (≤16 kph) constraints enforced in [r44_action_v2.py:50-51](../../sar_components/actions/r44_action_v2.py#L50-L51) |
| **TTS / TET / TIT** | Total Time Spent / Time Exposed to TTC threshold / Time Integrated TTC — efficiency + safety KPIs from Lu et al. 2023 |
| **CVS** | Coefficient of Variation of Speed (σ/μ) — safety surrogate from MARVEL (Zhang et al. 2024) |

> **Terminology note.** In the CAV-control literature (notably Vinitsky et al. 2018), *CAV-direct* and *posted* VSL are termed **"Lagrangian"** and **"Eulerian"** by analogy with the fluid-dynamics observer frame. We use the operational terminology throughout this plan and the derived papers for accessibility; verbatim quotes from prior work retain the original phrasing.

---

## 2. Research positioning

### 2.1 Problem statement

Freeway weaving sections (merge + diverge in close proximity) suffer **capacity drop** and **shock-wave propagation** when demand approaches capacity. Existing mitigation — posted VSL, ramp metering, hand-tuned differential lane control — has known limitations:
- Posted VSL is fundamentally incompatible with continuous-action learned policies — posted limits must be discrete by regulation and hardware (see ADR-014), so a controller outputting e.g. `seg_L1 = 76.4 km/h` cannot be posted-deployed regardless of driver-compliance level
- Static / rule-based policies cannot adapt to stochastic anomalies (incidents, weather, ramp spikes)
- Multi-agent RL approaches (e.g. MARVEL) impose deployment complexity that has stalled real-world uptake

**This project asks:** can a **single centralised distributional RL agent**, acting on connected automated vehicles directly (CAV-direct VSL), learn **per-lane differential speed control** that beats both static posted baselines and hand-tuned active CAV-direct policies on a ramp-interchange weaving section under stochastic demand and anomalies?

### 2.2 Research questions (Paper 1 scope — tight by design)

Paper 1 owns **one contribution slice** per [project_cash_cow_scope_discipline.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_cash_cow_scope_discipline.md). Active CAV-direct sweep, broader DRL/MPC/rule-based comparisons, and CAV penetration sweeps are explicitly *not* Paper 1 RQs — they are Paper 2 / Paper 3 / PhD chapter material (see §3).

| RQ | Question | Status | Evidence |
|---|---|---|---|
| RQ1 | Can a TQC agent with continuous per-lane CAV-direct VSL outperform a representative static posted baseline (M110_uniform) on aggregate reward, with the gain attributable to harmonization (lane variance suppression) rather than throughput gaming? | **Answered: YES (strengthened by 2026-05-19 100 % CAV results — see §8.5)** | TQC Box(4) 100 % CAV (`experiment_20260518_133246`): mean −164.8 across 5 seeds (best −155.9, worst −172.5), +221 reward over NC, +174 over M110_uniform. `lane_sigma` = 1.61 vs NC ≫ 1.6, `max_lane_diff_kph` = 3.3 vs NC ≫ 3. Throughput 4 657 vph ≈ baseline 4 660 ± 5 — preserved. |
| RQ2 | Does the policy generalise across anomaly conditions (ramp spike / speed reduction / lane closure) without retraining? | **Answered: YES** (verified at 50 % CAV; not yet re-checked at 100 % CAV, expected to be at-least-as-strong since the policy variance is lower) | Within-policy Δ ≤ ±3 reward points between normal and anomaly episodes vs NC's −5.6 (from 4-VM run, May-16). |
| RQ3 | Do the `reward_components` map to traffic-engineering KPIs that are **specific to CAV-direct VSL effectiveness** (not generic traffic safety / efficiency surrogates)? | **Answered: YES, with ablation backing (2026-05-19, see §8.5)** | Four-config ablation (base / harmo_pure / no_throughput / no_smoothness) confirms: physical KPIs (`lane_sigma`, `max_lane_diff_kph`, `ds_flow_vph`, action stats) move coherently with reward changes; **no_throughput preserves throughput as a side-effect** (4 662 vph vs base 4 657 — within noise) — directly addresses the standard reviewer challenge. KPI extractor (`tools/eval_to_kpi.py`) still pending (P2 in §3). |
| RQ4 | Is the contribution novel relative to the closest prior art? | **Answered: YES (qualified — see §11 + §2.3 for honest framing)** | No prior paper combines (TQC + per-lane mainline + ramp VSL + CAV-direct + stochastic anomalies). |

**Dropped from earlier draft (and why):**
- ~~RQ2 (active CAV-direct sweep)~~ → moved to **Paper 2 hook**. Defining the eight M*_active baselines was useful for sharpening Paper 1's claim, but the *sweep itself* is a richer contribution that deserves its own paper. Paper 1 may still report a single best active-CAV-direct point as a robustness check, but the headline comparison stays vs. static posted VSL.
- ~~RQ3 (harmonization-vs-throughput-gaming mechanism)~~ → folded into RQ1 as part of its evidence.
- ~~RQ5 (broad TTS/TET/CVS KPI translation)~~ → replaced by the narrower §8.4 KPI list specific to CAV-direct-VSL effectiveness, per pushback that broad safety surrogates are out of scope (see ADR-010).

### 2.3 Contribution claims (Paper 1, lit-grounded and honestly scoped)

Per §11 verbatim comparison against TD3LVSL (Lu et al. 2023), Vinitsky et al. 2018, and MARVEL (Zhang et al. 2024):

1. **First TQC-based VSL controller** ("cash cow" — the central methodological claim).
   TD3LVSL motivates TD3 *specifically* for Q-value overestimation; TQC strictly supersedes that motivation via 5-critic × 25-quantile distributional value heads. No reviewed paper in the corpus uses distributional RL for VSL. This is the load-bearing novelty that sustains the PhD's multi-paper plan (§3). **Empirically verified 2026-05-19**: 5 seeds × 100 % CAV achieve mean reward −164.8 (best −155.9), beating the strongest static-CAV-direct baseline (M60_active) by +40 reward points, with reward-weight ablation confirming the result is not a reward-tuning artefact (§8.5).

2. **Per-lane mainline + per-ramp CAV-direct VSL under stochastic anomaly demand** (qualified honestly).
   TD3LVSL has lane-level VSL but posted; Vinitsky has CAV-direct (their term: "Lagrangian") but uniform-per-segment; MARVEL has per-gantry but posted and discrete. The combined Box(4) `[L0, L1, L2, ramp]` continuous-action CAV-direct controller is **unreported in the corpus we reviewed**, but the author (Catalin) flags this claim as needing softer language in the paper than "first" — phrasing options like "to the best of our knowledge, the first reported instance combining …" with a clear bibliography pointer. The reviewer-defensible framing is the *combination*, not any single element. **Per-lane behaviour empirically confirmed**: action_L0_std ≈ 10 kph and L0-L2 differential ≈ +3.5 kph across seeds — the policy genuinely exercises the per-lane action space rather than collapsing to uniform control (§8.5).

3. ~~First evaluation against an exhaustive static CAV-direct baseline sweep~~ → **Paper 2 hook, not Paper 1**. Defining the M\*_active sweep was scope-defining work; the sweep *as a contribution* belongs to a follow-up paper. Paper 1 may include 1–2 active CAV-direct baselines as a robustness check but does not claim the sweep as its contribution.

4. **Safety by construction is empirically verified** (new claim, supportable per 2026-05-19 results).
   ADR-010's collision-counter codebase change landed and was exercised: **0 collisions across 660 evaluation episodes** (4 reward configs × 5/3 seeds × 30 episodes, plus 11 baselines per config). The Krauss + slowDown(duration=30 s) safety-by-construction argument is now backed by a concrete denominator, not just a theoretical claim. See §8.5.

### 2.4 Caveats kept vs deferred (paper-first scoping)

| Reviewer concern | Source paper | Decision | Justification |
|---|---|---|---|
| Reward weights chosen by hand, no ablation | MARVEL admits same on p. 162002 | **Address** — 5-row reward ablation in paper (P3) | Cheap (5 retrains); strengthens central claim |
| CAV penetration sweep | Vinitsky 2018 (10% AV benchmark) | **Defer** — "limitations" paragraph + ADR-008 | PhD chapter material; out-of-scope for Paper 1 per [project_cash_cow_scope_discipline.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_cash_cow_scope_discipline.md) |
| Safety surrogate (TTC, TET, TIT, CVS) | Lu 2023, MARVEL | **Defend by construction** — ADR-010 | SUMO Krauss car-following + TraCI `slowDown()` semantics together make rear-end collision impossible by construction. Paper reports collision-count = 0 across all eval episodes as positive evidence. **Codebase change required** to make this verifiable (see ADR-010 §Action). |
| MUTCD step-down across time | MARVEL devoted a section | **Partially address** — report `action_*_std` and inter-step Δ distribution; no new mechanism | Spatial step-down already enforced; temporal can be reported, not enforced |
| Simulator realism (vs calibrated TransModeler) | MARVEL | **Defend by SUMO citations** — ADR-011 | Lopez et al. 2018 (ITSC, the recommended SUMO citation), Krajzewicz et al. 2002 (validation paper), Behrisch et al. 2011 (overview). No new simulator calibration work. |
| Ramp-fraction sweep range arbitrary? | (anticipated) | **Defend by breakdown literature** — ADR-013 | [0.20, 0.30] brackets the stochastic-capacity / probabilistic-breakdown regime per Lorenz & Elefteriadou (TRB E-C018), Chung et al. 2007 (TRB Part B), Han et al. 2022 (TRC). Already implemented; ready paper paragraph in ADR-013. |
| **Reward-yardstick incomparability across reward-weight ablations** | (introduced by 2026-05-19 results) | **Methodological note** in §8.1 + §8.5 | When the reward weights differ between configs, the same physical scenario yields different reward numbers because the reward function itself differs. Cross-config comparisons must use either (a) within-config gap-over-baselines, where the agent and baselines share a yardstick, or (b) reward-independent physical KPIs (lane_sigma, ds_flow, max_lane_diff). NEVER compare absolute reward values across configs. Worked example in §8.5. |
| Comparison vs other DRL / hybrid / MPC controllers | Standard PhD-thesis question | **Defer to Paper 3** — explicit roadmap entry | Building external-comparator infrastructure now (logged in §3 backlog) so Paper 3 has the harness ready |

---

## 3. Project timeline / phase map

```
2023-2025  v1–v4    [4 → 3 lane-drop, posted VSL, DQN/QR-DQN/Rainbow]
                    Outcome: "Fixed 3 years, no positive result" — supervisor verdict
                    ─────────────────────────────────────────────────────────
2026-Q2    v5.0     Paradigm shift: ramp interchange, CAV-direct VSL, continuous TQC
                    (ADR-001 through ADR-007 below)
2026-05-16 v5.1     First 4-VM deploy on vast.ai (SAC4 / TQC4 / SAC5 / TQC5 × 5 seeds)
                    Outcome: TQC Box(4) +85 reward over NC; reproducible
2026-05-18 v5.2     - Reproducibility confirmed (2nd TQC Box(4) run within 2.4 pts)
                    - Lit comparison performed: novelty qualified (§11)
                    - Plan v0.2 authored
                    - 100 % CAV directive (ADR-008)
                    - Safety by construction (ADR-010, codebase change LANDED)
                    - SUMO defended by own citations (ADR-011)
                    - Cash-cow scope discipline (ADR-012)
                    - KPIs narrowed to CAV-direct VSL effectiveness (§8.4)
                    - 4 parallel training runs launched at 100 % CAV (base +
                      harmo_pure + no_throughput[partial 3 seeds] + no_smoothness)

2026-05-19 v5.3     ← we are here (plan v0.6)
                    - 4-config evaluation complete: see §8.5 verified results
                    - 0 collisions / 660 evaluation episodes (ADR-010 evidence)
                    - 100 % CAV gives mean −164.8 (vs 50 % CAV −321) — paper headline
                    - Reward-weight ablation confirms 5-term design is well-calibrated
                    - Cross-config reward-yardstick caveat surfaced and documented
                    ─────────────────────────────────────────────────────────
Paper 1    Next     P1: ✅ Codebase change — collision counting per ADR-010 (landed 2026-05-18)
           cash-cow P2: tools/eval_to_kpi.py — derive KPIs 1-8 + 10 from existing CSVs
                    P3: ✅ Reward-weight ablation — 4 configs run 2026-05-18, evaluated
                        2026-05-19 (base, harmo_pure, no_throughput, no_smoothness;
                        see §8.5 for results)
                    P4: ✅ 100 % CAV retrain of TQC Box(4) — 5 seeds completed
                        2026-05-18 (`experiment_20260518_133246`)
                    P5: Paper draft (venue: TBD after KPI strength is known)
                    NEXT: tools/eval_to_kpi.py — derive paper-ready KPI table from
                          the 2026-05-19 evaluation_summary.csv files (no new compute)
Paper 2    Later    Active CAV-direct baseline sweep analysis (M60-M110_active, diff_*)
                    + demand-pattern sensitivity sweep (widen ramp_fraction beyond
                      [0.20, 0.30] per ADR-013, sweep into under-stressed and
                      over-stressed regimes)
                    Reuses Paper 1's codebase + eval data
                    Question: "when does aggressive static beat learning?" and
                    "how does the per-lane controller degrade outside the
                    stochastic-capacity regime?"
Paper 3    Later    Apples-to-apples vs other DRL / MPC / hybrid / rule-based controllers
                    Requires implementing external comparators (build infra now)
PhD thesis Aggregate Papers 1-3 + HDV sensitivity sweep + multi-topology + MARL extension
                    Plus the "distributed RL" angle (cooperative multi-agent TQC)
```

---

## 4. Design Decisions Log (ADR)

Each entry follows MADR (Markdown ADR) format: status, context, decision, consequences, alternatives, references, traceability.

### ADR-001 — CAV-direct VSL over posted signs
**Status:** Accepted (v5.0, 2026-Q2)
**Context:** v4 used posted VSL on a lane-drop network and produced no positive result over 3 years. Driver-compliance variance dominated the signal.
**Decision:** Switch to **CAV-direct** VSL — agent commands CAVs directly via `traci.vehicle.slowDown()` every 5 SUMO steps, duration = one aggregation window (30 s). Implementation: [core/env_interact.py:545-600](../../core/env_interact.py#L545-L600).
**Consequences:**
- (+) Removes HDV compliance noise from the control signal
- (+) Enables per-vehicle granularity (per-lane control becomes meaningful)
- (−) Restricts the operating regime to networks with non-trivial CAV penetration
- (−) Adds TraCI overhead per simulation step
**Alternatives rejected:** Posted VSL (signal-to-noise too low — v4 evidence); mixed posted + CAV-direct hybrid (Box(5) variant kept for ablation — see ADR-004).
**References:** Vinitsky et al. 2018, *Lagrangian Control through Deep-RL Applications to Bottleneck Decongestion* (ITSC, pp. 759–765) — note: their *Lagrangian control* is our *CAV-direct VSL* per the terminology note in §1; the canonical demonstration that 10 % AV CAV-direct control can improve bottleneck outflow by 25 %.
**Traceability:** `_CONTROLLED_SEGS` ([env_interact.py:50-52](../../core/env_interact.py#L50-L52)), `_apply_cav_slowdown()` ([env_interact.py:545-600](../../core/env_interact.py#L545-L600)), `_SLOWDOWN_INTERVAL=5` ([env_interact.py:513](../../core/env_interact.py#L513)).
**See also:** ADR-014 strengthens this decision with an independent action-space–topology argument that holds even at 100% driver compliance.

### ADR-002 — Ramp interchange topology over lane-drop
**Status:** Accepted (v5.0)
**Context:** v4's 4→3 lane-drop is geometrically forced — the bottleneck location is fixed and well-studied. v5 needed a topology where harmonization could create *adaptive* gap-creation rather than static bottleneck mitigation.
**Decision:** Use `ramps_v0` / `ramps_v2`: 3-lane mainline → 4-lane weaving buffer (250 m, on-ramp acceleration lane L0) → 3-lane downstream, with on-ramp + off-ramp flanking the weaving section.
**Consequences:**
- (+) Bottleneck *and* merge interact dynamically — richer policy space
- (+) Realistic for highway interchanges (matches European geometry)
- (−) Two interacting bottlenecks make credit assignment harder
- (−) Single-topology study (a limitation for the paper; flagged in §2.4 and §9)
**Traceability:** [traffic_environment/sumo/ramps_v0.net.xml](../../traffic_environment/sumo/ramps_v0.net.xml), [generate_ramp_network.py](../../traffic_environment/sumo/generate_ramp_network.py).

### ADR-003 — Continuous action space + TQC over discrete + DQN family
**Status:** Accepted (v5.0)
**Context:** v4 used QR-DQN / Rainbow on a 5-level discrete VSL. Discrete actions interact poorly with MUTCD adjacent-lane gradient and step-down constraints — the agent kept choosing infeasible action combinations. TD3LVSL (Lu 2023) motivated TD3 specifically to address Q-value overestimation; TQC strictly supersedes via quantile critics.
**Decision:** Continuous Box(4) action with post-action MUTCD clipping. Primary algorithm: **TQC** (sb3-contrib) with 5 critic networks × 25 quantiles, top-2 quantiles dropped per critic. SAC baseline (sb3) for comparison.
**Consequences:**
- (+) Distributional value head reduces overestimation under noisy reward
- (+) MUTCD clipping is now a soft constraint (action projected, not gradient-blocked)
- (−) Continuous policy harder to interpret than discrete
- (−) Replay buffer is larger (500k transitions)
**Alternatives rejected:** Discrete QR-DQN (v4 lineage, failed); PPO (on-policy, sample inefficient); RecurrentPPO (kept as POMDP-safe option, lower priority); TD3 (TD3LVSL already published — TQC differentiates).
**References:** Kuznetsov et al. 2020 (TQC); Lu et al. 2023 (TD3LVSL — predecessor framing); SAC Spinning Up documentation (project knowledge base).
**Traceability:** `R44ActionV2._setup` ([r44_action_v2.py:88-99](../../sar_components/actions/r44_action_v2.py#L88-L99)), TQC build ([train.py:264-287](../../train.py#L264-L287)).

### ADR-004 — Per-lane action (Box(4) primary, Box(5)/Box(7) ablations)
**Status:** Accepted (v5.1)
**Context:** Per-lane differential VSL is sparsely studied in DRL literature. TD3LVSL uses lane-cells but posted; MARVEL is per-gantry uniform.
**Decision:** Box(4) is the primary: `[L0_VSL, L1_VSL, L2_VSL, ramp_VSL]` applied on `seg_0_before` (CAV-direct). Box(5) adds a posted-style sign on `seg_1_before` (CAV-direct / posted hybrid). Box(7) adds per-lane on `seg_1_before` too.
**Consequences:**
- (+) Empirical winner across 4-VM 5-seed comparison: Box(4) TQC mean −321 vs Box(5) TQC −335
- (+) Simpler than Box(5) / (7) → cleaner paper story
- (−) Per-lane VSL is less standard in real-world deployments (some jurisdictions don't permit it) — flag in paper "limitations"
**Note on Box(5):** Box(5) was an attempted CAV-direct / posted hybrid that adds a continuous posted-style sign on `seg_1_before` applied via `conn.edge.setMaxSpeed()` ([env_interact.py:499-503](../../core/env_interact.py#L499-L503)). Its empirical underperformance (TQC Box(5) mean −335 vs TQC Box(4) mean −321 — a +14 reward-point loss) is cited as the *empirical* leg of the methodological argument in ADR-014 against hybrid CAV-direct / posted designs. Box(5) is retained in the codebase as an ablation reference but is not the paper's primary action variant.
**Traceability:** [r44_action_v2.py:1-35](../../sar_components/actions/r44_action_v2.py#L1-L35), config flags `use_box5` / `use_box7` in [per_lane_stochastic.yaml:45-46](../../configurations/per_lane_stochastic.yaml#L45-L46).

### ADR-005 — Regime indicator in observation
**Status:** Accepted (v5.0)
**Context:** VSL is theoretically useful only in METASTABLE regime ([regime_detector.py:8-11](../../core/regime_detector.py#L8-L11)). Forcing the agent to discover this from raw speed/occupancy wastes capacity.
**Decision:** Include 3-D one-hot regime indicator in observation, computed by [`RegimeDetector`](../../core/regime_detector.py) on `seg_0_before` speed + occupancy.
**Consequences:**
- (+) Reduces sample complexity (agent doesn't relearn the regime classifier)
- (−) Couples observation to a hand-tuned threshold (75 / 45 kph speed + 8% occ)
**References:** Han et al. 2022; foundational work on regime-conditioned VSL.
**Traceability:** `RegimeDetector.classify()` ([regime_detector.py:101-117](../../core/regime_detector.py#L101-L117)), encoding at [r44_state_v2.py:143-148](../../sar_components/states/r44_state_v2.py#L143-L148).

### ADR-006 — Reward v4: quadratic penalties, ×5 scale, no dead zones
**Status:** Accepted (v5.1)
**Context:** Reward v3 had ~3 reward points spread across an episode, three of five terms *punished* acting, and throughput had a dead zone above flow_ratio=0.85 — i.e. the agent had no usable gradient (per the verbatim header docstring of [r44_reward_v4.py:1-46](../../sar_components/rewards/r44_reward_v4.py#L1-L46)).
**Decision:** Five quadratic-penalty terms, ×5 scale, episode returns in roughly [−600, +60]:
| Term | Weight | Computes |
|---|---|---|
| `r_harmo` | 0.35 | Upstream speed variance + per-lane variance at `seg_0_before` |
| `r_temporal` | 0.20 | Downstream speed step-to-step stability |
| `r_throughput` | 0.25 | Continuous flow ratio, no dead zone |
| `r_lane_eq` | 0.15 | Max inter-lane speed gap |
| `r_smoothness` | 0.05 | Action delta L2 norm |
**Consequences:**
- (+) Empirically converged policies (vs reward v3's collapse-to-no-op)
- (+) Per-component breakdown surfaces in eval CSV for KPI translation (RQ5)
- (−) Reward magnitude is project-internal; doesn't translate directly to engineering KPIs (RQ5 work item)
- (−) Weight choice not yet ablated (§2.4 caveat — must add before paper)
**Traceability:** [r44_reward_v4.py:55-178](../../sar_components/rewards/r44_reward_v4.py#L55-L178); weights configured at [per_lane_stochastic.yaml:52-57](../../configurations/per_lane_stochastic.yaml#L52-L57).

### ADR-007 — 30-s aggregation window + 5-frame stack
**Status:** Accepted (v5.0)
**Context:** v4 used 150 s windows on a single observation. Temporal context was implicit (in the env, not the agent).
**Decision:** `aggregation_time = 30 s` per env step; observation stacks 3 frames at `seg_0_before` and 5 frames overall (gives 150 s of temporal context to the agent explicitly).
**Consequences:**
- (+) 5× finer reaction time vs v4
- (+) Explicit temporal context — agent can detect regime transitions, not just steady-state
- (−) 4× more environment steps per episode → 4× larger replay buffer footprint
**Traceability:** `aggregation_time=30` ([per_lane_stochastic.yaml:9](../../configurations/per_lane_stochastic.yaml#L9)), `_STACK_SIZE=3` ([r44_state_v2.py:63](../../sar_components/states/r44_state_v2.py#L63)).

### ADR-008 — 100% CAV penetration for the paper
**Status:** Accepted (2026-05-18, this doc)
**Context:** Initial runs used 50% CAV. For paper-first focus the simplest contribution is 100% CAV (no mixed-traffic compliance variance to model). HDV sensitivity sweep is the natural PhD chapter follow-up.
**Decision:** Paper experiments use `cav_percentage = 100.0`. The current 50% CAV result is a robustness data point; the headline claim is 100% CAV.
**Consequences:**
- (+) Cleanest possible CAV-direct-only formulation
- (+) Eliminates a major reviewer-attack surface ("what about HDV compliance?")
- (−) Less directly deployable today (most fleets ≤ 20% CAV)
- (−) Requires retraining all 5 seeds at 100% CAV before paper submission (P4)
**Action item:** When retraining for the paper, set `cav_percentage = 100.0` in [per_lane_stochastic.yaml:16](../../configurations/per_lane_stochastic.yaml#L16). Do not silently change before then.
**References:** Vinitsky 2018 explicitly characterised 10% AV as the *lower bound* of usefulness; 100% is the upper-bound clean-room case.
**Traceability:** This ADR. Memory record: [project_paper_first_directive.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_paper_first_directive.md).

### ADR-009 — Distributional value head (TQC quantile critic), not distributed multi-agent
**Status:** Accepted (clarification 2026-05-16)
**Context:** Project naming has been ambiguous between *distributional* RL (value-distribution learning) and *distributed* RL (multi-agent / data-parallel).
**Decision:** This project is **distributional RL** — TQC's truncated quantile mixture value head. SubprocVecEnv is data-parallel rollout only, not MARL infrastructure. The intended PhD direction is **cooperative MARL (one TQC per gantry)**, but the paper sticks to centralised single-agent.
**Consequences:**
- (+) Clear scope for the paper — no MARL infrastructure needed
- (+) Distributional angle is paper-tight (TQC + reward distribution analysis)
- (−) The richer "distributed RL" framing waits for PhD
**Traceability:** ADR-003 (TQC choice); memory [project_speed_harmo_v5.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_speed_harmo_v5.md) §"Thesis framing".

### ADR-010 — Safety by construction (no TTC / TET / TIT surrogate term)
**Status:** Accepted (2026-05-18, paper-1 scoping)
**Context:** Lu et al. 2023 (TD3LVSL) and MARVEL both report TTC-based safety surrogates (TET, TIT, CVS). A naive reading of "Paper 1 must add safety surrogates" expands scope beyond the cash-cow contribution.
**Decision:** **Do not introduce a safety surrogate as a reward term or required KPI.** Defend safety *by construction* via two layered guarantees and report empirical evidence:

| Layer | Mechanism | Code reference |
|---|---|---|
| Car-following | SUMO's Krauss model enforces safe following distance per simulation step — vehicles cannot rear-end collide if `decel` and `tau` are within valid ranges (which they are in our fleet definition). The Krauss model has been validated in independent SUMO publications (see ADR-011). | [traffic_environment/vehicle_fleet.py](../../traffic_environment/vehicle_fleet.py) |
| Action smoothness | TraCI `slowDown(veh_id, target_speed, duration)` performs **gradual deceleration** over `duration` seconds, respecting each vehicle's `decel` parameter — not instantaneous teleportation. Our `duration = aggregation_time = 30 s` ([env_interact.py:582](../../core/env_interact.py#L582)) gives every CAV a full 30-second linear ramp to the new target. | [env_interact.py:545-622](../../core/env_interact.py#L545-L622) |

**Consequences:**
- (+) Paper 1 stays tight — no new metric definitions, no TraCI replay pass for TTC computation
- (+) Defense is verifiable, not hand-waved — once the codebase change below is made
- (−) Reviewer can still ask "did you measure collisions?" — we need positive evidence

**Required codebase change (action item — must complete before paper submission):**

The current SUMO launch ([env_interact.py:410-420](../../core/env_interact.py#L410-L420)) uses `--collision.action warn` + `--no-warnings` + stderr → DEVNULL. **This makes collisions silently undetectable.** Without changes, we cannot defend the safety claim with positive evidence.

Proposed change:
```python
# In TrafficMetrics dataclass (env_metrics.py):
collision_count: int = 0   # collisions observed during the episode

# In _advance_sumo (env_interact.py, every SUMO step):
try:
    collided = conn.simulation.getCollidingVehiclesNumber()
    if collided > 0:
        self._metrics.collision_count += collided
except Exception:
    pass

# Persist in evaluation_summary.csv as a new column.
# Report in paper: "0 collisions across 5 seeds × 30 episodes × 11 baselines = 1650 episodes".
```

**Why not change `--collision.action` to `remove`?** Because that *changes the dynamics* (colliding vehicles disappear instead of being detected and counted). Keeping `warn` + polling `getCollidingVehiclesNumber()` is the non-invasive fix.

**Alternatives rejected:**
- Adding a TTC reward term — adds tuning surface, expands scope, MARVEL already shows it's possible but our cash-cow contribution doesn't need it
- Using a different car-following model (e.g. EIDM, Krauss-Orig) — would require revalidation work; default Krauss is the accepted standard for VSL studies in SUMO
- Changing `--collision.action remove` — changes simulation dynamics

**Traceability:** [env_interact.py:410-420](../../core/env_interact.py#L410-L420) (SUMO launch flags), [env_interact.py:545-622](../../core/env_interact.py#L545-L622) (slowDown application). ADR-011 (car-following model validation).

### ADR-011 — SUMO + Krauss car-following defended by SUMO's own publications
**Status:** Accepted (2026-05-18)
**Context:** MARVEL uses commercial TransModeler with I-24-calibrated data. A naive reviewer would demand similar simulator calibration. The user has explicitly rejected investing in custom simulator calibration for Paper 1.
**Decision:** Defend simulator realism via SUMO's own peer-reviewed publication record (5 citations, all from [sumo.dlr.de/docs/Publications.html](https://sumo.dlr.de/docs/Publications.html)):

| # | Citation | Use |
|---|---|---|
| 1 | Lopez P. A., Behrisch M., Bieker-Walz L., Erdmann J., Flötteröd Y.-P., Hilbrich R., Lücken L., Rummel J., Wagner P., Wießner E. (2018). *Microscopic Traffic Simulation using SUMO*. IEEE ITSC. | **Recommended general citation** per SUMO's docs. Cite at first mention of "SUMO". |
| 2 | Krajzewicz D., Hertkorn G., Rössel C., Wagner P. (2002). *SUMO (Simulation of Urban MObility); An open-source traffic simulation*. MESM 2002. | Original software-paper for historical attribution. |
| 3 | Behrisch M., Bieker L., Erdmann J., Krajzewicz D. (2011). *SUMO – Simulation of Urban MObility: An Overview*. SIMUL 2011. | Cites the simulator's design choices including Krauss as default car-following model. |
| 4 | Krajzewicz D. (2002). *An Example of Microscopic Car Models Validation using the open source Traffic Simulation SUMO*. 14th European Simulation Symposium. | **Validation paper** — directly supports the "car-following models are validated" claim in ADR-010. |
| 5 | (To add per submission round) — a recent VSL-in-SUMO paper from `papers_RL_VSL/` corpus | Demonstrates SUMO as the established simulator for VSL studies. |

**Paper paragraph template:** *"We simulate the corridor using SUMO [1], the open-source microscopic traffic simulator whose car-following models (default: Krauss) have been independently validated [4]. SUMO is the established simulator for VSL studies in the recent literature [e.g. Lu et al. 2023, Vinitsky et al. 2018, …]. We deliberately rely on SUMO's default Krauss model rather than introduce a custom calibration step: our contribution is the VSL controller, not the simulator, and reproducibility is best served by sticking to the published default."*

**Consequences:**
- (+) Zero new validation work
- (+) Defense is reproducible (cite-and-move-on)
- (−) Doesn't refute a determined "but real corridor calibration?" reviewer — but that demand pushes Paper 1 toward Paper 3 scope; we decline politely

**Traceability:** SUMO launch flags ([env_interact.py:410-421](../../core/env_interact.py#L410-L421)); fleet definitions ([traffic_environment/vehicle_fleet.py](../../traffic_environment/vehicle_fleet.py)).

### ADR-013 — Ramp-fraction sweep range [0.20, 0.30] justified by breakdown-probability and capacity-drop literature
**Status:** Accepted (2026-05-18)
**Context:** Each scenario in the pool samples `ramp_fraction = V_R / (V_R + V_F)` uniformly from a configurable range ([stochastic_demand.py:37,52,86-87](../../traffic_environment/stochastic_demand.py#L37)). The current band is [0.20, 0.30]. A reviewer will ask whether the bounds are arbitrary or grounded.
**Decision:** **Keep [0.20, 0.30]** with the following bound defense from the project knowledge base (verbatim quotes, three sources):

> **Lorenz & Elefteriadou (TRB Circular E-C018, "A Probabilistic Approach to Defining Freeway Capacity and Breakdown"), p. 91:**
> *"Examining the data points for a one-minute aggregation interval at either site, it is apparent that the breakdown probabilities associated with the various flow rates are rather low (less than 10 percent), even for flow rates exceeding 2,000 vphpl. […] Essentially, the traffic stream is capable of absorbing brief fluctuations in the flow rate — even those above 2,000 vphpl — without resulting in a high risk of breakdown."*
> Same paper, p. 93: *"breakdown was observed to occur over a wide range of flow rates — rates both lower, and higher, than those traditionally associated with capacity — and were sustained for varying lengths of time."* (Site A 15-min P[breakdown] rises from ~5% at 1,550 vphpl to ~45% at 1,850 vphpl; Site B from ~10% at 2,000 vphpl to ~100% at 2,450 vphpl — Figs. 5–6, p. 92.)

> **Chung, Rudjanakanoknad & Cassidy (Transportation Research Part B, 2007, "Relation between traffic density and capacity drop at three freeway bottlenecks"), p. 85 + Table 1, p. 86:**
> *"Discharge flows exhibit considerable variation across days, but the occurrence of a capacity drop is common to all days. […] Drops of at least 10% were the norm."*
> I-805 merge bottleneck: pre-drop discharge 9,200–10,730 vph on a 4-lane freeway with metered on-ramp flow never exceeding 400 vph (≈ 4–4.5% ramp share during the active bottleneck).

> **Han, Yuan, Hegyi et al. (Transportation Research Part C 144, 2022, "A new reinforcement learning-based variable speed limit control approach to improve traffic efficiency against freeway jam waves"), p. 12:**
> *"In general, the free-flow capacities obtained from 100 random online simulation runs ranges from 1900 veh/h/lane to 2100 veh/h/lane. […] The mean of peak hour demands and mean off-peak hour demands are set to 90% of the capacity (which varies in different simulation runs) and 4000 veh/h respectively."*

**Bound defense (computed from the cited quantities):** A 3-lane mainline at 1,900–2,100 veh/h/lane gives free-flow V_F ≈ 5,700–6,300 vph. A ramp_fraction = 0.20 implies V_R ≈ 1,425–1,575 vph and total merge demand ≈ 7,100–7,900 vph; ramp_fraction = 0.30 implies V_R ≈ 2,440–2,700 vph and total ≈ 8,100–9,000 vph. Per Lorenz & Elefteriadou, per-lane flows in this band straddle the 5–45 % breakdown-probability regime at Site A and 10–100 % at Site B — the **"stochastic, controllable" zone** where VSL can plausibly act. Chung et al. show I-805 capacity drops trigger at 9,200–10,730 vph total flow with <5 % ramp share, so applying our 20–30 % range to a smaller mainline reproduces the same merge-stress envelope without driving the system into the permanent-breakdown tail observed above ≈ 2,450 vphpl. The lower bound (0.20) ensures every scenario reaches the threshold where Han et al. train RL controllers (≈ 90 % free-flow capacity); the upper bound (0.30) stays inside the band where capacity drop is probabilistic rather than guaranteed.

**Consequences:**
- (+) Sweep is defensible without new simulation work — three peer-reviewed citations bracket the chosen range
- (+) Reviewers can verify the math (V_F = lanes × per-lane capacity; V_R = ramp_fraction × total)
- (+) Already implemented and tested — the existing pool covers this band correctly
- (−) Does not exercise the under-stressed regime (ramp_fraction < 0.20) or the over-stressed regime (> 0.30) — flagged as **Paper 2 demand-sensitivity hook** in §3 / ADR-012

**Alternatives rejected:**
- Widening to [0.10, 0.35] — pushes the sweep into regimes where (a) VSL provides no benefit (low end) or (b) deterministic breakdown overwhelms any controller (high end), making the contribution noisier rather than stronger
- Fixed ramp_fraction (single value) — eliminates demand-pattern robustness, weaker than current
- Deferring the sweep entirely to Paper 2 — would remove an existing strength of Paper 1

**Paper paragraph template** (ready to drop into §Methods/Demand):
> *"Scenario demand is parameterised by the ramp-fraction `r = V_R / (V_R + V_F)`, sampled uniformly on [0.20, 0.30]. The lower bound is chosen so that total merge demand reaches approximately 90 % of free-flow capacity, matching the training regime adopted by Han et al. (2022, p. 12) for jam-wave VSL control on a comparable 3-lane stretch with 1,900–2,100 veh/h/lane free-flow capacity. The upper bound is constrained by the probabilistic breakdown curves of Lorenz and Elefteriadou (TRB Circular E-C018, pp. 91–93, Figs. 5–6): beyond this range, 15-minute breakdown probability exceeds ≈ 50 % per lane, leaving no controllable margin for VSL to recover free-flow operation. The chosen window therefore brackets the 'stochastic capacity' regime in which capacity drops at merge bottlenecks — empirically 10 % or more on Interstate 805 (Chung, Rudjanakanoknad and Cassidy, 2007, Table 1, p. 86) — are likely but not deterministic, which is precisely the operating regime against which any VSL strategy must be benchmarked."*

**References:**
- Lorenz, M. R. & Elefteriadou, L. *A Probabilistic Approach to Defining Freeway Capacity and Breakdown*. TRB Circular E-C018, pp. 84–95. Knowledge base: [papers_DistRL/A Probabilistic Approach to Defining Freeway Capacity and Breakdown.pdf](../knowledge_base/papers_DistRL/A%20Probabilistic%20Approach%20to%20Defining%20Freeway%20Capacity%20and%20Breakdown.pdf).
- Chung, K., Rudjanakanoknad, J. & Cassidy, M. J. (2007). *Relation between traffic density and capacity drop at three freeway bottlenecks*. Transportation Research Part B 41 (1), pp. 82–95. Knowledge base: [papers_DistRL/Relation between traffic density and capacity drop at three freeway bottlenecks.pdf](../knowledge_base/papers_DistRL/Relation%20between%20traffic%20density%20and%20capacity%20drop%20at%20three%20freeway%20bottlenecks.pdf).
- Han, Y., Yuan, K., Hegyi, A. et al. (2022). *A new reinforcement learning-based variable speed limit control approach to improve traffic efficiency against freeway jam waves*. Transportation Research Part C 144. Knowledge base: [papers_RL_VSL/A new reinforcement learning-based variable speed limit control approach...pdf](../knowledge_base/papers_RL_VSL/A%20new%20reinforcement%20learning-based%20variable%20speed%20limit%20control%20approach%20to%20improve%20traffic%20efficiency%20against%20freeway%20jam%20waves.pdf).
- HCM 6th ed. (cited *secondarily* via Lorenz & Elefteriadou p. 84, 89). Add a direct HCM citation to the paper bibliography if reviewers demand the primary source.

**Traceability:** `ramp_fraction_range` config ([per_lane_stochastic.yaml:21](../../configurations/per_lane_stochastic.yaml#L21)), sampling logic ([stochastic_demand.py:37,52,86-87](../../traffic_environment/stochastic_demand.py#L37)), pool generation ([generate_scenarios.py](../../generate_scenarios.py)).

### ADR-014 — Pure CAV-direct VSL is a methodological necessity, not a design preference
**Status:** Accepted (2026-05-18)
**Context:** ADR-001 motivated CAV-direct VSL primarily via HDV compliance variance — a reviewer can rebut this by pointing to enforcement-instrumented schemes that achieve high compliance. A separate, stronger argument exists from the side of action-space topology: a continuous-valued VSL action is **fundamentally incompatible with posted (roadside) display**, and this incompatibility holds even at 100 % driver compliance. This ADR documents that argument explicitly so it survives the PhD thesis and any subsequent paper derived from this codebase.
**Decision:** The DRL controller is **CAV-direct-only by methodological necessity**. Hybrid CAV-direct / posted designs are out of scope for any paper derived from this codebase. Static posted *baselines* remain in scope as comparison points (NC, M110_uniform, diff_mild) because they are inherently discrete and uniform — they do not face the continuous-action / discrete-display incompatibility.

**Four-argument defense:**

1. **Regulatory.** Posted VSL signs are legally restricted to discrete increments. The MUTCD §2B.13 (US) and equivalent EU national codes (e.g. Dutch RVV 1990, German StVO §41) specify VSL signs in fixed steps — typically 5 mph or 10 km/h. A continuous-valued posting (e.g. 76.4 km/h) is not a legally valid speed limit in any jurisdiction we are aware of.

2. **Display hardware.** Variable Message Sign hardware physically renders speed limits digit-by-digit via LED panels. Sub-unit precision is not displayable. **This argument is independent of regulation and of compliance — it is a physical constraint of the sign itself.**

3. **Cognition + compliance.** Drivers perceive posted limits in coarse psychophysical bins (~5–10 km/h), so even a hypothetical continuous display would be perceptually quantized. Compliance varies sharply with enforcement: uninstrumented posting typically achieves 60–80 % compliance in HDV fleets, while enforcement-instrumented schemes — average-speed cameras with license-plate recognition (e.g. UK *SPECS*, Dutch *trajectcontrole*, Italian *SICVe / Tutor*) — reportedly raise this toward ~95 % per national-level reports (citations to be added at submission time; a general acknowledgement is sufficient for the present scope per the cash-cow scope discipline of ADR-012). **Critically, compliance level is independent of the display constraint:** even at 100 % compliance, argument #2 still rules out continuous-valued postings — the driver cannot obey what the sign cannot show.

4. **Empirical (Box(5) ablation).** The codebase implements an attempted CAV-direct / posted hybrid in Box(5): the action vector includes a `seg_1_before_physical` field ([r44_action_v2.py:189-193](../../sar_components/actions/r44_action_v2.py#L189-L193)) applied via `conn.edge.setMaxSpeed("seg_1_before", v)` ([env_interact.py:499-503](../../core/env_interact.py#L499-L503)), which alters the edge-wide max speed for all vehicles. TQC Box(5) **underperforms** pure CAV-direct TQC Box(4) by ~14 reward points (−335 vs −321, mean across 5 seeds × 30 held-out episodes; `training_runs/experiment_20260516_094738/` vs `training_runs/experiment_20260516_095542/`). Real-world deployment of Box(5) would *further* require quantizing the continuous `seg_1_before_physical` value at display time, eroding the result still further.

5. **Information-theoretic (collapses the contribution).** Hybrid mode forces a single posted sign to summarise the per-lane action vector `[L0, L1, L2]`. Any single posted scalar destroys the lane-differential — which is the load-bearing novelty of ADR-004. Equivalently: per-lane CAV-direct VSL and uniform-posted VSL are not composable; either one alone is internally consistent, but mixing them sacrifices the per-lane signal at the display boundary.

**Consequences:**
- (+) Frames pure CAV-direct VSL as a *deliberate methodological commitment*, not a limitation
- (+) Insulates Paper 1 / Paper 2 / PhD from "why not hybrid?" reviewer attacks — the answer is "see ADR-014; the action space is not posted-deployable regardless of how strictly drivers comply"
- (+) Connects ADR-001 (CAV-direct context), ADR-003 (continuous action), ADR-004 (Box(4) primary) in a single defensible thesis
- (+) Compliance literature can be expanded into a dedicated PhD-chapter sub-section if reviewers demand it — the present plan keeps a general acknowledgement only, per ADR-012 scope discipline
- (−) Forecloses any future paper claiming to extend the controller with a discrete posted sign — but ADR-012 already commits to pure CAV-direct descendants for Papers 2 and 3

**Alternatives rejected:**
- Hybrid with action quantization at display time — see arguments #4 and #5 above
- Reformulating the action space as discrete to enable posted-sign deployment — destroys ADR-003 motivation (continuous + distributional TQC) and ADR-004 motivation (per-lane differential)

**Action items:**
- Before paper submission: collect national-level enforcement-compliance citations to instantiate argument #3 (UK SPECS, Dutch *trajectcontrole*, Italian *SICVe* — at least one peer-reviewed report per scheme). General statement suffices for plan v0.4; specific citations land in the paper bibliography.

**Traceability:** ADR-001 (CAV-direct context), ADR-003 (continuous action), ADR-004 (Box(4) primary + Box(5) ablation note); Box(5) hybrid implementation in [r44_action_v2.py:189-193](../../sar_components/actions/r44_action_v2.py#L189-L193) and [env_interact.py:499-503](../../core/env_interact.py#L499-L503); empirical evidence in evaluation results of `experiment_20260516_094738` (Box(4)) vs `experiment_20260516_095542` (Box(5)).

### ADR-012 — Cash-cow scope discipline (one contribution per paper)
**Status:** Accepted (2026-05-18)
**Context:** 5 years on the DQN line yielded no positive publication. The user is choosing scope discipline over breadth. Each subsequent paper must reuse this codebase but explore exactly one additional slice.
**Decision:** Build the PhD around **one cash cow** (TQC + per-lane CAV-direct VSL) and derive 2–3 concise papers + the thesis from it.

| Output | Contribution slice | What it reuses | What it adds |
|---|---|---|---|
| **Paper 1** (current) | TQC + per-lane CAV-direct VSL on a ramp interchange under stochastic anomaly demand vs static posted baselines | — | The cash-cow result |
| **Paper 2** (next, optional) | Active CAV-direct baseline sweep: when does aggressive static control beat learning? | Codebase + eval CSV | 6-point M*_active sweep analysis + decision-rule for static-vs-learned regime |
| **Paper 3** (later) | Apples-to-apples vs other DRL / MPC / hybrid systems | Codebase + eval harness | External comparator implementations (ALINEA, SPECIALIST, MPC-VSL) |
| **PhD thesis** | Aggregates Papers 1–3 + HDV sensitivity sweep + multi-topology generalisation + MARL extension | All of the above | Synthesis chapter + 2 new chapters (HDV sweep, MARL) |

**Consequences:**
- (+) Each paper is short, reviewable, and rejection-resilient (failure of one doesn't sink the PhD)
- (+) Reviewer comments demanding broader scope can be answered "addressed in Paper N (in prep)" without rewriting Paper 1
- (−) The thesis cannot claim a single overarching contribution; the synthesis chapter must do that work explicitly
**Traceability:** Memory [project_cash_cow_scope_discipline.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_cash_cow_scope_discipline.md); §3 timeline; §2.3 contribution claims explicitly mark which paper each claim belongs to.

---

## 5. System architecture

### 5.1 Module map

```
phd_speed_harmo_v5/
├── core/                              ← stable interface layer
│   ├── env_interact.py                  TrafficEnv: gymnasium.Env wrapping SUMO via TraCI
│   ├── sar_frame.py                     ABCs + factory functions for SAR plugins
│   ├── regime_detector.py               FREE_FLOW / METASTABLE / CONGESTED classifier
│   ├── env_metrics.py                   TrafficMetrics dataclass
│   └── constants.py                     MAX_SPEED_KPH and step/action limits
├── sar_components/                    ← pluggable MDP definitions (auto-discovered)
│   ├── states/                          r44_state_v* — observation builders
│   ├── actions/                         r44_action_v* — action → speed-limits dict
│   ├── rewards/                         r44_reward_v* — TrafficMetrics → RewardSignal
│   ├── registry.py                      decorator-based registration
│   └── discovery.py                     glob-import on first use
├── traffic_environment/               ← traffic-side machinery
│   ├── sumo/ramps_v*.net.xml            network geometry
│   ├── scenario_generator.py            paired (route, sumocfg) builder
│   ├── stochastic_demand.py             gamma-shaped demand profiles
│   ├── vehicle_fleet.py                 vehicle types + CAV / HDV mix
│   ├── scenario_pool.py                 pre-generated scenario manager
│   └── anomaly_injector.py              ramp_spike / speed_reduction / lane_closure
├── train.py                           ← SAC / TQC training, SubprocVecEnv, callbacks
├── evaluate_models.py                 ← held-out 30-ep eval, baselines vs trained
├── generate_scenarios.py              ← CLI for scenario pool generation
├── deploy_remote.sh                   ← bootstrap one vast.ai VM
├── deploy_4vm.sh                      ← per-VM dispatcher (1 / 2 / 3 / 4 selects algorithm)
├── launch_training.sh                 ← config-aware training entrypoint
├── launch_evaluation.sh               ← config-aware evaluation entrypoint
├── configurations/                    ← YAML configs (per_lane_stochastic.yaml)
├── tests/                             ← pytest suite + smoke tests
└── docs/                              ← this folder
    ├── plans/                           strategic docs (this file)
    └── knowledge_base/                  curated literature PDFs (gitignored)
```

### 5.2 SAR plugin registry — the central abstraction

Every MDP component is a plugin discovered by [`sar_components/discovery.py`](../../sar_components/discovery.py) at first use. The interface is defined in [`core/sar_frame.py`](../../core/sar_frame.py):

```
StateRepresentation  →  get_observation_space() + build_state(metrics, ...) + preprocess_state()
ActionStrategy       →  get_action_space()      + apply_action(action, metrics)
RewardFunction       →  calculate(metrics, ...) → RewardSignal(total, components)
```

A YAML config names the plugin variants ([per_lane_stochastic.yaml:30-33](../../configurations/per_lane_stochastic.yaml#L30-L33)); the factory functions in `sar_frame.py` instantiate them. This design allows **swapping reward functions or action spaces without touching `TrafficEnv`**, which is the load-bearing pattern that lets us version reward implementations (v1 → v4 currently).

### 5.3 Data flow (one training step)

```
SubprocVecEnv (N = 48 workers)
   │
   ▼
TrafficEnv.step(action)
   ├── action_strat.apply_action(...) → {seg_id: speed_limit_ms}
   ├── _advance_sumo(n_steps = 30)    → 30 × simulationStep + slowDown() every 5 steps
   ├── _collect_metrics()             → reads E1 detectors → TrafficMetrics
   ├── state_repr.build_state(metrics) → 77-d obs
   └── reward_func.calculate(metrics)  → RewardSignal(total, components)
   ▼
SB3 Replay Buffer  (500k transitions)
   ▼
TQC.train()  → gradient updates on actor + 5 critics × 25 quantiles
   ▼
EvalCallback (every 50k steps)  +  CheckpointCallback (every 50k steps)
   +  RewardComponentsCallback   → writes reward_components/* scalars to TensorBoard
```

---

## 6. DRL formulation

### 6.1 MDP definition

| Element | Definition |
|---|---|
| State *S* | 77-d vector: 3-frame stack × 24 features (per-segment + per-lane speed/flow/occ, regime one-hot) + 5 static (prev 4-D action + anomaly flag). See [r44_state_v2.py](../../sar_components/states/r44_state_v2.py). |
| Action *A* | Box(4) continuous ∈ ℝ⁴: `[L0_VSL_kph, L1_VSL_kph, L2_VSL_kph, ramp_VSL_kph]`. Bounds: lanes [60, 120], ramp [40, 90]. MUTCD-clipped post-policy. |
| Reward *R* | 5-term quadratic; see ADR-006. |
| Transition *P* | SUMO 1.21+ simulation, ballistic step method, 30 s aggregation window. |
| Episode horizon | 3600 sim seconds = 120 env steps. |
| Discount γ | 0.99 |

### 6.2 Algorithm choices

| Role | Algorithm | Rationale |
|---|---|---|
| Primary | **TQC** | Distributional value head reduces overestimation under noisy reward; 5 critics × 25 quantiles; top-2 dropped per critic. Methodologically supersedes TD3LVSL (Lu 2023). |
| Baseline | SAC | Same actor architecture, standard 2-critic; for ablation of "did distributional help?" |
| POMDP-safe | RecurrentPPO | Reserved if observability proves insufficient; not pursued in v5.1. |

Hyperparameters (paper-fixed unless ablation noted): [per_lane_stochastic.yaml:77-91](../../configurations/per_lane_stochastic.yaml#L77-L91). LR 3e-4, batch 256, buffer 500k, target entropy auto, net_arch [256, 256].

### 6.3 Training infrastructure

- **SubprocVecEnv N = 48** per seed → 5 seeds in parallel per VM = **240 SUMO processes** per VM.
- 1M total timesteps per seed (~9.5 h wallclock on EPYC 7B13 Milan; see [project_vm_hardware_profile_20260516.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_vm_hardware_profile_20260516.md)).
- Auto-save: CheckpointCallback every 50k steps; EvalCallback every 50k steps (10 deterministic eval episodes).
- `RewardComponentsCallback` pushes per-term reward to TensorBoard at every step ([train.py:159-178](../../train.py#L159-L178)).
- Seeds clamped to uint32 via `_seed_u32()` ([train.py:52-54](../../train.py#L52-L54)) to prevent NumPy RandomState overflow.

---

## 7. Network & traffic model

### 7.1 Topology

`ramps_v0` / `ramps_v2` — 3-lane mainline → 4-lane weaving buffer (250 m, on-ramp acceleration lane L0) → 3-lane downstream. On-ramp and off-ramp flank the weave. See [traffic_environment/sumo/ramps_v0.net.xml](../../traffic_environment/sumo/ramps_v0.net.xml).

### 7.2 Detector inventory

48 × E1 induction loops + 5 × E3 multi-entry-exit, all at 30-s frequency. Detector IDs follow `flow_loop_{seg}_{lane}_{pos}` and `e3_seg_*` patterns. See [traffic_environment/sumo/detectors_ramps_v0.add.xml](../../traffic_environment/sumo/detectors_ramps_v0.add.xml).

### 7.3 Vehicle fleet

Defined in [traffic_environment/vehicle_fleet.py](../../traffic_environment/vehicle_fleet.py). 140 vehicle types across 3 compliance groups (HDV nominal, HDV reckless, CAV). Per ADR-008 the paper uses **100% CAV** (HDV variants present in the fleet but not spawned).

### 7.4 Demand profile

Stochastic gamma-shaped peaks: peak ∈ [5500, 8000] vph, ramp fraction ∈ [0.20, 0.30], peak time ∈ [0.15, 0.30] of episode, decay ∈ [0.65, 0.80]. Noise std 0.05. See [traffic_environment/stochastic_demand.py](../../traffic_environment/stochastic_demand.py) and [per_lane_stochastic.yaml:17-24](../../configurations/per_lane_stochastic.yaml#L17-L24).

### 7.5 Anomaly injection

Per-episode probability 0.15. Three types ([traffic_environment/anomaly_injector.py](../../traffic_environment/anomaly_injector.py)):
- `ramp_spike` — sudden ramp demand surge
- `speed_reduction` — temporary speed-limit drop on a mainline segment (weather analog)
- `lane_closure` — temporary lane closure on a mainline segment

Anomaly start time and duration randomised. The agent receives a binary `anomaly_active` flag in its observation.

---

## 8. Evaluation methodology

### 8.1 Baselines (11 total)

Implemented in [evaluate_models.py:520-553](../../evaluate_models.py#L520-L553):

| Class | Policy | Description |
|---|---|---|
| Null | NC | Free-flow limits everywhere — *the agent must beat this to have learned anything* |
| Static posted | M110_uniform | Best uniform VSL from the Phase 3 feasibility sweep |
| Static posted | diff_mild | Best hand-tuned per-lane differential from Phase 3 |
| Active CAV-direct | M{60,70,80,90,100,110}_active | Uniform CAV slowDown to {60..110} kph only during METASTABLE; otherwise NC |
| Active CAV-direct | diff_mild_active | Differential (105/110/115/70) during METASTABLE |
| Active CAV-direct | diff_aggressive_active | Differential (80/90/100/55) during METASTABLE |

**Why the M\*_active set matters:** these are the *strongest possible rule-based baselines* — they do exactly what the DRL does (CAV-direct slowDown during METASTABLE only) but with hand-tuned fixed limits and no per-lane differentiation. Beating these is the real bar. **No prior paper in the corpus compares against an active CAV-direct sweep this exhaustive.**

### 8.2 Held-out evaluation protocol

- **30 episodes** per policy (deterministic models, same scenario seeds across policies for fair comparison)
- **Stochastic demand** + **15 % anomaly probability** — same distribution as training
- **5 parallel workers** per experiment
- Output: `evaluation_summary.csv` (per-episode), `trajectories.json` (per-step), aggregated reward table + anomaly breakdown + reward-component breakdown in the run log

### 8.3 Metrics — current

The reward components in `evaluation_summary.csv`:
- `total_reward`, `avg_rc_harmonization`, `avg_rc_lane_sigma`, `avg_rc_segment_sigma`, `avg_rc_temporal`, `avg_rc_throughput`, `avg_rc_flow_ratio`, `avg_rc_lane_equalisation`, `avg_rc_max_lane_diff_kph`, `avg_rc_smoothness`, `avg_rc_raw_unscaled`
- Plus traffic-side: `avg_ds_flow_vph`, `avg_merge_speed_kph`, `avg_L0_speed_kph`, `avg_L2_speed_kph`, `L0_L2_speed_delta`, `action_L*_mean`, `action_L*_std`, `peak_demand_vph`, `ramp_fraction`, `anomaly_type`, `anomaly_start_s`.

### 8.4 Metrics — KPIs for the CAV-direct VSL contribution (RQ3)

Per ADR-010 and ADR-012, Paper 1 reports KPIs **specific to CAV-direct VSL effectiveness** rather than generic traffic-engineering safety surrogates. All KPIs below are derivable from existing `evaluation_summary.csv` + `trajectories.json` — **no new SUMO runs required for the KPI translation itself**. The reward-weight ablation (P3) and the safety-by-construction collision count (ADR-010) do require new runs.

| # | KPI | What it shows | Source columns |
|---|---|---|---|
| 1 | **Mean reward gain vs NC** | Headline effectiveness | `total_reward` (mean over 30 episodes), compute Δ vs NC |
| 2 | **Throughput preservation** | DRL doesn't sacrifice flow for harmonization | `avg_ds_flow_vph` / `NC_avg_ds_flow_vph` |
| 3 | **Lane-speed harmonization (σ_lane)** | Direct mechanism for the reward gain | `avg_rc_lane_sigma` |
| 4 | **Lane-speed differential collapse** | Per-lane action's payoff | `avg_rc_max_lane_diff_kph` |
| 5 | **Bottleneck speed recovery at peak demand** | Effect at the most-stressed condition | `avg_merge_speed_kph` filtered to `peak_demand_vph > 7000` |
| 6 | **CAV control authority (action std)** | Policy actively reacts, not constant | `action_L0_std`, `action_L1_std`, `action_L2_std`, `action_ramp_std` |
| 7 | **Per-lane differential utilization** | Quantifies the per-lane action novelty | Fraction of steps where `\|L0_action − L2_action\| > 10 kph` (from trajectories.json) |
| 8 | **Anomaly robustness Δ** | Generalisation under stochastic events | `mean_reward(anomaly_episodes) − mean_reward(normal_episodes)` per policy |
| 9 | **Collision count** (safety-by-construction evidence) | Positive evidence for ADR-010 | new column once ADR-010's codebase change lands |
| 10 | **Reward-component decomposition** | What is the agent actually optimising? | All `avg_rc_*` columns, normalized by NC equivalents |

**Reporting style** (paper-tight):
- Headline = KPIs 1, 3, 9. One table, three numbers per policy.
- Mechanism evidence = KPIs 2, 4, 5, 10. One radar/spider chart per algorithm.
- Robustness = KPIs 6, 7, 8. One table per algorithm.
- **Demand-regime robustness** (cheap add): bin the 30 eval episodes by `ramp_fraction` quartile (already in `evaluation_summary.csv` per ADR-013) and report KPI 1 per quartile to show the policy doesn't degrade across the [0.20, 0.30] sweep. One small plot.

**Action items:**
- P1: Implement `tools/eval_to_kpi.py` to compute KPIs 1–8 + 10 from existing artifacts (no new runs).
- P1: Land the ADR-010 codebase change for collision counting (KPI 9).
- P2: Reward-weight ablation (5 retrains, drop-one-term-at-a-time) — strengthens the harmonization-mechanism claim of KPI 10.

**Explicitly NOT in this list (and why):**
- ~~TTS / TET / TIT / CVS~~ — these are *generic* traffic-engineering / safety-surrogate metrics that belong to Lu's and MARVEL's contribution slices, not ours. Adding them expands Paper 1 beyond cash-cow scope. CVS is trivial to compute (`σ/μ` from existing columns) so we include it in passing only if a reviewer asks; we do not lead with it.
- ~~MUTCD step-down violation count~~ — partially relevant; report as a paragraph, not a headline KPI.
- ~~Convergence wallclock~~ — reproducibility metadata (already in [project_vm_hardware_profile_20260516.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_vm_hardware_profile_20260516.md)), not a contribution KPI.

---

### 8.5 Results to date (2026-05-19 — 100 % CAV headline + 4-config reward-weight ablation)

Four training runs at **100 % CAV** evaluated on the shared scenario pool (seed=42, n=200, ramp_fraction ∈ [0.20, 0.30]) with 30 held-out episodes each. **Paper does not yet exist** — this section is a running log of verified results used to inform the eventual paper draft.

| Config | Experiment dir | w_h | w_t | w_q | w_l | w_s | Seeds | Status |
|---|---|---|---|---|---|---|---|---|
| **base** (headline) | `experiment_20260518_133246` | 0.35 | 0.20 | 0.25 | 0.15 | 0.05 | 5/5 | ✅ |
| **harmo_pure** (ablation ii) | `experiment_20260518_133504` | 0.70 | 0.00 | 0.00 | 0.30 | 0.00 | 5/5 | ✅ |
| **no_throughput** (ablation iii) | `experiment_20260518_142808` | 0.47 | 0.27 | 0.00 | 0.20 | 0.06 | 3/5 | ⚠ partial |
| **no_smoothness** (ablation i) | `experiment_20260518_144123` | 0.37 | 0.21 | 0.26 | 0.16 | 0.00 | 5/5 | ✅ |

#### 8.5.1 Physical KPIs (reward-independent — apples-to-apples across configs)

| Config | `lane_sigma` | `max_ldiff_kph` | `ds_flow_vph` | `action_L0_std` | `L0-L2_diff_kph` | **Collisions** |
|---|---|---|---|---|---|---|
| **base** | **1.61** 🥇 | **3.29** 🥇 | 4 657 | 10.27 | +3.47 | **0** |
| no_smoothness | 1.62 | 3.31 | 4 652 | 9.52 | +3.60 | 0 |
| harmo_pure | 1.75 | 3.45 | 4 662 | 10.88 | +4.15 | 0 |
| no_throughput | 1.77 | 3.55 | 4 662 | 9.66 | +3.95 | 0 |

🥇 = best across configs. Base achieves both the tightest lane variance and the lowest max-lane-differential, at parity throughput, with zero collisions.

#### 8.5.2 Within-config reward gap over baselines (the right comparison — see §2.4 caveat row)

Within each config the reward yardstick is consistent between the trained agent and the baselines, so within-config gaps ARE meaningful. M60_active is the strongest static baseline in every config (the strongest CAV-direct rule-based comparator from §8.1).

| Config | DRL mean reward | DRL best seed | DRL worst seed | Seed spread | vs M60_active | vs M110_uniform | vs NC |
|---|---|---|---|---|---|---|---|
| **base** | −164.8 | −155.9 | −172.5 | **16.6** 🥇 | **+40.1** | +174.4 | +221.4 |
| no_smoothness | −172.9 | −167.6 | −179.1 | 11.5 | +40.7 | +185.4 | +235.1 |
| no_throughput | −182.6 | −175.3 | −196.3 | 21.0 (3 seeds) | +46.9 | +228.2 | +289.7 |
| harmo_pure | −196.6 | −169.9 | −238.4 | **68.5** ⚠ | +54.7 | +279.9 | +366.4 |

🥇 = tightest seed-to-seed spread (most stable training). ⚠ = pathological seed variance.

#### 8.5.3 Headline 50 % → 100 % CAV uplift (base config, same scenario pool, same reward weights)

| Metric | 50 % CAV (May-16 4-VM run) | **100 % CAV (May-18, `experiment_20260518_133246`)** | Δ |
|---|---|---|---|
| Mean reward (5 seeds × 30 eps) | −321 | **−164.8** | +156 |
| `lane_sigma` | ~14 | **1.61** | 10× tighter |
| `max_lane_diff_kph` | ~26 | **3.29** | 8× tighter |
| `ds_flow_vph` | ~4 078 | **4 657** | +579 (+14 %) |
| Collisions (eval) | not measured | **0 / 150 episodes** | empirical safety |

The 100 % CAV result is qualitatively different from 50 % CAV. Confirms ADR-008 (100 % CAV is the right paper scope) and ADR-014 (the controller's contribution shows fully when CAV-direct control authority is uncompromised).

#### 8.5.4 Cross-config reward-yardstick caveat (worked example)

When reward weights change, the same physical scenario yields a different reward number — because the reward *function* itself is different. Concrete: in `experiment_20260518_133504` (harmo_pure), the NC baseline scores **−562.9** because harmo_pure weights `w_h=0.70` doubles the harmonization penalty per step. In the base config, NC scores **−386.2**. NC's *physical* behaviour is identical in both runs (same scenarios, same simulator, no control); only the reward yardstick changed.

**Therefore:**
- ❌ Wrong: compare base agent (−164.8) with harmo_pure agent (−196.6) and conclude "harmo_pure is worse by 32 reward points"
- ✅ Right (option A): compare within-config gap-over-baselines — base agent is +40.1 above M60_active under its own yardstick; harmo_pure agent is +54.7 above M60_active under *its* yardstick
- ✅ Right (option B): compare reward-independent physical KPIs (table in §8.5.1) — base achieves the tightest lane_sigma (1.61 vs 1.75 for harmo_pure), and harmo_pure shows 4× higher seed variance

The paper must report ablation results using physical KPIs (option B) or within-config gaps (option A), never raw cross-config reward differences.

#### 8.5.5 Reward-design conclusions (informing the paper's ablation narrative)

1. **Base 5-term reward is the right choice.** Best lane_sigma, best max_lane_diff, lowest seed variance (16.6 — half of harmo_pure's 68.5). Comparable throughput. The five terms are mutually reinforcing.
2. **Dropping `w_s` (smoothness) is near-free** (lane_sigma 1.62 vs 1.61). Smoothness is decorative for the asymptotic policy but its absence does not destabilise training. Defensible to keep for completeness; not worth fighting to remove.
3. **Dropping `w_q` (throughput) preserves throughput in practice** (4 662 vs 4 657 vph — within noise) but degrades lane_sigma by ~10 % (1.77 vs 1.61). The throughput term is **not load-bearing for the throughput KPI** — it's contributing to harmonization stability. Directly answers the standard reviewer challenge ("why a throughput term at all?").
4. **harmo_pure (drop temporal + throughput + smoothness)** explodes seed variance (68.5 vs base 16.6) without improving physical KPIs. The 3 dropped terms are doing *regularisation* work beyond their face-value contribution to the reward.
5. **Per-lane behaviour is genuinely exercised** (action_L0_std ≈ 9–11 kph, L0-L2 differential ≈ +3.5 to +4.2 kph). The agent is not collapsing to uniform-per-segment control — confirms ADR-004's claim.
6. **Safety-by-construction is empirically verified** (0 / 660 eval episodes across all configs). ADR-010 evidence is now in hand.

#### 8.5.6 Open follow-ups (for tools/eval_to_kpi.py and Paper-2)

- **Re-extend `no_throughput` to 5 seeds** when a cheap VM is available — the 3-seed partial is informative but a 5-seed run tightens the conclusion about the throughput term.
- **Anomaly breakdown** at 100 % CAV is not yet computed — the eval CSVs have the data (`anomaly_type` column), the breakdown can be derived without rerunning. Sits in `tools/eval_to_kpi.py` (P2).
- **CVS metric** (MARVEL's safety surrogate) is trivial to add (`lane_sigma / mean_speed`) from the existing CSV columns. Include if a reviewer asks; not lead-with material per §8.4.

---

## 9. Open questions / risks

| ID | Question / Risk | Mitigation |
|---|---|---|
| R-1 | Reward function is project-internal — no published baseline | RQ5 KPI translation, §11-fixed KPI list |
| R-2 | Single topology — generalisation untested | PhD extension; flag as future work |
| R-3 | 100 % CAV unrealistic for near-term deployment | ADR-008 acknowledges; PhD chapter does HDV sensitivity sweep |
| R-4 | Reward weights chosen by hand | Reward-weight ablation (P3); MARVEL admits same on p. 162002 |
| R-5 | Reward components may not be statistically separable | **Mitigated 2026-05-19**: 4-config ablation (§8.5) confirms physical KPIs move coherently with reward changes; base config has 16.6-point seed spread (tight, easily separable from baselines whose spread is ≤ 30) |
| R-6 | Vast.ai auto-shutdown unreliable | `vastai stop instance` workaround documented in [project_vast_ai_shutdown_gotcha.md](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/project_vast_ai_shutdown_gotcha.md) |
| R-7 | SUMO realism may be challenged | ADR-011 — defend by SUMO's own citations + position calibration as out-of-scope per ADR-012 |
| R-8 | Safety claim unverifiable today (SUMO `--collision.action warn` + suppressed warnings) | **Mitigated 2026-05-19**: ADR-010 codebase change landed, 0 / 660 evaluation episodes confirmed (§8.5). Safety-by-construction is now empirically verified, not just theoretical. |
| R-9 | Reward-yardstick incomparability across reward-weight ablations | **Surfaced 2026-05-19 §8.5.4**: documented in §2.4 caveats and §8.5; paper must report physical KPIs or within-config gaps, never raw cross-config reward differences |

---

## 10. Reproducibility checklist

For paper submission:
- [x] Seed list documented (5 seeds: 0, 1, 2, 3, 4); no_throughput is 3 seeds — re-extend before submission
- [x] Hyperparameter snapshot per run (`config.yaml` saved alongside model — verified for the 2026-05-18 runs)
- [x] Scenario pool deterministic from seed 42 + cav=100 (`scenario_pools/shared_seed42_n200_cav100/`)
- [x] Train + eval scripts versioned in git
- [x] Trained models + checkpoints archivable (~400 MB per VM)
- [x] TensorBoard event files preserved for per-component curves (`RewardComponentsCallback` writes 10 scalars per seed; verified in `experiment_20260517_174654` and later runs)
- [x] SUMO version pinned (≥ 1.21)
- [x] Python env via `requirements.txt` + `python 3.12`
- [x] Safety-by-construction empirically verified (0 / 660 episodes — §8.5)
- [ ] no_throughput ablation extended from 3 → 5 seeds (when a cheap VM is available — see §8.5.6)
- [ ] tools/eval_to_kpi.py implemented (anomaly breakdown, CVS, paper-ready KPI tables — see P2 in §3)
- [ ] National-level enforcement-compliance citations added (UK SPECS / Dutch trajectcontrole / Italian SICVe — per ADR-014 action item)

---

## 11. Prior art positioning (lit comparison, 2026-05-18)

Verbatim-quote-grounded comparison vs. the three closest papers in [docs/knowledge_base/](../knowledge_base/). All quotes traceable to PDF pages.

### 11.1 Side-by-side comparison table

| Dimension | Lu 2023 — TD3LVSL | Vinitsky 2018 | Zhang 2024 — MARVEL | **Our work** |
|---|---|---|---|---|
| **Algorithm** | TD3 (2 critics) | TRPO + GRU(64) | MAPPO, MLP [64,64] × 2 | **TQC, 5 critics × 25 quantiles, MLP [256,256]** |
| **Action space** | Discrete 7 / lane-cell, n = I × J ≤ 12 cells | Continuous per-lane Δv ∈ [−1.5, 1.0] m/s² for AVs | Discrete {30, 40, 50, 60, 70} mph / gantry | **Continuous Box(4): 3 lane-VSL [60-120 kph] + 1 ramp-VSL [40-90 kph]** |
| **Control mechanism** | Posted (sign-based) — *their term: Eulerian* | **CAV-direct** (AV speed cap) — *their term: Lagrangian* | Posted (gantries) — *their term: Eulerian* | **CAV-direct** (`traci.slowDown` on CAVs every 5 steps) |
| **Topology** | SR-91 bottleneck, 4 lanes, 2 on-ramps, SUMO | SF-Oakland Bay Bridge, 4→2→1 zipper, SUMO/Flow | I-24 Smart Corridor, 4 lanes + 3 ramps, TransModeler | **3-lane mainline → 4-lane weaving (250 m) → 3-lane downstream, on + off ramps, SUMO** |
| **CAV / compliance** | 100 % CAV (no sweep) | **10 % AV only** | 5 % train / 50 % + 100 % compliance test (human compliance, not CAV) | **50 % now → 100 % in paper (sweep planned for PhD)** |
| **Demand** | 130 fixed scenarios from PeMS (~5,300 vph mainline) | Fixed sampled inflow 1000–2000 vph | Fixed 1850 veh/lane/hr first hour | **Stochastic peak ∈ [5500, 8000] vph + anomalies (ramp_spike, speed_reduction, lane_closure) @ 15 % prob** |
| **Reward** | r_v (mean speed) + r_s (TTC), 2-term hybrid | Pure outflow (1 term) | adaptability + step-down + mobility, 3-term linear | **5 quadratic terms (harmonization upstream + lane variance + temporal stability + throughput + lane equalisation + smoothness) × 5** |
| **Baselines** | NoVSL, TD3RVSL, DQLLVSL, DDPGLVSL | Uncontrolled, feedback ramp meter | NoControl, Speed-Matching (deployed), IPPO, IAM variants | **NC, M110_uniform, diff_mild, M60-M110_active sweep (6 points), diff_mild_active, diff_aggressive_active** |
| **Headline KPI** | +69.7 % mean speed, −16.4 % TTS, −93.8 % TIT vs. NoVSL | +200 veh/h (≈25 %) outflow at high inflow | +63.4 % safety vs. NC, +58.6 % mobility vs. deployed | **~17 % reward improvement, halved lane_sigma, halved max_lane_diff** |
| **Safety surrogate** | TET, TIT, TTC threshold = 3 s | None | Normalised CVS, queue length, step-down violations | lane_sigma, harmonization penalty (no TTC/TET yet — KPI gap to close) |
| **Stochasticity** | Sampled traffic; vehicles deterministic CAV | "Randomly sample an inflow" 1000–2000 | Driver compliance only | **Stochastic demand + 3 anomaly types** |
| **Novelty headline (verbatim)** | "first to apply TD3 … LVSL … for CAVs" (p. 3) | "first … Lagrangian control of freeways by AVs" (p. 760) — *Lagrangian = our CAV-direct* | "first MARL framework … with real-world deployment capabilities" (Abstract) | **First TQC + per-lane mainline-VSL + ramp-VSL + CAV-direct + stochastic anomaly demand** |

### 11.2 Novelty assessment (qualified YES)

Per the subagent's synthesis: **no single paper in the corpus combines** (TQC + per-lane mainline + ramp VSL + CAV-direct VSL + stochastic anomaly demand + distributional critics). TD3LVSL is posted (their term: Eulerian); Vinitsky is CAV-direct (their term: Lagrangian) but uniform-per-segment and pre-distributional; MARVEL is MARL posted with discrete actions. The TQC choice itself is a meaningful methodological contribution — TD3LVSL motivates TD3 for overestimation, and TQC strictly supersedes that motivation with quantile critics.

### 11.3 Headline gain comparison

Our "~17 % reward improvement, halved lane_sigma" is **modest in headline magnitude** vs. TD3LVSL (+69.7 % mean speed, −93.8 % TIT vs. NoVSL) and MARVEL (+58.6 % mobility vs. deployed). However this is a **baseline-strength artefact**: TD3LVSL and MARVEL beat *NoVSL* or a single deployed rule, while we already beat **eight static CAV-direct + posted baselines including aggressive differentials**. Vinitsky's +25 % throughput at 10 % AV is the most directly comparable figure. **Action**: re-express our gain as `delta_flow_vph / NC_flow_vph` and `delta_merge_speed_kph / NC_merge_speed_kph` for direct comparison (RQ5 / P1 work item).

### 11.4 Methodology gaps — paper-1 scoping after pushback

See §2.4 for the full actionable list with the keep/defer decisions. In short:

**Address in Paper 1:**
1. **Reward-weight ablation** (P3): MARVEL admits the same gap on p. 162002 — cheap and strengthens the central claim.
2. **Collision-count evidence** (ADR-010 codebase change): converts the safety-by-construction claim into positive empirical evidence.

**Defend without new work:**
3. **Safety surrogates (TTC/TET/TIT/CVS)** → ADR-010 (safety by construction via Krauss + slowDown semantics).
4. **Simulator realism vs calibrated TransModeler** → ADR-011 (cite Lopez 2018 + Krajzewicz 2002 validation paper + cite-other-VSL-in-SUMO-papers).
5. **Ramp-fraction sweep range** → ADR-013 (three verbatim citations from Lorenz & Elefteriadou, Chung et al. 2007, Han et al. 2022 bracket [0.20, 0.30] as the stochastic-capacity / probabilistic-breakdown regime).

**Defer to future papers / PhD:**
5. **CAV penetration sweep** → PhD chapter (ADR-008).
6. **Comparison vs other DRL / hybrid / MPC controllers** → Paper 3 (ADR-012).
7. **Multi-topology generalisation** → PhD chapter.

---

## 12. Change log

| Date | Doc version | Author | Change |
|---|---|---|---|
| 2026-05-18 | v0.1 | Catalin + Claude | Initial draft. ADR-001 through ADR-009. §11 grounded in verbatim quotes from Lu 2023, Vinitsky 2018, Zhang 2024 (lit-comparison subagent results). |
| 2026-05-18 | v0.2 | Catalin + Claude | Pushback-driven revision. Trimmed RQs (4 instead of 6); dropped RQ2 (active-Lagrangian) → Paper 2 hook; softened contribution claim #2; added ADR-010 (safety by construction), ADR-011 (SUMO defense), ADR-012 (cash-cow scope discipline); rewrote §8.4 KPI list to focus on Lagrangian-VSL effectiveness rather than generic safety surrogates; updated §3 timeline with explicit Paper 1 / Paper 2 / Paper 3 / PhD split; added R-8 risk for unverified safety claim. |
| 2026-05-18 | v0.3 | Catalin + Claude | Added ADR-013 — ramp_fraction sweep [0.20, 0.30] defended by 3 verbatim citations (Lorenz & Elefteriadou TRB E-C018, Chung et al. 2007 TRB Part B, Han et al. 2022 TRC) bracketing the stochastic-capacity / probabilistic-breakdown regime. §2.4, §11.4, §3 (Paper 2 hook), §8.4 (per-quartile reporting) updated accordingly. No code change required — sweep already implemented at [stochastic_demand.py:37,52,86-87](../../traffic_environment/stochastic_demand.py#L37). |
| 2026-05-18 | v0.4 | Catalin + Claude | Added ADR-014 — pure CAV-direct VSL is a methodological necessity, not a design preference. Four-argument defense (regulatory / display / cognition+compliance / empirical Box(5) ablation / information-theoretic) with the load-bearing reframe that **the display constraint binds regardless of compliance level**, blocking continuous-action posted deployment even at the ~95 % compliance achievable via average-speed enforcement (UK SPECS / Dutch trajectcontrole / Italian SICVe). §2.1 problem-statement bullet rewritten; ADR-001 gets a cross-reference; ADR-004 documents Box(5) as the cited hybrid ablation. National-level enforcement-compliance citations to be added at paper submission time (general acknowledgement suffices for the plan per ADR-012 scope discipline). |
| 2026-05-18 | v0.5 | Catalin + Claude | Terminology refactor: "Lagrangian VSL" → **"CAV-direct VSL"**, "Eulerian VSL" → **"Posted VSL"** throughout plan body and ADRs (per user pushback that Lagrangian/Eulerian draws unnecessary jargon attention and isn't field-standard — 2 of 3 closest papers don't use it). Equivalence note added in glossary; verbatim paper quotes in §11 retain original terminology with inline "= our CAV-direct/posted" annotations. Memory updated with the equivalence for cross-paper correlation. |
| 2026-05-19 | v0.6 | Catalin + Claude | **Results milestone.** New §8.5 records the 2026-05-19 evaluation: 4-config 100 % CAV ablation (base + harmo_pure + no_throughput[3-seed partial] + no_smoothness), 660 evaluation episodes total, 0 collisions. Base config is the empirical winner on physical KPIs and seed stability. §2.2 RQ table updated with verified numbers for RQ1 + RQ3. §2.3 contribution claims now reference the §8.5 evidence; added a 4th claim covering empirically-verified safety. §2.4 + new R-9 risk surface the cross-config reward-yardstick caveat (worked example in §8.5.4). §3 timeline marks P1/P3/P4 done; P2 (KPI extractor) is the immediate next step. §10 reproducibility checklist updated with what's actually verified. Paper draft remains future work per user directive. |
