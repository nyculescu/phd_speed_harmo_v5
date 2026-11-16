import json
J=json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
def show(o,d=0,k='',maxd=3):
    if isinstance(o,dict):
        print(' '*d+str(k),'{dict',len(o),'}', '' if d<maxd*2 else list(o)[:8])
        if d<maxd*2:
            for kk,v in list(o.items())[:45]: show(v,d+2,kk,maxd)
    elif isinstance(o,list):
        print(' '*d+str(k),'[list',len(o),']',json.dumps(o)[:160])
    else: print(' '*d+str(k),repr(o)[:160])
top={k:v for k,v in J.items() if k not in('cells','S')}
show(top,0,'top',2)
c=J['cells']['TRUCK']
for k,v in c.items():
    if isinstance(v,dict): print(k,'dict',list(v)[:30])
    else: print(k, json.dumps(v)[:200])
