# Driving-parameter distributions for HDV and CAV: sourced values for SUMO randomization (v0)

v0, 2026-10-28, branch `v5b1`. Input: verified research claims in seven groups, plus a SUMO 1.27.1 parameter map checked against the 1.27.1 source and libsumo 1.27.1.

## How to read this note

- **Only verified values are used.** A value appears only if the verifier marked its claim "confirmed", or "partly" and supplied a corrected value. Rows marked "corr." use that corrected value. Everything else is in Section 6.
- **Access tags.** The tag is what the verifier actually read: FT means full text, ABS means abstract only. Rows marked "ABS: re-read before citing" must be checked against the full text first. No value read only in a search snippet is used.
- **Region.** Every value has a region. Much of the CAV evidence, and a good part of the HDV evidence, comes from the US. Check that it transfers before you use it for a European plant.
- **Derived values.** "derived" means arithmetic by a research agent or by me on sourced numbers. The source does not state it.
- **[VERIFY].** A value cited through another paper is marked [VERIFY], because the original was not read.
- **Gap or headway.** In SUMO, `tau` for Krauss works on the net gap, from the leader's rear to the follower's front. Some sources report gross front-to-front headway, which includes the vehicle length. Those rows say "gross".

**Calibration warning.** Every parameter we randomize is also a calibration knob. If many are randomized at once, it becomes hard to say why the plant behaves as it does (rule E3, V153). After any change to the vType set or its distributions:

- recalibrate the plant;
- re-run the V139 and T1a/T1b checks;
- only then collect gate data.

Calibrate only one or two means. Keep the shapes of the distributions fixed to their sources.

## 1. Summary

| Quantity | HDV-car | HDV-truck | CAV | SUMO attribute |
|---|---|---|---|---|
| Net time gap in following | Close following at about 60-70 km/h and above: mean 1.1-1.15 s, SD 0.42-0.43, sample cut at 2 s (UK) [1]. Most probable gap: 0.75 s in free flow, 1.2-1.9 s upstream of a bottleneck (NL) [2]. Per-driver means 0.98-1.68 s at 90-108 km/h (US) [4] | About equal to cars in UK close following (P70 less than 0.1 s higher) [1]. Larger than cars in NL and DE data [2][6]. DE legal floor: 50 m above 50 km/h [8] | ACC at its shortest setting: peaks 0.9-1.5 s (IT, SE) [13]; fitted values 0.54-1.13 s (US) [15]. Longest setting: 1.7-3.5 s [13][15]. ISO minimum τ ≥ 0.8 s [21]. CACC settings 0.6-1.1 s; 0.6 s chosen 57 % of the time (US) [18]. Truck CACC: 1.2 s most used (US) [19]. ALKS up to 60 km/h: 1.0-1.6 s for cars, 1.2-2.4 s for heavy vehicles [22] | `tau`; for CACC also `tauCACCToACC` |
| Standstill gap | Jam spacing including vehicle length: mostly 5-9 m (US NGSIM) [9]. Queue gap mean 3.66 m (US; ABS: re-read before citing) [10]. No EU data | 5 % of NGSIM jam spacings exceed 10 m, and all of those are heavy vehicles [9] | Fitted ACC jam gap 5.1-15.0 m, partly theoretical (US) [15]. Fitted Δ 0.66-7.28 m (US) [16]. ALKS floor: 2 m for cars, 2.4 m for heavy vehicles [22] | `minGap` |
| Acceleration (maximum desired) | Start-up intercept α 1.8-2.2 m/s², from below-average to above-average drivers (US design values) [26]. Per-frame motorway acceleration ~ Logistic(0.137, 0.167) (DE) [25] | Tractor-semitrailer drivers: α 0.15-0.37 m/s². Vehicle maxima: 0.45-0.89 m/s² (US) [26]. EU tractors: 250-380 kW at 40 t [28] | ISO maximum 2.0 m/s² (secondary source) [37]. openpilot clip 2.0 [41]. Measured ACC: 2.0-2.7 m/s² at 10-40 km/h, 0.57 m/s² at 90 km/h (US) [37] | `accel` |
| Normal deceleration | 95 % of braking time at 1-3 m/s²; 3-4 m/s² is called comfortable (EU) [29]. Design value 3.4 m/s² (US, via [30]) | No sourced value | ISO ≤ 3.5 m/s² (secondary source) [37][38]. Measured ACC: 98 % of decelerations milder than 2 m/s² (US) [37]. ALKS minimum-risk manoeuvre aims at ≤ 4.0 m/s² [32]. AV comfort: 1.0-1.5 m/s² [36] | `decel` |
| Emergency deceleration | Full stop, non-professional drivers: 7.4 m/s² dry, 7.0 wet. Professional drivers: 8.4 dry, 7.9 wet (DK) [30]. Type-approval floor 6.43 m/s² [33]. highD minimum −6.3 m/s² [25] | Type-approval floor 5.0 m/s² (1996 text) [34]. Braking in a wet curve, limited by stability: 0.16-0.27 g [35] | ALKS: a demand above 5.0 m/s² counts as an emergency manoeuvre [32] | `emergencyDecel` |
| Reaction time or update interval | Brake reaction to unexpected events: means 1.2-1.5 s; lognormal median 1.19 s (US) [45][46]. Car-following delay 1.36-1.54 s (NL) [47]. Per-vehicle SUMO action step: median 0.30 s (US arterial) [50] | 1.51 s, against 1.54 s for cars (NL) [47] | ACC response time 1-1.5 s (HU) [59]; minimum estimates 1.6-2.6 s (IT, SE) [13]. Fitted lag 0.15-0.99 s (US) [15]. V2V latency: ITS-G5 2-4 ms, LTE PC5 21-38 ms (NL, BE) [62][123] | `actionStepLength` (proxy only); EIDM `treaction` |
| Driver imperfection | Krauss sigma per vehicle: mean 0.34, median 0.30, right-skewed (US arterial) [50] | No sourced value | Not applicable: ACC, CACC and IDM ignore sigma | `sigma` |
| Perception error | Model assumptions only: gap error 5 %, inverse-TTC error 0.01 /s, error memory 20 s [52]. Looming threshold about 0.003 rad/s (ABS: re-read before citing) [107] | No sourced value | Radar: ±0.1-0.4 m range, ±0.1 km/h speed (datasheet) [115]. Camera: about 5 % range error at 44 m [119] | `device.driverstate.*`; EIDM `sigmagap`, `sigmaleader` |
| Lane-change gap acceptance | Critical net gap 0.68-0.9 s (DE) [69]. Mandatory changes, critical gap: lead 1.17 s, lag 1.26 s (US) [70]. Discretionary changes, median gap: lead 1.72 s, lag 1.91 s (US) [71] | No EU value | ALKS: may make the target-lane follower brake at most 3.0 m/s² and must keep at least 1.0 s [22]. lcAssertive about 0.85, matched to a prototype [82]. Humans cut in closer in front of an AV: median 7.58 m vs 9.57 m (US) [85] | `lcAssertive` (only through a simulation match) |
| Lane-change duration | Mean 5.7 s [6] or 7.6-7.8 s [74] (DE; the two studies define start and end differently) | 6.2 s [6] or 8.3-8.5 s [74] | AV 6.43 s vs human 6.63 s, urban roads (US) [84]. R79 limit: under 5 s for cars, under 10 s for heavy vehicles [83] | `--lanechange.duration` or `maxSpeedLat` |
| Lane-change rate | Falls from about 1 to 0.5 per veh-km as density rises (UK) [73]. About 0.24 per veh-km (DE, derived) [25] | Mostly between lanes 1 and 2 (DE) [74] | No sourced value | Calibration target for `lcSpeedGain`, `lcKeepRight` |
| Desired speed | Free flow at a 70 mph limit: mean 68 mph, 44 % above the limit (UK) [90]. Mean 99.7 km/h at a 100 km/h limit, all traffic states (DE) [95] | Articulated HGVs: mean 55 mph, 2 % above 60 mph (UK) [90]. Semitrailers at an 80 km/h limit: mean 85.5 km/h, V85 88 km/h (AT) [93]. EU limiter: 90 km/h [92] | ALKS must follow limits and stay at or below 130 km/h [22]. ISA speed control holds speed between the limit minus 5 km/h and the limit [102] | `speedFactor`, `maxSpeed` |
| Compliance with static or variable limits | Static 100 km/h without enforcement: 26 % complied (DE, 1984/85) [96]. Enforced VSL at 40 mph: about 85 % (UK) [100]. Advisory VSL: mean 18 km/h above the display, SD 11 (US) [101] | About 90 % of trucks with 3 or more axles drive above 80 km/h (AT) [93] | With ACC, drivers sped less (NL) [5] or more (US; ABS: re-read before citing) [103] | `speedFactor` × limit; TraCI at each VSL change |
| Information available to the controller | Point detectors: about 15 % of 30-s samples missing (US) [126]; 5-40 % of loops failed on a given day, depending on district (US) [127]; DE type-approval tolerance 10-20 % per lane-minute [134] | Same as cars | Probe data: penetration 0.08 % (AT) [139]; latency about 4 min (US) [138]. CAMs every 0.1-1 s [121] | No SUMO attribute: corrupt the readings in the controller layer |

## 2. Evidence by group

### 2.1 Time gap and standstill gap

**HDV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| Net gap in close following | Mean about 1.1 s, SD 0.42 s. Filters: gap ≤ 2 s, speed difference ≤ 1.5 m/s, speed ≤ 100 km/h. The value applies at about 70 km/h and above; it is not a pooled all-lane figure | UK (M25, M42 loops) | [1] Abstract, Summary, Sec. 3.1 | FT, corr. |
| Same, M25 middle lane, 60-100 km/h | Mean 1.15 s, SD 0.43 s, min 0.2 s, max 2.0 s (the max is the filter cap) | UK | [1] Sec. 3.1, Fig. 2 | FT |
| Speed dependence | About 1.5 s at 15 km/h and 1.1 s at 75 km/h. Below 70 km/h, Eq. 2 gives GH = 1.5 − 0.006·v. Above 70 km/h, offside lanes have smaller gaps | UK | [1] Sec. 3.1-3.2 | FT |
| Lower tail and shape | About 15 % of drivers keep ≤ 0.5 s (60-80 km/h). The distribution is left-skewed and the author rejects normality. He samples from the empirical CDF (Fig. 5) | UK | [1] Sec. 3.3, Figs. 5-6 | FT, corr. |
| HGV vs small-car followers | 70th percentile of HGV gaps less than 0.1 s higher (60-70 km/h); K-S test not significant. Holds within the ≤ 2 s filter. HGVs are banned from the offside lanes | UK | [1] Sec. 3.4, Fig. 7 | FT |
| Most probable net gap, by density | 0.75 s in free flow (fast lane). Upstream of a bottleneck: 1.2 s at 25-50 veh/km/lane, 1.9 s above 50. Slow lane somewhat higher. Truck followers behind cars: "considerably higher" (truck = length ≥ 6 m), no number given | NL (A9) | [2] Fig. 2 | FT |
| Mean net gap, dense synchronized flow | 2.25 s at ≥ 45 veh/km/lane. The SD of 0.29 s is the spread of 50-vehicle means, not the spread between drivers | NL (A9) | [2] Fig. 1 | FT |
| Gross headway, free flow, left lane, no speed limit | Mode about 0.68 s, almost independent of density. A non-negligible share is near 0.2 s. A speed limit moves the mode up | DE (A3, A1) | [3] Fig. 10 | FT |
| Per-driver mean steady-state gap, 7 drivers | 90-108 km/h: 0.98-1.68 s (COV 24-50 %). ≥ 108 km/h: 0.97-1.86 s. 18-36 km/h: 1.53-2.67 s. Pooled median: 1.2 s at 90-108 km/h and 2.5 s at 18-36 km/h | US (naturalistic, Washington DC) | [4] Table 2, Sec. 4.2 | FT |
| Fitted shape, 90-108 km/h | Pearson 5 with α 7.75, β 8.78, γ 0; implied mean about 1.30 s (derived). K-S, χ² and A-D all reject the fit on the full sample (88,692 points). It passes K-S only after down-sampling to ≤ 10 % | US | [4] Tables 4-5 | FT, corr. |
| Share of 10-s intervals with a gap below 1 s | 33.6 % (1,887 of 5,622). Manual and ACC/LKS driving are pooled | NL (motorways) | [5] Sec. 3.1 | FT |
| Gross headway at lane-change events | Cars: mean 1.53 s, SD 1.05, median 1.20, P25-P75 0.80-1.93. Heavy vehicles: mean 2.76 s, SD 2.36, median 1.92, P25-P75 0.99-3.90. n = 7,674 cars, 746 heavy vehicles | DE (highD) | [6] Table 1 | FT |
| Minimum headway kept when instructed (secondary) | 0.64-0.69 s, nearly constant from 50 to 100 km/h. Original: Taieb-Maimon & Shinar 2001 [VERIFY] | Not stated | via [4] p. 3 | FT (secondary) |
| Mean net gap above 55 km/h (secondary) | About 1.25 s, instrumented vehicle. Original: Brackstone et al. 2009 [VERIFY] | UK | via [1] p. 662 | FT (secondary), corr. |
| Manual headway assumed in a simulation | 1.64 s gross headway, drawn at random within ±10 % (1.48-1.8 s). The draw distribution is not stated. This is a simulation assumption | US | [18] Sec. 13 | FT, corr. |
| Driving-code advice | At least 2 s on high-speed roads, at least doubled on wet roads | UK | [7] Rule 126 | FT |
| Legal truck distance | Trucks above 3.5 t and buses must keep ≥ 50 m on the Autobahn above 50 km/h. This is a distance, not a time gap: about 2.25 s at 80 km/h and 2.0 s at 90 km/h (derived). Compliance is unknown | DE | [8] § 4(3) | FT |
| Jam spacing (Newell d*, includes vehicle length) | About 180 pairs. Most d* lie at 5-9 m (mean vehicle length 4.5 m). 10 % are below the vehicle's own length. 5 % exceed 10 m, all of them heavy vehicles. The implied standstill gap of 0.5-4.5 m is an inference; the paper does not state it | US (NGSIM I-80) | [9] Sec. 5, Table 1 | FT |
| Spacing in stopped queues | Mean 3.66 m, with no difference between sites. Probably bumper to bumper, but the abstract does not define it | US | [10] Abstract | ABS: re-read before citing |
| SUMO defaults | `tau` 1.0 s (for Krauss, on the net gap); `minGap` 2.5 m for passenger, truck, trailer and bus | n/a | [11][12] | FT |

**CAV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| ACC headway at the shortest setting, campaign N.1 | Peaks about 0.9 s (Hyundai Ioniq) and 1.3 s (Volvo XC40) | IT (public freeways) | [13] Sec. 4.1, Fig. 14 | FT |
| ACC headway at the shortest setting, campaign N.2 | KIA Niro 1.1 s, Mitsubishi Outlander 1.5, Ford S-Max 1.3, VW Golf E 1.4, Peugeot 3008 1.1. Cut-ins cause long upper tails | IT | [13] Sec. 4.1, Fig. 8 | FT |
| ACC headway at min / max settings, campaign N.3 | Tesla Model 3 1.3/2.7 s, BMW X5 1.2/2.5, Audi A6 1.2/3.5, Mercedes A 1.2/2.5. Overall about 1 s and 2.5 s. Human and ACC ranges are both roughly 1-4 s; the human distributions are more uniform | SE (AstaZero) | [13] Sec. 4.4, Fig. 11, Sec. 5 | FT |
| ACC min / max setting and response time | Minimum setting "a bit over 1 s"; maximum up to 3.5 s; response time 1.7-2.5 s | EU (JRC) | [14] Abstract | ABS: re-read before citing |
| Fitted ACC time gap th, model s = η + th·v, 7 vehicles | Minimum settings 0.544-1.127 s; maximum settings 1.734-2.054 s | US | [15] Table II | FT |
| Fitted jam gap η | 5.131-14.956 m. Vehicles A-D disengage below 25 mph, so their η is never physically reached | US | [15] Table II | FT |
| Lincoln MKZ ACC, 4 settings, model spacing = l + Δ + τ·v | High speed: τ 0.83 / 1.21 / 1.61 / 2.17 s with Δ 4.83 / 4.40 / 3.31 / 0.66 m. Low speed: τ 0.79 / 1.14 / 1.52 / 2.09 s with Δ 7.28 / 6.36 / 5.92 / 4.97 m | US | [16] Table 3 | FT |
| PATH prototype settings | CACC: 1.1, 0.9, 0.7, 0.6 s. ACC: 2.2, 1.6, 1.1 s | US | [17] PDF p. 39 | FT |
| ACC settings chosen by members of the public | 1.1 s 50.4 %; 1.6 s 18.5 %; 2.2 s 31.1 % | US (CA freeways) | [18] Sec. 13, Fig. 13.1 | FT |
| CACC settings chosen by members of the public | 0.6 s 57 %; 0.7 s 24 %; 0.9 s 7 %; 1.1 s 12 %. The mean CACC gap was 45 % of the mean ACC gap | US | [18] Sec. 13 | FT |
| Truck CACC use, 9 professional drivers | Gaps 0.6 / 0.9 / 1.2 / 1.5 / 1.8 s used 26.0 / 10.3 / 43.3 / 8.0 / 12.5 % of the time (mean epoch share). ACC settings 1.1-1.9 s. Stated preference: 1.2 s and 1.5 s | US (CA, Volvo Class 8) | [19] Table 1, Results; [66] | FT |
| Truck platooning minimum gap (project specification, not a standard) | Level A > 0.8 s, Level B > 0.5 s, Level C > 0.3 s, steady state at 80 km/h. Level A may use up to 1.5 s | EU (ENSEMBLE) | [20] Table 1 | FT |
| ISO 15622:2018 | τmin ≥ 0.8 s. At least one setting between 1.5 and 2.2 s above 8 m/s. Time gap = clearance / speed, i.e. a net gap | ISO | [21] cl. 6.2.3.1 | FT (preview) |
| ALKS minimum time gap | M1/N1: 1.0 s at 7.2 km/h, then 1.1 / 1.2 / 1.3 / 1.4 / 1.5 / 1.6 s at 10 / 20 / 30 / 40 / 50 / 60 km/h. M2/M3/N2/N3: 1.2-2.4 s at the same speeds. Linear interpolation between rows. Above 60 km/h national rules apply, with no number given | UNECE | [22] para. 5.2.3.3 | FT |
| ALKS minimum distance near standstill | ≥ 2 m (M1, N1) and ≥ 2.4 m (M2, M3, N2, N3) below 2 m/s | UNECE | [22] para. 5.2.3.3 | FT |
| Waymo AV vs human headway (gross, lognormal) | AV µ 1.25, σ 0.43; human µ 0.99, σ 0.49. The paper does not say whether µ is on the log scale. AVs following human drivers keep larger headways in every speed range. Mostly urban streets | US | [23] Sec. III.B | FT |
| Number of settings | BMW 5 series: 4; Tesla Model S: 7. Seconds per setting not given | NL (study cars) | [5] Sec. 2.1.1 | FT |
| Manufacturer example | 3 bars = 1.8 s (about 50 m at 100 km/h); 3-5 bars recommended | EU (Ford handbook) | [24] p. 156 | FT |

