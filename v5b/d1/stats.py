"""Screen D1 Rules 1, 4 and 5 on numbers (pure; no SUMO).

Convention (CLAUDE.md, Statistics): paired seeds, the median of paired differences, 95 % percentile bootstrap,
B = 2,000. Delays: lower is better. For a baseline b and a treatment o, d_i = b_i - o_i (> 0: o better) and
rel = median(d) / median(b); its CI resamples seeds jointly (same index draw for d and b).
"""
from __future__ import annotations

import numpy as np

B_BOOT = 2000
BOOT_SEED = 20261018
T0_MIN_REL = 0.10      # Rule 1 T0: O beats NC by >= 10 %
T1_MAX_TELEPORT_SHARE = 0.05
HF_MIN = 0.10          # Rule 5


def paired(base, treat, B: int = B_BOOT, seed: int = BOOT_SEED) -> dict:
    b, o = np.asarray(base, float), np.asarray(treat, float)
    if b.shape != o.shape or b.size == 0:
        raise ValueError("paired arrays must be non-empty and of equal length")
    d = b - o
    idx = np.random.default_rng(seed).integers(0, b.size, size=(B, b.size))
    md = np.median(d[idx], axis=1)
    mb = np.median(b[idx], axis=1)
    rel_b = md / mb
    med_b = float(np.median(b))
    return {"n": int(b.size), "med_base": med_b, "med_treat": float(np.median(o)), "med_diff": float(np.median(d)),
            "diff_ci": [float(np.percentile(md, 2.5)), float(np.percentile(md, 97.5))],
            "rel": float(np.median(d)) / med_b,
            "rel_ci": [float(np.percentile(rel_b, 2.5)), float(np.percentile(rel_b, 97.5))]}


def t0_check(o, nc) -> dict:
    """Rule 1 T0: rel = median(NC - O) / median(NC) >= 10 % and the CI of the median paired difference > 0."""
    r = paired(nc, o)
    r["pass"] = bool(r["rel"] >= T0_MIN_REL and r["diff_ci"][0] > 0.0)
    return r


def t1_check(teleports) -> dict:
    """Rule 1 T1: share of runs with >= 1 teleport < 5 %."""
    t = np.asarray(teleports)
    share = float(np.mean(t > 0)) if t.size else float("nan")
    return {"n_runs": int(t.size), "n_with_teleports": int(np.sum(t > 0)), "share": share,
            "pass": bool(t.size and share < T1_MAX_TELEPORT_SHARE)}


def headroom_cell(o, fx, rf) -> dict:
    """Rule 5 in one cell: best of FX, RF = the lower median delay (FX on a tie);
    HF = median(best - O) / median(best); pass if HF >= 10 % and the HF CI lower bound > 0."""
    best = "FX" if np.median(fx) <= np.median(rf) else "RF"
    r = paired(fx if best == "FX" else rf, o)
    return {"best": best, "HF": r["rel"], "HF_ci": r["rel_ci"], "med_diff_s": r["med_diff"],
            "diff_ci": r["diff_ci"], "n": r["n"], "med_best": r["med_base"], "med_O": r["med_treat"],
            "pass": bool(r["rel"] >= HF_MIN and r["rel_ci"][0] > 0.0)}


def decide(cells: dict) -> str:
    """Rule 5: CONTINUE if at least one cell passes, else STOP."""
    return "CONTINUE" if any(c["pass"] for c in cells.values()) else "STOP"


def best_rate(medians: dict) -> float:
    """FX tuning: the grid rate with the lowest median delay (the lower rate on a tie)."""
    return float(min(medians, key=lambda r: (medians[r], r)))
