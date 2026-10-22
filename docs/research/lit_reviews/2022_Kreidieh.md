# Review: A. R. Kreidieh, UC Berkeley PhD 2022 (mixed-autonomy traffic, RL / imitation learning)

Source: `text/2022_Kreidieh_Berkeley_PhD.txt` (full text read; Ch. 2 only the ring-road example).
Page convention: **[p. N] = printed page number** in the thesis header (PDF page = N + 7). Quotes are verbatim (<= 25 words).
Reader note: not a freeway-control thesis in the ALINEA/VSL sense. Actuators are **CAV accelerations or CAV speed commands**, objectives are stop-and-go damping and energy. Only one traffic-control experiment is a real **lane-drop bottleneck** (Flow "Bottleneck" benchmark, Sec. 3.3, in the thesis only as a summary table). No ramp metering or VSL baseline is evaluated anywhere. The only ramp-metering mention is as an analogy [p. 108], [p. 65].

Thesis structure: Ch. 3 Flow + benchmarks; Ch. 4 hierarchical RL (CHER); Ch. 5 and 6 imitation learning (DAgger) of a global-sensing expert; Ch. 7 TRPO ring-to-merge transfer; Ch. 8 conclusion. Ch. 5 and 6 are **imitation learning, not RL**.

---

## A. Chapter 3.2.2: Mixed-autonomy ring road (RL, TRPO)

1. **Problem/network.** Single-lane ring, one AV among human drivers; ring 260 m, N = 22 in the Ch. 2 example [p. 10]. Figure 3.5 uses a "circumference of 260 m" [p. 24]. Demand = closed system (no inflow). No incidents. Densities 0.08-0.10 veh/m evaluated [p. 26].
2. **Simulator/models.** Flow on SUMO [p. 17-24]. IDM with exogenous noise epsilon [p. 10]. IDM parameters for this experiment: **not stated** (Table 5.1 later gives v0=30, T=1, a=1.3, b=2, delta=4, s0=2, eps~N(0,0.3) for Ch. 5 only [p. 63]). No capacity drop (ring has no bottleneck); the instability is string instability [p. 19]. No calibration or validation against field data is stated for this experiment (the Sugiyama ring experiment is cited as qualitative support [p. 20]).
3. **RL.** TRPO, linear feature baseline, gamma = 0.999, step size 0.01; "three Intel i7-6600U CPU ... six hours. A total of six million samples" [p. 25]. State = local (v_AV, v_lead, headway) [p. 10]; action = bounded acceleration; reward = sum of speeds + c1*|a| [p. 11]; single agent, penetration 1 AV of 22 (about 4.5 %). Seeds: not stated.
4. **Baselines.** Human-driven (IDM) and hand-crafted FollowerStopper and a "PI with saturation" law (from Stern et al., ref [155]) [p. 24-26]. Tuning: the thesis says only that the hand-crafted controllers "only dissipate stop-and-go traffic at densities less than or equal to their calibration density" [p. 25]. No tuning procedure for the baselines is given.
5. **Evaluation.** Fig. 3.6: "averaged over ten runs at each evaluated density" [p. 26]; no CIs or tests; train vs zero-shot densities are distinguished ("zero-shot manner") [p. 25].
6. **Result.** Qualitative: the learned policy "match[es] the optimal uniform-flow conditions very closely for all explored densities" [p. 25]. No numbers in text. RL leaves larger gaps than FollowerStopper (reward-engineering side effect) [p. 25].
7. **Robustness.** Only the zero-shot density test; no noise, compliance or field test in this section.
8. **Limitations (thesis).** The gap-forming behavior "motivates the work outlined in Chapter 4" [p. 25]; delicate reward design.

## B. Chapter 3.3: Flow benchmarks, incl. the **Bottleneck** benchmark (RL: ARS, ES, TRPO, PPO)

This is the part relevant to the candidate. The thesis gives only a summary; details are deferred to refs [184, 185] (not in this file).

