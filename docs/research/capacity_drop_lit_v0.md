# Capacity drop at a SUMO lane drop: literature for a pre-registered model candidate (v0)

Date: 2026-10-13. Status: desk research only. No simulations were run. Not committed.
Context: SUMO 1.27.1, step 0.2 s, 3→2 lane drop built as a `zipper` node, EIDM + LC2013 near defaults, 100 km/h. In the pilots, queue discharge is ≈1,920 veh/h/lane, equal to or above the pre-breakdown flow.

Reading key: **[FT]** full text read; **[PART]** the relevant sections of the full text read; **[ABS]** abstract or summary page only; **[DOC]** official SUMO documentation or source code; **[DEV]** a statement by a SUMO developer on the mailing list or GitHub (not peer-reviewed); **[SEC]** a number taken from a source I read that cites the original, which I did not open; **[VERIFY]** not opened; do not rely on it until checked.

---


> **Spot-check by Claude Code (2026-10-13):**
> - **EIDM defaults** confirmed in the SUMO v1_27_1 source (`MSCFModel_EIDM.cpp`): treaction 0.5, tPersDrive 3, tPersEstimate 10, sigmagap 0.1, sigmaleader 0.02, sigmaerror 0.04, jerkmax 3, epsilonacc 1, taccmax 1.2, Mflatness 2, Mbegin 0.7, ccoolness 0.99, delta 4, stepping 0.25.
> - **GitHub #15951** confirmed: zipper merging starts at 100 m by default; with a visibility distance of 20 m, "vehicles will form a jam that goes almost up to the merging point". The quote "you will never see a drop in flow" is **not** in #15951; it is attributed to the sumo-user list, 2024-07-16, and is [VERIFY].
> - **Pilot evidence on C2:** the pilot's `laneend` variant (V69) is C2 at default LC2013 parameters. It gave 2,180–2,310 veh/h/lane before the drop and almost no queue (pilot README §2.7), not a capacity drop. Not data, but a warning.


## 1. Field values: capacity drop and queue discharge

| Source | Setting | Drop / discharge | Read |
|---|---|---|---|
| Zhang & Levinson 2004, TRR 1883:122-131 | 27 active bottlenecks, Twin Cities (MnDOT), 7 weeks | The flow drop after queue formation is **2-11 %** at all sites (mean ≈5 %, s.d. 2 %). Long-run mean QDF is **2,016 pcplph**; mean pre-queue flow is **2,124 pcplph**. | [FT] |
| Same paper, Table 1, site 25 | **I-94 WB at CR81, lane drop 3→2** (2 lanes at the bottleneck, 8.2 % heavy vehicles, 37 breakdowns in 28 days) | QDF **1,994 pcplph**, pre-queue flow **2,126 pcplph**, drop **7 %** | [FT] |
| Cassidy & Bertini 1999, TR-B 33(1):25-42 | 2 bottlenecks near Toronto | Discharge "can be 10% lower" than the pre-queue flow. Flows are near-stationary and reproducible day to day. Yuan et al. (2016) report the range as 8-10 % [SEC]. | [ABS] |
| Bertini & Leal 2005, J. Transp. Eng. 131(6):397-407 | Lane drop near London, corroborated at a Minneapolis lane drop | ≈10 % lower than the pre-queue flow | [VERIFY]: the publisher page returned 403; this number comes only from search-engine summaries |
| Chung, Rudjanakanoknad & Cassidy 2007, TR-B 41(1):82-95 | 3 bottlenecks with different geometries | The drop is tied to the density over an extended upstream segment; the density at drop onset is similar across sites once normalised per lane. The abstract gives no percentages. Yuan et al. (2016) quote **3-18 %**, and 8-18 % at a single site [SEC]. | [ABS] |
| Srivastava & Geroliminis 2013, TR-C 30:161-177 | Twin Cities on-ramp merges | ≈15 % at an on-ramp bottleneck [SEC, via Yuan 2016]. The drop depends on the ratio of mainline to ramp flow (search abstract). | [VERIFY]: the EPFL server returned 429/empty |
| Oh & Yeo 2012, TRR 2286:111-121 | Merges, Korea | Literature range **3-18 %** [SEC, via Yuan 2016]; the drop falls as the number of lanes rises (search abstract) | [VERIFY] |
| Yuan, Knoop & Hoogendoorn 2015, TRB poster 15-4064 / TRR 2491:72-80 | NL A4 (lane drop) and A12 (on-ramp), 3-lane sections, 1-min loop data, 6 days | Queue discharge **Q = 29·v_cong + 5000 veh/h** (3 lanes): 5,220-6,840 veh/h for congestion speeds of 6-60 km/h, against a pre-queue capacity of 6,300 veh/h (15 % trucks). Per lane that is ≈1,670 veh/h at v = 0 and ≈2,250 at 60 km/h. Yuan et al. (2019) put the drop at **≈26 % at zero speed**. Rain lowers the discharge, and the authors say the relation is site-specific. | [FT poster; TRR version not opened] |
| HCM / HCS (McTrans) | US facility analysis | Queue discharge drop default **7 %** ("based on a national average") | [ABS] McTrans web page; the HCM edition and chapter are **[VERIFY]** |
| Treiber, Hennecke & Helbing 2000 (intro) | Literature statement | "capacity drop (typically of the order of 20%)" | [FT], secondary |

