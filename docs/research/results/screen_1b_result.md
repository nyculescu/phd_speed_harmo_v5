# Screen #1b result (2026-10-16): CONTINUE (1 cell by efficiency, 2 by validity)

**Provenance.** Screen `abaf9a1f…` and code `94e4a769…` at `ca48b58`; 13 synthetic tests passed first.
- **Data:** TGSIM I-90/I-94 Stationary (`9uas-hf8b`, md5 `17dee825…`, 4,023,022 rows, 6 runs) and I-395 (`97n2-kuqi`, md5 `473e262d…`, 4,323,461 rows; 26,649 duplicate (id, step) rows dropped, keeping the first).
- **Leaders** were found for 93 % and 92 % of rows.
- **c_r** (outcomes per second): 1–5.

| fit → eval | regime | n | miss F | miss O | miss H | q F / O median / H (m/s²) | gap F / O / H (m) | E (O vs F) [95 % CI] | WIN |
|---|---|---|---|---|---|---|---|---|---|
| Chicago → DC | R2 | 27,606 | 0.001 | 0.003 | 0.050 | 1.74 / **1.00 (floor)** / 0.57 | 3.2 / 2.8 / 2.6 | **+14.8 %** [14.3, 15.1] | yes (b) |
| DC → Chicago | R1 | 7,005 | **0.307** | 0.035 | 0.050 | 0.56 / 1.45 / 1.26 | 2.5 / 3.0 / 2.8 | −19.5 % | yes (a) |
| DC → Chicago | R2 | 21,248 | **0.547** | 0.049 | 0.050 | 0.57 / 1.75 / 1.74 | 2.6 / 3.4 / 3.2 | −32.3 % | yes (a) |

Report-only cells:
- Chicago → DC R1: n = 282.
- Chicago → DC R3: O +10.2 %, valid.
- DC → Chicago R3: O −89 %, because of oscillation with small batches (c = 2).

## Reading (main session)

1. **Across both screens, one finding repeats.** Fixed per-regime margins do not transfer between freeways:
   - too optimistic when moved from DC to Chicago (31–55 % misses against a 5 % target);
   - too cautious when moved from Chicago to DC (gaps 15–21 % longer than needed).

   The online margin met its target in every gated cell of both screens, with no tuning on the new road.
2. **The efficiency win is real under the rules, but its mechanism is simple.**
   - In DC R2, O sits at the 1 m/s² floor almost all the time (p10–p90 = 1.00–1.00), while hindsight would allow 0.57.
   - The placebo, which uses the same rule in shuffled order, gains the same 15.0 %.
   - So the gain comes from **re-calibrating to the new site's level**, not from following changes over time.
3. **The opponent that matters most for confirmation:** a margin calibrated briefly on the new site and then frozen. It may capture the same gain. The draft protocols already list it ("same-site block-1 fit").
4. **Caveats.**
   - TGSIM speeds are Kalman-filtered, so leaders' braking looks mild: hindsight quantiles of 0.6–1.7 m/s². Part of the difference between sites may come from processing, not driving.
   - The 1 m/s² floor (fixed before data) binds in DC.
   - R3 oscillates when batches are small.
