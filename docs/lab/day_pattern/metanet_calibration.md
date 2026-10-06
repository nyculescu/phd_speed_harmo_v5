# U.S.169 SB METANET plant: calibration freeze

Protocol: `docs/plans/day_pattern_metanet_protocol_v3.md` (v3, binding). Stage: freeze (before any validation run); route stop record. Variant `step_b` (§1.7 step (b), G4). pycma 4.5.0. Calibration days only: 22 usable. Raw runs: `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet`; full numbers in `metanet_calibration.json`.

**Route after the freeze: STOP (N0 FAIL: step-halving).**

## Fit (§4.3–4.4)

- Nominal plant: restart seed 7190016, J = 0.1649 (continued to 8,000 evaluations: False).
- J terms (mean over days): NRMSE_q 0.071, NRMSE_v 0.116, NRMSE_v congestion 0.236; v0 whole-day J 0.093.

| seed | evals | best J | inadmissible evals | improvement last 20 % |
|---|---|---|---|---|
| 7190011 | 4008 | 0.1698 | 143 | 0.0010 |
| 7190012 | 4008 | 0.1697 | 131 | 0.0002 |
| 7190013 | 4008 | 0.1697 | 108 | 0.0003 |
| 7190014 | 4008 | 0.1698 | 250 | 0.0004 |
| 7190015 | 4008 | 0.1697 | 163 | 0.0011 |
| 7190016 | 4008 | 0.1649 | 119 | 0.0009 |
| 7190017 | 4008 | 0.1697 | 127 | 0.0004 |
| 7190018 | 4008 | 0.1697 | 93 | 0.0001 |

Frozen parameters: vf1 = 109.2, vf2 = 127.3, vf3 = 121.2, rc1 = 44.78, rc2 = 28.44, rc3 = 25.91, a1 = 3.087, a2 = 1.01, a3 = 2.748, tau = 12.01, nu = 54.64, kappa = 55.04, delta_m = 2.531, phi = 3.455, theta1 = 0.9911, rc4 = 30.14, a4 = 3.497.

## Step-halving (§2.5; gated as part of N0)

J(5 s) = 0.1649, J(2.5 s) = 0.1653, relative change 0.0023 (limit 0.05); P_1/P_2 episode-day sets unchanged: False; largest per-station RMS speed change 3.21 km/h. **FAIL**. P2 days only at 5 s: []; only at 2.5 s: ['20230517'].

## Identifiability (§4.5; reported, not gated)

- Near-best restarts (J ≤ 1.02 J_best): 1 ([7190016]).
- Non-identifiable: vf1 (restart spread not assessable); vf2 (restart spread not assessable); vf3 (restart spread not assessable); rc1 (restart spread not assessable); rc2 (restart spread not assessable); rc3 (restart spread not assessable); a1 (restart spread not assessable); a2 (restart spread not assessable); a3 (restart spread not assessable); tau (restart spread not assessable); nu (restart spread not assessable); kappa (restart spread not assessable); delta_m (restart spread not assessable); phi (restart spread not assessable); theta1 (restart spread not assessable); rc4 (restart spread not assessable); a4 (restart spread not assessable).
- Bound-active at the nominal: ['rc1', 'a2', 'a4'].
- Capacity per lane at the nominal (veh/h/lane): G1 3536, G2 1345, G3 2182, G4 2743, B1_head 2162.
- Median model − detector speed 05:00–06:00 (km/h): {'G1': -2.8383246688024215, 'G2': 12.444617671264709, 'G3': 5.1784665317865475, 'G4': 6.411932819919528}.
- Profiles are re-optimised with 600 evaluations per point; under-optimisation can only make a profile look less flat.

