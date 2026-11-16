import json, sys, pickle, numpy as np
z=np.load(sys.argv[1]); R=list(z['R']); L=list(z['L']); P=z['P']; Q=z['Q']; raw=z['raw']; IDX=z['IDX'].astype(np.int64); n=480; B=IDX.shape[0]
den=np.median(Q,axis=-1)
def pc(b,p=(1.25,98.75)): return np.percentile(b,p)
print('== per-learner E (ttc_net), own 97.5 % interval, share of seeds with fewer / equal / more ttc_net than the rule')
for r in ['lr400_16_1','p333','3ex2','3E-C_TRUCK','nc']:
    i=R.index(r); print(r,'median(R)=',den[1,i])
    for li,l in enumerate(L):
        d=(Q[1,i]-P[1,li]); pt=np.median(d)/den[1,i]*100; bs=raw[1,i,li]/den[1,i]*100; lo,hi=pc(bs)
        print(f"   {l}: E {pt:+6.2f} [{lo:+6.2f},{hi:+6.2f}]  fewer {np.mean(d>0):.3f} equal {np.mean(d==0):.3f} more {np.mean(d<0):.3f}  median(P_l)={np.median(P[1,li]):.1f} mean(P_l)={P[1,li].mean():.1f} mean(R)={Q[1,i].mean():.1f}")
    bs=raw[1,i].mean(0)/den[1,i]*100; print('   mean of five:',np.median(Q[1,i][None]-P[1],axis=-1).mean()/den[1,i]*100, pc(bs))
print('\n== alternative contrasts vs each competitor/near rule on ttc_net (all with joint seed bootstrap, same IDX, B=%d)'%B)
Pb=P[1].mean(0)  # pooled arm: per-seed mean of learners
def boot(f):
    out=np.empty(B)
    for b0 in range(0,B,1000): out[b0:b0+1000]=f(IDX[b0:b0+1000])
    return out
rows=[]
for r in R:
    i=R.index(r); q=Q[1,i]
    # (a) pooled arm median paired diff
    a_pt=np.median(q-Pb)/den[1,i]*100; a_bs=boot(lambda idx: np.median((q-Pb)[idx],axis=-1))/den[1,i]*100
    # (b) mean paired difference over mean(R), learners averaged
    b_pt=(q-Pb).mean()/q.mean()*100; b_bs=boot(lambda idx: (q-Pb)[idx].mean(-1)/q[idx].mean(-1))*100
    # (c) difference of medians: mean_l (med R - med P_l)/med R, medians recomputed per resample
    c_pt=np.mean((den[1,i]-np.median(P[1],axis=-1))/den[1,i])*100; c_bs=((z['medR'][1,i][None]-z['medP'][1])/z['medR'][1,i][None]).mean(0)*100
    rows.append((r,a_pt,pc(a_bs),b_pt,pc(b_bs),c_pt,pc(c_bs)))
print(f"{'rule':18s} | pooled-median paired | mean paired diff / mean(R) | diff of medians")
for r,a,ac,b,bc,c,cc in sorted(rows,key=lambda t:t[1]):
    print(f"{r:18s} | {a:+6.2f} [{ac[0]:+6.2f},{ac[1]:+6.2f}] | {b:+6.2f} [{bc[0]:+6.2f},{bc[1]:+6.2f}] | {c:+6.2f} [{cc[0]:+6.2f},{cc[1]:+6.2f}]")
print('\n== split halves, E(lr400_16_1) mean-of-five point')
i=R.index('lr400_16_1')
for nm,sl in [('first 240',slice(0,240)),('last 240',slice(240,480)),('even idx',slice(0,480,2)),('odd idx',slice(1,480,2))]:
    q=Q[1,i][sl]; print('  ',nm, np.mean([np.median(q-P[1,l][sl]) for l in range(5)])/np.median(q)*100)
print('\n== served vehicles and TTT: medians and paired median diffs vs v3w learners')
d=pickle.load(open(sys.argv[2],'rb'))['rows']
seeds=list(range(7489160,7489640)); si={s:k for k,s in enumerate(seeds)}
def arr(arm,key):
    a=np.full(n,np.nan)
    for r_ in d:
        if r_['arm']==arm: a[si[r_['seed']]]=r_[key]
    return a
for key in ['passed','arrived','N','all_delay','ttc_net','b45_step']:
    pl=np.array([arr(l,key) for l in L])
    s=f"{key:9s} v3w learner medians {np.round(np.median(pl,axis=-1),1)} pooled median {np.median(pl.mean(0)):.1f}"
    for r in ['lr400_16_1','p333','3ex2','3E-C_TRUCK','nc']:
        q=arr(r,key); s+=f" | {r} med {np.median(q):.1f} mean-of-5 median(P-R) {np.mean([np.median(p-q) for p in pl]):+.1f}"
    print(s)
