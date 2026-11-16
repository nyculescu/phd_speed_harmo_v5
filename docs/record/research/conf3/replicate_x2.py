"""Confirmatory 3b: X2 at 5,300 on fresh seeds, every arm confirmatory 3 ran in X2, read by decide3.read_cell unchanged. usage: replicate_x2.py run|read out_dir workers"""
import json
import sys
from pathlib import Path

from common import PRIMARY, Q, cfg, check_rows, load
from decide3 import read_cell
from v5b.fleet import plant_sweep as ps

CONF3 = Path("/home/catalin/work/phd/v5b1_runs/conf3")
SEEDS = range(7_440_220, 7_440_240)

if __name__ == "__main__":
    mode, out, w = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
    o = json.load(open(CONF3 / "opponents.json"))
    pol = {f"d{i}": {"pt": str(CONF3 / "train" / f"C{i}_final.pt")} for i in range(5)}
    arms = {"nc": {}, "p333": o["ctrl"]["p333"], **pol, o["single_rule"]: o["ctrl"][o["single_rule"]], **o["ctrl"]}
    f = out / "eval_x2.jsonl"
    if mode == "run":
        out.mkdir(parents=True, exist_ok=True)
        ps.matrix({f"X2|{n}": cfg(k, "X2") for n, k in arms.items()}, (Q,), SEEDS, f, w, str(out / "rd"))
    T = load(f)
    check_rows(T, 20)
    res = read_cell(T, "X2", o)
    print(json.dumps(res), flush=True)
    print("REPLICATES" if res["tuned_won"] else "DOES NOT REPLICATE", res["tuned"], "of 5", flush=True)
    pooled = load(f, CONF3 / "eval_primary.jsonl")
    pooled = {k: v for k, v in pooled.items() if k[0].startswith("X2|") and k[0].split("|")[1] in arms}
    check_rows(pooled, 40)
    p = read_cell(pooled, "X2", o)
    print("pooled 40 seeds, report-only, not the test:", p["tuned"], "of 5; counts", p["counts"], flush=True)
