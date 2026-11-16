"""Own extraction of the CF screen rows: per arm and seed, totals, zone and period splits."""
import json, sys, pickle
from collections import defaultdict
src, out = sys.argv[1], sys.argv[2]
ZONE = {"1": "away", "2": "away", "3": "away", "4": "away", "5": "away", "4a": "m2", "ramp2": "m2", "3a": "m1", "ramp1": "m1", "junction": "jn"}
T = defaultdict(dict)
roads, periods = set(), set()
sample = {}
for line in open(src):
    r = json.loads(line)
    cell, arm = r["name"].split("|", 1)
    d = {"all_delay": float(r["all_delay"]), "ttc_net": float(r["ttc_net"]), "b45_step": float(r.get("b45_step") or 0.0),
         "passed": float(r["passed"]), "N": float(r["N"]), "E30c": float(r.get("E30") or 0), "outE30c": float(r.get("out_E30") or 0),
         "ev45": float(sum(sum(r[f"m_peak_{c}"][3:]) for c in ("car", "alks", "truck"))), "coll": float(r["collisions"]),
         "delay": float(r.get("delay") or 0), "arrived": float(r.get("arrived") or 0), "ttc15": float(r.get("ttc15") or 0), "ttc2": float(r.get("ttc2") or 0),
         "b3_step": float(r.get("b3_step") or 0), "b7_step": float(r.get("b7_step") or 0), "teleports": float(r.get("teleports") or 0),
         "ttc3_lc": r.get("m_ttc3_lc"), "ttc3_all": r.get("m_ttc3_all")}
    z = defaultdict(float); p = defaultdict(float); zp = defaultdict(float); rd = defaultdict(float)
    for road, x in r.get("m_road_ttc3", {}).items():
        roads.add(road)
        if not isinstance(x, dict):
            x = {"na": x}
        for per, v in x.items():
            periods.add(per)
            z[ZONE.get(road, "other")] += v; p[per] += v; zp[ZONE.get(road, "other") + "|" + per] += v; rd[road] += v
    d["z"] = dict(z); d["p"] = dict(p); d["zp"] = dict(zp); d["rd"] = dict(rd)
    ge = defaultdict(float)
    for road, x in r.get("m_road_ge45", {}).items():
        ge[ZONE.get(road, "other")] += sum(x.values()) if isinstance(x, dict) else float(x)
    d["ge45z"] = dict(ge)
    d["b45z"] = {k[len("b45_step_g_"):]: v for k, v in r.items() if k.startswith("b45_step_g_")}
    T[arm][r["seed"]] = d
    if arm not in sample:
        sample[arm] = {k: r.get(k) for k in ("cell", "cell_spec", "arm", "learner", "commit", "pert_log", "c1_t0", "lv", "cfg", "m_ttc3_all", "m_ttc3_lc", "m_peak_car", "m_road_ge45", "steps")}
pickle.dump({"T": dict(T), "roads": sorted(roads), "periods": sorted(periods), "sample": sample}, open(out, "wb"))
print(len(T), "arms", {a: len(v) for a, v in T.items()} if len({len(v) for v in T.values()}) > 1 else len(next(iter(T.values()))), "roads", sorted(roads), "periods", sorted(periods))
