# Screen M: merge coordination and the delay ceiling at the merges (protocol-ready)

EXPLORATORY = recomputed here from stored S6 rows (cell S: steady, 5,300 veh/h, 240 paired seeds; `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/synth_work/`). Positive = less delay. No simulation ran.

## 1. Question; what a pass allows; what a KILL closes

- **Question.** In steady traffic on r2m3: (a) how much delay sits at the merges under p333, the best stored rule; (b) does a 2.0-4.0 s headway on lane-0 ALKS at merge 2 cut delay by at least 5 % against every opponent inside 0.8-1.6 s?
- **A pass allows,** in order: closing PR-28 (the zone sits at its location, V482 F16); a rules-only search of the family (planb.md §3.3); a DRL protocol only under K2. The controller is a rule; a learner needs new actions (b_env.py:37) and retraining.
- **A KILL closes,** per bounded cell, this always-on zone family as a 5 % delay lever; the triggered form (P1) and lane actuators (P2) stay open.

## 2. Approvals and preconditions

Author decisions:
1. A new post hoc study (planb.md:576): cap $4, inside the $40 / 7-day ceiling; one rental (V483); the seeds of section 6. Plan B's cap does not carry over (V488).
2. Headways above 1.6 s for this screen only, a CAV-contract departure as in V273.
3. Whether V355's KILL of fixed zone patterns covers these arms.

Before any delay is read:
- Zero runs: PR-26's drop estimator with a no-drop null (V244) on stored no-control rows; until then "capacity drop unknown".
- Identity, smoke and T0 (section 10).
- Lane-end trace (PR-24, PR-28): no control and p333, 2 seeds per cell; traced `end_stop2` samples equal the counter (plant_sweep.py:294).

## 3. Stage 0: stored rows (zero runs, EXPLORATORY)

E = [D(3a) − r(2)·K(3a)] + [D(4a) − r(3)·K(4a)] + ramp insertion queues, over `all_delay`. D: a road's delay; r: delay per vehicle-km on the road upstream; K: vehicle-km. E loads and changes nothing: an accounting bound at unchanged flow.

| Statement | Value | Decides |
|---|---|---|
| E under p333 | 9.20 % [8.35, 11.39] (97.5 %); merge 1 1.94 %, merge 2 7.13 %. By slow minutes at merge 2: 15 %, and 18 % in TRUCK, an association (an_delay_floor.md:8) | delay is left at merge 2 only |
| 22 stored rules against p333 | none has less delay by point | in-range pick at 5,300: p333 |
| Stored 1.0-1.2 s near a merge | −2.11 % [−3.70, −0.58] to −7.51 % [−9.97, −4.42] (97.5 %) | closed inside 0.8-1.6 s; above it, no record (an_delay_floor.md:88) |

**No simulated no-merge reference (correction 2); the reference is E.**
- Drafted (ramp vehicles enter at the main origin): +3.08 and +4.57 km per rerouted vehicle and 5,300 instead of 3,710 veh/h on edges 1-2, a plant change. About +15 % delay by definition (critic_M.md:9): a KILL unrelated to merges. Read on 3a to 5 only, the origin meters the flow (INFERENCE).
- No-ramp arm: it removes 1,590 veh/h below the merges, so it reads the speed-flow curve and cannot fail (an_delay_floor.md:51-52; INFERENCE).
- Flow-matched ideal merge: SUMO's insertion check replaces LC2013 (PR-02, PR-03; INFERENCE).

## 4. Arms

Cells: steady traffic at 5,300 and 6,000 veh/h. X1 is dropped: its slowdown sits directly below merge 2 (critic_M.md:46).

| Arm | Definition |
|---|---|
| Z20, Z30, Z40 | level table (1.6, 1.2, 1.0, 0.8, T) through `headways` (b_env.py:479), so the arm equals p333 outside its zone (INFERENCE; section 10 checks it). T for ALKS on lane `3_0` in its last 600 m and on `4a_1`, beside the accelerating lane (corridor.py:89). T = 2.0, 3.0, 4.0 s |
| U30 | Z30, but 0.8 s from the start of 4a, where LC2013's rear-gap rule then reads 0.8 s (INFERENCE) |
| Z16 | the zone at 1.6 s: in-range anchor and opponent |
| In-range | 5,300: p333 (the stored pick), os0_10_10. 6,000: the 15 carried rules (planb.md:203) and 3E-D_TRUCK. No control beside, never deciding |

