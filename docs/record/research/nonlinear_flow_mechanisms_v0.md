# Traffic-flow and bottleneck mechanisms that matter for control (v0)

Sourced sweep, 2026-10-29. Scope: field evidence, effect on fixed-gain controllers, microsimulation practice and a SUMO 1.27.1 path for seven mechanism families.

**Access tags.**
- FT: I read the full text myself (PDF converted to text, or HTML).
- FT*: full text opened, but the numbers were pulled out by the web-fetch tool and not re-read line by line.
- ABS: abstract only (from a publisher, index, TRID or OpenAlex page).
- DERIVED: my own arithmetic on sourced numbers. The inputs are named.
- brief: a plant number from the task brief, not from a source.
- [VERIFY]: not opened by me; only a search snippet or a second-hand mention. Never use it as evidence.

**Access problems on 2026-10-29.** The TU Delft repository refused connections all day. So the Yuan/Knoop/Hoogendoorn full texts and the Goñi-Ros sag papers could not be opened. ScienceDirect, SAGE and Springer returned 403. Several key numbers are therefore ABS or [VERIFY].

## Summary

Ranked by strength of field evidence times relevance to our actuators (CAV speed commands, meters, per-lane HDV limits):
1. **Capacity drop** (very strong; US, Canada, Japan, Germany). Field drops cluster at 5-10 %. Our plant's 17-23 % (DERIVED from brief) sits at the top of the field range, so controller gains are likely inflated. Recalibrating this one number matters most.
2. **Stochastic breakdown** (strong; DE, US, CA). Capacity is Weibull-like, with shape 10-20. The best meter set point is a risk trade-off below mean capacity. Ramp vehicles raise the risk more than mainline vehicles. VSL reduces the variance.
3. **On-ramp merge with ramp storage limits** (strong; US practice). This is the usual metering site. Meter rate bounds and queue caps saturate any fixed-gain controller. It is missing from our plant.
4. **Stop-and-go waves and hysteresis** (strong for waves, moderate for discharge loss). Waves travel at -15 to -24 km/h with periods of minutes, and IDM gets the period wrong. Waves cut discharge by 8-23 % on NGSIM US-101. This is the target of CAV and VSL wave damping.
5. **Interacting bottlenecks and off-ramp spillback** (good; US field). A downstream queue hides an upstream bottleneck. Exit-lane spillback cuts all-lane flow by about 10 %. A distant bottleneck makes ALINEA poorly damped (PI-ALINEA is needed). We have two lane drops in series but no ramps.
6. **Time-varying capacity** (good; US weather, Korea night). Rain cuts capacity by 10-11 %, darkness by 3-9 %, and trucks count 2.4-3.2 pcu in queue discharge. Each moves the critical occupancy, so a fixed set point drifts. Missing.
7. **Grades, sags and moving bottlenecks** (good; Japan, Germany). Drops are about 7-20 %, and the head of the queue moves within a sag. In SUMO only KraussPS sees slope, so our IDM CAVs would ignore it. Missing.

Second check: our single-lane discharge of about 1,200 veh/h (brief) is about 31-34 % below the Twin Cities mean in pcu (DERIVED). It is close to Japanese sag, tunnel and urban values. See section 2.

---

## 1. Stochastic breakdown: capacity as a random variable

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Capacity is treated as a random variable. 5-min capacities follow a Weibull distribution | F(q) = 1 - exp(-(q/β)^α) | German freeways | [1] §2.4, eq. 2 | FT |
| Breakdown interval definition: an interval is "uncensored" if the speed falls below a threshold in the next interval | example threshold 70 km/h | Germany | [1] §2.4; [2] §'Pre-breakdown capacity for an isolated bottleneck' | FT |
| Shape parameter on sections without a speed limit. It is larger (less variance) on sections with VSL | α ≈ 13 | German freeways | [1] §2.4 | FT |
| Typical range of the shape parameter | α 10-20, 13 recommended | Germany | [2] same §, after eq. 6 | FT |
| 5-min scale parameter from the German HCM (HBS) capacity | β = 1.275 × HBS capacity | Germany | [1] §2.4 | FT |
| Breakdown probability per 5 min at given loads, α = 13 | 4.2 % at HBS capacity (β/1.275); 22 % at 0.90β; 40 % at 0.95β; median 0.972β | from [1] | DERIVED | DERIVED |
| Interval conversion: 60-min scale = 12^(-1/α) × 5-min scale | factor 0.826 at α = 13 | from [2] | [2] eq. 7-10 | FT + DERIVED |
| Chain of n identical, independent bottlenecks: the scale shrinks by n^(-1/α) | n = 2: -5.2 %; n = 3: -8.1 % (α = 13) | from [2] | [2] §'Sequences of bottlenecks', eq. 14-18 | FT + DERIVED |
| The independence of bottlenecks in a chain "is not critical if the bottlenecks are located far enough" apart. Fully dependent bottlenecks act as one | qualitative | theory | [2] §'Sequences of bottlenecks' | FT |
| At ramp merges, breakdown can occur below the maximum observed flows. With the same flows, it sometimes happens and sometimes not. Clusters of ramp vehicles trigger it | qualitative | US, NCHRP 3-37 merges | [3] | ABS |
| Breakdown-probability models from more than 40 congestion events over about 20 days at 2 sites | P(breakdown) as a function of flow | Toronto, 2 bottlenecks | [4] | ABS |
| 100 extra ramp vehicles raise the breakdown probability more than 100 extra mainline vehicles | qualitative | US/Canada | [5] | ABS |
| Adding breakdown-probability models to SZM and COMPASS metering postponed congestion | 17-35 min (simulation; VISSIM, 5-6 h) | Minneapolis, Toronto | [5]; [6] | ABS |
| Daily QDF and pre-queue flows are normally distributed. 30-s QDF "should not be assumed to be constant" | QDF s.d. 141 pcplph, PQF s.d. 128 | Twin Cities, 27 bottlenecks | [7] abstract; results text | FT |
| Demand noise used in a whole-year stochastic capacity model | normal factor, mean 1, variance 0.1, on 5-min demand | Germany (A3) | [1] §2.3 | FT |

**Matters for control.**
- A fixed set point at "capacity" carries a large breakdown risk. At 0.90β the 5-min breakdown chance is 22 % (DERIVED, α = 13). So the throughput-optimal set point lies below the mean capacity. It depends on α, on the interval, and on how long the peak lasts.
- A deterministic plant rewards running at the knife edge. A stochastic plant penalises it. Fixed-gain ALINEA tuned on a deterministic plant will over-admit.
- The ramp share of the flow matters [5]. A controller that only watches the total downstream flow misses this.
- VSL raises α [1], so it reduces capacity randomness. This is a measurable benefit of speed harmonisation that a deterministic plant cannot show.
- Chains of bottlenecks reduce the system "reliability capacity" [2]. In a multi-bottleneck plant, the weakest-link risk adds up.

