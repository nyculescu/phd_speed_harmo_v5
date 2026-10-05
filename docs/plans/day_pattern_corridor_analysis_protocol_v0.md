# Corridor analysis: choosing the H1/H2 corridor from real MnDOT data (protocol v0)

*Committed 2026-10-05, before any criterion below is computed. The only things seen in advance are the data format and coverage (counts per 30 s per lane, occupancy in %, about 0.2 % null values, 87–98 % of detector-days present) and the screening shares (`day_pattern_screening_v0.json`, occupancy-based, 20 Wednesdays that are a subset of the days used here). Disclosed.*

**Data:**
- 3 shortlisted corridors (author choice 2026-10-05): I-35W SB, I-394 WB and T.H.100 SB (`vsl_lab/data/mndot.py` `TOP3`);
- 104 days of 2023: 52 Wednesdays, 26 Saturdays, 26 Sundays;
- mainline from 4 km upstream of the first metered ramp to 2 km downstream of the last;
- each metered ramp's queue, passage, merge, bypass and green detectors, and the exit detectors in between.

No new data requests. This is data analysis, not a simulation, and nothing here is a gate.

## 1. Definitions

**5-min bins over 05:00–23:00** (216 bins). For a lane-bin:
- **flow** = 12 × the sum of its ten 30-s counts (veh/h);
- **occupancy** = the mean of the 30-s values (%);
- valid if ≥ 9 of the 10 values are non-null.

**Station-bin** (valid if every lane is valid):
- flow q = the sum over lanes (veh/h);
- density k = Σ over lanes of (occupancy / 100) × 5,280 / L_field, where L_field (ft) is the detector's field length from the MnDOT configuration (IRIS convention, veh/mi);
- speed v = q / k (mph). If k = 0, v is undefined and counts as free flow.

**Station-day:** valid if ≥ 90 % of its bins are valid.

**Active bottleneck** (a speed-differential rule of the kind commonly used on PeMS/MnDOT data [VERIFY: Chen, Skabardonis & Varaiya 2004, TRR, SAGE]): between consecutive valid stations u (upstream) and d (downstream, within 3 km), in a bin where
- v_u < 40 mph; and
- v_d − v_u ≥ 20 mph.

It is **active on a day** if this holds in ≥ 5 of 7 consecutive bins, i.e. 35 min. **Onset** is the first bin of the first such window; **end** is the last bin of the last such window in that episode. Episodes separated by < 30 min are merged.

**The corridor's bottleneck B** = the station pair active on the most Wednesdays, within [first metered ramp − 0.5 km, last metered ramp + 2 km].

## 2. Criteria (applied to Wednesdays; weekend days reported separately)

| ID | Criterion | Rule |
|---|---|---|
| **C1** | A recurrent active bottleneck that varies from day to day | B is active on **30–90 %** of valid Wednesdays |
| **C2** | Ramp demand can be reconstructed | For **every** metered ramp, ≥ 1 Queue **and** ≥ 1 Passage detector is valid on ≥ 90 % of days. Valid means ≥ 90 % of bins valid, and not all-zero over 06:00–20:00. |
| **C3** | Upstream boundary uncongested *(reported; failure is not disqualifying)* | The most upstream valid station has v ≥ 45 mph in ≥ 95 % of bins on ≥ 95 % of valid days. If it fails, the approved upstream extension must reach a station that passes C3. |
| **C4** | Measurable capacity drop at B | On activation days with an episode ≥ 30 min, at the first valid station downstream of B:<br>• Q_pre = the mean flow in the 15 min before onset;<br>• Q_dis = the mean flow from onset + 10 min to end − 5 min (needs ≥ 20 min);<br>• r = Q_dis / Q_pre.<br>PASS if the **median r ∈ [0.82, 0.97]** over ≥ 5 activation days. |

**Reported, not gating:**
- Q_dis per lane (veh/h/lane): the real value that a simulated plant must reproduce;
- pre-breakdown maximum 15-min flow per lane (capacity) at the downstream station;
- onset times; episode durations; AM (before 12:00) vs PM (12:00 or later) episodes;
- share of Wednesdays with **both** an AM and a PM episode;
- **day shapes at the upstream boundary:** the number of peaks in the 15-min flow. A peak needs a prominence ≥ 15 % of the day's maximum and peaks must be ≥ 3 h apart. Days are labelled M (two peaks, one before and one after 12:00), ^ (one peak) or flat (maximum / median of 06:00–20:00 < 1.3).
- **the M-to-trapezoid descriptive check (author, 2026-10-05):** on Wednesdays, the bottleneck's daily congested duration against the boundary's daily total and peak-hour flow (Spearman ρ), plus a binned table of duration by demand quartile. This is descriptive only. It shows whether a narrow demand band separates short episodes from all-day ones.

## 3. Choice rule (fixed now)

1. **Eligible** = passes C1, C2 and C4.
2. Among the eligible corridors, rank by:
   1. C3 passed, or an upstream extension to ≥ 10 km available in the MnDOT configuration (detector stations exist);
   2. |share of activation Wednesdays − 0.5|, smallest first (most day-to-day variety);
   3. the share of Wednesdays with both AM and PM episodes, highest first.
3. **The top-ranked corridor is proposed to the author.** The full-year pull (with its exact request count) and the upstream extension follow only after the author agrees.
4. **If none is eligible:** report which criteria failed and by how much, and propose the next shortlist candidates (#4–#8 of `day_pattern_shortlist_v0.json`) for the same analysis. No criterion is relaxed.

## 4. Outputs

- `docs/plans/day_pattern_corridor_analysis_v0.json` (summary numbers only) and `day_pattern_corridor_analysis_v0.md`.
- A ledger row.
- Code: `vsl_lab/data/corridor_analysis.py`.
