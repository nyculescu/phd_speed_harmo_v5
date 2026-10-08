# U.S.169 SB METANET plant v4: calibration freeze

Protocol: `docs/plans/day_pattern_metanet_protocol_v4.md` (v4, binding). Stage: freeze (before any validation run). Variant `v4` (§A1, step (b), 39 cells), T = 0.75 s. pycma 4.5.0. Calibration days only: 22 usable. Raw runs: `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v4`; full numbers in `metanet_v4_calibration.json`.

**Route after the freeze: STOP (no usable spread at the freeze (none (deterministic-only); rules failed ['i', 'ii', 'iii']; §A6 (7)(b))).**

## Fit (§4.3–4.4)

- Nominal plant: restart seed 7191013, J = 0.1780 (continued to 8,000 evaluations: False).
- J terms (mean over days): NRMSE_q 0.070, NRMSE_v 0.123, NRMSE_v congestion 0.260; v0 whole-day J 0.096.

| seed | evals | best J | inadmissible evals | improvement last 20 % |
|---|---|---|---|---|
| 7191010 | 4008 | 0.1795 | 409 | 0.0089 |
| 7191011 | 4008 | 0.1797 | 409 | 0.0070 |
| 7191012 | 4008 | 0.1784 | 208 | 0.0026 |
| 7191013 | 4008 | 0.1780 | 144 | 0.0011 |
| 7191014 | 4008 | 0.1786 | 321 | 0.0006 |
| 7191015 | 4008 | 0.1786 | 308 | 0.0038 |
| 7191016 | 4008 | 0.1784 | 351 | 0.0006 |
| 7191017 | 4008 | 0.1787 | 266 | 0.0062 |

Frozen parameters: vf1 = 111.1, vf2 = 107.4, vf3 = 124.3, rc1 = 31.11, rc2 = 24.05, rc3 = 40.51, a1 = 2.589, a2 = 2.168, a3 = 2.018, tau = 55.12, nu = 90, kappa = 30.81, delta_m = 1.071, phi = 3.988, theta1 = 0.9737, rc4 = 33.14, a4 = 2.443.

## Step-halving (§2.5; gated as part of N0)

J(T = 0.75 s) = 0.1780, J(T/2) = 0.1780, relative change 0.0001 (limit 0.05); P_1/P_2 episode-day sets unchanged: True; largest per-station RMS speed change 0.43 km/h. **PASS**. Differing days: none.

## P11-k queue backing at the freeze (§A12; gated)

Tolerance 3 unbacked days over 22 days. B1: unbacked 1, pooled backed share 0.115; B2: unbacked 0, pooled backed share n/a. **PASS**.

## Speed at capacity (§A3)

- At the nominal: G1 v_c − thr = 0.25 km/h (A3-active), G2 v_c − thr = 0.04 km/h (A3-active), G3 v_c − thr = 11.33 km/h, G4 v_c − thr = 9.59 km/h.
- Per restart: 7191010: A3-inadmissible 751, first feasible eval 16; 7191011: A3-inadmissible 755, first feasible eval 4; 7191012: A3-inadmissible 581, first feasible eval 27; 7191013: A3-inadmissible 565, first feasible eval 13; 7191014: A3-inadmissible 459, first feasible eval 9; 7191015: A3-inadmissible 519, first feasible eval 2; 7191016: A3-inadmissible 438, first feasible eval 15; 7191017: A3-inadmissible 612, first feasible eval 16.

## Identifiability (§4.5; reported, not gated)

- Near-best restarts (J ≤ 1.02 J_best): 8 ([7191010, 7191011, 7191012, 7191013, 7191014, 7191015, 7191016, 7191017]).
- Non-identifiable: a3 (restart range >= 50 % of the bound); kappa (restart range >= 50 % of the bound); delta_m (restart range >= 50 % of the bound); theta1 (restart range >= 50 % of the bound); rc4 (restart range >= 50 % of the bound).
- Bound-active at the nominal: ['nu', 'phi'].
- Capacity per lane at the nominal (veh/h/lane): G1 2350, G2 1629, G3 3066, G4 2735, B1_head 2986.
- Median model − detector speed 05:00–06:00 (km/h): {'G1': -0.711656436050923, 'G2': 2.8330124720039436, 'G3': 0.7226737798507514, 'G4': 8.529029272832332}.
- Profiles are re-optimised with 600 evaluations per point; under-optimisation can only make a profile look less flat.

| parameter | flat share (J ≤ 1.02 J_best) | min profile J |
|---|---|---|
| vf3 | 0.000 | n/a |
| rc3 | 0.000 | n/a |
| tau | 0.000 | n/a |
| nu | 0.000 | n/a |
| kappa | 0.000 | n/a |
| delta_m | 0.000 | n/a |
| phi | 0.000 | n/a |
| theta1 | 0.000 | n/a |

