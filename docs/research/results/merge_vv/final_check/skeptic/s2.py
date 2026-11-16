# Own C-D5 edge under the merge-scaling model, with and without edge 1; merge share by plan groups.
import json, numpy as np
R = json.load(open("rows9.json"))
arms = sorted({k.split("#")[0] for k in R}); seeds = sorted({int(k.split("#")[1]) for k in R})
L = [a for a in arms if a.split("|")[1][:2] in ("w0", "w1", "w2", "w3", "w4")]
def col(a, f): return np.array([f(R[f"{a}#{s}"]) for s in seeds])
merge = lambda d: sum(d.get(k, 0) for k in ("3a", "4a", "ramp1", "ramp2"))
for a in arms:
    t = col(a, lambda d: d["tot"]); print(a, "merge share %.3f edge1 share %.3f, check sum %s" % (col(a, merge).sum() / t.sum(), col(a, lambda d: d.get("1", 0)).sum() / t.sum(), np.allclose(t, col(a, lambda d: sum(v for k, v in d.items() if k != "tot")))))
rng = np.random.default_rng(424242); n = len(seeds); I = rng.integers(0, n, (4000, n))
def edge(opp, f):
    O = col(opp, f); m = np.median(O); D = [-(col(w, f) - O) / m * 100 for w in L]
    return np.mean([np.median(d) for d in D]), np.mean([np.median(d[I], axis=1) for d in D], axis=0)
for opp in ("E30|lr400_16_1", "E30|grid_lr400_13_1"):
    for drop in (False, True):
        out = []
        for k in (1.0, 0.34, 0.2, 0.1, 0.02):
            f = lambda d, k=k: k * merge(d) + d.get("2", 0) + d.get("3", 0) + d.get("junction", 0) + (0 if drop else d.get("1", 0))
            p, b = edge(opp, f); out.append("k=%.2f %+.2f SE %.2f lo %+.2f" % (k, p, b.std(), np.percentile(b, 1.25)))
        print(opp, "drop edge1" if drop else "with edge1", " | ".join(out))
