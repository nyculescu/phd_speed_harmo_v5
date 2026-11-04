"""V352: does knowing the type of the driver behind help? usage: type_runs.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (4600.0, 5300.0)
SEEDS = range(7_419_770, 7_419_780)
X = {"kind": "slowdown", "limit_kmh": 25, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0}
P = {"cav_rule": [3, 3, 3]}

if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    ctl = {"nc": {"attrib": True}, "p333": {**P, "attrib": True}, "p222": {"cav_rule": [2, 2, 2]}, "lr": {"local_rule": {"r": 1000, "th": 10}, "env": {"hold": 10.0}}}
    ctl |= {f"t_{m}": {**P, "env": {"hw_type": {"mode": m}}} for m in ("any", "truck", "tau", "sigma", "either", "sf")}
    c = {}
    for n, k in ctl.items():
        c[n] = {**p0, "ctrl": k}
        c[f"{n}_slow25"] = {**p0, "ctrl": {**k, "env": {**k.get("env", {}), "perturb": X}}}
    ps.matrix(c, LEVELS, SEEDS, out / "rows.jsonl", w, str(out / "rd"))
    print("done", flush=True)
