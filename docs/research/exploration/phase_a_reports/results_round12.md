# results_round12: rounds 1 and 2, and the claim review

Sources: r1 = `docs/research/results/round_1_result.md`; r2 = `round_2_result.md`; cr = `docs/thesis/claim_review_round2.md`; p1, p2 = `docs/research/protocols/round_1.md`, `round_2.md`; tt2 = `docs/research/round2/report/test_table.csv`; val2 = `round2/report/validation.json`. Sign: positive = the arm has less delay or fewer TTC<3 s seconds (r2:79). CIs are 95 % unless stated.

**Headline that corrects the brief.** In round 2's test the v3w arm had less delay than the fixed 0.8-s rule p333: X1 +5.5 [+2.9, +8.0], X2 +6.1 [+3.4, +7.4] (tt2 rows "v3w arm"; arm level, uncorrected, descriptive). Round 1: X1 +2.6 [−1.8, +5.4], X2 +3.7 [+1.7, +5.0] (r1:211). "DRL ties 0.8 s on delay" holds only for the pre-registered per-policy delay-win reading (needs ≥ 5 %): 0 of 5 in round 1 (r1:212), 2 of 5 per cell for v3w in round 2 (r2:225).

## (a) Learner variants

Round 1 effects are at validation against baseline-v3 (delay) and os1_15_10 (TTC) (r1:74-80). Round 2 effects are against the v3w arm, delay / TTC (r2:109-117).

| Variant | Change | Result | Recorded reason | Clean negative? |
|---|---|---|---|---|
| v3w (control) | baseline-v3 recipe retrained on 7 levels, 4,500-6,000 (p1:20, :36) | Test vs baseline-v3, 97.5 %: delay X1 +3.5 [+1.2, +5.3], X2 +3.4 [+1.0, +4.8]; TTC +4.2 [+0.8, +8.3], +0.8 [−5.0, +5.9] (r1:105-106) | "retraining ... not from a change of method" (r1:9) | Confounded: range, schedule, seeds, reward references; each recipe trained once (r1:9-12, :248) |
| res (3B) | ±1 level offset on os1_15_10, 17 inputs, starts as the rule (p1:68-74) | Delay −1.6 [−3.5, +1.5], +2.4 [−0.7, +4.3]; TTC +9.6 [+4.5, +11.8], +10.0 [+7.2, +17.6] | Tied on delay, kept a third to a half of the TTC margin (r1:241); ±1 cannot reach 1.2 s from 0.8 s (r1:274) | No: action range confounded |
| attr (1A) | attributed delay replaces the spacing payment (p1:38-48) | Delay −13.5 [−14.5, −11.4], −10.4 [−11.9, −9.1]; TTC +32.9, +25.2 | "bought its margin with 10-13 % more delay" (r1:242) | No: weight 0.5 "fixed now, not tuned" (p1:48); learner C2 failed the collapse check (r1:69); heuristic (r1:275) |
| lagr (2C) | safety reward, delay constraint (p1:50-66) | Never evaluated: λ at cap 10 in 5 of 5 (r1:70) | Target sat about 6 % below the rules' mean delay, not 3 % (r1:65, :243); J on sampled actions (r1:273) | No: mis-set target; "concerns this constraint ... not PPO-Lagrangian in general" (r1:273) |
| 2B | LR and entropy decay, one critic scale (p2:26) | X1 −1.6 [−2.9, +1.0] / −0.8 [−5.8, +2.3]; X2 +0.1 [−2.5, +1.2] / 0.0 [−3.0, +3.2] | none beyond "not shown better" | under-powered (below) |
| 1B | gate hold and loss mask (p2:27) | −0.8 [−4.2, +1.0] / +0.2 [−5.1, +4.3]; −1.2 [−3.0, +0.2] / +0.3 [−4.4, +6.3] | none | Confounded: hold and mask together (p2:34-37); drops 42.5 % of decisions (r2:88) |
| 1D | 0.1-s braking charge in training (p2:28) | +1.0 [−1.8, +2.9] / +4.4 [−0.1, +6.5]; +0.1 [−1.0, +1.7] / +2.2 [−0.2, +5.5] | none | under-powered; TTC points positive |
| ahead | 2 look-ahead speed inputs (p2:29) | −0.7 [−3.2, +0.3] / +1.5 [−1.4, +7.3]; −0.8 [−1.6, +0.6] / **+7.3 [+2.4, +11.2]** | inputs are used: importance 0.220 and 0.171 (r2:121); they "read 1.0 on 2.4 % and 2.3 % of decisions" (r2:87, meaning not stated) | Not a null: X2 TTC CI excludes 0 but is under path (b)'s 10 % bar (p2:171) |
| rep | repeated slowdown in training (p2:30) | −0.4 [−1.6, +1.0] / +0.2 [−3.1, +4.2]; +0.2 [−1.7, +1.7] / +2.5 [−0.5, +5.7] | none | 799 remote rows unchecked (r2:54) |
| tail | argmax of mean probabilities of 6 checkpoints (p2:31) | Validation X2 delay +1.4 [+0.5, +2.4]; test, 98.75 %: X1 +0.9 [−0.8, +3.1] / +1.0 [−4.5, +3.3]; X2 −0.4 [−3.4, +2.0] / −1.8 [−5.2, +5.0] (r2:175-176) | validation advance did not replicate | reached the test; cleanest null |
| sw | 0.8 s and os1_15_10 before 594.72 m, v3w after (p2:32) | Validation X1 delay +2.1 [+0.4, +3.8]; test X1 −0.1 [−2.7, +1.7] / −0.9 [−3.5, +1.6]; X2 −0.5 [−3.0, +1.8] / −5.8 [−10.5, +0.1]; T2 X2 0 of 5 (r2:177-178, :192) | none | split point "fixed here and not swept" (p2:42): one hybrid design only |

