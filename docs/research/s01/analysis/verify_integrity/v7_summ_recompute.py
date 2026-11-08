# Recompute selected summary metrics from rows and st/*.npz with own code; compare with summary_rows_*.json.
import json, os, sys, warnings
from multiprocessing import Pool
import numpy as np
M = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/'

def mine(r):
    f = np.load(M + 'st/' + os.path.basename(r['m_st_file']))
    v, n = f['v'].astype(float), f['n'].astype(float)
    if list(v.shape) != list(r['m_st_shape']):
        return None, 'shape'
    V = np.full(v.shape, np.nan); m = n > 0; V[m] = 3.6 * v[m] / n[m]
    occ = m
    w = n.sum()
    jam = occ & (V < 30.0); cong = occ & (V < 60.0)
    cov = occ.mean(axis=0) >= 0.8
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        osc = [np.nanstd(V[:, j]) for j in np.nonzero(cov)[0]]
    out = {'jam_share': n[jam].sum() / w, 'congested_km_max': (cong.sum(axis=1) * r['m_st_dx'] / 1000).max(),
           'osc_kmh': float(np.mean(osc)) if osc else None}
    for c in ('car', 'alks', 'truck'):
        pk = r[f'm_peak_{c}']
        out[f'events_ge45_{c}'] = sum(pk[3:])
        out[f'cascade_share_{c}'] = r[f'm_cascade_{c}'] / r[f'm_events_{c}'] if r[f'm_events_{c}'] else None
    ls = r.get('m_dec_level_s')
    out['level_on_last'] = (ls[-1] / sum(ls)) if ls and sum(ls) else None
    return out, None

def work(tag):
    S = json.load(open(M + f'summary_rows_{tag}.json'))
    worst = {}
    n = 0; bad = 0
    for l in open(M + f'rows_{tag}.jsonl'):
        r = json.loads(l)
        key = f"{r['name']}|{r['q']:.0f}"
        s = S[key][str(r['seed'])]
        o, err = mine(r)
        if err:
            bad += 1; continue
        ref = {'jam_share': s['waves']['jam_share'], 'congested_km_max': s['waves']['congested_km_max'], 'osc_kmh': s['waves']['osc_kmh'],
               'level_on_last': (s['dec']['level_share_on'][-1] if 'dec' in s and s['dec']['level_share_on'] else None)}
        for c in ('car', 'alks', 'truck'):
            ref[f'events_ge45_{c}'] = s[f'events_ge45_{c}']; ref[f'cascade_share_{c}'] = s[f'cascade_share_{c}']
        for k in o:
            a, b = o[k], ref[k]
            if a is None or b is None:
                d = 0.0 if a is None and b is None else float('inf')
            else:
                d = abs(a - b) / max(abs(a), abs(b), 1e-12)
            worst[k] = max(worst.get(k, 0.0), d)
        n += 1
    return tag, n, bad, worst

if __name__ == '__main__':
    with Pool(3) as p:
        for tag, n, bad, worst in p.map(work, ['test', 'band', 's1']):
            print(tag, 'runs', n, 'shape errors', bad, 'max rel diff per metric', {k: float(f'{v:.2g}') for k, v in worst.items()})
