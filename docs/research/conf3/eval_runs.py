"""Evaluation. Primary cells: no control, p333, all chosen rules, policies. Map cells: no control, p333, the single rule, policies. usage: eval_runs.py train_dir out_dir workers"""
import json
import sys
from pathlib import Path

from common import COND, LEARNERS, PRIMARY, Q, SEEDS_EVAL, cfg
from v5b.fleet import plant_sweep as ps

if __name__ == "__main__":
    train, out, w = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    o = json.load(open(out / "opponents.json"))
    pol = {f"d{i}": {"pt": str(train / f"C{i}_final.pt")} for i in range(LEARNERS)}
    base = {"nc": {}, "p333": o["ctrl"]["p333"], **pol}
    single = {o["single_rule"]: o["ctrl"][o["single_rule"]]}
    prim = {f"{c}|{n}": cfg(k, c) for c in PRIMARY for n, k in {**base, **single, **o["ctrl"]}.items()}
    ps.matrix(prim, (Q,), SEEDS_EVAL, out / "eval_primary.jsonl", w, str(out / "rd"))
    ps.matrix({f"{c}|{n}": cfg(k, c) for c in PRIMARY for n, k in {**base, **single}.items()}, (4600.0,), SEEDS_EVAL, out / "eval_map_x.jsonl", w, str(out / "rd"))
    ps.matrix({f"{c}|{n}": cfg(k, c) for c in COND if c not in PRIMARY for n, k in {**base, **single}.items()}, (4600.0, Q), SEEDS_EVAL, out / "eval_map.jsonl", w, str(out / "rd"))
    print("done", flush=True)
