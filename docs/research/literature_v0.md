# Literature check v0: energy model, cost values, CAV comparators

*2026-10-13. Method: 3 topic researchers (web + local SUMO 1.27.1 tests), 1 adversarial citation and number verifier per topic, 1 cross-topic completeness critic (7 agents). Nothing here binds: decisions go to `docs/decisions.md`. "seen" says what was actually read; anything not read in full is [VERIFY]. Prices, guidance and software facts are as of the stated dates and may change. Local test scripts were in the session scratchpad and are not kept.*


## Energy model

### Recommendation (researcher)
MAIN model (SUMO built-in): HBEFA4 for all three classes, computed online at every 0.2 s step.
- Classes: PC_petrol_Euro-6d (and/or PC_diesel_Euro-6d) for HDV and CAV cars, TT_AT_gt34-40t_Euro-VI_D-E for trucks, PC_BEV for battery-electric cars.
- Why: it ships with 1.27.1 (no licence) and has been the SUMO default since 1.23.0. It is one fitting procedure from one European reference database (HBEFA 4.2). Its fit error for car fuel is 4–7 % and BEV FC_MJ 5 %. It has ICE fuel cut-off and negative BEV energy.
- Settings:
  - set mass (and frontSurfaceArea) in each vType, because the fuel cut-off threshold depends on them;
  - read TraCI getFuelConsumption (mg/s) and getElectricityConsumption (Wh/s) × 0.2 s, or tripinfo fuel_abs (mg) and electricity_abs (Wh, net);
  - convert fuel with LHV (GREET 1.8d.1: gasoline 43.448 MJ/kg, diesel 42.791 MJ/kg).
- Known weaknesses, to state in the protocol:
  - the truck class fits poorly (FC 29 %);
  - the acceleration dependence is a polynomial; in the HBEFA3 derivation it was slope-based and valid to ±0.6 m/s² only, and the same is unverified for HBEFA4;
  - there is a single BEV class, and in my test it under-charges acceleration relative to kinetic energy;
  - the fleet is EU, while the inflow is US.
- Alternative if the author prefers physics for BEVs: SUMO 'Energy' (EVM) as the main BEV model, with a stated published parameter set (e.g. Koch et al. 2021 Table II, BMW i3). In Behrisch et al. 2024 it was −4 % to +3 % on highway at 110 km/h. Avoid MMPEVEM as main: it returns NaN beyond motor limits and was up to +15 % on highway.

INDEPENDENT cross-check (offline from logged per-step speed and acceleration, never used in training):
- physics/power-based models of a different lineage:
  - VT-CPFM for petrol and diesel cars, calibrated from public EPA ratings of a chosen US car; needs a full-text read of Rakha et al. 2011 and Park et al. 2013 first;
  - SUMO Energy (EVM) for BEVs, run offline through emissionsDrivingCycle with an explicit acceleration column (never -a with 0.2 s data), or VT-CPEM;
  - PHEMlight5/PC_EU4_G as a free second ICE car check.
- Trucks: no free independent model found. Report the truck share separately and do a sensitivity row (e.g. truck energy ×0.7 and ×1.3, given the 29 % fit error).
- Pre-register that the sign of the controller's energy effect must agree between main and cross-check, and report both.
- Reason: the same model is in the RL reward (V16), so the policy can exploit model artefacts. Examples: the zero-fuel coasting threshold; BEV recuperation credit that HBEFA4 and EVM do not cap. An independent model is the guard against that.

Making ICE and BEV comparable (choose one for the headline, report the others as sensitivity rows):
- (A) Tank/battery-to-wheel: fuel mass × LHV versus battery-terminal Wh. Physical, simple, matches V10's 'kWh'; BEVs look about 3–4× more efficient.
- (B) Plug-to-wheel for BEVs: divide by a charging efficiency. Both Koch 2021 and Behrisch 2024 use 0.9 for comparison with WLTP data.
- (C) Well-to-wheel / primary energy: apply WTT factors (GREET or JEC) per carrier. Needs a separate sourced lookup, which is open.
- (D) Monetary per carrier: price fuel kWh and electricity kWh at their own retail prices. This is the natural fit for V16's 'energy price × kWh'.

My suggestion: (D) in the generalised-cost headline, (A) as the reported physical energy metric per cohort (V10), and (B)/(C) as sensitivity rows. The fleet mix is identical across arms, so the choice only changes cohort weights, not the sign of a paired difference.

### Verifier verdict on the recommendation
Sound: **False**. Most of the evidence holds up, and the main choice follows from it. Using HBEFA4 as the in-simulation model, with explicit mass and frontSurfaceArea, LHV conversion, a truck sensitivity row, a pre-registered cross-check that must agree in sign, and option D in the headline, is reasonable and well sourced.

One part of the recommendation rests on a false premise. It proposes running SUMO Energy (EVM) offline through emissionsDrivingCycle on 0.2 s logs with an explicit acceleration column.
- The tool is documented for 1 s rows and has no step-length option, so TS = 1 s.
- The Energy model computes lastV = v - a·TS. On 0.2 s data this gives negative energy while accelerating from low speed.
- In my run of the same profile, the offline net was 219.5 Wh against 255.95 Wh in the simulation (-14 %), with the acceleration and regeneration phases off by -5 % and +8 %.
- MMPEVEM also uses TS.
- The tool's absolute totals and Time column are 5x too large on 0.2 s rows.
So the claim that 'offline recomputation is exact' is shown only for HBEFA4, whose polynomial does not depend on TS. The EVM cross-check must be done another way: implement the EVM equations in Python with dt = 0.2, resample to 1 s, or run a second in-simulation shadow computation. Otherwise the sign-agreement check could be dominated by a tool artefact.

Other points to fix before the protocol:
- F7's idle column is rescaled from about 24.6 s to 5 s without saying so.
- The ICE spread is about ±18 %, not ±25 %.
- The AFDC 'typo' claim is speculation.
- The CMEM heavy-duty extension and VT-CPFM 'bang-bang' claims are not supported by the sources cited.
- If 'Koch et al. 2021 Table II' is adopted as the parameter set, its recuperation limits are 77 Nm / 50 kW, not the code defaults of 95.5 Nm / 42.8 kW.
- GREET 1.8d.1 E0 values (2010) should be replaced with current GREET E10 and ULSD values for a US inflow.
- The truck ×0.7 / ×1.3 sensitivity uses a fit error (against HBEFA) as if it were real-world uncertainty, so call it a heuristic.

