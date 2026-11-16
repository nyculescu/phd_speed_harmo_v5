"""EXPLORATORY: stored S6 rows. Delay of every non-learning arm against p333; paired spread; excess estimator and its placebo."""
import pickle, sys
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
rng = np.random.default_rng(20261110)
def ci(x, lev=95.0, B=10000):
    x = np.asarray(x, float)
    m = np.median(x[rng.integers(0, len(x), (B, len(x)))], axis=1)
    a = (100 - lev) / 2
    return np.median(x), np.percentile(m, a), np.percentile(m, 100 - a)
seeds = sorted(T["S|p333"])
print("n seeds", len(seeds), "keys", sorted(T["S|p333"][seeds[0]]["dl"]))
LEARN = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
for cond in ("S", "TRUCK"):
    base = np.array([T[f"{cond}|p333"][s]["d"] for s in seeds])
    med = np.median(base)
    print(f"\n{cond}: p333 median delay {med:.0f}; passed median {np.median([T[f'{cond}|p333'][s]['passed'] for s in seeds]):.0f}")
    rows = []
    for nm in sorted(T):
        c, a = nm.split("|", 1)
        if c != cond or a == "p333" or a in LEARN:
            continue
        x = np.array([T[nm][s]["d"] for s in seeds])
        d = 100.0 * (base - x) / med
        m, lo, hi = ci(d)
        _, lo2, hi2 = ci(d, 97.5)
        q = np.percentile(d, [25, 75])
        rows.append((m, a, lo, hi, lo2, hi2, d.std(ddof=1), (q[1] - q[0]) / 1.349, np.mean(d)))
    v = np.mean([[T[f"{cond}|{l}"][s]["d"] for s in seeds] for l in LEARN], axis=0)
    d = 100.0 * (base - v) / med
    m, lo, hi = ci(d)
    print(f"  v3w (mean of 5)   {m:+6.2f} [{lo:+6.2f}, {hi:+6.2f}] sd {d.std(ddof=1):.2f}")
    for m, a, lo, hi, lo2, hi2, sd, rsd, mean in sorted(rows, reverse=True):
        print(f"  {a:17s} {m:+6.2f} [{lo:+6.2f}, {hi:+6.2f}] 97.5%: [{lo2:+6.2f}, {hi2:+6.2f}]  sd {sd:5.2f}  robust sd {rsd:5.2f}  mean {mean:+6.2f}")
    # excess estimator and placebo
    def parts(nm):
        E, P1, P2, M1, M2 = [], [], [], [], []
        for s in seeds:
            r = T[nm][s]; dl, ds = r["dl"], r["ds"]
            rate = lambda g: dl[g] / max(ds[g] / 1000.0, 1e-9)
            m1 = dl["3a"] - rate("2") * ds["3a"] / 1000.0
            m2 = dl["4a"] - rate("3") * ds["4a"] / 1000.0
            q = dl.get("pending_ramp", 0.0) + dl.get("pending_ramp2", 0.0)
            E.append(100 * (m1 + m2 + q) / r["d"]); M1.append(100 * m1 / r["d"]); M2.append(100 * m2 / r["d"])
            P1.append(100 * (dl["2"] - rate("1") * ds["2"] / 1000.0) / r["d"])
            P2.append(100 * (dl["5"] - rate("4") * ds["5"] / 1000.0) / r["d"])
        return map(np.array, (E, M1, M2, P1, P2))
    for nm in ("p333", "nc", "os0_10_10"):
        E, M1, M2, P1, P2 = parts(f"{cond}|{nm}")
        print(f"  excess {nm}: total %.2f [%.2f, %.2f]" % ci(E), "| merge1 %.2f [%.2f, %.2f]" % ci(M1), "| merge2 %.2f [%.2f, %.2f]" % ci(M2), "| placebo 2-vs-1 %.2f [%.2f, %.2f]" % ci(P1), "| placebo 5-vs-4 %.2f [%.2f, %.2f]" % ci(P2), "| total 97.5%%: [%.2f, %.2f]" % ci(E, 97.5)[1:])
        print(f"     quantiles of total excess share p05 {np.percentile(E,5):.2f} p25 {np.percentile(E,25):.2f} p75 {np.percentile(E,75):.2f} p95 {np.percentile(E,95):.2f}; share of seeds below 5 %: {100*np.mean(E<5):.1f}")
