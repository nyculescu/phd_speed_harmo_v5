# Screen M, protocol-ready draft (angle: strongest opponents, plant validity)

EXPL = exploratory, mine, from stored S6 rows (240 seeds); scripts in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/opp/`. No simulation ran.

## 1. Question; what a pass allows; what a KILL closes
- **Question:** in steady traffic on plant_c3, does a headway rule at merge 2, with values up to 4 s, cut delay by at least 3 % against every delay-tuned incumbent?
- **A pass** allows a merge-study protocol; the passing controller is a rule (K2).
- **A KILL** closes M and P1 for delay on this plant. K0 only bounds P2.

## 2. Approvals and preconditions
Author decisions: (1) a new post hoc study (planb.md:576; V456(3)) with its own cap, rental and seeds; (2) headways above 1.6 s, outside the intended use (plant_vv_record_v0.md:9) and the level set (b_env.py:37), a contract departure as in V273; (3) no simulated no-merge reference (§3).

Plant checks, in order. A failure stops the screen. None prints a delay field.
- **Zero runs:** a second re-derivation of §3; PR-26's drop estimator with a no-drop null (V244) on stored no-control rows. Until then: "capacity drop unknown" (V327).
- **Identity, T3:** stored rows replay bit for bit with the new paths off (planb.md:177).
- **T0 on r2m3** (PR-10: "no r2m3 T0 record") for 1.6, 1.2, 1.0, 0.8, 2.0, 3.0 and 4.0 s. Pass per value: read-back equals the command; the median held time gap of commanded lane-0 CAVs at the start of 4a is at least 0.8 × the target and differs from the next lower value's (95 %). Reported: gate-off seconds, tau reversals, braking at 0.1 s (V367), lane-0 flow and lane changes, ramp vehicles entering in front of a commanded CAV. A failed value is dropped.
- **Lane-end check (PR-28, PR-24), no control and p333:** traced `end_stop2` samples (plant_sweep.py:294) equal the counter on 2 seeds per cell; `stuck_n` = 0; the longest wait reported (V195).

## 3. Stage 0

| Statement (EXPL) | Value | Decides |
|---|---|---|
| Merge excess E under p333 | 9.20 % [8.48, 11.23] of delay; merge 1 1.94 %, merge 2 7.13 % | the ceiling at unchanged flow (matches critic_M F2) |
| E's formula on road pairs with no merge | −1.25 %, −1.65 % | E can fail; it reads 1-2 points low |
| Part tied to merge-2 slow minutes | 15-18 % (an_delay_floor.md:8) | an upper ceiling; an association |
| Stored rules with less delay than p333 (point) | 0 of 22; 3E-D_TRUCK +0.00 [−0.19, +0.00] | p333 is on the delay frontier |
| Rules at 1.0-1.2 s near a merge | −2.1 to −7.5 % (critic_M F3) | closes values inside 0.8-1.6 s |

- E = [D(3a) − r(2)·K(3a)] + [D(4a) − r(3)·K(4a)] + ramp insertion queues. D: delay on a road; r: delay per vehicle-km on the upstream road; K: vehicle-km.
- Decided here, exploratory: values inside 0.8-1.6 s are closed; a ceiling above 5 % exists at merge 2 only, where PR-28 is open. Arms act at merge 2.
- **No simulated reference is sound.** The drafted one adds 3.08 and 4.57 km per rerouted vehicle and loads 5,300 instead of 3,710 veh/h upstream (critic_M F1). A no-ramp arm also removes the downstream load, so it cannot KILL (INFERENCE). A flow-matched insertion swaps LC2013 for SUMO's unvalidated insertion check (PR-02, PR-03). The ceiling is E on fresh rows (K0).

## 4. Arms
Cells: steady traffic, 5,300 and 6,000 veh/h. X1 is dropped (critic_M F8).

| Candidate | Rule (0.8 s elsewhere) |
|---|---|
| A16, A20, A30, A40 | lane-0 CAVs in the last 600 m of edge 3 take 1.6, 2.0, 3.0 or 4.0 s |
| L30 | A30 only while the roadside speed on 4a is below 60 km/h |
| C30 | A30 only while the accelerating lanes hold at least 2 vehicles (input 15) |
| G16, G30 | a CAV beside the accelerating lane, within 100 m of a vehicle on 4a_0 (input 14, b_env.py:935), takes 1.6 or 3.0 s until past it |

- The ALKS-leader gate stays: behind a human, 1.6 s (b_env.py:774-779). Level set {0.8, T}, so one step reaches T (hold, b_env.py:707). `tau_rise` stays.
- **Incumbents (deciding, same seeds):** p333, os0_10_10, os1_15_10, lr1000_16_2 (ASCH's pick, V496), 3E-D_TRUCK, and an in-cell re-pick: the lowest median delay among confirmatory 3's 69 grid rules on the tuning seeds (planb.md:204, :212). No control beside, never deciding.
- **Exposure:** no learner runs. Candidates are untuned; incumbents are tuned in the cell.
- **Confirmation, only after a provisional pass:** a 3E-D search in that cell (planb.md §3.3, plateau label included), a re-check on fresh seeds, and the same with `lcAssertive` 1.3 and 1.5 (V327). The pass stands only if the point stays above 0 in all three.

## 5. Measures

| Role | Measure | Reward relation (my reading of b_env.py:445, :842) |
|---|---|---|
| Deciding | `all_delay` | tied (speed, vehicles in system) |
| Constraints | `passed`; collisions; moving full-emergency events | tied (flow); a term; outside |
| Validity | `stuck_n`, `end_stop2`, ramp queues, delay by road, lane-0 flow | outside |
| Report-only | TTT, close-following, braking at 0.1 s | close-following: a term |

## 6. Seeds proposed
The author must confirm the block is free.

| Seeds | One purpose |
|---|---|
| 7,485,000-009 | smoke, identity, T3 |
| 7,485,010-019 | T0 |
| 7,485,020-059 | lane-end check |
| 7,485,100-139 | in-cell re-pick |
| 7,485,200-559 | check, n = 360, used once |
| from 7,486,000 | confirmation, its own proposal |

## 7. KILL rules
Statistic: planb.md §8.1. Level: 16 comparisons (8 arms × 2 cells), Bonferroni, two-sided 99.69 %, never lowered; "every incumbent" is an intersection (planb.md:429).
- **K0, every merge direction:** KILL in a cell if the 97.5 % (m = 2) upper bound of E's share under p333 is below 5 %.
- **K1, per arm and cell.** PASS (provisional): against every incumbent, point at least 3 % and lower bound above 0; flow at most 0.5 % worse (planb.md:438); Plan B's side tolerances (planb.md:332-333); `stuck_n` = 0. BOUNDED: upper bound against p333 below 3 %.
- **Screen:** PASS if one arm passes and is confirmed. Otherwise KILL: "bounded below 3 %" if all 16 are BOUNDED, else "not shown", bounds stated.
- **K2:** after a PASS, a DRL protocol only if the upper bound of E minus the rule's gain is at least 3 % of delay.
- **3 %:** the minimum detectable delay effect (planb.md:519); V435's tighter margin; a third of E. **5 %:** V462(1)'s delay tile; V435's margin; half of E. The drafted "5 %, lower bound above 3 %" goes with its reference.

## 8. Null and power
EXPL planning: stored paired differences of z33133, os1_10_0 and r4a1 against p333 (steady; paired SD about 17 % of the median), shifted to a true effect; 360 resampled from 240 seeds; 300 studies at 99.69 %.

| True effect | PASS | BOUNDED |
|---|---|---|
| −4 % | 0 % | 100 % |
| 0 | 0 % | 43-100 % |
| +3 % | 42-56 % | 0 % |
| +5 % | 91-100 % | 0 % |

- n = 240: PASS at +5 % is 63-100 %. "40 seeds detect 3 %" was wrong.
- Half-width 1.7-2.9 points: BOUNDED is near certain only for a true effect of 0 to −3 % or lower.
- K0: road pairs with no merge would fire it; p333 does not ([8.36, 11.39]).
- 6,000: not computed (20 stored seeds, another condition).

## 9. Runs x rate = cost

| Stage | Runs | Per 1,000 | Cost | Hours |
|---|---|---|---|---|
| Identity, T3, T0, lane-end | about 450 | $0.36 (correction 7) | $0.2 | 0.3 |
| Re-pick: 70 rules × 40 seeds × 2 cells | 5,600 | $0.115-0.36 | $0.6-2.0 | 1.1-3.3 |
| Check: 15 arms × 360 seeds × 2 cells | 10,800 | $0.36 | $3.9 | 6.4 |
| Total | about 16,850 | | $4.7-6.1 | 7.8-10 |

- Cap proposed: $8. Confirmation, per passing cell, on a new approval: 40,640 search rows at $0.115 (V490) plus 4,320 runs: about $6.2, 10 h.
- About $17.50 of the $40 went to Plan B on 9-10 November (V494).
- Build: 22-28 h (critic_M F10 accepted). Author time, apart: 2-3 h.

## 10. Plant and verification effect
- A code change, not a plant change, if identity holds. No route, `openGap` or `changeLane` change.
- T0 gives PR-10 its r2m3 record. Rows at 2.0-4.0 s carry "outside the plant's stated intended use; above the checked headway range".
- Smoke check: each row's `cfg` carries T, zone and trigger; the level histogram shows seconds at T; traced equals untraced.
- PR-28 stays a gap: the lane-end check describes, it does not validate.

## 11. Cells added to the count (N = 91) and post hoc labels
0: rules only (cells_tested.md:5). Post hoc: the whole screen; cells, merge-2 focus, arms and thresholds were set after stored results were seen.

## 12. Must-carry disclosures
- Merge-conflict and lane-change dynamics are outside the V&V record (plant_vv_record_v0.md:11; PR-08, PR-28); drop unknown (PR-26).
- LC2013 blocks a merge when the rear gap is below the follower's speed × tau / lcAssertive (MSLaneChanger.cpp:864-879; MSCFModel_IDM.cpp:218-221; checked): at 100 km/h, 15.9 m at 0.8 s and 79.4 m at 4.0 s (critic_M F4). A KILL is a result about this lane-change model; p333's merge gain may rest on it (INFERENCE).
- A long headway binds only behind an ALKS leader within 150 m; 4 s at 100 km/h is 111 m.
- After a pass, a learner needs a new action set and retraining, against this family tuned by CMA-ES in the cell (critic_M F9).
- No literature support is claimed (critic_M F7; Veksler et al. [VERIFY]). At 6,000, 73.8 % of vehicles finish (critic_M F8).
- Round-1 findings: all accepted, except "tau at most 1.6 s" (the question names longer values; labelled) and "120 seeds" (360, from the measured SD).

## 13. Expected outcome and your probability
KILL, bounded, in both cells. My judgement, not measured: a stop at T0 or the lane-end check 25 %; a provisional pass 4 %; a confirmed pass 2 %.
