# Swap null from the protocol text: one sign per learner and seed on the per-seed edge; nb resamples per swap.
import json, sys, numpy as np, multiprocessing as mp
z=np.load(sys.argv[1]); R=list(z['R']); P=z['P']; Q=z['Q']; n=480
den=np.median(Q,axis=-1); X=Q[:,:,None,:]-P[:,None,:,:]
mfull=np.median(X[0],axis=-1).mean(-1)
def edge_rule(r,m=1):
    i=R.index(r); return X[m,i]/den[m,i]*100       # (5,n)
def edge_chord(q,r):
    a,b=R.index(q),R.index(r); mq,mr=-mfull[a],mfull[b]; s=mq+mr
    w=0.5 if s==0 else min(1,max(0,mq/s))
    M=(1-w)*Q[1,a]+w*Q[1,b]; c=(1-w)*den[1,a]+w*den[1,b]
    return (M[None]-P[1])/c*100
def null(args):
    name,e,swaps,nb,seed=args
    rng=np.random.default_rng(seed); lo_pos=hi_neg=0; los=[]
    for s in range(swaps):
        y=e*rng.choice([-1.0,1.0],size=e.shape)
        idx=rng.integers(0,n,size=(nb,n))
        st=np.median(y[:,idx],axis=-1).mean(0)
        lo,hi=np.percentile(st,[1.25,98.75]); lo_pos+=lo>0; hi_neg+=hi<0
    return name,swaps,nb,lo_pos/swaps,hi_neg/swaps,(lo_pos+hi_neg)/2/swaps
if __name__=='__main__':
    jobs=[('E lr400_16_1',edge_rule('lr400_16_1'),2000,1000,11),
          ('chord lr400_16_1~nc',edge_chord('lr400_16_1','nc'),2000,1000,12),
          ('chord 3E-D_TRUCK~lr400_16_1',edge_chord('3E-D_TRUCK','lr400_16_1'),2000,1000,13),
          ('E lr400_16_1 seed2',edge_rule('lr400_16_1'),2000,1000,21),
          ('brake lr400_16_1',edge_rule('lr400_16_1',2),2000,1000,14),
          ('brake 3ex2',edge_rule('3ex2',2),2000,1000,15)]
    with mp.Pool(6) as p:
        for r in p.imap(null,jobs): print(r,flush=True)
