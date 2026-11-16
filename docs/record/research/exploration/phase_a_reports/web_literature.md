# web_literature: published evidence on per-CAV DRL versus tuned controllers (searched 2026-11-10)

Method note. Pages were opened with a fetch tool that answers through a small summarising model; I did not read any paper end to end. Every number below is as that tool (or a pdftotext extract I read directly, marked "direct") returned it, so **everything is [VERIFY]**. "Derived" marks a percentage computed from reported values, not stated by the authors. No local repo files were read.

## 1. CAV longitudinal RL on bottlenecks and ramps

- **Veksler, Hornstein, Wang, Delle Monache, Urieli, 2024, "Cooperative Cruising: RL-Based Time-Headway Control for Increased Traffic Efficiency"**, arXiv preprint. https://arxiv.org/html/2412.02520v3 [SKIMMED]. Plant: SUMO 1.17, 2 km of I-24, 4 lanes + 1 merge lane, 1800 veh/h/lane, CAV 20-100 %, PPO. Action: centralised, headway 1.5-6 s per upstream segment (2 segments), every 2.5 s, only lengthening above the 1.5 s default. Baselines: all-human; best fixed headway from "a parameter sweep" (tuned, one parameter). Gain: "up to a 7% increase in average speed at 100% CAV fraction" multi-lane, "up to a 13%" single-lane; RL gains from 40 % CAV in single-lane. Speed only; no delay or throughput numbers; 500 s runs; one geometry; lane-change model tuned "visually".
- **Elmorshedy, Smirnov, Abdulhai, 2024, "Freeway congestion management on multiple consecutive bottlenecks with RL-based headway control of autonomous vehicles"**, IET ITS 18(6) 1137-1163. https://experts.mcmaster.ca/scholarly-works/3402563 [ABSTRACT-ONLY]. Plant: 3 then 8 consecutive bottlenecks; simulator and penetration not found. Action: one headway per freeway section. Baseline: "shortest headway setting" (tuning not found). Gain: delay "by up to 22.30%" (3 bottlenecks), 18.87 % (8).
- **Same authors, 2023, "Freeway Congestion Management With RL Headway Control of CAVs"**, TRR 2677(7). https://experts.mcmaster.ca/scholarly-works/2893433 [ABSTRACT-ONLY]. Baseline "nondynamic headways"; delay "by up to 57%". Abstract states shorter headways raise capacity but breakdown still occurs at the bottleneck.
- **Vinitsky, Lichtlé, Parvate, Bayen, 2020/2023, "Optimizing Mixed Autonomy Traffic Flow With Decentralized AVs and Multi-Agent RL"**, ACM TCPS. https://ar5iv.labs.arxiv.org/html/2011.00120 [SKIMMED]. Plant: SUMO scaled Bay Bridge, 4→2→1 lanes, AVs hold back inflow (acceleration, 2.5 s). Baselines: no control; hand-designed decentralised ALINEA variant, grid-swept (tuned); centralised ALINEA traffic light. Gain: about 15 % outflow over the feedback controller at 5 % penetration; "our results sharply outperform the feedback controller despite extensive tuning". But: "its performance at a 40% penetration equals the performance of a traffic light based controller"; lane changing disabled in the main results, and "lane changing degrades the performance of our controllers".
- **Kreidieh, Wu, Bayen, 2018, "Dissipating stop-and-go waves in closed and open networks via deep RL"** (ITSC, venue not confirmed on the page). https://sites.google.com/view/itsc-dissipating-waves [ABSTRACT-ONLY]. Single-lane highway with merge; baseline 0 % AV only; 13 % throughput increase from 0 to 10 % penetration.
- **Ha, Chen, Dong, Du, Li, Labi, 2020**, arXiv 2010.05436. https://arxiv.org/abs/2010.05436 [ABSTRACT-ONLY]. GCN+DDPG CAVs versus "a rule-based controller"; design, tuning and numbers not found.

## 2. Extra actuators

- **Pan, Guo, Lam, Zhong, Wang, He, 2021, "Integrated optimal control strategies for freeway traffic mixed with CAVs: a model-based RL approach"**, TR-C 123. https://ira.lib.polyu.edu.hk/handle/10397/98043?mode=full [ABSTRACT-ONLY]. RM + lane-change control + VSL. "The effect of ramp metering is not significant when the penetration rate of CAVs is high enough." Baselines, numbers: not found.
- **ElSamadisy, Smirnov, Wang, Abdulhai, 2025, "DRL Freeway Controller Chooses Ramp Metering Over VSL"**, TRR 2679(8). https://experts.mcmaster.ca/scholarly-works/3596591 [ABSTRACT-ONLY]. Aimsun + QEW ramp; versus regulator-based RM and VSL; numbers not found.
- **Chen et al., 2021**, MARL on-ramp merging, arXiv 2105.05701 [ABSTRACT-ONLY]: "state-of-the-art benchmarks" not named; no numbers.
- No source found that isolates a gain to the extra actuator AND tests a tuned rule on that same actuator, except Veksler (fixed-headway sweep) and Vinitsky (feedback metering).

