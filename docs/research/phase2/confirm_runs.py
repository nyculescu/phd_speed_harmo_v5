"""V350: the local rule lr1000_10 on fresh seeds. usage: confirm_runs.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (4090.0, 4600.0)
SEEDS = range(7_419_760, 7_419_770)

if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    X = {f"slow{v}": {"kind": "slowdown", "limit_kmh": v, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0} for v in (25, 40)}
    ctl = {"nc": {}, "p333": {"cav_rule": [3, 3, 3]}, "p333h10": {"cav_rule": [3, 3, 3], "env": {"hold": 10.0}},
           "lr": {"local_rule": {"r": 1000, "th": 10}, "env": {"hold": 10.0}}}
    c = {}
    for n, k in ctl.items():
        c[n] = {**p0, "ctrl": k}
        for x, s in X.items():
            c[f"{n}_{x}"] = {**p0, "ctrl": {**k, "env": {**k.get("env", {}), "perturb": s}}}
    for x, s in X.items():
        c[f"oracle_{x}"] = {**p0, "ctrl": {"cav_rule": [3, 3, 3], "env": {"perturb": {**s, "hw_oracle": {"d": 500, "level": 1, "after": 120.0}}}}}
    ps.matrix(c, LEVELS, SEEDS, out / "rows.jsonl", w, str(out / "rd"))
    print("done", flush=True)
