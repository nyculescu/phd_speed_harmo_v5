"""Independent loader and paired statistic for the operating-map verification (written from scratch)."""
import json
from pathlib import Path

import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
KEEP = ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "b7_step", "finished_pct", "dist_step", "dist", "vs", "N",
        "ttc3", "ttc3_s_lo", "ttc3_s_mid", "ttc3_s_hi", "ttc2", "collisions", "teleports", "E30", "out_E30", "arrived", "steps")
ARMS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": [f"t{i}" for i in range(5)],
        "sw": [f"s{i}u500" for i in range(5)], "inc": [f"d{i}u500" for i in range(5)],
        "p333": ["p333"], "3e": ["3e"], "os1": ["os1_15_10"], "nc": ["nc"]}
SIGN = {"all_delay": -1, "ttc_net": -1, "passed": 1, "b3_step": -1, "b45_step": -1, "finished_pct": 1}
SETTINGS = [("s1", "B", 3500.0, "3500"), ("band", "B", 4500.0, "4500"), ("band", "B", 5000.0, "5000"), ("band", "B", 5250.0, "5250"),
            ("test", "X1", 5300.0, "X1"), ("test", "X2", 5300.0, "X2"), ("band", "B", 5500.0, "5500"), ("band", "B", 6000.0, "6000"),
            ("s1", "B", 7000.0, "7000")]


def num(r, k):
    v = r.get(k)
    return 0.0 if v is None else float(v)


def load(kind):
    """T[(name, q)][seed] = dict of kept numeric fields, plus 'pert' = whether pert_log is non-empty."""
    T = {}
    for line in open(D / f"rows_{kind}.jsonl"):
        r = json.loads(line)
        x = {k: num(r, k) for k in KEEP}
        x["pert"] = bool(r.get("pert_log"))
        T.setdefault((r["name"], float(r["q"])), {})[int(r["seed"])] = x
    return T


def arm(T, cell, q, members, key, f=None):
    """Per seed, the mean over learners of key (or of f(row) when f is given); seeds present for every learner."""
    runs = [T[(f"{cell}|{m}", q)] for m in members]
    seeds = sorted(set.intersection(*(set(r) for r in runs)))
    g = f if f is not None else (lambda x: x[key])
    return {s: float(np.mean([g(r[s]) for r in runs])) for s in seeds}


def eff(P, O, sign, B=20000, pct=(2.5, 97.5), seed=20261104):
    """sign * median(P - O) / median(O) * 100, percentile bootstrap over seeds, fixed denominator."""
    ss = sorted(set(P) & set(O))
    p = np.array([P[s] for s in ss])
    o = np.array([O[s] for s in ss])
    ref = max(float(np.median(o)), 1e-9)
    d = sign * (p - o) / ref * 100.0
    idx = np.random.default_rng(seed).integers(0, len(d), (B, len(d)))
    bm = np.median(d[idx], axis=1)
    lo, hi = np.percentile(bm, pct)
    return float(np.median(d)), float(lo), float(hi), len(ss)


def pdiff(P, O, B=20000, pct=(2.5, 97.5), seed=20261104):
    """Median of paired differences P - O in the metric's units, same bootstrap."""
    ss = sorted(set(P) & set(O))
    d = np.array([P[s] - O[s] for s in ss])
    idx = np.random.default_rng(seed).integers(0, len(d), (B, len(d)))
    lo, hi = np.percentile(np.median(d[idx], axis=1), pct)
    return float(np.median(d)), float(lo), float(hi), len(ss)


def verdict(t):
    return "P" if t[1] > 0 else ("O" if t[2] < 0 else "=")
