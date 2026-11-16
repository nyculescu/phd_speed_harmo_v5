# B0: do plant mergers stop more often than field mergers? (v1, 2026-11-16)

Status: **draft v1, for the author's approval** (V538, V539). v0 was reviewed by one Fable agent (2 blockers, 6 majors, 5 minors), and every finding is applied here (§9). Desk check: no simulation, no new seeds, $0. It informs limit M1 ("the plant's standing at acceleration-lane ends is not validated") with data from two field sites. It cannot validate the plant (two congested 2005 sites, 45 minutes on one day each [VERIFY], different geometry). Its result decides whether B1 (calibrated merging, rerun) is proposed (V539).

**Expected outcome, stated before data:** MIXED is the most likely reading (§4). Stage A can also stop B0 as NOT INFORMATIVE before any outcome is read.

## 1. Question and what it can say

Q: at matched target-lane speed, do the plant's human mergers come to a stop before merging more often than mergers at NGSIM US-101 and I-80?

The measure counts stops before a merge, wherever they happen: on the ramp, in a ramp queue or at the lane end. It is not the lane-end standing that carries the E30 edge; the link is printed (§5). The field lanes differ: US-101's lane 6 is an auxiliary lane, and I-80's lane 7 is an on-ramp lane [VERIFY both against the NGSIM documentation].

## 2. Data (all stored)

- **Plant:** merge logs of the 480 no-control runs at 300 m in `merge_vv` (`vv_remote/vv_screen/vv/L300__nc__5300__*.json.gz`, seeds 7,492,000-479, run `6e96988`, sha checked).
  - Mergers are vehicles that entered on a ramp and left 3a_0 or 4a_0 to the main lane (`v5b/fleet/vv_merge.py` `_merge`).
  - Only the first record per vehicle is used; the number of repeat records is printed.
  - Merges in the first 10 s after warm-up are dropped, because their history is short.
  - Each record holds `min_speed_10s`: the lowest speed at any 0.1-s step in the 10 s before the merge, on the ramp and acceleration lanes. It also holds the target-lane leader and follower (`lead`, `lag`, within 200 m).
