# Weather, darkness and rain crash risk: evidence v0 and protocol draft v1

Made 2026-10-30 by a 10-agent review (4 research streams, each checked by an adversarial verifier that re-opened every source; a code-reading critic of draft v0; a synthesis). Claude re-checked FHWA-HOP-13-042 Tables 34 and 35 itself. Only verifier-confirmed numbers are used; unopened leads are marked [VERIFY]. Status: draft, waiting for the author's answers to Q1-Q11.

## Evidence

| Quantity | Value | Source | Locator | Access |
|---|---|---|---|---|
| L08 medium rain CAF / SAF, 60 and 65 mph FFS | CAF 0.93 / 0.92; SAF 0.95 / 0.94 | FHWA-HOP-13-042 (June 2013) App. A, quoting SHRP 2-L08 Exh. 36-25 | Table 34 | FT (L08 report itself not opened) |
| L08 heavy rain CAF / SAF, 60 and 65 mph FFS | CAF 0.88 / 0.86; SAF 0.93 / 0.93 | same | Table 34 | FT |
| L08 targets at 100 km/h (62.1 mph) | medium CAF 0.926, SAF 0.946; heavy CAF 0.871, SAF 0.930 | linear interpolation of Table 34 (my arithmetic) | - | derived |
| L08 rain class bounds | medium >2.54 to ≤6.35 mm/h; heavy >6.35 mm/h; ≤2.54 mm/h counts as "nonsevere" (1.00) | FHWA-HOP-13-042 | Table 35 | FT |
| HCM 2010 rain capacity reduction | ≤0.10 in/h 2.01 % (1.17-3.43); 0.10-0.25 in/h 7.24 % (5.67-10.10); >0.25 in/h 14.13 % (10.72-17.67), so heavy CAF ≈ 0.859 | HCM 2010 Exh. 10-15 via FHWA-HOP-13-042 | Table 33 | SECONDARY (HCM 2010 superseded) |
| Light rain in the FHWA example | CAF 0.98 (1 − 2.01 %), SAF 0.98 | FHWA-HOP-13-042 | Table 36 and intro text | FT |
| Capacity definition behind the HCM rain averages | mean of the top 5 % of flows, occupancy 5-50 %; site means equal HCM 2.01 / 7.24 / 14.13 | Agarwal, Maze & Souleyrette 2005, CTRE Iowa State | p. 6; Table 2 p. 9 | FT (the HCM link is an inference) |
| Rain capacity, US loop data | −10 to −11 %, constant over 0-1.7 cm/h | FHWA-HOP-07-073 (Oct 2006) | §5.2 items 2-4; Table ES.1 | FT |
| Rain free-flow speed | −2 to −3.6 % light rain; −6 to −9 % at about 1.6 cm/h | same | §5.2 | FT |
| Rain speed at capacity | −8 to −10 % light; −8 to −14 % rain; aggregate c1 0.909 | same | §5.2; Table 5.4 | FT |
| Rain capacity constant c1 | 0.892 (n = 137, 3 sites) | same | Table 5.5 | FT |
| Jam density in rain | not impacted | same | §5.2 item 1 | FT |
| Meaning of "capacity" there | apex qc of a fitted Van Aerde curve; not separated from queue discharge | same | §3.2 | FT |
| NL pre-breakdown vs discharge capacity in rain | light (0.01-1 mm/h) −5.7 % (SD 1.9) vs −5.6 % (SD 1.3); heavy (>1 mm/h) −8.1 % (SD 2.6) vs −6.5 % (SD 1.5) | van Stralen, Calvert & Molin 2015, EJTIR 15(4) | §3.1 p. 491; Table 2 p. 492 | FT |
| Breakdown flow drop, rain vs no rain | 3.9-12.0 % vs 7.8-12.7 % | Kim, Mahmassani & Dong 2010, TRR 2188 | abstract | ABS |
| QDF vs pre-breakdown sensitivity | QDF more sensitive to weather (4 Milwaukee bottlenecks) | Dehman 2012, TRR 2286 | abstract | ABS |
| Discharge drop at California merges | about 5 % (drizzle) to 27 % (heavy, >2.54 mm/h) | Seeherman & Skabardonis 2020, JTE-A 146(10) | abstract | ABS |
| Review range, rain capacity and free speed | capacity −4 to −30 %, mostly 5-15 %; free speed −2 to −10 % | Snelder & Calvert 2016, EJTIR 16(1) | §2 pp. 131-132; Table 1 | FT |
| Time gap in rain, uncongested two-lane highway | gap +5.6 %, speed −3.7 %, following distance unchanged | Rahman 2010, MSc UConn | abstract | ABS |
| Time gap in rain, congested expressway | light rain: no time-gap change | Unrau & Andrey 2006, TRR 1980 | abstract | ABS |
| Headways as the mechanism | stated as "greater time headways", not measured | van Stralen et al. 2015; Snelder & Calvert 2016 | p. 483; Table 2 p. 133 | FT |
| Rain crash rate, meta-analysis | +71 % (95 % CI 31-111), N = 10; rain = 6-h total >0.4 mm; all roads, all severities | Qiu & Nixon 2008, TRR 2055 | Table 2 p. 142; p. 145 | FT |
| Rain injury rate | +49 % (28-70), N = 7 | same | Table 2 | FT |
| Heavy rain crash rate | +93 %, N = 1, intensity undefined | same | Table 2 | FT |
| Rain crash rate, studies 1990-2005 | +70 % (30-111), N = 4 | same | Table 3 p. 143 | FT |
| Rain, extremes excluded | +52 % (wording mixes injury and all-crash rates) | same | p. 144 | FT |
| French motorways, injury-accident added risk in rain | 3.5 (1995), 2.58 (2000), 2.38 (2005); authors say gauge-based values overestimate | Bergel et al., WCTR paper (venue and year [VERIFY]) | Table 2 p. 8 | FT |
| Canadian cities, rain RR | collisions 1.59, injuries 1.41 (urban) | Andrey et al. 2003 via Mills & Andrey, AMS 15B.4 | Table 1 | SECONDARY |
| US rain days | crashes +10 %, injuries +8 %; days >50 mm +51 % / +38 % | Black, Villarini & Mote 2017, WCAS 9(1) | abstract | ABS |
| Crash type in rain | multi-vehicle RR above single-vehicle (Kansas) | Tobin, Kumjian & Black 2021, AAP 151 | abstract | ABS |
| Crash composition on wet freeways | rear-end more likely on dry roads in daylight | Golob & Recker 2003 | abstract | ABS |
| Rain RR by congestion | about 5 at the lowest of 15 levels, about 1 at the highest (urban intersections, volume index) | Retallack & Ostendorf 2020, IJERPH 17(4) | abstract; §3.3 | FT |
| Trend in rain RR | declining (Canada 1984-2002; French motorways 1995-2005) | Andrey 2010; Bergel et al. | abstract; Table 2 | ABS; FT |
| Darkness and wet speed, German autobahns | darkness about −5 km/h; wet about −10 km/h; no capacity number | Brilon & Ponzlet 1996, TRR 1555 | TRID abstract | ABS |
| German capacity reductions vs daylight-dry | dark-dry 13-25 %; daylight-wet 12-29 %; dark-wet 38-47 % | Brilon & Ponzlet 1995 via FHWA-HOP-07-073 | §2.1 Table 2.1 | SECONDARY |
| Lighting on the A50 (NL, dry, free flow) | no capacity change; speed about +0.5 km/h | van der Vlist & Droppert-Zilver 1996, TNO INRO-VVG 1996-28 | Summary; §4.2; §5.1 | FT |
| Lighting and night capacity (NL) | +2.5 % at night; daytime n.s. | Van Goeverden, Botma & Bovy 1998, TRR 1646 | abstract | ABS |
| Night CAF, Korean freeways with little lighting | 0.97 / 0.93 / 0.91 at 80 / 100 / 120 km/h design speed | Kim & Lee 2015, IJHE 17(4) | Tables 6-9 | FT |
| Darkness speed, Swedish 110-120 km/h roads | −0.5 to −2.0 km/h, not significant | Jägerbrand & Sjöbergh 2016, SpringerPlus 5 | Tables 7-8 | FT |
| Darkness injury-accident risk | about +40 % (NO, SE, NL; all roads) | Johansson, Wanvik & Elvik 2009, AAP 41(4) | abstract | ABS |
| Rain demand, review | −2 to −14 %, mostly −2 to −5 % | Snelder & Calvert 2016 | p. 131 | FT |
| Dutch A16 motorway demand in rain | no change | Hogema 1996 via Snelder & Calvert Table 1 and Sándor 2013 | Table 1 p. 132; p. 121 | SECONDARY |
| NL stated adaptation, morning peak | light rain 110.9, heavy rain 105.5 (dry = 100) | van Stralen et al. 2015 | Table 5 p. 495 | FT (survey, not counts) |
| Belgian highways, daily counts | about −0.19 % per mm/day (coefficient −0.019 per 0.1 mm) | Cools, Moons & Wets 2010, WCAS 2(1) | Table 5 | FT (per-mm figure derived) |
| Scotland (Lothian) | −4 % / −4.6 % | Al Hassan & Barker 1999 via van Stralen 2015 and Snelder & Calvert 2016 | p. 483; Table 1 | SECONDARY |
| Melbourne wet days | −1.35 % winter; −2.11 % spring | Keay & Simmonds 2005, AAP 37(1) | abstract | ABS |
| Motorway exposure in rain | rainfall effect mainly direct on motorways, exposure unchanged (monthly models) | Bergel-Hayat et al. 2013, AAP 60 | abstract | ABS |
| Days with ≥1 mm, 1991-2020 | UK 159.1 per year (about 44 %); England 135.2 (about 37 %) | Met Office HadUK-Grid Raindays1mm | UK.txt, England.txt | FT (means derived) |
| Wet hours, lowland SE England | about 7-10 % (spring, summer); about 10-14 % (autumn, winter) | Lewis et al. 2018, J. Hydrol. 564 (CEH-GEAR1hr) | Fig. 14 p. 941 | FT (read from a colour map) |
| UK hours by rain intensity class | not found | - | - | gap |
| ALKS and weather | no numeric weather limits; must adapt speed to inclement weather; time gaps set only up to 60 km/h, national rules above | UN R157 01 series, Amend.4 (2023) | §5.2.3.2; §5.2.3.3 | FT (MarkLines mirror) |
| UK wet-road gap advice | at least 2 s, at least doubled on wet roads (advisory) | Highway Code | Rule 126 | FT |
| L2 activation in rain | odds ratio 0.53 (0.39-0.70) vs clear, above 40 mph | Russell et al. 2018, NHTSA DOT HS 812 642 | p. 30 | FT |
| ACC / CACC gaps in rain | not found | - | - | gap |