1. **Problem/network.** "idealized representation of the lane-reduction bottleneck witnessed on Oakland-San Francisco Bay Bridge. ... lanes are instead reduced from 4N to 2N to N" [p. 29]. N is a scaling factor (Bottleneck 0/1/2 = increasing size; Bottleneck 2 about double the throughput scale, see Table 3.1 [p. 31]). Goal: "restrict or otherwise modify the flow ... to avoid the triggering of a capacity drop" [p. 29]. Edge length, inflow/demand profile, incidents: **not stated** in this thesis. Merge benchmark (Fig 3.7c) and figure-eight, grid are other benchmarks [p. 26-29].
2. **Simulator/models.** SUMO via Flow [p. 21]. Car-following/lane-change parameters for the bottleneck benchmark: **not stated**. Capacity drop is said to exist ("This system exhibits the phenomenon known as capacity drop [138], where the throughput ... experiences a sharp drop in magnitude once the inflow ... surpasses a critical value" [p. 29]). **Its size is not stated, and calibration/validation against field data is not stated.**
3. **RL formulation.**
   - Algorithms: ARS (linear), ES (MLP 100-50-25, tanh), TRPO, PPO (256,256 value net) [p. 29-30].
   - State: per-lane, per-edge-segment mean position/speed of humans and of CAVs, plus outflow (veh/h) over the last 5 s [p. 29].
   - Action: "the RL action shifts the maximum speed of all the CAVs in the segment from their current value" per edge-segment and lane [p. 29] (a per-segment, per-lane speed-limit-like command, applied via CAVs only).
   - Reward: outflow in the last 5 s normalised by number of lanes and 500 [p. 29].
   - Single centralised agent.
   - Penetration rate: **not stated** in this thesis.
   - Budget: "500 training iterations", iteration = "50 rollouts/trajectories" [p. 30-31]. Seed count: not stated numerically ("did not have a complete number of seeds" is the only hint) [p. 31].
4. **Baselines.** "Human" (no control) only. No fixed speed limit, no ALINEA/PI-ALINEA, no feedback, no MPC, no tuned heuristic. (Compared across RL algorithms only.)
5. **Evaluation.** Table 3.1: "Average optimal return and standard deviation ... after 500 training iterations; average is over 40 rollouts" [p. 31]. Plus/minus values are standard deviations, not CIs; no paired tests. Train and test are the same environment; no generalisation test in this section.
6. **Headline numbers (Table 3.1 [p. 31]; percentages are MY arithmetic on the table, INTERPRETATION-level calculation):**

| Benchmark | Human | ARS | ES | TRPO | PPO |
|---|---|---|---|---|---|
| Bottleneck 0 | 1023 +/- 263 | 1265 +/- 263 (+24 %) | 1360 +/- 200 (+33 %) | 1298 +/- 268 (+27 %) | 1167 +/- 264 (+14 %) |
| Bottleneck 1 | 1135 +/- 319 | 1350 +/- 162 (+19 %) | 1378 +/- 192 (+21 %) | 1375 +/- 61 (+21 %) | 1258 +/- 200 (+11 %) |
| Bottleneck 2 | 1889 +/- 252 | 2284 +/- 231 (+21 %) | 2324 +/- 264 (+23 %) | 2131 +/- 190 (+13 %) | 2143 +/- 208 (+13 %) |

   Thesis commentary: in the small bottleneck policies "merge smoothly through lane reductions", but in larger ones "they fail to produce similar gains ... (e.g bottleneck2, for which the optimal reward should, in theory, be double ...)" [p. 31]. Also "gradient-based methods in particular fail to meaningfully update their behaviors after the first few iterations, as evidenced by the flat training curves within the large grid and bottleneck benchmarks" [p. 31]. The thesis does not claim these are optimal: "it remains to characterize whether the optimal solution has been achieved" [p. 30].
7. **Robustness/realism.** None in this section.
8. **Limitations (thesis).** Summary list [p. 31-32]: policies struggle in partially observable / high-dimensional tasks; learning "produc[es] little or no gains after the first few iterations ... despite performing on par with human models"; "policies learned in larger scale problems often underperform those produced in analogous simpler tasks". These motivate Chs. 4-7.

## C. Chapter 4: CHER, cooperative hierarchical RL (two traffic tasks + ant tasks)

