"""Across controlled arms (each learner and rule separately): what goes with ev45 - held level or traffic state?"""
from vlib import *
import numpy as np
from scipy.stats import spearmanr, rankdata
def lvm(road):
    return lambda r: r.get(f'lv_sum_{road}', 0) / r[f'lv_n_{road}'] if r.get(f'lv_n_{road}') else np.nan
def up_speed(r, t0=720):
    mm = r['m_minute']; i0 = (t0 - 300) // 60
    return 3.6 * sum(mm['m2_up_vs'][i0:]) / max(sum(mm['m2_up_n'][i0:]), 1)
def on08(r):
    on = sum(r['m_dec_level_s']); return r['m_dec_level_s'][3] / (on + r['m_dec_off_s'])
F = {'ev45': M['ev45_all'], 'ev4': M['ev4_all'], 'ev5a': M['ev5_alks'], 'ev45car': M['ev45_car'], 'lv4a': lvm('4a'), 'lv3': lvm('3'), 'on08': on08,
     'delay': M['all_delay'], 'passed': M['passed'], 'v3up': up_speed}
def partial(x, y, z):
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    ex = rx - np.polyval(np.polyfit(rz, rx, 1), rz); ey = ry - np.polyval(np.polyfit(rz, ry, 1), rz)
    return np.corrcoef(ex, ey)[0, 1]
for cell in ('X1', 'X2'):
    names = sorted({k[0].split('|')[1] for k in T if k[0].startswith(cell + '|')} - {'nc'})
    D = {k: np.array([np.nanmedian([f(T[(f'{cell}|{n}', s)]) for s in SEEDS]) for n in names]) for k, f in F.items()}
    print(cell, 'arms', len(names))
    for y in ('ev45', 'ev4', 'ev5a', 'ev45car'):
        print('  ', y, ' '.join(f'{x}:{spearmanr(D[x], D[y])[0]:+.2f}' for x in ('lv4a', 'lv3', 'on08', 'delay', 'passed', 'v3up')))
    print('   partial rho(ev45, lv4a | v3up) %+.2f ; rho(ev45, v3up | lv4a) %+.2f ; rho(ev45, lv4a | delay) %+.2f ; rho(ev45, delay | lv4a) %+.2f' % (
        partial(D['lv4a'], D['ev45'], D['v3up']), partial(D['v3up'], D['ev45'], D['lv4a']), partial(D['lv4a'], D['ev45'], D['delay']), partial(D['delay'], D['ev45'], D['lv4a'])))
    print('   rho(lv4a, v3up) %+.2f rho(lv4a, delay) %+.2f' % (spearmanr(D['lv4a'], D['v3up'])[0], spearmanr(D['lv4a'], D['delay'])[0]))