**Mapping notes.**

- **Net-gap sources.** [1], [2], [4], [21] and [22] report net gaps, so they map onto Krauss `tau` without conversion.
- **Gross-headway sources.** [3], [6] and [23] report gross headway; remove the vehicle length before mapping onto `tau`. The definition used in openACC [13] was not checked.
- **Linear model fits.** The fitted τ in [15] and [16] is closest to `tau`, and their η or Δ is closest to `minGap`. A Krauss vehicle given the same τ will not reproduce the same equilibrium exactly.

### 2.2 Acceleration and deceleration

**HDV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| Per-frame acceleration, cars | Logistic(0.137, 0.167). All vehicles: Logistic(0.122, 0.147); mean offset +0.12 m/s². Reading the two numbers as (location, scale) is an interpretation. SD about 0.30 m/s² (derived as s·π/√3). Free driving and car following are mixed | DE (highD) | [25] Sec. VI.B | FT |
| Per-frame acceleration, trucks | Logistic(0.088, 0.073); SD about 0.13 m/s² (derived) | DE (highD) | [25] Sec. VI.B | FT |
| Extremes, all classes | Maximum +5.6, minimum −6.3 m/s². Below −5.0 in 5 tracks, below −4.0 in 15. 0.9 % of vehicles brake at ≤ −1.5 (2.7 % at < −1.0). Clear weather | DE (highD) | [25] Sec. VI.B, Fig. 22 | FT |
| Start-up from rest, model a = α − β·v, observed through cars | α 2.02 m/s²; β 0.1184-0.1326 /s (Bonneson [VERIFY]) | US | [26] Table 2 | FT (review) |
| Recommended design start-up values | Above-average drivers 2.2 / 0.11; average 2.0 / 0.12; below-average 1.8 / 0.13; average left turn 2.0 / 0.22 (α in m/s² / β in 1/s) | US | [26] Table 2 | FT (review) |
| Tractor-semitrailer (WB-15) start-up | Vehicle maximum α: 0.89 / 0.58 / 0.48 / 0.45 m/s² at 100 / 200 / 300 / 400 lb/hp. Drivers: average 0.37 / 0.02, below average 0.15 / 0.01. Observed tractor-trailers: 0.15 / 0.01 | US | [26] Table 2 | FT (review) |
| Observed deceleration, average drivers | α 3.0 m/s², β 0.133 (NCHRP 154, 1974); 3.23 / 0.165 (1937). Old data [VERIFY] | US | [26] Table 2 | FT (review) |
| Legal minimum engine power | ≥ 5.0 kW per tonne of permissible gross weight for trucks; 2.2 kW/t for tractors | DE | [27] § 35 | FT |
| EU tractor-trailer power and mass | 250-380 kW; 330-350 kW engines have a 39 % share. Maximum combination 40 t. Assumed curb mass 7.4 t tractor + 7.0 t trailer. VECTO long-haul payload 19.3 t. Power-to-weight 6.3-9.5 kW/t at 40 t (derived) | EU | [28] pp. 5, 13, 20 | FT |
| Everyday braking | About 95 % of braking time at 1-3 m/s²; 2-4 % at 3-4; less than 1 % above 4. Recorded maxima 7-9 m/s². 37 drivers, 1 Hz GPS speeds, rates below 1 m/s² excluded | EU (NL, UK, DE, BE) | [29] Sec. 5.2 | FT |
| Strong braking events, n = 32 | Maximum deceleration 1-2 m/s²: 9 %; 2-3: 22 %; 3-4: 44 %; 4-5: 13 %; 5-6: 13 %. Selection rule: speed drop ≥ 40 km/h | EU | [29] Table 5, Sec. 5.3.3 | FT, corr. |
| Comfortable deceleration | 3-4 m/s². National sight-distance guidelines for design speeds ≥ 100 km/h assume 3.1 (FR, NL) to 3.9 m/s² (CH) | EU | [29] Summary p. 7, Sec. 5.3.2 | FT |
| Emergency stop, whole braking run | Professional drivers: 8.4 dry, 7.9 wet. Non-professional: 7.4 dry, 7.0 wet; per-car cells 6.5-8.7. 22 drivers | DK (test tracks) | [30] Tables 4.5-4.6 | FT, corr. |
| AASHTO design deceleration (secondary) | 3.4 m/s². About 90 % of drivers brake harder than 3.4; most brake above 4.5 for an unexpected object [VERIFY] | US | [30] Sec. 1.1.2 | FT (secondary) |
| Near-crash average deceleration, 10th percentile | 0.352 g at 80 km/h, 0.343 at 97, 0.338 at 105, 0.329 at 121 (about 3.36 m/s² at 97 km/h, derived). Vehicle class not a meaningful variable | US (SHRP2) | [31] Table 5.12 | FT |
| Reference attentive driver in ALKS approval | 0.75 s to the start of braking; 0.6 s jerk phase to 0.774 G (about 7.6 m/s², derived); 0.85 G after a full cut-in | UNECE (JP, NHTSA data) | [32] Annex 3, Table 1 | FT |
| Type-approval floor, cars (M1) | 6.43 m/s² with the engine disconnected (100 km/h); 5.76 with it connected | UNECE (R13-H) | [33] Annex 3, 2.1.1 | FT |
| Type-approval floor, heavy vehicles (1996 text) | 5.0 m/s² with the engine disconnected (M1: 5.8); 4.0 with it connected (M1: 5.0) | UNECE (R13 Rev.3) | [34] Annex 4 | FT |
| Tractor + semitrailer braking in a 152 m curve, wet (µ about 0.45) | 0.156-0.273 g. These values are limited by stability, not by brake capability | Not stated | [35] Table 1 | FT |
| Chauffeur's two-step deceleration | First jerk −0.9 to −1.5 m/s³ for about 1 s (releasing the accelerator), then −0.3 to −0.6 m/s³ (braking) | DE (test track) | [36] Sec. 2.3.1.2 | FT |
| SUMO defaults: accel / decel / emergencyDecel | Passenger 2.6 / 4.5 / 9; truck 1.3 / 4 / 7; trailer 1.0 / 4 / 7 in the docs, but libsumo 1.27.1 returns trailer accel 1.1; bus 1.2 / 4 / 7. The docs say accel and decel are "convenient" values, not maxima | n/a | [12]; SUMO map | FT |

**CAV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| ISO 15622:2010 limits (quoted) | Deceleration ≤ 3.5 m/s² averaged over 2 s; negative jerk ≤ 2.5 m/s³ averaged over 1 s [VERIFY] | ISO | [37] pp. 5-6 | FT (secondary) |
| Measured ACC acceleration from standstill, 2017 Audi Q7, 9 runs | Average by speed (km/h: m/s²): 0: 0.36; 10: 2.02; 20: 2.10; 30: 2.66; 40: 2.36; 50: 2.01; 60: 1.75; 70: 1.53; 80: 1.17; 90: 0.57. It sometimes exceeds the ISO 2.0 m/s² maximum | US (VA) | [37] Table 2 | FT |
| Measured ACC deceleration | 98 % of decelerations milder than −2 m/s²; effective maximum 2.0 m/s² | US | [37] pp. 10, 16 | FT |
| ISO 15622:2018 (paraphrased) | Average acceleration over 1 s ≤ 2 m/s²; deceleration not beyond −3.5 m/s²; jerk −2.5 m/s³ [VERIFY] | ISO | [38] Sec. V | FT (secondary) |
| ISO 15622:2018 (summarised) | Deceleration bound from −5 m/s² at low speed to −3.5 at high speed. The acceleration bound is printed "−4 to −2"; the sign is probably a typo (not verified) [VERIFY] | ISO | [39] Sec. 4.4 | FT (secondary) |
| Speed-dependent ACC acceleration limit, market cars and openpilot | a*(v) = a0 + (vc − v)·β with a0 ≈ 0.4 m/s², vc ≈ 40 m/s, β ≈ 0.015 /s, so about 0.58 m/s² at 100 km/h (derived). One human emergency of about −5 m/s² was nearly double the ACC limit | US | [40] Eq. 15, Fig. 13 | FT |
| openpilot clips | ACCEL_MAX 2.0, ACCEL_MIN −3.5, COMFORT_BRAKE 2.5, A_CRUISE_MIN −0.5 m/s². Cruise jerk 1.6 / 1.2 / 0.8 / 0.6 m/s³ at 0 / 10 / 25 / 40 m/s | Open source | [41] | FT |
| Autoware constraints (low-speed configuration) | Normal: ±1.0 m/s², jerk ±1.0. Limit: −2.5 / +1.0 m/s², jerk ±1.5 | Open source | [42] | FT |
| ALKS emergency boundary | Any deceleration demand above 5.0 m/s² is an emergency manoeuvre | UNECE | [32] 5.3.1.1 | FT |
| ALKS minimum-risk manoeuvre | Aim at ≤ 4.0 m/s²; short peaks allowed | UNECE | [32] 5.5.1 | FT |
| ALKS test scenario | Lead vehicle brakes at ≥ 6 m/s² (mean fully developed) to a stop. Risk perception starts when the lead exceeds 5 m/s² | UNECE | [32] Annexes 3, 5 | FT |
| AV deceleration profiles rated comfortable, 36 passengers | One step: −1.0 m/s², jerk −0.6. Two steps: −0.5 then −1.0 m/s² (jerks −1.0, −0.3), or −0.5 then −1.5 (jerks −1.0, −0.6). All rated positive | DE (test track) | [36] Tables 1-2 | FT |
| Comfort literature (secondary) | Well-perceived peak deceleration −0.5 to −1.3 m/s²; jerk perception threshold about 0.53 m/s³ [VERIFY] | Mixed | [36] Sec. 1 | FT (secondary) |
| AV comfort bounds used as an assumption | Acceleration ±1.25 m/s², jerk ±1 m/s³ (from de Winkel et al. 2023, not read) [VERIFY] | n/a | [38] Sec. V | FT (assumption) |

### 2.3 Reaction time, update interval, imperfection, string stability

**HDV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| Brake reaction time by expectancy | 0.70-0.75 s when fully expected; about 1.25 s for unexpected but common signals such as lead-car brake lights; roughly 1.5 s for a surprise | Not stated | [43] Abstract | ABS: re-read before citing |
| Brake onset vs kinematic urgency | Eyes-off-threat events: 141 of 142 brake within 1 s after the looming threshold (τ⁻¹ ≥ 0.2 s⁻¹), on average 0.42 s after it. Eyes-on-threat: 66 % within 1 s. 323 events, including trucks and buses | US (SHRP2), ANNEXT (US, Africa) | [44] Sec. 2, 3.3 | FT |
| Naturalistic brake reaction time | No secondary task: mean 1.120 s (SD 0.884). All safety-critical events: 1.255 (0.932). With a secondary task: 1.332 (0.950). Test track (NCHRP 400): 1.140 (0.204). Overall mean 1.3 s, P90 2.2 s | US | [45] p. 18 | FT |
| Unexpected events, earlier studies (mean / SD / P85 / P95, s) | Sivak 1982: 1.21 / 0.63 / 1.78 / 2.40. Wortman & Matthias: 1.30 / 0.60 / 1.80 / 2.35. Chang: 1.30 / 0.74 / 1.90 / 2.50. Olson & Sivak, young drivers: 1.10 / 0.15 / 1.35 / 1.60. Lerner: 1.51 / 0.40 / 1.91 / 2.20. Fambro: 0.99 / 0.22. Dozza 2013: 1.30 / 1.03. Cai & Savolainen: 1.51 / 1.24 / 2.61 / 8.44 [VERIFY originals] | Mostly US | [45] p. 14 | FT (secondary table) |
| Expected events | Olson & Sivak, young: 0.72 / 0.11 / 0.95 / 1.11 s; old: 0.73 / 0.10 / 1.00 / 1.29. Fambro: 0.59 / 0.19. Fitch: 0.78 / 0.03 | Mostly US | [45] p. 14 | FT (secondary table) |
| Reaction to lead-car brake lights in traffic, 87 drivers | Mean 1.38 s, SD 0.56. Lognormal: median 1.19 s, dispersion 0.390. P85 1.78, P90 1.96, P95 2.26 s. Across three data sets: median 1.1-1.2 s, mean 1.3-1.4 s | US | [46] Table 2 | FT |
| Car-following delay Tr, GHR-type fits, 518 triples | One-leader model 1.36 s (SD 0.28); two-leader model 1.54 s (SD 0.49). Heavy congestion | NL (A15) | [47] Table 3 | FT |
| Truck vs car drivers | Truck followers 1.51 s (SD 0.56, n 65); car followers 1.54 (0.46, n 428); followers of a truck 1.57 (0.64, n 67). No significance test | NL (A15) | [47] Table 4 | FT |
| Historical car-following delay | 1.2 s (Herman & Potts 1959, New York tunnels) [VERIFY] | US | [47] Sec. 2 | FT (secondary) |
| Interval between action points | Mean 2.5 s; driver means 1.8-4 s; exponential tail. Acceleration relaxation time about 0.5 s | JP (inferred), test track | [48] | FT |
| SUMO semantics | `actionStepLength` defaults to the step length. It resembles a reaction time but is not a true delay. A `tau` below the reaction time gives unsafe driving | n/a | [49] | FT |
| Per-trajectory calibrated Krauss `actionStepLength` | Mean 0.40 s, SD 0.28, P10 0.10, P50 0.30. The upper value 0.90 is labelled P95 in the table but P90 in the text. Bounds 0.1-1.0 s; SUMO 1.19 | US (urban arterial) | [50] Table 4 | FT |
| Per-trajectory calibrated Krauss `sigma` | Fit on speed, gap and acceleration: mean 0.34, SD 0.20, P10 0.12, P50 0.30, upper value 0.75. Fit on speed and gap: 0.51 / 0.22 / 0.21 / 0.51 / 0.91. Right-skewed, not Gaussian. `sigmaStep` mean 0.49 s | US (urban arterial) | [50] Table 4 | FT |
| Acceleration noise in free driving | Normal; SD 0.01 g ± 0.002 g (about 0.10 m/s²) at 20-60 mph, 4 drivers. Holland Tunnel: 0.73 ft/s² (about 0.22 m/s²) | US | [53] Sec. 2.2 | FT |
| Noise that reproduces platoon oscillations (stochastic IDM) | Typical intensity Q about 0.2 m²/s³. Q = 0.32 at marginal stability nearly matches the platoon data. Alternative: action points with Δa_max 1.2 m/s² and Q = 0 | CN data, DE model | [54] Sec. 2, 4 | FT (model) |
| Oscillation growth along a 25-car platoon | Speed SD grows almost linearly with car number when the leader drives at 7 or 15 km/h, and concavely at 30-50 km/h. At car 25 the speed SD is about 1.0-1.9 m/s (approximate reading of Fig. 5) | CN | [55] Fig. 5 | FT, corr. |
| UN R157 "careful driver" benchmark | Perception time 0.4 s plus braking delay 0.75 s. It brakes only when TTC < 2 s, reaching 7.6 m/s² 0.6 s after onset. In 27 of 34 SHRP2 cut-ins it braked later than the humans, and it crashed in 3 events | UNECE, US validation | [56] Sec. 2.2.1 | FT |

