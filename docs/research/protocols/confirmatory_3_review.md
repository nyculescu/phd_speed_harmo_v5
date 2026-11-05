# Review of confirmatory 3, revision 1

Run 2026-11-04 (V377): 5 independent reviewers, a skeptic for each, then a final critic. 11 agents, about 2.5 million tokens. Scripts and traces: `/home/catalin/work/phd/v5b1_runs/phase3/scratch/review3/`; the 4 simulation traces are in `docs/research/p0_trace/review3/`. Power figures are plug-in estimates from P0 rows; the traces are one seed on P0d.

## Findings

| Verdict | Severity | Dimension | Finding | Outcome |
|---|---|---|---|---|
| confirmed | blocker | integrity-history | The hidden-braking check has never run under a controller or a perturbation, and check 1 cannot measure it as written | adopted in revision 2 |
| confirmed | major | code-feasibility | Training settings are not pinned, and the defaults and only template silently run a different experiment | adopted in revision 2 |
| confirmed | major | code-feasibility | Check 1 cannot be computed in training mode, and step braking is unmeasured in the two cells that decide the claim | adopted in revision 2 |
| confirmed | major | code-feasibility | Adaptive on 4a does not exist, and the obvious config silently runs r4a1 six times | adopted in revision 2 |
| confirmed | major | code-feasibility | The copy rule has no tracer in the repo and no fixed definition, and a fractional level would be silently floored | adopted in revision 2 |
| confirmed | major | code-feasibility | Selection and claim rules leave choices open that the script must make, and decide.py cannot be reused | adopted in revision 2 |
| confirmed | major | integrity-history | A noisy 2 % filter and the p333 fallback can decide the claim, and may leave no rule form but p333 | adopted in revision 2 |
| confirmed | major | integrity-history | The deciding count tracks lane-end stops at ramp 2, and it has not been traced on P0d | counters by road and speed; the lane-end reading dropped |
| confirmed | major | integrity-history | 'Safety advantage' overstates what the run can show, and the outcome table has gaps | adopted in revision 2 |
| confirmed | major | integrity-history | The plant check gated r1m3 only; r2m3, the plant of the claim, was report-only and has no comparator | adopted in revision 2 |
| confirmed | major | integrity-history | No commitment on what a loss means, and the freeze starts too late | A3 |
| confirmed | major | integrity-history | No convergence check and no branch for a failed learner | adopted in revision 2 |
| confirmed | major | integrity-history | T0-T3 criteria are absent or too weak, and there is no early kill | adopted in revision 2 |
| confirmed | major | integrity-history | The delay win uses a TTC-chosen opponent, is uncorrected and has no sentence | adopted in revision 2 |
| confirmed | major | integrity-history | 'Unchanged' is inaccurate, and the gates' statistics are not defined | adopted in revision 2 |
| confirmed | major | integrity-history | Reward references name the wrong plant, and check 1 would not catch a P0c training environment | adopted in revision 2 |
| confirmed | major | opponents-fairness | The delay win is scored against a rule chosen for TTC, and it yields a 'safety advantage' sentence | adopted in revision 2 |
| confirmed | major | opponents-fairness | One opponent picked on 20 seeds: the 2 % gate is below the noise, so tuning-seed luck can decide the cell | adopted in revision 2 |
| confirmed | major | opponents-fairness | Rules that reach DRL's TTC at a modest delay cost never reach evaluation, so 'safety advantage' can overstate the result | adopted in revision 2 |
| confirmed | major | opponents-fairness | No rule family can express what the policies do; the copy rule is a strawman | own-state family added; tree copies not built |
| confirmed | major | opponents-fairness | The 30 % bar against a tuned opponent is close to unreachable, and 'None won' merges 'a rule matches' with 'a smaller edge' | A2, tuned reading at 10 % and replication at 30 % |
| confirmed | major | opponents-fairness | The rule with the same information as DRL has no selection rule, no outcome row and no adaptation gain | adopted in revision 2 |
| confirmed | major | plant-artefacts | The V2V fallback from 0.8 to 1.6 s is a second V367: full 9 m/s² braking in every 0.8-s arm, hidden from 1-Hz samples | A1 |
| confirmed | major | plant-artefacts | Network TTC below 3 s mostly counts controlled approaches to a slow queue, and headway alone moves a large part of it | adopted in revision 2 |
| confirmed | major | plant-artefacts | The P0d check does not cover the conditions the primary cells depend on | adopted in revision 2 |
| confirmed | major | stats-claims | The 30 % margin against a tuned opponent makes 'None won' the likely outcome even if DRL keeps its whole edge over p333 | A2 |
| confirmed | major | stats-claims | The delay win is tested against a rule chosen for low TTC, so it can fire while DRL only ties p333, and no sentence exists for it | adopted in revision 2 |
| confirmed | major | stats-claims | 'Safety advantage' overclaims a surrogate count, and the no-control contrast is pre-written from another plant | adopted in revision 2 |
| confirmed | major | stats-claims | The sentence claims 'the tuned rule forms tested', but only one noisily chosen rule per cell reaches evaluation | adopted in revision 2 |
| confirmed | major | stats-claims | The safety win's delay limit is relative to an opponent never re-checked on evaluation seeds, so DRL can be far slower than p333 | adopted in revision 2 |
| confirmed | major | stats-claims | The decision statistic is not written down, and the choice flips a quarter of stored pairs at the threshold | adopted in revision 2 |
| confirmed | minor | code-feasibility | The run order and required parts are not stated, and the stated reference plant is the wrong one | adopted in revision 2 |
| confirmed | minor | code-feasibility | Check 3 would not catch a wrong clock or a mislabelled rule | adopted in revision 2 |
| confirmed | minor | code-feasibility | The r1m3 reproduction check would pass even if _x were wrong | adopted in revision 2 |
| confirmed | minor | code-feasibility | The rows hold every claim metric, but some names mislead, and TTT is missing from the protocol | adopted in revision 2 |
| confirmed | minor | code-feasibility | The compute estimate is low by about 1 to 2 hours, and its one measurement has no controller in it | adopted in revision 2 |
| confirmed | minor | code-feasibility | One failed run wastes the rest of a batch, and a re-run silently keeps old rows | adopted in revision 2 |
| confirmed | minor | code-feasibility | The 0-collision entry filter can remove good rules by chance and is stricter than DRL's own gate | adopted in revision 2 |
| confirmed | minor | code-feasibility | Learners reuse earlier network seeds, and the binding convergence check is missing | adopted in revision 2 |
| confirmed | minor | code-feasibility | The disclosures read as if P0d passed its check on the plant being used, but r2m3 was report-only | adopted in revision 2 |
| confirmed | minor | integrity-history | The protocol never says all earlier evidence ran on P0, and it pins P0 numbers to the result | adopted in revision 2 |
| confirmed | minor | integrity-history | After the plant bug only the best cells are re-run; every other result stays on P0 and the protocol does not say so | adopted in revision 2 |
| confirmed | minor | integrity-history | TTT is missing and delay leaves out unfinished vehicles, against the binding metric rule | adopted in revision 2 |
| confirmed | minor | integrity-history | Line 32 and line 82 are not true for most of the map, and the evaluation roster is undefined | adopted in revision 2 |
| confirmed | minor | integrity-history | Pre-run check seeds are unnamed, the seed offset is unstated, and PPO seeds are reused | A6 |
| confirmed | minor | integrity-history | Copy rule and single rule are undefined, and '52 rules' double counts | adopted in revision 2 |
| confirmed | minor | integrity-history | Disclosures in the previous protocol or needed now are missing | adopted in revision 2 |
| confirmed | minor | integrity-history | Items Claude settled that the author has not explicitly decided | asked |
| confirmed | minor | opponents-fairness | No informed oracle on this plant; the 'knows the condition' wording is not true of any rule; the dropped MPC is not disclosed | text only; oracle row not run, disclosed |
| confirmed | minor | opponents-fairness | S, H1 and H2 compare DRL only with untuned p333, and the text contradicts itself | adopted in revision 2 |
| confirmed | minor | opponents-fairness | '0 collisions' discards rules on a known entry artefact while DRL gets a tolerance of 1 | adopted in revision 2 |
| confirmed | minor | opponents-fairness | Check 3 would not catch a family that silently runs as another; two small protocol gaps | adopted in revision 2 |
| confirmed | minor | plant-artefacts | Most of the primary count is not during the slowdown, so 'under these slowdowns' misdescribes what is measured | adopted in revision 2 |
| confirmed | minor | plant-artefacts | The full-emergency count is largely lane-end creep at 0.4 m/s, and its noise exceeds the claim rule's margin of 5 | adopted in revision 2 |
| confirmed | minor | plant-artefacts | Smoke check 1's '1-Hz braking within 5 % of step' either stops the run or tests nothing, depending on an unstated condition | adopted in revision 2 |
| confirmed | minor | plant-artefacts | The taper steps the limit about 1 m/s once per second, producing a clocked -4.5 m/s² pattern that 1-Hz samples miss | A1 |
| confirmed | minor | plant-artefacts | TTT is not in the protocol's metrics, though CLAUDE.md requires it, and delay is a mean over finishers | adopted in revision 2 |
| confirmed | minor | stats-claims | Delay and flow limits sit below one noise SD, so a perfect tie caps the rule at about 50-60 % whatever the TTC effect | not widened: skeptic showed it buys little and leaks |
| confirmed | minor | stats-claims | Every null and power figure, including mine, is from P0; no row exists under X1 or X2 on P0d, so V244 is unmet for the actual plant | adopted in revision 2 |
| confirmed | minor | stats-claims | The point estimate carries the margin; the CI and its Bonferroni level hardly affect the safety decision | adopted in revision 2 |
| confirmed | minor | stats-claims | 4 of 5 policies supports a statement about these trained policies, not about the method, and the policies are not independent | adopted in revision 2 |
| confirmed | minor | stats-claims | TTT is absent from the metrics although CLAUDE.md binds it, and delay overstates the gain because it leaves out unfinished vehicles | adopted in revision 2 |
| confirmed | minor | stats-claims | The single rule's criterion is undefined, and the 0-collision gate removes rules by chance | adopted in revision 2 |
| confirmed | minor | stats-claims | Reward references are written as P0c, a plant the protocol does not run on | adopted in revision 2 |
| not confirmed | none | opponents-fairness | The position family comes from one P0 seed in X1; X2 has no targeted rule and P0d was never traced | declined: not confirmed by the skeptic |