1. **Network.** (a) Ring road: 22 vehicles, "variable length (220-270m)", one vehicle replaced by learner [p. 55]. (b) "Highway": open network, "downstream traffic instabilities ... simulated via a slower-moving downstream segment produce congestion in the form of stop-and-go waves"; centralised policy over all AVs [p. 55]. Geometry (length, lanes), demand, penetration for Highway: **not stated**. No incidents.
2. **Simulator/models.** Flow/SUMO; warm-up 1500 steps, horizon 1500 steps; step 0.2 s (ring) and 0.4 s (highway) [p. 55-56]. IDM/lane-change parameters: not stated. No capacity drop, no calibration.
3. **RL.** TD3-based hierarchical (manager/worker), gamma 0.99, (256,256) nets, replay 200,000, etc. [p. 56]. Goals = desired AV speeds (0-10 m/s ring, 0-20 m/s highway) [p. 57]. Ring reward: r = (0.1/n_v)*sum v_i^2 ("sparser rewards") [p. 55]. Budget: Fig. 4.5 "averaged across 10 runs" [p. 44]; x-axis in the extracted figure text appears to run to about 3 x 10^6 steps (read from figure axis labels, uncertain) [p. 44].
4. **Baselines.** Flat TD3, plain HRL, HIRO, HAC [p. 44]. CHER's lambda tuned: "hyperparameter search for lambda values between [0.005, 0.01], and report the best performing policy" and delta in {25,50,75 %} "report the best performing policy" [p. 56]. Baseline hyperparameters: "similar" for TD3 [p. 44]; no equal-search statement for HIRO/HAC. So the proposed method gets a (small) tuning search the thesis does not claim for the baselines. No traffic-engineering baselines (no ramp meter, no VSL).
5. **Evaluation.** 10 runs per curve, no CIs or tests stated in the text; train/test not separated (training curves). Transfer test only for ant tasks.
6. **Results.** Traffic: qualitative only ("dampens the frequency and severity of stop-and-go traffic ... and improves vehicle throughput" [p. 45]). No numeric throughput gains in text. "within the Ant Maze task, no noticeable benefit is witnessed from CHER" [p. 45].
7. **Robustness.** None for traffic tasks.
8. **Limitations/future.** Future work only on multi-level hierarchies, option-critic, intrinsic motivation [p. 48].

## D. Chapter 5: Imitating a non-local expert on I-210 (DAgger; imitation learning)

1. **Network.** "1-mile section of the I-210 network in Los Angeles" [p. 65], multi-lane. Congestion is **synthetic**: high inflow from the left, outflow restricted "via a reduced speed limit within the rightmost 100 m" [p. 65]. Inflow sampled from [1900, 2300] veh/h/lane (step 50); downstream speed limit [5, 7] m/s [p. 67]. No incidents.
2. **Simulator/models.** Flow/SUMO, 0.4 s step, warm start 3600 s then 600 s [p. 67]. IDM: v0=30, T=1, a=1.3, b=2.0, delta=4, s0=2, eps~N(0,0.3) [p. 63]. Lane-change frequency is varied in robustness tests [p. 71]; base value not stated. **No capacity drop is modelled or claimed: congestion is imposed by a speed-limit patch.** No calibration/validation against field data stated.
3. **Formulation.** Expert = FollowerStopper-type controller with desired speed U = downstream speed (needs non-local info) plus a gap-recovery term c=0.001 [p. 65-67]. Learner: MLP (32,32,32), DAgger, 30k initial samples (20 rollouts) + 7.5k per epoch x 100 epochs = 750k samples [p. 68]. Observation = local (v, headway, v_lead) with N=5 past states at dt=2 s [p. 66]. Penetration 5 % [p. 68]. Single shared policy. Seeds: "5 seeds" [p. 68].
4. **Baselines.** Human-driven "baseline (no control)", the expert, and imitated policy without temporal info [p. 69-70]. No ramp-metering/VSL baseline, no RL baseline. Expert's parameters taken from prior work; no tuning described.
5. **Evaluation.** Energy (mpg, RAV4 fitted model), acceleration magnitude, outflow (veh/h/lane) [p. 69]. Mean +/- values in Fig. 5.5; no CIs or tests. Robustness tests below.
6. **Results.** "34.5 mpg and 34.4 mpg ... (a 15% improvement over the baseline value of 29.6 mpg)", acceleration "0.242 ... 0.240 m/s2 ... (a 60% reduction over the baseline value of 0.604 m/s2)", throughput "very minor reductions ... of around 2%" [p. 70]. Throughput did NOT increase.
7. **Robustness.** Penetration 2.5-10 % and IDM max-acceleration (0.8-1.6) and lane-change-frequency variations; imitated policy "continuing to outperform the baseline in all settings" (caption) [p. 72]; a gap to the expert opens for large human-model changes [p. 71]. Fig. 5.5 shows baseline mpg values varying roughly 24-30 mpg across IDM-a settings (read from the figure table text). No sensor noise, no field test; real-data validation listed as "ongoing work" [p. 72-73].
8. **Limitations/future.** "we aim to validate the performance of this control strategy on trajectories of human driving provided by the real world" [p. 72].

