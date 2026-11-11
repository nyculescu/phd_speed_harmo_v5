# PART 1. Screen M: merge coordination and the delay ceiling at the merges (protocol-ready, revised)

EXPLORATORY = recomputed here from stored rows (S6 cell S: steady, 5,300 veh/h, 240 paired seeds; the 6,000 band rows); scripts in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/final_work/`. Positive = less delay. No simulation ran.

## 1. Question; what a pass allows; what a KILL closes

- **Question.** In steady traffic at 5,300 veh/h on r2m3, does a 2.0-4.0 s headway on lane-0 ALKS at merge 2 cut delay by at least 5 % against p333 and beat every in-range opponent? Stage 0 only sizes the delay at the merges.
- **A pass allows,** in order: a PR-28 check with its own criterion; a rules-only search of the family (planb.md §3.3); a DRL protocol with its bar set against the searched rule. The passing controller is a rule. A learner needs actions above 1.6 s (b_env.py:37) and retraining; what it could add is unknown.
- **A KILL closes** this always-on lane-0 zone family as a 5 % delay lever at merge 2 at 5,300. The triggered form (P1) and lane actuators (P2) stay open.

## 2. Approvals and preconditions

Author decisions:
1. A new post hoc study (planb.md:576) with cap $3, inside the $40 / 7-day ceiling (about $17.50 used by Plan B, V494, whose cap does not carry over, V488); one rental (V483); the seeds of section 6.
2. Headways above 1.6 s, this screen only: a CAV-contract departure, as V273.
3. V355's KILL of fixed zone patterns is set aside for these arms.

Checks, in order (criteria in section 10):
- Identity and smoke: a failure stops the screen until fixed. T0: a failed arm is VOID.
- Lane-end counter trace (PR-24): no control and p333, 2 seeds per cell; traced `end_stop2` samples equal the counter (plant_sweep.py:294), or it is not reported.
- PR-28 stays open (label, section 7). PR-26's drop estimator with a no-drop null (V244) is report-only: it changes no arm, rule or threshold; its hours are outside section 9.

## 3. Stage 0: stored rows (zero runs, EXPLORATORY)

E = [D(3a) − r(2)·K(3a)] + [D(4a) − r(3)·K(4a)] + ramp insertion queues, over `all_delay` (D: a road's delay; r: delay per vehicle-km on the road upstream; K: vehicle-km). E is a descriptive split, not a bound.

| Statement | Value | Decides |
|---|---|---|
| E under p333 | 9.20 % [8.35, 11.38] (97.5 %); 7.13 % at merge 2 | nothing alone |
| Delay tied to minutes with 4a below 60 km/h | 14.6 % of mean delay (TRUCK 18 %, an_delay_floor.md:58); an association | delay sits at merge 2 |
| Why E is no bound | per slow minute it moves 62 % as much as delay; with no slow minute (22 seeds) it reads 5.72 % | no ceiling |
| Stored 1.0-1.2 s near a merge (4 rules) | −2.1 % [−3.8, −0.6] to −7.5 % [−10.0, −4.3] (97.5 %) | no re-run in range; above 1.6 s no record (an_delay_floor.md:88) |

**No simulated no-merge reference (correction 2).** No tested ceiling is on record; the one upper figure is a loose 39 % on roads 3a to 5 (an_delay_floor.md:56-57; INFERENCE). The memo's rule 1 is withdrawn.
- Drafted (ramp vehicles enter at the main origin): edges 1-2 carry 5,300 instead of 3,710 veh/h, the insertion point 1,767 instead of 1,237 veh/h per lane; +3.08 and +4.57 km per rerouted vehicle, about +15 % delay by definition (critic_M.md:9; an_delay_floor.md:65). A plant change; on 3a to 5 alone, the origin meters what arrives (INFERENCE).
- No-ramp arm (ramp vehicles dropped, main-route delay compared): removes 1,590 veh/h below the merges. A valid ceiling, but it reads the speed-flow curve: near 55 % by stored 3,500-veh/h rows (an_delay_floor.md:52; INFERENCE); no 5 % rule on it can fire.
- Flow-matched ideal merge: SUMO's insertion check replaces LC2013; unvalidated (PR-02, PR-03; INFERENCE).

## 4. Arms

Cells: steady traffic at 5,300 (deciding) and 6,000 veh/h (report-only). X1 is dropped: its slowdown sits directly below merge 2 (critic_M.md:46).

| Arm | Definition |
|---|---|
| Z20, Z30, Z40 | new lane-indexed rule class; level table (1.6, 1.2, 1.0, 0.8, T) through `headways` (b_env.py:479); hold 10 s. T on lane `3_0` in its last 600 m and on `4a_1`, beside the accelerating lane (corridor.py:89); 0.8 s elsewhere, so the arm equals p333 outside its zone (INFERENCE; section 10 checks it). T = 2.0, 3.0, 4.0 s |
| U30 | Z30 without `4a_1`: 0.8 s from the next 5-s decision on 4a (b_env.py:707-709) |
| Z16 | the zone at 1.6 s: in-range anchor and opponent |
| In-range | p333, the stored pick (none of 22 stored rules has less delay by point, EXPLORATORY), and os0_10_10; at 6,000 also os1_15_10. No control beside, never deciding |

**Equal exposure.** One long pick on 60 selection seeds at 5,300: lowest median paired delay against p333 among arms that passed T0, collisions at most p333's + 1 (planb.md:228), ties by list order, frozen before the verdict. The in-range rules had 240 stored seeds. At 6,000 nothing is picked.

## 5. Measures

Relation is to v3w's reward (b_env.py:842-843).

| Role | Measure | Relation |
|---|---|---|
| Deciding | `all_delay` (plant_sweep.py:347) | tied (speed and flow terms) |
| PASS conditions | flow `passed`; collisions, moving full-emergency events, `m_stuck_n` | tied; outside |
| Report-only | E by merge, slow minutes on 4a, TTT, delay on 4a and ramp 2 | tied |
| Report-only | close-following, braking at 3 m/s² | reward terms |
| Report-only | braking at 0.1 s (V367), `end_stop2`, fuel per km, jam share | outside |

## 6. Seeds proposed

The ledger shows no use from 7,485,000; the author must confirm.

| Seeds | One purpose |
|---|---|
| 7,480,000-002 (stored S5 rows) | identity replay; equality only |
| 7,485,000-009 | tool checks: T0, determinism, traced against untraced |
| 7,485,010-019 | lane-end counter trace |
| 7,485,020-099 | reserved: smoke repeats after a code fix only; never T0, selection or verdict (planb.md:357) |
| 7,485,100-159 | selection at 5,300 |
| 7,485,200-439 | verdict at 5,300, n = 240, used once |
| 7,485,440-499 | report rows at 6,000, n = 60 |

## 7. KILL rules

- **Statistic, level.** e = median(O − A) / median(O) × 100 over paired seeds, percentile bootstrap (planb.md:424); two-sided 97.5 %, Bonferroni m = 2 kept although one cell decides (planb.md:428). The pick uses other seeds; the opponents are an intersection (planb.md:429).
- **T0.** A long arm failing T0 in a cell is VOID there: the command did not bind in this zone; nothing about delay is closed. With none left at 5,300 the screen is VOID.
- **K1, at 5,300:** long pick against p333, os0_10_10 and Z16.
  - PASS: point at least 5 % against p333. Against each: lower bound above 0; flow at most 0.5 % lower (point); one-sided 95 % upper bound of the mean paired difference at most 0.02 collisions and 0.10 moving full-emergency events per run (planb.md:91-92). Stuck rows at most p333's + 2.
  - BOUNDED: upper bound against p333 below 5 %. Otherwise NOT SHOWN.
- **Screen.** KILL if BOUNDED: "at merge 2, where lane-end behaviour is not validated (PR-28), the picked arm is bounded below 5 % against p333; the other long arms that passed T0 lost a 60-seed selection". A PASS carries the same PR-28 clause. NOT SHOWN and VOID close nothing and allow no protocol.
- **6,000:** report-only; no PASS or KILL cites it. Each stage runs once.

**Why.**
- 5 %: V354's "coordination matters" rule on r2m3 at 4,600 and 5,300 (5 % against uniform 0.8 s, CI excluding 0, flow at most 0.5 % worse) and V462(1)'s delay tile; about half of E. Neither covers 6,000. Lower bound above 0 against each: planb.md:438.
- 3 % is dropped: the drafted "lower bound above 3 %" went with its reference; as a size it came from X1/X2 noise (planb.md:491, :519; paired SD 7-11 %, V435), against 16-17 % in S.
- "p333's + 2" (stored arms: 0-2 stuck rows of 240, EXPLORATORY), the 600-m zone, the last 100 m and 0.8 × T are design values with no record.

## 8. Null and power

EXPLORATORY planning: four stored merge rules' paired differences against p333, centred and shifted; os0_10_10 and a Z16 stand-in as the other opponents; n = 240; 1,000 studies per row.

| True effect against p333 | PASS | BOUNDED |
|---|---|---|
| 0 | 0.0 % | 99.7-100 % |
| 3 % | 0.0-3.7 % | 23-90 % |
| 5 % | 44-52 % | 1.4-1.8 % |
| 6 % | 81-95 % | 0.0-0.2 % |
| 7 % | 94-100 % | 0.0 % |

- With the 60-seed pick before it (one arm at the effect, three at 0; two noise cases): PASS 39-46 % at 5 %, 72-95 % at 6 %. A true 5 % arm loses the selection in 1-15 % of studies, so the KILL names the picked arm only.
- Half-width 1.2-2.7 points: a true 2 % is bounded in 48-100 %; at a true 0 the rows could bound about 3 %.
- Sign-flip null: lower bound above 0 in 1.2-1.7 % (nominal 1.25 %). T0 null, 10 of 10 seeds: 0.1 %.
- 6,000: the stored rows are 20 seeds under the training slowdown draw, paired SD 8-11 %, so 60 seeds give about ±3-4 points.

## 9. Runs × rate = cost

| Stage | Runs |
|---|---|
| 1: identity 15, determinism and traced twins 4, lane-end trace 8, T0 160 (8 arms, 10 seeds, 2 cells) | 187 |
| 2: selection at 5,300, 60 seeds, 5 arms | 300 |
| 3: verdict at 5,300, 240 seeds, 5 arms (pick, p333, os0_10_10, Z16, no control) | 1,200 |
| 4: report at 6,000, 60 seeds, 9 arms | 540 |
| Total | 2,227 |

- Rate (correction 7): 1,690 runs/h on 90 workers at $0.607/h, $0.36 per 1,000 runs (V493, V494). The 624 runs at 6,000 hold 845,125 vehicle-seconds against 578,720, so about 1.46 times slower (INFERENCE). About 1.5 h of runs; 1.8-2.2 machine-hours with setup and stage gates; $1.1-1.3. A T0 stop costs 187 runs, about $0.2.
- Build, my estimate: 16-22 h (critic_M.md:50: 2-3 days), with a lane-indexed rule class (ZonePattern reads road and position only, b_env.py:1041-1049) and T0's meters. Author time, apart: about 1.5 h.

## 10. Plant and verification effect

- **Identity.** S|p333, S|nc, S|os0_10_10 and S|r4a1 on 7,480,000-002 equal their stored rows on every key by value (V499). The new class with an empty zone equals stored S|p333 except on `name`, `cfg`, `lv`, `m_dec_want` and `m_dec_level_s`, whose length follows the level table (b_env.py:672; measure.py:130-136): entries 1-4 per zone equal, the fifth 0. Then this is a code change, not a plant change (planb.md:177).
- **Smoke.** `cfg` carries T and the zone; seconds at T appear inside the zone only; traced equals untraced (V386).
- **T0 (PR-10: "no r2m3 T0 record").** The zone at 1.0, 1.2, 1.6, 2.0, 3.0 and 4.0 s, U30 and p333; 10 seeds; both cells. Pass: `tau_mismatch` = 0 (plant_sweep.py:224); the median time gap of gated lane-0 ALKS in the last 100 m of `3_0` is above p333's in 10 of 10 seeds and at least 0.8 × T. Reported: lane-0 flow, gate-off share, ramp entries ahead of a commanded CAV, braking at 0.1 s.
- **Label, rows at 2.0-4.0 s:** "outside the plant's stated intended use: headway above the checked range 0.8-1.6 s (plant_vv_record_v0.md:9); merge-conflict and lane-change dynamics not validated (PR-08, PR-28)".

## 11. Cells added to the count (N = 91) and post hoc labels

0 added: rules only (cells_tested.md:5). Post hoc: cells, zone, values and thresholds follow the S6 results (planb.md:576).

## 12. Must-carry disclosures

- Exploratory, post hoc; a pass is headroom for a rule, never a claim.
- The target binds only behind an ALKS leader within 150 m (gate on in 56 % of ALKS-seconds under p333, EXPLORATORY), after a 0-5 s wait, rising 0.2 s per second, one level per 10-s hold (plant_sweep.py:70; b_env.py:707-711, :774-782). At the stored 73.9 km/h the 4.0-s command is reached 328-431 m into the zone; a 3-4 s target meters lane 0 (critic_M.md:33; both INFERENCE).
- LC2013 blocks a merge when the rear gap is below the follower's speed × tau / lcAssertive (MSLaneChanger.cpp:864-879): 79.4 m at 4.0 s and 100 km/h (critic_M.md:34). Results hold for this lane-change model only.
- 6,000 veh/h is above p333's capacity estimate (5,510-5,614 veh/h, an_delay_floor.md:43): under p333, edge 3 is below 60 km/h for a median 17 of 25 minutes (EXPLORATORY). No rule was tuned there.
- PR-28 is open. Capacity drop not settled (PR-26; V327: 11.7 % and 10.8 %, no null); the memo's "minimal drop" premise is withdrawn. No literature support is claimed.
- Run with V355 and the CAV contract set aside.

## 13. Expected outcome and probability (my judgement)

Expected: KILL. PASS 3 %; VOID at T0 5 %; BOUNDED 82 %; NOT SHOWN 10 %.

# PART 2. Skeptics' findings and handling

Verified = my own recomputation or reading (EXPLORATORY; `chk1.py`, `band.py`, `pw.py`, `null.py`, `lane.py`, `cfg.py` and their outputs in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/final_work/`) or the cited record. Section numbers are Part 1's.