Against the rules, all seven round-2 candidates look like v3w: u500 arms 36.9-48.4 % fewer TTC seconds than p333 and 22-29 % less delay than no control (r2:120; val2); tuned-reading count 10 of 10 for the five trained ones, tail 9, sw 7 (r2:129-131).

Cross-cutting flags:
- Five of seven stopped at validation, 40 seeds, uncorrected (r2:133).
- The paired delay SD is 7-11 % (V435), against arm CI half-widths of about 1.5-3 points. INFERENCE: a true 1-2 % delay gain was not detectable.
- 2B, 1B, 1D and ahead were judged on laptop rows against remote v3w rows (r2:44-46).
- All share v3w's training seeds; 5 learners "sample training noise only" (r2:448).
- "A null on 7 candidates in one round does not show that no other change would help" (p2:344).

## (b) v3w against the rules, per cell (round 2 test medians, r2:297-317)

| Cell | Arm | Delay veh-s | Flow | TTC<3 s |
|---|---|---|---|---|
| X1 | v3w | 230,763 | 2,139 | 1,809 |
| X1 | p333 | 242,346 | 2,119 | 3,365 |
| X1 | os0_10_10 | 248,766 | 2,123 | 2,598 |
| X1 | 3E-T | 250,054 | 2,114 | 2,255 |
| X1 | 3E-X1 (not counting) | 238,503 | 2,124 | 2,419 |
| X1 | no control | 322,813 | 2,037 | 1,493 |
| X2 | v3w | 226,353 | 2,157 | 1,534 |
| X2 | p333 | 237,372 | 2,127 | 2,711 |
| X2 | os1_15_10 | 240,654 | 2,124 | 2,152 |
| X2 | 3E-T | 242,170 | 2,134 | 1,737 |
| X2 | 3E-X2 | 229,111 | 2,146 | 1,732 |
| X2 | no control | 287,340 | 2,060 | 1,580 |

