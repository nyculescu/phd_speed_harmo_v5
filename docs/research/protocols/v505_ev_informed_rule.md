# EV: does knowing about an event in advance help a rule? (an early KILL for the "recovery after an event" direction)

Status: **DRAFT v2, not approved.** Rules only, no DRL, no claim. Outcomes: GAIN, KILL, NOT SHOWN or VOID. Approved so far: V505 (the step), V507 (cap about $6). Shared rules, words, seeds and cost: `v505_common.md`.

## 0. Decisions still open

| # | Decision | Recommendation | Pros | Cons | Weaker alternatives |
|---|---|---|---|---|---|
| E1 | Which event | **One event, EV-A:** a slowdown on edge 2 (upstream of merge 1), with its severity sized on no-control runs before it is fixed (§2) | far from the merge-2 lane end; already in code; sized so that it can pass the gate | a KILL speaks for this one event only | Adding EV-B, one slow vehicle on lane 0: it rides past both merges, so its cost is lane-end-loaded, and it needs about 816 s to cross the road, so its effect is cut off at the window end. A lane blockage: excluded, because with teleport off a stranded car blocks the lane to the run's end |
| E2 | The told rule's lever | headway only, at 0.8-1.6 s, set by an **override** inside the zone and window | the same lever v3w uses | on a 0.8-s base it can only lengthen headways (§1) | the existing `hw_oracle` path: it takes the minimum level (b_env.py:735), and on r2m3 it sits about 293 m off and skips 4a. Speed caps: a different actuator |
| E3 | The deciding size | 10 % of the best untold rule's event cost | a size worth a Plan 1 study; 5 % of event cost is about 1 % of total delay, inside Plan B's tie band | a true gain below 10 % can end in KILL; every KILL sentence states the gain it does not exclude | 5 %: closer to the memo's hint, but a wide NOT SHOWN zone at this n. (Screen D2's 10 % bar was of total delay, a different quantity) |

## 1. Question and the expected answer

On one new event fixed in advance, does a rule that is **told** when and where the event happens beat the best rule that is **not told**, on the event's delay cost?
- **What IP is:** the best of a grid of headway switches. It is a lower bound on what being told can give, not an upper limit. It is also V506's "per-type plan" for this one event type, told the timing. A DRL policy is never told; it can only infer the event from its inputs.
- **The expected answer is KILL, and this screen is built to deliver it cheaply.**
  - Every delay-best stored rule holds 0.8 s as its free level. On such a base, the told rule can only lengthen headways near the event.
  - At a capacity-limited slowdown, lengthening lowers throughput, and no delay mechanism for a told gain was identified in advance.
  - On r1m3, told lengthening cost 4.5 % delay (V347).
- **KILL:** the recovery direction is not pursued with the headway lever for this event, before any training. **GAIN:** a Plan 1 protocol may be written.
- **Prior evidence:**
  - a local rule that detects slow traffic matched the told rule on r1m3 (V351);
  - on BN4 with mainline metering, per-incident information helped in 1 of 4 cells (V101, V102);
  - none of these ran on plant_c3.

## 2. The event (EV-A)

- **What it is:** a speed limit L_ev on edge 2 (498 m, upstream of merge 1), tapered over 20 s as in X1. It represents an incident zone or a temporary limit.
- **Timing per seed:** onset drawn from U(450, 800) s, duration from U(240, 420) s, from `default_rng(seed + 505_001)`. The draw is made when the run starts and is written into the perturbation spec. It is the same for every arm on a seed. The end is at most 1,220 s, at least 280 s before the drain window (1,500-1,800 s).
- **Novelty:** it differs from X1 and X2 in edge, limit and duration, and from the training draw by edge (the training draw used edges 3-5).
- **Sizing,** on throw-away seeds 7,488,220-239 (n = 20), **no control only**, disclosed. p333 is run and printed but not used.
  - L_ev from the ladder {30, 20, 15, 10} km/h.
  - Pick the mildest level whose median event cost under no control (cell minus S on the same seed) is at least 15 % of S's median delay, with drain passed and `m_stuck_n` 0.
  - Reason: a 40 km/h limit on a road carrying 3,710 veh/h forms no queue by the review's spacing arithmetic.
  - If no level qualifies, EV is VOID.
