# Smoke rows vs main rows with the same key, every key except cfg and m_st_file.
import json, math
D = '/home/catalin/work/phd/v5b1_runs/'
M = D + 'measure_s01_remote/'
main = {}
for t in ('test', 'band', 's1'):
    for l in open(M + f'rows_{t}.jsonl'):
        r = json.loads(l); main[(r['name'], float(r['q']), int(r['seed']))] = r

def diff(a, b, p=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b:
                out.append((p + k, 'keyonly', None))
            else:
                out += diff(a[k], b[k], p + k + '.')
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((p, 'len', None))
        else:
            for x, y in zip(a, b):
                out += diff(x, y, p)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if a != b:
            out.append((p.rstrip('.'), 'num', abs(a - b) / max(abs(a), abs(b))))
    elif a != b:
        out.append((p, 'other', None))
    return out

for f in ['measure_s01_remote/smoke/smoke_rows.jsonl', 'measure_s01_remote/smoke1/smoke1_rows.jsonl', 's01_smoke1/smoke1_rows.jsonl',
          's01_smoke2/smoke1_rows.jsonl', 'round2_measure_smoke_2354/smoke_rows.jsonl']:
    R = [json.loads(l) for l in open(D + f) if l.strip()]
    print(f, len(R), 'rows')
    for r in R:
        k = (r['name'], float(r['q']), int(r['seed']))
        m = main.get(k)
        if m is None:
            print('   no main row for', k); continue
        a = {x: v for x, v in r.items() if x not in ('cfg', 'm_st_file')}
        b = {x: v for x, v in m.items() if x not in ('cfg', 'm_st_file')}
        d = diff(a, b)
        fields = sorted({x[0].split('.')[0] for x in d})
        mx = max([x[2] for x in d if x[2] is not None], default=0)
        print(f'   {k}: differing fields {fields} max rel {mx:.2g}')
