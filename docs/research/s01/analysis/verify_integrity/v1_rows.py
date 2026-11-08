# Independent comparison of S0 rows against round-2 stored rows by (name, q, seed).
import json, math, sys
from collections import Counter, defaultdict
D = '/home/catalin/work/phd/v5b1_runs/'
PAIRS = [('test', 'measure_s01_remote/rows_test.jsonl', 'round2/test/rows_6c49e7e.jsonl'),
         ('band', 'measure_s01_remote/rows_band.jsonl', 'round2/band/rows_6c49e7e.jsonl')]

def load(p):
    out = {}
    dup = 0
    n = 0
    with open(D + p) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            n += 1
            k = (r['name'], float(r['q']), int(r['seed']))
            if k in out:
                dup += 1
            out[k] = r
    return out, n, dup

def walk(a, b, path, res):
    # returns list of (path, kind, reldiff)
    if isinstance(a, dict) and isinstance(b, dict):
        ka, kb = set(a), set(b)
        for k in ka ^ kb:
            res.append((path + '.' + str(k), 'keyonly', None))
        for k in ka & kb:
            walk(a[k], b[k], path + '.' + str(k), res)
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            res.append((path, 'len', None))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, path + '[]', res)
        return
    if isinstance(a, bool) or isinstance(b, bool):
        if a is not b:
            res.append((path, 'bool', None))
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == b or (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b)):
            if type(a) is not type(b):
                res.append((path, 'type_only', 0.0))
            return
        den = max(abs(a), abs(b), 1e-300)
        res.append((path, 'num', abs(a - b) / den))
        return
    if a != b:
        res.append((path, 'other', None))

summary = {}
for tag, pn, po in PAIRS:
    new, nn, dn = load(pn)
    old, no, do = load(po)
    kn, ko = set(new), set(old)
    print(f'[{tag}] new lines {nn} keys {len(new)} dup {dn}; old lines {no} keys {len(old)} dup {do}')
    print(f'[{tag}] matched {len(kn & ko)} new-only {len(kn - ko)} old-only {len(ko - kn)}')
    field_cmp = 0
    exact_fields = 0
    tol_fields = 0
    mism = []
    keyonly = Counter()
    keyonly_nonzero = []
    type_only = Counter()
    rows_all_exact = 0
    fields_seen = set()
    cfg_diff = 0
    for k in sorted(kn & ko):
        a, b = new[k], old[k]
        ca = dict(a['cfg']); cb = dict(b['cfg'])
        ca.pop('measure', None)
        if ca != cb:
            cfg_diff += 1
        sa = {x for x in a if not x.startswith('m_') and x != 'cfg'}
        sb = {x for x in b if x != 'cfg'}
        row_ok = True
        for f in sa ^ sb:
            side = a if f in a else b
            v = side[f]
            keyonly[(f, 'new' if f in a else 'old')] += 1
            if v not in (0, 0.0, [], None):
                keyonly_nonzero.append((k, f, 'new' if f in a else 'old', v if isinstance(v, (int, float)) else type(v).__name__))
                row_ok = False
        for f in sa & sb:
            fields_seen.add(f)
            field_cmp += 1
            res = []
            walk(a[f], b[f], f, res)
            real = [r for r in res if r[1] != 'type_only']
            for r in res:
                if r[1] == 'type_only':
                    type_only[f] += 1
            if not real:
                exact_fields += 1
            elif all(r[1] == 'num' and r[2] <= 1e-9 for r in real):
                tol_fields += 1
                row_ok = False
            else:
                row_ok = False
                for r in real:
                    mism.append((k[0], k[1], k[2], r[0], r[1], r[2]))
        if row_ok:
            rows_all_exact += 1
    # also: m_ keys present in old rows?
    m_in_old = sum(1 for r in old.values() for x in r if x.startswith('m_'))
    print(f'[{tag}] field comparisons {field_cmp} exact {exact_fields} within1e-9-only {tol_fields} mismatching-fields {field_cmp-exact_fields-tol_fields}')
    print(f'[{tag}] distinct fields compared {len(fields_seen)}; rows fully exact {rows_all_exact}; cfg differ (measure stripped) {cfg_diff}')
    print(f'[{tag}] key present on one side only: {sum(keyonly.values())} occurrences, distinct {len(keyonly)}; nonzero ones {len(keyonly_nonzero)}')
    for (f, s), c in sorted(keyonly.items(), key=lambda t: -t[1])[:30]:
        print('   keyonly', f, s, c)
    print(f'[{tag}] int/float type-only differences: {dict(type_only)}')
    print(f'[{tag}] m_* keys in old rows: {m_in_old}')
    print(f'[{tag}] mismatches listed: {len(mism)}')
    for m in mism[:40]:
        print('   MISMATCH', m)
    for z in keyonly_nonzero[:20]:
        print('   KEYONLY_NONZERO', z)
    summary[tag] = dict(field_cmp=field_cmp, exact=exact_fields, tol=tol_fields, mism=len(mism), rows_exact=rows_all_exact,
                        fields=len(fields_seen), keyonly=sum(keyonly.values()), keyonly_nonzero=len(keyonly_nonzero), cfg_diff=cfg_diff)
    # per-field-name check: which fields exist in new rows but never compared
    allnew = set(x for r in new.values() for x in r if not x.startswith('m_'))
    allold = set(x for r in old.values() for x in r)
    print(f'[{tag}] non-m_ field names in new not in any old: {sorted(allnew-allold)}; in old not in any new: {sorted(allold-allnew)}')
    mk = set(x for r in new.values() for x in r if x.startswith('m_'))
    print(f'[{tag}] distinct m_ keys in new: {len(mk)}')
json.dump(summary, open(sys.argv[1], 'w'), indent=1)
