# V28: HBEFA4 truck curve checked against second sources (2026-10-13)

*One research agent; web sources opened 2026-10-13; local SUMO 1.27.1 tests (single vehicle). Fuel converted with LHV 42.70 MJ/kg (VECTO reference diesel, TU Graz report Table 10). Nothing here binds until the author decides.*

## Steady-speed fuel, flat road, a = 0 (g/km / kWh/km)
| Model | 60 | 80 | 90 | 100 | 120 km/h |
|---|---|---|---|---|---|
| HBEFA4 TT_AT_gt34-40t_Euro-VI_D-E | 382 / 4.53 | 349 / 4.14 | 338 / 4.01 | 329 / 3.90 | 316 / 3.75 |
| HBEFA4 TT_AT_gt40-50t_Euro-VI_D-E | 430 / 5.11 | 394 / 4.67 | 381 / 4.52 | 371 / 4.41 | 357 / 4.23 |
| HBEFA4 RT_gt32t_Euro-VI_D-E | 380 / 4.51 | 356 / 4.22 | 347 / 4.12 | 341 / 4.04 | 331 / 3.92 |
| HBEFA4 TT_AT_BEV (kWh/km, electricity) | 1.65 | 1.61 | 1.60 | 1.59 | 1.58 |
| HBEFA3 HDV_D_EU6 | 288 / 3.42 | 258 / 3.06 | 247 / 2.93 | 239 / 2.84 | 227 / 2.69 |
| COPERT / EEA, articulated 34–40 t Euro VI D/E (valid 5–80 km/h; * extrapolated) | 215 / 2.54 | 216 / 2.56 | 248* / 2.94 | 300* / 3.56 | 467* / 5.54 |
| Road load + Willans, 40 t | 221 / 2.62 | 238 / 2.83 | 254 / 3.01 | 273 / 3.23 | 320 / 3.79 |
| Road load + Willans, 32.1 t | 199 / 2.36 | 217 / 2.57 | 232 / 2.75 | 251 / 2.97 | 298 / 3.53 |
| Road load, constant 229 g/kWh, 40 t | 192 / 2.28 | 235 / 2.78 | 260 / 3.09 | 289 / 3.43 | 356 / 4.22 |
| **Measured**, TU Graz tractor #1, 32.1 t, 88 km/h flat | | | 228.5 g/km (tractor #2: 209.7) | | |

## Verdict: a fitting artefact, not physics
1. **Why the curve falls.** In SUMO's coefficient table (`HelpersHBEFA4.cpp`, v1_27_1), the fuel row of TT_AT_gt34-40t has the v² and v³ terms set exactly to zero. At a = 0, fuel per km is then f0/v + f1, which can only fall with speed, at every speed.
2. **It is systematic.** The v² and v³ terms are both zero in 131 of 165 TT, 102 of 139 RT and 138 of 140 urban-bus classes, and in **no car class**. TT_AT_BEV energy also falls with speed, which is physically impossible for a BEV at steady speed.
3. **Why the fit looks like this: inference, not verified.** The fitting inputs are "non-public" (`tools/emissions/hbefa2sumo.py`). The likely cause is a constrained fit to average-speed traffic-situation factors.
4. **The guidebook warns against this use.** It says its speed formulas are for average travelling speed, not for constant or "spot" speeds. Its HDV factors come from HBEFA, so COPERT is not independent, but it is U-shaped with a minimum near 70 km/h.
5. **Independent sources say fuel rises with speed:**
   - the road-load physics model (sourced parameters) rises about 15 % from 60 to 90 km/h;
   - a measured on-road study rises too (not steady state [VERIFY]).
6. **The level is also high.** HBEFA4 gives about 340 g/km at 88 km/h, against 228.5 g/km measured at 32.1 t.
7. **No speed cap fixes it.** It still falls 11 % from 60 to 90 km/h.

