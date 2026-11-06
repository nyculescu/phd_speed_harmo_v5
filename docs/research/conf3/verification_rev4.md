# Confirmatory 3, revision 4: verification of the fixed reading

Date 2026-11-05 (V396). Six independent reviewers each attacked the result from one angle: provenance, arithmetic, opponent selection, artefacts, robustness and process. A skeptic per reviewer then tried to refute each finding, a critic listed what was still missing, and two agents closed the most important gaps. 15 agents in all, about 2.56 million tokens, read-only, no simulations. Digest of every finding and verdict: `verification_rev4_digest.txt` beside this file. Scripts: `/home/catalin/work/phd/v5b1_runs/phase3/scratch/verify/`, outside git.

## Verdict

The fixed reading stands: **X2 is won on TTC by the tuned reading, and X1 is not won and closes [A3].** No finding changes a verdict under the protocol.

- **Provenance:** clean. The frozen code is byte-identical to `d2b2ecc`. All 2,000 evaluation rows are present, each once, on seeds 7,440,200-219, with configs as designed and the right final checkpoints with their input statistics. None of the 92 set-aside rows leaked in, and they are identical to the chain's.
- **Arithmetic:** clean. Independent code reproduces every number and verdict. The bootstrap method, level and seed decide no outcome.
- **Selection:** clean. It reproduces exactly from the tuning rows, and every chosen rule fires and uses only allowed information.
- **No artefact or shifted cost against the counting rules:**
  - the drop holds at the half-second offset, per vehicle-second and per kilometre;
  - it grows with severity: 17-23 % at TTC 2-3 s, 37-51 % below 1.5 s;
  - delay, flow, ramp delays, undertakes and fuel are equal or better;
  - two counts outside the reward fell: ramp-2 lane-end stops and stopped gaps below 2.5 m.

## What the result can and cannot say

| Point | Finding | Severity |
|---|---|---|
| Where the gain is | It arises after the slowdown, in the recovery queue: 82-96 % falls in 1,000-1,800 s, simulation time, after a 300-s warm-up. Places: roads 4a and ramp 2 (46-61 % against os1_15_10, 67-74 % against p333) and road 3. Before the slowdown, policies and rules differ by a median of 0-22 s. | major |
| V395's reading | "Mostly outside the slowdown periods" misread the period labels, and "the edge seems not specific to slowdowns" is not supported. In steady traffic at 5,300, 4 of 5 policies have CIs including 0 against p333. At 4,600 there is no edge. Same-seed S against X2 shows the gain appears after the slowdown. Both statements are withdrawn. | major |
| No control | In X2 the policies are not below no control on TTC below 3 s: -14.8 to +2.9 %, none better, d2 worse. ALKS braking at 3 m/s², counted per step, is 9-18 % above no control, all CIs excluding 0. The policies are lower on severe samples and on TTC below 1.5 s, at 16-21 % less delay. "Safety" therefore means safer than the tuned 0.8-s rules, not safer than no control. | major |
| Fragility | Won at the pre-registered minimum, 4 of 5. Leave-one-seed-out keeps 4 of 5 in 20 of 20 refits, but resampling all evaluation seeds gives "won" in about 27-30 % of replicates. The TTC conditions alone hold in about 76 %; the point-median delay and flow limits (SD 1-5 and 0.3-0.9 points against limits of 2 and 0.5) cause most of the rest. X1's "not won" is just as knife-edge: at a 3 % delay limit it would be won. So no "works in X2, not in X1" reading. | major |
| Counting set | The win depends on the evaluation-seed delay filter excluding a4400_10_1, the lowest-TTC tuned rule: delay -4.60 [-7.98, -0.51] % against p333. Had it counted, only 3 of 5 policies would clear. The X1 own-state choice os0_10_10 also ran in X2 as a by-product; there only 1 of 5 policies clear it, on delay and flow. The counting set is close to a draw among rules near p333's delay: the same set comes back in 47 % of resamples. | major, disclosure |
| Against lr1000_16_2 | Off merge 2, the gain is 3.7-9.7 %, below the 10 % margin. So the clearance against this rule rests on merge 2, whose lane-end behaviour was never validated on r2m3. Against os1_15_10 the margin holds even when only followers at 5 m/s or faster are counted (15-19 %). | major, open |
| Teaching to the test | ttc_net and the severe check both come from the same 1-Hz car-following samples that the reward penalises. Lateral and merge conflicts are not measured. | minor, disclosure |
| Who gains | Not measured: the class split (ALKS against human followers) needs a rerun with the `attrib` counter. Human braking at 3 m/s² fell against os1_15_10 and p333. One weak signal: d0 against r4a1 gives humans more braking at 4.5 m/s², which the total hides. | major, open |
| Window | 1,800 s ends while the X2 backlog is still discharging, so the size of the gain depends on the window. | minor, open |
| Training | The policies were still changing at update 500: final against u250 differs by up to 32 % on TTC, and the share of 0.8 s rose from 0.63-0.66 to 0.78-0.82 over training. X1's two slowdown events never occur in training (0 of 7,500 episodes); X2-like events are inside the training range but rare. | minor, disclosure |
| Opponent grid | lr1000_16_2 and os1_15_10 sit at the edge of their tuning grids. No family holds a long headway on ramp 2 alone; the copy rule does, but at 1.0 s on the mainline. | minor, disclosure |
| Harm cells | None against p333 and the single rule. Against no control, S at 4,600 is clearly worse for all 5 policies, on tiny counts (34 against 67-86 TTC-seconds). | minor, wording |

