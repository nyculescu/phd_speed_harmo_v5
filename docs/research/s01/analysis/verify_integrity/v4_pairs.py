# Identical-arm runs per seed; pert_log pairing across arms; p333 level shares.
import json, hashlib
from collections import defaultdict, Counter
import numpy as np
M = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/'

def rows(t):
    return [json.loads(l) for l in open(M + f'rows_{t}.jsonl') if l.strip()]

for tag in ['test', 'band', 's1']:
    R = rows(tag)
    h = {}
    pert = defaultdict(set)
    for r in R:
        core = {k: v for k, v in r.items() if k not in ('name', 'cfg') and not k.startswith('m_')}
        h[(r['name'], r['q'], r['seed'])] = hashlib.sha1(json.dumps(core, sort_keys=True).encode()).hexdigest()
        cell = r['name'].split('|')[0]
        pert[(cell, r['q'], r['seed'])].add(json.dumps(r.get('pert_log'), sort_keys=True))
    bad = sum(1 for v in pert.values() if len(v) > 1)
    print(f'[{tag}] pert_log groups {len(pert)}, groups with differing pert_log across arms {bad}')
    # identical pairs
    by = defaultdict(dict)
    for (n, q, s), d in h.items():
        cell, arm = n.split('|')
        by[(cell, q, s)][arm] = d
    pairs = Counter()
    tot = Counter()
    for (cell, q, s), am in by.items():
        inv = defaultdict(list)
        for a, d in am.items():
            inv[d].append(a)
        for d, al in inv.items():
            if len(al) > 1:
                pairs[(cell, q, tuple(sorted(al)))] += 1
        tot[(cell, q)] += 1
    for k, c in sorted(pairs.items()):
        print(f'   identical {k}: {c}/{tot[(k[0], k[1])]} seeds')
    # p333 level shares
    ls = [r['m_dec_level_s'] for r in R if r['name'].endswith('|p333')]
    if ls:
        A = np.array(ls, dtype=float)
        print(f'[{tag}] p333 m_dec_level_s shape {A.shape}; first row {A[0].tolist()}')
