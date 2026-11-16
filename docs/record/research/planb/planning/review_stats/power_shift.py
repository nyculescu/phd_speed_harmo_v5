"""W power at n = 120 when a new opponent (e.g. a converged delay-tuned 3E-D) is k points better on delay than the stored
closest rule: one shift of v3w's delay by k % of that rule's median, everything else as stored (planning proxy)."""
import json
from multiprocessing import Pool
import numpy as np
import power

orig_build = power.build


def build(cell, sc):
    if not sc.startswith("sh"):
        return orig_build(cell, sc)
    A, rules, P, closest = orig_build(cell, "f1")
    k = float(sc[2:])
    ref = float(np.median(A[closest]["all_delay"]))
    for key in list(P):
        if key[2] == "all_delay":
            P[key] = P[key] + k / 100 * ref
    return A, rules, P, closest


power.build = build
if __name__ == "__main__":
    jobs = [(c, f"sh{k}", 120, 600, 4000) for c, ks in (("X1@5300", (1, 2, 3, 4)), ("X2@5300", (0.5, 1, 1.5))) for k in ks]
    with Pool(4) as pool:
        out = pool.map(power.task, jobs, chunksize=1)
    json.dump(out, open("power_shift.json", "w"), indent=1)
    for r in out:
        print(json.dumps({k: r[k] for k in ("cell", "sc", "n", "reps", "closest", "W", "L", "GO30")}))
