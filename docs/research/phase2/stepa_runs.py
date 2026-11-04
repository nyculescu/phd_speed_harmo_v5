"""V348: step A, no training. Is adaptation needed (fixed headways under X)? Is learning needed (a local detection rule)? usage: stepa_runs.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (4090.0, 4600.0)
SEEDS = range(7_419_750, 7_419_760)
FIXED = {"p111": [1, 1, 1], "p222": [2, 2, 2], "p333": [3, 3, 3]}
LOCAL = [(r, th) for r in (400, 600, 1000) for th in (10, 13, 16)]

if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    X = {f"slow{v}": {"kind": "slowdown", "limit_kmh": v, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0} for v in (25, 40)}
    ctl = {"nc": {}} | {n: {"cav_rule": v} for n, v in FIXED.items()}
    ctl |= {f"lr{r}_{th}": {"local_rule": {"r": r, "th": th}, "env": {"hold": 10.0}} for r, th in LOCAL}
    c = {}
    for n, k in ctl.items():
        c[n] = {**p0, "ctrl": k}
        for x, s in X.items():
            c[f"{n}_{x}"] = {**p0, "ctrl": {**k, "env": {**k.get("env", {}), "perturb": s}}}
    for x, s in X.items():
        c[f"oracle_{x}"] = {**p0, "ctrl": {"cav_rule": [3, 3, 3], "env": {"perturb": {**s, "hw_oracle": {"d": 500, "level": 1, "after": 120.0}}}}}
    ps.matrix(c, LEVELS, SEEDS, out / "rows.jsonl", w, str(out / "rd"))
    print("done", flush=True)
