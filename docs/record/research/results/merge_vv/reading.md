# Merge V&V: reading (V536)

Plan: `docs/research/protocols/merge_vv.md` v1.1 (V532). Run: `vv/merge` 6e96988 on vast.ai instance 60874907 (AMD EPYC 7B13), 2026-11-15/16, about 11.2 h and $1.7. Files: `run/` (the run's own outputs and checksums) and `post/` (verification and analyses).

How this was read:
- The committed reader read once, on the machine (`run/status.txt`: "V2 MET | V3a REPLICATED | V3b WORSE", no VOID, no drops).
- Two independent re-implementations reproduced every deciding number exactly and the nulls within Monte Carlo noise (`post/analysis_ra.md`, `post/analysis_rb.md`). A third reproduced the V2 edges and the 752 printed numbers (`post/analysis_pr.md`).
- A judge applied §6 (`post/judge_draft.md`). Two skeptics checked it: one found no number wrong; the other found one blocker and several majors in the wording (`post/skeptics.json`). This file is the judge's draft with every finding applied.

C-D5 sign: positive means v3w had less close-following. Each interval states its level.

## 1. Pre-stated readings

| Reading | Numbers | Outcome |
|---|---|---|
| V1 wiring | 12 twin pairs equal; 0 wiring failures | pass |
| V1 definition | 0 failures (gap rebuilt, no cross-lane or off-route leader) | no BUG |
| V1 visual | 0 of 40 drawn seconds are non-events: 95 % upper bound about 7 %, for the 18 traced runs (w1u500, lr400_16_1, no control; 300 and 600 m) only. No edge-1 sample was drawn | **MET** |
| V2 meter equality | whole-second count = `ttc_net`, half-second count = `ttc_half`, every run | no BUG |
| V2 0.1-s minus 1-Hz edge, 95 % | lr400_16_1 +0.23 [−0.41, +0.60]; grid_lr400_13_1 −0.05 [−0.56, +0.47] | **MET** (300 m only) |
| V3a replication, 97.5 % lower, null bar 1.9 % | lr400_16_1 +16.0 [+12.2], null 1.18 %; grid_lr400_13_1 +21.7 [+16.2], null 1.08 % | **REPLICATED** |
| V3a main-lane sensitivity | lr400_16_1 +10.6 [+6.6], null 1.08 %; grid_lr400_13_1 +22.3 [+17.9], null 0.93 % | **also shown on main-lane samples** |
| V3b HOLDS, 97.5 % lower bounds | lr400_16_1 −21.0 [−28.2]; grid_lr400_13_1 −6.6 [−15.4] | not met |
| V3b WORSE, 98.75 % upper bound, null bar 0.94 % | lr400_16_1 −11.4, null 0.475 % (20,000 swaps); grid_lr400_13_1 +4.0 | **WORSE** (decided by lr400_16_1; against grid_lr400_13_1 neither bound excludes 0) |
| V3b change, 600 m minus 300 m, 95 % | lr400_16_1 −37.0 [−44.4, −28.9]; grid_lr400_13_1 −28.3 [−36.2, −19.1] | excludes 0 against both: **the edge depends on lane length** |
| VV-D12 standing removed | reader's cut 1 − median600/median300 over v3w, both rules and no control; no control's 95 % lower bounds 36.3 % and 15.3 % | **not met** (decided by no control) |
| V7 | no column uses the seed, event timing or a future state | **MET**, channel limits named |
| V4, V5, V6 | descriptive | §4 |

Combination rows (§6): "NOT REPLICATED with any 600-m reading" and "REPLICATED with HOLDS" do not apply. "The edge was shown at both lengths" is not licensed.

## 2. Fixed sentences, filled

**V2:** "the 0.1-s edge is within 3 points of the 1-Hz edge against both rules". Missed share per arm −0.003 % to −0.205 % (cause not established).

**V3a:** "replicated against lr400_16_1 and grid_lr400_13_1, 2 of E30's 14 competitors, no chords" (+16.0 % and +21.7 %). "The edge is also shown on main-lane samples at 300 m (+10.6 % [97.5 %: +6.6, +14.5] against lr400_16_1; +22.3 % [+17.9, +26.4] against grid_lr400_13_1)". "A main-lane edge does not rule out main-lane congestion caused by the short lanes; 600 m is the direct test."

**V3b, against lr400_16_1:** "against lr400_16_1, v3w spent 16.0 % less time below 3 s TTC at 300 m and −21.0 % [98.75 %: −29.0, −11.4] at 600 m (WORSE); change −37.0 [95 %: −44.4, −28.9]; lane-end standing fell by 95.8 % [95 % lower 93.8] for lr400_16_1 and by 92.6-97.1 % for the five v3w learners at merge 1, and by 97.4 % [96.5] and 92.7-95.7 % at merge 2; at 600 m the largest remaining deficit, in samples per run, sits on edge 1; the other 24 non-learning arms were not run at 600 m; neither the policy nor the rules were tuned for 600-m lanes; policy positions remapped, geometry not seen in training".

**V3b, against grid_lr400_13_1:** "against grid_lr400_13_1, v3w spent 21.7 % less time below 3 s TTC at 300 m and −6.6 % [97.5 %: −15.4, +3.0; 98.75 % upper +4.0] at 600 m (cell reading WORSE, decided by lr400_16_1; not shown against this rule); change −28.3 [95 %: −36.2, −19.1]; lane-end standing fell by 96.6 % [94.6] for grid_lr400_13_1 and by 92.6-97.1 % for the v3w learners at merge 1, and by 96.9 % [95.5] and 92.7-95.7 % at merge 2; at 600 m the largest remaining deficit, in samples per run, sits on edge 1; the other 24 non-learning arms were not run at 600 m; neither the policy nor the rules were tuned for 600-m lanes; policy positions remapped, geometry not seen in training".

Filling choices the plan leaves open (author to confirm): v3w's standing is given per learner (post hoc, no interval) because the reader's pooled form (84.3 % [81.8] and 85.2 % [80.3]) takes the median of a per-seed mean of five heavy-tailed learners and understates every learner's own cut. Edge 1 is the largest deficit group in both forms (pooled +22.4 and +22.6 samples per run; C-D5 numerator +22.0 and +21.8). The merge-area deficit is not quoted: it changes sign with the form against lr400_16_1 (+5.8 pooled, −6.3 C-D5).

**Edge-1 pre-statement**, factual content only: v3w's edge-1 deficit is unchanged by lane length (post hoc paired difference in v3w's edge-1 count +0.11 [95 %: −0.28, +0.49] per run; the rules' +0.01 and +0.05); edge 1 is geometrically unchanged (checked in every row). As the plan described for E30, v3w and p333 have about 25-27 edge-1 samples per run (median), at least 98 % in the slowdown's hold period, against about 3 for the lr rules (96-97 % in hold). The deficit itself is therefore not a lane-length effect. The pre-statement does not make the WORSE reading "not a lane-length effect": the change between the lengths sits outside edge 1 (next section).

## 3. Why 600 m reads WORSE (post hoc, decides nothing)

Source: `post/analysis_mech.md`.
- **At 300 m** the merge areas supplied about 92 % (lr400_16_1) and 96 % (grid_lr400_13_1) of the edge; edge 1 cost about 1.7 points. v3w already stood less at the lane ends than the rules (median 128-193 against 274 veh-s at merge 1; 436-513 against 900 at merge 2).
- **At 600 m** most lane-end standing disappears for every controlled arm, and the rules' typical seed goes nearly quiet: lr400_16_1's median total falls from 1,375.5 to 76.5 samples per run. The unchanged edge-1 deficit of about 22 samples then weighs about −28 points instead of −1.7.
- **Which counts changed** (exact Shapley split of the −37.0 change against lr400_16_1): merge area −20.7, rest (mostly merge spillback) −16.6, edge 1 +0.3. The change is a loss of the merge-area advantage, not a new deficit.
- **With edge 1 left out**, the 600-m edge is +8.1 % [95 %: +1.9, +15.1] against lr400_16_1 and +18.4 % [+11.2, +25.6] against grid_lr400_13_1 (printed, no null; not a reading).
- **Median against mean:** the 600-m counts are zero-inflated and heavy-tailed (lr400_16_1 median 76.5, mean 255). A mean-based form gives +23.6 % and +22.3 % in v3w's favour. Split by lr400_16_1's merge-area count, the learner runs have fewer samples than the rule on 3 %, 41 % and 78 % of seeds in the lower, middle and upper thirds. v3w's remaining 600-m advantage sits in the seeds where the rules' merges break down; the median seed is a quiet-merge seed where edge 1 dominates. This is disclosed, not used: the deciding statistic is C-D5, and WORSE stands.
- **Consistency with E30** (stored rows, 300 m, other seeds): v3w's counts agree within about 3 %; the larger edge here against lr400_16_1 (+16.0 against E30's +9.9) comes from that rule's higher merge-2 and rest counts on these seeds (untested).

