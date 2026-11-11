"""EXPLORATORY: structure of the stored rows (counts only)."""
import json, pickle, collections
import numpy as np
T = pickle.load(open('/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/floor/comp.pkl', 'rb'))
print(sorted(T))
d = T[('S', 'nc')][7480400]
print(sorted(d['minute']), len(d['minute']['m2_out']), d['q'], d['pert'], len(d['flow_min']))
for f in ('rows_s1.jsonl', 'rows_band.jsonl'):
    c = collections.Counter(); seeds = collections.defaultdict(set); pert = collections.Counter()
    for line in open('/home/catalin/work/phd/v5b1_runs/measure_s01_remote/' + f):
        r = json.loads(line)
        c[(r['name'], r['q'])] += 1; seeds[r['q']].add(r['seed'])
        pert[(r['q'], str(r.get('pert_log'))[:60])] += 1
    print(f, len(c))
    names = sorted({k[0] for k in c}); qs = sorted({k[1] for k in c})
    print(' names', names[:40]); print(' q', qs)
    for q in qs:
        print('  q', q, 'seeds', len(seeds[q]), min(seeds[q]), max(seeds[q]), 'nc rows', sum(v for k, v in c.items() if k[1] == q and k[0].endswith('nc')), 'p333 rows', sum(v for k, v in c.items() if k[1] == q and k[0].endswith('p333')))
    print(' pert kinds', collections.Counter(k[1] for k in pert).most_common(6))
