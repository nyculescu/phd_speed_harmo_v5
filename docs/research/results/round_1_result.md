# Round 1: result

**Outcome.** None of the three method candidates (3B res, 1A attr, 2C lagr) advanced. The control arm v3w advanced. v3w is baseline-v3's own recipe, retrained over 4,500-6,000 veh/h. On the test (used once, 97.5 % CIs, Bonferroni over 2 cells):
- **T1:** v3w is better than baseline-v3 in X1 and X2.
- **T2:** v3w wins confirmatory 3's tuned reading in both cells. In X1, only the fixed 0.8 s rule counted.
- **Band (reading B):** not shown.
- **Attribution (reading A):** does not apply, because no method candidate reached the test.

The gain therefore comes from retraining baseline-v3's recipe on the wider range, not from a change of method. That retraining changed several things together, and this round cannot separate them:
- the levels and their schedule (3 environments cycling through 7 levels);
- the training seeds;
- the reward references.

```
stage 0 ──► training ─────────► validation, 40 seeds ──► test, 40 + 20 fresh seeds, used once
            v3w   checks pass   advances                 T1 better than baseline-v3: X1 yes, X2 yes
            res   checks pass   did not qualify          T2 won: X1 5/5 (p333 only), X2 5/5 (p333, os1_15_10)
            attr  pass, C2 kept did not qualify, harm    B band: not shown (benefit at 5,500 only)
            lagr  OUT: λ at its cap in 5 of 5            A attribution: not applicable
```

C2 kept: attr's learner 2 failed the collapse check and stayed in, as the protocol requires when only one learner fails (§2).

## 1. Provenance

- **Protocol:** `docs/research/protocols/round_1.md`, revision 2 (V422), approved with its seeds (V423). The lean review is V424.
- **Code:**
  - **Stage 0 started at 08:50 on `b587ed8`.** Guard pausing stalled the end of stage 0a, so the chain was restarted at 10:34 on `93ec97e` (V427). 2,097 of stage 0a's 2,120 rows come from `b587ed8` (V427 recorded 2,096), and the restart ran the rest. The two commits have the same Python code. They differ only in `chain1.sh` (31 evaluation workers instead of the protocol's 64, V426) and the ledger.
  - **The chain-script bug of V438** stopped nothing that produced data. The one minute of res/attr training it touched was deleted and restarted.
- **Machines (V437, a disclosed deviation in schedule and machine):**
  - **Laptop:** stage 0 and v3w training. res also trained there from 15:28 to about update 150 and was frozen at the move. That partial run is kept as a record, not used; res restarted from update 0 on the rented machine.
  - **Rented EPYC 7B13:** res, attr and lagr training, validation and test, with 244 evaluation workers.
  - **Equality** was checked before the move. `checks1.py rows` reproduced every key of the laptop's rows, and the training fingerprint `2b512cb0…` was the same on both machines.
  - **Also a deviation:** on the rented machine, round 2's five DRL trainings (40 learners) and the 3E search ran beside res, attr and lagr (V442-V447). The round-2 trainings ran until 06:23, so they also overlapped validation and the test (V450). The protocol says nothing else runs beside training (V392). That rule exists for speed, and each run has fixed seeds, so the rows are not expected to depend on the load.
- **Throughput (V421):**
  - Stage 0a on the laptop: 64 workers ran 1,200 runs per hour, 31 ran 1,330 and 24 ran 1,372 (V425).
  - Rented machine: validation ran about 5,340 runs per hour, and the test with the band about 5,650.
  - The chain ran from 08:50 on 2026-11-06 to 05:34 on 2026-11-07.
- **Seeds,** as approved:
  - stage 0: 7,440,300-319, 340-359 and 370-389;
  - validation: 7,440,400-439;
  - test: 7,440,500-539 and band 7,440,540-559, each used once;
  - training: 7,464,000-7,471,799.
- **Timeline:**
  - stage 0: 2026-11-06, 08:50-11:20, restarted at 10:34;
  - v3w trained 11:20-15:28;
  - res, attr and lagr trained in parallel 17:02-04:18;
  - validation 04:18-04:57 and the test 04:57-05:34 on 2026-11-07.
