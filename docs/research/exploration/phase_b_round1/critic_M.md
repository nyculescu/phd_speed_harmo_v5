# critic_M: attack on direction M and screen M

**Basis.** Code read in `/home/catalin/work/phd/wt/planb_v23` and the SUMO 1.27.1 source clone. "EXPL" = my exploratory numbers from stored rows already read for a verdict: `/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl`, cell S (5,300 veh/h, 240 paired seeds 7,480,400-639, plant_c3), and `/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl` (20 seeds per level). Median of paired differences, 95 % percentile bootstrap, 10,000 resamples, rng 20261110. Positive = the arm has less delay than p333. Scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/work/`. No simulation ran. Veksler was read through a summarising fetch only [VERIFY].

## Findings

**F1 (blocker). The no-merge reference measures route length and upstream load, not merge friction.**
- Not a route change only. Ramp routes have 1 entry lane (corridor.py:55) and `FleetDemand` reduces `v.lane` modulo that in place (fleet.py:347-348). `routes_of` must change, and so must the users of route names: `self.ramp` (b_env.py:398), the per-route length in the delay (plant_sweep.py:325-341), the pending keys (measure.py:310-313). It moves demand between roads, so it is a plant change (planb.md:177).
- `all_delay` is vehicle-seconds minus distance / 100 km/h (plant_sweep.py:347), so it grows with every km driven. EXPL, p333: edge 1, 3 km upstream of any merge, holds 28.1 % [27.4, 28.5] of delay at 7.57 s per veh-km. Rerouted ramp vehicles drive 3.08 km (ramp 1) and 4.57 km (ramp 2) more (b_env.py:59, :74, :1033). INFERENCE: about 2,540 veh-km × 7.57 ≈ 19,200 veh-s, +15 % of p333's median 126,296, before the load on edges 1-2 rises from 3,710 to 5,300 veh/h (corridor.py:55). The merge excess to remove is about 9 % (F2). So the reference is expected at or above p333, and rule 1 would KILL M, P1 and P2 for a reason unrelated to merges.
- Power. "40 seeds detect about 3 %" comes from controller pairs on identical traffic. Under p333 the merge-2 excess runs 3,707 (p10) to 28,673 (p90) veh-s and correlates 0.87 with total delay (EXPL). INFERENCE: paired SD about 7-8 % of the median, so "lower bound above 3 %" needs a point near 6.5 % at 40 seeds.
- **Change:** delete arm 2 and use the route-preserving bound of F2. If a simulated reference is kept, compare only roads 3a to 5 (`m_road_vs`, `m_road_dist`), report the origin queue apart, at least 120 seeds.

**F2 (blocker). A sound bound shows headroom at merge 2 only, carried by the mainline, at the least validated spot.**
- EXPL, S, p333. Merge excess (delay on 3a and 4a above the adjacent upstream road's rate per veh-km, plus ramp insertion queues): 9.2 % [8.4, 11.2] of delay; mean share merge 1 2.1 %, merge 2 9.9 %. TRUCK: 11.1 % [10.5, 11.7]. It is an upper bound for a frictionless merge at unchanged flow.
- Ramps do not bind: ramp insertion queues 56 and 58 veh-s per run (0.0 %), ramp roads 0.6 % and 0.7 %, ramp-2 vehicles 38.3 s against 52.1 s for all. P1's "the ramp queue shrinks" has nothing to shrink.
- The excess sits on 4a (11.3 % of delay; 21.8 s per veh-km against 7.96 on edge 3) and correlates 0.96 with lane-end stops at merge 2 (`end_stop2` median 391.5, p90 2,032; merge 1 34.5). That is the open gap PR-28 (plant_vv_record_v0.md:79; V396: "merge-2 lane-end behaviour was never validated").
- **Change:** rule 1's "expected KILL" is wrong under a sound reference. State that rule 1 reads PR-28's location and supports nothing until PR-28 closes.

**F3 (blocker). The stored rows already hold the dose-response, with the wrong sign.** EXPL, S, against p333:

| Rule | Delay % | Delay on 4a, veh-s | Ramp-2 road + queue, veh-s | Lane-end stops, merge 2 |
|---|---|---|---|---|
| grid_r4a2 (1.0 s on 4a) | −3.75 [−5.57, −2.58] | +3,313 | +4 [+2, +7] | +105.5 [+44.0, +222.5] |
| r4a1 (1.2 s on 4a, V361) | −7.51 [−9.24, −4.74] | +5,668 | +72 [+13, +179] | +77.5 [−6.0, +205.5] |
| z33133 (1.2 s on the 794 m ending 100 m before 4a, b_env.py:1032-1034) | −4.14 [−5.61, −2.59] | +1,617 | +4 [+2, +9] | +45.0 [−6.0, +163.0] |
| grid_z31333 (1.2 s around merge 1) | −2.11 [−3.59, −1.12] | −341 | 0 [−1, +1] | −12.5 [−51.5, +27.5] |
| os0_10_10 (1.6 s when slow and the accelerating lane is crowded) | 0.00 [0.00, 0.00] | 0 | 0 | 0.0 [−26.5, 0.0] |
| no control (1.6 s) | −56.00 [−59.20, −54.73] | +16,095 | +2,548 | +33.5 [−108.5, +151.0] |

Every lengthening adds delay on the merge road and none helps the ramp. Records agree: V368 steady r4a1 57.1 s against 50.6 s; V355 KILL of fixed patterns; V347 1.2 s near a slowdown −4.5 [−5.5, −3.0] %. The screen adds only: lane 0 only, values above 1.6 s, a trigger. Arms 3-4 extrapolate in the losing direction. V274/V276 (m32, uniform tau) and the merge cap (V272: "still learns to slow, flow unchanged"; V304: "its only action lowers speed") are weaker support.

**F4 (major). Mechanism and a SUMO artefact.**
- At fixed flow a longer headway creates no space. EXPL: lane 0 between the merges carries 30.1 % of flow at 73.9 km/h. INFERENCE: about 1,350 veh/h, mean gross headway about 2.7 s, so a 3-4 s target meters lane 0 (V271: "the actuator can only slow"; V344 0 of 8). Short platoons already concentrate the slack: p333 cuts 4a delay by 16,095 veh-s against no control (EXPL).
- LC2013 blocks a change when the rear gap is below the follower's secure gap / lcAssertive (MSLaneChanger.cpp:864-879; MSLCM_LC2013.cpp:2056-2057), and IDM's secure gap is speed × tau (MSCFModel_IDM.cpp:218-221). So a longer tau raises the gap a merger needs in front of that CAV: 15.9 m at 0.8 s, 39.7 m at 2.0 s, 79.4 m at 4.0 s (27.8 m/s, lcAssertive 1.4). INFERENCE, untested: a gap held at tau T admits an equal-speed human merger only from T ≈ 2.5 s, so the 2.0-s arms cannot work by construction; part of p333's own merge gain may come from this rule (a threat to H1).

**F5 (major). Actuator limits.**
- ALKS is IDM, not ACC (fleet.py:265-268 through b_merge.py:45; PR-06). IDM honours any tau; no record above 1.6 s.
- `tau_rise` 0.2 s per 1-Hz update (b_env.py:781-782): 0.8 → 3.0 s takes 11 s ≈ 306 m at 100 km/h, → 4.0 s takes 16 s ≈ 444 m, for the command alone; tracking needs about 5.6 m/s below the leader. In a 300-m zone the 4.0-s arm equals the 3.0-s arm. Rule arms also move one level per 10-s hold (b_env.py:707-711).
- Gate: ALKS leader within 150 m (b_env.py:774-776). 4 s × 27.8 m/s = 111 m, and IDM's equilibrium gap near desired speed is larger. INFERENCE: the gate drops, tau falls to 1.6 s at once, then re-rises (chatter).
- **T0 must show:** read-back equals command; the held time gap at the merge start per zone length; the share of seconds the gate drops; braking at 0.1 s (V367); lane-0 flow and lane changes out of lane 0 in the zone (PR-08; planb.md:183).

**F6 (major). Intended use.** The record covers "1.6, 1.2, 1.0 or 0.8 s" and is "Not for: lateral or merge-conflict safety" (plant_vv_record_v0.md:9, :11); PR-10: "no r2m3 T0 record". L4's "the actuator the plant record already covers" is wrong on range. Every M row is outside the intended use.

**F7 (major). Literature mismatch [VERIFY].** Veksler: default 1.5 s is the floor ("can only increase time-headway"); baseline one fixed headway within 200 m before the merge, swept values not stated; inflow 1,800 veh/h/lane with a 30-50 s merging burst; 500-s runs; metric average speed; mechanism "prevent congestion from forming". Here the floor 0.8 s is the best rule and the plant absorbs bursts (V342; V314). The matching cell would be a burst, excluded (planb.md:317).

**F8 (major). Cells.** S at 5,300: ramps do not bind (F2). EXPL ladder, p333 medians: ramp-2 insertion queue 59.5 (5,250), 77.5 (5,500), 5,760.5 veh-s (6,000; 1.7 % of 341,366); lane-end stops 785.5, 1,219, 2,295.5. X1 puts a 25 km/h slowdown on edge 4, directly below merge 2 (conf3/common.py:14): V347's case, with the heaviest selection history. **Change:** drop X1; use S at 5,300 and 6,000 (inside 4,090-6,000), disclosing 73.8 % finished at 6,000.

**F9 (major). Nothing left for a learner.** If an arm passes, the controller is a rule. A DRL study's opponents are that family, CMA-ES-tuned per cell with input 14, plus p333 (H4); the memo's P1 already says a rule "can" match. v3w would need a new action set and retraining.

**F10 (minor). Cost.** "Half a day" is not credible: `routes_of` and the route-name users, a tau path above 1.6 s in `_v2v` beside the level and hold logic, two new rule classes, T0 for three values on r2m3 (none exists), T3, the bit-identity replay (planb.md:177), rental packaging (V483), a contract departure decision as in V273. My estimate: 2-3 days.

## Verdict

**Drop M as proposed.** Replace it with:
1. A zero-run statement from stored rows (F2 bound, F3 dose-response), re-derived by an independent reader, labelled exploratory.
2. PR-28 (merge-2 lane-end check) before any merge screen.
3. Only then, if the author wants it: one arm family at merge 2, triggered by a slow vehicle in the last 100 m of 4a_0, tau at most 1.6 s, S at 5,300 and 6,000, 120 seeds.

My probabilities (judgement): M as written passes both rules, at most 3 %; rule 1 as written passes, about 20 %, uninformative either way; the changed M shows at least 3 % delay headroom, about 5 %.