**SUMO path.**
- Breakdown randomness in SUMO comes from driver heterogeneity: `speedFactor` distributions, Krauss `sigma`, and per-vehicle `tau` and action step. No extra mechanism is needed to get a random breakdown time. But its distribution must be measured.
- Optional extra layer: a slowly varying "population" factor. One way is a 5-15 min AR(1) multiplier on `tau` through TraCI `vehicletype.setTau` or per vehicle. This is a model choice, not a sourced SUMO feature. Pre-register it if used.
- Keep insertion realistic. `departSpeed="0"` gives the worst insertion capacity, and `--step-length 0.1` raises single-lane capacity from 1,198 to 1,368 veh/h in the docs' own test (sigma 0.5, speedDev 0.1, departSpeed 0) [44]. A plant that cannot load its bottleneck cannot break down by chance.

**Calibration target.**
- Run constant-demand blocks at a ladder of flows (for example 85-105 % of the pre-queue maximum in 2.5 % steps), with many seeds, on throw-away calibration seeds.
- Classify each 5-min interval with the Brilon rule: the speed at the bottleneck detector falls below 70 km/h in the next interval [1].
- Fit the Weibull by maximum likelihood with censoring (eq. 1 in [1]).
- Target: α in 10-20 (13 typical). The 5-min β should lie within the plant's pre-queue flow range.
- Report the HBS-like point at about 4 % breakdown probability per 5 min (DERIVED).

**Already in our plant vs missing.** Partly present: heterogeneous, stochastic drivers exist (brief). Unknown: the breakdown-probability curve and α have not been measured. Missing: any check against α 10-20.

---

## 2. Capacity drop: size by bottleneck type, queue speed, trucks and lanes

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Flow drop after queue formation, all sites | 2-11 %, mean ≈ 5 %, s.d. 2 % | Twin Cities, 27 bottlenecks, 7 weeks | [7] abstract; results text; Table 1 | FT |
| Long-run mean QDF and pre-queue flow | QDF 2,016 pcplph; PQF 2,124 pcplph | Twin Cities | [7] abstract; results text | FT |
| Heavy-vehicle share at the studied bottlenecks | 0.7-8.8 % | Twin Cities | [7] data section | FT |
| Lane drop 3→2 (site 25, I-94 WB at CR81), 37 breakdowns in 28 days | drop 7 % (Table 1); QDF 1,994, PQF 2,126 pcplph | Minnesota | [7] Fig. 2 list, Table 1 | FT |
| Drop by bottleneck type, Twin Cities table | weaving 5.2 % (n = 5); entrance ramp 5.5 % (n = 11); tunnel 6.0 % (n = 2); bridge 5.5 % (n = 2); lane drop 7 % (n = 1) | from [7] Table 1 | DERIVED | DERIVED |
| Drop by lane count, Twin Cities table | 2 lanes 4.9 % (n = 14); 3 lanes 5.7 % (n = 11); 4 lanes 8.5 % (n = 2). Correlation of HV share with drop: 0.16 | from [7] Table 1 | DERIVED | DERIVED |
| Merge bottleneck (4 freeway lanes, metered ramp): queue discharge fell from 10,250 to 9,240 vph | 10 %; "losses of at least 8 percent were more the norm"; one day 5 % | I-805 NB, San Diego | [8] §3 | FT |
| Breakdown started each day when the shoulder-lane accumulation (X1-X3) first reached a critical value | 16 vehicles | I-805 NB | [8] §3, Table 1 | FT |
| Restrictive metering (400 vph), then relaxed metering (700 vph), recovered the outflow | up to 9,730 vph, about 13 % above breakdown flow; never sustained more than 13 min | I-805 NB | [8] §4 Experiments | FT |
| Authors' conclusion: "merges should not be over-controlled to avoid breakdown" | qualitative | I-805 NB | [8] §1 | FT |
| Discharge about 10 % below the pre-queue flow. Near-stationary, stable from day to day | ≈10 % | 2 bottlenecks near Toronto | [9] | ABS |
| The drop follows a sharp rise in density over an extended upstream segment. Per-lane drop densities are similar across 3 geometries | qualitative | 3 US bottlenecks | [10] | ABS |
| Capacity before and after queue formation, 52 days | 2,300 → 2,200 pcphpl (98 pcphpl; 4.3 % DERIVED) | QEW, Mississauga | [11] | ABS |
| The queue discharge rate "increase[s] considerably" with speed in congestion. Needs site-specific calibration | speeds 6-60 km/h | Dutch freeways | [12] | ABS |
| A speed-dependent reaction time reproduces QDF versus queue speed. Acceleration differences alone reduce QDF less than observed | qualitative | model + data | [13] | ABS |
| Larger headways after stop-and-go waves and upstream lane changes reduce downstream discharge | qualitative | trajectories (site not in abstract) | [14] | ABS |
| At merges, the drop is "negatively related to the number of lanes". It falls as the off-ramp flow ratio rises | qualitative | Korea (highway merges) | [15] | ABS |
| At ramp merges, the drop depends on the ratio of mainline to ramp flow | qualitative | Twin Cities merges | [16] | ABS |
| Breakdown flow and QDF in the target lanes at a merge (free-flow speed 60 km/h) | BDF 1,396, QDF 1,283 veh/h (≈8 %) | Hanshin Rte 13, Osaka (40,000 veh/day) | [17] §4.2 | FT |
| Default queue-discharge drop in HCS | 7 %, "based on a national average" | US | [18] | FT* (HCM edition [VERIFY]) |
| PCE of heavy vehicles derived from queue discharge flow | 2.36 at a ramp merge (HCM 2000: 1.5); 2.7-3.21 in a reconstruction zone (HCM: 2.0) | Ontario, 2 sites | [19] | ABS |
| Meters raise bottleneck capacity: they delay or prevent activation, allow higher pre-queue flows and raise QDF | qualitative (the abstract gives no %) | Twin Cities, 27 bottlenecks, 7+7 weeks | [20] | ABS |
| Meters-off study, fall 2000: meters gave 21 % fewer crashes and 9 % more mainline volume | 21 %; 9 % | Minneapolis | [28] §5.2.1 | FT* |
| Plant drop (pre-queue 1,450-1,550 → QDF 1,190-1,210 veh/h) | 17-23 %, mid 20 % | bn4x | brief → DERIVED | DERIVED |
| Plant QDF in pcu, with 7.5 % trucks at PCE 2.36-3.21 | 1,320-1,400 pcu/h/lane; 31-34 % below the Twin Cities mean QDF | from brief, [7], [19] | DERIVED | DERIVED |

**Matters for control.**
- The capacity drop is the main reason metering and mainline VSL can raise throughput at all. Without a drop, a meter mostly moves delay from the mainline to the ramp.
- The achievable gain scales roughly with the drop (my inference, not a sourced number). Our plant's 17-23 % is two to four times the field median for lane drops and merges (5-10 %). So controller gains on bn4x are probably inflated. The earlier 50 % plant was an extreme case of the same risk.
- The drop is not a constant. It grows when the queue is slow [12], [13] and after waves [14], [25]. It shrinks with more lanes at merges [15], although the Twin Cities table shows no such trend (DERIVED). It depends on the ramp share [16] and on trucks [19]. A fixed-gain controller tuned at one operating point sees a plant whose payoff moves with the queue state.
- Field metering recovered the drop only briefly (≤13 min) [8]. A controller that holds the bottleneck just below breakdown has to act on precursors, such as shoulder-lane accumulation [8] or density over a long segment [10]. A single downstream occupancy is not enough.

