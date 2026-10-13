# v5.B.1 decision log

Author decisions, newest last. "Open" items need the author before they bind. B1–B15 (`docs/v5b/design_v0.md` §2 on
`claude/v5b-core`) are draft inputs until re-confirmed here. Review findings are in `docs/architecture/review_v0.md`.

| # | Date | Decision | Status |
|---|---|---|---|
| V1 | 2026-10-13 | Branch `v5b1`, empty history, is the main branch and the GitHub default (confirmed `origin/HEAD → v5b1`) | decided |
| V2 | 2026-10-13 | The CORR2X network evolves into **F3Z** ("Freeway, 3 zones"). Supersedes the name F4R1M proposed the same day | decided |
| V3 | 2026-10-13 | **Action granularity: per-CAV commands** (accelerate / hold / brake in ±5 km/h steps). Lane/segment-level CAV targets were tried earlier and failed (author's experience, not a re-checked log). Zone-level agents also "almost failed" (author) | decided |
| V4 | 2026-10-13 | **No control (NC):** no speed limit beyond the network maximum, no speed set for any vehicle, **ramp meters off (always green)**. NC is not used in training; it is used in evaluation (the D5.8 denominator, extremes) | decided |
| V5 | 2026-10-13 | **HDV lane limits** as in v5: set the lane's maximum speed; HDVs comply partly (speed-factor spread). Full compliance is not wanted: the noise is part of the problem. **CAVs are kept outside lane limits by speed mode 95** (verified 2026-10-13 in SUMO 1.27.1, single vehicle, lane max 72 km/h: `setSpeed(108)` reaches 72 under the default mode 31, 108 under mode 95; mode 95 kept the safe gap behind a slower leader) | decided |
| V6 | 2026-10-13 | **Invalid run:** more than 2 collisions, or any teleport (> 0). A collision can happen through HDV non-compliance | decided; open: how an invalid run enters the paired statistics |
| V7 | 2026-10-13 | **Multi-agent API: PettingZoo.** Direction: **each CAV is an agent** | decided; open: the trainer (PettingZoo is an API, not a trainer); who sets HDV lane limits and meters |
| V8 | 2026-10-13 | **No pause gate.** Controllers are always active; they must learn when to start controlling, before the jam forms. (The answers given for a gate: one shared rule, no pause in a full jam, release CAVs / lanes to max / meters green while paused, are kept only in case a gate is reconsidered) | decided |
| V9 | 2026-10-13 | **Retire the word "demand"** in the design: the controller must not be told the inflow; it learns from what it measures | decided; open: the replacement term |
| V10 | 2026-10-13 | **New metric: energy use** (ICE and electric), including acceleration and braking; the author's most important metric for speed harmonisation. From SUMO if available, else a published model | decided; open: model choice, unit (energy per vehicle-km vs power), and its role in the D5.8 bar |
| V11 | 2026-10-13 | **Hard braking measured on CAVs** | decided; open: threshold; whether HDV braking is also reported |
| V12 | 2026-10-13 | **No step 0 run now.** Gather information and design first; NC is defined for evaluation later | decided |
| V13 | 2026-10-13 | **Network maximum speed 120 km/h**, a variable that may change later (e.g. 100 km/h) | decided |
| V14 | 2026-10-13 | **Separate Python environments** for v5.B.1 and v6, accepting duplicated disk and memory use | decided |
