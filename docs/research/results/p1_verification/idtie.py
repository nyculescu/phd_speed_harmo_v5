import json,os,re,statistics as st
from collections import defaultdict
R='/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
for q,N in ((1600,'c2000'),(2000,'c1800')):
    pool=defaultdict(list)
    pat=re.compile(rf'^{N}-(.+)_(slow|block)_q{q}_s74002([0-3]\d)\.json$')
    for f in os.listdir(R):
        m=pat.match(f)
        if m and '_d' not in m.group(1) and '_c' not in m.group(1):
            pool[m.group(1)].append(json.load(open(R+f))['delay_s'])
    med=sorted(((st.median(v),k,len(v)) for k,v in pool.items() if len(v)==80))
    print(q,[(k,round(m,2),n) for m,k,n in med[:5]], 'n actions',len(med))
