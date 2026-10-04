# Note for supervisor: DRL vs tuned control, where the thesis stands (draft, 2026-10-04)

**From:** Catalin Niculescu · **Thesis:** "Adaptive driving algorithms for intelligent road traffic systems" (submission ≈ Sept 2027)

## What happened

- **v4/v5 (VSL in SUMO).** DRL policies set speed limits directly; they never beat the VSL controllers. The effort was large: over 1,000 hours.
- **2026.** I switched to pre-registered "headroom gates" with:
  - baselines tuned on separate seeds;
  - paired replications with bootstrap CIs;
  - a door-to-door delay metric that includes origin queues.
- **Five candidate problems in v6** (fleet rebalancing, perimeter gating, bus holding, truck eco-approach, signal priority) were stopped early. Each time, a tuned rule or MPC left less than 10 % room for a learned layer.
- **The v5 DRL lab produced one pre-registered confirmatory result (R6).** A RecurrentPPO policy schedules a validated feedback ramp meter on a SUMO bottleneck with perturbations.
  - **Result:** 4.3 % less delay than a tuned event scheduler and 2.5 % less than an MPC whose model was fitted on separate seeds, on 210 reserved seeds, with both CIs excluding zero.
  - **Limits:** it does not generalise beyond its training perturbation mix, and a reference that knows the hidden condition still does 5.8 % better.

## What the literature check shows

I re-audited 39 RL/DRL VSL papers against their full texts, with page references and verified quotes (`docs/review/`).
- **15 of 39 have no classical comparator.** They compare with no control, a fixed limit, or other RL.
- **Of the 23 with one, 16 copy, hand-set, or do not state its parameters.** None tunes it on scenarios separate from the test.
- **Asymmetric comparisons are common.** For example, RL sets per-lane limits while the feedback controller posts one limit for all lanes.
- **Evaluation is usually on the training scenario,** often with single or selected runs and no dispersion.
- **Where the comparator was tuned, RL lost, tied, or won by about 0–2 %.** Two larger gains remain unreplicated: a macroscopic study, and a PhD thesis on a custom simulator with single runs.

The numerical inconsistencies I found look like honest errors. One reported "50.47 %" is reproducible from the paper's own table, even though its text quotes the wrong values. **I see no evidence of misconduct and do not intend to suggest any.** The problem is systematic optimistic bias in the evaluation designs, not individual wrongdoing.

**Conclusion:** the published DRL-VSL gains do not show what the thesis needs: DRL beating *tuned* control. My negative results are consistent with the literature once the literature is read against its comparators.

## What I propose

1. **Reframe the thesis around *when* DRL adds value over tuned control,** using DRL as a scheduler or residual on top of validated controllers. The core contributions:
   - the pre-registered gate protocol;
   - R6 as a small but confirmed positive case;
   - the killed cases as evidence on the limits.

   This still answers "DRL measurably improving predictive and reactive control", with honest effect sizes.
2. **Paper 1 (experimental):** "DRL vs tuned control under pre-registration" (R6 + gates). I would strengthen it with one reproduction of the strongest SUMO claim in the literature (Han et al. 2024, TRR), against a feedback controller that is tuned and per-lane. Estimated cost: 2–3 weeks.
3. **Paper 2 (audit):** a systematic, protocol-based audit of DRL-VSL evaluations. It needs a documented search and a second rater. Before submission, I would send each inconsistency to the authors concerned.
4. **Candidate venues (to confirm):** IEEE T-ITS (regular article, or the survey article type for Paper 2); TMLR (reproducibility studies); PLOS ONE (accepts null results); IEEE ITSC 2027 for an early short version.

## Decisions I need from you

- (a) Do you agree with the reframing?
- (b) One paper or two?
- (c) Should I do the Han 2024 reproduction before writing Paper 1?
- (d) Are you comfortable with an audit paper that names specific papers' weaknesses, and with contacting their authors first?