Scratch evidence is in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5/510dd91c-1bff-427e-90a7-d763e29122b9/scratchpad/lit/verify_energy (o_bev.csv, s_bev.csv, tl_bev.csv, web/*.txt).

### Local checks
Machine state: one tiny run per class, single vehicle, 80 s simulated; load average about 0.2 before the runs. All runs on SUMO 1.27.1 (libsumo) in /home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv, with SUMO_HOME unset and OMP_NUM_THREADS=1, on a copy of the toy net (one lane, 3 km) in scratchpad/lit/emtest.

Installed data:
- data/emissions has PHEMlight (PC_D_EU4, PC_G_EU4), PHEMlight5 (PC_EU4_D_MW, PC_EU4_G) and 11 MMPEVEM vType files;
- HBEFA3 and HBEFA4 are compiled in;
- the default type is HBEFA4/PC_petrol_Euro-4.

Classes run with the accelerate–cruise–brake–idle profile: HBEFA4 petrol, diesel and truck (TT_AT_gt34-40t_Euro-VI_D-E); HBEFA4 PC_BEV; HBEFA3 PC_G_EU4; PHEMlight5 PC_EU4_G; Energy; MMPEVEM VW_ID3. The numbers are in F7.

Results:
- ICE fuel is 0 while braking at −3 m/s² (cut-off).
- BEV braking energy is negative: HBEFA4 −127 Wh, Energy −172 Wh, MMPEVEM −75 Wh.
- MMPEVEM gives NaN in 13 steps, at 2 m/s² above 25.2 m/s.

Units verified:
- TraCI: mg/s and Wh/s;
- emission-output: per second by default;
- tripinfo with device.emissions and write-unfinished: fuel_abs in mg, electricity_abs in Wh net (255.95 Wh equals the battery drop);
- battery-output: Wh per step.

Offline: emissionsDrivingCycle with an explicit acceleration column reproduced the in-simulation fuel per step (max difference 0.003 mg/s; total 91,260 mg in both). Its -a option assumes 1 s rows and gave wrong accelerations on 0.2 s data. The sum-output FC is in g/km.

Read-only for the repo; all files are under scratchpad/lit (emtest, src, dl1-dl8).

### F1: Emission and energy models in the installed SUMO 1.27.1 (local check, docs, and source at tag v1_27_1)
Local check in /home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv (SUMO 1.27.1).

Model families, chosen with vType emissionClass='<family>/<class>':
- HBEFA (2.1), HBEFA3 and HBEFA4: coefficients are compiled into SUMO, so no data files are needed.
- PHEMlight and PHEMlight5: need data files. The pip install ships only demo files: PHEMlight PC_D_EU4 and PC_G_EU4; PHEMlight5 PC_EU4_D_MW and PC_EU4_G. These are Euro-4 cars only, with no trucks and no BEV.
- Energy (Kurczveil electric model): a single class.
- MMPEVEM: a single class. Eleven example BEV vType files ship in data/emissions/MMPEVEM (BMW i3, VW ID.3, ID.4, e-Up, an SUV, Peugeot, Opel, Hyundai, Citroen).
- Zero.

Default class: in 1.27.1, DEFAULT_VEHTYPE reports HBEFA4/PC_petrol_Euro-4. The overview page Models/Emissions.html still says the default is HBEFA3/PC_G_EU4, so that page is stale. The HBEFA4 page says HBEFA4 has been the default since 1.23.0.

How HBEFA4 computes (source HelpersHBEFA4.h, v1_27_1):
- rate = f0 + f1·v + f2·a' + f3·v² + f4·v³ + f5·a'·v + f6·a'·v², with a' = a + g·sin(slope).
- Fuel and pollutants are clamped to ≥ 0. Electricity is not clamped, so BEV recuperation comes out negative.
- Fuel cut-off is emulated: an ICE gives 0 fuel when v > 0 and a < coasting deceleration. The coasting deceleration is a linear function of v, vType mass and frontSurfaceArea (PollutantsInterface.cpp). My own estimate is about −0.5 m/s² at 30 m/s for an assumed 1500 kg, 2.2 m² car. So set mass explicitly in each vType.

HBEFA4 classes relevant here, with the documented fit error versus HBEFA 4.2 (a fit error, not a validation):
- PC_petrol_Euro-6d: FC 3.97 %;
- PC_diesel_Euro-6d: FC 6.93 %;
- PC_BEV: FC_MJ 5.04 % (the only BEV car class);
- TT_AT_gt34-40t_Euro-VI_D-E: FC 28.82 %. The docs say 'be careful … above 40 %'.

Units, all verified locally:
- TraCI getFuelConsumption: mg/s. getElectricityConsumption: Wh/s.
- emission-output: per-second rates (fuel mg/s, electricity Wh/s) unless --emission-output.step-scaled is set.
- tripinfo with --device.emissions.probability 1 (plus --tripinfo-output.write-unfinished for vehicles still on the road): fuel_abs in mg, electricity_abs in Wh, net of regeneration. Test: 255.95 Wh, which equals the battery drop 40000 − 39744.05 Wh.
- battery-output: energyConsumed in Wh per step; totalEnergyRegenerated in Wh.
- Since SUMO 1.14.0, fuel is in mg. --emissions.volumetric-fuel restores litres; the code then uses 742 g/L for gasoline and 836 g/L for diesel.

Other options: --phemlight-path, --phemlight-year, --phemlight-temperature.

Offline tool: bin/emissionsDrivingCycle computes the same models from a time;speed;accel timeline. With the acceleration column given, it reproduced the in-simulation per-step fuel to within 0.003 mg/s, with an identical total of 91,260 mg. With -a it differences consecutive rows as if they were 1 s apart, so it is wrong for 0.2 s logs: always pass acceleration explicitly. --sum-output FC is g/km (71.58, which equals the in-sim 91.26 g / 1.275 km).

**Fit.** Meets every requirement:
- per-vehicle, per-step energy at 0.2 s, flat road;
- passenger ICE (petrol and diesel Euro-6d), an articulated truck and a BEV, all from one source family (HBEFA4);
- sensitive to acceleration (fuel cut-off for ICE, negative energy for BEV);
- available both online (TraCI, outputs) and offline (emissionsDrivingCycle).

Limits:
- The fit to HBEFA 4.2 is good for cars (FC error 4–7 %) but poor for the truck class (29 %).
- HBEFA describes European (EU) fleets, while the inflow is from MnDOT (US).
- How HBEFA4's acceleration dependence was derived is not documented on the page [VERIFY]. For HBEFA3 it came from slope data valid only to ±0.6 m/s² and was extrapolated beyond that (see F3).

**Sources:**
- SUMO documentation, 'HBEFA4-based' (page and markdown source on eclipse-sumo main; page footer edited 2026-10-12; describes the current development docs, not explicitly 1.27.1). <https://sumo.dlr.de/docs/Models/Emissions/HBEFA4-based.html> (seen: docs_page). Supports: HBEFA 4.2 model since 1.14.0, default since 1.23.0; class names; fleet share 2022; fit errors (PC petrol Euro-6d FC 3.97 %, diesel Euro-6d 6.93 %, PC_BEV FC_MJ 5.04 %, TT_AT >34-40t Euro-VI D-E FC 28.82 %); electricity = HBEFA FC_MJ
- SUMO documentation, 'Models/Emissions' overview (accessed 2026-10-13). <https://sumo.dlr.de/docs/Models/Emissions.html> (seen: docs_page). Supports: List of families (HBEFA, HBEFA3, HBEFA4, PHEMlight, PHEMlight5, Energy, MMPEVEM, Zero); fuel unit changed from litres to mg in 1.14.0; --emissions.volumetric-fuel; its stated default (HBEFA3/PC_G_EU4) is stale
- Eclipse SUMO source, tag v1_27_1: src/utils/emissions/HelpersHBEFA4.h, PollutantsInterface.cpp, HelpersEnergy.cpp/.h, HelpersMMPEVEM.cpp/.h, EnergyParams.cpp. <https://github.com/eclipse-sumo/sumo/tree/v1_27_1/src/utils/emissions> (seen: full_text). Supports: HBEFA4 polynomial form, clamping, the coasting-deceleration fuel cut-off, Energy model equations and defaults, MMPEVEM returns NaN on invalid states
- Local test, SUMO 1.27.1 libsumo, 2026-10-13: scratchpad/lit/emtest (run.py, types.add.xml, em_*.xml, ti_*.xml, bat_energy_bev.xml, dc2.csv). <file:///tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5/510dd91c-1bff-427e-90a7-d763e29122b9/scratchpad/lit/emtest> (seen: local_test). Supports: Default class, available data files, output units, offline/online agreement

### F2: SUMO electric models: Energy (Kurczveil EVM) and MMPEVEM (Koch et al.)
Energy model (HelpersEnergy.cpp, v1_27_1).

Power terms:
- m·g·sin(slope)·v;
- 0.5·m·(v² − v_prev²)/TS;
- the same kinetic term for rotatingMass;
- 0.5·1.2041·A·cd·v³;
- c_roll·m·g·v;
- a radial (turning) term.

Efficiencies and auxiliaries:
- positive power is divided by propulsionEfficiency;
- negative power is multiplied by recuperationEfficiency, and by exp(−k/|a|) when recuperationEfficiencyByDeceleration k > 0 (default 0; this follows Fiori et al. 2016);
- constantPowerIntake is then added;
- the result is in Wh/s.

Defaults: mass 1830 kg, A 2.6 m², cd 0.35, rotatingMass 40 kg, c_roll 0.01, aux 100 W, η_prop 0.98, η_recup 0.96. Recuperation has no power or torque limit, so the model can over-credit hard braking.

MMPEVEM (HelpersMMPEVEM.cpp; Koch et al. 2021, full text read):
- component model: gearbox, motor loss map, inverter, battery with internal resistance;
- recuperation limits: torque 95.5 Nm and power 42.8 kW by default;
- returns NaN when demanded torque or power exceeds motor limits, or the loss map is undefined.

The NaN case happened locally: VW_ID3.xml at 2 m/s² above 25.2 m/s gave 13 NaN steps. Policies or HDV models that exceed vehicle capability will therefore produce NaN.

Koch et al. 2021, WLTC with 10 % charging loss, MMPEVEM versus manufacturer data:
- e-up 14.8 vs 14.5–14.9 kWh/100 km;
- i3 15.5 vs 15.3–16.3;
- ID.3 15.9 vs 15.4–15.9;
- ID.4 18.6 vs 18.2–18.5.
The SUMO Energy model was 4–7 % lower. Against a BMW i3 chassis-dynamometer WLTC, the battery-power RMSE was 4.99 kW and the cumulative energy was within about 1 %.

Behrisch, Flötteröd & Wagner 2024 (full text read), highway at 110 km/h in mild weather, 10 % charging loss, versus manufacturer real-world data:
- HBEFA4/PC_BEV: −7 % to +2 %, but one value (17.92 kWh/100 km) for all vehicles;
- EVM: −4 % to +3 %;
- MMPEVEM: −1 % to +15 %;
- PHEMlight5: +6 % to +16 %.
On WLTC, MMPEVEM and EVM came closest to the manufacturer data, and HBEFA4 is insensitive to vehicle characteristics.

**Fit.** Both models compute BEV energy per step with regeneration, online or offline, and both are physics-based in acceleration. That makes them better suited than a polynomial to judging acceleration and braking effects.

EVM: needs a stated vehicle parameter set (mass, A, cd, efficiencies). Its unlimited recuperation is a known optimism.

MMPEVEM: most detailed and best validated on WLTC, but:
- it overestimates at constant 110 km/h (up to +15 %);
- it returns NaN beyond motor limits, which needs handling or accel limits consistent with the vehicle.

For a 100–120 km/h freeway, the 2024 highway comparison favours EVM or HBEFA4.

**Sources:**
- Kurczveil, T., López, P.A., Schnieder, E. (2014). Implementation of an Energy Model and a Charging Infrastructure in SUMO. In: Simulation of Urban Mobility (SUMO 2013), LNCS 8594, pp. 33-43, Springer [VERIFY: metadata from Crossref only, text not read]. <https://doi.org/10.1007/978-3-662-45079-6_3> (seen: secondary). Supports: Origin of the SUMO Energy/battery model
- SUMO documentation, 'Models/Electric' (accessed 2026-10-13). <https://sumo.dlr.de/docs/Models/Electric.html> (seen: docs_page). Supports: Battery device, parameters and defaults, rotatingMass replaced internalMomentOfInertia in 1.20.0, battery-output fields in Wh
- Koch, L., Buse, D.S., Wegener, M., Schoenberg, S., Badalian, K., Dressler, F., Andert, J. (2021). Accurate physics-based modeling of electric vehicle energy consumption in the SUMO traffic microsimulator. IEEE ITSC 2021, pp. 1650-1657. <https://www.ccs-labs.org/bib/koch2021accurate/koch2021accurate.pdf (DOI 10.1109/ITSC48978.2021.9564463)> (seen: full_text). Supports: MMPEVEM structure; WLTC Table I values; RMSE 4.99 kW and about 1 % cumulative error versus the i3 dynamometer; SUMO Energy model 4-7 % lower; 90 % charging efficiency applied for WLTP comparison
- Behrisch, M., Flötteröd, Y.-P., Wagner, P. (2024). Comparing and Parameterizing the Electrical Energy Consumption Models in SUMO. SUMO Conference Proceedings 5. <https://www.tib-op.org/ojs/index.php/scp/article/download/1012/1232 (DOI 10.52825/scp.v5i.1012)> (seen: full_text). Supports: Tables 2-3: WLTC and highway at 110 km/h comparisons of HBEFA4, PHEMlight5, EVM and MMPEVEM versus manufacturer data; HBEFA4 has a single BEV class
- Local test, SUMO 1.27.1, 2026-10-13 (MMPEVEM VW_ID3 NaN at a = 2 m/s², v ≥ 25.2 m/s). <file:///tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5/510dd91c-1bff-427e-90a7-d763e29122b9/scratchpad/lit/emtest/em_VW_ID3.xml> (seen: local_test). Supports: NaN behaviour of MMPEVEM beyond motor limits

### F3: PHEM / PHEMlight / PHEMlight5 (TU Graz) and the HBEFA-in-SUMO derivation
PHEM:
- TU Graz with FVT; 1 Hz longitudinal-dynamics model with engine maps.
- Used to produce HBEFA emission factors.
- Weller et al. 2019 (HBEFA 4.1, full text summarised via WebFetch):
  - passenger cars: single-car CO2 within −4 to +3 % on WLTC and −6 to +9 % on RDE;
  - fleet-average segments: within < 2 % of CO2 monitoring and spritmonitor data;
  - but individual diesel models were 14 % below spritmonitor real-world fuel use;
  - heavy-duty vehicles: PHEM vs VECTO 0.8 % (long haul) and 1.5 % (regional delivery); VECTO itself ±3 % versus on-road tests. No fleet validation was possible for HDVs.

PHEMlight (TU Graz flyer):
- reduced PHEM for coupling to microscale traffic models;
- inputs: speed, gradient and vehicle data, giving wheel power; fuel or emissions come from normalised power curves;
- covers PC and LCV (petrol, diesel, CNG, HEV, BEV, Euro 0–6d), HDV (rigid truck, truck and trailer, buses; BEV only for citybus) and motorcycles;
- free only as demo data (Euro-4 PC). Licence prices in the TU Graz document: PC+LCV €2,000, HDV €2,000, complete €5,500; input data updated about every 2 years, latest dated September 2020. The document date is not shown, so prices may have changed.

PHEMlight5 in SUMO: adds deterioration (--phemlight-year) and NOx temperature correction. Only PC_EU4_D_MW and PC_EU4_G are public.

Krajzewicz et al. (2015, full text): in the HBEFA 2.1 and 3.1 SUMO derivations, the acceleration dependence came from HBEFA road-slope data and was valid only up to ±0.6 m/s². Larger accelerations and decelerations were extrapolated. The models had not been compared with real-world data (comparisons were 'under investigation').

**Fit.** PHEMlight5 is a power-based ICE model and so physically more defensible for acceleration effects. But only Euro-4 cars are free, there is no free truck or BEV data, and the full data cost money and licence terms.

The free PHEMlight5/PC_EU4_G is usable as a second ICE cross-check, but it is an older car. The ±0.6 m/s² limit of the HBEFA slope-derived acceleration term is a key caveat for a study about acceleration and braking. Whether the HBEFA4 fit in SUMO uses the same procedure is [VERIFY].

**Sources:**
- Weller, K., Lipp, S., Röck, M., Matzer, C., Bittermann, A., Hausberger, S. (2019). Real World Fuel Consumption and Emissions From LDVs and HDVs. Frontiers in Mechanical Engineering 5:45. <https://www.frontiersin.org/journals/mechanical-engineering/articles/10.3389/fmech.2019.00045/full (DOI 10.3389/fmech.2019.00045)> (seen: full_text). Supports: PHEM calibration and validation numbers for HBEFA 4.1 (passenger cars and HDV). Note: read through an automated summary of the first about 100k characters, not every page by eye
- TU Graz ITnA, 'PHEMlight' model and licence description (undated PDF). <https://www.itna.tugraz.at/assets/files/areas/em/PHEMlight_en.pdf> (seen: full_text). Supports: Model approach (Pnorm curves), vehicle coverage, licence prices, data dated September 2020, free Euro-4 PC demo data
- TU Graz ITnA, 'PHEM' model and licence description (file name suggests 2024-04). <https://www.itna.tugraz.at/assets/files/areas/em/phem-en-202404.pdf> (seen: full_text). Supports: PHEM is 1 Hz and used for HBEFA; vehicle categories; licensed
- Krajzewicz, D., Behrisch, M., Wagner, P., Luz, R., Krumnow, M. (2015). Second Generation of Pollutant Emission Models for SUMO. In: Modeling Mobility with Open Data, Lecture Notes in Mobility, pp. 203-221, Springer. <https://elib.dlr.de/89398/1/2ndGenEmissions.pdf (DOI 10.1007/978-3-319-15024-6_12)> (seen: full_text). Supports: HBEFA-in-SUMO polynomial form; acceleration dependence from slope data up to ±0.6 m/s², extrapolated beyond; no real-world validation at the time; PHEMlight approach
- SUMO documentation, 'PHEMlight' and 'PHEMlight5' (markdown source on main, accessed 2026-10-13). <https://sumo.dlr.de/docs/Models/Emissions/PHEMlight5.html> (seen: docs_page). Supports: Only two public classes; other classes licensed from TU Graz; --phemlight-path, --phemlight-year, --phemlight-temperature

### F4: Virginia Tech models: VT-Micro, VT-CPFM (ICE), VT-CPEM (EV)
VT-Micro:
- regression of log fuel or emission rate on polynomials of instantaneous speed and acceleration (exponents up to 3; separate coefficients for a ≥ 0 and a < 0);
- fitted to ORNL data for 5 light-duty vehicles and 3 light trucks, R² 0.92–0.99 against those data (Ahn et al. 2002, abstract);
- VT-Micro v2.0 extended to 60 light-duty vehicles and trucks in 5 LDV and 2 LDT categories, prediction errors within 17 % against laboratory data (Rakha et al. 2004, abstract).

VT-CPFM:
- power-based fuel model calibrated from public data (EPA city and highway fuel-economy ratings plus vehicle specifications);
- designed to avoid the 'bang-bang' optimal control that linear fuel-power models produce;
- validated against in-field measurements with R² ≈ 0.96 (Park et al. 2013, abstract).
I did not read the model equations; the original 2011 paper's full text was blocked (HTTP 403).

VT-CPEM (Fiori et al. 2016, abstract):
- inputs: second-by-second speed, acceleration and grade;
- the regenerative-braking efficiency depends on instantaneous deceleration, and SUMO's Energy model includes this as the optional exp(−k/|a|) factor;
- average error 5.9 % against empirical data; EVs recover more energy in city than in highway driving; HVAC substantially reduces range.

Availability: the papers publish equations and calibration procedures. As far as I found, there is no official open-source code, so the model would be implemented in Python from the papers.

**Fit.** These are good candidates for an independent cross-check computed from logged trajectories:
- they are US-calibrated, which matches the MnDOT/US inflow better than HBEFA (EU);
- VT-CPFM can be calibrated to a chosen US car from public EPA ratings.

Needed before use:
- read the full text of Rakha et al. 2011 and Park et al. 2013 for the equations and parameters;
- check whether truck calibrations exist [VERIFY].

The 1 Hz calibration basis is fine for 0.2 s data if computed per step (a known assumption).

**Sources:**
- Ahn, K., Rakha, H., Trani, A., Van Aerde, M. (2002). Estimating Vehicle Fuel Consumption and Emissions based on Instantaneous Speed and Acceleration Levels. Journal of Transportation Engineering 128(2):182-190. <https://doi.org/10.1061/(ASCE)0733-947X(2002)128:2(182)> (seen: abstract). Supports: Speed- and acceleration-based hybrid regression; ORNL data, 5 LDV and 3 LDT; R² 0.92-0.99 [VERIFY full text]
- Rakha, H., Ahn, K., Trani, A. (2004). Development of VT-Micro model for estimating hot stabilized light duty vehicle and truck emissions. Transportation Research Part D 9(1):49-74. <https://doi.org/10.1016/S1361-9209(03)00054-3> (seen: abstract). Supports: 60 LDV and LDT, 5 LDV and 2 LDT categories, errors within 17 % [VERIFY full text]
- Rakha, H.A., Ahn, K., Moran, K., Saerens, B., Van den Bulck, E. (2011). Virginia Tech Comprehensive Power-Based Fuel Consumption Model: Model development and testing. Transportation Research Part D 16(7):492-503. <https://doi.org/10.1016/j.trd.2011.05.008> (seen: secondary). Supports: VT-CPFM exists; equations not read (publisher returned 403) [VERIFY]
- Park, S., Rakha, H., Ahn, K., Moran, K. (2013). Virginia Tech Comprehensive Power-based Fuel Consumption Model (VT-CPFM): Model Validation and Calibration Considerations. International Journal of Transportation Science and Technology 2(4):317-336 (open access). <https://doi.org/10.1260/2046-0430.2.4.317> (seen: abstract). Supports: Calibration from EPA city and highway ratings; R² about 0.96 versus in-field data [VERIFY full text]
- Fiori, C., Ahn, K., Rakha, H.A. (2016). Power-based electric vehicle energy consumption model: Model development and validation. Applied Energy 168:257-268. <https://ideas.repec.org/a/eee/appene/v168y2016icp257-268.html (DOI 10.1016/j.apenergy.2016.01.097)> (seen: abstract). Supports: VT-CPEM inputs; instantaneous regenerative-braking efficiency; average error 5.9 %; HVAC effect [VERIFY full text]
- Ahn, K., Bichiou, Y., Farag, M., Rakha, H.A. Multi-objective Eco-Routing Model Development and Evaluation for Battery Electric Vehicles (arXiv 2104.09336) [VERIFY: author list beyond the first two not checked]. <https://arxiv.org/pdf/2104.09336> (seen: secondary). Supports: VT-Micro functional form (exp of a speed × acceleration polynomial, split by sign of a); VT-CPEM outputs and its instantaneous regeneration

### F5: VSP/MOVES and CMEM
VSP / MOVES (US EPA):
- VSP estimates engine power demand per unit mass from second-by-second speed and vehicle type;
- MOVES puts time into 23 operating-mode bins, defined by VSP and speed, each with a rate in g/h (EPA page updated 2026-06-03);
- energy and fuel in MOVES come from these bin rates, so they resolve acceleration only at bin granularity.
The light-duty VSP formula usually cited is v·(1.1a + 9.81·grade + 0.132) + 0.000302·v³ (Jiménez-Palacios 1999 MIT thesis). I recall it from memory and did not read it in the thesis [VERIFY].

CMEM (UC Riverside CE-CERT, NCHRP 25-11):
- physical, power-demand modal model giving second-by-second fuel and tailpipe emissions;
- built on chassis-dynamometer tests of more than 350 light-duty vehicles; later extended to heavy-duty diesel;
- validation figures not found in what I read.

**Fit.** Neither model is a good main model:
- MOVES bins are coarse in acceleration, and running MOVES is a heavy offline workflow;
- CMEM is US light-duty and dated (data from the late 1990s), and its distribution and status today are unclear (the CE-CERT page returned 403).

VSP binning could serve as a third, US-based sanity check of the direction of effects, but it adds little beyond VT-CPFM.

**Sources:**
- US EPA, 'What is Vehicle Specific Power (VSP)?' (MOVES page, last updated 2026-06-03). <https://www.epa.gov/moves/what-vehicle-specific-power-vsp> (seen: docs_page). Supports: VSP definition (in words), 23 operating-mode bins, reference EPA-420-P-05-003
- Barth, M., An, F., Younglove, T., Scora, G., Levine, C., Ross, M., Wenzel, T. (2000). Development of a Comprehensive Modal Emissions Model. NCHRP 25-11 final report, LBNL-46116. <https://energyanalysis.lbl.gov/publications/development-comprehensive-modal> (seen: abstract). Supports: CMEM is a physical modal model with second-by-second fuel and emissions from more than 350 dynamometer-tested LDVs; no validation numbers in the abstract
- Jiménez-Palacios, J.L. Understanding and quantifying motor vehicle emissions with vehicle specific power and TILDAS remote sensing. PhD thesis, MIT [year 1999 VERIFY]. <https://dspace.mit.edu/handle/1721.1/44505> (seen: secondary). Supports: Origin of VSP; coefficients not verified [VERIFY]

### F6: Fuel to energy conversion (lower heating values and densities)
Lower heating value (LHV), higher heating value (HHV) and density from GREET 1.8d.1 (Argonne), as tabulated by ORNL:

| Fuel | LHV (MJ/kg) | LHV (Btu/gal) | HHV (MJ/kg) | Density |
|---|---|---|---|---|
| Conventional gasoline | 43.448 | 116,090 | 46.536 | 2,819 g/gal, about 744.7 g/L |
| Reformulated or low-sulfur gasoline | 42.358 | 113,602 | — | 2,830 g/gal |
| US conventional diesel | 42.791 | 128,450 | 45.766 | 3,167 g/gal, about 836.6 g/L |
| Low-sulfur diesel | 42.612 | 129,488 | — | 3,206 g/gal |

The g/L values are my own conversion with 1 US gal = 3.78541 L.

Conversions in kWh per kg of fuel: gasoline 43.448/3.6 = 12.07; diesel 42.791/3.6 = 11.89.

US DOE AFDC (no date shown) gives LHV gasoline/E10 112,114–116,090 Btu/gal and low-sulfur diesel 128,488 Btu/gal. The diesel figure differs from GREET's 129,488 by exactly 1,000; GREET's Btu/lb × density reproduces 129,488, so the AFDC value looks like a typo [VERIFY].

SUMO's volumetric-fuel option uses 742 g/L (gasoline) and 836 g/L (diesel) in code.

EU JEC values: not found in the main JEC WTT v4a report (they are in an appendix I did not open) [VERIFY if EU values are wanted for consistency with HBEFA].

**Fit.** Use with SUMO mass-based fuel output: kWh = fuel_mg × 1e-6 kg/mg × LHV(MJ/kg) / 3.6.

Use LHV (net), not HHV, for tank-to-wheel. GREET 1.8d.1 is old (2010) and current GREET may differ slightly, but the US values fit the MnDOT setting. Gasoline blend (E10) choice: the US retail fuel is mostly E10, whose LHV is lower than conventional E0 [VERIFY the exact E10 value from current GREET].

**Sources:**
- ORNL table 'Lower and Higher Heating Values of Gas, Liquid and Solid Fuels', source: GREET 1.8d.1, Argonne National Laboratory (2010), as hosted for UIUC course NPRE 470. <https://courses.grainger.illinois.edu/npre470/sp2018/web/Lower_and_Higher_Heating_Values_of_Gas_Liquid_and_Solid_Fuels.pdf> (seen: full_text). Supports: LHV, HHV and densities for gasoline and diesel
- US DOE Alternative Fuels Data Center, Fuel Properties Comparison (accessed 2026-10-13, no date shown). <https://afdc.energy.gov/fuels/properties> (seen: docs_page). Supports: LHV gasoline/E10 112,114-116,090 Btu/gal; low-sulfur diesel 128,488 Btu/gal

### F7: Local tiny test: one car accelerating, cruising, braking (0.2 s steps)
Profile:
- 0→30 m/s at 2 m/s² (15 s, 228 m);
- cruise at 30 m/s for 30 s (900 m);
- −3 m/s² to stop (10 s, 147 m);
- idle about 5 s.
The car was driven with speedMode 0 and setSpeed. ICE kWh use the GREET LHVs from F6.

ICE results (fuel → kWh):

| Class | Accel (kWh) | Cruise (kWh) | Cruise | Braking | Idle (5 s) |
|---|---|---|---|---|---|
| HBEFA4/PC_petrol_Euro-6d | 0.549 | 0.527 | 0.585 kWh/km, 6.5 L/100 km | 0 (cut-off) | 0.026 kWh, about 0.43 g/s |
| HBEFA4/PC_diesel_Euro-6d | 0.703 | 0.624 | 0.693 kWh/km, 7.0 L/100 km | 0 | 0.026 |
| HBEFA4/TT_AT_gt34-40t_Euro-VI_D-E | 6.23 | 3.46 | 3.84 kWh/km, 38.7 L/100 km at 108 km/h | 0 | 0.135 |
| HBEFA3/PC_G_EU4 | 0.636 | 0.669 | 0.744 kWh/km | 0.002 | 0.053 |
| PHEMlight5/PC_EU4_G | 0.795 | 0.593 | 0.659 kWh/km | 0.0006 | 0.015 |

BEV results (Wh):

| Class | Accel | Cruise | Braking | Idle |
|---|---|---|---|---|
| HBEFA4/PC_BEV | 184.8 | 142.6 (158 Wh/km) | −127.3 | 4.2 |
| Energy (mass 1800 kg, A 2.3, cd 0.28, η 0.9/0.8, 100 W aux) | 280.8 | 146.8 (163 Wh/km) | −172.4 | 0.1 |
| MMPEVEM VW_ID3 | NaN (motor limit exceeded above 25.2 m/s) | 149.7 (166 Wh/km) | −75.2 (recuperation power capped) | 0.5 |

Two checks on the BEV numbers:
- For the Energy model, the net battery drop of 255.95 Wh matches the tripinfo electricity_abs and the battery-output totals.
- The kinetic energy at 30 m/s for 1.8 t is 0.225 kWh. HBEFA4/PC_BEV spends only 0.185 kWh accelerating and recovers 69 % of it, which is not physically consistent for a heavy BEV and shows the polynomial's limits in acceleration.

Also observed: the HBEFA4 diesel car uses more fuel mass than the petrol car at cruise. That is the model's output; I did not investigate the cause.

**Fit.** This confirms the following:
- every candidate runs in 1.27.1 at 0.2 s;
- ICE fuel cut-off is active in the braking phase;
- BEV regeneration is negative energy;
- units are as documented;
- offline recomputation is exact.

It also shows a spread between models in the acceleration phase: about ±25 % among ICE models and about 1.5× between the BEV models. So the energy effect of smoothing will depend on the model, which argues for a pre-registered cross-check.

**Sources:**
- Local test, SUMO 1.27.1 libsumo, 2026-10-13. <file:///tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5/510dd91c-1bff-427e-90a7-d763e29122b9/scratchpad/lit/emtest/run.py> (seen: local_test). Supports: All numbers in this finding

### Verification: citations and numbers that failed or were corrected

- [F1] **details_wrong**: Local test SUMO 1.27.1 (emtest), incl. emissionsDrivingCycle offline claim. Correction: Re-ran run.py for all 8 types: the in-sim numbers reproduce. The tripinfo electricity_abs of 255.95 Wh equals totalEnergyConsumed 428.32 minus regenerated 172.37, which equals the battery drop. --emission-output.step-scaled exists in 1.27.1. Two corrections on emissionsDrivingCycle. (1) The docs (Tools/Emissions) say the timeline must be 'increasing in steps of 1 s', and the code counts each row as 1 s: time++, l += v, and the sums add raw per-second rates. On 0.2 s rows, the Time column and the absolute totals are therefore 5x too large. The g/km figure (71.58) comes out right only because the distance and fuel sums are both inflated 5x. (2) The tool has no step-length option, so TS = 1 s. HelpersEnergy computes lastV = v - a·TS and divides by TS. I ran the Energy vType offline on a 0.2 s timeline with an explicit acceleration column. The electricity was NEGATIVE while accelerating at 0.2 s and 0.4 s (v = 0.4, a = 2 gives -0.447 Wh/s). Phase totals were 267.3 / 138.8 / -186.7 Wh against 280.8 / 146.8 / -172.4 in-sim, and the net was 219.5 against 255.95 Wh (-14 %). So 'offline recomputation is exact' holds only for HBEFA4, whose polynomial does not depend on TS, and not for EVM or MMPEVEM on 0.2 s data.
- [F4] **claim_not_supported**: Rakha et al. (2011) TR-D 16(7):492-503, DOI 10.1016/j.trd.2011.05.008. Correction: Crossref confirms the metadata and the five authors. The claim that VT-CPFM is 'designed to avoid bang-bang control' was not confirmed from any text I opened. Keep it [VERIFY].
- [F5] **details_wrong**: Barth et al. (2000) CMEM, NCHRP 25-11, LBNL page. Correction: The seven authors, April 2000, >350 dynamometer-tested LDVs and second-by-second output are confirmed. 'LBNL-46116' appears only in the PDF filename, not as a stated report number. 'Later extended to heavy-duty diesel' is not in the abstract that was cited; it needs its own source or [VERIFY].
- [F6] **claim_not_supported**: US DOE AFDC Fuel Properties Comparison. Correction: AFDC shows 112,114-116,090 Btu/gal (gasoline/E10) and 128,488 Btu/gal (diesel), as stated. The suggestion that 128,488 is a 'typo' is speculation: AFDC may use newer GREET ULSD values. It should not be stated even as a likely typo.
- [F7] **details_wrong**: Local test SUMO 1.27.1 run.py. Correction: The accel and cruise numbers reproduce exactly when converted with the F6 LHVs (petrol 0.549 / 0.527, diesel 0.703 / 0.624, truck 6.23 / 3.46, HBEFA3 0.636 / 0.669, PHEM5 0.795 / 0.593 kWh; BEVs 184.8 / 142.6 / -127.3, 280.8 / 146.8 / -172.4, NaN / 149.7 / -75.2 Wh). The idle phase is wrong: the script runs to 80 s, so idle lasts about 24.6 s, not 5 s. The raw idle totals are petrol 10.25 g (0.124 kWh), HBEFA4 BEV 20.0 Wh, Energy 0.69 Wh and MMPEVEM 2.48 Wh; the table's idle column is these values rescaled to 5 s, which is not disclosed. 'About ±25 % among ICE models' overstates the spread: the accel-phase range 0.549-0.795 kWh is about ±18 % around the midpoint (max/min 1.45). The HBEFA4 BEV vType sets no mass (the polynomial takes no mass input), so the kinetic-energy comparison is against an assumed 1.8 t car, not the simulated vehicle.
- [F3] **outdated**: PHEMlight licence €2,000 PC+LCV, €2,000 HDV, €5,500 complete; data Sept 2020. Correction: Correct as printed, but the document is undated and the data are from 2020; current prices are unknown.
- [F5] **unchecked**: VSP = v·(1.1a + 9.81·grade + 0.132) + 0.000302·v³. Correction: Not in any source opened; remains [VERIFY].
- [F6] **outdated**: Gasoline LHV 43.448 MJ/kg, 116,090 Btu/gal, 2,819 g/gal (744.7 g/L); diesel 42.791 MJ/kg, 128,450 Btu/gal, 3,167 g/gal (836.6 g/L); 12.07 / 11.89 kWh/kg. Correction: Arithmetic and transcription are correct, but GREET 1.8d.1 dates from 2010. US retail fuel is E10, so the E0 'conventional gasoline' LHV overstates energy per kg; current GREET is needed before use.
- [F6] **wrong**: AFDC 128,488 Btu/gal diesel is a typo. Correction: The value is correctly quoted, but nothing supports calling it a typo.
- [F7] **wrong**: Idle (5 s): petrol 0.026 kWh, BEV 4.2 Wh, Energy 0.1 Wh, MMPEVEM 0.5 Wh; truck 0.135 kWh. Correction: Actual idle is about 24.6 s. The raw totals are petrol 0.124 kWh (about 0.42 g/s), HBEFA4 BEV 20.0 Wh, Energy 0.69 Wh, MMPEVEM 2.48 Wh and truck about 0.64 kWh; the table values are undisclosed 5 s rescalings.
- [F7] **wrong**: ICE accel spread about ±25 %; BEV about 1.5x. Correction: The ICE spread is about ±18 % around the midpoint (max/min 1.45). BEV 280.8 / 184.8 = 1.52x is right.

Verified as stated: 41 citations and numbers.

### Open questions
- BEV main model: HBEFA4/PC_BEV (one family, single class) or SUMO Energy/EVM with a stated vehicle parameter set (physics-based acceleration, but uncapped recuperation)? The author decides.
- Fleet realism: HBEFA4 and PHEM are EU fleets (Euro-6d cars), while the inflow is MnDOT/US (heavier SUVs and pickups, US trucks). Accept and disclose, or scale mass and parameters to the US fleet?
- Trucks: HBEFA4 TT_AT fit error is 28.8 % for fuel, and no free independent truck model was found. Is a truck-energy sensitivity row enough? What truck speed cap applies (trucks at 120 km/h are unrealistic)?
- ICE/BEV comparability for the V16 headline: monetary per carrier (D), tank/battery-to-wheel (A), plug-to-wheel (B, with charging efficiency 0.9 per Koch 2021 and Behrisch 2024) or well-to-wheel (C, factors still to source)?
- [VERIFY] Was HBEFA4's acceleration dependence in SUMO derived like HBEFA3's (from slope data, valid to ±0.6 m/s², extrapolated beyond)? Ask the SUMO developers or read the HBEFA4 fitting scripts. It matters because control acts on acceleration.
- [VERIFY] VT-CPFM equations and parameters (Rakha et al. 2011; Park et al. 2013 is open access) need a full-text read before implementing the cross-check. Also: do truck calibrations exist?
- Auxiliary load and temperature: a Minnesota winter morning means large BEV heating loads (Fiori 2016 abstract: HVAC substantially reduces range). Fix the auxiliary power per season, or keep the 100 W / 360 W defaults and disclose?
- The HBEFA4 diesel car used more fuel mass than the petrol car at 108 km/h cruise in my test, and HBEFA4 petrol idle was about 0.43 g/s. Plausibility not checked against HBEFA tables.
- Policy exploitation: the energy model is in the reward, so the zero-fuel coasting threshold and uncapped BEV regeneration are possible reward hacks. Add a pre-registered check that the cross-check model agrees in sign.


## Generalised-cost values

### Recommendation (researcher)
These are candidates for V16/V18. The author must confirm them; nothing here binds yet.

(1) Value of time. Use USDOT BCA Guidance, Dec 2025, in 2024 $:
- cars: personal VTTS $20.10 per person-hour × weekday-peak occupancy 1.34 = $26.93 per vehicle-hour. Commuting is valued at the personal rate.
- trucks, if the simulation has any: $37.20 per vehicle-hour, driver only.
- sensitivity rows:
  - the 2016 memo ranges, ×0.70 to ×1.20;
  - MnDOT SFY2025: auto $26.00 per person-hour, truck $39.30. The dollar year is unstated [VERIFY];
  - an EU row from HEATCO, EU-25 car commute €8.48 per passenger-hour (€2002, factor prices). It must be uprated and labelled clearly before use.

(2) Energy. Price at resource cost, excluding taxes, as USDOT, MnDOT and HEATCO all do. Price each carrier in its native unit and report kWh separately.
- Central, 2025 EIA annual averages minus federal and average state taxes: gasoline about $2.58/gal (about $0.073/kWh HHV, $0.077/kWh LHV); diesel about $3.06/gal (about $0.076/kWh HHV).
- Electricity: 2025 US residential 17.30 ¢/kWh at the meter (no tax adjustment available).
- High row: Sep 2026 prices. Gasoline $4.355/gal and diesel $6.291/gal, both including taxes.
- Perceived-cost row: prices including taxes.
- State the HHV or LHV basis.
- Optional externality row: MnDOT's SCC of $238/t CO2 (2023 $). USDOT no longer monetises CO2.

(3) Hard braking. No accepted monetisation per event exists, so do not present a priced hard brake as sourced. Options:
- (a) Preferred for the headline: a constraint or guard, with the CAV hard-brake rate reported, for example 'not worse than NC by more than y %'.
- (b) A penalty in the training reward only, with headline sensitivity rows at $0, about $1 and about $63 (2024 $). These bounds are derived from Desai et al. 2021, the USDOT crash costs and NHTSA 2023, with all assumptions stated.
- (c) A crash-risk-based estimate, only if the threshold matches the source (about 2.5-2.7 m/s² on all vehicles, not V11's 3-4 m/s² on CAVs) and the severity mix is freeway-specific.

(4) Weights. Under these values delay dominates: 1 kWh of fuel is about 10-12 s of one car's delay. So:
- keep the delay guard x %;
- report energy on its own (V10);
- add an energy-weight sweep, since the control literature typically uses Pareto sweeps rather than monetary weights.

Dollar year: 2024 $ throughout, with the GDP deflator from BCA Table A-7 for any conversion.

### Verifier verdict on the recommendation
Sound: **True**. The core of the recommendation rests on verified evidence:
- USDOT Dec 2025 VTTS: $20.10 × 1.34 = $26.93/veh-h (2024 $). The document is hash-checked against an independent download.
- 2025 EIA fuel prices net of federal and average state taxes.
- EIA 2025 residential electricity at 17.30 ¢/kWh.
- Resource-cost treatment: USDOT treats taxes as transfers, MnDOT uses a 'tax-neutralized' fuel price, HEATCO uses factor costs.
- The finding that no guidance gives a money value per hard brake. USDOT BCA and MnDOT give none; MnDOT's speed-cycle change is an operating-cost unit with no number.
- The arithmetic, which recomputes (delay dominates: 1 kWh of fuel is about 10-12 s of one car's delay).

Corrections needed before the author uses it:
1. The MnDOT sensitivity row is outdated. Use MnDOT SFY2027 Table A.1 (Aug 2026, all values in 2025$): auto $26.20 (range $19.50-31.90) per person-hour, truck $40.60, SCC $256/t (2025$). This also settles the 'dollar year unstated' [VERIFY].
2. The optional carbon row should cite the SFY2027 SCC ($256/t, 2025$), not $238 (2023$).
3. The EUROCONTROL secondary values are outdated: the current release gives €22.89 / €55.90 at 2025 prices. They are air-passenger values uprated by inflation only, so they cannot serve as the EU car row.
4. Fix the JTRP 2025 co-author initials, Deshpande's γ list and author list, and the TR-C acceptance of arXiv:2408.05609.
5. The HHV basis of the EIA heat contents is not stated on the cited page. Confirm it in MER Appendix A before writing 'HHV' into V18.
6. Occupancy: USDOT's peak window is 06:00-08:59, but the demand runs 06:00-10:00. A time-weighted 1.34 / 1.41 occupancy, or a stated simplification, is more accurate than claiming a 'match'.

On hard braking, option (a) (a guard instead of a price) is defensible on the evidence, but it reopens V16. V16 is already decided as form A, which includes a cost per CAV hard brake. The finder correctly leaves this to the author. It should be put to the author explicitly as a change to V16, not as a default.

The $1-63 per-brake bounds are the finder's own derivation, and the inputs do not support them well:
- they rest on a cross-sectional work-zone slope;
- the probe penetration is 4.7 %;
- the threshold differs (OEM 2.67 m/s² vs V11's 3-4 m/s²);
- they use an all-roads crash-severity mix.

So they are fine only as clearly labelled sensitivity rows, never as a sourced central value.

The energy-weight sweep advice follows from the verified control literature: Zegeye et al. 2012 and Jayawardana & Wu 2022 use normalised or hand-tuned weights and sweeps, not money values.

Finally, the 2026 fuel prices are volatile (the next EIA release is 2026-10-14), so pin the price period and date it in the protocol.

### Local checks
I ran no SUMO test: this topic needed none.

Done locally (Python, scratchpad only):
- downloaded the documents and converted the PDFs to text (pdftotext). transportation.gov returned 403 (Akamai) to both curl and WebFetch, so the USDOT PDFs were read from Wayback Machine snapshots dated 2026-04 to 2026-10;
- computed the $/kWh conversions, per-vehicle-hour VTTS, the NHTSA mean crash cost, and the illustrative per-hard-brake bounds.

Scratch files are in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5/510dd91c-1bff-427e-90a7-d763e29122b9/scratchpad/lit/dl. The repo was not modified.

Disclosure: one Unpaywall API query (to find an open-access PDF location) included the user's email address as the API's required contact parameter. I should not have done that without asking, and I did not repeat it.

### F1: USDOT BCA Guidance for Discretionary Grant Programs, December 2025 edition ('2026 Update'): value of time, occupancy, crash costs, operating-cost treatment
This is the latest edition. The archived DOT landing page (Wayback snapshot of 2026-09-29) lists only 'Benefit Cost Analysis Guidance 2026 Update (Final).pdf', page last updated 2025-12-23. All values are in 2024 dollars.

Table A-2, value of travel time savings per person-hour:
- personal $20.10 (local travel; commuting must be valued at the personal rate);
- business $34.60;
- all purposes $21.80 (88.2 % personal, 11.8 % business);
- long-distance intercity personal $28.20;
- truck drivers $37.20, bus drivers $40.30. The operator only: no passengers, no freight.

Table A-3, occupancy (2022 NHTS): weekday peak 1.34 (trips starting 06:00-08:59 or 16:00-18:59), off-peak 1.41, weekend 1.81, all travel 1.52.

Table A-1, comprehensive crash costs (2024 $): PDO crash $9,700 (assumes 1.77 vehicles); injury crash $342,400; fatal crash $15,366,900. KABCO values: O $5,500, C $122,400, B $256,300, A $1,302,300, K $13,700,000.

Table A-4, vehicle operating costs: $0.56/mi for light-duty vehicles and $1.23/mi for trucks (AAA 2024, ATRI 2025). These exclude taxes and tolls, which the guidance calls transfer payments in BCA.

The guidance also says distance-based costs should not be converted into time-based equivalents. CO2 is no longer monetised (footnote 18: EO 14154 and OMB M-25-27). The previous edition (Nov 2024, 2023 $) gave personal $19.40, all purposes $21.10, truck $35.70.

**Fit.** Strong fit as the central US source.
- The F3Z peak (06:00-10:00) matches the weekday-peak occupancy definition.
- Car: $20.10 × 1.34 = $26.93 per vehicle-hour (my arithmetic). With the all-purpose value it is $29.21.
- Truck: $37.20 per vehicle-hour, driver only. Cargo time is not valued.
- Limits: these are national averages, not Minnesota-specific. The VTTS values are still derived from the 2016 memo (F2). The value of time may change again with the next edition, so check again before freezing the protocol.

**Sources:**
- U.S. DOT Office of the Secretary (December 2025). Benefit-Cost Analysis Guidance for Discretionary Grant Programs ('2026 Update (Final)'), Appendix A, Tables A-1 to A-4 and A-7; §5.3; footnote 18.. <https://www.transportation.gov/sites/dot.gov/files/2025-12/Benefit%20Cost%20Analysis%20Guidance%202026%20Update%20%28Final%29.pdf (read via http://web.archive.org/web/20261006165359/ because transportation.gov returned 403)> (seen: full_text). Supports: All values in 2024 $: VTTS, occupancy, crash costs, operating costs, taxes treated as transfers, CO2 no longer monetised.
- U.S. DOT, Benefit-Cost Analysis Guidance for Discretionary Grant Programs landing page (Wayback snapshot 2026-09-29), 'Last updated: Tuesday, December 23, 2025'. <http://web.archive.org/web/20260929185234/https://www.transportation.gov/mission/office-secretary/office-policy/transportation-policy/benefit-cost-analysis-guidance> (seen: docs_page). Supports: The 2026 Update is the edition listed as current.
- U.S. DOT (November 2024). Benefit-Cost Analysis Guidance 2025 Update (Final), Table A-2 (2023 $). <http://web.archive.org/web/20260407222503/https://www.transportation.gov/sites/dot.gov/files/2024-11/Benefit%20Cost%20Analysis%20Guidance%202025%20Update%20(Final).pdf> (seen: full_text). Supports: Previous-edition values for comparison (personal $19.40, all purposes $21.10, truck $35.70).

### F2: USDOT 'Revised Departmental Guidance on Valuation of Travel Time in Economic Analysis', 27 September 2016 (Revision 2, 2016 Update)
The memo values travel time as a percentage of hourly earnings:
- local personal 50 %, plausible range 35-60 %;
- business 100 %, range 80-120 %;
- vehicle operators 100 %, range 80-120 %.

Table 4 (2015 $ per person-hour): local personal $13.60, business $25.40, all purposes $14.10; truck drivers $27.20.

Table 5 ranges (2015 $): local personal $9.50-16.30; truck drivers $21.80-32.70.

The Dec 2025 BCA guidance (F1) still cites this memo as the basis of Table A-2. I found no later revision.

**Fit.** This memo is the method behind F1. Its plausible ranges give a defensible sensitivity row: personal ×0.70 to ×1.20 of the central value. In 2024 $ that is about $14.07-24.12 per person-hour, or $18.85-32.32 per car-hour at occupancy 1.34 (my arithmetic). Its 2015 $ figures are outdated, so use the F1 values for levels.

**Sources:**
- U.S. DOT Office of the Secretary, memorandum by V. White (27 Sept 2016). Revised Departmental Guidance on Valuation of Travel Time in Economic Analysis, Tables 1, 2, 4, 5. <https://www.transportation.gov/sites/dot.gov/files/docs/Revised%20Departmental%20Guidance%20on%20Valuation%20of%20Travel%20Time%20in%20Economic%20Analysis%20-%20September%202016.pdf (read via http://web.archive.org/web/20260508124111/)> (seen: full_text). Supports: VTTS percentages of wage, sensitivity ranges, 2015 $ values; the revision history (1997, 2003, 2011, 2016).

### F3: MnDOT Table A.1: recommended standard values for BCA, SFY 2025 (September 2024)
Value of travel time per person-hour, low / most likely / high:
- auto $19.30 / $26.00 / $31.60;
- truck driver $31.50 / $39.30 / $47.20.

These are adapted from the USDOT 2016 memo using Minnesota incomes and wages. The table does not state the dollar year of these rows; the CO2 row says 2023 $ [VERIFY].

Other values in the table:
- variable vehicle operating costs (auto $0.32/mi, truck $0.73/mi) value fuel 'at real tax-neutralized price';
- the social cost of CO2 is still included, at $238 per metric ton (2023 $);
- per-crash comprehensive costs (most likely): fatal $15.9M, suspected minor injury $380k, possible injury $180k, PDO $18k.

The MnDOT BCA web page also lists a cost per 'speed-cycle change' (cruise speed to a stop and back) as an operating-cost item. It is valued from added braking and acceleration costs, not crash risk. MnDOT gives no number for it on that page.

**Fit.** Good local sensitivity row: the inflow comes from MnDOT US-169. Its auto value is about 29 % above USDOT's personal value. It supports pricing fuel at a tax-neutral (resource) cost. The speed-cycle concept is the closest accepted monetisation of a braking event, but it is about operating cost. If I read it correctly, it would double count energy that SUMO already models. SFY 2026 values may exist; I did not find them on the page.

**Sources:**
- Minnesota DOT, Office of Transportation System Management (Sept 2024). Table A.1 Recommended standard values for use in cost-effectiveness & benefit-cost analysis in SFY 2025. <https://dot.state.mn.us/planning/program/pdf/Table%20A.1%20SV%20L-ML-H%2016-Sep-2024.pdf> (seen: full_text). Supports: Minnesota VTTS low/most likely/high values, tax-neutral fuel, SCC $238/t (2023 $), crash costs.
- Minnesota DOT, Benefit-Cost Analysis for Transportation Projects (web page). <https://dot.mn.gov/planning/program/benefitcost.html> (seen: docs_page). Supports: Definition of the speed-cycle change and its use as an operating-cost unit (dollars per speed-cycle change).

### F4: HEATCO D5 (2006), the EU reference for a sensitivity row
Table 4.7, non-work car VTTS per passenger-hour (€2002, factor prices):
- EU-25 commute, short distance €8.48;
- commute, long distance €10.89;
- other, short distance €7.11;
- Germany €8.04, Netherlands €7.77, France €10.95 (commute short).

Table 4.6, business car/train VTTS: EU-25 €23.82.

Table 4.8, road freight VTTS: €2.98 per tonne-hour (EU-25). Whether this covers driver costs: [VERIFY].

Other HEATCO rules:
- factor costs are the unit of account: market prices with indirect taxes must be converted;
- VTTS should be uprated with GDP per capita at an inter-temporal elasticity of 0.7;
- results should be run both with and without PPP adjustment.

**Fit.** Usable only as a clearly labelled EU sensitivity row, and only after uprating from 2002 to a current year. I did not source the HICP or GDP-per-capita indices, so I did not compute the uprated value.

A secondary source (EUROCONTROL standard inputs) reports HEATCO-based values uprated to 2024. It is aviation-oriented and was not checked [VERIFY].

National guidance (UK TAG Data Book v2.01, May 2025; Germany BVWP; Netherlands KiM) would be more current. I did not open them [VERIFY].

**Sources:**
- Bickel P., Friedrich R. et al.; Friedrich R. (ed.) (2006). HEATCO Deliverable 5: Proposal for Harmonised Guidelines for the Integrated Assessment of Transport Projects in Europe. IER, University of Stuttgart. Contract FP6-2002-SSP-1/502481. <https://elib.uni-stuttgart.de/server/api/core/bitstreams/99416160-e71b-4e00-a4ec-74b22c81da54/content> (seen: full_text). Supports: Tables 4.6-4.8 (I read the rows quoted); factor-cost accounting rule; elasticity 0.7; PPP advice.
- EUROCONTROL Standard Inputs for Economic Analyses, 'passenger value of time' chapter. <https://ansperformance.eu/economics/cba/standard-inputs/latest/chapters/passenger_value_of_time.html> (seen: secondary). Supports: Seen only in a search snippet: personal €22.34/h and business €54.56/h, HEATCO uprated to 2024 [VERIFY; aviation context].

### F5: US EIA retail fuel prices and taxes
US annual averages, $/gal including taxes:
- regular gasoline: 2024 $3.304, 2025 $3.097;
- on-highway diesel: 2024 $3.760, 2025 $3.660.

Minnesota regular gasoline: 2025 $2.963.

2026 monthly US prices (EIA release of 10/6/2026) are much higher and volatile:
- regular gasoline: Apr $4.103 to Sep $4.355;
- diesel: Apr $5.501, Aug $5.462, Sep $6.291.

Taxes as of January 2026 (EIA FAQ):
- federal: 18.40 ¢/gal on gasoline, 24.40 ¢/gal on diesel;
- average state tax: 33.27 ¢/gal on gasoline, 35.50 ¢/gal on diesel.
- EIA's 'factors affecting gasoline prices' page gives 33.55 ¢/gal for state gasoline taxes, which differs slightly. Local and sales taxes are excluded from both.

Removing federal and average state taxes (my arithmetic): 2025 gasoline about $2.58/gal and diesel about $3.06/gal. This is an approximation of resource cost: the Jan 2026 tax rates are applied to 2025 prices, and taxes are not the only wedge.

**Fit.** Prices may already be outdated and are moving fast in 2026, so pin one period and date it.
- Central: the 2025 annual average, with a 2026 high row.
- Appraisal practice prices fuel at resource cost, excluding taxes: USDOT treats taxes as transfers, MnDOT uses a 'tax-neutralized' price, HEATCO uses factor costs.
- A perceived cost, including taxes, belongs only in a behavioural sensitivity row.

**Sources:**
- U.S. EIA, Weekly Retail Gasoline and Diesel Prices, annual and monthly (Release Date 10/6/2026). <https://www.eia.gov/dnav/pet/pet_pri_gnd_dcus_nus_a.htm ; https://www.eia.gov/dnav/pet/pet_pri_gnd_dcus_nus_m.htm ; https://www.eia.gov/dnav/pet/pet_pri_gnd_dcus_smn_a.htm> (seen: docs_page). Supports: Annual and monthly retail prices including taxes, US and Minnesota.
- U.S. EIA FAQ 'How much tax do we pay on a gallon of gasoline and on a gallon of diesel fuel?' (as of January 2026). <https://www.eia.gov/tools/faqs/faq.php?id=10&t=10> (seen: docs_page). Supports: Federal 18.40/24.40 ¢/gal; average state 33.27/35.50 ¢/gal.
- U.S. EIA, Gasoline explained: factors affecting gasoline prices. <https://www.eia.gov/energyexplained/gasoline/factors-affecting-gasoline-prices.php> (seen: docs_page). Supports: Average state gasoline tax of 33.55 ¢/gal as of January 2026; this differs from the FAQ.

### F6: Heating values and conversion to $/kWh
Higher heating value (HHV, EIA):
- gasoline incl. ethanol: 120,214 Btu/gal (2023 end-use, MER Aug 2024);
- ULSD diesel: 137,381 Btu/gal;
- 1 kWh = 3,412 Btu.

Lower heating value (LHV, DOE AFDC fuel properties page):
- gasoline/E10: 112,114-116,090 Btu/gal;
- low-sulfur diesel: 128,488 Btu/gal.

Energy per gallon (my arithmetic): gasoline 35.23 kWh HHV and 32.9-34.0 kWh LHV; diesel 40.26 kWh HHV and 37.66 kWh LHV.

Prices per kWh of fuel energy:
- gasoline, 2025 incl. tax: $0.088/kWh HHV, $0.093/kWh LHV;
- gasoline, 2025 excl. tax: $0.073 HHV, $0.077 LHV;
- diesel, 2025 incl. tax: $0.091 HHV, $0.097 LHV;
- diesel, 2025 excl. tax: $0.076 HHV, $0.081 LHV;
- Sep 2026, excl. tax: gasoline $0.109 HHV, diesel $0.141 HHV.

Per litre: gasoline $0.818/L incl. tax and $0.682/L excl. tax (2025).

**Fit.** The HHV versus LHV choice moves $/kWh by about 5-7 %. Fuel energy (tank) and battery or meter electricity are also different bases.

Advice: price each carrier in its native unit (litres or mg of fuel; kWh of electricity at the meter, with a stated charging-efficiency assumption, which I did not source). Use kWh only for reporting. The conversions are mine and the inputs are cited.

**Sources:**
- U.S. EIA, Energy Explained: British thermal units (Btu). <https://www.eia.gov/energyexplained/units-and-calculators/british-thermal-units.php> (seen: docs_page). Supports: 1 kWh = 3,412 Btu; gasoline 120,214 Btu/gal; diesel 137,381 Btu/gal.
- U.S. DOE Alternative Fuels Data Center, Fuel Properties Comparison. <https://afdc.energy.gov/fuels/properties> (seen: docs_page). Supports: LHV and HHV per gallon for gasoline/E10 and low-sulfur diesel (footnote source not checked) [VERIFY].

### F7: US EIA electricity prices
Electric Power Monthly Table 5.3, US annual averages (¢/kWh):
- residential: 2024 16.48, 2025 17.30;
- commercial: 2024 12.75, 2025 13.41;
- year-to-date to July 2026: residential 18.19, commercial 13.97.

Table 5.6.A, July 2026, Minnesota: residential 17.45, commercial 13.49. US: residential 18.31, commercial 14.53.

**Fit.** Central for home charging: the 2025 US residential price of $0.173/kWh at the meter. A commercial row ($0.134) can stand for depot or workplace charging. Public DC fast-charging prices are higher; I did not source them.

These are retail prices. Electricity taxes are not separated out in these tables, so a resource-cost adjustment for electricity was not made [VERIFY]. Note that $/kWh at the meter is more than the $0.07-0.09/kWh of fuel chemical energy. This is not a contradiction: the bases differ.

**Sources:**
- U.S. EIA, Electric Power Monthly, Table 5.3 Average Price of Electricity to Ultimate Customers, 2016-July 2026. <https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_03> (seen: docs_page). Supports: US annual residential and commercial prices for 2024 and 2025, and 2026 year-to-date.
- U.S. EIA, Electric Power Monthly, Table 5.6.A (July 2026 and 2025, by state). <https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_6_a> (seen: docs_page). Supports: Minnesota and US July 2026 prices by sector.

### F8: Hard braking as a crash surrogate: the evidence found
Desai et al. (2020/2021), 23 Indiana interstate work zones:
- threshold: deceleration above 8.76 ft/s² (2.67 m/s²), as defined by the vehicle manufacturer (OEM);
- data: 196,215 hard-braking events from connected-vehicle probes (July-August 2019) and the crashes over the same two months;
- result: about 1 crash per mile for every 147 hard-braking events per mile (linear fit, R² 0.85);
- probe penetration averaged 4.7 %.

Hunter et al. (2021), 8 signalized intersections (abstract only): strong Spearman correlation between hard braking and rear-end crashes more than 400 ft upstream.

Sakhare & Bullock (2026), Indiana non-interstate state and US roads (Research Square preprint, not peer reviewed; abstract only):
- the best threshold was 0.25 g (ρ = 0.71);
- in a log-log fit, doubling the braking rate raised the crash rate by about 25 %. That implies an elasticity of about 0.32 (my calculation).

Simons-Morton et al. (2012), teen naturalistic study (search snippet only): elevated g-force event rates predicted crashes and near-crashes (OR 1.07 per unit rate; reported AUC 0.76) [VERIFY].

All of these are cross-sectional or associational. None gives a causal crash risk per hard-braking event, and none gives a monetary value per event.

**Fit.** No accepted monetisation per hard-braking event exists in any guidance I checked: USDOT BCA, MnDOT, HEATCO. Hard braking is used for screening and as a surrogate, not as a priced unit.

The threshold also does not match: V11 proposes 3-4 m/s² for CAVs, while the crash relations use about 2.45-2.67 m/s² measured on all probe vehicles. Ratios cannot be transferred across thresholds without assumptions.

**Sources:**
- Desai J., Li H., Mathew J.K., Cheng Y.-T., Habib A., Bullock D.M. (2021, online 2020-11-16). Correlating Hard-Braking Activity with Crash Occurrences on Interstate Construction Projects in Indiana. Journal of Big Data Analytics in Transportation 3:27-41. <https://doi.org/10.1007/s42421-020-00024-x (CC-BY PDF read via http://web.archive.org/web/20220120024858/https://link.springer.com/content/pdf/10.1007/s42421-020-00024-x.pdf)> (seen: full_text). Supports: Threshold 8.76 ft/s²; 147 hard-braking events per crash per mile; R² 0.85; penetration 4.7 %; work zones, 2 months.
- Hunter M., Saldivar-Carranza E., Desai J., Mathew J.K., Li H., Bullock D.M. (2021). A Proactive Approach to Evaluating Intersection Safety Using Hard-Braking Data. Journal of Big Data Analytics in Transportation 3. <https://doi.org/10.1007/s42421-021-00039-y> (seen: abstract). Supports: Spearman correlation of hard braking with upstream rear-end crashes at 8 intersections [VERIFY details].
- Sakhare R.S., Bullock D.M. (2026-09-02). Evaluating Connected Vehicle Hard Braking and Acceleration Thresholds for Network-Level Non-Interstate Highway Crash Prediction. Research Square preprint. <https://doi.org/10.21203/rs.3.rs-10555327/v1> (seen: abstract). Supports: Best threshold 0.25 g; ρ = 0.71; doubling the braking rate gives about +25 % crash rate (preprint, not peer reviewed) [VERIFY].
- Sakhare R.S., Desai J., Gartner M., Mukai J., Sturdevant J., Shellhamer R., Ruble J., McCoy M., Bullock D.M. (2025). Connected Vehicle Trajectory Data to Screen Network for Hard-Braking and Hard-Acceleration Events. JTRP report, Purdue/INDOT. <https://doi.org/10.5703/1288284318579> (seen: abstract). Supports: Hard-braking thresholds and computation methods vary across OEMs and vendors; restates the 147:1 work-zone ratio.
- Simons-Morton B.G., Zhang Z., Jackson J.C., Albert P.S. (2012). Do elevated gravitational-force events while driving predict crashes and near crashes? American Journal of Epidemiology 175(10):1075-1079. <https://swov.nl/en/publicatie/do-elevated-gravitational-force-events-while-driving-predict-crashes-and-near-crashes> (seen: secondary). Supports: g-force event rate predicts crashes and near-crashes in novice teens (OR 1.07, AUC 0.76) [VERIFY: search-result summary only].

### F9: Crash-risk-based estimate of a cost per hard brake (my derivation; not an accepted value)
Inputs:
- NHTSA 2023: 37,654 fatal, 1,697,252 injury and 4,403,453 PDO police-reported crashes (6,138,359 in total);
- 3,246,817 million vehicle-miles travelled;
- USDOT 2024 $ crash costs (F1).

Derived (all assumptions mine):
- mean comprehensive cost per police-reported crash about $195,900. About half of it comes from the fatal share;
- about 1.18e-6 crashes per vehicle-km, all roads, so about $0.23 of crash cost per vehicle-km on average;
- Desai's 147 probe hard brakes per crash at 4.7 % penetration means about 3,130 hard brakes across all vehicles per crash. This assumes probe vehicles brake like the rest of traffic, applies to work zones, and assumes a zero-intercept slope;
- average cost per hard brake: about $3.1 counting PDO crashes only, about $63 at the mean crash cost;
- marginal cost per hard brake, scaled by the preprint's elasticity of about 0.32: about $1 to $20.

For scale: at $26.93 per car-hour, $63 equals about 2.3 vehicle-hours of delay, and $1 equals about 2 minutes.

**Fit.** The range spans more than 60×. It depends on:
- the severity mix: rear-end crashes on freeways are mostly PDO or minor injury;
- the threshold;
- the setting: work zones versus open freeway;
- the penetration assumption and causality.

It is not suitable as a central headline weight. At the high end a few hard brakes would dominate the per-vehicle-km cost. Usable only as a bounded sensitivity row, with every assumption disclosed.

**Sources:**
- NHTSA (October 2025). Summary of Motor Vehicle Traffic Crashes: 2023 Data. DOT HS 813 762. <https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813762> (seen: full_text). Supports: 2023 crash counts by severity; VMT 3,246,817 million; fatality rate 1.26 per 100M VMT.
- U.S. DOT (Dec 2025), BCA Guidance Table A-1 (see F1); Desai et al. 2021 (see F8). <https://doi.org/10.1007/s42421-020-00024-x> (seen: full_text). Supports: Inputs to the derivation. The derivation itself is mine and is not published anywhere.

### F10: How time and energy are traded off in traffic-control and eco-driving papers
Zegeye, De Schutter, Hellendoorn, Breunesse & Hegyi (2012), predictive VSL plus ramp-metering controller (author version, full text):
- objective J = α1·TTS/TTS_n + α2·TE + α3·Δ/Δ_n, with emissions and fuel normalised by nominal values. The weights are dimensionless, not monetary;
- cases (α1, α2) = (1, 0), (0, 1), (9, 1);
- with emissions-only weighting, TE fell by more than 58 % but TTS rose by more than 120 %;
- with about 4:6 (RHP) or 2.5:7.5 (cMPC), emissions fell by more than 30 % without hurting TTS.

Jayawardana & Wu (2022), deep-RL eco-driving at signals, ECC (full text):
- piecewise, hand-tuned reward on normalised fuel, speed and stops (μ1 = -100 ... μ11 = -10), found by trial and error;
- the authors state that fuel and travel-time terms compete and are hard to balance. No monetary weights.

Deshpande et al. (2021), arXiv (cost function read):
- stage cost γ·ṁ_f/ṁ_f^norm + (1-γ)·t_s, with γ = 0.4 / 0.7 / 0.82 described as driving aggressiveness;
- savings compared at equal travel time.

Jayawardana et al. (2024/2025), arXiv (abstract only): 11-22 % cut in intersection CO2 'without harming throughput or safety'. How this was enforced: [VERIFY].

Monetary (VoT/fuel-price) weighting is standard in appraisal (BCA) but rare in the control papers I opened. Those use normalised weights tuned by hand or swept along a Pareto front.

**Fit.** This supports V16's choice of a monetised mix with a delay guard. Zegeye et al. show the failure mode V16 guards against: energy weight bought by large TTS increases.

The papers give no transferable weight ratio. Typical practice is a Pareto sweep or normalised weights, so a weight sweep should be reported next to the monetised headline.

**Sources:**
- Zegeye S.K., De Schutter B., Hellendoorn J., Breunesse E.A., Hegyi A. (2012). A predictive traffic controller for sustainable mobility using parameterized control policies. IEEE Trans. ITS 13(3):1420-1429. <https://doi.org/10.1109/TITS.2012.2197202 (author version read: https://www.bartdeschutter.org/publications/12-005-predictive-traffic-controller-sustainable/12-005-predictive-traffic-controller-sustainable.pdf)> (seen: full_text). Supports: Weighted normalised objective (TTS, TE, control variation); weight cases; trade-off numbers in Table I and Fig. 7 text.
- Jayawardana V., Wu C. (2022). Learning Eco-Driving Strategies at Signalized Intersections. European Control Conference 2022; arXiv:2204.12561. <https://arxiv.org/abs/2204.12561> (seen: full_text). Supports: Hand-tuned piecewise reward (Eq. 9, Table III); stated difficulty of balancing fuel against travel time.
- Deshpande S.R., Gupta S., Gupta A., Canova M. et al. (2021). Real-time Eco-Driving Control in Electrified Connected and Autonomous Vehicles using Approximate Dynamic Programming. arXiv:2108.02652. <https://arxiv.org/abs/2108.02652> (seen: full_text). Supports: Stage cost γ·normalised fuel + (1-γ)·time, γ values 0.4/0.7/0.82. Author list beyond the first author and the venue not checked [VERIFY].
- Jayawardana V., Freydt B., Qu A., Hickert C., Sanchez E., Tang C., Taylor M., Leonard B., Wu C. (2024, v2 2025). Mitigating Metropolitan Carbon Emissions with Dynamic Eco-driving at Scale. arXiv:2408.05609. <https://arxiv.org/abs/2408.05609> (seen: abstract). Supports: 11-22 % intersection CO2 cut claimed without harming throughput or safety; formulation not checked [VERIFY].

### F11: Implied weight ratios under the sourced values (my arithmetic)
Central inputs: $26.93 per car-hour (F1) and fuel energy at $0.073-0.093/kWh (F6).
- 1 kWh of fuel energy is worth about 10-12 s of one car's delay.
- At 100 km/h, time costs about $0.27 per vehicle-km. Fuel costs about $0.06 per vehicle-km, assuming an illustrative 7 L/100 km that I did not source.
- Crash cost averages about $0.23 per vehicle-km on all US roads (F9). I did not check freeway-specific rates.
- Electricity at $0.173/kWh at the meter is worth about 23 s of delay per kWh.

**Fit.** Under monetary weights the generalised cost is dominated by delay. Energy savings matter only when delay is nearly unchanged.

This makes V16's goal ('energy cannot be won by slowing traffic') close to automatic. The opposite risk follows: energy may be invisible in the headline. Report energy separately (V10) and add energy-weight sensitivity rows, for example ×1, ×3 and ×10, or a carbon-cost row.

**Sources:**
- Derived from F1, F6 and F9 (no external source for the ratios themselves). <https://www.transportation.gov/sites/dot.gov/files/2025-12/Benefit%20Cost%20Analysis%20Guidance%202026%20Update%20%28Final%29.pdf> (seen: full_text). Supports: Inputs only. The ratios are my calculation.

### Verification: citations and numbers that failed or were corrected

- [F3] **details_wrong**: MnDOT OTSM (Sept 2024), Table A.1 Recommended standard values ... SFY 2025. Correction: The SFY2025 table content is quoted correctly (hash-identical re-download): auto $19.30/$26.00/$31.60, truck $31.50/$39.30/$47.20, SCC $238/t (2023$), VOC auto $0.32 and truck $0.73 at a 'real tax-neutralized' fuel price, fatal $15.9M, minor $380k, possible $180k, PDO $18k. But this table is OUTDATED. MnDOT's Appendix A page (https://www.dot.state.mn.us/planning/program/appendix_a.html) now links 'Recommended standard values ... in SFY2027: Table A.1' (https://edocs-public.dot.state.mn.us/edocs_public/DMResultSet/download?docId=39198859). I read it in full: MnDOT OTSM, August 2026, 'Values (expressed in 2025$)'. Its values: auto VTTS $19.50/$26.20/$31.90 per person-hour; truck driver $32.50/$40.60/$48.70; SCC $256/t (2025$); auto VOC $0.31/mi; truck VOC $0.74/mi; fatal $17.0M; minor injury $400k; possible injury $190k; PDO $19k. The SFY2027 table gives its dollar year (2025$), which settles the [VERIFY] on the dollar year for the current row. The SFY2025 dollar year is still unstated in that table.
- [F4-eurocontrol] **details_wrong**: EUROCONTROL Standard Inputs, passenger value of time chapter. Correction: The current page (it redirects to standard-inputs.netlify.app, release 10.0.2) gives HEATCO EU25 personal €22.89/h and business €55.90/h, 'adjusted from 2002 to 2025 prices based on inflation'. The snippet values (€22.34 / €54.56, 2024 prices) are not on the current page; they come from an older release. These are air-passenger values uprated by inflation only, not by the GDP-per-capita elasticity, so they are not a substitute for the car commute row.
- [F6] **details_wrong**: EIA Energy Explained: British thermal units; DOE AFDC Fuel Properties Comparison. Correction: The numbers are confirmed: 1 kWh = 3,412 Btu, gasoline 120,214 Btu/gal, diesel 137,381 Btu/gal; AFDC LHV gasoline/E10 112,114-116,090 and diesel 128,488 Btu/gal. But the EIA page I fetched does not label these as higher heating values and does not mention '2023 end-use, MER Aug 2024'. It only points to MER Appendix A. The HHV label is plausible (EIA uses gross heat content) but is not supported by the cited page [VERIFY in MER App. A]. The conversions recompute correctly (to rounding).
- [F8-JTRP2025] **details_wrong**: Sakhare R.S., Desai J., Gartner M., Mukai J., Sturdevant J., Shellhamer R., Ruble J., McCoy M., Bullock D.M. (2025), JTRP, doi:10.5703/1288284318579. Correction: Five co-author initials are wrong. Crossref and the Purdue e-Pubs page give Christopher Gartner, Justin Mukai, Nathan Sturdevant, Nathaniel (Crossref) / Nathan (e-Pubs) Shellhamer, Taylor Ruble and Daniel (Dan) McCoy, so the citation should read Gartner C., Sturdevant N., Shellhamer N., Ruble T., McCoy D. The claims are confirmed in the abstract: thresholds and computation techniques differ across automotive companies and third-party vendors, and 'approximately 147 hard braking events in a work zone for every crash' (attributed to a previous study).
- [F10-Deshpande] **details_wrong**: Deshpande S.R., Gupta S., Gupta A., Canova M. (2021), arXiv:2108.02652. Correction: There are exactly four authors, so drop 'et al.'. The arXiv comment says it was submitted to an ASME journal (under review); I did not check the final venue. The stage cost γ·(normalised fuel) + (1-γ)·t is confirmed, but the γ values shown are 0.4, 0.7, 0.75 and 0.82: 0.75 is omitted. The setting is a 48 V mild-hybrid, not a general electrified CAV.
- [F3] **outdated**: MnDOT SFY2025 auto $19.30/$26.00/$31.60, truck $31.50/$39.30/$47.20, SCC $238/t (2023$), PDO $18k, fatal $15.9M. Correction: Superseded by MnDOT SFY2027 Table A.1 (Aug 2026, 2025$): auto $19.50/$26.20/$31.90; truck $32.50/$40.60/$48.70; SCC $256/t (2025$); fatal $17.0M; minor $400k; possible $190k; PDO $19k; auto VOC $0.31/mi; truck VOC $0.74/mi.
- [F3] **outdated**: MnDOT auto about 29 % above USDOT personal. Correction: With SFY2027: 26.20/20.10 = +30 %. The dollar years differ (2025$ vs 2024$).
- [F4] **outdated**: EUROCONTROL €22.34 personal / €54.56 business (2024). Correction: The current release (10.0.2) gives €22.89 / €55.90 at 2025 prices (inflation-uprated HEATCO EU25 values).
- [F10] **wrong**: Deshpande γ = 0.4 / 0.7 / 0.82. Correction: The set shown is 0.4, 0.7, 0.75, 0.82.

Verified as stated: 41 citations and numbers.

### Open questions
- Dollar year and price period: 2024 $ with 2025 annual EIA prices as central, and 2026 prices as a high row? 2026 fuel prices are volatile: diesel was $6.29/gal in Sep 2026.
- Resource cost (excluding taxes, appraisal practice) or perceived cost (including taxes) for the headline energy price? Energy basis: HHV or LHV, and fuel energy or electricity at the meter versus at the battery (charging efficiency not sourced)?
- Hard braking: headline guard/constraint (recommended), or a priced penalty with sensitivity bounds? If priced, should V11's threshold be moved to about 2.5-2.7 m/s² so it matches the crash-surrogate literature? Note that only CAV hard brakes are measured (V11), while the crash evidence covers all probe vehicles.
- Trucks: does the F3Z mix include trucks? If so, use the USDOT truck-driver VTTS ($37.20/veh-h, driver only, no cargo), or add a freight cargo value such as HEATCO €2.98/tonne-h [VERIFY]?
- Occupancy: use USDOT weekday peak 1.34 (06:00-08:59 window), or a MnDOT/Twin Cities corridor value? The guidance prefers local data, and I did not find a source for it.
- Add an emissions or carbon row, given USDOT stopped monetising CO2 (Dec 2025) while MnDOT SFY2025 still uses $238/t (2023 $)?
- EU sensitivity row: uprate HEATCO (needs HICP and GDP/capita indices, not sourced here), or use a current national guide (UK TAG Data Book v2.01, May 2025; German BVWP; Dutch KiM), none of which I opened [VERIFY]?
- Check whether MnDOT has published SFY2026 standard values, and confirm the dollar year of the SFY2025 VTTS rows.


## Rule-based CAV comparators

### Recommendation (researcher)
Implement and tune three rule-based comparators under the SAME interface as the DRL: per-CAV target ±5 km/h at most once per 2 s, with SUMO car-following as the safety cap. The best tuned one on validation is the D5.8 "best tuned proven controller". Report all three per regime.

1. **PI with saturation (Stern et al. 2018), re-parametrised for 120 km/h.**
   - Gap thresholds become time gaps; tune the window, v_catch and gamma on seeds 7,400,100-299.
   - Why "proven": a peer-reviewed field experiment, with 1 AV in 22 vehicles cutting speed sd by 54.7 %, fuel by about 28 % and braking by 74 % (TR-C 2018, Table 3). It is the canonical CAV wave-damping baseline and needs only local sensing, so it is the information-fair rule.
   - Warning: the archived port with the ring constants gave +119 to +180 % delay on the LD3 freeway. Using it untuned would be a weak-baseline violation.
2. **The Hayat et al. explicit controller (the CIRCLES MicroAccel family): min(a_safe, a_target, a_MPC).**
   - Local mode, plus a planning mode that takes v_down from the zone messages through the CIRCLES uniform-kernel speed planner (window w).
   - Why "proven": the only rule found that was field-tested on an open multilane freeway in dense mixed traffic (I-24, Nov 2022; -52 % speed variance within 400 m behind the AV, arXiv 2310.18151 / IEEE CSM 2025). It is also part of the largest CAV field test to date.
   - Its parameters are unpublished, so we tune them.
3. **CAV speed harmonisation upstream of each merge (Ma, Ghiasi et al.; FHWA-HRT-21-008 linear transition; Ghiasi et al. TR-C 2019).**
   - CAVs ramp their target linearly from their own speed to the prevailing downstream bottleneck speed over a zone of about 1-1.5 km, with a slow-leader local rule.
   - Why "proven": it is the US DOT/FHWA speed-harmonisation application, peer-reviewed and field-trialled in managed lanes (field results [VERIFY]). It is the only candidate aimed at merge bottlenecks and capacity drop, which ring smoothers do not address.

Optional reported rows (not the bar):
- FollowerStopper with U = the zone planner speed (cheap, since it is already in the archive);
- JAD (He et al. 2017), which has no field test, depends on prediction and is effective only when inflow < capacity;
- drop the per-CAV MPC arm and disclose it, under the D5.8 allowance.

Fairness rules to pre-register:
- comparators get the same observations as the DRL (own speed, leader gap and speed, zone messages) and the same tuning budget;
- the native-rate (0.1 s, unquantised) versions are reported only as a sensitivity row.

Before any of this, fix the CAV base car-following model and step length (F8), because a CACC artefact would bias every arm.

### Verifier verdict on the recommendation
Sound: **True**. Mostly sound. Three tuned rule comparators, all reported per regime and with the best one on validation as the D5.8 bar, follows from verified evidence and from V19. The MPC drop with disclosure is explicitly allowed in v5b1 CLAUDE.md:54 ('Under D5.8 the MPC arm is optional; dropping it must be disclosed').

Weaknesses to fix before pre-registration:

(1) Comparator 3's 'proven' rationale conflates two algorithms. FHWA-HRT-21-008 uses a heuristic linear transition 'building on Ma et al. (2017)' and points to Ghiasi et al. 2017 for the more advanced trajectory method. Ghiasi et al. 2019 (TR-C) is a different, more elaborate algorithm, read only as an abstract. The FHWA report is not peer-reviewed. The -12/-19 % delay gains are from a managed lane, bundled with CACC and cooperative merge, mostly at 70-100 % penetration. The noncoop rows (-6 % to -42 %) were omitted. Eq. 12 is unread. So 'peer-reviewed, field-trialled' overstates what was verified. Say 'FHWA-simulated, phase-1 field-tested (results unread)'.

(2) 'Hayat is the only rule field-tested on an open multilane freeway' is contradicted in part by the FHWA foreword (phase 1 field-tested speed harmonisation). 'Largest CAV field test to date' is the CIRCLES authors' own claim and should be attributed, not asserted.

(3) Hayat's Eq. 14 as printed is not a clip (max of max), so implement the text's intended clip and disclose it. Its parameters are unpublished, so 'tuned' is the only honest version.

(4) Weak-baseline risk. Holding comparators to the ±5 km/h-per-2-s interface while reporting native-rate versions 'only as a sensitivity row' could cripple acceleration-based laws (Hayat, FollowerStopper). That conflicts with 'no weak baselines' unless the interface is pre-registered as the deployment actuator for all arms. If a native-rate rule beats the quantised one on validation, the protocol must say in advance which one is the bar. The toy check only shows the quantiser does not destroy smoothing in one deterministic case.

(5) PI with saturation was field-proven at about 4.5 % penetration on a 7 m/s ring. Its 50 % penetration, 120 km/h, merge-bottleneck behaviour is unknown. It is canonical but not 'proven' for this plant.

(6) Wang et al. 2016 relies on VSL gantries, so it does not fit V15 as a CAV-only comparator.

The F8 point (fix the CAV base model and step length first) is well supported by the archive (round3_tm21_protocol.md).

### Local checks
1. **Archive check** (read-only git show and git grep on claude/v5b-core):
   - Found FollowerStopper and PI with saturation (vsl_lab/plants/ring.py, vsl_lab/controllers/pi_saturation.py), the CAV set-speed staircase (vsl_lab/controllers/cav_staircase.py), and the mrg3_run arms cavpi and cavconst.
   - Ring results: NC 85.2 %, best fixed FollowerStopper 88.8 %, tuned PI 100.2 % of v_e (docs/lab/t3_ring_r1_r2.md).
   - LD3 freeway: cavpi (ring constants, 25 % CACC) gave +180 % / +119 % delay vs its NC; NC with 25 % CACC gave +93 % / +45.7 % vs human-only (docs/lab/round4_th.md).
2. **One tiny SUMO 1.27.1 run** (libsumo, v5b1 venv, single lane, 0.1 s step, 900 s; script /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5/510dd91c-1bff-427e-90a7-d763e29122b9/scratchpad/lit/test/quant_check.py).
   - Setup: a scripted leader at 20 ± 10 m/s with a 60 s period, then one CAV, then 6 IDM humans. It checks that the ±5 km/h-per-2-s quantiser keeps a rule's smoothing.
   - Speed sd of the last human:
     - CAV as IDM (no control): 6.02 m/s;
     - PI with saturation, native: 3.35;
     - PI with saturation, quantised: 2.92;
     - FollowerStopper (informed U = 20), native: 0.03;
     - FollowerStopper, quantised: 0.61.
   - No collisions, and no CAV deceleration over 3 m/s². CAV minimum gap 10-51 m.
   - This is an interface sanity check only (one deterministic toy, informed U, scripted leader), not evidence about F3Z.

### F1: FollowerStopper and PI with saturation (Stern et al. 2018, Arizona ring field experiment)
Read in full (arXiv 1705.01693, the TR-C 89:205-221 version).

Control laws (Sec. 3):
- FollowerStopper: v_cmd = U when it is safe. Otherwise v_cmd blends toward min(v_lead, U) or 0 across three parabolic gap boundaries, dx_k = dx0_k + (dv-)^2/(2 d_k), with dx0 = 4.5/5.25/6.0 m and d = 1.5/1.0/0.5 m/s^2. U is an external desired speed, 'selected based on observation'.
- PI with saturation: U = the mean of the AV's own speed over m samples (38 s, about one lap). v_target = U + v_catch * clip((gap - g_l)/(g_u - g_l), 0, 1), with g_l 7 m, g_u 30 m, v_catch 1 m/s. Then v_cmd(j+1) = beta(alpha v_target + (1 - alpha) v_lead) + (1 - beta) v_cmd(j), with alpha = clip((gap - dx_s)/gamma, 0, 1), gamma 2 m, dx_s = max(2 s * dv, 4 m) and beta = 1 - alpha/2.
- The parameters were set in simulation and pre-tests for the ring.

Sensing: own speed and gap at 30 Hz; the leader speed is estimated from d(gap)/dt. There is no V2V and no downstream information. The low-level PID has a 20 Hz loop.

Setting: single-lane ring, 260 m, 21-22 vehicles with 1 AV (about 4.5-4.8 %), speeds about 6-8 m/s.

Table 3, wave interval vs best control interval:
- Exp A (FollowerStopper, U set by hand): speed sd 3.31 -> 0.64 m/s (-80.8 %); fuel 24.6 -> 14.1 l/100 km (-42.5 %); braking 8.58 -> 0.12 events/veh/km; throughput 1827 -> 2085 veh/h (+14.1 %).
- Exp B (trained human driver): speed sd -49.5 %; fuel -22.1 %; throughput +9.8 %.
- Exp C (PI with saturation): speed sd 3.85 -> 1.74 m/s (-54.7 %); fuel 29.0 -> 20.9 l/100 km (the text says -27.9 %, Table 3 says -28.1 %); braking -74.4 %; throughput -2.5 %.
- The comparison is before and after within one run, not randomised.

**Fit.** Strongest 'proven' credential: peer-reviewed, field-tested and widely reproduced. Weak fit to F3Z as published:
- It is single-lane ring work at about 7 m/s.
- The gap constants are absolute metres (g_u = 30 m is under a 1-s headway at 120 km/h).
- FollowerStopper needs an external U.
- Neither law addresses merge bottlenecks or capacity drop.

Archive (local, claude/v5b-core):
- Both are already implemented: vsl_lab/plants/ring.py and vsl_lab/controllers/pi_saturation.py (a dt-aware port).
- On the ring, tuned PI with saturation reached 100.2 % of the IDM equilibrium speed and the best fixed FollowerStopper U reached 88.8 % (docs/lab/t3_ring_r1_r2.md).
- On the LD3 freeway lane drop, arm `cavpi` (ring constants, every CAV at 25 % CACC) gave +180 % / +119 % delay vs its NC (docs/lab/round4_th.md). The paper constants are therefore a WEAK baseline at freeway speed.

Mapping to ±5 km/h per 2 s:
- compute v_cmd at the simulation step;
- every 2 s, move the CAV's target one 5 km/h step toward v_cmd when |v_cmd - target| >= 2.5 km/h;
- apply it with setSpeed while SUMO's car-following safe speed still caps it (the V5 speed-mode finding).

Tunables to re-parametrise and tune:
- PI with saturation: window, v_catch, g_l/g_u as time gaps (e.g. g = T·v), gamma, and the 2-s rule factor;
- FollowerStopper: U (from the zone downstream speed) and the dx0/d sets.

**Sources:**
- Stern R.E., Cui S., Delle Monache M.L., Bhadani R., Bunting M., Churchill M., Hamilton N., Haulcy R., Pohlmann H., Wu F., Piccoli B., Seibold B., Sprinkle J., Work D.B. (2018). Dissipation of stop-and-go waves via control of autonomous vehicles: Field experiments. Transportation Research Part C 89:205-221. arXiv 1705.01693 (submitted 4 May 2017). <https://arxiv.org/pdf/1705.01693 (DOI 10.1016/j.trc.2018.02.005)> (seen: full_text). Supports: The control laws and constants (Sec. 3.1-3.3), the ring setup (260 m, 21-22 vehicles), and the Table 3 results quoted above
- Archive: vsl_lab/plants/ring.py, vsl_lab/controllers/pi_saturation.py, docs/lab/t3_ring_r1_r2.md, docs/lab/round4_th.md (branch claude/v5b-core, repo phd_speed_harmo_v5). <git -C /srv/shared/Workspace/phd/phd_speed_harmo_v5 show claude/v5b-core:docs/lab/round4_th.md> (seen: local_test). Supports: Existing implementations; the ring tuning results; the untuned cavpi freeway result of +119/+180 % delay

### F2: Hayat et al. explicit local controller (CIRCLES 'MicroAccel' family; single-AV I-24 field test, Nov 2022)
Read in full (arXiv 2310.18151 v1).

Control law: a_cmd = min(a_safe, a_target, a_MPC).
- a_safe = -k(v - v_safe) + dv_safe/dt, where v_safe comes from the gap, s0 and the braking limits of ego and leader.
- a_target = -k(v - v_target).
- Local mode: v_target = the leader's mean speed over the last tau s, plus a catch-up term c1·max(0, c2(h - delta1·v))/max(1, v)^2 (Eq. 12 as printed). tau approximates the wave period.
- Planning mode: v_target = the downstream speed-planner value, clipped to [alpha0·v_lead, min(alpha1·v_lead, v_ref)] (Eq. 14).
- a_MPC anticipates leader braking (Eqs. 15-19).
- Numerical parameter values are NOT given; they are deferred to ref [27], a preprint.

Sensing: own speed, gap, leader speed and leader acceleration; optionally the downstream target speed sent over cellular.

Setting: one Toyota RAV4 in dense peak traffic on 4-lane westbound I-24 (Nashville), within the 100-vehicle MegaVanderTest; the expected penetration was 1-3 %.

Result (one run, AV in front vs behind):
- speed variance in front of the AV 19.6 m^2/s^2, behind it 9.4 m^2/s^2 (-52 %, vehicles within 400 m);
- Table 1: -52 % to -74 % within 200-600 m behind, fading to about +5 % at 1400 m;
- no energy or travel-time number.

Journal version: IEEE Control Systems Magazine 45(1):95-110, 2025, DOI 10.1109/MCS.2024.3503402 (from search metadata, not opened).

**Fit.** The best 'proven at freeway speed in open, multilane, mixed traffic' rule found. It is explicit (no learning), and its planning mode matches F3Z's zones exchanging downstream state.

Caveats:
- the evidence is one vehicle and one field run, with a before/behind comparison;
- the parameters are unpublished in this paper, so we must tune them ourselves (an advantage for 'tuned');
- it is acceleration-based.

Mapping: compute a_cmd every step, form v_cmd = v + a_cmd·2 s, then quantise to ±5 km/h per 2 s as in F1. Keep SUMO's safe-speed cap so that a_safe and the fast braking are not lost to quantisation; disclose this.

Tunables: k, s0, c1, c2, delta1, tau, alpha0, alpha1, v_ref (and k2).

**Sources:**
- Hayat A., Alanqary A., Bhadani R., Denaro C., Weightman R.J., Xiang S., Lee J.W., Bunting M., Gollakota A., Nice M.W., Gloudemans D., Zachár G., Davis J.F., Delle Monache M.L., Seibold B., Bayen A.M., Sprinkle J., Work D.B., Piccoli B. (2023). Traffic smoothing using explicit local controllers. arXiv 2310.18151 v1 (27 Oct 2023). <https://arxiv.org/pdf/2310.18151> (seen: full_text). Supports: The control law (Eqs. 8-19), sensing, the I-24 setting and the -52 % speed variance result (Sec. 5.2, Table 1); that the parameter values are not given
- Journal version: IEEE Control Systems Magazine 45(1):95-110 (2025), DOI 10.1109/MCS.2024.3503402 [VERIFY]. <https://its.berkeley.edu/publications/traffic-smoothing-using-explicit-local-controllers-experimental-evidence-dissipating-0> (seen: secondary). Supports: The journal venue, volume and pages (from a search summary only)

### F3: CIRCLES MegaController (Speed Planner + vehicle controller), 100-vehicle I-24 test, Nov 2022
Read in full (arXiv 2402.17043 v1 PDF; IEEE CSM DOI 10.1109/mcs.2024.3498552 from search metadata).

Architecture: a central Speed Planner over LTE, plus a per-vehicle controller that overrides the stock ACC.
- Speed Planner: fuses INRIX (about 60 s updates, about 180 s latency) with 1 Hz AV pings. It then applies a uniform-kernel average of the downstream speed over a window w (Eq. 17; w is the only tuning parameter), plus an optional RL 'buffer'.
- Vehicle-controller candidates in pre-deployment simulation (Sec. 3, Fig. 8; numbers only in a colour figure):
  - 'Simple', a hand-designed logic controller that largely follows the planner;
  - 'MicroAccel' (the explicit controller of F2, 6 variants);
  - RL (5 variants).
- The HybridRL controller with the kernel-smooth + RL-buffer planner was chosen. 97 of 100 vehicles ran the ACC-based RL controller in the final test (Sec. 7.4.3).

Field results in this paper:
- controller engagement 38 % (16 Nov) and 78 % (17 Nov);
- a qualitative fuel heat map;
- no quantified energy, speed-variance or travel-time result;
- the penetration estimate is deferred to another article.

The BAIR blog (25 Mar 2025, Lichtlé et al.) reports a field 'trend of roughly 15-20 % energy savings around the controlled cars' and up to 20 % in simulation with < 5 % AVs. That is the RL controller, not a rule.

**Fit.** The deployed controller was learned (RL), so it is NOT a rule comparator. The usable rule parts:
- the kernel-smooth speed planner (downstream mean speed over a window w), which maps naturally onto zone-to-zone messages;
- the 'Simple' planner-following logic, whose law is not specified in the text I read.

To build a planner + local-rule comparator (planner target -> F2 planning mode, or -> FollowerStopper U), use the planner from this paper. 'Proven' only in the sense of a field-deployed architecture; no peer-reviewed field energy number for the rule parts was found.

**Sources:**
- Lee J.W., Wang H., Jang K., Hayat A., Bunting M., et al., Bayen A.M. (2024/2025). Traffic Control via Connected and Automated Vehicles (CAVs): An Open-Road Field Experiment with 100 CAVs. arXiv 2402.17043 v1 (26 Feb 2024); IEEE Control Systems Magazine, DOI 10.1109/mcs.2024.3498552 [VERIFY volume/pages]. <https://arxiv.org/pdf/2402.17043v1> (seen: full_text). Supports: The architecture, kernel planner Eq. 17, candidate controllers (Simple/MicroAccel/RL), 97/100 on ACC-based RL, engagement 38 %/78 %, no quantified field energy result
- Lichtlé N., Jang K., Vinitsky E., Shah A., Lee J.W., Bayen A.M. (2025-03-25). Scaling Up Reinforcement Learning for Traffic Smoothing: A 100-AV Highway Deployment. BAIR blog. <https://bair.berkeley.edu/blog/2025/03/25/rl-av-smoothing/> (seen: full_text). Supports: The 15-20 % field energy-saving trend and up to 20 % in simulation; RL outputs ACC set speed/gap from local observations (blog, not peer-reviewed)

### F4: CAV trajectory-based speed harmonisation upstream of a merge bottleneck (Ma, Ghiasi et al.; FHWA)
FHWA-HRT-21-008 (March 2021; Ma, Leslie, Ghiasi, Guo, Sethi, Hale, Shladover, Lu, Huang), read in the relevant chapters.

Rule (pp. 41-42), heuristic and building on Ma et al. 2017:
- Virtual detectors along the speed-harmonisation zone average speed over 5 min.
- Global command: a linear speed transition from the CAV's current speed to the prevailing merge-area speed, over the distance to the zone boundary (Eq. 12 with v_cur, v_pre, D_cur, L_seg). The equation is an image I could not extract: [VERIFY its exact form].
- Local command: if the front vehicle is predicted to be slow, apply the same linear transition toward it.
- If the gap is < 50 m and dv < 5 m/s, slow down linearly.
- The best zone length was 1,500 m upstream of the merge.

Results (simulation, managed lane, bundled with CACC and cooperative merge; Table 4): adding speed harmonisation changed the average delay vs the bundle without it by:
- -12.86 % at 100 % market penetration (coop merge);
- -11.87 % at 70 %;
- -19.23 % at 30 %.
The report also quotes earlier I2V harmonisation studies: -10 % corridor-wide travel time and -35 % on bottleneck segments at >= 10 % CAV penetration (Talebpour et al. 2013, cited there).

Ghiasi, Li & Ma (2019), TR-C 104:210-233, abstract only: CAVs 'smoothly hedge against the backward deceleration waves' in mixed HV/CV/CAV traffic; 'significant improvements' in oscillation and fuel; no numbers in the abstract.

**Fit.** This is the most direct rule analogue of the v5.B.1 task:
- CAVs only;
- zone-length (about 1-1.5 km) speed transitions toward the downstream bottleneck speed;
- it targets merge bottlenecks, which the ring smoothers (F1) do not.

It needs a downstream prevailing speed, which the F3Z zone messages or detectors provide.

Mapping: the linear target speed vs distance is evaluated every 2 s and quantised to ±5 km/h; safety stays with SUMO car-following.

Tunables: SH zone length, detector averaging window (5 min in FHWA, probably too slow for waves), slow-front threshold, 50 m / 5 m/s local trigger.

'Proven': FHWA phase 1 field-tested speed harmonisation and phase 2 ran a limited managed-lane field study [VERIFY: I did not read the field-test chapters]. Peer-reviewed in TR-C 2019 [abstract only].

**Sources:**
- Ma J., Leslie E., Ghiasi A., Guo Y., Sethi S., Hale D., Shladover S., Lu X.-Y., Huang Z. (March 2021). Applying Bundled Speed-Harmonization, Cooperative Adaptive Cruise Control, and Cooperative-Merge Applications to Managed-Lane Facilities. FHWA-HRT-21-008. <https://www.fhwa.dot.gov/publications/research/operations/21008/21008.pdf> (seen: full_text). Supports: The speed-harmonisation rule description (pp. 40-42), the 1,500 m zone, Tables 2-4 delay/throughput numbers, the Talebpour et al. 2013 citation
- Ghiasi A., Li X., Ma J. (2019). A mixed traffic speed harmonization model with connected autonomous vehicles. Transportation Research Part C 104:210-233. <https://doi.org/10.1016/j.trc.2019.05.005> (seen: abstract). Supports: CAV trajectory smoothing against backward deceleration waves in mixed traffic; qualitative improvements (abstract via Semantic Scholar API) [VERIFY numbers]
- Ma J., Li X., Shladover S., Rakha H., Lu X.-Y., Jagannathan R., Dailey D. (2016). Freeway Speed Harmonization. IEEE Transactions on Intelligent Vehicles 1(1):78-89. <https://trid.trb.org/View/1423754> (seen: abstract). Supports: A review of VSL/CV/AV speed harmonisation and its experiments [VERIFY]

### F5: Jam-absorption driving (JAD): Nishi et al. 2013; He et al. 2017; later works
Nishi, Tomoeda, Shimura & Nishinari (2013), TR-B 50:116-129, DOI 10.1016/j.trb.2013.02.003 (abstract via RePEc):
- one vehicle does a 'slow-in' (decelerates early and opens a larger gap before the jam reaches it), then a 'fast-out';
- conditions on timing and speed so that compression and expansion waves cancel without secondary jams;
- minimal car-following model; theory only.

He, Zheng, Song & Zhu (2017), IEEE T-ITS 18(4):802-813, DOI 10.1109/TITS.2016.2587699 (abstract via TRID):
- Newell-based estimate of the JAD endpoint and choice of the absorbing vehicle given a desired absorbing speed;
- simulation only; prevented propagation and capacity drop in a single-oscillation scenario.

Review by He, Laval, Han, Hegyi, Nishi & Wu (arXiv 2504.11372 v2, May 2025; IEEE T-ITS 2026 per arXiv), read through a summarising fetch:
- JAD 'has not yet undergone any field testing';
- it needs wave-propagation prediction;
- the JAD speed is usually exogenous;
- secondary waves are 'unresolved';
- Nishi 2013 finds it effective 'only when the inflow is lower than the capacity';
- later variants move to platoons, optimal control or MPC (Han et al. 2021; Li, Yanagisawa & Nishinari 2024 TR-C 158; Liu et al. 2025 T-ITS).

**Fit.** Conceptually ideal for single-CAV action without infrastructure, but NOT 'proven':
- no field test;
- it needs a downstream wave detector or predictor (the zones could supply one).

Mapping: when a downstream wave is detected, the selected CAV ramps its target down to the JAD speed in 5 km/h steps (several hundred metres of execution distance per He 2017), holds it, then releases.

Tunables: JAD speed, activation rule, vehicle selection.

Recommend it as an optional reported row, not as the 'best proven' bar.

**Sources:**
- Nishi R., Tomoeda A., Shimura K., Nishinari K. (2013). Theory of jam-absorption driving. Transportation Research Part B 50:116-129. <https://ideas.repec.org/a/eee/transb/v50y2013icp116-129.html> (seen: abstract). Supports: The slow-in/fast-out concept and the no-secondary-jam conditions
- He Z., Zheng L., Song L., Zhu N. (2017). A Jam-Absorption Driving Strategy for Mitigating Traffic Oscillations. IEEE Transactions on Intelligent Transportation Systems 18(4):802-813. <https://trid.trb.org/View/1463343> (seen: abstract). Supports: Newell-based JAD and vehicle selection; simulation-only evidence
- He Z., Laval J., Han Y., Hegyi A., Nishi R., Wu C. (2025). A Review of Stop-and-Go Traffic Wave Suppression Strategies: Variable Speed Limit vs. Jam-Absorption Driving. arXiv 2504.11372 v2; IEEE T-ITS 2026 (journal ref as listed on arXiv) [VERIFY]. <https://arxiv.org/html/2504.11372v2> (seen: secondary). Supports: No JAD field test; reliance on prediction; secondary-wave and inflow < capacity limitations; list of later JAD works (read via a summarising fetch of the first 100k characters, not verbatim)

### F6: CAVs as coordinated moving bottlenecks (Čičić & Johansson 2019)
Read in full (CDC 2019, Nice, pp. around 3149).

Method (multi-class CTM): controlled CAVs are first collected into an area, then they drive as a moving bottleneck (U_p 60 km/h, U_min 50 km/h, covering a third of the lanes) to dissipate a wave. It is feedforward on the average density between the bottleneck and the wave.

Setting: 50 km freeway with no ramps; the wave is induced by a 2-min closure; 100 runs.

Result (Table I): mean TTT increase vs the wave-free base case
- 6.6 % with 0 % CAVs;
- 4.51 % at 3 %;
- 3.99 % at 5 %;
- 3.58 % at 10 % (exact density; medians 6.49/4.04/3.64/3.32 %).
The approximate-density version is slightly worse.

**Fit.** Macroscopic and simulation-only, so not 'proven'. It needs density estimates between the CAV group and the wave (zone messages could provide them). It is a useful design idea for a coordinated-zone rule; with a ±5 km/h-per-2-s interface it maps as a 60 km/h cap ramp on the CAVs of one zone. Optional at most.

**Sources:**
- Čičić M., Johansson K.H. (2019). Stop-and-go wave dissipation using accumulated controlled moving bottlenecks in multi-class CTM framework. 58th IEEE Conference on Decision and Control (CDC), Nice. <https://people.kth.se/~kallej/papers/transport_cdc19cicic.pdf> (seen: full_text). Supports: The control idea, its parameters, the 50 km CTM setting and the Table I TTT numbers

### F7: Connected-vehicle VSL / speed advisory delivered only to vehicles (Han, Chen & Ahn 2017; Wang et al. 2016; Yang & Jin 2014)
Han, Chen & Ahn (2017), TR-B 98:113-134, DOI 10.1016/j.trb.2016.12.013 (abstract via search summary):
- VSL at fixed bottlenecks actuated by connected vehicles, in three strategies (one CV per lane; CV + VMS; multiple CVs), with adaptive schemes and a failure probability;
- it builds on Chen, Ahn & Hegyi (2014, TR-B 70:340-358);
- no numbers seen.

Wang, Daamen, Hoogendoorn & van Arem (2016), J. Intelligent Transportation Systems 20:559-572, DOI 10.1080/15472450.2016.1157022 (secondary, US DOT ITS summary): VSL commands used as parameters of the onboard car-following controller; lower TTS and fuel in simulation.

Yang & Jin (2014), TR-C 41:48-60, DOI 10.1016/j.trc.2014.01.016 (secondary): IVC-based green-driving advisory speed limit to smooth followers; a related TRB 2014 field test reports up to 30 % fuel/CO2 in stop-and-go [VERIFY, different study].

**Fit.** Rule-based and analytical (kinematic wave). Han et al. 2017 fits 'no gantries, CVs as actuators' at fixed bottlenecks, close to F3Z's merges.

Not field-tested as far as I saw, and not read in full; marked [VERIFY]. They are candidates for a fourth row if F4's rule proves too ad hoc.

Mapping: the segment control speed becomes the CAV target in that segment, quantised to 5 km/h steps.

**Sources:**
- Han Y., Chen D., Ahn S. (2017). Variable speed limit control at fixed freeway bottlenecks using connected vehicles. Transportation Research Part B 98:113-134. <https://ideas.repec.org/a/eee/transb/v98y2017icp113-134.html> (seen: secondary). Supports: CV-actuated VSL strategies at fixed bottlenecks (search summary of the abstract) [VERIFY]
- Wang M., Daamen W., Hoogendoorn S.P., van Arem B. (2016). Connected variable speed limits control and car-following control with vehicle-infrastructure communication to resolve stop-and-go waves. Journal of Intelligent Transportation Systems 20:559-572 (venue/pages from Crossref). <https://www.itskrs.its.dot.gov/2016-b01087> (seen: secondary). Supports: The concept and qualitative TTS/fuel benefits [VERIFY]
- Yang H., Jin W.-L. (2014). A control theoretic formulation of green driving strategies based on inter-vehicle communications. Transportation Research Part C 41:48-60. <https://its.uci.edu/research_products/published-journal-article-a-control-theoretic-formulation-of-green-driving-strategies-based-on-inter-vehicle-communications> (seen: secondary). Supports: Advisory speed limit via IVC to smooth followers [VERIFY]

### F8: ACC/CACC string-stable designs (SUMO ACC/CACC from Milanés & Shladover 2014; Xiao et al.)
The SUMO CACC docs page (last edited 13 Feb 2026):
- cites Milanés & Shladover 2014 (TR-C 48:285-300, DOI 10.1016/j.trc.2014.09.001), Xiao, Wang & van Arem 2017 (TRR 2623), Xiao et al. 2018 (TR-C 96) and Porfyri et al. 2018;
- modes: speed control (no leader, or time gap > 2 s), gap control, gap-closing (< 1.5 s, with hysteresis to 2 s), and collision avoidance (TransAID);
- it warns of collisions at a 1 s step length.

Archive: NC with 25 % CACC on LD3 was +93.0 % / +45.7 % delay vs human-only (docs/lab/round4_th.md). The archive notes say emergency brakings at 0.5 s (23-79 per run) fell to 8-9 at 0.2/0.1 s; whether this is a SUMO artefact was not tested.

**Fit.** These are not smoothing comparators. They define the CAV's own longitudinal model, so they shape the NC row (V4) and every arm, because commands sit on top of them.

Choose the CAV base model and step length before the comparators: a CACC artefact would inflate every CAV gain.

NC = CAVs on their base ACC/CACC at the network maximum with no command.

**Sources:**
- SUMO documentation, Car-Following-Models/CACC (page last edited 13 Feb 2026). <https://sumo.dlr.de/docs/Car-Following-Models/CACC.html> (seen: docs_page). Supports: The source papers, mode-switching thresholds, the collision warning at 1 s steps
- Milanés V., Shladover S.E. (2014). Modeling cooperative and autonomous adaptive cruise control dynamic responses using experimental data. Transportation Research Part C 48:285-300. <https://doi.org/10.1016/j.trc.2014.09.001> (seen: secondary). Supports: The origin of SUMO's ACC/CACC (metadata via the SUMO docs and Semantic Scholar only)
- Archive notes: docs/review/design_space/notes_vehicles.md and docs/lab/round4_th.md (claude/v5b-core). <git -C /srv/shared/Workspace/phd/phd_speed_harmo_v5 show claude/v5b-core:docs/review/design_space/notes_vehicles.md> (seen: local_test). Supports: The +93 %/+45.7 % NC-with-CACC delay; step-length emergency-braking counts

### F9: Model-based / data-driven predictive CAV control (optional MPC comparator)
DeeP-LCC (Wang J., Zheng Y., Li K., Xu Q.; arXiv 2203.10639), seen only as a search-result summary: data-driven receding-horizon control of CAVs in mixed traffic via Willems' fundamental lemma, with safety constraints. The earlier version (arXiv 2110.10097) reports up to 24.96 % fuel saving in a braking scenario [VERIFY].

The a_MPC term of F2 already holds the anticipation part of a model-based CAV law.

The JAD-MPC variants (Liu et al. 2025 T-ITS; Han et al. 2021) appear in the F5 review.

**Fit.** Optional. CLAUDE.md lists an MPC with a model fitted on separate seeds in 'best non-learning', and D5.8 allows dropping it with disclosure. A per-CAV MPC at about 50 % penetration in SUMO is costly and was not field-proven at freeway scale in what I saw. Suggest dropping it and disclosing, or using F2's a_MPC as the model-based element.

**Sources:**
- Wang J., Zheng Y., Li K., Xu Q. DeeP-LCC: Data-EnablEd Predictive Leading Cruise Control in Mixed Traffic Flow. arXiv 2203.10639 [VERIFY venue]. <https://arxiv.org/abs/2203.10639v1> (seen: secondary). Supports: The method idea; fuel number from the earlier preprint per the search summary [VERIFY]

### F10: Archive implementations already available (claude/v5b-core)
Implemented and reusable as ports:
- vsl_lab/plants/ring.py: FollowerStopper and PISaturation at 0.1 s, equations checked against Stern et al.;
- vsl_lab/controllers/pi_saturation.py: a dt-aware port;
- vsl_lab/controllers/cav_staircase.py: per-CAV set-speed staircase in 1 km/h steps, at least X s apart, waiting until the speed is reached, via setMaxSpeed on ACC/CACC CAVs;
- vsl_lab/jobs/mrg3_run.py: arms 'cavpi' (P), 'cavconst' (C) and posted-VSL arms (MTFC, SPECIALIST, Carlson upstream staircase);
- vsl_lab/plants/mrg3.py: the CAV vType is SUMO CACC/ACC at defaults with speedFactor 1.5, so the set speed alone sets the desired speed.

No JAD, Hayat or speed-harmonisation-zone CAV rule exists in the archive.

**Fit.** Port PI with saturation and FollowerStopper (with provenance in the commit message, per CLAUDE.md). The staircase logic is a close template for the ±5 km/h per 2 s quantiser (change the step to 5 km/h and the interval to 2 s). The MTFC/SPECIALIST arms need VSL, which V15 excludes.

**Sources:**
- git show claude/v5b-core:vsl_lab/controllers/cav_staircase.py ; :vsl_lab/plants/ring.py ; :vsl_lab/jobs/mrg3_run.py ; :vsl_lab/plants/mrg3.py. </srv/shared/Workspace/phd/phd_speed_harmo_v5 (branch claude/v5b-core)> (seen: local_test). Supports: Which rules exist and how they actuate CAVs

### Verification: citations and numbers that failed or were corrected

- [F3] **details_wrong**: Lee et al. Traffic Control via CAVs: An Open-Road Field Experiment with 100 CAVs, arXiv 2402.17043 v1; IEEE CSM DOI 10.1109/mcs.2024.3498552. Correction: The arXiv v1 (26 Feb 2024) author order matches the citation (Lee, Wang, Jang, Hayat, Bunting, ...). The journal version (Crossref) is IEEE Control Systems 45(1):28-60, Feb 2025, with Lichtle added as 4th author and '(CAVs)' in the title. Confirmed in the text: the INRIX update of about 60 s and latency of about 180 s; Eq. 17 uniform kernel, which 'only requires one parameter, w, to tune'; Simple / MicroAccel (six variants) / RL (five variants); HybridRL with kernel smooth + RL buffer chosen; engagement 38 % / 78 %; 97 of 100 on the ACC-based controller. One correction: the 97/100 statement is in Sec. 2.2.3 'ACC-Based Controller', not Sec. 7.4.3.
- [F6] **details_wrong**: Cicic, Johansson (2019) 58th IEEE CDC, Nice. Correction: The pages are 3146-3151 and the DOI is 10.1109/CDC40024.2019.9029216 (Crossref), not 'around 3149'. Otherwise confirmed from the full text: rho_d = sigma/3 (one third of the lanes), U_p 60 km/h, U_min 50 km/h, 50 km with no ramps, a 2-min closure, 100 runs, and Table I means 6.6 / 4.51 / 3.99 / 3.58 % with medians 6.49 / 4.04 / 3.64 / 3.32 %. The approximate-density means (5.22 / 4.49 / 3.82 %) are indeed worse.
- [F7] **details_wrong**: Wang, Daamen, Hoogendoorn, van Arem (2016) J. Intelligent Transportation Systems 20(6):559-572. Correction: Crossref metadata match (issue 6). The cited itskrs URL returned HTTP 403 to my fetch. The abstract (Semantic Scholar) says the link controller 'regulates traffic speeds through variable speed limits (VSL) gantries' and intelligent vehicles use the VSL commands as parameters. The concept therefore relies on VSL gantries for all traffic, which V15 excludes; it is not a pure CAV-actuated rule. It was tested on a two-lane freeway in simulation and lowered TTS and fuel.
- [F7] **details_wrong**: Yang, Jin (2014) TR-C 41:48-60. Correction: Crossref metadata match. The cited its.uci.edu page shows only the title and no abstract, so it does NOT support the 'advisory speed limit' claim. That claim rests only on a search snippet of the abstract. The 30 % fuel/CO2 field figure is from a separate TRB 2014 paper (TRID 1289936), as the finding flags. Use the DOI 10.1016/j.trc.2014.01.016 and keep [VERIFY].
- [F8] **details_wrong**: Archive notes_vehicles.md and round4_th.md. Correction: +93.0 % / +45.7 % is confirmed in round4_th.md. The emergency-braking counts (CACC 23, ACC 79 at 0.5 s; 9 at 0.2 s and 8 at 0.1 s) are in docs/lab/round3_tm21_protocol.md:113-128, not in notes_vehicles.md, which only cites that file. That file already labels them 'a SUMO artefact at the plant's 0.5 s step' and notes that the step length also changes the human plant. So 'whether this is a SUMO artefact was not tested' understates what the archive says, although no root-cause test is recorded.
- [F2] **wrong**: Table 1: -52 % to -74 % within 200-600 m behind; about +5 % at 1400 m. Correction: The range over rows 200-600 m behind is -51 % to -74 %. +5 % holds only for 1400 m behind vs 1400 m in front; the same row is -34 % vs 200 m in front.
- [F6] **wrong**: CDC 2019 pp. around 3149. Correction: pp. 3146-3151, DOI 10.1109/CDC40024.2019.9029216

Verified as stated: 35 citations and numbers.

### Open questions
- FHWA-HRT-21-008 Eq. 12 (the linear speed-transition law) is an image that pdftotext could not extract. Read its exact form from the PDF page or from Ma et al. 2017 before implementing comparator 3.
- The Hayat et al. parameter values (k, s0, c1, c2, delta1, tau, alpha0, alpha1, k2) are only in their ref [27] preprint. Look for it or a CIRCLES code release, or tune from scratch and disclose.
- Were FHWA's speed-harmonisation field tests (phase 1 and the phase 2 managed-lane study) quantified? I did not read those chapters. Also, Ghiasi et al. 2019 was read as an abstract only [VERIFY].
- No peer-reviewed quantified energy result from the 100-vehicle I-24 test was found; only the BAIR blog trend of 15-20 %, which is for the RL controller. Search for a later CIRCLES energy paper if needed.
- Fairness: may comparators use the zone messages (downstream speed and density)? If the DRL agents see them, the comparators should too (CLAUDE.md: same observations). Decide before the protocol.
- Should comparators be held to the ±5 km/h-per-2-s interface (the fair-actuator rule), with native-rate versions as sensitivity rows only? Acceleration-based laws (Hayat, FollowerStopper's stopping region) lose fidelity under quantisation, and safety is then carried by SUMO car-following.
- CAV base model and step length (ACC vs CACC vs IDM; 0.1/0.2 s). The archive saw +45-93 % NC delay with CACC and step-dependent emergency braking, so this must be settled before the comparators are tuned.
- Include JAD as a reported row even though it is not field-proven? Drop the MPC arm with disclosure, under D5.8?
- Han, Chen & Ahn 2017 (CV-actuated VSL) was seen only as a search summary. If it turns out to be field-validated, it could replace or join comparator 3.


## Completeness critic (across the three topics)

Completeness critique (cross-set): v5.B.1 energy, cost values and CAV comparators. As of 2026-10-13.

Scope: I read docs/decisions.md V1–V19 and CLAUDE.md in v5b1. I ran three tiny local SUMO 1.27.1 tests (single vehicle, libsumo, 0.2 s steps). Scripts and output are in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5/510dd91c-1bff-427e-90a7-d763e29122b9/scratchpad/lit/critic: cruise.py (steady-speed energy at 60–130 km/h), step.py and up.py (how a ±5 km/h command is carried out), arith.py (the trade-off arithmetic). The repo was not modified.

## A. Arithmetic: can "crawl slowly" become optimal?

Steady-speed energy per km from the local runs (cruise.py; vTypes copied from emtest, mass not set):

| Class | 60 km/h | 100 km/h | 120 km/h | Trend |
|---|---|---|---|---|
| HBEFA4 petrol | 41.4 g/km | 45.9 g/km | 53.3 g/km | flat from 60 to 80 |
| HBEFA4 diesel | — | 55.6 g/km | 63.2 g/km | rises |
| HBEFA4 truck TT_AT | 381.6 g/km | 329.2 g/km | 316.1 g/km | **falls with speed** |
| HBEFA4 PC_BEV | — | 148 Wh/km | 177 Wh/km | rises |
| EVM (emtest parameters) | — | 148 Wh/km | 188 Wh/km | rises |

Prices are the cost set's central values:
- gasoline $2.58/gal ex-tax ÷ 2.819 kg/gal = $0.915/kg;
- diesel $3.06/gal ÷ 3.167 kg/gal = $0.966/kg;
- electricity $0.173/kWh at the meter ÷ 0.9 charging efficiency;
- value of time $26.93 per car-hour and $37.20 per truck-hour.

The densities are the GREET E0 figures from the energy set; E10 is not sourced.

Dropping from 120 to 100 km/h, per vehicle-km:

| Vehicle | Energy saved | Time lost | Ratio |
|---|---|---|---|
| Petrol car | $0.0068 | $0.0449 | time 6.6× larger |
| Diesel car | $0.0073 | $0.0449 | 6.1× |
| BEV, HBEFA4 | $0.0055 | $0.0449 | 8.1× |
| BEV, EVM | $0.0078 | $0.0449 | 5.8× |
| Truck | −$0.0126 (HBEFA4 says slower uses more fuel) | $0.062 | — |

Cost-minimising free-flow speed, searched over 60–130 km/h, as the energy weight is multiplied:

| Vehicle | ×1 | ×3 | ×10 | ×30 |
|---|---|---|---|---|
| Petrol and diesel cars | 130 | 130 | ≈100 | ≈80 |
| BEV, HBEFA4 | 130 | 130 | ≈102 | ≈80 |
| BEV, EVM | 130 | 130 | ≈90 | ≈61 |

What follows from this:

1. **With the central values, crawling is not optimal.** The generalised cost is set almost entirely by delay. The real risk is the opposite: energy barely shows in the headline. That conflicts with V10, which calls energy the author's most important metric, and it makes the D5.8 "≥ 10 % vs no control" bar in effect a delay bar. Put this to the author explicitly. Options: co-headline energy, or pre-register a second bar on energy.
2. **The ×10 energy-weight row proposed in the cost set (F11) flips the result.** Slowing to about 90–100 km/h becomes optimal. If that row is reported, the delay guard x % is what binds. Pre-register x and the weight sweep together.
3. **The hard-brake price is the real crawl risk.** One hard brake costs as much as this much car delay at $26.93 per car-hour:
   - $1 → 2.2 car-minutes;
   - $3.1 → 6.9 car-minutes;
   - $63 → 140 car-minutes.

   At the $63 row, CAVs would rationally open huge gaps or slow right down to avoid a single brake. Only CAV brakes are priced, so the harm moves onto HDVs. Cap the brake row, or keep hard braking as a constraint. Either way this reopens V16, so it is an author decision.
4. **The HBEFA4 truck class gets the direction wrong.** Fuel per km falls from 381.6 to 316.1 g/km between 60 and 120 km/h. A rough road-load sketch says the opposite: wheel energy per km is about +25 % from 100 to 120 km/h. My sketch assumed 36 t, a drag area of 6 m² and rolling resistance 0.006; none of these are sourced. So the reward would penalise any harmonisation that slows HDV trucks. The 29 % fit-error figure in the energy set does not capture this; the problem is the sign of the speed slope. A ×0.7/×1.3 sensitivity row does not fix a reversed gradient.

   My guess is that HBEFA4 is fitted over traffic situations, not steady-state physics [VERIFY]. That would also raise a double-counting question: the speed polynomial may already include average stop-and-go, and the acceleration term then adds it again [VERIFY].

## B. Unit and dollar-year mismatches

1. **The energy basis is mixed.** The energy set converts fuel to kWh with GREET 1.8d.1 lower heating values for E0 (2010). The cost set gives $/kWh on EIA heat contents labelled higher heating value; that label is not confirmed on the cited page. Combining the two puts the energy cost off by about 5–7 %.
   - Fix: price fuel per kg (EIA $/gal ÷ density of the same fuel). Use kWh, with one stated lower heating value, for reporting only.
   - Also note: SUMO uses 742 g/L for gasoline, GREET 744.7 g/L. HBEFA4 fuel mass refers to EU reference fuel, while US retail is E10 [VERIFY].
2. **Dollar years differ.** Value of time is in 2024 $. EIA fuel and electricity prices are 2025 nominal. MnDOT SFY2027 is in 2025 $. Deflate everything to one year with BCA Table A-7 [VERIFY the deflator value], or state 2025 $ throughout.
3. **Electricity is measured and priced at different points.**
   - SUMO reports Wh at the battery terminal; the price is at the meter.
   - The only charging efficiency (0.9) is an assumption used in Koch 2021 and Behrisch 2024, not a measured source [VERIFY].
   - Fuel is priced ex-tax at resource cost, but electricity is retail including taxes and fixed charges. Disclose the asymmetry or adjust.
4. **BEV recuperation is almost free under the EVM settings.**
   - At the code defaults (propulsion 0.98, recuperation 0.96), an accelerate-and-brake cycle loses only about 6 %. The emtest parameters (0.9/0.8) lose about 28 %. Neither has a power cap.
   - HBEFA4 PC_BEV recovered 69 % of the acceleration energy in the earlier test.
   - So stop-and-go costs BEVs little in energy, and per-step negative energy enters the reward.
   - Fix: a sourced efficiency set with recuperation caps. Note that Koch Table II has 77 Nm / 50 kW, not the code defaults.
5. **The per-vehicle-km denominator can be gamed.** Door-to-door delay counts insertion and ramp queues, which have zero km. If served vehicle-km shrinks, cost per vehicle-km can improve.
   - Fix: a fixed denominator (the inflow's vehicle-km, or no control's served vehicle-km). Co-headline served throughput, as CLAUDE.md requires.
6. **Occupancy.** USDOT's peak occupancy of 1.34 covers trips starting 06:00–08:59. From 09:00 to 10:00 the off-peak value of 1.41 applies. Use time weighting, or state the simplification.

## C. How the command is carried out (the local test changes several assumptions)

`setSpeed(v − 5 km/h)` on Krauss, ACC and CACC at 30 m/s gave −4.5 m/s² (the vType's decel) in the first step and −2.44 in the second. Upward it gave +2.6 m/s².

`slowDown(tgt, 2 s)`, `setAcceleration(a, 2 s)` or a per-step `setSpeed` ramp give ±0.69 m/s². But after the duration, `slowDown` and `setAcceleration` release the vehicle back to its own desired speed (it jumped to +2.6), so the new target must then be held with `setSpeed`.

Consequences:
- With a plain `setSpeed`, every "brake" command counts as a hard brake under V11's 3–4 m/s² threshold.
- Energy is then evaluated far outside the HBEFA slope-derived range (±0.6 m/s², from HBEFA 2.1/3.1; unverified for HBEFA4).
- Even a correct 2-s ramp is 0.69 m/s², just past that ±0.6 m/s² edge.

Pre-register the ramp-and-hold semantics for both the DRL and the comparators. Results: step.py and up.py.

## D. Sensing the comparators need versus V15 (HDVs not measured, no loop detectors)

| Controller | What it needs | Fit |
|---|---|---|
| PI with saturation, FollowerStopper | own speed, gap, leader speed (onboard radar; the leader is often an HDV) | OK only if onboard sensing of the leader counts as allowed. Decide whether it does. FollowerStopper's U must come from CAV probes. |
| Hayat | leader acceleration, plus downstream speed from the CIRCLES planner | The planner fused INRIX, which is all-vehicle probe data. That is not allowed here; use CAV-only pings (about 50 % penetration) and disclose the change. |
| FHWA-HRT-21-008 speed harmonisation | **virtual loop detectors** averaging speed over 5 min | Violates V15 as published. Replace with CAV-probe mean speeds and call it an adaptation. |
| JAD (He 2017), Čičić 2019 | wave and density estimates (Čičić needs all-vehicle density) | Needs a CAV-only estimator with a known penetration rate [VERIFY whether that is feasible at 50 %]. |
| Han, Chen, Ahn 2017 | bottleneck state | Detector-based. Wang 2016 needs VSL gantries, which are already excluded. |

Prerequisite missing from V1–V19: **the DRL agent's observation set is not decided.** The fairness rule ("same observations") can't be applied until it is. That decision must come before the comparators are chosen and tuned.

## E. Models and comparators an examiner would expect but are missing

1. **Malikopoulos, Hong, Park, Lee [+ Ryu?] (2019): "Optimal Control for Speed Harmonization of Automated Vehicles".**
   - Seen: arXiv 1611.04647 abstract only. The search summary gives IEEE T-ITS 20(7):2405–2417 and DOI 10.1109/TITS.2018.2865561 [VERIFY]. The arXiv page lists 4 authors; the search summary lists 5 [VERIFY].
   - Closed-form, real-time speed harmonisation of AVs before a speed-reduction zone. Per a search summary [VERIFY], it was benchmarked against VSL and the vehicular SPD-HARM.
   - Peer-reviewed, CAV-only, freeway bottleneck: a direct analogue that a reviewer will ask about. Whether it handles mixed traffic and which inputs it needs: [VERIFY, full text unread].
2. **SPD-HARM (vehicle-based speed harmonisation)**, the baseline used in that paper [VERIFY its source].
3. **Kesting, Treiber, Schönhof, Helbing (2008): "Adaptive cruise control design for active congestion avoidance", TR-C 16:668–683.** Metadata confirmed by search; text not read [VERIFY].
   - A traffic-state-dependent ACC rule: per vehicle, local sensing only, freeway bottlenecks, studied at varying penetration.
   - Fits V15 better than any ring smoother.
4. **A tuned constant CAV speed cap, one parameter** (`cavconst` in the archive). This is the trivial baseline that shows whether a learned policy beats simply slowing CAVs. The "constant-cap baseline" rule in the v5 CLAUDE.md is not carried into v5b1. Add it.
5. **A no-control sanity row.** The archive found no control with 25 % CACC at +45.7 % to +93 % delay versus human-only. If the CAV base model is poor, "≥ 10 % vs no control" becomes easy to meet. Report no control with the CAVs' base car-following equal to the HDVs' as a reference.
6. **Energy for a US inflow: US EPA MOVES.** A US examiner will ask why it is not used. A MOVES operating-mode cross-check of aggregate energy for each scenario is cheap (VSP bins). The VSP coefficients are still [VERIFY].
7. **Free truck cross-checks:** EU VECTO (cited in Weller 2019) and US EPA GEM are official simulators of heavy-duty fuel use [VERIFY whether they suit constant-speed and per-trajectory use]. Or use a road-load truck model with sourced parameters. Needed because of A.4.
8. **Ambient conditions in Minnesota.** No set covers cold-start or temperature effects for ICE, or HVAC load for BEVs (only the Fiori 2016 abstract). State the season and the auxiliary power.
9. **Fleet and powertrain mix is undecided.** Shares of petrol, diesel, BEV and trucks are open, as is which powertrains the CAVs have. A US or Minnesota source is needed (e.g., MnDOT vehicle-class counts on US-169, AFDC registrations) [VERIFY]. The CAV powertrain choice changes the sign and size of CAV-side energy effects.

## F. Claims that rest on unverified or self-derived sources (do not pre-register as sourced)

- **Hard-brake $1–$63:** my own derivation (work-zone cross-sectional slope, 4.7 % penetration, a different threshold). There is no accepted per-brake value. V11's 3–4 m/s² does not match the 2.67 m/s² used in the literature.
- **Comparator 3 "peer-reviewed, field-trialled":** the FHWA report is not peer-reviewed. Its field chapters are unread, Eq. 12 is unread, and Ghiasi 2019 was read as an abstract only.
- **Hayat:** parameters unpublished (ref [27]). Eq. 14 as printed is not a clip; implement the clip the text describes and disclose it. The journal version is unread.
- **VT-CPFM:** equations unread (403), so the proposed independent ICE cross-check cannot be built yet. The claim that it was designed to avoid bang-bang control is unsupported.
- **HBEFA4 acceleration derivation** is unknown. The HBEFA higher-heating-value label is unverified. The 0.9 charging efficiency is an assumption.
- **Offline EVM/MMPEVEM via emissionsDrivingCycle on 0.2 s data is wrong** (TS = 1 s; net −14 % in the verifier's run). The cross-check must be in-simulation or a Python re-implementation with dt = 0.2.
- **Outdated values:** MnDOT SFY2025 is superseded by SFY2027 (2025 $). The EUROCONTROL values are an old release and aviation-specific.
- **CLAUDE.md:** "Frejo & De Schutter 2021, ≈2–3 % / ≈9 % caps" is still [VERIFY].

## G. Concrete follow-ups, in order

1. **Author decision on the headline structure.** Energy share under monetary weights versus V10's "most important"; a second bar or co-headline on energy; the hard-brake row as a constraint or a capped price (this reopens V16); x % of the delay guard pre-registered together with the energy-weight sweep. Flag that the ×10 energy row makes 90–100 km/h optimal.
2. **Decide the agent observation set and the sensing allowed** (onboard radar of HDV leaders, CAV probes only). Then re-check each comparator's inputs against section D.
3. **Pre-register how a command is carried out** (ramp over 2 s, then hold) and the hard-brake threshold. Re-run step.py on the chosen CAV base model.
4. **Trucks:** check HBEFA4 TT_AT fuel versus speed against HBEFA 4.2 tables or a VECTO/GEM run. If the reversed slope is confirmed, replace the main truck model or exclude truck energy from the reward. Decide the truck speed cap.
5. **Pricing on mass:** gasoline/E10 and diesel $/kg with one density source. One dollar year (2025 $ or deflated to 2024 $). A charging-efficiency source, and recuperation caps for BEVs.
6. **Fixed denominator** for the per-vehicle-km headline. Report served vehicle-km.
7. **Literature:** read in full Malikopoulos et al. 2019 (inputs, mixed traffic or not), Kesting et al. 2008, SPD-HARM, the FHWA field chapters and Eq. 12, Park 2013 for VT-CPFM. Add the tuned constant-cap arm and the no-control base-model sanity row.
8. **Fleet mix** for the US-169 inflow, the CAV powertrain assignment and the season/auxiliary load. Each needs a source.

Sources opened in this pass: [arXiv 1611.04647](https://arxiv.org/abs/1611.04647) (abstract), [NJIT record](https://digitalcommons.njit.edu/fac_pubs/7503) (search result only), [Kesting et al. precursor, arXiv physics/0601096](https://arxiv.org/abs/physics/0601096) (search result only), [TU Dresden publication list](https://tu-dresden.de/bu/verkehr/ivw/osv/die-professur/beschaeftigte/martin.treiber/lebenslauf) (search result only), [sumo-user list on slowDown](https://eclipse.org/lists/sumo-user/msg04863.html) (search result only). All local numbers are from the scripts above.
