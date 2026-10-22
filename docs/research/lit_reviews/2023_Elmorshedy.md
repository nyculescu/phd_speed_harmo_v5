# Review: Elmorshedy (2023), Univ. of Toronto PhD, "Dynamic Autonomous Driving Headway Optimization with Deep Reinforcement Learning for Freeway Congestion Management and Control"

Source file: `text/2023_Elmorshedy_Toronto_PhD.txt` (only file read; no web).
Page convention: `[p. N]` is the `=== [page N] ===` marker of the text file (PDF page). The printed thesis page number is N minus 17 (e.g. marker 62 = printed 45). Quotes are verbatim, <= 25 words. "not stated" means I did not find it in the thesis text (I grepped for seed, replicat, confidence, t-test, noise, compliance, field test, ALINEA).

Supervisor Prof. Baher Abdulhai; WOLF/Flow-based interface by Dr. I. Smirnov [p. 29].

## 0. Structure and one-paragraph summary

Paper-based thesis, three technical chapters [p. 29]:
- Ch. 2 (IEEE OJ-ITS 2022): ACC time-headway impact on a calibrated 45 km QEW corridor in Aimsun + a regulator ("On-Off") headway controller.
- Ch. 3 (TRR 2023): PPO headway controller, single on-ramp bottleneck, one global agent.
- Ch. 4 (submitted manuscript): PPO headway control, 3-bottleneck and 8-bottleneck networks, global / independent / one-hop multi-agent.

Control idea (Ch. 3-4): a traffic-management centre sets the desired ACC time headway per ~300-500 m segment, every 10 s, for 100 % ACC vehicles. The agent learns to give very long headways (median 4-7 s, up to 20 s) to ramp vehicles, which is functionally ramp metering, and short headways (about 0.8-1.4 s) on the mainline. Thesis abstract claim: delay reduced "by up to 57% and 46% in the single-bottleneck and the multi-bottleneck networks" [p. 3]. These two numbers are relative to uncontrolled ACC with a 0.8-2.0 s headway range, not to the best static baseline (see section 6).

## 1. Problem, network, demand, incidents

### Ch. 2 (QEW corridor, quantification + On-Off control)
- Eastbound QEW, Ontario, plus parallel service roads, AM peak 6:00-10:00, 45 km, SOV and HOV classes, no trucks [p. 35]. Multiple bottlenecks and hotspots; base case has "two major congestion areas" east and west [p. 49].
- Demand from the Transportation Tomorrow Survey 2016 and larger assignment models [p. 35]; 142 TAZs, eight 30-min OD matrices [p. 171].
- Incidents: not stated (none modelled).

### Ch. 3 (single on-ramp bottleneck)
- Three-lane mainline plus one ramp, geometry of the Churchill ramp, Toronto [p. 74]. About 6 km long (Table 3-1) [p. 78].
- Mainline cut into six sections of ~300-500 m plus three ramp sections [p. 74-75]. Entry sections elongated to avoid virtual queues [p. 74-75].
- Demand: mainline 6000 veh/h, ramp 1260 veh/h, constant distribution; speed limit 120 km/h mainline, 50 km/h ramp [p. 77].
- How the demand was chosen: quote [p. 77] "the whole demand (7260 veh/hr) was tested first on the same network with no ramp demand to ensure that breakdown didn't occur". The split mainline/ramp was then set "analogous to that found in the real observed data" [p. 77].
- Simulated time 33 min 20 s = 200 control steps of 10 s [p. 77]. Incidents: not stated (none).

### Ch. 4 (3 and 8 bottlenecks)
- Three-lane mainline, three consecutive on-ramps, geometry between Churchill and Southdown ramps [p. 110]; 8-ramp network between Churchill and Cawthra ramps [p. 127]. Ramps 4 and 5 are about 200 m apart [p. 131].
- Demand: "the current real demand is scaled by a 2.5 multiplier" [p. 107]. Absolute veh/h values: not stated in these chapters. Network length of the 3- and 8-bottleneck networks: not stated.
- Reasons given for the 2.5x [p. 107]: (1) with 0.8 s headway the congestion was resolved at real demand, (2) anticipated future demand growth, (3) "increasing the demand to the level that activates the bottlenecks in the case of no control". Same multiplier for the 8-ramp network "to activate the bottlenecks even with the minimum 0.8 sec headway scenario" [p. 128].
- Sim time 33 min 20 s, 10 s cycle [p. 108]. Incidents: not stated.

