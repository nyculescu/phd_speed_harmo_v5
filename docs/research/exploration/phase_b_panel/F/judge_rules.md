# Screen F: judge, lens = project rules and statistics

Checked against planb.md, decisions.md, cmab.py, cma2.py, `/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json` (fields by script), `/home/catalin/work/phd/v5b1_runs/planb_s34_remote/cmab/TRUCK_ttc/` and the drafts' outputs in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/`. Scores are judgement.

| Draft | Score |
|---|---|
| rigor | 8 |
| opponent | 6.5 |
| cheap | 6 |

All three: corrections 1, 3, 5, 7 applied; seed sets disjoint; 7,485,xxx has 0 ledger hits (my grep); 0 cells added (V487, cells_tested.md:5); post hoc label; planb.md:575 and :153 put to the author; 97.5 % from Plan B's m = 2 (planb.md:428-429); no barred word; a pass allows a protocol only; over 1,400 words.

## draft_rigor.md: 8

Strongest:
1. One 480-seed verdict set, v3w's rows fixed across both stages. Every §8 number matches `rigor_oc_out.txt` and `rigor_oc2_out.txt` (K1 KILL 0.530 at a true 10 %, 0.232 at 12 %; label-swap 1.05 % against 1.25 %).
2. Correction 1 exact: replay 0-99, generations 100-299 on pool 7,480,150-189 under planb.md §3.3, fixed budget, Plan B's check set for the shortlist only, fresh selection and verdict seeds, today's 3E-C kept.
3. Stage 1 costs $1.8 before any search; label-swap check before PASS (planb.md:486); the delay bound also faces 3E-D_TRUCK.

Fatal flaws: none found.

Verified exact: planb.md:428, :429, :438, :486; cmab.py:204-205, :224; reading values −3.18 (steady, os1_15_10), +17.44 (os0_10_10 lower bound), jam share −0.57 [−7.30, +11.32]; per-learner mean 12.68. Weak: 10 % is sourced to V462(1)'s tile, and V462(1) says "No tile is a verdict".

## draft_opponent.md: 6.5

Strongest:
1. Drops the 10 % point (written after 11.80 %) for planb.md:438's "lower bound > 0 and at least 20 per run", fixed before S6. Null shown: false pass 1.3 % against 1.25 %, KILL 0.114 at a true 12 % (`f_oc_out.txt`, exact).
2. No counting filter: all 23 stored opponents and no control rerun (planb.md:214, :210).
3. Location rows off roads 4a, 4 and ramp 2. I re-ran `f_stage0.py`: +9.05 % [+4.50, +18.73], 3 of 5 learners, reproduces (EXPLORATORY).

Fatal as written:
- Incumbent = lowest of about 120 losses on one 80-seed selection set shared by three searches. This repeats critic_F F4 and weakens the opponents.
- "Inside $40 per 7 days" is not shown. Plan B's rentals of 2026-11-08 to 11-10 total about $18.3 (V475, V494, V499); caps of $15 + $13 give about $46 (INFERENCE: a rolling window).
- 3E-G has no bounds or encoding; 26 parameters get 100 generations, so critic_F F5's "the budget decides" stands.

Other: $12.6 spent before any verdict (CLAUDE.md: KILL early and cheap); rule 3 relaxes planb.md:438's learner condition on delay; a third outcome; plant_vv_record_v0.md:77 says "gap", not "not settled". Verified exact: planb.md:438, V381(2), drl_win_directions_v0.md:86, jam count −8.57 % [−14.29, −4.29].

## draft_cheap.md: 6

Strongest:
1. Stage 1 for about $1.1: re-select the 8 stored shortlist candidates on fresh seeds, no new search. The 8 names, the 54 check losses and CMA seed 20261109 match `checks.jsonl` and `meta.json`.
2. The only draft that counts the $18.3 already in the window; staged caps; "$0 close" branches.
3. Delay bound with margin, level (one-sided 98.75 %) and sources (planb.md:228, :437, exact); 10 % sourced to round_2.md:200, a deciding rule (exact).

Fatal as written:
- Two independent 240-seed verdicts under the 10 % point rule. Its own §8: a true 12 % edge passes both at most 49 % of the time, so round 1's noise KILL returns.
- The delay test omits 3E-D_TRUCK, "the strongest delay opponent the family can give" (planb.md:232); the verdict omits no control (planb.md:210).

Other: row 0.4's "about 1 % or less" is wrong: the reading holds jam count −8.57 % and congested km max +3.85 % [+1.54, +6.15] (95 %). No learner rule; no label-swap check; 200 generations only. Verified exact: planb.md:575, the steady counts (3 rules; 16 of 23), `cheap/oc_out.txt`.

## Winner: draft_rigor.md

Graft from cheap:
- Stage 1 re-selection of the stored shortlist on its own fresh selection set (about $0.2).
- The window arithmetic ($18.3 + $12.2), staged caps, "$0 close" branches, "re-base the block against screens M and R".
- "One-sided 98.75 %" in K2; round_2.md:200 as the source of 10 %; the 1e-9 replay tolerance (cma2.py:49).

Graft from opponent:
- planb.md:438's edge rule beside K1 as the author's choice. Rigor's own output gives it at 480 seeds: KILL 0.985, 0.422, 0.101, 0.006 at a true 0, 5, 8, 12 %.
- The location and lane-change rows as report-only validity rows (PR-28); no third outcome.
- Jam count shown worse; the wider post hoc list (measure classes, margin, seed count); PR-26 as a carried limit.

Cut or fix in the winner:
- "Used once" is wrong: the verdict seeds are read at both stages.
- K4 has no null for collisions and moving full-emergency events. Compute it now or make K4 report-only.
- The 1 % margin is the draft's choice (planb.md:227 is a search hinge); the record has 2 % (planb.md:437) and D11's 5 %. At 1 % a true 0.5 % deficit is KILLed 52 % of the time and a pass is capped at 0.92. Show the 2 % row; the author picks.
- The two-rule deciding set is a filter set with stored rows in view (planb.md:214). Apply K1 to every rule arm that runs; rerun the other 19 (9,120 runs, about $3.3, my arithmetic) or name the set-aside.
- K3 keeps only the close-following half of planb.md:438; say so.
- §3: add jam count, oscillation +1.02 % [+0.55, +1.36] and congested km max.
- Write "EXPL", "OC", "R6", "D" as words; exact template headings.
