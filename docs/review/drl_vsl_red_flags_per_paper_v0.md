# DRL-for-VSL literature: per-paper red-flag profiles (v0, 2026-10-04)

Companion to `drl_vsl_reality_check_v0.md`. One profile per paper #1–#39 of `docs/plans/vsl_hybrid_screen_v0.md` §3.2.

## How these profiles were made, and how far to trust them

- **Who read what.** Seven reader agents re-read the 39 local full texts in `docs/knowledge_base/` on 2026-10-04 under one brief: fixed flag codes, a location for every claim, and a verbatim quote for every flag. #7, #34 and #39 had a deeper pass (claim audit and reproduction spec).
- **Quotes.**
  - `Q[fNNN pN]` quotes are **machine-verified**: all 354 were found verbatim on the cited PDF page (whitespace and hyphenation ignored), using `docs/review/verify_quotes.py`.
  - `QI[...]` quotes (10) were read from rendered page images and are **not machine-verified** [VERIFY].
- **Page numbers.** `p. n` is the **PDF page index** (1-based), not the journal's printed page number.
- **Computed numbers.** "(c.)" means computed from printed values, with the arithmetic shown. I re-did these by hand only for #7 (Table IV, rendered), #24 (Table 5) and #34 (Fig. 12 values). Everything else is the reader agents' arithmetic: [VERIFY] before quoting it in a paper.
- **Figure readings.** Values read off figures (marked "fig.", "visual" or "approx.") are approximate.
- **Language.** The profiles describe what each paper does. They make no judgement about intent.

## Flag codes

| Code | Meaning |
|---|---|
| **B1** | strongest comparator is no control (NC) and/or other RL only |
| **B2** | classical comparator present, but its parameters are copied, set by hand, not stated, or tuned by an unstated method |
| **B3** | comparator tuned, but on the test scenario(s) |
| **B4** | asymmetric comparison: RL gets more actuators, information or lanes |
| **E1** | train = test (no held-out demand or seeds) |
| **E2** | hyperparameters, checkpoint or runs selected on test results |
| **S1** | single, "representative" or best run |
| **S2** | replications or seeds not stated |
| **S3** | no dispersion or test for the headline gain |
| **M1** | metric scope: origin or insertion queues excluded or unstated; throughput not reported |
| **M2** | headline metric is a proxy, or a trade-off is hidden |
| **P1** | macroscopic model with the capacity drop as an equation parameter |
| **P2** | microsimulation: capacity drop not demonstrated, or no calibration, or teleports and collisions not reported |
| **N1** | numerical inconsistency |
| **R1** | reproducibility gaps (code, parameters) |
| **C1** | claims exceed the evidence |
| **G+** | good practice |

## File map (text-file id → PDF under `docs/knowledge_base/`)

| id | PDF |
|---|---|
| f001 | `papers_RL_VSL/A case for the adoption of decentralised reinforcement learning for the control of traffic flow on South African highways.pdf` |
| f002 | `papers_RL_VSL/Accounting for dynamic speed limit control in a stochastic traffic environment A reinforcement learning approach.pdf` |
| f003 | `papers_RL_VSL/Adaptive Coordinated Variable Speed Limit between Highway Mainline and On-Ramp with Deep Reinforcement Learning.pdf` |
| f004 | `papers_RL_VSL/Adaptive Highway Traffic Management A Reinforcement Learning Approach for Variable Speed Limit Control with Random Anomalies.pdf` |
| f005 | `papers_RL_VSL/A lane-level variable speed limit approach based on twin delayed deep deterministic policy gradient in a connected automated vehicle environment.pdf` |
| f006 | `papers_RL_VSL/A new reinforcement learning-based variable speed limit control approach to improve traffic efficiency against freeway jam waves.pdf` |
| f007 | `papers_RL_VSL/A New Solution for Freeway Congestion_ Cooperative Speed Limit Control Using Distributed Reinforcement Learning.pdf` |
| f008 | `papers_RL_VSL/A Novel Framework Combining MPC and Deep Reinforcement Learning With Application  to Freeway Traffic Control.pdf` |
| f010 | `papers_RL_VSL/A variable speed limit control approach for freeway tunnels based on the.pdf` |
| f012 | `papers_RL_VSL/Cooperative Multi-Agent Reinforcement Learning for Large Scale Variable Speed Limit Control.pdf` |
| f013 | `papers_RL_VSL/Coordinated Variable Speed Limit Control for Consecutive Bottlenecks on.pdf` |
| f014 | `papers_RL_VSL/Decentralised reinforcement learning for ramp metering and variable speed limits on highways.pdf` |
| f016 | `papers_RL_VSL/Deep Q‐network learning‐based active speed management under autonomous driving.pdf` |
| f017 | `papers_RL_VSL/Deep Reinforcement Learning Approach for Lagrangian Control_ Impr.pdf` |
| f018 | `papers_RL_VSL/Deep Reinforcement Learning Based Lane-level  Variable Speed Limit Control.pdf` |
| f019 | `papers_RL_VSL/Differential variable speed limits control for freeway recurrent bottlenecks via deep actor-critic algorithm.pdf` |
| f020 | `papers_RL_VSL/Dynamic speed harmonization for mixed traffic flow on the freeway using deep.pdf` |
| f021 | `papers_RL_VSL/Enhancing Transferability of Deep Reinforcement  Learning-Based Variable Speed Limit Control Using Transfer Learning.pdf` |
| f023 | `papers_RL_VSL/Extended Variable Speed Limit control using Multi-agent  Reinforcement Learning.pdf` |
| f025 | `papers_RL_VSL/Imagination-Augmented Reinforcement Learning Framework for Variable Speed Limit Control.pdf` |
| f026 | `papers_RL_VSL/Impact of deep reinforcement learning on variable speed limit strategies in connected vehicles environments.pdf` |
| f027 | `papers_RL_VSL/Influence of Variable Speed Limit Control on Fuel and Electric Energy Consumption, and Exhaust Gas Emissions in Mixed Traffic Flows.pdf` |
| f028 | `papers_RL_VSL/Integrated Traffic Control for Freeway Recurrent Bottleneck Based on Deep Reinforcement Learning.pdf` |
| f029 | `papers_RL_VSL/Lagrangian Control through Deep-RL Applications to Bottleneck Decongestion.pdf` |
| f030 | `papers_RL_VSL/MARVEL Bringing Multi-Agent Reinforcement- Learning Based Variable Speed Limit  Controllers Closer to Deployment.pdf` |
| f031 | `papers_RL_VSL/Multi-Agent Deep Reinforcement Learning for Multi-Lane Freeways Differential Variable Speed Limit Control in Mixed Traffic Environment.pdf` |
| f032 | `papers_RL_VSL/Multi-agent Reinforcement Learning-Based Variable Speed Limit Strategy by Leveraging Connected and Autonomous Vehicles in Mixed Traffic Flow.pdf` |
| f034 | `papers_RL_VSL/Reinforcement learning based mainline dynamic speed limit adjustment of.pdf` |
| f035 | `papers_RL_VSL/Reinforcement Learning Based Variable Speed Limit Control for Mixed Traffic Flows Using Speed Transition Matrices for State Estimation.pdf` |
| f036 | `papers_RL_VSL/Reinforcement Learning Based Variable Speed Limit Control Strategy to Reduce Traffic Congestion at Freeway Recurrent Bottlenecks.pdf` |
| f037 | `papers_RL_VSL/Reinforcement Learning Based Variable Speed Limits Control to Reduce Crash Risks Near Traffic Oscillations on Freeways.pdf` |
| f038 | `papers_RL_VSL/Safety-oriented dynamic speed harmonization of mixed traffic flow in nonrecurrent congestion.pdf` |
| f039 | `papers_RL_VSL/Speed harmonisation and merge control using connected automated vehicles on a.pdf` |
| f040 | `papers_RL_VSL/Traffic flow optimization A reinforcement learning approach.pdf` |
| f041 | `papers_RL_VSL/Variable Speed Limit Control Based on Deep Reinforcement Learning_ A Possible Implementation.pdf` |
| f042 | `papers_RL_VSL/Variable speed limit control strategy for freeway tunnels based on a multi-objective deep reinforcement learning framework with safety perception.pdf` |
| f043 | `papers_RL_VSL/Variable Speed Limit Intelligent Decision-Making Control Strategy Based on Deep Reinforcement Learning under Emergencies.pdf` |
| f050 | `papers_RL_RM/An Eligibility Traces based Cooperative and Integrated Control Strategy for Traffic Flow Control  in Freeways.pdf` |
| f052 | `papers_RL_RM/An Integrated Control Method of Highway Ramp Metering and Variable Speed Limit based on the Internet of Vehicles.pdf` |

---

### #1 Walraven 2016, EAAI 52:203-212 — file f040
- Structure / simulator / network: direct tabular/NN Q-learning; speed limits {60,80,100,120} on sections 2-6, changed every 5 min; METANET, 8 sections x 3 km, 2 lanes, 1 h episodes, 3 deterministic demand scenarios (p. 5, Sec. 7.1; Fig. 7 p. 7). Additional SUMO test near Eindhoven (p. 8, Sec. 7.7).
- Headline claim (abstract, p. 1):
  Q[f040 p1]: "the resulting policies signiﬁcantly reduce trafﬁc congestion under high trafﬁc demand"
- Strongest comparator; how set: "best fixed speed limit assignment" = enumeration of all 13-step action sequences with |a_i - a_(i+1)| <= 20 on the same scenario (p. 6, Sec. 7.2). This is an in-sample, open-loop, time-varying oracle, not a feedback controller. No ALINEA/Carlson/SPECIALIST/MPC comparator anywhere.
  Q[f040 p6]: "The dashed horizontal lines in Fig. 8 represent the number of"
- Gain vs strongest, recomputed (veh.h, lower is better; Table 3 p. 7, multi-scenario policy vs best fixed): S1 (492.1-491.6)/491.6 = +0.10 % (RL worse); S2 (524.3-511.2)/511.2 = +2.56 %; S3 (516.5-514.5)/514.5 = +0.39 % (c.). Single-scenario NN+pred (Table 2): +0.67 %, +2.74 %, +0.37 % (c.). Vs no control (Table 3): (740.8-492.1)/740.8 = 33.6 %, 45.1 %, 32.8 % (c.).
- Evaluation protocol: each policy is learned and evaluated on the same scenario; Table 3 policies trained on the three scenarios and evaluated on the same three. +/- in Tables 2-3 is not defined in the text (I searched the whole file for "standard dev", "confidence": absent); the 20 policies per cell are 20 training runs (p. 6), evaluation itself is deterministic.
  Q[f040 p6]: "evaluated in a simulation run with the same trafﬁc scenario"
- Flags:
  - **B1** No classical controller; comparators are no control and an in-sample oracle. p. 6-7.
    Q[f040 p7]: "Baseline (no control) 740.8 954.5 768.6"
  - **E1** Train = test for the headline tables (Tables 2, 3); SUMO test (p. 8) is the only out-of-model check and has no classical comparator, only no control.
    Q[f040 p6]: "We learn and evaluate policies using the"
  - **C1** "significant" improvement and "predictions improve policy quality" are stated without a test. Table 2: NN S2 520.6 +/- 8.6 vs NN+pred 525.2 +/- 23.2 (pred worse in the mean); TC S2 549.1 vs 546.4 (diff 2.7 << sd 16-26).
    Q[f040 p1]: "of trafﬁc predictions improves the quality of the resulting policies"
  - **S3** No CI or test; Fig. 8 boxplots over 20 policies only (image, p. 7).
  - **M1** Throughput not reported; capacity drop is not discussed (word "capacity drop" absent from the file), so T1 of your protocol is not addressed.
- Good practice (G+): vehicle-hours in Eq. 6 (p. 4) sums section vehicles and on-ramp queues w_i, so queue time is in the cost; 20 independently trained policies per cell with dispersion; multi-scenario training; noise robustness with 50 runs per level, and it reports that above 10 % noise the policies can exceed the no-control cost (p. 8); discusses limits (small network, no flow control, p. 8-9). The authors claim "close to" the oracle, not better.
- Screen row check: agrees ("RL loses", train = test). Imprecise: lower bound is +0.10 % (S1), not +0.4 %; "best fixed assignment" is a 13-step time-varying oracle, not a fixed limit.
- Not checked / uncertain: SUMO result (Fig. 11, p. 8) is image-only and was not rendered; no code statement found.

### #2 Zhu & Ukkusuri 2014, TR-C 41:30-47 — file f002
- Structure / simulator / network: direct R-MART (tabular average-reward RL), per-link speed limits 20-80 mph (V0=20, I=7.5, A=8), authors' link-based dynamic network loading model (CTM-like, 3-part links), Sioux Falls reconstruction, 547 links, 346 nodes, 371 links controlled, 3600 s, lognormal random demand and random link capacities (p. 13-14, Sec. 4.1; Table 1 p. 12).
- Headline claim (abstract, p. 1):
  Q[f002 p1]: "Results show that the total travel time and emissions (in terms of CO) are reduced by"
  (continues on the next line: "around 18% and 20% compared with the base case of non-speed limit control.")
- Strongest comparator; how set: only no control (real-world posted limits).
  Q[f002 p15]: "Note that the results of the non-speed limit control case are set as the base for comparison."
- Gain, recomputed: 1 - 0.82 = 18 % TTT, 1 - 0.80 = 20 % CO, read as "fluctuating within a small range of 0.82/0.80" from run 80 on (p. 15). No table of absolute TTT/emission exists (searched: only Table 1 = parameters). Fig. 10 (p. 14, image) shows the ratio scattered roughly 0.77-0.84 over runs 80-100 (QI, read by eye).
- Evaluation protocol: Fig. 10 plots TTT and CO of each of 100 learning runs, relative to no control (first point = 1.0). Each run has new random demand and capacity draws; whether the no-control base is one draw or an average is not stated. The "implementation phase" (low epsilon) is described (p. 10) but never reported separately. No replications, no dispersion, no held-out scenario.
  Q[f002 p14]: "In this study, we set the maximum iteration as 100."
  Q[f002 p15]: "the result is not converging to a stable point."
- Flags:
  - **B1** Comparator is no control only. p. 15.
  - **E1 / S1 / S3** Result = the learning trajectory itself on the training environment; one trajectory, no CI. p. 14-15.
  - **B4 / P1** The RL may raise limits above the posted ones (up to 80 mph) and the model's free-flow speed equals the limit, so some gain can come from raising limits, not harmonisation; not separated. p. 15.
    Q[f002 p15]: "For some link, it is better to increase the speed limit for some period of time."
  - **C1** Abstract says the optimal scheme is obtained, while Sec. 4.2 says it does not converge.
    Q[f002 p1]: "the optimal speed limit scheme is obtained by applying the R-Markov"
  - **M1** Throughput not reported. Partly mitigated: demand stops 100 steps before the end so the network clears (p. 14).
  - **R1** No code; schedule constants unspecified.
    Q[f002 p17]: "A and B are scalars"
- Good practice (G+): stochastic demand and supply (20 % deviation); network cleared at the end so TTT is not truncated; honest caveat that findings "cannot be generalized to all the links" (p. 15-16); real topology at scale.
- Screen row check: agrees (NC only, no separate test). Add: "-18 %" is a band read from a figure, not a table value.
- Not checked / uncertain: Fig. 10 values are read by eye from a rendered page; emission formula Eq. 31 is garbled in the text layer.

### #3 Li Z. et al. 2017, IEEE T-ITS 18(11):3204-3217 — file f036
- Structure / simulator / network: direct tabular Q-learning with Softmax; state = 3 densities (4851 states), actions 20-65 mph step 5, 30 s control; modified CTM with inverse-lambda fundamental diagram (capacity drop 8.1 %, calibrated on PeMS), I-880 6-mile merge bottleneck; 4 h runs with 30 min warm-up (p. 6-8, 10).
- Headline claim (abstract, p. 1):
  Q[f036 p1]: "strategy reduced the system travel time by 49.34% in the stable"
- Strongest comparator; how set: Carlson-type two-loop feedback VSL. Method, data and numeric gains are not given in the paper (searched for K_I/K_P values: none printed).
  Q[f036 p10]: "based VSL algorithm were calibrated to optimize the control"
  Q[f036 p10]: "were tested but the overshooting cannot be fully prevented."
- Gain, recomputed: stable: 1046 -> 530 veh.h, (1046-530)/1046 = 49.3 % (c., p. 10); FB 24.96 % -> FB TTT = 1046 x (1-0.2496) = 784.9 (c.); QL vs FB (784.9-530)/784.9 = 32.5 % (c.). Fluctuating (absolute TTT only in Fig. 10): (0.8898-0.7816)/0.8898 = 12.2 % (c.). With the 10 mph/min rate limit (p. 11): 43.25 vs 16.24 gives (0.8376-0.5675)/0.8376 = 32.2 % (stable) and 14.46 vs 6.91 gives 8.1 % (fluctuating) (c.).
- Evaluation protocol: state table built from one week of field data (p. 7); the demand used to train the Q-values is not stated (searched Sec. IV); test = two demand profiles (Fig. 7, p. 8). Number of replications/seeds: not stated. No dispersion.
- Flags:
  - **B2** FB parameters "calibrated to optimize" with no method, scenario or values; footnote 1 shows several settings were tried on the evaluation scenarios. p. 10.
  - **E2 / C1** Headline uses the 30 s, no-rate-limit setting chosen after trying 30 s to 5 min; reward incentive/penalty "selected from multiple tests". p. 9-10.
    Q[f036 p9]: "selected from multiple tests."
  - **E1 / S2 / S3** Whether training and test demand differ is not stated; no seeds, no CI, "significantly" without a test. p. 10.
    Q[f036 p10]: "gested that the proposed QL-based VSL strategy significantly"
  - **P1** Capacity drop is a model parameter; the feedback loop and QL are both judged inside that model. p. 7.
    Q[f036 p7]: "To model the capacity drop,"
  - **M1** TTT is vehicles in the system; origin queues excluded by assumption; throughput not reported. p. 4.
    Q[f036 p4]: "either mainline or on-ramp did not spread to the origins, and so"
  - **B4 (low confidence)** QL state includes ramp and upstream densities; FB uses bottleneck density only. p. 3, 5.
    Q[f036 p5]: "loop. The primary controller compared the measured density"
- Good practice (G+): CTM calibrated on PeMS (capacity 1750 veh/h/ln, drop 8.1 %, flow error 12.6 %, speed error 10.8 %, p. 7); both a stable and a fluctuating demand; rate-limited variant reported (p. 11); limits of RL (black box, transferability) stated (p. 12).
- Screen row check: agrees (-32.5 % / -12.2 %, replications not stated). Add that 49.34 % is the best-case, no-rate-limit configuration.
- Not checked / uncertain: Fig. 10 (absolute TTT for the fluctuating case) is image-only, not rendered.

### #4 Li Z. et al. 2021, IEEE ITS Mag. (Winter 2021, pp. 64-70) — file f037
- Structure / simulator / network: direct tabular Q-learning (Softmax); objective = total crash risk from a logistic rear-end risk model (not delay); state = 3 section densities (3375 states); actions 20-65 mph, max change 10 mph/min; modified CTM (capacity drop 6.7 %, stochastic bottleneck sending flow to create oscillations), I-880, 100 min runs (p. 3-4).
- Headline claim (abstract, p. 2):
  Q[f037 p2]: "successfully reduced the crash risks by 19.4%."
- Strongest comparator; how set: authors' own GA-optimised VSL strategy [31]; tuning scenario not stated here.
  Q[f037 p5]: "optimal strategy applied a genetic algorithm to find the"
- Gain, recomputed (Table I, p. 5): RL vs NC (1075.9-867.6)/1075.9 = 19.4 % (c.); GA vs NC (1075.9-825.2)/1075.9 = 23.3 % (c.); RL vs GA = (867.6-825.2)/825.2 = 5.1 % MORE risk (c.). TTT: 197.3 -> 200.3 (+1.5 %, c.), GA 200.4 (+1.6 %).
- Evaluation protocol: training reward is the test metric on the same CTM scenario; number of runs not stated although the model is stochastic; Table I has single values.
  Q[f037 p3]: "The reward function was calculated as the decrease"
- Flags:
  - **E1** Reward = relative crash-risk reduction against the no-control run of the same scenario; test on that scenario. p. 3, 5.
  - **S2 / S3** Runs/seeds not stated; no dispersion. p. 5.
  - **M2** Headline is a surrogate crash-risk index (%/mi/h), not crashes; TTT is slightly worse (disclosed). p. 5.
  - **B4** Table II: RL with continuous learning (18.0/16.1/12.8 % at 5/10/15 mph overspeed) vs GA strategy (18.62/13.3/8.1 %). The RL is re-learned on 10 h of overspeed rewards; no re-optimisation of the GA strategy is mentioned (not found in text). At 5 mph the GA is better. p. 6.
    Q[f037 p6]: "VSL strategy in [29] 18.62 13.3 8.1"
  - **C1** "optimal" RL strategy while the GA strategy is better.
    Q[f037 p6]: "This study proposed an optimal RL-based VSL control strategy"
  - **N1 (label only)** Table headers cite "[29]" for the GA strategy, text cites [31]; [29] in the reference list is a different paper. p. 5-6, 7.
- Good practice (G+): states plainly that the GA strategy beats the RL on crash risk and that TTT rises by 1.5 % (p. 5); crash model from 3 years of crashes; CTM calibrated on one month of PeMS (p. 4); limits stated (p. 6).
- Screen row check: agrees (RL loses on TCR 867.6 vs 825.2). Add: the comparator is the authors' own GA strategy, the objective is crash risk, and TTT is also worse.
- Not checked / uncertain: the GA strategy's tuning data are in [31], which I did not read.

### #5 Han Y., Hegyi et al. 2022, TR-C 144:103900 — file f006
- Structure / simulator / network: direct tabular Q-learning, iterative offline/online scheme using one-step synthetic transitions from an extended CTM; action = (speed 50 or 60 km/h, upstream boundary cell); "real" process = METANET with VSL extension, 7.5 km, 25 cells, 3 lanes, jam waves triggered at the downstream boundary, stochastic FD parameters (sd 2 %) and demand (sd 5 %) (p. 11-12). Comparators: SPECIALIST, MPC on the extended CTM, DDQN variants.
- Headline claim (Sec. 5.2, p. 16):
  Q[f006 p16]: "In contrast, the proposed VSL control approach reduces the average total travel delay by 35.1% when"
  (the abstract itself claims "significantly reduces the exploration and learning costs").
- Strongest classical comparator; how set: MPC (Han 2017b) with the extended CTM as prediction model, "calibrated with the online simulation data", horizon 20 min, step 30 s, demand forecast = constant last-15-min mean; weights not printed (refers to the earlier paper) (p. 16). SPECIALIST tuned by heuristic rules / trial and error.
  Q[f006 p16]: "Model parameters are calibrated with the online simulation"
  Q[f006 p14]: "based on heuristic tuning rules using offline traffic data."
- Gain, recomputed (delay reduction vs no VSL: RL 35.1, MPC 25.9, SPECIALIST 15.5, p. 16-17): RL vs MPC (0.741-0.649)/0.741 = 12.4 %; vs SPECIALIST (0.845-0.649)/0.845 = 23.2 % (c.). The 35.1 % holds for runs with eta > 0.8 only; the average over the whole training is 31.3 % (p. 15), giving (0.741-0.687)/0.741 = 7.3 % vs MPC (c.). Comparators were run on 100 separate runs, not paired with the RL runs.
- Evaluation protocol: RL learns online on the same stochastic process model it is scored on (100 online runs per iteration, mean 15.9 iterations, so about 1590 runs (c.)); whole experiment repeated 20 times; stop rule on state coverage (eta > 0.8), not on delay. Dispersion (whisker plot) shown for RL only (Fig. 10, image, p. 15).
  Q[f006 p15]: "The average number of iterations in the"
