"""V302. usage: b_c8_select.py grid_rows.jsonl out.json : per level, the highest-flow pattern and the non-dominated patterns (up to 6 by flow)."""
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(list)
for line in open(sys.argv[1]):
    r = json.loads(line)
    if r["name"].startswith("p"):
        T[(r["name"], r["q"])].append(r)
out = {}
for q in sorted({k[1] for k in T}):
    P = {k[0]: np.array([np.median([r["passed"] for r in v]), -np.median([r["E30"] for r in v]), -np.median([r["brake3"] for r in v])]) for k, v in T.items() if k[1] == q}
    nd = [n for n in P if not any(all(P[m] >= P[n]) and any(P[m] > P[n]) for m in P if m != n)]
    nd.sort(key=lambda n: (-P[n][0], -P[n][1]))
    out[str(int(q))] = {"best": min(P, key=lambda n: (-P[n][0], -P[n][1])), "front": nd[:6], "values": {n: [float(x) for x in P[n]] for n in nd}}
json.dump(out, open(sys.argv[2], "w"), indent=0)