## Protocol draft v1


Status: draft, not approved. It replaces draft v0. Once the author answers Q1-Q11 it gets logged as the next decision (V204 if nothing comes first). Tags [Qn] mark text that depends on an answer. The text shows the recommended option.

## 1. Scope
- Three weather states: dry, medium rain and heavy rain. Each simulated day has one state, set when the vehicles are generated [Q1].
- Weather is an observed regime, not a hidden condition, because rain can be measured in practice. Opponents may be scheduled by it (§8).
- Not modelled, and disclosed: darkness [Q2], demand change [Q3], road friction (SUMO decel and emergencyDecel keep their dry values), CAV response [Q5].

## 2. Targets, fixed before any run
| State | SHRP 2-L08 class | QDF ratio target (CAF) | Human free-speed ratio (SAF) | Crash ratio R [Q4] |
|---|---|---|---|---|
| dry | - | 1 | 1 | 1 |
| medium | >2.54 to ≤6.35 mm/h | 0.926 | 0.946 | 1.71 |
| heavy | >6.35 mm/h | 0.871 | 0.930 | 1.71 |

- CAF and SAF come from linear interpolation of the 60 and 65 mph columns of FHWA-HOP-13-042 Table 34, at 100 km/h = 62.1 mph.
- R is the pooled rain crash rate of Qiu & Nixon 2008: +71 % (95 % CI 31-111 %).
- Report-only sensitivity rows: heavy rain at the HCM 2010 value (CAF 0.859); R = 1.31, 2.11 and 1.0.
- Disclosed assumption [Q10]: the L08 factor is applied to queue discharge (QDF), so the capacity drop is assumed unchanged in rain. The evidence is split:
  - NL: pre-breakdown and discharge capacity fall by similar amounts;
  - US: the breakdown drop is similar in rain and in dry weather;
  - Milwaukee: QDF is more sensitive to weather.
