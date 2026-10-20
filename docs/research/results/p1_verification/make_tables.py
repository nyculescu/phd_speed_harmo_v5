"""Build Tables 1 and 2 of docs/research/results/p1_result.md from result.json and the stored run files.
Pre-registered numbers are copied from result.json; descriptive ones are recomputed with the frozen project statistics
(v5b.p1.stats.paired: bootstrap seed 20261019, B = 20,000). Reads stored runs only; runs nothing.
Run with: python -I -B make_tables.py  (no bytecode is written into the frozen tree)."""
import json, statistics as stt, sys
import numpy as np
sys.path.insert(0, '/home/catalin/work/phd/p1_frozen_85f7d34')
from v5b.p1 import analysis as an, family as fam
from v5b.p1.stats import paired, prevalence_mix, LEVEL_95
RUN = '/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
R = json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
E, ARMS = R['eval'], R['tune']['arms']
S = list(range(7400500, 7400600))
_c = {}
def run(k):
    if k not in _c:
        _c[k] = json.load(open(RUN + k + '.json'))
    return _c[k]
def arr(keys, f='delay_s'): return np.array([run(k)[f] for k in keys], float)
def g(x): return f'{x:g}'
def keys_for(arm, inc, q):
    a = ARMS[an.qk(q)]; N = a['N']
    if arm == 'NC': return [an.fixed(fam.NC, inc, q, s)['key'] for s in S]
    if arm in ('N', 'FX', 'FB', 'PI', 'AD'): return [an.fixed(a[arm], inc, q, s)['key'] for s in S]
    if arm == 'ID': return [an.sw(N, a['ID'], inc, q, s)['key'] for s in S]
    if arm == 'IP': return [an.sw(N, a['IP'][inc], inc, q, s)['key'] for s in S]
    if arm == 'OR_in':
        out = []
        for s in S:
            ks = [an.sw(N, x, inc, q, s)['key'] for x in fam.A]
            out.append(fam.argmin_tie({k: run(k)['delay_s'] for k in ks}, ks))
        return out
# ---------------------------------------------------------------- Table 1
COLS = [('slow', 1600.0), ('block', 1600.0), ('none', 1600.0), ('slow', 2000.0), ('block', 2000.0), ('none', 2000.0)]
print('| Arm | ' + ' | '.join(('clean' if i == 'none' else i) + f'_q{int(q)}' for i, q in COLS) + ' |')
print('|---' * (len(COLS) + 1) + '|')
for arm in ('NC', 'N', 'FX', 'FB', 'PI', 'AD', 'ID', 'IP', 'OR_in'):
    cells = []
    for inc, q in COLS:
        if inc == 'none' and arm in ('ID', 'IP'):
            cells.append('= N'); continue
        if inc == 'none' and arm == 'OR_in':
            cells.append('–'); continue
        row = (E['per_q'][an.qk(q)]['clean_day'][arm] if inc == 'none'
               else E['table1_operating_map'][an.cell_name(inc, q)]['arms'][arm])
        es = stt.median(arr(keys_for(arm, inc, q), 'emergency_stops'))
        cells.append(f"{row['median_delay_s']:.1f} / {row['median_served_vph']:.0f} / {row['median_ttt_ctrl_vehh']:.1f}"
                     f" / {g(row['median_max_queue'])} / {g(es)}")
    print(f'| {arm} | ' + ' | '.join(cells) + ' |')
# ---------------------------------------------------------------- Table 2
def rc(s, b=False):
    t = f"{100*s['rel']:+.1f} [{100*s['rel_ci'][0]:.1f}, {100*s['rel_ci'][1]:.1f}]"
    return f'**{t}**' if b else t
def dc(s, sign=1):
    lo, hi = sorted((sign * s['diff_ci'][0], sign * s['diff_ci'][1]))
    return f"{sign*s['diff']:+.1f} [{lo:.1f}, {hi:.1f}]"
def pair(fn):  # one cell entry per q: slow / block
    return {q: ' / '.join(fn(an.cell_name(i, q), i, q) for i in ('slow', 'block')) for q in (1600.0, 2000.0)}
rows = []
s1 = E['S1']['per_cell_stats']
for r in ('FB', 'PI'):
    rows.append((f'S1a: ID vs {r}, rel % [S1 CI] (P)', pair(lambda c, i, q, r=r: rc(s1[c]['ID_vs'][r]['all_seeds']))))
pass_b = set(E['S1']['S1b_cells_both_views'])
rows.append(('S1b: IP vs ID, rel % [S1 CI] (P)', pair(lambda c, i, q: rc(s1[c]['IP_vs_ID']['all_seeds'], c in pass_b))))
for r in ('FB', 'PI'):
    rows.append((f'IP vs {r} at d = 0, s/veh [95 %] (D)', pair(lambda c, i, q, r=r: dc(paired(arr(keys_for(r, i, q)), arr(keys_for('IP', i, q)), LEVEL_95)))))
