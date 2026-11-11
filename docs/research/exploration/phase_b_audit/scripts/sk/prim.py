# EXPLORATORY: baseline-v3 policies against p333, all-vehicle delay, plant_c3, 5,300 veh/h, confirmatory 3 and 3b rows.
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
D=collections.defaultdict(dict)
for f in ['conf3_eval_primary.jsonl.gz','conf3b_eval_x2.jsonl.gz']:
    for r in rows(f):
        parts=r['name'].split('|')
        cell,arm=(parts[0],parts[-1]) if len(parts)>1 else ('X2',parts[0])
        D[(cell,arm)][r['seed']]=r['all_delay']
print(sorted(set(k[1] for k in D)))
for cell in sorted(set(k[0] for k in D)):
    ref=D[(cell,'p333')]; seeds=sorted(ref)
    for lab,ss in (('all',seeds),('200-219',[s for s in seeds if s<7440220]),('220-239',[s for s in seeds if s>=7440220])):
        if not ss: continue
        out=[]
        for a in ['d0','d1','d2','d3','d4']:
            x=D[(cell,a)]; s=[i for i in ss if i in x]
            if not s: continue
            m,lo,hi=stat(np.array([ref[i] for i in s]),np.array([x[i] for i in s]))
            out.append(f'{a} {m:+.1f} [{lo:+.1f}, {hi:+.1f}]')
        # stacked single learners
        dd=[]
        for a in ['d0','d1','d2','d3','d4']:
            x=D[(cell,a)]
            dd.append([ref[i]-x[i] for i in ss])
        dd=np.array(dd)/np.median([ref[i] for i in ss])*100
        n=dd.shape[1]; idx=rng.integers(0,n,(10000,n))
        bs=np.median(dd[:,idx].transpose(1,0,2).reshape(10000,-1),axis=1)
        print(f'{cell} seeds {lab} n={len(ss)}: '+'; '.join(out)+f' | stacked {np.median(dd):+.1f} [{np.percentile(bs,2.5):+.1f}, {np.percentile(bs,97.5):+.1f}]')
