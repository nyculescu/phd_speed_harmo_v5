import json, sys, pickle, collections, numpy as np
src='/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl'
t0=collections.defaultdict(lambda: collections.defaultdict(set)); t0keys=collections.Counter()
with open(src) as f:
    for line in f:
        r=json.loads(line); c=r.get('c1_t0') or {}
        t0keys[tuple(sorted(c))]+=1
        for k,v in c.items():
            if not isinstance(v,(dict,list)): t0[k][r['seed']].add(v)
print('c1_t0 key sets',t0keys.most_common(3))
for k,v in t0.items(): print(' c1_t0',k,': seeds with >1 distinct value across the 31 arms =',sum(len(x)>1 for x in v.values()),'of',len(v))
d=pickle.load(open(sys.argv[1],'rb'))
cf={a:json.loads(v[0]) for a,v in d['cfg'].items()}
base={k:v for k,v in cf['p333'].items() if k not in ('ctrl','cav_rule')}
print('p333 cfg keys',sorted(cf['p333'])); print('w0 cfg keys',sorted(cf['w0u250']))
for a,c in sorted(cf.items()):
    diff={k:(c.get(k),cf['p333'].get(k)) for k in set(c)|set(cf['p333']) if k not in ('ctrl',) and c.get(k)!=cf['p333'].get(k)}
    s=json.dumps(diff); print(f'{a:18s} non-ctrl cfg diffs vs p333: {s[:260]}')
print('p333 ctrl',json.dumps(cf['p333'].get('ctrl'))[:400]); print('lr400_16_1 ctrl',json.dumps(cf['lr400_16_1'].get('ctrl'))[:500]); print('nc',json.dumps(cf['nc'])[:600])
