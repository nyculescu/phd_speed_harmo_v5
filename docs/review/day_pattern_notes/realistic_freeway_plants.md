# Realistic simulated freeway bottleneck plants (on-ramp merge, lane drop, weaving) for full-day ramp-metering / VSL testing

Notes compiled 2026-10-04 by a research sub-agent. Reading status is marked on every source:
- **[read: …]** = the named part was read from the primary text (PDF/HTML extracted and searched); anything else in that source was not read.
- **[VERIFY]** = only the abstract, metadata, a search-engine snippet or an automated page summary was seen; treat the claim as unconfirmed.
- **[SAGE]** = published by SAGE (Transportation Research Record); the author cannot access these.
- Automated page summaries were found to be unreliable for PDFs (one summary of Hickert et al. 2026 invented content about capacity drop that is not in the paper), so claims below rely on text extracted locally wherever possible.

---

## Q1. Which SUMO car-following / lane-change settings reproduce capacity drop and realistic queue discharge at freeway merges, lane drops and weaves? Known SUMO merge issues

### Takeaway
I found **no published SUMO study that calibrates a freeway merge or lane drop to an empirical capacity drop *and* an empirical queue-discharge rate at the same time.** The closest evidence is a 2023 benchmark reporting that SUMO in its default configuration shows no capacity drop at an extended merge, while Aimsun and SymuVia do [VERIFY]. A 2026 SUMO-conference "best practice" recipe for ramp metering relies on heterogeneous driver classes and assertive ramp vehicles, but it reports no realism validation, and its published mainline vTypes use `tau` = 8.5–10 s. SUMO maintainers' advice points the same way: realism has to come from stochasticity (Krauss `sigma` or EIDM rather than IDM), driver heterogeneity, calibrated `lcCooperative`/`lcAssertive`, longer acceleration lanes, and correct merge geometry and connections.

### Cited Findings

