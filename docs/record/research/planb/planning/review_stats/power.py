"""Independent re-check of plan_b_v0 §8.8-8.9 (planning proxy, stored X1/X2 rows at 5,300, 14 rules).
Scenarios:
  f1, f0.75, f0.5  per-opponent scaling of v3w's delay and close-following effects (as synth/rule_v0.py);
  tieb             ONE shift of v3w's delay so that it exactly ties the closest rule on delay (the realistic least
                   favourable case: v3w no better than the best rule, still better than the others); close-following as stored;
  tieb_s           tieb plus a 0.5 % delay penalty (v3w slightly worse than the best rule);
  f1_sm, f0.75_sm  smoothed bootstrap of the paired differences (bandwidth 0.5 SD, variance-preserving), a check on lumpiness.
Outputs per (cell, scenario, n): W core rate, L rate, pilot GO rate at n = 30 (F0: every point >= 0)."""
import json
import sys
import zlib
from multiprocessing import Pool

import numpy as np

from load import V3W, load

C = load()
SIGN = {"all_delay": -1, "ttc_net": -1}
M = 3
LO, UP95 = 2.5 / M, 97.5
KS = ("all_delay", "ttc_net")


def build(cell, sc):
    A, rules = C[cell]["arms"], C[cell]["rules"]
    who = ("v3w",) + V3W
    P = {}
    # single shift for tieb: in vehicle-seconds, from the closest rule's stored median paired difference
    ref_d = {o: float(np.median(A[o]["all_delay"])) for o in rules}
    e_d = {o: -np.median(A["v3w"]["all_delay"] - A[o]["all_delay"]) / ref_d[o] * 100 for o in rules}
    closest = min(rules, key=lambda o: e_d[o])
    shift_vs = e_d[closest] / 100 * ref_d[closest]
    if sc == "tieb_s":
        shift_vs += 0.005 * ref_d[closest]
    for w in who:
        for o in rules:
            for k in KS:
                p = A[w][k].copy()
                base = sc.split("_")[0]
                if base.startswith("f"):
                    f = float(base[1:])
                    ref = float(np.median(A[o][k]))
                    d = SIGN[k] * (A["v3w"][k] - A[o][k]) / ref * 100
                    p = p - SIGN[k] * (1 - f) * float(np.median(d)) * ref / 100
                elif base == "tieb" and k == "all_delay":
                    p = p + shift_vs
                P[(w, o, k)] = p
    return A, rules, P, closest


def task(args):
    cell, sc, n, reps, b_in = args
    A, rules, P, closest = build(cell, sc)
    N = len(C[cell]["seeds"])
    cols = [(o, k) for o in rules for k in KS]
    J = np.random.default_rng(20261108).integers(0, n, (b_in, n))
    rng = np.random.default_rng(zlib.crc32(f"rev|{cell}|{sc}|{n}".encode()))
    smooth = sc.endswith("_sm")
    acc = {"W": 0, "core": 0, "L": 0, "Lclose": 0, "learnfail": 0, "GO30": 0}
    # full-data per-seed differences (for the smoothed version)
    Dfull = {}
    for (o, k) in cols:
        q = A[o][k]
        Dfull[(o, k)] = SIGN[k] * (P[("v3w", o, k)] - q) / float(np.median(q)) * 100
    for _ in range(reps):
        idx = rng.integers(0, N, n)
        D = np.empty((n, len(cols)))
        floor_ok = True
        lc = np.ones(len(V3W), bool)
        for j, (o, k) in enumerate(cols):
            if smooth:
                d0 = Dfull[(o, k)]
                mu, sd = d0.mean(), d0.std(ddof=1)
                h = 0.5
                D[:, j] = mu + (d0[idx] - mu + h * sd * rng.standard_normal(n)) / np.sqrt(1 + h * h)
            else:
                q, p = A[o][k][idx], P[("v3w", o, k)][idx]
                D[:, j] = SIGN[k] * (p - q) / float(np.median(q)) * 100
                if k == "ttc_net" and np.median(q - p) < 20:
                    floor_ok = False
            for li, l in enumerate(V3W):
                if not np.median(SIGN[k] * (P[(l, o, k)][idx] - A[o][k][idx])) > 0:
                    lc[li] = False
        Mb = np.median(D[J], axis=1)
        lo, up = np.percentile(Mb, LO, axis=0), np.percentile(Mb, UP95, axis=0)
        pt = np.median(D, axis=0)
        core = floor_ok and bool((lo > 0).all())
        harmv = [(k == "all_delay" and pt[j] < -2 and up[j] < 0) or (k == "ttc_net" and pt[j] < -10 and up[j] < 0) for j, (o, k) in enumerate(cols)]
        acc["core"] += core
        acc["W"] += core and lc.sum() >= 4
        acc["learnfail"] += core and lc.sum() < 4
        acc["L"] += any(harmv)
        acc["Lclose"] += any(h for h, (o, k) in zip(harmv, cols) if o == closest)
        # pilot F0 at n = 30 on an independent draw
        ip = rng.integers(0, N, 30)
        go = True
        for (o, k) in cols:
            q, p = A[o][k][ip], P[("v3w", o, k)][ip]
            if SIGN[k] * np.median(p - q) / float(np.median(q)) * 100 < 0:
                go = False
                break
        acc["GO30"] += go
    return {"cell": cell, "sc": sc, "n": n, "reps": reps, "closest": closest, **{k: round(v / reps, 4) for k, v in acc.items()}}


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    jobs = []
    for cell in ("X1@5300", "X2@5300"):
        for sc in ("f1", "f0.75", "f0.5", "tieb", "tieb_s", "f1_sm", "f0.75_sm"):
            jobs.append((cell, sc, 120, reps, 4000))
        for sc in ("f1", "tieb"):
            jobs.append((cell, sc, 80, reps, 4000))
    with Pool(4) as pool:
        out = pool.map(task, jobs, chunksize=1)
    json.dump(out, open("power.json", "w"), indent=1)
    for r in out:
        print(json.dumps(r))
