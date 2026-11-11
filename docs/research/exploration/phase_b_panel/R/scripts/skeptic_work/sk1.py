# EXPLORATORY (stored rows already read for verdicts): skeptic's recomputation of screen R's null and power in X1.
import sys
sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/rigor_work")
from power import arrays, mcrit, DS, RULES, T, Q, val
import numpy as np

L, O = arrays("X1", list(DS), RULES)
N = len(L)
arm = L.mean(axis=1)
d = O - arm[:, None]
med = np.median(O, axis=0)
pt = 100 * np.median(d, axis=0) / med
order = np.argsort(pt)
print("stored points:", {RULES[j]: round(float(pt[j]), 2) for j in order})


def study(Lr, Or, mc, tau=3.0):
    a = Lr.mean(axis=2)
    dd = Or - a[:, :, None]
    p = 100 * np.median(dd, axis=1) / np.median(Or, axis=1)
    lb = (dd <= 0).sum(axis=1) <= mc
    dl = Or[:, :, None, :] - Lr[:, :, :, None]
    pos = np.median(dl, axis=1) > 0     # (R, 5, K)
    k2 = pos.all(axis=2).sum(axis=1) >= 4     # the same 4 learners positive against every arm
    k2b = (pos.sum(axis=1) >= 4).all(axis=1)     # per arm, at least 4 of 5
    return p, lb, k2, k2b


def run(Ouse, n, R=10000, seed=3, tau=3.0):
    rng = np.random.default_rng(20261110 + seed)
    mc = mcrit(n)
    acc = np.zeros(6)
    close = np.zeros(Ouse.shape[1])
    for _ in range(R // 1000):
        idx = rng.integers(0, N, (1000, n))
        p, lb, k2, k2b = study(L[idx], Ouse[idx], mc, tau)
        a, b = (p >= tau).all(axis=1), lb.all(axis=1)
        acc += [a.mean(), b.mean(), k2.mean(), (a & b & k2).mean(), (a & b & ~k2).mean(), (a & b & k2b).mean()]
        close += np.bincount(p.argmin(axis=1), minlength=Ouse.shape[1])
    return acc / (R // 1000), close / R


def shifted(js, e):
    Ou = O.copy()
    for j in js:
        Ou[:, j] = O[:, j] - (pt[j] - e) / 100 * med[j]
    return Ou


n = 160
print("\nA. one new arm = p333 shifted (others as stored), n = 160: PASS, K1 point, K1 bound, K2")
j0 = order[0]
for e in (0, 1, 2, 3, 3.5, 4, 5):
    Ou = np.hstack([O, (O[:, j0] - (pt[j0] - e) / 100 * med[j0])[:, None]])
    r, _ = run(Ou, n)
    print(f"  edge {e}: PASS {r[3]:.3f} (point>=3 {r[0]:.3f}, LB>0 {r[1]:.3f}, K2 ok {r[2]:.3f}); arm passes but K2 fires {r[4]:.3f}")

print("\nB. k arms at the same true edge (nearest k stored rules shifted; others as stored), n = 160")
for k in (1, 3, 5, 12):
    js = order[:k]
    line = []
    for e in (3, 3.5, 4, 4.24, 5):
        r, _ = run(shifted(js, e), n)
        line.append(f"e={e}: {r[3]:.3f}")
    print(f"  k={k} ({','.join(RULES[j] for j in js[:5])}{'...' if k > 5 else ''}): " + " | ".join(line))

print("\nC. which stored rule is the closest by point (as stored)")
for n_ in (160,):
    r, cl = run(O, n_)
    print(f"  n={n_}: PASS {r[3]:.3f}; closest: " + ", ".join(f"{RULES[j]} {cl[j]:.2f}" for j in order[:5]))
r, cl = run(shifted(order[:3], 3.5), 160)
print("  three nearest all at edge 3.5: closest " + ", ".join(f"{RULES[j]} {cl[j]:.2f}" for j in order[:3]))

print("\nD. recorded 5 % bar at arm level (confirmatory_3.md:108 is per policy, 4 of 5), as stored, n = 160")
r, _ = run(O, 160, tau=5.0)
print(f"  arm point >= 5 against every stored rule and LB>0 and K2: {r[3]:.3f} (point clause {r[0]:.3f})")

print("\nE. direct percentile bootstrap check of the count-form bound, n = 160, p333 shifted to edge 0 and 2 (400 studies, B = 4,000)")
rng = np.random.default_rng(11)
for e in (0, 2):
    dd0 = d[:, j0] - (pt[j0] - e) / 100 * med[j0]
    hit = hit2 = 0
    for _ in range(400):
        x = dd0[rng.integers(0, N, 160)]
        b = np.median(x[rng.integers(0, 160, (4000, 160))], axis=1)
        hit += np.percentile(b, 1.25) > 0
        hit2 += (x <= 0).sum() <= mcrit(160)
    print(f"  edge {e}: LB>0 direct {hit/400:.3f}, count form {hit2/400:.3f}")
