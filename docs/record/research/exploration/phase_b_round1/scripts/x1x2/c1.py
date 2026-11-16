from lib import *
import re
from a2 import DS, T, pooled, Q
rng = np.random.default_rng(20261110)
def diffs(c, rule, sets, learner=None):
    A, B = pooled(c, rule, sets, learner)
    ds = sorted(set(A) & set(B)); ref = np.median([val(B[k], "all_delay") for k in ds])
    return np.array([(val(B[k], "all_delay") - val(A[k], "all_delay")) / ref * 100 for k in ds])
def power(d, delta, n, outer=1500, inner=1000, pct=1.25):
    x0 = d - np.median(d) + delta
    hit = 0
    for _ in range(outer):
        s = x0[rng.integers(0, len(x0), n)]
        lo = np.percentile(np.median(s[rng.integers(0, n, (inner, n))], axis=1), pct)
        hit += lo > 0
    return hit / outer
def need(d, delta):
    for n in (10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 160, 200, 240):
        p = power(d, delta, n)
        if p >= 0.8:
            return n, p
    return None, p
Z = (2.2414 + 0.8416) ** 2
for c, rules in (("X1", ["p333", "lr1000_10_1", "os0_10_10"]), ("X2", ["os0_10_10", "lr1000_10_1", "p333"])):
    for r in rules:
        d = diffs(c, r, list(DS))
        sd = d.std(ddof=1); mad = 1.4826 * np.median(np.abs(d - np.median(d)))
        per = {s: diffs(c, r, [s]).std(ddof=1) for s in DS}
        ls = [diffs(c, r, list(DS), i).std(ddof=1) for i in range(5)]
        print(f"{c} vs {r}: n={len(d)} median {np.median(d):+.2f} mean {d.mean():+.2f} SD {sd:.2f} (per set " + ", ".join(f"{k} {v:.1f}" for k, v in per.items()) + f"); robust SD (MAD) {mad:.2f}; single-learner SD {min(ls):.1f}-{max(ls):.1f}")
        print(f"   normal approx (mean, 97.5 % two-sided, 80 % power): 3 % -> {int(np.ceil(Z*(sd/3)**2))}, 5 % -> {int(np.ceil(Z*(sd/5)**2))}; x pi/2 for a median of normal data: {int(np.ceil(Z*(sd/3)**2*np.pi/2))}, {int(np.ceil(Z*(sd/5)**2*np.pi/2))}")
        print(f"   resampling (median, percentile bootstrap 97.5 %): 3 % -> {need(d, 3.0)}, 5 % -> {need(d, 5.0)}", flush=True)
# Screen R as drafted: point >= 3 % and 97.5 % CI lower bound > 0 against the best non-learning arm, on 60 fresh seeds; resample from the 120 pooled seeds
pol = re.compile(r"^[a-z]\d(u\d+)?$")
for c in ("X1", "X2"):
    rules = [r for r in sorted({n.split("|")[1] for (n, q) in T["r1test"] if n.startswith(c + "|") and not pol.match(n.split("|")[1])}) if r != "nc"]
    D = np.array([diffs(c, r, list(DS)) for r in rules])     # rules x seeds, each in % of its own median
    # raw delays for choosing the best rule by median delay
    raw = []
    for r in rules:
        A, B = pooled(c, r, list(DS)); ds = sorted(set(A) & set(B)); raw.append([val(B[k], "all_delay") for k in ds])
    raw = np.array(raw)
    res = {"fixed p333": 0, "lowest median delay rule": 0, "smallest advantage rule": 0}
    R = 2000
    for _ in range(R):
        idx = rng.integers(0, D.shape[1], 60)
        def ok(d):
            lo = np.percentile(np.median(d[rng.integers(0, 60, (1000, 60))], axis=1), 1.25)
            return np.median(d) >= 3.0 and lo > 0
        res["fixed p333"] += ok(D[rules.index("p333"), idx])
        res["lowest median delay rule"] += ok(D[np.argmin(np.median(raw[:, idx], axis=1)), idx])
        res["smallest advantage rule"] += ok(D[np.argmin(np.median(D[:, idx], axis=1)), idx])
    print(c, "share of 60-seed resamples in which v3w is NOT killed in this cell (stored rules only):", {k: round(v / R, 2) for k, v in res.items()})