**SUMO path.**
- At a zipper lane drop, the drop size is set mainly by where merging starts. In SUMO's default, zipper merging starts 100 m ahead, so vehicles pass at maximum flow and no drop appears. With `visibilityDistance` around 20 m, a jam forms closer to the drop and the outflow "matches the outflow of a jam". Varying the distance gives "any point in the continuum" [51]. This is a direct tuning knob. Pick it on calibration seeds against a field target, not against controller results.
- Other knobs [52]: inflow near the limit (`departSpeed="max"`, `departPos="last"`). A low `speedDev` (0.05 or less) makes the drop visible. A lower `lcCooperative` "increase[s] the capacity drop". A known dynamics issue separates lane speeds and weakens the drop.
- Measure the drop with oblique cumulative counts at a downstream detector, as in [8] and [9]: pre-queue flow (≥5 min before queue arrival) against the stationary QDF (≥15 min).

**Calibration target.**
- Lane drop or zipper: drop 5-10 %, central 7 % ([7] site 25, [17], [18]).
- Report a sensitivity run at 15-20 % as a low-queue-speed or oscillatory regime ([25], [38] DERIVED).
- QDF level: decide which field anchor fits the plant. The US level is about 2,000 pcplph [7]. The Japanese sag, tunnel and urban level is 1,117-1,361 veh/h/lane ([38], [17]). Write the choice down. The current 1,200 veh/h/lane matches the Japanese values, not the US ones.

**Already in our plant vs missing.** Present: a capacity drop at the zipper lane drops (brief). Likely too large: 17-23 % against field medians of 5-10 % (DERIVED). Unknown: whether the drop depends on queue speed in the plant.

---

## 3. Hysteresis and stop-and-go waves

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Propagation velocity of oscillations inside jams | -16 to -17 km/h (extended jams); about -18 km/h (isolated waves); c_obs = -17 km/h | German A5, about 400 congestions | [21] §3, §4 | FT |
| Propagation velocity on a US freeway (Fig. 6, taken from Zielke et al. 2008) | c ≈ -20 km/h | OR 217, US (the paper labels it "Orlando") | [21] §3 | FT |
| Wave period and growth rate | τ_obs = 10 min; σ_obs = 5 h⁻¹; wavelength always above 1 km, shorter with stronger bottlenecks | German A5 | [21] §3-4 | FT |
| IDM reproduces the speed but not the period or growth. "cannot be improved significantly by changing the model parameters" | τ_IDM = 6 min; σ_IDM ≈ 10 h⁻¹; HDM 8 min, 5 h⁻¹ | simulation against A5 | [21] §4 | FT |
| Propagation speed of the congested-traffic characteristic | c = -15 ± 5 km/h (citing Mika et al. 1969 and others) | literature | [22] §1.3 | FT |
| Oscillating congestion appears less often in the US than in Germany. Frequency depends on time gaps, acceleration, lane changing and speed limits | qualitative | DE, NL, US, JP | [22] §3.9 | FT |
| Oscillations: nearly constant speed, period of several minutes, amplitude stabilises upstream, no effect downstream of the bottleneck. New ones form near ramp interchanges, mainly from lane changes | 22-24 km/h | freeway queues (site not named on the page) | [23] | ABS |
| Waves on NGSIM US-101 | 10-15 mph upstream (16-24 km/h DERIVED) | US-101, Los Angeles | [24] p.2 | FT |
| Discharge after oscillations in the precursor and growth stages | reductions "as large as 25%"; full recovery in the stabilisation stage | US-101 | [24] p.2 | FT |
| Bottleneck discharge falls when drivers adopt larger response times after disturbances | 8-23 %; overall 16 %; precursor 27 %, growth 18 %, stable 7 % | NGSIM US-101 | [25] abstract; §5.1 | FT |
| Ordinary hysteresis dominates the precursor and growth stages. Oscillation amplitude correlates with hysteresis magnitude | qualitative | US-101, 5 oscillations | [24] p.2-3 | FT |
| 53 oscillations: lane changes are the main trigger where there are no large curves. Spontaneous formation occurred near roadside work on an uphill segment | 53 cases | trajectory data | [26] | ABS |
| Field test of SPECIALIST dynamic speed limits, Sep 2009 - Feb 2010 | resolved shock waves in nearly 80 % of activations for them; 40-50 % for other jam types | A12, NL, 14 km | [27] | ABS |

**Matters for control.**
- Waves are the target of CAV speed commands and SPECIALIST-type VSL. If the plant has no realistic waves, or the wrong period, a wave-damping controller is tested against the wrong plant.
- Waves reduce discharge (8-27 % by stage) [24], [25]. So damping them is a second throughput mechanism, on top of avoiding breakdown.
- A fixed-gain occupancy feedback (ALINEA) sees an oscillating signal with a 6-10 min period [21]. That is close to typical control and filter horizons. Gains tuned on a smooth plant can resonate or chatter.
- IDM gives too short a period and too fast a growth [21]. With 50 % IDM CAVs, our plant's wave dynamics may be IDM-dominated. Check them before trusting VSL or CAV gains.

**SUMO path.**
- Krauss `sigma` and heterogeneous `tau` and `speedFactor` already generate waves. IDM CAVs can be checked with the same detectors.
- Detect waves with lane-area or induction detectors every 100-200 m over 3-5 km upstream of the bottleneck, at 1-min aggregation, as in [21].
- Compute c (cross-correlation between neighbouring detectors), period (autocorrelation) and growth rate, with the [21] method.

**Calibration target.**
- c in -15 to -20 km/h (Germany -17, US -20 [21]; -22 to -24 in [23]).
- Period around 10 min for German data [21]. "Several minutes" in [23]. The period is site-specific, so use it as a range check, not a fit.
- Discharge after waves: 7-27 % lower by stage [25]. Use this as a plausibility band only.

**Already in our plant vs missing.** Unknown: waves likely exist (jams of 4-6 h with stochastic Krauss drivers, brief), but c, period and growth have not been measured. Risk: the IDM share may distort the period [21].

---

