"""Screen D1 Rules 1, 4 and 5 and Addendum (2026-10-19) A2, A5 on numbers (pure; no SUMO).

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


RULE5_SET = ("FX", "RF")   # the page's Rule 5 "best of FX, RF" (by median delay, FX on a tie): reported


def _hf(base, o) -> dict:
    r = paired(base, o)
    return {"HF": r["rel"], "HF_ci": r["rel_ci"], "med_diff_s": r["med_diff"], "diff_ci": r["diff_ci"],
            "med": r["med_base"], "pass": bool(r["rel"] >= HF_MIN and r["rel_ci"][0] > 0.0)}


def headroom_cell(o, fallbacks: dict) -> dict:
    """Rule 5 with Addendum (2026-10-19) A2, in one cell. For every fallback f (FX, RF, HL):
    HF_f = median(f - O) / median(f); the cell passes only if HF_f >= 10 % and its CI lower bound > 0 against
    EVERY fallback. The page's Rule 5 HF against the best of FX, RF (lower median delay) is reported as 'HF'."""
    o = np.asarray(o, float)
    per = {a: _hf(x, o) for a, x in fallbacks.items()}
    rule5 = [a for a in RULE5_SET if a in fallbacks] or list(fallbacks)
    best = min(rule5, key=lambda a: (float(np.median(fallbacks[a])), rule5.index(a)))
    binding = min(per, key=lambda a: (per[a]["HF_ci"][0], a))
    return {"n": int(o.size), "med_O": float(np.median(o)), "per_fallback": per,
            "best": best, "HF": per[best]["HF"], "HF_ci": per[best]["HF_ci"], "med_best": per[best]["med"],
            "med_diff_s": per[best]["med_diff_s"], "diff_ci": per[best]["diff_ci"], "rule5_pass": per[best]["pass"],
            "binding": binding, "pass": all(p["pass"] for p in per.values())}


def cell_with_invalid_check(o, fallbacks: dict, invalid) -> dict:
    """Addendum (2026-10-19) A5: if any O or fallback run of a seed is invalid, the cell is also computed without
    those seeds; it passes only if it passes both with and without them (no valid seed left: it fails)."""
    inv = np.asarray(invalid, bool)
    c = headroom_cell(o, fallbacks)
    c["n_invalid_seeds"] = int(inv.sum())
    c["pass_all_seeds"] = c["pass"]
    c["valid_only"] = None
    if not inv.any():
        c["pass_valid_only"] = c["pass"]
    elif inv.all():
        c["pass_valid_only"] = False
    else:
        keep = ~inv
        v = headroom_cell(np.asarray(o, float)[keep], {a: np.asarray(x, float)[keep] for a, x in fallbacks.items()})
        c["valid_only"] = v
        c["pass_valid_only"] = v["pass"]
    c["pass"] = bool(c["pass_all_seeds"] and c["pass_valid_only"])
    return c


def decide(cells: dict) -> str:
    """Rule 5: CONTINUE if at least one cell passes, else STOP."""
    return "CONTINUE" if any(c["pass"] for c in cells.values()) else "STOP"


def best_rate(medians: dict) -> float:
    """FX tuning: the grid rate with the lowest median delay (the lower rate on a tie)."""
    return float(min(medians, key=lambda r: (medians[r], r)))
