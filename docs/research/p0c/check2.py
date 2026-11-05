"""V374: the plant P0d against the earlier plant, with P0c alongside, on new seeds. usage: check2.py plant_p0d.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

SEEDS = range(7_440_045, 7_440_065)

if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    out, w = Path(sys.argv[2]), int(sys.argv[3])
    c = {k: v for k, v in d.items() if k not in ("smooth_s", "ease_max")}
    ps.matrix({"base": {}, "p0d": d}, ps.LADDER, SEEDS, out / "check.jsonl", w, str(out / "rd"))
    ps.matrix({"p0c": c}, (4600.0, 5300.0), SEEDS, out / "check_p0c.jsonl", w, str(out / "rd"))
    ps.matrix({"r2_p0d": {**d, "geom": "r2m3"}}, (4600.0, 5300.0), SEEDS, out / "check_r2.jsonl", w, str(out / "rd"))
    print("done", flush=True)
