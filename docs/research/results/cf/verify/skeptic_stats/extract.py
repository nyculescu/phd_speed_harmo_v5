import json, sys, collections, numpy as np
src, out = sys.argv[1], sys.argv[2]
keys = ("all_delay", "ttc_net", "b45_step", "E30", "out_E30")
data = collections.defaultdict(dict)
kc = collections.Counter(); cpu_rows = 0; miss = collections.Counter()
with open(src) as f:
    for line in f:
        r = json.loads(line)
        kc[len(r)] += 1
        cpu_rows += any("cpu" in k.lower() for k in r)
        for k in keys:
            if r.get(k) is None: miss[k] += 1
        data[r["arm"]][r["seed"]] = [float(r.get(k, np.nan)) for k in keys]
arms = sorted(data); seeds = sorted(data[arms[0]])
A = np.array([[data[a][s] for s in seeds] for a in arms])
np.savez(out, A=A, arms=np.array(arms), seeds=np.array(seeds), keys=np.array(keys))
print("arms", len(arms), "seeds", len(seeds), seeds[0], seeds[-1], "rows", sum(kc.values()))
print("keycount min/max", min(kc), max(kc), "n distinct", len(kc), "rows with cpu-like key", cpu_rows, "missing", dict(miss))
