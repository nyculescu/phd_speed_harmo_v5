"""EXPLORATORY, read-only: which (arm, seed) rows the stored S5 smoke holds. Names and seeds only."""
import json, glob, collections
c = collections.defaultdict(set)
for f in glob.glob("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s5/*/*.jsonl"):
    for line in open(f):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if "name" in r and "seed" in r:
            c[(f.split("/")[-2], r["name"])].add(r["seed"])
for k in sorted(c):
    if k[1].startswith("S|"):
        print(k, sorted(c[k]))
print(len(c), "arm entries in total")
