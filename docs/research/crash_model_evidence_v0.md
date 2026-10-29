# Crash model evidence v0 (Layer B, conflict-driven crashes)

Checked 2026-10-29. Access codes: FT = full text opened; ABS = abstract only; DATA = official data file opened and processed by a script here; DERIVED = arithmetic done here from the cited inputs. Pages read through the web-fetch tool were summarised by a helper model, so they are marked "FT (fetch)". Verify any number before a thesis claim.

## Summary for the B2 design

1. Measure: rear-end TTC between same-lane follower and leader. Compute it ourselves every 1 s step from `vehicle.getLeader`. Do not use the SSM device runtime value for "conflict seconds": it is the minimum since the encounter began, not the current TTC (Q8).
2. Threshold: TTC < 1.5 s as the main value, with 1.0 s and 3.0 s as sensitivity arms. 1.5 s is the most used value (SSAM default, SUMO code comment, review tables). No study gives a crash-validated best TTC threshold for freeways.
3. The only EU motorway validation of TTC against crashes (Orsini et al. 2020, Italy, 19 sections) used extreme value theory (EVT) on negated TTC. Observed rear-end crashes fell inside the 95 % CI at about 90 % of sections.
4. A constant p per conflict-second assumes a fixed crash-to-conflict ratio. Published ratios vary from 1:1,000 to 1:100,000 and depend on manoeuvre type. Fitted crash–conflict relations are not linear (SSAM: crashes ∝ conflicts^1.42).
5. Recommended method: p depends on severity (lower TTC, higher p), with the shape taken from an EVT tail (GPD on −TTC) fitted to no-control runs. The scale is then calibrated to the 25 %/day target. Keep constant p as a sensitivity arm.
6. Base rate (derived): 25 %/day on 1 km at 25,000–35,000 veh/day means 8.2–11.5 crashes per million veh-km. Real freeways have about 0.6 (US urban, all reported crashes) and 0.03 (GB motorways, injury crashes). Even with a ×5 uplift for queue states, the target is about 3× too high. Treat it as a stress regime and say so.
7. Consequences: 30–60 min of blockage fits typical lane-blocking incidents (HCM defaults: mean 35–68 min). Severe crashes can last more than 2 h. On GB motorways, 57 % of injury collisions involve exactly 2 vehicles. Rear-end is the largest crash type (DE: 45 % of injury crashes).
8. Demand: on a motorway weekday the peak hour carries about 7.7 % of daily traffic (UK data, derived). So 25,000–35,000 veh/day gives a peak demand 1.4–1.9× the 1,400 veh/h capacity. About 18,000 veh/day puts the peak exactly at capacity. Check this against the plant design.
9. Mixed fleet: reviews question whether conventional SSMs and thresholds transfer to ACC/CACC/automated vehicles (ABS only).

## Q1. Surrogate measures and thresholds

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| SSAM default thresholds | TTC 1.5 s, PET 5.0 s | US software, intersections | [5] ch. 2 p. 10, ch. 4 p. 141 | FT |
| Why SSAM uses 1.5 s | Conflicts with TTC above 1.5 s are "not generally considered … 'severe' enough" for field conflict studies | general | [5] ch. 2 p. 15 | FT |
| SUMO code comment on TTC threshold | "1.5s. is an appropriate criticality threshold according to Van der Horst (1991)", while the SUMO default is 3.0 s | SUMO 1.27.1 | [2] line 81 | FT |
| SUMO code comment on DRAC threshold | 3.4 m/s² cited to AASHTO (2004); the SUMO default is 3.0 m/s² | SUMO 1.27.1 | [2] line 82 | FT |
| Thresholds used in the motorway SSM literature (review table) | TTC 1.5 s; MTTC 4 s (Ozbay 2008); PET 1–1.5 s; DRAC > 3.35 m/s² (Archer 2005); PSD < 1 | review inside a UK M1 study | [7] Table 1 | FT (author manuscript) |
| TTC depends on speed | The authors say "a single threshold value of TTC may not be appropriate" at different speeds | UK M1 motorway | [7] conclusions | FT (author manuscript) |
| Threshold choice changes conflict counts a lot | TTC 1.5 s gave 8× more conflicts than 1.0 s (Songchitruksa & Zha 2014, as cited) | connected-vehicle study | [6] discussion p. 26–27 | FT (author manuscript) |
| Studies linking crashes to conflicts use lower PET thresholds than other studies | regression result | intersections, 386 studies 2010–19 | [6] discussion | FT (author manuscript) |
| TTC validated against motorway rear-end crashes | Observed crashes inside the 95 % CI at ~90 % of 19 radar sections (BM and POT); 6-year crash data | Italy, two motorways, 2013 TTC data | [8] abstract, Tables 4–5 | FT |
| TTC used in that study | Normalised TTC (TTC minus the minimum observed TTC); POT thresholds −0.41 to −1.37 s on negated TTC | Italy | [8] §4.1 eq. 5, Table 3 | FT |
| Conflict-based real-time model on a motorway | Radar TTC defines unsafe states; model predicts them within 5 min with > 93 % accuracy, recall and specificity; beat the crash-trained model | Italy motorway | [9] abstract | ABS |
| Aggregated Crash Index beats TTC, PSD, CPI for rear-end risk | "outperforms" (no numbers in abstract) | Australia, Pacific Motorway | [10] abstract | ABS |
| TTC misses close-following risk at small or zero speed difference | TTCD had a higher Pearson correlation with rear-end crash rate than traditional SSMs (no value in abstract) | US, Ann Arbor CV pilot | [11] abstract | ABS |
| MTTC and a crash index validated with crash data | "strong relationship" with real accident data (no value in abstract) | US, New Jersey Turnpike, simulation | [12] abstract | ABS |
| TET/TIT defined from trajectories over a segment | threshold must be adapted when safer ACC is introduced | NL, ACC assessment | [13] abstract | ABS |
| Loop-detector rear-end risk index for freeways | index based on safe stopping distance | US freeway loops | [14] abstract | ABS |
| Conventional SSMs may not suit CAV safety | review warns that simulation tools and SSMs may not capture CAV behaviour | review | [52] abstract | ABS |

