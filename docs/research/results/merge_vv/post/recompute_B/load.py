"""Flatten the screen rows into one DataFrame (recomputer B)."""
import json
import sys
from collections import Counter

import pandas as pd

SRC = '/home/catalin/work/phd/v5b1_runs/vv_remote/vv_screen/s6_rows.jsonl'
OUT = '/home/catalin/work/phd/v5b1_runs/vv_post/recompute_B/rows.pkl'

SCALARS = ['name', 'cell', 'arm', 'learner', 'seed', 'ttc_net', 'ttc3', 'm_ttc3_all',
           'vv_ttc3_main', 'vv_m_time', 'vv_m_step', 'vv_m_whole', 'vv_m_half', 'ttc_half',
           'end_stop', 'end_stop2', 'vv_enc', 'vv_merges', 'commit', 'collisions',
           'teleports', 'm_stuck_n', 'all_delay']

recs = []
roads = Counter()
periods = Counter()
with open(SRC) as f:
    for line in f:
        r = json.loads(line)
        d = {k: r.get(k) for k in SCALARS}
        tot = 0
        for road, per in r['m_road_ttc3'].items():
            roads[road] += 1
            s = 0
            for p, v in per.items():
                periods[p] += 1
                s += v
                d['rp_%s_%s' % (road, p)] = v
            d['road_%s' % road] = s
            tot += s
        d['road_sum'] = tot
        for lane in ('3a_0', '4a_0'):
            d['stand_s_' + lane] = r['vv_stand_s'].get(lane)
            d['stand_n_' + lane] = r['vv_stand_n'].get(lane)
        d['stand_s_keys'] = ','.join(sorted(r['vv_stand_s']))
        recs.append(d)

df = pd.DataFrame(recs)
rcols = [c for c in df.columns if c.startswith('road_') or c.startswith('rp_')]
df[rcols] = df[rcols].fillna(0)
df.to_pickle(OUT)
print('rows', len(df), 'roads', dict(roads), 'periods', dict(periods), file=sys.stderr)