- **Data and tables:**
  - The raw rows are in `/home/catalin/work/phd/v5b1_runs/round1_remote/out`.
  - The readings are in `test_result.json` and `validation.json`. They were copied to `docs/research/round1/report/`, together with `test_table.csv` (every arm, all counters, the splits and effects at 95 %) and `band_table.csv`. Those tables come from `docs/research/round1/report1.py`, which reads stored rows only.
  - An independent check re-derived every number with its own code. Its scripts are in `docs/research/round1/report/verify/`.
- **Sign convention:** effect = sign × median(P − O) / median(O) × 100 over paired seeds (`common.raw`). Positive means P has **less** delay, close-following or braking, or **more** flow. This is checked in the code, and every table here uses it.
  - **V449 mixes two conventions.**
  - Its T1 values are negated: delay −3.5 % and TTC −4.2 % mean less of each (+3.5 and +4.2 here).
  - Its validation values follow `common.raw`. res delay −1.6 % [−3.5, +1.5] means 1.6 % more delay than the incumbent, with the CI including 0. TTC +9.6 % (res) and +33 % (attr) mean fewer close-following seconds than os1_15_10.

## 2. Stage 0 and training

- **0a (report-only, 20 seeds):**
  - Over the 5 learners, the checkpoint score's rank correlation with u500 is −0.5 (u100), −0.8 (u150) and −0.9 (u250), so early checkpoints do not predict the final ranking (V429).
  - On these seeds the checkpoint rule chose u250 only for d3. That checkpoint clears X2, where its u500 fails on delay. At validation, baseline-v3 chose u500 for all 5.
- **0b:**
  - No baseline-v3 policy met J ≤ 0.97 (J was 1.016-1.026), so 2C trained.
  - The rules' own J is 1.025-1.035, because J averages ratios to a median. The 0.97 target therefore sat about 6 % below the rules' mean delay, not 3 %. This question was put to the author and never answered (V429, V448).
- **0c:** the reward references at the 7 training levels were written to every candidate's environment, v3w included.
- **Training checks (`tbcheck1.py`):**
  - v3w and res passed in all 5 learners.
  - **attr** passed as a candidate, but its learner C2 failed the collapse check: a = 0.0398 against 0.4 σ = 0.038 (b = +0.053, so b passed). The protocol keeps one failing learner in, with this disclosure, so C2 is in attr's validation arm.
  - **2C is out of the round:** λ sat at its cap of 10 over the last 100 updates in all 5 learners (the rule needs at least 3), with no collapse and clean logs. The protocol's label is "constraint not met at the cap".

## 3. Validation (40 seeds, 95 % CIs, no correction)

Delay is against the incumbent arm. TTC is close-following seconds (TTC below 3 s) against os1_15_10. Each arm is the per-seed mean over 5 learners at their chosen checkpoints. Baseline-v3 chose u500 for all 5 learners.

| Candidate | Checkpoints chosen | X1 delay | X1 TTC | X2 delay | X2 TTC | Verdict |
|---|---|---|---|---|---|---|
| v3w | u250 ×2, u500 ×3 | +3.7 [+0.8, +5.3] | +32.1 [+29.2, +35.5] | +3.0 [+1.2, +4.8] | +24.8 [+19.2, +32.6] | qualifies in both cells; advances |
| res (3B) | u250 ×1, u500 ×4 | −1.6 [−3.5, +1.5] | +9.6 [+4.5, +11.8] | +2.4 [−0.7, +4.3] | +10.0 [+7.2, +17.6] | does not qualify: delay CI includes 0, and TTC is below the 10 % bar (X2 is 9.99) |
| attr (1A) | u250 ×3, u500 ×2 | −13.5 [−14.5, −11.4] | +32.9 [+30.4, +38.5] | −10.4 [−11.9, −9.1] | +25.2 [+20.7, +31.3] | harm in both cells: delay clearly worse than the incumbent |

Against no control (95 %), at the chosen checkpoints:

