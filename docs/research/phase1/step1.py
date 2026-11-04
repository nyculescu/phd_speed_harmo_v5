"""V332: rules on r1m3 P0, no training. Select on 7,419,690-699, then test on 7,419,700-719. usage: step1.py plant_p0.json out_dir workers"""
import json
import sys
from pathlib import Path

import numpy as np

from v5b.fleet import plant_sweep as ps

LEVELS = (4600.0, 5300.0)
SETPOINTS = (8, 10, 12, 14, 16, 18, 20, 24)


def best(rows, names, q):
    A = {n: [r for r in rows if r["name"] == n and r["q"] == q] for n in names}
    ok = [n for n in names if not sum(r["collisions"] for r in A[n])]
    return min(ok, key=lambda n: np.median([r["delay"] for r in A[n]]))


if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    rd = str(out / "rd")
    c = {"p0": p0, "a333": {**p0, "ctrl": {"zones": [3, 3, 3]}}}
    pats = [f"p{u}{m}{d}" for u in range(4) for m in range(4) for d in range(4)]
    c |= {n: {**p0, "ctrl": {"cav_rule": [int(x) for x in n[1:]]}} for n in pats}
    meters = [f"alinea{s}" for s in SETPOINTS]
    c |= {f"alinea{s}": {**p0, "ctrl": {"meter": {"setpoint": s}}} for s in SETPOINTS}
    rows = ps.matrix(c, LEVELS, range(7_419_690, 7_419_700), out / "select.jsonl", w, rd)
    chosen = {str(q): {"pattern": best(rows, pats, q), "meter": best(rows, meters, q)} for q in LEVELS}
    (out / "chosen.json").write_text(json.dumps(chosen, indent=0))
    print("chosen", chosen, flush=True)
    names = {"p0", "a333", "p303"} | {x for v in chosen.values() for x in v.values()}
    ps.matrix({n: c[n] for n in sorted(names)}, LEVELS, range(7_419_700, 7_419_720), out / "test.jsonl", w, rd)
    print("done", flush=True)
