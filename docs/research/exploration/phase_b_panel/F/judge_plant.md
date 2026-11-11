# Screen F: judgement, lens traffic engineering, feasibility and cost

Citations checked by me in the code, planb.md, the ledger, `read6_v23.json` and `planb_s34_remote/cmab/TRUCK_ttc`. My scripts: `jp_checks.py`, `jp_r6b.py`, `jp_sc.py` in `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/`. "Fatal" = must be fixed before approval. I recomputed every cost line at the given rates: no error in any draft.

| Draft | Score | Cost, both stages | Spend before the first reading |
|---|---|---|---|
| rigor | 7.5 | $12.2, 20 h | $1.8 |
| cheap | 6.5 | $7.1, 12 h | $1.1 |
| opponent | 5.5 | $25, 39 h | $12.6 |

## draft_rigor: 7.5

Strongest points:
1. The delay margin (1 %) equals the free delay slack of the rule search (planb.md:227; cmab.py:48, verified). EXPLORATORY (mine): 1 % of delay is about 0.7 s per vehicle of the flow count in TRUCK (median 161,493 veh-s over 2,181 `passed`, p333; plant_sweep.py:29, :347). Margins are small in traffic terms, so matching the search is the right basis.
2. One 480-seed verdict set serves both stages; stage 2's verdict costs 480 runs. INFERENCE: conditioning on a stage 1 pass raises stage 2's false-pass rate by at most 1 / P(stage 1 pass). The continuation is implementable: `evals.jsonl` holds 2,400 records (replay cmab.py:220-225; refusal :204-205).
3. Keeps planb.md:438's flow, collision, emergency-braking and drain conditions and the label-swap null (planb.md:486).

Fatal flaws:
- K4's collision and full-emergency nulls are left "to be computed": a gate without a null (V244). v3w has 1 collision in 1,200 TRUCK runs, the rules 0 in 5,520 (an_s6_independent_measures.md:68).
- K2 is read on the pooled arm, which reads about 0.6 points low on delay (drl_win_directions_v0.md:86). At the stored values K2 alone fails 8 % of studies (`rigor_oc2_out.txt`: 0.916). An artefact can decide.

Other: stage 1 adds no new opponent; no plant-artefact control; no host-loss rule.

## draft_cheap: 6.5

Strongest points:
1. Stage 1 needs no search. Its 8 candidates match my recount of `checks.jsonl` (54 candidates), and each stores `params`. EXPLORATORY: g065i01 reads −32.22 on the check seeds at delay −1.83 %, beside g098i00's −32.53.
2. The only draft that counts the spend already inside the 7-day window (at least $18.3: V475, V494, V499).
3. A stated "given up" list; fresh seeds for each selection and verdict.

Fatal flaws:
- Its own table: a true 12 % edge passes both verdicts at most half the time, and g098i00 decides twice. A KILL "closes F" on close to a coin.
- Unequal slack: v3w may be 2 % worse on delay; the rule was penalised above +1 % and no +2 % search runs (critic_F.md:44 stays open).
- No flow, collision, emergency-braking or drain condition in the KILL rules. A pass could hide a throughput loss, a co-headline measure.

Other: 200 generations may not finish the search; no plant-artefact control.

## draft_opponent: 5.5

Strongest points:
1. The only draft that controls plant artefacts: a location guard on `m_road_ttc3` (measure.py:376), lane-change and half-second rows (measure.py:377; plant_sweep.py:158), T0 for PR-10 with `tau_mismatch` (plant_sweep.py:224; plant_vv_record_v0.md:46). All fields exist.
2. The richer family has a form: 6 named parameters whose inputs exist (b_env.py:925-935; LocalRule :991-1026). The author decides whether it is non-learning.
3. The edge rule uses numbers fixed before S6 (planb.md:438). Best curve: KILL 0.114 at a true 12 % (`f_oc_out.txt`).

Fatal flaws:
- $12.6 and 16.4 h of search run before the first reading, though today's arms alone give its 14 % KILL. This breaks the early-KILL rule.
- "$25, inside $40 per 7 days" is wrong before about 17 November, given the $18.3 above.
- 3E-G: 26 parameters, 100 generations. 100 did not settle 20 (`pick.json`: "not converged at 100 generations"), so the budget decides (critic_F.md:46). It needs a new rule class with roadside access, a 26-parameter encoder (cma2.py:40, :63 fix 20) and a start from a stored vector (cmab.py:93-99 refuses). 9 h is low; my judgement 14-18 h.
- Each incumbent is the best of 120 candidates on 80 seeds. That noise weakens the pick.

Other: 21 distant rules re-run (5,040 runs, $1.8) though the next closest lower bound is +17.44 % (`read6_v23.json`, os0_10_10). A pass is possible at a 2 % edge (20 of about 950 s per run).

## Winner: draft_rigor

Graft onto it:
- cheap: the re-picked stored rule as a stage 1 arm (about 1,080 selection rows and 480 verdict runs, $0.3); the 7-day window sum; a cap per stage; the "given up" list.
- opponent: the location guard as a third outcome, never a KILL; the validity rows; T0 on 2 smoke seeds; PR-09 per new rule; "at least 20 s per run" beside the 10 % point.

Cut or fix in it:
- Compute K4's nulls now, or make K4 report-only.
- Add per-learner delay points to K3 (as planb.md:438); print the pooled-arm bias beside K2.
- Add a rate check after 30 minutes with a stop. 5,280 rows/h came from an EPYC 7663 (V490), 1,690 runs/h from a Xeon 8163 (V493). INFERENCE: a slower host could push the $9.4 search past the $15 cap.
- Host loss (as V494): re-run stage 1's 4,800 rows on the new host, $1.7.
- A pass with the plateau label unmet is a pass at budget; say so.
- planb.md:428's m = 2 covers SURGE and TRUCK, not S and TRUCK: reword. Cut to 1,400 words.

Stored rows settle steady traffic in all three drafts.
