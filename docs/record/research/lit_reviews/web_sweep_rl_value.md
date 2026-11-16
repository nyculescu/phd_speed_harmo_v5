# Web sweep: where RL / DRL still adds value in freeway control (VSL, metering, CAV speed control)

Date: 2026-10-21. Engine: Claude Code `WebSearch` (standard and extended modes) and `WebFetch`; arXiv PDFs read locally with `pdftotext`. No patents, no paywall bypass.

**Basis tags**
- **[FT]**: full text read, or at least the method and results sections (arXiv PDF read with `pdftotext`).
- **[ABS]**: only the abstract or the publisher/repository landing page was read.
- **[SNIP]**: only a search-engine result snippet was seen. This is weaker than [ABS]: numbers marked [SNIP] must be checked against the paper before you rely on them.
- **[VERIFY]**: the venue, year or DOI could not be confirmed from a primary page.

**Context for the reader:** the candidate's own result is that on SUMO BN4, with a realistic capacity drop (5–8 %), neither constant nor tuned ALINEA / PI-ALINEA beats no control by 10 %. Earlier gains of 11–22 % came from a plant with a 40–50 % drop. Throughout, "tuned" means the baseline's parameters were optimised for the same scenario. "Plant realism" means whether the simulator's capacity drop and human-driver model were calibrated or checked against field data.

**Coverage caveat:** this is a one-day web sweep, not a systematic review. Search engines miss things; in particular, the "ETH replication of Hou et al." named in the brief was **not found** (see Theme A).

---

## Theme A. Fair comparisons, critiques, replications, benchmarks

| # | Citation | Link | Setting | Baseline (tuned?) | Plant realism / capacity drop | Result (as reported) | Basis |
|---|---|---|---|---|---|---|---|
| A1 | Belletti, Haziza, Gomes, Bayen. Expert level control of ramp metering based on multi-task deep RL. IEEE T-ITS 19:1198–1207, 2018 (venue per the citation in A6) | https://arxiv.org/abs/1701.08832 | Multi-ramp metering, 20-mile California freeway; BeATS macro simulator "calibrated by traffic experts" | ALINEA "calibrated by traffic engineers" (yes, expert-tuned) | Calibrated macroscopic model; capacity drop not discussed | Congested-period TTS (veh·h): no metering 11 085, **ALINEA 10 514**, MWR (their RL) 10 575, plain RL 10 617. RL reaches 96 % (MWR) or 80 % (plain) of ALINEA's improvement. **RL ≈ ALINEA, not better.** ALINEA itself gives only ≈ 5.2 % TTS over no control (my arithmetic from their table). | [FT] |
| A2 | Vinitsky, Lichtlé, Parvate, Bayen. Optimizing mixed autonomy traffic flow with decentralized AVs and multi-agent RL. ACM TCPS 7(2), 2023, doi:10.1145/3582576 | https://arxiv.org/abs/2011.00120 | Flow/SUMO Bay-Bridge 4→2→1 bottleneck (= BN4); AV penetration 5–40 % | Hand-designed feedback AV controller ("extensively tuned"); **ALINEA traffic-light baseline also shown** | IDM humans, **lane changing disabled**; congestion forms above ≈ 2 500 veh/h and does not dissolve; drop magnitude not calibrated | +20 % throughput (5 % AVs) to +33 % (40 %) over uncontrolled. Text: "its performance at a 40% penetration equals the performance of a traffic light based controller". **The best RL equals ALINEA-style metering; it does not beat it.** At 3 500 veh/h inflow, outflow is 1 803–2 034 veh/h depending on state space and penetration. | [FT] |
| A3 | Liu, Tang, Ji, Shen, Du. A DRL approach for ramp metering based on traffic video data. arXiv 2012.12104 (2020); journal version reported as J. Adv. Transp. 2021 [VERIFY] | https://arxiv.org/abs/2012.12104 | Single on-ramp, SUMO, Shanghai site, morning peak 7:50–9:00 | PI-ALINEA, "fine-tuned to minimize mean travel times" (yes) | Driving parameters "calibrated based on empirical data"; drop magnitude not reported | Peak median **mainline** travel time: no control 4.25 min, PI-ALINEA 3.75 (−11.7 %), DRL 3.4 (−20 %); 20 seeds. Tuned PI-ALINEA was **worse than no control in some seeds** (+10 %, +22 %). Headline metric is mainline-only (ramp delay reported separately as queues), and evaluation reuses the training demand profile. | [FT] |
| A4 | Airaldi, De Schutter, Dabiri. RL with MPC for highway ramp metering. IEEE T-ITS 26(5), 2025 | https://arxiv.org/abs/2311.08820 | METANET benchmark (2 origins, 1 ramp), random two-peak demand | MPC with a 30 %-wrong model; **PI-ALINEA with queue management, gains tuned by Bayesian optimisation**; DDPG | Plant = METANET with known parameters (same model class as the controller); no explicit capacity-drop calibration | MPC-RL TTS drops from ≈ 1 100 to 700 veh·h (−35 %) **relative to its own badly initialised MPC**. PI-ALINEA keeps queue violations low but has higher TTS. 15 seeds; CIs shown only for the proposed method. Code public. | [FT] |
| A5 | Ault & Sharon. RL benchmarks for traffic signal control (RESCO). NeurIPS Datasets & Benchmarks 2021 | https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/f0935e4cd5920aa6c7c996a5ee53a70f-Abstract-round1.html | Signals, SUMO (Ingolstadt, Cologne, grids) | Fixed time, greedy, max-pressure | Not applicable (signals) | Prior RL algorithms "are not robust to varying sensing assumptions and non-stylized intersection layouts". The closest benchmarking precedent; nothing equivalent exists for freeway VSL / metering. | [ABS] |
| A6 | Join, Abouaïssa, Fliess. Ramp metering: modeling, simulations and control issues. DECOD workshop, arXiv 2111.06610, 2021 | https://arxiv.org/abs/2111.06610 | Position paper (model-free control) | — | — | "deep reinforcement learning methods do not seem today to perform better than ALINEA" (citing A1). Opinion, not a test. | [FT] (the relevant passage) |
| A7 | Han, Wang, Leclercq. Leveraging RL for dynamic traffic control: a survey and challenges for field implementation. Commun. Transp. Res. 3:100104, 2023 (author list from a third-party page [VERIFY]) | https://doi.org/10.1016/j.commtr.2023.100104 | Survey with its own simulation experiments | — | — | Online RL has "high exploration and learning costs"; offline-trained RL performance "is highly reliant on the accuracy of the training simulator". | [ABS] |
| A8 | Rezaee, Abdulhai, Abdelgawad. Self-learning adaptive ramp metering, Toronto Hwy 401. TRR 2396, 2013 | https://trid.trb.org/ (record not opened) [VERIFY link] | Paramics microsimulation | Modified ALINEA (tuning not stated) | Calibrated network (per snippet) | RL −40 % and ALINEA −20 % total travel time, both vs no metering. Old work; shows the typical large-gain claim. | [SNIP] |
| A9 | Ahmad, Sadat, Ahmad, Bajpai, Silgu. RL controlled VSL in urban expressway mixed traffic. IEEE IMPACT conf., 2026 | https://acikerisim.bartin.edu.tr/entities/publication/d4818b35-275a-4d09-bd27-9993788e55ba | DQN VSL, SUMO merge, calibrated on 2 field sites | Rule-based VSL (tuning not stated) | Calibrated | DQN −18.8 % TTT vs no control; **rule-based VSL made TTT 21.7 % worse**. A clear weak-baseline pattern. | [SNIP] |
| A10 | ElSamadisy, Smirnov, Wang, Abdulhai. Deep RL freeway controller chooses ramp metering over variable speed limits. TRR, 2025, doi:10.1177/03611981251333340 | https://journals.sagepub.com/doi/10.1177/03611981251333340 | QEW on-ramp (Ontario), Aimsun | Unknown | Real geometry and demand (per snippet) | Title only: given both actuators, the learned policy uses metering rather than VSL. Abstract was blocked (HTTP 403). | [SNIP] |
| A11 | "ETH replication of Hou et al. ramp metering" (named in the brief) | — | — | — | — | **Not found** in 4 targeted queries (standard and extended). Ask the author for the exact reference. | — |

