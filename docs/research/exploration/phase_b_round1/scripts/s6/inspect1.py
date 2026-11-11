import json, collections
ROWS='/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
names=collections.Counter(); keysets=collections.Counter()
ex={}
for line in open(ROWS):
    r=json.loads(line)
    names[r['name']]+=1
    keysets[tuple(sorted(r))]+=1
    if r['name'] in ('TRUCK|v3w_C0','TRUCK|p333','TRUCK|nc') and r['name'] not in ex: ex[r['name']]=r
print(len(names)); print(sorted(names))
print(len(keysets))
for ks,c in keysets.items(): print(c,len(ks))
def show(o,d=0,k=''):
    if isinstance(o,dict):
        print(' '*d+str(k),'{dict',len(o),'}')
        if d<6:
            for kk,v in list(o.items())[:60]: show(v,d+2,kk)
    elif isinstance(o,list):
        print(' '*d+str(k),'[list',len(o),']',json.dumps(o)[:140])
    else: print(' '*d+str(k),repr(o)[:140])
show(ex['TRUCK|v3w_C0'],0,'v3w_C0')
