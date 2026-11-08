# Job configs vs round 2; S1 grid, seeds, health; seed overlap.
import json, glob, os, re
from collections import Counter, defaultdict
import numpy as np
D = '/home/catalin/work/phd/v5b1_runs/'
M = D + 'measure_s01_remote/'

def rows(p):
    with open(p) as fh:
        return [json.loads(l) for l in fh if l.strip()]

def strip(c):
    c = dict(c); c.pop('measure', None); return c

print('== (5) job configs ==')
for tag, new, old in [('test', 'job_test.json', 'round2/test/job_6c49e7e.json'), ('band', 'job_band.json', 'round2/band/job_6c49e7e.json')]:
    jn = json.load(open(M + new)); jo = json.load(open(D + old))
    an, ao = jn['arms'], jo['arms']
    diff = [k for k in set(an) & set(ao) if strip(an[k]) != ao[k]]
    meas_vals = Counter(json.dumps(an[k].get('measure')) for k in an)
    meas_in_old = sum('measure' in ao[k] for k in ao)
    print(tag, 'arms new', len(an), 'old', len(ao), 'only new', sorted(set(an) - set(ao)), 'only old', sorted(set(ao) - set(an)),
          'cfg diffs', len(diff), 'levels equal', jn['levels'] == jo['levels'], 'seeds equal', jn['seeds'] == jo['seeds'],
          'seed range', min(jn['seeds']), max(jn['seeds']), len(jn['seeds']), 'measure values', dict(meas_vals), 'measure in old', meas_in_old)
    print('   top-level keys new', sorted(jn), 'old', sorted(jo))
    # row cfg = job cfg
    R = rows(M + ('rows_%s.jsonl' % tag))
    bad = sum(1 for r in R if r['cfg'] != an[r['name']])
    print('   rows whose cfg != job cfg:', bad, 'of', len(R))

print('== (2) S1 ==')
js1 = json.load(open(M + 'job_s1.json'))
S1 = rows(M + 'rows_s1.jsonl')
keys = Counter((r['name'], float(r['q']), int(r['seed'])) for r in S1)
names = sorted({k[0] for k in keys}); qs = sorted({k[1] for k in keys}); seeds = sorted({k[2] for k in keys})
print('rows', len(S1), 'distinct keys', len(keys), 'dups', sum(c - 1 for c in keys.values() if c > 1))
print('names', names)
print('levels', qs, 'seeds', seeds[0], seeds[-1], len(seeds), 'contiguous', seeds == list(range(7440900, 7440920)))
full = {(n, q, s) for n in names for q in qs for s in seeds}
print('missing grid cells', len(full - set(keys)), 'extra', len(set(keys) - full))
print('job_s1 arms', sorted(js1['arms']), 'levels', js1['levels'], 'seeds', js1['seeds'][0], js1['seeds'][-1], len(js1['seeds']))
print('rows cfg == job cfg:', sum(r['cfg'] == js1['arms'][r['name']] for r in S1), '/', len(S1))
jb = json.load(open(D + 'round2/band/job_6c49e7e.json'))['arms']
print('S1 arm cfg == round2 band cfg (measure stripped):', {k: (strip(v) == jb.get(k)) for k, v in js1['arms'].items()})
T = rows(M + 'rows_test.jsonl'); B = rows(M + 'rows_band.jsonl')
st_seeds = {r['seed'] for r in T}; sb_seeds = {r['seed'] for r in B}
print('test seeds', min(st_seeds), max(st_seeds), len(st_seeds), '| band seeds', min(sb_seeds), max(sb_seeds), len(sb_seeds))
print('S1 seeds in test', len(set(seeds) & st_seeds), 'in band', len(set(seeds) & sb_seeds))
# health per arm/level
print('health per (name,q): n, collisions, teleports, contact_steps, steps set, finished_pct min/med/max, passed med, all_delay med')
agg = defaultdict(list)
for r in S1:
    agg[(r['name'], r['q'])].append(r)
for k in sorted(agg, key=lambda t: (t[1], t[0])):
    L = agg[k]
    fp = np.array([r['finished_pct'] for r in L])
    print(f"  {k[0]:14s} {k[1]:6.0f} n={len(L)} coll={sum(r.get('collisions',0) for r in L)} tele={sum(r.get('teleports',0) for r in L)} "
          f"contact={sum(r.get('contact_steps',0) for r in L)} steps={sorted({r.get('steps') for r in L})} fin={fp.min():.1f}/{np.median(fp):.1f}/{fp.max():.1f} "
          f"passed_med={np.median([r['passed'] for r in L]):.0f} delay_med={np.median([r['all_delay'] for r in L]):.0f} arrived_med={np.median([r['arrived'] for r in L]):.0f}")
# test/band health
for tag, R in [('test', T), ('band', B)]:
    coll = [(r['name'], r['q'], r['seed'], r['collisions']) for r in R if r.get('collisions', 0)]
    print(tag, 'collisions', sum(c[3] for c in coll), coll, 'teleports', sum(r.get('teleports', 0) for r in R),
          'contact_steps', sum(r.get('contact_steps', 0) for r in R), 'finished_pct min', min(r['finished_pct'] for r in R),
          'steps', sorted({r.get('steps') for r in R}))
# NaN / non-finite in numeric row fields
for tag, R in [('test', T), ('band', B), ('s1', S1)]:
    nan = Counter()
    for r in R:
        for k, v in r.items():
            if isinstance(v, float) and not np.isfinite(v):
                nan[k] += 1
    print(tag, 'non-finite scalar row fields', dict(nan))
