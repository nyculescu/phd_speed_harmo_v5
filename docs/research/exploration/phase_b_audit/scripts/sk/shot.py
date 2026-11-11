# EXPLORATORY: P0-trained, hand-scaled policies against p333 on r2m3 with P0, 5,300 veh/h; delay.
import gzip, json, collections
import numpy as np
R='/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/phase3/'
def rows(p):
    with gzip.open(R+p,'rt') as f:
        for l in f:
            l=l.strip()
            if l: yield json.loads(l)
rng=np.random.default_rng(20261110)
def stat(ref,arm):
    d=(ref-arm)/np.median(ref)*100
    n=len(d); idx=rng.integers(0,n,(10000,n))
    bs=np.median(d[idx],axis=1)
    return np.median(d),np.percentile(bs,2.5),np.percentile(bs,97.5)
def load(f, flt=None):
    D=collections.defaultdict(dict); cf=collections.Counter(); names=collections.Counter()
    for r in rows(f):
        if flt and not flt(r): continue
        c=dict(r['cfg']); c.pop('ctrl',None); cf[json.dumps(c,sort_keys=True)]+=1
        names[r['name']]+=1
        D[(r['name'],r['q'])][r['seed']]=(r['delay'], r['N']-r['dist']/27.78)
    return D,cf,names
for f in ['shot_rows.jsonl.gz','rulecheck_rows.jsonl.gz']:
    D,cf,names=load(f)
    print('==',f,'plant flags',dict(cf)); print('   arms',sorted(names)[:60])
D,cf,names=load('shot_rows.jsonl.gz')
for cell in ['S','X1','X2']:
    keys=[k for k in D if k[0].split('|')[0]==cell or k[0].startswith(cell+'|')]
    ref=[k for k in keys if k[0].endswith('p333')]
    if not ref: print(cell,'no p333',keys[:5]); continue
    ref=D[ref[0]]; seeds=sorted(ref)
    for which,ix in (('finishers',0),('all-vehicle proxy',1)):
        out=[]; pts=[]
        for k in sorted(keys):
            a=k[0].split('|')[-1]
            if a in('p333',): continue
            x=D[k]; s=[i for i in seeds if i in x]
            m,lo,hi=stat(np.array([ref[i][ix] for i in s]),np.array([x[i][ix] for i in s]))
            out.append(f'{a} {m:+.1f} [{lo:+.1f}, {hi:+.1f}]')
            if a not in('nc','r4a1'): pts.append((m,lo,hi))
        print(f'{cell} {which} n={len(seeds)}: '+'; '.join(out))
        print(f'   policies: points {min(p[0] for p in pts):+.1f} to {max(p[0] for p in pts):+.1f}; CI above 0: {sum(p[1]>0 for p in pts)}; below 0: {sum(p[2]<0 for p in pts)} of {len(pts)}')
