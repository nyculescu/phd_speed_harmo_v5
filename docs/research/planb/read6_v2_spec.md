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

### 1.1 Counting filter (item 1; the forms' source and TRUCK's list are corrected in amendment 3)

- Universe of cell c, in this order with duplicates dropped:
  - p333;
  - the cell's forms: each re-pick name r in `s6_picks.json` `repicks[c]`, resolved to `grid_r` if that name is in the deciding set, otherwise to `r` if it is (plan6's dedup kept the carried twin's name), otherwise the reading stops;
  - the 3E rules for the cell: 3E-T (`t3e`; round 2's e3_rules puts 3E-T in every cell), `e3c[c]` and `e3d[c]`. 3E-X1 and 3E-X2 belong to X1 and X2 only (round_2.md:65).
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
  - a field absent from a row stops the reading (except amendment 2's counters and amendment 3's `delay_ramp2`);
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

Amendment, made while implementing and before v2 ran on the S6 rows. Two v1 fields change by design, and the gate allows exactly these:
- `pr28`: None in a non-W cell in v1, filled in v2 (§1.4).
- A resilience R and its % of no control's loss: v2 hides them when that opponent's own null failed (§1.2, planb.md:462). This can happen only in a W cell, so not in this S6 reading.

A related detail for planted test rows without the report keys: `report_arrays` reads with `.get`. On real rows `derive()` sets every key, and a missing field stops the load (except amendment 2's counters and amendment 3's `delay_ramp2`).

Amendment 2, after the first v2 run stopped at load, before any v2 number existed. The run stopped on row S|w0u250 7,480,462, which lacks `sev3`:
- Over the S6 rows these counts are absent from some rows: `sev3` 265, `ttc15` 326, `ttc2` 3, and v1's `alks_full_moving` 12,413.
- No §5 field is ever None.
- plant_sweep counts them in a `defaultdict(float)` that writes a key only on its first hit (plant_sweep.py:111, :149, :194-198), and the row copies it (:341), so absent means zero events.
- So `ttc2`, `ttc15` and `sev3` read an absent key as 0, and the output counts these rows (`counters_absent_read_as_zero`). Every other report field stays strict.
- v1's default of 0 for `alks_full_moving` is correct for the same reason, so no v1 field is affected.
- A test written before this fix (7b7fc9f) fails on 02f5aeb.

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
| C1 | Code written after the S6 result was known (forking paths) | Items are transcriptions of registered text (table in §1). This spec is fixed before v2 runs. No item feeds a decision. Interpretive choices are fixed here, not after seeing v2's numbers. But item 1's outcome was foreseeable (§5). |
| C2 | §11: "no change to … the reading" after S1, and a reading change after S3a needs new seeds | No deciding rule changes, and the regression gate proves it. Items 1-3 are §11 bug fixes: v1 did not implement registered report text. Item 4 is output completeness. |
| C3 | §11's post-S6 bug rule | The tests are committed before the fix and fail on v1 (§3). Both outcomes of item 1 go into the V# and into any sentence that cites the counting filter. |
| C4 | Breaking the deciding path | The bit-for-bit regression gate, the same index matrix and rng seeds, and v1's deciding assertions kept (two v1 test edits, §5). |
| C5 | The implementer has seen the S6 numbers | Blind recounts of the new numbers by agents who see only this spec, the protocol and the rows, plus an adversarial review of the diff. |
| C6 | R in a NULL could be read as a claim | The report-only label carries its §8.5 reason. "Resilience" stays banned (planb.md:153). The W-path reading is unchanged, except amendment 1's hidden R. |
| C7 | Universe ambiguity (which names are the cell's forms; 3E-T in or out) | Pinned in §1.1 from round 2's code (decide1.tuned, common2e.e3_rules) and plan6's dedup, before running. |
| C8 | Null cost on the laptop (46 nulls, about 1.2 h single-threaded) | Reading only, no simulation (V483). Its own systemd unit at nice 10, single-threaded, under the CPU rules. |
| C9 | Read-once | v1 stays the reading (V496). v2 is the report supplement. Both outputs are kept and hashed, and sentences cite v1's verdict, which v2 reproduces. |
| C10 | Zero denominators and None fields in report-only counts | §1.3: effect `null` with the reason, `mean_diff` always given, None never turned into 0, an absent field stops the reading (except amendments 2 and 3). |
| C11 | Silent defaults flagged by the data review (`r.get(..) or 0.0`) | New fields use strict access. v1's three defaults (`alks_full_moving`, `end_stop2`, `b3_step`/`b45_step`) are kept for bit-identity, and v2 reports how many rows hit each default. |
| C12 | More numbers invite cherry-picking | Every v2 table is report-only, with no tiles or W/L words on the new measures. The sentence words come only from §1's templates. |
| C13 | The extra reference lines beside the sentence (§10) still need the run records | V494's resume, the near-twin opponent pairs (V496) and the G4 disclosure come from the ledger. v2 carries `must_carry` and the provenance it can read. |

## 5. Amendment 3: v2.1, after the review of v2

v2 (f84c9dc) ran once on the S6 rows: study NULL, TRUCK = T, and the gate passed. The review in §3 step 5 (three reviews and two blind recounts) then found the defects below. v2.1 fixes them; v2's output is kept and marked superseded.

Fixed in v2.1:
- **Item 1's universe was wrong in §1.1 itself.**
  - `s6_picks.json` `repicks` holds S3a's `cell_opponents`: the forms plus the delay opponent and the front row (repick.py:58). Round 2's universe holds the forms only (round_2.md:67; decide1.py:77).
  - TRUCK's delay opponent os1_10_10 is not a form, so grid_os1_10_10 was in v2's universe by mistake.
  - v2.1 takes the forms from S3a's repick.json (`--forms`). Its forms plus the delay opponent and the front row must equal the picks file's re-picks.
  - TRUCK resolves to 9 names: p333, grid_z31333, grid_r4a2, grid_lr400_13_1, grid_a41000_10_2, os0_10_10, 3e, 3E-C_TRUCK, 3E-D_TRUCK.
- **Excluded 3E rules are listed** (`excluded_3e`, round_2.md:73), with delay and close-following points against p333 and os1_15_10.
- **Blocks that are not read carry no verdict.** Resilience outside W, and close-following resilience always, no longer carry `passes` or `reading` (planb.md:153, :459).
- **No control with median(O) ≤ 0 on a v1 measure** now has a null effect, as §1.3 says. v1's 1e-9 floor stays only where v1's map has the entry.
- **delay_ramp2:** an absent value means None, because plant_sweep.py:345-346 writes it only when a ramp-2 vehicle finished. Rows read this way are counted (`absent_read_as_none`). A None entry names its cause.
- **Inputs:** a full reading needs `--picks` and `--forms`, and the picks file must match the config's run_commit and cells.
- **Gate:**
  - `t2_counting_filter` is compared with v2's `v1_value`;
  - a key v2 adds outside the spec's list is reported;
  - a failed per-opponent null is recognised after the JSON round trip (`null_ok` 0.0);
  - NaN equals NaN, and 0.0 differs from -0.0;
  - the pr28 skip applies at cell level only.
- **Tests and fixtures:**
  - 11 tests written before the fix (9e2f3bd) fail on f84c9dc; the log is kept. 3 coverage tests pin behaviour f84c9dc already had.
  - test_planb_read6_v2.py's forms test now calls `resolve`, and its `conf()` gives the forms.
  - run6's `fake_row` omits `sev3` and `delay_ramp2` on odd seeds, as plant_sweep does. pack_row's comment is corrected.

Not done: §5's jam metrics (jam_share, congested_share, jams; planb.md:338) need the space-time side files (measure.py:456-483), which S6 did not keep. The map holds the pack's congestion keys only.

Corrections to the text above:
- C4's "v1's tests unchanged" was wrong. e72b337 replaced test_null_failures' `"resilience" not in c` with a report-only status check, because item 2 puts R in every outcome. 02f5aeb added the report fields to the pack_row and fake_row fixtures. The deciding assertions are kept.
- §1.2's "delay R is read exactly as in v1" and §1.4's "the W path is unchanged" hold except for amendment 1, which hides an R whose own null fails.
- C1: item 1's counted set could be worked out from v1's output before this spec was written. v1's `overfit_vs_p333` holds each opponent's delay point against p333, the number `counted()` filters on. Item 1 is report-only and both values are reported. Any sentence citing the counting filter says it was foreseeable.
- The v2 test file's docstring said the regression test does not fail on v1. It did, because v1 has no `map_report_only`.

## 6. Amendment 4: v2.2, after the review of v2.1

v2.1 (6b5778c) ran once on the S6 rows: study NULL, TRUCK = T. The gate passed against v1 and on v2.0's output. A blind recount matched its universe (9 names), counted set (6 names), policies (5) and the excluded 3E points. The review of v2.1 (§3 step 5 again: three lenses, then skeptics on each finding) found the defects below. None of them touches a deciding field. v2.1's output is kept and marked superseded.

Fixed in v2.2:
- **Jam metrics.**
  - Amendment 3 said S6 did not keep the space-time side files. That was false: plan6.py:169-171 sets `measure` for every S6 job, and all 13,920 files are in V494's copy (present, but 14 empty: amendment 4a).
  - v2.2 reads them (`--st`) and adds §5's jam and congestion metrics (planb.md:338) from `measure.waves`: `jam_share`, `congested_share`, `jams`, `congested_km_mean`, `congested_km_max` and `osc_kmh`.
  - A missing file, or a field whose shape differs from the row's `m_st_shape`, stops the reading.
  - The output records the folder, the file count and a SHA-256 over the sorted per-file hashes (`space_time`). A full reading needs `--st`.
  - Left out: `front_kmh_median` (a wave speed, with no better or worse direction), `jam_clusters` (a list) and `osc_stations` (a coverage count).
- **Excluded 3E rules** carry 95 % intervals, as round 2's `e3_status` does (decide2.py:68-76).
- **Transfer 3E rules.**
  - 3E-X1 and 3E-X2 are in TRUCK's deciding set (planb.md:162), but under §1.1's reading (round_2.md:65) they are outside the universe.
  - They are now listed under `transfer_3e`: delay against p333 with its 95 % interval, and the counted set and the policies if they were included.
  - They are found as the deciding set's names that start with "3e" (any case) and are outside the universe.
- **`--forms`** must come from the picks file's run commit (repick.json `code.commit`).
- **Gate:**
  - when v1's `pr28` is None, the field must still be present in v2;
  - a hidden R must be exactly "statistic failed its null", with its `pct_of_nc_loss` None;
  - `map_repeats` follows the float rules and reports a missing entry;
  - a block that is not read must carry no `passes` or `reading`;
  - `space_time` and `report_version` are listed new keys; the spec's list had left out `report_version`.
- **Tests:**
  - 15 tests written before the fix fail on 6b5778c; the log is kept.
  - 6 coverage tests pin: the −2 % threshold and policies against the counted set; braking_clause's lowest upper bound and its None case; no control's null effect in S; main()'s `--forms` wiring and its input checks; each kind of change the gate reports, on a fixture with no NaN.
  - The v2.1 forms test now gives the commits. The v2.1 excluded-3E test reads the point of the new (point, interval) triple; this edit went in with the fix, because the format changes there.

Corrections to the text above:
- **v2.1's fails-on-f84c9dc evidence for its gate.** The test failed at its clean-copy assertion, on a NaN, before its planted edits ran. With a fixture that has no NaN, f84c9dc's gate misses 6 of the 7 edits, and 6b5778c's gate reports all 7 (`gate_edits_on_f84c9dc_and_6b5778c.log`).
- **C4's count.** Three commits edit v1's test files: e72b337, 02f5aeb and 6b5778c. 6b5778c's change makes fake_row omit `sev3` and `delay_ramp2` on odd seeds and corrects pack_row's comment. That fake_row change went in with the fix, not with the tests.
- **Stale sections.** §1.1 (the universe), §1.3 (an absent field stops the reading) and C6 (the W path is unchanged) are superseded by amendments 1 to 3, and now say so.
- **Round 2's other rows.** round_2.md's "reported beside" rows (:204-207) belong to round 2's own report, not to planb.md:476's "T2 with its counting filter". `overfit_vs_p333` already gives each opponent's delay and close-following against p333 at 95 %.

Amendment 4a, after the first v2.2 run stopped at load, before any v2.2 number existed. The run stopped on an empty side file (`EOFError`):
- 14 side files are empty (0 bytes): TRUCK 3E-C_TRUCK, seeds 7,480,610 to 7,480,630.
- Their rows are the last 14 written before the S6 host went offline (rows file lines 13,655-13,668). The files' times, 09:43-09:44 UTC, match V494's outage.
- The rows are complete JSON, and v1 read them. The side-file data was lost in the host's unclean reboot. The resume re-ran only the runs with no row, so these files were never rewritten. V494's hash lists were equal on both sides, so the files were already empty on the host.
- An empty side file now reads as None for the jam keys, under §1.3's rule: the entry is unfilled, with the count of None seeds, and is never 0. The cause is named, and the files are listed in `space_time.empty_files`.
- Anything else stops the reading as before: a missing file, an unreadable file, or a wrong shape.
- On S6 this leaves 3E-C_TRUCK's jam entries in TRUCK unfilled (14 of 240 seeds). Every other entry is complete.
- Not done: re-running those 14 runs to rebuild their side files. That needs a rental, and the run would have to reproduce the stored rows bit for bit. It is left to the author.
- A test written before this fix fails on d14307f. With the fix, the digest test expects the new `empty_files` key.

## 7. Amendment 5: v2.3, after the review of v2.2

The review of v2.2 (§3 step 5: three lenses, skeptics on each finding, and blind recounts D and E) found no wrong number and no change to a deciding field.
- Blind recount D found the 14 empty side files on its own and handled them as amendment 4a does.
- Blind recount E matched the universe, the counted set and the policies, and gave the excluded and transfer 3E listings.
- The empty files were rebuilt on a rental (V498-V500). `jobs/st_rebuilt` holds all 13,920 files, and v2.2 ran once on it.

The verified findings are test gaps, a gate gap and spec text. v2.3 fixes them, adds the items below, and runs once on `st_rebuilt`. Its output must equal v2.2's on every field v2.2 has, apart from the fields listed here and `report_version`.

Fixed or added in v2.3:
- **Jam metrics without the capped trucks.** In TRUCK, the 10 trucks capped at 40 km/h slow the cells they occupy alone. The pack therefore also stores the field without them (`v_nc`, `n_nc`, measure.py:390-393), and v2 already reports `m_cong_*` both ways. v2.3 adds `<key>_nc` for each jam key, from `v_nc`/`n_nc` where the file has them. A file without them had no capped vehicle, so its own field is used.
- **Front speed.** `front_kmh_median` stays out of the map for a different reason than amendment 4 gave. The pack's value is None on any run with no jam cluster spanning 3 time bins (about 1 % of S6 rows in a sample of 199). Under §1.3's rule, almost every paired entry would then be unfilled. The output counts these rows exactly (`space_time.front_none_rows`). `jam_clusters` is a per-cluster list; the pack's summary keeps only its count (`jams`).
- **Each side file is bound to its row.** The row's `m_cong_run_s` and `m_cong_vs` were computed in the run from the same field (measure.py:382-383). v2.3 recomputes them from each file (and the `_nc` pair from `v_nc`/`n_nc`) and reports, under `space_time.binding`, the number of rows checked, the files whose `m_cong_run_s` differs, and the largest relative difference in `m_cong_vs`. This is report-only; float32 storage can move `m_cong_vs` in the last digits.
- **measure** is loaded from this tree's `v5b/fleet/measure.py` by file path, not through `sys.path`. Its path and SHA-256 are in `space_time`.
- **Mechanism G** (planb.md:476, §7.3) is carried from repick.json into `provenance.mechanism_G`. MPC-F's held-out MSE is not in read6's inputs. It comes from S4c's record (`planb_s34_remote/mpcf/`), and the NULL report cites it from there.
- **The 3E intervals** use Plan B's index matrix (rng 20261108, built once per cell), the same estimator as round 2's raw(). Round 2 drew a new matrix (rng 20261104) on each call. On S6 the bounds differ by at most 0.085 points (review of v2.2); the docstrings now say so.
- **Gate:**
  - a resilience block that v1 does not have, and `cf_resilience` always, must carry a status starting "report-only" and no `passes`, `reading`, `pass` or `verdict`. A block marked "read" where v1 has no resilience is reported;
  - `same()` loses its unused dict branch.
- **Tests:** tests written before each fix fail on edebc7b, and the log is kept. Coverage tests pin:
  - the row's dt and dx;
  - the exact 95 % level;
  - close-following against os1_15_10;
  - `policies_if_included` with a blocking transfer rule;
  - the `--st` wiring through load_rows and main();
  - main()'s remaining input checks;
  - map_repeats on ci95, ci_m, list length, the S block and a missing block;
  - no_verdict on both blocks and both keys;
  - a hidden R whose `pct_of_nc_loss` key is missing.
  - The v2.2 digest test now compares only its own four `space_time` keys, since v2.3 adds keys beside them. This edit goes in with the fix.
- **Corrections:**
  - amendment 4's "each kind of change the gate reports" was too broad (the gate mutants above survived);
  - `run6.py:158` is the S5 path (now `plan6.py:169-171`);
  - §2's and C10's strict-field sentences now name amendments 2 and 3.

v2.1's and v2.2's outputs are marked superseded once v2.3 passes. v1 stays the deciding reading.

Amendment 5a, after the review of v2.3, with no change to what read6 computes. v2.3 ran once on `st_rebuilt` (09f49ad): NULL, TRUCK = T, the gate passed against v1, and a script check showed every v2.2 field unchanged. Blind recount F matched all 576 jam entries (12 keys, TRUCK and S, the 3E-C_TRUCK entries included) within 1.4e-14, and matched the side-file digest, `front_none_rows`, the binding and mechanism G. The review found no wrong number. Its findings:
- **No committed check of "v2.3 equals v2.2 on every v2.2 field".** `read6_superset.py OLD NEW` now does it: every leaf of OLD is in NEW with the same type and value, and only `report_version` may differ. Run on v2.2's output on `st_rebuilt` against v2.3's output, it passes.
- **The binding reason.** n is an integer count, stored exactly in float32. The file can differ from the row only when float32 rounding of the speed sum moves a cell's mean speed across 60 km/h. That adds or removes that cell's whole count from `m_cong_vs`, and could in principle change `m_cong_run_s`.
  - On S6, 7 values in 4 TRUCK files differ (4 on the main field, 3 on `_nc`), by −48 to +50 vehicle-samples, at most 7.7e-4 relative. `m_cong_run_s` never differs.
  - The files are listed in blind recount F's `binding_cells.log`. The output gives only the maximum.
- **Front speed.** It is None on 221 of the 13,920 rows (1.59 %: S 204, TRUCK 17), not "about 1 %".
- **`jam_clusters`.** measure.summary() keeps the whole waves() dict, and round 2's report table shows only the count. It stays out because it is a per-cluster list.
- **Without `--st`.** `front_none_rows` and `binding.rows` read 0, which here means not computed; `space_time.dir` is null in that case.
- **§8.7's other sources.** MPC-F's held-out MSE comes from S4c's record (`planb_s34_remote/mpcf/`). The tuning-seed half of the overfitting check comes from the S3a and S4 stage records (`planb_s34_remote/`). Neither is a read6 input.
- **The pack's merge metrics** (minutes below 60 km/h on each acceleration section, breakdown, recovery, capacity drop) are not part of :338's "jam and congestion metrics". That phrase refers to the pack's Waves group and G1b's congestion() (round_2_measure_addendum.md:47-61, V468). This finding was refuted and is listed for completeness.
- **The vs95 docstring** now says the bounds differ by up to 0.085 points on S6, not "in the last digits". read6.py's code is identical to 09f49ad apart from docstrings (checked by AST).
- **Tests.** 14 coverage tests (`test_planb_read6_v23b.py`) pin what the review's surviving mutants broke: the `_nc` counts, every array's shape, front_none from the main field and its count, measure taken from this tree even when another v5b comes first on sys.path, binding on both fields and with the row's dt and dx, the `_nc` None causes, mechanism G per cell, and the gate's hidden-R rule (null_ok must be failed, path under resilience only). The reviewer's mutants, re-run on them, are logged in `planb_s6_read_v23/mutcheck/mutants_v23b.log`.
