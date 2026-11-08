# Own per-seed arm means (over learners) of selected summary metrics; median over seeds; compare with report panel 'med' values.
import json, re
import numpy as np
M = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/'
S = json.load(open(M + 'summary_rows_test.json'))
G = {'no control': ['nc'], '3E-T': ['3e'], 'p333': ['p333'], 'v3w': ['w0u250', 'w1u500', 'w2u250', 'w3u500', 'w4u500'],
     'tail': [f't{i}' for i in range(5)], 'sw': [f's{i}u500' for i in range(5)], 'baseline-v3': [f'd{i}u500' for i in range(5)]}
F = {'jam share (< 30 km/h)': lambda m: m['waves']['jam_share'],
     'events peaking at -4.5 or harder': lambda m: m['events_ge45_car'] + m['events_ge45_alks'] + m['events_ge45_truck'],
     'cascade share (cars)': lambda m: m['cascade_share_car'],
     'speed oscillation': lambda m: m['waves']['osc_kmh'],
     'congested length, max': lambda m: m['waves']['congested_km_max']}
txt = open(M + 'report_rows_test.txt').read()
for cell in ('X1', 'X2'):
    for title, f in F.items():
        blk = re.search(re.escape(f'{cell} at 5,300 veh/h: {title},') + r'.*?(?:\n\n|\Z)', txt, re.S).group(0)
        meds = dict(re.findall(r'^\s{2}(\S.*?)\s{2,}[-=| ]*\s+med (\S+)', blk, re.M))
        meds = {k.strip(): v for k, v in meds.items()}
        out = []
        for lab, names in G.items():
            runs = [S[f'{cell}|{n}|5300'] for n in names]
            seeds = sorted(set.intersection(*[set(r) for r in runs]))
            xs = [np.mean([f(r[s]) for r in runs]) for s in seeds]
            out.append(f'{lab}={np.median(xs):.4g} (panel {meds.get(lab, "?")}, n={len(xs)})')
        print(cell, title, '; '.join(out))
