# Screen M, protocol-ready draft: merge coordination and the delay ceiling at the merges (cheapest decisive design)

EXPLORATORY = my re-derivation from stored S6 rows (cell S, 5,300 veh/h, 240 paired seeds; median of paired differences; 95 % percentile bootstrap); scripts in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/work_cheap/`. Edge = (p333 − arm) / median(p333) × 100; positive = the arm has less delay.

## 1. Question; what a pass allows; what a KILL closes
- In steady traffic on r2m3, does a headway above 1.6 s, held by lane-0 ALKS before and at merge 2, cut delay below p333 by at least 3 %?
- "Any merge controller" gets a stored-row ceiling (§3).
- A pass allows the PR-28 lane-end check, then a rules-only search of this rule family; no training. The passing controller is a rule (critic_M F9); a learner keeps only the gap between that tuned rule and the ceiling, and needs a new action set and retraining.
- A KILL closes, on this plant, headways above 1.6 s as a delay lever at the merges (memo L4, M, P1's `setTau` form). Lane actuators (P2) stay open.

## 2. Approvals and preconditions
Author decisions:
1. A new study with its own cap; $3 proposed. Plan B's $20 cap covered its two rentals (V488). The $40 / 7-day ceiling holds about $18 (V475, V494).
2. One rental (V483) and the seeds of §6.
3. Headways above 1.6 s for this screen only: a departure from the CAV contract and `HEADWAYS_S` (b_env.py:37), as V273 allowed once.
4. Whether V355's KILL of fixed zone patterns (1.2 or 0.8 s) covers this arm.

Preconditions: unit tests; §10's smoke checks. PR-26 is not one (no rule reads the drop). Nor is PR-28: it guards gains (plant_vv_record_v0.md:79), so a KILL does not need it; a pass supports nothing until it closes.

## 3. Stage 0: stored rows (zero runs, EXPLORATORY)
| Statement | Value | Decides |
|---|---|---|
| Merge excess under p333: delay on 3a and 4a above the upstream road's rate, plus ramp insertion queues | S 9.2 % [8.4, 11.2]; TRUCK 11.1 % [10.5, 11.7] | the ceiling: an accounting bound, not an intervention. Outer estimate by merge-2 slow minutes: 15 % (S), 18 % (TRUCK), an association (an_delay_floor.md:8) |
| Split, S | merge 1: 2.0 % [1.9, 2.1]; merge 2: 7.2 % [6.3, 9.0] | merge 1 is below 3 %: no arm there |
| Ramp-2 road and insertion queue | 0.8 % | nothing to shrink at 5,300 |
| Stored lengthening, edge | 1.0 s on 4a: −3.8 [−5.6, −2.6]; 1.2 s before 4a: −4.1 [−5.6, −2.6]; 1.2 s on 4a: −7.5 [−9.2, −4.7]; no control (1.6 s): −56.0 [−59.1, −54.7] | in range, all lose; those at merge 2 add merge-2 delay (+1.6 to +4.9 points). Above 1.6 s no row exists (an_delay_floor.md:88): stage 1 |
| Best stored rule on delay | none of 28 arms beats p333 (no interval clear of 0); os0_10_10: 0.00 [0.00, 0.00] | p333 is the one reference |

- **Reference.** The drafted no-merge arm is dropped: +3.08 and +4.57 km per rerouted vehicle, upstream load 3,710 → 5,300 veh/h, an overloaded origin (critic_M F1; an_delay_floor.md:65-66). A no-ramp arm cannot KILL: stored delay is 25.5 s per vehicle at 3,500 against 57.1 s at 5,300 (an_delay_floor.md:51-52; INFERENCE). An ideal merge needs a new insertion mechanism. The reference is row 1: it loads and changes nothing. Limit: spill-back onto edge 3 can make it understate.
- critic_M F8's 6,000 figures are not steady: those band rows carry the random training slowdown (cfg `perturb: random`).

## 4. Arms
| Arm | Definition |
|---|---|
| p333 | stored configuration (`cav_rule` [3, 3, 3], hold 10 s) |
| L30 | new rule class: 0.8 s everywhere, except 3.0 s on lane `3_0` in its last 700 m and on lane `4a_1` (corridor.py:89). Level table `(1.6, 1.2, 1.0, 0.8, 3.0)` passed by `ctrl.env.headways` (b_env.py:479; plant_sweep.py:71). One level per 10-s hold, rise 0.2 s per second, 150-m ALKS-leader gate unchanged (b_env.py:707-711, :774-786) |

- One value, one zone: 2.0 s cannot admit an equal-speed merger under LC2013 (critic_M F4, INFERENCE); 4.0 s sits at the gate; the rise alone takes 306 m (critic_M F5).
- Cells: steady traffic at 5,300 and 6,000 veh/h. X1 is dropped (critic_M F8).
- Equal exposure: neither arm is tuned on any seed.

## 5. Measures
No learner runs, so no measure is a reward term.
- Deciding: `all_delay` (plant_sweep.py:347), with served vehicles beside it.
- Branch: merge-2 friction = delay on 4a + ramp-2 road + ramp-2 insertion queue, in points of p333's median delay.
- Report-only: TTT, lane-end stops, close-following, braking at 0.1 s, gate-on share, delay by road and lane (PR-28).

## 6. Seeds proposed (the ledger shows no 7,485,xxx; the author confirms)
| Seeds | One purpose |
|---|---|
| 7,480,000-002 | identity replay of S5 p333 rows (V493; planb.md §6) |
| 7,485,000-009 | stage 1: T0, T3, traced against untraced |
| 7,485,100-219 | stage 2 |
| 7,485,300-419 | reserved for stage 3 |

## 7. KILL rules
- **Rule 1 (stage 1, T0, 10 seeds, 5,300).** KILL unless `tau_mismatch` = 0 (plant_sweep.py:224) and the median time gap of gated lane-0 ALKS in the last 100 m of `3_0` is at least 2.5 s and higher than under p333 in 10 of 10 seeds. 2.5 s is the smallest gap that admits a merger (critic_M F4, INFERENCE); no record sets it.
- **Rule 2 (stage 2, only after rule 1 passes, same rental).** Per cell, the edge with a two-sided 97.5 % percentile bootstrap interval (Bonferroni over 2 cells; planb.md:424, :428). PASS if in at least one cell the edge is at least 3 % with the lower bound above 0 and collisions at most p333's + 1 (planb.md:228). Otherwise KILL.
- **Branch.** A KILL also closes the triggered form (P1): an always-on zone supplies at least the gaps a trigger would (INFERENCE). Exception: if friction falls by at least 3 points with the lower bound above 0, stage 3 is the author's decision.
- **Why 3 %.** A third of the ceiling; Plan B's detectable effect at n = 120 (planb.md:519); below the 5 % delay win size (V462). The memo's 5 % / 3 % rule went with its reference; the stored ceiling exceeds it.

## 8. Null and power (EXPLORATORY: S6 differences of three stored lengthening rules, centred and shifted; 2,000 studies)
Paired SD in S is about 17 % (robust 11-14 %), against about 8 % in TRUCK.

| True edge, % | 0 | 3 | 4.6 | 7.2 | 9.2 |
|---|---|---|---|---|---|
| PASS per cell, n = 120 | 0.0-1.1 % | 29-43 % | 48-88 % | 84-100 % | 96-100 % |

- Rule 2 can fail and can pass. False pass over both cells: 2.5 % nominal. At the memo's n = 40 a true 9.2 % edge passes only 55-84 %.
- A KILL reports the interval's upper end, 1.9-3.4 points above the estimate, as the bound on the lever (round_2.md:361, V435).
- Rule 1: 10 of 10 under no effect has probability 0.1 %. It can fail: IDM's equilibrium gap at 3.0 s passes 150 m above about 92 km/h, so the gate drops; at lane 0's 73.9 km/h (critic_M F4) it is about 77 m (INFERENCE).
- At 6,000 no steady variance is stored; power there is unknown.

## 9. Runs × rate = cost
| Stage | Runs |
|---|---|
| identity 3, T3 2, untraced twins 2 | 7 |
| 1: T0 | 2 arms × 10 seeds = 20 |
| 2: delay | 2 arms × 120 seeds × 2 cells = 480 |

- 507 runs × $0.36 per 1,000 (S6-style, 1,690 runs/h) = $0.18. Batch 0.3 h; with setup under 1 machine-hour, about $0.6. A stage-1 KILL costs 27 runs.
- Build (my estimate): 10 h, of which the T0 trace and reader 3. The critic's 2-3 days holds for the full draft.
- Author time: about 1 h.

## 10. Plant and verification effect
- No plant file changes; a code change only if p333 replays bit-identical (planb.md:177).
- Smoke: L30 rows show 3.0-s seconds inside the zone only; T3; traced equals untraced (V386).
- T0 is rule 1; r2m3 has no T0 record (PR-10).
- Every L30 row carries "outside the plant's stated intended use: headway above 1.6 s" (plant_vv_record_v0.md:9) and "lane-change dynamics not validated (PR-08, PR-28)".

## 11. Cells added and post hoc labels
0 added: rules only (cells_tested.md:5); N stays 91. Post hoc: zone, lane, value and the 6,000 cell were chosen after stored rows were read (planb.md:576).

## 12. Must-carry disclosures
- Exploratory; a pass is no claim.
- A KILL holds for SUMO's LC2013 and this gate, at the location PR-28 leaves open.
- Capacity drop not settled (PR-26; V327: 11.7 % and 10.8 %, no null); the memo's "minimal drop" premise is withdrawn.
- At 6,000 demand exceeds p333's capacity estimate (5,510-5,614 veh/h, an_delay_floor.md:43).
- Literature mismatch [VERIFY] (critic_M F7).
- **Given up:** a simulated ceiling; 2.0 and 4.0 s; the 300-m zone; merge 1; no control and os0_10_10 as paid arms; the triggered rule; a 1.6-s lane-0 arm; PR-28 before the screen.

## 13. Expected outcome (my judgement)
KILL at stage 1 about 20 %; KILL at stage 2 about 68 %; branch to stage 3 about 8 %; PASS about 4 %.
