# Weather plant checks (V207): what happens when the results come in

Status: proposal v1 (2026-10-31), revised after Claude's review of rows B-E. Row A is decided (V211). No phase 2-4 outcome metric has been read; only the stop-rule fields were checked (phase 2: 90/90 drained, 0 teleports, 0 SUMO errors, 1 minGap intrusion). Becomes a decision once the author says OK.

## Purpose of the batch
The §5 checks answer four questions before any controller runs:
1. Is the wet plant valid?
2. What do the wet cells look like?
3. How are CAVs treated in rain (Q5)?
4. What crash scale k_s applies per wet state?

The next step (E) asks whether the plant leaves any room for control.

## What Claude does without asking
- Lets the batch finish and runs the §5 analysis after each phase.
- Writes summaries to `docs/research/results/`, logs V# results with ledger entries, and commits. Never pushes.
- Stops the driver only if a failure makes the remaining phases useless.
- Never: new seeds, new protocols, fan changes beyond V208, v6 changes.
- Interpretation waits for the author to switch to Extra High with ultracode on; until then, numbers only.

## Rows

| Id | When | Rule |
|---|---|---|
| A | decided, V211 | Contacts stop the work; minGap intrusions are counted, disclosed and flagged per arm. |
| B | fixed now, before phase 3 data | The base keeps CAVs unchanged in rain. The CAV bound (CAVs get the human g and SAF) is a robustness row in every wet-cell evaluation. Tuning and selection use the base only. A claim in a wet cell must hold under the base and must not be clearly worse under the bound (the harm margin of the claim protocol). Phase 3 bound days are report-only: bound minus base, paired on the same 10 seeds, in the primary metric (delay against the dry desired speed, the same reference in both variants) and in bottleneck QDF. |
| C | phase 2 analysis | Report-only, nothing is dropped. Per wet state: the paired wet-minus-dry effect with 95 % CIs on congestion delay (wet reference) and on the primary metric (dry reference), plus breakdowns, ramp waits and TTT. Each wet cell's role is set after E. If weather scheduling buys something (scheduled minus blind, T2 G reported), it is an adaptation regime. Otherwise it is a robustness row, where a controller must not be clearly worse. |
| D | phase 4 | Automatic: adopt k_s if the live check matches the offline replay and p_max < 1; R rows 1.31, 2.11, 1.0 reported. If the base-to-bound difference in expected crashes matters for a later claim, a bound k_s is computed from the 10 phase 3 bound days with the same rule. Disclosed: if Σw_wet < Σw_dry then k_s > R × k, meaning a higher risk per close encounter, which stands in for the unmodelled friction loss. |
| E | after §5, protocol for author approval first | Staged headroom check, designed so that a KILL comes early and cheap. **E1** (realistic demand, dry; about 260 day runs, about 22 h at the measured 12 days per hour): no control; ALINEA at the ramp32 meter with the V190 limits; one CAV speed-harmonization rule upstream of the lane drop; coarse grids of about 6 points each; 10 fresh tuning seeds; crash-free days plus one forced-incident day set (V202 placement, the same in every arm, so the arms stay paired). The informed oracle is the best grid point per seed. **Early KILL** if neither the tuned controllers nor the oracle beat no control by ≥ 10 % (median paired difference in the primary metric, CI excluding 0). **E2** (only after E1 passes): heavy-rain grids on the same seeds; weather-blind (pooled) and weather-scheduled tunings from the same runs; evaluation on 30 fresh seeds with stochastic crashes (k, k_s). Seeds: unused parts of the V135 tuning and evaluation partitions (7,430,200-399 and 600-799; 220-229 are already used), named for the author's OK. |

## Rejected options (Claude's review)
- **B as first drafted** ("bracket if the bound moves the effect outside the base CI"). It is a data-dependent fork that will almost surely fire, since slower CAVs must raise delay. It also compared an estimate with the other arm's CI instead of a paired difference, and used the wet reference, which changes for CAVs under the bound.
- **B: bound as a second base** (tune and select under both). This roughly doubles tuning cost in wet cells for an unsourced CAV behaviour.
- **B: a half-way CAV response.** Arbitrary; no source.
- **C as first drafted** (drop a wet cell if its CI includes 0). With 30 paired seeds, any rain effect will be significant, so the gate says nothing. Distinct for a regime claim means the best parameters differ, and that is measured in E, not in §5.
- **E with full grids on 20 seeds in both cells.** About 1,000 day runs, about 85 h. The staged design reaches the KILL decision in about 22 h.
- **E with a VSL for human drivers as the speed controller.** Level-dependent compliance (V176) is not modelled yet, so full compliance would overstate the headroom.
- **E on crash-free days only.** It could KILL a plant whose headroom lies in incident management. Stochastic crashes alone are unpaired across arms (control changes the encounters), which is why the forced-incident set is there.
- **E on peak-hour windows** (`--hours`). It saves compute, but its days are not comparable with the §5 reference days, and it changes the vehicle draws.

## Expected path (Claude's estimate, not a result)
- C: both wet cells show a clear rain effect.
- B: bound minus base is clearly positive.
- E1: the deciding step. The prior expects a KILL: published hybrid gains are 1.5-6 %, and metering was killed on the p1c plant.

## Timeline (estimates)
| Item | Expected |
|---|---|
| phase 3 | about 14:00 |
| phase 4 | about 16:30 |
| E1 protocol draft | after phase 4; runs only after approval and seed check |