θ1 profile and the model's B2/B1 merge-section ratio: .

## Capacity factors c1, c2 (§4.7)

- c2* = 1.20; build check at None: days [].
- Estimable: **False** (rules failed: ['i', 'ii', 'iii']); spread used for the stochastic rows: **none (deterministic-only)**.
- B1: 1 exact, 0 censored; KM median 1.00, upper atom 0.000, mass < 1 0.000, > 1 0.000; Tobit μ n/a, σ n/a (usable False).
- B2: 0 exact, 1 censored; KM median 1.20, upper atom 1.000, mass < 1 0.000, > 1 1.000; Tobit μ n/a, σ n/a (usable False).
- Non-reproducible days: 21 (share of real-active days 0.955); non-monotone day-lines: 0.

## Calibration-day diagnostics (§4.8)

- B1: real-active 22, model-active 1, agreement 0.05; heavy matched 1/22; Q_dis real 3674 vs model 3707 veh/h; r real 0.985 vs model 1.087.
- B2: real-active 9, model-active 0, agreement 0.59; heavy matched 0/9; Q_dis real n/a vs model n/a veh/h; r real n/a vs model n/a.
- Merge-section ratio B2/B1: model n/a vs real n/a on the same 0 days (F8: 1.114).
- θ1 = 0.974. Clipping: max share 0.00015; non-jam v_min floor max 0.00000; in-jam floor max 0.00000 (reported only).
- Origin misfits (days with supply-clipped volume > 1 veh): .

Benchmarks fixed before validation:

- B1: best daily-demand threshold classifier accuracy 1.000 (every day active: the constant classifier); demand-half climatology p_lower 0.958 (11/11), p_upper 0.958 (11/11), split at 45360 veh.
- B2: best daily-demand threshold classifier accuracy 0.864 (demand >= 46503 veh); demand-half climatology p_lower 0.208 (2/11), p_upper 0.625 (7/11), split at 45360 veh.

## Ensemble candidates (§4.6)

J <= 1.02 J_best, farthest first in normalised (tau, nu, kappa, delta_m, phi); admissible iff step-halving and P11-k pass on calibration days (recorded here) and N0, P11-k, deterministic and stochastic rows pass on validation days at §8.6 step 5 (a filter only, never a route stop).

- seed 7191016: J 0.1784, distance 0.648, step-halving None.
- seed 7191010: J 0.1795, distance 0.563, step-halving None.
- seed 7191017: J 0.1787, distance 0.331, step-halving None.
- seed 7191011: J 0.1797, distance 0.310, step-halving None.
- seed 7191015: J 0.1786, distance 0.245, step-halving None.
- seed 7191012: J 0.1784, distance 0.210, step-halving None.
- seed 7191014: J 0.1786, distance 0.184, step-halving None.

## Route stop

**STOP (no usable spread at the freeze (none (deterministic-only); rules failed ['i', 'ii', 'iii']; §A6 (7)(b))).** Reasons: no usable spread at the freeze (none (deterministic-only); rules failed ['i', 'ii', 'iii']; §A6 (7)(b)).


## Not run (disclosed)

- identifiability profiles (§4.5) and the ensemble candidates' step-halving and capacity grids (§4.6); the route-deciding checks (step-halving, P11-k, the nominal capacity grid, F-hat) were complete. Reason: author decision 2026-10-07 (D4.11): batch stopped after the route-deciding checks showed a stop at the freeze; the remaining items could not change the route.

## Notes (protocol v4)

- Protocol v4 (docs/plans/day_pattern_metanet_protocol_v4.md) = v3 + amendments §A1-§A14; disclosures §A11: v4 reopens the METANET route stopped by v3 (a disclosed deviation, D4.9 V6); plant selected after 2 attempts.
- The §A1 B-set rule eases relocation (b), rule (iv) and F-hat estimability, and shrinks F1's domain (§A11 item 2).
- Calibration days are used a second time; every calibration-day diagnostic here is in-sample (§A11 item 3).

## Disclosures

- The boundary station (Minnetonka Blvd) has no c_s (not in a §3.2.4 group); the observation operator uses c = 1 there. Dropped stations use their computed c_s (§3.2.4).
- Relocation rule (a) is evaluated on 05:00–23:00 bin means (the warm-up hour is excluded).
- Profile flatness is measured as the share of the 8 inter-point intervals whose two end points both have J ≤ 1.02 J_best.
- Censoring points c_low on a non-monotone line fall back to the arg-min component (flagged per day).
- The threshold classifier is evaluated in both directions (demand ≥ t and < t); its Brier score is 1 − accuracy.
