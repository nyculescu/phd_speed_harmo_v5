import json,sys
import numpy as np
sys.path.insert(0,'/home/catalin/work/phd/p1_frozen_85f7d34')
from v5b.p1.stats import paired, LEVEL_95, prevalence_mix
R='/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
res=json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
A=res['tune']['arms']; S=range(7400500,7400600)
def arr(f): return np.array([json.load(open(R+f.format(s=s)+'.json'))['delay_s'] for s in S])
for q in (1600,2000):
    a=A[str(q)]; N=a['N']
    ipS=arr(f"{N}-{a['IP']['slow']}_slow_q{q}_s{{s}}"); ipB=arr(f"{N}-{a['IP']['block']}_block_q{q}_s{{s}}")
    Nc=arr(f"{N}_none_q{q}_s{{s}}")
    for pi,p in a['prev'].items():
        g=p['PI']
        L=prevalence_mix(arr(f"{g}_slow_q{q}_s{{s}}"),arr(f"{g}_block_q{q}_s{{s}}"),arr(f"{g}_none_q{q}_s{{s}}"),float(pi))
        T=prevalence_mix(ipS,ipB,Nc,float(pi))
        st=paired(L,T,LEVEL_95,mean=True)
        print(q,pi,g,'IP vs PI_pi mean diff',round(st['diff'],1),[round(x,1) for x in st['diff_ci']],'rel',round(st['rel']*100,1))
for q in ('1600','2000'):
    ms=res['tune']['tables'][q]['median_switch']
    print(q,'median_switch keys',list(ms.keys()))
    for k,v in ms.items():
        if isinstance(v,dict):
            top=sorted(v.items(),key=lambda kv:kv[1])[:5]
            print('  ',k,[(a,round(b,2)) for a,b in top])
