"""Loader and round-2 statistic, written fresh for the round-2 check of revision 3."""
import json, pickle
from pathlib import Path
import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
HERE = Path(__file__).resolve().parent
KEYS = ["all_delay", "ttc_net", "passed", "b3_step", "b45_step", "finished_pct", "E30", "out_E30",
        "m_peak_alks", "m_peak_car", "m_peak_truck"]
GROUPS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"],
          "tail": [f"t{i}" for i in range(5)], "sw": [f"s{i}u500" for i in range(5)],
          "bv3": [f"d{i}u500" for i in range(5)]}
DRL = {n for g in GROUPS.values() for n in g}


def load():
    p = HERE / "rows2.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    T = {}
    for kind in ("test", "band", "s1"):
        with open(D / f"rows_{kind}.jsonl") as f:
            for line in f:
                r = json.loads(line)
                cell, a = r["name"].split("|")
                q = int(round(float(r["q"])))
                key = ("T" if cell in ("X1", "X2") else "B", cell, a, q)
                T.setdefault((cell, a, q), {})[int(r["seed"])] = {k: r.get(k) for k in KEYS}
    p.write_bytes(pickle.dumps(T))
    return T


def v(r, k):
    if callable(k):
        return float(k(r))
    x = r.get(k)
    return 0.0 if x is None else float(x)


def arm(T, cell, a, q, k):
    names = GROUPS.get(a, [a])
    rows = [T[(cell, n, q)] for n in names]
    seeds = sorted(set.intersection(*(set(x) for x in rows)))
    return {s: float(np.mean([v(x[s], k) for x in rows])) for s in seeds}


def boot(d, pct=(2.5, 97.5)):
    rng = np.random.default_rng(20261104)
    bs = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
    lo, hi = np.percentile(bs, pct)
    return float(lo), float(hi)


def eff(P, O, sign, pct=(2.5, 97.5)):
    """sign * median(P - O) / median(O) * 100 with its percentile bootstrap."""
    s = sorted(set(P) & set(O))
    p = np.array([P[x] for x in s]); o = np.array([O[x] for x in s])
    d = sign * (p - o) / float(np.median(o)) * 100
    lo, hi = boot(d, pct)
    return float(np.median(d)), lo, hi, len(s)


def mdiff(P, O, sign=1, pct=(2.5, 97.5)):
    s = sorted(set(P) & set(O))
    d = sign * np.array([P[x] - O[x] for x in s])
    lo, hi = boot(d, pct)
    return float(np.median(d)), lo, hi, len(s)


def f1(t, nd=1):
    return f"{t[0]:+.{nd}f} [{t[1]:+.{nd}f}, {t[2]:+.{nd}f}]"
