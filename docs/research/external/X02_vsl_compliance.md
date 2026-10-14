# X02: driver compliance with variable speed limits, with and without average-speed cameras

**Model:** Opus 5.5 · web search ON (max 25) · effort high · max tokens 16,000 · system prompt: Shared rules (README)

## Prompt (paste as the user message)
```
I am modelling motorway variable speed limits (VSL) as a comparison case in a microscopic traffic simulation, on a corridor inspired by Dublin's M50 (100 km/h limit; the real M50 has had a VSL system called eMOS since 2021, with lane-control signs on gantries). I need EMPIRICAL evidence on how well drivers comply with the displayed limits, in two cases:
(A) VSL alone, enforced only by ordinary policing or occasional spot cameras;
(B) VSL combined with average-speed (section) enforcement cameras.

Find and report:
1. Measured compliance with VSL in (A): share of vehicles at or below the displayed limit, mean speed relative to the limit, speed standard deviation, by limit level (e.g. 60/80/100 km/h) where available. Look for UK managed / smart motorways (M25, M42, M1, M6), Netherlands, Germany (Streckenbeeinflussungsanlagen), Sweden, Denmark, Australia, the USA, and Ireland's M50 eMOS if anything is published (TII reports, academic or press evidence).
2. The same measures under (B): UK variable average-speed enforcement (e.g. HADECS / SPECS on smart motorways), Austria (Section Control), the Netherlands (trajectcontrole), Italy (Tutor), Scotland (A9). Include before/after or with/without comparisons.
3. Effects on traffic flow, not only speed: does better compliance change capacity, the onset of breakdown, stop-and-go waves, travel time or crash rates? Give numbers with the setting.
4. How microsimulation studies represent compliance (e.g. a distribution of desired speed relative to the displayed limit, a compliance rate parameter), with the values they used and whether they were calibrated on field data.
5. A summary table: case (A) vs case (B), one row per study: country, road, metric, value, year, source.

Rules: give the year of each study; flag old (pre-2010) data; separate measured field data from simulation assumptions; do not merge numbers from different metrics. If no published evidence exists for the M50, say so plainly.

Length: at most about 3,500 words.
```

## Output (pasted by the author, date: )
