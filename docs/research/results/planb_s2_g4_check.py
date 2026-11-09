import json
import numpy as np
rows = [json.loads(l) for l in open('/home/catalin/work/phd/v5b1_runs/planb_remote/s2/s2_runs.jsonl')]
T = {}
for r in sorted(rows, key=lambda r: r['seed']):
    T.setdefault(r['name'], []).append(r)
W = range(20, 25)
rq = lambda r, k: float(np.mean([r['m_minute'][k][i] / 60.0 for i in W]))
K = ('ramp1_queue', 'ramp2_queue')
print('--- G4(ii)(b): median queue (vehicles) over 1,500-1,800 s, cell vs S, limit 1.1 x S')
for c in ('SURGE', 'TRUCK', 'PLACEBO'):
    for a in ('nc', 'p333'):
        for k in K:
            C = np.array([rq(r, k) for r in T[f'{c}|{a}']]); S = np.array([rq(r, k) for r in T[f'S|{a}']])
            mc, ms = np.median(C), np.median(S)
            print(f'{c:8s}{a:5s}{k:12s} cell {mc:.4f} S {ms:.4f} pass {bool(mc <= 1.1 * ms)}  seeds>0 cell {int((C>0).sum())}/40 S {int((S>0).sum())}/40  mean cell {C.mean():.3f} S {S.mean():.3f}')
print('--- null: S rows only, random 20/20 splits, how often does the same test fail?')
rng = np.random.default_rng(20261108)
for a in ('nc', 'p333'):
    for k in K:
        S = np.array([rq(r, k) for r in T[f'S|{a}']])
        f = 0
        for _ in range(5000):
            p = rng.permutation(40)
            f += not (np.median(S[p[:20]]) <= 1.1 * np.median(S[p[20:]]))
        print(f'S {a:5s}{k:12s} failure rate of "A <= 1.1 x B" with no effect: {100 * f / 5000:.1f} %')
print('--- stuck rows (m_stuck_n > 0), every arm')
for n, v in sorted(T.items()):
    x = [(r['seed'], r['m_stuck_n']) for r in v if r['m_stuck_n'] > 0]
    if x:
        print(n, x)
print('total rows', len(rows))
print('--- candidate: median cell <= max(1.1 x S, S + 1 vehicle)')
ok = lambda x, y: x <= max(1.1 * y, y + 1.0)
for a in ('nc', 'p333'):
    for k in K:
        S = np.array([rq(r, k) for r in T[f'S|{a}']])
        f = sum(not ok(np.median(S[p[:20]]), np.median(S[p[20:]])) for p in (rng.permutation(40) for _ in range(5000)))
        print(f'null S {a:5s}{k:12s} failure {100 * f / 5000:.2f} %')
for c in ('SURGE', 'TRUCK', 'PLACEBO'):
    print(c, {f'{a} {k}': bool(ok(np.median([rq(r, k) for r in T[f'{c}|{a}']]), np.median([rq(r, k) for r in T[f'S|{a}']]))) for a in ('nc', 'p333') for k in K})
print('--- the old test on every gate component per cell, without the ramp-queue part')
s = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_remote/s2/s2.json'))
for c, v in s['cells'].items():
    G = v['G4']
    print(c, {a: {k: G[a][k] for k in ('pr09_pass', 'backlog_pass', 'stuck_pass')} for a in ('nc', 'p333')}, 'coll', G['collisions_pass'], 'pr24', G['pr24_pass'])
r = next(x for x in T['SURGE|p333'] if x['seed'] == 7480037)
print('stuck row SURGE|p333 7480037: all_delay', round(r['all_delay']), 'end_stop', r['end_stop'], 'end_stop2', r['end_stop2'], 'pending_end', r['m_pending_end'], 'ramp2_queue last 5 min', [round(x / 60, 1) for x in r['m_minute']['ramp2_queue'][20:25]])
med = np.median([x['end_stop2'] for x in T['SURGE|p333']]); print('median end_stop2 over 40 seeds', med)
