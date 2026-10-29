# Nonlinear mechanisms: drivers, vehicles, exogenous conditions, actuators and sensing (v0)

Sweep date: 2026-10-29. Scope: mechanisms 1 to 7 of the brief, for the bn4x plant (SUMO 1.27.1).

Access tags:
- FT: full text opened; the cited section or table was read (not always the whole paper).
- ABS: only the abstract or a catalogue summary was opened.
- DERIVED: my own arithmetic on sourced numbers.
- [VERIFY]: not confirmed from a primary source I opened.

Search-engine snippets are not used as sources. Items that I saw only in snippets are listed in the gaps section.

## Summary

Ranked by strength of field evidence and by relevance to our actuators (VSL for humans, meters, per-CAV speed commands):

1. **VSL compliance is partial, additive and enforcement-driven.** Without enforcement, free speeds sit about 15 km/h above the posted limit; with radar enforcement compliance is high, but the effect is local to the gantry [4]. Compliance falls when the displayed limit is far below the current speed [3]. In SUMO, compliance is perfect and multiplicative by default (speedFactor) [31]. This is the largest gap between our plant and the field for the VSL actuator.
2. **Low VSL cannot meter the mainline.** Even with high compliance, 40 km/h still carried 1942 veh/h/lane for 17 min [4]. Any controller that uses VSL as a flow restrictor gets an inflated gain in a model that ignores this.
3. **Incident capacity is far below the lane share.** The remaining lanes work at about 54 % efficiency when a lane is blocked; rubbernecking alone cuts discharge by about 31 % [1]. For our 4-lane and 2-lane sections, HCM tables give 8 to 17 points more remaining capacity than this efficiency implies (DERIVED, [13]). Our crash process exists, but its residual capacity is not yet checked against these numbers.
4. **Weather moves capacity and speed together.** Capacity −2 % to −22 % by rain or snow intensity, free speed −2 % to −19 %, demand −2 % to −14 % in rain [12][14][16]. A fixed setpoint (for example the ALINEA critical occupancy) becomes wrong on wet days.
5. **Sensing is unreliable.** In California, 35 % to 40 % of loop detectors were "failed" on a typical day (District 11: 5 %) [28]. Failure types are known (stuck, hanging, chattering, cross-talk) [29].
6. **CAV effects are nonlinear in penetration.** Simulated CACC capacity grows quadratically with penetration [22][23]. All seven tested production ACC systems were string unstable in the field [24]. An IDM "ACC" may be more stable than real ACC.
7. **Meter compliance and rate limits.** Ramp-meter violation is about 10 % in Phoenix and under 2 % in Seattle (agency reports) [8]. One-car-per-green meters saturate at 800 to 900 veh/h/lane [26].
8. Weaker evidence: time gaps about twice as long in congestion (one Dutch site) [11]; demand responds to metering (−9 % freeway volume without meters) [9]; human drivers shorten headways next to CAV platoons (simulator only, and no effect in mixed traffic at 43 % CAV) [25]; darkness lowers speed by about 5 km/h [17].

## 1. Compliance with VSL and ramp meters

### Claims

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Free-flow speed at an unenforced VSL gantry relative to the posted limit | about 15 km/h above the limit | Spain, B-23 Barcelona, KP 6.15 | [4] §3 (site description) | FT |
| Effect of radar enforcement at the gantry | "high level of speed limit compliance"; effects concentrated around the enforcement point | Spain, B-23, KP 4.73 | [4] §3 and data-processing text | FT |
| Low compliance case reported in the literature | 79 km/h measured at a 60 km/h limit (Knoop et al. 2010) | Netherlands | [4] Table 1, note h (secondary) | FT |
| Advisory VSL (Smulders 1990): capacity effect | +1 % to 2 %, low compliance | Netherlands | [4] Table 1 (secondary) | FT |
| Highest flow sustained under a 40 km/h limit with enforcement | 1942 veh/h/lane for 17 min; occupancy 32.0–34.7 % | Spain, B-23 | [4] §4, abstract | FT |
| Conclusion on VSL as mainline metering | metering capability of low limits is limited; strict enforcement needed for compliance | Spain, B-23 | [4] conclusions, item iv | FT |
| Compliance with dynamic speed limits without enforcement devices | "very limited" | Spain | [5] abstract | ABS |
| Static-limit free speeds, Toronto freeway (QEW), 100 km/h limit | mean 119 km/h, SD 13.1 km/h, only 5 % at or below the limit | Canada | [2] p. 10 | FT |
| Static-limit free speeds, Western Australia, 100 km/h roads (Giles 2004) | mean 93.8 km/h, 70 % at or below the limit | Australia | [2] p. 10 (secondary) | FT |
| VSL safety benefit versus compliance (PARAMICS simulation) | benefit grows non-linearly; largest step from Low to Moderate compliance; travel time cost very large at Very High | Canada (simulation) | [2] "Interpretation of Results", p. 16–17 | FT |
| Advisory work-zone VSL, I-494: driver compliance measure | correlation 20 % to 60 %; weaker when the posted value is far below the approach speed | USA, Minnesota | [3] abstract and "Assessment of Driver Compliance" | FT |
| Same system: 1-min maximum speed difference | −25 % to −35 % (6–8 a.m.) | USA, Minnesota | [3] abstract | FT |
| Same system: downstream throughput 6–7 a.m. | +7.1 % (from 3,595) | USA, Minnesota | [3] results, Fig. 10 | FT |
| E18 Finland (advisory) compliance | up to 76 % | Finland | [6] Ch. 4 | FT |
| E4/E22 Sweden speed change under VSL | −5 to −15 km/h | Sweden | [6] Ch. 4 | FT |
| I-270/I-255 Missouri (mandatory signs) | compliance "surprisingly low" | USA | [6] Ch. 4 | FT |
| US 27 Florida (enforced by Highway Patrol) | high compliance, attributed to enforcement | USA | [6] Ch. 4 | FT |
| SPECIALIST field test, A12, 14 km, Sep 2009–Feb 2010 | shock waves resolved in nearly 80 % of activations for shock waves; 40–50 % for other jam types | Netherlands | [7] abstract | ABS |
| Upper bound if all vehicles follow VSL (simulation) | bottleneck capacity +5 % to 18 %; delay −10 % to 35 % | USA (simulation) | [22] §3 (b) | FT |
| Ramp meter violation rate, Phoenix, normal operation | about 10 % | USA, Arizona | [8] Phoenix section (ADOT interview) | FT |
| Ramp meter violation, Phoenix, with an underused HOV bypass | over 45 % | USA, Arizona | [8] same page | FT |
| Ramp meter violation, Seattle (WSDOT) | under 2 % | USA, Washington | [8] Seattle section | FT |
| Good enforcement can bring violation down to | about 5 % (Newman et al.) | USA | [8] §7.0 | FT |
| Long ramp delays raise violations | hypothesis only; "no studies have been performed to prove" | USA | [8] §7.0 | FT |
| Twin Cities ramp delays | as high as 20 min, yet violation "low" | USA, Minnesota | [8] §5 | FT |

