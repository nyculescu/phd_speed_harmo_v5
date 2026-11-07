# Round 2 pre-registration: four candidates trained while round 1 evaluates

Status: approved 2026-11-06 (V439), written before any round-1 validation or test result exists. Seeds approved: DRL training option A, 3E tuning 7,440,700–7,440,739.

## Why now

The author's request (2026-11-06): use the idle CPUs of the rented machine (V437) for the options from the nine-agent memo (`docs/reports/2026-11-05_21-29/`) not built in round 1. The author picked 2B, 1B, 1D and 3E.

## Candidates

The three DRL candidates each make one change to v3w's recipe, round 1's control. Everything else is as in round 1:
- plant r2m3;
- training levels 4,500–6,000 by 250;
- 5 learners × 3 envs, 500 updates;
- gamma 0.933, lambda 0.967, net seed 20261205;
- TensorBoard-only logging;
- the `tbcheck1.py` training checks.

Each candidate compares one-to-one against v3w.

| Candidate | Change | Memo finding | Design |
|---|---|---|---|
| 2B | learning rate and entropy coefficient decay linearly over the 500 updates; one critic scale for all learners: the median of v3w's five learner scales | F2: training stops improving early, then drifts toward close-following | `source/p2b.md` |
| 1B | gate mask: where the action cannot change anything, the level is held and the decision leaves the policy loss | F3: about half the decisions cannot act yet train the policy | `source/p1b.md` |
| 1D | the safety charge reads hard braking at every 0.1-s SUMO step instead of the 1-Hz sample | V367: 1-Hz metrics miss 9 m/s² ALKS braking | `source/p1d.md` |
| 3E | CMA-ES tunes a per-zone own-state rule (not DRL): the strongest non-learning opponent | memo: "before any thesis claim" | `source/p3e.md` |

Exact settings follow the design files. Where a design leaves a value open, the implementation states it, and it is fixed here before training starts.

## Seeds (for approval)

- **DRL training, option A (recommended):** the same training seeds as round 1, 7,464,000–7,471,799. These are the seeds v3w trained on, so each candidate differs from the control only by its change. They are training seeds, not evaluation seeds.
- DRL training, option B: fresh seeds 7,471,800–7,479,599, in the same layout as round 1.
- **3E tuning:** 7,440,700–7,440,739, fresh.
- Smoke runs use the existing smoke seed 7,419,899.

## Evaluation

Training curves are not results. The candidates are judged in round 2:
- on fresh validation and test seeds;
- under a round-2 protocol written before any round-2 candidate's validation result is read;
- with the round-1 finalists and the tuned rules (3E among them) alongside.

## Machine

These run on the rented machine of V437. Its rows and training fingerprint equal the laptop's, so the machine cannot change results.
