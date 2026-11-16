import json, sys
import numpy as np
sys.path.insert(0, ".")
from prev_check import EVAL, fixed, paired, IDX
D = json.load(open("delays.json"))["res"]
R = json.load(open("/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"))
for q in ("1600", "2000"):
    a = R["tune"]["arms"][q]
    E = lambda g: np.array([D[fixed(g, "none", q, s)][0] for s in EVAL])
    n0 = E(a["N"])
    print(f"== q {q}: N clean histogram (s/veh) bins 0-50-100-150-200-300-400-600:",
          np.histogram(n0, [0, 50, 100, 150, 200, 300, 400, 600])[0].tolist())
    arms = [(x, a[x]) for x in ("FX", "FB", "PI", "AD")] + [("NC", "NC")]
    arms += [(f"{x}_pi{p}", g) for p, v in a["prev"].items() for x, g in v.items() if x in ("PI", "FB")]
    for lab, g in arms:
        x = E(g)
        p = paired(x, n0)            # ref = arm, treat = N: diff = median(arm - N)
        d = x - n0
        sm = d[IDX].mean(1)
        print(f"  {lab:10s} {g:14s} med {np.median(x):6.1f} vs N {np.median(n0):6.1f} | paired median(arm-N) {p['diff']:6.1f} "
              f"[{p['diff_ci'][0]:6.1f}, {p['diff_ci'][1]:6.1f}] | mean(arm-N) {d.mean():6.1f} [{np.percentile(sm,2.5):6.1f}, {np.percentile(sm,97.5):6.1f}]"
              f" | arm worse on {100*np.mean(d>0):.0f} %")
    # breakdown co-occurrence: N high vs PI high
    pi_ = E(a["PI"]); thr = 2*np.median(n0)
    print("  seeds N>2med:", int((n0>thr).sum()), " of which PI>2med:", int(((n0>thr)&(pi_>thr)).sum()),
          " PI>2med & N<=2med:", int(((n0<=thr)&(pi_>thr)).sum()))