## Q2. From conflicts to crashes

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| Swedish TCT conversion factor | 1 accident per 1,000 to 100,000 conflicts | Sweden, urban intersections | [15] §3 intro, p. 24 | FT |
| Ratio depends on manoeuvre | about 1 police-reported injury accident per 8,000 serious conflicts (perpendicular car–car) vs 1 per 36,000 (parallel car–car) | Sweden (Hydén 1976; Linderholm 1981, as cited) | [15] §3.2.1, p. 28–29 | FT |
| Ratios between crash severity levels are not constant | They change over the hour of the week; 4.05 M crashes analysed | Germany (Berlin police; German Accident Atlas) | [16] §4 | FT |
| Rear-end conflict type: fewer serious, more light injuries than expected | qualitative | Germany | [16] §3 (mosaic plot) | FT |
| Crash–conflict regression (simulation) | ln(crashes) = 1.09 ln(conflicts) − 0.98, R² 0.27; crashes = 0.119 × conflicts^1.419, R² 0.41 | 83 intersections, British Columbia, VISSIM + SSAM | [5] Fig. 130–131, Table 83, p. 147 | FT |
| Volume-only model fitted better | R² 0.68 (ADT model) vs 0.27–0.41 (conflict models) | same | [5] p. 147–148 | FT |
| EVT block maxima (BM) on freeway | daily block maxima of −TTC; GEV shape −0.28 to −0.50 over 19 sections | Italy | [8] §5.1, Table 1 | FT |
| EVT peak over threshold (POT) on freeway | GPD shape −0.11 to −0.45; 163 to 11,989 exceedances per section in one year | Italy | [8] §5.2, Table 3 | FT |
| Crash probability from EVT | P(crash) = P(−TTC ≥ 0) = 1 − GEV(0) per block, or 1 − GP(0) per exceedance | Italy | [8] eq. 6, 9 | FT |
| Fit depends on segment length used for crash matching | observed within CI: 89.5 % (BM) and 84.2–94.7 % (POT) for 100–1,000 m; falls to 26–42 % at 5,000 m | Italy | [8] Tables 4–5 | FT |
| BM vs POT for freeway lane changes | POT better in data use, accuracy and reliability; return levels more robust than crash estimates | China, 29 freeway segments, 4,189 lane changes, PET | [17] abstract | ABS |
| Bivariate EVT on freeway merges | bivariate (PET + LPM) estimates closer to observed crashes and less uncertain than univariate | Canada, Highway 417 Ottawa | [18] abstract | ABS |
| EVT at intersections | 7 of 12 sites inside Poisson CIs; 3–6 weeks of observation needed | US, signalised intersections | [19] abstract | ABS |
| Pareto-based likelihood of a collision given a precursor event | method shown for road departures | theory + example | [21] abstract | ABS |
| Lomax model for P(crash given conflict) | small enough TTC thresholds allow unbiased estimates of expected crashes | theory + Monte Carlo | [20] abstract | ABS |
| Causal model: crash probability is a mixture over initiating conditions, weighted by evasive action | conflicts are proxies only under stated conditions | US freeway video (I-94) | [22] abstract | ABS |
| Near-crashes may not represent crashes | "severe discrepancy" between rear-striking near-crashes and crashes | US, 100-car naturalistic study | [23] abstract | ABS |
| Bivariate EVT with crash validation | bivariate better than univariate for rear-end and angle crashes | China, 10 intersections, drone video | [24] abstract | ABS |

