import json, sys, collections
import numpy as np
P = '/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl'
keys = ['ttc_net','ttc3','ttc3_s_lo','ttc3_s_mid','ttc3_s_hi','ttc3_r_3','ttc3_r_4a','ttc3_r_ramp2','ttc3_r_rest','end_stop','end_stop2','m_ttc3_all','m_ttc3_lc','halt_3a_0','collisions','ttc_half','vs','passed']
D = collections.defaultdict(lambda: collections.defaultdict(list))
G = collections.defaultdict(lambda: collections.defaultdict(list))
first = None
with open(P) as f:
    for line in f:
        r = json.loads(line)
        a = r['name'].split('|',1)[1]
        for k in keys:
            D[a][k].append(float(r.get(k, np.nan) or 0))
        mr = r.get('m_road_ttc3')
        if mr:
            if first is None:
                first = mr; print('m_road_ttc3 sample', json.dumps(mr)[:400])
            for g, per in mr.items():
                G[a][g].append(sum(per.values()) if isinstance(per, dict) else per)
out = {}
for a in sorted(D):
    d = {k: float(np.median(v)) for k, v in D[a].items()}
    d['n'] = len(D[a]['ttc_net'])
    d['share_lo'] = float(np.sum(D[a]['ttc3_s_lo'])/np.sum(D[a]['ttc3']))
    d['share_mid'] = float(np.sum(D[a]['ttc3_s_mid'])/np.sum(D[a]['ttc3']))
    d['share_lc'] = float(np.sum(D[a]['m_ttc3_all']) and np.sum(D[a]['m_ttc3_lc'])/np.sum(D[a]['m_ttc3_all']))
    d['road_share'] = {g: float(np.sum(v)/np.sum(D[a]['m_ttc3_all'])) for g, v in G[a].items()}
    d['road_med'] = {g: float(np.median(v)) for g, v in G[a].items()}
    d['ttc3_eq_net_frac'] = float(np.mean(np.array(D[a]['ttc3']) == np.array(D[a]['ttc_net'])))
    d['mall_eq_net_frac'] = float(np.mean(np.array(D[a]['m_ttc3_all']) == np.array(D[a]['ttc_net'])))
    out[a] = d
json.dump(out, open('agg.json','w'), indent=1)
for a in sorted(out):
    d = out[a]
    print(a, d['n'], 'net', round(d['ttc_net']), 'lo%', round(100*d['share_lo'],1), 'mid%', round(100*d['share_mid'],1), 'lc%', round(100*d['share_lc'],1),
          'es1', d['end_stop'], 'es2', d['end_stop2'], 'eq', d['ttc3_eq_net_frac'], d['mall_eq_net_frac'],
          {g: round(100*x,1) for g, x in sorted(d['road_share'].items())})
