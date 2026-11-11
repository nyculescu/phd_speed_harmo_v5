# EV: does knowing about an event in advance help a rule? (early KILL for the "recovery after an event" direction)

Status: **DRAFT v0, not approved.** Rules only, no DRL training, no claim. The outcome is HEADROOM, KILL, NOT SHOWN or VOID. Approval: V505 (the step), with the open decisions in §0 of this file and of `v505_m2_merge_check.md` (D5 budget, D6 branch).

## 0. Decisions for the author

| # | Decision | Recommendation | Why | Weaker alternative and why |
|---|---|---|---|---|
| E1 | The two events | EV-A, an upstream slowdown; EV-B, one slow vehicle (§2) | Both happen on real roads. Both exist in code with small changes. Neither is X1, X2, TRUCK or the training draw. EV-A sits upstream of merge 1, away from the merge-2 lane end. | A ramp-2 demand surge: SURGE failed the drain test (V487). A short lane blockage: excluded (planb.md:308-320), because with teleport off a stranded vehicle blocks the lane until the run ends. |
| E2 | The informed rule's lever | Headway only, the same 0.8-1.6 s levels v3w uses | The test must bound what an adaptive headway policy could gain. A wider lever would test a different controller. | Add speed caps: a different actuator, outside v3w's action and outside PR-10's checked range. |
| E3 | The deciding size | 10 % of the best uninformed rule's event cost | D2's headroom bar (screen_D2_incidents.md:58) and Plan B's G2-loss size; Fable's hint was about 5 %, which this design could not separate from noise in the event cost. | 5 %: closer to the hint, but in delay terms about 1 % of total, where Plan B's ties already sit. |

## 1. Question

On two new events fixed in advance, does a rule that is **told** where and when the event comes beat the best rule that is **not told**, on delay in the event cell?
- The told rule is the upper limit of what this headway lever can gain from knowing the event. A DRL policy is never told; it can only infer the event from its inputs.
- **If being told does not help (KILL),** the "recovery after an event" direction stops on this plant and this lever before any training.
- **If it helps (HEADROOM),** a Plan 1 protocol may be written: DRL trained on an event family, against the same opponents re-tuned on that family.

Prior evidence, both directions: on r1m3 P0 a told headway rule helped close-following and not delay (V347), and a local rule that detects slow traffic matched it (V351). On BN4 with mainline metering, per-incident information helped in 1 of 4 cells (V101, V102). Neither ran on plant_c3.

## 2. Events (fixed now, before any control result on them)

| Event | Definition | Timing per seed | Real-road meaning |
|---|---|---|---|
| EV-A | speed limit on edge 2 (498 m, upstream of merge 1) to 40 km/h, tapered over 20 s as X1 | onset U(600, 1,000) s, duration U(180, 360) s, from `default_rng(seed + 505_001)` | an incident or rubbernecking zone, or a temporary limit |
| EV-B | one vehicle on route `main`, lane 0, capped at 30 km/h for its whole trip | departure U(600, 900) s, from `default_rng(seed + 505_002)` | a slow vehicle: oversize load, farm vehicle, broken-down truck limping on |

- Both differ from X1 and X2 in edge set, limit and duration, and from the training draw (edges 3-5, 25-60 km/h) by edge (EV-A) or kind (EV-B).
- The same event is drawn for every arm on a seed, before any control acts. The timing is logged in the row.
- **Gate, on seeds 7,488,340-359 with no control and p333:**
  - delay in the cell is at least 10 % above S, with the CI lower bound above 0 (G1a);
  - the drain test of V486 passes, and `m_stuck_n` is 0.
  - An event that fails is dropped, not re-parameterised. If both fail, EV is VOID: nothing is closed, and any new event set is a new study.

## 3. Arms

Per event, each family is picked by median `all_delay` on the tuning seeds 7,488,360-399, then frozen before the evaluation seeds.

| Arm | Told? | Family | Size |
|---|---|---|---|
| NC | no | no control (shown, never deciding) | 1 |
| N | no | p333, the steady delay-best rule | 1 |
| FX | no | the best stored rule in this event cell: the 11 carried rules, the 5 grid re-picks, 3e, 3ex1, 3ex2, 3E-C_TRUCK and 3E-D_TRUCK (BASELINE v5 list; `copy` and MPC-F are left out, as a policy-derived rule and a model fitted to TRUCK) | 21 |
| SW | no | the best rule that **detects** the event: LocalRule (r ∈ {400, 1,000, 2,000} m, threshold ∈ {10, 13, 16} m/s, level ∈ {1.6, 1.2, 1.0} s) and ASCH's Plan B grid | 27 + 18 |
| IP | yes | from the FX pick, switch ALKS within d m upstream of the event to level L, from d/25 s before the event reaches them until `after` s past its end; d ∈ {500, 1,000, 2,000} m, L ∈ {1.6, 1.2, 1.0} s, after ∈ {0, 60, 180} s, plus "no switch" | 28 |

