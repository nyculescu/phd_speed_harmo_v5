# Independent recompute of D, E, braking from the protocol text (c1_confirm.md §1, c1_screen.md C-D5).
import pickle, sys, json, numpy as np
d=pickle.load(open(sys.argv[1],'rb')); rows=d['rows']
seed0=int(sys.argv[2]); out=sys.argv[3]
L=['w0u250','w1u500','w2u250','w3u500','w4u500']
arms=sorted(set(r['arm'] for r in rows)); R=[a for a in arms if a not in L]
seeds=list(range(7489160,7489640)); si={s:i for i,s in enumerate(seeds)}; n=len(seeds)
M=['all_delay','ttc_net','b45_step']
val={m:{a:np.full(n,np.nan) for a in arms} for m in M}
for r in rows:
    for m in M: val[m][r['arm']][si[r['seed']]]=r[m]
assert not any(np.isnan(val[m][a]).any() for m in M for a in arms)
P=np.array([[val[m][l] for l in L] for m in M]) # (3,5,n)
Q=np.array([[val[m][a] for a in R] for m in M]) # (3,26,n)
X=Q[:,:,None,:]-P[:,None,:,:] # (3,26,5,n) rule minus learner
B=20000; rng=np.random.default_rng(seed0)
raw=np.empty((3,26,5,B)); medR=np.empty((3,26,B)); medP=np.empty((3,5,B))
Xf=X.reshape(-1,n); Qf=Q.reshape(-1,n); Pf=P.reshape(-1,n)
c=200; IDX=np.empty((B,n),np.int16)
for b0 in range(0,B,c):
    idx=rng.integers(0,n,size=(c,n)); IDX[b0:b0+c]=idx
    raw.reshape(-1,B)[:,b0:b0+c]=np.median(Xf[:,idx],axis=-1)
    medR.reshape(-1,B)[:,b0:b0+c]=np.median(Qf[:,idx],axis=-1)
    medP.reshape(-1,B)[:,b0:b0+c]=np.median(Pf[:,idx],axis=-1)
np.savez_compressed(out,raw=raw,medR=medR,medP=medP,IDX=IDX,P=P,Q=Q,R=np.array(R),L=np.array(L),M=np.array(M))
