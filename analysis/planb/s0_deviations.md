# Plan B S0: findings against the protocol text

Found while building S0. None changes a cell, opponent, measure, margin, n or m unless the author decides so; each needs a V# before S1 (planb.md §11).

| # | Protocol text | Finding | Proposed handling |
|---|---|---|---|
| D1 | §4.2: "Spec test: exactly 10 distinct trucks per seed, all departing before 1,200 s"; "the 80-s grid rarely runs out of trucks" | Measured over all 1,000 seeds of the block (pure Python, the selection rule as written): 10 distinct trucks on every seed, but the 10th departs at or after 1,200 s on 9.4 % of seeds (median 1,115 s, 90th percentile 1,197 s, 99th 1,306 s, max 1,427 s). A truck departing at 1,427 s reaches merge 2 at about 1,904 s, after the window. With a 70-s grid: 1.7 %; 75 s: 3.7 %. | Keep the rule (the cell is the same for every arm on a seed, so no arm gains); correct the spec test to "10 distinct trucks, each departing at or after its slot and before 1,800 s"; report per seed the departure of the last truck. |
| D2 | §5: `stuck_n` = "vehicles below 0.1 m/s for 300 s or more while their leader within 50 m moves" | Taken literally it misses a vehicle stopped at a lane end with no leader on its lane, which is the deadlock the gate is for. Built as: below 0.1 m/s for 300 consecutive seconds and not behind a stopped leader (below 0.1 m/s) within 50 m; a moving leader or no leader within 50 m both count. | Accept the built definition (it counts everything the literal one counts, plus lane-end deadlocks). |

| D3 | (bug, not a protocol change) | The crash check found that `Perturb.step` dispatches to a method named `_<kind>`, so the demand helpers named `_surge` and `_truck_fixed` were also called every second (TypeError). Renamed `_demand_surge` / `_demand_truck_fixed`; a regression test pins that `step` is a no-op for the demand kinds. No run had used them. | none |
| D4 | §3.3: "`--cond` (cma2.py:405) and `common.COND` gain the new cells; `alks_full_moving` added to `KEYS` (cma2.py:45)" | Built as a separate script, `planb/cmab.py`, that imports cma2's functions and fixes every protocol setting in code (seeds, population, generations, checks, losses, admission, plateau thresholds), so a search cannot be launched with other settings; cma2.py is unchanged. `common.COND` gains SURGE and TRUCK. | Accept (same behaviour, fewer ways to misconfigure). |

## Build-check runs (ledger)

| Date | Runs | Seeds | What | Result |
|---|---|---|---|---|
| 2026-11-08 | 7 | stored (round 2 test/band, 7,440,840 and 7,440,880) | measure2 smoke at the Plan B code (perturb kinds, set reorder, pack keys) | every round 2 key equal (SMOKE PASS); old pack keys equal the S0 rental's rows except `m_dec_entropy_mean` on 4 policy rows (about 1e-9) |
| 2026-11-08 | 7 | the same | measure2 smoke at 79b889b on the laptop | every key, old pack keys included, equal to the Plan B code's rows: the entropy difference is laptop against EPYC floating point, not the code |
| 2026-11-08 | 6 | 7,480,000 (S1 smoke seed) | crash check: placeholder ASCH and v3w learner w0u250 in TRUCK, MPC-F data mode in SURGE, pack on; 3 runs, then the same 3 again | first attempt: all 3 crashed (D3); after the fix all 3 complete; 10 capped trucks at 40.0 km/h at most, 0 planned vehicles dropped, 0 stuck, 4 MPC-F holds |
| 2026-11-08 | 1 | 7,480,000 | the placeholder ASCH in TRUCK again, with an input diagnostic | inputs read at 300 decisions (empty bins only at the first); no switch. Seen in passing: the diagnostic's zone minimum speeds (78.7, 63.8, 59.6 km/h) for this one run; no gate quantity was computed |

The runs sum to 21 (7 + 7 + 6 + 1), as V481 records. Seed 7,480,000 is the S1/S5 smoke seed (§6); running it in S0 departs from §7.1 ("no simulation except unit tests"), which V481 noted as logged but no V# records as a deviation yet (review F26).
