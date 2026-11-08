# Rebuild the "random" slowdown draw from the seed and compare with logged pert_log; X1/X2 spec from job_test.
import json
from collections import Counter
import numpy as np
M = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/'

def draw(seed):
    r = np.random.default_rng(seed + 910_000)
    if r.random() >= 1.0 / 3.0:
        return dict(edge=str(r.choice(("3", "4", "5"))), lim=float(r.uniform(25.0, 60.0)), dur=float(r.uniform(60.0, 180.0)), t0=float(r.uniform(400.0, 1200.0)))
    return None

for tag in ['band', 's1']:
    R = [json.loads(l) for l in open(M + f'rows_{tag}.jsonl') if l.strip()]
    logs = {}
    for r in R:
        logs[r['seed']] = r.get('pert_log')
    ex = next(v for v in logs.values() if v)
    print(tag, 'pert_log example structure:', type(ex).__name__, len(ex), [type(e).__name__ for e in ex][:4], ex[:4])
    ok = 0; res = Counter()
    for s, lg in sorted(logs.items()):
        d = draw(s)
        if d is None:
            res['none'] += 1
            ok += (not lg)
            continue
        res['edge' + d['edge']] += 1
        # compare first and last logged times with t0 and t0+dur (+taper)
        ts = [e[0] if isinstance(e, (list, tuple)) else e.get('t') for e in lg] if lg else []
        good = bool(ts) and abs(min(ts) - d['t0']) <= 1.0
        ok += good
        if not good:
            print('  seed', s, 'draw', d, 'log', lg[:3])
    print(tag, 'seeds', len(logs), 'draw matches log start (<=1 s) or both none:', ok, dict(res))
j = json.load(open(M + 'job_test.json'))['arms']
for c in ('X1', 'X2'):
    specs = Counter(json.dumps(v['ctrl'].get('env', {}).get('perturb'), sort_keys=True) for k, v in j.items() if k.startswith(c + '|'))
    print(c, dict(specs))
