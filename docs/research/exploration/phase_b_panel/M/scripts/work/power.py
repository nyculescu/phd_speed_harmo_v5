"""EXPLORATORY: null and power of screen M's rules, from stored S6 rows in cell S (240 paired seeds).
Per-seed differences of a stored lengthening rule against p333 are centred on their median, then shifted by a true effect e.
A study draws n seeds with replacement; statistic = median; percentile bootstrap (B = 2,000). Shifts are exact, so one draw serves every e."""
import pickle
import numpy as np
T, _ = pickle.load(open("parts.pkl", "rb"))
seeds = list(range(7480400, 7480640))
col = lambda arm, k: np.array([T[("S", arm)][s][k] for s in seeds], float)
tot = col("p333", "all_delay"); med = np.median(tot)
rng = np.random.default_rng(20261110)
STUD, B = 2000, 2000
EFF = (0.0, 1.5, 3.0, 4.6, 6.0, 7.2, 9.2)
def run(d, n, lo_pct, thr=3.0):
    d0 = d - np.median(d)
    m0 = np.empty(STUD); l0 = np.empty(STUD); u0 = np.empty(STUD)
    for i in range(STUD):
        x = d0[rng.integers(0, len(d0), n)]
        b = np.median(x[rng.integers(0, n, (B, n))], axis=1)
        m0[i] = np.median(x); l0[i], u0[i] = np.percentile(b, (lo_pct, 100 - lo_pct))
    out = ["%.1f" % (100 * np.mean((m0 + e >= thr) & (l0 + e > 0))) for e in EFF]
    return out, np.median(u0 - m0), np.median(m0 - l0), np.mean((l0 > 0)) * 100, np.mean(u0 < thr) * 100
print("effects e (points):", EFF)
for label, key, sign in (("delay edge over p333, % of p333's median", "all_delay", 1.0), ("merge-2 friction reduction, points of p333's median delay", "f2", 1.0)):
    print("##", label)
    for arm in ("z33133", "r4a1", "grid_r4a2"):
        d = 100 * (col("p333", key) - col(arm, key)) / med
        print(f" analog {arm}: sd {d.std(ddof=1):.2f}, robust sd {1.4826*np.median(np.abs(d-np.median(d))):.2f}")
        for lvl, lo in (("95", 2.5), ("97.5", 1.25)):
            for n in (40, 80, 120, 160):
                out, hu, hl, fp, excl = run(d, n, lo)
                print(f"   level {lvl} % n {n:3d}: pass % at e = {out}; half-widths up {hu:.2f} down {hl:.2f}; lower bound > 0 at e = 0: {fp:.1f} %; upper bound < 3 at e = 0: {excl:.1f} %")