## 3. Robustness and adaptation

- Vinitsky et al. (above): "the feedback controllers degrade immediately upon penetration rate variation"; yet RL "trained at a 10% penetration rate does significantly worse when deployed at a 40% penetration rate"; domain-randomised "universal" policies trade peak performance for robustness.
- **Jayawardana, Tang, Li, Suo, Wu, 2022, "The Impact of Task Underspecification in Evaluating Deep RL"**, NeurIPS. https://vindulamj.github.io/rl-evaluations [SKIMMED, project page]. 164 intersections; fixed-time and max-pressure outperform all four DRL controllers when evaluated on the family of MDPs; IPPO does not beat an untuned fixed-time controller.
- **Not found:** any freeway study where the conventional controller was re-tuned per condition (the fair comparison). Two targeted searches returned none.

## 4. Hybrids

- **Önür, Dabiri, De Schutter, 2025, "Adaptive Tuning of Parameterized Traffic Controllers via MARL"**, ECC 2026. https://arxiv.org/html/2512.07417v2 [SKIMMED]. Multi-class METANET, weather switch, noisy demand; RL tunes PI-ALINEA and PI route-guidance gains. TTS (veh·h, 100 runs): MARL 7544.1 ± 41.1; single-agent 7583.1 ± 38.1; fixed "hand-tuned" 7656.7 ± 42.5; no control 8054.3 ± 36.8. Derived: 1.47 % below fixed parameters. No statistical test.
- **Airaldi, De Schutter, Dabiri, 2023/2025, "RL with MPC for Highway Ramp Metering"**, IEEE T-ITS 26(5). https://arxiv.org/pdf/2311.08820v3 [SKIMMED, results section direct]. METANET, one metered ramp; MPC started with 30 % model errors and untuned weights. TTS "from around 1100 to 700 veh h (or a 35% reduction)" versus its own deliberately poor start. PI-ALINEA gains "fine-tuned ... via Bayesian Optimisation": it curbs violations but with "higher TTS" (figure only, no number). DDPG: 293 380 parameters versus 53, slower.
- **Sun, Jamshidnejad, De Schutter, 2024, "A Novel Framework Combining MPC and DRL..."**, IEEE T-ITS 25(7). https://research.tudelft.nl/en/publications/a-novel-framework-combining-mpc-and-deep-reinforcement-learning-w [ABSTRACT-ONLY]. RM+VSL; outperforms standalone MPC and DRL on TTS; numbers not found (PDF host refused).
- **Onur, Dabiri, De Schutter, 2026**, hierarchical DRL-MPC, arXiv 2608.20858 [ABSTRACT-ONLY]: qualitative only.
- **Jayawardana, Li, Wu, Farid, Oguchi, 2024, "Generalizing Cooperative Eco-driving via Multi-residual Task Learning"** (ICRA 2024 per search). https://arxiv.org/html/2403.04232v1 [SKIMMED]. Signalised intersections, SUMO. Versus IDM at 20 % AV: RL from scratch emissions +64.08 %, throughput −34.70 %; nominal GLOSA-like rule +13.13 %, −30.07 %; residual MRTL −13.95 %, +7.95 %. The nominal rule is weak.
- **Sheng, Huang, Chen, 2024, "Traffic expertise meets residual RL"**, arXiv 2408.17380 [SKIMMED]: residual on a PI controller beats SAC/PPO/TRPO; the base controller alone is not reported.

## 5. Critical and negative results

- Jayawardana et al. 2022 (above).
- **Ault, Sharon, 2021, "RL Benchmarks for Traffic Signal Control"**, NeurIPS D&B. https://people.engr.tamu.edu/guni/papers/NeurIPS-signals.pdf [SKIMMED, direct]. "algorithms that claim state-of-the-art performance struggle in realistic traffic scenarios"; IPPO "demonstrates significant instability"; "Deep RL methods should give increased attention to hyper-parameter sensitivity".
- **Riehl, Kouvelas, Makridis, 2026, "sumoITScontrol"**, SUMO User Conference. https://eclipse.dev/sumo/documents/2026/preprints/pre-print-3284.pdf [SKIMMED, direct]. "many published control studies still rely on single-run evaluations and project-specific baseline implementations"; benchmarking against established baselines "is often limited".
- **Henderson et al., 2018, "Deep RL that Matters"**, AAAI. https://arxiv.org/abs/1709.06560 [ABSTRACT-ONLY].
- **El-Baklish, Kouvelas, Makridis, 2024, "A Variable Time Gap Strategy for ACC"**, arXiv 2402.14110. https://arxiv.org/html/2402.14110v2 [SKIMMED]. Non-learning H∞ variable gap versus calibrated constant gap, SUMO single-lane on-ramp: "improved traffic outflow by 1.05% on average" at 10 % penetration. The tool flagged an inconsistency between the conclusion and Table 1.

