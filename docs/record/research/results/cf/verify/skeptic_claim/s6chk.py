import json, sys, numpy as np
from collections import defaultdict
V = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
T = defaultdict(dict); cells = set()
for line in open("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"):
    r = json.loads(line)
    c, a = r["name"].split("|", 1); cells.add(c)
    T[(c, a)][r["seed"]] = (float(r["all_delay"]), float(r["ttc_net"]))
print("cells", sorted(cells), "arms per cell", {c: len([1 for (cc, a) in T if cc == c]) for c in cells})
for c in sorted(cells):
    arms = sorted(a for (cc, a) in T if cc == c)
    if not all((c, w) in T for w in V): print(c, "no v3w"); continue
    seeds = sorted(set.intersection(*[set(T[(c, a)]) for a in arms])); n = len(seeds)
    idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
    col = lambda a, j: np.array([T[(c, a)][s][j] for s in seeds])
    def e(o, j):
        O = col(o, j); m = np.median(O); D = [-(col(w, j) - O) / m * 100 for w in V]
        b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
        return (float(np.mean([np.median(d) for d in D])), *map(float, np.percentile(b, (1.25, 98.75))))
    print(c, "n", n)
    out = []
    for o in arms:
        if o in V: continue
        E, D = e(o, 1), e(o, 0)
        out.append((E[0], o, E, D))
    for E0, o, E, D in sorted(out)[:8]:
        print("   %-18s E %+.1f [%+.1f, %+.1f]  D %+.1f [%+.1f, %+.1f] %s" % (o, *E, *D, "competitor" if D[1] <= 1.0 or o == "p333" else "trade"))
    for o in ("lr400_16_1", "grid_lr400_13_1", "os0_10_10"):
        if (c, o) in T:
            E, D = e(o, 1), e(o, 0); print("   >> %-18s E %+.1f [%+.1f, %+.1f]  D %+.1f [%+.1f, %+.1f]" % (o, *E, *D))
