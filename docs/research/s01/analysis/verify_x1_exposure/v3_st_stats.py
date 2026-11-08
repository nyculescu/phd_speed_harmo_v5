"""Statistics on the space-time summaries: edge jam, 4a and edge-3 speed mix and density, approach exposure and TTC per approach exposure."""
import json
import sys

import numpy as np

sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure")
from vlib import arms_for, effect, fmt, g, load, mean_ci  # noqa: E402

OUT = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure"
ST = json.load(open(f"{OUT}/v2_st.json"))["store"]
T = load()
seeds = list(range(7440840, 7440880))
ncmp = 0


def arm_vals(cell, arm, fn):
    names = arms_for(cell)[arm]
    return np.array([np.mean([fn(ST[f"{cell}|{n}|{s}"], T[f"{cell}|{n}"][s]) for n in names]) for s in seeds])


for cell in ("X1", "X2"):
    print(f"\n===== {cell}")
    # edge jam medians
    for arm in ("nc", "v3w"):
        med = {e: np.median(arm_vals(cell, arm, lambda st, r, e=e: sum(st[f"vs_{e}_{lo}"] for lo in (0, 18)))) for e in ("3a", "3", "4a", "4")}
        print(f"  {arm} median jam (<30 km/h) veh-s: " + ", ".join(f"{e} {v:,.0f}" for e, v in med.items()))
    nc_rest3 = arm_vals(cell, "nc", lambda st, r: st["jam_3_rest"])
    d_rest3 = arm_vals(cell, "v3w", lambda st, r: st["jam_3_rest"]) - nc_rest3
    print(f"  edge-3 jam in rest: nc median {np.median(nc_rest3):,.0f}; v3w-nc mean {fmt(mean_ci(d_rest3), 0)}")
    for arm in ("v3w", "tail", "sw", "inc", "3e", "3ex", "p333", "os1_15_10"):
        lines = []
        for e in ("3", "4a"):
            # speed mix on the edge, % change of each class's vehicle-seconds vs nc (median-based effect, positive = more)
            mix = []
            for lo in (0, 18, 30, 60, 80):
                p = arm_vals(cell, arm, lambda st, r, e=e, lo=lo: st[f"vs_{e}_{lo}"])
                o = arm_vals(cell, "nc", lambda st, r, e=e, lo=lo: st[f"vs_{e}_{lo}"])
                mix.append(f"{lo}+ {fmt(mean_ci(p - o), 0)}")
                ncmp += 1
            dp = arm_vals(cell, arm, lambda st, r, e=e: st[f"dens_mov_{e}"])
            do = arm_vals(cell, "nc", lambda st, r, e=e: st[f"dens_mov_{e}"])
            ncmp += 1
            dens = effect(dp, do, 1)
            # TTC on the edge per vehicle-second in cells 18-60 km/h (dense moving)
            rp = arm_vals(cell, arm, lambda st, r, e=e: g(r, f"ttc3_r_{e}") / max(st[f"vs_{e}_18"] + st[f"vs_{e}_30"], 1))
            ro = arm_vals(cell, "nc", lambda st, r, e=e: g(r, f"ttc3_r_{e}") / max(st[f"vs_{e}_18"] + st[f"vs_{e}_30"], 1))
            ncmp += 1
            lines.append(f"    edge {e}: d veh-s by cell speed (mean v-nc) " + "; ".join(mix) + f"\n      moving-cell density % {fmt(dens)}; TTC per veh-s in 18-60 km/h cells (neg = more) {fmt(effect(rp, ro, -1))}")
        # approach exposure
        app = []
        for k in (10, 20, 30):
            p = arm_vals(cell, arm, lambda st, r, k=k: st[f"app{k}"])
            o = arm_vals(cell, "nc", lambda st, r, k=k: st[f"app{k}"])
            ncmp += 2
            mainline_ttc = lambda st, r, k=k: (g(r, "ttc3") - g(r, "ttc3_r_ramp2")) / max(st[f"app{k}"], 1)
            app.append(f"app{k} % {fmt(effect(p, o, 1))} | TTC(no ramp2)/app{k} (neg = more) {fmt(effect(arm_vals(cell, arm, mainline_ttc), arm_vals(cell, 'nc', mainline_ttc), -1))}")
        e4 = []
        for e in ("3", "4a"):
            p = arm_vals(cell, arm, lambda st, r, e=e: st[f"app20_{e}"])
            o = arm_vals(cell, "nc", lambda st, r, e=e: st[f"app20_{e}"])
            fn = lambda st, r, e=e: g(r, f"ttc3_r_{e}") / max(st[f"app20_{e}"], 1)
            ncmp += 2
            e4.append(f"app20 on {e}: d {fmt(mean_ci(p - o), 0)} (nc med {np.median(o):,.0f}); TTC_r_{e}/app20 (neg = more) {fmt(effect(arm_vals(cell, arm, fn), arm_vals(cell, 'nc', fn), -1))}")
        tp = arm_vals(cell, arm, lambda st, r: st["tdrop20"])
        to = arm_vals(cell, "nc", lambda st, r: st["tdrop20"])
        ncmp += 1
        print(f"  --- {arm}\n" + "\n".join(lines) + "\n    " + "\n    ".join(app) + "\n    " + "\n    ".join(e4) + f"\n    temporal drop >=20 km/h exposure % {fmt(effect(tp, to, 1))}")
print("comparisons", ncmp)
