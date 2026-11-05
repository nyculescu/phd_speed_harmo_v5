# Confirmatory 3: DRL against several rule forms on the fixed plant

Status: revision 2, approved by the author in V378 with the defaults at [A1] to [A6]; approved text at commit `170f84a`. The first tuning row comes from a later code commit, named in the ledger. Nothing here has run.

## Question

Under a sustained slowdown on r2m3 at 5,300 veh/h, on the fixed plant, do per-CAV DRL policies have fewer seconds at time-to-collision below 3 s, at about equal delay, than the best of several rule forms tuned on separate seeds?

## Plant and actuators

r2m3 with `docs/research/p0c/plant_p0d.json` (P0d), frozen as baseline v2. Not tuned for this study.

[A1] Two actuators still step on the whole second, and both are changed before any rule or policy runs, with a bench and a check first:

- **Headway rises.** When an ALKS loses V2V, its tau jumps from 0.8 to 1.6 s at once, which on one seed gave p333 about 70 moving full-emergency events per run that 1-Hz samples mostly miss. Rises are limited to 0.2 s per 1-s update; falls are unchanged. A new flag; our model, disclosed.
- **Slowdown taper.** The limit is written once per second. It moves to the 0.1-s clock and reaches the same limit at the same time.

No-control runs without a perturbation never use either, so baseline v2 reproduces.

## Controllers

No control is reported in every table and is not an opponent.

Rule families, all on the 10-s clock:

| Form | Members | Rules |
|---|---|---|
| Uniform | 1.6, 1.2, 1.0, 0.8 s | 4 |
| By zone | all patterns of 1.2 or 0.8 s over the 5 zones, except the 2 uniform ones | 30 |
| On road 4a | 1.6, 1.2 or 1.0 s on 4a, 0.8 s elsewhere | 3 |
| Local adaptive | 0.8 s, or 1.2 or 1.0 s when mean speed in the next 400 or 1,000 m is below 10, 13 or 16 m/s | 12 |
| Adaptive on 4a | local adaptive at 1.2 or 1.0 s, plus 1.2 or 1.0 s on 4a respectively | 12 |
| Own state | 0.8 s, or 1.2 or 1.6 s when past x = 500 m and own speed is below 10 or 15 m/s, with or without at least 10 vehicles on the accelerating lanes | 8 |
| Copy of the policies | mean level per road, traced from the trained policies on the tracing seeds, rounded to the nearest level | 1 |

70 rules. A rule tree distilled from each policy is not included: it needs new code, and it may be added only before the code freeze.

No MPC or forecast controller is an opponent; this arm is dropped. No oracle runs on r2m3; this is disclosed.

DRL: per-CAV, as in V334, without the speed action. PPO, gamma 0.933, lambda 0.967, safety weight 10, flow weight 0.4. 5 learners x 3 environments, 500 updates, final policies only, no selection. Evaluation takes the greedy action. Training draws perturbations as in V358, at levels 4,090, 4,600, 5,300.

Training settings come from a committed script, not by hand: `hold` 10, `seed0` 7,451,320, `seeds_per_worker` 520, workers 9-23, plant from `plant_p0d.json` with geom r2m3 and references from P0d no-control rows at all 3 levels. A check asserts all of this against the config saved with each learner. PPO network seeds are new, not those of earlier runs.

## Choosing the opponents

Each primary cell separately, on tuning seeds. A rule knows the condition and level in advance, not the event's time or place, and DRL knows neither. This favours the rules on knowledge; choosing on few seeds can also weaken them, so several go forward.

1. A rule is admissible if its median paired delay against p333 is at most 2 % worse and its collisions are at most p333's plus 1.
2. The lowest-TTC admissible rule of each form, and p333, go to the evaluation seeds.
3. On evaluation seeds, an opponent counts only if it stays within 2 % of p333 on delay. The table states which did not.

If only p333 is admissible in a cell, the sentence says so.

Also on evaluation seeds, not deciding the claim:

- **Delay opponent:** the rule with the lowest median delay among those with TTC at most 10 % worse than p333.
- **Single rule:** the rule admissible in both cells with the highest mean TTC gain over them, run in all 10 cells. It is the comparison with equal information, and its row reports the adaptation gain: per-condition rule against single rule, and the share DRL closes, with paired CIs.
- **Front row:** the rule with the lowest TTC among those with delay at most 10 % worse than p333.

## Conditions and levels

| Code | Condition | Role |
|---|---|---|
| X1 | Tapered slowdown, edge 4, 25 km/h, 120 s, at 600 and 1,200 s | primary at 5,300; map at 4,600 |
| X2 | Tapered slowdown, edge 3, 30 km/h, 180 s, at 700 s | primary at 5,300; map at 4,600 |
| S | Steady | map |
| H1 | Slow truck, cap 50 km/h, every 300 s | map |
| H2 | Ramp bursts, 120-s grid | map |

2 primary cells, 8 map cells. Map cells compare the policies with no control, p333 and the single rule; they are not tuned per cell and support no claim.

## Seeds

