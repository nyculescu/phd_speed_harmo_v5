# Review: Mansouryar (Sapienza PhD, 2025/26) and Zhou (Maryland MSc, 2019)

Source files (text extractions):
- A: `text/2026_Mansouryar_Sapienza_PhD_related.txt`
- B: `text/2019_ZhouW_Maryland_thesis.txt`

Conventions
- `[p. N]` is the `=== [page N] ===` marker of the text file, NOT the printed page number. Printed = marker - 1 for A (marker 94 = printed 93); printed = marker - 10 for B (marker 11 = printed 1).
- Quotes are verbatim, 25 words or fewer. "not stated" means I did not find it in the file. Numbers read from figures in the text extraction are flagged "verify against the figure".
- Everything labelled INTERPRETATION is my reading, not the author's claim.
- Both texts contain internal inconsistencies. They are listed per thesis, because they limit how far the numbers can be trusted.

---

# A) Mansouryar, "Smart Multimodal Corridor Control" (PhD, Sapienza, supervisor G. Fusco)

Scope read: Ch. 7 (rule-based VSL, field validation), Ch. 8 (SUMO comparison with the RL jam-shrinking VSL), conclusions, and Ch. 6 (DRL signal control) briefly. The thesis is mostly urban (bus priority, signals). The VSL part is two chapters.

## A1. Problem, network, demand, incidents

VSL on urban motorways, advisory only, no enforcement.
- Padua-Mestre A4 / Mestre ring road, Italy. Operational VSL system with lane-level VMS [p. 99-100]. Quote: "advisory system without enforcement measures applied to guarantee drivers' compliance" [p. 99].
- SUMO sketch of Padua-Mestre: 2.5 km, 5 controlled edges, panels/detectors every 500 m [p. 103].
- SUMO demand for that sketch: 3 routes per direction, 3600 s of continuous inflow, exponential departures with mean headway 0.5 s, "about 7200 vehicles per hour" [p. 104]. The number of lanes is not stated explicitly there. Lane control is for three lanes (slow, middle, fast) [p. 102].
- Naples ring road ("Napoli"): "6 km segment" [p. 110]. Demand profile, duration and lane count are not stated. The congestion type is a moving jam wave "caused by inflow change" [p. 118]. Standing queues are discussed only in the literature part [p. 115].
- Incidents: not modelled in the SUMO studies (not stated). The field system is described as also reacting to events ("reacts to events by protecting the area affected") [p. 100], but no incident results are shown.

## A2. Simulator, parameters, capacity drop

- SUMO. For the VSL chapters the car-following model and its parameters are not stated. The Krauss table (Table 3) is for the urban signal-control study [p. 84].
- Calibration of the Padua-Mestre SUMO sketch: the text says it "was chosen to test and calibrate the microsimulation algorithm and model" [p. 103], but no calibration procedure or numbers are given (not stated).
- Capacity drop: not modelled as a parameter, not calibrated, not validated, no size given (not stated). "Capacity drop" appears only in the literature review and in the description of RL-VSL for standing queues: "mitigating capacity drops" [p. 115]. Table 9 lists "Stabilizing occupancy and preventing capacity drop" for a Barcelona field study [p. 98].
- Driver compliance is modelled, as a speed-factor distribution (the stated novelty) [p. 110, 112-114]:
  - Fitted from a driving-simulator study (Storani et al. 2025) with questionnaires. Naples-ring-road-like layout, two lanes, 110 -> 80 -> 60 km/h and 110 -> 60 -> 80 km/h [p. 110-111]. This is not field data.
  - Compliant: speed factor = `1.278 - exp(-1.33584 + 0.144109 N(0,1))` [p. 113-114]. KS p = 0.700 [p. 113].
  - Non-compliant: `1.0 + exp(-1.50702 + 0.625617 N(0,1))` [p. 114]. KS p = 0.984 [p. 114].
  - Compliance rule: v85 <= max(1.05 V, V + 5 km/h) [p. 113].
  - The share of non-compliant drivers is only stated in the conclusion: "although 50% of the drivers were non-compliant, their speed profile was still constrained by the behavior of the compliant drivers" [p. 123].

