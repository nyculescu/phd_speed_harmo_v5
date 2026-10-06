# Day-pattern project: learning daily demand patterns for corridor control

*Branch `claude/day-pattern-core` · started 2026-10-05 · repo v5 (v6 is assigned to traffic lights and intersections) · the author's "big bump": treated as a new project inside v5*

## What it is

**Demand over a day has a shape:** one peak, two peaks (the weekday M), slopes, or near-flat. The shape differs from day to day in height, width, timing and rise and fall rates.

**Detectors at a bottleneck cannot count more than the road carries.** So on heavy days they hide how big and how early the true peak is.

**This project asks whether a controller that learns these patterns can control a real-world corridor measurably better than the best tuned proven controllers.** The corridor has 2–3 metered on-ramps and speed harmonisation upstream, and is controlled over whole days. The learning-based component either acts as a co-controller or feeds information to the proven controller.

**What counts as a thesis result** (author, 2026-10-05; `docs/plans/day_pattern_decisions_v0.md`, D1):
- a controller that relies on or integrates **DRL**, measurably beating every tuned opponent in a pre-registered, confirmatory test;
- supervised neural-network hybrids are opponents or complements. They become the target only if the DRL route fails;
- only positive DRL results count; a KILL ends a line of work early and is not written up as a paper.

## Design in one table

