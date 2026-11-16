import json,csv
d=json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
R=d['cells']['TRUCK']['map_report_only']
print(sorted(R['p333'].keys()))
def e(x):
    if isinstance(x,dict) and 'effect' in x:
        c=x.get('ci95') or [float('nan')]*2
        if x['effect'] is None: return 'None'
        return '%+.2f [%+.2f, %+.2f]'%(x['effect'],c[0],c[1])
    return json.dumps(x)[:80]
for k in ['alks_full_moving','ttc15','ttc2','sev3','robust_raw','osc','congested_share']:
    if k in R['p333']:
        print(k, '| p333', e(R['p333'][k]), '| os0', e(R['os0_10_10'][k]), '| 3E-C', e(R['3E-C_TRUCK'][k]), '| nc', e(R['nc'][k]))
rows=list(csv.DictReader(open('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round2/report/test_table.csv')))
for c in ('X1','X2'):
    print(c,'name: fuel g/km (fuel_step/dist_step*1000?), jerk_step, delay_ramp, delay_ramp2, delay')
    for r in rows:
        if r['cell']==c and r['name'] in ('v3w arm','p333','os0_10_10','os1_15_10','3ex1','3ex2','3e','lr1000_16_2','lr1000_10_1','nc'):
            print('   %-12s fuel/dist %.4f jerk %.0f ramp %.1f ramp2 %.1f delay %.1f'%(r['name'],float(r['fuel_step'])/float(r['dist_step']),float(r['jerk_step']),float(r['delay_ramp']),float(r['delay_ramp2']),float(r['delay'])))
