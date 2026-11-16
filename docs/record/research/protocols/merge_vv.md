# Merge V&V checks for the E30 confirmation (v1.1, 2026-11-15)

Status: **v1.1, approved (V532)**, after design review round 1 and a final check (`merge_vv_review.md`). Purpose: a record the author can defend before a committee for the E30 claim (V530, narrowed by V531). Each item states what was checked, how, and the criterion fixed before data. Results go into `docs/testing/plant_vv_record_v0.md`. Targets: PR-24 (counter trace) and PR-23 (1 Hz) closed or limited; PR-28 answered for lane length and road location, with its period part printed; PR-15 inspected (VV-D8); PR-08 and PR-27 for merges given a descriptive comparison, and they stay limits. Nothing here changes E30's plant. E30's reading changes only through the bug rule or the replication line (§6).

**Measure wording used everywhere:** `ttc_net` is time spent below 3 s TTC, in vehicle-seconds, sampled at 1 Hz (an exposure count of the TET kind [VERIFY]). It is same-lane and longitudinal: lane changes are instantaneous in this plant and lateral conflict is not modelled. "Lane-end standing" (`end_stop`, `end_stop2`) is vehicle-seconds below 1 m/s in the last 30 m of 3a or 4a. Neither counts events.

**Conventions:** C-D5 statistic as c1_confirm.md §1. Intervals are two-sided percentile intervals over joint seed resamples (B = 20,000, rng 20261108): a "97.5 % lower bound" is the 1.25th percentile, a "98.75 % upper bound" the 99.375th, a "95 %" interval 2.5-97.5. Nulls as c1_confirm.md §1: 2,000 swaps, the rate is the mean of both sides, a rate above its bar is re-estimated once with 20,000 swaps; for the 0.94 % bar, 20,000 swaps × 4,000 resamples. A failed null reads "not shown".

## 0. Committee questions and what answers them

| # | Question | Item | What it can and cannot say |
|---|---|---|---|
| Q1 | Does the count count what you say? | V1 trace | wiring, definition and what the counted samples are |
| Q2 | Is 1-Hz sampling enough? | V2 | whether the 0.1-s edge is within 3 points of the 1-Hz edge |
| Q3 | How much does the edge depend on the 300-m lanes? | V3 (300-m main-lane split; 600-m lanes; the paired change) | the size of the change from 300 to 600 m, **not** whether the 300-m behaviour is an artefact |
| Q3b | Is SUMO's standing at a lane end realistic? | V6 reading; no run answers it | stated as limit M1 whatever V6 finds |
| Q4 | Do vehicles merge like real drivers? | V4 descriptive comparison | no verdict; "compared with two congested 2005 Californian sites" |
| Q5 | Is a 300-m acceleration lane a realistic design? | V5 reading | design context, not model validation |
| Q6 | Could the policy use what a real car could not know? | V7 inspection (VV-D8) | PR-15; the V462 wording gate stays shut while M1 and PR-28's period part remain |

Outcomes: **MET**, **LIMIT** (a numbered limit carried by every claim sentence), **NOT INFORMATIVE**, **BUG** (fix, re-run everything affected, log both; §6). Never "proven" or "validated" (V456, V462).

## 1. Decisions (for the author)

