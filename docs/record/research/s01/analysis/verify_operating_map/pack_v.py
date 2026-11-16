"""Spot checks of F5's paired pack metrics (v3w minus p333) from summary_rows_*.json."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from lib import ARMS, SETTINGS, pdiff  # noqa: E402

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
S = {k: json.load(open(D / f"summary_rows_{k}.json")) for k in ("s1", "band", "test")}
CL = ("car", "alks", "truck")
F = {"jam_share": lambda m: m["waves"]["jam_share"], "jams": lambda m: m["waves"]["jams"],
     "ev45": lambda m: sum(m[f"events_ge45_{c}"] for c in CL), "ev_all": lambda m: sum(m[f"events_{c}"] for c in CL),
     "cascade_car": lambda m: m["cascade_share_car"], "osc": lambda m: m["waves"]["osc_kmh"],
     "cong_max": lambda m: m["waves"]["congested_km_max"]}


def arm(kind, cell, q, members, f):
    runs = [S[kind][f"{cell}|{m}|{q:.0f}"] for m in members]
    seeds = sorted(set.intersection(*(set(r) for r in runs)))
    return {s: float(np.mean([f(r[s]) for r in runs])) for s in seeds}


L = []
for kind, cell, q, lab in SETTINGS:
    if lab not in ("5000", "X1", "7000"):
        continue
    for name, f in F.items():
        A = {a: arm(kind, cell, q, ARMS[a], f) for a in ("v3w", "p333", "nc", "3e")}
        t = pdiff(A["v3w"], A["p333"])
        L.append(f"{lab} {name}: medians v3w {np.median(list(A['v3w'].values())):.4g}, p333 {np.median(list(A['p333'].values())):.4g}, "
                 f"nc {np.median(list(A['nc'].values())):.4g}, 3e {np.median(list(A['3e'].values())):.4g}; v3w-p333 {t[0]:+.4g} [{t[1]:+.4g}, {t[2]:+.4g}]")
open(Path(__file__).parent / "pack_v.txt", "w").write("\n".join(L))
print("\n".join(L))
