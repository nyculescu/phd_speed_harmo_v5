# Algorithm-first directions under your title: the top three

*2026-10-15. Scores are the refuter's judgement, not measurements.*

**Short answer.** Eight candidates were scouted and then attacked by a refuter. **Three survived, each only in a narrowed form.** All three share one loop: a simple forecast, a margin, and an online rule that resizes the margin from the errors just seen. None needs DRL. The seed A+B did **not** survive, because its wave half is already published.

**The prior-art check is incomplete.** Each candidate got about 8–12 web searches plus arXiv and Crossref lookups. There was no Google Scholar, Scopus or IEEE Xplore search, and most paywalled journal papers were not read. Below, "not found" means "not found in a short search".

**One decision comes first, for all three.** Does online conformal or Bayesian calibration count as "learning-based" under D5.8? If not, restate the bar before you look at any data.

**ACI (adaptive conformal inference).** After a miss, the margin grows by a big step. After each hit, it shrinks by a small step. Over the long run, the miss rate then meets your target.

```
 sensors ──> simple forecast ──> margin ──> planner / filter ──> acceleration
              #1 leader braking     ▲        #1 RSS safety filter
              #2 green window       │        #2 eco-approach DP
              #3 wave envelope      │        #3 smoothing MPC
                                    │
 what really happened ──> miss? ──> online update (ACI / CDT / Bayes)
```

## 1. Conformal RSS: a leader-adaptive safety filter (narrowed G1)

**Pitch.** A safety filter for one automated car, built on the RSS safe distance. RSS uses a fixed "maximum leader braking" value. Here that value is learned online, per traffic regime, from real leaders. Behind smooth leaders the gap gets shorter. In stop-and-go it gets longer.

**Algorithm.**
- Senses: own speed, radar gap, relative speed and a regime tag.
- Decides: the acceleration closest to a tuned ACC's command that still keeps the RSS distance.
- Adapts: the leader-braking envelope, per regime. It uses ACI with delayed feedback; a multivalid variant handles regimes that overlap.
- Method core: a theorem. If the leader does not react to the ego, the long-run violation share per regime stays at or below your target.

**Title.** "Adaptive" and "driving algorithm" fit well. "Traffic system" is weak. To fix it, add a capacity proxy from the time gap, or a chain of IDM cars behind the ego.

**Prior work and gap.**
- Zhou et al. 2026 already put a conformal margin in an ACC filter, with plain ACI as a baseline. Their leaders are scripted, and they calibrate on the error of their own-car model.
- Huriot 2026 and Dixit 2022 combine ACI with safety filters or planners, but outside traffic.
- Offline RSS calibration from naturalistic data may exist [VERIFY].
- **Gap (narrow):** a leader-braking score tied to barrier safety, online coverage per regime, and evidence across sites behind real leaders.

**DRL:** no.

**Testbed and data.** NumPy replay at 0.1 s; the ego replaces the recorded follower. Calibrate on reconstructed NGSIM I-80. Test on NGSIM US-101 and TGSIM I-294 (CC0).

**Baselines.**
- Default RSS.
- RSS calibrated offline, globally and **per regime. The per-regime version is the key opponent.**
- Tuned time-gap ACC.
- Recorded human driver (never reported alone).
- Hindsight oracle.

**Honest gain.** Unknown. It should be large against default RSS, but that is a weak baseline. Against the per-regime offline margin, expect a few percent or zero in gap. The win to hope for is equal violation rates across sites.

**Papers.**
- P1: the method, the theorem and the replay behind real leaders.
- P2: cut-ins with an envelope reset, or a wave smoother inside the filter.

**First test (2 weeks).** KILL if either holds:
- the per-regime envelopes differ by less than 0.1 s of time gap;
- across sites, the online envelope does not beat the per-regime offline one.

You fix the thresholds before data.

**Decisions (5).** Score and horizon; target rate and regime bins; datasets; ACI or multivalid; D5.8 restatement.

