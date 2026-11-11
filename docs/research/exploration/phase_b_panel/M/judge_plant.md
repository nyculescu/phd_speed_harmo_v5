# judge_plant: Screen M drafts (lens: traffic engineering, feasibility, cost)

Code: `/home/catalin/work/phd/wt/planb_v23/v5b/fleet/`. EXPLORATORY = my recomputation from stored S6 rows (cell S, p333, 240 seeds); scripts in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/judge_plant_work/`. No simulation ran. Scores are my judgement.

## Findings across the drafts

1. **A two-level table changes the run outside the zone.** A CAV starts at level index 0 and moves one level per 10-s hold (b_env.py:703-711); the gated target is `headways[lev]` (b_env.py:779). EXPLORATORY: p333's mean level index is 2.69 on edge 1, 1.0 on the ramps and 2.0 on their last stretch (3 = 0.8 s), so its ramp CAVs reach the accelerating lanes at about 1.0 s. With a two-level table they arrive at 0.8 s. The long arm then differs from p333 at the merges for a reason other than the zone. Rigor and opponent have this; cheap does not.
2. **Stored rows hold the in-range opponents at 5,300.** S6 holds 29 arms × 240 seeds in S, the 15 carried rules among them (planb.md:203); S3a holds 70 rules × 20 seeds in S (planb.md:358). EXPLORATORY: os0_10_10, os1_15_10 and lr1000_16_2 equal p333 on 77-81 of 240 seeds; median difference 0.00.
3. **Actuator limits were worked at 100 km/h.** EXPLORATORY: lane 3_0 runs at 73.9 km/h, lane 4a_1 at 45.1 km/h. INFERENCE (IDM equilibrium gap, equal speeds, 0.94-s human merger): there a 4.0-s gap is about 100 m and 54 m, inside the 150-m gate (b_env.py:36); the smallest T that admits a merger is about 1.6 s and 2.8 s. No value can be dropped by argument.
4. **6,000 veh/h exceeds p333's capacity estimate** (5,510-5,614; an_delay_floor.md:43). INFERENCE: 1 % of capacity is about 24,000 veh-s over the window, about 7 % of the band rows' 341,366 (critic_M.md:46), so the delay threshold reads capacity there. Only rigor says run speed at 6,000 is unmeasured (planb.md:538).

## draft_cheap: 6/10

Verified: table pass-through (b_env.py:479; plant_sweep.py:71); 3_0 feeds 4a_1 (corridor.py:89); `tau_mismatch` (plant_sweep.py:224); identity seeds (V493; planb.md:354); 6,000 band rows carry `perturb: random` (job_band.json). 507 runs, $0.18, 0.3 h: right.

Strong: (1) the only arm equal to p333 outside its zone; (2) T0 gates 480 runs behind 27; nothing stored is re-bought; (3) the merge-2 friction branch.

Fatal: (a) One value, one zone. A KILL, or a T0 failure at 3.0 s alone, closes "headways above 1.6 s". Finding 3 does not support dropping 2.0 and 4.0 s. (b) KILL means "not PASS" at n = 120. A true 3 % passes 29-43 % (its §8), so the KILL has no bound. planb.md:519 rests on X1- and X2-like noise, not S (paired SD 17 %).

Other: T0 at 5,300 only; 10 h build is tight (my estimate: 12-14 h).

## draft_rigor: 7/10

Verified: V354's 5 % rule, word for word; planb.md:203; input 14 (b_env.py:924, :935); V482 F16; planb.md:538. 5,260 runs, $1.9, 3.1 h: right.

Strong: (1) three values, each with T0 in both cells; a failed value leaves, the family stays; (2) PASS, bounded KILL or "not shown", with a null; (3) the 5 % threshold has a record on this plant (V354, V462(1)).

Fatal as written: finding 1 (a one-line fix).

Other: 900 selection runs repeat finding 2; three "both merges" arms add a zone where the stored excess is 2.0 % (EXPLORATORY, cheap §3); trigger arms have no T0; T0(b) passes 2.0 s at a 1.4-s gap, below 1.6 s.

## draft_opponent: 5/10

Verified: MSLaneChanger.cpp:864-879 and MSCFModel_IDM.cpp:218-221 (toolchain `sumo-src`); `end_stop2` (plant_sweep.py:294); ASCH = lr1000_16_2 (V496); `lcAssertive` 1.3 and 1.5 (V327); §9's arithmetic. `stuck_n` is `m_stuck_n`, pack only (measure.py:378).

Strong: (1) T0 on seven values, counting ramp vehicles that enter in front of a commanded CAV; (2) the A16 anchor, E's placebo and K2; (3) the LC2013 rule checked at source.

Fatal: (a) 16 comparisons at 99.69 %, "bounded" only if all 16 are. Its own file gives BOUNDED 43 % at a true 0 (r4a1 noise, n = 360). INFERENCE: arms near 0 end "not shown", after 16,850 runs. (b) Identity replay sits on fresh seeds 7,485,000-009; no stored rows exist there (planb.md:177). (c) Finding 1.

Other: 2,800 re-pick runs at 5,300 repeat S3a; three incumbents are p333's near-twins (finding 2); G, C and L arms have no T0; A arms drop to 0.8 s at 4a's start, unstated (b_env.py:781-782 limits rises only); 22-28 h build for a 4 % pass chance.

## Winner: draft_rigor

**Graft from cheap:** the five-level table (1.6, 1.2, 1.0, 0.8, T); T0 as a gate before selection; the friction branch; the 6,000 band-row caveat.

**Graft from opponent:** A16 as the in-range anchor; T0 pass at 0.8 × target, plus the ramp-entry count; one 3.0-s arm ending at 4a's start (INFERENCE: LC2013's rear gap falls back to 0.8 s); E's placebo and K0 (no extra runs); K2; the two-seed `end_stop2` trace (PR-24); the SUMO source lines.

**Add:** finding 4 beside the 6,000 verdict; V195 in stage 0 (older plant; a courtesy-gap rule failed).

**Cut or fix in rigor:** the (T, 0.8) table; the three "both merges" arms; the two trigger arms (795 veh/h on ramp 2, an_delay_floor.md:16, is a vehicle every 4.5 s against a 10-s hold, so a trigger is mostly on; INFERENCE); the in-range selection at 5,300 (read it from S6, keep it at 6,000); T0(b) (no pass below a 1.6-s held gap); rise distances (at stored speeds).

My count after these: about 4,000 runs, $1.4, 2.4 h at 1,690 runs/h (V493). Build stays 16-20 h.
