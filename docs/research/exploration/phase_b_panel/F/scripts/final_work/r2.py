"""Named fields from the recorded v2.3 reading (no dump)."""
import json
J = json.load(open('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json'))
C = J['cells']['TRUCK']
mro = C['map_report_only']
def show(e):
    if isinstance(e, dict):
        return {k: (round(v, 3) if isinstance(v, float) else ([round(x, 3) for x in v] if isinstance(v, list) and len(v) <= 4 and all(isinstance(x,(int,float)) for x in v) else (v if not isinstance(v,(list,dict)) else type(v).__name__))) for k, v in e.items()}
    return e
print('entry shape p333.congested_km_max:', show(mro['p333']['congested_km_max']))
for arm in ('p333', '3E-C_TRUCK', 'os0_10_10', '3E-D_TRUCK', 'nc'):
    for k in ('jam_share', 'jams', 'congested_km_mean', 'congested_km_max', 'congested_share', 'osc_kmh', 'events_ge45', 'ttc15', 'ttc2', 'sev3', 'b45_step', 'robust_braking', 'ttc3_lc_share', 'ttt', 'jam_share_nc','jams_nc','congested_km_mean_nc','congested_km_max_nc'):
        e = mro[arm].get(k)
        print(arm, k, show(e))
print()
M = C['map']
print('map arms', len(M), 'entry keys', sorted(M['p333']))
print('map p333 delay', show(M['p333']['delay']), 'cf', show(M['p333']['cf']))
rows = []
for a, v in M.items():
    d = v['delay']; c = v['cf']
    rows.append((d.get('ci_m', [None])[0], a, d.get('effect', d.get('e')), d.get('ci_m'), c.get('effect', c.get('e')), c.get('ci_m')))
for r in sorted(rows, key=lambda r: r[0]):
    print(r[1], 'delay', r[2], r[3], 'cf', r[4], r[5])
print('S map 3E-C', show(J['S']['map']['3E-C_TRUCK']['cf']), show(J['S']['map']['3E-C_TRUCK']['delay']))
print('m', J['m'])
print('must_carry', J['must_carry'] if isinstance(J['must_carry'], (str,)) else (J['must_carry'] if len(str(J['must_carry']))<1500 else str(J['must_carry'])[:1500]))
print('overfit 3E-C', {k: show(v) if isinstance(v, dict) else v for k, v in C['overfit_vs_p333']['3E-C_TRUCK'].items()})
print('pr28', show(C['pr28']) if isinstance(C['pr28'], dict) else C['pr28'])
