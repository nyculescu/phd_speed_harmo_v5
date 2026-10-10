# METANET v5 implementation: checkpoint (resume here)

Protocol: `docs/plans/day_pattern_metanet_protocol_v5.md` (binding, commit f7fe73b, D4.14). Phase: coding (High effort, ultracode off). No real day is simulated in this phase; no run launches before the code-review checkpoint (§B8 step 3).

## Plan (slices; each ends with tests passing and a local commit)

| # | Slice | Files | Status |
|---|---|---|---|
| A | Pure J5 item functions (taper, caps, P3/P4/P5a/P5c/P7a/P7b/P7c items, creditability per episode with the head rule, shaping g/h/s, hinges, realism rows, aggregation J5/J_d, parity ω_k, facts-hash guard) + synthetic tests (parts of 24-29, 31, 35, 40) | new `vsl_lab/jobs/metanet_j5.py`, new `tests/test_metanet_v5.py` | in progress |
| B | Gate refactor: per-day item functions shared by `metanet_gate.deterministic()` and J5; test 30 (bit-for-bit vs tag `metanet-v4-stop`) | `metanet_gate.py` | todo |
| C | Real-side facts `metanet_v5_precal_facts.json` (§B1.1) + J5 evaluator wiring into `simulate()` (cells 25-39 recorded) + CMA-ES driver on seeds 7,192,010-017 | new job module | todo |
| D | Step-halving (§B4), screen (§B5), ensemble/members + gate guard (§B6, §B8, test 36), route labels (test 39), premise check (§B7) | jobs | todo |
| E | Synthetic timing (§B12), adversarial code-review checkpoint (ultracode on), then the author's go | — | todo |

Rule for a resumed session: read this file and the protocol sections named in the slice; run `tests/test_metanet_v5.py`; continue the first slice not marked done. Never push without the author.

## Log
- 2026-10-09: checkpoint created; slice A started.
- 2026-10-09: slice A done. Item functions are pure (episode lists, per-episode Q_dis, cell matrices in; items out); P8g, P5c/P7b inputs (ratios, extent index error) and the real-side facts come in slices B-C. Next: slice B (gate refactor + test 30).

## Side study G-1 (SUMO 3-lane merge geometry/demand; author 2026-10-09; seeds 7,170,000-999 approved)
- S0 demand extremes: done (168b2e6), `docs/lab/g1_demand_extremes.md`. Sharp transitions; H5 shows a capacity drop in several layouts, H3 none. Open check: lanedrop results identical across ramp levels (inert ramp?).
- Next: S1 pre-registration (refine main_peak in 200 veh/h steps inside the H5 brackets, ≥ 10 seeds 7,170,100+), controllers nc + MTFC tuned + constant-VSL grid + "artificial DRL" oracles (O1 best constant per seed; O2 timed oracle around the seed's NC onset), labelled upper bounds; KILL if oracle gap over tuned classical < 10 %. Then length sweep (acceleration lane, downstream) only if S1 shows headroom.
- S1 done: all 5 cells KILL (H ≤ 0.2 % in 4; Z9 5.8 % [0, 27]); `docs/lab/g1_s1.md`. Length sweep not licensed. Open: author decision on Z9 follow-up.
- S2 done: Z9 KILL (H 1.6 % [0, 3.6]); **G-1 line closed** (`docs/lab/g1_s2.md`). Resume the main plan at slice B.