## 2. Simulator, car-following / lane-change, capacity drop

- Simulator: Aimsun Next 20 (commercial), via modified Flow framework + RLlib 1.8.0 [p. 76-77, 107]. Aimsun is also the Ch. 2 simulator (MicroSDK for external models, API for control) [p. 37].
- Human car following in Ch. 2: Aimsun default Gipps; "The manually driven vehicles in this study follow Aimsun's default Gipps model" [p. 38]. Manual speed acceptance 1.1 vs ACC 1.0 [p. 48].
- ACC car following (all chapters): Milanes-Shladover 2014 model, Aimsun's default ACC model [p. 46, 77]. Gap mode a = k2(x_l - x - thw*v) + k3(v_l - v); free mode a = k1(vf - v); detection thresholds 100 m / 120 m; k1-k3 "Default values in Aimsun" [p. 46-47]. a_max 2.0 m/s2, normal decel 3.0 m/s2, vf 100 km/h in Ch. 2 table [p. 47]; vehicle length 5 m; min headway 0.8 s (Tables 3-1 and 4-1) [p. 78, 108-109].
- IDM tested in Ch. 2 only: a=2, b=3, v0=100 km/h, s0=1 m, delta=4 [p. 40]. It was dropped because its achieved headway exceeds the desired one (average achieved 0.9 s for desired 0.8 s) [p. 44-45].
- Lane change: "Aimsun's Default" (Tables 3-1, 4-1) [p. 78, 108].
- Reaction time: 1.1 s for all vehicles, "found to be equal to 1.1 sec as a result of the network calibration" [p. 39]. Sim step 0.1 s.
- Capacity drop modelled? Only emergent from Aimsun. The thesis never gives a capacity-drop percentage measured in its own Ch. 3-4 networks. It shows flow-density diagrams "in which we plot the free-flow and congested lines separately to highlight the capacity loss" [p. 73] (Fig. 3-4) without a number. The Ch. 4 abstract cites the literature: "Capacity loss of ~10-20% is established in the literature and is responsible for up to 50% increase in system delay" [p. 95]. This is a citation, not a measurement of the Aimsun plant. The ch. 3/4 networks are described as "adopted from the geometry" of real Toronto ramps [p. 74, 110]; there is no calibration or validation of those networks against field data (not stated).
- Calibration/validation (Ch. 2 QEW only): manual calibration, GEH on 43 detectors: average GEH 4.9 (4-h) and 5.9 (1-h), 91 % / 87 % with GEH < 10, 56 % / 49 % < 5; speed RMSE 0.24 [p. 36]. Data: 20-s loop data on 12 days in Nov 2016, Google Directions speeds Oct 2018 [p. 173]. Calibrated: demand factor 80 %, reaction 1.1 s, merging distance 200 m, etc. (Table A1-1) [p. 176]. Appendix claim [p. 175]: simulated and observed flow-density diagrams "show similar values for road capacity (maximum flow), breakdown density, and free-flow speed" (qualitative, figures only). The calibrated QEW model was NOT the plant used for RL.
- Ch. 2 all drivers assigned the same parameters (homogeneous) [p. 36].

## 3. RL formulation (Ch. 3 and 4)

