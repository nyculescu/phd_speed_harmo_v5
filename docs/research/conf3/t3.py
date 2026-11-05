"""T3: at the run commit, stored no-control rows of baseline v2 reproduce every numeric key they hold. usage: t3.py baseline_rows.jsonl.gz out_dir. Exit 1 on any difference."""
import gzip
import json
import sys
from pathlib import Path

from common import PLANT
from v5b.fleet import plant_sweep as ps

P0D = {k: v for k, v in PLANT.items() if k not in ("tau_rise", "taper_fast", "fix_x", "geom")}
SEED = 7_440_045

if __name__ == "__main__":
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    stored = {(r["name"], r["q"], r["seed"]): r for r in map(json.loads, gzip.open(sys.argv[1], "rt"))}
    ps.matrix({"r2_p0d": dict(PLANT)}, (4600.0, 5300.0), [SEED], out / "t3.jsonl", 3, str(out / "rd"))
    ps.matrix({"p0d": P0D}, (5300.0,), [SEED], out / "t3.jsonl", 3, str(out / "rd"))
    bad = 0
    for line in open(out / "t3.jsonl"):
        new = json.loads(line)
        old = stored[(new["name"], new["q"], new["seed"])]
        diff = [k for k, v in old.items() if isinstance(v, (int, float)) and new.get(k) != v]
        print(new["name"], new["q"], "same" if not diff else f"DIFF {diff[:8]}", f"{sum(isinstance(v, (int, float)) for v in old.values())} keys", flush=True)
        bad += bool(diff)
    sys.exit(1 if bad else 0)
