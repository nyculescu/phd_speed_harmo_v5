"""Rule tuning: every rule in X1 and X2 at 5,300, and no control for those cells and the reward references. usage: tune.py out_dir workers [rule_json]"""
import json
import sys
from pathlib import Path

from common import LEVELS, PRIMARY, Q, SEEDS_TUNE, cfg, families
from v5b.fleet import plant_sweep as ps

if __name__ == "__main__":
    out, w = Path(sys.argv[1]), int(sys.argv[2])
    if len(sys.argv) > 3:     # the copy rule, after tracing
        ps.matrix({f"{c}|copy": cfg(json.load(open(sys.argv[3])), c) for c in PRIMARY}, (Q,), SEEDS_TUNE, out / "tune_copy.jsonl", w, str(out / "rd"))
    else:
        ps.matrix({"S|nc": cfg({}, "S")}, LEVELS, SEEDS_TUNE, out / "tune_nc.jsonl", w, str(out / "rd"))
        c = {f"{x}|nc": cfg({}, x) for x in PRIMARY}
        for rules in families().values():
            c |= {f"{x}|{n}": cfg(k, x) for n, k in rules.items() for x in PRIMARY}
        ps.matrix(c, (Q,), SEEDS_TUNE, out / "tune.jsonl", w, str(out / "rd"))
    print("done", flush=True)
