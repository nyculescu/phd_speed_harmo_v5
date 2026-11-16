# Screen M, protocol-ready draft (angle: statistical rigor)

Stored-row numbers are EXPLORATORY (S6 rows, cell S, 5,300 veh/h, 240 seeds). Scripts and outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/work_rigor/`. No simulation ran.

## 1. Question; what a pass allows; what a KILL closes

- **Question.** In steady traffic on r2m3 (plant_c3), does a rule giving the CAVs beside an accelerating lane a 2.0-4.0 s headway cut door-to-door delay by 5 % or more against the best rule within 0.8-1.6 s?
- **A pass allows** a protocol for a DRL study with a wider action set, against the passing rule family tuned by planb.md §3.3's search. v3w's levels end at 1.6 s (b_env.py:37), so a learner needs retraining. Left for it: which CAV yields, and when.
- **A KILL closes** M and P1 for delay on this plant, not P2 (section 3).

## 2. Approvals and preconditions

Author decisions:
- a cap, proposed $5 (Plan B's does not carry over); the rental (V483); the seeds;
- headways above 1.6 s: a departure from the CAV contract for this screen only, as in V273;
- V355 KILLed fixed zone patterns of 1.2 or 0.8 s "for this form"; six arms are such patterns at new values, so the author rules whether V355 covers them.

Before any comparison: identity replay and T0 (section 10). PR-26 is no precondition: no rule reads a capacity drop; the memo's "minimal drop" is withdrawn (V327: 11.7 % and 10.8 %, no null). PR-28 stays open: a pass at merge 2 is frozen until it closes (section 7).

## 3. Stage 0: statements from stored rows (zero runs, EXPLORATORY)

- Merge excess under p333: 9.2 % [8.4, 11.2] of delay in S, 11.1 % in TRUCK, almost all at merge 2; 15-18 % is tied to merge-2 slow minutes (critic_M.md:14; an_delay_floor.md:8).
- **Decided:** no ceiling is below 5 %, so the drafted rule 1 (KILL every merge actuator) cannot fire and is deleted. M does not bound P2.
- **Decided:** at 1.0-1.2 s the headway route is closed in S. Against p333 (97.5 %, my recomputation): grid_z31333 −2.1 % [−3.7, −0.6], grid_r4a2 −3.8 % [−6.0, −2.3], z33133 −4.1 % [−5.8, −2.5], r4a1 −7.5 % [−10.3, −4.4]. No stored rule beats p333.
- **Open:** above 1.6 s (no record, an_delay_floor.md:88) and 6,000 veh/h.
- An independent reader re-derives these before the rental.

**No simulated no-merge reference (correction 2).** None can carry a KILL:

| Candidate | Changes | Defect |
|---|---|---|
| Drafted | ramp vehicles drive 3.08 and 4.57 km more; upstream 3,710 → 5,300 veh/h | +15 % delay by definition (critic_M.md:9): cannot pass |
| No-ramp arm | 1,237 veh/h per lane everywhere, against 1,502 and 1,767 | removes density: 25.5 s per vehicle at 3,500, 57.1 s at 5,300 (an_delay_floor.md:51-52): cannot fail |
| Flow-matched ideal merge | insertion at speed on loaded lanes | refused insertions count as delay (b_env.py:427): SUMO's insertion rule decides it (INFERENCE) |

## 4. Arms

Cells: S at 5,300 and 6,000 veh/h; X1 dropped (critic_M.md:46). Settings as S6's p333 job. The V2V gate and rise limit stay (b_env.py:774-782). Long arms use two levels (T, 0.8 s) through `headways` (b_env.py:479-482).

| Arm | Definition | Count |
|---|---|---|
| Zone | ALKS in the mainline lane beside the accelerating lane, from 600 m before its start to its end, take T; others 0.8 s. Merge 2 only, or both. T = 2.0, 3.0, 4.0 s | 6 |
| Trigger | same lane and stretch, both merges; T only while input 14 shows an accelerating-lane vehicle within 100 m (b_env.py:924). T = 2.0, 3.0 s | 2 |
| In-range list | the 15 carried rules (planb.md:203), unchanged | 15 |
| No control | every table, never deciding | 1 |

- One zone length, 600 m: the rise needs 306 m to 3.0 s and 444 m to 4.0 s (critic_M.md:38), so 300-m zones are dropped.
- **Equal exposure.** One long pick and one in-range pick per cell, on the same 60 selection seeds: the lowest median paired delay against p333 among arms with median collisions at most p333's + 1 (planb.md:228). Ties: list order. Picks are frozen before the verdict stage.

## 5. Measures

- **Deciding:** `all_delay` and served flow `passed`, both tied to the per-vehicle reward's speed and flow terms (b_env.py:63-64).
- **Report-only, outside the reward:** delay by road, `end_stop2`, fuel per km, jam share, congested km, braking at 4.5 m/s² or harder at 0.1 s, `alks_full_moving`, collisions. Close-following `ttc_net` is a reward term.

## 6. Seeds proposed

The ledger shows none at or above 7,485,000; the author confirms.

| Seeds | Purpose |
|---|---|
| 7,480,400-402 (stored) | identity replay; equality printed only |
| 7,485,000-009 | T0, determinism; never read for delay |
| 7,485,010-099 | reserved: repeats after a fix |
| 7,485,100-159 | selection |
| 7,485,200-439 | verdict, n = 240 as S6 (planb.md:367), used once |

## 7. KILL rules

- **Statistic.** e = median(O − A) / median(O) × 100 over paired seeds; positive: arm A has less delay (planb.md:424).
- **Level.** 97.5 % two-sided (Bonferroni, 2 cells). The percentile bootstrap and the exact order-statistic interval of the median must both hold. The pick uses other seeds, so 8 arms need no correction.
- **T0 KILL.** No value above 1.6 s passes T0.
- **Per cell,** long pick against p333, os0_10_10 and the in-range pick. PASS: against each, point at least 5, lower bounds above 0, flow at most 0.5 % lower by point. Bounded KILL: against p333, upper bounds below 5. Otherwise "not shown".
- **Screen.** PASS if either cell passes; otherwise KILL.
- **Why 5 %.** V354 fixed "coordination matters" on r2m3 at 5 %, CI excluding 0, flow at most 0.5 % worse; V462(1)'s W tile uses 5 %. The drafted 3 % was a detectable effect (planb.md:519), not a size worth a study.
- **Location.** If a cell passes with over half the gain on 4a, 4 and ramp 2 (V482 F16), no protocol until PR-28 closes.
- **Stopping.** Each stage runs once: no added seeds, arms, cells or re-picks.

## 8. Null and power

EXPLORATORY: noise of four stored merge rules against p333; 2,000 simulated studies per row; one comparison (the three-opponent intersection can only lower PASS).

- Paired SD: 16-17 % of p333's median delay. SE of the median effect: 1.6-3.1 points at 40 seeds, 0.6-1.2 at 240. At a true 3 %, 40 seeds clear 0 in only 12-30 % of studies.

| True effect | PASS, n = 240 | Bounded KILL |
|---|---|---|
| 0 | 0.0 % | 99.7-100 % |
| 3 % | 0.1-7.1 % | 18-88 % |
| 5 % | 49-52 % | 0.9-1.2 % |
| 6 % | 87-96 % | 0.0 % |
| 7 % | 98-100 % | 0.0 % |

- Sign-flip null: lower bounds above 0 in 0.85-1.15 % (nominal 1.25 %); the bootstrap alone 1.0-2.1 %, hence two intervals.
- Selection: the best of eight null arms reads 5 % or more in 8 % of studies, so the pick is re-run. A true 6 % arm is picked in 94-100 %.
- It can fail (true 0) and pass: an arm removing two thirds of the 9.2 % excess passes in 82-96 %.
- Smallest gain excluded at a true 0: 1.3-2.7 %.
- 6,000: no steady paired rows; under condition T the paired SD is 8-10 % there, 8-15 % at 5,250 (20 seeds).

## 9. Runs × rate = cost

| Stage | Runs |
|---|---|
| Replay, T0, determinism | 100 |
| Selection: 23 arms × 60 × 2 | 2,760 |
| Verdict: up to 5 arms × 240 × 2 | 2,400 |
| Total | 5,260 |

- 1,690 runs/h, $0.36 per 1,000 (V493, V494; correction 7): about $1.9, $2.0 with 6 % setup (planb.md:538); 3.1 machine-hours. Speed at 6,000 is not measured.
- Build, my estimate: 16-20 h (rules 5, T0 meters 5, readers 4, packaging 3, review 2).
- Author time, apart: 1.5 h.

## 10. Plant and verification effect

- **Smoke.** S|p333, S|nc, S|r4a1, S|os0_10_10 on 7,480,400-402 equal the stored rows by value (V499); traced equals untraced (V386).
- **T0 (PR-10):** zone arm at both merges per value, and p333; 10 seeds, both cells. (a) `tau_mismatch` = 0 (plant_sweep.py:224); (b) median time gap of gated zone CAVs at the accelerating lane's start at least 0.8 + 0.5 × (T − 0.8) s (my judgement); (c) values under 0.2 s apart (one rise step) merge. A value failing (a) or (b) leaves the family. Reported: gate-drop share, braking at 0.1 s (V367), lane changes, `end_stop2`.
- **Label, every long-arm row:** "outside the plant's stated intended use (plant_vv_record_v0.md:9); merge-conflict and lane-change dynamics not validated (PR-08, PR-28)".

## 11. Cells added to the count (N = 91) and post hoc labels

Rules only: 0 cells (cells_tested.md:5). Post hoc (planb.md:576): designed after S6 and the stored dose-response.

## 12. Must-carry disclosures

- Post hoc; outside intended use; PR-08, PR-26, PR-28 open.
- LC2013 needs a rear gap of follower speed × tau / lcAssertive, so a longer tau raises the gap a merger needs (critic_M.md:34). A KILL holds for this lane-change model only.
- In-range rules were not tuned at 6,000: a lower-bound reference. About 74 % of vehicles finish there (condition T rows).
- No literature support is claimed (critic_M.md:44).
- A pass is headroom for a rule, never a claim.

## 13. Expected outcome and probability (a judgement)

Bounded KILL in both cells 80 %; KILL with a cell "not shown" 10 %; KILL at T0 6 %; PASS 4 %.
