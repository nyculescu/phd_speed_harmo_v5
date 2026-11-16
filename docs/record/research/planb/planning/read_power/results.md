# Plan B power and cost (planning only)

Read-only on stored rows; no simulation. The stored X1/X2 rows are round 2's test rows (S0 re-runs). Here they are used only to size a new protocol, never as evidence (V478). X1/X2 effects are a proxy for new cells, nothing more. Every band and S1 row is outside the plant's stated intended use (V462(4)).

Data: `/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_{test,band,s1}.jsonl`. v3w = per-seed mean over w0u250, w1u500, w2u250, w3u500, w4u500. Statistic: round 2's `conf3/common.raw`, sign × median(P − O) / median(O) × 100, percentile bootstrap, `default_rng(20261104)`. Robust braking: `ev4_ca` = events peaking at −4.0 or harder, cars + ALKS (`m_peak_*[2:]`); `ev5_alks` = ALKS events in (−9, −5] (`m_peak_alks[4:8]`). Both as `s01/analysis/x1_braking/common_x.py`. The fields exist in every row.

Check: the scripts reproduce s01 §6: X1 lr1000_10_1 delay +5.0 [+3.0, +8.8]; X2 os0_10_10 +2.4 [−0.6, +7.5]; X1 close-following against no control −16.6 [−25.1, −8.4]; X1 ev4_ca against no control −7.2 [−11.5, −4.8].

## 1. Paired differences (positive = v3w better; percent of the opponent's median)

| cell | metric | effect range over the 14 rules | weakest rule | SD of d over rules (median) | against no control |
|---|---|---|---|---|---|
| X1 | delay | +5.0 to +11.6 | lr1000_10_1 +5.0 [3.0, 8.8] | 6.7-10.7 (8.4) | +27.3, SD 6.8 |
| X1 | close-following | +18.8 to +44.7 | lr400_16_1 +18.8 | 10.9-17.2 (14.5) | −16.6, SD 22.9 |
| X1 | ev4_ca | −7.6 to +13.3 | lr400_16_1 −7.6 [−12.0, −3.8] | 6.5-9.5 (8.4) | −7.2 |
| X1 | ev5_alks | −5.2 to +48.6 | copy −5.2 [−12.6, +2.4] | 13.0-19.4 (16.6) | −422 (no control has about 9 per run) |
| X2 | delay | +2.4 to +12.2 | os0_10_10 +2.4 [−0.6, 7.5]; 3ex2 +3.0; lr1000_10_1 +4.1 | 5.0-7.7 (6.5) | +23.5, SD 5.6 |
| X2 | close-following | +11.5 to +42.8 | 3e +11.5 [5.6, 16.2] | 12.9-20.2 (16.9) | −0.9, SD 21.3 |
| X2 | ev4_ca | −6.9 to +12.1 | 3e −6.9 [−10.2, −2.8] | 7.9-10.5 (9.2) | −6.1 |
| X2 | ev5_alks | −2.3 to +29.1 | copy −2.3 | 15.2-19.8 (17.9) | −399 |

Opponent medians: delay 237k-266k vehicle-seconds (X1) and 226k-250k (X2), against v3w's 231k and 226k. Close-following 2,216-3,364 (X1) and 1,732-2,710 (X2), against v3w's 1,809 and 1,534. Band and S1 levels (only 3 rules; full table in `diffs_summary.md`): delay SD 1.1-3.1 % at 3,500-4,500, 6.6-16 % at 5,000-6,000 and 4.3-6.6 % at 7,000. Close-following SD reaches 56-136 % at 3,500-5,250, because the base counts are small.

**The median statistic is lumpy.** For some opponents, the per-seed differences have a gap around 0. In X1 against os0_10_10, 12 of 40 seeds are negative, and none lies between −1.5 and +1.7. The bootstrap lower bound then jumps between clusters: about 21 % of simulated studies give a lower bound at or below 0 (the lowest 10 % near −2), while 95 % of their point estimates stay at 3.9 or more. As a result, the pass rate against os0_10_10 is lower than a normal approximation would predict (66 % at n = 40, m = 3). The same lumpiness makes the stored lower bound depend on B: with 4,000 resamples it is 2.72, with 20,000 it is 3.2.

## 2. Power (bootstrap from the stored seeds; 1,000 simulated studies per n, 500 for the scaled scenarios)

