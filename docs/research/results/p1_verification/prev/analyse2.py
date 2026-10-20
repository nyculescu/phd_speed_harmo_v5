"""Mean (expected-value) view, win shares and clean-day bimodality, for IP / ID vs the strongest pi-retuned arms."""
import json
import sys

import numpy as np

sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/59738c75-cfe8-434e-99ee-b78b7087de37/scratchpad/p1v/prev")
from prev_check import EVAL, fixed, sw, mix, IDX  # noqa: E402

D = json.load(open(sys.argv[1]))["res"]
R = json.load(open("/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"))
arms = R["tune"]["arms"]
L0 = ("N", "FX", "FB", "PI", "AD")


def E(g, c, q):
    return np.array([D[fixed(g, c, q, s)][0] for s in EVAL])


def mean_ci(r, t):
    d = r - t
    sd, sr = d[IDX].mean(1), r[IDX].mean(1)
    rb = sd / sr
    return d.mean(), np.percentile(sd, [2.5, 97.5]), d.mean() / r.mean(), np.percentile(rb, [2.5, 97.5])


for q in ("1600", "2000"):
    a = arms[q]
    N = a["N"]
    ip = {inc: np.array([D[sw(N, a["IP"][inc], inc, q, s)][0] for s in EVAL]) for inc in ("slow", "block")}
    idd = {inc: np.array([D[sw(N, a["ID"], inc, q, s)][0] for s in EVAL]) for inc in ("slow", "block")}
    n0 = E(N, "none", q)
    print(f"\n========== q {q}")
    # clean-day bimodality: share of N clean-day seeds above 2x the median
    for g, lab in [(N, "N"), (a["PI"], "PI"), (a["prev"]["0.1"]["PI"], "PI_pi0.1"), (a["prev"]["0.25"]["PI"], "PI_pi0.25"),
                   (a["prev"]["0.5"]["PI"], "PI_pi0.5"), (a["FB"], "FB"), ("NC", "NC")]:
        x = E(g, "none", q)
        print(f"  clean {lab:10s} ({g:14s}) mean {x.mean():6.1f} median {np.median(x):6.1f} "
              f"share > 2*median(N) {np.mean(x > 2 * np.median(n0)):.2f}; vs N per seed: median diff {np.median(x - n0):6.1f}, "
              f"mean diff {np.mean(x - n0):6.1f}, share better than N {np.mean(x < n0):.2f}")
    print("  incident means: IP slow/block %.1f/%.1f, ID %.1f/%.1f; N clean mean %.1f" %
          (ip["slow"].mean(), ip["block"].mean(), idd["slow"].mean(), idd["block"].mean(), n0.mean()))
    for pi in (0.05, 0.1, 0.25, 0.5, 1.0):
        T = {"IP": mix(ip["slow"], ip["block"], n0, pi), "ID": mix(idd["slow"], idd["block"], n0, pi)}
        refs = {x: a[x] for x in L0}
        if str(pi) in a["prev"]:
            refs.update({f"{x}_pi{pi}": g for x, g in a["prev"][str(pi)].items()})
        rows = {}
        for r, g in refs.items():
            rows[r] = mix(E(g, "slow", q), E(g, "block", q), E(g, "none", q), pi)
        allm = {**{k: v.mean() for k, v in rows.items()}, **{k: v.mean() for k, v in T.items()}}
        rk = sorted(allm, key=allm.get)
        print(f"  pi {pi}: MEAN ranking: " + ", ".join(f"{k} {allm[k]:.1f}" for k in rk[:6]))
        tgt = [r for r in rows if r.startswith("PI")] + ([r for r in rows if r.startswith("FB")])
        for t in ("IP", "ID"):
            for r in tgt:
                md, mci, rel, rci = mean_ci(rows[r], T[t])
                win = np.mean(T[t] < rows[r])
                print(f"     {t} vs {r:9s}: mean diff {md:6.1f} s [{mci[0]:6.1f}, {mci[1]:6.1f}], rel_mean {100*rel:6.1f} % "
                      f"[{100*rci[0]:6.1f}, {100*rci[1]:6.1f}], median diff {np.median(rows[r]-T[t]):6.1f}, "
                      f"{t} lower on {100*win:.0f} % of seeds")
