# Judge's ruling on the merge V&V for the E30 cell (merge_vv.md v1.1, V532)

**Sources** (the tag after each number gives its source):
- [v3]: /home/catalin/work/phd/v5b1_runs/vv_remote/vv_screen/v3.json
- [v1]: /home/catalin/work/phd/v5b1_runs/vv_remote/vv_trace/v1.json
- [id] and [sm]: vv_replay/ident.json and vv_smoke/smoke.json
- [vis]: vv_post/v1_visual
- [mech]: vv_post/mechanism
- [A] and [B]: vv_post/recompute_A and vv_post/recompute_B
- [prt]: vv_post/printed
- [V4f] and [V4p]: vv_v4/field.json and vv_v4/plant.json
- [v567]: vv_post/v567.json
- [judge]: my own check, /home/catalin/work/phd/v5b1_runs/vv_post/judge/rule_medians.{py,txt}, post hoc

C-D5: positive means v3w had less. Interval levels are as the plan defines them.

**Integrity.** Three independent recomputations ([A], [B], [prt]) reproduce every deciding number in [v3] exactly, and the nulls agree within Monte Carlo noise. The input checks are clean:
- [v3]: n = 480, nothing dropped, `bugs` and `void` empty, one CPU (AMD EPYC 7B13).
- [id]: 0 differences between rules or learners, in both the plain and the traced replays.
- [sm]: the smoke check passes.

None of the reader defects the recomputers found changes a deciding reading (§3).

## 1. Readings by the plan's §6 table

| Reading | Numbers | Outcome |
|---|---|---|
| V1 wiring | 0 wiring and 0 twin failures; 12 twin pairs; 18 traced runs [v1] | pass |
| V1 definition | 0 failures [v1] | no BUG |
| V1 classification and visual | 0 of 40 sampled seconds are non-events, so the one-sided 95 % upper bound is 7.2 % [vis]. Leaders: 93.2 % same lane, 6.8 % next lane, 0 off the route [v1] | **V1 MET** |
| V2 meter equality | `bugs.meter` empty [v3] | no BUG |
| V2: 0.1-s edge minus 1-Hz edge, 95 % | lr400_16_1 +0.23 [−0.41, +0.60]; grid_lr400_13_1 −0.05 [−0.56, +0.47] [v3] | **MET**, so PR-23 is closed for this cell |
| V3a replication (97.5 %, null bar 1.9 %) | lr +16.0 [+12.2, +20.3], null 1.175 %; grid +21.7 [+16.2, +25.2], null 1.075 % [v3] | **REPLICATED** |
| V3a main lane | lr +10.6 [+6.6, +14.5], null 1.075 %; grid +22.3 [+17.9, +26.4], null 0.925 % [v3] | **also shown on main-lane samples** |
| V3b HOLDS (both 97.5 % lower bounds above 0) | lr −21.0 [−28.2, −12.4]; grid −6.6 [−15.4, +3.0] [v3] | not met |
| V3b WORSE (98.75 % upper bound below 0, null bar 0.94 %) | lr [−29.0, −11.4], null 0.475 % (20,000 swaps × 4,000 resamples); grid upper bound +4.0 [v3] | **WORSE**, against lr400_16_1 only. For grid alone it is NOT SHOWN (my per-rule label) |
| V3b change, 600 m minus 300 m (95 %) | lr −37.0 [−44.4, −28.9]; grid −28.3 [−36.2, −19.1] [v3] | excludes 0 against both rules, so "depends on lane length" is licensed |
| Combination: NOT REPLICATED with any 600-m reading | — | does not apply (the screen REPLICATED) |
| Combination: REPLICATED with HOLDS | — | does not apply (HOLDS not met). "Shown at both lengths" is **not** licensed |
| V4, V5, V6 | descriptive (§2) | the field sentence and M1 are carried |
| V7 | no column uses the seed, event timing or a future state [v567] | **MET**, with the channel limits named. PR-15 can close |
| V462 gate | M1 and PR-28's period part remain | **stays shut** |

