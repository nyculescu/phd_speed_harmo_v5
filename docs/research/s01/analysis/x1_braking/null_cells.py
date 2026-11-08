"""(e) A no-effect reference for the cascade share: if a follower's event start were independent of its leader's, the chance that the
leader started an event in the 3 s before is about 1 - exp(-3 s x lambda), lambda = event starts per vehicle-second (all classes,
ev_all / vehicle-seconds; a lower bound, because braking clusters in congestion). Also the cross-cell check: the same seeds run X1 and
X2, so X1 - X2 per arm and seed is paired (median and 95 % bootstrap CI, same resampling)."""
import numpy as np

from common_x import arm, diff_ci, load_T, med

T = load_T()
for cell in ("X1", "X2"):
    for g in ("nc", "v3w", "3e", "p333"):
        A = arm(T, cell, g)
        lam = [A[s]["ev_all"] / (A[s]["vs_car"] + A[s]["vs_alks"] + A[s]["vs_truck"]) for s in A]
        lam_c = [A[s]["ev_car"] / A[s]["vs_car"] for s in A]
        lam_a = [A[s]["ev_alks"] / A[s]["vs_alks"] for s in A]
        null = [1 - np.exp(-3.0 * x) for x in lam]
        print(f"{cell} {g:5s} events per veh-s {np.median(lam):.4f} (car {np.median(lam_c):.4f}, alks {np.median(lam_a):.4f}); uniform null cascade share {np.median(null):.3f}; "
              f"observed car {med(A, 'cshare_car'):.3f}, alks {med(A, 'cshare_alks'):.3f}, all {med(A, 'cshare_all'):.3f}")
print()
n = 0
for g in ("nc", "v3w", "tail", "sw", "bv3", "3e", "p333", "os1_15_10"):
    A1, A2 = arm(T, "X1", g), arm(T, "X2", g)
    for k in ("ev45_all", "ev45_car", "ev45_alks", "ev4_all", "ev5_alks", "all_delay", "passed"):
        d = diff_ci(A1, A2, k)
        n += 1
        print(f"X1 - X2 {g:9s} {k:10s} medX1 {med(A1, k):10.4g} medX2 {med(A2, k):10.4g} diff {d[0]:10.4g} [{d[1]:10.4g}, {d[2]:10.4g}]")
print("cross-cell comparisons:", n)
