# critic_F: attack on direction F and screen F

Scope: memo §1.1 H2/H4, §1.2 M6, §3 H-3/H-4, §5.2. "EXPL" = my exploratory number from stored S6 rows or recorded fields (already read for a verdict, no multiplicity control). J = `/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json`. Intervals are 97.5 % unless stated; positive = v3w better. Scripts and outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/critic_F/` (`null_F.py`, `checks.py`, `j2.py` to `j6.py`, `*_out.txt`).

## Findings

**F1. BLOCKER. Screen F's own KILL rule already fires in steady traffic on 240 recorded seeds.**
- J `S.map`: against 3E-C_TRUCK close-following +7.99 [−11.71, +31.46] at delay −0.01 [−1.33, +1.28]; grid_z31333 +7.05 [−18.14, +33.98]; lr400_16_1 +4.96 [−3.91, +27.15]. All three pass the screen's delay filter; none was tuned for S (`j6.py`, EXPL re-reading).
- In S, v3w is shown worse on delay than p333 −1.57 [−2.70, −0.24], os0_10_10 −1.61 [−2.78, −0.89], os1_15_10 −1.66 [−3.18, −0.66]. "Equal delay" is false there.
- X1 is worse than no control (−16.6 [−25.1, −8.4], round_2_result.md:265); X2 is closed (V466). INFERENCE: F is a TRUCK-only claim, on a cell chosen after related DRL results (planb.md:136), outside intended use, with S2 registered KILL (J `must_carry`; V486, V487).
- Change: write the scope as "TRUCK only; KILLed in S by stored rows", or add S to stage 1 under the same rule.

**F2. BLOCKER. At 80 seeds the KILL rule is mostly noise at the recorded effect.**
EXPL (`null_F.py`): 240 paired TRUCK seeds resampled, v3w pooled against 3E-C_TRUCK, shifted to a stated true edge; 4,000 studies, rng 20261111. Paired close-following SD = 37.8 % of 3E-C's median; v3w is lower on 60.4 % of seeds.

| True edge | P(KILL), 80 seeds, 97.5 % | 80 seeds, 95 % | 240 seeds, 97.5 % |
|---|---|---|---|
| 0 % | 0.994 | 0.988 | 0.998 |
| 8 % | 0.826 | 0.782 | 0.823 |
| 12 % | 0.609 | 0.524 | 0.303 |
| 15 % | 0.345 | 0.269 | 0.029 |
| 20 % | 0.104 | 0.072 | 0.001 |

- The gate can pass and fail (false pass at 0 %: about 0.6-1 %). A true 12 % edge is KILLed 61 % of the time; an 80 % pass needs about 18-20 %, more than the recorded edge over the unconverged rule.
- The 10 % point threshold sits 1.8 points under the observed 11.80 and was written after seeing it (precedent only: V462(1) tile rule).
- Change: 240 verdict seeds (10 arms = 2,400 runs, about $1.3 at V493-V494's rate, my arithmetic); print this table in the screen; state the level (97.5 % was Plan B's m = 2 cells, planb.md:427) and the threshold's source.

**F3. BLOCKER for the word "safety". The gate is not outside the reward, misdescribes the meter, and stored rows already answer it.**
- The reward holds TTC < 3 s and braking ≤ −3 m/s² (b_env.py:32, :798, :808, :839-843). TTC < 1.5 s and braking ≥ 4.5 are subsets of rewarded events; DRAC uses the same gap and closing speed. The memo's H2 omits the braking term.
- `e1_meter.py:14` supplies ttc3, drac3/7, brake3/7 and onsets: no TTC < 1.5, no 4.5. Its gap omits minGap (`e1_meter.py:73`); the stored count adds it (plant_sweep.py:162), so README.md:33's equality smoke fails as built (INFERENCE). Never hooked or run (README.md:31-34; V435; no import under `v5b/` or `planb/`). Cost: no record; it calls `getLeader` for every vehicle every 0.1 s (the pack alone is ×1.24, V468).
- The S6 rows already carry these measures (J `cells.TRUCK.map_report_only`; V468, V501). Against 3E-C_TRUCK: ttc15 +37.47 [+26.53, +49.47], sev3 +26.84 [+18.95, +39.30] (1 Hz); b45_step −1.55 [−5.05, +3.56]; robust braking −0.50 [−1.89, +1.28]; **braking events peaking at 4.5 m/s² or harder −5.73 [−8.80, −1.29], v3w shown worse** (read6.py:148). So clause 1 ("shown worse on any") fires now, and clause 2 ("better on at least one") cannot fail, because ttc15 is nested in the reward. One hit among 23 opponents × several measures, uncorrected: fragile both ways.
- "safe" and "safer" are already barred (planb.md:153; outline_v1.md:55).
- Change: remove the meter gate from stage 1. If kept: a fixed measure list, one named opponent, margins, multiplicity; the stored S6 values stated as the prior; meter fixed (minGap, thresholds), smoke-checked and timed before any cost line.

**F4. MAJOR. "Continue 3E-C from generation 100 to the plateau criterion" is undefined and measures selection luck.**
- Seeds: 16 of a 40-seed pool per generation, a window that repeats every 5 generations (cmab.py:42-44, :219; cma2.py:143, :325).
- The plateau exists only as "incumbent check loss at 60 minus at 100 < 1.0", "not scaled by any SE" (planb.md:238; cmab.py:51-52, :149). Incumbent trace (`checks.py`, from `planb_s34_remote/cmab/TRUCK_ttc/checks.jsonl`): −23.97 (60), −32.22 (70, 80, 90), −32.53 (100). The label fails on the 60→70 jump alone. INFERENCE: under a rolling 40-generation reading it holds at generation 110 unless one candidate scores below −33.22; the "converged rule" is then today's 3E-C and stage 1 is F2's coin.
- The incumbent is the minimum of 54 noisy check losses on 40 seeds. Check: −32.53 % at delay −0.10 % (`pick.json`). Fresh S6: 21.18 % fewer than p333 [14.77, 31.20] at 1.28 % more delay [0.48, 2.06] (J `overfit_vs_p333`, 95 %). INFERENCE: SE of a 40-seed check loss is about 10 points (SD 50.9 %, EXPL), so the 1.0 threshold is 0.1 SE; 200 more generations add 120 draws on the same 40 seeds. 3E-T showed the same, −14.3 % → −4.4 % (round_2_result.md:394). Overfit weakens the rule on fresh seeds, so it favours v3w.
- The population is still moving: generation-median close-following −12.6 % (generations 80-89) → −17.0 % (90-99), σ 0.092 (`run.log`).
- cmab.py:204 refuses a resume when `gens`, `check_at` or the code hashes differ: a continuation is a harness change. The memo's seeds contradict "continue": a new pool 7,485,100-139, no selection set, and "check" 200-279 used for the verdict.
- Change: a fixed budget (generations 100-300, no data-dependent stop); three disjoint seed sets (pool, selection ≥ 80, verdict 240); today's 3E-C (g098i00) kept as an arm and as an opponent; plateau reported, never used as a stop.

**F5. MAJOR. The opponent objective and the "richer family" let the search budget decide.**
- The filter admits every rule "not shown worse by more than 2 %". At 80 seeds (paired delay SD 6.5 %, EXPL) that admits rules up to about 4 % worse by point (INFERENCE). 3E-C's hinge is +1 % against p333 (cmab.py:47; planb.md:227). The strongest admissible opponent (hinge +2 %) is deferred to stage 2, so a stage 1 pass decides nothing.
- KILL is a union over every searched rule, uncorrected: each extra search adds KILL chance (0.345 each at a true 15 %).
- Richer family: no functional form, parameter count or generation budget. 100 generations did not settle 20 parameters; INFERENCE: 40 or more will not, so "frontier exhausted" cannot be delivered. A flexible rule on the actor's inputs found by CMA-ES is policy search (the memo's L3 lists evolution strategies as a learner); with H-4, the rule/learner line is undefined.
- Change: fix before data the family (form, parameters), the searches (number, hinge, generations, pool) and total rows; admit opponents by delay non-inferiority to p333 at the margin v3w must meet; one pre-named deciding opponent, or a correction.

**F6. MAJOR. The claim form has no delay test and is a trade-off.**
- The screen never tests v3w's delay. V435: 80 % power at a true tie needs about 60 seeds at a 5 % margin (95 % bound), 80 (97.5 %), about 160 at 3 %, SD 7-11 % in X2; "a margin under 5 % is not affordable" (explore2/README.md:23). In S, non-inferiority is not shown at 2 % against 7 opponents, nor at 3 % against os1_15_10 (`j6.py`, EXPL). A 5 % margin exceeds every delay difference among the nine tied rules (under 1 %).
- "No sentence claims a win on one measure alone" (planb.md:153, V462(1)); "a trade-off, not a net win" (claim_review_round2.md:197).
- M6 holds in TRUCK: about 75 % of counted seconds are on edge 4a, merge 2 (v3w 591.9 of 784.0; 3E-C 673.5 of 892.0; J `location`, medians, EXPL), lane end not validated (V396; PR-28, planb.md:183). v3w's lane-change share of close-following is shown higher than 21 of 23 opponents (J `ttc3_lc_share`).
- Change: add a delay non-inferiority test, margin and seeds fixed (INFERENCE: TRUCK SD 5.3 % supports about 2.3 % at 80 seeds at a true tie); S and no control as deciding rows; an author decision on V462(1).

**F7. MINOR.**
- (a) Frozen v3w against rules tuned in the cell is conservative on tuning (V478; planb.md:197, :215). §5.2 does not say so, nor that a KILL leaves "retrain for TRUCK" open. Add both; pre-commit no rescue by retraining. Not conservative: the cell selection.
- (b) Costs. 200 generations = 76,800 + 4,800 check rows. At V490's 40,640 rows in 7 h 42 min and $0.605/h: about 15.5 h, $9.4; 100 generations $4.7, not $4. §0 and §4 say "about $5". The 720-run check at $0.4 agrees with V493-V494. It is a new study: Plan B's $20 cap has about $2.50 left (V488, V494).

## Verdict

Is F worth its stage 1 cost as written: **no**. F1 and F3 are answered by stored rows at zero cost. F2 and F4 make the $5-10 buy a roughly 60 % KILL by noise against what is probably the same rule. Redesigned (changes F2, F4, F5, F6; about $11-12, my arithmetic) it could give one TRUCK-only sentence.

My probability that F survives both stages as written: about 10 %. That it gives a thesis-usable claim beyond a report-only TRUCK row: about 5 %. Both are judgement, not measured.