## E. Chapter 6: Expert relabeling, bottleneck and I-24 shockwave (DAgger; imitation learning)

1. **Network.** Single-lane straight track. (i) "Capacity-restricted bottleneck": capacity restriction beyond x_BN = 12 km imposed "by raising the desired time headway T" of human drivers [p. 82]. (ii) Shockwave: leader follows recorded I-24 (Nashville) trajectories, 10 trajectories (7 light/moderate, 3 heavy) [p. 83, 90]. Platoon: subplatoons of 25 vehicles (1 AV + 24 humans), 4 % penetration; shockwave: 250 vehicles, 10 AVs [p. 83]. Demand: platoons with uniform initial spacing, no inflow profile. No incidents.
2. **Models.** IDM (Table 6.1 [p. 84]): bottleneck v0=35, T=1.24 s (and T in [1.4, 1.8] in the tests [p. 90]), a=1.3, b=2.0, delta=4, s0=2, eps~N(0,0.3); trajectory scenario v0=45, T=1. Step 0.1 s, horizon 3600 s [p. 83]. **Capacity drop is not modelled as a drop**: the bottleneck is a static capacity reduction via larger T. The thesis states higher T "restrict[s] the number of vehicles that can reside in a freeway segment, thereby simulating the effects capacity drops" [p. 78]. Not calibrated/validated against field data for the bottleneck; the shockwave scenario uses real I-24 leader trajectories and INRIX 5-min segment speeds [p. 85].
3. **Formulation.** Expert (Eq. 6.5): speed command = v_des + kp(h - h_des) + kd(v_l - v) clipped by a safety filter, v_des from a 3000 m windowed average of segment speeds; kp=2.0, kd=0.5, h_des=2.0 s [p. 79-84]. DAgger, MLP (32,32,32), 10 initial simulations + 1 per update for 50 iterations [p. 85]. Single shared policy; seeds: not stated.
4. **Baselines.** Human-driven (all IDM), expert (global sensing), imitation (local sensing) [p. 90]. No tuned conventional controller and no RL baseline.
5. **Evaluation.** Energy (mpg), throughput (veh/h at 1 km -> 9 km for bottleneck; distance travelled for shockwave), headway proximity [p. 89-90]. Bottleneck: one run per T value apparently (no repeats or CIs stated). Shockwave: "average across 10 runs for each leading trajectory" [p. 87]. No statistical tests.
6. **Results.** Bottleneck (Table 6.3 [p. 86]): mpg gain +36.9 % at T=1.4 down to +4.6 % at T=1.8 (global sensing). **Throughput change is small:** e.g. T=1.4 human 1858 -> 1862 vs global 1917 -> 1874; T=1.7 human 1512 -> 1500 vs 1530 -> 1500 (veh/h). Shockwave (Table 6.4 [p. 87]): overall mean +16.57 % (global) and +14.50 % (local) total mpg; distance travelled -0.64 % / -1.67 %. Text: "equivalent level of throughput" [p. 90].
7. **Robustness.** Severity sweep (T 1.4-1.8; 10 real trajectories). Safety filter is part of both expert and learner [p. 79]. No sensor noise on speed estimates in bottleneck (segment speeds read directly from the simulator) [p. 85]; INRIX data adds realism only in the shockwave case. No field test. Imitated policy "tend[s] to be more conservative with larger gaps" [p. 90].
8. **Limitations/future.** Chapter summary does not list limits beyond its text; Ch. 8 sim-to-real, data needs [p. 113-114].

## F. Chapter 7: Dissipating stop-and-go waves, ring to on-ramp merge (RL, TRPO)