## 4. On-ramp merges, ramp queues and meter storage

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Meter rates, one vehicle per green | cycle 4-4.5 s; 240-900 veh/h; capacity 900 veh/h | US practice | [28] §5.3.6, Table 5-8 | FT* |
| Meter rates, several vehicles per green | cycle 6-6.5 s; 240-1,200 veh/h; capacity 1,100-1,200 veh/h | US practice | [28] Table 5-8 | FT* |
| Tandem (two-lane) meter | 400-1,700 veh/h; capacity 1,600-1,700 veh/h | US practice | [28] Table 5-8 | FT* |
| Minnesota algorithm: six fixed rates; the ramp wait is capped | lowest rate 150 veh/h (24-s cycle); example wait cap 4 min | Minneapolis | [28] §5.3.4 | FT* |
| Denver "helper": a ramp critical for more than 1 min triggers override of the next upstream meter | 20-s polling; 3 periods | Denver | [28] §5.3.4 | FT* |
| Drivers start to think a meter is broken after waiting | more than 15 s per cycle | US | [28] §5.3.1 | FT* |
| Traffic-responsive metering against pre-timed | 5-10 % better (1989 ITE source) | US | [28] §5.3.3 | FT* |
| Critical occupancy may be unknown or may change with environment or truck share, which motivates adaptive ALINEA | qualitative | simulation | [29] | ABS |
| A merge capacity drop arises from merging itself (extended Newell-Daganzo model) | validated on one site | M6, UK | [30] | ABS |
| Lane-changers leave voids. The same 4-parameter model gives both the bottleneck discharge drop and the moving-bottleneck capacity | qualitative | theory + data | [31] | ABS |
| Breakdown triggered by ramp platoons; shoulder-lane critical accumulation of 16 veh | see sections 1 and 2 | US | [3]; [8] | ABS; FT |

**Matters for control.**
- The meter is bounded, for example to 240-900 veh/h for one car per green [28]. The ramp queue is bounded by storage and by wait caps such as 4 min [28]. Near the bounds, any fixed-gain law saturates. Then the controller must switch to queue override, and integral terms need anti-windup.
- This hard nonlinearity decides most of what metering can do in the field. It is absent when the meter sits across all mainline lanes, as in our plant.
- Ramp platoons [3] and the ramp share [5], [16] make the best mainline set point depend on the ramp flow. A single critical occupancy is then wrong part of the time [29].
- A ramp queue that spills onto the arterial counts in door-to-door delay. This links meter benefit to arterial storage. It is a pre-registered side constraint in this project.

**SUMO path.**
- Build the on-ramp as an acceleration lane that is a dead-end lane, a little longer than in reality, because SUMO drivers slow down near its end [45].
- Meter: a traffic light on the ramp edge, one car per green with a 4-4.5 s cycle, and rates bounded to 240-900 veh/h [28]. Add a queue detector near the ramp entry and an override rule (cap the wait or the queue length).
- Arterial spillback: a feeder edge with limited storage upstream of the ramp. Vehicles that cannot enter wait in the insertion backlog, which already counts in door-to-door delay.
- Merge friction knobs: `lcCooperative`, `lcAssertive`, `lcSpeedGain`, `lcKeepRight`, `lcCooperativeSpeed` (LC2013 defaults 1.0, 1, 1.0, 1.0 and "= lcCooperative") [48]. `lcCooperative` is the documented lever on the merge drop [52].

**Calibration target.**
- Merge drop 8-10 % ([8], [17]); shoulder-lane accumulation at breakdown as a mechanism check [8].
- Breakdown probability rising faster with ramp flow than with mainline flow [5].
- A meter-off versus meter-on contrast in the plant of the same sign as Minneapolis (about +9 % mainline volume [28]), as a weak plausibility check only. That study was network-wide, not a single merge.

**Already in our plant vs missing.** Missing: no on-ramp, no ramp storage, no queue override. Our meter is a mainline signal across all lanes (brief). It does not face ramp-specific saturation or ramp-platoon breakdown.

---

## 5. Off-ramp spillback, weaving and interacting bottlenecks

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| A bottleneck formed whenever off-ramp queues spilled into the mandatory exit lane | flow 2,085 → 1,900 vphpl (nearly 10 %); one day 40 % | I-5 SB, Orange County (5 lanes + HOV) | [32] abstract, §3 | FT |
| Non-exiting drivers slowed in all lanes ("rubber-necking"). Longer exit queues went with lower adjacent-lane discharge | speeds often as low as 25 km/h in right lanes | I-5 SB | [32] §3 | FT |
| Changing a nearby signal so the exit queue did not spill back removed the bottleneck | exit demand above 1,250 vph served; flows of 2,100-2,200 vphpl | I-5 SB | [32] §4 | FT |
| During a detector malfunction, the downstream signal's service of the exit flow dropped | 1,200 → 820 vph | I-5 SB | [32] footnote | FT |
| A daily off-ramp queue grows and fills all non-HOV lanes. Shoulder lanes queue while median lanes do not ("multi-pipe") | starts 14:30-15:00, lasts to 18:00+ | I-880 NB to I-238, Oakland | [33] abstract; §1; §3 | FT |
| Weaving bottlenecks: discharge falls when freeway-to-ramp lane changes concentrate near the on-ramp. Placement depends on on-ramp flow | SR-55N: 9,865 → 8,465 vph (14 %); I-210W: 11,100 → 10,200 vph (8 %) | Santa Ana and Pasadena, CA | [34] Exec. summary, §3.1-3.2 | FT |
| Lane-change concentration near the on-ramp in a weave | 50 % of manoeuvres within 140-340 m of the on-ramp, by type and site | SR-55N, I-210W | [34] §3 | FT |
| A bottleneck about 1 km downstream of a merge became active only after a queue from further downstream dissipated | ≈1 km | US | [35] | ABS |
| A merge bottleneck stayed inactive for most of a rush because of an exogenous queue from downstream | 1 of 10 study days | I-805 NB | [8] §3, footnote 1 | FT |
| Drivers leaving at an off-ramp can stop congestion from growing beyond it. Ramp sequences create interconnected bottlenecks | qualitative | German A5 | [22] §4.2 | FT |
| ALINEA with a distant downstream bottleneck "may lead to a poorly damped closed-loop behavior". A tuned PI-ALINEA works over a range of distances | qualitative | macroscopic simulation | [36] | ABS |
| Chain of bottlenecks: lower combined capacity scale | see section 1 | theory | [2] | FT |

**Matters for control.**
- Bottleneck hiding: while a downstream queue sits over an upstream bottleneck, that bottleneck is inactive [35], [8]. A controller protecting it does nothing useful, or harm, until the queue clears. Then the active bottleneck jumps.
- A fixed-structure local controller cannot follow this. Coordinated zone control can. This is a core argument for the thesis topic.
- If the binding bottleneck is far from the meter, plain ALINEA is poorly damped [36]. The distance, and hence the right gain, changes when the active bottleneck moves.
- Exit-lane spillback lowers throughput for through traffic too, by about 10 % and up to 40 % [32]. Protecting the exit (off-ramp signal or exit-lane management) can be worth more than mainline metering at such sites.

**SUMO path.**
- Off-ramp with a downstream signal of limited capacity (for example a red phase that serves about 820-1,200 veh/h of exits [32]). The exit lane then queues back onto the mainline.
- "Rubber-necking" in adjacent lanes is not a SUMO mechanism. If wanted, emulate it with a TraCI rule that lowers the `speedFactor` of vehicles in adjacent lanes next to a queued exit lane. Calibrate the strength to about 10 % lost discharge [32]. This is an assumption and must be stated.
- Weaving: a combined on-off ramp. The auxiliary lane serves as the acceleration lane of the on-ramp and the deceleration lane of the off-ramp. The docs warn this can deadlock if the lane is short or traffic is very dense [45]. Check for teleports.
- Multiple bottlenecks: place them far enough apart for independence ([2] gives no number). Log which bottleneck is active per interval, so activation shifts can be counted.

