"""Emergency stops and collisions per arm and cell on the P1 evaluation seeds (7,400,500-599, main runs only).
Reads the stored run JSONs; runs nothing. Median over seeds; 'share>0' = seeds with at least one emergency stop."""
import json, statistics as st
R = '/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
res = json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
A = res['tune']['arms']
S = range(7400500, 7400600)
for q in (1600, 2000):
    a = A[str(q)]; N = a['N']
    for typ in ('slow', 'block', 'none'):
        arms = {'NC': 'NC', 'N': N, 'FX': a['FX'], 'FB': a['FB'], 'PI': a['PI'], 'AD': a['AD']}
        if typ != 'none':
            arms['ID'] = f"{N}-{a['ID']}"
            arms['IP'] = f"{N}-{a['IP'][typ]}"
        row = []
        for nm, k in arms.items():
            es, col = [], 0
            for s in S:
                d = json.load(open(R + f"{k}_{typ}_q{q}_s{s}.json"))
                es.append(d['emergency_stops']); col += d.get('collisions', 0) or 0
            row.append(f"{nm} {st.median(es):g} ({sum(1 for x in es if x > 0)}/100, coll {col})")
        print(f"{typ}_q{q}: " + '; '.join(row))