- Algorithm: PPO (KL-penalty variant, not clipped: "We found that the KL loss function gives slightly better results" [p. 71]); dense MLPs [32,32,32] policy and value, not shared; lr 5e-5, gamma 0.99, lambda 0.95, KL target 0.02, 10 SGD epochs, minibatch 128, 800 env steps per iteration (4 rollouts x 200 steps) (Tables 3-2, 4-2) [p. 77-79, 109].
- Discrete actions: continuous action tried too, "no substantial differences in performance, but somewhat faster learning for the agent with discretized actions" [p. 76]. Test-time actions are sampled stochastically: "sampling actions stochastically even at test time gave better results" [p. 76].
- State: average flow and speed per controlled section over the previous 10 s (detector mid-segment), plus bottleneck flow/speed in Ch. 4; scaled to [-10, 10] [p. 75, 106].
- Action: one desired headway per controlled segment, applied once per cycle. Ch. 3: 20 actions, mainline 0.8-2.7 s in 0.1 steps, ramp 1.0-20.0 s in 1.0 steps [p. 75]. Ch. 4: mainline 0.8-2.0 s, ramp 1-10 s; ramps 4 and 5 of the 8-ramp network extended to 1-20 s [p. 106, 130]. Headway ramp change limits: accel 2.0, decel 3.0 m/s2 [p. 77]. Headway never below 0.8 s "to ensure safety" [p. 79].
- Rationale for the long ramp range [p. 75]: "traffic breakdown was not avoided when the same ranges were assumed for mainline and ramp vehicles".
- Reward: bottleneck (merge) section flow over the previous 10 s, normalised to [-10,10]. Justification: total time spent minimisation is equivalent to exit-flow maximisation "given that the whole demand is served" (Papageorgiou et al. 2003) [p. 76, 107]. Chosen over delay because flow is "measurable in real-time ... in field test scenarios" [p. 76]. Ch. 4 global agent: sum of the 3 bottleneck flows; independent: own bottleneck flow; one-hop: own + directly neighbouring bottleneck flows [p. 111, 114, 116].
- Agents: Ch. 3 single global agent controlling 5 segments (scenario 1), ramp only (scenario 2) or 4 mainline (scenario 3) [p. 79-80]. Ch. 4: global (3 or 8 segments), independent (one per bottleneck), one-hop; scenario (1) ramps only, (2) ramps + mainline; 8-ramp network only independent and one-hop (global judged "not manageable") [p. 110, 128].
- Penetration: 100 % ACC in all RL experiments [p. 68, 101]. Mixed autonomy is listed as future work [p. 148].
- Training budget: Ch. 3: ~800 iterations (scenarios 1, 3), 400 (scenario 2) [p. 79-80]; at 800 steps per iteration that is about 640k control steps (INTERPRETATION: my arithmetic). Ch. 4: "between 250 and 350 iterations ... depending on how fast convergence was reached" [p. 110]. Reward-vs-iteration curves are shown as convergence evidence (Fig. 3-6) [p. 80].
- Seeds (training or evaluation), hyperparameter tuning, number of training runs: not stated.

## 4. Baselines

- Ch. 2: base case = 0 % ACC (Gipps human drivers); uncontrolled ACC at 0.8 s, 2.0 s, range [0.8,2.0]; the regulator-based On-Off control. On-Off rule: T_min if v_i < v_cr or q_i > Q*, else driver default; updated every 5 min; v_cr = 50 km/h; thresholds "decided based on historical observations" [p. 52-53, 59]. Whether Q*, v_cr were tuned systematically: not stated.
- Ch. 3 and 4 baselines: only (i) "uncontrolled ACC" = every vehicle picks headway in [0.8,2.0] s (mean ~1.2 s in Ch. 2/3 motivation), and (ii) "0.8 s everywhere" (best non-dynamic headway) [p. 77, 107-108]. Uncontrolled segments around the controlled ones are set to 0.8 s [p. 79].
- NOT compared: no-control with human drivers on the same plant; classical ramp metering (ALINEA etc.), VSL, feedback controllers; the Ch. 2 On-Off controller; MPC; other RL algorithms; a constant long ramp headway (static ramp throttle). The text grep found ALINEA/ramp metering only as analogy citations (e.g. [p. 84, 114]). "Tuned" baselines: n/a (static headways are the only baselines).
- The thesis states the conceptual analogy [p. 84]: "metering the ramp with headway control in a way analogous in effect to traditional ramp metering". No numerical comparison.

## 5. Evaluation

