"""Clean-day paired costs vs N (descriptive) with the frozen project bootstrap (v5b.p1.stats.paired, seed 20261019,
B = 20,000, 95 %). diff = median (or mean) of (arm - N); positive = arm worse than N. Reads stored runs only.
Run with: python -I -B clean_paired.py  (no bytecode is written into the frozen tree)."""
import json, sys
import numpy as np
sys.path.insert(0, '/home/catalin/work/phd/p1_frozen_85f7d34')
from v5b.p1.stats import paired, LEVEL_95
R = '/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
res = json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
S = range(7400500, 7400600)
def arr(g, q): return np.array([json.load(open(f'{R}{g}_none_q{q}_s{s}.json'))['delay_s'] for s in S])
for q in (1600, 2000):
    pc = res['eval']['per_q'][str(q)]['controllers']
    n = arr(pc['N'], q)
    print(f'q{q}: N median {np.median(n):.1f}; seeds with N > 2x median: {int((n > 2 * np.median(n)).sum())}/100')
    for arm in ('FX', 'FB', 'PI', 'AD', 'NC'):
        x = arr(pc[arm], q)
        m, a = paired(n, x, LEVEL_95), paired(n, x, LEVEL_95, mean=True)   # paired(r, t): diff = stat(r - t)
        print(f'  {arm:3s} - N: median {-m["diff"]:+.1f} [{-m["diff_ci"][1]:.1f}, {-m["diff_ci"][0]:.1f}]'
              f' | mean {-a["diff"]:+.1f} [{-a["diff_ci"][1]:.1f}, {-a["diff_ci"][0]:.1f}]'
              f' | arm worse on {int((x > n).sum())}/100; arm > 2x N median on {int((x > 2 * np.median(n)).sum())}'
              f' | arm Q1 {np.percentile(x, 25):.1f} (N Q1 {np.percentile(n, 25):.1f})')
