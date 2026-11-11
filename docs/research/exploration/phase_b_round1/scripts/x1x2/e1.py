from lib import *
import re
from a2 import DS, T, pooled, Q
from scipy.stats import spearmanr
pol = re.compile(r"^[a-z]\d(u\d+)?$")
for c in ("X1", "X2"):
    A, B = pooled(c, "p333", list(DS)); ds = sorted(A)
    dd = np.array([val(B[k], "all_delay") - val(A[k], "all_delay") for k in ds]); de = np.array([val(B[k], "end_stop2") - val(A[k], "end_stop2") for k in ds])
    r = spearmanr(dd, de)
    print(c, "per-seed (n=%d) Spearman of [p333 - v3w] delay with [p333 - v3w] lane-end stopped seconds at merge 2: %.2f (p %.3g); median end_stop2 p333 %.0f, v3w %.0f" % (len(ds), r.statistic, r.pvalue, np.median([val(B[k], "end_stop2") for k in ds]), np.median([val(A[k], "end_stop2") for k in ds])))
    rules = sorted({n.split("|")[1] for (n, q) in T["r2test"] if n.startswith(c + "|") and not pol.match(n.split("|")[1])})
    md, me = [], []
    for ru in rules:
        R = T["r2test"][(f"{c}|{ru}", Q)]
        md.append(np.median([val(x, "all_delay") for x in R.values()])); me.append(np.median([val(x, "end_stop2") for x in R.values()]))
    print("   r2test medians end_stop2:", ", ".join(f"{ru} {e:.0f}" for ru, e in sorted(zip(rules, me), key=lambda t: t[1])))
    Aw = pooled(c, "p333", ["r2test"])[0]
    print("   v3w per learner end_stop2 medians (r2test):", [round(float(np.median([val(x, "end_stop2") for x in T["r2test"][(f"{c}|{n}", Q)].values()]))) for n in DS["r2test"][1]])
    # delay edge vs p333 in seeds split by p333's own lane-end stops (halves)
    es = np.array([val(B[k], "end_stop2") for k in ds]); ref = np.median([val(B[k], "all_delay") for k in ds])
    lo, hi = dd[es <= np.median(es)], dd[es > np.median(es)]
    print("   edge vs p333 in seeds with p333 lane-end stops below/above the median: %.1f %% / %.1f %% (medians of paired diff over p333 median)" % (np.median(lo) / ref * 100, np.median(hi) / ref * 100))
