"""Part 1 and 3: stored per-rule effects (n = 40) and side-measure distributions, X1/X2 at 5,300. Planning proxy only."""
import json
import numpy as np
from load import load, V3W

C = load()
SIGN = {"all_delay": -1, "ttc_net": -1, "passed": 1, "ev4_vkm": -1, "N": -1}
rng = np.random.default_rng(20261108)


def eff(p, q, k):
    return SIGN[k] * np.median(p - q) / np.median(q) * 100


def ci(p, q, k, B=20000, lv=(2.5 / 3, 100 - 2.5 / 3, 2.5, 97.5, 5.0, 95.0)):
    n = len(p)
    J = rng.integers(0, n, (B, n))
    d = SIGN[k] * (p - q) / np.median(q) * 100
    m = np.median(d[J], axis=1)
    return [round(float(x), 2) for x in np.percentile(m, lv)]


out = {}
for cell in ("X1@5300", "X2@5300"):
    A, rules = C[cell]["arms"], C[cell]["rules"]
    P = A["v3w"]
    print(f"== {cell}: v3w med delay {np.median(P['all_delay']):.0f}, ttc {np.median(P['ttc_net']):.0f}, passed {np.median(P['passed']):.0f}, "
          f"coll {np.median(P['collisions'])}, fm {np.median(P['fm'])}, ev4_vkm {np.median(P['ev4_vkm']):.2f}")
    rows = []
    for o in rules + ["nc"]:
        Q = A[o]
        r = {"o": o}
        for k in ("all_delay", "ttc_net", "passed", "ev4_vkm"):
            r[k] = (round(float(eff(P[k], Q[k], k)), 2), ci(P[k], Q[k], k))
            r[k + "_sd"] = round(float(np.std(SIGN[k] * (P[k] - Q[k]) / np.median(Q[k]) * 100, ddof=1)), 2)
        r["coll"] = (float(np.median(P["collisions"])), float(np.median(Q["collisions"])))
        r["fm"] = (float(np.median(P["fm"] - Q["fm"])), float(np.median(Q["fm"])))
        r["ttc_red"] = float(np.median(Q["ttc_net"] - P["ttc_net"]))
        rows.append(r)
        print(f"{o:12s} delay {r['all_delay'][0]:+6.2f} lo98 {r['all_delay'][1][0]:+6.2f} sd {r['all_delay_sd']:5.2f} | ttc {r['ttc_net'][0]:+6.1f} lo98 {r['ttc_net'][1][0]:+6.1f} red {r['ttc_red']:6.0f}"
              f" | flow {r['passed'][0]:+5.2f} [{r['passed'][1][2]:+5.2f},{r['passed'][1][3]:+5.2f}] sd {r['passed_sd']:4.2f} | brk {r['ev4_vkm'][0]:+6.1f} [{r['ev4_vkm'][1][2]:+6.1f},{r['ev4_vkm'][1][3]:+6.1f}] sd {r['ev4_vkm_sd']:5.1f}"
              f" | coll P/O {r['coll']} fm d/O {r['fm']}")
    out[cell] = rows
    # learner-level distributions of collisions and fm
    print(" collisions per run (v3w learners pooled): ", np.percentile(np.concatenate([A[l]["collisions"] for l in V3W]), [10, 50, 90]),
          " p333:", np.percentile(A["p333"]["collisions"], [10, 50, 90]))
    print(" fm per run p333:", np.percentile(A["p333"]["fm"], [10, 50, 90]), " v3w mean:", np.percentile(P["fm"], [10, 50, 90]))
json.dump(out, open("observed.json", "w"), indent=1)
