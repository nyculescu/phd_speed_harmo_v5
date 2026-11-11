import json
import numpy as np
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
Z = np.load("s6_scalars.npz"); KEYS = list(Z["keys"])
c = lambda cell, arm, k: Z[f"{cell}|{arm}"][:, KEYS.index(k)]
for cell in ("TRUCK", "S"):
    x = c(cell, "nc", "ttc_net"); print(cell, "nc ttc_net median %.1f mean %.1f min %.0f max %.0f" % (np.median(x), x.mean(), x.min(), x.max()))
def f(d):
    s = "%+.2f" % d["effect"]
    for k in ("ci95", "ci_m"):
        if d.get(k): s += " %s[%+.2f, %+.2f]" % (k, *d[k])
    return s
R = J["S"]["map_report_only"]
for opp in ("nc", "3E-C_TRUCK", "p333", "os0_10_10", "os1_15_10"):
    e = R.get(opp) or {}
    print("S", opp, {k: f(v) for k, v in e.items() if k in ("delay", "cf", "events_ge45", "b45_step", "b3_step", "ttc15", "sev3", "robust_braking") and isinstance(v, dict) and v.get("effect") is not None})
# how many of the 23 opponents show v3w worse on events_ge45 / b45_step in TRUCK at ci_m
T = J["cells"]["TRUCK"]["map_report_only"]
for k in ("events_ge45", "b45_step", "b3_step", "robust_braking", "ttc15", "sev3", "ttc3_lc_share"):
    worse = [o for o, e in T.items() if o != "nc" and isinstance(e.get(k), dict) and e[k].get("ci_m") and e[k]["ci_m"][1] < 0]
    better = [o for o, e in T.items() if o != "nc" and isinstance(e.get(k), dict) and e[k].get("ci_m") and e[k]["ci_m"][0] > 0]
    print("TRUCK %-14s v3w shown worse than %d opponents %s; shown better than %d" % (k, len(worse), worse, len(better)))
print("location keys:", list(J["cells"]["TRUCK"]["location"])[:12])
print("must_carry:", json.dumps(J["must_carry"])[:700])
