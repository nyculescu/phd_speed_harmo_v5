"""V363: 7 policies against the rules on r2m3 at 5,300. usage: shot_runs.py plant_p0.json train_dir out.jsonl workers"""
import json
import sys
from pathlib import Path

from runs import COND, H10
from v5b.fleet import plant_sweep as ps

SEEDS = range(7_440_140, 7_440_160)

if __name__ == "__main__":
    p0, train, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
    out.parent.mkdir(parents=True, exist_ok=True)
    base = {**p0, "geom": "r2m3"}
    ctl = {"nc": {}, "p333": {"cav_rule": [3, 3, 3], "env": H10}, "r4a1": {"road_levels": {"4a": 1}, "env": H10}}
    ctl |= {f"d{i}": {"pt": str(train / f"C{i}_final.pt"), "env": H10} for i in range(7)}
    c = {}
    for n, k in ctl.items():
        for cond in ("S", "X1", "X2"):
            x = COND[cond]
            c[f"{cond}|{n}"] = {**base, "ctrl": {**k, "env": {**k.get("env", {}), **({"perturb": x} if x else {})}}}
    ps.matrix(c, (5300.0,), SEEDS, out, w, str(out.parent / "rd"))
    print("done", flush=True)
