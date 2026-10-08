# Hidden-demand check (D4.12; pre-registration `demand_check_prereg.md`)

**Signal "worth writing v5": YES.** Calibration days: 22.

| bottleneck | mode | heavy days | share with excess ≥ 15 min | median excess (min) | median peak A/Q_dis | inactive days with overload |
|---|---|---|---|---|---|---|
| B1 | R | 22 | 1.0 | 60.0 | 1.09 | 0/0 |
| B1 | R-NL | 22 | 1.0 | 60.0 | 1.095 | 0/0 |
| B1 | R-NL+Q | 22 | 1.0 | 75.0 | 1.1 | 0/0 |
| B2 | R | 9 | 1.0 | 60.0 | 1.064 | 13/13 |
| B2 | R-NL | 9 | 1.0 | 105.0 | 1.124 | 13/13 |
| B2 | R-NL+Q | 9 | 1.0 | 105.0 | 1.147 | 13/13 |

## Reading (2026-10-07)

- **Signal: YES as pre-registered, but not informative.** The reported sanity row shows that arrivals exceed the median heavy-day discharge on all 13 B2-inactive days too. "A_b > Q_dis" therefore does not separate jam days from free days. That is consistent with a stochastic pre-breakdown capacity above the post-breakdown discharge.
- **Even plain served counts (mode R) overload the real discharge on every heavy day** (median peak 1.09× at B1, 1.06× at B2). Hidden demand is therefore **not** the main reason the v4 fit never jams; this replaces the D4.11 diagnosis (an inference).

## Follow-up diagnostic (report-only; calibration days; v4 nominal plant with only rho_cr,G3 changed)

| G3 capacity per lane | J | NRMSE q / v / v-congestion | model B1 jam days | model B2 jam days |
|---|---|---|---|---|
| 3,066 (fitted) | 0.178 | 0.070 / 0.123 / 0.260 | 1 | 0 |
| 2,400 | 0.187 | 0.071 / 0.127 / 0.274 | 1 | 0 |
| 2,100 | 0.224 | 0.078 / 0.146 / 0.337 | 8 | 0 |
| 1,900 | 0.455 | 0.235 / 0.314 / 0.635 | 21 | 0 |

The real counts are 22 B1 and 9 B2 jam days.

As the capacity approaches the real discharge, the model jams at B1 on most days, but J more than doubles: the jams come at the wrong times and places. B2 never jams, because the B1 queue holds the flow back.

Inference (not proved; the other parameters were held fixed): the RMSE-based objective penalises a mistimed jam twice and so favours a never-jamming plant. A demand uplift would not change that.