- Disclosed spread across sources: for heavier rain the CAF ranges from 0.859 (HCM 2010) to 0.935 (NL discharge, >1 mm/h). FHWA-HOP-07-073 gives 0.89 at every intensity.

## 3. Mechanism (human drivers only)
- One new weather function runs after the fleet draw, after the hdv_car acceptance loop and the CAV branches (fleet.py:183-195). It does not go through HDV_TAU_SCALE or CAR_SF, so every random draw is the same in all states.
- hdv_car: tau ← round(g_s × tau, 3). Since g ≥ 1, tau stays ≥ actionStepLength.
- truck: tau is written explicitly as g_s × 1.0 (the SUMO default, [VERIFY]). Dry trucks also get tau 1.0 explicitly.
- Desired speed: each vehicle's maxSpeed = SAF_s × its dry desired speed. For trucks that is SAF_s × min(sf × LIMIT, TRUCK_MAX). speedFactor and the lane limits stay unchanged. Under a lowered VSL limit L the desired speed is min(sf × L, SAF_s × sf × LIMIT), so rain and VSL do not compound [Q6].
- Unchanged: length and minGap (so jam density is unchanged, as FHWA-HOP-07-073 found), sigma, actionStepLength, lane-change parameters, all CAVs [Q5], and the TTC threshold of 1.5 s.
- The incident zone multiplies the wet tau by 3 [Q7].
- Tests before any run:
  - dry and wet fleets share every class, depart time, lane, length, sf, CAV tau and CAV sf;
  - human tau = g × dry tau, within 0.0005;
  - trucks carry the explicit tau;
  - dry crash-free days reproduce the V198 trajectory hashes.

## 4. Calibration of g per wet state (lane-drop road ld32)
Setup:
- The V187 method (calib.run_once, calibrate.measure) with the plant v188 driver knobs and the human fleet only.
- Teleporting off, as on the plant.
- Demand profile: warm-up 300 s, ramp 1,200 s, hold 3,600 s instead of 1,200 s. T_CAP stays at 7,200 s.
- Breakdown threshold fixed at 50 km/h in every state.
- QDF = mean exit flow per lane over a fixed 20-min window starting at tb + 300 s, the same in both arms. A run is invalid if the window does not end before the hold does.

