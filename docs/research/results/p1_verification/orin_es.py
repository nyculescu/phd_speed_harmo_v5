"""Emergency stops of the in-sample oracle OR_in (per seed, the lowest main-run delay over A; ties in A order, as
v5b.p1.analysis.or_in). Reads stored runs only. Run with: python -I -B orin_es.py"""
import json, sys, statistics as st
sys.path.insert(0, '/home/catalin/work/phd/p1_frozen_85f7d34')
from v5b.p1 import analysis as an, family as fam
RUN = '/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
res = json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
for q in (1600.0, 2000.0):
    N = res['tune']['arms'][an.qk(q)]['N']
    for inc in ('slow', 'block'):
        dl, es = [], []
        for s in range(7400500, 7400600):
            keys = [an.sw(N, a, inc, q, s)['key'] for a in fam.A]
            runs = {k: json.load(open(RUN + k + '.json')) for k in keys}
            best = fam.argmin_tie({k: runs[k]['delay_s'] for k in keys}, keys)
            dl.append(runs[best]['delay_s']); es.append(runs[best]['emergency_stops'])
        print(f"{an.cell_name(inc, q)}: OR_in median delay {st.median(dl):.1f} (result.json "
              f"{res['eval']['table1_operating_map'][an.cell_name(inc, q)]['arms']['OR_in']['median_delay_s']:.1f}); "
              f"emergency stops median {st.median(es):g}, share>0 {sum(1 for x in es if x > 0)}/100")
