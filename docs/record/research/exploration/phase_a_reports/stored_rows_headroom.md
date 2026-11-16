# stored_rows_headroom: Plan B S6 rows, exploratory headroom reading

Everything computed here is EXPLORATORY: the rows were already read for the S6 verdict (V495, V496, V501). Unless a record is cited, numbers are mine: paired seeds, median of paired differences as % of the opponent's median, 95 % percentile bootstrap, 10,000 resamples, rng 20261110, no multiplicity control.

## Source and validity

- read6 v2.3 read `/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl` (`planb_s6_read_v23/run.sh`; SHA-256 69ccafc0… equals `inputs.sha256` and my own hash), not `planb_s56_backup` or `planb_s6_rebuild`. The rebuild only supplies 14 side files (V498-V500).
- 13,920 rows = 58 arms × 240 seeds (7,480,400-639), no drops (V494). One deciding cell, TRUCK (`read6_config.json`). S (steady, same seeds, same 29 arms) is the reference condition. Every number below rests on 240 paired seeds.
- Check: my pooled points equal the record (os0_10_10 −0.58, p333 −0.25; per-learner points equal `d4.learner_points`).
- Unit: `all_delay` is vehicle-seconds over the fixed window against 100 km/h (plant_sweep.py:347, read6.py:55). "s per planned vehicle" divides by `m_planned_window` (median 2,210, identical in every arm of a seed); that normalisation is mine.
- ASCH is an alias of lr1000_16_2 (`provenance.breakdown.aliases`).

## 1. Recorded table (TRUCK, v3w pooled, positive = v3w better, 97.5 % interval; read6_v23.json `comparisons`, V496)

| Opponent | Delay % | Close-following % |
|---|---|---|
| os0_10_10 | −0.58 [−0.93, +0.20] | +22.57 [+17.44, +27.90] |
| lr1000_10_1 | −0.25 [−0.83, +0.50] | +26.94 [+19.21, +35.30] |
| p333 (fixed) | −0.25 [−0.83, +0.50] | +26.94 [+19.21, +35.30] |
| 3E-D_TRUCK | +0.08 [−0.57, +0.90] | +30.25 [+22.98, +38.45] |
| grid_os1_10_10 | +0.16 [−0.68, +1.05] | +27.17 [+19.98, +32.61] |
| os1_15_10 | +0.18 [−0.64, +0.94] | +25.75 [+18.38, +29.70] |
| lr1000_16_2 (= ASCH) | +0.27 [−0.25, +0.90] | +28.80 [+21.81, +35.48] |
| lr400_13_2 | +0.72 [−0.04, +1.54] | +28.50 [+20.70, +34.07] |
| grid_lr400_13_1 | +0.83 [−0.05, +1.72] | +25.26 [+19.51, +31.33] |
| MPC-F | +1.09 [+0.56, +1.76] | +27.59 [+22.31, +32.01] |
| 3E-C_TRUCK | +1.12 [+0.75, +2.11] | +11.80 [+4.97, +19.71] |
| 3e (3E-T) | +4.62 [+3.75, +5.84] | +29.48 [+23.44, +35.52] |
| copy | +11.11 [+9.92, +12.48] | +33.33 [+29.17, +38.05] |

- The first nine rows block the delay claim: their lower bound is at or below 0. The margin is small: worst point −0.58 %, worst bound −0.93 %. The other 14 opponents have a delay lower bound above 0 (from grid_z31333 +0.98 [+0.56, +2.00]).
- Close-following: lower bound above 0 against all 23. Flow points run from +0.10 % (3E-D_TRUCK) to +1.16 % (copy).
- Per learner (mine, 95 %): delay CI above 0 for 5 of 5 learners against 13 opponents (MPC-F and the 12 with higher median delay), 0 of 5 against lr1000_10_1, p333 and os0_10_10; no learner is CI-clear worse than any opponent. Close-following CI above 0 for 5 of 5 against all 23.
- Estimator note (INFERENCE, not a re-reading). The pooled arm is the per-seed mean of 5 runs, the opponent is one run, and delay is right-skewed. The pooled median (161,591) is 0.64 % above the mean of the 5 learner medians (160,557). Against os0_10_10 the pooled point is −0.58 while the 5 per-learner points average +0.04; against p333, −0.25 and +0.14. On paired means (positive = v3w lower, % of opponent mean): lr1000_10_1 +0.55 [−0.11, +1.24], os0_10_10 +0.41 [−0.25, +1.10], and CI above 0 against the other 6 blockers (3E-D_TRUCK +0.71 [+0.06, +1.37] to grid_lr400_13_1 +2.28 [+1.45, +3.16]). It stays a tie with the three best rules. In S the recorded pooled reading has v3w behind os0_10_10 (−1.61, 95 % [−2.64, −1.03]); the paired mean gives −0.50 [−1.93, +0.96].

