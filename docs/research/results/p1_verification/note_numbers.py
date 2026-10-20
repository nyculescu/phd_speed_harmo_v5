"""Print every number used in docs/research/results/p1_result.md from result.json (no runs, no bootstrap).
rel and rel CIs in %, diff CIs in s/veh. Level is printed with each statistic."""
import json, sys
R = json.load(open(sys.argv[1] if len(sys.argv) > 1 else '/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
e = R['eval']
CELLS = ('slow_q1600', 'block_q1600', 'slow_q2000', 'block_q2000')
def f(s):
    return (f"rel {100*s['rel']:.1f} [{100*s['rel_ci'][0]:.1f}, {100*s['rel_ci'][1]:.1f}] diff {s['diff']:.1f} "
            f"[{s['diff_ci'][0]:.1f}, {s['diff_ci'][1]:.1f}] lvl {s['level']:.5f}")
print('S1a', e['S1']['S1a_pass'], e['S1']['S1a_cells_both_views'], 'S1b', e['S1']['S1b_pass'], e['S1']['S1b_cells_both_views'])
for c in CELLS:
    pc = e['S1']['per_cell_stats'][c]
    print(f'== {c}')
    for r in ('N', 'FX', 'FB', 'PI', 'AD'):
        print(f'  S1 ID vs {r}:', f(pc['ID_vs'][r]['all_seeds']))
    print('  S1 IP vs ID:', f(pc['IP_vs_ID']['all_seeds']))
    for r in ('N', 'FX', 'FB', 'PI', 'AD'):
        print(f'  IP vs {r} (S1 lvl):', f(e['cells'][c]['IP_vs_L0'][r]['all_seeds']))
    fl = e['fig1_ladder'][c]
    print('  fig1 strongest L0', fl['strongest_L0'], [(g['arm'], round(g['median_delay_s'], 1), f(g['vs_strongest_L0']) if g['vs_strongest_L0'] else None) for g in fl['rungs']])
    s2 = e['S2'][c]['all_seeds']
    print('  S2 x', round(100*s2['x'], 1), 'y', round(100*s2['y'], 1), 'yhat', round(100*s2['y_hat'], 1), 'plateau', s2['plateau_holds'], 'Rmax', s2['Rmax'])
    print('  TP', f(e['TP'][c]))
    s3 = e['S3'][c]
    for lab in ('d_star', 'c_star', 'p_star'):
        a = s3[lab]['all_seeds']
        print(f'  {lab}', a['value'], a['flag'], a['binding_arm'], a['ci'], 'gt_max', a['share_censored_gt_max'], 'never', a['share_never_ahead'],
              {r: (a['per_arm'][r]['value'], a['per_arm'][r]['flag'], [round(m, 1) for m in a['per_arm'][r]['M']] if isinstance(a['per_arm'][r].get('M'), list) else a['per_arm'][r].get('M')) for r in a['per_arm']})
    print('  clearance applies', s3['clearance_delay_applies'], 'combined vs IP', f(s3['combined_row']['vs_IP']['all_seeds']))
for q in ('1600', '2000'):
    pq = e['per_q'][q]
    print(f'== q{q} FA cost', pq['false_alarm_cost'])
    for pi, p in pq['prevalence'].items():
        print(f'  pi {pi} ctrl', p['controllers'])
        for t in ('ID_vs', 'IP_vs'):
            if t in p:
                print(f'   {t}', {r: f(p[t][r]['all_seeds']) for r in p[t]})
        rest = {k: v for k, v in p.items() if k not in ('controllers', 'ID_vs', 'IP_vs')}
        print('   rest', json.dumps(rest)[:900])
print('grid edges', json.dumps(R['tune'].get('grid_edges_report_only')))
