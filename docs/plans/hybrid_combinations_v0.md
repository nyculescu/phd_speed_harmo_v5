# Promising hybrid combinations: proven controller + DRL component (design v0, desk only)

*2026-10-05. Author's brief: start from a well-known proven controller as the **main controller**, and add a well-suited **DRL component** acting either as a **co-controller** or as an **information aggregator** feeding the main controller. Place it in a carefully selected network topology. Consider jointly:*
- *the topology;*
- *the DRL component;*
- *the state–action–reward (SAR) framework;*
- *vehicles, drivers, traffic conditions and disturbances.*

*Thesis claim (memory `thesis-claim-definition`): learning-based control (DRL), alone or **hybrid** with proven control families, measurably beats the best **tuned** proven control. Since 2026-10-05: hybrid first, with DRL alone only as a reference arm.*

*Inputs:*
- *`docs/plans/vsl_hybrid_screen_v0.md` §3, §6 (Cards A and B);*
- *`docs/review/design_space/README.md` and notes;*
- *`docs/review/day_pattern_research_v0.md`;*
- *`docs/plans/Thesis path with daily patterns (human).md` §4–5;*
- *the lab results in `docs/lab/STATUS.md`.*

*Literature not read in full is marked [VERIFY]. Probabilities are my judgements, not measurements.*

---

## 0. Summary

| # | Main controller (family) | DRL role | Hidden condition the DRL exploits | Network | Recommendation |
|---|---|---|---|---|---|
| **H1** | **HERO** = coordinated ALINEA (classical feedback + rule-based coordination) | **Co-controller:** a day-pattern *mode scheduler* every 10 min | the day's true demand curve (level, timing, shape), hidden in clipped counts | MnDOT corridor, 3 metered ramps, ≥ 10 km instrumented upstream | **First.** It fits the day-pattern pillar, R6's proven structure and the data already being pulled |
| **H2** | **MTFC-VSL + ALINEA** (classical feedback cascade, Carlson integrated scheme) | **Information aggregator:** supplies the density set-point and the expected inflow to MTFC | the day's effective capacity / critical density (driver mix, trucks, weather) | the same corridor, plus a VSL application area upstream of the bottleneck | **Second.** It brings speed harmonisation in, and fits the aggregator idea. Its prior is weak (G small in earlier screens) |
| H3 | **SPECIALIST** (rule-based, shock-wave theory) | Co-controller: activation, timing and parameters per detected jam | compliance and detection delay; wave occurrence by day pattern | a long homogeneous stretch (8–14 km) downstream of a bottleneck, gantries every ~500–700 m | **Deferred.** The plant-realism risk is high (waves) and an MPC may beat SPECIALIST outright |
| H4 | HERO / ALINEA (as H1) | Co-controller: an *event-mode switcher* (R6 generalised) | the type and severity of the disturbance (ramp spike, local slowdown, lane closure) | as H1 | **Merge into H1** as secondary hidden events. On its own it is weak (Lead 1: H = 3.3 %) |

**The one-line rationale.** Headroom for a hybrid appears only where the main controller is **blind to something that changes its best setting**, and where that something is **visible from history and the wider road** (README §1.2; v6 lessons §2). In H1 that something is the day's true demand, hidden by capacity clipping. In H2 it is the day's true capacity. Everything else is either plant realism or a robustness test.

---

## 1. Design principles common to all combinations

### 1.1 The DRL never actuates directly

The main controller always computes the meter rate or the speed limit, and keeps its own safety logic: queue override, rate and step limits, the solvability test. The DRL component acts in one of two ways.

| Role | What the DRL outputs | Counts as DRL? |
|---|---|---|
| **Co-controller** (scheduler, switcher, bounded residual) | a mode, a parameter set, an activation flag, or a bounded correction, every 5–15 min or per event | yes: RL-trained on the control reward |
| **Information aggregator** | an *input* to the main controller: a set-point, an expected demand, a time-to-breakdown, an effective capacity | **only if RL-trained end-to-end on the control reward**. An aggregator trained by supervised learning (a forecaster) is learning-based control but **not DRL**. Whether that suffices is the author's call (§6, decision 3) |