## 2. Fixed wordings, filled in

**V2.** "the 0.1-s edge is within 3 points of the 1-Hz edge against both rules"
- Differences as in the table above.
- The 0.1-s edges are +16.2 and +21.6; the 1-Hz edges +16.0 and +21.7 [v3].
- The missed share per arm runs from −0.003 % to −0.205 % (median per run) [v3]. Its sign is unexplained.

**V3a replication.** "replicated against lr400_16_1 and grid_lr400_13_1, 2 of E30's 14 competitors, no chords"
- Figures: +16.0 % [97.5 %: +12.2, +20.3] and +21.7 % [+16.2, +25.2] [v3].
- Post hoc: E30's own edge against lr was +9.9 [+6.2, +15.0] (V530). The intervals overlap, and no test of the difference was pre-stated. [mech] traces the gap to higher lr counts at merge 2 and in "rest" on these seeds; that is untested.

**V3a main lane.** "the edge is also shown on main-lane samples at 300 m (+10.6 % [+6.6, +14.5] against lr400_16_1; +22.3 % [+17.9, +26.4] against grid_lr400_13_1)". Added sentence: "a main-lane edge does not rule out main-lane congestion caused by the short lanes; 600 m is the direct test".

**Record sentence, against lr400_16_1.** "against lr400_16_1, v3w spent 16.0 % less time below 3 s TTC at 300 m and −21.0 % [−29.0, −11.4] at 600 m (WORSE); change −37.0 [−44.4, −28.9]; lane-end standing fell by 84.3 % [81.8] (v3w) and 95.8 % [93.8] (lr400_16_1) at merge 1 and 85.2 % [80.3] (v3w) and 97.4 % [96.5] (lr400_16_1) at merge 2; at 600 m the largest remaining deficit, in samples per run, sits on edge 1; the other 24 non-learning arms were not run at 600 m; neither the policy nor the rules were tuned for 600-m lanes; policy positions remapped, geometry not seen in training".

**Record sentence, against grid_lr400_13_1.** "against grid_lr400_13_1, v3w spent 21.7 % less time below 3 s TTC at 300 m and −6.6 % [−15.4, +3.0] at 600 m (NOT SHOWN); change −28.3 [−36.2, −19.1]; lane-end standing fell by 84.3 % [81.8] (v3w) and 96.6 % [94.6] (grid_lr400_13_1) at merge 1 and 85.2 % [80.3] (v3w) and 96.9 % [95.5] (grid_lr400_13_1) at merge 2; at 600 m the largest remaining deficit, in samples per run, sits on edge 1; [the rest as above]".

How the blanks were filled:
- Sources: [v3] v3a, v3b.holds, v3b.worse, v3b.change, v3b.cut, v3b.deficit_600.
- A negative b means more time.
- b's interval is given at the level of the reading that decided it: 98.75 % for WORSE; 97.5 % for the failed HOLDS, where the 98.75 % upper bound is +4.0.
- Choices where the plan is silent, for the author to approve: the plan does not say which arm fills x and y, so I give v3w and the opponent. The per-rule (HOLDS/WORSE/NOT SHOWN) label is my application of the plan.
- Edge 1 as the deficit group:
  - [v3]'s pooled form: +22.4 and +22.6 samples per run.
  - The C-D5 form gives the same group, at +22.0 [mech] and +21.8 [B].
  - The merge-area value flips sign between the two forms, so do not quote it (§3).

**VV-D12 clause ("with lane-end standing removed at merge m"): omitted.** The committed reader's cut is not met at either merge (`removed` false) [v3]. It requires v3w, both rules and no control. No control's lower bounds are 36.3 % and 15.3 %.

