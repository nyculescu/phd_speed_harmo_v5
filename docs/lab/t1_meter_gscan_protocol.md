# T1-M: headroom scan for the BN4 feedback meter under perturbations, pre-registration

*Committed 2026-10-03, before any scan run. Author choice: "A now, build B in parallel".*

**Why.** Posted-VSL harmonisation on LD3 was killed (G ≤ 4 %). DRL needs conditions in which the best classical *setting* changes strongly.
- **BN4** is the one plant where SUMO showed a capacity drop (1,044 → 900 veh/h).
- **Its meter** has large authority (−45 % door-to-door vs NC, R2 v2).
- **A feedback meter with a fixed set-point** (Vinitsky's q ← q + K_F (n_crit − n̂)) is expected to be wrong when capacity or demand changes unexpectedly.

**Plant:** BN4 as in R2 v2, with 10 % uncontrolled AVs, 40 s warm-up, 900 s control and an uncontrolled drain.
**Metric:** mean door-to-door time, including the origin queue.

**Perturbations** (env `perturb`; start ~ U(warm-up + 100, end − dur − 100) from rng(seed + 991)):

| Kind | Effect |
|---|---|
| `none` | no perturbation |
| `slow` | bottleneck edge 5 speed limit → 5 m/s for 300 s (3 m/s caused a teleport in the smoke run, so it was made milder; disclosed) |
| `block` | a vehicle stops at mid-edge 4, lane 1, for 180 s (it brakes normally) |
| `surge` | inflow × 1.3 for 300 s |

**Conditions:** q ∈ {1,600, 2,000} × the 4 kinds = 8.
**Controllers:** `nc` + `meter:K:n` for K ∈ {5, 10, 20, 40} and n ∈ {4, 6, 8, 10, 12}, i.e. 21.
**Seeds:** 7,110,160–7,110,179. This is the unused part of the T1 tuning range, reassigned and disclosed.
**Runs:** 3,360.

**Families**, per q:
- {none, slow}, {none, block}, {none, surge}, and all four together.

For each family:
- **G** = (J_pool − J_look) / J_pool;
- **J_pool** = the best single setting, averaged over the family's conditions;
- **J_look** = the per-condition best setting (oracle);
- J is the median over seeds;
- teleports are reported per condition.

**Rule:**
- G ≥ 10 % → candidate DRL target. An **H** step follows, pre-registered then, with non-learning adaptive meters, e.g. set-point switching on a detected slowdown or blockage.
- G < 10 % everywhere → the meter is killed as a DRL target on BN4.
- G is biased upwards, so a FAIL is a conservative KILL.

---

## Result and Addendum A: H step, pre-registered 2026-10-03 before any H run

**Scan result** (`t1_meter_gscan.md`, tuning seeds 7,110,160–7,110,179):
- **G (all four kinds mixed):** 15.4 % at q = 1,600 and 10.3 % at q = 2,000.
- **Single-kind families:** 1.8–8.8 %.
- **Blockage-condition teleports:** spread across controllers; 1 of 20 or 0 for the per-condition best. Reported, and the medians are unaffected.

**Lookup I** (oracle condition → meter setting), frozen in `docs/lab/t1_meter_lookup.json`:

| Inflow | Pooled best | none | slow | block | surge |
|---|---|---|---|---|---|
| 1,600 | 40:8 | 40:6 | 40:8 | 20:12 | 5:8 |
| 2,000 | 5:8 | 40:6 | 40:8 | 20:10 | 5:10 |

**Non-learning adaptive scheduler `evsched:v_slow:t_block:f_surge`** (`jobs/bn4_eval.py`): it detects events from measurements only and maps the detected state to the same lookup settings. It runs every 30 s:
- **block:** a vehicle on edge 4 lane 1 has been halted ≥ t_block s while lane 0 moves;
- **slow:** the 60-s mean speed on edge 5 is below v_slow;
- **surge:** the 120-s departure rate exceeds f_surge × the rate of the first 300 s of control;
- **otherwise:** none.

**H1 (tuning seeds 7,110,160–7,110,179).**
- **Grid:** v_slow ∈ {5, 7, 9} m/s, t_block ∈ {10, 20, 40} s, f_surge ∈ {1.15, 1.25, 1.35}, i.e. 27 settings × 8 conditions × 20 seeds.
- **Selection:** lowest mean over the 8 conditions of the median door-to-door time.

**H2 (fresh gate seeds 7,110,180–7,110,199)**, on the 8 conditions:
- `nc`;
- `meter:10:6` (the R2 v2 tuned meter, reported);
- the per-q pooled best fixed setting;
- the **lookup I** (oracle: the per-(q, kind) setting from `t1_meter_lookup.json`);
- the H1-tuned `evsched`.

**H, per q:**
- per seed s: J_X(s) = the mean over the 4 kinds of door-to-door time;
- best non-learning NL = whichever of {pooled fixed, `evsched`} has the lower median J (selected on gate seeds; this favours NL, so it is conservative);
- d(s) = J_NL(s) − J_I(s);
- **H = median(d) / median(J_NL)**, with a 95 % percentile-bootstrap CI of median(d).

**Rule:** a DRL target needs H ≥ 10 % **and** a CI lower bound > 0 (CLAUDE.md), at either q.

**Before any DRL claim** (not before exploratory DRL), an MPC baseline with a model fitted on separate seeds must also be built (CLAUDE.md).

## Addendum B (2026-10-03): DRL pilot P-M at q ≈ 1,600, pre-registered before any P-M training

**H result.** H = 20.4 % at q = 1,600, with a paired CI of [+18, +79] s, so this is a DRL target. At q = 2,000, H = −3.3 %, so it is not.

**Bug found in the plumbing test, before any P-M run.** `BN4Env.reset()` sized the previous-action vector for the AV-cap actuator (22 values) whatever the actuator, so the first observation of every `meter_sched` or `posted_vsl` episode had the wrong length. Fixed (`n_prev`). No earlier DRL run used those actuators: A-P5 was never run, and C was killed before any DRL.

**Hybrid design** (the validated feedback meter is always in the loop):
- **Actuator:** `meter_sched` with `meter_grid` = the q = 1,600 lookup settings ["40:6", "40:8", "20:12", "5:8"]. `allow_off` = false.
- **Decisions:** DRL picks the setting every 30 s.
- **Observation:** S-VIN (lane-piece counts and speeds, 20-s outflow, previous action).
- **Reward:** R-TTS, i.e. −(vehicles in network + waiting) per decision.

**Training:**
- inflow ~ U(1,400, 1,800); one perturbation per episode, uniform over {none, slow, block, surge}, with the same specs as the scan; timing from the seed;
- seed pool 7,210,000+;
- PPO, 16 envs × 60 steps (rollout 960, minibatch 240), 500 updates, 10 epochs, learning rate 3e-4 with decay, γ 0.99, GAE 0.95, net 128×128, learner seed 0.

**Checkpointing:** validation every 25 updates on q = 1,600 × the 4 kinds × seeds 7,110,320–7,110,322, metric `tts_system_ctrl_vehh`.

**Screening** (`jobs/t1_meter_pm.py`, `bn4_eval`, door-to-door including the drain):
- **Seeds:** 7,110,330–7,110,339, disjoint from the checkpoint seeds; 4 kinds × 10 seeds.
- **Controllers:** the final and best-validation policies, `evsched:7:20:1.15`, pooled `meter:40:8`, the lookup (oracle), `meter:10:6` and `nc`.
- **Score:** per seed, J(s) = the mean over the 4 kinds.
- **PASS:** median paired (DRL − `evsched`) ≤ −5 % of `evsched`'s median J, with the 95 % bootstrap CI excluding 0; and 0 health FAIL beyond those also seen in `evsched`'s runs.
- **Passers:** F class (3 seeds × 1,000 updates), then R5-M on test seeds 7,110,590–7,110,619.
- **Before a thesis claim:** an MPC baseline with a model fitted on separate seeds (CLAUDE.md).

**P-M (first launch) is INVALID: training stopped itself after 2 updates.**
- **Cause:** the training health rule stops a run when the FAIL share exceeds 1 % after 50 episodes. One perturbation episode out of 96 had a FAIL (1.04 %). FAILs of this kind are teleports, which the scan saw in about 2–5 % of blockage runs for every controller, NC included.
- **Its screening entry** in `t1_meter_pm.md` (final J 237.6 against `evsched` 197.9) **evaluates an untrained policy and is void.**

**P-M2** is identical to P-M except `--max-fail-share 0.05`, a new CLI option whose default stays 1 %.
- The 5 % tolerance follows from the scan's measured teleport rate: blockages are a quarter of the mix, so about 1 % of episodes are expected to FAIL.
- FAIL episodes are still counted and reported.

## P-M2 result and Addendum C: P-M3 exploratory variants (2026-10-03, before any P-M3 run)

**P-M2: screening FAIL.**
- 500 updates; FAIL share 2.8 %.
- Final DRL against `evsched`: median paired Δ +0.2 s (+0.1 %), CI [−26, +51]. Against the lookup: +6.5 %, n.s. Against NC: −20 %, CI excluding 0.
- **The validation curve shows no learning:** 16.0 at update 0 (a random policy over the 4 settings), 17.4 at the end.
- **The screening was underpowered:** with 10 seeds the CI widths were about ±40 s, against a 5 % target of about 10 s.

**P-M3, exploratory.** Three variants trained in parallel, each 1,000 updates, learner seed 0, otherwise P-M2's configuration (including `--max-fail-share 0.05`):

| Variant | Change |
|---|---|
| **a** | PPO + `obs_stack` 4 (the last 4 observations concatenated; events need trends) |
| **b** | RecurrentPPO (LSTM), no stack |
| **c** | plain PPO (the budget effect alone) |

**Screening, with more power:** fresh seeds 7,110,340–7,110,389 (50) × 4 kinds. Rule, comparators and statistics are as in Addendum B.

**Multiple comparisons, disclosed:** 4 pilots in total (P-M2 and P-M3 a–c) are screened against the same rule. A pass is an exploratory signal only. A claim still needs the F class (3 learner seeds × 1,000 updates), R5-M on the test seeds and the MPC baseline.

## P-M3 result and Addendum D: the claim path (2026-10-03, before any F-class or R5-M run)

**P-M3 screening** (50 seeds 7,110,340–7,110,389 × 4 kinds, q = 1,600; `t1_meter_pm.md`):

| Variant | Policy | vs `evsched` | 95 % CI | Verdict |
|---|---|---|---|---|
| **b (RecurrentPPO)** | final | **−9.6 %** | **[−40.8, −6.7] s** | **PASS** |
| a (stack 4) | final | +3.5 % | n.s. | FAIL |
| a | best | −2.1 % | n.s. | FAIL |
| c (plain PPO) | final | +2.6 % | n.s. | FAIL |

P-M3b's final policy also: vs pooled −10.2 % (CI excludes 0), vs lookup −1.0 % (n.s.), vs `meter:10:6` −13.3 %, vs NC −25.7 %.

**Disclosure:**
- **Screening looks:** 1 PASS out of 8 (P-M2 and P-M3 a–c, each final and best).
- **Learning:** the validation curves of a and b improved (19.1 → 14.9 and 17.9 → 14.8 veh·h); c's did not.

**F class.** RecurrentPPO, P-M3b's configuration, 1,000 updates.
- Learner seed 0 = the P-M3b run.
- Learner seeds 1 and 2 are new runs.
- **Evaluation:** the final policies.

**MPC-F, the fitted-model MPC baseline** (CLAUDE.md "best non-learning"), frozen before R5-M:
- **Data:** episodes with random setting switches on separate seeds 7,110,200–7,110,299 (T1 tuning range, unused).
- **Model:** regressors fitted on that data. They predict the next-5-min TTS increment from the current S-VIN features, the measured inflow and the candidate setting.
- **Control:** every 30 s, choose the setting with the lowest predicted cost (receding horizon, constant input over 5 min).
- **Never given the true model or the perturbation kind.**
- Its design details are added before it is fitted.

**R5-M**, the head-to-head:
- **Seeds and conditions:** test seeds 7,110,590–7,110,689 (100), × 4 kinds, at q = 1,600.
- **Controllers:** the F-class finals (3 seeds, plus their pooled median), `evsched:7:20:1.15`, pooled `meter:40:8`, MPC-F, `meter:10:6`, NC, and the lookup oracle (reported only).
- **Reading:**
  - DRL beats a comparator if the median paired difference in J (the mean over the 4 kinds of door-to-door time) is < 0 with the 95 % bootstrap CI excluding 0, **pooled and in ≥ 2 of 3 learner seeds**.
  - **"DRL measurably improves on the best non-learning control"** requires beating **both** `evsched` and MPC-F.
  - Per-kind results are reported, and no kind may be significantly worse by more than +5 %.
- **Side constraints:** health FAIL share ≤ 5 % (perturbation teleports, as with every controller); teleports reported.

### Addendum D2: MPC-F design, fixed before data generation and fitting (`jobs/mpcf.py`)

**Data:**
- seeds 7,110,200–7,110,299 × the 4 kinds × 5 replicates;
- inflow ~ U(1,400, 1,800) per replicate;
- the meter setting (one of the 4 lookup settings) is held for 10 decisions (300 s) at a time, chosen at random, starting at a random offset;
- one sample per completed hold: (S-VIN observation at hold start, 120-s measured inflow, setting, veh-s in the system over the hold).

**Model and fit:**
- an MLP (2 × 64 tanh) on standardised inputs (observation + inflow/2000 + setting one-hot), trained with MSE and Adam (lr 1e-3);
- 80/20 split **by (kind, seed) group**, with early stopping (patience 30 epochs);
- the validation R² is reported, and the model is frozen in `docs/lab/t1_mpcf_model.pt` before R5-M.

**Controller:** `mpcf` in `bn4_eval`. Every 30 s, the setting with the lowest predicted 300-s cost from the current state. It is never given the perturbation kind or the true model.

## R5-M result and Addendum E: P-M4 reliability (2026-10-03, before any P-M4 run)

**R5-M result** (`t1_meter_r5.md`): **no claim.**
- Pooled DRL against `evsched`: −1.0 %; against MPC-F: −0.5 %; both CIs include 0.
- Only learner seed 0 beats both.
- DRL robustly beats `meter:10:6` (−7.4 %) and NC (−16.4 %).
- **Diagnosis: unreliable training.** Seed 1's validation went 14.8 (best) → 17.8 (final). Checkpoint scores came from only 12 episodes.

**P-M4** (author choice: "both in parallel" with the corridor work):

| Item | P-M4 setting |
|---|---|
| algorithm and design | RecurrentPPO, same hybrid as P-M3b |
| learner seeds | 3, 4, 5 (fresh training pools) |
| updates | 2,000 |
| rollout | 16 envs × 120 steps (1,920 per update), minibatch 480 |
| other hyperparameters | as P-M3b (10 epochs, learning rate 3e-4 with decay, γ 0.99, GAE 0.95, net 128×128, `--max-fail-share 0.05`) |
| checkpoint selection | every 25 updates, on **40 episodes**: seeds 7,110,400–7,110,409 × the 4 kinds at q = 1,600 |

**Primary policy = the best-validation checkpoint** (CLAUDE.md: "checkpoints chosen on validation seeds only"). The final policy is reported as secondary.

**R5-M2:**
- **Seeds and conditions:** fresh test seeds 7,110,690–7,110,789 (100) × 4 kinds.
- **Controllers:** `evsched:7:20:1.15`, MPC-F (frozen), pooled `meter:40:8`, `meter:10:6`, NC and the lookup.
- **Reading:** exactly as in Addendum D. The claim needs beating both `evsched` and MPC-F, pooled and in ≥ 2 of 3 learners, with no kind significantly worse by more than 5 % and a FAIL share ≤ 5 %.

**P-M4 note (2026-10-03, during training).**
- **Seed 4 stopped at update 0** on the health rule: 4 perturbation-teleport FAILs in its first 64 episodes (6.25 % > 5 %, right after the 50-episode minimum).
- **Rerun:** it is re-run identically except `--fail-min-episodes 500` (a new option; the default stays 50), so the 5 % rule judges a meaningful sample. Seeds 3 and 5 continue unchanged.
- **The R5-M2 chain** is replaced by one that waits for all three learners by PID. The stopped seed-4 run is logged and not used.

## R5-M2 result (2026-10-03 14:37) and a seed-layout breach

**R5-M2** (`r5m2.md`; primary = the best-validation checkpoints of learners 3, 4, 5): **NO claim.**

| DRL vs | Pooled Δ | 95 % CI | Learners (3 / 4 / 5) | Beats |
|---|---|---|---|---|
| `evsched` | −2.7 % (−6.2 s) | [−13.0, +2.6] s | −9.3 / −3.9 / −8.8 s, none significant | no |
| MPC-F | −4.7 % (−11.1 s) | **[−19.6, −4.3] s** | only learner 3 significant | no (1 of 3) |
| pooled fixed | −4.7 % | excludes 0 | 2 of 3 | **yes** |
| `meter:10:6` | −12.4 % | excludes 0 | 3 of 3 | **yes** |
| NC | −24.5 % | excludes 0 | 3 of 3 | **yes** |

- **Per kind:** under blockages, −18 % vs `evsched` and −10.5 % vs MPC-F, both CIs excluding 0.
- **Secondary (final policies, `r5m2_final.md`):** also NO.
- **Interpretation:** all three learners are now competitive. Reliability is fixed relative to R5-M. The effect against the best non-learning control (about 3–5 %) is below what 100 seeds resolve per learner.

**Seed-layout breach (my error, disclosed).**
- R5-M2's test seeds 7,110,690–7,110,789 extend into the **reserved confirmatory range** 7,110,700–7,110,999 (approved layout, roadmap §10). 90 reserved seeds were consumed by an exploratory test.
- Seeds 7,110,790–7,110,999 (210) remain untouched.
- Any R6 confirmatory run uses only those 210 seeds, and is pre-registered before it runs.
