"""EXPLORATORY (rows already read for the S6 verdict). Operating characteristic of screen F's KILL rule on the stored TRUCK rows:
v3w pooled (per-seed mean of 5 learners) against 3E-C_TRUCK, close-following (ttc_net). No simulation of traffic."""
import numpy as np
Z = np.load("s6_scalars.npz"); KEYS = list(Z["keys"]); n = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda cell, arm, key: Z[f"{cell}|{arm}"][:, KEYS.index(key)]
pooled = lambda cell, key: np.mean([col(cell, l, key) for l in LEARN], axis=0)
rng = np.random.default_rng(20261110)
IDX = rng.integers(0, n, (10_000, n))
def eff(P, O, pct=(2.5, 97.5)):
    d = -(P - O) / np.median(O) * 100.0
    b = np.median(d[IDX], axis=1)
    return float(np.median(d)), *map(float, np.percentile(b, pct))
f = lambda t: "%+.2f [%+.2f, %+.2f]" % tuple(t)
for cell in ("TRUCK", "S"):
    P, O, R = pooled(cell, "ttc_net"), col(cell, "3E-C_TRUCK", "ttc_net"), col(cell, "p333", "ttc_net")
    d = -(P - O) / np.median(O) * 100.0
    print(cell, "v3w pooled vs 3E-C cf: 95 %", f(eff(P, O)), "| 97.5 %", f(eff(P, O, (1.25, 98.75))))
    print("   paired diff, %% of 3E-C median: mean %.2f, SD %.2f, IQR [%.2f, %.2f], skew %.2f; share of seeds with v3w lower %.3f" % (
        d.mean(), d.std(ddof=1), *np.percentile(d, (25, 75)), ((d - d.mean()) ** 3).mean() / d.std() ** 3, (d > 0).mean()))
    print("   medians s/run: v3w %.1f, 3E-C %.1f, p333 %.1f; SD across seeds: v3w %.1f, 3E-C %.1f, p333 %.1f" % (np.median(P), np.median(O), np.median(R), P.std(ddof=1), O.std(ddof=1), R.std(ddof=1)))
    per = [eff(col(cell, l, "ttc_net"), O, (1.25, 98.75)) for l in LEARN]
    print("   per learner 97.5 %:", " | ".join(f(p) for p in per))
    dd = -(pooled(cell, "all_delay") - col(cell, "3E-C_TRUCK", "all_delay")) / np.median(col(cell, "3E-C_TRUCK", "all_delay")) * 100
    print("   delay paired diff v3w vs 3E-C: median %.2f, SD %.2f %%" % (np.median(dd), dd.std(ddof=1)))
    dp = -(col(cell, "3E-C_TRUCK", "ttc_net") - R) / np.median(R) * 100.0
    print("   3E-C vs p333 cf (pos = 3E-C fewer): 95 %", f(eff(col(cell, "3E-C_TRUCK", "ttc_net"), R)), "SD %.2f" % dp.std(ddof=1))

# operating characteristic in TRUCK
P, O = pooled("TRUCK", "ttc_net"), col("TRUCK", "3E-C_TRUCK", "ttc_net")
obs = float(np.median(-(P - O) / np.median(O) * 100.0))
def oc(true, m, level, studies=4000, B=1000, one=None):
    Pu = (P if one is None else col("TRUCK", one, "ttc_net"))
    base = float(np.median(-(Pu - O) / np.median(O) * 100.0))
    Ps = Pu + (base - true) / 100.0 * np.median(O)      # shift so that the 240-seed statistic equals `true`
    r = np.random.default_rng(20261111)
    kill_pt = kill_lb = kill = 0
    pts = []
    for _ in range(studies):
        s = r.integers(0, n, m)
        p, o = Ps[s], O[s]
        d = -(p - o) / np.median(o) * 100.0
        b = np.median(d[r.integers(0, m, (B, m))], axis=1)
        lo = np.percentile(b, (100 - level) / 2)
        pt = np.median(d); pts.append(pt)
        a, c = pt < 10.0, lo <= 0.0
        kill_pt += a; kill_lb += c; kill += (a or c)
    return kill / studies, kill_pt / studies, kill_lb / studies, float(np.std(pts))
print("\nScreen F KILL rule (point < 10 % or lower bound <= 0), v3w pooled vs a rule with 3E-C's seed-level noise, TRUCK; 4,000 simulated studies, 1,000 bootstrap resamples each, rng 20261111")
print("true edge % | seeds | CI level | P(KILL) | P(point<10) | P(lb<=0) | SD of the point")
for m in (80, 240):
    for level in (97.5, 95.0):
        for true in (0.0, 5.0, 8.0, 10.0, 11.8, 12.0, 15.0, 18.0, 20.0, 25.0):
            k, a, c, sd = oc(true, m, level)
            print("%5.1f | %3d | %.1f | %.3f | %.3f | %.3f | %.2f" % (true, m, level, k, a, c, sd))
print("\nseeds needed (97.5 %): P(KILL) at true 12 % and true 15 %")
for m in (80, 160, 240, 400, 800):
    print(m, "true 12: %.3f" % oc(12.0, m, 97.5, studies=2000, B=600)[0], "| true 15: %.3f" % oc(15.0, m, 97.5, studies=2000, B=600)[0], "| true 0 pass: %.4f" % (1 - oc(0.0, m, 97.5, studies=2000, B=600)[0]))
print("\nsingle learner (w3u500) instead of the pooled arm, 80 seeds, 97.5 %:")
for true in (0.0, 12.0, 20.0):
    print(true, "P(KILL) %.3f" % oc(true, 80, 97.5, one="w3u500")[0])