### Matters for control
- The VSL actuator gain (speed change per km/h of displayed limit) is below 1 and depends on enforcement, on how far the limit is below current speeds, and on location relative to the gantry [3][4]. A controller tuned on a perfectly compliant plant over-estimates its own authority.
- The response saturates: very low limits do not cut flow much [4]. Strategies that rely on VSL as a mainline meter (low limits upstream of a bottleneck) lose most of their effect.
- Meter violation adds an uncontrolled inflow. If violation rises with waiting time (plausible, unproven [8]), the meter loses authority exactly when queues are long.

### SUMO path
- Today, desired speed = speedFactor × lane limit; with speedFactor > 1 vehicles exceed the limit in proportion [31]. Field data instead show an additive offset (about +15 km/h unenforced) [4].
- Proposal: give each human driver a compliance class at insertion (compliant, offset, ignore). When a vehicle enters a VSL lane, set its target with TraCI: `vehicle.setMaxSpeed(min(own free speed, limit + offset_i))`; for "ignore", keep the pre-VSL target. Draw `offset_i` from a distribution with mean near +15 km/h unenforced and near 0 at an enforced gantry [4].
- Make the offset larger when (approach speed − limit) is large, to reproduce the falling correlation in [3].
- VSS objects change the lane speed for all vehicles on the lane at once [32]. The docs do not say whether drivers react only at the sign. Check in a one-lane test whether vehicles upstream anticipate the new limit [VERIFY].
- Meter violation: `jmDriveAfterRedTime` only lets vehicles pass a red that turned red less than a threshold ago [31]. It does not model deliberate running. For deliberate running, select a share of vehicles and switch their TraCI speed mode to ignore red lights [VERIFY the speed-mode bit].

### Calibration target
- Speed distribution per displayed limit: mean free speed about limit + 15 km/h without enforcement [4]; Toronto static case 119 km/h at 100 km/h, SD 13.1 km/h [2].
- Compliance correlation 0.2 to 0.6 for an advisory system [3].
- Violation share: run 0 %, 2 %, 10 % as sensitivity cases [8].

### In our plant
- Already in: per-vehicle speedFactor (unknown whether it varies by VSL state).
- Missing: additive and enforcement-dependent compliance; level-dependent compliance; red-light violation at the meter (unknown, probably off since the default `jmDriveAfterRedTime` is −1 [31]).

## 2. Driver adaptation over time and conditions

### Claims

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Modal time headway in congested versus free traffic (single-vehicle data) | larger by a factor of about 2 | Netherlands, A9 Haarlem–Amsterdam | [11] abstract and §I | FT |
| Interpretation offered by the authors | drivers increase safety time gaps when local speed variance is high; this reproduces the capacity drop | model plus A9 data | [11] §I–II | FT |
| Twin Cities meter shutdown: freeway volume | −9 % | USA, Minnesota, 430 meters off | [9] study page | FT |
| Same: freeway travel time | +22 % | USA, Minnesota | [9] | FT |
| Same: freeway speed | −7 % | USA, Minnesota | [9] | FT |
| Same: travel-time reliability | −91 % | USA, Minnesota | [9] | FT |
| Same: crashes (seasonally averaged) | +26 % | USA, Minnesota | [9] | FT |
| Freeway throughput gain from metering, this evaluation | +14 %; 12 other studies average 18 % (range 0–86 %) | USA | [8] Table K.2 text | FT |
| Demand response to metering | short non-work trips deferred to unmetered times; peaks spread for work trips | USA, Minnesota | [10] abstract | ABS |
| Post-study rule on ramp waits | no more than 4 min on local ramps | USA, Minnesota | [9] | FT |
| Weather-induced demand change (literature table) | rain −2 % to −14 %, majority −2 % to −5 %; light rain +2.3 %, heavy rain −7.7 % (Netherlands, Van Stralen 2014) | multi-country | [16] §2, Table 1 | FT |

