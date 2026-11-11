import gzip, json, sys, collections
R='/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/'
def rows(p):
    op = gzip.open if p.endswith('.gz') else open
    with op(p,'rt') as f:
        for l in f:
            l=l.strip()
            if l: yield json.loads(l)
def show(p, n=1):
    rs=list(rows(R+p))
    print('==',p,len(rs))
    r=rs[0]
    def short(v):
        s=json.dumps(v,sort_keys=True)
        return s if len(s)<160 else s[:160]+'...'
    small={k:short(v) for k,v in sorted(r.items()) if not isinstance(v,(int,float)) or k in('seed','q','hold')}
    print(' nonnumeric keys:',small)
    print(' numeric keys:',sorted(k for k,v in r.items() if isinstance(v,(int,float)))[:80])
    return rs
for p in sys.argv[1:]:
    show(p)