**Calibration target.**
- Exit-spillback drop of about 10 % [32]. Weave drop 8-14 % [34].
- Activation-shift events present: an upstream bottleneck that turns on after a downstream queue clears [35].

**Already in our plant vs missing.** Present: two bottlenecks in series (4→2 and 2→1 zippers, brief). Their interaction (hiding, shifting) is unknown. Missing: off-ramps, weaving, exit-lane spillback.

---

## 6. Grades, sags, tunnels, lane drops and moving bottlenecks

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Uphill: output flow fell after the queue filled the downhill approach | about 10 %; 1,760 → 1,560 vph/lane (11.4 % DERIVED) | expressway near Tokyo, 3 lanes, no ramps, 2 km downhill then a 2.4 % incline | [37] abstract, §1, §3 | FT |
| Mechanism: the shoulder lane acts as a "release valve" for median-lane speed disturbances until its own flow is high | qualitative | same site | [37] abstract | FT |
| Bottleneck strength of a gradient against junctions | gradient (2-3 % valley) 110 veh/h/lane; junctions 320-550 veh/h/lane | German A5 near Frankfurt | [22] Table 1, §2 | FT |
| A hill with gradients up to 5 % often causes congestion | qualitative | A5 "Köpperner Berg" | [22] §2 | FT |
| Sags and tunnels, 2019, 10 jam events per section | BDF 1,397-1,507; QDF 1,117-1,361 veh/h/lane; CD ratio (1 - QDF/C(L)) 7.4-9.2 % | Tomei (2 lanes), Meishin tunnel (2), Kan-Etsu ×2 (3 lanes), Japan | [38] Table 1, Table 4 | FT (tables; Japanese text skimmed) |
| Same data, as BDF → QDF drop | 9.7-20.0 % by section | from [38] Table 4 | DERIVED | DERIVED |
| Where the bottleneck appears within a sag varies. The safe time gap sets the QDF level | qualitative | Japan | [38] abstract | FT |
| Sag and tunnel capacity is low even before congestion, drops further after it, and keeps falling as the queue grows. Brightness and time spent in the queue relate to following behaviour | qualitative | Japanese motorways | [39] | ABS (Japanese) |
| Stop-and-go waves on a sag: the primary trigger is car-following, not lane changing | qualitative | Tomei Expressway, 3-lane sag | [40] | ABS |
| Model view: sag and tunnel capacity loss equals a time-gap increase. Low light in tunnels makes drivers keep larger distances | qualitative | theory | [41] §2.1 | FT |
| Moving bottleneck from slow vehicles | moving at 72 km/h; 1,500-1,800 veh/h passed it, against 9,540-10,740 veh/h upstream | I-880 NB | [33] §3 | FT |
| Forward-moving bottlenecks, probably a slow HGV or road-works vehicle | 1.6 and 2.7 km/h (Fig. 17); 2 cases among about 245 breakdowns | German A5 | [22] §3.9 | FT |
| Lane drop and merge: drop and moving-bottleneck capacity both follow from lane-changer voids | qualitative | theory | [31] | ABS |
| Merges: smaller drop with more lanes | qualitative | Korea | [15] | ABS |

**Matters for control.**
- A sag or grade is a bottleneck with no ramp. There, only speed-based actuators work: VSL, CAV speed commands, or acceleration assistance (the conclusion of [40]).
- The head of the queue moves within the sag [38]. So a fixed detector for feedback can sit in the wrong place on some days. A fixed-gain controller with a fixed sensor then acts on the wrong signal.
- In the field, uphill drops are about 10 % [37], [38]. Their onset depends on lateral dynamics: the shoulder lane "release valve" [37]. This favours per-lane speed limits as a lever.
- Slow trucks on a grade act as moving bottlenecks [33], [22]. With 7.5 % trucks, that would be a real source of capacity variation. But it needs slope-aware truck dynamics.

**SUMO path.**
- Elevation comes from z values in the `edg.xml` shape, or from height maps, or from netedit [46]. Only the electric vehicle model, PHEMlight and the **KraussPS** car-following model use elevation [46].
- KraussPS subtracts g·sin(slope) from the acceleration bound and floors it at zero [50]. A 2.4 % grade removes about 0.235 m/s² (DERIVED). That is large for trucks.
- The SUMO 1.27.1 binary in our toolchain contains `carFollowing-KraussPS` [54]. So switching humans and trucks from Krauss to KraussPS is a one-attribute change (`carFollowModel="KraussPS"`).
- IDM, ACC and CACC ignore slope. A SUMO developer wrote in 2023 that only KraussPS and Rail take grade into account, and suggested TraCI `vehicle.getSlope` with `setAccel` and `setDecel` as a workaround [53]. For our IDM CAVs, slope effects would need that TraCI override. Pre-register it.
- Tunnels and sags in the time-gap view [38], [41]: a location-dependent `tau` increase (TraCI per vehicle on given edges) is the simplest emulation. Calibrate it to the BDF and QDF of [38].

**Calibration target.**
- Uphill: about 10 % output drop and about 1,560 vph/lane after breakdown [37] (a Japanese site; adjust to the local level).
- Sag and tunnel: CD ratio 7-9 % against capacity [38]; the bottleneck location varies between events [38].
- A gradient bottleneck must be clearly weaker than a junction bottleneck, about 110 against 320-550 veh/h/lane [22].

**Already in our plant vs missing.** Present: lane drops with zipper merges (brief). Missing: grades and sags (the plant is presumably flat; unknown), slope-aware car-following, and truck moving bottlenecks. Truck speed limits in the plant: unknown.

---

## 7. Time-varying capacity and a moving head of queue

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Capacity under light rain and rain (about 1.6 cm/h) | -10 to -11 % | Baltimore, Twin Cities, Seattle; 5-min loop data | [42] Table ES.1 | FT* |
| Capacity under light snow | -12 to -20 % | same | [42] Table ES.1 | FT* |
| Speed at capacity: light rain -8 to -10 %, rain -8 to -14 %. Free-flow speed: rain -6 to -9 % | as stated | same | [42] Table ES.1 | FT* |
| Visibility: capacity adjustment factor rising with visibility | 0.8-0.9 | Twin Cities | [42] Fig. ES.2 | FT* |
| Night-time capacity reduction by design speed | 80 km/h: 3.3 %; 100 km/h: 6.9 %; 120 km/h: 8.8 % | Korea Expressway, 2007-2009 | [43] | ABS |
| Bottleneck causes include changes in illumination (tunnel entrances, blinding sun), curves and bad weather | qualitative | DE (A5) and literature | [22] §3.9 | FT |
| A whole-year stochastic model varies the capacity scale for weather and truck share, and draws rain events from monthly rain probabilities | qualitative | Germany, A3, 44 sections | [1] §2.1, §2.4, §3.1 | FT |
| Congestion duration per year on the busiest A3 sections | up to 300 h/year (about 1.2 h per weekday, DERIVED with 250 weekdays) | A3, Hesse, 3-4 lanes | [1] §3.2 | FT + DERIVED |
| QDF decreases as the upstream queue gets longer (citing another study) | qualitative | literature | [7] introduction, item 2 | FT (second-hand) |
| The estimated bottleneck section (1.95-2.25 KP) is wider than the geometric merge (2.0-2.1 KP) | 300 m against 100 m | Hanshin Rte 13 | [17] §4.2 | FT |
| Critical occupancy changes with environment and truck share | qualitative | simulation | [29] | ABS |