1. **Network.** Open single-lane highway, L_h = 700 m, q_h = 2000 veh/h, on-ramp q_m = 100 veh/h; "designed to be a fixed source of perturbations rather than a realistic on-ramp inflow" [p. 104]. Closed ring 1400 m, 50 vehicles with a 700 m controlled region and periodic perturbations as training/transfer source [p. 104, 106]. No incidents.
2. **Models.** SUMO via Flow, step 0.2 s, 3600 s, agent step 1 s with 5 repeated steps [p. 106]. IDM "given parameters calibrated to model highway traffic [178]", noise N(0,0.2) "calibrated to match findings in [176]" [p. 105]; numeric IDM parameters: not stated here. Capacity drop: not modelled as such; "dropping the throughput from a free-flow value of 2000 veh/hr to an observed value of 1604 veh/hr" (a **-20 %** wave-induced loss, in a simulation whose perturbation is artificial) [p. 108]. Validation vs field data: not stated.
3. **RL.** TRPO, linear baseline, gamma 0.999, step 0.01, MLP (32,32,32) tanh [p. 106]. Single centralised agent controlling all CAVs, every (100/p)-th vehicle is an AV, penetration 0-10 % [p. 105, 107]. Obs: speeds/headways of lead/lag vehicles + ego speed; action: bounded accelerations, zero-padded [p. 105]. Reward: ||v_des|| - ||v_des - v|| - alpha * sum max(h_max - h_i, 0), v_des=25 m/s, h_max=1 s, alpha=0.1 [p. 105-106]. Seeds: "five seeds" for training; results "averaged over 10 simulations" [p. 107]. Training budget in samples: not stated.
4. **Baselines.** Human-driven, 0 % penetration. No other controller (no ramp metering, no VSL, no FollowerStopper in this chapter). Transfer vs from-scratch RL compared in Fig 7.5 [p. 108].
5. **Evaluation.** Throughput, mean speed, wave dissipation, spatio-temporal plots; no CIs/tests. Train = test network (same geometry); transfer ring -> open is the only generalisation test.
6. **Results.** "13% increase in throughput as the portion of automated vehicles ... increases from 0% to 10%, with vehicles on average moving at almost twice the speed" [p. 107]. "virtually eliminated at penetration rates of 10%" [p. 107]; "near complete wave dissipation with only 10% autonomous penetration" [p. 110]. Learned behavior resembles ramp metering: AVs slow near the network start, "maintaining the density ... approximately 0.36 veh/m" [p. 108]. Ring-road warm start gives a head start in training (Fig 7.5) [p. 109].
7. **Robustness.** Only penetration sweep (0-10 %). Not stated: noise, compliance, sensing errors, field data.
8. **Limitations/future.** Hope to solve "much larger and numerically more difficult highway network tasks from primitives learned on ring roads and single lane merges" [p. 110].

## G. Thesis-level limitations / future work (Ch. 8)

- Honest scope statement: "learning-based solutions ... are viable ... However, similar algorithms often fail when applied to larger scale tasks" [p. 112].
- Future: compositional/hierarchical skill libraries (merge vs lane-reduction bottleneck policies combined via options) [p. 113]; better human-driving models and "data on human driving responses ... from dense traffic settings" [p. 113]; sim-to-real: noise injection, adversarial learning, domain randomisation "are more likely needed" [p. 114].
- The thesis itself says "sim-to-real gap ... invalidate certain aspects of the learned response" [p. 113].
- Not stated anywhere: statistical testing, confidence intervals, tuned classical-control baselines, capacity-drop magnitude or calibration, any field test.

---

## H. INTERPRETATION (mine, not the thesis's)

### (a) Where does the gain physically come from; would it survive a 2-11 % capacity drop?

