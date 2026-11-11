# M2: do our results depend on how SUMO handles the end of the second on-ramp lane? (PR-28)

Status: **DRAFT v2, not approved.** A plant verification (V&V) check, not a DRL study. Its outcome labels recorded results; it never creates or strengthens a claim. Approved so far: V505 (the step), V507 (v3w may run here; closed cells under the rule below; cap about $6). Shared rules, words, seeds and cost: `v505_common.md`.

## 0. Decisions still open

| # | Decision | Recommendation | Pros | Cons | Weaker alternatives |
|---|---|---|---|---|---|
| D3 | The variant | V-A: on `4a_0` only, ramp-2 cars merge with `lcAssertive` = a; back to 1.4 once they have left `4a_0` | geometry, positions and v3w's inputs stay as in training; one parameter; SUMO reads it only through the merging car's own gap checks (MSLCM_LC2013.cpp:2056-2057) | it rescales gap acceptance; SUMO's stop-at-the-end mechanism stays | V-L, a longer 4a (SUMO's own advice): moves the positions v3w reads and every zone table. V-G, our own gap acceptance through TraCI: a new model with collision risk, the heaviest build |
| D4 | Seeds for S and TRUCK | the S6 seeds 7,480,400-639: base rows are the stored S6 rows, only V-A runs | half the runs (about $0.7 less on an EPYC host); the base readings are the recorded ones, exactly | the deciding reading uses Δv alone, so pairing buys little (the base rows feed the planned power and the report-only interaction); an exception to "every new round uses fresh seeds"; the seeds are outside V505's block and were Plan B's "evaluation, used once"; the pairing crosses commits and machines (`b0c9360`, Xeon 8163) | fresh seeds on both plants (7,488,760-999), +5,280 runs |
| D7 | Does M2 add to the count of cells tested (planb.md:145)? | yes: S-V, TRUCK-V and X1-V add 3 cells (91 → 94), labelled V&V and post hoc; the X1 base round adds none | counting can only make later claims harder | a larger count for a check that makes no claim | not counting, although the unit's text covers runs where a DRL policy ran |
| D8 | May a CHANGED edge withdraw the recorded edge? (V507(2) allows "label or withdraw") | label only: "not shown on the lane-end variant V-A (PR-28 record)" | V-A is a sensitivity case, not a validated plant; withdrawing on it would treat it as truer than the base | a recorded edge may stand that depends on an artefact | withdraw: stronger, but rests on an unvalidated plant |

**Rule for the closed cells (V507(2)), wording to approve:** "Amendment to [A3] (confirmatory_3.md:132), planb.md:160 and planb.md:575, for V&V reads only. The frozen v3w policies and stored rules may run in X1 and TRUCK, on the base plant and on V-A, to label recorded results for PR-28. These rows are never an effect estimate. They never enter a claim, a prior or a pooled count, and they cannot reopen a cell. Their values are printed only in the PR-28 V&V record, labelled 'V&V, not an effect estimate'."
- V503 (X1 stays closed for DRL) is unchanged.
- X2 is not included: no current conclusion rests on it (its edge did not replicate, V401; closed by V466), although PR-28 began there (V396).

## 1. Question

At merge 2, a car that finds no gap stops at the end of the accelerating lane and waits. SUMO's documentation says real drivers behave otherwise (Motorways.md:24-27: they "may accelerate up to the end"). Under no control in S, merge 2 has 26 times merge 1's lane-end waiting (S6 medians 522.5 against 20.0). Part of this is load: merge 2 sees 85 % of demand on the main road, against 70 % at merge 1. Three questions follow:
1. **Trace:** does the lane-end counter count what it claims (PR-24)?
2. **Variant:** is there a variant in which lane-end waiting at merge 2 falls by at least 75 %, without more hard braking, emergencies, collisions or stuck cars?
3. **Conclusions:** do the recorded conclusions in §3 read the same on that variant?

## 2. Variant V-A and its pick

- **V-A:** in `run_one`'s step hook, a ramp-2 car gets `laneChangeModel.lcAssertive` = a through libsumo at departure. This happens after the plant's own type settings, which would otherwise reset it (fleet.py:157, :179). The value goes back to 1.4 at the first step after the car has left lane `4a_0`.
  - The hook runs once per second, so a merged car may keep a for up to 1 s (about 25 m) on `4a_1`. This is disclosed.
  - Everything else equals the base. The row records a.