### Matters for control
- If time gaps grow with time spent in congestion, discharge capacity falls the longer a queue lasts. This makes early action worth more than late action. It also means the plant gain depends on history.
- Demand is elastic to metering delays [9][10]. A controller that holds long queues will see lower or shifted demand over days. Gains measured with fixed demand overstate or understate real benefit, depending on what is counted.

### SUMO path
- Time-gap adaptation: track for each human vehicle the time spent below a speed threshold; scale `tau` with `vehicle.setTau` up to a factor, and relax it back in free flow. Krauss has no native memory term (no source found for one in SUMO).
- Careful: our plant already has an 18 % capacity drop. Adding this mechanism on top may double-count. Use it as an alternative cause of the drop, re-calibrated to the same drop, not as an extra.
- Lane-change impatience exists as `lcImpatience` and `lcTimeToImpatience`, listed for SL2015 only [31]. Whether LC2013 honours them is [VERIFY].
- Day-to-day demand: an outer loop between simulated days. Shift a share of departures away from hours with high experienced entry delay (peak spreading [10]). The rerouting device [35] only helps if the network has alternative routes; bn4x is a single corridor (unknown if alternatives exist).

### Calibration target
- Headway distribution in congestion about twice the free-flow mode [11] (one site; treat as a check, not a target).
- Demand response: total freeway volume difference with and without metering of the order of 9 % [9] (one region, one shutdown; sensitivity only).

### In our plant
- Already in: none known.
- Missing: memory or frustration effects, day-to-day demand response, learning of VSL patterns (no field source found).

## 3. Weather, visibility and lighting

### Claims

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| HCM 2010 Exh. 10-15: capacity reduction, rain ≤0.10 in/h | 2.01 % (range 1.17–3.43) | USA | [12] Table 33 | FT |
| Same: rain 0.10–0.25 in/h | 7.24 % (5.67–10.10) | USA | [12] Table 33 | FT |
| Same: rain >0.25 in/h | 14.13 % (10.72–17.67) | USA | [12] Table 33 | FT |
| Same: snow >0.50 in/h | 22.43 % (19.53–27.82) | USA | [12] Table 33 | FT |
| Same: visibility <1 mi to <0.25 mi | 9.67 % to 11.67 % (one site) | USA | [12] Table 33 | FT |
| SHRP 2-L08 CAF at FFS 60 mph: medium rain / heavy rain | 0.93 / 0.88 | USA | [12] Table 34 | FT |
| SHRP 2-L08 speed factor at FFS 60 mph: medium rain / heavy rain | 0.95 / 0.93 | USA | [12] Table 34 | FT |
| SHRP 2-L08 CAF at 60 mph: heavy snow / low visibility | 0.78 / 0.90 | USA | [12] Table 34 | FT |
| HCM 7th ed. CAF table reproduces the same values | e.g. 65 mph: medium rain 0.92, heavy rain 0.86 | USA | [15] Table 15-4 (secondary) | FT |
| Our 100 km/h free speed in mph | about 62 mph, so the 60 and 65 mph columns bracket it | n/a | from [12] columns | DERIVED |
| FHWA empirical study: capacity in light rain and rain | −10 % to −11 % | USA (Minneapolis–St Paul, Baltimore, Seattle) | [14] Table ES.1 | FT |
| Same: free-flow speed, rain about 1.6 cm/h | −6 % to −9 % | USA | [14] Table ES.1 | FT |
| Same: capacity in light snow | −12 % to −20 % | USA | [14] Table ES.1 | FT |
| Same: jam density | no weather effect found | USA | [14] text | FT |
| Same: Twin Cities vs Baltimore speed reduction in snow | 19 % vs 5 % | USA | [14] text | FT |
| Literature range, rain capacity | −4 % to −30 %; most observations −5 % to −15 % | multi-country | [16] §2 and Table 1 | FT |
| Netherlands, rain capacity (Calvert and Snelder 2013) | −1.9 % per mm/h, up to 5 mm/h | Netherlands | [16] Table 1 (secondary) | FT |
| Netherlands, light / heavy rain capacity (Van Stralen 2014) | −4 % to −9 % (avg 6 %) / −4 % to −11 % (avg 8 %) | Netherlands | [16] Table 1 (secondary) | FT |
| Dense mist (Hoogendoorn et al. 2010) | speed reductions up to 30 % | Netherlands | [16] §2 (secondary) | FT |
| Germany: rain lowers speed (Brilon and Ponzlet) | −9.5 km/h (2 lanes), −12 km/h (3 lanes) | Germany | [16] Table 1 (secondary) | FT |
| Germany: darkness lowers average speed | about −5 km/h; wet road about −10 km/h; capacity loss "must be expected" but not quantified | Germany, 15 sites × 3 years | [17] abstract | ABS |
| Lighting installed on Dutch A50 | no change in speeds or estimated capacity in free flow | Netherlands | [18] abstract | ABS |