> Note: an RL-trained aggregator that outputs a set-point is mathematically a co-controller acting through the set-point channel. The distinction is about **design intent and interpretability**: the main controller stays in charge, and the DRL "informs" it.

### 1.2 Every factor gets one role, never all at once

The brief lists many factors. Randomising all of them at once dilutes the signal, multiplies training cost, and makes any result impossible to attribute. That was a lesson from v5, whose 100-type fleet was silently inert. Each factor therefore gets **one** role per combination:
- **P, plant realism:** calibrated and fixed. It makes the road behave like a real road (realism gate).
- **H, hidden condition:** randomised per day or event, unobserved directly by any controller. It is the reason DRL could help, so it must move the best setting (G ≥ 10 %).
- **T, held-out test:** varied only in evaluation, beyond the training range (generalisation, OOD).
- **O, out of scope** for this combination.

### 1.3 The same condition is defined at both model levels

The gate and training run on **METANET** (macroscopic) and the confirmation on **SUMO** (microscopic). Vehicle and driver factors exist as vehicles only in SUMO; in METANET they enter through the parameters below. Every hidden condition is therefore defined twice, consistently. For example, "cautious-driver day" = −x % capacity and −y % critical density in METANET, which corresponds to the S1-B3 class shift in SUMO.

| Factor | METANET representation | SUMO representation |
|---|---|---|
| truck / truck-trailer share | PCE-adjusted capacity; lower free speed on grades | vTypes (length 12 m and 18–22 m, accel 0.6–1.2 m/s²) |
| HDV heterogeneity / reckless share | capacity, critical density, drop size; relaxation τ and anticipation ν | vType distributions (S1-B3 pattern); a small reckless class with lcAssertive ↑ |
| speed-limit compliance | Hegyi's non-compliance α (desired speed = (1+α)·VSL) | speedFactor groups (normc pattern) |
| weather | free speed −v %, capacity −c %, critical density shift | speedFactor ↓, tau ↑, accel ↓ per weather class [values VERIFY] |
| CAV penetration / responsiveness | mixed-flow capacity term (only if CAVs are in scope) | ACC vType with setMaxSpeed staircase; a responsiveness lag. Avoid default CACC at 0.5 s (artefact, STATUS §14) |
| lane-changing behaviour | (implicit in drop and merge parameters) | LC2013 parameters, gated by realism (D-3: lcAssertive moves onsets) |

### 1.4 Two timescales

- **The main controller runs at its native period:** ALINEA and HERO 20–60 s; MTFC 60 s; SPECIALIST updates fronts every few seconds and detects each minute.
- **The DRL component decides slowly:** every **10 min** (H1), **5–10 min** (H2), or per detected event (H3, H4).

This is what makes the learning problem tractable. A full day is about 108 decisions at 10 min, instead of about 2,000 at 30 s. That is a direct answer to the convergence failures seen with DRL alone (author: "better at 60k than at 800k steps").

### 1.5 Shared DRL defaults (starting points; tuned on validation days only)