| Use | Range | State |
|---|---|---|
| Pre-run check under controllers | 7,440,065-074 | [A6] new, needs approval |
| Rule tuning and reward references | 7,440,160-179 | approved V376 |
| Tracing the policies | 7,440,180-189 | approved V376 |
| Evaluation, used once | 7,440,200-219, 20 paired seeds per cell | approved V376 |
| Training | 7,456,000-7,463,999 | approved V376 |

## Metrics

Primary, reported together: door-to-door delay and served flow. The delay limit below reads all-vehicle delay, because a mean over finishers leaves out the worst delays: vehicle-seconds in the system minus distance over free speed, unfinished vehicles and the insertion queue included. Finishers' delay and TTT are reported beside it.

Deciding surrogate for this claim: network TTC below 3 s. It is also a term of the policies' reward, its threshold comes from training needs (V265), and most of it is a low-speed queue, at median 5-7 m/s on one seed, largely around merge 2. Reported with it, in every row: TTC below 1.5 and 2 s; samples needing at least 3 m/s² to avoid the leader, dv²/(2 gap); all by road (3, 4a, r2 and rj2, rest), by follower speed (below 5, 5-10, above 10 m/s), and by period (before, taper, hold, 120 s after, rest).

Counted every 0.1 s: braking at 3, 4.5 and 7 m/s² for all vehicles and for ALKS; free-road ALKS braking; moving full-emergency events (2 m/s or faster; lane-end creep counted apart); fuel; jerk. Also: undertakes, lane-end stops at both ramps, ramp delays, collisions.

## Statistic

Effect = sign x median(P - O) / median(O) x 100 over paired seeds. CI: percentile bootstrap of the paired differences, 20,000 resamples, denominator fixed, at 97.5 % for 2 primary cells. Per-run lower = median(O - P). Collisions: sum over the 20 runs. A counter missing from a row is 0. `decide3.py` is committed before training and reproduces V368's table on `shot_rows`.

## Claim rules, fixed before data

[A2] Two readings, both with numbers fixed before their own results. An independent test of revision 1's single 30 % bar against a tuned rule gave about 5-20 % chance of passing at the effect sizes seen, and a pass or a tie could not be told apart. Those power figures are plug-in estimates from P0 rows. No false positive in 3,000 no-effect resamples.

