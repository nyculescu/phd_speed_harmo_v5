import json, sys
from collections import defaultdict
import numpy as np
P = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
n = 0
bad = defaultdict(int)
fx = defaultdict(set); geo = defaultdict(set); al = defaultdict(set)
D = defaultdict(dict)
keys_first = None
for line in open(P):
    r = json.loads(line); n += 1
    if keys_first is None:
        keys_first = sorted(k for k in r if any(s in k for s in ("ttc", "E30", "end_stop", "wall", "c1_t0", "m_road")))
        print("keys", keys_first); print("c1_t0", r.get("c1_t0")); print("m_road_ttc3", r.get("m_road_ttc3"))
    a = r["name"]
    c = r["cfg"]
    fx[a].add(c.get("fix_x")); geo[a].add(c.get("geom")); al[a].add((c.get("accel_len"), c.get("accel2_len")))
    tn = r["ttc_net"]
    bad["E30+out"] += (r["E30"] + r["out_E30"]) != tn
    bad["ttc3"] += r.get("ttc3", 0.0) != tn
    bad["m_ttc3_all"] += r.get("m_ttc3_all") != tn
    rt = r.get("m_road_ttc3")
    bad["m_road_sum"] += (sum(sum(v.values()) for v in rt.values()) if rt else None) != tn
    bad["ttc3_r_sum"] += sum(v for k, v in r.items() if k.startswith("ttc3_r_")) != tn
    D[a][r["seed"]] = (r.get("wall_s"), r.get("end_stop", 0.0), r.get("end_stop2", 0.0), tn, r.get("ttc_half", 0.0))
print("rows", n, "arms", len(D), "mismatch", dict(bad))
print("fix_x values", {str(v) for s in fx.values() for v in s}, "geom", {v for s in geo.values() for v in s}, "accel", {v for s in al.values() for v in s})
seeds = sorted({s for d in D.values() for s in d}); print("seeds", seeds[0], seeds[-1], len(seeds))
allw = np.array([x[0] for d in D.values() for x in d.values()], float)
print("all wall mean %.1f median %.1f" % (allw.mean(), np.median(allw)))
out = {}
for a in sorted(D):
    x = np.array(list(D[a].values()), float)
    out[a] = x
    print(f"{a}: n {len(x)} wall mean {x[:,0].mean():.1f} med {np.median(x[:,0]):.1f} | end_stop med {np.median(x[:,1]):.0f} mean {x[:,1].mean():.0f} zero% {100*(x[:,1]==0).mean():.0f} | end_stop2 med {np.median(x[:,2]):.0f} mean {x[:,2].mean():.0f} zero% {100*(x[:,2]==0).mean():.0f} | ttc_net med {np.median(x[:,3]):.0f} half/net med {np.median(x[:,4]/np.maximum(x[:,3],1)):.3f}")
json.dump({a: {str(s): v for s, v in d.items()} for a, d in D.items()}, open(sys.argv[1], "w"))