| Id | Severity | Finding | Verified | Handling |
|---|---|---|---|---|
| M-all-1 | blocker | E is not a bound; K0 cannot fire; correction 2 is not met | Yes. Own run: delay rises 2,341 and E's numerator 1,459 veh-s per slow minute (62 %); edges 4-5 hold 22 % of that slope, edge 3 8 %; the slow-minute part is 14.6 % of mean delay; E reads 5.72 % in the 22 seeds with no slow minute. K0's upper bound fell below 5 in 0 of 2,000 resampled studies (smallest 8.79). 6,000 band rows: edge 3 is below 60 km/h for a median 17 of 25 minutes (13 in the 5 seeds with no slowdown) | Accepted in full. Section 3 now says "E is a descriptive split, not a bound", gives the two reasons in its table, and says "no tested ceiling is on record". K0 and the placebo line are deleted. K2 is replaced by "a DRL protocol with its bar set against the searched rule" (section 1). The ceiling question is a stage-0 sizing and decides nothing. The memo's rule 1 is withdrawn. Added for correction 2: what each simulated candidate loads and changes, and why none is run. The no-ramp arm goes to the author (Open 1) |
| M-all-2 | blocker | The 6,000 cell decides without a null, a sourced threshold or a readable reference | Yes. V354 (4,600 and 5,300) and V462(1) (X1 and X2 at 5,300) are the 5 % records the screen cites; neither covers 6,000. The 6,000 band rows are 20 seeds under the training slowdown draw; paired SD 7.9-10.7 % (os1_15_10, 3e); `end_stop2` 2,296 (2,578 with no slowdown) against 391.5 at 5,300; served flow about 5,527 veh/h. Partly: "5 % of delay is under 1 % of capacity" is an INFERENCE I did not recompute | Accepted, option 1 as the default: 6,000 is report-only; PASS and KILL are read at 5,300; the level stays 97.5 % (planb.md:428). A further change of mine, not the skeptic's: a report-only cell needs no pick, so its in-range selection (1,200 runs) is cut and it runs 9 arms on 60 seeds (540 runs). Option 2 goes to the author (Open 2) |
| M-all-3 | major | Section 8's table is not K1's rule: it tests one comparison, K1 asks 5 % against each opponent | Yes. Own run, 5 % against each of three: PASS 10-38 % at a true 5 %, 42-89 % at 6 %, 76-99 % at 7 %; with the pick before it 8-37 %, 40-91 %, 69-100 % | Accepted, option 2 as the default: K1 reads "point at least 5 % against p333; lower bound above 0 against each". Reason: V354 set 5 % against uniform 0.8 s alone, and planb.md:438 asks a lower bound above 0 against every opponent. Section 8 is recomputed for this rule, with the pick. The stricter form goes to the author (Open 3) |
| M-all-4 | major | A T0 stop is called a KILL; the 600-m zone, the "last 100 m" and "0.8 × T" have no record; the 4.0-s command needs 328-431 m | Yes: plant_sweep.py:70 (5-s decision); b_env.py:781-782 (0.2 s per 1-Hz update, so 16 s from 0.8 to 4.0 s); lane `3_0` runs at 73.9 km/h (own run) | Accepted. Section 7: an arm failing T0 is VOID, "the command did not bind in this zone; nothing about delay is closed", and the KILL sentence says "the other long arms that passed T0 lost…". The three values are labelled design values with no record (section 7) and go to the author (Open 5). The rise distance is a disclosure (section 12) |
| M-all-5 | major | Preconditions have no criteria; the trace checks a counter (PR-24), not lane-end behaviour; PR-28 stays open | Yes: plant_vv_record_v0.md:70 (PR-24), :77 (PR-26), :79 (PR-28) | Accepted. PR-26's estimator is "report-only: it changes no arm, rule or threshold; its hours are outside section 9". The trace is named a PR-24 counter trace and has a consequence. The KILL and PASS sentences carry "at merge 2, where lane-end behaviour is not validated (PR-28)". A pass allows "a PR-28 check with its own criterion". This conflicts with critic_M's order (PR-28 before any merge screen): Open 4 |
| M-all-6 | major | Identity cannot pass by value on the five-level path; a lane-indexed class and T0's meters must be built | Yes: b_env.py:672 and :790 (`lv` holds 3 × levels entries); measure.py:130-136; the stored S|p333 row holds 12, 4 and 4 entries (own read); ZonePattern reads road and position only (b_env.py:1041-1049) | Accepted. Section 10 lists the excepted keys (`name` added, because the arm's name differs) and what must still match. Section 9 names the class and the meters; my build estimate rises from 16-20 h to 16-22 h |
| M-all-7 | minor | Runs at 6,000 are slower: 3.3-3.8 machine-hours, $2.0-2.3 | Partly. Verified: 845,125 against 578,720 vehicle-seconds per run; $0.36 per 1,000 runs. My count of the old plan's 6,000 runs is 2,724, not 2,726. That run time follows vehicle-seconds is an INFERENCE | Accepted in method. The numbers change with the new plan: 2,227 runs, 624 of them at 6,000 at about 1.46 times the time; 1.8-2.2 machine-hours; $1.1-1.3; cap $3 instead of $4 |
| M-all-8 | minor | Name the side-constraint bound; spare seeds are for smoke repeats only; U30 returns at the next 5-s decision, not at 4a's start | Yes: planb.md:91-92; planb.md:357; b_env.py:707-709 with plant_sweep.py:70 | Accepted, all three (sections 7, 6 and 4) |
| Checked, sound | | Signs; disjoint seed sets; 0 cells added; no barred word | Yes: cells_tested.md:5; the ledger holds no 7,485,xxx seed | Kept. The new 6,000 report set (7,485,440-499) is disjoint from the others |