- **T2:** X1 5 of 5, margin 16.3-24.2 % against 3E-T; X2 2 of 5, margin 7.5-14.1 % against 3E-X2 (r2:190, :197-198). X2 arm level at 99.17 %: TTC +12.3 [+2.5, +19.8], delay +3.0 [−0.1, +6.4] (r2:206).
- **Flow against p333:** +1.0 [+0.7, +1.6] X1, +1.4 [+0.9, +1.8] X2 (tt2).
- **Against any counting rule:** v3w is worse on no primary measure by point (X2: r2:13, :208; X1: the table).
- **Worse than no control:**
  - X1 TTC<3 s: −16.6 [−25.1, −8.4] (r2:265); round 1 −24.4 [−33.1, −15.4], 5 of 5 policies clearly worse (r1:112, :129; V449, signs corrected in V452).
  - X1 TTC<2 s −27.1 [−31.1, −17.9] and TTC<1.5 s −27.4 [−36.8, −15.2] (r2:323).
  - X1 braking at 3 m/s²: −13.2 [−15.6, −9.6] (cr:312); round 1 −15.7 [−18.5, −14.1], and at 7 m/s² −25.7 [−43.0, −9.7] (r1:152-153).
  - X2 braking at 3 m/s²: −4.8 [−8.1, −0.9] (r1:146).
  - Moving full-emergency events: 15 and 24 in 200 learner-runs, against 0 for no control (r1:202-206).
  - Band at 4,500: −122 [−155, +7], with tiny counts (r2:352, :380).
- X2 TTC against no control is not shown to differ: −0.9 [−5.8, +9.5] (r2:283).

## (c) Claim review

Status: "nothing here is approved" (cr:3).

Survives:
- X1 "W, with the 3E-T bracket ... Not answered against 3E-X1" (cr:9). It is "won in 99-100 % of seed resamples" (cr:37); arm margin 20.3 [15.2, 23.6] at 99.17 % (cr:310).
- X2 against no control "met (harm not shown; sw's CI reaches 12.1 % more close-following)" (cr:10).
- Replication against p333: 5 of 5 at 99.17 % (cr:176).

Struck or closed:
- X2 "N: the DRL claim against tuned rules closes in X2" (cr:10).
- X1 against no control "not met (all three arms harmed on close-following)" (cr:9).
- No delay-win sentence (cr:177). Round 1's X2 win "supports no sentence" (cr:248).
- Recommended out: "safety" for X1 (cr:64), "beats tuned rules", "beats no control", "not harmed" (cr:264), and unqualified "fixed before data" (cr:92).

Strongest objections:
- "A W against the rules beside "not met" against no control is a trade-off, not a net win." (cr:197)
- "X1's 16-24 % margin is set by where the 2 % delay filter cuts the rule family" (cr:29).
- "So the bar separates controllers only on close-following." (cr:187); "no null exists for it" (cr:238).
- "The cells were chosen where DRL already looked best, and were tested repeatedly" (cr:221); [A3] had closed X1 (cr:19).
- "v3w, tail and sw ... are one line of evidence" (cr:222).
- The "counters outside the reward" label "is wrong" (cr:28).
- No MPC or adaptive scheduler was run (cr:243).
- Fragility: X2's negative rests on 3E-T counting "0.19 points inside the filter"; some arm wins X2 in "about 16-20 % of resamples" (cr:22, :233).
- X2's closing "is a pre-registered stop, not evidence that the policies are no better than the rules" (cr:178).

## (d) Delay ceiling

- **Remaining delay under p333:** 242,346 (X1) and 237,372 (X2) veh-s per run, against 322,813 and 287,340 for no control. INFERENCE (ratio of medians): 75 % and 83 % of no-control delay remains. I found no free-flow or unavoidable-delay floor in these sources, so the recoverable share is unknown.
- **Rules below p333 on delay (tt2):**
  - X1: none. Best are lr1000_10_1 −0.9 [−1.7, +0.9] and 3E-T −0.9 [−5.7, +2.4].
  - X2: os0_10_10 +2.8 [+0.5, +5.6], lr1000_10_1 +2.2 [−0.7, +3.7], 3E-X2 +1.5 [−0.1, +3.9].