- Flags:
  - **E1** No held-out runs; scoring runs are the learning runs (by design of online learning). p. 15.
  - **B2** SPECIALIST tuned by trial and error; a second parameter set was tried (p. 16); MPC weights not printed. p. 21, 16.
    Q[f006 p21]: "Based on trial-and-error tuning,"
  - **B4** RL adapts on about 1590 process runs; comparators get a single calibration. p. 15-16.
  - **S3** No CI/test for RL-vs-MPC or RL-vs-SPECIALIST; comparators reported as one mean. p. 16-17.
  - **M1** Delay is time in the stretch minus free-flow time; throughput not reported; origin queue not part of the stretch. p. 15.
    Q[f006 p15]: "total time spent by all vehicles in the freeway stretch and the sum of all the vehicles"
  - **P1** Process model is METANET; full compliance assumed; jam wave artificially triggered. p. 12.
    Q[f006 p12]: "We assume that the drivers fully comply with the speed limit control."
  - **C1** "significantly reduces ... costs" without a test (abstract p. 1).
- Good practice (G+): deliberate model mismatch (extended CTM vs METANET) and the MPC is not given the true model; 20 repeats with randomised FD parameters and demand; reports exploration cost and the share of runs where VSL worsened delay (32.6 % vs 17.9 %, p. 17); states that the policy may be suboptimal (p. 20); tests a second SPECIALIST tuning (p. 16).
- Screen row check: agrees (35.1/25.9/15.5; -12.4 % vs MPC; -23 % vs SPECIALIST; needs 80 % coverage). Add: the -12.4 % is final-stage versus 100 unpaired comparator runs; whole-training average gives -7.3 % (c.).
- Not checked / uncertain: Figs. 10, 13, 16 (dispersion, learning curves) are images and were not rendered.

### #6 Zheng S. et al. 2023, J. Adv. Transp. 2023:4419907 — file f013
- Structure / simulator / network: direct MADDPG (centralised training, decentralised execution), 4 agents, speed limits {5..65} mph, 30 s; modified CTM with capacity drop 7.6 % (Table 1, p. 7), 4.2-mile 4-lane freeway, 4 merge on-ramps, 42 cells; static and dynamic 1 h demand scenarios (p. 6-8). Comparators: no control, independent DDPG (ISARL), local feedback VSL.
- Headline claim (abstract, p. 1):
  Q[f013 p1]: "18.01% and 17.07% in static and dynamic trafc scenarios, respectively."
  These are reductions vs NO control (Table 3, p. 14).
- Strongest comparators; how set: classical = local feedback VSL, parameters printed but taken from ref. [33]; re-tuning for this network not stated. RL = ISARL, which did not converge.
  Q[f013 p5]: "limit was rounded to the nearest 5 mph. More details can be"
  Q[f013 p8]: "ISARL-VSL did not converge during training, and its total"
- Gain, recomputed (Table 3, p. 14): vs FB static (263.87-235.19)/263.87 = 10.9 %, dynamic (300.50-265.33)/300.50 = 11.7 %; vs ISARL static (247.23-235.19)/247.23 = 4.9 %, dynamic (293.39-265.33)/293.39 = 9.6 % (c.). Table 3 percentages agree with the TTS values to within rounding (static MARL gives 18.02 %).
- Evaluation protocol: training "in a predetermined dynamic traffic scenario"; test = static and dynamic scenarios; whether the test dynamic profile differs from the training profile is not stated. Fig. 6(d) shows training TTS about 309 (MARL) and 333 (ISARL) veh.h (QI), which differ from the test values, unexplained. Ten trials averaged; what varies between trials is not stated; no sd/CI. Checkpoint used for testing not stated.
  Q[f013 p11]: "ten trials, and subsequently, the outcomes were subjected to"
- Flags:
  - **B2** FB gains from a literature source, no re-tuning stated; FB is worse than no control around 0.3 h in the dynamic case (p. 11). p. 5.
  - **B4** Agents also observe mainline and ramp demand (d_up, d_ramp); the FB controller uses density only. p. 3, 5.
    Q[f013 p3]: "of six components (di up , di ramp , ki down , ki up , ki ramp , and SLi t )."
  - **P1** Capacity drop is a CTM parameter; Table 4 (static, vs no control) gives (275.93-236.38)/275.93 = 14.3 % at 5 % drop and (362.34-261.17)/362.34 = 27.9 % at 15 % drop (c.): the gain scales with the built-in parameter. p. 16.
  - **S3 / C1** Means only, no test; "significantly outperformed". p. 17.
    Q[f013 p17]: "the MARL-VSL strategy signifcantly outperformed other"
  - **E2 (uncertain)** Reward constants "meticulously determined through multiple simulation rounds"; checkpoint choice not stated. p. 3, 7.
  - **M1** TTS = vehicles in the freeway system; ramp queues and throughput not reported. p. 7.
  - **R1** No code; data "upon request"; network architecture not stated (searched layer/neuron/hidden: absent). p. 17.
    Q[f013 p17]: "Te data supporting this study can be obtained from the"
- Good practice (G+): ISARL uses identical state/action/reward, which isolates coordination (p. 5); FB baseline restricted to density-based design for fairness (p. 5); 10 trials averaged; sensitivity to capacity drop 5-15 % (Table 4); reports where FB hurts (p. 11); speed and speed-sd in Table 2 next to TTS.
- Screen row check: agrees on -10.9 / -11.7 % (c.). Imprecise: "params not re-tuned" should read "parameters from ref. [33], tuning for this network not stated"; the strongest comparator overall is ISARL (RL), where the gain is 4.9 / 9.6 % (c.).
- Not checked / uncertain: Fig. 6 values are read by eye; Table 4 does not contain FB or ISARL.

### #7 Ke et al. 2021, IEEE T-ITS 22(7) — file f021

- **Structure / simulator / network:**
  - Direct DRL (DDQN), with transfer learning between scenarios.
  - Simulator: a custom macroscopic CTM with an inverse-λ capacity-drop fundamental diagram (p. 5, Eq. 7).
  - Network: I-880 northbound (Oakland), merge bottleneck at the W Tennyson Rd on-ramp (p. 5, Fig. 6 p. 6).
- **Headline claim:**
  - Source scenario: TTS reduced by 50.47 % with the stable demand and by 35.53 % with the fluctuating demand (p. 7, Sec. V-A).
  - Abstract range: 26.02–67.37 % for the stable demand and 21.31–69.98 % for the fluctuating demand, over the target scenarios (p. 1).
  Q[f021 p7]: "a 50.47% reduction in TTSs and a 35.53% reduction in TTSf ."
  Q[f021 p1]: "26.02% to 67.37% with the stable testing demand and 21.31% to"
- **Strongest classical comparator:** none. All percentages are relative to no control (NC). The authors state why: the transfer mechanisms differ (p. 10).
  Q[f021 p10]: "Note that the transferability was not compared with that"
  Q[f021 p10]: "of other VSL strategies (e.g., feedback methods and model"
- **Gain vs strongest comparator:**
  - There is no classical comparator, so this gain cannot be computed.
  - Against NC, see the claim audit below.
  - VSL-TL vs VSL-FL (the other RL arm) are within ±0.1 pp, except scenario 6, where FL is better: TTSs 1876.45 vs 2213.84 (Table III, p. 9).
- **Evaluation protocol:**
  - One deterministic CTM run per controller × demand. There are no replications, seeds or dispersion anywhere in the text (whole file searched).
  - The training demand is not described. Only the "two testing demands" are shown (Fig. 8, p. 8), so it cannot be determined whether training and testing demands differ.
  Q[f021 p7]: "The trained DDQN-based VSL was tested on the CTM"
  Q[f021 p7]: "using two testing demands, including a stable demand and a"
- **Flags:**
  - **N1** The text's absolute values (1020 → 812; 719 → 587 veh·h) give 20.4 % / 18.4 % (c.), not the stated 50.47 % / 35.53 % (p. 7). The resolution is in the claim audit.
    Q[f021 p7]: "and TTSf decrease to 812 veh · h and 587 veh · h, indicating"
  - **N1 (minor)** The capacity-drop magnitude is 8.4 % in the text (p. 5) but 8.1 % in Table I for the source scenario (QI, p. 6).
    Q[f021 p5]: "capacity drop is 8.4%, and the speed of the kinematic wave is"
  - **B1** The only comparator is NC, plus the VSL-FL RL arm. See the quotes above (p. 10).
  - **P1**
    - The capacity drop is an equation switch in the CTM: σ = Q_D when d > d_C (Eq. 7, p. 5). Keeping the bottleneck density below d_C removes it by construction.
    - The authors say both RL arms "could eliminate the capacity drop" (p. 10).
    - Across the target tables, VSL TTSs stays at ≈502–505 veh·h whatever the drop size (5 %, 8.1 %, 15 %; Tables II and IV). This is consistent with the gain coming entirely from the modelled drop.
    Q[f021 p10]: "large, and both the VSL-TL and the VSL-FL could eliminate"
  - **S1 / S2 / S3** Single run; replications not stated; no dispersion.
  - **E1 (cannot be excluded) / E2-risk**
    - The training demand is not stated (see above).
    - Reward shaping and the 30 s control period were chosen from "multiple rounds of simulation tests" (p. 3, p. 6). The scenarios used for those choices are not stated.
    Q[f021 p3]: "carefully decided from multiple rounds of simulation tests."
    Q[f021 p6]: "control periods and found the control period of 30 s lead to"
  - **M1**
    - TTS is the network total (Eq. 1–2, p. 3). Whether queues at the mainline origin are counted in the CTM is not stated.
    - Throughput is not reported. The authors themselves note that the percentages are large because the segment and period are short (p. 10).
    Q[f021 p10]: "in a short freeway segment for a short study period so that"
  - **R1** No code. Network size, learning rate, replay/batch size, ε schedule, cell length and jam density are missing (see the reproduction spec).
  - **C1** "learned the optimal policy" (p. 7) is asserted from a reward curve alone.
    Q[f021 p7]: "suggesting that the DDQN agent has learned the optimal policy"
- **Good practice (G+):**
  - The CTM is calibrated on one month of PeMS data, with reported MAPE: flows 9.2 %, speeds 11.2 % (p. 5).
  - The authors are explicit that no feedback or MPC comparison was made (p. 10).
  - A negative result is reported openly: TL is worse than FL in scenario 6 (p. 9).
  - Every percentage in Tables II–IV is reproducible from the absolute values printed in the same table (all 34 checked, c.).
- **Screen row check:**
  - **Partly imprecise.**
    - "the printed values give 20.4 %" is literally true for the text on p. 7.
    - But Tables II–IV contain values that reproduce 50.47 % exactly, and the most plausible error is in the text's absolute numbers, not in the percentage (see the audit).
  - "8.4 % drop" should read "8.4 % (text) / 8.1 % (Table I)".
- **Not checked / uncertain:**
  - The lane count is not stated in the text. Fig. 6 (p. 6) draws 4 lanes (QI); I am not certain that this is the modelled number.
  - Fig. 8 demand values were read from the figure, so they are approximate.

#### Claim audit, #7: where does 50.47 % come from?

**Occurrences of "50.47" in the text file.**
- There is exactly one: p. 7, Sec. V-A (whole file searched).
- There is no 50.47 in the abstract or conclusion. The abstract's range starts at 26.02 %.
- Table II (image, p. 7) holds the nearby values 50.78 % (VSL-TL, scenario 1) and 50.67 % (VSL-FL, scenario 1).

**Printed values on p. 7 (text).**
- NC: TTSs = 1020 and TTSf = 719 veh·h. Table II prints NC as 1020.68 and 719.34 (QI).
- DDQN: TTSs = 812 and TTSf = 587 veh·h.

**Definitions tested.**

| Candidate definition | Arithmetic (c.) | Result | Matches 50.47 / 35.53? |
|---|---|---|---|
| (NC−RL)/NC, text values | (1020−812)/1020; (719−587)/719 | 20.39 % ; 18.36 % | no |
| same with Table II NC | (1020.68−812)/1020.68; (719.34−587)/719.34 | 20.45 % ; 18.40 % | no |
| (NC−RL)/RL | (1020−812)/812; (719−587)/587 | 25.62 % ; 22.49 % | no |
| delay-based (TTS − free-flow TTS) | would need free-flow TTS = 1020−208/0.5047 = 607.9 and 719−132/0.3553 = 347.5 veh·h | — | not testable: no free-flow TTS is printed anywhere |
| vs untransferred model (VSL-FL) | not applicable: in the source scenario there is only one DDQN | — | no |
| NC 1020.68 vs Table IV scen. 8 VSL-TL 505.55 | (1020.68−505.55)/1020.68 | **50.47 %** | **yes (TTSs)** |
| NC 1020 vs Table IV scen. 7 VSL-FL 505.18 | (1020−505.18)/1020 | **50.47 %** | **yes (TTSs)** |
| TTSf: nearest printed VSL values | (719.34−463.37)/719.34; (719.34−463.10)/719.34; (719−463.37)/719 | 35.58 % ; 35.62 % ; 35.55 % | close, not exact |
| implied source DDQN values | 1020.68×(1−0.5047); 719.34×(1−0.3553) | 505.5 ; 463.8 veh·h | — |

**Key observation.** The text's "812" and "587" match, to the integer, the *No control* row of **scenario 7** in Table IV.
QI[f021 p9]: "Scenario 7 (Cdrop = 5%) No control 812.26 ... 587.89"

**Resolution (best explanation, not confirmed).**
- 50.47 % and 35.53 % are consistent with the source-scenario DDQN reaching TTSs ≈ 505.5 and TTSf ≈ 463.8 veh·h (c.).
- That is the same level the VSL reaches in every scenario where it removes the drop:

  | Scenario | VSL-TL TTSs | VSL-TL TTSf |
  |---|---|---|
  | 1 | 502.39 | 462.04 |
  | 7 | 502.39 | 462.64 |
  | 8 | 505.55 | 463.37 |

- So the percentages are probably right, and the absolute values 812/587 in the text are most likely mis-transcribed from Table IV's scenario-7 NC row.
- If instead 812/587 are correct, the source gain is 20.4 % / 18.4 % (c.).
- Either way it is a printed inconsistency (N1), and the paper does not let one decide between the two readings.

**Side observations.**
- VSL-TL TTSs = 502.39 appears identically for scenario 1 (overspeed 5 mph, Table II) and scenario 7 (drop 5 %, Table IV). The TTSf values differ (462.04 vs 462.64). I cannot tell whether this is a coincidence of a deterministic CTM or a copy.
- Training-time reductions check out, e.g. scenario 1: (141−61)/141 = 56.7 % (c.), matching Fig. 9 (p. 8).

**Practical reading for the thesis.** About 50 % TTS reduction vs NC, in a CTM whose capacity drop (8.1–8.4 %) is a model switch that VSL can switch off. There is no classical comparator, so this is not evidence that DRL beats a tuned controller.

#### Reproduction spec, #7 (SUMO 1.27 / libsumo)

- **Simulator used:** custom CTM (language not stated).
  - Porting to SUMO means re-creating a merge bottleneck whose capacity drop is *emergent*: it depends on car-following and lane-changing.
  - The 8.1–8.4 % drop and the "VSL removes the drop completely" mechanism will not carry over by construction. Expect a different and probably smaller gain.
- **Network:** I-880 NB, "6-mile" section (p. 5).
  - Fig. 6 postmiles run from 20.72 to 27.71 = 6.99 mi (c.).
  - 15 loop detectors.
  - VSL zone = detectors #9–#12 (PM 24.37–25.77, 1.4 mi), followed by a 0.6 mi acceleration area (p. 6).
  - Bottleneck = merge with the W Tennyson Rd on-ramp (around PM 26.37, fig.).
  - Intermediate ramps (Decoto, Fremont, Alvarado-Niles, Whipple, Industrial Pkwy) are drawn. Whether they are modelled is not stated.
- **Fundamental diagram:**
  - Free-flow speed 65 mph, capacity 1750 veh/h/ln, drop 8.4 % (text) / 8.1 % (Table I), wave speed 9.5 mph (p. 5).
  - d_c = 26.75 veh/mi/ln (p. 3). Check: 65×26.75 = 1738.75 veh/h/ln ≈ 1750 (c.).
  - Jam density and cell length are not stated.
- **Demand (testing; Fig. 8, approximate):**
  - Stable: mainline ≈ 3300 → ≈ 6600 veh/h, trapezoid with plateau ≈ 1.3–2.9 h; ramp ≈ 330 → ≈ 660 veh/h.
  - Fluctuating: mainline 4000–7000 veh/h.
  - Horizon 531 × 30 s = 4.43 h (c., p. 6).
  - **Training demand: MISSING.**
- **Target scenarios (Table I):**
  - Overspeed V_O = 5 / 7.5 / 10 mph.
  - V_F = 60 / 57.5 / 55 mph.
  - Drop 5 % / 15 %.
- **RL:**
  - DDQN; actions {5, 10, …, 65} mph (13 actions); control step 30 s; test-time rate limit 10 mph per step (p. 2–4).
  - State (6-dim): mainline demand, ramp demand, bottleneck density, VSL-zone density, ramp density, previous limit.
  - Reward (Eq. 3): piecewise-linear in downstream density, with c = 0.02, a +0.5 bonus for 26 ≤ d ≤ 27.5, −0.5 for d ≥ 45, −0.2 for not using the maximum limit in free flow, and −0.1 for a drop of more than 10 mph.
  - γ = 0.8.
  - Stopping rule: g_n < 5 %, k = 10.
  - Training stopped at episode 131 in the source scenario: 131 × 531 = 69.6 k steps (c.). Fig. 9 shows up to ≈ 200 episodes for full learning.
  - **MISSING:** network size and activation, learning rate, optimiser, replay size, batch, target-update period, ε schedule, wall time.
- **Baseline:** none. To be meaningful, a reproduction would have to add tuned feedback (e.g. a Carlson-type controller) and an MPC.
- **Evaluation:** one run per demand. CTM determinism is implied but not stated.
- **Code/data:** none. The only URL in the text is the PeMS data source, cited as "http://pems.dot.ca.gov/" (ref. 43, p. 11).
- **Top guesses needed:**
  1. Training demand.
  2. DDQN hyperparameters.
  3. Lane count and ramp modelling.
  4. CTM cell and step sizes.
  5. Origin-queue accounting in TTS.


### #8 Tabadkani Aval 2019, ICCKE 2019 — file f050
- Structure / simulator / network: direct tabular ETRL (eligibility-trace Q-learning) choosing RM rate and one VSL rate; macroscopic CTM calibrated by GA to MIDAS loop data, 8 sections, one on-ramp, M62 eastbound (Sec. II, V; Table 1, p. 4).
- Headline claim: the abstract/conclusion claim only that the strategy "can help improve" conditions; the text says the controlled runs show increased speed and flow (Sec. V, p. 4). No percentage anywhere. Searched whole file for "%", "percent", "baseline", "ALINEA": none besides the reference list.
- Strongest classical comparator: none. Only the no-control case (Fig. 3, p. 5). ALINEA is cited in the reference list only.
  Q[f050 p5]: "Fig. 3: Results of the no control case a) average speed b) traffic flow"
- Gain vs strongest comparator: not derivable. Results are 3-D surface plots (Fig. 3-5, p. 5); no table, no scalar TTT/delay. QI: colour scales differ between no-control and controlled plots, so no numbers can be read reliably.
- Evaluation protocol: 1000 training epochs on one day (5 April); first "test" on the same day; one further day (6 April) as "validation". One run each, no seeds, no dispersion (CTM is deterministic; demand is the measured profile).
  Q[f050 p4]: "Table (SAT) is tested for the traffic data of the same day."
  Q[f050 p4]: "strategy, traffic data from April 6th was used to test the SAT."
- Flags:
  - **B1** NC is the only comparator. Fig. 3 vs Fig. 4/5, p. 5.
  - **E1** the first test (Fig. 4) is on the training day; the second (Fig. 5) is one held-out day only. Sec. V, p. 4.
  - **M2** the "TTT" used as reward/criterion is defined as the number of vehicles accumulated and is to be maximised, i.e. not a travel-time metric; delay is never reported. Eq. 14 and Sec. IV, p. 4.
    Q[f050 p4]: "The maximization of TTT can be regarded as an acceptable"
  - **S1/S3** one run per case; no scalar results, no dispersion or test. Fig. 4-5.
  - **P1/P2** not applicable as such (macroscopic CTM, deterministic); the capacity drop is not mentioned (searched "drop": absent), so the model's congestion physics is only the triangular FD. Eq. 1-5, p. 2.
  - **N1 (labelling)** QI: Fig. 3 panel (a) is plotted in veh/h and (b) in km/h, while the caption says "a) average speed b) traffic flow"; Fig. 4(a) axis reads "veh/km". I cannot tell whether flow or density is plotted, so the claimed flow increase cannot be checked.
  - **C1** "near-optimal" is claimed in the Conclusions without any optimality evidence or comparator. p. 6.
    Q[f050 p6]: "authors used an ETRL algorithm to provide the near-optimal"
  - **R1** no RL hyperparameters (alpha, gamma, epsilon, discretisation), no code. Searched whole file.
  - **P2** n/a (macroscopic); calibration criterion is density error only (Eq. 7, p. 3), result Fig. 1 not quantified in text.
- Good practice (G+): a second day is used for validation; the model is calibrated on real detector data (Sec. V).
- Screen row check: agrees (NC only, "figures only"). Added precision: the "gain" is not even stated as a figure, and the optimised quantity is accumulation, not delay.
- Not checked / uncertain: units/panel mapping of Fig. 3-5 (see N1); the PDF page 7 is blank.

### #9 Sun, Jamshidnejad & De Schutter 2024, IEEE T-ITS 25(7):6756-6769 — file f008
- Structure / simulator / network: hierarchical hybrid: MPC (every 300 s) gives a baseline RM+2 VSL input, a DDPG agent (n-step TD, every 60 s) adds a bounded correction (+/-0.32 range for VSL, +/-0.4 for RM). Matlab METANET; Hegyi benchmark (6 km, 2 lanes, one on-ramp); plant parameters differ from MPC-model parameters (Table III, p. 9; Sec. IV-A, p. 8).
- Headline claim: abstract and contribution 2.
  Q[f008 p1]: "the proposed framework outperforms standalone MPC"
  Q[f008 p2]: "combined MPC-DRL outperforms other controllers in"
- Strongest classical comparator: per scenario the best of high-frequency MPC (Tc = 60 s) or parameterised MPC. Parameters: weights and horizon stated but not tuned by any described method; "tuned" is said only of DRL parameters.
  Q[f008 p9]: "wD = 0.4. The prediction window is 10 min, which means"
  Q[f008 p9]: "The other DRL parameters that are tuned during the learning"
- Gain vs strongest comparator (c., Table V, p. 11, TTS in veh.h, QI values; Table V is image-only and was rendered):
  vs the same standalone MPC: S1 (1407.47-1375.87)/1407.47 = 2.25 %; S2 0.86 %; S3 4.48 %; S4 2.96 %; S5 4.06 %; S6 2.30 %.
  vs the best MPC variant: S1 HF-MPC 1368.45, hybrid 1375.87 = 0.54 % worse; S2 PMPC 1370.96 vs 1388.29 = 1.26 % worse; S3 PMPC 1339.53 vs 1376.76 = 2.78 % worse; S4 HF 1231.47 vs 1265.21 = 2.74 % worse; S5 HF 1222.81 vs 1255.17 = 2.65 % worse; S6 PMPC 1207.26 vs 1266.48 = 4.91 % worse. The hybrid is never the best TTS.
  The paper states this itself for HF-MPC:
  Q[f008 p12]: "the best TTS, TWT, and minimum speed performance for most"
- Evaluation protocol: 6 scenarios (2 demand profiles x 3 Gaussian noise levels); 3000 training episodes in the same stochastic environment; evaluation = 10 independent runs with random demands. Seeds, mean vs median, and dispersion not stated; Table V has one number per cell.
  Q[f008 p10]: "with 3000 episodes"
  Q[f008 p11]: "10 times independently with random demands in order to"
