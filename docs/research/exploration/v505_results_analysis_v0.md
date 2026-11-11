# The two rules-only checks (M2 and EV): what the results mean (v0)

2026-11-11. Desk work only. Sources: the ledger rows on these checks, the recorded readings in `docs/research/results/v505_part1/`, and two small read-only scripts on the stored rows. Numbers marked "exploratory" come from those scripts or from rows that fed no verdict. Nothing here is a claim.

**Names.** M2 is the check of the second on-ramp: ramp cars were made to merge more pushily, to see whether recorded results depend on how SUMO lets cars wait at the end of the ramp lane. EV is the test of a rule that is told about a slowdown upstream. "The fixed rule" sets every automated car to a 0.8-second gap. "VOID" means the study stopped by its own rules before any verdict.

## 1. What each result means, and does not mean

- **M2 is VOID.** No pushiness level passed the safety bound, so no changed model was picked and no recorded result was re-read. The question "do our results depend on the lane end" is still open. It does not mean the results are sound, and it does not mean they are an artefact.
- **EV is VOID.** The slowdown was big enough, but under the fixed rule the queue on the second ramp had not drained by the end of the run. An event cost read on such a run depends on where the run stops, so the test was stopped. It does not say that being told helps or does not help. Recovery stays unanswered.
- **Both VOIDs close nothing.** They cost about $0.35 to $0.40 and showed that the checks, the stops and the code work as written.

## 2. The M2 finding

**Is "SUMO's stop-and-wait at the lane end shields the automated cars behind the merge" a fair exploratory reading?** Yes, as a description of this model. It is not a statement about real roads.

- In SUMO a ramp car changes lane only if the gap behind it is large enough for the follower to brake gently. The pushiness setting divides that needed gap. At level 2 the ramp car accepts half the gap. The follower must then brake harder than its normal limit, and that is counted as an emergency. So the emergencies follow from the way the model was changed.
- Other things that add to it: the automated car's normal braking limit (4.5 m/s²) and its half-second reaction step; the short 0.8-second gaps under the fixed rule, which leave less room (up to 4.5 extra emergencies per run against 1.3 without control); and the fact that only the merging car was changed. In real traffic the follower also gives way. That half was not modelled.
- **A larger hint sits in the same rows (exploratory, 60 days, rules only).** At level 2, under the fixed rule: stops at the lane end fall from about 740 to 46 per run, delay falls by about 10 %, seconds of close-following fall by about 75 %, and hard-braking seconds fall by about half. So in this model the lane end of the second ramp carries about a tenth of the fixed rule's delay and most of its close-following count.

**A cheap follow-up, and is it worth it?** Yes, in a different form. Do not change how pushy the ramp cars are. Lengthen the ramp lane at the second merge, or let followers give way. That reduces waiting without forcing unsafe merges. Rough size: two or three lane lengths, no control and the fixed rule, 60 days: about 360 runs, under $0.20, plus a few hours for the road change. It is worth it because the next step, approach C, is judged on close-following and hard braking, the two measures that moved most here.

## 3. The EV finding

- **What the undrained ramp queue says.** After the slowdown clears, a dense stream reaches the second merge. Under the fixed rule the gaps are short, ramp cars find fewer gaps, and their queue is still 3.4 vehicles above normal in the last five minutes (limit 2). Without control it is 1.1 above normal.
- **A hint (exploratory, sizing rows, 20 days).** The slowdown cost about 83,000 vehicle-seconds under the fixed rule and about 72,000 without control. The fixed rule still has far less delay in total. But it seems to pay at least as much for the event itself. That is where a controller that adapts after an event could gain. It is a hint for the recovery idea, not a result.
- **Stored conclusions.** It agrees with what the audit found: under the fixed rule the second merge runs close to its limit, and a push can leave it in a state it does not leave within the run. The delay tie in steady and truck conditions is not touched.
- **Approach C.** Its test conditions must drain, or its measures will depend on where the run stops. A slowdown of this size upstream is not usable as it is.

## 4. The CPU finding

