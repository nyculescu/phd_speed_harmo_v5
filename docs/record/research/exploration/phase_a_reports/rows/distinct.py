"""EXPLORATORY: how many distinct runs the 23 opponents give per seed; nc close-following by condition."""
import numpy as np
exec(open("analyse.py").read().split("out = {}")[0])
for cell in ("TRUCK", "S"):
    M = np.array([col(cell, o, "all_delay") for o in OPP])
    nd = np.array([len(set(M[:, s])) for s in range(n)])
    print(cell, "distinct delay values among 23 opponents per seed: median %d, min %d, max %d" % (np.median(nd), nd.min(), nd.max()))
    print("  nc cf median %.1f mean %.1f; nc delay median %.0f" % (np.median(col(cell, "nc", "ttc_net")), np.mean(col(cell, "nc", "ttc_net")), np.median(col(cell, "nc", "all_delay"))))
    best = OPP[int(np.argmin(np.median(M, axis=1)))]
    same = {o: int((M[OPP.index(o)] == M[OPP.index(best)]).sum()) for o in OPP if o != best}
    print("  seeds on which an opponent's delay equals the best single's (%s):" % best, {k: v for k, v in sorted(same.items(), key=lambda kv: -kv[1]) if v > 0})
    # winner shares with identical runs merged: share of seeds on which the best single is within 0.5 % and 1 % of the per-seed minimum
    bo = M[OPP.index(best)]; mn = M.min(axis=0)
    print("  best single within 0.5 %% of the per-seed minimum on %.1f %% of seeds, within 1 %% on %.1f %%, within 2 %% on %.1f %%" % tuple(100 * np.mean(bo <= mn * (1 + t)) for t in (0.005, 0.01, 0.02)))
    print("  per-seed gap best single - minimum, %% of best median: quartiles %s" % np.round(np.percentile((bo - mn) / np.median(bo) * 100, (25, 50, 75, 90)), 2))