- IP includes "no switch", so its pick on the tuning seeds is at least as good as FX there.
- For EV-B the zone moves with the slow vehicle (its live position from libsumo).
- IP reads the event schedule, which no real controller has. It is an upper limit and never an opponent in any later claim.
- **Code needed:** the existing `hw_oracle` cannot be used. It is anchored to r1m3's edge 4 (`EDGE4_X` 4,989.02 m, perturb.py:36), and `ROAD_X` has no "4a" (b_env.py:74), so on r2m3 it skips merge 2 and sits about 293 m short. IP needs a new class with r2m3 offsets (`_x_base`) and the event's own position, applied through `_hw_level` (it bypasses the 10-s hold, not `tau_rise`), and checked by T0.

## 4. Measures

- **Deciding:** `all_delay` in the event cell (veh-s, including insertion queues), paired by seed.
- **Event cost**, for the threshold and the report: each arm's `all_delay` in the cell minus its own `all_delay` in S on the same seed. In S, IP equals its FX base.
- **Report-only:** close-following, hard braking (`b45_net`), flow, collisions; delay by road and period; `end_stop2`; the time after the event's end until edge speeds at the event and at merge 2 are back above 60 km/h for 2 minutes.

## 5. Reading (fixed now)

For each event that passed the gate, and for each uninformed arm U in {N, FX, SW}, H(U) = median over seeds of (delay_U − delay_IP) in the event cell, divided by the median event cost of U. CIs are percentile bootstrap, B = 20,000, at 98.75 % two-sided (Bonferroni over 2 events).
- **HEADROOM:** in at least one event, H(U) ≥ 10 % with the CI lower bound above 0 against every U; IP's flow is at most 0.5 % lower by point; IP's collisions are at most U's + 0.05 per run.
- **KILL:** in every event that passed the gate, the CI upper bound of H against the best U is below 10 %.
- **NOT SHOWN:** otherwise. It closes nothing and allows no protocol.
- **Location:** for a HEADROOM event, the share of the delay difference that sits on road 4a, ramp 2 and the ramp-2 insertion queue is reported. If it is above 50 %, the result is labelled "lane-end-bound" and the deciding comparison must be repeated on M2's variant plant on the same evaluation seeds before Plan 1 may be written. It must hold there with the same rule.
- **Null:** before the reading, a label-swap null of IP against N must give a lower bound above 0 in at most 1.5 times the nominal share.
- **T4-style report:** whether the per-seed best IP setting differs from "no switch" on more than half the seeds.
- **Consequences, fixed now:**
  - KILL: the recovery direction (Plan 1 of `drl_aim_plans_v0.md`) closes for the headway lever on this plant. Plan 2 is not affected.
  - HEADROOM: a Plan 1 protocol may be written. Its events are new, chosen before data, and its opponents include SW and FX re-tuned on the training event family.
  - Cells-tested count: unchanged, because no DRL policy runs (planb.md:145). Each EV event is labelled post hoc (planb.md:576).

## 6. Seeds, runs and cost

| Seeds | Use |
|---|---|
| 7,488,300-309 | smoke, T0 of IP and of both events, determinism |
| 7,488,310-339 | reserved: repeats after a code fix |
| 7,488,340-359 | event gate |
| 7,488,360-399 | tuning (picks of FX, SW and IP), n = 40 |
| 7,488,400-519 | evaluation, n = 120, used once |
| 7,488,520-599 | reserved |

| Stage | Runs |
|---|---|
| Smoke and T0 | about 60 |
| Gate: 2 events × 2 arms × 20 seeds + S 2 × 20 | 120 |
| Tuning, no pack: (21 + 45 + 28 + 1) arms × 40 seeds × 2 events | 7,600 |
| Evaluation, with the pack: 5 arms × 120 × 2 events, plus S for NC, N and each FX and SW pick | about 1,920 |
| Repeat on M2's variant, only if lane-end-bound | up to 480 |

Cost: about $0.9 for tuning and $0.7 for evaluation, about $1.7 with setup. Machine time about 2.5 h. Build: the two event kinds with per-seed timing, the IP class, the readers with planted-row tests: about 8-10 h.

## 7. Checks before tuning

| Check | Requirement | If it fails |
|---|---|---|
| T0 events | edge-2 speeds fall to 40 km/h ± 5 % inside the window; the slow vehicle holds at most 30 km/h | stop; fix; repeat on 7,488,310-339 |
| T0 IP | inside its window and zone, commanded and read-back headways of ALKS behind an ALKS leader equal L; outside, equal the FX base | stop |
| Determinism | the same run twice is equal | stop |
| Untraced equal | traced and untraced rows are equal (V386) | stop |
| Power (planning) | from S6 TRUCK rows: the share of studies that read HEADROOM at a true H of 0 and of 15 % | stated in the run record; thresholds are not changed after it |

## 8. Disclosures every EV sentence carries

- Exploratory screen, rules only; post hoc events; IP is an upper limit with information no controller has.
- One lever (headway, 0.8-1.6 s); a KILL says nothing about speed, lane or ramp actuators.
- PR-28 open unless M2 closes it; capacity drop not settled (PR-26); synthetic, uncalibrated plant.
