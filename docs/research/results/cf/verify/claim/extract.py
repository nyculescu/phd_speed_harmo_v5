"""Stream the CF screen rows once and save per-arm per-seed arrays of the keys this check needs."""
import json, sys
import numpy as np
src, out = sys.argv[1], sys.argv[2]
def gs(d, roads):
    o = 0.0
    for g in roads:
        x = d.get(g, 0.0)
        o += sum(x.values()) if isinstance(x, dict) else float(x)
    return o
G = {"away": ("1", "2", "3", "4", "5"), "m2": ("4a", "ramp2"), "m1": ("3a", "ramp1"), "jn": ("junction",)}
T = {}
for line in open(src):
    r = json.loads(line)
    c, a = r["name"].split("|", 1)
    ttc = r.get("m_road_ttc3", {})
    d = {"all_delay": r["all_delay"], "ttc_net": r["ttc_net"], "b45_step": r.get("b45_step") or 0.0, "passed": r["passed"], "N": r["N"],
         "ttc_road_sum": gs(ttc, list(ttc))}
    for g, ks in G.items():
        d["ttc_" + g] = gs(ttc, ks)
    T.setdefault(a, {})[r["seed"]] = d
seeds = sorted(T["p333"])
keys = list(next(iter(T["p333"].values())))
np.savez(out, seeds=np.array(seeds), arms=np.array(sorted(T)), keys=np.array(keys),
         **{f"{a}__{k}": np.array([float(T[a][s][k]) for s in seeds]) for a in T for k in keys})
print(len(T), "arms", len(seeds), "seeds", keys)
print("road keys example", sorted(json.loads(open(src).readline()).get("m_road_ttc3", {})))
