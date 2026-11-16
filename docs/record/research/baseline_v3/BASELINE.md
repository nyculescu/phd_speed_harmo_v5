# Baseline v3: per-CAV DRL against tuned rules on plant_c3, 2026-11-05

Git tag `baseline-v3`. Decisions V377-V411. It freezes the state after confirmatory 3 and its replication, the verification, the demand sweep and the demand-profile test. It builds on baseline v2 (the P0d plant), which stays the no-controller reference.

The pre-registered results are confirmatory 3 and 3b. Everything else here is exploratory.

## What is frozen

- **Plant:** `plant_c3.json` on r2m3: P0d (baseline v2) plus `tau_rise` 0.2 (longer gaps grow at most 0.2 s per second), `taper_fast` and `fix_x`. Uncalibrated SUMO model: three lanes, two on-ramps 1.2 km apart, 50 % automated vehicles (ALKS), ideal V2V and roadside speeds.
- **Code:** commit `d2b2ecc`, frozen copy in `/home/catalin/work/phd/v5b1_runs/b_train/code_d2b2ecc`. Rule tuning and the no-control reward references ran at `fae4620`; rules read no input changed between the two.
- **Policies:** `policies/C0-C4_final.pt`. These are the 5 per-CAV PPO learners: 500 updates, 3 environments each, at demand 4,090, 4,600 and 5,300, with random slowdowns. Inputs are normalised by a running mean and SD saved in the checkpoint (V388-V389). Each policy has its config and its pilot statistics beside it.
- **Opponents:** `opponents.json`, chosen on tuning seeds from 70 rules in 6 forms (V377-V383), and `copy_rule.json`.
- **Seeds:**
  - tuning 7,440,160-179;
  - tracing 180-189;
  - evaluation 200-219;
  - replication 220-239;
  - training 7,456,000-7,463,782.

## The four controllers

| Controller | What it does (automated cars only) |
|---|---|
| No control | Every ALKS keeps 1.6 s to the car ahead |
| 0.8 s rule (p333) | An ALKS behind another ALKS within 150 m keeps 0.8 s, always; behind a human-driven car, 1.6 s |
| Best tuned rule in X2 (os1_15_10) | 0.8 s, but 1.2 s when past the first merge, slower than 15 m/s, with at least 10 cars waiting to merge |
| DRL policies (d0-d4) | Each ALKS's level (1.6, 1.2, 1.0 or 0.8 s) chosen every 10 s from its own local state |

## Results, in words: fewer and less mean DRL is better

**Pre-registered (confirmatory 3, V395-V396; 3b, V401):**

| Cell (5,300 veh/h) | Verdict | Against the best tuned rule |
|---|---|---|
| X2, original seeds | Won, 4 of 5, at the minimum | 24-30 % fewer close-following seconds (TTC below 3 s), delay within 2 % |
| X2, fresh seeds | Not confirmed, 1 of 5 | 14-26 % fewer close-following, but 1.6-10 % more delay |
| X1, original seeds | Not won, 3 of 5 | Only the 0.8 s rule counted: 33-46 % fewer, but 2 policies over the delay limit |

**Against the simple baselines in X1 and X2 at 5,300 (V405):**
- Against the 0.8 s rule: 29-45 % fewer close-following seconds, delay about the same.
- Against no control: 18-28 % less delay. Close-following is about the same in X2 and 31 % more in X1.

Each baseline is beaten on one measure, not both.

**Replays (V398):**
- Every stored number reproduces.
- To 3,000 s, all 5 policies have fewer close-following seconds than every counting rule.
- Human drivers gain too.
- Part of the gain at merge 2 moves to the mainline against r4a1.

**Demand sweep (V409; exploratory, 16 random levels from 3,920 to 5,910, 4 seeds):**
- Against the rules: 10-49 % fewer close-following seconds at most levels, including above the training range.
- Against no control: always 15-39 % less delay, and fewer close-following seconds only in a band near the onset of congestion, roughly 4,500-5,400 veh/h depending on the condition.

**Demand profiles (V410; exploratory, 10 seeds, small counts):**
- Step: DRL best.
- Slow sine: better than the rules.
- Fast sine: no difference from the rules.
- Peak: worse than the rules on close-following.
- Delay is always 23-28 % below no control.

The author has chased training with varying demand before and found it not worth it (V411).

## Known limits

- **Surrogate:** close-following (TTC below 3 s, read once a second) is a surrogate and is also in the policies' reward. Lateral and merge conflicts are not measured.
- **Lane ends:** merge-2 lane-end behaviour on r2m3 is not validated, and part of the X2 gain sits there (V396).
- **Opponents and fragility:** the opponents are rule families only; the MPC arm was dropped. The X2 win was reached at the minimum and depends on which rules passed the delay filter.
- **Input design:** inputs were hand-scaled until V387; earlier policies (V290-V368) used the old inputs.
- **Sweep fairness:** the rules were tuned at 5,300 only, which favours DRL at other demand levels in the sweep.

## Where everything is

- **In git, beside this file:**
  - plant, opponents, copy rule, environment, policies with configs and pilot statistics;
  - the reading tables `decide3_table.csv` and `decide3_map.csv`;
  - `rows/`: every evaluation, tuning, tracing, update-250, replication, replay, sweep and profile row, gzipped;
  - `runs/`: status logs, the chain log without warnings, sweep levels and profiles.
- **Reports:**
  - `docs/reports/2026-11-05_19-22/` (results);
  - `docs/reports/2026-11-05_20-51/` (demand sweep);
  - `docs/research/conf3/verification_rev4.md` (verification).
- **Read-only full copy, with `SHA256SUMS`:** `/home/catalin/work/phd/v5b1_runs/baseline_v3/`. It holds every run folder with all checkpoints, the frozen code and the verification scripts.
