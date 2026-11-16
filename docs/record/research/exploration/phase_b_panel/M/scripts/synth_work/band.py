"""EXPLORATORY, read-only: band rows at 6,000 veh/h (condition T). Scalars only."""
import json
import numpy as np
p = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl"
d = {}; pert = set(); fin = {}; e2 = {}
for line in open(p):
    r = json.loads(line)
    if r.get("q") != 6000.0:
        continue
    a = str(r["name"]).split("|")[-1]
    if a not in ("p333", "os1_15_10", "nc", "3e"):
        continue
    d.setdefault(a, {})[r["seed"]] = r["all_delay"]; fin.setdefault(a, []).append(r.get("finished_pct")); e2.setdefault(a, []).append(r.get("end_stop2"))
    c = r.get("cfg", {})
    pert.add(json.dumps(c.get("perturb") or c.get("ctrl", {}).get("env", {}).get("perturb")))
seeds = sorted(d["p333"]); P = np.array([d["p333"][s] for s in seeds]); med = np.median(P)
print("n", len(seeds), seeds[0], seeds[-1], "perturb", pert, "p333 median delay %.0f finished %% %.1f end_stop2 %.1f" % (med, np.median(fin["p333"]), np.median(e2["p333"])))
for a in ("os1_15_10", "3e", "nc"):
    x = 100 * (P - np.array([d[a][s] for s in seeds])) / med
    print(a, "edge %+.2f paired SD %.1f" % (np.median(x), x.std(ddof=1)))