## Q3. Simulated conflicts vs real crashes

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| Rank correlation, simulated conflicts vs crashes | Spearman 0.463 (ADT vs crashes: 0.788) | 83 intersections, British Columbia, VISSIM + SSAM | [5] ch. 4 test 1, p. 142 | FT |
| Simulation over-represents rear-end conflicts | rear-end 94.2 % of simulated conflicts vs 67.5 % of crashes | same | [5] Table 81, p. 143 | FT |
| Simulated "crashes" (TTC = 0) were mostly model artefacts | "most 'crashes' observed during simulation appeared to reflect anomalous behavior in the traffic model" and were filtered out | same | [5] p. 143 | FT |
| Calibration improves simulated vs field conflicts | rear-end conflict prediction MAPE 20 % after two-stage calibration | China, 10 signalised intersections | [25] abstract | ABS |
| Same at freeway merges | MAPE for total conflicts from 78.1 % to 33.4 %; rear-end 76.6 % to 33.5 % | China, freeway merge areas | [26] abstract | ABS |
| Calibration on safety measures (CPI) | GA-calibrated VISSIM matched observed safety measures | US, NGSIM data | [27] abstract | ABS |
| Simulation-based conflict prediction on an English motorway | VISSIM + SSAM conflicts used as labels; best random forest at 5-min aggregation; calibration flagged as key | England motorway | [28] abstract | ABS |
| Rule-based simulation conflicts gave no useful crash prediction; ML driver model did | EVT on simulated 2D-TTC conflicts | UK, 5 signalised intersections, Leeds | [29] abstract | ABS |
| SUMO crash injection ("blackout" of 3 s, constant speed) reproduces weekly crash peaks | activation probability per vehicle entering the zone: car 4.7 %, truck 1.6 %, bicycle 0.5 % | Germany, one Berlin intersection, SUMO via TraCI | [30] §2.2 | FT (preprint) |
| Collisions in SUMO are not crashes by default | Krauss is designed never to go below minGap; collisions need tau < step, apparentDecel < decel, driverstate, unsafe lane-change settings, etc. | SUMO docs | [3] "Deliberately causing collisions" | FT |
| No SUMO SSM vs freeway crash validation found | none | search 2026-10-29 | gap | – |

## Q4. Freeway real-time crash risk

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| Meta-analysis: speed variation | summary OR 1.225 (95 % CI 1.132–1.326), 5 estimates | freeways, international studies | [31] Table 7, p. 22–23 | FT (thesis) |
| Meta-analysis: average speed | OR 0.952 (0.909–0.996), 10 estimates (lower speed, more crashes) | same | [31] Table 7 | FT (thesis) |
| Meta-analysis: speed difference | OR 1.032 (1.026–1.038), only 2 estimates | same | [31] Table 7 | FT (thesis) |
| Meta-analysis: volume | OR 1.001 (1.000–1.001), 8 estimates | same | [31] Table 7 | FT (thesis) |
| Meta-analysis: coefficient of variation of speed | OR 2.76 (0.969–7.863), not significant | same | [31] Table 7 | FT (thesis) |
| Meta-analysis: average density | OR 0.968 (0.902–1.039); 0.909 after publication-bias correction | same | [31] Table 7 | FT (thesis) |
| Units of these ORs differ by study ("one additional unit") | caution for transfer | same | [31] §4.3 | FT (thesis) |
| Crash involvement rate by traffic state | bottleneck front, back of queue and congestion ≈ 5× free flow | US, I-880, 32 miles, 3 years | [32] abstract | ABS |
| Upstream occupancy and downstream CV of speed, 5–10 min before a crash | strongest predictors; > 69 % crash identification at log-odds threshold 1.0 | US, I-4 Orlando | [33] abstract | ABS |
| Short-term turbulence as crash precursor | precursors set objectively (no numbers in abstract) | Canada, Toronto freeway | [34] abstract | ABS |
| Crash-prone conditions from 110 video-recorded crashes | real-time model detected 58 % of crashes | US, I-94 Minneapolis | [35] abstract | ABS |
| Stopping shock waves and rear-end crashes | 41 shock waves, 5 crashes; crashes when reaction time > following headway | US, I-94 Minneapolis | [36] abstract | ABS |
| Volume, median speed and their variation by lane drive crash likelihood by type | qualitative | US, California freeways | [37] abstract | ABS |
| PDO crashes more likely in congested, variable-speed flow with many lane changes; severe crashes at high speed with large lane speed differences | qualitative | US, I-880 | [38] abstract | ABS |
| Motorway conflict risk varies with speed, density and weather | qualitative | UK M1 | [7] abstract | FT (author manuscript) |

