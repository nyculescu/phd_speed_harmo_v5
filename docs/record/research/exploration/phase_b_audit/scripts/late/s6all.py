"""Read-only: all_delay of every S6 arm, both cells. EXPLORATORY."""
import json, pickle
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
T = {}
with open(ROWS) as h:
    for line in h:
        r = json.loads(line)
        cell, arm = r["name"].split("|", 1)
        T.setdefault((cell, arm), {})[r["seed"]] = float(r["all_delay"])
pickle.dump(T, open("s6all.pkl", "wb"))
print(len(T))