| ID | Decision | Recommended | Cons of the recommendation | Alternative and why not |
|---|---|---|---|---|
| VV-D1 | Items | V1-V7 | about a day of build and review | V1 only: leaves Q3, the likely first question |
| VV-D2 | Arms (V2, V3) | v3w's 5 learners; lr400_16_1 and grid_lr400_13_1 (the two E30 competitors with the smallest 97.5 % lower bounds, +6.2 and +17.5); p333; no control | the other 24 arms are not run at 600 m | all 31 arms: 3.4 × the runs for rules further behind |
| VV-D3 | Lane variant | **A: 3a and 4a both 600 m**, every other edge unchanged (answers "does the edge survive when neither lane is short"; per-merge prints descriptive) | does not say which merge carries it | B: 3a only at 600 m (mirrors C1 check (a)): answers less, adds a variant |
| VV-D4 | Seeds (approval) | readings 7,492,000-479 (480 per length); traces and smoke 7,493,000-019; non-reading replays of stored E30 seeds 7,489,160 and 7,489,161. No hit for 7,492 or 7,493 in `decisions.md`, the repos, stored rows or 48 run-folder `meta.json` files; the builder scans the run folders in full | — | reuse E30's seeds for readings: breaks "fresh seeds every round" |
| VV-D5 | NGSIM reuse | reuse for a **descriptive** merge comparison only, disclosing V82 ("never reused"; its screen-1 use was car-following) and the review's first look (scratch outputs in `results/merge_vv/review_r1/field`, `/design`); extraction frozen before the plant merge log is read | V82 is relaxed for a different question | no field comparison: Q4 unanswered |
| VV-D6 | Run mode, cap | build, review, rent; one rental, one instance type; cap **$4** (as CF) | — | — |
| VV-D7 | Policy position at 600 m | **road-preserving remap:** x = the road's training start + lane position × (training length / built length); factor 1 on every road but 3a and 4a, the identity at 300 m (unit test); column 14 ("near") stays in metres | the policy still meets a geometry it never saw | raw built x: merge 2's learned band falls on edge 3, so a loss could not be read |
| VV-D8 | PR-15 | V7 inspection now, no runs | the roadside columns become a stated limit | leave open |
| VV-D9 | V2 margin | ±3 points; power under the half-second proxy (SE 0.35, an assumption): MET about 1.00 at a true difference of up to 1.5 points, 0.82 at 2, 0.03 at 3 | the proxy may understate the 0.1-s spread | wider: weaker |
| VV-D10 | n at 600 m | 480: resolves about +7 % at 300 m and about +7.5-9.6 % at 600 m (merge-scaling model, an inference) | an edge near +5 % at 600 m may read NOT SHOWN | 960 for the 7 deciding arms at 600 m: about 3,360 more runs (about $0.5); helps mainly if the merge-area cut is near 0.2 |
| VV-D11 | Lane-change parameters (lcCooperative 1, lcAssertive 1.4) | not varied; a limit | a committee may ask | a run: a new plant variant with no question that needs it now |
| VV-D12 | "Standing removed" wording | a merge counts as "standing removed" at 600 m if its cut's 95 % lower bound is at least 80 % | the bar is a judgment | a gate that voids V3b: a reading it no longer needs to guard |

## 2. Items

Road groups, fixed now: **merge area** = 3a, r, rj, 4a, r2, rj2; **edge 1**; **rest** = all other edges, junction samples included. The "main-lane" count is samples whose follower is on none of 3a_0, 4a_0, r, rj, r2, rj2.

**Instruments by run set:**

| Instrument | Runs |
|---|---|
| full sample tracer | V1 traces |
| merge log, lane-end standing log (one line per event) | V1 traces and all V3 runs |
| encounters counter, main-lane count | all V3 runs |
| 0.1-s meter | V3's 300-m runs and the smoke |

### V1 Counter trace (PR-24, PR-19)

