"""v5.B daily demand (design B6/B7, author 2026-10-13): a synthetic commuter M fitted to a real MnDOT weekday, with
day-to-day noise, over the day window 06:00-19:00 (simulation t = 0 at 06:00).

Shape: the fitted model in docs/v5b/data/mndot_us169sb_s460_weekday.json (US-169 SB station S460, median of 156
Tue-Thu weekdays 2023; relative RMSE 2.6 %):
    f(t) = base + plateau * sig((t - t_on)/w_on) * sig((t_off - t)/w_off) + A_am N(mu_am, s_am) + A_pm N(mu_pm, s_pm)
normalised so that the noise-free day peaks at 1, then scaled to `q_peak` veh/h.

Day-to-day noise (every day differs; `noise` scales all of it, 0 = the nominal day). PROVISIONAL magnitudes, to be fixed
in the v5.B protocol and raised later for stress tests:
    peak times      mu += N(0, 10 min)                 peak heights   A  *= exp(N(0, 0.08))
    peak widths     s  *= exp(N(0, 0.10))              day level      plateau *= exp(N(0, 0.05))
    slow wander     per-bin multiplicative AR(1), rho 0.8, sd 0.04 (5-min bins)
Arrivals within a bin stay Poisson (vsl_lab/sim/demand.py), so two days with the same profile still differ.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

SHAPE_FILE = Path(__file__).resolve().parents[2] / "docs/v5b/data/mndot_us169sb_s460_weekday.json"
T0_H, T1_H = 6.0, 19.0
DAY_S = (T1_H - T0_H) * 3600.0
NOISE = {"mu_min": 10.0, "A": 0.08, "s": 0.10, "plateau": 0.05, "ar_rho": 0.8, "ar_sd": 0.04}


def fit_params() -> dict:
    return dict(json.loads(SHAPE_FILE.read_text())["fit"])


def _f(p: dict, t_h: float) -> float:
    sig = lambda z: 1.0 / (1.0 + math.exp(-z))  # noqa: E731
    return (p["base"] + p["plateau"] * sig((t_h - p["t_on_h"]) / p["w_on_h"]) * sig((p["t_off_h"] - t_h) / p["w_off_h"])
            + p["A_am"] * math.exp(-0.5 * ((t_h - p["mu_am_h"]) / p["s_am_h"]) ** 2)
            + p["A_pm"] * math.exp(-0.5 * ((t_h - p["mu_pm_h"]) / p["s_pm_h"]) ** 2))


def _norm(p: dict) -> float:
    return max(_f(p, T0_H + k / 60.0) for k in range(int((T1_H - T0_H) * 60) + 1))


def day_params(rng: np.random.Generator, noise: float = 1.0) -> dict:
    p = fit_params()
    n = NOISE
    p["mu_am_h"] += rng.normal(0, n["mu_min"] / 60.0) * noise
    p["mu_pm_h"] += rng.normal(0, n["mu_min"] / 60.0) * noise
    p["A_am"] *= math.exp(rng.normal(0, n["A"]) * noise)
    p["A_pm"] *= math.exp(rng.normal(0, n["A"]) * noise)
    p["s_am_h"] *= math.exp(rng.normal(0, n["s"]) * noise)
    p["s_pm_h"] *= math.exp(rng.normal(0, n["s"]) * noise)
    p["plateau"] *= math.exp(rng.normal(0, n["plateau"]) * noise)
    return p


def day_profile(rng: np.random.Generator, q_peak: float, noise: float = 1.0, step: float = 300.0) -> list:
    """[(t0, t1, veh/h)] over [0, DAY_S), t = 0 at 06:00. Scaled by the NOMINAL day's peak, so a noisy day can peak a
    little above or below q_peak."""
    nominal = _norm(fit_params())
    p = day_params(rng, noise)
    out, ar = [], 0.0
    n_bins = int(round(DAY_S / step))
    sd = NOISE["ar_sd"] * noise
    for k in range(n_bins):
        ar = NOISE["ar_rho"] * ar + rng.normal(0, sd * math.sqrt(1 - NOISE["ar_rho"] ** 2))
        t_h = T0_H + (k + 0.5) * step / 3600.0
        q = q_peak * _f(p, t_h) / nominal * math.exp(ar)
        out.append((k * step, (k + 1) * step, max(q, 0.0)))
    return out
