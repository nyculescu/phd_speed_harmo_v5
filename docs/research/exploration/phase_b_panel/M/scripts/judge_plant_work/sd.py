import json, numpy as np
p = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
want = {"p333", "z33133", "r4a1", "grid_r4a2", "grid_z31333", "os0_10_10", "os1_10_0", "nc", "3E-D_TRUCK", "lr1000_16_2", "os1_15_10"}
d = {}
with open(p) as f:
    for line in f:
        if '"cell": "S"' not in line and '"cell":"S"' not in line:
            continue
        r = json.loads(line)
        a = r.get("arm") or r.get("name")
        if r.get("cell") == "S" and a in want:
            d.setdefault(a, {})[r["seed"]] = r["all_delay"]
seeds = sorted(d["p333"])
P = np.array([d["p333"][s] for s in seeds])
print("n", len(seeds), "median p333", round(float(np.median(P))), "sd p333 %", round(float(P.std(ddof=1) / np.median(P) * 100), 1))
rng = np.random.default_rng(20261110)
idx = rng.integers(0, len(seeds), (10000, len(seeds)))
for a in sorted(want - {"p333"}):
    A = np.array([d[a][s] for s in seeds])
    diff = P - A
    e = np.median(diff) / np.median(P) * 100
    b = np.median(diff[idx], axis=1) / np.median(P) * 100
    mad = 1.4826 * np.median(np.abs(diff - np.median(diff))) / np.median(P) * 100
    print(f"{a:14s} edge {e:+6.2f} [{np.percentile(b, 2.5):+.2f}, {np.percentile(b, 97.5):+.2f}]  95%   [{np.percentile(b, 1.25):+.2f}, {np.percentile(b, 98.75):+.2f}] 97.5%  paired SD {diff.std(ddof=1) / np.median(P) * 100:5.1f} %  robust {mad:5.1f} %  identical seeds {int((diff == 0).sum())}")
