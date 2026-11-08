"""Planning-only operating characteristic of the Plan B v0 reading rule, resampling the stored S0 X1/X2 rows at 5,300 (14 rules).
Per cell, against every rule: W = delay and close-following 98.33 % lower bounds > 0 (m = 3), close-following median paired
reduction >= 20 per run, flow point >= -0.5 %, collisions median(P) <= median(O) + 1, moving full-emergency median(P - O) <=
max(5 % of median(O), 5), at least 4 of 5 learners with point estimates > 0 on delay and close-following. W-b = W with robust
braking per vehicle-km more than 10 % worse (point) than some rule. L = delay point < -2 with the 95 % upper bound < 0, or
close-following point < -10 with the 95 % upper bound < 0, against any rule. Scenarios: v3w's delay and close-following effects
scaled by f (f = 0: a tie with each rule); lfc_d: label swap on the closest rule's delay; null: label swap on every rule's
delay and close-following."""
import json
import sys
import time
import zlib
from multiprocessing import Pool

import numpy as np

from load2 import V3W, load

M = 3
LO98, UP95 = 2.5 / M, 97.5
SIGN = {"all_delay": -1, "ttc_net": -1, "passed": 1, "ev4_vkm": -1}
CELLS = load()


def eff(p, q, k):
    return SIGN[k] * np.median(p - q) / max(float(np.median(q)), 1e-9) * 100


def task(args):
    cell, sc, n, reps, b_in = args
    C = CELLS[cell]
    A, rules = C["arms"], C["rules"]
    N = len(C["seeds"])
    who = ("v3w",) + V3W
    P = {}
    for w in who:
        for o in rules:
            for k in ("all_delay", "ttc_net"):
                p = A[w][k].copy()
                if sc.startswith("f"):
                    f = float(sc[1:])
                    ref = max(float(np.median(A[o][k])), 1e-9)
                    d = SIGN[k] * (A["v3w"][k] - A[o][k]) / ref * 100
                    p = p - SIGN[k] * (1 - f) * float(np.median(d)) * ref / 100
                P[(w, o, k)] = p
    swap = set()
    if sc == "null":
        swap = {(o, k) for o in rules for k in ("all_delay", "ttc_net")}
    elif sc == "lfc_d":
        swap = {(min(rules, key=lambda o: eff(A["v3w"]["all_delay"], A[o]["all_delay"], "all_delay")), "all_delay")}
    cols = [(o, k) for o in rules for k in ("all_delay", "ttc_net")]
    J = np.random.default_rng(20261108).integers(0, n, (b_in, n))
    rng = np.random.default_rng(zlib.crc32(f"v0|{cell}|{sc}|{n}".encode()))
    acc = dict.fromkeys(("core", "W_all", "Wb", "L", "core_gatefail", "core_learnfail"), 0)
    for _ in range(reps):
        idx = rng.integers(0, N, n)
        masks = {o: rng.random(n) < 0.5 for o in rules}
        D = np.empty((n, len(cols)))
        floor_ok = True
        lc = np.ones(len(V3W), bool)
        for j, (o, k) in enumerate(cols):
            q, p = A[o][k][idx], P[("v3w", o, k)][idx]
            if (o, k) in swap:
                p, q = np.where(masks[o], q, p), np.where(masks[o], p, q)
            D[:, j] = SIGN[k] * (p - q) / max(float(np.median(q)), 1e-9) * 100
            if k == "ttc_net" and np.median(q - p) < 20:
                floor_ok = False
            for li, l in enumerate(V3W):
                pl, ql = P[(l, o, k)][idx], A[o][k][idx]
                if (o, k) in swap:
                    pl, ql = np.where(masks[o], ql, pl), np.where(masks[o], pl, ql)
                if not np.median(SIGN[k] * (pl - ql)) > 0:
                    lc[li] = False
        Mb = np.median(D[J], axis=1)
        lo, up = np.percentile(Mb, LO98, axis=0), np.percentile(Mb, UP95, axis=0)
        pt = np.median(D, axis=0)
        core = floor_ok and all(lo[j] > 0 for j in range(len(cols)))
        harm = any((k == "all_delay" and pt[j] < -2 and up[j] < 0) or (k == "ttc_net" and pt[j] < -10 and up[j] < 0) for j, (o, k) in enumerate(cols))
        gates = True
        brake_bad = False
        for o in rules:
            pv, ov = A["v3w"], A[o]
            if eff(pv["passed"][idx], ov["passed"][idx], "passed") < -0.5:
                gates = False
            if np.median(pv["collisions"][idx]) > np.median(ov["collisions"][idx]) + 1:
                gates = False
            if np.median(pv["fm"][idx] - ov["fm"][idx]) > max(0.05 * np.median(ov["fm"][idx]), 5):
                gates = False
            if eff(pv["ev4_vkm"][idx], ov["ev4_vkm"][idx], "ev4_vkm") < -10:
                brake_bad = True
        learn = lc.sum() >= 4
        w = core and gates and learn
        acc["core"] += core
        acc["W_all"] += w
        acc["Wb"] += w and brake_bad
        acc["L"] += harm
        acc["core_gatefail"] += core and not gates
        acc["core_learnfail"] += core and gates and not learn
    return {"cell": cell, "scenario": sc, "n": n, "reps": reps, **{k: v / reps for k, v in acc.items()}}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "time":
        t = time.time()
        print(task(("X1", "obs", 120, 5, 4000)), time.time() - t)
        sys.exit()
    jobs = []
    for cell in ("X1", "X2"):
        for n in (80, 120):
            for sc, reps in (("f1", 300), ("f0.75", 300), ("f0.5", 300), ("f0", 300), ("lfc_d", 200), ("null", 200)):
                jobs.append((cell, sc, n, reps, 4000))
    with Pool(4) as pool:
        out = pool.map(task, jobs, chunksize=1)
    json.dump(out, open("rule_v0.json", "w"), indent=1)
    for r in out:
        print(json.dumps(r))