## 4. Printed, never deciding

Other measures, C-D5 (95 %); positive favours v3w:

| Measure | lr 300 m | lr 600 m | grid 300 m | grid 600 m |
|---|---|---|---|---|
| delay | +2.3 [+1.2, +3.1] | +0.7 [+0.4, +1.0] | +0.9 [+0.1, +1.7] | +0.2 [−0.1, +0.5] |
| TTT (`N`) | +0.5 [+0.2, +0.7] | +0.2 [+0.1, +0.2] | +0.2 [−0.0, +0.4] | +0.0 [−0.0, +0.1] |
| served flow | +0.6 [+0.4, +0.8] | +0.0 | +0.2 [+0.1, +0.4] | +0.0 |
| `b45_step` | +5.3 [+2.7, +7.5] | −5.1 [−7.1, −3.2] | +5.3 [+2.6, +7.8] | −5.3 [−7.4, −3.1] |
| `ttc2` | +35.3 | +26.0 [+16, +39] | +42.7 | +30.0 [+18, +40] |
| `ttc15` | +24.7 | +0.0 [0, +40] | +38.4 | +10.0 [0, +40] |
| `sev3` | +21.8 | +0.0 [0, 0] | +24.2 | +0.0 [0, +20] |
| distinct encounters | +12.1 [+8.5, +15.4] | −34.8 [−40.5, −26.8] | +17.7 | −20.8 [−28.2, −12.7] |