## A3. Control methods

### Rule-based dynamic VSL (the author's own, from the operational Traffic Guidance System) [p. 100-102]
- Advisory limits 40 to 90 km/h in 10 km/h steps, per lane [p. 99]. Ordinary limits: 90 km/h on left and central lanes, 60 km/h on the right lane [p. 99].
- Input: 5-minute per-lane data. A double exponential filter (alpha = 0.813864136, alpha1 = 0.391470025, gamma = 0.371373121) smooths density and speed [p. 100].
- Critical sections: density above a critical threshold taken from the fundamental diagram and field observation [p. 101].
- Logic [p. 101]:
  - Disposal capacity = density x speed x `pjsmalt` (generally 1.6), saturated at 90 % of section capacity.
  - Vehicles stored between each upstream VMS and the critical section divided by that capacity gives a disposal time.
  - The target speed is a function of VMS distance and disposal time, clipped to a minimum of 40 km/h (ring road) or 60 km/h (motorway).
- Consistency checks, iterated up to 10 times (usually 2-3) [p. 101-102]:
  - Observed-speed check (within 20 km/h of measured speed).
  - Vertical check (consecutive panels within 30 km/h).
  - Lane-adjustment check (at most two different speeds per panel).
  - Horizontal check (lane order, at most 30 km/h between lanes).
- No tuning procedure is described (not stated).
- Quality flag: the printed observed-speed rule reads "if |Vtarget - Vave| > 20 km/h, VTnew = VT, else VTnew = Vave + 20" [p. 101], which contradicts its own description ("the target speed is reduced"). I think it is a transcription slip, but I cannot confirm.

### RL "jam-shrinking" VSL [p. 115-117]
- Taken from Han et al. (2022), ref. [180] [p. 115]. The thesis calls the controller "DRL" [p. 120], but the formulation it writes down is Q-learning with a count-based learning rate and softmax exploration. No neural network or architecture is described. Quote: "solved using a model-free Q-learning algorithm" [p. 117].
- State (5 variables) [p. 116]: inflow to the VSL area q_I, mean density in the VSL section, jam length l_jam, mean speed in the jam, index of the most upstream congested cell P_jam.
- Action [p. 116]: a = [V(k), P_V(k)], the speed-limit value and the index of the most upstream VSL sign.
- Reward [p. 116-117]: J(k) = l_jam / v_jam and r(k) = J(k) - J(k+1), the reduction in "congestion severity".
- Update rule and exploration [p. 117]: kappa(s,a) = [1 / (1 + C(s,a)(1-gamma))]^0.7, softmax with temperature T.
- Not stated: gamma, T, number of episodes, convergence criterion, training scenario versus test scenario, action discretization, control period, and the state and action tables as actually used.
- Physical principle quoted from the cited work: speed limits upstream of a jam must give "sufficiently low inflow" and keep "moderate density in the VSL-controlled area" [p. 115]. Implicitly this is a jam-wave (SPECIALIST-type) logic [p. 115].

## A4. Baselines and tuning

- Ch. 7 SUMO: no control versus the rule-based VSL [p. 105-106].
- Ch. 8 SUMO: three scenarios only, no VSL, adaptive rule-based VSL, and RL VSL [p. 118-122].
- Field: VSL-active versus VSL-inactive periods [p. 107].
- No ramp metering baseline, no feedback controller (e.g. SPECIALIST or a PI-type law), no fixed-speed-limit baseline, no oracle. Whether the rule-based VSL was re-tuned for Naples is not stated. Whether the RL agent was tuned is not stated. The fairness of the comparison cannot be checked from the text, although the thesis promises "fair" comparison [p. 110, 115].

## A5. Evaluation