- **Bottleneck benchmark (B).** +11 to +33 % on "return" (outflow-based) in Table 3.1 [p. 31], relative to unmanaged human driving only. The thesis states the capacity drop exists but gives no size. INTERPRETATION: the gain can only be as large as the capacity lost; since the candidate found Flow's IDM Bay Bridge plant has a 40-50 % drop, gains of +20-30 % are plausible as "recovering part of a huge drop". On a plant with a 5-8 % drop the same mechanism has at most ~5-8 % of headroom, so these numbers would not transfer. This is a hypothesis, I did not verify the drop size in Flow (the thesis does not report it). The thesis's own remark that Bottleneck 2 gains are not double those of Bottleneck 0/1 hints the policy is far from the ceiling, but no ceiling is computed.
- **Ch. 5/6 (energy).** Gains come from **smoothing** (fewer accelerations, fewer stop-and-go waves): mpg +15 % and acceleration -60 % with throughput about -2 % (Ch. 5 [p. 70]); Ch. 6 bottleneck throughput change is within ~0-3 % while mpg moves +5 % to +37 % [p. 86]. INTERPRETATION: this gain is largely independent of capacity drop and would survive a small drop, but it is an **energy/comfort** gain, not a delay/throughput gain, so it does not answer the candidate's 10 % delay bar. The mpg gain is largest at T = 1.4 s (+36.9 %, human throughput 1858 veh/h, the least restrictive setting) and smallest at T = 1.8 s (+4.6 %, human throughput 1458 veh/h) [p. 86]; so in this scenario the benefit shrinks as the imposed capacity restriction gets stronger. INTERPRETATION only; one run per T is apparently reported.
- **Ch. 7.** The congestion is created by an artificial periodic perturbation (merge inflow 100 veh/h "designed to be a fixed source of perturbations") [p. 104]. The 13 % throughput gain [p. 107] is recovery of a wave-induced loss (2000 -> 1604 veh/h, -20 % [p. 108]) in a 700 m single-lane road. INTERPRETATION: again a large, simulator-generated loss; plausibly collapses if the loss is only a few percent.
- **Ch. 3.2.2 ring.** Gain exists because IDM is string-unstable by construction; real traffic evidence is only the Sugiyama experiment.

### (b) What is weak in the evaluation

1. Baselines: only "human/no control" (and FollowerStopper / PI-saturation on the ring); **no ALINEA/PI-ALINEA, no VSL, no tuned feedback, no MPC** anywhere. Baseline tuning is not described.
2. Statistics: mean +/- SD (Table 3.1) or means of 5-10 runs; no paired seeds, no CIs, no tests. In Table 3.1 the SDs (e.g. 263 on a 1023 mean) overlap the gaps between "human" and RL for several cells (e.g. PPO Bottleneck 0, 1, 2 differ by 0.5-0.6 SD).
3. Train = test (same network/seeds distribution) for the bottleneck benchmark; no held-out demand.
4. Capacity drop size and car-following/lane-change parameters of the bottleneck benchmark are not reported in the thesis; no calibration to field data for any traffic experiment (Ch. 6 uses real leader trajectories and INRIX speeds but IDM is not calibrated to them as far as stated).
5. Congestion is **imposed by construction** (speed-limit patch Ch. 5, larger T Ch. 6, artificial periodic perturbation Ch. 7), so the benefit is partly an artefact of the scenario design.
6. Proposed method (CHER) gets a lambda/delta search with "report the best performing policy"; baseline tuning budget not stated [p. 56].
7. Headline metrics are energy (fitted RAV4 model) and a speed-based reward, not door-to-door delay with queues; the thesis notes throughput can be traded (Ch. 6 uses distance travelled as proxy) [p. 89].
8. Observations/actuation unrealistically clean: segment speeds read directly from the simulator in the bottleneck scenario [p. 85]; no detection noise, latency or compliance modelling.

### (c) Possible innovative follow-ups given the candidate's finding (5-8 % realistic drop, metering does not beat no control by 10 %)

(These are my suggestions; none is in the thesis.)
1. **Report the capacity drop and "headroom" explicitly as a benchmark axis.** Kreidieh's bottleneck table has no drop size; a drop-size sweep (2-50 %) with tuned ALINEA/PI-ALINEA/VSL baselines would show where learned CAV/VSL control has headroom. This is a methodological contribution the thesis lacks.
2. **Imitate-then-refine against a tuned classical teacher** (Ch. 5/6 recipe): use an informed, non-local controller (global sensing, oracle drop-onset knowledge) as expert, distil to local observations, and report the gap between expert and imitation as the cost of information, evaluated on delay/throughput rather than energy. The thesis demonstrates the distillation but only on energy and with IDM-patch bottlenecks.
3. **Target the benefit that survives small drops**: smoothing/safety/energy co-benefits (Ch. 5/6 show +10-35 % mpg with throughput change ~0-3 %). A multi-objective claim (delay no worse, energy and acceleration variance clearly better) needs no 10 % delay gain.
4. **Robustness to the drop magnitude and driver heterogeneity as the learning target** (domain randomisation over drop size and IDM/lane-change parameters, as the thesis itself suggests in future work [p. 114]), then report the operating map where RL wins/ties/loses vs tuned controllers.
5. **Hierarchy/skill composition** (thesis future work [p. 113]): combine metering/VSL "skills" per segment type; no one has to beat a tuned controller everywhere.
