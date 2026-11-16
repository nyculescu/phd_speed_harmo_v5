"""V299 win rule. usage: b_night_c7_map.py rows.jsonl (F rows plus b_night_p303_robust_rows.jsonl, concatenated): F0-F2 against p303 per condition and level (higher is better everywhere)."""
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r


def diff(a, b, q, m, s):
    A, B = T[(a, q)], T[(b, q)]
    ds = sorted(set(A) & set(B))
    base = np.median([B[k][m] for k in ds])
    d = np.array([s * (A[k][m] - B[k][m]) / base * 100 for k in ds])
    rng = np.random.default_rng(20261102)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return float(np.median(d)), float(lo), float(hi)


def f(x):
    return f"{x[0]:+.1f}[{x[1]:+.1f},{x[2]:+.1f}]"


wins = ties = 0
for c in ("asl03", "asl08", "s25", "s80", "d"):
    for q in sorted({k[1] for k in T if k[0] == f"p303_{c}"}):
        w = t = 0
        for L in range(3):
            p, o = f"F{L}_{c}", f"p303_{c}"
            fl, tt, br = diff(p, o, q, "passed", 1), diff(p, o, q, "E30", -1), diff(p, o, q, "brake3", -1)
            coll = sum(r["collisions"] for r in T[(p, q)].values())
            win = fl[1] > 0 and tt[1] > 0 and not coll
            tie = abs(fl[0]) <= 0.5 and tt[1] > 0 and br[1] > 0
            w += win
            t += tie
            print(f"{p} {q:g}: flow {f(fl)} TTC {f(tt)} brake {f(br)} coll {coll} v_delay {f(diff(p, f'a000_{c}', q, 'passed', 1))}", "WIN" if win else "", "SAFER_AT_TIE" if tie else "")
        print(f"cell {c} {q:g}: win {w}/3 safer-at-tie {t}/3 | p303 v delay {f(diff(f'p303_{c}', f'a000_{c}', q, 'passed', 1))} | a333 v p303 flow {f(diff(f'a333_{c}', f'p303_{c}', q, 'passed', 1))} TTC {f(diff(f'a333_{c}', f'p303_{c}', q, 'E30', -1))}")
        wins += w >= 2
        ties += t >= 2
print(f"cells won {wins} of 10; cells safer at tied flow {ties} of 10")
