# Independent stream of the E30 rows: per (arm, seed) the fields needed to re-derive the design review's numbers.
import json, sys, numpy as np
src = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
keep = ["E30|w0u250","E30|w1u500","E30|w2u250","E30|w3u500","E30|w4u500","E30|lr400_16_1","E30|grid_lr400_13_1","E30|p333","E30|nc"]
rec = {}
roadset = set()
with open(src) as f:
    for line in f:
        r = json.loads(line)
        if r["name"] not in keep: continue
        rt = r.get("m_road_ttc3", {})
        roadset |= set(rt)
        g = lambda roads: sum(sum(rt.get(k, {}).values()) for k in roads)
        per = {}
        for k, x in rt.items():
            for p, v in x.items(): per[p] = per.get(p, 0) + v
        rec[(r["name"], r["seed"])] = dict(ttc_net=r["ttc_net"], ttc_half=r.get("ttc_half", np.nan), es=r.get("end_stop", 0), es2=r.get("end_stop2", 0),
            m1=g(("3a","ramp1")), m2=g(("4a","ramp2")), away=g(("1","2","3","4","5")), jn=g(("junction",)), delay=r["all_delay"],
            lc=r.get("m_ttc3_lc", 0), all3=r.get("m_ttc3_all", 0),
            p_th=per.get("taper",0)+per.get("hold",0), p_after=per.get("after",0), p_before=per.get("before",0), p_rest=per.get("rest",0))
print(len(rec), sorted(roadset))
arms = keep; seeds = sorted({s for a, s in rec})
fields = list(next(iter(rec.values())).keys())
np.savez("cols.npz", arms=np.array(arms), seeds=np.array(seeds), **{k: np.array([[rec[(a, s)][k] for s in seeds] for a in arms], float) for k in fields})