- SUMO Ch. 7: average travel time, outflow/inflow ("network throughput"), bottleneck speed [p. 105-106]. The text gives only qualitative statements, with the numbers in figures 47-49. Number of runs, seeds and statistics: not stated.
- SUMO Ch. 8: jam extent in space, mean time loss, emergency braking count, mean corridor speed [p. 117-122]. One value per scenario, no seeds, no replications, no CI (not stated).
- Train/test separation of the RL agent: not stated.
- Field data (Padua-Mestre, VSL-active versus inactive) [p. 106-107]:
  - One year of 5-minute per-lane flow, occupancy and speed; K-Means and DBSCAN clustering to separate stable, congested and transition states.
  - Two-sample t-tests and Kolmogorov-Smirnov tests on speeds and travel times.
  - This is an observational comparison of active versus inactive periods. Matching of demand, weather and days is not described (not stated).
  - Figure 53 caption contrasts "Tuesday, 5th of October VSL system was not active, Wednesday, 3d of March VSL was active" [p. 109], so the example days are in different months.

## A6. Headline numbers

| Item | Value | Page |
|---|---|---|
| Field travel time, VSL vs no VSL | "decreased by 9-19 %" | [p. 107] |
| Field speed variance | "reduced by 39-60 %" | [p. 107] |
| Abstract claim | "up to 19%" travel time, "more than 50%" speed variance, in congested conditions | [p. 3] |
| Naples jam extent, no VSL | 2500 m (x = 5500 -> 3000 m) | [p. 118] |
| Naples jam extent, rule-based VSL | 1500 m (x = 5500 -> 4000 m), "approximately 40%" shorter | [p. 119-120] |
| Naples jam extent, RL VSL | about 1250 m, "50% improvement" | [p. 120] |
| Mean time loss, no VSL / adaptive / RL | 371.86 / 273.52 / 302.58 s (verify against Figure 61) | [p. 121] |
| Emergency braking events, no VSL / adaptive / RL | 45 / 19 / 0 | [p. 122] |
| Mean corridor speed, RL / adaptive / no VSL | 51.48 / 44.028 / 54.288 km/h (verify against Figure 63) | [p. 122] |

- My arithmetic on the time-loss figure: rule-based -26.4 % and RL -18.6 % relative to no VSL. This relies on mapping the three numbers to the labels by text position and by the statement that adaptive is lowest.
- The mean-speed values show no-VSL with the highest mean speed. This is not discussed by the author.
- Padua-Mestre SUMO sketch: qualitative improvements in travel time, throughput and bottleneck speed, with no numbers in the text [p. 105-106].
- Quality flag: one SUMO paragraph says "findings from your Padua-Mestre real-world analysis" [p. 106], which looks like leftover drafting text.

## A7. How the rule-based VSL compared with the RL controller, and why rule-based is preferred

What the thesis says, exactly:
- Congestion reduction and throughput: the rule-based controller is better. Quote: "This results in the lowest mean time-loss and the smallest speed variability" [p. 121]. And: "Adaptive VSL is more effective for congestion reduction and throughput, whereas DRL-VSL excels in enhancing comfort and operational safety" [p. 123].
- Jam length: the RL controller is better (1250 m versus 1500 m; no control 2500 m). Quote: "the Deep Reinforcement Learning (DRL) controller demonstrates superior performance" [p. 120].
- Safety proxy: RL eliminates harsh braking (0 versus 19 versus 45) [p. 122-123]. The rule-based reduces but does not eliminate it [p. 122].
- The conclusion calls the two "complementary strengths that could be combined or tuned depending on system priorities" [p. 123].
- Stated reason for preferring rule-based for deployment: only the abstract says it: "highlighting the practicality of the rule-based solution for deployment" [p. 3]. The body gives no explicit argument (training cost, interpretability, safety certification, data needs, robustness): not stated. The supporting facts in the text are:
  - The rule-based controller is already operational on the Mestre ring road, with field validation (9-19 % travel-time reduction) [p. 100, 106-107, 123].
  - It has the best time loss in Naples [p. 121].
  - The RL controller has no field validation, and the author lists "transferability, scalability, and interpretability" as open issues for learning-based control [p. 126].
  - Future work: "Hybrid control frameworks combining rule-based logic with adaptive learning mechanisms could provide a balance between robustness and flexibility" [p. 126].
