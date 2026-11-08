"""Arithmetic only (no simulation): SUMO stores a = (vNext - v) / TS with TS = 100 / 1000. and, at the normal decel limit,
vNext = v - decel * TS (MSCFModel::minNextSpeed; MSVehicle::updateState, SUMO 1.27.1 source). For IEEE doubles, which side of -4.5 does
a step braking at exactly decel = 4.5 m/s2 land on, as a function of speed? And for a plateau of k consecutive steps from v0, how often
does at least one step read <= -4.5 (the event then counts in events_ge45)?"""
import numpy as np

TS = 100 / 1000.
dec = 4.5
rng = np.random.default_rng(1)
v = rng.uniform(0.5, 40.0, 2_000_000)
a = ((v - dec * TS) - v) / TS
print("single step at the decel limit, IEEE double:")
for lo, hi in ((0.5, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 40)):
    m = (v >= lo) & (v < hi)
    print(f"  v in [{lo:4.1f},{hi:4.1f}) m/s ({lo * 3.6:5.1f}-{hi * 3.6:5.1f} km/h): a < -4.5 {np.mean(a[m] < -4.5):.3f}, a == -4.5 {np.mean(a[m] == -4.5):.3f}, a > -4.5 {np.mean(a[m] > -4.5):.3f}")
print("plateau of k steps from v0 (v_k+1 = v_k - 0.45): share of events whose min a <= -4.5")
for lo, hi in ((4, 8), (8, 16), (16, 32)):
    v0 = rng.uniform(lo, hi, 200_000)
    for k in (1, 2, 5, 10, 20):
        vv, mn = v0.copy(), np.full(v0.shape, 0.0)
        ok = np.ones(v0.shape, bool)
        for _ in range(k):
            vn = vv - dec * TS
            ok &= vn > 0
            mn = np.minimum(mn, (vn - vv) / TS)
            vv = vn
        print(f"  v0 in [{lo},{hi}) m/s, k {k:2d}: share counted >= 4.5 = {np.mean(mn[ok] <= -4.5):.3f} (n {ok.sum()})")

print("with an action step of m sim steps (MSVehicle::planMove: between action steps vNext = v + a_prev * TS):")
for m in (1, 5, 10):
    for lo, hi in ((2, 4), (4, 8), (8, 16), (16, 32)):
        vv = rng.uniform(lo, hi, 200_000)
        below = tot = 0
        a = None
        for step in range(m):
            vn = (vv - dec * TS) if step == 0 else (vv + a * TS)
            a = (vn - vv) / TS
            below += np.sum(a < -4.5)
            tot += a.size
            vv = vn
        print(f"  m {m:2d}, v0 in [{lo},{hi}) m/s: share of plateau steps reading below -4.5 = {below / tot:.3f}")
