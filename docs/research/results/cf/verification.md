# E30 confirmation: verification of the PASS (V531)

Run 2026-11-15, after V530, on stored rows only (no simulation). Four reviewers (statistics and protocol fidelity on Fable 5.2; measure and claim wording on Opus 5.5), each finding re-derived by a skeptic on the other model, then a completeness critic (Opus 5.5; Fable was overloaded). Its jam reading was re-derived by the main session. Scripts and text outputs are in `verify/<role>/`; every finding with its verdict is in `verify/findings.json`.

## Verdict

The PASS reading is correct. Two independent re-implementations of c1_confirm.md §1 reproduce `screen.json` exactly with the protocol's rng (difference about 1e-14), and within resampling noise with other rngs. Run integrity holds: 31 arms × 480 seeds, one commit, one CPU model, the same event draw and the same vehicles on every seed for all arms, `v5b/` equal to 98cac5c, the seeds are fresh, and there is no exposure or holding artefact. No blocker.

The reading is narrower than V530's sentence suggests. The findings below change how it may be worded.

## What the edge is made of (post hoc, descriptive, uncorrected)

| Finding | Figures | Source |
|---|---|---|
| The minimum edge rests on one rule | lr400_16_1 +9.9 % [+6.2, +15.0]; every other arm's lower bound is at least +16.6 % | stats |
| lr400_16_1 is X1's close-following pick, not an untuned rule | lowest TTC within 10 % of p333's delay, from a 70-rule grid in X1 (`baseline_v3/opponents.json`) | claim skeptic |
| Against it the edge is at the two on-ramp merges | merge 1 +10.5 %, merge 2 +11.9 %; away from both merges −8.6 % [−14.7, −1.4] (v3w worse; with a Bonferroni correction over 26 arms the interval includes 0); against grid_lr400_13_1 away from the merges +4.6 % [−2.2, +12.8] | measure, fidelity, both skeptics |
| The merges carry most of every edge | 61-103 % of each competitor's edge | measure skeptic |
| The merge edge goes with merge-2 congestion | paired correlation with vehicle-seconds on edge 4a 0.93-0.96; with lane-end stops 0.85-0.90. C1 check (a): merge-2 close-following falls 35-98 % with a longer ramp-2 lane; merge 1 (also 300 m) was never length-checked | measure skeptic |
| The edge comes after the slowdown | 76-104 % of each edge falls in the rest of the window; during taper and hold v3w is worse than lr400_16_1 (−47 %), grid_lr400_13_1 (−39 %), lr400_13_2 (−33 %) and lr1000_16_2 (−29 %), and not shown different from MPC-F | measure, skeptic |
| It is not an exposure artefact | v3w serves the most vehicles (median passed 2,184); normalised by vehicle-seconds, vehicle-km or vehicles the edge is unchanged | stats, measure |
| Severe bands agree | against lr400_16_1: TTC < 2 s +32.1 %, < 1.5 s +21.9 %, DRAC +16.0 % | measure skeptic |
| Per learner | each learner alone beats lr400_16_1 (+7.3 to +12.7 %, lower bounds +3.2 to +8.4); v3w has fewer events than lr400_16_1 on only 59-63 % of seeds (a median shift, not a per-run win) | stats |

## Side measures (post hoc unless stated)

| Measure | Reading | Source |
|---|---|---|
| Delay against p333 (registered, not gating) | 0.3 % more delay; 97.5 % interval 0.5 % less to 1.1 % more; not resolvable. The exchange ratio (about 100 % per %) divides by a difference not resolved from 0; do not quote it | stats, claim |
| Delay against the fastest rule | 0.8 % slower than 3E-D_TRUCK [0.05, 1.5] | fidelity |
| Hard-braking time `b45_step` (registered) | not shown lower than every competitor (3ex2, lr400_16_1 lower bounds below 0); lower for 12 of 14 | stats |
| Hard-braking events `events_ge45` | more than 3ex2 (−4.0 % [−6.5, −0.65]), 3ex1 and 3e; only 3ex1 stays shown after a Bonferroni correction over 26; fewer than 21 of the 26 rules | claim skeptic |
| Jams (the independent check in V504 and V509(2); not in this protocol) | v3w 8.26 per run against p333's 7.88 (+0.37 [+0.15, +0.60], 95 %, mean of learners; C-D5 −5.0 % [−12.5, −1.25]); all 5 learners worse; also worse than lr1000_10_1 and 3ex2; not shown worse than lr400_16_1 or 3E-C_TRUCK; 2.5 fewer than no control | critic, re-derived by the main session |
| Fuel | not worse than any arm (vs lr400_16_1 −0.06 % [−0.18, +0.07]) | fidelity |
| Collisions | 18 of 14,880 runs; v3w 2 of 2,400, the others 16 of 12,480; teleports 0 | fidelity |
| Emergency braking beyond −9 m/s² | every arm about 21-28 ALKS events per run, no control included (the V367 artefact); v3w the fewest (21.4) | critic only, not re-derived |
| Late merges (proxy for merge-gap risk) | v3w's share of merges in the last 20 % of each lane is the lowest of all arms | critic only, not re-derived |