---

## Theme B. Plant realism: capacity drop, calibration, sensitivity of gains

| # | Citation | Link | Setting | Baseline | Plant realism / capacity drop | Result | Basis |
|---|---|---|---|---|---|---|---|
| B1 | Jin & Jin. Control of a lane-drop bottleneck through variable speed limits. arXiv 1310.2658 (journal version reported as TR-C 2015 [VERIFY]) | https://arxiv.org/abs/1310.2658 | LWR and link-queue models with capacity drop; PI-feedback VSL | No control | Analytical | The VSL strategy "is effective only when capacity drop occurs". This is the theoretical basis for the candidate's KILL: the mobility benefit of mainline control is bounded by the drop. | [ABS] |
| B2 | Srivastava & Geroliminis. Empirical observations of capacity drop in freeway merges with ramp control and integration in a first-order model. TR-C 30:161–177, 2013 | https://infoscience.epfl.ch/record/188341 | Twin Cities merges; field loop data | — | Field-measured drop; the drop depends on the mainline/ramp flow ratio and on whether metering is active | Empirical drop magnitudes and a two-capacity LWR model. | [SNIP] |
| B3 | Yuan, Knoop, Hoogendoorn. Capacity drop: relationship between speed in congestion and queue discharge rate. TRR 2491 (per the file name) [VERIFY] | https://research.tudelft.nl/files/75552687/2491_08.pdf (PDF returned 403) | A4/A12 (NL) field data | — | Discharge rate rises with speed in congestion. A related paper reports a drop of ≈ 26 % extrapolated to 0 km/h, shrinking at higher queue speeds. | The drop is **state-dependent, not a constant**. So a controller that raises queue speed can recover part of it; this is a lever for CAV speed control. | [SNIP] |
| B4 | de Souza, Mosslemi, Vrugt, Jin. Microscopic simulation replicates the capacity drop phenomenon. Procedia CS 130:908–913, 2018 | https://doi.org/10.1016/j.procs.2018.04.088 | Car-following + lane-change model calibrated on I-405 (Irvine) | — | Drop reproduced after joint calibration; a later IEEE Access 2022 paper says cooperative lane changing matters [SNIP] | Shows a microsimulator **can** be calibrated to the field drop. RL papers almost never do this. | [ABS] |
| B5 | SUMO users mailing list thread (2019) | https://www.eclipse.org/lists/sumo-user/msg05082.html | SUMO multi-lane segment | — | An unexpectedly large lane-to-lane drop was attributed to a model artefact; switching to Krauss or W99 car-following, or changing lane-change assertiveness, removed it | Not peer-reviewed. It does show that SUMO's capacity drop is sensitive to model choice. | [SNIP] |
| B6 | Čičić, Xiong, Jin, Johansson. Coordinating vehicle platoons for highway bottleneck decongestion and throughput improvement. IEEE T-ITS 23(7):8959–, 2022 | https://people.kth.se/~kallej/papers/transport_tits21cicic.pdf | Platoons as moving bottlenecks; multi-class CTM | No control; ideal actuation as upper bound | **Assumed drop 18.2 %** (4 000 → 3 273 veh/h) | Median delay −75.6 %, mean −52.7 % vs no control. A model-based Lagrangian controller (no RL); the gain is driven by an 18 % drop. | [FT] (abstract + simulation section) |
| B7 | Jerath, Gayah, Brennan. Mitigating delay due to capacity drop near freeway bottlenecks: zones of influence of connected vehicles. PLoS One 19(6):e0301188, 2024 | https://doi.org/10.1371/journal.pone.0301188 | LWR, single lane, event-triggered CV slowdown | No control | **Assumed 15 % drop**; cites empirical 3–18 %; the drop is not varied | Delay savings up to ≈ 25–35 % in favourable cases. The benefit vanishes when the bottleneck capacity ratio approaches 1. | [FT] (first 100k characters) |
| B8 | Jang, Lichtlé, Vinitsky et al. RL based oscillation dampening: scaling up single-agent RL to a 100 AV highway field test. arXiv 2402.17050, 2024 | https://arxiv.org/abs/2402.17050 | CIRCLES simulator replaying I-24 leader trajectories | IDM baseline, "Microaccel" (non-RL) | Humans = **IDM "using string-unstable hyperparameters"**, chosen so that waves appear | In simulation, the low-speed RL controller gives +8.2 % fuel economy, +14.7 % throughput and +8.7 % speed in the "bottleneck" scenario vs IDM; −27.5 % speed in free flow. A non-RL controller (Microaccel) is comparable. | [FT] |
| B9 | Kim, Cho, Wu. RL for robust advisories under driving compliance errors. IEEE T-ITS 26(6):7780–7791, 2025, doi:10.1109/TITS.2025.3550418 | https://doi.org/10.1109/TITS.2025.3550418 | Lagrangian advisories to human drivers | Non-robust RL | Models response delay and speed deviation | Performance "degrades sharply" under compliance errors. Domain randomisation recovers up to 2.2× average speed vs non-robust training. | [ABS] |
| B10 | Ke, Li, Cao, Liu. Enhancing transferability of DRL-based VSL using transfer learning. IEEE T-ITS 22(7):4684–4695, 2021, doi:10.1109/TITS.2020.2990598 | https://doi.org/10.1109/TITS.2020.2990598 | DDQN VSL; source = a real merge; targets include "diverse capacity drop scenarios" | Training from scratch; no control | Varies the drop across target scenarios (values not seen) | TTS −26 % to −67 % (stable demand) and −21 % to −70 % (fluctuating) vs no control. No tuned classical baseline seen. | [SNIP] |
| B11 | Kumar, Chakraborty, Peruru. Macroscopic characteristics of mixed traffic flow with DRL-based AVs and HDVs. arXiv 2603.25328, 2026 | https://arxiv.org/abs/2603.25328 | TD3 car-following trained on NGSIM; fundamental diagrams | IDM | Data-driven | All-RL vs all-human capacity +7.52 %. Results are sensitive to the time-gap distribution and the RL share. | [ABS] |

