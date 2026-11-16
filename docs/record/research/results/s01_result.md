# S0/S1 measurement: interpretation

Report-only (V470, V475). Everything here is descriptive: no claim, no pass/fail.
Data: `/home/catalin/work/phd/v5b1_runs/measure_s01_remote/`. Code: worktree `r2-metrics` (run commit 79b889b).
Analysis scripts and small outputs: `docs/research/s01/analysis/` (written `s01/` below); the full set, with the large intermediate files, is in `/home/catalin/work/phd/v5b1_runs/s01_analysis/`.

**What this rests on.**
- Six analyses ran: the five planned ones (integrity, x1_exposure, x1_braking, decisions, operating_map) and the all-rules map you asked for (map_all, 790 CIs: v3w, tail and sw against every non-learning controller).
- An independent adversarial verifier checked each of the six. This draft uses only what the verifiers confirmed, or their corrected numbers.
- A critic then checked the first draft against the data. It raised 25 issues and reproduced 26 of the draft's numbers with its own code. A second check read revision 2 against the data (182 numbers, none wrong). It found 4 critic issues only partly applied (2, 5, 6, 11) and 12 new points. Revision 3 applies each of them. A third check read revision 3 (300 numbers; 2 wrong, 6 minor wording points); all 8 are fixed in this version.
- I ran two checks of my own, read-only on the stored rows. For this revision I re-ran the whole oracle table of §7(c) with a new script (8 intervals, the 3E-T row included); it reproduces the critic's gate intervals exactly. The second check gives the X1 past-limit braking medians of every arm in §4.2. Scripts and outputs: `s01/revise/` (`oracle_r3.py`, `oracle_r3.out`, `pastlimit_check.py`).

**How to read the brackets.**
- `[key:F3]`: an analyst finding the verifier confirmed. `[key:F3*]`: a finding the verifier corrected; the text uses the corrected numbers or wording.
- `[key:vmN]`: item N in that verifier's "missed" list. `[key:verdict]`: the verifier's overall verdict.
- `[map_all:fix-a]` to `[map_all:fix-d]`: the map_all verifier's four required wording fixes. `[map_all:gap]`, `[map_all:caveats]`: the analysis's coverage-gap and caveat sections. `[map_all:verify]`: its verifier's check of the tables.
- `[critic:file]`: a figure from the critic's own scripts (`s01/critic/`). `[own check]`: recomputed for revision 3 (`s01/revise/`). `[check_r2]`: computed by the third check (`s01/check_r2/`).
- `[r2 l.N]`: `docs/research/results/round_2_result.md`, line N. `[r1 l.N]`: `docs/research/protocols/round_1.md`. `[Vnnn]`: `docs/decisions.md`.
- `[code:wt file l.N]`: a line of `v5b/fleet/file` in worktree `wt` under `/home/catalin/work/phd/wt/` (r2-metrics is the run commit 79b889b), read for this revision. A code reading shows what the code does, not that a run used it.
- "(my inference)" marks a link this draft draws between verified facts that nobody checked on its own.
- **†** marks a result from the band (4,500-6,000 veh/h) or from S1 (3,500 and 7,000 veh/h). Both run under condition T, the random training slowdown draw. Per V462(4) these rows are outside the plant's stated intended use [r2 l.396]. They are reported, and they count as evidence for no claim. Integrity counts in §2 (rows, seeds, collisions) are not results and carry no †.

**Statistic (round 2's).** Seeds are paired. An arm's value per seed is the mean over its learners. Effect = median(P − O) / median(O) × 100, with a 95 % percentile bootstrap (20,000 resamples of seeds, `default_rng(20261104)`). I write effects in plain words, e.g. "16.6 % more close-following than no control [8.4, 25.1]". In the §6 tables the sign is fixed instead: positive = v3w better. "Shown" means the 95 % CI excludes 0. "Not shown to differ" means the CI includes 0. That is not the same as "equal".

**Field names.** Close-following = `ttc_net` (vehicle-seconds with TTC < 3 s); delay = `all_delay`; served flow = `passed`; braking seconds = `b3_step`, `b45_step` (b3, b45); braking events = the pack's `m_peak_*` histograms (`events_ge45_*` in the summaries).

**Arms.** v3w = w0u250, w1u500, w2u250, w3u500, w4u500; tail = t0-t4; sw = s0u500-s4u500; baseline-v3 = d0u500-d4u500 [integrity:F9]. nc = no control; 3E-T = `3e`. Each test cell has 14 rules (15 distinct over both cells: 3E-X1 runs only in X1, 3E-X2 only in X2); they are listed in `s01/map_all/tables.md`.

---

## 1. Outcome

### 1.1 Your six questions

**(i) Why is X1 close-following worse than no control, and how can it improve without losing delay or X2?** (§3, §7a)
- v3w has 16.6 % more close-following than no control [8.4, 25.1], at 27.3 % less delay. Every rule has more (43-122 % [r2 l.19]): 3E-T 47.5 % [41.7, 59.0], os1_15_10 74.1 % [60.8, 94.2], p333 121.5 % [106.9, 143.2] [x1_exposure:F1, decisions:D7*].
- Stopped-queue exposure does not explain it. Per vehicle-km, per vehicle-second and per vehicle served, v3w still has more [x1_exposure:F3].
- The excess sits on merge 2's acceleration section 4a (+272 per run) and on edge 3 (+139), from the first slowdown on. Ramp 2 (−113) and the other roads (−73) offset part of it [x1_exposure:F2, decisions:D8*].
- On edge 3 it is a rate increase. On 4a the cause is open: traffic reaching the queue tail at speed, ramp-2 vehicles stopping at the lane end, or shorter gaps. The mechanism is not identified [x1_exposure:verdict].
- The X1 rise needs control. No control's X1 count is not shown to differ from its X2 count, while every controlled arm examined (v3w, tail, sw, baseline-v3, p333, os1_15_10, 3E-T) has 13-29 % more in X1 [decisions:vm6, decisions:D7*]. Across all 17 controlled arms present in both cells the rise is 9-32 %, every CI excluding 0 [check_r2].
- In X2 v3w's close-following is not shown to differ from no control's (−0.9 [−5.8, +9.5], positive = v3w fewer) [map_all:F2]. The reason is an offset: v3w removes no control's merge-1 queue (−288 per run), which cancels what it adds elsewhere (+217) [x1_exposure:F8*]. A change that weakens that removal could lose X2 (my inference).
- How to improve: trace four X1 seeds first (12 runs), then pick a term for the reading the trace supports. Guards fixed in advance: X1 delay within 2 % of v3w; X2 close-following and merge-1 close-following not worse than v3w's, read report-only under V466. Round 2 already trained five changes; under its advance rule none was shown better than v3w (§7a). Any S2 aimed at X1 on this plant needs your explicit decision, with X1's test history disclosed (§7).

**(ii) Were X1 and X2 trained together or separately?** Neither was a training condition (§2.1).
- v3w's 5 learners were trained once, at 7 demand levels from 4,500 to 6,000 veh/h, with at most one random slowdown per episode [V422; r1 l.20-22; integrity:F7*].
- X2 lies inside that draw (edge 3, 30 km/h, start 700 s). Its 180-s duration equals the draw's upper bound. X1's 25 km/h equals the draw's lower bound, and its second event lies outside the draw [integrity:F7*].
- Round 2's candidate rep added X1's two-event structure to training (29 % of episodes got two events) [V446]. It was not shown better than v3w at validation: X1 close-following +0.2 [−3.1, +4.2], X1 delay −0.4 [−1.6, +1.0] (positive = rep better) [r2 l.115, l.450].
- Only rules were tuned per cell, never the policies. 3E-X1 (for X1) and 3E-X2 (for X2) were tuned separately by CMA-ES on separate seeds, and neither search had converged at generation 40 [r2 l.9, l.12, l.100]. Confirmatory 3's grid forms were also tuned per cell [r2 l.449]. 3E-T was tuned under the training draw, not for either cell [r2 l.8].

**(iii) Is p333, or any non-learning controller, the winner anywhere?** (§6)
- On delay, no. No rule is shown better than v3w in any of the 9 cells or levels: 0 of 58 delay CIs. Not shown to differ: p333 and os1_15_10 at 3,500-6,000†, os0_10_10 in X2, 3E-T at 7,000† [map_all:F5].
- On close-following, only no control is shown better than v3w: in X1, at 3,500† and at 7,000†. No rule is shown better on delay and close-following together [map_all:F5].
- On hard braking, no control and two rules do lead. On b45: no control in X1, 3,500†, 4,500†, 6,000† and 7,000†; 3E-T in X1, X2, 6,000† and 7,000†; copy in X1. On b3: no control in X1, X2, 6,000† and 7,000†; 3E-T at 3,500†. On flow, os1_15_10 leads at 5,000† by a marginal 0.2 % [map_all:F1-F4, map_all:fix-a].
- Coverage gap: the band and S1 hold only no control, p333, os1_15_10 and 3E-T. The 12 other rules, including X1's and X2's best rules on delay, ran only in X1 and X2. So outside X1 and X2 "no rule beats v3w" covers only those four [map_all:gap].
- The likely source of the impression "p333 wins everywhere" is unpaired median delay: p333 has the lowest median of all arms at 3,500-5,250†. Paired, none of these leads is shown [operating_map:vm1].

**(iv) A wider training demand range, and the risk that the policy ignores regimes and wrecks itself?** (§7b)
- S1 measures how the current policy extrapolates, not what training there would do.
  - At 3,500†, v3w is not shown to differ from p333 on delay (−0.2 [−0.9, +0.1]) [operating_map:F2*].
  - At 7,000†, it is shown better than p333 and os1_15_10 on delay and not shown to differ from 3E-T. It has 29.7 % more b45 than 3E-T [23.7, 32.6] [operating_map:F2*, operating_map:F9, operating_map:F4].
- 3,500 and 7,000 are outside the plant's stated intended use (V462(4)). Training there would take the policy beyond it.
- How training there could go wrong is not tested. The candidate PPO mechanisms are hypotheses only: per-minibatch advantage normalisation in updates that hold only light traffic; the per-level no-control reference in the reward's shared term; reward scale at 7,000; interference between regimes in the shared network (§7b).
- Recommendation: keep 3,500 and 7,000 as fixed regression checks, not training levels (§7b).

**(v) Switching tail/sw-like tweaks on by condition?** (§7c)
- An oracle picks, per seed and with hindsight, whichever of v3w, tail and sw had the least close-following. On the test rows it is an in-sample upper bound, not a measured ceiling, and it depends on how the gate is defined [critic:oracle.out; own check, `revise/oracle_r3.py`]:
  - arm-level gate (per seed, the lowest of the three arm means): 9.6 % more close-following than no control in X1 [0.6, 19.3];
  - per-learner gate (per seed and learner index i, the lowest of w_i, t_i and s_i, then the mean over i): 0.9 % more [−5.9, +11.5], not shown to differ from no control.
  - For comparison, v3w alone has 16.6 % more [8.4, 25.1] and 3E-T 47.5 % more [41.7, 59.0].
- So this data does not rule switching out for X1 close-following. But a real gate needs a condition signal that the policy does not have [decisions:vm1], and part of the per-learner gate's gain is picking the luckiest of three runs per seed (my inference).
- Recommendation: no switch now. First an out-of-sample check from stored rows, with no new runs (§7c).

**(vi) Plan B: perturbation resilience against tuned rules?** (§6, §7d)
- In X1, v3w is shown better than all 14 rules on delay (+5.0 to +11.6 %), close-following (+18.8 to +44.7 %) and flow. In X2 it is shown better than 13 of 14 on delay (not shown to differ from os0_10_10) and than all 14 on close-following [map_all:F1, map_all:F2].
- Against it: rules lead on b45 (3E-T and copy in X1, 3E-T in X2), and no control leads on b45 in X1 and on b3 in X1 and X2 [map_all:F1, map_all:F2]. The per-cell rules are lower bounds [r2 l.100]. X1 close-following stays above no control's [x1_exposure:F1].
- Recorded closures: the DRL claim against tuned rules is closed in X2 on this plant (V466). X1 closed under [A3] (V395), and round 2 was its third test [r2 l.10, l.14]. Plan B on these cells needs your explicit decision, with this disclosed (§7d).

### 1.2 Other findings

- **The pack did not change the runs.** All 5,200 S0 rows equal round 2's rows on every shared field (761,642 field comparisons, 0 differences). They were produced on a different CPU (EPYC 7702, against round 2's EPYC 7B13). S1 is complete, uses fresh seeds and is healthy [integrity:F1, integrity:vm1, integrity:F4*, integrity:F5*].
- **Hard braking.** No braking behaviour specific to v3w is shown. The −4.5 m/s² count sits exactly on the normal braking limit, so what it counts depends on speed [x1_braking:F3*]. On the robust counts:
  - braking at −4.0 or harder, all classes: 7.9 % more than no control raw [5.3, 11.4], but only 1.7 % [0.5, 6.5] per vehicle served; cars plus ALKS: 7.2 % more raw [4.8, 11.5]. Against 3E-T: 3.3 % more [1.4, 5.9] [x1_braking:F5*, x1_braking:vm2];
  - braking past the limit is ALKS-only and about 5x no control's under every controller that shortens ALKS gaps. v3w is at the low end in X1: fewer than 3E-T (5.2 fewer [1.6, 8.1]) and p333 (29.2 fewer [26.4, 32.3]); copy has fewer by median [x1_braking:F6*].
