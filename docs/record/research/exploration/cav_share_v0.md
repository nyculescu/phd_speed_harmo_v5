# Share of automated cars: train per share, or test on a random share? (v0)

2026-11-10. Desk work only. Nothing was run and no script was needed: the stored rows of the present model hold no run at a share other than 50 %.

**Names used.** "The policy" is the frozen trained controller (v3w). "The fixed rule" sets every automated car to a 0.8-second gap. "Searched rules" are rules found by machine search. "Share" is the percentage of cars that are automated.

## Short answer

1. **Separate policies at 25, 50, 75 and 100 %:** this gives a map of how the delay tie moves with the share. It is unlikely to give the win the thesis aims at. It is the dearer option.
2. **Train at 50 %, test on a random share of 30 to 70 % per run:** this is a cheap robustness row. It can show that the policy does not break when the share differs from the one it was trained on. It cannot show a win over the fixed rule on delay, because that rule has no settings and so cannot be mis-tuned.

## What each would show

**Per-share policies.** Three things change with the share, and they change for every controller:
- The lever. A commanded gap takes effect only when the car ahead is also automated. At 50 % that holds about 56 % of the time (exploratory, stored rows). At 25 % it holds much less often, so every controller loses grip. At 100 % it always holds.
- The road's capacity. At 75 or 100 % the fixed rule shortens almost every gap. The road then carries the present demand with little or no jam (my inference, not measured). With no jam there is nothing left to win.
- The reference "no control". It moves too, because automated cars at their default gap behave differently from human drivers.

So the likely picture is: at 25 % every controller does little; at 50 % the known tie; at 75 and 100 % every short-gap controller reaches free flow at the present demand. A win for DRL would need a share where the lever still bites and the fixed rule is not already enough. Nothing in the records points to one.

**Random share at test time.** It asks one question: does a controller built at 50 % stay good at 30 to 70 %? Published work reports that learned controllers lose performance away from their training share, and that fixed-gain rules also degrade [not read in full; to verify]. The fixed rule here is immune by construction. So the honest expected result is "the policy is not worse than the fixed rule across shares", a tie again, plus a reading of whether its close-following edge holds.

## Is re-tuning the rules needed for a fair test?

- **Per-share policies: yes.** If the policy is trained at each share, every tuned and searched rule must be tuned at each share too. That is the project's equal-exposure rule. The earlier demand sweep showed why: the rules were tuned at one demand level only, and the record itself says this tilted every other level toward DRL.
- **Random share: no, if both sides are frozen from 50 %.** The policy and the rules were both built at 50 % and both meet the same shares. A rule re-tuned per share may be shown beside them as a reference, never as the deciding opponent.

## What the model's verification record says

- The stated intended use is "50 % automated cars". Every run at another share is outside it.
- The Plan B protocol excluded a change of share for that reason: it "leaves the stated 50 %" and "changes every vehicle's draw", so it is a change of the model, not a perturbation.
- The model itself was tuned with only no-control runs at 50 %.
- So each new share needs its own short check before any controller result: no-control behaviour, the bind check of the gap command, collisions, and stops at the end of the ramp lanes. The check of the second on-ramp that is now approved should be finished first, because its outcome may change the model.

## Cells tested and multiplicity

- The count of cells tested stands at 94. Each new share at the present demand adds one cell: three for option 1, one for option 2 (the random share counts as one condition).
- Option 1 read as "does DRL win at any share" is three or four tests of one question. The intervals must be widened for that (for four shares, 98.75 % in place of 95 %). Option 2 is one test.

## What the stored records already say

- Present model: nothing at any share but 50 %.
- An earlier model, before the present one was tuned: at 25 and 80 % share the policies of that time won none of ten cells against the rule of that time, on flow, not on delay. Those policies were trained at 50 % only, and the model and inputs have since changed. It does not carry over.
- The demand sweep on the present model: away from the tuning level the policy looked better on close-following, but the rules had not been re-tuned, so it showed nothing fair.

## Rough cost

| Item | Option 1: four shares | Option 2: random share |
|---|---|---|
| Model checks per share (no control, bind check) | about 600 runs, under $0.30 | about 400 runs (30 % and 70 %), under $0.20 |
| Training | 3 new sets, about $4 to $9 | none |
| Rule tuning | grid about 4,100 runs ($0.5 to $1.5); with a machine search per share about 122,000 runs more ($14) | none |
| Evaluation | about 10,000 runs, $1 to $4 | about 3,400 runs, $0.3 to $1.2 |
| Build | share as a setting, new no-control references for the reward, tests: 8 to 12 h | share drawn per run, the same draw for every controller: 3 to 5 h |
| Total | about $6 to $15 without searches, $20 to $29 with them | about $0.5 to $1.5 |

Dollar figures use the measured rates of the last rentals. Author time comes on top: one decision to amend the intended use, and seeds.

## Recommendation

Do not train per share now. It costs ten to twenty times more than the random-share test, needs every rule re-tuned at every share to be fair, adds three cells, and the likely result is a tie at 50 %, little effect at 25 %, and free flow for everyone above. Keep it as a later map for the thesis, to run only if one of the open checks first shows room for a controller.

Do the random-share test, but as a robustness row inside the next approved study, not as a study of its own. Fix it before any data: both sides frozen from 50 %; the same share draw for every controller on a seed; the reading is "not worse than the fixed rule on delay by more than a stated margin", with close-following beside it; a per-share re-tuned rule only as a reference. It adds one cell and under $2. It answers a question a reader of the thesis will ask, and it is honest about what it cannot show: it is a test of not breaking, not of winning.

## References

- Aim and honesty rules: ledger V504. Approved next steps and the cell count of 94: V505-V508.
- Intended use: `docs/testing/plant_vv_record_v0.md` (section 1; PR-04, PR-10). Share excluded as a model change: `docs/research/protocols/planb.md` (section 5.2 table, "ALKS share or driver mix").
- Gap command binds only behind an automated leader: `b_env.py:774-779`; the 56 % figure: `phase_b_panel/M/final.md` item 12 (exploratory).
- Earlier model at 25 and 80 %: V290, V299, V300. Demand sweep and its caveat: V406, V409, V419.
- Cell counting: `cells_tested.md:5`; planb.md:145, :576.
- Literature on share shifts (not read in full): Vinitsky et al., ACM TCPS 2023, as noted in `phase_a_reports/web_literature.md`.
- Rates: V475, V490, V493; training cost V450.
