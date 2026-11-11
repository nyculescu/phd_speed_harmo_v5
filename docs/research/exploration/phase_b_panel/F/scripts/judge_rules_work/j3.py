import json
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
T = J['cells']['TRUCK']; S = J['S']
def f(x): return f"{x['effect']:+.2f} [{x['ci_m'][0]:+.2f}, {x['ci_m'][1]:+.2f}]" if 'ci_m' in x else f"{x['effect']:+.2f} ci95 [{x['ci95'][0]:+.2f}, {x['ci95'][1]:+.2f}]"
# steady: K1 and K2 counts
k1 = [o for o, v in S['map'].items() if v['cf']['effect'] < 10 or v['cf']['ci_m'][0] <= 0]
print('S K1 fires against', len(k1), k1)
for marg in (-1, -2, -3):
    k2 = [o for o, v in S['map'].items() if v['delay']['ci_m'][0] <= marg]
    print('S K2 margin', marg, 'fires against', len(k2), 'holds', 23 - len(k2), k2)
k1t = [o for o, v in T['map'].items() if v['cf']['effect'] < 10 or v['cf']['ci_m'][0] <= 0]
print('TRUCK K1 fires', k1t)
for marg in (-1, -2):
    print('TRUCK K2', marg, [o for o, v in T['map'].items() if v['delay']['ci_m'][0] <= marg])
lo = sorted((v['delay']['ci_m'][0], o) for o, v in T['map'].items())[:4]
print('TRUCK lowest delay lower bounds', lo)
cfs = sorted((v['cf']['effect'], o, v['cf']['ci_m']) for o, v in T['map'].items())[:3]
print('TRUCK closest cf', cfs)
# 20 s per run rule: is there a field for median paired reduction?
print('cf keys', list(T['map']['3E-C_TRUCK']['cf'].keys()))
print('comparisons type', type(T['comparisons']).__name__, (list(T['comparisons'].keys())[:10] if isinstance(T['comparisons'], dict) else T['comparisons'][:1]))
ov = T['overfit_vs_p333']
print('overfit keys', list(ov.keys()))
print('overfit 3E-C', {k: v for k, v in ov['3E-C_TRUCK'].items()})
mr = T['map_report_only']
print('mro keys', list(mr.keys())[:30])
o = mr.get('3E-C_TRUCK')
print('mro 3E-C keys', list(o.keys()))
for k in o:
    if isinstance(o[k], dict) and 'effect' in o[k]:
        x = o[k]
        print('  3E-C', k, round(x['effect'], 2), [round(a, 2) for a in x.get('ci95', [])], [round(a, 2) for a in x.get('ci_m', [])] if 'ci_m' in x else '')
o = mr.get('p333')
for k in ('jam_share', 'congested_km_mean', 'events_ge45', 'osc_kmh', 'jams'):
    if k in o:
        x = o[k]; print('  p333', k, round(x['effect'], 2), [round(a, 2) for a in x.get('ci95', [])])
print('plateau', J['provenance']['plateau'])
print('pr28', T['pr28'] if not isinstance(T['pr28'], dict) else {k: (v if not isinstance(v, (dict, list)) else type(v).__name__) for k, v in T['pr28'].items()})
print('learner_signs', T['learner_signs'], T['n_learner_signs'])
pl = T['map']['3E-C_TRUCK']['per_learner']
print('per learner cf vs 3E-C', {k: round(v['cf']['effect'], 2) if isinstance(v.get('cf'), dict) else v for k, v in pl.items()})
