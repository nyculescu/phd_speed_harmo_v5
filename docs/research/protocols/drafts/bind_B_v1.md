# B bind check: cooperative gap creation without a ramp signal (protocol draft, rev 1)

Status: DRAFT rev 1, 2026-11-01, after one adversarial review. Nothing here binds until the author approves it and it gets a V number. No run may start before that. Writing this protocol is an Extra High phase with ultracode on for its design review (CLAUDE.md phase table).

Conventions:
- [A#] is an assumption made by Claude, with no field or literature source. Every number tagged [A#] needs the author's OK.
- [VERIFY] means the point is not confirmed by a source read in full.
- Prior art is cited only from the V/V\* items of `plan_ab/prior_art_B.md`, at the read level given there.
- Lane indices: on edges 1, 2 and 3, lane 0 is the right lane. On edge 3a, lane 0 is the acceleration lane and lane 1 is the right through lane (it continues lane 0 of edge 2). "Road lane" = index on edges 1, 2, 3 and index − 1 on 3a (3a_0 = "acc").

## 1. Purpose

Question, before any RL: **can mainline CAVs that open gaps (by slowing or moving left, with no ramp signal) reduce merge conflicts, conflict exposure and the merge breakdown hazard compared with no control?**

- The test arm is OR (§4.5), an informed heuristic planner with perfect state and schedule information. It is not an upper bound. A KILL means "this informed planner, and the tuned rule, found no effect" (the V242 caveat). It does not bound a learned controller with a richer action set.
- A tuned simple rule (UGR) is the first classical opponent that the later RL design must beat. The verified prior art found no tuned non-learning cooperative-merge opponent vs RL under paired seeds (prior_art_B §2, "not found in this search").
- Claim type (V74, V246; exact gate family is decision D7): merge safety is gated (C1, S1) together with the merge breakdown (C3). Smoothness is report-only in this check. Delay and served throughput are guards, co-headlined, with TTT alongside.
- Deviation from CLAUDE.md, named here: the binding early-KILL text uses door-to-door delay as the primary metric "at the realistic demand level". For B, V74 and V246 make delay a guard, and V245 replaces a single realistic level with a level axis. Both deviations need recording as a V-decision (D7).
- Out of scope: RL, claims of any kind, the lane-drop bottleneck (track A), crash days, weather.

## 2. Plant

### 2.1 Recommendation: merge-only plant `m32` primary, plus a v199 transfer row

| Option | For | Against | Cost per run (process) |
|---|---|---|---|
| **m32** (recommended): ramp32 without the 3→2 drop (edges 4 and 5 keep 3 lanes), meter TLS `rm` held green, plant v199 drivers and mix, constant-demand episodes | isolates the merge mechanism; demand can be set to the regime where gap creation is expected to work | new geometry variant and a new NC calibration ladder (§6.1); stuck-vehicle numbers not directly comparable with V193-V198; per-run cost not obviously below v199 (§10) | about 3-29 min [A1], measured in the smoke run |
| full v199, meter held green, PM slice 13:00-20:00 | no new plant; NC already characterised (V198, E1); it is where V193-V197 failed | the drop is the active bottleneck on 20/20 days (V244), and its queue spills back over the merge, so the merge sits in a standing queue for part of the PM, where gap creation is not expected to help (Scarinci 2017, "operates only in the free-flow state", full text) | median 46 min (E1-lite measured: 1,451-3,889 s under load) |

Reasons for the recommendation:
- prior_art_B §3.3: the benefits that were found come from free flow up to near-breakdown, not from standing queues. On v199 the drop's queue confounds that regime.
- The synthetic-plant principle (V245): m32's demand levels are fixed by a rule on NC calibration data before any control run, and they are reported as an axis.
- The v199 row (§6, report-only) tells whether an m32 effect survives on the thesis plant.

### 2.2 m32 definition (build, no runs yet)

- Geometry: `corridor.py` ramp32 nodes and edges, except that edges 4 and 5 have 3 lanes and the connections 3→4 and 4→5 map lanes 0-2 one to one. The acceleration lane (3a_0, 300 m) still ends, so the merge is an on-ramp bottleneck. Ramp `r` is 400 m long, 1 lane. TLS `rm` stays in the net and is held green in every arm (`fleet.all_green`), so the junction logic matches v199 NC (V4).
- Drivers and fleet: plant v199 knobs (`fleet.PLANTS["v199"]`: tau scale 0.8, action-step scale 0.5, IDM for all CAV classes). Mix V160-V161: hdv_car 42.5 %, truck 7.5 %, acc 12.5 %, cacc 12.5 %, alks 25 %. ALKS is the only commanded class (`fleet.COMMANDED`). Ramp-origin vehicles come from the same mix and are never commanded, in any arm, including ramp-origin ALKS after they merge [A2].
- Teleporting off (V197: `--time-to-teleport -1`), junction collision checks on, `--collision.action warn`, default `--collision.mingap-factor` (V211). Dry weather, no crash process (Layer A style).
- Demand: constant Poisson inflow at level Q (veh/h, total). Ramp share 15 % (V190, itself [VERIFY] against field data). 600 s warm-up at Q, a 3,600 s measurement window at Q, then the inflow stops and the run drains (cap 7,200 s, as `day.DRAIN_CAP`).
- Window key: a vehicle belongs to the window by its scheduled departure (`depart − departDelay`, as `parse_trips` gives), never by insertion or MA entry, so an arm cannot move vehicles out of the window by delaying them.
- Loops: the ramp32 loops minus the drop loops; `merge_up` (edge 2, −50 m); a new `merge_dn` loop on edge 3 at +300 m.
- Areas:
  - merge area MA = the last 100 m of edge 2, all of 3a, and the first 300 m of edge 3, all lanes;
  - control zone CZ = 1,500 m upstream of the 3a start up to the 3a start [A3].

### 2.3 CAV share

- Primary: v199 as is, so 25 % of all vehicles are commandable (ALKS).
- OR50 (ACC and CACC also commanded, 50 %) has two pre-registered uses: a report-only row at L2, and the T0 fallback (§7.1). The prior art says penetration matters: in FHWA-HRT-21-008 (full text, simulator [VERIFY]) delay falls by about 63 % already at 30 %, while Jing et al. 2022 (abstract) see conflict reductions mainly above 80 %. Commanding ACC/CACC departs from their V-definition as uncommanded production systems (D3).

## 3. SUMO-version handling

- Proposed: the toolchain stays on SUMO 1.27.1 (D9, open).
- Known gaps (prior_art_B §1d, GitHub ChangeLog and issues):
  - #17502 (IDM cooperative speeds) and #18249 (lcCooperativeHelpTime) are fixed only in 1.28.0;
  - #17483 (IDM lane-change deadlock) is fixed only in Git Main.
- Mitigations:
  - commanded CAVs act only through `setMaxSpeed` caps with a rate limit, the E1 ALKS path whose T0 passed in V226. SUMO's car-following keeps safety; there is no `setSpeed`, no `openGap` (except in the CG rival row) and no change to SUMO-internal cooperation;
  - lane changes go through `changeLane`, with SUMO's safety bits kept on (exact mode in §4.5);
  - C2 (stuck ramp vehicles), the outcome most exposed to #17483 and V193, is report-only (§5);
  - the deadlock is watched by artefact check A3 (§7.2) in every arm, two-sided.
- Excluded rung: raising SUMO-internal cooperation for CAVs (prior_art_B §3.10, item 2). The plant already sets lcCooperative = 1, and the remaining levers (lcCooperativeSpeed with IDM, lcCooperativeHelpTime) are the ones #17502 and #18249 affect in 1.27.1. It can come back as a report-only row if D9 moves to 1.28.0 (D5).

## 4. Arms

Every arm runs on the same plant, demand seed and SUMO seed as NC (common random numbers). Commands are planned at whole seconds and applied each 0.1 s step.

| Arm | Role | Stages |
|---|---|---|
| NC | baseline | C, T, E, V |
| NC′ | twin-SUMO-seed null, report-only | C |
| NCμ | micro-perturbation null for gate thresholds | C, E, V |
| CG | known-bad rule (V194) | E |
| UGR | tuned simple rule | T (grid), E (UGR\*) |
| OR | informed planner | T (grid), E (OR\*), V |
| CC | tuned constant cap (degenerate rival) | T (grid), E (CC\*) |
| R-rand | untargeted placebo | E |
| sham | determinism and instrumentation | S, E |
| OR50, NC+ban, OR+ban | report-only rows | E |

### 4.1 NC

SUMO defaults (LC2013, lcCooperative 1 as in the plant), meter green, no TraCI commands. In stage C, NC runs carry the shadow observer (§4.9).

### 4.2 NC′ and NCμ (nulls, V244)

- NC′: NC on the twin SUMO seed (demand seed + 5,000, the E1 convention). Stage C only, reported next to NCμ.
- NCμ: the same demand and SUMO seed as NC. At t = 600 s, the first ALKS on edge 1 (by vehicle id) driving within 1 m/s of its own maxSpeed gets a cap 0.5 km/h below it for 1 s, then its own maxSpeed back. This diverges the trajectories with no plausible control effect, so NCμ vs NC has the same pairing structure as an arm vs NC [A18]. The smoke check requires NCμ's trip hash to differ from NC's.

### 4.3 CG: the V194 courtesy rule (known failing, rival row)

`v5b/fleet/merge.py` CourtesyGap unchanged: openGap 1.5 s / 12 m / 10 s / rate 0.5 / 2 m/s², triggered after 10 s standing in the last 60 m. V195 failed with 0 → 10 teleports. With teleporting off in m32, the expected failure shows as A1 stuck-alongside waits, A2 self-blocking yielders and A3 deadlocks or undrained runs (§7.2). It is kept so that the tables show the known-bad rule.

### 4.4 UGR: tuned simple upstream gap-creation rule

A Scarinci-style action without a signal (Scarinci et al. 2015, full text: Δv = 10 km/h, slowing that starts ≥ 1.8 km upstream). UGR sees ramp vehicles only on `r` and `rj` (about 400 m), so ETA_j is at most about 15-20 s and its reach is about 450-600 m upstream of the 3a start, not 1.8 km. Every 1 s:

1. For each ramp vehicle j on `r` or `rj`, ETA_j = remaining distance to the 3a start / max(v_j, 5 m/s).
2. For each mainline-origin ALKS i on the right through lane (edges 1-2 lane 0, or 3a_1) with a distance to the 3a start d_i in [100 m, 1,500 m] that is not already yielding: ETA_i = d_i / v_i.
3. If |ETA_i − ETA_j| ≤ W, and j has no yielder yet, then i yields for j:
   - mode `slow`: cap = v_i − Δv, reached at ≤ 1.0 m/s² [A4];
   - mode `left`: first `changeLane(i, +1, 3 s)` when d_i > 300 m, then `slow` if the change did not happen within 3 s.
4. The cap is released when j has changed into road lane 0 ahead of i, when i passes the end of 3a, or after 30 s. Release restores i's own maxSpeed, as `SumoALKS` restores.
5. Each ALKS serves at most one ramp vehicle, and each ramp vehicle gets at most one yielder.
6. Yielder lane-change mode: as OR (§4.5, gap protection).

Tuning grid, fixed now: Δv ∈ {5, 10, 15} km/h × W ∈ {1, 2, 4} s [A5] × mode ∈ {slow, left}, which makes 18 points. The draft's D_trig axis is dropped because it selected nearly the same vehicles at 600 and 1,200 m. The smoke check requires distinct command sets across grid points. Tuning is per level (L1, L2, L3) on tuning seeds, by §8.4.

### 4.5 OR: informed gap-creation planner

**Information.**
- The exact state of every vehicle at each whole second (position, speed, lane, length, minGap).
- The full route-file departure schedule, mainline and ramp, so OR knows when each vehicle will be inserted.
- It does not know future driver noise or LC2013 decisions. It is a predictive heuristic with perfect information, not a clairvoyant optimum.

**Plan, every 1 s (receding horizon, 120 s ahead):**

1. *Ramp prediction.* For each ramp vehicle j that is on the ramp, or due to depart within 120 s:
   - t_j^nose = the time it reaches the 3a start, projected from its current speed accelerating at 1.0 m/s² up to its allowed speed [A6];
   - its merge window is x ∈ [30, 250] m along 3a_0 at its projected speeds.
2. *Slot search,* for j in order of t_j^nose (FIFO in OR-basic). Project the right-through-lane vehicles, including those due to be inserted within the horizon, at constant current speed (insertion speed for future ones), including the commands already committed for earlier ramp vehicles.
   - A slot is a consecutive pair (L, F) in that lane whose bumper gap passes the ramp vehicle's merge window while j is in it.
   - The required gap is s_req = len_j + v_F · H_req.
   - If a slot with gap ≥ s_req exists, it is logged as a "natural gap" and no command is given.
3. *Candidates.* Slots whose follower F is a mainline-origin ALKS (ramp-origin ALKS are never candidates), with the required back-shift Δs = s_req − predicted gap.
   - Back-shift achievable by a cap held until the merge time T: Δs(δ) = δT − δ²/(2a) for δ ≤ aT, so δ = aT − √(a²T² − 2aΔs).
   - Limits: a = 1.5 m/s² (A_CAP, E1); δ ≤ 30 km/h [A7]; the cap is ≥ 0.5 × v_F; no new command when F is within 30 m of the end of 3a.
   - Alternative action `left`: when F is an ALKS more than 300 m before the 3a start, `changeLane(F, +1, 3 s)` removes F from the slot, and the slot becomes (L, F's follower). It is feasible only if `getLeftLeaders` and `getLeftFollowers` gaps are ≥ v_F × 1.0 s on both sides [A8].
4. *Choice.* Among the feasible actions, pick the one with the least cost = Δs × (1 + the number of vehicles within a 2 s headway behind F) (a proxy for induced delay [A9]); `left` costs 0.5 × s_req [A9]. If nothing is feasible, log "infeasible" and give no command.
5. *Execution.* Cap v_F − δ through `setMaxSpeed`, with the rate limit of `control.command` (≤ a·dt per step). The cap holds until j is in road lane 0 ahead of F, or t_j^m + 3 s, or F leaves 3a. Then the own maxSpeed is restored. Commitments are kept unless they become infeasible, which is logged.

**OR-wide variant [A23]** (a tuning axis, D14): when F's follower F2 is a mainline-origin ALKS within a 2 s headway, F2 gets the same cap profile, so F's back-shift does not compress F-F2; and slot assignment is greedy by least cost over all ramp vehicles in the horizon instead of FIFO.

**Gap protection.**
- A yielding ALKS (slow or left, in OR, UGR and R-rand) gets laneChangeMode 1536 from its command until release: strategic, cooperative, speed-gain and keep-right changes off; bits 8-9 = 2 (respect others' speeds and gaps) and bits 10-11 = 1 kept [VERIFY the bit layout against the SUMO 1.27.1 TraCI docs]. For `left`, the mode is set once the change has completed and is held until j merges or 30 s pass, so keep-right cannot return F into the gap. Release restores the default mode.
- Human vehicles are not restricted in the primary arms. Gap theft (a vehicle other than j, from road lane 1 or from the ramp, entering the slot) is counted as a diagnostic (T0e).
- Optional near-side ban (Scarinci 2017; Zhu, Tasic, Qu 2022, full text: "leading to a failure" without it): inside MA, no right changes into the right through lane, i.e. from lane 1 on edges 2 and 3 and from lane 2 on 3a. It changes the road for every vehicle, so it is the optional pair NC+ban and OR+ban (D6).

**Tuning, as an informed oracle tuned on tuning seeds (method rule).** {OR-basic, OR-wide} × H_req ∈ {2.0, 2.5, 3.0} s [A10] = 6 points, per level, by §8.4. The other OR values are fixed now.

### 4.6 CC: tuned constant cap (degenerate rival)

The archive lesson (`docs/lessons_metric_gameability.md` §1, §3, claude/day-pattern-core) requires the best constant controller as a rival, since uniform slowing games speed-derived and spacing-derived metrics. CC caps every mainline-origin right-through-lane ALKS in CZ at its own maxSpeed − Δv, Δv ∈ {5, 10, 15} km/h [A22], with the same rate limit, released when it leaves MA. Tuned per level on tuning seeds by §8.4.

### 4.7 R-rand: untargeted-slowing placebo (V244)

- The same actuator and lane-change mode as OR, with commands not tied to ramp vehicles.
- Fitted per level from OR\*'s stage T runs only (never from stage E), frozen before stage E: the command rate (Poisson), the joint (δ, hold-time) distribution, the share of `left` actions, and the empirical distribution of command-onset positions relative to the 3a start. Each command goes to a random mainline-origin right-through-lane ALKS nearest to an onset position drawn from that distribution.
- Purpose: if R-rand matches OR, the gain comes from slowing or harmonising, not from gap creation, and the B mechanism is not shown.

### 4.8 Sham (determinism and instrumentation check)

The OR pipeline runs fully, with getters only: every speed command is `setMaxSpeed(own maxSpeed)`, a no-op, and it issues no `changeLane` and no `setLaneChangeMode` calls. The trip hashes must equal NC's.

### 4.9 Shadow observer (T0 nulls)

In every stage C NC run, OR's planner runs for all 6 tuning points with getters only and no commands, and logs each plan it would have made (target, slot, predicted gap, planned Δs). Its outcomes (did j enter ahead of F; realised minus predicted gap) give the no-command null for T0b and T0c. The smoke check requires the trip hash of NC with the observer to equal NC without it.

### 4.10 Optional rows (D3, D6)

- NC+ban and OR+ban at L2.
- OR50 at L2 (and as the T0 fallback, §7.1).
- All report-only.

## 5. Metrics

All metrics are per run, over the vehicles whose scheduled departure is in the measurement window (§2.2), unless stated otherwise.

**Lane-change detection (C1, guards).** A lane change is a change of road lane (§ conventions) of one vehicle, detected edge-aware, so a through vehicle crossing 2 → 3a → 3 on the same road lane is not a change. 3a_0 → 3a_1 is a merge. The smoke check requires exact equality of lane-change counts per (edge, from, to) in MA with SUMO `--lanechange-output`.

**Gate outcomes (recommended family, D7):**
- **C1, merge conflicts.** Conflict lane changes in MA per 1,000 window vehicles that reach MA.
  - At the 0.1 s step of the change, take the new follower F′ and the new leader L′. Bumper gap = libsumo distance + the follower's minGap, the `day.py` convention.
  - A conflict if TTC_rear = gap_rear / (v_F′ − v_c) < 1.5 s (closing only) or TTC_front < 1.5 s (V74, V173).
  - Reported split into commanded merges (target of an OR/UGR plan) and all others.
  - PET_m = gap_rear / v_F′ < 1.0 s [A11] is report-only, because OR's H_req enforces nearly the same test on the merges it commands (a Goodhart risk). Rows at 1.0 / 2.0 s TTC and 0.5 / 1.5 s PET_m are reported. Thresholds elsewhere: Z-Merge uses TTC 1.2 s (HTML); FHWA uses a 1.4 s critical gap (full text).
- **S1, conflict exposure (V74 safety measure).** Vehicle-seconds at own-lane TTC < 1.5 s (closing), all vehicles in CZ ∪ MA, per window vehicle entering CZ. Normalised by vehicles, not time, so slowing cannot dilute it.
- **C3, merge breakdown.** Minutes in breakdown at `merge_up` from `day.breakdowns` on the 30-s readings: an episode starts when the speed is below 0.5 × LIMIT on 4 consecutive readings and ends when 4 consecutive readings are not below it. Episodes are clipped to the window; an episode that started in warm-up counts only its in-window minutes and is not an in-window onset.
  - Testability floor: C3 minutes gate at a level only if NC's calibration median there is ≥ 5 min [A12]. Otherwise C3 at that level is the onset indicator (≥ 1 in-window onset), tested by an exact paired McNemar test, with the effect (b − c)/n required to exceed max(0.10, the p95 of |b − c|/n on NCμ vs NC pairs).
- Any other gate cell whose NC calibration median is 0 is untestable and moves to report-only before stage E.

**Report-only outcomes:**
- C2, stuck ramp vehicles: ramp vehicles that stood (< 2 m/s) in the last 60 m of 3a_0 for > 60 s, per 1,000 ramp vehicles (`RampMerge` longest-wait counter, V197). Report-only because it may mostly measure the V193 / #17483 LC2013 limitation; it can gate only after the D9 cross-check.
- Smoothness (V74): the SD of vehicle speeds in MA, per 60 s, then averaged. Screened against CC\* on stage T (§8.4): if CC\* reduces it by ≥ 10 % at a level, it is marked "gameable by uniform slowing" there.

**Safety guards (§8.2):**
- Physical contacts vs minGap intrusions (V211, `contact_counts`).
- Hard braking: vehicle-seconds with deceleration ≥ 3.0 m/s² (V11 proposal) and ≥ 4.5 m/s² [A13], in MA and in CZ separately.
- Conflict lane changes in CZ ∪ MA (the C1 detector over the larger area), so conflicts moved upstream by `left` actions or by vehicles passing slowed yielders count.
- SUMO "performs emergency braking" warnings (log count; whether the message carries the lane is [VERIFY]).

**Mobility guards (V74; CLAUDE.md metrics):**
- Door-to-door delay per vehicle including insertion and ramp waits (`parse_trips`), for all vehicles, mainline only and ramp only.
- Served throughput: the window vehicles that exit by the window end + 900 s.
- TTT (fixed window, unfinished vehicles counted to the window end).

**Breakdown hazard (report-only):** onsets per hour of free-state exposure at `merge_up` and `merge_dn`; P(≥ 1 onset in the window); Kaplan-Meier time to first onset per arm; on the v199 row, the same at the drop loop `up`.

**Command log** (UGR, OR, CC, R-rand, CG): for every command, t, the commanded vehicle, the target ramp vehicle, the action, δ, planned Δs, predicted gap, realised gap at the planned time, the outcome (accepted / stolen-by / not taken / infeasible), and the release reason. The shadow observer writes the same fields with no command.

## 6. Stages, seeds and runs

All seeds are **proposed, author approval needed** (D16).
- They come from the V135 block's reserved part, continuing V223's use of 7,431,000-109.
- Demand seeds 7,431,110-189 and twin SUMO seeds 7,436,110-129: not found in `docs/`, `v5b/`, `tests/`, the run-folder names under `~/work/phd/v5b1_runs`, or (rev 1) the contents of any `*.json` under `/home/catalin/work/phd` (grep for the decimal values 7,431,110-189 and 7,436,110-169: 0 files; the same grep finds 7,431,0xx in `fleet_weather_93b3eb9`, so the method works). Seeds stored in another form would be missed.
- V213 reserved 7,435,000-999 as SUMO-seed-only; 7,436,000-999 is not designated yet (D16).
- NCμ uses NC's seeds, so it needs no new seeds.
- Alternative: E1's unassigned 7,430,280-399, in the tuning part of the block, so not recommended.

Order: S → C → (freeze θ, guard informativeness, T0 nulls and levels in a committed file) → T → (freeze tuned points, T0 result, R-rand fit, smoothness screen) → E → V. Stage E launches only after T0 passes (§7.1).

| Stage | Seeds | Content | Runs |
|---|---|---|---|
| S smoke (§9) | 7,431,110 | one 20-min-window run per distinct arm and grid family at a provisional Q, plus one v199 1-h slice | about 12 |
| C calibration (throw-away, disclosed) | 7,431,110-129 | NC ladder 8 levels × 10 (110-119), with the shadow observer; at the 3 chosen levels NC on 120-129 (30), NC′ on 110-129 (60), NCμ on 110-129 (60) | 230 |
| C extension (only if no level reaches P ≥ 0.3) | 7,431,110-119 | ladder levels 1.10-1.25 × 10 | 40 |
| T tuning | 7,431,130-139 | per level L1-L3: NC 10, UGR 18 × 10, OR 6 × 10, CC 3 × 10 | 840 |
| T fallback (only if T0 fails at 25 %) | 7,431,130-139 | stage T again with the 50 % commanded set | up to 840 |
| E evaluation | 7,431,140-159 | 7 arms (NC, NCμ, CG, UGR\*, OR\*, CC\*, R-rand) × 3 levels × 20 (420); sham 2 seeds × 3 levels (6); T3 reruns of OR\*, UGR\*, CG on 2 seeds at L2 (6); OR50 at L2 × 20 (20) | 452 |
| V v199 transfer (report-only) | 7,431,160-169 | v199, meter green, PM 13:00-20:00 + drain: NC, NCμ and OR\* (OR\* tuned at L2) | 30 |
| UNCLEAR extension (D12) | 7,431,170-189 | NC, OR\*, R-rand, CC\* in one cell | 80 |
| optional | 7,431,140-159 | NC+ban, OR+ban at L2 | 40 |

### 6.1 Level rule, fixed before calibration

- Ladder: Q = {0.70, 0.75, …, 1.05} × 3 × 1,938 veh/h. The 1,938 veh/h is the V187 per-lane pre-queue flow, quoted in V199 [A14: transferring it to m32; ld43's per-lane QDF reached about 2,268 veh/h (V187), so the ladder may sit below m32's merge capacity].
- L1 = the lowest level with NC P(merge breakdown onset in the window) ≥ 0.3.
- L2 = the lowest level with P ≥ 0.7; if it equals L1, the next level up.
- L3 = the lowest level where NC's median C2 ≥ 5 per 1,000 ramp vehicles (the dense-queue regime, the V193 mode); if none, the top level.
- Extension, pre-registered: if no level reaches P ≥ 0.3, run levels 1.10-1.25 on the same seeds and apply the rule again.
- If still no level reaches P ≥ 0.3, the merge is not critical on its own in m32. Stop for the author before any control run (a plant decision with no outcome data yet), with the option of stage E on v199 meter-green PM slices (about 92 process-h extra).

### 6.2 Statistics

- Paired seeds; the median of paired differences; relative = median(diff) / median(NC); 95 % percentile bootstrap with 100,000 resamples.
- Gate multiplicity (D10, recommended): Bonferroni over 2 trigger arms (OR\*, UGR\*) × 3 gate outcomes × 3 levels = 18, which gives 99.72 % intervals (McNemar cells at α = 0.05/18). Unadjusted intervals are reported alongside. The mechanism test (§8.2 item 4) is an intersection of two comparisons that must both pass, so it needs no further correction.
- Guards use unadjusted two-sided 95 % intervals, so multiplicity never makes a guard easier to pass.
- Invalid runs (an undrained run, a SUMO error, or a physical contact after the stop rule):
  - an arm's invalid run counts as that arm's failure on that seed (V6): its worst observed value enters the statistics, never dropped;
  - an invalid NC run drops that seed's pair for every arm at that level, disclosed; if more than 2 of 20 NC runs at a level are invalid, that level is report-only [A21].

## 7. Tool checks (criteria fixed now)

### 7.1 T0: the actuator binds (on stage T data, before stage E)

Computed per level on stage T runs at the tuned points (OR\*, UGR\*), with nulls from the stage C shadow observer. Thresholds are frozen with the stage C file.

| Check | Statistic | Pass |
|---|---|---|
| T0a implementation | share of commands where the commanded ALKS (no leader, or a leader not slower than the cap) reaches cap + 1 m/s within δ/a + 2 s | ≥ 90 % [A15]; an implementation check only, since SUMO likely enforces maxSpeed as a hard cap [VERIFY] |
| T0b gap opened | median over commands of (realised gap at the planned time − OR's predicted no-command gap) / planned Δs | exceeds the bootstrap p95 of the same statistic on shadow plans by ≥ 0.25 [A15] |
| T0c accepted | share of commanded slots that the target enters ahead of the yielder (stolen and not-taken reported apart) | exceeds the shadow rate's bootstrap p95 by ≥ 10 pp [A15] |
| T0d dose | OR's commands per ramp vehicle | ≥ 1 per 20 ramp vehicles [A15] |
| T0e containment | yielders entering 3a_0 | 0 |

Outcomes, pre-registered:
- T0a or T0e fails: STOP (implementation bug), fix, re-run everything affected, log both.
- T0b-T0d fail for OR\* at a level: OR's cells at that level cannot trigger GO, reported as "non-binding".
- T0b-T0d fail for OR\* at all three levels at 25 %: run the T fallback with ACC and CACC also commanded (OR50 set, all commanded arms). If T0 fails again at all levels: **KILL B on m32, "the CAV actuator does not bind"**.
- T0 fails for UGR\* at a level: UGR's cells there are "non-binding" and cannot trigger GO.

### 7.2 SUMO-artefact check (the V193-V195 failure modes), every arm vs NC

| Mode | Measure | Flag if |
|---|---|---|
| A1 stuck with a car alongside (V195) | waits > 10 s in the last 60 m of 3a_0 with a left neighbour overlapping lengthwise | arm ≠ NC, paired 95 % CI excludes 0 (two-sided) |
| A2 self-blocking yielder (V195) | yielding ALKS below 2 m/s for > 10 s while its target has not merged | any in OR/UGR/CC/R-rand → listed; > 1 per 100 commands → flag [A16] |
| A3 deadlock (#17483-like) | any vehicle standing > 300 s; any pair standing alongside > 120 s with both able to continue on their lanes; undrained runs | undrained → invalid (§6.2); pairs ≠ NC (two-sided, 95 % CI) → flag |
| A4 contacts (V211) | physical contacts; minGap intrusions | any contact → stop rule (V207); intrusions above NC (95 % CI) → safety flag |
| A5 merge-end braking (V193) | hard braking within 50 m of the 3a_0 end | arm > NC, 95 % CI excludes 0 |
| A6 health | SUMO errors; arrived + removed = generated | any mismatch → invalid, STOP if systematic |

A flagged cell counts as not meeting §8.1. An arm that "wins" by working around a SUMO limitation (fewer stuck or deadlocked pairs than NC) is flagged too.

### 7.3 Nulls and placebos (V244)

- **Gate thresholds, computed on stage C before any control run.** For each gate statistic and level:
  - θ = the p95 of |S| for the same estimator on the NCμ vs NC pairs (20 pairs, 100,000 bootstrap resamples); the same θ on NC′ vs NC is reported alongside;
  - τ = max(10 %, θ) (D8 has the conservative alternative max(10 %, θ_μ, θ_′));
  - if θ > 30 % [A17], the cell is "uninformative at n = 20": removed from the gate before stage E and reported.
- **Guard informativeness, on stage C.** For each guard, the p97.5 of its relative paired change on NCμ vs NC. If it exceeds +20 % [A20], the guard cannot detect a +25 % increase at n = 20: it is "uninformative" and blocks GO in every cell.
- **T0 nulls:** the shadow observer (§4.9).
- **Like-for-like:** every gate statistic is a window count, mean or indicator, with no maxima. NCμ and NC′ go through the same code path as every arm.
- **Placebos:** sham = NC bit-identical (T3); R-rand and CC\* are the targeting controls (§8.2 item 4).

### 7.4 T3 determinism

The sham trip hashes equal NC's on 2 seeds × 3 levels, and the reruns of OR\*, UGR\* and CG on 2 seeds reproduce their hashes. Any mismatch: STOP.

## 8. Decision rules (fixed before data)

### 8.1 Cell effect

An arm X "beats NC by ≥ 10 %" in a cell (a gate outcome C1, S1 or C3 at a level) if:
- the cell is testable (§5 floors, §7.3 cap) and T0 passed for X at that level;
- the relative paired median reduction is ≥ τ (§7.3), or for a McNemar cell the onset rule of §5;
- the 99.72 % CI of the paired difference excludes 0 (or McNemar p < 0.05/18);
- the cell is not flagged (§7.2).

### 8.2 GO for B (to the RL design)

All of these must hold:
1. The smoke run passes, T3 passes, and T0 passes for OR\* at the cell's level.
2. OR\* or UGR\* beats NC by ≥ 10 % in at least one cell.
3. In that cell the guards hold (unadjusted 95 % CIs; each guard informative, §7.3):
   - 0 physical contacts;
   - minGap intrusions, hard braking (≥ 3.0 and ≥ 4.5 m/s², CZ and MA) and conflict lane changes in CZ ∪ MA not clearly worse: the median relative increase is ≤ +5 % and the CI lower bound is ≤ +5 % [A19];
   - delay of all vehicles not clearly worse: the CI lower bound of the relative change is ≤ +2 % (V37). Mainline and ramp delay are reported;
   - served throughput not lower by more than 2 % (the CI lower bound of the reduction is ≤ 2 %).
4. Mechanism: in that cell, OR\* beats both R-rand and the tuned CC\* on the cell's outcome (99.72 % CI excluding 0).

### 8.3 Outcomes other than GO

- **KILL B on m32**, any of:
  - no unflagged, testable, T0-passed cell of OR\* or UGR\* meets §8.1;
  - every qualifying cell fails item 3 or item 4 (report "untargeted slowing" when item 4 fails because CC\* or R-rand matches OR\*);
  - the T0 fallback fails (§7.1).
  Wording: "this informed planner and the tuned rule found no effect on m32". No inference about RL. Stop for the author before any v199 or RL work on B.
- **UNCLEAR:** the best OR\* cell has a reduction ≥ τ but its CI includes 0. No GO. One extension (D12): 20 new seeds 7,431,170-189 for NC, OR\*, R-rand and CC\* in that cell only, tested on the extension seeds alone at the full 99.72 % level; GO only if those seeds pass §8.1-8.2 by themselves.
- **STOP** is used only for code or harness faults: smoke failure, sham or T3 mismatch, T0a or T0e failure, systematic A6 errors, and the V207 contact stop rule.
- **Report-only, every outcome:**
  - oracle gap G_OR = (OR\* − UGR\*) / NC on each cell; if UGR\* captures ≥ 90 % of OR\*'s reduction, the room for a better policy within OR's action set is small (this says nothing about richer action sets);
  - the v199 transfer row (with NCμ as its noise reference), OR50, the ban rows, CG, C2, smoothness, PET_m, and the breakdown hazard.

### 8.4 Tuning objective (UGR, OR, CC; stage T, per level)

- Choose the point that minimises the sum of the median relative changes vs NC of C1 and S1 (plus C3 where its minutes floor holds) on the tuning seeds, subject to these guards (point estimates): all-vehicle delay ≤ +2 %, 0 contacts, conflict lane changes in CZ ∪ MA not above NC.
- Ties within 1 pp: the smaller Δv (UGR, CC), the smaller H_req, then OR-basic (OR).
- If no point passes the guards: the NC-closest point (smallest |Δ delay|), disclosed.
- After tuning: the smoothness screen against CC\* (§5) and the R-rand fit from OR\* (§4.7), both frozen before stage E.

## 9. Smoke check (V231), before every batch

One run per distinct arm and grid family (NC, NC with the shadow observer, NC′, NCμ, CG, UGR at its 18 points on a 10-min window, OR-basic, OR-wide, CC, R-rand, sham, OR50, v199 OR 1 h). The launch script stops on any failure. Checks:
- the output echoes the arm, the parameters, the level Q, the demand seed, the SUMO seed, the plant id and the commanded classes;
- the vehicles inserted equal the route-file departures exactly (departDelay accounted for), and each route's route-file count is inside the Poisson 99.9 % interval of its target;
- MA lane-change counts per (edge, from, to) equal SUMO `--lanechange-output` exactly (this option is used in the smoke only);
- the command log is non-empty for CG, UGR, OR, CC and R-rand, and empty for NC, NCμ (except its one perturbation) and sham; sham's hash equals NC's; NC with the observer equals NC without it; NCμ's hash differs from NC's; the 18 UGR points give 18 distinct command sets;
- every command respects δ ≤ 30 km/h and a ≤ 1.5 m/s² (+0.05 tolerance), every yielder carries laneChangeMode 1536 while yielding and the default after release, and every release restores the own maxSpeed;
- the run drains, with 0 contacts and 0 SUMO errors;
- `wall_s` is recorded, which sets the cost estimate of §10.

Batches launch from a frozen detached worktree at the run commit (memory rule). They run under the CPU guard and the v6-idle check (CLAUDE.md), with ≤ 27 workers and one simulation per process.

## 10. Machine-hour estimate

Per m32 run: 4,600 sim-s at L1/L2 (600 + 3,600 + drain), up to 11,400 sim-s at L3 (drain cap); budgeted at an average of 4,600-6,900 sim-s. Cost per sim-s 0.04-0.15 wall-s [A1]: near capacity m32 carries a similar number of vehicles to v199 (0.11), and adds per-step lane-change detection and OR planning.

| Item | Runs | Process-h |
|---|---|---|
| m32 S + C + T + E | 12 + 230 + 840 + 452 = 1,534 | 78-441 (about 240 at 0.10 wall-s per sim-s and 5,700 sim-s) |
| v199 transfer row | 30 | 23 (12-32; E1-lite PM slices: median 2,775 s) |
| conditional: ladder extension; UNCLEAR extension; optional ban rows | 40; 80; 40 | 2-12; 4-23; 2-12 |
| conditional: T fallback (50 % set) | up to 840 | 43-242 |

- Unconditional total: about **90-470 process-h**, so about **3-18 h of wall time at 27 workers**, plus about 0.3-1 h per stage boundary (each stage waits for its slowest job; a v199 run takes up to about 65 min).
- The UGR grid is 540 of the 840 stage T runs; D17 has a cheaper option.
- Not included: CPU-rule pauses, quiet nights, and build and test time. Code to build: m32 geometry, the constant-demand profile, MA/CZ instrumentation with edge-aware lane changes, the shadow observer, UGR, OR (basic, wide), CC, R-rand, NCμ, sham, the command log, and the analysis.
- The smoke `wall_s` replaces [A1] before stage C is launched. If m32 costs more than 0.15 wall-s per sim-s, re-estimate and tell the author.

## 11. What feeds the later RL design (sketch only, nothing decided)

- **Agents:** each commanded ALKS in CZ ∪ MA, with a variable count. PettingZoo parallel env (V7), parameter sharing, and attention over vehicle tokens with masks (Yan et al. 2024, HTML full text).
- **Observation per agent:**
  - own speed, distance to the 3a start, lane;
  - leader and follower gap and speed in its own lane and the left lane;
  - up to K = 5 ramp-vehicle tokens (ramp or 3a_0 position, speed, ETA difference to itself) with a mask;
  - `merge_up` 30-s occupancy and speed.
- **Information ladder:** V2V-local (realistic) vs the OR information set. Since OR is a heuristic, OR − UGR − RL differences mix information, policy class and action set; they are reported, not decomposed.
- **Action:**
  - discrete cap offsets {0, −5, −10, −15} km/h (V3 steps), plus {keep, move left} (the latter subject to D15);
  - every 1 s, through the same `setMaxSpeed` path, rate limit and SUMO safety as UGR and OR, so any safety layer is shared by the RL and classical arms (prior_art_B §3.11).
- **Reward:** C1 and S1 terms, a delay-guard penalty, and a hard-braking penalty, with weights fixed before training.
- **Taken from this check:** the levels where OR\* or UGR\* pays; which action (slow or left) they use; command rate and dose as an exploration prior; T0; UGR\* and CC\* as tuned opponents; G_OR; the measured m32 cost per sim-s.
- **Cost, same units:** 1 M env steps at a 1-s control step is 1 M sim-s: about 31 process-h on v199 (0.11 wall-s per sim-s) and about 11-42 process-h on m32 [A1]. At a 60-s step, 1 M steps on v199 is about 1,833 process-h (the "68 h" figure is wall time at 27 workers). The saving comes from the shorter step, not from m32.

## 12. Assumptions (all need the author)

- A1 m32 cost per simulated second (0.04-0.15 wall-s).
- A2 ramp-origin vehicles never commanded, also after merging.
- A3 CZ 1,500 m.
- A4 UGR decel 1.0 m/s².
- A5 UGR W grid {1, 2, 4} s.
- A6 ramp projection at 1.0 m/s².
- A7 δ ≤ 30 km/h and cap ≥ 0.5 v.
- A8 left-change gap check 1.0 s.
- A9 OR cost proxy and the left cost.
- A10 H_req grid.
- A11 PET_m definition and the 1.0 s threshold (report-only).
- A12 C3 minutes floor (5 min).
- A13 4.5 m/s² severe braking.
- A14 the per-lane 1,938 veh/h ladder base and the 1.25 extension.
- A15 T0 thresholds and shadow margins (0.25; 10 pp; 1 per 20).
- A16 the A2 flag rate.
- A17 the 30 % uninformative cap.
- A18 NCμ as the like-for-like null for CRN pairs, and its perturbation (0.5 km/h for 1 s).
- A19 guard margin +5 %.
- A20 guard informativeness (p97.5 ≤ +20 %).
- A21 invalid-NC rule (more than 2 of 20 → level report-only).
- A22 CC grid {5, 10, 15} km/h.
- A23 OR-wide definition.
- The ramp share of 15 % (V190, [VERIFY]).

## 13. Author decisions needed

Format: recommended option first; pros / cons; inferior alternatives and why.

| # | Decision | Recommended | Pros | Cons | Inferior alternatives (why) |
|---|---|---|---|---|---|
| D1 | Plant | m32 primary + v199 transfer row (NC, NCμ, OR\*) | isolates the merge; level axis per V245; thesis-plant check kept | new plant; not cheaper per run than v199 | v199 meter-green only (the drop's spill-back puts the merge in standing queues; no level axis) |
| D2 | Demand and levels | constant demand, 600 + 3,600 s, ladder 0.70-1.05 × 3 × 1,938 with a pre-registered 1.10-1.25 extension, level rule §6.1, ramp share 15 % | rule fixed before data; extension avoids a stop | [A14] base may not transfer | day profiles (levels not controllable); no extension (stop if the ladder is too low) |
| D3 | CAV share | ALKS 25 % primary; OR50 (ACC, CACC commanded) as report-only row and as the pre-registered T0 fallback | gives B a KILL path when 25 % does not bind | ACC/CACC are defined as uncommanded production systems | no OR50 (a non-binding 25 % ends in limbo); 50 % primary (departs from the fleet definition) |
| D4 | Ramp vehicles | never commanded, also after merging | keeps the "no ramp signal" claim clean | leaves ramp-side cooperation out | commanding ramp ALKS (confounds B with ramp-side control) |
| D5 | Arm set | NC, NC′ (C only), NCμ, CG, UGR, OR (basic and wide), CC, R-rand, sham; SUMO cooperation rung excluded on 1.27.1 (#17502, #18249) | degenerate rival and placebo both present; full rival ladder except a buggy rung | about 7 arms per cell in stage E | the draft set without CC (the gameability lesson's core fix missing); adding the cooperation rung on 1.27.1 (known bugs) |
| D6 | Gap protection | none in primary arms; optional NC+ban / OR+ban at L2, ban defined per edge (§4.5) | tests theft without changing the base road | ban result is report-only | ban as a plant rule for all arms (changes the road for every arm); no ban rows (theft's role untested) |
| D7 | Gate outcomes and deviations | gate family C1 (TTC only), S1 (V74 TTC exposure in CZ ∪ MA), C3 (with floor and McNemar fallback); C2, smoothness, PET_m report-only; record a V-decision that refines V74 for B, applies the 10 % KILL to this family (not delay), and lets the level axis replace "the realistic demand level" (V245) | keeps V74's safety measure; removes the Goodhart-prone PET_m and the artefact-prone C2 from the gate; names both CLAUDE.md deviations | smoothness (a V74 co-primary) not gated here | V74 literally (smoothness + TTC + hard braking: smoothness is gameable by uniform slowing, not merge-specific); the draft's C1-C3 (PET_m coupled to OR; C2 an LC2013 artefact risk; V74 measure missing) |
| D8 | Null for τ | θ from NCμ vs NC; NC′ vs NC reported | like-for-like with CRN pairs (V244) | NCμ is a new assumption [A18] | max(θ_μ, θ_′) (conservative, biases toward KILL); NC′ only (likely too wide for CRN pairs) |
| D9 | SUMO version | stay on 1.27.1; C2 report-only | no toolchain change; C2 risk removed from the gate | #17483 still present in the arms | 1.28.0 / Git Main cross-check of NC's C2 on 10 calibration seeds so C2 can gate (extra toolchain work; Git Main is not a release) |
| D10 | Multiplicity | Bonferroni × 18 (99.72 %), 100,000 resamples | exact family-wise control, simple | lower power, biased toward KILL | hierarchical (OR at × 9, then UGR\* at × 9 only if OR passes: needs a gatekeeping argument [VERIFY] to control the family-wise error); × 9 (ignores the two-arm trigger) |
| D11 | Thresholds | T0 vs shadow nulls (§7.1); artefact flags two-sided (§7.2); τ = max(10 %, θ) with the 30 % cap; guards at unadjusted 95 % with the +20 % informativeness rule | every gate and guard has a computed null (V244) | rare-event guards may turn out uninformative and block GO | the draft's fixed T0 thresholds (no null; T0c can pass without binding); Bonferroni-wide guard intervals (easier to pass) |
| D12 | GO / KILL / UNCLEAR | §8.2-8.3: KILL paths for non-binding actuators and flagged cells; STOP only for code faults; one UNCLEAR extension tested on its own seeds | B can be KILLed cheaply; no forking path after outcome data | the extension costs 80 runs | combined n = 40 re-test (inflates type-I error without alpha spending); STOP for the author on T0 failure (limbo) |
| D13 | UGR grid | Δv {5, 10, 15} × W {1, 2, 4} × mode {slow, left}, per level | every axis changes the command set | 540 tuning runs | the draft's D_trig axis (no effect within the 400 m ramp horizon); a 1 km ramp feeder edge so UGR sees vehicles earlier (a plant change, departs from ramp32) |
| D14 | OR strength | tune {OR-basic, OR-wide} × H_req per level | a stronger oracle makes a KILL more credible | +90 tuning runs; still a heuristic | OR-basic only (weaker oracle, more likely false KILL) |
| D15 | `left` action for ALKS | keep it, subject to a check of the UN R157 text (as amended) on whether ALKS lane changes are within scope [VERIFY; I recall a later amendment added lane changes, not confirmed] | richer action set for OR and RL | regulatory scope unconfirmed | slow-only for ALKS (safe for scope, but removes OR's cheaper action) |
| D16 | Seeds | demand 7,431,110-189 (110-129 C, 130-139 T, 140-159 E, 160-169 V, 170-189 UNCLEAR); twins 7,436,110-129; designate 7,436,000-999 as SUMO-seed-only in the same V-decision | contiguous, not found in docs, code, run names or run JSON contents | none known | E1's unassigned 7,430,280-399 (inside the tuning part of the block) |
| D17 | Machine budget | accept about 90-470 process-h (3-18 h wall) unconditional | per-level tuning of every rival, as CLAUDE.md requires | the high end is about a day of machine | UGR tuned on 5 seeds per point (halves the largest item, noisier choice); tuning at L2 only (weak rivals at L1 and L3, against "no weak baselines") |
| D18 | Assumptions | approve A1-A23 (§12) or change them before stage S | | | |

## 14. Changes from review

The review's verdict counts 18 majors; its issue list has 17. All 33 listed issues are answered below.

| Issue | Status |
|---|---|
| Blocker: R-rand parameters do not exist at L1, L3 | fixed: OR (6 points) tuned per level on stage T seeds; R-rand fitted per level from OR\* stage T runs, including onset positions and the `left` share (§4.7) |
| C3 undefined when NC median is 0 | fixed: 5-min floor, McNemar onset fallback against the NCμ null; any zero-median cell is untestable (§5) |
| T0b, T0c without nulls | fixed: shadow observer in stage C NC runs; thresholds = shadow p95 + margin (§4.9, §7.1) |
| NC′ null not like-for-like | fixed: NCμ micro-perturbation null for θ; NC′ reported alongside; conservative max as D8 alternative (§4.2, §7.3) |
| MA detector counts edge boundaries | fixed: edge-aware road-lane mapping; exact-equality smoke criterion per (edge, from, to) (§5, §9) |
| Conflicts displaced to CZ | fixed: S1 (TTC exposure in CZ ∪ MA) is a gate outcome; conflict lane changes in CZ ∪ MA are a guard (§5, §8.2) |
| C1 coupled to OR (PET_m) | fixed: TTC-only gate criterion; PET_m report-only; C1 split commanded / other; S1 added (§5) |
| No degenerate rival | fixed: CC arm tuned per level; item 4 requires OR\* to beat CC\* and R-rand; smoothness screened against CC\* (§4.6, §8.2) |
| KILL on wrong metric, deviation unnamed | fixed: both deviations named in §1 and put to the author as D7 |
| Non-GO exits end in STOP | fixed: OR50 fallback then KILL; flagged cells count as not meeting §8.1; STOP only for code faults (§7.1, §8.3) |
| T0 on stage E data | fixed: T0 on stage T runs; stage E only after T0 passes (§6, §7.1) |
| Bonferroni misses the two-arm factor | fixed: × 18, 99.72 % (§6.2); hierarchical option in D10 |
| Guard intervals unnamed, low power | fixed: unadjusted 95 %; informativeness rule on stage C blocks GO (§6.2, §7.3) |
| Rivals tuned at L2 only | fixed: UGR, OR, CC tuned per level; costed (§6, §10) |
| UGR D_trig has no effect | fixed: replaced by W {1, 2, 4} s; distinct-command smoke check; feeder-edge option in D13 |
| OR treated as an upper bound | fixed: KILL wording and §1, §8.3, §11 drop the inference about RL; OR-wide added (D14) |
| C2 may be an artefact | fixed: C2 report-only; A1, A3 flags two-sided; invalid-NC pairs dropped symmetrically (§5, §6.2, §7.2) |
| Smoke ±5 % inflow fails from noise | fixed: exact insertion vs route file, and route-file counts in the Poisson 99.9 % interval (§9) |
| Yielder keep-right and `left` expiry | fixed: laneChangeMode 1536 [VERIFY bits], held to release; T0e containment (§4.5) |
| Near-side ban targets wrong lane | fixed: defined per edge (§4.5) |
| Window key gameable | fixed: scheduled departure; C1 denominator defined (§2.2, §5) |
| UNCLEAR re-test inflates error | fixed: extension seeds tested alone at the full level (§8.3) |
| Run count and cost | fixed: recounted with the new arms (1,534 m32 runs); L3 budgeted at up to 11,400 sim-s; 0.04-0.15 range (§10) |
| §11 mixed units | fixed: process-h vs process-h at the same step (§11) |
| Ladder may not reach breakdown | fixed: pre-registered 1.10-1.25 extension (§6.1) |
| Repo mismatches (C3 rule, D9, H) | fixed: exact breakdown rule from `day.breakdowns`, warm-up handling; D9 marked proposed; renamed G_OR (§3, §5, §8.3) |
| Sham issues lane-change calls | fixed: getters and no-op setMaxSpeed only (§4.8) |
| Cooperation rung missing | fixed: excluded with reason (#17502, #18249, lcCooperative already 1), in D5 (§3) |
| T0a tautological, ACC condition | fixed: "leader not slower than the cap"; kept as implementation check only (§7.1) |
| R157 scope of `left` | not fixed in the text (needs the regulation): put to the author as D15 [VERIFY] |
| OR projection and ramp ALKS | fixed: full route-file schedule; ramp-origin ALKS excluded (§4.5) |
| CG failure under teleport off; v199 row noise | fixed: failure modes restated (§4.3); NCμ added to the v199 row (+10 runs) |
| Seed check incomplete | fixed: JSON contents grepped, 0 hits; 7,436,000-999 designation in D16 (§6) |
