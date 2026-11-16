import csv
rows=list(csv.DictReader(open('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1/report/test_table.csv')))
print([k for k in rows[0].keys() if 'vs' in k][:20])
for r in rows:
    if 'v3w' in r['name'] or r['name'] in ('incumbent arm','w arm'):
        print(r['cell'], r['name'], {k:v for k,v in r.items() if 'delay_vs' in k and v})
print(sorted(set(r['name'] for r in rows))[:40])
