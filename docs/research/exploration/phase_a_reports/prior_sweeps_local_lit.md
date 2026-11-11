# prior_sweeps_local_lit

Aliases (under `docs/research/` unless stated): RVS = `rl_value_synthesis_v0.md`; WS = `lit_reviews/web_sweep_rl_value.md`; DS0-DS3 = `direction_sweep_v0.md`, `_v1_algorithm_first.md`, `_v2_margins.md`, `_v3_events.md`; EX2c, EX2r = `explore2/candidates.md`, `README.md`; PA_A, PA_B = `prior_art_A_v0.md`, `prior_art_B_v0.md`; NFM, NDE = `nonlinear_flow_mechanisms_v0.md`, `nonlinear_driver_exogenous_mechanisms_v0.md`; TH = `literature_phd_theses_rl_speed_v0.md`; LR/ = `lit_reviews/`; HO = `docs/handoff/2026-11-05_drl_sar_algorithm_handoff.md`; OUT = `docs/thesis/outline_v1.md`; R2 = `results/round_2_result.md`.
Limits: the ledger was read by keyword and row heads only. `literature_v0.md`, `capacity_drop_lit_v0.md`, `strengthening_plan_v0.md`, `development_plan_v0.md` were skimmed; they cover energy and cost values, the lane-drop plant, the P1c metering line and the RSS / eco-approach lines.

## (a) Directions already listed, with verdicts

**Learner.**
- Attributed-delay reward (1A), PPO-Lagrangian (2C), residual PPO on os1_15_10 (3B), picked V414. Round 1: lagr out at the λ cap (V448); "res and attr did not qualify"; attr "delay worse by 13.5 % [11.4, 14.5]"; only v3w advanced, "No delay wins over the rules" (V449).
- Round 2: 2B, 1B (gate mask), 1D (0.1-s safety signal), ahead (look-ahead inputs), rep-slow, B-TAIL, sw (V439, V444); B-LOO dropped as biased (V445). Finalists tail and sw. X1 won 5 of 5 against p333, os0_10_10 and 3E-T, but 3E-X1 failed the delay filter with its search not converged (R2:7-10). X2 not won, closes (V466).
- Training with varying demand: "wasn't worth it" (V411; EX2c:48).
- Listed, never run, all [VERIFY]: QMIX/VDN/COMA, SAC-discrete/DQN, imitation then fine-tuning, graph/attention, recurrent, model-based RL, evolutionary strategies (HO:167-176).

**Plant / actuators.**
- Lane action "fails as built" (V317, r1m3). Speed action: 0 of 3 policies met the 5 % rule (V339, r1m3); "policies declined" it (HO:86). Speed-cap oracle: "0 of 8 best cases show headroom", a KILL for this action on this X (V344, r1m3). ALINEA "gains nothing" on r1m3 P0 (V333).
- C1 drop-size operating map, C2 BN4 replication (RVS:60-61): track A "closed for SUMO" (V256); calibrated plant rejected (V245). C4, CAVs raising queue speed to raise discharge: risk High (RVS:63).
- Cooperative merging without a ramp signal: "Expect a small mobility effect" (PA_B:205).
- "the original coordinated freeway zones (1.5–6 % prior)" dropped (DS3:28).

**Disturbance.**
- DS3, "reasoning, not measured": under recurring variety "A table tuned once matches adaptation"; non-recurring events are "where adaptation can pay" (DS3:7-10). Five directions (detector faults, incidents and surges, wave absorption, leader regime, work zones); "No headroom has been measured for any direction" (DS3:5, 18-22). Its archived support (17–28 %, DS3:12) was later withdrawn as a claim (V256).
- r1m3 wave check: hard braker, truck, ramp bursts, V2V outage formed no wave; only slow 25 km/h did (V342).
- Demand profiles, exploratory: step 36 % and 42 % fewer close-following seconds than the two rules; peak "69 % more than the rules" (V410). E3 (one step, fresh seeds): "a tie is likely" (EX2c:37).
- Plan B: SURGE dropped at S2 (V487). TRUCK = T, study NULL: delay lower bound at or below 0 against 9 of 23 opponents; close-following lower bound > 0 against all 23, smallest +11.80 % [+4.97, +19.71] (V496).
- Driver or CAV-share mismatch (`sigma_scale`): "Later" (EX2c:45). C3 learned scheduler under imperfect detection and a day mix: "headroom may be small" (RVS:62). RQ5 disturbed plants: evidence "none" (OUT:33).

