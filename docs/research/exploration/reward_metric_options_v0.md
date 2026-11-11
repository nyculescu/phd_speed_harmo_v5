# Several rewards and starred measures in parallel: how to do it honestly (v0)

2026-11-10. Desk work only. Nothing was run. The stored-row numbers are the exploratory ones of `drl_aim_plans_v0.md` and `drl_win_directions_v1.md`; they support no claim.

**Names used.** "The policy" is the trained controller. "The fixed rule" sets every automated car to a 0.8-second gap. "The searched rule" is the best rule found by machine search. An "approach" is one fixed triple: a reward, the one measure it is judged on, and a rule tuned for that same measure.

## Short answer

Running several approaches side by side is fine if the list is fixed first and every approach is reported, win or lose. It becomes metric shopping when the star is picked after the results are seen. The safe form is a funnel: a cheap rules-only check per measure, then at most two trained approaches, then one confirmation on fresh seeds. Three approaches at full size at once would cost about $30 to $45, near the whole weekly ceiling.

## How to avoid metric shopping

1. **Fix the list before any data.** Write each approach as a triple: reward, starred measure, opponent rule tuned on that measure. Three at most.
2. **Judge each policy only on its own star.** A policy trained for recovery is not also searched for a win on fuel. Readings on the other measures are shown, marked as not tested.
3. **Give the rules the same goal.** For each starred measure, one machine search of rules with that measure as its goal, on the same conditions the policy trains on.
4. **Keep one check that nobody was tuned on.** It must not get worse. Fuel per km and the number of jams are the natural ones.
5. **Separate choosing from proving.** Choose on one set of seeds, prove on another. The stored rows may only suggest.
6. **Report every approach,** with the count of approaches tried beside the count of cells tested. A loss is a row in the thesis, not a deleted run.
7. **Fix the event first.** The perturbation is set before any controller runs on it, and the tests against a simulator quirk are named in advance.

## Multiplicity: three ways, from strict to cheap

- **All approaches are claims at once.** Then they share the 5 % error. With three approaches each interval is read at 98.3 % in place of 95 %. To keep the same power this needs about 1.5 times the seeds. With two cells as well it is six tests, 99.2 %, about 1.8 times the seeds.
- **A fixed order.** The approaches are ranked before data. The first is tested at 95 %. The second is tested only if the first wins, and so on. No widening, but a loss at the top closes the rest as claims.
- **Choose, then confirm (recommended).** All approaches run on choosing seeds, with no claim. The best one alone goes to fresh seeds for one test at 95 % per cell. The others stay as reported rows. The number tried is disclosed. This is how the project already picks checkpoints.

One more caution. Each new reward is a new training recipe, and one recipe change already moved delay by about 3 % in the records without a known cause. So a difference between two rewards smaller than about 3 % cannot be credited to the reward.

## Which pairs are most worth it

| Approach | Reward change | Starred measure | What the stored rows say | Verdict |
|---|---|---|---|---|
| A. Recovery | none at first; training on a family of events | the extra delay an event causes, against the same day without it | the only hint: the truck cost about 31,500 vehicle-seconds under the policy and 33,200 to 33,600 under four of the best rules | first; it waits for the approved told-in-advance test |
| B. Reliability | weigh bad outcomes more than average ones | delay on the worst tenth of days, and the slowest 5 % of trips | a tie: +1.4 % [−1.3, +3.3] against the fixed rule | second; needs a trip log |
| C. Close-following without its costs | add a charge for hard braking read ten times a second | seconds with a short time to collision, with delay not worse | the strongest edge on record, +11.8 % [+5.0, +19.7] over the searched rule; but the policy is worse on hard-braking events (−5.7 %) and on the number of jams (−8.6 %) | the bonus measure; it fails the independent check today, so the reward must cure that first |
| Jam waves | charge for stop-and-go | share of road and time in a jam | the searched rule already matches the policy (−0.6 %) | not worth a training |
| Fuel | charge for fuel | fuel per km | all controllers within 0.2 % | no room |

Why these three: A has the only hint on a measure that is not delay. B is the easiest to defend on a real road. C is where the evidence is strongest, and its weakness is known and may be curable by the reward. A charge of that kind was tried once and was not shown to help on 40 seeds, which is too few to see a small effect.

## Cost of each (rough)

| Approach | Rule search | Training | Evaluation | Build | Total |
|---|---|---|---|---|---|
| A. Recovery | about 81,000 runs, $9 | $1.5 to $3 | about 23,000 runs, $2 to $8 | 20 to 30 h | $13 to $20 |
| B. Reliability | about 41,000 runs, $5 | $1.5 to $3 | about 11,500 runs, $1 to $4 | 20 to 25 h | $8 to $12 |
| C. Close-following without its costs | about 41,000 to 81,000 runs, $5 to $9 | $1.5 to $3 | about 6,700 runs, $1 to $2.5 | 10 to 15 h | $7 to $14 |

- All three at full size: about $28 to $46 and 50 to 70 build hours. That is at or above the $40 per 7 days, so it would have to be spread over two weeks.
- Savings if they share one new event and one evaluation: the evaluation is paid once, about $3 to $8 less. The three rule searches cannot be shared, because each has its own goal.
- The funnel's first stage, a rules-only check per measure: a few hundred runs each, under $1 in all.

## Recommendation

Do not launch three trainings at once. Use the funnel.

1. **Wait for the two approved rules-only steps.** The check of the second on-ramp may change the model. The told-in-advance test says whether recovery has any room.
2. **Run the same kind of cheap check for B and C** on new events fixed beforehand: can a rule tuned for the bad day beat the fixed rule on the bad day; does the searched rule's close-following result come with the same braking cost.
3. **Train at most two approaches,** the ones whose check showed room, with the list, stars, opponents and independent check written down first.
4. **Confirm one on fresh seeds** by "choose, then confirm". Star only that one in the thesis, and print the others in the same table with their outcomes.

If you prefer true parallel running, keep it to these three triples, register them together, and read them at 98.3 % with about 480 days per test. My estimate, as judgement only: the chance that at least one of the three gives a fair win is about 30 %.

## References

- Aim and honesty rules: ledger V504. Approved rules-only steps: V505-V508 (`docs/research/protocols/v505_*.md`).
- Stored-row numbers: `drl_aim_plans_v0.md`; `drl_win_directions_v1.md` §1.3; `docs/research/baseline_v5/readings/read6_v23_supplement.json`.
- Rules tuned on the same goal: `docs/research/protocols/planb.md` §3.3. Interval levels for several tests: planb.md §8 (lines 424-430).
- Recipe change moving delay by about 3 %: `round_1_result.md:246-251`; V429. The braking charge tried once: round 2 candidate 1D, `round_2_result.md` §3.
- Cells and approaches counted: `cells_tested.md`; planb.md:145.
- Rates and costs: V450, V475, V490, V493.