- **Gate,** on seeds 7,488,240-279 (n = 40), no control and p333:
  - G1a: delay in the cell at least 10 % above S, CI lower bound above 0;
  - drain as V486 (cell minus S, mean over the 40 seeds, at most 2 vehicles);
  - `m_stuck_n` 0.
  - A failed gate makes EV VOID. The event is not re-sized; any new event is a new study.

## 3. Arms

Picks are made on the tuning seeds 7,488,280-339 (n = 60) and frozen before evaluation.

| Arm | Told? | Definition | Size | Pick by |
|---|---|---|---|---|
| NC | no | no control; printed, never deciding | 1 | none |
| N | no | p333 | 1 | none |
| FX | no | the best stored rule in this cell: the 14 carried rules (p333 among them) and the 5 grid re-picks, with 3E-T, 3E-C_TRUCK and 3E-D_TRUCK among them | about 21 | median `all_delay` (no shared base; the noisiest pick) |
| SW (a) | no | on the FX base: when the mean roadside speed over the next r m is below th, use level L, held for `after` s once the speed recovers. r ∈ {400, 1,000, 2,000} m, th ∈ {10, 13, 16} m/s, L ∈ {1.6, 1.2, 1.0, 0.8} s, after ∈ {0, 60, 180} s | up to 108 | median paired difference against the FX base |
| SW (b) | no | ASCH: steady rule p333; switched rule from {3E-T, 3E-C_TRUCK, 3E-D_TRUCK}; θ ∈ {40, 55, 70} km/h, τ ∈ {10, 30, 60} s, h ∈ {5, 15} km/h; plus never switch | 55 | median paired difference against p333 |
| IP | **yes** | on the FX base: for ALKS within d m upstream of the edge-2 entry, or on edge 2, set the level to L, from d/25 s before onset until `after` s past the end. d ∈ {500, 1,000, 2,000} m, L ∈ {1.6, 1.2, 1.0, 0.8} s, after ∈ {0, 60, 180} s, plus no switch | up to 37 | median paired difference against the FX base |

- **Duplicates dropped:** settings with L equal to the FX pick's level in the zone duplicate FX and are not run (for a 0.8-s base: IP 28, SW (a) 81).
- **Sequence:** FX is picked first; SW (a) and IP are then built on that pick. All picks use the same 60 tuning seeds, and the evaluation seeds are fresh.
- **Best untold arm (bU):** whichever of N, FX and SW (the better of (a) and (b) by median event-cell delay) has the lowest median event-cell delay on the tuning seeds, frozen with the picks.
- **Disclosed exclusions:**
  - MPC-F: its prediction model must be fitted to each cell's dynamics, a fitting stage this screen does not run. The 3E rules are parameter sets used as they are. CLAUDE.md allows dropping the MPC arm if disclosed.
  - `copy`: it is derived from the policies.
- **IP reads the event schedule,** which no real controller has. It is never an opponent in any later claim.

## 4. Measures

- **Deciding:** the event's delay cost, read through `all_delay` in the event cell, paired by seed.
- **Event cost of an arm:** its `all_delay` in the cell minus its own `all_delay` in S on the same seed. In S, IP and SW (a) equal their FX base.
- **Report-only:**
  - common §3's measures;
  - delay by road and period; `end_stop2`;
  - **recovery time:** after the event's end, the time until the 1-minute mean speed on edges 1 and 2 is within 5 km/h of the same arm's S run on that seed. It is censored at 1,800 s, and the censored share is printed.

## 5. Reading (fixed now)

**Informed gain against an untold arm U:** G(U) = median over seeds of (delay_U − delay_IP) in the cell, divided by U's median event cost. The point is the full-sample ratio. Seeds are resampled jointly for the numerator and the denominator. CIs are 95 % two-sided, because one event decides.
- **GAIN:** all of these:
  - G(bU) ≥ 10 % with the lower bound above 0;
  - the lower bound above 0 against N, FX and SW;
  - IP's `passed` at most 0.5 % lower than bU's by point;
  - IP's collisions at most bU's + 0.05 per run;
  - IP's `b45_step` paired mean ratio against bU not failing common §4's braking form (M2 §2).
