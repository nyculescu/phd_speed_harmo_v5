# Round 1: result

**Outcome.** None of the three method candidates (3B res, 1A attr, 2C lagr) advanced. The control arm v3w advanced. v3w is baseline-v3's own recipe, retrained over 4,500-6,000 veh/h. On the test (used once, 98.75 % CIs):
- **T1:** v3w is better than baseline-v3 in X1 and X2.
- **T2:** v3w wins confirmatory 3's tuned reading in both cells. In X1, only the fixed 0.8 s rule counted.
- **Band (reading B):** not shown.
- **Attribution (reading A):** does not apply, because no method candidate reached the test.

The gain therefore comes from the wider training range, not from a change of method.

```
stage 0 ──► training ─────────► validation, 40 seeds ──► test, 40 + 20 fresh seeds, used once
            v3w   checks pass   advances                 T1 better than baseline-v3: X1 yes, X2 yes
            res   checks pass   did not qualify          T2 won: X1 5/5 (p333 only), X2 5/5 (p333, os1_15_10)
            attr  checks pass   did not qualify, harm    B band: not shown (benefit at 5,500 only)
            lagr  OUT: λ at its cap in 5 of 5            A attribution: not applicable
```

## 1. Provenance

- **Protocol:** `docs/research/protocols/round_1.md`, revision 2 (V422), approved with its seeds (V423). The lean review is V424.
- **Code:**
  - Snapshot `93ec97e` for the whole run. Its Python code is the same as `b587ed8`; the two differ only in `chain1.sh` and the ledger.
  - The chain-script bug of V438 stopped nothing that produced data. The one minute of res/attr training it touched was deleted and restarted.
- **Machines (V437, a disclosed deviation in schedule and machine only):**
  - laptop: stage 0 and v3w training;
  - rented EPYC 7B13: res, attr and lagr training, validation and test.
  - Equality was checked before the move. `checks1.py rows` reproduced every key of the laptop's rows, and the training fingerprint `2b512cb0…` was the same on both machines.
- **Seeds,** as approved:
  - stage 0: 7,440,300-319, 340-359 and 370-389;
  - validation: 7,440,400-439;
  - test: 7,440,500-539 and band 7,440,540-559, each used once;
  - training: 7,464,000-7,471,799.
- **Timeline:**
  - stage 0 ran on 2026-11-06, 10:34-11:20;
  - v3w trained 11:20-15:28;
  - res, attr and lagr trained in parallel 17:02-04:18;
  - validation ran 04:18-04:57 and the test 04:57-05:34 on 2026-11-07.
- **Data and tables:**
  - The raw rows are in `/home/catalin/work/phd/v5b1_runs/round1_remote/out`.
  - The readings are in `test_result.json` and `validation.json`. They were copied to `docs/research/round1/report/`, together with `test_table.csv` (every arm, all counters, the splits and effects at 95 %) and `band_table.csv`.
  - Those tables come from `docs/research/round1/report1.py`, which reads stored rows only.
- **Sign convention:** effect = sign × median(P − O) / median(O) × 100 over paired seeds (`common.raw`). Positive means P has **less** delay, close-following or braking, or **more** flow. This is checked in the code, so the hedge in V449 is no longer needed.

## 2. Stage 0 and training

- **0a (report-only):** the checkpoint score at u100-u250 ranks the learners opposite to u500. Early checkpoints do not predict the final ranking (V429).
- **0b:**
  - No baseline-v3 policy met J ≤ 0.97 (J was 1.016-1.026), so 2C trained.
  - The rules' own J is 1.025-1.035, because J averages ratios to a median. The 0.97 target therefore sits about 6 % below the rules' mean delay, not 3 %. This question was put to the author and never answered (V429, V448).
- **0c:** the reward references at the 7 training levels were written to every candidate's environment, v3w included.
- **Training checks (`tbcheck1.py`):**
  - v3w, res and attr passed.
  - **2C is out of the round:** λ ended at its cap of 10 in all 5 learners (the rule needs at least 3), with no collapse and clean logs. The protocol's label is "constraint not met at the cap".

## 3. Validation (40 seeds, 95 % CIs, no correction)

Delay is against the incumbent arm. TTC is the close-following seconds at TTC below 3 s, against os1_15_10. Each arm is the per-seed mean over 5 learners at their chosen checkpoints. Baseline-v3 chose u500 for all 5 learners.

