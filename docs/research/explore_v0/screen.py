"""V309 round 1 screen: paired against p303, higher is better everywhere. usage: screen.py runs_dir out.csv"""
import csv
import gzip
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

LIMIT = 27.78
ROUTE_LEN = {"main": 6489.02, "ramp": 3410.71}
METRICS = (("flow", 1), ("delay", -1), ("delay_ramp", -1), ("ttc_net", -1), ("brake_net", -1), ("ttc_merge", -1), ("brake_merge", -1))


def one(f):
    d = json.load(gzip.open(f, "rt"))
    r, w, e = d["row"], d["warm"], d["t_end"]
    delay = defaultdict(list)
    for v in d["vehicles"]:
        if w <= v["depart"] < e and v.get("arr") is not None and v["arr"] <= e:
            x = v["arr"] - v["depart"] - ROUTE_LEN[v["route"]] / (LIMIT * v["sf"])
            delay["all"].append(x)
            delay[v["route"]].append(x)
    return {"name": r["name"], "q": r["q"], "seed": r["seed"], "flow": r["passed"], "delay": float(np.mean(delay["all"])), "delay_ramp": float(np.mean(delay["ramp"])), "ttc_net": r["E30"] + r["out_E30"],
            "brake_net": r["brake3"] + r["out_b3"], "ttc_merge": r["E30"], "brake_merge": r["brake3"], "collisions": r["collisions"], "changes": r["changes"], "reversals": r["reversals"], "lane_cmds": r.get("lane_cmds", 0)}


def main():
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(one, map(str, sorted(Path(sys.argv[1]).glob("*.json.gz"))), chunksize=4))
    T = defaultdict(dict)
    for r in rows:
        T[(r["name"], r["q"])][r["seed"]] = r
    out = []
    for (n, q), A in sorted(T.items(), key=lambda x: (x[0][1], x[0][0])):
        B = T[("p303", q)]
        ds = sorted(set(A) & set(B))
        s = {"name": n, "q": q, "n": len(ds), "collisions": sum(a["collisions"] for a in A.values()), "changes": float(np.median([a["changes"] for a in A.values()])), "reversals": float(np.median([a["reversals"] for a in A.values()])), "lane_cmds": float(np.median([a["lane_cmds"] for a in A.values()]))}
        for m, sign in METRICS:
            s[m + "_abs"] = round(float(np.median([A[k][m] for k in ds])), 1)
            base = np.median([B[k][m] for k in ds])
            d = np.array([sign * (A[k][m] - B[k][m]) / base * 100 for k in ds])
            rng = np.random.default_rng(20261103)
            lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
            s[m], s[m + "_lo"], s[m + "_hi"] = round(float(np.median(d)), 2), round(float(lo), 2), round(float(hi), 2)
        out.append(s)
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.DictWriter(f, list(out[0]))
        w.writeheader()
        w.writerows(out)
    for q in sorted({r["q"] for r in out}):
        print(f"level {q:g}: flow, delay, ramp delay, TTC network, brake network, TTC merge against p303; collisions, lane commands, reversals")
        for s in sorted((r for r in out if r["q"] == q), key=lambda r: -(r["delay"] + r["flow"])):
            print(f" {s['name']}: " + " ".join(f"{s[m]:+.1f}[{s[m + '_lo']:+.1f},{s[m + '_hi']:+.1f}]" for m in ("flow", "delay", "delay_ramp", "ttc_net", "brake_net", "ttc_merge")) + f" coll {s['collisions']} lane {s['lane_cmds']:.0f} rev {s['reversals']:.0f}")
    q = 5300.0
    ok = [s for s in out if s["q"] == q and s["name"] in DIRECTIONS and (s["delay"] > 0 or s["flow"] > 0) and s["ttc_net"] >= -10 and s["brake_net"] >= -10 and not s["collisions"]]
    ok.sort(key=lambda s: -(s["delay"] + s["flow"]))
    print("eligible:", [s["name"] for s in ok], "shortlist:", [s["name"] for s in ok[:3]])


DIRECTIONS = ("hold10", "gamma95", "residual", "vehicles3", "saturated", "lane", "lane_hold10")
if __name__ == "__main__":
    main()
