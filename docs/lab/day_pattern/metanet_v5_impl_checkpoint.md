# METANET v5 implementation: checkpoint (resume here)

Protocol: `docs/plans/day_pattern_metanet_protocol_v5.md` (binding, commit f7fe73b, D4.14). Phase: coding (High effort, ultracode off). No real day is simulated in this phase; no run launches before the code-review checkpoint (§B8 step 3).

## Plan (slices; each ends with tests passing and a local commit)

| # | Slice | Files | Status |
|---|---|---|---|
| A | Pure J5 item functions (taper, caps, P3/P4/P5a/P5c/P7a/P7b/P7c items, creditability per episode with the head rule, shaping g/h/s, hinges, realism rows, aggregation J5/J_d, parity ω_k, facts-hash guard) + synthetic tests (parts of 24-29, 31, 35, 40) | new `vsl_lab/jobs/metanet_j5.py`, new `tests/test_metanet_v5.py` | in progress |
| B | Gate refactor: per-day item functions shared by `metanet_gate.deterministic()` and J5; test 30 (bit-for-bit vs tag `metanet-v4-stop`) | `metanet_gate.py`, new `metanet_items.py`, new `tests/test_metanet_gate_refactor.py` | **done** (test 30(a): 29/30 synthetic worlds identical; 1 world = latent tag crash, fixed); test 30(b) (J5 items = gate statistics) moves to slice C with the J5 evaluator |
| C | Real-side facts `metanet_v5_precal_facts.json` (§B1.1) + J5 evaluator wiring into `simulate()` (cells 25-39 recorded) + CMA-ES driver on seeds 7,192,010-017 | `metanet_v5_facts.py`, `metanet_j5_eval.py`, `metanet_v5_calibrate.py` | **code done**; facts built into the raw dir only (commit at §B8 step 4, after the code review, with `metanet_v5_precal_facts.sha256`); open: test 30(b), test 24 (zero cost), timing |
| D | Step-halving (§B4), screen (§B5), ensemble/members + gate guard (§B6, §B8, test 36), route labels (test 39), premise check (§B7) | `metanet_v5_freeze.py`, `metanet_v5_gate.py`, gate `ctx` path | **partly done**: route labels (t39), step-halving rule + runner (t37), premise check (not run), screen via gate ctx (t34), members rule, pure gate guard (t36). §4.7 grid computes J_d + b1cells_qual (v5 hook; v4 default unchanged), estimator takes selector "J_d", c1-inert reports. freeze orchestration (`finalize`: stops in order, lazy; grid CLI per c2 slice; record to `metanet_v5_calibration.json`; stop-order test). ensemble checks step (§B6, `ensemble` CLI) + members at finalize; v5 gate deterministic wiring (guard → start record → gate rows on validation days, boot seed 7,192,300, outputs in the v5 raw dir; wiring test). **Open:** v5 stochastic-row wiring (draw seed 7,192,301, v5 F̂), head-cell report (§B5), freeze-audit hook/record format (patch plant/freeze to the v5 record, start record), calib_screen_data build (not run yet) |
| E | Synthetic timing (§B12), adversarial code-review checkpoint (ultracode on), then the author's go | — | todo |

Rule for a resumed session: read this file and the protocol sections named in the slice; run `tests/test_metanet_v5.py`; continue the first slice not marked done. Never push without the author.

## Log
- 2026-10-09: checkpoint created; slice A started.
- 2026-10-09: slice A done. Item functions are pure (episode lists, per-episode Q_dis, cell matrices in; items out); P8g, P5c/P7b inputs (ratios, extent index error) and the real-side facts come in slices B-C. Next: slice B (gate refactor + test 30).

- 2026-10-10: slice B done. P4, P5a, P5c, P7a, P7b, P7c, P8 and P9's S1 now come from `metanet_items.py`, used by the gate (and by J5 in slice C). Harness: both gate versions run in one stubbed synthetic world (no real day); a planted change fails the test (mutation check). **Finding to disclose in the v5 freeze record:** the tagged gate raised `ValueError` in P9's S1 when the window [onset − 60 min, cut − 1] is empty (a model episode starting > 60 min after the real B2 cut); the refactor returns None (unscored), which was the code's evident intent. Pre-look fix; it changes no value where the tag ran. Also: `tests/test_metanet.py::test_relocation_flag_and_c2_star` had failed since the D4.10 switch (9df0d7e; v3 reading expected); now pinned to the v3 reading (v4 test 15 covers both). Full METANET suite: 64 passed. Note for future mutation checks on this exFAT mirror: mtime granularity can leave a stale .pyc; `touch` the restored source.

- 2026-10-10: slice C code done. Facts (raw dir, not committed): |R| = 18 (X-1 dropped), ω_2 = 52/9 = 5.778, U_2 = 0.4899 (as the protocol expected); P1c days with N1 − N2 < 0.02: 3, < 0: 2. Evaluator smoke on SYNTHETIC model inputs only (no candidate plant scored on real days): works; **one generation (12 × 22) = 27.6 s vs 19.9 s for the v4 J (+39 %, protocol §B12 assumed +13-17 %)** → profile and re-measure in slice E; the 24-h notice may apply. Records all 39 cells (superset of §B2's 25-39). Driver tested with a stub evaluator and a synthetic seed. J5's shaping windows now censor B1 per episode; P4 goes through `metanet_items.p4_day`.

- 2026-10-10: slice D parts 1-3 committed (route, step-halving, premise code, screen, members, guard). v5 tests 15 + refactor/screen tests 3 pass.

- 2026-10-10: slice D part 4 (grid J_d selector, c1-inert reports). Full METANET suite 71 passed.

## Side study G-1 (SUMO 3-lane merge geometry/demand; author 2026-10-09; seeds 7,170,000-999 approved)
- S0 demand extremes: done (168b2e6), `docs/lab/g1_demand_extremes.md`. Sharp transitions; H5 shows a capacity drop in several layouts, H3 none. Open check: lanedrop results identical across ramp levels (inert ramp?).
- Next: S1 pre-registration (refine main_peak in 200 veh/h steps inside the H5 brackets, ≥ 10 seeds 7,170,100+), controllers nc + MTFC tuned + constant-VSL grid + "artificial DRL" oracles (O1 best constant per seed; O2 timed oracle around the seed's NC onset), labelled upper bounds; KILL if oracle gap over tuned classical < 10 %. Then length sweep (acceleration lane, downstream) only if S1 shows headroom.
- S1 done: all 5 cells KILL (H ≤ 0.2 % in 4; Z9 5.8 % [0, 27]); `docs/lab/g1_s1.md`. Length sweep not licensed. Open: author decision on Z9 follow-up.
- S2 done: Z9 KILL (H 1.6 % [0, 3.6]); **G-1 line closed** (`docs/lab/g1_s2.md`). Resume the main plan at slice B.