| Arm | X1 delay | X1 TTC | X2 delay | X2 TTC |
|---|---|---|---|---|
| v3w | +28.0 [+23.8, +31.4] | −22.0 [−30.9, −16.8] | +23.3 [+21.8, +24.6] | −0.4 [−5.5, +13.8] |
| res | +25.8 [+21.6, +28.9] | −69.3 [−72.3, −56.0] | +22.0 [+20.3, +24.0] | −23.6 [−33.8, −7.6] |
| attr | +14.8 [+13.1, +18.1] | −18.8 [−24.6, −14.9] | +12.5 [+10.6, +13.7] | −6.2 [−9.7, +10.4] |
| baseline-v3 | +27.0 [+23.6, +28.8] | −30.7 [−35.7, −22.6] | +20.0 [+18.4, +22.6] | −4.4 [−14.4, +2.1] |

No floor KILL. Every u500 arm had at least 27.9 % fewer TTC seconds than p333, and 14-29 % less delay than no control.

v3w was the only finalist, so m = 1 × 2 = 2 and the test's Bonferroni level is 1 − 0.05/2 = 97.5 %, two-sided: bootstrap percentiles 1.25 and 98.75, as `decide1.bonferroni(2)` returns and as confirmatory 3 labels them. The protocol's text says "98.75 % for m = 2", which does not match its own formula: 98.75 is the upper percentile. At a true two-sided 98.75 % level every T1 and T2 verdict is unchanged: T1 delay X1 +3.5 [+1.1, +5.4] and X2 +3.4 [+0.8, +5.0]; T2 5 of 5 in both cells.

## 4. Test, used once (X1 and X2 at 5,300 veh/h, 40 seeds)

**Cells.** Times are on the simulation clock; the counters cover 300-1,800 s.
- **X1:** two tapered slowdowns (20-s taper, 120 s each) to 25 km/h, at 600 and 1,200 s, on edge 4. Edge 4 is the 1-km three-lane road after merge 2's accelerating section 4a. In the TTC split below, edge 4 counts under road "rest".
- **X2:** one tapered slowdown (20-s taper, 180 s) to 30 km/h, at 700 s, on edge 3. Edge 3 is the 1.2-km road between the two merges.

**Reading T1, against baseline-v3 (97.5 % CIs):**

| Cell | Delay | TTC seconds | Verdict |
|---|---|---|---|
| X1 | +3.5 [+1.2, +5.3] | +4.2 [+0.8, +8.3] | better |
| X2 | +3.4 [+1.0, +4.8] | +0.8 [−5.0, +5.9] | better |

Both arms against no control (95 %):

| Cell | v3w delay | v3w TTC | baseline-v3 delay | baseline-v3 TTC |
|---|---|---|---|---|
| X1 | +28.0 [+25.4, +30.6] | −24.4 [−33.1, −15.4] | +24.8 [+22.4, +28.3] | −31.4 [−34.6, −27.6] |
| X2 | +23.2 [+20.5, +25.6] | −1.9 [−7.1, +9.2] | +19.4 [+17.4, +23.1] | +1.8 [−13.8, +6.8] |

**Reading T2, confirmatory 3's tuned reading (97.5 % CIs):**

| Cell | Rules that count | v3w | Baseline-v3, same seeds | v3w's TTC gain over the strongest counting rule, per learner | No control |
|---|---|---|---|---|---|
| X1 | p333 only | **won, 5 of 5** | 2 of 5, not won: 3 blocked on delay or flow against p333 | 35-46 % against p333 | 1,436 TTC seconds, 39.2 % more delay |
| X2 | p333, os1_15_10 | **won, 5 of 5** | 4 of 5, also won: d3 blocked on delay against p333 | 22-31 % against os1_15_10 | 1,436 TTC seconds, 29.8 % more delay |

