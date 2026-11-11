# classify_early: records V149-V379 behind "DRL cannot win on delay" (author's item 1)

**Basis.** Ledger rows read in full: V147, V149, V155, V190, V193-V195, V197, V241-V245, V255-V257, V265-V361, V363-V382, V387-V389, V395, V396, V398, V401, V406, V407, V419, V429. Also `confirmatory_2.md`, `baseline_v0/BASELINE.md` and its paired tables, `explore_v0/round1_screen.csv`, `phase3/decide_table.csv`, the timeline, and the two sibling audits (`plant_choice.md`, `metric_audit.md`). No simulation ran.

**Labels.** EXPL = my number from stored rows that were already read for a verdict. Statistic: paired seeds, difference over the reference arm's median, median, 95 % percentile bootstrap, 10,000 resamples, RNG 20261110. Bias: R toward the rules, D toward DRL, A every controller alike, U unknown. Verdicts: CO carries over, DIR carries over in direction only, RC needs a re-check, SUP superseded. Defect numbers (D1-D30) are the timeline's.

## 0. Three facts first

1. **No record in V149-V379 ran on P0d or plant_c3, and none used normalised inputs.** Three ran on earlier plants (p1c, v190, v199), the m32 rows on the plant before V314's tuning, the rest on P0. Provenance check: every stored row of phases 1-3 carries `lcAssertive` and `smooth` only, no `ease`.
2. **A defect the timeline does not list: unequal clocks (CLK).** In V337 and V339 the policies ran with `hold` 10 and p333 with the default 30 (stored row settings; b_env.py:642). V351 measured the clock alone at "+1.6 to +2.3" % delay. Direction: D.
3. **Timeline D19, direction not supported.** I rebuilt all-vehicle delay for every P0 record as N − dist / 27.78. On 2,800 plant_c3 rows this proxy equals `all_delay` within 0.03 %. No sign changes anywhere (EXPL). p333 against no control reads +25.0 [+23.4, +27.0] against the finishers' +28.0, so the gain over no control was not understated.

## 1. Table

