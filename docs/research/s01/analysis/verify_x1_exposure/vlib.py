"""Own loader and statistics for the verification (written from scratch)."""
import json
from collections import defaultdict

import numpy as np

D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote"
DT = 0.1
ARMS = {
    "v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"],
    "tail": [f"t{i}" for i in range(5)],
    "sw": [f"s{i}u500" for i in range(5)],
    "inc": [f"d{i}u500" for i in range(5)],
    "nc": ["nc"], "p333": ["p333"], "3e": ["3e"], "os1_15_10": ["os1_15_10"],
}
SPECIAL = {"X1": "3ex1", "X2": "3ex2"}
BANDS = ("lo", "mid", "hi")


def arms_for(cell):
    a = dict(ARMS)
    a["3ex"] = [SPECIAL[cell]]
    return a


def derive(r):
    """Per-row derived exposures from the step speed histograms (5 km/h bins, all classes)."""
    vh = np.sum([np.array(r[f"m_vh_{c}"], float) for c in ("car", "alks", "truck")], axis=0) * DT
    r["e_tot"] = vh.sum()
    r["e_stop5"] = vh[0]
    r["e_lo"] = vh[0] + vh[1] + vh[2] + 0.6 * vh[3]
    r["e_mid"] = 0.4 * vh[3] + vh[4] + vh[5] + vh[6] + 0.2 * vh[7]
    r["e_hi"] = 0.8 * vh[7] + vh[8:].sum()
    r["_vh"] = vh
    return r


def load(fname="rows_test.jsonl"):
    T = defaultdict(dict)
    with open(f"{D}/{fname}") as f:
        for line in f:
            r = json.loads(line)
            T[r["name"]][r["seed"]] = derive(r)
    return T


def g(r, k):
    v = r.get(k)
    return 0.0 if v is None else v


def per_seed(T, cell, arm, fn):
    """Arm value per seed: mean over learners of fn(row)."""
    names = [f"{cell}|{n}" for n in arms_for(cell)[arm]]
    seeds = sorted(set.intersection(*(set(T[n]) for n in names)))
    return seeds, np.array([np.mean([fn(T[n][s]) for n in names]) for s in seeds])


def field(k):
    return lambda r: float(g(r, k))


def boot_idx(n, B=20000):
    return np.random.default_rng(20261104).integers(0, n, (B, n))


def effect(p, o, sign=-1, pct=(2.5, 97.5)):
    """sign x median(P - O) / median(O) x 100 with a percentile bootstrap of the median; denominator fixed."""
    ref = max(float(np.median(o)), 1e-9)
    d = sign * (p - o) / ref * 100.0
    idx = boot_idx(len(d))
    lo, hi = np.percentile(np.median(d[idx], axis=1), pct)
    return float(np.median(d)), float(lo), float(hi)


def mean_ci(d, pct=(2.5, 97.5)):
    d = np.asarray(d, float)
    idx = boot_idx(len(d))
    lo, hi = np.percentile(d[idx].mean(axis=1), pct)
    return float(d.mean()), float(lo), float(hi)


def med_ci(d, pct=(2.5, 97.5)):
    d = np.asarray(d, float)
    idx = boot_idx(len(d))
    lo, hi = np.percentile(np.median(d[idx], axis=1), pct)
    return float(np.median(d)), float(lo), float(hi)


def fmt(t, nd=1):
    return f"{t[0]:+.{nd}f} [{t[1]:+.{nd}f}, {t[2]:+.{nd}f}]"
