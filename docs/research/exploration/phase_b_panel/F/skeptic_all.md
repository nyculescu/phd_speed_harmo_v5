# Screen F: skeptic, all three lenses

EXPLORATORY = my recomputation from stored S6 TRUCK rows (240 seeds, already read for a verdict). Scripts, outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/skeptic_all_work/` (`sk1.py` to `sk4.py`, `*_out.txt`). "Reading" = `read6_v23_supplement.json`.

Found right: K1's table (sk2: KILL 1.000, 0.906, 0.534, 0.236, 0.005 at 0, 8, 10, 12, 15 %); stage 0; run counts, rates, dollars (V475, V490, V493, V494); code lines; correction 1's seeds (planb.md §6; `meta.json`); cells added 0 (cells_tested.md:5); no barred word.

**F-all-1. BLOCKER. K2 does not test "delay within 1 %"; §8's K2 line describes another quantity.**
- Evidence: K2 reads the 5-run mean against one run (planb.md:424). EXPLORATORY (sk1): against os0_10_10 the pooled effect is −0.58 %, the mean of the five single-learner effects +0.04 %; offset −0.63 [−0.86, −0.20] (95 %). Rules-only placebo (sk4): a pseudo-arm of 5 rules reads below its single-rule mean in 98 % of 168 combinations on delay (median −0.17), 95 % on close-following (median −1.55).
- At 480 seeds (sk3) K2 passes 0.905 at the stored differences, 0.757 when every learner ties p333, os0_10_10 and 3E-D_TRUCK, and 0.007 when every learner is 0.5 % worse. §8's "0.99 at a true tie" is a pooled tie (mine 0.984): each learner 0.1-0.6 % better. Against os0_10_10 a learner's margin is about 0.4 %, not 1 %.
- K1 too: with the edge stated as the single-learner mean, 12 % is KILLed 0.397, not 0.232 (sk2; the offset against 3E-C, −0.88 [−3.91, +2.38], is not shown). K1's source reads 10 % on single policies (round_2.md:200). The first round asked for this (an_s6_independent_measures.md:116).
- Change: §2 gets an author choice: (a) K1 and K2 read the mean of the five single-learner effects, pooled statistic beside; or (b) keep the pooled arm and write in §1 and §7 "pooled arm; about 0.4 % for a single learner against os0_10_10 (EXPLORATORY)". Replace §8's K2 line with the three numbers above; recompute §8.

**F-all-2. MAJOR. Recorded adverse rows are missing from §5 and §12.**
- Evidence: reading, `cells.TRUCK.map_report_only.p333`: congested km max −3.91 % [−6.52, −1.74] and mean −1.43 % [−3.04, −0.63], shown worse at 95 % and 97.5 % ([−6.96, −1.74]; [−3.35, −0.58]). §5 prints the max only against 3E-C, where it favours v3w; §12's stored costs omit both (planb.md:439).
- Change: §5 add "against p333: congested km max −3.91 % [−6.52, −1.74], shown worse; congested km mean shown worse". §12: "Stored costs: braking events, jam count, jerk against 3E-C; congested km mean and max against p333."

**F-all-3. MAJOR. A budget stop of stage 2 has no outcome.**
- Evidence: §4 says "no data-dependent stop"; §9 stops a stage above its cap. Stage 2 costs $10.4 against $12 at rental 1's rate (V490); rental 2 ran below plan, causes "not measured" (V493). Plan B's ceiling label (planb.md:238-239) is not carried.
- Change: §9 add "If the rate check projects stage 2 above $12, the continuation stops before generation 110's check; the screen ends 'stage 2 not run': no pass, no KILL; no shorter continuation is read."

**F-all-4. MAJOR. New generations are scored against stored reference rows that no check reproduces.**
- Evidence: cmab.py:208-209 loads stored rows; cma2.py:212 skips cached ones. p333's pool and check rows stay rental 1's at 96fde8d (`meta.json`). §2 reproduces S6 rows only.
- Change: §2 add "p333 on 7,480,150-229 and g098i00 on its 16 search seeds re-run on the rental and equal the stored rows by value (96 runs), before generation 100."

**F-all-5. MINOR. §1 says "at least 10 %"; K1 cannot bound it.**
- Evidence (sk2, EXPLORATORY): K1 passes 0.47 at a true 10 %, 0.09 at 8 %.
- Change: §1 "a point edge of 10 % or more with the lower bound above 0". §7 "K1's form and K2's margin are fixed in a V# before the rental."

**F-all-6. MINOR. The set-aside gives half its reason.**
- Evidence: reading, delay lower bounds: grid_os1_10_10 −0.68, os1_15_10 −0.64, below kept 3E-D_TRUCK's −0.57; §4 cites close-following only. EXPLORATORY: adding them leaves K2 at 0.905 (sk3).
- Change: print these bounds in §4, or keep both rules (960 runs, about $0.35).

**F-all-7. MINOR. A pass can be read as the claim.** 480 seeds at 97.5 % is confirmatory size; no later test is named. Change: §1 add "The screen's rows are not evidence for the sentence; the protocol uses fresh seeds."

**F-all-8. MINOR. Build and text.**
- To build: continuation (cmab.py:44-45, :51-52, :204-205); selection and pick (cmab.py:163 is bound to :43's seeds); seeds (plan6.py:25); a reader for K1-K4, fuel and jerk (read6.py has none). "12 h" has no record.
- Stage 2's "8 lowest admissible check losses": add "over generations 20-300".
- §2 owes a T0; §10 says none is owed.
- Sections 1-13 hold 1,908 words; the limit is 1,400.

Would I let this screen run as written: no.
