"""Per-comparison false 'better' rate of the W delay reading at the least favourable configuration (label swap, per seed
p <-> q with probability 1/2, as read_power and synth/rule_v0), m = 3 (lower percentile 0.833), for the three closest delay
rules per cell, at n = 40 and 120. More studies than synth/rule_v0.py's 200 so that a ~1 % rate is resolved."""
import json
import sys
import zlib
from multiprocessing import Pool

import numpy as np

from load import load

C = load()


def task(a):
    cell, o, n, reps, B = a
    A = C[cell]["arms"]
    P, Q = A["v3w"]["all_delay"], A[o]["all_delay"]
    N = len(P)
    rng = np.random.default_rng(zlib.crc32(f"lfc|{cell}|{o}|{n}|{B}".encode()))
    hit = 0
    for _ in range(reps):
        idx = rng.integers(0, N, n) if n != N else rng.permutation(N)
        p, q = P[idx], Q[idx]
        s = rng.random(n) < 0.5
        p, q = np.where(s, q, p), np.where(s, p, q)
        d = -(p - q) / np.median(q) * 100
        J = rng.integers(0, n, (B, n))
        if np.percentile(np.median(d[J], axis=1), 2.5 / 3) > 0:
            hit += 1
    k = hit
    # Clopper-Pearson 95 % via beta quantiles
    from scipy.stats import beta
    lo = beta.ppf(0.025, k, reps - k + 1) if k > 0 else 0.0
    hi = beta.ppf(0.975, k + 1, reps - k)
    return {"cell": cell, "o": o, "n": n, "reps": reps, "B": B, "rate": k / reps, "cp95": [round(float(lo), 4), round(float(hi), 4)]}


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    jobs = []
    for cell, rules in (("X1@5300", ("lr1000_10_1", "os0_10_10", "p333")), ("X2@5300", ("os0_10_10", "3ex2", "lr1000_10_1"))):
        for o in rules:
            for n in (40, 120):
                jobs.append((cell, o, n, reps, 4000))
        jobs.append((cell, rules[0], 120, reps // 2, 20000))
    with Pool(4) as pool:
        out = pool.map(task, jobs, chunksize=1)
    json.dump(out, open("lfc.json", "w"), indent=1)
    for r in out:
        print(json.dumps(r))