**Comparison with the pilot.** In absolute terms, 1,920 veh/h/lane of discharge is inside the field QDF range: 1,772-2,332 pcplph across the Twin Cities sites, and 1,994 at the 3→2 site. The unrealistic part is that SUMO does not build up a **pre-queue flow 5-10 % above discharge** before breakdown. Field drops at lane drops cluster at **≈7-10 %**. Drops of 15-26 % appear only with low congestion speeds or at on-ramps.

**Measurement note.** Field values compare pre-queue flow with queue discharge, measured downstream with cumulative counts (Cassidy-Bertini). Use the same definition, and confirm the inflow can exceed discharge: insertion settings change achievable insertion flow by hundreds of veh/h (Road Capacity doc) [DOC].

---

## 2. SUMO-specific evidence

### 2a. Reproducing capacity drop in SUMO
- **Erdmann (SUMO developer), sumo-user, 2 Apr 2019** [DEV], on reproducing a drop at an on-ramp merge:
  - the drop "can only be observed if the entering flow of the mainline is near the limit", e.g. with `departSpeed="max" departPos="last"`;
  - the default `speedDev` of 0.1 leaves gaps that the merge fills, "so you might actually see a capacity gain". Setting `speedDev="0.05"` or lower shows the drop;
  - lowering `lcCooperative` "reduce[s] the merging efficiency and thus increase[s] the capacity drop";
  - a "known issue" can separate lane speeds and so weaken the drop.
- **Erdmann, sumo-user, 16 Jul 2024** [DEV], thread "creating a capacity drop … before a zipper junction". This is exactly our case: a 4→2 lane drop where neither `zipper` nor `priority` gave a drop, even with `speedDev=0.05` and `lcCooperative=0.2`. His answer, quoted: *"With the default settings of sumo, zipper merging starts 100m ahead of the lane drop. This causes cars to travel through the lane drop with maximum speed and flow. Thus you will never see a drop in flow. If you change the visibilityDistance attribute to 20, then a jam can form closer to the lane drop and vehicles will be slower at the merging point. You will then see an outflow pattern that matches the 'outflow of a jam' which is below the maximum flow. By varying the merging distance, you can reach any point in the continuum between permanent maximum flow and jam-outflow."*
- **GitHub #15951 (2024-12/2025-01)** [DEV]: the same advice. With `visibilityDistance` 20, vehicles form a jam almost up to the merge point and pass it slowly.
- **GitHub #6150 (2019)** [DEV]: the zipper adaptation distance used to be hard-coded at 100 m. *"On highways, flow does improve as the distance increases … this may not be realistic behavior."*
- **GitHub #6553 (open)** [DEV], lane drop **without** a zipper (forced lane change):
  - `lcCooperativeSpeed="0"` reverses the lane-flow imbalance;
  - `"0.5"` balances it "at the cost of throughput … compared to zipper … the throughput is reduced by 25%". This is a developer test; the scenario is not published.
