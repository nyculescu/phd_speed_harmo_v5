import json, collections
import numpy as np
P = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_test.jsonl'
KEYS = ['all_delay', 'finished_pct', 'passed', 'arrived', 'N', 'flow_min', 'alks_full_events']
T = collections.defaultdict(dict)
for l in open(P):
    r = json.loads(l)
    T[r['name']][r['seed']] = {k: r.get(k) for k in KEYS}
for cell in ['X1', 'X2']:
    seeds = sorted(T[f'{cell}|p333'])
    for n in ['nc', 'p333', 'lr1000_10_1', 'os0_10_10', '3ex1' if cell == 'X1' else '3ex2', 'w0u250', 'w3u500']:
        R = [T[f'{cell}|{n}'][s] for s in seeds]
        fm = np.array([r['flow_min'] for r in R], float)
        print(cell, n, 'finished_pct med', round(float(np.median([r['finished_pct'] for r in R])), 1), 'passed med', np.median([r['passed'] for r in R]), 'arrived med', np.median([r['arrived'] for r in R]),
              '| minutes', fm.shape[1], 'last10 veh/min', round(float(fm[:, -10:].mean()), 1), 'first5', round(float(fm[:, :5].mean()), 1), 'last3', round(float(fm[:, -3:].mean()), 1))
