import pickle, numpy as np, pandas as pd, json
T=pickle.load(open('rows.pkl','rb'))
arms=sorted({a for a,_ in T}); seeds=sorted({s for _,s in T})
col=lambda a,k: np.array([float(T[(a,s)].get(k,0) or 0) for s in seeds])
print('plant rate per vehicle-second (sum counts / sum vs), mean speeds')
for a in ('nc','lr400_16_1','w1u500','p333'):
    print(a,{g:round(col(a,'g_'+g).sum()/col(a,'vs_'+g).sum(),4) for g in ('3a','4a','3','ramp2')},'net',round(col(a,'net').sum()/col(a,'vs').sum(),4),
          {x:round(col(a,'nv_'+x).sum()/col(a,'n_'+x).sum(),2) for x in ('3a_1','3_0','4a_1')})
# C-D5 statistic: per learner median of paired % differences (median of opponent in denominator), mean of five; joint bootstrap
L=['w0u250','w1u500','w2u250','w3u500','w4u500']
rng=np.random.default_rng(4242)
def cd5(opp,f,B=5000,lev=97.5):
    R=f(opp); Pl=np.array([f(l) for l in L])
    def stat(idx):
        r=R[idx]; return np.mean([np.median(-(p[idx]-r))/np.median(r)*100 for p in Pl])
    pt=stat(np.arange(len(R)))
    bs=[stat(rng.integers(0,len(R),len(R))) for _ in range(B)]
    lo,hi=np.percentile(bs,[(100-lev)/2,100-(100-lev)/2]); return round(pt,1),round(lo,1),round(hi,1)
F={'net':lambda a:col(a,'net'),'4a':lambda a:col(a,'g_4a'),'3a':lambda a:col(a,'g_3a'),
   'other':lambda a:col(a,'mall')-col(a,'g_3a')-col(a,'g_4a'),
   'other_no_edge1':lambda a:col(a,'mall')-col(a,'g_3a')-col(a,'g_4a')-col(a,'g_1'),
   'edge1':lambda a:col(a,'g_1'),
   'lc':lambda a:col(a,'lc'),'not_lc':lambda a:col(a,'mall')-col(a,'lc'),'hi':lambda a:col(a,'hi')}
for opp in ('lr400_16_1','grid_lr400_13_1'):
    print('C-D5 vs',opp,{k:cd5(opp,f) for k,f in F.items() if k!='edge1'})
print('edge-1 counted samples per run, medians:',{a:float(np.median(col(a,'g_1'))) for a in ['nc','lr400_16_1','grid_lr400_13_1','p333','p111','p222']+L})
# by period on 3a and 4a: where merge-1 samples fall
for a in ('nc','lr400_16_1','w1u500'):
    print(a,'3a by period (mean per run):',{p:round(col(a,f'gp_3a_{p}').mean(),1) for p in ('before','taper','hold','after','rest')},'4a:',{p:round(col(a,f'gp_4a_{p}').mean(),1) for p in ('before','taper','hold','after','rest')})
# gate arithmetic: required fall at merge 1 if merge 2 falls 91 % (nc at 595 m in S) for an 80 % total fall
for a in ('nc','lr400_16_1','grid_lr400_13_1','p333','w1u500'):
    e1,e2=np.median(col(a,'es1')),np.median(col(a,'es2')); print(a,'es1',e1,'es2',e2,'needed merge-1 fall if merge-2 falls 91%:',round((0.8*(e1+e2)-0.91*e2)/e1,2),' if 99%:',round((0.8*(e1+e2)-0.99*e2)/e1,2))
