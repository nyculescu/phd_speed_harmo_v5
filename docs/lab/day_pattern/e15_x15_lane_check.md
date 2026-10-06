# E15–X15 lane check (D4.5; protocol v3 §1.7, A1(ii)), 2026-10-06

**Question.** Does U.S.169 SB have a lane added at the Old Shakopee Rd entrance (E15, km 7.518) that ends at the T.H.101 exits (X14 km 8.999, X15 km 9.217)?

**Method.** Geometry sources only, with no traffic data. F16's flow ratio (R = 1.371) motivated the check and was not used to answer it. Raw files are in `/home/catalin/work/phd/vsl_lab_runs/day_pattern/lanecheck/`.

## Sources

| Source | Date of the information | What it says |
|---|---|---|
| MnDOT IRIS `metro_config.xml.gz` (r_nodes `rnd_1396` E15 … `rnd_95768` T.H.101) | config pulled for this project (current) | 2 mainline lanes throughout. `shift` stays 5 from Old Shakopee Rd (km 7.199) to T.H.101 (km 9.390), so no lane is added. |
| OpenStreetMap, SB US 169 ways (API map call, 2026-10-06; way histories) | current versions edited 2021-10-11 (user vrynkevich_l) and 2022-08-09 (user zbrown4) | **3 lanes** from about lat 44.8055 (just upstream of the E15 node at 44.8046), across the Minnesota River bridge, to about lat 44.7916. Short **4-lane** segments sit at 44.8039–44.8034 and 44.7971–44.7940; the latter has `turn:lanes = none\|none\|through;slight_right\|slight_right`, i.e. exit lanes before X14. The road is **2 lanes** from 44.7916 to T.H.101. |
| OpenStreetMap history of the same ways | 2011–2021 | The same ways were tagged **2 lanes** by several editors until 2021-10-11 (way 39292670, versions 8–16; way 188375340, versions 1–5). |
| Press: Star Tribune, "MnDOT removes temporary lane on Hwy. 169 in Bloomington" (2019; full text not retrieved, HTTP 429); Southwest News Media / Patch reports (2013–2014) | 2013–2019 | MnDOT has **restriped US 169 to add a temporary lane** between CR 18 (Shakopee) and Pioneer Tr when floods closed the T.H.101 / T.H.41 river crossings, and returned it to the existing condition afterwards. The shoulders were strengthened for this use. [VERIFY: details read only from search-result summaries] |

## Verdict

**Inconclusive. Step (b) of §1.7 applies, i.e. the G4 capacity substitute.**

The sources conflict:
- IRIS says 2 lanes.
- OSM says 3 lanes, but only since October 2021, by imagery-based editors.
- The press shows that a third lane has been added *temporarily* in flood years.

The lane count on a given 2023 day may therefore depend on the date. A Minnesota River flood season, if one occurred in spring 2023, could have triggered the temporary lane [not checked]. No primary MnDOT lane inventory was retrieved.

## How to resolve it

The author could:
- check dated street-level or aerial imagery of the Bloomington Ferry Bridge (US 169 SB, Old Shakopee Rd to T.H.101) for 2023, e.g. several dates across the year; or
- obtain MnDOT's through-lane inventory for that segment.

If 2023 imagery shows a permanent third lane, step (a) applies. If it shows 2 lanes, step (c) applies. If the count varies by date, the lane count becomes a per-day input. That would need a protocol rule before any new plant is fitted.
