"""V391: the evaluation rows that do not depend on the policies, run during training so the chain's evaluation step skips them.
Same names, configs and files as eval_runs.py; the chain later adds the policy and copy-rule arms. Rows are not read here. usage: precompute_eval.py out_dir workers"""
import json
import sys
from pathlib import Path

from common import COND, PRIMARY, Q, SEEDS_EVAL, cfg
from v5b.fleet import plant_sweep as ps

if __name__ == "__main__":
    out, w = Path(sys.argv[1]), int(sys.argv[2])
    o = json.load(open(out / "opponents.json"))
    base = {"nc": {}, "p333": o["ctrl"]["p333"]}
    single = {o["single_rule"]: o["ctrl"][o["single_rule"]]}
    prim = {f"{c}|{n}": cfg(k, c) for c in PRIMARY for n, k in {**base, **single, **o["ctrl"]}.items()}
    print("arms", len(prim), "+", 2 * len({**base, **single}), "+", (len(COND) - len(PRIMARY)) * len({**base, **single}), flush=True)
    ps.matrix(prim, (Q,), SEEDS_EVAL, out / "eval_primary.jsonl", w, str(out / "rd"))
    ps.matrix({f"{c}|{n}": cfg(k, c) for c in PRIMARY for n, k in {**base, **single}.items()}, (4600.0,), SEEDS_EVAL, out / "eval_map_x.jsonl", w, str(out / "rd"))
    ps.matrix({f"{c}|{n}": cfg(k, c) for c in COND if c not in PRIMARY for n, k in {**base, **single}.items()}, (4600.0, Q), SEEDS_EVAL, out / "eval_map.jsonl", w, str(out / "rd"))
    print("done", flush=True)
