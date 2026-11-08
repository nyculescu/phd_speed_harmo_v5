import json, pickle
from collections import defaultdict
D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/"
KEYS = ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "E30", "out_E30", "collisions", "teleports", "finished_pct", "dist")
T = {}
src = {}
for f in ("rows_test", "rows_band", "rows_s1"):
    with open(D + f + ".jsonl") as h:
        for line in h:
            r = json.loads(line)
            k = (r["name"], float(r["q"]))
            T.setdefault(k, {})
            if r["seed"] in T[k]:
                print("DUP", f, k, r["seed"])
            T[k][r["seed"]] = {x: r.get(x) for x in KEYS}
            src[k] = f
pickle.dump((T, src), open("rows.pkl", "wb"))
inv = defaultdict(list)
for (n, q), A in sorted(T.items()):
    cell, arm = n.split("|", 1)
    inv[(src[(n, q)], cell, q)].append((arm, len(A), min(A), max(A)))
for k, v in sorted(inv.items()):
    print(k, len(v))
    print("   ", [(a, n) for a, n, lo, hi in v])
    print("    seeds", sorted(set((lo, hi) for a, n, lo, hi in v)))