**Risks.**
- It is close to Zhou 2026.
- Violations are rare, so you need many leader-hours of data.
- NGSIM noise can create fake violations.
- A certified filter may keep longer gaps than humans do. Then "≥ 10 % better than no control" may be impossible.

## 2. Decision-calibrated eco-approach at actuated signals (narrowed G3)

**Pitch.** One connected car approaches an actuated signal and chooses: pass, or stop smoothly. A margin on the green window is tuned online for each signal group. It keeps the rate of "committed to pass, then braked hard or crossed on red" at your target. The data are switching streams you record yourself in Hamburg.

**Algorithm.**
- Senses: signal state, program ID, cycle second, distance and speed.
- Forecast: a frozen empirical forecast of the remaining green time.
- Decides: a known stochastic GLOSA / chance-constrained DP plans the speed, using the margin.
- Adapts: the margin, by conformal decision theory (CDT), every cycle. It replays the current plan against the real switch, so the car does not need to cross.

**Title.** Adaptive: the margin follows live errors. Driving algorithm: a planner for one vehicle. Traffic system: it uses V2I signal data (ARC-IT code [VERIFY]). The signal itself is not controlled.

**Prior work and gap.**
- Stochastic GLOSA is mature (Sun-Shen-Moura 2018, Shafik 2022, Typaldos-Papageorgiou 2022).
- Patent US12600379B2 calibrates signal windows **offline** to a violation target.
- CDT and ACI inside planners are standard in robotics.
- Two likely competitors are not read yet: Li-Wang-Hu (TR-C 177) and Xue et al. (TR-C 183).
- **Gap (narrow):** online, decision-level calibration on real data streams that change over time.

**DRL:** no.

**Testbed and data.** Record the Hamburg TLD feed by MQTT for 6–8 weeks, about 20–50 signal groups. The feed seems not to keep history, so start early. The licence has not been seen [VERIFY]. Replay the recorded states at one stop line with a longitudinal energy model.

**Baselines.**
- Deterministic GLOSA.
- SUMO's glosa device.
- Robust min/max window.
- Tuned global margin.
- **Margin table per group × program × time of day. This is the key opponent.**
- Patent-style offline window.
- Oracle.
- IDM human driver (never reported alone).

**Honest gain.** Eco-approach against an uninformed driver gives large savings in simulation: Shafik 2022 reports 37 % fuel with deterministic timing and 28 % with stochastic timing. Field gains are usually smaller. Against the margin table the gain is unknown, probably small in energy. A win is more likely in hard-brake and red-light rates when conditions change: program changes, holidays, detector faults.

**Papers.**
- P1: the calibrated eco-approach on real streams, with an operating map.
- P2: a queue-aware window with mixed traffic on one SUMO approach, or two signals in a row.

**First test.** KILL if any holds:
- the oracle saves less than 10 % energy against IDM;
- in every regime, the table comes within 1–2 % energy and within a preset violation margin;
- recording or the licence fails within 3 weeks.

Only the third check fits in 2 weeks.

**Decisions (5).** EV or ICE; CDT or ACI; signal-group sample; target rate and loss; base forecast.

**Risks.**
- Reviewers may call it "conformal on top of known GLOSA".
- Two competitors are still unread.
- The feed has gaps.
- All data come from one city.
- The table may close the whole gap.

## 3. Uncertainty-adaptive wave smoothing from roadside radar (narrowed G8)

**Pitch.** One car forecasts the stop-and-go waves ahead, using only sparse roadside radar, and states how uncertain the forecast is. When the forecast is vague, the car is more careful. It is tested on real I-24 waves from WaveX.