- **CMA-ES did not probe the ceiling.** Its objective was TTC with a delay hinge at +1 % (p2:58-59). INFERENCE: no delay-minimising rule search exists.
- **Policies below p333:** v3w +5.5 and +6.1 (above); tail +6.4 [+3.1, +9.3] and +5.7 [+3.1, +7.7]; baseline-v3 +1.7 [−1.0, +4.6] and +2.4 [−0.5, +4.3] (tt2).
- **Oracles:** none on plant_c3 in rounds 1-2. On r1m3:
  - the speed-cap oracle's best case was "delay -0.8 to -2.4 %, worse or tied" against p333 (V344);
  - the headway oracle (1.2 s near the slowdown) paid delay −4.5 [−5.5, −3.0] for TTC +56.8 [+46.3, +82.1] (V347).
- "0.8 s gaps cut delay at every level ... a property of the headway, not of DRL" (V419).

## (e) Hypotheses

- **H1, partly supported.**
  - For: V419, V344, V347; no rule beats p333 in X1; attr loses 10-13 % against baseline-v3 (r1:80) and the copy rule 7-14 % against p333 (r1:158-159, r2:285).
  - Against: the v3w arm is 5.5-6.1 % below p333 with CIs above 0 in round 2; the confounded retraining gave about 3.4 % over baseline-v3 (r1:246). The ceiling is near, not reached, and the gap is the size of the noise.
- **H2, supported.**
  - For: TTC<3 s and 3 m/s² braking are reward terms (cr:241); X1 is worse than no control on every threshold (cr:240); X2 "not shown to differ".
  - Against: X2 is better than no control at TTC<1.5 s, +11.4 [+5.3, +15.8], and on the severe check, +21.0 [+8.5, +29.1] (r2:326); the band at 5,000 and 5,250 has CIs above 0, report-only (r2:379).
- **H3, weakly tested.**
  - For: res, 1B and ahead gave no delay gain.
  - Against: ahead's X2 TTC +7.3 [+2.4, +11.2]; copying per-road levels costs delay (r2:285; V361: "not only a position pattern"). Memory, other actuators and other action sets were never tried (cr:214).
- **H4, half supported.**
  - For: the X2 margin fell from 22-31 % against os1_15_10 (r1:120) to 7.5-14.1 % against 3E-X2; both 3E-X searches were "still falling at generation 40" (r2:100).
  - Against: 3E-T's TTC gain shrank from −14.3 % to −4.4 % on fresh seeds (r2:394); 3E-X1 failed the filter on fresh seeds (r2:98); r4a1 "did not hold on fresh seeds" (V368); the X1 margin stays 16-24 %.
- **H5, supported.**
  - For: X2 was won, not replicated (V401, 1 of 5), won, then not won (r2:239-245); tail's and sw's validation advances vanished at test; counting flips with the estimator (r2:444-446); "T2 counts move between seed sets" (r1:253).
  - Against: the TTC edge over p333 replicated 5 of 5 in rounds 1 and 2 (r1:126, r2:224). In confirmatory 3b the replication reading was 3 of 5: TTC held at +28.8 to +39.9 % and the delay limit failed (V401).

**Outside H1-H5:**
1. The bar: 4 of 5 single policies, a 10 % margin and 99.17 % CIs. In X2 the arm is ahead (+12.3 [+2.5, +19.8]) yet "not won". INFERENCE: partly a power and bar-design outcome.
2. No control is the close-following floor in X1, so every short-headway controller, rule or DRL, fails that half (cr:187).
3. Training-recipe variance exceeds the method effects: learner SD 0.3-4.1 % (r1:250-251); reward flat after about update 100 (V413).
4. One demand level, in cells picked for DRL (cr:221).
5. The opponent set lacks MPC and ASCH in these rounds (cr:243).

**Not in these sources:** a recorded mechanism for any round-2 null; an oracle or delay floor on plant_c3; MPC-F, ASCH, the TRUCK condition and Plan B S6.