**Choice of m.** Within a cell, "better than every rule on delay and close-following" is an intersection over rules and metrics. An intersection-union test needs no correction across opponents: round 2 did the same (`round_2.md` l.194). So **m = the number of cells c (2-4)** when the claim reads "in at least one pre-registered cell", and **m = 1** when it reads "in every cell". m = 30 is shown as the ultra-conservative case (Bonferroni over about 15 opponents × 2 cells).

W3 = delay lower bound > 0 **and** close-following lower bound > 0 against all 14 rules (the V478 claim shape). Percent of studies:

| cell | n | m=1 | m=2 | m=3 | m=4 | m=30 |
|---|---|---|---|---|---|---|
| X1 | 20 | 33 | 16 | 12 | 10 | 1 |
| X1 | 40 | 76 | 64 | 59 | 51 | 24 |
| X1 | 60 | 91 | 83 | 80 | 76 | 51 |
| X1 | 80 | 96 | 94 | 92 | 91 | 74 |
| X2 | 20 | 4 | 1 | 1 | 0 | 0 |
| X2 | 40 | 17 | 8 | 6 | 4 | 0 |
| X2 | 60 | 36 | 23 | 17 | 14 | 3 |
| X2 | 80 | 52 | 40 | 33 | 30 | 8 |

- **Delay is what binds.** In X1, W1 (delay alone), W2 (close-following not worse than −10 %, by point or by bound), W3 and W4 (close-following ≥ +10 %) have the same power. The binding rules are os0_10_10, 3ex1 and os1_15_10. In X2 the binding rules are os0_10_10, lr1000_10_1 and 3ex2. Close-following binds only against 3E-T, at small n.
- **Smaller true effects.** Converged 3E rules could shrink v3w's margins. With delay and close-following effects scaled to 0.75 × stored: X1 W3 at m = 3 is 23 / 56 / 81 % at n = 40 / 60 / 80; X2 is 1 / 4 / 12 %. At 0.5 × stored, X1 W3 at m = 3 is at most 17 % (n = 80; 41 % at m = 1), and at 0.25 × it is 0 everywhere.
- **Hard braking as a gate would usually fail.** W3 plus ev4_ca not worse than 10 % (lower bound > −10) against every rule: X1 13 / 25 / 31 %, X2 7 / 22 / 39 % at m = 1, n = 40 / 60 / 80. Adding ALKS past-limit events: at most 6 % in X1. So braking fits the V478 wording only as a stated cost. Mean 95 % CI width at n = 60: ev4_ca 6.7 points (X1) and 5.7 (X2); ev5_alks 12.2 and 8.6.
- **V459-style bar against no control:** delay ≥ 10 % and no close-following harm. In X2 it passes in 100 % of studies. In X1 it passes in only 26 / 10 / 5 / 3 % at n = 20-80, because close-following harm against no control becomes shown as n grows.
- **Band and S1 levels** (only 3 rules; outside the intended use): W1 is 0-3 % at 3,500-5,500 at every n. At 6,000 it is 16-36 % (m = 1), and at 7,000 it is 71-96 % on delay, but W3 there is ≤ 12 %, because 3E-T ties on close-following.
- **Several cells** (`combos.md`; independent cells, each like X1 or like X2): with 3 cells at m = 3 and n = 80, "W3 in at least one cell" has 100 % power if all cells are X1-like, 97 % if half are, and 70 % if all are X2-like. At 0.75 × effects these become 99 / 85 / 31 %. "W3 in every cell" (m = 1) is 89 / 26 / 14 %.
- **Inner bootstrap size:** B = 4,000 against 20,000 on the same simulated studies changes power by 0-5.5 points (largest gap: X1 m = 4, 55.5 against 50.0).

**False positives under the label-swap (sign-flip) null.** Per seed and opponent, the two runs swap with probability ½, all metrics together. The table gives the per-comparison one-sided false "better" rate, as a mean over the 14 rules, for delay, close-following and ev4_ca:

| m | nominal | n = 20 | n = 40-80 |
|---|---|---|---|
| 1 | 2.5 % | 2.8-3.3 % (max 4.5) | 2.3-2.8 % (max 3.7) |
| 3 | 0.83 % | 0.8-1.2 % | 0.8-1.0 % |
| 4 | 0.63 % | 0.7-1.0 % | 0.6-0.8 % |
| 30 | 0.083 % | 0.10-0.26 % | 0.09-0.19 % |

