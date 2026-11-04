# Confirmatory 2: DRL against simple rules on clean plants

Status: draft for the author's approval (V356). Nothing here has run. Exploratory evidence: V305-V355.

## Question

On clean plants, does per-CAV DRL beat simple rules, on steady traffic and under perturbations?

## Plants

Both with the settings of `docs/research/baseline_v1/plant_p0.json`, frozen before any result on these seeds:

- r1m3 P0
- r2m3: second on-ramp, not tuned separately (V354, V355)

## Controllers

| Name | What it does | Tuning |
|---|---|---|
| No control | ALKS at 1.6 s | none |
| p333 | 0.8 s behind another ALKS | fixed |
| Adaptive rule | 0.8 s, or 1.2 s when mean speed in the next 1,000 m is below 10 m/s | fixed at `lr1000_10` (V351), not retuned |
| Per-CAV DRL | One shared policy, 4 headway levels | see below |

All controllers that act use the 10-s clock, so the clock is not a difference between them.

## DRL training

- PPO as in V334: gamma 0.933, lambda 0.967, safety weight 10, flow weight 0.4, reward references from each plant's no-control runs.
- One policy set per plant: 3 learners x 3 environments, 250 updates. Final policies only, no selection.
- The speed action is dropped: V339 shows it was declined.
- Each training episode draws at random: no perturbation (one third), or a tapered slowdown with edge 3, 4 or 5, limit 25 to 60 km/h, 60 to 180 s, starting between 400 and 1,200 s. Levels 4,090, 4,600, 5,300.
- Rules get no equivalent training: they are fixed, which favours DRL's exposure. This is disclosed, and it is why the rule's parameters stay untouched.

## Conditions at evaluation

| Code | Condition | DRL saw it in training? |
|---|---|---|
| S | Steady | yes |
| X1 | Tapered slowdown, edge 4, 25 km/h, 120 s, at 600 and 1,200 s | yes (family) |
| X2 | Tapered slowdown, edge 3, 30 km/h, 180 s, at 700 s | yes (family), this draw held out |
| H1 | Slow truck, cap 50 km/h, every 300 s | no |
| H2 | Ramp bursts, 120-s grid | no |

Levels 4,600 and 5,300. That makes 2 plants x 5 conditions x 2 levels = 20 cells.

## Seeds, for the author's approval

- Evaluation: 7,440,100-7,440,119, 20 paired seeds per cell, used once.
- Training: 7,441,000-7,444,999, new for this run.
- Reserved: 7,440,120-7,440,999.

## Metrics

Primary, reported together: door-to-door delay and served flow. Side constraints: network TTC below 3 s, network braking at 3 m/s² and harder, collisions. Also reported: ramp delay, fuel, jerk, braking at 4.5 and 7 m/s², lane-end stops. Median of paired differences, percentile bootstrap.

## Claim rules, fixed before data

CIs are Bonferroni-corrected over the 20 cells (99.75 %). The 95 % CIs are also reported, for the map only.

**Opponent in each cell:** the better of p333 and the adaptive rule by median delay on these seeds.

**DRL wins a cell on delay** if at least 2 of 3 policies have, against the opponent: delay at least 5 % better, corrected CI excluding 0; flow at most 0.5 % worse; network TTC and braking at most 10 % worse; collisions at most the opponent's plus 1.

**DRL wins a cell on safety** if at least 2 of 3 policies have: network TTC at least 30 % better, corrected CI excluding 0, and at least 20 per run lower; delay at most 2 % worse; flow at most 0.5 % worse; braking at most 5 % worse; collisions at most the opponent's plus 1.

**Sentences allowed:**

| Outcome | Sentence |
|---|---|
| No cell won | Per-CAV DRL, with this budget and these actions, was not shown to beat simple rules on these clean plants |
| Some cells won | DRL has a conditional advantage in the listed cells; everywhere else as the map shows |
| Won only under H1, H2 | The advantage is under perturbations it never saw |

**The adaptive rule's claim, separately:** the same safety rule against p333 under X1 and X2, in the 8 cells, Bonferroni over 8. Delay at most 5 % worse here, as in V346.

No "first" or "novel" wording. All controllers are always reported, per cell, as an operating map.

## Stop rules

- A failed smoke check stops the run.
- A bug found after results: fix, re-run everything affected, log both.
- No tuning of plant, rule, reward or budget after any evaluation row is read.
- Results that surprise are traced before they are reported.

## Checks before the run

1. Smoke in training mode: randomised perturbations reach SUMO; per-vehicle reward varies; default rows still reproduce.
2. Adaptive rule on r2m3: its road order includes edge 4a and ramp 2; fires near a slowdown and not without one.
3. Two collisions on the r2m3 ladder (V355) are traced first. If they show a new artefact, it comes back to the author before training.

## Compute

Training about 1.5 hours per plant; evaluation 6 controller rows (3 policies) x 20 cells x 20 seeds = 2,400 runs. About 6 hours in all overnight at CPU 30 %.

## Disclosures

- P0 is our tuning: `lcAssertive` 1.4 and our smooth no-undertaking rule for ALKS; SUMO's lane-change behaviour at that setting is not validated against real traffic.
- P0 was chosen on seeds 7,419,623-639 and checked on 640-649.
- The reward and action design were shaped by exploratory runs that knew p333, and the adaptive rule was chosen after seeing step A.
- r2m3's merges are 1.2 km apart; a longer spacing is untested.
- No capacity drop is established on these plants (V244, V271, V322).
- All exploratory runs are in `docs/decisions.md` V263-V355, including failed ones and the reward bug of V294.
- The usual adversarial review of this protocol was skipped: the author chose not to spend the tokens this week (V356).

## What this cannot show

It says nothing about DRL with other actions, much larger budgets, other networks, or real traffic. A tie here does not show DRL can't help elsewhere.
