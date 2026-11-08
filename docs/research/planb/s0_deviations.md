# Plan B S0: findings against the protocol text

Found while building S0. None changes a cell, opponent, measure, margin, n or m unless the author decides so; each needs a V# before S1 (planb.md §11).

| # | Protocol text | Finding | Proposed handling |
|---|---|---|---|
| D1 | §4.2: "Spec test: exactly 10 distinct trucks per seed, all departing before 1,200 s"; "the 80-s grid rarely runs out of trucks" | Measured over all 1,000 seeds of the block (pure Python, the selection rule as written): 10 distinct trucks on every seed, but the 10th departs at or after 1,200 s on 9.4 % of seeds (median 1,115 s, 90th percentile 1,197 s, 99th 1,306 s, max 1,427 s). A truck departing at 1,427 s reaches merge 2 at about 1,904 s, after the window. With a 70-s grid: 1.7 %; 75 s: 3.7 %. | Keep the rule (the cell is the same for every arm on a seed, so no arm gains); correct the spec test to "10 distinct trucks, each departing at or after its slot and before 1,800 s"; report per seed the departure of the last truck. |
