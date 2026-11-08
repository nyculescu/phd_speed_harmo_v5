# Plan B S0: findings against the protocol text

Found while building S0. None changes a cell, opponent, measure, margin, n or m unless the author decides so; each needs a V# before S1 (planb.md §11).

| # | Protocol text | Finding | Proposed handling |
|---|---|---|---|
| D1 | §4.2: "Spec test: exactly 10 distinct trucks per seed, all departing before 1,200 s"; "the 80-s grid rarely runs out of trucks" | Measured over all 1,000 seeds of the block (pure Python, the selection rule as written): 10 distinct trucks on every seed, but the 10th departs at or after 1,200 s on 9.4 % of seeds (median 1,115 s, 90th percentile 1,197 s, 99th 1,306 s, max 1,427 s). A truck departing at 1,427 s reaches merge 2 at about 1,904 s, after the window. With a 70-s grid: 1.7 %; 75 s: 3.7 %. | Keep the rule (the cell is the same for every arm on a seed, so no arm gains); correct the spec test to "10 distinct trucks, each departing at or after its slot and before 1,800 s"; report per seed the departure of the last truck. |
| D2 | §5: `stuck_n` = "vehicles below 0.1 m/s for 300 s or more while their leader within 50 m moves" | Taken literally it misses a vehicle stopped at a lane end with no leader on its lane, which is the deadlock the gate is for. Built as: below 0.1 m/s for 300 consecutive seconds and not behind a stopped leader (below 0.1 m/s) within 50 m; a moving leader or no leader within 50 m both count. | Accept the built definition (it counts everything the literal one counts, plus lane-end deadlocks). |

## Build-check runs (ledger)

| Date | Runs | Seeds | What | Result |
|---|---|---|---|---|
| 2026-11-08 | 7 | stored (round 2 test/band, 7,440,840 and 7,440,880) | measure2 smoke at the Plan B code (perturb kinds, set reorder, pack keys) | every round 2 key equal (SMOKE PASS); old pack keys equal the S0 rental's rows except `m_dec_entropy_mean` on 4 policy rows (about 1e-9) |
| 2026-11-08 | 7 | the same | measure2 smoke at 79b889b on the laptop | every key, old pack keys included, equal to the Plan B code's rows: the entropy difference is laptop against EPYC floating point, not the code |