---

## Theme C. Field deployments

| # | Citation | Link | Setting | Baseline | Realism | Result | Basis |
|---|---|---|---|---|---|---|---|
| C1 | Zhang, Zhang, Ji, Quiñones-Grueiro, Barbour, Gloudemans, Zachár, Weston, Biswas, Work. Real-world deployment and assessment of a MARL-based VSL control system. arXiv 2503.01017, 2025 (extends ITSC 2024; a TRID record exists) | https://arxiv.org/abs/2503.01017 | I-24 near Nashville, 17 mi, 67 gantries, live since 2024-03-08; trained in TransModeler | Rule-based benchmark, compared **offline from logs**; crashes compared before/after | Field | ≈ 34 M decisions. Policy share 81–87 % (≈ 98 % excluding capped gantries). Successful warning rate 88.6 % vs 74.4 % for the benchmark. Response to non-recurrent events < 1 min vs 2.15 min. Crashes in active periods 18.4 → 15.8 per month (−14 %); secondary crashes 7.2 → 3.6 (−50 %), labelled preliminary. **No measured travel time, throughput or delay effect.** No significance tests. AADT rose 6.6 %. The abstract's 26 % / 75 % do not match the tables. Training assumed 5 % compliance; actual compliance unmeasured. | [FT] |
| C2 | Zhang et al. MARVEL: MARL for large-scale VSL. arXiv 2310.12359, 2023/24 | https://arxiv.org/abs/2310.12359 | Simulation (8 agents on 7 mi for training, 34 agents on 17 mi for test) | No control (safety); deployed state-of-practice algorithm (mobility) | Microsimulation | Safety +63.4 % vs no control; mobility +58.6 % vs the deployed algorithm. Simulation only. | [ABS] |
| C3 | Offline RL dataset from a field-deployed VSL system (I-24), Zenodo 10.5281/zenodo.16376854 (2025); code Lab-Work/i24-vsl-orl | https://zenodo.org/records/16376854 · https://github.com/Lab-Work/i24-vsl-orl | 18 months (2024-03 to 2025-09), 67 controllers, ≈ 100 M samples; BC/BCQ/CQL/IQL/TD3+BC, evaluated in TransModeler | — | Field logs | **No results published** as of this sweep (no paper found). An opening for offline-RL work. | [ABS] (repo page) |
| C4 | Lee et al. (64 authors). Traffic control via CAVs: an open-road field experiment with 100 CAVs. arXiv 2402.17043, 2024; companion IEEE Control Systems 45(1):139–155, 2025, doi:10.1109/MCS.2024.3500332 | https://arxiv.org/abs/2402.17043 | I-24, Nov 2022, 100 vehicles, hierarchical MegaController (speed planner + on-vehicle RL/other) | — | Field | System paper; the abstract gives no measured outcomes. | [ABS] |
| C5 | BAIR blog. Scaling up RL for traffic smoothing: a 100-AV highway deployment, 2025-03-25 | https://bair.berkeley.edu/blog/2025/03/25/rl-av-smoothing/ | Same field test | Fuel of human drivers vs distance behind an engaged AV | Field (camera data) | "Trend" of ≈ 15–20 % energy savings around controlled cars; lower speed and acceleration variance. The authors say precise measurement is complicated. **Blog, not peer-reviewed**; points to IEEE doc 10858625 (not opened). | [FT] (blog) |
| C6 | Lichtlé et al. From sim to real: a pipeline for training and deploying traffic smoothing cruise controllers. IEEE T-RO 40:4490–4505, 2024, doi:10.1109/TRO.2024.3463407 | https://doi.org/10.1109/TRO.2024.3463407 | 772 km of I-24 data, one-lane simulator, 4 RAV4s on I-24 | Human/IDM | Data-driven leader trajectories | > 10 % fuel efficiency in congested simulation; field validation of behaviour, not of fuel. | [SNIP] |
| C7 | Stern et al. Dissipation of stop-and-go waves via control of autonomous vehicles: field experiments. TR-C 89:205–221, 2018 | https://arxiv.org/abs/1705.01693 | Ring track, ≈ 22 vehicles, 1 controlled AV (FollowerStopper / PI with saturation; **not RL**) | Human-only | Field | Velocity SD −49.5 % to −80.8 %; fuel −22.1 % to −42.5 %; throughput +14.1 %, +9.8 %, −2.5 % in experiments A, B, C. **A non-RL benchmark the RL work must beat.** | [FT] |
| C8 | Hegyi & Hoogendoorn. Dynamic speed limit control to resolve shock waves on freeways: field test results of the SPECIALIST algorithm (TRB record) | https://trid.trb.org/view/1096490 | A12 (NL), 14 km, Sep 2009 – Feb 2010 | No control | Field | Resolved shock waves in ≈ 80 % of activations for that jam type. About half of activations were for other jam types, with 40–50 % effectiveness. **This is the non-RL field bar for wave-targeted VSL.** | [SNIP] |
| C9 | Other RL field tests of metering or VSL (China, Europe, Australia) | — | — | — | — | **None found** in 3 queries (one extended). Hangzhou, Hong Kong and QEW items are simulation on real networks. | — |

