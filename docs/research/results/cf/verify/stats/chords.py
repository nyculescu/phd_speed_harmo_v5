# Independent chord recompute from c1_confirm.md §1.
import json, sys, numpy as np, itertools, multiprocessing as mp
z=np.load(sys.argv[1]); out=sys.argv[2]
R=list(z['R']); P=z['P']; Q=z['Q']; raw=z['raw']; IDX=z['IDX'].astype(np.int64); B=IDX.shape[0]; n=480
den=np.median(Q,axis=-1)
Dbs=raw[0].mean(1)/den[0][:,None]*100; Dlo,Dhi=np.percentile(Dbs,[1.25,98.75],axis=-1)
A=[i for i in range(26) if Dlo[i]<0]; Bs=[i for i in range(26) if Dhi[i]>0]
pairs=[]
seen=set()
for q in A:
    for r in Bs:
        if q==r: continue
        k=frozenset((q,r))
        if k in seen: continue
        seen.add(k); pairs.append((q,r))
X=Q[:,:,None,:]-P[:,None,:,:]
mfull=np.median(X[0],axis=-1).mean(-1)  # (26,) mean_l median(rule - P) on delay
mbs=raw[0].mean(1)                      # (26,B)
def wfun(mq,mr):
    s=mq+mr
    with np.errstate(divide='ignore',invalid='ignore'): w=np.where(s==0,0.5,mq/np.where(s==0,1,s))
    return np.clip(w,0,1)
def one(pr):
    q,r=pr
    wf=float(wfun(np.array(-mfull[q]),np.array(mfull[r])))
    w=wfun(-mbs[q],mbs[r])
    tq,tr=Q[1,q],Q[1,r]; Pt=P[1]
    cM=lambda w_: (1-w_)*den[1,q]+w_*den[1,r]
    Mf=(1-wf)*tq+wf*tr
    pt=np.median(Mf[None]-Pt,axis=-1).mean()/cM(wf)*100
    bs=np.empty(B)
    for b0 in range(0,B,500):
        idx=IDX[b0:b0+500]; wb=w[b0:b0+500,None]
        T=(1-wb)*tq[idx]+wb*tr[idx]
        bs[b0:b0+500]=np.median(T[None]-Pt[:,idx],axis=-1).mean(0)/cM(w[b0:b0+500])*100
    lo,hi=np.percentile(bs,[1.25,98.75]); wl,wh=np.percentile(w,[1.25,98.75])
    return dict(q=R[q],r=R[r],pt=pt,lo=lo,hi=hi,se=bs.std(ddof=1),w=wf,w_ci=[wl,wh],share_w0=float((w==0).mean()),share_w1=float((w==1).mean()))
if __name__=='__main__':
    print('A (lo<0):',[R[i] for i in A]); print('B (hi>0):',len(Bs)); print('pairs',len(pairs))
    with mp.Pool(6) as p: res=p.map(one,pairs,chunksize=4)
    json.dump(res,open(out,'w'))