| Candidate | Checkpoints chosen | X1 delay | X1 TTC | X2 delay | X2 TTC | Verdict |
|---|---|---|---|---|---|---|
| v3w | u250 ×2, u500 ×3 | +3.7 [+0.8, +5.3] | +32.1 [+29.2, +35.5] | +3.0 [+1.2, +4.8] | +24.8 [+19.2, +32.6] | qualifies in both cells; advances |
| res (3B) | u250 ×1, u500 ×4 | −1.6 [−3.5, +1.5] | +9.6 [+4.5, +11.8] | +2.4 [−0.7, +4.3] | +10.0 [+7.2, +17.6] | does not qualify: delay CI includes 0, and TTC is below the 10 % bar (X2 is 9.99) |
| attr (1A) | u250 ×3, u500 ×2 | −13.5 [−14.5, −11.4] | +32.9 [+30.4, +38.5] | −10.4 [−11.9, −9.1] | +25.2 [+20.7, +31.3] | harm in both cells: delay clearly worse than the incumbent |

No floor KILL. Every u500 arm had at least 27.9 % fewer TTC seconds than p333, and 14-29 % less delay than no control. v3w was the only finalist, so the test's Bonferroni level is 1 − 0.05/2, two-sided: 98.75 %.

## 4. Test, used once (X1 and X2 at 5,300 veh/h, 40 seeds)

**Cells:**
- **X1:** two 120-s slowdowns to 25 km/h on edge 4, at 600 and 1,200 s.
- **X2:** one 180-s slowdown to 30 km/h on edge 3, at 700 s.

**Reading T1, against baseline-v3 (98.75 % CIs):**

| Cell | Delay | TTC seconds | Verdict |
|---|---|---|---|
| X1 | +3.5 [+1.2, +5.3] | +4.2 [+0.8, +8.3] | better |
| X2 | +3.4 [+1.0, +4.8] | +0.8 [−5.0, +5.9] | better |

**Reading T2, confirmatory 3's tuned reading (98.75 % CIs):**

| Cell | Rules that count | v3w | Baseline-v3, same seeds | v3w's TTC gain over the strongest counting rule, per learner |
|---|---|---|---|---|
| X1 | p333 only | **won, 5 of 5** | 2 of 5: 3 blocked on delay or flow against p333 | 35-46 % against p333 |
| X2 | p333, os1_15_10 | **won, 5 of 5** | 4 of 5 | 22-31 % against os1_15_10 |

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

- **X2, cell won on TTC:** Under one 180-s slowdown to 30 km/h (X2), 5 of 5 per-CAV PPO headway policies (v3w, trained at 4,500-6,000 veh/h) had fewer seconds at TTC below 3 s than each of 2 counting rules tuned on separate seeds. Over the 5 policies the margin was 22-31 % against the counting rule with the lowest TTC (os1_15_10), with delay and flow within the stated limits. This is a surrogate.
  - *Where the gain is:* mostly on edges 3 and 4a, at follower speeds above 10 m/s, and in the queue after the slowdown ("rest", 1,000-1,800 s).
  - No control: the policies' TTC seconds are not shown to differ from it, and no control pays 29.8 % more delay.
- **X1, only p333 counted:** The same, against the fixed 0.8 s rule (35-46 %). No other rule met the delay filter.
  - *Where the gain is:* edges 4a and 3, follower speeds below 5 m/s, and the periods after each slowdown ends ("after" and "rest").
  - **No control had fewer such seconds, at 39.2 % more delay.**
- **Both cells:**
  - The severe-conflict check is met, so confirmatory 3's rule permits the word "safety". The X1 no-control clause must stay beside it.
  - Collisions are too rare to compare. Per 40 runs: v3w 0.2 (one in 200 learner-runs per cell); baseline-v3 0; the rules 0-1; no control 1 (X1) and 0 (X2).
  - Round 1 ran no map cells, so cells other than X1 and X2 at 5,300 are not shown to be unharmed.

The "where" lines are medians of the TTC split counters, not tests. Their totals equal the deciding count (the `ttc3` median equals the `ttc_net` median in every arm). Medians per arm, TTC seconds below 3 s:

| Split | X1 v3w | X1 p333 | X1 no control | X2 v3w | X2 os1_15_10 | X2 no control |
|---|---|---|---|---|---|---|
| edge 3 | 415 | 828 | 250 | 313 | 522 | 93 |
| edge 4a | 971 | 1,660 | 673 | 714 | 870 | 621 |
| ramp 2 | 365 | 427 | 454 | 282 | 331 | 305 |
| below 5 m/s | 718 | 1,312 | 593 | 616 | 713 | 555 |
| above 10 m/s | 468 | 822 | 357 | 381 | 586 | 369 |
| after slowdown (120 s) | 425 | 720 | 338 | 93 | 103 | 164 |
| rest | 1,094 | 1,903 | 799 | 1,286 | 1,706 | 1,069 |

