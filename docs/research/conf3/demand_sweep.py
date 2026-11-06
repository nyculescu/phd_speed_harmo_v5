"""Exploratory demand sweep (V406): where may the per-CAV policies have a purpose? 16 demand levels drawn at random, S, X1 and X2,
policies against no control, the 0.8 s rule, the best tuned rule and the single rule, on 4 used evaluation seeds. Report-only. usage: demand_sweep.py out_dir workers"""
import json
import sys
from pathlib import Path

import numpy as np

from common import cfg
from v5b.fleet import plant_sweep as ps

CONF3 = Path("/home/catalin/work/phd/v5b1_runs/conf3")
LEVELS = tuple(sorted(float(round(x, -1)) for x in np.random.default_rng(20261105).uniform(3800.0, 6000.0, 16)))
SEEDS = range(7_440_200, 7_440_204)
CONDS = ("S", "X1", "X2")

if __name__ == "__main__":
    out, w = Path(sys.argv[1]), int(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    o = json.load(open(CONF3 / "opponents.json"))
    arms = {"nc": {}, "p333": o["ctrl"]["p333"], "os1_15_10": o["ctrl"]["os1_15_10"], "lr400_13_2": o["ctrl"]["lr400_13_2"], **{f"d{i}": {"pt": str(CONF3 / "train" / f"C{i}_final.pt")} for i in range(5)}}
    (out / "levels.json").write_text(json.dumps({"levels": LEVELS, "rng_seed": 20261105, "range": [3800, 6000], "seeds": list(SEEDS)}))
    print("levels", LEVELS, flush=True)
    ps.matrix({f"{c}|{n}": cfg(k, c) for c in CONDS for n, k in arms.items()}, LEVELS, SEEDS, out / "sweep.jsonl", w, str(out / "rd"))
    print("done", flush=True)