### Matters for control
- Weather shifts the critical density and capacity at the same time [14]. ALINEA and PI-ALINEA hold a fixed occupancy setpoint; on a wet day that setpoint is too high, so the controller lets the bottleneck break down. VSL and MTFC thresholds have the same problem.
- Demand often drops in heavy rain [16], which partly offsets the capacity loss. Ignoring demand change exaggerates wet-day congestion.

### SUMO path
- Draw a weather state per hour from a climate table (UK data needed: see gaps). Map it to CAF and speed factor from [12] (60–65 mph columns, DERIVED).
- Speed factor: scale each human's target speed (`vehicle.setSpeedFactor` or the lane limit).
- Capacity factor: scale human `tau` (and possibly `minGap`) with `vehicle.setTau` until the measured queue discharge matches the CAF. Jam density should stay unchanged [14], so do not scale vehicle length.
- Road friction: libsumo 1.27.1 has `lane.setFriction` (local API check). Whether Krauss or IDM use friction is [VERIFY]; do not rely on it.
- CAVs: no source found on ACC/CACC time gaps or disengagement in rain. Keep CAV settings unchanged and flag it.
- Demand: scale hourly demand in rain by −2 % to −8 % (sensitivity range, from [16]).

### Calibration target
- Queue discharge rate per weather state within ±1 percentage point of the CAF; free speed within ±1 point of the speed factor [12].
- Check: jam density unchanged [14].

### In our plant
- Already in: none.
- Missing: weather states, visibility, darkness. Darkness has weak evidence (speed only, no capacity change found for lighting) [17][18]; low priority.

## 4. Incidents and rubbernecking

### Claims

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Remaining capacity, shoulder incident (3-lane motorways) | mean F = 0.72, SD 0.09 | Netherlands (A1, A2 and others; 90 incidents in total) | [1] Table 5 | FT |
| Remaining capacity, 1 of 3 lanes blocked | F = 0.36, SD 0.14 | Netherlands | [1] Table 5 | FT |
| Remaining capacity, 2 of 3 lanes blocked | F = 0.18, SD 0.12 | Netherlands | [1] Table 5 | FT |
| Rubbernecking in the non-incident direction | F = 0.69, SD 0.08 (29 queues) | Netherlands | [1] Table 5, §5 | FT |
| Efficiency of the remaining lanes when 1 or 2 lanes are blocked | η = 0.54 | Netherlands | [1] Table 5, §5 | FT |
| Share of incidents that produced a queue | shoulder 9 %, 1 lane 43 %, 2 lanes 65 %, rubbernecking 7 % | Netherlands | [1] Table 3 | FT |
| Older values in the literature, 1 of 3 blocked | 0.35 to 0.53 (Goolsby 1971 to Smith 2003) | USA and Netherlands | [1] Table 1 (secondary) | FT |
| HCM 2010 Exh. 10-17, 2-lane direction | shoulder disablement 0.95, shoulder accident 0.81, 1 blocked 0.35, 2 blocked 0 | USA | [13] Table 40 | FT |
| HCM 2010 Exh. 10-17, 4-lane direction | 0.99, 0.85, 1 blocked 0.58, 2 blocked 0.25, 3 blocked 0.13 | USA | [13] Table 40 | FT |
| SHRP 2-L08 factor on the open lanes, 4-lane, 1 blocked | 0.77 | USA | [13] Table 41 | FT |
| Our 4-lane section, 1 lane blocked, using η = 0.54 | F ≈ 0.54 × 3/4 = 0.41 (HCM: 0.58) | n/a | from [1] and [13] | DERIVED |
| Our 2-lane section, 1 lane blocked, using η = 0.54 | F ≈ 0.27 (HCM: 0.35) | n/a | from [1] and [13] | DERIVED |
| Our 1-lane section, 1 lane blocked | F = 0 (full closure) | n/a | geometry | DERIVED |

### Matters for control
- A blocked lane cuts capacity by much more than its lane share [1]. The bottleneck moves to the incident site. A controller tuned for the recurrent lane drop now protects the wrong location.
- Spread is large (SD 0.12–0.14 of F) [1]. A fixed-gain controller faces a random capacity each time.
- Rubbernecking creates a second, transient bottleneck without any lane loss (F = 0.69) [1].

### SUMO path
- Our crashes already block a lane for 30–60 min. Check the remaining-lane discharge against η = 0.54 and HCM.
- If SUMO gives too high a discharge, add a "passing zone" near the site: lower lane speed (`lane.setMaxSpeed`) and raise `tau` for vehicles inside it, until η matches. The zone length is not sourced [VERIFY]; vary it.
- Rubbernecking without blockage: add exogenous events with F about 0.69 on all lanes for the duration of a crash elsewhere (bn4x has no opposite carriageway; treat as an exogenous event).