**Equal exposure.** Per cell, one long pick, and at 6,000 one in-range pick, on 60 selection seeds: lowest median paired delay against p333, collisions at most p333's + 1 (planb.md:228), ties by list order, frozen before the verdict. At 5,300 the in-range rules had 240 stored seeds.

## 5. Measures

Relation is to v3w's reward (b_env.py:842-843).

| Role | Measure | Relation |
|---|---|---|
| Deciding | `all_delay` (plant_sweep.py:347) | tied (speed, flow) |
| PASS conditions | flow `passed`; collisions, moving full-emergency events, `m_stuck_n` | tied; outside |
| Report-only | E by merge, TTT, merge-2 friction (delay on 4a, ramp 2, its queue); close-following, braking at 0.1 s (V367); `end_stop2`, fuel per km, jam share | tied; terms; outside |

## 6. Seeds proposed

The ledger shows no use from 7,485,000; the author must confirm.

| Seeds | One purpose |
|---|---|
| 7,480,000-002 (stored S5 rows) | identity replay; equality only |
| 7,485,000-009 | T0, determinism, traced against untraced |
| 7,485,010-019 | lane-end trace |
| 7,485,020-099 | reserved: repeats |
| 7,485,100-159 | selection |
| 7,485,200-439 | verdict, n = 240, used once |

## 7. KILL rules

- **Statistic, level.** e = median(O − A) / median(O) × 100 over paired seeds, percentile bootstrap (planb.md:424); two-sided 97.5 %, Bonferroni over 2 cells; the pick uses other seeds and the opponents are an intersection (planb.md:428-429).
- **T0.** A long arm failing T0 in a cell leaves it; with none left, the cell is KILLed at T0.
- **K0, the ceiling.** KILL every merge direction for delay in a cell if E's 97.5 % upper bound under p333 on the verdict rows is below 5 %; at 6,000 only if edge 3 has a median of 0 minutes below 60 km/h (otherwise E's reference road is congested).
- **K1,** long pick against p333, os0_10_10, Z16 and the in-range pick. PASS: against each, point at least 5 % and lower bound above 0; flow at most 0.5 % lower (point); mean-based tolerances of 0.02 collisions and 0.10 moving full-emergency events per run (planb.md:91-92); stuck rows at most p333's + 2 (stored arms: 0-2 of 240, EXPLORATORY). BOUNDED: upper bound against p333 below 5 %. Otherwise NOT SHOWN.
- **Screen.** PASS if either cell passes. KILL per bounded cell: "the picked arm is bounded below 5 %; three long arms lost a 60-seed selection". Not shown closes nothing and allows no protocol.
- **K2.** After a PASS, a DRL protocol only if E's upper bound minus the searched rule's gain is at least 5 %.
- Each stage runs once.

**Why.** 5 %: V354's "coordination matters" rule on r2m3 and V462(1)'s delay tile; about half of E. The drafted "lower bound above 3 %" went with its reference; 3 % was a detectable effect on X1/X2 noise (planb.md:519), and here the paired SD is 16-17 %.

## 8. Null and power

EXPLORATORY planning: paired differences of four stored merge rules against p333, centred and shifted; n = 240; 2,000 studies; one comparison.

| True effect | PASS | BOUNDED |
|---|---|---|
| 0 | 0.0 % | 99.8-100 % |
| 3 % | 0.0-6.3 % | 22-88 % |
| 5 % | 49-53 % | 1.3-1.6 % |
| 6 % | 86-96 % | 0.0-0.1 % |

- Upper half-width 1.3-2.7 points: a true 2 % is bounded in 49-100 %.
- Sign-flip null: lower bound above 0 in 1.15-1.65 % (nominal 1.25 %). Selection null: the best of four null arms reads 5 % or more in 0.0-2.0 %.
- T0: 10 of 10 seeds above p333 under no effect: 0.1 %.
- K0 can fire: E reads −1.25 % and −1.65 % on road pairs with no merge.
- 6,000: no steady paired rows are stored; power unknown.