- **Decisions.** Whole-run aggregates show no lower confidence and no more reversals in X1. Its gap choice does change: longer in X1, also within each road [decisions:D4*, decisions:D6]. The policy sees only local, current inputs, so this test had little power [decisions:vm1]. p333's 0.934 is correct. The panel title is inverted: level index 3 is 0.8 s, the *shortest* gap. The missing 6.6 % is the climb from 1.6 s after each ALKS enters [decisions:D1, decisions:D2, integrity:F11*].
- **Corrections to the first look:**
  - v3w is not the smoothest of all controllers. tail and sw have slightly less jam and oscillation, and tail and p333 a slightly shorter maximum congested length (1.645 and 1.65 km against 1.67). The oscillation differences are tiny (8.80, 8.88, 8.89 km/h). All of these are untested medians [integrity:vm7];
  - the "1,044 vs 818" braking count is speed-selective [x1_braking:F3*];
  - at 7,000†, "4.5 % less delay than 3E-T" is not shown [−0.7, +6.2] [operating_map:F9].
- **For S2.** The diagnosis does not yet point to one training change. The cheapest next step is a traced re-run of four X1 seeds to settle the 4a mechanism (§7a).

---

## 2. Integrity

| Check | Result | Source |
|---|---|---|
| S0 rows vs round-2 rows | 5,200 of 5,200 equal on 159 shared fields; 761,642 comparisons; 0 differences | [integrity:F1] |
| Machines | round 2: instance 59653253 (EPYC 7B13); S0: instance 59681619 (EPYC 7702) | [integrity:vm1] |
| Code change from round 2 to S0 | only `measure.py` (+435, new) and the hooks in `plant_sweep.py` (+20/−2) | [integrity:F2*] |
| Pack self-consistency | 0 failures over all 5,560 runs; summaries recompute exactly; report panels regenerate | [integrity:F3] |
| S1 grid | 360 = 9 arms × 2 levels × 20 seeds (7,440,900-919); the seeds occur nowhere else; configs equal the band's | [integrity:F4*] |
| S1 safety | collisions 0, contact steps 0 | [integrity:F5*] |
| S0 collisions (report-only) | 5 runs with one each: X1 s2u500, X2 w3u500, X1 d0u500, X2 lr400_13_2, band 5,000 t0 | [map_all:F9] |
| Teleports | 0, but the counter cannot fire (SUMO runs with `--time-to-teleport -1`) | [integrity:vm2] |
| Pairing | in every cell, level and seed, all arms see the same slowdown; the draw rebuilt from the seed matches the log within 0.6 s | [integrity:F7*] |
| Re-runs | same-host re-runs are identical; laptop and remote differ only in `m_dec_entropy_mean`, at 1e-9 to 3e-8 relative | [integrity:F13] |
| Summary files | no NaN or inf; None only in metrics that are optional by design; no report panel dropped a seed | [integrity:F12] |

Points that matter when reading the rest:

- **S1 neutrality is inferred, not shown.** No S1 run without the pack exists. The evidence is indirect: the same code path is exact in S0, and re-runs are deterministic [integrity:vm5].
- **finished_pct has a built-in floor.** The 6,778-m mainline takes 244.8 s at 100 km/h, which is 16.3 % of the 1,500-s window. So about 84 % of vehicles can finish even in free flow; the floor is approximate, since ramp routes are shorter and speeds vary. At 3,500†, 83.7-86.1 % do. At 7,000†, the 54-70 % comes from congestion plus the insertion backlog (2,204-2,384 vehicles served of 2,917 demanded). `all_delay` counts those queued and unfinished vehicles [integrity:F5*, integrity:vm3].
- **p333 and os1_15_10 are the same runs at low demand.** That follows from how the rules are defined. They are identical on 20/20 S1 seeds at 3,500† and on 17, 10, 6, 1 and 0 of 20 band seeds at 4,500†, 5,000†, 5,250†, 5,500† and 6,000†. At 3,500, S1 has 8 distinct arms, not 9 [integrity:F8].
- **The statistic.** `conf3/common.raw` defaults to a 97.5 % interval (pct 1.25, 98.75). Every analysis passed (2.5, 97.5). The denominator median(O) is held fixed, so the CI ignores its uncertainty [integrity:F14].
- **The CI's own null.** Under a sign-flip null, the 95 % CI excludes 0 in about 6 % of comparisons at n = 20 and about 5 % at n = 40. A single borderline exclusion should not be read on its own [operating_map:F10].
- **Missing values carry information in some metrics.** If anyone later reads the m1/m2 breakdown and recovery metrics: they are None in a large, arm-dependent share of runs (`m2.recovery_min` in about 70 % of test runs) [integrity:F12].

### 2.1 Training conditions: were X1 and X2 trained together?

No. Neither cell was a training condition, and v3w was trained once.

- **v3w's training.** 5 learners × 3 environments, 500 updates. The environments cycle through the 7 levels 4,500, 4,750, …, 6,000 veh/h; each update covers 3 consecutive levels. Slowdowns come from the random draw, and the reward references come from no control at each training level (stage 0c) [r1 l.20-22, V422, V429].
- **The draw against the cells** [integrity:F7*]:

| Feature | Training draw | X2 | X1 |
|---|---|---|---|
| Events | at most one (5-6 of 20 seeds have none in the band† and S1†) | one | two, 600 s apart |
| Edge | 3, 4 or 5 | 3 (inside) | 4 (inside) |
| Speed limit | uniform 25-60 km/h | 30 km/h (inside) | 25 km/h (the lower bound) |
| Duration | uniform 60-180 s | 180 s (the upper bound) | 120 s each (inside) |
| Start | 400-1,200 s | 700 s (inside) | 600 s (inside) and 1,200 s (the upper bound) |
| Demand | 7 levels, 4,500-6,000 veh/h in steps of 250 | 5,300 (inside the range, not one of the levels) | 5,300 (same) |

- **What lies outside the draw is X1's second event.** Round 2's candidate rep trained on that structure: a second event 300-800 s after the first, in 29 % of episodes [V446]. At validation it was not shown better than v3w in either cell (X1 close-following +0.2 [−3.1, +4.2]; X1 delay −0.4 [−1.6, +1.0]; positive = rep better) [r2 l.115, l.450].
- **Per-cell tuning exists only for rules.** 3E-X1 and 3E-X2 were tuned separately, each for its own cell, by CMA-ES on separate seeds. Both searches were still falling at generation 40, so each is a lower bound on its family. 3E-X1 also failed round 2's delay filter [r2 l.9, l.12, l.100]. Confirmatory 3's grid forms (os0_10_10 and the others) were tuned per cell too [r2 l.449].
- **3E-T** was tuned under the training draw at 4,500-6,000 veh/h, not for either cell. Its search ran 40 of 100 generations, with convergence unchecked [r2 l.8, l.253].

---

## 3. X1 close-following: what drives v3w's excess

### 3.1 What `ttc_net` counts

At each 1-s sample after the 300-s warm-up, `ttc_net` counts vehicles with a same-lane leader within 200 m, a positive closing speed, and gap/closing speed < 3 s. It covers the whole network, all classes (humans included), ramps and junction lanes. A stopped follower cannot count; a creeping one can. `ttc_net = E30 + out_E30`, where E30 is the merge-1 area [x1_exposure:F0].

### 3.2 Where and when

```
flow ->
                   merge 1                         merge 2
 edges 1, 2 ----- [ 3a ] ------- edge 3 ------- [ 4a ] ------- edge 4 ------- 5 --->
                    ^           3,793-4,987 m  4,987-5,282 m  5,282-6,278 m
                 ramp 1                           ^
               (E30 area)                       ramp 2
                           X2 slowdown                         X1 slowdowns (two)
                           30 km/h, 180 s                      25 km/h, 120 s each
```
Positions from [x1_braking:F2*]; cells from [integrity:F7*].

| Road, X1 | v3w − nc (mean per run) | v3w − 3E-T (median paired, round 2) |
|---|---|---|
| 4a | +272.3 [229.4, 311.6] | −80 [−149, −40] |
| edge 3 | +138.5 [88.1, 189.4] | −253 [−273, −206] |
| ramp 2 | −113.3 [−171.5, −55.9] | −107 [−172, −77] |
| other roads | −73.1 [−149.8, −11.4] | not given |
| total | +224.3 [118.6, 328.4] | −457 [−516, −354] |

Sources: [x1_exposure:F2]; [r2 l.255-256], round 2's test rows, which S0 reproduces exactly. Round 2's medians do not add up.

