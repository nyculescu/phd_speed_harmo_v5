import json, numpy as np
p = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
roads = ("1", "2", "3a", "3", "4a", "4", "5", "r", "rj", "r2", "rj2")
acc = {r: [] for r in roads}; share = {r: [] for r in roads}
with open(p) as f:
    for line in f:
        if '"name": "S|p333"' not in line:
            continue
        r = json.loads(line)
        tot = sum(r.get(f"lv_n_{x}", 0.0) for x in roads)
        for x in roads:
            n = r.get(f"lv_n_{x}", 0.0)
            if n:
                acc[x].append(r[f"lv_sum_{x}"] / n); share[x].append(n / tot)
for x in roads:
    print(x, "mean level index", round(float(np.median(acc[x])), 3), "share of ALKS-seconds", round(float(np.median(share[x])), 3))
