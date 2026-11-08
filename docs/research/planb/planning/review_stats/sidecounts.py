"""Zero-inflation of the collision and moving full-emergency gates (plan_b_v0 §8.3), stored X1/X2 rows at 5,300."""
import numpy as np
from load import load, V3W

C = load()
for cell in ("X1@5300", "X2@5300"):
    A, rules = C[cell]["arms"], C[cell]["rules"]
    print("==", cell)
    for k in ("collisions", "fm"):
        lv = np.stack([A[l][k] for l in V3W])
        print(f" {k}: v3w learners: mean/run {lv.mean():.3f}, share of runs >= 1: {(lv >= 1).mean():.3f}, per-seed learner-mean median {np.median(A['v3w'][k]):.2f}, max {A['v3w'][k].max():.2f}")
        for o in rules + ["nc"]:
            x = A[o][k]
            print(f"   {o:12s} mean {x.mean():.3f} share>=1 {(x >= 1).mean():.3f} median {np.median(x):.1f}")
