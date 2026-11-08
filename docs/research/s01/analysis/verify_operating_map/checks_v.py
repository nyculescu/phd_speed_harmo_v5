"""Checks for (a) close-following against nc, (b) the 3,500 spread, p333 = os1 identity, per-learner effects against p333."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from lib import ARMS, KEEP, SETTINGS, arm, eff, load, pdiff  # noqa: E402

OUT = Path(__file__).parent
T = {k: load(k) for k in ("s1", "band", "test")}
out = {}
L = []


def f3(t):
    return f"{t[0]:+.4g} [{t[1]:+.4g}, {t[2]:+.4g}]"


# (a) nc level and controller excess, per run, per vehicle-km, share of on-network vehicle-time
per_vkm = lambda x: x["ttc_net"] / max(x["dist_step"] / 1000.0, 1e-9)
share = lambda x: 100.0 * x["ttc_net"] / max(x["vs"], 1e-9)
L.append("== (a) nc level: median ttc_net, per veh-km, % of vehicle-time; dist_step km; vs")
for kind, cell, q, lab in SETTINGS:
    nc = T[kind][(f"{cell}|nc", q)]
    xs = list(nc.values())
    L.append(f"{lab}: ttc_net {np.median([x['ttc_net'] for x in xs]):.1f}; per vkm {np.median([per_vkm(x) for x in xs]):.5f}; "
             f"share {np.median([share(x) for x in xs]):.5f} %; vkm {np.median([x['dist_step'] for x in xs]) / 1000:.0f}; "
             f"ttc2 {np.median([x['ttc2'] for x in xs]):.1f}")
for lab_want in ("3500", "7000"):
    kind, cell, q, lab = [s for s in SETTINGS if s[3] == lab_want][0]
    nc = arm(T[kind], cell, q, ARMS["nc"], "ttc_net")
    ncv = arm(T[kind], cell, q, ARMS["nc"], None, per_vkm)
    ncs = arm(T[kind], cell, q, ARMS["nc"], None, share)
    ncd = arm(T[kind], cell, q, ARMS["nc"], "dist_step")
    for a in ("v3w", "p333", "os1", "3e"):
        A = arm(T[kind], cell, q, ARMS[a], "ttc_net")
        Av = arm(T[kind], cell, q, ARMS[a], None, per_vkm)
        As = arm(T[kind], cell, q, ARMS[a], None, share)
        Ad = arm(T[kind], cell, q, ARMS[a], "dist_step")
        r = {"abs": pdiff(A, nc), "pct": eff(A, nc, -1), "vkm_abs": pdiff(Av, ncv), "vkm_pct": eff(Av, ncv, -1),
             "share_pp": pdiff(As, ncs), "dist_pct": eff(Ad, ncd, 1)}
        out[f"a|{lab}|{a}"] = r
        L.append(f"{lab} {a}-nc: abs {f3(r['abs'])}; pct {f3(r['pct'])}; per-vkm abs {f3(r['vkm_abs'])}; per-vkm pct {f3(r['vkm_pct'])}; "
                 f"share pp {f3(r['share_pp'])}; vkm +{r['dist_pct'][0]:.2f} %")
    # speed bands at 7000
    if lab == "7000":
        for a in ("nc", "v3w", "p333", "3e", "os1"):
            lo = arm(T[kind], cell, q, ARMS[a], "ttc3_s_lo")
            hi = arm(T[kind], cell, q, ARMS[a], "ttc3_s_hi")
            t3 = arm(T[kind], cell, q, ARMS[a], "ttc3")
            L.append(f"7000 {a}: lo share {np.median([lo[s] / max(t3[s], 1) for s in lo]):.3f}; hi median {np.median(list(hi.values())):.1f}")

# (b) 3,500 spread among controllers and slowdown split
kind, cell, q = "s1", "B", 3500.0
L.append("\n== (b) 3500 pairwise among controllers, effect % (positive = first better)")
for key, sg in (("all_delay", -1), ("ttc_net", -1), ("b3_step", -1), ("b45_step", -1), ("passed", 1)):
    A = {a: arm(T[kind], cell, q, ARMS[a], key) for a in ("v3w", "p333", "os1", "3e", "nc")}
    for p, o in (("v3w", "p333"), ("v3w", "3e"), ("p333", "3e"), ("v3w", "nc"), ("p333", "nc"), ("3e", "nc")):
        t = eff(A[p], A[o], sg)
        out[f"b|{key}|{p}|{o}"] = t
        L.append(f"{key} {p}-{o}: {f3(t)}")
    L.append(f"{key} medians: " + ", ".join(f"{a} {np.median(list(v.values())):.1f}" for a, v in A.items()))
pert = {s: x["pert"] for s, x in T[kind][("B|nc", q)].items()}
agree = all(T[kind][(f"B|{m}", q)][s]["pert"] == pert[s] for m in sum(ARMS.values(), []) if (f"B|{m}", q) in T[kind] for s in pert)
L.append(f"slowdown seeds at 3500: {sum(pert.values())} of {len(pert)}; flag agrees across arms: {agree}")
for flag in (True, False):
    ss = [s for s in pert if pert[s] == flag]
    for a in ("v3w", "p333", "3e"):
        A = arm(T[kind], cell, q, ARMS[a], "all_delay")
        N = arm(T[kind], cell, q, ARMS["nc"], "all_delay")
        t = eff({s: A[s] for s in ss}, {s: N[s] for s in ss}, -1)
        L.append(f"  slowdown={flag} {a}-nc delay: {f3(t)} n={t[3]}")

# p333 identical to os1 (kept fields)
L.append("\n== p333 rows identical to os1_15_10 on all kept fields")
for kind, cell, q, lab in SETTINGS:
    P, O = T[kind][(f"{cell}|p333", q)], T[kind][(f"{cell}|os1_15_10", q)]
    same = sum(all(P[s][k] == O[s][k] for k in KEEP) for s in P)
    L.append(f"{lab}: {same}/{len(P)}")

# per-learner v3w against p333 on delay and ttc_net
L.append("\n== per-learner v3w vs p333 (delay, ttc_net); count of learners with CI below 0 (p333 better)")
for kind, cell, q, lab in SETTINGS:
    row = []
    for key in ("all_delay", "ttc_net"):
        O = arm(T[kind], cell, q, ["p333"], key)
        ts = [eff(arm(T[kind], cell, q, [m], key), O, -1) for m in ARMS["v3w"]]
        row.append(f"{key}: " + " ".join(f"{t[0]:+.1f}[{t[1]:+.1f},{t[2]:+.1f}]" for t in ts) + f"  p333-better {sum(t[2] < 0 for t in ts)}, v3w-better {sum(t[1] > 0 for t in ts)}")
    L.append(f"{lab} " + " || ".join(row))

# collisions and teleports
L.append("\n== collisions / teleports totals per arm (summed over seeds, mean over learners)")
for kind, cell, q, lab in SETTINGS:
    s = []
    for a in ("v3w", "p333", "3e", "os1", "nc"):
        c = arm(T[kind], cell, q, ARMS[a], "collisions")
        tp = arm(T[kind], cell, q, ARMS[a], "teleports")
        s.append(f"{a} {sum(c.values()):.1f}/{sum(tp.values()):.0f}")
    L.append(f"{lab}: " + ", ".join(s))
json.dump(out, open(OUT / "checks_v.json", "w"), indent=0)
open(OUT / "checks_v.txt", "w").write("\n".join(L))
print("\n".join(L))
