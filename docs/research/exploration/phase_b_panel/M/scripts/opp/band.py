"""EXPLORATORY: stored band rows (condition T, 20 seeds per level): paired spread of rule delay against p333 by demand level."""
import json
from collections import defaultdict
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl'
T = defaultdict(dict)
names = set()
for line in open(ROWS):
    r = json.loads(line)
    names.add(r["name"])
    T[r["name"]][r["seed"]] = (r["all_delay"], r.get("passed"), r.get("m_planned_window"), r.get("end_stop2"), r.get("end_stop"))
ns = sorted(names)
print(len(ns), ns[:12], "...", ns[-6:])
levels = sorted({n.split("|")[0] for n in ns})
arms = sorted({n.split("|", 1)[1] for n in ns})
print("levels", levels); print("arms", arms)
for lv in levels:
    if f"{lv}|p333" not in T:
        continue
    seeds = sorted(T[f"{lv}|p333"])
    b = np.array([T[f"{lv}|p333"][s][0] for s in seeds]); med = np.median(b)
    pl = [T[f"{lv}|p333"][s][2] for s in seeds]; pa = [T[f"{lv}|p333"][s][1] for s in seeds]
    line = f"{lv}: n {len(seeds)} p333 median delay {med:.0f}; passed/planned median {np.median(np.array(pa)/np.array(pl)) if pl[0] else float('nan'):.3f}; end_stop1 {np.median([T[f'{lv}|p333'][s][4] for s in seeds]):.0f} end_stop2 {np.median([T[f'{lv}|p333'][s][3] for s in seeds]):.0f} |"
    for a in arms:
        if a in ("p333",) or f"{lv}|{a}" not in T or a.startswith("w"):
            continue
        x = np.array([T[f"{lv}|{a}"][s][0] for s in seeds if s in T[f"{lv}|{a}"]])
        if len(x) != len(b):
            continue
        d = 100 * (b - x) / med
        line += f" {a} {np.median(d):+.1f} sd {d.std(ddof=1):.1f};"
    print(line[:900])
