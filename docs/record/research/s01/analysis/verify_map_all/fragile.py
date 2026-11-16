import pickle, json
import numpy as np
T, src = pickle.load(open("rows.pkl", "rb"))
M = json.load(open("mine.json"))
exec(open("calc.py").read().split("cells = ")[0].split("T, src = ")[0])
exec("def _x(): pass")
ARMS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": [f"t{i}" for i in range(5)], "sw": [f"s{i}u500" for i in range(5)]}
MET = {"delay": ("all_delay", -1), "cf": ("ttc_net", -1), "flow": ("passed", 1), "b3": ("b3_step", -1), "b45": ("b45_step", -1)}
def v(r, k):
    x = r.get(k); return 0.0 if x is None else float(x)
def arm_rows(cell, q, names):
    rows = [T[(f"{cell}|{n}", q)] for n in names]
    return {s: {k: float(np.mean([v(r[s], k) for r in rows])) for k, _ in MET.values()} for s in rows[0]}
def rule_rows(cell, q, n):
    return {s: {k: v(r, k) for k, _ in MET.values()} for s, r in T[(f"{cell}|{n}", q)].items()}
mk = lambda lo, hi: "A" if lo > 0 else ("R" if hi < 0 else "=")
near = []
for c in M:
    for k, (e, lo, hi) in M[c]["eff"].items():
        if min(abs(lo), abs(hi)) < 0.05:
            near.append((c, k, e, lo, hi))
print("bounds within 0.05 of 0:", len(near))
for c, k, e, lo, hi in near:
    cell, q = c.split("|"); q = float(q)
    a, r, m = k.split("|")
    A, B = arm_rows(cell, q, ARMS[a]), rule_rows(cell, q, r)
    key, sg = MET[m]
    ds = sorted(A)
    ref = max(float(np.median([B[s][key] for s in ds])), 1e-9)
    d = np.array([sg * (A[s][key] - B[s][key]) / ref * 100 for s in ds])
    marks = []
    for sd in range(100):
        rng = np.random.default_rng(1000 + sd)
        lo2, hi2 = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), (2.5, 97.5))
        marks.append(mk(lo2, hi2))
    base = mk(lo, hi)
    flips = sum(x != base for x in marks)
    print(f"{c} {k}: {e:+.3f} [{lo:+.4f}, {hi:+.4f}] {base}  flips in 100 rng seeds: {flips} -> {sorted(set(marks))}")