## Recommendation (agent; author decides)
- **Do not use the HBEFA4 (or HBEFA3) heavy-vehicle classes** for energy in the reward or the metrics.
- **Trucks:** a road-load + Willans model in Python per 0.2 s step:
  - P = (R0 + R2·v²)·v + (m + m_rot)·a·v;
  - parameters from TU Graz tractor #1: rolling resistance 5.50 N/kN, CdA 5.21 m² (R2 = 3.095 N·s²/m²), m_rot = 750 kg;
  - Willans slope 184.5 g/kWh at the wheel;
  - offset F0 = 1.10 g/s, calibrated to the measured 228.5 g/km at 88 km/h, at 40 t;
  - zero fuel when P < 0 (own choice).
- **Sensitivity rows:** the constant-consumption version and COPERT (≤ 80 km/h). Pre-register that the sign of the result agrees.
- **Truck speed cap 90 km/h** (vType maxSpeed 25 m/s; Directive 92/6/EEC [VERIFY, summary only]). The Irish HGV motorway limit may be lower (80 km/h?) [VERIFY].

## Emission class strings in SUMO 1.27.1 (each tested as a vType)
Unknown names **stop SUMO** ("emissionClass … doesn't exist"); there is no silent fallback. The lower-case aliases fail.
- **Petrol car:** `HBEFA4/PC_petrol_Euro-6d` (fit error 3.97 %), `…Euro-6d-temp`, Euro-1…7; HBEFA3 `PC_G_EU0…6`.
- **Diesel car:** `HBEFA4/PC_diesel_Euro-6d` (6.93 %), `…Euro-6d-temp`; HBEFA3 `PC_D_EU0…6`.
- **HEV car: none.** HBEFA4 has HEVs only for urban buses. Full PHEMlight has them but needs a licence.
- **PHEV car:** pairs per Euro class, a fuel mode plus an electric mode. For example `HBEFA4/PC_PHEV_petrol_Euro-6d_(P)` (13.22 %) with `…_(El)` (4.06 %), and the diesel pair `…_(D)` / `…_(El)`. This needs two vTypes or a blend done in post-processing.
- **BEV car:** `HBEFA4/PC_BEV` (5.04 %), `Energy`, MMPEVEM files.
- **Trucks:** `HBEFA4/TT_AT_<size>_Euro-VI_D-E`, `RT_<size>_Euro-VI_D-E`, `TT_AT_BEV`, `TT_AT_PHEV_…`, `TT_AT_LNG_…`, `RigidTruck_BEV_gt12t`.

## Sources (opened 2026-10-13)
- SUMO source v1_27_1, read in full: `src/utils/emissions/HelpersHBEFA4.cpp/.h`, `HelpersHBEFA3.cpp`, `tools/emissions/hbefa2sumo.py`, at github.com/eclipse-sumo/sumo/tree/v1_27_1.
- SUMO docs, HBEFA4-based and HBEFA3-based pages (main branch).
- Rexeis et al. (TU Graz FVT), *Comparison of fuel consumption and emissions for representative heavy-duty vehicles in Europe*, report FVT-099/17, 27/02/2018, for the ICCT. Tables 4, 6, 9, 10 and 13, §6.2 and §7.4 read. <https://theicct.org/wp-content/uploads/2021/06/HDV-EU-fuel-consumption_TU-Graz_ICCT-Consultant-Report_27022018_vF.pdf>. The origin of the Willans slope is [VERIFY].
- EMEP/EEA air pollutant emission inventory guidebook 2023 (update 2026), chapter 1.A.3.b.i-iv: relevant sections read and Appendix 4 xlsx parsed.
- Rehder & Rehder, SIMEA 2023, PAP48 (full text; its abstract and body numbers disagree).
- Directive 92/6/EEC Art. 3: EUR-Lex summary only [VERIFY].

## Not checked
- HBEFA 4.2 tables (licensed).
- A VECTO or GEM run.
- The HBEFA4 fitting inputs.
- The Willans offset rests on one measured point; gear effects at low speed are ignored.