- Metric: "average network delay of all vehicles in the given highway segment" [p. 79]; reported as total / freeway (mainline) / ramp delay, % differences; Table 3-3 gives absolute uncontrolled ACC values (total 41.38, freeway 31.4, ramp 95.9 sec/km) [p. 81]. Throughput and cumulative bottleneck flow plotted (Fig. 3-16) [p. 90]. Flow-density diagrams of the bottleneck sections used as the main mechanism evidence.
- Virtual queues: entry sections are elongated "to accommodate all queuing vehicles" and all demand must enter by the end of the run [p. 106-107]. So ramp queue time is inside the delay metric (good), but ramp queue length is effectively unbounded (see 9b).
- Safety metric (TTC): not used; listed as future work [p. 150].
- Replications: Ch. 2 "Five replications ... and the average values ... are compared" [p. 39]. Ch. 3-4: number of evaluation runs, seeds, confidence intervals, significance tests: not stated. Trained-action histograms are shown "for one simulation" [p. 82]. All tables report one number per cell (point estimates).
- Train/test separation: the agents are trained and evaluated on the same network and the same constant demand (6000+1260 veh/h; 2.5x scale); separate test demand or seeds: not stated. The thesis itself says [p. 150] "The trained agents in this research are specific to the networks they are trained for".
- Generalisation: none tested (variable demand, other geometry, penetration) - all listed as future work [p. 149-150].

## 6. Headline results

Ch. 2 (QEW, Shladover ACC, 5 replications) [p. 48, 54-55]:
- 2.0 s headway at 100 % ACC: throughput -20 %, delay +110 %, speed -24 %. 0.8 s: up to +3 % throughput, -34 % delay, +18 % speed. Range headway: +2 %, -16 %, +6 %.
- With On-Off control at 100 % penetration: 2.0 s case turns to +2 % / -15 % / +12 %; range case +3 % / -28 % / +17 % (delay is a reduction).
- IDM-ACC at 2.0 s: throughput -26 %, delay +122 %, speed -25 % [p. 41].

Ch. 3 (single merge; delay differences, total / freeway / ramp) [p. 81, 84-85, 87-88]:

| Scenario (agent controls) | vs uncontrolled ACC | vs 0.8 s everywhere |
|---|---|---|
| 0.8 s everywhere (static) | -35.94 / -40.16 / -30.54 % | - |
| (1) mainline + ramp | -53.38 / -83.85 / +53.48 % | -27.24 / -73.02 / +120.97 % |
| (2) ramp only | -56.71 / -88.99 / +49.75 % | -32.43 / -81.61 / +115.60 % |
| (3) mainline only | -45.51 / -32.66 / -69.59 % | -14.95 / +12.53 / -56.21 % |

- Breakdown avoided in (1) and (2), not avoided in (3) [p. 92]. Trained ramp headway median ~7 s (1) and ~5 s (2), mode 4 s; mainline medians ~1.0 s in (1) [p. 82-86].
- The abstract's "57 %" = -56.71 % vs uncontrolled ACC (scenario 2), whereas the gain over the best static baseline (0.8 s) is 32.43 % total delay (ramp-only), 27.24 % (mainline + ramp).

Ch. 4, 3-bottleneck network (total delay vs uncontrolled ACC / vs 0.8 s) [p. 111-112, 116-117, 119-120, 122-123, 125]:
- 0.8 s everywhere: -30.34 % total vs uncontrolled.
- Ramps only: global -45.87 / -22.30 %; independent -41.04 / -15.37 %; one-hop -45.73 / -22.10 %. Ramp delay vs 0.8 s: +42.59 %, +67.66 %, +45.70 %.
- Ramps + mainline: global -32.87 / -3.63 %; independent -35.86 / -7.93 %; one-hop -38.08 / -11.12 %.
- Fundamental diagrams: breakdown mostly avoided; global in (2a) left residual congestion at bottleneck 1 [p. 120].

Ch. 4, 8-bottleneck network, ramps only [p. 128-133]:
- 0.8 s everywhere: only -11.08 % total delay vs uncontrolled ACC. Independent: -25.27 % vs uncontrolled / -15.97 % vs 0.8 s; one-hop: -27.86 % / -18.87 % (ramp delay +4.90 % vs uncontrolled; +17.86 % vs 0.8 s).
- Breakdown not avoided at bottlenecks 4 and 5 even with ramp headway up to 20 s [p. 130, 132]; a 19 s headway on R5 was imposed unsuccessfully [p. 134].
- Thesis note [p. 129]: "we did not differentiate between delays on the ramp and delays on the freeway in this work".
- Ch. 4 abstract: "up to 22.30%, and 18.87% compared to shortest headway setting" [p. 96].

