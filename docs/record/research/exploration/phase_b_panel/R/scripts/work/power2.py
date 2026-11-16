# EXPLORATORY: X1 pass chance at n = 160 and 240, interval half-widths, and no control read-outs on the pooled stored rows.
from power import *
L, O = arrays("X1", list(DS), RULES)
arm = L.mean(axis=1); d = O - arm[:, None]
pt = 100 * np.median(d, axis=0) / np.median(O, axis=0)
j0 = int(np.argmin(pt)); med = np.median(O[:, j0])
print("closest", RULES[j0], round(float(pt[j0]), 2))
for e in (0, 1, 2, 2.5, 3, 3.5, 4, 5):
    new = (O[:, j0] - (pt[j0] - e) / 100 * med)[:, None]
    print(f"true edge {e}: " + " | ".join(f"n={n}: PASS {sim(L, O, n, add=new)[0][3]:.3f}" for n in (120, 160, 240)))
print("as stored: " + " | ".join(f"n={n}: PASS {sim(L, O, n)[0][3]:.3f}" for n in (120, 160, 240)))
# half-width of the 97.5 % interval against p333 at n = 120, 160, 240 (direct bootstrap, 400 outer resamples)
rng = np.random.default_rng(5)
for n in (120, 160, 240):
    lo, hi = [], []
    for _ in range(400):
        ii = rng.integers(0, 120, n); dd = d[ii, j0]
        b = np.median(dd[rng.integers(0, n, (2000, n))], axis=1)
        p = np.median(dd); q = np.percentile(b, [1.25, 98.75])
        lo.append(100 * (p - q[0]) / med); hi.append(100 * (q[1] - p) / med)
    print(f"n={n}: mean half-widths of the 97.5 % interval against p333: -{np.mean(lo):.2f} / +{np.mean(hi):.2f} points")
# no control: close-following and delay, pooled 120 seeds, 95 %
for c in ("X1", "X2"):
    for key in ("ttc_net", "all_delay"):
        Lk, Ok = arrays(c, list(DS), ["nc", "p333"], key)
        a = Lk.mean(axis=1)
        for j, r in enumerate(["nc", "p333"]):
            dd = Ok[:, j] - a; m = np.median(Ok[:, j])
            rng = np.random.default_rng(20261110)
            b = 100 * np.median(dd[rng.integers(0, 120, (20000, 120))], axis=1) / m
            print(f"{c} {key} v3w against {r}: {100*np.median(dd)/m:+.1f} [{np.percentile(b, 2.5):+.1f}, {np.percentile(b, 97.5):+.1f}] (95 %, 120 seeds)")
        # p333 against no control (T0/T1 read)
        dd = Ok[:, 0] - Ok[:, 1]; m = np.median(Ok[:, 0])
        rng = np.random.default_rng(20261110)
        b = 100 * np.median(dd[rng.integers(0, 120, (20000, 120))], axis=1) / m
        print(f"{c} {key} p333 against nc: {100*np.median(dd)/m:+.1f} [{np.percentile(b, 2.5):+.1f}, {np.percentile(b, 97.5):+.1f}] (95 %, 120 seeds)")