## 2. Absolute headroom

| Arm | TRUCK median, veh-s | s per planned vehicle | S median, veh-s |
|---|---|---|---|
| No control | 231,312 | 104.3 | 200,589 |
| Best single opponent | 161,493 (lr1000_10_1; p333 has the same median) | 72.7 | 125,808 (grid_os1_10_10) |
| v3w pooled | 161,591 | 72.6 | 127,465 |
| v3w learners | 158,775 to 162,362 | 71.9 to 73.2 | 124,690 to 126,693 |

- Share of no-control delay removed, TRUCK: best opponent 29.29 % [27.97, 30.20]; v3w 28.94 % [28.24, 30.01] (record: +28.94 [+28.07, +30.10], V496). S: 35.20 % [34.25, 38.32] and 35.54 % [33.30, 37.56].
- About 70 % of no-control delay remains, but that is not the cap: the floor is not 0 (the reference is 100 km/h) and the rows hold no free-flow run. The recoverable part cannot be computed from the rows.
- Reference (INFERENCE): TRUCK − S on the same seed is +28,788 veh-s [25,185, 31,821] for no control (equals the recorded `nc_median_loss`), +33.2k to +33.6k for four of the best rules, +31,459 [30,806, 32,909] for v3w. The truck-induced part is about 20 % of the best rule's TRUCK delay.

## 3. Hindsight selection oracle (per-seed minimum over the 23 opponents)

- TRUCK: +3.42 % [+2.70, +4.17] below the best single opponent; adding no control changes nothing. v3w is 4.14 % [3.66, 4.68] above the oracle. S: +5.19 % [+4.00, +6.61].
- It is biased upward by selection. Checks:
  - Same-recipe yardstick: the per-seed minimum over the 5 v3w learners is +2.09 % [+1.49, +2.53] below the best single learner; the oracle over the 5 lowest-median rules gives +1.19 % [+0.74, +1.81]. Picking among nominally equal policies "gains" more than picking among the best rules.
  - Split-half, 2,000 splits: a 3-bin scheduler on no-control delay (a difficulty proxy), fitted on one half, gains +0.01 % [−0.91, +1.02] on the other, where the hindsight oracle shows +3.83 %. The best single chosen on one half sits +1.02 % above the other half's best.
  - A scheduler that picks per seed the rule that was lowest in S on that seed: −0.97 % [−1.47, −0.37], worse than the best single.
  - Twin rules p333 and lr1000_10_1 give identical delay on 194 of 240 seeds; where they diverge, the SD of the difference is 1.59 % of the median (grid_r4a2 and grid_a41000_10_2: 190 seeds, 3.16 %).
- INFERENCE: 3.4 % is an optimistic bound, and no tested conditioning recovered any of it.
- Two of my checks failed as nulls and are not used: a per-opponent shuffle across seeds (+9.75 %; it breaks the shared seed term) and a twin-noise simulation (+0.46 % in TRUCK, +6.55 % in S; heavy tails).
- Missing for a clean bias estimate: replicate runs of one controller on the same demand draw with another random stream. The rows hold one run per arm and seed.

## 4. Per-seed winner

