## Angle: the search procedure (a fair, cheap screening funnel)

### Findings (measured, with file and number)

Scripts: `/home/catalin/work/phd/v5b1_runs/sar3c/tmp/{rank,noise,noise2,trainlog}.py`. "Fewer/less" means DRL is better. ρ is Spearman rank correlation over the 5 learners.

1. **Training reward cannot rank or stop runs** (`conf3/train/C*_updates.jsonl`). The reward is already at its final level by updates 91-110 (median of 5 learners -0.173; at 481-500 it is -0.187). Learner ranks by 20-update windows are unstable: ρ against 481-500 runs from -0.3 to 1.0. The final-window reward ranks learners against their 40-seed X2 evaluation at ρ = -0.7 for both TTC and delay. For example, d3 has the lowest reward and the fewest close-following seconds.
2. **Policies still move between update 250 and 500** (`rows/conf3_u250.jsonl.gz`, tuning seeds 7,440,160-164). The final checkpoint has fewer TTC seconds than u250 in 10 of 10 learner-cells, but u250 had less delay in 7 of 10. So the trade-off point keeps sliding toward TTC. Learner rank at u250 against the final: ρ -0.2 (X1) and 0.8 (X2) on TTC, 0.5 and -0.4 on delay.
3. **That u250 test is too small to settle the question.** Final policies ranked on those same 5 seeds against the 20 evaluation seeds give ρ 0.6/0.7 on TTC and -0.3/0.6 on delay. So 5 seeds cannot separate "early checkpoints mislead" from seed noise. Whether u100/u250 predicts u500 is **not yet known**.
4. **Seed noise.** X2 at 5,300, pooling 40 seeds from `conf3_eval_primary` and `conf3b_eval_x2`. Measure: 97.5 % bootstrap half-width of the protocol statistic against os1_15_10.

| Seeds | TTC (points) | Delay (points) |
|---|---|---|
| 5 | 15-26 | 10-14 |
| 20 | 8-14 | 5-8 |
| 40 | 5-10 | 3-6 |

DRL arm against DRL arm (paired), delay: 5.5-6.5 points at 20 seeds, 3.3-5.2 at 40. Between the two 20-seed blocks, the delay point estimates moved by 4-13 points: 0.8-7.5 % less on the original seeds, 1.6-10.2 % more on fresh ones.
5. **The incumbent as one arm** (5-learner mean per seed, 40 seeds), against os1_15_10: TTC 21.9 % fewer (±5.3), delay 0.7 % more (±4.1). **Delay is the side of the bar that binds, and the 2 % limit sits inside the noise.**
6. **Learner (training-seed) spread at 40 seeds** is of the same order as the evaluation noise: TTC 15-25 % fewer, delay from 2.5 % less to 3.5 % more.
7. **A floor that keeps the incumbent:** at u250, all 10 learner-cells already had 22-44 % fewer TTC seconds than p333 (5 seeds, `conf3_tune` rows).
8. **Cost.**
   - Training: 5 learners ran **in parallel** in 3.3 h wall (chain log 11:52-15:10; 15 envs; CPU 38 %).
   - Evaluation: about 1,500 runs per hour on 32 workers (sweep: 1,728 runs in 66 min; conf3b: 360 runs in 16 min).
   - Checkpoints (`c_train.py:291`) hold weights and scale only. A resume (`:268`) restarts Adam and the seed stream, so pause-and-resume is not exact.

**Inference (mine):**
- A whole candidate with 5 learners costs one 3.3-h slot, so early stopping saves at most about 1.6 h per candidate.
- The real cost is evaluation noise. The funnel should spend on validation seeds and common training seeds, not on halving.

### Options

**A. Stage 0: calibrate the funnel on the existing checkpoints (no training)**
- *Problem:* findings 2-3. We do not know whether early checkpoints rank learners, or whether picking a checkpoint on validation moves delay (the checkpoint-selection part overlaps path 2).
- *Change:* none to the SAR or the algorithm. Evaluate C0-C4 at u50…u500 (10 checkpoints each) in X1 and X2 at 5,300 on 20 validation seeds. Run os1_15_10, p333 and no control on the same seeds. The evaluation path is the d2b2ecc `eval_runs.py`/`decide3.read_cell`, given checkpoint paths.
- *Cost:* about 2,100 runs, about 1.4 h of compute. A small build.
- *Risk:* rank among learners of one algorithm may not carry over to rank across algorithms. It uses 20 seeds of the approved block.
- *Test and KILL:* compute ρ of the bar score (delay against os1_15_10, provided TTC is at least 10 % fewer) at u100, u150 and u250 against u500, in each cell. If the u500-best learner is not in the u250 top 2, or ρ is below 0.8 in either cell, early rungs (option B) are KILLed for this project. Report-only: whether a validation-chosen checkpoint clears the bar where the final does not.

