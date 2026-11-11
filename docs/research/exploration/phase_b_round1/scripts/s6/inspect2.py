import json, collections
ROWS='/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
allk=collections.Counter(); types={}
ex=None
for line in open(ROWS):
    r=json.loads(line)
    for k,v in r.items():
        allk[k]+=1; types.setdefault(k,type(v).__name__)
    if r['name']=='TRUCK|w0u250' and ex is None: ex=r
print(len(allk))
for k in sorted(allk):
    v=ex.get(k)
    s=json.dumps(v)
    print(k, allk[k], types[k], (s[:90] if s else ''), ('len=%d'%len(v) if isinstance(v,(list,dict)) else ''))
