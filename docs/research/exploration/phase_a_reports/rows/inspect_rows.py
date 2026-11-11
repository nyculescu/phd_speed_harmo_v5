import json, collections
ROWS='/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
cnt=collections.Counter(); seeds=collections.defaultdict(set)
first=None
for i,line in enumerate(open(ROWS)):
    r=json.loads(line)
    if first is None: first=r
    cnt[r['name']]+=1; seeds[r['name']].add(r['seed'])
for k in sorted(cnt): print(k,cnt[k],min(seeds[k]),max(seeds[k]))
print(len(cnt))
for k,v in sorted(first.items()):
    s=json.dumps(v)
    print(k, type(v).__name__, s[:110])