---

## Theme D. Gains that do not depend on a capacity drop: waves, safety, eco-driving, compliance, low penetration

| # | Citation | Link | Setting | Baseline | Realism | Result | Basis |
|---|---|---|---|---|---|---|---|
| D1 | Wu, Kreidieh, Parvate, Vinitsky, Bayen. Flow: a modular learning framework for mixed autonomy traffic. IEEE T-RO 38(2):1270–1286, 2022, doi:10.1109/TRO.2021.3087314 | https://arxiv.org/abs/1710.05465 | Ring and other benchmarks, SUMO | Human (IDM) | IDM | System velocity up to +57 % with 4–7 % AVs; waves removed on a single-lane ring. | [ABS] |
| D2 | Poudel, Li, Heaslip. EnduRL: safety, stability and efficiency of mixed traffic under real-world perturbations via RL. arXiv 2311.12261, 2023/24 | https://arxiv.org/abs/2311.12261 | Ring and bottleneck; acceleration profiles from real trajectories | Prior RL and heuristic robot-vehicle controllers (FollowerStopper, etc.) | Realistic perturbations | **Prior robot-vehicle controllers degrade under real-world perturbations, "sometimes even lower than 100% HVs".** New RL: safety up to 66 %, efficiency 54 %, stability 97 % (baseline not named in the abstract). | [ABS] |
| D3 | Lichtlé et al. Traffic smoothing controllers for AVs using DRL and real-world trajectory data. ITSC 2023, doi:10.1109/ITSC57777.2023.10421828 | https://arxiv.org/abs/2401.09666 | One-lane I-24 trajectory replay | Human | Data-driven | > 15 % fuel savings at 4 % AV penetration on wave-heavy trajectories. | [SNIP] |
| D4 | Li, Liu et al. RL-based VSL control to reduce crash risks near traffic oscillations on freeways. IEEE ITS Magazine, 2020/21, doi:10.1109/MITS.2019.2907631 | https://ieeexplore.ieee.org/document/8957251/ | Q-learning VSL with a rear-end crash-risk model | No control (likely) | Simulation | Crash risk −19.4 % after training. | [SNIP] |
| D5 | Zhang, Xu, Yu, Yu. Enhancing multi-scenario applicability of freeway VSL control strategies using continual learning. Accid. Anal. Prev. 204, 2024 (PMID 38838466) | https://pubmed.ncbi.nlm.nih.gov/38838466/ | DRL VSL across scenarios (jams, secondary-crash prevention) | Not stated | Simulation | Speed SD −28.77 %, travel time −7.25 %. Names the "performance decay" of DRL VSL on earlier scenarios. | [SNIP] |
| D6 | Yang, Wang, Golpayegani, Wang. DVS-RG: differential VSL with DRL and graph state. arXiv 2405.09163, 2024 | https://arxiv.org/abs/2405.09163 | SUMO-RL, PPO, lane-level VSL | "State-of-the-art DRL methods" (unnamed) | Assumes full connectivity | Waiting time "reduced to 68.44%"; potential collisions −15.93 %. No classical baseline named. | [ABS] |
| D7 | Wu, Tan, Ran. Differential VSL control for freeway recurrent bottlenecks via DRL. TR-C 117, 2020 [VERIFY volume] | https://arxiv.org/abs/1810.10952 | DDPG, SUMO, 5-lane CA freeway | Not named in the abstract | — | "efficiency, safety and emissions can be improved"; no numbers in the abstract. | [ABS] |
| D8 | Kušić, Ivanjko, Vrbanić, Gregurić, Dusparic. Spatial-temporal traffic flow control on motorways using distributed MARL. Mathematics 9(23):3081, 2021, doi:10.3390/math9233081 | https://doi.org/10.3390/math9233081 | Distributed W-learning VSL with dynamic zones, SUMO | W-learning VSL and a proportional speed controller with static zones (per the ITSC 2021 companion) | — | "Significant" improvement claimed; numbers not seen. | [ABS] |
| D9 | Sheng, Huang, Chen. Knowledge-informed model-based residual RL for CAV trajectory control. Commun. Transp. Res. 4:100142, 2024 | https://arxiv.org/abs/2408.17380 | IDM prior + learned residual dynamics, wave dissipation | Unnamed RL agents | — | Better sample efficiency and smoothness; no numbers in the abstract. | [ABS] |
| D10 | Long, Shi, Zhou, Li. Physics enhanced residual policy learning (PERPL) for safety cruising in mixed traffic platooning. arXiv 2409.15595, 2024 | https://arxiv.org/abs/2409.15595 | Linear controller + residual RL, with actuator and communication delay | Linear controllers; pure RL | — | Smaller headway errors and better oscillation dampening in unseen extreme scenarios. | [SNIP] |

