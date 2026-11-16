"""V370: the fixed plant P0c, P0 and the earlier plant on unused seeds. usage: check.py plant_p0c.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

SEEDS = range(7_440_035, 7_440_045)

if __name__ == "__main__":
    c = json.load(open(sys.argv[1]))
    out, w = Path(sys.argv[2]), int(sys.argv[3])
    p0 = {k: v for k, v in c.items() if k != "ease"}
    ps.matrix({"base": {}, "p0": p0, "p0c": c}, ps.LADDER, SEEDS, out / "check.jsonl", w, str(out / "rd"))
    ps.matrix({"r2_p0": {**p0, "geom": "r2m3"}, "r2_p0c": {**c, "geom": "r2m3"}}, (4600.0, 5300.0), SEEDS, out / "check_r2.jsonl", w, str(out / "rd"))
    print("done", flush=True)
