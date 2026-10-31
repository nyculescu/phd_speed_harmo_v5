# E1 staged headroom check: protocol v1

Status: proposal (2026-10-31), not approved, nothing has run. It implements row E of `docs/research/weather_plant_strategy_v0.md` (V212). The draft came from two independent drafts, a merge, and three adversarial reviews (statistics, controllers, build); Claude then applied the fixes in §14. Tags [Qn] mark text that depends on an author answer in §13; the text shows Claude's recommendation. After the answers, the protocol is logged as the next V# with this file's sha256 and a ledger entry. E1 uses no phase 2-4 weather result.

## 1. Scope and question
- **Question:** on plant v199, in dry weather, at the realistic demand level (§9.1), does any proven controller cut door-to-door delay by ≥ 10 % against no control? The same question is asked of a per-day oracle that may also choose no control.
- **Cells:** R, recurrent days without incidents; I, the same days with one lane-blocking incident at a fixed site [Q3].
- **Candidates:** ramp metering at the ramp32 meter (ALINEA, PI-ALINEA); speed harmonization of the commandable CAVs (ALKS) upstream of the lane drop; the two together; the per-day oracle over all of them.
- **E1 is a screen, not a claim.** Its numbers are in-sample tuning results and are never a thesis claim. A continue only buys E2's compute; E2 re-tests on 30 fresh seeds.
- **What a KILL says** [Q7]: no proven controller, and no per-day choice among them, gains ≥ 15 % in that cell with probability ≥ 0.80. Gains between 10 and 15 % can be missed; the upper end of the CI of rel is reported with every KILL. A KILL means no learning-helper claim on v199 with these actuators, dry, at the realistic demand level; E2 does not run and the author decides the next step.
- **Design rule:** the cheapest set of runs whose KILL holds up. Each simplification either makes a KILL harder or is disclosed with its bias direction (§11.3).
- **Out of scope:** rain and stochastic crashes (E2); other demand levels; VSL for human drivers (V212: level-dependent compliance is not modelled); MPC and learning arms.
- **Expected outcome (Claude's estimate, not a result):** a KILL is more likely than a pass; the uncertainty is wide.
  - Against a pass: the prior (published hybrid gains 1.5-6 %); the p1c metering KILL (V147, V149); under the V190 limits the meter can hold only about 22 vehicles (§3.2); only ALKS (25 % of vehicles) take commands; the median capacity drop here (about 11 %) is about half of the 22 % in Chaves et al. 2018, where MTFC gained much more.
  - For a pass: on the V198 days the lane drop broke down at a pre-queue flow of 3,336-3,660 veh/h (median about 3,460) and discharged at 2,984-3,099 veh/h (median about 3,050), Claude's reading of `docs/research/results/fleet_v190_tpoff_v0.json`. PM-peak demand is 45,000 × 7.75 % ≈ 3,487 veh/h, near the breakdown flow and about 14 % above QDF. Holding the inflow just below the breakdown flow is the textbook case for MTFC and PI-ALINEA (Jin & Jin 2013: speed control helps only when a capacity drop exists).

## 2. Plant and fixed settings
| Item | Value | Source |
|---|---|---|
| Plant | `PLANTS["v199"]`: v190 (ramp32, teleporting off) plus the passing zone f = 3.0 | V197, V200, V201 |
| Geometry | entry edges 1 (3,000 m) and 2 (498.3 m), 3 lanes; 1-lane ramp `r` 391.7 m (storage about 50 vehicles), meter at node `rm`, then `rj` 28.3 m; edge `3a` with the 294.7 m acceleration lane `3a_0` (no successor); edge 3, 1,192 m, 3 lanes, lane `3_2` ends at its end; edge 4, 996 m, 2 lanes; exit edge 5, 500 m | `v5b/fleet/corridor.py`, net cache `ramp32_3aa2e9555e` |
| Speed limit | 100 km/h on every edge, the ramp included | corridor.py |
| Fleet | HDV car 42.5 %, truck 7.5 %, ACC 12.5 %, CACC 12.5 %, ALKS 25 %; v188 human drivers; CAVs on IDM with sourced gaps; only ALKS take commands | V161, V173 |
| Demand | ADT 45,000 veh/day, `day.UK_WEEKDAY` shares, ramp share 15 % [VERIFY] | V189, V190 |
| Weather | dry; `weather()` is not called | V212 |
| Simulation | SUMO/libsumo 1.27.1, step 0.1 s, one simulation per process, `nice 10` | day.py |
| Day | demand 00:00-24:00, then drain until empty (`DRAIN_CAP` 7,200 s) | day.py |
| Crashes | none in R; in I only the blocker of §5.2 (crash process with k = 0); k = 0.001085 is used only offline, for expected crashes (§7.5) | V198, V202 |
| Collisions | physical contacts and minGap intrusions counted apart | V211 |

**Plant state under no control** (V198, seeds 7,430,040-049; identical on v199 per V201; Claude's reading of `fleet_v190_tpoff_v0.json`):
- lane drop: the main PM episode starts 15:30-16:32 and lasts 128-221 min; median flow drop about 11 % (8-17 %);
- merge: the first PM breakdown comes at 16:07-16:51, always after the drop's onset, so the merge queue is mostly the drop's spillback (Claude's inference);
- ramp: maximum queue 51-56 vehicles with the meter green.
- Headroom follows the size of the capacity drop (p1c lesson, V139/V155), so the drop and QDF at the lane drop are reported next to every result.

**Meter signal:** TLS `rm`, one link (state string of length 1). `corridor.METER = "meter"` is wrong and is not used. Under no control the meter is all green, as in V198.

**New loops** (30-s period, all lanes, measurement only; they change the net-cache hash, not the dynamics, which the regression in §10.3 checks):
- `alinea_3_{0-2}`: edge 3 at 100 m, 100 m past the end of edge `3a` (the Amsterdam distance in Papageorgiou et al. 1991);
- `drop_3_{0-2}`: edge 3 at 1,042 m, 150 m before lane `3_2` ends (primary drop loop);
- `dropend_3_{0-2}`: edge 3 at 1,172 m, 20 m before the lane end (fallback, chosen only by §10.3).
- Existing loops stay: `up_3`, `merge_up_2`, `e4_4`, `exit_5`, `ramp_q_r_0`, `ramp_out_r_0`.
- **Logged per 30 s for every loop group:** flow, occupancy and speed. Today's series has none of these per loop.

**Controller hook:**
- Meter and control laws run in the whole-second block of `run_day`, after the plant's own per-second steps (ramp merge, passing zone) and before the TTC scan. The ALKS caps are applied every 0.1-s step (§3.3).
- Laws update at t = 60·n s. A 60-s sensor value is the mean of the last two complete 30-s `getLastInterval*` readings over the loop group's lanes.
- Controllers are active from 00:00 until the network is empty, the drain included (V132 WP1).
- **They see:** the loops; the meter state; ALKS positions and speeds (V2I); vehicle counts and waits on `r_0` (simulation counts, disclosed as ideal sensing). Never the crash process, the seed or the future.

**Output:**
- one frozen commit, run from a detached worktree, as a systemd user unit;
- raw runs under `/home/catalin/work/phd/v5b1_runs/e1/<cell>/<arm>/<point>/ss<sumo_seed>/`, so twins never collide with main runs (today `day_s{seed}.json`, `conflicts_s{seed}.npz`, `sumo_s{seed}.log` and `rd_s{seed}` carry neither arm nor SUMO seed, and `crash.py` globs `conflicts_s*.npz`);
- every file name also carries the PID; the summary goes to `docs/research/results/fleet_e1_v0.json` (< 5 MB).

## 3. Arms

### 3.1 No control (NC)
The meter stays green all day and no CAV gets a command: the V198 run path.

### 3.2 Meter family M at TLS `rm` [Q2]
**Rate law** (every 60 s; r in veh/h, occupancy o in %):
- **M-A, ALINEA at `alinea_3`:** r_law(k) = r_s(k−1) + K_R [ô − o_m(k)]. Nominal K_R = 70 veh/h per % (Papageorgiou, Hadj-Salem & Blosseville 1991, which reports results "insensitive for a wide range of K_R"); sample interval 60 s [VERIFY that the paper's K_R was used at 60 s].
- **M-P, PI-ALINEA at the drop loop:** r_law(k) = r_s(k−1) − K_P′ [o_d(k) − o_d(k−1)] + K_I′ [ô − o_d(k)] (Wang et al. 2014, in the form written by Stylianopoulou et al. 2018), capped at r_meas(k−1) + 400 veh/h ("an empirical value", Wang 2014 as cited there).
  - Gains in density units: Wang-attributed set K_P = 100, K_I = 4 km·lane/h [VERIFY, secondary source only]; conservative set K_P = 60, K_I = 1 (Stylianopoulou 2018).
  - Conversion ρ = 10·o / L̄ per lane, averaged over the 3 lanes of the drop loop. L̄ is the mean vehicle length of the generated fleet, measured on the draw of seed 7,430,040 and frozen (about 5.2 m by Claude's arithmetic from `CAR_SEGMENTS` and `TRUCK_LEN`). SUMO loops are taken as points [VERIFY in 1.27.1].
- **State r_s(k−1)** (anti-windup; Papageorgiou 1991: r(k−1) is the volume actually admitted): the commanded rate if the last period was metering (at least one red phase) and had no downstream-limited second; otherwise the realised rate (releases in the last 60 s × 60), clipped to [240, 900].
- **Start:** r(0) = 900, resting green, so every law starts as NC.

**Queue law and bounds (V190 limits)**, in this order:
1. **Queue law:** r = max(r_law, 24·N_q), with N_q the vehicles on `r_0` at the update. 24·N_q veh/h serves the present queue in 150 s, 60 s inside the 210-s backstop below. At the PM ramp demand of about 523 veh/h it settles near 22 vehicles. It is a rate form of the queue-control law r = max(r_ALINEA, r_queue) (Smaragdis & Papageorgiou 2003 [VERIFY]).
2. **Bounds:** r = clip(r, 240, 900).
3. **Rest green** (meter off) if r = 900, or if r ≥ 1.05 × the ramp arrival rate (5-min mean at `ramp_q_r_0`) with at most 2 vehicles on `r_0`. So the upper bound equals NC, and a standing queue is never flushed by a switch to green. Metering resumes when r < 0.95 × the arrival rate.
4. **Queue override (checked every 30 s):** if `ramp_q_r_0` reads occupancy ≥ 30 % over the last interval, rest green until it reads below 15 %. A free ramp reads about 3 % (520 veh/h × 5 m / 25 m/s). Thresholds are Claude's choice.
5. **Wait backstop (checked every second):** a vehicle's wait is its time on `r_0` minus the free traverse time 14.1 s. If the longest wait reaches 210 s, the commanded rate becomes 900 (the actuator's maximum; the signal keeps metering, no flush) until the longest wait falls below 150 s. The 30-s margin to the V190 4-min limit and the hysteresis are Claude's choice. The wait is measured at the meter; NC already exceeds 4 min at the end of the acceleration lane (V198).

**Actuator** (release tracking of `v5b/p1c/meter.py`, adapted to one lane and to a 100 km/h approach):
- While metering, the target cumulative release grows by r/3,600 per second; owed = target − releases, capped at 2. A release is a vehicle that leaves `r` for `rj` (per-second ID-set diff).
- **Rest in red** while metering. A green of 2 s starts when at least one vehicle is owed and a vehicle stands within 15 m of the stop line below 3 m/s. It extends up to 4 s while another vehicle is owed and within 15 m. Then a 1-s amber (only slow vehicles are near the line), then red.
- **Metering onset** (rest green → red): a 5-s kinematic amber, as in p1c (`AMBER = 5.0`).
- **Downstream-limited second:** a release is owed, the signal is green, and the head vehicle has not left within 2 s because `rj` or the last 50 m of `3a_0` holds a vehicle below 2 m/s. These seconds are counted and excluded from the actuator checks.
- The timing values are Claude's choice [VERIFY against the FHWA Ramp Management and Control Handbook]; T0 (§10.3) is their acceptance test, and a change made to pass T0 is logged.

**Logged:** commanded, applied and realised rate per 60 s; seconds in each override, backstop and downstream-limited state; red phases; per-vehicle wait on `r_0`; per-vehicle red exposure; red passages.

### 3.3 CAV family C: mainstream traffic flow control through the ALKS [Q1]
**Law** (every 60 s): b(k) = clip(b(k−1) + clip(K_I [ô − o_d(k)], −0.2, +0.2), 0.3, 1.0), b(0) = 1.
- Basis: the I-type MTFC of Carlson, Papamichail & Papageorgiou 2011 [VERIFY, abstract only], in the form Chaves et al. 2018 used with ACC actuators (60-s period, at most 20 km/h change per period).
- Sensor: the drop loop, as for M-P (unless §10.4 moves C to `dropend_3`).
- K_I: chosen in §10.4 from {0.005, 0.01, 0.02, 0.04, 0.08, 0.16} per percentage point (nominal 0.02). The range is wide because the gain is unsourced; no gain scheduling is used (disclosed).
- b_min = 0.3 (30 km/h), Claude's estimate; §10.4 reports 0.3 against 0.5.

**Cap profile:** c = b(k) × 27.78 m/s, the ALKS desired speed. The cap must hold over the held stretch [x_h, 892 m] of edge 3; upstream of x_h it tapers at a_c = 1.5 m/s²:
- cap(x) = c for x ≥ x_h; cap(x) = min(27.78, √(c² + 2·a_c·(x_h − x))) for x < x_h.
- The taper is at most (27.78² − 8.33²)/(2 × 1.5) ≈ 234 m long, so commands start at x_h − 234 m.
- **Short zone:** held 592-892 m (300 m, as in Chaves 2018); commands from 358 m.
- **Long zone:** commands from 150 m (50 m past `alinea_3`, so capped ALKS never pass that loop); held 384-892 m (508 m).
- The 300 m from 892 m to the lane end is the acceleration area (Chaves 2018 used 300 m).

**Actuation** (every 0.1-s step, each ALKS on edge 3 in the command range, not blocked):
- `vehicle.setMaxSpeed(max(cap(x_i), v_i − a_c·0.1))`, called only when the value changes by more than 0.01 m/s. Commanded deceleration stays ≤ 1.5 m/s² at every step, including when b drops by 0.2 at an update. A cap updated once per second would let SUMO brake at the full vType decel for part of the second (MSCFModel bounds the next speed only by the decel).
- The vehicle's own vType maxSpeed is read at its first command and every command takes the minimum with it (kept for an E2 weather cap).
- Restore: that maxSpeed is set back when the vehicle leaves the command range, or when b = 1 and its cap has reached its desired speed. Restores skip blocked or removed vehicles and are counted apart from commands.
- **Never** `setSpeed` (`setSpeed(-1)` would restart a stopped vehicle) and **never** `setSpeedFactor` (it compounds with a weather cap).

**Who is commanded:** only ALKS (V161). ACC and CACC follow their own IDM. Compliance is 100 % (automated vehicles).

**Logged:** b per 60 s; commanded ALKS-seconds; cap violations (speed above cap + 0.5 m/s for more than 20 s); restore mismatches; commands to blocked vehicles; the maximum per-step deceleration of commanded ALKS.

### 3.4 Combination MC* (stage B2, always) [Q6]
- The tuned M* and C* of the same cell run together.
- **If M* is M-P** (both laws integrate the drop-loop error), MC* is a cascade: the meter acts first, and C's integrator stays at b = 1 until the meter is saturated (r held up by the queue law or at 240, or an override or backstop active, in at least one of the last 2 minutes). After 5 minutes without saturation, b returns to 1 at +0.2 per minute. This is the integrated scheme attributed to Carlson et al. 2014, TR-C 46:209-221 [VERIFY before the freeze; if the paper's logic differs, its logic is adopted and logged].
- **If M* is M-A** (different sensors), the two laws run in parallel unchanged. A cascade would hold C back until the drop queue reaches `alinea_3`.
- Why always: preventing a breakdown is a threshold effect, so two actuators that each fall short can succeed together. A KILL from the single arms alone would be open to that objection on a thesis about coordinated zones.
- The b and r histories of MC* are reported.

## 4. Grids
| Points | Law | Loop | Setpoint ô | Fixed |
|---|---|---|---|---|
| M1-M3 | ALINEA | `alinea_3` | 0.85, 0.95, 1.05 × ô_cr,m | K_R from §10.4 |
| M4-M6 | PI-ALINEA | drop loop | 0.85, 0.95, 1.05 × ô_cr,d | gains from §10.4, +400 cap |
| C1-C3 | MTFC-I, short zone | drop loop | 0.85, 0.95, 1.05 × ô_cr,d | b_min 0.3, \|Δb\| ≤ 0.2, K_I from §10.4 |
| C4-C6 | MTFC-I, long zone | drop loop | 0.85, 0.95, 1.05 × ô_cr,d | same |

- ô_cr is measured before data on throw-away days (§10.3).
- **The setpoint is the grid axis.** The literature reports low sensitivity to gain (Papageorgiou 1991; in Riehl et al. 2026, K_P from 5 to 50 differed by far less than the seed SD over 20 seeds). The setpoint has the most leverage.
- **Why the grid sits at or below ô_cr:** a feedback law can prevent breakdown only with a setpoint at or below the true critical occupancy. 1.05 absorbs an underestimate; the edge rule (§8) extends one step, to 0.75 or 1.15.
- **Idle points:** the first 3 seeds of every point run first. A point that is idle on all 3 (meter metering < 5 min, or b < 1 for < 5 min, over the day) is replaced once per family variant by the next lower setpoint not yet in the grid (step 0.10). The idle runs are kept and reported. A replacement that is idle too stops the work for the author.
- **Equal treatment:** both families get 6 points, the same seeds, the same gain-check rule, the same selection rule and the same edge rule (p1c audit finding CTRL-F14).
- **Not included:** a constant or time-of-day ALKS cap (open-loop; kept as a baseline for the later helper comparison; V98 found BN4 caps worse than NC); a gain grid; schedules that switch within the day.

## 5. Day sets
Each E1 seed runs as an R day and an I day with identical demand.

### 5.1 R: recurrent days
A full day with no incident, as in the V198 reference days.

### 5.2 I: one lane-blocking incident at a fixed site [Q3]
**The event** (a stalled vehicle; it replaces the V202 forced crash, see §13 Q3):
- At the first step at or after 16:00:00 (57,600 s), the blocker is the human vehicle (HDV car or truck) on lane `3_1` that is nearest to 650 m among those that can stop there at their vType decel with 10 m to spare (position ≤ 650 − v²/(2·decel) − 10 m). If there is none, the first such vehicle in a later step is taken.
- `vehicle.setStop(v0, "3", pos=650.0, laneIndex=1, duration=3000.0)`: it brakes at its normal deceleration and stops at 650 m. `cp.force(t, (v0,), 2700, cls)` registers it, so it is removed 2,700 s after selection (the middle of U(30, 60) min, as in V202), and `pz.add(v0)` keys the f = 3 passing zone to it (±100 m). k = 0, so no other crash happens.
- Exactly one vehicle stops, at the same site, in every arm. No emergency stop happens, so the V201 contact artefact cannot occur (a vehicle stopped at 9 m/s² from free flow, and its follower touched it).
- **Calibration check before data (§10.3):** the V199 η measurement of `v5b/fleet/incident.py` with the blocker instead of the crash, on the V200 setting (straight 3-lane road, right lane, f = 3.0, seeds 7,430,040-049). Pass: median η within 0.54 ± 0.05 on ≥ 8 valid seeds (the V199 rule; the crash gave 0.532). Report-only: the middle lane, and the per-seed difference from the V200 crash runs. **If the check fails**, the I cell falls back to the V202 crash (§13 Q3, second alternative) and that fallback is logged.

**Why this site and time:**
- 650 m on edge 3 lies inside the 611-684 m range of the V203 crash sites, about 540 m before the lane end; the incident queue reaches the merge (V203: merge breakdown +53.8 min under NC).
- 16:00 opens the busiest hour (7.75 % of ADT).
- V203 measured the crash version on the 13:00-20:00 slice: +226.0 s [203.5, 237.6] of mean HDV-car delay. The blocker's full-day effect is measured on the stage-0 NC I days.

**What each controller sees:** the drop loop is downstream of the site, so it sees an under-loaded bottleneck during the blockage (M-P relaxes, C returns to b = 1); `alinea_3` sees the incident queue once it spills back. No arm has incident logic, so **the I cell tests the recovery-phase headroom of recurrent controllers**, not incident management (disclosed, §12).

### 5.3 Pairing and checks
- **Identical in every arm:** site, lane, trigger time, duration, zone factor and the number of stopped vehicles.
- **Different by arm:** which vehicle stops and when it reaches the site (seconds after 16:00). Reported per seed and arm; an arm is flagged "incident not balanced" if its stop time differs from NC's by > 60 s on ≥ 3 of 10 seeds.
- **Prefix check:** within a seed and arm, the R and I days must match exactly up to 57,600 s (30-s series and departed counts). A mismatch stops the work for the author.
- The blocker is left out of the primary metric in every arm (§7.1).

### 5.4 Realism
I is a stress cell: one 45-min middle-lane blockage at 16:00 on a 1.2-km link. At k, P(≥ 1 crash per day) is 25 % (V198), and most crashes fall elsewhere or at other times. The I cell is reported on its own and never weighted into a "typical day".

## 6. Seeds [Q4]
| Use | Seeds | Status |
|---|---|---|
| E1 main, both cells, all arms | 7,430,230 onward, the first n (10, 15 or 20 by §9.3): 230-239, 230-244 or 230-249 | unused (seed check 2026-10-31: no run file, result or git match) |
| C1 fresh-seed extension (§9.6) | the 10 seeds after the main set (240-249, 245-254 or 250-259) | unused |
| SUMO twin seeds (demand seed + 5,000) | 7,435,230-7,435,259 as needed | unused |
| Stage 0 throw-away | 7,430,040-049, twins 7,435,040-049 | plant selected on 040-049; V198 hashes exist |
| E2 tuning (E2's own protocol) | the E1 main seeds | fixed now, regardless of C1 |
| E2 evaluation, reserved | 7,430,660-689 | unused |
| Skipped: soft allocations of drafts that never ran | 7,430,200-229, 400-419, 600-659, 800-899 | never used, so no reader can suspect reuse |
| Reserve | 7,430,260-399, 690-799 | untouched |

- **7,435,000-7,435,999 is logged as SUMO-seed-only:** never a demand seed, so no later run reuses a twin's driver-noise stream.
- **One seed set for both cells:** I − R is paired within seed and arm. Cost: a pass in both cells is not two independent results.
- **A twin** keeps the demand seed (same vehicles, departures, lanes and speed factors) and changes only SUMO's `--seed` (dawdling and lane-change draws). It needs a new `--sumo-seed` flag whose default equals the demand seed, so every existing hash holds.
- Before launch Claude re-runs the seed check (an exact grep for every range above in run folders and git) and logs the ranges in the V# row.

## 7. Metrics

### 7.1 Primary: D
- D = mean door-to-door delay per vehicle over the day [s/veh], all classes, both origins: delay_i = (duration_i + departDelay_i) − routeLength_i / v_des,i, with v_des the dry desired speed before any command (`day.py:255-257`).
- It includes the origin queue and insertion backlog, the ramp queue and meter wait, and the acceleration-lane wait. A CAV cap counts as delay.
- In I the blocker is left out in every arm; a run is valid only if arrived + removed = generated. Whether removed vehicles write a tripinfo is checked in stage 0.
- New code: the all-vehicle scalar (today only class means), with a unit test on a hand-built tripinfo.
- **Effect of arm X** (`v5b/p1/stats.py` `paired(D_NC, D_X)`): d_i = D_NC,i − D_X,i; Δ = median(d); rel = Δ / median(D_NC); two-sided 95 % percentile bootstrap over seeds, resampled jointly, B = 20,000, `BOOT_SEED` 20261019; plus the sign count.

### 7.2 Co-headline: served throughput
- Arrivals at the end of edge 5 by origin, in fixed windows: AM 07:00-10:00, PM 15:00-20:00, the whole day. Paired difference against NC with its CI.
- **Throughput loss:** the whole CI of the PM difference lies below −1 % of NC's PM throughput.

### 7.3 TTT (always reported)
- TTT_w = vehicle-hours in the network plus the insertion backlog over [0, 86,400 s]; vehicles still present count to 24:00. Full-trip TTT to the end of the drain is also reported.
- **TTT conflict:** the whole CI of the relative TTT_w difference lies below −5 %.

### 7.4 Secondary (report-only)
- D by origin, class and departure hour; D of vehicles departing 15:00-20:00; the 95th percentile of delay; the share delayed > 10 min; the off-peak share of NC delay; the share of the gain carried by vehicles arriving after 24:00 (V131 D3).
- **I cell:** recovery-phase D (vehicles departing from the blocker's removal to 20:00) and the interaction Δ_I − Δ_R.
- **Mean version:** `paired(..., mean=True)`, the per-seed gain distribution, and the number of seeds with d_i ≥ 10 % of D_NC,i. The median rule needs about 8-9 of 10 seeds better than NC (at n = 10 the percentile lower bound lies between the 2nd and 3rd order statistics), so a gain on only some days shows here and in the oracle (§8), not in the tuned arms.
- **Bottlenecks:** at the lane drop, breakdown count and minutes (detected at the drop loop), pre-queue flow, QDF and drop; at the merge, breakdown minutes and the flow at `alinea_3` (mainline plus ramp), labelled spillback-dominated. Today's merge "drop/QDF" uses the exit flow (`day.py:89`) and is not reported as a merge capacity. In C arms, `up_3` minutes below 50 km/h are reported as slow-zone minutes, not breakdowns.
- Maximum insertion backlog; maximum ramp queue; ramp waits (maximum, 95th percentile, count above 240 s); red exposure; acceleration-lane stands and merge speeds by class.
- **Controller activity:** override, backstop and downstream-limited seconds; meter-on minutes; realised/commanded rate; b history; ALKS-minutes with b < 1; ALKS compliance.
- **Operating map:** every grid point in every cell, with Δ, rel, CI and sign count.

### 7.5 Safety and tolerances
| Metric | Rule |
|---|---|
| Physical contacts | any contact stops the work for the author (V207, V211) |
| minGap intrusions [Q8] | per arm, pooled over its R and I days, against NC's pooled count: exact conditional binomial test, X_arm ~ Bin(X_arm + X_NC, 0.5) (the same vehicles over the same routes, so equal exposure), one-sided α = 0.05. p < 0.05 sets the V211 safety flag. Tabulated by location (`r`/`rj`/`3a`, zone, lane-end area, incident site) and by whether the follower trails a commanded ALKS |
| Emergency-braking warnings per day | flag if the paired median increase exceeds +5 per day with the CI excluding 0 (NC has 1-4 per day, V198; Claude's tolerance) |
| Expected crashes per day | from each run's conflict records (human followers, TTC < 1.5 s, the V173 linear rule, k = 0.001085), as in the V198 offline replay; flag if the whole CI of the relative paired difference lies above +5 % |
| Red exposure | every ramp vehicle ≤ 245 s; a violation is a controller bug: stop |
| Red passages | 0; any one is a bug: stop |
| Cap violations, restore mismatches, commands to blocked vehicles | must be 0; any one is a bug: stop. A command counts as to a blocked vehicle only if it is issued after `cp.force` ran in an earlier step; on R days nothing is blocked |

A flagged arm's pass is handled by the decision tree (§9.7). The expected-crash row looks ahead to E2: a controller that adds close encounters loses part of its gain once crashes are stochastic.

### 7.6 Harm labels (report-only, fixed now for E2)
The 5 % margin, as in V83, V99 and V212: "clearly worse" when the whole CI of rel lies below −5 %; "harm not excluded" when part of it does. Reported per arm and cell. Harm in the other cell does not block a continue; it is carried into E2 as a ledger challenge.

### 7.7 Health, per run
Drained; 0 teleports; 0 SUMO errors; arrived + removed = generated. Expected health codes: H-R2, H-R4b, H-R5 (V198), plus H-E2 and H-R1 on I days (the removed blocker never arrives; every vehicle falls under route "main"). The `health` status field is never used as the validity test. Also logged: route-file and run hashes, controller id and parameters, the blocker record, the prefix check, `wall_s`.

## 8. Tuning and oracle
**Tuned best per family and cell:** M* = the meter point (M1-M6 and any replacement or extension) with the largest Δ over the main seeds; C* likewise. Ties within 0.1 s/veh go to the middle setpoint, then the shorter zone, then ALINEA. The tuning is in-sample, which makes a KILL harder. Report-only: one tuning pooled over both cells; a leave-one-seed-out estimate (biased low, V97); G = (D_tuned − D_O) / D_tuned.

**Edge rule (stage B1, V148 precedent):**
- Fires in a cell when a family variant's tuned best sits at 0.85 or 1.05 (or at a replacement setpoint at the grid's edge), beats the 0.95 point of the same variant and zone, and no tuned arm (M*, C*) passes in that cell.
- Runs one more point, one step beyond (0.75 or 1.15), on the main seeds; at most one extension per family and cell. If the new point wins, "grid edge reached" is disclosed. The trigger has a unit test on synthetic numbers for both edges.

**Per-day oracle O_off (the decision oracle):**
- O_off,s = min(D_NC,s, min over every point run in that cell of D_point,s), with points = 12 grid points, replacements, extensions and MC*. So d_s ≥ 0: on each day it may choose no control.
- It bounds any per-day choice among these settings held constant over the day, a scheduler that can switch off included. It does not bound schedules that switch within the day.
- It is informed of the day's demand and the day's driver noise. The replicate (§9.5) removes the noise part.
- It is not CLAUDE.md's I ("never the best grid point per gate seed"); E1 reports no H. Label: "per-day oracle, in-sample upper bound".
- Family oracles O_M and O_C, and the oracle without NC, are report-only.
- Reported: the point O_off picks on each seed, how often it picks NC, and how often a grid edge.
- **Consequence:** O_off ≤ every point and NC on every seed, so with shared bootstrap draws its rel and CI lower bound are at least those of every tuned arm. After stage B is complete, if O_off fails §9.2 in both cells, the verdict is KILL whatever the tuned arms show.

## 9. KILL / continue rule

### 9.1 The realistic demand level
ADT 45,000 veh/day with the `UK_WEEKDAY` shares and the 15 % ramp share, dry, full day, plant v199: the plant's reference demand (1.1 × the ld32 full-mix pre-queue capacity / 7.75 %; V189 step 3, V190). It is the only level in E1, so no level can be picked after the data.

### 9.2 Pass rule
Arm X passes in cell τ iff: (1) rel ≥ 0.10; (2) the lower end of the 95 % CI of Δ is > 0; (3) all of X's and NC's runs in that cell are valid, with 0 contacts. (1)-(2) are exactly `p1/stats.rule_cell(paired(D_NC, D_X))["a"]`. Tuned arms (M*, C*, MC*) count directly, unless §9.4 requires their replicate; O_off counts only through its replicate (§9.5).

### 9.3 Stages and power [Q7]
1. **Stage 0** (§10): checks, calibration, gains, and the power rule below.
2. **Stage A:** 13 arm-points (NC + 12) × n seeds × 2 cells. No outcome metric is read until stage A is complete; only stop-rule and activity fields are monitored.
3. **Stage B:** B1 edge extensions where §8 fires, then B2 MC* in both cells. Tuned arms and O_off are then recomputed.
4. **Stage C (conditional):** C1 for a borderline tuned arm (§9.6); the Rule 2 replicate of a tuned pass (§9.4); C2 in a cell where only O_off passes (§9.5). In a cell where C1 and C2 could both apply, C1 runs first.

**Power rule (per cell, from stage 0, before any main-seed run):**
- s = SD(d0) / median(D_NC), with d0_s = D_NC,s − D_twin,s over the 10 throw-away twin pairs of that cell; its upper 80 % confidence bound s_U = s × √(9 / χ²₉(0.20)) ≈ 1.293 s.
- n = the smallest of 10, 15 and 20 with P(pass | true gain 15 %) ≥ 0.80 at s_U, by Monte Carlo of the exact §9.2 rule (normal d, R = 2,000, B = 2,000). Both cells use the larger n.
- Pre-computed (Claude's Monte Carlo, ±0.02): P(pass) ≥ 0.80 at a true 15 % needs s_U ≤ about 0.125 at n = 10, 0.14 at n = 15, 0.17 at n = 20; so n = 10 if s ≤ 0.097, 15 if s ≤ 0.11, 20 if s ≤ 0.13. At a true 10 % no n gives more than about 0.50, because the point estimate must reach 0.10.
- A cell that misses 0.80 even at n = 20 still runs at n = 20, but is labelled underpowered: its non-pass is reported and does not count toward a KILL.
- **After stage A:** the same calculation with the observed SD of the best tuned arm's paired differences. Below 0.80 there, the KILL is labelled "underpowered (post hoc)".
- The noise of the twins (independent SUMO seeds) is probably larger than that between an arm and NC run on the same SUMO seed, so this rule errs toward more seeds (Claude's inference).

### 9.4 Noise floors (stage 0, report-only, with two fixed rules)
A Monte Carlo under the global null with per-run noise SD = SD(d0)/√2, n seeds:
- φ_O: the expected in-sample rel of O_off (12 points + NC);
- φ_T: the expected rel of the best of one family's 6 points;
- the false-continue probability of the whole procedure (tuned arms, MC* as a 7th point, B1, C1, O_off and its replicate).
- Claude's pre-computation at n = 10: s = 0.10 gives φ_O ≈ 0.115 (P(rel ≥ 0.10) ≈ 0.69) and φ_T ≈ 0.038; s = 0.13 gives φ_O ≈ 0.149 and φ_T ≈ 0.049.
- **Rule 1:** if φ_O ≥ 0.05, the oracle replicate C2 is part of the expected path and is budgeted. A noise-dominated oracle cannot give a continue by itself; a failing in-sample O_off is still a KILL.
- **Rule 2:** if φ_T ≥ 0.05, a tuned pass also needs its replicate: the tuned point and NC on the twin SUMO seeds of the main set, §9.2 on the twin pairs (NC twins shared with C2).

### 9.5 Oracle replicate (C2) [Q5]
- When: O_off passes in-sample in a cell where no tuned arm passes.
- What runs: per seed, the pick j*(s) and NC on the twin SUMO seed; where j*(s) = NC the twin difference is 0 and no extra run is needed. At most 2n runs per cell.
- Pass: §9.2 on the twin pairs (D_NC,twin − D_j*,twin). It removes noise picking and keeps the oracle's knowledge of the day's demand. It does not test new days (E2 does). The replicated estimate is biased low; in-sample and replicated values are reported as a bracket (V97).

### 9.6 Fresh-seed extension (C1)
- When: the best of M*, C* and MC* in a cell has rel ≥ 0.10 but a CI that includes 0. Once per cell.
- What runs: NC and that arm at its chosen setting on the 10 seeds after the main set (20 runs).
- Pass: §9.2 on all n + 10 seeds, and the fresh 10 alone give rel ≥ 0.05. Both values are reported. C1 is part of the global-null Monte Carlo.

### 9.7 Decision tree
Per cell τ, after stage B and any stage C:
- P_T(τ): a tuned arm passes (§9.2, with C1 and Rule 2 where they apply) and is not flagged;
- P_O(τ): O_off passes in-sample and C2 confirms;
- F(τ): a pass that is flagged: V211 safety flag, braking or expected-crash flag (§7.5), "incident not balanced" (§5.3), throughput loss (§7.2) or TTT conflict (§7.3).

The first matching line decides:
| Order | Condition | Verdict | Next |
|---|---|---|---|
| 1 | P_T(R) | CONTINUE-T | E2 as drafted, after the author's OK |
| 2 | P_O(R) | CONTINUE-O | E2 with per-day adaptation as its question; tuned arms below 10 % disclosed |
| 3 | P_T(I) or P_O(I) | I-ONLY | default: the recurrent line on v199 is KILLed and E2 does not start; an incident study needs its own protocol. The author may override in a logged V# |
| 4 | F(R) or F(I) not empty | FLAGGED-ONLY | default: treated as no pass, so KILL, with the flags reported. The author may override in a logged V# with reasons |
| 5 | otherwise | KILL | logged as a V# with a ledger entry; E2 does not run |

- A KILL is labelled "powered" if the power rule held in both cells and after stage A; otherwise it names the underpowered cell. With every KILL: the upper CI end of rel for O_off and the best tuned arm, the in-sample/replicate bracket, and the leave-one-seed-out values.
- **Multiplicity:** up to 8 chances to continue (3 tuned arms and O_off × 2 cells), with no correction. A correction would make a KILL easier; a false continue costs E2 compute, a false KILL ends the plant. The asymmetry is deliberate; the global-null false-continue probability (§9.4) is reported. E2 controls multiplicity for its own claims.

### 9.8 False results and their guards
| False KILL path | Guard |
|---|---|
| the grid misses the good setpoint | measured ô_cr; idle-point replacement; edge rule; O_off over all points |
| the meter faces a distant bottleneck | PI-ALINEA at the drop loop [Q2] |
| two partial gains that add up | MC* always, a cascade when both laws share a sensor |
| a gain on some days only | O_off may choose NC per day; mean version and seed counts reported |
| headroom only in the incident recovery | the I cell (incident management itself is untested, disclosed) |
| headroom only in rain | none; disclosed (V212 ledger) |
| a real gain hidden by noise | power rule (MDE 15 % at 0.80); C1; upper CI end reported |
| the full-day mean dilutes a peak gain | PM-departure D and the off-peak share reported |
| a weak actuator by construction | red-rest meter with kinematic amber and a queue law inside the backstop; per-step tapered caps; T0 acceptance tests |
| a bug or an idle controller | unit tests, T0, T3, smoke runs; idle-point rule |
| too little CAV authority (25 % actuated) | none; the KILL holds at this penetration only (disclosed) |

| False continue path | Guard |
|---|---|
| the oracle picks noise | noise floor; replicate C2 |
| the tuned best picks noise | Rule 2; leave-one-seed-out report; E2 on 30 fresh seeds |
| delay moved to the ramp or origin | D includes both; split by origin; V190 limits and backstop |
| a gain from the drain (p1c DRAIN) | full days; control active all day; after-24:00 share |
| a gain bought with safety | V211 binomial flag; braking and expected-crash flags |
| a milder incident in the controlled arm | one blocker at a fixed site; stop-time balance |
| the percentile bootstrap too narrow at small n | sign count and mean version reported |
| no stochastic breakdown in the plant (V176), which favours flow-holding controllers | disclosed |

### 9.9 Every verdict is reported with
All arms in one table (never NC alone); throughput, TTT and safety flags; harm labels in the other cell; the drop and QDF at the lane drop; every run, failed and smoke runs included.

## 10. Checks before data
Criteria are fixed here, before they run. No main-seed run starts before all of §10 passes.

### 10.1 Unit tests (V137 lesson)
- **Meter:** clipping; the r_s state (commanded vs realised; downstream-limited periods); the queue law; the queue override and backstop with hysteresis; rest green at 900 and at ≥ 1.05 × arrivals with ≤ 2 queued; red rest and the per-vehicle green; the 5-s onset amber; the PI-ALINEA +400 cap and the sign of its difference term. A synthetic test: 523 veh/h arrivals for 2 h with ALINEA pinned at 240 never trips the backstop and keeps the longest wait below 210 s.
- **CAV:** saturation and rate limit of b; the cap profile and the per-step deceleration limit (including a 0.2 drop of b); command range by edge and position; blocked vehicles skipped; restores skip blocked or removed vehicles; the saved maxSpeed restored exactly, also with a pre-set vType maxSpeed (the E2 bound case: command = min(cap, maxSpeed)); b = 1 gives no command.
- **Cascade:** C's integrator stays at b = 1 until the meter is saturated, and returns as specified.
- **Blocker:** selection by the braking filter; exactly one vehicle; stop at 650 m on `3_1`; removal at selection + 2,700 s; passing zone keyed to it.
- **Metrics:** D on a hand-built tripinfo with the removed vehicle left out; TTT_w with an insertion backlog; window throughput; waits and red exposure; the binomial safety test.
- **Runner:** folder layout with arm, point and SUMO seed; `--ctrl` and `--sumo-seed` defaults; resume from a job list; first-3-seeds ordering; tuned and oracle selection; the edge, C1, Rule 2 and C2 triggers and the decision tree on synthetic numbers.

### 10.2 Wave 1 on throw-away seeds (no controller outcome is read)
- **NC full days:** 10 R days (7,430,040-049) and their 10 twins (7,435,040-049); 10 I days (040-049) and their 10 twins.
- **Blocker η check:** 10 straight-road runs (V200 setting, right lane) and 10 report-only runs (middle lane), seeds 7,430,040-049.
- **T0, PM slices 15:00-19:00, each with an NC slice:**
  - meter in test mode (overrides off): fixed r = 300 and r = 450 veh/h on 040 (a queue stands); fixed r = 500 on 041 (just below demand, short queue);
  - meter with overrides on: r = 300 on 041;
  - CAV: b = 0.5, long zone, on 040 R and 040 I.
- **Smoke, full I days on 041:** M-A, M-P, C and MC at provisional settings.

### 10.3 Wave 1 analysis: pass and stop criteria
- **Inert code:** the 10 NC R days reproduce their V198/V201 hashes, 10 of 10; otherwise stop.
- **Twins:** route files byte-identical; run hashes differ. A twin that does not change the hash stops the work for the author (C2 would need another perturbation).
- **Blocker η:** as in §5.2. Also reported: the full-day I − R effect in D under NC.
- **T1:** the drop and QDF at the lane drop are reported; stop if the median drop is below 2 %, the bottom of the 2-11 % field band (Zhang & Levinson 2004, V176).
- **Drop onset t_b per NC R day:** the first breakdown after 12:00 at `drop_3`, by the `breakdowns()` speed rule applied to that loop, of any length. Stop if fewer than 8 days have one.
- **ô_cr per loop group and day:** within the 60 min before t_b, excluding 10 min after any earlier breakdown, the 5-min window (10 consecutive 30-s intervals) with the highest mean flow at that loop; ô_cr,day is its mean occupancy. ô_cr is the median over the days. At `alinea_3` it is labelled "occupancy at the pre-breakdown peak flow": M-A protects the merge area from the drop's spillback, it does not hold the merge at its own capacity (disclosed).
- **Drop-loop choice (lead time):** a loop qualifies if, on ≥ 8 of 10 days, its 60-s occupancy first crosses its ô_cr within [t_b − 5 min, t_b + 2 min] and stays below it for ≥ 80 % of the hour before t_b − 5 min. `drop_3` is used if it qualifies, else `dropend_3`; if neither does, stop for the author.
- **`alinea_3` sees the spillback:** on ≥ 8 of 10 days its occupancy exceeds ô_cr,m within 60 min after t_b, and stays below it for ≥ 80 % of the hour before t_b − 5 min. Otherwise stop for the author.
- **Power rule and noise floors:** §9.3-9.4, per cell. The I cell is checked like R.
- **T0 meter:** over owed seconds that are not downstream-limited, realised/commanded in [0.95, 1.05] per 5-min interval with ≥ 3 vehicles on `r_0`; ramp flow and `alinea_3` occupancy differ from the NC slice (counts with `getLastIntervalVehicleNumber`); 0 red passages, 0 contacts and 0 minGap intrusions on `r`, `rj` and `3a`; emergency-braking warnings on `r_0`, `rj` and the meter junction not above the NC slice; acceleration-lane stands and merge speeds by class reported against NC. On the overrides-on slice, the override and the backstop fire, and red exposure stays ≤ 245 s.
- **T0 CAV:** 0 cap violations and restore mismatches; compliance ≥ 95 %; maximum per-step deceleration of commanded ALKS ≤ 1.6 m/s²; mean ALKS speed in the held stretch within 1 m/s of c; ALKS released with a free leader (gap > 100 m) reach ≥ 0.9 × their desired speed within 300 m; drop-loop flow or occupancy differs from NC; human TTC < 1.5 s records behind commanded ALKS reported against NC; on the I slice, 0 contacts.
- **Prefix:** NC R and I match up to 57,600 s on all 10 seeds.
- **Smoke:** all runs drain with 0 contacts; output schema complete; names carry arm, point and SUMO seed; the blocker record is written; removed-vehicle handling in D checked; `wall_s` of I days recorded for the compute estimate. Outcomes are not looked at.
- **On a T0 failure:** fix, then repeat once; a second failure stops the work for the author.

### 10.4 Wave 2: gains, CAV checks, determinism (R days)
- **Gain check:** PM slices 13:00-20:00 on 7,430,040-042 at 0.95 × ô_cr; MTFC in the long zone; candidates ALINEA K_R ∈ {35, 70, 140}, PI-ALINEA {Wang-attributed, conservative}, MTFC K_I ∈ {0.005, 0.01, 0.02, 0.04, 0.08, 0.16}.
  - **Swing:** top to bottom of the range and back (b ≥ 0.9 → ≤ 0.4 → ≥ 0.9; r ≥ 850 → ≤ 300 → ≥ 850). A candidate with more than 2 swings in any hour of active control on ≥ 2 of 3 seeds is excluded.
  - **Lead time** (drop-loop laws, M-P and C): among the rest, candidates that act (r < 900, or b < 1) before the run's drop onset on ≥ 2 of 3 seeds, or whose run has no onset, are preferred.
  - **Choice:** then the lowest median RMS of the controlled occupancy around ô over the active minutes; the nominal (70; Wang-attributed; 0.02) wins if within 10 % of the best; a candidate that never acts on ≥ 2 of 3 seeds has no RMS. If every candidate of a law is excluded, stop for the author. This is a control-quality criterion, not the outcome metric.
- **b_min (report-only):** at the chosen K_I, b_min 0.5 against 0.3 on the same slices: TTC < 1.5 s records, intrusions and the minutes at b_min. Any C safety flag is disclosed as conditional on b_min.
- **Self-reaction:** off-peak slices 10:00-13:00 on 040-042, fixed b = 0.5 in the long zone against NC. If drop-loop occupancy rises by > 10 % (the released ALKS still accelerate past the loop), C uses `dropend_3`, if it qualified in §10.3; otherwise this is disclosed.
- **T3, after the gains are fixed:** 3-h I slices (15:00-18:00, seed 040) for M-A, M-P, C and MC at 0.85 × ô_cr, 5 repeats each in separate processes. Pass: 5 of 5 identical run hashes and controller logs per arm; each repeat logs ≥ 10 red phases (meter arms) or ≥ 10 ALKS-minutes with b < 1 (C arms); every hash differs from the NC slice. Plus one MC full day at the same settings, run twice, identical (covers the drain and the 24:00 snapshot). Fix-then-repeat-once applies.

### 10.5 Freeze and launch
- **Into decisions.md (V#) before the first main-seed job:** ô_cr,m, ô_cr,d and the drop loop used; L̄ and the chosen gains; the blocker check result; s, s_U, n, φ_O and φ_T per cell; the regression hashes; this protocol's sha256. Every value fixed in stage 0 is disclosed as calibrated on throw-away seeds.
- **Checkpoint:** adversarial code review of the plant changes, controllers and runner (phase table: checkpoint, ultracode on).
- **Launch:** from a frozen detached worktree at the run commit, as a systemd user unit; jobs run as `python -m v5b.fleet.day one … --ctrl …` so that the guard pattern `v5b\.fleet\.(day|weather|incident) one` matches; `unset SUMO_HOME; export OMP_NUM_THREADS=1`; the package temperature logged per batch; after the resource check, a check that the v6 sessions are idle (otherwise CPU < 15 %) and the seed re-check; I days first in the job order (the slowest). Before any night, Claude asks the author: away mode or the quiet limits (V208).

### 10.6 Stop rules during the runs
- **Stop the batch for the author on:** any physical contact; a run that does not drain, teleports or has a SUMO error (V207, V211); any broken invariant of §7.5; an R/I prefix mismatch; an idle replacement point (§4).
- **Process failure:** re-run that job once; a second failure stops the work.
- **Actuator fault (stop):** meter realised/commanded outside [0.90, 1.10] over a run's metering, non-downstream-limited owed seconds with ≥ 3 vehicles on `r_0`; ALKS compliance below 90 %.
- **CPU:** the CPU guard through `v5b/ops/watch.py`, at most 27 workers; pauses do not change results.
- **A bug found after results:** fix, re-run everything affected on the same seeds, log both outcomes (CLAUDE.md).
- **Every run is kept and reported,** failed and smoke runs included.

## 11. Compute

### 11.1 Runs and time
Rate: about 11 full-day runs per hour with 27 workers, unpaused (the first phase-2 jobs finished after 8,416-9,372 s). Phase 2 as a whole ran at about 6 days per hour of wall time because the quiet nights paused it. Slices, Claude's estimates: 13:00-20:00 ≈ 0.45 day, 15:00-19:00 ≈ 0.3, 3 h ≈ 0.25, a straight-road η run ≈ 0.1. I days and controlled days may cost more (more vehicles in the network, per-step ALKS caps); stage 0 measures it.

| Stage | Day-equivalents | Compute at 11/h | When |
|---|---|---|---|
| 0, wave 1 | about 49 (40 full NC days, 9 T0 slices, 4 smoke days, 20 η runs) | about 4.5 h | always |
| 0, wave 2 | about 25 (33 gain slices, b_min, self-reaction, T3, 2 smoke days) | about 2.3 h | always |
| A | 26 n: 260 / 390 / 520 at n = 10 / 15 / 20 | 24 / 35 / 47 h | always |
| B1 | ≤ 4 n | ≤ 3.6 h at n = 10 | tuned best at an edge, no tuned pass |
| B2, MC* | 2 n | 1.8 h at n = 10 | always |
| C1 | ≤ 40 | ≤ 3.6 h | borderline tuned arm |
| C2 | ≤ 4 n | ≤ 3.6 h at n = 10 | O_off passes in-sample only |
| Rule 2 replicate | ≤ 2 n extra | ≤ 1.8 h at n = 10 | φ_T ≥ 0.05 and a tuned pass |

- **Expected path at n = 10** (a KILL, B1 in two family-cells): about 374 day-equivalents, 34 h of compute; about 38 h if C2 runs in both cells (likely if φ_O ≥ 0.05).
- **Worst case at n = 10:** about 45 h. **At n = 20:** expected about 69 h, worst about 80 h.
- **Against V212's "about 22 h":** V212 counted stage A at 10 seeds only. Added: stage 0 (about 7 h), MC*, the conditional stages, and possibly more seeds from the power rule.
- **Wall time:** each stage waits for its slowest job (a full day is about 2.3-2.6 h under load), so add about 2-3 h per stage boundary. Expected at n = 10: about 42-46 h in away mode; each quiet night adds up to about 9 h if jobs are paused.

### 11.2 Build (author and Claude time, not compute)
About 700-800 LOC plus about 350 LOC of tests (Claude's estimate after the review additions):
- `fleet/control.py`: `RampMeter` (ALINEA, PI-ALINEA, queue law, overrides, red-rest actuator), `ALKSHarmonizer` (law, cap profile, per-step actuation), the cascade;
- `day.py`: the hook (per second and per step), the blocker, the new loops and their 30-s series, D and the other metrics, the folder layout, `--ctrl`, `--sumo-seed`;
- `incident.py`: the blocker mode for the η check;
- `fleet/e1.py`: job lists, resume, first-3-seeds ordering, CPU guard, analysis (ô_cr, lead-time tests, swings, RMS, prefix and balance checks, power and noise-floor Monte Carlo), tuned and oracle selection, stage triggers, the decision tree.

### 11.3 What is cut, and why a KILL stays valid
| Cut | Saving | Bias for a KILL | Why acceptable |
|---|---|---|---|
| no separate validation seeds; tuned arms and O_off judged in-sample | about 26 n runs | against a KILL | makes a KILL harder; replicates and E2 protect a continue |
| 6-point grids, gains from a pre-check | full grids, about 1,000 runs (rejected in V212) | toward a KILL | measured ô_cr; idle and edge rules; O_off; low gain sensitivity in the literature |
| n from the power rule, not 30 | 30-seed designs | toward a KILL for gains of 10-15 % | MDE stated; C1 when borderline; upper CI end reported |
| MC* at one point, no joint tuning | a 6 × 6 grid, about 720 runs | toward a KILL | MC* enters O_off; disclosed |
| one blocker placement; no stochastic crashes | stochastic crashes are unpaired | either way | the stochastic mix is in E2 |
| dry only | heavy rain in E2 | toward a KILL for a rain-only gain | V212; ledger challenge; disclosed |
| no MPC, no non-learning scheduler | a model-based arm | toward a KILL | optional under D5.8, disclosed; O_off bounds every per-day choice over these settings |
| ALKS-only commands, no human VSL | none (V161, V212) | toward a KILL | disclosed; full-compliance human VSL would overstate headroom |

Rejected cheaper designs: forking I days from a state saved at 16:00 (saves about half of each I run, but needs saved Python state and adds a determinism risk); peak-hour windows for the main runs (V212: different vehicle draws); R first and I only after a KILL in R (saves nothing on the expected path, and I is needed for the harm labels).

## 12. Disclosures
- **Oracle:** in-sample per day; may choose NC; not CLAUDE.md's I; no H; bounds only choices held constant over the day.
- **Tuning:** chosen and judged on the same seeds; E1 is a screen and no E1 number is a claim. The protocol is fixed and hashed before data but not registered externally; avoid the wording "pre-registered before any data" (V130).
- **Statistics:** no multiplicity correction; n from the power rule; MDE 15 % at 0.80; gains of 10-15 % can be missed; the median rule needs about 8-9 of 10 seeds better than NC; at small n the percentile bootstrap moves in steps between order statistics.
- **Calibration seeds:** ô_cr, L̄, the drop-loop choice, the gains, SD(d0), the noise floors and the power estimate all come from 7,430,040-049, on which plant v188/v190 was selected. The power estimate is re-stated on the main seeds after stage A.
- **Dry only:** if E1 gives a KILL, an advantage that exists only in heavy rain is never tested (V212 ledger).
- **Incident:** one site and time; a stalled vehicle with normal braking, not a crash; checked against the V199 η target, not against field incident durations; a stress cell; it tests the recovery-phase headroom of recurrent controllers, not incident management.
- **Ideal sensing and actuation:** perfect loops (no faults, noise or delay; V176 lists detector faults as missing); N_q and waits from simulation counts; exact ALKS positions; no command delay; 100 % ALKS compliance.
- **Commandable share:** 25 % (ALKS). ACC and CACC are IDM with short gaps and no cooperation (V173); IDM CAVs are probably more string-stable than production ACC (V176 (e)), so the CAV rule's gain may differ from reality in an unknown direction.
- **Missing mechanisms (V176):** stochastic Weibull breakdown; off-ramp spillback; level-dependent VSL compliance; grades and sags; detector faults; stop-and-go wave speed and period. The last one and IDM string stability bear directly on CAV headroom.
- **Meter:** V190 limits after FHWA (V176) [VERIFY the FHWA values]; the queue law (150-s target), the 210-s backstop, the hysteresis values, the override thresholds and the signal timing are Claude's choices; they leave a lever of about 22 vehicles; no unconstrained-meter row.
- **CAV rule:** K_I range, b_min, a_c = 1.5 m/s², the zone ends and the acceleration area are Claude's choices (Carlson 2011, Müller 2015 [VERIFY]); no gain scheduling.
- **MC*:** a cascade when both laws share the drop loop, parallel otherwise; no joint tuning.
- **Merge metrics:** the merge's own capacity drop is not measured (its breakdowns follow the drop's spillback).
- **Ramp share and QDF:** 15 % ramp share [VERIFY]; the 1,794 veh/h/lane QDF is the ld32 human fleet (V187).
- **The 10 % bar** is a project rule (CLAUDE.md), not a field threshold.
- **Expected size of gains:** Chaves et al. 2018 found −24.4 % TTS for MTFC with a 22 % drop and a 3-h peak (AIMSUN); Jin & Jin 2013 found that speed control helps only with a capacity drop, and more with a larger drop. This plant's median drop is about 11 %, and a full-day mean dilutes peak percentages.
- **Literature status:** "full text" means the E1 literature agent opened the source in this round; Claude did not re-open them. Abstract-only or secondary sources are marked [VERIFY].

## 13. Author questions
Each gives Claude's recommendation, its pros and cons, and the alternatives Claude considers inferior.

**Q1. Which CAV speed-harmonization rule?**
- **Recommended:** I-type MTFC on the ALKS only (§3.3): drop-loop feedback; a cap profile that tapers at 1.5 m/s² so the cap holds over the whole zone; caps applied every 0.1-s step; short (held 300 m) and long (commands from 150 m) zones; K_I chosen from 6 values over a factor of 32; b_min 0.3.
- **Pros:** model-free feedback with few parameters, like ALINEA; its closest published precedent is a merge plus lane drop with ACC actuators (Chaves et al. 2018); it shares PI-ALINEA's detector, so the families compete on equal terms; the review fixes remove two weaknesses by construction (most of the short zone spent braking; 4.5 m/s² pulses from once-per-second caps).
- **Cons:** K_I, b_min, a_c and the zone ends are Claude's choices; humans can overtake capped ALKS at 25 % penetration, so its authority is uncertain; it cannot see an incident upstream of its loop; per-step commands cost some run time.
- **Inferior alternatives:** PI or cascade MTFC (Müller et al. 2015 [VERIFY]): one more unsourced gain that 6 points cannot tune. Trajectory-based harmonization (FHWA-HRT-21-008; Ghiasi et al. 2019 [VERIFY]): needs a queue-tail prediction, and its published results are bundled with CACC and cooperative merging. CV moving bottlenecks (Han, Chen & Ahn 2017 [VERIFY]): needs fundamental-diagram parameters, and at 25 % actuation reduces to a zone cap. SPECIALIST (Hegyi & Hoogendoorn 2010 [VERIFY]): built for moving jams, not a standing lane-drop queue. A constant or time-of-day cap: open-loop, not a proven controller. The draft's once-per-second cap: pulse braking charged to the CAV rule's safety flags.

**Q2. The meter arm: ALINEA only (V212's wording), or 3 ALINEA and 3 PI-ALINEA points, with the revised actuator?**
- **Recommended:** 3 ALINEA points at `alinea_3` and 3 PI-ALINEA points at the drop loop; the meter rests in red while metering and gives one short green per waiting vehicle, with a 5-s kinematic amber at metering onset; a queue law that targets 150 s, inside the 210-s backstop; the backstop releases at the maximum rate instead of resting green.
- **Pros:** the active bottleneck is the lane drop 1.2 km past the merge, where ALINEA alone is reported as poorly damped (Wang 2014) or not capable (Kan 2016) [VERIFY, abstracts only], and PI-ALINEA is the published fix; the same compute covers both bottlenecks. The actuator fixes remove two flaws the review found: the draft's wait rule settled at 240 s, above its own 210-s backstop, so every strong meter point would flush its queue at the peak; and a 1-s amber in front of 100 km/h traffic would add hard braking that is charged to the meter.
- **Cons:** 3 setpoints per variant; the Wang gains come from a secondary source; departs from V212's wording; the meter can hold only about 22 vehicles; the signal timing is Claude's choice, accepted only through T0.
- **Inferior alternatives:** 6 ALINEA setpoints: the lane drop gets no proper law, a straw-man objection to a KILL. The draft's actuator (rest green, 1-s amber, 240-s wait rule): weakens the meter by construction. netconvert's 6-s amber with 2 vehicles per green: longer cycles and release overshoot (the V140 mechanism). A meter-approach speed zone in every arm: a plant change, so new hashes and a new regression. An unconstrained meter (no 4-min limit): not deployable; at most a report-only row.

**Q3. The incident in the I cell?**
- **Recommended:** a stalled vehicle at a fixed site (§5.2): at 16:00 the nearest human vehicle on `3_1` that can stop at 650 m with normal braking; stopped 45 min; f = 3 zone around it; checked against the V199 η target before data.
- **Pros:** the same site, lane and vehicle count in every arm by construction. It removes a bias the review found in V202: an arm that keeps traffic moving meets the 16:00 crash in free flow, as a single-vehicle emergency stop from about 25 m/s. That is the V201 contact artefact, so the contact stop rule would halt exactly the arms that work. V199's η was calibrated on a single stopped vehicle too. About 40 LOC; the check costs about 2 day-equivalents.
- **Cons:** departs from V202 and from the V203 measurements (the crash version); a stall with normal braking is a milder start than a crash; which vehicle stops still differs by arm; if the η check fails, E1 falls back to the crash version.
- **Inferior alternatives:** V202 unchanged, plus a crash-speed balance flag and a "not evaluable" label for arms with a forced-crash contact: cheaper, but the I cell would be unevaluable or biased against effective arms, toward a false KILL. A fixed lane closure: needs edge 3 split (a plant change, new hashes, a new regression). An earlier trigger in free flow (15:00): every arm gets a free-flow crash, with the contact artefact. Two placements: +26 n runs. Stochastic crashes: unpaired across arms (E2).

**Q4. Seeds?**
- **Recommended:** the §6 table: main from 7,430,230 (n by the power rule); C1 on the next 10; twins at demand seed + 5,000, with 7,435,000-7,435,999 logged as SUMO-seed-only; stage 0 on 7,430,040-049 and twins 7,435,040-049; E2 tuning on the E1 main seeds; E2 evaluation reserved at 7,430,660-689.
- **Pros:** all unrun (seed check 2026-10-31); clear of drafts that never ran (V153, V154); one set for both cells keeps I − R paired; 040-049 allow the hash regression against V198; twins keep demand identical.
- **Cons:** only n independent demand draws; 040-049 are selection-conditioned (disclosed); the twin range lies in V135's "rest reserved" part (an exact grep before use).
- **Inferior alternatives:** starting at 7,430,200 or 220 (named in drafts that never ran, which invites a reuse question); separate I seeds (the within-seed I − R pairing is lost at the same cost); twins at 7,430,250-259 (they would equal the default SUMO seed of later runs on those demand seeds); twins in 8,xxx,xxx (8,000,000-8,099,999 belongs to v6); stage 0 on the unused 7,431,050-079 (loses the V198 hash regression).

**Q5. The oracle and its replicate?**
- **Recommended:** one decision oracle O_off that may also choose no control on each day; it counts only if its picks pass again with new SUMO draws (C2). Tuned passes need a replicate only if their noise floor φ_T ≥ 5 % (Rule 2).
- **Pros:** O_off bounds a per-day scheduler that can switch off, which is what a learning helper could be, and it catches gains that hold on some days only (the median rule cannot). The replicate is needed: at the noise level the draft's power check accepted, the in-sample oracle "passes" from noise alone with probability about 0.69-0.89 (Claude's Monte Carlo). One oracle instead of three cuts the chances to continue from 12 to 8.
- **Cons:** an in-sample oracle pass that does not replicate becomes a KILL (a change to V212's rule); the replicated estimate is biased low (reported as a bracket, V97); C2 is likely on the expected path (about +4 h).
- **Inferior alternatives:** V212 literally (an in-sample oracle pass leads to E2): spends E2's compute on noise. Three oracles, each replicated: more chances to continue and up to 3 × the runs. Always replicating tuned passes: about 2 n runs for a bias of about 4-5 % (φ_T, Claude's Monte Carlo), and E2 re-tests on fresh seeds anyway. A leave-one-seed-out oracle as the rule: needs a predictor of the day, which E1 does not have (reported only). E1b, a full grid on fresh seeds: about 22 h, and it still selects per day.

**Q6. The additions to V212's design: MC* always, the edge rule, the fresh-seed extension?**
- **Recommended:** yes. MC* in both cells always, as a cascade when both laws use the drop loop and in parallel otherwise; edge extensions only where a tuned best sits at an edge and no tuned arm passes; C1 only for a borderline tuned arm, passing only if the fresh seeds alone give rel ≥ 0.05.
- **Pros:** answers the three strongest objections to a cheap KILL (the grid stopped short; two actuators beat either alone, the thesis topic; a real gain hidden by noise); the conditional parts run only when they could change the verdict; the cascade is the published integrated form [VERIFY Carlson 2014].
- **Cons:** about 2 n + up to 4 n + 40 runs; MC* at one point, without joint tuning; C1 reuses the first seeds for selection (disclosed; the fresh-only condition limits it).
- **Inferior alternatives:** stage A only: a KILL open to all three objections. An additive screen (run MC* only if the summed per-day gains reach 10 %): it skips exactly the threshold case where two actuators that each fail succeed together. A 6 × 6 combined grid: about 720 runs. A parallel MC* even when both laws integrate the same error: two integrators fighting is a straw man.

**Q7. How strong must a KILL be?**
- **Recommended:** a stated minimum detectable effect: n is the smallest of 10, 15, 20 with P(pass | true 15 %) ≥ 0.80 at the upper 80 % bound of the measured noise, per cell; a cell underpowered at 20 seeds does not count toward a KILL; every KILL reports the upper CI end of rel.
- **Pros:** a KILL then means something checkable. The draft's check accepted noise at which a true 10 % gain passes 38 % of the time and a 15 % gain 76 % (Claude's Monte Carlo, matching the reviewer's); its claim that E1 "could have seen a real 10 % gain" was false. The 10 % bar of CLAUDE.md stays unchanged.
- **Cons:** gains of 10-15 % can be missed (stated); n = 20 would double stage A (about 69 h expected instead of 34-38 h); the noise is estimated from 10 throw-away pairs.
- **Inferior alternatives:** the draft's half-width check: false KILLs about 63 % of the time at a true 10 % gain, at its acceptance limit. MDE 10 % at 0.80: impossible while the point estimate must reach 0.10 (at most about 0.50 for any n). A lower screening bar (for example 7 %) so that 10 % gains are seen: departs from the binding 10 % rule and lets more E2 runs start on gains E2 must then reject. 20 seeds always: about +24 h even when the noise is low.

**Q8. The operational test for the V211 safety flag?**
- **Recommended:** per arm, pooled minGap intrusions over its R and I days against NC's: an exact conditional binomial test (p0 = 0.5, equal exposure), one-sided α = 0.05; plus a table by location and by whether the follower trails a commanded ALKS. Contacts still stop the work.
- **Pros:** V211's "paired CI excluding 0" can never fire at these counts (1 intrusion in 63 days so far, V209): most daily differences are 0, so the CI is [0, 0]. The binomial test flags, for example, 5 against 0 (p ≈ 0.03) and not 4 against 0 (p ≈ 0.06); the location table separates actuator artefacts (meter, zone) from plant ones.
- **Cons:** it changes how V211 is applied (its intent stays); α = 0.05 is a convention; with many arms some flags may arise by chance (all are reported, and a flag only routes the decision, §9.7).
- **Inferior alternatives:** V211 literally: a flag that cannot fire. A fixed rule such as "≥ 3 more intrusions than NC": not scaled to n or to the base rate. A per-day Poisson rate CI: needs far more events than E1 will see.

## 14. Review resolution
Three adversarial reviews of the merged draft found 49 issues (2 blockers). Claude checked them against the code and the SUMO 1.27.1 behaviour they cite, and re-ran the power simulation; all were accepted, some in a different form.

| Id | Issue | Resolution |
|---|---|---|
| stat1, buil9 (blocker) | the power check did not support "could see a real 10 % gain" | power rule with MDE 15 % at 0.80, upper 80 % noise bound, n up to 20 (§9.3, Q7) |
| stat2, buil1 (blocker) | the I cell had no noise or power check | 10 NC I days and 10 I twins in stage 0; per-cell power rule |
| cont1 (blocker) | wait rule settled at 240 s, above the 210-s backstop: flush cycles | queue law at 150 s; backstop releases at the maximum rate, no flush (§3.2) |
| stat3 | noise floor and power check worked against each other; reversed wording | Rule 1 (§9.4), corrected wording |
| stat4, cont15, buil10 | edge-rule trigger named the wrong edge | 0.85 or 1.05; "no tuned arm passes"; unit test (§8) |
| stat5 | the median rule hides day-specific gains; the oracle could not choose no control | O_off includes NC; mean version and seed counts reported (§7.4, §8) |
| stat6, cont3 | the forced crash depended on the arm and penalised arms that work | fixed-site stalled vehicle with normal braking, η check, fallback (§5.2, Q3) |
| stat7 | tuned-arm noise bias not "small" | φ_T and the global-null Monte Carlo; Rule 2 (§9.4) |
| stat8 | author-routed verdicts without defaults; incomplete outcome table | ordered decision tree with defaults (§9.7) |
| stat9 | C1 was a two-look test | fresh-only rel ≥ 0.05; in the Monte Carlo (§9.6) |
| stat10 | which oracle C2 replicates | O_off only (§9.5) |
| stat11 | when the oracle KILL applies | after stage B (§8) |
| stat12 | idle-point stop had no remedy | first 3 seeds first; one pre-stated replacement (§4) |
| stat13 | conflict flags without margins | −1 % throughput, −5 % TTT_w (§7.2-7.3) |
| stat14 | twin range not reserved; E2 seeds unclear | 7,435,xxx SUMO-seed-only; E2 tuning on the E1 main seeds (§6) |
| stat15 | calibration disclosure incomplete | SD(d0), noise floors and power added (§12) |
| cont2, buil4 | 1-s amber at 100 km/h | red rest, per-vehicle green, 5-s onset amber; T0 braking criteria (§3.2, §10.3) |
| cont4, buil7 | ô_cr anchor late; loop tests trivial; series not logged | onset at the drop loop; lead-time tests; 30-s per-loop logging (§2, §10.3) |
| cont5, buil2 | merge drop/QDF was the exit flow; slowdowns counted as breakdowns | merge reported as spillback-dominated; drop-loop breakdowns; slow-zone minutes; long zone starts after `alinea_3` (§3.3, §7.4) |
| cont6 | short zone mostly spent braking | taper upstream so the cap holds over the zone (§3.3) |
| cont7, buil13 | once-per-second caps give 4.5 m/s² pulses | per-step caps; T0 deceleration criterion (§3.3, §10.3) |
| cont8 | MTFC gain invented and narrowly searched | 6 values over ×32; lead-time preference; no scheduling disclosed (§10.4) |
| cont9 | MC* had no coordination | cascade when both laws share the drop loop (§3.4) |
| cont10 | the I cell cannot find incident-management headroom | recovery-phase D and Δ_I − Δ_R; claim reworded (§5.2, §7.4) |
| cont11 | the V211 flag could never fire | exact conditional binomial on pooled counts; location table (§7.5, Q8) |
| cont12, buil3 | actuator checks blamed downstream limits | downstream-limited seconds defined and excluded; "metering" defined; r_s rule (§3.2) |
| cont13 | drop loop may react to released ALKS | wave-2 self-reaction check (§10.4) |
| cont14, buil5 | restore and blocked-command invariants would fire on I days | restores skip blocked or removed vehicles; command timing defined; R days have no blocked set (§3.3, §7.5) |
| cont16 | b_min unsourced, drives safety flags | report-only 0.3 against 0.5; disclosed (§10.4) |
| cont17 | standstill releases may add merge stands | reported in T0 by class (§10.3) |
| cont18 | restore test only for the dry case | unit test with a pre-set maxSpeed (§10.1) |
| buil6 | T3 could pass without control acting | T3 after the gains, at 0.85 × ô_cr, activity required, 5 repeats, full-day repeat (§10.4) |
| buil8 | wall time ignored quiet nights | wall time per mode (§11.1) |
| buil11 | health codes would fail every I day | H-E2, H-R1 expected; status never the validity test (§7.7) |
| buil12 | twin file names collide | folder per SUMO seed (§2) |
| buil14 | gain-check cell, zone and density conversion unspecified | R days, long zone, mean over the drop loop's 3 lanes (§3.2, §10.4) |
| buil15 | guard pattern and launch environment | named in §10.5 |
| buil16 | I-day and controller cost unmeasured | `wall_s` from wave 1; I days first (§10.3, §10.5) |