## 9. Runs × rate = cost

| Stage | Runs |
|---|---|
| 1: identity 15, determinism and traced twins 4, lane-end trace 8, T0 160 (8 arms, 10 seeds, 2 cells) | 187 |
| 2: selection, 60 seeds: 5 arms at 5,300, 20 at 6,000 | 1,500 |
| 3: verdict, 240 seeds: 5 arms at 5,300, 6 at 6,000 | 2,640 |
| Total | 4,327 |

- Rate (correction 7): 1,690 runs/h on 90 workers at $0.607/h, $0.36 per 1,000 runs (V493, V494): about $1.6, 2.6 machine-hours. Speed at 6,000 is unmeasured. A T0 stop costs 187 runs.
- Build, my estimate: 16-20 h, as critic_M's 2-3 days. Author time, apart: about 1.5 h.

## 10. Plant and verification effect

- **Identity.** S|p333, S|nc, S|os0_10_10 and S|r4a1 on 7,480,000-002 equal the stored rows by value (V499), as does the new rule class with an empty zone: a code change, not a plant change (planb.md:177).
- **Smoke.** `cfg` carries T and the zone; seconds at T appear inside the zone only; traced equals untraced (V386).
- **T0 (PR-10: "no r2m3 T0 record").** The zone at 1.0, 1.2, 1.6, 2.0, 3.0, 4.0 s, U30 and p333: seven values, 10 seeds, both cells. Pass: `tau_mismatch` = 0 (plant_sweep.py:224), and the median time gap of gated lane-0 ALKS in the last 100 m of `3_0` is above p333's in 10 of 10 seeds and at least 0.8 × T. Reported: lane-0 flow and density, gate-off share, ramp entries ahead of a commanded CAV.
- **Label, rows at 2.0-4.0 s:** "outside the plant's stated intended use: headway above the checked range 0.8-1.6 s (plant_vv_record_v0.md:9); merge-conflict and lane-change dynamics not validated (PR-08, PR-28)".

## 11. Cells added to the count (N = 91) and post hoc labels

0 added: rules only (cells_tested.md:5). Post hoc: cells, zone, values and thresholds follow the S6 results.

## 12. Must-carry disclosures

- Exploratory, post hoc; a pass is headroom for a rule, never a claim.
- LC2013 blocks a merge when the rear gap is below the follower's speed × tau / lcAssertive (MSLaneChanger.cpp:864-879): 79.4 m at 4.0 s and 100 km/h (critic_M.md:34). Results hold for this lane-change model only.
- The target binds only behind an ALKS leader within 150 m (a 4.0-s gap is 111 m at 100 km/h), rises 0.2 s per second and moves one level per 10-s hold (b_env.py:707-711, :774-782). A 3-4 s target meters lane 0 (critic_M.md:33; INFERENCE).
- 6,000 veh/h is above p333's capacity estimate (5,510-5,614 veh/h, an_delay_floor.md:43): delay reads capacity there. In-range rules were never tuned at 6,000.
- PR-28 is open. The memo's "minimal drop" premise is withdrawn (PR-26; V327: 11.7 % and 10.8 %, no null). No literature support is claimed.

## 13. Expected outcome and probability (my judgement)

Expected: KILL. PASS 4 %; both cells stopped at T0 10 %; no pass with every verdict cell bounded 68 %; no pass with a cell not shown 18 %.

## Synthesis notes

- Base: draft_rigor (both judges); the five-level table replaces its (T, 0.8) table.
- Trigger arms: judge_plant cut them, judge_rules kept them. Cut: at 795 veh/h on ramp 2 a trigger is mostly on (INFERENCE); the KILL no longer names P1.
- Friction branch: judge_plant wanted it, judge_rules found it reopens a KILL. Kept report-only.
- In-range selection at 5,300 is read from stored rows (judge_plant) and kept at 6,000.
- `stuck_n` = 0 (both judges) became "p333's + 2": p333's stored rows hold one stuck row (seed 7,480,615).
- Added: a spill-back guard on K0 at 6,000; K2 at 5 %. Removed: the second interval (judge_rules).
- Length: sections 1-13 hold about 1,250 words of prose and 320 in tables; with the tables they exceed 1,400, because the named grafts did not fit.
