# EXPLORATORY: baseline-v3 policies against p333, all-vehicle delay, confirmatory 3 map cells (plant_c3).
import gzip, json, collections
import numpy as np
R='/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v3/rows/'
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
for f in ['conf3_eval_map.jsonl.gz','conf3_eval_map_x.jsonl.gz']:
    D=collections.defaultdict(dict)
    names=collections.Counter()
    cfgs=collections.Counter()
    for r in rows(f):
        cell,arm=r['name'].split('|',1)
        D[(cell,r['q'],arm)][r['seed']]=r['all_delay']
        names[arm]+=1
        c=dict(r['cfg']); c.pop('ctrl',None); cfgs[json.dumps(c,sort_keys=True)]+=1
    print('==',f,dict(names)); print('   plant flags:',dict(cfgs))
    for (cell,q) in sorted(set((k[0],k[1]) for k in D)):
        ref=D.get((cell,q,'p333'))
        if not ref: continue
        out=[]
        seeds=sorted(ref)
        for a in ['d0','d1','d2','d3','d4','nc']:
            x=D.get((cell,q,a))
            if not x: continue
            s=[s for s in seeds if s in x]
            m,lo,hi=stat(np.array([ref[i] for i in s]),np.array([x[i] for i in s]))
            out.append(f'{a} {m:+.1f} [{lo:+.1f}, {hi:+.1f}] n={len(s)}')
        print(f'  {cell} {q:.0f}: '+'; '.join(out))
