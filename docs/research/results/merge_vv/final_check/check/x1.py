# Own stream of the stored E30 rows: per (arm, seed) the fields the final check needs.
import json, numpy as np
src = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
rec = {}; keys = None; roads = set(); n = 0; fixx = set(); geom = set()
with open(src) as f:
    for line in f:
        r = json.loads(line); n += 1
        if keys is None: keys = sorted(r.keys())
        rt = r.get("m_road_ttc3", {}); roads |= set(rt)
        g = lambda ks: sum(sum(rt.get(k, {}).values()) for k in ks)
        fixx.add(r["cfg"].get("fix_x")); geom.add(r["cfg"].get("geom"))
        rec[(r["name"], r["seed"])] = dict(ttc_net=r["ttc_net"], ttc_half=r.get("ttc_half", 0.0),
            es=r.get("end_stop", 0), es2=r.get("end_stop2", 0), delay=r["all_delay"],
            m1=g(("3a", "ramp1")), m2=g(("4a", "ramp2")), e1=g(("1",)), rest=g(("2", "3", "4", "5")), jn=g(("junction",)),
            ttc2=r.get("ttc2", 0), ttc15=r.get("ttc15", 0), sev3=r.get("sev3", 0), b45=r.get("b45_step", 0),
            roadsum=sum(sum(v.values()) for v in rt.values()), N=r.get("N", 0), e30=r.get("E30", 0), oute30=r.get("out_E30", 0))
arms = sorted({a for a, s in rec}); seeds = sorted({s for a, s in rec})
print("rows", n, "arms", len(arms), "seeds", len(seeds), min(seeds), max(seeds), "roads", sorted(roads), "fix_x", fixx, "geom", geom)
print("complete grid:", all((a, s) in rec for a in arms for s in seeds))
fields = list(next(iter(rec.values())).keys())
np.savez("cols.npz", arms=np.array(arms), seeds=np.array(seeds), **{k: np.array([[rec[(a, s)][k] for s in seeds] for a in arms], float) for k in fields})
json.dump(keys, open("keys.json", "w"))
print(arms)
