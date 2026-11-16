import json, sys, pickle, numpy as np
z=np.load(sys.argv[1]); R=list(z['R']); L=list(z['L']); P=z['P']; Q=z['Q']; raw=z['raw']; n=480
den=np.median(Q,axis=-1); i=R.index('lr400_16_1')
bs=raw[1,i].mean(0)/den[1,i]*100
lo=np.percentile(bs,1.25); u,c=np.unique(np.round(bs,9),return_counts=True)
print('E(lr400_16_1) resample dist: unique values',len(u),'of',len(bs),'; share exactly at lo',np.mean(np.isclose(bs,lo)),'; P(bs<=0)=',np.mean(bs<=0),'; P(bs<5)=',np.mean(bs<5),'min',bs.min())
for p in [0.1,0.5,1.25,2.5,5,50,95,97.5,98.75]: print('  pct',p,round(float(np.percentile(bs,p)),3))
# larger B, other rng
X=(Q[1,i][None]-P[1])/den[1,i]*100
for seed in (5,6):
    rng=np.random.default_rng(seed); out=[]
    for _ in range(100):
        idx=rng.integers(0,n,(1000,n)); out.append(np.median(X[:,idx],axis=-1).mean(0))
    o=np.concatenate(out); print('B=100000 rng',seed,'lo/hi 97.5%:',np.percentile(o,[1.25,98.75]),' 99% two-sided:',np.percentile(o,[0.5,99.5]),' 99.9%:',np.percentile(o,[0.05,99.95]))
# Hodges-Lehmann / sign-based exact CI per learner for the median paired difference
from math import comb
def sign_ci(d,alpha=0.025):
    d=np.sort(d); m=len(d); cum=0; k=0
    while True:
        cum+=comb(m,k)/2**m
        if cum>alpha/2: break
        k+=1
    return d[k-1] if k>0 else d[0], d[m-k]
for li,l in enumerate(L):
    a,b=sign_ci(X[li]); print('  exact sign-test 97.5 % CI for median paired diff,',l,':',round(a,2),round(b,2))
# heterogeneity by drawn duration and onset
d=pickle.load(open(sys.argv[2],'rb'))['rows']
seeds=list(range(7489160,7489640)); si={s:k for k,s in enumerate(seeds)}
on=np.empty(n); du=np.empty(n)
for r in d:
    if r['arm']=='nc': on[si[r['seed']]]=r['draw'][1]; du[si[r['seed']]]=r['draw'][2]
for nm,v in (('duration',du),('onset',on)):
    qs=np.quantile(v,[0,1/3,2/3,1])
    for k in range(3):
        m=(v>=qs[k])&(v<=qs[k+1]) if k==2 else (v>=qs[k])&(v<qs[k+1])
        for r in ('lr400_16_1','p333'):
            j=R.index(r); e=np.mean([np.median(Q[1,j][m]-P[1,l][m]) for l in range(5)])/np.median(Q[1,j][m])*100
            print(f'  {nm} tercile {k+1} [{qs[k]:.0f},{qs[k+1]:.0f}] n={m.sum()} E({r})={e:+.2f}',end=' |')
        print()
# P0 check: rule vs nc on delay
nc=Q[0,R.index('nc')]; IDX=z['IDX'].astype(np.int64)
res=[]
for r in R:
    if r=='nc': continue
    x=-(Q[0,R.index(r)]-nc)/np.median(nc)*100; pt=np.median(x); b=np.median(x[IDX],axis=-1); res.append((np.percentile(b,2.5),pt,r))
print('P0: smallest 95 % lower bound',min(res),' smallest point',min((p,r) for _,p,r in res),' largest',max((p,r) for _,p,r in res))
ch=json.load(open(sys.argv[3]))
w=[c for c in ch if 'lr400_16_1' in (c['q'],c['r'])]; o=[c for c in ch if 'lr400_16_1' not in (c['q'],c['r'])]
print('chords with lr400_16_1:',len(w),'lo range',min(c['lo'] for c in w),max(c['lo'] for c in w),'| without:',len(o),'min lo',min((c['lo'],c['q'],c['r']) for c in o))
print('interior full-sample w:',sum(0<c['w']<1 for c in ch),' w==0:',sum(c['w']==0 for c in ch),' w==1:',sum(c['w']==1 for c in ch))
print('min lo among interior-w chords',min((c['lo'],c['q'],c['r'],c['w']) for c in ch if 0<c['w']<1))
