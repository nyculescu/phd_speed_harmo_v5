# Screen R, rigor draft: null and power of the cell rule from stored rows (EXPLORATORY; rows already read for verdicts).
import sys
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/exploration/phase_b_round1/scripts/x1x2")
from lib import load, val, RUNS
import numpy as np
from scipy.stats import binom
Q = 5300.0
DS = {"r1test": (RUNS + "round1_remote/out/test/test.jsonl", ["w0", "w1", "w2", "w3", "w4"]),
      "r2val": (RUNS + "round2/val/rows_6c49e7e.jsonl", ["w0u250", "w1u250", "w2u500", "w3u500", "w4u500"]),
      "r2test": (RUNS + "round2/test/rows_6c49e7e.jsonl", ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"])}
T = {k: load(f) for k, (f, _) in DS.items()}
RULES = ["p333", "lr1000_10_1", "os0_10_10", "lr1000_16_2", "os1_15_10", "lr400_13_2", "z33133", "os1_10_0", "r4a1", "a4400_10_1", "lr400_16_1", "copy"]
E3 = {"X1": ["3ex1", "3e"], "X2": ["3ex2", "3e"]}
LEVEL_Q = 0.0125     # lower end of a two-sided 97.5 % interval
TAU = 3.0


def arrays(c, sets, rules, key="all_delay"):
    """per-seed arrays over the pooled sets: learners (n, 5), opponents (n, K)"""
    L, O = [], []
    for s in sets:
        names = DS[s][1]
        seeds = sorted(T[s][(f"{c}|p333", Q)])
        L.append(np.array([[val(T[s][(f"{c}|{n}", Q)][k], key) for n in names] for k in seeds]))
        O.append(np.array([[val(T[s][(f"{c}|{r}", Q)][k], key) for r in rules] for k in seeds]))
    return np.vstack(L), np.vstack(O)


def mcrit(n, q=LEVEL_Q):
    """largest count m of non-positive paired differences with bootstrap P(median* <= 0) < q (percentile bootstrap of the median)"""
    best = -1
    for m in range(0, n + 1):
        p = m / n
        if n % 2:
            pr = binom.sf((n - 1) // 2, n, p)     # at least (n+1)/2 draws at or below 0
        else:
            pr = binom.sf(n // 2, n, p) + 0.5 * binom.pmf(n // 2, n, p)
        if pr < q:
            best = m
        else:
            break
    return best


def rule(Lr, Or, mc):
    """Lr (R, n, 5), Or (R, n, K): cell passes if, against every opponent, point >= TAU, lower bound > 0, and >= 4 of 5 learners have a positive point against every opponent"""
    arm = Lr.mean(axis=2)
    d = Or - arm[:, :, None]     # positive = v3w less delay
    pt = 100 * np.median(d, axis=1) / np.median(Or, axis=1)
    lb = (d <= 0).sum(axis=1) <= mc
    dl = Or[:, :, None, :] - Lr[:, :, :, None]     # (R, n, 5, K)
    lp = (np.median(dl, axis=1) > 0).all(axis=2).sum(axis=1) >= 4
    a, b = (pt >= TAU).all(axis=1), lb.all(axis=1)
    return a, b, lp, pt


def sim(L, O, n, R=20000, seed=1, add=None):
    """resample n seeds; add = extra opponent columns"""
    if add is not None:
        O = np.hstack([O, add])
    rng = np.random.default_rng(20261110 + seed)
    out = np.zeros(4)
    mc = mcrit(n)
    pts = []
    for i in range(0, R, 2000):
        idx = rng.integers(0, len(L), (2000, n))
        a, b, lp, pt = rule(L[idx], O[idx], mc)
        out += [a.mean(), b.mean(), lp.mean(), (a & b & lp).mean()]
        pts.append(pt.min(axis=1))
    return out / (R / 2000), np.concatenate(pts)


def direct_lb(d, B=4000, rng=None):
    idx = rng.integers(0, len(d), (B, len(d)))
    return np.percentile(np.median(d[idx], axis=1), 100 * LEVEL_Q)


if __name__ == "__main__":
    print("mcrit:", {n: mcrit(n) for n in (40, 60, 80, 100, 120, 160, 240)})
    for c, sets, rules in (("X1", list(DS), RULES), ("X2", list(DS), RULES), ("X2", ["r2val", "r2test"], RULES + E3["X2"]), ("X1", ["r2val", "r2test"], RULES + E3["X1"])):
        L, O = arrays(c, sets, rules)
        arm = L.mean(axis=1)
        N = len(arm)
        print(f"\n## {c}, {len(sets)} sets, N = {N}, opponents {len(rules)}")
        d = O - arm[:, None]
        pt = 100 * np.median(d, axis=0) / np.median(O, axis=0)
        sd = 100 * d.std(axis=0, ddof=1) / np.median(O, axis=0)
        order = np.argsort(pt)
        rng = np.random.default_rng(20261110)
        idx = rng.integers(0, N, (20000, N))
        for j in order[:5]:
            bs = 100 * np.median(d[idx, j], axis=1) / np.median(O[:, j])
            lo, hi = np.percentile(bs, [1.25, 98.75])
            print(f"  {rules[j]}: point {pt[j]:+.2f}, 97.5 % [{lo:+.2f}, {hi:+.2f}], SD {sd[j]:.1f}, nonpos {int((d[:, j] <= 0).sum())}/{N} (mcrit {mcrit(N)}), half-widths -{pt[j]-lo:.2f} +{hi-pt[j]:.2f}")
        # check of the count form of the lower bound against the direct bootstrap
        rng = np.random.default_rng(7)
        agree = tot = 0
        j0 = order[0]
        for n in (80, 120):
            for _ in range(300):
                ii = rng.integers(0, N, n)
                dd = d[ii, j0] - np.median(d[:, j0]) + rng.choice([0, 0.01, 0.02, 0.03]) * np.median(O[:, j0])
                agree += (direct_lb(dd, rng=rng) > 0) == ((dd <= 0).sum() <= mcrit(n)); tot += 1
        print(f"  count form vs direct bootstrap (B = 4,000), closest rule, shifted to true edges 0-3 %: agree {agree}/{tot}")
        if len(sets) == 2 and c == "X1":
            continue
        # as stored
        for n in (60, 80, 120, 160):
            r, _ = sim(L, O, n)
            print(f"  as stored, n = {n}: point>=3 all {r[0]:.3f}, LB>0 all {r[1]:.3f}, learners 4/5 {r[2]:.3f}, PASS {r[3]:.3f}")
        # a new opponent: the closest stored rule shifted so that the true edge against it is e % (other opponents as stored)
        j0 = order[0]
        med = np.median(O[:, j0])
        for e in (0, 1, 2, 3, 4, 5, 6):
            new = (O[:, j0] - (pt[j0] - e) / 100 * med)[:, None]
            line = []
            for n in (80, 120, 160):
                r, pmin = sim(L, O, n, add=new)
                line.append(f"n={n}: PASS {r[3]:.3f} (pt {r[0]:.3f}, LB {r[1]:.3f}, lrn {r[2]:.3f})")
            print(f"  new opponent = {rules[j0]} shifted, true edge {e} %: " + " | ".join(line))
        # the same with only the arm clauses, one comparison, label-swap null
        rng = np.random.default_rng(99)
        for n in (80, 120, 160):
            mc = mcrit(n); lbp = ps = 0; Rn = 40000
            for i in range(0, Rn, 4000):
                ii = rng.integers(0, N, (4000, n))
                sg = rng.choice([-1.0, 1.0], (4000, n))
                dd = d[ii, j0] * sg
                lb = (dd <= 0).sum(axis=1) <= mc
                p = 100 * np.median(dd, axis=1) / med >= TAU
                lbp += lb.sum(); ps += (lb & p).sum()
            print(f"  label-swap null, one comparison ({rules[j0]}), n = {n}: LB>0 {lbp/Rn:.4f} (nominal 0.0125), LB>0 and point>=3 {ps/Rn:.4f}")
