# Corridor selection v1: a bottleneck-anchored network screen (protocol)

*Committed 2026-10-05, before the counts pull and before any result below is computed.*
- *Author's choice: option (b) of `day_pattern_corridor_analysis_v0.md`.*
- *It replaces only the **selection procedure**. The corridor criteria C1–C4, their thresholds and the choice rule of `day_pattern_corridor_analysis_protocol_v0.md` (+ Addendum A) are unchanged and are applied to the corridors this screen proposes.*

## 1. Data

**Days and lanes:** the 20 screening Wednesdays of 2023 (1st and 3rd Wednesday, Feb–Nov), on the screening's station set (928 stations in the 440 windows).
- One lane per station, the lane the screening used: available that day, middle lane first.
- Its occupancy is cached. **30-s counts are added for exactly those lane-days: 14,488 new requests** (798 are already cached). Fetched at ≤ 5 req/s.

**What is known in advance:** only the occupancy-based screening shares (`day_pattern_screening_v0.json`) and the three corridors already analysed. Disclosed.

## 2. Bottleneck detection (the same definitions as the corridor protocol §1, on one lane)

**Lane speed:** v = q / k, with
- q = 12 × the counts in a 5-min bin;
- k = (occupancy / 100) × 5,280 / L_field.

Bins run 05:00–23:00; a bin is valid with ≥ 9/10 values present. A station-day is valid with ≥ 90 % of its bins valid.

**Pairs:** consecutive screened stations (u upstream, d downstream) along each MnDOT corridor, in configuration order, with d − u ≤ 3 km, and both valid that day.

**Active bottleneck:** v_u < 40 mph and v_d − v_u ≥ 20 mph, in ≥ 5 of 7 consecutive bins.

**Candidate bottleneck:** a pair valid on ≥ 15 of the 20 Wednesdays and active on **30–90 %** of them (the C1 band).

## 3. Feasibility (configuration and the cached availability lists only; no requests)

A candidate is **feasible** if all three hold:
1. **Feeding ramps:** ≥ 2 metered entrances lie in [km_u − 6 km, km_d].
   - The nearest of them is within 2 km upstream of d, which makes the pair plausibly that merge's bottleneck.
   - Each has ≥ 1 Queue and ≥ 1 Passage detector in the configuration.
   - These detectors appear in the MnDOT archive list of ≥ 90 % of the 20 days. That is a pre-filter for C2, which itself is applied later on real data.
2. **A long approach:** the configuration has mainline stations ≥ 10 km upstream of the first feeding ramp (the author's long-road requirement).
3. **Downstream observability:** at least 2 more stations with configuration detectors downstream of d, within 5 km.

## 4. Ranking and proposal (fixed now)

1. **Merge near-duplicates:** on the same route and direction, candidates whose u lie within 3 km of each other are merged, keeping the one with the most active days.
2. **Rank the feasible candidates** by:
   1. |share of active Wednesdays − 0.5|, smallest first;
   2. number of feeding metered ramps (max 3), largest first;
   3. median v_d − v_u over its activation bins, largest first.
3. **The top 3 are proposed for the corridor analysis.** Each corridor is defined as:
   - **meters:** its 2–3 feeding ramps nearest to d;
   - **mainline:** from 4 km upstream of the first feeding ramp, through d, plus the next 2 stations;
   - **detectors:** all ramp detectors of those meters, and the exits in that range.

   The 104-day pull for each is made only if it is **≤ 12,000 requests per corridor**. That is the author-approved "about 10k per corridor" plus a 20 % margin. If larger, the count is reported and the author decides.
4. **If no candidate is feasible:** report the counts at each filter step and stop. No threshold is relaxed.

## 5. Outputs

- `docs/plans/day_pattern_bnscreen_v1.json`: summary; the candidate and feasibility tables; the top 3 with exact request counts.
- A ledger row for the pull and one for the screen.
- Code: `vsl_lab/data/bn_screen.py`.

## Addendum A (2026-10-05, code review before the screen ran; no result existed)

An adversarial review (workflow `wf_f8bed967-0ce`) confirmed 7 findings, 5 of them distinct. All were fixed **before the screen ran**, so no result is affected:
1. **Request count.** It now counts only detectors in that day's MnDOT archive list, exactly what the pull fetches. The old count was 0–37 % too high and could wrongly mark a corridor as over the 12,000 cap.
2. **Ranking.** Key 1 now uses the exact distance |active/valid − 0.5| (a fraction), so exact ties reach key 2. The same fix is in the corridor-analysis choice rule.
3. **Exits.** The top-3 corridors include exits over the whole mainline range (§4.3), not only to last ramp + 2 km (`corridor_detectors(..., exit_down_km)`).
4. **Pull keys.** The `pull --from-bnscreen` keys are unique per corridor (route, direction, u label). Two top-3 corridors on one route no longer overwrite each other.
5. **Over-cap corridors.** Over-cap corridors are not analysed; they are listed as "author decision pending".

The protocol text is unchanged; these fixes make the code follow it.

## Addendum B (2026-10-05, after the first screen run; a bug found after results)

**First run** (`day_pattern_bnscreen_v1_asrun.json`):
- 893 pairs → 53 candidates → 23 feasible;
- top 3: U.S.169 SB Anderson Lakes Pkwy, I-494 NB S of Co Rd 6, I-94 EB Riverside Ave.

**Artefact.** The I-94 EB downstream station (Huron Blvd) reports **zero counts and zero occupancy on all 20 days**. A dead detector's zeros passed as "present values", k = 0 was read as free flow, and so every slowdown upstream counted as an active bottleneck. 85th St (I-35W NB, rank 4) is dead on 10 of 20 days.

**Fix** (the rule C2 already uses for ramp detectors, `ramp_valid`): a lane-day whose counts sum to zero over 06:00–20:00 is **invalid**.
- In the screen, that station-day is invalid.
- In the corridor analysis, any dead lane makes the station-day invalid, since a station is valid only if every lane is.

**Both outcomes logged:** the screen and the corridor analysis v1 are re-run with the fix.