| Item | Default | Why |
|---|---|---|
| Algorithm | **RecurrentPPO** (LSTM). **MaskablePPO** with a feature history as the variant when masks matter more than memory | Memory recovers the day's phase (§5 of the thesis path). Masks enforce storage and step rules. No maskable-recurrent implementation exists in contrib [VERIFY], so combining them needs custom code |
| Policy / network | actor and critic MLP 2 × 128 tanh; LSTM 64–128; separate critic | the R6 configuration, kept as the known-working baseline |
| Privileged critic + context head | the critic sees the true hidden condition (training only); an auxiliary head predicts it, for example time-to-peak or the day's capacity | design-space R1 ladder. The context head is a **diagnostic**: if it can't predict the condition, the history doesn't carry it |
| Action space | **discrete menu** of tuned settings (5–20 options), with masks | R6's design. The tuned controller is inside the menu, so the hybrid starts from the baseline |
| Normalisation | **fixed physical scaling:** flow / capacity, occupancy / critical occupancy, speed / free speed, queue / storage, time as sin/cos of the day. **No running VecNormalize** | the policy then transfers METANET → SUMO and corridor → corridor |
| Reward | −(vehicle-hours in network + ramp queues + origin queues) over the decision interval, i.e. the TTS increment including entry queues | aligned with the primary metric (door-to-door delay). No proxy terms (v5 lesson: the speed-variance reward cost +23 % TTS) |
| Discount | γ ≈ 0.97–0.98 per 10-min step (effective horizon ≈ 4–8 h) | peaks and recoveries span hours |
| Learning rate | 3e-4 with linear decay (S0 fix `34ae76f` makes this actually happen) | the R6 learners trained at constant lr and drifted |
| Rollout | 16–32 envs (METANET is cheap) × 1 day each; ≥ 500 updates; 3–5 learner seeds | the lab's budget rule |
| Convergence | roadmap C1 (final within 2 % of best, slope, EV > 0.6, entropy stable, entropy floor). Checkpoint chosen on **validation days** only | catches the "60k better than 800k" failure |
| Training data | synthetic days from the fitted multi-peak model (primitives, §5 of the thesis path), concentrated around the M → trapezoid transition; hidden conditions sampled per day | real structure, unlimited variety |
| Non-RL rivals on the same features | ARS (linear policy) and BO/CMA-ES-tuned schedules | if ARS matches the DRL, the claim is not about DRL (design-space R3) |
| Environment | METANET corridor, 05:00–23:00 plus drain; controller periods as §1.4; seeds from the approved block 7,190,xxx | full days are needed for the timing problem |

### 1.6 Neural-network components beyond RL (added 2026-10-05 at the author's request; this reframes the plan)

**Terms first.** LSTM, GRU, TCN, CNN, graph networks (GNN) and transformers are **network architectures**. Supervised learning (classification, regression, forecasting), imitation learning and reinforcement learning are **learning paradigms**. RecurrentPPO already *uses* an LSTM inside an RL policy. The real question is therefore which **paradigm** the learned component uses, not which network.

**Supervised and imitation alternatives for the DRL component:**