| parameter | flat share (J ≤ 1.02 J_best) | min profile J |
|---|---|---|
| vf3 | 0.000 | 0.1697 |
| rc3 | 0.000 | 0.1656 |
| tau | 0.000 | 0.1655 |
| nu | 0.000 | 0.1690 |
| kappa | 0.000 | 0.1674 |
| delta_m | 0.000 | 0.1704 |
| phi | 0.000 | 0.1705 |
| theta1 | 0.000 | 0.1707 |

θ1 profile and the model's B2/B1 merge-section ratio: θ1 0.750: J 0.1718, ratio n/a (n 0); θ1 0.787: J 0.1717, ratio n/a (n 0); θ1 0.825: J 0.1714, ratio n/a (n 0); θ1 0.863: J 0.1713, ratio n/a (n 0); θ1 0.900: J 0.1712, ratio n/a (n 0); θ1 0.938: J 0.1711, ratio n/a (n 0); θ1 0.975: J 0.1709, ratio n/a (n 0); θ1 1.013: J 0.1707, ratio n/a (n 0); θ1 1.050: J 0.1712, ratio n/a (n 0).

## Capacity factors c1, c2 (§4.7)

- c2* = n/a; build check at 0.8: days ['20230118', '20230201', '20230215', '20230315', '20230329', '20230405', '20230503', '20230517', '20230531', '20230607', '20230621', '20230705', '20230802', '20230816', '20230830', '20230920', '20231004', '20231018', '20231101', '20231115', '20231206', '20231220'].
- Estimable: **False** (rules failed: ['iv']); spread used for the stochastic rows: **none**.

## Calibration-day diagnostics (§4.8)

- B1: real-active 22, model-active 22, agreement 1.00; heavy matched 21/22; Q_dis real 3551 vs model 3552 veh/h; r real 1.024 vs model 1.107.
- B2: real-active 9, model-active 2, agreement 0.68; heavy matched 2/9; Q_dis real 3650 vs model 3390 veh/h; r real 0.990 vs model 1.055.
- Merge-section ratio B2/B1: model 0.985 vs real 1.084 on the same 1 days (F8: 1.114).
- θ1 = 0.991. Clipping: max share 0.00000; non-jam v_min floor max 0.00000; in-jam floor max 0.00096 (reported only).
- Origin misfits (days with supply-clipped volume > 1 veh): E15 1.

Benchmarks fixed before validation:

- B1: best daily-demand threshold classifier accuracy 1.000 (every day active: the constant classifier); demand-half climatology p_lower 0.958 (11/11), p_upper 0.958 (11/11), split at 45360 veh.
- B2: best daily-demand threshold classifier accuracy 0.864 (demand >= 46503 veh); demand-half climatology p_lower 0.208 (2/11), p_upper 0.625 (7/11), split at 45360 veh.

## Ensemble candidates (§4.6)

J <= 1.02 J_best, farthest first in normalised (tau, nu, kappa, delta_m, phi); admissibility filter (N0, deterministic rows, stochastic rows) runs at §8.6 step 5 on validation days as a filter only.

- none (no other restart within 1.02 J_best).

## Route stop

**FAIL (N0: step-halving, §2.5); F1 not triggered (N0 is outside the §6.1 set); route stop before any validation run (§0.3, §6.2, §8.6 step 4).** Author decision: accept the route stop as pre-registered (option (a), 2026-10-06).

Step probe on 20230517 (real P_2 episodes [[138, 156]]):
- T = 5.0 s: P_2 episodes [], max qualifying bins in 7 = 4, near misses {'145': 19.51, '147': 19.55, '149': 19.44, '155': 19.46}.
- T = 2.5 s: P_2 episodes [[143, 152]], max qualifying bins in 7 = 5, near misses {}, RMS / max change of the Pioneer Tr speed vs the previous step 3.03 / 32.0 mph.
- T = 1.25 s: P_2 episodes [[143, 150]], max qualifying bins in 7 = 5, near misses {}, RMS / max change of the Pioneer Tr speed vs the previous step 0.68 / 8.2 mph.
- T = 0.625 s: P_2 episodes [[143, 150]], max qualifying bins in 7 = 5, near misses {}, RMS / max change of the Pioneer Tr speed vs the previous step 0.29 / 3.5 mph.

