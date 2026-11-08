# Missing / None / NaN in summary_rows_*.json per metric path and arm group.
import json, math, re
from collections import Counter, defaultdict
M = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/'

def group(arm):
    if re.fullmatch(r'w[0-4]u\d+', arm): return 'v3w'
    if re.fullmatch(r't[0-4]', arm): return 'tail'
    if re.fullmatch(r's[0-4]u\d+', arm): return 'sw'
    if re.fullmatch(r'd[0-4]u\d+', arm): return 'd'
    return arm

def flat(x, p, out):
    if isinstance(x, dict):
        if not x:
            out.append((p, 'emptydict'))
        for k, v in x.items():
            flat(v, p + '.' + k if p else k, out)
    elif isinstance(x, list):
        if not x:
            out.append((p, 'emptylist'))
        for v in x:
            flat(v, p + '[]', out)
    elif x is None:
        out.append((p, 'None'))
    elif isinstance(x, float) and not math.isfinite(x):
        out.append((p, 'nonfinite'))
    else:
        out.append((p, 'ok'))

for tag in ['test', 'band', 's1']:
    S = json.load(open(M + f'summary_rows_{tag}.json'))
    rows = [json.loads(l) for l in open(M + f'rows_{tag}.jsonl')]
    rk = {(r['name'], float(r['q'])): set() for r in rows}
    for r in rows:
        rk[(r['name'], float(r['q']))].add(str(r['seed']))
    n_entries = sum(len(v) for v in S.values())
    # map keys
    miss = 0; extra = 0
    for (n, q), seeds in rk.items():
        key = f'{n}|{q:g}' if f'{n}|{q:g}' in S else (f'{n}|{q}' if f'{n}|{q}' in S else f'{n}|{q:.0f}')
        got = set(S.get(key, {}))
        miss += len(seeds - got); extra += len(got - seeds)
    print(f'[{tag}] summary groups {len(S)} entries {n_entries} rows {len(rows)} missing-for-row {miss} extra {extra}; sample key {next(iter(S))}')
    cnt = defaultdict(Counter)   # path -> status counts
    by_arm = defaultdict(Counter)   # (path,status,group) for bad
    present = defaultdict(Counter)  # top-level metric presence per group
    ngroup = Counter()
    for key, d in S.items():
        arm = key.split('|')[1]
        g = group(arm)
        for seed, e in d.items():
            ngroup[g] += 1
            for k in e:
                present[g][k] += 1
            out = []
            flat(e, '', out)
            for p, st in out:
                cnt[p][st] += 1
                if st in ('None', 'nonfinite'):
                    by_arm[(p, st)][g] += 1
    nonfin = sum(c['nonfinite'] for c in cnt.values())
    nones = sum(c['None'] for c in cnt.values())
    print(f'[{tag}] total None {nones}, non-finite {nonfin}')
    for (p, st), c in sorted(by_arm.items()):
        print(f'   {st:9s} {p:40s} {dict(c)}')
    # top-level keys missing in some entries, per group
    allk = set(k for g in present for k in present[g])
    for k in sorted(allk):
        lack = {g: ngroup[g] - present[g][k] for g in ngroup if present[g][k] < ngroup[g]}
        if lack:
            print(f'   key {k} absent in: {lack}')
    # emptiness
    emp = {p: c['emptylist'] + c['emptydict'] for p, c in cnt.items() if c['emptylist'] + c['emptydict']}
    print(f'[{tag}] empty containers: {emp}')
