import json,os,sys
import numpy as np
sys.path.insert(0,'/home/catalin/work/phd/p1_frozen_85f7d34')
from v5b.p1.stats import paired, LEVEL_95, LEVEL_S1
R='/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
res=json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
A=res['tune']['arms']
S=list(range(7400500,7400600))
_c={}
def D(k):
    if k not in _c:
        _c[k]=json.load(open(R+k+'.json'))['delay_s']
    return _c[k]
def arr(fmt): return np.array([D(fmt.format(s=s)) for s in S])
def pr(lbl,st): print(lbl,'rel%',round(st['rel']*100,1),[round(x*100,1) for x in st['rel_ci']],'diff',round(st['diff'],1),[round(x,1) for x in st['diff_ci']],'lvl',round(st['level'],5))
cells=[('slow',1600),('slow',2000),('block',1600),('block',2000)]
for typ,q in cells:
    a=A[str(q)]; N=a['N']
    ip=arr(f"{N}-{a['IP'][typ]}_{typ}_q{q}_s{{s}}")
    idd=arr(f"{N}-{a['ID']}_{typ}_q{q}_s{{s}}") if a['ID']!=N else arr(f"{N}_{typ}_q{q}_s{{s}}")
    for arm in ('FB','PI'):
        ref=arr(f"{a[arm]}_{typ}_q{q}_s{{s}}")
        pr(f'{typ}_q{q} IP vs {arm} 95',paired(ref,ip,LEVEL_95))
    pr(f'{typ}_q{q} IP vs ID 95',paired(idd,ip,LEVEL_95))
    # IP_d30 vs ID
    try:
        ipd=arr(f"{N}-{a['IP'][typ]}_d30_{typ}_q{q}_s{{s}}")
        pr(f'{typ}_q{q} IP_d30 vs ID S1lvl',paired(idd,ipd,LEVEL_S1))
    except Exception as e: print('d30 missing',e)
# block_q1600 alternative ID f40_10
a=A['1600']
try:
    alt=arr("c2000-f40_10_block_q1600_s{s}"); ip=arr("c2000-f40_14_block_q1600_s{s}")
    pr('block_q1600 IP vs ID=f40_10 S1',paired(alt,ip,LEVEL_S1))
except Exception as e: print('alt missing',e)
t=res['tune']['tables']['1600']['median_incident_pooled']
items=sorted(t.items(),key=lambda kv:kv[1])[:6]
print('q1600 pooled tuning medians top', [(k,round(v,2)) for k,v in items])
t=res['tune']['tables']['2000']['median_incident_pooled']
print('q2000 pooled tuning medians top', [(k,round(v,2)) for k,v in sorted(t.items(),key=lambda kv:kv[1])[:6]])
# clean day
for q in (1600,2000):
    pc=res['eval']['per_q'][str(q)]['controllers']
    n=arr(f"{pc['N']}_none_q{q}_s{{s}}")
    print(q,'N clean median',round(np.median(n),1),'seeds > 2x median',int((n>2*np.median(n)).sum()))
    for arm in ('FX','FB','PI','AD','NC'):
        x=arr(f"{pc[arm]}_none_q{q}_s{{s}}")
        pr(f' clean {q} {arm}-N median (as N vs arm)',paired(x,n,LEVEL_95))
        pr(f' clean {q} {arm}-N mean',paired(x,n,LEVEL_95,mean=True))
