"""V341: the phase 2 wave check on r1m3 P0, no training, paired with the same seeds without X. usage: wave_runs.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (3500.0, 4090.0, 4600.0)
SEEDS = range(7_419_740, 7_419_750)
X = {"placebo": {"kind": "brake", "factor": 0.95, "hold": 1.0, "period": 180.0, "first": 420.0}}
X |= {f"brake{v}": {"kind": "brake", "target_kmh": v, "hold": 5.0, "period": 180.0, "first": 420.0} for v in (60, 40, 20)}
X |= {f"truck{v}": {"kind": "truck", "cap_kmh": v, "period": 300.0, "first": 360.0} for v in (70, 60, 50)}
X |= {f"burst{v}": {"kind": "burst", "cycle": float(v)} for v in (60, 90, 120)}
X |= {f"slow{v}": {"kind": "slowdown", "limit_kmh": v, "dur": 120.0, "times": [600.0, 1200.0]} for v in (60, 40, 25)}
OUT = {f"outage{v}": {"kind": "outage", "dur": float(v), "times": [600.0, 1200.0]} for v in (15, 30, 60)}

if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    c = {"none": {**p0, "ctrl": {"st": True}}, "p333": {**p0, "ctrl": {"cav_rule": [3, 3, 3], "st": True}}}
    c |= {n: {**p0, "ctrl": {"st": True, "env": {"perturb": s}}} for n, s in X.items()}
    c |= {n: {**p0, "ctrl": {"cav_rule": [3, 3, 3], "st": True, "env": {"perturb": s}}} for n, s in OUT.items()}
    ps.matrix(c, LEVELS, SEEDS, out / "rows.jsonl", w, str(out / "rd"))
    print("done", flush=True)
