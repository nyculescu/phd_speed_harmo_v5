# Plant TTC < 3 s samples per vehicle-second by road group, and vehicle-weighted mean speed on main lanes near the merges.
import json, collections
import numpy as np
P = '/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl'
want = {'nc', 'lr400_16_1', 'w1u500', 'p333'}
T = collections.defaultdict(lambda: collections.defaultdict(float)); V = collections.defaultdict(lambda: collections.defaultdict(float))
sp = collections.defaultdict(lambda: collections.defaultdict(float))
ex = None
with open(P) as f:
    for line in f:
        r = json.loads(line)
        a = r['name'].split('|', 1)[1]
        if a not in want: continue
        if ex is None: ex = r.get('m_road_vs'); print('m_road_vs sample', json.dumps(ex)[:300])
        T[a]['net'] += r['ttc_net']; V[a]['net'] += r['vs']
        for g, per in (r.get('m_road_ttc3') or {}).items():
            T[a][g] += sum(per.values())
        for g, per in (r.get('m_road_vs') or {}).items():
            V[a][g] += sum(per.values()) if isinstance(per, dict) else per
        for x in ('3a_1', '3_0', '4a_1'):
            sp[a]['n_' + x] += r.get('n_' + x, 0); sp[a]['nv_' + x] += r.get('nv_' + x, 0)
out = {}
for a in want:
    out[a] = {g: round(T[a][g] / V[a][g], 4) for g in T[a] if V[a].get(g)}
    out[a]['mean_speed_ms'] = {x: round(sp[a]['nv_' + x] / max(sp[a]['n_' + x], 1), 2) for x in ('3a_1', '3_0', '4a_1')}
print(json.dumps(out, indent=1))
json.dump(out, open('rate.json', 'w'), indent=1)
