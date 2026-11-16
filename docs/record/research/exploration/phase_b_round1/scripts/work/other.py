"""EXPLORATORY: per-road delay split in the stored S0/S1 measurement rows (band = demand ladder, test = X1/X2)."""
import json, sys
from collections import defaultdict
import numpy as np
REF = 100.0 / 3.6
rng = np.random.default_rng(20261110)

def ci(x):
    x = np.asarray(x, float)
    m = np.median(x[rng.integers(0, len(x), (10000, len(x)))], axis=1)
    return np.median(x), np.percentile(m, 2.5), np.percentile(m, 97.5)

def tot(d):
    return sum(d.values()) if isinstance(d, dict) else float(np.sum(d))

for path in sys.argv[1:]:
    T = defaultdict(dict)
    names = defaultdict(int)
    for line in open(path):
        r = json.loads(line)
        names[(r["name"], r.get("q"))] += 1
        if "m_road_vs" not in r:
            continue
        nm = r["name"]
        if not any(k in nm for k in ("p333", "nc")):
            continue
        vs = {g: tot(p) for g, p in r["m_road_vs"].items()}
        ds = {g: tot(p) for g, p in r["m_road_dist"].items()}
        dl = {g: vs[g] - ds.get(g, 0.0) / REF for g in vs}
        t = sum(dl.values())
        rate = lambda g: dl[g] / max(ds[g] / 1000.0, 1e-9)
        exc = (dl["3a"] - rate("2") * ds["3a"] / 1000.0) + (dl["4a"] - rate("3") * ds["4a"] / 1000.0) + dl.get("pending_ramp", 0.0) + dl.get("pending_ramp2", 0.0)
        T[(nm, r.get("q"))][r["seed"]] = dict(t=t, exc=100.0 * exc / t, m1=100.0 * (dl["3a"] - rate("2") * ds["3a"] / 1000.0) / t, m2=100.0 * (dl["4a"] - rate("3") * ds["4a"] / 1000.0) / t,
                                               pend=dl.get("pending_ramp", 0.0) + dl.get("pending_ramp2", 0.0), pmain=dl.get("pending_main", 0.0), ramps=100.0 * (dl["ramp1"] + dl["ramp2"]) / t,
                                               r1=rate("1"), r3=rate("3"), r4a=rate("4a"), r5=rate("5"), es=r.get("end_stop"), es2=r.get("end_stop2"), all=r.get("all_delay"))
    print(path.split("/")[-1], "arms with rows:", len(names), "| sample names:", sorted({n for n, _ in names})[:40])
    for key in sorted(T, key=lambda k: (str(k[0]), k[1] or 0)):
        d = T[key]
        f = lambda k: [v[k] for v in d.values()]
        e = ci(f("exc"))
        print(f"  {key[0]:14s} q {key[1]} n {len(d)}: delay {np.median(f('t')):8.0f}; merge excess {e[0]:5.1f} % [{e[1]:5.1f}, {e[2]:5.1f}] (m1 {np.median(f('m1')):4.1f}, m2 {np.median(f('m2')):4.1f}); ramp insertion queue {np.median(f('pend')):6.0f} veh-s; main queue {np.median(f('pmain')):7.0f}; ramp roads {np.median(f('ramps')):4.1f} %; s/veh-km e1 {np.median(f('r1')):5.2f} e3 {np.median(f('r3')):5.2f} 4a {np.median(f('r4a')):5.2f} e5 {np.median(f('r5')):5.2f}; end stops m1 {np.median(f('es')):5.0f} m2 {np.median(f('es2')):5.0f}")