- **What was found.** Every rule run repeats exactly on the new machine. The 30 policy runs do not repeat exactly.
- **How large it is (exploratory, my script on the 30 pairs).** In all 30, every traffic value is equal: delay, flow, close-following, braking, fuel. In 29 the only difference is one diagnostic number of the policy's network, at about one part in a hundred million. In 1 the policy also preferred a different gap level somewhere, with no effect on traffic.
- **What it changes for future comparisons.** Exact identity is the wrong test for a learned policy across machine types. Use two tests: traffic values equal, and network diagnostics within a small tolerance. Still, one flipped choice can change a run. So run every arm of one comparison on the same machine type, or re-run the policy arms on fresh seeds, as the M2 protocol already planned.
- **What it changes for the stored baseline.** No number changes. Add one line to the baseline's disclosures: the policy rows are tied to the processor type they ran on; rule rows are not. Name the processor in the record. The cause is most likely floating-point rounding in the network library [VERIFY].

## 5. What changes for the parked directions and for approach C

- **Recovery (parked):** still unanswered, and slightly more interesting after the EV hint. It needs a new event that drains, which is a new study.
- **Reliability, share of automated cars, jam waves, fuel, the earlier screens:** unchanged.
- **Approach C:** it moves up in risk, not down in interest. Its star and its charge both sit mostly at the lane end of the second ramp.

**Recommendation.** Go on to approach C's first, rules-only step, with three guards written into its protocol. First, report every measure split into "at the second merge" and "elsewhere", and name the "elsewhere" reading before data. Second, add the longer-ramp-lane check to C's model check, beside the 30 % and 70 % share check. Third, keep all arms on one machine type and test policy identity by traffic values. *Pros:* it uses what the two checks taught at almost no cost; it protects C's star from the weakest part of the model; it keeps the lane-end question alive without a second large study. *Cons:* the lane-end gap stays open in the verification record until the longer-lane check is read; the split halves the events behind each reading, so more days are needed. *Weaker alternatives:* repeat M2 with pushiness between 1 and 2 (the safety bound failed by a wide margin at 2, and a milder level may not cut waiting enough to count); re-size the slowdown and run EV again now (a new study, for an idea that is parked); pause C until the lane end is settled (it may never be settled inside SUMO); ignore the machine finding (it would mix machine types inside one comparison).

## 6. A paragraph for the verification notes or a status update

"Two rules-only checks were run under protocols fixed in advance. Both stopped by their own rules before a verdict, so they close nothing. The first tried to test whether recorded results depend on how the simulator lets ramp cars wait at the end of the second on-ramp lane. Making ramp cars merge more readily cut that waiting sharply, but it also produced emergency braking by the automated cars behind, above the bound set beforehand, so no changed model was adopted and the question stays open in the verification record. The rows suggest, without establishing it, that this lane end carries a notable part of the delay and most of the close-following count under short headways. The second check sized an upstream slowdown for a test of a rule that is told about the event. The slowdown was large enough, but under short headways the queue on the second ramp had not drained by the end of the run, so the test was not run. The checks also showed that rule runs repeat exactly across processor types, while the learned policies repeat on every traffic measure but not bit for bit. Later comparisons will keep all arms on one processor type."

## References

- Ledger: V505-V508 (approval and protocols), V512-V513 (criteria fixed before data), V514-V518 (rental and results), V509-V511 (approach C and the share row).
- Protocols: `docs/research/protocols/v505_common.md`, `v505_m2_merge_check.md`, `v505_ev_informed_rule.md`.
- Readings: `docs/research/results/v505_part1/pick.json`, `size.json`, `gate.json`, `ident.json`, `status.txt`.
- Rows: `v5b1_runs/v505_remote/m2_pick`, `m2_ident`; S6 rows of baseline v5. Scripts: `aim_scripts/ident1.py` and `aim_scripts/pick2.py`; means over 60 pick seeds; not a reading under the protocol.
- SUMO's gap rule at a lane change: `drl_win_directions_v1.md` §4.3 (source lines there). Lane-end gap: `docs/testing/plant_vv_record_v0.md`, PR-28.
- Automated-car braking limits: `plant_vv_record_v0.md`, PR-06.
