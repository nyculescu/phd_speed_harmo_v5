import pickle, sys, numpy as np
sys.path.insert(0, "/home/catalin/work/phd/p1_frozen_85f7d34")
from v5b.p1 import family as fam
R = pickle.load(open(sys.argv[1], "rb"))
TUNE = range(7400200, 7400240)
def fk(g, inc, q, s): return f"{g}_{inc}_q{q}_s{s}"
def sk(N, a, inc, q, s):
    g, back = fam.parse_action(a); return f"{N}-{g}" + ("+back" if back else "") + f"_{inc}_q{q}_s{s}"
def top(per, order, n=4):
    lst = sorted(order, key=lambda c: (np.median(per[c]), order.index(c)))
    return [(c, round(float(np.median(per[c])), 1)) for c in lst[:n]]
for q in (1600, 2000):
    none = {g: [R[fk(g, "none", q, s)]["delay_s"] for s in TUNE] for g in fam.G}
    pooled = {g: [R[fk(g, i, q, s)]["delay_s"] for i in ("slow", "block") for s in TUNE] for g in fam.G + fam.PI}
    assert all(len(v) == 40 for v in none.values()) and all(len(v) == 80 for v in pooled.values())
    N = top(none, list(fam.G))[0][0]
    print(f"q{q} N:", top(none, list(fam.G)))
    print(f"q{q} FX:", top(pooled, list(fam.CONST)))
    print(f"q{q} FB:", top(pooled, list(fam.FEEDBACK)))
    print(f"q{q} PI:", top(pooled, list(fam.PI), 6))
    for e in ("e4", "e5"):
        print(f"   PI best {e}:", top(pooled, [p for p in fam.PI if p.endswith(e)], 2))
    for inc in ("slow", "block"):
        per = {p: [R[fk(p, inc, q, s)]["delay_s"] for s in TUNE] for p in fam.PI}
        print(f"   PI per type {inc}:", top(per, list(fam.PI), 3), " FB per type:", top(per | {g: [R[fk(g, inc, q, s)]["delay_s"] for s in TUNE] for g in fam.FEEDBACK}, list(fam.FEEDBACK), 2))
    FB = top(pooled, list(fam.FEEDBACK))[0][0]
    ad = {fam.ad_id(e, FB): [R[fk(fam.ad_id(e, FB), i, q, s)]["delay_s"] for i in ("slow", "block") for s in TUNE] for e in fam.ETA_GRID}
    print(f"q{q} AD:", top(ad, list(ad), 3))
    per = {i: {a: [R[sk(N, a, i, q, s)]["delay_s"] for s in TUNE] for a in fam.A} for i in ("slow", "block")}
    for i in ("slow", "block"):
        print(f"q{q} IP {i}:", top(per[i], list(fam.A)))
    pool = {a: per["slow"][a] + per["block"][a] for a in fam.A}
    print(f"q{q} ID (pooled median):", top(pool, list(fam.A)))
    # alternative ID criteria (sensitivity only)
    mean_ = {a: [np.mean(pool[a])] for a in fam.A}
    avgmed = {a: [(np.median(per["slow"][a]) + np.median(per["block"][a])) / 2] for a in fam.A}
    print(f"   ID alt (pooled mean):", top(mean_, list(fam.A), 3), " (avg of type medians):", top(avgmed, list(fam.A), 3))
