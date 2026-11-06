"""E2 (V434): how often a delay rule passes a true tie, and what a non-inferiority margin needs.

Noise: paired per-seed delay differences (arm minus os1_15_10, X2 at 5,300, both 20-seed blocks)
of the 5 baseline-v3 policies and p333, as % of the reference median, each arm centred on 0.
Seeds are drawn with replacement from these centred differences, plus a true shift.
Statistic: median of paired differences, percentile bootstrap (the protocol convention).
"""
import gzip, json
import numpy as np

R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v3/rows/"
REF = "os1_15_10"
rows = {}
for f in ("conf3_eval_primary.jsonl.gz", "conf3b_eval_x2.jsonl.gz"):
    for line in gzip.open(R + f, "rt"):
        r = json.loads(line)
        cell, arm = r["name"].split("|", 1)
        if cell == "X2" and r["q"] == 5300.0:
            rows.setdefault(arm, {})[r["seed"]] = r["all_delay"]

arms = [a for a in sorted(rows) if a.startswith("d") and len(a) <= 3] + ["p333"]
pools = {}
for a in arms:
    s = sorted(k for k in rows[a] if k in rows[REF])
    d = np.array([rows[a][k] - rows[REF][k] for k in s])
    d = d / np.median([rows[REF][k] for k in s]) * 100
    pools[a] = d - np.median(d)
    print(f"{a}: n={len(s)}, sd of paired % diff {d.std(ddof=1):.1f}")

rng = np.random.default_rng(7434)
NS = (20, 40, 60, 80, 120, 160)
OUTER, INNER = 1000, 1000


def pass_rates(pool, n, shift):
    """Pass rates of: point estimate <= +2 %; upper 95 % / 97.5 % bound <= margin (2, 3, 5)."""
    x = pool[rng.integers(0, len(pool), (OUTER, n))] + shift
    pt = np.median(x, 1)
    idx = rng.integers(0, n, (INNER, n))
    up95 = np.empty(OUTER)
    up975 = np.empty(OUTER)
    for i in range(OUTER):
        b = np.median(x[i][idx], 1)
        up95[i], up975[i] = np.percentile(b, [97.5, 98.75])
    out = {"point<=2": np.mean(pt <= 2)}
    for m in (2, 3, 5):
        out[f"ni95<={m}"] = np.mean(up95 <= m)
        out[f"ni975<={m}"] = np.mean(up975 <= m)
    return out


for shift, label in ((0.0, "true tie: pass rate = power"),
                     (2.0, "true +2 % worse: pass rate = false pass for margin 2"),
                     (3.0, "true +3 % worse: false pass for margin 3"),
                     (5.0, "true +5 % worse: false pass for margin 5")):
    print(f"\n{label} (mean over {len(arms)} arms)")
    keys = None
    for n in NS:
        res = [pass_rates(pools[a], n, shift) for a in arms]
        keys = keys or list(res[0])
        if n == NS[0]:
            print("n " + " ".join(keys))
        print(f"{n} " + " ".join(f"{np.mean([r[k] for r in res]):.2f}" for k in keys))