| Record | Used for | Plant | Network, demand | Inputs, policies, training | Seeds, status | Open defects, bias | Verdict |
|---|---|---|---|---|---|---|---|
| V149 | P3: mainline metering KILL; best PI-ALINEA "rel −0.3 %", CI [−1.7, +4.6] s/veh | p1c "BN4 slowdown", zipper + Krauss, 0.5 s (V255(4)) | BN4 lane drop; demand not stated in the row | no DRL; an all-lane mainline signal | 7,430,180-199; registered gate, "run once" | D1: the "realistic 5-8 % drop" premise is withdrawn (V255(4)). "in the slowdown cell the incident is the binding bottleneck" (V155). A against any meter | DIR. Other plant, other actuator. Only the mechanism transfers, and it hangs on PR-26 |
| V194, V195 | P1: courtesy-gap rule, 10 teleports against 0 | v190, teleporting on | ramp32 with a lane drop; 4,600 | no DRL; `openGap` | one seed, 7,400,000; the 10-seed test "was not run" | The fail signal was teleports; teleporting is off on plant_c3 (timeline D30). The target "was alongside, not behind": the rule's aim failed. U for DRL | RC. Does not carry: plant, actuator, 1 seed |
| V241 | P3: all 6 MTFC arms "clearly worse" | v199 | ramp32 + lane drop + incident zone; demand not stated in the row | no DRL | n = 20; registered screen; result UNCLEAR | D1: "T1 could not fail", no drop shown (V244). MTFC "restricts flow before the breakdown"; "Not shown: ... CAV control in general" (V242). A | DIR, conditional on PR-26 |
| V266, V270, V272 | Route A, P3: coordinator PPO with cap offsets; "No policy shows a flow gain" | m32, ALKS step 0.1 s | 1 ramp, 3 lanes; 4,090 / 4,300 / 4,600 | 46 inputs, scaling not stated; 3 learners × 8 envs, 500 updates | 7,419,800-859; exploratory | D8 sawtooth: braking is a reward term and "a controller could have gained by avoiding it" (V324). A capped ALKS no longer trips the no-undertaking rule (INFERENCE), so the plant paid for slowing. It confounds the "slowing-down bias" reading against DRL | SUP: actuator dropped (V277), plant replaced (V328) |
| V267, V268 | fixed offsets match PPO on proxies, flow unchanged | m32 | same | none | same seeds; offset "best of 5 on these seeds" | D8; selection on the test seeds: R | SUP |
| V271 | "m32 shows no capacity drop"; "the actuator can only slow" | m32 | demand 4,325-4,806 | none | stored runs, n 1-6 per level; report-only | D1: "no null computed"; "a drop against a true maximum is not excluded" | DIR; see `plant_choice.md` |
| V274, V276 | H1: 0.8 s raises flow, +12.2 % (upper bound) and +7.9 % (V2V rule) at 5,300 | m32 | 4,090-5,300 | none | 7,419,860-899; exploratory | D5: gap columns withdrawn (V283). "IDM realism at these headways is unchecked" (V274): toward the fixed rule | CO: re-tested on P0 (V333), r2m3 (V355), plant_c3 (V382: p333 delay +29.6 / +19.9 / +12.8 %) |
| V279 | zone PPO run 4b does not beat the best fixed arm | m32 | 4,090-5,300 | zone agent | 7,419,910-929; exploratory | D5: "Run 4 must not be read as a test of learning" (V283). R | SUP: withdrawn as a test |
| V285 | zone PPO run 5: "0 of 3 policies pass" | m32, ALKS step 0.5 s | 4,600, 5,300 | zone agent | 7,419,930-949; bar fixed before data | D7: no delay in the bar. "the run 5 failure was the reward" (V304). R | SUP by V304 |
| V287, V288 | H4: a 9-pattern search gives p303 | m32 | 4,090-5,300 | none | tune 950-959, check 960-979 | D7, D8 | SUP: p333 is the reference from P0 on (V333) |
| V292, V293 | per-CAV C "0 for 4 runs" | m32 | 4,600, 5,300 | reward absent in training | 7,419,930-949 | D6 (V294): "No own speed, no flow contribution, no safety term". R | SUP: "C with its intended reward has not been tested" (V294) |
| V297 | pass, 3 of 3 at 5,300 | m32 | 5,300 | hand-scaled (baseline_v3/BASELINE.md:69); F0-F2, 250 updates, 30-s clock | 930-949, reused | D7: safety test applied in "1 of 39" comparisons. D | SUP by V298 |
| V298 | "C fails the fresh-seed check: 1 of 3" | m32 | 5,300 | F0-F2 | 7,419,960-979; rule fixed before data | D7: "under one vehicle separates 1 of 3 from 2 of 3". The extra TTC was on merge lanes only; whole network +1, +7, −6 (V307(3)). R | SUP by V307, then V337 |
| V300 | D2: "C wins 0 of 10 cells against p303" | m32; share 25 / 80 %, ALKS step 0.3 / 0.8 s | 4,300-5,300 | F0-F2, "trained only at nominal conditions" | 7,419,980-989, 10 per cell | D7, D8, D22; "a loss does not rule out a policy trained across them" (V299) | SUP; never re-tested on plant_c3 |
| V302, V304 | "DRL adds nothing over rules on m32"; H-5: the weight "moves C along the rules' trade-off" | m32 | 4,600, 5,300 | hand-scaled; F, G, H 250 updates; B 500 | select 600-609, test 650-669; rule fixed before data | D7: "Delay ... was in no bar" (V307); D22 (R). "the test was generous": opponents "not the strongest on the test seeds" (D) | SUP for delay. H-5 part never re-tested |
| V307 | delay edge over p303 "did not replicate": +6.5, +5.3, +5.5, then +1.7, +1.1, −0.7 | m32 | 5,300 | F0-F2 | 650-669, 960-979; post hoc | D19. No per-vehicle 0.8-s rule among the opponents. Against a333 (record, post hoc): F0 +6.06 [+3.62, +9.53], then +4.84 [+0.18, +8.93]; F1 and F2 not on the second set | SUP. The one plant with a recorded 5-6 % delay edge is the plant before V314's tuning |
| V317 lane | H3, P2: collisions "30 and 68 in 10 runs", "Not traced" | m32 | 4,600, 5,300 | hand-scaled; 1 learner, 100 updates | 7,419,670-679; exploratory | D9. Lane rules collide too (5-12): the actuator as built fails for rules and DRL alike (A) | RC; never re-tested |
| V317 `hold10`; V309 `residual` (H-2) | delay against p303 +9.1 [−0.2, +12.3]; `residual` +4.5 [−0.5, +7.4] (`round1_screen.csv`) | m32 | 5,300 | as above | same | CLK: 10 s against p303's 30 s (V287): D | SUP (V351; round 1's `res`) |
| V333 | H1: p333 +28.0 [+26.1, +30.1] against no control. P4: "ALINEA gains nothing" | r1m3 P0 | 4,600, 5,300 | none | select 690-699, test 700-719 | D12(b): hidden braking eased merging (lane-end stops 30.5 against 361 without it, V371): against any meter. EXPL: setpoint 24 gives rows identical to no control on 39 of 40 runs; setpoint 16 at 5,300 −0.5 [−2.0, +0.6]. Gain untuned; no ALINEA + p333 arm | Headway part CO. ALINEA part RC: no meter result on any later plant |
| V337 | H1: policies against p333 +1.5 [−0.8, +4.0], +1.8 [+0.3, +3.1], +1.3 [−1.6, +3.1] | r1m3 P0 | 4,600, 5,300 | hand-scaled, 16 inputs; 3 × 3 envs, 250 updates; steady training (timeline INFERENCE) | 7,419,720-739; rule fixed before data; "Exploratory, no claim" | CLK: D. D22: R. D12, D17 in both arms: U. D19: EXPL +1.5 [−0.1, +2.9], +1.5 [+0.3, +2.5], +1.8 [−0.8, +2.9] | CO for the steady tie: re-tested on plant_c3, r2m3 (V395 map; S6). Never on r1m3 |
| V339 | H3, P3: "no speed cap 88-95 % of the time" | r1m3 P0 | 4,600, 5,300 | hand-scaled, 17 inputs, 12 actions | same seeds | D12(c): a cap step brakes at up to −9 m/s² and "speed undershoots the cap" (V367); the reward's 1-Hz flag cannot see it. Against the speed action. A constant cap below the 100 km/h reference adds delay by definition (INFERENCE). CLK: D | Tie CO. Speed part RC |
| V342 | D4, M1: "the plant absorbs the rest" | r1m3 P0 | 3,500-4,600; 5,300 left out | none | 7,419,740-749 | D11: statistic fixed post hoc. D12: P0 without X already holds 709 and 924.5 full-emergency ALKS events per run at 4,090 and 4,600 (V371, other seeds). U | DIR. The wave statistic never ran on plant_c3 |
| V344 | H1, P3: speed-cap oracle, "0 of 8 best cases show headroom" | r1m3 P0 | 4,090, 4,600 | none | 7,419,790-799; best of 6 on the same seeds | D12(c): the oracle uses the same cap (b_env.py:361): against it. D13 step slowdown. D19: EXPL −0.5 to −1.5 | RC: "need a look" (V367), never done |
| V347 | H1: 1.2 s near the slowdown "pays delay −4.5 [−5.5, −3.0] %" | r1m3 P0 | 4,090, 4,600 | none | 7,419,780-789 | D17: the later fixes "cost p333 about 10-13 % delay under the slowdowns" on 2 seeds (V380): toward p333. D19: EXPL −3.5 [−4.8, −2.4] | SUP for slowdown cells: on plant_c3 arms that lengthen have less delay than p333 in X1, X2 (memo M2). No oracle bound on plant_c3: RC |
| V349 | H1: fixed 1.0 and 1.2 s cost delay, −6.6 and −15.5 % | r1m3 P0 | 4,090, 4,600 | none | 7,419,750-759; all-seed reading post hoc | D17: toward p333. CLK for the local rules. D19: EXPL −6.1, −14.0 | Steady part DIR. Slowdown part SUP |
| V351 | H4: "learning is not needed on this X" | r1m3 P0 | 4,090, 4,600 | none | 7,419,760-769; fixed before data | D16, D17; a TTC reading | SUP: V353 ("does not help" at 5,300), V359 ("narrower"), V395, V401 |
| V353 | hidden driver types: "no value" | r1m3 P0 | 4,600, 5,300 | none | 7,419,770-779 | D12, D16, D17: U | DIR; never re-tested |
| V355 | H1: 5-zone patterns tie uniform 0.8 s; KILL "for this form" | r2m3 with P0 | 4,600, 5,300 | none; 10-s clock for all | select 7,440,010-014, test 015-034 | 1 of 32 patterns picked on 5 seeds: toward uniform 0.8 s. D12, D14, D17, D20. D19: EXPL −2.3 [−3.3, −0.4], +1.2 [−6.5, +4.2] | CO in steady and TRUCK (3E-D tied with p333, memo H1). Not in X1, X2 |
| V359 | H1: "No delay win in any cell" of 20 | r1m3 P0; r2m3 with P0 | 4,600, 5,300; S, X1, X2, H1, H2 | hand-scaled; 3 per plant, 250 updates; trained on the slowdown family | 7,440,100-119; registered, not adversarially reviewed | The rule needs 5 % with a 99.75 % interval on 20 seeds; r2m3 X1 5,300 read +5.3, +0.6, +4.9. D17 (toward p333), D22 (R), D26 (rules untuned: D). D19: EXPL, still 0 of 20 | r2m3 S, H1, H2: CO (plant_c3 map cells, V395). r2m3 X1: SUP. r1m3 half: never re-tested |
| V361 | H4: "a rule matches" (`r4a1`) | r2m3 with P0 | 5,300 | conf-2 policies | 7,440,120-139; exploratory | "Best of several rules on these seeds, which favours the rules" (V360): R | SUP by V368 |
| V364 | M3: reward "flat from about update 50-100" | r2m3 with P0 | training | hand-scaled; 7 learners | training log | D22 | DIR; for the late records |
| V368 | delay "about equal" to p333; "no clear gain" from more learners; `r4a1` did not hold (H-4) | r2m3 with P0 | 5,300; S, X1, X2 | hand-scaled; 7 × 3 envs, 500 updates | 7,440,140-159; exploratory | D17 (toward p333), D12, D14, D20, D22; "only one fixed rule tested" (D) | S tie CO. X1 tie SUP. `r4a1`: CO (V401: −7.0 %, failed the filter) |

