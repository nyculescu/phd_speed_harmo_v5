import json
J=json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
def show(o,d=0,k='',maxd=2):
    if isinstance(o,dict):
        print(' '*d+str(k),'{dict',len(o),'}', list(o)[:40] if d>=maxd*2 else '')
        if d<maxd*2:
            for kk,v in list(o.items())[:60]: show(v,d+2,kk,maxd)
    elif isinstance(o,list):
        print(' '*d+str(k),'[list',len(o),']',json.dumps(o)[:200])
    else: print(' '*d+str(k),repr(o)[:200])
show(J,0,'top',1)
c=J['cells']['TRUCK']
show(c,0,'TRUCK',1)
show(J['S'],0,'S',2)
