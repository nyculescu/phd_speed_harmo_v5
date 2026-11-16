"""Own check: X1 medians of ALKS braking events peaking past the limit (m_peak_alks bins 4-7), every arm."""
import json
import sys
from collections import defaultdict
import numpy as np

G = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": [f"t{i}" for i in range(5)],
     "sw": [f"s{i}u500" for i in range(5)], "baseline-v3": [f"d{i}u500" for i in range(5)]}
member = {n: g for g, ns in G.items() for n in ns}
val = defaultdict(lambda: defaultdict(list))
with open(sys.argv[1]) as f:
    for line in f:
        r = json.loads(line)
        cell, a = r["name"].split("|")
        if cell != "X1":
            continue
        pk = r.get("m_peak_alks")
        x = float(sum(pk[4:8])) if pk else 0.0
        val[member.get(a, a)][int(r["seed"])].append(x)
out = sorted((float(np.median([np.mean(v) for v in d.values()])), g, len(d)) for g, d in val.items())
for m, g, n in out:
    print(f"{g} {m:.1f} n={n}")