## 2. Findings

**(i) What H1, H3 and H4 rest on.**
- **H1, steady and TRUCK.** It stands on the plant_c3 records alone (V419, S6). V337 and the steady cells of V359 and V368 agree and were re-tested there. Two bullets in the memo's "For" list do not carry: V344 needs a re-check, and V347's sign is reversed in the plant_c3 slowdown cells by the memo's own M2.
- **H1, X1.** V359's "no delay win" was not an absent edge. EXPL, the same three policies on 40 P0 seeds (7,440,100-139), r2m3 X1 5,300, against p333: +3.9 [+0.4, +8.0], +0.6 [−3.1, +2.7], +4.4 [+0.0, +8.2]. The rule could not detect 5 % on 20 seeds. So the X1 edge predates plant_c3 and normalisation. In steady traffic the same pooling gives −1.3 to +1.7, all intervals through 0.
- **H3.** The code facts carry. "Widening has not helped" leans on V339 and V317. Both need a re-check: one actuator carried the hidden braking, the other was never traced. No action other than the four headway levels has been tested on plant_c3 (INFERENCE from the rows I read; the late classifier should confirm).
- **H4.** Every early support is superseded: V300 and V304 (flow bar, old plant), V351 (narrowed by V353 and V359), V361 (reversed by V368). H4 rests on the late records only.