**Algorithm.**
- Senses: I-24 RDS stations ahead (0.3–0.5 mi apart, 30 s data), own speed and leader radar.
- Forecast: an envelope of the leader's speed 1–4 min ahead. It comes from a particle filter or EnKF on a flow model, or from a small NN ensemble with conformal intervals.
- Decides: an MPC picks the speed under two chance limits, on entering the slow region and on the maximum gap. ACC is the fallback.
- Adapts: the margins follow the forecast's width.

**Title.** The strongest fit of the three: the caution adapts, the algorithm drives one vehicle, and corridor detectors are the input.

**Prior work and gap.**
- Smoothing on I-24 with downstream data already exists:
  - Fu et al. 2023: >15 % energy at 4 % AVs, in simulation;
  - Wang et al. 2024: a 100-car field test;
  - Lichtlé 2024: the same replay testbed;
  - Coifman & Liu 2026.
- Jam absorption from detectors: Li et al. 2024 and He 2026, both in simulation only.
- Li-Yanagisawa-Nishinari (TR-C 158) is unread and may be very close [VERIFY].
- **Gap (narrow and fragile):** radar is the only input, an explicit uncertainty estimate scales the caution, and real inputs are checked against real ground truth. But Fu et al. say modest estimates are enough.

**DRL:** no. If D5.8 needs a neural network, use the NN-ensemble forecaster.

**Testbed and data.** Single-lane replay on WaveX (CC BY 4.0). The leader comes from the MOTION speed field, and RDS is the only input. 10–20 virtual followers (Newell, IDM) drive behind. Replay cannot show a wave dissolving. MOTION covers less road than RDS [VERIFY].

**Baselines.**
- Tuned ACC.
- **The same planner with point forecasts. This is the key opponent.**
- SD-JAD, on isolated waves.
- The same planner with the perfect speed field.
- The Ji et al. offline optimum.

Regimes: detector spacing, latency, and isolated vs merging waves.

**Honest gain.** Ji et al. 2026 report 9.80–14.08 % less passenger-car CO2 if all traffic were smoothed offline. One car acting in real time will get less. The gain over point forecasts is unknown and may be zero.

**Papers.**
- P1: radar-only adaptive smoothing, with an operating map.
- P2: a heavy truck as the ego.

**First test (2 weeks).** KILL if any holds:
- the perfect-information planner beats the tuned ACC by less than 5 % energy;
- in every regime, point forecasts capture ≥ 90 % of that gain;
- there are fewer than about 30 usable lane-day episodes.

**Decisions (5).** Forecaster; follower models; α and maximum gap; regime grid; car or truck in P2.

**Risks.**
- Highest risk of being scooped: the WaveX authors, the CIRCLES groups and He all work on this.
- I-24 waves often merge (Ji et al.: 212–513 wave components per day).
- Results depend on the follower model.

## Comparison (refuter scores, each out of 10)

| Candidate | Survives | Title fit | Novelty | Total /50 | Deciding issue |
|---|---|---|---|---|---|
| #1 Conformal RSS (G1) | narrowed | 6 | 4 | 31 | narrow gap vs Zhou 2026 |
| #2 Calibrated eco-approach (G3) | narrowed | 8 | 4 | 31 | data must be recorded |
| #3 Radar wave smoothing (G8) | narrowed | 8 | 3 | 27 | scoop risk; gain may be ~0 |
| Wave-scheduled ACC (G2) | no | 8 | 3 | 28 | headroom likely too small |
| Follower-aware AV (G5) | no | 8 | 3 | 28 | concept published (Zhou-Yan-Yang 2024) |
| Regen-aware EV ACC (G4) | no | 4 | 4 | 26 | core rule patented |
| **Seed A+B (G6)** | no | 8 | 4 | 26 | wave half published |
| Cut-in-hazard ACC (G7) | no | 7 | 3 | 24 | too few cut-ins to adapt |

The total is five scores added together. G2 and G5 score higher than #3, but each has a fatal issue.

## My suggestion (judgement, not evidence)

