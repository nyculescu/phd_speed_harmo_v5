"""EXPLORATORY extras on the stored S6 rows: skew of the pooled arm, mean-based paired differences, a same-seed scheduler, TRUCK - S loss, close-following headroom."""
import json
import numpy as np
exec(open("analyse.py").read().split("out = {}")[0])     # loader and helpers only
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
def mdiff(P, O):
    d = (P - O) / np.mean(O) * 100.0; b = np.mean(d[IDX], axis=1); lo, hi = np.percentile(b, (2.5, 97.5)); return float(d.mean()), float(lo), float(hi)
for cell in ("TRUCK", "S"):
    print("\n#####", cell)
    P = pooled(cell, "all_delay"); L = {l: col(cell, l, "all_delay") for l in LEARN}
    med = {o: float(np.median(col(cell, o, "all_delay"))) for o in OPP}
    top = sorted(OPP, key=med.get)[:9]
    print("(a) pooled median %.0f; mean of the 5 learner medians %.0f; pooled mean %.0f" % (np.median(P), np.mean([np.median(x) for x in L.values()]), P.mean()))
    sk = lambda x: float(((x - x.mean()) ** 3).mean() / x.std() ** 3)
    print("    skewness of all_delay: single learner runs %s; pooled %.2f; %s %.2f" % (" ".join("%.2f" % sk(x) for x in L.values()), sk(P), top[0], sk(col(cell, top[0], "all_delay"))))
    print("    opp | pooled median-stat (pos = v3w better) | mean of 5 per-learner points | paired MEAN diff, pos = v3w higher delay, % of opp mean [95 % CI]")
    for o in top:
        O = col(cell, o, "all_delay")
        print("    %-16s %s | %+.2f | %s" % (o, f(eff(P, O)), np.mean([eff(x, O)[0] for x in L.values()]), f(mdiff(P, O))))
    if cell == "S":
        r = J["S"]["map"].get("os0_10_10", {}).get("delay"); print("    recorded S map os0_10_10 delay:", json.dumps(r))
    # (b) same-seed scheduler: on each seed pick the opponent with the lowest delay in the OTHER condition (same seed = same demand draw)
    other = "S" if cell == "TRUCK" else "TRUCK"
    M = np.array([col(cell, o, "all_delay") for o in OPP]); Mo = np.array([col(other, o, "all_delay") for o in OPP])
    best = min(med, key=med.get); bo = col(cell, best, "all_delay")
    pick = Mo.argmin(axis=0); sched = M[pick, np.arange(n)]
    print("(b) scheduler that picks per seed the opponent lowest in %s on that seed, vs best single %s (pos = scheduler lower):" % (other, best), f(eff(sched, bo)))
    rk = np.argsort(np.argsort(M, axis=0), axis=0); rko = np.argsort(np.argsort(Mo, axis=0), axis=0)
    rho = [np.corrcoef(rk[:, s], rko[:, s])[0, 1] for s in range(n)]
    print("    per-seed rank correlation of the 23 opponents' delay between TRUCK and S: median %.2f, IQR [%.2f, %.2f]" % (np.median(rho), *np.percentile(rho, (25, 75))))
    # seed-level winner persistence: correlation across seeds of (o - best) between conditions, after removing the seed mean over opponents
    R = M - M.mean(axis=0); Ro = Mo - Mo.mean(axis=0)
    cc = [np.corrcoef(R[i], Ro[i])[0, 1] for i in range(len(OPP))]
    print("    per-opponent correlation across seeds of its seed-centred delay in TRUCK and in S: median %.2f, min %.2f, max %.2f" % (np.median(cc), min(cc), max(cc)))
    # (d) close-following headroom
    cf = {o: col(cell, o, "ttc_net") for o in OPP + ["nc"]}; Pc = pooled(cell, "ttc_net")
    lo = min(OPP, key=lambda o: np.median(cf[o]))
    print("(d) close-following median s per run: nc %.1f, lowest opponent %s %.1f, v3w pooled %.1f; v3w vs nc %s; lowest opp vs nc %s" % (np.median(cf["nc"]), lo, np.median(cf[lo]), np.median(Pc), f(eff(Pc, cf["nc"])), f(eff(cf[lo], cf["nc"]))))
    print("    opponents with CI-clear lower cf than nc: %d of 23" % sum(eff(cf[o], cf["nc"])[1] > 0 for o in OPP))
# (c) TRUCK - S loss on the same seed
print("\n(c) loss = TRUCK - S delay on the same seed (veh-s), median [95 % CI]")
for a in ["nc", "lr1000_10_1", "os0_10_10", "grid_os1_10_10", "3E-D_TRUCK"]:
    print("   ", a, f(meddiff(col("TRUCK", a, "all_delay") - col("S", a, "all_delay"))))
print("    v3w pooled", f(meddiff(pooled("TRUCK", "all_delay") - pooled("S", "all_delay"))))
print("    recorded nc_median_loss:", J["cells"]["TRUCK"]["resilience"]["nc_median_loss"], "status:", J["cells"]["TRUCK"]["resilience"]["status"][:40])
