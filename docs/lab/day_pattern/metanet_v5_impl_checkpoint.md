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
