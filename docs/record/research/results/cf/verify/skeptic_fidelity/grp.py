import json, sys, numpy as np
from collections import defaultdict
G = {"4a": "merge2", "ramp2": "merge2", "pending_ramp2": "merge2", "3a": "merge1", "ramp1": "merge1", "pending_ramp": "merge1"}
AWAY = ("1", "2", "3", "4", "5")
def s(x): return sum(x.values()) if isinstance(x, dict) else float(x)
V = defaultdict(dict); coll = defaultdict(int); tele = 0; fuel = defaultdict(dict); nrows = defaultdict(int)
for line in open(sys.argv[1]):
    r = json.loads(line)
    arm = r["arm"]; key = arm
    nrows[arm] += 1
    t = r.get("m_road_ttc3", {})
    g = {"away": sum(s(t.get(k, 0)) for k in AWAY), "merge2": sum(s(v) for k, v in t.items() if G.get(k) == "merge2"),
         "merge1": sum(s(v) for k, v in t.items() if G.get(k) == "merge1"), "net": float(r["ttc_net"]), "fuel": float(r.get("fuel_km") or 0)}
    V[key][r["seed"]] = g
    coll[arm] += float(r["collisions"]) > 0
    tele += float(r.get("teleports", 0) or 0) > 0
print("arms", dict(nrows)); print("rows with collisions", dict((k, v) for k, v in coll.items() if v), "teleport rows", tele)
print("v3w keys", [k for k in V if k.startswith("v3w")])
seeds = sorted(V["lr400_16_1"]); L = ["w0u250","w1u500","w2u250","w3u500","w4u500"]
def edge(opp, m, B=4000):
    R = np.array([V[opp][x][m] for x in seeds]); P = np.array([[V[l][x][m] for x in seeds] for l in L])
    rng = np.random.default_rng(1); n = len(seeds)
    f = lambda idx: np.mean([np.median(-(P[i, idx] - R[idx])) / np.median(R[idx]) * 100 for i in range(len(L))])
    pt = f(np.arange(n)); bs = np.array([f(rng.integers(0, n, n)) for _ in range(B)])
    return round(pt, 2), round(np.percentile(bs, 1.25), 2), round(np.percentile(bs, 98.75), 2), round(float(np.median(R)), 1), round(float(np.mean([np.median(p) for p in P])), 1)
for m in ("net", "away", "merge2", "merge1"): print("lr400_16_1", m, edge("lr400_16_1", m))
for m in ("away",): print("3E-C_TRUCK", m, edge("3E-C_TRUCK", m))
print("fuel vs lr400_16_1", edge("lr400_16_1", "fuel", 2000))
