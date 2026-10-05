# Corridor analysis: results (v0 as run, v1 after the data-extent fix)

*2026-10-05.*
- *Protocol `day_pattern_corridor_analysis_protocol_v0.md` (commit `c4280b6`, before any criterion was computed), Addendum A (`7f6478e`, before the re-run).*
- *Data: MnDOT 2023, 104 days (52 Wednesdays, 26 Saturdays, 26 Sundays).*
- *Summaries: `day_pattern_corridor_analysis_v0_asrun.json` and `…_v1.json`.*

## Verdict: no corridor is eligible, in both v0 and v1. No criterion was relaxed.

| Corridor | C1 recurrent, variable bottleneck (30–90 % of Wednesdays) | C2 ramp demand reconstructable | C3 upstream boundary free (reported) | C4 capacity drop r ∈ [0.82, 0.97] | Why it fails |
|---|---|---|---|---|---|
| **I-35W SB** | **FAIL:** 2/52 (B = T.H.280 → Industrial Blvd) | PASS (all 1.0) | 0.88 (extension available to −11 km) | FAIL (n = 2) | The morning slowdown is **spread over ≥ 9 km** (45–56 mph from Industrial Blvd to University Ave) with no ≥ 20 mph speed jump. The occupancy screen saw "congestion", but there is no pinned active bottleneck. |
| **I-394 WB** | **PASS:** 19/50 = 0.38 (B = Shelard Pkwy → Co Rd 73, PM, onset ≈ 16:00) | **FAIL:** Louisiana Ave queue detectors have no data (0.0); the others are 0.96–1.0 | PASS (0.96) | **PASS:** median r = 0.968 (IQR 0.950–0.999), n = 19 | C2 only. Also, only 1 of its 3 metered ramps (Louisiana Ave) feeds B. |
| **T.H.100 SB** | **FAIL:** no observable bottleneck | PASS (all 1.0) | 0.88 | — | The queue head is at the corridor's end (77th St). MnDOT has no station downstream of it, and "N of I-494" has no 2023 data. |

**What changed from v0 to v1:**
- the downstream stations were added (data-extent fix), and five code-review fixes were applied (Addendum A);
- C2 shares are now Wednesday-only. For example, I-394 WB Co Rd 73 moves from 0.98 to 0.96;
- day-shape counts: I-394 WB Wednesdays went from M = 52 to M = 37, plus 15 days with 3–4 peaks, now labelled "other";
- **no verdict changed.**

## What the real data say (reported items; useful whichever corridor is chosen)

**I-394 WB, the one site with a measurable pinned bottleneck:**
- **queue discharge ≈ 1,886 veh/h/lane;**
- pre-breakdown 15-min capacity ≈ 1,988 veh/h/lane;
- **capacity drop ≈ 3 %** (median r = 0.968);
- episodes are 65 min (median).

This is the realistic target a simulated plant must reproduce. It sits inside the realism gate's 1,600–2,400 band, and at the low end of the 3–18 % drop range.

**The "M to trapezoid" question (author, 2026-10-05), on I-394 WB Wednesdays.** By quartile of daily demand at the upstream boundary:

| Demand quartile | Share of Wednesdays with a breakdown | Median congested minutes |
|---|---|---|
| Q1 | 8 % | 0 |
| Q2 | 33 % | 0 |
| Q3 | 58 % | 40 |
| Q4 | 54 % | 45 |

The Spearman correlation between total demand and congested duration is ρ = 0.41. Breakdown switches on over a narrow band of daily demand, between Q1 and Q3: a total-demand difference of about 16 % (33.6k → 38.9k veh). That fits the author's "narrow band" observation. On this site the PM peak breaks down and the AM peak does not, so no Wednesday had both an AM and a PM episode.

**Day shapes at the boundary:**
- Wednesdays are almost always two-peaked: I-35W SB has 49/52 M; I-394 WB has 37 M plus 15 with three or four peaks (a late-evening bump).
- Weekends are flat, one-peaked or irregular.

**Data quality to remember:** some stations report impossible free-flow speeds (Winnetka Ave 157 mph; I-35W SB upstream 82–88 mph), which points to field-length errors. They need recalibration before any speed-based use.

## The lesson for the next selection

The shortlist was built from windows of consecutive metered ramps, scored by occupancy. That finds **congested** stretches, not **pinned bottlenecks with metered ramps feeding them**. Two of the three candidates failed for exactly that reason (a spread-out slowdown; a queue head at the edge of the data). The third had the bottleneck upstream of most of its ramps.

**A better order:**
1. find the pinned active bottlenecks first, with the speed-differential rule on counts plus occupancy;
2. only then keep those with 2–3 metered ramps upstream, healthy queue and passage detectors, and a free-flowing approach ≥ 10 km long.

## Options (author's choice; request counts exact for the 104-day set)

| Option | What | MnDOT requests | Time at ≤ 5 req/s |
|---|---|---|---|
| **(a)** As the protocol says: analyse shortlist #4–#8 (T.H.36 WB, T.H.62 EB, I-94 WB, I-35E NB, I-94 EB) | 104 days × every detector of each window | **58,656** | ≈ 4–5 h |
| **(b)** Recommended: a **bottleneck-anchored network screen**. Add 30-s counts to the screening's 20 Wednesdays (occupancy already cached), apply the speed-differential rule metro-wide, keep bottlenecks with 2–3 healthy metered ramps upstream, then run the corridor analysis on the best 1–3 | **15,291** now, then about 10k per chosen corridor | ≈ 1.2 h, then about 1 h per corridor |
| (c) Bottleneck-anchored I-394 WB: re-window around Shelard Pkwy with the metered ramps upstream of it | small (the config shows which ramps exist; data partly cached) | minutes | Louisiana Ave's missing queue data probably still fails C2 |

Option (b) needs a short protocol v1 (selection procedure only; C1–C4 unchanged), committed before the pull.