---

## Theme E. Hybrids: RL on top of or around classical control, safe, offline and model-based RL, robustness, multi-objective

| # | Citation | Link | Setting | Baseline (tuned?) | Realism | Result | Basis |
|---|---|---|---|---|---|---|---|
| E1 | Airaldi et al. (= A4): MPC as the RL function approximator | https://arxiv.org/abs/2311.08820 | METANET | BO-tuned PI-ALINEA, MPC, DDPG | Model-class plant | RL repairs a wrong-model, untuned MPC; only 53 learnable parameters vs 293 380 for DDPG; interpretable parameter drift. | [FT] |
| E2 | Sun, Jamshidnejad, De Schutter. A novel framework combining MPC and DRL with application to freeway traffic control. IEEE T-ITS 25(7):6756–6769, 2024, doi:10.1109/TITS.2023.3342651 | https://research.tudelft.nl/en/publications/a-novel-framework-combining-mpc-and-deep-reinforcement-learning-w | Slow MPC + fast DRL correction; RM + VSL benchmark (METANET) | Standalone MPC, standalone DRL | Model uncertainty and disturbances | Better than both on TTS and constraint satisfaction (no numbers in the abstract). | [ABS] |
| E3 | Önür, Dabiri, De Schutter. Adaptive tuning of parameterized traffic controllers via MARL. ECC 2026, arXiv 2512.07417 | https://arxiv.org/abs/2512.07417 | RL agents set state-feedback gains at low frequency; multi-class network | No control; **fixed-parameter feedback**; single-agent RL tuner | — | Beats fixed-gain feedback; on par with single-agent RL; more resilient to failures. **The closest published item to "RL tunes ALINEA".** | [ABS] |
| E4 | Onur, Dabiri, De Schutter. Sharing control authority between DRL and MPC: multi-class transportation networks. arXiv 2608.20858, 2026 | https://arxiv.org/abs/2608.20858 | Hierarchical MPC (slow) + DRL (fast) | Hybrid state-feedback–MPC; hierarchical MPC | Model mismatch, noisy demand | Outperforms the first; much less computation than the second. | [ABS] |
| E5 | Han, Wang, Li, Roncoli, Gao, Liu. A physics-informed RL-based strategy for local and coordinated ramp metering. TR-C 137:103584, 2022 | https://doi.org/10.1016/j.trc.2022.103584 | Iterative training on historical + model-generated data | Feedback metering; simulator-only RL | Microsimulation as the "real" process | Beats both; **tabular RL beat batch-constrained deep RL** because data were limited. | [ABS] |
| E6 | Han, Hegyi, Zhang, He, Chung, Liu. A new RL-based VSL control approach to improve traffic efficiency against freeway jam waves. TR-C 144:103900, 2022 | https://doi.org/10.1016/j.trc.2022.103900 | Explores online and offline; evaluates actions on the "real" process (macroscopic) | Existing VSL approaches | Targets model mismatch | Lower exploration cost; no numbers in the abstract. | [ABS] |
| E7 | Hu & Ma. Demonstration-guided DRL for coordinated ramp metering and perimeter control in large-scale networks. arXiv 2303.03395, 2023 | https://arxiv.org/abs/2303.03395 | ALINEA and gating act as "teachers"; Hong Kong network (simulated) | ALINEA, gating (teachers) | Meso-macro model | Student exceeds its teachers. A snippet said ≈ 12.9 % TTT [SNIP, unverified]. | [ABS] |
| E8 | Zheng, Li, Li, Ke. Enhancing RL-based ramp metering at freeway uncertain bottlenecks using curriculum learning. IET ITS 18(10):1863–1878, 2024, doi:10.1049/itr2.12494 | https://doi.org/10.1049/itr2.12494 | Modified CTM; random or multiple bottleneck locations | Feedback metering | Macroscopic | Training time −45 % to −65 %; beats feedback metering. | [SNIP] |
| E9 | Kim, Cho, Wu (= B9): domain randomisation for compliance errors | https://doi.org/10.1109/TITS.2025.3550418 | — | — | — | Robust training matters more than the algorithm. | [ABS] |

---

## Theme F. Incident-responsive control, detection uncertainty, evaluation over day mixes

