import csv
rows=list(csv.DictReader(open('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round2/report/test_table.csv')))
for r in rows:
    if r['name']=='v3w arm':
        print(r['cell'], 'all_delay',r['all_delay'],'ttc3',r['ttc3'])
        for k,v in r.items():
            if ('delay_vs' in k or 'ttc_vs' in k) and v: print('   ',k,v)
med={ (r['cell'],r['name']):float(r['all_delay']) for r in rows}
for c in ('X1','X2'):
    v=med[(c,'v3w arm')]
    xs=sorted((d,n) for (cc,n),d in med.items() if cc==c)
    print(c,[(n,round(d),round(100*(d-v)/d,1)) for d,n in xs if not n[0] in 'dstw' or n in('tail arm','sw arm')][:12])
