"""Descriptive checks quoted in p1_result.md, with the frozen project statistics (v5b.p1.stats.paired, bootstrap
seed 20261019, B = 20,000). Reads stored runs only. Run with: python -I -B ip_checks.py
(1) IP vs each L0 arm at 95 % (d = 0); (2) IP with detection delay d = 30 / 60 s vs undelayed ID (S1 level);
(3) block_q1600 S1b with the runner-up ID f40_10 (S1 level); (4) share of OR_in picks with n_crit = 16."""
import json, sys
import numpy as np
sys.path.insert(0, '/home/catalin/work/phd/p1_frozen_85f7d34')
from v5b.p1 import analysis as an, family as fam
from v5b.p1.stats import paired, LEVEL_95, LEVEL_S1
RUN = '/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
res = json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
S = list(range(7400500, 7400600))
_c = {}
def D(k):
    if k not in _c:
        _c[k] = json.load(open(RUN + k + '.json'))['delay_s']
    return _c[k]
def arr(keys): return np.array([D(k) for k in keys])
def fmt(p): return (f"rel {100*p['rel']:+.1f} % [{100*p['rel_ci'][0]:.1f}, {100*p['rel_ci'][1]:.1f}]; "
                    f"diff {p['diff']:+.1f} s/veh [{p['diff_ci'][0]:.1f}, {p['diff_ci'][1]:.1f}] (level {p['level']:.5f})")
for q in (1600.0, 2000.0):
    a = res['tune']['arms'][an.qk(q)]; N = a['N']
    for inc in ('slow', 'block'):
        c = an.cell_name(inc, q)
        ip = arr([an.sw(N, a['IP'][inc], inc, q, s)['key'] for s in S])
        idd = arr([an.sw(N, a['ID'], inc, q, s)['key'] for s in S])
        for r in ('N', 'FX', 'FB', 'PI', 'AD'):
            print(f'{c} IP vs {r} 95 %:', fmt(paired(arr([an.fixed(a[r], inc, q, s)['key'] for s in S]), ip, LEVEL_95)))
        for d in (30.0, 60.0):
            ipd = arr([an.canon_sw(N, a['IP'][inc], inc, q, s, d=d)['key'] for s in S])
            print(f'{c} IP(d={d:g} s) vs ID(d=0) S1 level:', fmt(paired(idd, ipd, LEVEL_S1)))
        if c == 'block_q1600':
            alt = arr([an.sw(N, 'f40_10', inc, q, s)['key'] for s in S])
            print(f'{c} IP vs ID=f40_10 S1 level:', fmt(paired(alt, ip, LEVEL_S1)))
        n16 = 0
        for s in S:
            d = {x: D(an.sw(N, x, inc, q, s)['key']) for x in fam.A}
            g, _back = fam.parse_action(fam.argmin_tie(d, list(fam.A)))
            n16 += g.startswith('f') and g.split('_')[1] == '16'
        print(f'{c} OR_in picks with n_crit = 16: {n16}/100')