### Calibration target
- Discharge at the incident site: F within the band given by η = 0.54 ± 0.14 [1] and the HCM value [13] for the same lane count.
- Rubbernecking: F = 0.69 ± 0.08 [1].

### In our plant
- Already in: crash-driven lane blockages, 30–60 min, P(≥1 crash/day) = 25 % (from the brief).
- Unknown: whether the residual capacity matches [1] or [13].
- Missing: rubbernecking without blockage; shoulder incidents.

## 5. Heavy vehicles

### Claims

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| PCE, rural 4-lane Interstate, 0 % grade, 0.5 mi | 2.2 to 4.0 (by truck length 150–250 ft and 40–120 lb/hp) | USA (CTSW simulation) | [19] Table 30 | FT |
| PCE, same road, 3 % grade, 0.75 mi | 9.0 to 14.7 | USA (CTSW simulation) | [19] Table 30 | FT |
| PCE, urban congested freeway, 0 % grade | 1.5 to 3.0 | USA | [19] Table 31 | FT |
| Minimum speed of a 130,000-lb truck on a 6 % grade | 20 mph | USA | [19] text | FT |
| SUMO default trailer class | length 16.5 m, accel 1.0 m/s², decel 4 m/s², maxSpeed 130 km/h, speedDev 0.05 | n/a | [21] | FT |
| Heavy-vehicle share at 27 Twin Cities bottlenecks | 0.7 % to 8.8 % (2000 data) | USA, Minnesota | [20] data section | FT |
| Flow drop after queue forms at these bottlenecks | 2 % to 11 %, mean about 5 %, SD 2 % | USA, Minnesota | [20] results | FT |

### Matters for control
- On grades, a truck uses several times the road space of a car [19]. Capacity then depends on truck share by hour, which changes over the day. A fixed setpoint does not track this.
- Slow-accelerating trucks lengthen the discharge from a queue. This matters most for a meter across all lanes: trucks leaving a red stop line set the effective discharge.

### SUMO path
- Grade: give edges z-coordinates only if the real site has grades (unknown). Whether SUMO car-following models reduce acceleration on slopes is [VERIFY]. A safe path is TraCI: lower `accel` and `maxSpeed` for trucks on upgrade edges, from power-to-weight.
- Truck lane restrictions: SUMO lane permissions (`disallow` on the left lanes). No field number on the effect was opened (see gaps).
- Platooning: not in scope for bn4x now; evidence opened was simulation only (see gaps).

### Calibration target
- Truck share by hour from the site counts; PCE on flat urban freeway 1.5–3.0 [19] as a plausibility check for the simulated truck effect on discharge.

### In our plant
- Already in: 7.5 % trucks, trailer class.
- Unknown: grades.
- Missing: truck lane restrictions, truck platooning, hourly variation of truck share (unknown).
- Note: our capacity drop (about 18 %) is above the Twin Cities range of 2–11 % [20]. Other sites may differ; the breakdown agent should check this.

## 6. CAV penetration effects

### Claims

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Mean time gap chosen by drivers with ACC (field test) | 1.55 s | USA (PATH test vehicles, public drivers) | [22] §2 (c) | FT |
| Lane capacity with ACC, 10 % to 100 % penetration (simulation with field gaps) | 2026 to 2093 veh/h/lane, about unchanged | USA (simulation) | [22] §2 (c) | FT |
| Mean CACC gap selections | 0.64 s (men) and 0.78 s (women), vs 1.43 and 1.68 s with ACC | USA (field test) | [22] §2 (f) | FT |
| Lane capacity at 100 % CACC | about 4000 veh/h/lane | USA (simulation) | [22] §2 (g) | FT |
| Capacity vs CACC share, mixed with manual cars | quadratic; lags at intermediate penetration | USA (simulation) | [22] §2 (g), Fig. 2 | FT |
| Later PATH models: capacity at 100 % CACC | 3080 veh/h/lane; about 63 % above 0 % | USA (simulation, calibrated) | [23] abstract and §results | FT |
| On-ramp disturbance effect on that capacity | up to −13 % | USA (simulation) | [23] abstract | FT |
| Production ACC string stability | all 7 tested 2018 models string unstable | USA, >1,200 miles of tests | [24] abstract | FT |
| Platoon test with identical ACC cars | 6 mph disturbance grew to 25 mph; last car disengaged ACC | USA | [24] abstract | FT |
| Human drivers next to CAV platoons, mixed traffic, 43 % CAV (simulator) | no significant difference from all-manual base | Netherlands (51 drivers) | [25] abstract | FT |
| Same, with a dedicated CAV lane | car-following THW 0.128 s shorter; merging gaps up to 12.7 % shorter | Netherlands (simulator) | [25] abstract and results (Model a) | FT |
| Drivers next to truck platoons with 0.3 s vs 1.4 s gaps (Gouy et al. 2014) | shorter THW, more time below 1 s | country not checked (simulator) | [25] §1 (secondary) | FT |
| Drivers following an automated vehicle (Rahmati et al., field) | drove closer than when following a human | country not stated in [25] | [25] §1 (secondary) | FT |

