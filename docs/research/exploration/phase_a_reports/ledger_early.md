# ledger_early: rows V1-V299 (docs/decisions.md lines 9-318)

Coverage: every row's lead skimmed; about 110 rows read in full (V77-V103, V112, V116, V130-V149, V152-V155, V158-V176 selected, V180-V203 selected, V204-V216, V220-V225, V236-V258, V261-V299). Rows V1-V68 were read as leads only. Result notes cited by the rows were not opened. Every "Lesson" is this reader's INFERENCE.

## (a) Lines where adaptation or learning did not pay

1. **Self-calibrating safety margin (V83-V87).** Closed VALID-ONLY, no paper (V85). The row gives no effect size. Recorded reason (V86): "it does not bind against ACC gaps; the freeze rival is as good"; V87: "fixed per-regime tables matched online calibration everywhere". Lesson: test that the lever binds (gate G1) and include a "calibrate once, then freeze" rival.
2. **Eco-approach at signals, screen #2 (V82).** "STOP (no headroom)". No number in the row. Lesson: a one-page oracle screen stops a line cheaply.
3. **Detector-fault metering, screen D1 (V90, V101).** After the meter bug fix the healthy feedback meter is "−10 % vs a constant rate [CI −54, +9] (was −49 %)". Reason (V90): constant demand and no disturbance, so "detector faults cannot matter by construction". Lesson: a screen must contain the variation the adaptive arm is meant to exploit.
4. **Incident screen D2, P1, P1b, C1 (V94, V101-V103, V112, V116).** Per-type plan beat the no-incident controller (10-35 % by the paired convention, V99; before the meter bug fix of V100); C1 gave "16.2 % [7.3, 23.7]" (V116). All withdrawn as claims (V256): measured on a "single, unrealistically large (about 42 %), near-deterministic zipper + Flow-IDM drop"; about half of C1's gap is drain at 900 veh/h, against a PI opponent worse than no control on window TTT (V255). V94's "fixed tables always win" reading was itself withdrawn (V101). Lesson: a gain against no control can be the plant's artefact; check the plant before the controller.
5. **Mainline metering on the calibrated BN4 (V147, V149).** Best constant rate "6.1 % worse than no control", CI [−18.3, +3.0] s/veh; best PI-ALINEA "rel −0.3 %", CI [−1.7, +4.6] s/veh. KILL stands, but the "realistic 5-8 % drop" premise does not (V155, V255(4)). V155 critic X1: fluid ceiling "about 6-10 %" for any mainline meter, "RL included" (estimate, not verified). Lesson: bound the headroom by a fluid estimate before building.
6. **E1-lite on v199 (V238-V243).** ALINEA 1.05 "+0.083 [-0.005, 0.151]", UNCLEAR; all six MTFC (CAV speed-cap) arms "clearly worse" (−0.217 to −0.361). Best-of-9 null floor: mean +0.065, p95 +0.142 (V241). Reason (V242, V244, inference in the record): no capacity drop on v199, so control "can only move where the queue sits". Lesson: without a drop, delay headroom is redistribution; n = 20 could not separate 0 from +10 %.
7. **B, coordinator PPO with speed-cap offsets, runs 1-3 (V266, V270, V272).** Run 1 near uniform; runs 2-3 "roughly match the best fixed offset"; "No policy shows a flow gain". Reading (V271, untested): "the actuator can only slow". Lesson: sweep the fixed settings of an actuator before training on it.
8. **B, zone-headway PPO, runs 4b and 5 (V279, V285).** Run 5: "0 of 3 policies pass"; PPO "found the same lever as the rule". Run 4b is not a test of learning (wrong penalty, V283). Lesson: once a rule holds the lever, the learner has to beat that rule, not no control.
9. **Per-CAV PPO, C runs 1-4 (V288-V293).** 0 for 4, but the per-vehicle reward never reached training (V294); they count only as shared-reward, no-safety policies. Lesson: four runs were explained before the reward was checked in training mode.
10. **Per-CAV PPO with the intended reward (V297-V298).** Passed validation at 5,300 (3 of 3), failed fresh seeds (1 of 3). Against p303: flow "+0.5 [-0.2,+0.8], +0.8 [-0.2,+1.8], -0.1 [-0.5,+0.8]"; TTC "-11 [-17,-4], -12 [-17,-2], -23 [-28,-12]". Against a333: TTC +29, +34, +25, CIs excluding 0. Lesson: the learner lands between the two rules on the flow-TTC trade; no cell shows flow and TTC both better than p303.

