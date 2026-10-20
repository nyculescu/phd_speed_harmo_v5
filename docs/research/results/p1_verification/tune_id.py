import sys, json, os
sys.path.insert(0, "/home/catalin/work/phd/p1_frozen_85f7d34")
import numpy as np
from v5b.p1 import analysis as an, family as fam
RUN = "/home/catalin/work/phd/v5b1_runs/p1/v99"
R = json.load(open(f"{RUN}/result.json"))
seeds = list(range(R["seeds"]["tune"][0], R["seeds"]["tune"][1] + 1))
A = [fam.action_name(g, b) if hasattr(fam, "action_name") else (g + ("+back" if b else "")) for b in (False, True) for g in fam.G]
for q in (1600.0, 2000.0):
    N = R["tune"]["arms"][an.qk(q)]["N"]
    pooled = {}
    for a in A:
        v = []
        for inc in ("slow", "block"):
            for s in seeds:
                k = an.sw(N, a, inc, q, s)["key"] if fam.parse_action(a)[0] != N or fam.parse_action(a)[1] else an.sw(N, a, inc, q, s)["key"]
                p = f"{RUN}/runs/{k}.json"
                if os.path.exists(p): v.append(json.load(open(p))["delay_s"])
        if v: pooled[a] = (float(np.median(v)), len(v))
    print(q, sorted(pooled.items(), key=lambda z: z[1][0])[:5])
