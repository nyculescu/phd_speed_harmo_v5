import pickle
import numpy as np
from scipy.stats import spearmanr
from vlib import T, SEEDS, ARMS, comp, arm, M
S = pickle.load(open('st_metrics.pkl', 'rb'))


def sarm(cell, a, k):
    return {s: float(np.mean([S[(cell, n, s)][k] for n in ARMS[a]])) for s in SEEDS}


nc_ = 0
for cell, P in (('X1', ('pre', 'w1', 'a1', 'mid', 'w2', 'a2', 'late')), ('X2', ('pre', 'w', 'a', 'late'))):
    for opp in ('nc', '3e'):
        t = comp(sarm(cell, 'v3w', 'f1.5'), sarm(cell, opp, 'f1.5')); nc_ += 1
        print(cell, f'v3w-{opp} f1.5 total', f'P {t[0]:.0f} O {t[1]:.0f} d {t[2]:+.0f} [{t[3]:+.0f}, {t[4]:+.0f}]  ({-t[5]:+.1f}% [{-t[7]:+.1f}, {-t[6]:+.1f}])')
    # split by road (all periods) and by period (all roads), v3w - nc, pooled sums
    for rn in ('up', '3a', '3', '4a', '4', '5'):
        key = lambda s, a, rn=rn: sum(np.mean([S[(cell, n, s)][f'f1.5_{rn}_{p}'] for n in ARMS[a]]) for p in P)
        A = {s: key(s, 'v3w') for s in SEEDS}; B = {s: key(s, 'nc') for s in SEEDS}
        t = comp(A, B); nc_ += 1
        print(f'  road {rn:3s} v3w {t[0]:7.0f} nc {t[1]:7.0f} d {t[2]:+6.0f} [{t[3]:+6.0f}, {t[4]:+6.0f}]')
    for p in P:
        key = lambda s, a, p=p: sum(np.mean([S[(cell, n, s)][f'f1.5_{rn}_{p}'] for n in ARMS[a]]) for rn in ('up', '3a', '3', '4a', '4', '5'))
        A = {s: key(s, 'v3w') for s in SEEDS}; B = {s: key(s, 'nc') for s in SEEDS}
        t = comp(A, B); nc_ += 1
        print(f'  period {p:4s} v3w {t[0]:7.0f} nc {t[1]:7.0f} d {t[2]:+6.0f} [{t[3]:+6.0f}, {t[4]:+6.0f}]')
    # road x period table of the v3w-nc median difference (descriptive)
    print('  road x period median(v3w-nc):')
    for rn in ('up', '3a', '3', '4a', '4', '5'):
        row = []
        for p in P:
            A = sarm(cell, 'v3w', f'f1.5_{rn}_{p}'); B = sarm(cell, 'nc', f'f1.5_{rn}_{p}')
            row.append(f'{p}:{np.median([A[s]-B[s] for s in SEEDS]):+6.0f}')
        print('   ', rn, ' '.join(row))
    # seed-level association with event differences
    dF = np.array([sarm(cell, 'v3w', 'f1.5')[s] - sarm(cell, 'nc', 'f1.5')[s] for s in SEEDS])
    for m in ('ev45_all', 'ev4_all', 'ev5_alks', 'ev45_car', 'ev4_car'):
        A = arm(cell, 'v3w', m); B = arm(cell, 'nc', m)
        dE = np.array([A[s] - B[s] for s in SEEDS])
        rho, p = spearmanr(dF, dE)
        print(f'  Spearman seeds: d f1.5 vs d {m}: {rho:+.2f} (p {p:.3f})')
    # jam by road
    for rn in ('up', '3', '4a', '4'):
        t = comp(sarm(cell, 'v3w', f'jam_{rn}'), sarm(cell, 'nc', f'jam_{rn}')); nc_ += 1
        print(f'  jam veh-s road {rn}: v3w {t[0]:.0f} nc {t[1]:.0f} d {t[2]:+.0f} [{t[3]:+.0f}, {t[4]:+.0f}]')
print('comparisons', nc_)