- Control-mismatch caveat: the RL agent targets jam length (a surrogate), not time loss, so its ranking on jam length and its ranking on time loss differ.

## A8. Stated limitations and future work [p. 126]

- Microsimulation "cannot fully capture all aspects of real-world traffic behavior"; sensor inaccuracies, communication delays and long-term adaptation are not modelled.
- VSL field analysis is on one corridor, so transferability depends on local traffic and compliance. The compliance model is "a simplification of observed behavior".
- Interaction between simultaneous control strategies is not addressed.
- Future work: connected-vehicle data for state estimation, hybrid rule + learning, transferability/scalability/interpretability of learning, field pilots, person-based and environmental metrics.
- Ch. 8 also notes that the rule-based VSL has no outflow-balancing strategy yet [p. 120].

## A9. Chapter 6, DRL signal control and transit priority (brief)

- Network: Via Prenestina, Rome, 5100 m, 21 signalized intersections, tram lines 5, 14, 19 [p. 85]. SUMO with Krauss, max speed 50 km/h [p. 84]. Counts from ATAC at three time windows (morning, lunch, evening peaks) [p. 85].
- Method: DQN-type agent with 2 conv layers plus hand-made features (queue L, waiting time W, phase P, vehicles V) and a phase-gated head [p. 81-83]. Action: keep or switch to the next phase. 4 s update interval, gamma 0.9, lr 0.001, epsilon 0.05, memory 20,000 [p. 82]. Reward: weighted sum of queue, time loss, waiting time, switches, throughput (and tram terms in scenario 2) [p. 80-81]. Weights omega are not given (not stated).
- Calibration and validation: outflow per intersection, R^2 = 0.9603, RMSE 44.77, MAPE 10.04, GEH "89% < 4" [p. 86-87].
- Results [p. 88-92]: network queue sum 10,713,723 m (current) -> 4,943,131 m (scenario 1, -54 %) and 7,673,754 m (scenario 2, with tram priority, -28 %). Private vehicle delay about -50 % in scenario 1. Tram delay -31 % in scenario 2.
- The baseline is "Current". Its type is not defined in the chapter (not stated). The abstract says the DRL system beats "fixed-time and traditional adaptive controls" [p. 2], but the chapter only shows "Current". No seeds, no CIs. The conclusion says the effect was measured "from the start of training" [p. 92].
- INTERPRETATION: signal control has real headroom (queue and delay cuts of 30-50 %), so large RL gains there are plausible. They say nothing about a freeway bottleneck with a 5-8 % capacity drop.

## A10. INTERPRETATION (Mansouryar)

Where the gain comes from physically:
- Field and Padua-Mestre sketch: lowering and harmonizing speeds upstream of a critical section cuts speed variance and keeps the section from breaking down. Gains are reported as travel time and variance, not as discharge flow [p. 106-107].
- Naples SUMO: jam-wave shrinking. Lower inflow into the wave while keeping moderate density in the VSL zone [p. 115]. This is a different mechanism from avoiding the capacity drop at a standing bottleneck.
- Part of the SUMO gain is likely by construction, since SUMO speed limits act through a speed-factor/hard-cap mechanism that the author himself criticises [p. 110], and the stochastic compliance model only partly repairs it.

Would it survive a realistic 5-8 % capacity drop?
- Honestly unknown. The chapters never state their plant's capacity drop, so the size of the gain cannot be linked to it.
- For a standing bottleneck, the upper bound on what drop-avoidance can give is of the order of the drop itself (5-8 % of discharge during the queue), before any loss from metering the inflow. A 19-26 % time-loss or travel-time cut would then have to come from something other than recovering discharge flow (for example jam-wave dissipation, a transient demand surge, or model artefacts).
- Moving-jam control may still work because the waves' own dynamics differ, but the thesis does not test the capacity-drop size.