- **Ladder:** a ∈ {2, 3, 5, 10}.
- **Pick,** on no control and p333 in S, seeds 7,488,020-079 (n = 60, with the pack). Only lane-end waiting and safety are read; no delay or close-following value. The pick uses p333 runs to choose a plant change, which is disclosed under V456(3). The pick is the smallest a with all of:
  - median `end_stop2` at least 75 % lower than the base on the same seeds, for both arms;
  - braking: the paired mean ratio of `b45_step`, and of `alks_b45_step`, against the base fails if its point is above 1.05 and its 95 % lower bound is above 1.00;
  - emergencies: the one-sided 95 % upper bound of the paired mean excess of `alks_full_moving` is at most 0.05 per run;
  - collisions per run at most the base's + 0.05;
  - `m_stuck_n` 0, and drain: the mean backlog over 1,500-1,800 s (ramp-1 queue, ramp-2 queue, total) at most 2 vehicles above the base on the same seed (V486's form, variant against base).
  - Before the pick, the false-fail rate of the braking bound at n = 60 is computed from S6 S rows (two rules of near-equal braking) and printed.
- **If no a reaches 75 % within the bounds:** the a with the largest cut that meets every other bound is used, if its cut is at least 50 %, and every M2 sentence names it "partial variant (cut x %)". If no a reaches 50 %, M2 is VOID and PR-28 stays a gap.
- **A dose check** at a second level is not run, to keep the test simple. The weaker alternative costs about 2,640 runs.
- **Printed beside the pick:**
  - `end_stop` (merge 1) on the same runs;
  - `m_mergepos_m2`;
  - lane changes by ramp-2 cars on `4a_1`-`4a_3`, 4 and 5 (base against variant);
  - merge-1 lane-end waiting at a matched main-road load, from the stored r2m3 ladder at 6,000 veh/h (P0 plant; merge 2 can spill back into merge 1 there).

## 3. Conclusions read (fixed now)

Each conclusion has one deciding opponent. The others are printed beside it. Base values are read6 v2.3's recorded ones (`read6_v23.json`, common §4's statistic, 97.5 %).