Fit:
- Grid g ∈ {1.00, 1.05, ..., 1.50} for each wet state, using that state's SAF. 20 throw-away seeds. A dry arm (g = 1, SAF = 1) runs on the same seeds. That makes 460 runs.
- For each seed, the paired ratio r = QDF_wet / QDF_dry.
- Take the median r at each grid point and fit a monotone decreasing curve (pool-adjacent-violators). g* is where the curve equals the CAF, found by linear interpolation and rounded to 0.01.
- If the curve does not cross the CAF in [1.0, 1.5], stop for the author.

Confirmation at g*: 30 fresh throw-away seeds with a paired dry arm. It passes only if all of these hold:
1. the bootstrap 95 % CI of the median paired QDF ratio contains the CAF, and the median lies within ±0.02 of it;
2. at least 80 % of seeds in each arm have a valid breakdown window;
3. the human free-speed ratio lies within ±0.01 of the SAF (harmonic-mean speed of human vehicles at the upstream loop during the 300-s warm-up);
4. 0 teleports, 0 SUMO collisions, and every run drains.

If it fails: refit once with the confirmation data added, then confirm once more on 30 new fresh seeds. A second failure stops the work for the author.

Reported with no pass/fail:
- the wet/dry pre-queue flow ratio with its CI; if it misses the CAF by more than its CI, it is reported as a known deviation;
- the wet median capacity drop, checked against the V184 band of 2-11 %;
- wet/dry ratios of critical density, critical occupancy and speed at capacity. Speed at capacity is compared with FHWA-HOP-07-073 (0.86-0.92). If it falls outside that range, this is disclosed before any setpoint-based claim;
- the share of 30-s intervals at 'up' with speeds between 40 and 60 km/h;
- QDF window lengths and the number of invalid runs;
- heavy rain at CAF 0.859: g is read from the same fit and confirmed on the same 30 seeds (30 more runs). Report-only.

## 5. Plant-level checks on v199, before any controller run
All on fresh seeds (§9), with no control.

5.1 Realized effect with the full fleet mix. On ld32, use the V188 step 2 ramp profile for each state and report the wet/dry pre-queue flow, QDF and free speed. Every cell is reported both by its L08 label and by these realized ratios.

5.2 Crash-free days on ramp32 for each state: human-only (10 seeds) and full mix (30 seeds; these are the reference days).
- Report: wet/dry discharge at merge_up and up, the active bottleneck, ramp waits over 60 s and over 300 s, the longest wait, ramp queue, breakdowns, delays under both references (§7), TTT, drain status and collisions.
- Stop for the author if any run fails to drain, deadlocks or has a SUMO collision.

5.3 Crash scale per wet state.
- From the conflict records of the 5.2 full-mix days, choose k_s so that the mean expected number of crashes per day equals R times the dry mean on the same seeds.
- With the linear weight, k_s = R × k × Σw_dry / Σw_wet. This holds while every p is below 1; p_max is reported.
- Then run the V198 live check.
- Report expected crashes per day and P(≥ 1 crash/day) for each state. If dry stays at 0.25, R = 1.71 gives about 0.39 (Poisson approximation, my arithmetic).

5.4 Incident zone in rain.
- Use the V199 3-lane setup with the wet human fleet, f = 3, and 10 seeds per wet state.
- Report η against the wet QDF (confirmed ratio × 1,794 veh/h/lane) and against the dry QDF.
- Proposed rule: stop for the author if the wet η differs from 0.54 by more than 0.10 [Q7].

5.5 CAV bound (report-only). Repeat 5.1 and the 5.2 full-mix days on 10 seeds, with every CAV class given the human g and SAF.

## 6. Disclosures in every weather table
- CAVs keep their dry behaviour. I found no field data on ACC or CACC gaps in rain.
- Scaling tau is a calibration device, not a sourced headway change. Field data: +5.6 % time gap in uncongested rain on a two-lane highway; no time-gap change in congested light rain.
- The L08 factors are US values from 2013, and HCM 2010 has been superseded. L08 medium and heavy rain is probably rare in the UK (my inference), so a whole day of it is a stress cell, not a typical day.
- R covers all crash types on all road types, mostly from studies before 2006, and rain crash risk has fallen over time. Its value for rear-end crashes in congestion is unknown. One urban study found the rain risk ratio falls toward 1 in congestion.
- Trucks use the same factors as cars; no source covers trucks separately.
- No darkness, no friction effect, no demand change.

## 7. Metrics across cells
- Primary: door-to-door delay including origin and insertion queues, measured against the dry desired speed. This reference is the same in every cell and counts the rain slowdown as delay. Served throughput is co-headlined.
- Secondary: delay against the wet desired speed (congestion delay only).
- TTT over a fixed window, with unfinished vehicles counted to the end of the window.
- All controllers in a cell use the same reference.

## 8. Opponents [Q9]
- Weather-scheduled: each proven controller is tuned per state on tuning seeds and applied through a state → parameters lookup. This is realistic, since rain can be observed.
- Weather-blind: one tuning pooled over the three states.
- A helper claim in a weather cell needs a win over the weather-scheduled opponent. The gap between the blind and scheduled opponents is reported as what weather scheduling alone buys.
- If rain episodes (1b) are chosen later, add a scheduler fed by an observed rain signal.