## Q5. Crash consequences on motorways

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| Most common crash type on Autobahn: collision with a vehicle ahead or waiting | 45 % of injury crashes, n = 114,796, 2011–2016 | Germany | [39] §3.3.3, Fig. 24 (Destatis data) | FT |
| Same type among fatal crashes | 38 %, n = 2,166 | Germany | [39] Fig. 25 | FT |
| Rear-ending in injury crashes, 2010 | 38 % of 18,829 injury crashes (BMVI programme, as cited) | Germany | [39] §2.5 | FT |
| Longitudinal-traffic crash type (Unfalltyp) | 63 % (introduction, Destatis 2015) and 61 % (2011–2016) of injury crashes | Germany | [39] introduction, §3.3.2 | FT |
| Rear-end share, Italian motorways 2011–2016 | 29 % of all 5,632 crashes; 60 % of injury crashes (859/1,429); 46 % of fatal (23/50) | Italy | [8] §4.2 | FT |
| Vehicles per injury collision on motorways (incl. A(M)), 2024 | 1: 18.1 %; 2: 57.2 %; 3: 16.8 %; 4+: 7.9 % (n = 3,258) | GB | [41] collision file; count matches [40] | DATA |
| Two-vehicle collisions with one front and one back impact (rear-end proxy) | 1,085 = 58.2 % of 2-vehicle and 33.3 % of all motorway injury collisions | GB 2024 | [41] vehicle file, impact codes per STATS20 2011 §2.16 | DATA |
| Rear-end share, all state highways 2020 | 53,252 of 131,053 crashes = 40.6 % | US, California | [48] p. 114 chart; DERIVED share | FT |
| Default freeway incident lane impact | shoulder 75.4 %, 1 lane 19.6 %, 2 lanes 3.1 %, 3 lanes 1.9 % | US, HCM 7th ed. | [43] Table 15-6 | FT (fetch) |
| Default incident duration by lanes closed | mean 34 / 34.6 / 53.6 / 67.9 min (shoulder / 1 / 2 / 3+ lanes); max 58–93 min | US, HCM 7th ed. (all incidents, not only crashes) | [43] Table 15-6 | FT (fetch) |
| Incident duration classes | minor < 30 min; intermediate 30 min–2 h; major > 2 h | US, MUTCD 2003 §6I.01 | [44] | FT (fetch) |
| Motorway incidents cleared within 1 h | target ≥ 86 %; achieved 88.7 % (RP2, 2020–2025) | England, National Highways | [42] | FT (fetch) |
| Duration distribution shape | log-normal, log-logistic and Weibull are the usual fits | review | [45] §2.4, Table 2 | FT |
| Truck crash durations | log-normal within homogeneous groups; overturns longest | US, Los Angeles, > 9,000 crashes | [46] abstract | ABS |
| Crash durations (Weibull AFT with random parameters fits best) | qualitative | Australia, freeway network | [47] abstract | ABS |
| SUMO can stop colliding vehicles for a set time | `--collision.stoptime` | SUMO docs | [3] | FT |

## Q6. Base rates

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| Reported injury collisions on motorways | 45 per billion veh-miles in 2025; 80 in 2016 | GB | [40] sheet Collision_rates | DATA |
| Same in per million veh-km | 0.028 (2025); 0.050 (2016) | GB | DERIVED from [40] (1 mile = 1.609344 km) | DERIVED |
| Motorway injury collisions, count | 3,252 in 2025; 5,405 in 2016 | GB | [40] sheet Collisions | DATA |
| All reported crashes (incl. PDO), urban freeways | 0.78 per million veh-miles (2020); 0.95 (3-year 2018–2020) | US, California | [48] p. 7 table | FT |
| Fatal + injury crashes, urban freeways | 0.24 (2020); 0.30 (3-year) per million veh-miles | US, California | [48] p. 7 | FT |
| All crashes, rural freeways | 0.46 (2020); 0.49 (3-year) | US, California | [48] p. 7 | FT |
| Caltrans states it receives all processable reports, including PDO | statement | US, California | [48] §A | FT |
| Converted to per million veh-km | urban 3-year all crashes 0.59; F+I 0.19 | US, California | DERIVED from [48] | DERIVED |
| Autobahn casualties | 134 per billion veh-km (2 killed), 2011–2016 | Germany | [39] §3.1 | FT |
| Police-recorded crashes, all roads, 2024 | 2,512,697 total; 290,701 with injury (ratio 8.6) | Germany (all roads, not motorway only) | [49]; ratio DERIVED | FT (fetch) |
| Target λ for P(≥1 crash/day) = 25 % | λ = −ln(0.75) = 0.288 crashes/day | plant | DERIVED | DERIVED |
| Implied rate on 1 km | 0.288 / (ADT × 1 km / 10⁶) = 11.5, 9.6, 8.2 per million veh-km at 25k, 30k, 35k veh/day | plant | DERIVED | DERIVED |
| Same site at real US urban freeway rate | 5.4–7.5 crashes/year; P(≥1/day) 1.5–2.0 %; target is 14–20× higher | plant | DERIVED from [48] | DERIVED |
| Same site at GB motorway injury rate | 0.26–0.36 injury crashes/year; target is about 300–400× higher | plant | DERIVED from [40] | DERIVED |
| Queue states raise crash involvement about 5× | still about 3× below the target after this uplift | plant | DERIVED from [32] (ABS) and [48] | DERIVED |

