import json, collections
ROWS='/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
cnt=collections.Counter()
first={}
for i,line in enumerate(open(ROWS)):
    r=json.loads(line)
    cnt[r['name']]+=1
    if r['name'] in ('S|nc','S|p333','S|v3w','TRUCK|nc') and r['name'] not in first: first[r['name']]=r
for k in sorted(cnt): print(k,cnt[k])
r=first['S|p333']
def show(v,ind=0,depth=0):
    for k,x in sorted(v.items()):
        if isinstance(x,dict) and depth<2:
            print(' '*ind+k, 'dict', len(x)); show(x,ind+2,depth+1)
        else:
            s=json.dumps(x); print(' '*ind+k, type(x).__name__, (len(x) if hasattr(x,'__len__') else ''), s[:160])
show(r)
print(set(first['S|v3w'])-set(r), set(r)-set(first['S|v3w']), set(first['S|nc'])^set(r))
