"""EXPLORATORY planning: rates of PASS / KILL / UNDECIDED for the screen-M check rule, from stored S6 paired differences
(merge-zone rules against p333), shifted to a stated true median effect. PASS: point >= 3 and lower bound > 0. KILL: upper bound < 3."""
import pickle, sys
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
rng = np.random.default_rng(20261110)
seeds = sorted(T["S|p333"])
LEV = 97.5; A = (100 - LEV) / 2
STUD, B = 500, 600
def rates(d, e, n):
    d = d - np.median(d) + e
    out = np.zeros(3)
    for _ in range(STUD):
        x = d[rng.integers(0, len(d), n)]
        m = np.median(x[rng.integers(0, n, (B, n))], axis=1)
        lo, hi, pt = np.percentile(m, A), np.percentile(m, 100 - A), np.median(x)
        out[0 if (pt >= 3 and lo > 0) else 1 if hi < 3 else 2] += 1
    return 100 * out / STUD
for cond, proxies in (("S", ("r4a1", "z33133", "os1_10_0")), ("TRUCK", ("z33133",))):
    base = np.array([T[f"{cond}|p333"][s]["d"] for s in seeds]); med = np.median(base)
    for a in proxies:
        d = 100 * (base - np.array([T[f"{cond}|{a}"][s]["d"] for s in seeds])) / med
        print(f"\n{cond} proxy {a}: paired sd {d.std(ddof=1):.1f} %, robust {(np.percentile(d,75)-np.percentile(d,25))/1.349:.1f} %")
        for n in (80, 120, 240):
            hw = []
            for _ in range(200):
                x = d[rng.integers(0, len(d), n)]
                m = np.median(x[rng.integers(0, n, (B, n))], axis=1)
                hw.append((np.percentile(m, 100 - A) - np.percentile(m, A)) / 2)
            line = f"  n {n}: median half-width {np.median(hw):.2f} |"
            for e in (-4, 0, 1.5, 3, 5, 7):
                p, k, u = rates(d, e, n)
                line += f" e={e:+}: P {p:.0f} K {k:.0f} U {u:.0f};"
            print(line, flush=True)
