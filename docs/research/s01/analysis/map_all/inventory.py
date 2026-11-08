import json, sys
from collections import defaultdict
base = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/"
for f in ("rows_test.jsonl", "rows_band.jsonl", "rows_s1.jsonl"):
    T = defaultdict(set)
    keys = None
    missing = defaultdict(int)
    for line in open(base + f):
        r = json.loads(line)
        T[(r["name"], r["q"])].add(r["seed"])
        if keys is None:
            keys = sorted(k for k in r if not k.startswith("m_"))
        for k in ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "E30", "out_E30", "dist", "finished_pct", "collisions", "teleports"):
            if r.get(k) is None:
                missing[k] += 1
    print("==", f, "groups", len(T))
    by_q = defaultdict(list)
    for (n, q), s in sorted(T.items()):
        by_q[q].append((n, len(s), min(s), max(s)))
    for q, L in sorted(by_q.items()):
        print(" q", q, "n_names", len(L), "seed counts", sorted({x[1] for x in L}), "seed range", min(x[2] for x in L), max(x[3] for x in L))
        print("   ", " ".join(x[0] for x in L))
    print(" missing(None/absent) counts:", dict(missing))
    print(" non-m_ keys:", keys)
