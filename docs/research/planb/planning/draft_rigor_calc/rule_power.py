"""Planning-only power and null of the draft_rigor reading rule (m = 2), resampling the stored S0/S1 X1/X2 rows at 5,300.

Rule per cell, against every stored rule: delay and close-following lower bounds > 0 at 1 - 0.05/m; close-following median
paired count reduction >= 20 per run; flow lower bound > -1 %; robust braking (ev4_ca, raw counts) lower bound > -15 %;
at least 4 of 5 learners with point estimates > 0 on delay and close-following against every rule."""
import json
import sys
import zlib
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/planb/read_power")
from load_arms import METRICS, V3W, load  # noqa: E402

M = 2
LO_P = 2.5 / M
MET = ("all_delay", "ttc_net", "passed", "ev4_ca")
CELLS = load()


def task(args):
    cell, sc, n, reps, b_in = args
    C = CELLS[cell]
    A, rules = C["arms"], C["rules"]
    N = len(C["seeds"])
    who = ["v3w"] + list(V3W)
    # shifted policy values per (who, opponent, metric)
    P = {}
    for w in who:
        for o in rules:
            for k in MET:
                p = A[w][k].copy()
                if sc.startswith("f") and k in ("all_delay", "ttc_net"):
                    f = float(sc[1:])
                    s = METRICS[k]
                    ref = max(float(np.median(A[o][k])), 1e-9)
                    d = s * (A["v3w"][k] - A[o][k]) / ref * 100
                    p = p - s * (1 - f) * float(np.median(d)) * ref / 100
                P[(w, o, k)] = p
    swap = set()
    if sc == "null":
        swap = {(o, k) for o in rules for k in MET}
    elif sc == "lfc_d":
        s = METRICS["all_delay"]

        def eff(o):
            ref = float(np.median(A[o]["all_delay"]))
            return float(np.median(s * (A["v3w"]["all_delay"] - A[o]["all_delay"]) / ref * 100))
        swap = {(min(rules, key=eff), "all_delay")}
    cols = [(o, k) for o in rules for k in MET]
    J = np.random.default_rng(20261104).integers(0, n, (b_in, n))
    rng = np.random.default_rng(zlib.crc32(f"{cell}|{sc}|{n}".encode()))
    acc = {r: 0 for r in ("W3", "W3_floor", "W3_flow", "W3_brake", "W3_learn", "FULL")}
    for _ in range(reps):
        idx = rng.integers(0, N, n)
        masks = {o: rng.random(n) < 0.5 for o in rules}
        D = np.empty((n, len(cols)))
        floor_ok, learn_ok = True, True
        lcount = np.zeros(len(V3W), bool) | True
        for j, (o, k) in enumerate(cols):
            q = A[o][k][idx]
            p = P[("v3w", o, k)][idx]
            if (o, k) in swap:
                p, q = np.where(masks[o], q, p), np.where(masks[o], p, q)
            ref = max(float(np.median(q)), 1e-9)
            D[:, j] = METRICS[k] * (p - q) / ref * 100
            if k == "ttc_net" and np.median(q - p) < 20:
                floor_ok = False
            if k in ("all_delay", "ttc_net"):
                for li, l in enumerate(V3W):
                    pl = P[(l, o, k)][idx]
                    ql = A[o][k][idx]
                    if (o, k) in swap:
                        pl, ql = np.where(masks[o], ql, pl), np.where(masks[o], pl, ql)
                    if not np.median(METRICS[k] * (pl - ql)) > 0:
                        lcount[li] = False
        learn_ok = lcount.sum() >= 4
        Mb = np.median(D.T[:, J], axis=2).T
        LO = np.percentile(Mb, LO_P, axis=0)
        lo = {c: LO[j] for j, c in enumerate(cols)}
        w3 = all(lo[(o, "all_delay")] > 0 and lo[(o, "ttc_net")] > 0 for o in rules)
        flow = all(lo[(o, "passed")] > -1 for o in rules)
        brake = all(lo[(o, "ev4_ca")] > -15 for o in rules)
        acc["W3"] += w3
        acc["W3_floor"] += w3 and floor_ok
        acc["W3_flow"] += w3 and flow
        acc["W3_brake"] += w3 and brake
        acc["W3_learn"] += w3 and learn_ok
        acc["FULL"] += w3 and floor_ok and flow and brake and learn_ok
    return {"cell": cell, "scenario": sc, "n": n, "reps": reps, **{k: v / reps for k, v in acc.items()}}


if __name__ == "__main__":
    jobs = []
    for cell in ("X1@5300", "X2@5300"):
        for n in (80, 120):
            for sc, reps in (("obs", 400), ("f0.75", 400), ("lfc_d", 400), ("null", 200)):
                jobs.append((cell, sc, n, reps, 4000))
    with Pool(4) as pool:
        out = pool.map(task, jobs, chunksize=1)
    json.dump(out, open("rule_power.json", "w"), indent=1)
    for r in out:
        print(json.dumps(r))
