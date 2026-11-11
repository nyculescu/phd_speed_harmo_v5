# EXPLORATORY: recompute the X1 delay ranking of confirmatory 3's stored tuning rows
import json, collections, numpy as np
T = collections.defaultdict(dict)
with open("/home/catalin/work/phd/v5b1_runs/conf3/tune.jsonl") as h:
    for line in h:
        r = json.loads(line)
        if r["name"].startswith("X1|"):
            T[r["name"][3:]][r["seed"]] = float(r["all_delay"])
seeds = sorted(T["p333"])
print("rules", len(T), "seeds", len(seeds), seeds[0], seeds[-1])
med = sorted((float(np.median([T[n][s] for s in seeds])), n) for n in T if len(T[n]) == len(seeds))
print("lowest medians:", [(n, round(m)) for m, n in med[:4]])
ref = np.median([T["p333"][s] for s in seeds])
pos = [n for n in T if n != "p333" and np.median([(T["p333"][s] - T[n][s]) / ref * 100 for s in seeds]) > 0]
print("rules with a positive paired point against p333:", sorted(pos))
