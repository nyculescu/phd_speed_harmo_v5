"""EXPLORATORY: lane use between the merges and where ramp vehicles change lane (stored S6 rows, cell S)."""
import pickle, sys
import numpy as np
D = pickle.load(open(sys.argv[1], "rb"))
for arm in ("S|nc", "S|p333"):
    rows = D[arm]
    seeds = sorted(rows)
    sh, sp, m1, m2 = [], [], [], []
    for s in seeds:
        r = rows[s]
        nv = np.array([r["nv_3_0"], r["nv_3_1"], r["nv_3_2"]])
        n = np.array([r["n_3_0"], r["n_3_1"], r["n_3_2"]])
        sh.append(100 * nv / nv.sum())
        sp.append(3.6 * nv / n)
        m1.append(np.array(r["m_mergepos_m1"], float)); m2.append(np.array(r["m_mergepos_m2"], float))
    sh, sp = np.median(sh, axis=0), np.median(sp, axis=0)
    a, b = np.sum(m1, axis=0), np.sum(m2, axis=0)
    print(arm, "edge 3 flow share by lane % (0,1,2):", np.round(sh, 1), "mean speed km/h:", np.round(sp, 1))
    print("   merge position histogram, share % per bin, merge 1:", np.round(100 * a / a.sum(), 1), "| merge 2:", np.round(100 * b / b.sum(), 1))
