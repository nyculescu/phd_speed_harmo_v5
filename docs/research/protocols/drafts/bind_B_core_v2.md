# B bind check, core gate (v2, V256 amendment)

Status: DRAFT v2, 2026-11-02, revised after one adversarial review with two reviewers (one line per issue in "Review changes" at the end). v1 (`bind_B_core_v1.md`) was approved under V256(3) together with the stage-0 amendment. This file folds that amendment in, tagged [V256a]-[V256f] where each item lands. Next: the author decides N1-N2 (§12) under a V number, then build and smoke (V256(3)). No run happens before that. Reference: `docs/research/protocols/drafts/bind_B_v1.md` (full v1), `docs/research/prior_art_B_v0.md`. Tags: [A#] = Claude's assumption (A1-A15 were approved with D1-D5; A16-A20 are new and wait for N1/N2, §12); [C] = read by Claude on 2026-11-02 in the repo code or in the SUMO 1.27.1 source (git tag v1_27_1); [VERIFY] = not confirmed by a source read in full.

## 1. Question and scope

Can informed cooperative gap creation by mainline CAVs, using speed caps only (no lane-change commands, no ramp signal), reduce merge conflicts compared with no control (NC)? A KILL means "this informed planner and the tuned rule, with speed caps only, found no effect on m32". It says nothing about CAV lane changes (half of V246's B) or about RL with a richer action set (V242 caveat). Out of scope: RL; mechanism attribution (a constant-cap rival and an untargeted placebo, v1 §4.6-4.7, come only after a GO); the lane drop (track A); crashes; weather.
Deviations from CLAUDE.md (recorded with D2, approved in V256):
- the 10 % early-KILL bar applies to E_MA, not to door-to-door delay (V74, V246: delay is a guard);
- a per-share demand-level axis replaces "the realistic demand level" (V245);
- of V74's co-primaries, only TTC exposure gates; smoothness is report-only and hard braking is a guard.

## 2. Plant: m32 (kept from v1)

- m32 = ramp32 without the 3 → 2 drop (edges 4 and 5 keep 3 lanes):
  - the meter TLS `rm` is held green in every arm (the same junction logic as v199 NC);
  - v199 human drivers (`fleet.PLANTS["v199"]`, action steps as V187, held fixed in every check);
  - teleporting off (V197), 0.1-s step, dry, no crash process.
  The 300-m acceleration lane 3a_0 still ends (`merge: laneend`), so the merge is the only bottleneck.
- Human vehicle types [C]: HDV cars use Krauss with no `accel` written (`fleet.HDV_ACCEL` is None under v199; V188's calibrated 2.6 equals SUMO's passenger default). Trucks use Krauss in the trailer class, so SUMO's trailer default applies: accel 1.1 m/s², read in the SUMO source as in §3.
- Build path [C]. `fleet.build_net` sends `geom == corridor.NAME` to `corridor.build(LIMIT)`, which has no lane parameter. `corridor.EDGES` gives edges 4 and 5 two lanes, the 3 → 4 and 4 → 5 connections are `range(2)`, and `corridor.loop_ids()` reads the module `EDGES`. So m32 cannot reuse that branch, and editing the constants would break ramp32.
  - Build: `corridor.build(speed, lanes45)` (2 for ramp32, 3 for m32), with the lane counts in the spec hash, so the net cache key differs; `corridor.loop_ids(geom)`.
  - Every `== corridor.NAME` test (`fleet.build_net`, `loop_ids`, `all_green`, `routes`; `day.run_day` lines 283 and 287) becomes membership in {ramp32, m32}.
  - ramp32's lanes, connections and loop ids must stay as in the current build. The smoke checks both nets (§10).
- Why this plant: on v199 the drop is the active bottleneck on 20/20 days and its queue spills back over the merge (V244). Prior art finds gap-creation benefits from free flow up to near breakdown, not in standing queues (prior_art_B §3.3; Scarinci 2017, full text).
- Demand: constant Poisson demand Q (total), ramp share 15 % (V190, [VERIFY]); 600 s warm-up, a 3,600 s window, then drain (cap 7,200 s after the inflow ends, `day.DRAIN_CAP`). A vehicle belongs to the window by its scheduled departure, so delaying it cannot move it out of the window. The scheduled departure is stored for every vehicle from the route file, arrived or not (§11).
- Areas:
  - MA = the last 100 m of edge 2, all of 3a, the first 300 m of edge 3, and the internal junction lanes between them (`:m_*`, `:ae_*`) [A16];
  - CZ = 1,500 m upstream of the 3a start [A1];
  - merge lanes = road lane 0 (2_0, 3a_1, 3_0) and 3a_0; other lanes = 2_1-2, 3a_2-3, 3_1-2 [VERIFY the ids on the m32 build].
- SUMO 1.27.1 IDM issues (v1 §3): #17483 (IDM lane-change deadlock, fixed only in Git Main), #17502 and #18249 (fixed in 1.28.0) [VERIFY].
  - At 50-80 % ALKS most mergers meet IDM followers at a lane end, which is the #17483 setting.
  - V249 shows lane-end IDM discharge at 1,276-1,319 veh/h with a wide spread.
  - Handled by the C0.1 deadlock gate (§4, first), the ladder's tool-artefact rule (§4) and the standing guards (§9). A share that is UNTESTABLE for a tool artefact can never contribute to a KILL (§9).

## 3. Shared CAV contract (V248(3))

A is closed for SUMO (V256(2)). This block therefore binds B, and binds any later CAV study only through a new decision.

- vType [V256b]: as written by `fleet.VehSpec.vtype_xml` under `fleet.apply_plant("v199")` [C]:
  - vClass passenger;
  - carFollowModel IDM: `PLANTS["v199"]["cav_models"]` overrides the ACC default in `fleet.CAV_MODELS`;
  - tau 1.6 s (`fleet.ALKS_TAU`);
  - LC2013 with lcCooperative 1;
  - speedFactor 1.0, with no draw (`fleet.sample`), written on `<vehicle>`, not on the vType;
  - length and width from the V156 draws.
  `vtype_xml` writes no other car-following attribute, `apply_plant` sets only the human tau and action-step scales, the incident factor and `cav_models`, and the actuator writes only maxSpeed (plus the lane-change lock below). So **the ALKS acceleration is not set by any code; SUMO's default applies.** The values below come from the SUMO 1.27.1 source (`SUMOVTypeParameter.cpp` vClass defaults, the `MSCFModel.cpp` base constructor, `MSCFModel_IDM.cpp`), not from the docs:

| Parameter | Value | Where it comes from |
|---|---|---|
| accel | 2.6 m/s² | `getDefaultAccel`, passenger branch; the base constructor applies it to every model, IDM included |
| decel / emergencyDecel / apparentDecel | 4.5 / 9.0 / 4.5 m/s² | `getDefaultDecel`; `getDefaultEmergencyDecel` with `--default.emergencydecel` "default"; apparentDecel defaults to decel (`fleet.CAV_APPARENT_DECEL` is None). 4.5 is SUMO's passenger default, unsourced for ALKS [VERIFY against R157 if it is cited]; it is also IDM's comfortable deceleration b (`MSCFModel_IDM.cpp:45`) |
| minGap | 2.5 m | vClass default |
| own maxSpeed | 55.56 m/s (200 km/h) | vClass default; the desired speed is 27.78 m/s (speedFactor 1.0 × the 100-km/h limit) |
| IDM delta / stepping | 4 / 0.25 s | `MSCFModel_IDM`; one internal iteration per step at 0.1 and at 0.05 s |
| collision min-gap factor | 0.1 for IDM (1.0 for the Krauss humans) | `MSCFModel_IDM.cpp:47`; `--collision.mingap-factor` is not passed (default −1, `MSFrame.cpp:420`, so `MSLane.cpp:1991` uses the follower model's value). SUMO registers an ALKS collision only within 0.25 m, so intrusions are measured from sampled gaps instead (§5) |

- vType rule [V256b]: the build writes accel 2.6, decel 4.5 and emergencyDecel 9.0 into each ALKS vType, so the route file states them. Behaviour is unchanged by construction; the smoke checks this with a trip hash (§8) equal to the build without them, and reads the values back for every ALKS (§10). Supporting evidence: the stage-0 smoke read back 2.6 for its Krauss vTypes, which have no accel written and go through the same default (`p1c/stage0.smoke_check`; smoke 11/11 in V254) [C].
- Actuator: only `control.command(cap, v, own_max, dt=<run step>)`, with the step passed explicitly (B 0.1 s, or 0.05 s if C0 requires it).
  - V226 exact restore: the own maxSpeed comes back, and allowed speed = min(own maxSpeed, desired).
  - No `changeLane`, `openGap` or `setSpeed`.
  - Per vehicle, B's actuator stores the original laneChangeMode and own maxSpeed once, with a holder count over the roles that hold the vehicle (UGR yielder; OR F, F2 or lane-1 guard, possibly for several slots). It applies the lowest active cap and restores both at the last release.
  - The counters `cap_violations`, `restore_mismatch`, `allowed_mismatch` and `lcmode_restore_mismatch` (against the stored original) must all be 0. They are reimplemented for B, because `control.SumoALKS` ties them to MTFC, edge 3 and `STEP` = 0.1 [C].
- Lane-change mode: used only as a lock, on a capped vehicle and, in OR, on an uncapped lane-1 ALKS near an active slot (§6).
  - The lock is laneChangeMode 1537. `MSVehicle::Influencer::setLaneChangeMode` (`MSVehicle.cpp:806-812`) decodes it as strategic 1, cooperative 0, speed gain 0, keep right 0, TraCI priority 2, sublane 1 [C].
  - It is restored to the stored original mode at the last release.
- Share axis: s ∈ {25, 50, 80} % ALKS of all vehicles; trucks 7.5 %; the rest are human cars.
  - There is no uncommanded ACC/CACC, so "CAV share" has one meaning [A3].
  - Class labels come from a separate RNG stream, so departures and lanes match across shares.
  - A null at 25 % alone is never a KILL.
- B commands only mainline-origin ALKS. Ramp-origin vehicles are never commanded, also after they merge. Levels are calibrated per share (§4), since CAV gaps change capacity (V189).

## 4. Demand levels, deadlock, step, stuck-mode and loading checks (rules fixed now)

All counts used by any rule below are taken by vehicle ID, not from loop interval counts [V256e]:
- a merge is the first change of a ramp-origin vehicle from 3a_0 to 3a_1. It is detected every step from the change in `lane.getLastStepVehicleIDs("3a_0")` and timed at step resolution. Re-entries into 3a_0 by any vehicle are counted, report-only;
- a section crossing is a vehicle's first passage of the section over the union of its lanes, from ID-registering loops read every step (`inductionloop.getLastStepVehicleIDs`): at the 3a_1 end (1 m before the lane end) and at the MA end (edge 3, 300 m);
- 30-s counts bin these event times.
Loop counts are report-only (§8).

**Stage C0**, per share: 10 throw-away seeds at 1.10 × B0 (if fewer than 9/10 NC runs at 0.1 s break down, also at 1.25 × B0), with three runs each: NC at 0.1 s, NC at 0.05 s, and NCμ at 0.1 s. The C0 NC runs at the step B then uses are the ladder's 1.10 and 1.25 levels (same seeds, §7). All C0 runs finish before the C0 outcome is read.

- **C0.1 Deadlock gate, first [V256a].** A deadlock event (teleporting off) is an interval longer than X = 120 s [A16] during which both hold:
  1. the same vehicle (by ID) is inside MA and at or below 0.1 m/s throughout;
  2. no vehicle crosses the end of 3a_1 (road lane 0 at x = 3,800 m). A lane change out of 3a_1 is not a crossing.
- Implementation [C]:
  - W(t) = the largest `vehicle.getWaitingTime` over vehicles in MA. SUMO adds a step while the speed is ≤ 0.1 m/s and the vehicle is not accelerating, and resets it when the vehicle moves (`MSVehicle::updateWaitingTime`, `MSVehicle.cpp:4280-4286`); it does not count during a SUMO stop.
  - C(t) = the time since the last 3a_1-end crossing (per-step ID loop).
  - Read at every whole second; an event is active while min(W, C) > X.
  - Stored per event: start (t − min(W, C) at the first active second), end, the ID of the vehicle with the largest W at the start, its lane and position.
  - A run stops once min(W, C) reaches 600 s, with status 'deadlocked' (§9 treats it like any deadlocked run) [A16].
- Where condition 2 is measured [A16]: every merger leaves through the end of 3a_1. A blockage at the lane end stops that crossing, while lanes 1-2 can keep leaving MA, and so can lane 0 further on, refilled by keep-right changes. An all-lane MA-exit test would therefore miss it; that test fits bn4L, whose last merge has one lane. The all-lane form is reported but does not gate.
- Why X = 120 s [A16]: it equals v1's standing-pair limit, and it sits below the longest ramp waits on drained teleport-off v190 days (311-662 s, V198). Whether lane 0 kept moving during those waits was not recorded, so "no event there" is an assumption. Reported per run: the longest W and the longest C.
- Undrained alone is not a deadlock. An undrained run without an event is overload or a slow drain, and is reported separately.
- C0 runs above the cells it protects (1.10 or 1.25 × B0, against L1/L2 at P(onset) 0.1/0.3), so overload deadlocks can decide C0.1 (a con of N1). Report-only: deadlock events per ladder level and share.
- **Prior: a hypothesis for B, not evidence [V256a].** The hypothesis is that NC at 0.1 s does not deadlock on m32.
  - For it:
    - V189: the v188 lane-end corridor with 50 % CAVs, all on IDM, at 0.1 s: 10/10 days drained, 0 teleports (teleporting on).
    - V197-V198: v190 at 0.1 s with teleporting off and the same mix: 10/10 PM slices and 10/10 full days drained, 0 collisions.
    - v199 adds only the crash passing zone, which is inactive without crashes (V199).
    - Stage 0's lane-end IDM a = 1.0 was undrained at the drain cap on 4/10 seeds at 0.5 s and on 0/10 at 0.25 s. V255 counted these as deadlocks; in the stored runs they are exactly the 4 runs with drained = False (e.g. s7432000: 1,961 of 5,106 trips) [C]. No per-second data were stored, so whether they meet the C0.1 definition is unknown.
  - Against transfer:
    - those mixes had 25 % ALKS plus ACC/CACC at tau 0.6-2.2 s, not 50-80 % ALKS at tau 1.6 s;
    - stage 0's IDM was the Flow vType (accel 1.0 or 2.6, decel 1.5, tau 1.0, minGap 2.0; `p1c/plant.py`) [C];
    - its a = 2.6 row was never loaded (V255), so it says nothing about deadlocks at the ALKS acceleration;
    - standing was not the same as undrained there either: the lane-end IDM a = 1.0 row had 5/10 and 4/10 seeds free of > 300-s standing at 0.5 and 0.25 s (V254), against undrained runs on 4/10 and 0/10.
- **C0.2 Lattice criteria** (v1, [A2]), on ID counts [V256e]. Queued = the 30-s intervals inside a `breakdowns_merge` episode, from onset + 5 min to recovery (the QDF span) [A17]. A run is evaluable with ≥ 10 queued intervals and no deadlock event. Per evaluable run:
  - the 30-s MA-end crossing counts on 3_0 take ≥ 4 distinct values, with no value in > 50 % of intervals;
  - the 30-s merge counts meet the same test;
  - no single inter-merge time holds > 20 % of merges, with merge times from the per-step detector binned at 0.1 s at both steps (so 0.05-s runs are not judged on a finer lattice).
  - C0.2 passes at a step if ≥ 8 runs are evaluable over the C0 levels run, ≥ 80 % of them pass, and the across-seed CV of per-run QDF is ≥ 0.5 % (A's criterion 1, which caught the near-deterministic zipper discharge, V255) [A17]. Fewer than 8 evaluable runs is a fail.
- **C0.3 Step criterion** (v1, [A2]): |paired median QDF ratio (0.05/0.1) − 1| ≤ max(2 %, the p95 of |QDF ratio NCμ/NC − 1| by bootstrap). QDF = the mean 30-s MA-end crossing flow by ID (all lanes) from onset + 5 min to recovery, over seeds where both runs of the pair have a merge onset and neither has a deadlock event; fewer than 8 such pairs is a fail [A17].
- **C0 outcome, fixed now [A17].** Per share s and step h: D(s, h) = NC at h has a deadlock event on ≤ 1 of 10 seeds at every C0 level run; Lat(s, h) = C0.2 passes at h; St(s) = C0.3 passes.

| Per share s | Share state |
|---|---|
| D(s, 0.1) and D(s, 0.05) both fail | tool-UNTESTABLE(s, "deadlock"); no ladder run at s |
| otherwise | "ok at 0.1 s" if D(s, 0.1), Lat(s, 0.1) and St(s) hold; "ok at 0.05 s" if D(s, 0.05) and Lat(s, 0.05) hold (both, one or neither) |

| Over the shares not UNTESTABLE (checked top to bottom) | B runs |
|---|---|
| none left | no ladder; the verdict is INCONCLUSIVE (§9) |
| every one ok at 0.1 s | every stage at 0.1 s |
| every one ok at 0.05 s | every stage of every share at 0.05 s, re-costed, author told; C0.3 is reported but not gated (no step below 0.05 s is tested; disclosed) |
| otherwise | **B-UNTESTABLE(m32, step)**: a defined, reported result, not a KILL; any continuation needs a new V decision |

- Deadlocked runs are left out of C0.2-C0.3 and reported. NCμ events are reported.

**Ladder:**
- Base B0 = 3 × 1,602 veh/h, the V189 full-mix pre-queue flow per lane, used as the ladder centre only [A4].
- Ladder: Q = {0.60, 0.65, …, 1.10} × B0, 10 throw-away seeds per level and share, NC only, at the C0 step.
- Outcome per run: ≥ 1 in-window merge breakdown onset (`day.breakdowns` on `merge_up`, series field 5: speed < 0.5 × LIMIT on 4 consecutive 30-s readings).
- **V170 check [V256f] [C].**
  - `day.run_day` takes loop speeds from `smoke.loop_speed`: a vehicle-weighted mean over the loops that had traffic, `None` when no vehicle passed. An empty lane has weight 0, so the V170 bug (an empty lane read as speed 0) is not in this path. `control.LoopBank.read` computes the same mean.
  - `p1c/episode._mean` still has the bug (−1 is mapped to 0, then a plain mean is taken). B does not use it.
  - Residual: `day.breakdowns` reads an interval with no passing vehicle as free (NaN → LIMIT). So a full standstill over all three `merge_up` loops for 30 s reads as free, which can split or hide an onset. This needs a standing queue with no vehicle crossing, which the deadlock gate covers. Report-only: per run, the number of in-window `merge_up` intervals with no passing vehicle and occupancy > 0.
  - The vehicle-weighted mean over three lanes can stay above 13.9 m/s while only lane 0 is congested. L1/L2 stay on the approved rule; report-only beside it: a lane-0 onset (`merge_up_2_0` speed, same 4-reading rule).
- **Levels:** from a logistic fit of onset on Q (the stochastic-capacity idea, Brilon et al. [VERIFY]): L1 = Q at P(onset) = 0.1, L2 = Q at P = 0.3 [A5] (off the bimodal P = 0.5 point), rounded to 10 veh/h. If the fit fails (perfect separation, non-monotone), the empirical P is interpolated linearly between adjacent levels.
- **Report-only beside it [V256f]: P(sustained onset)** = the share of runs with an in-window onset whose episode lasts ≥ 15 min (`breakdowns` field `min`; an episode cut off by the run end counts at its observed length), per level and share, with its own Q at 0.1 and 0.3 from the same fit. L1/L2 stay on the approved 4-reading onset.
- **Extension:** P < 0.3 at 1.10 → levels 1.15-1.30; P ≥ 0.1 at 0.60 → levels 0.40-0.55. When C0 used 1.25 × B0, that level exists anyway. Still no 0.3 crossing after the extension → **plant-UNTESTABLE(s) "not critical"**, before any control run.
- **Loading check [V256d] [A19]**, per share, at the highest ladder level run, on runs without a deadlock event (≥ 8 needed, else the check fails). The merge counts as loaded past its discharge if both hold:
  1. the median of (MA-end crossings / scheduled departures), both counted over [2,400, 4,200) s, is ≤ 0.97 and below the smallest per-run ratio at the lowest ladder level run (a free-flow null from the ladder itself);
  2. ≥ 80 % of those runs have a merge onset that is active at 4,200 s or lasts ≥ 15 min within the window, so the queue sits at the merge and not at the insertion edge.
  - Failing at 1.10 → the extension levels 1.15-1.30 run even if P ≥ 0.3 was already reached. Failing at the extension's top → **plant-UNTESTABLE(s) "merge not loaded"**, before any control run.
  - Reported per run: `max_pending` and the p95 insertion delay, so an entry-limited run can be told apart from a merge that is not loaded. At 1.30 × B0 the mainline inflow is about 1,770 veh/h per lane with a fixed departLane and departSpeed max, which may be near single-lane capacity at 80 % IDM (inference).
  - The lesson behind it: stage 0's lane-end IDM a = 2.6 was never loaded past its discharge (peak demand 1,884 / 1,642 against about 2,120-2,200 veh/h; V255), so its drop went untested.
- **Stuck-mode check [V256c] [A18]**, on every NC and NCμ run from C0 onward, over [600, 4,200) s. A stuck episode is any 10 consecutive 30-s intervals (5 min) in which ≥ 5 ramp-origin vehicles stand (< 2 m/s, `merge.V_STOP`) on r, rj or 3a_0 at every interval end, and the merges total ≤ 25 % of the ramp-origin vehicles scheduled to depart in the same 5 min (route file). Overlapping windows form one episode.
  - Why relative: ramp demand on the main ladder is 433-793 veh/h (36-66 per 5 min). A fixed "≤ 3 merges per 30 s" sits at 83 % of the mean arrival at 0.60 × B0 and above it in the low extension, so an ordinary merge queue (normal LC2013 behaviour, V197-V198) would trip it.
  - Reported per share and level: episodes per run, stuck minutes, and the distribution of (5-min merges / scheduled ramp departures) over queued intervals, so the gap between the bulk and the 25 % line is visible.
- **Tool-artefact rule [V256a, V256c] [A17]**, per share, before any control run. The bracket of L1 (and of L2) is the two adjacent ladder levels with Q_lo ≤ L < Q_hi: 20 NC runs, one bracket if L1 and L2 share it. A tool-artefact run has a deadlock event, is undrained at the cap, or has a stuck episode. More than 2 of 20 in either bracket → **tool-UNTESTABLE(s)**, with the three causes counted separately. The tolerance matches A14 (a stage-E cell is out above 2 of 20 dropped pairs).
  - Operating characteristics (Claude's binomial calculation, runs independent). With a per-run artefact rate of 2 / 5 / 10 %, one bracket gives tool-UNTESTABLE with P 0.007 / 0.075 / 0.32, two brackets at most 0.014 / 0.15 / 0.54.
  - For C0.1 (≤ 1 of 10 per level and step): P(a share fails at one level) 0.016 / 0.086 / 0.26, and P(at least one of the 3 shares fails at 0.1 s at one level) 0.048 / 0.24 / 0.60. That share is then not "ok at 0.1 s", which moves B to 0.05 s or ends it.
- Report-only: the merge pre-queue flow (10-min mean before each onset; a new mean-based estimator, since `day.breakdowns` returns the max, V244) and QDF (mean from onset + 5 min to recovery) per lane, from ID counts, against V189's 1,602 / 1,487.

## 5. Primary outcome: merge-lane low-TTC exposure per vehicle (kept)

- Definition: E_MA = vehicle-seconds with same-lane rear TTC < 1.5 s (closing only) while a window-vehicle follower is on a merge lane inside MA, divided by the number of window vehicles.
  - The denominator comes from the route file, so it is the same in every arm of a seed and cannot be moved by caps or locks; in effect the gate tests the numerator. Report-only per arm: the numerator, and the window vehicles that enter a merge lane in MA (the v2 denominator, which UGR's and OR's locks can shift).
  - Sampled every whole second with the `day.py` method (getLeader; TTC = (gap + follower minGap) / closing speed).
  - Lower is better.
  - Lanes 1-2 exposure (E_MA12) and E_CZ are guards with the same denominator, so conflicts moved to other lanes are caught.
- Why this outcome:
  - it is V74's safety measure;
  - it catches compression behind a slowed yielder and cut-ins by gap thieves;
  - a conflict-lane-change test (gap ≥ v·TTC) would nearly repeat OR's own acceptance test (Goodhart);
  - it is continuous, so fewer cells have a zero median;
  - the TTC sampler exists (`day.py`); the lane, position and MA attribution is new code (§11).
- **Intrusions [A20]** (closes O1). SUMO registers an IDM (ALKS) follower's collision only within 0.25 m and a Krauss human's within 2.5 m (§3). UGR's yielders and OR's F are ALKS, so the arms move merge followers onto ALKS and would lower registered intrusions mechanically. An intrusion episode is therefore a run of consecutive sampled seconds in which a follower's bumper gap to its same-lane leader (getLeader distance + follower minGap) is < 2.5 m, for every class. The per-second sample misses intrusions shorter than 1 s, in every arm alike.
- The V211 lateral/junction gap is handled by restriction for the primary (E_MA uses no collision events) and by replay for the guard. Each SUMO collision event is classified by the V209 replay and `day._bumper`:
  - (a) physical contact, or no same-lane distance that the replay cannot clear → that arm's run is a failure (worst-value rule, §9) and the batch pauses for the author to confirm the class; in NC the pair is dropped and counts toward the A14 limit. Contact (bumper gap ≤ 0) is below every class's registration threshold, so class (a) does not depend on the follower's class;
  - (b) a SUMO event that is a minGap intrusion only → report-only;
  - (c) intrusion guard, on sampled intrusion episodes: per cell, X_arm ~ Bin(X_arm + X_NC, 0.5), and one-sided p < 0.05 fails the guard (V213 Q8). NC episodes never drop a pair.
- Report-only:
  - E_MA split into merge-linked seconds (the leader is a ramp vehicle that changed lane within 3 s) and the others;
  - conflict lane changes in MA;
  - stolen, accepted and infeasible slots;
  - onsets;
  - ramp vehicles stuck > 60 s;
  - smoothness (speed SD in MA).

## 6. Arms (4) and instrumentation

- **NC:** SUMO defaults (LC2013, lcCooperative 1), meter green, no commands.
- **NCμ (null, V244):** NC with the same seeds. At t = 600 s, the first ALKS on edge 1 within 1 m/s of its allowed (desired) speed, 27.78 m/s, gets a cap 0.5 km/h below that speed for 1 s [A6].
  - [v2 fix]: v1 said "maxSpeed". The ALKS own maxSpeed is 55.56 m/s (§3), so v1's wording could never trigger.
  - Divergence check (stage C): NCμ and NC MA entry times differ by > 1 s for ≥ 80 % of window vehicles. Otherwise the perturbation repeats every 300 s on the first eligible ALKS. The spread is reported.
- **UGR (tuned rule):** runs every 1 s.
  - For each ramp vehicle j on `r`/`rj`: ETA_j = distance to the 3a start / max(v_j, 5 m/s).
  - A mainline-origin ALKS i on 2_0 or 1_0, 100-1,500 m before the 3a start, not already yielding, with ETA_i = d_i / max(v_i, 5 m/s) and |ETA_i − ETA_j| ≤ W, yields for j (one yielder per j, one j per yielder).
  - Cap c = max(v_i − Δv, 0.5 v_i, 5 m/s) via `command`; no trigger if c ≥ v_i; lane lock as in §3.
  - Release when j is on road lane 0 ahead of i, when i passes the 3a end, or after 30 s.
  - Grid: Δv {5, 10, 15} km/h × W {1, 2, 4} s [A7] = 9 points.
- **OR (perfect-information gap creator):** OR knows every vehicle's state, the route-file schedule and the current LC2013 change wishes. It does not know future LC2013 decisions or driver noise, so it is an informed heuristic, not an upper bound; the wishes are kept out of any later RL observation. Every 1 s, with a 120-s horizon, it handles ramp vehicles in arrival order:
  1. t_j = the time j reaches the 3a start (current speed, accelerating at 1.0 m/s² to its allowed speed [A8]); the merge window is 30-250 m along 3a_0. A j already on 3a_0 gets no new plan; a slot already planned for it follows the release rule in step 6.
  2. Project the road-lane-0 vehicles (1_0, 2_0, 3a_1, scheduled insertions included) at constant speed plus committed caps. A slot is a consecutive pair (L, F) whose gap passes j's window. s_req = len_j + minGap_j + v_F × H_req. A natural slot ≥ s_req is logged, with no command.
  3. Candidates: F is a mainline-origin ALKS more than 30 m before the 3a end. Δs = s_req − the predicted gap. Cap offset δ = aT − √(a²T² − 2aΔs), with a = 1.5 m/s² and T = the time to the merge. A candidate is feasible if δ ≤ 30 km/h and v_F − δ ≥ 0.5 v_F [A9]. An ALKS F2 within 2 s behind F gets the same profile.
  4. Theft filter: reject a slot if a non-commanded vehicle in road lane 1 within ±s_req shows a right-change wish, tested as `getLaneChangeState(v, -1)[0] & LCA_RIGHT` (LCA_RIGHT = 1 << 2, `SUMOXMLDefinitions.h:2186`; the getter reads the saved state and has no side effects, libsumo `Vehicle.cpp:806-810`) [C]; take the next feasible slot.
  5. Pick the least cost Δs × (1 + vehicles within 2 s behind F) [A10]; if none is feasible, log "infeasible".
  6. Execute through `command` each step; lock F and F2 (§3); ALKS in road lane 1 within ±s_req of an active slot get the same lock.
     - Theft re-plan: a vehicle other than j that enters the slot becomes L, Δs is recomputed and the cap extended within the limits; otherwise the slot is released.
     - Release when j is on road lane 0 ahead of F, at t_j + 3 s after the planned merge, when F leaves 3a, or after 30 s, with exact restore of speed and mode (holder count, §3).
  - Tuning: H_req {2.0, 2.5, 3.0} s [A11] = 3 points.
- B is preventive only. Neither arm acts on ramp vehicles already standing at the 3a_0 end, the V193-V197 failure population (usually with a car alongside, V195; waits up to 689 s, V197). The stuck check (§4) and the standing guards (§9) are its only coverage.
- **Shadows and sham (not arms):**
  - In the stage-C NC runs, two shadows run together, with getters only: the OR shadow (OR's planner, logging plans at all 3 H_req values) and the UGR shadow (UGR's trigger, logging (i, j, trigger time) at all 9 points). T0 uses the points tuned later.
  - Sham = OR with no-op commands.
  - The trip hashes (§8) of both must equal NC.

## 7. Stages, seeds, runs

Seeds approved (V256(3)): demand seed = SUMO seed, from the V135 block after V206-V207's 7,431,000-109. In v1's check, 7,431,110-190 was not found in `docs/`, `v5b/`, `tests/`, run file names or any `*.json` under `/home/catalin/work/phd` (grep 2026-11-01; the same grep finds 7,431,0xx). Track A used 7,432,xxx.

| Stage | Seeds | Content | Runs |
|---|---|---|---|
| S smoke | 7,431,110 | per share: NC, NC 0.05 s, NC + shadows, NCμ, sham, UGR, OR; at 50 %: the unset-vType trip-hash run and the two deadlock-detector controls (§10) | 24 |
| C0 deadlock, lattice, step | 7,431,111-120 | per share at 1.10 × B0: NC 0.05 s and NCμ (NC 0.1 s is the ladder's 1.10 level); at 1.25 × B0 when needed, the same (NC 0.1 s is the 1.25 level, run whatever the extension rule says) | 60 (+ ≤ 60 at 1.25) |
| C ladder (throw-away, disclosed) | 7,431,111-120 | 11 levels × 10 seeds × 3 shares, NC; loading, stuck and tool-artefact checks | 330 (+ ≤ 240 extension: up to 4 low and 4 high levels per share) |
| C nulls | 7,431,121-140 | per share × level: NC + shadows 20, NCμ 20 | 240 |
| T tuning | 7,431,141-150 | per share × level: NC 10, UGR 90, OR 30 | 780 |
| E evaluation | 7,431,151-170 | per share × level: NC, NCμ, UGR\*, OR\* × 20; sham 2 seeds × 6 cells; T3 reruns 12 | 504 |
| UNCLEAR extension | 7,431,171-190 | one cell per share: NC, OR\* × 20 | ≤ 120 |

## 8. Tool checks and nulls (fixed now)

- **Trip hash:** SHA-1 of the sorted tripinfo rows (id, depart, departDelay, arrival, departLane, arrivalLane, routeLength, timeLoss) at full precision, plus the collision-event list. Every identity check uses it: sham = NC, shadows = NC, unset vType = explicit vType, the T3 reruns, NCμ ≠ NC. `SumoSim.result_hash` (counts, 10-s arrival bins, TTS rounded to 1e-4 veh-h, collision count; `v5b/d1/sumo_runner.py`) [C] is too coarse for identity and is kept as a secondary.
- **T0a (implementation, every arm):**
  - the §3 counters are 0, every command stays within the taper, and the lock is set and restored;
  - **count identities [V256e]:**
    - in a drained run, MA-end crossings by vehicle ID = trips in the tripinfo = inserted vehicles, and merges = ramp-origin trips (`corridor.build` gives 3a_0 no outgoing connection [C], checked on the net in the smoke, and teleporting is off, so every ramp vehicle leaves it at least once; a merge is the first exit);
    - in an undrained run, crossings + vehicles still upstream of the section = inserted vehicles;
    - loop interval counts at the same sections are report-only, with their difference to the ID counts per run (stage 0's e4 loops overcounted by 2-88, V255).
  - Any failure → STOP, fix, re-run everything affected, and log both outcomes.
- **T0 for OR\*** (stage T, per share) [A12]:
  - T0b: the median of (realised gap − predicted no-command gap) / planned Δs exceeds the OR-shadow bootstrap p95 by ≥ 0.25;
  - T0c: the share of commanded slots that j enters ahead of F exceeds the shadow rate's p95 by ≥ 10 pp.
- **T0 for UGR\*** [A12]:
  - T0b-UGR: the median of (realised gap ahead of i at j's merge − the UGR-shadow gap for the same (i, j)) / Δs_UGR exceeds the UGR-shadow p95 by ≥ 0.25, with Δs_UGR = Δv × hold − Δv²/(2 A_CAP) and hold = the time to release;
  - T0c as above, against the UGR shadow (j enters ahead of i).
- An arm that fails T0b or T0c at a share is "non-binding" there.
- **θ** (V244, like-for-like), per share × level: θ = the p95 of |relative paired median change| of E_MA on NCμ vs NC (20 pairs, 100,000 resamples, the gate's estimator). τ = max(10 %, θ). θ > 30 %, or an NC calibration median E_MA of 0 [A13] → the cell leaves the gate before stage E.
- **Invalid runs in stages C and T** (the §9 rules, applied earlier): a deadlocked or undrained NC or NCμ run drops its pair from θ, and more than 2 of 20 dropped → the cell leaves the gate [A14]. In tuning, a point with a deadlocked, undrained or failed run takes the worst value of that point over its seeds or of all points, whichever is worse; a deadlocked or undrained NC tuning run drops that seed for every point.
- **Guard informativeness:** if NCμ's p97.5 of a guard's relative change exceeds +20 % [A13], that guard blocks GO in that cell.
- **Operating characteristics (V240 lesson), report-only**, after the stage-C nulls and before stage T: a parametric Monte Carlo of the whole §9 rule (Bonferroni gate, the UNCLEAR extension, the verdict table), from the stage-C NC/NCμ paired SDs per cell. Reported: P(GO | global null), P(KILL | one 50 % or 80 % cell at τ + 5 pp), P(INCONCLUSIVE | global null). The numbers go to the author before stage T and change no rule without a new V decision.
- **T3:** the sham trip hash = NC, and reruns of UGR\* and OR\* on 2 seeds reproduce their trip hashes. A mismatch → STOP.

## 9. Decision rules (fixed now)

- **Statistics:** paired seeds; the median of paired differences; relative = median(diff) / median(NC); 95 % percentile bootstrap with 100,000 resamples.
  - The gate family is 2 arms × 2 levels × 3 shares = 12; Bonferroni gives 99.58 % intervals.
  - Guards use unadjusted 95 % intervals.
  - Count guards that are 0 in most runs (deadlock events, standing > 300 s) use an exact one-sided sign test on the seeds where arm and NC differ, since a percentile CI of the median difference collapses to [0, 0] there.
- **Cell effect** (arm X ∈ {UGR\*, OR\*}, share s, level L): T0 passed; E_MA reduction ≥ τ; the 99.58 % CI excludes 0; and all guards hold:
  - **validity:** no class-(a) event, and the intrusion guard passes (§5);
    - an undrained, deadlocked (C0.1 definition, including runs stopped at 600 s) or failed arm run takes the worst value of that arm over the cell's seeds or of all arms, whichever is worse;
    - an undrained or deadlocked NC run drops the pair; more than 2 of 20 dropped → the cell is out [A14];
  - **delay and throughput:**
    - door-to-door delay of all vehicles, including insertion and ramp waits: the CI lower bound of the relative increase ≤ +2 % (V37);
    - door-to-door delay of ramp-origin window vehicles, insertion and ramp waits included: the CI lower bound of the relative increase ≤ +5 % (the A15 margin) [A20]. Ramp vehicles are 15 % of trips, so the all-vehicle guard alone would let ramp delay rise by roughly 13 % (Claude's estimate at equal per-vehicle delays);
    - served throughput (window vehicles out by window end + 900 s): the CI lower bound of the loss ≤ 2 %. It is expected to be non-binding at L1/L2, where every window vehicle leaves in time in every arm (served throughput was nearly degenerate on drained slices, V239(2)). Report-only beside it: MA-end crossings by ID over [2,400, 4,200) s, relative to NC;
  - **displaced conflicts:** E_MA12, E_CZ and hard braking (vehicle-seconds ≥ 3.0 m/s² in CZ ∪ MA): median increase ≤ +5 % and CI lower bound ≤ +5 % [A15];
  - **self-blocking** (v1 A2): a yielder below 2 m/s for > 10 s while its target has not merged, more than 1 per 100 commands → no GO in that cell;
  - **artefact workarounds** [V256a, V256c]: for deadlock events and vehicles standing > 300 s, the one-sided sign test against the arm (the arm higher on the discordant seeds with p < 0.05; this needs ≥ 5 discordant seeds) fails the guard. Stuck episodes: a GO must also hold with every seed removed where either run has a stuck episode (sensitivity fixed now). Fewer events in the arm never block a GO, since giving ramp vehicles gaps is the mechanism under test.
- **Share state**, checked in this order:
  1. **UNTESTABLE(s)**, of one of two kinds, with the reason reported:
     - **tool-UNTESTABLE(s):** C0.1 fails at both steps, or the tool-artefact rule (§4: deadlock, undrained, stuck);
     - **plant-UNTESTABLE(s):** no 0.3 crossing, or the merge is not loaded (§4).
  2. **UNINFORMATIVE(s):** the L2 cell is out (§8) and L1 is not GO.
  3. **GO(s):** any remaining cell meets the cell effect.
  4. **NON-BINDING(s):** both arms fail T0 at s.
  5. **UNCLEAR(s):** the best OR\* cell that passed T0 has a reduction ≥ τ but its CI includes 0. One extension follows (20 fresh seeds, NC and OR\*, that cell only, alone at 99.58 %): pass → GO(s), else NO-EFFECT(s). Disclosed: with up to 3 extensions the family has up to 15 tests, so the Bonferroni bound on the family-wise error is about 15 × 0.42 % ≈ 6.3 %.
  6. Otherwise **NO-EFFECT(s)**.
- B-UNTESTABLE(m32, step) (C0, §4) ends B before the ladder and is reported as such.

| Condition (checked top to bottom) | Verdict |
|---|---|
| any share GO (25 % included) | GO; passing shares reported (80 % only = "high penetration only") |
| no GO; 50 % or 80 % UNINFORMATIVE | INCONCLUSIVE (no KILL) |
| no GO; 50 % or 80 % tool-UNTESTABLE | INCONCLUSIVE: tool artefact at s (cause reported; SUMO #17483 is fixed only after 1.27.1 [VERIFY], so an upgrade is noted as the way to retest) |
| no GO; 50 % and 80 % both plant-UNTESTABLE | INCONCLUSIVE: at high shares the merge is not critical or not loaded (reasons reported) |
| no GO; 50 % and 80 % each NO-EFFECT, NON-BINDING or plant-UNTESTABLE, at least one NO-EFFECT or NON-BINDING | KILL B (speed caps only) on m32 |

- 25 % states other than GO never change the verdict. Stop for the author after any verdict.
- Every NO-EFFECT, KILL or INCONCLUSIVE report states each gated cell's upper CI as the largest effect not excluded (V240(2)), together with the operating characteristics (§8).
- Report-only:
  - G_OR = (OR\* − UGR\*) / NC per cell;
  - TTT (fixed window, unfinished vehicles counted to the window end);
  - mainline and ramp delay;
  - the §4 and §5 report-only rows.
- **Tuning** (stage T, per share × level): minimise the median relative change of E_MA vs NC, subject to these point estimates: delay ≤ +2 %, no class-(a) event, E_CZ and E_MA12 not above NC.
  - Ties within 1 pp go to the smaller Δv or H_req.
  - If no point passes, the NC-closest point is used (smallest |Δ delay|), disclosed.

## 10. Smoke (V231), before every batch

One short run per distinct arm, grid family, step and share (§7 row S). The launch script stops on any failure.
Checks (v1):
- each output echoes arm, parameters, share, Q, seed, plant id and step;
- inserted vehicles = route-file departures;
- realised class shares and route counts fall inside the Poisson 99.9 % interval;
- the command log is non-empty for UGR and OR, empty for NC and sham, and has one entry for NCμ;
- sham and shadow trip hashes = NC, and the NCμ trip hash ≠ NC;
- grid points give distinct command sets;
- laneChangeMode reads back as 1537 while locked and as the stored original after the last release;
- the §3 counters are 0;
- the run drained, with no class-(a) event;
- `wall_s` is recorded.
Added in v2:
- **ALKS read-back [V256b]:** accel 2.6, decel 4.5, emergencyDecel 9.0, minGap 2.5 and tau 1.6 through the `ls.vehicletype` getters on each ALKS's own type `t.<vid>` (the p1c probe already uses `getAccel`, `getDecel`, `getMinGap` [C]); speedFactor 1.0 through `ls.vehicle.getSpeedFactor`, as `smoke._readback` does, because it is written on `<vehicle>` [C]. One NC run at 50 % built without the explicit attributes must give the same trip hash.
- **Nets and code paths:** on m32, edges 4 and 5 have 3 lanes; 3 → 4 and 4 → 5 connect on all 3 lanes; 3a_0 is the only lane with no successor; the `add.xml` loop count equals `loop_ids("m32")`; TLS `rm` reads all 'G' after `all_green`; the `RampMerge` summary and `LoopBank` rows are present. On ramp32, lanes, connections and loop ids match the current build.
- **Counts [V256e]:** the T0a count identities hold. At 0.1 and 0.05 s, every ramp-origin trip has exactly one merge time, and merge times are not confined to whole seconds.
- **Deadlock-detector controls [V256a]**, at 50 %, on the smoke seed:
  1. a vehicle held with `setSpeed(0)` for 200 s within the last 10 m of 3a_1 logs exactly one deadlock event (not with a SUMO stop, during which `getWaitingTime` does not count; `day._block` stops its blocker first);
  2. a ramp vehicle held the same way for 200 s at the end of 3a_0, with lane 0 moving, logs none [A16].
- **Unit tests:** the stuck-mode, loading and tool-artefact statistics and the C0 outcome tables, on synthetic inputs.
Launch: batches launch from a frozen detached worktree, under the CPU guard and the v6-idle check, with ≤ 27 workers and one simulation per process.

## 11. Machine hours and build

- **Runs and machine time:** about 1,938 unconditional runs (+ ≤ 420 conditional: C0 at 1.25, both ladder extensions, UNCLEAR), about 4,800 sim-s each.
  - At 0.04-0.15 wall-s per sim-s (v1 [A1], unmeasured for m32 at 80 % ALKS; 0.05-s runs take about 2×), that is **about 105-390 process-h, or 4-15 h wall at 27 workers**.
  - The smoke `wall_s` replaces this range before stage C0; it includes the new per-step loops, the merge detector and the lane and position logging.
- **Cost risks:**
  - a deadlocked run stops at a 600-s event (§4). Before that, with teleporting off, the road upstream of the merge fills (about 3.5 km × 3 lanes, roughly 1,500 vehicles; Claude's estimate), so the per-second getLeader sweep costs more per sim-s;
  - an undrained run without an event still runs to the drain cap (up to 11,400 sim-s, about 2.4× a normal run, more per sim-s);
  - if C0 moves every stage to 0.05 s, the cost about doubles.
- **Not included:** CPU-rule pauses, and build and test time for:
  - from v1: the share mixes, constant demand, merge-lane exposure, UGR, OR, both shadows, NCμ, sham, the C0 lattice statistics, the mean-based pre-queue estimator, analysis;
  - added in v2: the ID-based section and merge counters with the count identities, the deadlock detector and its two controls, the stuck-mode and loading statistics, the explicit ALKS vType attributes and their read-back, the `merge_up` empty-interval count, P(sustained onset);
  - added in review: the parameterised `corridor.build(speed, lanes45)` and `loop_ids(geom)` with the geometry-set tests (§2); the trip hash; the per-step merge detector and ID-registering loops at the 3a_1 end and the MA end; B's own actuator with the holder count and the four counters; sampled intrusion episodes; the lane-0 onset; the operating-characteristics Monte Carlo.
- **Stored per run** (`day.run_day` stores none of this now; it keeps loop counts, the `r_0` count, the `merge_up` speed, and trip rows for arrived vehicles only):
  - per vehicle: scheduled departure, insertion time, MA entry time, merge time at step resolution, 3a_1-end and MA-end crossing times;
  - per conflict row: follower lane and position (for the MA and merge-lane attribution);
  - per 30 s: merges, standing ramp-origin vehicles on r, rj and 3a_0, scheduled ramp departures;
  - per run: deadlock events (§4), the longest W and C, the stop status, intrusion episodes, `max_pending` and the insertion-delay p95.
  This allows an independent recompute, as in V255.

## 12. Author decisions

D1-D5 were approved under V256(3) and are kept below for reference. The amendment and the review force two new choices, N1 and N2. N2 includes two corrections to approved D2 definitions (the E_MA denominator and the intrusion measurement); they change normalisation and measurement, not what D2 chose.

| # | Decision | Recommended | Pros | Cons | Inferior alternatives (why) |
|---|---|---|---|---|---|
| D1 | Plant, levels, step check | m32 as §2; C0 step check with fixed outcomes; per-share ladder centred on 3 × 1,602; L1/L2 at P(onset) 0.1/0.3; drain rule for #17483 | isolates the merge; checks the V249 lattice per lane before the ladder; avoids the bimodal point | new geometry; 0.05 s may double cost | v199 meter-green PM (the drop queue covers the merge); L2 = Q50 (bimodal, likely uninformative) |
| D2 | Primary outcome and deviations | E_MA on merge lanes (§5); E_MA12, E_CZ, hard braking as guards; the §1 deviations recorded as a V-decision; V211 by restriction plus replay classes | V74 measure without lanes-1-2 dilution; displaced conflicts still guarded; post-event rule fixed | smoothness and hard braking leave the co-primary | all-lane E_MA (dilution biases toward KILL); conflict lane changes (Goodhart with H_req, sparse); fixing the lateral classifier (build work the gate does not need) |
| D3 | CAV contract, shares, verdict | §3 block; ALKS 25/50/80 %, rest human; speed caps only (V248(3) read as excluding lane-change commands); §9 verdict table | one CAV meaning; complete verdict table | B's lane-change half untested | v199 ratios for the remainder (ACC/CACC fall from 25 % to 4.6 %, two meanings of share); a report-only `left` OR variant (more build, no gate weight) |
| D4 | Gap protection | inside OR, CAV-only: lock 1537, lane-1 ALKS lock, theft filter, re-plan, F2 platoon cap | follows prior art without touching humans | HDV thieves cannot be blocked at 25 % | near-side ban for all vehicles (an infrastructure actuator outside the contract); no protection (gaps stolen, an uninformative KILL) |
| D5 | Seeds and budget | 7,431,110-190 as §7; about 105-390 process-h | contiguous, unused, no overlap with A | at n = 20 a 99.58 % CI excludes 0 only when about 16-17 of 20 paired differences share the sign (Claude's sign-test estimate) | UGR tuned on 5 seeds (noisier rival); tuning at L2 only (weak rival at L1) |
| N1 (new) | Deadlock gate and tool artefacts (V256a) | event = > 120 s with the same vehicle in MA (internal lanes included) at ≤ 0.1 m/s and no crossing at the 3a_1 end, from `getWaitingTime` and a per-step ID loop; a run stops at a 600-s event [A16]. The C0 outcome tables (one step for all of B; B-UNTESTABLE(m32, step) as a defined result), C0.2 "queued" and evaluability, the QDF CV test, and the ladder tool-artefact rule (> 2 of 20 per L1/L2 bracket deadlocked, undrained or stuck) [A17]. Tool-UNTESTABLE at 50 % or 80 % gives INCONCLUSIVE, never KILL | catches a lane-0 deadlock that an all-lane MA-exit test misses on a 3-lane road; separates deadlock from overload and from long ramp waits while lane 0 moves; every C0 combination has a defined result; the tolerance matches A14; a SUMO artefact at a high share cannot produce a KILL | the 3a_1-end test is a narrower reading of "no exit from the merge area"; C0 runs above the cells it protects (1.10/1.25 × B0), so overload deadlocks can decide it; a lane-0 standstill > 120 s inside a breakdown also counts; INCONCLUSIVE becomes likelier (tool-UNTESTABLE about 0.15 per share at a 5 % artefact rate, §4); shares that pass only at different steps end B; 0.05 s doubles cost | the literal all-lane MA exit (misses lane-0 deadlocks; reported only); X = 300 s (2-5-min mutual blocks would pass as normal); "any vehicle below 0.1 m/s" (true in most stop-and-go queues); a step per share (shares would no longer compare at one step); tool and plant UNTESTABLE treated alike (a SUMO bug at 80 % could give a KILL); a separate 1-in-10 look per rule and level (P(UNTESTABLE) about 0.5 per share at a 5 % rate, reviewer's estimate) |
| N2 (new) | Stuck, loading and guard repairs (V256c, V256d, review) | stuck: any 5 min with ≥ 5 ramp vehicles standing at every 30-s mark and merges ≤ 25 % of scheduled ramp departures [A18], in the tool-artefact rule and as a stage-E sensitivity. Loading: on deadlock-free runs, median crossings/demand ≤ 0.97 and below the free-flow minimum, ≥ 80 % of runs with the queue at the merge, at the top level [A19]; else the extension, else plant-UNTESTABLE. E_MA, E_MA12 and E_CZ over all window vehicles. Intrusions as sampled bumper gaps < 2.5 m for every class (closes O1). A ramp-delay guard (CI lower bound ≤ +5 %) [A20]. Sign tests for the count guards | an NC reference in an artefact state, or a merge never loaded, cannot produce a GO or a KILL; the stuck line scales with ramp demand; neither the primary nor the intrusion guard can move with which vehicles enter merge lanes or where the arms put ALKS; "safety by starving the ramp" is guarded; the count guards can fail | two approved D2 definitions change (normalisation and measurement only); 25 %, 0.97 and 2.5 m are unmeasured on m32; the per-second sample misses intrusions < 1 s; one more guard makes a GO harder | report-only flags (a verdict could rest on a stuck NC or on transient onsets, the stage-0 lesson); a fixed ≤ 3 merges per 30 s (trips on ordinary queues at low demand); a loading test on the insertion backlog alone (a merge queue that reaches the entry would read as not loaded); `--collision.mingap-factor 1` for all vehicles (more SUMO events, each needing a V209 replay; detection-only under `warn` [VERIFY]); the v2 E_MA denominator (shifted by the arms' locks) |

Assumptions approved with their decision:
- D1: A1 (CZ 1,500 m), A2 (C0 lattice and step thresholds), A4 (B0 as centre), A5 (P 0.1/0.3), and the 15 % ramp share (V190).
- D2: A13 (30 % and +20 % caps), A14 (invalid-NC rule), A15 (guard margin +5 %).
- D3: A3 (share mix), A6 (NCμ perturbation), A7 (UGR grid), A12 (T0 margins).
- D4: A8 (ramp projection), A9 (δ limits), A10 (OR cost), A11 (H_req grid).
- D5: the seed range.
- New and pending:
  - N1: A16 (X = 120 s, the same-vehicle reading, the 3a_1-end crossing point, MA internal lanes, the 600-s stop); A17 (the C0 outcome tables, the 1-in-10 C0.1 tolerance, C0.2 "queued", evaluability, the 8-run minimums and the 0.5 % QDF CV, the 2-of-20 bracket rule).
  - N2: A18 (stuck: 5 min, ≥ 5 standing, 25 % of scheduled ramp departures); A19 (loading: 0.97, the free-flow null, 80 %, ≥ 8 deadlock-free runs); A20 (the 2.5-m intrusion gap; the +5 % ramp-delay margin).

Found while amending:
- **O1** (closed by N2, §5): SUMO's registration threshold depends on the follower's class (IDM 0.25 m, Krauss 2.5 m), so registered intrusions are no longer used for the guard.
- **O2.** The A draft's contract says "v199 speedFactor draws" for the ALKS, but the code fixes ALKS speedFactor at 1.0 (`fleet.sample`) [C]. A is closed; this is noted for any reuse of that text.

v2 changes (V256 amendment):
- (a) the C0.1 deadlock gate comes first, with the per-share UNTESTABLE rule, the hypothesis label and the cited evidence; the drain rule is split into its causes (§4, §9);
- (b) the ALKS parameter table from the source, the explicit vType attributes and their read-back (§3, §10);
- (c) the stuck-mode check, its rule and its stage-E guard (§4, §9);
- (d) the loading check (§4);
- (e) ID counts throughout, with identities in T0a (§4, §8);
- (f) the V170 statement, the empty-interval report and P(sustained onset) (§4).
- Also changed: A's closure noted in §3; seeds marked approved; the m32 code-path check; the NCμ trigger fixed to the allowed speed; cost and build lists updated.

v1 review changes:
- the verdict table with UNTESTABLE/UNINFORMATIVE/INCONCLUSIVE states; the UGR shadow and its T0; fixed collision classes; the CLAUDE.md deviations named; one §3 contract block (IDM per PLANTS v199, a human remainder, lock 1537 with its restore counter);
- the C0 step check moved before the ladder, with per-lane lattice tests, a null-set threshold and fixed outcomes; L1/L2 at P 0.1/0.3 with a fit fallback; the UGR speed floor and the self-blocking guard; the #17483 drain rule;
- E_MA on merge lanes only, with the E_MA12 guard; the speed-caps-only KILL wording; the NCμ divergence check; the worst-value wording; the OR information set; the NC-median-0 rule; the power note; smoke, sham and lock read-back counted; assumptions mapped to D1-D5.

## Review changes

Reviewer 1 (1 blocker, 12 major, 8 minor):
- R1.1 blocker, C0 outcome gaps: fixed; two C0 outcome tables (per share, then one step for all of B), every row ending in 0.1 s, 0.05 s, tool-UNTESTABLE(s) or B-UNTESTABLE(m32, step) (§4).
- R1.2 major, deadlock condition 1 ambiguous: fixed; same vehicle by ID, with the per-event record (§4).
- R1.3 major, stage-0 evidence was "undrained": fixed; relabelled on both lines and checked on the stored runs (4 runs with drained = False) (§4).
- R1.4 major, UNTESTABLE tolerances: fixed; "next to" = the bracketing pair of levels, one pooled tool-artefact rule (> 2 of 20, matching A14), P(UNTESTABLE) stated at 2 / 5 / 10 % (§4).
- R1.5 major, tool artefact could give a KILL: fixed; tool-UNTESTABLE and plant-UNTESTABLE split; tool-UNTESTABLE at 50 % or 80 % gives INCONCLUSIVE (§9).
- R1.6 major, artefact guard could not fail and was two-sided: fixed; one-sided exact sign test for deadlock events and > 300-s standing, a stuck-seed removal sensitivity (§9).
- R1.7 major, E_MA denominator gameable: fixed; all window vehicles, with numerator and the old denominator reported (§5); in N2.
- R1.8 major, ramp harm diluted: fixed; ramp-vehicle delay guard, CI lower bound ≤ +5 % (§9); in N2.
- R1.9 major, stuck threshold not demand-scaled: fixed; merges ≤ 25 % of scheduled ramp departures over 5 min, with the distribution reported (§4).
- R1.10 major, C0.2 "queued" undefined: fixed; queued = QDF span of a merge episode, ≥ 10 intervals per run, ≥ 8 evaluable runs, ≥ 80 % passing, QDF CV ≥ 0.5 %, C0.3 source stated (§4).
- R1.11 major, no operating characteristics: fixed; report-only Monte Carlo after the stage-C nulls (§8), upper CI in every NO-EFFECT/KILL/INCONCLUSIVE report (§9).
- R1.12 major, O1 intrusion bias: fixed; class-independent sampled bumper gap < 2.5 m (§5); in N2.
- R1.13 major, C0.1 gates at higher loads: fixed as asked; placement kept, stated in N1's cons, deadlock events per ladder level reported (§4, §12).
- R1.14 minor, served throughput non-binding: fixed; labelled non-binding at L1/L2, ID-based MA-end crossings reported beside it; not made a gate, to avoid another new choice (§9).
- R1.15 minor, "0.05 s also fails" had no verdict: fixed; B-UNTESTABLE(m32, step) (§4, §9).
- R1.16 minor, loading check on deadlocked runs and no null: fixed; deadlock-free runs only (≥ 8), ratio also below the lowest level's minimum (§4).
- R1.17 minor, statistics not computable from stored data: fixed; per-run storage list (§11).
- R1.18 minor, stages C and T had no invalid-run rule: fixed (§8).
- R1.19 minor, X = 120 s justification was an inference: fixed; marked [A16], longest W and C per run reported, 600-s early stop (§4).
- R1.20 minor, run counts and multiplicity: fixed; counts corrected (C0 + ≤ 60, extension ≤ 240, conditional ≤ 420), family-wise bound about 6.3 % disclosed, T0 required for UNCLEAR (§7, §9, §11). Not changed: the extension level stays 99.58 % (the disclosure was the reviewer's alternative and needs no new choice).
- R1.21 minor, merge identity ignored re-entry: fixed; merge = first exit from 3a_0, re-entries counted report-only (§4, §8).

Reviewer 2 (0 blocker, 6 major, 12 minor):
- R2.1 major, m32 build path contradicts the code: fixed; parameterised builder and `loop_ids(geom)`, geometry-set tests, net smoke checks (§2, §10).
- R2.2 major, result hash too weak: fixed; trip hash for every identity check, `result_hash` secondary (§8).
- R2.3 major, O1 confirmed in source: fixed with option (b), sampled gaps for every class (§5); folded into N2 rather than a third decision; option (a) is listed as an alternative.
- R2.4 major, "while queued" undefined: fixed, as R1.10 (§4).
- R2.5 major, merge-detection resolution: fixed; per-step detector, 0.1-s binning at both steps (§4).
- R2.6 major, deadlock condition 1 ambiguous and unimplemented: fixed; `getWaitingTime` plus a per-step 3a_1-end loop, MA internal lanes included, smoke control 1 uses `setSpeed(0)` (§2, §4, §10).
- R2.7 minor, lane-change [VERIFY] closable: fixed; [C] with the cited lines, theft test as `& LCA_RIGHT` (§3, §6). I checked `MSVehicle.cpp:806-812`, `SUMOXMLDefinitions.h:2186` and libsumo `Vehicle.cpp:806-810` myself.
- R2.8 minor, nested lock roles: fixed; both lock uses listed, holder count, restore at last release (§3).
- R2.9 minor, speedFactor read-back and decel label: fixed (§3, §10).
- R2.10 minor, "the code exists": fixed; reworded, new logging listed (§5, §11).
- R2.11 minor, V198 "lane 0 moving": fixed, as R1.19.
- R2.12 minor, standing ramp vehicles not targeted: fixed; B stated as preventive, OR rule for a j already on 3a_0 (§6).
- R2.13 minor, T0a identity: fixed, as R1.21.
- R2.14 minor, run counts: fixed, as R1.20; the 1.25 NC runs are the extension's 1.25 level.
- R2.15 minor, deadlocked run cost: fixed; 600-s early stop, cost note (§4, §11).
- R2.16 minor, entry-limited top levels: fixed; `max_pending` and the insertion-delay p95 reported with the loading check (§4).
- R2.17 minor, count guards collapse to [0, 0]: fixed, as R1.6 (§9).
- R2.18 minor, merge onset may miss lane-0 congestion: fixed; report-only lane-0 onset, L1/L2 unchanged (§4).