## 6. Wave damping with few AVs

- **Lichtlé, Jang, Vinitsky, Shah, Lee, Bayen, 2025**, BAIR blog on MegaVanderTest. https://bair.berkeley.edu/blog/2025/03/25/rl-av-smoothing/ [SKIMMED, not peer-reviewed]. Simulation: "up to 20%" fuel savings "with fewer than 5% of AVs"; field: "a trend of 15 to 20% of energy savings around our controlled cars". No travel time, delay or throughput; no conventional-controller comparison.
- **Lee et al., 2024/2025, "Traffic Control via CAVs: An Open-Road Field Experiment with 100 CAVs"**, IEEE CSM 45(1). https://arxiv.org/html/2402.17043v1 [SKIMMED, both halves]. No numeric field result on energy, throughput or travel time; controllers engaged "38% of all times" (11/16), "78%" (11/17); wave damping qualitative; "it was not expected that they would completely smooth out all traffic waves".
- **Lichtlé et al., 2023**, ITSC, arXiv 2401.09666 [ABSTRACT-ONLY]: one-lane trajectory replay, fuel savings over 15 % at 4 % penetration; no named baseline.
- **Jang et al., 2024**, arXiv 2402.17050 [ABSTRACT-ONLY]: no numbers in the abstract.
- **Stern et al., 2018**, TR-C 89, arXiv 1705.01693 [ABSTRACT-ONLY]: ring, >20 vehicles, one AV; no numbers in the abstract.
- Reading: yes, reported benefits are energy and smoothness; delay or throughput gains appear only against no control (Kreidieh) (INFERENCE from the sources above).

## Unverified leads (no numbers)

Frejo & De Schutter 2021, LB-TFC Parts 1-2 (abstract page only: LB-TFC "close to the optimal one" and better than MTFC+PI-ALINEA; the ≈ 2-3 % / ≈ 9 % figures in the project CLAUDE.md could not be checked); Belletti et al. 2017 (arXiv 1701.08832; abstract has no ALINEA comparison); Join, Abouaïssa, Fliess 2021 (arXiv 2111.06610; a DRL-vs-ALINEA remark seen only in a search snippet); Agarwal et al. 2021 (arXiv 2108.13264); Cui et al. 2017; Hayat et al. 2022; Kušić et al. 2020/2021 reviews; a 2017-2025 CAV speed-control review (HTTP 429); arXiv 2401.11148, 2409.15595, 2412.04341, 2110.08124, 2310.16748; Vinitsky et al. 2018 ITSC; Flow benchmarks (CoRL 2018; no tuned-baseline result found); Elmorshedy 2024 DOAJ page (403).

## Closing

**(a) Best-supported route (INFERENCE).** Change the plant/actuator so the decision is spatially targeted and coordinated: section-level or centralised headway commands upstream of a merge (Veksler; Elmorshedy), or CAVs acting as a moving ramp meter (Vinitsky). These are the only freeway cases found where RL beat a tuned or shortest-headway baseline using the same actuator. Note the winning action is *lengthening* headway before the merge from segment-level state, not picking a short headway from local state: consistent with H1 and H3. Second: hybrids, which reliably beat their base controller, but the size tracks how badly the base is tuned or modelled (35 % from a deliberately broken MPC; 1.47 % derived over hand-tuned PI gains). Disturbance route: support is thin; no per-condition re-tuned baseline exists, and RL itself degraded under penetration shift. Improving the learner alone: no supporting evidence found; likely to fail.

**(b) Realistic gain against tuned baselines (INFERENCE).** About 1-2 % TTS (Önür, derived; El-Baklish 1.05 % outflow for a non-learning adaptive gap) to 7 % average speed (Veksler, 100 % CAV, multi-lane). The 15-22 % figures (Vinitsky, Elmorshedy) are "up to", abstract-level or with lane changing disabled. Plan for low single digits on delay.

**(c) Strongest cautions.**
1. Jayawardana et al. 2022: fixed-time and max-pressure beat four DRL methods once evaluation covers a family of scenarios (supports H5).
2. Vinitsky et al.: the 15 % edge over a tuned feedback rule shrinks to parity with a traffic-light ALINEA at 40 % penetration and degrades with lane changing.
3. MegaVanderTest (Lee et al.; BAIR blog): the largest field test reports energy trends only, no measured delay or throughput benefit, no tuned-controller comparison (INFERENCE: consistent with H2, the edge is in smoothness, not delay).
