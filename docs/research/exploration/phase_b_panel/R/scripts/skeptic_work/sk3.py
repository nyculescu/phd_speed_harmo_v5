# EXPLORATORY: noise of the stage-1 selection (20 seeds, median paired delay against p333), from stored X1 rule rows (120 seeds).
import sys
sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/rigor_work")
from power import arrays, DS, RULES
import numpy as np
L, O = arrays("X1", list(DS), RULES)
N = len(O)
p = O[:, 0]
med = np.median(p)
D = 100 * (p[:, None] - O[:, 1:]) / med     # positive = the rule has less delay than p333, % of p333's median
print("rule minus p333, pooled 120 seeds: " + "; ".join(f"{RULES[j+1]} median {np.median(D[:, j]):+.1f}, SD {D[:, j].std(ddof=1):.1f}" for j in range(D.shape[1])))
Dc = D - np.median(D, axis=0)     # centred: every candidate truly equal to p333
rng = np.random.default_rng(20261110)
for n in (20, 40):
    idx = rng.integers(0, N, (20000, n))
    m = np.median(Dc[idx], axis=1)     # (R, 11)
    print(f"n={n}: SD of the selection statistic per candidate {m.std(axis=0).min():.2f}-{m.std(axis=0).max():.2f} points; best-of-11 apparent gain over p333 when none is better: median {np.median(m.max(axis=1)):+.2f}, 95th {np.percentile(m.max(axis=1), 95):+.2f}")
    for x in (1.0, 2.0, 3.0):
        hit = show = 0
        for j in range(Dc.shape[1]):
            mm = m.copy(); mm[:, j] += x
            hit += (mm.argmax(axis=1) == j).mean(); show += (mm[:, j] > 0).mean()
        print(f"   one candidate truly {x:.0f} % below p333's delay: picked as best of 11 in {hit/Dc.shape[1]:.2f}; shows 'less delay than p333' in {show/Dc.shape[1]:.2f}")
