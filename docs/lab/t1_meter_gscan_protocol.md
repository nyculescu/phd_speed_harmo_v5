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
