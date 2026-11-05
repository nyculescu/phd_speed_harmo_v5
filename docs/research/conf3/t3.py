"""T3: at the run commit, stored no-control rows of baseline v2 reproduce every numeric key they hold. usage: t3.py baseline_rows.jsonl.gz tmp_dir. Exit 1 on any difference."""
import gzip
import json
import sys

from common import PLANT
from v5b.fleet import plant_sweep as ps

P0D = {k: v for k, v in PLANT.items() if k not in ("tau_rise", "taper_fast", "fix_x", "geom")}
WANT = [("r2_p0d", {**PLANT}, 4600.0, 7_440_045), ("r2_p0d", {**PLANT}, 5300.0, 7_440_045), ("p0d", P0D, 5300.0, 7_440_045)]

if __name__ == "__main__":
    rows = {(r["name"], r["q"], r["seed"]): r for r in map(json.loads, gzip.open(sys.argv[1], "rt"))}
    bad = 0
    for name, c, q, s in WANT:
        old, new = rows[(name, q, s)], ps.run_one((name, c, q, s, sys.argv[2]))
        diff = [k for k, v in old.items() if isinstance(v, (int, float)) and new.get(k) != v]
        print(name, q, s, "same" if not diff else f"DIFF {diff[:8]}", flush=True)
        bad += bool(diff)
    sys.exit(1 if bad else 0)