**Hybrid.**
- Residual PPO on the best rule: did not qualify (V449). sw (zone-switched hybrid): X1 5 of 5, X2 0 of 5 (R2:26-27).
- RL as tuner or repair: "against a well-tuned one it is small or untested" (RVS:38). Reviewers' suggestions only: a supervisory scalar over a safe micro layer (LR/2025_Shi.md:147); rule logic as a shield, or RL tuning its parameters (LR/2026_Mansouryar_2019_Zhou.md §A10); imitate-then-refine against a tuned teacher (LR/2022_Kreidieh.md §H(c)).
- Non-learning adaptive opponents (RQ4): evidence "none" (OUT:32); MPC-F and ASCH ran only in TRUCK, where ASCH picked the fixed rule lr1000_16_2 (V491).

**Non-DRL lines.** "None of the three needs DRL" (DS0:11); DS1's survivors score 3-4/10 on novelty (DS1:261); "no candidate passes all five gates" (DS2:7); a fixed per-site or per-regime table "matches online self-calibration" (DS2:18).

## (b) RL against conventional freeway control, as cited locally

| Paper (local ref) | Recorded claim | Baseline; tuned? | Plant | Read status |
|---|---|---|---|---|
| Belletti 2018 (WS:21) | TTS ALINEA 10 514, RL 10 575; "RL ≈ ALINEA, not better" | ALINEA "calibrated by traffic engineers" | BeATS macro | [FT] |
| Vinitsky 2023 (WS:22; PA_A:26) | at 40 % "equals the performance of a traffic light based controller" | ALINEA light; tuned feedback AV | BN4, lane changes off | [FT] arXiv (RVS:11); TCPS text [VERIFY] |
| Vinitsky 2018 (PA_A:27) | "matches the performance of feedback ramp metering" | meter "tuned empirically" | 4→2→1, 10 % AVs | [FT-kw] |
| Liu 2020 (WS:23) | mainline travel time: PI-ALINEA −11.7 %, DRL −20 % | PI-ALINEA "fine-tuned" | SUMO ramp; mainline-only metric; test = training demand | [FT]; journal [VERIFY] |
| Airaldi 2025 (WS:24) | −35 % relative to its own badly initialised MPC | BO-tuned PI-ALINEA | METANET | [FT] |
| Elmorshedy 2023 (LR/2023_Elmorshedy.md:66, 74, 95) | DRL headways 32.43 % less delay than 0.8 s everywhere | static headways; no ALINEA | Aimsun, 100 % ACC; seeds not stated | thesis full text |
| Wu 2018 (LR/2018_Wu.md ch. 6) | RL better than "hand-designed controllers" on velocity | FollowerStopper, PI-saturation calibrated at one density | 22-car ring | thesis full text |
| Kreidieh 2022 (§B) | outflow +11 to +33 % (reviewer's arithmetic) | "Human" only | Flow bottleneck | thesis full text |
| Shi 2025 (ch. 5) | vs "+ ALINEA RM": −2.1 % to −12.8 % TTT (reviewer's arithmetic) | ALINEA unspecified | SUMO, 100 % CAV, single runs | thesis full text |
| Mansouryar 2026 (§A6-A7) | time loss: rule 273.52 s, RL 302.58 s; emergency brakings 19 vs 0 | rule-based VSL; tuning not stated | SUMO, one run | thesis full text |
| W. Zhou 2019 MSc (§B6) | QL-VSL −15.98 %, feedback VSL −8.20 % | tuning not stated | DTALite, single run | thesis full text |
| MARVEL field 2025 (WS:57) | warning rate 88.6 % vs 74.4 %; no delay effect measured | rule-based, offline | I-24 | [FT] |
| Jang 2024 (WS:46) | non-RL Microaccel "comparable" | IDM, Microaccel | I-24 replay | [FT] |
| Ke 2021 (PA_A:23) | gains at 5 % and 15 % drop | no control only | CTM | [FT] searcher |
| Han 2022; Önür 2026; Sun 2024 (WS:94, 92, 91) | beat feedback metering / fixed gains / standalone MPC | tuning not seen | various | [ABS] |
| Rezaee 2013; Ahmad 2026; ElSamadisy 2025 (WS:28-30; PA_A:72) | large gains; rule-based VSL worse than no control | not stated | various | [SNIP] |
| Isser, ETH 2026 (TH:40; RVS:78) | replication of an RL-beats-ALINEA claim | n/a | ramp metering | not read |
| Frejo & De Schutter 2021 (`literature_v0.md`:1227) | ≈2–3 % / ≈9 % caps | n/a | n/a | [VERIFY] |

"Baselines: none is a tuned feedback controller" in the theses read (RVS:43). INFERENCE: the only full-text win over a tuned classical controller recorded locally is Liu 2020, on a mainline-only metric.

## (c) Mechanisms where a fixed rule is wrong part of the time

NFM and NDE describe the bn4x plant (NDE:3), not r2m3.
- **Capacity drop, hysteresis.** Field 2-11 %, mean ≈ 5 % (NFM:77); "The drop is not a constant" (NFM:106). r1m3, estimator without a null: 1.7 % at 5,300, 4.2 % at 6,000 (V327). No r2m3 value found. INFERENCE: consistent with H1.
- **Stop-and-go waves.** Discharge 8-23 % lower after disturbances (NFM:136); IDM gets the period wrong (NFM:130). r1m3 absorbs every tested perturbation except a 25 km/h slowdown (V342); on r2m3 the waves are the imposed X1/X2 slowdowns, and oscillation differences between controllers are "tiny" (`results/s01_result.md`:86).
- **Lane-change-induced breakdown.** Main trigger in 53 oscillations (NFM:138, ABS). SUMO 1.27.1 lane-change issues unfixed (PA_B:164-168). Reproduction on r2m3: not found.
- **Merge-ratio shifts.** Drop depends on the mainline/ramp ratio (NFM:94, ABS); "A single critical occupancy is then wrong part of the time" (NFM:180). No ramp-share variation found.
- **Weather.** Rain −10 to −11 % capacity (NFM:280); a fixed set point "over-admits in rain at dusk" (NFM:294). No ledger row from V300 on matches weather.
- **Heterogeneous drivers.** All 7 tested production ACC systems string unstable (NDE:22). r2m3: TRUCK tested, NULL (V496); CAV share fixed at 50 %.
- **Incidents, sensing.** Remaining lanes at about 54 % efficiency (NDE:19); 35-40 % of loops failed on a typical day (NDE:21). r2m3 assumes "ideal V2V and roadside speeds" (HO:26); no incident cell found.

## (d) RVS conclusions

- RVS:49: "Our KILL is not an outlier. It is what the better-controlled studies suggest: at a realistic drop, the mobility headroom at a bottleneck is small *for every controller*."
- RVS:50-54: "RL's documented value lies elsewhere: adaptation and robustness across conditions; safety and responsiveness; CAV-based smoothing, where non-RL controllers are strong competitors; repairing mis-tuned model-based control."
- RVS:20: evidence that RL beats tuned classical inflow limiting: "None found."
- RVS:26-28: wave damping needs "string-unstable humans (often set by design)"; "Non-RL controllers do as well".
- RVS:38: "against a well-tuned one it is small or untested."
- RVS:13: novelty is "not found in this sweep".

## (e) Recorded ideas not yet tested on r2m3 (within the rows read)

1. Long ramp headways (Elmorshedy's 1-20 s); r2m3's set is 1.6-0.8 s (HO:81).
2. Recurrent, attention, value-decomposition, off-policy, imitation, model-based, ES learners (HO:167-176).
3. Lane and speed actions: r1m3 only (V317, V339, V344).
4. Demand step or surge on fresh seeds: SURGE dropped at a gate, never read (V487).
5. Driver or CAV-share mismatch; penetration as an axis (EX2c:45; PA_B:231-236).
6. Weather, merge-ratio shifts, incidents with imperfect detection, V2V or sensing faults, string-unstable ACC.
7. A learned scheduler of a rule's parameters with the adaptation-gain metric (RVS:62).
8. Non-learning adaptive opponents on X1/X2 (OUT:32); 3E-X1 to convergence (R2:9).
9. E1, the 0.1-s safety meter on finalists and tuned rules: "Not done yet" (EX2r:31); no later row found. E2's margin: "Later rounds only" (EX2r:25).
10. C4, raising queue speed (RVS:63).

INFERENCE: every local sweep reaches the same prior: fixed tables match adaptation under recurring variety, and adaptation can pay only under non-recurring events. The event cells run so far (X1, X2, TRUCK) kept a close-following edge; no delay win over the rules held at the deciding level (the nearest: tail's X2 delay win, 4 of 5 at 97.5 % and 3 of 5 at 99.17 %, V466).