**Edge-1 pre-statement.** "a WORSE or NOT SHOWN carried by edge 1 is not a lane-length effect; edge 1 is unchanged at 600 m". It applies (§3).
- The E30 description holds at both lengths: v3w has 26.4 and 26.5 edge-1 samples per run; p333 28.0 and 27.5; lr 3.2; grid 3.3. At least 98 % of them fall in the hold period [mech].

**V4.** "compared with two congested Californian sites (2005) [VERIFY site facts]; a comparison, not a validation".

Accepted lag time gap (follower above 5 m/s), median [95 %]:

| Site or group | Lag gap | n |
|---|---|---|
| US-101 | 1.09 s [1.00, 1.17] | 338 |
| I-80 | 1.10 s [0.98, 1.21] | 233 |
| Plant, human mergers in the 480 no-control runs at 300 m | 1.58 s [1.57, 1.59] | 91,235 |
| Plant, behind a human follower | 1.36 s [1.34, 1.37] | — |
| Plant, behind an ALKS | 1.66 s [1.65, 1.67] | — |

Speed difference, merger minus follower:
- US-101 +1.00 m/s [0.79, 1.21]; I-80 +0.33 [0.25, 0.45].
- Plant +1.10 [1.05, 1.16]; behind a human +0.34 [0.32, 0.37]; behind an ALKS +1.56 [1.48, 1.64].

Spread over periods:
- Lag: US-101 0.99-1.14 s; I-80 1.01-1.21 s.
- Speed difference: US-101 0.95-1.11 m/s; I-80 0.25-0.47 m/s.

Sources: [V4f], [V4p]. Field intervals are over vehicles, plant intervals over runs. Plant merges are instantaneous lane changes; field merges are timed at the lane-ID change (US-101) or the line crossing (I-80). The ALKS mergers (151,319) are excluded.

**V5** (context, not validation; labels as corrected by the checker [v567]). Measured to the lane end, the plant is 294.72 m at full width, with no taper.

| Source | Guidance | Where 295 m sits |
|---|---|---|
| DMRB CD 122 v1.1.1, rural motorway parallel merge | auxiliary lane at least 230 m (nose tip to taper start) plus a 75 m taper; 370 m or more at high flows | above the minimum, below the extended length (flow condition unchecked); 10 m short of 305 m to the taper end |
| TxDOT RDM Table 4-18, 60-65 mph | La 55-113 m (50 mph ramp) to 366-430 m (from a stop), taper excluded | above for a free-flowing ramp, below from a stop |
| Caltrans HDM 504.3 (not a plan candidate) | metered entrance at least 91.4 m; 304.8 m above 1,500 veh/h; plus a 183 m taper | above the minimum, about 10 m below the high-volume minimum (condition unchecked) |
| RAA 2008 via BASt V277 (secondary) [VERIFY] | 250 m including a 60 m taper | above |

- Every source has an end taper; the plant has none.
- "Relevant sections read in full." AASHTO was not read [VERIFY].

**V6.** **NOT INFORMATIVE** under the pre-stated search, dated 2026-11-16 [v567].
- Google Scholar was blocked, so OpenAlex and web search were substituted. Seven sources were read in full, and none compares SUMO's lane-end merging with field data.
- **Post hoc, outside the fixed terms**, found and re-checked by the checker:
  - Kolbe et al. (2023, arXiv:2308.01093) ran SUMO with IDM and the default lane-change model on the A565 Bonn-Beuel on-ramp and compared it with drone data. They report that "the IDM model produces large negative accelerations at the end of the on-ramp lane because vehicles stop and wait for a suitable gap" [one site; VERIFY the SUMO version and parameters; the 2024 Applied Sciences version was not opened].
  - SUMO's documentation (Simulation/Motorways) says SUMO drivers decelerate on approaching an acceleration-lane end, unlike humans, and suggests longer acceleration lanes than in reality [VERIFY the current page].
- Neither source changes the reading. Both strengthen M1.