## 9. Seeds [Q8]
- The V135 calibration block 7,430,000-049 looks fully used: 000-019 by p1c, 020-039 by earlier fleet steps, 040-049 by V187-V203. Seeds 040-049 are not reused for weather work, because the dry plant was selected on them.
- The author names fresh ranges. Claude checks they are unused in docs, code and run folders before using them.
- Needed: 20 seeds for the g fit and 60 for confirmation plus reserve (all throw-away), and 30 for §5. Regime seeds come from the V135 tuning, validation and evaluation partitions, in the regime protocol.

## 10. Compute (my estimate, not measured)
- ld32: about 700 short runs (fit, confirmation, the HCM arm, 5.1, 5.5). At the draft's rate of about 130 runs per hour that is about 5-6 h, plus 90 runs if a refit is needed.
- §5: about 140 day runs plus 20 incident runs. Their time is to be estimated from the V198 batch log.
- CPU guard, at most 32 workers, and a resource check before every batch.

## 11. Corrections to draft v0
- Snelder & Calvert 2016 do not give a −2 % to −8 % demand range. They give −2 % to −14 %, mostly −2 % to −5 %.
- The "+70 % [VERIFY]" crash figure is Qiu & Nixon 2008: +71 % (CI 31-111 %), all roads and all severities.
- The L08 intensity classes are now checked: medium is 2.54-6.35 mm/h and heavy is above 6.35 mm/h. L08 counts light rain as "nonsevere" (factor 1.00).
- Targets are interpolated to 62.1 mph instead of taken from the 60 mph column.
- The A50 lighting report has now been read in full, not just its abstract.
- "A clear hidden condition" was wrong: rain is observable.

## 12. Review points handled differently from the review's suggestion
- Reusing 040-049 for g: not adopted. Fresh seeds are used instead, because 10 selection-conditioned seeds are too few for the fit.
- Three opponents: two under 1(a), because with whole-day states a scheduler fed by observed rain is the same as the per-state lookup.
- The reviewer's [VERIFY] on the HCM capacity definition: not relied on. The verified sources show that the FHWA guide gives no definition, FHWA-HOP-07-073 uses the apex of a fitted curve, and the apparent HCM basis averages the top 5 % of flows.
- The CAV share of the weather effect: measured and reported (5.1, 5.5), not recalibrated, because no source says how CAVs respond to rain.

## Author questions and recommendations