**Matters for control.**
- Rain moves capacity by about 10 % [42], and darkness by 3-9 % [43]. Both move the critical occupancy. This is the documented reason for adaptive ALINEA [29].
- A fixed set point tuned for dry daylight over-admits in rain at dusk, and under-admits otherwise. This is a clean, field-sized "regime" for pre-registered operating maps.
- The truck share has the same effect through PCE [19]. Its effect in queue discharge exceeds the HCM values.
- A moving head of queue ([17], [35], [38]) means the right feedback detector changes. That is a structural, not a gain, problem for local controllers.

**SUMO path.**
- Weather or darkness as a scheduled regime: per vType `tau` up (time gap), `speedFactor` down, set by TraCI `vehicletype.setTau` and `setSpeedFactor` at regime changes. Size it so that the plant's capacity falls by the field amount.
- SUMO's friction device only lowers the maximum speed, by factor = -0.3491f² + 0.8922f + 0.4493 (since 1.14.0) [47]. It does not change the time gap, so on its own it is not a capacity model.
- Darkness: same mechanism with smaller sizes (Korea 6.9 % at 100 km/h [43]).
- Truck-share regimes through the demand mix.

**Calibration target.**
- Rain regime: capacity -10 to -11 %, speed at capacity -8 to -14 % [42].
- Night regime at 100 km/h: capacity about -7 % [43] (one country, abstract only).

**Already in our plant vs missing.** Present: crash lane blockages of 30-60 min, P(≥1 crash/day) = 25 % (brief). Missing: weather, darkness, truck-share regimes, and a varying head-of-queue location (unknown for the zipper drops).

---

## SUMO 1.27.1 facts used above

| claim | value | country/site | source [n] + section/table/page | access |
|---|---|---|---|---|
| Default zipper merging starts 100 m before the drop: no flow drop. With `visibilityDistance` 20 m the outflow equals jam outflow; the merge distance spans the continuum | 100 m default; 20 m example | SUMO (developer, 16 Jul 2024) | [51] | FT (dev post) |
| A drop is visible only with inflow near the limit (`departSpeed="max" departPos="last"`) and `speedDev` ≤ 0.05. A lower `lcCooperative` increases the drop. A known dynamics issue separates lane speeds | as stated | SUMO (developer, 2-3 Apr 2019) | [52] | FT (dev post) |
| Single-lane insertion capacity in the docs' test, default step against `--step-length 0.1` | 1,198 → 1,368 veh/h (sigma 0.5, speedDev 0.1, departSpeed 0) | SUMO docs | [44] | FT* |
| Acceleration lanes: a dead-end lane, somewhat longer than in reality. Combined on-off ramps may deadlock | qualitative | SUMO docs | [45] | FT* |
| Models that use elevation: electric vehicle, PHEMlight, KraussPS | as stated | SUMO docs | [46] | FT* |
| KraussPS: aMax = max(0, aBound - g·sin(slope)) | code | SUMO doxygen (current; version not shown) | [50] | FT |
| KraussPS is present in our SUMO 1.27.1 binary; lanes accept a `friction` attribute | `carFollowing-KraussPS`; net_file.xsd line 109 | local toolchain | [54] | FT (local check) |
| Only KraussPS and Rail take grade into account; TraCI workaround | as stated | SUMO (developer, 4 Jun 2023) | [53] | FT (dev post) |
| Friction device lowers only the maximum speed | factor = -0.3491f² + 0.8922f + 0.4493; since 1.14.0 | SUMO docs | [47] | FT* |
| VSS act on listed lanes (`lanes` attribute) | as stated | SUMO docs | [49] | FT* |

---

## Gaps

- **Unreachable or paywalled full texts.** Yuan et al. 2015 and 2017, Goñi-Ros sag papers, Zielke et al. 2008, Bertini & Leal 2005, and Zhang & Levinson 2010 (with its "73 % / 2 % / 3 %" figures) were not opened. See the [VERIFY] list.
- **No published SUMO reproduction of a Weibull breakdown curve was found.** That is one search, not exhaustive. We would be first to report the plant's α, so the method needs care.
- **There is no direct field analogue for a 2→1 zipper on a 100 km/h freeway.** The closest are the Twin Cities 3→2 lane drop (7 %) [7] and a Japanese merge (8 %) [17]. UK numbers were not found.
- **Truck share and drop size.** No clean elasticity was found. There are only PCE values [19] and a weak correlation in the Twin Cities table (0.16, DERIVED, HV share 0.7-8.8 %).
- **Darkness.** Only one country, abstract only [43]. A Dutch lighting study appeared in a search snippet and was not opened.
- **Ramp storage design rules** (storage length per veh/h, queue-detector placement) were not found with numbers. Only the wait caps and override logic [28].
- **Rubber-necking at exit queues** [32] has no SUMO mechanism. Any emulation is an assumption.
- **Hysteresis measurement** (Laval 2011) was not opened. The hysteresis claims rest on [24] and [25].
- **Lane count.** [15] (merges, Korea) and the Twin Cities table (DERIVED) disagree on the direction. Unresolved.
- **The plant's jam duration (4-6 h per peak, brief) looks long** next to about 1.2 h per weekday on the worst German A3 sections (DERIVED from [1]). This is only an indirect comparison, because sites and demand differ. It suggests checking whether demand is far above capacity; if so, metering can mostly move delay.

## Sources (opened)