Bearing on the hypotheses. **H1 supported for flow** (these rows score flow past the merge and speed, not door-to-door delay): fixed tau 1.2 / 1.0 / 0.8 s gives flow +8.1 / +9.9 / +12.2 % at 5,300 (V274, upper bound), +3.9 / +6.0 / +7.9 % under the V2V rule (V276). **H3:** V289 measured that a vehicle's own headway barely changes its own speed (speed term 0.468 / 0.469 in the merge zone); the table stands as a measurement of incentives, but its use as the cause of the collapse is withdrawn (V294). **H4:** a 9-pattern rule search produced p303, which ties or beats every learner (V287, V298). **H5:** 10-seed tuning flattered the rule (+3.1 became +1.9, CI including 0, V285); the V297 pass did not replicate; the bar's safety test applied in 1 of 39 comparisons (V297). **H2 consistent in this range:** against delay alone F0-F2 have more TTC < 3 s events (-27, -20, -37; negative = more events, V297-V298) while beating a333 on TTC; TTC is in the reward (safety weight 10, V296). INFERENCE: the TTC edge exists only against rules that ignore TTC.

## (b) Checklist for a new headroom screen

- Gate statistic has a no-drop null: v199's T1 null median was 10.8-12.65 % against a 2 % stop line, so "T1 could not fail" (V244).
- Merge model is not the result: zipper caps discharge at 1,344 veh/h at 0.1 s against 1,932 at 0.5 s (V180); zipper + Flow-IDM discharges about 900 veh/h on every seed (V249, V255).
- Empty detector intervals: an empty lane counted as speed 0 (V168, V170); an empty 30-s interval read as free, so a standing lane 0 never triggered onset (V261).
- Counters count what they claim: the emergency-stop regex matched none of about 21 million lines (V155(3)); "short gaps" were stopped queues at minGap (V283); 420 "collisions" were one standstill contact counted per step (V280); SUMO collisions include minGap intrusions (V209, V211); lane-end crawl contacts occur without any command (V291).
- Reward reaches the learner in training mode (V294); smoke check after every change (V231).
- Actuator T0: meter released 1.45 × commanded (V140), then 0.80 (V220); ALKS hold deficit came from the ending lane (V225).
- The screen can pass and can fail: grid edge rule (V154, V241); incident as the binding bottleneck made a verdict "close to predetermined" (V155 M1); power stated first (P(UNCLEAR) 0.72 with no effect, V240).
- Oracle cross-fitted: in-sample OR would have passed 3 cells (V94); ORX is biased low (V97).
- Tuning seeds separate from test seeds, then a fresh-seed check (V285, V298); no brittle point-estimate lines (V298: under one vehicle separated 1 of 3 from 2 of 3).
- Teleports: 14 at the on-ramp on v190 (V191), teleporting off since V197; the archive plant ran with teleport 300 (V255).
- Drain and window: report the share of a gain earned in the drain (V131 D3, V255).
- Opponent not weaker than no control (V255(3)); breakdown detector outside the lane-change zone (V185-V187); pre-queue flow not demand-limited (V271).

## (c) Disturbances and plant variants built or studied