- **GitHub #16198** [DEV]: an early drop in a user's run. The developer answered that `sigma=0.5` and `lcCooperative=0` can cause it, and that "capacity is a function of the model parameters".
- **Salles, Oswald & Reuss 2024** (IEEE ITSC; arXiv 2408.03722) [PART]:
  - setup: a 3.4 km **ring road at 50 km/h** with periodic 25-s closures, on a *modified* SUMO 1.16 at a 0.04 s step;
  - "the traffic flow generated by the calibrated, heterogeneous EIDM exhibits the capacity drop observed in real traffic". In that setup only EIDM produced stop-and-go waves;
  - the 486 calibrated parameter sets came from urban intersection drone data and are not printed in the paper;
  - the authors add that whether the simulated values match reality "remains to be verified".
- **ANNSIM 2025, "Discrepancy of lane flow distribution … lane-drop bottleneck in SUMO: a comparison of two car-following models"** (IEEE Xplore 11118854) [VERIFY]: not opened. A search summary claims that Krauss overestimates the bottleneck capacity by 46 %; that claim is unverified.

### 2b. Zipper node behaviour [DOC]
- In the Intersections doc, for link state Z: "Speed depends directly on neighboring traffic (braking only takes place on demand)".
- In PlainXML, connection attribute `visibility`: "For 'zipper'-links, this attribute controls the point at which zipper-merging behavior starts (default 100m)."
- In the Motorways doc: "The usual way to set up a lane-number reduction is to configure one of the lanes as a dead-end … and force vehicles to change-lanes. In some situations it may be appropriate to declare the node … as a zipper node instead."
- GitHub #15224 [DEV]: "emergency braking at zipper with low visibilityDistance". It was closed on 2024-07-30 under milestone 1.22.0, so the fix should be in 1.27.1. Emergency braking still needs to be counted.

### 2c. EIDM parameters (docs table, Definition of Vehicles; source `MSCFModel_EIDM.cpp` at tag v1_27_1)