**V7.** **MET**: no column of v3w's 16-column actor observation uses the seed, event timing or a future state. Two inspections were reconciled [v567]. Disclosures:
- Roadside columns: 12 (own 200-m bin mean speed), 13 (merge-1 zone mean speed), 15 (count on 3a_0 + 4a_0).
- Column 14's sign reaches any range (the nearest vehicle on 3a_0 or 4a_0, magnitude clipped at 100 m).
- Sensing range is not enforced for columns 6, 7, 9 and 14.
- During training only, the critic read privileged globals g7 (insertion backlog), g8 (episode clock) and g9 (carries the demand level).

**M1.** "the plant's standing at acceleration-lane ends is not validated; the E30 edge sits mostly where it occurs".

## 3. Where pre-stated rules pull apart

**Rule P, the edge-1 pre-statement.** The plan does not define "carried by". I applied it using the plan's own printed items:
- The 600-m edge with edge 1 left out is lr +8.1 [95 %: +1.9, +15.1] and grid +18.4 [+11.2, +25.6] [v3].
- The largest deficit group is edge 1.
- Edge-1 counts do not change with lane length (post hoc): v3w +0.11 [−0.28, +0.49]; lr +0.01 [−0.29, +0.29] [mech].

So both the WORSE (lr) and the NOT SHOWN (grid) are carried by edge 1.
- **Licenses:** "the 600-m WORSE is carried by edge 1, which is unchanged at 600 m; it is not a lane-length effect".
- **Does not license:**
  - dropping or softening the WORSE reading;
  - "the edge holds at 600 m outside edge 1" (a printed item at 95 %, with no null);
  - "lane length has no effect".

**Rule C, the change rule.** The change excludes 0 against both rules.
- **Licenses:** "the edge depends on acceleration-lane length (change −37.0 [−44.4, −28.9] and −28.3 [−36.2, −19.1])".
- **Does not license:**
  - any mechanism;
  - that the 300-m behaviour is or is not an artefact (§0 Q3, §5);
  - "v3w turns worse because the lanes are longer" (Rule P forbids that).

**They are compatible.** C is about how big the edge is across lengths. P is about what the 600-m reversal is made of. Both statements go into the record together.

Explanation for the author (post hoc, decides nothing):
- C-D5 divides by the rule's median total, which falls from 1,375.5 to 76.5 for lr [mech].
- So a constant deficit of about 22 edge-1 samples weighs −1.7 points at 300 m and about −28 points at 600 m [mech].
- What the longer lanes removed is the merge-area advantage that outweighed that deficit at 300 m. At 300 m the merge area supplies about 92 % (lr) and 96 % (grid) of the edge [mech].
- With edge 1 left out, the change is lr −9.8 [−17.0, −1.8] and grid −5.0 [−12.4, +3.1] [A], [B].
- The split of the −37 points depends on the accounting:
  - by counts (Shapley): merge −20.7, rest −16.6, edge 1 +0.3;
  - by terms of the statistic: edge 1 −27.2, the rest −10.2 [mech].
- Neither split is pre-registered.
- The plan stated before data that "NOT SHOWN or WORSE is a likely outcome". The observed no-edge-1 edge (+8.1) lies in the range of the expectation table's edge-1 column (+6.0 to +11.5). The total (−21.0) is below that table's lowest row (−5.6). This comparison is descriptive.

**VV-D12.** The plan fixes neither the form of the cut nor the arms. The committed reader is the pre-data operationalisation: 1 − median600/median300, applied to v3w (pooled), both rules and no control. Under it, the reading is "not removed".
- Under the same form without no control, both merges would read "removed". Under mean-based forms, no arm passes ([A], [B]).
- Both of those are post hoc and unusable. The record states the form and that no control decides the reading.

