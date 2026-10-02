"""Paired statistics (one convention everywhere): median of paired differences with a
95 % percentile bootstrap CI. Written fresh for the lab (roadmap §0)."""
from __future__ import annotations

import numpy as np


def paired_median_diff(a, b, n_boot: int = 10_000, seed: int = 0, alpha: float = 0.05) -> dict:
    """Median of (b - a) over pairs, with a percentile-bootstrap CI over pairs."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    assert a.shape == b.shape and a.ndim == 1 and len(a) > 0
    d = b - a
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    boots = np.median(d[idx], axis=1)
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return {"median_diff": float(np.median(d)), "ci_lo": float(lo), "ci_hi": float(hi), "n": int(len(d)),
            "excludes_0": bool(lo > 0 or hi < 0)}


def rel(x: float, ref: float) -> float:
    return float(x / ref) if ref else float("nan")