### Matters for control
- CAV benefits rise slowly at low penetration and fast at high penetration [22][23]. A controller tuned at one penetration is mistuned at another.
- If real ACC amplifies disturbances [24], per-CAV speed commands can create, not damp, waves. A plant with string-stable IDM CAVs makes CAV-based control look easier than it is.
- Human adaptation near AVs is small and simulator-only [25]. It should not drive design choices.

### SUMO path
- SUMO has ACC and CACC models based on Milanés and Shladover and on Xiao et al.; the docs warn of collisions at a 1 s step [34]. Our 0.1 s step is below that.
- Test string stability of our IDM CAV types with a platoon disturbance test; compare against the 6 → 25 mph amplification in [24]. Gunter et al. publish their data [24], which can be used to fit an "as sold" ACC type.
- Human adaptation near AVs: optional per-step TraCI rule (leader is CAV → `tau` −0.13 s), only as a sensitivity case [25].
- Driver State device can add perception errors to Krauss, IDM, ACC and CACC; ACC/CACC need `applyDriverState="1"` [33].

### Calibration target
- ACC mean time gap about 1.5 s [22]; CACC 0.6–0.8 s [22].
- Capacity vs penetration curve shape (quadratic) as a check [22][23].

### In our plant
- Already in: 50 % CAVs on IDM with ACC, CACC and ALKS-like gaps.
- Unknown: string stability of the IDM CAV types; CAV behaviour when the leader is human.
- Missing: string-unstable "as sold" ACC variant; human adaptation near AVs.

## 7. Actuators and sensing

### Claims

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Shortest practical one-car-per-green cycle | 4 s (1 s green, 1 s yellow, 2 s red) → 900 veh/h | USA, Texas | [26] p. 1 | FT |
| More reasonable cycle in the field | 4.5 s → 800 veh/h | USA, Texas | [26] p. 1 | FT |
| Two-cars-per-green (bulk) metering | 6–6.5 s cycle → 1100–1200 veh/h | USA, Texas | [26] p. 1–2 | FT |
| Dual-lane metering | 1600–1700 veh/h | USA, Texas | [26] p. 2 | FT |
| Queue management with ALINEA | a queue controller beat a common queue-override scheme in simulation and worked in the field | Greece/EU | [27] abstract | ABS |
| VSL step size in US deployments | mostly 5 mph steps; Washington table in 10 mph steps | USA | [6] Ch. 4 | FT |
| Max difference between adjacent VSL segments (OR 217) | 10 mph | USA, Oregon | [6] Ch. 4 | FT |
| VSL update periods | 20 s (I-285) to 5 min (Missouri) | USA | [6] Ch. 4 | FT |
| Loop sensors reported "failed" on any given day | 35 % statewide; District 4: 40 %, 7: 35 %, 11: 5 % (Oct–Dec 2005) | USA, California | [28] §2 | FT |
| Reliable sensor share on a typical day in 2005 | 60 % | USA, California | [28] summary | FT |
| Sensors that always failed in the study period | District 4: 24 %, 7: 16 %, 11: 3 % | USA, California | [28] findings | FT |
| Repair programme success for always-failed sensors | under 5 % | USA, California | [28] findings | FT |
| Loop failure types | stuck, hanging on/off, chattering, cross-talk, pulse breakup, intermittent | USA | [29] §2 (citing Payne et al. 1976) | FT |
| Loop sample period in PeMS | 30 s | USA, California | [29] §2; [28] §2 | FT |
| Probe penetration needed for speed estimates | 2–3 % of drivers with GPS phones | USA, I-880 (Mobile Century, 100 cars) | [30] abstract | FT |

### Matters for control
- Meter output saturates per lane [26]. Our meter spans all four lanes; per-lane cycle limits bound the lowest and highest rates, which makes the plant nonlinear at both ends.
- VSL steps of 5–10 mph and rate limits quantise the actuator [6]. A continuous controller output must be rounded, which adds a dead band.
- A controller fed by failed or stuck detectors acts on wrong data. With 5–40 % failed sensors per day [28], fault detection or imputation becomes part of the controller.

### SUMO path
- Meter: enforce min green, min red and cycle limits in the controller wrapper. Record the realised rate, not the commanded one.
- VSL: round commands to the step size; limit change per update and difference between neighbouring gantries.
- Detectors: SUMO E1 loops are exact. Add a fault layer between `getLastIntervalVehicleNumber` and the controller: per detector-day failure (Bernoulli, 5–40 % scenario range [28]), failure modes from [29], and a 30 s reporting delay [29].
- Probe data: CAVs already report position and speed; sample them at 2–3 % or more to test probe-only control [30].

### Calibration target
- Fault rates: sensitivity runs at 5 %, 20 %, 40 % failed detectors [28].
- Meter: realised max rate per lane at 800–900 veh/h for one-car-per-green [26] (only if our meter works this way; unknown).

### In our plant
- Already in: a meter across all lanes; detector faults and noise planned (from the brief).
- Unknown: meter cycle limits; VSL step size and rate limits.
- Missing: fault layer, reporting delay, probe sampling.

