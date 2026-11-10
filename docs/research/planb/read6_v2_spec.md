# read6 v2: specification (V497), fixed before any v2 code runs on the S6 rows

read6 v1 (b0c9360) was run once on the S6 rows (V495). Its verdict, TRUCK = T and study NULL, was verified by two blind recounts and three adversarial reviews (V496). That review found three report-completeness gaps, and the author decided to fix them in a v2 (V497). v2 changes no deciding rule. Every item below transcribes registered text that v1 did not implement.

## 1. What v2 adds or fixes

| # | Item | Registered text v1 did not implement |
|---|---|---|
| 1 | T2 counting filter: apply round 2's universe half | planb.md:476 "round 2's T2 with its counting filter"; round_2.md:66-69; decide1.tuned and common2e.opponents2 |
| 2 | R and close-following resilience in every outcome, labelled report-only when R is not read | planb.md:571 (NULL row lists R), :465 (close-following resilience is report-only), :462 (an R whose null fails is reported only as "statistic failed its null") |
| 3 | No control and §5's report-only measures in the map | planb.md:210 (no control "in every table"), :330 (robust braking raw and per vehicle served beside), :332 (`contact_steps` beside), :338 (report-only measures "in every table"), :343 (TRUCK lane-change share) |
| 4 | The NULL sentence's fields in every outcome | planb.md:149 (closest opponents with effects and CIs, the breakdown), :571 (braking, location, plateau labels), :143 (PR-28 share), :336 (braking [z] and the lowest upper bound) |

Item 4 was a refuted review finding: not a defect against §8, only a gap in what the reader outputs. It is added so the NULL sentence is filled by the committed script instead of by hand.

### 1.1 Counting filter (item 1)

