# Judge (project rules and statistics): Screen M drafts

**Basis.** Own recomputation from the S6 rows, cell S, 240 seeds (EXPLORATORY; `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/M/judge_rules_work/chk2.py`): p333 median 126,296 veh-s; merge excess 9.20 % [8.48, 11.23] (95 %); paired SD 15.8-17.3 %. The drafts' stage-0 numbers and power tables agree with it. This replaces an earlier judge_rules.md, re-checked.

**All three pass on:** barred words (none); 0 cells added (cells_tested.md:5); post hoc label; disjoint sets from 7,485,000 (unused in the ledger); own cap; correction 7's $0.36 rate; no simulated no-merge reference, with reasons; a pass only "allows". All exceed 1,400 words. All end "otherwise KILL", so "not shown" also closes the direction.

**Defect shared by rigor and opponent (INFERENCE from code, not run).** A CAV starts at level index 0 and moves one index per hold (b_env.py:703, :707-710, :778). Under p333 (four levels, hold 10 s) it needs three steps to reach 0.8 s. A two-level table removes that on every road, so the long arms differ from p333 outside the zone; edges 1-2 hold 30.2 % of delay (an_delay_floor.md:28). Cheap's table (1.6, 1.2, 1.0, 0.8, 3.0) avoids it.

## draft_rigor: 7 / 10

Strongest:
1. The 5 % size is on record for this plant: V354 (5 %, CI excluding 0, flow at most 0.5 % worse) and V462(1).
2. Level right: 97.5 %, m = 2; selection on other seeds; intersection (planb.md:429). Nulls computed for the interval (sign-flip 0.85-1.15 % against 1.25 %) and for selection. My check: true 0 gives bounded KILL 99.8-100 %; true 5 % gives PASS 52-53 %.
3. Closures go to the author: V355, V273; a merge-2 pass is frozen by V482 (F16).

Verified: V354, V462(1), V482, V355; planb.md:228, :367, :428-429; b_env.py:479-482, :774-782, :924; `work_rigor/power2_out.txt`.

Fatal unless fixed:
- The level-table defect.
- T0 test (b) is an absolute gap (1.4 s for T = 2.0 s), not compared with p333, with no null (V244). Lane 0's mean gross headway is about 2.7 s (critic_M.md:33), so it may pass with no command (INFERENCE).
- PASS has no collision or full-emergency condition at the verdict (planb.md:332-333).
- "A KILL closes M and P1" is wider than the evidence: the bound covers the picked arm only.

Lesser: a second interval departs from the one convention (planb.md:424); identity on S6's "used once" seeds (planb.md:367), not 000-002 (planb.md:354); unlabelled inferences; no excess formula; no ceiling or power at 6,000.

## draft_opponent: 6 / 10

Strongest:
1. Family level: 16 comparisons, 99.69 %, with power at that level (my check: true +3 % gives PASS 49-57 %).
2. E has a formula and a placebo null (−1.25 %, −1.65 %, verified); K2 puts a number on what is left for a learner.
3. Plant checks in order (PR-26 null, T0 for seven values, lane-end trace); PASS carries flow, side tolerances and `stuck_n` = 0.

Verified: V496 (ASCH = lr1000_16_2), V490, V327; planb.md:204, :212, :438; MSLaneChanger.cpp:864-879; plant_vv_record_v0.md:9, :46.

Fatal:
- V355's KILL of fixed zone patterns is not named; A16-A40 are fixed patterns.
- "Identity" sits on 7,485,000-009, where no stored row exists.
- The level-set defect.
- Confirmation is a point rule with no interval (against V435); its `lcAssertive` runs change a plant parameter, against its section 10.
- Unequal exposure: untuned candidates against incumbents re-picked in the cell; a KILL still "closes M and P1".
- 3 % leans on planb.md:519, computed on X1/X2 rows (planb.md:491), not this cell.
- 16,850 runs, 5,600 of them a re-pick before any candidate gain: not an early, cheap KILL (CLAUDE.md).

## draft_cheap: 4 / 10

Strongest:
1. T0 is a KILL rule compared with p333, null computed (10 of 10: 0.1 %); a stage-1 stop costs 27 runs.
2. The five-level table; identity on 7,480,000-002 (planb.md:354; V493).
3. It finds that the 6,000 band rows carry the random training slowdown (cfg `perturb: random`, verified).

Verified: corridor.py:89; plant_sweep.py:71, :224; planb.md:424, :428; round_2.md:361; `work_cheap/power_out.txt`.

Fatal:
- The KILL has no bound. My check (n = 120, 97.5 %): a true +3 % edge is KILLed in 57-68 % per cell, a true +5 % (V462's win size) in 7-44 %.
- It closes every value above 1.6 s and the triggered form from one untuned 3.0-s arm; an always-on long target meters lane 0 (critic_M.md:33), unlike a trigger.
- Rule 1's 2.5-s line has no record (its own words), yet it can KILL the lever.
- One opponent, untuned at 6,000; no control in no table (planb.md:210).
- The branch statistic has no level and reopens a KILL.
- Section 5 has no reward classification; 2.0 and 4.0 s are not run.

## Winner: draft_rigor

Graft from opponent:
- E's formula and placebo; K0 at 6,000 on the verdict p333 rows; K2.
- PASS side conditions (planb.md:332-333) and `stuck_n` = 0.
- T0 on seven values (PR-10); PR-26's null and the lane-end trace before the verdict.
- Smoke check: `cfg` and the level histogram show T.

Graft from cheap:
- The level table (1.6, 1.2, 1.0, 0.8, T); identity on 7,480,000-002.
- T0 against p333, with its null, as a costed stop before selection.
- The "condition T" label on 6,000 figures; the post hoc and "given up" lists.
- A pass allows the PR-28 check and a rule search before any DRL protocol.

Cut or fix in the winner:
- KILL wording: "the picked arm is bounded below 5 %; seven arms lost a 60-seed selection; 'not shown' closes nothing".
- The second interval: an author decision, or out.
- Label inferences; state each interval's level; cut to 1,400 words.

Not checked: rigor's "82-96 %"; V195; the level-table effect's size.
