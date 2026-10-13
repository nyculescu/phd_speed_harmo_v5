# Irish / EU parameters for the M50-inspired design (checked 2026-10-13)

*One research agent; sources opened 2026-10-13; repo not modified. Nothing binds until the author decides. The arithmetic marked as such is the agent's own.*

## 1. Value of travel time (VTT)
Sources (read in full):
- TII PAG Unit 6.11 *National Parameters Values Sheet*, PE-PAG-02030, Sept 2026 edition: <https://www.tiipublications.ie/library/PE-PAG-02030-08.pdf>
- DoT *Transport Appraisal Framework* (TAF) Module 8, Update Version 2, July 2026: <https://assets.gov.ie/static/documents/f6ebdcc4/TAF_2026_Module_8_Detailed_Guidance_on_Appraisal_Parameters.pdf>

| Item | Value | Where |
|---|---|---|
| VTT, work / business | €26.16 per person-hour (factor cost); ×1.16 = €30.35 at market prices | TAF Table 6, §8.8.4; TII T6.11.9 |
| VTT, commuting | **€8.90 per person-hour** (market prices) | same |
| VTT, other non-work | €8.01 per person-hour (market prices) | same |
| Price base | **2016 prices** | TAF §8.1.7; TII T6.11.1 |
| Real growth | TII: 1.049/yr 2016–19, 1.022/yr 2020–24, 1.023/yr 2025–30+. TAF: 2.2 % / 2.3 % (GNP per person employed). TAF applies growth to work VTT only; TII applies its table generally | TAF Table 7, §8.8.6; TII T6.11.10 |
| Conversion to current € | CSO CPI inflation calculator | TII T6.11.8; TAF §8.7 |
| Car occupancy, weekday AM peak | work 1.26, commuting 1.23, other 1.66 | TII T6.11.34 |
| Goods-vehicle occupancy, AM peak | OGV1 1.09, OGV2 1.03 (work) | same |
| Goods-vehicle time cost | No VTT per vehicle-hour. Closest: driver work VTT × occupancy, plus the non-fuel time cost (factor cost, 2016): OGV1 360.71 c/h, OGV2 695.30 c/h | TAF Table 12; TII T6.11.17 |
| Motorway vehicle mix, 2016 | car 82.97 %, LGV 8.81 %, OGV1 2.99 %, OGV2 4.77 %, PSV 0.65 % | TII T6.11.32 |
| Purpose split by time of day | not found | — |

Agent's arithmetic [VERIFY the step convention]: real growth 2016 → 2026 is about ×1.41. The CPI uplift to 2026 euros is still to be applied.

## 2. Unit of account and energy
- **Perceived costs, with everything at market prices** (t = 0.16; TAF §8.1.6). Non-work fuel is at market prices; work fuel is net of VAT (TAF §8.11.3).
- **Fuel prices, TII T6.11.15 (2016 prices):** petrol 130.6 c/L market (47.4 c/L excluding duty and VAT); diesel 120.7 c/L (50.0). Growth 1.07/yr 2016–21, then 1.00.
- **No official electricity price.** EV consumption is given as 0.221 kWh/km (car) and 0.259 kWh/km (LGV), from UK TAG 2015.
- **Official average-speed fuel function:** L/km = a/v + b + c·v + d·v² (TAF Table 10 / TII T6.11.14). Petrol car: a 0.5155, b 0.06767, c −0.0007362, d 0.000005619. Coefficients are also given for diesel, LGV, OGV1 and OGV2. This is a possible cross-check for V28, with the usual average-speed caveat.

## 3. Heating values and densities
| Fuel | Density (kg/m³) | LHV (MJ/kg) | MJ/L | kWh/L |
|---|---|---|---|---|
| Petrol, RED Annex III | – | 43 | 32 | 8.89 |
| Diesel, RED Annex III | – | 43 | 36 | 10.00 |
| Gasoline E5, JEC WTW v5 | 746 | 42.3 | 31.56 | 8.77 |
| Gasoline E10, JEC WTW v5 | 748 | 41.5 | 31.04 | 8.62 |
| Diesel B7 market blend, JEC WTW v5 | 836 | 42.7 | 35.70 | 9.92 |