**Reader print defects** (none deciding; do not quote these values):
- The `deficit_600` merge-area value depends on the form: +5.8 pooled versus −6.3 in the C-D5 form.
- Cells printed as 0.0 [0, 0] where the rule's median is 0 are not readable: g_rest at 600 m [mech], and p_taper vs lr at 300 m and vs both rules at 600 m [judge].
- p_before at 600 m is coarse: the rule median is 1 [judge].
- The CPU VOID check cannot fail. That is moot here, since only one CPU was used.
- A missing key is read as 0. One no-control row (600 m) is affected, and it is in no deciding comparison.
- Status prints a bare "V3b WORSE" with no edge-1 qualifier.

## 4. Plain-words summary for the author

**What the committee can be told:**
1. **The counter counts what we say.** In 18 traced runs, the wiring, definition and twin checks all pass. All 40 randomly drawn counted seconds are real closing approaches, which bounds the share of non-events below 7.2 %. Tracing does not change a run.
2. **1-Hz sampling is enough for this edge.** The 0.1-s edge is within 0.6 points of the 1-Hz edge.
3. **On 480 new seeds, with 300-m lanes, the edge replicates** against the two closest rules (+16.0 %, +21.7 %). It also shows on main-lane samples.
4. **The edge depends strongly on acceleration-lane length.**
   - With 600-m lanes it falls by 37 and 28 points.
   - v3w becomes WORSE than lr400_16_1 (−21.0 %) and is not shown different from grid_lr400_13_1.
   - Both the direction and the edge-1 effect were stated before the data.
5. **The reversal sits on edge 1,** on the approach to the 30 km/h slowdown during its hold period.
   - There v3w has about 22 more samples per run than the lr rules, at both lengths.
   - Left out, v3w still has less close-following at 600 m (+8.1 %, +18.4 %). This figure is printed, not deciding.
6. **Other measures at 600 m** (printed, not deciding):
   - TTC below 2 s still favours v3w: +26.0 [+16, +39] against lr.
   - Hard braking `b45_step` is worse for v3w: −5.1 [−7.1, −3.2] and −5.3 [−7.4, −3.1].
   - v3w has more distinct encounters: −34.8 and −20.8.
   - Delay is +0.7 [+0.4, +1.0] against lr, in v3w's favour [v3].
   - Each must carry the fixed reward sentence.
7. **The policy uses nothing a real car could not know.** Some inputs assume a roadside feed.
8. **Merges compared with NGSIM:** the plant accepts longer lag gaps than the field does (descriptive only).
9. **The 295-m lane is a design-guidance length,** but it has no end taper.

**What cannot be claimed:**
- "Verified and validated" (the V462 gate is shut).
- "The edge survives longer lanes" or "was shown at both lengths".
- Whether the 300-m behaviour is a plant artefact.
- That SUMO's lane-end standing is realistic (M1). Post hoc evidence from one site points the other way.
- That merges are validated, or anything about lateral or merge-conflict safety.
- Anything about the other 24 non-learning arms at 600 m.
- That the reversal is caused by longer lanes.

## 5. Record entries (plant_vv_record_v0.md)