- Two-sided at m = 1 and n = 20, the rate is 5.9-6.1 %; s01 §8 reported about 6 %.
- So the statistic is slightly liberal at n = 20 and close to nominal from n = 40. In the far tail (m = 30) it runs up to about 2-3 × nominal, partly from Monte Carlo noise.
- **Rule level:** under the global null, W1 and W3 are 0.0 % (the intersection is very conservative). In the least favourable configuration (only the closest rule null, all else as stored), W1 or W3 is ≤ 2.8 % at m = 1, ≤ 1.4 % at m = 3 and ≤ 1.0 % at m = 4. That is about the per-comparison rate, as an intersection-union test should give.

## 3. Cost (`cost_table.md`)

Per cell:
- **Evaluation:** (15 opponents + 5 learners + no control) × n. The 15 opponents are 12 fixed rules, 3E-T, the per-cell 3E and one V457 opponent; 14 or 18 opponents change the totals by under 1 %.
- **3E search:** generations × 24 × 16 seeds, plus 40 reference runs and 7 × 40 final runs. That is 15,680 runs at 40 generations (round 2's searches; `cma3e_x1/runs.jsonl` holds 15,400 rows), 38,720 at 100 and 57,920 at 150.
- **Tool checks:** about 300 runs (my estimate). **Pilot:** 21 arms × 10 seeds.

Rates:
- **Rental A** (V475, 59 workers, $0.312/h): 2,450-3,050 runs/h. The X1/X2 rows ran at about 2,450/h, measured from file times. Wall time = batch / 0.88.
- **Rental B** (V461, 244 workers, $0.81/h): about 6,400 runs/h, measured on the 3E searches.
- **Laptop** (V425-V426, 31 workers): 1,330 runs/h by day. V465's 3,201 laptop rows in 2.41 h match this. The night rate of about 530/h under the 40 % cap is assumed, not measured.

| cells | n | 3E generations | total runs | rental A h | rental A $ | rental B h | rental B $ | laptop days |
|---|---|---|---|---|---|---|---|---|
| 2 | 60 | 40 / 100 / 150 | 34.9k / 81.0k / 119.4k | 13-16 / 30-38 / 45-55 | 4-5 / 9-12 / 14-17 | 6 / 14 / 21 | 5 / 12 / 17 | 1.5 / 3.4 / 5.0 |
| 3 | 60 | 40 / 100 / 150 | 52.4k / 121.5k / 179.1k | 20-24 / 45-56 / 67-83 | 6-8 / 14-18 / 21-26 | 9 / 22 / 32 | 8 / 17 / 26 | 2.2 / 5.1 / 7.5 |
| 4 | 60 | 40 / 100 / 150 | 69.8k / 162.0k / 238.8k | 26-32 / 60-75 / 89-111 | 8-10 / 19-23 / 28-35 | 12 / 29 / 42 | 10 / 23 / 34 | 2.9 / 6.8 / 10.0 |

- **The 3E searches are 90-98 % of all runs.** Evaluation alone (3 cells × 21 arms × 60 seeds = 3,780 runs) takes 1.4-1.75 h on rental A, under $0.50. Going from n = 60 to n = 80 adds 420 runs per cell: for 3 cells, 1,260 runs, about 0.5 h and $0.15.
- **Sequential floor of one 3E search:** about 437 s per generation on 122 workers (V461), so about 12 h for 100 generations. With 3-4 searches sharing one machine, the time is set by throughput (the table).
- **Not costed:**
  - building and running V457's MPC or adaptive scheduler (not built; its per-run time may be much longer);
  - the convergence rule itself (how many generations is unknown: round 2's searches were still falling at 40, with sigma flat at 0.23-0.28);
  - code and V&V work for perturbation kinds that do not exist yet (a lane closure or demand surge; `perturb.py` has none, brake, truck, burst, slowdown, outage and random);
  - an optional per-cell re-pick of confirmatory 3's 69-form grid: 69 × 20 = 1,380 runs per cell, under 4 % of the total.
- **Fresh seeds needed** (count only; the author approves ranges): per cell, 40 for 3E tuning + 10 for checks + 10 for the pilot + n. That is 360 seeds for 3 cells at n = 60, and 560 for 4 cells at n = 80.

## Files

Each line is the script, then the output it writes:
- `load_arms.py` → `arms.pkl`
- `diffs.py` → `diffs_table.md`, `diffs_summary.md`, `diffs.json`
- `power.py` → `power_all.json`
- `check_bin.py` → `check_bin.json`
- `report.py` → `power_tables.md`
- `combos.py` → `combos.md`
- `cost.py` → `cost_table.md`, `cost.json`
