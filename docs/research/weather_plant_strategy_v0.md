# Weather plant checks (V207): what happens when the results come in

Status: proposal, written 2026-10-31 before any phase 2-4 outcome metric was read. Only the stop-rule fields (drained, collisions) of the 63 finished phase 2 days were checked. Becomes a decision once the author says OK.

## Purpose of the batch
The §5 checks answer four questions before any controller runs:
1. Is the wet plant valid (drains, no artefacts)?
2. Are the wet days distinct regimes, or near-copies of dry?
3. How are CAVs treated in rain (Q5)?
4. What crash scale k_s applies per wet state?

The next step (E) then asks whether the plant leaves any room for control at all.

## What Claude does without asking
- Lets the batch finish and runs the §5 analysis after each phase.
- Writes summaries to `docs/research/results/` and logs results as V# entries. Commits them; never pushes.
- Stops the driver unit only if a failure makes the remaining phases useless (a bug in our code, a deadlock). Otherwise later phases keep running and only their use waits for the author.
- Never: new seeds, new protocols, fan or cooling changes beyond V208, any v6 change.
- Interpreting the results (the "means" lines in the V# entry) waits for the author to switch to Extra High with ultracode on. Until then the numbers are reported only.

## Questions for the author, each with a default

| Id | When | Question | Default (Claude's recommendation) |
|---|---|---|---|
| A | collision replay done (about 1 h) | Accept the dry-day collision on seed 7,431,093? | If it is a SUMO lane-change artefact: accept. Every collision is counted and disclosed; a plant check fails only if a state has more than 1 collision in 30 days or any collision has the striking vehicle at ≥ 2 m/s. If our code caused it: fix it, re-run everything it touches. |
| B | phases 2 and 3 done | Q5: how do CAVs behave in rain? | Bracket if the CAV bound moves the wet-minus-dry congestion delay outside the base run's 95 % CI (same 10 seeds): carry both CAV variants into every wet cell, and any claim must hold under both. Otherwise keep the base (CAVs unchanged). |
| C | phase 2 done | Keep both wet cells? | A wet state is a distinct regime if the paired wet-minus-dry congestion delay (against the wet desired speed) has a 95 % CI excluding 0. A state that fails this is dropped from the controller study, reported once. The dry-reference delay is not used here, because it counts the rain slowdown as delay by construction. |
| D | phase 4 done | Adopt k_s? | Automatic if the live check matches the offline replay and p_max < 1. Otherwise stop for the author. |
| E | after §5 | Run a headroom check before adding more V176 mechanisms? | Yes. Claude drafts the protocol for approval first: no control, a tuned ramp meter, one tuned speed controller; dry and heavy cells; weather-blind and weather-scheduled tunings. Early KILL on this plant if no arm beats no control by ≥ 10 % (median paired difference, CI excluding 0). The scheduled-minus-blind gap is reported: it measures how much room weather leaves for adaptation. Seeds come from the V135 tuning partition, named for the author's OK. |

## Expected path (Claude's estimate, not a result)
- A: an artefact, so accept with the rule.
- C: both wet cells distinct on congestion delay; this is uncertain, since phase 1 showed the CAVs halving the rain effect.
- B: bracket, since the CAV bound roughly doubled the QDF effect in phase 1.
- E: decides whether the line continues.

## Timeline (estimates)
| Item | Expected |
|---|---|
| collision replay | about 12:30 |
| phase 2 | about 15:00 |
| phase 3 | about 17:30 |
| phase 4 | about 20:00 |
