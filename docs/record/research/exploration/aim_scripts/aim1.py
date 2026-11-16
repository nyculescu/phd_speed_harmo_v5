"""EXPLORATORY: tail (worst days), ramp against all, fuel per km; S6 rows, already read for a verdict."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["p333", "3E-C_TRUCK", "os0_10_10", "nc"]
K = ["all_delay", "delay", "delay_ramp", "delay_ramp2", "fuel_km"]
T = {}
for line in open(ROWS):
    r = json.loads(line); c, a = r["name"].split("|", 1)
    if a in L or a in OPP:
        T[(c, a, r["seed"])] = [r.get(k) for k in K]
seeds = list(range(7480400, 7480640)); n = len(seeds)
rng = np.random.default_rng(20261110); IDX = rng.integers(0, n, (2000, n))
def col(c, a, j): return np.array([float(T[(c, a, s)][j]) if T[(c, a, s)][j] is not None else np.nan for s in seeds])
def ci(f):
    b = np.array([f(i) for i in IDX]); return "%+.2f [%+.2f, %+.2f]" % (f(np.arange(n)), *np.nanpercentile(b, (2.5, 97.5)))
for c in ("TRUCK", "S"):
    print("#####", c, "(positive = v3w lower; single learners, mean over 5; seed bootstrap 95 %)")
    for o in OPP:
        O = col(c, o, 0); P = [col(c, l, 0) for l in L]
        # worst days: the 24 seeds (10 %) where no control has the most delay
        nc = col(c, "nc", 0)
        def tail(i):
            cut = np.quantile(nc[i], 0.9); m = nc[i] >= cut
            return np.mean([np.mean(O[i][m] - p[i][m]) for p in P]) / np.mean(O[i][m]) * 100
        def p90(i):
            return np.mean([(np.quantile(O[i], 0.9) - np.quantile(p[i], 0.9)) for p in P]) / np.quantile(O[i], 0.9) * 100
        def med(j):
            Oj = col(c, o, j); Pj = [col(c, l, j) for l in L]
            return lambda i: np.mean([np.nanmedian(Oj[i] - p[i]) for p in Pj]) / np.nanmedian(Oj[i]) * 100
        print(" vs %-11s worst-10%%-days delay %s | 90th pct of days %s" % (o, ci(tail), ci(p90)))
        print("                ramp1 trip delay %s | ramp2 %s | fuel/km %s" % (ci(med(2)), ci(med(3)), ci(med(4))))
    for a in ["p333", "3E-C_TRUCK", "nc"] + L[:1]:
        d, r1, r2 = (np.nanmedian(col(c, a, j)) for j in (1, 2, 3))
        print("   medians %-11s all trips %.1f s, ramp1 %.1f s, ramp2 %.1f s, ramp2/all %.2f" % (a, d, r1, r2, r2 / d))
