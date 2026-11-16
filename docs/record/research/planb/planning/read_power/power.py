"""Part 2: bootstrap power and false-positive rate of "v3w better than every rule in a cell" win rules (planning only).

Each simulated study draws n seeds with replacement from the stored seeds of one cell (joint rows: every arm on that seed), then
reads it exactly as round 2 would: d = sign * (P - O) / median(O) * 100, point = median(d), percentile bootstrap with the same
fixed index matrix for every comparison (default_rng(20261104)), Bonferroni level 1 - 0.05/m read at percentiles 2.5/m and
100 - 2.5/m, for m = 1..30. B_IN inner resamples instead of 20,000 for time; check_bin.py compares the two.

Scenarios: obs (stored effects); fX (delay and close-following effects against every opponent scaled by X, by shifting the
v3w values; braking unchanged); null (label-swap null: per seed and opponent the two runs swap with probability 1/2, all metrics
together); lfc_d (only the delay column of the rule with the smallest stored delay effect is label-swapped, all else as stored);
lfc_t (the same for close-following)."""
import json
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_arms import METRICS, load  # noqa: E402

OUT = Path(__file__).resolve().parent
MET = ("all_delay", "ttc_net", "ev4_ca", "ev5_alks")
MS = np.arange(1, 31)
LO_P = 2.5 / MS
HI_P = 100 - 2.5 / MS
RULES_OUT = ("W1", "W2p", "W2ni", "W3", "W4", "W3b", "W3bb", "NC", "W3nc", "W1any")
CELLS = None


def setup(cell, scenario):
    C = CELLS[cell]
    A = C["arms"]
    rules = C["rules"]
    opps = rules + (["nc"] if C["has_nc"] else [])
    cols = [(o, k) for o in opps for k in MET]
    P = {}
    for o, k in cols:
        p = A["v3w"][k].copy()
        if scenario.startswith("f") and k in ("all_delay", "ttc_net"):
            f = float(scenario[1:])
            s = METRICS[k]
            ref = max(float(np.median(A[o][k])), 1e-9)
            d = s * (A["v3w"][k] - A[o][k]) / ref * 100
            p = p - s * (1 - f) * float(np.median(d)) * ref / 100
        P[(o, k)] = p
    swap = {}
    if scenario == "null":
        swap = {c: True for c in cols}
    elif scenario in ("lfc_d", "lfc_t"):
        k = "all_delay" if scenario == "lfc_d" else "ttc_net"
        s = METRICS[k]

        def eff(o):
            ref = max(float(np.median(A[o][k])), 1e-9)
            return float(np.median(s * (A["v3w"][k] - A[o][k]) / ref * 100))
        weakest = min(rules, key=eff)
        swap = {(weakest, k): True}
    return C, A, rules, opps, cols, P, swap


def task(args):
    cell, scenario, n, reps, b_in = args
    C, A, rules, opps, cols, P, swap = setup(cell, scenario)
    N = len(C["seeds"])
    K = len(cols)
    ci = {c: i for i, c in enumerate(cols)}
    J = np.random.default_rng(20261104).integers(0, n, (b_in, n))
    rng = np.random.default_rng(zlib.crc32(f"{cell}|{scenario}|{n}".encode()))
    acc = {r: np.zeros(30) for r in RULES_OUT}
    one = np.zeros((30, K))     # one-sided false "better": lower bound > 0
    two = np.zeros((30, K))     # CI excludes 0
    pts, wid = [], []
    t0 = time.time()
    ir = [ci[(o, "all_delay")] for o in rules]
    it = [ci[(o, "ttc_net")] for o in rules]
    ib = [ci[(o, "ev4_ca")] for o in rules]
    ib5 = [ci[(o, "ev5_alks")] for o in rules]
    for _ in range(reps):
        idx = rng.integers(0, N, n)
        masks = {o: rng.random(n) < 0.5 for o in opps}
        D = np.empty((n, K))
        for (o, k), j in ci.items():
            p, q = P[(o, k)][idx], A[o][k][idx]
            if swap.get((o, k)):
                m = masks[o]
                p, q = np.where(m, q, p), np.where(m, p, q)
            D[:, j] = METRICS[k] * (p - q) / max(float(np.median(q)), 1e-9) * 100
        pt = np.median(D, axis=0)
        DT = D.T
        M = np.concatenate([np.median(DT[:, J[s:s + 2000]], axis=2).T for s in range(0, b_in, 2000)])
        LO = np.percentile(M, LO_P, axis=0)     # (30, K)
        HI = np.percentile(M, HI_P, axis=0)
        one += LO > 0
        two += (LO > 0) | (HI < 0)
        pts.append(pt)
        wid.append(HI[0] - LO[0])
        w1 = (LO[:, ir] > 0).all(axis=1)
        acc["W1"] += w1
        acc["W1any"] += (LO[:, ir] > 0).any(axis=1)
        acc["W2p"] += w1 & (pt[it] >= -10).all()
        acc["W2ni"] += w1 & (LO[:, it] > -10).all(axis=1)
        w3 = w1 & (LO[:, it] > 0).all(axis=1)
        acc["W3"] += w3
        acc["W4"] += w3 & (pt[it] >= 10).all()
        w3b = w3 & (LO[:, ib] > -10).all(axis=1)
        acc["W3b"] += w3b
        acc["W3bb"] += w3b & (LO[:, ib5] > -10).all(axis=1)
        if "nc" in opps:
            dj, tj = ci[("nc", "all_delay")], ci[("nc", "ttc_net")]
            harm = pt[tj] < -10 and HI[0, tj] < 0     # round 2's harm rule, at 95 %
            nc = (pt[dj] >= 10) & (LO[:, dj] > 0) & (not harm)
            acc["NC"] += nc
            acc["W3nc"] += w3 & nc
    return {"cell": cell, "scenario": scenario, "n": n, "reps": reps, "b_in": b_in, "sec": time.time() - t0,
            "power": {r: (v / reps).tolist() for r, v in acc.items()},
            "one": (one / reps).tolist(), "two": (two / reps).tolist(), "cols": [f"{o}|{k}" for o, k in cols],
            "pt_mean": np.mean(pts, axis=0).tolist(), "w95_mean": np.mean(wid, axis=0).tolist()}


def init():
    global CELLS
    CELLS = load()


def main(which):
    init()
    jobs = []
    if which in ("main", "all"):
        for cell in ("X1@5300", "X2@5300"):
            for n in (20, 40, 60, 80):
                for sc, reps in (("obs", 1000), ("null", 1000), ("lfc_d", 1000), ("lfc_t", 500), ("f0.75", 500),
                                 ("f0.5", 500), ("f0.25", 500)):
                    jobs.append((cell, sc, n, reps, 4000))
    if which in ("band", "all"):
        for cell in ("B@3500", "B@4500", "B@5000", "B@5250", "B@5500", "B@6000", "B@7000"):
            for n in (20, 40, 60, 80):
                for sc, reps in (("obs", 500), ("null", 500)):
                    jobs.append((cell, sc, n, reps, 4000))
    jobs.sort(key=lambda j: -j[2] * j[3])
    with Pool(4, initializer=init) as pool:
        res = pool.map(task, jobs, chunksize=1)
    (OUT / f"power_{which}.json").write_text(json.dumps(res))
    print("tasks", len(res), "cpu s", round(sum(r["sec"] for r in res)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
