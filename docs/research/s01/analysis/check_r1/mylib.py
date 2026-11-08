"""Independent loader and round-2 statistic for the round-1 check."""
import json, pickle
from pathlib import Path
import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
HERE = Path(__file__).resolve().parent
KEYS = ["all_delay", "ttc_net", "passed", "b3_step", "b45_step", "finished_pct",
        "m_peak_alks", "m_peak_car", "m_peak_truck"]
G = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"],
     "tail": [f"t{i}" for i in range(5)], "sw": [f"s{i}u500" for i in range(5)],
     "bv3": [f"d{i}u500" for i in range(5)]}


def load():
    p = HERE / "rows.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    T = {}
    for kind in ("test", "band", "s1"):
        with open(D / f"rows_{kind}.jsonl") as f:
            for line in f:
                r = json.loads(line)
                cell, a = r["name"].split("|")
                q = int(float(r["q"]))
                T.setdefault((cell, a, q), {})[int(r["seed"])] = {k: r.get(k) for k in KEYS}
    p.write_bytes(pickle.dumps(T))
    return T


def val(r, k):
    if callable(k):
        return k(r)
    x = r.get(k)
    return 0.0 if x is None else float(x)


def arm(T, cell, a, q, k):
    names = G.get(a, [a])
    rows = [T[(cell, n, q)] for n in names]
    seeds = sorted(set.intersection(*(set(x) for x in rows)))
    return {s: float(np.mean([val(x[s], k) for x in rows])) for s in seeds}


def eff(A, B, sign=-1, pct=(2.5, 97.5)):
    ds = sorted(set(A) & set(B))
    a = np.array([A[s] for s in ds]); b = np.array([B[s] for s in ds])
    ref = max(float(np.median(b)), 1e-9)
    d = sign * (a - b) / ref * 100
    rng = np.random.default_rng(20261104)
    bs = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
    lo, hi = np.percentile(bs, pct)
    return float(np.median(d)), float(lo), float(hi), len(ds)


def mdiff(A, B, sign=1):
    ds = sorted(set(A) & set(B))
    d = sign * np.array([A[s] - B[s] for s in ds])
    rng = np.random.default_rng(20261104)
    bs = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
    lo, hi = np.percentile(bs, (2.5, 97.5))
    return float(np.median(d)), float(lo), float(hi), len(ds)


def fmt(t):
    return f"{t[0]:+.1f} [{t[1]:+.1f}, {t[2]:+.1f}] n={t[3]}"
