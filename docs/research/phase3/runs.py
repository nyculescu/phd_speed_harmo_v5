"""Confirmatory 2 evaluation (V358). usage: runs.py plant_p0.json train_dir out.jsonl workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (4600.0, 5300.0)
SEEDS = range(7_440_100, 7_440_120)
COND = {"S": None,
        "X1": {"kind": "slowdown", "edge": "4", "limit_kmh": 25, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0},
        "X2": {"kind": "slowdown", "edge": "3", "limit_kmh": 30, "dur": 180.0, "times": [700.0], "taper": 20.0},
        "H1": {"kind": "truck", "cap_kmh": 50, "period": 300.0, "first": 360.0},
        "H2": {"kind": "burst", "cycle": 120.0}}
H10 = {"hold": 10.0}

if __name__ == "__main__":
    p0, train, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
    out.parent.mkdir(parents=True, exist_ok=True)
    c = {}
    for plant, base in (("r1m3", p0), ("r2m3", {**p0, "geom": "r2m3"})):
        ctl = {"nc": {}, "p333": {"cav_rule": [3, 3, 3], "env": H10}, "lr": {"local_rule": {"r": 1000, "th": 10}, "env": H10}}
        ctl |= {f"d{i}": {"pt": str(train / plant / f"C{i}_final.pt"), "env": H10} for i in range(3)}
        for name, k in ctl.items():
            for cond, x in COND.items():
                env = {**k.get("env", {}), **({"perturb": x} if x else {})}
                c[f"{plant}|{cond}|{name}"] = {**base, "ctrl": {**k, "env": env}}
    ps.matrix(c, LEVELS, SEEDS, out, w, str(out.parent / "rd"))
    print("done", flush=True)
