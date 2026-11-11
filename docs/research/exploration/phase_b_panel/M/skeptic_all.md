# Skeptic (all lenses): Screen M, synth.md

EXPLORATORY = recomputed here from stored S6 cell S rows (240 seeds) and the 6,000-veh/h band rows (20 seeds under the training slowdown draw, 5 with no slowdown). Scripts and outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/skeptic_work/`. No simulation ran. Line numbers are synth.md's.

**M-all-1 (blocker). E is not a bound and K0 cannot fire; correction 2 is not met.**
- EXPLORATORY: per merge-2 slow minute, `all_delay` rises 2,341 veh-s and E's numerator 1,459 (62 %). E leaves out edges 4 and 5 (22 % of the slope) and edge 3 (8 %). The slow-minute part is 14.6 % of mean delay, above E's 9.20 %; with no slow minute (22 seeds) E still reads 5.72 %.
- K0 at 5,300: the upper bound fell below 5 in 0 of 4,000 resampled studies. At 6,000 its guard is false in stored rows: edge 3 is below 60 km/h for a median 17 of 25 minutes (13 in the 5 seeds with no slowdown).
- Change: line 25, "E is a descriptive split, not a bound". Line 33, "No sound ceiling is on record; question (a) stays open". Delete K0 (line 78) and line 100. Line 81: "K2 is set in the later protocol, against the searched rule".

**M-all-2 (blocker). The 6,000 cell decides without a null, a sourced threshold or a readable reference.**
- Line 101 says "power unknown"; V244 needs the null before the run. Stored band rows give one: paired SD 8-11 % of p333's median (EXPLORATORY). Yet this cell alone can pass the screen (line 80).
- V354 fixed 5 % for 4,600 and 5,300; V462(1) for X1 and X2 at 5,300. At 6,000, 5 % of delay is under 1 % of capacity (judge_plant.md:10, INFERENCE), and `end_stop2` is 2,296-2,578 per run against 391.5 at 5,300.
- Change, lines 40 and 80: "6,000 is report-only; PASS and KILL are read at 5,300; the level stays 97.5 %". Or keep it deciding with an author-approved threshold and these rows (EXPLORATORY, normal stand-in): PASS 0 % at 0, 49-51 % at 5 %, 88-94 % at 6 %; BOUNDED 50-81 % at 3 %.

**M-all-3 (major). Section 8's table is not K1's rule.** It tests one comparison; K1 needs 5 % against each opponent (line 79). EXPLORATORY, against p333, os0_10_10 and a Z16 stand-in: PASS 10-40 % at a true 5 % (table: 49-53 %) and 43-90 % at 6 % (table: 86-96 %); with the 60-seed pick before it, 37-90 % at 6 %. Medians do not add: 5 % against p333 goes with 3.8-5.1 % against os0_10_10. The 0 % row and the BOUNDED column hold. Change: replace the PASS column; or line 79, "point at least 5 % against p333; lower bound above 0 against each".

**M-all-4 (major). A T0 stop is called a KILL (line 77).** T0 tests the 600-m zone, the "last 100 m" and "0.8 × T"; none has a record. The command waits 0-5 s (plant_sweep.py:70), then needs 16 s to reach 4.0 s (b_env.py:781-782): 328-431 m at the stored 73.9 km/h (INFERENCE). Change: "with none left, the cell is VOID: the command did not bind in this zone; nothing about delay is closed". Line 80: "the other long arms that passed T0 lost…".

**M-all-5 (major). Preconditions without criteria; PR-28 stays open.** Line 21's trace checks a counter (PR-24), not lane-end behaviour; line 19 names no consequence. Change: line 19, "report-only here; it changes no arm, rule or threshold; its hours are outside section 9". Lines 9 and 80: add to each PASS and KILL sentence "at merge 2, where lane-end behaviour is not validated (PR-28)". Line 8: "a PR-28 check with its own criterion" for "closing PR-28".

**M-all-6 (major). The identity check cannot pass by value on the five-level path (line 117).** `lv` has 3 × len(headways) entries (b_env.py:672; stored 12). `m_dec_want` and `m_dec_level_s` have len(headways) (measure.py:130-136; stored 4). Change: "every key equal by value, except `cfg`, `lv`, `m_dec_want` and `m_dec_level_s`: the first four entries per zone equal, the fifth 0". To build: a lane-indexed rule class (ZonePattern reads road and position only, b_env.py:1041-1049); T0's meters.

**M-all-7 (minor). Cost.** The arithmetic holds (4,327 runs, $1.55 at V493-V494's rate), but 2,726 runs are at 6,000, each with 845,125 vehicle-seconds against 578,720 (EXPLORATORY). INFERENCE and change for line 112: 3.3-3.8 machine-hours, $2.0-2.3, under the $4 cap.

**M-all-8 (minor). Wording.** Line 79: name the bound, "one-sided 95 % upper bound of the mean difference" (planb.md:91-92). Line 70: "smoke repeats after a code fix only; never T0, selection or verdict" (planb.md:357). Line 45: U30 returns to 0.8 s at the next 5-s decision on 4a, not at its start (b_env.py:707-709).

**Checked, sound:** signs; disjoint seed sets; 0 cells added (cells_tested.md:5); no barred word.

Would I let this screen run as written: no.
