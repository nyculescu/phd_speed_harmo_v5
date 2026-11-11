import json, glob, os
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
T = J['cells']['TRUCK']
mr = T['map_report_only']
def r(a):
    return None if a is None else ([None if b is None else round(b, 2) for b in a] if isinstance(a, list) else round(a, 2))
for opp in ('3E-C_TRUCK', 'p333'):
    o = mr[opp]
    for k in ('events_ge45', 'jam_share', 'congested_share', 'jams', 'congested_km_mean', 'congested_km_max', 'osc_kmh', 'ttc3_lc_share', 'collisions', 'alks_full_moving'):
        x = o.get(k)
        if isinstance(x, dict):
            print(opp, k, {kk: r(vv) for kk, vv in x.items() if kk in ('effect', 'ci95', 'ci_m', 'ci9875', 'level')}, [kk for kk in x.keys()])
        else:
            print(opp, k, x)
print('plateau', J['provenance']['plateau'])
p = T['pr28']
print('pr28', {k: (v if not isinstance(v, (dict, list)) else type(v).__name__) for k, v in p.items()} if isinstance(p, dict) else p)
print('learner_signs', T['learner_signs'], T['n_learner_signs'])
pl = T['map']['3E-C_TRUCK']['per_learner']
vals = {k: v for k, v in pl.items()}
k0 = list(vals)[0]; print('per learner entry', vals[k0])
try:
    cfv = [v['cf']['effect'] if isinstance(v['cf'], dict) else v['cf'] for v in vals.values()]
    print('per learner cf', [round(c, 2) for c in cfv], 'mean', round(sum(cfv) / 5, 2))
except Exception as e:
    print('err', e)
# supplement
sp = '/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json'
print(os.path.exists(sp), os.path.getsize(sp) if os.path.exists(sp) else '')
