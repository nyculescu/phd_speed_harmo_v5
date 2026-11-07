"""Independent checks of round-1 report claims F7, F8, F10, F11, F13 from the raw rows (aggregates only)."""
import json
from collections import defaultdict
import numpy as np

OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"


def load(path):
    T = defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        T[(r["name"], float(r["q"]))][r["seed"]] = r
    return T


def v(r, k):
    x = r.get(k)
    return 0.0 if x is None else float(x)


def arm(T, names, q):
    rows = [T[(n, q)] for n in names]
    seeds = sorted(set.intersection(*(set(r) for r in rows)))
    keys = set()
    for r in rows:
        for s in seeds:
            keys |= {k for k, x in r[s].items() if isinstance(x, (int, float)) and not isinstance(x, bool)}
    return {s: {k: sum(v(r[s], k) for r in rows) / len(rows) for k in keys} for s in seeds}


def med(A, k):
    return float(np.median([v(x, k) for x in A.values()]))


def eff(A, B, k, sign=-1, pct=(2.5, 97.5), n=20000, seed=1):
    ds = sorted(set(A) & set(B))
    ref = float(np.median([v(B[s], k) for s in ds]))
    d = np.array([sign * (v(A[s], k) - v(B[s], k)) / ref * 100 for s in ds])
    rng = np.random.default_rng(seed)
    bs = np.median(d[rng.integers(0, len(d), (n, len(d)))], axis=1)
    lo, hi = np.percentile(bs, pct)
    return round(float(np.median(d)), 2), round(float(lo), 2), round(float(hi), 2), len(ds)


T = load(f"{OUT}/test/test.jsonl")
B = load(f"{OUT}/test/band.jsonl")
print("test arms", len(T), "band arms", len(B))
Q = 5300.0
for c in ("X1", "X2"):
    W = arm(T, [f"{c}|w{i}" for i in range(5)], Q)
    D = arm(T, [f"{c}|d{i}" for i in range(5)], Q)
    NC = T[(f"{c}|nc", Q)]
    print(c, "F7 v3w vs nc 95%: ttc", eff(W, NC, "ttc_net"), "delay", eff(W, NC, "all_delay"))
    print(c, "F8 T1 v3w vs d 98.75%: ttc", eff(W, D, "ttc_net", pct=(1.25, 98.75)), "delay", eff(W, D, "all_delay", pct=(1.25, 98.75)))
    print(c, "F8 T1 v3w vs d 95%: ttc", eff(W, D, "ttc_net"))
    print(c, "F11 medians: v3w b3_step", med(W, "b3_step"), "nc all_delay", med(NC, "all_delay"), "v3w all_delay", med(W, "all_delay"),
          "d b3_step", med(D, "b3_step"))
    # F13: moving full-emergency totals per 40 runs per arm
    tot = {}
    for (n, q), A in T.items():
        if n.startswith(c + "|") and q == Q:
            tot[n.split("|")[1]] = (sum(v(r, "alks_full_moving") for r in A.values()), sum(1 for r in A.values() if v(r, "alks_full_moving") > 0),
                                   med(A, "alks_full_moving"))
    print(c, "F13 alks_full_moving (total, runs>0, median):", dict(sorted(tot.items())))
    print(c, "F13 arm medians: v3w", med(W, "alks_full_moving"), "d", med(D, "alks_full_moving"))

# F10: blind spots in band incl. 5-learner arm means
print("F10 band blind spots (name, q, brake 1Hz/step, ttc whole/half, med b3_step, med ttc_net, med ttc_half)")
qs = sorted({q for (_, q) in B})
items = []
for q in qs:
    items.append(("v3w arm", q, arm(B, [f"B|w{i}" for i in range(5)], q)))
    items.append(("d arm", q, arm(B, [f"B|d{i}" for i in range(5)], q)))
for (n, q), A in B.items():
    items.append((n, q, A))
for n, q, A in items:
    b, s, t, h = med(A, "brake_net"), med(A, "b3_step"), med(A, "ttc_net"), med(A, "ttc_half")
    if (s >= 50 and abs(b / s - 1) > 0.05) or (h >= 50 and abs(t / h - 1) > 0.05):
        print(" ", n, q, round(b / s, 3), round(t / max(h, 1), 3), round(s, 1), t, h)
# test arm means too
for c in ("X1", "X2"):
    for lab, p in (("v3w", "w"), ("d", "d")):
        A = arm(T, [f"{c}|{p}{i}" for i in range(5)], Q)
        b, s, t, h = med(A, "brake_net"), med(A, "b3_step"), med(A, "ttc_net"), med(A, "ttc_half")
        print("test arm", c, lab, round(b / s, 3), round(t / h, 3))