**CAV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| Fitted ACC lag τ, 7 models | 0.153-0.994 s: 0.284-0.993 s at the minimum settings, 0.153-0.994 s at the maximum. All 14 fits are string-unstable. More than 1,200 miles of driving | US | [15] Table II | FT, corr. |
| Measured ACC platoon instability | A 6 mph slowdown grew to 25 mph along 7 identical cars; the last car's ACC disengaged | US | [15] Sec. IV-C | FT |
| 2015 luxury EV ACC | Minimum setting: τe 0.516 s, η 8.34 m. Maximum: 1.688 s, 7.57 m. Unstable at both | US | [57] Table I | FT |
| ACC response time, one controller | 0.8-1.2 s | EU (JRC) | [58] Abstract | ABS: re-read before citing |
| Minimum response times, 11 ACC systems | 1.6-2.6 s; median 1.9 s (derived). The authors call them indicative | IT, SE | [13] Table IV | FT |
| Response times, AstaZero campaign | Tesla 1.9 s, BMW 2.7, Mercedes 2, Audi 2.6; never below 0.7 s. String-unstable, especially at short settings. The same paper's Table IV gives lower minima for these cars | SE, IT | [13] Sec. 4.4, Sec. 5 | FT |
| Multi-brand platoon, 10 vehicles | 1-1.5 s is representative; no link with target speed (30-60 km/h) | HU (ZalaZONE) | [59] Sec. 5.2 | FT |
| String stability vs time-gap setting | Shortest gap: the perturbation more than doubles from the 2nd to the last vehicle. Longest gap: median indicator about 0.5 at the last vehicle. Medium gap: roughly neutral. 33 perturbations at 30-40 km/h | HU | [59] Sec. 5.3.1 | FT |
| Level-2 platoon on public roads | Unsuitable for platoons of more than about 3-4 vehicles | NL | [60] Abstract | ABS: re-read before citing |
| ISO time-gap range and review verdict | ISO 15622: 0.8-2.2 s (secondary) [VERIFY]; ADAC guideline 1.8 s. The review concludes that commercial ACC is not string-stable because response times are long | ISO, DE | [61] | FT (secondary) |
| V2V latency in CACC field tests | ITS-G5: mode about 4 ms, mean 3.4-3.9 ms, SD 1.0-1.7, P95 4-5 ms, PER < 0.02 % (CAM) and < 0.1 % (iCLCM). LTE PC5: mode 22-25 ms, mean 38.0 ms (CAM) and 30.8 ms (iCLCM), SD 13-15, P95 65 / 56 ms, values up to 80 ms, PER 4.5-5 %. 25 Hz, 2 Toyota Prius, no other traffic | NL (Lelystad) | [62] Sec. 3, Table 1 | FT, corr. |
| Maximum constant delay for string stability (analysis) | 29 / 111 / 300 ms at time gaps of 0.3 / 0.6 / 1.0 s. Vehicle lag 0.1 s, actuator delay 0.2 s; packet loss ignored | NL | [62] Sec. 2 | FT (analysis) |
| CACC fallback in the field prototype | Falls back to ACC after 3 lost packets or latency above 100 ms. String-stable at 0.3 s over ITS-G5 and LTE PC5 (2-vehicle platoon). Over LTE Uu with TLS on, the follower's deceleration was amplified | NL | [62] Sec. 3.4, Table 2 | FT, corr. |
| 3GPP platooning requirements | Lowest automation: 30 msg/s, 25 ms, 90 %. Highest: 30 msg/s, 10 ms, 99.99 %, 80 m. Sensor sharing: 20 ms. Reporting: 2 msg/s, 500 ms | 3GPP | [63] Table 5.2-1 | FT |
| Truck powertrain delay and lag (simulation assumption) | 0.1-0.3 s each; gains tuned for a 0.8 s gap. The authors state that trucks have longer delays and lags than cars | US | [67] | FT (assumption) |

### 2.4 Lane changing and merging

