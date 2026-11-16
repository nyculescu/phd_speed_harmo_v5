"""Own loader and protocol statistic for the round-1 check. Written independently of common1/decide1/decide3."""
import json
from collections import defaultdict

import numpy as np

OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
P95 = (2.5, 97.5)
B2 = (1.25, 98.75)  # Bonferroni m=2 percentiles (a 97.5 % two-sided interval)
B2_WIDE = (0.625, 99.375)  # a 98.75 % two-sided interval, the level the report names


def load(path):
    T = defaultdict(dict)
    with open(path) as h:
        for line in h:
            r = json.loads(line)
            keep = {k: v for k, v in r.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
            T[(r["name"], float(r["q"]))][int(r["seed"])] = keep
    return dict(T)


def g(row, k):
    v = row.get(k)
    return 0.0 if v is None else float(v)


def stat(P, O, key, sign=-1, pct=B2, n_boot=20000, seed=20261104):
    s = sorted(set(P) & set(O))
    assert s
    o = np.array([g(O[x], key) for x in s])
    p = np.array([g(P[x], key) for x in s])
    den = max(float(np.median(o)), 1e-9)
    d = sign * (p - o) / den * 100.0
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), (n_boot, len(d)))
    meds = np.median(d[idx], axis=1)
    lo, hi = np.percentile(meds, pct)
    return float(np.median(d)), float(lo), float(hi)


def pmed(P, O, key):
    s = sorted(set(P) & set(O))
    return float(np.median([g(P[x], key) - g(O[x], key) for x in s]))


def med(A, key):
    return float(np.median([g(r, key) for r in A.values()]))


def coll(A):
    return float(sum(g(r, "collisions") for r in A.values()))


def arm(T, names, q):
    rows = [T[(n, q)] for n in names]
    seeds = sorted(set(rows[0]).intersection(*[set(r) for r in rows[1:]]))
    keys = set()
    for r in rows:
        for s in seeds:
            keys |= set(r[s])
    return {s: {k: sum(g(r[s], k) for r in rows) / len(rows) for k in keys} for s in seeds}


def f(t, nd=1):
    return "%+.*f [%+.*f, %+.*f]" % (nd, t[0], nd, t[1], nd, t[2])