### Counters with no control beside (medians over 40 runs)

Each policy arm is the per-seed mean over 5 learners. All 13 opponents are in `test_table.csv`. Delay is in vehicle-seconds and includes unfinished vehicles and the insertion queue.

| Cell | Arm | Delay | Flow | TTC < 3 s | Severe | Braking ≥ 3 m/s² (step) | Braking ≥ 7 m/s² (step) | Moving full-emergency |
|---|---|---|---|---|---|---|---|---|
| X1 | v3w | 227,631 | 2,132 | 1,825 | 95 | 3,650 | 4.0 | 0 |
| X1 | baseline-v3 | 237,820 | 2,120 | 1,866 | 91 | 3,624 | 4.1 | 0 |
| X1 | p333 | 229,735 | 2,124 | 3,068 | 159 | 4,277 | 4.5 | 0 |
| X1 | os1_15_10 | 240,686 | 2,097 | 2,606 | 136 | 4,020 | 4.4 | 0 |
| X1 | no control | 325,289 | 2,023 | 1,436 | 87 | 3,144 | 3.0 | 0 |
| X2 | v3w | 218,702 | 2,159 | 1,504 | 77 | 3,369 | 3.5 | 0 |
| X2 | baseline-v3 | 221,979 | 2,139 | 1,498 | 75 | 3,313 | 3.5 | 0 |
| X2 | p333 | 223,716 | 2,134 | 2,449 | 137 | 3,863 | 4.4 | 0 |
| X2 | os1_15_10 | 225,575 | 2,137 | 1,902 | 114 | 3,551 | 4.0 | 0 |
| X2 | no control | 279,918 | 2,063 | 1,436 | 92 | 3,210 | 3.4 | 0 |

**Descriptive, not a reading:** v3w's arm has less delay than os1_15_10 (X1 +5.5 [+3.1, +10.5], X2 +4.7 [+1.3, +7.2], 95 %). It does not have less delay than p333 or the delay opponent, so the delay-win reading is 0 of 5.

**1-Hz against step braking (blind-spot check, 5 % limit):**
- Every test arm is within the limit.
- In the band runs, 10 single-learner arms count 5-7 % less braking at 1 Hz than every 0.1 s (ratio 0.93-0.95). One arm (w1 at 4,500) has a whole/half-second TTC ratio of 0.89, on small counts (the v3w arm's median there is 74 s per run).
- No reading uses the 1-Hz braking count, so no verdict changes.

## 5. Reading B, the band (20 fresh seeds, training slowdowns, 95 %: one arm read)

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
   - res tied the incumbent on delay and lost most of the close-following margin;
   - attr bought its margin with 10-13 % more delay;
   - lagr could not meet its delay constraint.
   - With 3 candidates in one round, this does not show that no change to the state, action, reward or algorithm would help (protocol, "What this cannot show").
2. **The wider training range helped:**
   - v3w has about 3.4 % less delay than baseline-v3 in both cells, at equal (X2) or lower (X1) close-following;
   - it wins T2 with 5 of 5 in both cells, where baseline-v3 gets 2 of 5 (X1) and 4 of 5 (X2) on the same fresh seeds.
3. **Limits on any claim:**
   - **X1** counts only the fixed 0.8 s rule, and no control has fewer close-following seconds there.
   - **X2** is the cleaner cell. Against two tuned rules, v3w's close-following is not shown to differ from no control's (−1.9 [−7.1, +9.2], 95 %), at about 23 % less delay.
   - **The rules were not re-tuned.** 3E's CMA-ES rule had 14.3 % fewer TTC seconds than os1_15_10, at +2.0 % delay, on its own tuning seeds (V448). The margin against a properly tuned rule may shrink. The protocol recommends that search before any thesis claim.
   - **Other limits:**
     - checkpoint selection between u250 and u500, rather than final policies only;
     - the 2 % delay limit is judged on a point estimate, with a CI half-width of about 3-6 points;
     - the TTC count is a surrogate;
     - the plant is uncalibrated;
     - V2V is ideal.

## 7. Open, for the author

- Whether v3w replaces baseline-v3 as the incumbent (baseline v4). The protocol fixes T1's test but not what follows from it.
- Round 2's evaluation protocol: fresh validation and test seeds, and the opponents, with 3E's winner as the tuned rule once it moves into `b_env.py`. The 5 round-2 DRL candidates have trained and passed their checks (V450).