Qualitative thesis claims: ramps-only control beats ramp + mainline control [p. 119, 136]; global agent best only for small problems, one-hop best for larger [p. 138]; "The solution to the headway control problem is not unique" [p. 137].

## 7. Robustness / realism checks

- Sensor noise, detection errors, communication delay/loss, compliance of drivers with the commanded headway: not stated. 100 % automated compliance assumed. Ch. 2 notes the ACC reaction time 1.1 s and a speed-acceptance difference [p. 39, 48].
- Sim-to-real / field test: none. Reward is chosen to be "implemented in field test scenarios" [p. 76] but no field test.
- Demand variation / incidents / penetration sweep (for the RL): none.
- Safety: headway floor 0.8 s only; "vehicles with a time headway shorter than the reaction time may raise safety concerns" (reaction time 1.1 s > 0.8 s headway) [p. 57].
- Sensitivity to hyperparameters, to reward choice, to different action ranges: only the continuous-vs-discrete remark [p. 76]; nothing else.

## 8. The thesis's own limitations and future work [p. 148-150, also 56-57, 92, 138]

- Mixed autonomy (RL assumed 100 % penetration) [p. 148-149].
- Closely spaced, high-demand ramps (R4/R5) not solved; need other measures (route guidance) or longer-range coordination [p. 149].
- Coordinated multi-agent RL with explicit coordination [p. 149].
- Variable demand; thesis expects headway choice "won't be of huge significance in low demands" and "shorter headways may be sufficient" at medium demand [p. 149-150].
- A generalised agent; "The trained agents in this research are specific to the networks they are trained for" [p. 150]; transfer learning.
- Safety (TTC) and stability metrics [p. 150]; integration with surface-street control [p. 150].
- Ch. 2 limits: IDM headway error; results "a first good approximation" [p. 58, 60]; ACC models vary by manufacturer [p. 60].
- Ch. 3: global agent has "curse of dimensionality" training difficulty [p. 92]. NN training is computationally intensive [p. 138].

## 9. INTERPRETATION (mine, not the thesis's claims)

### (a) Where does the gain physically come from; would it survive a realistic 2-11 % capacity drop?
- Mechanism: the learned policy is ramp throttling. Median ramp headway 4-7 s means ramp inflow is cut to a few hundred veh/h (a 5 s headway is about 720 veh/h per lane of ramp traffic, 7 s about 515 veh/h; my arithmetic, ramp lane count not stated), so that merge-section flow stays below the level that triggers breakdown. The thesis itself says so: the agent "learning to meter the ramp" and ramp-only control is best [p. 84-86, 91].
- The gain over the best static baseline (0.8 s) is 15-32 % total delay and comes with ramp delay +18 to +121 % [p. 85, 88, 112, 132]. Mainline delay falls 55-89 %. So the net benefit exists only because mainline vehicles dominate the delay sum, and a breakdown costs a lot of mainline delay. The thesis states this as the explanation [p. 119].
- Size of the breakdown penalty in this plant: not measured as a percentage. The huge freeway delay reductions (-76 to -89 % vs 0.8 s) suggest the Aimsun ACC plant (Milanes-Shladover ACC, 0.8 s headway, 1.1 s reaction time, 100 % ACC, 5 m vehicles) loses a lot at a merge when pushed over capacity. I cannot verify the drop size; the flow-density figures [p. 74, 82, 85] show it only graphically. The only quoted figure is the literature's 10-20 % [p. 95].
- Demand was tuned to the regime where control matters: Ch. 3 total demand 7260 veh/h on three lanes (about 2420 veh/h/lane), chosen so that the base breaks down at the merge but "breakdown didn't occur" without ramp demand [p. 77]; Ch. 4 a 2.5x multiplier chosen "to activate the bottlenecks" [p. 107, 128]. In the 8-ramp network, where the static 0.8 s baseline is already congested (-11 % only), the RL gain over it is still 16-19 % but not all bottlenecks cleared [p. 128-132].
- Survival under a small capacity drop: no evidence in the thesis either way (never tested). Reasoning: if the physics gain comes from avoiding a capacity drop, the achievable delay saving should shrink with the drop. At 2-11 % the saving relative to a well-tuned static or ALINEA-type metering would be expected to be small, because throttling the ramp trades a certain ramp delay against a smaller avoided mainline loss. This matches the candidate's own finding; it is an inference, not something shown in the thesis. A gain-over-static of 20-30 % that relies on the demand being just above capacity and on an unbounded ramp queue should not be expected to transfer.
- Also, the comparison to "uncontrolled ACC" includes a deliberately poor baseline (range headway up to 2 s), which inflates headline numbers (57 %, 46 %) with a gain that is mostly from the ACC headway setting itself (0.8 s everywhere already gives -30 to -36 % [p. 81, 111]), not from the RL.