- **Start with #1.** It needs only free data and NumPy, and its kill test is fast.
- **#1 and #2 use the same machinery.** One thesis line could be "online-calibrated margins for one automated vehicle", with P1 on the freeway and P2 at a signal.
- **#3 fits the title best** but has the highest scoop risk.
- **About 11 months remain.** Run each kill test before building anything.

## Rejected and why

- **G2 wave-scheduled ACC:** a linear ACC barely damps waves that last minutes, so the headroom is likely below the kill line.
- **G4 regen-aware EV ACC:** the core rule is a granted patent (US12515659B2), and the results would just follow the assumed regen model.
- **G5 follower-aware AV:** the core concept is published (Zhou, Yan & Yang 2024, with DRL and V2V). Adapting probably adds little over rear sensing.
- **G6 seed A+B:** the wave half is published, the cut-in half is circular, and it needs 6 decisions.
- **G7 cut-in-hazard ACC:** too few cut-ins happen to adapt to, and Lichtlé 2024 and AACC (Hu et al.) cover most of it.
- **Personalised ACC:** it needs a user study.
- **Truck-platoon gaps:** there is no free platoon data.
- **Zipper merging:** it needs SUMO lane changes, which failed in your past work.

## Sources

**Verified** (opened by a scout or the refuter; mostly read at abstract level):
- Zhou 2026: https://arxiv.org/abs/2609.35415
- Gibbs & Candès 2021: https://arxiv.org/abs/2106.00170
- Huriot 2026: https://proceedings.mlr.press/v331/huriot26a.html
- Dixit 2022: https://arxiv.org/abs/2212.00278
- Lekeufack 2023 (CDT): https://arxiv.org/abs/2310.05921
- Shalev-Shwartz 2017 (RSS): https://arxiv.org/abs/1708.06374
- TGSIM: https://catalog.data.gov/dataset/third-generation-simulation-data-tgsim
- Sun, Shen & Moura 2018: https://arxiv.org/abs/1802.07192
- Shafik 2022: https://arxiv.org/abs/2208.13709
- Typaldos & Papageorgiou 2022: https://arxiv.org/abs/2211.12159
- US12600379B2: https://patents.google.com/patent/US12600379B2/en
- Hamburg TLD feed: https://tld.iot.hamburg.de/v1.1/
- Fu 2023: https://arxiv.org/abs/2302.07453
- Wang 2024: https://arxiv.org/abs/2402.16993
- Lichtlé 2024: https://arxiv.org/abs/2401.09666
- Coifman & Liu 2026: https://doi.org/10.1016/j.trc.2025.105497
- He 2026: https://arxiv.org/abs/2602.10234
- Li, Nishi et al. 2024: https://arxiv.org/abs/2409.03968
- Ji 2026: https://arxiv.org/abs/2603.21476
- Ji (wave analysis): https://arxiv.org/abs/2409.00326
- WaveX: https://zenodo.org/records/17122740
- Zhou, Yan & Yang 2024: https://arxiv.org/abs/2401.11148
- US12515659B2: https://patents.google.com/patent/US12515659B2/en
- Hu (AACC): https://arxiv.org/abs/2412.12197

**Exists, content not read [VERIFY]:**
- Xue et al.: https://doi.org/10.1016/j.trc.2025.105460
- Li, Wang & Hu: https://doi.org/10.1016/j.trc.2025.105198
- Li, Yanagisawa & Nishinari, TR-C 158:104394

**Not verified [VERIFY]:** offline RSS calibration (search snippet only); Hamburg licence; ARC-IT codes; how much road WaveX covers.
## Main-session check (2026-10-15, night)

Fetched myself. These notes override the text above where they differ.

