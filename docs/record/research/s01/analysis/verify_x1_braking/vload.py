"""Load test rows into a compact pickle: (name, seed) -> flat numeric dict, plus histogram lists."""
import json, pickle, sys
import numpy as np

D = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/'
KEEP_LIST = ('m_peak_car', 'm_peak_alks', 'm_peak_truck', 'm_ah_car', 'm_ah_alks', 'm_ah_truck',
             'm_dur_car', 'm_dur_alks', 'm_dur_truck', 'm_dec_level_s', 'pert_log', 'm_st_shape', 'flow_min')
out = {}
for f, tag in (('rows_test.jsonl', 'test'),):
    with open(D + f) as h:
        for line in h:
            r = json.loads(line)
            d = {k: float(v) for k, v in r.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
            for k in KEEP_LIST:
                if k in r:
                    d[k] = r[k]
            for k in ('m_dec_totals',):
                if k in r and r[k]:
                    for kk, vv in r[k].items():
                        d[f'{k}_{kk}'] = float(vv)
            d['m_minute'] = r.get('m_minute')
            d['m_offsets'] = r.get('m_offsets')
            d['m_st_file'] = r.get('m_st_file')
            d['name'] = r['name']
            out[(r['name'], int(r['seed']))] = d
pickle.dump(out, open('test.pkl', 'wb'))
print(len(out), 'rows', len({k[0] for k in out}), 'names', len({k[1] for k in out}), 'seeds')
