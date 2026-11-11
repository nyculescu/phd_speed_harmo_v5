import sys
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/exploration/phase_b_round1/scripts/x1x2")
from lib import *
DS = {"r1test": RUNS+"round1_remote/out/test/test.jsonl", "r2val": RUNS+"round2/val/rows_6c49e7e.jsonl", "r2test": RUNS+"round2/test/rows_6c49e7e.jsonl"}
for k, f in DS.items():
    T = load(f)
    qs = sorted({q for (_, q) in T})
    for c in ("X1", "X2"):
        ns = sorted(n.split("|")[1] for (n, q) in T if n.startswith(c + "|") and q == 5300.0)
        seeds = sorted(T[(f"{c}|p333", 5300.0)])
        print(k, c, len(ns), "seeds", len(seeds), seeds[0], seeds[-1], "|", " ".join(ns))
    print(k, "q levels", qs[:8])