- **KILL:** the upper bound of G(bU) is below 10 %. The sentence: "being told the time and place of this upstream slowdown, used as zone headway switching, did not cut its delay cost by 10 % against the best untold rule; a gain of up to [UB] % is not excluded."
- **KILL BY PICK:** IP's tuning pick is "no switch", or its rows equal FX's on every tuning seed. The told grid found nothing better than its base. It reads as KILL, with the same sentence plus "by pick". The best switching setting's paired difference and CI on the tuning seeds are printed. The zero-width rule of common §4 does not apply here.
- **NOT SHOWN:** otherwise. It closes nothing.
- **Null:** for IP against each of N, FX and SW, a label-swap null within seed must give a lower bound above 0 in at most 1.5 times the nominal 2.5 %. A comparison that fails reads "statistic failed its null", and GAIN and KILL cannot be read from it.
- **Location:** common §6 applies to GAIN and to KILL.
- **Planned power,** computed after FX's tuning rows and before the rest of tuning. The model is fixed now:
  - one IP setting has a true G of 15 %, and every other setting 0;
  - the setting-to-setting spread is taken as the spread of the FX family's paired differences against the FX pick on the 60 tuning seeds;
  - the event cost and its spread come from the gate rows;
  - the evaluation uses n = 120.
  - If the false-KILL probability is above 10 %, tuning extends to n = 100 (7,488,500-539, all families re-picked). If it is still above 10 %, evaluation extends to n = 160 (7,488,540-579). If it is still above 10 %, a KILL reads "KILL, underpowered (P = x)" and closes nothing.

## 6. Consequences (fixed now)

| Outcome | What changes |
|---|---|
| KILL, KILL BY PICK | the recovery direction (Plan 1 of `drl_aim_plans_v0.md`) is not pursued with the headway lever for this event (EV-A at L_ev on edge 2). Other events, other actuators and Plan 2 are not affected |
| GAIN | a Plan 1 protocol may be written: events fixed before data, DRL trained on an event family, against FX and SW re-tuned on that family |
| NOT SHOWN, VOID, KILL underpowered, unresolved | nothing closes; the outcome is logged |
| Cells tested | unchanged: no DRL policy runs here (planb.md:145). The event is labelled post hoc (planb.md:576) |

## 7. Runs

| Stage | Runs |
|---|---|
| Smoke and T0: every distinct configuration once, plus 3 seeds for the 5 evaluation arms | about 250 |
| Sizing: 4 levels × 2 arms × 20 + S 2 × 20, with the pack | 200 |
| Gate: 2 arms × 40 in the cell and in S, with the pack | 160 |
| Tuning, without the pack: FX about 21 × 60; then IP 28-37, SW (a) 81-108 and SW (b) 55, each × 60 | about 9,700-12,000 |
| Evaluation, with the pack: 5 arms × 120 in the cell; S for NC, N, FX and SW | 1,080 |

Only if triggered: the repeat on V-A (1,080) and the power extensions (common §7). Costs are in common §7.

## 8. Checks before tuning

| Check | Requirement | If it fails |
|---|---|---|
| T0 event | the edge-2 limit read back from libsumo follows the schedule (taper and value) at every 0.1 s; mean edge-2 speed inside the window is at most 1.05 × L_ev | stop; fix; repeat on 7,488,460-499 |
| T0 IP | for ALKS that hold a commanded level (an ALKS leader, the same one as the last second), the commanded level inside zone and window equals L; the read-back headway reaches L within the `tau_rise` time for rises and at once for falls; outside, it equals the FX base | stop |
| T0 SW (a) | the level switches when the detector condition holds and returns `after` s after it clears | stop |
| Determinism; traced equals untraced | as in M2 | stop |

## 9. Disclosures every EV sentence carries

- Exploratory screen, rules only.
- The event is post hoc, and its severity was sized on throw-away no-control runs.
- IP is the best of one told grid: a lower bound on the value of being told, using information no controller has.
- KILL was the expected reading (§1). FX's pick is the noisiest of the three picks.
- One lever: headway at 0.8-1.6 s. One event. No MPC arm.
- PR-28 is open: M2 can at most make it partial. The capacity drop is not settled (PR-26). The plant is synthetic and uncalibrated.
