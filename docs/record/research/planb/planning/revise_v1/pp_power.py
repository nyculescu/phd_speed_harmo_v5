"""Planning proxy for plan_b_v1: per-policy W (T2 unit) against the arm-level W, and mean-based side-constraint pass rates.
Stored X1/X2 rows at 5,300 (40 seeds, 14 rules), resampled to n; stored effects (f1) and f0.75. Not evidence."""
import json, sys, zlib, pickle
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/planb/review_stats")
from load import V3W, load
C = load()
M = 3
LO, HI = 2.5 / M, 100 - 2.5 / M
B, REPS = 1000, 200


def eff(p, o, J):
    # positive = v3w better (lower); returns point and bootstrap array
    d = o - p
    den = np.median(o)
    pt = np.median(d) / den * 100
    bs = np.median(d[J], axis=1) / den * 100
    return pt, bs


def task(args):
    cell, f, n = args
    A, rules = C[cell]["arms"], C[cell]["rules"]
    N = len(C[cell]["seeds"])
    rng = np.random.default_rng(zlib.crc32(f"pp|{cell}|{f}|{n}".encode()))
    who = ("v3w",) + V3W
    # scale effects towards 0 by (1-f) of the stored median paired difference, per opponent and measure (as review power.py)
    P = {}
    for w in who:
        for o in rules:
            for k in ("all_delay", "ttc_net"):
                d = A["v3w"][k] - A[o][k]
                P[(w, o, k)] = A[w][k] - (1 - f) * float(np.median(d))
    acc = {"arm": 0, "pp4": 0, "pp_k": [0] * 6, "fm05": 0, "fm10": 0, "col02": 0, "col05": 0}
    for _ in range(REPS):
        idx = rng.integers(0, N, n)
        J = rng.integers(0, n, (B, n))
        arm_ok = True
        pol_ok = {w: True for w in V3W}
        for o in rules:
            O = {k: A[o][k][idx] for k in ("all_delay", "ttc_net")}
            for w in who:
                if w != "v3w" and not pol_ok[w] and not arm_ok:
                    continue
                pd, bd = eff(P[(w, o, "all_delay")][idx], O["all_delay"], J)
                pc, bc = eff(P[(w, o, "ttc_net")][idx], O["ttc_net"], J)
                red = np.median(O["ttc_net"] - P[(w, o, "ttc_net")][idx])
                lod, loc = np.percentile(bd, LO), np.percentile(bc, LO)
                if w == "v3w":
                    if not (lod > 0 and loc > 0 and red >= 20):
                        arm_ok = False
                else:
                    if not (lod > 0 and loc > 0 and pc >= 10 and red >= 20):
                        pol_ok[w] = False
                    if not (pd > 0 and pc > 0):
                        arm_ok = arm_ok and sum(pol_ok.values()) >= 0  # learner point check below
            # learner point signs for the arm rule
        npt = sum(all(np.median(A[o]["all_delay"][idx] - P[(w, o, "all_delay")][idx]) > 0 and
                      np.median(A[o]["ttc_net"][idx] - P[(w, o, "ttc_net")][idx]) > 0 for o in rules) for w in V3W)
        k = sum(pol_ok.values())
        acc["arm"] += arm_ok and npt >= 4
        acc["pp4"] += k >= 4
        acc["pp_k"][k] += 1
        # side constraints, stored values (not scaled): one-sided 95 % upper bound of mean(P - O) <= tol against every o
        ok = {"fm05": True, "fm10": True, "col02": True, "col05": True}
        for o in rules:
            for key, tols in (("fm", (("fm05", .05), ("fm10", .10))), ("collisions", (("col02", .02), ("col05", .05)))):
                d = A["v3w"][key][idx] - A[o][key][idx]
                ub = np.percentile(d[J].mean(axis=1), 95)
                for name, t in tols:
                    ok[name] = ok[name] and ub <= t
        for name in ok:
            acc[name] += ok[name]
    out = {"cell": cell, "f": f, "n": n, "reps": REPS, "B": B, "W_arm": acc["arm"] / REPS, "W_pp4": acc["pp4"] / REPS,
           "pp_k_dist": [x / REPS for x in acc["pp_k"]], "fm_tol0.05": acc["fm05"] / REPS, "fm_tol0.10": acc["fm10"] / REPS,
           "col_tol0.02": acc["col02"] / REPS, "col_tol0.05": acc["col05"] / REPS}
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    jobs = [(c, f, n) for c in ("X1@5300", "X2@5300") for f in (1.0, 0.75) for n in (120, 240)]
    with Pool(4) as p:
        res = p.map(task, jobs)
    json.dump(res, open(__file__.replace(".py", ".json"), "w"), indent=1)