What is weak:
- One run per scenario, no seeds, no CI. RL training details missing. RL labelled DRL while the formulation is Q-learning.
- Different metrics rank the controllers differently (jam length versus time loss versus mean speed), and no-VSL has the highest mean speed.
- Field comparison is active versus inactive, observational, with no demand matching.
- The compliance model is fitted to a driving simulator, not to field behaviour.
- The deployment preference is asserted, not argued.

Innovative follow-up ideas (suggestions only):
1. Report RL against tuned proven controllers on a calibrated 5-8 % drop plant, and state an equivalence margin and the power to detect a null result. The null result is itself publishable and addresses a gap in these two theses.
2. Use the rule-based logic's multi-level consistency checks (30 km/h steps, lane order, minimum limits) as a safety shield around RL actions, or let RL tune only its parameters (`pjsmalt` 1.6, thresholds, critical density), in line with Mansouryar's own hybrid suggestion [p. 126].
3. Put the gain target on what a drop-avoidance controller cannot do: incidents or work zones with 30 %+ capacity loss, reliability/variance, harsh braking and conflicts, jam-wave suppression.
4. Train over randomised compliance and capacity-drop sizes (domain randomisation), and test on held-out values, using Mansouryar's lognormal compliance model as one axis.

---

# B) Zhou, "A Q-learning based integrated VSL and hard shoulder running control to reduce travel time at freeway bottleneck" (MSc, Univ. of Maryland, 2019, advisor L. Zhang)

## B1. Problem, network, demand, incidents

- I-270 southbound near the I-270 spur / I-495 beltway, Maryland. The study bottleneck is the diverging point where the five-lane mainline splits into two three-lane carriageways [p. 54].
- ATM segment: 5.5 miles, with 4.25 miles upstream of the diverge in the VSL segment. Of this, 0.75 mile next to the diverge is an uncontrolled acceleration section. The VSL section proper is 3.5 miles, split into 7 parts [p. 62-63]. A 1-mile hard-shoulder section sits at the bottleneck, with a 0.25-mile buffer [p. 63].
- Demand: from a calibrated regional model (MWCOG 2015 base year). Mainline volume reaches "7,500 vehicles/hour", about half toward the spur; spur demand about "1600 vehicles/hour/lane" for 2.5 hours [p. 68]. Six driver classes (SOV, HOV2, HOV3, APV, COM, TRK) [p. 65].
- Field context: free-flow corridor travel time about 29 minutes, rising to 67 (AM) and 52 (PM) minutes; speeds fall from 65 to 30 mph, as low as 10 mph [p. 53].
- Incidents: the thesis cites "more than 150 incidents" in the 2016 peak period [p. 54], but the simulated scenario is the recurrent peak ("the mapping of the actual traffic condition" [p. 68]). Incidents are not simulated (not stated as simulated).

## B2. Simulator, parameters, capacity drop

- DTALite, mesoscopic, "Newell's cumulative flow count model" [p. 56, 64]. Link-based queueing, no individual car following.
- Supply parameters [p. 64]: free-flow speed 65 mph; freeway lane capacity 2000 veh/mile/lane (as printed); wave speed 12 mph; critical density 30.7 veh/mi/lane; jam density 180; "Percentage of dropped capacity (%) 10"; discharge after drop 1800 (as printed).
- Capacity drop: modelled as a fixed 10 % parameter [p. 64]. The literature statement in the thesis is "The capacity decreases by about 20% at a bottleneck" [p. 33]. So the plant's 10 % is half the literature figure the author quotes. Calibration or validation of the drop against field data: not stated.
- Calibration and validation [p. 59-62]:
  - 179 sensors (RITIS and SHA I-TMS, 2015), OD estimation plus manual demand adjustment.
  - Supply parameters (lane capacity, jam density) adjusted [p. 61].
  - WMSE for volume 32.74 % -> 7.91 %; for corridor travel time 40 % -> 10 % [p. 62].
  - Travel time reference: RITIS 15-minute data [p. 60-61].
