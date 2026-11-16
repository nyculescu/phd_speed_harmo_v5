# Version timeline for the evidence audit

Reference for the classification step. Read-only work. Sources: ledger rows read in full for every V-number cited; the plant files compared key by key; stored rows tallied for their plant flags. "INFERENCE" marks what no record states. "Provenance check" marks a tally of stored rows (flags and keys only, no outcome statistic).

## 1. What the classifier must know first

1. **DRL-against-rules results exist on three plants only:** m32 (V265-V317), P0 on r1m3 and r2m3 (V332-V368), plant_c3 on r2m3 (V382-V502). P0c and bare P0d carried no-controller checks and a few traces only (V370: "No controller runs on P0c until the author decides"; V374; V377; V380).
2. **Provenance check, stored rows.** Phase 1 steps 1-3, phase 2 oracle, headway and confirm rows, the r2m3 check, confirmatory 2 (1,200 r1m3 + 1,200 r2m3 rows), the rule check and the shot: every row carries `smooth` and `lcAssertive 1.4` only, no `ease`. So all of them ran on the plant with the hidden braking of V367. Confirmatory 3, 3b, the demand sweep, round 2's test (2,800 rows) and S6 (13,920 rows): every row carries all plant_c3 flags.
3. **Every policy before V388 used hand-scaled inputs** ("earlier policies (V290-V368) used the old inputs", baseline_v3/BASELINE.md:69).
4. **Delay changed definition at confirmatory 3.** Before: mean over vehicles planned and finished inside the window (plant_sweep.py:326-333; baseline_v0/BASELINE.md:136). After: all-vehicle delay in vehicle-seconds, "unfinished vehicles and the insertion queue included" (plant_sweep.py:347; confirmatory_3.md:90). Provenance check: no row before confirmatory 3 has the `all_delay` key.
5. **So every record before V382 carries at least one plant or metric defect that was later fixed** (the sawtooth on m32; the hidden braking, the tau jump and finishers' delay on P0), and every policy in it used hand-scaled inputs. A record from V382 on still carries the open items of section 4: 1-Hz close-following, merge-2 lane ends, the pooled arm, the window end, the unsettled capacity drop.

## 2. (A) Plant versions

| Name | Defined, changed, frozen | Commit, tag | Change against the previous version | Results on it |
|---|---|---|---|---|
| BN4 (archive) | V255(2) | archive `vsl_lab` bn4, "unchanged since 920ff71" | zipper + Flow-IDM, lane changes off, 0.5 s step, teleport 300 | D5.10, R6, P1/P1b, C1; withdrawn as claims V256 |
| p1c "realistic plant" | V149, V255(4); earlier rows not read | `1b58869` | BN4 slowdown; zipper + Krauss at 0.5 s (V255(4)) | V149 (metering KILL) |
| ramp32 / v190 | V190 | not stated | 3 lanes, 1-lane ramp, 300-m acceleration lane, lane drop 3 to 2 about 1.5 km after the merge; "plant v188 drivers and mix"; ramp share 15 % | V190-V198 (courtesy gap V194-V195) |
| v199 | V199 | E1-lite code `8eb212c` | ramp32 plus the incident passing zone | V199-V244; E1-lite V236-V243 (V241) |
| bn4L | V250, V254 | `60e9664` | lengthened BN4, teleporting off | A stage 0: A-UNTESTABLE (V254) |
| m32 | drafted V250, approved V256(3), built V259, testable V264 | `f3f0c4c`, `7da3c02`, `e72d0d6`; stored as tag `baseline-v0` (`b7c535a`, V307) | ramp32 without the lane drop; meter green; constant demand; step 0.1 s; teleporting off; trucks 7.5 %; 50 % ALKS in the training and evaluation rows read (25 and 80 % in C0 and the operating map) | V259-V317 |
| r1m32, then r1m3 "as adopted" | V318, V319 | none | a name only; the same plant as m32 | reference arm in V322-V329 |
| plant sweep candidates | V314, V322-V327 | `2b865a1`, `124b930` | only no-control runs scored; nothing frozen | none |
| r1m3 P0 (`sm_as1.4_h0`) | rule V326, pick V328, check V329, accepted V330 | `124b930`; tag `baseline-v1`; `plant_p0.json` | `lcAssertive` 1.4 for all vehicles; the smooth no-undertaking rule for ALKS (5-s look-ahead, target set on the whole second); SUMO's abrupt rule off for ALKS | V329-V353; r1m3 half of confirmatory 2 (V356-V359) |
| r1m2 | V320-V321, V330-V331 | `6400571` | 2 main lanes, P0 settings | check only |
| r2m3 (a geometry) | V354 | `e2649d7` | second on-ramp with a 295-m lane 4a, about 1.2 km after merge 1; demand 70 / 15 / 15 %; "P0 settings unchanged", no tuning | with P0: V354-V368 |
| P0c | V370, check V371 | `5760e96`; no tag; `plant_p0c.json` | P0 + `ease` | check only; fails 2 of 7 items (V371) |
| P0d | V374, check V375, accepted V376 | `823eb7f`; tag `baseline-v2` | P0c + `smooth_s` 8.0 + `ease_max` 4.4, "chosen after seeing C7 of V371, on used seeds" | check V375; traces V377, V380 "as built"; no DRL result |
| plant_c3 | A1 in V378, build V380, pre-run V382, run V383 and V390, frozen V411 | `fae4620`, `d2b2ecc`; tag `baseline-v3`; later `baseline-v4` (v3w policies, V455), `baseline-v5` (V502) | P0d + `tau_rise` 0.2 + `taper_fast` + `fix_x`, on r2m3. First named in V385 | V382-V502 |

Within m32 the ALKS action step changed: 0.1 s in B runs 1 to 4b ("The policies were not trained with the delay", V280), 0.5 s from run 5 on (V283 "Run 5 keeps the delay"). The V2V rule dates from V275. Plan B adds the TRUCK and SURGE perturbations; the plant file is unchanged (baseline_v5/BASELINE.md:7-11).

**P0, P0c, P0d and plant_c3, key by key** (the JSON files; `baseline_v2/plant_p0d.json` equals `p0c/plant_p0d.json`, and `conf3/plant_c3.json` equals `baseline_v3/plant_c3.json`, by SHA-256):

| Key | P0 | P0c | P0d | plant_c3 | Effect |
|---|---|---|---|---|---|
| `smooth` | true | true | true | true | ALKS do not undertake; desired speed capped behind a slower left-lane vehicle (V326) |
| `lcAssertive` | 1.4 | 1.4 | 1.4 | 1.4 | all vehicles |
| `ease` | absent | true | true | true | the cap moves every 0.1 s, a small step under the speed; one vehicle brakes at most -2.53 m/s² "against -9 as built" (V370) |
| `smooth_s` | absent (code default 5.0, b_env.py:75) | absent | 8.0 | 8.0 | look-ahead of the rule |
| `ease_max` | absent (0.0, b_env.py:356) | absent | 4.4 | 4.4 | braking allowed when closing needs it |
| `tau_rise` | absent | absent | absent | 0.2 | a headway rises at most 0.2 s per 1-s update (b_env.py:781-782) |
| `taper_fast` | absent | absent | absent | true | slowdown taper on the 0.1-s clock (b_env.py:415) |
| `fix_x` | absent | absent | absent | true | positions and zone offsets from r2m3's real lane lengths; "the position input no longer clipped before the road ends" (confirmatory_3.md:147) |
| `geom` | absent | absent | absent | r2m3 | road |

Not in these files and unchanged across the four: fleet, human driver models, ALKS IDM (tau 1.6 s, accel 2.6, decel 4.5, emergency 9.0 m/s², action step 0.5 s; plant_vv_record_v0.md PR-06), SUMO options. The training file `phase1/plant_p0_train.json` writes the same P0 as `lc.lcAssertive` 1.4, `smooth`, `alks.lcOvertakeRight` 1, plus reward references at 4,090, 4,600 and 5,300.

INFERENCE: for no control in steady traffic, plant_c3 and P0d on r2m3 give the same run. `tau_rise` acts only on a commanded headway, `taper_fast` only under a slowdown, `fix_x` only on positions read by rules and policies. V382's T3 ("r2m3 no-control rows of baseline v2 ... reproduce every numeric key") agrees.

## 3. (B) Input and trainer versions

| Version | Rows | Plant | Inputs | Action and clock | Reward | Training demand | Policies |
|---|---|---|---|---|---|---|---|
| B coordinator | V265-V272 | m32, ALKS step 0.1 s | 46 values, one coordinator; scaling not stated | cap offset 0-30 km/h on 6 ALKS, every 1 s | per second: braking, TTC < 3 s, vehicles in system, collision (V265); run 3 an "efficiency reward" (V269) | 4,090 / 4,300 / 4,600 | runs 1-3 |
| B zones | V277-V285, V302-V304 | m32 | zone agent | one headway per zone, rate limited (V278) | runs 4 and 4b: a gap penalty that charged stopped queues (V283); run 5; later C's shared reward (V304) | not stated | runs 4, 4b, 5; B0-B2 |
| Per-CAV, reward absent | V286-V293 | m32, ALKS step 0.5 s | own state plus short broadcasts (V286), hand-scaled | 4 headways; decide every 5 s, move once per 30 s; 30-s clock from run 3 (V290) | trained on "the shared term only ... a shared collision cost and the move charge. No own speed, no flow contribution, no safety term" (V294) | not stated | C runs 1-4, attribution run |
| Per-CAV, intended reward | V294-V304 | m32 | same; `hold left` dead "since V290" (V387) | 30-s clock; gamma 0.8 per decision | flow 0.4, safety 10, move 0.01 (V296); weights 20 and 40 (V304) | not stated | 84-update run, F0-F2, G, H |
| Screen | V309, V317 | m32 | same | variants: 10-s clock (gamma 0.933, lambda 0.967), gamma 0.95, residual on p303, lane action | same | `saturated`: 5,300 and 6,000 only | 1 learner, 100 updates each |
| Phase 1 step 2 | V334-V337 | r1m3 P0 | 16 actor inputs (read from the stored policy file), hand-scaled | 10-s clock, "the 10-s hold" | safety 10, flow 0.4, references from P0 no control | 4,090 / 4,600 / 5,300, steady only (INFERENCE from the keys of `plant_p0_train.json`) | d0-d2, 250 updates |
| Step 3 | V338-V339 | r1m3 P0 | 17 inputs (adds own speed level) | 12 actions: 3 caps × 4 headways, "applied through the same smooth cap" | unchanged | same | 3 policies |
| Confirmatory 2, shot | V356-V359, V363, V368 | r1m3 P0; r2m3 with P0 | 16, hand-scaled; r2m3 positions added (V358), built on r1m3's lengths (V365(4)) | 10 s | as V334 | 4,090 / 4,600 / 5,300; one third no event, else a tapered slowdown on edge 3, 4 or 5, 25-60 km/h, 60-180 s (confirmatory_2.md:32) | 3 per plant, 250 updates; shot 7 learners, 500 updates |
| Confirmatory 3, revision 3 | V383-V388 | plant_c3 | hand-scaled | 10 s | same | same | stopped after 3 updates (V388; "5 updates, not 3", V396); not read |
| Confirmatory 3, revision 4 = baseline-v3 | V388-V411 | plant_c3 | 16, scaled by running mean and SD, clip 5; a never-varying input set to 0; the self-count of the acceleration-lane input fixed (V388, V389) | 10 s | "v3": safety 10 on 1-Hz flags, flow 0.4 (confirmatory_3.md:42; b_env.py:841-843) | 4,090 / 4,600 / 5,300, one environment per level, random slowdowns (round_1.md:20) | d0-d4, 500 updates, final only |
| Round 1 | V415-V449 | plant_c3 | 16 normalised; `res` adds the rule level as input 17 (V415) | `res`: 3 offsets around os1_15_10 | v3 (v3w, res), attr, lagr | 7 levels 4,500-6,000 by 250, cycling (V420) | v3w kept; res, attr, lagr; checkpoints chosen on validation |
| Round 2 | V439-V450 | plant_c3 | `ahead`: 18 inputs (V455) | 1B: gate mask | 2B anneal; 1D braking read at 0.1 s "while TTC stays 1-Hz" (V440); rep: repeated slowdowns | round 1's seeds and range | 2b, 1b, 1d, ahead, rep; sw and tail evaluation only; B-LOO dropped (V445) |
| Plan B | V478-V502 | plant_c3 + TRUCK | 16 normalised | 10 s | none | none: v3w "frozen since 2026-11-06" (baseline_v5/BASELINE.md:19) and never trained on TRUCK | w0-w4 |

Clocks that differ between arms: rules answer every 5 s, policies every 10 s, "which favours the rules" (V381(2)). The reward's safety flags are 1-Hz in every reward mode (s01_result.md:625).

## 4. (C) Defect ledger

Direction: R = toward the rules, D = toward DRL, A = every controller alike, U = unknown.

| ID | Defect | Found | Fixed | Plant and results touched | Direction, mechanism |
|---|---|---|---|---|---|
| D1 | Capacity-drop estimator without a null. v199's T1 "could not fail" (null median 10.8-12.65 % against a 2 % stop line). The V271 estimator has "no null computed" | V244, V271 | open (PR-26, gap) | v199 (V220, V241); m32 (V271); sweep (V322, V327) | U. The readings (m32 -4.7 / -2.0 / -0.1 %; adopted 5.1 / 1.7 / 4.2 %; P0 candidate 11.7 % on 3 runs) cannot rank plants by headroom |
| D2 | BN4: near-deterministic discharge of about 900 veh/h, a drop of about 42 % | V247, V254, V255 | results withdrawn V256 | D5.10, R6, P1/P1b, C1. V149's plant "no longer called realistic" | A against no control: any controller that avoids the standing state gains ("a constant 1,800 veh/h meter ties the DRL", V255) |
| D3 | SUMO registers an IDM collision only within 0.25 m | V257 | open (stated as weak evidence) | every collision count | A; may hide risk of short headways for rules and DRL alike |
| D4 | Collisions counted per step: 420 "events" were one standstill contact; "the collision reward has the same flaw" | V280 | reading corrected V280; the code fix is not stated (later rows hold `collisions` and `contact_steps`: INFERENCE) | m32, B runs 1-4b | R in V279's first reading (charged to a policy arm); none after V280 |
| D5 | The "short gap" count was stopped queues | V283 | V283 (`gap25` only above 1 m/s) | V274, V276, V279, V280, V282; run 4's penalty | Against short-headway arms and against run 4's policies: the penalty charged queues, so the policy backed off. Readings withdrawn |
| D6 | The per-vehicle reward never reached training | V294 | V294 (`c1e0ac3`), with a smoke check in training mode | C runs 1-4 and the attribution run; V288-V293 explanations | R: the bar failures of runs 3 and 4 "apply to a shared-reward, no-safety C" |
| D7 | Bar read on flow with a safety test behind a 0.5 % point gate ("1 of 39 comparisons"); delay "was in no bar" | V297, V298, V307 | delay became the measure from phase 1 (V334) | V285-V304 | Both ways: V297's pass rested on it (D); V298's fail turned on "under one vehicle" (R) |
| D8 | Sawtooth: ALKS brake at -4.5 m/s² about every 4 s under SUMO's no-undertaking rule | V324 | V326 changed its form only (V367); removed in P0c and P0d | m32 and r1m3 as adopted: "Every stored braking and fuel count, baseline v0 included" | A against no control ("a controller could have gained by avoiding it"); between rules and DRL U |
| D9 | Lane action: 30 and 68 collisions in 10 runs, "Not traced" | V317 | open | m32 screen | U. The record that closes the lane actuator has no trace; lane rules lost too (flow -2 to -9) |
| D10 | Plant-sweep score: no ramp term, clipping at 30 | V322 | follow-ups V323-V327; the author picked from tables | plant choice only | none on controllers; the pick used braking numbers that D12 later voided (V367) |
| D11 | Wave statistic: a limit drop dipped the whole edge and counted as reach | V342 | corrected post hoc in V342 | wave check | The reading "the plant absorbs the rest" rests on a statistic fixed after the data |
| D12 | Hidden 9 m/s² ALKS braking in the smooth cap; 1-Hz samples miss it (1-Hz to step ratio 0.45-0.64, V371) | V367 | V370 (P0c), V374-V376 (P0d) | every result on P0, V329-V368 | Three parts. (a) Braking counts understated for all arms: A. (b) Delay: under no control at 5,300, P0 reads 120.2 s against P0c's 127.5 (V371), because the hard braking opened gaps. Under a controller this was never measured, so the bias on any comparison is U. (c) Any lowered speed cap braked at up to -9 m/s²: against every speed-cap arm, rule, oracle or DRL (V339, V344 "need a look") |
| D13 | Step slowdown: vehicles on the edge "must obey the new limit at once" | V345 | V346 (taper over 20 s) | V342, V344 | Braking cost of the event overstated, A; delay "not separately measured" |
| D14 | r2m3 positions used r1m3's lengths ("a few metres high from 4a on; the effect is untested"); position input clipped | V365(4) | `fix_x`, V380 | r2m3 with P0: V354-V368 | U: shifts rule zones and the policy's position input |
| D15 | 1-Hz braking counters | V367 | step counters from V370; a 5 % check in every later report | all braking counts to V368 | as D12(a). The reward's braking flag stays 1-Hz except in 1D |
| D16 | Close-following (TTC below 3 s) read at 1 Hz | V370, V433 | open (PR-23, limit). The 0.1-s meter E1 was built (V435); no run of it was found (INFERENCE from the search). Whole against half-second checks: 0.976-1.033 (V382); band rows up to 1.142 and one at 0.89 (round_2_result.md:333; round_1_result.md:217) | every close-following reading, V265-V502 | U. The flag is also the reward term, so a policy is paid on the same sample phase that judges it: a D-direction risk, not measured |
| D17 | V2V loss sets tau "from 0.8 to 1.6 s at once": a second hidden braking source | V377(1) | `tau_rise`, V380 | every short-headway arm under the V2V rule, V275-V376 (INFERENCE for rows before V377) | Flattered short headways under slowdowns: on 2 seeds the fixes "cost p333 about 10-13 % delay" (V380, together with D18). Toward p333 and every short-headway controller against no control; between p333 and DRL U ("No policy was traced") |
| D18 | Slowdown taper stepped once per second | V377(2) | `taper_fast`, V380 | tapered slowdowns V346-V368 | A; "about 1 % of TTC" |
| D19 | Finishers-only delay "can flip the 2 % gate" | V377(5) | all-vehicle delay from confirmatory 3 (confirmatory_3.md:90) | V307-V376 | Toward the arm that finishes fewer vehicles, since its worst delays are left out. Largest for no control, so gains over it are understated: A. Between rules and DRL small where flows tie: U |
| D20 | Network TTC "is mostly a low-speed queue"; merge-2 lane ends never validated (ramp 2 has 608.5 lane-end stops per run against 7 at ramp 1, baseline_v2/BASELINE.md:40) | V377(3), V396 | split counters V380; validation open (PR-28, gap) | r2m3, V354-V502 | Toward whichever arm lengthens headways at merge 2: D on close-following, and on delay in X1 (memo §1.4). V398: the X2 edge "is not only lane-end creep" |
| D21 | Trace changed the run (`_x` writes `xlast`) | V386 | V386 | teaching traces V385 only | none on results |
| D22 | Inputs hand-scaled; input [11] dead; x/300 saturated in 93 % of decisions; the acceleration-lane input counted the vehicle itself (0 in 33.7 % of on-ramp decisions) | V387, V389(5) | V388-V389. Still open: the merge-zone speed input covers merge 1 only (memo H3) | every policy V286-V368 | R: a handicapped learner; "Effect on learning: not measured" |
| D23 | `lcAssertive` 1.4 and lane changing not validated; entry collisions | V341; PR-08 | open (limit) | P0 to plant_c3 | A: easier merging (ramp delay 229.8 to 79.9 s, V329) leaves less merge delay for any controller to recover |
| D24 | The queue "never clears at 5,300 in any arm" | V398 | open | r2m3 at 5,300 | U: percentage differences depend on the window end |
| D25 | Rules answer every 5 s, policies every 10 s; rules tuned per cell; v3w not retrained for TRUCK | V381(2); memo M5 | kept, disclosed | plant_c3 | R |
| D26 | Opponents weak or picked on few seeds: untuned rules in confirmatory 2 (V359); r4a1 "picked on those seeds" (V368); rules tuned at 5,300 only in the sweeps (baseline_v3/BASELINE.md:70); 3E-C "not converged" (V496) | as cited | 70 rules in 6 forms from confirmatory 3; CMA-ES rules in round 2 and Plan B | V359-V368, V406-V419, S6 | D |
| D27 | Learner defects: gate-closed decisions unmasked, others' delay priced "about 200 times below" (V413); lagr target about 6 % below the rules, not 3 % (V429); 40-seed validation cannot see 1-2 % (V435) | as cited | 1B tested, not shown better (round_2_result.md:421); the rest open | rounds 1 and 2 | R: the variants are not clean negatives |
| D28 | Pooled arm: per-seed mean of 5 learner runs against single runs, on a right-skewed measure | memo M4; critic_ranking_audit.md:49 | open | arm-level readings of rounds 1 and 2 and Plan B's W (V462, V480(8)) | R on delay: pooled point -0.58 % against a per-learner mean of +0.04 % (exploratory, from the memo; not recomputed here) |
| D29 | Gate G4(ii)(b) had "no working null" (S's own random splits fail it 44-48 %) | V484 (second row) | V486, after the read, with an imperfect blind | Plan B S2 | Not a ranking bias. TRUCK, Plan B's only cell, stands on a post-read deviation |
| D30 | Teleporting is off (`--time-to-teleport -1`, day.py:134, used by b_env.py:164) | this audit | not a defect by itself | m32 to plant_c3 | "0 teleports" in V328, V370 C1, V374 C1 and PR-17 holds by construction and could not fail (INFERENCE from the option; verify in SUMO's documentation). Provenance check: the `teleports` key sums to 0 over the S6 and round-2 test rows. A blocked vehicle stays and adds delay to its own arm. A stuck check was found only in B's C0 (V258) and Plan B (`stuck_n`, V482): INFERENCE from the rows read |
| D31 | Process deviations: validation rows from two machines (V465); tile rule logged after validation rows existed (V463); X2's closing rule asked after the data (V466) | as cited | disclosed | round 2 | U; PR-18 reports identical rows across machines |
| D32 | Reading errors, later withdrawn: "mostly outside the slowdown periods" (V396); "DRL beats the simple baselines clearly" (V405); mixed signs (V452) | as cited | corrected | text only | none on rows |

## 5. (D) Lookup: V-range to plant, inputs, metric and open defects

| Rows | What ran | Plant | Inputs, trainer | Delay metric | Defects open |
|---|---|---|---|---|---|
| V149 | mainline metering laws | p1c BN4 slowdown, zipper + Krauss, 0.5 s | no DRL | per-vehicle delay, s/veh; exact form not stated | D1, D2 (V255(4)) |
| V194-V195 | courtesy-gap rule | v190, teleporting on (10 teleports) | no DRL | none; the pass rule was 0 teleports and 0 collisions | D1 |
| V241 | ALINEA, MTFC (E1-lite) | v199 (INFERENCE from V243: "E1 on v199 is closed") | no DRL | D on a slice | D1 |
| V256-V258 | decisions, protocol drafts | none | none | none | none |
| V259-V264 | build, C0, ladder; no control | m32, ALKS step 0.1 s | none | none | D1, D3, D8 |
| V265-V273 | B runs 1-3 (speed caps) | m32, ALKS step 0.1 s | B coordinator | none; safety proxies, then flow | D1, D3, D4, D8, D16 |
| V274-V280 | fixed headways, V2V rule, runs 4 and 4b | m32 | B zones | none; flow | + D5, D17 |
| V281-V285 | headway sweep, rule tuning, run 5 | m32, ALKS step 0.5 s | B zones | none; flow | D5 fixed V283; D1, D3, D4, D7, D8, D16, D17 |
| V286-V293 | C runs 1-4, p-rules | m32 | per-CAV, reward absent | none; flow | + D6, D22 |
| V294-V304 | F0-F2, operating map, cheaper tests | m32 | per-CAV, intended reward | none; flow | D6 fixed; D1, D3, D7, D8, D16, D17, D22 |
| V305-V313 | baseline v0 and decisions | m32 | stored policies | finishers (first delay numbers, V307) | + D19 |
| V314-V327 | plant sweep, no control (V317: the screen, on m32) | m32 / r1m3 as adopted and candidates | V317 only: screen variants | finishers | D1, D8, D9, D10, D16, D19 |
| V328-V331 | P0 pick and check; r1m2 check | r1m3 P0; r1m2 | none | finishers | D1, D12, D15, D16, D19, D23, D30 |
| V332-V339 | phase 1: rules and ALINEA, step 2, step 3 | r1m3 P0 | phase 1 (16 inputs; 17 in step 3), hand-scaled | finishers | D1, D12, D15, D16, D17, D19, D22, D23 |
| V340-V353 | wave check, oracles, local rule, driver types; no training | r1m3 P0 | none | finishers | same without D22; + D11 (V342), D13 (V342, V344), D18 (from V346) |
| V354-V355 | r2m3 check; no training | r2m3 with P0 | none | finishers | + D14, D20 |
| V356-V368 | confirmatory 2, rule check, shot | r1m3 P0; r2m3 with P0 | confirmatory 2 and shot, hand-scaled | finishers | D1, D12, D14, D15, D16, D17, D18, D19, D20, D22, D23, D26 |
| V369-V373 | P0c fix and check; no controller | P0c | none | finishers | D12 and D15 fixed; D1, D16, D17, D19, D20, D23, D30 |
| V374-V376 | P0d check; no controller | P0d | none | finishers | same |
| V377-V383 | review, build, pre-run checks; p333 traces | r2m3 P0d (V377; V380 "as built"), then plant_c3 (V380 "new", V382) | one stored P0-trained policy as a trace arm (V382) | all-vehicle from V380 | D14, D17, D18, D19 fixed in V380; D1, D16, D20, D22, D23, D24, D25 |
| V384-V390 | pages, teaching traces, aborted run, normalisation | plant_c3 | hand-scaled (shot policy C1; revision 3) | all-vehicle | D21 (V385 only), D22 |
| V391-V401 | confirmatory 3 revision 4, verification, replays, 3b | plant_c3 | baseline-v3, normalised | all-vehicle | D1, D16, D20, D23, D24, D25 |
| V402-V411 | reports, demand sweep, profiles, baseline v3 | plant_c3 | baseline-v3 | all-vehicle | same + D26 (rules tuned at 5,300 only) |
| V412-V419 | options memo, round 1 design, second demand sweep | plant_c3 | baseline-v3 | all-vehicle | same + D26, D27 |
| V420-V438 | round 1 stage 0 and training; E1, E2; rental kit | plant_c3 | round 1 | all-vehicle; training-mode `delay_s` for 2C | D1, D16, D20, D23, D24, D25, D27 |
| V439-V447 | round 2 candidates built and trained | plant_c3 | round 2 | all-vehicle | same |
| V448-V452 | round 1 result and report | plant_c3 | v3w, res, attr, lagr | all-vehicle | same + D28 |
| V453-V467 | round 2 evaluation, baseline v4, writing decisions | plant_c3 | v3w, sw, tail, round 2 | all-vehicle | same + D31 |
| V468-V477 | measurement pack, S0 / S1 | plant_c3 | v3w, tail, sw | all-vehicle | D1, D16, D20, D23, D24, D25, D28 |
| V478-V483, V484 (first) | Plan B protocol and S0; replication plan | plant_c3 | v3w frozen | all-vehicle | same |
| V484 (second)-V487 | Plan B S1, S2, G4 repair | plant_c3 + TRUCK, SURGE | no v3w row in S2 (V485) | all-vehicle | same + D29 |
| V488-V494 | S3a-S6 | plant_c3 + TRUCK | v3w frozen; 23 opponents | all-vehicle | D1, D16, D20, D23, D24, D25, D26 (3E-C), D28 |
| V495-V502 | read6 v1 to v2.3, rebuild, baseline v5 | plant_c3 + TRUCK | v3w | all-vehicle | same |

**The memo's records, placed:**

| Record | Plant | Inputs | Open at the time |
|---|---|---|---|
| V297, V298, V304 (H-5; "DRL adds nothing" on m32) | m32 | hand-scaled, 30-s clock | D7, D8, D17, D22; no delay bar |
| V317 (lane action, P2) | m32 | hand-scaled, 100 updates | D8, D9 |
| V333 (ALINEA, P4) | r1m3 P0 | none | D12, D19 |
| V337 (H1) | r1m3 P0 | hand-scaled, 250 updates | D12, D15, D17, D19, D22 |
| V339, V344 (H3, P3) | r1m3 P0 | V339 hand-scaled; V344 none | D12(c), D13 (V344), D19 |
| V347 (H1) | r1m3 P0 | none | D12, D17, D18, D19 |
| V355 (r2m3 coordination KILL) | r2m3 with P0 | none | D12, D14, D17, D19, D20 |
| V359 (H1: "no delay win in any of 20 cells") | r1m3 P0; r2m3 with P0 | hand-scaled, 250 updates | D12, D14, D17, D18, D19, D20, D22, D26 |
| V419, V429, V475 (H1) | plant_c3 | normalised | D16, D20, D24, D25, D26 |
| Rounds 1 and 2, V466 (H3, H4, L1-L3) | plant_c3 | normalised | D16, D20, D24, D25, D27, D28 |
| S6, V496 (H1, H4) | plant_c3 + TRUCK | normalised, v3w not retrained | D16, D20, D24, D25, D28, D29 |
| V149, V241, V194-V195 (P3, P1) | BN4 Krauss; v199; v190 | no DRL | D1, D2; other plants and actuators |

## 6. Limits of this timeline

- Rows V1-V255 were read only where cited. The plants bn4x and the lane-end corridors (V171-V189) are not described.
- The policy input counts come from the first layer of the stored policy files. The meaning of each input on r1m3 against r2m3 was not traced.
- Directions in section 4 are mechanisms from the records. Only D12(b), D17 and D28 have a measured size, each on few seeds or exploratory.
- No statistic was computed from stored rows.
