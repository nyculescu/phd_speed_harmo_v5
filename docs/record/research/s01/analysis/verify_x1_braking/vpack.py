"""Does the measured run reproduce round 2's stored row on every stored key?"""
import json, math
from collections import Counter
D = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_test.jsonl'
R2 = '/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl'
r2 = {}
with open(R2) as h:
    for line in h:
        r = json.loads(line)
        r2[(r['name'], int(r['seed']), float(r.get('q', 0)))] = r
print('round2 rows', len(r2))
found = diff_rows = 0
diff_keys = Counter(); nkeys = Counter(); missing_in_new = Counter()
def same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return (math.isnan(a) and math.isnan(b)) or a == b
        except TypeError:
            return a == b
    return a == b
with open(D) as h:
    for line in h:
        r = json.loads(line)
        k = (r['name'], int(r['seed']), float(r.get('q', 0)))
        o = r2.get(k)
        if o is None:
            continue
        found += 1
        bad = False
        for kk, vv in o.items():
            if kk == 'cfg':
                continue
            nkeys[kk] += 1
            if kk not in r:
                missing_in_new[kk] += 1; bad = True; continue
            if not same(vv, r[kk]):
                diff_keys[kk] += 1; bad = True
        diff_rows += bad
print('matched rows', found, 'rows with any difference', diff_rows, 'keys compared', len(nkeys))
print('keys differing', dict(diff_keys.most_common(10)), 'missing in new', dict(missing_in_new.most_common(10)))