- Simulation period: 6:00-9:00, with warm-up 4:00-6:00 and cool-down 9:00-11:00 [p. 64]. The text elsewhere says 5:00-11:00 with a two-hour warm-up [p. 63].
- Driver compliance: assumed 100 %: "it is assumed that all drivers would fully obey the posted speed limits" [p. 78]. Detector data assumed perfect [p. 66, 78].
- Speed-limit mechanism in the model: lower limit lowers the maximum flow and raises critical density (Figure 3-1(c) and text) [p. 35]. DTALite represents VSL "using lane capacity and dynamic speed control" [p. 57].

## B3. Control method (Q-learning, tabular)

- Algorithm: tabular Q-learning with epsilon-greedy, Q-table updated by the standard rule (eq. 8) [p. 40-42]. Described as "model-free".
- State (3 discretised variables) [p. 45-46]: network corridor queue delay (5 levels, Table 3-1), queue delay reduction (Table 3-2) and density of the VSL segment (7 levels, Table 3-3). Text says 13 levels for queue-delay reduction, but Table 3-2 lists 7 levels (-3..3) [p. 45-46]. Posted speed limits are also said to be in the state [p. 45].
- Actions [p. 47-48]:
  - Speed limits are multiples of 5, bounded, no large jumps; limits are changed jointly for the VSL segments.
  - VSL: increase or decrease by 5 or 10 mph, or by different amounts.
  - HSR: activate or deactivate the shoulder lane.
  - Control period 5 or 10 minutes [p. 47].
- Reward [p. 49, 51]:
  - eq. 13: `R = -alpha (Q_k - Q_{k-1}) |Q_k - Q_{k-1}| - beta Q_bottleneck`. The first term is the signed-square change in cumulated network queue delay; the second is the bottleneck queue delay.
  - eq. 14: an HSR activation penalty `theta / [(Q)(Q_b)]^epsilon`, so the shoulder opens only when both corridor and bottleneck queue delay are high [p. 51].
