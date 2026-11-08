import pickle
import numpy as np
T, src = pickle.load(open("rows.pkl", "rb"))
ARMS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": [f"t{i}" for i in range(5)]}
MET = {"delay": ("all_delay", -1), "flow": ("passed", 1), "b3": ("b3_step", -1)}
def v(r, k):
    x = r.get(k); return 0.0 if x is None else float(x)
cases = [("B", 3500.0, "v3w", "3e", "flow"), ("B", 4500.0, "v3w", "3e", "delay"), ("B", 5000.0, "v3w", "os1_15_10", "flow"),
         ("B", 5250.0, "tail", "3e", "flow"), ("X2", 5300.0, "v3w", "lr400_16_1", "b3")]
for cell, q, a, r, m in cases:
    key, sg = MET[m]
    rows = [T[(f"{cell}|{n}", q)] for n in ARMS[a]]
    B = T[(f"{cell}|{r}", q)]
    ds = sorted(B)
    A = {s: np.mean([v(x[s], key) for x in rows]) for s in ds}
    ref = max(float(np.median([v(B[s], key) for s in ds])), 1e-9)
    d = np.array([sg * (A[s] - v(B[s], key)) / ref * 100 for s in ds])
    bs = np.median(d[np.random.default_rng(20261104).integers(0, len(d), (20000, len(d)))], axis=1)
    out = {p: tuple(round(x, 3) for x in np.percentile(bs, (p, 100 - p))) for p in (2.5, 1.25, 0.5)}
    print(cell, q, a, r, m, out)