| Component | Paradigm | What it outputs | Where it plugs in | Evidence found (all [VERIFY]) |
|---|---|---|---|---|
| **Demand / traffic forecaster** (LSTM, BiLSTM, TCN; physics-informed variants) | supervised regression | the expected demand or density over the next 15–60 min | an *information aggregator* for HERO/ALINEA ("predictive ALINEA"), MTFC or MPC | physics-informed LSTM with a localised and an integrated **Predictive ALINEA** ([Univ. Genova records](https://unige.iris.cineca.it/handle/11567/1301562)); BiLSTM freeway forecasting on a calibrated Melbourne freeway ([Sci. Rep. 2021](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8668885/)) |
| **Breakdown / day-type classifier** | supervised classification | P(breakdown within the next k min); day type or cluster | triggers HERO's anticipatory mode, or selects the plan | ANN breakdown prediction at merges using ramp and upstream data, 96–97 % accuracy ([Algorithms 2023](https://www.mdpi.com/1999-4893/16/6/298)); day-type clustering (research report §1) |
| **Imitation of the informed reference** (behaviour cloning, then DAgger) | supervised / imitation | the mode the informed reference *I* would choose, from online-available observations only | replaces the RL scheduler of H1 | none found for freeway control; the method itself is standard (Ross, Gordon & Bagnell 2011, DAgger [VERIFY]) |
| **Learned dynamics model** | supervised | next-state prediction | the model inside an MPC (model-based learning control) | learning-based MPC review (Hewing et al. 2020 [VERIFY]); RL + MPC ramp metering (Airaldi et al. 2023, [arXiv 2311.08820](https://arxiv.org/pdf/2311.08820)) |
| **Demand reconstruction** (estimator) | supervised | the true demand behind clipped counts, from queues, upstream flows and travel time | input to any controller, and the source of training labels | freeway accuracy figures not found (research report §2) |

**How this reframes the research:**
1. **The supervised rivals become mandatory comparators.**
   - Their training target (true demand, or *I*'s actions) is **available**: in simulation it is known, and in real data it can be reconstructed in hindsight from upstream detectors.
   - Supervised training is far more stable than RL, which directly addresses the "better at 60k than at 800k steps" problem.
   - So a DRL hybrid must beat **forecast-informed HERO** (supervised aggregator) and **imitation of *I*** on the same observations. Otherwise the result says "learning helped", not "DRL was needed". This extends the ARS check (§1.5) to neural rivals.
2. **They can train on real days; RL cannot, easily.**
   - A forecaster or classifier can be trained on reconstructed **real** 2023 MnDOT days and tested on 2024 days.
   - RL trains on synthetic days fitted to real ones.
   - The forecasting route therefore uses *real* day-to-day predictability directly. This is an advantage for the supervised variants, and a validity check for RL's synthetic training.
3. **What RL can add that supervised learning cannot** (this is where a DRL claim must live):
   - *I* is a heuristic reference, **not an optimum**. Imitating it can at best approach it.
   - RL optimises the actual objective, so in principle it can **exceed** *I*: for example, trading ramp-queue storage now against breakdown risk hours later, which no forecast or label directly encodes.
   - So the DRL claim is strongest as "DRL beats the forecast-informed and imitation hybrids", not just the tuned controller.
4. **A stacked design:** the DRL scheduler can take the forecaster's or classifier's outputs **as observations** (forecast-augmented DRL). This shortens the memory the policy needs, which helps the timing problem (thesis path §5). The supervised parts then stay frozen and separately tested.
5. **The predictability check** (thesis path §5.5.3) is exactly a supervised forecaster or classifier. So the same component serves as a gate diagnostic, a comparator, and possibly an input to DRL.
6. **Architecture choice:** for a 3-ramp corridor with about 15–30 stations, LSTM, GRU or TCN on station sequences is adequate. Graph networks pay off at network scale (many interacting nodes) and are not needed first. No evidence was found that transformers help here.

**The decision this raises for the thesis claim:** does a **supervised NN hybrid** (for example, LSTM-forecast-informed HERO) count as the positive "learning-based control" result? Or must the winning component be **DRL**? (The memory `thesis-claim-definition` currently reads "learning-based control, i.e. DRL".) Either way, the supervised hybrids are in the comparison.

---

## 2. H1: HERO + DRL day-pattern mode scheduler (co-controller). **Recommended first.**

### 2.1 Idea

HERO coordinates ALINEA at several ramps and balances their queues. It is reactive: it starts metering hard when the bottleneck's occupancy rises.
- **On a heavy day,** the counts it and its timetable rely on are clipped. It meters too late and lets the bottleneck break down, which costs the capacity drop for the rest of the peak.
- **On a light day,** metering early only costs ramp delay.

The DRL layer sees the long upstream road, the day so far and the time. Every 10 minutes it chooses **how anticipatory HERO should be**.

### 2.2 Specification

| Dimension | Choice for H1 |
|---|---|
| **Network topology** | |
| Corridor | one of I-35W SB, I-394 WB, T.H.100 SB (2023 data being pulled), chosen on capacity drop and M/trapezoid variety; extended to **≥ 10 km upstream** of the first metered ramp, and 2 km downstream of the bottleneck |
| Detector placement | MnDOT mainline stations every ~0.5–1 km, all lanes; ramp **queue + passage + merge** detectors; off-ramp exit detectors (flow balance) |
| Bottleneck / disturbance location | the recurrent bottleneck seen in the data (e.g. I-35W SB at Johnson St); disturbances at the metered ramps (demand spikes) and downstream of the bottleneck (lane closure) |
| Traffic lights | the 3 ramp meters, MnDOT-style (rate-controlled release); storage and maximum wait from the MnDOT config (e.g. storage 410–560 m; default `max_wait` 240 s [VERIFY meaning]) |
| VSL / speed actuation | **none in H1** (metering only), so effects can be attributed. VSL comes in with H2 |
| Control-zone length | the 3 ramps + 2 km downstream (≈ 5–7 km); observation zone ≥ 15 km |
| Lane-level topology | from the MnDOT config (2–4 lanes, auxiliary lanes at merges); METANET per segment, SUMO per lane |
| **Main controller** | HERO over ALINEA (Papamichail & Papageorgiou [SAGE][VERIFY]); ALINEA (Papageorgiou et al. 1991 [SAGE][VERIFY]); parameters tuned with BO on 2023 tuning days |
| **DRL role** | co-controller: a **mode** from a menu of ~12 options = {bottleneck occupancy set-point offset −10 / −5 / 0 / +5 %} × {HERO coordination aggressiveness low / medium / high}, plus an "anticipatory early start" flag per ramp. Masks: ramp storage, maximum wait |
| **State** | 5-min aggregates of every station (flow / capacity, occupancy / critical occupancy, a speed proxy); ramp queue estimates (queue minus passage counts); time of day (sin/cos); weekday / weekend flag; cumulative entering volume since 05:00 / typical; previous mode; LSTM memory |
| **Action** | discrete mode (above), every 10 min |
| **Reward** | −ΔTTS including ramp and origin queues, per 10 min |
| **Vehicles / drivers / conditions** | **P:** MnDOT-observed mix (truck share from length data where available [VERIFY that Mayfly `length` covers these stations]); normal HDV. **H (primary):** the day's demand curve (multi-peak, level around the transition). **H (secondary, from H4):** ramp-demand spikes, lane closures. **T:** weather classes (snow / rain days from 2024), unusual days (holidays). **O:** CAVs, VSL compliance |
| **Comparators** | NC; tuned fixed-time metering per calendar type (counts-fitted); first-hour pattern matching; tuned ALINEA; tuned HERO; **adaptive ALINEA** (online critical-occupancy estimation, AD-ALINEA-style [VERIFY]); MPC with a METANET fitted on separate days and a fitted forecast; **forecast-informed HERO** (LSTM/TCN demand forecaster as information aggregator, §1.6); **breakdown-classifier-triggered HERO** (§1.6); **imitation of *I*** (DAgger, §1.6); ARS; DRL alone (reference arm) |
| **Informed reference (gate)** | HERO with the mode schedule computed from the **true** day demand (frozen mapping), and MPC with true demand |
| **Kill tests** | realism (S1-style) on the calibrated METANET; the predictability check (can a forecaster time the onset from the same observations?); T2 G = informed mode table vs pooled best mode ≥ 10 %; the headroom gate on 2024 days |

### 2.3 Why it is promising, and why it may still fail

**For it:**
- It targets the **one mechanism that tuned feedback structurally lacks**: knowledge of demand that is not yet at the bottleneck, plus clipped-count blindness on heavy days.
- It has R6's structure (DRL turning a proven meter's dial), which is the project's only confirmed hybrid win.
- The data and the plant work are already moving.

**Against it:**
- HERO is reported to approach proactive optimal control while being purely reactive (abstract only [VERIFY]).
- Most of the day pattern is calendar-predictable.
- Published anticipation gains over tuned feedback are about 0–4 %.

**Kill probability, my judgement:** about 85 %. It is lower than Card A's 93 % because the long upstream view and the clipped-count mechanism are new sources of headroom, and realism is now handled by calibration rather than SUMO defaults.

---

## 3. H2: MTFC-VSL + ALINEA with a DRL information aggregator (set-point and inflow). **Second.**

### 3.1 Idea

The Carlson integrated scheme holds traffic upstream of the bottleneck with variable speed limits (MTFC, a PI cascade on the bottleneck density) and meters the ramps (ALINEA). Its performance hinges on the **density set-point** (≈ critical density). Its gains matter little: in Carlson 2013, TTS moved only −32.2 to −34.7 % across the gain grid.
- On a day when the bottleneck's real capacity is lower (cautious drivers, more trucks, rain, snow), a fixed set-point is too high, and the bottleneck breaks down.
- When capacity is higher, the set-point is too low, and capacity is wasted.

The DRL **aggregates** the long-road observations and the day so far into the set-point and the expected inflow, and feeds them to MTFC every 5–10 min. MTFC stays in charge of the speed limits.

### 3.2 Specification (differences from H1)

| Dimension | Choice for H2 |
|---|---|
| VSL / speed-actuation locations | an application area of 1.5–3 km upstream of the bottleneck, gantries every ~500 m, then a ~500 m acceleration area (the MTFC design) |
| Speed-actuation timing | 60 s (the MTFC period) |
| Magnitude of speed change | b in steps of 0.1 of the legal limit, b ≥ 0.2; ≤ 0.2 change per step (Carlson parameters read in full, Transportes 2013) |
| Spatial propagation | the same b over the application area, with ≤ 0.2 difference between adjacent gantries; no moving fronts (that is H3) |
| Main controller | MTFC cascade + ALINEA (Carlson et al. 2010/2011/2014 [VERIFY]), BO-tuned |
| DRL role | **information aggregator:** outputs ρ̂ (the density set-point, from 0.80–1.10 × the reference critical density) and an expected-inflow class; RL-trained on the control reward |
| State | as H1, plus the VSL-area outflow and the current b |
| Vehicles / drivers / conditions | **H:** the day's effective capacity (driver-population class from S1-B3; truck share; weather class). **P:** compliance distribution (normc), fixed. **T:** compliance outside the training range; reckless share |
| Comparators | as H1, plus tuned MTFC, **adaptive MTFC** (online ρcrit estimation, the main threat), Hegyi-type VSL+RM MPC with fitted METANET and fitted α, best constant VSL |
| Prior evidence | weak: truck share G = 4.0 %, compliance G = 0.8 %, driver class never tested (README §1.2); direct RL vs tuned MTFC ≈ 1.6 % (screen #11) |

**Why keep it:** it is the natural home for **speed harmonisation** in the thesis, and for the author's **information-aggregator** idea. It shares H1's corridor, data and plant, so its tool checks (T0 actuator, T2 G) cost days, not weeks.

**Kill probability, my judgement:** about 90 %.

---

## 4. H3: SPECIALIST + DRL activation and timing co-controller (deferred)

**Idea.** SPECIALIST resolves moving jam waves with a speed-limited area built from shock-wave theory. In field data, solvability depended on the effective limit (compliance) and the detection delay: 0–35 % of waves were solvable (Hegyi et al. 2009, read). The DRL decides per detected jam: activate or skip, the displayed limit V ∈ {50, 60, 70} km/h, the area extent, and **anticipatory pre-activation** on days whose pattern predicts waves.

**Topology.** It needs a long homogeneous stretch (the field test used 14 km of the A12 [VERIFY]) where waves travel upstream, with gantries every ~500–700 m and detectors every ~500 m. Most MnDOT corridors have ramps every 1–2 km, so a candidate stretch must be found.

**Why deferred:**
1. **Realism:** SUMO does not reproduce stop-and-go waves at scale even when calibrated (Hickert et al. 2026, partly read), so a microscopic confirmation may be impossible.
2. **The comparator trap:** in macroscopic tests, MPC beat SPECIALIST (Han et al. 2022, read: RL −35 %, MPC −26 %, SPECIALIST −16 % vs NC). A strong MPC comparator can therefore make H fail whatever G is.
3. Round 4 found that a constant speed limit captured most of the harmonisation benefit at LD3.

**Revisit if:** the calibrated METANET of the chosen corridor shows recurrent moving waves, and H1 or H2 passes.

---

## 5. H4: event-mode switcher (R6 generalised): merge into H1

The R6 mechanism (a faster, more reliable detection of the event type than a rule-based detector) gave −19 % against the event scheduler under blockages. Across varied severities and durations, though, the headroom was only 3.3 % (Lead 1). On its own it is weak.

**Proposal:** in H1, use the disturbances the author listed as **secondary hidden events** inside the day:
- **ramp-demand spikes** (+30–50 % for 15–30 min at one ramp);
- **localised speed reductions** (a work zone or a weather cell, −20 to −40 km/h over 1–2 km for 30–60 min);
- **lane closures** (1 lane, 20–60 min, downstream of the bottleneck).

This keeps the R6 idea alive on a realistic corridor, which is option D for R6, without a separate study.

---

## 6. Recommendation and decisions

**Recommended order:**
1. **H1** on the chosen MnDOT corridor: realism → predictability check → T2 → gate. H4's events are included as secondary hidden events.
2. **H2's tool checks** (T0: does the VSL area hold traffic back? T2: does the best set-point move with the day's capacity class?) in parallel, because they share the plant.
3. Only if H1 or H2 passes its gate: DRL training (hybrid first, DRL alone as the reference arm), then SUMO confirmation.
4. H3 only if the METANET corridor shows moving waves.

**Not recommended now:**
- **CAV-centred combinations.** SUMO's default CACC artefacts are known; the v5 100 %-CAV failure; and the author's constraint against new car-following models. CAVs stay a held-out test (T) at 10–20 % penetration in the confirmation stage.
- **Weather as a primary hidden condition.** The data link (MnDOT RWIS) and its behavioural parameters are unverified. Use it as a held-out test first.

**Status 2026-10-05:** decisions 1–6 are settled by the author. See `day_pattern_decisions_v0.md` (D2.2.1, D2.2.2, D2.3.1, D2.3.2 and D1). In short:
- H1 first, with H2's tool checks in parallel;
- H4's disturbances in H1 as secondary surprises;
- the factor roles as proposed;
- "multimodal" = several peaks;
- the winning component must integrate DRL.

**Decisions for the author (as asked):**
1. Start with **H1**, and run H2's tool checks in parallel?
2. For H1, include **H4's disturbances** as secondary hidden events (yes), or keep H1 purely about day patterns?
3. **Information aggregator:** must it be RL-trained, so that it counts as DRL? Or is a supervised forecaster feeding the main controller acceptable as "learning-based"? (§1.1)
4. Factor roles (§1.2): agree that vehicle classes, normal and heterogeneous HDVs and lane-changing are **plant realism** (fixed, calibrated)? That the **day pattern** (H1) and **effective capacity** (H2) are the hidden conditions? And that weather, reckless share, compliance outside range and CAVs are **held-out tests**?
5. Is "multimodal demand profiles" in the brief the multi-peak demand shape? I read it that way, not as transport modes.
6. ~~Supervised NN hybrid as the result?~~ **Decided (author, 2026-10-05):**
   - for now, the **winning component must be DRL**;
   - supervised NN hybrids are **opponents or complements** (for example, forecasts as DRL inputs);
   - if this research fails, switch to a hybrid supervised neural network.

   This also settles **decision 3**: an aggregator meant to be the winning component must be RL-trained; a supervised aggregator is an opponent or a complement.
