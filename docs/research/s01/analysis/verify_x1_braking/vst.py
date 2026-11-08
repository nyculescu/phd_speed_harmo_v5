"""Own space-time localisation: vehicle crossings of 50-m speed steps needing a given deceleration, by road and period."""
import pickle
import numpy as np
from vlib import T, SEEDS, ARMS
ST = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/'
r0 = T[('X1|nc', SEEDS[0])]
off = r0['m_offsets']
edges = [('up', 0, off['3a']), ('3a', off['3a'], off['3']), ('3', off['3'], off['4a']), ('4a', off['4a'], off['4']), ('4', off['4'], off['5']), ('5', off['5'], off['_end'])]
xc = (np.arange(136) + 1) * 50.0     # boundary between cell j and j+1
reg = np.array([next((nm for nm, a, b in edges if a <= x < b), '5') for x in xc])


def periods(cell):
    if cell == 'X1':
        P = [('pre', 300, 600), ('w1', 600, 720), ('a1', 720, 840), ('mid', 840, 1200), ('w2', 1200, 1320), ('a2', 1320, 1440), ('late', 1440, 1800)]
    else:
        P = [('pre', 300, 700), ('w', 700, 880), ('a', 880, 1000), ('late', 1000, 1800)]
    t = 300 + 10 * np.arange(150)
    return P, np.array([next(nm for nm, a, b in P if a <= tt < b) for tt in t])


out = {}
for cell in ('X1', 'X2'):
    P, per = periods(cell)
    for a in ('nc', '3e', 'v3w', 'p333'):
        for n in ARMS[a]:
            for s in SEEDS:
                r = T[(f'{cell}|{n}', s)]
                z = np.load(ST + r['m_st_file'])
                V, N = z['v'].astype(float), z['n'].astype(float)
                v = np.where(N > 0, V / np.maximum(N, 1), np.nan)     # m/s
                v1, v2 = v[:, :-1], v[:, 1:]
                areq = np.where(np.isfinite(v1) & np.isfinite(v2) & (v1 > v2), (v1 ** 2 - v2 ** 2) / 100.0, 0.0)
                cross = np.where(np.isfinite(v1), N[:, :-1] * np.nan_to_num(v1) / 50.0, 0.0)     # vehicles crossing the boundary per bin
                res = {}
                for thr in (1.5, 2.5):
                    m = cross * (areq >= thr)
                    res[f'f{thr}'] = m.sum()
                    for rn in ('up', '3a', '3', '4a', '4', '5'):
                        cols = reg[:-1] == rn
                        for pn, _, _ in P:
                            res[f'f{thr}_{rn}_{pn}'] = m[per == pn][:, cols].sum()
                # jam vehicle-seconds by road
                jam = np.where(np.isfinite(v) & (v * 3.6 < 30), N, 0.0)
                for rn, xa, xb in edges:
                    cols = (np.arange(136) * 50 >= xa) & (np.arange(136) * 50 < xb)
                    res[f'jam_{rn}'] = jam[:, cols].sum()
                out[(cell, n, s)] = res
pickle.dump(out, open('st_metrics.pkl', 'wb'))
print(len(out))