- **Field:** `v5b1_data/ngsim/ngsim_8ect-6jqj.csv` (md5 file beside it), with V4's merge frames, trajectory splits and smoothing (`docs/research/vv/ngsim_merges.py`).
- **Already seen (disclosed):**
  - V4 read the medians of the field and plant merges' speeds, lag gaps and speed differences to the follower. The band edges below were set after that.
  - The reading read the plant's lane-end standing totals.
  - V6 (Kolbe et al. 2023; SUMO's documentation) gives a prior that the plant stops more.
  - Not yet computed for either side: `min_speed_10s`, any stop share, band counts.

## 3. Measures

- **Stopped before merging (deciding):** minimum speed in the 10 s before the merge below a threshold.
  - Plant: `min_speed_10s` below 1 m/s.
  - Field: below 1 m/s and, separately, below 2 m/s. Both are checked against the plant at 1 m/s, because smoothing pulls short stops up and trajectory edges down (review finding 4).
  - Field window: every sample of the merger's trajectory in the 10 s before the merge frame, whatever its Lane_ID. Samples within 0.6 s of the trajectory's start or end are not used (the centred 1-s mean halves speeds there).
- **Censoring (field only):** a merger in view for less than 10 s before its merge frame is kept, with two bounds.
  - f_lo counts a censored merger with no observed stop as not stopped.
  - f_hi counts it as stopped.
  - The plant is never censored: r, rj and 3a, about 715 m, are always in view.
- **Bands:** two bandings, both deciding.
  1. The target-lane **leader's** speed at the merge (primary, because a stopped merger makes its follower brake).
  2. The **follower's** speed.
  - Bands: below 5, 5-10, 10-15, 15-20, and 20 m/s or more. A merger with no leader (or follower) within 200 m on the target lane forms its own band, on both sides (field: none within 200 m in view).
  - Plant: `lead.speed`, `lag.speed`. Field: the nearest vehicle ahead and behind on the target lane at the merge frame (V4's follower; the leader is added).
- **Mergers compared:** plant human mergers (cars and trucks) against all field mergers. Plant ALKS mergers, and plant shares split by follower type (human or ALKS), are printed only.

## 4. Stages, statistic and readings

**Stage 0, code check, no data:**
- Trace that the no-control runs keep the ramp-meter node `rm` all green for the whole run (`b_env.py:180`; reading §6 item 5).
- If it does not, a stop at the signal counts as a plant stop at merge 1. Merge 1 is then printed only, and the deciding plant shares use merge 2.

**Stage A, counts only (no stop is read):**
- Printed per site and per banding:
  - merger counts per band;
  - median band speed within each band;
  - the censored share;
  - repeat plant merges;
  - blocks per period.
- From these, before any stop is read:
  - the pooling is frozen (a band under 20 plant or 10 field mergers joins its neighbour towards 10-15 m/s);
  - a power table is computed over a grid of field shares (1, 5, 10, 20, 30, 50 %), under a stated design effect.
- Stage A outputs are committed before stage B.
- **Stop rule:**
  - If more than 20 % of a site's weight sits in pooled bands, that site is "not comparable" and B0 can read MIXED at most.
  - If the power table gives under 0.5 for MORE at a true difference of +10 points and under 0.5 for NOT MORE at a true difference of 0, at either site, B0 stops as **NOT INFORMATIVE** and goes back to the author without stage B.

**Stage B, the read:**
- **Standardised difference per site and banding:** D = Σ_b w_b × p_b − f, in percentage points.
  - w_b: the site's share of mergers in band b.
  - p_b: the plant's pooled stop share in band b.
  - f: the site's stop share.
  - Computed with f_lo and with f_hi.
- **Interval:** 95 % percentile from B = 20,000 joint resamples (rng 20261116).
  - Plant: seeds resampled.
  - Field: blocks of merge time resampled within each period, so mergers in one queue stay together; w_b and f come from the same resample.
  - Blocks of 1, 2 and 5 minutes; the widest interval decides.
- **Ratio:** the same, as the plant share over the field share.
- **Field-against-field reference:** D between US-101 and I-80, with the same code, printed. It shows how much two real sites differ.

| Reading | Rule (every one must hold) | Wording |
|---|---|---|
| **MORE** | lower bound of D > 0 at both sites; with f_hi; field thresholds 1 and 2 m/s; both bandings; widest interval | "at matched target-lane speed, the plant's human mergers stopped before merging more often than at two congested 2005 Californian sites, 45 minutes on one day each [VERIFY site facts] (plant a %, field b % and c %; the two sites differ by d points); of the plant's stoppers, e % stood in the last 30 m of the acceleration lane" |
| **NOT MORE** | upper bound of D ≤ +5 points and ratio upper bound ≤ 1.5 at both sites; with f_lo; both thresholds; both bandings; widest interval | "at matched target-lane speed, the plant's human mergers stopped before merging at most 5 points more often (95 % upper bound) than at two congested 2005 Californian sites, 45 minutes on one day each [VERIFY site facts] (plant a %, field b % and c %)" |
| **MIXED** | otherwise | all shares and intervals, no other wording |

The 5-point margin and the 1.5 ratio are judgements. No reading is a validation.

## 5. Printed, never deciding

- Raw (unstandardised) shares per site, band, plant merge (3a, 4a) and field period.
- Plant only:
  - shares by follower type (human, ALKS);
  - merge position along the acceleration lane, and the share of merges in the last 30 m;
  - the share of stoppers also counted in the lane-end standing log;
  - ALKS mergers.
- Field only: a 5-s window; merge position from the first ramp-lane sample, as a spread.

## 6. Consequences

| Reading | M1 | Next step |
|---|---|---|
| MORE | M1 keeps its wording and adds the MORE sentence, with the lane-end share e | back to the author: writing, or B1 with emergency braking and collisions as co-readings (V518 makes a VOID likely) |
| NOT MORE | M1 stays a limit and adds the NOT MORE sentence | B1 is not proposed, unless e shows the plant's stops sit mostly at the lane end; then back to the author |
| MIXED | M1 unchanged; the numbers are printed | back to the author |
| NOT INFORMATIVE (stage A) | M1 unchanged | back to the author |

A MORE is not attributed to SUMO's lane-change model alone: plant followers include ALKS, which accept larger gaps (V4: 1.66 s behind an ALKS against 1.36 s behind a human).

## 7. Order

1. Stage 0 code check.
2. Reader `docs/research/b0/b0_read.py` (stage A and stage B as separate commands), with tests on planted plant records and hand-made field trajectories:
   - a stop 12 s before the merge is not counted, and one 8 s before is;
   - a merger with 9 s of history is censored and enters f_lo and f_hi as stated;
   - a merger entering at 1.8 m/s is not read as stopped once edge samples are dropped;
   - a repeat plant merge is dropped.
3. Reader committed and its hash recorded. Then stage A, its outputs committed, then the stop rule. Then stage B, read once.
4. Laptop only: numpy and pandas on stored data, no simulation (V483); under the night CPU cap after 23:00.
5. A Fable check reproduces D from the outputs. Anything later is labelled post hoc.

## 8. Limits

- Two congested sites from 2005, 45 minutes on one day each, with different geometry and lane roles.
- Field speeds are smoothed; plant speeds are not. Both field thresholds must agree.
- Field trajectories are cut at the camera edge; the bounds carry that.
- Plant merges are instantaneous lane changes.
- Only no control is compared, at one demand.
- It says how often mergers stop before merging, not whether stopping at the lane end is realistic.

## 9. Review of v0 (one Fable agent, 2026-11-16)

| # | Finding | Applied |
|---|---|---|
| 1 | Blocker: the 10-s exclusion drops fast field mergers and favours NOT MORE | censored mergers kept; f_lo and f_hi bounds; plant merges in the first 10 s after warm-up dropped |
| 2 | Blocker: no common-support rule; open top band | stage A counts and frozen pooling; the 20 % not-comparable rule; band split at 20 m/s; a 200-m "none" band on both sides |
| 3 | Band variable affected by the stop | leader banding primary; both bandings must agree |
| 4 | Smoothing asymmetry | edge samples dropped; field 1 and 2 m/s both deciding |
| 5 | A 5-s window cannot be computed for the plant | field only, printed |
| 6 | NOT MORE unreachable or misleading | power table in stage A; ratio bound; reworded |
| 7 | No null; few clusters | field-against-field reference; blocks within periods; widest of 1/2/5-min |
| 8 | Consequence overclaimed | sentence states the lane-end share; follower type printed; NOT MORE's next step depends on it |
| minor | Repeat merges; disclosures; ramp signal; I-80 window; wording | first record only; §2; stage 0; whole trajectory before the merge frame; "informs", "45 minutes on one day each" |