- Flags:
  - **C1** abstract and p. 2 say "outperforms other controllers" / "standalone MPC and DRL"; Table V shows HF-MPC and PMPC with lower TTS in all 6 scenarios. The gain holds only against the standalone 300 s MPC and the (non-converged) DRL. Sec. IV-D.
  - **B2** MPC weights/horizon hand-set, no tuning method; the MPC also gets a mismatched model by construction. Sec. IV-B.
  - **B4** information asymmetry: the DRL state contains the real demand, the MPC uses predicted demand (Fig. 4). Eq. 7, p. 6; p. 9.
    Q[f008 p6]: "the real demands at simulation sampling"
    Q[f008 p9]: "by MPC are shown in Figure 4."
  - **E1** train and test share the same two demand profiles and noise distribution; no held-out profile or noise level; disjointness of evaluation noise draws from training not stated (searched "seed": absent).
  - **S2/S3** 10 runs, no dispersion, no test; differences of 0.5-4.9 % are not tested.
  - **P1** METANET plant and METANET MPC model with parametric mismatch only (no structural mismatch); the capacity-drop-like effect is a model feature.
    Q[f008 p8]: "parameters are assumed unknown in this case study, and the"
  - **E2/R1** DRL hyperparameters "tuned" with no stated data; checkpoint choice not stated (searched "checkpoint": absent). No code statement found.
  - **C1 (DRL comparator)** standalone DRL fails to converge in S1-S3 and is worse than no control in S1, S5, S6 (Table V), so "beats DRL" is against a weak learner.
    Q[f008 p10]: "scenario 1, 2, and 3, the DRL with 10-step TD fails to converge"
- Good practice (G+): honest disclosure that HF-MPC is best on TTS; reports TWT, min speed, constraint violation and compute time (HF-MPC mean 21-23 s per step vs 0.7 s hybrid, QI); the hybrid has lower constraint violation than every MPC variant in S1-S6 (e.g. S1 9.97 % vs HF 18.64 %, QI); TTS covers the whole network including queues.
  Q[f008 p7]: "the performance criteria consist of TTS of all the vehicles"
- Screen row check: agrees (-0.9...-4.5 % vs the same MPC; 0.5-4.9 % worse than best variant, all 6 scenarios; Table V confirmed by render). Imprecision: "means only": the paper does not say whether cells are means or medians.
- Not checked / uncertain: whether the TWT/constraint figures are means; Sec. III formulation (read, not re-derived).

### #10 Vinitsky et al. 2018, ITSC 2018 — file f029
- Structure / simulator / network: direct TRPO (GRU policy) setting per-lane, per-piece speed limits for the autonomous vehicles only (10 % penetration) in SUMO/Flow; 4 to 2 to 1 lane bottleneck; IDM with 20 % desired-speed noise; lane changing disabled (Sec. III, p. 3-4).
- Headline claim (abstract):
  Q[f029 p1]: "a 25% improvement at high inflows"
- Strongest classical comparator: feedback ramp meter (ALINEA-type, T = 30 s, KF = 20, ncrit = 8), "tuned empirically"; on which scenarios/seeds is not stated.
  Q[f029 p5]: "These values were tuned empirically and we"
  Q[f029 p5]: "stress that there may be better values."
- Gain vs strongest comparator: the 25 % is vs uncontrolled: (1000-800)/800 = 25 % (c., "around 1000" vs "approximately 800", p. 2, p. 5). Vs the ramp meter no figure is given; the text says RL only matches it above the critical inflow.
  Q[f029 p6]: "critical inflow but matches the performance of feedback ramp"
  QI (Fig. 10, p. 6, approximate): RM outflow about 1175-1320 veh/h at inflows 1200-1700 vs RL about 1000-1060, i.e. RL roughly 15-25 % lower there; similar above about 1900. Also RL is below uncontrolled up to inflow 1600 (Fig. 9).
- Evaluation protocol: one trained policy (400 iterations, one curve, Fig. 8). Training inflow sampled in 1000-2000; evaluation sweeps 400-2500 with 10 runs per inflow for RL and uncontrolled, 20 for RM. Training seeds not stated; disjointness of evaluation seeds not stated.
  Q[f029 p6]: "10 runs at each inflow value for RL and 20 for the ramp"
- Flags:
  - **B4** the comparator is a different actuator: RL sets speed limits for AVs in 4-5 pieces with per-lane density/speed and outflow observations; RM is a single signal using one vehicle count. RL's reward is outflow. Sec. II-E, III-B/C.
    Q[f029 p2]: "the speed limits of the autonomous vehicles in the bottleneck"
  - **B2/B3** RM tuned "empirically", method and data unstated.
  - **M1/M2** only outflow is reported (no delay/TTS, no entry queues). The reward is outflow.
    Q[f029 p4]: "For our reward function we simply used the outflow over"
  - **S1** single trained policy; no seeds across training runs. **S3** the solid lines in Fig. 9/10 are means; no band for RL.
  - **P2** capacity drop demonstrated (G+), but the network is "modeled after" the Bay Bridge, not calibrated; a stop rule replaces collisions; lane changing disabled.
    Q[f029 p3]: "a full stop. This is unrealistic, but empirically this behavior"
    Q[f029 p3]: "experiment, lane changing is disabled for all the vehicles in"
  - **N1 (minor)** Fig. 6 caption: "min and max over the two runs" vs "10 runs" in text.
    Q[f029 p5]: "is bounded by the min and max over the two runs."
- Good practice (G+): capacity-drop characterisation with 10 runs, mean +/- 1 sd, min/max (Fig. 6, p. 5); code released.
  Q[f029 p1]: "code and tutorials can be found at https://github.com/"
- Screen row check: agrees on type, comparator, "matches above / under-performs below" and capacity drop. Imprecise: "approx 0" hides that RL is clearly below RM at inflows ~1200-1700 (Fig. 10), and "per-lane VSL" is for AVs only (10 %), not a limit seen by all vehicles.
- Not checked / uncertain: Fig. 10 values are visual estimates.

### #11 Schmidt-Dumont & van Vuuren 2019, J. S. Afr. Inst. Civ. Eng. 61(3) — file f001
- Structure / simulator / network: tabular Q-learning and kNN-TD agents; RM, VSL, and RM+VSL as independent / hierarchical / maximax MARL; AnyLogic microscopic model of the N1 outbound from Cape Town (Sec. "Microscopic model", p. 5-6).
- Headline claim: the conclusion, p. 12.
  Q[f001 p12]: "reductions in the TTS of 10.13%, 12.70%"
  Q[f001 p12]: "and 10.39% respectively over the no-control"
- Strongest classical comparator: PI-ALINEA (RM only) at 94.45 % of NC TTS (Table 3, p. 9) is the best classical result in the paper; the comparator used for MARL is the integrated feedback controller (Carlson 2014) at 96.64 % (Table 5, p. 12). Parameters: found by "empirical parameter evaluation" on the same simulation.
  Q[f001 p9]: "An empirical parameter evaluation was"
  Q[f001 p9]: "were set to 60 and 40 respectively, as these"
- Gain, recomputed (c., Tables 3-5): VSL-only kNN-TD vs MTFC: (95.09-93.92)/95.09 = 1.23 %; Q-learning vs MTFC (95.09-93.55)/95.09 = 1.62 %. Hierarchical MARL vs integrated feedback: (96.64-87.30)/96.64 = 9.66 %; vs PI-ALINEA alone: (94.45-87.30)/94.45 = 7.57 %. Printed 6.45/6.08/4.91 and 12.70/3.36 % reproduce.
  Q[f001 p9]: "TTS 1 960.01 98.37% 94.45% 93.00% 89.30%"
  Q[f001 p12]: "TTS 1960.01 96.64% 89.87% 87.30% 89.61%"
- Evaluation protocol: 30 runs per case, the same 30 seeds for every controller; mean values in tables, box plots (Fig. 7-9). Training protocol (episodes, learning rates, whether learning continues in the 30 runs): not found in text (searched "train", "episode", "iteration"); details deferred to a PhD thesis.
  Q[f001 p9]: "same 30 seed values were employed in each"
- Flags:
  - **B3** baselines (target density, K gains, number/location of controllers) and RL settings (agent location, delta, target density) were picked by search on the same scenario; seed separation from the 30 test seeds not stated. Sec. "Ramp metering" / "VSL", p. 9-10.
    Q[f001 p9]: "Furthermore, setting the value of KR in (4)"
  - **B4** MARL uses two sites (R300 and Okavango) while the integrated feedback controller is placed at one.
    Q[f001 p11]: "troller is implemented at this interchange."
    Q[f001 p11]: "first of these is at the R300 interchange,"
  - **B2** the MARL comparator (integrated feedback, 96.64 %) is weaker than the PI-ALINEA result of the same paper (94.45 %).
  - **E1** no train/test split visible; one calibrated afternoon peak (15:30-18:30) for tuning and testing.
  - **S3/C1** ANOVA/Levene/post-hoc tests are announced but no p-values or CIs are printed; text uses "significant".
    Q[f001 p8]: "Analysis of Variance (ANOVA)"
    Q[f001 p12]: "implementations resulted in significant"
  - **N1** NC component TTS values sum to 1920.01 (844.11+992.19+69.71+14.00, c.) vs printed TTS 1960.01 (diff 40.00). Treated columns reproduce TTS within about 1.7 veh.h (e.g. ALINEA 1928.1 vs 1927.1, hierarchical MARL 1711.1 vs 1709.4, c.); the kNN-TD VSL column is off by 69.5 (TTS 93.92 % x 1960.01 = 1840.8 vs 103.91 % x 844.11 + 81.61 % x 992.19 + 100.63 % x 69.71 + 102.57 % x 14.00 = 1771.3, c.). All % gains are relative to 1960.01.
    Q[f001 p9]: "TTSN1 844.11 106.99% 110.21% 107.12% 72.81%"
    Q[f001 p11]: "TTSN1 844.11 111.58% 97.04% 103.91%"
  - **M1** TTS is "time spent in the system"; throughput not reported; treatment of vehicles still queued at the end or outside entries not stated.
  - **P2** validation by flow counts only; no capacity drop shown ("neither the measured data nor the simulated output resembles the classical fundamental diagram").
    Q[f001 p6]: "fundamental diagram. This may be due"
  - **R1** RL hyperparameters and training schedule absent (deferred).
    Q[f001 p9]: "Schmidt-Dumont (2018)."
- Good practice (G+): real-data calibration with per-counter errors (Tables 1-2); TTS broken down by origin so that on-ramp delay under RM is visible (e.g. TTSO 342 % with feedback); common random numbers; 30 runs; many classical baselines (ALINEA, PI-ALINEA, MTFC, integrated).
- Screen row check: agrees on the 6.45/4.91 and 12.70/3.36 figures and "tuned, same scenario". Add: the best classical result in the paper is PI-ALINEA (5.55 % reduction), so "hier. MARL vs integrated FB 9.7 %" overstates against the strongest; and "train = test" is not confirmed by the text (training protocol not found).
- Not checked / uncertain: box plots (Fig. 7-9) viewed only for Fig. 9; whether TTS includes vehicles still queued at the end.

### #12 Schmidt-Dumont & van Vuuren (venue unclear) — file f014
- Publication info: no real publication data found in the text (searched whole file for manuscript, DOI, copyright, received, accepted, published, arXiv). Every page has a T-ITS running header; the only date line is stock template text, and the references are dated 2017, so "2015" cannot be the writing date.
  Q[f014 p1]: "IEEE TRANSACTIONS ON INTELLIGENT TRANSPORTATION SYSTEMS, VOL. 14, NO. 8, AUGUST 2015"
  Q[f014 p1]: "Manuscript received April 19, 2005; revised August 26, 2015."
  Q[f014 p10]: "[Online], [Cited May 1st , 2017], Available from"
  Author bio says "currently working toward the M.-Eng." (p. 10). From my own knowledge, T-ITS vol. 14 is 2013 and "April 19, 2005" is the IEEEtran sample text: [VERIFY]. Treat as an unpublished manuscript/preprint (about 2017), not a T-ITS paper.
- Structure / simulator / network: same formulations as #11 (Q-learning, kNN-TD; RM, VSL, 3 MARL schemes) on a hypothetical Hegyi benchmark (2 lanes, 6 x 1 km, one on-ramp), AnyLogic, default vehicle parameters (Sec. IV, VI-B, p. 3, 7).
  Q[f014 p7]: "the default values for the"
- Headline claim: p. 9-10 conclusion; contribution list p. 1.
  Q[f014 p9]: "yields marginally better results than ALINEA, often due to"
- Strongest classical comparator: ALINEA (RM only), modified for microsim (Eq. 17). K_R and target density not stated (searched whole file for K_R values: none).
  Q[f014 p7]: "KR is a nonnegative control parameter, and ρ̂"
- Gain (c., Tables I-III, TTT veh.h): kNN-TD RM vs ALINEA S1 (1455.93-1405.10)/1455.93 = 3.49 %; S2 3.07 %; S3 8.90 %; S4 2.73 %. Q-learning RM vs ALINEA: -0.90 % (S1, worse), 1.44, 8.74, 2.41 %. Best MARL variant vs ALINEA: S1 6.06 %, S2 4.94 %, S3 9.90 %, S4 2.88 %. ALINEA is worse than NC in S4 (552.44 vs 550.00, +0.44 %). VSL-only RL has only NC as comparator (Table II).
  Q[f014 p7]: "TTT 1 753.01 1 455.93 1 469.00 1 405.10"
  Q[f014 p9]: "TTT 1 753.01 1 386.17 1 384.02 1 367.74"
- Evaluation protocol: 4 demand scenarios, each trained 1000 epochs on its own scenario with the same seed every episode; evaluation = 30 runs with varying seeds, same seeds for all controllers; averages only.
  Q[f014 p7]: "training period, the same seed was employed. The learning"
  Q[f014 p7]: "the purpose of comparison, however, the same 30 seeds were"
- Flags:
  - **B2** ALINEA parameters not stated, no tuning method.
  - **B4** combined RM+VSL RL (Table III) is compared with RM-only ALINEA; no integrated classical controller.
  - **B1** VSL-only RL: NC only (Table II).
  - **E1** trained and tested on the same demand scenario (single fixed training seed, test on 30 other seeds if disjoint; disjointness not stated).
  - **S3** averages only; one box plot (Fig. 7-8) for one scenario.
  - **P2** hypothetical, uncalibrated network; capacity drop not demonstrated; default vehicle parameters.
  - **N1 (minor)** Table II S4 Q-learning TTT 547.41 vs TTTHW+TTTOR 514.50+33.91 = 548.41 (c.); Table III S1 maximax TTT 1367.74 vs 760.45+609.29 = 1369.74 (c.); all other rows sum exactly.
  - **C1** "first" claims for several items (p. 1).
    Q[f014 p1]: "paper demonstrates the first application of the kNN-TD RL"
- Good practice (G+): on-ramp queue time is counted (TTTOR 855 vs 45 NC; vehicles wait in a buffer), so delay shifted to the ramp is visible; common random numbers; ALINEA included.
  Q[f014 p7]: "the vehicle is stored in a queue buffer until sufficient space"
- Screen row check: partly disagrees. "-2.9...-9.9 %" matches the best MARL variant vs ALINEA (S4 hier. 2.88, S3 maximax 9.90), i.e. a two-actuator RL vs an RM-only baseline; for RM-only RL vs ALINEA the range is 2.7-8.9 % and Q-learning loses in S1. The venue is a template header (see above); "2015" is unreliable.
- Not checked / uncertain: Fig. 6-8 only skimmed from text.

### #13 Wang C. et al. 2019, IEEE Access 7:41947-41956 — file f007
- Structure / simulator / network: distributed Q-learning with kNN-TD over 3 VSL agents (10 segments, 8 speed limits 30-100 km/h), reward from density (mobility) or TTC-based speed difference (safety); MOTUS (IDM+, LMRS); A16 near Drechttunnel, 2 km, one on- and off-ramp; assumes all vehicles are connected and comply (Sec. III-V, p. 3-8).
  Q[f007 p3]: "we assume the vehicles in the study to have basic"
- Headline claim (abstract):
  Q[f007 p1]: "Results revealed that compared with no control cases, the proposed"
- Strongest classical comparator: none; only no control. The paper itself lists comparison with other strategies as future work.
  Q[f007 p8]: "Three scenarios are tested: the no control scenario, the traf-"
  Q[f007 p10]: "the proposed DQL algorithm will be compared with other"
- Gain (Table 2, p. 9, image-only; rendered). Mobility control vs NC: freeway TTT (326.9-229.2)/326.9 = 29.89 % (c.; printed -29.89 %); bottleneck TTT (37.4-18.163)/37.4 = 51.43 % (c.; printed -51.44 %); bottleneck outflow 1632 to 2036 = +24.76 % (c.; printed +24.77 %). Safety control: freeway TTT 305.583, -6.52 % (c. 6.52 %). All printed percentages reproduce within 0.02.
- Evaluation protocol: peak hour 16:30-18:00 of one demand scenario; no number of runs, seeds, or training schedule (searched "replic", "seed", "episode", "train", "run"). One value per cell.
  Q[f007 p8]: "peak hour’’ (16:30-18:00) simulation results are"
- Flags:
  - **B1** NC only.
  - **S1/S2/S3** single value per cell, number of replications not stated, no dispersion.
  - **E1** no training/test split described; training schedule absent; claim that it "improves continually" is not shown (no learning curve).
    Q[f007 p1]: "improve its performance continually as time goes on."
  - **M1** TTT counts vehicles inside the 10 segments only; entry/origin queues and section throughput are not reported (bottleneck outflow only).
    Q[f007 p8]: "ber of vehicles in segment i at time step t,"
  - **M2** safety headlines use proxies (stops 1020 to 0, SD of speed -82.59 %); mobility and safety controllers are different objectives and the safety variant gives only -6.52 % TTT (the paper says so).
  - **P2** calibration shown as a visual flow-density scatter (Fig. 10); no error metric, no capacity-drop size, no teleport/collision report.
    Q[f007 p8]: "can satisfy the traffic control requirement. For the details of"
  - **R1** DQL parameters (gamma, E, sigma, k, centres per agent beyond figures) not given; no code statement.
  - **C1** "significantly reduced" in abstract with no test.
    Q[f007 p1]: "is significantly reduced. We also"
- Good practice (G+): open-source simulator MOTUS; calibration against real data; reports the mobility/safety trade-off honestly (both controllers in Table 2); printed percentages are arithmetically consistent.
- Screen row check: agrees (MOTUS, A16 Drechttunnel, NC only, -29.9 % TTT vs NC). Imprecise: -29.9 % is the freeway-section TTT for the mobility controller only; the safety controller gives -6.5 %. "train = test" is not supported or contradicted by the text (no training protocol found).
- Not checked / uncertain: Table 2 numbers were read from a rendered image (QI); Fig. 11-12 not analysed.

### #14 Kušić 2020, ITSC (WL-VSL) — file f023
- Structure / simulator / network: two tabular W-learning agents (Q-tables 225 states x 10 joint actions) setting limits on two consecutive 1 km sections upstream of a 0.5 km on-ramp bottleneck; SUMO, synthetic motorway, 1.5 h runs, control step 150 s (Sec. IV, V.A; Fig. 1; p. 3-4).
- Headline claim (p. 1, abstract):
  Q[f023 p1]: "We show that WL-VSL outperforms base cases (no control,"
  Q[f023 p1]: "of traffic parameters up to 18 %."
- Strongest comparator: SGL-VSL (single-agent Q-learning, same state/reward family) and IND-VSL; no classical (feedback/rule/MPC) controller at all. Learning parameters of the baselines "αQ = 0.5 and γ = 0.8 according to [11], [13]" (p. 5); not tuned per baseline.
  Q[f023 p5]: "αQ = 0.5 and γ = 0.8 according to [11], [13]. Most of the"
- Gain vs strongest comparator (Table I, p. 8): TTSreward WL 2.14 vs SGL 2.24: (2.24-2.14)/2.24 = 4.5 % (c.); density in L3 (23.4-20.7)/23.4 = 11.5 % (c.); speed 89.5/83.7-1 = +6.9 % (c.). Vs no control the table values reproduce (9.70, 7.31, 18.18, 28.57 %; no N1). The "18 %" in the abstract is the L3 density vs no control.
  Q[f023 p8]: "T T Sreward [veh · h] 2.37 2.14 9.70 2.35 0.84 2.24 5.48"
  Overall-network TTS shows no gain (p. 6, Fig. 4): all controllers converge to the no-control level.
  Q[f023 p6]: "T T S value obtained in simulations without VSL control."
- Evaluation protocol: trained 6000 sims on the dynamic demand, then 200 exploitation-only runs (p. 4); one SUMO seed; static scenarios (3 on-ramp loads) tested with the policy trained on the dynamic one, but only the medium load is shown (p. 7, Fig. 5). No std/CI.
  Q[f023 p5]: "stochastically using a particular simulation seed (in this work"
  Q[f023 p7]: "results follow the same pattern, we selected the medium"
- Flags:
  - **B1** Comparators are no control and other RL variants only. Table I, p. 8.
  - **B4** WL-VSL chooses among 10 joint (per-section) actions; SGL-VSL and IND-VSL have 4 limits (SGL forced to the same limit on both sections). p. 4-5.
    Q[f023 p6]: "set (10 actions) which take care about safety restrictions"
  - **S1/S2** One seed (2000); whether the 200 test runs differ is not stated (searched whole file for "seed", "replic", "runs").
  - **S3** No dispersion or test for any Table I number; text says "significantly" for TTSreward (p. 6).
  - **E1/E2** Table I is introduced as "results obtained during the learning process" on the training demand; omega "selected from multiple tests" without a stated selection scenario (p. 5).
    Q[f023 p5]: "Results obtained during the learning process in case of"
    Q[f023 p5]: "compared to [28] and selected from multiple tests. Parameter"
  - **M1/M2** The headline "up to 18 %" is a density proxy; TTSreward is TTS of L1-L3 only (a reward component, not network delay); overall TTS = no-control level; no throughput, no on-ramp queue/delay. p. 4, 6, 8.
  - **R1** No code/data link found in text.
- Good practice (G+): states that baselines are worse than no control where they are (IND-VSL speed -2.03 %, occupancy -14.28 %, Table I); reports that overall TTS does not improve; uses same state/learning algorithm for all RL baselines (controlled comparison); tests the policy on a second demand regime (static).
- Screen row check: agrees. "local TTS -4.5 %" is vs SGL-VSL (Table I); "overall ≈ NC" agrees (Fig. 4, p. 6-7); "single seed" agrees (p. 5). Imprecision only: the abstract's 18 % is density, not TTS.
- Not checked / uncertain: static-scenario results exist only as Fig. 5 (image); Fig. 3/4 not read numerically.

### #15 Wu Y. 2020, TR-C 117 — file f019
- Structure / simulator / network: single DDPG agent setting per-lane limits (action 40-75 mph, 5 mph steps, 5 lanes, every 1 min) for a 875 m I-405 merge section built from OSM/PeMS demand; SUMO, 5 h episodes, Poisson demand, half Krauss / half IDM (Sec. 4, 5.1, 5.3; p. 5, 8, 10).
- Headline claim (p. 14 text; abstract has no numbers):
  Q[f019 p14]: "example, the DVSL improves 8.1% in average travel time in episodes with incidents and 5.8% in ones without incidents, whereas the"
  Q[f019 p1]: "the DRL based DVSL control strategy is able to improve the safety, efficiency and"
- Strongest comparator: RL only (Q-learning per Li 2017, VSL-DQN, VSL-AC, all with one limit for all lanes) plus NoVSL at 65 mph. No classical feedback/MPC controller. Their own parameters (state/network) are described; tuning protocol of the RL baselines not stated.
  Q[f019 p13]: "Q learning, same speed limit for each lane: A similar model proposed by Li et al. (2017)."
  Q[f019 p13]: "NoVSL, baseline: The baseline without any VSL. The vehicles are running with speed limits 65 mph in the mainline."