**(ii) Closed or likely-to-fail directions.**
- **P1:** V194-V195 do not carry. The verdict rests on the plant_c3 delay floor.
- **P2:** V317 is the only record. It shows a broken actuator, not missing headroom.
- **P3:** none of V339, V344, V241, V149 carries as a test. Only the mechanism does ("caps only move the delay"), and it depends on PR-26.
- **P4:** V333 does not carry. One setpoint never acted; the plant's hidden braking had eased merging; r2m3 has no meter at ramp 2.
- **D2:** V300 is m32 only. **D4:** V342 in direction only; the fuel part was re-read on plant_c3 (memo §1.3). **H-2:** early screen superseded. **H-4:** `r4a1` carries. **H-5:** V304 never re-tested.

**(iii) Three re-checks that would change the most.** All rules-only, so the cells-tested count adds 0. Fresh seeds need the author's approval.
1. **Speed lever on plant_c3 (V339, V344).** No control, p333, 6 oracle settings; S, X1, X2 at 5,300; 20 seeds: 480 runs, $0.05-0.17. A pass reopens P3 and changes H3. The oracle code is still there (perturb.py:8, :118-122); it needs a smoke check with `fix_x`.
2. **Headway oracle on plant_c3, X1 and X2 (V347).** No control, p333, 6 oracle settings, fixed 1.0 s and 1.2 s: 10 arms × 2 cells × 20 seeds = 400 runs, $0.04-0.14. It gives the event-aware upper bound that screen R lacks. If the oracle shows no delay gain while v3w shows +4.2 %, the edge is not a response to the event, which supports the PR-28 reading.
3. **Lane lever (V317).** First zero-run: lane flows on plant_c3 from stored rows. On m32, lane 0 carried 1,212 veh/h against 1,790 and 1,952 "under every controller checked" (V307(4)). If that holds, 2 lane rules, p333 and no control × 2 cells × 20 seeds = 160 runs, $0.02-0.06, with a trace of every collision. Lane changing is not validated (PR-08), so a gain would be an artefact candidate.