| ID | Requirement | Method | Evidence | Status |
|---|---|---|---|---|
| PR-01 | (unchanged) | I | **r2m3 net inspected at 6e96988** (V5; the 300-m net keeps E30's hash, V533). 3 main lanes; one-lane ramps; 3a_0 and 4a_0 294.72 m at full width to an abrupt dead end, no taper; 100 km/h on every edge including the ramps; static signal at rm (79/6/5 s). **Spacing:** end of 3a (x 3,800) to start of 4a (x 5,000) is 1.2 km; the ramp junctions are 1.5 km apart. **Design context (not validation):** CD 122 above its minimum and below its extended length; TxDOT above for a free-flowing ramp, below from a stop; Caltrans about 10 m below its high-volume minimum; RAA via V277 above [VERIFY]. Every source has a 55-183 m end taper, which the plant lacks [v567] | met for lanes, lengths and limits; "1.2 km apart" to be reworded by the author |
| PR-08 | (unchanged) | D, A | Existing evidence plus **V4** (VV-D5, V82 relaxed for this question): "compared with two congested Californian sites (2005) [VERIFY site facts]; a comparison, not a validation". Lag gap: field 1.09 and 1.10 s; plant 1.58 s (1.36 s behind a human, 1.66 s behind an ALKS). Speed difference: field +1.00 and +0.33 m/s; plant +0.34 behind a human, +1.56 behind an ALKS [V4f, V4p]. Merges in the plant are instantaneous | limit: not validated against real traffic; merges compared descriptively |
| PR-15 | (unchanged) | I | **V7:** `CavEnv._obs` (b_env.py:923-980, 6e96988); the actor reads 16 local columns; none uses the seed, event timing or a future state. Limits: roadside columns 12, 13 and 15; column 14's sign at any range; sensing range not enforced for columns 6, 7, 9 and 14; the critic alone read g7-g9 in training [v567] | met, with the channel limits named |
| PR-19 | (unchanged) | T | V386. **V&V tracer:** 12 traced runs equal their untraced twins; 6 traced stored-seed runs equal their stored rows on every traffic key; the identity replay of 9 arms (plain and traced) shows 0 differences [v1, id] | met; rerun after tracing changes |
| PR-23 | (unchanged) | T | Existing evidence plus **V2** (E30 cell, 300 m, seeds 7,492,000-479): meter whole-second count = `ttc_net` and half-second count = `ttc_half` in every run. "The 0.1-s edge is within 3 points of the 1-Hz edge against both rules": +0.23 [−0.41, +0.60] and −0.05 [−0.56, +0.47]. Missed share −0.003 % to −0.205 %, cause not established. Meter written fresh in `vv_merge.py` (V533) [v3] | met for the E30 cell against lr400_16_1 and grid_lr400_13_1; 1 Hz elsewhere stays a limit |
| PR-24 | (unchanged) | D | V283. **V1 on `ttc_net`:** 18 runs (w1u500, lr400_16_1, no control; 300 and 600 m); 0 wiring, definition or twin failures; logs reproduce `ttc_net`, the road groups, `end_stop`/`end_stop2`, the main-lane count and the encounters. Leaders 93.2 % same lane, 6.8 % next lane, 0 elsewhere. 0 of 40 drawn seconds are non-events (bound 7.2 %); 2 of the 40 have a leader standing at a lane end. Descriptive: 19 of 40 are below 5 m/s, including 4 creeps in standing queues, which the definition counts. The bound covers the traced runs only [v1, vis] | met for `ttc_net`, lane-end standing, the main-lane count and encounters; partial for `b45_step`, `ttc2`, `ttc15`, `sev3` and jams [VERIFY whether earlier traces exist] |
| PR-27 | (unchanged) | A | Baseline v1 lane table; V4 merge comparison (see PR-08) | limit for merges (descriptive); gap for per-lane flows and speeds against detectors |
| PR-28 | (unchanged) | A, T | V396; **V3** (9 arms × 480 seeds × 300 and 600 m). (1) The V3a replication and main-lane sentences with their added sentence (§2). (2) Both record sentences, and "the 600-m WORSE is carried by edge 1, which is unchanged at 600 m; it is not a lane-length effect". (3) "The edge depends on lane length." (4) VV-D12 not met: committed cut 1 − median600/median300, decided by no control. (5) Period part, printed only, vs lr: 300 m hold −63.4 [−71.2, −54.1], after −14.0, rest +19.9 [+15.7, +23.8]; 600 m hold −565, after −28.6, rest +9.3 [+2.8, +17.6]; taper not readable. (6) Fixed reward sentence beside `ttc2`/`ttc15`/`sev3`/`b45_step` [v3] | partial: lane length and road location answered; period part open; carries M1; whether the 300-m behaviour is an artefact is not answered |
| §4 M1 | — | — | "M1: the plant's standing at acceleration-lane ends is not validated; the E30 edge sits mostly where it occurs." V6 NOT INFORMATIVE. Post hoc: Kolbe et al. 2023 and SUMO's Motorways page [VERIFY]. At 600 m the arms still stand at the lane ends: v3w median 32 and 77 veh-s, no control 110 and 412 [v3] | limit |

After the author approves these rows, recount the tally line.

## 6. Consequence for the E30 sentence, and the gate

**E30's PASS reading is unchanged.** There is no BUG (V1 definition, V2 meter), and the replication line reads REPLICATED. By the plan's header, nothing else can change it.

**Additions to the verification.md sentence:**
- the replication wording;
- both record sentences;
- the edge-1 qualifier;
- "the 0.1-s edge is within 3 points of the 1-Hz edge against both rules";
- M1;
- the V4 field sentence.

**Wording rules:**
- The sentence must not use "survives", "shown at both lengths" or "verified and validated".
- My suggestion, not fixed by the plan: name the plant "with 295-m acceleration lanes ending without a taper". The "at least 6.2 %" holds for those lanes only. At 600 m it was not shown against grid_lr400_13_1 and reversed against lr400_16_1.

**The V462 gate stays shut.** M1 and PR-28's period part remain (§0 Q6, §6 V7 row), and the record is not yet reviewed. PR-15 can close, and PR-24 is met for `ttc_net`.

## 7. Open items

1. **Author approvals where the plan is silent:**
   - the per-rule HOLDS/WORSE/NOT SHOWN label;
   - which arms fill the standing slot;
   - the interval level shown for b;
   - "carried by edge 1" judged from the printed no-edge-1 edge and the largest-deficit group.
2. **Record:** state the VV-D12 form and its arm set; quote no merge-area `deficit_600` value; mark zero-median cells as not readable. Any reprint by a fixed reader is post hoc.
3. **PR-24:** trace or locate traces for `b45_step`, `ttc2`, `ttc15`, `sev3` and jams.
4. **PR-28's period part** has no pre-stated test. Closing it needs a new item.
5. **V6:** the pre-stated search is incomplete:
   - Google Scholar was not run;
   - the 2013-2017 SUMO volumes were only partly screened;
   - Barthauer 2016 was not read;
   - the Berghaus & Oeser 2025 full text is blocked.

   Read and check Kolbe 2023 (and its 2024 journal version) and SUMO's Motorways page before citing [VERIFY].
6. **V5:**
   - check the flow triggers against the plant (CD 122 85 % of capacity; Caltrans 1,500 veh/h; TxDOT 4,600 veh/h);
   - check whether the rm signal runs in the E30 arms;
   - record the missing taper as a design deviation;
   - AASHTO and RAA were not read as primary sources.
7. **V7:** the share of decisions with a leader or follower beyond 150 m is unmeasured; a read-only count would size it. The commit the policies were trained at is not established.
8. **V4:** check the site facts and the NGSIM lane roles [VERIFY]. The plant side covers no-control runs at 300 m only.
9. **Untested explanations:**
   - why v3w and p333 have about 22 more edge-1 samples than the lr rules (one inference: LocalRule widens ALKS headways below 16 m/s ahead);
   - why lr's counts are higher here than in E30;
   - the negative missed share;
   - the no-control row with `ttc_net` = 0 (seed 7,492,030, 600 m).
10. **Process:** the V1 visual agent ran a few sub-second Python prints without `nice`, always one at a time. Its `__pycache__` folder and [prt]'s `time.log` are left in their output folders.
11. **decisions.md:** record the author's acceptance of this ruling under a new V# (memory: record every decision).

My only compute was one `nice -n 19` pass over s6_rows.jsonl for the rule medians by period. No repo or run file was modified.

Files are in /home/catalin/work/phd/v5b1_runs/vv_post/judge/:
- rule_medians.py
- rule_medians.txt