- **Detector faults.** Screen D1 only, on BN4 (page `docs/research/protocols/screen_D1_detector_faults_draft.md`, V88-V90). Fault rates sourced (V158; "35-40 % of California loops failed on a typical day", V176), but "Not built" in the fleet plant (V162). Whether control matters: not supported, not refuted (V90).
- **Incidents and crashes.** Seeded crash process `v5b/fleet/crash.py` (V174; k = 0.001085 on v190, V198). Passing zone `v5b/fleet/incident.py`, f = 3.0, η "0.532 [0.529, 0.540]" (V200). A forced PM crash adds "+226.0 s [203.5, 237.6]" mean HDV-car delay with the zone, against +12.9 s [−18.7, 69.3] without (V203). No controller was tested: the E1 I cell never ran (V243).
- **Weather.** `fleet.weather`, g = 1.12 (medium) and 1.23 (heavy) (V206). Wet minus dry delay: medium "+40.5 s/veh [23.9, 54.9]", heavy "+105.8 [85.2, 124.3]" (V214). Crash scale per state (V216). The weather-scheduled against weather-blind comparison (E2, V204 Q9, V212) never ran. Critical-occupancy shift too noisy to show (V206).
- **Trucks.** 7.5 % trailer class, human-driven (V156, V161). In a 1-lane bottleneck one truck costs "about 3.4 car-equivalents" (V183, DERIVED, [VERIFY]). No control test.
- **Driver heterogeneity.** Per-vehicle sourced distributions in `v5b/fleet/` (V158, V162), means calibrated (V187). Adaptive human drivers: not found in V1-V299.
- **Capacity-drop realism.** V139-V149, V177-V189, V244, V254-V256. "no controller has yet been tested on a plant with a verified drop, because no such plant exists in this project" (V255(5)); m32 shows none (V271).
- **CAV share, delay, demand.** p303 rows at 25 % and 80 % share, action step 0.3 and 0.8 s, demand 4,300 and 4,800 (V290): at 80 % flow +7.1 % at both levels. V299 fixed a 10-cell map of F0-F2 against p303 on these conditions; its result lies outside this range.
- **Ramp merge.** Courtesy-gap rule: 10 teleports against 0 (V195); squeeze-in rule: 15 collision events (V197).

## (d) Directions rejected or parked

- Lane, segment and zone-level CAV targets (V3, author experience); VSL and HDV lane limits (V15); VSL on SUMO plants (V98: "LD3 headroom ≤ 4 %, VSL DRL killed"); MTFC through ALKS (V241).
- Non-learning adaptive scheduler dropped from P2 (V63); V280 notes that none has been tested.
- Margin theme (V87); measurement studies (V78); sweep v3 directions 3-5 (wave absorption, leader-regime inference, work zones) never screened (`docs/research/direction_sweep_v3_events.md:20-22`).
- Metering under incidents: mechanism is prior art (V97), then KILL (V149). E1 upper grid edges and MC* never run; I-cell lite screen parked, needs a new V# (V243).
- Calibrated-plant study (V245); drop-ladder map A "closed for SUMO", a macroscopic plant possible later by a new decision (V256).
- Vinitsky reproduction demoted to a report-only rung (V248; 47-95 h per stored run, V247).
- C3, a learned scheduler for tuned ALINEA under imperfect detection, parked behind C1 (V152).
- EVT crash model (V172); tuning SUMO's collision rate (V163-V164).
- "Only positive DRL results count" retired (V243).

## (e) Headroom prior

Rows V1-V299 do not restate "1.5-6 %" or "2-3 %" (searched, none found). Both stand only in the project CLAUDE.md: Method, "Prior: published hybrid gains ... about 1.5-6 % (macroscopic models); three v6 gates found 0-5 %" (no source named), and Claim rules, "≈ 2-3 % over the strongest published logic controller, and ≈ 9 % over MTFC+PI-ALINEA (Frejo & De Schutter 2021, Seville; D5.1) [VERIFY]". In-range statements of the same kind:

- V74: "about 85-95 % of delay is unavoidable queueing at the drop" (pilot, not data).
- V152: on BN4 "the best RL equals ALINEA at 40 % AVs, with lane changes off (Vinitsky et al. 2023, checked in the arXiv full text, lines 623 and 821)".
- V155 X1: 6-10 % ceiling (unverified estimate).
- V242: a perfectly timed meter "could recover only about 1-5 %" (that channel only).
- V247: "Expected mobility effects are small; reported benefits come below breakdown and mostly at high CAV shares" (prior-art search for cooperative merging; no source named in the row).