- **Runs:** smoke seeds 7,493,000-001 at 300 m and 600 m, arms w1u500 (median learner on E30 close-following), lr400_16_1 and no control, each traced with an untraced twin (24 runs); stored E30 seeds 7,489,160-161 for the same arms, traced, against their stored rows (6 runs).
- **Tracer** (side file; no call that writes state, V386, `CavEnv._x` excluded): every 1-Hz sample adding to `ttc_net` (time, follower and leader ids, types, edges, lanes, lane positions, SUMO gap, minGap, speeds); every lane-end standing sample; every merge (id, type, edge, lane position, speed, the target-lane leader and follower with ids, types, speeds, and net gaps rebuilt from positions).
- **Wiring checks:** each traced run equals its twin, and each stored-seed trace its stored row, on every traffic key (provenance and timing excluded; policy diagnostics within V519's tolerance), as cf_ident; logged samples equal `ttc_net` and the road groups; `end_stop`/`end_stop2`, the main-lane count and encounters recounted from the log equal the run's values; TTC recomputed from the log is below 3 s for every sample. A traced run that differs from its twin is a tracer bug and re-runs nothing in E30.
- **Definition checks (BUG if failed):** for every same-lane sample, the SUMO gap equals the gap rebuilt from positions and lengths within 0.01 m; a leader on neither the follower's lane nor the next lane of its route: must be 0 (the share of next-lane samples printed).
- **A non-event** is a counted sample whose leader is not ahead on the follower's lane or the next lane of its route, or whose gap is not closing.
- **Classification (printed, every sample, by code):** follower on a main lane or on an acceleration lane or ramp; leader standing in a lane-end zone; either vehicle merged in the last 5 s; follower type; speed band; period. Edge-1 samples are described by period and position along the edge, with no cause assumed. Printed per run: distinct encounters (consecutive samples of one pair = one) and their durations; distinct vehicles that stood at each lane end.
- **Visual check:** 40 samples drawn as a simple random sample (rng 20261115), plotted by position and speed; 0 of 40 non-events bounds their share below about 7 % (95 %); a non-event found reads LIMIT with its kind.
- **Outcome:** MET if all checks pass and no non-event is found; LIMIT with the kind; BUG.

### V2 Resolution (PR-23)

- **Meter:** `e1_meter.py` changed to the counter's definition (gap + minGap) and to sample whole seconds at the counter's moment; wired in read-only.
- **BUG checks:** the meter's whole-second count equals `ttc_net` in every run; its half-second count equals `ttc_half`.
- **Deciding statistic:** the 0.1-s edge minus the 1-Hz edge, same runs, against lr400_16_1 and grid_lr400_13_1 (C-D5 form, 95 % interval). **MET** ("the 0.1-s edge is within 3 points of the 1-Hz edge against both rules") if both intervals lie within ±3 points (VV-D9); **LIMIT** otherwise, both edges printed. Its false MET at a true difference of exactly 3 points is about 2.5 % per rule; no null is needed for an equivalence reading.
- **Printed:** the missed share per arm = (0.1-s time − 1-Hz count × 1 s) / 0.1-s time. Already on record (stored rows, post hoc): the half-second-shifted 1-Hz count gives the same edge (difference +0.5 points, SE 0.34).

### V3 Lane-length dependence (PR-28)

**Plant variant (VV-D3 A):** 3a and 4a are 600 m; every other edge keeps its length (merge 2 moves 300 m downstream with edge 3 unchanged). Rules: `LocalRule.N_BINS` and the roadside bins derived from the built network (equal to the hard-coded values at 300 m, checked in review). Policy: VV-D7's remap. Arms that depend on geometry and are not in V3 refuse a changed geometry (run guard). T0: the whole lane-length dict against the 300-m net; only 3a_* and 4a_* may differ, by +300 m. Neither the policy nor any rule was tuned for 600-m lanes.

**Runs:** 9 arms × 480 seeds (7,492,000-479) × {300, 600} m = 8,640.

**V3a, 300 m (no new plant):**
- **Replication line** (C-D5 on `ttc_net`, 97.5 % lower bounds, null bar 1.9 %): v3w against lr400_16_1 and grid_lr400_13_1. **REPLICATED** ("replicated against lr400_16_1 and grid_lr400_13_1, 2 of E30's 14 competitors, no chords") or **NOT REPLICATED** (stated with intervals). Reported with every E30 sentence, whichever way it reads.
- **Main-lane sensitivity** (pre-registered, same levels): the same statistic on the main-lane count. Wordings fixed now: "the edge is also shown on main-lane samples at 300 m (x % [lo, hi])" / "not shown on main-lane samples alone (x % [lo, hi])". Added in both cases: "a main-lane edge does not rule out main-lane congestion caused by the short lanes; 600 m is the direct test".

**V3b, 600 m:**
- **Deciding readings** (C-D5 on `ttc_net`):
  - **HOLDS:** at 600 m both 97.5 % lower bounds above 0, nulls under 1.9 %.
  - **WORSE:** a 98.75 % upper bound below 0, null bar 0.94 %.
  - **NOT SHOWN:** otherwise.
- **The change (answers Q3):** the 600-m edge minus the 300-m edge on the same seeds, seeds resampled jointly, 95 % interval, against each rule. A statement that the edge depends on lane length is made only if this interval excludes 0.
- **Record sentence, fixed now:** "against [rule], v3w spent a % less time below 3 s TTC at 300 m and b % [lo, hi] at 600 m (HOLDS / WORSE / NOT SHOWN); change c [lo, hi]; lane-end standing fell by x % [lo] at merge 1 and y % [lo] at merge 2; at 600 m the largest remaining deficit, in samples per run, sits on [group]; the other 24 non-learning arms were not run at 600 m; neither the policy nor the rules were tuned for 600-m lanes; policy positions remapped, geometry not seen in training". "With lane-end standing removed at merge m" is added only for merges meeting VV-D12.
- **Pre-stated:** a WORSE or NOT SHOWN carried by edge 1 is not a lane-length effect; edge 1 is unchanged at 600 m. In E30, v3w and p333 have 22-26 edge-1 samples per run, mostly in the slowdown's hold period, against 2-3 for the lr rules.
- **Expectation, stated before data (an inference from stored E30 rows, not a measurement):** 80-85 % of each arm's close-following sits in the merge area. If 600-m lanes cut merge-area counts by the same factor in all arms:

| Merge-area count kept | Edge against lr400_16_1 | P(HOLDS) | Same, edge-1 samples left out |
|---|---|---|---|
| 0.34 (no control's merge-2 cut in C1 check (a), S) | +7.3 % | about 0.85 | +11.5 % |
| 0.2 | +4.7 % | about 0.3-0.4 | +10.3 % |
| 0.1 | +0.4 % | about 0.02 | +8.3 % |
| 0.02 (p333's cut in C1 check (a)) | −5.6 % | 0 | +6.0 % |

So NOT SHOWN or WORSE is a likely outcome, and the edge-1 column shows how much of that edge 1 alone would carry.

**Printed, never deciding (V3a and V3b):** edges by road group (merge area, edge 1, rest), per merge and by period (`m_road_ttc3` period keys); the 600-m edge with edge-1 samples left out; lane-end standing per arm and merge, with distinct vehicles; delay, TTT, served flow, collisions, jams; `ttc2`, `ttc15`, `sev3` and `b45_step` edges with the fixed sentence "TTC below 3 s and braking at 3 m/s² or harder are terms of v3w's training reward; TTC below 2 s and 1.5 s are stricter versions of the rewarded event and `b45_step` of the rewarded braking; only DRAC (`sev3`) is outside the reward" (post hoc on E30 against lr400_16_1: +32.1, +21.9, +16.0, and `b45_step` +2.4 [−0.6, +5.0]); distinct encounters; whether any rule beats no control on delay by 10 % at 600 m.

### V4 Merges against NGSIM (PR-08, PR-27; descriptive, VV-D5)

- **Field merges:** US-101: lane 6 → 5 changes by vehicles that entered on lane 7 (lane 7 → 6 is the gore renaming); I-80: the lateral crossing of the lane-7/6 line (Lane_ID changes sit at the coded lane end). Exact duplicate rows dropped; positions smoothed before speeds. Lane roles are inferred from the data and checked against the NGSIM documentation [VERIFY].
- **Quantities:** accepted lag time gap = net gap to the target-lane follower / that follower's speed, for followers above 5 m/s, median; speed difference to that follower at the merge. Per site, pooled over its periods, with a bootstrap interval over vehicles; periods shown as spread.
- **Plant:** human-driven merges (cars, trucks) in V3a's no-control runs, from the merge log; the same quantities, split by a human or ALKS follower. Plant merges are instantaneous lane changes; field merges are timed at the line crossing; stated beside the figures.
- **No verdict.** Record sentence fixed now: "compared with two congested Californian sites (2005) [VERIFY site facts]; a comparison, not a validation". Two sites cannot validate merging (§5). The extraction script is committed before the plant log is read.

### V5 Design guidance (PR-01)

Read at least two primary sources on acceleration-lane length near 100 km/h (candidates: AASHTO Green Book; UK DMRB CD 122; German RAA [VERIFY all; read in full before citing]). Criterion fixed now: record the guidance range for a parallel acceleration lane at the matching design speed, and say whether 295 m to the lane end lies inside, below or above it, with the source's own definition of length. Context only.

### V6 Lane-end standing in the literature (no runs)

Search scope fixed now: Google Scholar and the SUMO user-conference proceedings, terms "SUMO lane change model validation merge", "LC2013 on-ramp merging", "forced merge lane drop field data"; search date recorded; at most 10 sources read in full. Outcome wording: "source X compared Y against Z and found W" [VERIFY each], or NOT INFORMATIVE if none compares SUMO lane-end merging with field data. Whatever it finds, limit M1 stays: "the plant's standing at acceleration-lane ends is not validated; the E30 edge sits mostly where it occurs".

### V7 Inputs a real car could use (PR-15; VV-D8)

Inspection, no runs: for each column of v3w's observation, its source in code and whether it uses the seed, event timing or a future state (PR-15's test). **MET** if no column does; otherwise a LIMIT naming the columns. Each column's channel (on-board, V2V within 150 m, roadside feed also read by the rules) is listed as a stated assumption, and roadside columns are named as a limit (e.g. the merge-zone mean speed, the vehicle counts on 3a_0 and 4a_0).

## 3. Build (branch `vv/merge` from `c1/confirm` 4dfefca, own worktree)

- `corridor.build` for r2m3: 3a lengthened downstream with the r2m3 nodes (e2, b, x, r02, rm2) shifted too, so every edge but 3a and 4a keeps its length (today `accel_len` leaves 4a at 300 m and stretches rj2 to 330 m).
- Bins from the built network for `LocalRule.N_BINS` and the roadside bins; VV-D7 remap with a unit test; run guard for other geometry-dependent arms; T0 on the whole lane-length dict.
- Tracer, merge and standing logs, encounters counter, main-lane count, meter fix, each with twin tests (PR-19).
- Identity replay at 300 m: the 9 arms on stored E30 seeds 7,489,160-161 equal their stored rows on every traffic key (as cf_ident).
- `read_vv.py` with planted-row tests for every reading in §6; the NGSIM extraction with tests on a hand-made trajectory.
- Before the rental: the reader and the extraction committed, hashes recorded; runs launched from a frozen, detached worktree at the run commit; each reading read once; later analysis labelled post hoc.

## 4. Order, machine and cost

Smoke on the rental (twins, identity, T0 at 600 m, meter equality, an assertion that the remapped x on 3a and 4a stays within the 300-m training range, the share of decisions with column 15 at its cap, measured seconds per run with the meter on, and lane-end standing at 600 m for no control and lr400_16_1, printed for the author) → cap check → V1 traces → V3 runs (V2 inside the 300-m half) → readings → V4 (laptop, no simulation) → V5, V6, V7 (reading). All runs on one instance type, the E30 type if available; if the rental must split, both lengths of a seed run on the same type, and the type is recorded per row.
Runs: 8,640 + 30 traces + about 40 smoke and identity runs. At CF's rate (1,067 runs per hour on 30 workers, $0.149/h) about 8.2 h and about $1.2 before the meter's overhead (about 6 M extra leader lookups per 300-m run, unmeasured); re-quoted from the smoke before the screen; cap $4.

## 5. Limits this plan leaves

M1 lane-end standing not validated (V6). Lateral and merge-gap conflict not measured; lane changes instantaneous. Two field sites cannot validate merging. No calibration. Lane-change parameters not varied (VV-D11). Other cells, shares and demands not tested. A change between 300 and 600 m says how much the edge depends on lane length, not whether the 300-m behaviour is an artefact.

## 6. Readings and consequences

| Reading | Level, null | Outcome → effect on the E30 sentence and record | PR row |
|---|---|---|---|
| V1 wiring | exact | tracer bug → fix the tracer; nothing in E30 re-run | PR-19 |
| V1 definition | exact | BUG in `ttc_net` → fix; re-run the E30 arms affected on their stored seeds (cost from the run count) and re-read under the bug rule; log both | PR-24 |
| V1 classification, visual | printed; 0/40 bound | non-event found → LIMIT naming it | PR-24 |
| V2 meter equality | exact | BUG → as V1 definition | PR-23 |
| V2 0.1-s minus 1-Hz edge | 95 %, ±3 points | MET → PR-23 closed for this cell; LIMIT → "the 1-Hz edge is not shown to carry to 0.1 s" | PR-23 |
| V3a replication | 97.5 % lower, 1.9 % | NOT REPLICATED → stated beside every E30 sentence | — |
| V3a main-lane sensitivity | 97.5 % lower, 1.9 % | "not shown on main-lane samples alone" → the E30 sentence names it | PR-28 |
| V3b HOLDS / WORSE / NOT SHOWN | 97.5 % lower, 1.9 %; 98.75 % upper, 0.94 % | the fixed record sentence goes into PR-28 and beside the E30 sentence | PR-28 |
| V3b change | 95 % | "depends on lane length" only if it excludes 0 | PR-28 |
| NOT REPLICATED with any 600-m reading | — | both reported; no "survives" wording; the change is still printed | PR-28 |
| REPLICATED with HOLDS | — | "the edge was shown at both lengths" with the change | PR-28 |
| V4, V5, V6 | descriptive | the field sentence and M1 carried | PR-08, PR-27, PR-01 |
| V7 | MET / LIMIT | can close PR-15; the V462 gate stays shut while M1 and PR-28's period part remain | PR-15 |
