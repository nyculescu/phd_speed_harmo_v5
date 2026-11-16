"""C-D5 statistic on derived keys (read only): per learner median paired % diff vs opponent, mean of 5, joint seed bootstrap."""
import sys
import numpy as np
import pandas as pd
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
import os
df = pd.read_pickle(os.environ.get("ROWS", os.path.join(os.path.dirname(__file__), "rows.pkl")))
seeds = sorted(df.seed.unique())
n = len(seeds)
B = int(os.environ.get("B", "20000"))
IDX = np.random.default_rng(20261108).integers(0, n, (B, n))
P975 = (1.25, 98.75)
T = {a: g.set_index("seed").loc[seeds] for a, g in df.groupby("arm")}

def col(a, f):
    g = T[a]
    return f(g).to_numpy(dtype=float) if callable(f) else g[f].to_numpy(dtype=float)

def edge(opp, f):
    O = col(opp, f)
    m = max(float(np.median(O)), 1e-12)
    D = [-(col(w, f) - O) / m * 100.0 for w in V3W]
    pt = float(np.mean([np.median(d) for d in D]))
    b = np.mean([np.median(d[IDX], axis=1) for d in D], axis=0)
    lo, hi = np.percentile(b, P975)
    return pt, float(lo), float(hi)

def fmt(x):
    return f"{x[0]:+6.1f} [{x[1]:+6.1f},{x[2]:+6.1f}]"
