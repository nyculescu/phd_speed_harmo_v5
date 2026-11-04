"""V360: can a fixed rule match the DRL win of V359? usage: rulecheck_runs.py plant_p0.json train_dir out.jsonl workers"""
import json
import sys
from pathlib import Path

from runs import COND, H10
from v5b.fleet import plant_sweep as ps

SEEDS = range(7_440_120, 7_440_140)
RULES = {"p333": {"cav_rule": [3, 3, 3]}, "r4a0": {"road_levels": {"4a": 0}}, "r4a1": {"road_levels": {"4a": 1}}, "r4a2": {"road_levels": {"4a": 2}},
         "z0": {"pattern": [3, 3, 3, 0, 3]}, "z1": {"pattern": [3, 3, 3, 1, 3]},
         "mimic": {"road_levels": {"1": 2, "2": 3, "3a": 2, "3": 2, "4a": 1, "4": 2, "5": 3}}}

if __name__ == "__main__":
    p0, train, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
    out.parent.mkdir(parents=True, exist_ok=True)
    base = {**p0, "geom": "r2m3"}
    ctl = RULES | {f"d{i}": {"pt": str(train / "r2m3" / f"C{i}_final.pt")} for i in range(3)}
    c = {}
    for n, k in ctl.items():
        for cond in ("S", "X1", "X2"):
            x = COND[cond]
            c[f"{cond}|{n}"] = {**base, "ctrl": {**k, "env": {**H10, **({"perturb": x} if x else {})}}}
    ps.matrix(c, (5300.0,), SEEDS, out, w, str(out.parent / "rd"))
    print("done", flush=True)