| # | Citation | Link | Setting | Baseline | Realism | Result | Basis |
|---|---|---|---|---|---|---|---|
| F1 | MARVEL field (= C1): non-recurrent events | https://arxiv.org/abs/2503.01017 | 546 labelled events (337 with TMC records) | Rule-based benchmark (offline); TMC reports | Field | Mean response < 1 min vs 2.15 min (benchmark) and > 9 min (TMC). **Detection and response speed, not the control effect on delay.** | [FT] |
| F2 | Lu, Chen, Grant-Muller. Indirect RL for incident-responsive ramp control. Procedia SBS 111:1112–1122, 2014, doi:10.1016/j.sbspro.2014.01.146 (also ITSC 2013) | https://doi.org/10.1016/j.sbspro.2014.01.146 | Own platform + AIMSUN | ALINEA (thesis) | — | The thesis reports gains over ALINEA under severe congestion; incident numbers not seen. | [SNIP] |
| F3 | Zhang et al. 2024 AAP (= D5): multi-scenario decay | https://pubmed.ncbi.nlm.nih.gov/38838466/ | Recurrent, jam and secondary-crash scenarios | — | — | One DRL policy loses performance on earlier scenarios; continual learning helps. | [SNIP] |
| F4 | Zheng et al. 2024 IET ITS (= E8): bottleneck location uncertainty (accidents, lane closures) | https://doi.org/10.1049/itr2.12494 | — | — | — | Only RL item found that treats the bottleneck location as random. | [SNIP] |
| F5 | Evaluation over day mixes or prevalence (incident share, demand-day distribution) with held-out real days | — | — | — | — | **No RL freeway paper found** that pre-registers a day mix, weights results by prevalence, or evaluates on held-out real demand days (3 queries). | — |

---

## Synthesis

### (i) Where RL demonstrably adds value, and under which conditions

1. **Field-proven, but not for delay: VSL as a warning and harmonisation system (I-24, C1).** The evidence is warning accuracy (+14 points of successful warning rate over a rule-based benchmark), faster reaction to non-recurrent events (< 1 min vs 2.15 min), and preliminary crash reductions. **No field delay or throughput gain has been reported.** The crash figures are before/after, with no control corridor and no tests. So RL's demonstrated field value is **safety and responsiveness**, not mobility.
2. **CAV-based wave smoothing (CIRCLES, Stern, D1–D3).** Energy savings of ≈ 10–20 % are reported at about 4–5 % penetration in simulation. The field "trend" of ≈ 15–20 % comes from a blog, and the 100-AV peer-reviewed outcome analysis was not found. Two caveats:
   - This benefit **does not need a capacity drop**, but it does need waves. The simulators make humans string-unstable on purpose (B8).
   - A non-RL controller (FollowerStopper / PI with saturation) already gives 22–43 % fuel savings on a ring in the field (C7). "Microaccel" (non-RL) is comparable to RL in B8.
3. **RL as a repair or tuning layer for model-based control (A4, E2–E4).** RL reliably fixes a **mis-specified or badly tuned** MPC or feedback controller, with interpretable parameters. The benefit is the **adaptation gain**; against a well-tuned controller on a correct model it is small or untested.
4. **Robustness through training design (B9, D2, E8, B10).** Domain randomisation, curriculum learning and transfer learning give measurable robustness to compliance errors, perturbations, and bottleneck-location uncertainty. In each case the comparison is against **non-robust RL**, not against tuned classical controllers.
5. **Metering vs mainline control on capacity-drop plants.** On the BN4 geometry itself, the best RL **equals** an ALINEA-style traffic-light baseline at 40 % AVs (A2). On a calibrated macro model (BeATS), RL ≈ expert-calibrated ALINEA, and ALINEA itself gains only ≈ 5 % TTS over no control (A1). This agrees with the candidate's KILL: **when the drop is realistic, the mobility headroom is small for every controller, learned or not.** B1 gives the theory: mainline control helps only through the drop.

### (ii) What is weak across the literature

- **Baselines are weak or untuned.** Rule-based VSL that is *worse than no control* (A9); unnamed "state-of-the-art DRL" baselines (D6); headline gains taken against no control only (B10, D4, C2-safety). Tuned PI-ALINEA appears only rarely (A3, A4), and SPECIALIST or MTFC **never** appears as an RL opponent (no paper found).
- **The plant drives the result.** Capacity drops are assumed (15–18 % in B6 and B7) or uncalibrated (A2: IDM with no lane changes; B8: humans string-unstable by design). Only B4 shows a microsimulator calibrated to the field drop, and none of the RL papers found varies the drop magnitude systematically and reports the gain as a function of it (B10 varies it but reports no such curve in what was seen).
- **The metrics can be gamed.** A3 headlines mainline travel time, with ramp delay reported separately as queues; peak medians rather than window totals; the same demand profile for training and testing.
- **Statistics.** Few seeds (15–20); CIs only for the proposed method (A4); no paired tests; field before/after without controls (C1). Abstract numbers inconsistent with the tables (C1: 26 % vs 14 %).
- **No shared freeway benchmark** comparable to RESCO for signals (A5). The ETH replication named in the brief could not be found.
- **Field mobility effects of RL are unmeasured.** I-24 MARVEL reports no delay or throughput; the CIRCLES quantitative analysis is not in peer-reviewed form (as far as this sweep found).

### (iii) Concrete research gaps that could be new for this PhD

For each gap: the evidence that it is open, and what would show that it is *not* open. Each falsification test is a further targeted search; run these on Scopus or Google Scholar before claiming anything.

1. **The gain of RL and of classical controllers as a function of capacity-drop magnitude (an "operating map in Δ").** Sweep the calibrated drop (e.g. 2–20 %) and report the gain of tuned ALINEA / PI-ALINEA, MTFC-VSL and RL at each value, with paired CIs.
   - *Open because:* B1 states the dependence qualitatively; B6 and B7 fix the drop (18.2 %, 15 %); B10 varies scenarios without reporting a gain-vs-drop curve; no RL paper found reports such a curve.
   - *Falsified if:* a paper is found that varies the drop over a range for learned and tuned classical controllers (search "capacity drop magnitude" + "sensitivity" + RL/VSL in TR-C/TR-B 2015–2026).
   - *Fit:* this directly reuses the candidate's T1f/T1g infrastructure, and the KILL becomes a positive methods result.