No finding is rejected.

## Open for the author

1. **No-merge reference (correction 2).** Default: none is simulated; stage 0 gives sizes (a 9.2 % split, 14.6 % tied to slow minutes), not a ceiling. Alternative: buy the no-ramp arm (p333 without ramp vehicles on the 240 verdict seeds, about 240 more runs, plus a per-route delay counter). It is a valid ceiling but a loose one (near 55 %, INFERENCE), and no 5 % rule on it can fire.
2. **6,000 veh/h.** Default: report-only, 60 seeds, no pick. Alternatives: drop it (624 fewer runs); or make it deciding, which needs a threshold approved by the author (none is on record), 240 seeds and an in-range selection among the 15 carried rules (about 2,100 more runs, about $1.1 more). Planning power there, from the skeptic's normal stand-in with the band rows' SD: PASS 49-51 % at a true 5 %, BOUNDED 50-81 % at 3 %.
3. **K1's PASS form.** Default: 5 % against p333 and a lower bound above 0 against each (PASS 44-52 % at a true 5 %, 81-95 % at 6 %). Stricter alternative: 5 % against each opponent (10-38 % and 42-89 %). It asks that headways above 1.6 s add 5 % over the same zone at 1.6 s.
4. **PR-28 order.** Default: the screen runs with PR-28 open and its sentences labelled; a PR-28 check follows only a pass. critic_M asked for PR-28 before any merge screen. The record holds no criterion and no reference for lane-end behaviour, so that order needs both written before it, at a cost in hours I cannot state.
5. **Design values with no record:** the 600-m zone, the last 100 m, 0.8 × T, and "stuck rows at most p333's + 2". They are fixed here before data and need approval with the screen. Z40 may fail T0 through zone length alone; it is then VOID and no statement about 4.0 s is made.
6. **Level.** Default: 97.5 % kept with one deciding cell (planb.md:428). At 95 % the intervals would be narrower; I did not compute that table.
7. **The approvals of section 2:** cap $3, the rental, seeds 7,485,000-499, the contract departure (as V273), and setting V355 aside.

Length: Part 1 holds about 1,330 words of prose and about 300 in tables, numbers and symbols not counted; it is above the 1,500 asked because the corrected rules, the reference candidates and the binding labels did not fit in less.
