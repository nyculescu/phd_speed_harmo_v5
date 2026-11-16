"""V334: per-CAV policies against p333, a333 and no control on r1m3 P0. usage: evaluate.py plant_p0.json train_dir env.json seed0 n_seeds out.jsonl workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LEVELS = (4600.0, 5300.0)

if __name__ == "__main__":
    p0, train, env = json.load(open(sys.argv[1])), Path(sys.argv[2]), json.load(open(sys.argv[3]))
    seeds = range(int(sys.argv[4]), int(sys.argv[4]) + int(sys.argv[5]))
    out = Path(sys.argv[6])
    c = {"p0": p0, "p333": {**p0, "ctrl": {"cav_rule": [3, 3, 3]}}, "a333": {**p0, "ctrl": {"zones": [3, 3, 3]}}}
    if env.get("speed_action"):
        c |= {f"p333v{v}": {**p0, "ctrl": {"cav_rule": [3, 3, 3], "speed": k, "env": {"speed_action": True}}} for k, v in ((1, 90), (2, 80))}
    c |= {f"d{i}": {**p0, "ctrl": {"pt": str(train / f"C{i}_final.pt"), "env": env}} for i in range(3)}
    ps.matrix(c, LEVELS, seeds, out, int(sys.argv[7]), str(out.parent / "rd"))
    print("done", flush=True)
