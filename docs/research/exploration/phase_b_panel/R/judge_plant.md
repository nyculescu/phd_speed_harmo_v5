# Screen R: judgement of the three drafts (lens: traffic engineering, feasibility, cost)

"OK" = I opened the cited line and it agrees. EXPLORATORY = computed on stored rows already read for verdicts; my scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/judge_plant_work/` (`t0_stored.py`, `rank.py`). Code lines: `planb_v23` copy.

## Common to all three

- Each draft's runs, machine-hours and dollars reproduce from correction 7's rates (V475, V490, V493, OK). None uses $0.53.
- X1 is not a cell in the Plan B tools (pb.py:27, :255; cmab.py:40, :42-43): a harness change in every draft.
- Stored rows already hold an r2m3 binding record. EXPLORATORY, `conf3/tune.jsonl`, X1 at 5,300, seeds 7,440,160-179, uniform 1.6 s against p333: `tau_on_match`/`tau_on_n` = 1.0000 in 40 of 40 rows; served flow −4.3 % [−5.0, −2.9]; mean speed −9.9 % [−11.5, −8.2] (95 %). Median `end_stop2`: p333 2,602; lr1000_10_1 2,378; os0_10_10 1,393; uniform 1.6 s 762.

## draft_cheap: 7.5 / 10

Strongest:
1. Staged KILL-only reads: under $1 at stage 1; $5.1-5.5 for 42,150 runs in full.
2. Stage 0 removes paid work: its delay re-rank of the 69-rule grid reproduces. Precondition 2 is right: the recorded delay win needs 5 % for 4 of 5 policies (confirmatory_3.md:108, OK) and read 0 of 5 and 2 of 5 (round_1_result.md:212; round_2_result.md:225, OK).
3. The near-gap rule contests the mechanism with an input the searched family lacks: column 14 (b_env.py:924, :935, OK); ZoneOwnState reads columns 0, 2, 4, 15 (b_env.py:1127-1128, OK).

Fatal as written (cheap to repair): n = 80. Its own output gives a 24 % KILL at the stored edge, 12 % at n = 120 (`work/cheap_null_power.out`), to save about $0.2.

Faults:
- The generation-40 read adds a data-dependent stop (excluded by planb.md:237) and a third look, to save at most $2.8.
- V398 is cited for X1's queue; its long runs were X2 only (rerun.py:87).
- No scheduler, no longer look-ahead rules (critic_R.md F4): under $1 saved.
- Near-gap: d cannot exceed 100 m (b_env.py:44, :935); rules decide every 5 s (plant_sweep.py:70), so d = 25 m may seldom bind (INFERENCE). Build of 10-12 h is credible.

## draft_rigor: 6 / 10

Strongest:
1. No new rule class. The LocalRule grid counts correctly (60 minus 12 existing = 48; conf3/common.py:33, OK); ASCH takes its library from files (asch.py:7, OK).
2. n = 160, a label-swap null, three pass labels fixed in advance.
3. The early-KILL check (planb.md:406, OK) and §13's note that closing PR-28 beforehand could spare the spend.

Fatal flaws: none.

Faults:
- No early read: the 40,640-row search ($4.7, 7.7 h) is always bought. K1 is an intersection (planb.md:429), so a KILL-only read adds no false pass.
- No arm acts at merge 2: the artefact is labelled, not contested. Its own forecast: 43 % labelled pass, 7 % usable.
- It re-runs 69 rules stored rows already rank (1,380 runs) and 11 carried rules stored at least 5.5 % behind (an_x1x2_delay_edge.md:29, :32; 1,760 runs).
- Look-ahead 700 and 1,500 m act as 600 and 1,400 m (b_env.py:998, :58); V398 misread, as above.

## draft_opponent: 6.5 / 10

Strongest:
1. Best artefact control: HYB needs no code (ZoneOwnState, b_env.py:1117-1129, OK); a three-part clean pass; it alone says X1's drain is unchecked.
2. Widest opponent set, with a KILL-only read at $1.4.
3. PR-10 uses an existing counter (plant_sweep.py:226-227, OK).

Fatal as written:
- K3 says "against any arm". If no control counts, stored rows fire K3 now (round_2_result.md:265, OK) and R ends at zero cost. If not (planb.md:437, :448), K3 is nearly idle: v3w has 44 % less close-following than p333 (EXPLORATORY, `rigor_work/power2.out`).
- "PR-28 control … a failure stops the screen". A failed hand-built arm is not a plant failure; the gate has no computed null; os0_10_10 acts on the whole road past 500 m (b_env.py:1082), so HYB's effect is unknown.

Faults:
- $14 against a $16 cap for its own 10 % clean pass; the second start costs $4.7.
- Build of "about 13 h" is not credible: the search start accepts p333 or one own-state rule (cmab.py:93-99); the long-window script is X2-only, no pack (rerun.py:87-89, OK); PR-26's estimator is uncosted. My judgement: 20-25 h.
- "MPC-F last on delay" is wrong: 11th of 23 (recorded_table_out.txt:13).
- Clean-pass part (c): 1,800-3,000 s holds no slowdown, so an edge there is merge discharge, not recovery (INFERENCE).

## Winner: draft_cheap

Graft onto it:
- From draft_opponent: HYB as a stage-1 arm; one 3E-D search, started from HYB if it leads p333 on the selection seeds, else from p333; the 20 longer look-ahead LocalRules; clean-pass parts (a) and (b); the 3,000-s run as a read-out by period, survivors only; "X1's drain is unchecked".
- From draft_rigor: n = 160; ASCH-delay after the search; the planb.md:406 check; the three pass labels; the label-swap null; the closed-paths list.
- From this review: the stored binding record as a stage 0 line.

Cut or fix in the winner:
- Cut the generation-40 read; correct V398's scope.
- The near-gap binding check reports, per d, the share of decisions with the trigger held.
- Define the "rules-only lane-end check" (no draft does), or state that R alone cannot allow a DRL protocol.
- Cost after the grafts (my estimate, correction 7's rates): about 47,000 runs, 12-13 machine-hours, $7-8 in full, $1.2 at a stage-1 KILL; cap $10.
- Ask the author how the $40 per 7 days counts Plan B's $17.50 (V490, V493).
