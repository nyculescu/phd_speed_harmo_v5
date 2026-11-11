# plant_choice: the plant as a choice (author's item 2)

**Basis.** Ledger rows read in full: V139-V149, V177-V189, V244-V256, V271, V314-V329, V342, V370-V376, V380, V382; the files named in the task. SUMO source: `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/sumo-src`, tag v1_27_1 (none under the repo's `toolchain/`). **EXPL** = my numbers from stored S6 rows, cell S, 5,300 veh/h, 240 seeds, plant_c3, already read for a verdict. Runs are the bootstrap unit; 95 % percentile, 10,000 resamples, RNG 20261110. Scripts and outputs: `audit2/drop.py`, `mpos.py`, `*_out.txt`. No simulation ran.

## A. V314: what was tuned, and what it did

- **Tuned:** lane changing, road, human drivers. **Unchanged:** fleet shares, demand, ALKS tau 1.6 s. **Score:** flow, TTT, fuel, TTC and braking at 4,600 and 5,300, "only no-control runs scored, so no controller result shapes the plant" (V314). 4,154 sweep runs, then 80 check runs (V322, V324, V327, V329).
- The score "picked poor winners" and had "no ramp term" (V322); the author then chose from a table (V323, V328).
- **Frozen:** only `lcAssertive` 1.4 and the smooth no-undertaking rule (`baseline_v1/plant_p0.json`). No human-driver parameter changed.
- **Before to after at 5,300** (V329): flow 1,957 to 2,097.5; delay 146.4 to 126.9 s; ramp delay 229.8 to 79.9 s. Lane-end stops 1,969 to 86 (V327).
- **P0 held an artefact** (ALKS braking at 9 m/s², V367). Without it: delay 120.2 to 127.5 s, lane-end stops 30.5 to 361 (V371). P0d against the earlier plant: delay +8.6 % [+4.0, +13.1] (V375). P0d's settings were "chosen after seeing C7 ... on used seeds" (V374).
- **Capacity drop** (V271's estimator, no null): earlier plant 5.1 / 1.7 / 4.2 % at 4,600 / 5,300 / 6,000; chosen plant 11.7 % (3 runs) and 10.8 % (11 runs) at 5,300 and 6,000 (V322, V327). "Minimal" was the intent; no reading shows it was met.
- **Waves:** only a 25 km/h slowdown makes one; truck, burst and outage form none (V342).

Effect on headroom:
1. The tuning took about 9-11 % of no-control delay and two thirds of ramp delay out of the plant. That was merge friction, which state feedback works on. **Less headroom for searched rules and DRL alike.** This was the intent (V315).
2. The 1.6-s default stayed. What is left is static: p333 against no control +29.6 / +19.9 / +12.8 % delay in S / X1 / X2 (V382), "a property of the headway, not of DRL" (V419). A rule with no parameters takes all of it. **Direction: toward the fixed rule, against searched rules and DRL together.**
3. The plant was scored at 1.6 s only. Under p333 merge 2 is not smooth: lane-end stops median 391.5, p90 2,032 in S (critic_M.md F2); 2,518 in X1 against 728 for no control (an_x1x2_delay_edge.md:72). "No control is best" describes the 1.6-s fleet, not the plant the controllers run on. Direction unknown.
4. `tau_rise` is a further choice: on 2 development seeds it cost p333 about 10-13 % delay under slowdowns, "as the plant's hard braking had also opened gaps" (V380). Slowdown records before plant_c3 leaned **toward p333**.

## B. V256, "closed for SUMO"

Argument and evidence:
1. BN4, 0.5-s step, 54 configurations: zipper + Krauss 7.0 %, Flow-IDM 50-54 % (V139).
2. Work-zone 3→2: 54 configurations twice, then 216; none passes, "within the pre-registered knobs" (V142-V145).
3. bn4x, human-only, 0.1 s: the zipper caps throughput near 1,350 veh/h at fine steps (V180). BN4's 5-8 % drop is "probably set by SUMO's zipper junction model ... not proven" (V181).
4. Lane-end corridors: ld32 passes at 7.4 % after a detector change made after data (V186, V187); ld43 shows no drop. INFERENCE: if that 7.4 % used V139's max-based rule (V255(4)), V244 makes it no evidence. I did not open `calibrate.measure`.
5. v199: the max-5 statistic reads 10.8-12.65 % with no drop at all; "T1 could not fail" (V244).
6. bn4L stage 0: 5 rows × 2 steps, 190 runs, none meets the criteria (V254). The audit narrows it: "'No real drop' is supported only for lane-end Krauss"; lane-end IDM a = 2.6 "was never loaded past its discharge, so its drop is untested" (V255).
7. V256(2): "A is closed for SUMO by decision".

What the evidence supports:
- A decision to stop track A, resting on "no configuration tried gave a verified realistic drop". Not a statement about SUMO. Not about realism: the calibrated-plant study was refused (V245).
- Every plant in it is a lane drop. I found no drop calibration at an on-ramp merge, the present bottleneck. The developer's on-ramp recipe (`speedDev` 0.05 or less, lower `lcCooperative`, inflow near the limit; capacity_drop_lit_v0.md:41-45) and candidates C3, C4 (:181-209) do not appear in the rows I read. V314 moved the other way.
- V149's "realistic 5-8 % drop" premise was withdrawn: "The KILL stands; the realism premise does not" (V255(4)). `rl_value_synthesis_v0.md`:24-25, :49 still use it, and memo §1.5 quotes :49.
- "No controller has yet been tested on a plant with a verified drop" (V255(5)).

**Does it hold on plant_c3?** EXPL. Flow out of 4a per minute; onset = 2 minutes below 60 km/h, in minutes 5-19.

| | No control | p333 |
|---|---|---|
| Runs with a breakdown | 238 of 240 | 200 of 240 |
| 5 min before against 5 min after, % | −0.5 [−1.7, +0.7], n 101 | −0.5 [−2.1, 0.0], n 121 |
| Same, minus a placebo matched on pre-flow (windows with no slow minute) | 0.0 [−1.2, +1.2] | −1.3 [−1.9, −0.1] |
| Placebo alone | −1.9 [−3.9, −1.0], 12 runs | +0.8 [−0.4, +1.6], 139 runs |
| Pack statistic, best 5 min before (measure.py:490) | −1.1 [−2.6, −0.8] | +2.8 [+1.7, +3.7] |
| Pack statistic on runs with no breakdown | 2 runs only | +3.2 [+1.9, +5.0], 40 runs |

- No flow loss after breakdown is shown. Flow in slow minutes is 5,329 veh/h against 5,251 in free minutes (p333).
- The measurement pack's own drop statistic reads about 3 % where nothing broke down: V244's defect.
- Limit: pre-onset flow is demand-limited (medians 5,088 and 5,280; saturated 5,342 and 5,544 at 7,000 on 6 seeds, an_delay_floor.md:43). A drop against a true maximum is not excluded, as in V271. Missing: unperturbed no-control runs with demand ramped past capacity; the stored ladders carry random slowdowns on most seeds.
- PR-26 stays a gap. "Minimal" and "11.7 %" are both unsupported.

## C. A plant with a verified drop

- "Without a drop, a meter mostly moves delay"; the gain "scales roughly with the drop (my inference ...)" (nonlinear_flow_mechanisms_v0.md:104-105). Field drops 2-11 % [FT]; merges 8-10 % (:77, :190).
- **Fixed 0.8 s:** it cannot hold flow below breakdown. Under p333 road 4a is slow in 32 % of minutes (EXPL). With a drop those minutes would also lose flow, so headroom above p333 would exist. Today it does not.
- **Searched state-feedback rules:** first in line. Lengthening, now a pure cost (critic_M.md F3), could pay.
- **Per-CAV DRL:** the same headroom through the same lever. The local synthesis found no case of RL beating tuned classical control at a bottleneck (rl_value_synthesis_v0.md:20-25; its [ABS] and [SNIP] items are [VERIFY]).
- INFERENCE: headroom ≤ drop size × time in breakdown. A plant built now is post hoc; V245's condition applies (drop fixed before any control result).

## D. The lane-change rule (critic_M F4): confirmed in the source

- The rear gap a lane changer needs is the **follower's** `getSecureGap` divided by `lcAssertive` (MSLaneChanger.cpp:864-865, :879; MSLCM_LC2013.cpp:2056-2057).
- For IDM that is speed × tau plus a speed-difference term (MSCFModel_IDM.cpp:218-221). `setTau` writes that tau (MSVehicleType.cpp:634-640; b_env.py:784). The front gap uses the merger's own tau the same way (MSLaneChanger.cpp:909-910, :924).
- So a commanded 0.8 s halves, against 1.6 s, the gap an ALKS demands behind a merger. A real merging driver does not know the follower's setting.
- EXPL, S, share of merge-2 lane changes made in the last 60 m: p333 11.8 %; 1.0 s on 4a +2.8 points [+1.8, +4.2]; 1.2 s on 4a +4.1 [+2.6, +5.9]; no control +8.2 [+6.7, +9.5]. Longer headway, later merges. Consistent with the rule, not a test of it: longer headways also slow 4a.
- **p333's lead at the merges, and "every lengthening costs delay" behind H1, could partly be this rule. Direction: toward the fixed rule.** Size unknown.
- Against a simple reading: in X1 p333 has the most lane-end stops (2,518; v3w 1,278; no control 728). Short platoons also block mergers.

## E. Table

The record is a draft, "not yet reviewed or approved"; 6 met, 13 partial, 7 gap, 2 limit (plant_vv_record_v0.md:3, :17).

| Choice or gap | Effect on headroom; mechanism | Direction of bias | What settles it; cost |
|---|---|---|---|
| V314 tuning (`lcAssertive` 1.4, smooth rule) | Removes merge friction: 9-11 % of no-control delay | Toward the fixed rule; searched rules and DRL lose alike | p333 and one searched rule at `lcAssertive` 1.0; rules-only runs |
| 1.6 s as no control | Leaves a static 13-30 % gain | Toward the fixed rule | Report against p333; zero-run |
| Plant never scored at 0.8 s | Merge-2 stops return under p333 | Unknown | Rules-only runs |
| PR-26 capacity drop (gap) | Breakdown costs speed, not flow | Toward the fixed rule; every state-feedback controller alike | No-control demand ramp, like-for-like statistic with placebo; no-controller runs |
| V256 scope | Lane drops only; on-ramp untried | Same as PR-26 | New plant and record; a build |
| PR-28 merge-2 lane ends (gap) | The X1 edge over p333 sits here; SUMO drivers "slow down near its end" (nonlinear_flow_mechanisms_v0.md:184, [VERIFY]) | Toward DRL and lengthening rules, in X1 and X2 | Lane-end trace, longer-lane variant; rules-only runs |
| LC2013 gap rule tied to tau (PR-08) | Short tau admits mergers by construction | Toward the fixed rule | Lane-change trace (gap, follower tau), rules-only; patched SUMO is a build |
| PR-08 `lcAssertive`, instant lane changes (limit) | No lane-change voids, less friction | Every controller alike | PR-27; a build |
| PR-06 ALKS is IDM; read-back test not located | 0.8 s carries no stability cost; "IDM realism at these headways is unchecked" (V274) | Toward the fixed rule (INFERENCE) | Unit test, zero-run; a lagged model is a build |
| PR-10 bind check | V382 has an r2m3 T0 ("commanded level reached 100 %") the record does not cite; held gap not shown | Every controller alike | Citation, zero-run; bench |
| PR-09 smooth rule (own model) | "rerun for each new plant"; S6's new arms not in the record | Unknown | Step check on stored rows; zero-run |
| PR-07 UN R157 (gap) | If 0.8 s is not admissible, the floor and the reference move | Unknown | Desk analysis [VERIFY]; zero-run |
| PR-16 ideal V2V (limit), PR-15 inputs (gap) | Rules read 400-1,000 m ahead, tuned with the condition known (memo M5) | Toward searched rules | Inspection, zero-run; noise model is a build |
| PR-23 1-Hz TTC, PR-24 counters (gap) | Close-following only; `end_stop2` itself never traced | Unknown on delay | One trace per counter; rules-only |
| PR-27 field comparison (gap) | Lane shares and speeds unvalidated | Unknown | Stored lane table against MnDOT; zero-run |
| PR-02, PR-03, PR-21 | Main insertion queue 4,404 veh-s in every arm; every class held to 100 km/h (an_delay_floor.md:19, :65) | Every controller alike (dilutes percentages) | Unit tests; zero-run |
| PR-01, 04, 05, 11, 13, 17, 20, 25 (partial) | No mechanism found | None found | Inspections; zero-run |

**Not done.** The plant version of each record behind H1 (item 1). Whether the stored rows hold the 0.1-s braking keys PR-09's re-check needs.
