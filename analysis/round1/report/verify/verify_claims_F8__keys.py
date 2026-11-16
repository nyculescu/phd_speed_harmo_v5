import json, sys, collections
p = sys.argv[1]
n = 0; keys = collections.Counter(); bad = 0
for line in open(p):
    line = line.strip()
    if not line: continue
    try: r = json.loads(line)
    except Exception: bad += 1; continue
    n += 1
    keys.update(r.keys())
print(p.split('/')[-1], 'rows', n, 'bad', bad)
print(sorted(keys.items())[:80])
