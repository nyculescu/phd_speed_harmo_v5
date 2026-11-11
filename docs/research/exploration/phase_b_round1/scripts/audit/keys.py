import json,sys
d=json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
def show(o,p='',depth=0,maxd=3):
    if isinstance(o,dict):
        ks=sorted(o.keys())
        if depth>=maxd or len(ks)>40:
            print(p,'dict',len(ks),ks[:30]);return
        for k in ks: show(o[k],p+'/'+str(k),depth+1,maxd)
    elif isinstance(o,list):
        print(p,'list',len(o), (type(o[0]).__name__ if o else ''), (sorted(o[0].keys())[:20] if o and isinstance(o[0],dict) else (o[:6] if len(o)<=6 else '')))
    else:
        s=repr(o); print(p,s[:100])
show(d)