## Q7. Weekday demand shape

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| Motorway weekday hourly share (mean of 10 single-direction MIDAS sites, Tue–Thu, 9 Sep–16 Oct 2025) | 00–05 h: 0.5–1.1 %/h; 06–07: 5.3; 07–08: 7.2; 08–09: 6.7; 10–14: 5.6–6.1; 15–16: 7.2; 16–17: 7.75 (peak); 17–18: 7.4; 18–19: 5.7; 19–20: 4.0; 22–23: 1.4 | England motorways (M1, M4, M6, M20, M25, M42, M60) | [51]; DERIVED profile | DATA |
| Share 07:00–19:00 | 77.9 %; 00:00–06:00: 5.7 % | same | [51] | DATA |
| Peak-hour share varies by site and direction | 7.55–9.91 % | same | [51] | DATA |
| All-roads weekday profile (Tue–Thu mean) | AM peak 08–09 h 7.9 % (2019), 7.7 % (2025); PM peak 17–18 h 8.4 % (2019), 16–17 h 8.3 % (2025); 07–19 h 80.6 % | GB, all roads | [50] sheet TRA0307; shares DERIVED from indices | DATA |
| Daily volume that puts the peak hour at 1,400 veh/h | about 18,000 veh/day | plant | DERIVED from [51] | DERIVED |
| Peak demand at 25k / 30k / 35k veh/day | 1,938 / 2,325 / 2,712 veh/h = 1.38 / 1.66 / 1.94 × capacity; 12–13 hours above 1,400 veh/h | plant | DERIVED from [51] | DERIVED |

Full profile (motorway, [51], share of daily traffic in %): 0.61, 0.51, 0.52, 0.65, 1.08, 2.35, 5.32, 7.23, 6.71, 6.02, 5.61, 5.70, 5.89, 6.10, 6.60, 7.21, 7.75, 7.41, 5.70, 4.00, 2.80, 1.96, 1.40, 0.89 (hours 00–01 to 23–24).

## Q8. SUMO SSM device (1.27.1)

| claim | value | country/setting | source + section | access |
|---|---|---|---|---|
| Measures computed | TTC, DRAC, PET, MDRAC; also PPET (in code, not described in docs); global BR, SGAP, TGAP | SUMO | [1] "Available SSMs"; [2] line 80 | FT |
| Default thresholds | TTC < 3.0 s; DRAC > 3.0 m/s²; MDRAC > 3.4 m/s²; PET < 2.0 s; PPET < 2.0 s; BR > 0; SGAP < 0.2 m; TGAP < 0.5 s | SUMO | [1] Parameters; [2] lines 81–90 | FT |
| Other parameters | range 50 m; extratime 5 s; mdrac.prt 1 s; file, trajectories, geo, write-positions, write-lane-positions, write-na, filter-edges.input-file, exclude-conflict-types | SUMO | [1] Parameters | FT |
| Output | `<SSMLog>` with `<conflict begin end ego foe>` holding minTTC, maxDRAC, PET, maxMDRAC (time, position, type, value, speed); one `<globalMeasures>`; full time series only with `trajectories` | SUMO | [1] Output | FT |
| Known gaps | merging DRAC incomplete; conflict area simplified; lateral conflicts with neighbour-lane traffic ignored; MDRAC tested only for types 0–8; no PET at unregulated junctions | SUMO | [1] notes | FT |
| Runtime access | `vehicle.getParameter(id, "device.ssm.minTTC" / "minPET" / "maxDRAC")`; code also accepts "maxMDRAC" and "minPPET"; error if the measure is not enabled; "" if no value | SUMO 1.27.1 | [1] TraCI; [2] lines 4272–4320 | FT |
| Runtime value is not instantaneous | it is the min (or max) over all active encounters of each encounter's extreme so far | SUMO 1.27.1 | [2] `getParameter` loop over `myActiveEncounters` | FT |
| Works with libsumo | yes, tested | test below | test | DATA |
| libsumo limits | no subscriptions that need extra arguments (except getLeader); GUI experimental | SUMO docs | [4] Limitations | FT |