## Gaps

1. VSL spatial anticipation and response delay at gantries: no field source with numbers found.
2. Learning of VSL patterns over days, and driver frustration with long queues: no field source found.
3. Accepted merge gaps versus remaining acceleration-lane length (Marczak, Daamen and Buisson 2013, TR-C): not opened [VERIFY].
4. Ramp-meter compliance versus lane count, volume and metering rate (Geffen, Cottam, Haule, Wu 2025, TRR, DOI 10.1177/03611981251347599): not opened [VERIFY].
5. Lower and upper meter limits of 240 and 900 veh/h/lane attributed to the California Ramp Meter Design Manual: seen only in a snippet [VERIFY].
6. Papageorgiou, Kosmatopoulos, Papamichail 2008 (TRR 2047) on VSL effects on the flow-occupancy diagram, and Weikl, Bogenberger, Bertini 2013 (TRR 2380, A99): not opened [VERIFY].
7. Darkness and capacity: one TRR paper (DOI 10.3141/1646-01) reportedly found +2.5 % night capacity with lighting; not opened [VERIFY].
8. Truck share and capacity drop (TU Delft study), truck overtaking bans (FOSIM study) and truck platooning: not opened [VERIFY].
9. UK weather frequency by hour (rain intensity, fog) to drive a weather process: not searched yet.
10. Loop count and speed error magnitudes (noise level): no source opened.
11. ACC/CACC behaviour in rain or fog, and ACC disengagement rates: none found.
12. SUMO checks: VSS anticipation, slope effect on acceleration, friction effect on car-following, speed-mode bit for red-light running, LC2013 support for impatience [VERIFY in short tests].
13. Gouy et al. 2014 (TR-F 27: 264–273) primary text not opened; cited here via [25].

## Sources

