"""EXPLORATORY, read-only: own check of Screen M's stage-0 numbers and of the skeptic's M-all-1 (stored S6 rows, cell S, 240 seeds)."""
import pickle
import numpy as np
T = pickle.load(open("mine.pkl", "rb"))
rng = np.random.default_rng(7791)
REF = 100.0 / 3.6
P = T["p333"]; seeds = sorted(P); n = len(seeds)
G = sorted(P[seeds[0]]["vs"])
dl = {g: np.array([P[s]["vs"].get(g, 0.0) - P[s]["ds"].get(g, 0.0) / REF for s in seeds]) for g in G}
ds = {g: np.array([P[s]["ds"].get(g, 0.0) for s in seeds]) for g in G}
d = np.array([P[s]["d"] for s in seeds], float)
planned = np.array([P[s]["planned"] for s in seeds], float)
print("p333 median all_delay %.0f; max |sum of groups - all_delay| %.0f" % (np.median(d), np.max(np.abs(sum(dl.values()) - d))))
rate = lambda g: dl[g] / (ds[g] / 1000.0)
m1 = dl["3a"] - rate("2") * ds["3a"] / 1000.0
m2 = dl["4a"] - rate("3") * ds["4a"] / 1000.0
q = dl["pending_ramp"] + dl["pending_ramp2"]
num = m1 + m2 + q
E = 100 * num / d
def ci(x, lev, B=10000):
    b = np.median(x[rng.integers(0, len(x), (B, len(x)))], axis=1); a = (100 - lev) / 2
    return np.percentile(b, a), np.percentile(b, 100 - a)
print("E median %.2f, 97.5 %% CI [%.2f, %.2f], 95 %% CI [%.2f, %.2f]" % (np.median(E), *ci(E, 97.5), *ci(E, 95)))
print("  merge-1 part median %.2f %%, merge-2 part %.2f %%, queues %.2f %%; mean shares %.2f / %.2f / %.2f" % (np.median(100 * m1 / d), np.median(100 * m2 / d), np.median(100 * q / d), np.mean(100 * m1 / d), np.mean(100 * m2 / d), np.mean(100 * q / d)))
# placebo: the same formula on road pairs with no merge
pl1 = dl["2"] - rate("1") * ds["2"] / 1000.0
pl2 = dl["5"] - rate("4") * ds["5"] / 1000.0
print("  placebo pairs (no merge): edge 2 against 1: %.2f %%; edge 5 against 4: %.2f %%" % (np.median(100 * pl1 / d), np.median(100 * pl2 / d)))
# K0 at 5,300: can it fire?
fire = 0; ST = 2000; lo = 1e9
for _ in range(ST):
    x = E[rng.integers(0, n, 240)]
    ub = np.percentile(np.median(x[rng.integers(0, 240, (1000, 240))], axis=1), 98.75)
    fire += ub < 5.0; lo = min(lo, ub)
print("K0 at 5,300: upper bound below 5 in %d of %d resampled studies; smallest upper bound %.2f" % (fire, ST, lo))
# slow minutes
slow = np.array([P[s]["m2_acc_slow"] for s in seeds], float); up = np.array([P[s]["m2_up_slow"] for s in seeds], float)
print("4a slow minutes: median %.1f, mean %.2f, seeds with 0: %d; edge-3 (m2_up) slow minutes: median %.1f, seeds with 0: %d; minutes %d" % (np.median(slow), slow.mean(), (slow == 0).sum(), np.median(up), (up == 0).sum(), P[seeds[0]]["m2_acc_nmin"]))
X = np.column_stack([np.ones(n), planned - planned.mean(), slow])
fit = lambda y: np.linalg.lstsq(X, y, rcond=None)[0]
ca = fit(d); ce = fit(num)
res = d - X @ ca
print("all_delay = %.0f + %.0f x (planned - mean) + %.0f x slow minutes; R2 %.2f; intercept %.1f %% of mean; slow-minute part %.1f %% of mean delay" % (ca[0], ca[1], ca[2], 1 - res.var() / d.var(), 100 * ca[0] / d.mean(), 100 * ca[2] * slow.mean() / d.mean()))
print("E numerator slope %.0f veh-s per slow minute = %.0f %% of all_delay's slope" % (ce[2], 100 * ce[2] / ca[2]))
for lab, gs in (("4a", ["4a"]), ("3", ["3"]), ("4+5", ["4", "5"]), ("1+2+3a", ["1", "2", "3a"]), ("ramp2+queue+junction", ["ramp2", "pending_ramp2", "junction"])):
    print("   slope share on %s: %.0f %%" % (lab, 100 * fit(sum(dl[g] for g in gs))[2] / ca[2]))
z = slow == 0
print("seeds with no slow minute: n %d; E median %.2f %%; all_delay median %.0f (%.1f %% below all seeds)" % (z.sum(), np.median(E[z]), np.median(d[z]), 100 * (1 - np.median(d[z]) / np.median(d))))
print("corr(E numerator, all_delay) %.2f; corr(merge-2 part, end_stop2) %.2f; end_stop2 median %.1f, p90 %.0f" % (np.corrcoef(num, d)[0, 1], np.corrcoef(m2, [P[s]["end2"] for s in seeds])[0, 1], np.median([P[s]["end2"] for s in seeds]), np.percentile([P[s]["end2"] for s in seeds], 90)))
print("ramp insertion queues p333: ramp1 median %.0f, ramp2 median %.0f veh-s; N median %.0f; passed median %.0f; planned median %.0f" % (np.median(dl["pending_ramp"]), np.median(dl["pending_ramp2"]), np.median([P[s]["N"] for s in seeds]), np.median([P[s]["passed"] for s in seeds]), np.median(planned)))
# arms against p333
col = lambda a: np.array([T[a][s]["d"] for s in seeds], float)
LEARN = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
print("arm against p333: median paired difference %% of p333's median [97.5 %% CI], paired SD %%, identical seeds, stuck rows, collisions sum")
pos = []
for a in sorted(T):
    if a in LEARN or a == "p333":
        continue
    x = 100 * (d - col(a)) / np.median(d)
    lo_, hi_ = ci(x, 97.5)
    st = sum(T[a][s]["stuck"] > 0 for s in seeds)
    if np.median(x) > 0:
        pos.append(a)
    print("   %-18s %+7.2f [%+.2f, %+.2f]  SD %5.1f  same %3d  stuck rows %d  collisions %d" % (a, np.median(x), lo_, hi_, x.std(ddof=1), int((x == 0).sum()), st, sum(T[a][s]["col"] for s in seeds)))
print("rules or opponents with a positive median paired difference:", pos)
print("p333: stuck rows %d (seeds %s); collisions %d; alks_full_moving sum %s; tau_mismatch max %s" % (sum(P[s]["stuck"] > 0 for s in seeds), [s for s in seeds if P[s]["stuck"] > 0], sum(P[s]["col"] for s in seeds), sum((P[s]["afm"] or 0) for s in seeds), max(P[s]["tm"] for s in seeds)))