- Gain vs strongest comparator (ATT, Tables 4-5, p. 14): no incidents DVSL 80.82 vs VSL-DQN 83.26: (83.26-80.82)/83.26 = 2.9 % (c.); with incidents 82.69 vs Q-learning 87.69: (87.69-82.69)/87.69 = 5.7 % (c.). Vs NoVSL 5.83 % and 8.07 % (c.), matching the text. Volume: DVSL 30953 vs DQN 30886 = +0.2 % (c.).
  Q[f019 p14]: "DVSL −7.133 3.511 −2.848 −8.568 214.6 1.224 4.209 0.215 80.82 30953"
  Q[f019 p14]: "NoVSL −8.718 3.257 −2.837 −8.684 222.9 1.259 4.221 0.215 85.82 30042"
- Evaluation protocol: 2000 training episodes, each with fresh Poisson demand and 50 % incident chance; 100 test episodes (with/without incidents) averaged (p. 13-14); generalisation on 30 episodes with fixed demand and altered speedFactor/lcSpeedGain (p. 15). Seeds, training repetitions and dispersion not stated.
  Q[f019 p14]: "compare the average performance of the different methods across the 100 test episodes with and without incidents."
- Flags:
  - **B1** No classical controller; gain over best RL is 2.9 % / 5.7 % ATT.
  - **S1/S2/S3** One trained agent per method (not stated otherwise); no std/CI/test for Tables 4-5; "significantly" used without a test.
  - **E2** Reward-function comparison (Table 3, one training scenario) uses "networks with the best records"; checkpoint choice for Tables 4-5 not stated.
    Q[f019 p11]: "we choose the networks with the best records for the corresponding rewards to conduct comparison."
  - **B4** DVSL may post up to 75 mph while NoVSL is 65 mph (action range of the RL baselines not stated); ablation with same-limit RL agents is present, but they also differ in algorithm.
    Q[f019 p10]: "adjusts speed limits from 40 to 75 mph with an increment of 5 mph."
  - **C1** (a) Safety: the abstract claims improved safety, but r3 (emergency braking, higher is better) of DVSL is worse than NoVSL in no-incident episodes: -2.848 vs -2.837 (c., Table 4, row quotes above) and the text concedes DQN brakes less. (b) Generalisation: abstract says robustness is observed; the text reports failure at speedFactor 1.1.
    Q[f019 p1]: "and the robustness of the DRL agent is observed from the"
    Q[f019 p16]: "it produces unsatisfactory performance when mean value equal to 1.1."
  - **N1** p. 16: DVSL travel time "slightly improves" while the printed values go from 68.0900 s to 72.0000 s (a rise of 3.91 s, c.); which reference the 76.52 -> 71.14 s pair belongs to is not stated.
    Q[f019 p16]: "average travel time of DVSL agents, which changes from 68.0900s to 72.0000 s."
  - **M1** ATT definition (inclusion of vehicles not yet inserted/queued) not found; throughput (Volume) is reported alongside, which is good. No teleport/collision counts found (searched whole file).
  - **P2** Capacity drop not demonstrated, only "average speed is 25 mile/h" without control (p. 8, Fig. 5).
- Good practice (G+): throughput reported next to ATT; same-limit DQN/AC ablations isolate per-lane control; held-out test episodes with fresh random demand; incident/no-incident split; honest failure case at speedFactor 1.1; open code.
  Q[f019 p10]: "Our simulation environment is open source and available online."
- Screen row check: agrees. "-2.9 % / -5.7 % ATT vs best RL" reproduces (c., above); "fails at speedFactor 1.1" agrees (p. 16).
- Not checked / uncertain: Fig. 12 (generalisation, image only); RL-baseline action ranges; learning rates (not found in text).

### #16 Chai 2021, ISCTT (MADDPG ramp metering + VSL) — file f052
Note: the text layer is garbled (font encoding shifted by 29 code points; digits lost, PDF has 8 pages not 9). I rendered pp. 1, 4, 5, 6, 7, 8 and read them as images; pp. 2-3 were read only through a character-shifted decode. All quotes below are QI[] (not auto-verifiable).
- Structure / simulator / network: MADDPG with 2 agents (RM on/off every 3 s, VSL limit {22+2k}, M = 6, every 30 s) on a SUMO merge (3 lanes, 1 ramp lane, 4 -> 3 lane bottleneck), all vehicles CACC (Sec. 3, 4; Table 2-3; Fig. 7).
- Headline claim (p. 1, abstract):
  QI[f052 p1]: "the new method increased the average speed of the bottleneck by 28%, average occupancy dropped by 18%, evacuation traffic increased by 12%, the total travel time decreased by 21%."
- Strongest comparator: "Strategy 4, feedback integrated control" (unnamed feedback RM + feedback VSL). Parameters, formulas, tuning: not found (read pp. 4-7 as images, decoded pp. 2-3).
  QI[f052 p6]: "Strategy 1 to 5 correspond to no control method, ALINEA ramp control, feedback variable speed limit control, feedback integrated control,"
- Gain, Table 4 (p. 7), total travel time (s): S1 859982, S2 754457, S3 744890, S4 716728, S5 (MADDPG) 562819. S5 vs S4: (716728-562819)/716728 = 21.47 % (c.; text 21.46 %); S5 vs S1 34.55 % (c.); S4 vs S1 16.66 % (c.). Table is internally consistent. The 28 %, 18 % and 12 % figures appear only in prose/figures (Fig. 9-11) and cannot be derived from any printed table.
  QI[f052 p7]: "Strategy 5: Integrated control based on MADDPG under the Internet of Vehicles 562819 34.55"
- Evaluation protocol: training 200 simulations x 150 iterations; 7200 s runs (Table 3, p. 6). Results are single time-series curves (Fig. 9-11) and one TTT per strategy; no held-out demand, seeds or dispersion; demand not stated.
  QI[f052 p6]: "Number of simulations; Number of iterations 200times; 150times"
- Flags:
  - **B2** Strategy 4 (and the ALINEA/feedback-VSL strategies) have no stated parameters or tuning.
  - **E1/S1/S2/S3** No separate test scenario; one run per strategy; no dispersion; demand profile not found.
  - **M1/M2** TTT definition not given (ramp-queue/waiting of metered vehicles unclear); throughput only as a flow curve (Fig. 11); headline numbers include proxies (bottleneck speed, occupancy).
  - **N1** Action set: p. 4 gives v0 = 22 m/s, I = 2 m/s, M = 6, i.e. 22..34 m/s (c.), whereas Table 3 (p. 6) lists 20..32 m/s.
    QI[f052 p4]: "v0 - the minimum speed limit of the upstream lane of the mainline (22m/s is selected in this article)"
    QI[f052 p6]: "Speed limit {20, 22, 24, 26, 28, 30, 32} (m/s)"
  - **N1** (weaker) abstract 28 % / 18 % / 12 % not derivable from printed tables (see above).
  - **R1** No code/data; demand, comparator controllers, reward weights not specified.
  - **P2** No calibration, demand or capacity-drop evidence; teleports/collisions not reported (searched decoded text).
- Good practice (G+): training hyper-parameters printed (Table 3: lr 0.0001, batch 32, replay 1,000,000, noise 0.2); Table 4 percentages recompute exactly.
- Screen row check: partly agrees. "-21.5 % TTT" reproduces (21.47 %, c.) and "single run" agrees. The screen's "identity and params not stated" is imprecise: the identity is stated (feedback integrated control, Strategy 4; p. 6), but its parameters are not.
- Not checked / uncertain: pp. 2-3 only via decode; Fig. 9-11 values read by eye; demand absent from everything I viewed.

### #17 Gregurić 2020, ELMAR (DQN, VISSIM) — file f041
- Structure / simulator / network: single-VMS DQN (3 conv layers, 7 limits 60-130 km/h, 3 min steps), image-like state, composite reward; VISSIM, synthetic 8 km motorway with 2 on-ramps + 1 off-ramp, 2 h runs, 20 min demand surge (Sec. IV-V; Fig. 3-4).
- Headline claim (p. 6):
  Q[f041 p6]: "Initial results show that the DQL algorithm produces better"
- Strongest comparator: SPSC (Simple Proportional Speed Controller) plus no control; SPSC gain/set-point/tuning not stated, only "compared in [10]".
  Q[f041 p2]: "portional Speed Controller (SPSC) compared in [10]."
- Gain, Table II (p. 6): speed 109.4 vs SPSC 97.1: 109.4/97.1-1 = +12.7 % (c.); density (28.86-21.65)/28.86 = 25.0 % (c.). SPSC is indistinguishable from no control (97.1 vs 96.4 km/h; 28.86 vs 28.85 veh/km), i.e. the comparator did not act or did not bind.
  Q[f041 p6]: "No control 96.4 28.85"
  Q[f041 p6]: "SPSC 97.1 28.86"
  Q[f041 p6]: "DQN 109.4 21.65"
- Evaluation protocol: 10080 simulation runs, first 500 for observation (p. 5); the DQN row is "most representative DQL result"; no held-out demand, no seeds, no dispersion.
  Q[f041 p5]: "for 20 min causing congestion. This study is based on 10080"
  Q[f041 p6]: "algorithm SPSC [10], and most representative DQL result."
- Flags:
  - **B2** SPSC parameters not stated; its null effect suggests a weak or non-binding baseline.
  - **S1/S2/S3** One selected ("most representative") run; no seeds, no std/CI.
  - **E1** Single synthetic scenario used for training and the table; no separate test demand.
  - **M1/M2** Only mean speed and density in the congested area; no TTS/delay/throughput/on-ramp queue. The reward itself uses speed-limit/speed terms, so speed is partly the objective.
  - **P2** Synthetic demand, no calibration, no capacity-drop demonstration, no teleport/collision report.
  - **R1** Reward weights set on the same scenario ("set to 85 according to the executed simulation trials", Cv2 = 55 likewise); no code.
    Q[f041 p4]: "and maximal allowed speed, and it is set to 85 according to"
- Good practice (G+): conclusion is hedged ("Initial results") and states that convergence speed and stability are low.
  Q[f041 p6]: "process are low for both previously mentioned parameters."
- Screen row check: agrees (SPSC not stated; +12.7 % and -25 % reproduce; "representative run" confirmed, p. 6). Addition: SPSC equals no control in Table II.
- Not checked / uncertain: no-control speed limit, units of density (per lane?), Fig. 5-6 not read.

### #18 Gregurić 2022, EAAI 112:104850 (DDPG, VISSIM) — file f026
- Structure / simulator / network: DDPG with ConvLSTM state (vehicle-position images) in five strategies of 2-6 continuous actions (limit per lane, zone start/length, on-ramp limits), vehicles obey via ISA; VISSIM, synthetic 8 km, 2 mainstream lanes, 2 on-ramps, 120 min (Sec. 2-4).
- Headline claim (p. 1, abstract):
  Q[f026 p1]: "overall motorway throughput compared to one which is based on the static speed limit zones and"
  Note: the abstract has no percentages; throughput is never tabulated (searched whole file for veh/h, served, volume, outflow); it is inferred from speed and TTS.
- Strongest comparator: SPSC with gain 4.5 "according to Wang (2011)"; no tuning described. Baselines' reward evaluated over 100 sims.
  Q[f026 p10]: "gain value set to 4.5 according to the results presented in Wang (2011),"
  Q[f026 p10]: "sented as the average value computed based on 100 simulations under"
- Gain, Table 2 (p. 13) TTS veh*h, SPSC vs best DDPG: bottleneck 186 -> 169: (186-169)/186 = 9.1 % (c.); overall mainstream 579 -> 561 (mainstream-based) = 3.1 % (c.), or 560 (on-ramp control) = 3.3 % (c.). The static two-action DDPG, the closest analogue of SPSC, is worse than SPSC: 207 vs 186 = +11.3 % and 590 vs 579 = +1.9 % (c.).
  Q[f026 p13]: "SPSC 52.25 86.06 15.06 186 86.65 97.78 4.75 579"
  Q[f026 p13]: "DDPG 2 actions 53.33 84.67 11.19 207 83.96 95.05 5.75 590"
  Q[f026 p13]: "DDPG 6 actions 59.25 90.23 12.11 173 90.62 99.67 4.44 560"
- Evaluation protocol: table values are averages of the "last 10 best performing" simulations taken from the learning process; terminated runs excluded; no held-out scenario or exploitation-only test; no dispersion across runs.
  Q[f026 p12]: "the average values of the last 10 best performing"
  Q[f026 p12]: "simulations. The simulations which are terminated before their end are"
- Flags:
  - **B2** SPSC gain taken from literature, not tuned on this scenario; no set-point/tuning described (searched for "tun", "Kv").
  - **E2** Reported results are the best-10 runs; selection criterion and pool size (number of training runs) not found; DDPG training budget not found.
  - **E1** Same synthetic scenario for training, selection and reporting.
  - **S1/S2/S3** No seed count; no std/CI/test across runs; the table gives only a mean over selected runs.
  - **B4** DDPG strategies add per-lane limits, spatially moving zones, on-ramp limits and ISA compliance; SPSC has one fixed zone. The like-for-like variant (2 actions) loses to SPSC (see above).
  - **M1/M2** TTS only on two mainstream measurement sections; on-ramp queue is shown only as a curve (Fig. 7); the reward is bottleneck speed (proxy); throughput is claimed but not tabulated.
  - **P2** Capacity drop assumed ("after the time-frame of capacity drop phenomena"), not demonstrated; demand "manually tuned" to induce congestion; terminated-run counts and teleports not reported.
    Q[f026 p10]: "Traffic demand in the simulation model is manually tuned in order"
  - **R1** No code link; number of training simulations not found.
- Good practice (G+): safety side metrics (aggressive braking, headway) reported and the increase in braking admitted; five strategies compared under one learner; excluded terminated runs disclosed; limits compliance mechanism stated; open access.
- Screen row check: agrees. "-9.1 %" bottleneck and "-3.1 % / -3.3 %" network reproduce (c.); "gain 4.5 from Wang 2011, not tuned" and "last 10 best" confirmed (p. 10, 12). Addition: terminated runs are excluded, and the 2-action DDPG is worse than SPSC.
- Not checked / uncertain: Figs. 6-11 read only via captions; hyper-parameters of exploration noise not located.

### #19 Cheng 2022, J. Adv. Transp. (ACVSL, DDPG) — file f003
- Structure / simulator / network: hybrid: DDPG chooses the continuous parameter λ of the authors' own density-error VSL law (Eq. 4-8) for mainline and 2 ramp sections every 2 min; reward = normalised bottleneck outflow (Eq. 13); VISSIM 5.3, 3-lane mainline + 1 ramp lane, 2 h runs (Sec. 2-4).
- Headline claim (p. 1, abstract):
  Q[f003 p1]: "enhance traﬃc ﬂow through the merging zone by around 10% and 19% under static and dynamic demand, respectively, in"
- Strongest comparator: EX-ACVSL, the best of 30 random-λ exploration epochs of the same law; plus Do-nothing. No ALINEA/SPSC/MPC/feedback controller or fixed-λ tuned law (searched whole file; ALINEA appears only in the literature review).
  Q[f003 p10]: "exploration, while 30 and 70 epochs in the training for the"
  Q[f003 p12]: "EX-ACVSL), and that of without control (i.e. Do-nothing)."
- Gain, Table 4 (p. 9) average flow, veh/h: static 4291 vs EX 3998: (4291-3998)/3998 = 7.3 % (c.), vs Do-nothing 3909: 9.8 % (c.); dynamic 4818 vs EX 4208: 14.5 % (c.), vs Do-nothing 4041: 19.2 % (c.). In the dynamic case EX-ACVSL has higher speed (47 vs 44 km/h) and lower density (94 vs 115 veh/km); the paper admits the speed result (p. 14).
  Q[f003 p9]: "Avg. 4,291 3,998 3,909 4,818 4,208 4,041"
  Q[f003 p13]: "DRL-ACVSL strategy by 7% and 10% under static demand,"
- Evaluation protocol: training demand 5400/1400 veh/h static, a rising/falling profile dynamic; test demand 5500/1500 static and a shifted profile (Table 3 test columns are +7 % to +25 % above training, c.); one 2 h simulation per test scenario; Table 4 "Std. DV" is across control steps within one run, not across seeds.
  Q[f003 p11]: "trained controller entails a 2 h simulation under static"
- Flags:
  - **B1/B2** Strongest comparator is the authors' own law with random λ (a weak tuning method with 30 draws, vs 30+30/70 learning epochs for DRL), plus no-control. No published controller. p. 10.
  - **E2** Meta-parameters "set with the best performance is adopted"; DRL result taken at the best epoch (24th/65th) chosen on training-demand flow; the selection data vs the test run is not separated explicitly.
    Q[f003 p9]: "with the best performance is adopted."
    Q[f003 p11]: "the 24th and 65th epoch, beating the best control scheme"
  - **S1/S2/S3** Single test run per scenario, no seeds, no CI/test; "significantly" used (p. 2).
  - **M1/M2** The headline metric (bottleneck outflow) is the training reward; no travel time/delay/queue reported (searched whole file); do-nothing outflow 3909 veh/h vs 7000 veh/h static demand (c.) shows large unserved demand not accounted for.
  - **C1** Abstract's "reduced density and speed variation by around 30 %" holds for density std (26.7 % static vs Do-nothing, c.) but speed std falls only 9 % in the dynamic case vs both (10 vs 11, Table 4).
  - **R1** Data "on reasonable request", no code; Table 2 lists Cv without a value; network layer sizes not stated.
    Q[f003 p15]: "from the corresponding author upon reasonable request."
  - **P2** Capacity-drop magnitude not demonstrated separately; teleports/collisions not reported (searched).
- Good practice (G+): test demand differs from training demand (Table 3); mean, median and std reported; the non-learning counterpart of the same law (EX-ACVSL) isolates the learning effect; reports the case where EX beats DRL (speed, dynamic).
- Screen row check: agrees. "+7 % / +14 %" is vs EX-ACVSL (+7.3 %, +14.5 %, c.); "best of 30 random λ" agrees (exploration = 30 epochs, p. 10); "single run" agrees (p. 11). Refinement: the +10 % / +19 % headline is vs Do-nothing, and the 14 % is truncated from 14.5 %.
- Not checked / uncertain: Fig. 6 (13 % / 19 % in training) and Fig. 12 are image-only; whether EX-ACVSL is a fixed λ or a time-indexed series is unclear from the text.

### #20 Vrbanić 2022a, Sustainability 14:932 — file f027
- Structure / simulator / network: centralised tabular Q-learning VSL (2-step TD, 14 density states, actions 60-130 km/h, 5-min control step) whose limits are posted only to electric CAVs (no VMS except at 0 % CAV) — Sec. 4, p. 7-8; SUMO via TraCI, 8 km synthetic motorway, 2 on-ramps, 1 off-ramp, 2 h runs — Sec. 5.1, p. 9; 7 CAV penetration scenarios 0-100 % — Sec. 5.2, p. 10; two rewards (r_TTS, r_TEC).
- Headline claim: Table 2/3 (p. 11-12), text p. 12-13: QL-VSL TTS -4.55 % vs baseline at 30 % CAV; conclusion says both rewards "outperform" baseline.
  Q[f027 p13]: "QL-VSL managed to reduce TTS and MTT by 4.55% and 3.1% compared to the baseline scenario"
