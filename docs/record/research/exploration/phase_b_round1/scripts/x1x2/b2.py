import pickle, numpy as np
from b1 import PER, SEG, W
res = pickle.load(open("b1.pkl", "rb"))
rng = np.random.default_rng(20261110)
def ci(d, f=np.mean):
    b = f(d[rng.integers(0, len(d), (10000, len(d)))], axis=1)
    return np.percentile(b, [2.5, 97.5])
for cell, C in res.items():
    seeds = sorted(C["p333"])
    arm = {s: {k: np.mean([C[w][s][k] for w in W], axis=0) for k in C[W[0]][s]} for s in seeds}
    for rule in [a for a in C if a not in W]:
        d = {k: np.array([C[rule][s][k] - arm[s][k] for s in seeds]) for k in arm[seeds[0]] if k[0] != "cumflow"}
        tot = d[("total", "", "")]; ref = np.median([C[rule][s][("total", "", "")] for s in seeds])
        print(f"\n## {cell} rule {rule} minus v3w arm, n={len(seeds)}; total diff mean {tot.mean():.0f} veh-s ({tot.mean()/ref*100:+.1f} % of rule median {ref:.0f}), median {np.median(tot):.0f} ({np.median(tot)/ref*100:+.1f} %)")
        for k in ("main_all", "pend_all", "resid", "N", "dist", "N_off_main"):
            x = d[(k, "", "")]; lo, hi = ci(x)
            print(f"  {k}: mean {x.mean():+.0f} [{lo:+.0f}, {hi:+.0f}] = {x.mean()/tot.mean()*100:.0f} % of total mean diff")
        for k in ("end_stop2", "end_stop", "passed", "arrived", "delay_ramp2", "delay_ramp", "delay"):
            x = d[(k, "", "")]; lo, hi = ci(x)
            print(f"  {k}: rule med {np.median([C[rule][s][(k,'','')] for s in seeds]):.1f} v3w med {np.median([arm[s][(k,'','')] for s in seeds]):.1f} mean diff {x.mean():+.1f} [{lo:+.1f}, {hi:+.1f}]")
        print("  mainline delay diff by period x segment: mean veh-s (share of total mean diff %); * = 95 % CI of mean excludes 0")
        print("  period | " + " | ".join(s[0] for s in SEG) + " | row sum | per 100 s | pend r1 | pend r2 | stopped r2 (veh-s)")
        for pn, a, b in PER[cell]:
            cells = []
            rs = np.zeros(len(seeds))
            for sn, _, _ in SEG:
                x = d[("main", pn, sn)]; rs += x; lo, hi = ci(x)
                cells.append(f"{x.mean():+.0f} ({x.mean()/tot.mean()*100:+.0f}){'*' if lo > 0 or hi < 0 else ''}")
            lo, hi = ci(rs)
            ex = []
            for k in ("pend_r1", "pend_r2", "queue_r2"):
                x = d[(k, pn, "")]; l2, h2 = ci(x); ex.append(f"{x.mean():+.0f}{'*' if l2 > 0 or h2 < 0 else ''}")
            print(f"  {pn} | " + " | ".join(cells) + f" | {rs.mean():+.0f} ({rs.mean()/tot.mean()*100:+.0f}){'*' if lo > 0 or hi < 0 else ''} | {rs.mean()/(b-a)*100:+.0f} | " + " | ".join(ex))
        cf = np.array([C[rule][s][("cumflow", "", "")] - arm[s][("cumflow", "", "")] for s in seeds])
        print("  cumulative vehicles into road 4 (rule minus v3w), mean at min 5,7,9,12,15,17,19,22,25:", " ".join(f"{cf[:, i-1].mean():+.1f}" for i in (5, 7, 9, 12, 15, 17, 19, 22, 25)))
