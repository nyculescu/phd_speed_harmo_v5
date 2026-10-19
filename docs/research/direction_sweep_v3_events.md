# Direction sweep v3: five directions after the margin theme (V87, 2026-10-18)

**Method.** Three independent scouts: vehicle level, traffic-system level, and an open search. Each scored about 6 directions on gates G1–G6 (V86 plus G6, "adaptation pays"). The main session combined their results.

**Evidence quality.** Search snippets and abstracts only; no full papers or datasets were read. arXiv counts are lower bounds, because transport work is mostly published in journals. No headroom has been measured for any direction. Treat every number as [VERIFY].

## The pattern found independently by all three scouts (reasoning, not measured)

- **Recurring variety** (time of day, site, weather, vehicle class) can be observed or predicted. A table tuned once matches adaptation there; this is why the margin theme failed.
- **Non-recurring events** (detector faults, incidents, work zones, waves arriving now) cannot be planned for. That is where adaptation can pay.

Archived support (claude/day-pattern-core, D5.10, chapter level, BN4 single merge): a learned meter beat the best tuned non-learning arm by 17–28 % in the "slow" and "block" perturbations. In "none" and "surge" it did not beat the best non-learning arm (a constant rate in both).

## The five directions

| # | Direction | G6 | Crowding | Plant / data | Main risk | Kill test |
|---|---|---|---|---|---|---|
| 1 | **Ramp metering (and signals) that survives detector faults** | 7–8 | low for ramp metering (0 arXiv hits with faults); moderate for signals | SUMO; PeMS health flags give real fault onsets and durations | a fixed fallback rate may come within 10 %; a TTI study found fixed rates best on congested ramps [VERIFY] | oracle vs fallbacks on one merge, ~1 day build, < 1 h compute |
| 2 | **Control during incidents and demand surges** | 7 | moderate (LLM incident control is trending) | SUMO with random incidents; real incidents too rare for a big real-data test | max pressure, plus incident-plan tables | hindsight-optimal vs max pressure, 1–2 days |
| 3 | **Early wave absorption from delayed downstream data** | 6 | high (CIRCLES) | I-24 + SUMO | scoop; a simple smoother may capture most of the gain | oracle wave timing vs fixed smoother, ~1 day |
| 4 | **Inferring the human leader's current driving regime** | 6 | moderate | highD/NGSIM replay | a normal following gap may absorb the leader's variation | oracle future leader vs best fixed predictor, 1–2 days |
| 5 | **Work-zone speed or merge control** | 7 | low | SUMO only; no public work-zone data | results depend entirely on the simulator | transfer vs per-site tuning over 10 closures, ~2 days |

Directions 1, 2 and 5 form one family: "adaptive control when the normal plan is wrong".

**Dropped by the scouts:**
- probe-based signal timing (Google Project Green Light; Michigan with GM);
- the original coordinated freeway zones (1.5–6 % prior);
- bus bunching, merging, emergency vehicles, mixed fleets, cyclist overtaking, few-shot site transfer, and anti-exploitation gap policy (each either repeats "a table wins" or has no data or plant).

**Next (V88):** a draft screen for direction 1: `docs/research/protocols/screen_D1_detector_faults_draft.md`.