"TTC below 3 s and braking at 3 m/s² or harder are terms of v3w's training reward; TTC below 2 s and 1.5 s are stricter versions of the rewarded event and `b45_step` of the rewarded braking; only DRAC (`sev3`) is outside the reward." At 600 m, `ttc15` and `sev3` medians are 1-2 events, so the percentages move in coarse steps; cells where the rule's median is 0 (rest and taper at 600 m) are not readable.

- Collisions over 480 runs (300 / 600 m): learners 0/0, lr 1/0, grid 2/1, p333 1/0, no control 0/1. Teleports 0.
- Every rule beats no control on delay by more than 10 % at 600 m: lr +29.3 [+28.2, +30.0], grid +29.3 [+28.5, +30.0], p333 +30.3 [+29.6, +31.3].
- Lane-end standing at 600 m: controlled arms 5-12 (merge 1) and 21-32 (merge 2) veh-s per run, 1-2 vehicles; no control 110 and 412 veh-s (7 and 19 vehicles).
- Column 15 never at its cap for the learners at 600 m (0 of about 32 M decisions each).

**V4** (VV-D5): "compared with two congested Californian sites (2005) [VERIFY site facts]; a comparison, not a validation". Accepted lag gap (median, 95 %): US-101 1.09 s [1.00, 1.17] (n 338), I-80 1.10 s [0.98, 1.21] (n 233); plant, human mergers in the 480 no-control runs at 300 m, 1.58 s [1.57, 1.59] (1.36 s behind a human, 1.66 s behind an ALKS). Speed difference to the follower: US-101 +1.00 m/s, I-80 +0.33; plant +1.10 (+0.34 behind a human, +1.56 behind an ALKS). Plant merges are instantaneous lane changes; field merges are timed at the lane-ID change (US-101) or the line crossing (I-80). The field extraction ran before the plant log was read.

**V5** (context only; relevant sections read in full): 295 m to the lane end, at full width, no taper.

