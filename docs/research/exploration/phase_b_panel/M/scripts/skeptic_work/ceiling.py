"""EXPLORATORY, read-only: is E (Screen M's accounting excess) a ceiling? Stored S6 rows, cell S, p333, 240 seeds.
(1) chance K0 fires at 5,300 on a fresh 240-seed sample drawn from the stored E values;
(2) where the delay tied to merge-2 slow minutes sits, by road, against what E counts."""
import pickle
import numpy as np
T = pickle.load(open("s.pkl", "rb"))
rng = np.random.default_rng(20261112)
P = T["p333"]; seeds = sorted(P); n = len(seeds)
G = ["1", "2", "3a", "3", "4a", "4", "5", "ramp1", "ramp2", "junction", "pending_main", "pending_ramp", "pending_ramp2"]
dl = {g: np.array([P[s]["dl"].get(g, 0.0) for s in seeds]) for g in G}
ds = {g: np.array([P[s]["ds"].get(g, 0.0) for s in seeds]) for g in G}
d = np.array([P[s]["d"] for s in seeds]); planned = np.array([P[s]["planned"] for s in seeds], float)
rate = lambda g: dl[g] / (ds[g] / 1000.0)
m1 = dl["3a"] - rate("2") * ds["3a"] / 1000.0
m2 = dl["4a"] - rate("3") * ds["4a"] / 1000.0
q = dl["pending_ramp"] + dl["pending_ramp2"]
E = 100 * (m1 + m2 + q) / d
print("sum of road groups minus all_delay, max abs veh-s: %.0f" % np.max(np.abs(sum(dl.values()) - d)))
print("E median %.2f; share of seeds with E < 5: %.1f %%" % (np.median(E), 100 * np.mean(E < 5)))
# (1) K0 at 5,300
fire = 0; ST = 4000; ubs = []
for _ in range(ST):
    x = E[rng.integers(0, n, 240)]
    b = np.median(x[rng.integers(0, 240, (1000, 240))], axis=1)
    ub = np.percentile(b, 98.75); ubs.append(ub); fire += ub < 5.0
print("K0 at 5,300: studies of 240 seeds resampled from the stored E: 97.5 %% upper bound below 5 in %d of %d; smallest upper bound %.2f" % (fire, ST, min(ubs)))
# (2) slow minutes
slow = np.array([P[s]["m2_acc_slow"] for s in seeds], float); up = np.array([P[s]["m2_up_slow"] for s in seeds], float)
print("4a minutes below 60 km/h: median %.1f, seeds with 0: %d; edge-3 slow minutes: median %.1f, seeds with 0: %d (of %d minutes)" % (np.median(slow), (slow == 0).sum(), np.median(up), (up == 0).sum(), P[seeds[0]]["m2_acc_nmin"]))
X = np.column_stack([np.ones(n), planned - planned.mean(), slow])
tot_c = 0.0
print("least squares per road group: delay_g = a + b x (planned - mean) + c x (4a slow minutes); c in veh-s per slow minute")
for g in G:
    c = np.linalg.lstsq(X, dl[g], rcond=None)[0][2]; tot_c += c
    print(f"   {g:14s} c = {c:8.1f}   mean delay {dl[g].mean():8.0f}")
call = np.linalg.lstsq(X, d, rcond=None)[0]
cE = np.linalg.lstsq(X, m1 + m2 + q, rcond=None)[0]
print("all_delay: c = %.1f (sum over groups %.1f), intercept %.0f = %.1f %% of mean; mean slow minutes %.2f -> slow-minute part %.1f %% of mean delay" % (call[2], tot_c, call[0], 100 * call[0] / d.mean(), slow.mean(), 100 * call[2] * slow.mean() / d.mean()))
print("E's numerator (veh-s): c = %.1f per slow minute, intercept %.0f; so E's numerator moves %.0f %% as much as all_delay per slow minute" % (cE[2], cE[0], 100 * cE[2] / call[2]))
c4a = np.linalg.lstsq(X, dl["4a"], rcond=None)[0][2]
print("share of the slow-minute slope on 4a itself: %.0f %%; on 3: %.0f %%; on 4+5: %.0f %%; on 1+2+3a: %.0f %%" % tuple(100 * np.linalg.lstsq(X, sum(dl[g] for g in gs), rcond=None)[0][2] / call[2] for gs in (["4a"], ["3"], ["4", "5"], ["1", "2", "3a"])))
z = slow == 0
print("seeds with 0 slow minutes at 4a: n %d; median all_delay %.0f against %.0f for all (%.1f %% lower); their E median %.2f %%; E numerator median %.0f against %.0f veh-s" % (z.sum(), np.median(d[z]), np.median(d), 100 * (1 - np.median(d[z]) / np.median(d)), np.median(E[z]), np.median((m1 + m2 + q)[z]), np.median(m1 + m2 + q)))
print("   difference of medians, all seeds minus no-slow seeds: all_delay %.0f veh-s; E numerator %.0f veh-s" % (np.median(d) - np.median(d[z]), np.median(m1 + m2 + q) - np.median((m1 + m2 + q)[z])))
print("rates veh-s per veh-km, medians: " + ", ".join(f"{g} {np.median(rate(g)):.2f}" for g in ["1", "2", "3a", "3", "4a", "4", "5"]))
print("rate on edge 3 against 4a slow minutes: corr %.2f; rate(3) median in no-slow seeds %.2f against %.2f in seeds with 10 or more slow minutes (n %d)" % (np.corrcoef(rate("3"), slow)[0, 1], np.median(rate("3")[z]), np.median(rate("3")[slow >= 10]), (slow >= 10).sum()))
print("run size N (veh-s): median %.0f" % np.median([P[s]["N"] for s in seeds]))
