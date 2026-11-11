import gzip, json, sys, collections
R='/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/'
def rows(p):
    op = gzip.open if p.endswith('.gz') else open
    with op(p,'rt') as f:
        for l in f:
            l=l.strip()
            if l: yield json.loads(l)
for p in sys.argv[1:]:
    rs=list(rows(p if p.startswith('/') else R+p))
    print('==',p,len(rs))
    seen={}
    for r in rs:
        n=r.get('name')
        if n in seen: continue
        seen[n]=1
        d={k:v for k,v in sorted(r.items()) if isinstance(v,(str,dict,bool)) or k in('hold','clock','every')}
        s=json.dumps(d,sort_keys=True)
        print('  ',n,'|',s[:420])
    cf=collections.Counter(json.dumps(r.get('cfg'),sort_keys=True) for r in rs)
    print('  cfg tally:',dict(cf))
    print('  seeds:',min(r['seed'] for r in rs),max(r['seed'] for r in rs),'q:',sorted(set(r.get('q') for r in rs)))