- Parameters (Table 3-4) [p. 53]: learning iterations 150-500; learning rate 0.005; "reward decay" 0.99 and "discount factor" 0.9 both listed; start epsilon 0.9. Table 3-8 [p. 64] says 120 learning iterations with 20 assignments per iteration.
- The thesis argues the contribution is the queue-delay-based state and reward, the VSL+HSR coordination, and "the first paper analyzing RL-based ATM control with DTA model" (to the author's best knowledge) [p. 19].

## B4. Baselines and tuning

- No control (calibrated base case); QL-based VSL alone; QL-based HSR alone (listed as a scenario [p. 66], but no results given for it, not stated); QL VSL+HSR; one feedback-based VSL benchmark "discussed in a research paper of Zhang et al [83]" [p. 68].
- Tuning of the feedback VSL: not stated. No fixed (static) speed limit, no ALINEA or ramp metering, no tuned reference, no other learning method.
- The QL agent's hyperparameters were chosen by the author ("after multiple tests" for the penalty function [p. 51], and "after several experiments" for the 1-minute data interval [p. 66]). No search protocol is given.

## B5. Evaluation

- MOEs [p. 67-68]: corridor travel time on the ATM segment, bottleneck speed and density, system travel time, ramp queue delay.
- One simulated morning peak per scenario. Number of runs, seeds, repeated trials, confidence intervals and significance tests: not stated.
- Training versus testing: not stated for the main results. The only held-out evaluation is "By applying random traffic flow in the network, the model set correctly captured 90% (23 of 25 tests) of the congestion scenarios and provided optimal controls immediately" [p. 75]. What "correctly captured" and "optimal" mean is not defined.
- The same DTA scenario seems to be used for training and reporting (not stated otherwise). Training is separate from evaluation only in the sense of offline learning.
- The conclusion states five scenarios (5-min VSL, 10-min VSL, 5-min coordinated, 10-min coordinated, no control) [p. 75]. The results tables show only one VSL and one VSL+HSR row, and which control period they use is not stated.

## B6. Headline results

Corridor travel time (Table 4-1) [p. 69]:

| Scenario | Corridor TT (min) | Change |
|---|---|---|
| No control | 21.91 | - |
| Single VSL (QL) | 18.40 | -15.98 % |
| VSL + HSR (QL) | 16.01 | -26.94 % |
| Feedback VSL | 20.09 | -8.20 % |

Bottleneck speed (Table 4-2) [p. 70]:

| Scenario | Speed (mph) | Change |
|---|---|---|
| No control | 16.20 | - |
| QL VSL | 23.57 | +45.59 % |
| QL VSL+HSR | 29.32 | +80.98 % |
| Feedback VSL | 23.02 | +42.10 % |

Table 4-3 [p. 73] (freeway mainline and ramps, change versus no control):
- QL-VSL: corridor TT -15.98 %, speed +13.97 %, density -10.83 %, queue delay -29.67 %; ramp travel time -5.17 %, ramp queue delay -14.9 %.
- QL-VSL+HSR: corridor TT -26.94 %, speed +24.77 %, queue delay -40.4 %; ramp travel time -13.79 %, ramp queue delay -31.61 %.
- Feedback VSL: corridor TT -8.20 %, queue delay -23.56 %, but ramp travel time +17.24 % and ramp queue delay +29.56 %. The author comments that performance "deteriorates significantly under the feedback-based ATM control, especially the queue delay on ramps" [p. 74].

Author's reading:
- QL-VSL and feedback VSL "differs in the trend but not markedly in the substance of average speed" [p. 71]. QL-VSL wins on corridor travel time [p. 72].
- HSR drives the largest step: bottleneck speed rises to about 40 mph between 8:00 and 8:30 when the shoulder is open, "attributes to the direct increase of roadway capacity" [p. 72].
- The text at p. 72 says VSL+HSR is "40% higher than VSL-alone". From Table 4-2, 29.32 / 23.57 = +24 % (my arithmetic).

Internal inconsistencies (reduce trust in the numbers):
- Feedback VSL travel-time gain: 8.20 % [p. 69, 73] versus 8.6 % [p. 76].
- Text p. 69: corridor travel time "increases to 18 minutes", while Table 4-1 gives 21.91 for no control.
- Text p. 72: HSR "helps it decrease from 30 minutes to 20 minutes", which does not match Table 4-1 (21.91 to 16.01).
- Simulation period (p. 63 versus p. 64 Table 3-8) and learning iterations (150-500 versus 120) differ.
- Table 4-3 mainline speeds (39.15 mph for no control) differ from Table 4-2 bottleneck speed (16.20 mph); they are different measures, but the thesis does not say so.

## B7. Field data and realism checks

- Calibrated on 2015 sensor volumes (179 sensors) and RITIS travel times [p. 59-62]. No VSL field data: the future work asks for "Traffic data from a VSL-equipped freeway" [p. 80].
- Realism gaps stated by the author: full compliance, perfect detector data [p. 78], simple VSL/HSR implementation rules that "may not be the optimal installation method" [p. 80], one model per scenario type [p. 77].
- Capacity drop not validated against bottleneck field data (not stated).

## B8. Stated limitations and future work [p. 77-80]

- Long training time; "Defects in any link will result in a great reduction of traffic control effects" [p. 77].
- VSL effects depend on bottleneck type (diverge, merge, ramps, lane count). "A series of models need to be built, trained and tested for different traffic conditions" [p. 77].
- Full-compliance assumption and perfect detector data [p. 78].
- Future work: more efficient training/parallelism, compliance distributions from behavioural models, modelling intermittent detector data, optimised VSL/HSR layout with microscopic models and VSL-equipped freeway data [p. 78-80].

## B9. INTERPRETATION (Zhou)

Where the gain comes from physically:
- HSR is the largest lever and it is a capacity addition: the thesis cites +22 % temporary capacity for a three-lane freeway [p. 36] and shows the biggest step when the shoulder opens [p. 72]. This is not drop avoidance and would not shrink if the drop is small.
- VSL-alone (-16 % corridor time): by the thesis's own theory it holds inflow below the post-drop capacity [p. 35]. The mechanism is built into DTALite (a lower limit lowers the maximum flow, assumed 100 % compliance). The result is therefore partly by construction.
- The size of the VSL gain is bounded by the drop. With the modelled drop at 10 % and a 3-hour congested period, a 16 % corridor time gain is plausible only because the network-level queue also spills over a long corridor, and because corridor travel time includes the whole queue's spill back [p. 69]. I cannot verify this from the text.

Would it survive a realistic 5-8 % drop?
- The VSL-only part would probably shrink, because the thesis's own plant has 10 % and the mechanism is drop avoidance. This is my estimate, not a result. The HSR part would likely survive because it adds capacity.
- Q-learning versus feedback: the thesis shows QL-VSL and feedback VSL with near-equal bottleneck speed (23.57 versus 23.02 mph) [p. 70], and the advantage lies in corridor travel time and ramp queues. That suggests the RL gain over a reasonable feedback law is modest on the bottleneck itself, and it is at risk of vanishing against a tuned feedback law (the baseline is not stated as tuned).

What is weak:
- Single run, no seeds, CIs or tests. Held-out testing is a single "23 of 25" statement with undefined success criterion.
- Baseline is untuned feedback VSL from the group's own earlier paper. No static or tuned baselines.
- State and reward use network-wide queue delay, which is available in the simulator but hard to measure in the field. That makes the "no human knowledge" advantage less practical.
- Several text-versus-table contradictions (above).
- Tabular Q-learning with discretised state is scenario specific; the author concedes one model per scenario [p. 77].
- The ramp effect is the one honest strength: the feedback VSL hurts ramps (+29.56 % queue delay) and QL does not [p. 73], which supports including ramp and origin queues in the metric.

Innovative follow-up ideas (suggestions only):
1. Evaluate with ramp and origin queues in the headline metric (Zhou's feedback-VSL ramp result shows why a mainline-only metric can be gamed).
2. Combine actuators with different mechanisms: one that adds capacity or spreads demand (lane-level limits, CAV speed commands, hard shoulder) and one that avoids the drop. Test which part survives when the drop is 5-8 %.
3. Replace tabular Q-learning with a policy trained across randomised drop size, demand and compliance, and report generalisation to unseen scenarios and a tuned feedback or static baseline with CIs.
4. Use measurable states only (loop-detector-like), and test the same policy under detector noise and dropout, which Zhou lists as future work [p. 78-79].

---

# Cross-thesis takeaways for the candidate (INTERPRETATION)

- Neither thesis states the capacity-drop size of a validated plant in a way that ties the reported gain to it. Zhou models 10 % (while quoting about 20 % from the literature) [p. 33, 64]; Mansouryar gives no figure.
- Neither reports multiple seeds or CIs for its RL comparison, so neither contradicts the candidate's null result.
- The more defensible RL gains in these texts are not in discharge flow: ramp queues (Zhou), harsh braking (Mansouryar, 0 versus 19 versus 45), and added capacity (Zhou's HSR). Mansouryar also concludes that the rule-based controller wins on time loss.
- Open space for a new contribution: a statistically careful comparison (tuned rule/feedback baselines, ramp-inclusive metric, seeds, CIs, equivalence margins) on a calibrated small-drop plant, and a hybrid in which RL adapts or schedules a proven controller under safety constraints.