**B. Successive halving across candidates (rungs at 125, 250 and 500 updates; keep the better half on 20 validation seeds)**
- *Problem:* training compute when there are many candidates (more than 4).
- *Change:* none to the SAR. Algorithm side: an exact resume (save the Adam state, RNG and seed pointer at `c_train.py:291`). Evaluate at each rung with training stopped (V392).
- *Cost:* about 40 % less training than option C for 8 candidates, plus 3 stop-the-world evaluations of about 0.3 h each, plus the resume build.
- *Risk:* the trade-off still moves after u250 (finding 2), so rungs favour fast starters that later slide; 20-seed ranks are noisy; a resume bug would confound results.
- *Test:* only if A passes; Stage 2 as in option C.

**C. Fixed-budget bake-off, common training seeds, checkpoint selection on validation (recommended after A)**
- *Problem:* findings 1, 4, 5 and 6. Noise and learner spread, not compute, decide the outcome.
- *Change:* the procedure only. Each candidate SAR or algorithm (at most 4 per round, picked from paths 1-3) trains **5 learners × 500 updates in one slot**. All candidates use **the same 5 training seed streams** (common random numbers, so the comparisons are paired). The only KILL during training is the existing collapse check.
- *Stage 1, validation:* 40 validation seeds; X1 and X2 at 5,300. Arms:
  - each candidate at u250 and u500;
  - the incumbent d0-d4 final;
  - os1_15_10, p333 and no control.

  Screening score: the 5-learner arm's paired delay against the incumbent arm, read only if its TTC against os1_15_10 is at least 10 % fewer. A candidate advances if its delay is less than the incumbent's with a 95 % CI excluding 0. At most 2 advance.

  The floor KILL: the u500 arm has fewer than 10 % fewer TTC seconds than p333, or more delay than no control.
- *Stage 2, test (fresh seeds, used once):* the finalists' 5 learners, each at the checkpoint chosen on validation, on 40 test seeds in X1 and X2. Read with the confirmatory 3 tuned reading (4 of 5 policies; protocol statistic). Bonferroni over finalists × cells: 2 × 2 gives 98.75 % CIs. The incumbent is re-read on the same seeds, report-only.
- *Cost, 4 candidates:*
  - training 4 × 3.3 = 13.2 h;
  - validation about 3,800 runs ≈ 2.6 h;
  - test about 1,450 runs ≈ 1 h;
  - total about 17 h, run serially, roughly one day of wall time.
- *Risk:*
  - with a 2 % delay limit, even 40 test seeds (±3-6) can fail a true tie;
  - common seeds make a seed-specific quirk shared;
  - 4 candidates is a cap, not a search of the space.
- *KILL for the round:* no candidate beats the incumbent on delay with the CI excluding 0 on validation. Path 3 then stops for this round and baseline-v3 stays.

**D. Wide screen, 1 learner per candidate (5 candidates per 3.3-h slot).** Listed only to reject it: learner spread (finding 6) is as large as the effects sought.

### Recommendation

**A, then C.** A costs 1.4 h and no training. It answers, at 20 seeds instead of 5, the one question that decides whether rungs are worth building. It also shows whether checkpoint choice alone moves delay. C is then a fair, paired, 17-h round with the selection on validation seeds and one fresh test.

*Pros:* every element answers a measured problem; selection needs no multiplicity correction, Bonferroni only at the test; the incumbent needs no retraining.

*Cons:* 40 + 40 new seeds; about one day of wall time per round; at most 4 candidates per round.

*Inferior alternatives:*
- **B as the main path:** findings 2-3 do not support rank preservation, and it needs an exact resume. It is worth building only if A passes and more than 4 candidates are queued.
- **D:** see finding 6.
- **Screening on the training reward:** finding 1 (ρ = -0.7 against the evaluation), and the reward changes with each SAR anyway.
- **20 test seeds as in confirmatory 3:** finding 4 (±5-8 points on delay against a 2 % limit). This is what V399 priced at about 27-30 % "won".

Packing more than 5 learners per slot might halve training time (CPU 38 %), but V392 showed contention. It needs a 10-minute timing check before anyone relies on it.

### Open questions for the author (at most 3)

1. Seeds: approve validation 7,440,300-339, test 7,440,400-439 and training 7,464,000-7,479,999, one shared list for all candidates? My grep of `docs/decisions.md` finds no use of these ranges. They need your approval and a check of the run folders.
2. The bar: the 2 % delay limit lies inside 40-seed noise (±3-6 points). Keep it, with 40 test seeds, or restate it before Stage 2? This overlaps path 1.
3. The cap per round: 4 candidates (about 17 h), or fewer?