**Reported beside (confirmatory 3's readings):**

| Reading | X1 | X2 |
|---|---|---|
| Replication against p333 (TTC ≥ 30 % better) | 5 of 5 | 5 of 5 |
| Delay win | 0 of 5 | 0 of 5 |
| Severe-conflict check ("safety" gate) | met | met |
| Policies clearly worse than no control on TTC | 5 of 5 | 0 of 5 |
| No control's extra delay against the policies | 39.2 % | 29.8 % |

Baseline-v3's final policies equal its chosen checkpoints (u500 for every learner), so their rows are identical (`final_vs_chosen_incumbent` = 0).

### Sentences allowed (confirmatory 3's table, filled from this run)

Model: an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds.

- **X2, cell won on TTC:** Under a tapered slowdown to 30 km/h for 180 s on the road between the ramps (X2), 5 of 5 per-CAV PPO headway policies (v3w, trained at 4,500-6,000 veh/h) had fewer seconds at TTC below 3 s than each of the 2 counting rules: the fixed p333, and os1_15_10, tuned on separate seeds. Over the 5 policies the margin was 22-31 % against the counting rule with the lowest TTC (os1_15_10), with delay and flow within the stated limits. This is a surrogate.
  - *Where the gain is.* Against os1_15_10: median paired difference in TTC samples, 40 seeds, 95 % CI.
    - **Roads:** mostly on edges 3 and 4a, 219 [164, 254] and 131 [105, 217], about three quarters of the gain.
    - **Speeds:** at every follower speed: below 5 m/s 135 [96, 200]; 5-10 m/s 145 [99, 180]; 10 m/s or more 230 [179, 249]. The fastest band is the largest, but under half the gain.
    - **Time:** mostly in "rest" (1,000-1,800 s, 800 of the 1,500 counted seconds): 456 [356, 573]. "rest" is a time window; no counter shows whether these samples are in a queue.
  - Not counting, by the delay filter against p333: r4a1 −3.1 %, lr1000_16_2 −2.9 % and a4400_10_1 −4.9 %. a4400_10_1 has 1,847 TTC seconds, fewer than os1_15_10's 1,902.
  - **No control,** medians per run: 1,436 TTC seconds, 279,918 vehicle-seconds of delay, 3,210 vehicle-seconds of braking at 3 m/s².
    - The policies' TTC seconds are not shown to differ from it (−1.9 [−7.1, +9.2], 95 %), and no control pays 29.8 % more delay.
    - The policies brake at 3 m/s² 4.8 % more than no control (−4.8 [−8.1, −0.9], 95 %).
- **X1, only p333 counted:** The same, under two tapered slowdowns to 25 km/h for 120 s on edge 4, against the fixed 0.8 s rule (35-46 %).
  - No other rule met the delay filter. Paired delay against p333: z33133 −5.2 %, lr400_13_2 −4.8 %, os0_10_10 −5.1 %.
  - *Where the gain is:* edges 4a and 3, follower speeds below 5 m/s, and the periods after each slowdown ends ("after" and "rest").
  - **No control had fewer such seconds, at 39.2 % more delay.**
    - No control's medians per run: 1,436 TTC seconds, 325,289 vehicle-seconds of delay, 3,144 vehicle-seconds of braking at 3 m/s².
    - The policies brake at 3 m/s² 15.7 % more than no control (−15.7 [−18.5, −14.1], 95 %).
    - At 7 m/s² they brake 25.7 % more (−25.7 [−43.0, −9.7], 95 %; medians 4.0 against 3.0 s per run).
- **Both cells:**
  - The severe-conflict check is met, so confirmatory 3's rule permits the word "safety". The X1 no-control clause must stay beside it.
  - **Collisions are too rare to compare.** Per 40 runs: v3w 0.2 (one in 200 learner-runs per cell); baseline-v3 0; the rules 0-1; no control 1 (X1) and 0 (X2).
  - **The copy rule did not meet the delay filter.** It is confirmatory 3's fixed per-road rule, traced from baseline-v3's policies.
    - X1: 2,215 TTC seconds per run, delay −13.6 [−17.7, −9.2] against p333.
    - X2: 1,756 TTC seconds, fewer than os1_15_10's 1,902, delay −10.3 [−12.6, −7.5] against p333.
    - Report-only: against the copy rule, v3w clears the margins with 5 of 5 policies in X1 (TTC +13.3 to +26.6 %) and 4 of 5 in X2 (learner 4: +9.2 [+5.8, +18.4], below the 10 % margin), at 9.8-13.3 % less delay.
  - Round 1 ran no map cells, so cells other than X1 and X2 at 5,300 are not shown to be unharmed.

**About the split counters.** The "where" lines come from the TTC split counters, not from tests. In every run, the road, speed and period splits each add up to the deciding count. `ttc3` is the same 1-Hz test as `ttc_net`, taken in the same second, so the two are equal by construction. Medians do not add up. The table below leaves out road "rest", 5-10 m/s, and the before, taper and hold periods.

Medians per arm, TTC seconds below 3 s:

| Split | X1 v3w | X1 p333 | X1 no control | X2 v3w | X2 os1_15_10 | X2 no control |
|---|---|---|---|---|---|---|
| edge 3 | 415 | 828 | 250 | 313 | 522 | 93 |
| edge 4a | 971 | 1,660 | 673 | 714 | 870 | 621 |
| ramp 2 | 365 | 427 | 454 | 282 | 331 | 305 |
| below 5 m/s | 718 | 1,312 | 593 | 616 | 713 | 555 |
| above 10 m/s | 468 | 822 | 357 | 381 | 586 | 369 |
| after each slowdown (120 s each; X1 has two) | 425 | 720 | 338 | 93 | 103 | 164 |
| rest (X1 840-1,200 and 1,440-1,800 s; X2 1,000-1,800 s) | 1,094 | 1,903 | 799 | 1,286 | 1,706 | 1,069 |

### Counters with no control beside (medians over 40 runs)

**Definitions:**
- Each policy arm is the per-seed mean over 5 learners. All 12 rule arms (the copy rule included) and no control are in `test_table.csv`.
- Delay is in vehicle-seconds and includes unfinished vehicles and the insertion queue.
- Flow is the number of vehicles that reach edge 4, past both merges, in the 1,500-s window after warm-up; vehicles already on edge 4 at the start are not counted. 2,132 is about 5,120 veh/h.
- Severe counts the 1-Hz samples whose deceleration needed to avoid the leader is at least 3 m/s².

| Cell | Arm | Delay | Flow (vehicles per 1,500 s) | TTC < 3 s | Severe | Braking ≥ 3 m/s² (step) | Braking ≥ 7 m/s² (step) | Moving full-emergency, ALKS (events per run) |
|---|---|---|---|---|---|---|---|---|
| X1 | v3w | 227,631 | 2,132 | 1,825 | 95 | 3,649 | 4.0 | 0 |
| X1 | baseline-v3 | 237,820 | 2,120 | 1,866 | 91 | 3,624 | 4.1 | 0 |
| X1 | p333 | 229,735 | 2,124 | 3,068 | 159 | 4,277 | 4.5 | 0 |
| X1 | os1_15_10 | 240,686 | 2,097 | 2,606 | 136 | 4,020 | 4.4 | 0 |
| X1 | no control | 325,289 | 2,023 | 1,436 | 87 | 3,144 | 3.0 | 0 |
| X2 | v3w | 218,702 | 2,159 | 1,504 | 77 | 3,368 | 3.5 | 0 |
| X2 | baseline-v3 | 221,979 | 2,139 | 1,498 | 75 | 3,313 | 3.5 | 0 |
| X2 | p333 | 223,716 | 2,134 | 2,449 | 137 | 3,863 | 4.4 | 0 |
| X2 | os1_15_10 | 225,575 | 2,137 | 1,902 | 114 | 3,551 | 4.0 | 0 |
| X2 | no control | 279,919 | 2,063 | 1,436 | 92 | 3,210 | 3.4 | 0 |

**Moving full-emergency events.** The medians of 0 hide rare events. Events per run (counts in brackets):

| Arm | X1 | X2 |
|---|---|---|
| v3w | 0.075 (15 in 200 learner-runs) | 0.12 (24/200) |
| baseline-v3 | 0.085 (17/200) | 0.09 (18/200) |
| p333 | 0.075 (3/40) | 0.15 (6/40) |
| os1_15_10 | 0.10 (4/40) | 0.15 (6/40) |
| no control | 0 | 0 |

**Delay against the rules (descriptive, not a reading; 95 %):**
- v3w's arm has less delay than os1_15_10: X1 +5.5 [+3.1, +10.5], X2 +4.7 [+1.3, +7.2].
- It also has less delay than each cell's delay opponent: X1 lr1000_10_1 +4.3 [+2.4, +6.3], X2 os1_10_0 +6.6 [+3.4, +9.5].
- Against p333 it has less delay in X2 (+3.7 [+1.7, +5.0]). In X1 the CI includes 0 (+2.6 [−1.8, +5.4]).
- The delay-win reading compares each policy with the lower-delay of p333 and the delay opponent, which is p333 in both cells, and needs at least 5 %. The 5 policies reach 0.2-3.8 % (X1) and 1.9-4.3 % (X2), so the delay-win reading is 0 of 5.

**1-Hz against step braking (blind-spot check, 5 % limit):**
- Every test arm is within the limit: the largest deviation is 4.4 % on braking and 1.9 % on TTC.
- In the band runs, 10 single-learner arms count 5-7 % less braking at 1 Hz than every 0.1 s (ratio 0.93-0.95). So do three 5-learner arms: v3w at 5,250 (0.947), which is the arm reading B reads, and baseline-v3 at 5,000 (0.948) and 5,250 (0.940). No reading uses the 1-Hz braking count.
- One arm (w1 at 4,500) has a whole/half-second TTC ratio of 0.89 (medians 72.5 and 81.5 per run, above the check's 50-count floor). Reading B reads the v3w arm, whose ratio there is 1.03, and 4,500 is an edge level that is not required, so no verdict changes.

## 5. Reading B, the band (20 fresh seeds, training slowdowns, 95 %: one arm read)

"Training slowdowns" is the training's random draw per seed: 6 of the 20 band seeds have no slowdown, and the other 14 have one, on edge 3 (6), 4 (2) or 5 (6).

Close-following seconds against no control (positive = fewer). Delay is against no control.

| veh/h | v3w TTC | v3w delay | baseline-v3 TTC (report-only) | p333 TTC | os1_15_10 TTC |
|---|---|---|---|---|---|
| 4,500 (edge) | −17 [−112, +642] | +23 [+21, +30] | −53 [−99, +250] | −10 | +30 |
| 5,000 | +38 [−10, +71] | +26 [+21, +31] | +20 [−6, +51] | −13 | −5 |
| 5,250 | +36 [−1, +76] | +32 [+27, +38] | +25 [+0.7, +76] | +28 | −30 |
| 5,500 | **+29 [+5, +50]** | +29 [+25, +38] | +23 [−7, +46] | −65 | −26 |
| 6,000 (edge) | +7.6 [+2.4, +13.8] | +27 [+22, +30] | −4.9 [−12.8, +1.8] | −65 | −18 |

- **Not shown** for v3w: the benefit holds at 5,500 only. At 5,000 and 5,250 the point estimates are 36-38 %, but the CIs reach below 0 with 20 seeds.
- Baseline-v3 (report-only) is not shown either: its benefit holds at 5,250 only.
- At 4,500 the counts are tiny (no control has about 40 s per run), hence the very wide CI.
- At 6,000, v3w is the only arm with fewer close-following seconds than no control and its CI is clear of 0, but 7.6 % is below the 10 % bar. Edges are not required either way.

## 6. What this means

1. **No method change helped in this round:**
   - res tied the incumbent on delay and kept only a third to a half of its close-following margin over os1_15_10 (9.6 % and 10.0 %, against the incumbent's 28.8 % and 21.5 % at validation);
   - attr bought its margin with 10-13 % more delay;
   - lagr did not meet its delay target. That target sat about 6 % below the rules' mean delay rather than the intended 3 % (§2).
   - With 3 candidates in one round, this does not show that no change to the state, action, reward or algorithm would help (protocol, "What this cannot show").
2. **v3w is better than baseline-v3 (T1):**
   - v3w has about 3.4 % less delay than baseline-v3 in both cells (X1 +3.5 [+1.2, +5.3], X2 +3.4 [+1.0, +4.8], 97.5 %).
   - Close-following is lower in X1 (+4.2 [+0.8, +8.3]). In X2 it is not shown to differ (+0.8 [−5.0, +5.9]).
   - v3w differs from baseline-v3 in range, schedule, reward references and training seeds (protocol, Disclosures). Each recipe was trained once, so the gain is not attributed to the range alone.
   - The T1 intervals cover evaluation seeds only; the 5 learners are fixed. Median delay per learner (exploratory):
     - baseline-v3: 230,915-247,277 (X1) and 216,348-240,328 (X2), SD 2.6 % and 4.1 % of the mean;
     - v3w: 226,277-228,153 and 214,767-221,549, SD 0.3 % and 1.3 %.
     - In X1 every v3w learner has less delay than every baseline-v3 learner. In X2 the ranges overlap.
   - **T2:** v3w wins with 5 of 5 in both cells. Baseline-v3 gets 2 of 5 in X1 (not won) and 4 of 5 in X2, which also wins that cell. On confirmatory 3b's 20 fresh seeds, the same baseline-v3 policies got 1 of 5 in X2 (V401). So T2 counts move between seed sets and do not compare the two recipes.
3. **Limits on any claim:**
   - **X1** counts only the fixed 0.8 s rule, and no control has fewer close-following seconds there.
   - **X2** is the cleaner cell. v3w won T2 against both counting rules there (p333, which is fixed, and os1_15_10, which is tuned). Its close-following is not shown to differ from no control's (−1.9 [−7.1, +9.2], 95 %), at about 23 % less delay.
   - **The rules were not re-tuned.** 3E's CMA-ES rule had 14.3 % fewer TTC seconds than os1_15_10, at 2.0 % more delay. Those figures are pooled over the training slowdowns (condition T) at 4,500-6,000 veh/h, on its own 40 tuning seeds (V448), not measured in X1 or X2 at 5,300. Still, the margin against a properly tuned rule may shrink. The protocol recommends that search before any thesis claim.
   - **Other limits:**
     - checkpoint selection between u250 and u500, rather than final policies only;
     - the 2 % delay limit is judged on a point estimate, with a CI half-width of about 3-6 points. At 40 seeds it passes a policy truly 2 % worse about half the time (V435);
     - the TTC count is a surrogate;
     - the plant is uncalibrated;
     - V2V is ideal.
4. **Disclosures from the protocol** (round_1.md, "Disclosures"), beyond the limits above:
   - **Teaching to the test:** the judged 1-Hz flag (TTC below 3 s) is a term of v3w's reward, as it was of baseline-v3's.
     - The counters outside the reward agree against the counting rules (95 %, arm against rule; X1 against p333, X2 against os1_15_10):
       - TTC below 2 s: X1 +66.0 [+60.6, +71.6]; X2 +47.8 [+39.7, +56.0].
       - TTC below 1.5 s: X1 +60.4 [+56.4, +67.7]; X2 +36.1 [+27.8, +48.9].
       - The severe check: X1 +41.3 [+33.2, +49.7]; X2 +30.4 [+20.4, +43.6].
     - Against no control:
       - X1 is worse on all three (TTC below 2 s: −37.4 [−41.9, −31.7]).
       - X2 is not shown to differ at 2 s (−3.0 [−10.8, +3.4]). It is better at 1.5 s (+8.6 [+1.1, +19.8]) and on the severe check (+18.2 [+9.1, +24.9]).
   - **2C's J is measured on the sampled actions of training.** d_ref comes from the rules, and the 0b stop from greedy policies, so λ may have risen partly from exploration. lagr's exit therefore concerns this constraint, whose target sat about 6 % below the rules, not PPO-Lagrangian in general.
   - **3B's range:** ±1 cannot reach 1.2 s from 0.8 s, and the from-scratch policies use longer gaps (V413).
   - **1A's attribution** is a heuristic, not causal.
   - **The band was chosen after the sweep's data** (V419, post hoc). Reading B tested it on fresh seeds.
   - **Literature:** PPO-Lagrangian, residual policy learning and the attribution idea are named families [VERIFY]. None is claimed as new.

## 7. Open, for the author

- Whether v3w replaces baseline-v3 as the incumbent (baseline v4). The protocol fixes T1's test but not what follows from it.
- Round 2's evaluation protocol: fresh validation and test seeds, and the opponents, with 3E's winner as the tuned rule once it moves into `b_env.py`. The 5 round-2 DRL candidates have trained and passed their checks (V450). A draft is in `docs/research/protocols/round_2.md`.
- round_1.md's Multiplicity line ("98.75 % for m = 2, 99.375 % for m = 4") mislabels the levels. The code applied 1 − 0.05/m. The protocol text is left unchanged, as approved.