2. **Re-evaluating the Flow/BN4 RL results on a calibrated plant (a replication).** Retrain the Vinitsky et al. setting (A2) with lane changes on and a field-calibrated drop, and compare against tuned ALINEA.
   - *Open because:* A2 disabled lane changes, did not calibrate the drop, and only *equalled* ALINEA. No replication was found (A11).
   - *Falsified if:* a published replication of the decentralized-bottleneck code with calibrated humans exists (check GitHub forks and citers of doi:10.1145/3582576).

3. **CAV speed control that raises queue speed, to shrink the drop itself.** B3 says the discharge rate rises with speed in congestion. Can a few CAVs raise queue speed and thereby the discharge rate? This is a mechanism different from inflow limiting, and it would be measured on a plant whose speed-dependent drop is calibrated.
   - *Open because:* the wave-smoothing work (C5–C7, D1–D3) targets fuel and oscillation, and the metering/VSL work targets inflow; no item found tests discharge-rate recovery through queue-speed control.
   - *Falsified if:* a paper is found that uses CAVs to raise the queue discharge rate via queue speed (search "queue discharge rate" + "connected automated vehicles" + control).

4. **Fair, pre-registered RL vs SPECIALIST / MTFC for jam waves (VSL), with door-to-door delay including ramps.**
   - *Open because:* SPECIALIST has field results (C8) but no RL head-to-head was found; MTFC is never an RL opponent (Theme E searches); E6 compares only against "existing VSL approaches".
   - *Falsified if:* a paper is found that benchmarks RL against SPECIALIST or MTFC with tuning disclosed.

5. **Adaptation gain of an RL gain-scheduler for ALINEA / PI-ALINEA / MTFC, measured as the share of the fixed-tuned → per-condition-tuned gap closed.**
   - *Open because:* E3 is the closest work (ECC 2026, abstract only) but uses a generic state-feedback controller; no report of "gap closed" against an oracle lookup was found.
   - *Falsified if:* the E3 full text or a T-ITS follow-up reports exactly this oracle-gap metric for ALINEA. **Read E3 in full first.**

6. **Offline RL on the I-24 VSL logs, with off-policy evaluation against the deployed policy.**
   - *Open because:* the dataset and code exist (C3), but no results paper was found.
   - *Falsified if:* a 2025–2026 paper on it appears (watch the Zenodo citations and Lab-Work). Caveat: outside the candidate's SUMO line; a data-access path is needed.

7. **Prevalence-weighted evaluation over realistic day mixes** (recurrent, incident, weather, low-demand days), with held-out real days (e.g. from MnDOT data, already available to the candidate).
   - *Open because:* no RL freeway paper with pre-registered day mixes or prevalence weighting was found (F5). D5 shows single policies decay across scenarios.
   - *Falsified if:* a paper is found that reports controller gains weighted by observed day-type frequencies.

8. **Incident-responsive control with imperfect detection** (detection delay and false alarms in the RL observation), on metering or VSL.
   - *Open because:* F1 measures detection speed but not the control effect; F2 is old work and assumes known incidents; no RL work found models detection uncertainty (Theme F search).
   - *Falsified if:* a paper is found that combines incident detection uncertainty with RL freeway control.

9. **Safety-first VSL under partial compliance, evaluated on surrogate safety with a tuned classical VSL opponent.**
   - *Open because:* C1 assumed 5 % compliance and did not measure it; B9 is about advisories; D4–D6 use no or unnamed baselines.
   - *Falsified if:* a paper is found that sweeps the compliance rate for RL VSL against tuned rule-based VSL with paired statistics.

10. **A small open freeway-control benchmark protocol** (calibrated SUMO plants with known drop, tuned classical opponents, paired-seed statistics, door-to-door delay including ramps). The equivalent of RESCO for freeways.
    - *Open because:* A5 covers signals only; no freeway equivalent was found.
    - *Falsified if:* an existing freeway RL benchmark with tuned classical baselines is found (search "benchmark" + "ramp metering" + "variable speed limit" + SUMO, 2022–2026).

**Most defensible combination for a Sept-2027 timeline (my judgement, not a literature fact):** gaps 1 + 3 + 5 on the existing SUMO line, with 7 as the evaluation frame. This turns the current KILL into a mapped, conditional result and keeps learning in the role where the literature shows it adds value: adaptation and robustness, not raw headroom.

---

## Search log (engine: Claude Code WebSearch unless noted; F = WebFetch; P = arXiv PDF via curl + pdftotext)

