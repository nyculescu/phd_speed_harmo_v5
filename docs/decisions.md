# v5.B.1 decision log

Author decisions, newest last. "Open" items need the author before they bind. B1–B15 (`docs/v5b/design_v0.md` on
`claude/v5b-core`) are draft inputs until re-confirmed here.

| # | Date | Decision | Status |
|---|---|---|---|
| V1 | 2026-10-13 | Branch `v5b1`, empty history, becomes the main branch; pushed to GitHub (default-branch switch pending, `gh` not installed) | decided |
| V2 | 2026-10-13 | The CORR2X network evolves into **F4R1M** ("Freeway, 4 ramps (2 on, 2 off), 1 merge") | decided; open: does "1 merge" mean the 3→2 lane drop? |
| V3 | 2026-10-13 | **Action granularity: per-CAV commands** (accelerate / hold / brake in ±5 km/h steps). Lane/segment-level CAV targets were tried earlier and failed (author's experience, not a re-checked log) | decided |
| V4 | 2026-10-13 | **No control (NC):** no speed limit beyond the network maximum and no speed set for any vehicle; every vehicle obeys the network maximum of **120 km/h** | decided; open: 120 vs 100 km/h; ramp meters in NC (assumed off, always green) |
| V5 | 2026-10-13 | **HDV lane limits** as in v5: set the lane's maximum speed to the imposed limit; HDVs comply partly (speed-factor spread). Full compliance is not wanted: the noise is part of the problem a smart controller must handle | decided; open: how CAVs are kept outside lane limits (SUMO check in T0) |
| V6 | 2026-10-13 | **Invalid run:** more than 2 collisions or teleports invalidate a run. A collision can happen through HDV non-compliance | decided; open: count combined or each; how an invalid run enters the paired statistics |
| V7 | 2026-10-13 | **Multi-agent API: PettingZoo** | decided; open: install location (venv314 is shared with v6), trainer, who is an agent (zone or CAV) |