### (b) What is weak in the evaluation
- No classical ramp-metering baseline (ALINEA/PI-ALINEA, demand-capacity), no VSL baseline, no static throttle baseline (e.g. constant ramp headway of 5 s), no On-Off controller from Ch. 2: the incremental value of RL over a one-parameter tuned throttle is untested. Since the policy reduces to a long ramp headway, a constant long ramp headway might reproduce most of the gain (not tested; INTERPRETATION).
- Point estimates from apparently single runs; no seeds, CIs, tests; no training-seed variability; "one simulation" histograms [p. 82]. Stochastic sampling at test time used because it "gave better results" [p. 76] (selected on the test environment, as far as stated).
- Train = test (same network, constant demand, 33 min, 200 steps). Constant demand means no adaptation challenge; a fixed ramp setting would face the same conditions.
- Plant realism: the RL plant is a generic 3-lane merge with ACC-only traffic (100 % ACC, homogeneous behaviour), not calibrated; capacity drop not quantified; very short horizon.
- Unbounded ramp queues (entry sections elongated) hide spillback to surface streets; ramp delay is simply added to freeway delay with equal weight [p. 129]. Ramp headways of up to 20 s imply stringent compliance and long waits (not examined fairness-wise).
- Delay normalisation (sec/km, "delay of all vehicles on segments") and the exact definition of reference delay are not given beyond [p. 79]; delay includes elongated entry sections, so numbers depend on how those were built.
- Reward = bottleneck flow is not equal to delay; the thesis admits non-uniqueness and that reward-maximising behaviour caused worse delay in the ramp + mainline case [p. 137]. No ablation of reward or state.
- No sensor noise, delays, comms, partial penetration, or mixed traffic. No safety metrics.
- Abstract numbers are the maxima over scenarios and compared with the weakest baseline.

### (c) What an innovative follow-up could be, given the candidate's finding
These are suggestions, not claims from the thesis.
1. Report the "value of adaptivity" versus a tuned ALINEA/PI-ALINEA and a tuned constant throttle on a plant with a measured 2-11 % capacity drop, and map where RL wins/ties/loses (regimes). This thesis supplies no such comparison, so it leaves that gap open.
2. Use the thesis's own large sensitivity of capacity to the driver/ACC headway setting (throughput -20 to -26 % between 2.0 s and 0.8 s at 100 % ACC [p. 41, 48]) as the hidden condition: when the vehicle population's headway or reaction mix shifts, the best ALINEA set-point or throttle rate shifts, so a fixed-tuned controller is mis-tuned and an adaptive controller has headroom. This turns the gain mechanism from "avoid a 20-40 % breakdown" into "track a moving capacity". It needs a plant where capacity truly varies by that much across conditions (the candidate's T2 criterion).
3. Pre-register the adaptation gain: the fraction of the gap between fixed-tuned and per-condition-tuned controller closed by RL/adaptive scheduler, with paired seeds and CIs. The thesis has none of this statistical machinery.
4. Do both ramp-queue-bounded and unbounded cases, with the primary metric including origin/ramp queues (the thesis includes ramp queue delay but with unbounded storage), and report surface-street spillback as a side constraint.
5. Mixed autonomy (low CAV penetration) with realistic compliance, which the thesis flags as future work [p. 148-149]; at low penetration the headway-as-metering mechanism cannot throttle the ramp, so a different actuator mix (per-lane limits for HDVs, CAV speed commands) is required: an open design space.
6. The one-hop vs independent vs global comparison (coordination effect, ramp-vs-freeway delay balance) [p. 137-138] is a small but concrete finding that could be re-tested with proper seeds and a stronger baseline set.
