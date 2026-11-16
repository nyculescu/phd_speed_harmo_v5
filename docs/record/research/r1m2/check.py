"""V330: r1m2 with and without the r1m3 P0 settings on a demand ladder. usage: check.py out_dir workers"""
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

LADDER = (2400.0, 2700.0, 3000.0, 3300.0, 3600.0, 4000.0)
CFG = {"r1m2_plain": {"geom": "r1m2"}, "r1m2_p0": {"geom": "r1m2", "smooth": True, "lcAssertive": 1.4}}

if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    ps.matrix(CFG, LADDER, range(7_419_680, 7_419_690), out / "check.jsonl", int(sys.argv[2]), str(out / "rd"))
    print("done", flush=True)