## Corrections to V530

- Null rates: the 234 deciding tests are 0.73-1.60 %; the 14 braking nulls are 0.85-1.48 %. All pass the 1.9 % bar.
- 115 of the 220 chords are clamped at the full sample to one rule, so 105 are real mixes.
- "Weakest competitor lr400_16_1": write "closest rule". It is X1's close-following pick.
- "Delay −0.3 %" reads as faster. v3w has 0.3 % more delay.
- Served flow and TTT were missing: v3w serves the most vehicles, and its TTT is equal to p333's.

## Disclosures the sentence must carry

1. Post hoc (V524): the cell, the star and co-star measures, the 5 % edge, the competitor rule and the chords were fixed after C1's E30 rows and the stored S and TRUCK readings had been seen; PASS was the expected reading (V526, V527).
2. Close-following (TTC < 3 s per ALKS, plus half of its direct follower's) is a term of v3w's training reward, anywhere on the network (`b_env.py:798-852`, w_safety 10). The rules picked on it were picked in other cells.
3. A transfer comparison: no rule was tuned on E30. This is the CF protocol's bar, not the "best tuned" thesis bar.
4. By C1's own registered rules these rows read NOT RESOLVABLE (delay) again. The PASS rests on CF-D6's choice, made after C1, to state delay as a trade. C1's jams and events vetoes were not carried into CF.
5. Close-following is a surrogate, not crash risk. The V&V record lists "lateral or merge-conflict safety" under "Not for", yet the edge is at the merges. PR-23 is partial (1 Hz); PR-24 (counter trace) and PR-28 (merge 1 length) are gaps.
6. Scope: one cell, 50 % share only (the V510/V511 share row was not run, because C closed), one CPU model, a synthetic uncalibrated plant; 95 cells tested on this plant. Since V504, the approaches tried were M2 and the EV rule (VOID) and C (C1 NOT RESOLVABLE, then this study), and the rest parked. V504's aim, a win on a measure such as jam waves, is not met: jams are worse than p333.
7. Name: the roadmap's "C1 confirmation CONFIRMED 16.2 %" belongs to the earlier P1 line, so call this study the "E30 confirmation".

## Sentence, worded after verification (for the author)

> On the simulated r2m3 freeway (synthetic, uncalibrated; 50 % ALKS; 5,300 veh/h), in one incident-like slowdown cell (edge 2 at 30 km/h for 4-7 min), with the cell, measures and margins fixed after an exploratory screen, on 480 fresh seeds, the frozen per-CAV DRL headway policy (5 learners; close-following is a term of its training reward) had at least 6.2 % less same-lane close-following (TTC below 3 s, a surrogate) over the 25-min window than each of the 14 stored non-learning rules not shown more than 1 % slower than it (none tuned on this event; 7 picked from confirmatory 3's grid in cells X1 and X2), and than every mix of a faster with a slower rule. Against the closest rule (lr400_16_1) the edge came at the two on-ramp merges and in the recovery after the slowdown; away from the merges and during the slowdown it had more close-following (post hoc). Its delay was 0.3 % higher than p333's (not resolved: from 0.5 % lower to 1.1 % higher), its hard braking was not shown lower than every rule, and it had about 5 % more jams than p333 (post hoc).

## Open, needing runs (not started)

- An E30-tuned rule: a close-following search under a delay cap (the "best tuned" bar; stage 2, closed by V524).
- The V510/V511 random-share row in E30.
- V&V: a traced `ttc_net` sample including a lane-end stop (PR-24); a merge-1 length check (PR-28).

## Merge V&V outcome (V536)

The merge V&V (`docs/research/results/merge_vv/reading.md`) leaves the PASS reading unchanged: no counter or meter bug, and the edge replicates on 480 fresh seeds at 300 m against lr400_16_1 (+16.0 %) and grid_lr400_13_1 (+21.7 %), also on main-lane samples. With 600-m acceleration lanes it is not shown against grid_lr400_13_1 and reverses against lr400_16_1 (−21.0 % [98.75 %: −29.0, −11.4]); "the edge depends on lane length". Every E30 sentence carries the replication line, both record sentences (reading.md §2), "the 0.1-s edge is within 3 points of the 1-Hz edge against both rules", M1 and the V4 sentence, and never "survives", "shown at both lengths" or "verified and validated". Proposed, for the author: "in this plant, with 295-m acceleration lanes ending without a taper", and no "safety benefit".