| Source | Guidance | Where 295 m sits |
|---|---|---|
| DMRB CD 122 v1.1.1, rural motorway parallel merge | auxiliary lane ≥ 230 m plus 75 m taper; ≥ 370 m at sustained high flows | above the minimum, below the extended length (flow condition unchecked); 10 m short of 305 m to the taper end |
| TxDOT RDM Table 4-18, 60-65 mph | La 55-113 m (50 mph ramp) to 366-430 m (from a stop), taper excluded | above for a free-flowing ramp, below from a stop |
| Caltrans HDM 504.3 (not a plan candidate) | ≥ 91.4 m; ≥ 304.8 m above 1,500 veh/h ramp volume; 183 m taper | above the minimum, about 10 m below the high-volume length (condition unchecked) |
| RAA 2008, via BASt report V277 (secondary) | 250 m including a 60 m taper | above [VERIFY primary] |

Every source requires an end taper; the plant has none. AASHTO was not read [VERIFY].

**V6:** the pre-stated search could not be run as fixed (Google Scholar blocked automated access). The substitute (OpenAlex and web search with the fixed terms, TIB SUMO proceedings 2020-2026 by title; 2013-2017 volumes partly) read 7 sources in full; none compares SUMO's lane-end merging with field data. Post hoc, outside the fixed terms: Kolbe et al. (2023, arXiv:2308.01093, read in full by the checker; key sentence re-checked) compared SUMO with IDM and the default lane-change model on the A565 Bonn-Beuel on-ramp against drone trajectories and found that "the IDM model produces large negative accelerations at the end of the on-ramp lane because vehicles stop and wait for a suitable gap"; the authors call this behaviour unrealistic [one site; graphical; SUMO version and parameters not stated; the 2024 journal version not opened]. SUMO's own documentation (1.27.1, `Simulation/Motorways.md`) says SUMO drivers decelerate on approaching the end of an acceleration lane, unlike humans, and suggests making acceleration lanes "somewhat longer than in reality". Both strengthen M1.

**V7:** the actor reads 16 columns (`CavEnv._obs`, b_env.py:923-980); none uses the seed, event timing or a future state (two inspections, reconciled; `post/v567.json`). Stated assumptions: columns 12, 13 and 15 come from a roadside feed (12 is also read by LocalRule; 13 and 15 only by rules outside this study); column 14's sign tells which side the nearest acceleration-lane vehicle is at any range; sensing range is not enforced for columns 6, 7, 9 and 14 (share of decisions beyond 150 m unmeasured); in training only, the critic read the insertion backlog, the episode clock and a term carrying the demand level.

## 5. Consequences

- **E30's PASS reading stands** under its own protocol: no BUG, and the replication reads REPLICATED.
- **Its meaning narrows further.** The edge is a property of this plant's 295-m acceleration lanes, which end without a taper and where SUMO's vehicles stand at the lane end. With 600-m lanes it is not shown against grid_lr400_13_1 and reverses against lr400_16_1 on the median seed. Whether the 300-m behaviour is an artefact is not answered (§5 of the plan).
- **The E30 sentence must carry:** the replication line, both record sentences, "the 0.1-s edge is within 3 points of the 1-Hz edge against both rules", M1 and the V4 sentence. It must not use "survives", "shown at both lengths" or "verified and validated". Approved (V537): scope it as "in this plant, with 295-m acceleration lanes ending without a taper", and never call the edge a safety benefit.
- **The V462 gate stays shut:** PR-15 closes, but PR-24 is met only for the traced counters and PR-28 is partial (period part open; the artefact question unanswered); the record is not reviewed.

## 6. Open items

1. Done (V537): the author approved the §2 filling choices and the E30 scope wording.
2. PR-24: trace `b45_step`, `ttc2`, `ttc15`, `sev3` and jams before they enter a claim.
3. PR-28 period part: no pre-stated test; closing it needs a new item.
4. V6: Google Scholar not run; Barthauer (SUMO 2016) not read; Berghaus and Oeser 2025 full text blocked.
5. V5: flow triggers against the plant's ramp volumes; whether the rm signal runs in the E30 arms; AASHTO and RAA primaries.
6. V7: count decisions with a leader or follower beyond 150 m.
7. V4: check the NGSIM site facts and lane roles [VERIFY].
8. Untested: why v3w and p333 have about 22 more edge-1 samples than the lr rules (one inference: LocalRule widens ALKS headways when the roadside speed ahead drops below 16 m/s); the negative missed share; the no-control 600-m row with `ttc_net` = 0 (seed 7,492,030).