Test done here (files in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/31d6d8e5-e88c-4870-9b77-cc7ccfbaac6c/scratchpad/crash_research/sumo_test/`):
- Network: 600 m with 2 lanes, then 600 m with 1 lane, 100 km/h, built with `netconvert`. Demand: 2,400 veh/h for 900 s, Krauss with sigma 0.5 and tau 1.0, step 1 s, seed 1. All vehicles equipped (`--device.ssm.probability 1`, measures `TTC DRAC PET MDRAC`, range 100 m). Run with libsumo 1.27.1 (`python -I`, SUMO_HOME unset).
- `getParameter` worked every step. Its value matched our own same-lane TTC (from `getLeader` gap + minGap, divided by closing speed) when TTC was falling, e.g. 8.65, 7.65, 6.65 s.
- After that it stayed at the earlier minimum (6.65 s while own TTC was 6.81 s and then 22.9 s). It kept falling (5.77 → 4.16 s) while the same-lane leader was not closing, so it also tracks foes on the other lane or the merge.
- Consequence: 14,354 vehicle-seconds with device minTTC < 3 s vs 752 with instantaneous same-lane TTC < 3 s (19× more). Do not use the device runtime value to count conflict seconds.
- Output file: 412 conflicts. Each one is written twice when all vehicles are equipped (206 of type 2 FOLLOWING_FOLLOWER and 206 of type 3 FOLLOWING_LEADER). Use `exclude-conflict-types foe` or deduplicate. 138 entries had minTTC < 1.5 s.
- No collisions with default settings. Wall time was 0.31 s with the device and per-step reads, and 0.08 s without (tiny run, not a benchmark).

## Gaps and risks

- No study validates SUMO conflicts (SSM device or own TTC) against freeway crashes. The freeway validations use radar or video TTC (Italy), or VISSIM (New Jersey, ABS only).
- No crash-to-conflict ratio for freeways was found. The only ratios found (1:8,000, 1:36,000, 1:1,000–100,000) are Swedish and mostly from urban intersections.
- The 3 s TTC threshold (SUMO default) has no crash-validated source here. The SUMO code comment itself cites 1.5 s.
- Many key freeway papers were read as abstracts only: [9]–[14], [17], [18], [32]–[38]. Their numbers beyond the abstract are unchecked.
- Not opened (blocked or not found): Le (2009) TAMU thesis on VISSIM conflicts vs crashes at freeway weaving sections; Mahmud et al. (2017) review; the Tarko et al. (2009) TRB white paper; Hydén (1987); Van der Horst (1991); Archer (2005); the published version of the Roshandel meta-analysis (AAP 79, 2015). Claims from them appear only "as cited".
- The meta-analysis ORs [31] are from the 2014 MEng thesis, not the 2015 journal paper. Values may differ. Units differ by study.
- Crash duration: no EU distribution of crash blockage time was found. The UK KPI gives only the share cleared within 1 h. HCM defaults are US data for all incidents, not crashes only.
- German Autobahn crash rate per veh-km was not obtained, because the Destatis tables were not reached. The German total-to-injury ratio (8.6) covers all roads.
- GB data cover injury collisions only. The rear-end proxy (front + back impact) is our own rule. 2024 data mix the 2011 and 2024 STATS19 specifications.
- COVID affects the Caltrans 2020 rates and the RAS0302 2020–2021 figures. The 3-year Caltrans rates soften this.
- WebTRIS profile: 10 random sites, one direction each, 6 autumn weeks. The directional peak (AM vs PM) differs by site.
- A constant p per conflict-second ties crash counts to the step length and the threshold. Results must be reported with the threshold sensitivity arms.
- ACC/CACC/ALKS vehicles may make conventional TTC thresholds less meaningful (review [52], ABS).

## Sources

1. Eclipse SUMO. SSM Device (docs page, last edited 16 April 2025). https://sumo.dlr.de/docs/Simulation/Output/SSM_Device.html
2. Eclipse SUMO. `src/microsim/devices/MSDevice_SSM.cpp`, tag v1_27_1. https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_27_1/src/microsim/devices/MSDevice_SSM.cpp
3. Eclipse SUMO. Safety (docs page, last edited 12 October 2026). https://sumo.dlr.de/docs/Simulation/Safety.html
4. Eclipse SUMO. Libsumo (docs page). https://sumo.dlr.de/docs/Libsumo.html
5. Gettman, D., Pu, L., Sayed, T., Shelby, S. (2008). Surrogate Safety Assessment Model and Validation: Final Report. FHWA-HRT-08-051. https://www.fhwa.dot.gov/publications/research/safety/08051/08051.pdf
6. Arun, A., Haque, M.M., Washington, S., Sayed, T., Mannering, F. (2021). A systematic review of traffic conflict-based safety measures with a focus on application context. Analytic Methods in Accident Research 32, 100185. Author manuscript: https://eprints.qut.edu.au/212594/1/Manuscript_19_07_2021_AA.pdf
7. Formosa, N., Quddus, M., Ison, S., Abdel-Aty, M., Yuan, J. (2020). Predicting real-time traffic conflicts using deep learning. Accident Analysis & Prevention 136, 105429. Author manuscript: https://ndownloader.figshare.com/files/21808122
8. Orsini, F., Gecchele, G., Gastaldi, M., Rossi, R. (2020). Large-scale road safety evaluation using extreme value theory. IET Intelligent Transport Systems 14(9), 1004–1012. https://www.research.unipd.it/retrieve/f77d0ba0-0a9b-41fb-9a2e-18b0978fe0f8/2020_IET-ITS_Orsini_etAl.pdf
9. Orsini, F., Gecchele, G., Rossi, R., Gastaldi, M. (2021). A conflict-based approach for real-time road safety analysis: Comparative evaluation with crash-based models. Accident Analysis & Prevention 161, 106382. Abstract via Europe PMC (PMID 34479121).
10. Kuang, Y., Qu, X., Wang, S. (2015). A tree-structured crash surrogate measure for freeways. Accident Analysis & Prevention 77, 137–148. Abstract via Europe PMC (PMID 25710638).
11. Xie, K., Yang, D., Ozbay, K., Yang, H. (2019). Use of real-world connected vehicle data in identifying high-risk locations based on a new surrogate safety measure. Accident Analysis & Prevention 125, 311–319. Abstract via Europe PMC (PMID 29983165).
12. Ozbay, K., Yang, H., Bartin, B., Mudigonda, S. (2008). Derivation and validation of new simulation-based surrogate safety measure. Transportation Research Record 2083, 105–113. https://doi.org/10.3141/2083-12 (abstract via OpenAlex)
13. Minderhoud, M.M., Bovy, P.H.L. (2001). Extended time-to-collision measures for road traffic safety assessment. Accident Analysis & Prevention 33, 89–97. Abstract via Europe PMC (PMID 11189125).
14. Oh, C., Park, S., Ritchie, S.G. (2006). A method for identifying rear-end collision risks using inductive loop detectors. Accident Analysis & Prevention 38, 295–301. Abstract via Europe PMC (PMID 16246286).
15. Svensson, Å. (1998). A method for analysing the traffic process in a safety perspective. Doctoral thesis, Lund Institute of Technology. https://lucris.lub.lu.se/ws/files/4456913/1653512.pdf
16. Junghans, M., Leich, A., Nippold, R., Wagner, P. (2025). Quantifying the upper levels of Hydén's traffic safety pyramid using global data. Traffic Safety Research 9, e000102. https://elib.dlr.de/215917/2/e000102.pdf
17. Zheng, L., Ismail, K., Meng, X. (2014). Freeway safety estimation using extreme value theory approaches: A comparative study. Accident Analysis & Prevention 62, 32–41. Abstract via Europe PMC (PMID 24129319).
18. Zheng, L., Ismail, K., Sayed, T., Fatema, T. (2018). Bivariate extreme value modeling for road safety estimation. Accident Analysis & Prevention 120, 83–91. Abstract via Europe PMC (PMID 30098455).
19. Songchitruksa, P., Tarko, A.P. (2006). The extreme value theory approach to safety estimation. Accident Analysis & Prevention 38, 811–822. Abstract via Europe PMC (PMID 16546103).
20. Tarko, A.P. (2018). Estimating the expected number of crashes with traffic conflicts and the Lomax distribution. Accident Analysis & Prevention 113, 63–73. Abstract via Europe PMC (PMID 29407670).
21. Tarko, A.P. (2012). Use of crash surrogates and exceedance statistics to estimate road safety. Accident Analysis & Prevention 45, 230–240. Abstract via Europe PMC (PMID 22269505).
22. Davis, G.A., Hourdos, J., Xiong, H., Chatterjee, I. (2011). Outline for a causal model of traffic conflicts and crashes. Accident Analysis & Prevention 43, 1907–1919. Abstract via Europe PMC (PMID 21819818).
23. Jonasson, J.K., Rootzén, H. (2014). Internal validation of near-crashes in naturalistic driving studies. Accident Analysis & Prevention 62, 102–109. Abstract via Europe PMC (PMID 24144495).
24. Wang, C., Xu, C., Dai, Y. (2019). A crash prediction method based on bivariate extreme value theory and video-based vehicle trajectory data. Accident Analysis & Prevention 123, 365–373. Abstract via Europe PMC (PMID 30597330).
25. Huang, F., Liu, P., Yu, H., Wang, W. (2013). Identifying if VISSIM simulation model and SSAM provide reasonable estimates for field measured traffic conflicts at signalized intersections. Accident Analysis & Prevention 50, 1014–1024. Abstract via Europe PMC (PMID 23000074).
26. Fan, R., Yu, H., Liu, P., Wang, W. (2013). Using VISSIM simulation model and Surrogate Safety Assessment Model for estimating field measured traffic conflicts at freeway merge areas. IET Intelligent Transport Systems 7(1), 68–77. https://doi.org/10.1049/iet-its.2011.0232 (abstract via OpenAlex)
27. Cunto, F., Saccomanno, F.F. (2008). Calibration and validation of simulated vehicle safety performance at signalized intersections. Accident Analysis & Prevention 40, 1171–1179. Abstract via Europe PMC (PMID 18460386).
28. Katrakazas, C., Quddus, M., Chen, W.-H. (2018, online 2017). A simulation study of predicting real-time conflict-prone traffic conditions. IEEE Transactions on Intelligent Transportation Systems 19(10), 3196–3207. https://doi.org/10.1109/tits.2017.2769158 (abstract via OpenAlex)
29. Liu, X., Prato, C.G., Markkula, G. (2026). Improving crash frequency prediction from simulated traffic conflicts using machine learning based microsimulation. arXiv:2606.12500. https://arxiv.org/abs/2606.12500
30. Nippold, R., Leich, A., Wagner, P. (2026). Reproducing weekly crash patterns using a minimalist driver error model. SUMO User Conference 2026, preprint. https://sumo.dlr.de/preprints/pre-print-3232.pdf
31. Roshandel, S. (2014). Impact of real-time traffic characteristics on freeway crash occurrence: systematic review and meta-analysis. MEng (Research) thesis, Queensland University of Technology. https://eprints.qut.edu.au/79151/ (published as Roshandel, Zheng, Washington, Accident Analysis & Prevention 79, 198–211, 2015, not opened)
32. Yeo, H., Jang, K., Skabardonis, A., Kang, S. (2013). Impact of traffic states on freeway crash involvement rates. Accident Analysis & Prevention 50, 713–723. Abstract via Europe PMC (PMID 22795398).
33. Abdel-Aty, M., Uddin, N., Pande, A., Abdalla, M.F., Hsia, L. (2004). Predicting freeway crashes from loop detector data by matched case-control logistic regression. Transportation Research Record 1897, 88–95. https://doi.org/10.3141/1897-12 (abstract via OpenAlex)
34. Lee, C., Hellinga, B., Saccomanno, F. (2003). Real-time crash prediction model for application to crash prevention in freeway traffic. Transportation Research Record 1840, 67–77. https://doi.org/10.3141/1840-08 (abstract via OpenAlex)
35. Hourdos, J., Garg, V., Michalopoulos, P.G., Davis, G.A. (2006). Real-time detection of crash-prone conditions at freeway high-crash locations. Transportation Research Record 1968, 83–91. https://doi.org/10.1177/0361198106196800110 (abstract via OpenAlex)
36. Chatterjee, I., Davis, G.A. (2016). Analysis of rear-end events on congested freeways by using video-recorded shock waves. Transportation Research Record 2583, 110–118. https://doi.org/10.3141/2583-14 (abstract via OpenAlex)
37. Golob, T.F., Recker, W.W., Alvarez, V.M. (2004). Freeway safety as a function of traffic flow. Accident Analysis & Prevention 36, 933–946. Abstract via Europe PMC (PMID 15350870).
38. Xu, C., Tarko, A.P., Wang, W., Liu, P. (2013). Predicting crash likelihood and severity on freeways with real-time loop detector data. Accident Analysis & Prevention 57, 30–39. Abstract via Europe PMC (PMID 23628940).
39. Richter, T., Seebo, D., Daghestani, H., Martin, D., Hofmann, W. (2023). Ansätze zur Verbesserung der Verkehrssicherheit auf Bundesautobahnen. UDV Forschungsbericht Nr. 79, GDV, Berlin. https://www.udv.de/resource/blob/130998/103ded9eaf113e61851a464843e306d2/79-vs-auf-bab-data.pdf
40. Department for Transport (2026). RAS0302: Reported road collision and casualty numbers and rates by severity, road type and class, GB, 10 years up to 2025. https://assets.publishing.service.gov.uk/media/6a63992ce2d191f0bc8b6ef2/ras0302.ods
41. Department for Transport. STATS19 open data 2024: collisions https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2024.csv and vehicles https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-2024.csv; code list STATS20 (2011) https://assets.publishing.service.gov.uk/media/60d0cc968fa8f57cf3f0b3ad/stats20-2011.pdf
42. Office of Rail and Road. Annual assessment of National Highways' performance, end of the second road period (April 2020 to March 2025). https://www.orr.gov.uk/annual-assessment-national-highways-performance-end-second-road-period-april-2020-march-2025-0
43. Texas DOT. Transportation Systems Planning manual, §15.4.4.3 Traffic Incidents, Table 15-6 (source stated: HCM 7th edition). https://www.txdot.gov/manuals/des/tsp/chapter-15-transportation-system-management-and-op/15-4-performance-measurement/15-4-4-factors-affecting-travel-time-reliability/15-4-4-3-traffic-incidents.html
44. FHWA. MUTCD 2003, Chapter 6I, §6I.01. https://mutcd.fhwa.dot.gov/htm/2003/part6/part6i.htm
45. Li, R., Pereira, F.C., Ben-Akiva, M.E. (2018). Overview of traffic incident duration analysis and prediction. European Transport Research Review 10:22. https://etrr.springeropen.com/track/pdf/10.1186/s12544-018-0300-1
46. Golob, T.F., Recker, W.W., Leonard, J.D. (1987). An analysis of the severity and incident duration of truck-involved freeway accidents. Accident Analysis & Prevention 19, 375–395. Abstract via Europe PMC (PMID 3675808).
47. Tavassoli Hojati, A., Ferreira, L., Washington, S., Charles, P. (2013). Hazard based models for freeway traffic incident duration. Accident Analysis & Prevention 52, 171–181. Abstract via Europe PMC (PMID 23333698).
48. Caltrans (2022). 2020 Crash Data on California State Highways. https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/annual-collision-data/2020_crash_data_on_chswy-webv3-a11y.pdf
49. Destatis. Verkehrsunfälle und Verunglückte im Zeitvergleich (table). https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Verkehrsunfaelle/Tabellen/liste-strassenverkehrsunfaelle.html
50. Department for Transport. TRA0307: Traffic distribution by time of day and day of the week on all roads, GB (May 2026). https://assets.publishing.service.gov.uk/media/6a0b7e78c510c3913d8267ce/tra0307-traffic-distribution-by-time-of-day.ods
51. National Highways. WebTRIS API v1.0, Daily 15-min reports for sites 12358, 1850, 4313, 4519, 289, 10722, 788, 18501, 14280, 6174, 9 Sep–16 Oct 2025. https://webtris.nationalhighways.co.uk/api/v1.0/
52. Wang, C., Xie, Y., Huang, H., Liu, P. (2021). A review of surrogate safety measures and their applications in connected and automated vehicles safety modeling. Accident Analysis & Prevention 157, 106157. Abstract via Europe PMC (PMID 33975090).

Scripts used for DATA and DERIVED rows: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/31d6d8e5-e88c-4870-9b77-cc7ccfbaac6c/scratchpad/crash_research/tools/` (`stats19.py`, `webtris.py`, `profile.py`, `ods.py`, `epmc.py`, `oa.py`, `oa_title.py`).
