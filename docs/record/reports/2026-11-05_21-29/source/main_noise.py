import gzip, json, sys, numpy as np
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v3/rows/"
rows = {}
for f, blk in (("conf3_eval_primary.jsonl.gz", "orig"), ("conf3b_eval_x2.jsonl.gz", "fresh")):
    for line in gzip.open(R + f, "rt"):
        r = json.loads(line)
        cell, arm = r["name"].split("|", 1)
        if cell != "X2" or r["q"] != 5300.0:
            continue
        rows.setdefault(arm, {})[r["seed"]] = (r["ttc_net"] if "ttc_net" in r else r["ttc3"], r["all_delay"], blk)
print("arms:", sorted(rows)[:40])
rng = np.random.default_rng(0)
def stat(arm, ref, blks):
    s = sorted(k for k in rows[arm] if k in rows[ref] and rows[arm][k][2] in blks)
    a = np.array([rows[arm][k][:2] for k in s]); b = np.array([rows[ref][k][:2] for k in s])
    d = a - b; med = np.median(b, 0)
    pt = np.median(d, 0) / med * 100
    bs = np.array([np.median(d[i], 0) for i in rng.integers(0, len(s), (5000, len(s)))]) / med * 100
    lo, hi = np.percentile(bs, [2.5, 97.5], 0)
    return len(s), pt, lo, hi
ref = "os1_15_10"
pol = [a for a in sorted(rows) if a.startswith("d") and len(a) <= 3]
for blks in (("orig",), ("fresh",), ("orig", "fresh")):
    for arm in pol + ["p333"]:
        n, pt, lo, hi = stat(arm, ref, blks)
        print(f"{'+'.join(blks):10s} {arm:6s} n={n} ttc {pt[0]:6.1f} [{lo[0]:6.1f},{hi[0]:6.1f}]  delay {pt[1]:5.1f} [{lo[1]:5.1f},{hi[1]:5.1f}]")
