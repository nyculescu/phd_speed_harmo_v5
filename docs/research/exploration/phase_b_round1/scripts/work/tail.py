"""EXPLORATORY: distribution over seeds of the merge-excess delay under p333, cell S (stored S6 rows)."""
import pickle, sys
import numpy as np
D = pickle.load(open(sys.argv[1], "rb"))
REF = 100.0 / 3.6
tot = lambda p: sum(p.values()) if isinstance(p, dict) else float(np.sum(p))
for arm in ("S|p333", "S|os0_10_10", "S|nc"):
    X = []
    for s in sorted(D[arm]):
        r = D[arm][s]
        vs = {g: tot(p) for g, p in r["m_road_vs"].items()}; ds = {g: tot(p) for g, p in r["m_road_dist"].items()}
        dl = lambda g: vs[g] - ds.get(g, 0.0) / REF
        rate = lambda g: dl(g) / (ds[g] / 1000.0)
        m1 = dl("3a") - rate("2") * ds["3a"] / 1000.0
        m2 = dl("4a") - rate("3") * ds["4a"] / 1000.0
        X.append((r["all_delay"], m1, m2, r["end_stop2"], dl("pending_ramp") + dl("pending_ramp2") + dl("ramp1") + dl("ramp2")))
    X = np.array(X)
    q = lambda c: np.round(np.percentile(X[:, c], [10, 25, 50, 75, 90]), 0)
    print(arm, "all_delay p10..p90", q(0)); print("   merge-1 excess", q(1), "| merge-2 excess", q(2), "| end_stop2", q(3), "| ramps+ramp queues", q(4))
    print("   mean share of delay: m1 %.1f %%, m2 %.1f %%; top 10 %% of seeds by m2 hold %.0f %% of all m2 excess; corr(m2 excess, all_delay) %.2f; corr(m2 excess, end_stop2) %.2f" % (
        100 * X[:, 1].sum() / X[:, 0].sum(), 100 * X[:, 2].sum() / X[:, 0].sum(), 100 * np.sort(X[:, 2])[-24:].sum() / X[:, 2].sum(), np.corrcoef(X[:, 2], X[:, 0])[0, 1], np.corrcoef(X[:, 2], X[:, 3])[0, 1]))