- Universe of cell c, in this order with duplicates dropped:
  - p333;
  - the cell's forms: each re-pick name r in `s6_picks.json` `repicks[c]`, resolved to `grid_r` if that name is in the deciding set, otherwise to `r` if it is (plan6's dedup kept the carried twin's name), otherwise the reading stops;
  - the 3E rules for the cell: 3E-T (`t3e`; round 2's e3_rules puts 3E-T in every cell), `e3c[c]` and `e3d[c]`. 3E-X1 and 3E-X2 belong to X1 and X2 only (round_2.md:69).
- TRUCK resolves to: p333, grid_a41000_10_2, grid_lr400_13_1, os0_10_10, grid_os1_10_10, grid_r4a2, grid_z31333, 3e, 3E-C_TRUCK, 3E-D_TRUCK.
- An opponent counts if its delay point against p333 is at least −2 % (unchanged from v1).
- Policies = learners meeting round 2's per-policy bar against the counted set (`t2_policy`, unchanged).
- The output gives the universe, the counted set, the policies, and v1's value under `v1_value`.
- Without forms (no `--picks`), the universe has no forms, and the output says so.

### 1.2 Resilience (item 2)

- Delay R is unchanged: R(o) = median(loss_o − loss_v3w), with loss = cell − S on the same seed and S twins taken from `s_alias`.
- Close-following resilience uses the same formula on `ttc_net` (samples per run).
- Each opponent gets its own label-swap null: 2,000 swaps (`null_swaps`), B = 20,000, rate at most 1.5 × nominal. The rng seeds are RNG + 11 for delay (as in v1) and RNG + 13 for close-following.
- Per opponent: when the null fails, the R value is replaced by "statistic failed its null" and the rate is kept.
- Outcome W or W-b with W's null passed: delay R is read exactly as in v1. Close-following resilience is labelled `report-only`.
- Any other outcome: both are computed and labelled "report-only, not read: §8.5 reads R only in a W or W-b cell after W; §10 lists R in the NULL report". No sentence may use "resilience" or "resilient" (planb.md:153).

### 1.3 Report-only map (item 3)

- New key `map_report_only` in each cell and in S. v1's `map` stays byte-identical.
- Opponents: the deciding set plus no control (`nc`); in S, the S names plus `nc`.
- Measures:
  - v1's eight;
  - `events_ge45`: the sum over car, ALKS and truck of `m_peak_*[3:]`, as measure.py:524;
  - `ttc2`, `ttc15`, `sev3`, `gap25`, `delay_ramp`, `delay_ramp2`;
  - `m_cong_vs`, `m_cong_run_s`, `m_cong_vs_nc`, `m_cong_run_s_nc`;
  - `contact_steps`;
  - `robust_raw`: the event count behind `robust_rate`;
  - `robust_per_served`: `robust_raw` / `passed`;
  - `ttc3_lc_share`: `m_ttc3_lc` / `m_ttc3_all`;
  - `collisions` and `alks_full_moving`.
- Per entry:
  - the effect `sign × median(P − O) / median(O) × 100`, with intervals at 95 % and 1 − 0.05/m on the cell's index matrix. Sign is +1 for flow and −1 for every other measure, so positive = v3w lower. The share and the congestion measures carry no "better" reading; their sign only orients the column;
  - when median(O) ≤ 0, the effect is `null` with the reason;
  - always `mean_diff` (mean(P − O) and its 95 % interval) and the medians of P and O.
- Missing or None fields:
  - a field absent from a row stops the reading;
  - a None value (possible for the ramp delays) leaves that arm's entry unfilled, with the count of None seeds. It never becomes 0.
- Consistency check: for v1's measures against deciding opponents, `map_report_only` must equal v1's `map` (the regression script checks it).

### 1.4 NULL-sentence fields (item 4)

- `closest` and `d4`, by v1's rule (the lowest lower bound at 1 − 0.05/m), are computed in every outcome. The W path is unchanged.
- `braking_clause`, at 95 %:
  - the opponent with the largest point excess, with its CI;
  - the opponent with the lowest upper bound, if different.
- `pr28`: v1's rule against the closest opponent on delay, computed in every outcome (report-only; TRUCK carries PR-28 unconditionally, planb.md:143).
- `provenance`, from `--picks`:
  - the plateau label and generations of each tuned search;
  - `s_alias`;
  - the picks file's SHA-256;
  - the breakdown as lists: fixed (p333); tuned for the cell (the grid re-picks resolved, 3E-C, 3E-D); re-picks equal to a carried rule; carried for other conditions; distilled (copy, planb.md:217); ASCH and steady aliases; MPC-F.
- Counts are left to the write-up, because os0_10_10 and p333 are both carried rules and TRUCK re-picks.

## 2. What v2 must not change

Every field of v1's output keeps its value bit for bit, except `cells.*.t2_counting_filter`. The fields covered include:
- the outcome, harm, gates, comparisons, the learner signs and drain;
- no control (V459), the adaptation gain, `map`, `location`, `overfit_vs_p333`;
- the study outcome, the vetoed cells and S's `map`.

`read6_regress.py V1.json V2.json` checks this, plus the consistency check in §1.3. Any other difference stops: v2's output is not used, and the difference is logged.

## 3. Order of work (§11's post-S6 bug rule)

1. This spec and the new tests are committed together. The tests run on v1 and must fail on items 1 to 4; the failing log is kept.
2. v2 is implemented. Old and new tests must pass.
3. v2 runs once on the S6 rows, from a clean worktree, in its own unit, at nice 10.
4. The regression gate runs.
5. An adversarial review of the diff against this spec and the protocol, and blind recounts of the new numbers from this spec, the protocol and the rows, without v2's code or output.
6. A V# records both outcomes of item 1 (v1's value and v2's value) and the deciding fields being unchanged. Every post-S6 bug search is logged with its trigger; the trigger here is V496's verification workflow.

## 4. Challenges and cons, and how each is handled

| # | Challenge or con | Handling |
|---|---|---|
| C1 | Code written after the S6 result was known (forking paths) | Items are transcriptions of registered text (table in §1). This spec is fixed before v2 runs. No item feeds a decision. Interpretive choices are fixed here, not after seeing v2's numbers. |
| C2 | §11: "no change to … the reading" after S1, and a reading change after S3a needs new seeds | No deciding rule changes, and the regression gate proves it. Items 1-3 are §11 bug fixes: v1 did not implement registered report text. Item 4 is output completeness. |
| C3 | §11's post-S6 bug rule | The tests are committed before the fix and fail on v1 (§3). Both outcomes of item 1 go into the V# and into any sentence that cites the counting filter. |
| C4 | Breaking the deciding path | The bit-for-bit regression gate, the same index matrix and rng seeds, and v1's tests unchanged. |
| C5 | The implementer has seen the S6 numbers | Blind recounts of the new numbers by agents who see only this spec, the protocol and the rows, plus an adversarial review of the diff. |
| C6 | R in a NULL could be read as a claim | The report-only label carries its §8.5 reason. "Resilience" stays banned (planb.md:153). The W-path reading is unchanged. |
| C7 | Universe ambiguity (which names are the cell's forms; 3E-T in or out) | Pinned in §1.1 from round 2's code (decide1.tuned, common2e.e3_rules) and plan6's dedup, before running. |
| C8 | Null cost on the laptop (46 nulls, about 1.2 h single-threaded) | Reading only, no simulation (V483). Its own systemd unit at nice 10, single-threaded, under the CPU rules. |
| C9 | Read-once | v1 stays the reading (V496). v2 is the report supplement. Both outputs are kept and hashed, and sentences cite v1's verdict, which v2 reproduces. |
| C10 | Zero denominators and None fields in report-only counts | §1.3: effect `null` with the reason, `mean_diff` always given, None never turned into 0, an absent field stops the reading. |
| C11 | Silent defaults flagged by the data review (`r.get(..) or 0.0`) | New fields use strict access. v1's three defaults (`alks_full_moving`, `end_stop2`, `b3_step`/`b45_step`) are kept for bit-identity, and v2 reports how many rows hit each default. |
| C12 | More numbers invite cherry-picking | Every v2 table is report-only, with no tiles or W/L words on the new measures. The sentence words come only from §1's templates. |
| C13 | The extra reference lines beside the sentence (§10) still need the run records | V494's resume, the near-twin opponent pairs (V496) and the G4 disclosure come from the ledger. v2 carries `must_carry` and the provenance it can read. |
