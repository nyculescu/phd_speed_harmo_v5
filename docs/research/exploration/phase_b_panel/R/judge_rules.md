# Judge (project rules and statistics): Screen R drafts

Citations were checked against the records and the `planb_v23` code. Power tables were compared with each draft's `.out` files; I did not re-run them. Power figures and stored-row numbers are EXPLORATORY.

Common to all three: no barred word; a pass stays "allows a protocol"; 0 cells added (cells_tested.md:5); correction 7's rates used, $0.53 never; X1 alone decides, 97.5 % is kept (planb.md:428), a two-cell alternative is given; seeds from 7,485,300, unused in the ledger (my grep). All exceed 1,400 words and need trimming.

## draft_rigor: 8 / 10 (winner)

Strongest:
1. The most complete null and power. Every §8 figure reproduces in `rigor_work/power.out` and `power2.out`: pass 0.0 / 5.1 / 53 / 91 % at true edges 0 / 2 / 3 / 4 %, n = 160; label-swap null 1.1 % against nominal 1.25 %. n = 160 matches V435.
2. Correction 4 is exact: the two-cell alternative states 2 × 1.25 % = 2.5 % and says V466 must be set aside.
3. Pass labels fixed in advance with records: PR-28-bound (planb.md:143; read6.py:487-499), trade-off (planb.md:141), opponent below plateau (planb.md:238).

Flaws, none fatal:
- It omits the recorded bar: a delay win is 5 % for 4 of 5 policies (confirmatory_3.md:108). 3 % at arm level is weaker, and the author is not asked to accept it.
- LocalRule look-aheads 700 and 1,500 m do not exist: the class floors to 200-m bins (b_env.py:58, :998), so they run as 600 and 1,400 m.
- No early read: the whole $7.0-8.2 is spent before a KILL can fire.
- "Read four times" cites critic_R.md:9, not primary records. "No delay-tuned opponent exists" ignores confirmatory 3's grid delay opponent (confirmatory_3.md:62).
- "The queue never clears (V398)" is an X2 record (rerun.py:87).
- One search start; §12 lacks braking against no control (s01_result.md:453) and the 15/24 correction (round_1_result.md:202).

Also verified: confirmatory_3.md:132; planb.md:160, :429, :438; s01_result.md:558, :561.

## draft_opponent: 7 / 10

Strongest:
1. The widest opponent set: 15 carried rules, 3 grid picks, HYB, two 3E-D starts, ASCH-D. HYB matches os0_10_10 (conf3/common.py:39) and ZoneOwnState (b_env.py:1117-1129).
2. Plant checks before any v3w row: a T0 record for r2m3 (PR-10, plant_vv_record_v0.md:46; plant_sweep.py:225-227), PR-13, a PR-28 manipulation check.
3. Closure cited to primary records (round_1_result.md:212; round_2_result.md:282, :239); an early KILL-only read at about $1.4.

Fatal as written:
- K3 fires "against any arm" and has no null. If no control counts, K3 already fires on recorded rows (−16.6 % [−25.1, −8.4], 95 %, round_2_result.md:265) and the screen cannot pass. Its scope must be stated.

Other flaws:
- Clean-pass clause (c), K1 on a 3,000-s window, has no null and no stored X1 variance.
- Seeds 350-369 serve three purposes.
- "MPC-F last on delay" is wrong: 11th of 23 (recorded_table_out.txt:3-25).
- "Metric survives, gate failure (planb.md:438)": the record reads "metric win, gate failure", planb.md:441.
- PR-10's 0.99 has no record. A HYB search start needs an unlisted code change (cmab.py:93-99).
- $14 under a $16 cap, for a screen it rates 65 % KILL.

## draft_cheap: 6.5 / 10

Strongest:
1. The only draft that makes the weaker bar an author decision: 5 % for 4 of 5 (confirmatory_3.md:108), read 0 of 5 and 2 of 5 (round_1_result.md:212; round_2_result.md:225); 1 of 5 on pooled stored rows (an_x1x2_delay_edge.md:80).
2. KILL-first staging: stage 1 under $1. The arithmetic holds.
3. The near-gap rule reads observation column 14 (b_env.py:924, :935), which the searched family does not (b_env.py:1128).

Fatal for a pass (a KILL stays valid):
- The opponent set is not the strongest. It drops the scheduler, every LocalRule beyond the old grid, and 11 carried rules, lr1000_16_2 among them. A pass would not answer the screen's question.

Other flaws:
- n = 80: its own table KILLs a true 4.2 % edge 24 % of the time, on three rules only; 120 seeds halve that for about $0.2. Its 3 % record (planb.md:519) is for n = 120.
- Near-gap d = 100 m sits at the input's clip: the column reads 100 m when no vehicle is there (b_env.py:44, :924). "Within 100 m" is always true unless the inequality is strict.
- The stop at generation 40 departs from "no early stop" (planb.md:229); stated, needs approval.
- The two-cell alternative omits that V466 must be set aside; "at most 5 %, two-sided" is loose.

## Winner: draft_rigor

Graft from draft_cheap:
- §2 item 2, the weaker-bar decision, with "without this decision R closes at stage 0, at zero cost".
- The near-gap rule, with a strict "below d" and d of at most 75 m.
- §12: the edge in vehicle-seconds and vehicles served.
- The zero-run grid re-rank row.

Graft from draft_opponent:
- The early KILL-only read after the carried and grid arms.
- HYB as a fixed arm, with its `end_stop2` manipulation check.
- The PR-10 T0 record and the PR-13 check, on their own seed set.
- The primary closure citations; the 15/24 correction; braking against no control; "V398 is X2, X1 unchecked"; "X1's two events never occur in training" (cells_tested.md:29).

Cut or fix in draft_rigor:
- Look-aheads to 600 and 1,400 m.
- Replace critic_R.md:9 with primary records; reword "no delay-tuned opponent".
- Put the 5 % recorded bar beside 3 %.

Outside R: seeds 7,485,300-699 collide with the F and M drafts (F rigor: 7,485,200-679). The synthesis needs one partition.