- **#1, Zhou et al. (arXiv 2609.35415, 28 Sep 2026): confirmed, and close.** Title: "Adaptive Safety Filtering for Frozen ACC Policies via Conformal Residual Calibration".
  - The adaptive variant updates conformal margins online from completed transitions.
  - The abstract does not say whether the leaders are scripted or recorded, or whether the residuals are leader errors or own-car errors. The text above says "scripted leaders, own-car model error"; I could not confirm that from the abstract [VERIFY in the full paper].
  - **#1's gap (real leaders, leader-braking score tied to RSS, per-regime coverage across sites) is thin.** Read Zhou et al. in full before choosing #1.
- **#2, Xue, Bai, Zhou, Ding & Vu, TR-C 2025 (online 27 Nov 2025, doi 10.1016/j.trc.2025.105460): exists, and close.**
  - Title: "Chance-constrained eco-driving control of connected autonomous vehicles in mixed traffic environment at signalized intersections with uncertain signal timings". Abstract not available.
  - What remains for #2 is online, decision-level calibration on real, changing signal streams.
  - Li, Wang & Hu (TR-C, Jun 2025): "Ecological driving at an actuated signalized intersection: a practical solution of Vehicle-Road-Cloud Integration system". Also close [VERIFY content].
- **#2's data, the Hamburg TLD feed: exists.** It is an OGC SensorThings API v1.1 service with MQTT at `tld.iot.hamburg.de:1883`. **No licence is shown on the service page** [VERIFY before recording]. History retention is not stated.
- **#2, Shafik, Eteifa & Rakha 2022 (arXiv 2208.13709): confirmed.** It reports 37 % fuel savings (deterministic SPaT) and 28 % (stochastic) against uninformed drivers, in simulation.
- **#3, Li, Yanagisawa & Nishinari, TR-C 158 (2023): exists.** Title: "A Jam-Absorption Driving System for Reducing Multiple Moving Jams by Estimating Moving Jam Propagation". Close to #3; abstract not read [VERIFY].
- **Overall reading (mine).** All three survivors scored 3–4/10 on novelty. With a simple testbed and one person, the field is crowded. The realistic contribution is an incremental but rigorous one: online calibration of a known controller, tested on real data. A PhD can rest on that, but there is no headline breakthrough.

### Further checks (same night)

- **#1, Zhou et al. 2026, full text (arXiv HTML v1):**
  - The leaders are **scripted profiles** (brake and stop-go phases with random offsets); no dataset is used.
  - The calibrated score is the error of a full-state, one-step predictor that assumes a constant leader speed.
  - The main quantile is a **single global value**, not one per regime. ACI is a baseline, which Adaptive RACF beats by 5.21 pp.
  - **No RSS:** the filter uses constant-time-headway spacing.
  - The authors' own limitation: "Evidence remains limited to simulated ACC…".
  - **So #1's gap is real but narrow:** behind real leaders, an RSS leader-braking envelope, and per-regime coverage across sites.
- **#2's data: historical Hamburg signal data are already public.** No 6–8-week recording is needed.
  - Jeschor, Matthes, Springer, Pape & Fröhlich, "Traffic Light Data of Hamburg collected in September and October 2023 (Observations from SensorThings API)", TU Dresden OPARA, published 2024-05-03.
  - Content: `observations.csv.zip`, 31.49 GB. Primary and secondary signal, cycle second, program, and detector observations.
  - Licence: CC BY 4.0, with source data under dl-de/by-2-0.
  - Completeness is "not fully guaranteed".
  - URL: https://opara.zih.tu-dresden.de/items/5ab10b56-679b-4943-8278-dd923427e883/full
- **#2's prior work on forecasting:** the same group published Jeschor et al., "Cloudy with a Chance of Green: Measuring the Predictability of 18,009 Traffic Lights in Hamburg", IEEE IV 2024, pp. 2882–2889 (arXiv 2403.18830).
  - It covers 424 M switching cycles over four weeks.
  - Its context is cyclist GLOSA in the PrioBike-HH project.
  - **Forecasting the green window is their topic. #2 must stay on the vehicle's decision layer**: online calibration of the commit/stop margin and the energy and violation trade-off, for cars or EVs.
