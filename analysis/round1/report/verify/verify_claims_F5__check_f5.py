import json, sys
from collections import defaultdict
import numpy as np
F = "/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl"
T = defaultdict(dict)
for line in open(F):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
Q = 5300.0
def v(r, k):
    x = r.get(k); return 0.0 if x is None else float(x)
def raw(A, B, key, sign=-1, pct=(1.25, 98.75)):
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([v(B[k], key) for k in ds])), 1e-9)
    d = np.array([sign * (v(A[k], key) - v(B[k], key)) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261104)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), pct)
    return round(float(np.median(d)), 2), round(float(lo), 2), round(float(hi), 2)
def med(A, k): return float(np.median([v(x, k) for x in A.values()]))
def coll(A): return sum(v(x, "collisions") for x in A.values())
def arm(names):
    seeds = set.intersection(*[set(T[(n, Q)]) for n in names])
    out = {}
    for s in seeds:
        out[s] = {k: float(np.mean([v(T[(n, Q)][s], k) for n in names])) for k in ("all_delay", "passed", "ttc_net", "b3_step", "collisions")}
    return out
dopp = {"X1": "lr1000_10_1", "X2": "os1_10_0"}
P95 = (2.5, 97.5)
for c in ("X1", "X2"):
    A = lambda n: T[(f"{c}|{n}", Q)]
    print(c, "n seeds", len(A("p333")), "median all_delay p333", round(med(A("p333"), "all_delay")), dopp[c], round(med(A(dopp[c]), "all_delay")), "os1_15_10", round(med(A("os1_15_10"), "all_delay")))
    dop = min((dopp[c], "p333"), key=lambda r: med(A(r), "all_delay"))
    print("  reference picked (decide3:54):", dop)
    W = arm([f"{c}|w{i}" for i in range(5)])
    for ref in ("p333", dopp[c]):
        print(f"  v3w arm vs {ref} delay 95%:", raw(W, A(ref), "all_delay", -1, P95), "97.5%:", raw(W, A(ref), "all_delay"))
    for i in range(5):
        P = A(f"w{i}")
        R = A(dop)
        d = raw(P, R, "all_delay")
        f = raw(P, R, "passed", 1)[0]; t = raw(P, R, "ttc_net")[0]; b = raw(P, R, "b3_step")[0]
        ok = d[0] >= 5.0 and d[1] > 0 and f >= -0.5 and t >= -10 and b >= -10 and coll(P) <= coll(R) + 1
        print(f"  w{i} vs {dop}: delay {d} flow {round(f,2)} ttc {round(t,2)} brake {round(b,2)} clears={ok}", "| vs", dopp[c] if dop=="p333" else "p333", raw(P, A(dopp[c] if dop=="p333" else "p333"), "all_delay"))
