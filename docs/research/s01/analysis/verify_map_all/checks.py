import pickle, json
import numpy as np
def v(r, k):
    x = r.get(k)
    return 0.0 if x is None else float(x)
T, src = pickle.load(open("rows.pkl", "rb"))
M = json.load(open("mine.json"))
# integrity
bad = sum(1 for A in T.values() for r in A.values() if abs(v(r, "ttc_net") - v(r, "E30") - v(r, "out_E30")) > 1e-6)
print("rows", sum(len(A) for A in T.values()), "ttc mismatches", bad)
print("teleports>0", sum(1 for A in T.values() for r in A.values() if v(r, "teleports") > 0))
col = {}
for (n, q), A in T.items():
    c = sum(v(r, "collisions") for r in A.values())
    if c: col[(n, q)] = c
print("collisions", col)
print("finished_pct min", min(v(r, "finished_pct") for A in T.values() for r in A.values()))
# identity p333 vs os1_15_10 (only the stored KEYS subset) -> use raw file for every key
import json as J
D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/"
full = {}
for f in ("rows_band", "rows_s1"):
    for line in open(D + f + ".jsonl"):
        r = J.loads(line)
        if r["name"] in ("B|p333", "B|os1_15_10"):
            full[(r["name"], r["q"], r["seed"])] = r
for q in (3500.0, 4500.0, 5000.0, 5250.0, 5500.0, 6000.0, 7000.0):
    diff = []
    for s in range(7440880, 7440920):
        a, b = full.get(("B|p333", q, s)), full.get(("B|os1_15_10", q, s))
        if a is None: continue
        ks = (set(a) | set(b)) - {"name", "cfg", "m_st_file"}
        if any(a.get(k) != b.get(k) for k in ks): diff.append(s)
    print("p333 vs os1 differ", q, len(diff), diff[:5])
# paired medians arm - rule
for c, a, r in (("B|3500", "v3w", "p333"), ("B|5000", "v3w", "os1_15_10"), ("B|5000", "v3w", "p333"), ("X2|5300", "v3w", "lr1000_10_1"), ("B|4500", "v3w", "3e")):
    print("arm-rule paired median", c, a, r, {m: round(-M[c]["pmed"][f"{a}|{r}|{m}"], 1) for m in ("delay", "cf")})
