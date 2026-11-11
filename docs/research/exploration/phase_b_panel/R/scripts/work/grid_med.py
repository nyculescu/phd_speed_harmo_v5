import json, collections, numpy as np
f = "/home/catalin/work/phd/v5b1_runs/conf3/tune.jsonl"
T = collections.defaultdict(dict)
with open(f) as h:
    for line in h:
        r = json.loads(line); T[r["name"]][r["seed"]] = float(r["all_delay"])
for c in ("X1", "X2"):
    m = sorted((float(np.median(list(v.values()))), float(np.mean(list(v.values()))), k.split("|")[1]) for k, v in T.items() if k.startswith(c + "|"))
    print(c, "lowest median delay (median, mean):", [(n, round(a), round(b)) for a, b, n in m[:8]])
    print(c, "p333:", [(n, round(a), round(b)) for a, b, n in m if n == "p333"], "rank", [n for _, _, n in m].index("p333") + 1, "of", len(m))
    mm = sorted((b, n) for a, b, n in m)
    print(c, "lowest mean delay:", [(n, round(b)) for b, n in mm[:6]])
