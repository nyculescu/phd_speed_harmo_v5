# H1: T1f re-run with the constant-rate grid above the discharge flow (V154, DRAFT)

**Status:** on hold. The design review (V155, `docs/research/reviews/p1c_h1_design_review.md`) found that the slowdown cell cannot test the band above QDF. Do not run this draft.

## 1. Why

V147's T1f tested constant rates of 0.6-1.0 × QDF only (`v5b/p1c/bn4_slow_test.py:44`: 1,150-1,950 veh/h). The grid has three problems:

- A constant meter can gain only if it holds flow **above** the discharge flow (QDF 1,954 veh/h, V147) and below the pre-queue flow (2,106 veh/h, V139). The grid never entered that band.
- The tuning medians fell with every step up the grid (299 → 109 s/veh), and the best rate (1,950) sat on the top edge. T1f had no edge-extension rule; T1g did (V148).
- At the test demand (2,100 veh/h), a 1,950 veh/h meter builds its own queue at about 150 veh/h. That is the same as the breakdown queue it should prevent (2,100 − 1,953 ≈ 147 veh/h).

T1f therefore could not pass as designed. By the CLAUDE.md bug rule, the affected test is re-run and both outcomes are logged. V147 stays in the record.

## 2. What stays fixed (from V146 / V147)

- **Plant:** BN4 with lane changes, the V139 configuration (`zip100`, Krauss, lcCooperative 1.0, speedDev 0.10, step 0.5 s).
- **Actuator:** release-tracking (V141), with r_min = 800 veh/h.
- **Demand:** q_near = 2,100 veh/h.
- **Slowdown incident:** edge 5 at 5 m/s, in the seed-drawn window.
- **Delay:** door-to-door, including depart delay. Runs drain until empty.
- **Pass bar:** the T1f bar (§4).

## 3. What changes

| Item | V147 | H1 |
|---|---|---|
| Constant grid, veh/h | 1,150, 1,350, 1,550, 1,750, 1,950 | 1,150, 1,350, 1,550, 1,750, 1,950, **2,000, 2,050, 2,100, 2,150** |
| Grid edge rule | none | if the best rate is 2,150, add 2,200 and 2,250 once, on the same tuning seeds |
| Tuning seeds | 7,430,160-169 | **7,430,220-229** (fresh, tuning range) |
| Evaluation seeds | 7,430,170-179 (10) | **7,430,640-659** (20, fresh, evaluation range; more power, disclosed) |
| Cells evaluated | slowdown | slowdown (binding) + clean day (report only) |

The clean-day cell is tuned separately, with the same grid and seeds. It tests whether the slowdown, which sits on the final one-lane edge, rather than the meter, sets the result (hypothesis B in the session notes). It does not change the verdict.

The seed ranges are inside the V135 block. They avoid the V153 plan's G2 (100-119), G3 tuning (200-219) and G3 evaluation (600-639) seeds.

## 4. Criteria (fixed before data)

- **Validity (as T1c):** 0 invalid runs, 0 teleports, 0 collisions. Otherwise the run is void and is reported, not interpreted.
- **H1 PASS:** in the slowdown cell, the best tuned constant rate gives rel = median(NC − best) / median(NC) ≥ 10 % over the 20 evaluation seeds. This is the T1f bar. The 95 % percentile bootstrap CI of the median paired difference is reported alongside.
- **H1 FAIL:** rel < 10 %.

**Report** for both cells:
- rel and CI;
- seeds better;
- window TTT;
- served flow;
- the share of runs with a breakdown at the gate's edge-4 loops (V143 detector, from the stored series);
- the full tuning curve.

## 5. Reading, fixed before data

| Outcome | Reading |
|---|---|
| PASS | The V147 KILL came from the grid flaw. Constant metering is alive on this plant. V149 (feedback) stands as measured, and its gap to the constant meter becomes a question to explain. |
| FAIL, best rate > 1,950 | The flaw is fixed, and the KILL stands on stronger evidence. |
| FAIL, best rate ≤ 1,950 | The band above QDF does not help here. The KILL stands. |
| Clean day rel ≥ 10 % but slowdown FAIL | Supports hypothesis B: the incident, not the plant, removes the headroom. This feeds H2 (recurrent congestion without an incident on the bottleneck). |

## 6. Cost and execution

- **Runs:** tuning 10 seeds × 2 cells × (9 rates + NC) = 200, plus at most 40 for the edge rule; evaluation 20 seeds × 2 cells × 2 arms = 80. About 320 runs in total, about 1 min of compute (measured: median 0.8 s per run; T1g's 1,120 runs in 1.7 min).
- **Execution:** from a frozen copy at the run commit, with the CPU guard, in its own systemd user unit. Run once.
- **Code:** a new script `v5b/p1c/h1_grid.py` that reuses `t1checks.job` / `run_jobs`. `bn4_slow_test.py` is unchanged.
