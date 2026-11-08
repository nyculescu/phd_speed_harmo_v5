"""Critic's own loader and round-2 statistic, written from the stated definition."""
import json
import pickle
from pathlib import Path

import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
HERE = Path(__file__).resolve().parent
KEEP_M = {"m_peak_alks", "m_peak_car", "m_peak_truck", "m_dist_m_alks", "m_dist_m_car", "m_dist_m_truck",
          "m_dec_level_s", "m_st_file", "m_cascade_car", "m_events_car"}
GROUPS = {
    "v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"],
    "tail": [f"t{i}" for i in range(5)],
    "sw": [f"s{i}u500" for i in range(5)],
    "bv3": [f"d{i}u500" for i in range(5)],
}


def load(kind):
    p = HERE / f"rows_{kind}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    T = {}
    with open(D / f"rows_{kind}.jsonl") as f:
        for line in f:
            r = json.loads(line)
            r = {k: v for k, v in r.items() if not k.startswith("m_") or k in KEEP_M}
            r.pop("cfg", None)
            cell, arm = r["name"].split("|")
            T.setdefault((cell, arm, float(r["q"])), {})[r["seed"]] = r
    p.write_bytes(pickle.dumps(T))
    return T


def v(r, k):
    x = r.get(k)
    return 0.0 if x is None else float(x)


def arm(T, cell, a, q, f=None):
    """Per seed value: mean over learners for a group, else the single arm. f(row) derives a value."""
    names = GROUPS.get(a, [a])
    rows = [T[(cell, n, q)] for n in names]
    seeds = sorted(set.intersection(*(set(x) for x in rows)))
    out = {}
    for s in seeds:
        out[s] = np.mean([f(x[s]) for x in rows])
    return out


def raw(A, B, sign=-1):
    ds = sorted(set(A) & set(B))
    a = np.array([A[s] for s in ds]); b = np.array([B[s] for s in ds])
    ref = max(float(np.median(b)), 1e-9)
    d = sign * (a - b) / ref * 100
    rng = np.random.default_rng(20261104)
    bs = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
    lo, hi = np.percentile(bs, (2.5, 97.5))
    return round(float(np.median(d)), 2), round(float(lo), 2), round(float(hi), 2), len(ds)


def diff_mean(A, B):
    ds = sorted(set(A) & set(B))
    d = np.array([A[s] - B[s] for s in ds])
    rng = np.random.default_rng(20261104)
    bs = d[rng.integers(0, len(d), (20000, len(d)))].mean(axis=1)
    lo, hi = np.percentile(bs, (2.5, 97.5))
    return round(float(d.mean()), 2), round(float(lo), 2), round(float(hi), 2)


def med(A):
    return float(np.median(list(A.values())))