- TRUCK: 22 of 23 opponents win at least one seed. Top shares: lr400_13_2 10.0 %, 3E-D_TRUCK 8.3 %, grid_lr400_13_1 7.5 %, MPC-F 7.5 %. The best single (lr1000_10_1) wins 2.8 % and is within 1 % of the per-seed minimum on 17.9 % of seeds. S: 20 winners, top lr400_16_1 13.3 %.
- A rule's seed-centred delay in TRUCK correlates weakly with its value in S on the same seed (median r 0.20, range −0.03 to 0.28).
- INFERENCE: no rule is best on most seeds, but the variation behaves like run-to-run noise. Adaptation headroom inside the family is neither shown nor excluded.

## 5. Delay against close-following (TRUCK medians: veh-s, seconds per run)

- v3w 161,591 / 819.5; p333 = lr1000_10_1 161,493 / 1,178; os0_10_10 162,350 / 1,116; grid_lr400_13_1 162,333 / 1,080.5; 3E-C_TRUCK 164,871 / 951; no control 231,312 / 1,234.
- No opponent is shown better than v3w on both measures, or on either one. v3w is shown better on both than 15 of 24 (14 opponents and no control). Pareto set by medians: v3w and p333/lr1000_10_1.
- v3w sits where no opponent reaches: at delay within ±1 % of the nine tied rules, its close-following is 22.6 to 30.3 % lower (smallest: os0_10_10, 251.9 s per run).
- Nearest on close-following is 3E-C_TRUCK: +112.2 s per run [59.2, 180.2] more than v3w, with +1,839 veh-s [1,391, 3,233] more delay. Its search was "not converged at 100 generations" (`provenance.plateau`, V496), so the rule family's close-following frontier is not exhausted. By medians it reaches 283 of v3w's 414.5 s reduction against no control (INFERENCE).
- Against no control, v3w has less close-following in TRUCK: +29.06 % [+26.35, +33.31] (record `no_control.cf95`). Only 4 of 23 rules are CI-clear below no control. In S: +45.86 % [+42.20, +50.47]; there the edge over 3E-C_TRUCK is not shown (+7.99 [−9.72, +25.32]).

## 6. Variance and power (v3w − best single opponent, TRUCK)

- SD of the paired difference: 5.32 % of the opponent's median (8,586 veh-s) for the pooled arm; 6.18 to 6.72 % for one learner. SE of the median 0.342, of the mean 0.343.
- Smallest gain detectable with 80 % power at n = 240: 0.96 % (two-sided 95 %), 1.06 % (S6's 97.5 %).
- Seeds needed, pooled arm, 97.5 % (95 %): 2 % → 68 (56); 3 % → 30 (25); 5 % → 11 (9). One learner, mean-based: 104 (86), 47 (39), 17 (14).
- S: SD 11.21 %; detectable 1.4 to 2.2 %; 2 % needs 113 to 299 seeds.
- Caveats: normal approximation; W needs the bound against all 23 opponents and 4 of 5 learner signs, so real power is lower.

## Reading against the hypotheses (INFERENCE)

- H1 holds here: the fixed rule p333 ties for the lowest median among 23; the CMA-ES delay rule, MPC-F and the grids do not beat it.
- H2: the first half holds (the edge is on close-following only). The second half fails in TRUCK and S, where v3w is safer than no control. The record has the opposite in X1 (cells_tested.md A22, A25).
- H4 holds for delay. On close-following the best searched rule stops at about two thirds of v3w's reduction, unconverged.
- S6 was not underpowered: it could detect about 1 %. Any true delay edge over the best rule in TRUCK is below about 1 %.
- Likely to fail: a delay claim on this plant and actuator, and a scheduler hybrid over the existing rules (bound 3.4 %, realised 0.0 %).
- Credible only as a different claim form: delay non-inferiority with close-following superiority. T2 (delay point ≥ −2 %) reads 5 of 5, report-only (V496, V501). It would need fresh seeds, a margin fixed before data, a converged 3E-C search and a safety measure outside the reward.

## Scripts and outputs

Folder `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseA/rows/`: `load_rows.py` (cache `s6_scalars.npz`), `analyse.py` → `analyse_out.txt`, `extra.py` → `extra_out.txt`, `distinct.py` → `distinct_out.txt`, `recorded_table.py` → `recorded_table_out.txt`, `inspect_rows.py`, `inspect_read.py`.