**Evidence that default SUMO lacks capacity drop at merges**
- In a benchmark of three European microsimulators at a point diverge and an extended merge, the authors conclude that the tools reproduce elementary merge/diverge behaviour, "however, their default configuration does not, entirely or partially, reproduce the traffic conditions induced by insertions and desertions as predicted by the analytical models" (Boukhellouf, Buisson & Chiabaut 2023, *European Transport Research Review* 15, art. 12, abstract) [VERIFY] — [OpenAlex record / DOI](https://doi.org/10.1186/s12544-023-00586-1).
- A search-engine snippet of the same paper's full text states: "A capacity drop is identified in SymuVia and Aimsun but not in SUMO, with the maximum capacity drop in Aimsun around 17%, higher than SymuVia's 7%, consistent with on-field observations between 5 and 30%." [VERIFY: snippet only. The full text (CC-BY) was blocked by bot protection at Springer and HAL. SUMO version, models and parameters used are unknown to me.] — [Springer](https://link.springer.com/article/10.1186/s12544-023-00586-1); open copy listed at [HAL hal-04715667](https://hal.science/hal-04715667v1/file/BoukhelloufBuissonChiabaut_ETRR_2023.pdf).
- A search snippet of a 2025 ANNSIM paper ("Discrepancy of Lane Flow Distribution and Lane-Wise Speed Distribution When Simulating Lane-Drop Bottleneck in SUMO: A Comparison of Two Car-Following Models") says the Krauss model "overestimates the bottleneck capacity by 46% and cannot replicate the lane flow distribution effectively". [VERIFY: abstract page returned HTTP 403; authors, second model and data not confirmed] — [ACM DL](https://dl.acm.org/doi/abs/10.22360/ANNSIM.2025.ANSS.43).

**Maintainer statements (SUMO GitHub)**
- On a merge bottleneck, a SUMO maintainer (namdre) confirmed that `sigma=0.5` or `lcCooperative=0` can cause early congestion. "The extent of cooperation and the aggressiveness of merging (lcAssertive) may need to be calibrated to fit your local ground truth", and runs are deterministic unless `--random` is set (issue #16198, 2025) — [GitHub #16198](https://github.com/eclipse-sumo/sumo/issues/16198).
- In the same thread a second maintainer (robertalms) recalls known gaps for disparate lane speeds at highway ramps: lane-change aggressiveness when stuck in congested lanes, cooperativeness of fast-lane vehicles, and lower `speedFactor` on adjacent lanes in real jams. namdre also notes that the **default lane-change model is LC2013**; SL2015 is used only when `--lateral-resolution` activates the sublane model — [GitHub #16198](https://github.com/eclipse-sumo/sumo/issues/16198).
- For a single-lane merge showing no downstream speed drop, the maintainer said the vType "is eliminating two important sources that would create a density→reducedSpeed relationship": IDM "has no random speed fluctuations", so "consider using Krauss or EIDM instead"; and a fixed `maxSpeed` narrows the desired-speed distribution (issue #16659, 2025) — [GitHub #16659](https://github.com/eclipse-sumo/sumo/issues/16659).
- For a 4→3→2 lane drop with unrealistic lane use, the maintainer says custom connections were invalid. Either leave the dropped lane without a connection (forced lane change, "this lane will be then at a disadvantage") or make the junction type `zipper` ("traffic will merge smoothly (within road capacity limits)") (issue #17841, closed 2026-04) — [GitHub #17841](https://github.com/eclipse-sumo/sumo/issues/17841).
- Open issues still relevant to merges:
  - "Check on ramp merging behavior for sublane model | actionstep>simstep | ballistic" — [#3696](https://github.com/eclipse-sumo/sumo/issues/3696);
  - "add parameter lcStrategicOnramp" — [#4068](https://github.com/eclipse-sumo/sumo/issues/4068);
  - "deadlock when lane-changing close to lane end" — [#5124](https://github.com/eclipse-sumo/sumo/issues/5124);
  - "consider lane type (acceleration) for determining strategic look-ahead distance" — [#3515](https://github.com/eclipse-sumo/sumo/issues/3515);
  - "vehicles underestimate speed gain on fast neighboring lane" (2025) — [#16302](https://github.com/eclipse-sumo/sumo/issues/16302).

  [Titles read only.]

**SUMO documentation**
- Motorway ramps doc: acceleration lanes are modelled as dead-end lanes. "It may be useful to make acceleration lanes in SUMO somewhat longer than in reality. This compensates for the cautious default behavior of SUMO drivers." Simulated drivers decelerate approaching the lane end because they cannot anticipate lane-change success. For lane drops, use a dead-end lane (forced change) or a `zipper` node [tool summary of page; VERIFY wording] — [SUMO docs: Motorways](https://sumo.dlr.de/docs/Simulation/Motorways.html).
- Lane-change parameters and defaults [tool extraction of page; VERIFY] — [SUMO docs: vehicle types](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html):

  | Parameter | Meaning | Default and range |
  |---|---|---|
  | `lcStrategic` | eagerness for strategic changes | 1.0 |
  | `lcCooperative` | willingness to cooperate | 1.0, range [0,1] |
  | `lcSpeedGain` | eagerness to change for speed | 1.0 |
  | `lcKeepRight` | keep-right obligation | 1.0 |
  | `lcAssertive` | "the required gap is divided by this value" | 1 |
  | `lcLookaheadLeft` | strategic look-ahead to the left | 2.0 |
  | `lcSpeedGainRight` | left/right threshold asymmetry for speed gain | 0.1 |
  | `lcSigma` | lateral imperfection | 0 |
  | `lcImpatience` | dynamic factor on lcAssertive and lcPushy | 0, range −1…1 |
  | `lcTimeToImpatience` | time to maximum impatience | ∞ |
  | `lcAccelLat` | maximum lateral acceleration | 1.0 |
  | `lcPushy` | lateral encroachment | 0 |
  | `lcCooperativeSpeed` | cooperative speed adjustment | = lcCooperative |
  | `lcStrategicLookahead` | strategic look-ahead distance | 3000 m |

  Car-following models available include Krauss (default), IDM, IDMM, EIDM, W99, Wiedemann, ACC, CACC, BKerner and others. `actionStepLength` defaults to the simulation step.
- Road-capacity doc: capacity is set mainly by `length` (5 m), `minGap` (2.5 m) and `tau` (1 s), with gross headway = (length+minGap)/v + tau. That gives roughly 2,482 veh/h per lane theoretical capacity at 16.66 m/s with Krauss defaults, but "achieved insertion capacity varies significantly (1198–2482 veh/hour…)". Realised flow is lowered by heterogeneous desired speeds and random slow-downs. `--step-length 0.1` plus `--extrapolate-departpos` improves insertion capacity [tool summary; VERIFY numbers] — [SUMO docs: RoadCapacity](https://sumo.dlr.de/docs/Simulation/RoadCapacity.html).

**Riehl, Kouvelas & Makridis (2026), SUMO-conference "best practice" recipe** [read: §3.1 "Case Study for Ramp Metering", plus the public route file]. Source: "sumoITScontrol: Traffic Controller Collection for SUMO Traffic Simulations", *SUMO Conference Proceedings* 7 (pre-print, published 2026-05-03) — [pre-print PDF](https://sumo.dlr.de/preprints/pre-print-3284.pdf); [code](https://github.com/DerKevinRiehl/sumoITScontrol).
- The plant is a 2-lane, 4.1 km motorway with 3 metered on-ramps. Geometry variants: 200 m auxiliary lane, no auxiliary lane, or multi-lane ramp with a 300 m auxiliary lane. Each run is 4,200 s (1 h of analysis plus 10 min warm-up) at a 0.5 s step, which the authors call "the coarsest time resolution that still provides stable and sufficiently accurate traffic dynamics".
- Geometry and control advice:
  - use unregulated priority junctions at merges; if regulated, "ramp vehicles may behave overly cautiously and wait excessively for large gaps";
  - forbid mainline vehicles from changing into the auxiliary lane;
  - leave enough acceleration distance between the meter signal and the merge, or "vehicles will merge at unrealistically low speeds, artificially reducing mainline capacity";
  - put detectors on mainline lanes, never on auxiliary lanes.
- Demand advice:
  - "Homogeneous driver settings often lead to overly stable traffic flow and underestimate the formation of disturbances and capacity drops." Use ≥ 5 driver classes per vehicle category and origin, with mainline more cooperative and ramp more assertive;
  - use probabilistic (geometric) insertion with `probability`, not `vehsPerHour`;
  - `departSpeed="max"`, `departLane="free"`, `departPos="last"`, `insertionChecks="none"`;
  - always verify realised flow with detectors.
- Table 3 of the paper:

  | | `tau` (s) | `lcAssertive` | `lcCooperative` | `accel` (m/s²) | `decel` (m/s²) |
  |---|---|---|---|---|---|
  | Mainline | 10.0 → 8.5 | 0.01–0.20 | 1.0 | 0.5–1.1 | 3.5–5.5 |
  | Ramp | 1.5 → 0.4 | 9.5–12.0 | 0.03–0.00 | 4.0–5.0 | 3.0–8.0 |

  The public `Demand_1.rou.xml` confirms mainline `tau="10.0"`…`"8.5"` and also sets `lcSigma` (1.8 mainline, 0.4 ramp), `lcPushy` (0 mainline, 1.0 ramp), `minGapLat` (9.0 mainline, 0.13 ramp) and `lcTimeToImpatience` (15 s mainline, 5 s ramp). It selects the lane-change model via `<param key="laneChangeModel" value="SL2015"/>` — [route file](https://raw.githubusercontent.com/DerKevinRiehl/sumoITScontrol/HEAD/demos/demo_simulation_models/example_ramp_metering/Demand_1.rou.xml).
- No capacity-drop magnitude, discharge rate or comparison with field data is reported in the parts read.

**IDM / EIDM evidence relevant to SUMO**
- Salles, Oswald & Reuss (2024) extended SUMO's EIDM (modified SUMO 1.16) with vehicle dynamics and per-vehicle calibration to drone trajectories at a Stuttgart signalised intersection [VERIFY: tool summary of HTML]:
  - in a 3.4 km ring at 50 km/h the calibrated heterogeneous EIDM "exhibits the capacity drop observed in real traffic";
  - in a 5 km closure test "only the EIDM produces stop-and-go waves", but the models "overestimated the characteristic wave velocity";
  - code at github.com/stepeos/pycarmodel_calibration.

  [arXiv 2408.03722](https://arxiv.org/html/2408.03722v1).
- The original EIDM-in-SUMO paper calibrated drive-off at signalised intersections, not freeway merges (Salles, Kaufmann & Reuss 2022, *SUMO Conference Proceedings* 1) [VERIFY: abstract] — [TIB-OP](https://www.tib-op.org/ojs/index.php/scp/article/download/95/262).
- In SUMO's I-24 calibration (IDM plus LC2013 parameters, 5-min RDS data), the best values were [VERIFY: tool summary, not read in full] — [arXiv 2409.19090](https://arxiv.org/html/2409.19090):
  - car-following: v_f 40.23 m/s, s_j 2.32 m, τ 1.85 s, a 1.78 m/s², b 3.89 m/s²;
  - lane change: lcStrategic 0.09, lcCooperative 0.34, lcAssertive 2.71, lcSpeedGain 1.04, lcKeepRight 0.24;
  - errors: flow RMSE 305 veh/h/lane, speed RMSE 8.5 mph.

  The study reproduced congestion onset location and queue propagation, but capacity drop was not reported as a target (Wang, de Souza & Karbowski 2024).
- Theory: variance-driven time gaps in car-following models reproduce the A9 (NL) headway distributions. The modal time headway shifts "by a factor of about 2 under congested conditions", which "macroscopically … corresponds to the capacity drop" (Treiber, Kesting & Helbing 2006, *Phys. Rev. E* 74, 016123) [VERIFY: abstract] — [arXiv physics/0508222](https://arxiv.org/pdf/physics/0508222).
- The Enhanced IDM (ACC model) removes IDM's unrealistic over-reaction to cut-ins. Kesting, Treiber & Helbing (2010) separate "maximum capacity before breakdown" from "(dynamic) bottleneck capacity after breakdown" (*Phil. Trans. R. Soc. A* 368, 4585–4605) [VERIFY: abstract] — [arXiv 0912.3613](https://arxiv.org/pdf/0912.3613).

**Field reference values for a realism gate**
- Capacity-drop range in the literature, as summarised by Wang et al. (2023): "Empirical data show that capacity drop ranges between 5% and 30% of the maximum observable discharge flow" [read: §1.1] — [MDPI](https://www.mdpi.com/2071-1050/15/3/2050).
- A UCI MSc thesis lists 3 % (Banks 2010), 8–10 % (Cassidy & Bertini 1999) and 18 % (Chung et al. 2007). On this reading, the "3–18 %" range used in our gate spans several sources, with 18 % attributed to Chung et al. (Chong 2017) [read: lit-review lines only] — [eScholarship](https://escholarship.org/content/qt18d9s080/qt18d9s080.pdf).
- Chung, Rudjanakanoknad & Cassidy, "Relation between traffic density and capacity drop at three freeway bottlenecks", *Transportation Research Part B* 41(1), 82–95 (2007; online 2006) [VERIFY: metadata only] — [DOI](https://doi.org/10.1016/j.trb.2006.02.011).
- At one lane-drop site, discharge varied from 5,220 to 6,040 veh/h depending on the congestion type. Stop-and-go outflows were always lower than standing-queue outflows (Yuan, Knoop, Leclercq & Hoogendoorn 2017, *Transportmetrica B* 5(2), 145–158) [VERIFY: abstract] — [DOI](https://doi.org/10.1080/21680566.2016.1245163).
- Field example from an urban expressway merge in Shanghai: about 4,200 veh/h before breakdown and about 3,700 veh/h discharge, i.e. 11.9 % drop (Wang et al. 2023, Fig. 4) [read]. Per-lane numbers are not given in the parts read.
- A fitting method for Wu's fundamental diagram estimates **free-flow capacity and queue-discharge rate separately** from loop data (Knoop & Daamen 2017, *Transportmetrica B* 5(2), 129–144) [VERIFY: abstract]. It is useful for computing the realism-gate targets from any field loop dataset — [DOI](https://doi.org/10.1080/21680566.2016.1256239).

### Inferences
- **Mainline `tau` in the published recipe.** With Krauss, the minimum gross headway is about `tau + (length+minGap)/v`. At `tau` = 10 s and v ≈ 30 m/s that caps mainline flow near 3600/10.25 ≈ 350 veh/h/lane. **I cannot confirm whether this is intended or an error, and I may be misreading how SUMO applies `tau` here.** In any case, this recipe should not be copied as a validated realism configuration.
- **SL2015 may not be active in that recipe.** In SUMO the lane-change model is normally chosen with the vType *attribute* `laneChangeModel`. A generic `<param key="laneChangeModel">` probably does not select it, and SL2015 is used automatically only with `--lateral-resolution`. Not tested; verify with a 1-minute run.
- **Likely cause of our low discharge.** Our signalised plant passed with Krauss (1,854 veh/h/lane), so Krauss longitudinal queue discharge is probably adequate. The freeway failures (900–1,528 veh/h/lane) are therefore more likely lateral/merge artefacts than car-following ones. Candidate mechanisms, all consistent with the docs and Riehl et al.:
  - ramp vehicles decelerating or stopping at the dead end of the acceleration lane and entering at low speed;
  - regulated or priority junction settings making ramp drivers over-cautious;
  - mainline vehicles using the auxiliary lane.

  This is untested.
- **Our IDM runs.** IDM with a = 1.0 m/s² (Flow defaults) and no stochasticity plausibly explains both slow discharge and missing breakdown dynamics. The maintainer explicitly recommends Krauss or EIDM over IDM for density-driven speed reduction.
- **A promising SUMO configuration to screen** (inference, not a published validated set):
  - Krauss or EIDM with `sigma` > 0;
  - ≥ 5 heterogeneous vTypes per origin (`speedFactor` distribution, `tau` about 0.8–1.6 s on the mainline);
  - ramp vTypes with high `lcAssertive`, low `lcCooperative`, and `lcImpatience`/`lcTimeToImpatience` set;
  - mainline `lcCooperative` < 1 calibrated;
  - acceleration lanes lengthened (per the docs);
  - auxiliary lane closed to mainline lane changes;
  - 0.1–0.5 s step;
  - discharge measured on mainline lanes ≥ 300–500 m downstream of the merge (the maintainer notes full speed is regained by about 450 m).
- **Lane drops vs on-ramps.** The lane drop with a `zipper` node probably gives the cleanest capacity control but no drop by construction ("merge smoothly within road capacity limits"). A forced dead-end lane is the configuration more likely to generate drop, but also artefacts.

### Gaps
- No primary SUMO paper was found that reports a calibrated freeway capacity drop within 3–18 % **and** a queue discharge of ≥ 1,600 veh/h/lane. The Boukhellouf et al. full text (SUMO version, models, parameters) could not be retrieved.
- The ANNSIM 2025 SUMO lane-drop paper (403) and the NCHRP/NASEM I-210 SUMO calibration appendix (only image placeholders were served) were not read.
- No SUMO-specific study of W99 or ACC models at freeway merges was found in this pass.
- `actionStepLength` effects at merges are only flagged in an open issue (#3696); no quantitative source was found.

---

## Q2. Context: how VISSIM / Aimsun studies reproduce (or fail to reproduce) capacity drop at merges

### Takeaway
Commercial tools share SUMO's weakness. Default gap-acceptance merging is too conservative, so ramp vehicles queue on the acceleration lane while the mainline flows freely, and capacity drop rarely emerges. Published successes needed **model surgery** (IDM car-following plus a forced or urgency-dependent merge model, or Hidas' lane-change model) **plus calibration to site data**.

### Cited Findings
- Wang, Wang, Yu & Guo (2023) [read: §2.3, §4] — [MDPI](https://www.mdpi.com/2071-1050/15/3/2050):
  - "It is not yet easy to faithfully reproduce capacity drop at bottlenecks, e.g., freeway merges and lane drops, in microscopic simulation" tools such as AIMSUN and VISSIM.
  - With default AIMSUN, "ramp merging vehicles usually have to wait on the acceleration lane much longer than in reality, while the mainstream traffic is not much congested … merging happened only around the end of the acceleration lane".
- The same authors replaced Gipps car-following with IDM and the Gipps merge with a heuristic forced-lane-change model, whose speed, speed-difference and distance thresholds relax linearly along the acceleration lane. They calibrated it on the A20 (NL) [read: §4.3–4.4]:
  - the first-merge capacity was about 2,085 veh/h/lane;
  - mainline outflow stayed at capacity (about 4,170 veh/h) for about 15 min, then "dropped by 14.5%";
  - reverse-lambda fundamental diagrams appeared;
  - ALINEA prevented the drop.

  Success was attributed to IDM for all vehicles, the forced merge model and calibration on real data. Full calibration details are in Perraki's MSc thesis and Perraki, Roncoli, Papamichail & Papageorgiou [not read; VERIFY].
- de Souza, Mosslemi, Vrugt & Jin (2018) calibrated a combined car-following and lane-changing model to I-405 (Irvine) data and report that it "predicts accurately the capacity drop phenomenon" (*Procedia Computer Science* 130, 908–913) [VERIFY: abstract] — [DOI](https://doi.org/10.1016/j.procs.2018.04.088). Wang et al. (2023) describe it as replacing Aimsun's Gipps lane change with Hidas' model [read: §2.3].
- VISSIM 10 and MOTUS, calibrated on Dutch on-ramp, off-ramp and weaving trajectory data, "are as yet unable to simulate turbulent traffic around motorway ramps realistically, in terms of lane change locations and headway distribution" (van Beinum et al. 2020, *J. Transp. Eng. Part A* 146) [VERIFY: abstract] — [DOI](https://doi.org/10.1061/jtepbs.0000296).
- An Aimsun MSc study of a lane-drop/merge bottleneck (Gipps car-following; cooperation distance 330 m, aggressiveness 40 %, cooperation 80 %, reaction time 1.1 s) obtained a **5.52 % capacity-drop ratio**. The drop ratio rose towards 100 % as acceleration or merge distance shrank (Chong 2017, UC Irvine) [read: setup and results lines] — [eScholarship](https://escholarship.org/content/qt18d9s080/qt18d9s080.pdf).
- Capacity drop in INTEGRATION was triggered mainly by truck share, i.e. acceleration heterogeneity (Chamberlayne et al., as reviewed in Wang et al. 2023) [secondary; VERIFY].
- Chen & Ahn created drop by making ramp vehicles merge below mainline speed and then accelerate at a bounded rate (as reviewed in Wang et al. 2023) [secondary; VERIFY]. This matches the bounded-acceleration mechanism of Laval & Daganzo: "Bounded acceleration explains … the capacity drop of freeway bottlenecks" (Laval & Daganzo 2004 working paper; the journal version is believed to be *Transportation Research Part B* 40, 2006) [VERIFY].
- **Stop-and-go waves.** Hickert et al. (2026) benchmark calibration on SUMO I-24 scenarios [read: §5.4, results]:
  - scenarios: a 1.3 km on-ramp toy network, a 3-mile I-24 segment, and a 4-mile two-way I-24 network with 12 h of INCEPTION data;
  - "we find all methods are insufficient to capture stop-and-go behavior of traffic waves", and at large scale the waves "degrade to non-existence";
  - manual calibration of one freeway microsimulation environment typically takes "180 and 4,500 working hours" (citing Alexiadis et al. 2014; secondary).

  [arXiv 2608.19642](https://arxiv.org/pdf/2608.19642).

### Inferences
- The consistent lesson across tools is that **merge realism is a lateral-model problem**. A plant passes a capacity-drop gate only when ramp drivers become progressively more willing to accept short gaps along the acceleration lane and then accelerate with bounded rates.
- In SUMO the closest knobs are `lcAssertive`, `lcImpatience`/`lcTimeToImpatience`, `lcCooperative`/`lcCooperativeSpeed`, ramp vType `accel`, and acceleration-lane length.
- Commercial tools are not a shortcut. They need the same surgery and add licensing cost.

### Gaps
- No VISSIM study was found in this pass that reports a quantitative merge capacity drop reproduced against field data with stated W99 parameters (CC0–CC9, lane-change parameters).
- Perraki's calibration details for the A20 Aimsun model were not read.

---

## Q3. Macroscopic plants: CTM/LTM with capacity drop and METANET calibrated to real sites; realism and use for ramp-metering/VSL evaluation

### Takeaway
First-order (LWR/CTM) models do not produce capacity drop unless it is **added explicitly**. Options are a two-capacity fundamental diagram with a memory rule (Srivastava & Geroliminis 2013), the variants reviewed and validated on UK data by Kontorinaki et al. (2017), or endogenous merge models (Leclercq et al.). Second-order METANET generates drop "to an extent" and has decades of real-site validation and field-controller lineage (Paris Boulevard Périphérique, Amsterdam ring, Monash Freeway HERO). Both run full days in milliseconds to seconds. Their key risk is that **the drop magnitude is a modelling choice**, and controller benefit scales with it.

### Cited Findings

**CTM / LWR with capacity drop**
- Srivastava & Geroliminis (2013), *Transportation Research Part C* 30, 161–177 [VERIFY: search snippet of EPFL record; PDF download failed (HTTP 429)] — [EPFL PDF](https://infoscience.epfl.ch/record/188341/files/Sriv_Gerol_2013.pdf?version=1); [DOI](https://doi.org/10.1016/j.trc.2013.02.006):
  - empirical evidence of capacity drop at Twin Cities freeway–ramp merges, with a phase-diagram method to estimate it;
  - "the level of drop depends on the ratio of mainline vs. ramp flow", and the paper investigates whether ramp control affects it;
  - model: a fundamental diagram with two capacity values and a memory-based rule within a Godunov (CTM) scheme, "more reliable and accurate" than earlier theories against real data and a micro-simulation of a long stretch.
- Kontorinaki, Spiliopoulou, Roncoli & Papageorgiou (2017), "First-order traffic flow models incorporating capacity drop: overview and real-data validation", *Transportation Research Part B* 106, 52–75 [VERIFY: repository metadata/abstract snippet] — [DOI](https://doi.org/10.1016/j.trb.2017.10.014); [TUC repository](https://dias.library.tuc.gr/view/74059?locale=en):
  - LWR-type models "are unable to reproduce … the capacity drop and stop-and-go waves" without extension;
  - the paper reviews capacity-drop extensions of discretised LWR models, proposes a new one "with emphasis on practical applicability for traffic simulation, management and control", and validates them on a UK motorway network.
- Cao, Nilsson & Coogan (2021) [read: abstract and introduction] — [arXiv 2106.10347](https://arxiv.org/pdf/2106.10347):
  - they treat capacity drop and hysteresis as one behaviour in a CTM;
  - "if capacity drop is ignored in the control design, then the resulting controller … may be significantly suboptimal";
  - an MILP-based MPC that accounts for drop is optimal for a long enough horizon, and a hand-crafted integral-feedback modification also beats the drop-ignorant controller.
- Leclercq, Laval & Chiabaut (2011) extend the Newell–Daganzo merge model with an **endogenous** capacity drop caused by merging, validated on an M6 (UK) merge (*Procedia – Social and Behavioral Sciences*, ISTTT) [VERIFY: abstract] — [DOI](https://doi.org/10.1016/j.sbspro.2011.04.505). Follow-up: Leclercq, Knoop, Marczak & Hoogendoorn, "Capacity drops at merges: new analytical investigations", *Transportation Research Part C* (2016; online 2015) [VERIFY: metadata] — [DOI](https://doi.org/10.1016/j.trc.2015.06.025).
- Jin, Gan & Jin, "A kinematic wave theory of capacity drop" [not read; VERIFY] — [arXiv 1310.2660](https://arxiv.org/pdf/1310.2660). Companion VSL paper on a lane-drop bottleneck [not read; VERIFY] — [arXiv 1310.2658](https://arxiv.org/pdf/1310.2658).
- In LWR, "a static speed-density relation, implying unbounded acceleration/deceleration … deliver[s] no capacity drop". METANET's dynamic speed equation "yields capacity drop to an extent" (Wang et al. 2023 §2.2) [read].

**METANET calibrated to real sites**
- Wang et al. (2023) reproduce a merge capacity drop in METANET [read: §3]:
  - 3-lane, 4 km stretch with 16 segments;
  - the parameter table lists 2,050 veh/h/lane and a 15 % "capacity drop rate" with δ = 0.9 (table layout parsed from PDF; VERIFY);
  - segment flow peaked near 6,500 veh/h, then dropped, and ALINEA prevented the drop.
- Wang, Yu, Guo, Papamichail, Papageorgiou et al. (2022), "Macroscopic traffic flow modelling of large-scale freeway networks with field data verification: state-of-the-art review, benchmarking framework, and case studies using METANET", *Transportation Research Part C* 145, 103904 [VERIFY: metadata only] — [DOI](https://doi.org/10.1016/j.trc.2022.103904).
- Amsterdam ring: METANET was validated on the motorway network around Amsterdam, with quantitative link-level validation and qualitative network-level validation (Kotsialos, Papageorgiou, Diakaki, Pavlis & Middelham 2002, *IEEE Transactions on ITS*) [VERIFY: abstract] — [DOI](https://doi.org/10.1109/tits.2002.806804).
- Paris: a macroscopic model was validated on a 6 km stretch of the southern Boulevard Périphérique with several ramps "under a broad spectrum of traffic conditions"; Part II covers coordinated ramp metering (Papageorgiou, Blosseville & Hadj-Salem 1990, *Transportation Research Part A*) [VERIFY: abstract] — [Part II DOI](https://doi.org/10.1016/0191-2607(90)90048-b).
- ALINEA field results at single and multiple ramps of the Boulevard Périphérique and the A10 West, Amsterdam (Papageorgiou, Hadj-Salem & Middelham 1997, *Transportation Research Record* 1603, 90–98) [SAGE] [VERIFY: abstract] — [DOI](https://doi.org/10.3141/1603-12).
- Monash Freeway (Melbourne) HERO (Papamichail, Papageorgiou, Vong & Gaffney 2010, *Transportation Research Record* 2178, 10–20) [SAGE] [VERIFY: abstract] — [DOI](https://doi.org/10.3141/2178-02). An open copy is listed at [EPFL infoscience 165859](http://infoscience.epfl.ch/record/165859), which may give the author access despite the SAGE publisher.
  - HERO targets critical occupancy "to overcome the problem of uncertain freeway capacity";
  - field results at 6 inbound ramps showed "a significant increase of traffic throughput and a reduction of travel times" against the previous system, with roll-out to 63 ramps (no numbers in the abstract).
- VSL+RM MPC on an adapted METANET (Hegyi, De Schutter & Hellendoorn 2005, *Transportation Research Part C*) [VERIFY: metadata; abstract of the 2002 ACC version read] — [DOI](https://doi.org/10.1016/j.trc.2004.08.001).
- Full-year simulation of ALINEA vs HERO on an 8-mile Kansas City corridor: localised gains; "ramp metering may cause a new (possibly 'hidden') bottleneck to occur downstream"; on-ramp operations deteriorated under isolated control (Shehada & Kondyli 2019, *Journal of Advanced Transportation*) [VERIFY: abstract] — [DOI](https://doi.org/10.1155/2019/8740158).

**Mesoscopic SUMO**
- Ni, Akopian, Kouvelas & Makridis (2026) find that SUMO's Eissfeldt mesoscopic model "does not fully comply with the principle of the LWR model", gives "unrealistic onset and recovery pattern of congestion", and "generally underestimate[s]" congestion. They propose an LTM-style meso implementation. A related SUMO issue, "Implement the LIFT (meso-LTM) model", was closed 2026-07-14 [read: abstract] — [arXiv 2606.09282](https://arxiv.org/pdf/2606.09282); [GitHub #18203](https://github.com/eclipse-sumo/sumo/issues/18203).

### Inferences
- A two-capacity CTM (or a METANET with calibrated drop) is the cheapest plant that **passes a capacity-drop gate by construction**. That is exactly why it is weak evidence for a DRL claim: gains from "preventing breakdown" scale directly with the assumed drop (Cao et al. show the controller ranking flips depending on whether drop is modelled).
- A defensible use is to:
  - set the drop magnitude from a field fit, e.g. Wu-FD queue discharge via Knoop & Daamen (2017), or the Srivastava–Geroliminis ramp-ratio dependence;
  - report sensitivity of every controller gain to the drop magnitude (e.g. 0 %, 5 %, 10 %, 15 %);
  - confirm the ranking on a micro plant.
- First-order CTM does not create stop-and-go waves. A VSL evaluation that relies on wave dissipation (SPECIALIST-type) needs METANET, a second-order or Lagrangian model, or micro.

### Gaps
- Exact drop magnitudes from Srivastava & Geroliminis (2013) and the model ranking from Kontorinaki et al. (2017) were not read (paywalled, or download failed).
- No openly downloadable, calibrated METANET or CTM parameter set for the Paris, Amsterdam or Monash sites was found in this pass.
- Grenoble South Ring: a search snippet indicates an 11.8 km CTM "tuned by using real data and Aimsun micro-simulator", with 15-s loop data over 35 days in 2014. Source pages were not read [VERIFY] — [HAL thesis record](https://hal-univ-tlse3.archives-ouvertes.fr/INRIA/tel-01103036v1).

---

## Q4. Openly available calibrated freeway scenarios (hybrid / benchmark) and their calibration evidence

### Takeaway
Open, calibrated **SUMO freeway** scenarios exist:
- Alicante–Murcia (9 days, 97 km);
- I-24 segments (Wang et al. 2024; the Hickert et al. 2026 benchmark, with code promised "upon publication");
- the Flow/I-210 network.

None that I found documents a validated capacity drop or queue-discharge rate, and the newest benchmark reports that calibrated SUMO I-24 models lose stop-and-go waves at scale.

### Cited Findings
- **Alicante–Murcia (Spain)** [read: abstract; GitHub metadata] — [DOI](https://doi.org/10.1109/access.2021.3126269); [GitHub](https://github.com/msepulcre/Alicante-Murcia-SUMO-Scenario):
  - SUMO, "9 full days of traffic over a 97 km freeway section", light and heavy vehicles;
  - calibrated with Spanish road-authority data using "Clone Feedback", an iterative demand calibration that needs only flow measurements, and reported to model "traffic flow, the traffic speed and the road's occupancy";
  - repository is MIT-licensed, about 46 MB, last pushed 2023-02 (González-Delicado, Gozálvez, Mena-Oreja, Sepulcre & Coll-Perales 2021, *IEEE Access* 9, 154423–154434).
- **I-24 MOTION (Nashville)**:
  - Gloudemans et al. (2023), *Transportation Research Part C* 155, 104311 [VERIFY: abstract of arXiv version] — [arXiv 2301.11198](https://doi.org/10.48550/arxiv.2301.11198): 276 cameras over about 4.2 mi of a 4–5 lane freeway with "frequently observed congestion", producing trajectory datasets.
  - SUMO calibration (Wang, de Souza & Karbowski 2024): a 3.5-mile westbound segment with 4–6 lanes, 2 on-ramps and 1 off-ramp; IDM plus LC2013 parameters; repository link "removed for review" [VERIFY] — [arXiv 2409.19090](https://arxiv.org/html/2409.19090).
  - Hickert et al. (2026) benchmark [read: §5]: small, medium and large scenarios; INCEPTION v1.0.0 has 40 h of trajectories; the large scenario uses 12 h of aggregate data; GA, SPSA, SL and MA-IDM calibrators were compared; "data and evaluation code will be made available upon publication" — [arXiv 2608.19642](https://arxiv.org/pdf/2608.19642).
  - On the small toy on-ramp network, count RMSE was 5.06 for SUMO defaults vs 3.59–4.40 for calibrators, and velocity MAPE 39.8 % for defaults vs 5.2 % for the best method (Table 3) [read].
  - A MARL VSL was trained "in a traffic simulator" and deployed on 17 miles of I-24 with 67 VSL controllers. The authors quantify sim-to-real mismatch (Zhang et al. 2024) [read: abstract; simulator identity not stated in abstract] — [arXiv 2407.08021](https://arxiv.org/abs/2407.08021).
- **Flow / I-210 (Los Angeles)**:
  - Flow integrates SUMO (and Aimsun) with RL libraries (Wu, Kreidieh, Parvate, Vinitsky & Bayen 2017; Vinitsky et al. 2018, CoRL benchmarks) [VERIFY: abstract].
  - A search snippet describes congestion in the I-210 network as "generated via an imbalance between inflow and outflow conditions, with high inflow rates and restricted outflow", coupled with human-driver string instability [VERIFY: snippet; primary paper not identified] — [search result: arXiv 2208.12534](https://arxiv.org/pdf/2208.12534).
  - The National Academies (2024) report *Using Cooperative Automated Transportation Data for Freeway Operational Strategies* (DOI 10.17226/27748) has an "Appendix B – I-210 Eastbound SUMO Model Calibration" [VERIFY: content not served] — [NASEM](https://www.nationalacademies.org/read/27748/chapter/11).
- **SUMO ramp-metering controller collection**: ALINEA, PI-ALINEA, METALINE and HERO-inspired controllers on a synthetic 4.1 km plant, open source (Riehl et al. 2026) [read: §2.1, §3.1] — [GitHub](https://github.com/DerKevinRiehl/sumoITScontrol). Useful as a **tuned-baseline implementation reference**, not as a realism-validated plant.
- SUMO's scenario list page exists but was not read in this pass — [SUMO docs: Scenarios](https://sumo.dlr.de/docs/Data/Scenarios.html).

### Inferences
- Alicante–Murcia is the only open SUMO freeway scenario I found that covers **full days** with multi-day calibration. It is the most direct candidate for "full-day" testing. Its realism for merge capacity drop and discharge is undocumented; our T1 gate would have to be run on it.
- The Flow/I-210 congestion mechanism, as described in the snippet, is boundary-imposed. It would likely fail a realism gate that requires endogenous merge breakdown.
- The Hickert et al. finding is a direct warning for our roadmap. A plant calibrated to counts and speeds can still lack the phenomena that VSL/RM act upon, so the gate must test phenomena (drop, discharge, waves), not only goodness of fit.

### Gaps
- Licence, SUMO version compatibility (built for pre-1.27 SUMO?), and detector-level validation numbers for Alicante–Murcia were not checked.
- No open Aimsun/VISSIM freeway model with public calibration evidence was found. Grenoble GTL data availability was not verified.

---

## Q5. Cost (effort, compute) and main risks of each plant option

### Takeaway
Fastest to a defensible result, as a ranking (inference):
1. A **macroscopic CTM/METANET plant with field-fitted, sensitivity-swept drop**, for exploration and training (very cheap). Its main risk is that the benefit is baked in.
2. A **SUMO micro plant rebuilt per the merge-realism checklist**, used for confirmation (moderate). Its risk is that it may still fail, since there is no published SUMO precedent.
3. An **open calibrated SUMO corridor (Alicante–Murcia)** for full-day external validity (moderate to high). Its risks are porting and undocumented bottleneck realism.

A commercial tool with a custom merge model is the highest-effort route and is not clearly better.

### Cited Findings
- Manual microsimulation calibration effort is 180–4,500 working hours per freeway environment (Alexiadis et al. 2014, as cited by Hickert et al. 2026) [secondary; VERIFY] — [arXiv 2608.19642](https://arxiv.org/pdf/2608.19642).
- The I-24 SUMO calibration used about 15,340 objective evaluations per experiment (differential evolution, population 10–20, up to 100 iterations) on the synthetic scenario (Wang et al. 2024) [VERIFY: tool summary] — [arXiv 2409.19090](https://arxiv.org/html/2409.19090).
- Riehl et al. (2026) chose a 0.5 s step as the coarsest stable choice for motorway merging [read] — [pre-print](https://sumo.dlr.de/preprints/pre-print-3284.pdf).
- Calibrated microsimulators fail to reproduce stop-and-go waves at scale, and performance declines with network size, vehicles and duration (Hickert et al. 2026) [read].
- Capacity-drop-aware vs drop-ignorant ramp-metering controllers differ significantly in a capacity-drop CTM (Cao et al. 2021) [read: abstract].
- Aimsun needed a custom forced-merge model plus calibration to show a 14.5 % drop (Wang et al. 2023) [read].
- VISSIM 10 could not reproduce ramp turbulence even after calibration (van Beinum et al. 2020) [VERIFY].

### Inferences

**Options at a glance** (my estimates, not measured; compute figures are order of magnitude, using our 32-worker libsumo setup as reference)

| Option | Realism evidence | Effort | Compute per simulated day | Main risks |
|---|---|---|---|---|
| A. SUMO micro, merge-realism rebuild (Krauss/EIDM + sigma; ≥ 5 vTypes; assertive/impatient ramp drivers; long acceleration lanes; aux-lane change ban; zipper or forced lane drop) | Maintainer and docs guidance; Riehl et al. recipe (unvalidated); no published SUMO drop calibration | 1–3 weeks of T0/T1 iterations | Seconds to minutes per corridor-day per process; parallel over seeds | May still fail T1; tuning to the gate risks over-fitting to the gate; teleports at forced merges; stop-and-go may be absent |
| B. CTM with two-capacity drop (Srivastava–Geroliminis / Kontorinaki variant) or METANET | Real-site validations (Paris, Amsterdam, UK, Twin Cities); decades of controller lineage (ALINEA, HERO, MPC) | Days (own implementation) | Milliseconds to seconds per day | Drop is assumed, so controller benefit is partly an assumption; CTM has no stop-and-go waves; gameable metrics (e.g. ramp queues hidden by point queues) |
| C. Hybrid: B for screening and DRL training, A for confirmation (or MPC model = B fitted on separate seeds, plant = A) | Combines both | B + A | Mostly B cost | Sim-to-sim gap; must pre-register that the confirmatory plant is A |
| D. Open SUMO corridor (Alicante–Murcia; I-24 when released) | Multi-day flow, speed and occupancy calibration (A–M); I-24 counts and speeds; drop and discharge unverified | 1–4 weeks to port and validate on SUMO 1.27 and add metering/VSL | Minutes to hours per day (97 km, 9 days) | Bottleneck realism unknown; demand calibration may be detector-driven (boundary-imposed congestion) |
| E. Aimsun/VISSIM with custom merge model | Wang et al. 2023 (Aimsun 14.5 % drop) | Licence plus weeks; API surgery | Similar to A | Cost, closed source, reproducibility |

- **Cheapest discriminating check for option A, before more tuning.** Run a single-lane jam-release (queue-discharge) test on the freeway vTypes. If that alone gives ≥ 1,600 veh/h/lane, the remaining deficit is the merge model, so tune `lcAssertive`, `lcImpatience` and acceleration-lane length. If not, fix the car-following first (`accel`, `tau`, `minGap`, `sigma`). This mirrors why the signalised plant passed.
- **Gate design.** The gate should keep requiring **both** a discharge rate of ≥ 1,600 veh/h/lane (fit field targets with the Wu FD) **and** a drop of 3–18 %, measured at the same downstream mainline detector. Wang et al. (2023) note that drop "could only be seen precisely at activated bottleneck locations", so detector placement can create or hide the drop.

### Gaps
- No measured SUMO wall-clock benchmarks for freeway corridors were found in the sources; the compute figures above are my estimates.
- Whether Alicante–Murcia runs unchanged on SUMO 1.27 is unknown.
- No source quantifies how much DRL or MPC gain over ALINEA/HERO depends on assumed drop magnitude, beyond Cao et al.'s qualitative "significantly suboptimal".

#### Harvard reference list (reading status in brackets)
- Boukhellouf, M., Buisson, C. and Chiabaut, N. (2023) 'Merging and diverging operations: benchmark of three European microscopic simulation tools and comparison with analytical formulations', *European Transport Research Review*, 15, art. 12. doi:10.1186/s12544-023-00586-1. [VERIFY]
- Cao, M.E., Nilsson, G. and Coogan, S. (2021) 'On the impact of the capacity drop phenomenon for freeway traffic flow control', arXiv:2106.10347. [abstract/intro read]
- Chong, A.K.-H. (2017) *Analysis of Bottleneck Traffic Capacity Drop using Aimsun Simulation*. MSc thesis, University of California, Irvine. [partly read]
- Chung, K., Rudjanakanoknad, J. and Cassidy, M.J. (2007) 'Relation between traffic density and capacity drop at three freeway bottlenecks', *Transportation Research Part B*, 41(1), pp. 82–95. [VERIFY]
- de Souza, F., Mosslemi, M., Vrugt, J.A. and Jin, W.-L. (2018) 'Microscopic simulation replicates the capacity drop phenomenon', *Procedia Computer Science*, 130, pp. 908–913. [VERIFY]
- Gloudemans, D. et al. (2023) 'I-24 MOTION: an instrument for freeway traffic science', *Transportation Research Part C*, 155, 104311. [VERIFY]
- González-Delicado, J.J., Gozálvez, J., Mena-Oreja, J., Sepulcre, M. and Coll-Perales, B. (2021) 'Alicante-Murcia freeway scenario…', *IEEE Access*, 9, pp. 154423–154434. [abstract read]
- Hegyi, A., De Schutter, B. and Hellendoorn, H. (2005) 'Model predictive control for optimal coordination of ramp metering and variable speed limits', *Transportation Research Part C*, 13. [VERIFY]
- Hickert, C., Samaei, M., Wang, A., Zhang, C., Sun, L., Wang, Y., Ameli, M. and Wu, C. (2026) 'The calibration illusion in traffic microsimulation', arXiv:2608.19642 (working paper). [partly read]
- Kesting, A., Treiber, M. and Helbing, D. (2010) 'Enhanced intelligent driver model to access the impact of driving strategies on traffic capacity', *Phil. Trans. R. Soc. A*, 368, pp. 4585–4605. [VERIFY]
- Knoop, V.L. and Daamen, W. (2017) 'Automatic fitting procedure for the fundamental diagram', *Transportmetrica B*, 5(2), pp. 129–144. [VERIFY]
- Kontorinaki, M., Spiliopoulou, A., Roncoli, C. and Papageorgiou, M. (2017) 'First-order traffic flow models incorporating capacity drop: overview and real-data validation', *Transportation Research Part B*, 106, pp. 52–75. [VERIFY]
- Kotsialos, A., Papageorgiou, M., Diakaki, C., Pavlis, Y. and Middelham, F. (2002) 'Traffic flow modeling of large-scale motorway networks using the macroscopic modeling tool METANET', *IEEE Transactions on ITS*, 3(4). [VERIFY]
- Laval, J.A. and Daganzo, C.F. (2004) *Multi-lane hybrid traffic flow model: quantifying the impacts of lane-changing maneuvers on traffic flow*. Working paper (journal version believed to be *Transportation Research Part B* 40, 2006). [VERIFY]
- Leclercq, L., Laval, J.A. and Chiabaut, N. (2011) 'Capacity drops at merges: an endogenous model', *Procedia – Social and Behavioral Sciences*. [VERIFY]
- Ni, Y.-C., Akopian, A., Kouvelas, A. and Makridis, M.A. (2026) 'Revisiting mesoscopic traffic flow simulation in SUMO: limitations, analysis, and an alternative', arXiv:2606.09282. [abstract read]
- Papageorgiou, M., Blosseville, J.M. and Hadj-Salem, H. (1990) 'Modelling and real-time control of traffic flow on the southern part of Boulevard Périphérique in Paris, Parts I–II', *Transportation Research Part A*, 24. [VERIFY]
- Papageorgiou, M., Hadj-Salem, H. and Middelham, F. (1997) 'ALINEA local ramp metering: summary of field results', *Transportation Research Record*, 1603, pp. 90–98. [SAGE] [VERIFY]
- Papamichail, I., Papageorgiou, M., Vong, V. and Gaffney, J. (2010) 'Heuristic ramp-metering coordination strategy implemented at Monash Freeway, Australia', *Transportation Research Record*, 2178, pp. 10–20. [SAGE] [VERIFY]
- Riehl, K., Kouvelas, A. and Makridis, M.A. (2026) 'sumoITScontrol: traffic controller collection for SUMO traffic simulations', *SUMO Conference Proceedings*, 7 (pre-print). [§3.1 read]
- Salles, D., Kaufmann, S. and Reuss, H.-C. (2022) 'Extending the intelligent driver model in SUMO and verifying the drive off trajectories with aerial measurements', *SUMO Conference Proceedings*, 1. [VERIFY]
- Salles, D., Oswald, S. and Reuss, H.-C. (2024) 'Improving the intelligent driver model by incorporating vehicle dynamics: microscopic calibration and macroscopic validation', arXiv:2408.03722. [VERIFY]
- Shehada, M.K. and Kondyli, A. (2019) 'Evaluation of ramp metering impacts on travel time reliability and traffic operations through simulation', *Journal of Advanced Transportation*, 2019. [VERIFY]
- Srivastava, A. and Geroliminis, N. (2013) 'Empirical observations of capacity drop in freeway merges with ramp control and integration in a first-order model', *Transportation Research Part C*, 30, pp. 161–177. [VERIFY]
- Treiber, M., Kesting, A. and Helbing, D. (2006) 'Understanding widely scattered traffic flows, the capacity drop, and platoons as effects of variance-driven time gaps', *Physical Review E*, 74, 016123. [VERIFY]
- van Beinum, A., Broekman, E., Farah, H., Schakel, W., Wegman, F. and Hoogendoorn, S. (2020) 'Critical assessment of microscopic simulation models for simulating turbulence around motorway ramps', *Journal of Transportation Engineering, Part A*, 146. [VERIFY]
- Wang, Y., de Souza, F. and Karbowski, D. (2024) 'Calibrating microscopic traffic models with macroscopic data', arXiv:2409.19090. [VERIFY]
- Wang, Y., Wang, L., Yu, X. and Guo, J. (2023) 'Capacity drop at freeway ramp merges with its replication in macroscopic and microscopic traffic simulations: a tutorial report', *Sustainability*, 15(3), 2050. [§1–4 largely read]
- Wang, Y., Yu, X., Guo, J., Papamichail, I., Papageorgiou, M. et al. (2022) 'Macroscopic traffic flow modelling of large-scale freeway networks with field data verification…', *Transportation Research Part C*, 145, 103904. [VERIFY]
- Yuan, K., Knoop, V.L., Leclercq, L. and Hoogendoorn, S.P. (2017) 'Capacity drop: a comparison between stop-and-go wave and standing queue at lane-drop bottleneck', *Transportmetrica B*, 5(2), pp. 145–158. [VERIFY]
- Zhang, Y. et al. (2024) 'Field deployment of multi-agent reinforcement learning based variable speed limit controllers', arXiv:2407.08021. [abstract read]
- SUMO documentation pages (Motorways; Road Capacity; Vehicle Types) and GitHub issues #16198, #16659, #17841, #3696, #4068, #5124, #3515, #16302, #18203 (accessed 2026-10-04).