## The X2 sentence, completed from the template

In an uncalibrated SUMO model of a three-lane freeway with two on-ramps 1.2 km apart and 50 % automated vehicles, at 5,300 veh/h, with ideal V2V and ideal roadside speeds:

> Under a tapered slowdown to 30 km/h for 180 s on the road between the ramps, at least 4 of 5 per-CAV PPO headway policies, trained for 500 updates, had fewer seconds at TTC below 3 s than each of 3 counting rules tuned on separate seeds and the fixed 0.8 s rule: 8.5-30.0 % over the 5 policies against the counting rule with the lowest TTC. Median delay and flow were within the stated limits. This is a surrogate. The gain arose in the queue that remained after the slowdown, mostly at the second merge and on the road before it. No control had 1,639 such seconds, 297,046 vehicle-seconds of delay and 3,497 vehicle-seconds of braking at 3 m/s²; the policies were not below no control on this count, at 16-21 % less delay. Collisions: none in the primary arms, too rare to compare. No map cell shows the policies clearly worse than p333 or the single rule; cells not listed are not shown to be unharmed where the CI is wide.

Beside it, always:
- the cell was won at the minimum count and is sensitive to the evaluation seeds;
- it depends on the delay filter excluding a4400_10_1 (with that rule, 3 of 5);
- with 20 seeds a delay cost of a few per cent is not excluded.

**X1:** neither reading. Only p333 counted. 2 of 5 policies had median delay 2.5-3.1 % worse than it; their paired CIs include 0. No control had fewer seconds at TTC below 3 s, at 37.5 % more delay. The single-rule sentence does not apply, because the single rule itself failed X1's delay filter.

Do not write: "at equal delay", "robust", "clear", "consistent", "safer" without "than the tuned 0.8-s rules", "not specific to slowdowns", or that per-CAV PPO succeeds in about 80 % of runs.

## Process and records

- **Pre-run checks:** T0 and T3 ran at `fae4620` only, and the chain checks only that the gate file exists. The run's own rows meet T0's gates: on-level share at least 0.996 for every policy arm, and moving events within no control's plus 5. Rule rows reproduce at `d2b2ecc`: the 92 set-aside rows are identical. A policy arm was never replayed at `d2b2ecc`.
- **Commits:** tuning and the no-control references come from `fae4620`; everything else, including both selections, ran at `d2b2ecc`. Rules read no changed input.
- **Corrections to the record:**
  - the aborted hand-scaled run did 5 updates, not 3 (V388, protocol Disclosures, status.txt);
  - the copy rule's delay is 8.6 % (X2) and 9.6 % (X1) on the protocol's statistic, not "about 7 %";
  - V395's recheck "with separate code" ran inline and was not kept; this verification replaces it.
- **Not reported in V395:**
  - u250 against the final policies, and the level shares (above);
  - 4 map arms whose whole-second and half-second TTC differ by 5-7 % (H1 and H2 at 4,600);
  - 8 collisions in H1 at 4,600, one per arm on one seed, no control included.
- **Latent differences between code and text, with no effect here:**
  - `decide3.py` counts the copy rule only if it was admissible on tuning seeds;
  - the adaptation share uses a one-sided test.
  - Fix both before `decide3.py` is reused.
- **Other disclosures:**
  - the guard ran at 95 % from 11:57 (V391), with no pauses;
  - a stored P0 policy was compared with p333 on the check seeds before approval, trace only;
  - the normalisation smoke's tolerance was widened after seeing it (V389).

## Replays done (V398)

All 200 base replays reproduce every stored number, and the long runs match at 1,800 s. Over 300-3,000 s, all 5 policies have lower TTC below 3 s than every counting rule, with CIs excluding 0, at equal or better delay. The gain is not only creep on the accelerating lane: without 4a_0, it is still 16-30 % against os1_15_10. Against r4a1, some conflicts move to the 4a mainline. Human and truck followers have fewer TTC seconds than under every rule and under no control, including human-behind-human pairs, which no reward term charges. ALKS followers have more TTC seconds than under no control. Details: `rerun/analysis.txt` and V398.

## Open, as listed before the replays

All of these are report-only replays on used seeds and cannot change the verdict.

1. **Replay one policy arm** at `d2b2ecc` and compare every key with the stored row. This tests determinism.
2. **Rerun X2 at 5,300** for policies, counting rules and no control, after an exact-reproduction assert, with two additions:
   - TTC on 4a_0 against the mainline lanes, and in the last 50 m of 4a_0;
   - the `attrib` class split by follower, adding the leader's class so that reward-charged pairs can be told from spillover.
3. **The same with a longer window**, to full recovery.

About 200-400 runs, roughly 10-20 minutes at 24 workers.

**Thesis level:** the opponents are rule families only, since the MPC arm was dropped. Whether that suffices for a thesis-level claim under V95 is the author's decision.
