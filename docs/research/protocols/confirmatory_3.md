# Confirmatory 3: DRL's safety edge against several rule forms on P0c

Status: draft for the author's approval (V369). Nothing here has run. It starts only after the author accepts a fixed plant (V371, V372). Exploratory evidence: V359, V361, V368.

## Question

Under a sustained slowdown on r2m3, does per-CAV DRL keep its safety edge when the plant is fixed and the opponents are the best of several rule forms, tuned on separate seeds?

## Plant

r2m3 with the fixed plant the author accepts after V371, frozen before any result on these seeds. Not tuned for this study.

## Controllers

No control is reported in every table and is not an opponent.

Rule families, all on the 10-s clock:

| Family | Members | Count |
|---|---|---|
| Uniform headway | 1.6, 1.2, 1.0, 0.8 s | 4 |
| By zone | all patterns of 1.2 or 0.8 s over the 5 zones (V354) | 32 |
| On road 4a | 1.6, 1.2, 1.0 s on 4a, 0.8 s elsewhere | 3 |
| Local adaptive | 0.8 s, or 1.2 s when mean speed in the next 400 or 1,000 m is below 10, 13 or 16 m/s | 6 |
| Adaptive on 4a | the local rule, plus 1.2 s on 4a | 6 |
| Copy of the policies | mean level per road, traced from the trained policies on the tracing seeds | 1 |

DRL: per-CAV, as in V334, without the speed action: gamma 0.933, lambda 0.967, safety weight 10, flow weight 0.4. Reward references come from P0c's no-control runs on the tuning seeds. 5 learners x 3 environments, 500 updates, the binding budget in `CLAUDE.md`. Final policies only, no selection. Training draws perturbations as in V358.

## Fairness to the rules

The opponent is chosen for each cell separately on tuning seeds, so a rule knows the condition and the level in advance, which DRL does not. This favours the rules and is deliberate.

In each cell, the opponent is the rule with the lowest network TTC among those with delay at most 2 % worse than p333 and 0 collisions on the tuning seeds. If none qualifies, the opponent is p333.

One single rule chosen across all cells is reported too.

## Conditions and levels

| Code | Condition | Role |
|---|---|---|
| X1 | Tapered slowdown, edge 4, 25 km/h, 120 s, at 600 and 1,200 s | primary at 5,300; map at 4,600 |
| X2 | Tapered slowdown, edge 3, 30 km/h, 180 s, at 700 s | primary at 5,300; map at 4,600 |
| S | Steady | map |
| H1 | Slow truck, cap 50 km/h, every 300 s | map |
| H2 | Ramp bursts, 120-s grid | map |

That makes 2 primary cells and 8 map cells.

## Seeds, for the author's approval

| Use | Range |
|---|---|
| Rule tuning and reward references | 7,440,160-179, 20 seeds |
| Tracing the policies for the copy rule | 7,440,180-189 |
| Evaluation, used once | 7,440,200-219, 20 paired seeds per cell |
| Training | 7,456,000-7,463,999, new |
| Reserved | 7,440,220-999 |

## Metrics

Primary, reported together: door-to-door delay and served flow. Side constraints: network TTC below 3 s; braking at 3 m/s² and harder, counted every 0.1 s; ALKS full-emergency events; collisions. Also reported: ramp delays, fuel and jerk counted every 0.1 s, undertakes, lane-end stops, TTC at the half second. Median of paired differences, percentile bootstrap.

## Claim rules, fixed before data

CIs are Bonferroni-corrected over the 2 primary cells (97.5 %). The map uses 95 % and supports no claim.

**DRL wins a primary cell on safety** if at least 4 of 5 policies have, against the cell's opponent: network TTC at least 30 % better, corrected CI excluding 0, and at least 20 per run lower; delay at most 2 % worse; flow at most 0.5 % worse; braking at most 5 % worse; full-emergency events at most 5 % more, or at most 5 more per run; collisions at most the opponent's plus 1. These are the numbers of V359, unchanged but for the new braking count.

**DRL wins a primary cell on delay** if at least 4 of 5 policies have: delay at least 5 % better, corrected CI excluding 0; flow at most 0.5 % worse; network TTC and braking at most 10 % worse; collisions at most the opponent's plus 1.

**Sentences allowed:**

| Outcome | Sentence |
|---|---|
| Both primary cells won | On this plant, per-CAV DRL has a safety advantage over the tuned rule forms tested under these slowdowns at 5,300; elsewhere as the map shows |
| One primary cell won | The same, for the listed cell only |
| None won | With this budget and these actions, the edge seen in V359 and V368 was not confirmed against tuned rules on the fixed plant |

Whatever the outcome, the comparison with no control is stated next to it: in V359 and V368 no control had the lowest or an equal TTC under these slowdowns, at much higher delay.

No "first" or "novel" wording. All controllers are reported per cell as an operating map.

## Stop rules

- A failed smoke check stops the run.
- A bug found after results: fix, re-run everything affected, log both.
- No tuning of plant, rules, reward or budget after any evaluation row is read.
- Results that surprise are traced before they are reported.

## Checks before the run

1. Smoke in training mode: the eased cap and randomised perturbations reach SUMO; per-vehicle reward varies; 1-Hz braking stays within 5 % of step braking.
2. `_x` and the zone offsets use r2m3's real lengths, and the position input no longer clips before the road ends. Only r2m3 changes; r1m3 rows still reproduce.
3. Every rule family runs on r2m3 and reaches SUMO.

## Compute

Rule tuning: about 52 rules x 10 cells x 20 seeds, about 10,400 runs. At about 1 minute per run on 24 workers, about 7 hours. If that is too long, tuning runs only X1 and X2 at 5,300 first, about 2,100 runs and 1.5 hours, and the other cells use the same rule; this is the plan unless the author asks for all cells.

Training: about 4 hours at 15 environments. Evaluation: about 7 controllers x 10 cells x 20 seeds = 1,400 runs, about 1 hour. About 7 hours in all, CPU guard at the author's limit.

## Disclosures

- This run is chosen after V359, V361 and V368, on the cell where DRL already looked best.
- P0c's fix was found by this project's review and its check is exploratory in tone, on 10 seeds. P0c keeps `lcAssertive` 1.4 and the smooth rule, chosen before the fix and not validated against real traffic.
- The reward and action design were shaped by exploratory runs that knew p333.
- r2m3's merges are 1.2 km apart; other spacings are untested.
- No capacity drop is established on these plants.
- All exploratory runs are in `docs/decisions.md`, including failed ones.

## What this cannot show

It says nothing about other actions, other networks, other spacings or real traffic. A rule outside these families could still match DRL. Only 2 conditions decide the claim.
