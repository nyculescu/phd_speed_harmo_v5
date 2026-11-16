import numpy as np
exec(open("s2.py").read().split("K = lambda")[0])
K = lambda k: (lambda a: c(a, k))
opp = "E30|lr400_16_1"
f = lambda a: c(a, "p_after") + c(a, "p_rest")
pt, b = edge(opp, f); print("after+rest edge %+.2f [%+.2f,%+.2f] med opp %.1f v3w mean med %.1f" % (pt, *np.percentile(b, [1.25, 98.75]), np.median(f(opp)), np.mean([np.median(f(w)) for w in V])))
show("before", *edge(opp, K("p_before")))
# D2 null: random halves of one arm, cut in median stops
r = np.random.default_rng(3)
for a in ["E30|nc", "E30|lr400_16_1", "E30|w1u500"]:
    s = c(a, "es") + c(a, "es2"); cuts = []
    for _ in range(2000):
        p = r.permutation(len(s)); h1, h2 = s[p[:240]], s[p[240:]]
        cuts.append(1 - np.median(h2) / np.median(h1))
    print(a, "random-half cut 2.5/97.5 pct %.3f %.3f" % tuple(np.percentile(cuts, [2.5, 97.5])))
# D9 power
from math import erf, sqrt
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
for e in [9.9, 6.2, 5.0]:
    print("power LB>0 n=480 SE 1.92 edge %.1f: z2.24 %.3f z2.50 %.3f" % (e, Phi(e / 1.92 - 2.24), Phi(e / 1.92 - 2.50)))
print("0 of 20 UB95 %.3f, 0 of 40 %.3f" % (1 - 0.05 ** (1 / 20), 1 - 0.05 ** (1 / 40)))
print("n for +5 power .9 z2.24: %.0f ; power .8: %.0f" % (480 * (1.92 / (5 / 3.52)) ** 2, 480 * (1.92 / (5 / (2.24 + 0.84))) ** 2))