- Strongest classical comparator: RB-VSL (HCM-LoS density rule, Eq. 7, p. 11). Parameters "set according to [7]" (authors' earlier paper); no tuning described.
  Q[f027 p11]: "the speed limit values were set according to [7]"
- Gain vs RB-VSL (c., TTS, Table 2, p. 11), 0/10/30/50/70/90 % CAV: (779.7-778.2)/779.7 = 0.19 %; (718.6-709.7)/718.6 = 1.24 %; (687.8-656.5)/687.8 = 4.55 %; (613.9-611.8)/613.9 = 0.34 %; (571.9-560.9)/571.9 = 1.92 %; (491.2-487.5)/491.2 = 0.75 %; 100 %: 0 (identical). Table 3 (r_TEC) vs RB: 1.65 / 0.64 / 4.14 / 0.13 / 3.57 / 1.95 % (c., p. 12). At 30 % CAV, RB-VSL TTS equals baseline (687.8, p. 11), i.e. RB is inactive there.
- Evaluation protocol: Q-function learned per scenario with 2000 training runs (p. 10); results are single numbers per scenario; the table is not stated to be a held-out greedy evaluation; demand profile is one fixed profile (Fig. 3). Seeds/replications: not found in text (searched seed, replic, random, average, standard dev, confidence).
  Q[f027 p10]: "Then, 2000 simulations for each defined scenario were performed to learn the QL-VSL policy."
- Flags:
  - **E2** Hyperparameters (theta, lambda) were selected by the summed TTS gain over the same scenarios that are then reported (Appendix A, p. 16-18); the reported setting is the best of nine (c.: sum of TTS over 0-90 % CAV, 3797.0 for the chosen block vs 3799.2-3839.2 for the others, Table A1).
    Q[f027 p16]: "The best combination of those hyper-parameters is chosen based on the sum of improvements of TTS for QL-VSL"
  - **S1/S2/S3** No seeds, no dispersion, no test for any gain. The spread across the nine hyperparameter settings at 30 % CAV is 656.5-682.8 (Table A1, p. 17-18), i.e. 26.3/687.8 = 3.8 % of baseline (c.), the same order as the 4.55 % headline.
    Q[f027 p12]: "The TTS for the QL-VSL control strategy converged to 657.8 veh·h after approximately 1500 training episodes"
  - **N1** Fig. 4 text gives 657.8 for the converged TTS at 30 % CAV vs 656.5 in Table 2 (p. 11); Table A1 last block gives 770.6 at 0 % CAV vs 778.2 in Table 2 (p. 18 vs p. 11; block identified by position, label layout is ambiguous); text attributes "17.22 % from 23.4 to 19.4" to r_TTS at 90 % CAV, but those printed values are Table 3 (r_TEC), 70 % CAV (Table 2 90 % CAV is 18.2 -> 17.8).
    Q[f027 p13]: "mean ρm significantly for the scenario with 90% CAVs by 17.22% from 23.4 veh/km/ln to 19.4 veh/km/ln"
  - **C1** "significantly" used for density/TTS changes without any statistical test (p. 13).
    Q[f027 p13]: "Furthermore, mean ρm was significantly improved by 9.89%"
  - **M1** TTS/MTT are over the whole modelled segment; no throughput, no statement on origin/insertion queues.
    Q[f027 p10]: "TTS and MTT were measured on the entire modeled motorway segment"
  - **B2** RB-VSL thresholds not tuned/justified here (see above); **P2** capacity drop, teleports and collisions not reported (searched whole file); **R1** no code/data statement found (searched code, github, availab).
- Good practice (G+): full 9-point hyperparameter table disclosed (App. A); convergence curves shown; classical RB-VSL comparator in addition to no-control; 7 penetration levels; authors state VSL is "obsolete" at 100 % CAV (p. 14-15); vehicle/emission models parameterised from real vehicle data (p. 10).
- Screen row check: agrees (0.2-4.6 % TTS range matches Table 2 vs RB-VSL; "hyperparameters picked on test" confirmed, App. A p. 16).
- Not checked / uncertain: Figs. 1-3 (images); whether Table 2 values are last-run or best-run is not stated.

### #21 Vrbanić 2022b, MED 2022 — file f035
- Structure / simulator / network: STM-QL-VSL: same tabular QL as #20 but state from Speed Transition Matrices of CAV probe data (20 segments), reward = proportional TTS; one (VSL1) or two (VSL2) control zones — Sec. III-IV, p. 3-4; SUMO, same synthetic motorway (2 on-ramps, 1 off-ramp), 24 x 5-min steps; 6 CAV penetration scenarios 10-100 % — p. 4.
- Headline claim: abstract p. 1 and Sec. VI p. 6: both configurations "outperform both no control and RB-VSL in all MoEs for each mixed traffic flow scenario".
  Q[f035 p6]: "outperform both no control and RB-VSL in all MoEs for"
- Strongest comparator: no control or RB-VSL, whichever is lower per scenario (RB-VSL is worse than no control in scenarios 1, 3, 4, 5 and better only in scenario 2, Table I p. 5). RB-VSL "modeled in the same way as in our previous works [5], [7]"; thresholds not given in this paper.
- Gain vs best of {NC, RB} (c., TTS veh-h, Table I p. 5): sc.1 (713.0-702.4)/713.0 = 1.49 % (STM1); sc.2 (649.3-635.8)/649.3 = 2.08 % (STM2; STM1 1.0 %); sc.3 (627.4-618.6)/627.4 = 1.40 %; sc.4 (548.4-542.6)/548.4 = 1.06 %; sc.5 (489.2-488.5)/489.2 = 0.14 %; sc.6 0. Printed "Improvement" columns are relative to no control only.
- Evaluation protocol: policy learned per scenario with 2000 simulations (p. 4); results one number per cell; same demand profile for training and evaluation (Fig. 2). Seeds/replications/dispersion: not found in text (searched seed, replic, averag, repeat).
  Q[f035 p4]: "separately by performing 2000 simulations for each scenario."
- Flags:
  - **C1** "all MoEs ... each scenario" is contradicted by Table I: STM-QL-VSL2 in scenario 4 is worse than no control on TTS (548.9 vs 548.4) and MTT (279.1 vs 278.6); in scenario 1 STM2 is worse than RB-VSL on mean speed (61.4 vs 62.3) and density (36.9 vs 36.5); scenario 6 is a 3-way tie.
    QI[f035 p5]: "STM-QL-VSL2 548.9 279.1 95.4 19.2 -0.1 -0.2 0.0 -1.1"
  - **S1/S2/S3** single run per cell, no dispersion; gains of 0.1-1.5 % are small relative to any plausible run-to-run noise (not measured here).
  - **E1/E2** hyperparameters (lambda = 0.9) taken from a sensitivity analysis in [7] on the same simulator and demand; evaluation on the training scenario.
    Q[f035 p3]: "and it was set to 0.9 based on performed sensitivity analysis"
  - **B2** RB-VSL not tuned, thresholds only by reference to [7].
    Q[f035 p4]: "RB-VSL algorithm was modeled in the same way as in our previous works [5],"
  - **M1** TTS/MTT summed over all edges and ramps, but queue/insertion backlog and throughput are not reported.
    Q[f035 p4]: "mented edge and on- and off-ramps, while ρ and v were"
  - **P2** capacity drop / teleports / calibration not reported; **R1** no code/data statement found.
- Good practice (G+): both a 1-zone and a 2-zone variant reported, including cases where the variant is worse; honest observation that RB-VSL is worse than no control in most scenarios and that VSL is useless at 100 % CAV (p. 5-6).
- Screen row check: partly disagrees. Screen gives "0...-1.5 % TTS" (matches STM1 only); STM2 reaches 2.08 % vs RB-VSL in scenario 2 (c., Table I p. 5). Note also that the no-control TTS at the same nominal CAV share differs from #20 (e.g. 30 %: 664.4 here vs 687.8 in f027 Table 2) with no explanation (uncertain: set-ups may differ).
- Not checked: Figs. 2-5 (images).

### #22 Xiao 2022, IET ITS 16 — file f034
- Structure / simulator / network: tabular Q-learning (softmax + epsilon-greedy), state = (mainline density, off-ramp queue, vehicles passed) 11x11x11, action = mainline speed limit 40-90 km/h in 5-km/h steps, 60 s cycle — Sec. 3.2, p. 4-6; VISSIM + Python COM, 2-lane 1.6 km mainline with a single-lane off-ramp feeding a signalised intersection (Wuhan Second Ring data) — Sec. 4, p. 6-7. Three schemes: free control, queue rule, Q-learning (Table 1, p. 7).
- Headline claim: Table 2 (p. 8): TTT 268.43 / 214.13 / 183.19 h; text: Q-learning (Scheme 2) "performs the best".
  Q[f034 p8]: "is 16.69% in comparison to Scheme 1."
- Strongest comparator: Scheme 1, mainline VSL driven by off-ramp queue length with fixed thresholds (80/70/60/50/40 km/h); activates when "queue exceeds half of ramp" (Sec. 4.4.2, p. 7). Thresholds are stated, the way they were chosen is not.
  Q[f034 p7]: "the queue length of off-ramp exceeds half of ramp, the"
- Gain vs Scheme 1 (c., Table 2 p. 8): TTT (214.13-183.19)/214.13 = 14.45 %; delay (12.58-10.48)/12.58 = 16.69 %; speed (62.08-59.82)/59.82 = 3.78 %; service volume 4661 -> 4657 veh (-0.09 %). Matches the printed 14.45 % / 16.69 % / 3.8 %.
- Evaluation protocol: one demand profile (2 h peak, Wuhan data, Sec. 4.2, p. 6); Q-table trained for ~120 episodes (convergence, Fig. 6, p. 8), then the same scenario is simulated for Table 2. No seeds, replications, dispersion or test (searched seed, replic, repeated, random).
  Q[f034 p8]: "After the training times reach 120, the reward function tends to be steady, which is regarded as convergence."
- Flags:
  - **N1** Printed 32.75 % (TTT, Scheme 2 vs 0) vs (268.43-183.19)/268.43 = 31.75 % (c.); conclusion's delay reduction vs Scheme 0 "37.60 %" vs (17.35-10.48)/17.35 = 39.60 % (c.); conclusion's "27.49 %" vs Scheme 1 contradicts the 16.69 % printed in Sec. 5.2 (c. 16.69 %).
    Q[f034 p9]: "average delay is reduced by 37.60% and 27.49%, respectively."
  - **E1/S1/S2/S3** train = test on one scenario, single run, no dispersion.
    Q[f034 p10]: "may be tried to improve the accuracy. The scenario assumed"
  - **B2/B3** rule comparator: derivation of thresholds not stated; no tuning on separate seeds; not tuned at all as far as stated.
  - **C1** Title/abstract frame the work as a "connected and autonomous vehicles environment", but the method and simulation sections contain no CAV modelling (searched whole file for CAV: only intro/discussion); the sole statement is hypothetical.
    Q[f034 p9]: "Under the environment of CAV, VSL may become more suit-"
  - **M1** TTT scope (which links, inclusion of ramp queue vehicles) is not defined; service volume is reported (G+ partly).
  - **P2/R1** no capacity-drop evidence, calibration or teleport statement; data only "upon request".
    Q[f034 p10]: "by Mr. Shengyang Kang, which may be available upon request"
- Good practice (G+): throughput (service volume) reported next to TTT, delay and speed (Table 2); the authors list the single scenario and slow convergence as drawbacks (p. 10); both TTT and queue-time-series figures shown.
- Screen row check: agrees (-14.5 % TTT = 14.45 % vs the rule, c.). Imprecision: the screen says rule parameters "[not stated]"; the thresholds are stated (p. 7), only their derivation is missing.
- Not checked: Figs. 5-10 (images), the stochasticity of the VISSIM demand.

### #23 Wang C. 2022, IEEE T-ITS 23(9) — file f028
- Structure / simulator / network: centralised DDPG/TD3 (prioritised replay, extra exploration) outputting a joint action for 1 RM + 2 VSL (scene 1) or 3 RM + 4 VSL (scene 2) every 60 s; reward = 0.25 speed + 0.25 on-ramp queue term + 0.5 waiting vehicles — Sec. V-VI, p. 6-9; SUMO, 2 km Drechttunnel-like bottleneck (scene 1), 6.5 km Alicante-Murcia (scene 2), 2 h episodes, 200 training episodes (Table VI, p. 10).
- Headline claim: abstract p. 1; Sec. VII-C p. 11 (from Fig. 11): IFBC saves 12.5 %, DRL 20.83 % vs FTC; abstract "more than 20 %".
  Q[f028 p1]: "superior to other methods and can save more than 20% of the"
- Strongest classical comparator: IFBC = PI ramp metering + integral-feedback VSL "modified from [7]" (Sec. III-C, p. 4-5), gains K_I = 15, K_p = 40, occupancy 30 %, queue limit 15 veh; no tuning method stated. FTC is fixed-time metering with 30 s green/red (p. 10), not tuned.
  Q[f028 p5]: "K I = 15, K p = 40"
- Gain vs IFBC (c., values read from text of Fig. 11, p. 11): FTC ~1200 h, IFBC ~1050 h, DRL ~950 h; (1050-950)/1050 = 9.5 %; vs FTC (1200-950)/1200 = 20.83 % (matches printed); IFBC vs FTC (1200-1050)/1200 = 12.5 % (matches). The text itself says "slightly outperformed". Scene 2: only FTC vs DRL, (4620-3000)/4620 = 35.1 % (c., p. 12); IFBC is not run in scene 2.
  Q[f028 p11]: "DRL methods slightly outperformed the IFBC method, this is"
- Evaluation protocol: "results after 200 episodes of training"; Fig. 11 plots total travel time per training episode (mean line + std band); no separate test seeds/scenarios or greedy evaluation phase described (searched test, seed, random: only exec-time tests). Exec time "ran ten times" (p. 13) is for runtime only.
  Q[f028 p11]: "training (which are 400 simulation hours) are demonstrated"
  Q[f028 p13]: "Every case ran ten times to"
- Flags:
  - **E1** headline gain is read from training-episode curves (rendered Fig. 11, p. 11, QI): TD3C trace ends near 950-1000 h, DDPGC near 1000-1050 h, IFBC ~1050 h, with overlapping std bands; no held-out evaluation. Because curves include exploration noise (p. 12) this may be conservative for DRL, but the text value "around 950" is not tied to a stated episode window.
    Q[f028 p11]: "time of IFBC is about 1050 hours, and the total travel time of"
  - **B2** IFBC gains/thresholds copied/modified from [7], tuning not stated; FTC untuned (fixed 30 s phases).
    Q[f028 p10]: "ing signal circulates in a fixed phase sequence, with"
  - **B1/C1** scene-2 claim (35 %) is only against FTC; "outperforms other control methods" in the conclusion rests on a ~10 % gap read from a figure.
    Q[f028 p12]: "3000 hours on average, saving 35% more time than the FTC"
  - **S1/S3** one training run per algorithm, no significance test between DRL and IFBC; what the std band is taken over (time steps, replicates, seeds) is not stated.
  - **M1** TTT "includes ... waiting time on the road"; ramp-queue/insertion treatment and throughput not reported for scene 1.
    Q[f028 p11]: "travel time includes vehicle traveling time and waiting time on"
  - **P1/P2** no demonstration of capacity drop in SUMO, no calibration beyond "as accurate as possible", teleports not reported; vehicles assumed to obey commands.
  - **R1** hyperparameters listed (Table VI, image) but no code/data statement found.
- Good practice (G+): same states/actions/rewards for all methods (p. 11); both RM and VSL in the benchmark with an on-ramp queue limit equal to the DRL's (15 veh); two networks; learning curves with std bands; hyperparameter table.
- Screen row check: agrees. "-9.5 % (c., Fig. 11)" reproduces; "evaluated on training episodes" is confirmed (Fig. 11 = training curves). Caveat: 9.5 % rests on the text's approximate "about/around" values; the figure shows overlapping bands.
- Not checked: Tables III-IV (demand, image only), Fig. 14 values beyond the text.

### #24 Lu 2023, TR-C 153:104221 (TD3LVSL) — file f005
- Structure / simulator / network: lane-level VSL, each lane cell an agent, TD3 actor-critic with floor-mapped continuous action to 40-70 mph in 5-mph steps, 60 s cycle, hybrid reward (speed + TTC safety); SUMO, SR-91 bottleneck from PeMS data, 4 lanes, 3 control segments x 100 m, 4 h runs, **100 % CAV** with full compliance — Sec. 3-4, p. 5-13.
- Headline claim: abstract p. 1; conclusion p. 20: TD3LVSL beats DDPG-based LVSL; Table 5 p. 16.
  Q[f005 p20]: "(3) The TD3LVSL approach outperforms the state-of-the-art approaches in terms of improving traffic safety and efficiency."
- Strongest comparator: DDPGLVSL (RL). No rule-based, feedback or MPC VSL controller is compared; benchmarks are NoVSL, TD3RVSL (segment-level), DQLLVSL, DDPGLVSL (Sec. 4.3, p. 13).
  Q[f005 p13]: "This paper compares the TD3LVSL with several state-of-the-art methods as follows."
- Gain (c., Table 5 p. 16, TTS veh-h): vs DDPGLVSL (26.13-25.67)/26.13 = 1.76 % (matches printed, p. 15); vs NoVSL (29.87-25.67)/29.87 = 14.06 %, printed "-16.37 %" -> **N1**. Same mismatch for others: TD3RVSL 2.95 % (printed 3.04), DQLLVSL 9.31 % (10.26), DDPGLVSL 12.52 % (14.34). Mean-speed percentages are consistent (e.g. 40.91/24.11 = +69.68 %). Section 5.2 says the table averages per-simulation-hour values (p. 15), which may explain the gap (uncertain).
  Q[f005 p16]: "TD3LVSL 40.91 69.67% 25.67 − 16.37%"
- Evaluation protocol: 130 scenarios sampled around hourly mean/SD of PeMS data (Table 2), 100 train / 30 test (Sec. 4.2, p. 12); results are means over test scenarios per hour (p. 15). Number of training seeds: not stated; dispersion on Tables 5-6: none.
  Q[f005 p12]: "100 of these scenarios are used to train the RL-based control approaches, and the other 30 scenarios are used for testing."
- Flags:
  - **B1** no classical comparator; the best comparator is another RL variant. Gain over it is 1.76 % TTS.
  - **S2/S3** no seed count, no std/CI/test on a 1.76 % TTS gap between two RL agents; the authors themselves note the gap is small at high flow.
    Q[f005 p16]: "Even under the high-flow conditions, the TD3LVSL still has little improvement compared with"
  - **E2** hyperparameters of TD3LVSL (hidden units 192, delay interval 4, reward weight) chosen from Figs. 12-14 on "performance"; which of the 100/30 scenarios were used is not stated. DDPGLVSL is given the same architecture rather than its own tuning.
    Q[f005 p15]: "policy updates η are chosen to be 192 and 4 in the following experiment."
    Q[f005 p13]: "including the number of hidden layers and the number of hidden units."
  - **M1/M2** mean speed is measured "in the bottleneck area" only and is both the reward and a headline (+69.67 %); TTS definition is inconsistent ("total time speeding" vs "total travel time"); throughput and ramp/insertion backlog not reported.
    Q[f005 p14]: "TTS denotes the total travel time of the vehicles in the simulation system"
  - **C1** "outperforms the state-of-the-art approaches" while the comparator set contains no classical VSL (see above); safety gains are SUMO-TTC surrogates.
  - **P2** capacity drop shown from PeMS (Fig. 8) but not demonstrated in SUMO; IDM parameters taken from literature; teleports/collisions not reported; 100 % CAV, full compliance.
    Q[f005 p12]: "the vehicle in the training and testing are all CAVs that can fully obey the speed limits"
  - **R1** "Data will be made available on request" (p. 20).
- Good practice (G+): held-out test scenarios (30 of 130); demand sampled from real PeMS statistics with SDs (Table 2); ablations on reward weight, control-area length, control cycle, CAV penetration/speed factor (Figs. 14-22); both efficiency and safety indices.
- Screen row check: mostly agrees ("-1.8 % TTS" vs other RL, "no classical baseline"). Disagrees on "-16.4 % vs NC": that is the printed value, but the value derivable from printed TTS is 14.06 % (c., Table 5).
- Not checked: Figs. 12-22 (image-only) and whether the 100/30 split was used for Sec. 5.1 selection.

### #25 Chen X. 2023, ICCSSE 2023 — file f018
- Structure / simulator / network: lane-level TD3 VSL (5 actuators: 4 mainline lanes + ramp speed limit 5-40 km/h), reward = inflow - outflow in the section, 5-min control period; SUMO, 2.5 km Hangzhou-Ningbo Expressway merge, 6 h demand from one holiday day (M2M) plus simulated ramp, Poisson demand per period — Sec. III-IV, p. 3-5.
- Headline claim: abstract p. 1; conclusion p. 6: ATS +12.3 % vs no VSL.
  Q[f018 p1]: "that the VSL control based on TD3 can effectively reduce average"
  Q[f018 p6]: "indicator, using VSL improves traffic efficiency by 12.3%"
- Strongest comparator: no control (fixed {100,100,120,120,40} km/h) only; no classical or RL comparator.
  Q[f018 p5]: "In this study, we conducted a baseline simulation under"
- Gain (c., Table II p. 6, ATS m/s): (20.9-18.6)/18.6 = 12.37 %, printed 12.3 %; per hour 0.5 / 3.9 / 15.2 / 34.7 / 22.2 / 8.4 %; recomputed 0.4 / 3.9 / 15.4 / 35.3 / 22.4 / 8.5 % are within 1-decimal rounding of the printed inputs. No travel-time, delay or throughput result is printed anywhere in the file.
- Evaluation protocol: 200 training episodes (p. 4-5); the with-VSL ATS is "collected" from a run on the same demand model (Poisson per period, one demand profile), no held-out test set, seeds or replications stated; single time series in Fig. 8.
  Q[f018 p4]: "volume in each period followed a Poisson distribution. Trucks"
- Flags:
  - **B1** only no-control comparator.
  - **M2/C1** abstract claims reduced "average travel time" and more "passing vehicles"; neither is reported (whole file searched; results are ATS only, Table II p. 6). ATS is also close to the reward's logic (flow-based) and not defined as space- or time-mean.
  - **E1/S1/S2/S3** train = test demand model, single representative run, no dispersion, number of seeds not stated.
  - **B4** RL controls the ramp speed limit (5-40 km/h) in addition to lane limits, while the baseline is fixed; with a 5 km/h ramp limit this can act like metering and may hold vehicles out of the measured section (ATS scope not stated).
    Q[f018 p4]: "is {5, 10, 15, 20, 25, 30, 35, 40}(km/h)."
  - **M1** ATS section scope/inclusion of ramp-queued vehicles not stated.
  - **P2/R1** capacity drop shown conceptually (Fig. 1-2), not measured in the sim; no calibration, teleport/collision report; all vehicles comply (stated limitation); no code/data statement; RL hyperparameters (Table-level) not found.
    Q[f018 p6]: "The limitation of this study is that we assumed all vehicles"
- Good practice (G+): demand from a measured holiday-peak flow; states the full-compliance limitation; per-hour breakdown showing that gains vanish at low demand (Table II).
- Screen row check: agrees (NC only; +12.3 % speed).
- Not checked: Figs. 6-8 (images).

### #26 Hua & Fan 2023, IET Intell. Transp. Syst. 17:2519-2530 — file f020
- Structure / simulator / network: direct, single-agent DDPG with differential per-lane limits (Sec. 3.1.3, p. 4); the action dimension is 6, "from 50 to 75 mph with an increment of 5 mph" (Sec. 4.2, p. 6); SUMO; 2 km I-80 northbound weaving segment, 4 mainline lanes, 5 lanes in the weaving area (Sec. 4.1, p. 6). State = lane occupancies, dim 10 (Sec. 3.1.2, p. 4). Mixed traffic, CAV market penetration 0/25/50/75/100 %.
- Headline claim: DSH improves mobility and safety vs no control at all MPRs (Table 2, p. 8; Conclusion, p. 10).
  Q[f020 p1]: "the proposed method can enhance mobility and achieve co-benefits with safety"
- Strongest classical comparator; how set: none. The only comparator is no control (NC); no rule-based, feedback or MPC VSL is run.
  Q[f020 p8]: "The comparison is based on no control without"
- Gain vs strongest comparator (recomputed): Table 2 (p. 8) prints DSH mean travel time as improvement vs NC at 0 % MPR (82.48 s): 5.21, 4.92, 4.50, 4.55, 4.62 %; NC itself: 0, 0.18, -0.05, 0.12, 0.75 %. Same-MPR comparison, e.g. at 100 %: 1 - (1-0.0462)/(1-0.0075) = 1 - 0.9538/0.9925 = 3.90 % (c., Table 2, p. 8); at 25 %: 1 - 0.9508/0.9982 = 4.75 % (c.); 50 %: 4.55 % (c.); 75 %: 4.44 % (c.). So the like-for-like range is about 3.9-5.2 % (c.). Against NC only.
  Q[f020 p8]: "Mean travel time(s) No 82.48 0.18% −0.05% 0.12% 0.75%"
  Q[f020 p8]: "DSH 5.21% 4.92% 4.50% 4.55% 4.62%"
- Evaluation protocol: 300 training episodes (Fig. 5, p. 6); 20 test episodes averaged (Sec. 5.2, p. 8); demand drawn at random each episode from Poisson means taken from PeMS (Sec. 4.2, p. 6). No std/CI, no seed list, no statement of which checkpoint is tested (searched whole file for "seed", "std", "confidence": not found).
  Q[f020 p8]: "performances over 20 test episodes."
  Q[f020 p6]: "and the demand is randomly generated for each"
- Flags:
  - **B1** Only no-control comparator; no classical VSL (rule, feedback, MPC) and no other RL. Table 2, p. 8.
    Q[f020 p8]: "The comparison is based on no control without"
  - **M2** Training reward is cumulative emergency deceleration (a safety proxy), while the mobility headline is mean travel time; MTT scope (arrived vehicles only? origin queues?) and throughput are not defined or reported (searched whole file for "throughput", "queue": only discussed qualitatively). Sec. 3.1.4, p. 5; Table 2, p. 8.
    Q[f020 p5]: "a safety-oriented function as r"
  - **E1** Same Poisson demand distribution for training and testing; no held-out demand pattern (only fresh random draws, if the 20 test episodes are fresh; not stated). Sec. 4.2, p. 6.
    Q[f020 p6]: "and the demand is randomly generated for each"
  - **S2/S3** Seeds/replications of training not stated; no dispersion on a 3.9-5.2 % travel-time gain. Table 2, p. 8.
    Q[f020 p8]: "performances over 20 test episodes."
  - **P2** SUMO built-in parameters, no capacity drop shown, teleports/collisions not reported (searched whole file for "teleport": not found). Sec. 4.2, p. 6.
    Q[f020 p6]: "This study mainly utilizes the built-in parameters in"
  - **R1** Hyperparameters "fine-tuned after many trials" (selection set not stated); code/data on request only. p. 5, p. 11.
    Q[f020 p5]: "All hyperparameters in this work were fine-"
    Q[f020 p11]: "are available from the corresponding author upon reasonable"
- Good practice (G+): reports the environmental trade-off honestly (CO2 and fuel worse than NC at 0 % and 25 % MPR: DSH -9.51 %, -1.76 %, Table 2, p. 8); hyperparameters (Sec. 3.2, p. 5) and the demand means (Sec. 4.2, p. 6) are given in the text; MPR sweep; headway sensitivity (Fig. 7, p. 10).
- Screen row check: mostly agrees (direct DDPG, SUMO I-80 weave, NC only). Imprecise: the screen's "-4.5...-5.2 %" is the printed DSH column (vs NC at 0 % MPR, 4.50-5.21 %); the like-for-like range vs NC at the same MPR is about 3.9-5.2 % (c.). Screen's "full" read: confirmed full text.
- Not checked / uncertain: Fig. 7 (headway sensitivity) is an image and was not read numerically; the exact definition of "mean travel time" (which vehicles) is not stated, so M1 is "not defined", not "excluded".

### #27 Zhang Y. et al. 2023, IEEE SMARTCOMP — file f012
- Structure / simulator / network: direct cooperative MARL (MAPPO, CTDE, shared parameters), discrete limits 30/50/70 mph; TransModeler; 7-mile, 4-lane I-24 westbound, 3 ramps; 5 agents in training, 10 in testing (Sec. III-IV, p. 3-5).
- Headline claim: "significant reduction in speed variation"; "performs satisfactorily under varying traffic demand and compliance rates" (Abstract, p. 1). Safety metric (CVS) improved "up to 32.7 %" with "up to 6.5 %" mobility cost (Sec. V-C, p. 8).
  Q[f012 p8]: "metric can be improved up to 32.7% with a little negative"
- Strongest classical comparator; how set: none. Only no control (Table II, p. 7).
  Q[f012 p7]: "No control 0.52 (0.01) 0.52 (0.01)"
- Gain vs strongest comparator (recomputed, vs NC): CVS B (0.52-0.35)/0.52 = 32.7 %; C (0.52-0.36)/0.52 = 30.8 % (c., Table II, p. 7). Delay (VHD, veh.hr), worse than NC: B (304.59-289.98)/289.98 = +5.04 %; C (715.26-671.65)/671.65 = +6.49 % (c., Table II, p. 7). The printed mean differences (14.61 and 43.61) are smaller than the printed std of either arm in B (22.27, 20.01) and comparable in C (36.27, 41.81).
  Q[f012 p7]: "MARL-VSL 304.59 (20.01) 715.26 (41.81)"
- Evaluation protocol: train on one scenario (flow 1850 veh/lane/hr, on-ramp ~1000 veh/lane/hr, 100 % compliance, 5 agents; Sec. IV-A, p. 5). Test A/B/C with 10 agents and 5 % compliance; "10 experiments" per arm, mean (std) in Table II (Sec. V-C, p. 8). Scenario A is not in Table II (no congestion). Scenario B uses the same mainstream flow as training.
  Q[f012 p5]: "set high enough as 1850 veh/lane/hr for the"
  Q[f012 p5]: "of 1850 veh/l/hr, 5% com-"
  Q[f012 p8]: "We run 10 experiments with and without MARL-VSL"
- Flags:
  - **B1** Only NC; no rule/feedback/MPC VSL. Table II, p. 7.
    Q[f012 p7]: "No control 0.52 (0.01) 0.52 (0.01)"
  - **M2** The safety headline is CVS, which is also built into the reward (global safety term), and the mobility metric (VHD) is worse than NC in both tested scenarios; no crash or conflict measure. Eq. 6-7 (p. 4), Eq. 14-15 (p. 5), Table II (p. 7).
    Q[f012 p4]: "CVS values among all agents at timestep t using the following"
    Q[f012 p5]: "of Variation in Speed (CVS) and the Vehicle Hours Delay"
  - **M1** VHD is detector-volume based (Eq. 15, p. 5); on-ramp / origin queues and throughput are not reported.
    Q[f012 p5]: "of Variation in Speed (CVS) and the Vehicle Hours Delay"
  - **E1** (partial) Scenario B is described as similar to the training demand; B differs from training only in compliance (5 % vs 100 %) and agent count. p. 6.
    Q[f012 p6]: "Scenario B has similar"
  - **C1** "significant reduction", "generalizes", "robustness ... compliance" without a significance test; the CVS drop at 5 % compliance is not explained (Abstract p. 1; Sec. V-B p. 6; Conclusion p. 8).
    Q[f012 p6]: "the compliance rate in all three testing scenarios is around 5%"
  - **P2** Default TransModeler car-following, no calibration or capacity-drop demonstration, teleports/collisions not reported (searched whole file: not found). Sec. IV-C, p. 5.
    Q[f012 p5]: "car following model is selected in TransModeler."
  - **R1** Hyperparameters given (Table I, p. 5); no code or data statement found (searched "github", "available", "code").
- Good practice (G+): discloses the delay penalty (+5.0 / +6.5 %) and does not hide it (Sec. V-C, p. 8); reports mean (std) over 10 runs; scalability tested with 10 agents after training with 5.
  Q[f012 p8]: "noted that despite the observed slight increase in VHD under"
- Screen row check: agrees (NC only; delay +5.0 % / +6.5 %, worse). Screen's "full" confirmed.
- Not checked / uncertain: whether the 10 NC and 10 MARL runs are paired by seed (not stated). The mechanism for a -31 % CVS at 5 % compliance is not explained in the text (not an error per se).

### #28 Zhang Y. et al. 2024 (MARVEL), IEEE Access 12:161995-162013 — file f030
- Structure / simulator / network: direct MARL (MAPPO / IPPO, MAPPO + invalid-action masking), 5 levels 30-70 mph, sequential decisions with the downstream action in the state; TransModeler; training on a 7-mile corridor with 8 agents (p. 9), testing on the 17-mile I-24 Smart Corridor with 34 gantries (p. 9-10).
- Headline claim (abstract, p. 1):
  Q[f030 p1]: "63.4% compared to the no-control scenario and enhances traffic mobility by 58.6% compared to a state-of-"
- Strongest classical comparator; how set: Speed-Matching (deployed on I-24, rule-based). Thresholds: tuning method and scenario not stated (Sec. V-C, p. 10).
  Q[f030 p10]: "have been carefully searched to achieve"
- Gain vs strongest comparator (recomputed from Table 3, p. 15, read from the rendered image): CVS vs NC: A (0.43-0.18)/0.43 = 58.1 %; B and C (0.41-0.15)/0.41 = 63.4 % (c.). So 63.4 % is the best scenario, vs NC. CVS vs Speed-Matching: A 0.17 vs 0.18, B 0.15 vs 0.15, C 0.14 vs 0.15 (tie or Speed-Matching slightly better; 2-decimal rounding). Max queue length vs Speed-Matching: A (7.2-6.0)/7.2 = 16.7 %; B (8.7-3.7)/8.7 = 57.5 % (MAPPO), (8.7-3.6)/8.7 = 58.6 % (MAPPO-IAM); C (11.9-6.4)/11.9 = 46.2 % (c.). So 58.6 % is the best scenario and the best variant. Max queue length vs NC: B 3.7 vs 1.5, i.e. (3.7-1.5)/1.5 = +147 %; A 6.0 vs 4.8 = +25 %; C 6.4 vs 1.6 = +300 % (c.), i.e. MARVEL is worse than NC on the mobility metric.
  Q[f030 p14]: "baseline has the minimum queue length, the Speed-Matching"
- Evaluation protocol: train and test networks differ (geometry, demand, compliance 5 % in training vs 5 / 50 / 100 % in test); "10 stochastic experiments for each control method in each scenario" (p. 13); mean +/- std in Table 3 (image, p. 15); learning curves over three random seeds (Sec. VI-A, p. 11). No paired test.
  Q[f030 p13]: "We conducted 10 stochastic experiments for each control"
  Q[f030 p11]: "with three random seeds is presented in Fig. 4."
- Flags:
  - **M2** The mobility headline is maximum queue length (length of road below 35 mph), not delay/TTS/throughput, and it is the best of three scenarios and two variants; relative to NC the queue is longer in all three scenarios (Table 3, image, p. 15).
    Q[f030 p10]: "The mobility performance is evaluated using the queue"
    Q[f030 p15]: "under VSL control have a longer queue length than the No"
  - **B2/B3** Speed-Matching thresholds "carefully searched" with no method, no stated tuning scenario, and "original version ... without considering its potential revised versions".
    Q[f030 p10]: "Matching algorithm, without considering its potential revised"
  - **M1** No delay, travel-time, or throughput measure at all (searched whole file for "throughput": only in related-work context).
  - **P2** Default TransModeler car-following, no calibration; capacity drop not shown.
    Q[f030 p11]: "art commercial microsimulator without a massive calibration"
  - **C1** Abstract says "enhances traffic mobility by 58.6 %" without "up to" or the metric; the CVS result vs Speed-Matching is a tie (Table 3, image).
  - **E2 (uncertain)** Reward weights w1-w3 "selected via hyperparameter search"; the scenarios used for the search are not stated.
    Q[f030 p7]: "These particular values were selected via hyperparameter"
  - **R1** Hyperparameters in Table 2 (p. 11); no code/data statement found.
- Good practice (G+): out-of-distribution test networks (17 mi, 34 agents, 3 compliance levels) vs a separate training scenario; 10 stochastic runs with std; three training seeds; discloses that NC has the shortest queue (p. 14-15); open-loop check on real I-24 data; limitations section (p. 16-17).
- Screen row check: agrees on "safety +63.4 %", "carefully searched", "NC minimum queue", "uncalibrated". Imprecise: the screen does not give the mobility headline (58.6 % in max queue length vs Speed-Matching) and does not say 63.4 % is the best scenario and vs NC.
- Not checked / uncertain: all Table 3 numbers are from a rendered image (read at 130 dpi; digits legible); Table 1 (deployed VSL systems, p. 3) not read.

### #29 Pelenczei et al. 2024, ICINCO (vol. 2, pp. 117-124) — file f004
- Structure / simulator / network: cooperative multi-agent RL (independent learners, shared network, Q-learning with a neural net, 3 actions +/-10 km/h per zone); SUMO; synthetic 8 x 300 m, 3-lane segments, 18 VSL zones, random anomalies that create a lane-drop bottleneck (Sec. 4, p. 3).
- Headline claim: "enhanced performance of RL-based VSL control over traditional approaches" (Abstract, p. 1).
  Q[f004 p1]: "Our findings reveal an enhanced performance of RL-based VSL control over traditional ap-"
- Strongest classical comparator; how set: per metric: MCS (travel time), MTFC (waiting time, queue), FF = no control (emissions). MCS "predefined thresholds" and MTFC "integral gain" are described but no values or tuning method are given (searched whole file for "tun", "hyperparam", gain values: not found).
  Q[f004 p4]: "utilizes predefined thresholds in order"
  Q[f004 p5]: "where KI denotes the integral gain and e0 (t) is the"
- Gain vs strongest comparator (recomputed, high density, Table 1, p. 6): travel time vs MCS Uniform (312.6-275.6)/312.6 = 11.8 %, Poisson (295.9-277.2)/295.9 = 6.3 % (c.); waiting time vs MTFC (10.94-5.62)/10.94 = 48.6 %, (7.95-5.50)/7.95 = 30.8 % (c.); CO2 vs FF (2251.9-1953.6)/2251.9 = 13.2 % (printed 13.3 %), Poisson 13.1 % (c.). The "Minimal Performance Gain" row reproduces. MTFC is worse than no control on travel time: (434.0-314.7)/314.7 = +37.9 % Uniform, (441.1-305.9)/305.9 = +44.2 % Poisson (c.).
  Q[f004 p6]: "Uniform 11.8% 48.6% 50.0% 13.3% 14.5% 13.3%"
- Evaluation protocol: Table 1 = "average values of 100 test episodes in high traffic density"; Uniform and Poisson arrival distributions; normal-density results only in Fig. 5 (bar chart, image, p. 7). Training episodes/seeds/hyperparameters not stated; no std or CI anywhere.
  Q[f004 p6]: "Over 100 seeded pseudorandom test episodes, we"
- Flags:
  - **B2** MCS and MTFC parameters and tuning not stated; MTFC (a bottleneck-occupancy controller using "four detectors") is worse than no control on travel time and CO2, which is consistent with an untuned or mismatched baseline in a random-anomaly network. Table 1, p. 6; Sec. 5.1.3, p. 4-5.
    Q[f004 p5]: "The system integrates four detectors positioned"
  - **B4 (uncertain)** RL agents observe occupancy of all 18 zones; how MTFC's detector location is set when the anomaly position is random is not stated.
  - **M2/M1** The RL reward is the inverse of waiting time and the headline gains are largest on waiting time and queue length; SUMO waiting/travel-time scope (insertion backlog, departed vehicles) not defined; no throughput. Sec. 4.1.3, p. 4.
    Q[f004 p4]: "waiting time wt during the preceding ∆t time interval,"
  - **S2/S3** Seeds for training not stated; no dispersion; "the performance gain of cMARL increases with traffic density" is claimed from single means (Sec. 6, p. 7).
    Q[f004 p7]: "cMARL increases with traffic density, highlighting its"
  - **N1 (low confidence)** Units look inconsistent: "CO2 [kg/s]" 2251.9 and "Queue length [veh / s]" (Table 1, p. 6); probably label errors, flagged only because the numbers cannot be read as printed.
    Q[f004 p6]: "Uniform 314.7 16.21 29.46 2251.9 956.3 718.3"
  - **P2** Synthetic network, no calibration to field data, capacity drop and teleports/collisions not reported (searched whole file for "teleport", "calibrat": not found).
  - **R1** No RL hyperparameters, network, training length, or code statement (searched whole file).
- Good practice (G+): 100 seeded test episodes; two arrival distributions; compares three baselines, and reports the metric-wise minimal gain (uses the best baseline per metric); reports sustainability metrics; claims are bounded to the synthetic setting in the conclusion.
- Screen row check: numbers agree (-11.8 % / -6.3 % TT vs MCS, Table 1, p. 6). Imprecise: "baselines untuned" should read "baseline parameters and tuning not stated"; "MTFC worse than NC" holds for travel time and emissions, but MTFC is better than NC on waiting time and queue length (Table 1). The -11.8 / -6.3 % apply to high density only.
- Not checked / uncertain: Fig. 5 (image, p. 7): my visual reading is that cMARL travel-time bars at normal density look similar to FF/MCS, which would contradict "outperforms baseline methods across all traffic flow parameters" (p. 7), but I did not extract numbers; verify.

### #30 Jin J. et al. 2024, Accid. Anal. Prev. 201:107570 — file f010
- Structure / simulator / network: rule-gated direct RL; deep Dyna-Q (model-based RL) with a multilane CTM as planning model, K = 1/5/10 planning steps; safety trigger from a random-DCN crash-risk model (act only if predicted crash probability exceeds a threshold); SUMO; Robin Williams Tunnel, 4,000 ft section, two VSL signs (Sec. 3-4, p. 3-10).
- Headline claim: 16-20 % safety (conflicts) and 3-6.5 % efficiency vs a fixed speed limit; "outperform traditional VSL strategy based on the traffic flow prediction model" (Abstract, p. 1).
  Q[f010 p1]: "significantly increase traffic safety performance by"
- Strongest classical comparator; how set: MCTM_VSL (MPC + genetic algorithm on the MCTM). Parameters and tuning not stated. Strongest comparator overall is the model-free DRL_VSL (same algorithm family), which beats the proposed MBRL variants in absolute terms.
  Q[f010 p11]: "using a model predictive control framework and a genetic algorithm,"
- Gain vs strongest comparator (recomputed): time-loss reductions vs FSL (Table 8, p. 14; text p. 13): MCTM_VSL 5.00 % / 2.28 %; DDQ(1) 6.84 % / 3.16 %; DRL_VSL 7.15 % / 3.31 %. DDQ(1) vs MCTM_VSL: 1 - (1-0.0684)/(1-0.0500) = 1.94 % weekday; 1 - 0.9684/0.9772 = 0.90 % weekend (c.). DDQ(1) vs DRL_VSL: 6.84 vs 7.15 % (weaker). Conflicts (Fig. 11, image, p. 13): weekday MCTM 19346, DDQ(1) 17989, DRL 17430; (19346-17989)/19346 = 7.0 % (c.); weekend 6131 vs 5718 = 6.7 % (c.); DRL_VSL is better (22.99 % / 17.03 % vs FSL).
  Q[f010 p13]: "traffic efficiency, with a 5.00 % reduction in total time loss in the"
  Q[f010 p14]: "DDQ(1)_VSL Yes 4,644 20.52 1,127 16.46 5,617 6.84 625 3.16"
- Evaluation protocol: train on 5 h Weibull-generated demand (SL A-E), 180 episodes; test on two real-volume 5 h scenarios (weekday, weekend, 2-7 a.m.), different from training; evaluation metrics (TTC < 3 s conflicts, time loss within 500 ft of the tunnel) differ from the training reward (crash-risk + exit flow) (Sec. 4.2, 5.2, p. 10-11). Replications per scenario: not stated; no dispersion; single values per strategy (Fig. 11, Tables 6-8).
  Q[f010 p11]: "alternate indicators to evaluate traffic"
  Q[f010 p11]: "for all cars within 500 feet before and after the tunnel"
- Flags:
  - **S2/S3** No replication count, seeds, std or CI for any test result; "significantly" used without a test. Sec. 5.2, p. 11-14.
    Q[f010 p11]: "each scenario lasting 5 h and covering 600 control"
  - **B4 (uncertain)** The safety advantage comes from the rule-based trigger: without it the MBRL policy reduces conflicts by only 1.82 % / 2.35 % (DDQ(1)), vs 14.5 % / 10.4 % for MCTM_VSL (Fig. 11, image); it also reduces time loss more without the trigger (9.00 % / 5.30 %). Whether MCTM_VSL and DRL_VSL also run a trigger is not stated in the text I read (searched "trigger": no mention for them).
    Q[f010 p14]: "No 411 1.82 161 2.35 7,395 9.00 1,047 5.30"
    Q[f010 p14]: "VSL strategy with safety triggers is reported to be slightly less efficient"
  - **B2** MCTM_VSL (GA/MPC) horizon, weights and tuning not stated; not stated whether tuned on the test scenarios.
  - **M1** Both metrics are measured only within 500 ft of the tunnel; no throughput, no network-wide or origin-queue delay.
    Q[f010 p11]: "for all cars within 500 feet before and after the tunnel"
  - **N1** Text says each 5 h test covers "600 control intervals", while training uses 18,000 s episodes with 300 s cycles, 10,800 cycles over 180 episodes, i.e. 60 per 5 h (c.: 18,000/300 = 60; 180 x 60 = 10,800). The two agree only if the test cycle differs from 300 s, which is not stated. Sec. 4.2 (p. 11) vs Sec. 5.2.1 (p. 11).
    Q[f010 p11]: "each scenario lasting 5 h and covering 600 control"
  - **C1** "Significantly" / "outperform" vs MCTM_VSL rests on a 0.9-1.9 % time-loss difference with no dispersion (see arithmetic above); vs DRL_VSL the proposed method is weaker and wins only per unit training time.
  - **R1** "Data will be made available on request"; MCTM/GA parameters partially given (Tables 1-2, p. 10).
    Q[f010 p15]: "Data will be made available on request."
- Good practice (G+): held-out demand (training demand is synthetic Weibull, test is real volume); evaluation metrics differ from training reward (stated "impartiality of assessment criteria", p. 11); SUMO calibrated against detector data with all GEH < 4 and speed difference < 3 mph (Sec. 5.1, p. 11); reports honestly that DRL_VSL is best in absolute performance and the trigger costs efficiency; sample-efficiency ablation over K.
- Screen row check: mostly agrees (rule-gated, Dyna-Q, MCTM-MPC [GA], -1.9 % / -0.9 %: reproduced with DDQ(1) vs MCTM_VSL on time loss). Imprecise: "2 runs" is two test scenarios (weekday, weekend); the number of replications per scenario is not stated. The screen's comparator omits that the model-free DRL_VSL is stronger than every MBRL variant in absolute terms.
- Not checked / uncertain: Fig. 11 values read from a rendered image (p. 13); Fig. 12 (time-loss series) not rendered; Table 8 was used for the time-loss percentages.

### #31 Jin J. et al. 2025, Expert Syst. Appl. 267:126277 — file f042
- Structure / simulator / network: rule-gated direct DRL (D3QN, weighted-sum reward 0.6 safety / 0.4 efficiency), safety trigger at crash probability 0.4; SUMO; Robin Williams Tunnel, 1,250 m section, two VSL signs (Sec. 3-4, p. 5-8).
- Headline claim: 14-19 % safety and 2-4 % efficiency vs fixed speed limit (Abstract, p. 1).
  Q[f042 p1]: "strategy significantly improves traffic safety performance by 14–19% and traffic efficiency by 2–4% compared to"
- Strongest classical comparator; how set: none. Comparators are the fixed speed limit (FSL) and RL variants of the same algorithm (DRL_E efficiency-only, DRL_S safety-only) plus an ablation without trigger (MDRL_SE_C). No rule-based, feedback or MPC VSL.
  Q[f042 p9]: "current fixed speed limit strategy for the Robin Williams Tunnel serves"
- Gain vs strongest comparator (recomputed, Table 6, p. 10): vs FSL: conflicts (17,489-21,582)/21,582 = -18.96 % weekday; (4,895-5,700)/5,700 = -14.12 % weekend; time loss (74,923.00-77,683.76)/77,683.76 = -3.55 %; (17,446.89-17,877.46)/17,877.46 = -2.41 % (c.). vs DRL_E on time loss: (74,923.00-67,903.16)/67,903.16 = +10.3 % worse weekday; (17,446.89-16,905.36)/16,905.36 = +3.2 % worse weekend (c.). vs DRL_S on conflicts: (17,489-16,430)/16,430 = +6.4 % more weekday; (4,895-4,652)/4,652 = +5.2 % more weekend (c.). vs the no-trigger variant MDRL_SE_C on time loss: 74,923.00 vs 71,001.98, worse.
  Q[f042 p10]: "MDRL_SE_T 17,489 − 0.19 4895 − 0.14 74,923.00 − 0.04 17446.89 − 0.02"
  Q[f042 p10]: "DRL_E 24,837 0.15 6289 0.10 67,903.16 − 0.13 16905.36 − 0.05"
- Evaluation protocol: training demand = 2-7 a.m. of one weekday (16 Oct 2019); test = "one weekday and one weekend" 2-7 a.m., 60 control periods; replications and seeds not stated; no dispersion (Sec. 4.3, p. 7; Sec. 5.3.2, p. 9).
  Q[f042 p7]: "(October 16, 2019), including both peak and low traffic hours, as shown"
  Q[f042 p9]: "scenario runs for 5 h, which includes 60 control periods. Additionally,"
- Flags:
  - **B1** No non-learning VSL comparator; the headline is vs a fixed limit, and vs RL variants that are the paper's own weight settings. Table 6, p. 10.
    Q[f042 p9]: "current fixed speed limit strategy for the Robin Williams Tunnel serves"
  - **E1 (uncertain)** The test weekday is not dated in the text, and the weekday demand curve in Fig. 10 (image, p. 10) looks the same as the training-day curve in Fig. 5 (image, p. 7); if so, the weekday test is on the training demand. Verify with the authors' data.
    Q[f042 p7]: "(October 16, 2019), including both peak and low traffic hours, as shown"
  - **S2/S3** Replications/seeds and dispersion not stated; "significantly" used for 2-4 % efficiency without a test.
    Q[f042 p1]: "strategy significantly improves traffic safety performance by 14–19% and traffic efficiency by 2–4% compared to"
  - **B4** The proposed method has the trigger (a rule that acts only above crash probability 0.4); the RL comparators DRL_E and DRL_S are not stated to have one. Sec. 4.4, p. 8; Table 6, p. 10.
    Q[f042 p8]: "crash probability greater than 0.4),"
  - **N1** Text says the no-trigger variant "still records a 5 % improvement in the number of traffic conflicts" while Table 6 prints +0.05 on weekend conflicts (5,999 vs 5,700 = +5.2 %, more conflicts) (c.). Sec. 5.3.2, p. 11; Table 6, p. 10.
    Q[f042 p11]: "still records a 5 % improvement in the number of traffic conflicts."
    Q[f042 p10]: "MDRL_SE_C 22,240 0.03 5999 0.05 71,001.98 − 0.09 16713.45 − 0.07"
  - **M1** Conflicts and time-loss definitions (TTC threshold, zone) are not given in this paper (searched "TTC": not found); presumably the same as the 2024 paper, but not stated. No throughput or origin-queue delay.
  - **C1** "Good balance between safety and efficiency" is a middle position between two RL settings, with each beaten on its own metric (see arithmetic).
    Q[f042 p11]: "based VSL strategy which is safety-oriented, but inferior to the DRL_E-"
  - **R1** "Data will be made available on request"; network architecture of D3QN not given in Table 4 (p. 8).
    Q[f042 p13]: "Data will be made available on request."
- Good practice (G+): simulator validated against detector data (GEH < 5, speed within 3 mph, Sec. 5.1, p. 8); crash-risk model test metrics given (accuracy 0.91, AUC 0.86, Table 5, p. 9); reports that the no-trigger variant is more efficient and that the proposed strategy is worse than DRL_E on efficiency (Sec. 5.3.2, p. 11); same hyperparameters across the three RL arms (Table 4, p. 8); limitations noted (p. 12-13).
- Screen row check: agrees (rule-gated direct D3QN, fixed limit, "no dominance"). Add: no classical comparator exists; the other arms are RL weight variants.
- Not checked / uncertain: Fig. 5 vs Fig. 10 equality is visual only (80 dpi); Fig. 11-12 not read numerically.

### #32 Kang 2024, Comput.-Aided Civ. Infrastruct. Eng. 39 — file f016
- Structure / simulator / network: single DQN agent (Keras) sets 5-min speed limits on 6 consecutive sections of a ~10 km stretch of the Seoul Outer Ring Expressway, PTV VISSIM via COM (Sec. 1-3, Fig. 1, Table 2, pp. 2-6). Mixed CAV/HDV traffic, W99 CAV parameters (Table 3, p. 6). Separate DQN per CAV market-penetration rate (MPR). State = 11 variables per section, reward = TTC-based safety term plus relative speed change (Eqs. 6-9, pp. 10-11).
- Headline claim: abstract, p. 1.
  Q[f016 p1]: "revealed that safety and traffic density are improved by 53% and 59%, respectively,"
- Strongest classical comparator; how set: none. The only comparator is the "default" scenario without VSL (Sec. 5.2, p. 12; Fig. 6, p. 13). No rule-based, feedback or MPC VSL is implemented. [B1]
- Gain, recomputed: density in Section 5 at MPR 50: 0.15 -> 0.07 = (0.15-0.07)/0.15 = 53.3 % (c., p. 12). Risk: 0.05 -> 0.02 = (0.05-0.02)/0.05 = 60 % (c.; printed 59 %, consistent with rounded inputs). The abstract assigns 53 % to "safety" and 59 % to "density", the reverse of Sec. 5.2 (see N1). No travel time, TTS, delay or throughput is reported for the headline result. Section 6 (lane block, MPR 0) is shown only as speed and risk curves (Fig. 8, p. 14).
- Evaluation protocol: 100 training episodes per scenario; "The trained model was tested by each scenario"; before/after comparison "performed 10 times" and averaged (Sec. 4.6, p. 11). Calibration of HDV desired speeds against Oct 2017 loop data with the U-value (p. 5). No dispersion, no test, no held-out demand stated.
- Flags:
  - **B1** No-control (default) is the only comparator. Sec. 5.2, p. 12.
    Q[f016 p12]: "compared to the default (0.05 → 0.02, indicating a 59%"
  - **E1** Policy is trained per MPR scenario and tested on the same scenario; no separate demand or seed set is described. p. 11.
    Q[f016 p11]: "tested by each scenario. When confirming the model per-"
  - **N1** Abstract and Sec. 5.2 swap the two metrics (53 % belongs to density, 59 % to risk in Sec. 5.2); 0.05->0.02 is 60 % rather than 59 % (rounding of printed inputs). Abstract p. 1 vs p. 12.
    Q[f016 p12]: "with a significant reduction in MPR 50 (0.15 → 0.07, indi-"
  - **M1/M2** Headline metrics are section-5 density and a TTC-based risk index, both proxies; the reward is speed-change plus TTC. Fig. 6 reports "Section 5" only. p. 13.
    Q[f016 p13]: "Density (upper) and risk (lower) results of Section 5 by market penetration rate (MPR) scenarios."
  - **S2/S3** 10 evaluation runs are stated, but only means are shown and no dispersion or test is reported; "significant" is used without a test. pp. 11, 15.
    Q[f016 p15]: "sity results significantly in the MPR 25 and 50 scenarios,"
  - **C1** "Significant reduction in delay" is claimed for the lane-block case, but Fig. 8 shows speed and risk (caption p. 14), and delay is not quantified.
    Q[f016 p14]: "one, two, and three VSLs showed a significant reduction"
  - **R1** Table 4 gives epsilon 0.999, while Sec. 5.1 says annealed from 1 to 0.01; no code or data statement found in text (searched whole file for "code", "github", "data availab", "seed").
    Q[f016 p8]: "0.999 (probability of taking a"
  - **P2** Network is calibrated to loop data (U <= 0.1 at MPR 0 only); capacity drop and teleports/collisions are not reported.
- Good practice (G+): VISSIM network calibrated with U-value on field loop data (p. 5); 10 evaluation replications; reports honestly that VSL gives no benefit at MPR 75/100.
  Q[f016 p12]: "no significant improvement was noted with the application"
- Screen row check: agrees on simulator, comparator (NC only) and "density -53 %". Imprecise: 53 % is Section-5 density at MPR 50 only; risk -59 % is not mentioned; the gain vanishes at MPR >= 75; the abstract's metric labels are swapped.
- Not checked / uncertain: Fig. 6 bar values (image); the number of training runs per MPR (not stated).

### #33 Li & Lasenby 2024, IEEE T-ITS 25(2) — file f025
- Structure / simulator / network: single-agent I2A (A2C + CNN environment model + LSTM rollout encoders), 11 discrete limits 20-70 mph, 60 s control interval; SUMO model of a 2.8 km M25 J12 merge, calibrated on 10 June 2019 and validated on 17 June 2019 with GEH (Secs. III-V, pp. 3-6; Table I, p. 6).
- Headline claim: abstract, p. 1.
  Q[f025 p1]: "the proposed I2A agent outperforms other"
- Strongest comparator; how set: DQL and A2C (both RL, same state/actions). No rule-based, feedback or MPC controller is run, although the introduction discusses them (pp. 1-2). Comparator tuning not stated in the main text; "Appendix D" holds agent settings but is not in the PDF (not found in text). [B1, B2]
  Q[f025 p3]: "in Appendix D."
- Gain, recomputed: vs no-control (538 veh.h): I2A 11.9 %, DQL 9.7 %, A2C 8.9 % (p. 7). I2A TTS printed as 473 veh.h (p. 8): (538-473)/538 = 12.1 % (c.), vs printed 11.9 % (538 x 0.881 = 474; rounding). DQL TTS = 538 x (1-0.097) = 485.8 (c.); (485.8-473)/485.8 = 2.6 % (c.). vs A2C: 490.1 -> 3.5 % (c.). Bottleneck volume: +9.0 % vs +7.9 % (DQL), i.e. 1.1 pp apart (p. 7).
- Evaluation protocol: training 300 episodes, demand scaled 85-115 % of a profile drawn from 10 June weekdays; results are "means of 10 simulation runs" (p. 6-7). Which demand the test runs use (a held-out day, or the calibration day 10 June 2019) is not stated. No dispersion. Compliance sensitivity gives single numbers (473/482/506 veh.h, p. 8).
- Flags:
  - **B1** Strongest comparator is another RL agent; the RL-vs-RL gap is ~2.6 % TTS.
    Q[f025 p7]: "recorded 9.7% and 8.9% improvements in TTS respectively,"
  - **S1/S3** Means of 10 runs with no spread; a 2-3 % difference between RL variants cannot be separated from noise. Training-seed count not stated (S2).
    Q[f025 p7]: "are the means of 10 simulation"
  - **E1** Test demand not distinguished from training demand (possible train = test on the calibration day).
    Q[f025 p6]: "were randomly sampled between 85% and 115% of a demand"
  - **C1** "Outperforms" is based on a 2-4 % TTS difference without a test; the conclusion also says "only trained and evaluated based on a merge bottleneck".
    Q[f025 p8]: "The proposed agent was only trained and evaluated based"
  - **R1** Appendices A-D and the supplementary material are not in the PDF; reward parameters (lambda_p = 5) are given but demand profile, TTS_c and rollout settings are not in the main text.
  - **N1 (minor)** 473 vs 11.9 % (12.1 % derived); Fig. 7 y-axis runs 0-5 "veh x h" while the text TTS is 538 veh.h (units/scale not explained; image p. 7).
- Good practice (G+): TTS includes vehicles waiting to enter (p. 3); capacity drop exhibited in the no-control run and bottleneck volume reported next to TTS (p. 7); calibration + validation on separate days (p. 6); compliance sensitivity (p. 8).
  Q[f025 p3]: "takes into account vehicles waiting to enter the network"
  Q[f025 p7]: "The capacity drop occurred shortly"
- Screen row check: agrees (-2.5 % TTS vs the best RL agent is about 2.4-2.6 % (c.); -11.9 % vs NC confirmed; capacity drop exhibited confirmed). Add: no non-learning controller anywhere; I2A advantage rests on 10-run means without dispersion.
- Not checked / uncertain: Fig. 7 curve values (image); appendices (absent).

### #34 Han et al. 2024, TRR 2678(9) — file f031

- **Structure / simulator / network:**
  - Direct DRL: MADDPG with one agent per lane (3 agents).
  - Simulator: SUMO.
  - Network: 5 km three-lane section of G15 southbound, Shenzhen. Two on-ramps (O1, O2), one off-ramp (D1); merge bottleneck at O2 (p. 3, p. 7).
  - Mixed traffic: HDV + CAV, with CAV penetration rate (PR) of 30 % in the headline result.
- **Headline claim:**
  - MARL-DVSLC TTS = 448.14 (stable demand) and 428.05 (fluctuating demand).
  - "Improved by" 21.34 % / 16.75 % vs feedback (FB) and 12.88 % / 10.24 % vs DDPG-DVSLC (p. 12; abstract p. 1 for the DDPG numbers).
  Q[f031 p12]: "scenario, the TTS of MARL-DVSLC is 448.14 vehicles"
  Q[f031 p12]: "trol performance is improved by 21.34% and 12.88%,"
  Q[f031 p12]: "trol performance is 16.75% and 10.24% higher than that"
- **Strongest classical comparator:** Carlson et al. FB VSL, with one limit for all lanes in [60, 120] km/h.
  - The gains are stated, but no tuning procedure is described. The only justification given is "control efficiency and stability" (p. 8).
  Q[f031 p8]: "control efficiency and stability comprehensively,"
  Q[f031 p8]: "VSLC are 0.0004, 10, and 38, respectively."
  Q[f031 p8]: "the speed limits is [60,120] km/h. Considering the"
- **Gain vs strongest comparator:** see the claim audit. The true relative reductions vs FB are 26.39 % (stable) and 18.99 % (fluctuating) (c.).
- **Evaluation protocol:**
  - Training and test both use the same two demand profiles (Fig. 5). Demand is Poisson with a random departure lane (p. 7).
  - The number of test runs or seeds, and whether test seeds differ from training seeds, are not stated anywhere (whole file searched: no "seed" or "replication").
  - One TTS bar per method; no dispersion (Fig. 12, p. 12).
  Q[f031 p7]: "the traffic volume of each period follows a Poisson dis-"
- **Flags:**
  - **N1** The "% vs FB/DDPG" numbers are percentage-point differences of NC-relative reductions, not reductions relative to the comparator. The arithmetic is in the audit.
    - In Fig. 12 the legend appears swapped: the text assigns 448.14 to the stable demand, but in the figure 448.14 is the bar the legend labels "fluctuating" (QI, p. 12). Fig. 13 at PR = 30 % agrees with the text.
    - Table 1 lists "Experience replay memory size 0.001", which is not a valid buffer size.
    - TTS is reported in "vph".
    Q[f031 p9]: "Experience replay memory size 0.001"
  - **B2** FB gains are given without units, setpoints, sampling period or tuning method (p. 8; quotes above).
  - **B4** The comparison is asymmetric:
    - RL sets per-lane limits, with lane-specific ranges (lane 1 in [90, 120], p. 7).
    - FB posts one limit on all lanes.
    - The authors themselves attribute part of the gain to this (p. 11).
    - RL also observes per-segment inflow, density, speed, waiting vehicles and outflow, plus the O2 ramp state (p. 4).
    Q[f031 p1]: "thereby setting different speed limits for each lane. The reward function takes into account the total time spent (TTS) on"
    Q[f031 p11]: "adopts a uniform VSLC. This practice leads directly to a"
  - **E1** Trained and evaluated on the same two demand profiles. There is no held-out demand or seed set (p. 7, Fig. 5).
  - **E2-risk** RL parameters were "carefully determined … based on the multiple rounds of testing and parameter tuning" (p. 8). The data used is not stated.
    Q[f031 p8]: "meters of MARL-DVSLC are carefully determined in"
  - **S1 / S2 / S3** The number of evaluation runs is not stated; no std/CI; no test.
  - **M1** Per-lane TTS (Eq. 1). Whether vehicles not yet inserted (insertion backlog at the origins and O2) are counted is not stated. No served throughput is reported.
  - **P2** A capacity drop of 7.8 % is asserted from "calibration results", but no calibration data or method is shown. Teleports and collisions are not reported.
    Q[f031 p7]: "the capacity drop is 7.8%. It should be noted that"
  - **R1** Code is "available … on reasonable request" (p. 14). Model parameters are "taken from the aforementioned literature" without values (p. 7). HDV compliance follows a normal distribution, with parameters not given (p. 3).
    Q[f031 p14]: "Some or all data, models, or code that support the findings of"
  - **C1** "always outperforms" and "significantly" are claimed with no replications or tests (p. 2, p. 13).
    Q[f031 p2]: "various situations, and always outperforms the"
- **Good practice (G+):**
  - A classical FB comparator *and* a DRL comparator (DDPG-DVSLC) are included, using the same state, action and reward.
  - Two demand profiles.
  - A PR sensitivity sweep over 0–100 % (Fig. 13).
  - Simulation in SUMO with stochastic arrivals.
  - The FB gains are printed, which many papers omit.
- **Screen row check:**
  - **Disagrees in one point.** "−21.34 % / −16.75 % vs FB" is not a reduction relative to FB. It is the gap in NC-relative reductions, in percentage points.
    - Relative to FB, the RL reduction is 26.4 % / 19.0 % (c.).
    - Relative to DDPG, it is 17.8 % / 12.5 % (c.).
    - The direction of the error makes the paper's numbers *smaller* than the true relative gains.
  - The rest agrees: no tuning, one limit vs per-lane, no CI.
- **Not checked / uncertain:**
  - Fig. 12 values were read from an image (QI).
  - Fig. 5 demand values are approximate.
  - Reward-curve values in the text file read "around 29 / 21", but the rendered page shows "−9 / −1" (minus signs lost in extraction).

#### Claim audit, #34

**Printed TTS values (Fig. 12, QI p. 12; veh·h), with the stable/fluctuating assignment taken from the text:**

| Method | Stable | Fluctuating |
|---|---|---|
| NC | 752.8 | 598.92 |
| FB | 608.79 | 528.37 |
| DDPG | 545.1 | 489.38 |
| MARL | 448.14 | 428.05 |

| Claim | Relative to comparator (c.) | NC-relative difference in pp (c.) | Printed |
|---|---|---|---|
| vs NC, stable | (752.8−448.14)/752.8 = 40.47 % | — | 40.47 % ✓ |
| vs NC, fluct. | (598.92−428.05)/598.92 = 28.53 % | — | 28.53 % ✓ |
| vs FB, stable | (608.79−448.14)/608.79 = **26.39 %** | (608.79−448.14)/752.8 = 40.47 − 19.13 = **21.34 pp** | 21.34 % |
| vs FB, fluct. | (528.37−428.05)/528.37 = **18.99 %** | (528.37−428.05)/598.92 = **16.75 pp** | 16.75 % |
| vs DDPG, stable | (545.1−448.14)/545.1 = **17.79 %** | 96.96/752.8 = **12.88 pp** | 12.88 % |
| vs DDPG, fluct. | (489.38−428.05)/489.38 = **12.53 %** | 61.33/598.92 = **10.24 pp** | 10.24 % |

- All four comparator numbers are reproduced exactly as differences in NC-normalised reduction (pp), not as reductions relative to the comparator.
- FB itself gives only 19.13 % (stable) and 11.78 % (fluctuating) vs NC (c.).

**FB configuration.**
- "secondary controller parameter K_I" = 0.0004, "K′_I" = 10, "K′_P" = 38 (p. 8), described as Carlson et al. (ref. 6, IEEE T-ITS, "Local feedback-based mainstream traffic flow control…").
- One common limit on all three lanes, range [60, 120] km/h.
- Not given:
  - units;
  - the density or occupancy setpoint;
  - the flow setpoint;
  - the control period (the RL period is 60 s; whether FB uses the same is not stated);
  - the rounding and rate limits;
  - whether FB limits are sent to CAVs by I2V like the RL limits. The text only says that the TCC strategy "is replaced by the corresponding method in turn".
- No tuning procedure is described.
- The RL agents have lane-specific ranges and per-lane limits, and in practice lane 1 is held at 120 km/h (p. 9). That is an actuator FB does not have (B4).

**Bottom line.** Against the stated FB, the gain is 26 % / 19 % (c.). But FB is untuned and less actuated (B2 + B4), the gain comes from an unknown number of runs with no dispersion (S2/S3), and evaluation is on the training demands (E1).

#### Reproduction spec, #34 (SUMO 1.27 / libsumo)

- **Simulator used:** SUMO; version and step length not stated. Porting is native, but the SUMO version differs.
- **Network:**
  - 5 km, 3 mainline lanes, G15 southbound.
  - O1 on-ramp, D1 off-ramp, O2 on-ramp (bottleneck). The bottleneck forms about 3 km downstream of the mainline start (p. 9).
  - VSL area 1 km, acceleration area 200 m upstream of O2 (p. 7).
  - **MISSING:** positions of O1 and D1; ramp lengths and lanes; acceleration-lane length at O2; segment count j for detectors; detector types. Fig. 4 is only a map sketch.
- **Demand (Fig. 5, approximate, 2 h):**
  - Stable: R1 (main→main) ≈ 3800 → ≈ 5500 veh/h, plateau about 0.6–1.15 h.
  - R2 (O1), R3 (→D1) and R4 (O2) range from ≈ 200 to ≈ 1300 veh/h, with R4 the highest.
  - The fluctuating profile is similar but noisy.
  - Poisson arrivals; uniform random departure lane (p. 7).
- **Vehicles:**
  - HDV: IDM + LC2013.
  - CAV: ACC and CACC (Milanés models; both exist in SUMO).
  - PR ∈ {0, 30, 60, 100} % (p. 7; Fig. 13 axis).
  - **MISSING:** all model parameter values ("taken from the aforementioned literature"); the mean and std of the HDV compliance distribution; the CAV "speed limit command" implementation.
  - Assumed: 200 m I2V range, perfect communication.
- **Capacity drop:** 7.8 % claimed, not shown.
- **RL:**
  - MADDPG with 3 agents; centralised critics; dense layers of 128 units with batch normalisation; sigmoid actor output (p. 5–6).
  - Discrete limits: {90, 100, 110, 120}, {80, 90, 100}, {60, 70, 80, 90, 100} km/h. The mapping from the sigmoid output to an index is not specified.
  - Per-lane state: (inflow, density, speed, waiting count, outflow) per segment. Lane 3 is averaged with the O2 ramp.
  - Reward: r = q_out − q_in per lane (Eq. 2).
  - γ = 0.99, batch 1024, lr = 0.001, τ = 0.0001, Adam. The replay size is printed as "0.001", which is invalid.
  - 1000 episodes × (2 h / 60 s = 120 steps) = 120,000 steps (c.). The reward plateaus at about 310 episodes.
  - **MISSING:** number of hidden layers (Fig. 2 only), exploration noise, warm-up, training PR and demand, wall time.
- **Baselines:**
  - FB as described above, with missing setpoints and period.
  - DDPG-DVSLC: Wu et al. (ref. 12) with the same MDP.
- **Evaluation:** number of runs and seeds not stated.
- **Code/data:** "available from the corresponding author on reasonable request" (p. 14). No URL.
- **Top guesses needed:**
  1. Ramp geometry and positions.
  2. Exact demand numbers.
  3. HDV compliance and CAV parameters.
  4. FB setpoints and period.
  5. Training versus evaluation seeds.


### #35 Hua & Fan 2024, Physica A 634 — file f038
- Structure / simulator / network: single DDPG agent sets per-lane speed limits (6 levels, 50-75 mph) on I-80 (1.4 mi, weaving area), SUMO via TraCI; mixed Krauss HDV / IDM CAV; incident = a vehicle stopped 5-10 min (Secs. 3.1-4, pp. 4-7). State = lane occupancies (10 dims). Reward = minus cumulative emergency deceleration (Sec. 3.1, p. 4).
- Headline claim: abstract (qualitative); numbers in Sec. 5.1, p. 7.
  Q[f038 p7]: "slightly compromising sustainability"
- Strongest comparator; how set: no control only (p. 7-8; Table 1). The introduction argues RL beats classical controllers (p. 2) but none is implemented. [B1]
  Q[f038 p2]: "achieve comparable performance with less prior knowledge"
- Gain, recomputed (Table 1, p. 8): rows are "improvement by percentage" against NC at 10 % MPR (ATT 90.68). No-event: NC 50 % = 90.68 x (1-0.0543) = 85.76; DSH 50 % = 90.68 x (1-0.0962) = 81.96; gain = 4.4 % (c.). At 90 %: NC 81.77, DSH 77.41 -> 5.3 % (c.). At 10 %: 8.2 % (c.). Special event: 8.7 %, 7.0 %, 2.4 % (c.). The text's "ATT can be reduced by 14.63 % under 90 % MPR" is relative to NC at 10 % MPR, not NC at 90 %. Collision probability: 15.0 % -> 9.2 % at 90 % MPR (Table 1).
- Evaluation protocol: 300 training episodes (p. 5); agent trained in "no event" and "special event" settings; "holistic evaluation is done with 20 episodes for each MPR" averaged (p. 7). Demand "randomly generated for each round" (p. 6). No dispersion; no train/test split of seeds stated.
- Flags:
  - **B1** No classical comparator.
  - **C1** The 14.63 % ATT figure compares DSH at 90 % MPR with NC at 10 % MPR; the DSH-attributable gain at equal MPR is 4.4-5.3 % (c.). p. 7-8.
    Q[f038 p7]: "DSH has minimal impact at equivalent MPR levels"
  - **E1/S2/S3** 20 evaluation episodes, mean only, same network and demand generator as training; no dispersion or significance test.
    Q[f038 p7]: "The holistic evaluation is done with 20 episodes for each Market Penetration Rate"
  - **M1/M2** Objective and lead metric are surrogate safety (collision probability from TTC < 3 s, DRAC); ATT scope (insertion/queued vehicles) and throughput are not reported.
  - **N1 (minor)** Text says compliance 0.7 "indicating 30% compliance"; the text on time cost (260 s -> 269 s) is not reconciled with an ATT gain (probably wall-clock, unclear).
    Q[f038 p7]: "The time cost for pre- and post- control only increases from 260 s to 269 s"
  - **R1** "The data that has been used is confidential"; DDPG hyperparameters "fine-tuned after many trials" with no procedure or data split.
    Q[f038 p11]: "The data that has been used is confidential"
- Good practice (G+): reports the sustainability trade-off (emissions/fuel worse with DSH, Table 1; p. 7); sensitivity to SSM thresholds and weather (Tables/Fig. 6, pp. 9-10); demand drawn from PeMS.
- Screen row check: agrees on the -2.4...-8.7 % ATT range (reproduced as 2.4-8.7 % (c.) under the reading that percentages are relative to each block's NC-10 % row); NC only confirmed. Imprecise: row omits that the policy's reward is a safety proxy and that the text's 14.63 % is against NC at 10 % MPR.
- Not checked / uncertain: the baseline of the special-event block percentages (assumed to be that block's NC 10 % row, p. 7); Table 1 mixes absolute (NC 10 %) and % values; Fig. 3-6 images.

### #36 Ko 2020, IET Intell. Transp. Syst. 14(8) — file f039
- Structure / simulator / network: two homogeneous-team DQNs shared by all CAVs: merge control (MC, 1 s, picks which CAV crosses first) and speed harmonisation (SH, 10 s, per-CAV target-speed increments). SUMO, 3 km two-lane road with a lane closure; mixed CAV/CHV/NHV (Secs. 4-5, pp. 3-7; Fig. 5; Table 1).
- Headline claim: abstract, p. 1.
  Q[f039 p1]: "increasing the throughput up to 30% and reducing the fuel consumption up to 20%, when compared to the late"
- Strongest comparator; how set: base case (BC), late merge (LM), FIFO, MC alone, and MC + simple speed harmonisation (SSH, "proposed in [36]"). No parameters given for SSH, FIFO or LM (pp. 7). [B2]
  Q[f039 p7]: "Additionally, the SSH proposed in [36] is exploited"
- Gain, recomputed from Table 2 (p. 11), proposed MC+SH ("MC + SC" in the PDF text):
  - Throughput vs FIFO: from 1722 vs 1874 (2000 veh/h, 20 % CAV) = -8.1 % up to +19.2 % (3000 veh/h, 80 % CAV); min -10.9 % (3500, 20 %) (c.). FIFO wins at 20 and 35 % CAV in every input rate.
  - vs MC alone: -4.8 % ... +1.7 % (c.). vs MC+SSH: -3.2 % ... +2.0 % (c.). MC+SH has the best throughput in no CAV-share column except at 50 % CAV (+0.0...+1.3 % vs the best of FIFO/MC/MC+SSH, within the printed std).
  - vs LM: IR max for MC+SH = 27.2 % (3000 veh/h, 65 % CAV); abstract says "up to 30 %". MC alone reaches 32.1 % and FIFO 33.8 %.
  - Fuel (Table 3, p. 12): MC+SH vs MC+SSH 0.31 vs 0.35 l at 3500 veh/h, 80 % CAV = -11.4 % (c.; 2-decimal rounding); about equal at 20 % CAV.
- Evaluation protocol: train at 50 % CAV and 3500 veh/h for 550 episodes, "selected one of the trained Q-networks"; test over arrival 2000-4000 and CAV 20-80 %, "simulated 20 times for each scenario"; mean and std printed (Tables 2-3, pp. 11-12; p. 7).
- Flags:
  - **N1** Abstract "up to 30 %" throughput is not reached by the proposed MC+SH (max 27.2 %, Table 2). p. 1 vs p. 11.
    Q[f039 p11]: "MC + SC 1721 13.6 19.5 1741 14.0 20.2 1784 49.0 22.1 1869 26.5 27.2 1877 48.4 27.1"
  - **C1** Gains over the strongest comparators are small or negative on throughput; the paper says so.
    Q[f039 p9]: "does not have the highest throughput in the overall evaluation"
  - **B2** SSH, FIFO and LM have no stated parameters or tuning. p. 7.
  - **E2** Checkpoint "one of the trained Q-networks" chosen without a criterion; the architecture (5 hidden layers) is chosen by test-type throughput/fuel.
    Q[f039 p7]: "test using five hidden layers has the best result in terms of vehicle"
  - **S1** One training run (one network); training seeds not stated. p. 7.
    Q[f039 p7]: "We selected one of the trained Q-networks and evaluated the"
  - **E1** The training condition (50 % CAV, 3500 veh/h) is one cell of the test grid; other cells are out-of-distribution (also G+).
  - **M1** No travel-time/delay metric; throughput at the bottleneck and per-vehicle fuel only.
  - **R1** No code or data statement found in text (searched the whole file).
- Good practice (G+): std from 20 test runs per cell (Tables 2-3); generalisation grid over 5 arrival rates x 5 CAV shares; includes FIFO, LM and a rule-based SH comparator; reports the throughput/fuel trade-off and where the proposed method loses.
- Screen row check: agrees (-10.9 ... +19.2 % vs FIFO reproduced exactly (c.); "1 training run" agrees). Add: the headline in the abstract is against LM, and vs the authors' own MC the SH adds fuel savings but not throughput. The control is CAV target speed, not roadside VSL.
- Not checked / uncertain: Figs. 6-16 (images); "MC + SC" in the extracted tables is read as MC + SH (the PDF text layer prints SC).

### #37 Yang 2024, Sustainability 16:965 — file f043
- Structure / simulator / network: rule-gated direct DDPG (action noise decayed x 0.89) outputs continuous speed-limit values for cells upstream of an emergency point; self-triggered only while an emergency flag is set (Secs. 3-4, pp. 6-11). SUMO 1.19.0, Hong Kong-Zhuhai-Macao bridge section from OSM, three flow levels; reward r = f_out - f_in (Eq. 4, p. 8).
- Headline claim: abstract, p. 1.
  Q[f043 p1]: "the proposed strategy has improved by over 28.30% compared to other methods."
- Strongest classical comparator; how set: an unspecified "rule-based" VSL; no thresholds, source or tuning given anywhere (p. 11, Tables 3-5). [B2, R1]
  Q[f043 p11]: "no control (baseline) and traditional rule-based (rule-based) methods for VSL in different road environments"
- Gain, recomputed from Tables 3-5 (pp. 15-16), ATT: low flow NC 81.27, rule 87.89, DDPG 92.57, IDDPG 82.88 -> I-DDPG is +1.98 % worse than no control; vs rule (87.89-82.88)/87.89 = 5.7 % (c.). Medium: NC 91.22, rule 88.65, DDPG 87.66, IDDPG 84.64 -> 7.21 % vs NC (printed), 4.5 % vs rule, 3.5 % vs DDPG (c.). High: NC 92.7, rule 88.69, DDPG 87.56, IDDPG 85.39 -> 7.89 % vs NC, 3.7 % vs rule, 2.5 % vs DDPG (c.). PCN (potential collisions): low 76 vs NC 106, rule 92, DDPG 79 -> vs DDPG 3.8 % (c.); medium 82 vs DDPG 88 = 6.8 % (c.); high 83 vs 90 = 7.8 % (c.).
- Evaluation protocol: 600 max training episodes (Table 2); evaluated per flow level, single value per method per table; number of replications, seeds and any held-out demand: not found in text (searched for "seed", "repeat", "replicat", "averag"). Demand profiles in Figs. 9-11 are "randomly selected".
- Flags:
  - **N1/C1** The abstract's "over 28.30 %" safety and "over 7.21 %" efficiency are the I-DDPG gains vs no control (low-flow PCN, medium-flow ATT), not "compared to other methods"; against the other controllers they are 3.8-17.4 % (PCN) and 2.5-10.5 % (ATT; 10.5 % is low flow vs DDPG, which is itself 13.9 % worse than NC) (c.). pp. 1, 15-16.
    Q[f043 p1]: "our strategy has improved over 7.21% compared to the others"
  - **B1/C1** At low flow no-control beats every controller on ATT.
    Q[f043 p15]: "although no control is better than the other three control strategies in terms of efficiency at low traffic levels"
  - **B2** The rule-based baseline is undefined; DDPG and I-DDPG share the same task and training setup.
  - **S2/S3** No replications, dispersion or test; differences of 2-4 % in ATT are reported as ranking.
  - **E1** No held-out demand or seeds described.
  - **M1/M2** PCN counts a conflict when TTC is *greater* than 3 s as defined; ATT scope and throughput not reported; reward is a flow-difference proxy; "safety factors can be ignored" is stated in the reward section.
    Q[f043 p14]: "If the value of TTC is greater than 3 s, the number of potential collisions will be increased by 1."
  - **P2** Capacity drop is imposed by stopping an emergency vehicle for 3 min; no calibration of demand/network to data, no teleport or collision reporting.
  - **N1 (minor)** Memory pool: text says 512, Table 2 says 215.
    Q[f043 p14]: "This is because the memory bank parameter is set"
  - **R1** "Data are contained within the article"; no code.
    Q[f043 p17]: "Data are contained within the article."
- Good practice (G+): the percentages printed in Tables 3-5 are arithmetically consistent with the printed absolute values (e.g. 8.15 %, 13.90 %, 1.98 %, 7.21 %, all checked); the low-flow loss versus no control is reported rather than hidden; three flow levels.
- Screen row check: agrees on range and "rule VSL [not stated]" (-2.5 ... -5.7 % ATT reproduced vs the nearest controller). Imprecise: the -5.7 % low-flow figure is against a rule controller that is itself worse than no control; versus NC the proposed method loses 2.0 % at low flow.
- Not checked / uncertain: Fig. 13 entropy-weighted index; Figs. 9-12 (images).

### #38 Yan (W.) 2025, LNEE 1379 (ICAUS 2024) — file f032
- Structure / simulator / network: three MAPPO agents set speeds of two CAVs forming a moving bottleneck and the start/end of the controlled zone (a1..a4), limits 30-80 km/h; SUMO, M25 merge, 1 h (17:00-18:00) from UK data, 7.5 km control area, 500 m bottleneck (Secs. 3-4, pp. 3-7).
- Headline claim: abstract, p. 1 and conclusion, p. 10.
  Q[f032 p1]: "the proposed strategy improves traffic efficiency by 40%."
- Strongest comparator; how set: DDPG-MVSL (another RL agent) and no VSL; hyperparameters of DDPG-MVSL not given (p. 6, 8). No classical VSL. [B1, B2]
  Q[f032 p6]: "A comparative analysis will be performed between MAPPO-MVSL, DDPG-MVSL, and without variable speed control."
- Gain, recomputed: Fig. 6 (right) bars, read approx. from the image: NoVSL ~3.3, DDPG ~11.5, MAPPO ~18 m/s. (18-11.5)/11.5 = 57 %; (18-3.3)/(11.5-3.3) = 1.8x improvement ratio (c., image, approx.). Neither gives "40 %"; (18-11.5)/18 = 36 %. Safety (Fig. 8 bars): TTC ~0.43 / ~1.24 / ~1.46 s; (1.46-1.24)/1.24 = 18 % (c., approx.), text says "approximately 16 %".
- Evaluation protocol: 300 Poisson scenarios generated, 250 for training (p. 8); both RL agents trained 250 episodes; evaluation shown as one time series per method (Fig. 6 left); number of test scenarios behind the bars not stated.
- Flags:
  - **N1** "40 %" is not derivable from the figure and is described three ways: "improves traffic efficiency by 40 %" (abstract), "improvement ... 40 % higher than that of the DDPG-MVSL" (p. 9), "by 40 % compared to DDPG-MVSL" (p. 10).
    Q[f032 p9]: "the improvement achieved by MAPPO-MVSL is approximately 40% higher than that of the DDPG-MVSL."
  - **C1** Abstract calls the comparator "the traditional single-agent variable speed control strategy"; in the text it is DDPG-MVSL, an RL method. p. 1 vs p. 6.
    Q[f032 p1]: "Compared with the baseline and the traditional single-agent variable speed control strategy,"
  - **M2** "Efficiency" is the average speed in the 500 m bottleneck area; "safety" is a mean TTC over only those vehicles below an unstated TTC threshold (Eq. 6), reported as "danger reduced by 16 %" in the abstract and "16 % increase in average collision time" in the text. No delay, TTS or throughput.
    Q[f032 p9]: "ensuring an approximately 16% increase in the average collision time per vehicle."
  - **S1/S2/S3** Single curves and bars; no replications, no dispersion, no test. Training reward is flat and noisy (Fig. 5, image p. 8; text: reward "fluctuated around 42.5").
    Q[f032 p8]: "Reward fluctuated around 42.5 throughout the training process."
  - **E2/R1** "Hyperparameters were fine-tuned" with no procedure; GAE lambda is 0.99 in text and 0.95 in Table 2 (N1).
    Q[f032 p8]: "supported by a GAE Lambda value of 0.99 to reduce bias."
  - **P2** Flow-density scatter (Fig. 4) is shown, but network/demand calibration and teleports are not reported; NC speed collapses to ~3 m/s for most of the hour (Fig. 6, image).
  - **B4** MAPPO controls two CAV speeds and the zone start/end via four actions; the DDPG-MVSL action set and information are not described, so equal footing cannot be checked.
- Good practice (G+): train/test scenario split is implied (250 of 300 scenarios); heat maps and flow-density diagram shown; the limitation of continuing oscillations is stated (p. 9).
- Screen row check: agrees ("other RL", "ambiguous 40 %"). Add: no value derivable from the figure bars, the metric is bottleneck-zone speed, and "full" depends on a single scenario curve.
- Not checked / uncertain: bar and curve values are visual estimates from rendered Figs. 6 and 8 (pp. 9-10); CAV penetration rate (Fig. 3, image) not extracted.

### #39 Vatani Nezafat 2019, PhD dissertation, Old Dominion Univ. — file f017

- **Structure / simulator / network:**
  - Direct DRL: A3C with 16 workers.
  - Simulator: a custom Python micro-simulator (p. 25, p. 46). Car following is the Goñi-Ros sag-curve IDM; lane changing is LMRS.
  - Three isolated bottlenecks:
    - sag curve, 1 lane;
    - lane drop, 3→2;
    - on-ramp, 2 lanes plus ramp.
  - Lagrangian VSL: only connected vehicles (CVs) in a 1 km control section obey, with full compliance (p. 38).
- **Headline claim:**
  - Total delay reduced vs NC by 63 % (sag), 64 % (lane drop) and 19 % (on-ramp) at 100 % CV penetration (MPR), and "RL outperforms feedback controller in all bottlenecks" (p. 52–54, p. 73).
  Q[f017 p52]: "The VSL reduced the total delay by 63% compared to the no control scenario."
  Q[f017 p53]: "The VSL reduced the total delay by 64% compared to the no control scenario."
  Q[f017 p73]: "but the results show that the RL outperforms feedback controller in all bottlenecks."
- **Strongest classical comparator:** an ALINEA-inspired P-control VSL, v(t) = v_target + k(ρ_target − ρ_b(t−1)) (Eq. 33, p. 37), tuned by grid search (p. 49).
  Q[f017 p49]: "Optimal parameters of this controller were found through a grid search."
- **Gain vs strongest comparator:** remaining-delay reduction (c.), see the audit. 21 % (sag), 54 % (lane drop), 7 % (on-ramp) on the training demand; 22 %, 29 % and 6 % on the new demand.
- **Evaluation protocol:**
  - Headline RL and FB numbers are single runs at 100 % MPR on the training demand (one trapezoidal 20-min peak).
  - A "new demand pattern" (short peak followed by a longer peak) is a held-out demand for both controllers, but again with one run each (p. 55–60).
  - The MPR sensitivity uses 50 runs per MPR with medians and boxplots (p. 61–71).
  Q[f017 p56]: "It should be noted all three algorithms were trained only on short demand with one peak."
  Q[f017 p61]: "Each market penetration level is simulated 50 times"
- **Flags:**
  - **B3**
    - The FB grid search is described in one sentence. Grid ranges, tuned parameters (v_target, k, ρ_target, T_c), objective and scenario are not stated.
    - From the context ("optimal solutions" shown per bottleneck at 100 % MPR on the same demand, p. 49–51), the FB was tuned on the same scenario on which it is compared.
    - RL is likewise trained on that scenario, so both arms are "tuned on test". This is symmetric, but in-sample.
  - **R1** FB parameter values found by the grid search are not reported anywhere (whole file searched).
  - **S1** Headline comparisons (63/64/19 % vs 53/21/13 %) are single runs.
    - The dissertation's own 50-run medians at 100 % MPR (Fig. 33, p. 62, QI) read ≈ 63 % (sag), ≈ 55 % (lane drop) and ≈ 20 % (on-ramp).
    - So the lane-drop headline of 64 % lies above its own 50-run median.
    - No FB replications exist at all.
  - **S3** No dispersion or test for any RL-vs-FB comparison. Boxplots exist only for RL across MPR.
  - **E2-risk**
    - Training ran to ≈ 14,500 episodes and collapsed to about −100 % between 12,000 and 14,000 episodes (Fig. 23, p. 52; text p. 51).
    - Which checkpoint is evaluated is not stated.
    Q[f017 p51]: "the divergence from the optimal solution can be seen between 12000 and 14000 episodes."
  - **N1 (labels)** Several result sentences name the wrong bottleneck. I paired numbers to bottlenecks by figure number.
    - p. 50 (lane-drop FB): "delay caused by on-ramp".
    - p. 58 (lane-drop FB, new demand): "caused by the sag curve".
    - p. 60 (on-ramp RL, new demand): "caused by the lane reduction".
    Q[f017 p50]: "The feedback controller was able to eliminate 21% of the delay caused by on-ramp when market"
    Q[f017 p58]: "only eliminate 10% of the delay caused by the sag curve."
    Q[f017 p60]: "The RL was able to eliminate 11% of delay caused by the lane reduction."
  - **B4 (mild)**
    - RL sees bottleneck *and* entrance density, stacked over 10 steps; FB sees only the bottleneck density.
    - RL is rate-limited (±5/10 km/h per minute). FB has no stated rate limit and reaches 20 km/h (p. 50). That cuts against RL.
  - **P2 (partial)**
    - The capacity drop is visible in the NC exit-flow plots: lane drop ≈ 4000 → ≈ 2800 veh/h (Fig. 15, p. 43, QI).
    - The networks and parameters are hypothetical and uncalibrated ("hypothetical model parameters", p. 42). There are no collisions or insertion statistics.
  - **M1 (minor)**
    - Delay = TTT − TTT without the bottleneck, over all vehicles until the network empties (Eq. 35, p. 48). This is full-scope.
    - Insertion blocking is ruled out explicitly only for the sag network (p. 38).
  - **C1** "outperforms … in all bottlenecks" rests on single runs; the on-ramp margin is 19 % vs 13 % of delay eliminated.
- **Good practice (G+):**
  - Comparator tuned by grid search: rare in this literature, even if undocumented.
  - A held-out demand pattern on which both controllers are evaluated.
  - 50-run Monte Carlo with medians and boxplots for MPR sensitivity.
  - Negative performance at low MPR reported openly (p. 62–65).
  - Full-population delay metric.
  - Model parameters tabulated (Tables 1–2).
- **Screen row check:**
  - The −21 % / −54 % / −7 % numbers reproduce. They are single runs on the tuning/training scenario (B3/E1). Add the new-demand figures: −22 % / −29 % / −6 % (c.).
  - **"no seeds or CI" is imprecise.** There are 50 runs per MPR with boxplots, but only for RL sensitivity, not for the RL-vs-FB headline.
  - Grid-search details are absent, so "**grid-search tuned**" should carry "(method undocumented, in-sample)".
- **Not checked / uncertain:**
  - Figs. 34–43 boxplots were not rendered.
  - New-demand profile values (Fig. 27 ff.) were not read.
  - The lane-drop median of ≈ 55 % is read from Fig. 33 (QI).

#### Claim audit, #39

Remaining delay = 1 − fraction eliminated. Gain = (remaining_FB − remaining_RL) / remaining_FB (c.).

| Scenario (100 % MPR) | RL eliminated | FB eliminated | Remaining RL / FB | Gain vs FB (c.) | Locations |
|---|---|---|---|---|---|
| Sag, training demand | 63 % | 53 % | 37 / 47 | (47−37)/47 = **21.3 %** | p. 52, p. 49 |
| Lane drop, training demand | 64 % | 21 % | 36 / 79 | (79−36)/79 = **54.4 %** | p. 53, p. 50 |
| On-ramp, training demand | 19 % | 13 % | 81 / 87 | (87−81)/87 = **6.9 %** | p. 54, p. 50 |
| Sag, new demand | 48 % | 33 % | 52 / 67 | **22.4 %** | p. 55, p. 56 |
| Lane drop, new demand | 36 % | 10 % | 64 / 90 | **28.9 %** | p. 58 |
| On-ramp, new demand | 11 % | 5 % | 89 / 95 | **6.3 %** | p. 60 |

Q[f017 p49]: "The feedback controller was able to eliminate 53% of the delay caused by sag curve when the penetration rate of CVs is 100%."
Q[f017 p54]: "The VSL reduced the total delay by 19% compared to the no control scenario."
Q[f017 p56]: "only eliminate 33% of the delay caused by the sag curve"

- **Median sensitivity.** With the lane-drop RL 50-run median of ≈ 55 % (Fig. 33, QI) in place of the single-run 64 %, the gain is (79−45)/79 = 43 % (c.). Still large, but FB has only one run.
- **How the grid search was done.** One sentence (p. 49): no grid, no tuned values, no objective, no scenario named. It was run per bottleneck, apparently at 100 % MPR on the same short-peak demand that is then used for the comparison. **Tuning and test scenarios coincide** for the training-demand rows.
- **New-demand rows.** These are out-of-sample for both arms, assuming FB was not re-tuned; the text does not say it was. They are the fairer comparison: **22 % / 29 % / 6 %**, each a single run.

#### Reproduction spec, #39 (SUMO 1.27 / libsumo)

- **Simulator used:** custom Python micro-simulator, Δt = 0.5 s (Table 1, p. 39, QI).
  - Car following: Goñi-Ros sag model, i.e. IDM plus a gradient-compensation term (Eqs. 1–7).
  - Lane changing: LMRS (Eqs. 8–22).
  - **Porting:**
    - SUMO has no Goñi-Ros sag model. I am not certain how fully SUMO 1.27 car-following models account for road slope; verify.
    - The sag case therefore needs either a custom car-following model (C++ plugin or per-step libsumo `setSpeed`/`setAcceleration` override) or a substitute bottleneck.
    - LMRS is not in SUMO (LC2013/SL2015 are), so lane-drop and on-ramp capacity drops will differ.
- **Networks (p. 38–45):**
  - **Sag:** 12 km, 1 lane. Grade −0.5 % rising linearly to +2.5 % over x = 10.7–11.3 km. Limit 120 km/h. Control section 9.3–10.3 km. Detector on the uphill (exact position in Fig. 10 only).
  - **Lane drop:** 6 km, 3 lanes, lane 1 drops at 5.7 km. Control section 1.7–2.7 km, applied to lanes 2–3 only. Lane changes forbidden from 0.05 km to the end of the control section. Detectors at 5.7 km and 0.05 km.
  - **On-ramp:** 6 km, 2 lanes plus a 150 m parallel acceleration lane ending at 5.7 km. Control section 1.7–2.7 km on the mainline. Same detectors.
- **Vehicle parameters:**
  - Table 1: v_des 120 km/h, a 1.45 m/s², b 2.1 m/s², T 1.2 s, s0 3 m, v_crit 65 km/h, γ 1.15, c 0.0001 s⁻¹.
  - Table 2 (LMRS): T_min 0.56 s, τ 25 s, x0 295 m, t0 43 s, d_free 0.365, d_sync 0.577, d_coop 0.78, v_gain 69.6 km/h.
  - Homogeneous fleet; δ (speed-limit adherence) value not given.
- **Demand:** trapezoid. 0 → peak over 5 min, 10 min plateau, 5 min ramp-down, then 0 until empty.
  - Peaks: 2400 veh/h (sag); 4200 veh/h (lane drop); 2000 main + 1000 ramp veh/h (on-ramp).
  - Arrival process (deterministic or random headways): **not stated**.
  - The new-demand profile is given only in figures.
- **RL:**
  - A3C, 16 asynchronous workers, 8-core Xeon (p. 46).
  - Actions Δv ∈ {−10, −5, 0, +5, +10} km/h every 60 s.
  - State: 10 × 2 stack of (ρ_bottleneck, ρ_entrance); for the adaptive variant, 10 × 3 with %CV.
  - Actor and critic MLPs 64-128-128-128, ReLU; softmax and linear heads.
  - Terminal-only reward (TD_NC − TD_ctrl)/TD_NC; γ = 0.99.
  - About 10,000 episodes to converge (sag; Fig. 23 runs to ≈ 14.5 k). Episode ≈ 25–30 simulated minutes (fig.).
  - **MISSING:** learning rate, optimiser, entropy coefficient, bootstrap interval b, VSL min/max bounds, checkpoint selection, wall time, episode counts for lane drop and on-ramp.
- **Baseline:** P-control (Eq. 33), measured every T_c with a one-period delay. **MISSING:** v_target, k, ρ_target, T_c, bounds, grid ranges, tuning objective and scenario.
- **Evaluation:** headline single runs. 50 runs per MPR (5–100 %, step 5) for sensitivity; MPR randomness is binomial per vehicle.
- **Code/data:** none. The only URLs in the file are ODU Digital Commons links, e.g. "https://digitalcommons.odu.edu/cee_etds/84" (p. 1).
- **Top guesses needed:**
  1. FB parameters and grid.
  2. A3C optimiser and learning rate, plus action bounds.
  3. Arrival stochasticity at 100 % MPR.
  4. Sag gradient model in SUMO.
  5. The LMRS → LC2013/SL2015 mapping and the capacity drop it yields.
