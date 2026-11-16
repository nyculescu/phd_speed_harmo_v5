"""C-D5 edges of v3w on stored S6 rows (exploratory context, not fresh seeds) against the strongest E30 competitors."""
import json, sys
import numpy as np
from collections import defaultdict
V = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
OPP = ("lr400_16_1", "grid_lr400_13_1", "os0_10_10", "p333", "3ex2", "MPC-F")
AWAY = ("1", "2", "3", "4", "5")
def gs(d, roads):
    o = 0.0
    for g in roads:
        x = d.get(g, 0.0)
        o += sum(x.values()) if isinstance(x, dict) else float(x)
    return o
T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    c, a = r["name"].split("|", 1)
    if a in V or a in OPP:
        t = r.get("m_road_ttc3", {})
        T[(c, a)][r["seed"]] = (float(r["all_delay"]), float(r["ttc_net"]), gs(t, AWAY))
cells = sorted({c for c, _ in T})
print("cells", cells)
for c in cells:
    seeds = sorted(set.intersection(*[set(T[(c, a)]) for a in V + OPP if (c, a) in T]))
    if not seeds:
        continue
    n = len(seeds); idx = np.random.default_rng(20261108).integers(0, n, (4000, n))
    col = lambda a, j: np.array([T[(c, a)][s][j] for s in seeds])
    out = []
    for o in OPP:
        if (c, o) not in T:
            continue
        res = []
        for j in (1, 0, 2):
            O = col(o, j); m = np.median(O)
            D = [-(col(w, j) - O) / m * 100 for w in V]
            b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
            res.append("%+.1f [%+.1f, %+.1f]" % (np.mean([np.median(d) for d in D]), *np.percentile(b, (1.25, 98.75))))
        out.append(f"  {o}: E {res[0]}  D {res[1]}  away {res[2]}")
    print(c, "n", n); print("\n".join(out))
