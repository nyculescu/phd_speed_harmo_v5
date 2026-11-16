# Descriptive paired comparison by follower-speed band and by road group; not the protocol's C-D5 statistic.
import json, collections
import numpy as np
P = '/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl'
L = ['w0u250','w1u500','w2u250','w3u500','w4u500']
want = set(L + ['lr400_16_1','nc','p333','grid_lr400_13_1'])
X = collections.defaultdict(dict)
with open(P) as f:
    for line in f:
        r = json.loads(line)
        a = r['name'].split('|',1)[1]
        if a not in want: continue
        mr = r.get('m_road_ttc3') or {}
        g = {k: sum(v.values()) for k, v in mr.items()}
        d = {k: float(r.get(k, 0) or 0) for k in ('ttc_net','ttc3_s_lo','ttc3_s_mid','ttc3_s_hi','end_stop','end_stop2','m_ttc3_lc','m_ttc3_all')}
        d['g3a'] = g.get('3a', 0); d['g4a'] = g.get('4a', 0); d['gother'] = sum(v for k, v in g.items() if k not in ('3a','4a'))
        d['nlc'] = d['m_ttc3_all'] - d['m_ttc3_lc']
        X[a][r['seed']] = d
seeds = sorted(X['lr400_16_1'])
K = ['ttc_net','ttc3_s_lo','ttc3_s_mid','ttc3_s_hi','g3a','g4a','gother','m_ttc3_lc','nlc','end_stop','end_stop2']
v3w = {s: {k: np.mean([X[l][s][k] for l in L]) for k in K} for s in seeds}
rng = np.random.default_rng(1)
res = {}
for opp in ('lr400_16_1','nc','p333','grid_lr400_13_1'):
    res[opp] = {}
    for k in K:
        a = np.array([X[opp][s][k] for s in seeds]); b = np.array([v3w[s][k] for s in seeds])
        dlt = a - b
        bs = [np.median(rng.choice(dlt, len(dlt))) for _ in range(2000)]
        res[opp][k] = dict(med_opp=float(np.median(a)), med_v3w=float(np.median(b)), med_diff=float(np.median(dlt)),
                           ci=[float(np.percentile(bs,2.5)), float(np.percentile(bs,97.5))], rel_pct=float(100*np.median(dlt)/max(np.median(a),1e-9)))
json.dump(res, open('band.json','w'), indent=1)
for opp in res:
    print('==', opp, '(positive = v3w fewer)')
    for k, d in res[opp].items():
        print(f"{k:11s} opp {d['med_opp']:8.1f} v3w {d['med_v3w']:8.1f} diff {d['med_diff']:7.1f} [{d['ci'][0]:.1f}, {d['ci'][1]:.1f}] rel {d['rel_pct']:.1f}%")