| Element | Choice | Where |
|---|---|---|
| Main bet | **H1:** HERO coordinated ramp metering + a DRL day-pattern scheduler (co-controller), with secondary surprise events (R6's idea re-tested on a realistic road) | `docs/plans/hybrid_combinations_v0.md` §2 |
| Alongside | **H2 tool checks:** MTFC speed limits + ALINEA, with DRL supplying the day's capacity estimate | same, §3 |
| Plant | **METANET** calibrated to a real MnDOT corridor for the gate; **SUMO** confirmation, if it passes realism (P6b) | `docs/plans/day_pattern_plants_v0.md`, gate draft §1 |
| Days | real Minneapolis demand reconstructed, a flexible multi-peak model fitted; train on generated days, test on real 2024 days; full days | gate draft §2 |
| Opponents | timetables, first-hour pattern matching, tuned ALINEA/HERO, adaptive ALINEA, forecast MPC, LSTM-informed HERO, classifier-triggered HERO, imitation of the informed reference, ARS, DRL alone | gate draft §3 |
| Gate | informed reference (true demand) vs best opponent; KILL if < 10 %; two looks (all days, heavy days), each at 97.5 % | gate draft §4 |
| The timing problem | a learnability ladder (flat → step → ramp → one peak → two peaks → full day), aimed at the hybrid's DRL layer; cheap rungs alongside the gate | thesis path §5 |

## Status (2026-10-06)

- **Done:**
  - literature review: `docs/review/day_pattern_research_v0.md`;
  - plant options;
  - the SUMO discharge pre-check (P3-ALIVE: car-following is not the problem, merges are; `docs/lab/day_pattern/p3_precheck.md`);
  - MnDOT screening, corridor analyses v0–v2, corridor **U.S.169 SB** (two bottlenecks in series; decisions D3.1–D3.5);
  - METANET protocol v3 (binding), pre-calibration facts, calibration (8 CMA-ES restarts; J = 0.1649).
- **METANET route: STOPPED (2026-10-06, D4.1).** The gated step-halving check failed (N0, §2.5): halving the time step changes the set of calibration days with a model B2 episode (20230517). Finer steps agree with each other, so the 5-s plant is not converged inside the B2 queue. The protocol makes this a route stop before any validation run; the author accepted it as pre-registered. No validation day was simulated. Record: `docs/lab/day_pattern/metanet_calibration.md`.
- **Next (D4.2–D4.5):** a pre-registered, KILL-only **prize screen** on a fast, optimistic plant (seeds 7,191,xxx). If it does not KILL, METANET v4 follows as the gate plant (P6b unchanged). The E15–X15 lane check comes first. Study: `docs/lab/day_pattern/next_plant_study_v0.md`.

## Documents, in reading order

1. `docs/plans/day_pattern_idea_v0.md`: the original idea (M, ^, /, \, capacity-clipped peaks).
2. `docs/plans/Thesis path with daily patterns (human).md`: a plain-language thesis path (claim, timing problem, kill points).
3. `docs/plans/day_pattern_decisions_v0.md`: **every author decision, dated.**
4. `docs/plans/hybrid_combinations_v0.md`: H1–H4, factor roles, DRL defaults, neural components beyond RL (§1.6).
5. `docs/review/day_pattern_research_v0.md`, plus its notes in `docs/review/day_pattern_notes/`: the literature (Harvard references; [VERIFY]/[SAGE] tags).
6. `docs/plans/day_pattern_plants_v0.md`: plant options and costs.
7. `docs/plans/day_pattern_gate_draft_v0.md`: the gate **draft**. Deliberately uncommitted until the corridor is chosen; it becomes a protocol only when committed before any run.
8. `docs/plans/day_pattern_corridor_selection_v0.md`, `…_screening_v0.json`, `…_shortlist_v0.json`: MnDOT access (Mayfly) and the screening.
9. `docs/plans/day_pattern_corridor_analysis_protocol_v0.md` (+ Addendum A), `…_v0_asrun.json`, `…_v1.json`: corridor choice.
10. `docs/lab/day_pattern/`: the P3 pre-check protocol and results.

## Code

| Path | Purpose |
|---|---|
| `vsl_lab/data/mndot.py` | MnDOT Mayfly fetcher (≤ 5 req/s, disk cache), windows, screening, corridor detector sets, pulls |
| `vsl_lab/data/corridor_analysis.py` | corridor criteria C1–C4 and the reported items |
| `vsl_lab/jobs/dp_jamrelease.py` | SUMO single-lane queue-discharge pre-check |
| `vsl_lab/plants/metanet.py` | METANET plant of U.S.169 SB (protocol v3) |
| `vsl_lab/data/metanet_inputs.py`, `metanet_events.py`, `metanet_facts.py` | data layers, event comparison, pre-calibration facts |
| `vsl_lab/jobs/metanet_calibrate.py`, `metanet_postcal.py`, `metanet_freeze.py` | CMA-ES calibration, step-halving / grid / profiles / step probe, freeze and stop record |
| `vsl_lab/jobs/metanet_gate.py` | plant gate (§5); written and smoke-tested on calibration days only; never run (route stop; it refuses to run) |
| `vsl_lab/ops/guard.py`, `vsl_lab/ops/scheduler.py` | compute guard (CPU > 90 % for 2 min; 95 ± 3 °C) and batch runner |

Lab infrastructure (runner, health checks, ledger, statistics, trainer with the S0 fixes) is shared with the VSL lab under `vsl_lab/`.

## Data, seeds, ledger

- **Raw data** (outside the repo, ext4): `/home/catalin/work/phd/dp_data/mndot/`.
  - **2023** is for screening, fitting and tuning; **2024** is reserved for the gate.
- **Seeds:** 7,190,000–7,190,999 (approved 2026-10-05):
  - 000–099 plant and tool checks (7,190,000–010 used by the P3 pre-check);
  - 100–299 tuning;
  - 300–499 validation;
  - 500–699 gate;
  - 700–999 reserved.
- **Ledger:** `vsl_lab/runs/ledger.csv`, track **DP**. Every batch, pull and analysis is logged, including failures.

## Rules

The rules are `CLAUDE.md` in full:
- protocol before data;
- tuned opponents on separate seeds;
- paired seeds, medians, bootstrap CIs;
- a bug after results means fix, re-run and log both;
- the compute guard;
- [VERIFY] for anything not read in full;
- no "first/novel" claims.
