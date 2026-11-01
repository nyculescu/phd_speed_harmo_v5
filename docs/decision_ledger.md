# Decision ledger

Started 2026-10-31 (V210). There is one entry per decision. Each entry gives the decision, its potential challenges (risks, assumptions, what a reviewer could attack), and its confirmed issues (problems that showed up after the decision, with evidence). `docs/decisions.md` stays the full log; this file tracks how decisions hold up. Entries before V210 are seeded only for the decisions the current weather batch depends on.

Status: **open** (proposed, not decided), **holds** (no confirmed issue), **holds, issue disclosed**, **changed** (superseded; the new V# is named).

## Open

None.

## Decided

### V187. ld32 human-driver calibration (2026-10-29)
- Decision: tau scale 0.8 and action-step scale 0.5 (human action step mean about 0.21 s, some 0.5 s). These are calibrated values, not field-sourced. They are the only one of 20 configurations that passes.
- Potential challenges:
  - Action steps below the sourced 0.3-0.4 s.
  - Short reaction steps combined with LC2013 can produce artefacts.
  - The 4 → 3 lane drop had no capacity drop.
- Confirmed issues: V209, a minGap intrusion (2.36 m bumper distance, no contact). A human car with a 0.5 s action step could not react to a cut-in it had not seen at its last action point.
- Status: holds, issue disclosed.

### V197/V198. Teleporting off on plant v190 (2026-10-30)
- Decision: no teleports; a jam must resolve itself. The squeeze-in rule failed.
- Potential challenges: deadlocks at the merge or lane drop on heavier days; long ramp waits (H-R5 on every day).
- Confirmed issues: none. Every finished day so far drained, including 41 wet days.
- Status: holds.

### V199. Incident passing zone f = 3 (2026-10-30)
- Decision: human tau × 3 within ±100 m of an active crash; η 0.532 against the field value 0.54.
- Potential challenges: calibrated on one straight 3-lane road in dry weather; the effect in rain was unknown.
- Confirmed issues: none. In rain, η against the wet QDF is 0.52 / 0.52 (V207 phase 1), inside the ±0.10 band.
- Status: holds.

### V204. Weather protocol (2026-10-30)
- Decision: whole-day dry, medium and heavy states; humans only (CAVs unchanged, Q5); R = 1.71; QDF calibrated to the L08 CAF.
- Potential challenges:
  - Q5: unchanged CAVs dilute the rain effect.
  - Q1: a whole day of rain at L08 intensities is a stress cell, not a typical day.
  - Q4: R covers all crash types.
  - Q10: assumes an unchanged capacity drop.
- Confirmed issues:
  - Q5, confirmed in V207 phase 1: the realized full-mix QDF ratios are 0.973 / 0.956 against the targets 0.926 / 0.871 (0.944 / 0.895 with the CAV bound). This goes to strategy row B.
  - Q10 is consistent so far (V206: drop unchanged within its CI).
- Status: holds, issue disclosed; Q5 is pending row B.

### V206. Rain calibration g = 1.12 / 1.23 (2026-10-30)
- Decision: confirmed at the first attempt.
- Potential challenges: speed and occupancy at capacity do not reproduce the field shift.
- Confirmed issues: that shift is too noisy to show (speed-at-capacity ratio CIs 0.82-1.10 and 0.95-1.12), disclosed. Any setpoint (ALINEA-type) claim across weather must state it.
- Status: holds, issue disclosed.

### V207. Weather plant checks (2026-10-30)
- Decision: phases 1-4 on seeds 7,431,080-109; stop for the author on a SUMO collision or a day that fails to drain.
- Potential challenges: stop rules written before collisions and minGap intrusions were told apart.
- Confirmed issues: the stop rule fired on dry seed 7,431,093 (V209). It was a minGap intrusion, not contact; the batch continues. Settled by V211.
- Status: holds, issue disclosed.

### V208. Away mode: 95 % CPU, pad 1,000 rpm (2026-10-31)
- Decision: applied on the author's word that they are leaving home.
- Potential challenges: the batch's 27 workers use about 85 % CPU, so the higher limit buys little.
- Confirmed issues: none.
- Status: holds.

### V210. Decision ledger started (2026-10-31)
- Decision: this file; every new decision gets an entry in the same turn, and confirmed issues are added when they appear.
- Potential challenges: two records to keep in step (this file and `docs/decisions.md`).
- Confirmed issues: none.
- Status: holds.

### V211. Collision rule A: contacts and minGap intrusions apart (2026-10-31)
- Decision: count physical contacts and minGap intrusions separately. Any physical contact keeps the V207 stop rule.
  - Intrusions are counted, reported per weather state and per controller arm, and disclosed.
  - An arm whose intrusion rate is above no control's (paired CI excluding 0) gets a safety flag; its cells are not claimed without the author.
  - Code: record the bumper-to-bumper distance at each SUMO collision event. Dynamics and hashes stay unchanged.
- Potential challenges:
  - The tolerance is Claude's choice, not sourced.
  - SUMO's lane-change check ignores the follower's planned acceleration. Controllers that create more stop-and-go near the lane drop may raise the intrusion rate.
  - A reviewer may read "SUMO collisions" as a plant defect. The answer is the physical-contact count, which so far is 0.
  - Events recorded before the code change (1 so far, V209) have speeds only. Each needs a replay to settle contact, about 25 min of one core for an 08:00 event.
- Confirmed issues: none yet.
- Status: holds.

### V212. Weather results strategy v1 (2026-10-31)
- Decision: rows B-E of `docs/research/weather_plant_strategy_v0.md` (B: CAV bound as robustness row; C: report-only, no cell dropped; D: automatic k_s; E: staged headroom check, E1 dry with early KILL).
- Potential challenges:
  - B: the bound (CAVs as cautious as humans) is unsourced at both ends; "not clearly worse" needs the harm margin of the later claim protocol.
  - C: wet cells kept even if they change little; their cost is carried until E sets their role.
  - E1: 6-point grids may miss the best setting and understate headroom; the per-seed oracle bounds this from above.
  - E1: the CAV harmonization rule is not built yet; its design choices bias headroom.
  - E1: 10 seeds give wide CIs.
  - E1: the forced-incident placement is one choice of time and place.
  - E1: the KILL tests dry only; a heavy-rain-only advantage is left to E2, which runs only if E1 passes.
- Confirmed issues: none yet.
- Status: holds.

### V213. E1 headroom-check protocol v1 (2026-10-31)
- Decision: `docs/research/protocols/e1_headroom.md` approved as recommended (Q1-Q8), the V212 row E design after three adversarial reviews (49 issues, 2 blockers, all resolved in its §14). Eight author questions (Q1-Q8).
- Potential challenges:
  - The compute grows from V212's about 22 h to about 34-38 h expected at 10 seeds, and about 69 h if the power rule needs 20 seeds.
  - The KILL is stated as "no gain ≥ 15 % with probability 0.80"; gains of 10-15 % can be missed.
  - The stalled-vehicle incident departs from V202 and needs its η check.
  - The meter actuator, the CAV cap profile and the MTFC gain range are Claude's choices, accepted only through T0 and the gain check.
- Confirmed issues:
  - The blocker η check failed (0.396 against 0.54 ± 0.05), V215.
  - The checkpoint review confirmed about 45 distinct code defects, 10 critical; §8 and §9.6 contradict each other on C1; "of any length" makes t_b a blip, V215.
- Status: holds.

### V214. Weather rows B and C: numbers (2026-10-31)
- Decision: none; report-only numbers under V212 rows B and C. Interpretation waits for Extra High with ultracode on.
- Potential challenges:
  - All-vehicle D is rebuilt from class means and regenerated class counts, because the batch code predates the E1 all-vehicle metric. It is exact for the paired bound-minus-base difference (same vehicles), and a weighted mean otherwise.
  - QDF is taken from the longest breakdown episode, which under the heavy bound starts in the morning, not at the PM peak.
  - The batch code predates V211, so collisions are SUMO events; the one dry event is the V209 minGap intrusion.
- Confirmed issues: none yet.
- Status: holds.

### V215. E1 checkpoint review and stage-0 amendments (2026-10-31)
- Decision: A1 a hold-at-speed-0 blocker diagnostic before the crash fallback; A2 fix every confirmed review defect to the protocol text, with tests; A3 t_b from the main PM breakdown (longest episode after 12:00, gaps < 10 min merged); A4 a C1 pass can rescue a cell where O_off failed; A5 T0 ALKS hold test over uncongested minutes, recovery test as a stop rule.
- Potential challenges:
  - A3 is set after a reviewer saw fragment drop values (no controller outcome); the 10-min merge gap is a choice.
  - A4 adds a route to a continue that §8 excluded; C1 runs on fresh seeds only.
  - A1 changes how the incident is held; if it passes, the I cell differs from V213 §5.2 in the hold only.
  - About 45 fixes at once can bring new bugs; the re-review of the diff covers this.
- Confirmed issues: none yet.
- Status: holds.

### V216. Weather row D: k_s adopted (2026-10-31)
- Decision: none beyond the V207 rule; k_s adopted automatically because the live check matched 10 of 10 days per wet state with p_max < 1.
- Potential challenges:
  - R = 1.71 is one literature ratio; the report rows 1.31 and 2.11 bracket it.
  - 10 live days per state check the code path, not the crash rate.
- Confirmed issues: none yet.
- Status: holds.
