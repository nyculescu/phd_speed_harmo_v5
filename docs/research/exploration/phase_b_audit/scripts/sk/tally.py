# Provenance tally: plant flags and the all_delay key only. No outcome statistic.
import gzip, json, collections, glob, os
def rows(p):
    op = gzip.open if p.endswith('.gz') else open
    with op(p,'rt') as f:
        for l in f:
            l=l.strip()
            if l: yield json.loads(l)
files=sorted(glob.glob('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v3/rows/*.jsonl.gz'))
files+=['/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl','/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl']
for p in files:
    c=collections.Counter(); n=0; ad=0; seeds=set()
    for r in rows(p):
        n+=1; ad+=('all_delay' in r); seeds.add(r.get('seed'))
        cfg=r.get('cfg')
        if isinstance(cfg,dict):
            k={x:cfg[x] for x in cfg if x not in('ctrl','measure')}
            c[json.dumps(k,sort_keys=True)]+=1
        else: c['no cfg key']+=1
    print(os.path.basename(p),'| rows',n,'| all_delay',ad,'| seeds',min(seeds),'-',max(seeds),'|',dict(c))
