import json, sys, collections
import numpy as np
P = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_test.jsonl'
KEYS = ['all_delay', 'delay', 'delay_ramp', 'delay_ramp2', 'ttc_net', 'passed', 'end_stop2', 'finished_pct', 'N']
T = collections.defaultdict(dict)
for l in open(P):
    r = json.loads(l)
    T[r['name']][r['seed']] = {k: r.get(k) for k in KEYS}
names = sorted(T)
print(len(names), names)
L = ['w0u250', 'w1u500', 'w2u250', 'w3u500', 'w4u500']
rng_seed = 20261110
def eff(Pv, Ov, level=95.0):
    # positive = P better (lower); median of paired differences over the reference median
    d = Ov - Pv
    e = 100 * np.median(d) / np.median(Ov)
    rng = np.random.default_rng(rng_seed)
    idx = rng.integers(0, len(d), (10000, len(d)))
    b = 100 * np.median(d[idx], axis=1) / np.median(Ov[idx], axis=1)
    a = (100 - level) / 2
    return e, np.percentile(b, a), np.percentile(b, 100 - a)
for cell in ['X1', 'X2']:
    seeds = sorted(T[f'{cell}|p333'])
    print(cell, 'seeds', len(seeds), seeds[0], seeds[-1])
    arm = {k: np.array([np.mean([T[f'{cell}|{n}'][s][k] for n in L]) for s in seeds]) for k in KEYS if k != 'delay_ramp2' or True}
    opps = [n.split('|')[1] for n in names if n.startswith(cell + '|') and n.split('|')[1] not in L and not n.split('|')[1][0] in 'tsd' ]
    print(' opps', opps)
    for o in opps:
        O = {k: np.array([T[f'{cell}|{o}'][s][k] for s in seeds], float) for k in KEYS}
        out = []
        for k in ['all_delay', 'delay_ramp', 'delay_ramp2']:
            for lv in ([95.0, 97.5] if k == 'all_delay' else [95.0]):
                e, lo, hi = eff(arm[k], O[k], lv)
                out.append(f'{k}@{lv}: {e:+.1f} [{lo:+.1f}, {hi:+.1f}]')
        print('  v3w arm vs', o, ' | '.join(out), '| med all_delay', round(float(np.median(O['all_delay']))))
    # per learner vs key opponents
    for o in ['p333', 'lr1000_10_1', 'os0_10_10', '3ex2' if cell == 'X2' else '3ex1', 'lr1000_16_2']:
        O = np.array([T[f'{cell}|{o}'][s]['all_delay'] for s in seeds], float)
        pts = [eff(np.array([T[f'{cell}|{n}'][s]['all_delay'] for s in seeds], float), O)[0] for n in L]
        print('  per-learner delay vs', o, [round(p, 1) for p in pts], 'mean', round(float(np.mean(pts)), 2))
    # envelope: v3w arm vs per-seed best rule is not a fair arm; instead SD of paired pct difference
    for o in ['p333', 'lr1000_10_1', 'os0_10_10']:
        O = np.array([T[f'{cell}|{o}'][s]['all_delay'] for s in seeds], float)
        d = 100 * (O - arm['all_delay']) / np.median(O)
        d1 = 100 * (O - np.array([T[f'{cell}|w0u250'][s]['all_delay'] for s in seeds], float)) / np.median(O)
        print('  paired SD % (arm, single learner) vs', o, round(float(np.std(d, ddof=1)), 1), round(float(np.std(d1, ddof=1)), 1), 'mean diff arm', round(float(np.mean(d)), 2))
