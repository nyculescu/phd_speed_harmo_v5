"""V346: can CAVs keep p333's delay gain near a slowdown and lose its safety cost by lengthening the headway there? usage: hw_runs.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (4090.0, 4600.0)
SEEDS = range(7_419_780, 7_419_790)
GRID = [(d, lv) for d in (500, 1000, 2000) for lv in (0, 1)]     # level 0 is 1.6 s, level 1 is 1.2 s

if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    P = {"cav_rule": [3, 3, 3]}
    c = {"nc": {**p0, "ctrl": {"st": True}}, "p333": {**p0, "ctrl": {**P, "st": True}}}
    for lim in (25, 40):
        x = {"kind": "slowdown", "limit_kmh": lim, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0}
        c[f"nc_slow{lim}"] = {**p0, "ctrl": {"st": True, "env": {"perturb": x}}}
        c[f"p333_slow{lim}"] = {**p0, "ctrl": {**P, "st": True, "env": {"perturb": x}}}
        for d, lv in GRID:
            c[f"hw{lim}_d{d}_l{lv}"] = {**p0, "ctrl": {**P, "env": {"perturb": {**x, "hw_oracle": {"d": d, "level": lv, "after": 120.0}}}}}
    ps.matrix(c, LEVELS, SEEDS, out / "rows.jsonl", w, str(out / "rd"))
    print("done", flush=True)