1. reinforcement learning ramp metering replication study Hou ALINEA comparison (std)
2. deep reinforcement learning ramp metering compared to tuned ALINEA fair comparison 2023 (std)
3. Vinitsky 2023 optimizing mixed autonomy traffic flow … bottleneck (std)
4. ETH Zurich replication deep reinforcement learning ramp metering reproducibility (std)
5. I-24 MARVEL multi-agent RL variable speed limit field deployment results (std)
6. CIRCLES 100 autonomous vehicles I-24 experiment results energy savings … (std)
7. MegaVanderTest RL traffic smoothing 100 vehicles arXiv results (std)
8. "Traffic Control via Connected and Automated Vehicles: An Open-Road Field Experiment with 100 CAVs" arXiv (std)
9. "From Sim to Real" traffic smoothing cruise controllers deployment I-24 Lichtlé IEEE (std)
10. CIRCLES MegaVanderTest energy analysis results … 2025 (std)
11. "ramp metering" RL "replication" OR "reproduce" ETH research collection thesis (**extended**)
12. Hou ramp metering DRL SUMO replicated "ETH" … (std)
13. Airaldi De Schutter Dabiri RL MPC ramp metering METANET results (std)
14. review RL freeway traffic control VSL ramp metering critical assessment baselines 2023 2024 (std)
15. physics-informed RL ramp metering Han Leclercq TR-C (std)
16. RL VSL capacity drop calibrated simulation sensitivity … (std)
17. capacity drop reproduction microscopic simulation SUMO car-following calibration … (std)
18. VSL benefit depends on capacity drop magnitude analysis mainstream traffic flow control (std)
19. Flow benchmark bottleneck IDM capacity drop unrealistic critique … (std)
20. robustness of DRL freeway control to model mismatch domain randomization VSL transfer (std)
21. Ke Li Cao Liu enhancing transferability DRL VSL transfer learning IEEE T-ITS (std)
22. RL VSL crash risk reduction traffic oscillations freeway Li Liu (std)
23. Accident Analysis and Prevention 2024 DRL VSL continual learning … (std)
24. safe RL ramp metering fallback ALINEA residual policy freeway (std)
25. offline RL freeway ramp metering OR VSL historical detector data (std)
26. offline RL VSL I-24 field data benchmark arXiv 2025 (std)
27. physics-enhanced residual policy learning CAV mixed traffic stop-and-go TR-C (std)
28. Stern dissipation of stop-and-go waves … field experiments fuel (std)
29. DRL CAVs mixed traffic low penetration wave dampening FollowerStopper PI saturation baseline (std)
30. VSL driver compliance rate RL robustness low compliance results (std)
31. DRL VSL real-time crash risk model reward freeway safety AAP (std)
32. Cathy Wu MIT RL Lagrangian control mixed autonomy … (std)
33. RL adaptive tuning of ALINEA gain parameters … (std)
34. comparison MPC versus DRL freeway traffic control VSL METANET benchmark (std)
35. "mainstream traffic flow control" RL OR "MTFC" DRL comparison (std)
36. "Leveraging reinforcement learning for dynamic traffic control: A survey and challenges for field implementation" (std)
37. Han Wang Leclercq 2023 Commun. Transp. Res. … 100104 (std)
38. incident responsive ramp metering OR VSL RL incident detection uncertainty freeway (std)
39. DRL VSL non-recurrent congestion incident lane closure SUMO results baseline (std)
40. DQN VSL urban expressway merge SUMO calibrated … 18.8% … 21.7% (std)
41. Lu Chen Grant-Muller incident-responsive ramp control indirect RL (std)
42. SPECIALIST VSL jam wave RL comparison Hegyi field test (std)
43. Wang Xu Zhang Ran integrated traffic control freeway recurrent bottleneck DRL … (std) — no match
44. field test DRL ramp metering real expressway deployment China results (std)
45. real-world implementation RL VSL motorway Europe Australia field trial (std)
46. first field trial RL ramp metering motorway live traffic evaluation 2024 2025 2026 (**extended**)
47. ElSamadisy Abdulhai DRL freeway controller RM VSL QEW Aimsun results (std)
48. Kušić Ivanjko distributed MARL VSL motorway Mathematics 2021 … (std)
49. comparing RL and model-based controllers for traffic wave dampening … benchmark (std)
50. Srivastava Geroliminis empirical observations of capacity drop … (std)
51. Yuan Knoop Hoogendoorn capacity drop queue discharge rate … (std)
52. ramp metering or VSL benefit varies by day evaluation across many days … (std)
53. RL traffic control evaluation protocol statistical significance seeds baselines "reproducibility" RESCO (std)
54. CAVs as actuators prevent capacity drop bottleneck moving bottleneck Čičić Johansson (std)
55. RL adaptive setpoint critical occupancy ALINEA … PI-ALINEA gain scheduling hybrid (std)
56. DRL freeway control trained historical demand days PeMS evaluation across days … (std)
57. curriculum learning RL ramp metering freeway uncertain bottlenecks IET ITS 2024 (std)
58. ieeexplore 10858625 traffic smoothing 100 AV CIRCLES RL paper title (std) — ID not resolved
59. Flow modular learning framework … IEEE T-RO 2022 DOI (std)
60. safety-oriented VSL DRL crash risk prediction model reward 2023 2024 TR-C OR AAP (**extended**)
61. DRL freeway incident management lane blockage VSL RM secondary crash … (std)
62. multi-objective RL freeway traffic control Pareto front … VSL (std)
63. CAV mobile actuators VSL RL bottleneck capacity drop mixed traffic penetration TR-C (std)
64. Lagrangian control bottleneck throughput AVs realistic capacity drop calibrated human driver model RL gains shrink (std)

**Fetches (F) and PDFs (P).**
- F: arxiv 2503.01017 (html), BAIR blog, arxiv abs 2402.17043, 2012.12104, 1810.10952, 2405.09163, 2311.12261, 1705.01693, 2310.12359, 2512.07417, 2303.03395, 2408.17380, 2608.20858, 2603.25328, 2402.17050, 1310.2658, 1701.08832; PolyU and TU Dresden portals (Han 2022 ×2); TU Delft portal (Sun 2024); Seoultech portal (Kim 2025); UCI ITS (de Souza 2018); PMC (Jerath 2024); GitHub i24-vsl-orl; Research Square rs-10046871 (title only).
- Blocked (403 / refused): sagepub, doaj, TU Delft file, dcsc.tudelft.nl, PubMed (cookie wall), fis.tu-dresden (one page).
- P: 2311.08820v3, 1705.01693, 1701.08832, 2011.00120, 2111.06610, 2402.17050v2, 2012.12104, and the KTH Čičić T-ITS PDF.
