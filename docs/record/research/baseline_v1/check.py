"""V328: r1m3 P0 and the earlier plant on unused seeds, all four demand levels. usage: check.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

if __name__ == "__main__":
    out = Path(sys.argv[2])
    ps.matrix({"base": {}, "p0": json.load(open(sys.argv[1]))}, ps.LADDER, range(7_419_640, 7_419_650), out / "check.jsonl", int(sys.argv[3]), str(out / "rd"))
    print("done", flush=True)
