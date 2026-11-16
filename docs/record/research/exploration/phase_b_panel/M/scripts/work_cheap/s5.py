"""Which seeds the stored S5 rows hold for p333 (read-only)."""
import json, glob
from collections import Counter
for p in sorted(glob.glob('/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s5/*/*.jsonl')):
    c = Counter()
    for line in open(p):
        r = json.loads(line)
        if r["name"].endswith("|p333"):
            c[(r["name"], r["seed"], r.get("q"))] += 1
    print(p.split("/s5/")[1], sorted(c.items()))