1. Brilon W., Geistefeldt J. "A stochastic approach for freeway performance estimation." PIARC World Road Congress, Paris 2007 (year from the proceedings URL), paper IP192. https://proceedings-paris2007.piarc.org/ressources/files/4/IP192-Geistefeldt-E.pdf [FT]
2. Wu N., Geistefeldt J. "Modeling reliability in freeway networks." TRR 2422 (2014) 71-78, author copy. https://homepage.rub.de/ning.wu/pdf/TRB2014_Reliability_pub.pdf [FT]
3. Elefteriadou L., Roess R.P., McShane W.R. "Probabilistic nature of breakdown at freeway merge junctions." TRR 1484 (1995) 80-89. https://trid.trb.org/View/451862 [ABS]
4. Lorenz M.R., Elefteriadou L. "Defining freeway capacity as function of breakdown probability." TRR 1776 (2001) 43-51. https://trid.trb.org/view/717305 [ABS]
5. Elefteriadou L., Kondyli A., Brilon W., Hall F.L., Persaud B., Washburn S. "Enhancing ramp metering algorithms with the use of probability of breakdown models." J. Transp. Eng. 140(4) (2014) 04014003. Abstract via https://api.openalex.org/works?search=Enhancing%20Ramp%20Metering%20Algorithms and https://experts.mcmaster.ca/scholarly-works/1624936 [ABS]
6. Elefteriadou L. et al. "Proactive ramp management under the threat of freeway-flow breakdown." Procedia Soc. Behav. Sci. 16 (2011) 4-14. https://experts.mcmaster.ca/scholarly-works/1624939 [ABS]
7. Zhang L., Levinson D. "Some properties of flows at freeway bottlenecks." TRR 1883 (2004) 122-131. https://conservancy.umn.edu/server/api/core/bitstreams/d452c120-6059-418a-abaf-ef30d35f7373/content [FT]
8. Cassidy M.J., Rudjanakanoknad J. "Increasing capacity of an isolated merge by metering its on-ramp." UC Berkeley working paper, 2004 (TR-B 39(10) (2005) 896-913). https://escholarship.org/content/qt30s46939/qt30s46939.pdf ; citation https://econpapers.repec.org/RePEc:eee:transb:v:39:y:2005:i:10:p:896-913 [FT]
9. Cassidy M.J., Bertini R.L. "Some traffic features at freeway bottlenecks." TR-B 33(1) (1999) 25-42. https://ideas.repec.org/a/eee/transb/v33y1999i1p25-42.html [ABS]
10. Chung K., Rudjanakanoknad J., Cassidy M.J. "Relation between traffic density and capacity drop at three freeway bottlenecks." TR-B 41(1) (2007) 82-95. https://ideas.repec.org/a/eee/transb/v41y2007i1p82-95.html [ABS]
11. Agyemang-Duah K., Hall F.L. "Some issues regarding the numerical value of freeway capacity." Int. Symp. Highway Capacity, Karlsruhe 1991, 1-15. https://trid.trb.org/View/360937 [ABS]
12. Yuan K., Knoop V.L., Hoogendoorn S.P. "Capacity drop: relationship between speed in congestion and the queue discharge rate." TRR 2491 (2015) 72-80. Abstract via https://api.openalex.org/works/https://doi.org/10.3141/2491-08 [ABS]
13. Yuan K., Knoop V.L., Hoogendoorn S.P. "A microscopic investigation into the capacity drop: impacts of longitudinal behavior on the queue discharge rate." Transp. Sci. 51(3) (2017) 852-862. https://econpapers.repec.org/RePEc:inm:ortrsc:v:51:y:2017:i:3:p:852-862 [ABS]
14. Oh S., Yeo H. "Impact of stop-and-go waves and lane changes on discharge rate in recovery flow." TR-B 77 (2015) 88-102. https://econpapers.repec.org/RePEc:eee:transb:v:77:y:2015:i:c:p:88-102 [ABS]
15. Oh S., Yeo H. "Estimation of capacity drop in highway merging sections." TRR 2286 (2012) 111-121. Abstract via https://api.openalex.org/works/https://doi.org/10.3141/2286-13 [ABS]
16. Srivastava A., Geroliminis N. "Empirical observations of capacity drop in freeway merges with ramp control and integration in a first-order model." TR-C 30 (2013) 161-177. https://infoscience.epfl.ch/record/188341 [ABS]
17. Hattori F., Wada K. "A second order model of capacity drop at expressway lane-drop bottlenecks." arXiv 2509.12636 (2025). https://arxiv.org/pdf/2509.12636 [FT]
18. McTrans (Univ. of Florida), HCS article on queue discharge capacity drop. https://mctrans.ce.ufl.edu/?p=874 [FT*]
19. Al-Kaisy A.F., Hall F.L., Reisman E.S. "Developing passenger car equivalents for heavy vehicles on freeways during queue discharge flow." TR-A 36(8) (2002) 725-742. https://experts.mcmaster.ca/scholarly-works/250657 [ABS]
20. Zhang L., Levinson D. "Ramp metering and freeway bottleneck capacity." TR-A 44(4) (2010) 218-235. https://econpapers.repec.org/RePEc:eee:transa:v:44:y:2010:i:4:p:218-235 [ABS]
21. Treiber M., Kesting A. "Calibration and validation of models describing the spatiotemporal evolution of congested traffic patterns." arXiv 1008.1639 (2010) (published in TR-C). https://arxiv.org/pdf/1008.1639 ; https://ar5iv.arxiv.org/html/1008.1639 [FT]
22. Schönhof M., Helbing D. "Empirical features of congested traffic states and their implications for traffic modeling." arXiv cond-mat/0408138 (2004) (Transp. Sci. 41(2) (2007) 135-166). https://arxiv.org/pdf/cond-mat/0408138 [FT]
23. Mauch M., Cassidy M.J. "Freeway traffic oscillations: observations and predictions." ISTTT 15 (2002) 653-673. https://its.berkeley.edu/node/4127 [ABS]
24. Chen D., Ahn S., Zheng Z., Laval J. "Traffic hysteresis and the evolution of stop-and-go oscillations." Extended abstract, 1st LATSIS Symposium 2012. https://transp-or.epfl.ch/heart/2012/latsis2012_submission_165.pdf [FT]
25. Chen D., Ahn S., Laval J., Zheng Z. "On the periodicity of traffic oscillations and capacity drop: the role of driver characteristics." TR-B 59 (2014) 117-136, author version. https://eprints.qut.edu.au/64888/1/On_the_periodicity_of_traffic_oscillations_and_capacity_drop_the_role_of_driver_characteristics.pdf [FT]
26. Zheng Z., Ahn S., Chen D., Laval J. "Freeway traffic oscillations: microscopic analysis of formations and propagations using wavelet transform." TR-B 45(9) (2011) 1378-1388. https://econpapers.repec.org/RePEc:eee:transb:v:45:y:2011:i:9:p:1378-1388 [ABS]
27. Hegyi A., Hoogendoorn S.P. "Dynamic speed limit control to resolve shock waves on freeways: field test results of the SPECIALIST algorithm." IEEE ITSC 2010, 519-524. https://trid.trb.org/view/1096490 [ABS]
28. FHWA. Ramp Management and Control Handbook, Chapter 5. https://ops.fhwa.dot.gov/publications/ramp_mgmt_handbook/manual/manual/5_1.htm [FT*]
29. Smaragdis E., Papageorgiou M., Kosmatopoulos E. "A flow-maximizing adaptive local ramp metering strategy." TR-B 38(3) (2004) 251-270. https://ideas.repec.org/a/eee/transb/v38y2004i3p251-270.html [ABS]
30. Leclercq L., Laval J.A., Chiabaut N. "Capacity drops at merges: an endogenous model." TR-B 45(9) (2011) 1302-1313. https://ideas.repec.org/a/eee/transb/v45y2011i9p1302-1313.html [ABS]
31. Laval J.A., Daganzo C.F. "Lane-changing in traffic streams." TR-B 40(3) (2006) 251-264. https://ideas.repec.org/a/eee/transb/v40y2006i3p251-264.html [ABS]
32. Cassidy M.J., Anani S.B., Haigwood J.M. "Study of freeway traffic near an off-ramp." California PATH WP UCB-ITS-PWP-2000-10 (2000) (later in TR-A). https://escholarship.org/content/qt4mh8b630/qt4mh8b630.pdf [FT]
33. Muñoz J.C., Daganzo C.F. "Experimental characterization of multi-lane freeway traffic upstream of an off-ramp bottleneck." California PATH WP UCB-ITS-PWP-2000-13 (2000). https://escholarship.org/content/qt8635j1df/qt8635j1df.pdf [FT]
34. Lee J., Cassidy M.J. "An empirical and theoretical study of freeway weave bottlenecks." UC Berkeley, 2008. https://escholarship.org/content/qt2970816w/qt2970816w.pdf [FT]
35. Bertini R.L., Cassidy M.J. "Some observed queue discharge features at a freeway bottleneck downstream of a merge." TR-A 36(8) (2002) 683-697. https://its.berkeley.edu/node/4122 [ABS]
36. Wang Y., Kosmatopoulos E., Papageorgiou M., Papamichail I. "Local ramp metering in the presence of a distant downstream bottleneck: theoretical analysis and simulation study." IEEE T-ITS (2014). Abstract via https://api.openalex.org/works/https://doi.org/10.1109/TITS.2014.2307884 [ABS]
37. Patire A.D., Cassidy M.J. "A congestion mechanism for uphill expressways, Part I: the shoulder lane 'release valve'." UCB-ITS-VWP-2010-1 (2010). https://escholarship.org/content/qt1kk127zn/qt1kk127zn.pdf [FT]
38. Kai S., Wada K., Horiguchi R., Xing J. "Empirical analysis of capacity drop phenomenon at multiple sag and tunnel bottlenecks on expressway in Japan." JSTE J. Traffic Eng. 9(2) (2023) A_280-A_287. https://www.jstage.jst.go.jp/article/jste/9/2/9_A_280/_pdf [FT: tables; Japanese text skimmed]
39. Koshi M., Kuwahara M., Akahane H. "A study on congestion phenomena at tunnels and sags on motorways." Doboku Gakkai Ronbunshu (1993). Abstract via OpenAlex, https://doi.org/10.2208/jscej.1993.65 [ABS, Japanese]
40. Goñi-Ros B., Knoop V.L., van Arem B., Hoogendoorn S.P. "Empirical analysis of the causes of stop-and-go waves at sags." IET ITS (2014). Abstract via OpenAlex, https://doi.org/10.1049/iet-its.2013.0102 [ABS]
41. Martínez I., Jin W.-L. "Impact of VSL location on capacity drop: a case of sag and tunnel bottlenecks." ISTS'18 / Transp. Res. Procedia. https://www.cee.ehime-u.ac.jp/~keikaku/ists18/pdf/ISTS_IWTDCS_2018_paper_27.pdf [FT]
42. Hranac R., Sterzin E., Krechmer D., Rakha H., Farzaneh M. "Empirical studies on traffic flow in inclement weather." FHWA-HOP-07-073 (2006). https://ops.fhwa.dot.gov/publications/weatherempirical/sect0.htm ; https://ops.fhwa.dot.gov/publications/weatherempirical/sect3.htm [FT*]
43. Kim Y.S., Lee S.S. "Development of adjustment factors under day and night conditions for freeway capacity to improve traffic safety." Int. J. Highway Eng. 17(4) (2015) 107-115. https://koreascience.kr/article/JAKO201525550548547.page [ABS]
44. SUMO docs, Simulation/RoadCapacity. https://sumo.dlr.de/docs/Simulation/RoadCapacity.html [FT*]
45. SUMO docs, Simulation/Motorways. https://sumo.dlr.de/docs/Simulation/Motorways.html [FT*]
46. SUMO docs, Networks/Elevation. https://sumo.dlr.de/docs/Networks/Elevation.html [FT*]
47. SUMO docs, Simulation/Friction. https://sumo.dlr.de/docs/Simulation/Friction.html [FT*]
48. SUMO docs, Definition of Vehicles, Vehicle Types, and Routes (LC2013 table). https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html [FT*]
49. SUMO docs, Simulation/Variable Speed Signs. https://sumo.dlr.de/docs/Simulation/Variable_Speed_Signs.html [FT*]
50. SUMO doxygen, MSCFModel_KraussPS.cpp (current development tree; version not shown). https://sumo.dlr.de/doxygen/de/d42/_m_s_c_f_model___krauss_p_s_8cpp_source.html [FT]
51. Erdmann J., sumo-user, 16 Jul 2024, "creating a capacity drop and lane-changing before a zipper junction." https://www.eclipse.org/lists/sumo-user/msg14212.html [FT]
52. Erdmann J., sumo-user, 2-3 Apr 2019, "reproducing the phenomenon capacity drop." https://www.eclipse.org/lists/sumo-user/msg03979.html [FT]
53. Erdmann J., sumo-user, 4 Jun 2023, on grade in car-following models. https://www.mail-archive.com/sumo-user@eclipse.org/msg12057.html [FT]
54. Local check, 2026-10-29: `strings` on `.../phd_speed_harmo_v5b1_toolchain/venv/.../sumo/bin/sumo` (Eclipse SUMO 1.27.1) shows `carFollowing-KraussPS` and `MSCFModel_KraussPS`; `sumo/data/xsd/net_file.xsd` line 109 defines a lane `friction` attribute. [FT, local]

