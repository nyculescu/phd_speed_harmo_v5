# B bind check, core gate (slim draft per V248(4))

Status: DRAFT, 2026-11-01, not approved; no run before the author approves it under a V number. Reference: `docs/research/protocols/drafts/bind_B_v1.md` (full v1), `docs/research/prior_art_B_v0.md`. [A#] = Claude's assumption, needs the author; [VERIFY] = not confirmed by a source read in full.

## 1. Question and scope

Can informed cooperative gap creation by mainline CAVs, with speed caps only (no lane-change commands, no ramp signal), reduce merge conflicts compared with no control (NC)? A KILL means "this informed planner and the tuned rule, with speed caps only, found no effect on m32"; it says nothing about CAV lane changes (half of V246's B) or RL with a richer action set (V242 caveat). Out of scope: RL, mechanism attribution (a constant-cap rival and an untargeted placebo, v1 §4.6-4.7, come only after a GO), the lane drop (track A), crashes, weather.
Deviations from CLAUDE.md, to record as a V-decision with D2: the 10 % early-KILL bar applies to E_MA, not to door-to-door delay (V74, V246: delay is a guard); a per-share demand-level axis replaces "the realistic demand level" (V245); of V74's co-primaries only TTC exposure gates, smoothness is report-only and hard braking is a guard.

## 2. Plant: m32 (kept from v1)

- ramp32 without the 3 → 2 drop (edges 4, 5 keep 3 lanes), meter TLS `rm` held green in every arm (same junction logic as v199 NC), v199 human drivers (`fleet.PLANTS["v199"]`, action steps as V187, held fixed in every check), teleporting off (V197), 0.1-s step, dry, no crash process. The 300-m acceleration lane 3a_0 still ends (`merge: laneend`), so the merge is the only bottleneck.
- Why: on v199 the drop is the active bottleneck on 20/20 days and its queue spills over the merge (V244); prior art finds gap-creation benefits from free flow to near breakdown, not in standing queues (prior_art_B §3.3, Scarinci 2017 full text).
- Constant Poisson demand Q (total), ramp share 15 % (V190, [VERIFY]); 600 s warm-up, 3,600 s window, then drain (cap 7,200 s). A vehicle belongs to the window by its scheduled departure, so delaying it cannot move it out.
- Areas: MA = last 100 m of edge 2 + all of 3a + first 300 m of edge 3; CZ = 1,500 m upstream of the 3a start [A1]. Merge lanes = road lane 0 (2_0, 3a_1, 3_0) and 3a_0; other lanes = 2_1-2, 3a_2-3, 3_1-2 [VERIFY ids on the m32 build].
- SUMO 1.27.1 IDM issues (v1 §3): #17483 (IDM lane-change deadlock, fixed only in Git Main), #17502 and #18249 (fixed in 1.28.0) [VERIFY]. At 50-80 % ALKS most mergers meet IDM followers at a lane end, the #17483 setting; V249 shows lane-end IDM discharge at 1,276-1,319 veh/h with wide spread. Handled by the stage-C drain rule (§4) and the standing guards (§9).

## 3. Shared CAV contract (V248(3); bind_A_core.md must cite this block verbatim)

- vType: the E1 ALKS as run under `fleet.apply_plant("v199")`: carFollowModel IDM (`PLANTS["v199"]["cav_models"]` overrides the ACC default in `fleet.CAV_MODELS`; read in code 2026-11-01), tau 1.6 s (`fleet.ALKS_TAU`), other parameters as E1.
- Actuator: only `control.command(cap, v, own_max, dt=<run step>)`, step passed explicitly (B 0.1 s; A's BN4 step differs); V226 exact restore (own maxSpeed back; allowed speed = min(own maxSpeed, desired)). No `changeLane`, `openGap` or `setSpeed`. Counters `cap_violations`, `restore_mismatch`, `allowed_mismatch` and a new `lcmode_restore_mismatch` must be 0.
- Lane-change mode: allowed only as a lock on a capped vehicle, laneChangeMode 1537 (strategic changes stay on; cooperative, speed-gain, keep-right off; bits 8-9 = 2, bits 10-11 = 1; [VERIFY the bit layout in the SUMO 1.27.1 TraCI docs before stage S]), set with the cap and restored to the vehicle's prior mode at release.
- Share axis s ∈ {25, 50, 80} % ALKS of all vehicles; trucks 7.5 %, the rest human cars; no uncommanded ACC/CACC, so "CAV share" means the same in A and B [A3]. Class labels from a separate RNG stream, so departures and lanes match across shares. A null at 25 % alone is never a KILL.
- B commands only mainline-origin ALKS; ramp-origin vehicles never, also after merging. Levels are calibrated per share (§4), since CAV gaps change capacity (V189).

## 4. Demand levels and step check (rules fixed now)

- Stage C0, step check (V248(1), V249), before the ladder, per share, 10 throw-away seeds at 1.10 × B0 (if fewer than 9/10 NC runs break down, at 1.25 × B0): NC at 0.1 s, NC at 0.05 s, NCμ at 0.1 s. Lattice criteria per run while queued: 30-s counts on 3_0 and the 3a_0 → 3a_1 merge count per 30 s each take ≥ 4 distinct values with no value in > 50 % of intervals; no single inter-merge time (0.1-s resolution) holds > 20 % of merges [A2]. Step criterion: |paired median QDF ratio (0.05/0.1) − 1| ≤ max(2 %, p95 of |QDF ratio NCμ/NC − 1| by bootstrap) [A2].
- C0 result, fixed now: pass → stages at 0.1 s. Fail at 0.1 s while 0.05 s meets the lattice criteria → every stage runs at 0.05 s, re-costed, author told. 0.05 s also fails → m32 is step-sensitive: B STOP for the author.
- Base B0 = 3 × 1,602 veh/h, the V189 full-mix pre-queue flow per lane, used as the ladder centre only [A4]. Ladder: Q = {0.60, 0.65, …, 1.10} × B0, 10 throw-away seeds per level and share, NC only. Outcome per run: ≥ 1 in-window merge breakdown onset (`day.breakdowns` on `merge_up`, field 5: speed < 0.5 × LIMIT on 4 consecutive 30-s readings).
- Levels from a logistic fit of onset on Q (stochastic-capacity idea, Brilon et al. [VERIFY]): L1 = Q at P(onset) = 0.1, L2 = Q at P = 0.3 [A5] (off the bimodal P = 0.5 point), rounded to 10 veh/h. Fit fails (perfect separation, non-monotone) → linear interpolation of the empirical P between adjacent levels.
- Extension: P < 0.3 at 1.10 → levels 1.15-1.30; P ≥ 0.1 at 0.60 → 0.40-0.55. No 0.3 crossing after it → share UNTESTABLE, before any control run.
- Drain rule (#17483): per share, count NC undrained runs and standing pairs (alongside > 120 s). More than 1 of 10 NC runs undrained at a ladder level next to L1 or L2 → share UNTESTABLE, before any control run.
- Report-only: merge pre-queue flow (10-min mean before each onset; new mean-based estimator, since `day.breakdowns` returns the max, V244) and QDF (mean from onset + 5 min to recovery) per lane, against V189's 1,602 / 1,487.

## 5. Primary outcome: merge-lane low-TTC exposure per vehicle (chosen)

- E_MA = vehicle-seconds with same-lane rear TTC < 1.5 s (closing only) while a window-vehicle follower is on a merge lane inside MA, divided by the window vehicles that enter a merge lane in MA. Sampled every whole second with the `day.py` method (getLeader; TTC = (gap + follower minGap) / closing speed). Lower is better. Lanes 1-2 exposure (E_MA12) and E_CZ are guards, so conflicts moved to other lanes are caught.
- Why: V74's safety measure; catches compression behind a slowed yielder and cut-ins by gap thieves; a conflict-lane-change test (gap ≥ v·TTC) is nearly OR's own acceptance test (Goodhart); continuous, so fewer zero-median cells; existing code.
- V211 lateral/junction gap: restricted for the primary (E_MA uses no collision events), handled by replay for the guard. Each SUMO collision event is classified by the V209 replay and `day._bumper`: (a) physical contact, or no same-lane distance that the replay cannot clear → that arm's run is a failure (worst-value rule, §9) and the batch pauses for the author to confirm the class; in NC the pair is dropped and counts toward the A14 limit; (b) minGap intrusion only, in NC → pair kept; (c) intrusion only, in an arm → intrusion guard: per cell, X_arm ~ Bin(X_arm + X_NC, 0.5), one-sided p < 0.05 fails the guard (V213 Q8).
- Report-only: E_MA split into merge-linked seconds (leader a ramp vehicle that changed lane within 3 s) and others; conflict lane changes in MA; stolen, accepted and infeasible slots; onsets; ramp stuck > 60 s; smoothness (speed SD in MA).

## 6. Arms (4) and instrumentation

- **NC:** SUMO defaults (LC2013, lcCooperative 1), meter green, no commands.
- **NCμ (null, V244):** NC with the same seeds; at t = 600 s the first ALKS on edge 1 within 1 m/s of its maxSpeed gets a cap 0.5 km/h lower for 1 s [A6]. Divergence check (stage C): NCμ and NC MA entry times differ by > 1 s for ≥ 80 % of window vehicles; else the perturbation repeats every 300 s on the first eligible ALKS; the spread is reported.
- **UGR (tuned rule):** every 1 s, for each ramp vehicle j on `r`/`rj`, ETA_j = distance to the 3a start / max(v_j, 5 m/s). A mainline-origin ALKS i on 2_0 or 1_0, 100-1,500 m before the 3a start, not yielding, with ETA_i = d_i / max(v_i, 5 m/s) and |ETA_i − ETA_j| ≤ W yields for j (one yielder per j, one j per yielder): cap c = max(v_i − Δv, 0.5 v_i, 5 m/s) via `command`, no trigger if c ≥ v_i; lane lock (§3). Release when j is on road lane 0 ahead of i, i passes the 3a end, or 30 s. Grid: Δv {5, 10, 15} km/h × W {1, 2, 4} s [A7] = 9 points.
- **OR (perfect-information gap creator):** knows every vehicle's state, the route-file schedule and current LC2013 change wishes, not future LC2013 decisions or driver noise (an informed heuristic, not an upper bound; the wishes are kept out of any later RL observation). Every 1 s, horizon 120 s, ramp vehicles in arrival order:
  1. t_j = time j reaches the 3a start (current speed, accelerating at 1.0 m/s² to its allowed speed [A8]); merge window 30-250 m along 3a_0.
  2. Project road-lane-0 vehicles (1_0, 2_0, 3a_1, scheduled insertions included) at constant speed plus committed caps. A slot is a consecutive pair (L, F) whose gap passes j's window. s_req = len_j + minGap_j + v_F × H_req. A natural slot ≥ s_req is logged, no command.
  3. Candidates: F a mainline-origin ALKS more than 30 m before the 3a end; Δs = s_req − predicted gap; cap offset δ = aT − √(a²T² − 2aΔs), a = 1.5 m/s², T = time to the merge; feasible if δ ≤ 30 km/h and v_F − δ ≥ 0.5 v_F [A9]. An ALKS F2 within 2 s behind F gets the same profile.
  4. Theft filter: reject a slot if a non-commanded vehicle in road lane 1 within ±s_req shows a right-change wish (`getLaneChangeState(v, -1)`, [VERIFY bits in 1.27.1]); take the next feasible slot.
  5. Least cost Δs × (1 + vehicles within 2 s behind F) [A10]; none feasible → log "infeasible".
  6. Execute through `command` each step; lock F and F2 (§3); ALKS in road lane 1 within ±s_req of an active slot get the same lock. Theft re-plan: a vehicle other than j entering the slot becomes L, Δs is recomputed and the cap extended within the limits, else released. Release when j is on road lane 0 ahead of F, t_j + 3 s after the planned merge, F leaves 3a, or 30 s; exact restore of speed and mode.
  - Tuning: H_req {2.0, 2.5, 3.0} s [A11] = 3 points.
- **Shadows and sham (not arms):** in the stage-C NC runs, the OR shadow (OR's planner with getters only, logging plans at all 3 H_req) and the UGR shadow (UGR's trigger with getters only, logging (i, j, trigger time) at all 9 points) run together; T0 uses the points tuned later. Sham = OR with no-op commands. Both hashes must equal NC.

## 7. Stages, seeds, runs

Seeds proposed, author approval needed (D5): demand seed = SUMO seed, from the V135 block after V206-V207's 7,431,000-109. 7,431,110-190 was not found in `docs/`, `v5b/`, `tests/`, run file names or any `*.json` under `/home/catalin/work/phd` (grep 2026-11-01; the same grep finds 7,431,0xx); track A's v1 uses 7,432,xxx.

| Stage | Seeds | Content | Runs |
|---|---|---|---|
| S smoke | 7,431,110 | per share: NC, NC 0.05 s, NC + shadows, NCμ, sham, UGR, OR | 21 |
| C0 step check | 7,431,111-120 | per share: NC 0.05 s, NCμ (NC 0.1 s is the ladder's 1.10 level) | 60 (+ ≤ 60 at 1.25) |
| C ladder (throw-away, disclosed) | 7,431,111-120 | 11 levels × 10 × 3 shares, NC | 330 (+ ≤ 120 extension) |
| C nulls | 7,431,121-140 | per share × level: NC + shadows 20, NCμ 20 | 240 |
| T tuning | 7,431,141-150 | per share × level: NC 10, UGR 90, OR 30 | 780 |
| E evaluation | 7,431,151-170 | per share × level: NC, NCμ, UGR\*, OR\* × 20; sham 2 seeds × 6 cells; T3 reruns 12 | 504 |
| UNCLEAR extension | 7,431,171-190 | one cell per share: NC, OR\* × 20 | ≤ 120 |

## 8. Tool checks and nulls (fixed now)

- T0a (implementation, every arm): the §3 counters 0, every command within the taper, lock set and restored. Fail → STOP, fix, re-run all affected, log both.
- T0 for OR\* (stage T, per share): T0b median (realised gap − predicted no-command gap) / planned Δs exceeds the OR-shadow bootstrap p95 by ≥ 0.25; T0c share of commanded slots that j enters ahead of F exceeds the shadow rate's p95 by ≥ 10 pp [A12].
- T0 for UGR\*: T0b-UGR median (realised gap ahead of i at j's merge − UGR-shadow gap for the same (i, j)) / Δs_UGR exceeds the UGR-shadow p95 by ≥ 0.25, with Δs_UGR = Δv × hold − Δv²/(2 A_CAP), hold = time to release; T0c as above against the UGR shadow (j enters ahead of i) [A12].
- An arm failing T0b or T0c at a share is "non-binding" there.
- θ (V244, like-for-like): per share × level, θ = p95 of |relative paired median change| of E_MA on NCμ vs NC (20 pairs, 100,000 resamples, the gate's estimator). τ = max(10 %, θ). θ > 30 % or NC calibration median E_MA = 0 [A13] → cell out of the gate before stage E.
- Guard informativeness: if NCμ's p97.5 of a guard's relative change exceeds +20 % [A13], that guard blocks GO in that cell.
- T3: sham hash = NC; reruns of UGR\* and OR\* on 2 seeds reproduce their hashes. Mismatch → STOP.

## 9. Decision rules (fixed now)

- Statistics: paired seeds, median of paired differences, relative = median(diff) / median(NC), 95 % percentile bootstrap, 100,000 resamples. Gate family 2 arms × 2 levels × 3 shares = 12, Bonferroni → 99.58 % intervals. Guards use unadjusted 95 %.
- Cell effect (arm X ∈ {UGR\*, OR\*}, share s, level L): T0 passed; E_MA reduction ≥ τ; 99.58 % CI excludes 0; guards hold:
  - no class-(a) event, intrusion guard passes (§5); an undrained or failed arm run takes the worst value of that arm over the cell's seeds or of all arms, whichever is worse; an undrained NC run drops the pair, > 2 of 20 → cell out [A14];
  - door-to-door delay of all vehicles, including insertion and ramp waits: CI lower bound of the relative increase ≤ +2 % (V37); served throughput (window vehicles out by window end + 900 s): CI lower bound of the loss ≤ 2 %;
  - E_MA12, E_CZ and hard braking (vehicle-seconds ≥ 3.0 m/s² in CZ ∪ MA): median increase ≤ +5 % and CI lower bound ≤ +5 % [A15];
  - self-blocking (v1 A2): a yielder below 2 m/s for > 10 s while its target has not merged, more than 1 per 100 commands → no GO in that cell;
  - vehicles standing > 300 s not different from NC (two-sided 95 % CI), so a deadlock workaround cannot win.
- Share state, in this order: **UNTESTABLE(s)** (§4 no crossing or drain rule); **UNINFORMATIVE(s)** if the L2 cell is out (§8) and L1 is not GO; **GO(s)** if any remaining cell meets the cell effect; **NON-BINDING(s)** if both arms fail T0 at s; **UNCLEAR(s)** if the best OR\* cell has a reduction ≥ τ but its CI includes 0: one extension (20 fresh seeds, NC and OR\*, that cell only, alone at 99.58 %), pass → GO(s), else NO-EFFECT(s); else **NO-EFFECT(s)**.

| Condition (checked top to bottom) | Verdict |
|---|---|
| any share GO (25 % included) | GO; passing shares reported (80 % only = "high penetration only") |
| no GO; 50 % or 80 % UNINFORMATIVE | INCONCLUSIVE (no KILL) |
| no GO; 50 % and 80 % both UNTESTABLE | INCONCLUSIVE: merge not critical or not drainable at high shares |
| no GO; 50 % and 80 % each NO-EFFECT, NON-BINDING or UNTESTABLE, at least one NO-EFFECT or NON-BINDING | KILL B (speed caps only) on m32 |

- 25 % states other than GO never change the verdict. Stop for the author after any verdict.
- Report-only: G_OR = (OR\* − UGR\*) / NC per cell; TTT (fixed window, unfinished vehicles to window end); mainline and ramp delay; §5 report-only rows.
- Tuning (stage T, per share × level): minimise the median relative change of E_MA vs NC, subject to point estimates delay ≤ +2 %, no class-(a) event, E_CZ and E_MA12 not above NC. Ties within 1 pp: smaller Δv or H_req. No point passes: the NC-closest point (smallest |Δ delay|), disclosed.

## 10. Smoke (V231), before every batch

One short run per distinct arm, grid family, step and share (§7 row S); the launch script stops on any failure. Checks: each output echoes arm, parameters, share, Q, seed, plant id, step; inserted vehicles = route-file departures; realised class shares and route counts inside the Poisson 99.9 % interval; command log non-empty for UGR and OR, empty for NC and sham, one entry for NCμ; sham and shadow hashes = NC, NCμ hash ≠ NC; distinct command sets across grid points; laneChangeMode read back as 1537 while locked and the prior mode after release; §3 counters 0; drained; no class-(a) event; `wall_s` recorded. Batches launch from a frozen detached worktree, under the CPU guard and the v6-idle check, ≤ 27 workers, one simulation per process.

## 11. Machine hours and build

About 1,935 unconditional runs (+ ≤ 300 conditional), about 4,800 sim-s each. At 0.04-0.15 wall-s per sim-s (v1 [A1], unmeasured for m32 at 80 % ALKS; 0.05-s runs about 2×) that is about **105-390 process-h, 4-15 h wall at 27 workers**; the smoke `wall_s` replaces the range before stage C0. If C0 moves every stage to 0.05 s, about double. Not included: CPU-rule pauses, build and test time (m32 net, share mixes, constant demand, merge-lane exposure, UGR, OR, both shadows, NCμ, sham, `lcmode_restore_mismatch`, the C0 lattice statistics, the mean-based pre-queue estimator, analysis).

## 12. Author decisions (≤ 5)

| # | Decision | Recommended | Pros | Cons | Inferior alternatives (why) |
|---|---|---|---|---|---|
| D1 | Plant, levels, step check | m32 as §2; C0 step check with fixed outcomes; per-share ladder centred on 3 × 1,602; L1/L2 at P(onset) 0.1/0.3; drain rule for #17483 | isolates the merge; checks the V249 lattice per lane before the ladder; avoids the bimodal point | new geometry; 0.05 s may double cost | v199 meter-green PM (drop queue covers the merge); L2 = Q50 (bimodal, likely uninformative) |
| D2 | Primary outcome and deviations | E_MA on merge lanes (§5); E_MA12, E_CZ, hard braking as guards; the §1 deviations recorded as a V-decision; V211 by restriction plus replay classes | V74 measure without lanes-1-2 dilution; displaced conflicts still guarded; post-event rule fixed | smoothness and hard braking leave the co-primary | all-lane E_MA (dilution biases toward KILL); conflict lane changes (Goodhart with H_req, sparse); fixing the lateral classifier (build work the gate does not need) |
| D3 | CAV contract, shares, verdict | §3 block, adopted verbatim by A before either core draft is approved; ALKS 25/50/80 %, rest human; speed caps only (V248(3) read as excluding lane-change commands); §9 verdict table | one CAV meaning in A and B; complete verdict table | B's lane-change half untested; A's draft still names the model [VERIFY] and must change | v199 ratios for the remainder (ACC/CACC fall from 25 % to 4.6 %, two meanings of share); a report-only `left` OR variant (more build, no gate weight) |
| D4 | Gap protection | inside OR, CAV-only: lock 1537, lane-1 ALKS lock, theft filter, re-plan, F2 platoon cap | follows prior art without touching humans | HDV thieves not blockable at 25 %; [VERIFY] LC bits | near-side ban for all vehicles (an infrastructure actuator outside the contract); no protection (gaps stolen, an uninformative KILL) |
| D5 | Seeds and budget | 7,431,110-190 as §7; about 105-390 process-h | contiguous, unused, no overlap with A | at n = 20 a 99.58 % CI excludes 0 only when about 16-17 of 20 paired differences share the sign (Claude's sign-test estimate) | UGR tuned on 5 seeds (noisier rival); tuning at L2 only (weak rival at L1) |

Assumptions approved with their decision: D1: A1 CZ 1,500 m, A2 C0 lattice and step thresholds, A4 B0 as centre, A5 P 0.1/0.3, ramp share 15 % (V190). D2: A13 30 % and +20 % caps, A14 invalid-NC rule, A15 guard margin +5 %. D3: A3 share mix, A6 NCμ perturbation, A7 UGR grid, A12 T0 margins. D4: A8 ramp projection, A9 δ limits, A10 OR cost, A11 H_req grid. D5: seed range.

Review changes: verdict table with UNTESTABLE/UNINFORMATIVE/INCONCLUSIVE states; UGR shadow and T0; fixed collision classes; CLAUDE.md deviations named; one §3 contract block for A and B (IDM per PLANTS v199, human remainder, lock 1537 with restore counter).
C0 step check moved before the ladder with per-lane lattice tests, a null-set threshold and fixed outcomes; L1/L2 at P 0.1/0.3 with a fit fallback; UGR speed floor and self-blocking guard; #17483 drain rule.
E_MA on merge lanes only with E_MA12 guard; speed-caps-only KILL wording; NCμ divergence check; worst-value wording; OR information set; NC-median-0 rule; power note; smoke, sham and lock read-back counted; assumptions mapped to D1-D5.
