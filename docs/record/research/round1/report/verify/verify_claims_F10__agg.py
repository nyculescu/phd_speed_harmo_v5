import json, sys, statistics as st
from collections import defaultdict
rows = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    cell, arm = r['name'].split('|', 1)
    rows[(cell, arm)][r['seed']] = r
def med(cell, arms, key):
    seeds = sorted(set.intersection(*[set(rows[(cell, a)]) for a in arms]))
    vals = [st.mean(rows[(cell, a)][s].get(key, 0) for a in arms) for s in seeds]
    return round(st.median(vals), 1), len(seeds)
print(sorted(set(a for c, a in rows)))
for cell in ('X1', 'X2'):
    for lab, arms in (('v3w', ['w0','w1','w2','w3','w4']), ('p333', ['p333']), ('os1_15_10', ['os1_15_10']), ('nc', ['nc'])):
        print(cell, lab, {k: med(cell, arms, k) for k in ('ttc2', 'ttc15', 'ttc_net')})
