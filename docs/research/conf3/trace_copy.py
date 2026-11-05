"""Traces the trained policies on the tracing seeds and writes the copy rule: mean level per road, rounded. usage: trace_copy.py train_dir out_dir workers"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from common import LEARNERS, PRIMARY, Q, SEEDS_TRACE, cfg, load, val
from v5b.fleet import plant_sweep as ps

if __name__ == "__main__":
    train, out, w = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    c = {f"{x}|d{i}": cfg({"pt": str(train / f"C{i}_final.pt")}, x) for i in range(LEARNERS) for x in PRIMARY}
    ps.matrix(c, (Q,), SEEDS_TRACE, out / "trace.jsonl", w, str(out / "rd"))
    T = load(out / "trace.jsonl")
    s, n = defaultdict(float), defaultdict(float)
    for A in T.values():
        for r in A.values():
            for k in r:
                if k.startswith("lv_sum_"):
                    s[k[7:]] += val(r, k)
                    n[k[7:]] += val(r, "lv_n_" + k[7:])
    levels = {road: int(round(s[road] / n[road])) for road in sorted(s) if n[road]}
    json.dump({"road_levels": levels}, open(out / "copy_rule.json", "w"), indent=1)
    print("copy rule", levels, {r: round(s[r] / n[r], 2) for r in sorted(s) if n[r]}, flush=True)