| # | Cell | Recorded result | Recorded reading | Measure |
|---|---|---|---|---|
| C1 | TRUCK | v3w against os0_10_10: −0.58 [−0.93, +0.20] | neither | `all_delay` |
| C2 | TRUCK | v3w against 3E-C_TRUCK: +11.80 [+4.97, +19.71] | better | `ttc_net` |
| C3 | S | v3w against p333: −1.57 [−2.70, −0.24] | neither (worse with the CI excluding 0, but under Plan B's 2 % harm size) | `all_delay` |
| C5 | X1 | v3w against p333: +4.2 [+2.4, +5.9] on 120 seeds (memo, exploratory) | read on fresh seeds on the base plant first | `all_delay` |
| C5b | X1 | v3w ahead of the tuned rule grid on close-following (rounds 1-2, V449, V452) | read on fresh seeds on the base plant first | `ttc_net` |

**Report-only:**
- C4 in S (p333 against os0_10_10 and lr1000_16_2): identical rows on about a third of seeds.
- C6 in TRUCK (rule provenance): 3E-C_TRUCK against p333 on `ttc_net`, and os0_10_10 against p333 on `all_delay`.

## 4. Reading

- **Binding check per cell, on the verdict runs.** For every arm in the conclusion's deciding comparison, and for no control, V-A must cut median `end_stop2` by at least the pick's bar (75 %, or the partial cut x achieved), judged by the paired-ratio 95 % upper bound. Otherwise the conclusion reads **VARIANT DID NOT BIND**.
- **Base on fresh seeds (X1 only):** the base reading is made on the fresh base rows first. If C5 is not "better" there, it reads **NOT REPLICATED**, and the variant reading is not made. C5b likewise.
- **Variant reading:**
  - **SAME:** Δv's comparison reading (common §4) equals the base reading;
  - **CHANGED:** it differs; the direction is printed in the V&V record;
  - **NOT RESOLVABLE:** Δv's CI half-width is more than 1.5 times Δb's.
- **For every SAME on "neither":** the record prints the smallest shift detectable at 80 % from Δv's half-width, as "no change detected; a shift of x points or more would have been seen with 80 % probability".
- **Interaction:** I = Δv − Δb with its CI is printed in the V&V record for every comparison. It is report-only: at n = 240 its CI is about 2 points wide for delay in S and about 9 for close-following in TRUCK.
- **Null:** for every deciding Δv, read6's swap null: v3w and opponent labels swapped within seed on the variant rows, 2,000 swaps, at most 1.5 times the nominal rate. A failure reads "statistic failed its null". A base/variant swap is run only as a check on the report-only I.
- **Planned power,** from the S6 rows, recomputed in the run record before any variant row and never used to change a rule. Figures from the second review, with a correlation of 0.2 between base and variant per-seed effects:
  - "neither" reads CHANGED in 1-3 % of no-change studies;
  - a 2-point delay shift is caught in at least 98 % of studies;
  - C2 reads CHANGED in 0 % of no-change studies at equal variance, and in 10 % with the variant's spread 1.5 times larger;
  - a 1-point shift in S is missed in about 58 % of studies;
  - a 5-point loss of C2's edge reads SAME in about 80 % of studies.

## 5. Consequences (fixed now)

Beside a recorded result only a label is printed, never a variant value. Values appear only in the PR-28 V&V record.

| Reading | What changes |
|---|---|
| SAME | PR-28 record: "not shown to change on V-A (a = x)", with the detectable shift. Nothing is added beside the recorded result |
| CHANGED | beside the recorded result: "not shown to be insensitive to SUMO's lane-end behaviour (PR-28 record, L-n)". Under D8 it is not withdrawn |
| NOT REPLICATED (X1) | beside the recorded X1 result: "did not replicate on fresh seeds (PR-28 record)" |
| VARIANT DID NOT BIND, NOT RESOLVABLE, failed null | that conclusion is "not tested"; the reason is logged |
| X1 not run (cap) | C5 and C5b read "not tested" |
| VOID, failed trace | PR-28 stays "gap", with the reason logged |
| SAME for C1, C2 and C3, with C5 and C5b SAME or not tested | PR-28 becomes: "partial: located by road and period (not lane); not shown to depend on the merge gap-acceptance scale on 4a_0 (V-A, a = x) for [the conclusions read]; SUMO's stop-at-lane-end mechanism and the commanded-headway dependence (PR-08) untested". A numbered limit L-n with that sentence is added to the V&V record. PR-28 stays open under V462 |
| any other mix | PR-28 stays "gap"; each conclusion's reading is logged |

## 6. Arms and cells

- **S and TRUCK:** no control, p333, os0_10_10, 3E-C_TRUCK, 3E-D_TRUCK, lr1000_16_2 and the five learners: 11 arms, each with S6's config and checkpoint hashes.
- **X1:** no control, p333, os0_10_10, 3E-T and the five learners: 9 arms, on both plants.
- **Identity, first:** every S and TRUCK arm, including one replay per learner, is replayed on the base plant on 3 S6 seeds, and every key must be equal by value.
  - If a rule differs, M2 stops until it is explained (bug rule).
  - If only v3w rows differ (another CPU's torch arithmetic), the S and TRUCK verdict switches to fresh seeds 7,488,760-999 on both plants, D4's alternative. The switch is logged, and its cost counts against the cap.

## 7. Checks before the verdict

| Check | Requirement | If it fails |
|---|---|---|
| Identity | as in §6 | as in §6 |
| Determinism (T3) | the same run twice is equal | stop |
| Trace (PR-24) | on 2 seeds × {no control, p333}, traced samples equal `end_stop2` and `end_stop` | M2 is VOID |
| V-A binds | read back from libsumo: a for ramp-2 cars on `4a_0`; 1.4 on `4a_1`-`4a_3`, 4 and 5 from the second after they leave `4a_0` | stop |
| Traced equals untraced | as V386 | stop |

## 8. Disclosures every M2 sentence carries

- V&V check, post hoc. V-A is a sensitivity case, not a validated plant. Its level was picked on no-control and p333 runs, reading lane-end waiting and safety only.
- No field reference for lane-end behaviour exists in the record. SUMO's documentation is the only primary statement found.
- V-A keeps SUMO's stop-at-the-end mechanism and the gap rule that reads the follower's commanded headway (PR-08).
- The location report is by road and period, not by lane.
- If D4: the base rows are S6's, from `b0c9360`. The base effects were known when this protocol was written; only the variant rows are new.