- **Q1. How weather enters a day: one state per whole day, or rain episodes within a day?** Recommended: (a) One state per whole day, with dry, medium and heavy as regime cells. Treat weather as an observed regime, not a hidden condition. Why: I found no published UK share of hours by intensity class. It could only be derived from MIDAS Open or the Environment Agency 15-min API. Episodes would need runtime tau changes, which clash with the incident zone's save-and-restore of tau (incident.py:79-84). Whole-day states keep common random numbers simple. Disclose that a whole day at L08 intensities (≥2.54 mm/h) is a stress cell: about 37 % of English days have ≥1 mm, and lowland England has roughly 7-14 % wet hours.
- **Q2. Darkness: skip it, or add a speed-only regime of −5 km/h?** Recommended: (a) Skip it and disclose the omission. Possible later lead: an unlit night cell at the Korean CAF of 0.93. Why: The evidence for a lit 100 km/h motorway conflicts. On the A50 (full text) lighting changed neither capacity nor speed (about 0.5 km/h). In Sweden darkness changed speeds by −0.5 to −2 km/h, not significant. In Germany it was about −5 km/h (abstract only). Only mostly unlit Korean sites give a capacity factor (0.93 at 100 km/h). A −5 km/h regime would rest on one abstract.
- **Q3. Demand in rain: unchanged, or −5 %?** Recommended: (a) Unchanged, with no demand arm in the base. If a sensitivity row is wanted, use −3 %, made by thinning the dry arrival stream. Why: On the Dutch A16 motorway demand did not change (secondary). Monthly models find motorway exposure unchanged in rain (abstract). Dutch stated-preference data even show increases. The review gives mostly −2 % to −5 % (not −2 % to −8 %), and Scotland about −4 % (secondary, monthly data from the 1990s). Thinning keeps vehicle indices and the crash draws paired; a new Poisson stream would break that.
- **Q4. Crash risk in rain** Recommended: Option (a), done this way: recalibrate k for each wet state so that the expected crashes per day equal R × the dry value on the same seeds, with R = 1.71. Report-only rows at R = 1.31, 2.11 and 1.0, where 1.0 shows the bias of option (b). Why: k × R undershoots, because longer tau and lower speeds cut the TTC encounters. P(≥1 crash/day) is also not a rate. R = 1.71 is Qiu & Nixon 2008 (full text: +71 %, CI 31-111 %; +70 % for 1990-2005 studies). The motorway-only French value (2.38) is called an overestimate by its own authors, and the US daily +10 % is diluted. The only heavy-rain value is one record (+93 %), so both wet states use the same R. Disclose that R covers all crash types: rear-end risk in congestion is unknown, and the sources point both ways (Retallack, Golob & Recker, Tobin).
- **Q5 (new). How should CAVs behave in rain?** Recommended: Unchanged in the base, and disclosed. Add a report-only bound where every CAV class gets the human g and SAF. Name the cells by their realized plant-level ratios as well as by the L08 label. Why: I found no source on ACC or CACC gaps or speeds in rain. UN R157 gives no numbers above 60 km/h, and the Highway Code advice to double the gap is advisory. With 50 % CAVs, the realized effect is about half the sourced factor (the reviewer's arithmetic: fleet desired-speed ratio 0.976 / 0.966, against 0.951 / 0.931 for humans). Controllers that command CAVs therefore gain in wet cells by construction, and the bound is needed to read the results.
- **Q6 (new). How should the rain speed effect combine with lowered HDV speed limits (VSL)?** Recommended: Base: a non-compounding form, desired speed = min(sf × posted limit, SAF × sf × 100 km/h), set through each human vehicle's maxSpeed. Sensitivity: the multiplicative form through speedFactor. Report the VSL results under both. Why: SUMO's desired speed is speedFactor × lane limit, so scaling speedFactor would let a VSL command slow wet drivers further than dry ones. That would build a VSL effect into the wet cells by construction. There is no field basis for compliance with posted limits in rain.
- **Q7 (new). Incident passing zone in rain** Recommended: Keep f = 3 and measure the wet η per state against the wet QDF. Stop for the author if it differs from 0.54 by more than 0.10 (a proposed tolerance, not sourced). Why: The zone multiplies the wet tau (3 g tau), and η is defined against the dry QDF of 1,794 veh/h/lane. Knoop 2009 does not split by weather, so recalibrating f per state would aim at a target with no source. The reviewer's estimate is η_wet of about 0.50-0.52, but that was not measured.
- **Q8 (new). Seeds for the weather work** Recommended: The author names fresh ranges: 20 + 60 throw-away seeds for the g fit and confirmation, and 30 for the plant-level checks. Claude checks they are unused before any run. 7,430,040-049 are not reused. Why: The V135 calibration block 7,430,000-049 looks fully used (my grep of decisions.md and the code). 040-049 are selection-conditioned, because plant v188 was chosen on them. CLAUDE.md requires fresh seeds and the author's approval. Some 7,431,xxx numbers appear in p1 result files, so the reserved part of the block needs a check first.
- **Q9 (new). Which opponents count in weather cells?** Recommended: Two opponents per cell: one weather-scheduled (tuned per state on tuning seeds, used through a lookup) and one weather-blind (a single pooled tuning). A helper must beat the weather-scheduled one. The gap between the blind and scheduled opponents is reported. Why: Rain is observable, and the project rule takes I as a lookup from condition to parameters, tuned on tuning seeds. Otherwise a learning helper could win just by detecting rain. With whole-day states, a scheduler fed by observed rain is the same as the lookup.
- **Q10 (new). What the CAF is calibrated against** Recommended: Calibrate queue discharge (QDF) to the L08 CAF, which assumes the capacity drop is unchanged in rain, and disclose it. Report the pre-queue ratio and the wet drop (checked against the 2-11 % band), with a deviation note if the pre-queue ratio misses the CAF by more than its CI. Why: No opened source says whether the L08 or HCM factors scale pre-breakdown capacity or queue discharge. In NL the two fall alike (−5.7 % vs −5.6 %, −8.1 % vs −6.5 %). Kim 2010 finds similar breakdown drops in rain and dry weather. Dehman 2012 finds QDF more sensitive. The model's pre-queue measure is demand-limited and moved with detector placement (V185 vs V187). The reviewer found tau scaling moves pre-queue flow and QDF alike (0.931 vs 0.933).
- **Q11 (new). Add a light-rain cell?** Recommended: Not now. Revisit only if the regime results show a weather effect worth mapping in finer steps. Why: For light rain the sources range from 1.00 (L08 'nonsevere') to 0.98 (HCM 2010), 0.944 (NL discharge) and 0.89 (FHWA-HOP-07-073), so any value would be a choice. The medium target of 0.926 is close to the Dutch discharge value for rain above 1 mm/h (0.935), so the medium cell already stands for common heavier European rain.

## Review issues on draft v0

- critical: The ±0.02 pass band is narrower than the 10-seed sampling uncertainty of the paired wet/dry QDF ratio. Pass or fail for a grid point will be decided by noise, and neighbouring g values (step 0.05) cannot be told apart. Fix: Use 20-30 calibration seeds per state. Pool all grid points into a monotone fit of ratio against g and pick g by interpolation. Then confirm at the chosen g on new throw-away calibration seeds, and pass only if the bootstrap 95 % CI of the median paired ratio contains the CAF and the point estimate lies within ±0.02. Report the CI, not only the median.
- major: The QDF window is short and its length depends on the breakdown time. Wet runs break down earlier, so the wet and dry QDF are averaged over windows of different length and phase, which confounds the ratio. Fix: For this calibration, extend HOLD (e.g. to 3,600 s) and measure QDF over a fixed-length window, e.g. 20 min starting at tb+300, identical in both arms. Pre-register a run as invalid if the window does not fit. Report the window lengths.
- major: It is unclear what the target is. The SHRP 2 / HCM CAFs, as I understand them, scale pre-breakdown capacity, not queue discharge. Calibrating QDF to the CAF silently assumes the capacity drop is unchanged in rain. The model's 'pre' measure is too unreliable to serve as a target on its own. Fix: Pre-register QDF as the calibrated quantity and state openly the assumption that the drop is unchanged in rain. Report the wet/dry pre-queue ratio and the wet drop, with a check that the wet median drop stays within the V184 band of 2-11 % (calib.py:34). If the pre ratio departs from the CAF by more than its CI, report it as a known deviation.
- major: The grid probably does not reach the heavy-rain target, and the protocol has no rule for selection, bracketing or refinement. Fix: Extend the grid to about 1.5, with 0.05 steps above 1.2. Pre-register the rule: closest to the target; if two values bracket it, one refinement grid; otherwise stop for the author; then the confirmation run on new seeds.
- major: The natural way to apply g breaks common random numbers (CRN) and changes the CAVs, against the protocol's 'CAVs unchanged'. That route is scaling HDV_TAU_SCALE, the only tau knob calib.run_once exposes. Fix: Add a separate weather knob applied after acceptance: v.tau = round(g×tau, 3) after fleet.py:183, and v.sf ×= saf for hdv_car and truck only, after the draws. Check it with a test: the dry and wet fleets must share every class, length, lane, CAV tau and CAV sf, and the human tau must be exactly g× (dry tau).
- major: The incident zone composes multiplicatively with rain (tau × 3g) and was never calibrated in wet. Measured against wet queue discharge, crashes in rain would be more severe than the Knoop target, which is an artefact with no source behind it. Fix: Pre-register one of two options. (i) Keep f = 3 and report η_wet, measured on inc3 per state against the wet QDF (10 seeds × 2 states, same V199 rule). (ii) Recalibrate f per state so that η = 0.54 against the wet QDF. Disclose that Knoop 2009 does not condition on weather.
- major: Option 4(a), multiplying k by a field crash-rate ratio R, does not give R× crashes. In rain the encounters themselves fall, so k×R undershoots. P(≥1 crash/day) is also not a rate. Fix: On wet crash-free calibration days, recalibrate k_wet so that the expected crashes per day (or per veh-km) equal R × the dry value; demand is unchanged, so exposure is the same. Report the realized P(≥1) per state. Use a rear-end-specific R if one can be sourced, otherwise disclose. Under option (b), report the crash count per state as a known bias.
- major: CAVs keep their dry gaps and speeds, so the plant-level weather effect on v199 is roughly half the sourced CAF and SAF. The labels 'medium' and 'heavy' rain then overstate it, and controllers that command CAVs gain an advantage in wet cells by construction. Fix: Before the regime runs, measure the realized wet/dry ratios of pre-queue flow, QDF and free speed on the full v199 mix (V188 step 2 style ramp on ld32 and on ramp32). Name the cells by those realized values, report them, and disclose the CAV assumption in every table.
- major: A calibration on ld32 does not transfer to the on-ramp merge of ramp32. Larger human tau should make lane-change gap acceptance harder, and with teleporting off the ramp waits and merge breakdowns in rain are uncalibrated and could grow sharply. Fix: Add a ramp32 check per state, before the regime runs: no control, crash-free, human-only and full mix. Report the wet/dry discharge ratio at both bottlenecks (merge_up and up), the active bottleneck, ramp waits >60/300 s, the longest wait and whether runs drain. Pre-register a stop rule for deadlock or a failure to drain.
- major: Speed limits for HDVs (VSL) compound with the rain speedFactor, so a VSL command lowers wet human speeds further than in dry. VSL then looks different across regimes by construction. Fix: Pre-register how the rain factor interacts with a lowered limit: e.g. desired = min(sf×limit, saf×sf×LIMIT), done by capping maxSpeed, or keep the multiplicative form as a disclosed assumption with a sensitivity arm. Report VSL results under both.
- major: The delay reference depends on how the speed factor is implemented, and delays count only vehicles that arrived. Delays across weather cells are therefore not on a common basis. Fix: Pre-register both delay definitions (against the dry and against the wet desired speed) and TTT over a fixed window with unfinished vehicles counted to the window end. Use the same reference for all controllers within a cell.
- major: Comparing controllers across weather cells is unfair unless the proven controllers may also be scheduled by weather. Rain is observable in practice, so a learning helper could win just by detecting it. Fix: Pre-register three opponents per cell: tuned for each weather state (oracle lookup), a single tuning across states, and a non-learning scheduler driven by an observable rain signal. Report the adaptation gain against each.
- major: The mechanism behind the expected regime advantage, a shift of critical occupancy and density in rain, is never checked against field data. Fix: Report wet/dry critical density, critical occupancy and speed at capacity from the calibration runs, and compare them with the [14] tables if they give these [VERIFY]. If the gap is large, disclose it before any setpoint-based claim.
- minor: Trucks have no explicit tau, so a g applied through VehSpec.tau skips them silently. The truck maxSpeed cap also dilutes the truck speed reduction. Fix: Write tau = g×1.0 explicitly for wet trucks, decide whether the cap scales too, and state both. Define the free-speed check: loop, window (warm-up at 800 veh/h/lane) and time-mean against harmonic speed.
- minor: Breakdown detection uses an absolute 50 km/h threshold. That stays valid with SAF 0.93-0.95, but only as long as rain is implemented through speedFactor and not the lane limit. Fix: Pre-register the thresholds fixed at 0.5×100 km/h in every state and the speed effect via speedFactor only. Report the share of 30-s intervals between 40 and 60 km/h at 'up' as a sensitivity check.
- minor: The calibration simulator teleports after 300 s, while plant v199 runs with teleporting off, and the draft pass rule drops V187's zero-teleport and zero-collision requirement. Fix: Add 0 teleports and 0 SUMO collisions in both arms to the pass rule, or run the calibration with teleporting off as on the plant.
- minor: Option 3(b), demand -5 %, would regenerate the arrival stream and shift every vehicle index. That breaks CRN across states, including the crash draws keyed by index. Fix: If 3(b) is chosen, generate the dry stream and thin it with an independent seeded uniform per vehicle, keeping indices or IDs, so the wet fleet is a subset of the dry fleet.
- minor: Option 1(b), rain episodes, would need runtime setTau and setSpeedFactor calls, which clash with the passing zone's save-and-restore of tau. Fix: If 1(b) is chosen, compute tau from a single source of truth (base × rain(t) × zone flag) instead of saving and restoring.
- minor: Seeds: the protocol names no seeds for the per-state reference days or the regime runs. The calibration reuses 7,430,040-049, the seeds on which the dry plant was selected. Fix: Keep 040-049 for g as throw-away calibration seeds. Use new author-approved seeds for the confirmation run, the per-state k calibration and the regime runs, and record them in decisions.md.
- minor: The source values are not fully pinned down: rain intensity definitions are unchecked, the speed column does not match 100 km/h (about 62 mph), and HCM 2010 gives a different heavy-rain value. Fix: Check the SHRP 2-L08 intensity bins against [12]. Interpolate the 60/65 mph columns (about 0.926 / 0.872), or take 60 mph and disclose it. Run the heavy-rain cell with the HCM 2010 value as a sensitivity arm.

## Open [VERIFY] items

- SUMO 1.27.1: default tau for a Krauss vType of vClass trailer with no tau set (assumed 1.0); confirm before writing it explicitly.
- SUMO 1.27.1: vType maxSpeed caps the desired speed as min(maxSpeed, speedFactor × lane speed), and how it interacts with desiredMaxSpeed. The truck TRUCK_MAX cap already relies on this.
- SUMO 1.27.1: whether the LC2013 safe-gap check grows with tau. If so, ramp32 merging gets harder in rain (the reviewer's belief, unchecked).
- HCM 6th and 7th editions: whether the HCM 2010 Exh. 10-15 and SHRP 2-L08 Exh. 36-25 weather factors carried over, and whether they are defined against pre-breakdown capacity or queue discharge. The SHRP 2-L08 final report was not opened.
- HCM 2010 light-rain bound (0.10 in/h) against Agarwal et al. 2005 (0.01 in/h); check HCM 2010 directly.
- Koetse & Rietveld 2009 (+75 % accidents in precipitation, seen only via Snelder & Calvert); not opened.
- Bergel et al. French motorway paper: conference name and year (WCTR Lisbon 2010, inferred from the URL).
- Inaccessible lead: Seeherman 2014 dissertation (QDF −7.5 % drizzle, −10.8 % moderate, −19.3 % heavy; Pittsburg lane drop −11.2 %). Not used.
- Inaccessible lead: Seeherman's rendering of Brilon & Ponzlet (rain −175 / −150 veh/h/lane, darkness plus rain >250). The primary TRR 1555 paper is needed; its two secondary renderings conflict.
- Leads not opened: Dehman 2012 factor tables; Yuan et al. 2015 rainy-day discharge; Mejia et al. 2023 full text; Aksoy & Öğüt 2018 dry discharge values; Hammit et al. 2018 Gipps parameters by weather; Grove et al. 2015 truck ACC headways in adverse weather.
- UK hourly rain by intensity class (MIDAS Open or the EA Hydrology API): needed only for option 1(b) or for climate weighting of the cells. The CEH-GEAR1hr wet-hour percentages are read from a colour map.
- Kim & Lee 2015 attribute 'dark dry' reductions (13-25 %) to HCM 2010; the HCM exhibit is not identified.
- Reviewer computations not re-run here: dry QDF CV 5.0 %, CI half-widths 0.036-0.043 at 10 seeds, η_wet ≈ 0.50-0.52, and the fleet desired-speed ratios 0.976 / 0.966. Confirm them in the first calibration batch.
- My grep that the 7,430,000-049 block is fully used, and which 7,431,xxx numbers in p1 result files are seeds, before the author names the new ranges.
- UN R157 supplements after Amend.4 (March 2023) not checked; the text was read from a MarkLines mirror, not unece.org.