## Not opened: leads only [VERIFY]

- Zielke B.A., Bertini R.L., Treiber M. (2008), TRR 2088, 57-67. A search snippet gave wave speeds of about 19-20 km/h (US), 16 (DE) and 14 (UK). The full text was not opened. [21] confirms only the US value of about -20 km/h.
- Bertini R.L., Leal M.T. (2005), J. Transp. Eng. 131(6). Lane-drop discharge about 10 % lower (search summaries only).
- Zhang & Levinson (2010) [20]: "73 % longer pre-queue period, 2 % higher pre-queue flow, 3 % higher QDF" appeared only in a search snippet. The abstract I opened has no percentages.
- Srivastava & Geroliminis (2013) [16]: drops of about 15 % and 8 % at one on-ramp, second-hand via Yuan et al.
- Goñi-Ros et al. (sags): QDF about 12 % (2-lane) and 14 % (3-lane) below free-flow capacity, via Xing et al.; 3,150 and 5,340 vph. From a search snippet; TU Delft repository unreachable.
- Yuan et al. (2015) poster: QDF = 29·v + 5,000 veh/h for 3 lanes. From an earlier project note, not re-opened today.
- TTI report 2121: uncontrolled single-lane ramp capacity 1,800-2,200 veh/h (search snippet).
- Laval J.A. (2011), "Hysteresis in traffic flow revisited", TR-B 45(2). Only the abstract summary via search.
- Elefteriadou et al. (2014) [5]: the 17-35 min figure is in the OpenAlex abstract (ABS). The underlying simulation details were not seen.
