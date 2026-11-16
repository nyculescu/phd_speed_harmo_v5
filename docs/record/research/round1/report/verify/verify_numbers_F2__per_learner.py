import json, sys, itertools
import numpy as np
p = sys.argv[1]
rows = [json.loads(l) for l in open(p)]
T = {}
for r in rows:
    T.setdefault(r["name"], {})[r["seed"]] = r
def rel(a, b, key):
    ds = sorted(set(T[a]) & set(T[b]))
    ref = np.median([T[b][s][key] for s in ds])
    d = np.array([-(T[a][s][key] - T[b][s][key]) / ref * 100 for s in ds])
    return float(np.median(d))
for cell in ("X1", "X2"):
    # arm mean incumbent per seed
    inc = {s: np.mean([T[f"{cell}|d{i}"][s]["all_delay"] for i in range(5)]) for s in T[f"{cell}|d0"]}
    med_inc = np.median(list(inc.values()))
    print(cell)
    for pre in ("d", "w", "f"):
        vals = []
        for i in range(5):
            A = T[f"{cell}|{pre}{i}"]
            d = np.median([-(A[s]["all_delay"] - inc[s]) / med_inc * 100 for s in A])
            vals.append(d)
        print(" ", pre, "per-learner delay gain vs incumbent arm mean (%):", [round(v, 1) for v in vals])
    # per-learner mean delay
    for pre in ("d", "w"):
        print(" ", pre, "mean delay per learner:", [round(float(np.mean([T[f"{cell}|{pre}{i}"][s]["all_delay"] for s in T[f"{cell}|{pre}{i}"]])), 2) for i in range(5)])
    # rank test: all v3w learners better than all baseline-v3 learners?
    wm = [np.mean([T[f"{cell}|w{i}"][s]["all_delay"] for s in T[f"{cell}|w{i}"]]) for i in range(5)]
    dm = [np.mean([T[f"{cell}|d{i}"][s]["all_delay"] for s in T[f"{cell}|d{i}"]]) for i in range(5)]
    U = sum(1 for a in wm for b in dm if a < b)
    # exact permutation p (one-sided) on U
    allv = wm + dm
    cnt = 0; tot = 0
    for comb in itertools.combinations(range(10), 5):
        g = [allv[k] for k in comb]; h = [allv[k] for k in range(10) if k not in comb]
        u = sum(1 for a in g for b in h if a < b); tot += 1; cnt += u >= U
    print("  Mann-Whitney U (w<d) =", U, "of 25; exact one-sided p =", round(cnt / tot, 4))
