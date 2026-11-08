"""Names, levels, seed counts and field presence per rows file (aggregates only)."""
import json, sys
from collections import defaultdict
D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/"
for f in ("rows_test.jsonl", "rows_band.jsonl", "rows_s1.jsonl"):
    T = defaultdict(set)
    keys = defaultdict(int)
    n = 0
    for line in open(D + f):
        r = json.loads(line)
        T[(r["name"], r["q"])].add(r["seed"])
        for k in ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "finished_pct", "dist", "dist_step", "vs", "N", "collisions", "teleports"):
            keys[k] += r.get(k) is not None
        n += 1
    print(f, n, "rows")
    print("  field presence:", dict(keys))
    byq = defaultdict(list)
    for (nm, q), s in sorted(T.items()):
        byq[q].append(f"{nm}:{len(s)}")
    for q, L in sorted(byq.items()):
        print("  q", q, len(L), "names;", " ".join(L))
    allseeds = sorted(set().union(*T.values()))
    print("  seeds", allseeds[0], "..", allseeds[-1], len(allseeds))