**HDV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| On-ramp merge, post-encroachment time (137 merges) | Merging behind a mainline vehicle: median 4.0 s, P25 2.6. Merging in front: median 3.0 s, P25 2.0. Merging into a gap (accepted gap): roughly uniform on 5.0-15.1 s, mean 9.7 ± 2.9 | DE (A39) | [68] Sec. IV, Fig. 10 | FT |
| Critical net gap to the target-lane follower (Raff's method) | Cooperative lane changes 0.68 s. Lane changes right after an on-ramp merge 0.9 s. Gaps above 5 s excluded | DE (highD, exiD) | [69] Sec. 3 | FT |
| Gross headway at cut-ins | 0.1-4 s, peak at 1 s; 850 cut-ins | DE (highD) | [25] Sec. IV | FT |
| Critical gaps in mandatory lane changes (gamma) | Pooled mean: lead 1.17 s (variance 0.82), lag 1.26 s (variance 0.87). Gamma α / β, uncongested: adjacent→shoulder lane lead 1.54 / 0.80, lag 2.42 / 0.47; shoulder→adjacent lead 1.49 / 0.61, lag 1.10 / 0.92. Congested: adjacent→shoulder lead 1.88 / 0.71, lag 1.98 / 0.71; shoulder→adjacent lead 1.78 / 0.66, lag 1.57 / 0.79. In congestion lag gaps are 22 % and lead gaps 15 % larger. About 30 % of drivers are inconsistent. Only gaps ≤ 5 s analysed | US (NGSIM I-80) | [70] p. 11, Table 6 | FT |
| Accepted gaps in mandatory lane changes | Mean 1.34 s. Mean accepted gap 1.29 s uncongested, 1.40 s congested. Median 1.13 s in both data sets | US | [70] | FT, corr. |
| Discretionary lane changes, 477 cases | Median lead gap 1.72 s, lag gap 1.91 s; heavy-tailed, lognormal preferred. Mean relative speed: lag +1.43 m/s, lead −0.35 m/s | US (I-294, TGSIM) | [71] Slides 5-7 | FT |
| Share of headways below 1 s, all vehicles vs lane-changing vehicles | 24.6 vs 52.1 %; 15.6 vs 46.6 %; 15.5 vs 41.8 % (three sites) | CN | [72] Table 10 | FT |
| Lane-change rate | About 1 per veh-km in very light traffic, falling to about 0.5 near capacity. The absolute count starts to fall at about 25 veh/km | UK (M42) | [73] | FT |
| Lane-change rate | 0.83, 1.04, 0.86 per veh-km (three sites) | CN | [72] Table 2 | FT |
| highD totals | 110,500 vehicles, 45,000 km driven, 11,000 lane changes (5,600 complete in view); 77 % cars, 23 % trucks. About 0.24 lane changes per veh-km (derived). Maximum lane-change rate at about 3,500 veh/h total on 3 lanes (Busch 1984 [VERIFY]) | DE | [25] Sec. IV, V-B | FT |
| Discretionary lane-change duration, cars | Left: n 1,355, mean 7.57 s, SD 1.60, range 3.56-15.12. Right: n 1,550, mean 7.79 s, SD 1.63, range 4.32-21.60 | DE (highD location 1, limit 120 km/h) | [74] Table II | FT |
| Same, heavy vehicles | Left: n 213, mean 8.34 s, SD 1.92. Right: n 220, mean 8.45 s, SD 1.76. Longer than cars (Mann-Whitney p reported as 0.000); direction not significant | DE | [74] Tables II-III | FT |
| Lane-change duration, survival analysis | Cars: n 7,674, mean 5.70 s, median 5.55 s. Heavy vehicles: n 746, median 6.08 s, mean 6.20 s (6.22 in the text). Generalized gamma has the lowest BIC; for trucks, lognormal has a slightly lower AIC | DE (highD) | [6] Tables 1-2 | FT, corr. |
| Lanes used in truck lane changes | Heavy vehicles: left changes 1→2 198, 2→3 15; right changes 2→1 205, 3→2 15. Cars: 1→2 312, 2→3 1,043; 2→1 452, 3→2 1,098 (lane 1 = rightmost) | DE | [74] Table I | FT |
| Truck lane-change motives, 142 events with another vehicle near | Overtaking 60.1 %; avoiding merging vehicles 30.0 %. Mean range rate −1.66 m/s (left changes), +1.40 m/s (right). Suggested threshold for right changes: range below 12.7 m (P10) | US (naturalistic trucks) | [75] Results | FT |
| Left-lane ban | Trucks above 3.5 t and vehicles with trailers may use the left lane only to queue for a left turn (3 or more lanes, outside built-up areas) | DE | [76] § 7(3c) | FT |
| Zipper rule | Traffic in the continuing lane must let blocked vehicles merge alternately, one after each vehicle, just before the narrowing | DE | [76] § 7(4) | FT, corr. |
| Zipper compliance in work zones | Closed-lane use 29 %, 49 % (congested) and 11 %; 50 % means perfect use. +0.6 % per 100 veh/h; −1.5 % per +10 % trucks in the closed lane; an upstream message sign adds 2.3-5.1 % | US (Michigan) | [77] Table 25 | FT |
| Lane closure at roadworks | 75 % of vehicles changed lane once, 20 % twice, 5 % more. Hotspots near the signs at 700, 400 and 120 m, and where the works first become visible. Left-lane use about 10 % at peak | SE (E20) | [78] Sec. 3-4 | FT |
| Lane flow on 3 lanes | Right lane saturates around 800 veh/h, left lane around 2,600 veh/h (Busch 1984 [VERIFY]). highD shows the same trend | DE | [25] Sec. V-A | FT |
| Capacity drop of default SUMO at a merge | Maximum / average drop: SUMO basic 3.78 / 1.24 %; SUMO zipper 1.72 / 1.13 %; Aimsun 17.16 %; SymuVia 7.04 %; analytical model 25.57 %. Field drops are cited as 5-30 %. "No capacity drop is observed for SUMO" | FR (simulation) | [79] Table 4 | FT |
| LC2013 parameters calibrated on detector speeds | Best case (Exp. 3.b): lcStrategic 0.09, lcCooperative 0.34, lcAssertive 2.71, lcSpeedGain 1.04, lcKeepRight 0.24. Over six experiments: lcAssertive 2.47-4.84, lcKeepRight 0.05-0.56. Weakly identified | US (I-24) | [80] Table 6 | FT |
| lcAssertive assumed for legacy vehicles | normal(1.2, 0.05) truncated to [1.1, 1.3]. The earlier value of 1.3 caused CAV emergency braking from cut-ins | EU (TransAID, simulation) | [82] Table 26, p. 32 | FT (assumption) |
| lcAssertive assumed for conventional vehicles | 1.0 / 1.3 / 1.6, one third each; other LC2013 parameters at 1.0 | DE urban (simulation) | [81] Table I | FT (assumption) |
| Human cut-ins in front of an AV vs a human driver | Median gap 7.58 m (n 706) vs 9.57 m (n 3,172). 68.0 % vs 51.8 % below 10 m. Speed-matched: 7.51 vs 9.25 m. Highway and arterial roads mixed | US (Waymo) | [85] Table I | FT (preprint) |

**CAV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| lcAssertive matched to a prototype automated vehicle | About 0.85: 0.7-0.9 for the gap to the target-lane leader, 0.55-0.6 for the gap to the current leader. Baseline normal(0.85, 0.02) on [0.8, 0.9]. TransAID "CVs" (manual drivers with lane-change assist): normal(1.15, 0.05) on [1.1, 1.25] | EU (TransAID) | [82] Sec. 2.2.2.1, Tables 27-28 | FT |
| AV parameters assumed in a simulation | lcAssertive 0.5 / 0.7 / 0.9; lcStrategic 3.0; lcSpeedGain 5.0; lcKeepRight 1.2 | Simulation | [81] Table I | FT (assumption) |
| ALKS regular lane change | The approaching vehicle in the target lane may be made to brake at no more than 3.0 m/s², starting 0.4 s after the manoeuvre starts (if detected for ≥ 1.0 s before) or else 1.4 s. The remaining gap must never fall below 1.0 s of ALKS travel. An equal-speed or slower follower must be ≥ 1.0 s back. If nothing is detected, assume a vehicle at the rear sensing range driving at the limit + 30 km/h (at most 160 km/h) | UNECE | [22] 5.2.6.7.2 | FT |
| ALKS lane change during a minimum-risk manoeuvre | Braking imposed on the follower ≤ 3.7 m/s², starting after 0.0, 0.4 or 1.4 s. Remaining gap 0.5 s toward a slower lane or the hard shoulder, otherwise 1.0 s. An equal-speed or slower follower must be ≥ 0.7 s back | UNECE | [22] 5.2.6.7.3 | FT |
| ALKS lane-change execution | Lateral acceleration ≤ 1 m/s² beyond what the curve needs, in one continuous movement. Regular lane changes allowed only for M1 and N1 vehicles. Deceleration ≤ 2 m/s² during the lane-change procedure, except to avoid a collision. R157 covers only M and N1 vehicles, so heavy trucks are outside it | UNECE | [22] 5.2.6.6.1, 5.2.6.7.5 | FT, corr. |
| Driver-initiated automated lane change (R79, ACSF category C) | S_critical = (v_rear − v)·tB + (v_rear − v)²/(2a) + v·tG, with a = 3 m/s², tB = 0.4 s, tG = 1 s, v_rear ≤ 130 km/h. The manoeuvre starts 3.0-5.0 s after the driver's action and must finish in under 5 s (M1, N1) or under 10 s (heavy vehicles). Rear sensing range ≥ 55 m | UNECE | [83] 5.6.4.6-5.6.4.8 | FT |
| Discretionary lane-change duration, AV vs human | AV: n 180, mean 6.43 s, SD 1.11, range 3.8-10.5. Human: n 178, mean 6.63 s, SD 1.60, range 3.4-12.5. Not significant. Surface roads only. Do not use the reported lognormal "variance": it does not match the SD | US (Waymo) | [84] Table 1 | FT |
| Share of cooperative behaviour | Lane changer: AV 69.0 % vs human 57.9 %. Yielding target-lane vehicle: 33.1 % vs 26.1 %. Speeds below 25 m/s (urban) | US (Waymo) | [86] Sec. 4.1.1 | FT |
| Supervised automated mandatory lane changes, 78 trials | At the lane crossing, lead gaps exceed about 0.54 s and lag gaps about 0.65 s; the lag gap is usually larger | US (NC arterial, 45 mph) | [87] | FT (preprint) |
| Cooperative merge into a CACC platoon | Merging vehicle's headway 0.5-1.5 s, mostly near 1.5 s. Headway inside the platoon 0.84 s. Time to merge: 35 s automated vs 36 s manual. Capacity loss about 7 % (3,973 → 3,703 veh/h/lane, authors' estimate) | US (I-95, VA) | [88] Ch. 4 | FT |
| Speed guidance at a ramp merge (driving simulator) | Median minimum headway, non-guided vs guided: mainline car 0.75 vs 1.76 s (the report's "+57 %" label is inconsistent); ramp car 0.73 vs 0.74; mainline truck 1.11 vs 1.11; ramp truck 1.04 vs 1.03. 7 volunteers | US (simulator) | [89] Table 5 | FT |

### 2.5 Speed choice and compliance

**HDV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| Free-flow speed of cars on motorways, 70 mph limit, 2024 | <50 mph 2 %; 50-54 4 %; 55-59 8 %; 60-64 14 %; 65-69 27 %; 70-74 24 %; 75-79 12 %; 80-84 5 %; 85-89 2 %; 90-94 1 %; ≥95 below 0.5 %. Mean 68 mph. 44 % above the limit, 20 % by ≥ 5 mph, 7 % by ≥ 10 mph | UK (GB) | [90] SPE0102_(2024) | FT |
| Derived from those bins | Mean about 68.3 mph (0.976 × limit); SD about 8.5 mph (about 0.12 × limit). Bin midpoints with Sheppard correction (derived) | UK | [90] | derived |
| Articulated HGVs on motorways (60 mph limit) | <50 mph 6 %; 50-54 39 %; 55-59 53 %; 60-64 2 %; ≥65 below 0.5 %. Mean 55 mph; 2 % above the limit. Derived: mean about 54.6 mph (87.8 km/h), SD about 3.4 mph (5.5 km/h) | UK | [90] | FT |
| Other goods vehicles | Rigid 2-axle: mean 62 mph. Rigid 3+ axles: mean 56 mph, 12 % above 60 mph. Vans ≤ 3.5 t: mean 69 mph, 47 % above 70 mph | UK | [90] | FT |
| 2023 compliance | Articulated HGVs: 2 % above the limit, below 1 % by more than 10 mph. Cars: 45 %, 8 % by more than 10 mph. DfT says the low HGV share "may be influenced by" the 56 mph limiters. Smart motorways excluded | UK | [91] | FT |
| EU speed limiters | Goods vehicles N2, N3: 90 km/h. Buses and coaches M2, M3: 100 km/h | EU | [92] Art. 2-3 | FT |
| Truck speeds at an 80 km/h limit, 6,340 trucks by radar (mean / V85 km/h / share above 80) | Semitrailer with trailer 85.5 / 88.0 / 91.8 %. 3-axle 85.4 / 88.0 / 88.7 %. 5-axle 85.1 / 89.0 / 90.4 %. Drawbar trailer 85.0 / 88.0 / 88.7 %. 2-axle above 7.5 t 87.6 / 90.9 / 91.2 %. 2-axle 3.5-7.5 t 93.6 / 105.8 / 94.8 %. Vans: mean 106.6, V85 123.6, 6.4 % above 130 | AT | [93] Table 1 | FT |
| Truck speeds by lane | 2-axle above 3.5 t: lane 1 mean about 90, V85 about 97; lane 2 about 100 / 106. 3+ axles: about 85 / 88 in both lanes | AT | [93] pp. 3-4 | FT |
| Daytime V85 at a fixed 100 km/h limit | 108 (2016) → 105 km/h (2021). All road authorities pooled, not motorways only. Computed from minute-averaged lane speeds | NL | [94] Fig. 3 | FT, corr. |
| Roads with time-of-day limits (100 km/h by day) | Daytime V85 in 2021: 109 (100/120 roads) and 111 (100/130 roads) vs 105 on fixed-100 roads; the difference is significant | NL | [94] Fig. 3 | FT |
| Section control | V85 almost equal to the limit, e.g. 100 vs 107 km/h without control. 22 of 307 sites | NL | [94] p. 9, Fig. 5 | FT |
| Mean light-vehicle speed by limit, 2024 | 80 km/h: 85.0; 100: 99.7; 120: 112.0; unlimited: 124.1; work zone 100: 95.4; work zone 80: 76.1. All traffic states, not filtered for free flow. Change 2014-2024: −3.6 km/h at the 100 and 120 limits | DE | [95] Table 7, Sec. 3.7 | FT |
| Compliance of car drivers with static limits | 1984/85, no enforcement: 63 % complied at 120 km/h, 26 % at 100. Enforcement raised compliance at 100 to above 70 %. 1992-94 (Lower Saxony): 82 % at 120, 56 % and 65 % at 100. Hessen ozone limit of 90: 50 % | DE | [96] Sec. 1.2 | FT |
| Response of mean speed to a change in the limit | +3.5 km/h mean car speed per +10 km/h limit (motorways, 2+1 roads); −2 km/h per −10 km/h. Earlier studies average about 2.5 km/h per 10 km/h | SE | [97] Abstract | ABS: re-read before citing, corr. |
| Motorway limit raised from 110 to 120 km/h | Cars about 115 → 118.5 km/h (read from a chart). No significant change for trucks with trailers | SE | [98] Slide 14 | FT |
| Fixed speed cameras | Mean speed −4.3 %; share above the limit −35 %. Mostly rural 70 km/h roads | SE | [98] Slide 19 | FT |
| Spot speed cameras in series, 361 sites | Mean speed −3.5 km/h overall, −7.9 at the cameras, −3.0 between them. Compliance +16 percentage points. Limits 50-90 km/h, no motorways | SE | [106] Abstract | FT |
| Ireland, 2024 (news report of the RSA survey) | About 1 in 6 drivers above 120 km/h on motorways. 78 % of HGVs above their 80 km/h limit on 100 km/h roads | IE | [99] | FT (secondary) |
| Enforced variable limits (managed motorway) | 70-50 mph signals: "consistently high", no number. 40 mph: about 85 % compliant at the enforcement threshold | UK (M42) | [100] Sec. 5.4 | FT |
| Advisory variable limits (not enforced) | Speed minus displayed limit: mean = median +18 km/h, SD 11. 88 % above, 10 % below. Weekdays 80 % faster, weekends 87 %. About +16 km/h at displays of 64-80 km/h; median slightly below the display at 48 and 56 km/h | US (Portland) | [101] Sec. 4.2-4.3 | FT |
| Static 89 km/h urban freeway | 76 % faster than the limit, 22 % slower; 90 % within ±20 % | US | [101] Table 1 | FT |
| Enforced VSL on the A99 | The faster drivers go above the limit, the higher the displayed limit. Compliance is higher than at the US advisory site. Values only in a figure | DE | [101] Sec. 5 | FT |
| ISA speed control (human drivers) | Stabilised speed between the limit minus 5 km/h and the limit (speedometer speed). Deceleration ≤ 3.0 m/s²; intervention within 1.5 s; correct limit on ≥ 90 % of the test distance. The driver can override it and can switch it off; it resets at each start. It is one of four allowed ISA options | EU | [102] Annex I, Art. 4 | FT (third-party compilation) |
| SUMO speed defaults | Passenger `speedFactor` normc(1, 0.1, 0.2, 2); `speedDev` 0.05 for trucks; `maxSpeed` 200 km/h passenger, 130 km/h truck and trailer | n/a | [11][12] | FT |
| Compliance assumed in VSL simulations | 5 % (I-24 controller training); full compliance (SUMO study) | US; SE | [104] Sec. III-B; [105] | FT |

**CAV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| ALKS speed | At most 130 km/h; above 60 km/h only if a minimum-risk lane change is possible. It must follow traffic rules, and the approval tests check that it keeps to the limits | UNECE | [22] 2.1, 5.1.2, 5.2.3.1, Annex 6 | FT |
| Level-2 ACC + LKS in naturalistic driving | With a lead vehicle, drivers sped in 19.3 % of 10-s intervals (all system states). Speeding was less likely with ACC + LKS than in manual driving, and more likely when the driver overrode the ACC | NL | [5] Sec. 3.1 | FT |
| ACC set speed | Operating range 0-150 km/h (Tesla), 0-180 km/h (BMW). Target speed set by hand or taken from the detected limit | NL (study cars) | [5] Sec. 2.1.1 | FT |
| Speeding with ACC | 95 % with ACC vs 77 % manual; 96 % with ACC + lane centering. The abstract does not define the metric | US (Boston) | [103] | ABS: re-read before citing |

### 2.6 Perception and information errors

**HDV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| Human Driver Model errors (model values) | Relative gap error 5 %; inverse-TTC error 0.01 /s; error correlation time 20 s; reaction time 0-2 s; 1-7 vehicles anticipated | n/a (DE authors) | [52] Table 1 | FT (assumption) |
| SUMO driver-state defaults | initialAwareness 1.0 (no errors); errorTimeScaleCoefficient 100; errorNoiseIntensityCoefficient 0.2; speedDifferenceErrorCoefficient 0.15; headwayErrorCoefficient 0.75; freeSpeedErrorCoefficient 0; both change-perception thresholds 0.1; minAwareness 0.1 | n/a | [51] | FT |
| Basis of those defaults | A visual comparison with one 5.5-min car-following episode (Krauss with accel 1.0, decel 3.0, sigma 0, tau 0.72). No fit statistic | DE (simTD) | [82] Sec. 2.3.1.3 | FT (assumption) |
| Awareness after a take-over (TransAID assumptions) | "CVs" (manual drivers with L1-2 cooperative automation): initialAwareness normal(0.7, 0.2) on [0.6, 1.0]; recoveryRate normal(0.2, 0.1) on [0.1, 0.5] /s. CAV group 1: normal(0.3, 0.3) on [0.1, 1.0], recovery normal(0.2, 0.1) on [0.01, 0.5]. CAV group 2: normal(0.6, 0.2) on [0.3, 1.0], recovery normal(0.3, 0.1) on [0.1, 0.5] | EU | [82] Tables 27-29 | FT, corr. |
| EIDM built-in errors | sigmagap 0.10; sigmaleader 0.02; tPersEstimate 10 s; treaction 0.50 s; tPersDrive 3.00 s. For sigmaerror the docs say 0.10, but 1.27.1 uses 0.04 (Section 3) | n/a | [11]; SUMO map | FT |
| Wiedemann defaults | W99 cc4 −0.25 m/s, cc5 0.35 m/s, cc6 6.00 × 10⁻⁴ rad/s; Wiedemann estimation 0.5, security 0.5 | n/a | [11] | FT |
| Threshold for perceiving closing speed | About 0.003 rad/s of angular velocity of the lead vehicle; Stevens exponent about 0.8 | Lab | [107] | ABS: re-read before citing |
| TTC estimation | Threshold about 0.003 rad/s; the SD of the estimates grows linearly with TTC; small TTCs are underestimated | Lab (film) | [108] | ABS: re-read before citing |
| Perceived / actual TTC in real approaches | Mean ratio well below 1 (plotted on a 0.40-0.70 axis). It falls as the driver's speed rises and rises with closing speed. True TTC 3.6 and 5.6 s. No effect of age or gender | US (test track) | [109] pp. 39-44 | FT |
| Distance and headway estimation (review) | Distances of 3-90 m are usually underestimated (exponents 0.91-1.00, general perception). Cited studies: drivers overestimate their own headway, so the headways they produce are shorter than intended [VERIFY originals] | Review | [110] | FT (review) |
| Distraction in normal driving | Any secondary activity in 51.93 % of baseline segments; hand-held phone 6.40 %; talking with a passenger 14.58 %. Distraction was a factor in 68.3 % of 905 crashes; odds ratio 2.0. All road types | US (SHRP2) | [111] | FT |
| Secondary tasks, car drivers | 10.2 % of driving time: FR 8.3 %, DE 1.9 %, PL 19.4 %, UK 8.8 % | EU | [112] Sec. 4.1.1 | FT |
| Secondary tasks, truck drivers | About 20 % of annotated driving time; phone use is about 25 % of that. Delivery trucks | EU | [112] Sec. 4.2.1 | FT |
| Phone use by road type | 13 % of phone interactions happen on motorways, which carry about 20 % of driving time (DfT split). 69 % of 51 drivers used a phone; median task 27 s | UK | [113] | FT |
| Phone use seen at the roadside, 2023 | 0.3 % of drivers (cars 0.20 %, vans 0.62 %, HGVs 0.29 %). Hand-held use only; new method, not comparable with earlier years | UK (England) | [114] | FT |

**CAV**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| 77 GHz long-range radar | Range 0.2-250 m. Range accuracy ±0.40 m (far) and ±0.10 m (near). Speed accuracy ±0.1 km/h; resolution 0.37 / 0.43 km/h. Cycle about 72 ms | n/a (datasheet) | [115] | FT |
| Radar datasheets (review) | Bosch LRR3: 250 m, 0.1 m, 0.12 m/s, 80 ms. Delphi ESR: 174 m, 1.8 m, 0.12 m/s, 50 ms. Continental ARS30x: 250 m, 1.5 %, 0.14 m/s, 66 ms. SMS UMRR: 250 m, 2.5 %, 0.28 m/s, 79 ms. Summary: range accuracy from 10 cm up to 1-5 %, speed accuracy about 0.2 m/s | Review | [116] Table 1 | FT |
| Lidar datasheets (review) | Range accuracy 0.02-0.5 m; speed accuracy 0.5 m/s; cycle 10-50 ms | Review | [116] Table 2 | FT |
| Rotating 16-channel lidar | 100 m range; ±3 cm typical; 5-20 Hz | n/a (datasheet) | [117] | FT |
| Production ACC radar | About 250 m, 40° aperture; mid-range radar 160 m | n/a (manufacturer) | [118] | FT |
| Mono camera for ACC | With a 1-pixel error: about 5 % range error at 44 m, about 10 % at 90 m; the absolute error grows with the square of range. Range-rate error about 1 m/s at 30 m with Δt 0.1 s. Best Δt 0.27 s at 24 m to 0.65 s at 57 m | IL (manufacturer research) | [119] Sec. 3 | FT |
| Cameras (review) | Stereo: 5 cm error at 3 m, about 3 m at 40 m. Mono with deep learning: 6 m up to 60 m, 20 m at 120 m. 15-25 frames/s | Review | [116] Sec. 3.4 | FT |
| ISO 15622:2010 | τmin ≥ 0.8 s. The sensing-range clause is not in the free sample | ISO | [120] cl. 6.2.4.1 | FT (sample) |
| ETSI CAM rules | Interval 100 ms to 1 s. A new CAM when heading changes by > 4°, position by > 4 m or speed by > 0.5 m/s. Generation in < 50 ms | EU | [121] cl. 6.1.3, 6.1.5.1 | FT |
| CAMs in OEM test-drive traces | Intervals are multiples of 100 ms, not periodic, with jitter of about ±10 ms | EU | [142] Sec. II | FT |
| 3GPP Release 14 V2X | V2V and V2I latency ≤ 100 ms; pre-crash 20 ms; V2N ≤ 1,000 ms; ≤ 10 messages/s per device; 50-300 bytes | 3GPP | [122] cl. 5.2 | FT |
| V2I delivery ratio vs distance (ITS-G5 / PC5) | 0 m 98 / 100 %; 200 m 96 / 100; 300 m 85 / 100; 400 m 57 / 92; 500 m 48 / 75; 600 m 39 / 56; 700 m 12 / 16; 850 m 0 / 0 | BE (E313) | [123] Table II | FT |
| V2I latency percentiles (ms, ITS-G5 / PC5) | P50 2.43 / 20.86; P95 3.29 / 33.20; P99 121.23 / 45.03; max 515.57 / 50.57. Security raises mean latency about 8× / 2.2×, still below 100 ms | BE | [123] Table III, Sec. VI-C | FT |
| V2V losses, same direction | Both technologies start losing packets at about 480 m | BE | [123] Sec. VI-B | FT |
| Link-level tests | Mean latency: ITS-G5 about 10 ms, C-V2X about 25 ms. No important errors in line of sight up to 650 m. Under C-V2X interference, the ITS-G5 error floor rose to about 20 % (adjacent channel) and 12 % (same channel); C-V2X stayed near 0 % and 5 % | DE (airfield) | [124] | FT, corr. |
| Cooperative awareness range on highways | Awareness ratio stays ≥ 90 % up to 100 m (SE), 250 m (NL), 400 m (FI), 200 m (IT) for V2V; 650 m for V2I (IT) | EU (DRIVE C2X) | [125] Table III | FT |
| CACC latencies | See Section 2.3, [62] | NL | [62] | FT |

### 2.7 Infrastructure sensing (what the controller sees)

These rows describe the controller's information, not vehicle behaviour. The HDV part covers point detectors, which measure all traffic. The CAV part covers probe and V2X data.

**HDV: point detectors**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| Missing 30-s samples | About 15 % (Los Angeles) | US (CA) | [126] p. 160 | FT |
| Error types, share of loops | Stuck off 5.6 %; hanging on (occupancy > 0, flow 0) 5.5 %; very high occupancy 9.6 %; constant values 11.2 %; any error 16 %. The types overlap | US (CA District 12) | [126] Table 1 | FT |
| Loops failed on a given day | 35 % statewide (late 2005): District 4 40 %, District 7 35 %, District 11 5 %. Only 60 % of the network gave reliable data on a typical day | US (CA) | [127] Sec. 1, Abstract | FT |
| Loops failed for a whole quarter or year | District 4 23-25 %, District 7 16-17 %, District 11 2-4 % | US (CA) | [127] Table 6 | FT, corr. |
| Failure and repair runs | District 4: 80 % of working runs last ≤ 50 days per year. Failure runs of exactly 1 day (2006): District 4 61 %, District 7 48 %, District 11 49 %. Conclusion 6 swaps the districts, so check Fig. 17 | US (CA) | [127] Sec. 9 | FT |
| Reporting interval | 30 s; 90 % of point sensors are loops | US (CA) | [128] Sec. 1 | FT |
| Occupancy and vehicle length | k = Σ L_i / v_i; effective length = vehicle length + detection-zone length | US | [128] Sec. 5 | FT |
| Vehicle length spread | 85 % of vehicles are 15-22 ft (4.6-6.7 m); some reach 80 ft | US (I-80) | [129] Sec. 2.3 | FT |
| Single-loop speed from an assumed 19 ft length | About 70 % of 30-s estimates within 5 % of the true speed, in a truck-restricted lane only; better over 5 min | US (I-80) | [129] Fig. 2-7A | FT, corr. |
| Time-mean vs space-mean speed | Differ by up to a factor of 4, most at low speeds | Motorway (country not stated) | [130] | ABS: re-read before citing |
| Missing values in 1-min data, per section-day | 97.95 % of section-days have < 20 % missing, 92.44 % < 10 %, 59.65 % < 1 %. The days were pre-filtered to < 60 % missing | DE (NRW) | [131] Sec. 2 | FT |
| Interval and fleet | 30 s; about 7,830 detectors (loops and radar) | US (MN) | [132] Ch. 1 | FT |
| Dead detector (zero all day) | About 2.5 % of detector-days | US (MN) | [132] Ch. 4 | FT |
| Volume mismatch between neighbouring stations | < 1 % when all detectors work; usually > 5 % when one is faulty | US (MN) | [132] Ch. 2 | FT |
| Interval-boundary errors | More than 15 % of 30-s intervals (Yu et al. 2009 [VERIFY]) | US | [132] Ch. 1 | FT (secondary) |
| Motorway detection system availability | 98.1-98.7 % per month (Sep-Mar), 93.8-95.0 % (Apr-Aug). The drop follows a change in fault classification. Target 95 %. Probably smart motorways only | UK | [133] Table D.5 | FT, corr. |
| Radar stopped-vehicle detection | 89 % detected, 6 % false, 12.2 s to alert. Regions: 76-93 %, 3-13 %, 8.5-15.3 s | UK (smart motorways) | [133] Table 2.2 | FT |
| Type-approval count tolerance, per lane-minute | All vehicles < 10 % above 10 veh/min, < 20 % below. Trucks < 20 % / < 35 %. Hourly < 3 % / < 5 %. Checked statistically against a reference, not a hard bound | DE (TLS 2012) | [134] IV.1.4.1 | FT, corr. |
| Detection-rate classes A1 / A2 / A3 | All vehicles ≥ 99 / 97 / 95 %; cars 97 / 95 / 90; trucks 90 / 85 / 80; articulated 95 / 90 / 85 | DE | [134] Table IV-14 | FT |
| Mean-speed tolerance | < 3 km/h below 100 km/h; < 3 % above | DE | [134] 1.5.3 | FT |
| Allowed aggregation intervals | 15 s, 30 s, 1-60 min; VSL control uses minute data | DE | [134] Annex 6 | FT |
| ALINEA field settings | Cycle 40 s; minimum green 10 s, maximum 40 s; occupancy set point 29 %; gain 70 veh/h; ordered vs actual ramp flow differs by about 2 veh per cycle | FR (Paris) | [135] | FT (OCR scan) |
| ALINEA detector position | 40 m (Paris) and 400 m (Amsterdam) downstream of the ramp nose; ramp volume updated every 10 s to ≥ 1 min | FR, NL | [135] | FT |
| Metering-rate update | Every 20 or 60 s, depending on the system | US | [136] 7.2.1 | FT |
| Dutch motorway sensors | About 500 m apart; 1-min counts and speeds | NL (A13) | [137] | FT |
| Side-fire radar specification | Per-lane volume typically 98-99 %, minimum 90 %; missed and false detections ≤ 15 % per lane; occupancy ±20 %; speed ±3 mph, under stated "nominal" conditions | US (vendor) | [143] | FT |
| Side-fire radar vs loops | Lanes 2-4 almost always within 5 %; lane 1 within 10 % off-peak; peak usually within 10 %; speeds within 5-10 mph off-peak | US (TX) | [144] p. 5 | FT |
| Acoustic and early video detectors | Acoustic, 15-min counts: 0-5 % error off-peak, 10-50 % in congestion. Early video: < 20 % error under ideal conditions | US | [144] | FT |
| Non-intrusive detectors, lane 1, 15-min counts | Within 10 % in free flow; large errors in lanes 1-2 in congestion; occupancy error rises in congestion | US (TX, IH-35) | [145] p. 2 | FT, corr. |
| Loops vs radar, per vehicle | Radar flow and occupancy are noisier than loops. Two loop-card models locked up without showing a fault | US (I-80) | [146] | ABS: re-read before citing |

**CAV: probe and V2X data**

| Quantity | Value | Region | Source, locator | Access |
|---|---|---|---|---|
| GPS-probe latency | Mean 4.26 min (AM peak), 3.94 min (PM peak); 95 % within 6 min. Slowdowns 3.60 min, recoveries 4.79 min | US (SC) | [138] Tables 1, 3 | FT |
| Earlier latency results | Mean 6.8 min, often above 10 min (Kim & Coifman [VERIFY]); ≤ 8 min (Haghani et al. [VERIFY]) | US | [138] | FT (secondary) |
| Probe penetration and fleet bias | Mean 0.08 %, at most 0.5 %. Probe fleet 50.3 % trucks vs 13.3 % in the detector data | AT (A12) | [139] Table 3 | FT |
| Probe GPS interval | Mean 15.1 s, SD 13.0 s | AT | [139] Table 2 | FT |
| Penetration needed (review) | 1 % to 4-5 %; at least 2.4 %. Motorways: ≥ 1 % with a 20 s interval (simulation) [VERIFY originals] | Review | [139] Sec. 2 | FT (secondary) |
| Probe-to-loop ratio | 1.1 % over 17:00-24:00 (not a true penetration rate); hourly 0.7-1.4 %. Distance from probe point to the nearest road: mean 6.8 m, SD 13.2 m | IT (Turin, urban) | [140] | FT, corr. |
| Penetration enough for freeway speeds | 2-3 % (100 phones, 10 miles, 8 h) | US (I-880) | [141] | ABS: re-read before citing |

## 3. SUMO mapping and model choice

These findings come from the SUMO 1.27.1 parameter map ([147], [148]). The live online docs are newer than 1.27.1. Where they disagree, the 1.27.1 source wins.

### 3.1 Parameter map

| Quantity | Attribute | Models | Default in 1.27.1 | How to vary per vehicle | Watch out |
|---|---|---|---|---|---|
| Desired time gap | `tau` | All | 1.0 s | `vTypeDistribution`, or `vehicle.setTau` (creates a singular type) | Not accepted as a distribution in XML. The meaning differs by model: in Krauss it is a safety term on the net gap, in IDM and EIDM it is T, in ACC and CACC it is the control time gap. Values below the reaction time give unsafe driving |
| CACC fallback gap | `tauCACCToACC` | CACC | 1.0 s (source only; missing from the docs) | Per vType | `vehicle.setTau` overwrites both `tau` and `tauCACCToACC` |
| Standstill gap | `minGap` | All | 2.5 m | `vTypeDistribution`, `setMinGap` | ACC adds a hard-coded d0 = clamp(75/v − 5, 0, 2) m |
| Acceleration | `accel` | All | 2.6 passenger, 1.3 truck, 1.1 trailer (libsumo; docs say 1.0 for trailer) | `vTypeDistribution`, `setAccel` | Distribution syntax is rejected. Speed-dependent profiles exist but were not tested |
| Normal deceleration | `decel` | All | 4.5 passenger, 4.0 truck and trailer | `vTypeDistribution`, `setDecel` | A hard cap in Krauss, a comfort target b in IDM |
| Emergency deceleration | `emergencyDecel` | All except Daniel1 | 9.0 passenger, 7.0 truck and trailer | `setEmergencyDecel` | Used only when the safe speed needs more than `decel` |
| Apparent deceleration | `apparentDecel` | Leader property | = `decel` | `setApparentDecel` | Describes the leader. Set it on trucks to make their followers more cautious |
| Action step | `actionStepLength` | All; EIDM warns it is incompatible | = step length | `vTypeDistribution`, `setActionStepLength` | Any value above the step switches the whole simulation to ballistic integration. Not a true delay. Rounded to a multiple of the step |
| EIDM reaction | `treaction` | EIDM | 0.50 s | Per vType | A maximum; do not combine with an action step or driverstate |
| Dawdling | `sigma`, `sigmaStep` | Krauss family only | 0.5; step length | `vTypeDistribution`, `setImperfection` | One-sided: speed −= sigma·accel·U[0,1)·dt. It lowers mean speed and capacity; it is not zero-mean noise. IDM, EIDM, ACC and CACC ignore it |
| EIDM noise | `sigmaerror`, `sigmagap`, `sigmaleader`, `tPersDrive`, `tPersEstimate` | EIDM | 0.04 (the docs' 0.10 is wrong for 1.27.1), 0.10, 0.02, 3 s, 10 s | Per vType | Random draws are platform-dependent, so seeds do not reproduce across machines |
| EIDM coolness | `ccoolness` | EIDM | 0.99 | Per vType | The docs' spelling `coolness` is silently ignored |
| Desired speed | `speedFactor`, `speedDev` | All | Passenger normc(1, 0.1, 0.2, 2) | Sampled per vehicle; vehicle attribute; `setSpeedFactor` | The only vType attribute that accepts a distribution, and only norm or normc; lognormal is rejected. Desired speed = min(maxSpeed, sf·desiredMaxSpeed, sf·lane limit) |
| Speed compliance | none (`speedFactor` × limit; vClass edge limits) | All | n/a | `setSpeedFactor` at each VSL change | A fixed multiplier at every limit level |
| Technical cap | `maxSpeed` | All | 55.56 m/s passenger, 36.11 m/s truck and trailer | `setMaxSpeed` | The 90 km/h truck cap must be set explicitly |
| Start-up delay | `startupDelay` | All except Daniel1 | 0 s | Per vType | Effect on queue discharge not tested |
| Gap acceptance | `lcAssertive` | LC2013, SL2015 | 1 | `setParameter('laneChangeModel.lcAssertive')` | The required gaps are divided by this value. It is the main LC2013 knob for merging |
| Other LC2013 terms | `lcStrategic`, `lcCooperative`, `lcCooperativeSpeed`, `lcSpeedGain`, `lcSpeedGainRight`, `lcKeepRight`, `lcOvertakeRight`, `lcStrategicLookahead`, `lcLookaheadLeft` | LC2013, SL2015 | 1.0, 1.0, = lcCooperative, 1.0, 0.1, 1.0, 0, 3000 m, 2.0 | `setParameter` | libsumo reads them back with 2 decimals. `lcSpeedGainUrgency` (50) and `lcCooperativeHelpTime` (60 s) can be set per vType only |
| Impatience in lane changing | `lcImpatience`, `lcTimeToImpatience` | SL2015 only | 0; infinity | Not under LC2013 | Under LC2013 the XML accepts it but it has no effect. `lcCooperativeHelpThreshold` and `lcCooperativeMinSpeed` do not exist in 1.27.1 |
| Junction impatience | `impatience`, `jmTimegapMinor`, `jmIgnoreFoeProb`, `jmDriveAfterRedTime` | Junction model | 0; 1 s; 0; −1 | `vehicletype.setParameter` | `vehicle.setImpatience` lasts only until the next step. Junction defaults cannot be read through libsumo |
| Perception errors | `device.driverstate.*` | Krauss, IDM; ACC and CACC only with `applyDriverState=1`; EIDM none (all tested) | See Section 2.6 | `<param>` per vehicle; `setParameter('device.driverstate.awareness')` | EIDM ignores the device silently. The error scales linearly with headway |
| Driver-state reaction time | `device.driverstate.maximalReactionTime` | Any model with the device | = original action step | `<param>` | **Bug in 1.27.1**: rounding via remquo corrupts any action step ≥ 0.8 s (at a 0.1 s step) when awareness is below 1, and the mapping is inverted against the docs. Do not use |
| Take-over device | `device.toc.*` | Device | responseTime 5.0 s, recoveryRate 0.10, initialAwareness 0.50, mrmDecel 1.50 | `<param>` | It also creates a driverstate device, so the bug above can apply after a take-over |
| ACC gains | `speedControlGain`, `gapClosingControlGainSpeed`/`Space`, `gapControlGainSpeed`/`Space`, `collisionAvoidanceGainSpeed`/`Space`, `collisionAvoidanceOverride` | ACC | −0.4; 0.8 / 0.04; 0.07 / 0.23; 0.23 / 0.8; 2 m/s | Per vType | The defaults (TransAID) damp the string instability of the original controller. Use a 0.1 s step: the docs report collisions at 1 s |
| CACC gains and communication | `gapControlGainGap` 0.45, `gapControlGainGapDot` 0.0125, `gapClosingControlGainGap` 0.005, `...GapDot` 0.05, `speedControlGainCACC` −0.4, `speedControlMinGap` 1.66 m; vehicle parameter `carFollowModel.caccCommunicationsOverrideMode` (0-3) | CACC | as listed | Per vType; the communication mode per vehicle at runtime | Cooperative mode only behind a CACC leader. Communication is ideal: no delay or loss parameter. Mode thresholds (2 s, 1.5 s) are hard-coded |
| Collision threshold | `collisionMinGapFactor` | All | 1.0 Krauss; 0.1 IDM, EIDM, ACC, CACC | Per vType | Collision counts are not comparable across models unless this is equalised |
| Sampling mechanism | `<vTypeDistribution>`; `createVehTypeDistribution.py` (normal, normalCapped, lognormal, uniform, gamma) | All | n/a | Pre-sampled vTypes; a flow draws one per vehicle (tested) | Getters called on a distribution ID return a random member |

**Hygiene.**

- **XML validation.** With `SUMO_HOME` unset (project rule), XML validation is off, so misspelled attributes are ignored silently. Run one validation pass with `SUMO_HOME` pointing at the venv's sumo package and `--xml-validation always`; it catches errors such as `coolness`.
- **Docs version.** Check every default against the 1.27.1 source, not the live docs.

### 3.2 HDV model choice

| Property | Krauss | IDM | EIDM |
|---|---|---|---|
| Meaning of `tau` | Safety term in the safe-speed rule, on the net gap; field time gaps map onto it loosely | Desired time gap T; field time gaps map onto it directly | Desired time gap T |
| Built-in noise | One-sided dawdling (`sigma`); lowers capacity | None (deterministic) | Human-Driver-Model noise |
| Driver-state errors | Yes | Yes | No (silently ignored) |
| Action step | Yes (switches the whole simulation to ballistic) | Yes | Incompatible; use `treaction` |
| Collision factor | 1.0 | 0.1 | 0.1 |
| Per-vehicle SUMO calibration found | `sigma` and `actionStepLength` on a US arterial [50] | None; HDM error values are assumptions [52] | None for freeways |
| Main risks | `tau` is not a measured gap; `sigma` shifts mean speed | Default parameters give very conservative lane-change gap acceptance | Docs errors; random draws not portable across machines (a T3 determinism risk); may briefly exceed the limit |

**My suggestion (for the author to decide).**

- **Keep Krauss for HDV in v0.** It is the current plant model, and the only per-vehicle SUMO calibration evidence found is for Krauss [50].
- **Consider IDM + driverstate only if field time-gap distributions must map onto `tau` directly.** Switching models means full recalibration.
- **Avoid EIDM in v0**, because of the risks in the table.

### 3.3 CAV model choice

- **ACC for production-like ACC cars.** Choose between two gain sets:
  - SUMO's default gains, which damp the string instability;
  - the original controller gains (`gapClosing` and `collisionAvoidance` gains at 0.07 / 0.23, override about 100, per the SUMO docs). These match the field finding that commercial ACC is string-unstable at short gaps [15][59][60].

  This is a design decision. The provenance of the default gains is not verified: Milanés & Shladover (2014) was not read [VERIFY].
- **CACC for cooperative vehicles,** with time gaps from [18][19][20]. SUMO's CACC has ideal communication, so latency and loss [62][123] have to be emulated in the libsumo layer. That emulation needs its own design.
- **ALKS-like automated vehicles.** Use ACC with the R157 time gaps up to 60 km/h [22]. No sourced value exists above 60 km/h.
- **For all CAV classes:**
  - use a 0.1 s step;
  - equalise `collisionMinGapFactor` with the HDV model before counting conflicts;
  - set `applyDriverState=1` only if sensor noise is wanted. Sensor errors do not scale with headway the way SUMO's error does (Section 2.6).

## 4. Proposed per-vehicle distributions

Status labels used below:

- **Sourced distribution**: the source gives a shape and parameters.
- **Sourced range**: there is a range but no distribution.
- **Assumption**: taken from earlier modelling practice, not from field data.
- **Rule**: taken from a regulation.
- **None**: no sourced distribution.

**Implementation.** Pre-sample N vTypes with `createVehTypeDistribution.py` and put them in a `vTypeDistribution`. Sample `speedFactor` inside each vType. The sampling seed is part of the plant definition, so ask the author which approved seed range covers it. No source gives correlations between parameters, so sample independently. That independence is an assumption.

**Calibration.** Each row below is also a calibration knob. Fix the shapes to their sources and calibrate only one or two means, for example the means of `tau` and `accel`, against a field capacity drop. Then recalibrate the plant and re-run the V139 and T1a/T1b checks.

**HDV-car**

| Parameter | Proposal | Basis | Status |
|---|---|---|---|
| `tau` | Use the empirical close-following net-gap CDF: mean 1.15 s, SD 0.43 s, range 0.2-2.0 s, left-skewed. The Fig. 5 CDF must be digitised, or recomputed from highD. A truncated normal would be a simplification that the source rejects. Lower bound ≥ `actionStepLength`. The mean is the calibration knob | [1] Sec. 3.1, 3.3 | Sourced distribution (UK, truncated at 2 s). In Krauss this sets the shape only, not the realised gaps |
| `minGap` | Keep 2.5 m or calibrate it. No EU data | [9][10] (US) | None |
| `accel` | 1.8-2.2 m/s² for below-average to above-average drivers; shares not sourced. The SUMO default of 2.6 lies above this range, but Long's α is the intercept of a speed-decreasing model, so the two are not directly comparable | [26] | Sourced range (US) |
| `decel` | 3-4 m/s² called comfortable; design value 3.4 | [29][30] | Sourced range (EU, US). In Krauss, `decel` probably also affects capacity through the safe-speed rule; this is a hypothesis to test |
| `emergencyDecel` | 7.0-8.4 m/s² (dry/wet, non-professional/professional means); per-car cells 6.5-9.0; type-approval floor 6.43 | [30][33] | Sourced range (DK) |
| `actionStepLength` | Right-skewed: mean 0.40 s, SD 0.28, P10 0.10, P50 0.30, upper value 0.90, on [0.1, 1.0] in 0.1 s steps | [50] | Sourced distribution, but from a US urban arterial, so it transfers weakly to freeways. Avoid ≥ 0.8 s if driverstate awareness can drop below 1 |
| `sigma` | Right-skewed: mean 0.34, SD 0.20, P10 0.12, P50 0.30, upper value 0.75, on [0.1, 1.0] | [50] | Sourced distribution (US arterial). A strong capacity knob |
| `speedFactor` | Use the motorway free-flow bins relative to the 70 mph limit. A normc approximation has mean 0.98 and SD 0.12 (derived). Truncation is not sourced: about 2 % of cars are below 0.71 × limit and less than 0.5 % above 1.36 × limit (derived). At a 100 km/h limit the mean may be about 1.0 (DE mean 99.7 km/h, all traffic states) or a little above (NL V85 105-108 km/h); this is an inference | [90][94][95] | Sourced distribution (UK, 112.7 km/h limit) |
| VSL compliance rule | SUMO's fixed multiplier is wrong across limit levels. Evidence: advisory VSL +18 km/h with SD 11 (US); enforced 40 mph about 85 % compliant (UK); +3.5 km/h per +10 km/h of limit (SE, ABS). A level-dependent rule via `setSpeedFactor` at each VSL change would be needed | [97][100][101] | None for enforced EU VSL |
| `lcAssertive` | normal(1.2, 0.05) on [1.1, 1.3]. Field critical gaps (0.68-0.9 s DE; 1.17 / 1.26 s US) can only be matched through a simulation check | [82] Table 26; [69][70] | Assumption |
| `lcSpeedGain`, `lcKeepRight`, `lcCooperative`, `lcStrategic` | Keep the defaults and calibrate their means to the lane-change rate (0.5-1 per veh-km UK; about 0.24 highD, derived) and to lane flows (right lane saturates near 800 veh/h, DE) | [25][73][80] | None |
| Lane-change duration | Cars: mean 5.70 s [6] or 7.57-7.79 s, SD 1.6 [74]; the two studies define start and end differently. In LC2013 without the sublane model, use the global `--lanechange.duration` or per-vType `maxSpeedLat`. A 3.5 m lane in 5.7-7.6 s means about 0.46-0.61 m/s lateral speed (derived) | [6][74] | Sourced moments (DE). The duration option is global, so it cannot vary per vehicle |
| `impatience`, `jmTimegapMinor` | Keep the defaults | none | None |
| `device.driverstate.*` | Defaults rest on one visual comparison. If used, the share of vehicles with awareness below 1 is an assumption | [51][82] | None |

**HDV-truck**

| Parameter | Proposal | Basis | Status |
|---|---|---|---|
| `tau` | Evidence conflicts: about equal to cars in UK close following [1]; larger in NL and DE [2][6]; the DE 50 m rule means about 2.0-2.25 s at 80-90 km/h (derived) [8]. One option: same shape as cars, with a mean shift chosen in calibration | [1][2][6][8] | None |
| `accel` | US drivers α 0.15-0.37 m/s²; vehicle maxima 0.45-0.89. EU power-to-weight about 6.3-9.5 kW/t at 40 t (derived), against a legal minimum of 5.0 | [26][27][28] | Sourced range (US) |
| `decel`, `emergencyDecel` | Type-approval floor 5.0 m/s² (1996 text); wet-curve stability limit 0.16-0.27 g | [34][35] | None |
| `maxSpeed` | 25.0 m/s (90 km/h, EU limiter). It must be set: the trailer default is 130 km/h | [92] | Rule |
| `speedFactor` | A narrow distribution just below the cap. UK articulated HGVs: mean 87.8 km/h, SD 5.5 km/h (derived). AT semitrailers at an 80 km/h limit: mean 85.5, V85 88 km/h, so a mean factor of about 1.07 against an 80 km/h truck limit (derived) | [90][93] | Sourced distribution (UK bins); AT moments only |
| Lane use | Left-lane ban on 3+ lane roads (DE) as a lane permission; trucks change mostly between lanes 1 and 2 | [74][76] | Rule; field pattern |
| Lane-change duration | Mean 6.2 s [6] or 8.3-8.5 s, SD 1.8-1.9 [74] | [6][74] | Sourced moments (DE) |

**CAV**

| Class | Parameter | Proposal | Basis | Status |
|---|---|---|---|---|
| ACC | `tau` | Discrete: 1.1 s 50.4 %, 1.6 s 18.5 %, 2.2 s 31.1 %. These are US prototype setting levels. EU production cars cluster at 0.9-1.5 s at their shortest setting, and ISO requires ≥ 0.8 s. Setting shares for EU drivers were not found | [18][13][21] | Sourced distribution (US) |
| ACC | `minGap` | Keep the default. ACC adds d0, and the fitted η or Δ values are not measured standstill gaps | [15][16] | None |
| ACC | `accel`, `decel` | Fixed bounds: 2.0 m/s² up and 2.0-3.5 m/s² down. The field acceleration limit falls with speed (a0 + (vc − v)·β); speed profiles in SUMO are untested | [37][40][41] | Rule and field bounds, no distribution |
| ACC | Gains | Choose SUMO defaults (stable) or the original gains (string-unstable, closer to field data) | [15][59][60]; SUMO map | Design choice |
| ACC | `speedFactor` | Set speed relative to the limit is not sourced. Evidence on direction conflicts: less speeding in NL, more in the US | [5][103] | None |
| CACC | `tau` | Cars, discrete: 0.6 s 57 %, 0.7 s 24 %, 0.9 s 7 %, 1.1 s 12 %. Trucks: 0.6 / 0.9 / 1.2 / 1.5 / 1.8 s at 26.0 / 10.3 / 43.3 / 8.0 / 12.5 %. ENSEMBLE Level A floor: > 0.8 s | [18][19][20] | Sourced distribution (US); EU rule floor |
| CACC | Latency and loss | Not a SUMO attribute; emulate in libsumo. Use the percentiles: ITS-G5 P50 2.43, P95 3.29, P99 121 ms; PC5 P50 20.9, P95 33.2, P99 45.0 ms. Fall back to ACC after 3 lost packets or more than 100 ms | [123] Table III; [62] | Sourced distribution (BE, NL) |
| ALKS-like AV | `tau` | R157 table up to 60 km/h: 1.0-1.6 s for cars, 1.2-2.4 s for heavy vehicles. No value above 60 km/h | [22] | Rule |
| ALKS-like AV | `lcAssertive` | normal(0.85, 0.02) on [0.8, 0.9], matched to a prototype | [82] | Assumption (manufacturer prototype) |
| ALKS-like AV | `speedFactor` | 1.0 with no spread. This is an interpretation of R157, which does not prescribe a speed factor. An ISA-like band would be the limit minus 5 km/h to the limit | [22][102] | Rule-derived |
| ALKS-like AV | Comfort `decel` | 1.0-1.5 m/s² | [36] | Sourced range (DE test track) |

## 5. Gaps

Most important for the plant come first.

1. **Truck car following in Europe.** There are no steady car-following time gaps for trucks: car-truck, truck-car and truck-truck pairs. They could be computed from highD; the likely paper (Sustainability 18(8):4003) returned 403. Ossen & Hoogendoorn 2011 truck parameters were not read.
2. **Standstill gap.** No European field data for `minGap`. Commercial ACC stopping gaps were not found either.
3. **Acceleration and braking.**
   - No per-driver distribution of maximum acceleration for European cars: Bosetti et al. 2014 was blocked; UDRIVE and euroFOT were not searched.
   - No distribution of truck acceleration, comfortable braking or emergency braking.
   - No European queue-discharge acceleration.
4. **Freeway imperfection and action step.** No freeway calibration of Krauss `sigma` or `actionStepLength`; the only one is from a US arterial [50].
5. **Lane changing.**
   - No truck gap acceptance in Europe.
   - No LC2013 calibration on European trajectories.
   - No keep-right compliance rate and no European zipper compliance data.
   - No European split between mandatory and discretionary lane changes.
   - Daamen et al. 2010 and Marczak et al. 2013 merge data were not accessible.
6. **Speed limits.**
   - No compliance with enforced European VSL by displayed level (Dutch matrix signs, Prague, Barcelona, Stockholm MCS).
   - No data on lane-specific limits.
   - German and Dutch truck speed distributions were not read.
7. **ACC behaviour.** No ACC set speed relative to the limit, no shares of ACC time-gap settings chosen by European drivers, and no settings for production truck ACC.
8. **CACC and standards.**
   - No CACC acceleration limits.
   - The full text of Milanés & Shladover (2014), the basis of SUMO's ACC and CACC defaults, was not read [VERIFY].
   - ISO 15622:2018 and ISO 22179 primary texts were not read: acceleration and jerk endpoints, cmin, d_max.
9. **Perception.**
   - No field-calibrated distribution of driverstate parameters.
   - No truck-cab perception data.
   - No freeway-specific share of distraction.
   - No field measurement of production radar noise against ground truth.
10. **Controller information.**
    - No European loop-failure rates (Dutch MoniCa).
    - No end-to-end latency from detector to control centre.
    - The accuracy of UK MIDAS (TRL 541) was not read.
    - No V2X performance under high channel load.
11. **SUMO version.** Some SUMO docs pages read are the current online versions. Defaults not already checked in the 1.27.1 source still need checking.
12. **Inconsistencies inside sources.** Note them; do not resolve them silently.
    - Hoogendoorn & Ossen: the text contradicts Table 4 [47].
    - openACC: Table IV contradicts Sec. 4.4 [13].
    - Riggins et al.: 3 days in the text, 4 in the table [101].
    - Rajagopal & Varaiya: Conclusion 6 swaps the districts [127].
    - METRANS: the "+57 %" label does not match its numbers [89].
    - Waymo lane-change paper: the lognormal "variance" does not match the SD [84].
    - Sivak et al.: 1982 (n 1,644) [45] and 1981 (n 87) [46] are not reconciled.
    - Guo et al. cite Knoop at 0.4-0.5 lane changes per veh-km, while [73] reports 0.5-1.
13. **Search budget.** The web-search budget ran out in several groups. A follow-up run is needed for items 1-7 and 10.

## 6. Rejected or unverified claims

**Claims not used: the verifier could not access the source.**

| Claim | Group | Verdict | Reason |
|---|---|---|---|
| ISA trials cut mean speed by 3-4 km/h on links between intersections (Biding & Lind 2002, SWOV catalogue) | speed | inaccessible | Bot check on the page; snippet only; no other copy found |
| 6 % of Irish drivers used a hand-held device in 2024; on motorways 9 % → 2 % (RSA survey) | perception | inaccessible | RSA page returned 403; snippet only |

**Parts of "partly" claims that are not used.** For each, the corrected value is in Section 2.

| Claim part | Group | Reason |
|---|---|---|
| Al-Obaedi 1.1 s as a pooled "all lanes, all vehicle types" figure | headway | Not stated; the value is tied to about 70 km/h and above |
| Al-Obaedi fits a Normal distribution in Fig. 5 | headway | Wrong: normality was tested and rejected |
| Loulizi Pearson 5 as the "best fit", and "recommend empirical" | headway | The fit is rejected at full sample size; "recommend" overstates the authors |
| Brackstone et al.: drivers followed trucks more closely; flow had little effect | headway | Unverified; the original was blocked |
| Shladover 2011 manual headway "drawn uniformly" | headway | Not in the source; also a gross headway, not a net gap |
| EUSight event selection "speed drop ≥ 20 km/h" | accel | The report says ≥ 40 km/h |
| Greibe non-professional cell range 6.6-8.7 | accel | It is 6.5-8.7 |
| Jiang et al.: the 15 km/h case grows concavely | reaction | Wrong: it grows almost linearly |
| Gunter et al.: 0.153 s at Vehicle B's minimum setting | reaction | Table II lists it under the maximum setting |
| Cimoli et al.: PC5 mean of 38 ms for all messages | reaction, perception | Holds for CAMs only (iCLCM 30.8 ms) |
| Cimoli et al.: string-stable at 0.3 s over LTE Uu | reaction | Abstract only; Table 2 shows the deceleration amplified |
| Cimoli et al.: Uu 95th percentile shifts by 20-30 ms | perception | It doubles; only the mean and SD shift by 20-30 ms |
| Bham: uncongested/congested split attached to the median | lanechange | Those are means; the median is 1.13 s in both. Shorter gaps near the lane drop are qualitative |
| Li, Li & Ni: generalized gamma best on both AIC and BIC for trucks | lanechange | Lognormal has a slightly lower AIC |
| StVO § 7(4): the duty lies on the merging vehicles | lanechange | The duty lies on the continuing lane |
| R157: the 2 m/s² deceleration limit applies after the lane-change procedure | lanechange | It applies during the procedure |
| RWS V85 at 100 km/h as a motorway-only value | speed | All road authorities are pooled |
| Vadeby & Forsman: 2.5 km/h per 10 km/h as this study's own result | speed | It comes from earlier studies |
| TransAID awareness values labelled "CAV-AV" | perception | They are for "CVs"; CAV values differ |
| de Ponte Müller 2021: co-channel ITS-G5 traffic raised the error floor | perception | Direction reversed: C-V2X interference raised the ITS-G5 floor |
| Rajagopal & Varaiya: "never worked over 27 months" | infra | The source counts per quarter or per year |
| Coifman 2001: 70 % within 5 % as general single-loop accuracy | infra | One favourable lane only |
| ORR: MIDAS availability for the whole network, and a real fall from April | infra | Probably smart motorways only; the drop reflects a fault-classification change |
| TLS 2012: hard per-minute error bound | infra | A statistical test tolerance |
| Ajmar et al.: 1.1 % over 17 h as a penetration rate | infra | 7 h; a ratio, not a penetration rate |
| Middleton & Parker: within 10 % in all lanes | infra | Lane 1, 15-min counts; the occupancy finding excludes radar |
| Chen et al.: "hanging on 9.6 %" | infra | 9.6 % is Type 3; Type 2 (hanging on) is 5.5 % |

**Seen only in search snippets or secondary summaries, never claimed.**

- Germany's "recommended 1.8 s / fines below 0.9 s" rule.
- Silver & Farber's "7 % at 440 ft".
- The "60 % of actual" TTC underestimation.
- Relative-speed thresholds of 3-8 × 10⁻⁴ rad/s.
- Bokare & Maurya truck and car accelerations.
- FMVSS 121 at 0.41 g.
- SHRP2 near-crash median of 0.74 g.
- ISO 15622:2018 acceleration (4 → 2 m/s²) and jerk (5 → 2.5 m/s³) endpoints.
- ISO 22179 figure values.
- "1.7-2.5 s" attributed to Makridis et al. 2020 T-ITS; the abstract says 0.8-1.2 s.
- Milanés & Shladover ACC 1.1 s and CACC 0.6 s.
- 16 drivers in Nowakowski et al.
- "10 % of MoniCa loop data unreliable".
- Dutch FCD coverage of 6-8 % or 5 %.
- 98 % compliance on M42 hard-shoulder running.
- The definition of the ACPO threshold.
- The BASt statement on zipper data.
- Loops "in the 99-percent range".
- Local ramp-metering strategies "every 20-60 s".
- A truck limiter set at about 85 km/h.

## 7. Sources

**Downloaded copies.** Downloaded PDFs and text extracts are under /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/31d6d8e5-e88c-4870-9b77-cc7ccfbaac6c/scratchpad/research/, in one subfolder per group (headway, accel, reaction, lanechange, speed, perception, infra, sumo_map). Treat them as untrusted data.

**"fetch" entries.** "fetch" marks a source read through a web-fetch tool's extraction. Spot-check its quotes before citing.

[1] Al-Obaedi J.T.S. (2019). Close Following Behavior: Estimation of Desired Gap Headway Using Loop Detector Data. IJE Trans. B 32(5), 661-666. FT. UK. https://www.ije.ir/article_88197_1e2f630c19541beb4988499a6ddad3f0.pdf
[2] Nishinari K., Treiber M., Helbing D. (2004). Interpreting the Wide Scattering of Synchronized Traffic Data by Time Gap Statistics. arXiv:cond-mat/0212295v2. FT. NL. https://arxiv.org/pdf/cond-mat/0212295
[3] Knospe W., Santen L., Schadschneider A., Schreckenberg M. (2002). Single-vehicle data of highway traffic. arXiv:cond-mat/0203347v1. FT. DE. https://arxiv.org/pdf/cond-mat/0203347
[4] Loulizi A., Bichiou Y., Rakha H. (2019). Steady-State Car-Following Time Gaps. J. Adv. Transp. 2019:7659496. FT. US. https://vtechworks.lib.vt.edu/bitstreams/81a36270-bc15-4de8-8f00-b0efb241977c/download
[5] Varotto S.F., Mons C., Hogema J.H., Christoph M., van Nes N., Martens M.H. (2022). Do adaptive cruise control and lane keeping systems make the longitudinal vehicle control safer? TR-C 141:103756. FT. NL. https://publications.tno.nl/publication/34639619/RCOG2E/varotto-2022-do.pdf
[6] Li Y., Li L., Ni D. Exploration of lane-changing duration for heavy vehicles and passenger cars: a survival analysis approach. arXiv:2108.05710. FT. DE. https://arxiv.org/pdf/2108.05710
[7] The Highway Code, Rule 126 (GOV.UK). FT, fetch. UK. https://www.gov.uk/guidance/the-highway-code/general-rules-techniques-and-advice-for-all-drivers-and-riders-103-to-158
[8] Straßenverkehrs-Ordnung (StVO 2013), § 4. FT, fetch. DE. https://www.gesetze-im-internet.de/stvo_2013/__4.html
[9] Duret A. Measurement of variability involved in the car-following rules. ECTRI Young Researchers Seminar. FT. US (NGSIM). https://www.ectri.org/wp-content/uploads/2019/01/Duret_A_Session3_Traffic2.pdf
[10] Long G. (2002). Intervehicle Spacings and Queue Characteristics. TRR 1796, 86-96. ABS. US. https://trid.trb.org/View/727952
[11] SUMO documentation: Definition of Vehicles, Vehicle Types, and Routes (live version, not pinned to 1.27.1). FT, fetch. https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html
[12] SUMO documentation: Vehicle Type Parameter Defaults. FT, fetch. https://sumo.dlr.de/docs/Vehicle_Type_Parameter_Defaults.html
[13] Makridis M., Mattas K., Anesiadou A., Ciuffo B. OpenACC: an open database of car-following experiments. arXiv:2004.06342 (TR-C 125, 2021). FT. IT, SE. https://arxiv.org/pdf/2004.06342
[14] Makridis M., Mattas K., Ciuffo B., Re F., Kriston A., Minarini F., Rognelund G. (2020). Empirical study on the properties of adaptive cruise control systems. TRR, doi 10.1177/0361198120911047. ABS. EU. https://publications.jrc.ec.europa.eu/repository/handle/JRC118731
[15] Gunter G. et al. Are commercially implemented adaptive cruise control systems string stable? arXiv:1905.02108 (IEEE T-ITS). FT. US. https://arxiv.org/pdf/1905.02108
[16] Shi X., Li X. (2021). Empirical study on car-following characteristics of commercial automated vehicles with different headway settings. TR-C 128:103134. FT. US. https://par.nsf.gov/servlets/purl/10309778
[17] Shladover S. et al. (2009). Effect of CACC on Traffic Flow: Testing Drivers' Choices of Following Distances. Caltrans CA09-0818. FT. US. https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/f0017245-final-report-task-0818.pdf
[18] Shladover S.E., Lu X.-Y., Nowakowski C., Su D. (2011). Development and Evaluation of Selected Mobility Applications for VII. Caltrans CA11-2138. FT. US. https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/task-2138-tsm-a11y.pdf
[19] Yang S., Shladover S.E., Lu X.-Y., Ramezani H., Kailas A., Altan O.D. (2021). A Bayesian regression analysis of truck drivers' use of CACC. J. Intell. Transp. Syst., doi 10.1080/15472450.2021.1990051. FT. US. https://static1.squarespace.com/static/51e8c713e4b07eca5c618cb7/t/61bbc7684a678c70805c088f/1639696235631/2021-yang-shladover-ramezani-lu-kailas-altan-jits.pdf
[20] Vissers J., Banspach J. et al. (2018). ENSEMBLE D2.2 Platooning use-cases, scenario definition and Platooning Levels. FT. EU. https://publications.tno.nl/publication/34640452/Llx58b/vissers-2018-V1.pdf
[21] ISO 15622:2018 Adaptive cruise control systems, public preview (iTeh). FT (preview). https://cdn.standards.iteh.ai/samples/71515/46b6e07bde1f4c6f91cd143563bdc70f/ISO-15622-2018.pdf
[22] UN Regulation No. 157 (ALKS), 01 series, E/ECE/TRANS/505/Rev.3/Add.156/Amend.4 (2023). FT. UNECE. https://www.marklines.com/statics/unece/pdf_202311/R157am4e.pdf
[23] Hu X., Zheng Z., Chen D., Sun J. (2023). Autonomous Vehicle's Impact on Traffic: Empirical Evidence From Waymo Open Dataset. IEEE T-ITS 24(6). FT. US. https://par.nsf.gov/servlets/purl/10492724
[24] Ford Mondeo Owner's Handbook, ACC section (ManualsLib 991883). FT, fetch. EU. https://www.manualslib.com/manual/991883/Ford-Mondeo.html?page=156
[25] Kruber F., Wurst J., Chakraborty S., Botsch M. (2019). Highway traffic data: macroscopic, microscopic and criticality analysis ... highD. arXiv:1903.04249. FT. DE. https://arxiv.org/pdf/1903.04249
[26] Long G. (2000). Acceleration Characteristics of Starting Vehicles. TRB Paper 00-0980. FT (review). US. https://www.fdot.gov/docs/default-source/rail/publications/studies/safety/accelerationresearch.pdf
[27] Straßenverkehrs-Zulassungs-Ordnung (StVZO) § 35. FT. DE. https://www.gesetze-im-internet.de/stvzo_2012/__35.html
[28] Delgado O., Rodríguez F., Muncrief R. (2017). Fuel Efficiency Technology in European Heavy-Duty Vehicles. ICCT. FT. EU. https://www.mobilitafutura.eu/wp-content/uploads/2022/06/EU-HDV-Tech-Potential_ICCT-white-paper_14072017_vF.pdf
[29] CEDR Call 2013, EUSight D5.2 Driving Experiment Report (2015). FT. EU. https://www.cedr.eu/download/other_public_files/research_programme/call_2013/safety/eusight/Eusight_D5_Driving_experiment.pdf
[30] Greibe P. (2007). Braking distance, friction and behaviour. Trafitec. FT. DK. https://trafitec.dk/wp-content/uploads/2024/02/Braking-distance-friction-and-driver-behaviour.pdf
[31] Wood J., Zhang S. (2017). Evaluating Relationships Between Perception-Reaction Times, Emergency Deceleration Rates, and Crash Outcomes. MPC 17-338. FT. US. https://www.ugpti.org/resources/reports/downloads/mpc17-338.pdf
[32] UN Regulation No. 157 (ALKS), Amend.1 consolidated (2022). FT. UNECE. https://www.marklines.com/statics/unece/pdf_202207/R157am1e_0.pdf
[33] UN Regulation No. 13-H (MLIT bilingual copy). FT. UNECE. https://www.mlit.go.jp/jidosha/un/UN_R013H.pdf
[34] UN ECE Regulation No. 13, Rev.3 (1996). FT. UNECE. https://digitallibrary.un.org/record/237462/files/E_ECE_324_Rev.1_Add.12_Rev.3_E_ECE_TRANS_505_Rev.1_Add.12_Rev.3-EN.pdf
[35] Hart P., Bruzsa L. Brake System Comparison for European and North-American Heavy Vehicles. HVTT forum. FT. Region not stated. https://hvttforum.org/wp-content/uploads/2019/11/Hart-Brake-System-Comparison-for-European-and-North-American-Heavy-Vehicles.pdf
[36] Horn S. et al. (2024). User evaluation of comfortable deceleration profiles for highly automated driving. TR-F 105, 206-221. FT. DE. https://eprints.whiterose.ac.uk/id/eprint/216873/
[37] Goodall N.J., Lan C.-L. (2020). Car-following Characteristics of Adaptive Cruise Control from Empirical Data. J. Transp. Eng. A 146(9), preprint. FT. US. https://engrxiv.org/preprint/download/1317/2753
[38] Hadjigeorgiou A., Timotheou S. (2025). Energy Consumption Optimization for Autonomous Vehicles via Positive Control Input Minimization. arXiv:2506.04685. FT. https://arxiv.org/pdf/2506.04685
[39] Tordeux A., Lebacque J.-P., Lassarre S. Robustness analysis of car-following models for full speed range ACC systems. arXiv:1911.11805v2. FT. https://arxiv.org/pdf/1911.11805
[40] Zhou H., Zhou A., Li T., Chen D., Peeta S., Laval J. (2021). Impact of Acceleration/deceleration limits on the String Stability of ACC. arXiv:2108.03232. FT. US. https://arxiv.org/pdf/2108.03232
[41] commaai opendbc `interfaces.py` (commit b3bd79a); openpilot `longitudinal_planner.py`, `long_mpc.py` (commit 2ab952d). FT. https://github.com/commaai/opendbc/blob/master/opendbc/car/interfaces.py
[42] autowarefoundation autoware_launch, `common.param.yaml` (commit 28d1330). FT. https://github.com/autowarefoundation/autoware_launch/blob/main/autoware_universe_launch/autoware_planning_config/config/scenario_planning/common/common.param.yaml
[43] Green M. (2000). "How Long Does It Take to Stop?" Transportation Human Factors 2(3). ABS. https://doi.org/10.1207/STHF0203_1
[44] Markkula G., Engström J., Lodin J., Bärgman J., Victor T. (2016). A farewell to brake reaction times? AAP (postprint). FT. US, ANNEXT. https://eprints.whiterose.ac.uk/102162/1/A%20farewell%20to%20brake%20reaction%20times%20-%202016-06-23%20-%20for%20self-archiving.pdf
[45] TRB Webinar "Speed and Sight Criteria for Geometric Design" (6 Feb 2025), NCHRP 15-75 slides. FT. US. https://onlinepubs.trb.org/onlinepubs/webinars/250206.pdf
[46] Taoka G.T. (1989). An Analytical Model for Driver Response. TRR 1213. FT. US. https://onlinepubs.trb.org/Onlinepubs/trr/1989/1213/1213-001.pdf
[47] Hoogendoorn S.P., Ossen S. (2006). Empirical Analysis of Two-Leader Car-Following Behavior. EJTIR 6(3), 229-246. FT. NL. https://journals.open.tudelft.nl/ejtir/article/download/3447/3595
[48] Wagner P., Lubashevsky I. (2003). Empirical basis for car-following theory development. arXiv:cond-mat/0311192. FT. JP (inferred). https://arxiv.org/pdf/cond-mat/0311192
[49] SUMO documentation: Car-Following Models. FT. https://sumo.dlr.de/docs/Car-Following-Models/index.html
[50] Schrader M., Karnik A.Y., Hainen A.M., Bittle J.A. (2024). Calibrating Car-Following Models Using SUMO-in-the-Loop and Vehicle Trajectories From Roadside Radar. SUMO Conf. Proc. 5. FT. US. https://doi.org/10.52825/scp.v5i.1127
[51] SUMO documentation: Driver State. FT. https://sumo.dlr.de/docs/Driver_State.html
[52] Treiber M., Kesting A., Helbing D. Delays, Inaccuracies and Anticipation in Microscopic Traffic Models. arXiv:cond-mat/0404736v3 (Physica A). FT. https://arxiv.org/pdf/cond-mat/0404736
[53] Montroll E.W., Potts R.B. Car Following and Acceleration Noise. HRB Special Report 79, ch. 2. FT. US. https://onlinepubs.trb.org/Onlinepubs/sr/sr79/79-003.pdf
[54] Treiber M., Kesting A. (2018). The Intelligent Driver Model with Stochasticity. TR-B 117 (arXiv:1708.06952). FT. https://arxiv.org/pdf/1708.06952
[55] Jiang R. et al. (2014). Traffic Experiment Reveals the Nature of Car-Following. PLoS ONE 9(4):e94351 (arXiv:1402.2254). FT. CN. https://arxiv.org/pdf/1402.2254
[56] Olleja P., Markkula G., Bärgman J. (2025). Validation of human benchmark models for automated driving system approval. AAP 213:107922. FT. https://eprints.whiterose.ac.uk/id/eprint/223729/1/1-s2.0-S0001457525000089-main.pdf
[57] Gunter G., Janssen C., Barbour W., Stern R., Work D.B. (2019). Model-Based String Stability of ACC Systems Using Field Data. IEEE T-IV (arXiv:1902.04983). FT. US. https://arxiv.org/pdf/1902.04983
[58] Makridis M., Mattas K., Ciuffo B. (2020). Response Time and Time Headway of an Adaptive Cruise Control. IEEE T-ITS 21(4). ABS. EU. https://doi.org/10.1109/TITS.2019.2948646
[59] Ciuffo B. et al. (2021). Requiem on the positive effects of commercial adaptive cruise control on motorway traffic. TR-C 130:103305. FT. HU. https://www.repository.cam.ac.uk/bitstreams/f9ddcc6a-e069-4b8b-a435-c229f369e58e/download
[60] Knoop V.L. et al. (2019). Platoon of SAE Level-2 Automated Vehicles on Public Roads. TRR 2673(9). ABS. NL. https://doi.org/10.1177/0361198119845885
[61] Korbmacher R., Khound P., Tordeux A. (2025). Understanding Collective Stability of ACC Systems. arXiv:2504.04530. FT. https://arxiv.org/pdf/2504.04530
[62] Cimoli B. et al. (2022). Practical Challenges in Hybrid Communication Ecosystems Based on ITS-G5 and LTE for CACC and GLOSA. Front. Future Transp., doi 10.3389/ffutr.2022.742731. FT. NL. https://www.frontiersin.org/journals/future-transportation/articles/10.3389/ffutr.2022.742731/pdf
[63] 3GPP TS 22.186, Enhancement of 3GPP support for V2X scenarios, Table 5.2-1 (ETSI TS 122 186 V15.4.0; Rel-19 mirror). FT. https://www.etsi.org/deliver/etsi_ts/122100_122199/122186/15.04.00_60/ts_122186v150400p.pdf ; https://www.itecspec.com/3gpp/22.186/s/5.2
[64] SUMO documentation: ACC model. FT. https://sumo.dlr.de/docs/Car-Following-Models/ACC.html
[65] SUMO documentation: CACC model. FT. https://sumo.dlr.de/docs/Car-Following-Models/CACC.html
[66] Yang S. et al. A First Investigation of Truck Drivers' Preferences and Behaviors Using a Prototype CACC System. TRB 2018 poster. FT. US. https://path.berkeley.edu/wp-content/uploads/2024/11/trb2018_poster_sy.pdf
[67] Salek M.S., Chowdhury M. et al. Asymmetric Linear Bilateral Control Model, Automated Truck Platoon. arXiv:2112.14528v2. FT. US. https://arxiv.org/pdf/2112.14528v2
[68] Klitzke L., Gimm K., Koch C., Köster F. Extraction and Analysis of Highway On-Ramp Merging Scenarios. arXiv:2104.05661v2. FT. DE. https://arxiv.org/pdf/2104.05661
[69] Hofinger F., Fellendorf M. Lane change behavior on motorways based on naturalistic trajectory data. hEART 2023, paper 2329. FT. DE. https://transp-or.epfl.ch/heart/2023/abstracts/hEART_2023_paper_2329.pdf
[70] Bham G.H. (2008). Analyzing Microscopic Behavior: Driver Mandatory Lane Change Behavior on a Multilane Freeway. UTC R157. FT, fetch. US. https://rosap.ntl.bts.gov/view/dot/40452/dot_40452_DS1.pdf
[71] Zhang Y. (2024). An Investigation of Discretionary Lane-changing Decisions (TGSIM). TRB slides. FT. US. https://zhang-yanlin.github.io/uploads/TRB2024_TGSIM_LC_Yanlin.pdf
[72] Guo M., Wu Z., Zhu H. (2018). Empirical study of lane-changing behavior on three Chinese freeways. PLoS ONE 13(1):e0191466. FT, fetch. CN. https://pmc.ncbi.nlm.nih.gov/articles/PMC5783389/
[73] Knoop V.L., Colé J., Wilson R.E., Buisson C., van Arem B. (2010). Quantifying the Number of Lane Changes in Traffic. FT. UK. https://www.victorknoop.eu/research/papers/trbtft.pdf
[74] Li G., Yang Z., Pan Y. In-depth Analysis of Durations of Discretionary Lane Changes on Freeway. arXiv:2108.06640. FT. DE. https://arxiv.org/pdf/2108.06640
[75] Nobukawa K. et al. (2016). Gap Acceptance During Lane Changes by Large-Truck Drivers. IEEE T-ITS 17(3). FT, fetch. US. https://stacks.cdc.gov/view/cdc/38311/cdc_38311_DS1.pdf
[76] Straßenverkehrs-Ordnung (StVO 2013), § 7. FT, fetch. DE. https://www.gesetze-im-internet.de/stvo_2013/__7.html
[77] Smart Work Zone Deployment Initiative (2024). Improving the Effectiveness of Zipper Merge Lane Control in Freeway Work Zones. TPF-5(438). FT. US. https://swzdi.intrans.iastate.edu/wp-content/uploads/2025/01/improving_effectiveness_zipper_merge_w_cvr.pdf
[78] Grumert E.F., Bernhardsson V. (2026). Analysing road user behaviour at roadwork zones using large-scale trajectory data. ETRR 18:10. FT, fetch (summary with partial quotes). SE. https://doi.org/10.1186/s12544-026-00777-6
[79] Boukhellouf M., Buisson C., Chiabaut N. (2023). Merging and diverging operations: benchmark of three European microscopic simulation tools. ETRR 15:12. FT, fetch. FR. https://doi.org/10.1186/s12544-023-00586-1
[80] Wang Y., de Souza F., Karbowski D. (2024). Calibrating microscopic traffic models with macroscopic data. arXiv:2409.19090v1. FT. US. https://arxiv.org/pdf/2409.19090
[81] Pelizza A., Orsini F., Yilmaz-Niewerth S., Rossi R., Friedrich B. (2023). Exploring the impact of automated vehicles lane-changing behavior on urban network efficiency. arXiv:2309.14731. FT. https://arxiv.org/pdf/2309.14731
[82] TransAID consortium, Mintsis E. (ed.) (2019). D3.1 v2.0 Modelling, simulation and assessment of vehicle automations and automated vehicles' driver behaviour in mixed traffic. FT. EU. https://elib.dlr.de/132647/1/TransAID_D3.1_2nd%20Iteration_Modelling%20simulation%20and%20assessment%20of%20vehicle%20automations_v2.0_Final.pdf
[83] UN Regulation No. 79, Rev.3 Amend.2 (2018). FT. UNECE. https://www.marklines.com/statics/unece/pdf_201901/R079r3am2e.pdf
[84] Wen X., Huang C., Jian S., He D. Analysis of discretionary lane-changing behaviors of autonomous vehicles based on real-world data (author manuscript; venue not checked). FT. US. https://personal.hkust-gz.edu.cn/hedengbo/assets/publicationPDFs/Wen_TransportmetricaA_2023a.pdf
[85] Alhuraish A., Wang Y., Zhou H. (2026). Cut-In Gap Acceptance Toward Autonomous vs. Human-Driven Vehicles. arXiv:2605.01485v1 (preprint). FT. US. https://arxiv.org/abs/2605.01485
[86] Chung S., Talebpour A., Hamdar S.H. (2025). Characterizing Lane-Changing Behavior in Mixed Traffic. arXiv:2512.07219v1. FT. US. https://arxiv.org/pdf/2512.07219
[87] Sharma A., Al Hasan M.A., Chen D., List G.F. (2026). Controlled Experiments on Lane Changing by Transitional Autonomous Vehicle. arXiv:2607.27085v2 (preprint). FT. US. https://arxiv.org/pdf/2607.27085
[88] FHWA (2021). Applying Bundled Speed-Harmonization, CACC, and Cooperative-Merge Applications to Managed-Lane Facilities. FHWA-HRT-21-008. FT. US. https://www.fhwa.dot.gov/publications/research/operations/21008/21008.pdf
[89] METRANS PSR-21-20. Connectivity-Based Cooperative Ramp Merging in Multimodal and Mixed Traffic Environment. FT. US. https://www.metrans.org/assets/research/psr-21-20%20final%20report%20-%20revised.pdf
[90] Department for Transport (2025). Table SPE0102: Free flow vehicle speeds, GB, 2018-2024. FT. UK. https://assets.publishing.service.gov.uk/media/685a8814db207fc18744d5ed/spe0102.ods
[91] Department for Transport (2024). Vehicle speed compliance statistics for Great Britain: 2023. FT, fetch. UK. https://www.gov.uk/government/statistics/vehicle-speed-compliance-statistics-for-great-britain-2023/vehicle-speed-compliance-statistics-for-great-britain-2023
[92] Council Directive 92/6/EEC as amended by 2002/85/EC (consolidated 2002). FT. EU. https://legislation.gov.uk/eudr/1992/6/pdfs/eudr_19920006_2002-12-04_en.pdf
[93] Kuratorium für Verkehrssicherheit (2011). Lkw-Geschwindigkeitsverhalten auf Autobahnen. AK Wien, Verkehr und Infrastruktur 44. FT. AT. https://www.arbeiterkammer.at/infopool/akportal/Verkehr_und_Infrastruktur_44.pdf
[94] Rijkswaterstaat (2022). Notitie V85 2021. FT. NL. https://open.rws.nl/publish/pages/116926/notitie_v85_2021_definitief.pdf
[95] BASt (2025). Auswirkung einer generellen zulässigen Höchstgeschwindigkeit von 130 km/h auf Autobahnen auf die CO2-Emissionen. doi 10.60850/fv-v6. FT. DE. https://www.bmv.de/SharedDocs/DE/Publikationen/StV/studie-tempolimit-auswirkungen.pdf?__blob=publicationFile
[96] Umweltbundesamt. Umweltauswirkungen von Geschwindigkeitsbeschränkungen (publication 3136). FT. DE. https://www.umweltbundesamt.de/system/files/medien/publikation/long/3136.pdf
[97] Vadeby A., Forsman Å. (2014). Evaluation of new speed limits in Sweden: a sample survey. Traffic Inj. Prev. 15(8), 778-785. ABS, fetch. SE. https://pubmed.ncbi.nlm.nih.gov/24484445
[98] Vadeby A. (VTI). Results: Safety Benefits of Implemented Measures. Trafikverket Vision Zero Academy presentation (undated). FT. SE. https://bransch.trafikverket.se/contentassets/6af107d0cbe94281af73a57b9761c189/16_safety_benefits_vadeby.pdf
[99] Dublin People (2 July 2025). Speeding remains widespread on Irish roads, RSA survey finds (secondary news). FT, fetch. IE. https://dublinpeople.com/news/dublin/articles/2025/07/02/67654-2/
[100] Unwin P., Marsh P. (2009). "ATM to Managed Motorways". European Transport Conference 2009. FT. UK. https://aetransport.org/public/downloads/BBUJg/3937-514ec5c76aa6e.pdf
[101] Riggins G., Bertini R.L., Ackaah W., Margreiter M. (2016). Evaluation of Driver Compliance to Displayed Variable Advisory Speed Limit Systems. TR Procedia 15, 640-651. FT. US, DE. https://www.scipedia.com/wd/images/c/c4/Draft_Content_980678065-beopen1136-8335-document.pdf
[102] Commission Delegated Regulation (EU) 2021/1958 (ISA), LawPlayer compilation of EUR-Lex. FT, fetch (third party). EU. https://lawplayer.com/eu/act/32021R1958
[103] Monfort S.S. et al. (2022). Speeding behavior while using adaptive cruise control and lane centering in free flow traffic. Traffic Inj. Prev. 23(2), 85-90. ABS, fetch. US. https://pubmed.ncbi.nlm.nih.gov/35044286/
[104] Zhang Y. et al. (2025). Real-World Deployment and Assessment of a Multi-Agent RL-Based VSL Control System. arXiv:2503.01017. FT. US. https://arxiv.org/abs/2503.01017
[105] Grumert E.F., Tapani A., Ma X. (2018). Characteristics of variable speed limit systems. ETRR 10:21 (read via LiU DiVA). FT. SE. https://etrr.springeropen.com/articles/10.1186/s12544-018-0294-8
[106] Vadeby A., Howard C. (2024). Spot speed cameras in a series: effects on speed and traffic safety. AAP 199:107525 (VTI DiVA copy). FT. SE. https://vti.diva-portal.org/smash/get/diva2:1844821/FULLTEXT01.pdf
[107] Hoffmann E.R., Mortimer R.G. (1996). Scaling of relative velocity between vehicles. AAP 28(4), 415-421. ABS. https://trid.trb.org/View/464448
[108] Hoffmann E.R., Mortimer R.G. (1994). Drivers' estimates of time to collision. AAP 26(4), 511-520. ABS. https://trid.trb.org/View/408844
[109] Kiefer R.J. et al. (2005). Surprise Braking Trials, Time-to-Collision Judgments, and "First Look" Maneuvers. DOT HS 809 902. FT, fetch. US. https://rosap.ntl.bts.gov/view/dot/3658/dot_3658_DS1.pdf
[110] Shinar D., Shaham M. (2003). Benefits of a moving point-of-light as a means to maintaining safe headways in tunnels. DSC North America 2003. FT. https://www.nads-sc.uiowa.edu/dscna/2003/papers/Shinar_Benefits%20of%20a%20Moving%20Point%20of%20Light....pdf
[111] Dingus T.A. et al. (2016). Driver crash risk factors and prevalence evaluation using naturalistic driving data. PNAS 113(10), 2636-2641. FT. US. https://pmc.ncbi.nlm.nih.gov/articles/PMC4790996/
[112] Bärgman J., van Nes N. et al. (2017). The UDrive dataset and key analysis results. UDRIVE D41.1. FT. EU. https://erticonetwork.com/wp-content/uploads/2017/12/UDRIVE-D41.1-UDrive-dataset-and-key-analysis-results-with-annotation-codebook.pdf
[113] Hibberd D., Batool Z., Carsten O., Ismaeel R. (2019). A naturalistic study of mobile phone distraction during driving (UDRIVE). DfT TRSS0004. FT. UK. https://assets.publishing.service.gov.uk/media/5f7de688e90e070dea12efce/A-naturalistic-study-of-mobile-phone-distraction-during-driving-analysis-of-UDRIVE-project-database.pdf
[114] Department for Transport. Mobile phone use by drivers, England 2023. FT. UK. https://www.gov.uk/government/statistics/seatbelt-and-mobile-phone-use-surveys-2023/mobile-phone-use-by-drivers-england-2023
[115] Continental. ARS 408-21 Long Range Radar Sensor 77 GHz data sheet. FT. https://platformselect.autonomoustuff.com/wp-content/uploads/2020/08/ARS-408-21-whitelabel.pdf
[116] de Ponte Müller F. (2017). Survey on Ranging Sensors and Cooperative Techniques for Relative Positioning of Vehicles. Sensors 17(2):271. FT. https://pmc.ncbi.nlm.nih.gov/articles/PMC5335929/
[117] Velodyne Lidar. Puck (VLP-16) datasheet 63-9229 Rev-H. FT. https://cdn.shopify.com/s/files/1/1750/5061/files/63-9229_Rev-H_Puck__Datasheet_Web.pdf
[118] Bosch press release "Bosch presents new radar sensor" (Automotive World, 13 Aug 2013). FT, fetch. https://www.automotiveworld.com/news-releases/bosch-presents-new-radar-sensor/
[119] Stein G.P., Mano O., Shashua A. (2003). Vision-based ACC with a Single Camera: Bounds on Range and Range Rate Accuracy. IEEE IV 2003. FT. https://www.cs.huji.ac.il/~shashua/papers/IV2003.pdf
[120] ISO 15622:2010, free sample (iTeh). FT (sample). https://cdn.standards.iteh.ai/samples/50024/6d01413ee38948a894df2cb2df9747d7/ISO-15622-2010.pdf
[121] ETSI EN 302 637-2 V1.4.1 (2019). Cooperative Awareness Basic Service. FT. EU. https://www.etsi.org/deliver/etsi_en/302600_302699/30263702/01.04.01_60/en_30263702v010401p.pdf
[122] 3GPP TS 22.185 V14.3.0 (ETSI TS 122 185). Service requirements for V2X services. FT. https://www.etsi.org/deliver/etsi_ts/122100_122199/122185/14.03.00_60/ts_122185v140300p.pdf
[123] Maglogiannis V. et al. Experimental V2X Evaluation for C-V2X and ITS-G5 Technologies in a Real-Life Highway Environment (author version). FT. BE. https://www.marquez-barja.com/images/papers/AUTHOR-Version-Experimental_V2X_Evaluation_for_C-V2X_and_ITS-G5_Technologies_in_a_Real-Life_Highway_Environment.pdf
[124] de Ponte Müller F., Rashdan I., Schmidhammer M., Sand S. (2021). ITS-G5 and C-V2X Link Level Performance Measurements. 27th ITS World Congress. FT. DE. https://elib.dlr.de/142341/1/ITS-G5_and_C-V2X_Link_Level_Performance_Measurements_dePonteMueller_v4.0.pdf
[125] Boban M., d'Orey P.M. (2016). Exploring the Practical Limits of Cooperative Awareness in Vehicular Communications. arXiv:1503.06590v3. FT. EU. https://arxiv.org/pdf/1503.06590
[126] Chen C., Kwon J., Rice J., Skabardonis A., Varaiya P. (2003). Detecting Errors and Imputing Missing Data for Single-Loop Surveillance Systems. TRR 1855, 160-167. FT. US. https://connected-corridors.berkeley.edu/sites/default/files/detecting_errors_and_imputing_missing_data_for_single-loop_surveillance_systems.pdf
[127] Rajagopal R., Varaiya P. (2007). Health of California's Loop Detector System. PATH UCB-ITS-PRR-2007-13. FT. US. https://escholarship.org/uc/item/71w9q93p
[128] Bickel P.J. et al. (2007). Measuring Traffic. Statistical Science 22(4), 581-597. FT. US. https://arxiv.org/pdf/0804.2982
[129] Coifman B. (2001). Traffic Data Measurement and Validation. PATH UCB-ITS-PRR-2001-40. FT. US. https://escholarship.org/uc/item/72t619n7
[130] Knoop V., Hoogendoorn S.P., van Zuylen H. (2009). Empirical Differences Between Time Mean Speed and Space Mean Speed. Traffic and Granular Flow '07. ABS. https://ideas.repec.org/h/spr/sprchp/978-3-540-77074-9_36.html
[131] Wang S., Schreckenberg M., Guhr T. (2022). Identifying subdominant collective effects in a large motorway network. arXiv:2202.07644. FT. DE. https://arxiv.org/pdf/2202.07644
[132] Kwon T.M. (2020). Improve Traffic Volume Estimates from MnDOT's Regional Traffic Management Center. MnDOT 2020-02. FT, fetch. US. https://rosap.ntl.bts.gov/view/dot/62219/dot_62219_DS1.pdf
[133] Office of Rail and Road (2023). Second annual assessment of safety performance on the strategic road network. FT. UK. https://www.orr.gov.uk/sites/default/files/2023-12/second-annual-assessment-of-safety-performance-on-the-srn_1.pdf
[134] BASt (2012). Technische Lieferbedingungen für Streckenstationen (TLS 2012). FT. DE. https://www.bast.de/DE/Publikationen/Regelwerke/Verkehrstechnik/Unterseiten/V5-tls-2012.pdf?__blob=publicationFile&v=1
[135] Papageorgiou M., Hadj-Salem H., Blosseville J.-M. (1991). ALINEA: A Local Feedback Control Law for On-Ramp Metering. TRR 1320. FT (OCR scan). FR, NL. https://onlinepubs.trb.org/Onlinepubs/trr/1991/1320/1320-008.pdf
[136] FHWA. Freeway Management and Operations Handbook, ch. 7 Ramp Management and Control. FT. US. https://files.topslab.wisc.edu/its/rampmetering/fmoh_chp7_ramp.pdf
[137] Cenedese C. et al. (2021). Highway Traffic Control via Smart e-Mobility, Part II: Dutch A13 Case Study. arXiv:2102.09433. FT. NL. https://arxiv.org/pdf/2102.09433
[138] Wang Z., Hamedi M., Young S. A Methodology for Calculating the Latency of GPS-Probe Data. arXiv:1801.06128. FT. US. https://arxiv.org/pdf/1801.06128
[139] Blumthaler W., Bursa B., Mailer M. (2020). Influence of floating car data quality on congestion identification. EJTIR 20(4), 22-37. FT. AT. https://doi.org/10.18757/ejtir.2020.20.4.5304
[140] Ajmar A., Arco E., Boccardo P., Perez F. (2019). Floating Car Data (FCD) for Mobility Applications. ISPRS Archives XLII-2/W13. FT. IT. https://isprs-archives.copernicus.org/articles/XLII-2-W13/1517/2019/isprs-archives-XLII-2-W13-1517-2019.pdf
[141] Herrera J.C. et al. Evaluation of Traffic Data Obtained via GPS-Enabled Mobile Phones: the Mobile Century Field Experiment. ABS. US. https://its.berkeley.edu/node/3234
[142] Molina-Masegosa R., Sepulcre M., Gozalvez J., Berens F., Martinez V. (2020). Empirical Models for the Realistic Generation of Cooperative Awareness Messages. IEEE TVT (arXiv:2004.06919). FT. EU. https://arxiv.org/pdf/2004.06919
[143] Wavetronix. SmartSensor HD specification sheet. FT. US. http://www.signalcontrol.com/products/wavetronix/Wavetronix_SmartSensor_HD_126.pdf
[144] Middleton D. Results of Non-Intrusive Detector Tests. TTI (2003/2004). FT. US. https://houstonvaluepricing.tti.tamu.edu/reports/documents/detector_paper_middleton2.pdf
[145] Middleton D., Parker R. (2003). Summary Report on Evaluation of Vehicle Detection Systems. TTI 0-2119-S. FT. US. https://library.ctr.utexas.edu/hostedPDFs/tti/0-2119-S.pdf
[146] Coifman B. (2004). An Assessment of Loop Detector and RTMS Performance. PATH/ITS Berkeley. ABS. US. https://econpapers.repec.org/RePEc:cdl:itsrrp:qt3qt5909m
[147] Eclipse SUMO 1.27.1 source and docs (tag v1_27_1): MSCFModel_Krauss, _ACC, _CACC, _EIDM, MSDriverState, MSLCM_LC2013, MSLCM_SL2015, MSAbstractLaneChangeModel, MSVehicle, SUMOXMLDefinitions. https://github.com/eclipse-sumo/sumo/tree/v1_27_1
[148] Local SUMO 1.27.1 tests (probe.py, dyn.py, ds_asl.py, imp.py, out_defaults.json, out_set.json), libsumo 1.27.1: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/31d6d8e5-e88c-4870-9b77-cc7ccfbaac6c/scratchpad/research/sumo_map/test/
[149] SUMO documentation: EIDM. https://sumo.dlr.de/docs/Car-Following-Models/EIDM.html
[150] SUMO documentation: Vehicle Speed. https://sumo.dlr.de/docs/Simulation/VehicleSpeed.html
[151] SUMO documentation: ToC Device. https://sumo.dlr.de/docs/ToC_Device.html
[152] SUMO documentation: createVehTypeDistribution.py. https://sumo.dlr.de/docs/Tools/Misc.html#createvehtypedistributionpy