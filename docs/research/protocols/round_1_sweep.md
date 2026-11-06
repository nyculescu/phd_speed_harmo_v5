# Round 1, step 0: demand sweep to set the training range

Status: draft for the author's approval (V416). The author decided that round 1's policies train over a bigger demand range, and that the range is set after a sweep test. Nothing runs before the author approves this text and its seeds.

## Question

Over which constant demand levels does control matter on this plant, and up to which level does the plant still serve its demand? The answer sets the lower and upper ends of the training range.

## Design, kept simple (V408)

- **Plant:** baseline-v3's `plant_c3.json` on r2m3, unchanged.
- **Condition:** training conditions, the random slowdowns of `env.json` (two in three episodes have one), the same draw per seed for every arm.
- **Levels:** constant demand per run, from 2,500 to 7,500 veh/h in steps of 250 (21 levels).
- **Arms:**
  - no control, p333 (0.8 s everywhere) and os1_15_10 (the best tuned rule in X2);
  - baseline-v3's five final policies, which show where today's training range leaves gaps.
- **Seeds:** 10 fresh seeds, the same for every arm (paired).
- **Runs:** 8 arms × 21 levels × 10 seeds = 1,680, about 1.2 h on 32 workers. Without the policies: 630 runs, about 0.5 h.

## Measures, per level and arm

- all-vehicle delay and close-following (TTC below 3 s, read once a second), as in confirmatory 3;
- the served ratio: vehicles entering road 4 (past both merges) over the demand in the 1,500-s window;
- teleports and collisions.

## Range rule, fixed before data

- **Lower end L:** the lowest level at which p333 or os1_15_10 differs from no control by at least 10 % in delay or in close-following, with the 95 % CI excluding 0. The statistic is the protocol's paired median difference, with a percentile bootstrap of 20,000 resamples. Below L the tested controllers do not change the traffic.
- **Upper end U:** the highest level at which:
  - every arm has 0 teleports in all 10 runs;
  - every arm has at most 2 collisions in total over the 10 runs;
  - the best arm's median served ratio is at least 0.90.

  Above U, at least a tenth of the demand stays queued whatever these controllers do, or the plant is no longer clean.
- If L > U, the rule gives no range and the result goes to the author.
- **The policies' rows do not enter L or U.** They are reported per level, against no control and the rules, so the author can see where baseline-v3 is worse.

## What the sweep does not decide

These go into round 1's protocol, revision 2, after the sweep and with the author:
- how many training levels inside [L, U], and how environments cover them;
- whether evaluation adds demand levels besides 5,300;
- whether a control arm trains baseline-v3's own recipe over the new range.

The reward references (no-control braking, close-following and vehicles per second at each training level) and 2C's d_ref are computed at the chosen levels, on separate seeds, in round 1's stage 0.

## Seeds, proposed

7,440,600-609, in the block approved in V354, unused (the ledger and code use up to 7,440,239, and round 1's draft proposes 300-539).

## Report

HTML in `docs/reports/<timestamp>/`, with three parts:
- per level: delay, close-following and served ratio for every arm;
- the effects against no control with CIs;
- L and U with the rule's reasons.

Numbers are in words ("fewer" and "less" mean the controller is better). All of it is exploratory, except the range rule, which is fixed here.