## From the final critic, not separately verified

| Severity | Finding | Outcome |
|---|---|---|
| major | Verdict on 'ttt-and-censored-delay' looks too low: counting unfinished vehicles flips the 2 % gate that picks the opponent | adopted: delay limit reads all-vehicle delay |
| major | The deciding threshold TTC < 3 s has no source, was chosen for training, and is the policies' own reward term; the severe tail is not recorded | disclosed; companions logged; "safety" gated |
| major | The rule forms use the one longer level that the 2 % gate tends to reject, so the strongest hybrid is never offered | adopted: 1.0 s variants added |
| major | The code that decides the claim does not exist yet, and neither the protocol nor the plan reviews it before the run | A4 |
| major | An expected win is never traced, and no rule says what a bad trace does to the sentence | adopted, without the 50 % rule |
| minor | The historical 'never clearly worse elsewhere' rule was dropped without a record, and 'elsewhere as the map shows' can hide harm | adopted: harm cells listed in every sentence |
| minor | A safety sentence rests on perfect V2V and perfect roadside speeds, undisclosed and untested, though an outage perturbation exists | disclosed; outage cell not added |
| minor | The evaluation action is not stated: training samples, evaluation takes the argmax, and all convergence evidence is on the sampled policy | adopted; greedy checkpoints replaced by the u250 comparison |
| minor | Nothing ties the run's code to the frozen r2m3 plant; check 2 only tests r1m3 | adopted |
| minor | Braking at 4.5 and 7 m/s² fell out of the reported metrics, though the plant was just fixed because of them | adopted |
| minor | The pre-registration does not identify the approved text, and two statements in it are not yet true | adopted |

## Full text

`confirmatory_3_review.json.gz`: every finding with its evidence, proposed change and the skeptic's reason.
