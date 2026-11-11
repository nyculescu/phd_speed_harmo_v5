"""EXPLORATORY: paired delay effects against p333 in stored rows, and their spread. Positive = arm has less delay."""
import pickle, sys
import numpy as np
D = pickle.load(open(sys.argv[1], "rb"))
K = list(D["keys"]); iD = K.index("all_delay"); iP = K.index("passed"); iF = K.index("finished_pct")
rng = np.random.default_rng(20261110)
seeds = list(range(7480400, 7480640))

def col(name, i=iD, src="s6", sd=seeds):
    return np.array([D[src][name][s][i] for s in sd], float)

def boot(d, den, n=None, B=10000, lo=1.25, hi=98.75):
    n = n or len(d)
    idx = rng.integers(0, len(d), (B, n))
    m = np.median(d[idx], axis=1) / den * 100
    return m.std(), np.percentile(m, lo), np.percentile(m, hi), np.percentile(m, 2.5), np.percentile(m, 97.5)

P = col("S|p333"); den = np.median(P)
print("S p333 median all_delay", round(den), "sd %", round(P.std() / den * 100, 1), "finished_pct median", np.median(col("S|p333", iF)))
print("os0_10_10 == p333 on all 240 seeds:", bool(np.all(col("S|os0_10_10") == P)))
print("\nS, 5,300, 240 seeds: effect %, 95 % CI, 97.5 % CI, paired SD %, robust SD % (1.4826 MAD), SE of median at n=240/120/80/60/40")
rows = []
for name in sorted(D["s6"]):
    if not name.startswith("S|") or name == "S|p333":
        continue
    A = col(name); d = P - A
    e = np.median(d) / den * 100
    se240, l975, h975, l95, h95 = boot(d, den)
    ses = [boot(d, den, n, B=4000)[0] for n in (120, 80, 60, 40)]
    mad = 1.4826 * np.median(np.abs(d - np.median(d))) / den * 100
    rows.append((e, name, l95, h95, l975, h975, d.std() / den * 100, mad, se240, *ses))
for r in sorted(rows, reverse=True):
    print("%+6.2f %-22s [%+6.2f,%+6.2f] [%+6.2f,%+6.2f] sd %5.1f rsd %5.1f se %4.2f %4.2f %4.2f %4.2f %4.2f" % r)

# flow effect spread for the same proxies
print("\nserved flow (passed) effect % against p333, paired, S:")
Pp = col("S|p333", iP)
for name in ("S|r4a1", "S|grid_r4a2", "S|z33133", "S|grid_z31333", "S|nc", "S|os0_10_10"):
    d = col(name, iP) - Pp
    m = np.median(d) / np.median(Pp) * 100
    idx = rng.integers(0, 240, (10000, 240))
    bm = np.median(d[idx], axis=1) / np.median(Pp) * 100
    print("  %-16s %+5.2f [%+5.2f, %+5.2f]  mean %+5.2f" % (name, m, np.percentile(bm, 2.5), np.percentile(bm, 97.5), d.mean() / Pp.mean() * 100))

# band rows, condition T (random training slowdown), 20 seeds per level
print("\nband rows (condition T, 20 seeds): paired delay effect against p333 and paired SD %, by level")
for q in (5000.0, 5250.0, 5500.0, 6000.0):
    b = D["band"]
    sd = sorted(b[("B|p333", q)])
    Pb = np.array([b[("B|p333", q)][s][iD] for s in sd], float)
    fin = np.median([b[("B|p333", q)][s][iF] for s in sd])
    out = []
    for name in ("B|os1_15_10", "B|3e", "B|nc"):
        A = np.array([b[(name, q)][s][iD] for s in sd], float)
        d = Pb - A
        out.append("%s %+6.2f sd %5.1f rsd %5.1f" % (name[2:], np.median(d) / np.median(Pb) * 100, d.std() / np.median(Pb) * 100, 1.4826 * np.median(np.abs(d - np.median(d))) / np.median(Pb) * 100))
    print("  q %.0f p333 median %7.0f finished %5.1f | " % (q, np.median(Pb), fin) + " | ".join(out))