1. Knoop, V., Hoogendoorn, S., Adams, K. (2009). Capacity reductions at incidents sites on motorways. EJTIR 9(4), 363–379. https://journals.open.tudelft.nl/ejtir/article/download/3318/3478
2. Hellinga, B., Mandelzys, M. (accepted 2010). Impact of driver compliance on the safety and operational impacts of freeway variable speed limit systems. ASCE J. Transportation Engineering (preprint). https://www.civil.uwaterloo.ca/bhellinga/publications/Publications/ASCE 2010 Impact of Driver Compliance on VSLS.pdf
3. Kwon, E., Brannan, D., Shouman, K., Isackson, C., Arseneau, B. (2007). Development and field evaluation of variable advisory speed limit system for work zones. TRR 2015, 12–18. https://www.dot.state.mn.us/trafficeng/workzone/doc/Var-Adv-SpeedSystem-WZ-Report.pdf
4. Soriguera, F., Martínez, I., Sala, M., Menéndez, M. (2017). Effects of low speed limits on freeway traffic flow. TR Part C 77, 257–274. https://upcommons.upc.edu/bitstreams/271525be-078b-4297-8eeb-c262e2f04b3e/download
5. Soriguera, F., Martínez, I., Menéndez, M. (2015). Experimenting with dynamic speed limits on freeways. TRB 94th Annual Meeting. https://upcommons.upc.edu/entities/publication/421270b9-8954-4cff-b005-96d6ee0a74f5
6. FHWA. Synthesis of Variable Speed Limit Signs, Chapter 4 Findings (FHWA-HOP-17-003, from the URL). https://ops.fhwa.dot.gov/publications/fhwahop17003/ch4.htm
7. Hegyi, A., Hoogendoorn, S.P. (2010). Dynamic speed limit control to resolve shock waves on freeways: field test results of the SPECIALIST algorithm. IEEE ITSC 2010, 519–524 (TRID record). https://trid.trb.org/view/1096490
8. Cambridge Systematics (2001). Twin Cities Ramp Meter Evaluation, Appendix K: Technical Memorandum, Secondary Research. https://www.dot.state.mn.us/rampmeter/pdf/appendices/k.pdf
9. MnDOT. Ramp meter study (web page). https://www.dot.state.mn.us/rampmeter/study.html
10. Zhang, L., Levinson, D. (2002). Estimation of demand response to ramp metering. Proc. ICTTS 2002, 674–681 (RePEc record). https://econpapers.repec.org/RePEc:nex:wpaper:rampmeterdemand
11. Treiber, M., Kesting, A., Helbing, D. (2006). Understanding widely scattered traffic flows, the capacity drop, platoons, and times-to-collision as effects of variance-driven time gaps. Published in Phys. Rev. E per the arXiv listing [VERIFY volume]; arXiv physics/0508222. https://arxiv.org/pdf/physics/0508222
12. FHWA. Guide for Highway Capacity and Operations Analysis of ATDM Strategies (FHWA-HOP-13-042, from the URL), Appendix A: Speed/Capacity for Weather. https://ops.fhwa.dot.gov/publications/fhwahop13042/appa.htm
13. Same guide, Appendix C (incidents). https://ops.fhwa.dot.gov/publications/fhwahop13042/appc.htm
14. FHWA (2006). Empirical Studies on Traffic Flow in Inclement Weather, Executive Summary (FHWA-HOP-07-073). https://ops.fhwa.dot.gov/publications/weatherempirical/sect0.htm
15. TxDOT. Design manual 15.4.4.2 Weather Events (reproduces HCM 7th ed. CAF). https://www.txdot.gov/manuals/des/tsp/chapter-15-transportation-system-management-and-op/15-4-performance-measurement/15-4-4-factors-affecting-travel-time-reliability/15-4-4-2-weather-events.html
16. Snelder, M., Calvert, S. (2016). Quantifying the impact of adverse weather conditions on road network performance. EJTIR 16(1), 128–149. https://journals.open.tudelft.nl/ejtir/article/download/3118/3305
17. Brilon, W., Ponzlet, M. (1996). Variability of speed-flow relationships on German autobahns. TRR 1555, 91–98 (TRID record). https://trid.trb.org/View/471118
18. Van der Vlist, M.J.M., Droppert-Zilver, M.N. (1996). Traffic processing on the Dutch A50 motorway without and with illumination. TNO INRO-VVG 1996-28 (TRID record). https://trid.trb.org/View/503730
19. FHWA. Comprehensive Truck Size and Weight Limits Study, Modal Shift Comparative Analysis Technical Report, Chapter 6. https://ops.fhwa.dot.gov/freight/SW/map21tswstudy/technical_rpts/mscanalysis/06impact_trafic_op.htm
20. Zhang, L., Levinson, D. (2004). Some properties of flows at freeway bottlenecks. TRR 1883, 122–131. https://conservancy.umn.edu/server/api/core/bitstreams/d452c120-6059-418a-abaf-ef30d35f7373/content
21. SUMO documentation: Vehicle Type Parameter Defaults. https://sumo.dlr.de/docs/Vehicle_Type_Parameter_Defaults.html
22. Shladover, S.E., Lu, X.-Y., Nowakowski, C. (2011). Development and Assessment of Selected Mobility Applications for VII: Principal Findings. PATH UCB-ITS-PRR-2011-14. https://escholarship.org/content/qt5r33k6wk/qt5r33k6wk.pdf
23. Liu, H., Xiao, L., Kan, X., et al. (2018). Using Cooperative Adaptive Cruise Control (CACC) to Form High-Performance Vehicle Streams. Final Report. PATH. https://escholarship.org/content/qt8pw857gb/qt8pw857gb.pdf
24. Gunter, G., et al. (2021). Are commercially implemented adaptive cruise control systems string stable? IEEE T-ITS 22(11), 6992–7003. https://lab-work.github.io/download/gunter2020commercially.pdf
25. Razmi Rad, S., Farah, H., Taale, H., van Arem, B., Hoogendoorn, S.P. (2022). The impact of a dedicated lane for connected and automated vehicles on the behavior of drivers of manual vehicles. RSS 2022 conference paper. https://www.nrso.ntua.gr/rss2022/wp-content/uploads/2022/06/RSS2022_paper_253.pdf
26. TTI / TxDOT (2000). Design Criteria for Ramp Metering: Appendix to TxDOT Roadway Design Manual. FHWA/TX-01/2121-3. https://library.ctr.utexas.edu/hostedPDFs/tti/2121-3.pdf
27. Spiliopoulou, A.D., Manolis, D., Papamichail, I., Papageorgiou, M. (2010/2011). Queue management techniques for metered freeway on-ramps. TRR 2178, 40–48 (Infoscience record). https://infoscience.epfl.ch/record/165887
28. Rajagopal, R., Varaiya, P. (2007). Health of California's Loop Detector System. PATH UCB-ITS-PRR-2007-13. https://escholarship.org/content/qt71w9q93p/qt71w9q93p.pdf
29. Bickel, P.J., Chen, C., Kwon, J., Rice, J., van Zwet, E., Varaiya, P. (2007). Measuring traffic. Statistical Science 22(4), 581–597. https://arxiv.org/pdf/0804.2982
30. Herrera, J.C., Work, D.B., Herring, R., et al. (2009). Evaluation of traffic data obtained via GPS-enabled mobile phones: the Mobile Century field experiment. UCB-ITS-VWP-2009-8. https://escholarship.org/content/qt0sd42014/qt0sd42014.pdf
31. SUMO documentation: Definition of Vehicles, Vehicle Types, and Routes (speedFactor, junction model and lane-change parameters). https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html
32. SUMO documentation: Variable Speed Signs. https://sumo.dlr.de/docs/Simulation/Variable_Speed_Signs.html
33. SUMO documentation: Driver State device. https://sumo.dlr.de/docs/Driver_State.html
34. SUMO documentation: CACC car-following model. https://sumo.dlr.de/docs/Car-Following-Models/CACC.html
35. SUMO documentation: Automatic Routing (rerouting device). https://sumo.dlr.de/docs/Demand/Automatic_Routing.html

Local check (not a literature source): libsumo 1.27.1 in the v5b1 venv exposes `lane.setFriction`, `edge.setFriction`, `vehicle.setTau`, `vehicle.setSpeedFactor`, `vehicle.setActionStepLength`, `vehicle.setImperfection` and `vehicle.setDecel`.
