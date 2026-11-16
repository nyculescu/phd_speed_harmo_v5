"""V343: how much can a controller that knows the slowdown in advance recover? usage: oracle_runs.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (4090.0, 4600.0)
SEEDS = range(7_419_790, 7_419_800)
HEAD = {"nc": {}, "p333": {"cav_rule": [3, 3, 3]}}
GRID = [(d, c) for d in (500, 1000, 2000) for c in (60, 80)]

if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    c = {}
    for h, ctl in HEAD.items():
        c[h] = {**p0, "ctrl": dict(ctl)}
        for lim in (25, 40):
            x = {"kind": "slowdown", "limit_kmh": lim, "dur": 120.0, "times": [600.0, 1200.0]}
            c[f"{h}_slow{lim}"] = {**p0, "ctrl": {**ctl, "env": {"perturb": x}}}
            for d, cap in GRID:
                c[f"{h}_slow{lim}_o{d}_{cap}"] = {**p0, "ctrl": {**ctl, "env": {"perturb": {**x, "oracle": {"d": d, "cap_kmh": cap}}}}}
    ps.matrix(c, LEVELS, SEEDS, out / "rows.jsonl", w, str(out / "rd"))
    print("done", flush=True)
