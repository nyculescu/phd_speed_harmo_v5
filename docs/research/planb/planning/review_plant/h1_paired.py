"""Paired H1-vs-S delay change per seed at 5,300 (conf3 eval_map rows), for no control and p333: a proxy for TRUCK's G1a."""
import json, sys
import numpy as np
from collections import defaultdict
T = defaultdict(dict)
for f in sys.argv[1:]:
    for line in open(f):
        r = json.loads(line)
        T[(r["name"], r["q"])][r["seed"]] = r
names = sorted({k[0] for k in T})
print("names sample:", names[:12], "...", len(names))
rng = np.random.default_rng(1)
for arm in ("nc", "p333", "lr400_13_2"):
    for q in (5300.0, 4600.0):
        S, H = T.get((f"S|{arm}", q)) or T.get((arm + "|S", q)), T.get((f"H1|{arm}", q)) or T.get((arm + "|H1", q))
        if not S or not H:
            continue
        ds = sorted(set(S) & set(H))
        d = np.array([H[s]["all_delay"] - S[s]["all_delay"] for s in ds])
        base = np.median([S[s]["all_delay"] for s in ds])
        eff = 100 * np.median(d) / base
        bs = [100 * np.median(d[rng.integers(0, len(d), len(d))]) / base for _ in range(5000)]
        print(arm, q, "n", len(ds), f"H1 vs S delay {eff:+.1f} % [{np.percentile(bs, 2.5):+.1f}, {np.percentile(bs, 97.5):+.1f}]")