Precondition for the DIR verdicts of V149, V241, V271 and V344: the capacity drop (PR-26), in `plant_choice.md`.

**(iv) Where the bias ran for DRL or against the rules, so the tie is stronger than recorded.**
- **V337, V339, V317 `hold10`:** the clock. With equal clocks on r1m3 P0, confirmatory 2's policies (other policies, same plant) read −1.6 [−3.4, −0.1], −0.7, −1.1 at 4,600 and +0.7, +1.1, −0.3 at 5,300 (`decide_table.csv`, 95 %). In V337 a333 was also ahead of p333 (91.5 against 92.8 s), close to the policies (90.0-91.0).
- **V359:** rules untuned on r2m3 while DRL trained on the slowdown family ("which favours DRL's exposure", confirmatory_2.md).
- **V304:** opponents picked on other seeds were "not the strongest", and no setting passed.
- **V297:** the pass rested on a gate that skipped the safety test.
- **V344, V347:** best of a grid on the reading seeds favours the oracle.

The other way, toward the rules: D17 on every P0 slowdown record, D22 on every policy before V388, D12(c) on the speed action, 5-seed selection in V355, same-seed rule picks in V285 and V361. Sizes are unmeasured except D17's 10-13 % on 2 seeds.

## 3. Never tested on plant_c3 with normalised inputs

INFERENCE from the rows read; none found.
- Any controller on r1m3 after the braking fixes. P0c and P0d carried no-control checks only (V370, V374); plant_c3 is r2m3.
- The speed action, constant caps, the speed-cap oracle.
- The lane action and lane rules.
- ALINEA or any ramp meter.
- The headway oracle and the driver-type oracle.
- The wave statistic; the brake and V2V-outage perturbations.
- Coordinator and zone agents.
- Safety weights 20 and 40, gamma 0.95, the 30-s clock.
- CAV share other than 50 %; ALKS action step other than 0.5 s.
- The `openGap` rule.

The one bridge: a P0-trained, hand-scaled policy as a trace arm on plant_c3, 10 seeds, medians, "not evaluated for any claim": delay 111.8 against p333's 118.2 in X1, 107.9 against 108.8 in X2, 51.3 against 58.2 in steady traffic (V382). No paired reading was made.

## 4. Limits

- Rows V380-V502 were read only where a verdict needed them.
- The 1-Hz distance in the delay proxy is untested on P0, where braking fell between samples (V367). It applies to every arm.
- EXPL intervals are 95 %, not Bonferroni; they change no registered verdict.
- V351's clock effect was measured at 4,090 and 4,600 only. On plant_c3 the clocks are 5 s for rules and 10 s for policies (V381(2)); the size of that is not measured.

Scripts and outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit2/ce/` (`keys.py`, `proxy_check.py`, `d19.py`, `d19b.py`, `d19c.py`, `d19c.out`, `pool.py`, `cfgs.py`, `alinea.py`).