Sources:
- (EU) 2018/2001, consolidated 2024-07-16, Annex III: <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02018L2001-20240716>
- JEC WTW v5, EUR 30284 EN (2020), Table 8 p. 40: <https://www.concawe.eu/wp-content/uploads/jec_wtw_v5_121213_final.pdf>

The JEC MJ/L and kWh/L columns are the agent's arithmetic. Which blend Ireland sells (E5 or E10) is [VERIFY].

## 4. M50 facts
Main source: TII *National Road and Greenway Network Indicators 2025*, July 2026, pp. 14–22: <https://www.tii.ie/media/w4xns2ed/tii-national-road-and-greenway-network-indicators-2025.pdf>

| Fact | Value | Source |
|---|---|---|
| AADT 2025 (all vehicles, % HGV) | J5–J6 164,000 (7.5 %); J6–J7 161,750 (8.5 %); J7–J9 159,000 (7.4 %); J4–J5 152,250 (7.5 %); J9–J10 135,250 (3.7 %); J10–J11 123,000 (3.3 %); J11–J12 116,750; J12–J13 110,000; J16–J17 53,750 | p. 16 |
| Records 2025 | Highest daily flow 189,590 (N3–N2, 26 June). Highest hourly flow 13,277 (N7–N4, 07–08 h, 23 July), probably two-way [VERIFY]. Busiest day: Thursday | p. 15 |
| AM peak | Both directions congested. Southbound N2→N7 at LOS F/E around 07–09 h; northbound N7–N4 at E/F 07–09 h; northbound J15–J16 at F at 08 h | p. 18 |
| **Speed limit** | **100 km/h**; reduced to 80 or 60 km/h under congestion or bad weather | TII press release (undated, pre-eMOS) |
| **VSL in operation (eMOS)** | Launched 17 Sep 2021. Planned: 19 gantries, 386 lane control signals, 64 VMS, "fully deployed … early 2023". In 2025, 72–75 % of speed reductions were for congestion | TII press release 17 Sep 2021; TII 2025 p. 21 |
| Lanes | 32 km widened from 2 to 3 lanes each way, "a fourth auxiliary lane in some places" (2010). No official lane count per section [VERIFY] | RTÉ, 28 Sep 2010 |
| Junction spacing | J3–J17 is about 38.5 km over 14 junctions, about 2.75 km apart on average | Wikipedia [VERIFY] |

**Traffic data:**
- Open data: <https://data.tii.ie/traffic-counter-readme.html>, CC BY 4.0. Daily CSVs of per-vehicle records (lane, class, length, gap, headway), per-site per-class daily counts and per-minute counts.
- **Gap:** files from 2013-06 to 2021-03 return HTTP 200; every date tested from 2021-06 to 2026-10 returned 403.
- Live portal: trafficdata.tii.ie (Drakewell). Its API answered "not_permitted".
- No M50 counter id found (a "M50 J6–J7" counter is mentioned in search results only [VERIFY]).

## 5. Fleet shares
| Item | Value | Source (date) |
|---|---|---|
| Private-vehicle stock by fuel, June 2026 | petrol 866,106; diesel 1,257,849; HEV+PHEV 334,439 (no split); BEV 124,753. Shares 33.5 / 48.7 / 12.9 / 4.8 % (agent's arithmetic) | CSO *Composition of Ireland's Vehicle Fleet 2026*, Table 5, 28 Jul 2026: <https://www.cso.ie/en/releasesandpublications/ep/p-civf/compositionofirelandsvehiclefleet2026/keyfindings/> |
| New cars 2025 | petrol 25.11 %, HEV 22.48 %, BEV 18.89 %, diesel 17.09 %, PHEV 14.82 % (124,954 cars) | SIMI, 2 Jan 2026: <https://www.simi.ie/en/news/124-954-new-car-registrations-in-2025> (read via fetch, not curl-verified) |

V23's "HDVs about 80 % ICE" matches the stock (petrol + diesel 82.2 %), not new sales (42 %).

## Not verified
- Lane counts per section, and the official speed-limit order (e.g. whether any section is 120 km/h).
- An M50 counter id and the portal's granularity.
- The 403 on open files after about 2021.
- The HEV/PHEV split of the stock.
- The Irish petrol blend.
- Purpose shares by time of day.
- An official Irish electricity price.