def s2(c, i, q):
    x = E['S2'][c]['all_seeds']; t = f"[{100*x['y']:.1f}, {100*x['x']:.1f}]"
    return f'**{t}**' if x['y'] > 0 else t
rows.append(('S2 bracket [y, x], % (P)', pair(s2)))
rows.append(('TP placebo, % (P, report only)', pair(lambda c, i, q: f"{100*E['TP'][c]['rel']:.1f}")))
def star(lab, unit_fmt):
    def f(c, i, q):
        a = E['S3'][c][lab]['all_seeds']
        if lab == 'c_star' and not E['S3'][c]['clearance_delay_applies']:
            return 'n/a (stay plan)'
        v = 'never ahead' if a['flag'] == 'IP never ahead' else unit_fmt(a['value'])
        return f"{v} [{unit_fmt(a['ci'][0])}, {unit_fmt(a['ci'][1])}] {a['binding_arm']}"
    return f
rows.append(('S3 d*, s [95 %], binding arm (P, no test)', pair(star('d_star', lambda v: f'{v:.1f}'.rstrip('0').rstrip('.')))))
rows.append(('S3 p* [95 %], binding arm (P, no test)', pair(star('p_star', lambda v: f'{v:.2f}'))))
rows.append(('S3 c*, s [95 %] (P, no test)', pair(star('c_star', lambda v: f'{v:.1f}'))))
rows.append(('Combined row vs IP, rel % (P, no test)', pair(lambda c, i, q: f"{100*E['S3'][c]['combined_row']['vs_IP']['all_seeds']['rel']:.1f}")))
print()
print('| Statistic | q1600: slow / block | q2000: slow / block |')
print('|---|---|---|')
for lab, v in rows:
    print(f'| {lab} | {v[1600.0]} | {v[2000.0]} |')
# clean day and prevalence (one entry per q)
def perq(fn): return {q: fn(q) for q in (1600.0, 2000.0)}
def clean_pi(q):
    n = arr(keys_for('N', 'none', q)); p = arr(keys_for('PI', 'none', q))
    return f"{dc(paired(n, p, LEVEL_95), -1)} / {dc(paired(n, p, LEVEL_95, mean=True), -1)}"
crow = [('Clean day: PI − N, paired median / mean, s/veh (D)', perq(clean_pi)),
        ('One false alarm: FA − N, paired median, s/veh (P, report only)',
         perq(lambda q: dc(E['per_q'][an.qk(q)]['false_alarm_cost']['all_seeds'])))]  # stored as paired(FA, N): diff = median(FA - N)
PIS = ('0.1', '0.25', '0.5')
prev = lambda q: E['per_q'][an.qk(q)]['prevalence']
crow.append(('PI_π at π = 0.1 / 0.25 / 0.5', perq(lambda q: ' / '.join(prev(q)[p]['controllers']['PI'] for p in PIS))))
for t in ('ID', 'IP'):
    crow.append((f'{t} vs PI_π, rel % [95 %] (P, report only)', perq(lambda q, t=t: ' / '.join(
        rc(prev(q)[p][f'{t}_vs']['PI']['all_seeds'], prev(q)[p][f'{t}_vs']['PI']['all_seeds']['diff_ci'][0] > 0) for p in PIS))))
def mean_gain(q):
    a = ARMS[an.qk(q)]; out = []
    ipS, ipB, nC = arr(keys_for('IP', 'slow', q)), arr(keys_for('IP', 'block', q)), arr(keys_for('N', 'none', q))
    for p in PIS:
        gpi = prev(q)[p]['controllers']['PI']
        L = prevalence_mix(*(arr([an.fixed(gpi, i, q, s)['key'] for s in S]) for i in ('slow', 'block', 'none')), float(p))
        out.append(dc(paired(L, prevalence_mix(ipS, ipB, nC, float(p)), LEVEL_95, mean=True)))
    return ' / '.join(out)
crow.append(('IP vs PI_π, mean gain, s/veh [95 %] (D)', perq(mean_gain)))
def fstar(q):
    out = []
    for p in PIS:
        a = prev(q)[p]['f_star']['all_seeds']
        v = 'never ahead' if a['flag'] == 'IP never ahead' else f"{a['value']:.2f}"
        out.append(f"{v} [{a['ci'][0]:.2f}, {a['ci'][1]:.2f}]")
    return ' / '.join(out)
crow.append(('f*(π) [95 %], PI binding (P, no test)', perq(fstar)))
print('| *Clean day and prevalence (per q)* | q1600 | q2000 |')
for lab, v in crow:
    print(f'| {lab} | {v[1600.0]} | {v[2000.0]} |')
