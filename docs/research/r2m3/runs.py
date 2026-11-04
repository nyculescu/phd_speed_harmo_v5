"""V354: r2m3 no-training check. Ladder, then all patterns by zone over 1.2 s and 0.8 s; select on 5 seeds, test on 20. usage: runs.py plant_p0.json out_dir workers"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

from v5b.fleet import plant_sweep as ps

LADDER = (3500.0, 4090.0, 4600.0, 5300.0, 6000.0)
LEVELS = (4600.0, 5300.0)
G = {"geom": "r2m3"}
INTERACT = ("31333", "33313", "31313")


def pat(s):
    return {"pattern": [int(x) for x in s], "env": {"hold": 10.0}}


if __name__ == "__main__":
    p0, out, w = json.load(open(sys.argv[1])), Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    rd = str(out / "rd")
    ps.matrix({"plain": {**G}, "p0": {**p0, **G}}, LADDER, range(7_440_000, 7_440_010), out / "ladder.jsonl", w, rd)
    names = ["".join(x) for x in itertools.product("13", repeat=5)]
    c = {"nc": {**p0, **G}, "p22222": {**p0, **G, "ctrl": pat("22222")}}
    c |= {f"p{n}": {**p0, **G, "ctrl": pat(n)} for n in names}
    rows = ps.matrix(c, LEVELS, range(7_440_010, 7_440_015), out / "select.jsonl", w, rd)
    chosen = {}
    for q in LEVELS:
        ok = [f"p{n}" for n in names if n != "33333" and not sum(r["collisions"] for r in rows if r["name"] == f"p{n}" and r["q"] == q)]
        chosen[str(q)] = min(ok, key=lambda n: np.median([r["delay"] for r in rows if r["name"] == n and r["q"] == q]))
    (out / "chosen.json").write_text(json.dumps(chosen))
    print("chosen", chosen, flush=True)
    test = {"nc", "p33333", "p22222", *chosen.values(), *(f"p{n}" for n in INTERACT)}
    ps.matrix({n: c[n] for n in sorted(test)}, LEVELS, range(7_440_015, 7_440_035), out / "test.jsonl", w, rd)
    print("done", flush=True)
