# Screen #1 result (2026-10-16): CONTINUE, by rule 3(a) only

The run used screen `0ccd6a16…` and code `f427e6c1…` at `b250c7f`. Its 7 synthetic tests passed first. Data: NGSIM `8ect-6jqj`, md5 `f6c10496…`, 11,850,526 rows; the I-80 + US-101 rows number 9,369,320, of which 704,000 were exact duplicates and were removed.
An earlier attempt failed when the disk filled (a runaway Froonty test log) before any data was read. That failure is logged here as well.

| fit → eval | regime | n windows | miss F | miss O | miss H | gap F (m) | gap O (m) | gap H (m) | E (O vs F) [95 % CI] | WIN |
|---|---|---|---|---|---|---|---|---|---|---|
| I-80 → US-101 | R1 | 5,269 | 0.029 | 0.048 | 0.050 | 3.3 | 3.6 | 3.1 | −9.5 % [−14.2, −4.7] | no |
| I-80 → US-101 | R2 | 20,488 | 0.020 | 0.049 | 0.050 | 5.3 | 9.7 | 4.1 | −81.9 % [−93.8, −69.6] | no |
| US-101 → I-80 | R1 | 14,877 | **0.078** | 0.047 | 0.050 | 3.1 | 3.8 | 3.3 | −23.0 % [−27.3, −20.1] | **yes (a)** |
| US-101 → I-80 | R2 | 28,257 | **0.098** | 0.049 | 0.050 | 4.0 | 8.7 | 5.1 | −116.1 % [−128.0, −104.3] | **yes (a)** |

R3 cells are report-only (gap O worse than F). The clip share is ≤ 0.2 % everywhere. Each cell has 22–26 two-minute blocks.

## Reading (main session)

1. **What passed.** Fixed per-regime margins **do not transfer between the two sites**.
   - Fitted on US-101, they under-cover on I-80: 7.8 % and 9.8 % misses against a 5 % target and a 7.5 % limit. R1 fails narrowly.
   - The online margin held 4.7–4.9 % in every cell.
   - That is the validity half of the idea.
2. **What did not pass.** Efficiency. The online margin needs much longer gaps than the fixed one (+10 % to +116 %), and than hindsight.
3. **The cause is visible, and it is a design flaw of the screen.**
   - The tracker is shared by all cars at a site. Outcomes therefore arrive in batches of roughly 100 every 10 s, each moving q by 0.5 (+0.475 on a miss, −0.025 on a hit).
   - So q swings widely: its median is 4.4–10.3 m/s², where about 2–3 is needed.
   - The development plan normalised the step by the batch size (η/c, plan F2). The one-page screen dropped that, and the error is the main session's.
   - The placebo (the same rule, sequential, without batched delay) also holds 5 % with far shorter gaps, which supports this explanation (E_P vs F: +3.6 to −33 % against O's −9.5 to −116 %).
4. **Consequences** (protocol-before-data rules):
   - NGSIM is now spent on this design.
   - Any fix (a batch-normalised step, or one tracker per car) is a design change informed by throw-away data. That is allowed, and disclosed here.
   - The fix must be judged on **fresh** data (TGSIM), never on NGSIM again.