**Tuned reading, which decides the claim.** A primary cell is won on TTC if at least 4 of 5 policies have, against every opponent that counts in that cell: TTC at least 10 % better (V363's number), CI excluding 0, and at least 20 per run lower; delay at most 2 % worse; flow at most 0.5 % worse; braking at 3 m/s² at most 5 % worse; moving full-emergency events at most 5 % or 5 per run more; collisions at most the opponent's plus 1. Also against p333: delay at most 5 % worse and flow at most 1 % worse.

**Replication reading, reported beside it.** At least 4 of 5 policies meet V359's safety rule against p333 on P0d: TTC at least 30 % better, with the same limits. It says whether the earlier result survives the plant fix.

**Delay win:** at least 4 of 5 policies have, against the lower-delay of the delay opponent and p333: delay at least 5 % better, CI excluding 0; flow at most 0.5 % worse; TTC and braking at most 10 % worse; collisions at most the opponent's plus 1.

**The word "safety"** may be used only if at least 4 of 5 policies are also no worse than the opponent on samples needing at least 3 m/s². Otherwise the sentence says "fewer seconds at TTC below 3 s; severe conflicts not shown to differ".

## Sentences allowed

Every sentence names the model: an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds.

| Outcome | Sentence |
|---|---|
| Cell won on TTC | Under [slowdown], at least 4 of 5 per-CAV PPO headway policies had [x] % [CI] fewer seconds at TTC below 3 s than each of [n] rule forms tuned on separate seeds, with delay and flow within the stated limits. This is a surrogate. [Where the gain is] |
| Only p333 counted | The same, against the fixed 0.8 s rule; no other form met the delay filter |
| Replication yes, tuned no | The edge over the fixed 0.8 s rule held on the fixed plant, but the policies did not clear the margins against [rule]: [TTC, delay] |
| Copy rule not cleared | The policies did not clear the margins against a fixed per-road rule copied from them: [TTC, delay] |
| Single rule beaten, per-condition rules not | An advantage of not needing the condition in advance; no general claim |
| Delay win | Per-CAV DRL has a delay advantage in the listed cell |
| Neither reading | The edge seen on P0 was not confirmed on the fixed plant with this budget and these actions |

Every sentence also states, from this run: no control's TTC, delay and braking, and "no control had fewer such seconds, at [y] % more delay" whenever at least 4 of 5 policies are clearly worse on TTC; collisions, which are too rare to compare; and the map cells where at least 4 of 5 policies are clearly worse than the cell's reference, on delay by over 2 % or TTC by over 10 %. Cells not listed are not shown to be unharmed where the CI is wide.

No "first" or "novel" wording. All controllers are reported per cell as an operating map.

## Closing the line

[A3] If no primary cell is won, this DRL line closes on these slowdowns: no further training, tuning, plant change or seed round, and the negative result is reported. If one cell is won, the other closes the same way. A re-run under the bug rule below is not a new round.

## Stop rules

- From the first tuning row: no change to plant, rules, reward, budget or claim rules, except by a logged author decision, disclosed, followed by fresh tuning and evaluation seeds.
- Any failed pre-run check stops the chain and goes to the author.
- **Early kill,** after rule tuning: if no rule beats no control on delay by at least 10 %, CI excluding 0, in X1 or X2 at 5,300, the chain stops and goes to the author.
- A learner that crashes restarts with the same seeds and is logged. A learner failing the collapse check stays in with a disclosure; it keeps its vote and is not replaced. If more than one fails, the chain stops before evaluation.
- A bug found after results: fix, re-run everything affected, log both.
- Every primary cell, won or not, is traced on 2 evaluation seeds. A trace can add an explanation; it cannot change the outcome of a claim rule. The sentence names where the gain is.

**Collapse check:** mean reward over updates 401-500 within 0.03 of updates 301-400, and at least the mean of updates 1-50. Null from the shot's learners: at most 0.027. It detects collapse, not convergence, so level shares over training and the u250 policy against the final one, on 5 tuning seeds in X1 and X2, are also reported.

## Order and checks before the run

1. **Build:** both actuator changes; rule classes; TTC and period counters; `_x` and the zone offsets on r2m3's real lengths, with the position input no longer clipped before the road ends; opponent selection, `decide3.py`, the policy tracer, the config generator. All in one commit before training.
2. **Code review:** [A4] adversarial, as `CLAUDE.md` requires before long runs, of that commit.
3. **T3, determinism:** at the run commit, r2m3 no-control rows of baseline v2 reproduce every numeric key (`r2_p0d`, seed 7,440,045, 4,600 and 5,300); r1m3 P0d rows too. `decide3.py` reproduces `shot_table.csv`.
4. **Bench:** one vehicle, a tau rise of 0.8 to 1.6 s as built and rate-limited.
5. **T0, under controllers, on seeds 7,440,065-074, gates fixed now:** r2m3 at 5,300, S, X1, X2; no control, p333, `r4a1`, `lr1000_10`, each rule form once, and one stored policy as a trace-only arm. Per controller: 1-Hz braking within 5 % of step braking; TTC at whole and half second within 5 %; moving full-emergency events at most no control's plus 5; tau of eligible ALKS equals the commanded level; duplicate rules give identical rows.
6. **T1, T2:** report, on those rows, that control changes flow and delay against no control. No capacity drop is established on these plants, and the rule's value does not rest on one.
7. **Smoke in training mode:** the eased cap, tau limit, 0.1-s taper and random perturbations reach SUMO; per-vehicle reward varies; references are P0d's.
8. **Run:** rule tuning, early kill, training, collapse check, tracing and the copy rule, evaluation, reading.

## Compute

Measured on the P0d check: 240 runs in about 21 minutes on 24 workers, with no controller.

Rule tuning: 70 rules x 2 cells x 20 seeds = 2,800 runs, about 4-5 hours. Training: about 4 hours at 15 environments. Evaluation: about 15 controllers x 2 primary cells x 20 seeds and 8 x 8 x 20, about 1,900 runs, about 3 hours. Pre-run checks: under 1 hour. About 12 hours of compute. [A5] CPU guard: 90 %, the default, unless the author sets another limit.

## Disclosures

- All evidence before this run (V359, V361, V368) ran on P0, with its hidden braking, the instant tau rise and the 1-s taper. Only those best cells are repeated on the fixed plant; every other phase 1-3 result stays on P0.
- This run is chosen after those results, on the cell where DRL already looked best. V361's rule did not hold on fresh seeds (V368).
- P0d's look-ahead and braking limit were chosen after an earlier check failed on undertakes, and P0d's own check failed that item narrowly at 5,300 (V375); the author counted it as met (V376). `lcAssertive` 1.4 and the smooth rule were chosen before the fix and are not validated against real traffic.
- P0d's gates were on r1m3; r2m3 was report-only. There, at 5,300, lane-end stops are 608.5 per run at ramp 2 against 7 at ramp 1 under no control.
- The own-state family was derived from policies trained on P0. The reward and action design were shaped by exploratory runs that knew p333.
- V2V and roadside speeds are ideal, with no latency or loss. Humans do not adapt to ALKS. 50 % ALKS. Fleet placeholders: the human tau shape, the ALKS gap above 60 km/h, the speed-factor bounds.
- Undertakes are not zero.
- No capacity drop is established. r2m3's merges are 1.2 km apart; other spacings are untested.
- This protocol had an independent review with skeptics (V377); its findings, accepted and declined, are in `confirmatory_3_review.md`. All exploratory runs are in `docs/decisions.md`, including failed ones.

## What this cannot show

It says nothing about other actions, other networks, other spacings or real traffic. 4 of 5 is a statement about these trained policies, not the method in general. A rule outside these families could still match DRL. TTC below 3 s is a surrogate, and this model is not calibrated, so a win is not a safety result for real traffic. Only 2 conditions decide the claim.