- Everything in this record after the step-halving check (capacity grid, c2*, F-hat, identifiability profiles, §4.8 diagnostics) is post-stop and report-only: it ran on calibration days after the FAIL was known (a driver scheduled before the result) and may not inform any capacity-factor, plant or protocol choice.
- The step-halving FAIL was checked by an adversarial review (4 independent lenses: implementation, simulator time step, event rule, protocol reading; 2026-10-06): none refuted it. The step loop scales every term by T, the event rule is unchanged, and the observation operator does not cause the flip (the decisions are the same with c_s = 1).
- The 5-s plant is not converged in time step inside the B2 queue: finer steps (2.5, 1.25, 0.625 s) agree with each other and keep the 20230517 P_2 episode, while 5 s drops it (step_probe). The FAIL is a numerical defect of the T = 5 s plant, not a threshold artefact around a converged answer.
- Protocol inconsistency disclosed: §5.5 ('reported, not gated') and Appendix A round-1 row 16 still list step-halving as reported (a v1 remnant); §2.5, the §5.3 N0 row, §8.6 step 4 and Appendix C round-3 issue 2 make it gated, and the specific, amended text governs.
- Fix after results (logged, both outcomes): the model-side mask of §5.1 used np.isfinite (it also masked real +inf bins, K = 0); it now masks NaN only, as written. The step-halving check was re-run with the fix; both outcomes are in stephalving_7190016_mask_isfinite.json and stephalving_7190016.json.
- Provenance: the CMA-ES batch was launched at 06:08:58 from commit 663dd62 (the working tree held only untracked files the job does not import); its ledger row carries the commit at append time (9f0e477+dirty), because metanet.py gained diagnostic counters during the run (aaa8b21). J(5 s) in the step-halving run equals the CMA-ES best J bit for bit, so those counters left the dynamics unchanged.
- The capacity-grid batch report counts its 41 jobs as failed: the grid subcommand printed a path instead of a JSON line. All 41 jobs exited with code 0 and wrote their files; the subcommand now prints a JSON line.
- The nominal restart 7190016 is alone in its basin (the other 7 restarts end at J ~ 0.1697). Its tau = 12.0 s is the closest of all restarts to the 2T = 10 s bound (T/tau = 0.42 at 5 s); the fit may partly exploit the 5-s scheme. Choosing another restart now would be post hoc.
- Post-stop lesson (report-only; the explanation is a hypothesis, not tested): the event stations that close the bottleneck pairs sit inside the model's bottleneck cells: Pioneer Tr (S1140, P_1's downstream station) in B1's last cell (30) and Old Shakopee Rd (S1141, P_2's downstream station) in B2's last cell (32). In the capacity grid at c2 = 0.80, B2 is model-active on all 22 days and relocation branch (b) (an episode at Old Shakopee Rd -> T.H.101) fires on 869 of 902 (c1, day) points: S1141 reads the bottleneck cell's queue speeds. At c1 = c2 = 1, branch (a) fires on 6 of 22 days at cell 33 (the E15 merge cell). The same placement may contribute to the model's B2 activity on only 2 of the 9 real-B2 calibration days.

## Disclosures

- The boundary station (Minnetonka Blvd) has no c_s (not in a §3.2.4 group); the observation operator uses c = 1 there. Dropped stations use their computed c_s (§3.2.4).
- Relocation rule (a) is evaluated on 05:00–23:00 bin means (the warm-up hour is excluded).
- Profile flatness is measured as the share of the 8 inter-point intervals whose two end points both have J ≤ 1.02 J_best.
- Censoring points c_low on a non-monotone line fall back to the arg-min component (flagged per day).
- The threshold classifier is evaluated in both directions (demand ≥ t and < t); its Brier score is 1 − accuracy.