| XML attribute | Default (source 1.27.1) | Meaning |
|---|---|---|
| `treaction` | 0.5 s | Maximum interval between action points: the CF decision update for acceleration only. The driver reacts sooner in critical situations (see `epsilonacc`). It plays the role of reaction time. **`actionStepLength` / driver state must not be used with EIDM.** |
| `tPersDrive` | 3 s | Correlation time of the Wiener process for the driving error (from the HDM) |
| `tPersEstimate` | 10 s | Correlation time of the Wiener processes for the gap and speed estimation errors |
| `sigmagap` | 0.10 | Gap estimation error magnitude, s_est = s·exp(σ_gap·w) (the HDM's V_s) |
| `sigmaleader` | 0.02 | Leader speed estimation error, entering as −gap·σ_leader·w (units 1/s, the HDM's r_c) |
| `sigmaerror` | **0.04 in the source; the docs table says 0.10** | Driving (acceleration) error magnitude, scaled up in critical situations. Salles et al. (2020) used 0.1. |
| `jerkmax` | 3 m/s³ | Maximum change of acceleration between steps |
| `epsilonacc` | 1 m/s² | If the computed acceleration drops by more than this between action points, the driver reacts immediately |
| `taccmax` | 1.2 s | Time to reach maximum acceleration after drive-off (applied below 0.5 m/s) |
| `Mflatness` | 2 | Flatness of the drive-off curve (recommended 1.5-3) |
| `Mbegin` | 0.7 | Shift of the drive-off curve |
| `ccoolness` | 0.99 | Coolness from the Enhanced IDM/CAH. **The docs table spells it `coolness`; the XML attribute in `SUMOXMLDefinitions.cpp` is `ccoolness`.** |
| `tpreview` | 4 s | Look-ahead for speed-limit changes |
| `delta` / `stepping` | 4 / 0.25 s | IIDM exponent / internal step |

Other EIDM notes [DOC]: intended for steps of 0.05-0.5 s (larger steps cause emergency braking and collisions); untested with ballistic update; smaller safe gaps than IDM; `randNorm` is platform-dependent (#8921).

Passenger defaults: accel 2.6 m/s², decel 4.5 m/s², minGap 2.5 m, tau 1 s, speedDev 0.1.

In the source, the estimation-error and reaction terms are not applied below 3 m/s (`EST_REAC_THRESHOLD`). **No source shows EIDM producing a capacity drop at a motorway lane drop.** Erdmann (2021) [DEV]: EIDM "should be suitable for spontaneous jams but I haven't tried out the parameters".

### 2d. Krauss: metastability and outflow below the maximum flow
- **Krauß 1998, PhD thesis / DLR-Forschungsbericht 98-08** [PART, chapter 5]:
  - in the *high-deceleration* limit, "the model does not reproduce the capacity drop … the outflow from jams is not lower than the maximum flow";
  - in the *low-acceleration-low-deceleration* class (dimensionless a = 0.2, b = 0.6, with τ = 1 s and l = 7.5 m, i.e. **a ≈ 1.5 m/s², b ≈ 4.5 m/s²**), the fundamental diagram is branched and hysteretic: "this finally models the capacity drop correctly";
  - q_max − q_out grows **linearly with the noise ε**, which was studied over 0.5-1 (Fig. 5.26). At the ε where it vanishes, the metastable branch disappears. The exact ε at zero cannot be read from the text: [VERIFY] from the figure;
  - his crude SI estimates for parameter values were a ≈ 0.8 m/s², b ≈ 4.5 m/s²;
  - the thesis model's time step equals τ = 1 s.
- **SUMO docs** [DOC]:
  - `sigma` defaults to 0.5;
  - `sigmaStep` defaults to the step length; "If set to a constant value (i.e 1), this decouples the driving imperfection from the simulation step-length".
- **Erdmann 2021** [DEV]: Krauss shows spontaneous jams only with sigma ≥ 0.8.
- **Salles et al. 2024, Table I** [PART]: Krauss with `actionStepLength` 1 s gave 7,587 collisions at a signalised intersection; calibrated heterogeneous Krauss gave 13,829.

### 2e. LC2013 parameters affecting merge friction [DOC]

| Parameter | Default | Meaning |
|---|---|---|
| `lcStrategic` | 1.0 | Eagerness for strategic changes. Higher means earlier; 0 means change only at the lane end; −1 disables. |
| `lcCooperative` | 1.0 | Willingness to change lanes cooperatively. Lower means less cooperation; −1 disables. |
| `lcCooperativeSpeed` | = lcCooperative | Cooperative speed adjustment, i.e. opening gaps (the #6553 knob) |
| `lcSpeedGain` | 1.0 | Eagerness to change lanes for speed gain |
| `lcAssertive` | 1 | Willingness to accept lower gaps; the required gap is divided by this value |
| `lcImpatience` | 0 | Modifies lcAssertive/lcPushy. The docs table lists it for **SL2015 only**. |
| `lcSigma` | 0.0 | Lateral positioning imperfection |
| `--lanechange.duration` | 0 (instantaneous) | Simple continuous lane-change model: constant lateral speed over the given time |

---

## 3. Model literature with explicit outflow < maximum flow

- **IDM, Treiber, Hennecke & Helbing 2000** (PRE 62:1805; arXiv cond-mat/0002177) [FT]:
  - standard set: v0 = 120 km/h, **T = 1.6 s, a = 0.73 m/s², b = 1.67 m/s², s0 = 2 m, δ = 4**, l = 5 m;
  - for this set "Q_max ≈ Q_out", i.e. **no capacity drop**. Q_out = 1,689 veh/h at T = 1.6 s;
  - Q_max − Q_out grows as T decreases ("traffic becomes more unstable"), and stability is mainly set by a, b and T (lower a is less stable). A drop needs an unstable regime, s1 > 0, or other extensions.
- **HDM, Treiber, Kesting & Helbing 2006** (Physica A 360:71-88; arXiv cond-mat/0404736) [FT]:
  - reaction time T′, estimation errors V_s = 5 % and r_c = 0.01 s⁻¹, correlation time τ = 20 s, anticipation n_a = 1-7. IDM base: T = 1.1-1.5 s, a = 1 m/s², b = 1.5 m/s², s0 = 2 m;
  - for n_a = 1, a 100-vehicle platoon is string-stable up to **T′ ≈ 0.8 s**. Larger T′ gives oscillations, and finally crashes beyond a second threshold;
  - the paper maps congested-state phases. **It does not quantify a capacity drop.**
- **VDT, Treiber, Kesting & Helbing 2006** (arXiv physics/0508222) [PART]: time gaps that grow with speed variance explain the drop. Not available in SUMO.
- **EIDM origin, Salles, Kaufmann & Reuss 2020**, SUMO User Conf. (SCP 1, doi 10.52825/scp.v1i.95) [FT]:
  - EIDM = IIDM + HDM action points/estimation errors + CAH coolness + drive-off correction;
  - validated **only on urban drive-off at a signalised intersection** (Stuttgart, SUMO 1.0.1, step 0.1 s);
  - Table 2 lists four EIDM vehicle sets:
    - length 3 / 4 / 4.5 / 5 m;
    - accel = decel 2.4 / 2.7 / 3.0 / 3.5 m/s²;
    - tau 1.2 / 1.1 / 1.0 / 0.9 s;
    - treaction 0.5 / 0.5 / 0.4 / 0.4 s;
    - **δ = 2**; minGap mean 2.5 m (2-3); speedFactor mean 1.1, s.d. 0.2 (0.9-1.4);
  - Table 3 lists the EIDM-specific parameters: tpreview 4, tPersEstimate 10, tPersDrive 3, sigmagap 0.1, sigmaleader 0.02, **sigmaerror 0.1**, ccoolness 0.99, taccmax 1.2, Mflatness 2, Mbegin 0.7, jerkmax 3;
  - **the paper says nothing about capacity drop.**
- **Yuan, Knoop & Hoogendoorn 2016/2017** (TRR 2560; Transp. Sci. 51(3):852-862) [FT, accepted manuscripts]:
  - inter-driver acceleration spread (U[0.5, 2] m/s²) cuts discharge only to ≈6,522 veh/h, against 5,000 observed for 3 lanes;
  - an **extended reaction time** reproduces the empirical speed-discharge relation, with t_ex = 0.195·max(0, 1 − v_j/v_max) s and no drop above ≈63 km/h;
  - their conclusion: modelling reaction time matters more than modelling acceleration.
- **Yuan, Laval, Knoop, Jiang & Hoogendoorn 2019** (Transportmetrica B 7(1)) [PART]: stochastic desired acceleration (geometric Brownian motion) gives a drop of ≈22 % at v_j = 0 for σ̃² = 0.06. This is not a SUMO model.
- **Laval & Daganzo 2006** (TR-B 40:251-264) [VERIFY, not opened]. Its mechanism is described on Daganzo's web page [DOC-like, read]: lane changers with bounded acceleration create voids at a lane drop, and the discharge drops by ≈10 %.
- **traffic-simulation.de (Treiber)** [read]: the demo uses a = 0.3 m/s² to provoke stop-and-go; "Realistic values are 0.8 to 2.5 m/s²".

---

## 4. Conclusion

### 4a. Is there a published demonstration of a capacity drop in SUMO at a lane drop?
**No, I found none in any peer-reviewed or SUMO-conference source I could open.**
- The only explicit statements that a SUMO lane drop produces "jam outflow below the maximum flow" are a SUMO developer's mailing-list and GitHub replies (2024-2025) [DEV]. They are not peer-reviewed and give no numbers.
- The only peer-reviewed SUMO capacity-drop demonstration I read is a 50 km/h ring road with closures, using calibrated heterogeneous EIDM on a modified SUMO 1.16 (Salles et al. 2024). That is not a lane drop and not a motorway.
- The ANNSIM 2025 SUMO lane-drop paper is [VERIFY].

The mechanism literature agrees on one point:
- high-acceleration, string-stable car following with instantaneous, frictionless merging (which is what SUMO's default zipper gives) yields outflow ≈ maximum flow (Krauß 1998; Treiber et al. 2000; GitHub #6150);
- a drop needs friction at the merge (lane-change voids, slower passage) or delayed or noisy acceleration out of the queue (reaction time, noise).

### 4b. Ranked discrete candidates (each fixed before data; do not tune within a candidate)

**C1: zipper with late merge start.** Same network and EIDM types; set `visibility="20"` on the zipper `<connection>`s of the lane drop.
- *Source:* Erdmann [DEV] 2024-07-16 and #15951; attribute semantics in PlainXML [DOC]; #6150.
- *Expected effect:* the queue reaches the merge and vehicles pass it slowly, so the outflow falls toward the jam outflow of the CF model. The size is unknown. With EIDM's high default acceleration (2.6 m/s²), the jam outflow may itself be close to the maximum flow, so the drop could be small.
- *Risks:*
  - emergency braking at a late zipper (#15224; fixed for 1.22.0, but count `emergencyBraking`/collisions);
  - the developer says the distance spans "any point in the continuum", so it is a knob. Pre-register **20 m only**; no sweep.

**C2: SUMO's "usual" lane drop, no zipper.** The dropped lane has no outgoing connection (dead end), with forced LC2013 changes at default LC parameters.
- *Source:* Motorways doc [DOC]; #6553 [DEV] reports throughput 25 % below the zipper when cooperation is reduced to balance the lanes.
- *Expected effect:* friction from the merge and lane changes (the Laval-Daganzo-type mechanism) and lane imbalance. The flow on the dropped lane is higher by default. The drop is plausible but may overshoot: 25 % against 7-10 % in the field at lane drops.
- *Risks:*
  - blocking and stopped vehicles at the lane end;
  - teleports (`time-to-teleport`);
  - a strong upstream lane imbalance;
  - sensitivity to the `lcCooperative*` family. Pre-register the defaults only.

**C3: EIDM with the published Salles et al. 2020 human-driver set.**
- *Values:* the four vehicle sets of Table 2, in equal shares:
  - accel = decel 2.4 / 2.7 / 3.0 / 3.5 m/s²;
  - tau 1.2 / 1.1 / 1.0 / 0.9 s;
  - treaction 0.5 / 0.5 / 0.4 / 0.4 s;
  - delta 2; minGap 2.0-3.0 m (mean 2.5);
  - Table 3: sigmaerror 0.1, sigmagap 0.1, sigmaleader 0.02, tPersDrive 3, tPersEstimate 10, ccoolness 0.99, taccmax 1.2, Mflatness 2, Mbegin 0.7, jerkmax 3, tpreview 4.
  - Keep the corridor's motorway speedFactor distribution, not the urban 1.1 ± 0.2.
- *Source:* the paper that defines EIDM [FT]. Salles et al. 2024 report a capacity drop with *calibrated heterogeneous* EIDM [PART].
- *Expected effect:* heterogeneity, δ = 2 and a 2.5× larger driving error than the source default should make discharge noisier and lower. The direction is likely; the magnitude is unknown.
- *Risks:*
  - the parameters are urban (drive-off), not calibrated on motorways;
  - the drop may still be ≈0;
  - shorter vehicles (3 m) raise capacity. Fix lengths to the corridor's values and disclose it;
  - platform-dependent `randNorm` (#8921).

**C4: Krauss in Krauß's low-acceleration regime** (replaces EIDM for HDVs).
- *Values:* `carFollowModel="Krauss" accel="1.5" decel="4.5" tau="1.0" sigma="0.8" sigmaStep="1"`.
- *Source:*
  - a = 0.2 (×7.5 m/s²) and b = 0.6 (×7.5 m/s²) from Krauß 1998 §5.5, where the drop appears and grows with ε [PART];
  - sigma 0.8 is Erdmann's [DEV] threshold for spontaneous jams;
  - `sigmaStep=1` matches the thesis's 1 s update [DOC].
- *Expected effect:* a hysteretic, metastable fundamental diagram with outflow below maximum flow on any road, not only at the lane drop.
- *Risks:*
  - changes the whole HDV model (the EIDM design is lost);
  - high noise lowers the free-flow capacity and creates spontaneous jams away from the bottleneck;
  - sigma 0.8 is not a calibrated value;
  - accel 1.5 is below the realistic 0.8-2.5 band's typical mid-range;
  - the ε at which the drop vanishes needs [VERIFY] from Fig. 5.26.

**Not ranked:**
- *EIDM with larger `treaction`* (HDM T′ ≤ 0.8 s for string stability; Yuan's reaction-time mechanism). No source gives an EIDM value for a motorway drop, and EIDM action points are not the HDM's delay-differential reaction time.
- *`--lanechange.duration`* (highD discretionary lane-change durations average ≈7.6-7.8 s; Li, Yang & Pan, arXiv 2108.06640 [PART], definition-dependent). No source shows that it yields a drop in SUMO.
- *IDM with Treiber 2000 parameters.* The paper itself shows Q_max ≈ Q_out.

**Suggested protocol (for the author to decide).**
- Pre-register the baseline plus C1-C4 as discrete arms.
- Use calibration seeds only, with the Cassidy-Bertini pre-queue vs QDF measure.
- Pre-register a field band before running, e.g. 5-15 % with a lane-drop centre of ≈7-10 % (Zhang & Levinson 2004; Cassidy & Bertini 1999).
- Pre-register the safety screens: 0 collisions and an emergency-braking count.
- Pre-register the selection rule: the highest-ranked candidate inside the band.
- Disclose all arms.

---

## Sources (opened unless marked)
1. SUMO docs, EIDM page: https://sumo.dlr.de/docs/Car-Following-Models/EIDM.html [DOC]
2. SUMO docs, Definition of Vehicles (parameter tables): https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html [DOC]
3. SUMO source `MSCFModel_EIDM.cpp`, `.h`, `SUMOXMLDefinitions.cpp` @ v1_27_1: https://github.com/eclipse-sumo/sumo/tree/v1_27_1/src [DOC]
4. SUMO docs: Vehicle_Type_Parameter_Defaults, Simulation/RoadCapacity, Simulation/Intersections, Networks/PlainXML, Simulation/Motorways, Simulation/SublaneModel, Car-Following-Models/index (all under https://sumo.dlr.de/docs/) [DOC]
5. sumo-user threads: msg03961/03979 (2019), msg05079-05090 (2019), msg09846 (2021), msg14209/14212 (2024): https://www.eclipse.org/lists/sumo-user/ [DEV]
6. GitHub eclipse-sumo/sumo issues #6150, #6553, #15224, #15951, #16146, #16198, #17724, #17841 [DEV]
7. Salles, Kaufmann, Reuss 2020, SUMO User Conf.: https://eclipse.dev/sumo/documents/2020/SUMO2020_paper_28.pdf (doi 10.52825/scp.v1i.95) [FT]
8. Salles, Oswald, Reuss 2024, arXiv 2408.03722 [PART]
9. Treiber, Hennecke, Helbing 2000, arXiv cond-mat/0002177 (PRE 62:1805) [FT]
10. Treiber, Kesting, Helbing 2006, arXiv cond-mat/0404736 (Physica A 360:71) [FT]
11. Treiber, Kesting, Helbing 2006, arXiv physics/0508222 (PRE 74:016123) [PART]
12. Krauß 1998, DLR-Forschungsbericht 98-08 (copy at https://eclipse.org/lists/sumo-dev/pdfxJQThiZzWZ.pdf; provenance of the copy not verified) [PART]
13. Zhang & Levinson 2004, TRR 1883: https://conservancy.umn.edu/server/api/core/bitstreams/d452c120-6059-418a-abaf-ef30d35f7373/content [FT]
14. Yuan, Knoop, Hoogendoorn 2015, TRB poster: https://repository.tudelft.nl/file/File_ace3c1b7-8d24-4291-a736-b7205f7eb09a [FT]
15. Yuan, Knoop, Hoogendoorn 2016 TRR 2560 (AAM): https://repository.tudelft.nl/file/File_4d1189a5-c875-4742-a595-baaea9e94d14 [FT]; 2017 Transp. Sci. (AAM) File_c36d1ee7-… [PART]
16. Yuan, Laval, Knoop, Jiang, Hoogendoorn 2019, Transportmetrica B: File_727f5568-… [PART]
17. Cassidy & Bertini 1999 abstract: https://ideas.repec.org/a/eee/transb/v33y1999i1p25-42.html [ABS]
18. Chung, Rudjanakanoknad, Cassidy 2007 abstract: https://ideas.repec.org/a/eee/transb/v41y2007i1p82-95.html [ABS]
19. Daganzo lane-drop page: http://faculty.ce.berkeley.edu/daganzo/Research/LaneDrop/ [read]
20. McTrans HCS page: https://mctrans.ce.ufl.edu/?p=874 [ABS]
21. traffic-simulation.de IDM info: https://traffic-simulation.de/info/info_IDM.html [read]
22. De Souza et al. 2018, Procedia CS 130 (UCI ITS summary page) [ABS]
23. Li, Yang, Pan, arXiv 2108.06640 [PART]
24. Ni et al. 2026, arXiv 2606.09282 [PART]
25. [VERIFY] Bertini & Leal 2005; Srivastava & Geroliminis 2013; Oh & Yeo 2012 and 2015; Laval & Daganzo 2006; ANNSIM 2025 (IEEE 11118854); Kesting & Treiber 2008; HCM 7th ed.