- **Roads.** The excess over no control sits on 4a and edge 3. Ramp 2 and the remaining roads partly offset it. v3w has fewer close-following seconds than 3E-T on every road listed, most on edge 3. p333 adds +1,873 [1,726, 2,023] over no control on edges 3 and 4a together [x1_exposure:F2].
- **Speed bands.** The excess over no control is spread over all three: below 5 m/s +73.1 [27.4, 116.7], 5-10 m/s +55.9 [18.6, 92.8], at 10 m/s or faster +95.4 [68.3, 122.5] [x1_exposure:F2]. Against 3E-T, v3w has fewer in every band: −48 [−105, −13] below 5 m/s, −196 [−234, −163] at 5-10 m/s, −205 [−218, −177] at 10 m/s or faster (round 2's median statistic) [r2 l.257].
- **Time.**

| Period, X1 | v3w against no control | v3w − 3E-T (median paired, round 2) |
|---|---|---|
| before the first slowdown (< 600 s) | +3 [−4, +15] per run, no excess shown | not given |
| during the slowdowns ("hold") | 20.0 % more [−4.8, 25.4], not shown | −104 [−128, −62] |
| the 120 s after each slowdown | 18.1 % more [9.6, 25.3] | −141 [−162, −123] |
| the rest of the run (840-1,200 s and 1,440-1,800 s) | 23.4 % more [11.4, 31.1] | −158 [−222, −93] |

Sources: [decisions:D8*] (before), [decisions:vm4] (the three later periods); [r2 l.258], round 2's test rows, which S0 reproduces exactly.

  - From the first slowdown on, the excess over no control has a similar size relative to no control's count. Per second that is +0.20, +0.25 and +0.27 close-following seconds. The hold CI includes 0 because that window is only 200 s long [decisions:vm4].
  - In every period after the first slowdown, v3w has fewer close-following seconds than 3E-T [r2 l.258]. p333's time split is not verified.
- tail, sw and baseline-v3 show a similar road pattern (4a +254 to +304, edge 3 +128 to +210) [x1_exposure:F2]. Every v3w learner shows the excess by point estimate, but w3u500's CI reaches 0 [x1_exposure:F9].

### 3.3 Exposure

The hypothesis under test: no control's stopped queues hide its close-following (a stopped follower cannot count), and v3w turns them into moving dense traffic.

| `ttc_net` in X1, more than no control | v3w | 3E-T | p333 | Source |
|---|---|---|---|---|
| per run (raw) | 16.6 % [8.4, 25.1] | 47.5 % [41.7, 59.0] | 121.5 % [106.9, 143.2] | [x1_exposure:F1, decisions:D7*] |
| per vehicle-km | 13.8 % [3.9, 22.3] | 44.2 % | 113.7 % | [x1_exposure:F3, x1_exposure:F9] |
| per vehicle-second | 30.0 % [22.3, 34.9] | not verified | not verified | [x1_exposure:F3] |
| per moving vehicle-second (≥ 5 km/h) | 26.2 % [18.5, 32.9] | not verified | not verified | [x1_exposure:F3] |
| per vehicle served | 9.9 % [0.6, 20.2] | not verified | not verified | [x1_exposure:F3] |
| excluding ramp 2, per approach vehicle-second (post-hoc proxy) | 37.6 % [17.3, 43.8]; network approach exposure itself +2.2 % [−1.0, 6.4] | not verified | not verified | [x1_exposure:vm2; verify_x1_exposure/v3_st_stats.txt l.12] |

The last row leaves out ramp 2, where v3w has 113 fewer seconds, so it is inflated. Its proxy was defined after the data were seen. The verifier's verdict text calls it "TTC per app20", which is a mislabel.

At network level, v3w's close-following per unit of exposure is higher under every normalisation tried. A rate/exposure split over the three speed bands shows two opposing parts [x1_exposure:F4*, x1_exposure:F9]:

| X1, close-following seconds per run, against no control | v3w | 3E-T | p333 |
|---|---|---|---|
| exposure part (less time in slow states) | −648 [−704, −594] | −501 | −757 |
| rate part (more close-following per unit of time in each band) | +873 [778, 966] | +1,201 | +2,569 |
| total | +224 [119, 328] | +700 (sum) | +1,812 (sum) |

Every controller has the same structure. The analysis states that the policies' rate parts are the smallest of all controllers; its numbers give v3w +873 against 3E-T +1,201 and p333 +2,569 [x1_exposure:F9]. So, at network level, stopped-queue exposure does not explain the excess. By road it is less clear-cut. The road-level figures below exist only for v3w against no control; the rules' values are not verified:

- **Edge 3: a rate effect.**
  - Under no control, the slowdown queue spills back over the whole edge and lasts into "rest" (median 63,241 jam vehicle-seconds there). v3w removes most of it: −48,781 [−54,778, −43,128] [x1_exposure:F5*].
  - Even per moving vehicle-second, v3w's rate is about twice no control's (108 % more [67, 135]) [x1_exposure:F5*].
  - With approach exposure, too, it stays a rate effect: rate part +119.3 [93.3, 144.6], exposure part +19.2 [−14.0, 55.4] [x1_exposure:vm2].
- **4a, the largest part: open.**
  - v3w has 11.3 % less jam there [3.9, 18.8], not the same jam [x1_exposure:vm7].
  - Per moving vehicle-second, v3w's rate is 36.6 % higher [28.2, 44.3] [x1_exposure:F5*].
  - But approach exposure on 4a roughly doubles under v3w: +1,249 vehicle-seconds [966, 1,559] against no control's median of 1,256. Traffic now reaches the queue tail at speed from a free-flowing edge 3. Per unit of this exposure, v3w has 20.2 % *fewer* [8.6, 36.5], and the 4a split becomes rate −318.5 [−459.4, −188.6] plus exposure +590.8 [460.7, 728.4] [x1_exposure:vm2].
  - The approach proxy is not validated on 4a. Across no-control seeds, its Spearman with 4a close-following is −0.01 (against +0.59 on edge 3), and it was defined after the data were seen. So neither reading of 4a is established [x1_exposure:F4*, x1_exposure:vm2].
- **Two correlations that cannot be read as mechanism.**
  - "More jam goes with more close-following" across seeds cannot be told apart from "more traffic, more close-following": across no-control seeds, jam share and vehicle-seconds have rho 0.94 in X1 [x1_exposure:vm5].
  - Per-seed correlations of the paired differences sit at their shuffled-no-control null (observed 0.32, null median 0.60) [x1_exposure:F7].

### 3.4 Severity by road

Across the network, the count of severe closings `sev3` (required deceleration ≥ 3 m/s²) is not shown to change: 0.0 %, with a CI from 7.3 % fewer to 11.2 % more. That flat total comes from roads cancelling [x1_exposure:F6*, x1_exposure:vm1]:

| Road | v3w − nc, `sev3` per run | nc median | 3E-T, p333 |
|---|---|---|---|
| 4a | +12.7 [8.2, 17.2] (about +70 %) | 18 | not verified |
| edge 3 | +3.5 [2.8, 4.2] | 1 | not verified |
| ramp 2 | −11.0 [−19.4, −2.6] | | not verified |
| other roads | −3.3 [−7.3, −0.1] | | not verified |

tail, sw and baseline-v3 agree with v3w within about 2 per road [x1_exposure:vm1].

On 4a the relative excess is similar at the 3, 2 and 1.5 s thresholds (+40 %, +54 % and +44 % of no control's medians). Where the excess sits, severe closings rise. The analyst's first reading ("shorter gaps at small closing speeds, low required deceleration") is therefore not supported. Harder approaches to the queue tail, or lane-end stops on the acceleration lane, fit the counters at least as well [x1_exposure:F6*].

**A candidate for 4a: ramp-2 merge failure (not shown).** Across all 35 arms the link below holds by median; the paired figures are v3w against no control only. The verifier measured `end_stop2`, the vehicle-seconds stopped in the last 30 m of the acceleration lane 4a_0. Under v3w it rises by 461 [357, 558] over no control in X1 (no control's median 728) and by 229 [128, 329] in X2. Across 35 arms, the median of 4a close-following tracks the median of `end_stop2` (Spearman 0.85 in X1, 0.77 in X2). Per seed, the link is at its null. The stored counters cannot split close-following by lane [x1_exposure:vm3].

**Headway alone does not explain it.** Over all ALKS time (with V2V off counted at 1.6 s), the median mean gap in X1 is v3w 1.205 s and 3E-X1 1.249 s. Yet 3E-X1 has 58 % excess over no control, against v3w's 17 % [x1_exposure:F9, x1_exposure:vm6]. Section 5.3 gives the rule-only view.

### 3.5 Why X2 differs

| Close-following seconds per run | v3w − nc, merge-1 area (E30) | v3w − nc, rest of network (out_E30) | v3w − nc, total | nc E30 median | total, v3w against 3E-T |
|---|---|---|---|---|---|
| X1 | −83.3 [−144.7, −31.2] | +307.6 [206.7, 402.0] | +224.3 [118.6, 328.4] | 61 | 20.3 % fewer [15.7, 22.9] |
| X2 | −287.5 [−379.0, −201.9] | +216.8 [159.0, 276.2] | −70.7 [−174.1, 30.4], not shown | 456 | 11.5 % fewer [5.6, 16.2] |

Sources: [x1_exposure:F8*] for the no-control columns (means of paired differences); [map_all:F1, map_all:F2] for 3E-T (round 2's median statistic). The E30 split for the rules is not verified, so where 3E-T's gap sits (merge 1 or elsewhere) is not known.

- In both cells, v3w adds close-following outside merge 1. Inside the merge-1 area it removes some: in X2 no control's queue reaches merge 1, and v3w removes most of it [x1_exposure:F8*].
- The X1 minus X2 difference in v3w's excess is +295.1 [156.8, 433.7]. Of that, E30 accounts for +204.2 [112.0, 295.1] (69 %) and out_E30 for +90.9 [−5.6, 186.3] [x1_exposure:F8*].
- In X2 the per-exposure increase also exists, with a rate part of +401.2 [319.6, 483.9]. It sits mostly, though not only, below 18 km/h: below 5 m/s +344.6, 5-10 m/s +41.7 [1.1, 80.7] [x1_exposure:F8*].
- The X1-X2 comparison is paired correctly: the first 300 s of the space-time field are byte-identical between X1 and X2 in 40/40 seeds [x1_exposure:vm4].

The rise from X2 to X1, per arm [decisions:D7*, decisions:vm6]:

| Arm | Close-following, X1 against X2 |
|---|---|
| no control | 7.3 % fewer in X1 [−4.1, +20.6], not shown to differ |
| v3w | 17.0 % more [6.9, 21.2] |
| p333 | 23.0 % more [13.9, 34.1] |
| os1_15_10 | 22.7 % more [14.4, 26.9] |
| 3E-T | 28.9 % more [20.5, 35.7] |

Every controlled arm examined has 13-29 % more in X1; across all 17 controlled arms present in both cells the rise is 9-32 % (a4400_10_1 9.3 % [1.1, 19.3] to r4a1 32.1 % [17.7, 41.5]) [check_r2]. For no control, no rise is shown: its X1 count is not shown to differ from its X2 count. So the X1 rise needs control. The verifier reads it as an interaction of controlled short gaps with X1's traffic [decisions:vm6].

### 3.6 What we know and what we do not

| Statement | Confidence | Source |
|---|---|---|
| Stopped-queue exposure does not explain the excess at network level | high | [x1_exposure:F3, x1_exposure:F4*] |
| The edge-3 part is a rate increase | medium | [x1_exposure:F5*, x1_exposure:vm2] |
| The 4a part (the largest) is approach exposure, lane-end merge stops, or rate | open | [x1_exposure:vm2, x1_exposure:vm3] |
| Severe closings rise where the excess sits | medium | [x1_exposure:vm1] |
| In X2 v3w's close-following is not shown to differ from no control's, mainly because of an offset at merge 1 | medium | [x1_exposure:F8*, map_all:F2] |
| The X1 rise needs control (no rise shown for no control) | medium | [decisions:vm6] |

Side note, not investigated: under no control, `stop_gap` (stopped followers with a bumper gap below 2.5 m) is 0 in every run. Under every controller it is not: the v3w mean is 45.6 per run in X1, and p333's median is 1,014 [x1_exposure:F10].

---

## 4. X1 hard braking: who, where, when

### 4.1 What the −4.5 count measures

- A braking event starts at the first 0.1-s step with acceleration ≤ −3.0 m/s² and ends at the first step above it. Its peak is the minimum. `events_ge45` = events peaking at ≤ −4.5 [x1_braking:F2*].
- −4.5 m/s² is exactly SUMO's default normal braking limit for cars and ALKS (for trucks it is 4.0). Under no control in X1, cars spend 565 steps per run in [−5.0, −4.5) but only 2 in [−5.5, −5.0). Most steps just below −4.5 are braking *at* the limit [x1_braking:F3*].
- Whether a step at the limit is stored just above or just below −4.5 depends on speed, through floating-point arithmetic. It lands below at about 7-29 km/h and never at 58-115 km/h. So `events_ge45` counts every event past the limit, plus the limit events that happen to pass through about 7-29 km/h. It is a speed-selective count, not a measure of how much hard braking there is. This rests on arithmetic plus the shape of the histogram; it was not traced in a run [x1_braking:F3*].
- ALKS (SUMO ACC) can brake slightly beyond 4.5 m/s². The [−5.5, −5.0) bin holds 12 ALKS steps per run under no control, 86 under v3w, 128 under 3E-T and 264 under p333 [x1_braking:vm7].
- The first-look numbers reproduce exactly. Medians: v3w 1,044, nc 818.5, 3E-T 868.5 [x1_braking:F4].
- (my inference) `b45_step` and `alks_b45_step` use the same −4.5 threshold, at step level, so the same caveat applies to them and to every `b45_step` comparison in sections 6 and 7. Nobody checked this separately.

### 4.2 Robust and speed-selective counts

Robust counts (they avoid the −4.5 edge):

| Count | v3w vs nc, X1 | v3w vs nc, X2 | v3w vs 3E-T | v3w vs p333, X1 | Source |
|---|---|---|---|---|---|
| events peaking ≤ −4.0, cars + ALKS | +305 [202, 486]; 7.2 % more [4.8, 11.5] | not verified | X1: cars +39.8 [−29.6, 149], ALKS +83.9 [68.9, 113] | not verified | [x1_braking:F5*, x1_braking:F8*] |
| same, all classes (trucks sit on their own −4.0 limit) | +343 [230, 497]; 7.9 % more [5.3, 11.4] | +341 [134, 475]; 7.7 % more [3.0, 10.8] | X1 +155 [65, 278], 3.3 % more [1.4, 5.9]; X2 +328 [184, 438] | not verified | [x1_braking:F5*] |
| same, all classes, per vehicle served | 1.7 % more [0.5, 6.5] | 3.1 % more [−0.4, 5.9] | not verified | not verified | [x1_braking:vm2] |
| same, all classes, per vehicle-km | 4.9 % more [3.2, 8.9] | not verified | not verified | not verified | [x1_braking:F7*] |
| ALKS events past the limit (−5 to −9) | 48.4 vs 9 per run; +38 [37.4, 40.4] | 48.6 vs 9.5; +37.9 [36.7, 40] | X1 5.2 fewer [1.6, 8.1]; X2 7.3 fewer [0, 9.3], not shown (CI bound at 0) | 29.2 fewer [26.4, 32.3] | [x1_braking:F6*] |
| truck events peaking ≤ −3.5 | 19.7 % more [13.4, 31.6] | 26.7 % more | not verified | not verified | [x1_braking:vm3] |

Speed-selective counts (they inherit the −4.5 edge of §4.1):

| Count | v3w vs nc, X1 | v3w vs nc, X2 | v3w vs 3E-T | v3w vs p333, X1 | Source |
|---|---|---|---|---|---|
| events peaking ≤ −4.5 | +204 [149, 267] | +27 [−55, 62] | X1 +185 [112, 221]; X2 +98 [78, 179] | 356 fewer [315, 389] | [x1_braking:F4] |
| `b45_step`, all vehicles | 28.8 % more [17.8, 32.4] | not shown to differ | X1 16.1 % more [10.2, 21.3]; X2 8.5 % more [1.8, 13.5] | 28.4 % fewer [25.5, 31.2] | [map_all:F1, map_all:F2, operating_map:F4] |
| ALKS seconds at ≤ −4.5 | +69.8 s [51.1, 100.4] | not verified | not verified | not verified | [x1_braking:F8*] |
| non-ALKS seconds at ≤ −4.5 | +17.1 s [15.3, 22.8] | not verified | not verified | not verified | [x1_braking:F8*] |

Once exposure is counted, most of the robust excess over no control disappears: v3w serves 5.1 % more vehicles [x1_braking:vm2, x1_braking:F7*]. The "exposure explains little" reading holds only for the speed-selective −4.5 count (21.9 % more per km) [x1_braking:F7*].

Braking past the limit, X1 medians per run, every arm [x1_braking:F6*; critic:spot.out; own check]: no control 9; copy 46.0; v3w 48.4; lr400_16_1 49.5; sw 49.6; tail 50.8; 3E-T 51.5; baseline-v3 52.7; lr1000_16_2 54; lr400_13_2 54; a4400_10_1 55.5; 3E-X1 58.5; z33133 60; lr1000_10_1 64; r4a1 73; p333 77; os1_10_0 77.5; os0_10_10 78.5; os1_15_10 89.5.

It is about 5x no control's under every controller that shortens ALKS gaps. v3w is second lowest, 1.1-4.3 events below lr400_16_1, sw, tail, 3E-T and baseline-v3 (medians, untested). copy has fewer. In X2, copy (47.5) and tail (48.3) have slightly lower medians than v3w (48.6). Human cars barely brake past −5.0 in any arm (3.1 vs 2 events per run) [x1_braking:F6*].

**Why the gap shows in X1 only.** On the −4.5 count, most of the X1-specific gap comes from no control's count *falling* in X1 compared with X2: −141.5 [−260.5, −67]. Its −4.0 count is not shown to change (+48 [−152, 329]). v3w itself rises only a little: +49.4 [23.3, 88]. 3E-T is not shown to change (−26.5 [−113.5, 69.5]). This points to which side of −4.5 the limit steps land on, not to less braking. It remains an inference, because X2 is a different scenario, not a no-effect null [x1_braking:F9].

### 4.3 Who brakes

- Braking past the limit is ALKS-only [x1_braking:F6*].
- The class splits against no control below have a 3E-T counterpart only for the −4.0 count; the rest are not verified against the rules.
- By seconds at ≤ −4.5, the ALKS carry about 80 % of the excess over no control. That split rests on the speed-selective −4.5 threshold (§4.1) [x1_braking:vm4].
- Human-driven trucks brake more too, proportionally more than cars [x1_braking:vm3].
- Against 3E-T, on the −4.0 count: in X1 only the ALKS differ (cars +39.8 [−29.6, 149], ALKS +83.9 [68.9, 113]). In X2 the cars differ as well (+232.7 [85.6, 340.8]) [x1_braking:F8*].
- `free_brake_alks_step` (ALKS braking with no close leader) falls under v3w (−83.8 s [−96.0, −53.7] against no control). That is because v3w's ALKS more often have a close leader, so this counter tells us nothing about braking on a free road [x1_braking:vm1].
- Side note: ALKS steps also pile up just above −7.0 m/s² under every controller (medians of 30-34 steps per run in [−7.0, −6.5) against 1 for no control), so `b7_step` may sit on another such edge. The cause is unknown [x1_braking:F13].

### 4.4 Where and when (proxies only)

Braking events are stored without time or place [x1_braking:F2*]. Everything here rests on proxies, and confidence is low.

- **Speed fronts.** This proxy counts vehicles crossing 50-m steps that need ≥ 1.5 m/s² between cell means. Against no control it rises by 328 [286, 433] (+28 %) in X1, split evenly: edge 3 +176 [41, 303], 4a +190 [128, 289], edge 4 0. Against 3E-T it is not shown to differ (−6 [−95, 82]) [x1_braking:F10*, x1_braking:vm6].
- After about 780 s, edge 3 runs at 27-49 km/h under no control and at 48-73 km/h under v3w. 4a is congested (14-40 km/h) from about 660 s in all arms [x1_braking:F10*].
- Fronts do not explain the braking well:
  - among controllers, faster edge-3 traffic goes with *fewer* −4.5 events (partial rho −0.44 in X1, −0.54 in X2);
  - in X2, fronts rise 11.5 % [7.0, 17.1] with no change shown in −4.5 events;
  - against 3E-T, fronts are not shown to differ while the −4.5 count is higher.

  So "faster edge 3 meets the merge-2 queue" explains part of v3w vs nc at most, and not v3w vs other controllers [x1_braking:F10*, x1_braking:vm5, x1_braking:vm6].
- **Gaps and braking across arms.** Over 34 controlled arms, the commanded gap level on 4a goes with the −4.5 count (Spearman +0.66 in X1; +0.74 after controlling for edge-3 speed) [x1_braking:F11, x1_braking:vm5]. But braking past the limit does not follow the 4a level (rho 0.20). v3w also has fewer past-limit events than 3E-T (5.2 fewer [1.6, 8.1]), even though it commands shorter gaps on 4a (level 1.64 against 1.10). The commanded level acts only while V2V is on, about 57 % of ALKS time [x1_braking:F11, x1_braking:F6*, x1_braking:F2*].

### 4.5 Cascades

- The car cascade share is 0.227 for v3w against 0.203 for no control (+0.025 [0.007, 0.032]). For ALKS it is 0.294 against 0.244 (+0.047 [0.042, 0.054]) [x1_braking:F12].
- Against 3E-T, the car share is not shown to differ (+0.004 [−0.006, 0.012]), and v3w's ALKS share is lower (−0.007 [−0.011, −0.003]) [x1_braking:F12].
- Every controller raises the ALKS share (p333 0.359, os1_15_10 0.335) [x1_braking:F12].
- The only null available is a uniform-chance lower bound (0.032-0.043). A fixed 3-s window combined with shorter following gaps raises the share by construction. So do not read this as stronger wave propagation, or as something specific to v3w [x1_braking:F12].

### 4.6 Reading

No hard-braking behaviour specific to v3w is shown [x1_braking:verdict]:

- every DRL policy has a similar −4.5 count (medians, untested: tail 1,035, sw 1,042, baseline-v3 1,036, v3w 1,044), and p333 has the most (1,402) [integrity:vm7];
- braking at the limit rises a little against no control, mostly in line with the extra vehicles served, and 3.3 % against 3E-T;
- ALKS braking past the limit is the real difference from no control, and every gap-shortening controller shares it.

---

## 5. Policy decisions

### 5.1 What can be compared

Rules are asked about every ALKS at every 5-s decision; policies only when a vehicle's 10-s clock is due. So applied, kept and ignored shares cannot be compared between rules and policies. For example, p333's applied share of 0.053 against v3w's 0.318 reflects how often each is asked, not behaviour [decisions:D3].

### 5.2 Does v3w act differently in X1?

- **Whole-run aggregates show no lower confidence and no more reversals.** Paired X1 − X2 over 40 seeds [decisions:D4*]:
  - confidence (`conf_med`): +0.004 [−0.005, +0.012];
  - reversal share: +0.002 [−0.005, +0.005];
  - entropy: −0.013 [−0.019, −0.006], i.e. slightly *more* certain in X1;
  - more excess changes per ALKS, beyond the entry climb (+0.615 [0.288, 0.778]). The rules show a similar rise, not compared pairwise (os1_15_10 +0.549 [0.243, 0.950], 3E-T +0.740 [0.636, 0.825]), so it is not policy-specific.
- **This null was expected and has little power.** The policy reads 16 local, current-state features: no clock and no memory of events. The second slowdown reaches it only through local traffic [decisions:vm1].
- **A local difference may be diluted.** sw learners 1, 3 and 4 run the *same* checkpoints as w1u500, w3u500 and w4u500, but sw only consults them downstream. Read that way, 2 of 3 CIs show the same networks less confident in X1:
  - sw: −0.021 [−0.041, −0.011], −0.009 [−0.046, +0.010] and −0.036 [−0.054, −0.010];
  - v3w: +0.012, +0.007 and +0.001.

  This is suggestive only, because sw's upstream rule changes the traffic its policy sees [decisions:vm2].
- **Both test cells differ from the band†.** Against band runs of equal mean density, X1 and X2 are both less confident (residuals −0.046 [−0.059, −0.043] and −0.057 [−0.064, −0.052]) and reverse more (+0.035 [0.032, 0.038] and +0.036 [0.034, 0.039]). This is a difference between the test cells and the band average, not something specific to X1 [decisions:D5*].
- **Outside the trained range (S1†).** At 7,000†, the reversal share is below the band trend under all three fit forms (−0.013 to −0.023). Whether confidence is above or below the trend depends on the fit form, so I draw nothing from it. Raw `conf_med`: 0.843 at 3,500† and at 4,500†, 0.651 at 6,000†, 0.554 at 7,000† [decisions:D5*, decisions:vm5].

Correct wording: "a different decision pattern in X1 is not shown at whole-run resolution". That is weaker than "v3w does not act out of distribution".

### 5.3 Gap choice and close-following

- **v3w picks longer gaps in X1.**
  - Its V2V-on share at 0.8 s is 0.731 [0.721, 0.737] in X1 against 0.775 [0.768, 0.783] in X2: −0.044 paired [−0.057, −0.035]. Its mean V2V-on gap is 0.021 s longer [0.017, 0.028] [decisions:D6].
  - Within each road the commanded level also falls: edge 3 −0.156 [−0.173, −0.105], 4a −0.090 [−0.126, −0.079], edge 4 −0.080 [−0.099, −0.062]. So the decisions themselves change, not only where the ALKS spend their time [decisions:D6].
  - tail, sw and baseline-v3 do the same. 3E-T's 0.8-s share is not shown to change (−0.008 [−0.024, +0.006]), but its mean gap lengthens (+0.016 s [0.010, 0.026]) [decisions:D6].
  - Level shares are not split by speed, so the longer gaps may sit in slow traffic, where they matter little [decisions:vm8].
- **Longer gaps, yet more close-following.** Close-following still rises 17.0 % from X2 to X1. p333, whose level choice is identical in both cells, rises 23.0 % [decisions:D7*].
- **Short-gap share orders the rules, but not the policies.**
  - Among the 14 rule arms, more time at 0.8 s goes with more close-following (Spearman −0.82 in X1, permutation p 0.0002; −0.75 in X2) [decisions:vm3].
  - The four policy arms sit far below that trend: 15-30 % excess over no control at a 0.8-s share of 0.67-0.76, against 72-86 % for rules at 0.73-0.77. For example, v3w at 0.731 has 16.6 % more than no control, while os1_15_10 at 0.733 has 74.1 % more [60.8, 94.2] [decisions:D7*].
  - So the overall short-gap share does not explain the gap between policies and rules.
- **Where the policies put short gaps.** On ramp 2 they keep ALKS near 1.6 s (v3w commanded level 0.35 on r2 and 0.33 on rj2, against os1_15_10's 1.60 and 1.90 and p333's 2.25 and 2.82) [decisions:D8*]. That this placement in space and time explains the policies' lower close-following is the leading hypothesis; it is untested.
- **Reversals.** v3w's X1 reversal share is 0.472. It is 0.452 without the ALKS whose V2V is on less than 20 % of the time, against 0.25-0.32 for the rules. So churn by ALKS whose level never acts does not explain the difference [decisions:D10, decisions:vm10].
- **Timing proxy (low confidence).** Grouping ALKS by departure time suggests v3w lengthens gaps for cohorts that pass the X1 slowdowns. The 1,080-1,140-s cohort shows −0.094 [−0.103, −0.084]. But that cohort reaches edge 4 at 1,406-1,468 s, after the second slowdown has ended, so it meets the queue and the recovery, not the slowdown itself [decisions:D9].

### 5.4 The p333 0.934 value

- The panel "ALKS at the longest level, V2V on" plots `level_share_on[-1]`, which is level index 3. With `HEADWAYS_S = (1.6, 1.2, 1.0, 0.8)` s, index 3 is 0.8 s, the **shortest** gap. The title is inverted: a high value means more time at the shortest gap. This changes how the first look should read that panel [decisions:D1].
- p333 is CavRule [3, 3, 3]: it asks for 0.8 s for every ALKS in every zone. It never reverses and makes no excess changes [decisions:D2].
- Every ALKS starts at level 0 (1.6 s) and moves up one level per 10-s hold. In X1 the climb takes on average 10.5 s of about 159 V2V-on seconds per ALKS: 1 − 10.5/158.8 = 0.934 [decisions:D2].
- Traced per vehicle, among ALKS with V2V on at some point: the median is 15 s below level 3, p90 23 s, the maximum 24 s, and no vehicle spends over 30 s [integrity:vm4, integrity:F11*].
- The share rises with demand, because V2V-on time per ALKS grows while the climb stays the same: 0.910 at 3,500† (109.6 s per ALKS) and 0.947 at 7,000† (205.1 s) [decisions:D2].
- No decisions are taken in the 300-s warm-up. So every ALKS already on the road at 300 s also starts at level 0, and part of the climb is a window-start effect that all arms share [decisions:vm9].
- In practice, the "share at the shortest gap" has a ceiling of about 0.91-0.95, not 1.0. os1_15_10 reaches the same ceiling at 4,500† (0.912) [decisions:D2].

---

## 6. Operating map: v3w against every non-learning controller

You asked (2026-11-08) that the map compare v3w with all non-learning controllers, not only p333. Positive = v3w better: less delay or close-following. "=" = not shown to differ. X1 and X2 have 40 seeds; band† and S1† levels 20.

**The answer in short** [map_all:F5, map_all:fix-a]:
- No rule is shown better than v3w on delay anywhere: 0 of 58 delay CIs. No rule is shown better on delay and close-following together in any of the 9 cells or levels.
- On close-following, only no control is shown better: in X1, at 3,500† and at 7,000†.
- On hard braking, no control, 3E-T and copy lead in the cells listed under each table.
- Outside X1 and X2, only four controllers ran (§6.4, coverage gap).

**A note on copy.** copy sets a fixed level per road; nothing adapts at run time. Its levels were traced from baseline-v3's DRL policies (confirmatory 3), so its design is learning-derived. It counts as non-learning here [map_all:vm4].

### 6.1 X1 at 5,300 veh/h (40 seeds)

| Opponent | Delay | Close-following |
|---|---|---|
| no control | +27.3 [+24.7, +30.4] | −16.6 [−25.1, −8.4] (no control better) |
| p333 | +5.5 [+2.9, +8.0] | +44.7 [+40.4, +53.6] |
| os1_15_10 | +6.3 [+4.1, +11.4] | +32.4 [+28.4, +35.5] |
| os0_10_10 | +5.5 [+3.2, +9.0] | +31.9 [+25.2, +37.5] |
| os1_10_0 | +6.3 [+4.3, +10.6] | +32.6 [+28.8, +38.2] |
| 3E-T | +5.4 [+3.5, +9.7] | +20.3 [+15.7, +22.9] |
| 3E-X1 | +7.8 [+4.0, +11.3] | +26.2 [+22.9, +28.9] |
| copy | +11.6 [+9.3, +15.2] | +22.2 [+16.2, +26.6] |
| lr1000_10_1 | +5.0 [+3.0, +8.8] | +39.5 [+33.3, +43.1] |
| lr1000_16_2 | +6.8 [+4.1, +9.5] | +33.3 [+28.4, +39.4] |
| lr400_13_2 | +7.2 [+5.0, +11.4] | +36.5 [+32.9, +40.1] |
| lr400_16_1 | +10.8 [+7.5, +13.4] | +18.8 [+15.9, +23.4] |
| a4400_10_1 | +9.9 [+5.8, +13.5] | +20.9 [+12.6, +23.7] |
| r4a1 | +10.3 [+6.6, +12.5] | +34.4 [+33.0, +37.3] |
| z33133 | +7.3 [+6.0, +10.3] | +37.3 [+33.8, +47.4] |

Source [map_all:F1, map_all:verify] (cells from `s01/map_all/tables.md`, which the verifier recomputed in full).

Braking and flow: on b45, no control (−28.8 [−32.4, −17.8]), 3E-T (−16.1 [−21.3, −10.2]) and copy (−5.4 [−11.7, −1.9]) are better than v3w; 3E-X1 and a4400_10_1 are not shown to differ. On b3, no control is better (−13.2 [−15.6, −9.6]); lr400_16_1 and a4400_10_1 are not shown to differ. On flow, v3w is shown better than all 15 opponents (14 rules and no control) [map_all:F1].

### 6.2 X2 at 5,300 veh/h (40 seeds)

| Opponent | Delay | Close-following |
|---|---|---|
| no control | +23.5 [+21.7, +25.4] | −0.9 [−5.8, +9.5] = |
| p333 | +6.1 [+3.4, +7.4] | +42.8 [+37.1, +46.8] |
| os1_15_10 | +6.5 [+4.0, +8.4] | +26.0 [+22.6, +33.6] |
| os0_10_10 | +2.4 [−0.6, +7.5] = | +20.0 [+16.0, +28.9] |
| os1_10_0 | +5.8 [+2.8, +8.2] | +27.4 [+21.5, +34.2] |
| 3E-T | +7.5 [+5.9, +9.3] | +11.5 [+5.6, +16.2] |
| 3E-X2 | +3.0 [+0.7, +5.6] | +12.3 [+5.0, +18.7] |
| copy | +11.6 [+10.5, +13.4] | +23.1 [+13.3, +29.9] |
| lr1000_10_1 | +4.1 [+0.2, +5.4] | +38.8 [+31.7, +45.3] |
| lr1000_16_2 | +5.8 [+2.8, +8.9] | +29.7 [+21.7, +34.6] |
| lr400_13_2 | +7.4 [+3.9, +9.2] | +29.0 [+18.0, +33.9] |
| lr400_16_1 | +10.0 [+5.5, +13.4] | +20.9 [+15.2, +26.6] |
| a4400_10_1 | +12.2 [+7.6, +13.7] | +19.3 [+14.6, +26.5] |
| r4a1 | +7.6 [+4.6, +11.7] | +26.2 [+21.9, +30.1] |
| z33133 | +8.1 [+6.3, +10.8] | +35.9 [+28.2, +44.7] |

Source [map_all:F2, map_all:verify] (cells from `s01/map_all/tables.md`).

Braking and flow: on b45, 3E-T is better than v3w (−8.5 [−13.5, −1.8]); no control, os0_10_10, 3E-X2, copy and r4a1 are not shown to differ. On b3, no control is better (−3.9 [−5.9, −0.9]). On flow, v3w is shown better than 14 of the 15 opponents; os0_10_10 is not shown to differ (+0.3 [−0.3, +0.7]) [map_all:F2]. In X2, os0_10_10, 3E-X2 and lr1000_10_1 are closer to v3w on delay than p333 is.

### 6.3 Band† and S1† (20 seeds per level; only four controllers present)

Every row here is † (outside the plant's stated intended use, V462(4)).

| Level | Metric | p333 | os1_15_10 | 3E-T | no control |
|---|---|---|---|---|---|
| 3,500† | delay | −0.2 [−0.9, +0.1] = | same runs as p333 | +0.8 [+0.3, +1.4] | +16.5 [+14.4, +17.9] |
| 3,500† | close-following | −0.9 [−40.5, +29.8] = | same runs as p333 | −18.8 [−32.5, +39.4] = | −272.7 [−303.6, −87.3] (no control better; 21.9 vs 5.5 per run) |
| 4,500† | delay | −0.2 [−2.0, +0.8] = | −0.5 [−2.6, +0.5] = | +0.5 [0.0, +2.1] | +22.9 [+20.8, +26.3] |
| 4,500† | close-following | +16.6 [−11.9, +44.6] = | +14.9 [−15.9, +32.9] = | −4.4 [−35.7, +26.8] = | −121.6 [−155.1, +7.3] = |
| 5,000† | delay | −3.2 [−5.3, +1.4] = | −2.4 [−5.7, +3.3] = | +3.3 [+0.3, +7.9] | +33.8 [+24.8, +39.9] |
| 5,000† | close-following | +8.1 [−36.7, +52.8] = | −2.4 [−32.0, +62.4] = | +17.5 [−8.6, +70.6] = | +48.2 [+6.3, +94.3] |
| 5,250† | delay | +1.3 [−8.9, +7.5] = | −1.4 [−6.7, +8.5] = | +6.5 [+1.0, +11.8] | +35.4 [+29.4, +38.8] |
| 5,250† | close-following | +45.6 [−40.8, +110.4] = | +26.9 [−41.6, +106.9] = | +34.4 [+7.1, +50.0] | +37.7 [+14.9, +55.4] |
| 5,500† | delay | −1.4 [−6.6, +2.8] = | +0.1 [−4.0, +4.2] = | +11.9 [+2.7, +15.2] | +33.7 [+29.4, +35.5] |
| 5,500† | close-following | +40.3 [+19.8, +51.2] | +24.7 [+13.4, +42.7] | +25.7 [+10.0, +36.2] | +1.7 [−12.5, +17.7] = |
| 6,000† | delay | +2.3 [−1.6, +6.3] = | +2.9 [−1.2, +7.4] = | +4.1 [+1.2, +7.7] | +26.4 [+22.5, +28.7] |
| 6,000† | close-following | +46.5 [+24.9, +57.0] | +25.7 [+12.6, +29.5] | +21.8 [+16.1, +27.7] | −0.6 [−14.2, +13.4] = |
| 7,000† | delay | +3.7 [+2.6, +5.2] | +6.6 [+1.6, +9.9] | +4.5 [−0.7, +6.2] = | +17.5 [+14.1, +20.6] |
| 7,000† | close-following | +42.3 [+36.9, +45.3] | +32.6 [+22.8, +40.2] | +1.4 [−2.2, +13.5] = | −70.4 [−76.1, −62.1] (no control better) |

Source [map_all:F3, map_all:F4, map_all:verify]. At 3,500† p333 and os1_15_10 are identical on every seed and key; at 4,500† they differ on 3 of 20 seeds.

Braking and flow [map_all:F3, map_all:F4, map_all:fix-a, map_all:verify]:
- On b45, no control is better than v3w at 3,500† (−24.6 [−36.1, −11.5]), 4,500† (−23.8 [−38.7, −0.5], upper bound close to 0), 6,000† (−14.0 [−23.5, −7.7]) and 7,000† (−67.4 [−72.6, −59.9]). 3E-T is better at 6,000† (−9.8 [−12.6, −2.8]) and 7,000† (−29.7 [−32.6, −23.7]).
- On b3, no control is better at 6,000† (−16.0 [−19.0, −9.5]) and 7,000† (−46.4 [−49.4, −42.1]), and 3E-T at 3,500† (−2.2 [−3.7, −0.6]).
- On flow, os1_15_10 is better at 5,000† (−0.2 [−0.2, 0.0], marginal).

### 6.4 Reading the map

- **Does any non-learning controller beat v3w?** [map_all:F5, map_all:fix-a]
  - Delay and close-following together: no rule, in any of the 9 cells or levels.
  - Delay alone: no rule anywhere. Of 58 delay CIs, 44 favour v3w and 14 are not shown to differ; 0 favour a rule. The 14 are p333 and os1_15_10 at 3,500-6,000†, os0_10_10 in X2 and 3E-T at 7,000†.
  - Close-following alone: only no control, in X1, at 3,500† and at 7,000†. Of 58 CIs, 39 favour v3w and 16 are not shown to differ.
  - Hard braking: no control, 3E-T and copy lead in the cells listed under each table.
  - These are 95 % CIs, unadjusted. An adjustment widens intervals, so it can only turn a lead into "not shown to differ". "No rule ahead on delay" holds under any adjustment; the counts of v3w leads are upper bounds [map_all:caveats].
- **The delay/close-following front** (rules only, point estimates; my reading of [map_all:F6, map_all:fix-b]).
  - "Beyond the front" is meant here in a weak sense: no rule dominates v3w, and v3w dominates at least one front rule.
  - In that sense v3w is beyond the front in X1, X2, 5,250†, 5,500†, 6,000† and 7,000†. It dominates the whole rule front under both point methods only in X1.
  - At 4,500† and 5,000† its position depends on the point method.
  - At 3,500† it is inside the front: p333 (= os1_15_10) is better by 390 vehicle-seconds of delay and 0.4 of close-following, both not shown to differ.
- **Strongest rule per cell (medians)** [map_all:F7].
  - Delay: lr1000_16_2 (X1), lr1000_10_1 (X2), p333 at 5,000-7,000†, p333 = os1_15_10 at 3,500† and 4,500†.
  - In X2, lr1000_10_1 has a lower median delay than v3w (226,204 against 226,353), yet the paired effect favours v3w (+4.1 [+0.2, +5.4]).
  - Close-following, without no control: a4400_10_1 (X1), 3E-X2 (X2), 3E-T at 3,500†, 4,500†, 5,500†, 6,000† and 7,000†, p333 at 5,000†, os1_15_10 at 5,250†.
- **tail and sw** show the same pattern, with small differences [map_all:F8*, map_all:fix-d].
  - No rule is better than either on delay in X1, X2 or any band† level.
  - On close-following, only no control is better: in X1 for both, and at 4,500† for tail (−67.8 [−122.4, −7.3]). At 4,500† v3w is not shown to differ from no control (−121.6 [−155.1, +7.3]). So tail's mark against no control differs from v3w's there; tail and v3w were not compared pairwise.
  - Not shown to differ in X2: tail from 3E-X2 on delay and from no control on close-following (+1.4 [−4.4, +8.7]); sw from no control and 3E-X2 on close-following.
  - On b45, 3E-T, 3E-X2, copy and, for sw in X1, a4400_10_1 are better. No control is better on b3 and b45 in X1 (both), at 6,000† (both), on b45 at 4,500† (tail) and on b3 in X2 (sw).
- **Marginal marks.** Five leads rest on a CI bound within 0.05 of 0 [map_all:fix-c].
  - They keep their marks under 100 alternative RNG seeds.
  - At 97.5 % intervals, 3 become "not shown to differ": 4,500† delay against 3E-T, 5,250† tail flow against 3E-T, and X2 b3 against lr400_16_1.
  - At 99 %, 5,000† flow (os1_15_10 better) persists: −0.160 [−0.221, −0.005]. 3,500† flow against 3E-T reaches a lower bound of exactly 0: +0.041 [0.000, +0.109] [check_r2].
  - One near-bound case goes the other way: at 4,500†, b3 against 3E-T is −1.26 [−4.50, +0.041]. A narrower interval could turn it into a 3E-T lead [map_all:vm6].
- **Coverage gap** [map_all:gap, map_all:vm3].
  - 12 rules ran only in X1 and X2 at 5,300 veh/h, never in the band or S1: os0_10_10, os1_10_0, copy, lr1000_10_1, lr1000_16_2, lr400_13_2, lr400_16_1, a4400_10_1, r4a1, z33133, 3E-X1 and 3E-X2. They include X1's and X2's best rules on delay and the close-following leaders a4400_10_1 and 3E-X2.
  - So "no rule beats v3w" in the band† and S1† means only no control, p333, os1_15_10 and 3E-T.
  - Filling the gap on the same seeds (band 7,440,880-899, S1 900-919), pairing with the existing rows: 1,400 runs for the 10 fixed rules (10 × 7 levels × 20 seeds), 1,680 with 3E-X1 and 3E-X2. Running 3E-X1 and 3E-X2 under condition T tests them outside their tuning cell.
  - A fresh-seed round, which every new round requires, also re-runs the 4 present controllers (4 × 7 × 20 = 560) and v3w (5 learners × 7 × 20 = 700) [map_all:vm3]:

| Fresh-seed round | 10 fixed rules | all 12 rules |
|---|---|---|
| without tail and sw | 2,660 runs | 2,940 runs |
| with tail and sw (+700 each) | 4,060 runs | 4,340 runs |

  - At V475's measured rate (2,600-3,050 runs per hour on the S0/S1 mix, $0.10-0.13 per 1,000 runs, pack on), that is about 0.9-1.1 hours of batch time without tail and sw and about 1.3-1.7 hours with them, and well under $1 either way (my estimate, runs × rate). In V475 the batch took 88 % of the total time; setup, reports and fetch took the rest. New seeds need your approval.
  - Every one of these rows would still be †.
- **Count.** 790 CIs, of which 785 are distinct: at 3,500† p333 and os1_15_10 are the same runs [map_all:vm5]. The verifier recomputed all 790 and the 405 medians with its own code, with 0 mismatches [map_all:verify].

### 6.5 v3w against p333 (the first look's question)

This view repeats one column of §6.1-6.3. The tuned rules for the same settings are in those tables. Paired effects, positive = v3w better [operating_map:F2*, operating_map:F3]:

| Setting | Seeds | `all_delay` | `ttc_net` |
|---|---|---|---|
| 3,500† (S1) | 20 | −0.2 [−0.9, +0.1] | −0.9 [−40.5, +29.8] |
| 4,500† | 20 | −0.2 [−2.0, +0.8] | +16.6 [−11.9, +44.6] |
| 5,000† | 20 | −3.2 [−5.3, +1.4] | +8.1 [−36.7, +52.8] |
| 5,250† | 20 | +1.3 [−8.9, +7.5] | +45.6 [−40.8, +110.4] |
| X1 (5,300) | 40 | +5.5 [+2.9, +8.0] | +44.7 [+40.4, +53.6] |
| X2 (5,300) | 40 | +6.1 [+3.4, +7.4] | +42.8 [+37.1, +46.8] |
| 5,500† | 20 | −1.4 [−6.6, +2.8] | +40.3 [+19.8, +51.2] |
| 6,000† | 20 | +2.3 [−1.6, +6.3] | +46.5 [+24.9, +57.0] |
| 7,000† (S1) | 20 | +3.7 [+2.6, +5.2] | +42.3 [+36.9, +45.3] |

Marks per setting (V = v3w shown better; v or p = point estimate favours v3w or p333, not shown; . = not shown, direction not listed) [operating_map:F2*, operating_map:F3, operating_map:F4]:

| Metric | 3,500† | 4,500† | 5,000† | 5,250† | X1 | X2 | 5,500† | 6,000† | 7,000† |
|---|---|---|---|---|---|---|---|---|---|
| delay | p | p | p | v | V | V | p | v | V |
| close-following | p | v | v | v | V | V | V | V | V |
| braking b3 and b45 | . | . | . | . | V | V | V | V | V |

- **Tally.** Over 9 settings × 6 metrics (54 comparisons), v3w is shown better in 25, p333 in 1, and 28 are not shown to differ. All 25 v3w leads come from five dense settings (X1, X2, 5,500†, 6,000†, 7,000†), and the six metrics are correlated. So the evidence is those five settings, not 25 separate results; three of the five are †. p333's one lead is finished_pct at 5,000† (0.19 percentage points [0.05, 0.32]), which fits chance: about 3 of 54 are expected under no effect [operating_map:F1*, operating_map:F10].
- **Per learner.** On delay, p333 is shown better in 1 of 45 learner-setting comparisons (w3u500 at 5,500†, −2.7 [−11.0, −0.02]), and v3w in 16: X1 5/5, X2 5/5, 7,000† 4/5, 6,000† 2/5, 5,500† 0/5. On close-following: p333 in 0 of 45, v3w in 26 [operating_map:vm2].
- **Braking and flow in dense settings.** In X1, X2, 5,500†, 6,000† and 7,000†, v3w has 12-23 % less `b3_step` and 22-29 % less `b45_step` than p333 (`b45_step` caveat from 4.1). It has 1.0-2.2 % more served flow in X1, X2, 6,000† and 7,000†; at 5,500† flow is not shown to differ [operating_map:F4].
- **Low and medium demand (3,500-5,250†, and 5,500† on delay).** On delay and close-following, nothing is shown to differ, and the CIs are wide. At 5,000†, the point estimate favours p333 by 3.2 %, and the CI allows p333 to be up to about 5 % better. At 5,250† it allows either arm to be up to about 8-9 % better. This is not equivalence [operating_map:F2*, operating_map:vm4].
- **Likely source of "p333 wins everywhere."**
  - On unpaired median `all_delay`, p333 is first of *all* arms at 3,500† (39,650 vs v3w 40,040), 4,500† (75,261 vs 76,766), 5,000† (105,944 vs 111,820) and 5,250† (137,904 vs 142,103). At 6,000† it is also below v3w (341,366 vs 345,390; tail is lowest). v3w has the lower median only at 5,500†, X1, X2 and 7,000†.
  - Paired, none of p333's leads is shown, and at 6,000† the paired estimate favours v3w (+2.3 %) [operating_map:vm1].
  - The panel medians at 5,000† favour p333 on 12 of 16 panels; paired, only 3 of them differ, all by small amounts [operating_map:F5*].
- **"p333 is the best rule" holds only narrowly.**
  - It holds among p333, os1_15_10 and 3E-T. p333 has less delay than 3E-T at 3,500† (1.1 % [0.5, 2.0]), 4,500† (2.2 % [0.4, 3.4]), 5,250† (6.0 % [1.4, 10.6]) and 5,500† (12.7 % [2.4, 18.5]).
  - In X1 and X2 other rules have the lowest median delay (§6.4), and in X2 os0_10_10 has less delay than p333 (2.9 % [0.5, 5.7]).
  - p333 has the most close-following of all rules run in X1 and X2 (15 distinct rules) [operating_map:F5*].
- **v3w against 3E-T.**
  - v3w has less delay at every level except 7,000†, where it is not shown (4.5 % [−0.7, +6.2]). At 4,500† the lower bound is only +0.03 [operating_map:F2*, operating_map:F9].
  - 3E-T has less `b45_step` in X1 (v3w 16.1 % more [10.2, 21.3]), X2 (8.5 % [1.8, 13.5]), 6,000† (9.8 % [2.8, 12.6]) and 7,000† (29.7 % [23.7, 32.6]).
  - At 7,000† their close-following is not shown to differ (+1.4 [−2.2, +13.5]) [operating_map:F4, operating_map:F9].
- **Close-following against no control, by demand, with every controller present.**
  - At 7,000† all four controllers have more than no control, per run and per vehicle-km: v3w +1,706 per run [1,505, 1,845] (61.3 % more per vehicle-km [53.6, 68.8]); 3E-T +1,739 [1,455, 2,042] (65.2 % [52.9, 77.0]); os1_15_10 +3,726 [2,805, 4,110] (145.1 %); p333 +4,813 [4,260, 4,973] (185.7 % [166.1, 194.7]). No control's base there is not small: 2,424 per run [operating_map:F6].
  - At 3,500† the large percentages (164-273 %) sit on a base of 5.5 per run. The absolute excess is 9-15 per run, and for 3E-T the CI includes 0 [operating_map:F6, integrity:vm6].
  - At 5,000† and 5,250†, v3w has *fewer* than no control (48.2 % fewer [6.3, 94.3] and 37.7 % fewer [14.9, 55.4]). There 3E-T, p333 and os1_15_10 are not shown to differ from v3w on close-following, except 3E-T at 5,250† (v3w 34.4 % fewer [7.1, 50.0]) [operating_map:F3, map_all:F3].

---

## 7. What this means for your ideas

**Recorded closures (read these before any S2 plan).**
- **X2 is closed.** Under D10's T2 reading (V466), the DRL claim against tuned rules is closed in X2 on this plant. No further DRL training, tuning, plant change or seed round is run in X2 on this plant [r2 l.14, l.432].
- **X1 has a test history.** It closed under confirmatory 3's [A3] (V395). Rounds 1 and 2 re-tested it, and round 2 was its third test on plant_c3; under D10 it does not close [r2 l.10, l.427]. A new X1 test would be the fourth, which adds forking paths.
- **The band and condition T are outside the plant's stated intended use** (V462(4)) [r2 l.396]. S1 runs under condition T too, at 3,500 and 7,000. Every † number in this report is such a row.
- **So any S2 aimed at X1 on this plant needs your explicit decision, with this history disclosed.** X2 can serve only as a report-only guard.

### (a) Improve X1 close-following without losing delay or X2

**What round 2 already tried.** Five trained changes, each one change to v3w's recipe, on v3w's training seeds [r2 l.450]. At validation, under round 2's advance rule, none was shown better than v3w in either cell [r2 l.111-115, l.421]. Positive = candidate better than v3w; 40 seeds, 95 %:

| Candidate | Change | X1 delay | X1 close-following | X2 delay | X2 close-following |
|---|---|---|---|---|---|
| 2B | learning-rate and entropy annealing, one critic scale | −1.6 [−2.9, +1.0] | −0.8 [−5.8, +2.3] | +0.1 [−2.5, +1.2] | 0.0 [−3.0, +3.2] |
| 1B | gate hold | −0.8 [−4.2, +1.0] | +0.2 [−5.1, +4.3] | −1.2 [−3.0, +0.2] | +0.3 [−4.4, +6.3] |
| 1D | hard braking charged at every 0.1-s step | +1.0 [−1.8, +2.9] | +4.4 [−0.1, +6.5] | +0.1 [−1.0, +1.7] | +2.2 [−0.2, +5.5] |
| ahead | look-ahead inputs | −0.7 [−3.2, +0.3] | +1.5 [−1.4, +7.3] | −0.8 [−1.6, +0.6] | +7.3 [+2.4, +11.2] |
| rep | X1's second slowdown in training | −0.4 [−1.6, +1.0] | +0.2 [−3.1, +4.2] | +0.2 [−1.7, +1.7] | +2.5 [−0.5, +5.7] |

ahead's X2 close-following CI excludes 0, but the gain stays below round 2's 10 % close-following path (`round_2.md` D2). 1D comes closest in X1. A null on these changes does not show that no other change would help [r2 l.423].

**Recommendation: settle the 4a mechanism before changing training.** Run a traced re-run of four X1 seeds for no control, one v3w learner and 3E-T (12 runs): 7,440,853 and 7,440,878 (largest excess) and 7,440,854 and 7,440,869 (median seeds) [x1_exposure:F7].
- For each close-following sample, log follower class, lane (acceleration lane 4a_0 or a main lane), road, gap, closing speed and required deceleration.
- Show that the untraced counters equal the stored rows, following the lesson that a trace can change a run.
- These are round-2 test seeds, so the trace is diagnosis only, never evidence for a claim. Their reuse needs your approval.

The trace decides between the three readings left for 4a. Each points to a different S2 change:
1. **Main-lane traffic reaches the queue tail at speed.** Then the target is a severity-aware term: required deceleration, or closing speed at TTC < 3 s, rather than the raw count. Severe closings rise where the excess sits (4a and edge 3), and the network total hides it [x1_exposure:F6*, x1_exposure:vm1].
   - How it differs from 1D. The current reward already charges each ALKS w_safety × (own TTC flag + own hard braking + 0.5 × (direct follower's TTC flag + follower's hard braking)), all as binary 1-Hz flags, in every reward mode [code:r2-metrics b_env.py l.836-843; r1 l.52]. 1D moved only the two braking parts to the share of each second spent braking hard, read at every 0.1-s step; both TTC flags stayed binary 1-Hz flags [code:r2-1d b_env.py l.857-860]. A severity term would differ by grading each closing, by required deceleration or closing speed, instead of a binary TTC < 3 s flag.
   - If the trace shows the excess is mostly hard braking, by the ALKS or by their followers, 1D already charged that at step resolution, and its X1 close-following was +4.4 [−0.1, +6.5], not shown.
2. **Ramp-2 vehicles stop at the lane end and followers close in.** Then the target is ramp-2 merging: lane-end stops rise by 461 vehicle-seconds [357, 558] over no control [x1_exposure:vm3]. The term's design is open.
3. **Shorter gaps in moving traffic.** Then the target is the gap choice on 4a and edge 3.

What the evidence already supports, in every case: act from the first slowdown on, on 4a and edge 3, while keeping the ramp-2 and merge-1 gains [x1_exposure:F2, x1_exposure:F8*, decisions:D8*]. The edge-3 part is a rate effect under both exposures [x1_exposure:vm2]. A term aimed only at 4a and edge 3 could give back v3w's gains on ramp 2 (−113) and the other roads (−73) in X1, and at merge 1 in X2 (−288) (my inference).

**Guards, fixed before any S2 data** (non-inferiority against v3w, same seeds):
- X1 delay: not more than 2 % worse than v3w, round 2's limit. At 40 seeds a 2 % limit on a point estimate passes a policy truly 2 % worse about half the time (V435) [r2 l.447].
- X2 close-following (`ttc_net`) and merge-1 close-following (E30): not worse than v3w's. These are read report-only, because X2 is closed (V466). They protect the merge-1 removal on which X2's "not shown to differ from no control" rests [x1_exposure:F8*].
- These are guards, not a claim reading.

- **Pros:** it targets what was measured; it is cheap (12 runs; size the time from the measured per-run rate before launching); and it avoids training against a mechanism nobody has confirmed.
- **Cons:** one more step before S2, and four seeds may not settle it. Any close-following term may cost delay (my inference): among rules, more short-gap time goes with more close-following [decisions:vm3], but no verified analysis links close-following to delay directly. The policies already sit far below the rule trend [decisions:D7*]. And S2 on X1 needs your decision on the test history.

**Weaker alternatives:**
- **X1-like double slowdowns in the training draw.** Already tried as rep. Its X1 close-following was not shown to differ from v3w's (+0.2 [−3.1, +4.2]) [r2 l.115, l.450]. The diagnosis also does not point to an out-of-draw failure:
  - the per-exposure increase also appears in X2, which is inside the draw (rate part +401 [320, 484]) [x1_exposure:F8*];
  - the policy has no clock or event memory, so the second event reaches it only as local traffic [decisions:vm1];
  - every controlled arm examined shows the X1 rise too (13-29 %) [decisions:vm6].
- **A severity-graded TTC term now, without the trace.** Weaker: it fits reading 1 only. If the 4a excess is lane-end stops (reading 2), it charges the wrong thing. And 1D, the nearest change already tried, was not shown better (X1 close-following +4.4 [−0.1, +6.5]) [r2 l.113].
- **An exposure-normalised measure as the yardstick instead of raw `ttc_net`.** Weaker: the excess survives every network-level normalisation (13.8 % more per vehicle-km [3.9, 22.3]; 9.9 % more per vehicle served [0.6, 20.2]) [x1_exposure:F3]. Only the unvalidated approach proxy on 4a turns it around [x1_exposure:vm2]. Project rules also forbid proxy headline metrics. Report per-km and per-served columns beside the raw count, never instead of it.
- **Do nothing, on the view that the excess is exposure.** Not supported at network level or on edge 3 [x1_exposure:F3, x1_exposure:F4*, x1_exposure:vm2]. It is still possible for the 4a part only.

### (b) A wider demand range (3,500 to 7,000) in training

**What S1 shows.** Every number here is †.
- **At 3,500†:**
  - every controller has 15.5-16.5 % less delay than no control, with similar gains on seeds with and without a slowdown (v3w 16.3 % and 16.5 %) [operating_map:F7];
  - v3w vs p333 on delay: −0.2 % [−0.9, +0.1], not shown to differ (p333 slightly better by point estimate) [operating_map:F2*];
  - close-following sits on a base of 5.5 per run [operating_map:F6];
  - the only measurable spread among controllers is that 3E-T has about 1 % more delay and about 2 % less `b3_step` [operating_map:F7];
  - every controller has 15-25 % more `b45_step` than no control, about 13-18 vehicle-seconds per run (`b45_step` caveat from 4.1) [operating_map:vm5].
- **At 7,000†:**
  - v3w has the lowest delay against no control, p333 and os1_15_10. Against 3E-T it is not shown to differ [operating_map:F2*, operating_map:F9];
  - its close-following is not shown to differ from 3E-T's, but it has 29.7 % more `b45_step` [23.7, 32.6] [operating_map:F4];
  - its raw confidence is lowest there (0.554), and its reversal share is below the band trend [decisions:D5*].
- v3w was trained at 4,500-6,000 only [r1 l.20]. S1 therefore measures how the current policy extrapolates, not what training there would do.
- Both levels are outside the plant's stated intended use (V462(4)). Training there would take the policy beyond it.

**Your worry, that the policy may "ignore" regimes with nothing to gain and wreck its behaviour.** The mechanisms below are hypotheses. None was tested here.
- *Advantage normalisation (hypothesis).* At 3,500 almost every action earns the same return, so the advantages are near 0.
  - Each training update covers 3 consecutive demand levels [r1 l.20]. With 3,500 added, some updates would hold only light traffic. Per-minibatch normalisation would then inflate noise into full-size updates.
  - In updates that mix regimes, light-traffic states would get almost no gradient, and the shared network would drift there with whatever it learns elsewhere.
  - The run commit's trainer normalises the advantages over each minibatch, for every candidate [code:r2-metrics c_train.py l.300-302, l.326]. That v3w's own training used this same code path was not checked.
- *Reward references (hypothesis, narrowed by the code).* Round 1 sets the reward references per level from no control in steady traffic (stage 0c) [r1 l.105]. At 3,500† no control has almost no close-following (5.5 per run even with slowdowns) [operating_map:F6]. But in the per-CAV environment's reward the TTC charge is a fixed-weight flag with no reference [code:r2-metrics b_env.py l.836-843], so a near-zero close-following reference cannot inflate it. The reference that divides is `n_ref`, no control's vehicles in system, in the shared term n / n_ref − 1 [code:r2-metrics b_env.py l.546-550, l.850-857; r1 l.53]. A 3,500 level would need its own `n_ref`; how that term scales across levels is not checked.
- *Reward scale (hypothesis).* Delay at 7,000† is far larger than at 3,500†. Without per-level scaling, high-demand episodes dominate the gradient.
- *Catastrophic forgetting (hypothesis).* If the demand mix shifts during training, for example in a curriculum, behaviour in regimes seen less often can decay. With levels cycling every 7 updates [r1 l.20], interference is more likely than forgetting.
- (my inference) Demand level is not a policy input [decisions:vm1]. For the network, a "regime" is a distribution of local states, so free-flow states probably already occur in training episodes. Not checked.

**Recommendation: keep 3,500 out of the training mix. Keep it, with 7,000, as a fixed regression check in every evaluation, as in S1.** Widen upwards only if S2 aims at over-capacity behaviour, and then in steps, watching the 3,500 check. Any training level outside 4,500-6,000 needs your decision, because it lies outside the stated intended use.
- **Pros:** no training budget goes where the controllers present differ by about 1 % of delay or less (3,500†: v3w not shown to differ from p333, 0.8 % less than 3E-T). The check catches a wrecked policy directly. It avoids the hypothesised normalisation and scale risks.
- **Cons:** it gives up, as a training target, the braking cost at 3,500† that every controller shares. With no learning signal in light traffic, a future policy could regress there; the check exists to catch that.

**Weaker alternatives:**
- **Uniform 3,500-7,000 in training.** Weaker: it spends budget where the controllers present differ by about 1 % of delay or less (3,500†), adds the hypothesised risks and leaves the intended use. The congested dynamics at 7,000† (finished_pct 54-70 %) [integrity:F5*] may dominate the reward.
- **Per-regime reward or advantage normalisation now.** Weaker as a first step: it treats a failure nobody has observed. Keep it for a wider-range run that shows the regression.

### (c) Switching tail/sw-like tweaks on by condition

**Evidence.**
- In X1, tail (15.3 % more than no control [6.7, 27.1]), sw (18.4 % [7.1, 27.4]) and v3w (16.6 % [8.4, 25.1]) have similar point estimates of the excess and a similar 4a/edge-3 pattern; they were not compared pairwise here [x1_exposure:F1, x1_exposure:F2]. All three are well below 3E-T's 47.5 % [decisions:D7*].
- Their braking medians and mean gaps are close too (similar point estimates, not compared pairwise) [x1_braking:F4, x1_braking:F6*, x1_exposure:vm6].
- Three sw learners run v3w's own checkpoints [integrity:F9].
- At round 2's validation, tail and sw were not shown to differ from v3w on X1 close-following (−3.2 [−7.2, +3.3] and +2.0 [−1.1, +5.4], positive = candidate better) [r2 l.116-117].

**Oracle check** [critic:oracle.out for the gate rows; own check, `revise/oracle_r3.py`, for every row]. Per seed, the gate picks with hindsight the variant with the least close-following. Both gates are in-sample upper bounds on the test rows, not measured ceilings, and report-only. Effect against no control, positive = fewer close-following seconds than no control:

| Gate | X1 | X2 |
|---|---|---|
| none (v3w alone) | −16.6 [−25.1, −8.4] [map_all:F1] | −0.9 [−5.8, +9.5] [map_all:F2] |
| arm-level: per seed, the lowest of the v3w, tail and sw arm means | −9.6 [−19.3, −0.6] | +7.0 [−1.9, +12.5] |
| per learner: per seed and learner index i, the lowest of w_i, t_i and s_i, then the mean over i | −0.9 [−11.5, +5.9] | +14.1 [+7.6, +18.7] |
| 3E-T, for reference | −47.5 [−59.0, −41.7] [decisions:D7*; own check] | −15.4 [−22.8, −4.6] [own check] |

- The arm-level oracle stays above no control in X1. The per-learner oracle is not shown to differ from no control. So this data does not rule switching out for X1 close-following.
- Both gates choose on the outcome itself, with hindsight. The per-learner gate takes the minimum of three runs per learner and seed, so part of its gain is selection on run-to-run noise (my inference). The delay of the gated arms was not computed.
- A real gate would need a condition signal that the policy does not have [decisions:vm1].

**Recommendation: do not build a switch for X1 close-following now.** If you want to pursue it, run an out-of-sample check first, from stored rows and with no new runs: pick, per learner and cell, the variant on round 2's validation rows, and read that choice on the test rows, on close-following and delay.
- **Pros:** no build effort until a gate that could exist shows a gain. The check is cheap. It follows the diagnosis that the excess is shared by every policy variant.
- **Cons:** it gives up, for now, whatever part of the per-learner oracle's gain is real. Switching for other targets (for example towards 3E-T for braking at 7,000†) was not evaluated.

**Weaker alternatives:**
- **Report the oracle as a measured ceiling.** Wrong: the "ceiling" moves from 9.6 % above no control to not shown to differ, depending on the gate's definition, and both are in-sample.
- **A learned gate.** It needs a condition signal the policy lacks. It is bounded by the in-sample oracle and adds detector errors.
- **A hand rule on local speed.** The same bound, plus tuning and more comparisons.

### (d) Plan B: perturbation resilience against tuned rules (never p333 alone)

**Evidence.**
- **X1:** v3w is shown better than all 14 rules on delay (+5.0 to +11.6 %), close-following (+18.8 to +44.7 %) and flow (+0.8 to +2.7 %) [map_all:F1].
- **X2:** v3w is shown better than 13 of 14 rules on delay; os0_10_10 is not shown to differ (+2.4 [−0.6, +7.5]), and the margins over 3E-X2 (+3.0 [+0.7, +5.6]) and lr1000_10_1 (+4.1 [+0.2, +5.4]) are narrow. It is shown better than all 14 on close-following (smallest margin 3E-T, +11.5 [+5.6, +16.2]) [map_all:F2].
- **Per learner,** against p333 only: delay shown better for 5 of 5 learners in X1 and X2, 4 of 5 at 7,000†, 2 of 5 at 6,000† and 0 of 5 at 5,500† [operating_map:vm2]. Per-learner comparisons against the other rules are not in the verified material.
- **These are arm-level 95 % readings.** Round 2's T2 read each policy at 99.17 % with a 10 % close-following margin. X2 was not won there: tail 3, v3w 2 and sw 0 of 5 against 3E-T and 3E-X2 [r2 l.11-16].
- **Against Plan B:**
  - braking: 3E-T has less `b45_step` than v3w in X1 and X2, copy in X1; no control leads on b45 in X1 and on b3 in X1 and X2 [map_all:F1, map_all:F2];
  - in X1, v3w still has more close-following than no control [x1_exposure:F1];
  - the tuned opponents are lower bounds: 3E-X1's and 3E-X2's searches had not converged, 3E-X1 failed the delay filter, and 3E-T ran 40 of 100 generations with convergence unchecked [r2 l.9, l.100, l.253];
  - V457's parallel-track opponents, an MPC with a model fitted on separate seeds and/or a non-learning adaptive scheduler, are not built [V457; r2 l.441];
  - in the band† and S1†, from 3,500 to 5,250, nothing is shown against p333 and os1_15_10, and only four controllers ran there [map_all:F3, map_all:gap].

**Recommendation: Plan B is a fair candidate only as a new pre-registered study, framed as a conditional advantage, and only after your explicit decision with the closures disclosed.** On X1 and X2 of plant_c3 it would be X1's fourth test and a re-opening of a closed X2. New perturbation cells would avoid re-testing closed cells, but they stay on the same plant with the same policies (my inference).
- **Hypothesis to pre-register (from this data, not a claim):** "under the pre-registered perturbations, the policy has less delay and less close-following than every tuned rule in the cell". This data supports that wording in X1. In X2 it holds on close-following and against 13 of 14 rules on delay. At 7,000† v3w has less delay than p333 and os1_15_10 and is not shown to differ from 3E-T.
- **Opponents per cell:** all 14 rules, the 3E rules re-tuned per cell until their searches converge, and V457's MPC and/or adaptive scheduler, or a disclosed reason for leaving them out. Never p333 alone, never no control alone.
- **Seeds:** fresh, approved by you.
- **Side constraints:** hard braking reported per opponent, including where v3w loses (3E-T on b45).
- **Report** the band region where nothing is shown, and every † row as outside the intended use.
- **Pros:** it fits the conditional-advantage principle. In X1 v3w is shown better than all 14 rules on delay, close-following and flow. In X2 it is shown better than all 14 on close-following and 13 of 14 on delay. Rules lead on b45 [map_all:F1, map_all:F2]. The comparison needs no new training.
- **Cons:** the closure history; the braking cost against 3E-T; opponents that are lower bounds, so the advantage may shrink against converged ones; X1 close-following above no control; X2's per-policy margins failed at T2; building the MPC opponent costs time.

**Weaker alternatives:**
- **Against p333 alone.** Forbidden, and misleading too: p333 has the most close-following of all rules run in X1 and X2, and in X2 os0_10_10 beats it on delay [operating_map:F5*].
- **Against no control alone.** Forbidden by the project rules.
- **Re-reading the existing X1/X2 rows as Plan B evidence.** These are the round-2 test rows, already used. Reading them again for a new claim adds forking paths.
- **The report-only operating map in article 1 instead (V457(1)).** It needs no reopening and is already decided, but it supports no claim, so it is weaker as Plan B.

---

## 8. Caveats, open questions and comparisons

**Caveats**
- Report-only. S0 reused round 2's test and band seeds, and S1 used fresh seeds. Nothing here supports a claim. A claim needs a pre-registered protocol and fresh seeds.
- Every band and S1 row (†) is outside the plant's stated intended use (V462(4)).
- No single close-following or braking event was traced. The 4a mechanism is open.
- The road, speed and period splits are marginal, not joint. Nobody can say from the stored data which speed band the 4a excess falls in.
- The −4.5 threshold sits on the braking limit, so `events_ge45` is speed-selective [x1_braking:F3*]. (my inference) `b45_step` comparisons inherit this. The truck part of the −4.0 count (truck limit 4.0) and the −9 ALKS bin sit on limits too [x1_braking:F5*]. The pile above −7 m/s² is unexplained [x1_braking:F13].
- Zero teleports is not evidence of health. Use collisions and contact steps [integrity:vm2].
- S1 pack neutrality is inferred, not shown [integrity:vm5].
- The CI ignores uncertainty in the no-control median. About 6 % of no-effect comparisons exclude 0 at n = 20 [integrity:F14, operating_map:F10].
- The approach-exposure proxy was defined after seeing the data and is not validated on 4a [x1_exposure:vm2].
- The first-look smoothness ranking (jam share, oscillation, congested length) is based on medians without CIs [integrity:vm7].
- The all-rules map is arm-level only, at unadjusted 95 %. Its band results that are not shown to differ are low power, not equivalence (CI widths reach about 100-150 points at 5,000-5,250†). Its front is read from point estimates [map_all:caveats].
- The oracle figures are in-sample upper bounds on the test rows, and they change with the gate's definition [critic:oracle.out; own check].
- The code readings in §7 (reward terms, advantage normalisation) show what the run commit's code does; that v3w's training used the same path was not checked.
- Left out because no verifier recomputed them: the no-control-calibrated counterfactual regressions, the 5-km/h histogram bin differences, the stopped share within the slow band, moving-cell density, per-learner moving rates, the 128 test_table cells, and any reading of "jam clusters".
- The inverted panel title (`measure2.py` METRICS, line 215) should be relabelled before anyone reads that panel again. That is a code change outside this report.

**Open questions**
1. What makes up the 4a excess: queue-tail approaches, ramp-2 lane-end stops, or shorter gaps? (Answered by the trace in 7a.)
2. Do v3w's decisions differ downstream in X1? This needs per-decision confidence by place and time in a later pack [decisions:vm2].
3. Are the longer X1 gaps in slow or in moving traffic? This needs level shares split by speed [decisions:vm8].
4. Why does every gap-shortening controller have about 5x no control's past-limit ALKS braking [x1_braking:F6*]?
5. Do the `b45_step` rankings hold when counted at −4.0 and −5.0?
6. Does a cell-level switch between v3w, tail and sw help out of sample (§7c)?
7. Do the 12 rules missing from the band and S1 change the map there (§6.4)?
8. Did v3w's training use the run commit's reward and per-minibatch advantage normalisation, and how does the shared term's `n_ref` scale across demand levels (§7b)?

**Comparisons made.**
- The six analyses made 10,859 statistical comparisons in total:
  - integrity: 0 (plus 761,642 exact-equality checks);
  - x1_exposure: 2,868;
  - x1_braking: 3,963;
  - decisions: 1,253;
  - operating_map: 1,985;
  - map_all: 790 (785 distinct).
- The verifiers added about 3,600 more for the first five (x1_exposure about 1,440, x1_braking about 386, decisions about 350, operating_map about 1,450). The map_all verifier recomputed all 790 CIs and 405 medians and re-ran the marks under other RNG seeds. Many of these recompute the analysts' intervals.
- The critic made about 60 interval estimates. My own checks made 8 intervals (the whole oracle table, the 3E-T row included, re-run for revision 3 with `revise/oracle_r3.py`) and 19 medians (`revise/pastlimit_check.py`).
- That is about 15,000 interval estimates or tests in all. They overlap and are correlated, and none is corrected for multiplicity. With about 6 % chance exclusions, several hundred "CI excludes 0" results are expected by chance, which is why this draft leans on large, consistent effects only.
